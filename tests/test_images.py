import json

from infrafit import kb
from infrafit.consistency import check_run
from infrafit.detect.artifacts import parse_artifacts
from infrafit.detect.images import classify_image
from infrafit.detect.manifests import parse_manifests
from infrafit.detect.workloads import detect_workloads
from infrafit.kb_lint import _lint_images
from infrafit.pipeline import analyze
from infrafit.repo import open_snapshot

APP = "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/health')\ndef h():\n    return 'ok'\n"


def _write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def _inventory(tmp_path, run_id="r"):
    ctx = analyze(str(tmp_path / "repo"), tmp_path / "out", until="S1", run_id=run_id)
    assert check_run(ctx.out_dir) == []
    return json.loads((ctx.out_dir / "inventory.json").read_text())


def _workloads(root):
    snap = open_snapshot(str(root), root.parent / "_w")
    return detect_workloads(snap, parse_manifests(snap), parse_artifacts(snap))


def test_classify_image_names():
    assert classify_image("nginx:1.27-alpine")["role"] == "reverse-proxy"
    assert classify_image("nginxinc/nginx-unprivileged:stable")["component"] == "nw:proxy/nginx/default"
    assert classify_image("docker.io/library/postgres@sha256:abc")["component"] == "ds:unspecified/postgresql/default"
    assert classify_image("localhost:5000/redis:7")["role"] == "cache"
    assert classify_image("temporalio/auto-setup:1.22")["label"] == "temporalio/auto-setup"
    hint = classify_image("gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.8")
    assert (hint["role"], hint["hosting_hint"], hint["label"]) == (
        "infra", "ds:gcp/cloudsql-postgres/single", "cloud-sql-proxy")
    assert classify_image("dpage/pgadmin4:8")["role"] == "dev-tool"
    assert classify_image("acme/nginx-app:1") is None
    assert classify_image("acme/redis-exporter:1") is None
    assert classify_image("acme/data-exporter:2") is None  # 사용자 이미지 이름의 -exporter는 앱이다(FC3)
    assert classify_image("") is None


def test_compose_nginx_is_reverse_proxy_not_endpoint_owner(tmp_path):
    repo = tmp_path / "repo"
    _write(repo, "requirements.txt", "fastapi==0.115\nasyncpg==0.29\n")
    _write(repo, "main.py", APP)
    _write(repo, "docker-compose.yml",
           "services:\n  web:\n    image: acme/web:1\n    command: uvicorn main:app\n"
           "  nginx:\n    image: nginx:alpine\n    volumes:\n      - ./nginx.conf:/etc/nginx/conf.d/default.conf\n")
    _write(repo, "nginx.conf", "server {\n  listen 80;\n  location / {\n    proxy_pass http://web:8000;\n  }\n}\n")
    inv = _inventory(tmp_path)
    kinds = {w["id"]: w["kind"] for w in inv["workloads"]}
    assert kinds == {"w-nginx": "reverse-proxy", "w-web": "web"}
    assert {(e["workload"], e["status"]) for e in inv["endpoints"] if e["route"] not in ("/docs", "/redoc", "/openapi.json")} == {("w-web", "confirmed")}
    ds = next(d for d in inv["datastores"] if d["id"] == "ds-postgresql")
    assert ds["used_by"] == ["w-web"]
    nginx_path = next(p for p in inv["request_paths"] if p["workload"] == "w-nginx")
    assert [h["kind"] for h in nginx_path["hops"]] == ["reverse-proxy"]


