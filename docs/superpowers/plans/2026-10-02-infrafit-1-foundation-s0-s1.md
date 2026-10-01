# infrafit 계획 1: 기반 + S0 접수 + S1 인벤토리 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 저장소 하나를 받아 `intake.json`(S0)과 `inventory.json`(S1)을 스키마에 맞게 결정적으로 만들어 내는 `infrafit analyze --until S1` 명령을 만든다.

**Architecture:** S1은 판단 없이 "무엇이 있는가"만 기록한다. 탐지 지식(구성 요소 ID 목록, 탐지 시그니처, 기본값 표)은 코드가 아니라 `knowledge/` 아래 YAML에 두고, 코드는 그것을 해석한다. 모든 단계 출력은 `schemas/infrafit.schema.json`으로 검증한 뒤에 쓰고, 단계가 끝나면 일관성 검사기가 단계 사이 참조를 검사한다.

**Tech Stack:** Python 3.12, uv, PyYAML, jsonschema, python-hcl2, pytest

**Spec:** `docs/superpowers/specs/2026-10-01-infrafit-design.md` (§3 지식 베이스, §4 워크플로 개요, §5 S0, §6 S1, §15 결과 JSON·일관성 검사, §18 테스트)

## 이 계획의 범위

설계 문서 §19의 M1 중 **S0·S1과 그 기반**만 다룬다.

| 이 계획 | 다음 계획으로 미룬 것 |
|---|---|
| 프로젝트 골격, 스키마 검증, 단계 출력 쓰기와 캐시 | 계획 2: S2 프로필(탐지기 + LLM 추론 + 가정, `candidate` 사실 확정) |
| S0 접수 | 계획 3: 능력 지식 베이스 YAML 변환(226개 구성 요소), 요구 조건 변환표, S3 적합성, S4 추천, 분석·추천 리포트 |
| S1 인벤토리: 워크로드, 엔드포인트, 데이터 범위, 현재 구성 요소, 기존 산출물, 기본값 사실, 요청 경로, 미매핑 | |
| S1이 쓰는 지식: 구성 요소 ID 목록(능력 값 없이), 탐지 시그니처, 기본값 표 | |
| S0~S1 일관성 검사, 픽스처 F1~F6, 골든 테스트, 단계별 예시 | |

## Global Constraints

- Python `>=3.12`, 패키지와 실행은 uv(`uv run …`).
- 스키마의 단일 출처는 `schemas/infrafit.schema.json`(JSON Schema 2020-12). 단계 출력은 이 파일의 `$defs`(`Intake`, `Inventory`)로 검증을 통과해야만 파일로 쓴다.
- 구성 요소 ID 형식: `^(cp|ds|ca|qu|sc|rt|fs|nw):[a-z0-9._-]+/[a-z0-9._-]+/[a-z0-9._-]+$`. 출력에 나오는 구성 요소 ID는 `unmapped`, `pending`을 빼고 모두 `knowledge/components/catalog.yaml`에 있어야 한다.
- 범위 ID 형식: `^(w|ep|ds|svc|path)-[a-z0-9._-]+$`.
- 근거(`Evidence`)의 `path`는 저장소 기준 상대 경로(POSIX 구분자)이고, `snippet`은 그 줄의 원문(앞뒤 공백 제거, 최대 200자)이다.
- S0·S1은 결정적이다. 같은 입력이면 `meta`를 뺀 출력이 바이트 단위로 같아야 한다. 출력 목록은 모두 정렬해서 쓴다.
- S1은 판단하지 않는다. 판단이 필요한 사실은 `status: candidate`로 낸다(설계 §6).
- 네트워크 접근은 GitHub URL 입력 시 `git clone`뿐이다.
- 문서와 코드 주석은 한국어, 커밋 메시지는 영어. 커밋 메시지 끝에 `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`.

## 파일 구조

```
one-click-deploy-agent/
  pyproject.toml
  .gitignore
  infrafit/
    __init__.py               버전
    cli.py                    argparse 진입점: analyze, kb lint, check-run
    schema.py                 스키마 로드와 $defs 단위 검증
    run.py                    RunContext(실행 디렉터리, 단계 출력 쓰기, 캐시), input_hash, now_iso
    repo.py                   Snapshot(파일 목록, 읽기, glob), open_snapshot, language_ratios
    evidence.py               evidence(), line_of(), grep_lines()
    kb.py                     knowledge/ 로더: catalog, signatures, defaults, watchlist, kb_version
    kb_lint.py                knowledge/ 형식 검사
    pipeline.py               analyze(): 단계 실행 순서
    consistency.py            S0~S1 일관성 검사
    stages/
      __init__.py
      s0_intake.py
      s1_inventory.py
    detect/
      __init__.py
      manifests.py            package.json, requirements*.txt, pyproject.toml, Procfile
      artifacts.py            Dockerfile, compose, k8s(원문 + kustomize 렌더링), Terraform, 플랫폼 설정, CI 파서
      defaults.py             기본값 사실 적용, 구간(hop) 기본값
      signatures.py           시그니처 매칭
      workloads.py            워크로드 찾기(k8s > compose > 코드)
      endpoints.py            엔드포인트 찾기(Python AST, Django, Express, Next.js)
      components.py           데이터 범위, 현재 구성 요소, 호스팅 정교화, 미매핑
      paths.py                요청 경로
  knowledge/
    components/catalog.yaml
    signatures/datastores.yaml  cache.yaml  queue.yaml  scheduler.yaml  realtime.yaml  files.yaml  watchlist.yaml
    defaults.yaml
  fixtures/
    f1-simple-web-app/  (simple-web-app develop@6050701 스냅샷) + expected.yaml
    f2-sqlite-erp/  f3-vibe-shop/  f4-overbuilt-internal/  f5-small-blog/  f6-long-jobs/  (각각 expected.yaml)
    */golden/intake.json, inventory.json
  schemas/examples/f2-sqlite-erp/intake.json, inventory.json
  scripts/export_f1.sh, update_golden.py
  tests/
```

---

### Task 1: 프로젝트 골격과 CLI 진입점

**Files:**
- Create: `pyproject.toml`, `.gitignore`, `infrafit/__init__.py`, `infrafit/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Produces: `infrafit.cli.main(argv: list[str] | None = None) -> int`, `infrafit.cli.build_parser() -> argparse.ArgumentParser`. 하위 명령은 `sub.add_parser(...)` 후 `set_defaults(func=...)`로 등록하고, `main`은 `args.func(args)`의 반환값을 종료 코드로 쓴다.

- [ ] **Step 1: 프로젝트 파일 작성**

`pyproject.toml`:
```toml
[project]
name = "infrafit"
version = "0.1.0"
description = "앱 저장소를 읽고 필요한 만큼의 인프라를 판정하는 진단 엔진"
requires-python = ">=3.12"
dependencies = [
  "jsonschema>=4.23",
  "pyyaml>=6.0",
  "python-hcl2>=4.3",
]

[project.scripts]
infrafit = "infrafit.cli:main"

[dependency-groups]
dev = ["pytest>=8.3"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["infrafit"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

`.gitignore`:
```
.venv/
__pycache__/
.pytest_cache/
out/
```

`infrafit/__init__.py`:
```python
"""infrafit: 앱 저장소를 읽고 필요한 만큼의 인프라를 판정한다."""

__version__ = "0.1.0"
```

- [ ] **Step 2: 실패하는 테스트 작성**

`tests/test_cli.py`:
```python
import pytest

from infrafit.cli import main


def test_version_prints_and_exits_zero(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert "infrafit 0.1.0" in capsys.readouterr().out


def test_no_command_prints_help(capsys):
    assert main([]) == 0
    assert "usage: infrafit" in capsys.readouterr().out
```

- [ ] **Step 3: 테스트가 실패하는지 확인**

Run: `uv run pytest tests/test_cli.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'infrafit.cli'`)

- [ ] **Step 4: CLI 구현**

`infrafit/cli.py`:
```python
"""infrafit 명령줄 진입점."""

from __future__ import annotations

import argparse

from infrafit import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="infrafit")
    parser.add_argument("--version", action="version", version=f"infrafit {__version__}")
    parser.add_subparsers(dest="command")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "func", None) is None:
        parser.print_help()
        return 0
    return args.func(args)
```

- [ ] **Step 5: 테스트 통과 확인**

Run: `uv run pytest tests/test_cli.py -v`
Expected: PASS (2 passed)

- [ ] **Step 6: 커밋**

```bash
git add pyproject.toml uv.lock .gitignore infrafit/__init__.py infrafit/cli.py tests/test_cli.py
git commit -m "feat: scaffold infrafit package and CLI entry point"
```

---

### Task 2: 스키마 검증과 단계 출력 쓰기

**Files:**
- Create: `infrafit/schema.py`, `infrafit/run.py`
- Test: `tests/test_schema.py`, `tests/test_run.py`

**Interfaces:**
- Produces:
  - `infrafit.schema.SchemaError(ValueError)`
  - `infrafit.schema.validate(def_name: str, data: dict) -> None` — `$defs/<def_name>`로 검증, 실패 시 `SchemaError`(경로와 메시지 최대 10개)
  - `infrafit.run.now_iso() -> str` (UTC, `YYYY-MM-DDTHH:MM:SSZ`)
  - `infrafit.run.input_hash(*parts) -> str` (`sha256:` + hex, `json.dumps(parts, sort_keys=True, default=str)` 기준)
  - `infrafit.run.code_version() -> str` — `infrafit/` 아래 모든 `.py` 내용의 sha256 앞 12자리. 단계 입력 해시에 넣어서, 코드가 바뀌면 캐시가 무효가 되게 한다
  - `infrafit.run.STAGES: dict[str, tuple[str, str]]` — 단계 → (파일 이름, `$defs` 이름). 이 계획에서는 `{"S0": ("intake", "Intake"), "S1": ("inventory", "Inventory")}`
  - `infrafit.run.RunContext` — 필드 `run_id: str`, `out_dir: Path`, `cache_dir: Path`; `RunContext.create(out_root: Path, run_id: str | None = None) -> RunContext`; `write_stage(stage, body, input_hash, started_at) -> dict`(meta를 붙여 검증 후 `<out_dir>/<파일 이름>.json`과 캐시에 쓰고 전체 데이터를 반환); `cached(stage, input_hash) -> dict | None`(캐시에 있으면 meta를 이번 실행으로 바꿔 반환)

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_schema.py`:
```python
import pytest

from infrafit.schema import SchemaError, validate

META = {"run_id": "r1", "stage": "S0", "input_hash": "sha256:x"}


def test_valid_intake_passes():
    validate("Intake", {
        "meta": META, "repo": "x", "commit": "abc", "files_total": 1,
        "files_scanned": 1, "excluded": [], "languages": {"python": 1.0},
    })


def test_missing_field_raises_with_path():
    with pytest.raises(SchemaError) as exc:
        validate("Intake", {"meta": META, "repo": "x"})
    assert "Intake" in str(exc.value)
    assert "commit" in str(exc.value)


def test_unknown_def_raises():
    with pytest.raises(SchemaError):
        validate("NoSuchDef", {})
```

`tests/test_run.py`:
```python
import json

import pytest

from infrafit.run import RunContext, code_version, input_hash, now_iso
from infrafit.schema import SchemaError

BODY = {"repo": "x", "commit": "abc", "files_total": 1, "files_scanned": 1,
        "excluded": [], "languages": {}, "overrides": None}


def test_input_hash_is_stable_and_prefixed():
    assert input_hash("S0", "abc") == input_hash("S0", "abc")
    assert input_hash("S0", "abc") != input_hash("S0", "abd")
    assert input_hash("S0").startswith("sha256:")


def test_code_version_is_short_hash():
    assert len(code_version()) == 12


def test_write_stage_validates_and_writes(tmp_path):
    ctx = RunContext.create(tmp_path, run_id="r1")
    data = ctx.write_stage("S0", BODY, input_hash="sha256:h", started_at=now_iso())
    written = json.loads((tmp_path / "r1" / "intake.json").read_text())
    assert written == data
    assert written["meta"]["stage"] == "S0"
    assert written["meta"]["run_id"] == "r1"


def test_write_stage_rejects_invalid_body(tmp_path):
    ctx = RunContext.create(tmp_path, run_id="r1")
    with pytest.raises(SchemaError):
        ctx.write_stage("S0", {"repo": "x"}, input_hash="sha256:h", started_at=now_iso())
    assert not (tmp_path / "r1" / "intake.json").exists()


def test_cache_returns_body_with_new_meta(tmp_path):
    first = RunContext.create(tmp_path, run_id="r1")
    first.write_stage("S0", BODY, input_hash="sha256:h", started_at=now_iso())
    second = RunContext.create(tmp_path, run_id="r2")
    hit = second.cached("S0", "sha256:h")
    assert hit is not None
    assert hit["meta"]["run_id"] == "r2"
    assert hit["commit"] == "abc"
    assert second.cached("S0", "sha256:other") is None
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `uv run pytest tests/test_schema.py tests/test_run.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: 구현**

`infrafit/schema.py`:
```python
"""schemas/infrafit.schema.json으로 단계 출력을 검증한다."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import jsonschema

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "infrafit.schema.json"


class SchemaError(ValueError):
    """단계 출력이 스키마를 통과하지 못했다."""


@lru_cache(maxsize=1)
def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validate(def_name: str, data: dict) -> None:
    schema = _schema()
    if def_name not in schema["$defs"]:
        raise SchemaError(f"{def_name}: $defs에 없는 정의")
    sub = {"$schema": schema["$schema"], "$defs": schema["$defs"], "$ref": f"#/$defs/{def_name}"}
    validator = jsonschema.Draft202012Validator(sub, format_checker=jsonschema.FormatChecker())
    errors = sorted(validator.iter_errors(data), key=lambda e: [str(p) for p in e.path])
    if errors:
        parts = [f"{'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}" for e in errors[:10]]
        raise SchemaError(f"{def_name}: " + "; ".join(parts))
```

`infrafit/run.py`:
```python
"""실행 디렉터리, 단계 출력 쓰기, 입력 해시 캐시."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from infrafit.schema import validate

STAGES: dict[str, tuple[str, str]] = {
    "S0": ("intake", "Intake"),
    "S1": ("inventory", "Inventory"),
}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def input_hash(*parts) -> str:
    raw = json.dumps(parts, sort_keys=True, default=str, ensure_ascii=False)
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


@lru_cache(maxsize=1)
def code_version() -> str:
    pkg = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    for path in sorted(pkg.rglob("*.py")):
        digest.update(path.relative_to(pkg).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()[:12]


def dump_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


@dataclass
class RunContext:
    run_id: str
    out_dir: Path
    cache_dir: Path

    @classmethod
    def create(cls, out_root: Path, run_id: str | None = None) -> "RunContext":
        rid = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_dir = out_root / rid
        out_dir.mkdir(parents=True, exist_ok=True)
        cache_dir = out_root / ".cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cls(run_id=rid, out_dir=out_dir, cache_dir=cache_dir)

    def _meta(self, stage: str, input_hash: str, started_at: str) -> dict:
        return {"run_id": self.run_id, "stage": stage, "input_hash": input_hash,
                "started_at": started_at, "finished_at": now_iso()}

    def write_stage(self, stage: str, body: dict, input_hash: str, started_at: str) -> dict:
        name, def_name = STAGES[stage]
        data = {"meta": self._meta(stage, input_hash, started_at), **body}
        validate(def_name, data)
        text = dump_json(data)
        (self.out_dir / f"{name}.json").write_text(text, encoding="utf-8")
        cache_file = self.cache_dir / stage / (input_hash.replace(":", "-") + ".json")
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(text, encoding="utf-8")
        return data

    def cached(self, stage: str, input_hash: str) -> dict | None:
        cache_file = self.cache_dir / stage / (input_hash.replace(":", "-") + ".json")
        if not cache_file.exists():
            return None
        data = json.loads(cache_file.read_text(encoding="utf-8"))
        started = now_iso()
        data["meta"] = self._meta(stage, input_hash, started)
        name, _ = STAGES[stage]
        (self.out_dir / f"{name}.json").write_text(dump_json(data), encoding="utf-8")
        return data
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `uv run pytest tests/test_schema.py tests/test_run.py -v`
Expected: PASS (8 passed)

- [ ] **Step 5: 커밋**

```bash
git add infrafit/schema.py infrafit/run.py tests/test_schema.py tests/test_run.py
git commit -m "feat: validate stage outputs against schema and cache by input hash"
```

---

### Task 3: 저장소 스냅샷, 근거, S0 접수

**Files:**
- Create: `infrafit/repo.py`, `infrafit/evidence.py`, `infrafit/stages/__init__.py`, `infrafit/stages/s0_intake.py`, `infrafit/pipeline.py`
- Modify: `infrafit/cli.py` (`analyze` 하위 명령)
- Test: `tests/test_repo.py`, `tests/test_s0.py`

**Interfaces:**
- Consumes: `RunContext`, `input_hash`, `now_iso` (Task 2)
- Produces:
  - `infrafit.repo.match_glob(path: str, pattern: str) -> bool` — `fnmatch` 기준, `**/`로 시작하는 패턴은 루트 파일에도 맞음
  - `infrafit.repo.Snapshot` — 필드 `root: Path`, `repo: str`, `commit: str`, `files: list[str]`(분석 대상 텍스트 파일, 정렬), `files_total: int`, `excluded: list[str]`; 메서드 `read(rel) -> str`, `lines(rel) -> list[str]`, `glob(pattern) -> list[str]`, `exists(rel) -> bool`
  - `infrafit.repo.open_snapshot(source: str, workdir: Path) -> Snapshot`
  - `infrafit.repo.language_ratios(files: list[str]) -> dict[str, float]`
  - `infrafit.evidence.evidence(snap, rel, line=None, kind=None) -> dict`
  - `infrafit.evidence.line_of(snap, rel, needle: str) -> int | None` (부분 문자열이 처음 나오는 줄)
  - `infrafit.evidence.grep_lines(snap, rel, pattern: str, flags: int = 0) -> list[int]`
  - `infrafit.stages.s0_intake.run_s0(ctx: RunContext, snap: Snapshot) -> dict`
  - `infrafit.pipeline.analyze(source: str, out_root: Path, until: str = "S1", run_id: str | None = None) -> RunContext`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_repo.py`:
```python
from infrafit.evidence import evidence, grep_lines, line_of
from infrafit.repo import language_ratios, match_glob, open_snapshot


def _make(tmp_path):
    (tmp_path / "app.py").write_text("import sqlite3\nconn = sqlite3.connect('x.db')\n")
    (tmp_path / "web").mkdir()
    (tmp_path / "web" / "index.ts").write_text("export const a = 1\n")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "x.js").write_text("x\n")
    (tmp_path / "logo.png").write_bytes(b"\x89PNG")
    return open_snapshot(str(tmp_path), tmp_path / "_work")


def test_match_glob_handles_root_and_nested():
    assert match_glob("package.json", "**/package.json")
    assert match_glob("a/b/package.json", "**/package.json")
    assert match_glob("app/api/x/route.ts", "**/app/**/route.ts")
    assert not match_glob("app/api/x/page.ts", "**/app/**/route.ts")


def test_snapshot_excludes_dirs_and_binaries(tmp_path):
    snap = _make(tmp_path)
    assert snap.files == ["app.py", "web/index.ts"]
    assert snap.excluded == ["node_modules/"]
    assert snap.files_total == 3
    assert snap.commit.startswith("tree-")


def test_commit_is_deterministic(tmp_path):
    assert _make(tmp_path).commit == open_snapshot(str(tmp_path), tmp_path / "_w2").commit


def test_language_ratios():
    assert language_ratios(["a.py", "b.py", "c.ts", "README.md"]) == {"python": 0.667, "typescript": 0.333}


def test_evidence_and_search(tmp_path):
    snap = _make(tmp_path)
    assert line_of(snap, "app.py", "sqlite3.connect") == 2
    assert grep_lines(snap, "app.py", r"sqlite3") == [1, 2]
    ev = evidence(snap, "app.py", 2, kind="tech")
    assert ev == {"path": "app.py", "line": 2, "snippet": "conn = sqlite3.connect('x.db')", "kind": "tech"}
    assert evidence(snap, "app.py") == {"path": "app.py", "line": None, "snippet": "app.py"}
```

`tests/test_s0.py`:
```python
import json

from infrafit.pipeline import analyze


def test_analyze_until_s0_writes_valid_intake(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "main.py").write_text("print('hi')\n")
    (repo / "infrafit.yaml").write_text("assumptions:\n  D2.baseline_concurrency: 200\n")
    ctx = analyze(str(repo), tmp_path / "out", until="S0", run_id="r1")
    intake = json.loads((ctx.out_dir / "intake.json").read_text())
    assert intake["files_scanned"] == 2
    assert intake["languages"] == {"python": 1.0}
    assert intake["overrides"] == {"assumptions": {"D2.baseline_concurrency": 200}}
    assert intake["meta"]["stage"] == "S0"
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `uv run pytest tests/test_repo.py tests/test_s0.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: 구현**

`infrafit/repo.py`:
```python
"""저장소 스냅샷: 분석 대상 파일 목록과 읽기."""

from __future__ import annotations

import fnmatch
import hashlib
import os
import subprocess
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

EXCLUDED_DIRS = frozenset({
    ".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".next",
    ".nuxt", "vendor", ".terraform", "coverage", ".pytest_cache", ".mypy_cache", "out",
})
BINARY_EXTS = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp", ".pdf", ".zip", ".gz", ".tgz",
    ".woff", ".woff2", ".ttf", ".eot", ".db", ".sqlite", ".sqlite3", ".mp4", ".mp3",
})
MAX_TEXT_BYTES = 1_000_000
LANG_BY_EXT = {
    ".py": "python", ".ts": "typescript", ".tsx": "typescript", ".js": "javascript",
    ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript", ".go": "go",
    ".java": "java", ".kt": "kotlin", ".rb": "ruby", ".php": "php", ".rs": "rust",
    ".cs": "csharp",
}


def match_glob(path: str, pattern: str) -> bool:
    if fnmatch.fnmatchcase(path, pattern):
        return True
    return pattern.startswith("**/") and fnmatch.fnmatchcase(path, pattern[3:])


@dataclass
class Snapshot:
    root: Path
    repo: str
    commit: str
    files: list[str]
    files_total: int
    excluded: list[str]
    _cache: dict[str, str] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self._fileset = set(self.files)

    def read(self, rel: str) -> str:
        if rel not in self._cache:
            self._cache[rel] = (self.root / rel).read_text(encoding="utf-8", errors="replace")
        return self._cache[rel]

    def lines(self, rel: str) -> list[str]:
        return self.read(rel).splitlines()

    def glob(self, pattern: str) -> list[str]:
        return [f for f in self.files if match_glob(f, pattern)]

    def exists(self, rel: str) -> bool:
        return rel in self._fileset


def _walk(root: Path) -> tuple[list[str], list[str], int]:
    files: list[str] = []
    excluded: list[str] = []
    total = 0
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = Path(dirpath).relative_to(root).as_posix()
        keep = []
        for d in sorted(dirnames):
            if d in EXCLUDED_DIRS:
                excluded.append(f"{d}/" if rel_dir == "." else f"{rel_dir}/{d}/")
            else:
                keep.append(d)
        dirnames[:] = keep
        for name in sorted(filenames):
            total += 1
            path = Path(dirpath) / name
            if path.suffix.lower() in BINARY_EXTS or path.stat().st_size > MAX_TEXT_BYTES:
                continue
            files.append(path.relative_to(root).as_posix())
    return sorted(files), sorted(excluded), total


def _commit(root: Path, files: list[str]) -> str:
    try:
        top = subprocess.run(["git", "-C", str(root), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, check=True).stdout.strip()
        if Path(top).resolve() == root.resolve():
            return subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                                  capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    digest = hashlib.sha256()
    for rel in files:
        digest.update(rel.encode("utf-8"))
        digest.update(hashlib.sha256((root / rel).read_bytes()).digest())
    return "tree-" + digest.hexdigest()[:16]


def open_snapshot(source: str, workdir: Path) -> Snapshot:
    if source.startswith(("https://", "http://", "git@")):
        dest = workdir / "source"
        if not dest.exists():
            workdir.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "clone", "--depth", "1", source, str(dest)],
                           capture_output=True, check=True)
        root, repo = dest, source
    else:
        root = Path(source).resolve()
        if not root.is_dir():
            raise FileNotFoundError(f"저장소 경로가 없음: {source}")
        repo = str(root)
    files, excluded, total = _walk(root)
    # 작업 디렉터리가 저장소 안에 있으면 분석 대상에서 뺀다.
    try:
        work_rel = workdir.resolve().relative_to(root).as_posix() + "/"
        files = [f for f in files if not f.startswith(work_rel)]
    except ValueError:
        pass
    return Snapshot(root=root, repo=repo, commit=_commit(root, files), files=files,
                    files_total=total, excluded=excluded)


def language_ratios(files: list[str]) -> dict[str, float]:
    counts = Counter(LANG_BY_EXT[Path(f).suffix.lower()] for f in files
                     if Path(f).suffix.lower() in LANG_BY_EXT)
    total = sum(counts.values())
    return {k: round(v / total, 3) for k, v in sorted(counts.items())} if total else {}
