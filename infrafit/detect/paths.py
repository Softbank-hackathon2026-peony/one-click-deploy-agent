"""요청 경로: 엣지 → 로드밸런서 → 리버스 프록시 → 앱 서버 (설계 §6.6)."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from infrafit import kb
from infrafit.detect.artifacts import ParsedArtifact, _d, build_source, ingress_backends
from infrafit.detect.components import platform_config_for
from infrafit.detect.defaults import fact_settings, hop_settings
from infrafit.detect.environments import Environment, env_slug, workload_in
from infrafit.detect.nginx import ProxyRoute, ProxyServer
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
NGINX_PROXY = "nw:proxy/nginx/default"
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


def _edge(snap: Snapshot, w: WorkloadInfo, artifacts: list[ParsedArtifact]) -> dict | None:
    """이 워크로드의 컴퓨트를 정한 플랫폼 설정이 있을 때만 그 플랫폼의 엣지를 지난다."""
    config = platform_config_for(w, artifacts)
    comp = EDGE_BY_FILE.get(PurePosixPath(config.path).name) if config else None
    return _hop("edge-proxy", comp, {}, [evidence(snap, config.path)]) if comp else None


def _ingress_hop(snap: Snapshot, w: WorkloadInfo, objects: list, source: str) -> dict | None:
    for doc in objects if isinstance(objects, list) else []:
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
        return _hop("load-balancer", comp, explicit, [evidence(snap, build_source(source))])
    return None


def _load_balancer(snap: Snapshot, w: WorkloadInfo, artifacts: list[ParsedArtifact]) -> dict | None:
    # 경로 순으로 보아 실제 파일이 kustomize 렌더(#build)보다 먼저 나오게 한다.
    for art in sorted(artifacts, key=lambda a: a.path):
        if art.kind != "k8s":
            continue
        hop = _ingress_hop(snap, w, art.objects, art.path)
        if hop:
            return hop
    return None


def _proxy_hop(facts: list[dict], evs: list[dict | None]) -> dict:
    """리버스 프록시 구간: 설정은 근거가 달린 사실 그대로(같은 키도 값마다 하나씩) + 기본값."""
    seen, ev = set(), []
    for e in evs:
        if e and (e["path"], e["line"]) not in seen:
            seen.add((e["path"], e["line"]))
            ev.append(e)
    ev.sort(key=lambda e: (e["path"], e["line"] or 0))
    return {"order": 0, "kind": "reverse-proxy", "component": NGINX_PROXY, "osi_layer": "L7",
            "settings": fact_settings(NGINX_PROXY, facts, kb.defaults()), "evidence": ev}


def _front(snap: Snapshot, w: WorkloadInfo, artifacts: list[ParsedArtifact], env: Environment | None) -> list[dict]:
    """워크로드의 앞 구간(엣지·로드밸런서). env가 None이면 환경 밖 매니페스트에서 찾는다."""
    lb = _load_balancer(snap, w, artifacts) if env is None else _ingress_hop(snap, w, env.objects, env.source)
    return [h for h in (_edge(snap, w, artifacts), lb) if h]


def build_paths(snap: Snapshot, workloads: list[WorkloadInfo], artifacts: list[ParsedArtifact],
                compute: dict[str, str], environments: list[Environment],
                proxy: tuple[list[ProxyServer], list[ProxyRoute]] | None = None) -> list[dict]:
    """워크로드마다, 그 워크로드가 있는 렌더된 환경마다 경로 하나. 어느 환경에도 없으면 environment null 경로 하나.
    nginx 프록시 워크로드도 경로를 갖고, 자기 앞 구간이 없는 프록시 대상은 프록시를 거치는 경로를 갖는다."""
    servers, routes = proxy if proxy else ([], [])
    proxy_ids = {s.proxy for s in servers}
    by_id = {w.id: w for w in workloads}
    rendered = sorted((e for e in environments if e.rendered), key=lambda e: e.name)
    paths = []
    for w in sorted(workloads, key=lambda w: w.id):
        if w.kind != "web" and w.id not in proxy_ids:
            continue
        tail = []
        if w.id not in proxy_ids and not str(compute.get(w.id, "")).startswith(MANAGED_RUNTIME_PREFIXES):
            server = app_server(w.command)
            if server:
                tail.append(_hop("app-server", server[0], server[1], [w.entrypoint]))

        def hops_for(env: Environment | None) -> list[dict]:
            env_name = env.name if env else None
            own = _front(snap, w, artifacts, env)
            if w.id in proxy_ids:
                mine = [s for s in servers if s.proxy == w.id and s.environment == env_name]
                if not mine:
                    return own
                return own + [_proxy_hop([f for s in mine for f in s.settings], [s.evidence for s in mine])]
            incoming = [r for r in routes if r.target == w.id and r.environment == env_name and r.proxy != w.id
                        and r.proxy in by_id]
            if own or not incoming:
                return own + tail
            # 프록시가 여럿이면 프록시 워크로드 id 순 첫 번째
            pid = min(r.proxy for r in incoming)
            mine = [r for r in incoming if r.proxy == pid]
            return (_front(snap, by_id[pid], artifacts, env)
                    + [_proxy_hop([f for r in mine for f in r.settings], [r.evidence for r in mine])] + tail)

        def make(pid: str, env: Environment | None) -> dict:
            hops = [dict(h) for h in hops_for(env)]
            for i, hop in enumerate(hops):
                hop["order"] = i
            return {"id": pid, "workload": w.id, "environment": env.name if env else None, "hops": hops}

        present = [e for e in rendered if workload_in(e, w)]
        if not present:
            paths.append(make(f"path-{w.id[2:]}", None))
        for e in present:
            paths.append(make(f"path-{w.id[2:]}.{env_slug(e.name)}", e))
    return paths
