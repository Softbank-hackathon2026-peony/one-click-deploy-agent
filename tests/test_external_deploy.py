"""계획 1e 작업 1: 외부 서비스와 환경별 배포 대상(합성 저장소)."""

import json

from infrafit import kb_lint
from infrafit.consistency import check_run, check_s1
from infrafit.pipeline import analyze

FASTAPI = "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/health')\ndef h():\n    return 'ok'\n"


def _write(repo, files: dict[str, str]):
    for rel, text in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)


def _inventory(tmp_path, files, run_id="r"):
    repo = tmp_path / "repo"
    _write(repo, files)
    ctx = analyze(str(repo), tmp_path / "out", until="S1", run_id=run_id)
    assert check_run(ctx.out_dir) == []
    return json.loads((ctx.out_dir / "inventory.json").read_text())


def _app(d=""):
    p = f"{d}/" if d else ""
    return {f"{p}requirements.txt": "fastapi==0.115\nuvicorn==0.30\n", f"{p}main.py": FASTAPI}


def _ext(inv):
    return {s["id"]: s for s in inv["external_services"]}


def _deploy_envs(inv):
    return {e["name"]: e for e in inv["environments"] if e["kind"] in ("platform", "ci-deploy")}


def _env_computes(inv):
    return sorted((c["scope"], c["environment"], c["component"], c["status"])
                  for c in inv["current_components"] if "environment" in c)


# --- 외부 서비스 ----------------------------------------------------------------

def test_external_dependency_only_is_candidate(tmp_path):
    files = _app()
    files["requirements.txt"] += "openai==1.0\n"
    inv = _inventory(tmp_path, files)
    s = _ext(inv)["ext:openai"]
    assert (s["status"], s["used_by"], s["secrets"], s["kind"]) == ("candidate", ["w-web"], [], "llm-api")
    assert [(e["path"], e["line"]) for e in s["evidence"]] == [("requirements.txt", 3)]


def test_external_dependency_and_env_is_confirmed_with_secrets(tmp_path):
    files = _app("server")
    files["server/requirements.txt"] += "anthropic==0.40\n"
    files["server/.env.example"] = "# 키\nANTHROPIC_API_KEY=\nDATABASE_URL=x\n"
    files["server/llm.py"] = "import os\nkey = os.getenv('ANTHROPIC_API_KEY')\n"
    files["web/src/pay.ts"] = "const s = process.env.STRIPE_SECRET_KEY;\n"
    inv = _inventory(tmp_path, files)
    ext = _ext(inv)
    a = ext["ext:anthropic"]
    assert (a["status"], a["secrets"], a["used_by"]) == ("confirmed", ["ANTHROPIC_API_KEY"], ["w-web"])
    assert {(e["path"], e["line"]) for e in a["evidence"]} == {
        ("server/requirements.txt", 3), ("server/.env.example", 2), ("server/llm.py", 2)}
    # 환경변수만 맞으면 후보, 근거 파일을 품는 워크로드가 없으면 used_by는 비운다
    st = ext["ext:stripe"]
    assert (st["status"], st["secrets"], st["used_by"]) == ("candidate", ["STRIPE_SECRET_KEY"], [])


def test_external_code_use_is_confirmed_and_test_aux_paths_alone_do_not_count(tmp_path):
    files = _app()
    files["notify.py"] = "URL = 'https://hooks.slack.com/services/x'\n"
    files["tests/test_x.py"] = "requests.post('https://api.tosspayments.com/v1')\n"
    files["scripts/notion.py"] = "requests.get('https://api.notion.com/v1/pages')\n"
    files["docker-compose.yml"] = ("services:\n  web:\n    build: .\n    environment:\n"
                                   "      - SENDGRID_API_KEY\n")
    inv = _inventory(tmp_path, files)
    ext = _ext(inv)
    assert ext["ext:slack-webhook"]["status"] == "confirmed"
    assert "ext:toss-payments" not in ext and "ext:notion" not in ext
    sg = ext["ext:sendgrid"]
    assert sg["secrets"] == ["SENDGRID_API_KEY"]
    assert [(e["path"], e["line"]) for e in sg["evidence"]] == [("docker-compose.yml", 5)]


# --- platform 환경 --------------------------------------------------------------

