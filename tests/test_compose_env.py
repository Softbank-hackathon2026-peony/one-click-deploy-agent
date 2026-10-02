from infrafit.detect.artifacts import parse_artifacts
from infrafit.detect.environments import detect_environments, env_command, workload_in
from infrafit.detect.manifests import parse_manifests
from infrafit.detect.nginx import find_proxies
from infrafit.detect.paths import build_paths
from infrafit.detect.workloads import detect_workloads
from infrafit.repo import open_snapshot


def _write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def _analyze(root):
    snap = open_snapshot(str(root), root / "_w")
    arts = parse_artifacts(snap)
    ws = detect_workloads(snap, parse_manifests(snap), arts)
    envs = detect_environments(arts, ws)
    proxy = find_proxies(snap, ws, arts, envs)
    paths = build_paths(snap, ws, arts, {}, envs, proxy)
    return snap, arts, ws, envs, proxy, paths


def _env(envs, name):
    return next(e for e in envs if e.name == name)


def test_base_override_and_variant_merge(tmp_path):
    _write(tmp_path, "docker-compose.yml", "services:\n  api:\n    image: acme/api:1\n"
           "    environment:\n      - A=1\n      - B=2\n  worker:\n    image: acme/worker:1\n")
    _write(tmp_path, "docker-compose.override.yml", "services:\n  api:\n    command: uvicorn main:app\n"
           "    environment:\n      B: '3'\n      C: '4'\n")
    _write(tmp_path, "docker-compose.prod.yml", "services:\n  api:\n    environment:\n      - A=9\n"
           "  extra:\n    image: acme/extra:1\n")
    _write(tmp_path, "sub/compose.dev.yaml", "services:\n  web:\n    image: acme/web:1\n")
    snap, _, _, envs, _, _ = _analyze(tmp_path)
    assert [(e.name, e.kind, e.rendered, e.source) for e in envs] == [
        ("compose", "compose", True, "docker-compose.yml"),
        ("compose.dev/sub", "compose", True, "sub/compose.dev.yaml"),
        ("compose.prod", "compose", True, "docker-compose.prod.yml")]
    base, prod = _env(envs, "compose"), _env(envs, "compose.prod")
    assert sorted(base.services) == ["api", "worker"]
    assert base.services["api"]["environment"] == {"A": "1", "B": "3", "C": "4"}
    assert base.services["api"]["command"] == "uvicorn main:app"
    assert base.services["api"]["image"] == "acme/api:1"
    assert sorted(prod.services) == ["api", "extra", "worker"]
    assert prod.services["api"]["environment"] == {"A": "9", "B": "3", "C": "4"}
    assert prod.services["api"]["command"] == "uvicorn main:app"
    d = prod.to_dict(snap)
    assert (d["name"], d["kind"], d["rendered"], d["source"]["path"]) == (
        "compose.prod", "compose", True, "docker-compose.prod.yml")


DEPLOY = ("apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: {name}\nspec:\n"
          "  selector:\n    matchLabels: {{app: {name}}}\n  template:\n    metadata:\n      labels: {{app: {name}}}\n"
          "    spec:\n      containers:\n      - name: {name}\n        image: {image}\n{extra}"
          "---\napiVersion: v1\nkind: Service\nmetadata:\n  name: {name}\nspec:\n  selector: {{app: {name}}}\n"
          "  ports:\n  - port: 80\n")


def _deploy(name, image, extra=""):
    return DEPLOY.format(name=name, image=image, extra=extra)


def test_service_workload_matching(tmp_path):
    _write(tmp_path, "k8s/api.yaml", _deploy("api", "acme/api:1"))
    _write(tmp_path, "k8s/api-verify.yaml", _deploy("api-verify", "acme/api:1"))
    _write(tmp_path, "k8s/db-migrate.yaml", _deploy("db-migrate", "acme/migrate:1"))
    _write(tmp_path, "migrate/Dockerfile", "FROM python:3.12\nCMD python migrate.py\n")
    _write(tmp_path, "docker-compose.yml", "services:\n  api:\n    image: acme/api:1\n"
           "  migrate:\n    build: ./migrate\n")
    _, _, ws, envs, _, _ = _analyze(tmp_path)
    env = _env(envs, "compose")
    assert env.members == {"w-api": "api", "w-db-migrate": "migrate"}
    by_id = {w.id: w for w in ws}
    assert workload_in(env, by_id["w-api"]) and not workload_in(env, by_id["w-api-verify"])


