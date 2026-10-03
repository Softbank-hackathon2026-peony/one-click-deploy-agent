# InfraFit QA 후속 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** agentcore QA(10/03)에서 InfraFit 원인으로 남은 네 가지를 고친다: Procfile `beat` 누락, 코드 경로 deploy_units 의 저장소 컨테이너 누락, `time.sleep(40)` 같은 긴 동기 대기 미탐지, 근거 있는 요구에 대한 능력 모름(Lambda 웹소켓) 후보의 추천.

**Architecture:** S1(workloads·deploy_units)·S2(profile_detectors 시그니처)·S4(recommend) 각각 한 군데씩 고친다. 지식(images.yaml `image`·`url_scheme`·`url_template`, profile_detectors.yaml 시그니처)은 YAML 에 두고 kb_lint 가 검사한다. 출력 모양은 하위 호환(새 선택 필드와 outcome 값 하나만 추가).

**Tech Stack:** Python 3.12, pytest (`.venv/bin/python -m pytest -q`), PyYAML, jsonschema.

**Spec:** `docs/superpowers/specs/2026-10-03-infrafit-qa-followup-design.md`

## Global Constraints

- 저장소 `/Users/jerry/Desktop/workspace/projects/softbank-hackerton/one-click-deploy-agent`, 브랜치 `main` 에 직접 커밋(사용자 결정). push 는 컨트롤러가 마지막에 한다.
- 기준선: `.venv/bin/python -m pytest -q` → 507 passed. `kb_lint.lint()` → `[]`.
- 값을 지어내지 않는다: 저장소 컨테이너는 비밀번호 없이 뜨는 저장소만(redis·memcached), 접속 주소 환경변수는 코드에서 찾은 이름에만 넣는다.
- 출력 하위 호환: 기존 필드 이름·모양 유지. 새 필드는 선택(스키마 required 에 넣지 않음).
- 코드 주석·메시지는 한국어, 짧게, 기존 스타일.
- 커밋 메시지 끝에 정확히 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

---

### Task 1: Procfile `beat`·`scheduler`·`cron` → scheduled 워크로드

**Files:**
- Modify: `infrafit/detect/workloads.py` (`PROC_KINDS` 줄 29, Procfile 루프 줄 252-257)
- Test: `tests/test_deploy_units.py`

**Interfaces:**
- Produces: Procfile `beat:`/`scheduler:`/`cron:` 항목과, 표에 없는 유형이라도 명령이 `celery … beat` 인 항목은 `kind: scheduled` 워크로드(`w-scheduled` 등). deploy_units 코드 경로에서 컨테이너가 된다(`one_shot: false`).

- [ ] **Step 1: 실패하는 테스트** (`tests/test_deploy_units.py` 끝)

```python
def _celery_repo(root):
    _write(root, "requirements.txt", "flask==3.0.3\ncelery==5.4.0\nredis==5.0.4\ngunicorn==22.0.0\n")
    _write(root, "Procfile", "web: gunicorn -b 0.0.0.0:$PORT app:app\nworker: celery -A tasks worker --loglevel=info\n"
                             "beat: celery -A tasks beat --loglevel=info\n")
    _write(root, "app.py", "from flask import Flask\nfrom tasks import send_report\napp = Flask(__name__)\n\n"
                           "@app.get('/health')\ndef health():\n    return 'ok'\n")
    _write(root, "tasks.py", "import os\nfrom celery import Celery\n\n"
                             "REDIS_URL = os.environ.get(\"REDIS_URL\", \"redis://localhost:6379/0\")\n"
                             "celery = Celery(\"tasks\", broker=REDIS_URL, backend=REDIS_URL)\n\n"
                             "@celery.task\ndef send_report(kind):\n    return kind\n")


def test_procfile_beat_is_scheduled_workload_and_container(tmp_path):
    _celery_repo(tmp_path)
    ctx = analyze(str(tmp_path), tmp_path / "out", until="S1", run_id="r")
    inv = json.loads((ctx.out_dir / "inventory.json").read_text())
    kinds = {w["name"]: w["kind"] for w in inv["workloads"]}
    assert kinds.get("scheduled") == "scheduled" or "scheduled" in kinds.values()
    sched = next(w for w in inv["workloads"] if w["kind"] == "scheduled")
    assert sched["entrypoint"]["path"] == "Procfile" and sched["entrypoint"]["line"] == 3
    cs = {c["workload"]: c for c in inv["deploy_units"]["containers"]}
    assert cs[sched["id"]]["command"] == "celery -A tasks beat --loglevel=info"
    assert cs[sched["id"]]["one_shot"] is False


def test_unknown_procfile_type_with_celery_beat_command_is_scheduled(tmp_path):
    _celery_repo(tmp_path)
    _write(tmp_path, "Procfile", "web: gunicorn -b 0.0.0.0:$PORT app:app\nclockwork: celery -A tasks beat\n")
    ctx = analyze(str(tmp_path), tmp_path / "out", until="S1", run_id="r")
    inv = json.loads((ctx.out_dir / "inventory.json").read_text())
    assert any(w["kind"] == "scheduled" for w in inv["workloads"])
```

