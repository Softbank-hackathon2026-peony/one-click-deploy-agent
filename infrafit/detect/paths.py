"""요청 경로: 엣지 → 로드밸런서 → 앱 서버 (설계 §6.6)."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from infrafit import kb
from infrafit.detect.artifacts import ParsedArtifact, _d, build_source, ingress_backends
from infrafit.detect.defaults import hop_settings
from infrafit.detect.workloads import WorkloadInfo
from infrafit.evidence import evidence
from infrafit.repo import Snapshot

EDGE_BY_FILE = {
    "vercel.json": "nw:vercel/edge-proxy/default",
    "netlify.toml": "nw:netlify/edge-proxy/default",
    "fly.toml": "nw:fly/proxy/default",
    "render.yaml": "nw:render/proxy/default",
    "railway.json": "nw:railway/proxy/default",
    "railway.toml": "nw:railway/proxy/default",
    "railway.ts": "nw:railway/proxy/default",
}
LB_BY_CLASS = {"alb": "nw:aws/alb/default", "gce": "nw:gcp/classic-alb/gke-ingress", "nginx": "nw:k8s/ingress-nginx/default"}
MANAGED_RUNTIME_PREFIXES = ("cp:vercel/", "cp:netlify/")
_ALB_IDLE = re.compile(r"idle_timeout\.timeout_seconds=(\d+)")


def app_server(command: str) -> tuple[str, dict] | None:
    cmd = command.strip() if isinstance(command, str) else ""
    if "uvicorn" in cmd:
        m = re.search(r"--timeout-keep-alive[ =](\d+)", cmd)
        return "nw:app/uvicorn/default", ({"timeout_keep_alive": int(m.group(1))} if m else {})
    if "gunicorn" in cmd:
        m = re.search(r"--keep-?alive[ =](\d+)", cmd)
        return "nw:app/gunicorn/default", ({"keepalive": int(m.group(1))} if m else {})
    if "next start" in cmd:
        return "nw:app/next-start/default", {}
    if "flask run" in cmd:
        return "nw:app/flask-dev/default", {}
    if "manage.py runserver" in cmd:
        return "nw:app/django-runserver/default", {}
    if cmd.startswith(("node ", "npm start")):
        return "nw:app/node-http/default", {}
    return None


def _hop(kind: str, component: str, explicit: dict, ev: list[dict]) -> dict:
    return {"order": 0, "kind": kind, "component": component, "osi_layer": "L7",
            "settings": hop_settings(component, explicit, kb.defaults()), "evidence": ev}


def _edge(snap: Snapshot, artifacts: list[ParsedArtifact]) -> dict | None:
    for art in artifacts:
        if art.kind == "platform-config":
            comp = EDGE_BY_FILE.get(PurePosixPath(art.path).name)
            if comp:
                return _hop("edge-proxy", comp, {}, [evidence(snap, art.path)])
    return None


def _load_balancer(snap: Snapshot, w: WorkloadInfo, artifacts: list[ParsedArtifact]) -> dict | None:
    # 경로 순으로 보아 실제 파일이 kustomize 렌더(#build)보다 먼저 나오게 한다.
    for art in sorted(artifacts, key=lambda a: a.path):
        if art.kind != "k8s":
            continue
        for doc in art.objects if isinstance(art.objects, list) else []:
            if not isinstance(doc, dict) or doc.get("kind") != "Ingress" or w.name not in ingress_backends(doc):
                continue
            annotations = _d(_d(doc.get("metadata")).get("annotations"))
            cls = _d(doc.get("spec")).get("ingressClassName") or annotations.get("kubernetes.io/ingress.class")
            comp = LB_BY_CLASS.get(str(cls), "unmapped")
            explicit = {}
            m = _ALB_IDLE.search(str(annotations.get("alb.ingress.kubernetes.io/load-balancer-attributes", "")))
            if comp == "nw:aws/alb/default" and m:
                explicit["idle_timeout"] = int(m.group(1))
            # 렌더 결과(#build)는 실제 파일이 아니므로 kustomization.yaml을 근거로 쓴다
            return _hop("load-balancer", comp, explicit, [evidence(snap, build_source(art.path))])
    return None


def build_paths(snap: Snapshot, workloads: list[WorkloadInfo], artifacts: list[ParsedArtifact],
                compute: dict[str, str]) -> list[dict]:
    paths = []
    for w in sorted(workloads, key=lambda w: w.id):
        if w.kind != "web":
            continue
        hops = [h for h in (_edge(snap, artifacts), _load_balancer(snap, w, artifacts)) if h]
        if not str(compute.get(w.id, "")).startswith(MANAGED_RUNTIME_PREFIXES):
            server = app_server(w.command)
            if server:
                hops.append(_hop("app-server", server[0], server[1], [w.entrypoint]))
        for i, hop in enumerate(hops):
            hop["order"] = i
        paths.append({"id": f"path-{w.id[2:]}", "workload": w.id, "hops": hops})
    return paths