def test_third_party_images_and_dockerfile_worker(tmp_path):
    repo = tmp_path / "repo"
    _write(repo, "docker-compose.yml",
           "services:\n  temporal:\n    image: temporalio/auto-setup:1.22\n"
           "  cloudsql:\n    image: gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.8\n"
           "  postgres:\n    image: postgres:16\n  adminer:\n    image: adminer\n")
    _write(repo, "docker/worker.Dockerfile", 'FROM node:20\nCMD ["node", "dist/workers/cloud.js"]\n')
    _write(repo, ".devcontainer/Dockerfile", 'FROM node:20\nCMD ["sleep", "infinity"]\n')
    inv = _inventory(tmp_path)
    assert [(w["id"], w["kind"], w["status"]) for w in inv["workloads"]] == [("w-worker", "worker", "candidate")]
    assert inv["workloads"][0]["entrypoint"]["path"] == "docker/worker.Dockerfile"
    labels = {u["label"]: u["evidence"] for u in inv["unmapped"]}
    assert set(labels) == {"image:temporalio/auto-setup", "image:cloud-sql-proxy",
                           "hosting-hint:ds:gcp/cloudsql-postgres/single"}
    assert labels["image:temporalio/auto-setup"][0]["path"] == "docker-compose.yml"
    assert labels["hosting-hint:ds:gcp/cloudsql-postgres/single"][0]["line"] == 4
    ds = next(d for d in inv["datastores"] if d["id"] == "ds-postgresql")
    assert ds["status"] == "candidate"
    assert [(e["path"], e["line"]) for e in ds["evidence"]] == [("docker-compose.yml", 6)]
    comp = next(c for c in inv["current_components"] if c["scope"] == "ds-postgresql")
    assert (comp["component"], comp["status"]) == ("ds:unspecified/postgresql/default", "candidate")


def test_compose_datastore_used_by_depends_on(tmp_path):
    repo = tmp_path / "repo"
    _write(repo, "docker-compose.yml",
           "services:\n  postgres:\n    image: postgres:16\n  redis:\n    image: redis:7\n"
           "  api:\n    image: acme/api:1\n    depends_on: [postgres]\n"
           "  jobs:\n    image: acme/jobs:1\n    depends_on:\n      postgres:\n        condition: service_healthy\n"
           "  other:\n    image: acme/other:1\n")
    inv = _inventory(tmp_path)
    ds = {d["id"]: d for d in inv["datastores"]}
    assert (ds["ds-postgresql"]["status"], ds["ds-postgresql"]["used_by"]) == ("candidate", ["w-api", "w-jobs"])
    # 아무도 depends_on하지 않으면 사용 주체 규칙(모든 백엔드 워크로드)
    assert ds["svc-redis"]["used_by"] == ["w-api", "w-jobs", "w-other"]


def test_compose_evidence_joins_signature_scope(tmp_path):
    repo = tmp_path / "repo"
    _write(repo, "requirements.txt", "fastapi==0.115\nasyncpg==0.29\n")
    _write(repo, "main.py", APP)
    _write(repo, "docker-compose.yml", "services:\n  db:\n    image: postgres:16\n"
                                       "  api:\n    image: acme/api:1\n    depends_on: [db]\n")
    inv = _inventory(tmp_path)
    assert [d["id"] for d in inv["datastores"]] == ["ds-postgresql"]
    ds = inv["datastores"][0]
    comp = next(c for c in inv["current_components"] if c["scope"] == "ds-postgresql")
    assert (comp["label"], comp["status"]) == ("SIG-DS-POSTGRES", "confirmed")
    assert ("docker-compose.yml", 2) in [(e["path"], e["line"]) for e in ds["evidence"]]
    assert ("requirements.txt", 2) in [(e["path"], e["line"]) for e in ds["evidence"]]


def test_single_dockerfile_links_to_image_only_workload(tmp_path):
    repo = tmp_path / "repo"
    _write(repo, "Dockerfile", 'FROM python:3.12\nCMD ["uvicorn", "main:app"]\n')
    _write(repo, "docker-compose.yml", "services:\n  web:\n    image: registry/x:latest\n")
    [w] = _workloads(repo)
    assert (w.id, w.command, w.code_root, w.dockerfile) == ("w-web", "uvicorn main:app", "", "Dockerfile")


