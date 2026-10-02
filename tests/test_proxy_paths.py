from infrafit.detect.artifacts import parse_artifacts
from infrafit.detect.endpoints import _request_path, extract_endpoints, select_location
from infrafit.detect.environments import detect_environments
from infrafit.detect.manifests import parse_manifests
from infrafit.detect.nginx import LocationInfo, ProxyServer, find_proxies
from infrafit.detect.paths import build_paths
from infrafit.detect.workloads import WorkloadInfo, detect_workloads
from infrafit.repo import open_snapshot

EV = {"path": "x", "line": 1, "snippet": "x"}


def _write(tmp_path, rel, text):
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def _analyze(tmp_path):
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    arts = parse_artifacts(snap)
    ws = detect_workloads(snap, parse_manifests(snap), arts)
    envs = detect_environments(arts)
    proxy = find_proxies(snap, ws, arts, envs)
    paths = build_paths(snap, ws, arts, {}, envs, proxy)
    endpoints = extract_endpoints(snap, ws, proxy[1], proxy[0])
    return paths, endpoints


def _deploy(name, image, command=None):
    cmd = f"        command: {command}\n" if command else ""
    return (f"apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: {name}\nspec:\n"
            f"  selector:\n    matchLabels: {{app: {name}}}\n  template:\n    metadata:\n      labels: {{app: {name}}}\n"
            f"    spec:\n      containers:\n      - name: {name}\n        image: {image}\n{cmd}"
            f"---\napiVersion: v1\nkind: Service\nmetadata:\n  name: {name}\nspec:\n  selector: {{app: {name}}}\n"
            f"  ports:\n  - port: 80\n")


INGRESS = ("apiVersion: networking.k8s.io/v1\nkind: Ingress\nmetadata:\n  name: web\nspec:\n"
           "  ingressClassName: nginx\n  defaultBackend:\n    service: {name: proxy, port: {number: 80}}\n")


def _lb_repo(tmp_path, conf):
    _write(tmp_path, "k8s/proxy.yaml", _deploy("proxy", "nginx:1.27"))
    _write(tmp_path, "k8s/a.yaml", _deploy("a", "acme/a:1", '["uvicorn", "main:app"]'))
    _write(tmp_path, "k8s/b.yaml", _deploy("b", "acme/b:1", '["uvicorn", "main:app"]'))
    _write(tmp_path, "k8s/ingress.yaml", INGRESS)
    _write(tmp_path, "nginx/default.conf", conf)


def _by_id(paths):
    return {p["id"]: p for p in paths}


def _kinds(path):
    return [(h["order"], h["kind"], h["component"]) for h in path["hops"]]


def test_proxy_chain_paths(tmp_path):
    _lb_repo(tmp_path, "upstream ua { server a:80; }\nupstream ub { server b:80; }\n"
             "server {\n  listen 80;\n  proxy_read_timeout 30s;\n"
             "  location /a/ { proxy_pass http://ua; }\n  location /b/ { proxy_pass http://ub; }\n}\n")
    paths = _by_id(_analyze(tmp_path)[0])
    assert sorted(paths) == ["path-a", "path-b", "path-proxy"]
    assert _kinds(paths["path-proxy"]) == [(0, "load-balancer", "nw:k8s/ingress-nginx/default"),
                                           (1, "reverse-proxy", "nw:proxy/nginx/default")]
    for name in ("a", "b"):
        assert _kinds(paths[f"path-{name}"]) == [(0, "load-balancer", "nw:k8s/ingress-nginx/default"),
                                                 (1, "reverse-proxy", "nw:proxy/nginx/default"),
                                                 (2, "app-server", "nw:app/uvicorn/default")]
    rp = paths["path-a"]["hops"][1]
    assert rp["evidence"][0]["path"] == "nginx/default.conf"
    assert [e["line"] for e in rp["evidence"]] == [6]  # proxy_pass 줄
    read = [s for s in rp["settings"] if s["key"] == "proxy_read_timeout"]
    assert read == [{"key": "proxy_read_timeout", "value": 30, "defaulted": False,
                     "evidence": {"path": "nginx/default.conf", "line": 5, "snippet": "proxy_read_timeout 30s;"}}]
    send = next(s for s in rp["settings"] if s["key"] == "proxy_send_timeout")
    assert send["value"] == 60 and send["defaulted"] is True and "evidence" not in send
    assert {s["key"] for s in rp["settings"]} >= {"proxy_connect_timeout", "client_max_body_size", "keepalive_timeout"}
    keys = [(s["key"], str(s["value"])) for s in rp["settings"]]
    assert keys == sorted(keys)
    proxy_hop = paths["path-proxy"]["hops"][1]
    assert [e["line"] for e in proxy_hop["evidence"]] == [3]  # server 블록
    assert next(s for s in proxy_hop["settings"] if s["key"] == "proxy_read_timeout")["value"] == 30


