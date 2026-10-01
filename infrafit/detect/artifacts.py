"""기존 산출물(Dockerfile, compose, k8s, Terraform, 플랫폼 설정, CI) 파싱."""

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass, field
from pathlib import PurePosixPath

import yaml

from infrafit.evidence import evidence, line_of
from infrafit.repo import Snapshot

PLATFORM_FILES = {"vercel.json", "netlify.toml", "fly.toml", "render.yaml", "railway.json", "railway.toml"}


@dataclass
class ParsedArtifact:
    kind: str
    path: str
    parsed: bool
    settings: list[dict] = field(default_factory=list)
    objects: list = field(default_factory=list)

    def get(self, key: str, default=None):
        for s in self.settings:
            if s["key"] == key:
                return s["value"]
        return default

    def to_dict(self) -> dict:
        return {"kind": self.kind, "path": self.path, "parsed": self.parsed,
                "settings": sorted(self.settings, key=lambda s: s["key"])}


def _fact(snap: Snapshot, rel: str, key: str, value, line: int | None = None) -> dict:
    fact = {"key": key, "value": value, "defaulted": False}
    if line:
        fact["evidence"] = evidence(snap, rel, line)
    return fact


def _unquote(v):
    if isinstance(v, str) and len(v) >= 2 and v[0] == v[-1] == '"':
        return v[1:-1]
    return v


def _is_block_list(v) -> bool:
    return isinstance(v, list) and bool(v) and all(isinstance(x, dict) for x in v)


def flatten(obj, prefix: str = "", depth: int = 2) -> dict:
    if _is_block_list(obj):
        obj = obj[0]
    if not isinstance(obj, dict):
        return {prefix.rstrip("."): _unquote(obj)} if prefix else {}
    out: dict = {}
    for k, v in obj.items():
        if str(k).startswith("__"):
            continue
        key = f"{prefix}{k}"
        if isinstance(v, dict) or _is_block_list(v):
            if depth > 0:
                out.update(flatten(v, key + ".", depth - 1))
        elif isinstance(v, list):
            out[key] = [_unquote(x) for x in v]
        else:
            out[key] = _unquote(v)
    return out


# --- Dockerfile ---------------------------------------------------------------

def _exec_form(arg: str) -> str:
    if arg.startswith("["):
        try:
            return " ".join(str(x) for x in json.loads(arg))
        except json.JSONDecodeError:
            return arg
    return arg


def parse_dockerfile(snap: Snapshot, rel: str) -> ParsedArtifact:
    instrs: list[tuple[str, str, int]] = []
    buf, start = "", None
    for i, text in enumerate(snap.lines(rel), 1):
        s = text.strip()
        if not buf and (not s or s.startswith("#")):
            continue
        if start is None:
            start = i
        if s.endswith("\\"):
            buf += s[:-1].rstrip() + " "
            continue
        buf += s
        op, _, arg = buf.partition(" ")
        instrs.append((op.upper(), arg.strip(), start))
        buf, start = "", None
    art = ParsedArtifact("dockerfile", rel, True, objects=instrs)
    froms = [x for x in instrs if x[0] == "FROM"]
    if froms:
        art.settings.append(_fact(snap, rel, "base_image", froms[-1][1].split()[0], froms[-1][2]))
    art.settings.append(_fact(snap, rel, "stages", len(froms)))
    for key, op in (("user", "USER"), ("cmd", "CMD"), ("entrypoint", "ENTRYPOINT"),
                    ("expose", "EXPOSE"), ("healthcheck", "HEALTHCHECK")):
        found = [x for x in instrs if x[0] == op]
        if found:
            value = _exec_form(found[-1][1]) if op in ("CMD", "ENTRYPOINT") else found[-1][1]
            art.settings.append(_fact(snap, rel, key, value, found[-1][2]))
    return art


# --- compose ------------------------------------------------------------------