첫 테스트의 `kinds` 단언은 실행해서 실제 워크로드 이름(`scheduled` 일 것)을 확인한 뒤 하나의 정확한 단언(`kinds["scheduled"] == "scheduled"` 등)으로 바꿔라 — or 단언을 남기지 않는다.

- [ ] **Step 2: 실패 확인** — `.venv/bin/python -m pytest -q tests/test_deploy_units.py -k "beat or celery"` → scheduled 워크로드 없음.

- [ ] **Step 3: 구현**

```python
PROC_KINDS = {"web": "web", "worker": "worker", "clock": "scheduled", "beat": "scheduled", "scheduler": "scheduled",
              "cron": "scheduled", "release": "migration-job"}
# 표에 없는 Procfile 유형이라도 Celery beat(정기 작업 스케줄러)를 실행하면 정기 작업이다
CELERY_BEAT = re.compile(r"\bcelery\b.*\bbeat\b")
```

Procfile 루프:

```python
        wkind = PROC_KINDS.get(proc) or ("scheduled" if CELERY_BEAT.search(cmd) else None)
```

- [ ] **Step 4: 통과 확인 + 전체** — `pytest -q` (골든이 바뀌면 이유를 보고서에 적는다: 픽스처에 Procfile beat 가 없으면 바뀌지 않아야 한다).

- [ ] **Step 5: 커밋** — `Treat Procfile beat/scheduler/cron and celery beat commands as scheduled workloads` + trailer.

---

### Task 2: 코드 경로 deploy_units 의 저장소 컨테이너와 접속 주소

**Files:**
- Modify: `knowledge/images.yaml` (redis·memcached 항목), `infrafit/kb_lint.py` (`IMAGE_KEYS`, `_lint_images`), `infrafit/detect/images.py` (`classify_image` 가 새 필드를 돌려줌), `infrafit/detect/deploy_units.py` (`_from_code`, `detect_deploy_units`), `infrafit/stages/s1_inventory.py` (호출)
- Test: `tests/test_deploy_units.py`, `tests/test_images.py`

**Interfaces:**
- Consumes: Task 1 의 scheduled 컨테이너, `_celery_repo` 도우미.
- Produces: `detect_deploy_units(snap, artifacts, workloads, datastores, current_components=None)`; images.yaml 항목 선택 필드 `image: str`, `url_scheme: list[str]`, `url_template: str` (`{scheme}`, `{host}`, `{port}` 자리표시자만).

- [ ] **Step 1: images.yaml**

redis 항목에 `image: "redis:7-alpine"`, `url_scheme: [redis, rediss]`, `url_template: "{scheme}://{host}:{port}/0"`; memcached 항목에 `image: "memcached:1.6-alpine"`. postgres·mysql·mongo 에는 넣지 않는다(파일 위 주석에 이유 한 줄: "비밀번호 없이는 뜨지 않는 공식 이미지는 image 를 두지 않는다").

- [ ] **Step 2: 실패하는 테스트**

`tests/test_deploy_units.py`:

