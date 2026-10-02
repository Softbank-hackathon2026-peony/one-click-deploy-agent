"""다단 리버스 프록시 체인: 요청 경로와 exposure가 프록시 뒤의 프록시를 따라간다."""

from infrafit.detect.artifacts import parse_artifacts
from infrafit.detect.endpoints import extract_endpoints
from infrafit.detect.environments import detect_environments
from infrafit.detect.manifests import parse_manifests
from infrafit.detect.nginx import find_proxies
from infrafit.detect.paths import build_paths, fronted_proxies
from infrafit.detect.workloads import detect_workloads
from infrafit.repo import open_snapshot


def _write(tmp_path, rel, text):
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def _analyze(tmp_path):
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    arts = parse_artifacts(snap)
    ws = detect_workloads(snap, parse_manifests(snap), arts)
    envs = detect_environments(arts, ws)
    servers, routes = find_proxies(snap, ws, arts, envs)
    fronted = fronted_proxies(snap, ws, arts, envs, servers)
    paths = build_paths(snap, ws, arts, {}, envs, (servers, routes))
    endpoints = extract_endpoints(snap, ws, routes, servers, fronted)
    return {p["id"]: p for p in paths}, endpoints


def _deploy(name, image, command=None):
    cmd = f"        command: {command}\n" if command else ""
    return (f"apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: {name}\nspec:\n"
            f"  selector:\n    matchLabels: {{app: {name}}}\n  template:\n    metadata:\n      labels: {{app: {name}}}\n"
            f"    spec:\n      containers:\n      - name: {name}\n        image: {image}\n{cmd}"
            f"---\napiVersion: v1\nkind: Service\nmetadata:\n  name: {name}\nspec:\n  selector: {{app: {name}}}\n"
            f"  ports:\n  - port: 80\n")


INGRESS = ("apiVersion: networking.k8s.io/v1\nkind: Ingress\nmetadata:\n  name: web\nspec:\n"
           "  ingressClassName: nginx\n  defaultBackend:\n    service: {name: pa, port: {number: 80}}\n")


def _chain_repo(tmp_path, a_conf, b_conf, routes):
    """Ingress → nginx pa → nginx pb → app. 프록시 설정은 각자의 이미지에 COPY된다."""
    for name, conf in (("pa", a_conf), ("pb", b_conf)):
        _write(tmp_path, f"{name}/Dockerfile", f"FROM nginx:1.27\nCOPY nginx/{name}.conf /etc/nginx/conf.d/default.conf\n")
        _write(tmp_path, f"nginx/{name}.conf", conf)
        _write(tmp_path, f"k8s/{name}.yaml", _deploy(name, f"acme/{name}:1"))
    _write(tmp_path, "k8s/app.yaml", _deploy("app", "acme/app:1", '["uvicorn", "main:app"]'))
    _write(tmp_path, "k8s/ingress.yaml", INGRESS)
    _write(tmp_path, "app/Dockerfile", "FROM python:3.12\nCMD uvicorn main:app\n")
    _write(tmp_path, "app/main.py", "".join(f'@app.get("{r}")\ndef h{i}(): ...\n' for i, r in enumerate(routes)))


def _kinds(path):
    return [(h["kind"], h["component"]) for h in path["hops"]]


def _read_timeouts(hop):
    return [(s["value"], s["defaulted"]) for s in hop["settings"] if s["key"] == "proxy_read_timeout"]


def _exposure(endpoints):
    out = {}
    for e in endpoints:
        vals = e.get("exposure")
        assert vals is None or len(vals) == 1
        out[(e["workload"], e["route"])] = vals[0]["value"] if vals else None
    return out


LB = ("load-balancer", "nw:k8s/ingress-nginx/default")
RP = ("reverse-proxy", "nw:proxy/nginx/default")


def test_chain_path_has_reverse_proxy_hop_per_proxy(tmp_path):
    _chain_repo(tmp_path, "server {\n  location / { proxy_pass http://pb; proxy_read_timeout 30s; }\n}\n",
                "server {\n  location / { proxy_pass http://app; proxy_read_timeout 90s; }\n}\n", ["/x"])
    paths, _ = _analyze(tmp_path)
    app = paths["path-app"]
    assert _kinds(app) == [LB, RP, RP, ("app-server", "nw:app/uvicorn/default")]
    assert [h["order"] for h in app["hops"]] == [0, 1, 2, 3]
    a_hop, b_hop = app["hops"][1], app["hops"][2]
    assert _read_timeouts(a_hop) == [(30, False)]
    assert [(e["path"], e["line"]) for e in a_hop["evidence"]] == [("nginx/pa.conf", 2)]
    assert _read_timeouts(b_hop) == [(90, False)]
    assert [(e["path"], e["line"]) for e in b_hop["evidence"]] == [("nginx/pb.conf", 2)]
    # 중간 프록시 pb의 경로: 앞 구간 + pa에서 pb로 가는 route 구간 + pb 자신의 server 구간
    assert _kinds(paths["path-pb"]) == [LB, RP, RP]
    assert _read_timeouts(paths["path-pb"]["hops"][1]) == [(30, False)]
    assert paths["path-pb"]["hops"][2]["evidence"][0]["path"] == "nginx/pb.conf"
    assert _kinds(paths["path-pa"]) == [LB, RP]