def test_same_key_different_values_per_location(tmp_path):
    _lb_repo(tmp_path, "upstream ua { server a:80; }\n"
             "server {\n"
             "  location /a/ { proxy_pass http://ua; proxy_read_timeout 15s; }\n"
             "  location /a2/ { proxy_pass http://ua; proxy_read_timeout 60s; }\n"
             "  location /a3/ { proxy_pass http://ua; proxy_read_timeout 15s; }\n}\n")
    paths = _by_id(_analyze(tmp_path)[0])
    rp = paths["path-a"]["hops"][1]
    read = [s for s in rp["settings"] if s["key"] == "proxy_read_timeout"]
    assert [(s["value"], s["defaulted"], s["evidence"]["line"]) for s in read] == [(15, False, 3), (60, False, 4)]
    send = next(s for s in rp["settings"] if s["key"] == "proxy_send_timeout")
    assert send["default_source"]["ref"] == "docs/research/capabilities/09-network-lb-ingress.md"
    assert [e["line"] for e in rp["evidence"]] == [3, 4, 5]


def test_own_ingress_keeps_own_path(tmp_path):
    _lb_repo(tmp_path, "server { location / { proxy_pass http://a:80; } }\n")
    _write(tmp_path, "k8s/ingress-a.yaml", INGRESS.replace("name: web", "name: a-web").replace("name: proxy", "name: a"))
    paths = _by_id(_analyze(tmp_path)[0])
    assert [k for _, k, _ in _kinds(paths["path-a"])] == ["load-balancer", "app-server"]


def test_shared_code_root_gives_endpoints_to_each_workload(tmp_path):
    _write(tmp_path, "app/main.py", '@app.get("/items")\ndef items(): ...\n')
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    ws = [WorkloadInfo(id=f"w-{n}", kind="web", name=n, entrypoint=EV, status="confirmed", source="compose",
                       code_root="app") for n in ("api", "admin")]
    eps = extract_endpoints(snap, ws)
    assert [(e["id"], e["workload"], e["status"]) for e in eps] == [
        ("ep-admin-001", "w-admin", "confirmed"), ("ep-api-001", "w-api", "confirmed")]


def _compose_repo(tmp_path, conf, apps):
    _write(tmp_path, "docker-compose.yml", "services:\n  proxy:\n    image: nginx:1.27\n    volumes:\n"
           "      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro\n"
           + "".join(f"  {n}:\n    build: ./{n}\n" for n in apps))
    _write(tmp_path, "nginx.conf", conf)
    for n in apps:
        _write(tmp_path, f"{n}/Dockerfile", "FROM python:3.12\nCMD uvicorn main:app\n")


def _exposure(endpoints):
    return {(e["workload"], e["route"]): e.get("exposure") for e in endpoints}


def test_exposure_return_location_not_routed(tmp_path):
    _compose_repo(tmp_path, "server {\n  location /internal/ { return 404; }\n"
                  "  location /api/ { proxy_pass http://a; }\n}\n", ["a"])
    _write(tmp_path, "a/main.py", '@app.get("/api/{x}")\ndef x(): ...\n@app.get("/internal/y")\ndef y(): ...\n')
    _, eps = _analyze(tmp_path)
    assert _exposure(eps) == {("w-a", "/api/{x}"): "routed", ("w-a", "/internal/y"): "not-routed"}


def test_exposure_through_auth_request_subrequest(tmp_path):
    _compose_repo(tmp_path, "server {\n  location = /_v { internal; proxy_pass http://b/internal/v; }\n"
                  "  location /api/ { auth_request /_v; proxy_pass http://a; }\n}\n", ["a", "b"])
    _write(tmp_path, "a/main.py", '@app.get("/api/x")\ndef x(): ...\n')
    _write(tmp_path, "b/main.py", '@app.get("/internal/v")\ndef v(): ...\n@app.post("/other")\ndef o(): ...\n')
    _, eps = _analyze(tmp_path)
    assert _exposure(eps) == {("w-a", "/api/x"): "routed", ("w-b", "/internal/v"): "routed",
                              ("w-b", "/other"): "not-routed"}


def test_exposure_with_uri_rewrite(tmp_path):
    _compose_repo(tmp_path, "server {\n  location /api/ { proxy_pass http://a/v1/; }\n}\n", ["a"])
    _write(tmp_path, "a/main.py", '@app.get("/v1/items/{i}")\ndef i(): ...\n@app.get("/api/items")\ndef j(): ...\n')
    _, eps = _analyze(tmp_path)
    # /api/items/x1 요청이 /v1/items/x1로 전달되므로 /v1/items/{i}는 닿는다. /api/items는 /v1/items로 바뀌어 닿지 않는다
    assert _exposure(eps) == {("w-a", "/v1/items/{i}"): "routed", ("w-a", "/api/items"): "not-routed"}
    _write(tmp_path, "a/main.py", '@app.get("/v1/items/{i}")\ndef i(): ...\n@app.get("/api/items/{i}")\ndef j(): ...\n')
    _, eps = _analyze(tmp_path)
    assert _exposure(eps) == {("w-a", "/v1/items/{i}"): "routed", ("w-a", "/api/items/{i}"): "not-routed"}


