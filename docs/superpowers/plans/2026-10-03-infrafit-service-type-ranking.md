# S4 서비스 유형별 순위 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** S4 후보 순위를 고정 키("확실성 → 비용")에서 서비스 유형(실시간/장시간 처리/상태 저장/백그라운드/가벼운 웹)마다 다른 기준 순서의 사전식 순위로 바꾸고, 판정 근거·범위 경계(coverage)·후보별 기준 값·decided_by 를 출력한다.

**Architecture:** 지식은 새 `knowledge/ranking.yaml`(유형 판정 조건, 기준 순서, why, refs)에 두고 `kb_lint` 가 검사한다. 순수 함수 모듈 `infrafit/fit/ranking.py` 가 유형 판정·기준 값 계산 도우미·비용 동률·decided_by 를 맡고, `infrafit/fit/recommend.py` 는 조합 순위(`run`)와 services 워크로드별 플랫폼 고르기(`_choose`)에서 그 함수를 쓴다. S1~S3, 규칙, 조합 만들기, 비용 계산, outcome 은 바꾸지 않는다.

**Tech Stack:** Python 3.12, PyYAML, jsonschema, pytest (`.venv/bin/python -m pytest`)

**Spec:** `docs/superpowers/specs/2026-10-03-infrafit-service-type-ranking-design.md`

## Global Constraints

- 저장소: `/Users/jerry/Desktop/workspace/projects/softbank-hackerton/one-click-deploy-agent`, 브랜치 `feat/service-type-ranking`. 테스트는 `.venv/bin/python -m pytest -q` (작업 전 기준 485 passed).
- 가중합 금지. 순위는 사전식이고 유형마다 기준 **순서**만 다르다.
- 모든 유형의 `order` 첫 기준은 `certainty`.
- `cost_tie_ratio: 0.15`. 동률 = 합을 아는 후보 중 최저 합 × 1.15 이하(최저 기준점 하나, 쌍별 비교 아님).
- 유형 판정에는 `source: "detector"` 인 차원 행만 쓴다(`assumption` 제외).
- 능력 값을 모르면 나쁜 쪽(문제 있음)으로 센다.
- 처리 시간 여유 기준(필요 등급 → 요구 상한): 1초 미만 → 60, 수십 초 → 600, 수 분 → 상한 없음, 그 이상 → 상한 없음. 상한 없음 = `CP.platform_request_timeout` 이 `False`.
- `ops_burden` 출력은 유지, 순위에서는 뺀다.
- 범위 선언: `scope: {service_types: 5, criteria: 7}`.
- 코드 주석·docstring·메시지는 한국어, 기존 스타일(짧게)을 따른다.
- 커밋 메시지 끝에 `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`.

## File Structure

| 파일 | 할 일 |
|---|---|
| `knowledge/ranking.yaml` (새) | 범위 선언, 기준 7개, 유형 5개 |
| `infrafit/kb.py` | `ranking()` 로더 |
| `infrafit/kb_lint.py` | `_lint_ranking()` + `lint()` 에 연결 |
| `infrafit/fit/ranking.py` (새) | `CRITERIA`, `classify`, `a2_of`, `lacks_*`, `unsafe_data`, `cost_value`, `sort_key`, `decided_by` |
| `infrafit/fit/recommend.py` | Recommender 에 ranking 연결: `_choose`, `_candidate`, `run`, `build_recommendation(ranking=None)` |
| `infrafit/stages/s4_recommend.py` | `ranking` 인자 + 입력 해시에 포함 |
| `schemas/infrafit.schema.json` | `$defs.Ranking`, `Recommendation.ranking`, `Candidate.criteria`·`decided_by` |
| `tests/test_ranking.py` (새) | 단위·통합 테스트 |
| `tests/test_kb.py` | ranking lint 테스트 |
| `scripts/qa_ranking.py` (새) | 픽스처 f1~f6 순위 표(QA) |
| `README.md`, `recommend.py` docstring | 순위 설명 갱신 |

---

### Task 1: `knowledge/ranking.yaml` + 로더 + lint

**Files:**
- Create: `knowledge/ranking.yaml`
- Modify: `infrafit/kb.py` (끝에 로더 추가)
- Modify: `infrafit/kb_lint.py` (`_lint_ranking` 추가, `lint()` 에 연결)
- Create: `infrafit/fit/ranking.py` (이 태스크에서는 `CRITERIA` 상수만)
- Test: `tests/test_kb.py`

**Interfaces:**
- Produces: `kb.ranking() -> dict` (YAML 그대로), `infrafit.fit.ranking.CRITERIA: tuple[str, ...]`, `kb_lint._lint_ranking(cfg: dict | None = None, detectors: dict | None = None, research_dir=None) -> list[str]`

- [ ] **Step 1: 실패하는 lint 테스트 쓰기** — `tests/test_kb.py` 끝에 추가

```python
import copy

from infrafit import kb
from infrafit.kb_lint import _lint_ranking


def test_ranking_file_passes_lint_and_declares_scope():
    cfg = kb.ranking()
    assert _lint_ranking() == []
    assert cfg["scope"] == {"service_types": 5, "criteria": 7}
    assert [t["id"] for t in cfg["service_types"]] == ["realtime", "long_request", "stateful", "background", "light_web"]
    assert all(t["order"][0] == "certainty" for t in cfg["service_types"])


def test_ranking_lint_catches_bad_entries():
    good = kb.ranking()

    def issues(mutate):
        cfg = copy.deepcopy(good)
        mutate(cfg)
        return " ".join(_lint_ranking(cfg))

    assert "certainty" in issues(lambda c: c["service_types"][0]["order"].reverse())
    assert "nope" in issues(lambda c: c["service_types"][0]["order"].append("nope"))
    assert "Z9" in issues(lambda c: c["service_types"][0]["when"]["any"].append({"dimension": "Z9", "equals": "x"}))
    assert "없는값" in issues(lambda c: c["service_types"][0]["when"]["any"].append({"dimension": "A3", "equals": "없는값"}))
    assert "default" in issues(lambda c: c["service_types"].append(dict(c["service_types"][-1], id="x2")))
    assert "T-999" in issues(lambda c: c["service_types"][0]["refs"].append("T-999"))
    assert "scope" in issues(lambda c: c["scope"].update(criteria=8))
    assert "계산 함수" in issues(lambda c: c["criteria"].append({"id": "latency", "label": "지연", "better": "lower"}))
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/test_kb.py -q`
Expected: FAIL — `ImportError: cannot import name '_lint_ranking'`

- [ ] **Step 3: `knowledge/ranking.yaml` 만들기**

