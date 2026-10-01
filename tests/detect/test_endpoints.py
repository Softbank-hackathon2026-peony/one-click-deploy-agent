from infrafit.detect.endpoints import extract_endpoints
from infrafit.detect.workloads import WorkloadInfo
from infrafit.repo import open_snapshot


def _w(wid, app_dir=""):
    return WorkloadInfo(id=wid, kind="web", name=wid[2:], entrypoint={"path": "x", "line": None, "snippet": "x"},
                        status="confirmed", source="code", app_dir=app_dir)


def _write(tmp_path, rel, text):
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def _routes(eps):
    return sorted((e["method"], e["route"]) for e in eps)


def test_python_flask_fastapi_with_prefix(tmp_path):
    _write(tmp_path, "app.py", """from fastapi import APIRouter
router = APIRouter(prefix="/api")

@router.get("/items")
def items(): ...

@app.route("/login", methods=["POST", "GET"])
def login(): ...

@app.websocket("/ws")
async def ws(): ...
""")
    eps = extract_endpoints(open_snapshot(str(tmp_path), tmp_path / "_w"), [_w("w-web")])
    assert _routes(eps) == [("GET", "/api/items"), ("GET", "/login"), ("POST", "/login"), ("WEBSOCKET", "/ws")]
    assert eps[0]["id"] == "ep-web-001"
    assert eps[0]["handler"]["line"] == 4


def test_express_django_next(tmp_path):
    _write(tmp_path, "server.js", "const app = express()\nconst router = express.Router()\n"
                                  "app.get('/health', h)\nrouter.post(\"/orders\", h)\napp.all('/x', h)\n")
    _write(tmp_path, "web/src/client.ts", "export const load = () => api.get('/api/board/posts')\n")
    _write(tmp_path, "proj/urls.py", "urlpatterns = [path('reports/', v), re_path(r'^old/$', v)]\n")
    _write(tmp_path, "app/(shop)/api/cart/route.ts", "export async function GET() {}\nexport const POST = async () => {}\n")
    _write(tmp_path, "pages/api/users/index.ts", "export default function h() {}\n")
    eps = extract_endpoints(open_snapshot(str(tmp_path), tmp_path / "_w"), [_w("w-web")])
    assert _routes(eps) == [
        ("ANY", "/^old/$"), ("ANY", "/api/users"), ("ANY", "/reports/"), ("ANY", "/x"),
        ("GET", "/api/cart"), ("GET", "/health"), ("POST", "/api/cart"), ("POST", "/orders")]


def test_assignment_by_name_tokens(tmp_path):
    _write(tmp_path, "apps/billing/handlers.py", "@router.post('/invoices')\ndef f(): ...\n")
    _write(tmp_path, "apps/catalog/handlers.py", "@router.get('/items')\ndef f(): ...\n")
    ws = [_w("w-billing"), _w("w-billing-sync"), _w("w-catalog-api"), _w("w-gateway")]
    eps = extract_endpoints(open_snapshot(str(tmp_path), tmp_path / "_w"), ws)
    by_route = {e["route"]: e["workload"] for e in eps}
    assert by_route == {"/invoices": "w-billing", "/items": "w-catalog-api"}


def test_malformed_input_is_skipped(tmp_path):
    _write(tmp_path, "bad.py", "def (:\n")
    _write(tmp_path, "ok.py", """router = APIRouter(prefix=PREFIX)
@router.get(PATH)
def a(): ...
@router.get(f"/x{1}")
def b(): ...
@router.get(5)
def c(): ...
@app.route("/r", methods=METHODS)
def d(): ...
@app.route("/s", methods=[1, "post", name])
def e(): ...
@router.get()
def f(): ...
""")
    eps = extract_endpoints(open_snapshot(str(tmp_path), tmp_path / "_w"), [_w("w-web")])
    assert _routes(eps) == [("GET", "/r"), ("POST", "/s")]
    assert extract_endpoints(open_snapshot(str(tmp_path), tmp_path / "_w"), []) == []