def test_no_proxy_keeps_plan1_output(tmp_path):
    _write(tmp_path, "docker-compose.yml", "services:\n  a:\n    build: ./a\n")
    _write(tmp_path, "a/Dockerfile", "FROM python:3.12\nCMD uvicorn main:app\n")
    _write(tmp_path, "a/main.py", '@app.get("/x")\ndef x(): ...\n')
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    arts = parse_artifacts(snap)
    ws = detect_workloads(snap, parse_manifests(snap), arts)
    paths, eps = _analyze(tmp_path)
    assert eps == extract_endpoints(snap, ws)
    assert all("exposure" not in e for e in eps)
    assert paths == build_paths(snap, ws, arts, {}, [])


def _loc(modifier, pattern, order, internal=False, children=()):
    return LocationInfo(modifier, pattern, internal, order, children=list(children))


def _pick(locs, path):
    loc = select_location(locs, path)
    return (loc.modifier, loc.pattern) if loc else None


def test_select_location_rules():
    locs = [_loc("", "/", 0), _loc("=", "/exact", 1), _loc("", "/exact", 2), _loc("^~", "/static/", 3),
            _loc("~", r"\.png$", 4), _loc("~*", r"\.PNG$", 5), _loc("", "/img/", 6), _loc("~", r"^/img/a", 7),
            _loc("@", "fallback", 8), _loc("", "/hidden/", 9, internal=True)]
    assert _pick(locs, "/exact") == ("=", "/exact")
    assert _pick(locs, "/exactly") == ("", "/exact")
    assert _pick(locs, "/static/x.png") == ("^~", "/static/")
    assert _pick(locs, "/img/b.png") == ("~", r"\.png$")
    assert _pick(locs, "/img/a.png") == ("~", r"\.png$")  # 설정 순서상 앞선 정규식
    assert _pick(locs, "/img/a.jpg") == ("~", r"^/img/a")
    assert _pick(locs, "/x.Png") == ("~*", r"\.PNG$")
    assert _pick(locs, "/img/c") == ("", "/img/")
    assert _pick(locs, "fallback") is None
    assert _pick(locs, "/hidden/x") == ("", "/hidden/")  # internal도 후보다(외부 요청은 404)
    assert select_location([_loc("", "/a/", 0)], "/b") is None


def test_select_location_nested():
    outer = _loc("", "/api/", 0, children=[_loc("", "/api/v2/", 1), _loc("~", r"\.json$", 2)])
    locs = [outer, _loc("~", r"^/api/v2/x", 3)]
    assert _pick(locs, "/api/v2/x") == ("~", r"^/api/v2/x")
    assert _pick(locs, "/api/v2/y") == ("", "/api/v2/")
    assert _pick(locs, "/api/z.json") == ("~", r"\.json$")
    assert _pick(locs, "/api/z") == ("", "/api/")
    assert select_location([_loc("~", "([", 0)], "/x") is None  # 잘못된 정규식은 건너뛴다


def test_inherited_key_gets_default_fact_per_route(tmp_path):
    _lb_repo(tmp_path, "upstream ua { server a:80; }\n"
             "server {\n"
             "  location /a/ { proxy_pass http://ua; proxy_read_timeout 15s; }\n"
             "  location /a2/ { proxy_pass http://ua; }\n}\n")
    rp = _by_id(_analyze(tmp_path)[0])["path-a"]["hops"][1]
    read = [s for s in rp["settings"] if s["key"] == "proxy_read_timeout"]
    assert [(s["value"], s["defaulted"]) for s in read] == [(15, False), (60, True)]
    assert read[0]["evidence"]["line"] == 3
    assert read[1]["default_source"]["ref"] == "docs/research/capabilities/09-network-lb-ingress.md"
    assert "evidence" not in read[1]


def _ws(roots):
    return [WorkloadInfo(id=f"w-{n}", kind="web", name=n, entrypoint=EV, status="confirmed", source="compose",
                         code_root=r) for n, r in roots]


