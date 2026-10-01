"""기존 산출물(Dockerfile, compose, k8s, Terraform, 플랫폼 설정, CI) 파싱."""

from __future__ import annotations

import json
import posixpath
import shutil
import subprocess
import tomllib
from dataclasses import dataclass, field
from pathlib import PurePosixPath

import hcl2
import yaml

from infrafit.detect.manifests import parent_dir
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
        art.settings.append(_fact(snap, rel, "base_image", next((t for t in froms[-1][1].split() if not t.startswith("--")), ""), froms[-1][2]))
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
    if not isinstance(data, dict):
        return ParsedArtifact("compose", rel, False)
    services = data.get("services")
    if not isinstance(services, dict):
        services = {}
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
    if not isinstance(data, dict):
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
    if not isinstance(data, dict):
        return ParsedArtifact("ci", rel, False)
    jobs = data.get("jobs")
    if not isinstance(jobs, dict):
        jobs = {}
    uses = sorted({step["uses"] for job in jobs.values() if isinstance(job, dict)
                   for step in (job["steps"] if isinstance(job.get("steps"), list) else [])
                   if isinstance(step, dict) and "uses" in step})
    art = ParsedArtifact("ci", rel, True, objects=[("workflow", data)])
    art.settings.append(_fact(snap, rel, "jobs", sorted(jobs)))
    art.settings.append(_fact(snap, rel, "uses", uses))
    return art


# --- 쿠버네티스 ---------------------------------------------------------------

def _d(v) -> dict:
    """dict가 아닌 값(None, 리스트, 문자열 등)은 빈 dict로 본다."""
    return v if isinstance(v, dict) else {}


def pod_spec(doc: dict) -> dict:
    kind = doc.get("kind")
    spec = _d(doc.get("spec"))
    if kind == "CronJob":
        spec = _d(_d(spec.get("jobTemplate")).get("spec"))
    if kind in ("Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob"):
        return _d(_d(spec.get("template")).get("spec"))
    return {}


def ingress_backends(doc: dict) -> list[str]:
    spec = _d(doc.get("spec"))
    names = set()
    default = _d(_d(spec.get("defaultBackend")).get("service")).get("name")
    if isinstance(default, str) and default:
        names.add(default)
    rules = spec.get("rules")
    for rule in rules if isinstance(rules, list) else []:
        paths = _d(_d(rule).get("http")).get("paths")
        for path in paths if isinstance(paths, list) else []:
            name = _d(_d(_d(path).get("backend")).get("service")).get("name")
            if isinstance(name, str) and name:
                names.add(name)
    return sorted(names)


def _k8s_settings(snap: Snapshot, rel: str, doc: dict) -> list[dict]:
    kind = doc["kind"]
    meta = _d(doc.get("metadata"))
    prefix = f"{kind}/{meta.get('name', '?')}"
    spec = _d(doc.get("spec"))
    out: list[dict] = []

    def add(key: str, value) -> None:
        out.append(_fact(snap, rel, f"{prefix}.{key}", value))

    if kind in ("Deployment", "StatefulSet") and "replicas" in spec:
        add("replicas", spec["replicas"])
    pod = pod_spec(doc)
    if pod:
        if "terminationGracePeriodSeconds" in pod:
            add("terminationGracePeriodSeconds", pod["terminationGracePeriodSeconds"])
        containers = pod.get("containers")
        c = containers[0] if isinstance(containers, list) and containers else None
        if isinstance(c, dict):
            if c.get("image"):
                add("image", c["image"])
            parts = [v if isinstance(v, list) else [] for v in (c.get("command"), c.get("args"))]
            cmd = [str(x) for x in parts[0] + parts[1]]
            if cmd:
                add("command", " ".join(cmd))
            add("readinessProbe", "readinessProbe" in c)
            add("livenessProbe", "livenessProbe" in c)
            add("preStop", bool(_d(c.get("lifecycle")).get("preStop")))
    if kind == "CronJob":
        for key in ("schedule", "concurrencyPolicy"):
            if key in spec:
                add(key, spec[key])
    if kind == "Ingress":
        annotations = _d(meta.get("annotations"))
        cls = spec.get("ingressClassName") or annotations.get("kubernetes.io/ingress.class")
        if cls:
            add("ingressClassName", cls)
        for k, v in sorted(annotations.items()):
            add(f"annotations.{k}", v)
        add("backends", ingress_backends(doc))
    if kind == "HorizontalPodAutoscaler":
        for key in ("minReplicas", "maxReplicas"):
            if key in spec:
                add(key, spec[key])
    if kind == "PodDisruptionBudget":
        for key in ("minAvailable", "maxUnavailable"):
            if key in spec:
                add(key, spec[key])
    return out


def parse_k8s(snap: Snapshot, rel: str) -> ParsedArtifact | None:
    try:
        docs = [d for d in yaml.safe_load_all(snap.read(rel)) if isinstance(d, dict)]
    except yaml.YAMLError:
        return None
    docs = [d for d in docs if "kind" in d and "apiVersion" in d]
    if not docs:
        return None
    art = ParsedArtifact("k8s", rel, True, objects=docs)
    for doc in docs:
        art.settings.extend(_k8s_settings(snap, rel, doc))
    return art