```python
def test_code_path_redis_becomes_store_container_with_env(tmp_path):
    _celery_repo(tmp_path)
    u = _units(tmp_path, tmp_path)
    assert u["source"]["kind"] == "code"
    stores = {d["id"]: d for d in u["datastores"]}
    assert stores["redis"]["datastore"] == "svc-redis"
    assert stores["redis"]["image"] == "redis:7-alpine" and stores["redis"]["ports"] == [6379]
    assert stores["redis"]["env"] == {} and stores["redis"]["evidence"]["path"] == "requirements.txt"
    for c in u["containers"]:
        assert "redis" in c["depends_on"]
        assert c["env"]["REDIS_URL"] == "redis://redis:6379/0" and "REDIS_URL" in c["env_names"]


def test_code_path_postgres_needs_credentials_so_no_container(tmp_path):
    _write(tmp_path, "requirements.txt", "flask==3.0.3\npsycopg2-binary==2.9.9\n")
    _write(tmp_path, "app.py", "import os, psycopg2\nfrom flask import Flask\napp = Flask(__name__)\n"
                               "conn = psycopg2.connect(os.environ.get('DATABASE_URL', 'postgres://localhost/app'))\n\n"
                               "@app.get('/h')\ndef h():\n    return 'ok'\n")
    u = _units(tmp_path, tmp_path)
    assert u["datastores"] == []
    assert any(x["field"].startswith("datastores.") and "비밀번호" in x["why"] for x in u["unresolved"])


def test_code_path_without_env_default_adds_container_but_no_env(tmp_path):
    _celery_repo(tmp_path)
    _write(tmp_path, "tasks.py", "from celery import Celery\ncelery = Celery('tasks', broker='redis://localhost:6379/0')\n")
    u = _units(tmp_path, tmp_path)
    assert [d["id"] for d in u["datastores"]] == ["redis"]
    assert all("REDIS_URL" not in c["env"] for c in u["containers"])
```

`tests/test_images.py` (기존 `_lint_images` 테스트 옆):

```python
def test_image_field_lint():
    from infrafit.kb_lint import _lint_images
    assert _lint_images([{"match": ["redis"], "role": "cache", "image": "redis:7-alpine",
                          "url_scheme": ["redis"], "url_template": "{scheme}://{host}:{port}/0"}]) == []
    issues = " ".join(_lint_images([
        {"match": ["a"], "role": "cache", "image": "redis"},                       # 태그 없음
        {"match": ["b"], "role": "reverse-proxy", "image": "nginx:1"},             # 저장소가 아님
        {"match": ["c"], "role": "cache", "image": "x:1", "url_template": "{user}@{host}"},   # 모르는 자리표시자
    ]))
    assert "태그" in issues and "role" in issues and "url_template" in issues
```

`postgres://` 테스트는 InfraFit 이 `psycopg2-binary` 를 postgres 저장소(`ds:unspecified/postgresql/default`)로 잡는지 먼저 확인하고, 잡지 않으면 다른 확실한 신호(`asyncpg`·`DATABASE_URL` 등 시그니처가 잡는 것)로 바꿔라.

- [ ] **Step 3: 실패 확인.**

- [ ] **Step 4: 구현**

`kb_lint.py`:

```python
IMAGE_KEYS = {"match", "role", "component", "hosting_hint", "port", "image", "url_scheme", "url_template"}
IMAGE_REF = re.compile(r"^[a-z0-9][a-z0-9._/-]*:[A-Za-z0-9._-]+$")
URL_FIELDS = re.compile(r"\{(\w+)\}")
```

`_lint_images` 루프 안:

```python
        if "image" in e:
            if not isinstance(e["image"], str) or not IMAGE_REF.match(e["image"]):
                issues.append(f"{name}: image 는 태그가 있는 공식 이미지여야 함 {e.get('image')!r}")
            if e.get("role") not in ("datastore", "cache", "queue"):
                issues.append(f"{name}: image 는 저장소 role(datastore·cache·queue)에만 둔다 (role {e.get('role')})")
        if "url_scheme" in e and not (isinstance(e["url_scheme"], list) and e["url_scheme"]
                                      and all(isinstance(s, str) and s.isalnum() for s in e["url_scheme"])):
            issues.append(f"{name}: url_scheme 은 영숫자 문자열 목록")
        if "url_template" in e:
            fields = set(URL_FIELDS.findall(str(e["url_template"])))
            if not fields <= {"scheme", "host", "port"} or "url_scheme" not in e:
                issues.append(f"{name}: url_template 자리표시자는 scheme·host·port 만, url_scheme 이 필요함")
```