def parse_compose(snap: Snapshot, rel: str) -> ParsedArtifact:
    try:
        data = yaml.safe_load(snap.read(rel)) or {}
    except yaml.YAMLError:
        return ParsedArtifact("compose", rel, False)
    services = data.get("services") or {}
    art = ParsedArtifact("compose", rel, True,
                         objects=[(n, services[n] if isinstance(services[n], dict) else {}) for n in sorted(services)])
    for name, svc in art.objects:
        if "image" in svc:
            art.settings.append(_fact(snap, rel, f"services.{name}.image", svc["image"],
                                      line_of(snap, rel, f"image: {svc['image']}")))
        cmd = svc.get("command")
        if cmd:
            art.settings.append(_fact(snap, rel, f"services.{name}.command",
                                      " ".join(str(c) for c in cmd) if isinstance(cmd, list) else str(cmd)))
        if svc.get("ports"):
            art.settings.append(_fact(snap, rel, f"services.{name}.ports", [str(p) for p in svc["ports"]]))
    return art


# --- 플랫폼 설정 --------------------------------------------------------------

def parse_platform(snap: Snapshot, rel: str) -> ParsedArtifact:
    name = PurePosixPath(rel).name
    try:
        if name.endswith(".json"):
            data = json.loads(snap.read(rel) or "{}")
        elif name.endswith(".toml"):
            data = tomllib.loads(snap.read(rel))
        elif name.endswith((".yaml", ".yml")):
            data = yaml.safe_load(snap.read(rel)) or {}
        else:
            return ParsedArtifact("platform-config", rel, False)
    except (json.JSONDecodeError, tomllib.TOMLDecodeError, yaml.YAMLError):
        return ParsedArtifact("platform-config", rel, False)
    art = ParsedArtifact("platform-config", rel, True, objects=[(name, data)])
    for key, value in sorted(flatten(data).items()):
        art.settings.append(_fact(snap, rel, key, value))
    return art


# --- CI -----------------------------------------------------------------------

def parse_ci(snap: Snapshot, rel: str) -> ParsedArtifact:
    try:
        data = yaml.safe_load(snap.read(rel)) or {}
    except yaml.YAMLError:
        return ParsedArtifact("ci", rel, False)
    jobs = data.get("jobs") or {}
    uses = sorted({step["uses"] for job in jobs.values() if isinstance(job, dict)
                   for step in job.get("steps") or [] if isinstance(step, dict) and "uses" in step})
    art = ParsedArtifact("ci", rel, True, objects=[("workflow", data)])
    art.settings.append(_fact(snap, rel, "jobs", sorted(jobs)))
    art.settings.append(_fact(snap, rel, "uses", uses))
    return art


# --- 분류 ---------------------------------------------------------------------

def _classify(rel: str) -> str | None:
    p = PurePosixPath(rel)
    name = p.name
    if name == "Dockerfile" or name.startswith("Dockerfile.") or name.endswith(".Dockerfile"):
        return "dockerfile"
    if name in PLATFORM_FILES or rel == ".railway/railway.ts":
        return "platform-config"
    if rel.startswith(".github/workflows/") and name.endswith((".yml", ".yaml")):
        return "ci"
    if name.endswith((".yml", ".yaml")) and (name.startswith("docker-compose") or name.startswith("compose")):
        return "compose"
    if name.endswith(".tf"):
        return "terraform"
    if name.endswith((".yml", ".yaml")):
        return "k8s?"
    return None


def parse_artifacts(snap: Snapshot) -> list[ParsedArtifact]:
    out: list[ParsedArtifact] = []
    for rel in snap.files:
        kind = _classify(rel)
        if kind == "dockerfile":
            out.append(parse_dockerfile(snap, rel))
        elif kind == "compose":
            out.append(parse_compose(snap, rel))
        elif kind == "platform-config":
            out.append(parse_platform(snap, rel))
        elif kind == "ci":
            out.append(parse_ci(snap, rel))
    return sorted(out, key=lambda a: a.path)
