"""S1 deploy_units(다중 컨테이너 계약 §1)."""

import json
from pathlib import Path

from infrafit.consistency import check_run
from infrafit.pipeline import analyze

ROOT = Path(__file__).resolve().parent.parent


def _write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def _units(repo, tmp_path) -> dict:
    ctx = analyze(str(repo), tmp_path / "out", until="S1", run_id="r")
    assert check_run(ctx.out_dir) == []
    return json.loads((ctx.out_dir / "inventory.json").read_text())["deploy_units"]


def _by_id(items):
    return {x["id"]: x for x in items}


def test_compose_shared_build_datastores_and_proxy_entry(tmp_path):
    u = _units(ROOT / "fixtures" / "f1-simple-web-app" / "repo", tmp_path)
    assert u["source"] == {"kind": "compose", "path": "docker-compose.yml"}
    images = _by_id(u["images"])
    assert images["board"]["context"] == "" and images["board"]["dockerfile"] == "services/board/Dockerfile"
    assert set(images) == {"board", "auth", "frontend"}
    cs = _by_id(u["containers"])
    # 같은 build를 쓰는 서비스는 이미지 하나를 공유하고, 서비스 이름은 그대로다
    assert {n for n, c in cs.items() if c.get("image") == "board"} == {"board-api", "board-worker", "migrate"}
    assert set(cs) == {"migrate", "auth", "board-api", "board-worker", "nginx"}
    assert cs["board-worker"]["command"] == "python -m board.worker"
    assert cs["board-worker"]["depends_on"] == ["migrate", "redis"]
    assert cs["board-worker"]["workload"] == "w-board-worker"
    assert cs["board-api"]["ports"] == [8000] and cs["board-worker"]["ports"] == []
    # 마이그레이션은 다른 서비스가 service_completed_successfully로 기다린다
    assert cs["migrate"]["one_shot"] is True and cs["board-api"]["one_shot"] is False
    # 접속 URL에 비밀번호가 든 DATABASE_URL은 이름만
    assert "DATABASE_URL" not in cs["board-worker"]["env"] and "DATABASE_URL" in cs["board-worker"]["env_names"]
    assert cs["board-worker"]["env"]["REDIS_URL"] == "redis://redis:6379/0"
    assert cs["board-worker"]["evidence"]["path"] == "docker-compose.yml"
    stores = _by_id(u["datastores"])
    assert stores["postgres"]["datastore"] == "ds-postgresql" and stores["postgres"]["image"] == "postgres:16-alpine"
    assert stores["postgres"]["ports"] == [5432]
    assert "POSTGRES_PASSWORD" in stores["postgres"]["env_names"]
    assert "POSTGRES_PASSWORD" not in stores["postgres"]["env"]
    assert stores["redis"]["datastore"] == "svc-redis" and stores["redis"]["ports"] == [6379]
    assert u["entry"]["container"] == "nginx" and u["entry"]["port"] == 8080
    assert u["unresolved"] == []


def test_compose_override_profiles_restart_and_registry_images(tmp_path):
    _write(tmp_path, "requirements.txt", "fastapi\n")
    _write(tmp_path, "main.py", "from fastapi import FastAPI\napp = FastAPI()\n")
    _write(tmp_path, "Dockerfile", 'FROM python:3.12\nEXPOSE 8000\nCMD ["uvicorn", "main:app"]\n')
    _write(tmp_path, "docker-compose.yml",
           "services:\n"
           "  web:\n    build: .\n    ports:\n      - '8000:8000'\n      - '127.0.0.1:9229:9229'\n"
           "    depends_on: [cache, seed]\n"
           "  setup:\n    image: acme/setup:1\n    restart: 'no'\n    command: ['sh', '-c', 'echo a && echo b']\n"
           "  seed:\n    build: .\n    profiles: [seed]\n"
           "  cache:\n    image: redis:7\n"
           "  admin:\n    image: adminer\n    ports: ['8081:8080']\n")
    _write(tmp_path, "docker-compose.override.yml", "services:\n  web:\n    environment:\n      MODE: dev\n")
    u = _units(tmp_path, tmp_path)
    cs = _by_id(u["containers"])
    assert set(cs) == {"web", "setup"}  # profiles 서비스·개발 도구는 띄우지 않는다
    assert cs["web"]["env"] == {"MODE": "dev"}  # override 병합
    assert cs["web"]["ports"] == [8000, 9229]
    assert cs["web"]["depends_on"] == ["cache"]
    assert {"field": "containers.web.depends_on", "why": "배포 단위에 없는 서비스 seed(profiles·개발 도구)"} \
        in u["unresolved"]
    assert cs["setup"]["registry_image"] == "acme/setup:1" and "image" not in cs["setup"]
    assert cs["setup"]["one_shot"] is True
    assert cs["setup"]["command"] == "sh -c 'echo a && echo b'"
    assert [i["id"] for i in u["images"]] == ["web"]
    assert u["datastores"][0]["id"] == "cache" and u["datastores"][0]["ports"] == [6379]
    assert u["entry"] == {"container": "web", "port": 8000, "why": "유일하게 호스트 포트를 연 web/proxy 컨테이너"}