`images.py` `classify_image` 반환 dict 에 `"image": entry.get("image"), "url_scheme": entry.get("url_scheme"), "url_template": entry.get("url_template")` 추가. 이 함수 결과를 쓰는 다른 곳이 키 집합에 의존하지 않는지 grep 으로 확인.

`deploy_units.py`: 모듈 위에

```python
from infrafit.repo import Snapshot, parent_dir   # (이미 있음)
from infrafit.detect.testpaths import is_test_path
from infrafit.detect.signatures import is_aux_path

# 코드에서 저장소 주소를 기본값으로 읽는 환경변수: os.environ.get("X", "redis://…"), os.getenv(…), process.env.X || "…"
_ENV_DEFAULT = (
    re.compile(r"""os\.(?:environ\.get|getenv)\(\s*["']([A-Z][A-Z0-9_]*)["']\s*,\s*["'](\w+)://"""),
    re.compile(r"""process\.env\.([A-Z][A-Z0-9_]*)\s*(?:\|\||\?\?)\s*["'`](\w+)://"""),
)
CODE_EXTS = (".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx")
```

`_from_code(snap, artifacts, workloads, datastores, current_components)` 끝, `return` 전에:

```python
    stores = _code_stores(snap, containers, apps, datastores or [], current_components or [], unresolved)
    return {"source": {"kind": "code", "path": apps[0].entrypoint["path"]}, "images": images,
            "containers": containers, "datastores": stores, "entry": entry, "unresolved": unresolved}
```

```python
def _image_entry(component: str) -> dict | None:
    """images.yaml 에서 이 구성 요소를 가리키는 항목(첫 번째)."""
    return next((e for e in kb.images() if e.get("component") == component), None)


def _code_stores(snap: Snapshot, containers: list[dict], apps: list[WorkloadInfo], datastores: list[dict],
                 current: list[dict], unresolved: list[dict]) -> list[dict]:
    """compose·k8s 없이 코드에서만 쓰는 저장소: 비밀번호 없이 뜨는 공식 이미지가 있으면 같은 묶음의 컨테이너로 만든다.
    앱 코드가 저장소 주소를 기본값으로 읽는 환경변수가 있으면 그 이름에 컨테이너 주소를 넣는다(없으면 넣지 않는다)."""
    comp_of = {c["scope"]: c["component"] for c in current}
    used_ids = {c["id"] for c in containers}
    out = []
    for d in datastores:
        if d.get("status") != "confirmed":
            continue
        entry = _image_entry(comp_of.get(d["id"], ""))
        if entry is None:
            continue
        if not entry.get("image"):
            _unresolved(unresolved, f"datastores.{d['id']}", "접속 정보(비밀번호)가 필요한 저장소라 컨테이너를 만들지 않는다")
            continue
        sid = entry["match"][0]
        sid = f"{sid}-store" if sid in used_ids else sid
        used_ids.add(sid)
        port = entry.get("port")
        ev = (d.get("evidence") or [{}])[0]
        out.append({"id": sid, "datastore": d["id"], "image": entry["image"], "ports": [port] if port else [],
                    "env": {}, "env_names": [], "evidence": {k: ev[k] for k in ("path", "line", "snippet") if k in ev}})
        users = set(d.get("used_by") or [])
        for c in containers:
            if c.get("workload") not in users:
                continue
            c["depends_on"] = list(dict.fromkeys([*c["depends_on"], sid]))
            w = next((a for a in apps if a.id == c["workload"]), None)
            for name, scheme in _env_defaults(snap, w, entry.get("url_scheme") or []):
                if entry.get("url_template") and port:
                    c["env"][name] = entry["url_template"].format(scheme=scheme, host=sid, port=port)
                    c["env_names"] = sorted({*c["env_names"], name})
    return out


def _env_defaults(snap: Snapshot, w: WorkloadInfo | None, schemes: list[str]) -> list[tuple[str, str]]:
    """워크로드 코드에서 저장소 주소(스킴)를 기본값으로 읽는 환경변수 (이름, 스킴). 테스트·보조 경로는 보지 않는다."""
    if w is None or not schemes:
        return []
    root = w.code_root or ""
    found: dict[str, str] = {}
    for rel in snap.files:
        if not rel.endswith(CODE_EXTS) or (root and not rel.startswith(root.rstrip("/") + "/")) \
                or is_test_path(rel) or is_aux_path(rel):
            continue
        for line in snap.lines(rel):
            for rx in _ENV_DEFAULT:
                for name, scheme in rx.findall(line):
                    if scheme in schemes:
                        found.setdefault(name, scheme)
    return sorted(found.items())
