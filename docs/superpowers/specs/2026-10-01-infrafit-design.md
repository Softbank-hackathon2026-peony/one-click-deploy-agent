# infrafit 설계 문서 — 필요한 만큼의 인프라를 판정하는 진단 엔진

- 작성일: 2026-10-01
- 상태: 설계 검토 중
- 저장소: `one-click-deploy-agent` (이전 이름 `one-click-deploy-k8s`. 실행 대상이 k8s만이 아니게 되어 이름을 바꿨다. CLI와 패키지 이름은 `infrafit`)
- 이 문서의 범위: 전체 구조 + **P1 진단 엔진 상세**. P2~P5는 각자 별도 설계 문서를 쓴다.

## 1. 목적

저장소 하나를 받아서 다음을 한다.

1. 이 앱이 **무엇으로 돌아가는지**, 이미 어떤 인프라가 있는지 코드에서 파악한다.
2. 이 앱에 **어느 수준의 안정성이 필요한지** 판단한다. 재난, 트래픽 폭증, 무중단 배포, 정합성 각각에 대해 판단하며, "필요 없음"도 정당한 답이다.
3. 필요 수준과 현재 수준의 **차이**를 찾는다. 부족하면 위험, 넘치면 비용 낭비다.
4. 차이를 메우는 **가장 싼 구성**(티어)과 처방을 근거, 출처, 가격과 함께 제시한다.
5. (P4) 처방이 실제로 맞는지 부하 테스트와 장애 주입으로 증명한다.

### 누구를 위한 도구인가
- 1차 사용자는 Dockerfile, k8s, Terraform을 모르는 **바이브코더**다. 그래서 사용자에게 질문하지 않는다.
- 개발자나 시니어는 같은 리포트에서 가정과 규칙을 펼쳐 보고 고친다. 사용자 유형마다 흐름을 따로 두지 않는다.

### 면접 과제로서의 목적
이 작품은 클라우드 지식을 보여주는 면접 과제다. 그래서 **판단은 LLM이 아니라 직접 작성한 규칙집이 내린다**(§4). 규칙 하나하나가 "조건 → 결정 → 이유 → 트레이드오프 → 공식 출처"를 갖고, 면접에서 그대로 설명 자료가 된다.

## 2. 설계 원칙

1. **판단은 규칙이, LLM은 사실 추출과 설명만 한다.** 같은 사실이 들어오면 같은 판정이 나온다.
2. **근거 없는 결론은 버린다.** 모든 사실과 추론은 `파일:줄` 근거를 갖는다. LLM 추론은 인용한 줄이 실제로 존재하고 주장한 내용을 담고 있는지 기계적으로 검사하고, 통과하지 못하면 버린다.
3. **묻지 않는다. 대신 가정을 드러낸다.** 코드로 알 수 없는 값(예상 접속자 수 등)은 도메인별 기본값으로 가정하고, 리포트 맨 위에 보여준다.
4. **필요한 만큼만 만든다.** 시나리오마다 필요 수준을 먼저 정하고, 그 수준의 규칙만 적용한다. 과잉 구성도 결함으로 지적한다.
5. **비용은 모든 판정을 거르는 필터다.** 필요 수준을 만족하는 구성 중 가장 싼 것을 고른다. 다만 정합성처럼 아끼면 안 되는 곳은 규칙이 명시한다.
6. **이미 있는 인프라를 존중한다.** 필요 수준을 만족하는 기존 구성은 유지한다. 교체 비용(이전 작업)도 판정에 넣는다.

## 3. 전체 구조

```
 저장소(경로 또는 GitHub URL)
   │
   ▼
 ┌──────────────────────── P1 진단 엔진 ────────────────────────┐
 │ ① 탐지      결정적 규칙으로 사실(Fact) 추출 (파일:줄 근거)       │
 │ ② 추론      LLM: 도메인 분류, 모호한 사실 판단 → 근거 검사       │
 │ ③ 필요 수준  규칙: 사실 + 추론 → 시나리오별 필요 수준 + 가정      │
 │ ④ 현재 수준  규칙: 사실 → 시나리오별로 이미 갖춘 통제와 달성 수준  │
 │ ⑤ 차이·처방  규칙: (필요 − 현재) → 처방 목록                     │
 │ ⑥ 티어·비용  규칙 + 가격 API: 처방을 만족하는 티어별 견적 → 선택   │
 │ ⑦ 리포트    LLM: 판정 결과를 쉬운 말로 설명 (판정은 바꾸지 않음)  │
 └──────────────────────────────────────────────────────────────┘
   │ report.json (기계용)          │ report.html (사람용)
   ▼                               ▼
 P2 앱 코드 수정 PR       P3 티어별 실행기       P4 검증 루프       P5 웹 UI
 (세션 외부화 등)        (티어 0/1/2 배포)     (부하·장애·배포)    (URL 입력 → 리포트)
```

| 하위 프로젝트 | 입력 | 출력 |
|---|---|---|
| P1 진단 엔진 | 저장소 | `report.json`, `report.html` |
| P2 앱 코드 수정 | `report.json`의 코드 처방 | 브랜치 + PR (변경마다 근거 규칙 ID) |
| P3 티어별 실행기 | `report.json`의 티어와 인프라 처방 | 티어 0: 플랫폼 설정, 티어 1: Dockerfile + 서비스 정의, 티어 2: Terraform + k8s 매니페스트. 그리고 배포 |
| P4 검증 루프 | 배포된 환경 + 시나리오별 필요 수준 | 시나리오별 통과 여부, "동시 N명까지, 월 $X" |
| P5 웹 UI | GitHub URL | P1~P4를 버튼으로 실행 |

진행 순서: P1 → P2 → P3(티어 2부터, `simple-web-app`으로 시연) → P4 → P3 나머지 티어 → P5.

## 4. 시나리오 × 수준

진단의 중심 개념이다. 시나리오는 넷이고, 비용은 시나리오가 아니라 모든 판정에 걸리는 필터다.

### 4.1 수준 정의