def test_endpoints_by_linked_code_root_are_candidates(tmp_path):
    repo = tmp_path / "repo"
    _write(repo, "app/Dockerfile", 'FROM python:3.12\nCMD ["uvicorn", "main:app"]\n')
    _write(repo, "app/requirements.txt", "fastapi==0.115\n")
    _write(repo, "app/main.py", APP)
    _write(repo, "docker-compose.yml", "services:\n  web:\n    image: registry/x:latest\n"
                                       "  admin:\n    image: registry/x:2\n")
    inv = _inventory(tmp_path)
    assert {(e["workload"], e["status"]) for e in inv["endpoints"]} == {("w-admin", "candidate"),
                                                                       ("w-web", "candidate")}


def test_reverse_proxy_only_compose_falls_back_to_code(tmp_path):
    repo = tmp_path / "repo"
    _write(repo, "requirements.txt", "fastapi==0.115\n")
    _write(repo, "main.py", APP)
    _write(repo, "docker-compose.yml", "services:\n  proxy:\n    image: traefik:v3\n")
    inv = _inventory(tmp_path)
    assert [(w["id"], w["kind"]) for w in inv["workloads"]] == [("w-proxy", "reverse-proxy"), ("w-web", "web")]
    assert {e["workload"] for e in inv["endpoints"]} == {"w-web"}
    path = next(p for p in inv["request_paths"] if p["workload"] == "w-proxy")
    assert [(h["kind"], h["component"]) for h in path["hops"]] == [("reverse-proxy", "unmapped")]


def test_build_dockerfile_from_nginx_is_reverse_proxy(tmp_path):
    repo = tmp_path / "repo"
    _write(repo, "front/Dockerfile", "FROM node:20 AS build\nRUN npm run build\nFROM nginx:1.27\n"
                                     "COPY --from=build /app/dist /usr/share/nginx/html\n")
    _write(repo, "docker-compose.yml", "services:\n  front:\n    build: ./front\n"
                                       "  api:\n    image: acme/api:1\n    command: node server.js\n")
    kinds = {w.id: w.kind for w in _workloads(repo)}
    assert kinds == {"w-api": "web", "w-front": "reverse-proxy"}


def test_devcontainer_and_dev_tools_ignored(tmp_path):
    repo = tmp_path / "repo"
    _write(repo, ".devcontainer/Dockerfile", 'FROM node:20\nCMD ["sleep", "infinity"]\n')
    _write(repo, "docker-compose.yml", "services:\n  mail:\n    image: mailhog/mailhog\n"
                                       "  pga:\n    image: dpage/pgadmin4:8\n")
    inv = _inventory(tmp_path)
    assert inv["workloads"] == []
    assert inv["unmapped"] == []


def test_infra_image_with_component_becomes_candidate_component(tmp_path, monkeypatch):
    entries = kb.images() + ({"match": ["acme-infra"], "role": "infra",
                              "component": "ca:unspecified/redis/default"},)
    monkeypatch.setattr(kb, "images", lambda: entries)
    repo = tmp_path / "repo"
    _write(repo, "docker-compose.yml", "services:\n  x:\n    image: acme-infra:1\n"
                                       "  api:\n    image: acme/api:1\n")
    inv = _inventory(tmp_path)
    comp = [c for c in inv["current_components"] if c["component"] == "ca:unspecified/redis/default"]
    assert [c["status"] for c in comp] == ["candidate"]
    assert [u["label"] for u in inv["unmapped"]] == []


def test_lint_images_catches_bad_entries():
    issues = _lint_images([{"match": ["x"], "role": "bogus"},
                           {"match": ["y"], "role": "datastore", "component": "ds:nope/x/y"},
                           {"match": ["z"], "role": "infra", "hosting_hint": "ds:nope/a/b"},
                           {"role": "cache"}])
    assert any("bogus" in i for i in issues)
    assert any("ds:nope/x/y" in i for i in issues)
    assert any("ds:nope/a/b" in i for i in issues)
    assert any("match" in i for i in issues)
    assert _lint_images(list(kb.images())) == []


