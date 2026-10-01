import json

from infrafit.detect.manifests import parent_dir, parse_manifests
from infrafit.repo import open_snapshot


def test_parses_node_python_and_procfile(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({
        "scripts": {"start": "node index.js"},
        "dependencies": {"express": "^4", "pg": "^8"},
        "devDependencies": {"jest": "^29"},
    }, indent=2))
    (tmp_path / "api").mkdir()
    (tmp_path / "api" / "requirements.txt").write_text("# deps\nFlask==3.0\nuvicorn[standard]>=0.30\n-r base.txt\n")
    (tmp_path / "svc").mkdir()
    (tmp_path / "svc" / "pyproject.toml").write_text('[project]\nname="svc"\ndependencies = ["fastapi>=0.115", "Typing_Extensions"]\n')
    (tmp_path / "Procfile").write_text("web: gunicorn app:app\nworker: celery -A tasks worker\n")
    m = parse_manifests(open_snapshot(str(tmp_path), tmp_path / "_w"))
    assert m.deps["express"][0] == "package.json"
    assert m.deps["jest"][0] == "package.json"
    assert m.deps["flask"] == ("api/requirements.txt", 2)
    assert m.deps["uvicorn"] == ("api/requirements.txt", 3)
    assert "fastapi" in m.deps_by_dir["svc"]
    assert "typing-extensions" in m.deps
    assert m.scripts[":start"][0] == "node index.js"
    assert m.procfile[":worker"] == ("celery -A tasks worker", "Procfile", 2)


def test_locations_keep_every_manifest(tmp_path):
    for d in ("svc-a", "svc-b"):
        (tmp_path / d).mkdir()
        (tmp_path / d / "requirements.txt").write_text("asyncpg==0.29\n")
    m = parse_manifests(open_snapshot(str(tmp_path), tmp_path / "_w"))
    assert m.deps["asyncpg"] == ("svc-a/requirements.txt", 1)
    assert m.locations["asyncpg"] == [("svc-a/requirements.txt", 1), ("svc-b/requirements.txt", 1)]


def test_parent_dir():
    assert parent_dir("package.json") == ""
    assert parent_dir("a/b/package.json") == "a/b"