```

`snap.files`·`snap.lines` 이름이 실제 `Snapshot` API 와 같은지 `infrafit/repo.py` 에서 확인하고 맞춘다(목록 메서드가 `glob` 뿐이면 `snap.glob("**/*")`). `code_root` 가 `""`(저장소 루트)이면 전체를 본다. 컨테이너 `env` 에 값을 넣을 때 `is_secret(name, value)` 가 참이면 넣지 않는다(주소에 비밀번호가 없으니 보통 거짓).

`detect_deploy_units(..., datastores, current_components=None)` 에서 `_from_code(snap, artifacts, workloads, datastores, current_components)` 로 넘기고, `s1_inventory.py` 호출을 `detect_deploy_units(snap, artifacts, workloads, datastores, components)` 로 바꾼다.

- [ ] **Step 5: 통과 확인 + 전체 + 골든** — `pytest -q`. `test_golden` 이 바뀌면 `.venv/bin/python scripts/update_golden.py` 로 다시 만들고 `git diff --stat fixtures/` 와 바뀐 내용(저장소 컨테이너·depends_on·env 만이어야 함)을 보고서에 적는다. 다른 내용이 바뀌면 코드 문제다. `kb_lint.lint() == []`.

- [ ] **Step 6: 커밋** — `Add credential-free code-path store containers with env wiring to deploy_units` + trailer.

---

### Task 3: A2 시그니처 — 요청 경로의 긴 동기 대기

**Files:**
- Modify: `knowledge/profile_detectors.yaml` (`code:` 의 A2 시그니처 뒤)
- Test: `tests/test_profile.py`

- [ ] **Step 1: 실패하는 테스트** (`tests/test_profile.py`, 기존 `_run`·`_app`·`_py` 도우미 사용)

```python
def test_a2_long_sleep_in_handler(tmp_path):
    main = ("import time\nfrom fastapi import FastAPI\napp = FastAPI()\n\n"
            "@app.get('/slow')\ndef slow():\n    time.sleep(40)\n    return 'ok'\n")
    a2 = _app(_run(tmp_path, _py(main)), "A2")
    assert (a2["value"], a2["source"]) == ("수십 초", "detector")
    assert [(e["path"], e["line"]) for e in a2["evidence"]] == [("main.py", 7)]


def test_a2_short_sleep_is_not_long(tmp_path):
    main = "import time\nfrom fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/s')\ndef s():\n    time.sleep(2)\n    return 'ok'\n"
    assert _app(_run(tmp_path, _py(main)), "A2")["source"] == "assumption"


def test_a2_long_settimeout_in_express_route(tmp_path):
    pkg = '{"dependencies": {"express": "4"}}\n'
    server = ("const express = require('express');\nconst app = express();\n"
              "app.get('/slow', async (req, res) => {\n"
              "  await new Promise((r) => setTimeout(r, 30000));\n  res.send('ok');\n});\napp.listen(3000);\n")
    a2 = _app(_run(tmp_path, {"package.json": pkg, "server.js": server}), "A2")
    assert a2["value"] == "수십 초" and a2["evidence"][0]["line"] == 4
```

- [ ] **Step 2: 실패 확인.**

- [ ] **Step 3: 구현** — `profile_detectors.yaml` `code:` 의 `PD-A2-LONG-*` 뒤에:

```yaml
  # A2: 요청 경로의 긴 동기 대기(10초 이상 상수). 변수 인자는 잡지 않는다
  - id: PD-A2-SLEEP-PY
    dimension: A2
    value: "수십 초"
    scope: request-path
    glob: ["**/*.py"]
    regex: '(?:\btime\.|\basyncio\.|(?<![\w.]))sleep\(\s*[1-9]\d+(?:\.\d+)?\s*\)'
  - id: PD-A2-SLEEP-JS
    dimension: A2
    value: "수십 초"
    scope: request-path
    glob: ["**/*.js", "**/*.mjs", "**/*.cjs", "**/*.ts", "**/*.tsx", "**/*.jsx"]
    regex: '\bsetTimeout\([^,]*,\s*[1-9]\d{4,}\s*\)|\b(?:sleep|delay)\(\s*[1-9]\d{4,}\s*\)'
