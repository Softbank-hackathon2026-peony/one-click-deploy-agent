"""웹 워크로드의 엔드포인트 찾기(설계 §6.2)."""

from __future__ import annotations

import ast
import re
from collections import defaultdict
from pathlib import PurePosixPath

from infrafit.detect.workloads import WorkloadInfo
from infrafit.evidence import evidence
from infrafit.repo import Snapshot

HTTP_METHODS = ("get", "post", "put", "delete", "patch")
NEXT_METHODS = "GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS"
_SERVER_VAR = re.compile(
    r"\b(?:const|let|var)\s+(\w+)\s*=\s*(?:await\s+)?"
    r"(?:express\s*\(|express\.Router\s*\(|require\(\s*['\"]express['\"]\s*\)(?:\.Router)?\s*\(|Router\s*\("
    r"|fastify\s*\(|Fastify\s*\(|new\s+Koa\s*\(|new\s+Router\s*\(|new\s+Hono\s*\()")
_ROUTE_CALL = re.compile(r"\b(\w+)\.(get|post|put|delete|patch|all)\(\s*['\"`]([^'\"`]+)['\"`]")
_DJANGO = re.compile(r"\b(?:re_)?path\(\s*r?['\"]([^'\"]*)['\"]")
_NEXT_EXPORT = re.compile(rf"export\s+(?:async\s+)?function\s+({NEXT_METHODS})\b|export\s+const\s+({NEXT_METHODS})\s*=")

Raw = tuple[str, str, str, int, str]  # (메서드, 경로, 파일, 줄, 프레임워크)


def _prefixes(tree: ast.AST) -> dict[str, str]:
    out: dict[str, str] = {}
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)):
            continue
        func = node.value.func
        fname = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
        if fname not in ("APIRouter", "Blueprint"):
            continue
        for kw in node.value.keywords:
            if kw.arg in ("prefix", "url_prefix") and isinstance(kw.value, ast.Constant):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        out[target.id] = str(kw.value.value)
    return out


def _python(snap: Snapshot) -> list[Raw]:
    out: list[Raw] = []
    for rel in snap.glob("**/*.py"):
        try:
            tree = ast.parse(snap.read(rel))
        except (SyntaxError, ValueError, RecursionError):
            continue
        prefixes = _prefixes(tree)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                if not (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)):
                    continue
                if not dec.args or not isinstance(dec.args[0], ast.Constant) or not isinstance(dec.args[0].value, str):
                    continue
                owner = dec.func.value.id if isinstance(dec.func.value, ast.Name) else ""
                path = prefixes.get(owner, "") + dec.args[0].value
                attr = dec.func.attr
                if attr in HTTP_METHODS:
                    out.append((attr.upper(), path, rel, dec.lineno, "python"))
                elif attr == "route":
                    methods = ["GET"]
                    for kw in dec.keywords:
                        if kw.arg == "methods" and isinstance(kw.value, (ast.List, ast.Tuple)):
                            methods = [str(e.value).upper() for e in kw.value.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
                    out += [(m, path, rel, dec.lineno, "python") for m in methods]
                elif attr == "websocket":
                    out.append(("WEBSOCKET", path, rel, dec.lineno, "python"))
    return out


def _django(snap: Snapshot) -> list[Raw]:
    out: list[Raw] = []
    for rel in snap.glob("**/urls.py"):
        for i, text in enumerate(snap.lines(rel), 1):
            for m in _DJANGO.finditer(text):
                out.append(("ANY", "/" + m.group(1), rel, i, "django"))
    return out


def _express(snap: Snapshot) -> list[Raw]:
    out: list[Raw] = []
    for pattern in ("**/*.js", "**/*.ts", "**/*.mjs", "**/*.cjs"):
        for rel in snap.glob(pattern):
            if PurePosixPath(rel).name.startswith("route.") and "/app/" in f"/{rel}":
                continue
            servers = set(_SERVER_VAR.findall(snap.read(rel)))
            if not servers:
                continue
            for i, text in enumerate(snap.lines(rel), 1):
                for m in _ROUTE_CALL.finditer(text):
                    if m.group(1) not in servers:
                        continue
                    method = "ANY" if m.group(2) == "all" else m.group(2).upper()
                    out.append((method, m.group(3), rel, i, "express"))
    return out


def _next_route_path(parts: list[str]) -> str:
    keep = [p for p in parts if not (p.startswith("(") and p.endswith(")")) and not p.startswith("@")]
    return "/" + "/".join(keep)


def _next(snap: Snapshot) -> list[Raw]:
    out: list[Raw] = []
    for ext in ("ts", "js", "tsx", "jsx"):
        for rel in snap.glob(f"**/app/**/route.{ext}"):
            parts = PurePosixPath(rel).parts
            idx = len(parts) - 1 - list(reversed(parts)).index("app")
            route = _next_route_path(list(parts[idx + 1:-1]))
            for i, text in enumerate(snap.lines(rel), 1):
                for m in _NEXT_EXPORT.finditer(text):
                    out.append((m.group(1) or m.group(2), route, rel, i, "nextjs"))
    for ext in ("ts", "js"):
        for rel in snap.glob(f"**/pages/api/**.{ext}"):
            parts = list(PurePosixPath(rel).with_suffix("").parts)
            idx = len(parts) - 1 - list(reversed(parts)).index("pages")
            segs = parts[idx + 1:]
            if segs and segs[-1] == "index":
                segs = segs[:-1]
            out.append(("ANY", "/" + "/".join(segs), rel, 1, "nextjs"))
    return out


def _assign(rel: str, webs: list[WorkloadInfo]) -> WorkloadInfo:
    if len(webs) == 1:
        return webs[0]
    segments = set(PurePosixPath(rel).parts)

    def score(w: WorkloadInfo) -> int:
        s = len(set(w.name.split("-")) & segments)
        if w.app_dir and rel.startswith(w.app_dir + "/"):
            s += 10
        return s

    best = max(webs, key=lambda w: (score(w), -len(w.name), [-ord(c) for c in w.id]))
    return best if score(best) > 0 else sorted(webs, key=lambda w: w.id)[0]


def extract_endpoints(snap: Snapshot, workloads: list[WorkloadInfo]) -> list[dict]:
    webs = [w for w in workloads if w.kind == "web"]
    if not webs:
        return []
    raw = sorted(set(_python(snap) + _django(snap) + _express(snap) + _next(snap)),
                 key=lambda r: (r[2], r[3], r[0], r[1]))
    counters: dict[str, int] = defaultdict(int)
    out: list[dict] = []
    for method, route, rel, line, framework in raw:
        w = _assign(rel, webs)
        counters[w.id] += 1
        out.append({"id": f"ep-{w.id[2:]}-{counters[w.id]:03d}", "workload": w.id, "method": method,
                    "route": route, "handler": evidence(snap, rel, line), "framework": framework,
                    "status": "confirmed"})
    return out