```yaml
# S4 서비스 유형별 순위(설계 docs/superpowers/specs/2026-10-03-infrafit-service-type-ranking-design.md).
#
# 다루는 경우의 수를 선언한다(scope). 이 밖은 coverage(partial|default)로 출력에 표시한다.
# 순위는 사전식이고(설계 §9.7, 가중합 없음) 유형마다 기준 순서(order)만 다르다. 첫 기준은 항상 certainty.
# service_types 는 위에서부터 검사해 처음 맞는 하나를 쓴다. when 은 근거 있는 차원 값(source: detector)만 본다.
# when 연산자: {dimension, equals} | {dimension, in} | {dimension, kinds}(B1·B2·E2 의 kinds 교집합)
#             | {datastores: true}(인벤토리 데이터 저장소가 하나 이상) | {any: [...]} | default(마지막 유형만)
# refs 는 docs/research/considerations/*.md 항목 ID(근거 문서).

scope: {service_types: 5, criteria: 7}
cost_tie_ratio: 0.15

criteria:
  - {id: certainty, label: 확실성, better: lower}
  - {id: cost, label: 비용, better: lower}
  - {id: always_on, label: 상시 응답, capability: CP.always_on, better: lower}
  - {id: request_headroom, label: 처리 시간 여유, capability: CP.max_request_seconds, better: lower}
  - {id: scaling, label: 확장, capability: CP.horizontal_scaling, better: lower}
  - {id: data_safety, label: 데이터 안전, capability: DS.colocated_vm, better: lower}
  - {id: config_burden, label: 설정 부담, better: lower}

service_types:
  - id: realtime
    label: 실시간
    when: {any: [{dimension: A3, equals: "장시간 양방향(웹소켓)"}, {dimension: A1, in: ["실시간 연결"]}]}
    order: [certainty, always_on, scaling, cost, config_burden]
    why: "연결이 끊기지 않아야 하는 서비스라 비용보다 상시 실행과 연결 수 확장이 먼저다"
    refs: [T-006, W-001, T-016]
  - id: long_request
    label: 장시간 처리
    when: {any: [{dimension: A2, in: ["수십 초", "수 분", "그 이상"]}, {dimension: E2, kinds: ["llm-api"]}]}
    order: [certainty, request_headroom, cost, always_on, config_burden]
    why: "요청이 플랫폼 시간 상한에 걸리면 실패하므로, 필요한 처리 시간보다 한 단계 여유 있는 플랫폼이 먼저다"
    refs: [W-011, W-080, C-060]
  - id: stateful
    label: 상태 저장
    when: {any: [{dimension: B1, equals: "있음"}, {dimension: B2, equals: "있음"}, {datastores: true}]}
    order: [certainty, data_safety, cost, config_burden]
    why: "데이터를 잃으면 되돌릴 수 없으므로 관리형 저장소(백업·내구성)가 비용보다 먼저다"
    refs: [T-009, C-028, COST-098]
  - id: background
    label: 백그라운드
    when: {any: [{dimension: A1, in: ["워커", "정기 작업"]}, {dimension: B3, equals: "있음"}, {dimension: A4, equals: "있음"}]}
    order: [certainty, always_on, cost, config_burden]
    why: "요청이 없을 때도 작업이 돌아야 하므로 상시 실행이 비용보다 먼저다"
    refs: [C-093, W-018, T-013]
  - id: light_web
    label: 가벼운 웹
    when: default
    order: [certainty, cost, config_burden, always_on]
    why: "요청이 짧고 가끔 오는 서비스라 비용이 가장 중요하고, 요청 과금 플랫폼이 유리하다"
    refs: [COST-068, T-016, COST-008]
```

- [ ] **Step 4: `infrafit/fit/ranking.py` 시작 (CRITERIA 만)**

```python
"""S4 서비스 유형별 순위(knowledge/ranking.yaml, 설계 2026-10-03-infrafit-service-type-ranking-design.md).

유형 판정, 기준 값 계산 도우미, 비용 동률, decided_by. 순위는 사전식이고 유형마다 기준 순서만 다르다.
"""

from __future__ import annotations

# 계산 함수가 있는 기준. ranking.yaml criteria 는 이 안에서만 고른다(kb_lint)
CRITERIA = ("certainty", "cost", "always_on", "request_headroom", "scaling", "data_safety", "config_burden")
```

- [ ] **Step 5: `infrafit/kb.py` 끝에 로더 추가**

```python
@lru_cache(maxsize=1)
def ranking() -> dict:
    """S4 서비스 유형별 순위(knowledge/ranking.yaml)."""
    return _load("ranking.yaml")
```

- [ ] **Step 6: `infrafit/kb_lint.py` 에 `_lint_ranking` 추가** — `def lint()` 바로 위에 넣는다. 파일 위쪽 import(`from infrafit import kb` 아래)에 `from infrafit.fit.ranking import CRITERIA` 를 추가한다(`re` 는 이미 import 되어 있다).

```python
CONSIDERATION_ID = re.compile(r"^#{2,4} +([A-Z]+-\d+)\b", re.M)
RANKING_LEAF_KEYS = ({"dimension", "equals"}, {"dimension", "in"}, {"dimension", "kinds"}, {"datastores"})


def _consideration_ids(research_dir) -> set[str]:
    ids: set[str] = set()
    for path in sorted((research_dir / "considerations").glob("*.md")):
        ids |= set(CONSIDERATION_ID.findall(path.read_text(encoding="utf-8")))
    return ids


def _lint_ranking(cfg: dict | None = None, detectors: dict | None = None, research_dir=None) -> list[str]:
    """ranking.yaml: 범위 숫자, 기준 id(계산 함수 있음), 유형 when 어휘·order·default·refs."""
    cfg = kb.ranking() if cfg is None else cfg
    dims = (kb.profile_detectors() if detectors is None else detectors).get("dimensions") or {}
    research_dir = RESEARCH_DIR if research_dir is None else research_dir
    known_refs = _consideration_ids(research_dir)
    issues: list[str] = []
    criteria = [c.get("id") for c in cfg.get("criteria") or []]
    types = cfg.get("service_types") or []
    scope = cfg.get("scope") or {}
    if scope.get("criteria") != len(criteria) or scope.get("service_types") != len(types):
        issues.append(f"ranking: scope {scope} 가 실제 개수(criteria {len(criteria)}, service_types {len(types)})와 다름")
    for cid in criteria:
        if cid not in CRITERIA:
            issues.append(f"ranking: 기준 {cid} 의 계산 함수가 없음 (infrafit/fit/ranking.py CRITERIA)")
    if len(set(criteria)) != len(criteria):
        issues.append("ranking: 기준 id 중복")
    if not isinstance(cfg.get("cost_tie_ratio"), (int, float)) or not 0 <= cfg["cost_tie_ratio"] < 1:
        issues.append("ranking: cost_tie_ratio 는 0 이상 1 미만 숫자")
    defaults = [i for i, t in enumerate(types) if t.get("when") == "default"]
    if defaults != [len(types) - 1]:
        issues.append("ranking: when: default 는 마지막 유형 하나만")
    seen: set[str] = set()
    for t in types:
        tid = str(t.get("id"))
        if tid in seen:
            issues.append(f"ranking: 유형 id 중복 {tid}")
        seen.add(tid)
        order = t.get("order") or []
        if not order or order[0] != "certainty":
            issues.append(f"ranking {tid}: order 첫 기준은 certainty")
        for c in order:
            if c not in criteria:
                issues.append(f"ranking {tid}: order 의 {c} 가 criteria 에 없음")
        if not t.get("label") or not t.get("why"):
            issues.append(f"ranking {tid}: label·why 필수")
        refs = t.get("refs") or []
        if not refs:
            issues.append(f"ranking {tid}: refs 필수")
        for ref in refs:
            if ref not in known_refs:
                issues.append(f"ranking {tid}: refs {ref} 가 docs/research/considerations 에 없음")
        when = t.get("when")
        if when == "default":
            continue
        leaves = when.get("any") if isinstance(when, dict) and set(when) == {"any"} else [when]
        for leaf in leaves or []:
            if not isinstance(leaf, dict) or set(leaf) not in RANKING_LEAF_KEYS:
                issues.append(f"ranking {tid}: when 형식 오류 {leaf}")
                continue
            if "datastores" in leaf:
                continue
            dim = leaf["dimension"]
            if dim not in dims:
                issues.append(f"ranking {tid}: when.dimension {dim} 은 profile_detectors.yaml 에 없는 차원")
                continue
            vocab = dims[dim].get("values") or []
            values = [leaf["equals"]] if "equals" in leaf else (leaf.get("in") or [])
            for v in values:
                if v not in vocab:
                    issues.append(f"ranking {tid}: {dim} 값 {v} 가 어휘 {vocab} 에 없음")
            if "kinds" in leaf and not (isinstance(leaf["kinds"], list) and leaf["kinds"]):
                issues.append(f"ranking {tid}: kinds 는 비어 있지 않은 목록")
    return issues
```

