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

compose·k8s 가 없을 때(`_from_code`) 인벤토리 데이터 저장소 중 **접속 정보 없이 띄울 수 있는 것**을 `deploy_units.datastores` 로 만든다.

- `images.yaml` 에 선택 필드 `image`(공식 레지스트리 이미지, 태그 필수)를 **비밀번호 없이 뜨는 저장소에만** 둔다: redis(`redis:7-alpine`) 만 둔다(memcached 는 카탈로그 컴포넌트가 없어 해석되지 않으므로 `image` 도 두지 않는다). postgres·mysql·mongo 공식 이미지는 비밀번호 환경변수 없이는 뜨지 않으므로 `image` 를 두지 않는다(코드 경로에서 컨테이너를 만들지 않고 `unresolved` 에 `datastores.<범위>: 접속 정보(비밀번호)가 필요한 저장소라 컨테이너를 만들지 않는다` 를 남긴다).
- `kb_lint._lint_images`: `image` 는 `^[a-z0-9][a-z0-9._/-]*:[A-Za-z0-9._-]+$`(태그 필수, 레지스트리 호스트 없음), `role` 이 datastore·cache·queue 일 때만 허용. `IMAGE_KEYS` 에 `image` 추가.
- 대상: `inventory.datastores` 중 `status: confirmed` 이고, 그 범위의 현재 구성 요소(`current_components` 의 component)가 `image` 가 있는 `images.yaml` 항목의 `component` 와 같은 것(예: `ca:unspecified/redis/default`). 라이브러리(`qu:lib/...`), BaaS·클라우드 관리형, SQLite 는 대상이 아니다.
- 단위 모양은 compose 경로의 저장소 항목과 같다: `{id, datastore: <범위 id>, image, ports: [images.yaml port], env: {}, env_names: [], evidence: <저장소 범위 첫 근거>}`. `id` 는 그 `images.yaml` 항목의 첫 match 이름(`redis`)이고, 컨테이너 id 와 겹치면 `<이름>-store`, `<이름>-store2`, … 로 유일해질 때까지.
- 앱 컨테이너 중 `workload` 가 그 범위 `used_by` 에 있는 것의 `depends_on` 에 저장소 id 를 넣는다.
- **접속 주소 환경변수**: 그 앱 워크로드 코드(`code_root` 아래, 테스트·보조 경로 제외)에서 기본값이 그 저장소 주소인 환경변수 읽기를 찾는다 — Python `os.environ.get("X", "redis://…")`·`os.getenv("X", "redis://…")`, JS/TS `process.env.X || "redis://…"`·`process.env.X ?? "redis://…"` (주소 스킴은 images.yaml 항목의 새 선택 필드 `url_scheme: ["redis", "rediss"]` 로 정한다). 기본값 URL 의 호스트가 루프백(`LOOPBACK_HOSTS`: localhost·127.x·::1)일 때만 그 컨테이너의 `env[X] = "redis://<저장소 id>:<port><기본값의 경로>"`(스킴은 `rediss` 로 읽혀도 항상 평문 `redis://`, 경로 `/1` 등은 그대로 두고 경로가 없으면 붙이지 않는다; `url_template` 필드로: redis `"redis://{host}:{port}{path}"`, 자리표시자는 scheme·host·port·path), `env_names` 에 `X`. 외부 호스트 기본값(`redis://cache.example.com:6380/2`)은 덮어쓰지 않는다. 단위에는 `env` 값만 두고 근거 줄은 출력하지 않는다(DeployUnits 스키마 그대로). 하나도 넣지 못한 사용자 컨테이너(환경변수 기본값 없음·외부 호스트)는 `unresolved` 에 `containers.<id>.env` 항목으로 남긴다(지어내지 않음).
- `detect_deploy_units` 시그니처: `datastores` 외에 `current_components` 를 받는다(`run_s1` 이 `components` 를 넘김).
- 테스트: 합성 Flask+Celery+Redis(Procfile web/worker/beat, `REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")`) → `deploy_units.datastores == [{id: "redis", datastore: "svc-redis", image: "redis:7-alpine", ports: [6379], ...}]`, web·worker·beat 의 `depends_on` 에 `redis`, `env["REDIS_URL"] == "redis://redis:6379/0"`, `env_names` 에 `REDIS_URL`; `rediss://localhost:6379/1` → `redis://redis:6379/1`, 외부 호스트·기본값 없음 → env 없음 + unresolved. postgres 를 코드에서만 쓰는 앱 → datastores 비어 있고 unresolved 에 비밀번호 항목. SQLite·BaaS 는 만들지 않음. images.yaml lint 테스트(태그 없는 image, role 불일치, url_template 형식).