# --- Terraform ----------------------------------------------------------------

def parse_terraform(snap: Snapshot, rel: str) -> ParsedArtifact:
    try:
        data = hcl2.loads(snap.read(rel))
    except Exception:  # python-hcl2는 파싱 오류마다 다른 예외를 낸다
        return ParsedArtifact("terraform", rel, False)
    art = ParsedArtifact("terraform", rel, True)
    for block in data.get("resource") or []:
        for rtype, named in _d(block).items():
            rtype = _unquote(rtype)  # 이 버전은 블록 레이블의 따옴표를 유지한다
            for rname, attrs in _d(named).items():
                rname = _unquote(rname)
                attrs = attrs[0] if isinstance(attrs, list) and attrs else attrs
                art.objects.append((rtype, rname, attrs))
                for key, value in sorted(flatten(attrs).items()):
                    art.settings.append(_fact(snap, rel, f"{rtype}.{rname}.{key}", value))
    for block in data.get("provider") or []:
        for pname, attrs in _d(block).items():
            pname = _unquote(pname)
            attrs = attrs[0] if isinstance(attrs, list) and attrs else attrs
            attrs = _d(attrs)
            region = _unquote(attrs.get("region"))
            alias = _unquote(attrs.get("alias"))
            if region:
                key = f"provider.{pname}.{alias}.region" if alias else f"provider.{pname}.region"
                art.settings.append(_fact(snap, rel, key, region))
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


# --- kustomize ----------------------------------------------------------------

KUSTOMIZATION_NAMES = ("kustomization.yaml", "kustomization.yml", "Kustomization")
KUSTOMIZE_TIMEOUT = 60
BUILD_SUFFIX = "#build"


def is_build_path(path: str) -> bool:
    """kustomize 렌더 결과의 가상 경로(`<dir>/kustomization.yaml#build`)인가."""
    return path.endswith(BUILD_SUFFIX)


def build_source(path: str) -> str:
    """렌더 결과면 근거로 쓸 실제 kustomization.yaml 경로, 아니면 그대로."""
    return path[: -len(BUILD_SUFFIX)] if is_build_path(path) else path


def kustomize_binary() -> list[str] | None:
    if shutil.which("kustomize"):
        return ["kustomize", "build"]
    if shutil.which("kubectl"):
        return ["kubectl", "kustomize"]
    return None


def kustomize_identity() -> str:
    """캐시 키용: 사용할 kustomize 실행 파일 경로와 버전 출력, 없으면 "none"."""
    cmd = kustomize_binary()
    if cmd is None:
        return "none"
    path = shutil.which(cmd[0]) or cmd[0]
    version_cmd = [path, "version"] if cmd[0] == "kustomize" else [path, "version", "--client"]
    try:
        result = subprocess.run(version_cmd, capture_output=True, text=True, timeout=KUSTOMIZE_TIMEOUT)
        version = (result.stdout + result.stderr).strip()
    except (subprocess.TimeoutExpired, OSError):
        version = "unknown"
    return f"{path} {version}"


def _kustomization_files(snap: Snapshot) -> dict[str, str]:
    """디렉터리 → kustomization 파일 경로."""
    out: dict[str, str] = {}
    for rel in snap.files:
        if PurePosixPath(rel).name in KUSTOMIZATION_NAMES:
            out.setdefault(parent_dir(rel), rel)
    return out


def kustomize_leaves(snap: Snapshot) -> list[str]:
    files = _kustomization_files(snap)
    referenced: set[str] = set()
    for d, rel in files.items():
        try:
            data = yaml.safe_load(snap.read(rel)) or {}
        except yaml.YAMLError:
            continue
        if not isinstance(data, dict):
            continue
        for key in ("resources", "bases", "components"):
            items = data.get(key)
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, str):
                    continue
                target = posixpath.normpath(posixpath.join(d, item))
                if target == ".":
                    target = ""
                if target in files:
                    referenced.add(target)
    return sorted(d for d in files if d not in referenced)


def build_overlays(snap: Snapshot, runner=subprocess.run) -> list[ParsedArtifact]:
    cmd = kustomize_binary()
    if cmd is None:
        return []
    out: list[ParsedArtifact] = []
    for d in kustomize_leaves(snap):
        rel = (f"{d}/kustomization.yaml" if d else "kustomization.yaml") + BUILD_SUFFIX
        result = runner(cmd + [str(snap.root / d)], capture_output=True, text=True)
        if result.returncode != 0:
            out.append(ParsedArtifact("k8s", rel, False))
            continue
        try:
            docs = [x for x in yaml.safe_load_all(result.stdout)
                    if isinstance(x, dict) and "kind" in x and "apiVersion" in x]
        except yaml.YAMLError:
            out.append(ParsedArtifact("k8s", rel, False))
            continue
        art = ParsedArtifact("k8s", rel, True, objects=docs)
        for doc in docs:
            art.settings.extend(_k8s_settings(snap, rel, doc))
        out.append(art)
    return out


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
        elif kind == "terraform":
            out.append(parse_terraform(snap, rel))
        elif kind == "k8s?":
            art = parse_k8s(snap, rel)
            if art is not None:
                out.append(art)
    out.extend(build_overlays(snap))
    return sorted(out, key=lambda a: a.path)
