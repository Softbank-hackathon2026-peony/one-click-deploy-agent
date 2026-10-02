"""S2 프로필: 합성 저장소마다 탐지기 양성·음성, 스키마, 결정성, 일관성 검사, kb lint."""

import copy
import json

import pytest

from infrafit import kb
from infrafit.consistency import check_run, check_s2
from infrafit.kb_lint import _lint_profile_detectors
from infrafit.pipeline import analyze
from infrafit.profile.owners import Imports, Owners
from infrafit.repo import open_snapshot
from infrafit.schema import validate

FASTAPI = "fastapi==0.115\n"
MAIN = "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/h')\ndef h():\n    return 'ok'\n"


def _write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def _run(tmp_path, files: dict[str, str], name="out"):
    repo = tmp_path / "repo"
    for rel, text in files.items():
        _write(repo, rel, text)
    ctx = analyze(str(repo), tmp_path / name, until="S2", run_id="r")
    assert check_run(ctx.out_dir) == []
    profile = json.loads((ctx.out_dir / "profile.json").read_text())
    validate("Profile", profile)
    return profile


def _app(profile, dim):
    rows = [r for r in profile["dimensions"] if r["scope"] == "w-app" and r["dimension"] == dim]
    assert len(rows) == 1, (dim, profile["dimensions"])
    return rows[0]


def _py(main=MAIN, **extra):
    return {"requirements.txt": FASTAPI, "main.py": main, **extra}


def test_plain_web_app_defaults(tmp_path):
    p = _run(tmp_path, _py())
    assert p["llm_used"] is False
    assert _app(p, "A1")["value"] == ["웹"]
    a2 = _app(p, "A2")
    assert (a2["value"], a2["source"], a2["assumption_key"]) == ("1초 미만", "assumption", "A2")
    assert _app(p, "A3")["value"] == "짧은 HTTP"
    assert _app(p, "A4")["value"] == "없음"
    for dim in ("B1", "B2", "E2"):
        assert _app(p, dim)["value"] == {"value": "없음", "kinds": []}
    assert _app(p, "B3")["value"] == "없음"
    assert _app(p, "D2")["value"] == "낮음" and _app(p, "G3")["value"] == "높음"
    assert {a["key"]: a["value"] for a in p["assumptions"]} == {"A2": "1초 미만", "D2": "낮음", "G3": "높음"}
    assert all(a["reason"] for a in p["assumptions"])
    assert _app(p, "A1")["aggregated_from"] == ["w-web"]
    assert {r["scope"] for r in p["dimensions"]} == {"w-web", "w-app"}


def test_a2_llm_call_through_local_import(tmp_path):
    main = ("from fastapi import FastAPI\nfrom app.services.llm import ask\napp = FastAPI()\n\n"
            "@app.post('/gen')\ndef gen():\n    return ask()\n\n@app.get('/h')\ndef h():\n    return 'ok'\n")
    svc = "import openai\n\ndef ask():\n    return openai.OpenAI().chat.completions.create(model='x')\n"
    p = _run(tmp_path, _py(main, **{"requirements.txt": FASTAPI + "openai==1.35\n", "app/__init__.py": "", "app/services/__init__.py": "",
                                     "app/services/llm.py": svc}))
    a2 = _app(p, "A2")
    assert (a2["value"], a2["source"]) == ("수십 초", "detector")
    assert {(e["path"], e["line"]) for e in a2["evidence"]} == {("app/services/llm.py", 1), ("app/services/llm.py", 4)}
    ep_rows = [r for r in p["dimensions"] if r["scope"].startswith("ep-") and r["dimension"] == "A2"]
    # 요청 경로 탐지는 파일 단위: main.py에 핸들러가 있는 엔드포인트가 모두 같은 값을 받는다
    inv = json.loads((tmp_path / "out" / "r" / "inventory.json").read_text())
    in_main = sorted(e["id"] for e in inv["endpoints"] if e["handler"]["path"] == "main.py")
    assert sorted(r["scope"] for r in ep_rows) == in_main
    assert {r["confidence"] for r in ep_rows} == {"medium"}  # 핸들러에서 import 한 단계
    w = next(r for r in p["dimensions"] if r["scope"] == "w-web" and r["dimension"] == "A2")
    assert w["aggregated_from"] == in_main
    assert "A2" not in {a["key"] for a in p["assumptions"]}
    assert _app(p, "E2")["value"] == {"value": "있음", "kinds": ["ext:openai"]}


