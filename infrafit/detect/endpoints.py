"""웹 워크로드의 엔드포인트 찾기(설계 §6.2)."""

from __future__ import annotations

import ast
import re
from collections import defaultdict
from pathlib import PurePosixPath

from infrafit.detect.manifests import Manifests, parse_manifests, parent_dir
from infrafit.detect.nginx import LocationInfo, ProxyRoute, ProxyServer
from infrafit.detect.proxy_graph import fronted_in, upstream_chains
from infrafit.detect.testpaths import is_test_path
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
# `X.route({ method: ..., url: ... })`(Fastify 등의 라우트 객체)
_ROUTE_OBJECT = re.compile(r"\b(\w+)\.route\(\s*\{")
_OBJ_METHOD = re.compile(r"\bmethod\s*:\s*(\[[^\]]*\]|['\"`][^'\"`]+['\"`])")
_OBJ_URL = re.compile(r"\burl\s*:\s*['\"`]([^'\"`]+)['\"`]")
_STRING = re.compile(r"['\"`]([^'\"`]+)['\"`]")
# 함수 매개변수 목록: `function x(a, b)`, `(a, b) =>`, `(a: T): R =>`, `a =>`
_FUNC_PARAMS = re.compile(r"\bfunction\b\s*\*?\s*\w*\s*\(([^)]*)\)"
                          r"|\(([^()]*)\)\s*(?::\s*[^=;{}()]+)?=>"
                          r"|\b(\w+)\s*=>")
_PARAM_NAME = re.compile(r"^\s*(?:\.\.\.)?(\w+)")
# 가장 가까운 package.json에 이 중 하나가 있으면 매개변수 이름만으로 서버 변수로 본다
SERVER_DEPS = ("express", "fastify", "koa", "hono", "@koa/router")
SERVER_PARAMS = frozenset({"app", "router", "server", "fastify", "instance", "api"})
# Express 계열 framework 이름: 가장 가까운 package.json 의존성 중 이 순서로 처음 있는 것, 없으면 express
EXPRESS_FAMILY = ("fastify", "koa", "hono", "express")
_DJANGO = re.compile(r"\b(?:re_)?path\(\s*r?['\"]([^'\"]*)['\"]")
_NEXT_EXPORT = re.compile(rf"export\s+(?:async\s+)?function\s+({NEXT_METHODS})\b|export\s+const\s+({NEXT_METHODS})\s*=")

# 경로 매개변수: (?P<x>...), {x}, /:x(세그먼트 시작만), [x](·[...x]·[[...x]]), <x>, <int:x>
_PARAM = re.compile(r"\(\?P<[^>]+>[^)]*\)|\{[^}/]*\}|<[^>/]*>|\[\[?[^\]/]*\]?\]|(?<=/):[A-Za-z_]\w*")
PREFIX_MODIFIERS = ("", "^~")

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


_INCLUDE_ATTRS = {"include_router": "prefix", "register_blueprint": "url_prefix"}
_MAX_DEPTH = 5

Ref = tuple[str, str]  # (파일, 라우터 변수명)


def _join(a: str, b: str) -> str:
    """경로 조각을 '/'가 겹치거나 빠지지 않게 잇는다. 한쪽이 비면 다른 쪽 그대로."""
    if not a:
        return b
    if not b:
        return a
    return a.rstrip("/") + "/" + b.lstrip("/")


def _module_file(snap: Snapshot, directory: str, parts: list[str]) -> str | None:
    """directory 기준 점 경로(parts)에 해당하는 모듈 파일(`x.py` 또는 `x/__init__.py`)."""
    if not parts:
        return None
    base = "/".join(([directory] if directory else []) + parts)
    for cand in (f"{base}.py", f"{base}/__init__.py"):
        if snap.exists(cand):
            return cand
    return None


def _abs_module_file(snap: Snapshot, rel: str, parts: list[str]) -> str | None:
    """절대 import: 현재 파일 디렉터리에서 위로 올라가며 처음 찾은 모듈 파일."""
    d = str(PurePosixPath(rel).parent)
    d = "" if d == "." else d
    while True:
        found = _module_file(snap, d, parts)
        if found:
            return found
        if not d:
            return None
        parent = str(PurePosixPath(d).parent)
        d = "" if parent == "." else parent