def test_compose_evidence_points_at_service_definition(tmp_path):
    repo = tmp_path / "repo"
    _write(repo, "docker-compose.yml",
           "x-env: &env\n  DATABASE_URL: postgres://u@postgres:5432/db\n"
           "services:\n  api:\n    image: acme/api:1\n    depends_on:\n      postgres:\n        condition: x\n"
           "  postgres:\n    image: postgres:16\nvolumes:\n  postgres:\n")
    inv = _inventory(tmp_path)
    ds = next(d for d in inv["datastores"] if d["id"] == "ds-postgresql")
    # 2번 줄은 접속 URL 시그니처(FB9) 근거다. 이미지 근거는 앵커 값이 아니라 서비스 정의 줄이다
    assert [(e["path"], e["line"]) for e in ds["evidence"]] == [("docker-compose.yml", 2), ("docker-compose.yml", 9)]
    assert ds["used_by"] == ["w-api"]


def test_compose_workload_entrypoint_skips_anchor_value(tmp_path):
    repo = tmp_path / "repo"
    _write(repo, "docker-compose.yml",
           "x-env: &env\n  API_URL: http://api:8000\n  NOTE: 'api: old'\n"
           "services:\n  api:\n    image: acme/api:1\n")
    [w] = _workloads(repo)
    assert (w.entrypoint["path"], w.entrypoint["line"]) == ("docker-compose.yml", 5)


def test_single_dockerfile_links_to_workloads_sharing_one_image(tmp_path):
    repo = tmp_path / "repo"
    _write(repo, "Dockerfile", 'FROM python:3.12\nCMD ["uvicorn", "main:app"]\n')
    _write(repo, "docker-compose.yml", "services:\n  web:\n    image: registry/x:latest\n"
                                       "  jobs:\n    image: registry/x:1\n    command: python -m jobs.worker\n")
    ws = {w.id: w for w in _workloads(repo)}
    assert {w.dockerfile for w in ws.values()} == {"Dockerfile"}
    assert (ws["w-web"].command, ws["w-jobs"].command) == ("uvicorn main:app", "python -m jobs.worker")


def test_single_dockerfile_not_linked_to_different_images(tmp_path):
    repo = tmp_path / "repo"
    _write(repo, "Dockerfile", 'FROM python:3.12\nCMD ["uvicorn", "main:app"]\n')
    _write(repo, "docker-compose.yml", "services:\n  web:\n    image: registry/x:latest\n"
                                       "  admin:\n    image: registry/admin:latest\n")
    ws = _workloads(repo)
    assert [(w.dockerfile, w.code_root, w.root_guessed) for w in ws] == [(None, None, False)] * 2


def test_dev_and_test_dockerfiles_do_not_become_workloads(tmp_path):
    repo = tmp_path / "repo"
    cmd = 'FROM node:20\nCMD ["node", "server.js"]\n'
    _write(repo, "docker-compose.yml", "services:\n  postgres:\n    image: postgres:16\n")
    _write(repo, "Dockerfile", cmd)
    _write(repo, "Dockerfile.dev", cmd)
    _write(repo, "ci.Dockerfile", cmd)
    _write(repo, "tests/Dockerfile", cmd)
    assert [(w.name, w.dockerfile) for w in _workloads(repo)] == [("root", "Dockerfile")]


def test_test_dockerfile_does_not_block_single_link(tmp_path):
    repo = tmp_path / "repo"
    _write(repo, "Dockerfile", 'FROM python:3.12\nCMD ["uvicorn", "main:app"]\n')
    _write(repo, "Dockerfile.test", 'FROM python:3.12\nCMD ["pytest"]\n')
    _write(repo, "docker-compose.yml", "services:\n  web:\n    image: reg/b:1\n")
    [w] = _workloads(repo)
    assert (w.id, w.dockerfile, w.command) == ("w-web", "Dockerfile", "uvicorn main:app")


def test_dev_dockerfile_name_parts():
    from infrafit.detect.testpaths import is_dev_dockerfile as _is_dev_dockerfile
    assert all(_is_dev_dockerfile(p) for p in ("Dockerfile.dev", "app/local.Dockerfile", "e2e/Dockerfile",
                                               "x/Dockerfile.debug", "spec/Dockerfile", "a/__tests__/Dockerfile",
                                               "test.dockerfile"))
    assert not any(_is_dev_dockerfile(p) for p in ("Dockerfile", "api/Dockerfile.prod", "docker/worker.Dockerfile",
                                                   "devtools/Dockerfile", "latest/Dockerfile"))


