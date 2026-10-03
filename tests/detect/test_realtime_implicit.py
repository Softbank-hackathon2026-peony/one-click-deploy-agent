import json

from infrafit import kb
from infrafit.detect.endpoints import extract_endpoints
from infrafit.detect.manifests import parse_manifests
from infrafit.detect.signatures import unmapped_signature_labels
from infrafit.detect.workloads import WorkloadInfo
from infrafit.kb_lint import _lint_implicit_routes
from infrafit.repo import open_snapshot


def _w(wid, code_root=""):
    return WorkloadInfo(id=wid, kind="web", name=wid[2:], entrypoint={"path": "x", "line": None, "snippet": "x"},
                        status="confirmed", source="code", app_dir=code_root, code_root=code_root)


def _write(tmp_path, rel, text):
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def _eps(tmp_path, workloads=None):
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    return extract_endpoints(snap, workloads or [_w("w-web")], manifests=parse_manifests(snap))


def _rows(eps):
    return [(e["method"], e["route"], e["framework"], e["status"], e["handler"]["path"], e["handler"]["line"])
            for e in eps]


GRADLE = 'plugins { id("org.springframework.boot") version "3.2.0" }\ndependencies {\n{deps}}\n'


def _gradle(tmp_path, *deps):
    lines = "".join(f'    implementation("{d}")\n' for d in deps)
    _write(tmp_path, "build.gradle.kts", GRADLE.replace("{deps}", lines))


def test_spring_stomp_and_server_endpoint(tmp_path):
    _gradle(tmp_path, "org.springframework.boot:spring-boot-starter-web",
            "org.springframework.boot:spring-boot-starter-websocket")
    _write(tmp_path, "src/main/kotlin/WsConfig.kt", """@Configuration
@EnableWebSocketMessageBroker
class WsConfig : WebSocketMessageBrokerConfigurer {
    override fun registerStompEndpoints(registry: StompEndpointRegistry) {
        // registry.addEndpoint("/old")
        registry.addEndpoint("/ws/chat", "/ws/alt")
            .setAllowedOriginPatterns("*")
    }
    override fun configureMessageBroker(registry: MessageBrokerRegistry) {
        registry.enableSimpleBroker("/topic")
    }
}
""")
    _write(tmp_path, "src/main/java/Echo.java", '@ServerEndpoint(value = "/echo")\npublic class Echo {}\n')
    assert _rows(_eps(tmp_path)) == [
        ("WEBSOCKET", "/echo", "spring-mvc", "confirmed", "src/main/java/Echo.java", 1),
        ("WEBSOCKET", "/ws/alt", "spring-mvc", "confirmed", "src/main/kotlin/WsConfig.kt", 6),
        ("WEBSOCKET", "/ws/chat", "spring-mvc", "confirmed", "src/main/kotlin/WsConfig.kt", 6)]
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    (entry,) = unmapped_signature_labels(snap, parse_manifests(snap), kb.unmapped_signatures())
    assert entry["label"] == "spring-stomp-simple-broker"
    assert [(e["path"], e["line"]) for e in entry["evidence"]] == [
        ("build.gradle.kts", 4), ("src/main/kotlin/WsConfig.kt", 2), ("src/main/kotlin/WsConfig.kt", 10)]


def test_stomp_unmapped_needs_websocket_starter(tmp_path):
    _gradle(tmp_path, "org.springframework.boot:spring-boot-starter-web")
    _write(tmp_path, "src/main/java/A.java", "@EnableWebSocketMessageBroker\nclass A {}\n")
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    assert unmapped_signature_labels(snap, parse_manifests(snap), kb.unmapped_signatures()) == []


def test_socketio_server_path_and_default(tmp_path):
    _write(tmp_path, "package.json", json.dumps({"dependencies": {"socket.io": "^4", "express": "^4"}}))
    _write(tmp_path, "server.js", """import { Server } from "socket.io";
const io = new Server(httpServer, {
  cors: { origin: "*" },
  path: "/rt",
});
""")
    _write(tmp_path, "legacy.js", "const socketIO = require('socket.io');\nconst io = socketIO(server);\n")
    _write(tmp_path, "client.js", "import { io } from 'socket.io-client';\nconst s = io('/x', { path: '/nope' });\n")
    assert [r[:3] + r[4:] for r in _rows(_eps(tmp_path))] == [
        ("WEBSOCKET", "/socket.io", "socket.io", "legacy.js", 2), ("WEBSOCKET", "/rt", "socket.io", "server.js", 2)]


def test_fastapi_docs_respect_constructor_and_skip_disabled(tmp_path):
    _write(tmp_path, "requirements.txt", "fastapi\nprometheus-fastapi-instrumentator\n")
    _write(tmp_path, "main.py", """from fastapi import FastAPI
app = FastAPI(
    title="x",
    docs_url="/api/docs",
    redoc_url=None,
)
Instrumentator().instrument(app).expose(app, include_in_schema=False)

@app.get("/openapi.json")
def mine(): ...
""")
    _write(tmp_path, "admin.py", "from fastapi import FastAPI\nsub = FastAPI(openapi_url=None)\n")
    assert _rows(_eps(tmp_path)) == [
        ("GET", "/openapi.json", "fastapi", "confirmed", "main.py", 9),
        ("GET", "/api/docs", "fastapi", "candidate", "main.py", 2),
        ("GET", "/metrics", "fastapi", "candidate", "main.py", 7)]