그리고 `lint()` 의 반환식 끝에 `+ _lint_ranking()` 을 붙인다:

```python
            + _lint_rule_vocabulary() + _lint_profile_detectors() + _lint_ranking())
```

- [ ] **Step 7: 통과 확인**

Run: `.venv/bin/python -m pytest tests/test_kb.py -q`
Expected: PASS. 순환 import 오류가 나면(`infrafit.fit.ranking` → 아무것도 import 하지 않으므로 나면 안 됨) 원인을 확인한다.

- [ ] **Step 8: 전체 테스트**

Run: `.venv/bin/python -m pytest -q`
Expected: 487 passed (`test_knowledge_files_pass_lint` 가 새 lint 도 돌린다)

- [ ] **Step 9: 커밋**

```bash
git add knowledge/ranking.yaml infrafit/kb.py infrafit/kb_lint.py infrafit/fit/ranking.py tests/test_kb.py
git commit -m "Add knowledge/ranking.yaml (service types, criteria order, scope) with loader and lint

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: 유형 판정 `classify`

**Files:**
- Modify: `infrafit/fit/ranking.py`
- Test: `tests/test_ranking.py` (새)

**Interfaces:**
- Consumes: `kb.ranking()` (Task 1), `infrafit.fit.engine.match_when`, `dim_value`
- Produces: `classify(dims: list[dict], datastores: list[dict], cfg: dict) -> dict` — 반환은 출력 `ranking` 블록 그대로:
  `{"service_type", "label", "coverage": "full"|"partial"|"default", "matched": [{"type", "by": [{"dimension", "value", "at": [str]}]}], "unprioritized": [str], "default_reason": str|None, "criteria_order": [str], "why", "refs": [str], "scope": dict}`

- [ ] **Step 1: 실패하는 테스트 쓰기** — `tests/test_ranking.py`

```python
"""S4 서비스 유형별 순위(knowledge/ranking.yaml)."""

from infrafit import kb
from infrafit.fit.ranking import classify


def dim(d, value, source="detector", path="app.py", line=3, scope="w-web"):
    return {"dimension": d, "scope": scope, "value": value, "source": source, "confidence": "high",
            "evidence": [{"path": path, "line": line, "snippet": f"{d} signal"}]}


DS = [{"id": "ds-pg", "role": "primary-db", "used_by": ["w-web"], "status": "confirmed",
       "evidence": [{"path": "db.js", "line": 2, "snippet": "new Pool()"}]}]


def test_single_type_is_full_coverage_with_evidence():
    r = classify([dim("A3", "장시간 양방향(웹소켓)", path="server.js", line=12)], [], kb.ranking())
    assert r["service_type"] == "realtime" and r["label"] == "실시간"
    assert r["coverage"] == "full" and r["unprioritized"] == [] and r["default_reason"] is None
    assert r["matched"] == [{"type": "realtime",
                             "by": [{"dimension": "A3", "value": "장시간 양방향(웹소켓)", "at": ["server.js:12"]}]}]
    assert r["criteria_order"] == ["certainty", "always_on", "scaling", "cost", "config_burden"]
    assert r["refs"] == ["T-006", "W-001", "T-016"] and r["scope"] == {"service_types": 5, "criteria": 7}


def test_higher_type_wins_and_rest_is_unprioritized():
    dims = [dim("B2", {"value": "있음", "kinds": ["sqlite"]}), dim("A1", ["웹", "실시간 연결"])]
    r = classify(dims, DS, kb.ranking())
    assert r["service_type"] == "realtime" and r["coverage"] == "partial"
    assert [m["type"] for m in r["matched"]] == ["realtime", "stateful"]
    assert r["unprioritized"] == ["stateful"]
    stateful = r["matched"][1]["by"]
    assert {"dimension": "datastores", "value": "ds-pg", "at": ["db.js:2"]} in stateful


def test_assumption_rows_do_not_classify():
    r = classify([dim("A2", "수십 초", source="assumption"), dim("A1", ["웹"])], [], kb.ranking())
    assert r["service_type"] == "light_web" and r["coverage"] == "default"
    assert r["matched"] == [] and r["default_reason"]


def test_llm_api_kind_is_long_request():
    r = classify([dim("E2", {"value": "있음", "kinds": ["llm-api", "payments"]})], [], kb.ranking())
    assert r["service_type"] == "long_request"
    assert r["matched"][0]["by"][0]["dimension"] == "E2"


def test_datastores_alone_is_stateful_and_background_detected():
    assert classify([], DS, kb.ranking())["service_type"] == "stateful"
    r = classify([dim("A1", ["워커"])], [], kb.ranking())
    assert r["service_type"] == "background" and r["coverage"] == "full"


def test_same_evidence_across_workloads_is_deduplicated():
    dims = [dim("A3", "장시간 양방향(웹소켓)", scope="w-a"), dim("A3", "장시간 양방향(웹소켓)", scope="w-b")]
    r = classify(dims, [], kb.ranking())
    assert r["matched"][0]["by"] == [{"dimension": "A3", "value": "장시간 양방향(웹소켓)", "at": ["app.py:3"]}]
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/test_ranking.py -q`
Expected: FAIL — `ImportError: cannot import name 'classify'`

- [ ] **Step 3: `classify` 구현** — `infrafit/fit/ranking.py` 에 추가 (import 를 파일 위로 올린다)

```python
from infrafit.fit.engine import dim_value, match_when

DEFAULT_REASON = "근거 있는 차원 값이 어느 유형 조건에도 맞지 않음"


def _at(evidence) -> list[str]:
    out = []
    for e in evidence or []:
        if e.get("path"):
            out.append(f"{e['path']}:{e['line']}" if e.get("line") else e["path"])
    return out


def _hits(when: dict, dims: list[dict], datastores: list[dict]) -> list[dict] | None:
    """조건에 맞으면 근거 목록 [{dimension, value, at}], 아니면 None."""
    if "any" in when:
        found = [h for child in when["any"] if (h := _hits(child, dims, datastores)) is not None]
        return [x for h in found for x in h] if found else None
    if "datastores" in when:
        if bool(datastores) != bool(when["datastores"]):
            return None
        return [{"dimension": "datastores", "value": d["id"], "at": _at(d.get("evidence"))} for d in datastores]
    if "kinds" in when:
        rows = [d for d in dims if d["dimension"] == when["dimension"] and isinstance(d.get("value"), dict)
                and set(d["value"].get("kinds") or []) & set(when["kinds"])]
    else:
        rows = match_when(when, dims)
    if not rows:
        return None
    return [{"dimension": d["dimension"], "value": dim_value(d.get("value")), "at": _at(d.get("evidence"))}
            for d in rows]


