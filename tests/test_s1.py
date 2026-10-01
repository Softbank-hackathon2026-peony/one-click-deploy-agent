import json

from infrafit.consistency import check_run
from infrafit.pipeline import analyze


def test_analyze_until_s1_on_small_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "requirements.txt").write_text("fastapi==0.115\nuvicorn==0.30\nasyncpg==0.29\n")
    (repo / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/health')\ndef h():\n    return 'ok'\n")
    (repo / "Dockerfile").write_text('FROM python:3.12\nCMD ["uvicorn", "main:app"]\n')
    ctx = analyze(str(repo), tmp_path / "out", until="S1", run_id="r1")
    inv = json.loads((ctx.out_dir / "inventory.json").read_text())
    assert [w["id"] for w in inv["workloads"]] == ["w-web"]
    assert [(e["method"], e["route"]) for e in inv["endpoints"]] == [("GET", "/health")]
    assert [d["id"] for d in inv["datastores"]] == ["ds-postgresql"]
    assert inv["request_paths"][0]["hops"][0]["component"] == "nw:app/uvicorn/default"
    assert check_run(ctx.out_dir) == []


def test_analyze_survives_malformed_manifests(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "package.json").write_text('["not", "an", "object"]')
    (repo / "docker-compose.yml").write_text("services: [1, 2]\n")
    (repo / "k8s.yaml").write_text("- 1\n- just a string\n")
    (repo / "Dockerfile").write_text("FROM x\n")
    ctx = analyze(str(repo), tmp_path / "out", until="S1", run_id="r2")
    assert check_run(ctx.out_dir) == []
