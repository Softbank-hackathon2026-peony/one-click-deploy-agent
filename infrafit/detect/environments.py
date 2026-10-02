"""환경: kustomize 환경 overlay(말단, 또는 overlays 아래의 환경 디렉터리) 하나가 환경 하나다."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath

from infrafit.detect.artifacts import ParsedArtifact, _d, build_source, is_build_path
from infrafit.detect.workloads import WorkloadInfo, slug
from infrafit.evidence import evidence
from infrafit.repo import Snapshot

WORKLOAD_KINDS = {"Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob"}


@dataclass
class Environment:
    name: str
    source: str  # 실제 kustomization.yaml 경로
    rendered: bool
    objects: list[dict] = field(default_factory=list)

    def to_dict(self, snap: Snapshot) -> dict:
        return {"name": self.name, "rendered": self.rendered, "source": evidence(snap, self.source)}


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


def detect_environments(artifacts: list[ParsedArtifact]) -> list[Environment]:
    built = sorted((a for a in artifacts if is_build_path(a.path)), key=lambda a: a.path)
    names = [_env_name(_leaf_dir(build_source(a.path))) for a in built]
    envs = []
    for art, name in zip(built, names):
        source = build_source(art.path)
        if names.count(name) > 1:  # 이름이 겹치면 leaf 경로 전체로 구분한다
            name = _leaf_dir(source)
        objects = [o for o in art.objects if isinstance(o, dict)] if art.parsed and isinstance(art.objects, list) else []
        envs.append(Environment(name or "root", source, bool(art.parsed), objects))
    return sorted(envs, key=lambda e: e.name)


def env_slug(name: str) -> str:
    return slug(name.replace("/", "-"))


def workload_in(env: Environment, w: WorkloadInfo) -> bool:
    for doc in env.objects:
        if not isinstance(doc, dict) or doc.get("kind") not in WORKLOAD_KINDS:
            continue
        meta = _d(doc.get("metadata"))
        if meta.get("name") == w.name or _d(meta.get("labels")).get("app.kubernetes.io/name") == w.name:
            return True
    return False