def test_chain_exposure_through_prefix_stripping(tmp_path):
    _chain_repo(tmp_path, "server {\n  location /api/ { proxy_pass http://pb/; }\n}\n",
                "server {\n  location /v1/ { proxy_pass http://app; }\n}\n", ["/v1/users", "/admin"])
    _, eps = _analyze(tmp_path)
    # 외부 /api/v1/users → pa에서 /v1/users로 → pb의 /v1/ → app /v1/users
    assert _exposure(eps) == {("w-app", "/v1/users"): "routed", ("w-app", "/admin"): "not-routed"}


def test_chain_exposure_internal_location_in_inner_proxy(tmp_path):
    _chain_repo(tmp_path, "server {\n  location / { proxy_pass http://pb; }\n}\n",
                "server {\n  location /internal/ { internal; }\n  location / { proxy_pass http://app; }\n}\n",
                ["/internal/y", "/z"])
    _, eps = _analyze(tmp_path)
    assert _exposure(eps) == {("w-app", "/internal/y"): "not-routed", ("w-app", "/z"): "routed"}


def test_chain_exposure_needs_outer_proxy_to_forward(tmp_path):
    # pb는 /b/를 app으로 넘기지만 pa는 /a/만 pb로 넘기므로 외부 요청은 pb의 /b/에 닿지 않는다
    _chain_repo(tmp_path, "server {\n  location /a/ { proxy_pass http://pb; }\n}\n",
                "server {\n  location /b/ { proxy_pass http://app; }\n  location /a/ { proxy_pass http://app; }\n}\n",
                ["/b/x", "/a/x"])
    _, eps = _analyze(tmp_path)
    assert _exposure(eps) == {("w-app", "/b/x"): "not-routed", ("w-app", "/a/x"): "routed"}


def test_chain_subrequest_in_inner_proxy_reached(tmp_path):
    _chain_repo(tmp_path, "server {\n  location / { proxy_pass http://pb; }\n}\n",
                "server {\n  location = /_v { internal; proxy_pass http://app/auth; }\n"
                "  location /api/ { auth_request /_v; proxy_pass http://app; }\n}\n", ["/auth", "/other"])
    _, eps = _analyze(tmp_path)
    assert _exposure(eps) == {("w-app", "/auth"): "routed", ("w-app", "/other"): "not-routed"}


def test_cyclic_proxies_terminate(tmp_path):
    _chain_repo(tmp_path, "server {\n  location / { proxy_pass http://pb; }\n}\n",
                "server {\n  location /loop/ { proxy_pass http://pa; }\n  location / { proxy_pass http://app; }\n}\n",
                ["/loop/x", "/y"])
    paths, eps = _analyze(tmp_path)
    assert _kinds(paths["path-app"]) == [LB, RP, RP, ("app-server", "nw:app/uvicorn/default")]
    assert _kinds(paths["path-pa"]) == [LB, RP]  # 자기 앞 구간이 있으면 체인을 따라가지 않는다
    assert _kinds(paths["path-pb"]) == [LB, RP, RP]
    assert _exposure(eps) == {("w-app", "/loop/x"): "not-routed", ("w-app", "/y"): "routed"}


def test_cyclic_proxies_without_front_terminate(tmp_path):
    _write(tmp_path, "docker-compose.yml", "services:\n"
           "  pa:\n    image: nginx:1.27\n    volumes:\n      - ./pa.conf:/etc/nginx/conf.d/default.conf:ro\n"
           "  pb:\n    image: nginx:1.27\n    volumes:\n      - ./pb.conf:/etc/nginx/conf.d/default.conf:ro\n"
           "  app:\n    build: ./app\n")
    _write(tmp_path, "pa.conf", "server {\n  location / { proxy_pass http://pb; }\n}\n")
    _write(tmp_path, "pb.conf", "server {\n  location /a/ { proxy_pass http://pa; }\n"
           "  location / { proxy_pass http://app; }\n}\n")
    _write(tmp_path, "app/Dockerfile", "FROM python:3.12\nCMD uvicorn main:app\n")
    _write(tmp_path, "app/main.py", '@app.get("/y")\ndef y(): ...\n')
    paths, eps = _analyze(tmp_path)
    assert [h["kind"] for h in paths["path-pa.compose"]["hops"]] == ["reverse-proxy", "reverse-proxy"]
    assert [h["kind"] for h in paths["path-pb.compose"]["hops"]] == ["reverse-proxy", "reverse-proxy"]
    # app ← pb ← pa(← pb는 순환이라 끊는다)
    app = paths["path-app.compose"]["hops"]
    assert [h["kind"] for h in app] == ["reverse-proxy", "reverse-proxy", "app-server"]
    assert [e["path"] for e in app[0]["evidence"]] == ["pa.conf"]
    assert [e["path"] for e in app[1]["evidence"]] == ["pb.conf"]
    assert _exposure(eps) == {("w-app", "/y"): "routed"}