def test_ambiguous_candidates_do_not_match(tmp_path):
    _write(tmp_path, "k8s/a.yaml", _deploy("a", "acme/app:1"))
    _write(tmp_path, "k8s/b.yaml", _deploy("b", "acme/app:2"))
    _write(tmp_path, "docker-compose.yml", "services:\n  app:\n    image: registry.io/acme/app:3\n")
    _, _, _, envs, _, _ = _analyze(tmp_path)
    assert _env(envs, "compose").members == {}


def _mixed_repo(root):
    """kustomize overlay(dev)와 compose가 같은 nginx 프록시를 다르게 설정한다."""
    _write(root, "proxy/Dockerfile", "FROM nginx:1.27\n"
           "COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template\n")
    _write(root, "nginx/default.conf.template",
           "server {\n  proxy_read_timeout 22s;\n  location / { proxy_pass http://${UP}; }\n}\n")
    _write(root, "nginx/compose.conf.template",
           "server {\n  proxy_read_timeout 11s;\n  location / { proxy_pass http://${UP}; }\n}\n")
    envfrom = "        envFrom:\n        - configMapRef: {name: proxy-cfg}\n"
    _write(root, "k8s/base/proxy.yaml", _deploy("proxy", "acme/proxy:1", envfrom)
           + "---\napiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: proxy-cfg\ndata:\n  UP: api-verify:8000\n")
    args = ('        command: ["uvicorn", "main:app"]\n'
            '        args: ["--timeout-keep-alive", "30"]\n')
    _write(root, "k8s/base/api.yaml", _deploy("api", "acme/api:1", args))
    _write(root, "k8s/base/api-verify.yaml", _deploy("api-verify", "acme/api:1", args))
    _write(root, "k8s/base/kustomization.yaml", "resources: [proxy.yaml, api.yaml, api-verify.yaml]\n")
    _write(root, "k8s/overlays/dev/kustomization.yaml",
           "resources: [../../base]\npatches:\n- target: {kind: Deployment, name: api}\n  patch: |-\n"
           "    - op: replace\n      path: /spec/template/spec/containers/0/args\n"
           '      value: ["--timeout-keep-alive", "45"]\n')
    _write(root, "docker-compose.yml", "services:\n  proxy:\n"
           "    build: {context: ., dockerfile: proxy/Dockerfile}\n"
           "    environment:\n      - UP=api:8000\n"
           "    volumes:\n      - ./nginx/compose.conf.template:/etc/nginx/templates/default.conf.template:ro\n"
           "  api:\n    image: acme/api:1\n    command: uvicorn main:app --timeout-keep-alive 5\n")


def test_bind_mount_overrides_image_config_only_in_compose(tmp_path):
    _mixed_repo(tmp_path)
    _, _, _, envs, (servers, routes), _ = _analyze(tmp_path)
    assert [e.name for e in envs] == ["compose", "dev"]
    files = {(s.proxy, s.environment): s.evidence["path"] for s in servers}
    assert files == {("w-proxy", "compose"): "nginx/compose.conf.template",
                     ("w-proxy", "dev"): "nginx/default.conf.template"}


def test_proxy_target_per_environment(tmp_path):
    _mixed_repo(tmp_path)
    _, _, _, _, (_, routes), _ = _analyze(tmp_path)
    assert [(r.environment, r.upstream, r.target, r.status) for r in routes] == [
        ("compose", "${UP}", "w-api", "confirmed"), ("dev", "${UP}", "w-api-verify", "confirmed")]


def test_app_server_uses_environment_command(tmp_path):
    _mixed_repo(tmp_path)
    _, arts, ws, envs, _, paths = _analyze(tmp_path)
    by_id = {p["id"]: p for p in paths}
    assert sorted(by_id) == ["path-api-verify.dev", "path-api.compose", "path-api.dev",
                             "path-proxy.compose", "path-proxy.dev"]

    def keep_alive(pid):
        hop = next(h for h in by_id[pid]["hops"] if h["kind"] == "app-server")
        return next(s["value"] for s in hop["settings"] if s["key"] == "timeout_keep_alive")

    assert (keep_alive("path-api.compose"), keep_alive("path-api.dev")) == (5, 45)
    # compose 환경에는 로드밸런서·엣지가 없고, 프록시를 거친다
    assert [h["kind"] for h in by_id["path-api.compose"]["hops"]] == ["reverse-proxy", "app-server"]
    api = next(w for w in ws if w.id == "w-api")
    assert env_command(_env(envs, "dev"), api, arts) == "uvicorn main:app --timeout-keep-alive 45"
    assert env_command(None, api, arts) == api.command