| 시나리오 | L0 불필요 | L1 기본 | L2 강화 | L3 핵심 |
|---|---|---|---|---|
| **재난/장애** (D) | 영속 데이터가 없음 | 데이터를 잃지 않는다: 자동 백업 + 복원 가능 | 존(AZ) 하나가 죽어도 계속 동작: Multi-AZ DB, 앱 Pod 존 분산, 자동 페일오버 | 다른 시스템이 무너질 때 오히려 써야 하는 서비스: 의존성 장애 시 디그레이드 모드, 리전 장애 대비(복구 절차와 리허설) |
| **트래픽 폭증** (T) | 사용자 수가 고정됨 (사내 도구 등) | 완만한 증가를 오토스케일로 흡수 | 예고된 이벤트: 사전 증설 스케줄, 캐시, 커넥션 풀러 | 예고 없는 폭증: 큐 + 백프레셔, 레이트 리밋, 노드 여유 용량, 무거운 작업 격리 |
| **무중단 배포** (U) | 점검 시간 공지가 가능 | 롤링 배포 + readiness probe + 종료 신호 처리 | 마이그레이션 하위 호환(expand/contract), PDB, LB 드레이닝, 자동 롤백 | 카나리 배포 + 지표 기반 자동 중단 |
| **정합성** (C) | 잃어도 되는 데이터만 있음 | 트랜잭션과 유니크 제약으로 기본 무결성 | 재시도해도 중복이 생기지 않음: 멱등성 키, 웹훅 중복 처리, 작업 큐 멱등 소비 | 결제·재고: 동시성 제어(잠금/버전), 아웃박스, DB 동기 복제, 쓰기 직후 읽기는 주 DB에서 |

수준은 누적이다. L2는 L1의 통제를 모두 포함한다.

### 4.2 필요 수준을 정하는 규칙 (요약)

필요 수준은 사실과 추론에서 규칙으로 정한다. 여러 규칙이 걸리면 가장 높은 수준을 쓴다. 전체 규칙은 `rules/levels/*.yaml`에 있다.

| 시나리오 | 수준 | 조건 (예) |
|---|---|---|
| D | L0 | 영속 저장소(DB, 파일 저장)가 감지되지 않음 |
| D | L1 | 사용자가 만든 데이터가 영속 저장소에 있음 (기본값) |
| D | L2 | 결제나 유료 구독이 있음, 또는 B2B 계약 신호(조직·팀·청구 모델) |
| D | L3 | 도메인이 재난·안전·의료·공공 알림으로 추론됨 |
| T | L0 | 도메인이 사내 도구이고, 공개 가입이 없고, SSO만 있음 |
| T | L1 | 공개 웹 서비스 (기본값) |
| T | L2 | 예약·티켓팅·쿠폰·오픈 시각 같은 예고된 이벤트 신호 |
| T | L3 | 도메인이 재난·속보·실시간 이벤트, 또는 선착순 신호 |
| U | L0 | T=L0이고 D≤L1 |
| U | L1 | 기본값 |
| U | L2 | T≥L2 또는 C≥L2 또는 마이그레이션 디렉터리가 있음 |
| U | L3 | C=L3이고 T≥L2 |
| C | L0 | 쓰기 경로가 캐시·로그·분석 이벤트뿐임 |
| C | L1 | 사용자 데이터 쓰기가 있음 (기본값) |
| C | L2 | 웹훅 수신, 비동기 작업 큐, 클라이언트 재시도 경로가 있음 |
| C | L3 | 결제 SDK, 재고·잔액·좌석 차감 패턴 |

### 4.3 가정 (코드로 알 수 없는 값)

필요 수준마다 수치 가정을 붙인다. 리포트 맨 위에 "이렇게 가정했어요"로 노출하고, 사용자가 고치면 ③부터 다시 계산한다.

| 수준 | 가정 |
|---|---|
| T L1 | 평시 동시 접속 50, 피크 = 평시 × 3, 10분에 걸쳐 증가 |
| T L2 | 피크 = 평시 × 10, 예고 시각에 시작 |
| T L3 | 피크 = 평시 × 20, 1분 안에 도달 (`simple-web-app` 부하 시나리오와 같은 비율) |
| D L1 | RPO 24시간, RTO 4시간 |
| D L2 | RPO 5분, RTO 30분 |
| D L3 | RPO 1분 이하, RTO 5분 이하, 의존성 장애 시 읽기 기능 유지 |
| C L3 | 결제·재고 데이터 RPO 0 (커밋된 쓰기는 잃지 않음) |

평시 동시 접속 기본값은 도메인별 표(`rules/assumptions.yaml`)에서 정한다. 리전은 UI 언어와 통화로 추론하고, 기본값은 서울(`ap-northeast-2` / `asia-northeast3`)이다.

### 4.4 현재 수준과 차이

- 수준마다 **통제(control)** 목록이 있다. 예: D L2 = {DB Multi-AZ, Pod 존 분산, DB 자동 페일오버}.
- 통제는 사실로 충족 여부를 판단한다. 판단할 근거가 없으면 "미확인"이다.
- 현재 수준 = 모든 통제가 충족된 가장 높은 수준.
- 차이 = 필요 − 현재. 양수면 **부족**(위험, 처방 생성), 음수면 **과잉**(비용 낭비, 축소 처방 생성).
- 인프라 파일이 전혀 없으면 인프라 통제는 모두 미충족이다. 이 경우 처방은 "보완"이 아니라 "새로 구성"이 된다.

## 5. 데이터 모델

모두 pydantic 모델이고 `report.json`의 스키마가 된다.

