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


def test_dockerfile_settings_come_from_final_stage(tmp_path):
    _write(tmp_path, "Dockerfile",
           "FROM node:22 AS build\nUSER node\nEXPOSE 9999\nCMD [\"npm\", \"test\"]\n"
           "FROM gcr.io/distroless/nodejs22-debian12\nCOPY --from=build /app /app\nCMD [\"server.js\"]\n")
    art = parse_artifacts(open_snapshot(str(tmp_path), tmp_path / "_w"))[0]
    assert art.get("base_image") == "gcr.io/distroless/nodejs22-debian12"
    assert art.get("user") is None
    assert art.get("user_inherited_from") == "gcr.io/distroless/nodejs22-debian12"
    assert art.get("expose") is None
    assert art.get("cmd") == "server.js"


def test_dockerfile_final_stage_from_earlier_stage_inherits_its_settings(tmp_path):
    _write(tmp_path, "Dockerfile",
           "FROM --platform=linux/amd64 python:3.12 AS base\nUSER app\nEXPOSE 8000\n"
           "FROM base AS final\nCMD uvicorn main:app\n")
    art = parse_artifacts(open_snapshot(str(tmp_path), tmp_path / "_w"))[0]
    assert art.get("base_image") == "base"
    assert art.get("user") == "app"
    assert art.get("user_inherited_from") is None
    assert art.get("expose") == "8000"


def test_dockerfile_without_from_does_not_crash(tmp_path):
    _write(tmp_path, "Dockerfile", "USER x\nFROM\nFROM a AS\n")
    art = parse_artifacts(open_snapshot(str(tmp_path), tmp_path / "_w"))[0]
    assert art.parsed


def test_dockerignore_is_not_a_dockerfile(tmp_path):
    _write(tmp_path, "frontend/Dockerfile.dockerignore", "node_modules\n")
    _write(tmp_path, "frontend/Dockerfile.prod", "FROM nginx\n")
    arts = parse_artifacts(open_snapshot(str(tmp_path), tmp_path / "_w"))
    assert [(a.kind, a.path) for a in arts] == [("dockerfile", "frontend/Dockerfile.prod")]


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


def test_non_dict_roots_do_not_raise(tmp_path):
    _write(tmp_path, "compose.yaml", "- a\n- b\n")
    _write(tmp_path, ".github/workflows/x.yml", "jobs: [1, 2]\n")
    _write(tmp_path, "vercel.json", "[]")
    arts = {a.path: a for a in parse_artifacts(open_snapshot(str(tmp_path), tmp_path / "_w"))}
    assert arts["compose.yaml"].parsed is False
    assert arts["vercel.json"].parsed is False
    assert arts[".github/workflows/x.yml"].get("jobs") == []


def test_dockerfile_from_flags_skipped(tmp_path):
    _write(tmp_path, "Dockerfile",
           "FROM --platform=$BUILDPLATFORM node:22 AS build\nFROM --platform=linux/amd64 python:3.12-slim\n")
    art = parse_artifacts(open_snapshot(str(tmp_path), tmp_path / "_w"))[0]
    assert art.get("base_image") == "python:3.12-slim"
