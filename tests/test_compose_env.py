from infrafit.detect.artifacts import ParsedArtifact, parse_artifacts
from infrafit.detect.environments import detect_environments, env_command, workload_in
from infrafit.detect.manifests import parse_manifests
from infrafit.detect.nginx import find_proxies
from infrafit.detect.paths import build_paths
from infrafit.detect.workloads import WorkloadInfo, detect_workloads
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
    # 변형 환경은 기본 + 변형만 병합한다(override 제외, F3)
    assert prod.services["api"]["environment"] == {"A": "9", "B": "2"}
    assert "command" not in prod.services["api"]
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
    # 대응한 워크로드가 없는 compose는 환경을 만들지 않는다(F7)
    assert [e.name for e in envs] == []


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


def test_only_plain_override_merges_into_base(tmp_path):
    _write(tmp_path, "compose.yaml", "services:\n  api:\n    image: acme/api:1\n")
    _write(tmp_path, "compose.override.yaml", "services:\n  api:\n    command: a\n")
    _write(tmp_path, "compose.prod.override.yml", "services:\n  api:\n    command: b\n")
    _, _, _, envs, _, _ = _analyze(tmp_path)
    assert [(e.name, e.source, e.services["api"].get("command")) for e in envs] == [
        ("compose", "compose.yaml", "a"), ("compose.prod.override", "compose.prod.override.yml", "b")]


def test_compose_name_colliding_with_kustomize_gets_source_dir():
    arts = [ParsedArtifact("k8s", "k8s/overlays/compose/kustomization.yaml#build", True, objects=[]),
            ParsedArtifact("compose", "docker-compose.yml", True, objects=[("api", {})])]
    api = WorkloadInfo("w-api", "web", "api", {}, "confirmed", "compose")
    envs = detect_environments(arts, [api])
    assert [(e.name, e.kind) for e in envs] == [("compose", "kustomize"), ("compose@root", "compose")]


def test_directory_mount_hides_image_files_under_it(tmp_path):
    _write(tmp_path, "proxy/Dockerfile", "FROM nginx:1.27\nCOPY templates/ /etc/nginx/templates/\n")
    _write(tmp_path, "proxy/templates/default.conf.template",
           "server {\n  location / { proxy_pass http://api:8000; }\n}\n")
    _write(tmp_path, "proxy/templates/extra.conf.template",
           "server {\n  listen 81;\n  location / { proxy_pass http://api:8000; }\n}\n")
    _write(tmp_path, "nginx-dev/default.conf.template",
           "server {\n  proxy_read_timeout 7s;\n  location / { proxy_pass http://api:8000; }\n}\n")
    _write(tmp_path, "k8s/proxy.yaml", _deploy("proxy", "acme/proxy:1"))
    _write(tmp_path, "k8s/api.yaml", _deploy("api", "acme/api:1"))
    _write(tmp_path, "docker-compose.yml", "services:\n  proxy:\n    image: acme/proxy:1\n"
           "    volumes:\n      - ./nginx-dev:/etc/nginx/templates\n  api:\n    image: acme/api:1\n")
    _, _, _, _, (servers, _), _ = _analyze(tmp_path)
    by_env = {}
    for s in servers:
        by_env.setdefault(s.environment, []).append(s.evidence["path"])
    assert by_env == {None: ["proxy/templates/default.conf.template", "proxy/templates/extra.conf.template"],
                      "compose": ["nginx-dev/default.conf.template"]}


# --- 최종 리뷰 F1·F2·F3·F5·F7 ---------------------------------------------------

def test_variant_without_services_makes_no_environment(tmp_path):
    # F1: 파싱에 실패했거나 서비스가 없는 변형 파일은 기본 파일을 베낀 환경을 만들지 않는다
    _write(tmp_path, "docker-compose.yml", "services:\n  api:\n    image: acme/api:1\n")
    _write(tmp_path, "docker-compose.broken.yml", "services: [\n")
    _write(tmp_path, "compose.empty.yaml", "version: '3'\n")
    _, _, _, envs, _, _ = _analyze(tmp_path)
    assert [e.name for e in envs] == ["compose"]


def test_merge_follows_docker_for_volumes_ports_environment(tmp_path):
    # F2: volumes는 컨테이너 경로 단위, ports·expose는 겹치지 않게 덧붙이고, environment는 변수 이름 단위
    _write(tmp_path, "docker-compose.yml", "services:\n  api:\n    image: acme/api:1\n"
           "    volumes:\n      - ./a:/x\n      - ./b:/y:ro\n      - {type: bind, source: ./c, target: /z}\n"
           "    ports: ['80:80']\n    expose: ['9000']\n    environment: [A=1]\n")
    _write(tmp_path, "docker-compose.override.yml", "services:\n  api:\n"
           "    volumes:\n      - ./b2:/y\n      - ./d:/w\n"
           "    ports: ['80:80', '81:81']\n    expose: ['9001']\n    environment: {B: 2}\n")
    _, _, _, envs, _, _ = _analyze(tmp_path)
    api = _env(envs, "compose").services["api"]
    assert api["volumes"] == ["./a:/x", "./b2:/y", {"type": "bind", "source": "./c", "target": "/z"}, "./d:/w"]
    assert api["ports"] == ["80:80", "81:81"]
    assert api["expose"] == ["9000", "9001"]
    assert api["environment"] == {"A": "1", "B": "2"}