def _dedupe(hits: list[dict]) -> list[dict]:
    out: list[dict] = []
    for h in hits:
        same = next((o for o in out if o["dimension"] == h["dimension"] and o["value"] == h["value"]), None)
        if same is None:
            out.append({**h, "at": list(dict.fromkeys(h["at"]))})
        else:
            same["at"] = list(dict.fromkeys(same["at"] + h["at"]))
    return out


def classify(dims: list[dict], datastores: list[dict], cfg: dict) -> dict:
    """앱 워크로드 차원 행(근거 있는 것만)과 데이터 저장소로 서비스 유형 하나를 고른다. 출력 `ranking` 블록."""
    usable = [d for d in dims if d.get("source") == "detector"]
    types = cfg["service_types"]
    matched = []
    for t in types:
        if t["when"] == "default":
            continue
        hits = _hits(t["when"], usable, datastores)
        if hits is not None:
            matched.append({"type": t["id"], "by": _dedupe(hits)})
    chosen = next((t for t in types if matched and t["id"] == matched[0]["type"]), None) \
        or next(t for t in types if t["when"] == "default")
    if not matched:
        coverage = "default"
    elif len(matched) == 1:
        coverage = "full"
    else:
        coverage = "partial"
    return {
        "service_type": chosen["id"], "label": chosen["label"], "coverage": coverage, "matched": matched,
        "unprioritized": [m["type"] for m in matched[1:]],
        "default_reason": None if matched else DEFAULT_REASON,
        "criteria_order": list(chosen["order"]), "why": chosen["why"], "refs": list(chosen["refs"]),
        "scope": dict(cfg["scope"]),
    }
```

(`matched` 는 `types` 순서로 쌓이므로 `matched[0]` 이 가장 위 유형이다.)

- [ ] **Step 4: 통과 확인**

Run: `.venv/bin/python -m pytest tests/test_ranking.py -q`
Expected: 6 passed

- [ ] **Step 5: 커밋**

```bash
git add infrafit/fit/ranking.py tests/test_ranking.py
git commit -m "Classify service type from detector dimensions with coverage and evidence

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: 기준 값 도우미, 비용 동률, decided_by

**Files:**
- Modify: `infrafit/fit/ranking.py`
- Test: `tests/test_ranking.py`

**Interfaces:**
- Consumes: `infrafit.fit.engine.cap_value(component, key)`
- Produces:
  - `A2_ORDER: tuple[str, ...]`, `SCALING_KINDS = ("web", "realtime")`
  - `a2_of(dims: list[dict]) -> str | None` — 근거 있는 A2 중 가장 높은 값
  - `lacks_always_on(component: dict | None) -> bool`
  - `lacks_headroom(component: dict | None, a2: str | None) -> bool`
  - `lacks_scaling(component: dict | None) -> bool`
  - `unsafe_data(cid: str, component: dict | None) -> bool`
  - `cost_value(total: float | None, unknown_n: int, partial: float, cheapest: float | None, ratio: float) -> tuple`
  - `sort_key(values: dict, order: list[str]) -> tuple`
  - `decided_by(rows: list[tuple[str, dict]], order: list[str]) -> list[dict | None]`

- [ ] **Step 1: 실패하는 테스트 추가** — `tests/test_ranking.py` 끝에

```python
from infrafit.fit.ranking import (a2_of, cost_value, decided_by, lacks_always_on, lacks_headroom, lacks_scaling,
                                  sort_key, unsafe_data)


def comp(**caps):
    return {"id": "cp:x/y/z", "capabilities": {k.replace("__", "."): {"value": v} for k, v in caps.items()}}


def test_a2_of_takes_highest_detector_value():
    assert a2_of([dim("A2", "수십 초"), dim("A2", "수 분"), dim("A2", "그 이상", source="assumption")]) == "수 분"
    assert a2_of([dim("A2", "1초 미만", source="assumption")]) is None


def test_headroom_needs_one_tier_above():
    limited = comp(CP__platform_request_timeout=True, CP__max_request_seconds=300)
    long_ok = comp(CP__platform_request_timeout=True, CP__max_request_seconds=3600)
    unlimited = comp(CP__platform_request_timeout=False)
    unknown = comp(CP__platform_request_timeout=True)
    assert lacks_headroom(limited, "수십 초") is True        # 600 미만
    assert lacks_headroom(long_ok, "수십 초") is False
    assert lacks_headroom(long_ok, "수 분") is True          # 상한 없음이 필요
    assert lacks_headroom(unlimited, "그 이상") is False
    assert lacks_headroom(unknown, "수십 초") is True        # 모르면 나쁜 쪽
    assert lacks_headroom(limited, None) is False            # 근거 있는 A2 없음
    assert lacks_headroom(comp(CP__platform_request_timeout=True, CP__max_request_seconds=60), "1초 미만") is False


def test_capability_flags_count_unknown_as_bad():
    assert lacks_always_on(comp(CP__always_on=True)) is False
    assert lacks_always_on(comp(CP__always_on=False)) is True
    assert lacks_always_on(None) is True
    assert lacks_scaling(comp(CP__horizontal_scaling=True)) is False
    assert lacks_scaling(comp()) is True
    assert unsafe_data("ds:vm/compose-postgres/default", comp(DS__colocated_vm=True)) is True
    assert unsafe_data("ds:local/sqlite/wal", None) is True
    assert unsafe_data("ds:aws/rds-postgres/single-az", comp(DS__engine="postgres")) is False


def test_cost_value_ties_within_ratio_of_cheapest():
    assert cost_value(10.0, 0, 10.0, 10.0, 0.15) == (False, 0.0, 0)
    assert cost_value(11.5, 0, 11.5, 10.0, 0.15) == (False, 0.0, 0)
    assert cost_value(11.6, 0, 11.6, 10.0, 0.15) == (False, 11.6, 0)
    assert cost_value(0.0, 0, 0.0, 0.0, 0.15) == (False, 0.0, 0)
    assert cost_value(1.0, 0, 1.0, 0.0, 0.15) == (False, 1.0, 0)
    assert cost_value(None, 2, 5.0, 10.0, 0.15) == (True, 2, 5.0)
    assert cost_value(None, 1, 0, None, 0.15) > cost_value(99.0, 0, 99.0, 1.0, 0.15)


def test_sort_key_and_decided_by_follow_order():
    order = ["certainty", "always_on", "cost"]
    a = {"certainty": (False, 0, 0), "always_on": 0, "cost": (False, 30.0, 0), "scaling": 9}
    b = {"certainty": (False, 0, 0), "always_on": 1, "cost": (False, 0.0, 0), "scaling": 0}
    c = {"certainty": (False, 0, 0), "always_on": 1, "cost": (False, 0.0, 0), "scaling": 0}
    assert sort_key(a, order) < sort_key(b, order)
    assert decided_by([("C1", a), ("C2", b), ("C3", c)], order) == [
        {"criterion": "always_on", "over": "C2"}, {"criterion": "name", "over": "C3"}, None]
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/test_ranking.py -q`
Expected: FAIL — `ImportError: cannot import name 'a2_of'`

- [ ] **Step 3: 구현** — `infrafit/fit/ranking.py` 에 추가 (`cap_value` 를 engine import 에 더한다: `from infrafit.fit.engine import cap_value, dim_value, match_when`)