def test_chain_depth_is_capped(tmp_path):
    names = [f"p{i}" for i in range(7)]
    svcs = "".join(f"  {n}:\n    image: nginx:1.27\n    volumes:\n      - ./{n}.conf:/etc/nginx/conf.d/default.conf:ro\n"
                   for n in names)
    _write(tmp_path, "docker-compose.yml", f"services:\n{svcs}  app:\n    build: ./app\n")
    for i, n in enumerate(names):
        nxt = names[i + 1] if i + 1 < len(names) else "app"
        _write(tmp_path, f"{n}.conf", f"server {{\n  location / {{ proxy_pass http://{nxt}; }}\n}}\n")
    _write(tmp_path, "app/Dockerfile", "FROM python:3.12\nCMD uvicorn main:app\n")
    _write(tmp_path, "app/main.py", '@app.get("/y")\ndef y(): ...\n')
    paths, eps = _analyze(tmp_path)
    app = paths["path-app.compose"]["hops"]
    assert [h["kind"] for h in app] == ["reverse-proxy"] * 5 + ["app-server"]
    assert [h["evidence"][0]["path"] for h in app[:5]] == [f"p{i}.conf" for i in range(2, 7)]
    assert _exposure(eps) == {("w-app", "/y"): "routed"}


def test_chain_ends_at_proxy_with_own_front(tmp_path):
    # pb는 자기 Ingress가 있어 체인이 pb에서 끝난다: pa가 넘기지 않는 /b/도 pb로 바로 들어온다
    _chain_repo(tmp_path, "server {\n  location /a/ { proxy_pass http://pb; }\n}\n",
                "server {\n  location /b/ { proxy_pass http://app; proxy_read_timeout 90s; }\n}\n", ["/b/x"])
    _write(tmp_path, "k8s/ingress-pb.yaml", INGRESS.replace("name: web", "name: pb-web").replace("name: pa", "name: pb"))
    paths, eps = _analyze(tmp_path)
    app = paths["path-app"]["hops"]
    assert _kinds(paths["path-app"]) == [LB, RP, ("app-server", "nw:app/uvicorn/default")]
    assert [e["path"] for e in app[1]["evidence"]] == ["nginx/pb.conf"]
    assert _kinds(paths["path-pb"]) == [LB, RP]
    assert _exposure(eps) == {("w-app", "/b/x"): "routed"}


def test_single_proxy_results_unchanged(tmp_path):
    """프록시가 하나뿐인 저장소: 체인 규칙을 넣어도 경로·exposure가 단일 프록시 규칙의 결과 그대로다."""
    _write(tmp_path, "k8s/proxy.yaml", _deploy("proxy", "acme/proxy:1"))
    _write(tmp_path, "proxy/Dockerfile", "FROM nginx:1.27\nCOPY nginx/default.conf /etc/nginx/conf.d/default.conf\n")
    _write(tmp_path, "nginx/default.conf", "server {\n  proxy_read_timeout 30s;\n"
           "  location = /_v { internal; proxy_pass http://b/v; }\n"
           "  location /api/ { auth_request /_v; proxy_pass http://a/; }\n"
           "  location /internal/ { internal; }\n}\n")
    for n in ("a", "b"):
        _write(tmp_path, f"k8s/{n}.yaml", _deploy(n, f"acme/{n}:1", '["uvicorn", "main:app"]'))
        _write(tmp_path, f"{n}/Dockerfile", "FROM python:3.12\nCMD uvicorn main:app\n")
    _write(tmp_path, "k8s/ingress.yaml", INGRESS.replace("name: pa", "name: proxy"))
    _write(tmp_path, "a/main.py", '@app.get("/users")\ndef u(): ...\n@app.get("/internal/x")\ndef i(): ...\n')
    _write(tmp_path, "b/main.py", '@app.get("/v")\ndef v(): ...\n@app.get("/w")\ndef w(): ...\n')
    paths, eps = _analyze(tmp_path)
    assert sorted(paths) == ["path-a", "path-b", "path-proxy"]
    for name in ("a", "b"):
        hops = paths[f"path-{name}"]["hops"]
        assert _kinds(paths[f"path-{name}"]) == [LB, RP, ("app-server", "nw:app/uvicorn/default")]
        assert [e["line"] for e in hops[1]["evidence"]] == [3 if name == "b" else 4]
        assert _read_timeouts(hops[1]) == [(30, False)]
    assert _kinds(paths["path-proxy"]) == [LB, RP]
    assert [e["line"] for e in paths["path-proxy"]["hops"][1]["evidence"]] == [1]
    assert _exposure(eps) == {("w-a", "/users"): "routed", ("w-a", "/internal/x"): "routed",
                              ("w-b", "/v"): "routed", ("w-b", "/w"): "not-routed"}
    # fronted를 넘기지 않아도(단일 프록시) exposure는 같다
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    arts = parse_artifacts(snap)
    ws = detect_workloads(snap, parse_manifests(snap), arts)
    servers, routes = find_proxies(snap, ws, arts, detect_environments(arts, ws))
    assert extract_endpoints(snap, ws, routes, servers) == eps
