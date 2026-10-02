"""환경: kustomize 환경 overlay(말단, 또는 overlays 아래의 환경 디렉터리) 하나, compose 설정(기본 파일과
override, 또는 그 위의 변형 파일) 하나가 각각 환경 하나다."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath

import yaml

from infrafit.detect.artifacts import ParsedArtifact, as_dict, build_source, is_build_path, pod_spec
from infrafit.detect.manifests import parent_dir
from infrafit.detect.workloads import (WorkloadInfo, compose_build, compose_command, image_name, slug,
                                       workload_dockerfile)
from infrafit.evidence import evidence
from infrafit.repo import Snapshot

WORKLOAD_KINDS = {"Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob"}
# 한 디렉터리에 기본 파일이 여럿이면 docker compose와 같은 순서로 하나를 고른다
COMPOSE_BASE_NAMES = ("compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml")
COMPOSE_PREFIXES = ("docker-compose.", "compose.")
OVERRIDE = "override"


@dataclass
class Environment:
    name: str
    source: str  # 실제 kustomization.yaml 경로, compose 환경이면 기본 파일 또는 변형 파일
    rendered: bool
    objects: list[dict] = field(default_factory=list)
    kind: str = "kustomize"  # "kustomize" | "compose"
    services: dict[str, dict] = field(default_factory=dict)  # compose 환경의 병합된 서비스 정의
    members: dict[str, str] = field(default_factory=dict)  # compose 환경: 워크로드 id → 서비스 이름
    origins: dict[str, dict[str, str]] = field(default_factory=dict)  # 서비스 → 키 → 그 값을 정한 compose 파일

    def to_dict(self, snap: Snapshot) -> dict:
        return {"name": self.name, "kind": self.kind, "rendered": self.rendered,
                "source": evidence(snap, self.source)}


def _leaf_dir(source: str) -> str:
    parent = str(PurePosixPath(source).parent)
    return "" if parent == "." else parent


def _env_name(leaf: str) -> str:
    """마지막 `overlays/`까지 뗀 나머지. `overlays/`가 없으면 leaf 경로 전체."""
    parts = leaf.split("/") if leaf else []
    for i in range(len(parts) - 1, -1, -1):
        if parts[i] == "overlays":
            return "/".join(parts[i + 1:]) or leaf
    return leaf


def _kustomize_environments(artifacts: list[ParsedArtifact]) -> list[Environment]:
    built = sorted((a for a in artifacts if is_build_path(a.path)), key=lambda a: a.path)
    names = [_env_name(_leaf_dir(build_source(a.path))) for a in built]
    envs = []
    for art, name in zip(built, names):
        source = build_source(art.path)
        if names.count(name) > 1:  # 이름이 겹치면 leaf 경로 전체로 구분한다
            name = _leaf_dir(source)
        objects = [o for o in art.objects if isinstance(o, dict)] if art.parsed and isinstance(art.objects, list) else []
        envs.append(Environment(name or "root", source, bool(art.parsed), objects))
    return envs


# --- compose -------------------------------------------------------------------

def _variant(rel: str) -> str | None:
    """compose 파일 이름의 변형 부분: 기본 파일이면 "", `docker-compose.<x>.yml`이면 x, 그 밖의 이름은 None."""
    name = PurePosixPath(rel).name
    if name in COMPOSE_BASE_NAMES:
        return ""
    for prefix in COMPOSE_PREFIXES:
        for suffix in (".yml", ".yaml"):
            if name.startswith(prefix) and name.endswith(suffix) and len(name) > len(prefix) + len(suffix):
                return name[len(prefix):-len(suffix)]
    return None


def _is_override(variant: str | None) -> bool:
    """`docker-compose.override.yml`·`compose.override.yaml` 등: 기본 파일 위에 늘 병합하는 파일(docker 동작).
    `compose.prod.override.yml` 같은 이름은 변형 파일이다."""
    return variant == OVERRIDE


def _env_vars(value) -> dict | None:
    """compose `environment`(목록 또는 맵) → 변수 이름 → 값. 둘 다 아니면 None."""
    if isinstance(value, dict):
        return {str(k): v for k, v in value.items()}
    if isinstance(value, list):
        out = {}
        for item in value:
            k, sep, v = str(item).partition("=")
            if k:
                out[k] = v if sep else None
        return out
    return None


def _merge(files: list[ParsedArtifact]) -> tuple[dict[str, dict], dict[str, dict[str, str]]]:
    """서비스 단위 병합: 뒤 파일의 키가 앞 파일의 키를 덮고, `environment`는 변수 이름 단위로 합친다.
    (병합된 서비스, 서비스 → 키 → 마지막으로 그 키를 쓴 파일)."""
    services: dict[str, dict] = {}
    origins: dict[str, dict[str, str]] = {}
    for art in files:
        if not art.parsed or not isinstance(art.objects, list):
            continue
        for obj in art.objects:
            if not isinstance(obj, tuple) or len(obj) != 2 or not isinstance(obj[0], str):
                continue
            merged = services.setdefault(obj[0], {})
            origin = origins.setdefault(obj[0], {})
            for key, value in as_dict(obj[1]).items():
                origin[str(key)] = art.path
                new = _env_vars(value) if key == "environment" else None
                old = _env_vars(merged.get(key)) if key == "environment" and key in merged else None
                if new is not None:
                    merged[key] = {**old, **new} if old is not None else new
                else:
                    merged[key] = value
    return services, origins


def _compose_environments(artifacts: list[ParsedArtifact]) -> list[Environment]:
    by_dir: dict[str, list[ParsedArtifact]] = {}
    for art in sorted((a for a in artifacts if a.kind == "compose"), key=lambda a: a.path):
        by_dir.setdefault(parent_dir(art.path), []).append(art)
    envs: list[Environment] = []
    for d, files in sorted(by_dir.items()):
        bases = sorted((a for a in files if _variant(a.path) == ""),
                       key=lambda a: COMPOSE_BASE_NAMES.index(PurePosixPath(a.path).name))
        overrides = [a for a in files if _is_override(_variant(a.path))]
        variants = [a for a in files if _variant(a.path) and not _is_override(_variant(a.path))]
        layers = (bases[:1] + overrides) if bases else []
        candidates = ([("compose", bases[0], layers)] if bases else []) + [
            (f"compose.{_variant(v.path)}", v, layers + [v]) for v in variants]
        for name, source, chain in candidates:
            services, origins = _merge(chain)
            if not services:
                continue
            envs.append(Environment(f"{name}/{d}" if d else name, source.path, True, kind="compose",
                                    services=services, origins=origins))
    # 이름이 겹치면(docker-compose.x.yml과 compose.x.yml) 경로 순 첫 번째만 둔다
    unique: dict[str, Environment] = {}
    for env in envs:
        unique.setdefault(env.name, env)
    return list(unique.values())


def _service_dockerfile(env: Environment, svc: dict) -> str | None:
    build = compose_build(env.source, svc)
    return build[1] if build else None


def _match_services(env: Environment, workloads: list[WorkloadInfo], artifacts: list[ParsedArtifact]) -> None:
    """서비스 ↔ 워크로드: 이름이 같으면 대응하고, 남은 것끼리는 같은 Dockerfile이나 같은 이미지 이름으로
    서로 유일한 후보일 때만 대응한다."""
    names = set(env.services)
    for w in workloads:
        if w.name in names:
            env.members[w.id] = w.name
    taken = set(env.members.values())
    rest_services = sorted(n for n in env.services if n not in taken)
    rest = [w for w in workloads if w.id not in env.members]
    wanted = {}
    for w in rest:
        df = workload_dockerfile(w, artifacts)
        wanted[w.id] = (df.path if df else None, image_name(w.image) if w.image else "")
    pairs = set()
    for n in rest_services:
        svc = as_dict(env.services[n])
        svc_df = _service_dockerfile(env, svc)
        svc_image = image_name(str(svc.get("image") or "")) if isinstance(svc.get("image"), str) else ""
        for w in rest:
            df, image = wanted[w.id]
            if (svc_df and svc_df == df) or (svc_image and svc_image == image):
                pairs.add((n, w.id))
    for n, wid in sorted(pairs):
        if sum(1 for p in pairs if p[1] == wid) == 1 and sum(1 for p in pairs if p[0] == n) == 1:
            env.members[wid] = n


def detect_environments(artifacts: list[ParsedArtifact], workloads: list[WorkloadInfo]) -> list[Environment]:
    kustomize = _kustomize_environments(artifacts)
    taken = {e.name for e in kustomize}
    compose = _compose_environments(artifacts)
    for env in compose:
        if env.name in taken:  # kustomize 환경과 이름이 겹치면 compose 쪽에 원본 디렉터리를 붙인다
            env.name = f"{env.name}@{parent_dir(env.source) or 'root'}"
        _match_services(env, workloads, artifacts)
    return sorted(kustomize + compose, key=lambda e: e.name)


def env_slug(name: str) -> str:
    return slug(name.replace("/", "-"))


def is_workload_doc(doc, w: WorkloadInfo) -> bool:
    """매니페스트 객체가 워크로드 w의 객체인가: 워크로드 종류이고 이름이나 app.kubernetes.io/name 라벨이 같다."""
    if not isinstance(doc, dict) or doc.get("kind") not in WORKLOAD_KINDS:
        return False
    meta = as_dict(doc.get("metadata"))
    return meta.get("name") == w.name or as_dict(meta.get("labels")).get("app.kubernetes.io/name") == w.name


def workload_in(env: Environment, w: WorkloadInfo) -> bool:
    if env.kind == "compose":
        return w.id in env.members
    return any(is_workload_doc(doc, w) for doc in env.objects)


def env_service(env: Environment | None, w: WorkloadInfo) -> dict | None:
    """compose 환경에서 워크로드에 대응한 서비스 정의. 대응이 없거나 compose 환경이 아니면 None."""
    if env is None or env.kind != "compose" or w.id not in env.members:
        return None
    return as_dict(env.services.get(env.members[w.id]))


def env_scopes(w: WorkloadInfo, environments: list[Environment]) -> list[Environment | None]:
    """워크로드를 볼 범위(None은 환경 밖). 렌더된 환경 중 워크로드가 있는 것들.
    k8s 워크로드가 kustomize 환경에 없으면 일반 매니페스트(환경 밖)에도 있으므로 None도 둔다.
    그 밖의 워크로드는 어느 환경에도 없을 때만 None."""
    inside = [e for e in environments if e.rendered and workload_in(e, w)]
    if w.source == "k8s" and not any(e.kind == "kustomize" for e in inside):
        return [None] + inside
    return inside or [None]


def _rendered_command(env: Environment, w: WorkloadInfo) -> str:
    doc = next((d for d in env.objects if is_workload_doc(d, w)), None)
    containers = pod_spec(doc).get("containers") if doc is not None else None
    containers = [as_dict(c) for c in containers] if isinstance(containers, list) else []
    c = next((x for x in containers if w.image and x.get("image") == w.image), containers[0] if containers else {})
    parts = [v if isinstance(v, list) else [] for v in (c.get("command"), c.get("args"))]
    return " ".join(str(x) for x in parts[0] + parts[1])


def env_command(env: Environment | None, w: WorkloadInfo, artifacts: list[ParsedArtifact]) -> str:
    """그 환경에서 워크로드가 실행하는 명령. 환경이 정하지 않으면 워크로드의 명령."""
    cmd = ""
    if env is not None and env.kind == "compose":
        svc = env_service(env, w)
        cmd = compose_command(env.source, svc, artifacts) if svc is not None else ""
    elif env is not None:
        cmd = _rendered_command(env, w)
    return cmd or w.command


def _compose_key_line(snap: Snapshot, rel: str, service: str, key: str) -> int | None:
    """compose 파일에서 services.<service>.<key> 키가 있는 줄."""
    try:
        root = yaml.compose(snap.read(rel))
    except yaml.YAMLError:
        return None
    for path_key in ("services", service, key):
        if not isinstance(root, yaml.MappingNode):
            return None
        found = next(((k, v) for k, v in root.value if isinstance(k, yaml.ScalarNode) and k.value == path_key), None)
        if found is None:
            return None
        if path_key == key:
            return found[0].start_mark.line + 1
        root = found[1]
    return None


def env_command_evidence(snap: Snapshot, env: Environment | None, w: WorkloadInfo,
                         artifacts: list[ParsedArtifact]) -> list[dict]:
    """env_command가 어디서 왔는가: compose 서비스 `command` 줄(없으면 빌드 Dockerfile의 ENTRYPOINT·CMD 줄),
    kustomize 환경의 렌더 명령이 워크로드 명령과 다르면 그 kustomization.yaml, 그 밖에는 워크로드 진입점."""
    if env is not None and env.kind == "compose":
        svc = env_service(env, w)
        name = env.members.get(w.id)
        if svc is not None and isinstance(svc.get("command"), (str, list)) and svc.get("command"):
            rel = env.origins.get(name, {}).get("command", env.source)
            return [evidence(snap, rel, _compose_key_line(snap, rel, name, "command"))]
        build = compose_build(env.source, svc) if svc is not None else None
        df = next((a for a in artifacts if a.kind == "dockerfile" and a.path == build[1]), None) if build else None
        evs = [f["evidence"] for f in (df.settings if df else [])
               if f.get("key") in ("entrypoint", "cmd") and f.get("evidence")]
        if evs:
            return sorted(evs, key=lambda e: e["line"] or 0)
    elif env is not None:
        cmd = _rendered_command(env, w)
        if cmd and cmd != w.command:
            return [evidence(snap, env.source)]
    return [w.entrypoint]