def test_render_and_compose_are_two_environments(tmp_path):
    files = _app("api")
    files["api/Dockerfile"] = 'FROM python:3.12\nCMD ["uvicorn", "main:app"]\n'
    files["docker-compose.yml"] = "services:\n  api:\n    build: ./api\n    ports: ['8000:8000']\n"
    files["render.yaml"] = ("services:\n  - type: web\n    name: api\n    runtime: docker\n"
                            "    dockerfilePath: ./api/Dockerfile\n    dockerContext: ./api\n")
    inv = _inventory(tmp_path, files)
    kinds = sorted((e["name"], e["kind"]) for e in inv["environments"])
    assert kinds == [("compose", "compose"), ("render", "platform")]
    assert _deploy_envs(inv)["render"]["members"] == ["w-api"]
    assert _deploy_envs(inv)["render"]["source"]["path"] == "render.yaml"
    computes = sorted((c["component"], c.get("environment")) for c in inv["current_components"]
                      if c["scope"] == "w-api")
    assert computes == [("cp:local/compose/default", None), ("cp:render/web/unspecified-plan", "render")]
    assert _env_computes(inv) == [("w-api", "render", "cp:render/web/unspecified-plan", "confirmed")]


def test_platform_config_in_subdirectory_names_environment(tmp_path):
    files = {**_app("api"), "web/package.json": '{"dependencies": {"next": "14"}}',
             "web/app/page.tsx": "export default function P() { return null }\n", "web/fly.toml": "app = 'x'\n",
             "api/fly.toml": "app = 'y'\n"}
    inv = _inventory(tmp_path, files)
    envs = _deploy_envs(inv)
    assert envs["fly/api"]["members"] == ["w-api"]
    assert all(c[2] == "cp:fly/machines/default" for c in _env_computes(inv))


# --- ci-deploy 환경 -------------------------------------------------------------

def test_gcloud_run_deploy_source_manual_only(tmp_path):
    files = {**_app("server"), ".github/workflows/deploy.yml": (
        "name: d\non:\n  workflow_dispatch:\njobs:\n  deploy:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - uses: actions/checkout@v4\n      - run: |\n          echo hi\n"
        "          gcloud run deploy api --source server --region asia-northeast3\n")}
    inv = _inventory(tmp_path, files)
    env = _deploy_envs(inv)["ci/deploy"]
    assert (env["members"], env["manual"]) == (["w-web"], True)
    assert (env["source"]["path"], env["source"]["line"]) == (".github/workflows/deploy.yml", 11)
    assert _env_computes(inv) == [("w-web", "ci/deploy", "cp:gcp/cloud-run/unspecified", "confirmed")]


def test_ecs_pattern_uses_docker_build_in_same_job(tmp_path):
    files = {**_app("api"), "api/Dockerfile": 'FROM python:3.12\nCMD ["uvicorn", "main:app"]\n',
             ".github/workflows/release.yml": (
                 "on: [push]\nenv:\n  CTX: api\njobs:\n  ecs:\n    runs-on: ubuntu-latest\n    steps:\n"
                 "      - run: docker build -t app:1 -f ${{ env.CTX }}/Dockerfile ${{ env.CTX }}\n"
                 "      - uses: aws-actions/amazon-ecs-deploy-task-definition@v1\n"
                 "        with:\n          task-definition: td.json\n")}
    inv = _inventory(tmp_path, files)
    env = _deploy_envs(inv)["ci/release"]
    assert (env["members"], env["manual"], env["source"]["line"]) == (["w-web"], False, 9)
    assert _env_computes(inv) == [("w-web", "ci/release", "cp:aws/ecs/unspecified", "confirmed")]


def test_ssm_pattern_uses_compose_file_named_in_workflow(tmp_path):
    files = {**_app("admin"), "admin/Dockerfile": 'FROM python:3.12\nCMD ["uvicorn", "main:app"]\n',
             "deploy/docker-compose.prod.yml": "services:\n  admin:\n    build: ../admin\n",
             ".github/workflows/ec2.yml": (
                 "on:\n  workflow_dispatch:\njobs:\n  ec2:\n    runs-on: ubuntu-latest\n    steps:\n"
                 "      - run: >\n          aws ssm send-command --document-name AWS-RunShellScript\n"
                 "          --parameters commands='docker compose -f deploy/docker-compose.prod.yml up -d'\n")}
    inv = _inventory(tmp_path, files)
    env = _deploy_envs(inv)["ci/ec2"]
    assert (env["members"], env["manual"], env["source"]["line"]) == (["w-admin"], True, 8)
    assert _env_computes(inv) == [("w-admin", "ci/ec2", "cp:aws/ec2/docker-compose", "confirmed")]