def test_compose_several_public_webs_pick_first_and_flag(tmp_path):
    for d in ("vote", "result"):
        _write(tmp_path, f"{d}/Dockerfile", 'FROM python:3.12\nCMD ["python", "app.py"]\n')
    _write(tmp_path, "docker-compose.yml",
           "services:\n  vote:\n    build: ./vote\n    ports: ['8080:80']\n"
           "  result:\n    build: ./result\n    ports: ['8081:80']\n")
    u = _units(tmp_path, tmp_path)
    assert [i["id"] for i in u["images"]] == ["vote", "result"]
    assert u["entry"]["container"] == "vote" and u["entry"]["port"] == 80
    assert [x["field"] for x in u["unresolved"]] == ["entry"]


K8S = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  template:
    metadata:
      labels: {app: api}
    spec:
      containers:
        - name: api
          image: ghcr.io/acme/api:1.2
          args: ["serve", "--port", "8000"]
          ports: [{containerPort: 8000}]
          env:
            - {name: LOG_LEVEL, value: info}
            - name: DB_PASSWORD
              valueFrom: {secretKeyRef: {name: db, key: password}}
---
apiVersion: v1
kind: Service
metadata:
  name: api-svc
spec:
  type: LoadBalancer
  selector: {app: api}
  ports: [{port: 80, targetPort: 8000}]
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  template:
    metadata:
      labels: {app: postgres}
    spec:
      containers:
        - name: postgres
          image: postgres:16
---
apiVersion: batch/v1
kind: Job
metadata:
  name: migrate
spec:
  template:
    spec:
      containers:
        - name: migrate
          image: ghcr.io/acme/api:1.2
          command: ["python", "-m", "migrate"]