## 3. A2 시그니처: 요청 경로의 긴 동기 대기

- `profile_detectors.yaml` `code` 에 추가:
  - `PD-A2-SLEEP-PY`: A2 "수십 초", scope request-path, glob `**/*.py`, regex `\b(?:time\.sleep|asyncio\.sleep|await\s+asyncio\.sleep)\(\s*(?:[1-9]\d|[1-9]\d{2,})(?:\.\d+)?\s*\)` (10초 이상 상수)
  - `PD-A2-SLEEP-JS`: A2 "수십 초", glob js/ts, regex `\b(?:setTimeout|sleep|delay)\(\s*(?:[^,()]*,\s*)?(?:[1-9]\d{4,})\s*\)` (10,000ms 이상 상수) — `setTimeout(fn, 30000)` 형태와 `sleep(30000)`.
  - 두 시그니처 모두 `unless` 는 두지 않는다(테스트 경로는 탐지기가 이미 제외).
- 상수가 아닌 인자(변수)는 잡지 않는다. 60초 이상 상수도 같은 값 "수십 초" 로 낸다(등급 상한은 규칙이 다룬다; 더 긴 값은 근거 부족).
- 테스트: `time.sleep(40)` 핸들러 → `w-web` A2 "수십 초"(detector, file:line); `time.sleep(2)` 는 잡지 않음; `setTimeout(resolve, 30000)` 잡음.

## 4. S4: 근거 있는 차원에서 확인 못 한 후보는 추천하지 않는다

사용자 결정: "모르는 것은 모른다고 표시". 값을 지어내지 않는다. agentcore(PR #6)가 `candidates` 와 `criteria.certainty.evidence_unknown` 을 쓰므로 후보 목록 모양은 바꾸지 않는다(하위 호환).

- 근거 있는 차원(source=detector)에서 unknown 셀이 난 후보에 `unknown: [{scope, component, rule, dimension, dimension_value, capability, at: [file:line…]}]` 를 붙인다(셀마다, 중복 제거). `engine.Cell` 에 출력하지 않는 `evidence_unknowns` 목록을 두고 `evaluate` 가 unknown 판정 때 채운다. `Recommender` 가 `_add` 에서 조합에 모은다.
- `recommended` = `candidates` 중 `unknown` 이 없는 첫 후보. 모든 후보가 그렇다면 `recommended: null`, `outcome: "unverified"`, `outcome_detail: {message: "조건을 만족하는지 확인하지 못한 후보만 남았다", unknown_capabilities: [중복 없는 capability 키]}`. outcome enum 에 `unverified` 추가.
- 순위·`decided_by` 는 지금 그대로(확실성 첫 요소가 이미 이런 후보를 뒤로 보낸다).
- `check_s4`: `recommended` 가 있으면 그 후보에 `unknown` 이 없어야 함; outcome `unverified` 면 recommended 가 null 이고 모든 후보에 `unknown` 이 있어야 함.
- 스키마: `Candidate.unknown`(선택, 항목 정의), outcome enum.
- 테스트: 웹소켓 앱 + Lambda(CP.websocket 없음)·EC2(websocket true) → Lambda 후보에 `unknown[0] == {capability: "CP.websocket", dimension: "A3", rule: "CAP-WEBSOCKET-001", at: [server.js 줄] …}`, recommended 는 EC2; 모든 후보가 unknown 이면 outcome `unverified`, recommended null.
- 모듈 docstring·README S4 절에 한 문단 추가.

## 바뀌지 않는 것

탈락 규칙, 비용 계산, 서비스 유형별 순위, 능력 표의 플랫폼 공식 값(Lambda 900초 등 — Worker 제한 30/60초는 agentcore 가 덮어쓴다).

## 검증

- `pytest` 전체, `kb_lint.lint() == []`, 픽스처 골든(f1~f6) 재생성 후 바뀐 곳 확인(§1·§2 는 S1 출력이라 골든이 바뀔 수 있다 — 바뀐 내용이 beat·저장소 컨테이너뿐인지 확인).
- 합성 c2·웹소켓 저장소를 `fixtures/` 에 `f7-celery-redis`, `f8-socketio-chat` 으로 추가하고 골든을 만든다(실제 QA 소스는 자격 증명이 생기면 비교).