```

kb_lint `_lint_profile_detectors` 가 새 항목(id 형식, 차원·값 어휘)을 통과하는지 확인.

- [ ] **Step 4: 통과 확인 + 전체 + lint** (기존 픽스처 f1~f6 골든은 S1 만이라 바뀌지 않아야 한다).

- [ ] **Step 5: 커밋** — `Detect long constant sleeps in request paths as A2 tens of seconds` + trailer.

---

### Task 4: S4 — 근거 있는 요구에 대한 능력을 모르는 후보는 추천하지 않음

**Files:**
- Modify: `infrafit/fit/engine.py` (`Cell`, `evaluate`), `infrafit/fit/recommend.py` (`Recommender._cell`/`_add`/`Combo`/`_candidate`/`run`/`_outcome`, 모듈 docstring), `infrafit/consistency.py` (`check_s4`), `schemas/infrafit.schema.json` (`Candidate.unknown`, outcome enum), `README.md` S4 절
- Test: `tests/test_ranking.py` (기존 도우미 `capc`, `web_inventory`, `prof`, `dim`, `WS_RULE` 사용), `tests/test_fit_recommend.py`

**Interfaces:**
- Produces: 후보 선택 필드 `unknown: [{scope, component, rule, dimension, dimension_value, capability, at}]`; `recommended` 는 `unknown` 없는 첫 후보; outcome `unverified`.

- [ ] **Step 1: 실패하는 테스트** (`tests/test_ranking.py`)

```python
def test_evidence_unknown_candidate_is_not_recommended(tmp_path):
    caps = [capc(RUN, "gcp", "gcp_cloud_run", 0, CP__always_on=False, CP__horizontal_scaling=True),   # websocket 모름
            capc(ECS, "aws", "aws_ecs_fargate", 30, CP__websocket=True, CP__always_on=True, CP__horizontal_scaling=True)]
    rec, fit, inv = recommend(prof(dim("A3", "장시간 양방향(웹소켓)", path="server.js", line=8)), caps)
    run = next(c for c in rec["candidates"] if c["placement"][0]["component"] == RUN)
    assert run["unknown"] == [{"scope": "w-web", "component": RUN, "rule": "CAP-WEBSOCKET-001", "dimension": "A3",
                               "dimension_value": "장시간 양방향(웹소켓)", "capability": "CP.websocket",
                               "at": ["server.js:8"]}]
    top = next(c for c in rec["candidates"] if c["id"] == rec["recommended"])
    assert top["placement"][0]["component"] == ECS and "unknown" not in top
    assert rec["outcome"] == "recommended"
    assert check_s4(rec, fit, inv, prof(dim("A3", "장시간 양방향(웹소켓)", path="server.js", line=8))) == []
    for c in rec["candidates"]:
        validate("Candidate", c)


def test_all_candidates_unknown_gives_unverified_outcome(tmp_path):
    caps = [capc(RUN, "gcp", "gcp_cloud_run", 0, CP__always_on=False)]
    p = prof(dim("A3", "장시간 양방향(웹소켓)"))
    rec, fit, inv = recommend(p, caps)
    assert rec["candidates"] and rec["recommended"] is None
    assert rec["outcome"] == "unverified"
    assert rec["outcome_detail"]["unknown_capabilities"] == ["CP.websocket"]
    assert check_s4(rec, fit, inv, p) == []
    validate("Recommendation", {**rec, "meta": _meta()})
