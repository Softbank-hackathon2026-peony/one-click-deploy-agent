"""S1 인벤토리: 무엇이 있는가(설계 §6)."""

from __future__ import annotations

from infrafit import kb
from infrafit.detect.artifacts import parse_artifacts
from infrafit.detect.components import find_unmapped, map_components
from infrafit.detect.defaults import apply_defaults
from infrafit.detect.endpoints import extract_endpoints
from infrafit.detect.manifests import parse_manifests
from infrafit.detect.paths import build_paths
from infrafit.detect.signatures import match_signatures
from infrafit.detect.workloads import detect_workloads
from infrafit.repo import Snapshot
from infrafit.run import RunContext, code_version, input_hash, now_iso


def run_s1(ctx: RunContext, snap: Snapshot) -> dict:
    started = now_iso()
    h = input_hash("S1", snap.commit, kb.kb_version(), code_version())
    cached = ctx.cached("S1", h)
    if cached is not None:
        return cached
    manifests = parse_manifests(snap)
    artifacts = parse_artifacts(snap)
    apply_defaults(artifacts, kb.defaults())
    workloads = detect_workloads(snap, manifests, artifacts)
    endpoints = extract_endpoints(snap, workloads)
    matches = match_signatures(snap, manifests, kb.signatures())
    datastores, components, compute = map_components(snap, matches, workloads, artifacts)
    body = {
        "workloads": [w.to_dict() for w in workloads],
        "endpoints": endpoints,
        "datastores": datastores,
        "current_components": components,
        "request_paths": build_paths(snap, workloads, artifacts, compute),
        "existing_artifacts": [a.to_dict() for a in artifacts],
        "unmapped": find_unmapped(snap, manifests),
    }
    return ctx.write_stage("S1", body, input_hash=h, started_at=started)
