import json

from infrafit.detect.artifacts import is_build_path, parse_artifacts
from infrafit.detect.manifests import parse_manifests
from infrafit.detect.workloads import detect_workloads
from infrafit.repo import open_snapshot


def _run(tmp_path):
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    return detect_workloads(snap, parse_manifests(snap), parse_artifacts(snap))


def _write(tmp_path, rel, text):
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def test_code_workloads_merge_procfile_and_prefer_dockerfile_command(tmp_path):
    _write(tmp_path, "requirements.txt", "flask==3.0\n")
    _write(tmp_path, "Procfile", "web: gunicorn app:app\nworker: python worker.py\n")
    _write(tmp_path, "Dockerfile", 'FROM python:3.12\nCMD ["flask", "run"]\n')
    ws = _run(tmp_path)
    assert [(w.id, w.kind) for w in ws] == [("w-web", "web"), ("w-worker", "worker")]
    web = ws[0]
    assert web.command == "flask run"
    assert web.entrypoint["path"] == "requirements.txt"
    assert web.code_root == ""
    assert ws[1].command == "python worker.py"


def test_static_frontend_and_multiple_dirs(tmp_path):
    _write(tmp_path, "frontend/package.json", json.dumps({"devDependencies": {"vite": "^5"}}))
    _write(tmp_path, "api/package.json", json.dumps({"dependencies": {"express": "^4"}, "scripts": {"start": "node server.js"}}))
    _write(tmp_path, "admin/package.json", json.dumps({"dependencies": {"express": "^4"}}))
    ws = _run(tmp_path)
    assert [(w.id, w.kind) for w in ws] == [
        ("w-static", "static-frontend"), ("w-web-admin", "web"), ("w-web-api", "web")]
    assert next(w for w in ws if w.id == "w-web-api").command == "node server.js"


def test_k8s_takes_priority_and_skips_infra_images(tmp_path):
    _write(tmp_path, "package.json", json.dumps({"dependencies": {"express": "^4"}}))
    _write(tmp_path, "k8s/app.yaml", """apiVersion: apps/v1
kind: Deployment
metadata: {name: api}
spec: {template: {spec: {containers: [{name: api, image: acme/api:1}]}}}
---
apiVersion: apps/v1
kind: Deployment
metadata: {name: queue-worker}
spec: {template: {spec: {containers: [{name: w, image: acme/api:1, command: [node, worker.js]}]}}}
---
apiVersion: apps/v1
kind: StatefulSet
metadata: {name: db}
spec: {template: {spec: {containers: [{name: db, image: postgres:16}]}}}
---
apiVersion: batch/v1
kind: Job
metadata: {name: db-migrate}
spec: {template: {spec: {containers: [{name: m, image: acme/api:1}]}}}
""")
    _write(tmp_path, "services/api/Dockerfile", 'FROM node:22\nCMD ["node", "server.js"]\n')
    ws = _run(tmp_path)
    assert [(w.id, w.kind) for w in ws] == [
        ("w-api", "web"), ("w-db-migrate", "migration-job"), ("w-queue-worker", "worker")]
    assert ws[0].command == "node server.js"
    assert ws[2].command == "node worker.js"
    assert ws[0].entrypoint["path"] == "k8s/app.yaml"
    assert ws[0].code_root == "services/api"


def test_compose_code_root_from_build(tmp_path):
    _write(tmp_path, "docker-compose.yml", """services:
  api:
    build: {context: ., dockerfile: services/api/Dockerfile}
  web:
    build: ./web
  db:
    image: postgres:16
""")
    ws = {w.id: w for w in _run(tmp_path)}
    assert set(ws) == {"w-api", "w-web"}
    assert ws["w-api"].code_root == "services/api"
    assert ws["w-web"].code_root == "web"


def test_kustomize_build_only_workload_uses_kustomization_path(tmp_path):
    _write(tmp_path, "k8s/base/kustomization.yaml", "resources: [dep.yaml]\n")
    _write(tmp_path, "k8s/base/dep.yaml", """apiVersion: apps/v1
kind: Deployment
metadata: {name: api}
spec: {template: {spec: {containers: [{name: api, image: acme/api:1}]}}}
""")
    from infrafit.detect.artifacts import ParsedArtifact
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    doc = {"apiVersion": "apps/v1", "kind": "Deployment", "metadata": {"name": "only-built"},
           "spec": {"template": {"spec": {"containers": [{"name": "c", "image": "acme/x:1"}]}}}}
    art = ParsedArtifact("k8s", "k8s/base/kustomization.yaml#build", True, objects=[doc])
    ws = detect_workloads(snap, parse_manifests(snap), [art])
    assert ws[0].entrypoint["path"] == "k8s/base/kustomization.yaml"
    assert ws[0].entrypoint["line"] is None