```

> 테스트에서 넘기는 작업 디렉터리(`tmp_path / "_work"`)는 로컬 경로 입력일 때 만들어지지 않으므로 파일 목록에 영향이 없다. 그래서 `files_total == 3`(app.py, web/index.ts, logo.png)이다. 실제 실행에서는 작업 디렉터리가 `out/<run-id>`이고, 저장소 안에 있으면 분석 대상에서 빠진다.

`infrafit/evidence.py`:
```python
"""근거(Evidence) 만들기와 줄 검색."""

from __future__ import annotations

import re

from infrafit.repo import Snapshot


def evidence(snap: Snapshot, rel: str, line: int | None = None, kind: str | None = None) -> dict:
    snippet = rel
    if line is not None:
        lines = snap.lines(rel)
        if 0 < line <= len(lines):
            snippet = lines[line - 1].strip()[:200] or rel
    ev = {"path": rel, "line": line, "snippet": snippet}
    if kind:
        ev["kind"] = kind
    return ev


def line_of(snap: Snapshot, rel: str, needle: str) -> int | None:
    for i, text in enumerate(snap.lines(rel), 1):
        if needle in text:
            return i
    return None


def grep_lines(snap: Snapshot, rel: str, pattern: str, flags: int = 0) -> list[int]:
    rx = re.compile(pattern, flags)
    return [i for i, text in enumerate(snap.lines(rel), 1) if rx.search(text)]
```

`infrafit/stages/__init__.py`:
```python
"""워크플로 단계(S0~S9). 단계 하나 = 모듈 하나."""
```

`infrafit/stages/s0_intake.py`:
```python
"""S0 접수: 커밋 고정, 파일 범위, 언어 비율, 사용자 조정 파일."""

from __future__ import annotations

import yaml

from infrafit.repo import Snapshot, language_ratios
from infrafit.run import RunContext, code_version, input_hash, now_iso


def _overrides(snap: Snapshot) -> dict | None:
    if not snap.exists("infrafit.yaml"):
        return None
    data = yaml.safe_load(snap.read("infrafit.yaml"))
    return data if isinstance(data, dict) else None


def run_s0(ctx: RunContext, snap: Snapshot) -> dict:
    started = now_iso()
    overrides = _overrides(snap)
    body = {
        "repo": snap.repo,
        "commit": snap.commit,
        "files_total": snap.files_total,
        "files_scanned": len(snap.files),
        "excluded": snap.excluded,
        "languages": language_ratios(snap.files),
        "overrides": overrides,
    }
    return ctx.write_stage("S0", body, input_hash=input_hash("S0", snap.commit, overrides, code_version()),
                           started_at=started)
```

`infrafit/pipeline.py`:
```python
"""단계 실행 순서."""

from __future__ import annotations

from pathlib import Path

from infrafit.repo import open_snapshot
from infrafit.run import RunContext
from infrafit.stages.s0_intake import run_s0

ORDER = ["S0", "S1"]


def analyze(source: str, out_root: Path, until: str = "S1", run_id: str | None = None) -> RunContext:
    if until not in ORDER:
        raise ValueError(f"지원하지 않는 단계: {until}")
    ctx = RunContext.create(out_root, run_id)
    snap = open_snapshot(source, ctx.out_dir)
    run_s0(ctx, snap)
    return ctx
```

`infrafit/cli.py` 수정 — `build_parser`를 아래로 바꾼다:
```python
def _cmd_analyze(args: argparse.Namespace) -> int:
    from pathlib import Path

    from infrafit.pipeline import analyze

    ctx = analyze(args.source, Path(args.out), until=args.until, run_id=args.run_id)
    print(ctx.out_dir)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="infrafit")
    parser.add_argument("--version", action="version", version=f"infrafit {__version__}")
    sub = parser.add_subparsers(dest="command")

    analyze = sub.add_parser("analyze", help="저장소를 분석한다")
    analyze.add_argument("source", help="로컬 경로 또는 GitHub URL")
    analyze.add_argument("--out", default="out", help="실행 결과 디렉터리 루트")
    analyze.add_argument("--until", default="S1", help="이 단계까지 실행")
    analyze.add_argument("--run-id", default=None)
    analyze.set_defaults(func=_cmd_analyze)
    return parser
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `uv run pytest tests/ -v`
Expected: PASS (전체 통과)

- [ ] **Step 5: 커밋**

```bash
git add infrafit/repo.py infrafit/evidence.py infrafit/stages infrafit/pipeline.py infrafit/cli.py tests/test_repo.py tests/test_s0.py
git commit -m "feat: add repository snapshot, evidence helpers and S0 intake"
```

---

### Task 4: 픽스처 저장소와 기대 판정(엔진 실행 전 작성)

설계 원칙에 따라 기대 판정은 엔진을 만들기 전에 적고, 엔진 결과에 맞춰 고치지 않는다. 엔진 결과가 다르면 엔진을 고친다. 기대가 틀렸다고 판단되면 고치지 말고 멈춰서 보고한다.

**Files:**
- Create: `scripts/export_f1.sh`, `fixtures/<픽스처>/expected.yaml`, `fixtures/<픽스처>/repo/**`(F1은 스크립트로 생성)

픽스처의 저장소 내용은 항상 `repo/` 아래에 두고, `expected.yaml`과 `golden/`은 그 바깥에 둔다. 기대 판정이나 골든 파일이 분석 대상에 섞이면 파일 수와 커밋 해시가 바뀌기 때문이다.

**Interfaces:**
- Produces: 각 픽스처 디렉터리와 `expected.yaml`. 형식은 아래 F2 예와 같고, Task 16의 테스트가 이 형식을 읽는다.
  - `repo_dir`: 분석할 저장소 디렉터리(픽스처 디렉터리 기준). 항상 `repo`
  - `match`: `exact`(목록이 정확히 같아야 함) 또는 `subset`(기대 항목이 모두 있으면 됨)
  - `workloads[]`: `{id, kind}`
  - `endpoints[]`: `{method, route}` (`exact`면 집합이 같아야 함)
  - `endpoint_workloads[]`(선택): `{path_contains, workload}` — 핸들러 파일 경로에 문자열이 들어간 엔드포인트 중 하나 이상이 그 워크로드에 배정됨
  - `datastores[]`: `{id, role, used_by?}` — `used_by`가 있으면 정확히 같아야 함
  - `current_components[]`: `{scope, component, status}` — 항상 subset
  - `artifacts[]`: `{kind, path, settings: {키: 값 또는 {value, defaulted}}}` — 항상 subset
  - `request_paths[]`: `{id, hops: [{kind, component, settings?}]}` — `hops`가 있으면 구간 순서와 종류·구성 요소가 정확히 같아야 함. `hops`를 생략하면 경로 존재만 확인
  - `unmapped[]`: 라벨 목록(`exact`면 같아야 함)

- [ ] **Step 1: F1 스냅샷 스크립트 작성과 실행**

`scripts/export_f1.sh`:
```bash
#!/usr/bin/env bash
# simple-web-app의 고정 커밋을 F1 픽스처로 내보낸다.
set -euo pipefail
COMMIT="${1:-6050701}"
SRC="${SIMPLE_WEB_APP:-../simple-web-app}"
DEST="fixtures/f1-simple-web-app/repo"
rm -rf "$DEST"
mkdir -p "$DEST"
git -C "$SRC" archive "$COMMIT" | tar -x -C "$DEST"
echo "$COMMIT" > fixtures/f1-simple-web-app/SOURCE
```

Run: `chmod +x scripts/export_f1.sh && ./scripts/export_f1.sh`
Expected: `fixtures/f1-simple-web-app/repo/k8s/base/auth.yaml`이 생기고 `SOURCE`에 `6050701`

- [ ] **Step 2: F1 기대 판정**

`fixtures/f1-simple-web-app/expected.yaml`:
```yaml
written_at: "2026-10-02"
note: 엔진 실행 전에 작성. simple-web-app develop@6050701
repo_dir: repo
match: subset
workloads:
  - {id: w-nginx, kind: web}
  - {id: w-auth, kind: web}
  - {id: w-auth-verify, kind: web}
  - {id: w-board-api, kind: web}
  - {id: w-board-worker, kind: worker}
  - {id: w-db-migrate, kind: migration-job}
workloads_exact: true
endpoint_workloads:
  - {path_contains: services/auth/, workload: w-auth}
  - {path_contains: services/board/, workload: w-board-api}
datastores:
  - {id: ds-postgresql, role: primary-db, used_by: [w-auth, w-auth-verify, w-board-api, w-board-worker, w-db-migrate]}
  - {id: svc-redis, role: cache, used_by: [w-auth, w-auth-verify, w-board-api, w-board-worker, w-db-migrate]}
  - {id: svc-redis-streams, role: queue, used_by: [w-auth, w-auth-verify, w-board-api, w-board-worker, w-db-migrate]}
current_components:
  - {scope: ds-postgresql, component: "ds:unspecified/postgresql/default", status: confirmed}
  - {scope: svc-redis, component: "ca:unspecified/redis/default", status: confirmed}
  - {scope: w-auth, component: "cp:k8s/deployment/unspecified-cluster", status: confirmed}
artifacts:
  - {kind: dockerfile, path: services/auth/Dockerfile, settings: {cmd: "uvicorn auth.main:app --host 0.0.0.0 --port 8000 --no-access-log"}}
  - {kind: compose, path: docker-compose.yml, settings: {}}
  - {kind: k8s, path: k8s/base/auth.yaml, settings: {"Deployment/auth.terminationGracePeriodSeconds": 30, "Deployment/auth.readinessProbe": true}}
  - {kind: ci, path: .github/workflows/ci.yml, settings: {}}
request_paths:
  - id: path-auth
    hops:
      - {kind: app-server, component: "nw:app/uvicorn/default", settings: {timeout_keep_alive: {value: 5, defaulted: true}}}
  - id: path-nginx
```

> simple-web-app의 base 매니페스트는 `terminationGracePeriodSeconds: 30`을 명시하므로 기본값이 아니라 명시 값으로 기대한다(6050701에서 확인). `k8s/components/`와 `k8s/overlays/`의 패치 파일에도 같은 이름의 Deployment가 있지만, 워크로드는 경로 순 첫 번째(base)를 쓴다.

- [ ] **Step 3: F2 sqlite-erp 작성**

`fixtures/f2-sqlite-erp/repo/README.md`:
```markdown
# 사내 결재 시스템

부서별 결재 요청을 올리고 팀장이 승인하는 사내 업무용 시스템입니다. 근무 시간에 전 직원이 사용합니다.
```

`fixtures/f2-sqlite-erp/repo/requirements.txt`:
```
flask==3.0.3
gunicorn==22.0.0
openpyxl==3.1.5
```

`fixtures/f2-sqlite-erp/repo/Procfile`:
```
web: gunicorn -w 4 -b 0.0.0.0:$PORT app:app
```

`fixtures/f2-sqlite-erp/repo/Dockerfile`:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV FLASK_APP=app.py
CMD ["flask", "run", "--host=0.0.0.0"]
```

`fixtures/f2-sqlite-erp/repo/schema.sql`:
```sql
CREATE TABLE departments (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT UNIQUE, department_id INTEGER, role TEXT);
CREATE TABLE approvals (id INTEGER PRIMARY KEY, doc_no TEXT, title TEXT, requester_id INTEGER, status TEXT);
CREATE TABLE counters (name TEXT PRIMARY KEY, n INTEGER NOT NULL);
```

`fixtures/f2-sqlite-erp/repo/db.py`:
```python
import sqlite3
import time

DB_PATH = "erp.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def execute_with_retry(sql, params=(), retries=5):
    for attempt in range(retries):
        try:
            conn = get_conn()
            with conn:
                return conn.execute(sql, params)
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < retries - 1:
                time.sleep(0.2 * (attempt + 1))
                continue
            raise
```

`fixtures/f2-sqlite-erp/repo/app.py`:
```python
import io
import os

from flask import Flask, request, send_file, session
from openpyxl import Workbook

from db import execute_with_retry, get_conn

app = Flask(__name__)
app.secret_key = "change-me"
UPLOAD_DIR = "uploads"


@app.route("/login", methods=["POST"])
def login():
    session["email"] = request.form["email"]
    return {"ok": True}


@app.get("/approvals")
def list_approvals():
    rows = get_conn().execute("SELECT * FROM approvals ORDER BY id DESC").fetchall()
    return {"items": [dict(r) for r in rows]}


@app.post("/approvals")
def create_approval():
    execute_with_retry("UPDATE counters SET n = n + 1 WHERE name = 'approval'")
    n = get_conn().execute("SELECT n FROM counters WHERE name = 'approval'").fetchone()["n"]
    execute_with_retry("INSERT INTO approvals (doc_no, title, status) VALUES (?, ?, 'pending')",
                       (f"AP-{n:06d}", request.json["title"]))
    return {"doc_no": f"AP-{n:06d}"}, 201


@app.post("/approvals/<int:approval_id>/approve")
def approve(approval_id):
    execute_with_retry("UPDATE approvals SET status = 'approved' WHERE id = ?", (approval_id,))
    return {"ok": True}


@app.get("/export")
def export():
    wb = Workbook()
    ws = wb.active
    for row in get_conn().execute("SELECT * FROM approvals"):
        ws.append(list(row))
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(buf, download_name="approvals.xlsx")


@app.post("/attachments")
def upload():
    f = request.files["file"]
    f.save(os.path.join(UPLOAD_DIR, f.filename))
    return {"ok": True}
```

`fixtures/f2-sqlite-erp/expected.yaml`:
```yaml
written_at: "2026-10-02"
note: 엔진 실행 전에 작성
repo_dir: repo
match: exact
workloads:
  - {id: w-web, kind: web}
endpoints:
  - {method: POST, route: /login}
  - {method: GET, route: /approvals}
  - {method: POST, route: /approvals}
  - {method: POST, route: "/approvals/<int:approval_id>/approve"}
  - {method: GET, route: /export}
  - {method: POST, route: /attachments}
datastores:
  - {id: ds-sqlite, role: primary-db}
  - {id: svc-container-disk, role: file-storage}
current_components:
  - {scope: ds-sqlite, component: "ds:local/sqlite/wal", status: confirmed}
  - {scope: svc-container-disk, component: "fs:local/container-disk/default", status: candidate}
  - {scope: w-web, component: "cp:docker/container/unspecified-host", status: confirmed}
artifacts:
  - kind: dockerfile
    path: Dockerfile
    settings:
      cmd: "flask run --host=0.0.0.0"
      user: {value: root, defaulted: true}
request_paths:
  - id: path-web
    hops:
      - {kind: app-server, component: "nw:app/flask-dev/default"}
unmapped: []
```

- [ ] **Step 4: F3 vibe-shop 작성**

`fixtures/f3-vibe-shop/repo/package.json`:
```json
{
  "name": "vibe-shop",
  "private": true,
  "scripts": { "dev": "next dev", "build": "next build", "start": "next start" },
  "dependencies": {
    "better-sqlite3": "^11.3.0",
    "next": "15.0.0",
    "react": "19.0.0",
    "react-dom": "19.0.0",
    "stripe": "^17.0.0"
  }
}
```

`fixtures/f3-vibe-shop/repo/vercel.json`:
```json
{ "regions": ["iad1"] }
```

`fixtures/f3-vibe-shop/repo/lib/db.ts`:
```ts
import Database from "better-sqlite3";

export const db = new Database("shop.db");
```

`fixtures/f3-vibe-shop/repo/lib/session.ts`:
```ts
const sessions = new Map<string, { userId: string }>();

export function getSession(id: string) {
  return sessions.get(id);
}

export function setSession(id: string, userId: string) {
  sessions.set(id, { userId });
}
```

`fixtures/f3-vibe-shop/repo/app/page.tsx`:
```tsx
export default function Home() {
  return <main>Vibe Shop</main>;
}
```

`fixtures/f3-vibe-shop/repo/app/api/products/route.ts`:
```ts
import { db } from "@/lib/db";

export async function GET() {
  const rows = db.prepare("SELECT * FROM products").all();
  return Response.json(rows);
}
```

`fixtures/f3-vibe-shop/repo/app/api/checkout/route.ts`:
```ts
import Stripe from "stripe";
import { db } from "@/lib/db";

const stripe = new Stripe(process.env.STRIPE_KEY!);

export async function POST(req: Request) {
  const { productId } = await req.json();
  const p = db.prepare("SELECT stock, price FROM products WHERE id = ?").get(productId) as any;
  if (p.stock > 0) {
    db.prepare("UPDATE products SET stock = stock - 1 WHERE id = ?").run(productId);
  }
  const intent = await stripe.paymentIntents.create({ amount: p.price, currency: "krw" });
  return Response.json({ clientSecret: intent.client_secret });
}
```

`fixtures/f3-vibe-shop/repo/app/api/webhooks/stripe/route.ts`:
```ts
import { db } from "@/lib/db";

export async function POST(req: Request) {
  const event = await req.json();
  if (event.type === "payment_intent.succeeded") {
    db.prepare("INSERT INTO orders (intent_id) VALUES (?)").run(event.data.object.id);
  }
  return new Response("ok");
}
```

`fixtures/f3-vibe-shop/repo/app/api/upload/route.ts`:
```ts
import { writeFile } from "fs/promises";
import path from "path";

export async function POST(req: Request) {
  const form = await req.formData();
  const file = form.get("file") as File;
  await writeFile(path.join(process.cwd(), "public/uploads", file.name), Buffer.from(await file.arrayBuffer()));
  return Response.json({ ok: true });
}
```

`fixtures/f3-vibe-shop/expected.yaml`:
```yaml
written_at: "2026-10-02"
note: 엔진 실행 전에 작성
repo_dir: repo
match: exact
workloads:
  - {id: w-web, kind: web}
endpoints:
  - {method: GET, route: /api/products}
  - {method: POST, route: /api/checkout}
  - {method: POST, route: /api/webhooks/stripe}
  - {method: POST, route: /api/upload}
datastores:
  - {id: ds-sqlite, role: primary-db}
  - {id: svc-process-memory, role: session}
  - {id: svc-container-disk, role: file-storage}
current_components:
  - {scope: ds-sqlite, component: "ds:local/sqlite/default", status: confirmed}
  - {scope: svc-process-memory, component: "ca:local/process-memory/default", status: candidate}
  - {scope: svc-container-disk, component: "fs:local/container-disk/default", status: candidate}
  - {scope: w-web, component: "cp:vercel/functions/unspecified-plan", status: confirmed}
artifacts:
  - {kind: platform-config, path: vercel.json, settings: {regions: [iad1]}}
request_paths:
  - id: path-web
    hops:
      - {kind: edge-proxy, component: "nw:vercel/edge-proxy/default"}
unmapped: []
```

- [ ] **Step 5: F4 overbuilt-internal 작성**

`fixtures/f4-overbuilt-internal/repo/README.md`:
```markdown
# internal-reports

사내 리포트 조회 도구. SSO로 로그인한 직원만 사용합니다.
```

`fixtures/f4-overbuilt-internal/repo/package.json`:
```json
{
  "name": "internal-reports",
  "private": true,
  "scripts": { "start": "node index.js" },
  "dependencies": { "express": "^4.21.0", "pg": "^8.13.0" }
}
```

`fixtures/f4-overbuilt-internal/repo/index.js`:
```js
const express = require("express");
const { Pool } = require("pg");

const app = express();
const pool = new Pool({ connectionString: process.env.DATABASE_URL });

app.get("/health", (req, res) => res.send("ok"));

app.get("/reports", async (req, res) => {
  const { rows } = await pool.query("SELECT * FROM reports ORDER BY created_at DESC LIMIT 50");
  res.json(rows);
});

app.listen(process.env.PORT || 3000);
```

`fixtures/f4-overbuilt-internal/repo/k8s/deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: internal-reports
spec:
  replicas: 3
  selector:
    matchLabels: { app: internal-reports }
  template:
    metadata:
      labels: { app: internal-reports }
    spec:
      containers:
        - name: app
          image: 123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/internal-reports:1.0.0
          command: ["node", "index.js"]
          ports:
            - containerPort: 3000
```

`fixtures/f4-overbuilt-internal/repo/k8s/ingress.yaml`:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: internal-reports
spec:
  ingressClassName: alb
  rules:
    - http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: internal-reports
                port:
                  number: 80
```

`fixtures/f4-overbuilt-internal/repo/terraform/main.tf`:
```hcl
provider "aws" {
  region = "ap-northeast-2"
}

provider "aws" {
  alias  = "us"
  region = "us-east-1"
}

resource "aws_eks_cluster" "main" {
  name     = "internal"
  role_arn = "arn:aws:iam::123456789012:role/eks"
  vpc_config {
    subnet_ids = ["subnet-a", "subnet-b", "subnet-c"]
  }
}

resource "aws_nat_gateway" "a" {
  subnet_id = "subnet-a"
}

resource "aws_nat_gateway" "b" {
  subnet_id = "subnet-b"
}

resource "aws_nat_gateway" "c" {
  subnet_id = "subnet-c"
}

resource "aws_db_instance" "main" {
  engine                  = "postgres"
  instance_class          = "db.r6g.large"
  multi_az                = true
  backup_retention_period = 7
}

resource "aws_db_instance" "replica_us" {
  provider            = aws.us
  replicate_source_db = "main"
  instance_class      = "db.r6g.large"
}
```

`fixtures/f4-overbuilt-internal/expected.yaml`:
```yaml
written_at: "2026-10-02"
note: 엔진 실행 전에 작성
repo_dir: repo
match: exact
workloads:
  - {id: w-internal-reports, kind: web}
endpoints:
  - {method: GET, route: /health}
  - {method: GET, route: /reports}
datastores:
  - {id: ds-postgresql, role: primary-db}
current_components:
  - {scope: ds-postgresql, component: "ds:aws/rds-postgres/multi-az-instance", status: confirmed}
  - {scope: w-internal-reports, component: "cp:aws/eks/unspecified", status: confirmed}
artifacts:
  - kind: terraform
    path: terraform/main.tf
    settings:
      aws_db_instance.main.multi_az: true
      aws_db_instance.main.storage_encrypted: {value: false, defaulted: true}
      provider.aws.us.region: us-east-1
  - kind: k8s
    path: k8s/ingress.yaml
    settings:
      Ingress/internal-reports.ingressClassName: alb
request_paths:
  - id: path-internal-reports
    hops:
      - {kind: load-balancer, component: "nw:aws/alb/default", settings: {idle_timeout: {value: 60, defaulted: true}}}
      - {kind: app-server, component: "nw:app/node-http/default", settings: {keep_alive_timeout: {value: 5, defaulted: true}}}
unmapped: []
```

- [ ] **Step 6: F5 small-blog 작성**

`fixtures/f5-small-blog/repo/package.json`:
```json
{
  "name": "small-blog",
  "private": true,
  "scripts": { "dev": "next dev", "build": "next build", "start": "next start" },
  "dependencies": {
    "@supabase/supabase-js": "^2.45.0",
    "next": "15.0.0",
    "react": "19.0.0",
    "react-dom": "19.0.0"
  }
}
```

`fixtures/f5-small-blog/repo/vercel.json`:
```json
{}
```

`fixtures/f5-small-blog/repo/lib/supabase.ts`:
```ts
import { createClient } from "@supabase/supabase-js";

export const supabase = createClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!);
```

`fixtures/f5-small-blog/repo/app/page.tsx`:
```tsx
import { supabase } from "@/lib/supabase";

export default async function Home() {
  const { data } = await supabase.from("posts").select("slug,title").order("created_at", { ascending: false });
  return <ul>{data?.map((p) => <li key={p.slug}>{p.title}</li>)}</ul>;
}
```

`fixtures/f5-small-blog/repo/app/posts/[slug]/page.tsx`:
```tsx
import { supabase } from "@/lib/supabase";

export default async function Post({ params }: { params: { slug: string } }) {
  const { data } = await supabase.from("posts").select("*").eq("slug", params.slug).single();
  return <article>{data?.body}</article>;
}
```

`fixtures/f5-small-blog/repo/app/api/revalidate/route.ts`:
```ts
import { revalidatePath } from "next/cache";

export async function POST() {
  revalidatePath("/");
  return Response.json({ ok: true });
}
```

`fixtures/f5-small-blog/expected.yaml`:
```yaml
written_at: "2026-10-02"
note: 엔진 실행 전에 작성
repo_dir: repo
match: exact
workloads:
  - {id: w-web, kind: web}
endpoints:
  - {method: POST, route: /api/revalidate}
datastores:
  - {id: ds-supabase-postgres, role: primary-db}
current_components:
  - {scope: ds-supabase-postgres, component: "ds:supabase/postgres/unspecified-plan", status: confirmed}
  - {scope: w-web, component: "cp:vercel/functions/unspecified-plan", status: confirmed}
artifacts:
  - {kind: platform-config, path: vercel.json, settings: {}}
request_paths:
  - id: path-web
    hops:
      - {kind: edge-proxy, component: "nw:vercel/edge-proxy/default"}
unmapped: []
```

- [ ] **Step 7: F6 long-jobs 작성**

`fixtures/f6-long-jobs/repo/package.json`:
```json
{
  "name": "long-jobs",
  "private": true,
  "scripts": { "dev": "next dev", "build": "next build", "start": "next start" },
  "dependencies": {
    "exceljs": "^4.4.0",
    "next": "15.0.0",
    "nodemailer": "^6.9.15",
    "pg": "^8.13.0",
    "react": "19.0.0",
    "react-dom": "19.0.0"
  }
}
```

