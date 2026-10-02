from infrafit.detect.artifacts import parse_artifacts
from infrafit.detect.environments import Environment
from infrafit.detect.manifests import parse_manifests
from infrafit.detect.nginx import find_proxies
from infrafit.detect.workloads import WorkloadInfo, detect_workloads
from infrafit.repo import open_snapshot

EV = {"path": "x", "line": 1, "snippet": "x"}


def _write(tmp_path, rel, text):
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def _run(tmp_path, workloads=None, environments=()):
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    arts = parse_artifacts(snap)
    ws = workloads if workloads is not None else detect_workloads(snap, parse_manifests(snap), arts)
    return find_proxies(snap, ws, arts, list(environments))


def _w(name, image="", source="k8s"):
    return WorkloadInfo(id=f"w-{name}", kind="web", name=name, entrypoint=EV, status="confirmed",
                        source=source, image=image)


def _settings(obj):
    return {s["key"]: s["value"] for s in obj.settings}


def _compose(services):
    return "services:\n" + "".join(f"  {name}:\n{body}" for name, body in services)


def test_dockerfile_copy_template_and_included_snippet(tmp_path):
    _write(tmp_path, "docker-compose.yml", _compose([
        ("proxy", "    build: {context: ., dockerfile: proxy/Dockerfile}\n"),
        ("api", "    image: acme/api:1\n")]))
    _write(tmp_path, "proxy/Dockerfile", "FROM nginx:1.27\n"
           "COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template\n"
           "COPY nginx/snippets/ /etc/nginx/snippets/\n")
    _write(tmp_path, "nginx/default.conf.template",
           "server {\n  listen 80;\n  location /api/ {\n    include /etc/nginx/snippets/p.conf;\n  }\n}\n")
    _write(tmp_path, "nginx/snippets/p.conf", "proxy_pass http://api:8000;\nproxy_read_timeout 15s;\n")
    servers, routes = _run(tmp_path)
    assert [(s.proxy, s.environment) for s in servers] == [("w-proxy", None)]
    assert len(routes) == 1
    r = routes[0]
    assert (r.proxy, r.environment, r.location, r.internal) == ("w-proxy", None, ("", "/api/"), False)
    assert (r.upstream, r.uri, r.target, r.status) == ("api:8000", None, "w-api", "confirmed")
    fact = next(s for s in r.settings if s["key"] == "proxy_read_timeout")
    assert fact["value"] == 15 and fact["defaulted"] is False
    assert (fact["evidence"]["path"], fact["evidence"]["line"]) == ("nginx/snippets/p.conf", 2)
    loc = servers[0].locations[0]
    assert (loc.modifier, loc.pattern, loc.proxies) == ("", "/api/", [("w-api", None)])


def test_upstream_with_dockerfile_env_and_keepalive(tmp_path):
    _write(tmp_path, "docker-compose.yml", _compose([
        ("proxy", "    build: .\n"), ("a", "    image: acme/a:1\n")]))
    _write(tmp_path, "Dockerfile", "FROM nginx:1.27\nENV UP=a:80 OTHER=x\n"
           "COPY default.conf /etc/nginx/conf.d/default.conf\n")
    _write(tmp_path, "default.conf",
           "upstream u { server ${UP}; keepalive 16; }\nserver { location / { proxy_pass http://u; } }\n")
    _, routes = _run(tmp_path)
    assert [(r.upstream, r.target, r.environment) for r in routes] == [("u", "w-a", None)]
    fact = next(s for s in routes[0].settings if s["key"] == "upstream_keepalive")
    assert fact["value"] == 16 and fact["evidence"]["line"] == 1


def _proxy_env(name, up):
    return Environment(name, f"k8s/overlays/{name}/kustomization.yaml", True, [
        {"kind": "Deployment", "metadata": {"name": "proxy"},
         "spec": {"template": {"spec": {"containers": [
             {"name": "nginx", "image": "acme/proxy:1",
              "envFrom": [{"configMapRef": {"name": f"proxy-cfg-{name}9"}}]}]}}}},
        {"kind": "ConfigMap", "metadata": {"name": f"proxy-cfg-{name}9"}, "data": {"UP": up}},
        {"kind": "Deployment", "metadata": {"name": "a"}},
        {"kind": "Deployment", "metadata": {"name": "b"}}])


def test_environments_override_upstream_via_configmap(tmp_path):
    _write(tmp_path, "proxy/Dockerfile", "FROM nginx:1.27\nENV UP=zzz:80\n"
           "COPY default.conf /etc/nginx/conf.d/default.conf\n")
    _write(tmp_path, "proxy/default.conf",
           "upstream u { server ${UP}; }\nserver { location / { proxy_pass http://u; } }\n")
    ws = [_w("proxy", "acme/proxy:1"), _w("a"), _w("b")]
    servers, routes = _run(tmp_path, ws, [_proxy_env("dev", "a:80"), _proxy_env("prod", "b:80")])
    assert [(r.environment, r.target) for r in routes] == [("dev", "w-a"), ("prod", "w-b")]
    assert [s.environment for s in servers] == ["dev", "prod"]
    assert servers[1].locations[0].proxies == [("w-b", None)]


