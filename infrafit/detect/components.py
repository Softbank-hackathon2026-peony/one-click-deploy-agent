"""데이터 범위와 현재 구성 요소 매핑, 미매핑 의존성."""

from __future__ import annotations

from pathlib import PurePosixPath

from infrafit import kb
from infrafit.detect.artifacts import ParsedArtifact, _d, flatten
from infrafit.detect.manifests import Manifests, parent_dir
from infrafit.detect.signatures import Match
from infrafit.detect.workloads import WorkloadInfo, slug
from infrafit.evidence import evidence
from infrafit.repo import Snapshot

PLATFORM_COMPUTE = {
    "vercel.json": "cp:vercel/functions/unspecified-plan",
    "netlify.toml": "cp:netlify/functions/unspecified-plan",
    "fly.toml": "cp:fly/machines/default",
    "render.yaml": "cp:render/web/unspecified-plan",
    "railway.json": "cp:railway/service/unspecified-plan",
    "railway.toml": "cp:railway/service/unspecified-plan",
    "railway.ts": "cp:railway/service/unspecified-plan",
}
GENERIC_PROVIDERS = {"local", "unspecified", "lib"}


def scope_id(component: str, role: str) -> str:
    provider, product, _ = component.split(":", 1)[1].split("/")
    name = product if provider in GENERIC_PROVIDERS else f"{provider}-{product}"
    prefix = "ds" if role in ("primary-db", "search") else "svc"
    return f"{prefix}-{slug(name)}"


def _terraform_objects(artifacts: list[ParsedArtifact]):
    for art in artifacts:
        if art.kind == "terraform":
            for obj in art.objects:
                if isinstance(obj, (tuple, list)) and len(obj) == 3 and isinstance(obj[0], str):
                    yield obj[0], obj[1], obj[2], art.path


def _refine_hosting(component: str, artifacts: list[ParsedArtifact]) -> tuple[str, str | None]:
    for rtype, _, attrs, path in _terraform_objects(artifacts):
        flat = flatten(attrs)
        if component == "ds:unspecified/postgresql/default":
            if rtype == "aws_db_instance" and str(flat.get("engine", "")).startswith("postgres"):
                multi = flat.get("multi_az") in (True, "true")
                return ("ds:aws/rds-postgres/multi-az-instance" if multi else "ds:aws/rds-postgres/single-az"), path
            if rtype == "google_sql_database_instance" and str(flat.get("database_version", "")).startswith("POSTGRES"):
                ha = flat.get("settings.availability_type") == "REGIONAL"
                return ("ds:gcp/cloudsql-postgres/ha" if ha else "ds:gcp/cloudsql-postgres/single"), path
        if component == "ca:unspecified/redis/default":
            if rtype.startswith("aws_elasticache_"):
                return "ca:aws/elasticache/node-based", path
            if rtype == "google_redis_instance":
                return "ca:gcp/memorystore/redis", path
    return component, None


def _ep(w: WorkloadInfo) -> str | None:
    path = _d(w.entrypoint).get("path")
    return path if isinstance(path, str) else None


def _compute_for(w: WorkloadInfo, artifacts: list[ParsedArtifact]) -> tuple[str, str | None]:
    for art in sorted(artifacts, key=lambda a: a.path):
        if art.kind == "platform-config":
            comp = PLATFORM_COMPUTE.get(PurePosixPath(art.path).name)
            if comp:
                return comp, art.path
    tf_types = {rtype for rtype, _, _, _ in _terraform_objects(artifacts)}
    if w.source == "k8s":
        if "aws_eks_cluster" in tf_types:
            return "cp:aws/eks/unspecified", _ep(w)
        if "google_container_cluster" in tf_types:
            return "cp:gcp/gke/unspecified", _ep(w)
        return "cp:k8s/deployment/unspecified-cluster", _ep(w)
    if w.source == "compose":
        return "cp:local/compose/default", _ep(w)
    for target in (w.app_dir, ""):
        for art in artifacts:
            if art.kind == "dockerfile" and parent_dir(art.path) == target:
                return "cp:docker/container/unspecified-host", art.path
    return "unmapped", None


def _under(path: str, root: str) -> bool:
    return root == "" or path == root or path.startswith(root + "/")


def _users(evidence_items: list[dict], workloads: list[WorkloadInfo]) -> list[str]:
    backend = [w for w in workloads if w.kind != "static-frontend"]
    paths = {e["path"] for e in evidence_items}
    users = sorted(w.id for w in backend
                   if w.code_root is not None and any(_under(p, w.code_root) for p in paths))
    return users or sorted(w.id for w in backend)


def map_components(snap: Snapshot, matches: list[Match], workloads: list[WorkloadInfo],
                   artifacts: list[ParsedArtifact]) -> tuple[list[dict], list[dict], dict[str, str]]:
    scopes: dict[str, dict] = {}
    for m in matches:
        sid = scope_id(m.component, m.role)
        entry = scopes.setdefault(sid, {"role": m.role, "component": m.component, "status": m.status,
                                        "signatures": [], "evidence": []})
        entry["signatures"].append(m.signature)
        entry["evidence"].extend(m.evidence)
        if m.status == "confirmed":
            entry["status"] = "confirmed"

    datastores: list[dict] = []
    comps: list[dict] = []
    for sid in sorted(scopes):
        s = scopes[sid]
        component, tf_path = _refine_hosting(s["component"], artifacts)
        ev = list(s["evidence"])
        if tf_path:
            ev.append(evidence(snap, tf_path))
        datastores.append({"id": sid, "role": s["role"], "used_by": _users(s["evidence"], workloads),
                           "evidence": s["evidence"], "status": s["status"]})
        comps.append({"scope": sid, "component": component, "label": ",".join(s["signatures"]),
                      "settings": [], "evidence": ev, "status": s["status"]})

    compute: dict[str, str] = {}
    for w in sorted(workloads, key=lambda w: w.id):
        comp, path = _compute_for(w, artifacts)
        compute[w.id] = comp
        entry = {"scope": w.id, "component": comp, "settings": [], "status": "confirmed",
                 "evidence": [evidence(snap, path)] if path else []}
        if comp == "unmapped":
            entry["label"] = "no deployment config"
        comps.append(entry)
    return datastores, comps, compute


def find_unmapped(snap: Snapshot, manifests: Manifests) -> list[dict]:
    known = {leaf["dependency"].lower() for s in kb.signatures()
             for cond in [s["when"]] + [r["when"] for r in s.get("refine", [])]
             for leaf in kb.iter_conditions(cond) if "dependency" in leaf}
    out = []
    for name in kb.watchlist():
        if name in manifests.deps and name not in known:
            rel, line = manifests.deps[name]
            out.append({"label": name, "evidence": [evidence(snap, rel, line)]})
    return out