```python
A2_ORDER = ("1초 미만", "수십 초", "수 분", "그 이상")
# 필요 등급 → 한 단계 여유 있는 요청 상한(초). None = 상한이 없어야 함(CP.platform_request_timeout false)
HEADROOM_NEED = {"1초 미만": 60, "수십 초": 600, "수 분": None, "그 이상": None}
SCALING_KINDS = ("web", "realtime")


def a2_of(dims: list[dict]) -> str | None:
    """근거 있는(detector) A2 값 중 가장 높은 등급. 없으면 None."""
    vals = [dim_value(d.get("value")) for d in dims if d["dimension"] == "A2" and d.get("source") == "detector"]
    vals = [v for v in vals if v in A2_ORDER]
    return max(vals, key=A2_ORDER.index) if vals else None


def lacks_always_on(component: dict | None) -> bool:
    return cap_value(component, "CP.always_on") is not True


def lacks_headroom(component: dict | None, a2: str | None) -> bool:
    """필요 등급보다 한 단계 위 상한이 없는가. 근거 있는 A2 가 없으면 따지지 않는다. 상한을 모르면 여유 없음."""
    if a2 not in HEADROOM_NEED:
        return False
    if cap_value(component, "CP.platform_request_timeout") is False:
        return False
    need = HEADROOM_NEED[a2]
    if need is None:
        return True
    limit = cap_value(component, "CP.max_request_seconds")
    return not (isinstance(limit, (int, float)) and not isinstance(limit, bool) and limit >= need)


def lacks_scaling(component: dict | None) -> bool:
    return cap_value(component, "CP.horizontal_scaling") is not True


def unsafe_data(cid: str, component: dict | None) -> bool:
    """VM 안 컨테이너 저장소나 로컬 SQLite 인가(관리형·BaaS 가 아님)."""
    return (cap_value(component, "DS.colocated_vm") is True or cap_value(component, "DS.engine") == "sqlite"
            or cid.startswith("ds:local/sqlite"))


def cost_value(total: float | None, unknown_n: int, partial: float, cheapest: float | None, ratio: float) -> tuple:
    """비용 기준 값. 합을 모르면 (True, 모르는 수, 아는 부분합). 알면 최저 합 × (1 + ratio) 이하는 0(동률)."""
    if total is None:
        return (True, unknown_n, partial)
    tied = cheapest is not None and total <= cheapest * (1 + ratio)
    return (False, 0.0 if tied else total, 0)


def sort_key(values: dict, order: list[str]) -> tuple:
    return tuple(values[c] for c in order)


def decided_by(rows: list[tuple[str, dict]], order: list[str]) -> list[dict | None]:
    """순위 순서의 (id, 기준 값)마다 바로 다음 후보와 처음 갈린 기준. 마지막은 None."""
    out: list[dict | None] = []
    for i, (_, vals) in enumerate(rows):
        if i + 1 == len(rows):
            out.append(None)
            continue
        nid, nvals = rows[i + 1]
        out.append({"criterion": next((c for c in order if vals[c] != nvals[c]), "name"), "over": nid})
    return out
```

`cap_value(component, key)` 는 `capabilities[key]["value"]` 를 돌려주고 키가 없거나 `None`/`"unknown"` 이면 `None` 이다(engine.py:28-44). `source` 는 요구하지 않으므로 테스트의 `comp()` 처럼 `{"value": v}` 만 넣어도 된다.

- [ ] **Step 4: 통과 확인**

Run: `.venv/bin/python -m pytest tests/test_ranking.py -q`
Expected: 11 passed

- [ ] **Step 5: 커밋**

```bash
git add infrafit/fit/ranking.py tests/test_ranking.py
git commit -m "Add ranking criteria helpers: one-tier request headroom, cost tie to cheapest, decided_by

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: S4 에 연결 + 스키마 + 입력 해시

**Files:**
- Modify: `infrafit/fit/recommend.py` (`Recommender.__init__`, `_choose`, `_candidate`, `run`, `build_recommendation`)
- Modify: `infrafit/stages/s4_recommend.py`
- Modify: `schemas/infrafit.schema.json` (`$defs.Ranking` 새로, `Recommendation.properties.ranking`, `Candidate.properties.criteria`·`decided_by`)
- Test: `tests/test_ranking.py`

**Interfaces:**
- Consumes: Task 2·3 의 모든 함수, `kb.ranking()`
- Produces: `build_recommendation(inventory, profile, fit, capabilities, rules, ranking: dict | None = None) -> dict` — 결과에 `ranking`(classify 블록), 후보마다 `criteria`·`decided_by`. `run_s4(ctx, inventory, profile, fit, capabilities=None, rules=None, ranking=None)`.

- [ ] **Step 1: 실패하는 통합 테스트 추가** — `tests/test_ranking.py` 끝에

```python
from infrafit.consistency import check_s4
from infrafit.fit.matrix import build_fit
from infrafit.fit.recommend import build_recommendation
from infrafit.schema import validate

RUN = "cp:gcp/cloud-run/unspecified"
EC2 = "cp:aws/ec2/docker-compose"
ECS = "cp:aws/ecs/unspecified"
WS_RULE = {"id": "CAP-WEBSOCKET-001", "when": {"dimension": "A3", "equals": "장시간 양방향(웹소켓)"},
           "require": {"capability": "CP.websocket", "equals": True}, "otherwise": "infeasible",
           "config_from": None, "message": "websocket needed"}


def capc(cid, cloud, target, cost, **caps):
    src = {"doc": "capabilities/05-compute-tier1-2.md", "line": 10, "url": "https://example.com/doc", "quote": "q"}
    c = {"id": cid, "cloud": cloud, "family": "cp", "ops_burden": "low", "target": target,
         "capabilities": {k.replace("__", "."): {"value": v, "source": src} for k, v in caps.items()}}
    c["capabilities"]["COST.monthly_floor_usd"] = {"value": cost, "source": src}
    return c


def three_platforms(run_cost=0, ecs_cost=30, with_ec2=True):
    caps = [capc(RUN, "gcp", "gcp_cloud_run", run_cost, CP__websocket=True, CP__always_on=False,
                 CP__horizontal_scaling=True),
            capc(ECS, "aws", "aws_ecs_fargate", ecs_cost, CP__websocket=True, CP__always_on=True,
                 CP__horizontal_scaling=True)]
    if with_ec2:
        caps.append(capc(EC2, "aws", "aws_ec2", 10, CP__websocket=True, CP__always_on=True,
                         CP__horizontal_scaling=False))
    return caps


def web_inventory():
    return {"workloads": [{"id": "w-web", "kind": "web", "name": "web", "status": "confirmed",
                           "entrypoint": {"path": "app.py", "line": 1, "snippet": "app"}}],
            "endpoints": [], "request_paths": [], "datastores": [], "current_components": []}


def prof(*dims):
    return {"domain": {"value": "x", "votes": []}, "dimensions": list(dims), "assumptions": [],
            "dropped_inferences": [], "llm_used": False, "resolutions": []}


def recommend(p, caps):
    inv = web_inventory()
    fit = build_fit(inv, p, caps, [WS_RULE])
    rec = build_recommendation(inv, p, fit, caps, [WS_RULE])
    return rec, fit, inv


def compute_order(rec):
    return [c["placement"][0]["component"] for c in rec["candidates"]]


def test_same_candidates_rank_differently_by_service_type():
    caps = three_platforms()
    realtime, fit, inv = recommend(prof(dim("A3", "장시간 양방향(웹소켓)")), caps)
    assert realtime["ranking"]["service_type"] == "realtime"
    assert compute_order(realtime) == [ECS, EC2, RUN]     # 상시 응답 → 확장 → 비용
    assert [c["decided_by"] for c in realtime["candidates"]] == [
        {"criterion": "scaling", "over": "C2"}, {"criterion": "always_on", "over": "C3"}, None]
    light, _, _ = recommend(prof(), caps)
    assert light["ranking"]["service_type"] == "light_web" and light["ranking"]["coverage"] == "default"
    assert compute_order(light) == [RUN, EC2, ECS]        # 비용 0 < 10 < 30
    for rec in (realtime, light):
        for cand in rec["candidates"]:
            validate("Candidate", cand)
    assert check_s4(realtime, fit, inv, prof(dim("A3", "장시간 양방향(웹소켓)"))) == []