def test_service_selector_resolves_to_differently_named_deployment(tmp_path):
    _write(tmp_path, "k8s/app.yaml", """apiVersion: v1
kind: Service
metadata: {name: backend}
spec: {selector: {app: api-pod}}
---
apiVersion: apps/v1
kind: Deployment
metadata: {name: api}
spec: {template: {metadata: {labels: {app: api-pod, tier: be}}, spec: {containers: [{name: api, image: acme/api:1}]}}}
---
apiVersion: apps/v1
kind: Deployment
metadata: {name: proxy}
spec: {template: {spec: {containers: [{name: nginx, image: acme/proxy:1}]}}}
""")
    _write(tmp_path, "proxy/Dockerfile", "FROM nginx:1.27\nCOPY default.conf /etc/nginx/conf.d/default.conf\n")
    _write(tmp_path, "proxy/default.conf", "server { location / { proxy_pass http://backend:8080; } }\n")
    _, routes = _run(tmp_path)
    assert [(r.upstream, r.target, r.status) for r in routes] == [("backend:8080", "w-api", "confirmed")]


def test_compose_bind_mount_nginx_conf(tmp_path):
    _write(tmp_path, "docker-compose.yml", _compose([
        ("proxy", "    image: nginx:1.27\n    volumes:\n      - ./nginx.conf:/etc/nginx/nginx.conf:ro\n"),
        ("api", "    image: acme/api:1\n")]))
    _write(tmp_path, "nginx.conf",
           "events {}\nhttp {\n  server {\n    location / { proxy_pass http://api:8000; }\n  }\n}\n")
    _, routes = _run(tmp_path)
    assert [(r.target, r.status) for r in routes] == [("w-api", "confirmed")]


def test_settings_inherit_location_server_http(tmp_path):
    _write(tmp_path, "docker-compose.yml", _compose([
        ("proxy", "    image: nginx:1.27\n    volumes:\n      - ./nginx.conf:/etc/nginx/nginx.conf\n"),
        ("api", "    image: acme/api:1\n")]))
    _write(tmp_path, "nginx.conf", """http {
  client_max_body_size 10m;
  server {
    proxy_read_timeout 30s;
    keepalive_timeout 2m 60s;
    location / { proxy_pass http://api; }
    location /slow { proxy_read_timeout 5s; proxy_pass http://api; }
  }
}
""")
    servers, routes = _run(tmp_path)
    by_loc = {r.location[1]: _settings(r) for r in routes}
    assert by_loc["/"]["proxy_read_timeout"] == 30 and by_loc["/slow"]["proxy_read_timeout"] == 5
    assert by_loc["/"]["client_max_body_size"] == "10m" and by_loc["/"]["keepalive_timeout"] == 120
    assert _settings(servers[0]) == {"client_max_body_size": "10m", "keepalive_timeout": 120,
                                     "proxy_read_timeout": 30}
    assert [s["key"] for s in servers[0].settings] == sorted(s["key"] for s in servers[0].settings)


def test_uri_variable_nested_internal_and_subrequests(tmp_path):
    _write(tmp_path, "docker-compose.yml", _compose([
        ("proxy", "    image: nginx:1.27\n    volumes:\n      - ./conf.d:/etc/nginx/conf.d\n"),
        ("u", "    image: acme/u:1\n")]))
    _write(tmp_path, "conf.d/site.conf", """server {
  location /a { proxy_pass http://u/internal/x; }
  location /b { proxy_pass http://$backend; }
  location = /_v { internal; proxy_pass http://u/v; }
  location /c {
    auth_request /_v;
    location ~* \\.js$ { proxy_pass http://u; }
  }
  location @fallback { return 404; }
}
""")
    servers, routes = _run(tmp_path)
    got = {r.location: (r.upstream, r.uri, r.target, r.internal, r.subrequests) for r in routes}
    assert got[("", "/a")] == ("u", "/internal/x", "w-u", False, [])
    assert got[("", "/b")] == ("$backend", None, None, False, [])
    assert got[("=", "/_v")] == ("u", "/v", "w-u", True, [])
    assert got[("~*", "\\.js$")] == ("u", None, "w-u", False, [])
    locs = servers[0].locations
    assert [(loc.modifier, loc.pattern, loc.order) for loc in locs] == [
        ("", "/a", 0), ("", "/b", 1), ("=", "/_v", 2), ("", "/c", 3), ("@", "fallback", 5)]
    c = locs[3]
    assert c.subrequests == ["/_v"] and c.proxies == []
    assert [(x.modifier, x.pattern, x.order, x.proxies) for x in c.children] == [("~*", "\\.js$", 4, [("w-u", None)])]
    assert locs[1].proxies == [(None, None)]