```python
class Evidence(BaseModel):
    path: str            # 저장소 기준 상대 경로
    line: int | None     # 파일 전체가 근거면 None
    snippet: str         # 근거 줄 원문 (최대 200자)

class Fact(BaseModel):
    id: str              # 예: "state.session.in_memory"
    value: str | int | bool | dict
    evidence: list[Evidence]
    source: Literal["detector", "inference"]
    confidence: Literal["high", "medium"]   # 탐지기는 high, 추론은 medium

class Assumption(BaseModel):
    key: str             # 예: "traffic.baseline_concurrency"
    value: float | str
    reason: str          # 왜 이 값인지 (도메인 근거)
    overridden: bool     # 사용자가 고쳤는지

class LevelDecision(BaseModel):
    scenario: Literal["D", "T", "U", "C"]
    required: int        # 0~3
    current: int
    rule_ids: list[str]  # 필요 수준을 정한 규칙
    controls: list[ControlStatus]   # 통제별 충족/미충족/미확인 + 근거

class Prescription(BaseModel):
    id: str
    kind: Literal["code", "infra", "reduce"]  # reduce = 과잉 축소
    scenario: str
    rule_id: str
    summary: str         # 쉬운 말 한 줄
    detail: str          # 전문가용 설명
    tier_specific: dict[str, str]   # 티어별 구현 방법
    monthly_cost_delta_usd: float | None

class TierOption(BaseModel):
    tier: Literal[0, 1, 2]
    platform: str        # 예: "vercel+supabase", "cloud-run", "ecs-fargate", "gke", "eks"
    feasible: bool
    excluded_by: list[str]          # 제외한 규칙 ID
    monthly_baseline_usd: float | None
    peak_hourly_usd: float | None
    migration_effort: Literal["none", "small", "medium", "large"]

class ControlStatus(BaseModel):
    control_id: str      # 예: "D-CTL-002"
    status: Literal["met", "unmet", "unknown"]
    evidence: list[Evidence]

class DroppedInference(BaseModel):
    claim: dict          # LLM이 낸 원래 항목
    reason: str          # 예: "인용한 줄이 존재하지 않음"

class Report(BaseModel):
    repo: str
    commit: str
    generated_at: datetime
    facts: list[Fact]
    assumptions: list[Assumption]
    levels: list[LevelDecision]
    prescriptions: list[Prescription]
    tiers: list[TierOption]
    chosen_tier: TierOption
    dropped_inferences: list[DroppedInference]   # 근거 검사에서 버린 LLM 추론
    rulebook_version: str
    price_snapshot_date: date
```

## 6. ① 탐지 계층

결정적이다. 같은 커밋이면 같은 사실이 나온다.

### 6.1 지원 범위
- **1차(규칙 완비):** JavaScript/TypeScript(Node, Next.js, Express, NestJS), Python(FastAPI, Django, Flask).
- **그 외 언어:** 의존성 파일과 인프라 파일만 탐지하고, 코드 수준 사실은 ② 추론에 맡긴다(신뢰도 medium).

### 6.2 탐지기 구성

| 탐지기 | 방법 | 만드는 사실 (예) |
|---|---|---|
| manifest | `package.json`, `pyproject.toml`, `requirements*.txt`, lock 파일 파싱 | `runtime.*`, `framework.*`, `dep.*` (stripe, prisma, socket.io, bullmq …) |
| entrypoint | scripts, `Procfile`, 프레임워크 규약 | `process.web`, `process.worker`, `process.cron`, `frontend.static` / `frontend.ssr` |
| code (semgrep) | 언어별 semgrep 규칙 (`detectors/semgrep/*.yaml`) | `state.session.in_memory`, `state.upload.local_fs`, `state.inmem_cache`, `ws.no_shared_adapter`, `cron.no_lock`, `db.connect_per_request`, `ext.no_timeout`, `webhook.no_dedupe`, `tx.multi_write_no_tx`, `concurrency.decrement_no_lock`, `ops.sigterm_handler`, `ops.health_endpoint`, `ops.file_logging`, `heavy.password_hash`, `heavy.image`, `heavy.llm_call` |
| schema | Prisma schema, SQL 마이그레이션, SQLAlchemy/Django 모델 | `db.kind`, `db.sqlite_file`, `data.user_generated`, `data.payment`, `data.inventory`, `db.migration_tool`, `db.migration.destructive` (DROP/RENAME/NOT NULL 추가) |
| config | `.env.example`, 코드의 env 참조, 비밀 패턴 | `env.required`, `secret.hardcoded`, `config.localhost_hardcoded` |
| infra | Dockerfile, compose, k8s YAML(kustomize는 `kustomize build` 결과), Terraform(HCL 파싱), `vercel.json` 등 | `infra.platform`, `k8s.hpa`, `k8s.pdb`, `k8s.probe.readiness`, `k8s.prestop`, `k8s.topology_spread`, `k8s.resources`, `tf.db.multi_az`, `tf.db.backup_retention`, `tf.nat_gateway_count`, `tf.instance_types`, `tf.region_count` |
| repo | git 로그, 테스트 디렉터리, CI 파일 | `ops.tests`, `ops.ci`, `repo.commit_frequency` |

### 6.3 탐지 규칙의 품질 관리
- semgrep 규칙마다 양성/음성 예제 파일을 둔다(`detectors/semgrep/tests/`). `semgrep --test`로 검증한다.
- 픽스처 저장소(§13)마다 기대 사실 목록(golden)을 두고 회귀 테스트한다.

## 7. ② 추론 계층 (LLM)

### 7.1 하는 일
1. **도메인 분류**: README, 라우트 이름, 페이지 문구, 스키마로 도메인을 고른다. 목록은 `rules/domains.yaml`에 고정한다(커뮤니티, 커머스, 예약·티켓팅, 사내 도구, 콘텐츠·블로그, SaaS B2B, 재난·공공 알림, 실시간·채팅, 기타).
2. **모호한 사실 판단**: 탐지기가 "후보"로 올린 것을 확정한다. 예: `fs.writeFile`이 사용자 업로드인지 빌드 스크립트인지.
3. **1차 지원 밖 언어의 코드 수준 사실**을 추론한다.
4. **신호 추출**: 예고된 이벤트 신호, 선착순 신호, B2B 신호 등 §4.2 규칙의 입력.

### 7.2 근거 검사 (grounding)
LLM 출력은 JSON 스키마로 받고, 각 항목은 `Evidence`를 하나 이상 가져야 한다. 검사기는 다음을 확인한다.
- 파일과 줄이 존재한다.
- `snippet`이 그 줄(앞뒤 2줄 허용)과 일치한다.
- 사실 ID가 허용 목록에 있다.

통과하지 못한 항목은 버리고 `dropped_inferences`에 이유와 함께 남긴다. 리포트에서도 보인다.