def test_override_mount_keeps_base_mounts_for_proxy_config(tmp_path):
    # F2: override가 마운트 하나를 더해도 기본 파일의 nginx 설정 마운트는 남는다
    _write(tmp_path, "docker-compose.yml", "services:\n  proxy:\n    image: nginx:1.27\n"
           "    volumes:\n      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro\n  api:\n    build: ./api\n")
    _write(tmp_path, "docker-compose.override.yml", "services:\n  proxy:\n    volumes:\n      - ./logs:/var/log/nginx\n")
    _write(tmp_path, "nginx.conf", "server {\n  location / { proxy_pass http://api:8000; }\n}\n")
    _write(tmp_path, "api/Dockerfile", "FROM python:3.12\nCMD uvicorn main:app\n")
    _, _, _, _, (_, routes), _ = _analyze(tmp_path)
    assert [(r.environment, r.target) for r in routes] == [("compose", "w-api")]


def test_variant_environment_does_not_include_override(tmp_path):
    # F3: 변형 환경 = 기본 + 변형(`docker compose -f base -f variant`), override는 기본 환경에만
    _write(tmp_path, "docker-compose.yml", "services:\n  api:\n    image: acme/api:1\n    environment: [A=1]\n")
    _write(tmp_path, "docker-compose.override.yml", "services:\n  api:\n    command: dev\n"
           "    environment: [B=2]\n")
    _write(tmp_path, "docker-compose.prod.yml", "services:\n  api:\n    environment: [C=3]\n")
    _, _, _, envs, _, _ = _analyze(tmp_path)
    base, prod = _env(envs, "compose").services["api"], _env(envs, "compose.prod").services["api"]
    assert (base.get("command"), base["environment"]) == ("dev", {"A": "1", "B": "2"})
    assert (prod.get("command"), prod["environment"]) == (None, {"A": "1", "C": "3"})


def test_args_only_overlay_keeps_image_entrypoint(tmp_path):
    # F5: command 없이 args만 바꾼 overlay는 이미지 ENTRYPOINT 뒤에 args
    _write(tmp_path, "api/Dockerfile", 'FROM python:3.12\nENTRYPOINT ["uvicorn"]\nCMD ["main:app"]\n')
    _write(tmp_path, "k8s/base/api.yaml", _deploy("api", "acme/api:1"))
    _write(tmp_path, "k8s/base/kustomization.yaml", "resources: [api.yaml]\n")
    _write(tmp_path, "k8s/overlays/dev/kustomization.yaml",
           "resources: [../../base]\npatches:\n- target: {kind: Deployment, name: api}\n  patch: |-\n"
           "    - op: add\n      path: /spec/template/spec/containers/0/args\n"
           '      value: ["main:app", "--timeout-keep-alive", "45"]\n')
    _, arts, ws, envs, _, paths = _analyze(tmp_path)
    api = next(w for w in ws if w.id == "w-api")
    assert env_command(_env(envs, "dev"), api, arts) == "uvicorn main:app --timeout-keep-alive 45"
    hop = next(h for p in paths if p["id"] == "path-api.dev" for h in p["hops"] if h["kind"] == "app-server")
    assert hop["component"] == "nw:app/uvicorn/default"
    assert next(s["value"] for s in hop["settings"] if s["key"] == "timeout_keep_alive") == 45


def test_devcontainer_and_infra_only_compose_make_no_environment(tmp_path):
    # F7: .devcontainer compose와 대응한 워크로드가 없는 compose는 환경이 아니다
    _write(tmp_path, "k8s/api.yaml", _deploy("api", "acme/api:1"))
    _write(tmp_path, ".devcontainer/docker-compose.yml", "services:\n  api:\n    image: acme/api:1\n")
    _write(tmp_path, "infra/docker-compose.yml", "services:\n  db:\n    image: postgres:16\n")
    _, _, _, envs, _, _ = _analyze(tmp_path)
    assert envs == []


def test_dash_named_variant_and_override_family(tmp_path):
    # F7: docker-compose-<x>.yml은 변형, override는 같은 계열의 기본 파일에만 병합한다
    _write(tmp_path, "docker-compose.yml", "services:\n  api:\n    image: acme/api:1\n")
    _write(tmp_path, "compose.override.yaml", "services:\n  api:\n    command: other-family\n")
    _write(tmp_path, "docker-compose-prod.yml", "services:\n  api:\n    command: prod\n")
    _, _, _, envs, _, _ = _analyze(tmp_path)
    assert [(e.name, e.source, e.services["api"].get("command")) for e in envs] == [
        ("compose", "docker-compose.yml", None), ("compose.prod", "docker-compose-prod.yml", "prod")]


def test_valueless_compose_variable_is_absent(tmp_path):
    # F6: 값 없는 `KEY`는 호스트 값을 받으므로(알 수 없음) 없음으로 보고, 이미지 ENV가 남는다
    _write(tmp_path, "proxy/Dockerfile", "FROM nginx:1.27\nENV UP=b:8000\n")
    _write(tmp_path, "docker-compose.yml", "services:\n  proxy:\n    build: ./proxy\n"
           "    environment: [UP=a:8000]\n"
           "    volumes:\n      - ./nginx.conf.template:/etc/nginx/templates/default.conf.template:ro\n"
           "  a:\n    image: acme/a:1\n  b:\n    image: acme/b:1\n")
    _write(tmp_path, "docker-compose.override.yml", "services:\n  proxy:\n    environment:\n      UP:\n")
    _write(tmp_path, "nginx.conf.template", "server {\n  location / { proxy_pass http://${UP}; }\n}\n")
    _, _, _, envs, (_, routes), _ = _analyze(tmp_path)
    assert _env(envs, "compose").services["proxy"]["environment"] == {"UP": None}
    assert [(r.environment, r.target) for r in routes] == [("compose", "w-b")]