def test_malformed_objects_do_not_crash(tmp_path):
    from infrafit.detect.artifacts import ParsedArtifact
    _write(tmp_path, "x.yaml", "a: 1\n")
    _write(tmp_path, "docker-compose.yml", "a: 1\n")
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    good = {"kind": "Deployment", "metadata": {"name": "ok"},
            "spec": {"template": {"spec": {"containers": [
                {"name": "c", "image": "a/b", "command": "run", "args": None}]}}}}
    bad = [
        "str", None, {"kind": "Deployment", "metadata": "x"},
        {"kind": "Deployment", "metadata": {"name": ["l"]}},
        {"kind": "Deployment", "metadata": {"name": "a"}, "spec": {"template": {"spec": {"containers": ["x"]}}}},
        {"kind": "Deployment", "metadata": {"name": "b"}, "spec": {"template": {"spec": {"containers": 5}}}},
        {"kind": "Deployment", "metadata": {"name": "c"}, "spec": {"template": {"spec": {"containers": [{"image": 3, "command": 7}]}}}},
        good,
    ]
    ws = detect_workloads(snap, parse_manifests(snap), [ParsedArtifact("k8s", "x.yaml", True, objects=bad)])
    assert "w-ok" in [w.id for w in ws]
    compose = ParsedArtifact("compose", "docker-compose.yml", True,
                             objects=[("a", None), ("b", {"build": 5, "command": {"x": 1}}), "junk", ("c", {"build": {"context": 3, "dockerfile": []}})])
    assert detect_workloads(snap, parse_manifests(snap), [compose])


def test_is_build_path():
    assert is_build_path("k8s/kustomization.yaml#build")
    assert not is_build_path("k8s/a#b.yaml")


def test_k8s_file_with_hash_in_name_keeps_line_evidence(tmp_path):
    (tmp_path / "k8s").mkdir()
    (tmp_path / "k8s" / "a#b.yaml").write_text(
        "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: api\nspec:\n  template:\n    spec:\n"
        "      containers: [{name: api, image: acme/api:1}]\n")
    ws = _run(tmp_path)
    assert ws[0].entrypoint["path"] == "k8s/a#b.yaml"
    assert ws[0].entrypoint["line"] == 4


def test_compose_workload_facts_come_from_base_file_first(tmp_path):
    # F4: compose.prod.yml이 이름순으로 앞서도 사실은 기본 파일에서, 종류는 토큰 규칙으로 정한다
    _write(tmp_path, "compose.yml", "services:\n  api:\n    build: ./api\n    command: uvicorn main:app\n")
    _write(tmp_path, "compose.prod.yml", "services:\n  api:\n"
           "    command: gunicorn -k uvicorn.workers.UvicornWorker main:app\n")
    _write(tmp_path, "api/Dockerfile", "FROM python:3.12\nCMD uvicorn main:app\n")
    [w] = _run(tmp_path)
    assert (w.kind, w.entrypoint["path"], w.code_root, w.dockerfile, w.command) == (
        "web", "compose.yml", "api", "api/Dockerfile", "uvicorn main:app")


def test_worker_kind_is_token_based(tmp_path):
    # F4: `--workers 4`나 gunicorn 워커 클래스는 워커 프로세스가 아니다
    _write(tmp_path, "docker-compose.yml", "services:\n"
           "  a:\n    image: acme/a:1\n    command: uvicorn main:app --workers 4\n"
           "  b:\n    image: acme/b:1\n    command: gunicorn -k uvicorn.workers.UvicornWorker main:app\n"
           "  c:\n    image: acme/c:1\n    command: celery -A app worker\n"
           "  d:\n    image: acme/d:1\n    command: python jobs/worker.py\n"
           "  e:\n    image: acme/e:1\n    command: node dist/worker.js\n"
           "  f:\n    image: acme/f:1\n    command: rq worker --with-scheduler\n"
           "  g:\n    image: acme/g:1\n    command: python -m app.worker\n")
    assert [(w.name, w.kind) for w in _run(tmp_path)] == [
        ("a", "web"), ("b", "web"), ("c", "worker"), ("d", "worker"), ("e", "worker"), ("f", "worker"), ("g", "worker")]


def test_k8s_workers_option_is_not_worker(tmp_path):
    _write(tmp_path, "k8s/api.yaml", "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: api\nspec:\n"
           "  template:\n    spec:\n      containers:\n      - name: api\n        image: acme/api:1\n"
           '        command: ["uvicorn", "main:app", "--workers", "4"]\n')
    assert [(w.name, w.kind) for w in _run(tmp_path)] == [("api", "web")]


def _k8s_deploy(name, command):
    return (f"apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: {name}\nspec:\n"
            f"  template:\n    spec:\n      containers:\n      - name: {name}\n        image: acme/{name}:1\n"
            f"        command: {command}\n")


def test_worker_name_segment_makes_worker(tmp_path):
    # F4a: 이름 조각(-, _, .로 나눈)이 worker·workers면 명령과 상관없이 워커다
    _write(tmp_path, "k8s/email-worker.yaml", _k8s_deploy("email-worker", '["node", "dist/index.js"]'))
    _write(tmp_path, "k8s/api.yaml", _k8s_deploy("api", '["uvicorn", "main:app", "--workers", "4"]'))
    _write(tmp_path, "k8s/jobs.yaml", _k8s_deploy("mail_workers", '["node", "dist/index.js"]'))
    _write(tmp_path, "k8s/networker.yaml", _k8s_deploy("networker", '["node", "dist/index.js"]'))
    assert [(w.name, w.kind) for w in _run(tmp_path)] == [
        ("api", "web"), ("email-worker", "worker"), ("mail_workers", "worker"), ("networker", "web")]