def test_deploy_target_not_found_is_unmapped(tmp_path):
    files = {**_app("server"), ".github/workflows/cd.yaml": (
        "on:\n  release:\njobs:\n  go:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - run: gcloud run deploy other --image gcr.io/p/other:1\n")}
    inv = _inventory(tmp_path, files)
    env = _deploy_envs(inv)["ci/cd"]
    assert (env["members"], env["manual"]) == ([], False)
    assert _env_computes(inv) == []
    un = [u for u in inv["unmapped"] if u["label"].startswith("deploy-target:")]
    assert [(u["label"], [(e["path"], e["line"]) for e in u["evidence"]]) for u in un] == [
        ("deploy-target:gcloud-run-deploy", [(".github/workflows/cd.yaml", 7)])]


def test_malformed_workflows_and_platform_configs_do_not_crash(tmp_path):
    files = {**_app(), ".github/workflows/a.yml": "jobs: [1, 2]\n",
             ".github/workflows/b.yml": "on: push\njobs:\n  x:\n    steps: 'kubectl apply -f k8s'\n",
             ".github/workflows/c.yml": "on: push\njobs:\n  x:\n    steps:\n      - run: 'vercel deploy \"unterminated'\n"
                                        "      - 5\n      - with: [1]\n        uses: amondnet/vercel-action@v25\n",
             "render.yaml": "services: {a: 1}\n", "app.yaml": "- runtime\n", "vercel.json": "[1]"}
    inv = _inventory(tmp_path, files)
    assert sorted(_deploy_envs(inv)) == ["ci/c/x/0", "ci/c/x/2", "vercel"]


# --- 지식 베이스·일관성 ---------------------------------------------------------

def test_kb_lint_checks_external_and_deploy_entries():
    assert kb_lint.lint() == []
    bad_ext = [{"id": "ext:X", "label": "", "kind": "nope", "when": {"any": [{"env": "("}]}},
               {"id": "ext:a", "label": "a", "kind": "other", "when": {"all": []}}, "junk"]
    issues = kb_lint._lint_external(bad_ext)
    assert any("ID 형식" in i for i in issues) and any("kind" in i for i in issues)
    assert any("env 정규식" in i for i in issues) and any("any 목록" in i for i in issues)
    bad_deploy = [{"id": "d", "match": {"run": "(", "uses": "x"}, "compute": "unmapped", "target": ["x"]},
                  {"id": "e", "match": {"uses": "a/b"}, "compute": "cp:none/x/y", "target": ["cwd"]}]
    issues = kb_lint._lint_deploy(bad_deploy)
    assert any("label" in i for i in issues) and any("target" in i for i in issues)
    assert any("catalog" in i for i in issues) and any("match" in i for i in issues)


def test_consistency_checks_members_environments_and_external_ids():
    inv = {"workloads": [{"id": "w-a"}], "endpoints": [], "datastores": [], "request_paths": [],
           "current_components": [{"scope": "w-a", "component": "unmapped", "environment": "nope"}],
           "environments": [{"name": "ci/x", "members": ["w-b"]}],
           "external_services": [{"id": "ext:a", "used_by": ["w-c"]}, {"id": "ext:a", "used_by": []}]}
    issues = check_s1(inv, None)
    assert "environment ci/x: unknown member workload w-b" in issues
    assert "current component w-a: unknown environment nope" in issues
    assert "duplicate external service id: ext:a" in issues
    assert "external service ext:a: unknown workload w-c" in issues


def test_example_env_placeholder_alone_is_not_an_external_service(tmp_path):
    files = _app()
    files[".env.example"] = "# 4차 스프린트에서 사용 예정\nANTHROPIC_API_KEY=\nGOOGLE_APPLICATION_CREDENTIALS=\n"
    inv = _inventory(tmp_path, files)
    assert "ext:anthropic" not in _ext(inv) and "ext:firebase" not in _ext(inv)