`fixtures/f6-long-jobs/repo/vercel.json`:
```json
{ "functions": { "app/api/export/route.ts": { "maxDuration": 300 } } }
```

`fixtures/f6-long-jobs/repo/lib/db.ts`:
```ts
import { Pool } from "pg";

export const pool = new Pool({ connectionString: process.env.DATABASE_URL });
```

`fixtures/f6-long-jobs/repo/app/api/export/route.ts`:
```ts
import ExcelJS from "exceljs";
import { pool } from "@/lib/db";

export async function GET() {
  const wb = new ExcelJS.Workbook();
  const ws = wb.addWorksheet("orders");
  for (let offset = 0; offset < 200000; offset += 1000) {
    const { rows } = await pool.query("SELECT * FROM orders ORDER BY id LIMIT 1000 OFFSET $1", [offset]);
    rows.forEach((r) => ws.addRow(Object.values(r)));
  }
  const buf = await wb.xlsx.writeBuffer();
  return new Response(buf);
}
```

`fixtures/f6-long-jobs/repo/app/api/signup/route.ts`:
```ts
import nodemailer from "nodemailer";
import { pool } from "@/lib/db";

const mailer = nodemailer.createTransport({ host: process.env.SMTP_HOST });

export async function POST(req: Request) {
  const { email } = await req.json();
  await pool.query("INSERT INTO users (email) VALUES ($1)", [email]);
  mailer.sendMail({ to: email, subject: "환영합니다" });
  return Response.json({ ok: true });
}
```

`fixtures/f6-long-jobs/expected.yaml`:
```yaml
written_at: "2026-10-02"
note: 엔진 실행 전에 작성
repo_dir: repo
match: exact
workloads:
  - {id: w-web, kind: web}
endpoints:
  - {method: GET, route: /api/export}
  - {method: POST, route: /api/signup}
datastores:
  - {id: ds-postgresql, role: primary-db}
current_components:
  - {scope: ds-postgresql, component: "ds:unspecified/postgresql/default", status: confirmed}
  - {scope: w-web, component: "cp:vercel/functions/unspecified-plan", status: confirmed}
artifacts:
  - {kind: platform-config, path: vercel.json, settings: {"functions.app/api/export/route.ts.maxDuration": 300}}
request_paths:
  - id: path-web
    hops:
      - {kind: edge-proxy, component: "nw:vercel/edge-proxy/default"}
unmapped: []
```

- [ ] **Step 8: 커밋**

```bash
git add scripts/export_f1.sh fixtures/
git commit -m "test: add fixture repositories and expected S1 judgments written before the engine"
```

---

### Task 5: 매니페스트 파싱

**Files:**
- Create: `infrafit/detect/__init__.py`, `infrafit/detect/manifests.py`
- Test: `tests/detect/test_manifests.py`

**Interfaces:**
- Consumes: `Snapshot`, `line_of` (Task 3)
- Produces:
  - `infrafit.detect.manifests.Manifests` — 필드
    - `deps: dict[str, tuple[str, int | None]]` — 의존성 이름(소문자, Python은 `_`→`-`) → 처음 나온 (파일, 줄). Node와 Python을 한 사전에 모은다
    - `deps_by_dir: dict[str, set[str]]` — 매니페스트가 있는 디렉터리(`""` = 루트) → 의존성 이름 집합
    - `locations: dict[str, list[tuple[str, int | None]]]` — 의존성 이름 → 그 의존성이 나온 모든 (파일, 줄). 시그니처 근거와 `used_by` 판정이 이것을 쓴다
    - `scripts: dict[str, tuple[str, str, int | None]]` — `"<디렉터리>:<스크립트 이름>"` → (명령, 파일, 줄)
    - `procfile: dict[str, tuple[str, str, int]]` — `"<디렉터리>:<프로세스 종류>"` → (명령, 파일, 줄)
  - `infrafit.detect.manifests.parse_manifests(snap: Snapshot) -> Manifests`
  - `infrafit.detect.manifests.parent_dir(rel: str) -> str` (`"a/b/package.json"` → `"a/b"`, 루트 파일 → `""`)

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/detect/__init__.py`: 빈 파일

`tests/detect/test_manifests.py`:
```python
import json

from infrafit.detect.manifests import parent_dir, parse_manifests
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
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `uv run pytest tests/detect/test_manifests.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: 구현**

`infrafit/detect/__init__.py`:
```python
"""S1 탐지기. 판단하지 않고 있는 것만 기록한다."""
```

`infrafit/detect/manifests.py`:
```python
"""의존성 매니페스트와 실행 정의 파싱."""

from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import PurePosixPath

from infrafit.evidence import line_of
from infrafit.repo import Snapshot

_REQ_NAME = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def parent_dir(rel: str) -> str:
    parent = PurePosixPath(rel).parent.as_posix()
    return "" if parent == "." else parent


def _norm_py(name: str) -> str:
    return name.lower().replace("_", "-")


@dataclass
class Manifests:
    deps: dict[str, tuple[str, int | None]] = field(default_factory=dict)
    deps_by_dir: dict[str, set[str]] = field(default_factory=dict)
    locations: dict[str, list[tuple[str, int | None]]] = field(default_factory=dict)
    scripts: dict[str, tuple[str, str, int | None]] = field(default_factory=dict)
    procfile: dict[str, tuple[str, str, int]] = field(default_factory=dict)

    def add(self, name: str, rel: str, line: int | None) -> None:
        self.deps.setdefault(name, (rel, line))
        self.deps_by_dir.setdefault(parent_dir(rel), set()).add(name)
        if (rel, line) not in self.locations.setdefault(name, []):
            self.locations[name].append((rel, line))


def _node(snap: Snapshot, m: Manifests) -> None:
    for rel in snap.glob("**/package.json"):
        try:
            data = json.loads(snap.read(rel))
        except json.JSONDecodeError:
            continue
        for section in ("dependencies", "devDependencies"):
            for name in sorted(data.get(section) or {}):
                m.add(name.lower(), rel, line_of(snap, rel, f'"{name}"'))
        for name, cmd in sorted((data.get("scripts") or {}).items()):
            m.scripts[f"{parent_dir(rel)}:{name}"] = (str(cmd), rel, line_of(snap, rel, f'"{name}"'))


def _requirements(snap: Snapshot, m: Manifests) -> None:
    for rel in snap.glob("**/requirements*.txt"):
        for i, text in enumerate(snap.lines(rel), 1):
            body = text.split("#", 1)[0].strip()
            if not body or body.startswith("-"):
                continue
            match = _REQ_NAME.match(body)
            if match:
                m.add(_norm_py(match.group(1)), rel, i)


def _pyproject(snap: Snapshot, m: Manifests) -> None:
    for rel in snap.glob("**/pyproject.toml"):
        try:
            data = tomllib.loads(snap.read(rel))
        except tomllib.TOMLDecodeError:
            continue
        reqs = list((data.get("project") or {}).get("dependencies") or [])
        names = [mm.group(1) for r in reqs if (mm := _REQ_NAME.match(r))]
        poetry = ((data.get("tool") or {}).get("poetry") or {}).get("dependencies") or {}
        names += [k for k in poetry if k.lower() != "python"]
        for name in names:
            m.add(_norm_py(name), rel, line_of(snap, rel, name))


def _procfile(snap: Snapshot, m: Manifests) -> None:
    for rel in snap.glob("**/Procfile"):
        for i, text in enumerate(snap.lines(rel), 1):
            if ":" not in text or text.lstrip().startswith("#"):
                continue
            proc, cmd = text.split(":", 1)
            m.procfile[f"{parent_dir(rel)}:{proc.strip()}"] = (cmd.strip(), rel, i)


def parse_manifests(snap: Snapshot) -> Manifests:
    m = Manifests()
    _node(snap, m)
    _requirements(snap, m)
    _pyproject(snap, m)
    _procfile(snap, m)
    return m
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `uv run pytest tests/detect/test_manifests.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: 커밋**

```bash
git add infrafit/detect/__init__.py infrafit/detect/manifests.py tests/detect/
git commit -m "feat: parse dependency manifests and Procfile"
```

---

### Task 6: 지식 베이스(구성 요소 목록, 시그니처, 기본값)와 kb lint

**Files:**
- Create: `knowledge/components/catalog.yaml`, `knowledge/signatures/{datastores,cache,queue,scheduler,realtime,files,watchlist}.yaml`, `knowledge/defaults.yaml`, `infrafit/kb.py`, `infrafit/kb_lint.py`
- Modify: `infrafit/cli.py` (`kb lint` 하위 명령)
- Test: `tests/test_kb.py`

**Interfaces:**
- Produces:
  - `infrafit.kb.KB_DIR: Path`
  - `infrafit.kb.catalog() -> dict[str, dict]` — ID → `{id, family, name, source}`
  - `infrafit.kb.signatures() -> tuple[dict, ...]` — 시그니처 형식은 아래 YAML
  - `infrafit.kb.watchlist() -> tuple[str, ...]`
  - `infrafit.kb.defaults() -> tuple[dict, ...]`
  - `infrafit.kb.kb_version() -> str` — `knowledge/` 아래 모든 파일 내용의 sha256 앞 12자리
  - `infrafit.kb.iter_conditions(cond: dict)` — 조건 트리를 펼쳐 말단 조건(`dependency` 또는 `code`)을 내놓는 생성기
  - `infrafit.kb_lint.lint() -> list[str]` — 문제 목록(빈 목록이면 통과)
  - 시그니처 YAML 형식:
    ```yaml
    signatures:
      - id: SIG-…              # 고유
        component: "ds:…"      # catalog에 있어야 함
        role: primary-db       # Datastore.role 값 중 하나
        status: confirmed      # confirmed | candidate
        when: {any: [조건…]}   # 또는 {all: [...]}, 중첩 가능
        refine:                # 선택. 처음 맞는 것으로 구성 요소를 바꿈
          - {component: "…", when: {...}, status: …}
    # 조건: {dependency: <이름>} 또는 {code: {glob: <패턴>, regex: <정규식>, flags: i}}
    ```
  - 기본값 YAML 형식: `{artifact, key, value, source: {ref, quote?, checked_at?}}` + `artifact`가 `k8s`면 `match_kind`, `terraform`이면 `resource`, `hop`이면 `component`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_kb.py`:
```python
from infrafit import kb
from infrafit.kb_lint import lint


def test_knowledge_files_pass_lint():
    assert lint() == []


def test_catalog_contains_ids_used_by_fixtures():
    for cid in ["ds:local/sqlite/wal", "cp:vercel/functions/unspecified-plan",
                "nw:app/uvicorn/default", "nw:aws/alb/default"]:
        assert cid in kb.catalog()


def test_iter_conditions_flattens_tree():
    cond = {"any": [{"dependency": "pg"}, {"all": [{"dependency": "x"}, {"code": {"glob": "*", "regex": "a"}}]}]}
    leaves = list(kb.iter_conditions(cond))
    assert {"dependency": "pg"} in leaves
    assert len(leaves) == 3


def test_kb_version_is_short_hash():
    assert len(kb.kb_version()) == 12
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `uv run pytest tests/test_kb.py -v`
Expected: FAIL (`ImportError`)

- [ ] **Step 3: 구성 요소 목록 작성**

`knowledge/components/catalog.yaml`:
```yaml
# S1이 쓰는 구성 요소 ID 목록. 능력 값은 계획 3에서 같은 ID로 components/*.yaml에 채운다.
components:
  # 저장소
  - {id: "ds:local/sqlite/default", family: ds, name: "SQLite (롤백 저널)", source: docs/research/capabilities/01-sql-databases.md}
  - {id: "ds:local/sqlite/wal", family: ds, name: "SQLite (WAL)", source: docs/research/capabilities/01-sql-databases.md}
  - {id: "ds:unspecified/postgresql/default", family: ds, name: "PostgreSQL (호스팅 미확인)", source: docs/research/capabilities/01-sql-databases.md}
  - {id: "ds:unspecified/mysql/default", family: ds, name: "MySQL (호스팅 미확인)", source: docs/research/capabilities/01-sql-databases.md}
  - {id: "ds:unspecified/mongodb/default", family: ds, name: "MongoDB (호스팅 미확인)", source: docs/research/capabilities/02-nosql-baas.md}
  - {id: "ds:supabase/postgres/unspecified-plan", family: ds, name: "Supabase Postgres (플랜 미확인)", source: docs/research/capabilities/01-sql-databases.md}
  - {id: "ds:firebase/firestore/standard", family: ds, name: "Cloud Firestore (Standard)", source: docs/research/capabilities/02-nosql-baas.md}
  - {id: "ds:aws/rds-postgres/single-az", family: ds, name: "RDS for PostgreSQL 단일 AZ", source: docs/research/capabilities/01-sql-databases.md}
  - {id: "ds:aws/rds-postgres/multi-az-instance", family: ds, name: "RDS for PostgreSQL Multi-AZ 인스턴스", source: docs/research/capabilities/01-sql-databases.md}
  - {id: "ds:gcp/cloudsql-postgres/single", family: ds, name: "Cloud SQL for PostgreSQL 단일", source: docs/research/capabilities/01-sql-databases.md}
  - {id: "ds:gcp/cloudsql-postgres/ha", family: ds, name: "Cloud SQL for PostgreSQL HA", source: docs/research/capabilities/01-sql-databases.md}
  # 캐시
  - {id: "ca:local/process-memory/default", family: ca, name: "프로세스 메모리", source: docs/research/capabilities/03-cache-queue-scheduler-realtime-storage.md}
  - {id: "ca:unspecified/redis/default", family: ca, name: "Redis (호스팅 미확인)", source: docs/research/capabilities/03-cache-queue-scheduler-realtime-storage.md}
  - {id: "ca:aws/elasticache/node-based", family: ca, name: "ElastiCache 노드 기반", source: docs/research/capabilities/03-cache-queue-scheduler-realtime-storage.md}
  - {id: "ca:gcp/memorystore/redis", family: ca, name: "Memorystore for Redis", source: docs/research/capabilities/03-cache-queue-scheduler-realtime-storage.md}
  # 큐
  - {id: "qu:unspecified/redis-streams/default", family: qu, name: "Redis Streams", source: docs/research/capabilities/03-cache-queue-scheduler-realtime-storage.md}
  - {id: "qu:lib/bullmq/default", family: qu, name: "BullMQ", source: docs/research/capabilities/03-cache-queue-scheduler-realtime-storage.md}
  - {id: "qu:lib/celery/default", family: qu, name: "Celery", source: docs/research/capabilities/03-cache-queue-scheduler-realtime-storage.md}
  - {id: "qu:aws/sqs/standard", family: qu, name: "Amazon SQS 표준", source: docs/research/capabilities/03-cache-queue-scheduler-realtime-storage.md}
  # 스케줄러
  - {id: "sc:local/in-process/default", family: sc, name: "앱 프로세스 안 스케줄러", source: docs/research/capabilities/03-cache-queue-scheduler-realtime-storage.md}
  - {id: "sc:k8s/cronjob/default", family: sc, name: "Kubernetes CronJob", source: docs/research/capabilities/03-cache-queue-scheduler-realtime-storage.md}
  - {id: "sc:vercel/cron/unspecified-plan", family: sc, name: "Vercel Cron (플랜 미확인)", source: docs/research/capabilities/03-cache-queue-scheduler-realtime-storage.md}
  # 실시간
  - {id: "rt:lib/socketio/no-adapter", family: rt, name: "Socket.IO (어댑터 없음)", source: docs/research/capabilities/03-cache-queue-scheduler-realtime-storage.md}
  - {id: "rt:lib/socketio/redis-adapter", family: rt, name: "Socket.IO (Redis 어댑터)", source: docs/research/capabilities/03-cache-queue-scheduler-realtime-storage.md}
  - {id: "rt:lib/ws/default", family: rt, name: "ws", source: docs/research/capabilities/03-cache-queue-scheduler-realtime-storage.md}
  # 파일 저장소
  - {id: "fs:local/container-disk/default", family: fs, name: "컨테이너 로컬 디스크", source: docs/research/capabilities/03-cache-queue-scheduler-realtime-storage.md}
  - {id: "fs:aws/s3/default", family: fs, name: "Amazon S3", source: docs/research/capabilities/03-cache-queue-scheduler-realtime-storage.md}
  - {id: "fs:gcp/gcs/default", family: fs, name: "Google Cloud Storage", source: docs/research/capabilities/03-cache-queue-scheduler-realtime-storage.md}
  - {id: "fs:supabase/storage/default", family: fs, name: "Supabase Storage", source: docs/research/capabilities/03-cache-queue-scheduler-realtime-storage.md}
  # 컴퓨트
  - {id: "cp:vercel/functions/unspecified-plan", family: cp, name: "Vercel Functions (플랜 미확인)", source: docs/research/capabilities/04-compute-tier0.md}
  - {id: "cp:netlify/functions/unspecified-plan", family: cp, name: "Netlify Functions (플랜 미확인)", source: docs/research/capabilities/04-compute-tier0.md}
  - {id: "cp:fly/machines/default", family: cp, name: "Fly.io Machines", source: docs/research/capabilities/04-compute-tier0.md}
  - {id: "cp:render/web/unspecified-plan", family: cp, name: "Render 웹 서비스 (플랜 미확인)", source: docs/research/capabilities/04-compute-tier0.md}
  - {id: "cp:railway/service/unspecified-plan", family: cp, name: "Railway 서비스 (플랜 미확인)", source: docs/research/capabilities/04-compute-tier0.md}
  - {id: "cp:k8s/deployment/unspecified-cluster", family: cp, name: "쿠버네티스 (클러스터 미확인)", source: docs/research/capabilities/05-compute-tier1-2.md}
  - {id: "cp:aws/eks/unspecified", family: cp, name: "Amazon EKS (구성 미확인)", source: docs/research/capabilities/05-compute-tier1-2.md}
  - {id: "cp:gcp/gke/unspecified", family: cp, name: "GKE (구성 미확인)", source: docs/research/capabilities/05-compute-tier1-2.md}
  - {id: "cp:local/compose/default", family: cp, name: "docker compose", source: docs/research/capabilities/05-compute-tier1-2.md}
  - {id: "cp:docker/container/unspecified-host", family: cp, name: "컨테이너 (실행 환경 미확인)", source: docs/research/capabilities/05-compute-tier1-2.md}
  # 네트워크 경로
  - {id: "nw:app/uvicorn/default", family: nw, name: "uvicorn", source: docs/research/capabilities/09-network-lb-ingress.md}
  - {id: "nw:app/gunicorn/default", family: nw, name: "gunicorn", source: docs/research/capabilities/09-network-lb-ingress.md}
  - {id: "nw:app/node-http/default", family: nw, name: "Node.js http 서버", source: docs/research/capabilities/09-network-lb-ingress.md}
  - {id: "nw:app/next-start/default", family: nw, name: "next start", source: docs/research/capabilities/09-network-lb-ingress.md}
  - {id: "nw:app/flask-dev/default", family: nw, name: "Flask 개발 서버", source: docs/research/capabilities/09-network-lb-ingress.md}
  - {id: "nw:app/django-runserver/default", family: nw, name: "Django 개발 서버", source: docs/research/capabilities/09-network-lb-ingress.md}
  - {id: "nw:proxy/nginx/default", family: nw, name: "nginx 리버스 프록시", source: docs/research/capabilities/09-network-lb-ingress.md}
  - {id: "nw:aws/alb/default", family: nw, name: "AWS Application Load Balancer", source: docs/research/capabilities/09-network-lb-ingress.md}
  - {id: "nw:gcp/classic-alb/gke-ingress", family: nw, name: "GCP Classic Application LB (GKE Ingress)", source: docs/research/capabilities/09-network-lb-ingress.md}
  - {id: "nw:k8s/ingress-nginx/default", family: nw, name: "ingress-nginx", source: docs/research/capabilities/09-network-lb-ingress.md}
  - {id: "nw:vercel/edge-proxy/default", family: nw, name: "Vercel 엣지 프록시", source: docs/research/capabilities/09-network-lb-ingress.md}
  - {id: "nw:netlify/edge-proxy/default", family: nw, name: "Netlify 엣지 프록시", source: docs/research/capabilities/09-network-lb-ingress.md}
  - {id: "nw:fly/proxy/default", family: nw, name: "Fly.io 프록시", source: docs/research/capabilities/09-network-lb-ingress.md}
  - {id: "nw:render/proxy/default", family: nw, name: "Render 프록시", source: docs/research/capabilities/09-network-lb-ingress.md}
  - {id: "nw:railway/proxy/default", family: nw, name: "Railway 프록시", source: docs/research/capabilities/09-network-lb-ingress.md}
```

- [ ] **Step 4: 시그니처 작성**

`knowledge/signatures/datastores.yaml`:
```yaml
signatures:
  - id: SIG-DS-SQLITE
    component: "ds:local/sqlite/default"
    role: primary-db
    status: confirmed
    when:
      any:
        - {dependency: better-sqlite3}
        - {dependency: sqlite3}
        - {code: {glob: "**/*.py", regex: "sqlite3\\.connect\\("}}
        - {code: {glob: "**/schema.prisma", regex: "provider\\s*=\\s*\"sqlite\""}}
        - {code: {glob: "**/settings*.py", regex: "django\\.db\\.backends\\.sqlite3"}}
    refine:
      - component: "ds:local/sqlite/wal"
        when:
          any:
            - {code: {glob: "**/*.py", regex: "journal_mode\\s*=\\s*WAL", flags: i}}
            - {code: {glob: "**/*.ts", regex: "journal_mode\\s*=\\s*WAL", flags: i}}
            - {code: {glob: "**/*.js", regex: "journal_mode\\s*=\\s*WAL", flags: i}}
  - id: SIG-DS-POSTGRES
    component: "ds:unspecified/postgresql/default"
    role: primary-db
    status: confirmed
    when:
      any:
        - {dependency: pg}
        - {dependency: postgres}
        - {dependency: psycopg}
        - {dependency: psycopg2}
        - {dependency: psycopg2-binary}
        - {dependency: asyncpg}
        - {code: {glob: "**/schema.prisma", regex: "provider\\s*=\\s*\"postgresql\""}}
        - {code: {glob: "**/settings*.py", regex: "django\\.db\\.backends\\.postgresql"}}
  - id: SIG-DS-MYSQL
    component: "ds:unspecified/mysql/default"
    role: primary-db
    status: confirmed
    when:
      any:
        - {dependency: mysql2}
        - {dependency: mysqlclient}
        - {dependency: pymysql}
        - {code: {glob: "**/schema.prisma", regex: "provider\\s*=\\s*\"mysql\""}}
  - id: SIG-DS-MONGO
    component: "ds:unspecified/mongodb/default"
    role: primary-db
    status: confirmed
    when:
      any:
        - {dependency: mongodb}
        - {dependency: mongoose}
        - {dependency: pymongo}
        - {dependency: motor}
  - id: SIG-DS-SUPABASE
    component: "ds:supabase/postgres/unspecified-plan"
    role: primary-db
    status: confirmed
    when:
      any:
        - {dependency: "@supabase/supabase-js"}
        - {dependency: supabase}
  - id: SIG-DS-FIRESTORE
    component: "ds:firebase/firestore/standard"
    role: primary-db
    status: confirmed
    when:
      any:
        - {code: {glob: "**/*.ts", regex: "getFirestore\\("}}
        - {code: {glob: "**/*.js", regex: "getFirestore\\("}}
        - {code: {glob: "**/*.py", regex: "firestore\\.client\\("}}
```

`knowledge/signatures/cache.yaml`:
```yaml
signatures:
  - id: SIG-CA-REDIS
    component: "ca:unspecified/redis/default"
    role: cache
    status: confirmed
    when:
      any:
        - {dependency: redis}
        - {dependency: ioredis}
  - id: SIG-CA-SESSION-EXPRESS-MEMORY
    component: "ca:local/process-memory/default"
    role: session
    status: candidate
    when:
      all:
        - {dependency: express-session}
        - any:
            - {code: {glob: "**/*.js", regex: "session\\(\\s*\\{"}}
            - {code: {glob: "**/*.ts", regex: "session\\(\\s*\\{"}}
  - id: SIG-CA-SESSION-MAP
    component: "ca:local/process-memory/default"
    role: session
    status: candidate
    when:
      any:
        - {code: {glob: "**/*session*.ts", regex: "new Map\\s*[<(]"}}
        - {code: {glob: "**/*session*.js", regex: "new Map\\s*[<(]"}}
```

`knowledge/signatures/queue.yaml`:
```yaml
signatures:
  - id: SIG-QU-REDIS-STREAMS
    component: "qu:unspecified/redis-streams/default"
    role: queue
    status: confirmed
    when:
      any:
        - {code: {glob: "**/*.py", regex: "\\.xadd\\("}}
        - {code: {glob: "**/*.ts", regex: "\\.xadd\\("}}
        - {code: {glob: "**/*.js", regex: "\\.xadd\\("}}
  - id: SIG-QU-BULLMQ
    component: "qu:lib/bullmq/default"
    role: queue
    status: confirmed
    when: {any: [{dependency: bullmq}]}
  - id: SIG-QU-CELERY
    component: "qu:lib/celery/default"
    role: queue
    status: confirmed
    when: {any: [{dependency: celery}]}
  - id: SIG-QU-SQS
    component: "qu:aws/sqs/standard"
    role: queue
    status: confirmed
    when:
      any:
        - {code: {glob: "**/*.ts", regex: "SendMessageCommand"}}
        - {code: {glob: "**/*.js", regex: "SendMessageCommand"}}
        - {code: {glob: "**/*.py", regex: "\\.send_message\\("}}
