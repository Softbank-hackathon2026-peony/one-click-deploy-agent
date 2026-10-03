# S4 서비스 유형별 순위 설계 (v1)

작성 2026-10-03. 대상: InfraFit S4(`infrafit/fit/recommend.py`), 새 지식 파일 `knowledge/ranking.yaml`.
QA 후 agentcore 에 vendor 동기화로 반영한다(이 문서 §8).

## 왜

지금 S4 순위는 모든 앱에 같은 사전식 키를 쓴다: 근거 있는 모름 → 비용을 아는가 → 비용 → 모름 수 → 운영 부담 → 설정 수 → 이름.
그래서 실시간 채팅 앱과 하루 몇 번 쓰는 데모 API 가 같은 잣대(사실상 "싼 것")로 줄 선다. 운영 부담은 출처 있는 값이 없어(capabilities.yaml:24) 모두 `high` 로 같아 순위에 영향이 없다.

이 설계는 **서비스 특성(유형)마다 비교 기준의 우선순위를 다르게** 둔다. 설계 문서 §9.7 원칙(설명할 수 있어야 하므로 가중합을 쓰지 않는다)은 그대로 지킨다: 사전식 순서이고, 순서만 유형마다 다르다.

## 범위 선언 (다루는 경우의 수)

모든 서비스를 다루지 않는다. 이 버전이 다루는 경우는 아래가 전부이고, 출력(`ranking.scope`)과 README 에 그대로 밝힌다.

- 서비스 유형 5개: 실시간 / 장시간 처리 / 상태 저장 / 백그라운드 / 가벼운 웹
- 비교 기준 7개: 확실성 / 비용 / 상시 응답 / 처리 시간 여유 / 확장 / 데이터 안전 / 설정 부담
- 플랫폼: capabilities.yaml 의 컴퓨트 구성 요소(현재 8개)

범위 밖(여러 유형이 동시에 걸림, 어느 유형에도 근거 없음)은 답을 내되 `coverage` 로 표시한다(§3). 확장은 데이터(ranking.yaml, capabilities.yaml) 추가로 한다(§7).

바뀌지 않는 것: S1~S3, 탈락 규칙(rules.yaml), 조합 만들기, 비용 계산, outcome 판정.

## 1. `knowledge/ranking.yaml`