def test_unlinked_config_links_to_single_nginx_workload_as_candidate(tmp_path):
    _write(tmp_path, "docker-compose.yml", _compose([
        ("proxy", "    image: nginx:1.27\n"), ("api", "    image: acme/api:1\n")]))
    _write(tmp_path, "deploy/site.conf", "server { location / { proxy_pass http://api:8000; } }\n")
    _, routes = _run(tmp_path)
    assert [(r.proxy, r.target, r.status) for r in routes] == [("w-proxy", "w-api", "candidate")]


def test_unlinked_config_with_two_nginx_workloads_is_not_linked(tmp_path):
    _write(tmp_path, "docker-compose.yml", _compose([
        ("proxy", "    image: nginx:1.27\n"), ("edge", "    image: nginx:1.25\n"),
        ("api", "    image: acme/api:1\n")]))
    _write(tmp_path, "deploy/site.conf", "server { location / { proxy_pass http://api:8000; } }\n")
    assert _run(tmp_path) == ([], [])


def test_missing_include_broken_file_and_include_cycle(tmp_path):
    _write(tmp_path, "docker-compose.yml", _compose([
        ("proxy", "    image: nginx:1.27\n    volumes:\n      - ./conf:/etc/nginx/conf.d\n"),
        ("api", "    image: acme/api:1\n")]))
    _write(tmp_path, "conf/a.conf", "include /etc/nginx/conf.d/b.inc;\ninclude /etc/nginx/missing/*.conf;\n"
           "server { location / { include conf.d/b.inc; proxy_pass http://api; } }\n")
    _write(tmp_path, "conf/b.inc", "include /etc/nginx/conf.d/a.conf;\ninclude /etc/nginx/conf.d/b.inc;\n")
    _write(tmp_path, "conf/broken.conf", "server { location / { proxy_pass http://api;\n")
    servers, routes = _run(tmp_path)
    assert [(r.location, r.target) for r in routes] == [(("", "/"), "w-api")]
    assert len(servers) == 1


def test_copy_all_into_non_nginx_workload_does_not_link_config(tmp_path):
    _write(tmp_path, "docker-compose.yml", _compose([
        ("api", "    build: .\n"), ("web", "    image: nginx:1.27\n")]))
    _write(tmp_path, "Dockerfile", "FROM python:3.12\nWORKDIR /app\nCOPY . .\n")
    _write(tmp_path, "deploy/nginx.conf", "events {}\nhttp { server { location / { proxy_pass http://api:8000; } } }\n")
    servers, routes = _run(tmp_path)
    assert [s.proxy for s in servers] == ["w-web"]
    assert [(r.proxy, r.target, r.status) for r in routes] == [("w-web", "w-api", "candidate")]


def test_sub_second_times_round_up():
    from infrafit.detect.nginx import _seconds
    assert [_seconds(x) for x in ("500ms", "1500ms", "0", "0s", "1m30s", "15", "abc", "1x")] == [
        1, 2, 0, 0, 90, 15, "abc", "1x"]


def test_service_selector_matches_name_prefixed_workload_by_label(tmp_path):
    _write(tmp_path, "proxy/Dockerfile", "FROM nginx:1.27\nCOPY default.conf /etc/nginx/conf.d/default.conf\n")
    _write(tmp_path, "proxy/default.conf", "server { location / { proxy_pass http://backend; } }\n")
    env = Environment("dev", "k8s/overlays/dev/kustomization.yaml", True, [
        {"kind": "Deployment", "metadata": {"name": "dev-proxy", "labels": {"app.kubernetes.io/name": "proxy"}}},
        {"kind": "Service", "metadata": {"name": "backend"}, "spec": {"selector": {"app": "be"}}},
        {"kind": "Deployment", "metadata": {"name": "dev-api", "labels": {"app.kubernetes.io/name": "api"}},
         "spec": {"template": {"metadata": {"labels": {"app": "be"}}}}}])
    _, routes = _run(tmp_path, [_w("proxy", "acme/proxy:1"), _w("api")], [env])
    assert [(r.environment, r.target, r.status) for r in routes] == [("dev", "w-api", "confirmed")]


