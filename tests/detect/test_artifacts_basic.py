from infrafit.detect.artifacts import flatten, parse_artifacts
from infrafit.repo import open_snapshot


def _write(tmp_path, rel, text):
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def test_dockerfile_settings_and_exec_form(tmp_path):
    _write(tmp_path, "Dockerfile",
           "FROM node:22 AS build\nRUN npm ci \\\n  && npm run build\nFROM node:22-slim\nUSER node\nCMD [\"node\", \"server.js\"]\n")
    art = parse_artifacts(open_snapshot(str(tmp_path), tmp_path / "_w"))[0]
    assert art.kind == "dockerfile" and art.parsed
    assert art.get("base_image") == "node:22-slim"
    assert art.get("stages") == 2
    assert art.get("user") == "node"
    assert art.get("cmd") == "node server.js"
    assert art.objects[1] == ("RUN", "npm ci && npm run build", 2)


def test_compose_services(tmp_path):
    _write(tmp_path, "docker-compose.yml",
           "services:\n  web:\n    image: app:dev\n    command: [\"uvicorn\", \"main:app\"]\n    ports: [\"8000:8000\"]\n  db:\n    image: postgres:16\n")
    art = parse_artifacts(open_snapshot(str(tmp_path), tmp_path / "_w"))[0]
    assert art.kind == "compose"
    assert art.get("services.web.command") == "uvicorn main:app"
    assert art.get("services.web.ports") == ["8000:8000"]
    assert art.get("services.db.image") == "postgres:16"


def test_platform_configs_and_ci(tmp_path):
    _write(tmp_path, "vercel.json", '{"regions": ["icn1"], "functions": {"api/x.ts": {"maxDuration": 60}}}')
    _write(tmp_path, "fly.toml", 'app = "x"\nkill_signal = "SIGINT"\n[http_service]\ninternal_port = 8080\n')
    _write(tmp_path, ".github/workflows/ci.yml",
           "on: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n")
    arts = {a.path: a for a in parse_artifacts(open_snapshot(str(tmp_path), tmp_path / "_w"))}
    assert arts["vercel.json"].get("regions") == ["icn1"]
    assert arts["vercel.json"].get("functions.api/x.ts.maxDuration") == 60
    assert arts["fly.toml"].get("kill_signal") == "SIGINT"
    assert arts["fly.toml"].get("http_service.internal_port") == 8080
    assert arts[".github/workflows/ci.yml"].get("jobs") == ["test"]
    assert arts[".github/workflows/ci.yml"].get("uses") == ["actions/checkout@v4"]


def test_flatten_unquotes_and_skips_metadata():
    data = {"engine": '"postgres"', "__start_line__": 3, "settings": [{"tier": "db-f1", "ip": {"ipv4": True}}]}
    assert flatten(data) == {"engine": "postgres", "settings.tier": "db-f1", "settings.ip.ipv4": True}
