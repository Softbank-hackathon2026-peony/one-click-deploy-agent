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