def test_a2_long_work_in_next_route_and_a4_unawaited(tmp_path):
    pkg = '{"dependencies": {"next": "15.0.0", "exceljs": "4", "nodemailer": "6"}}\n'
    export = ('import ExcelJS from "exceljs";\nexport async function GET() {\n'
              '  const wb = new ExcelJS.Workbook();\n  return new Response("x");\n}\n')
    signup = ('export async function POST() {\n  mailer.sendMail({ to: "a" });\n'
              '  return Response.json({});\n}\n')
    p = _run(tmp_path, {"package.json": pkg, "app/api/export/route.ts": export, "app/api/signup/route.ts": signup})
    a2 = _app(p, "A2")
    assert a2["value"] == "수십 초" and a2["confidence"] == "high"
    assert [(e["path"], e["line"]) for e in a2["evidence"]] == [("app/api/export/route.ts", 3)]
    a4 = _app(p, "A4")
    assert a4["value"] == "있음" and [(e["path"], e["line"]) for e in a4["evidence"]] == [("app/api/signup/route.ts", 2)]


def test_a4_awaited_promise_is_not_after_response(tmp_path):
    pkg = '{"dependencies": {"next": "15.0.0"}}\n'
    signup = 'export async function POST() {\n  await mailer.sendMail({ to: "a" });\n  return Response.json({});\n}\n'
    p = _run(tmp_path, {"package.json": pkg, "app/api/signup/route.ts": signup})
    assert _app(p, "A4")["value"] == "없음"


def test_a3_sse_and_websocket(tmp_path):
    sse = MAIN + ("\n@app.get('/s')\ndef s():\n"
                  "    return StreamingResponse(gen(), media_type='text/event-stream')\n")
    p = _run(tmp_path / "a", _py(sse))
    assert _app(p, "A3")["value"] == "스트리밍(SSE)"
    ws = MAIN + "\n@app.websocket('/ws')\nasync def ws(sock):\n    await sock.accept()\n"
    p = _run(tmp_path / "b", _py(ws))
    a3 = _app(p, "A3")
    assert a3["value"] == "장시간 양방향(웹소켓)" and a3["evidence"][0]["path"] == "main.py"
    assert _app(p, "A1")["value"] == ["웹", "실시간 연결"]


def test_a4_background_tasks_and_test_paths_skipped(tmp_path):
    bg = MAIN + "\n@app.post('/j')\ndef j(background_tasks: BackgroundTasks):\n    return 'ok'\n"
    p = _run(tmp_path / "a", _py(bg))
    assert _app(p, "A4")["value"] == "있음"
    tests_only = _py(**{"tests/test_bg.py": "from fastapi import BackgroundTasks\n",
                        "scripts/job.py": "import asyncio\nasyncio.create_task(x())\n"})
    p = _run(tmp_path / "b", tests_only)
    assert _app(p, "A4")["value"] == "없음"


def test_b1_rate_limit_memory_vs_shared_store(tmp_path):
    mem = MAIN + "limiter = Limiter(key_func=get_remote_address)\n"
    p = _run(tmp_path / "a", _py(mem))
    assert _app(p, "B1")["value"] == {"value": "있음", "kinds": ["in-memory-rate-limit"]}
    shared = MAIN + "limiter = Limiter(key_func=get_remote_address, storage_uri='redis://r')\n"
    p = _run(tmp_path / "b", _py(shared))
    assert _app(p, "B1")["value"]["value"] == "없음"