### 7.3 실행 방식
- Claude Agent SDK(Python)로 실행한다. 에이전트에게는 읽기 전용 도구(Read, Grep, Glob)만 준다.
- 입력: ① 사실 목록 + 저장소 파일 트리. 에이전트는 필요한 파일을 직접 읽는다.
- 결과는 `(저장소 커밋, 규칙집 버전, 프롬프트 버전)`을 키로 캐시한다. 같은 커밋을 다시 진단하면 같은 추론을 쓴다.
- 도메인 분류는 3회 실행해서 다수결로 정한다. 셋이 모두 다르면 "기타"로 두고 가정에 표시한다.

## 8. 규칙집

판정의 전부이자 면접 자료다. `rules/` 아래 YAML로 쓰고, 엔진은 이 파일만 해석한다.

### 8.1 규칙 형식

```yaml
id: C-L3-001
kind: level            # level | control | prescription | tier | cost
scenario: C
title: 결제가 있으면 정합성은 핵심 수준
when:
  any_fact: [dep.stripe, dep.toss_payments, data.payment]
then:
  required_level: 3
why: >
  결제는 재시도와 웹훅 재전송이 일상적으로 일어난다. 중복 청구나 결제 유실은
  돈과 신뢰를 직접 잃는다.
tradeoff: >
  DB 동기 복제와 아웃박스 처리로 쓰기 지연과 비용이 늘어난다.
sources:
  - url: https://docs.stripe.com/webhooks
    quote: "..."
    checked_at: 2026-10-01
```

```yaml
id: T-TIER-003
kind: tier
title: 1분 안에 20배 폭증이면 scale-to-zero 단독 구성은 제외
when:
  level: {T: 3}
  assumption: {traffic.ramp_seconds: {lte: 60}}
then:
  require_on_tier1: [min_instances >= baseline_instances]
why: >
  콜드 스타트와 인스턴스 기동 시간 동안 들어온 요청은 대기하거나 실패한다.
  예고 없는 폭증에는 최소 인스턴스를 남겨 두어야 한다.
tradeoff: 유휴 시간에도 최소 인스턴스 비용이 나간다.
sources: [...]
```

### 8.2 규칙 종류
| 종류 | 역할 | 예 |
|---|---|---|
| level | 필요 수준 결정 (§4.2) | 결제 → C L3 |
| control | 통제의 충족 판단 | D L2 "DB Multi-AZ": `tf.db.multi_az == true` 또는 매니지드 HA 설정 |
| prescription | 미충족 통제 → 처방 | 인메모리 세션 → Redis 세션 저장소 (코드) + 매니지드 Redis (인프라) |
| tier | 티어 제외·조건 | 장시간 연결·상시 워커가 있으면 티어 0의 서버리스 함수 제외 |
| cost | 비용 함정·과잉 탐지 | T L0인데 노드 3대 이상 + AZ별 NAT Gateway → 축소 처방 |

### 8.3 출처 원칙
- 모든 규칙은 공식 1차 자료(클라우드 공식 문서, kubernetes.io, 프레임워크·DB 공식 문서, Twelve-Factor, Stripe 문서 등)를 하나 이상 인용한다. 예외는 이 문서의 설계 원칙(§2)에서 직접 나온 규칙뿐이고, 그 경우 출처 칸에 원칙 번호를 적는다.
- 출처마다 URL, 짧은 인용문, 확인 날짜를 적는다. 수치(타임아웃 상한, 가격 등)는 반드시 출처를 연 날짜 기준이다.
- CI에서 `infrafit rules lint`가 출처 없는 규칙, 90일 넘게 확인하지 않은 출처를 잡는다.
- 규칙집의 출처 목록과 확인 결과는 §15에 둔다.

### 8.4 1차 규칙 목록
규칙 ID 체계: `{시나리오|TIER|COST}-{L수준|종류}-{번호}`. 구현 계획에서 하나씩 YAML로 옮긴다.

**재난 (D)**
| ID | 조건 → 결정 | 출처 |
|---|---|---|
| D-CTL-001 | D≥1: DB 자동 백업 + 보존 기간 ≥ 7일 (RDS는 API·CLI로 만들면 기본 보존 기간이 1일이므로 Terraform 값을 반드시 확인) | S10 |
| D-CTL-002 | D≥2: DB Multi-AZ(동기 대기) 또는 regional HA | S10 |
| D-CTL-003 | D≥2: 앱 Pod/태스크가 2개 이상의 존에 분산 | S6, S17 |
| D-CTL-004 | D≥2: 의존성 장애가 liveness 실패로 번지지 않음 (liveness가 DB를 보지 않음) | S6 |
| D-CTL-005 | D≥3: 외부 의존성 호출에 타임아웃 + 실패 시 디그레이드 경로(stale 캐시 등) | S1, S13 |
| D-CTL-006 | D≥3: 복구 절차 문서 + P4 복구 리허설 통과 | S13 |
| D-PRE-001 | SQLite 파일 DB + D≥1 → 매니지드 Postgres로 이전 (코드: 드라이버·마이그레이션) | S1 |
| D-PRE-002 | 로컬 디스크 업로드 → 오브젝트 스토리지 | S1 |

**트래픽 폭증 (T)**
| ID | 조건 → 결정 | 출처 |
|---|---|---|
| T-CTL-001 | T≥1: 프로세스가 상태를 갖지 않음 (세션·업로드·인메모리 상태 없음) | S1 |
| T-CTL-002 | T≥1: 오토스케일 설정 + 상한 | S6, S2 |
| T-CTL-003 | T≥2: 최대 인스턴스 × 풀 크기 ≤ DB 최대 커넥션, 아니면 커넥션 풀러 | S8 |
| T-CTL-004 | T≥2: 읽기 많은 경로에 캐시 | S13 |
| T-CTL-005 | T≥2: 예고 시각 기준 사전 증설(스케줄 스케일링 또는 min 상향) | S2, S6 |
| T-CTL-006 | T≥3: 쓰기 경로에 큐 + 백프레셔(큐 한도 초과 시 503 + Retry-After) | S7 |
| T-CTL-007 | T≥3: 레이트 리밋 (사용자 기준 + IP 기준) | S13 |
| T-CTL-008 | T≥3: 비밀번호 해시·이미지 처리 등 무거운 작업을 별도 워크로드로 격리 | S13 |
| T-CTL-009 | T≥3 & 티어 2: 노드 여유 용량(저우선순위 자리표시 Pod) 또는 빠른 노드 프로비저닝 | S14 |
| T-CTL-010 | T≥3 & 큐 워커: CPU가 아닌 큐 길이로 확장 | S7 |
| T-PRE-001 | 웹소켓 + 공유 어댑터 없음 → Redis 어댑터 | S1 |
| T-PRE-002 | 크론 + 분산 락 없음 → 단일 실행 보장(스케줄러 서비스 또는 락) | S1 |
| T-PRE-003 | 서버리스에서 요청마다 DB 연결 → 풀러(RDS Proxy, PgBouncer 등) | S8 |

