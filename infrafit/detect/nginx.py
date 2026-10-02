"""nginx 리버스 프록시 설정 읽기와 upstream → 워크로드 해석."""

from __future__ import annotations

import fnmatch
import json
import posixpath
import re
import shlex
from dataclasses import dataclass, field
from pathlib import PurePosixPath

import crossplane

from infrafit.detect.artifacts import ParsedArtifact, _d, _final_chain, _stages, is_build_path, pod_spec
from infrafit.detect.environments import WORKLOAD_KINDS, Environment, workload_in
from infrafit.detect.manifests import parent_dir
from infrafit.detect.workloads import WorkloadInfo, _dockerfile_for_image
from infrafit.evidence import evidence
from infrafit.repo import Snapshot

CONF_SUFFIXES = (".conf", ".conf.template", ".conf.tmpl")
PROXY_DIRECTIVES = {"server", "upstream", "location", "proxy_pass"}
TIME_KEYS = ("proxy_read_timeout", "proxy_send_timeout", "proxy_connect_timeout", "keepalive_timeout")
SETTING_KEYS = TIME_KEYS + ("client_max_body_size", "proxy_http_version")
NGINX_ROOT = "/etc/nginx/"
TEMPLATE_DIR = "/etc/nginx/templates/"
CONFD_DIR = "/etc/nginx/conf.d"
MAX_INCLUDE_DEPTH = 10
TIME_UNITS = {"ms": 0.001, "s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800, "M": 2592000, "y": 31536000}
_TIME = re.compile(r"(\d+)(ms|s|m|h|d|w|M|y)?")
_ENVSUBST = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
_PROXY_PASS = re.compile(r"^(?:https?|grpcs?)://([^/]*)(/.*)?$")
_MODIFIER = re.compile(r"^(=|~\*|~|\^~)(.+)$")


@dataclass
class LocationInfo:
    modifier: str  # "", "=", "~", "~*", "^~", "@"
    pattern: str
    internal: bool
    order: int  # server 안에서의 설정 순서(정규식 검사 순서)
    proxies: list[tuple[str | None, str | None]] = field(default_factory=list)  # (대상 워크로드 id, uri)
    subrequests: list[str] = field(default_factory=list)
    children: list[LocationInfo] = field(default_factory=list)


@dataclass
class ProxyServer:
    proxy: str
    environment: str | None
    settings: list[dict]  # server 단위 실효 설정(server → http)
    locations: list[LocationInfo]  # 맨 위 location들(중첩은 children)
    evidence: dict | None = None  # server 블록 위치


@dataclass
class ProxyRoute:
    proxy: str
    environment: str | None
    location: tuple[str, str]
    internal: bool
    upstream: str
    uri: str | None
    target: str | None
    status: str
    subrequests: list[str] = field(default_factory=list)
    settings: list[dict] = field(default_factory=list)
    evidence: dict | None = None  # proxy_pass 지시어 위치


# --- 설정 파일 ----------------------------------------------------------------

def _is_conf_name(rel: str) -> bool:
    name = PurePosixPath(rel).name
    return name == "nginx.conf" or name.endswith(CONF_SUFFIXES)


def _parse(snap: Snapshot, rel: str, cache: dict) -> list | None:
    """crossplane으로 한 파일만 읽는다(include는 따라가지 않는다). 실패하면 None."""
    if rel not in cache:
        cache[rel] = None
        try:
            result = crossplane.parse(str(snap.root / rel), single=True, check_ctx=False,
                                      check_args=False, comments=False)
            config = result.get("config") or []
            if result.get("status") == "ok" and config and config[0].get("status") == "ok":
                parsed = config[0].get("parsed")
                cache[rel] = parsed if isinstance(parsed, list) else None
        except Exception:  # crossplane은 입력에 따라 여러 예외를 낸다
            cache[rel] = None
    return cache[rel]


def _walk(nodes):
    for n in nodes or []:
        if isinstance(n, dict):
            yield n
            if isinstance(n.get("block"), list):
                yield from _walk(n["block"])


def _has(nodes, names) -> bool:
    return any(n.get("directive") in names for n in _walk(nodes))


def _config_files(snap: Snapshot, cache: dict) -> list[str]:
    return [rel for rel in snap.files
            if _is_conf_name(rel) and _has(_parse(snap, rel, cache), PROXY_DIRECTIVES)]


# --- 컨테이너 경로 → 저장소 경로 ---------------------------------------------

def _workload_dockerfile(w: WorkloadInfo, artifacts: list[ParsedArtifact]) -> ParsedArtifact | None:
    df = _dockerfile_for_image(w.image, artifacts) if w.image else None
    if df is None and w.code_root is not None:
        local = sorted((a for a in artifacts if a.kind == "dockerfile" and parent_dir(a.path) == w.code_root),
                       key=lambda a: (PurePosixPath(a.path).name != "Dockerfile", a.path))
        df = local[0] if local else None
    return df


def _chain_instrs(df: ParsedArtifact | None) -> list[tuple[str, str, int]]:
    """최종 이미지에 들어가는 명령(마지막 단계와 FROM으로 잇는 앞 단계, 앞 단계부터)."""
    if df is None or not isinstance(df.objects, list):
        return []
    instrs = [x for x in df.objects if isinstance(x, tuple) and len(x) == 3]
    return [x for st in reversed(_final_chain(_stages(instrs))) for x in st["instrs"]]


def _final_image(df: ParsedArtifact | None) -> str:
    if df is None or not isinstance(df.objects, list):
        return ""
    stages = _stages([x for x in df.objects if isinstance(x, tuple) and len(x) == 3])
    return " ".join(st["image"] for st in _final_chain(stages))


def _tokens(arg: str) -> list[str]:
    if arg.startswith("["):
        try:
            data = json.loads(arg)
            return [str(x) for x in data] if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []
    try:
        return shlex.split(arg)
    except ValueError:
        return arg.split()


def _repo_files_under(snap: Snapshot, src: str) -> list[str] | None:
    """저장소 경로 src가 파일이면 [src], 디렉터리면 그 아래 파일들, 없으면 None."""
    if src == "":
        return list(snap.files)
    if snap.exists(src):
        return [src]
    under = [f for f in snap.files if f.startswith(src + "/")]
    return under or None


def _map_source(snap: Snapshot, src_rel: str, dest: str, out: dict[str, str], is_dir_dest: bool) -> None:
    files = _repo_files_under(snap, src_rel)
    if files is None:
        return
    if files == [src_rel]:
        out[posixpath.join(dest, PurePosixPath(src_rel).name) if is_dir_dest else dest] = src_rel
        return
    for f in files:
        rest = f[len(src_rel) + 1:] if src_rel else f
        out[posixpath.join(dest, rest)] = f


def _norm(path: str) -> str:
    p = posixpath.normpath(path)
    return "" if p == "." else p


def _dockerfile_mapping(snap: Snapshot, df: ParsedArtifact | None) -> dict[str, str]:
    out: dict[str, str] = {}
    if df is None:
        return out
    base = parent_dir(df.path)
    workdir = "/"
    for op, arg, _ in _chain_instrs(df):
        if op == "WORKDIR" and arg:
            workdir = posixpath.join(workdir, arg.strip())
        if op not in ("COPY", "ADD"):
            continue
        tokens = _tokens(arg)
        if any(t.startswith("--from") for t in tokens):
            continue
        tokens = [t for t in tokens if not t.startswith("--")]
        if len(tokens) < 2:
            continue
        *sources, dest = tokens
        dest = posixpath.join(workdir, dest)
        is_dir_dest = dest.endswith("/") or len(sources) > 1
        for src in sources:
            if "://" in src:
                continue
            # 빌드 컨텍스트: Dockerfile 디렉터리 기준을 먼저, 없으면 저장소 루트 기준
            for cand in (_norm(posixpath.join(base, src)), _norm(src)):
                if not cand.startswith("..") and _repo_files_under(snap, cand) is not None:
                    _map_source(snap, cand, posixpath.normpath(dest) if not dest.endswith("/") else dest,
                                out, is_dir_dest)
                    break
    return out


def _compose_services(artifacts: list[ParsedArtifact]) -> list[tuple[str, str, dict]]:
    out = []
    for art in artifacts:
        if art.kind != "compose" or not isinstance(art.objects, list):
            continue
        for obj in art.objects:
            if isinstance(obj, tuple) and len(obj) == 2 and isinstance(obj[0], str):
                out.append((art.path, obj[0], _d(obj[1])))
    return out


def _compose_mapping(snap: Snapshot, compose_path: str, svc: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    volumes = svc.get("volumes")
    for v in volumes if isinstance(volumes, list) else []:
        if isinstance(v, str):
            parts = v.split(":")
            if len(parts) < 2:
                continue
            host, target = parts[0], parts[1]
        elif isinstance(v, dict) and v.get("type", "bind") == "bind":
            host, target = str(v.get("source") or ""), str(v.get("target") or "")
        else:
            continue
        if not host.startswith(".") or not target.startswith("/"):
            continue
        src = _norm(posixpath.join(parent_dir(compose_path), host))
        if not src.startswith(".."):
            _map_source(snap, src, target, out, False)
    return out


def _with_templates(mapping: dict[str, str]) -> dict[str, str]:
    """nginx 공식 이미지: /etc/nginx/templates/X.template → /etc/nginx/conf.d/X."""
    out = dict(mapping)
    for cpath, rel in mapping.items():
        if cpath.startswith(TEMPLATE_DIR) and cpath.endswith(".template"):
            out.setdefault(f"{CONFD_DIR}/{cpath[len(TEMPLATE_DIR):-len('.template')]}", rel)
    return out


# --- 워크로드 환경 변수 --------------------------------------------------------

def _dockerfile_env(df: ParsedArtifact | None) -> dict[str, str]:
    out: dict[str, str] = {}
    for op, arg, _ in _chain_instrs(df):
        if op != "ENV":
            continue
        tokens = _tokens(arg)
        if tokens and "=" in tokens[0]:
            for t in tokens:
                k, sep, v = t.partition("=")
                if sep and k:
                    out[k] = v
        elif tokens:
            out[tokens[0]] = " ".join(tokens[1:])
    return out


def _compose_env(svc: dict) -> dict[str, str]:
    env = svc.get("environment")
    out: dict[str, str] = {}
    if isinstance(env, dict):
        out = {str(k): str(v) for k, v in env.items() if v is not None}
    elif isinstance(env, list):
        for item in env:
            k, sep, v = str(item).partition("=")
            if sep and k:
                out[k] = v
    return out


def _is_workload_doc(doc, w: WorkloadInfo) -> bool:
    if not isinstance(doc, dict) or doc.get("kind") not in WORKLOAD_KINDS:
        return False
    meta = _d(doc.get("metadata"))
    return meta.get("name") == w.name or _d(meta.get("labels")).get("app.kubernetes.io/name") == w.name


def _k8s_env(objects: list, w: WorkloadInfo) -> dict[str, str]:
    """워크로드 첫 컨테이너의 envFrom ConfigMap data, 그 위에 env[].value(쿠버네티스와 같은 우선순위)."""
    doc = next((d for d in objects if _is_workload_doc(d, w)), None)
    if doc is None:
        return {}
    containers = pod_spec(doc).get("containers")
    c = _d(containers[0]) if isinstance(containers, list) and containers else {}
    configmaps = {_d(o.get("metadata")).get("name"): _d(o.get("data")) for o in objects
                  if isinstance(o, dict) and o.get("kind") == "ConfigMap"}
    out: dict[str, str] = {}
    env_from = c.get("envFrom")
    for item in env_from if isinstance(env_from, list) else []:
        name = _d(_d(item).get("configMapRef")).get("name")
        if isinstance(name, str):
            out.update({str(k): str(v) for k, v in configmaps.get(name, {}).items() if v is not None})
    env = c.get("env")
    for item in env if isinstance(env, list) else []:
        item = _d(item)
        if isinstance(item.get("name"), str) and "value" in item and item["value"] is not None:
            out[item["name"]] = str(item["value"])
    return out


# --- 지시어 펼치기 -----------------------------------------------------------

def _include_targets(pattern: str, mapping: dict[str, str]) -> list[str]:
    cpath = pattern if pattern.startswith("/") else posixpath.join(NGINX_ROOT, pattern)
    depth = cpath.count("/")
    hits = [c for c in mapping if c.count("/") == depth and fnmatch.fnmatchcase(c, cpath)]
    return [mapping[c] for c in sorted(hits)]


def _expand(snap: Snapshot, rel: str, nodes: list, mapping: dict[str, str], cache: dict,
            stack: tuple[str, ...], included: set[str]) -> list[dict]:
    """include를 그 자리에 펼친 지시어 트리. 각 지시어에 원래 파일(`file`)을 단다."""
    out: list[dict] = []
    for n in nodes:
        if not isinstance(n, dict) or not isinstance(n.get("directive"), str):
            continue
        args = [str(a) for a in n.get("args") or []]
        if n["directive"] == "include":
            if not args or len(stack) > MAX_INCLUDE_DEPTH:
                continue
            for target in _include_targets(args[0], mapping):
                parsed = _parse(snap, target, cache) if target not in stack else None
                if parsed is not None:
                    included.add(target)
                    out.extend(_expand(snap, target, parsed, mapping, cache, stack + (target,), included))
            continue
        node = {"directive": n["directive"], "args": args, "line": n.get("line"), "file": rel, "block": None}
        if isinstance(n.get("block"), list):
            node["block"] = _expand(snap, rel, n["block"], mapping, cache, stack, included)
        out.append(node)
    return out


# --- 설정 값 ------------------------------------------------------------------

def _seconds(raw: str):
    pos, total = 0, 0.0
    for m in _TIME.finditer(raw):
        if m.start() != pos:
            return raw
        total += int(m.group(1)) * TIME_UNITS[m.group(2) or "s"]
        pos = m.end()
    return round(total) if raw and pos == len(raw) else raw


def _fact(snap: Snapshot, node: dict, key: str, value) -> dict:
    return {"key": key, "value": value, "defaulted": False,
            "evidence": evidence(snap, node["file"], node.get("line"))}


def _block_settings(snap: Snapshot, nodes: list[dict]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for n in nodes:
        key = n["directive"]
        if key in SETTING_KEYS and n["args"] and key not in out:
            raw = n["args"][0]
            out[key] = _fact(snap, n, key, _seconds(raw) if key in TIME_KEYS else raw)
    return out


def _sorted_facts(facts: dict[str, dict]) -> list[dict]:
    return [facts[k] for k in sorted(facts)]


# --- 호스트 → 워크로드 ---------------------------------------------------------

def _pod_labels(doc: dict) -> dict:
    spec = _d(doc.get("spec"))
    if doc.get("kind") == "CronJob":
        spec = _d(_d(spec.get("jobTemplate")).get("spec"))
    return _d(_d(_d(spec.get("template")).get("metadata")).get("labels"))


@dataclass
class _Scope:
    """한 (프록시 워크로드, 환경)에서 해석에 쓰는 자료."""
    objects: list
    variables: dict[str, str]
    workloads: list[WorkloadInfo]
    compose_names: set[str]
    link_status: str


def _resolve_host(host: str, scope: _Scope) -> tuple[str | None, str]:
    h = host.rsplit(":", 1)[0] if host.count(":") == 1 else host
    by_name = {w.name: w for w in scope.workloads}
    for doc in scope.objects:
        if not isinstance(doc, dict) or doc.get("kind") != "Service" or _d(doc.get("metadata")).get("name") != h:
            continue
        selector = _d(_d(doc.get("spec")).get("selector"))
        if not selector:
            continue
        ids = sorted({by_name[name].id for o in scope.objects
                      if isinstance(o, dict) and o.get("kind") in WORKLOAD_KINDS
                      and isinstance(name := _d(o.get("metadata")).get("name"), str) and name in by_name
                      and all(_pod_labels(o).get(k) == v for k, v in selector.items())})
        if ids:
            return ids[0], "candidate" if len(ids) > 1 else scope.link_status
    if h in scope.compose_names and h in by_name:
        return by_name[h].id, scope.link_status
    if h in by_name:
        return by_name[h].id, scope.link_status
    return None, "candidate"


def _substitute(text: str, variables: dict[str, str]) -> str:
    return _ENVSUBST.sub(lambda m: variables.get(m.group(1), m.group(0)), text)


def _resolve_pass(arg: str, upstreams: dict[str, dict], scope: _Scope) -> list[dict]:
    """proxy_pass 하나 → 해석된 대상 목록(upstream의 server마다 하나)."""
    m = _PROXY_PASS.match(arg)
    if not m:
        return [{"upstream": arg, "uri": None, "target": None, "status": "candidate", "keepalive": None}]
    raw_host, raw_uri = m.group(1), m.group(2)
    host = _substitute(raw_host, scope.variables)
    uri = _substitute(raw_uri, scope.variables) if raw_uri else None
    if "$" in host:
        return [{"upstream": raw_host, "uri": uri, "target": None, "status": "candidate", "keepalive": None}]
    up = upstreams.get(host)
    hosts = [_substitute(s, scope.variables) for s in up["servers"]] if up else [host]
    out = []
    for h in hosts:
        target, status = (None, "candidate") if "$" in h or not h else _resolve_host(h, scope)
        out.append({"upstream": raw_host, "uri": uri, "target": target, "status": status,
                    "keepalive": up["keepalive"] if up else None})
    return out


# --- server와 location ---------------------------------------------------------

def _location_args(args: list[str]) -> tuple[str, str]:
    if len(args) >= 2:
        return args[0], args[1]
    if not args:
        return "", ""
    if args[0].startswith("@"):
        return "@", args[0][1:]
    m = _MODIFIER.match(args[0])
    return (m.group(1), m.group(2)) if m else ("", args[0])


def _locations(snap: Snapshot, nodes: list[dict], inherited: list[dict[str, dict]], upstreams: dict,
               scope: _Scope, counter: list[int], routes: list[ProxyRoute], proxy: str,
               environment: str | None) -> list[LocationInfo]:
    out: list[LocationInfo] = []
    for n in nodes:
        if n["directive"] != "location" or n["block"] is None:
            continue
        block = n["block"]
        modifier, pattern = _location_args(n["args"])
        loc = LocationInfo(modifier, pattern, any(x["directive"] == "internal" for x in block), counter[0])
        counter[0] += 1
        loc.subrequests = [x["args"][0] for x in block
                           if x["directive"] == "auth_request" and x["args"] and x["args"][0] != "off"]
        chain = [_block_settings(snap, block)] + inherited
        effective: dict[str, dict] = {}
        for level in chain:
            for k, fact in level.items():
                effective.setdefault(k, fact)
        for x in block:
            if x["directive"] != "proxy_pass" or not x["args"]:
                continue
            for r in _resolve_pass(x["args"][0], upstreams, scope):
                loc.proxies.append((r["target"], r["uri"]))
                facts = dict(effective)
                if r["keepalive"] is not None:
                    facts["upstream_keepalive"] = r["keepalive"]
                routes.append(ProxyRoute(
                    proxy, environment, (modifier, pattern), loc.internal, r["upstream"], r["uri"], r["target"],
                    r["status"], list(loc.subrequests), _sorted_facts(facts), evidence(snap, x["file"], x["line"])))
        loc.children = _locations(snap, block, chain, upstreams, scope, counter, routes, proxy, environment)
        out.append(loc)
    return out


def _http_nodes(nodes: list[dict]) -> list[dict]:
    """http 문맥 지시어: 파일 맨 위(conf.d 파일은 http 안에 include된다)와 http 블록 안."""
    out = []
    for n in nodes:
        if n["directive"] == "http" and n["block"] is not None:
            out.extend(n["block"])
        else:
            out.append(n)
    return out


def _upstreams(snap: Snapshot, trees: list[list[dict]]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for nodes in trees:
        for n in _http_nodes(nodes):
            if n["directive"] != "upstream" or not n["args"] or n["block"] is None or n["args"][0] in out:
                continue
            servers = [x["args"][0] for x in n["block"] if x["directive"] == "server" and x["args"]]
            keep = next((x for x in n["block"] if x["directive"] == "keepalive" and x["args"]), None)
            value = int(keep["args"][0]) if keep and keep["args"][0].isdigit() else None
            out[n["args"][0]] = {"servers": servers,
                                 "keepalive": _fact(snap, keep, "upstream_keepalive", value) if value is not None else None}
    return out


# --- 설정 ↔ 워크로드 연결 -------------------------------------------------------

def _is_entry(cpath: str | None) -> bool:
    if cpath is None:
        return False
    return cpath == "/etc/nginx/nginx.conf" or (posixpath.dirname(cpath) == CONFD_DIR and cpath.endswith(".conf"))


def _links(snap: Snapshot, workloads: list[WorkloadInfo], artifacts: list[ParsedArtifact],
           configs: list[str], dockerfiles: dict[str, ParsedArtifact | None]) -> tuple[dict, dict]:
    """워크로드 id → 경로 매핑, 워크로드 id → [(저장소 파일, 컨테이너 경로 또는 None, 연결 상태)]."""
    services = _compose_services(artifacts)
    mappings: dict[str, dict[str, str]] = {}
    for w in workloads:
        mapping = _dockerfile_mapping(snap, dockerfiles[w.id])
        for path, name, svc in services:  # 런타임 바인드 마운트가 이미지 내용을 덮는다
            if name == w.name:
                mapping.update(_compose_mapping(snap, path, svc))
        mappings[w.id] = _with_templates(mapping)
    links: dict[str, list[tuple[str, str | None, str]]] = {w.id: [] for w in workloads}
    linked: set[str] = set()
    for w in workloads:
        for cpath, rel in sorted(mappings[w.id].items()):
            if rel in configs:
                links[w.id].append((rel, cpath, "confirmed"))
                linked.add(rel)
    nginx_based = [w for w in workloads
                   if "nginx" in w.image.lower() or "nginx" in _final_image(dockerfiles[w.id]).lower()]
    if len(nginx_based) == 1:
        links[nginx_based[0].id].extend((rel, None, "candidate") for rel in configs if rel not in linked)
    return mappings, links


def _entries(snap: Snapshot, links: list[tuple[str, str | None, str]], cache: dict) -> list[tuple[str, str]]:
    entries = [(rel, status) for rel, cpath, status in links if _is_entry(cpath)]
    if not entries:
        entries = [(rel, status) for rel, _, status in links if _has(_parse(snap, rel, cache), {"server"})]
    seen, out = set(), []
    for rel, status in entries:
        if rel not in seen:
            seen.add(rel)
            out.append((rel, status))
    return out


def _scopes(w: WorkloadInfo, environments: list[Environment]) -> list[Environment | None]:
    inside = [e for e in environments if workload_in(e, w)]
    return inside or [None]


def find_proxies(snap: Snapshot, workloads: list[WorkloadInfo], artifacts: list[ParsedArtifact],
                 environments: list[Environment]) -> tuple[list[ProxyServer], list[ProxyRoute]]:
    cache: dict = {}
    configs = _config_files(snap, cache)
    if not configs:
        return [], []
    dockerfiles = {w.id: _workload_dockerfile(w, artifacts) for w in workloads}
    mappings, links = _links(snap, workloads, artifacts, configs, dockerfiles)
    raw_k8s = [d for a in artifacts if a.kind == "k8s" and not is_build_path(a.path) and isinstance(a.objects, list)
               for d in a.objects if isinstance(d, dict)]
    services = _compose_services(artifacts)
    compose_names = {name for _, name, _ in services}
    servers: list[ProxyServer] = []
    routes: list[ProxyRoute] = []
    for w in workloads:
        entries = _entries(snap, links[w.id], cache)
        if not entries:
            continue
        trees, included = [], set()
        for rel, status in entries:
            trees.append((rel, status, _expand(snap, rel, _parse(snap, rel, cache) or [], mappings[w.id], cache,
                                               (rel,), included)))
        # 다른 진입 설정이 include한 파일은 따로 진입점으로 세지 않는다
        trees = [t for t in trees if t[0] not in included]
        upstreams = _upstreams(snap, [t[2] for t in trees])
        for env in _scopes(w, environments):
            variables = _dockerfile_env(dockerfiles[w.id])
            if env is None:
                for _, name, svc in services:
                    if name == w.name:
                        variables.update(_compose_env(svc))
                objects = raw_k8s
            else:
                objects = env.objects
            variables.update(_k8s_env(objects, w))
            env_name = env.name if env else None
            for rel, status, nodes in trees:
                scope = _Scope(objects, variables, workloads, compose_names, status)
                http = _http_nodes(nodes)
                http_settings = _block_settings(snap, http)
                counter = [0]
                for n in http:
                    if n["directive"] != "server" or n["block"] is None:
                        continue
                    server_settings = _block_settings(snap, n["block"])
                    effective = {**http_settings, **server_settings}
                    counter[0] = 0
                    locs = _locations(snap, n["block"], [server_settings, http_settings], upstreams, scope,
                                      counter, routes, w.id, env_name)
                    servers.append(ProxyServer(w.id, env_name, _sorted_facts(effective), locs,
                                               evidence(snap, n["file"], n["line"])))
    servers.sort(key=lambda s: (s.proxy, s.environment or "", s.evidence["path"], s.evidence["line"] or 0))
    routes.sort(key=lambda r: (r.proxy, r.environment or "", r.evidence["path"], r.evidence["line"] or 0,
                               r.location, r.upstream, r.target or "", r.uri or ""))
    return servers, routes