def test_cost_within_tie_ratio_falls_through_to_next_criterion():
    tied, _, _ = recommend(prof(), three_platforms(run_cost=10, ecs_cost=11, with_ec2=False))
    assert compute_order(tied) == [ECS, RUN]               # 11 ≤ 10×1.15 동률 → 상시 응답에서 ECS
    assert tied["candidates"][0]["decided_by"] == {"criterion": "always_on", "over": "C2"}
    assert tied["candidates"][0]["criteria"]["cost"] == {"monthly_usd": 11.0, "tied_with_cheapest": True}
    apart, _, _ = recommend(prof(), three_platforms(run_cost=10, ecs_cost=12, with_ec2=False))
    assert compute_order(apart) == [RUN, ECS]
    assert apart["candidates"][0]["decided_by"]["criterion"] == "cost"


def test_candidate_criteria_lists_all_seven():
    rec, _, _ = recommend(prof(dim("A3", "장시간 양방향(웹소켓)")), three_platforms())
    crit = rec["candidates"][0]["criteria"]
    assert set(crit) == {"certainty", "cost", "always_on", "request_headroom", "scaling", "data_safety",
                         "config_burden"}
    assert crit["certainty"] == {"evidence_unknown": False, "unknown_cost_components": 0, "unknown_count": 0}
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/test_ranking.py -q`
Expected: FAIL — `KeyError: 'ranking'`

- [ ] **Step 3: `recommend.py` import 와 `__init__`**

파일 위 import 에 추가:

```python
from infrafit import kb
from infrafit.fit.ranking import (SCALING_KINDS, a2_of, classify, cost_value, decided_by, lacks_always_on,
                                  lacks_headroom, lacks_scaling, sort_key, unsafe_data)
```

`Recommender.__init__` 시그니처와 끝부분:

```python
    def __init__(self, inventory: dict, profile: dict, fit: dict, capabilities: list[dict], rules: list[dict],
                 ranking: dict):
        ...  # 기존 줄 그대로
        self.pin_rules = {r["id"] for r in rules if r.get("config_from") in PIN_CONFIG_KEYS}
        # 서비스 유형별 순위: 앱 워크로드(리버스 프록시 제외)의 차원으로 유형 하나를 정한다
        self.workloads = [s for s in self.app if s.workload_kind != "reverse-proxy"]
        self.ranking = classify([d for s in self.workloads for d in s.dims], inventory.get("datastores", []), ranking)
        self.order = self.ranking["criteria_order"]
        self.tie_ratio = float(ranking["cost_tie_ratio"])
```

- [ ] **Step 4: `_choose` 를 유형 순서로** — 기존 `_choose` 전체를 교체

```python
    def _choose(self, scope: Scope, options: list[str], transformed: bool):
        """services: 워크로드 하나에 둘 플랫폼(유형의 기준 순서 → 과금 방식 → ID). (선택 또는 None, 탈락 사유)"""
        rows, reasons = [], []
        for cid in options:
            cell, ev = self._cell(scope, cid, transformed)
            if cell["result"] == "infeasible":
                reasons += [{"type": "violation", "detail": f"{scope.id} × {cid} — {v['rule']}: {v.get('message', '')}",
                             "violation": v} for v in cell["violations"]]
                continue
            rows.append((cid, cell, ev, self._option_cost(scope, cid, cell)))
        cheapest = min((cost for *_, cost in rows if cost is not None), default=None)
        a2 = a2_of(scope.dims)
        scored = []
        for cid, cell, ev, cost in rows:
            comp = self.components.get(cid)
            values = {
                "certainty": (bool(ev and cell["result"] == "unknown"), cost is None, cell["result"] == "unknown"),
                "cost": cost_value(cost, int(cost is None), 0.0, cheapest, self.tie_ratio),
                "always_on": int(lacks_always_on(comp)),
                "request_headroom": int(lacks_headroom(comp, a2)),
                "scaling": int(scope.workload_kind in SCALING_KINDS and lacks_scaling(comp)),
                "data_safety": 0,
                "config_burden": len(cell["requires_config"]),
            }
            scored.append((sort_key(values, self.order) + (self._mode_key(scope, cid), cid), cid))
        scored.sort()
        return (scored[0][1] if scored else None), reasons
```

- [ ] **Step 5: `_candidate` 에 기준 값** — `_candidate` 의 `return` 직전에 계산을 넣고, 반환 dict 의 `"_sort"` 를 아래 두 키로 바꾼다

```python
        def placed(sid):
            return self.components.get(combo.assignment.get(sid))

        here = [s for s in self.workloads if s.id in combo.assignment]
        certainty = (combo.evidence_unknown > 0, len(unknown_cost), unknown_cells + len(unknown_cost))
        values = {
            "certainty": certainty,
            "cost": None,   # run()에서 최저 합을 알고 나서 채운다
            "always_on": sum(lacks_always_on(placed(s.id)) for s in here),
            "request_headroom": sum(lacks_headroom(placed(s.id), a2_of(s.dims)) for s in here),
            "scaling": sum(s.workload_kind in SCALING_KINDS and lacks_scaling(placed(s.id)) for s in here),
            "data_safety": sum(unsafe_data(combo.assignment[s.id], self.components.get(combo.assignment[s.id]))
                               for s in self.data if s.id in combo.assignment and not s.external),
            "config_burden": configs + len(used),
        }
```

반환 dict 에서 기존 `"_sort": (...)` 줄을 지우고:

```python
            # 순위에만 쓰고 출력하지 않는다
            "_values": values,
            "_cost": (None if unknown_cost else total, len(unknown_cost), total),
            "_name": combo.name,
```

`sum()` 의 bool 합은 int 다. `values` 의 각 값이 int 인지(bool 아님) 확인하고, bool 이 남으면 `int(...)` 로 감싼다.

- [ ] **Step 6: `run` 의 정렬 교체** — `feasible.sort(...)` 부터 `del cand["_sort"]` 까지를 교체

```python
        cheapest = min((c["_cost"][0] for c in feasible if c["_cost"][0] is not None), default=None)
        for cand in feasible:
            total, unknown_n, partial = cand["_cost"]
            cand["_values"]["cost"] = cost_value(total, unknown_n, partial, cheapest, self.tie_ratio)
        feasible.sort(key=lambda c: sort_key(c["_values"], self.order) + (c["_name"],))
        for i, cand in enumerate(feasible, start=1):
            cand["id"], cand["rank"] = f"C{i}", i
        for cand, why in zip(feasible, decided_by([(c["id"], c["_values"]) for c in feasible], self.order)):
            v, total = cand["_values"], cand["_cost"][0]
            cand["criteria"] = {
                "certainty": {"evidence_unknown": v["certainty"][0], "unknown_cost_components": v["certainty"][1],
                              "unknown_count": v["certainty"][2]},
                "cost": {"monthly_usd": total, "tied_with_cheapest": total is not None and v["cost"][1] == 0.0},
                **{k: v[k] for k in ("always_on", "request_headroom", "scaling", "data_safety", "config_burden")},
            }
            cand["decided_by"] = why
            for k in ("_values", "_cost", "_name"):
                del cand[k]