**무중단 배포 (U)**
| ID | 조건 → 결정 | 출처 |
|---|---|---|
| U-CTL-001 | U≥1: readiness probe | S6 |
| U-CTL-002 | U≥1: SIGTERM 처리(진행 중 요청 마무리 후 종료). 유예 시간은 플랫폼마다 다르다: Cloud Run 10초, k8s 기본 30초 | S1, S3, S6 |
| U-CTL-003 | U≥2: 파괴적 마이그레이션을 expand/contract로 분리 | S9 |
| U-CTL-004 | U≥2: 마이그레이션을 앱 기동과 분리된 단계(Job/태스크)로 실행 | S9 |
| U-CTL-005 | U≥2: PDB(티어 2) / 최소 정상 비율(티어 1) | S6, S4 |
| U-CTL-006 | U≥2: LB 드레이닝 ≥ preStop 지연, 종료 유예 시간 안에 들어감 | S6 |
| U-CTL-007 | U≥2: 실패 시 자동 롤백(ECS 배포 서킷 브레이커, 롤아웃 실패 감지 등) | S4 |
| U-CTL-008 | U≥3: 카나리 + 오류율 기반 자동 중단 | S13 |

**정합성 (C)**
| ID | 조건 → 결정 | 출처 |
|---|---|---|
| C-CTL-001 | C≥1: 여러 테이블을 바꾸는 쓰기는 트랜잭션 안에서 | S8 |
| C-CTL-002 | C≥2: 웹훅은 이벤트 ID로 중복 제거 + 순서에 의존하지 않음 | S12 |
| C-CTL-003 | C≥2: 클라이언트 재시도 가능한 쓰기에 멱등성 키 | S12 |
| C-CTL-004 | C≥2: 큐 소비자가 멱등 (at-least-once 전제) | S15 |
| C-CTL-005 | C≥3: 재고·잔액 차감에 행 잠금 또는 버전 검사 | S8 |
| C-CTL-006 | C≥3: 결제 데이터 DB는 동기 복제(Multi-AZ). 비동기 읽기 복제본에서 쓰기 직후 읽기 금지 | S10, S11 |
| C-CTL-007 | C≥3: 외부 결제 호출에 멱등성 키 | S12 |

**티어 (TIER)**
| ID | 조건 → 결정 | 출처 |
|---|---|---|
| TIER-001 | 상시 실행 워커, 함수 최대 실행 시간을 넘는 작업, 4.5MB를 넘는 요청 본문이 있으면 티어 0의 서버리스 함수(Vercel 등)만으로는 불가 | S27 |
| TIER-002 | 요청 처리 시간이 티어 1 플랫폼 타임아웃 상한(Cloud Run 최대 60분, 웹소켓도 이 제한을 받음)을 넘는 경로가 있으면 해당 플랫폼 제외 | S2 |
| TIER-003 | T=3 & 1분 램프 → 티어 1은 최소 인스턴스 필수 | S2 |
| TIER-004 | 티어 2는 다음 중 하나가 있을 때만 후보: 서비스 5개 이상, 큐 길이 기반 확장 + 노드 여유 용량 필요, 네트워크 정책·사이드카 필요, 이미 k8s 운영 중 | S5 (고정비) |
| TIER-005 | 기존 플랫폼이 필요 수준을 만족하면 유지 (교체 비용 > 절감액) | 원칙 6 |

**비용 (COST)**
| ID | 조건 → 결정 | 출처 |
|---|---|---|
| COST-001 | T≤1 & D≤1인데 티어 2 → 과잉, 티어 1 견적과 비교 | S5, S21 |
| COST-002 | AZ별 NAT Gateway + 트래픽 적음 → 비용 경고. VPC 엔드포인트, 리전 NAT Gateway, D≤1이면 단일 NAT 검토. D≥2이면 AZ별 NAT가 AWS 권장 구성임을 함께 표시 | S18 |
| COST-003 | AZ 간 트래픽이 많은 구조 → 존 인지 라우팅 검토 | S25 |
| COST-004 | 상태 없는 워커·배치 → Spot / Fargate Spot (중단 통보 견디는 조건) | S22 |
| COST-005 | 멀티 아키텍처 빌드 가능 → ARM(Graviton) 인스턴스 (AWS 공식 문구: 비슷한 x86 인스턴스보다 최대 20% 저렴) | S23 |
| COST-006 | requests가 P4 실측의 2배 이상 → right-sizing (VPA 추천 모드 참고) | S26 |
| COST-007 | D≤1인데 멀티 리전 → 과잉 | S13 |
| COST-008 | 요청마다 LLM 등 유료 외부 API → 트래픽 비례 비용 경고 + 사용자별 한도 | 원칙 5 |
| COST-009 | C=3 데이터의 단일 AZ 구성 → **절감 대상 아님** 표시 (반대 방향 규칙) | S10 |

## 9. ⑥ 티어와 비용

### 9.1 티어 후보
| 티어 | 플랫폼 후보 | 산출물 (P3) |
|---|---|---|
| 0 현재 플랫폼 유지 | Vercel, Netlify, Supabase, Firebase 등 이미 쓰는 것 | 코드 수정 + 플랫폼 설정 |
| 1 관리형 컨테이너 | Cloud Run, ECS Fargate | Dockerfile + 서비스 정의(Terraform) |
| 2 쿠버네티스 | GKE, EKS | Terraform + Kustomize 매니페스트 |