def test_compose_command_falls_back_to_build_dockerfile(tmp_path):
    _write(tmp_path, "k8s/app.yaml", _deploy("app", "acme/app:1"))
    _write(tmp_path, "app/Dockerfile", 'FROM python:3.12\nENTRYPOINT ["uvicorn"]\nCMD ["main:app"]\n')
    _write(tmp_path, "docker-compose.yml", "services:\n  app:\n    build: ./app\n")
    _, arts, ws, envs, _, paths = _analyze(tmp_path)
    assert env_command(_env(envs, "compose"), ws[0], arts) == "uvicorn main:app"
    hop = next(p for p in paths if p["id"] == "path-app.compose")["hops"][0]
    assert [(e["path"], e["line"]) for e in hop["evidence"]] == [("app/Dockerfile", 2), ("app/Dockerfile", 3)]


def test_compose_only_repo(tmp_path):
    _write(tmp_path, "docker-compose.yml", "services:\n  api:\n    build: ./api\n")
    _write(tmp_path, "api/Dockerfile", "FROM python:3.12\nCMD uvicorn main:app\n")
    _, _, ws, envs, _, paths = _analyze(tmp_path)
    assert [(e.name, e.members) for e in envs] == [("compose", {"w-api": "api"})]
    assert [(p["id"], p["environment"]) for p in paths] == [("path-api.compose", "compose")]
    assert [h["component"] for h in paths[0]["hops"]] == ["nw:app/uvicorn/default"]


def test_broken_or_empty_compose_gives_no_environment(tmp_path):
    _write(tmp_path, "docker-compose.yml", "services: [\n")
    _write(tmp_path, "b/compose.yaml", "version: '3'\n")
    _write(tmp_path, "c/docker-compose.yml", "services:\n  x: 1\n  y: [1]\n")
    _write(tmp_path, "c/docker-compose.override.yml", "- not a map\n")
    _write(tmp_path, "d/compose.yml", "services: {}\n")
    _write(tmp_path, "d/compose.prod.yml", "services:\n  api:\n    environment: 5\n")
    _write(tmp_path, "d/compose.override.yml", "services:\n  api:\n    environment: [1, X]\n")
    _, _, _, envs, _, _ = _analyze(tmp_path)
    names = [e.name for e in envs]
    assert "compose" not in names and "compose/b" not in names
    # 서비스 본문이 dict가 아니어도 서비스는 있다(빈 정의)
    assert _env(envs, "compose/c").services == {"x": {}, "y": {}}
    assert _env(envs, "compose.prod/d").services["api"]["environment"] == 5


def _app_server_evidence(paths, pid):
    hop = next(h for p in paths if p["id"] == pid for h in p["hops"] if h["kind"] == "app-server")
    return [(e["path"], e["line"]) for e in hop["evidence"]]


def test_app_server_evidence_follows_command_source(tmp_path):
    _mixed_repo(tmp_path)
    _write(tmp_path, "docker-compose.override.yml",
           "services:\n  api:\n    environment: [X=1]\n    command: uvicorn main:app --timeout-keep-alive 6\n")
    _, _, ws, _, _, paths = _analyze(tmp_path)
    assert _app_server_evidence(paths, "path-api.compose") == [("docker-compose.override.yml", 4)]
    # 렌더 명령이 워크로드 명령과 다르면 그 환경의 kustomization.yaml
    assert _app_server_evidence(paths, "path-api.dev") == [("k8s/overlays/dev/kustomization.yaml", None)]
    verify = next(w for w in ws if w.id == "w-api-verify")
    assert _app_server_evidence(paths, "path-api-verify.dev") == [
        (verify.entrypoint["path"], verify.entrypoint["line"])]


INGRESS = ("apiVersion: networking.k8s.io/v1\nkind: Ingress\nmetadata:\n  name: api\nspec:\n"
           "  ingressClassName: nginx\n  defaultBackend:\n    service: {name: api, port: {number: 80}}\n")


def test_plain_k8s_workload_keeps_null_path_beside_compose(tmp_path):
    _write(tmp_path, "k8s/api.yaml", _deploy("api", "acme/api:1", '        command: ["uvicorn", "main:app"]\n'))
    _write(tmp_path, "k8s/ingress.yaml", INGRESS)
    _write(tmp_path, "docker-compose.yml", "services:\n  api:\n    image: acme/api:1\n"
           "    command: uvicorn main:app\n")
    _, _, _, _, _, paths = _analyze(tmp_path)
    kinds = {p["id"]: [h["kind"] for h in p["hops"]] for p in paths}
    assert kinds == {"path-api": ["load-balancer", "app-server"], "path-api.compose": ["app-server"]}
