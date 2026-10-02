import json

from infrafit import kb
from infrafit.consistency import check_run
from infrafit.detect.artifacts import parse_artifacts
from infrafit.detect.manifests import parse_manifests
from infrafit.detect.workloads import classify_image, detect_workloads
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
    assert {(e["workload"], e["status"]) for e in inv["endpoints"]} == {("w-web", "confirmed")}
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
    assert [(e["path"], e["line"]) for e in ds["evidence"]] == [("docker-compose.yml", 9)]
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