### 9.2 선택 절차
1. 티어 규칙으로 불가능한 후보를 제외한다(이유를 남긴다).
2. 남은 후보마다 처방을 그 티어의 자원 목록(BOM)으로 바꾼다. 예: "Multi-AZ DB" → `db.r7g.large Multi-AZ` 또는 Cloud SQL HA.
3. 자원 목록을 가격 계층에 넣어 평시 월 비용과 피크 시간당 비용을 계산한다.
4. 이전 비용(migration_effort)을 더해 가장 낮은 후보를 고른다. 동점이면 운영 부담이 낮은 쪽(낮은 티어)을 고른다.
5. 클라우드는 코드가 이미 쓰는 클라우드 SDK·설정을 따른다. 신호가 없으면 두 클라우드 견적을 모두 보여주고 싼 쪽을 고른다.

### 9.3 가격 계층
- 가격은 공식 API로 가져온다: AWS Price List Query API, Google Cloud Billing Catalog API (S20). 티어 1·2의 Terraform은 Infracost로 교차 확인한다 (S19).
- Infracost는 Terraform·CloudFormation·CDK를 다루고 k8s 매니페스트는 다루지 않는다. 그래서 티어 2의 노드 수는 매니페스트의 requests 합계와 HPA 상한으로 직접 계산해서 Terraform 노드 그룹 크기로 바꾼 뒤 견적을 낸다.
- 가격은 날짜와 함께 `prices/snapshot-YYYY-MM-DD.json`으로 저장한다. API가 실패하면 마지막 스냅샷을 쓰고 리포트에 날짜를 표시한다.
- 출력: 평시 월 비용, 피크 시간당 비용, 사용자 1,000명당 월 비용, 시나리오 수준을 한 단계 올리거나 내릴 때의 월 비용 차이.
- P1의 비용은 가정한 부하 기준 **견적**이다. P4가 실측으로 교체한다.

## 10. ⑦ 리포트

### 10.1 구조
1. **요약**: 선택한 티어, 평시 월 비용, 시나리오별 필요/현재 수준, 위험 개수, 과잉 개수
2. **이렇게 가정했어요**: 도메인, 가정 수치, 근거. 고치는 방법(`infrafit.yaml`)
3. **시나리오 카드** ×4: 필요 수준(근거), 현재 수준, 통제별 상태, 처방
4. **티어 비교**: 후보별 가능 여부, 제외 이유, 견적
5. **비용**: 항목별 견적, 과잉 지적, 수준별 비용 차이
6. **버린 추론**: 근거 검사에서 탈락한 LLM 주장
7. **다음 단계**: P2 코드 수정, P3 배포, P4 검증

### 10.2 두 깊이
- 기본: 쉬운 말 한 줄 + 영향("서버를 2대로 늘리면 로그인이 풀려요").
- 펼치기: 규칙 ID, 사실과 근거 줄, 이유, 트레이드오프, 출처 링크.

설명 문장은 LLM이 쓰지만, 입력은 판정 결과로 고정한다. 출력 검사기가 설명 안의 수치·수준·티어가 판정과 같은지 확인한다.

### 10.3 사용자 조정
저장소 루트의 `infrafit.yaml`(선택)로 가정과 수준을 고칠 수 있다.
```yaml
assumptions:
  traffic.baseline_concurrency: 200
levels:
  D: 1          # 재난 시 필수 서비스가 아님
```
조정한 값은 리포트에 "사용자 지정"으로 표시한다.

## 11. 인터페이스 (P1)
- CLI: `infrafit diagnose <경로|GitHub URL> [--out DIR] [--no-llm]`
  - `--no-llm`: 탐지 + 규칙만 실행. 도메인은 기본값, 추론 사실은 비어 있음. 결정성 테스트와 오프라인 실행용.
- `infrafit rules lint`: 규칙 형식, 출처, 확인 날짜 검사.
- `infrafit explain <규칙 ID>`: 규칙 하나를 사람용으로 출력 (면접 시연용).
- Claude Code 플러그인(얇은 래퍼): `/infrafit` 스킬이 CLI를 실행하고 리포트를 요약한다.

## 12. 오류 처리
| 상황 | 동작 |
|---|---|
| 1차 지원 밖 언어 | 탐지는 manifest/infra까지만, 코드 수준은 추론(medium). 리포트에 표시 |
| 저장소가 큼 (파일 5만 개 초과) | `node_modules`, `vendor`, 빌드 산출물 제외 후 진행. 제외 목록 표시 |
| LLM 호출 실패 | `--no-llm` 결과로 리포트 생성, 상단에 "추론 없이 생성됨" 표시 |
| 근거 검사 실패 | 해당 추론만 버림 (§7.2) |
| `kustomize build`/HCL 파싱 실패 | 해당 파일을 원문 YAML/HCL 정규식 탐지로 낮춤, 사실 신뢰도 medium |
| 가격 API 실패 | 마지막 스냅샷 사용, 날짜 표시 |
| 통제 판단 근거 없음 | "미확인". 현재 수준 계산에서는 미충족으로 취급하고 리포트에 따로 표시 |

## 13. 테스트

### 13.1 픽스처 저장소
`fixtures/` 아래 네 개를 둔다. 각각 기대 사실(golden facts)과 기대 판정(golden decisions)을 가진다.

| 픽스처 | 내용 | 기대 판정 (핵심) |
|---|---|---|
| F1 `simple-web-app` | 기존 저장소 스냅샷 (커밋을 고정해서 복사) | D3 T3 U2 C2 필요. 앱 쪽 통제(상태 없음, 큐·백프레셔, 멱등성 키, 존 분산, PDB, preStop)는 충족. Terraform이 아직 없어 DB Multi-AZ·백업 같은 인프라 통제는 미충족 → 인프라는 "새로 구성" 처방. 복구 리허설(D-CTL-006) 미충족. 티어 2 선택 |
| F2 `vibe-shop` | Next.js + SQLite + 인메모리 세션 + 로컬 업로드 + Stripe 웹훅(중복 처리 없음) + 재고 차감(잠금 없음) | C3 T2 D2 필요. 현재 C≤1, T0, D0. 코드 처방 다수(D-PRE-001/002, C-CTL-002/005, T-CTL-001). 티어 1 선택 |
| F3 `overbuilt-internal` | 사내 도구인데 EKS + 3 AZ NAT + Multi-AZ RDS + 멀티 리전 | T0 D1 필요. 과잉 처방(COST-001/002/007). 티어 1 또는 0 권고 |
| F4 `small-blog` | Next.js + Supabase on Vercel, 정적 위주 | T1 D1 필요. 현재 충족. 티어 0 유지, 변경 없음 |

