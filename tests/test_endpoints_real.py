import pytest

from infrafit.detect.artifacts import parse_artifacts
from infrafit.detect.endpoints import extract_endpoints
from infrafit.detect.manifests import parse_manifests
from infrafit.detect.signatures import match_signatures
from infrafit.detect.testpaths import is_test_path
from infrafit.detect.workloads import WorkloadInfo, detect_workloads
from infrafit.repo import open_snapshot

FASTAPI = "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/health')\ndef h():\n    return 'ok'\n"


def _write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def _w(wid="w-web", code_root=None):
    return WorkloadInfo(id=wid, kind="web", name=wid[2:], entrypoint={"path": "x", "line": None, "snippet": "x"},
                        status="confirmed", source="code", code_root=code_root)


def _snap(root):
    return open_snapshot(str(root), root / "_w")


def _eps(root, workloads=None):
    snap = _snap(root)
    ws = workloads if workloads is not None else detect_workloads(snap, parse_manifests(snap), parse_artifacts(snap))
    return extract_endpoints(snap, ws, manifests=parse_manifests(snap))


def _routes(eps):
    return sorted((e["method"], e["route"]) for e in eps)


@pytest.mark.parametrize("rel", [
    "tests/x.py", "app/test/x.py", "web/__tests__/a.js", "e2e/a.ts", "spec/a.js", "pkg/testing/a.py",
    "test_x.py", "app/x_test.py", "conftest.py", "src/a.test.ts", "src/a.spec.js",
    "src/main/java/FooTest.java", "src/FooTest.kt", "FooTests.java", "FooTests.kt", "src/test/java/Foo.java"])
def test_test_paths(rel):
    assert is_test_path(rel)


@pytest.mark.parametrize("rel", ["app/main.py", "contest.py", "src/Contest.java", "latest/a.py", "testdata.py",
                                 "src/testimonials.ts", "api/routes.js"])
def test_non_test_paths(rel):
    assert not is_test_path(rel)


def test_test_files_have_no_endpoints(tmp_path):
    _write(tmp_path, "main.py", FASTAPI)
    _write(tmp_path, "tests/test_x.py", "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/phantom')\ndef p(): ...\n")
    _write(tmp_path, "test_y.py", "@app.post('/phantom2')\ndef p(): ...\n")
    _write(tmp_path, "src/a.spec.js", "const app = express()\napp.get('/phantom3', h)\n")
    assert _routes(_eps(tmp_path, [_w()])) == [("GET", "/health")]


def test_signature_code_condition_ignores_test_files(tmp_path):
    sigs = [{"id": "SIG-T", "component": "ds:local/sqlite/default", "role": "primary-db", "status": "confirmed",
             "when": {"code": {"glob": "**/*.py", "regex": r"sqlite3\.connect\("}}}]
    _write(tmp_path, "tests/test_db.py", "import sqlite3\nsqlite3.connect('x')\n")
    snap = _snap(tmp_path)
    assert match_signatures(snap, parse_manifests(snap), sigs) == []
    _write(tmp_path, "db.py", "import sqlite3\nsqlite3.connect('x')\n")
    snap = _snap(tmp_path)
    [m] = match_signatures(snap, parse_manifests(snap), sigs)
    assert [e["path"] for e in m.evidence] == ["db.py"]


def test_root_app_owns_its_endpoints(tmp_path):
    _write(tmp_path, "docker-compose.yml", "services:\n  api:\n    build: .\n  admin:\n    build: ./admin\n")
    _write(tmp_path, "Dockerfile", "FROM python:3.12\nCMD [\"uvicorn\", \"main:app\"]\n")
    _write(tmp_path, "admin/Dockerfile", "FROM python:3.12\nCMD [\"uvicorn\", \"main:app\"]\n")
    _write(tmp_path, "main.py", FASTAPI)
    _write(tmp_path, "admin/main.py", "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/admin')\ndef a(): ...\n")
    eps = {e["route"]: (e["workload"], e["status"]) for e in _eps(tmp_path)}
    assert eps == {"/health": ("w-api", "confirmed"), "/admin": ("w-admin", "confirmed")}


def test_fastify_plugin_and_route_object(tmp_path):
    _write(tmp_path, "api/package.json", '{"dependencies": {"fastify": "^4"}}\n')
    _write(tmp_path, "api/src/routes.ts", """export async function routes(fastify: FastifyInstance, opts) {
  fastify.get('/a', async () => 'a')
  fastify.route({
    method: ['GET', 'HEAD'],
    url: '/b',
    handler: async (req, reply) => { reply.send({ url: '/not-a-route' }) },
  })
}
""")
    _write(tmp_path, "api/src/more.js", "module.exports = async (instance) => {\n  instance.post('/c', h)\n}\n"
                                        "export default async function (app) { app.route({ method: 'DELETE', url: '/d' }) }\n")
    eps = _eps(tmp_path, [_w()])
    assert _routes(eps) == [("DELETE", "/d"), ("GET", "/a"), ("GET", "/b"), ("HEAD", "/b"), ("POST", "/c")]
    assert {e["framework"] for e in eps} == {"fastify"}
    b = next(e for e in eps if e["route"] == "/b")
    assert b["handler"]["line"] == 3


def test_parameter_servers_need_server_dependency(tmp_path):
    _write(tmp_path, "web/package.json", '{"dependencies": {"axios": "^1"}}\n')
    _write(tmp_path, "web/client.js", "function f(app) { app.get('/x', h) }\n")
    _write(tmp_path, "srv/package.json", '{"dependencies": {"express": "^4", "koa": "^2"}}\n')
    _write(tmp_path, "srv/r.js", "function f(router) { router.get('/y', h) }\n")
    _write(tmp_path, "plain.js", "const app = express()\napp.get('/z', h)\n")
    eps = _eps(tmp_path, [_w()])
    assert sorted((e["route"], e["framework"]) for e in eps) == [("/y", "koa"), ("/z", "express")]


def test_flask_add_url_rule_with_blueprint_prefixes(tmp_path):
    _write(tmp_path, "views.py", """from flask import Blueprint
bp = Blueprint("v", __name__, url_prefix="/v1")

def f(): ...

bp.add_url_rule("/x", view_func=f, methods=["POST"])
bp.add_url_rule("/y", "y", f)
""")
    _write(tmp_path, "app.py", "from flask import Flask\nfrom views import bp\napp = Flask(__name__)\n"
                               "app.register_blueprint(bp, url_prefix=\"/api\")\napp.add_url_rule('/', view_func=f)\n")
    eps = _eps(tmp_path, [_w()])
    assert _routes(eps) == [("GET", "/"), ("GET", "/api/v1/y"), ("POST", "/api/v1/x")]
    x = next(e for e in eps if e["route"] == "/api/v1/x")
    assert (x["handler"]["path"], x["handler"]["line"]) == ("views.py", 6)