# 예전 부분 문자열 토큰(postgres, redis, mysql, mongo, valkey, memcached, rabbitmq, minio, localstack)이
# 워크로드에서 빼던 흔한 이미지들: 이미지 분류도 모두 워크로드가 아닌 것으로 본다
PG = "ds:unspecified/postgresql/default"
REDIS = "ca:unspecified/redis/default"
TOKEN_COVERED = {
    "postgres:16-alpine": ("datastore", PG), "bitnami/postgresql:16": ("datastore", PG),
    "postgis/postgis:16-3.4": ("datastore", PG), "timescale/timescaledb:latest-pg16": ("datastore", PG),
    "timescale/timescaledb-ha:pg16": ("datastore", PG), "pgvector/pgvector:pg16": ("datastore", PG),
    "ankane/pgvector:latest": ("datastore", PG), "supabase/postgres:15.1.0": ("datastore", PG),
    "cimg/postgres:16.1": ("datastore", PG), "circleci/postgres:12-alpine": ("datastore", PG),
    "mysql:8": ("datastore", "ds:unspecified/mysql/default"),
    "mysql/mysql-server:8.0": ("datastore", "ds:unspecified/mysql/default"),
    "bitnami/mysql:8.0": ("datastore", "ds:unspecified/mysql/default"),
    "mongo:7": ("datastore", "ds:unspecified/mongodb/default"),
    "bitnami/mongodb:7.0": ("datastore", "ds:unspecified/mongodb/default"),
    "mongodb/mongodb-community-server:7.0-ubi8": ("datastore", "ds:unspecified/mongodb/default"),
    "bitnami/mongodb-sharded:7.0": ("datastore", "ds:unspecified/mongodb/default"),
    "redis:7-alpine": ("cache", REDIS), "bitnami/redis:7.2": ("cache", REDIS),
    "redis/redis-stack:latest": ("cache", REDIS), "redis/redis-stack-server:7.2.0-v10": ("cache", REDIS),
    "bitnami/redis-cluster:7.2": ("cache", REDIS), "bitnami/redis-sentinel:7.2": ("cache", REDIS),
    "valkey/valkey:8": ("cache", REDIS), "bitnami/valkey:8.0": ("cache", REDIS),
    "bitnami/valkey-cluster:8.0": ("cache", REDIS),
    "memcached:1.6": ("cache", None), "bitnami/memcached:1.6": ("cache", None),
    "rabbitmq:3-management": ("queue", None), "bitnami/rabbitmq:3.13": ("queue", None),
    "minio/minio:latest": ("infra", None), "quay.io/minio/minio:RELEASE.2024": ("infra", None),
    "bitnami/minio:2024": ("infra", None), "minio/mc:latest": ("infra", None),
    "localstack/localstack:3": ("dev-tool", None), "localstack/localstack-pro:3": ("dev-tool", None),
    "mongo-express:1": ("dev-tool", None), "rediscommander/redis-commander:latest": ("dev-tool", None),
    "redis/redisinsight:latest": ("dev-tool", None), "redislabs/redisinsight:1.14": ("dev-tool", None),
    "phpmyadmin:5": ("dev-tool", None), "phpmyadmin/phpmyadmin:5": ("dev-tool", None),
    "gcr.io/cloudsql-docker/gce-proxy:1.33": ("infra", None),
    "gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.8": ("infra", None),
    "gcr.io/cloudsql-docker/cloudsql-proxy:1.11": ("infra", None),
}


def test_token_covered_images_are_classified():
    got = {image: (c["role"], c["component"]) if (c := classify_image(image)) else None for image in TOKEN_COVERED}
    assert got == TOKEN_COVERED