def _imports(snap: Snapshot, rel: str, tree: ast.AST) -> dict[str, tuple[str, str | None]]:
    """지역 이름 -> (모듈 파일, 원래 이름). 원래 이름이 None이면 모듈 자체를 가리킨다."""
    out: dict[str, tuple[str, str | None]] = {}

    def find(parts: list[str], level: int) -> str | None:
        if level:
            d = PurePosixPath(rel).parent
            for _ in range(level - 1):
                d = d.parent
            base = "" if str(d) == "." else str(d)
            return _module_file(snap, base, parts)
        return _abs_module_file(snap, rel, parts)

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module.split(".") if node.module else []
            for alias in node.names:
                local = alias.asname or alias.name
                sub = find(mod + [alias.name], node.level)
                if sub:
                    out[local] = (sub, None)
                    continue
                owner = find(mod, node.level)
                if owner:
                    out[local] = (owner, alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if not alias.asname and "." in alias.name:
                    continue  # `import a.b`는 이름 a만 묶으므로 다루지 않는다
                f = _abs_module_file(snap, rel, alias.name.split("."))
                if f:
                    out[alias.asname or alias.name] = (f, None)
    return out


def _ref(rel: str, node: ast.expr, imports: dict[str, tuple[str, str | None]]) -> Ref | None:
    """include 대상 표현식을 (파일, 변수명)으로 푼다. 못 풀면 None."""
    if isinstance(node, ast.Name):
        imp = imports.get(node.id)
        if imp is None:
            return (rel, node.id)
        return (imp[0], imp[1]) if imp[1] else None
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        imp = imports.get(node.value.id)
        if imp and imp[1] is None:
            return (imp[0], node.attr)
    return None


def _mounts(snap: Snapshot, trees: dict[str, ast.AST]) -> dict[Ref, list[tuple[Ref, str]]]:
    """자식 라우터 -> [(부모 라우터, include 접두어)]. 접두어가 문자열 상수가 아니면 건너뛴다."""
    out: dict[Ref, list[tuple[Ref, str]]] = defaultdict(list)
    for rel, tree in trees.items():
        imports = _imports(snap, rel, tree)
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr in _INCLUDE_ATTRS and isinstance(node.func.value, ast.Name)
                    and node.args):
                continue
            child = _ref(rel, node.args[0], imports)
            if child is None:
                continue
            prefix = ""
            ok = True
            for kw in node.keywords:
                if kw.arg == _INCLUDE_ATTRS[node.func.attr]:
                    if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        prefix = kw.value.value
                    else:
                        ok = False
            parent = _ref(rel, node.func.value, imports)
            if ok and parent is not None:
                out[child].append((parent, prefix))
    return out


def _include_prefixes(ref: Ref, mounts: dict[Ref, list[tuple[Ref, str]]], own: dict[Ref, str],
                      stack: tuple[Ref, ...] = ()) -> set[str]:
    """라우터가 앱까지 연결되며 받는 include 접두어 전부(중간 라우터 자체 접두어 포함). 순환과 깊이 초과는 끊는다."""
    out: set[str] = set()
    if len(stack) < _MAX_DEPTH:
        for parent, prefix in mounts.get(ref, []):
            if parent == ref or parent in stack:
                continue
            mid = own.get(parent, "")
            out |= {_join(_join(pp, mid), prefix) for pp in _include_prefixes(parent, mounts, own, stack + (ref,))}
    return out or {""}


def _code_files(snap: Snapshot, pattern: str) -> list[str]:
    """pattern에 맞는 파일 중 테스트 코드가 아닌 것."""
    return [rel for rel in snap.glob(pattern) if not is_test_path(rel)]


def _str_arg(call: ast.Call) -> str | None:
    """첫 인자가 문자열 상수면 그 값."""
    if call.args and isinstance(call.args[0], ast.Constant) and isinstance(call.args[0].value, str):
        return call.args[0].value
    return None


