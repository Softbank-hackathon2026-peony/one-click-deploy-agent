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
    assert [(e["method"], e["route"], e["status"]) for e in inv["endpoints"]] == [
        ("GET", "/health", "confirmed"), ("GET", "/openapi.json", "candidate"), ("GET", "/docs", "candidate"),
        ("GET", "/redoc", "candidate")]
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


def test_dirty_tree_is_not_served_from_cache(tmp_path):
    import subprocess

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "requirements.txt").write_text("fastapi==0.115\n")
    (repo / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n")
    git = ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t"]
    subprocess.run(git + ["init", "-q"], check=True)
    subprocess.run(git + ["add", "."], check=True)
    subprocess.run(git + ["commit", "-qm", "init"], check=True)
    out = tmp_path / "out"
    first = analyze(str(repo), out, until="S1", run_id="a")
    inv_a = json.loads((first.out_dir / "inventory.json").read_text())
    (repo / "store.py").write_text("import sqlite3\nconn = sqlite3.connect('x.db')\n")
    second = analyze(str(repo), out, until="S1", run_id="b")
    inv_b = json.loads((second.out_dir / "inventory.json").read_text())
    assert inv_a["datastores"] == []
    assert [d["id"] for d in inv_b["datastores"]] == ["ds-sqlite"]
    assert inv_a["meta"]["input_hash"] != inv_b["meta"]["input_hash"]


def test_kustomize_identity_is_part_of_cache_key(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "main.py").write_text("print(1)\n")
    monkeypatch.setattr("infrafit.stages.s1_inventory.kustomize_identity", lambda: "none")
    a = analyze(str(repo), tmp_path / "out", until="S1", run_id="a")
    monkeypatch.setattr("infrafit.stages.s1_inventory.kustomize_identity", lambda: "/bin/kustomize v5")
    b = analyze(str(repo), tmp_path / "out", until="S1", run_id="b")
    hash_a = json.loads((a.out_dir / "inventory.json").read_text())["meta"]["input_hash"]
    hash_b = json.loads((b.out_dir / "inventory.json").read_text())["meta"]["input_hash"]
    assert hash_a != hash_b


DEPLOYMENT = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  template:
    spec:
      containers:
        - name: api
          image: acme/api:1
          command: [uvicorn, main:app]
"""


def test_nested_platform_config_does_not_capture_k8s_workload(tmp_path):
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    (repo / "k8s").mkdir()
    (repo / "docs" / "vercel.json").write_text("")
    (repo / "k8s" / "api.yaml").write_text(DEPLOYMENT)
    ctx = analyze(str(repo), tmp_path / "out", until="S1", run_id="r")
    inv = json.loads((ctx.out_dir / "inventory.json").read_text())
    compute = {c["scope"]: c["component"] for c in inv["current_components"]}
    assert compute["w-api"] == "cp:k8s/deployment/unspecified-cluster"
    hops = [(h["kind"], h["component"]) for h in inv["request_paths"][0]["hops"]]
    assert hops == [("app-server", "nw:app/uvicorn/default")]


def test_root_platform_config_adds_compute_and_edge(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "vercel.json").write_text("{}")
    (repo / "package.json").write_text('{"dependencies": {"next": "14"}, "scripts": {"start": "next start"}}')
    ctx = analyze(str(repo), tmp_path / "out", until="S1", run_id="r")
    inv = json.loads((ctx.out_dir / "inventory.json").read_text())
    compute = {c["scope"]: c["component"] for c in inv["current_components"]}
    assert compute["w-web"] == "cp:vercel/functions/unspecified-plan"
    hops = [(h["kind"], h["component"]) for h in inv["request_paths"][0]["hops"]]
    assert hops == [("edge-proxy", "nw:vercel/edge-proxy/default")]