def test_cloudsql_proxy_variants_hint_hosting():
    for image in ("gcr.io/cloudsql-docker/gce-proxy:1.33", "cloudsql-proxy:1", "gcr.io/x/cloud-sql-proxy:2"):
        assert classify_image(image)["hosting_hint"] == "ds:gcp/cloudsql-postgres/single", image


def test_compose_third_party_images_are_not_workloads(tmp_path):
    repo = tmp_path / "repo"
    _write(repo, "docker-compose.yml",
           "services:\n  api:\n    image: acme/api:1\n  mongo:\n    image: bitnami/mongodb:7.0\n"
           "  redis:\n    image: redis/redis-stack:latest\n  admin:\n    image: mongo-express:1\n")
    assert [(w.id, w.kind) for w in _workloads(repo)] == [("w-api", "web")]


def test_single_web_workload_endpoints_confirmed_despite_guessed_root(tmp_path):
    repo = tmp_path / "repo"
    _write(repo, "k8s/api.yaml", "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: api\nspec:\n"
                                 "  template:\n    spec:\n      containers:\n        - name: api\n"
                                 "          image: acme/api:1\n")
    _write(repo, "svc/Dockerfile", 'FROM node:20\nCMD ["node", "index.js"]\n')
    _write(repo, "svc/package.json", '{"dependencies": {"express": "4"}}\n')
    route = "const express = require('express')\nconst app = express()\napp.get('/{0}', (q, s) => s.send('x'))\n"
    _write(repo, "svc/index.js", route.format("in"))
    _write(repo, "other/package.json", '{"dependencies": {"express": "4"}}\n')
    _write(repo, "other/x.js", route.format("out"))
    inv = _inventory(tmp_path)
    assert sorted((e["route"], e["workload"], e["status"]) for e in inv["endpoints"]) == [
        ("/in", "w-api", "confirmed"), ("/out", "w-api", "confirmed")]


def test_lint_images_shadowed_duplicate_family_and_keys():
    issues = _lint_images([{"match": ["redis*"], "role": "cache"},
                           {"match": ["redis-stack", "acme/redis-x"], "role": "cache"},
                           {"match": ["foo", "foo"], "role": "infra"},
                           {"match": ["pg"], "role": "datastore", "component": "ca:unspecified/redis/default"},
                           {"match": ["q"], "role": "queue", "component": "ds:unspecified/postgresql/default"},
                           {"match": ["px"], "role": "reverse-proxy", "component": "ca:unspecified/redis/default"},
                           {"match": ["c"], "role": "cache", "component": "ds:unspecified/postgresql/default"},
                           {"match": ["k"], "role": "infra", "hostnig_hint": "x"}])
    text = "\n".join(issues)
    assert "redis-stack" in text and "acme/redis-x" in text  # 앞 패턴 redis*에 가려진다
    assert "foo" in text
    for name in ("pg", "q", "px", "c"):
        assert any(f"image {name}:" in i and "family" in i for i in issues), name
    assert "hostnig_hint" in text
    assert len(issues) == 8


def test_development_and_testing_dockerfiles_are_dev():
    from infrafit.detect.testpaths import is_dev_dockerfile as _is_dev_dockerfile
    assert _is_dev_dockerfile("Dockerfile.development")
    assert _is_dev_dockerfile("api/testing.Dockerfile")


def test_manifests_and_build_dirs_under_test_paths_do_not_create_workloads(tmp_path):
    repo = tmp_path / "repo"
    _write(repo, "requirements.txt", "fastapi==0.115\n")
    _write(repo, "main.py", APP)
    _write(repo, "tests/fixtures/app/package.json", '{"dependencies": {"express": "4"}}\n')
    _write(repo, "e2e/Procfile", "worker: node run.js\n")
    _write(repo, "testing/build.gradle", "plugins { id 'org.springframework.boot' }\n"
                                        "dependencies { implementation 'org.springframework.boot:spring-boot-starter-web' }\n")
    assert [(w.id, w.code_root) for w in _workloads(repo)] == [("w-web", "")]