F2~F4는 이 저장소 안에서 새로 만든다.

### 13.2 테스트 종류
- 탐지기 단위 테스트: semgrep `--test`, 파서별 pytest.
- 규칙 엔진 단위 테스트: 규칙마다 걸리는 경우와 걸리지 않는 경우.
- 골든 테스트: 픽스처 × `--no-llm` 결과가 기대 사실·판정과 같다.
- 추론 평가: 픽스처마다 추론을 5회 실행해서 도메인 분류 일치율, 근거 검사 통과율을 기록한다. 기준: 도메인 일치 5/5, 근거 통과율 90% 이상.
- 리포트 검사: 설명 문장의 수치가 판정과 일치하는지 검사기 테스트.

## 14. 기술 스택과 디렉터리

- Python 3.12, uv, pydantic v2, semgrep(OSS CLI), python-hcl2, PyYAML, kustomize CLI, Jinja2(HTML 리포트), pytest
- LLM: Claude Agent SDK (Python). 모델 선택과 SDK 사용법은 구현 계획 단계에서 claude-api 레퍼런스로 확정한다.

```
one-click-deploy-agent/
  infrafit/
    cli.py
    model.py              # §5 데이터 모델
    detect/               # ① 탐지기 (manifest, entrypoint, code, schema, config, infra, repo)
      semgrep/            #   semgrep 규칙 + tests/
    infer/                # ② 추론 (Agent SDK, 프롬프트, 근거 검사기)
    engine/               # ③④⑤ 규칙 해석기 (level, control, prescription)
    tier/                 # ⑥ 티어 선택
    pricing/              # ⑥ 가격 API 클라이언트, 스냅샷
    report/               # ⑦ JSON/HTML 리포트, 설명 생성, 설명 검사기
  rules/
    domains.yaml
    assumptions.yaml
    levels/  controls/  prescriptions/  tiers/  costs/
  prices/                 # 가격 스냅샷
  fixtures/               # F1~F4 + golden 파일
  tests/
  docs/
    rules/                # 규칙집 사람용 문서 (rules/*.yaml에서 생성, 면접 자료)
    superpowers/specs/
```

## 15. 출처 목록

규칙의 `sources`는 이 표의 ID를 쓴다. 모두 2026-10-01에 공식 페이지를 직접 열어 확인했다. Google Cloud 문서는 `docs.cloud.google.com`으로 옮겨졌으므로 새 주소를 쓴다.