def _kw_methods(call: ast.Call) -> list[str]:
    """`methods=[...]` 키워드의 문자열 메서드들. 키워드가 없으면 GET."""
    for kw in call.keywords:
        if kw.arg == "methods" and isinstance(kw.value, (ast.List, ast.Tuple)):
            return [str(e.value).upper() for e in kw.value.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
    return ["GET"]


def _route_calls(tree: ast.AST):
    """(라우트 호출, 메서드들): 데코레이터 라우트(`@X.get("/r")`, `@X.route("/r", methods=...)`)와
    Flask `X.add_url_rule("/r", methods=...)`. 경로가 문자열 상수인 것만."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                if not (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)) or _str_arg(dec) is None:
                    continue
                attr = dec.func.attr
                if attr in HTTP_METHODS:
                    yield dec, [attr.upper()]
                elif attr == "route":
                    yield dec, _kw_methods(dec)
                elif attr == "websocket":
                    yield dec, ["WEBSOCKET"]
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
              and node.func.attr == "add_url_rule" and _str_arg(node) is not None):
            yield node, _kw_methods(node)


def _python(snap: Snapshot) -> list[Raw]:
    trees: dict[str, ast.AST] = {}
    for rel in _code_files(snap, "**/*.py"):
        try:
            trees[rel] = ast.parse(snap.read(rel))
        except (SyntaxError, ValueError, RecursionError):
            continue
    mounts = _mounts(snap, trees)
    own_prefix = {(rel, var): pre for rel, tree in trees.items() for var, pre in _prefixes(tree).items()}
    out: list[Raw] = []
    for rel, tree in trees.items():
        prefixes = _prefixes(tree)
        for call, methods in _route_calls(tree):
            owner = call.func.value.id if isinstance(call.func.value, ast.Name) else ""
            own = _join(prefixes.get(owner, ""), _str_arg(call))
            incs = _include_prefixes((rel, owner), mounts, own_prefix) if owner else {""}
            for inc in sorted(incs):
                path = _join(inc, own)
                out += [(m, path, rel, call.lineno, "python") for m in methods]
    return out


def _django(snap: Snapshot) -> list[Raw]:
    out: list[Raw] = []
    for rel in _code_files(snap, "**/urls.py"):
        for i, text in enumerate(snap.lines(rel), 1):
            for m in _DJANGO.finditer(text):
                out.append(("ANY", "/" + m.group(1), rel, i, "django"))
    return out


def _package_deps(snap: Snapshot, manifests: Manifests, rel: str) -> set[str]:
    """파일이 속한 가장 가까운 package.json의 의존성 이름들(없으면 빈 집합)."""
    d = parent_dir(rel)
    while True:
        if snap.exists(f"{d}/package.json" if d else "package.json"):
            return manifests.deps_by_dir.get(d, set())
        if not d:
            return set()
        d = parent_dir(d)


def _param_servers(text: str) -> set[str]:
    """함수 매개변수 중 서버 변수로 흔히 쓰는 이름(`function x(fastify, opts)`, `async (app) =>` 등)."""
    out: set[str] = set()
    for m in _FUNC_PARAMS.finditer(text):
        params = m.group(1) if m.group(1) is not None else m.group(2) if m.group(2) is not None else m.group(3)
        for param in params.split(","):
            name = _PARAM_NAME.match(param)
            if name and name.group(1) in SERVER_PARAMS:
                out.add(name.group(1))
    return out


def _top_level(text: str, start: int) -> str:
    """text[start]의 `{`로 여는 객체에서 바로 아래 단계 글자만 남긴 문자열. 더 깊은 `{}`·`()` 안은 공백으로
    바꿔 핸들러 본문의 `url:` 같은 글자를 키로 읽지 않는다. 문자열 안 괄호는 세지 않는다."""
    out: list[str] = []
    depth = 0
    quote = ""
    for ch in text[start:]:
        if quote:
            quote = "" if ch == quote else quote
        elif ch in "'\"`":
            quote = ch
        elif ch in "{(":
            depth += 1
        elif ch in "})":
            depth -= 1
            if depth == 0:
                break
        out.append(ch if depth == 1 else " ")
    return "".join(out)


def _route_objects(text: str, servers: set[str]) -> list[tuple[list[str], str, int]]:
    """`X.route({ method, url })`(X는 서버 변수) → (메서드들, 경로, 줄)."""
    out = []
    for m in _ROUTE_OBJECT.finditer(text):
        if m.group(1) not in servers:
            continue
        body = _top_level(text, m.end() - 1)
        method, url = _OBJ_METHOD.search(body), _OBJ_URL.search(body)
        if not (method and url):
            continue
        methods = sorted({x.upper() for x in _STRING.findall(method.group(1))})
        out.append((methods, url.group(1), text.count("\n", 0, m.start()) + 1))
    return out


def _express(snap: Snapshot, manifests: Manifests) -> list[Raw]:
    out: list[Raw] = []
    for pattern in ("**/*.js", "**/*.ts", "**/*.mjs", "**/*.cjs"):
        for rel in _code_files(snap, pattern):
            if PurePosixPath(rel).name.startswith("route.") and "/app/" in f"/{rel}":
                continue
            text = snap.read(rel)
            deps = _package_deps(snap, manifests, rel)
            servers = set(_SERVER_VAR.findall(text))
            if any(dep in deps for dep in SERVER_DEPS):
                servers |= _param_servers(text)
            if not servers:
                continue
            framework = next((fw for fw in EXPRESS_FAMILY if fw in deps), "express")
            for i, line in enumerate(snap.lines(rel), 1):
                for m in _ROUTE_CALL.finditer(line):
                    if m.group(1) not in servers:
                        continue
                    method = "ANY" if m.group(2) == "all" else m.group(2).upper()
                    out.append((method, m.group(3), rel, i, framework))
            for methods, route, i in _route_objects(text, servers):
                out += [(method, route, rel, i, framework) for method in methods]
    return out


def _next_route_path(parts: list[str]) -> str:
    keep = [p for p in parts if not (p.startswith("(") and p.endswith(")")) and not p.startswith("@")]
    return "/" + "/".join(keep)


def _next(snap: Snapshot) -> list[Raw]:
    out: list[Raw] = []
    for ext in ("ts", "js", "tsx", "jsx"):
        for rel in _code_files(snap, f"**/app/**/route.{ext}"):
            parts = PurePosixPath(rel).parts
            idx = len(parts) - 1 - list(reversed(parts)).index("app")
            route = _next_route_path(list(parts[idx + 1:-1]))
            for i, text in enumerate(snap.lines(rel), 1):
                for m in _NEXT_EXPORT.finditer(text):
                    out.append((m.group(1) or m.group(2), route, rel, i, "nextjs"))
    for ext in ("ts", "js"):
        for rel in _code_files(snap, f"**/pages/api/**.{ext}"):
            parts = list(PurePosixPath(rel).with_suffix("").parts)
            idx = len(parts) - 1 - list(reversed(parts)).index("pages")
            segs = parts[idx + 1:]
            if segs and segs[-1] == "index":
                segs = segs[:-1]
            out.append(("ANY", "/" + "/".join(segs), rel, 1, "nextjs"))
    return out


def _assign(rel: str, webs: list[WorkloadInfo]) -> tuple[WorkloadInfo, bool]:
    """(워크로드, 근거로 정했는가). 아무 근거도 없어 첫 워크로드로 보낸 것은 추측이다."""
    if len(webs) == 1:
        return webs[0], True
    segments = set(PurePosixPath(rel).parts)

    def score(w: WorkloadInfo) -> int:
        s = len(set(w.name.split("-")) & segments)
        if any(root and rel.startswith(root + "/") for root in {w.app_dir, w.code_root}):
            s += 10
        return s

    best = max(webs, key=lambda w: (score(w), -len(w.name), [-ord(c) for c in w.id]))
    if score(best) > 0:
        return best, True
    return sorted(webs, key=lambda w: w.id)[0], False


def _roots(w: WorkloadInfo) -> set[str]:
    """워크로드 코드의 뿌리 디렉터리들. code_root는 `""`(저장소 루트)도 뿌리이고 None만 모름이다.
    app_dir는 코드에서 찾은 워크로드만 채우고 나머지는 기본값 `""`라서, 비어 있지 않을 때만 뿌리로 본다
    (코드·Dockerfile 워크로드는 code_root가 app_dir와 같아 루트 앱도 code_root로 잡힌다)."""
    return {r for r in (w.app_dir or None, w.code_root) if r is not None}


def _owners(rel: str, webs: list[WorkloadInfo]) -> list[WorkloadInfo]:
    """핸들러 파일을 app_dir 또는 code_root 아래에 둔 web 워크로드 중 그 루트가 가장 깊은 것들(같으면 모두, id 순)."""
    depth: dict[str, int] = {}
    for w in webs:
        roots = [r for r in _roots(w) if r == "" or rel.startswith(r + "/")]
        if roots:
            depth[w.id] = max(len(PurePosixPath(r).parts) for r in roots)
    if not depth:
        return []
    deepest = max(depth.values())
    return sorted((w for w in webs if depth.get(w.id) == deepest), key=lambda w: w.id)


# --- nginx location 선택과 노출 판정 -------------------------------------------

def _matches(loc: LocationInfo, path: str) -> bool:
    flags = re.IGNORECASE if loc.modifier == "~*" else 0
    try:
        return re.search(loc.pattern, path, flags) is not None
    except re.error:  # PCRE 전용 문법 등은 건너뛴다
        return False


REGEX_MODIFIERS = ("~", "~*")


def _nested(loc: LocationInfo, request_path: str) -> LocationInfo:
    return (select_location(loc.children, request_path) if loc.children else None) or loc


def select_location(locations: list[LocationInfo], request_path: str) -> LocationInfo | None:
    """nginx 규칙: `=` 정확 일치 → 가장 긴 접두어(`^~`면 확정) → 그 접두어 안의 중첩 정규식 → 바깥 정규식(설정 순서)
    → 기억한 접두어(또는 그 안의 중첩 선택). 명명 location(`@x`)만 후보에서 뺀다. internal location도 고를 수 있고,
    고른 것이 internal이면 외부 요청은 아무 데도 닿지 않는다(nginx 404)."""
    cands = [loc for loc in locations if loc.modifier != "@"]
    exact = next((loc for loc in cands if loc.modifier == "=" and loc.pattern == request_path), None)
    if exact is not None:
        return _nested(exact, request_path)
    prefixes = [loc for loc in cands if loc.modifier in PREFIX_MODIFIERS and request_path.startswith(loc.pattern)]
    best = max(prefixes, key=lambda loc: (len(loc.pattern), -loc.order), default=None)
    if best is not None and best.modifier == "^~":
        return _nested(best, request_path)
    inner = select_location(best.children, request_path) if best is not None and best.children else None
    if inner is not None and inner.modifier in REGEX_MODIFIERS:
        return inner
    regexes = sorted((loc for loc in cands if loc.modifier in REGEX_MODIFIERS), key=lambda loc: loc.order)
    regex = next((loc for loc in regexes if _matches(loc, request_path)), None)
    if regex is not None:
        return _nested(regex, request_path)
    return inner or best


def _request_path(route: str, framework: str = "") -> str:
    if framework == "django":  # 정규식 경로의 앵커는 요청 경로에 없다
        route = route.replace("^", "").removesuffix("$")
    path = _PARAM.sub("x1", route)
    return path if path.startswith("/") else "/" + path


def _forwarded(loc: LocationInfo, uri: str | None, path: str) -> str:
    """location이 uri를 가진 proxy_pass로 넘길 때 upstream이 받는 경로."""
    if uri is None:
        return path
    rest = path[len(loc.pattern):] if loc.modifier in PREFIX_MODIFIERS and path.startswith(loc.pattern) else ""
    return uri + rest


def _all_locations(locations: list[LocationInfo]) -> list[LocationInfo]:
    out = []
    for loc in locations:
        out.append(loc)
        out.extend(_all_locations(loc.children))
    return out


def _reached(server: ProxyServer, path: str) -> set[tuple[str, str]]:
    """외부 요청 path가 이 server에서 고른 location으로 닿는 (워크로드 id, 전달 경로)들."""
    loc = select_location(server.locations, path)
    if loc is None or loc.internal:  # internal location을 고른 외부 요청은 404
        return set()
    return {(t, _forwarded(loc, uri, path)) for t, uri in loc.proxies if t}


def _external(locations: list[LocationInfo]) -> list[LocationInfo]:
    """외부 요청이 고를 수 있는 location(internal·명명 제외, 그 안의 중첩 포함)."""
    out = []
    for loc in locations:
        if loc.modifier != "@" and not loc.internal:
            out.append(loc)
            out.extend(_external(loc.children))
    return out


def _requests_for(server: ProxyServer, workload: str, path: str) -> list[str]:
    """upstream 경로 path가 workload에 닿을 수 있는 외부 요청 후보: path 자체, 그리고 workload로 uri U를 붙여
    넘기는 외부 접두사 location L마다 path가 U로 시작하면 L.pattern + path[len(U):](접두사를 떼는 프록시)."""
    out = [path]
    for loc in _external(server.locations):
        if loc.modifier not in PREFIX_MODIFIERS:
            continue
        for t, uri in loc.proxies:
            if t == workload and uri is not None and path.startswith(uri):
                out.append(loc.pattern + path[len(uri):])
    return sorted(set(out))


def _subrequest_reached(server: ProxyServer) -> set[tuple[str, str]]:
    """외부에서 고를 수 있는 location의 하위 요청(auth_request)은 호출 엔드포인트와 상관없이 닿는다."""
    internal = [x for x in _all_locations(server.locations) if x.internal]
    out: set[tuple[str, str]] = set()
    for loc in _external(server.locations):
        for name in loc.subrequests:
            for sub in (x for x in internal if x.pattern == name):
                out |= {(t, _forwarded(sub, uri, name)) for t, uri in sub.proxies if t}
    return out


class _Reach:
    """한 환경에서 프록시에 들어온 요청 경로가 닿는 (워크로드 id, 전달 경로)들을 기억해 둔다."""

    def __init__(self, servers: list[ProxyServer]):
        self.by_proxy: dict[str, list[ProxyServer]] = defaultdict(list)
        for server in servers:
            self.by_proxy[server.proxy].append(server)
        self._memo: dict[tuple, frozenset] = {}

    def server(self, proxy: str, i: int, path: str) -> frozenset:
        key = (proxy, i, path)
        if key not in self._memo:
            self._memo[key] = frozenset(_reached(self.by_proxy[proxy][i], path))
        return self._memo[key]

    def proxy(self, proxy: str, path: str) -> frozenset:
        key = (proxy, None, path)
        if key not in self._memo:
            self._memo[key] = frozenset().union(*(self.server(proxy, i, path)
                                                  for i in range(len(self.by_proxy.get(proxy, [])))))
        return self._memo[key]


def _chain_reached(chain: tuple[str, ...], top: int, reach: _Reach, workload: str, path: str) -> set[tuple[str, str]]:
    """체인 맨 위 프록시의 top번째 server로 들어온 외부 요청 후보가 체인 끝 프록시에서 닿는 (워크로드 id, 전달 경로)들.
    후보는 workload의 upstream 경로 path에서 시작해 아래 단계부터 위로 역매핑해 만들고(_requests_for),
    맨 위에서부터 단계마다 다시 location을 골라 다음 프록시로 넘어가는 것만 따라간다(internal을 고르면 404)."""
    targets = chain[1:] + (workload,)
    cands = {path}
    for i in range(len(chain) - 1, 0, -1):
        cands |= {c for server in reach.by_proxy.get(chain[i], []) for r in cands
                  for c in _requests_for(server, targets[i], r)}
    top_server = reach.by_proxy[chain[0]][top]
    cands = {c for r in cands for c in _requests_for(top_server, targets[0], r)}
    reached: set[tuple[str, str]] = set()
    for r in cands:
        reached |= reach.server(chain[0], top, r)
    for i in range(1, len(chain)):
        forwarded = {fwd for t, fwd in reached if t == chain[i]}
        reached = {hit for r in forwarded for hit in reach.proxy(chain[i], r)}
    return reached


def _exposure_in(env: str | None, out: list[dict], routes: list[ProxyRoute], servers: list[ProxyServer],
                 fronted: set[str]) -> dict[str, str]:
    """환경 env의 server·route만 써서, 그 환경 route가 target으로 하는 워크로드의 엔드포인트 id별 값을 계산한다.
    프록시 뒤의 프록시는 체인 맨 위 프록시로 들어온 외부 요청이 단계마다 전달되어 닿는지로 본다.
    fronted는 이 환경에서 앞 구간(엣지·로드밸런서)이 있는 프록시 id들이다."""
    routes = [r for r in routes if r.environment == env]
    servers = [s for s in servers if s.environment == env]
    routed = {r.target for r in routes if r.target}
    reach = _Reach(servers)
    # 하위 요청(auth_request)은 요청이 들어오는 프록시마다 무조건 닿는다. 체인 맨 위가 아닌 프록시도
    # 위 단계 route로 요청을 받으므로 환경의 모든 server를 본다
    reached: set[tuple[str, str]] = set()
    for server in servers:
        reached |= _subrequest_reached(server)
    chains = {w: sorted(upstream_chains(routes, fronted, w)) for w in sorted(routed)}
    for ep in out:
        if ep["workload"] not in routed:
            continue
        path = _request_path(ep["route"], ep["framework"])
        for chain in chains[ep["workload"]]:
            for top in range(len(reach.by_proxy.get(chain[0], []))):
                reached |= _chain_reached(chain, top, reach, ep["workload"], path)
    return {ep["id"]: "routed" if (ep["workload"], _request_path(ep["route"], ep["framework"])) in reached
            else "not-routed" for ep in out if ep["workload"] in routed}


def _mark_exposure(out: list[dict], routes: list[ProxyRoute], servers: list[ProxyServer],
                   fronted: set[tuple[str, str | None]]) -> None:
    """엔드포인트마다 exposure를 [{environment, value}]로 쓴다. route가 없는 환경은 넣지 않는다."""
    envs = sorted({r.environment for r in routes if r.target}, key=lambda e: (e is not None, e or ""))
    for env in envs:
        values = _exposure_in(env, out, routes, servers, fronted_in(fronted, env))
        for ep in out:
            if ep["id"] in values:
                ep.setdefault("exposure", []).append({"environment": env, "value": values[ep["id"]]})


def extract_endpoints(snap: Snapshot, workloads: list[WorkloadInfo], routes: list[ProxyRoute] | None = None,
                      servers: list[ProxyServer] | None = None,
                      fronted: set[tuple[str, str | None]] | None = None,
                      manifests: Manifests | None = None) -> list[dict]:
    """fronted: 앞 구간이 있는 (프록시 id, 환경 이름). 프록시 체인이 거기서 끝난다(paths.fronted_proxies).
    manifests: Express 계열 서버 변수·framework 판정에 쓰는 의존성(없으면 여기서 읽는다)."""
    # 엔드포인트는 web 워크로드에만 배정한다(리버스 프록시·정적 프런트엔드 제외)
    webs = [w for w in workloads if w.kind == "web"]
    if not webs:
        return []
    if manifests is None:
        manifests = parse_manifests(snap)
    found = sorted(set(_python(snap) + _django(snap) + _express(snap, manifests) + _next(snap)),
                   key=lambda r: (r[2], r[3], r[0], r[1], r[4]))
    # 같은 (메서드, 경로, 파일, 줄)은 하나만 둔다
    seen: set[tuple[str, str, str, int]] = set()
    raw = []
    for r in found:
        if r[:4] not in seen:
            seen.add(r[:4])
            raw.append(r)
    counters: dict[str, int] = defaultdict(int)
    out: list[dict] = []
    for method, route, rel, line, framework in raw:
        # 여러 워크로드가 같은 코드를 쓰면 근거가 있는 워크로드마다 하나씩, 없으면 점수·대체 규칙
        owners = _owners(rel, webs)
        # 하나뿐인 Dockerfile로 추측한 code_root로 정한 소유자는 후보다
        targets = [(w, not w.root_guessed) for w in owners] if owners else [_assign(rel, webs)]
        for w, sure in targets:
            counters[w.id] += 1
            out.append({"id": f"ep-{w.id[2:]}-{counters[w.id]:03d}", "workload": w.id, "method": method,
                        "route": route, "handler": evidence(snap, rel, line), "framework": framework,
                        "status": "confirmed" if sure else "candidate"})
    if routes:
        _mark_exposure(out, routes, servers or [], fronted or set())
    return out
