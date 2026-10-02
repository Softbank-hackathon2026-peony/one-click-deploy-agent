import json

from infrafit.detect.manifests import parse_manifests
from infrafit.repo import parent_dir
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


def test_node_tolerates_invalid_json_and_non_dict_structures(tmp_path):
    # Test with [] at root
    (tmp_path / "package.json").write_text("[]")
    # Test with a/package.json having non-dict fields
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "package.json").write_text(json.dumps({
        "dependencies": ["x"],  # list instead of dict
        "scripts": [],  # list instead of dict
    }))
    m = parse_manifests(open_snapshot(str(tmp_path), tmp_path / "_w"))
    # Should parse without error and add no deps/scripts from invalid files
    assert len(m.deps) == 0
    assert len(m.scripts) == 0


def test_requirements_skips_urls_vcs_and_paths(tmp_path):
    (tmp_path / "requirements.txt").write_text(
        "git+https://github.com/x/y.git\n"
        "https://host/a.whl\n"
        "./local_pkg\n"
        "mylib @ https://host/mylib.whl\n"
    )
    m = parse_manifests(open_snapshot(str(tmp_path), tmp_path / "_w"))
    # Only mylib should be recorded
    assert "mylib" in m.deps
    assert m.deps["mylib"][0] == "requirements.txt"
    assert len(m.deps) == 1  # Only mylib


def test_pyproject_optional_dependencies(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\ndependencies = ["fastapi"]\n\n[project.optional-dependencies]\n'
        'gcs = ["google-cloud-storage>=2"]\ndev = ["pytest"]\n')
    m = parse_manifests(open_snapshot(str(tmp_path), tmp_path / "_w"))
    assert m.deps["google-cloud-storage"] == ("pyproject.toml", 6)
    assert "pytest" in m.deps_by_dir[""]


def test_dockerfile_package_installs(tmp_path):
    (tmp_path / "api").mkdir()
    (tmp_path / "api" / "Dockerfile").write_text(
        "FROM python:3.12\n"
        "RUN pip install --no-cache-dir -r requirements.txt \\\n"
        "    'psycopg[binary]==3.2' SQLAlchemy>=2.0 && apt-get install -y curl\n"
        "RUN python -m pip install -i https://x/simple uvicorn~=0.30 .\n"
        "RUN npm install -g pm2 && npm i express@4 @acme/sdk@1.2 --save && yarn add pg && pnpm add -D Redis\n"
        "RUN npm install\n")
    m = parse_manifests(open_snapshot(str(tmp_path), tmp_path / "_w"))
    assert m.deps["psycopg"] == ("api/Dockerfile", 2)
    assert m.deps["sqlalchemy"] == ("api/Dockerfile", 2)
    assert m.deps["uvicorn"] == ("api/Dockerfile", 4)
    for name in ("express", "@acme/sdk", "pg", "redis"):
        assert m.deps[name] == ("api/Dockerfile", 5), name
    for name in ("pm2", "requirements.txt", "curl", "https://x/simple", ".", "-y"):
        assert name not in m.deps
    # Dockerfile 설치 목록은 워크로드를 만들지 않는다(모듈 의존성이 아니다)
    assert m.deps_by_dir == {}