| ID | 주제 | 확인한 내용 | URL |
|---|---|---|---|
| S1 | Twelve-Factor | VI 프로세스는 상태 없음·공유 없음, IX SIGTERM에 우아하게 종료, XI 로그는 stdout 이벤트 스트림, III 설정은 환경변수 | https://12factor.net/processes · /disposability · /logs · /config |
| S2 | Cloud Run | 요청 타임아웃 기본 300초·최대 3600초, 웹소켓도 요청 타임아웃 적용, 과금 방식(요청 기반 / 인스턴스 기반, 예전 이름 "CPU always allocated"), 최소 인스턴스, 동시성(gcloud·Terraform 기본 80×vCPU, 최대 1000) | https://docs.cloud.google.com/run/docs/configuring/request-timeout · /run/docs/triggering/websockets · /run/docs/configuring/billing-settings · /run/docs/configuring/min-instances · /run/docs/about-concurrency |
| S3 | Cloud Run 종료 | SIGTERM 후 10초 뒤 종료 | https://docs.cloud.google.com/run/docs/container-contract |
| S4 | ECS / Fargate | 장시간 실행 서비스, 배포 서킷 브레이커 자동 롤백(롤링 업데이트 컨트롤러 전용) | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs_services.html · /deployment-circuit-breaker.html |
| S5 | 컨트롤 플레인 요금 | EKS 클러스터당 시간당 $0.10(표준 지원), GKE 클러스터 관리비 시간당 $0.10, GKE 무료 등급 결제 계정당 월 $74.40 크레딧(존 클러스터·Autopilot만) | https://aws.amazon.com/eks/pricing/ · https://cloud.google.com/kubernetes-engine/pricing |
| S6 | Kubernetes | HPA, PDB, preStop 훅, 종료 유예 기본 30초, readiness 실패 시 Service 엔드포인트에서 제외, topologySpreadConstraints | https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/ · /workloads/pods/disruptions/ · /containers/container-lifecycle-hooks/ · /workloads/pods/pod-lifecycle/ · /scheduling-eviction/topology-spread-constraints/ |
| S7 | KEDA | 대기 메시지가 없으면 0으로 축소, SQS·Redis Streams 스케일러 | https://keda.sh/docs/2.21/concepts/scaling-deployments/ · /scalers/aws-sqs/ · /scalers/redis-streams/ |
| S8 | 커넥션과 트랜잭션 | PostgreSQL `max_connections` 기본값은 보통 100, PgBouncer 트랜잭션 풀링, RDS Proxy 커넥션 풀 | https://www.postgresql.org/docs/current/runtime-config-connection.html · https://www.pgbouncer.org/features.html · https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rds-proxy.html |
| S9 | Parallel Change | expand → migrate → contract 세 단계 | https://martinfowler.com/bliki/ParallelChange.html |
| S10 | DB 가용성·백업 | RDS Multi-AZ 동기 대기 복제본과 자동 페일오버, 백업 보존 0~35일(콘솔 기본 7일, API·CLI 기본 1일), PITR(트랜잭션 로그 5분마다 업로드), Cloud SQL HA(두 존 디스크에 복제 후 커밋)와 PITR | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZSingleStandby.html · /USER_WorkingWithAutomatedBackups.BackupRetention.html · /USER_PIT.html · https://docs.cloud.google.com/sql/docs/postgres/high-availability · /sql/docs/postgres/backup-recovery/pitr |
| S11 | 읽기 복제본 | RDS 읽기 복제본은 비동기 복제, 지연은 ReplicaLag 지표. 쓰기 직후 읽기 위험은 비동기 복제에서 나온 우리의 추론임을 규칙에 명시한다 | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_ReadRepl.html |
| S12 | Stripe | `Idempotency-Key` 헤더(v1은 24시간 이후 키 삭제 가능, v2는 30일), 웹훅은 같은 이벤트가 여러 번 올 수 있으니 이벤트 ID로 중복 제거, 전달 순서 보장 없음 | https://docs.stripe.com/api/idempotent_requests · https://docs.stripe.com/api-v2-overview · https://docs.stripe.com/webhooks |
| S13 | 아키텍처 프레임워크 | AWS Well-Architected 신뢰성 원칙, Google Cloud Well-Architected Framework(이전 이름 Architecture Framework) 신뢰성 원칙, AWS DR 전략 4가지(백업·복원, 파일럿 라이트, 웜 스탠바이, 멀티 사이트 액티브/액티브) | https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html · https://docs.cloud.google.com/architecture/framework/reliability · https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html |
| S14 | 노드 여유 용량 | 낮은 우선순위 자리표시 Pod로 용량 확보 | https://docs.cloud.google.com/kubernetes-engine/docs/how-to/capacity-provisioning · https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md |
| S15 | SQS | FIFO는 5분 중복 제거 구간, 표준 큐는 최소 1회 전달이므로 소비자를 멱등하게 | https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues-exactly-once-processing.html · /standard-queues-at-least-once-delivery.html |
| S16 | 장애 주입 | AWS FIS, GCP Fault Injection Testing(Pre-GA), Chaos Mesh | https://docs.aws.amazon.com/fis/latest/userguide/what-is.html · https://docs.cloud.google.com/fault-injection-testing · https://chaos-mesh.org/docs/ |
| S17 | 존 분산 | GKE 리전 클러스터는 컨트롤 플레인과 노드를 여러 존에 복제, EKS 모범 사례의 존 분산 | https://docs.cloud.google.com/kubernetes-engine/docs/concepts/regional-clusters · https://docs.aws.amazon.com/eks/latest/best-practices/application.html |
| S18 | NAT Gateway | 서울 시간당 $0.059 + GB당 $0.059(us-east-1은 $0.045/$0.045), 복원력을 위해 AZ마다 NAT 권장, 리전 NAT Gateway 존재 | https://aws.amazon.com/vpc/pricing/ · https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-basics.html · /nat-gateways-regional.html |
| S19 | Infracost | Terraform·CloudFormation·CDK 비용 추정(Apache-2.0). k8s 매니페스트는 지원 목록에 없음 | https://www.infracost.io/docs/ |
| S20 | 가격 API | AWS Price List `GetProducts`, Google Cloud Billing `services.skus.list` | https://docs.aws.amazon.com/aws-cost-management/latest/APIReference/API_pricing_GetProducts.html · https://docs.cloud.google.com/billing/docs/reference/rest/v1/services.skus/list |
| S21 | Cloud Run 요금 | 요청 기반 무료 등급(월 18만 vCPU초, 36만 GiB초, 요청 200만 건), 최소 인스턴스는 유휴 요율로 과금 | https://cloud.google.com/run/pricing |
| S22 | Spot | Fargate Spot 최대 70% 할인과 중단 2분 전 SIGTERM, EC2 Spot 2분 전 통보, GKE Spot VM 기본 30초 유예 | https://aws.amazon.com/fargate/pricing/ · https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-capacity-providers.html · https://docs.cloud.google.com/kubernetes-engine/docs/concepts/spot-vms |
| S23 | Graviton | 비슷한 x86 인스턴스보다 최대 20% 저렴 | https://aws.amazon.com/ec2/graviton/ |
| S24 | GKE Autopilot | Pod 기반 과금(Pod가 요청한 CPU·메모리·임시 저장소를 초 단위로) | https://cloud.google.com/kubernetes-engine/pricing |
| S25 | AZ 간 전송 | 같은 리전 AZ 간 GB당 방향별 $0.01 | https://aws.amazon.com/ec2/pricing/on-demand/ |
| S26 | right-sizing | requests는 스케줄링 기준, limits는 kubelet이 강제, VPA `Off` 모드는 추천만 함 | https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/ · https://kubernetes.io/docs/concepts/workloads/autoscaling/vertical-pod-autoscale/ |
| S27 | Vercel Functions | 최대 실행 시간 Hobby 300초, Pro·Enterprise 800초(1800초 베타), 요청·응답 본문 4.5MB 제한 | https://vercel.com/docs/functions/limitations |

가격과 한도 수치는 이 날짜 기준이다. 실제 판정에서는 §9.3의 가격 API 값을 쓰고, 이 표는 규칙의 근거 설명에만 쓴다.

## 16. 이후 하위 프로젝트 (개요)

- **P2 앱 코드 수정**: `kind: code` 처방마다 변경 템플릿(프레임워크별)을 두고, 에이전트가 적용한 뒤 기존 테스트와 처방별 검사(예: 세션이 Redis에 저장되는지)를 돌린다. 처방 하나 = 커밋 하나, 커밋 메시지에 규칙 ID.
- **P3 티어별 실행기**: 티어 2부터. `simple-web-app`의 `docs/deploy.md` 계약(Secret 이름, 마이그레이션 Job, REAL_IP_FROM, KEDA)을 만족하는 Terraform(AWS/GCP)과 overlay를 만든다. 그다음 티어 1(Cloud Run, ECS Fargate), 티어 0.
- **P4 검증 루프**: 시나리오 × 필요 수준마다 검증 시나리오를 정의한다. T: k6 스텝·스파이크 부하, D: 존 장애·DB 페일오버·의존성 차단 주입(AWS FIS, Chaos Mesh. GCP Fault Injection Testing은 2026-10 기준 Pre-GA라 기본 수단으로 쓰지 않는다), U: 부하 중 롤아웃하며 오류율 측정, C: 중복 웹훅·동시 주문 주입 후 불변식 검사. 결과로 "동시 N명까지, 월 $X"와 right-sizing 값을 리포트에 되돌려 넣는다.
- **P5 웹 UI**: GitHub URL 입력 → 진단 리포트 → 수준·가정 조정 → P2~P4 실행 버튼.