"""


def test_k8s_only(tmp_path):
    _write(tmp_path, "api/Dockerfile", 'FROM python:3.12\nCMD ["python", "app.py"]\n')
    _write(tmp_path, "api/requirements.txt", "asyncpg\n")
    _write(tmp_path, "deploy/app.yaml", K8S)
    u = _units(tmp_path, tmp_path)
    assert u["source"] == {"kind": "k8s", "path": "deploy/app.yaml"}
    assert [(i["id"], i["context"], i["dockerfile"]) for i in u["images"]] == [("api", "api", "api/Dockerfile")]
    cs = _by_id(u["containers"])
    # 다른 컨테이너는 Service 이름으로 접속하므로 id는 Service 이름이다
    assert set(cs) == {"api-svc", "migrate"}
    api = cs["api-svc"]
    assert api["image"] == "api" and api["workload"] == "w-api" and api["ports"] == [8000]
    assert api["command"] == "serve --port 8000" and "entrypoint" not in api
    assert api["env"] == {"LOG_LEVEL": "info"} and api["env_names"] == ["DB_PASSWORD", "LOG_LEVEL"]
    assert cs["migrate"]["one_shot"] is True and cs["migrate"]["entrypoint"] == "python -m migrate"
    assert cs["migrate"]["image"] == "api"
    assert [(d["id"], d["image"], d["ports"]) for d in u["datastores"]] == [("postgres", "postgres:16", [5432])]
    assert u["entry"]["container"] == "api-svc" and u["entry"]["port"] == 8000


def test_single_dockerfile_app(tmp_path):
    _write(tmp_path, "requirements.txt", "fastapi\nuvicorn\n")
    _write(tmp_path, "main.py", "from fastapi import FastAPI\napp = FastAPI()\n")
    _write(tmp_path, "Dockerfile", 'FROM python:3.12\nEXPOSE 8000\nCMD ["uvicorn", "main:app", "--host", "0.0.0.0"]\n')
    u = _units(tmp_path, tmp_path)
    assert u["source"]["kind"] == "code"
    assert u["images"] == [{"id": "web", "context": "", "dockerfile": "Dockerfile",
                            "evidence": {"path": "Dockerfile", "line": 1, "snippet": "FROM python:3.12"}}]
    assert len(u["containers"]) == 1
    c = u["containers"][0]
    assert (c["id"], c["workload"], c["image"], c["ports"], c["one_shot"]) == ("web", "w-web", "web", [8000], False)
    assert "command" not in c  # 이미지 CMD를 그대로 쓴다
    assert u["datastores"] == []
    assert u["entry"] == {"container": "web", "port": 8000, "why": "유일하게 포트를 아는 web 컨테이너"}


def test_code_app_without_dockerfile_flags_missing_dockerfile(tmp_path):
    _write(tmp_path, "package.json", '{"dependencies": {"express": "4"}, "scripts": {"start": "node server.js"}}')
    _write(tmp_path, "server.js", "const express = require('express')\n")
    u = _units(tmp_path, tmp_path)
    assert [(i["id"], i["context"], "dockerfile" in i) for i in u["images"]] == [("web", "", False)]
    assert u["containers"][0]["command"] == "node server.js"
    assert u["entry"] is None
    assert {x["field"] for x in u["unresolved"]} == {"images.web.dockerfile", "containers.web.ports"}


def test_secret_env_values_go_only_to_names(tmp_path):
    _write(tmp_path, "Dockerfile", 'FROM python:3.12\nCMD ["python", "-m", "app.worker"]\n')
    _write(tmp_path, "docker-compose.yml",
           "services:\n  worker:\n    build: .\n    environment:\n"
           "      OPENAI_API_KEY: sk-abcdefghijklmnopqrstuvwxyz\n"
           "      SESSION_SECRET: s3cret\n"
           "      AUTH_TOKEN: t\n"
           "      ADMIN: sk-abcdefghijklmnopqrstuvwxyz\n"
           "      BROKER_URL: amqp://guest:guest@rabbit:5672/\n"
           "      CACHE_URL: redis://cache:6379/0\n"
           "      FROM_HOST:\n"
           "      REGION: ${AWS_REGION:-us-east-1}\n"
           "      DEBUG: false\n")
    u = _units(tmp_path, tmp_path)
    c = u["containers"][0]
    assert c["env"] == {"CACHE_URL": "redis://cache:6379/0", "DEBUG": "false"}
    assert c["env_names"] == ["ADMIN", "AUTH_TOKEN", "BROKER_URL", "CACHE_URL", "DEBUG", "FROM_HOST",
                              "OPENAI_API_KEY", "REGION", "SESSION_SECRET"]


def _celery_repo(root):
    _write(root, "requirements.txt", "flask==3.0.3\ncelery==5.4.0\nredis==5.0.4\ngunicorn==22.0.0\n")
    _write(root, "Procfile", "web: gunicorn -b 0.0.0.0:$PORT app:app\nworker: celery -A tasks worker --loglevel=info\n"
                             "beat: celery -A tasks beat --loglevel=info\n")
    _write(root, "app.py", "from flask import Flask\nfrom tasks import send_report\napp = Flask(__name__)\n\n"
                           "@app.get('/health')\ndef health():\n    return 'ok'\n")
    _write(root, "tasks.py", "import os\nfrom celery import Celery\n\n"
                             "REDIS_URL = os.environ.get(\"REDIS_URL\", \"redis://localhost:6379/0\")\n"
                             "celery = Celery(\"tasks\", broker=REDIS_URL, backend=REDIS_URL)\n\n"
                             "@celery.task\ndef send_report(kind):\n    return kind\n")


def test_procfile_beat_is_scheduled_workload_and_container(tmp_path):
    _celery_repo(tmp_path)
    ctx = analyze(str(tmp_path), tmp_path / "out", until="S1", run_id="r")
    inv = json.loads((ctx.out_dir / "inventory.json").read_text())
    kinds = {w["name"]: w["kind"] for w in inv["workloads"]}
    assert kinds["scheduled"] == "scheduled"
    sched = next(w for w in inv["workloads"] if w["kind"] == "scheduled")
    assert sched["entrypoint"]["path"] == "Procfile" and sched["entrypoint"]["line"] == 3
    cs = {c["workload"]: c for c in inv["deploy_units"]["containers"]}
    assert cs[sched["id"]]["command"] == "celery -A tasks beat --loglevel=info"
    assert cs[sched["id"]]["one_shot"] is False


def test_unknown_procfile_type_with_celery_beat_command_is_scheduled(tmp_path):
    _celery_repo(tmp_path)
    _write(tmp_path, "Procfile", "web: gunicorn -b 0.0.0.0:$PORT app:app\nclockwork: celery -A tasks beat\n")
    ctx = analyze(str(tmp_path), tmp_path / "out", until="S1", run_id="r")
    inv = json.loads((ctx.out_dir / "inventory.json").read_text())
    assert any(w["kind"] == "scheduled" for w in inv["workloads"])


def test_code_path_redis_becomes_store_container_with_env(tmp_path):
    _celery_repo(tmp_path)
    u = _units(tmp_path, tmp_path)
    assert u["source"]["kind"] == "code"
    stores = {d["id"]: d for d in u["datastores"]}
    assert stores["redis"]["datastore"] == "svc-redis"
    assert stores["redis"]["image"] == "redis:7-alpine" and stores["redis"]["ports"] == [6379]
    assert stores["redis"]["env"] == {} and stores["redis"]["evidence"]["path"] == "requirements.txt"
    for c in u["containers"]:
        assert "redis" in c["depends_on"]
        assert c["env"]["REDIS_URL"] == "redis://redis:6379/0" and "REDIS_URL" in c["env_names"]


def test_code_path_postgres_needs_credentials_so_no_container(tmp_path):
    _write(tmp_path, "requirements.txt", "flask==3.0.3\npsycopg2-binary==2.9.9\n")
    _write(tmp_path, "app.py", "import os, psycopg2\nfrom flask import Flask\napp = Flask(__name__)\n"
                               "conn = psycopg2.connect(os.environ.get('DATABASE_URL', 'postgres://localhost/app'))\n\n"
                               "@app.get('/h')\ndef h():\n    return 'ok'\n")
    u = _units(tmp_path, tmp_path)
    assert u["datastores"] == []
    assert any(x["field"].startswith("datastores.") and "비밀번호" in x["why"] for x in u["unresolved"])


def test_code_path_without_env_default_adds_container_but_no_env(tmp_path):
    _celery_repo(tmp_path)
    _write(tmp_path, "tasks.py", "from celery import Celery\ncelery = Celery('tasks', broker='redis://localhost:6379/0')\n")
    u = _units(tmp_path, tmp_path)
    assert [d["id"] for d in u["datastores"]] == ["redis"]
    assert all("REDIS_URL" not in c["env"] for c in u["containers"])


def test_celery_beat_regex_is_tight_for_unknown_procfile_types(tmp_path):
    _celery_repo(tmp_path)
    _write(tmp_path, "Procfile", "web: gunicorn -b 0.0.0.0:$PORT app:app\nqueue: celery -A tasks worker -Q beat\n")
    ctx = analyze(str(tmp_path), tmp_path / "out", until="S1", run_id="r")
    inv = json.loads((ctx.out_dir / "inventory.json").read_text())
    assert not any(w["kind"] == "scheduled" for w in inv["workloads"])
    _write(tmp_path, "Procfile", "web: gunicorn -b 0.0.0.0:$PORT app:app\nclockwork: celery --app=tasks beat -l info\n")
    ctx = analyze(str(tmp_path), tmp_path / "out2", until="S1", run_id="r")
    inv = json.loads((ctx.out_dir / "inventory.json").read_text())
    assert any(w["kind"] == "scheduled" for w in inv["workloads"])


def test_code_path_js_redis_env_default(tmp_path):
    _write(tmp_path, "package.json", '{"dependencies": {"express": "4", "ioredis": "5"}}\n')
    _write(tmp_path, "server.js", "const express = require('express');\nconst Redis = require('ioredis');\n"
                                  "const url = process.env.REDIS_URL || \"redis://localhost:6379\";\n"
                                  "const redis = new Redis(url);\nconst app = express();\n"
                                  "app.get('/h', (req, res) => res.send('ok'));\napp.listen(process.env.PORT || 3000);\n")
    u = _units(tmp_path, tmp_path)
    assert [d["id"] for d in u["datastores"]] == ["redis"]
    assert u["containers"]
    for c in u["containers"]:
        assert c["env"]["REDIS_URL"] == "redis://redis:6379/0"


def test_code_path_env_default_only_in_test_path_is_ignored(tmp_path):
    _write(tmp_path, "requirements.txt", "flask==3.0.3\nredis==5.0.4\n")
    _write(tmp_path, "app.py", "import redis\nfrom flask import Flask\napp = Flask(__name__)\nr = redis.Redis()\n\n"
                               "@app.get('/h')\ndef h():\n    return 'ok'\n")
    _write(tmp_path, "tests/test_x.py", "import os\nURL = os.environ.get(\"REDIS_URL\", \"redis://localhost\")\n")
    u = _units(tmp_path, tmp_path)
    assert [d["id"] for d in u["datastores"]] == ["redis"]
    assert all("REDIS_URL" not in c["env"] for c in u["containers"])