```

`knowledge/signatures/scheduler.yaml`:
```yaml
signatures:
  - id: SIG-SC-INPROC
    component: "sc:local/in-process/default"
    role: scheduler
    status: candidate
    when:
      any:
        - {dependency: node-cron}
        - {dependency: cron}
        - {dependency: apscheduler}
        - {dependency: schedule}
  - id: SIG-SC-K8S-CRONJOB
    component: "sc:k8s/cronjob/default"
    role: scheduler
    status: confirmed
    when:
      any:
        - {code: {glob: "**/*.yaml", regex: "^kind:\\s*CronJob"}}
        - {code: {glob: "**/*.yml", regex: "^kind:\\s*CronJob"}}
  - id: SIG-SC-VERCEL-CRON
    component: "sc:vercel/cron/unspecified-plan"
    role: scheduler
    status: confirmed
    when: {any: [{code: {glob: "vercel.json", regex: "\"crons\""}}]}
```

`knowledge/signatures/realtime.yaml`:
```yaml
signatures:
  - id: SIG-RT-SOCKETIO
    component: "rt:lib/socketio/no-adapter"
    role: realtime
    status: confirmed
    when: {any: [{dependency: socket.io}]}
    refine:
      - component: "rt:lib/socketio/redis-adapter"
        when: {any: [{dependency: "@socket.io/redis-adapter"}]}
  - id: SIG-RT-WS
    component: "rt:lib/ws/default"
    role: realtime
    status: candidate
    when: {any: [{dependency: ws}]}
```

`knowledge/signatures/files.yaml`:
```yaml
signatures:
  - id: SIG-FS-LOCAL
    component: "fs:local/container-disk/default"
    role: file-storage
    status: candidate
    when:
      any:
        - {code: {glob: "**/*.py", regex: "\\.save\\(\\s*os\\.path\\.join\\("}}
        - {code: {glob: "**/*.ts", regex: "writeFile(Sync)?\\("}}
        - {code: {glob: "**/*.js", regex: "writeFile(Sync)?\\("}}
        - {code: {glob: "**/*.js", regex: "multer\\(\\s*\\{\\s*dest"}}
        - {code: {glob: "**/*.ts", regex: "multer\\(\\s*\\{\\s*dest"}}
  - id: SIG-FS-S3
    component: "fs:aws/s3/default"
    role: file-storage
    status: confirmed
    when:
      any:
        - {dependency: "@aws-sdk/client-s3"}
        - {code: {glob: "**/*.py", regex: "(upload_fileobj|put_object)\\("}}
  - id: SIG-FS-GCS
    component: "fs:gcp/gcs/default"
    role: file-storage
    status: confirmed
    when:
      any:
        - {dependency: "@google-cloud/storage"}
        - {dependency: google-cloud-storage}
  - id: SIG-FS-SUPABASE
    component: "fs:supabase/storage/default"
    role: file-storage
    status: confirmed
    when:
      any:
        - {code: {glob: "**/*.ts", regex: "\\.storage\\s*\\.from\\("}}
        - {code: {glob: "**/*.js", regex: "\\.storage\\s*\\.from\\("}}
```

`knowledge/signatures/watchlist.yaml`:
```yaml
# 인프라에 영향을 주지만 아직 시그니처가 없는 패키지. 있으면 S1의 unmapped로 나온다.
packages:
  - pg-boss
  - kafkajs
  - nats
  - amqplib
  - pika
  - cassandra-driver
  - neo4j-driver
  - "@elastic/elasticsearch"
  - elasticsearch
  - meilisearch
  - typesense
  - pusher
  - ably
  - "@upstash/redis"
  - "@planetscale/database"
  - "@neondatabase/serverless"
  - "@vercel/postgres"
  - "@vercel/kv"
  - "@vercel/blob"
  - appwrite
  - convex
  - pocketbase
```

- [ ] **Step 5: 기본값 표 작성**

`knowledge/defaults.yaml`:
```yaml
# 설정이 없을 때 적용되는 값. S1은 설정이 없으면 이 값을 defaulted: true로 기록한다(설계 §6.5).
defaults:
  - artifact: dockerfile
    key: user
    value: root
    source: {ref: docs/research/capabilities/08-artifacts-compute.md}
  - artifact: k8s
    match_kind: Deployment
    key: terminationGracePeriodSeconds
    value: 30
    source:
      ref: "https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/"
      quote: "The default terminationGracePeriodSeconds setting is 30 seconds."
      checked_at: "2026-10-01"
  - artifact: k8s
    match_kind: CronJob
    key: concurrencyPolicy
    value: Allow
    source: {ref: docs/research/considerations/03-deploy-release.md}
  - artifact: terraform
    resource: aws_db_instance
    key: backup_retention_period
    value: 0
    source: {ref: docs/research/capabilities/06-artifacts-datastores.md}
  - artifact: terraform
    resource: aws_db_instance
    key: multi_az
    value: false
    source: {ref: docs/research/capabilities/06-artifacts-datastores.md}
  - artifact: terraform
    resource: aws_db_instance
    key: storage_encrypted
    value: false
    source: {ref: docs/research/capabilities/06-artifacts-datastores.md}
  - artifact: hop
    component: "nw:app/uvicorn/default"
    key: timeout_keep_alive
    value: 5
    source: {ref: docs/research/capabilities/09-network-lb-ingress.md}
  - artifact: hop
    component: "nw:app/gunicorn/default"
    key: keepalive
    value: 2
    source: {ref: docs/research/capabilities/09-network-lb-ingress.md}
  - artifact: hop
    component: "nw:app/node-http/default"
    key: keep_alive_timeout
    value: 5
    source: {ref: docs/research/capabilities/09-network-lb-ingress.md}
  - artifact: hop
    component: "nw:aws/alb/default"
    key: idle_timeout
    value: 60
    source: {ref: docs/research/capabilities/09-network-lb-ingress.md}
  - artifact: hop
    component: "nw:gcp/classic-alb/gke-ingress"
    key: backend_timeout
    value: 30
    source: {ref: docs/research/capabilities/09-network-lb-ingress.md}
```

- [ ] **Step 6: 로더와 lint 구현**

`infrafit/kb.py`:
```python
"""knowledge/ 아래 YAML 지식 베이스 로더."""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path

import yaml

KB_DIR = Path(__file__).resolve().parent.parent / "knowledge"


def _load(rel: str) -> dict:
    return yaml.safe_load((KB_DIR / rel).read_text(encoding="utf-8")) or {}


@lru_cache(maxsize=1)
def catalog() -> dict[str, dict]:
    return {c["id"]: c for c in _load("components/catalog.yaml")["components"]}


@lru_cache(maxsize=1)
def signatures() -> tuple[dict, ...]:
    out: list[dict] = []
    for path in sorted((KB_DIR / "signatures").glob("*.yaml")):
        if path.name == "watchlist.yaml":
            continue
        out.extend(yaml.safe_load(path.read_text(encoding="utf-8"))["signatures"])
    return tuple(out)


@lru_cache(maxsize=1)
def watchlist() -> tuple[str, ...]:
    return tuple(_load("signatures/watchlist.yaml")["packages"])


@lru_cache(maxsize=1)
def defaults() -> tuple[dict, ...]:
    return tuple(_load("defaults.yaml")["defaults"])


