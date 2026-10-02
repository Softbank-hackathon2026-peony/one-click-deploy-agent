# infrafit 계획 2 (MVP): S2 프로필 → S3 적합성 → S4 추천 Implementation Plan

> **For agentic workers:** 시간 예산이 짧다. 작업 1·2는 병렬(워크트리), 작업 3은 둘의 형식(아래 고정)을 전제로 같이 시작해도 된다. 리뷰는 마지막에 한 번.

**Goal:** S1 인벤토리에서 앱의 요구(차원)를 뽑고, 출처 있는 능력 값과 명시 규칙으로 모든 후보를 비교해 **배포 구성(컴퓨트 + 데이터 저장소)을 추천**한다. LLM 없음, 결정적.

**MVP 범위**
- 컴퓨트 후보 6개(연구 문서 `capabilities/05-compute-tier1-2.md`): Lambda Function URL(§3.5), Cloud Run 요청 기반(§2.1), Cloud Run 인스턴스 기반(§2.2), ECS Fargate + ALB(§3.1), EC2 + docker compose(§7.1), Compute Engine + docker compose(§7.2). AgentCore 대상 id와의 대응을 함께 적는다(`aws_lambda`, `gcp_cloud_run`, `aws_ecs_fargate`, `aws_ec2`, `gcp_compute_engine`).
- 데이터 후보: Postgres → RDS Postgres single-AZ / Cloud SQL Postgres single, Redis → ElastiCache / Memorystore, SQLite → 그대로(영속 디스크가 있는 컴퓨트에서만) 또는 변형 "SQLite → 관리형 Postgres".
- 차원 MVP: A1, A2, A3, A4, B1, B2, B3, E2, 그리고 가정 D2(평시 동시성 낮음), G3(예산 민감 높음).
- 출처 정책(README §3): 능력 값은 **적격(A) 출처의 인용이 있는 것만** 쓴다. `⚠️근거없음` 줄은 쓰지 않는다. 값을 못 찾으면 `unknown`.

**Spec:** `docs/superpowers/specs/2026-10-01-infrafit-design.md` §7(S2), §8(S3), §9(S4). 출력은 `schemas/infrafit.schema.json`의 `Profile`, `Fit`, `Recommendation`으로 검증한다(필요한 최소 필드만 채우되 스키마는 통과).

## Global Constraints
- 계획 1~1e와 같다(결정성, 검증 후 쓰기, 실제 근거 줄, 지식은 `knowledge/` YAML, 카탈로그 ID만, `kb lint` 0, 기대값 미기록, 테스트는 tmp_path 합성 저장소, 커밋 영어 + `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`).

## 고정 형식 (작업 사이 계약)

`knowledge/capabilities.yaml`
```yaml
components:
  - id: "cp:aws/lambda/function-url"        # 카탈로그 ID (없으면 catalog.yaml에 출처와 함께 추가)
    target: aws_lambda                        # AgentCore 대상 id (데이터 구성 요소는 생략)
    cloud: aws
    family: cp
    ops_burden: low                           # low|medium|high, 근거 문장과 출처 필수
    capabilities:
      CP.max_request_seconds: {value: 900, source: {doc: "capabilities/05-compute-tier1-2.md", line: 123, url: "https://...", quote: "..."}}
      CP.websocket: {value: false, source: {...}}
```
능력 키(MVP): `CP.max_request_seconds`(int), `CP.websocket`(bool), `CP.cpu_after_response`(bool), `CP.cpu_after_response_config`(문자열: 켜는 설정 이름, 없으면 생략), `CP.persistent_local_disk`(bool), `CP.scale_to_zero`(bool), `CP.single_instance_config`(문자열: 인스턴스를 1개로 고정하는 설정), `CP.always_on`(bool), `DS.engine`(postgres|redis|sqlite), `COST.monthly_floor_usd`(number, 서울 리전 기준 최소 구성, 출처 필수; 모르면 키 생략).

`knowledge/rules.yaml`
```yaml
rules:
  - id: R-A3-WEBSOCKET
    when: {dimension: A3, equals: websocket}
    require: {capability: CP.websocket, equals: true}
    otherwise: infeasible                       # infeasible | config
    config_from: null                           # otherwise=config일 때 설정 이름을 가져올 능력 키
    message: "장시간 웹소켓 연결이 필요한데 이 플랫폼은 지원하지 않는다"
```
최소 규칙: A2(수십 초 이상) × max_request_seconds, A3(websocket) × websocket, A4(응답 후 작업) × cpu_after_response(없으면 config_from cpu_after_response_config), B1(프로세스 메모리 상태) × single_instance_config(config), B2(로컬 디스크 상태) × persistent_local_disk(infeasible → 변형 후보), B3(단일 실행) × single_instance_config(config), A1(worker/scheduled 상시) × always_on 또는 cpu_after_response.