```

같은 함수의 반환 dict 에 `"ranking": self.ranking,` 을 추가한다(`"perspectives": None,` 아래).

- [ ] **Step 7: `build_recommendation` 과 `run_s4`**

`recommend.py` 끝:

```python
def build_recommendation(inventory: dict, profile: dict, fit: dict,
                         capabilities: list[dict], rules: list[dict], ranking: dict | None = None) -> dict:
    return Recommender(inventory, profile, fit, capabilities, rules,
                       kb.ranking() if ranking is None else ranking).run()
```

`infrafit/stages/s4_recommend.py` 의 `run_s4` 전체:

```python
def run_s4(ctx: RunContext, inventory: dict, profile: dict, fit: dict,
           capabilities: list[dict] | None = None, rules: list[dict] | None = None,
           ranking: dict | None = None) -> dict:
    started = now_iso()
    capabilities = list(kb.capabilities().values()) if capabilities is None else capabilities
    rules = list(kb.rules()) if rules is None else rules
    ranking = kb.ranking() if ranking is None else ranking
    h = input_hash("S4", body_of(inventory), body_of(profile), body_of(fit), capabilities, rules, ranking,
                   code_version())
    cached = ctx.cached("S4", h)
    if cached is not None:
        return cached
    body = build_recommendation(inventory, profile, fit, capabilities, rules, ranking)
    return ctx.write_stage("S4", body, input_hash=h, started_at=started)