@lru_cache(maxsize=1)
def kb_version() -> str:
    digest = hashlib.sha256()
    for path in sorted(KB_DIR.rglob("*.yaml")):
        digest.update(path.relative_to(KB_DIR).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()[:12]


def iter_conditions(cond: dict) -> Iterator[dict]:
    if "any" in cond or "all" in cond:
        for child in cond.get("any", []) + cond.get("all", []):
            yield from iter_conditions(child)
    else:
        yield cond
```

`infrafit/kb_lint.py`:
```python
"""knowledge/ 형식 검사."""

from __future__ import annotations

import re

from infrafit import kb

COMPONENT_ID = re.compile(r"^(cp|ds|ca|qu|sc|rt|fs|nw):[a-z0-9._-]+/[a-z0-9._-]+/[a-z0-9._-]+$")
ROLES = {"primary-db", "cache", "session", "queue", "scheduler", "realtime", "file-storage", "search", "other"}
STATUSES = {"confirmed", "candidate"}
ARTIFACTS = {"dockerfile", "k8s", "terraform", "hop"}


def _lint_catalog() -> list[str]:
    issues: list[str] = []
    seen: set[str] = set()
    for c in kb._load("components/catalog.yaml")["components"]:
        cid = c.get("id", "")
        if not COMPONENT_ID.match(cid):
            issues.append(f"catalog: 잘못된 ID 형식 {cid!r}")
        if cid in seen:
            issues.append(f"catalog: 중복 ID {cid}")
        seen.add(cid)
        if c.get("family") != cid.split(":")[0]:
            issues.append(f"catalog: {cid}의 family가 접두어와 다름")
        if not c.get("name") or not c.get("source"):
            issues.append(f"catalog: {cid}에 name 또는 source 없음")
    return issues


def _lint_condition(sig_id: str, cond: dict) -> list[str]:
    issues: list[str] = []
    for leaf in kb.iter_conditions(cond):
        if "dependency" in leaf:
            if not isinstance(leaf["dependency"], str) or not leaf["dependency"]:
                issues.append(f"{sig_id}: dependency가 비었음")
        elif "code" in leaf:
            code = leaf["code"]
            if not code.get("glob") or not code.get("regex"):
                issues.append(f"{sig_id}: code에 glob 또는 regex 없음")
                continue
            try:
                re.compile(code["regex"])
            except re.error as e:
                issues.append(f"{sig_id}: 정규식 오류 {e}")
            if code.get("flags") not in (None, "i"):
                issues.append(f"{sig_id}: flags는 i만 허용")
        else:
            issues.append(f"{sig_id}: 알 수 없는 조건 {leaf}")
    return issues


def _lint_signatures() -> list[str]:
    issues: list[str] = []
    catalog = kb.catalog()
    seen: set[str] = set()
    for s in kb.signatures():
        sid = s.get("id", "?")
        if sid in seen:
            issues.append(f"signature: 중복 ID {sid}")
        seen.add(sid)
        if s.get("component") not in catalog:
            issues.append(f"{sid}: catalog에 없는 구성 요소 {s.get('component')}")
        if s.get("role") not in ROLES:
            issues.append(f"{sid}: 잘못된 role {s.get('role')}")
        if s.get("status") not in STATUSES:
            issues.append(f"{sid}: 잘못된 status {s.get('status')}")
        if not s.get("when"):
            issues.append(f"{sid}: when 없음")
        else:
            issues += _lint_condition(sid, s["when"])
        for r in s.get("refine", []):
            if r.get("component") not in catalog:
                issues.append(f"{sid}: refine의 구성 요소가 catalog에 없음 {r.get('component')}")
            issues += _lint_condition(sid, r.get("when", {}))
    return issues


def _lint_defaults() -> list[str]:
    issues: list[str] = []
    for d in kb.defaults():
        name = f"default {d.get('artifact')}:{d.get('key')}"
        if d.get("artifact") not in ARTIFACTS:
            issues.append(f"{name}: 잘못된 artifact")
        if "key" not in d or "value" not in d:
            issues.append(f"{name}: key 또는 value 없음")
        if not (d.get("source") or {}).get("ref"):
            issues.append(f"{name}: source.ref 없음")
        if d.get("artifact") == "hop" and d.get("component") not in kb.catalog():
            issues.append(f"{name}: catalog에 없는 구성 요소")
        if d.get("artifact") == "k8s" and not d.get("match_kind"):
            issues.append(f"{name}: match_kind 없음")
        if d.get("artifact") == "terraform" and not d.get("resource"):
            issues.append(f"{name}: resource 없음")
    return issues


def lint() -> list[str]:
    return _lint_catalog() + _lint_signatures() + _lint_defaults()
```

`infrafit/cli.py`에 추가(`build_parser` 안, `return parser` 앞):
```python
    kb_cmd = sub.add_parser("kb", help="지식 베이스 도구")
    kb_sub = kb_cmd.add_subparsers(dest="kb_command")
    kb_lint = kb_sub.add_parser("lint", help="knowledge/ 형식 검사")
    kb_lint.set_defaults(func=_cmd_kb_lint)
```
그리고 파일 위쪽 함수들 옆에:
```python
def _cmd_kb_lint(args: argparse.Namespace) -> int:
    from infrafit.kb_lint import lint

    issues = lint()
    for issue in issues:
        print(issue)
    print(f"{len(issues)}개 문제")
    return 1 if issues else 0
```

- [ ] **Step 7: 테스트 통과 확인**

Run: `uv run pytest tests/test_kb.py -v && uv run infrafit kb lint`
Expected: PASS (4 passed), 그리고 `0개 문제`

- [ ] **Step 8: 커밋**

```bash
git add knowledge/ infrafit/kb.py infrafit/kb_lint.py infrafit/cli.py tests/test_kb.py
git commit -m "feat: add component catalog, detection signatures, defaults table and kb lint"
```

---

### Task 7: 시그니처 매칭

**Files:**
- Create: `infrafit/detect/signatures.py`
- Test: `tests/detect/test_signatures.py`

**Interfaces:**
- Consumes: `Snapshot`, `evidence` (Task 3), `Manifests` (Task 5), 시그니처 형식 (Task 6)
- Produces:
  - `infrafit.detect.signatures.Match` — `@dataclass(frozen=True)`: `signature: str`, `component: str`, `role: str`, `status: str`, `evidence: tuple[dict, ...]`
  - `infrafit.detect.signatures.match_signatures(snap, manifests, sigs) -> list[Match]` — 시그니처 순서대로, 맞은 것만. `dependency` 조건의 근거는 그 의존성이 나온 모든 매니페스트 줄, `code` 조건의 근거는 조건당 최대 5줄

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/detect/test_signatures.py`:
```python
from infrafit.detect.manifests import parse_manifests
from infrafit.detect.signatures import match_signatures
from infrafit.repo import open_snapshot

SIGS = (
    {"id": "SIG-A", "component": "ds:local/sqlite/default", "role": "primary-db", "status": "confirmed",
     "when": {"any": [{"code": {"glob": "**/*.py", "regex": r"sqlite3\.connect\("}}]},
     "refine": [{"component": "ds:local/sqlite/wal",
                 "when": {"any": [{"code": {"glob": "**/*.py", "regex": "journal_mode=wal", "flags": "i"}}]}}]},
    {"id": "SIG-B", "component": "ca:unspecified/redis/default", "role": "cache", "status": "confirmed",
     "when": {"all": [{"dependency": "redis"}, {"code": {"glob": "**/*.py", "regex": "Redis\\("}}]}},
    {"id": "SIG-C", "component": "qu:lib/celery/default", "role": "queue", "status": "confirmed",
     "when": {"any": [{"dependency": "celery"}]}},
)


def _snap(tmp_path):
    (tmp_path / "requirements.txt").write_text("redis==5.0\n")
    (tmp_path / "db.py").write_text("import sqlite3\nc = sqlite3.connect('a.db')\nc.execute('PRAGMA journal_mode=WAL')\n")
    return open_snapshot(str(tmp_path), tmp_path / "_w")


def test_any_with_refine_upgrades_component(tmp_path):
    snap = _snap(tmp_path)
    matches = match_signatures(snap, parse_manifests(snap), SIGS)
    a = next(m for m in matches if m.signature == "SIG-A")
    assert a.component == "ds:local/sqlite/wal"
    assert {"path": "db.py", "line": 2, "snippet": "c = sqlite3.connect('a.db')", "kind": "tech"} in a.evidence
    assert any(e["line"] == 3 for e in a.evidence)


def test_all_requires_every_condition(tmp_path):
    snap = _snap(tmp_path)
    matches = match_signatures(snap, parse_manifests(snap), SIGS)
    assert [m.signature for m in matches] == ["SIG-A"]
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `uv run pytest tests/detect/test_signatures.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: 구현**

`infrafit/detect/signatures.py`:
```python
"""knowledge/signatures/*.yaml의 시그니처를 저장소에 맞춰 본다."""

from __future__ import annotations

import re
from dataclasses import dataclass

from infrafit.detect.manifests import Manifests
from infrafit.evidence import evidence
from infrafit.repo import Snapshot

MAX_CODE_EVIDENCE = 5


@dataclass(frozen=True)
class Match:
    signature: str
    component: str
    role: str
    status: str
    evidence: tuple[dict, ...]


def _eval(cond: dict, snap: Snapshot, manifests: Manifests) -> list[dict]:
    """맞으면 근거 목록, 안 맞으면 빈 목록."""
    if "any" in cond:
        out: list[dict] = []
        for child in cond["any"]:
            out += _eval(child, snap, manifests)
        return out
    if "all" in cond:
        parts = [_eval(child, snap, manifests) for child in cond["all"]]
        return [e for part in parts for e in part] if all(parts) else []
    if "dependency" in cond:
        return [evidence(snap, rel, line, "tech")
                for rel, line in manifests.locations.get(cond["dependency"].lower(), [])]
    if "code" in cond:
        code = cond["code"]
        flags = re.MULTILINE | (re.IGNORECASE if code.get("flags") == "i" else 0)
        rx = re.compile(code["regex"], flags)
        out = []
        for rel in snap.glob(code["glob"]):
            for i, text in enumerate(snap.lines(rel), 1):
                if rx.search(text):
                    out.append(evidence(snap, rel, i, "tech"))
                    if len(out) >= MAX_CODE_EVIDENCE:
                        return out
        return out
    raise ValueError(f"알 수 없는 조건: {cond}")


def match_signatures(snap: Snapshot, manifests: Manifests, sigs) -> list[Match]:
    out: list[Match] = []
    for sig in sigs:
        ev = _eval(sig["when"], snap, manifests)
        if not ev:
            continue
        component, status = sig["component"], sig["status"]
        for refine in sig.get("refine", []):
            extra = _eval(refine["when"], snap, manifests)
            if extra:
                component = refine["component"]
                status = refine.get("status", status)
                ev = ev + extra
                break
        out.append(Match(sig["id"], component, sig["role"], status, tuple(ev)))
    return out
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `uv run pytest tests/detect/test_signatures.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: 커밋**

```bash
git add infrafit/detect/signatures.py tests/detect/test_signatures.py
git commit -m "feat: match detection signatures against repository"
```

---

### Task 8: 기존 산출물 파서 — Dockerfile, compose, 플랫폼 설정, CI

**Files:**
- Create: `infrafit/detect/artifacts.py`
- Test: `tests/detect/test_artifacts_basic.py`

**Interfaces:**
- Consumes: `Snapshot`, `evidence`, `line_of` (Task 3)
- Produces:
  - `infrafit.detect.artifacts.ParsedArtifact` — `@dataclass`: `kind: str`, `path: str`, `parsed: bool`, `settings: list[dict]`, `objects: list`; 메서드 `to_dict() -> dict`(`ExistingArtifact` 형식, settings는 key로 정렬), `get(key, default=None)`
    - `objects` 내용: dockerfile = `[(명령, 인자, 줄)]`, compose = `[(서비스 이름, 서비스 dict)]`, k8s = 문서 dict 목록, terraform = `[(리소스 타입, 이름, 속성 dict)]`, platform-config = `[(파일 이름, 파싱된 dict)]`
  - `infrafit.detect.artifacts.flatten(obj, prefix: str = "", depth: int = 2) -> dict` — 중첩 dict를 `a.b.c` 키로 펼침(블록 목록은 첫 원소), `__`로 시작하는 키 무시, 따옴표로 감싼 문자열은 벗김
  - `infrafit.detect.artifacts.parse_artifacts(snap) -> list[ParsedArtifact]` — 경로 순 정렬. 이 Task에서는 dockerfile, compose, platform-config, ci만, Task 9에서 k8s와 terraform 추가
  - 설정 키 규칙: dockerfile `base_image`, `stages`, `user`, `cmd`, `entrypoint`, `expose`, `healthcheck` / compose `services.<이름>.image|command|ports` / platform-config는 `flatten` 결과 / ci `jobs`(작업 이름 목록), `uses`(사용한 액션 목록)

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/detect/test_artifacts_basic.py`:
```python
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
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `uv run pytest tests/detect/test_artifacts_basic.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: 구현**

`infrafit/detect/artifacts.py`:
```python
"""기존 산출물(Dockerfile, compose, k8s, Terraform, 플랫폼 설정, CI) 파싱."""

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass, field
from pathlib import PurePosixPath

import yaml

from infrafit.evidence import evidence, line_of
from infrafit.repo import Snapshot

PLATFORM_FILES = {"vercel.json", "netlify.toml", "fly.toml", "render.yaml", "railway.json", "railway.toml"}


@dataclass
class ParsedArtifact:
    kind: str
    path: str
    parsed: bool
    settings: list[dict] = field(default_factory=list)
    objects: list = field(default_factory=list)

    def get(self, key: str, default=None):
        for s in self.settings:
            if s["key"] == key:
                return s["value"]
        return default

    def to_dict(self) -> dict:
        return {"kind": self.kind, "path": self.path, "parsed": self.parsed,
                "settings": sorted(self.settings, key=lambda s: s["key"])}


def _fact(snap: Snapshot, rel: str, key: str, value, line: int | None = None) -> dict:
    fact = {"key": key, "value": value, "defaulted": False}
    if line:
        fact["evidence"] = evidence(snap, rel, line)
    return fact


def _unquote(v):
    if isinstance(v, str) and len(v) >= 2 and v[0] == v[-1] == '"':
        return v[1:-1]
    return v


def _is_block_list(v) -> bool:
    return isinstance(v, list) and bool(v) and all(isinstance(x, dict) for x in v)


def flatten(obj, prefix: str = "", depth: int = 2) -> dict:
    if _is_block_list(obj):
        obj = obj[0]
    if not isinstance(obj, dict):
        return {prefix.rstrip("."): _unquote(obj)} if prefix else {}
    out: dict = {}
    for k, v in obj.items():
        if str(k).startswith("__"):
            continue
        key = f"{prefix}{k}"
        if isinstance(v, dict) or _is_block_list(v):
            if depth > 0:
                out.update(flatten(v, key + ".", depth - 1))
        elif isinstance(v, list):
            out[key] = [_unquote(x) for x in v]
        else:
            out[key] = _unquote(v)
    return out


# --- Dockerfile ---------------------------------------------------------------

def _exec_form(arg: str) -> str:
    if arg.startswith("["):
        try:
            return " ".join(str(x) for x in json.loads(arg))
        except json.JSONDecodeError:
            return arg
    return arg


def parse_dockerfile(snap: Snapshot, rel: str) -> ParsedArtifact:
    instrs: list[tuple[str, str, int]] = []
    buf, start = "", None
    for i, text in enumerate(snap.lines(rel), 1):
        s = text.strip()
        if not buf and (not s or s.startswith("#")):
            continue
        if start is None:
            start = i
        if s.endswith("\\"):
            buf += s[:-1].rstrip() + " "
            continue
        buf += s
        op, _, arg = buf.partition(" ")
        instrs.append((op.upper(), arg.strip(), start))
        buf, start = "", None
    art = ParsedArtifact("dockerfile", rel, True, objects=instrs)
    froms = [x for x in instrs if x[0] == "FROM"]
    if froms:
        art.settings.append(_fact(snap, rel, "base_image", froms[-1][1].split()[0], froms[-1][2]))
    art.settings.append(_fact(snap, rel, "stages", len(froms)))
    for key, op in (("user", "USER"), ("cmd", "CMD"), ("entrypoint", "ENTRYPOINT"),
                    ("expose", "EXPOSE"), ("healthcheck", "HEALTHCHECK")):
        found = [x for x in instrs if x[0] == op]
        if found:
            value = _exec_form(found[-1][1]) if op in ("CMD", "ENTRYPOINT") else found[-1][1]
            art.settings.append(_fact(snap, rel, key, value, found[-1][2]))
    return art


# --- compose ------------------------------------------------------------------

def parse_compose(snap: Snapshot, rel: str) -> ParsedArtifact:
    try:
        data = yaml.safe_load(snap.read(rel)) or {}
    except yaml.YAMLError:
        return ParsedArtifact("compose", rel, False)
    services = data.get("services") or {}
    art = ParsedArtifact("compose", rel, True,
                         objects=[(n, services[n] if isinstance(services[n], dict) else {}) for n in sorted(services)])
    for name, svc in art.objects:
        if "image" in svc:
            art.settings.append(_fact(snap, rel, f"services.{name}.image", svc["image"],
                                      line_of(snap, rel, f"image: {svc['image']}")))
        cmd = svc.get("command")
        if cmd:
            art.settings.append(_fact(snap, rel, f"services.{name}.command",
                                      " ".join(str(c) for c in cmd) if isinstance(cmd, list) else str(cmd)))
        if svc.get("ports"):
            art.settings.append(_fact(snap, rel, f"services.{name}.ports", [str(p) for p in svc["ports"]]))
    return art


# --- 플랫폼 설정 --------------------------------------------------------------

def parse_platform(snap: Snapshot, rel: str) -> ParsedArtifact:
    name = PurePosixPath(rel).name
    try:
        if name.endswith(".json"):
            data = json.loads(snap.read(rel) or "{}")
        elif name.endswith(".toml"):
            data = tomllib.loads(snap.read(rel))
        elif name.endswith((".yaml", ".yml")):
            data = yaml.safe_load(snap.read(rel)) or {}
        else:
            return ParsedArtifact("platform-config", rel, False)
    except (json.JSONDecodeError, tomllib.TOMLDecodeError, yaml.YAMLError):
        return ParsedArtifact("platform-config", rel, False)
    art = ParsedArtifact("platform-config", rel, True, objects=[(name, data)])
    for key, value in sorted(flatten(data).items()):
        art.settings.append(_fact(snap, rel, key, value))
    return art


# --- CI -----------------------------------------------------------------------

def parse_ci(snap: Snapshot, rel: str) -> ParsedArtifact:
    try:
        data = yaml.safe_load(snap.read(rel)) or {}
    except yaml.YAMLError:
        return ParsedArtifact("ci", rel, False)
    jobs = data.get("jobs") or {}
    uses = sorted({step["uses"] for job in jobs.values() if isinstance(job, dict)
                   for step in job.get("steps") or [] if isinstance(step, dict) and "uses" in step})
    art = ParsedArtifact("ci", rel, True, objects=[("workflow", data)])
    art.settings.append(_fact(snap, rel, "jobs", sorted(jobs)))
    art.settings.append(_fact(snap, rel, "uses", uses))
    return art


# --- 분류 ---------------------------------------------------------------------

def _classify(rel: str) -> str | None:
    p = PurePosixPath(rel)
    name = p.name
    if name == "Dockerfile" or name.startswith("Dockerfile.") or name.endswith(".Dockerfile"):
        return "dockerfile"
    if name in PLATFORM_FILES or rel == ".railway/railway.ts":
        return "platform-config"
    if rel.startswith(".github/workflows/") and name.endswith((".yml", ".yaml")):
        return "ci"
    if name.endswith((".yml", ".yaml")) and (name.startswith("docker-compose") or name.startswith("compose")):
        return "compose"
    if name.endswith(".tf"):
        return "terraform"
    if name.endswith((".yml", ".yaml")):
        return "k8s?"
    return None


def parse_artifacts(snap: Snapshot) -> list[ParsedArtifact]:
    out: list[ParsedArtifact] = []
    for rel in snap.files:
        kind = _classify(rel)
        if kind == "dockerfile":
            out.append(parse_dockerfile(snap, rel))
        elif kind == "compose":
            out.append(parse_compose(snap, rel))
        elif kind == "platform-config":
            out.append(parse_platform(snap, rel))
        elif kind == "ci":
            out.append(parse_ci(snap, rel))
    return sorted(out, key=lambda a: a.path)
```

> `.railway/railway.ts`는 TypeScript라서 파싱하지 않고 `parsed: false`로만 기록된다(`parse_platform`의 마지막 분기).

- [ ] **Step 4: 테스트 통과 확인**

Run: `uv run pytest tests/detect/test_artifacts_basic.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: 커밋**

```bash
git add infrafit/detect/artifacts.py tests/detect/test_artifacts_basic.py
git commit -m "feat: parse Dockerfile, compose, platform configs and CI workflows"
```

---

### Task 9: 기존 산출물 파서 — 쿠버네티스, Terraform

**Files:**
- Modify: `infrafit/detect/artifacts.py`
- Test: `tests/detect/test_artifacts_k8s_tf.py`

**Interfaces:**
- Consumes: `ParsedArtifact`, `flatten`, `_fact` (Task 8)
- Produces:
  - `infrafit.detect.artifacts.pod_spec(doc: dict) -> dict` — Deployment·StatefulSet·DaemonSet·Job·CronJob의 Pod spec(없으면 `{}`)
  - `infrafit.detect.artifacts.ingress_backends(doc: dict) -> list[str]` — Ingress가 가리키는 서비스 이름(정렬)
  - `parse_artifacts`가 k8s와 terraform도 낸다.
  - 설정 키 규칙: k8s `<Kind>/<이름>.<키>` — `replicas`, `terminationGracePeriodSeconds`, `image`, `command`(command + args), `readinessProbe`, `livenessProbe`, `preStop`(불리언), `schedule`, `concurrencyPolicy`, `ingressClassName`, `annotations.<키>`, `backends`, `minReplicas`, `maxReplicas`, `minAvailable`, `maxUnavailable` / terraform `<타입>.<이름>.<flatten 키>`, `provider.<이름>[.<alias>].region`
  - 제한: kustomize 패치 파일도 원문 그대로 파싱한다. 패치에 없는 필드는 "없음"으로 보이므로, 기본값 적용(Task 10)은 첫 컨테이너에 `image`가 있는 완전한 객체에만 한다. `kustomize build` 기반 파싱은 이 계획 범위 밖이다.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/detect/test_artifacts_k8s_tf.py`:
```python
from infrafit.detect.artifacts import parse_artifacts
from infrafit.repo import open_snapshot

K8S = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 2
  template:
    spec:
      terminationGracePeriodSeconds: 45
      containers:
        - name: api
          image: example/api:1
          command: ["uvicorn", "main:app"]
          args: ["--timeout-keep-alive", "75"]
          readinessProbe: {httpGet: {path: /healthz, port: 8000}}
          lifecycle: {preStop: {exec: {command: ["sleep", "10"]}}}
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web
  annotations:
    alb.ingress.kubernetes.io/load-balancer-attributes: idle_timeout.timeout_seconds=120
spec:
  ingressClassName: alb
  rules:
    - http:
        paths:
          - backend: {service: {name: api, port: {number: 80}}}
"""

TF = """provider "aws" {
  region = "ap-northeast-2"
}

resource "aws_db_instance" "main" {
  engine   = "postgres"
  multi_az = true
}

resource "google_sql_database_instance" "pg" {
  database_version = "POSTGRES_16"
  settings {
    availability_type = "REGIONAL"
  }
}
"""


def _snap(tmp_path):
    (tmp_path / "k8s").mkdir()
    (tmp_path / "k8s" / "app.yaml").write_text(K8S)
    (tmp_path / "k8s" / "not-k8s.yaml").write_text("foo: bar\n")
    (tmp_path / "main.tf").write_text(TF)
    return open_snapshot(str(tmp_path), tmp_path / "_w")


def test_k8s_settings(tmp_path):
    arts = {a.path: a for a in parse_artifacts(_snap(tmp_path))}
    assert "k8s/not-k8s.yaml" not in arts
    k = arts["k8s/app.yaml"]
    assert k.kind == "k8s"
    assert k.get("Deployment/api.replicas") == 2
    assert k.get("Deployment/api.terminationGracePeriodSeconds") == 45
    assert k.get("Deployment/api.command") == "uvicorn main:app --timeout-keep-alive 75"
    assert k.get("Deployment/api.readinessProbe") is True
    assert k.get("Deployment/api.livenessProbe") is False
    assert k.get("Deployment/api.preStop") is True
    assert k.get("Ingress/web.ingressClassName") == "alb"
    assert k.get("Ingress/web.backends") == ["api"]
    assert k.get("Ingress/web.annotations.alb.ingress.kubernetes.io/load-balancer-attributes") == \
        "idle_timeout.timeout_seconds=120"


def test_terraform_settings(tmp_path):
    arts = {a.path: a for a in parse_artifacts(_snap(tmp_path))}
    t = arts["main.tf"]
    assert t.kind == "terraform" and t.parsed
    assert t.get("aws_db_instance.main.engine") == "postgres"
    assert t.get("aws_db_instance.main.multi_az") is True
    assert t.get("google_sql_database_instance.pg.settings.availability_type") == "REGIONAL"
    assert t.get("provider.aws.region") == "ap-northeast-2"
    assert ("aws_db_instance", "main") in [(o[0], o[1]) for o in t.objects]
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `uv run pytest tests/detect/test_artifacts_k8s_tf.py -v`
Expected: FAIL (k8s·terraform 산출물이 없음)

- [ ] **Step 3: 구현** — `infrafit/detect/artifacts.py`에 추가

파일 위 import에 `import hcl2` 추가. 그리고 `parse_ci` 아래에 추가:
```python
# --- 쿠버네티스 ---------------------------------------------------------------

def pod_spec(doc: dict) -> dict:
    kind = doc.get("kind")
    spec = doc.get("spec") or {}
    if kind == "CronJob":
        spec = ((spec.get("jobTemplate") or {}).get("spec")) or {}
    if kind in ("Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob"):
        return ((spec.get("template") or {}).get("spec")) or {}
    return {}


def ingress_backends(doc: dict) -> list[str]:
    spec = doc.get("spec") or {}
    names = set()
    default = ((spec.get("defaultBackend") or {}).get("service") or {}).get("name")
    if default:
        names.add(default)
    for rule in spec.get("rules") or []:
        for path in ((rule or {}).get("http") or {}).get("paths") or []:
            name = (((path or {}).get("backend") or {}).get("service") or {}).get("name")
            if name:
                names.add(name)
    return sorted(names)


def _k8s_settings(snap: Snapshot, rel: str, doc: dict) -> list[dict]:
    kind = doc["kind"]
    meta = doc.get("metadata") or {}
    prefix = f"{kind}/{meta.get('name', '?')}"
    spec = doc.get("spec") or {}
    out: list[dict] = []

    def add(key: str, value) -> None:
        out.append(_fact(snap, rel, f"{prefix}.{key}", value))

    if kind in ("Deployment", "StatefulSet") and "replicas" in spec:
        add("replicas", spec["replicas"])
    pod = pod_spec(doc)
    if pod:
        if "terminationGracePeriodSeconds" in pod:
            add("terminationGracePeriodSeconds", pod["terminationGracePeriodSeconds"])
        containers = pod.get("containers") or []
        if containers:
            c = containers[0]
            if c.get("image"):
                add("image", c["image"])
            cmd = [str(x) for x in (c.get("command") or []) + (c.get("args") or [])]
            if cmd:
                add("command", " ".join(cmd))
            add("readinessProbe", "readinessProbe" in c)
            add("livenessProbe", "livenessProbe" in c)
            add("preStop", bool((c.get("lifecycle") or {}).get("preStop")))
    if kind == "CronJob":
        for key in ("schedule", "concurrencyPolicy"):
            if key in spec:
                add(key, spec[key])
    if kind == "Ingress":
        annotations = meta.get("annotations") or {}
        cls = spec.get("ingressClassName") or annotations.get("kubernetes.io/ingress.class")
        if cls:
            add("ingressClassName", cls)
        for k, v in sorted(annotations.items()):
            add(f"annotations.{k}", v)
        add("backends", ingress_backends(doc))
    if kind == "HorizontalPodAutoscaler":
        for key in ("minReplicas", "maxReplicas"):
            if key in spec:
                add(key, spec[key])
    if kind == "PodDisruptionBudget":
        for key in ("minAvailable", "maxUnavailable"):
            if key in spec:
                add(key, spec[key])
    return out


def parse_k8s(snap: Snapshot, rel: str) -> ParsedArtifact | None:
    try:
        docs = [d for d in yaml.safe_load_all(snap.read(rel)) if isinstance(d, dict)]
    except yaml.YAMLError:
        return None
    docs = [d for d in docs if "kind" in d and "apiVersion" in d]
    if not docs:
        return None
    art = ParsedArtifact("k8s", rel, True, objects=docs)
    for doc in docs:
        art.settings.extend(_k8s_settings(snap, rel, doc))
    return art


# --- Terraform ----------------------------------------------------------------

def parse_terraform(snap: Snapshot, rel: str) -> ParsedArtifact:
    try:
        data = hcl2.loads(snap.read(rel))
    except Exception:  # python-hcl2는 파싱 오류마다 다른 예외를 낸다
        return ParsedArtifact("terraform", rel, False)
    art = ParsedArtifact("terraform", rel, True)
    for block in data.get("resource") or []:
        for rtype, named in block.items():
            for rname, attrs in named.items():
                attrs = attrs[0] if isinstance(attrs, list) and attrs else attrs
                art.objects.append((rtype, rname, attrs))
                for key, value in sorted(flatten(attrs).items()):
                    art.settings.append(_fact(snap, rel, f"{rtype}.{rname}.{key}", value))
    for block in data.get("provider") or []:
        for pname, attrs in block.items():
            attrs = attrs[0] if isinstance(attrs, list) and attrs else attrs
            region = _unquote(attrs.get("region"))
            alias = _unquote(attrs.get("alias"))
            if region:
                key = f"provider.{pname}.{alias}.region" if alias else f"provider.{pname}.region"
                art.settings.append(_fact(snap, rel, key, region))
    return art
```

`parse_artifacts`의 반복문에 분기 두 개를 추가:
```python
        elif kind == "terraform":
            out.append(parse_terraform(snap, rel))
        elif kind == "k8s?":
            art = parse_k8s(snap, rel)
            if art is not None:
                out.append(art)
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `uv run pytest tests/detect/ -v`
Expected: PASS (전체 통과)

- [ ] **Step 5: 커밋**

```bash
git add infrafit/detect/artifacts.py tests/detect/test_artifacts_k8s_tf.py
git commit -m "feat: parse Kubernetes manifests and Terraform resources"
```

---

### Task 9b: kustomize overlay 렌더링

kustomize 패치 파일만 원문으로 읽으면 패치에 없는 필드가 "없음"으로 보인다. 그래서 다른 kustomization에서 참조되지 않는 **최종 overlay**마다 `kustomize build`(없으면 `kubectl kustomize`) 결과를 따로 파싱한다. 원문 파싱은 근거 줄을 위해 그대로 둔다.

**Files:**
- Modify: `infrafit/detect/artifacts.py`
- Test: `tests/detect/test_kustomize.py`

**Interfaces:**
- Consumes: `ParsedArtifact`, `_k8s_settings` (Task 9), `parent_dir` (Task 5)
- Produces:
  - `infrafit.detect.artifacts.kustomize_binary() -> list[str] | None` — `["kustomize", "build"]` 또는 `["kubectl", "kustomize"]`, 둘 다 없으면 `None`
  - `infrafit.detect.artifacts.kustomize_leaves(snap) -> list[str]` — kustomization 디렉터리 중 다른 kustomization의 `resources`·`bases`·`components`에서 참조되지 않는 것(정렬)
  - `infrafit.detect.artifacts.build_overlays(snap, runner=subprocess.run) -> list[ParsedArtifact]` — 최종 overlay마다 kind `k8s`, path `<디렉터리>/kustomization.yaml#build`. 빌드가 실패하면 `parsed: False`
  - `parse_artifacts`가 렌더링 결과도 함께 낸다
- 환경: 개발 기계에 `kustomize`가 있어야 F1 골든이 맞는다(`brew install kustomize`). 없으면 렌더링 테스트는 건너뛴다.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/detect/test_kustomize.py`:
```python
import pytest

from infrafit.detect.artifacts import build_overlays, kustomize_binary, kustomize_leaves
from infrafit.repo import open_snapshot

BASE = """apiVersion: apps/v1
kind: Deployment
metadata: {name: api}
spec:
  template:
    spec:
      containers: [{name: api, image: acme/api:1}]
"""
PATCH = """apiVersion: apps/v1
kind: Deployment
metadata: {name: api}
spec:
  template:
    spec:
      terminationGracePeriodSeconds: 45
"""


def _tree(tmp_path):
    files = {
        "k8s/base/kustomization.yaml": "resources: [api.yaml]\n",
        "k8s/base/api.yaml": BASE,
        "k8s/components/extra/kustomization.yaml": "apiVersion: kustomize.config.k8s.io/v1alpha1\nkind: Component\n",
        "k8s/overlays/prod/kustomization.yaml": "resources: [../../base]\npatches: [{path: patch.yaml}]\n",
        "k8s/overlays/prod/patch.yaml": PATCH,
        "k8s/overlays/dev/kustomization.yaml": "resources: [../../base]\ncomponents: [../../components/extra]\n",
    }
    for rel, text in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    return open_snapshot(str(tmp_path), tmp_path / "_w")


def test_leaves_exclude_referenced_dirs(tmp_path):
    assert kustomize_leaves(_tree(tmp_path)) == ["k8s/overlays/dev", "k8s/overlays/prod"]


def test_build_failure_is_recorded(tmp_path):
    class Failed:
        returncode = 1
        stdout = ""

    arts = build_overlays(_tree(tmp_path), runner=lambda *a, **k: Failed())
    if kustomize_binary() is None:
        assert arts == []
    else:
        assert [(a.path, a.parsed) for a in arts] == [
            ("k8s/overlays/dev/kustomization.yaml#build", False),
            ("k8s/overlays/prod/kustomization.yaml#build", False)]


@pytest.mark.skipif(kustomize_binary() is None, reason="kustomize 없음")
def test_build_renders_patched_objects(tmp_path):
    arts = {a.path: a for a in build_overlays(_tree(tmp_path))}
    prod = arts["k8s/overlays/prod/kustomization.yaml#build"]
    assert prod.parsed
    assert prod.get("Deployment/api.terminationGracePeriodSeconds") == 45
    assert prod.get("Deployment/api.image") == "acme/api:1"
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `uv run pytest tests/detect/test_kustomize.py -v`
Expected: FAIL (`ImportError`)

- [ ] **Step 3: 구현** — `infrafit/detect/artifacts.py`에 추가

파일 위 import에 `import posixpath`, `import shutil`, `import subprocess`, `from infrafit.detect.manifests import parent_dir`를 추가하고, `parse_terraform` 아래에:
```python
# --- kustomize ----------------------------------------------------------------

KUSTOMIZATION_NAMES = ("kustomization.yaml", "kustomization.yml", "Kustomization")


def kustomize_binary() -> list[str] | None:
    if shutil.which("kustomize"):
        return ["kustomize", "build"]
    if shutil.which("kubectl"):
        return ["kubectl", "kustomize"]
    return None


def _kustomization_files(snap: Snapshot) -> dict[str, str]:
    """디렉터리 → kustomization 파일 경로."""
    out: dict[str, str] = {}
    for rel in snap.files:
        if PurePosixPath(rel).name in KUSTOMIZATION_NAMES:
            out.setdefault(parent_dir(rel), rel)
    return out


def kustomize_leaves(snap: Snapshot) -> list[str]:
    files = _kustomization_files(snap)
    referenced: set[str] = set()
    for d, rel in files.items():
        try:
            data = yaml.safe_load(snap.read(rel)) or {}
        except yaml.YAMLError:
            continue
        for key in ("resources", "bases", "components"):
            for item in data.get(key) or []:
                target = posixpath.normpath(posixpath.join(d, str(item)))
                if target in files:
                    referenced.add(target)
    return sorted(d for d in files if d not in referenced)


def build_overlays(snap: Snapshot, runner=subprocess.run) -> list[ParsedArtifact]:
    cmd = kustomize_binary()
    if cmd is None:
        return []
    out: list[ParsedArtifact] = []
    for d in kustomize_leaves(snap):
        rel = f"{d}/kustomization.yaml#build" if d else "kustomization.yaml#build"
        result = runner(cmd + [str(snap.root / d)], capture_output=True, text=True)
        if result.returncode != 0:
            out.append(ParsedArtifact("k8s", rel, False))
            continue
        try:
            docs = [x for x in yaml.safe_load_all(result.stdout)
                    if isinstance(x, dict) and "kind" in x and "apiVersion" in x]
        except yaml.YAMLError:
            out.append(ParsedArtifact("k8s", rel, False))
            continue
        art = ParsedArtifact("k8s", rel, True, objects=docs)
        for doc in docs:
            art.settings.extend(_k8s_settings(snap, rel, doc))
        out.append(art)
    return out
```

`parse_artifacts`의 `return sorted(out, key=lambda a: a.path)` 바로 앞에 한 줄 추가:
```python
    out.extend(build_overlays(snap))
```

> `_k8s_settings`는 줄 번호 없이 `_fact`를 부르므로, `#build`가 붙은 가상의 경로를 넘겨도 파일을 읽지 않는다.

- [ ] **Step 4: 테스트 통과 확인**

Run: `uv run pytest tests/detect/ -v`
Expected: PASS (kustomize가 없으면 `test_build_renders_patched_objects`만 SKIP)

- [ ] **Step 5: 커밋**

```bash
git add infrafit/detect/artifacts.py tests/detect/test_kustomize.py
git commit -m "feat: render kustomize leaf overlays and parse the built manifests"
```

---

### Task 10: 기본값 사실

**Files:**
- Create: `infrafit/detect/defaults.py`
- Test: `tests/detect/test_defaults.py`

**Interfaces:**
- Consumes: `ParsedArtifact`, `pod_spec` (Task 8~9), 기본값 형식 (Task 6)
- Produces:
  - `infrafit.detect.defaults.apply_defaults(artifacts: list[ParsedArtifact], entries) -> None` — 없는 키에 `{key, value, defaulted: True, default_source}`를 추가
  - `infrafit.detect.defaults.hop_settings(component: str, explicit: dict, entries) -> list[dict]` — 구간 설정: `explicit`(키 → 값)은 `defaulted: False`로, 기본값 표의 나머지 키는 `defaulted: True`로. key로 정렬

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/detect/test_defaults.py`:
```python
from infrafit.detect.artifacts import ParsedArtifact
from infrafit.detect.defaults import apply_defaults, hop_settings

SRC = {"ref": "docs/x.md"}
ENTRIES = (
    {"artifact": "dockerfile", "key": "user", "value": "root", "source": SRC},
    {"artifact": "k8s", "match_kind": "Deployment", "key": "terminationGracePeriodSeconds", "value": 30, "source": SRC},
    {"artifact": "terraform", "resource": "aws_db_instance", "key": "multi_az", "value": False, "source": SRC},
    {"artifact": "hop", "component": "nw:app/uvicorn/default", "key": "timeout_keep_alive", "value": 5, "source": SRC},
)


def test_dockerfile_default_added_only_when_missing():
    a = ParsedArtifact("dockerfile", "Dockerfile", True, settings=[])
    b = ParsedArtifact("dockerfile", "b/Dockerfile", True,
                       settings=[{"key": "user", "value": "app", "defaulted": False}])
    apply_defaults([a, b], ENTRIES)
    assert a.settings == [{"key": "user", "value": "root", "defaulted": True, "default_source": SRC}]
    assert b.get("user") == "app"


def test_k8s_default_only_for_full_objects():
    full = {"kind": "Deployment", "metadata": {"name": "api"},
            "spec": {"template": {"spec": {"containers": [{"name": "api", "image": "acme/api:1"}]}}}}
    patch = {"kind": "Deployment", "metadata": {"name": "web"},
             "spec": {"template": {"spec": {"containers": [{"name": "web", "resources": {}}]}}}}
    a = ParsedArtifact("k8s", "k.yaml", True, objects=[full, patch])
    apply_defaults([a], ENTRIES)
    assert a.get("Deployment/api.terminationGracePeriodSeconds") == 30
    assert a.get("Deployment/web.terminationGracePeriodSeconds") is None


def test_terraform_default_per_resource():
    a = ParsedArtifact("terraform", "main.tf", True, objects=[("aws_db_instance", "main", {})])
    apply_defaults([a], ENTRIES)
    assert a.get("aws_db_instance.main.multi_az") is False


def test_hop_settings_mix_explicit_and_default():
    assert hop_settings("nw:app/uvicorn/default", {}, ENTRIES) == [
        {"key": "timeout_keep_alive", "value": 5, "defaulted": True, "default_source": SRC}]
    assert hop_settings("nw:app/uvicorn/default", {"timeout_keep_alive": 75}, ENTRIES) == [
        {"key": "timeout_keep_alive", "value": 75, "defaulted": False}]
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `uv run pytest tests/detect/test_defaults.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: 구현**

`infrafit/detect/defaults.py`:
```python
"""설정이 없을 때 적용되는 기본값을 사실로 기록한다(설계 §6.5)."""

from __future__ import annotations

from infrafit.detect.artifacts import ParsedArtifact, pod_spec


def _is_full_object(doc: dict) -> bool:
    """kustomize 패치가 아니라 완전한 객체인가. 패치는 보통 이미지가 없다."""
    if doc.get("kind") == "CronJob":
        return "schedule" in (doc.get("spec") or {})
    containers = pod_spec(doc).get("containers") or []
    return bool(containers) and bool(containers[0].get("image"))


def _target_keys(art: ParsedArtifact, entry: dict) -> list[str]:
    if art.kind == "dockerfile":
        return [entry["key"]]
    if art.kind == "k8s":
        return [f"{d['kind']}/{(d.get('metadata') or {}).get('name', '?')}.{entry['key']}"
                for d in art.objects if d.get("kind") == entry["match_kind"] and _is_full_object(d)]
    if art.kind == "terraform":
        return [f"{rtype}.{rname}.{entry['key']}" for (rtype, rname, _) in art.objects
                if rtype == entry["resource"]]
    return []


def apply_defaults(artifacts: list[ParsedArtifact], entries) -> None:
    for art in artifacts:
        present = {s["key"] for s in art.settings}
        for entry in entries:
            if entry["artifact"] != art.kind:
                continue
            for key in _target_keys(art, entry):
                if key not in present:
                    art.settings.append({"key": key, "value": entry["value"], "defaulted": True,
                                         "default_source": entry["source"]})
                    present.add(key)


def hop_settings(component: str, explicit: dict, entries) -> list[dict]:
    out = [{"key": k, "value": v, "defaulted": False} for k, v in explicit.items()]
    for entry in entries:
        if entry["artifact"] == "hop" and entry["component"] == component and entry["key"] not in explicit:
            out.append({"key": entry["key"], "value": entry["value"], "defaulted": True,
                        "default_source": entry["source"]})
    return sorted(out, key=lambda s: s["key"])
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `uv run pytest tests/detect/test_defaults.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: 커밋**

```bash
git add infrafit/detect/defaults.py tests/detect/test_defaults.py
git commit -m "feat: record defaulted settings from the defaults table"
```

---

### Task 11: 워크로드 찾기

**Files:**
- Create: `infrafit/detect/workloads.py`
- Test: `tests/detect/test_workloads.py`

**Interfaces:**
- Consumes: `Snapshot`, `evidence`, `line_of`; `Manifests`, `parent_dir` (Task 5); `ParsedArtifact`, `pod_spec` (Task 8~9)
- Produces:
  - `infrafit.detect.workloads.WorkloadInfo` — `@dataclass`: `id`, `kind`, `name`, `entrypoint: dict`, `status`, `source`(`k8s` | `compose` | `code`), `app_dir: str = ""`, `command: str = ""`, `image: str = ""`, `code_root: str | None = None`; `to_dict()`는 `{id, kind, name, entrypoint, status}`만 낸다
  - `code_root`(이 워크로드의 코드가 있는 디렉터리, `""` = 저장소 전체, `None` = 모름): 코드 워크로드는 `app_dir`, k8s 워크로드는 이미지 이름의 마지막 조각과 디렉터리 이름이 같은 Dockerfile의 디렉터리, compose 워크로드는 `build`의 Dockerfile 디렉터리(또는 context) → 없으면 이미지 규칙. 데이터 범위의 `used_by` 판정(Task 13)이 쓴다
  - `infrafit.detect.workloads.detect_workloads(snap, manifests, artifacts) -> list[WorkloadInfo]` — id 순 정렬
  - 규칙(우선순위대로 하나만 사용):
    1. k8s에 Deployment·StatefulSet·Job·CronJob이 있으면 그것들. 이름으로 중복 제거(경로 순 첫 번째). 이미지 이름에 `postgres`, `redis`, `mysql`, `mongo`, `valkey`, `memcached`, `rabbitmq`, `minio`, `localstack`이 들어가면 제외. 종류: CronJob → `scheduled`, Job → 이름이나 명령에 `migrat`가 있으면 `migration-job` 아니면 `worker`, 그 외 → 이름이나 명령에 `worker`가 있으면 `worker`, 아니면 `web`
    2. compose 서비스가 있으면 그것들(같은 이미지 제외 규칙). 종류: 이름이나 명령에 `migrat` → `migration-job`, `worker` → `worker`, 아니면 `web`
    3. 코드: 디렉터리별 프레임워크 의존성 — `next`, `express`, `fastify`, `koa`, `@nestjs/core`, `hono`, `fastapi`, `flask`, `django` → `web`; 서버 프레임워크 없이 `vite`만 → `static-frontend`. `Procfile`의 `web` / `worker` / `clock` / `release`는 `web` / `worker` / `scheduled` / `migration-job`(같은 디렉터리·종류면 합침)
  - ID: k8s·compose는 `w-<이름 slug>`. 코드는 종류마다 하나면 `w-<종류>`(`static-frontend`는 `w-static`), 여러 개면 `w-<종류>-<디렉터리 slug>`
  - 실행 명령(`command`) 우선순위: k8s 컨테이너 command+args → (k8s 이미지 이름의 마지막 조각과 디렉터리 이름이 같은 Dockerfile의 CMD) → compose command → 코드 워크로드는 웹이면 `app_dir`(없으면 루트)의 Dockerfile CMD → Procfile 같은 종류 → package.json `start` 스크립트, 웹이 아니면 Procfile 같은 종류만

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/detect/test_workloads.py`:
```python
import json

from infrafit.detect.artifacts import parse_artifacts
from infrafit.detect.manifests import parse_manifests
from infrafit.detect.workloads import detect_workloads
from infrafit.repo import open_snapshot


def _run(tmp_path):
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    return detect_workloads(snap, parse_manifests(snap), parse_artifacts(snap))


def _write(tmp_path, rel, text):
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def test_code_workloads_merge_procfile_and_prefer_dockerfile_command(tmp_path):
    _write(tmp_path, "requirements.txt", "flask==3.0\n")
    _write(tmp_path, "Procfile", "web: gunicorn app:app\nworker: python worker.py\n")
    _write(tmp_path, "Dockerfile", 'FROM python:3.12\nCMD ["flask", "run"]\n')
    ws = _run(tmp_path)
    assert [(w.id, w.kind) for w in ws] == [("w-web", "web"), ("w-worker", "worker")]
    web = ws[0]
    assert web.command == "flask run"
    assert web.entrypoint["path"] == "requirements.txt"
    assert web.code_root == ""
    assert ws[1].command == "python worker.py"


def test_static_frontend_and_multiple_dirs(tmp_path):
    _write(tmp_path, "frontend/package.json", json.dumps({"devDependencies": {"vite": "^5"}}))
    _write(tmp_path, "api/package.json", json.dumps({"dependencies": {"express": "^4"}, "scripts": {"start": "node server.js"}}))
    _write(tmp_path, "admin/package.json", json.dumps({"dependencies": {"express": "^4"}}))
    ws = _run(tmp_path)
    assert [(w.id, w.kind) for w in ws] == [
        ("w-static", "static-frontend"), ("w-web-admin", "web"), ("w-web-api", "web")]
    assert next(w for w in ws if w.id == "w-web-api").command == "node server.js"


def test_k8s_takes_priority_and_skips_infra_images(tmp_path):
    _write(tmp_path, "package.json", json.dumps({"dependencies": {"express": "^4"}}))
    _write(tmp_path, "k8s/app.yaml", """apiVersion: apps/v1
kind: Deployment
metadata: {name: api}
spec: {template: {spec: {containers: [{name: api, image: acme/api:1}]}}}
---
apiVersion: apps/v1
kind: Deployment
metadata: {name: queue-worker}
spec: {template: {spec: {containers: [{name: w, image: acme/api:1, command: [node, worker.js]}]}}}
---
apiVersion: apps/v1
kind: StatefulSet
metadata: {name: db}
spec: {template: {spec: {containers: [{name: db, image: postgres:16}]}}}
---
apiVersion: batch/v1
kind: Job
metadata: {name: db-migrate}
spec: {template: {spec: {containers: [{name: m, image: acme/api:1}]}}}
""")
    _write(tmp_path, "services/api/Dockerfile", 'FROM node:22\nCMD ["node", "server.js"]\n')
    ws = _run(tmp_path)
    assert [(w.id, w.kind) for w in ws] == [
        ("w-api", "web"), ("w-db-migrate", "migration-job"), ("w-queue-worker", "worker")]
    assert ws[0].command == "node server.js"
    assert ws[2].command == "node worker.js"
    assert ws[0].entrypoint["path"] == "k8s/app.yaml"
    assert ws[0].code_root == "services/api"


def test_compose_code_root_from_build(tmp_path):
    _write(tmp_path, "docker-compose.yml", """services:
  api:
    build: {context: ., dockerfile: services/api/Dockerfile}
  web:
    build: ./web
  db:
    image: postgres:16
""")
    ws = {w.id: w for w in _run(tmp_path)}
    assert set(ws) == {"w-api", "w-web"}
    assert ws["w-api"].code_root == "services/api"
    assert ws["w-web"].code_root == "web"
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `uv run pytest tests/detect/test_workloads.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: 구현**

`infrafit/detect/workloads.py`:
```python
"""워크로드(프로세스 단위) 찾기: k8s > compose > 코드 순서로 하나를 쓴다."""

from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass
from pathlib import PurePosixPath

from infrafit.detect.artifacts import ParsedArtifact, pod_spec
from infrafit.detect.manifests import Manifests, parent_dir
from infrafit.evidence import evidence, line_of
from infrafit.repo import Snapshot

INFRA_IMAGE_TOKENS = ("postgres", "redis", "mysql", "mongo", "valkey", "memcached", "rabbitmq", "minio", "localstack")
WEB_FRAMEWORKS = ("next", "express", "fastify", "koa", "@nestjs/core", "hono", "fastapi", "flask", "django")
PROC_KINDS = {"web": "web", "worker": "worker", "clock": "scheduled", "release": "migration-job"}


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9.-]+", "-", text.lower()).strip("-") or "root"


@dataclass
class WorkloadInfo:
    id: str
    kind: str
    name: str
    entrypoint: dict
    status: str
    source: str
    app_dir: str = ""
    command: str = ""
    image: str = ""
    code_root: str | None = None

    def to_dict(self) -> dict:
        return {"id": self.id, "kind": self.kind, "name": self.name,
                "entrypoint": self.entrypoint, "status": self.status}


def _dockerfiles(artifacts: list[ParsedArtifact]) -> list[ParsedArtifact]:
    return [a for a in artifacts if a.kind == "dockerfile"]


def _dockerfile_for_image(image: str, artifacts: list[ParsedArtifact]) -> ParsedArtifact | None:
    last = image.split("/")[-1].split(":")[0].split("@")[0]
    for df in _dockerfiles(artifacts):
        if last and PurePosixPath(df.path).parent.name == last:
            return df
    return None


def _dockerfile_cmd_for_image(image: str, artifacts: list[ParsedArtifact]) -> str:
    df = _dockerfile_for_image(image, artifacts)
    return (df.get("cmd") or "") if df else ""


def _code_root_for_image(image: str, artifacts: list[ParsedArtifact]) -> str | None:
    df = _dockerfile_for_image(image, artifacts)
    return parent_dir(df.path) if df else None


def _compose_code_root(compose_path: str, svc: dict, image: str, artifacts: list[ParsedArtifact]) -> str | None:
    build = svc.get("build")
    base = parent_dir(compose_path)
    if isinstance(build, str):
        root = posixpath.normpath(posixpath.join(base, build))
        return "" if root == "." else root
    if isinstance(build, dict):
        context = posixpath.normpath(posixpath.join(base, str(build.get("context", "."))))
        context = "" if context == "." else context
        if build.get("dockerfile"):
            return parent_dir(posixpath.normpath(posixpath.join(context, str(build["dockerfile"]))))
        return context
    return _code_root_for_image(image, artifacts)


def _dockerfile_cmd_for_dir(app_dir: str, artifacts: list[ParsedArtifact]) -> str:
    for target in (app_dir, ""):
        for df in _dockerfiles(artifacts):
            if parent_dir(df.path) == target and df.get("cmd"):
                return df.get("cmd")
    return ""


def _is_infra(image: str) -> bool:
    return any(token in image.lower() for token in INFRA_IMAGE_TOKENS)


def _from_k8s(snap: Snapshot, artifacts: list[ParsedArtifact]) -> list[WorkloadInfo]:
    seen: dict[str, WorkloadInfo] = {}
    for art in artifacts:
        if art.kind != "k8s":
            continue
        for doc in art.objects:
            kind = doc.get("kind")
            if kind not in ("Deployment", "StatefulSet", "Job", "CronJob"):
                continue
            name = (doc.get("metadata") or {}).get("name")
            containers = pod_spec(doc).get("containers") or []
            if not name or name in seen or not containers:
                continue
            c = containers[0]
            image = str(c.get("image") or "")
            if _is_infra(image):
                continue
            cmd = " ".join(str(x) for x in (c.get("command") or []) + (c.get("args") or []))
            text = f"{name} {cmd}".lower()
            if kind == "CronJob":
                wkind = "scheduled"
            elif kind == "Job":
                wkind = "migration-job" if "migrat" in text else "worker"
            else:
                wkind = "worker" if "worker" in text else "web"
            line = line_of(snap, art.path, f"name: {name}")
            seen[name] = WorkloadInfo(
                id=f"w-{slug(name)}", kind=wkind, name=name, entrypoint=evidence(snap, art.path, line),
                status="confirmed", source="k8s", image=image,
                command=cmd or _dockerfile_cmd_for_image(image, artifacts),
                code_root=_code_root_for_image(image, artifacts))
    return list(seen.values())


def _from_compose(snap: Snapshot, artifacts: list[ParsedArtifact]) -> list[WorkloadInfo]:
    out: list[WorkloadInfo] = []
    names: set[str] = set()
    for art in artifacts:
        if art.kind != "compose":
            continue
        for name, svc in art.objects:
            image = str(svc.get("image") or "")
            if name in names or _is_infra(image):
                continue
            names.add(name)
            cmd = svc.get("command") or ""
            cmd = " ".join(str(x) for x in cmd) if isinstance(cmd, list) else str(cmd)
            text = f"{name} {cmd}".lower()
            wkind = "migration-job" if "migrat" in text else "worker" if "worker" in text else "web"
            out.append(WorkloadInfo(
                id=f"w-{slug(name)}", kind=wkind, name=name,
                entrypoint=evidence(snap, art.path, line_of(snap, art.path, f"{name}:")),
                status="confirmed", source="compose", image=image, command=cmd,
                code_root=_compose_code_root(art.path, svc, image, artifacts)))
    return out


def _from_code(snap: Snapshot, manifests: Manifests, artifacts: list[ParsedArtifact]) -> list[WorkloadInfo]:
    found: dict[tuple[str, str], dict] = {}
    for d, deps in sorted(manifests.deps_by_dir.items()):
        web_fw = next((fw for fw in WEB_FRAMEWORKS if fw in deps), None)
        if web_fw:
            found[("web", d)] = {"dep": web_fw}
        elif "vite" in deps:
            found[("static-frontend", d)] = {"dep": "vite"}
    for key, (cmd, rel, line) in sorted(manifests.procfile.items()):
        d, proc = key.split(":", 1)
        wkind = PROC_KINDS.get(proc)
        if not wkind:
            continue
        entry = found.setdefault((wkind, d), {})
        entry.setdefault("proc", (cmd, rel, line))

    by_kind: dict[str, list[str]] = {}
    for wkind, d in found:
        by_kind.setdefault(wkind, []).append(d)

    out: list[WorkloadInfo] = []
    for (wkind, d), info in sorted(found.items()):
        short = "static" if wkind == "static-frontend" else wkind
        wid = f"w-{short}" if len(by_kind[wkind]) == 1 else f"w-{short}-{slug(d)}"
        if "dep" in info:
            dep = info["dep"]
            rel, line = manifests.deps[dep]
            # 같은 의존성이 여러 디렉터리에 있으면 이 디렉터리의 매니페스트 줄을 근거로 쓴다
            for pattern in ("package.json", "requirements.txt", "pyproject.toml"):
                local = f"{d}/{pattern}" if d else pattern
                if snap.exists(local):
                    ln = line_of(snap, local, f'"{dep}"' if pattern == "package.json" else dep)
                    if ln:
                        rel, line = local, ln
                        break
            entry = evidence(snap, rel, line)
        else:
            _, rel, line = info["proc"]
            entry = evidence(snap, rel, line)
        proc_cmd = info["proc"][0] if "proc" in info else ""
        start = manifests.scripts.get(f"{d}:start")
        start_cmd = start[0] if start else ""
        if wkind == "web":
            # 이미지가 있으면 그 CMD가 실제로 배포되는 실행 명령이다
            command = _dockerfile_cmd_for_dir(d, artifacts) or proc_cmd or start_cmd
        else:
            command = proc_cmd
        out.append(WorkloadInfo(id=wid, kind=wkind, name=wid[2:], entrypoint=entry,
                                status="confirmed", source="code", app_dir=d, command=command, code_root=d))
    return out


def detect_workloads(snap: Snapshot, manifests: Manifests, artifacts: list[ParsedArtifact]) -> list[WorkloadInfo]:
    workloads = _from_k8s(snap, artifacts) or _from_compose(snap, artifacts) or _from_code(snap, manifests, artifacts)
    return sorted(workloads, key=lambda w: w.id)
```

> 웹 워크로드의 실행 명령은 Dockerfile CMD를 Procfile보다 우선한다. 이미지가 있으면 그것이 실제로 배포되는 명령이기 때문이다. 웹이 아닌 워크로드(워커 등)는 이미지 CMD가 보통 웹 서버이므로 Procfile 명령만 쓴다.

- [ ] **Step 4: 테스트 통과 확인**

Run: `uv run pytest tests/detect/test_workloads.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: 커밋**

```bash
git add infrafit/detect/workloads.py tests/detect/test_workloads.py
git commit -m "feat: detect workloads from k8s, compose or code"
```

---

### Task 12: 엔드포인트 찾기

**Files:**
- Create: `infrafit/detect/endpoints.py`
- Test: `tests/detect/test_endpoints.py`

**Interfaces:**
- Consumes: `Snapshot`, `evidence`; `WorkloadInfo`, `slug` (Task 11)
- Produces:
  - `infrafit.detect.endpoints.extract_endpoints(snap, workloads: list[WorkloadInfo]) -> list[dict]` — `Endpoint` 형식 `{id, workload, method, route, handler, framework, status: "confirmed"}`. 웹 워크로드가 없으면 빈 목록
  - 찾는 방법:
    - Python(AST): `@<이름>.get|post|put|delete|patch("경로")`, `@<이름>.route("경로", methods=[...])`(기본 GET), `@<이름>.websocket("경로")` → `WEBSOCKET`. 같은 모듈의 `<이름> = APIRouter(prefix="…")` 또는 `Blueprint(…, url_prefix="…")` 접두어를 붙인다. framework = `python`
    - Django: `urls.py`의 `path("…")` / `re_path("…")` → `ANY`, 경로 앞에 `/`. framework = `django`
    - Express류: `**/*.js|ts|mjs|cjs`에서 같은 파일 안에 `express()`, `express.Router()`, `require('express')`, `Router()`, `fastify()`, `new Koa()`, `new Router()`, `new Hono()`로 **서버 객체를 만든 변수**가 있을 때, 그 변수의 `.get|post|put|delete|patch|all('경로'` 호출만 → 메서드 대문자(`all`은 `ANY`). 서버 객체가 없는 파일(프론트엔드의 `api.get(...)` 같은 클라이언트 호출)은 건너뛴다. framework = `express`
    - Next.js App Router: `**/app/**/route.ts|js|tsx|jsx`의 `export (async) function GET` / `export const GET` → 경로는 `app/` 다음부터 `route.*` 전까지, `(그룹)`과 `@슬롯` 조각 제거. framework = `nextjs`
    - Next.js Pages Router: `**/pages/api/**`의 `.ts|.js` → `ANY`, `index`는 상위 경로. framework = `nextjs`
  - 배정: 웹 워크로드가 하나면 그것. 여럿이면 `app_dir`가 경로의 접두어인 워크로드(점수 +10) 또는 워크로드 이름을 `-`로 나눈 조각과 경로 조각이 겹치는 수가 큰 것. 동점이면 이름이 짧은 것, 그다음 id. 모두 0점이면 id가 가장 앞선 웹 워크로드
  - ID: `ep-<워크로드 id에서 w- 뺀 것>-<세 자리 순번>`, (파일, 줄, 메서드, 경로) 순 정렬 후 매김

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/detect/test_endpoints.py`:
```python
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
    _write(tmp_path, "services/auth/routes.py", "@router.post('/login')\ndef f(): ...\n")
    _write(tmp_path, "services/board/routes.py", "@router.get('/posts')\ndef f(): ...\n")
    ws = [_w("w-auth"), _w("w-auth-verify"), _w("w-board-api"), _w("w-nginx")]
    eps = extract_endpoints(open_snapshot(str(tmp_path), tmp_path / "_w"), ws)
    by_route = {e["route"]: e["workload"] for e in eps}
    assert by_route == {"/login": "w-auth", "/posts": "w-board-api"}
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `uv run pytest tests/detect/test_endpoints.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: 구현**

`infrafit/detect/endpoints.py`:
```python
"""웹 워크로드의 엔드포인트 찾기(설계 §6.2)."""

from __future__ import annotations

import ast
import re
from collections import defaultdict
from pathlib import PurePosixPath

from infrafit.detect.workloads import WorkloadInfo
from infrafit.evidence import evidence
from infrafit.repo import Snapshot

HTTP_METHODS = ("get", "post", "put", "delete", "patch")
NEXT_METHODS = "GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS"
_SERVER_VAR = re.compile(
    r"\b(?:const|let|var)\s+(\w+)\s*=\s*(?:await\s+)?"
    r"(?:express\s*\(|express\.Router\s*\(|require\(\s*['\"]express['\"]\s*\)(?:\.Router)?\s*\(|Router\s*\("
    r"|fastify\s*\(|Fastify\s*\(|new\s+Koa\s*\(|new\s+Router\s*\(|new\s+Hono\s*\()")
_ROUTE_CALL = re.compile(r"\b(\w+)\.(get|post|put|delete|patch|all)\(\s*['\"`]([^'\"`]+)['\"`]")
_DJANGO = re.compile(r"\b(?:re_)?path\(\s*r?['\"]([^'\"]*)['\"]")
_NEXT_EXPORT = re.compile(rf"export\s+(?:async\s+)?function\s+({NEXT_METHODS})\b|export\s+const\s+({NEXT_METHODS})\s*=")

Raw = tuple[str, str, str, int, str]  # (메서드, 경로, 파일, 줄, 프레임워크)


def _prefixes(tree: ast.AST) -> dict[str, str]:
    out: dict[str, str] = {}
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)):
            continue
        func = node.value.func
        fname = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
        if fname not in ("APIRouter", "Blueprint"):
            continue
        for kw in node.value.keywords:
            if kw.arg in ("prefix", "url_prefix") and isinstance(kw.value, ast.Constant):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        out[target.id] = str(kw.value.value)
    return out


def _python(snap: Snapshot) -> list[Raw]:
    out: list[Raw] = []
    for rel in snap.glob("**/*.py"):
        try:
            tree = ast.parse(snap.read(rel))
        except SyntaxError:
            continue
        prefixes = _prefixes(tree)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                if not (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)):
                    continue
                if not dec.args or not isinstance(dec.args[0], ast.Constant) or not isinstance(dec.args[0].value, str):
                    continue
                owner = dec.func.value.id if isinstance(dec.func.value, ast.Name) else ""
                path = prefixes.get(owner, "") + dec.args[0].value
                attr = dec.func.attr
                if attr in HTTP_METHODS:
                    out.append((attr.upper(), path, rel, dec.lineno, "python"))
                elif attr == "route":
                    methods = ["GET"]
                    for kw in dec.keywords:
                        if kw.arg == "methods" and isinstance(kw.value, (ast.List, ast.Tuple)):
                            methods = [str(e.value).upper() for e in kw.value.elts if isinstance(e, ast.Constant)]
                    out += [(m, path, rel, dec.lineno, "python") for m in methods]
                elif attr == "websocket":
                    out.append(("WEBSOCKET", path, rel, dec.lineno, "python"))
    return out


def _django(snap: Snapshot) -> list[Raw]:
    out: list[Raw] = []
    for rel in snap.glob("**/urls.py"):
        for i, text in enumerate(snap.lines(rel), 1):
            for m in _DJANGO.finditer(text):
                out.append(("ANY", "/" + m.group(1), rel, i, "django"))
    return out


def _express(snap: Snapshot) -> list[Raw]:
    out: list[Raw] = []
    for pattern in ("**/*.js", "**/*.ts", "**/*.mjs", "**/*.cjs"):
        for rel in snap.glob(pattern):
            if PurePosixPath(rel).name.startswith("route.") and "/app/" in f"/{rel}":
                continue
            servers = set(_SERVER_VAR.findall(snap.read(rel)))
            if not servers:
                continue
            for i, text in enumerate(snap.lines(rel), 1):
                for m in _ROUTE_CALL.finditer(text):
                    if m.group(1) not in servers:
                        continue
                    method = "ANY" if m.group(2) == "all" else m.group(2).upper()
                    out.append((method, m.group(3), rel, i, "express"))
    return out


def _next_route_path(parts: list[str]) -> str:
    keep = [p for p in parts if not (p.startswith("(") and p.endswith(")")) and not p.startswith("@")]
    return "/" + "/".join(keep)


def _next(snap: Snapshot) -> list[Raw]:
    out: list[Raw] = []
    for ext in ("ts", "js", "tsx", "jsx"):
        for rel in snap.glob(f"**/app/**/route.{ext}"):
            parts = PurePosixPath(rel).parts
            idx = len(parts) - 1 - list(reversed(parts)).index("app")
            route = _next_route_path(list(parts[idx + 1:-1]))
            for i, text in enumerate(snap.lines(rel), 1):
                for m in _NEXT_EXPORT.finditer(text):
                    out.append((m.group(1) or m.group(2), route, rel, i, "nextjs"))
    for ext in ("ts", "js"):
        for rel in snap.glob(f"**/pages/api/**.{ext}"):
            parts = list(PurePosixPath(rel).with_suffix("").parts)
            idx = len(parts) - 1 - list(reversed(parts)).index("pages")
            segs = parts[idx + 1:]
            if segs and segs[-1] == "index":
                segs = segs[:-1]
            out.append(("ANY", "/" + "/".join(segs), rel, 1, "nextjs"))
    return out


def _assign(rel: str, webs: list[WorkloadInfo]) -> WorkloadInfo:
    if len(webs) == 1:
        return webs[0]
    segments = set(PurePosixPath(rel).parts)

    def score(w: WorkloadInfo) -> int:
        s = len(set(w.name.split("-")) & segments)
        if w.app_dir and rel.startswith(w.app_dir + "/"):
            s += 10
        return s

    best = max(webs, key=lambda w: (score(w), -len(w.name), [-ord(c) for c in w.id]))
    return best if score(best) > 0 else sorted(webs, key=lambda w: w.id)[0]


def extract_endpoints(snap: Snapshot, workloads: list[WorkloadInfo]) -> list[dict]:
    webs = [w for w in workloads if w.kind == "web"]
    if not webs:
        return []
    raw = sorted(set(_python(snap) + _django(snap) + _express(snap) + _next(snap)),
                 key=lambda r: (r[2], r[3], r[0], r[1]))
    counters: dict[str, int] = defaultdict(int)
    out: list[dict] = []
    for method, route, rel, line, framework in raw:
        w = _assign(rel, webs)
        counters[w.id] += 1
        out.append({"id": f"ep-{w.id[2:]}-{counters[w.id]:03d}", "workload": w.id, "method": method,
                    "route": route, "handler": evidence(snap, rel, line), "framework": framework,
                    "status": "confirmed"})
    return out
```

> `pages/api` glob은 `**/pages/api/**.ts`로 쓴다. `fnmatch`의 `*`가 `/`도 맞추므로 하위 디렉터리까지 잡힌다.

- [ ] **Step 4: 테스트 통과 확인**

Run: `uv run pytest tests/detect/test_endpoints.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: 커밋**

```bash
git add infrafit/detect/endpoints.py tests/detect/test_endpoints.py
git commit -m "feat: extract HTTP endpoints for Python, Django, Express and Next.js"
```

---

### Task 13: 데이터 범위, 현재 구성 요소, 미매핑

**Files:**
- Create: `infrafit/detect/components.py`
- Test: `tests/detect/test_components.py`

**Interfaces:**
- Consumes: `Match` (Task 7), `WorkloadInfo`, `slug` (Task 11), `ParsedArtifact`, `flatten` (Task 8~9), `kb.signatures`, `kb.watchlist`, `kb.iter_conditions` (Task 6)
- Produces:
  - `infrafit.detect.components.map_components(snap, matches, workloads, artifacts) -> tuple[list[dict], list[dict], dict[str, str]]` — (`datastores`, `current_components`, 워크로드 id → 컴퓨트 구성 요소 id)
  - `infrafit.detect.components.find_unmapped(snap, manifests) -> list[dict]`
  - 규칙:
    - 범위 ID: 역할이 `primary-db`·`search`면 `ds-`, 그 외 `svc-`. 이름 조각은 구성 요소 ID의 제공자가 `local`, `unspecified`, `lib`이면 제품, 아니면 `<제공자>-<제품>` (예: `ds:local/sqlite/wal` → `ds-sqlite`, `ds:supabase/postgres/…` → `ds-supabase-postgres`). 같은 ID로 두 시그니처가 맞으면 근거를 합치고 상태는 `confirmed`가 우선
    - `used_by`: 데이터 범위의 시그니처 근거 파일 중 하나라도 워크로드의 `code_root` 아래(또는 `code_root == ""`)에 있으면 사용 중. `static-frontend`는 제외. 그렇게 찾은 워크로드가 하나도 없으면(예: `code_root`를 모름) `static-frontend`가 아닌 모든 워크로드로 대체한다
    - 호스팅 정교화: `ds:unspecified/postgresql/default`는 Terraform `aws_db_instance`(engine이 `postgres`로 시작)가 있으면 `multi_az`가 참이면 `ds:aws/rds-postgres/multi-az-instance` 아니면 `…/single-az`, `google_sql_database_instance`(database_version이 `POSTGRES`로 시작)가 있으면 `settings.availability_type == "REGIONAL"`이면 `ds:gcp/cloudsql-postgres/ha` 아니면 `…/single`. `ca:unspecified/redis/default`는 `aws_elasticache_*` → `ca:aws/elasticache/node-based`, `google_redis_instance` → `ca:gcp/memorystore/redis`. 정교화 근거로 Terraform 파일을 덧붙인다
    - 컴퓨트: 플랫폼 설정 파일(경로 순 첫 번째) `vercel.json` → `cp:vercel/functions/unspecified-plan`, `netlify.toml` → `cp:netlify/functions/unspecified-plan`, `fly.toml` → `cp:fly/machines/default`, `render.yaml` → `cp:render/web/unspecified-plan`, `railway.json`·`railway.toml`·`.railway/railway.ts` → `cp:railway/service/unspecified-plan`. 없으면 k8s 워크로드는 Terraform `aws_eks_cluster` → `cp:aws/eks/unspecified`, `google_container_cluster` → `cp:gcp/gke/unspecified`, 아니면 `cp:k8s/deployment/unspecified-cluster`. compose 워크로드 → `cp:local/compose/default`. 코드 워크로드는 Dockerfile(`app_dir` 또는 루트)이 있으면 `cp:docker/container/unspecified-host`, 없으면 `unmapped`(label `no deployment config`, 근거 없음)
    - 미매핑: watchlist에 있고 어떤 시그니처의 `dependency` 조건에도 없는 의존성

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/detect/test_components.py`:
```python
from infrafit.detect.artifacts import ParsedArtifact
from infrafit.detect.components import map_components
from infrafit.detect.signatures import Match
from infrafit.detect.workloads import WorkloadInfo
from infrafit.repo import open_snapshot

EV = ({"path": "db.py", "line": 1, "snippet": "x"},)


def _w(wid, kind="web", source="code", app_dir=""):
    return WorkloadInfo(id=wid, kind=kind, name=wid[2:], entrypoint={"path": "k8s/a.yaml", "line": 3, "snippet": "x"},
                        status="confirmed", source=source, app_dir=app_dir)


def test_scope_ids_and_merge(tmp_path):
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    matches = [
        Match("A", "ds:local/sqlite/wal", "primary-db", "confirmed", EV),
        Match("B", "fs:local/container-disk/default", "file-storage", "candidate", EV),
        Match("C", "ds:supabase/postgres/unspecified-plan", "primary-db", "confirmed", EV),
        Match("D", "ca:local/process-memory/default", "session", "candidate", EV),
        Match("E", "ca:local/process-memory/default", "session", "confirmed", EV),
    ]
    ds, comps, compute = map_components(snap, matches, [_w("w-web"), _w("w-static", "static-frontend")], [])
    assert [(d["id"], d["role"], d["used_by"]) for d in ds] == [
        ("ds-sqlite", "primary-db", ["w-web"]),
        ("ds-supabase-postgres", "primary-db", ["w-web"]),
        ("svc-container-disk", "file-storage", ["w-web"]),
        ("svc-process-memory", "session", ["w-web"]),
    ]
    by_scope = {c["scope"]: c for c in comps}
    assert by_scope["svc-process-memory"]["status"] == "confirmed"
    assert by_scope["w-web"]["component"] == "unmapped"
    assert by_scope["w-web"]["label"] == "no deployment config"
    assert compute == {"w-web": "unmapped", "w-static": "unmapped"}


def test_hosting_refinement_and_k8s_compute(tmp_path):
    (tmp_path / "main.tf").write_text("x\n")
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    tf = ParsedArtifact("terraform", "main.tf", True, objects=[
        ("aws_db_instance", "main", {"engine": "postgres", "multi_az": True}),
        ("aws_eks_cluster", "main", {}),
    ])
    matches = [Match("P", "ds:unspecified/postgresql/default", "primary-db", "confirmed", EV)]
    ds, comps, compute = map_components(snap, matches, [_w("w-api", source="k8s")], [tf])
    by_scope = {c["scope"]: c for c in comps}
    assert ds[0]["id"] == "ds-postgresql"
    assert by_scope["ds-postgresql"]["component"] == "ds:aws/rds-postgres/multi-az-instance"
    assert any(e["path"] == "main.tf" for e in by_scope["ds-postgresql"]["evidence"])
    assert compute["w-api"] == "cp:aws/eks/unspecified"


def test_used_by_follows_code_roots(tmp_path):
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    ev = ({"path": "services/auth/pyproject.toml", "line": 5, "snippet": "x"},
          {"path": "services/board/pyproject.toml", "line": 5, "snippet": "x"})
    ws = [
        WorkloadInfo(id="w-auth", kind="web", name="auth", entrypoint=EV[0], status="confirmed",
                     source="k8s", code_root="services/auth"),
        WorkloadInfo(id="w-board-worker", kind="worker", name="board-worker", entrypoint=EV[0],
                     status="confirmed", source="k8s", code_root="services/board"),
        WorkloadInfo(id="w-nginx", kind="web", name="nginx", entrypoint=EV[0], status="confirmed",
                     source="k8s", code_root="frontend"),
        WorkloadInfo(id="w-unknown", kind="web", name="unknown", entrypoint=EV[0], status="confirmed",
                     source="k8s", code_root=None),
    ]
    ds, _, _ = map_components(snap, [Match("P", "ds:unspecified/postgresql/default", "primary-db", "confirmed", ev)],
                              ws, [])
    assert ds[0]["used_by"] == ["w-auth", "w-board-worker"]


def test_platform_config_wins(tmp_path):
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    vercel = ParsedArtifact("platform-config", "vercel.json", True)
    _, comps, compute = map_components(snap, [], [_w("w-web")], [vercel])
    assert compute["w-web"] == "cp:vercel/functions/unspecified-plan"
    assert comps[0]["evidence"] == [{"path": "vercel.json", "line": None, "snippet": "vercel.json"}]
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `uv run pytest tests/detect/test_components.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: 구현**

`infrafit/detect/components.py`:
```python
"""데이터 범위와 현재 구성 요소 매핑, 미매핑 의존성."""

from __future__ import annotations

from pathlib import PurePosixPath

from infrafit import kb
from infrafit.detect.artifacts import ParsedArtifact, flatten
from infrafit.detect.manifests import Manifests, parent_dir
from infrafit.detect.signatures import Match
from infrafit.detect.workloads import WorkloadInfo, slug
from infrafit.evidence import evidence
from infrafit.repo import Snapshot

PLATFORM_COMPUTE = {
    "vercel.json": "cp:vercel/functions/unspecified-plan",
    "netlify.toml": "cp:netlify/functions/unspecified-plan",
    "fly.toml": "cp:fly/machines/default",
    "render.yaml": "cp:render/web/unspecified-plan",
    "railway.json": "cp:railway/service/unspecified-plan",
    "railway.toml": "cp:railway/service/unspecified-plan",
    "railway.ts": "cp:railway/service/unspecified-plan",
}
GENERIC_PROVIDERS = {"local", "unspecified", "lib"}


def scope_id(component: str, role: str) -> str:
    provider, product, _ = component.split(":", 1)[1].split("/")
    name = product if provider in GENERIC_PROVIDERS else f"{provider}-{product}"
    prefix = "ds" if role in ("primary-db", "search") else "svc"
    return f"{prefix}-{slug(name)}"


def _terraform_objects(artifacts: list[ParsedArtifact]):
    for art in artifacts:
        if art.kind == "terraform":
            for rtype, rname, attrs in art.objects:
                yield rtype, rname, attrs, art.path


def _refine_hosting(component: str, artifacts: list[ParsedArtifact]) -> tuple[str, str | None]:
    for rtype, _, attrs, path in _terraform_objects(artifacts):
        flat = flatten(attrs)
        if component == "ds:unspecified/postgresql/default":
            if rtype == "aws_db_instance" and str(flat.get("engine", "")).startswith("postgres"):
                multi = flat.get("multi_az") in (True, "true")
                return ("ds:aws/rds-postgres/multi-az-instance" if multi else "ds:aws/rds-postgres/single-az"), path
            if rtype == "google_sql_database_instance" and str(flat.get("database_version", "")).startswith("POSTGRES"):
                ha = flat.get("settings.availability_type") == "REGIONAL"
                return ("ds:gcp/cloudsql-postgres/ha" if ha else "ds:gcp/cloudsql-postgres/single"), path
        if component == "ca:unspecified/redis/default":
            if rtype.startswith("aws_elasticache_"):
                return "ca:aws/elasticache/node-based", path
            if rtype == "google_redis_instance":
                return "ca:gcp/memorystore/redis", path
    return component, None


def _compute_for(w: WorkloadInfo, artifacts: list[ParsedArtifact]) -> tuple[str, str | None]:
    for art in artifacts:
        if art.kind == "platform-config":
            comp = PLATFORM_COMPUTE.get(PurePosixPath(art.path).name)
            if comp:
                return comp, art.path
    tf_types = {rtype for rtype, _, _, _ in _terraform_objects(artifacts)}
    if w.source == "k8s":
        if "aws_eks_cluster" in tf_types:
            return "cp:aws/eks/unspecified", w.entrypoint["path"]
        if "google_container_cluster" in tf_types:
            return "cp:gcp/gke/unspecified", w.entrypoint["path"]
        return "cp:k8s/deployment/unspecified-cluster", w.entrypoint["path"]
    if w.source == "compose":
        return "cp:local/compose/default", w.entrypoint["path"]
    for target in (w.app_dir, ""):
        for art in artifacts:
            if art.kind == "dockerfile" and parent_dir(art.path) == target:
                return "cp:docker/container/unspecified-host", art.path
    return "unmapped", None


def _under(path: str, root: str) -> bool:
    return root == "" or path == root or path.startswith(root + "/")


def _users(evidence_items: list[dict], workloads: list[WorkloadInfo]) -> list[str]:
    backend = [w for w in workloads if w.kind != "static-frontend"]
    paths = {e["path"] for e in evidence_items}
    users = sorted(w.id for w in backend
                   if w.code_root is not None and any(_under(p, w.code_root) for p in paths))
    return users or sorted(w.id for w in backend)


def map_components(snap: Snapshot, matches: list[Match], workloads: list[WorkloadInfo],
                   artifacts: list[ParsedArtifact]) -> tuple[list[dict], list[dict], dict[str, str]]:
    scopes: dict[str, dict] = {}
    for m in matches:
        sid = scope_id(m.component, m.role)
        entry = scopes.setdefault(sid, {"role": m.role, "component": m.component, "status": m.status,
                                        "signatures": [], "evidence": []})
        entry["signatures"].append(m.signature)
        entry["evidence"].extend(m.evidence)
        if m.status == "confirmed":
            entry["status"] = "confirmed"

    datastores: list[dict] = []
    comps: list[dict] = []
    for sid in sorted(scopes):
        s = scopes[sid]
        component, tf_path = _refine_hosting(s["component"], artifacts)
        ev = list(s["evidence"])
        if tf_path:
            ev.append(evidence(snap, tf_path))
        datastores.append({"id": sid, "role": s["role"], "used_by": _users(s["evidence"], workloads),
                           "evidence": s["evidence"], "status": s["status"]})
        comps.append({"scope": sid, "component": component, "label": ",".join(s["signatures"]),
                      "settings": [], "evidence": ev, "status": s["status"]})

    compute: dict[str, str] = {}
    for w in sorted(workloads, key=lambda w: w.id):
        comp, path = _compute_for(w, artifacts)
        compute[w.id] = comp
        entry = {"scope": w.id, "component": comp, "settings": [], "status": "confirmed",
                 "evidence": [evidence(snap, path)] if path else []}
        if comp == "unmapped":
            entry["label"] = "no deployment config"
        comps.append(entry)
    return datastores, comps, compute


def find_unmapped(snap: Snapshot, manifests: Manifests) -> list[dict]:
    known = {leaf["dependency"].lower() for s in kb.signatures()
             for cond in [s["when"]] + [r["when"] for r in s.get("refine", [])]
             for leaf in kb.iter_conditions(cond) if "dependency" in leaf}
    out = []
    for name in kb.watchlist():
        if name in manifests.deps and name not in known:
            rel, line = manifests.deps[name]
            out.append({"label": name, "evidence": [evidence(snap, rel, line)]})
    return out
```

> `evidence(snap, path)`(줄 없음)는 파일이 스냅샷에 있는지 확인하지 않는다. 테스트의 `vercel.json`처럼 파일이 없어도 근거는 만들어진다. 일관성 검사(Task 15)가 실제 실행에서는 근거 파일의 존재를 확인한다.

- [ ] **Step 4: 테스트 통과 확인**

Run: `uv run pytest tests/detect/test_components.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: 커밋**

```bash
git add infrafit/detect/components.py tests/detect/test_components.py
git commit -m "feat: map datastores and current components with hosting refinement"
```

---

### Task 14: 요청 경로

**Files:**
- Create: `infrafit/detect/paths.py`
- Test: `tests/detect/test_paths.py`

**Interfaces:**
- Consumes: `WorkloadInfo` (Task 11), `ParsedArtifact`, `ingress_backends` (Task 9), `hop_settings` (Task 10), `kb.defaults`
- Produces:
  - `infrafit.detect.paths.app_server(command: str) -> tuple[str, dict] | None` — 실행 명령에서 (구성 요소 id, 명시 설정)
    - `uvicorn` → `nw:app/uvicorn/default`, `--timeout-keep-alive N` → `{"timeout_keep_alive": N}`
    - `gunicorn` → `nw:app/gunicorn/default`, `--keep-alive N` 또는 `--keepalive N` → `{"keepalive": N}`
    - `next start` → `nw:app/next-start/default`
    - `flask run` → `nw:app/flask-dev/default`
    - `manage.py runserver` → `nw:app/django-runserver/default`
    - `node ` 또는 `npm start`로 시작 → `nw:app/node-http/default`
    - 그 외 → `None`
  - `infrafit.detect.paths.build_paths(snap, workloads, artifacts, compute: dict[str, str]) -> list[dict]` — 웹 워크로드마다 `RequestPath` `{id: "path-<w- 뺀 id>", workload, hops}`. 구간 순서:
    1. 엣지: 플랫폼 설정이 있으면 `edge-proxy` — `vercel.json` → `nw:vercel/edge-proxy/default`, `netlify.toml` → `nw:netlify/edge-proxy/default`, `fly.toml` → `nw:fly/proxy/default`, `render.yaml` → `nw:render/proxy/default`, Railway 파일 → `nw:railway/proxy/default`
    2. 로드밸런서: 백엔드 서비스 이름이 워크로드 이름과 같은 Ingress(경로 순 첫 번째) → `load-balancer`. 클래스 `alb` → `nw:aws/alb/default`(어노테이션 `alb.ingress.kubernetes.io/load-balancer-attributes`의 `idle_timeout.timeout_seconds=N` → `{"idle_timeout": N}`), `gce` → `nw:gcp/classic-alb/gke-ingress`, `nginx` → `nw:k8s/ingress-nginx/default`, 그 외 → `unmapped`
    3. 앱 서버: 컴퓨트가 `cp:vercel/…`, `cp:netlify/…`(관리형 런타임)가 아니고 `app_server(command)`가 결과를 내면 `app-server`
  - 모든 구간은 `osi_layer: "L7"`, 설정은 `hop_settings`로 채우고, `order`는 0부터

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/detect/test_paths.py`:
```python
from infrafit.detect.artifacts import ParsedArtifact
from infrafit.detect.paths import app_server, build_paths
from infrafit.detect.workloads import WorkloadInfo
from infrafit.repo import open_snapshot


def _w(wid, command="", kind="web"):
    return WorkloadInfo(id=wid, kind=kind, name=wid[2:], entrypoint={"path": "x", "line": None, "snippet": "x"},
                        status="confirmed", source="k8s", command=command)


def test_app_server_parsing():
    assert app_server("uvicorn main:app --timeout-keep-alive 75") == ("nw:app/uvicorn/default", {"timeout_keep_alive": 75})
    assert app_server("gunicorn -w 4 --keep-alive 5 app:app") == ("nw:app/gunicorn/default", {"keepalive": 5})
    assert app_server("flask run --host=0.0.0.0") == ("nw:app/flask-dev/default", {})
    assert app_server("node index.js") == ("nw:app/node-http/default", {})
    assert app_server("python -m board.worker") is None


def test_ingress_and_app_server_hops(tmp_path):
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    ingress = {"apiVersion": "networking.k8s.io/v1", "kind": "Ingress",
               "metadata": {"name": "web", "annotations": {
                   "alb.ingress.kubernetes.io/load-balancer-attributes": "idle_timeout.timeout_seconds=120"}},
               "spec": {"ingressClassName": "alb",
                        "rules": [{"http": {"paths": [{"backend": {"service": {"name": "api"}}}]}}]}}
    k8s = ParsedArtifact("k8s", "k8s/ingress.yaml", True, objects=[ingress])
    paths = build_paths(snap, [_w("w-api", "uvicorn main:app"), _w("w-worker", kind="worker")], [k8s],
                        {"w-api": "cp:k8s/deployment/unspecified-cluster"})
    assert [p["id"] for p in paths] == ["path-api"]
    hops = paths[0]["hops"]
    assert [(h["order"], h["kind"], h["component"]) for h in hops] == [
        (0, "load-balancer", "nw:aws/alb/default"), (1, "app-server", "nw:app/uvicorn/default")]
    assert hops[0]["settings"] == [{"key": "idle_timeout", "value": 120, "defaulted": False}]
    assert hops[1]["settings"][0]["defaulted"] is True


def test_managed_runtime_skips_app_server(tmp_path):
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    vercel = ParsedArtifact("platform-config", "vercel.json", True)
    paths = build_paths(snap, [_w("w-web", "next start")], [vercel], {"w-web": "cp:vercel/functions/unspecified-plan"})
    assert [(h["kind"], h["component"]) for h in paths[0]["hops"]] == [("edge-proxy", "nw:vercel/edge-proxy/default")]
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `uv run pytest tests/detect/test_paths.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: 구현**

`infrafit/detect/paths.py`:
```python
"""요청 경로: 엣지 → 로드밸런서 → 앱 서버 (설계 §6.6)."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from infrafit import kb
from infrafit.detect.artifacts import ParsedArtifact, ingress_backends
from infrafit.detect.defaults import hop_settings
from infrafit.detect.workloads import WorkloadInfo
from infrafit.evidence import evidence
from infrafit.repo import Snapshot

EDGE_BY_FILE = {
    "vercel.json": "nw:vercel/edge-proxy/default",
    "netlify.toml": "nw:netlify/edge-proxy/default",
    "fly.toml": "nw:fly/proxy/default",
    "render.yaml": "nw:render/proxy/default",
    "railway.json": "nw:railway/proxy/default",
    "railway.toml": "nw:railway/proxy/default",
    "railway.ts": "nw:railway/proxy/default",
}
LB_BY_CLASS = {"alb": "nw:aws/alb/default", "gce": "nw:gcp/classic-alb/gke-ingress", "nginx": "nw:k8s/ingress-nginx/default"}
MANAGED_RUNTIME_PREFIXES = ("cp:vercel/", "cp:netlify/")
_ALB_IDLE = re.compile(r"idle_timeout\.timeout_seconds=(\d+)")


def app_server(command: str) -> tuple[str, dict] | None:
    cmd = command.strip()
    if "uvicorn" in cmd:
        m = re.search(r"--timeout-keep-alive[ =](\d+)", cmd)
        return "nw:app/uvicorn/default", ({"timeout_keep_alive": int(m.group(1))} if m else {})
    if "gunicorn" in cmd:
        m = re.search(r"--keep-?alive[ =](\d+)", cmd)
        return "nw:app/gunicorn/default", ({"keepalive": int(m.group(1))} if m else {})
    if "next start" in cmd:
        return "nw:app/next-start/default", {}
    if "flask run" in cmd:
        return "nw:app/flask-dev/default", {}
    if "manage.py runserver" in cmd:
        return "nw:app/django-runserver/default", {}
    if cmd.startswith(("node ", "npm start")):
        return "nw:app/node-http/default", {}
    return None


def _hop(kind: str, component: str, explicit: dict, ev: list[dict]) -> dict:
    return {"order": 0, "kind": kind, "component": component, "osi_layer": "L7",
            "settings": hop_settings(component, explicit, kb.defaults()), "evidence": ev}


def _edge(snap: Snapshot, artifacts: list[ParsedArtifact]) -> dict | None:
    for art in artifacts:
        if art.kind == "platform-config":
            comp = EDGE_BY_FILE.get(PurePosixPath(art.path).name)
            if comp:
                return _hop("edge-proxy", comp, {}, [evidence(snap, art.path)])
    return None


def _load_balancer(snap: Snapshot, w: WorkloadInfo, artifacts: list[ParsedArtifact]) -> dict | None:
    for art in artifacts:
        if art.kind != "k8s":
            continue
        for doc in art.objects:
            if doc.get("kind") != "Ingress" or w.name not in ingress_backends(doc):
                continue
            meta = doc.get("metadata") or {}
            annotations = meta.get("annotations") or {}
            cls = (doc.get("spec") or {}).get("ingressClassName") or annotations.get("kubernetes.io/ingress.class")
            comp = LB_BY_CLASS.get(str(cls), "unmapped")
            explicit = {}
            m = _ALB_IDLE.search(str(annotations.get("alb.ingress.kubernetes.io/load-balancer-attributes", "")))
            if comp == "nw:aws/alb/default" and m:
                explicit["idle_timeout"] = int(m.group(1))
            return _hop("load-balancer", comp, explicit, [evidence(snap, art.path)])
    return None


def build_paths(snap: Snapshot, workloads: list[WorkloadInfo], artifacts: list[ParsedArtifact],
                compute: dict[str, str]) -> list[dict]:
    paths = []
    for w in sorted(workloads, key=lambda w: w.id):
        if w.kind != "web":
            continue
        hops = [h for h in (_edge(snap, artifacts), _load_balancer(snap, w, artifacts)) if h]
        if not str(compute.get(w.id, "")).startswith(MANAGED_RUNTIME_PREFIXES):
            server = app_server(w.command)
            if server:
                hops.append(_hop("app-server", server[0], server[1], [w.entrypoint]))
        for i, hop in enumerate(hops):
            hop["order"] = i
        paths.append({"id": f"path-{w.id[2:]}", "workload": w.id, "hops": hops})
    return paths
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `uv run pytest tests/detect/test_paths.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: 커밋**

```bash
git add infrafit/detect/paths.py tests/detect/test_paths.py
git commit -m "feat: build request paths from platform configs, ingress and app server"
```

---

### Task 15: S1 조립, 일관성 검사, CLI

**Files:**
- Create: `infrafit/stages/s1_inventory.py`, `infrafit/consistency.py`
- Modify: `infrafit/pipeline.py`, `infrafit/cli.py` (`check-run` 하위 명령)
- Test: `tests/test_s1.py`, `tests/test_consistency.py`

**Interfaces:**
- Consumes: Task 3~14의 모든 탐지기, `RunContext`, `kb`
- Produces:
  - `infrafit.stages.s1_inventory.run_s1(ctx: RunContext, snap: Snapshot) -> dict`
  - `infrafit.consistency.ConsistencyError(RuntimeError)` — `issues: list[str]`
  - `infrafit.consistency.check_s1(inventory: dict, repo_root: Path | None) -> list[str]` — 검사 항목:
    - 범위 ID(워크로드, 엔드포인트, 데이터 범위, 요청 경로) 중복 없음
    - 엔드포인트의 `workload`, 데이터 범위의 `used_by`, 요청 경로의 `workload`가 워크로드에 있음
    - 현재 구성 요소의 `scope`가 범위에 있음
    - 구성 요소 ID(현재 구성 요소, 구간)가 `unmapped`·`pending`이 아니면 catalog에 있음
    - 요청 경로 ID가 `path-` + 워크로드 id에서 `w-` 뺀 것이고, 구간 `order`가 0부터 연속
    - `repo_root`가 있으면 모든 근거의 파일이 있고, 줄 번호가 파일 줄 수 이하
  - `infrafit.consistency.check_run(run_dir: Path) -> list[str]` — 실행 디렉터리의 `intake.json`·`inventory.json`을 스키마로 검증하고 `check_s1`(repo가 로컬 디렉터리면 그 경로로) 실행
  - `analyze(..., until="S1")`는 S1 뒤에 `check_s1`을 돌려 문제가 있으면 `ConsistencyError`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_consistency.py`:
```python
from infrafit.consistency import check_s1

EV = {"path": "app.py", "line": 1, "snippet": "x"}


def _inv():
    return {
        "workloads": [{"id": "w-web", "kind": "web", "entrypoint": EV, "status": "confirmed"}],
        "endpoints": [{"id": "ep-web-001", "workload": "w-web", "method": "GET", "route": "/", "handler": EV, "status": "confirmed"}],
        "datastores": [{"id": "ds-sqlite", "role": "primary-db", "used_by": ["w-web"], "status": "confirmed"}],
        "current_components": [{"scope": "ds-sqlite", "component": "ds:local/sqlite/default", "evidence": [EV], "status": "confirmed"}],
        "request_paths": [{"id": "path-web", "workload": "w-web", "hops": [
            {"order": 0, "kind": "app-server", "component": "nw:app/uvicorn/default", "settings": []}]}],
        "existing_artifacts": [], "unmapped": [],
    }


def test_clean_inventory_has_no_issues(tmp_path):
    (tmp_path / "app.py").write_text("x\n")
    assert check_s1(_inv(), tmp_path) == []


def test_detects_broken_references(tmp_path):
    inv = _inv()
    inv["endpoints"][0]["workload"] = "w-nope"
    inv["current_components"][0]["component"] = "ds:made/up/thing"
    inv["request_paths"][0]["id"] = "path-other"
    inv["request_paths"][0]["hops"][0]["order"] = 3
    inv["workloads"].append(dict(inv["workloads"][0]))
    issues = check_s1(inv, None)
    assert any("duplicate" in i for i in issues)
    assert any("w-nope" in i for i in issues)
    assert any("ds:made/up/thing" in i for i in issues)
    assert any("path-other" in i for i in issues)
    assert any("order" in i for i in issues)


def test_detects_missing_evidence_file(tmp_path):
    issues = check_s1(_inv(), tmp_path)
    assert any("app.py" in i for i in issues)
```

`tests/test_s1.py`:
```python
import json

from infrafit.consistency import check_run
from infrafit.pipeline import analyze


def test_analyze_until_s1_on_small_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "requirements.txt").write_text("fastapi==0.115\nuvicorn==0.30\nasyncpg==0.29\n")
    (repo / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/health')\ndef h():\n    return 'ok'\n")
    (repo / "Dockerfile").write_text('FROM python:3.12\nCMD ["uvicorn", "main:app"]\n')
    ctx = analyze(str(repo), tmp_path / "out", until="S1", run_id="r1")
    inv = json.loads((ctx.out_dir / "inventory.json").read_text())
    assert [w["id"] for w in inv["workloads"]] == ["w-web"]
    assert [(e["method"], e["route"]) for e in inv["endpoints"]] == [("GET", "/health")]
    assert [d["id"] for d in inv["datastores"]] == ["ds-postgresql"]
    assert inv["request_paths"][0]["hops"][0]["component"] == "nw:app/uvicorn/default"
    assert check_run(ctx.out_dir) == []
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `uv run pytest tests/test_consistency.py tests/test_s1.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: 구현**

`infrafit/stages/s1_inventory.py`:
```python
"""S1 인벤토리: 무엇이 있는가(설계 §6)."""

from __future__ import annotations

from infrafit import kb
from infrafit.detect.artifacts import parse_artifacts
from infrafit.detect.components import find_unmapped, map_components
from infrafit.detect.defaults import apply_defaults
from infrafit.detect.endpoints import extract_endpoints
from infrafit.detect.manifests import parse_manifests
from infrafit.detect.paths import build_paths
from infrafit.detect.signatures import match_signatures
from infrafit.detect.workloads import detect_workloads
from infrafit.repo import Snapshot
from infrafit.run import RunContext, code_version, input_hash, now_iso


def run_s1(ctx: RunContext, snap: Snapshot) -> dict:
    started = now_iso()
    h = input_hash("S1", snap.commit, kb.kb_version(), code_version())
    cached = ctx.cached("S1", h)
    if cached is not None:
        return cached
    manifests = parse_manifests(snap)
    artifacts = parse_artifacts(snap)
    apply_defaults(artifacts, kb.defaults())
    workloads = detect_workloads(snap, manifests, artifacts)
    endpoints = extract_endpoints(snap, workloads)
    matches = match_signatures(snap, manifests, kb.signatures())
    datastores, components, compute = map_components(snap, matches, workloads, artifacts)
    body = {
        "workloads": [w.to_dict() for w in workloads],
        "endpoints": endpoints,
        "datastores": datastores,
        "current_components": components,
        "request_paths": build_paths(snap, workloads, artifacts, compute),
        "existing_artifacts": [a.to_dict() for a in artifacts],
        "unmapped": find_unmapped(snap, manifests),
    }
    return ctx.write_stage("S1", body, input_hash=h, started_at=started)
```

`infrafit/consistency.py`:
```python
"""단계 간 일관성 검사(설계 §15.1). 이 계획에서는 S0~S1."""

from __future__ import annotations

import json
from pathlib import Path

from infrafit import kb
from infrafit.schema import SchemaError, validate

SPECIAL_COMPONENTS = {"unmapped", "pending"}


class ConsistencyError(RuntimeError):
    def __init__(self, issues: list[str]):
        super().__init__("; ".join(issues))
        self.issues = issues


def _evidence_items(obj):
    if isinstance(obj, dict):
        if {"path", "snippet"} <= obj.keys() and "line" in obj:
            yield obj
        for value in obj.values():
            yield from _evidence_items(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _evidence_items(value)


def check_s1(inventory: dict, repo_root: Path | None) -> list[str]:
    issues: list[str] = []
    workloads = {w["id"] for w in inventory["workloads"]}
    ids = ([w["id"] for w in inventory["workloads"]] + [e["id"] for e in inventory["endpoints"]]
           + [d["id"] for d in inventory["datastores"]] + [p["id"] for p in inventory["request_paths"]])
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        issues.append(f"duplicate scope id: {dup}")
    scopes = set(ids)
    catalog = kb.catalog()
    for e in inventory["endpoints"]:
        if e["workload"] not in workloads:
            issues.append(f"endpoint {e['id']}: unknown workload {e['workload']}")
    for d in inventory["datastores"]:
        for u in d["used_by"]:
            if u not in workloads:
                issues.append(f"datastore {d['id']}: unknown workload {u}")
    for c in inventory["current_components"]:
        if c["scope"] not in scopes:
            issues.append(f"current component: unknown scope {c['scope']}")
        if c["component"] not in SPECIAL_COMPONENTS and c["component"] not in catalog:
            issues.append(f"current component {c['scope']}: not in catalog {c['component']}")
    for p in inventory["request_paths"]:
        if p["workload"] not in workloads:
            issues.append(f"request path {p['id']}: unknown workload {p['workload']}")
        if p["id"] != "path-" + p["workload"][2:]:
            issues.append(f"request path id {p['id']} does not match workload {p['workload']}")
        if [h["order"] for h in p["hops"]] != list(range(len(p["hops"]))):
            issues.append(f"request path {p['id']}: hop order is not 0..n-1")
        for h in p["hops"]:
            if h["component"] not in SPECIAL_COMPONENTS and h["component"] not in catalog:
                issues.append(f"request path {p['id']}: not in catalog {h['component']}")
    if repo_root is not None:
        for ev in _evidence_items(inventory):
            target = repo_root / ev["path"]
            if not target.is_file():
                issues.append(f"evidence file missing: {ev['path']}")
            elif ev["line"] is not None:
                count = len(target.read_text(encoding="utf-8", errors="replace").splitlines())
                if ev["line"] > count:
                    issues.append(f"evidence line out of range: {ev['path']}:{ev['line']}")
    return sorted(set(issues))


def check_run(run_dir: Path) -> list[str]:
    issues: list[str] = []
    intake = json.loads((run_dir / "intake.json").read_text(encoding="utf-8"))
    try:
        validate("Intake", intake)
    except SchemaError as e:
        issues.append(str(e))
    inventory_file = run_dir / "inventory.json"
    if inventory_file.exists():
        inventory = json.loads(inventory_file.read_text(encoding="utf-8"))
        try:
            validate("Inventory", inventory)
        except SchemaError as e:
            issues.append(str(e))
        root = Path(intake["repo"])
        issues += check_s1(inventory, root if root.is_dir() else None)
    return issues
```

`infrafit/pipeline.py`를 아래로 바꾼다:
```python
"""단계 실행 순서."""

from __future__ import annotations

from pathlib import Path

from infrafit.consistency import ConsistencyError, check_s1
from infrafit.repo import open_snapshot
from infrafit.run import RunContext
from infrafit.stages.s0_intake import run_s0
from infrafit.stages.s1_inventory import run_s1

ORDER = ["S0", "S1"]


def analyze(source: str, out_root: Path, until: str = "S1", run_id: str | None = None) -> RunContext:
    if until not in ORDER:
        raise ValueError(f"지원하지 않는 단계: {until}")
    ctx = RunContext.create(out_root, run_id)
    snap = open_snapshot(source, ctx.out_dir)
    run_s0(ctx, snap)
    if until == "S0":
        return ctx
    inventory = run_s1(ctx, snap)
    issues = check_s1(inventory, snap.root)
    if issues:
        raise ConsistencyError(issues)
    return ctx
```

`infrafit/cli.py`에 추가(`build_parser` 안):
```python
    check = sub.add_parser("check-run", help="실행 결과의 스키마·일관성 검사")
    check.add_argument("run_dir")
    check.set_defaults(func=_cmd_check_run)
```
그리고 함수:
```python
def _cmd_check_run(args: argparse.Namespace) -> int:
    from pathlib import Path

    from infrafit.consistency import check_run

    issues = check_run(Path(args.run_dir))
    for issue in issues:
        print(issue)
    print(f"{len(issues)}개 문제")
    return 1 if issues else 0
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `uv run pytest -v`
Expected: PASS (전체 통과)

- [ ] **Step 5: 커밋**

```bash
git add infrafit/stages/s1_inventory.py infrafit/consistency.py infrafit/pipeline.py infrafit/cli.py tests/test_s1.py tests/test_consistency.py
git commit -m "feat: assemble S1 inventory with consistency checks and check-run command"
```

---

### Task 16: 픽스처 기대 판정 테스트

**Files:**
- Create: `tests/test_fixtures.py`

**Interfaces:**
- Consumes: `analyze` (Task 15), `fixtures/*/expected.yaml` 형식 (Task 4)

- [ ] **Step 1: 테스트 작성**

`tests/test_fixtures.py`:
```python
"""엔진 실행 전에 적어 둔 기대 판정(expected.yaml)과 S1 결과를 비교한다.

실패하면 기대를 고치지 말고 엔진을 고친다. 기대가 틀렸다고 판단되면 멈추고 보고한다.
"""

import json
from pathlib import Path

import pytest
import yaml

from infrafit.pipeline import analyze

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
CASES = sorted(p.parent.name for p in FIXTURES.glob("*/expected.yaml"))


def _load(name):
    expected = yaml.safe_load((FIXTURES / name / "expected.yaml").read_text())
    repo = FIXTURES / name / expected.get("repo_dir", ".")
    return expected, repo


def _settings_match(actual_settings, expected_settings):
    by_key = {s["key"]: s for s in actual_settings}
    for key, want in (expected_settings or {}).items():
        assert key in by_key, f"설정 없음: {key}"
        if isinstance(want, dict):
            assert by_key[key]["value"] == want["value"], key
            assert by_key[key]["defaulted"] == want["defaulted"], key
        else:
            assert by_key[key]["value"] == want, key


@pytest.fixture(scope="module", params=CASES)
def case(request, tmp_path_factory):
    expected, repo = _load(request.param)
    if not repo.exists():
        pytest.skip(f"{request.param}: 저장소 없음(scripts/export_f1.sh 실행 필요)")
    ctx = analyze(str(repo), tmp_path_factory.mktemp("out"), until="S1", run_id="t")
    inv = json.loads((ctx.out_dir / "inventory.json").read_text())
    return request.param, expected, inv


def test_workloads(case):
    _, exp, inv = case
    actual = {(w["id"], w["kind"]) for w in inv["workloads"]}
    want = {(w["id"], w["kind"]) for w in exp["workloads"]}
    if exp["match"] == "exact" or exp.get("workloads_exact"):
        assert actual == want
    else:
        assert want <= actual


def test_endpoints(case):
    _, exp, inv = case
    actual = {(e["method"], e["route"]) for e in inv["endpoints"]}
    if "endpoints" in exp:
        want = {(e["method"], e["route"]) for e in exp["endpoints"]}
        assert actual == want if exp["match"] == "exact" else want <= actual
    for rule in exp.get("endpoint_workloads", []):
        assert any(rule["path_contains"] in e["handler"]["path"] and e["workload"] == rule["workload"]
                   for e in inv["endpoints"]), rule


def test_datastores(case):
    _, exp, inv = case
    actual = {(d["id"], d["role"]) for d in inv["datastores"]}
    want = {(d["id"], d["role"]) for d in exp["datastores"]}
    assert actual == want if exp["match"] == "exact" else want <= actual
    by_id = {d["id"]: d for d in inv["datastores"]}
    for d in exp["datastores"]:
        if "used_by" in d:
            assert by_id[d["id"]]["used_by"] == d["used_by"], d["id"]


def test_current_components(case):
    _, exp, inv = case
    actual = {(c["scope"], c["component"], c["status"]) for c in inv["current_components"]}
    for c in exp["current_components"]:
        assert (c["scope"], c["component"], c["status"]) in actual, c


def test_artifacts(case):
    _, exp, inv = case
    by_path = {a["path"]: a for a in inv["existing_artifacts"]}
    for want in exp.get("artifacts", []):
        assert want["path"] in by_path, want["path"]
        assert by_path[want["path"]]["kind"] == want["kind"]
        _settings_match(by_path[want["path"]]["settings"], want.get("settings"))


def test_request_paths(case):
    _, exp, inv = case
    by_id = {p["id"]: p for p in inv["request_paths"]}
    for want in exp.get("request_paths", []):
        assert want["id"] in by_id, want["id"]
        if "hops" not in want:
            continue
        hops = by_id[want["id"]]["hops"]
        assert [(h["kind"], h["component"]) for h in hops] == [(h["kind"], h["component"]) for h in want["hops"]]
        for actual_hop, want_hop in zip(hops, want["hops"]):
            _settings_match(actual_hop["settings"], want_hop.get("settings"))


def test_unmapped(case):
    _, exp, inv = case
    if "unmapped" in exp:
        assert sorted(u["label"] for u in inv["unmapped"]) == sorted(exp["unmapped"])
```

- [ ] **Step 2: 테스트 실행**

Run: `uv run pytest tests/test_fixtures.py -v`
Expected: PASS (6개 픽스처 × 7개 검사). 실패하면 실패한 검사의 메시지를 보고 **엔진 코드를 고친다.** `expected.yaml`이 틀렸다고 판단되면 고치지 말고 멈추고 보고한다.

- [ ] **Step 3: 커밋**

```bash
git add tests/test_fixtures.py
git commit -m "test: compare S1 output with expected judgments for all fixtures"
```

---

### Task 17: 골든 결과, 결정성, 단계별 예시

**Files:**
- Create: `scripts/update_golden.py`, `fixtures/*/golden/intake.json`, `fixtures/*/golden/inventory.json`, `schemas/examples/f2-sqlite-erp/intake.json`, `schemas/examples/f2-sqlite-erp/inventory.json`
- Test: `tests/test_golden.py`

**Interfaces:**
- Consumes: `analyze` (Task 15), `validate` (Task 2), `check_s1` (Task 15)
- Produces:
  - `scripts/update_golden.normalize(data: dict) -> dict` — `meta` 제거, intake의 `repo`를 `"<repo>"`로 바꿈
  - 골든은 기대 판정 테스트(Task 16)가 통과한 실행 결과를 고정한 회귀용 기준이다

- [ ] **Step 1: 골든 갱신 스크립트 작성**

`scripts/update_golden.py`:
```python
"""픽스처마다 S0~S1을 돌려 골든 결과와 F2 단계별 예시를 갱신한다.

tests/test_fixtures.py가 통과한 상태에서만 실행한다.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from infrafit.pipeline import analyze  # noqa: E402
from infrafit.run import dump_json  # noqa: E402


def normalize(data: dict) -> dict:
    out = {k: v for k, v in data.items() if k != "meta"}
    if "repo" in out:
        out["repo"] = "<repo>"
    return out


def main() -> None:
    for expected_file in sorted((ROOT / "fixtures").glob("*/expected.yaml")):
        fixture = expected_file.parent
        expected = yaml.safe_load(expected_file.read_text(encoding="utf-8"))
        repo = fixture / expected.get("repo_dir", ".")
        with tempfile.TemporaryDirectory() as tmp:
            ctx = analyze(str(repo), Path(tmp), until="S1", run_id="golden")
            golden = fixture / "golden"
            golden.mkdir(exist_ok=True)
            for name in ("intake", "inventory"):
                data = json.loads((ctx.out_dir / f"{name}.json").read_text(encoding="utf-8"))
                (golden / f"{name}.json").write_text(dump_json(normalize(data)), encoding="utf-8")
        print(f"updated {fixture.name}")
    examples = ROOT / "schemas" / "examples" / "f2-sqlite-erp"
    examples.mkdir(parents=True, exist_ok=True)
    for name in ("intake", "inventory"):
        data = json.loads((ROOT / "fixtures" / "f2-sqlite-erp" / "golden" / f"{name}.json").read_text(encoding="utf-8"))
        data["meta"] = {"run_id": "example", "stage": "S0" if name == "intake" else "S1",
                        "input_hash": "sha256:example"}
        (examples / f"{name}.json").write_text(dump_json(data), encoding="utf-8")
    shutil.rmtree(ROOT / "out" / ".cache", ignore_errors=True)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 실패하는 테스트 작성**

`tests/test_golden.py`:
```python
import json
import sys
from pathlib import Path

import pytest
import yaml

from infrafit.consistency import check_s1
from infrafit.pipeline import analyze
from infrafit.schema import validate

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from update_golden import normalize  # noqa: E402

FIXTURES = sorted(p.parent for p in (ROOT / "fixtures").glob("*/golden/inventory.json"))


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda p: p.name)
def test_matches_golden(fixture, tmp_path):
    expected = yaml.safe_load((fixture / "expected.yaml").read_text())
    ctx = analyze(str(fixture / expected.get("repo_dir", ".")), tmp_path, until="S1", run_id="t")
    for name in ("intake", "inventory"):
        actual = normalize(json.loads((ctx.out_dir / f"{name}.json").read_text()))
        golden = json.loads((fixture / "golden" / f"{name}.json").read_text())
        assert actual == golden, f"{fixture.name}/{name}: 골든과 다름. 의도한 변경이면 scripts/update_golden.py 실행"


def test_deterministic_without_cache(tmp_path):
    repo = ROOT / "fixtures" / "f2-sqlite-erp" / "repo"
    a = analyze(str(repo), tmp_path / "a", until="S1", run_id="r")
    b = analyze(str(repo), tmp_path / "b", until="S1", run_id="r")
    for name in ("intake", "inventory"):
        left = normalize(json.loads((a.out_dir / f"{name}.json").read_text()))
        right = normalize(json.loads((b.out_dir / f"{name}.json").read_text()))
        assert json.dumps(left, sort_keys=True) == json.dumps(right, sort_keys=True)


@pytest.mark.parametrize("name,def_name", [("intake", "Intake"), ("inventory", "Inventory")])
def test_examples_pass_schema_and_consistency(name, def_name):
    data = json.loads((ROOT / "schemas" / "examples" / "f2-sqlite-erp" / f"{name}.json").read_text())
    validate(def_name, data)
    if name == "inventory":
        assert check_s1(data, ROOT / "fixtures" / "f2-sqlite-erp" / "repo") == []
```

- [ ] **Step 3: 테스트가 실패하는지 확인**

Run: `uv run pytest tests/test_golden.py -v`
Expected: FAIL (골든 파일과 예시 파일이 아직 없음 — `test_matches_golden`은 0건 수집, 예시 테스트는 `FileNotFoundError`)

- [ ] **Step 4: 골든과 예시 생성**

Run: `uv run python scripts/update_golden.py`
Expected: `updated f1-simple-web-app` … `updated f6-long-jobs` 6줄

생성된 `fixtures/f2-sqlite-erp/repo/golden/inventory.json`을 열어 Task 4의 기대 판정과 같은지 눈으로 한 번 확인한다(워크로드 1개, 엔드포인트 6개, `ds-sqlite`가 `ds:local/sqlite/wal`, 요청 경로에 `nw:app/flask-dev/default`).

- [ ] **Step 5: 테스트 통과 확인**

Run: `uv run pytest -v`
Expected: PASS (전체 통과)

- [ ] **Step 6: 커밋**

```bash
git add scripts/update_golden.py fixtures/*/golden schemas/examples tests/test_golden.py
git commit -m "test: pin golden S0-S1 outputs, check determinism and stage examples"
```

---

## 완료 기준

- `uv run pytest`가 전부 통과한다.
- `uv run infrafit kb lint`가 `0개 문제`.
- `uv run infrafit analyze fixtures/f2-sqlite-erp/repo --until S1`이 `out/<run-id>/intake.json`, `inventory.json`을 만들고, `uv run infrafit check-run out/<run-id>`가 `0개 문제`.
- 기대 판정(`expected.yaml`)은 Task 4에서 쓴 그대로이고, 엔진 결과에 맞춰 고친 흔적이 없다.

## 다음 계획

- **계획 2 (S2 프로필):** 이 계획의 실제 `inventory.json`을 입력으로, 차원 탐지기(semgrep 규칙), `candidate` 사실 확정, 엔드포인트별 차원 값과 집계, 도메인 분류, 가정 표, LLM 추론(Claude Agent SDK)과 근거 검사를 만든다.
- **계획 3 (S3·S4·리포트):** 능력 표 226개를 `knowledge/components/*.yaml`로 옮기고, 요구 조건 변환표, 비교 규칙 엔진, 앱 변형, 산정, 비용, 순위, 관점별 대표, 민감도, 분석·추천 리포트를 만든다.