def test_k8s_env_uses_container_matching_workload_image(tmp_path):
    _write(tmp_path, "proxy/Dockerfile", "FROM nginx:1.27\nCOPY default.conf /etc/nginx/conf.d/default.conf\n")
    _write(tmp_path, "proxy/default.conf", "server { location / { proxy_pass http://${UP}; } }\n")
    env = Environment("dev", "k8s/overlays/dev/kustomization.yaml", True, [
        {"kind": "Deployment", "metadata": {"name": "proxy"}, "spec": {"template": {"spec": {"containers": [
            {"name": "sidecar", "image": "acme/sidecar:1", "env": [{"name": "UP", "value": "b"}]},
            {"name": "nginx", "image": "acme/proxy:1", "env": [{"name": "UP", "value": "a"}]}]}}}}])
    _, routes = _run(tmp_path, [_w("proxy", "acme/proxy:1"), _w("a"), _w("b")], [env])
    assert [r.target for r in routes] == ["w-a"]


def test_pathological_glob_includes_terminate(tmp_path):
    import time
    _write(tmp_path, "docker-compose.yml", _compose([
        ("proxy", "    image: nginx:1.27\n    volumes:\n      - ./conf.d:/etc/nginx/conf.d\n      - ./x:/etc/nginx/x\n"),
        ("api", "    image: acme/api:1\n")]))
    _write(tmp_path, "conf.d/site.conf",
           "server { location / { include /etc/nginx/x/*.inc; proxy_pass http://api; } }\n")
    for i in range(20):
        _write(tmp_path, f"x/{i:02d}.inc", "include /etc/nginx/x/*.inc;\nproxy_set_header A b;\n")
    start = time.monotonic()
    _, routes = _run(tmp_path)
    assert time.monotonic() - start < 5
    assert [r.target for r in routes] == ["w-api"]


def test_upstream_with_several_servers_gives_route_per_server(tmp_path):
    _write(tmp_path, "docker-compose.yml", _compose([
        ("proxy", "    image: nginx:1.27\n    volumes:\n      - ./default.conf:/etc/nginx/conf.d/default.conf\n"),
        ("a", "    image: acme/a:1\n"), ("b", "    image: acme/b:1\n")]))
    _write(tmp_path, "default.conf",
           "upstream u { server a:80; server b:80 backup; server nowhere:80; }\n"
           "server { location / { proxy_pass http://u; } }\n")
    servers, routes = _run(tmp_path)
    assert sorted((r.upstream, r.target or "") for r in routes) == [("u", ""), ("u", "w-a"), ("u", "w-b")]
    assert sorted(servers[0].locations[0].proxies, key=str) == sorted(
        [("w-a", None), ("w-b", None), (None, None)], key=str)


def test_compose_environment_beats_dockerfile_env_and_env_space_form(tmp_path):
    _write(tmp_path, "docker-compose.yml", _compose([
        ("proxy", "    build: .\n    environment:\n      - UP=b:80\n"),
        ("a", "    image: acme/a:1\n"), ("b", "    image: acme/b:1\n")]))
    _write(tmp_path, "Dockerfile", "FROM nginx:1.27\nENV UP a:80\nENV OTHER a\n"
           "COPY default.conf /etc/nginx/conf.d/default.conf\n")
    _write(tmp_path, "default.conf",
           "server { location / { proxy_pass http://${UP}; } location /o { proxy_pass http://${OTHER}; } }\n")
    _, routes = _run(tmp_path)
    assert {r.location[1]: r.target for r in routes} == {"/": "w-b", "/o": "w-a"}


def test_copy_sources_resolve_against_compose_build_context(tmp_path):
    cases = {
        # 컨텍스트가 저장소 루트
        "root": ("{context: ., dockerfile: services/web/Dockerfile}", "services/web/nginx/", "services/web/nginx"),
        # 컨텍스트가 Dockerfile 디렉터리도 저장소 루트도 아니다
        "sub": ("{context: services, dockerfile: web/Dockerfile}", "web/nginx/", "services/web/nginx"),
        # Dockerfile 디렉터리 기준 경로도 있지만 실제 빌드는 컨텍스트(루트) 기준이다
        "decoy": ("{context: ., dockerfile: services/web/Dockerfile}", "nginx/", "nginx"),
    }
    for name, (build, src, conf_dir) in cases.items():
        root = tmp_path / name
        _write(root, "docker-compose.yml", _compose([("web", f"    build: {build}\n"),
                                                     ("api", "    image: acme/api:1\n")]))
        _write(root, "services/web/Dockerfile", f"FROM nginx:1.27\nCOPY {src} /etc/nginx/conf.d/\n")
        _write(root, f"{conf_dir}/app.conf", "server { location / { proxy_pass http://api:8000; } }\n")
        if name == "decoy":
            _write(root, "services/web/nginx/app.conf", "server { location / { proxy_pass http://other:1; } }\n")
        _, routes = _run(root)
        assert [(r.proxy, r.target, r.status, r.evidence["path"]) for r in routes] == [
            ("w-web", "w-api", "confirmed", f"{conf_dir}/app.conf")], name