def test_monitoring_images_are_infra():
    for image, label in (("prom/prometheus:v2", "prom/prometheus"), ("prom/node-exporter", "prom/node-exporter"),
                         ("grafana/grafana:11", "grafana/grafana"), ("grafana/loki:3", "grafana/loki"),
                         ("otel/opentelemetry-collector-contrib:0.100", "otel/opentelemetry-collector-contrib"),
                         ("prometheuscommunity/postgres-exporter", "prometheuscommunity/postgres-exporter"),
                         ("oliver006/redis_exporter:v1", "oliver006/redis_exporter"),
                         ("percona/mongodb_exporter:0.40", "percona/mongodb_exporter"),
                         ("quay.io/prometheuscommunity/postgres-exporter:v0.15", "prometheuscommunity/postgres-exporter"),
                         ("bitnami/redis-exporter:1", "bitnami/redis-exporter"),
                         ("quay.io/prometheus/node-exporter:v1", "prometheus/node-exporter")):
        c = classify_image(image)
        assert (c["role"], c["component"], c["label"]) == ("infra", None, label), image


def test_monitoring_compose_services_are_unmapped_not_workloads(tmp_path):
    repo = tmp_path / "repo"
    _write(repo, "docker-compose.yml", "services:\n  api:\n    image: acme/api:1\n"
                                       "  prom:\n    image: prom/prometheus\n"
                                       "  pgx:\n    image: prometheuscommunity/postgres-exporter\n")
    inv = _inventory(tmp_path)
    assert [w["id"] for w in inv["workloads"]] == ["w-api"]
    assert [u["label"] for u in inv["unmapped"]] == ["image:prom/prometheus", "image:prometheuscommunity/postgres-exporter"]


def test_app_server_evidence_falls_back_to_linked_dockerfile_command(tmp_path):
    repo = tmp_path / "repo"
    _write(repo, "requirements.txt", "fastapi==0.115\n")
    _write(repo, "main.py", APP)
    _write(repo, "Dockerfile", 'FROM python:3.12\nCOPY . .\nCMD ["uvicorn", "main:app"]\n')
    _write(repo, "docker-compose.yml", "services:\n  web:\n    image: registry/x:latest\n")
    inv = _inventory(tmp_path)
    hop = next(h for p in inv["request_paths"] for h in p["hops"] if h["kind"] == "app-server")
    assert [(e["path"], e["line"]) for e in hop["evidence"]] == [("Dockerfile", 3)]


def test_dockerfile_workload_context_is_repo_root_when_sources_live_there(tmp_path):
    repo = tmp_path / "repo"
    _write(repo, "package.json", '{"name": "x"}\n')
    _write(repo, "src/workers/cloud.js", "console.log(1)\n")
    _write(repo, "docker/worker.Dockerfile",
           'FROM node:20 AS build\nCOPY package.json ./\nCOPY --chown=node:node src ./src\n'
           'FROM node:20\nCOPY --from=build /app /app\nCMD ["node", "src/workers/cloud.js"]\n')
    _write(repo, "api/Dockerfile", 'FROM python:3.12\nCOPY . .\nCOPY main.py .\nCMD ["python", "main.py"]\n')
    _write(repo, "api/main.py", "print(1)\n")
    ws = {w.id: w for w in _workloads(repo)}
    assert (ws["w-worker"].code_root, ws["w-worker"].build_context) == ("", "")
    assert (ws["w-api"].code_root, ws["w-api"].build_context) == ("api", None)


def test_image_field_lint():
    from infrafit.kb_lint import _lint_images
    assert _lint_images([{"match": ["redis"], "role": "cache", "image": "redis:7-alpine",
                          "url_scheme": ["redis"], "url_template": "redis://{host}:{port}{path}"}]) == []
    issues = " ".join(_lint_images([
        {"match": ["a"], "role": "cache", "image": "redis"},                       # 태그 없음
        {"match": ["b"], "role": "reverse-proxy", "image": "nginx:1"},             # 저장소가 아님
        {"match": ["c"], "role": "cache", "image": "x:1", "url_template": "{user}@{host}"},   # 모르는 자리표시자
    ]))
    assert "태그" in issues and "role" in issues and "url_template" in issues