```

- [ ] **Step 8: 스키마** — `schemas/infrafit.schema.json` 을 Python 으로 고친다(들여쓰기 2칸, `ensure_ascii=False` 유지 — 고치기 전에 파일이 `json.dumps(..., indent=2, ensure_ascii=False)` 형식과 같은지 `git diff --stat` 로 확인하고, 다르면 손으로 같은 내용을 넣는다)

```bash
.venv/bin/python - <<'EOF'
import json
from pathlib import Path
p = Path("schemas/infrafit.schema.json")
s = json.loads(p.read_text(encoding="utf-8"))
d = s["$defs"]
crit = ["certainty", "cost", "always_on", "request_headroom", "scaling", "data_safety", "config_burden"]
d["Ranking"] = {
    "type": "object", "additionalProperties": False,
    "required": ["service_type", "label", "coverage", "matched", "unprioritized", "default_reason",
                 "criteria_order", "why", "refs", "scope"],
    "properties": {
        "service_type": {"type": "string"}, "label": {"type": "string"},
        "coverage": {"type": "string", "enum": ["full", "partial", "default"]},
        "matched": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["type", "by"],
            "properties": {"type": {"type": "string"}, "by": {"type": "array", "items": {
                "type": "object", "additionalProperties": False, "required": ["dimension", "value", "at"],
                "properties": {"dimension": {"type": "string"}, "value": {},
                               "at": {"type": "array", "items": {"type": "string"}}}}}}}},
        "unprioritized": {"type": "array", "items": {"type": "string"}},
        "default_reason": {"type": ["string", "null"]},
        "criteria_order": {"type": "array", "items": {"type": "string", "enum": crit}},
        "why": {"type": "string"}, "refs": {"type": "array", "items": {"type": "string"}},
        "scope": {"type": "object", "additionalProperties": False, "required": ["service_types", "criteria"],
                  "properties": {"service_types": {"type": "integer"}, "criteria": {"type": "integer"}}},
    },
}
d["Recommendation"]["properties"]["ranking"] = {"$ref": "#/$defs/Ranking"}
d["Candidate"]["properties"]["criteria"] = {
    "type": "object", "additionalProperties": False, "required": crit,
    "properties": {
        "certainty": {"type": "object", "additionalProperties": False,
                      "required": ["evidence_unknown", "unknown_cost_components", "unknown_count"],
                      "properties": {"evidence_unknown": {"type": "boolean"},
                                     "unknown_cost_components": {"type": "integer"},
                                     "unknown_count": {"type": "integer"}}},
        "cost": {"type": "object", "additionalProperties": False,
                 "required": ["monthly_usd", "tied_with_cheapest"],
                 "properties": {"monthly_usd": {"type": ["number", "null"]},
                                "tied_with_cheapest": {"type": "boolean"}}},
        **{k: {"type": "integer", "minimum": 0} for k in crit[2:]},
    },
}
d["Candidate"]["properties"]["decided_by"] = {
    "type": ["object", "null"], "additionalProperties": False, "required": ["criterion", "over"],
    "properties": {"criterion": {"type": "string", "enum": crit + ["name"]},
                   "over": {"type": "string", "pattern": "^C[0-9]+$"}},
}
p.write_text(json.dumps(s, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
EOF
git diff --stat schemas/infrafit.schema.json
```

Expected: 추가된 줄만 있는 diff(수백 줄 재포맷이 생기면 `git checkout schemas/infrafit.schema.json` 후 손으로 넣는다).

- [ ] **Step 9: 새 테스트 통과 확인**

Run: `.venv/bin/python -m pytest tests/test_ranking.py -q`
Expected: 14 passed

- [ ] **Step 10: 전체 테스트와 기존 테스트 기대값 점검**

Run: `.venv/bin/python -m pytest -q`

기존 테스트(`tests/test_fit_recommend.py`, `tests/test_topologies.py`)가 순위 순서 때문에 실패할 수 있다. 실패마다:
1. 테스트 프로필로 유형이 무엇이 되는지, 그 유형 `order` 로 계산하면 새 순서가 맞는지 손으로 확인한다.
2. 의도된 변화면 기대값을 고치고 그 줄에 이유 주석(예: `# 실시간 유형: 상시 응답 → 확장 → 비용`)을 단다.
3. 의도와 다르면(예: 탈락·비용·outcome 이 바뀜) 코드를 고친다. 탈락·비용·outcome 은 이 작업에서 바뀌면 안 된다.
4. `ops_burden` 순위에 기대던 테스트는 이제 `config_burden` 또는 이름으로 갈린다 — 기대값을 고치고 주석을 단다.

Expected 최종: 전부 통과 (485 + 2 + 14 = 501, 고친 테스트는 수가 같다)

- [ ] **Step 11: 커밋**

```bash
git add infrafit/fit/recommend.py infrafit/stages/s4_recommend.py schemas/infrafit.schema.json tests/
git commit -m "Rank S4 candidates by service-type criteria order; output ranking, criteria and decided_by

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: 문서 갱신 + 픽스처 QA

**Files:**
- Modify: `infrafit/fit/recommend.py` (모듈 docstring 의 `순위:` 문단, `services:` 줄의 괄호 설명)
- Modify: `README.md` (S4 설명 근처에 한 절)
- Create: `scripts/qa_ranking.py`
- Create: `docs/superpowers/notes/2026-10-03-service-type-ranking-qa.md`

**Interfaces:**
- Consumes: `infrafit.pipeline.analyze(source: str, out_root: Path, until="S4", run_id=str)` — `source` 는 문자열 경로, `out_root` 는 `Path`

- [ ] **Step 1: `recommend.py` docstring 수정**

`services:` 줄의 괄호 `(근거 있는 모름 없음 → 비용을 앎 → 낮은 비용 → 모르는 셀 → 운영 부담 → 설정 수 → 과금 방식 → ID)` 를 `(서비스 유형의 기준 순서 → 과금 방식 → ID, knowledge/ranking.yaml)` 로 바꾸고, `순위:` 문단 전체를 다음으로 바꾼다:

```
순위(knowledge/ranking.yaml, 설계 2026-10-03-infrafit-service-type-ranking-design.md): 실현 불가 제외 → 앱 워크로드의 근거 있는
차원으로 서비스 유형 하나를 정하고(실시간 > 장시간 처리 > 상태 저장 > 백그라운드 > 가벼운 웹, 해당 없으면 가벼운 웹) 그 유형의
기준 순서로 사전식 정렬 → 조합 이름. 기준: certainty(근거 있는 모름·모르는 비용) / cost(최저 합 × 1.15 이내 동률, 합이 null이면
뒤) / always_on / request_headroom(필요 등급보다 한 단계 위 상한) / scaling / data_safety / config_burden. 능력 값을 모르면 나쁜 쪽.
운영 부담은 출처 있는 값이 없어 순위에 쓰지 않는다. 출력: ranking(유형·coverage·근거·기준 순서), 후보마다 criteria·decided_by.
```

- [ ] **Step 2: README 에 절 추가** — `README.md` 에서 S4 를 설명하는 곳(없으면 107행 근처 "다음 구현 대상" 앞)에 추가

```markdown
### S4 순위: 서비스 유형별 기준 순서

다루는 경우의 수를 선언한다: 서비스 유형 5개 × 비교 기준 7개(`knowledge/ranking.yaml` `scope`). 순위는 가중합 없이 사전식이고, 유형마다 기준을 보는 순서만 다르다.

| 유형 (판정 우선순위) | 판정 근거 (detector 차원만) | 기준 순서 |
|---|---|---|
| 실시간 | A3 웹소켓, A1 실시간 연결 | 확실성 → 상시 응답 → 확장 → 비용 → 설정 부담 |
| 장시간 처리 | A2 수십 초 이상, E2 llm-api | 확실성 → 처리 시간 여유 → 비용 → 상시 응답 → 설정 부담 |
| 상태 저장 | B1·B2 있음, 데이터 저장소 | 확실성 → 데이터 안전 → 비용 → 설정 부담 |
| 백그라운드 | A1 워커·정기 작업, B3, A4 | 확실성 → 상시 응답 → 비용 → 설정 부담 |
| 가벼운 웹 | 위에 해당 없음 | 확실성 → 비용 → 설정 부담 → 상시 응답 |

- 여러 유형에 걸리면 위 유형 하나를 쓰고 `coverage: partial` + `unprioritized` 로, 해당 없으면 `coverage: default` 로 표시한다.
- 후보마다 7개 기준 값(`criteria`)과 바로 다음 후보를 이긴 기준(`decided_by`)을 낸다.
- 확장: 유형 = `service_types` 한 항목, 기준 = 출처 있는 능력 키 + `criteria` 한 줄 + `infrafit/fit/ranking.py` 계산. `kb_lint` 가 검사한다.
- 운영 부담은 출처 있는 값이 없어 기준에서 뺐다.
```

- [ ] **Step 3: QA 스크립트 `scripts/qa_ranking.py`**

```python
"""픽스처마다 S4 순위 요약 표(QA). 사용: python scripts/qa_ranking.py [--root <infrafit 저장소>]

--root 를 주면 그 저장소의 infrafit 으로 돌린다(예: main 워크트리와 비교). 픽스처는 이 저장소의 fixtures/.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
RUNNER = """
import sys
from pathlib import Path
from infrafit import pipeline
pipeline.analyze(sys.argv[1], Path(sys.argv[2]), until="S4", run_id="qa")
"""


def run(root: Path, fixture: Path) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, "-c", RUNNER, str(fixture / "repo"), tmp], check=True, cwd=root,
                       env={"PYTHONPATH": str(root), "PATH": "/usr/bin:/bin"}, capture_output=True)
        return json.loads((Path(tmp) / "qa" / "recommendation.json").read_text(encoding="utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=HERE)
    args = ap.parse_args()
    print("| 픽스처 | 유형 | coverage | 근거 | 1~3위 (월 USD, decided_by) |")
    print("|---|---|---|---|---|")
    for fx in sorted((HERE / "fixtures").glob("f*")):
        rec = run(args.root.resolve(), fx)
        rk = rec.get("ranking") or {}
        by = "; ".join(f"{m['type']}:" + ",".join(f"{b['dimension']}@{'/'.join(b['at'][:1])}" for b in m["by"][:2])
                       for m in rk.get("matched", []))
        tops = []
        for c in rec["candidates"][:3]:
            comp = ",".join(sorted({p["component"].split("/")[1] for p in c.get("placement", [])}))
            cost = c["cost"]["monthly_baseline_usd"]
            why = (c.get("decided_by") or {}).get("criterion", "-")
            tops.append(f"{c['id']} {c.get('topology')}:{comp} ({cost}, {why})")
        print(f"| {fx.name} | {rk.get('service_type', '-')} | {rk.get('coverage', '-')} | {by or '-'} | "
              f"{'<br>'.join(tops) or rec['outcome']} |")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 새 순위로 QA 표 만들기**

Run: `.venv/bin/python scripts/qa_ranking.py > /tmp/qa-new.md && cat /tmp/qa-new.md`
Expected: f1~f6 각 줄에 유형·coverage·1~3위. 예외가 나면 그 픽스처를 `pipeline.analyze` 로 직접 돌려 원인을 고친다.

- [ ] **Step 5: main 의 기존 순위와 비교**

```bash
git worktree add /tmp/infrafit-main main
.venv/bin/python scripts/qa_ranking.py --root /tmp/infrafit-main > /tmp/qa-old.md
cat /tmp/qa-old.md
git worktree remove /tmp/infrafit-main
```

Expected: 유형·coverage 열은 `-`, 1~3위는 기존 순위.

- [ ] **Step 6: QA 노트 쓰기** — `docs/superpowers/notes/2026-10-03-service-type-ranking-qa.md`

내용: (1) 새 표(`/tmp/qa-new.md`)와 기존 표(`/tmp/qa-old.md`)를 그대로 붙인다. (2) 1위가 바뀐 픽스처마다 한 줄: 기존 1위 → 새 1위, 갈린 기준(`decided_by`), 그 유형의 `why` 와 맞는지 "맞음/의심" 판정. (3) coverage 가 partial·default 인 픽스처와 빠진 특성. (4) 의심 항목은 원인 가설과 함께 "사람 확인 필요"로 남긴다(코드 수정은 사용자 확인 후).

- [ ] **Step 7: 전체 테스트 + lint**

Run: `.venv/bin/python -m pytest -q && .venv/bin/python -c "from infrafit.kb_lint import lint; print(lint())"`
Expected: 모두 통과, `[]`

- [ ] **Step 8: 커밋**

```bash
git add infrafit/fit/recommend.py README.md scripts/qa_ranking.py docs/superpowers/notes/2026-10-03-service-type-ranking-qa.md
git commit -m "Document service-type ranking and add fixture QA table comparing with main

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

## agentcore 반영 (이 계획 범위 밖, QA 승인 후 별도 계획)

- `scripts/sync_infrafit.py` 로 vendor 갱신
- `agent/inventory.py` 요약 `recommendation` 에 `ranking`(service_type, coverage, unprioritized, criteria_order, why) + 후보 `decided_by`
- 경고 한 줄: `InfraFit: <유형> 유형으로 판단 — <기준 순서> 순으로 비교 (coverage)`
- 프롬프트: 유형과 기준 순서를 candidates 의 why 에 반영