def test_fastapi_docs_need_dependency(tmp_path):
    _write(tmp_path, "main.py", "from fastapi import FastAPI\napp = FastAPI()\n")
    assert _eps(tmp_path) == []


def test_spring_actuator_and_springdoc_paths_from_config(tmp_path):
    _gradle(tmp_path, "org.springframework.boot:spring-boot-starter-webflux",
            "org.springframework.boot:spring-boot-starter-actuator",
            "org.springdoc:springdoc-openapi-starter-webflux-ui:2.3.0")
    _write(tmp_path, "src/main/resources/application.yml", """management:
  endpoints:
    web:
      base-path: /manage
springdoc:
  api-docs:
    path: /api-docs
""")
    assert _rows(_eps(tmp_path)) == [
        ("GET", "/manage/health", "spring-webflux", "candidate", "src/main/resources/application.yml", 4),
        ("GET", "/swagger-ui.html", "spring-webflux", "candidate", "build.gradle.kts", 5),
        ("GET", "/api-docs", "spring-webflux", "candidate", "src/main/resources/application.yml", 7)]


def test_springdoc_api_only_and_actuator_default(tmp_path):
    _gradle(tmp_path, "org.springframework.boot:spring-boot-starter-web",
            "org.springframework.boot:spring-boot-starter-actuator",
            "org.springdoc:springdoc-openapi-starter-webmvc-api:2.3.0")
    assert [(e["route"], e["handler"]["line"]) for e in _eps(tmp_path)] == [
        ("/actuator/health", 4), ("/v3/api-docs", 5)]


def test_fastify_swagger_route_prefix_and_assignment(tmp_path):
    _write(tmp_path, "api/package.json", json.dumps(
        {"dependencies": {"fastify": "^4", "@fastify/swagger": "^8", "@fastify/swagger-ui": "^4"}}, indent=2))
    _write(tmp_path, "api/src/config/swagger.js", "export const uiOptions = {\n  routePrefix: '/docs',\n};\n")
    _write(tmp_path, "web/package.json", json.dumps({"dependencies": {"express": "^4"}}))
    eps = _eps(tmp_path, [_w("w-api", "api"), _w("w-web", "web")])
    assert [(e["workload"], e["route"], e["framework"], e["status"], e["handler"]["path"]) for e in eps] == [
        ("w-api", "/docs", "fastify", "candidate", "api/src/config/swagger.js")]


def test_implicit_route_lint_catches_bad_entries():
    bad = [{"id": "X", "framework": "f", "trigger": {"call": {"globs": ["*.py"], "regex": "(", "dependency": "d"}},
            "routes": [{"method": "GET", "path": "{}", "default": "docs", "override": {"keyword": "a", "code": {}}}]}]
    issues = _lint_implicit_routes(bad)
    assert any("정규식 오류" in i for i in issues)
    assert any("default" in i for i in issues)
    assert any("override" in i for i in issues)
    assert _lint_implicit_routes() == []


def test_socketio_ignores_other_namespaces_server_classes(tmp_path):
    _write(tmp_path, "package.json", json.dumps({"dependencies": {"socket.io": "^4"}}))
    _write(tmp_path, "server.js", "import http from 'http';\nimport { Server } from 'socket.io';\n"
           "const server = new http.Server(app);\nconst io = new Server(server);\n")
    assert [r[:3] + r[4:] for r in _rows(_eps(tmp_path))] == [("WEBSOCKET", "/socket.io", "socket.io", "server.js", 4)]


def test_python_socketio_servers(tmp_path):
    """Flask-SocketIO `SocketIO(app)`(옵션 `path`)와 python-socketio `socketio.Server(`·`AsyncServer(`. 클라이언트는 아니다."""
    _write(tmp_path, "requirements.txt", "Flask==3.0.3\nFlask-SocketIO==5.3.6\npython-socketio==5.11.0\n")
    _write(tmp_path, "app.py", "from flask import Flask\nfrom flask_socketio import SocketIO\n"
                               "app = Flask(__name__)\nsocketio = SocketIO(app)\n")
    _write(tmp_path, "rt/server.py", "import socketio\nsio = socketio.AsyncServer(async_mode='asgi')\n"
                                     "other = socketio.Server()\n")
    _write(tmp_path, "admin.py", "from flask_socketio import SocketIO as S\nws = S(path='/admin-ws')\n")
    _write(tmp_path, "client.py", "import socketio\nc = socketio.Client()\nc.connect('http://x', socketio_path='/nope')\n")
    assert _rows(_eps(tmp_path)) == [
        ("WEBSOCKET", "/admin-ws", "socket.io", "confirmed", "admin.py", 2),
        ("WEBSOCKET", "/socket.io", "socket.io", "confirmed", "app.py", 4),
        ("WEBSOCKET", "/socket.io", "socket.io", "confirmed", "rt/server.py", 2),
        ("WEBSOCKET", "/socket.io", "socket.io", "confirmed", "rt/server.py", 3)]