`profile.json`의 `dimensions[]`는 스키마 `DimensionValue`(scope는 워크로드 id 또는 `w-*` 집계), `source`는 detector|assumption, 근거는 inventory 근거를 그대로.

---

### Task 1: 지식 — 능력 값·규칙·카탈로그 (워크트리 A)
- 위 6개 컴퓨트와 4개 데이터 구성 요소의 능력 값을 연구 문서에서 **적격 출처 인용이 있는 줄만** 골라 `knowledge/capabilities.yaml`에 옮긴다(`doc`/`line`/`url`/`quote` 필수; 인용 문구는 그 줄에 있는 것). 표시가 `⚠️근거없음`인 줄, `미확인` 값은 쓰지 않는다(키 생략).
- `knowledge/rules.yaml` 최소 규칙. 카탈로그에 없는 ID는 출처와 함께 추가.
- `kb lint`: 형식, 카탈로그 일관성, source 필수, 인용 문구가 `doc:line`에 실제로 있는지(문자열 포함) 검사.
- 테스트: lint 음성 사례들.

### Task 2: S2 프로필 (워크트리 B)
- `infrafit/stages/s2_profile.py` + `infrafit/profile/*.py`: inventory(+스냅숏)에서 MVP 차원을 결정적으로 뽑는다. 탐지 지식(정규식 등)은 `knowledge/profile_detectors.yaml`.
  - A1: 워크로드 종류. A2: 요청 경로 핸들러 파일이 LLM API(외부 서비스 kind llm-api) 또는 긴 작업 시그니처를 쓰면 "수십 초", 아니면 가정 "1초 미만". A3: WEBSOCKET 엔드포인트 → websocket, SSE 응답 패턴 → sse. A4: FastAPI `BackgroundTasks`, `asyncio.create_task`, `threading.Thread`, Spring `@Async`, Node 응답 후 미대기 Promise 패턴. B1: process-memory 캐시 범위, `spring-stomp-simple-broker`, 인메모리 세션·레이트리밋. B2: sqlite·container-disk 범위. B3: in-process scheduler 시그니처, Spring `@Scheduled`. E2: 외부 서비스 kind llm-api/payments/messaging.
  - 가정: D2=낮음, G3=높음(`assumptions[]`에 이유).
- 스키마 `Profile`로 검증, 파이프라인 `--until S2`.

### Task 3: S3 적합성 + S4 추천 (작업 1·2 형식 전제)
- S3: 범위(앱 워크로드 집계 `w-*` 하나 + 데이터 범위들) × 같은 family의 모든 후보에 규칙 적용 → `FitCell`(feasible / feasible_with_config / infeasible / unknown, 위반·설정·모르는 키, 위반마다 규칙 id와 능력 출처). 현재 구성 요소는 `is_current`.
- S4: 조합 = 컴퓨트 1 × (데이터 범위마다 같은 클라우드의 관리형 대응, SQLite는 영속 디스크 컴퓨트면 유지·아니면 "SQLite→관리형 Postgres" 변형). 순위: 실현 가능 → 월 최소 비용(합산, 모르면 unknown_count) → 운영 부담 → 설정 요구 수. `recommended`, `candidates`(순위·비용·근거), `rejected`(위반 이유·출처). AgentCore 대상 id를 함께 낸다(후보 assignment의 컴퓨트 → target).
- 파이프라인 `--until S4`, `check-run`이 S2~S4 스키마 검증.
- 실제 저장소 12개와 픽스처 6개로 실행해 예외 없음 확인.

### Task 4: AgentCore 연결 (컨트롤러)
- vendor 다시 복사, `inventory.py`가 S4까지 돌려 요약에 `recommendation`(1~5순위, 위반 이유와 출처, 비용)을 넣는다. 프롬프트: "InfraFit 추천은 규칙·출처 기반 판정이다. target 은 InfraFit 1순위를 따르고, 다르게 고르면 warnings 에 이유를 써라." 비밀값은 inventory와 `env_names`를 함께 보라, candidate 사실은 단정하지 말라.
