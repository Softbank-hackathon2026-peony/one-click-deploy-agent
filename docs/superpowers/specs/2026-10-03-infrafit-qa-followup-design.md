# InfraFit QA 후속 설계 (v1)

작성 2026-10-03. agentcore QA(런타임 bf66308~c4d7ad6, 재현 소스 `s3://pawploy-agent-135808950984/projects/prj-qa-*/source/`)에서
나온 InfraFit 쪽 원인 네 가지를 고친다. agentcore 쪽 반영(경고 문구, nginx 설정 마운트, Worker 시간 제한 덮어쓰기, vendor 재동기화)은
agentcore 저장소의 별도 설계 문서가 다룬다. 이 변경은 main 에 바로 넣는다(사용자 결정).

합성 재현(`/tmp/c2app`: Flask + Celery + Redis, Procfile web/worker/beat, `time.sleep(40)` 엔드포인트)으로 확인한 현재 동작:
- workloads = web, worker (beat 없음) → `PROC_KINDS` 에 `beat` 가 없어 Procfile 항목이 버려진다(workloads.py:29, 254).
- inventory.datastores = svc-redis(`ca:unspecified/redis/default`, confirmed) 가 있는데 `deploy_units.datastores: []` (deploy_units.py `_from_code` 가 빈 목록 고정).
- A2 = "1초 미만"(assumption): 요청 경로의 긴 동기 대기(`time.sleep(40)`)를 보는 시그니처가 없다.
- 웹소켓 앱(socket.io): Lambda 는 `CP.websocket` 값이 없어 규칙이 unknown → `candidates` 에 남는다. 현재 순위(evidence_unknown 이 certainty 첫 요소)로는 1순위가 되지 않지만, 모든 후보가 unknown 이면 1순위가 될 수 있고 agentcore 화면에는 후보로 그대로 보인다.

## 1. Procfile `beat`·`scheduler` → scheduled 워크로드

- `PROC_KINDS` 에 `beat: scheduled`, `scheduler: scheduled`, `cron: scheduled` 추가(workloads.py:29). `clock` 은 그대로.
- 프로세스 유형이 표에 없어도 명령이 `celery ... beat` 이면 scheduled 로 본다(명령 토큰에 `beat` 가 있고 `celery` 가 앞에 있을 때). 그 밖의 미지 유형은 지금처럼 버린다.
- scheduled 워크로드는 기존 S2 규칙대로 A1 "정기 작업" 을 낸다(상시 실행 요구 → CAP-ALWAYSON-001). deploy_units 코드 경로에서 컨테이너가 된다(아래 §2 와 같은 `_from_code`; `one_shot` 아님).
- 테스트: Procfile `beat:` 가 있는 저장소 → workloads 에 `w-scheduled`(kind scheduled) 가 있고 entrypoint 가 Procfile 줄을 가리킨다; deploy_units.containers 에 `beat` 컨테이너가 있다.

## 2. 코드 경로 deploy_units 에 저장소 컨테이너

compose·k8s 가 없을 때(`_from_code`) 인벤토리 데이터 저장소 중 **컨테이너로 띄울 수 있는 것**을 `deploy_units.datastores` 로 만든다.

- 대상: `inventory.datastores` 항목 중 `status: confirmed` 이고, 그 범위의 현재 구성 요소(`current_components`)가 `images.yaml` 항목의 `component` 와 같은 것(예: `ca:unspecified/redis/default`, `ds:unspecified/postgresql/default`). 라이브러리 구성 요소(`qu:lib/celery/default` 등)와 BaaS·클라우드 관리형(`provider` 가 `unspecified` 가 아닌 것)은 만들지 않는다.
- `images.yaml` 에 선택 필드 `image` 를 더한다: 코드 경로가 쓸 공식 레지스트리 이미지(태그 포함). 예: postgres 항목 `image: "postgres:16-alpine"`, mysql `mysql:8`, mongo `mongo:7`, redis `redis:7-alpine`, rabbitmq `rabbitmq:3-management-alpine`. `kb_lint._lint_images`: `image` 는 `^[a-z0-9][a-z0-9._/-]*:[A-Za-z0-9._-]+$`(태그 필수, 레지스트리 호스트 없음) 이어야 하고, `role` 이 datastore·cache·queue 일 때만 허용.
- 단위 모양은 compose 경로의 저장소 항목과 같다: `{id, datastore(범위 id), image, ports: [images.yaml port], env: {}, env_names: [], evidence}`. `id` 는 `images.yaml` 첫 match 이름(`redis`, `postgres`)으로 하되 컨테이너 id 와 겹치면 `-db`/`-cache` 를 붙인다. `evidence` 는 저장소 범위의 첫 근거(코드 file:line).
- 앱 컨테이너의 `depends_on` 에 그 저장소 id 를 넣는다(`used_by` 기준).
- `detect_deploy_units` 시그니처: `datastores` 외에 `current_components` 를 받는다(`run_s1` 에서 `components` 전달).
- 접속 URL 바꾸기(코드의 `redis://localhost:6379/0` → 서비스 이름)는 agentcore 가 지금 compose 경로에서 하는 방식 그대로 한다(InfraFit 범위 밖). `env_names` 에 저장소 URL 환경변수 이름(인벤토리 external/datastore 근거의 환경변수, 있으면)을 남겨 agentcore 가 찾을 수 있게 한다 — 인벤토리에 그 정보가 없으면 비워 둔다.
- 테스트: 합성 c2 → `deploy_units.datastores == [{id: "redis", datastore: "svc-redis", image: "redis:7-alpine", ports: [6379], ...}]`, web·worker·beat 의 `depends_on` 에 `redis`; SQLite 전용 저장소(`ds:local/sqlite/*`)·BaaS(supabase) 는 만들지 않음; images.yaml lint 테스트(태그 없는 image, role 불일치 거부).