def test_b2_sqlite_and_b3_in_process_scheduler(tmp_path):
    main = MAIN + "import sqlite3\nconn = sqlite3.connect('app.db')\n"
    sched = "from apscheduler.schedulers.background import BackgroundScheduler\ns = BackgroundScheduler()\n"
    p = _run(tmp_path, {"requirements.txt": FASTAPI + "apscheduler==3.10\n", "main.py": main, "jobs.py": sched})
    assert _app(p, "B2")["value"] == {"value": "있음", "kinds": ["sqlite"]}
    b3 = _app(p, "B3")
    assert b3["value"] == "있음"
    assert ("jobs.py", 2) in {(e["path"], e["line"]) for e in b3["evidence"]}


def test_spring_scheduled_async_and_stomp_broker(tmp_path):
    gradle = ('plugins { id("org.springframework.boot") version "3.2.0" }\ndependencies {\n'
              '    implementation("org.springframework.boot:spring-boot-starter-web")\n'
              '    implementation("org.springframework.boot:spring-boot-starter-websocket")\n}\n')
    app = ("package com.x\n\n@SpringBootApplication\nclass App\n")
    jobs = ("package com.x\n\nclass Jobs {\n    @Scheduled(cron = \"0 * * * * *\")\n    fun tick() {}\n\n"
            "    @Async\n    fun push() {}\n}\n")
    ws = ("package com.x\n\n@Configuration\n@EnableWebSocketMessageBroker\nclass Ws {\n"
          "    fun c(registry: MessageBrokerRegistry) {\n        registry.enableSimpleBroker(\"/topic\")\n    }\n}\n")
    p = _run(tmp_path, {"build.gradle.kts": gradle, "src/main/kotlin/com/x/App.kt": app,
                        "src/main/kotlin/com/x/Jobs.kt": jobs, "src/main/kotlin/com/x/Ws.kt": ws})
    assert _app(p, "B3")["value"] == "있음"
    assert _app(p, "A4")["value"] == "있음"
    assert _app(p, "B1")["value"] == {"value": "있음", "kinds": ["websocket-broker"]}


def test_worker_has_no_request_dimensions(tmp_path):
    files = {"requirements.txt": FASTAPI, "main.py": MAIN,
             "Procfile": "web: uvicorn main:app\nworker: python worker.py\n", "worker.py": "print('x')\n"}
    p = _run(tmp_path, files)
    assert _app(p, "A1")["value"] == ["웹", "워커"]
    worker = [r for r in p["dimensions"] if r["scope"] not in ("w-app", "w-web") and not r["scope"].startswith("ep-")]
    assert worker and not {r["dimension"] for r in worker} & {"A2", "A3"}
    assert len(_app(p, "A1")["aggregated_from"]) == 2


def test_no_app_workload_has_no_dimensions_or_assumptions(tmp_path):
    p = _run(tmp_path, {"README.md": "hello\n"})
    assert p["dimensions"] == []
    assert p["assumptions"] == []


def test_batch_entrypoint_is_one_off_run_with_low_confidence(tmp_path):
    main = 'def main(): ...\n\n\nif __name__ == "__main__":\n    main()\n'
    p = _run(tmp_path, {"jobs/collect.py": main})
    a1 = _app(p, "A1")
    assert a1["value"] == ["일회성 실행"] and a1["confidence"] == "low"
    w = next(r for r in p["dimensions"] if r["scope"] == "w-collect" and r["dimension"] == "A1")
    assert w["confidence"] == "low"
    assert {a["key"] for a in p["assumptions"]} >= {"D2", "G3"}


def test_deterministic_and_cached(tmp_path):
    files = _py(**{"jobs.py": "import asyncio\nasyncio.create_task(x())\n"})
    a = _run(tmp_path, files, "a")
    b = _run(tmp_path, files, "b")
    strip = lambda d: json.dumps({k: v for k, v in d.items() if k != "meta"}, sort_keys=True)  # noqa: E731
    assert strip(a) == strip(b)
    c = _run(tmp_path, files, "a")  # 같은 출력 루트: 캐시
    assert strip(a) == strip(c) and a["meta"]["input_hash"] == c["meta"]["input_hash"]