```yaml
scope: {service_types: 5, criteria: 7}
cost_tie_ratio: 0.15            # 설계 §9.7 값

criteria:
  - id: certainty
    label: 확실성
    better: lower
  - id: cost
    label: 비용
    better: lower
  - id: always_on
    label: 상시 응답
    capability: CP.always_on
    better: lower
  - id: request_headroom
    label: 처리 시간 여유
    capability: CP.max_request_seconds
    better: lower
  - id: scaling
    label: 확장
    capability: CP.horizontal_scaling
    better: lower
  - id: data_safety
    label: 데이터 안전
    capability: DS.colocated_vm
    better: lower
  - id: config_burden
    label: 설정 부담
    better: lower

service_types:                  # 위에서부터 검사, 처음 맞는 하나를 쓴다
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

`refs` 는 docs/research/considerations 의 항목 ID 다(근거 문서). `why` 는 출력에 그대로 나간다.

`when` 연산자: `equals`, `in`(목록 값 A1 은 원소 하나라도), `kinds`(B1·B2·E2 같은 `{value, kinds}` 값의 kinds 와 교집합), `datastores: true`(인벤토리 데이터 저장소가 하나 이상, BaaS 포함), `any`, `default`(마지막 유형만).

## 2. 유형 판정

- 입력: profile.json 의 앱 집계 범위(`w-app`, 겹치면 `w-app.all`) 차원 행과 inventory 데이터 저장소.
- **`source: assumption` 인 차원 행은 판정에 쓰지 않는다.** (예: A2 기본값 "1초 미만", D2 가정) 근거 있는 값(`detector`)만 유형을 정한다.
- 모든 유형의 `when` 을 평가해 맞는 유형 목록(`matched`)을 만들고, 그중 가장 위의 유형을 `service_type` 으로 쓴다. 맞는 것이 없으면 `light_web`.
- 결정적이다(LLM 없음). 같은 커밋 + 같은 지식 베이스면 같은 결과.

## 3. 범위 경계 표시 (`coverage`)

| coverage | 조건 | 출력 |
|---|---|---|
| `full` | 맞는 유형이 정확히 하나 | |
| `partial` | 맞는 유형이 2개 이상 | `unprioritized` = 쓰지 않은 유형들(근거와 함께). "이번 순위에서 우선 고려하지 않은 특성" |
| `default` | 맞는 유형이 없어 `light_web` | `default_reason`: "근거 있는 차원 값이 어느 유형 조건에도 맞지 않음" |

탈락 규칙은 유형과 무관하게 모든 차원에 적용되므로, `partial` 이어도 쓰지 않은 유형의 요구(예: 상태 저장 앱의 로컬 디스크)는 이미 S3 규칙으로 걸러진 상태다. `coverage` 는 "줄 세우는 순서"에서 빠진 특성만 말한다.

## 4. 기준 값 계산 (조합 하나당)

조합 안 구성 요소가 여럿이면 "문제가 되는 곳의 수"를 센다. 능력 값을 모르면 나쁜 쪽으로 친다(모르는 플랫폼이 유리해지지 않게).

| 기준 | 값 (작을수록 좋음) |
|---|---|
| certainty | 튜플 (근거 있는 모름 셀 > 0, 모르는 비용 구성 요소 수, 모름 셀 수 + 모르는 비용 수). 지금 키의 해당 부분 그대로 |
| cost | 튜플 (합이 null, 비용 값). 비용 값 = 합을 아는 실현 가능 후보 중 최저 합 × (1 + cost_tie_ratio) 이하면 0, 아니면 합. 합이 null 인 후보끼리는 지금처럼 (모르는 비용 수, 아는 부분합) |
| always_on | `CP.always_on` 이 true 가 아닌 구성 요소에 놓인 앱 워크로드 수 |
| request_headroom | A2 가 근거 있는 워크로드 중, 놓인 구성 요소의 요청 상한이 **필요 등급보다 한 단계 위 기준** 미만인 수. 기준: 수십 초 → 600초, 수 분 → 상한 없음(`CP.platform_request_timeout: false` 또는 `CP.max_request_seconds` 없음), 그 이상 → 상한 없음, 1초 미만 → 60초. 상한 없음 플랫폼은 항상 통과 |
| scaling | `CP.horizontal_scaling` 이 true 가 아닌 구성 요소에 놓인 web·realtime 워크로드 수 |
| data_safety | VM 안 컨테이너 저장소(`DS.colocated_vm: true`) 또는 로컬 SQLite 에 놓인 데이터 범위 수. 관리형·BaaS 는 0 |
| config_burden | (feasible_with_config 셀 수 + 서로 다른 구성 요소 수) |

"한 단계 여유"로 정한 이유: 상한을 단순히 클수록 좋게 두면 장시간 앱에서 항상 상한 없는 VM 이 이긴다(예: f6 에서 Cloud Run 3600초로 충분해도). 규칙(S3)이 이미 "필요 등급 충족"을 보장하므로, 순위는 "여유가 있는가"만 본다.

## 5. 순위

- 정렬 키 = 유형 `order` 의 기준 값을 이어 붙이고 마지막에 조합 이름(`recommend.py:458` 교체).
- `order` 에 없는 기준은 순위에 쓰지 않는다(값은 출력에 남긴다).
- services 조합의 워크로드별 플랫폼 고르기(`recommend.py:317`)도 같은 `order` 를 워크로드 단위로 적용한다(cost 는 그 워크로드 비용, 동률 기준은 후보 플랫폼 중 최저 × 1.15). 조합 순위와 배치 기준이 같아야 설명이 맞는다.
- `ops_burden` 출력 필드는 그대로 두되 순위에서는 뺀다(출처 없음).

## 6. 출력 (`recommendation.json`, 스키마 갱신)

최상위 `ranking`:

```json
{
  "service_type": "realtime",
  "label": "실시간",
  "coverage": "partial",
  "matched": [
    {"type": "realtime", "by": [{"dimension": "A3", "value": "장시간 양방향(웹소켓)", "at": ["server.js:12"]}]},
    {"type": "stateful", "by": [{"dimension": "B2", "value": "있음", "at": ["db.js:3"]}]}
  ],
  "unprioritized": ["stateful"],
  "default_reason": null,
  "criteria_order": ["certainty", "always_on", "scaling", "cost", "config_burden"],
  "why": "연결이 끊기지 않아야 하는 서비스라 ...",
  "refs": ["T-006", "W-001", "T-016"],
  "scope": {"service_types": 5, "criteria": 7}
}
```

후보마다:
- `criteria`: 7개 기준 값 전부(`order` 에 없어도). 값은 사람이 읽을 수 있는 형태(`{"always_on": 0, "cost": {"monthly_usd": 12.21, "tied_with_cheapest": true}, ...}`).
- `decided_by`: 바로 다음 순위 후보와 처음 갈린 기준. `{"criterion": "scaling", "over": "C2"}`. 마지막 후보와 이름으로만 갈린 경우는 `{"criterion": "name", ...}`.

outcome 이 recommended 가 아니면(no_feasible, static_only, not_deployable) `ranking` 은 유형 판정까지만 채우고 후보 필드는 없다.

## 7. 확장과 검사

- 유형 추가 = `service_types` 한 항목. 기준 추가 = capabilities.yaml 에 출처 있는 능력 키 + `criteria` 한 줄 + recommend.py 의 기준 계산 함수 하나(기준 id → 함수 표).
- `kb_lint` 추가 검사: `order` 의 기준이 `criteria` 에 있음, `order` 첫 번째는 `certainty`, `when` 의 차원 ID·값이 profile_detectors.yaml 어휘에 있음, `default` 는 마지막 유형 하나만, `refs` 가 considerations 문서에 존재, `scope` 숫자가 실제 개수와 같음.
- 기준 계산 함수가 없는 기준 id 는 시작 시 오류(조용히 무시하지 않음).

## 8. 테스트·QA·agentcore 반영

단위 테스트(tests/test_ranking.py):
- 유형 판정 5가지 각각, 우선순위 충돌(realtime + stateful → realtime, coverage partial), 근거 없음 → light_web/default
- assumption 차원은 판정에 안 씀(A2 가정 "1초 미만"이 long_request 를 막지도 만들지도 않음)
- 같은 후보 집합에서 유형에 따라 1위가 바뀜(실시간: 상시 응답, 가벼운 웹: 비용)
- 비용 동률 15%(최저 대비) 경계값, null 비용 후보 뒤로
- request_headroom 한 단계 여유: 수십 초가 필요할 때 상한 600초 이상·상한 없음은 0, 60~599초는 1 (60초 미만은 S3 에서 이미 탈락)
- decided_by 계산, kb_lint 오류 검출

QA: fixtures f1~f6 를 S4 까지 돌려 유형·coverage·1위·decided_by 를 표로 만들고 지금 순위와 비교한다. 1위가 바뀐 픽스처마다 이유가 `why` 와 맞는지 사람이 확인한다.

agentcore 반영(QA 후 별도 작업):
- `scripts/sync_infrafit.py` 로 vendor 갱신
- `agent/inventory.py` 요약의 `recommendation` 에 `ranking`(service_type, coverage, unprioritized, criteria_order, why) 추가, 후보에 `decided_by`
- 경고 한 줄: `InfraFit: <유형> 유형으로 판단 — <기준 순서> 순으로 비교 (coverage)`
- 프롬프트: 유형과 기준 순서를 candidates 의 why 에 반영하라고 지시