## 3. A2 시그니처: 요청 경로의 긴 동기 대기

- `profile_detectors.yaml` `code` 에 추가:
  - `PD-A2-SLEEP-PY`: A2 "수십 초", scope request-path, glob `**/*.py`, regex `\b(?:time\.sleep|asyncio\.sleep|await\s+asyncio\.sleep)\(\s*(?:[1-9]\d|[1-9]\d{2,})(?:\.\d+)?\s*\)` (10초 이상 상수)
  - `PD-A2-SLEEP-JS`: A2 "수십 초", glob js/ts, regex `\b(?:setTimeout|sleep|delay)\(\s*(?:[^,()]*,\s*)?(?:[1-9]\d{4,})\s*\)` (10,000ms 이상 상수) — `setTimeout(fn, 30000)` 형태와 `sleep(30000)`.
  - 두 시그니처 모두 `unless` 는 두지 않는다(테스트 경로는 탐지기가 이미 제외).
- 상수가 아닌 인자(변수)는 잡지 않는다. 60초 이상 상수도 같은 값 "수십 초" 로 낸다(등급 상한은 규칙이 다룬다; 더 긴 값은 근거 부족).
- 테스트: `time.sleep(40)` 핸들러 → `w-web` A2 "수십 초"(detector, file:line); `time.sleep(2)` 는 잡지 않음; `setTimeout(resolve, 30000)` 잡음.

## 4. S4: 근거 있는 차원에서 unknown 인 후보는 추천에서 분리

사용자 결정: "모르는 것은 모른다고 표시". 값을 지어내지 않는다.

- `run()` 에서 실현 가능 후보 중 `combo.evidence_unknown > 0`(근거 있는 차원의 규칙이 unknown 셀을 냄)인 조합은 `candidates` 에 넣지 않고 새 최상위 `unverified` 목록에 넣는다. 항목: `{id: "U1"…, topology, assignment, placement, cost, unknown: [{scope, component, rule, dimension, dimension_value, capability, at: [file:line]}]}`. 순서는 같은 정렬 키.
- `recommended` 는 `candidates` (확인된 후보) 중 1순위. 확인된 후보가 하나도 없고 `unverified` 가 있으면 `recommended: null`, `outcome: "unverified"`, `outcome_detail: {message: "조건을 만족하는지 확인하지 못한 후보만 남았다", unknown_capabilities: [...]}`. outcome enum 에 `unverified` 추가.
- 가정 값에서 나온 unknown 은 지금처럼 `candidates` 에 남는다(순위 뒤쪽, `criteria.certainty.unknown_count`).
- `check_s4`: `unverified` id 가 `U1..Un` 연속, `candidates` 와 겹치지 않음, `recommended` 가 null 이면 candidates 비어 있음.
- 스키마: `Recommendation.unverified`(선택), `Unverified` 정의, outcome enum.
- 테스트: 웹소켓 앱 + Lambda(CP.websocket 없음) → Lambda 조합은 `unverified` 에 있고 `unknown[0].capability == "CP.websocket"`, `dimension == "A3"`, `at` 에 server.js 줄; 확인된 후보가 있으면 `recommended` 는 그중 1순위; 모든 후보가 unknown 이면 outcome `unverified`. 기존 `test_ranking_feasible_then_unknown_then_cost` 류는 기대값을 이 규칙에 맞춘다(순위 로직 자체는 그대로).
- 모듈 docstring·README S4 절에 한 문단 추가.

## 바뀌지 않는 것

탈락 규칙, 비용 계산, 서비스 유형별 순위, 능력 표의 플랫폼 공식 값(Lambda 900초 등 — Worker 제한 30/60초는 agentcore 가 덮어쓴다).

## 검증

- `pytest` 전체, `kb_lint.lint() == []`, 픽스처 골든(f1~f6) 재생성 후 바뀐 곳 확인(§1·§2 는 S1 출력이라 골든이 바뀔 수 있다 — 바뀐 내용이 beat·저장소 컨테이너뿐인지 확인).
- 합성 c2·웹소켓 저장소를 `fixtures/` 에 `f7-celery-redis`, `f8-socketio-chat` 으로 추가하고 골든을 만든다(실제 QA 소스는 자격 증명이 생기면 비교).