```

`dim(...)` 도우미에 `path`·`line` 인자가 있는지 확인(있음: `dim(d, value, source="detector", path="app.py", line=3, scope="w-web")`). `validate("Recommendation", …)` 에 필요한 `meta` 는 `tests/test_fit_recommend.py` 의 `run_s4` 기반 검증 방식을 따르거나 `run_s4(RunContext…)` 로 단계 출력을 만들어 검증한다 — `_meta()` 를 새로 만들지 말고 기존 테스트가 쓰는 방법을 그대로 써라.

- [ ] **Step 2: 실패 확인.**

- [ ] **Step 3: 구현**
- `engine.Cell` 에 출력하지 않는 `evidence_unknowns: list[dict] = field(default_factory=list)`; `evaluate` 의 `state == "unknown"` 분기에서 detector 근거가 있을 때 `refs` 의 빠진 키마다 `{"rule": rule["id"], "dimension": <hit 의 detector 행 차원>, "dimension_value": dim_value(첫 detector 행 value), "capability": k, "at": [path:line…최대 2]}` 를 넣는다(scope·component 는 Recommender 가 붙인다).
- `Recommender._cell`: 캐시 값을 `(cell.to_dict(), cell.evidence_unknown, cell.evidence_unknowns)` 로 바꾸고 기존 호출부(`cell, ev = …`)를 세 값 반환에 맞게 고치거나, 별도 dict `self.unknown_detail[key]` 에 저장해 기존 반환을 유지한다(호출부가 적은 쪽).
- `Combo` 에 `unknowns: list[dict]`; `_add` 가 `ev and cell["result"] == "unknown"` 일 때 `{"scope": scope.id, "component": cid, **u}` 를 중복 없이 더한다.
- `_candidate`: `combo.unknowns` 가 있으면 `"unknown": combo.unknowns`.
- `run`: 정렬·id 부여 뒤 `recommended = next((c["id"] for c in feasible if not c.get("unknown")), None)`.
- `_outcome(feasible, batch)`: feasible 이 있고 모두 `unknown` 이면 `("unverified", {"message": "조건을 만족하는지 확인하지 못한 후보만 남았다", "unknown_capabilities": sorted({u["capability"] for c in feasible for u in c["unknown"]})})`.
- `check_s4`: 스펙 §4 두 규칙. 기존 "recommended is null although candidates exist" 검사를 outcome `unverified` 일 때 예외로.
- 스키마: `Candidate.properties.unknown` (항목 required 7개, additionalProperties false), outcome enum 에 `unverified`, outcome_detail 이 이 모양을 허용하는지 확인(지금 `outcome_detail` 정의를 보고 맞춘다).
- README S4 절과 recommend.py docstring 에 한 문단.

- [ ] **Step 4: 통과 확인 + 전체** — 기존 테스트 중 근거 있는 unknown 후보가 `recommended` 였던 것이 있으면, 새 규칙이 의도한 변화인지 확인하고 기대값을 고친다(주석에 이유). 탈락·비용·순위가 바뀌면 코드 문제다.

- [ ] **Step 5: 커밋** — `Do not recommend candidates whose platform capability is unknown for a detected requirement; unverified outcome` + trailer.

---

### Task 5: 재현 픽스처·문서

**Files:**
- Create: `fixtures/f7-celery-redis/repo/**` (Task 1 `_celery_repo` 와 같은 파일 + `/slow` 핸들러 `time.sleep(40)`), `fixtures/f8-socketio-chat/repo/{package.json,server.js}` (express + socket.io)
- Modify: `fixtures/*/golden/*` (스크립트로), `README.md`, `docs/superpowers/notes/2026-10-03-infrafit-qa-followup.md` (새)

- [ ] **Step 1: 픽스처 두 개를 만들고 `.venv/bin/python scripts/update_golden.py`** — 새 골든만 생기고 기존 f1~f6 골든은 Task 2 결과 외에는 바뀌지 않아야 한다.
- [ ] **Step 2: `scripts/qa_ranking.py`** 를 돌려 f7·f8 줄을 확인한다: f7 은 workloads 에 scheduled, deploy_units 에 redis, A2 "수십 초"; f8 은 Lambda 후보에 `unknown`(CP.websocket) 이 있고 recommended 가 아님.
- [ ] **Step 3: QA 노트** — 항목별(beat, 코드 경로 저장소, sleep A2, 웹소켓 unknown) 전후 비교 한 줄씩과 위 표.
- [ ] **Step 4: README** — deploy_units 코드 경로 저장소, A2 sleep 시그니처, S4 unknown/unverified 를 한 줄씩.
- [ ] **Step 5: 전체 테스트 + lint** → 커밋 `Add QA repro fixtures (celery+redis, socket.io) and document QA follow-up` + trailer.