def test_shared_code_goes_to_deepest_root(tmp_path):
    _write(tmp_path, "svc/api/main.py", '@app.get("/items")\ndef items(): ...\n')
    _write(tmp_path, "svc/other.py", '@app.get("/o")\ndef o(): ...\n')
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    eps = extract_endpoints(snap, _ws([("outer", "svc"), ("inner", "svc/api")]))
    assert [(e["workload"], e["route"]) for e in eps] == [("w-inner", "/items"), ("w-outer", "/o")]
    eps = extract_endpoints(snap, _ws([("outer", "svc"), ("inner", "svc/api"), ("twin", "svc/api")]))
    assert sorted((e["workload"], e["route"]) for e in eps) == [
        ("w-inner", "/items"), ("w-outer", "/o"), ("w-twin", "/items")]


def test_subrequest_target_routed_without_calling_endpoint(tmp_path):
    _compose_repo(tmp_path, "server {\n  location = /_v { internal; proxy_pass http://b/internal/v; }\n"
                  "  location /api/ { auth_request /_v; proxy_pass http://a; }\n}\n", ["a", "b"])
    _write(tmp_path, "b/main.py", '@app.get("/internal/v")\ndef v(): ...\n@app.post("/other")\ndef o(): ...\n')
    _, eps = _analyze(tmp_path)
    assert _exposure(eps) == {("w-b", "/internal/v"): "routed", ("w-b", "/other"): "not-routed"}


def test_select_location_nested_regex_beats_outer_regex():
    outer = _loc("", "/api/", 0, children=[_loc("~", r"\.json$", 1)])
    locs = [outer, _loc("~", "^/api/", 2)]
    assert _pick(locs, "/api/x.json") == ("~", r"\.json$")
    assert _pick(locs, "/api/x") == ("~", "^/api/")


def test_internal_location_blocks_external_request(tmp_path):
    _compose_repo(tmp_path, "server {\n  location /internal/ { internal; }\n"
                  "  location / { proxy_pass http://a; }\n}\n", ["a"])
    _write(tmp_path, "a/main.py", '@app.get("/internal/y")\ndef y(): ...\n@app.get("/z")\ndef z(): ...\n')
    _, eps = _analyze(tmp_path)
    assert _exposure(eps) == {("w-a", "/internal/y"): "not-routed", ("w-a", "/z"): "routed"}


def test_request_path_parameters():
    assert _request_path("/^api/items/(?P<pk>[0-9]+)/$", "django") == "/api/items/x1/"
    assert _request_path("/items/<int:pk>/<slug>") == "/items/x1/x1"
    assert _request_path("/v1/items:batch") == "/v1/items:batch"
    assert _request_path("/users/:id/[post]/{x}") == "/users/x1/x1/x1"
    assert _request_path("api/x") == "/api/x"


def test_proxy_without_server_in_environment_gets_default_hop(tmp_path):
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    w = WorkloadInfo(id="w-proxy", kind="web", name="proxy", entrypoint=EV, status="confirmed", source="k8s")
    other = ProxyServer("w-proxy", "elsewhere", [], [], {"path": "x", "line": 1, "snippet": "x"})
    paths = build_paths(snap, [w], [], {}, [], ([other], []))
    hops = paths[0]["hops"]
    assert [(h["kind"], h["evidence"]) for h in hops] == [("reverse-proxy", [])]
    assert hops[0]["settings"] and all(s["defaulted"] for s in hops[0]["settings"])


def _express_compose_repo(tmp_path, conf, routes):
    _write(tmp_path, "docker-compose.yml", "services:\n  proxy:\n    image: nginx:1.27\n    volumes:\n"
           "      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro\n"
           "  app:\n    build: ./app\n    command: node server.js\n")
    _write(tmp_path, "nginx.conf", conf)
    _write(tmp_path, "app/Dockerfile", 'FROM node:20\nCMD ["node", "server.js"]\n')
    _write(tmp_path, "app/package.json", '{"dependencies": {"express": "^4"}}\n')
    _write(tmp_path, "app/server.js", "const app = express();\n"
           + "".join(f"app.get('{r}', h);\n" for r in routes))


def test_exposure_through_prefix_stripping_proxy(tmp_path):
    # /api/users 요청이 /users로 전달된다
    _express_compose_repo(tmp_path, "server {\n  location /api/ { proxy_pass http://app:3000/; }\n}\n", ["/users"])
    _, eps = _analyze(tmp_path)
    assert _exposure(eps) == {("w-app", "/users"): "routed"}


def test_exposure_reverse_mapping_only_under_uri(tmp_path):
    _express_compose_repo(tmp_path, "server {\n  location /api/ { proxy_pass http://app:3000/v1/; }\n}\n",
                          ["/v1/users", "/admin"])
    _, eps = _analyze(tmp_path)
    # /api/users → /v1/users. /admin은 /v1/ 아래가 아니어서 어떤 요청으로도 닿지 않는다
    assert _exposure(eps) == {("w-app", "/v1/users"): "routed", ("w-app", "/admin"): "not-routed"}
