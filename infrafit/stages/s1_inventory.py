"""S1 인벤토리: 무엇이 있는가(설계 §6)."""

from __future__ import annotations

from infrafit import kb
from infrafit.detect.artifacts import kustomize_identity, parse_artifacts
from infrafit.detect.components import find_unmapped, image_unmapped, map_components
from infrafit.detect.defaults import apply_defaults
from infrafit.detect.environments import detect_environments
from infrafit.detect.endpoints import extract_endpoints
from infrafit.detect.images import image_services
from infrafit.detect.manifests import parse_manifests
from infrafit.detect.nginx import find_proxies
from infrafit.detect.paths import build_paths, fronted_proxies
from infrafit.detect.signatures import match_signatures
from infrafit.detect.workloads import detect_workloads
from infrafit.repo import Snapshot, content_digest
from infrafit.run import RunContext, code_version, input_hash, now_iso


def run_s1(ctx: RunContext, snap: Snapshot) -> dict:
    started = now_iso()
    # 커밋이 아니라 스캔한 파일 내용으로 키를 만든다: 커밋되지 않은 변경도 결과를 바꾼다
    h = input_hash("S1", content_digest(snap.root, snap.files), kustomize_identity(),
                   kb.kb_version(), code_version())
    cached = ctx.cached("S1", h)
    if cached is not None:
        return cached
    manifests = parse_manifests(snap)
    artifacts = parse_artifacts(snap)
    apply_defaults(artifacts, kb.defaults())
    workloads = detect_workloads(snap, manifests, artifacts)
    environments = detect_environments(artifacts, workloads)
    servers, routes = find_proxies(snap, workloads, artifacts, environments)
    endpoints = extract_endpoints(snap, workloads, routes, servers,
                                  fronted_proxies(snap, workloads, artifacts, environments, servers), manifests)
    matches = match_signatures(snap, manifests, kb.signatures())
    services = image_services(snap, artifacts)
    datastores, components, compute = map_components(snap, matches, workloads, artifacts, services)
    body = {
        "workloads": [w.to_dict() for w in workloads],
        "endpoints": endpoints,
        "datastores": datastores,
        "current_components": components,
        "request_paths": build_paths(snap, workloads, artifacts, compute, environments, (servers, routes)),
        "environments": [e.to_dict(snap) for e in environments],
        "existing_artifacts": [a.to_dict() for a in artifacts],
        "unmapped": find_unmapped(snap, manifests) + image_unmapped(services),
    }
    return ctx.write_stage("S1", body, input_hash=h, started_at=started)
