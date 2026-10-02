from infrafit.detect.endpoints import extract_endpoints
from infrafit.detect.workloads import WorkloadInfo
from infrafit.repo import open_snapshot


def _w(wid="w-web"):
    return WorkloadInfo(id=wid, kind="web", name=wid[2:], entrypoint={"path": "x", "line": None, "snippet": "x"},
                        status="confirmed", source="code", app_dir="")


def _write(tmp_path, rel, text):
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def _routes(tmp_path):
    eps = extract_endpoints(open_snapshot(str(tmp_path), tmp_path / "_w"), [_w()])
    return sorted((e["method"], e["route"]) for e in eps)


def test_same_file_include_prefix(tmp_path):
    _write(tmp_path, "app.py", """router = APIRouter()
app.include_router(router, prefix="/api")

@router.get("/x")
def x(): ...
""")
    assert _routes(tmp_path) == [("GET", "/api/x")]


def test_relative_module_import_with_router_own_prefix(tmp_path):
    _write(tmp_path, "pkg/main.py", "from . import routes\napp.include_router(routes.router, prefix=\"/api\")\n")
    _write(tmp_path, "pkg/routes.py", "router = APIRouter(prefix=\"/users\")\n\n@router.get(\"/{id}\")\ndef g(): ...\n")
    assert _routes(tmp_path) == [("GET", "/api/users/{id}")]


def test_from_import_name_and_absolute_imports(tmp_path):
    _write(tmp_path, "svc/main.py", "from .routes import router as r\nfrom pkg import items\n"
                                    "import pkg.orders as orders\n"
                                    "app.include_router(r, prefix='/a')\napp.include_router(items.router, prefix='/b')\n"
                                    "app.include_router(orders.router, prefix='/c')\n")
    _write(tmp_path, "svc/routes.py", "router = APIRouter()\n@router.get('/1')\ndef f(): ...\n")
    _write(tmp_path, "pkg/items.py", "router = APIRouter()\n@router.get('/2')\ndef f(): ...\n")
    _write(tmp_path, "pkg/orders/__init__.py", "router = APIRouter()\n@router.get('/3')\ndef f(): ...\n")
    assert _routes(tmp_path) == [("GET", "/a/1"), ("GET", "/b/2"), ("GET", "/c/3")]


def test_two_level_chain(tmp_path):
    _write(tmp_path, "main.py", "from api import api\napp.include_router(api, prefix='/api')\n")
    _write(tmp_path, "api.py", "from . import users\napi = APIRouter()\napi.include_router(users.router, prefix='/users')\n")
    _write(tmp_path, "users.py", "router = APIRouter()\n@router.get('/me')\ndef me(): ...\n")
    assert _routes(tmp_path) == [("GET", "/api/users/me")]


def test_same_router_included_twice(tmp_path):
    _write(tmp_path, "app.py", "router = APIRouter()\napp.include_router(router, prefix='/v1')\n"
                               "app.include_router(router, prefix='/v2')\n@router.get('/x')\ndef x(): ...\n")
    assert _routes(tmp_path) == [("GET", "/v1/x"), ("GET", "/v2/x")]


def test_unresolvable_module_keeps_plain_route(tmp_path):
    _write(tmp_path, "main.py", "from . import missing\napp.include_router(missing.router, prefix='/api')\n"
                                "from . import routes\napp.include_router(routes.router, prefix=prefix_var)\n")
    _write(tmp_path, "routes.py", "router = APIRouter()\n@router.get('/x')\ndef x(): ...\n")
    assert _routes(tmp_path) == [("GET", "/x")]


def test_flask_register_blueprint(tmp_path):
    _write(tmp_path, "app.py", "from .views import bp\napp.register_blueprint(bp, url_prefix='/admin/')\n")
    _write(tmp_path, "views.py", "bp = Blueprint('v', __name__, url_prefix='/u')\n@bp.route('/list', methods=['POST'])\ndef l(): ...\n"
                                 "@bp.route('')\ndef root(): ...\n")
    assert _routes(tmp_path) == [("GET", "/admin/u"), ("POST", "/admin/u/list")]


def test_include_cycle_terminates(tmp_path):
    _write(tmp_path, "app.py", "a = APIRouter()\nb = APIRouter()\na.include_router(b, prefix='/b')\n"
                               "b.include_router(a, prefix='/a')\n@a.get('/x')\ndef x(): ...\n")
    # 순환은 끊기고(a는 b 안에 /a로만 걸린다) 무한 재귀 없이 끝난다
    assert _routes(tmp_path) == [("GET", "/a/x")]


def test_intermediate_router_own_prefix_kept(tmp_path):
    _write(tmp_path, "main.py", "from api import api\napp.include_router(api, prefix='/api')\n")
    _write(tmp_path, "api.py", "from . import users\napi = APIRouter(prefix='/v1')\napi.include_router(users.router, prefix='/users')\n")
    _write(tmp_path, "users.py", "router = APIRouter()\n@router.get('/me')\ndef me(): ...\n")
    assert _routes(tmp_path) == [("GET", "/api/v1/users/me")]


def test_parent_router_imported_from_other_file(tmp_path):
    _write(tmp_path, "main.py", "from .core import api\nfrom . import users\napi.include_router(users.router, prefix='/users')\n"
                                "app.include_router(api, prefix='/api')\n")
    _write(tmp_path, "core.py", "api = APIRouter()\n")
    _write(tmp_path, "users.py", "router = APIRouter()\n@router.get('/me')\ndef me(): ...\n")
    assert _routes(tmp_path) == [("GET", "/api/users/me")]


def test_depth_over_five_is_cut(tmp_path):
    lines = ["r%d = APIRouter()" % i for i in range(8)]
    lines += ["r%d.include_router(r%d, prefix='/p%d')" % (i - 1, i, i) for i in range(1, 8)]
    lines += ["@r7.get('/x')", "def x(): ..."]
    _write(tmp_path, "app.py", "\n".join(lines) + "\n")
    # 사슬이 깊이 5에서 끊겨, 위쪽(p1, p2)은 접두어에 들어가지 않는다
    assert _routes(tmp_path) == [("GET", "/p3/p4/p5/p6/p7/x")]


def test_double_dot_relative_import(tmp_path):
    _write(tmp_path, "pkg/sub/main.py", "from .. import routes\napp.include_router(routes.router, prefix='/api')\n")
    _write(tmp_path, "pkg/routes.py", "router = APIRouter()\n@router.get('/x')\ndef x(): ...\n")
    assert _routes(tmp_path) == [("GET", "/api/x")]