def test_owners_split_by_directory(tmp_path):
    _write(tmp_path, "server/a.py", "x\n")
    _write(tmp_path, "worker/b.py", "x\n")
    _write(tmp_path, "shared/c.py", "x\n")
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    inv = {"workloads": [
        {"id": "w-server", "kind": "web", "name": "server", "entrypoint": {"path": "server/pyproject.toml"}},
        {"id": "w-worker", "kind": "worker", "name": "worker", "entrypoint": {"path": "worker/pyproject.toml"}}],
        "endpoints": []}
    o = Owners(snap, inv, ["w-server", "w-worker"])
    assert o.owners("server/a.py") == ["w-server"]
    assert o.owners("worker/b.py") == ["w-worker"]
    assert o.owners("shared/c.py") == []  # 둘 이상이면 품은 기준이 없는 파일은 귀속하지 않는다


def test_imports_resolve_python_and_js(tmp_path):
    _write(tmp_path, "app/routers/r.py", "from ..services import llm\nfrom app.util import f\n")
    _write(tmp_path, "app/services/llm.py", "x\n")
    _write(tmp_path, "app/util.py", "x\n")
    _write(tmp_path, "web/app/api/route.ts", 'import { pool } from "@/lib/db";\nimport x from "../../lib/y";\n')
    _write(tmp_path, "web/lib/db.ts", "x\n")
    _write(tmp_path, "web/lib/y.js", "x\n")
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    imp = Imports(snap)
    assert set(imp.direct("app/routers/r.py")) == {"app/services/llm.py", "app/util.py"}
    assert set(imp.direct("web/app/api/route.ts")) == {"web/lib/db.ts", "web/lib/y.js"}


def test_check_s2_flags_bad_rows(tmp_path):
    files = _py()
    p = _run(tmp_path, files)
    inv = json.loads((tmp_path / "out" / "r" / "inventory.json").read_text())
    bad = copy.deepcopy(p)
    bad["dimensions"].append({"dimension": "A3", "scope": "w-nope", "value": "websocket", "source": "detector",
                              "confidence": "high", "evidence": [{"path": "missing.py", "line": 1, "snippet": "x"}]})
    issues = check_s2(bad, inv, tmp_path / "repo")
    assert any("unknown scope" in i for i in issues)
    assert any("outside vocabulary" in i for i in issues)
    assert any("evidence file missing" in i for i in issues)
    assert check_s2(p, inv, tmp_path / "repo") == []


@pytest.mark.parametrize("mutate,needle", [
    (lambda c: c["dimensions"]["A2"].update(default={"value": "빠름", "source": "assumption", "reason": "r"}),
     "default.value"),
    (lambda c: c["dimensions"]["A2"]["default"].pop("reason"), "reason"),
    (lambda c: c["code"].append({"id": "X", "dimension": "A9", "value": "있음", "scope": "workload",
                                 "glob": ["**/*.py"], "regex": "x"}), "정의되지 않은 dimension"),
    (lambda c: c["code"].append({"id": "Y", "dimension": "A3", "value": "websocket", "scope": "workload",
                                 "glob": ["**/*.py"], "regex": "x"}), "어휘에 없는 value"),
    (lambda c: c["code"].append({"id": "Z", "dimension": "B1", "kind": "k", "scope": "everywhere",
                                 "glob": ["**/*.py"], "regex": "("}), "scope"),
    (lambda c: c["code"].append({"id": "Z", "dimension": "B1", "kind": "k", "scope": "workload",
                                 "glob": ["**/*.py"], "regex": "("}), "정규식 오류"),
    (lambda c: c["code"].append(dict(c["code"][0])), "중복 ID"),
    (lambda c: c["components"].append({"component": "zz:none/*", "dimension": "B2", "kind": "k"}), "카탈로그"),
    (lambda c: c["external"].append({"kinds": ["llm-api"], "dimension": "A4"}), "kinds 차원"),
    (lambda c: c.update(app_scope="app"), "app_scope"),
])
def test_lint_profile_detectors_negative(mutate, needle):
    cfg = copy.deepcopy(kb.profile_detectors())
    assert _lint_profile_detectors(cfg) == []
    mutate(cfg)
    issues = _lint_profile_detectors(cfg)
    assert any(needle in i for i in issues), issues
