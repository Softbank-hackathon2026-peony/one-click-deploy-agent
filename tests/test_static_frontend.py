"""정적 프런트엔드 워크로드: 플랫폼 설정의 컴퓨트·엣지 경로, 다른 이미지에 들어가는 빌드 결과."""

import json

from infrafit.consistency import check_run
from infrafit.pipeline import analyze

VITE = json.dumps({"devDependencies": {"vite": "^5"}, "scripts": {"build": "vite build"}})
FLASK_APP = "from flask import Flask\napp = Flask(__name__)\n\n@app.get('/api/x')\ndef x():\n    return 'ok'\n"


def _write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def _inventory(tmp_path):
    ctx = analyze(str(tmp_path / "repo"), tmp_path / "out", until="S1", run_id="r")
    assert check_run(ctx.out_dir) == []
    return json.loads((ctx.out_dir / "inventory.json").read_text())


def _compute(inv, wid):
    return next(c for c in inv["current_components"] if c["scope"] == wid)


def test_vercel_static_site_is_not_functions_and_gets_edge_path(tmp_path):
    repo = tmp_path / "repo"
    _write(repo, "package.json", VITE)
    _write(repo, "vercel.json", '{"rewrites": []}\n')
    inv = _inventory(tmp_path)
    assert [(w["id"], w["kind"]) for w in inv["workloads"]] == [("w-static", "static-frontend")]
    comp = _compute(inv, "w-static")
    assert comp["component"] == "unmapped"
    assert [e["path"] for e in comp["evidence"]] == ["vercel.json"]
    [path] = inv["request_paths"]
    assert [(h["kind"], h["component"]) for h in path["hops"]] == [("edge-proxy", "nw:vercel/edge-proxy/default")]


def test_static_build_copied_into_another_image_is_not_a_workload(tmp_path):
    repo = tmp_path / "repo"
    _write(repo, "requirements.txt", "flask==3.0\n")
    _write(repo, "app.py", FLASK_APP)
    _write(repo, "frontend/package.json", VITE)
    _write(repo, "Dockerfile", 'FROM python:3.12\nCOPY frontend/dist ./static\nCOPY . .\nCMD ["flask", "run"]\n')
    inv = _inventory(tmp_path)
    assert [(w["id"], w["kind"]) for w in inv["workloads"]] == [("w-web", "web")]


def test_static_frontend_never_takes_the_root_dockerfile_compute(tmp_path):
    repo = tmp_path / "repo"
    _write(repo, "requirements.txt", "flask==3.0\n")
    _write(repo, "app.py", FLASK_APP)
    _write(repo, "frontend/package.json", VITE)
    _write(repo, "Dockerfile", 'FROM python:3.12\nCOPY . .\nCMD ["flask", "run"]\n')
    inv = _inventory(tmp_path)
    assert _compute(inv, "w-static")["component"] == "unmapped"
    assert _compute(inv, "w-web")["component"] == "cp:docker/container/unspecified-host"
    assert [p["workload"] for p in inv["request_paths"]] == ["w-web"]


def test_root_dockerfile_of_subdir_app_bundles_static_and_cites_cmd(tmp_path):
    repo = tmp_path / "repo"
    _write(repo, "backend/requirements.txt", "flask==3.0\n")
    _write(repo, "backend/app.py", FLASK_APP)
    _write(repo, "frontend/package.json", VITE)
    _write(repo, "Dockerfile", "FROM python:3.12\nCOPY backend/ backend/\nCOPY frontend/dist/ frontend/dist/\n"
                               'CMD ["flask", "--app", "app", "run"]\n')
    inv = _inventory(tmp_path)
    assert [(w["id"], w["kind"]) for w in inv["workloads"]] == [("w-web", "web")]
    [path] = inv["request_paths"]
    hop = path["hops"][0]
    assert (hop["component"], [(e["path"], e["line"]) for e in hop["evidence"]]) == (
        "nw:app/flask-dev/default", [("Dockerfile", 4)])


def test_worker_http_routes_are_not_given_to_the_web_workload(tmp_path):
    _two_dirs(tmp_path / "repo", '["celery", "-A", "tasks", "worker"]')
    inv = _inventory(tmp_path)
    assert [(w["id"], w["kind"]) for w in inv["workloads"]] == [("w-server", "web"), ("w-worker", "worker")]
    assert [(e["workload"], e["route"]) for e in inv["endpoints"]] == [("w-server", "/api/items")]


def _two_dirs(repo, worker_cmd):
    app = "from fastapi import FastAPI\napp = FastAPI()\n\n@app.post('{0}')\ndef h():\n    return 'ok'\n"
    _write(repo, "server/requirements.txt", "fastapi==0.115\n")
    _write(repo, "server/main.py", app.format("/api/items"))
    _write(repo, "worker/requirements.txt", "fastapi==0.115\n")
    _write(repo, "worker/app.py", app.format("/jobs"))
    _write(repo, "worker/Dockerfile", f"FROM python:3.12\nCMD {worker_cmd}\n")


def test_http_worker_dir_with_web_command_stays_web(tmp_path):
    _two_dirs(tmp_path / "repo", '["uvicorn", "app:app"]')
    inv = _inventory(tmp_path)
    assert [(w["id"], w["kind"]) for w in inv["workloads"]] == [("w-server", "web"), ("w-worker", "web")]
    assert ("w-worker", "/jobs") in [(e["workload"], e["route"]) for e in inv["endpoints"]]
    path = next(p for p in inv["request_paths"] if p["workload"] == "w-worker")
    assert [h["component"] for h in path["hops"]] == ["nw:app/uvicorn/default"]


def test_worker_dir_with_worker_command_is_worker(tmp_path):
    _two_dirs(tmp_path / "repo", '["celery", "-A", "tasks", "worker"]')
    inv = _inventory(tmp_path)
    assert [(w["id"], w["kind"]) for w in inv["workloads"]] == [("w-server", "web"), ("w-worker", "worker")]


def test_routes_kept_when_web_workload_has_no_code_root(tmp_path):
    repo = tmp_path / "repo"
    _write(repo, "requirements.txt", "fastapi==0.115\ncelery==5\n")
    _write(repo, "main.py", "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/items')\ndef h():\n    return 'ok'\n")
    _write(repo, "Dockerfile", 'FROM python:3.12\nCOPY . .\nCMD ["uvicorn", "main:app"]\n')
    _write(repo, "docker-compose.yml", "services:\n  api:\n    image: ghcr.io/acme/api:1\n"
                                       "  worker:\n    build: .\n    command: celery -A tasks worker\n")
    inv = _inventory(tmp_path)
    assert [(w["id"], w["kind"]) for w in inv["workloads"]] == [("w-api", "web"), ("w-worker", "worker")]
    assert [(e["workload"], e["route"], e["status"]) for e in inv["endpoints"]] == [("w-api", "/items", "confirmed")]
