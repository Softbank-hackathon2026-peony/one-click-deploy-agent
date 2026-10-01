# one-click-deploy-agent 설계 문서 (v2)

- 작성일: 2026-10-01
- 상태: 설계 검토 중
- 저장소: `one-click-deploy-agent` (이전 이름 `one-click-deploy-k8s`. 실행 대상이 k8s만이 아니게 되어 이름을 바꿨다). CLI와 패키지 이름은 `infrafit`
- v1과의 차이: 판정 모델을 "시나리오 × 수준"에서 **"앱 요구(차원) × 구성 요소 능력"**으로 바꿨다. 판정은 **고정된 단계(S0~S8)**로 진행하고, 단계마다 정해진 JSON을 낸다. 시나리오 수준은 판정의 입력이 아니라 요구에서 파생되는 요약이다.

## 1. 목적

저장소 하나를 받아서 다음을 한다.

1. 코드를 읽고 이 앱이 **무엇으로 어떻게 돌아가는지**, 이미 어떤 인프라가 있는지 파악한다.
2. 코드에서 앱의 **요구**(동시 쓰기, 요청 처리 시간, 상태 보유, 데이터 중요도 등 35개 차원)를 추출한다.
3. 요구를 **모든 후보 구성 요소의 능력**과 맞춰 본다. 컴퓨트 후보에는 Lambda, VM, 관리형 컨테이너, 쿠버네티스, PaaS가 모두 들어간다. 현재 구성 요소도 같은 방식으로 판정한다.
4. 요구를 만족하는 조합 중 **가장 합리적인 구성**을 고르고, 모든 후보의 비교 결과와 탈락 이유를 남긴다.
5. 선택한 구성에 맞게 **앱 코드를 고치고**, 없는 산출물(Dockerfile, Terraform, 매니페스트, CI)을 **만들고**, 잘못된 기존 산출물은 **고치거나 교체**한다.
6. 만든 것을 **검증**한다. 정적 검증 후 배포해서 부하·장애·소크로 확인하고, 실측값으로 판정을 다시 돌린다.
7. 모든 결과를 **고정된 형식의 JSON**(`result.json`)으로 낸다.

### 누구를 위한 도구인가
- 기본 사용자는 Dockerfile, k8s, Terraform을 모르는 **바이브코더**다. 인프라 질문에 답할 수 없으므로 묻지 않는다.
- 개발자나 시니어는 같은 결과에서 근거, 가정, 규칙을 펼쳐 보고 고친다. 사용자 유형마다 흐름을 따로 두지 않는다.

### 면접 과제로서의 목적
이 작품은 클라우드 지식을 보여주는 면접 과제다. 그래서 판단은 LLM이 아니라 **공식 출처가 붙은 지식 베이스와 규칙**이 내린다. "왜 Lambda가 아니고 이것인가"에 대해 결과 JSON의 비교표와 위반 근거로 답할 수 있어야 한다.

## 2. 설계 원칙

1. **판단은 규칙이, LLM은 추출·생성·설명만 한다.** 같은 입력이면 같은 판정이 나온다.
2. **근거 없는 결론은 버린다.** 모든 사실은 `파일:줄` 근거를 갖는다. LLM 추론은 인용한 줄이 실제로 그 내용을 담고 있는지 기계적으로 검사하고, 통과하지 못하면 버린다.
3. **묻지 않는다. 대신 가정을 드러내고, 가정이 틀리면 결론이 어디서 바뀌는지 보여준다(민감도).**
4. **상황을 나열하지 않는다.** 상황은 요구 차원과 구성 요소 능력의 조합에서 나온다. 지식 베이스에는 유한한 두 목록(차원, 능력)과 그 사이의 비교 규칙만 둔다.
5. **필요한 만큼만 만든다.** 능력이 요구보다 훨씬 크면 과잉으로 판정한다. 검증과 관측도 필요한 만큼만 한다.
6. **비용은 모든 판정을 거르는 필터다.** 단, 아끼면 안 되는 곳(금전·규제 데이터의 내구성 등)은 규칙이 명시한다.
7. **기존 인프라도 같은 기준으로 판정한다.** 이미 있다는 사실은 유지할 이유가 아니다. 유지 / 부분 수정 / 교체 중 하나로 판정한다. 기존 구성에 담긴 의도적인 결정(리전, 도메인, 클라우드 계정, 네이밍, 환경 분리)은 판정과 충돌하지 않는 한 따른다. 교체 비용은 판정에 넣되 거부권은 아니다.
8. **모든 후보를 비교한다. 지름길 규칙을 두지 않는다.** "서비스가 5개 이상이면 k8s" 같은 규칙은 금지한다. 후보는 능력 표 전체이고, 탈락은 반드시 "어떤 요구가 어떤 능력을 넘었나"로 설명한다.
9. **생성물은 검증이 리뷰를 대신한다.** 사용자는 생성물을 리뷰할 수 없다. 그래서 모든 생성물은 실행 가능한 검증을 통과해야 하고, 판정에 중요한 설정은 플랫폼 기본값에 맡기지 않고 항상 명시한다.
10. **고정된 워크플로, 고정된 스키마.** 단계 순서와 각 단계 출력 스키마는 고정이다. 단계 출력은 스키마 검증을 통과해야 다음 단계로 간다.

## 3. 지식 베이스

판정과 생성은 아래 문서만 근거로 한다. 사람이 읽는 원본은 `docs/research/`의 Markdown이고, 엔진은 이를 옮긴 기계용 YAML(`knowledge/`)을 읽는다.

| 원본 | 내용 | 기계용 |
|---|---|---|
| [docs/research/dimensions.md](../../research/dimensions.md) | 앱 요구 차원 35개. 값의 범위, 코드에서 읽는 법, 맞춰 볼 능력 키 | `knowledge/dimensions.yaml` |
| [docs/research/capabilities/01~05](../../research/capabilities/README.md) | 구성 요소 148개의 능력. 능력 키 단위, 값마다 공식 출처 | `knowledge/components/*.yaml` |
| [docs/research/capabilities/06~08](../../research/capabilities/README.md) | 구성 요소별 생성 산출물: Terraform 리소스, 핵심 속성, 앱 계약, 로컬 대응, 검증 명령 | `knowledge/artifacts/*.yaml` |
| [docs/research/capabilities/09~10](../../research/capabilities/README.md) | 네트워크 경로 구성 요소(로드밸런서, 인그레스, CDN, DNS, WAF, 인증서, 출구 NAT, 사설 연결)의 능력과 생성 산출물. 능력 값마다 OSI 계층 표시 | `knowledge/components/nw-*.yaml` |
| 요구 조건 변환표 (M1에서 작성) | 차원 값 → 능력 조건 매핑. 비교 규칙은 이 표에서 생성된다(§8.3) | `knowledge/requirements.yaml` |
| 기본값 표 (M1에서 작성) | 플랫폼·라이브러리·앱 서버 기본값과 출처(§6.4) | `knowledge/defaults.yaml` |
| 교체 차이 표 (작성 예정) | 구성 요소 A → B로 바꿀 때 코드 변경 항목 (프레임워크별) | `knowledge/swaps/*.yaml` |
| [docs/research/considerations/](../../research/considerations/README.md) | 고려 요소 878개. 위 문서들과 규칙의 재료 | — |
| `rules/` | 비교 규칙, 위생 규칙, 비용 규칙 (§15) | `rules/*.yaml` |

### 3.1 ID 체계
- 차원: `A1`~`G3` (dimensions.md 그대로)
- 구성 요소: `{계열}:{제공자}/{제품}/{변형}`. 계열은 `cp`(컴퓨트), `ds`(저장소), `ca`(캐시), `qu`(큐), `sc`(스케줄러), `rt`(실시간), `fs`(파일 저장소), `nw`(네트워크 경로). 예: `cp:gcp/cloud-run/request-billing`, `cp:aws/lambda/default`, `cp:aws/ec2/single-vm-compose`, `ds:aws/rds-postgres/multi-az-instance`, `ds:local/sqlite/wal`, `ca:local/process-memory`, `nw:aws/alb/default`, `nw:gcp/classic-alb/gke-ingress`, `nw:app/uvicorn/default`
- 범위(scope): 워크로드 `w-…`, 데이터 `ds-…`, 보조 구성 요소 `svc-…`, 요청 경로 `path-…`
- 능력 값: `{구성 요소 ID}#{능력 키}`. 예: `ds:local/sqlite/wal#DS.concurrent_writers`
- 규칙: §15.2

### 3.2 미확인 값
능력 값이 `미확인`이면 기계용 YAML에서 `unknown`이다. 비교 결과도 `unknown`이 되고(§8.4), 판정에 쓰였다면 결과 JSON의 `unverified`에 반드시 나온다.

### 3.3 스냅샷
지식 베이스와 가격은 날짜가 붙은 스냅샷이다. 결과 JSON의 `run`에 사용한 스냅샷 날짜를 적는다. `infrafit kb lint`가 출처 없는 값, 90일 넘게 확인하지 않은 출처를 잡는다.

## 4. 워크플로 개요

```
 S0 접수       저장소 → intake.json
 S1 인벤토리   [결정적]           무엇이 돌아가고 무엇이 이미 있나 → inventory.json
 S2 프로필     [탐지 + LLM]       워크로드·저장소별 차원 값과 가정 → profile.json
 S3 적합성     [결정적]           (워크로드·데이터) × 모든 후보 구성 요소 → fit.json
 S4 결정       [결정적 + 가격]    조합 후보 → 순위 → 선택 + 민감도 → plan.json
 S5 변경       [LLM, 검증 필수]   코드 수정 + 산출물 생성·수정·교체 → changes.json + 패치
 S6 정적 검증  [결정적]           빌드·실행, plan, 정책, 스키마, 테스트 → verify-static.json
 S7 동적 검증  [배포 시]          부하·장애·소크·관측 → verify-dynamic.json
                                   실측값으로 가정 교체 → S3부터 다시 ─┐
 S8 결과       [결정적 + LLM 설명] → result.json + report.html  ◄──────┘
```

| 단계 | 결정적인가 | LLM | 실패하면 |
|---|---|---|---|
| S0 | 예 | 없음 | 중단 |
| S1 | 예 | 없음 | 해당 파서만 낮은 신뢰도로 대체, 계속 |
| S2 | 탐지는 예, 추론은 캐시로 재현 | 추론 (읽기 전용) | LLM 실패 시 탐지 결과 + 가정만으로 계속 |
| S3 | 예 | 없음 | 중단 |
| S4 | 예 | 없음 | 가능한 후보가 없으면 "가능한 구성 없음"과 막는 위반 목록을 내고 S8로 |
| S5 | 아니오 (검증으로 보정) | 코드 수정, 산출물 작성 | 변경 단위로 롤백, 실패 항목 표시 |
| S6 | 예 | 없음 | S5로 되돌려 고치기(최대 3회), 그래도 실패면 실패로 기록 |
| S7 | 측정값은 아님 | 없음 | 실패한 검증을 기록, 판정 재실행 |
| S8 | 판정 부분은 예 | 설명 문장만 | — |

공통 규칙:
- 단계 출력은 `out/<run-id>/<단계>.json`에 쓴다. 스키마는 `schemas/infrafit.schema.json`의 `$defs`(§14).
- 단계마다 입력 해시(저장소 커밋 + 지식 베이스 버전 + 규칙 버전 + 사용자 조정 + 이전 단계 출력)를 키로 캐시한다. 같은 키면 다시 계산하지 않는다.
- 실행 범위는 `--until S4`(진단·결정까지), `--until S6`(변경과 정적 검증까지), 전체(배포 포함)로 고른다.

## 5. S0 접수

- 입력: 로컬 경로 또는 GitHub URL, 선택적 사용자 조정 파일 `infrafit.yaml`(§13.3)
- 하는 일: 커밋 고정, 파일 트리 수집, 제외 경로 적용(`node_modules`, `vendor`, 빌드 산출물, `.git`), 언어 비율 계산
- 출력 `intake.json`: `repo`, `commit`, `files_total`, `files_scanned`, `excluded[]`, `languages{}`, `overrides`

## 6. S1 인벤토리

결정적이다. "무엇이 있는가"만 정하고 "충분한가"는 판단하지 않는다.

### 6.1 워크로드 찾기
프로세스 단위로 워크로드를 만든다: `web`, `worker`, `scheduled`, `realtime`, `static-frontend`, `migration-job`.
근거: `package.json` scripts, `Procfile`, 프레임워크 규약(Next.js, Django, FastAPI 등), 큐 소비 코드, 크론 정의, 웹소켓 서버, compose 서비스, k8s Deployment·CronJob, 플랫폼 설정.

### 6.2 현재 구성 요소 매핑
쓰고 있는 것을 능력 표 ID로 바꾼다. 예: Prisma `provider = "sqlite"` + `PRAGMA journal_mode=WAL` → `ds:local/sqlite/wal`, `express-session` 기본 저장소 → `ca:local/process-memory`, `vercel.json` → `cp:vercel/functions/<플랜 가정>`.
매핑할 수 없는 것은 `unmapped`로 두고, S2에서 LLM이 능력 표 밖 구성 요소로 처리한다(§7.5).

### 6.3 기존 산출물 파싱
Dockerfile, compose, k8s(kustomize는 `kustomize build` 결과), Terraform(HCL 파싱), 플랫폼 설정(`vercel.json`, `netlify.toml`, `fly.toml`, `render.yaml`, `.railway/railway.ts` 등), CI 파일을 파싱해서 핵심 설정값을 뽑는다.

### 6.4 기본값 사실
설정이 없으면 플랫폼·라이브러리 기본값이 적용된다. 이것이 위험인 경우가 많다(예: Postgres `lock_timeout` 0, ALB 유휴 60초 vs uvicorn keep-alive 5초, `aws_db_instance` 백업 0일). 그래서 설정이 없을 때 "없음"이 아니라 `{value: <기본값>, defaulted: true, default_source: <출처>}`로 기록한다. 기본값 표는 `knowledge/defaults.yaml`.

### 6.5 요청 경로
외부에서 요청을 받는 워크로드마다 요청이 지나는 구간(hop)을 순서대로 기록한다. 범위 ID는 `path-<워크로드>`다.

```
클라이언트 → DNS → CDN·WAF → 로드밸런서·인그레스 → 컨테이너 안 리버스 프록시 → 앱 서버 → (출구 NAT·사설 연결) → 데이터
```

- 각 구간은 구성 요소 ID(`nw:*`, 앱 서버는 `nw:app/<서버>/…`)와 설정값을 갖는다. 설정이 없으면 §6.4의 기본값 사실로 기록한다.
- 근거: 플랫폼 설정, Ingress·Service 매니페스트와 어노테이션, Terraform LB 리소스, nginx 설정, 앱 서버 실행 명령(`uvicorn --timeout-keep-alive`, `gunicorn --keep-alive`, Node `server.keepAliveTimeout`).
- 배포 설정이 없으면 경로는 "앱 서버"만 있는 상태로 기록하고, 나머지 구간은 S4에서 후보 조합이 정해질 때 채워진다.

### 6.6 출력 `inventory.json`
`workloads[]`, `datastores[]`(저장소마다 ID), `current_components[]`(워크로드·저장소별 매핑), `request_paths[]`(경로별 구간 목록), `existing_artifacts[]`(종류, 경로, 파싱된 설정, 기본값 사실), `unmapped[]`.

## 7. S2 프로필

워크로드와 저장소마다 35개 차원의 값을 정한다.

### 7.1 근거의 세 종류
| 종류 | 뜻 | 예 (C1 쓰기 동시성) |
|---|---|---|
| tech | 무엇을 쓰는가 | `better-sqlite3` |
| context | 누가, 얼마나 쓰는가 | 결재·부서 테이블, 쓰기 API 수, `gunicorn -w 4` |
| pain | 이미 한계에 부딪힌 흔적 | `database is locked` 재시도, `busy_timeout` |

### 7.2 추출 방법
- **탐지기(결정적)**: manifest 파싱, semgrep 규칙(JS/TS, Python 1차 지원), 스키마 파싱, 설정 파싱. 차원마다 탐지 규칙을 `knowledge/dimensions.yaml`에 둔다.
- **추론(LLM)**: Claude Agent SDK, 읽기 전용 도구(Read, Grep, Glob)만 사용. 하는 일은 네 가지다.
  1. 도메인 분류(고정 목록, 3회 다수결)
  2. 탐지기가 후보로 올린 것 확정. 예: `fs.writeFile`이 사용자 업로드인지 빌드 스크립트인지
  3. 1차 지원 밖 언어의 차원 추출
  4. 사용 맥락 판단. 예: 동시에 쓰는 주체가 몇이나 되는지
- **근거 검사**: LLM 출력의 각 항목은 근거를 하나 이상 갖고, 파일·줄 존재, 인용 일치(앞뒤 2줄 허용), 허용된 차원 ID와 값인지 검사한다. 통과하지 못하면 버리고 `dropped_inferences`에 남긴다.
- 추론 결과는 `(커밋, 지식 베이스 버전, 프롬프트 버전)`으로 캐시해서 재실행 시 같은 값을 쓴다.

### 7.3 값 결정
- 탐지기 근거가 있으면 탐지기 값(신뢰도 high). 추론만 있으면 추론 값(medium).
- 근거가 없으면 **가정**: 도메인별 기본값 표(`knowledge/assumptions.yaml`, 재료는 considerations/08 파트 2)에서 가져온다. 가정마다 `reason`을 적는다.
- 코드로 알 수 없는 값의 대표: 평시 동시 접속(D2), 데이터 규모(C6), 플랫폼 플랜(G1), 예산 민감도(G3), 외부 공급자 한도(E3).

### 7.4 출력 `profile.json`
`domain`(값, 근거, 투표 결과), `dimensions[]`(차원 ID, 범위(워크로드 또는 저장소 ID), 값, 근거[], 출처, 신뢰도, defaulted), `assumptions[]`, `dropped_inferences[]`.

### 7.5 능력 표에 없는 구성 요소
S1에서 `unmapped`로 남은 구성 요소는 같은 능력 키로 공식 문서를 찾아 프로필을 만든다(출처 인용과 근거 검사 필수). 결과는 `knowledge/components/_runtime/`에 캐시하고 `provisional: true`로 표시한다. 사람이 검토하면 정식 능력 표로 옮긴다.

## 8. S3 적합성

결정적이다. **모든 범위(워크로드, 저장소) × 그 범위에 맞는 계열의 모든 후보**를 비교한다. 현재 구성 요소도 후보 중 하나로 같은 비교를 거친다.

### 8.1 후보 집합
- 컴퓨트 워크로드: `cp:*` 전부 — 티어 0 PaaS, Lambda·Cloud Run functions, Cloud Run(과금 모드별), ECS Fargate·Express Mode, VM(단일 + compose, 오토스케일 그룹), GKE, EKS 등
- 저장소: 같은 질의 모델(C5)을 지원하는 `ds:*` 전부
- 세션·캐시·큐·스케줄러·실시간·파일: 해당 계열 전부
- 네트워크 경로: 구간 종류별 `nw:*` 전부(로드밸런서, 인그레스, CDN, WAF, DNS, 출구, 사설 연결). 경로는 컴퓨트 선택에 따라 구성이 달라지므로 단독 비교 결과는 S4에서 경로로 조립된다(§9.2)
- 제외는 규칙으로만 한다. 예: 서울 리전 필요(D5) + 서울 없음 → 위반

### 8.2 비교 규칙의 종류
| 종류 | 형태 | 예 |
|---|---|---|
| compare | 차원 값 ≤/≥/∈ 능력 값 | A2 최대 처리 시간 ≤ `CP.request_timeout` / C1 = high → `DS.concurrent_writers` = many |
| capacity | 상한 × 단위 소비 ≤ 하류 한도 | (최대 인스턴스 × 풀 크기) ≤ `DS.connections` |
| timing | 시간 값 사이의 부등식 | 앱 keep-alive > LB 유휴 타임아웃, 종료 유예 ≥ preStop + 요청 마무리, 중복 제거 보존 ≥ 상대 재시도 기간 |
| combination | 여러 사실의 AND | readiness가 DB 검사 AND 디그레이드 코드 있음 → 디그레이드가 사용자에게 닿지 않음 |
| overprovision | 능력 ≫ 요구 | D1 = 고정(내부), D2 = 낮음, F1 = 길어도 됨인데 멀티 존 + 노드 3개 이상 |

### 8.3 요구 조건 변환표
비교 규칙은 손으로 하나씩 쓰지 않고, **차원 값이 어떤 능력 조건을 요구하는지**를 적은 변환표(`knowledge/requirements.yaml`)에서 생성한다. 표의 한 줄이 compare 규칙 하나가 된다. 그래서 "왜 이 차원이 이 능력을 요구하는가"를 표 한 곳에서 검토할 수 있다.

| 차원 = 값 | 요구하는 능력 조건 (예) |
|---|---|
| C1 = high | `DS.concurrent_writers` = many |
| C2 = 있음 | `DS.row_contention` ∋ 행 잠금 또는 원자적 갱신 |
| C3 = 강한 불변식 | `DS.transactions` ∋ 다중 행 트랜잭션, 쓰기 직후 읽기는 동기 복제 경로 |
| C7 = 사용자 생성 이상 | `DS.backup` ∋ 자동 백업, 최악 RPO ≤ F3 가정값 |
| F1 = 짧아야 함 | `DS.availability` ∋ 자동 페일오버 / `CP.availability` ∋ 멀티 존 / `NW.availability` ⊇ 리전 |
| A2 = 수십 초 이상 | `CP.request_timeout` ≥ A2 / 경로의 모든 `NW.request_timeout` ≥ A2 |
| A3 = 장시간 연결 | `CP.long_connection` 지원 / 경로의 모든 `NW.websocket` 지원, 지속 한도 ≥ 요구 |
| A4 = 있음 | `CP.cpu_outside_request` = 예 |
| A7 = 큼 | `CP.request_size` ≥ 요구 / 경로의 모든 `NW.body_size` ≥ 요구, 아니면 서명 URL 직접 업로드로 A7 자체를 바꿈 |
| B1 = 있음 | 인스턴스 2개 이상이면 공유 상태 구성 요소(`CA.shared_state`) 필요 (범위 사이 제약, §9.2) |
| B2 = 있음 | `CP.local_disk` = 영속 + 인스턴스 1개, 아니면 파일 저장소 교체 |
| D5 = 한국 | 모든 구성 요소 `*.regions` ∋ 서울 (F5가 데이터 위치를 요구하면 위반, 아니면 지연 비용으로 순위 불이익) |
| E2 = 있음 | 사용자별 한도 장치 필수 (위반이 아니라 S5 변경 항목) |

표의 각 줄은 "왜"와 출처를 갖는다. 표에 없는 차원-능력 쌍은 비교하지 않는다. 즉 비교 범위가 표로 명시된다.

### 8.4 결과 값
각 (범위, 후보) 쌍은 다음 중 하나다.
- `feasible`: 모든 규칙 통과
- `feasible_with_config`: 통과하려면 특정 설정이 필요. 예: Cloud Run은 인스턴스 기반 과금일 때만 A4(응답 후 작업) 통과. 필요한 설정을 `requires_config[]`로 남기고 S5가 반드시 명시한다
- `infeasible`: 하나 이상의 위반. 위반마다 `{rule, dimension, required, capability_key, actual, source}`
- `unknown`: 판정에 필요한 능력 값이 `unknown`. 탈락시키지 않고 순위에서 불이익(§9.4)을 주며 `unverified`에 기록

### 8.5 수준과 무관한 위생 규칙
인증서·도메인 만료, 타임아웃 기본값, N+1 쿼리, 하드코딩된 비밀처럼 어떤 구성을 고르든 문제가 되는 것은 `hygiene` 결과로 따로 낸다. 후보 비교에는 영향이 없고 S5의 변경 항목이 된다.

### 8.6 현재 요청 경로 검사
S1에서 기록한 현재 경로는 S3에서 timing 규칙으로 검사한다. 예: 앱 서버 keep-alive(uvicorn 기본 5초) < LB 유휴 타임아웃(ALB 기본 60초) → 간헐 502. GKE Ingress 백엔드 타임아웃 기본 30초 < 웹소켓 요구(A3) → 연결 끊김. 결과는 `path_checks[]`이고, 위반은 현재 구성 판정(modify)과 S5 변경 항목이 된다.

### 8.7 출력 `fit.json`
`matrix[]`(범위, 후보, 결과, 위반[], requires_config[], unknown_keys[]), `current_assessment[]`(현재 구성 요소별: keep / modify / replace / overprovisioned와 근거), `path_checks[]`(현재 경로별 구간과 위반), `hygiene[]`.

## 9. S4 결정

### 9.1 조합 후보 만들기
범위마다 S3에서 가능(`feasible`, `feasible_with_config`, `unknown`)으로 나온 후보를 모아 아키텍처 후보를 만든다.
- 워크로드마다 다른 컴퓨트를 허용한다. 예: 웹은 Cloud Run, 워커는 GKE. 단, 운영 부담이 늘어나는 만큼 §9.3 비용에 반영된다.
- 조합 폭발을 막기 위해 범위마다 비용 하위 k개(기본 5)만 조합한다. 현재 구성 요소는 가능하면 항상 포함한다.
- 조합마다 아래 범위 사이 제약(§9.2)을 검사한다. 하나라도 위반하면 그 조합은 탈락하고, 탈락 이유는 `cross_scope`로 남는다.

### 9.2 범위 사이 제약
범위 하나만 봐서는 판정할 수 없는 조건이다. 조합이 정해져야 검사할 수 있으므로 S4에서 한다.

| 종류 | 조건 (예) | 근거 능력 |
|---|---|---|
| 공유 가능성 | 데이터 구성 요소가 여러 호스트에서 접근할 수 없는데(SQLite 파일, 컨테이너 로컬 디스크, 프로세스 메모리) 그것을 쓰는 컴퓨트의 최대 인스턴스가 2 이상 → 위반 | `DS.multi_host_access`, `FS.shared_access`, `CA.shared_state`, `CP.scaling` |
| 합산 용량 | Σ(이 저장소를 쓰는 워크로드의 최대 인스턴스 × 인스턴스당 연결 수) ≤ `DS.connections`, 아니면 풀러 필수 / Σ 외부 호출 연결 ≤ NAT 포트 용량 | `DS.connections`, `NW.egress` |
| 연결성 | 컴퓨트에서 사설 데이터로 닿는 수단이 있어야 함(서버리스 → VPC 연결 수단), 리전 일치 | `NW.private_connectivity`, `*.regions` |
| 경로 조립 | 컴퓨트 선택이 경로 구간을 정한다(ECS Express → ALB, GKE Ingress → Classic ALB, 서울 Cloud Run 커스텀 도메인 → 전역 LB + 서버리스 NEG). 조립한 경로 전체에 timing·compare 규칙을 적용 | `NW.*`, `CP.*` |
| 클라우드 혼합 | 서로 다른 클라우드를 섞으면 이그레스 요금과 운영 부담을 더함(위반은 아님) | `NW.egress`, 가격 |
| 플랫폼 결합 | 한 플랫폼 기능이 다른 구성 요소를 전제(예: Supabase Storage → Supabase 프로젝트) | 능력 표의 전제 조건 |

위반은 `{type: cross_scope, rule, scopes[], detail, source}`로 기록한다. 조립한 경로는 후보마다 `paths[]`에 구간 목록으로 남는다.

### 9.3 비용과 부담 계산
| 항목 | 계산 |
|---|---|
| 평시 월 비용 | 구성 요소별 고정비 + 가정한 평시 부하의 변동비. 네트워크 경로 비용(LB 시간 요금, NAT, 이그레스, 퍼블릭 IPv4, CDN) 포함. 가격은 가격 스냅샷(AWS Price List, GCP Billing Catalog) |
| 피크 시간당 비용 | 가정한 피크 부하에서의 시간당 비용 |
| 사용자 1,000명당 월 비용 | 평시 월 비용 / 가정 사용자 수 |
| 사람이 할 단계 수 | 생성 산출물 표의 "자동화 불가 단계" 합 |
| 이전 비용 | 현재 → 후보의 교체 차이 표 항목 수와 데이터 이전 필요 여부 |
| 운영 부담 | 능력 키 `CP.ops_burden` 등. 운영 역량(G2)이 낮으면 가중 |

### 9.4 순위
사전식 순서로 정한다. 설명할 수 있어야 하므로 가중합을 쓰지 않는다.
1. `infeasible`이나 범위 사이 제약 위반이 하나라도 있는 조합은 제외
2. `unknown`이 적은 쪽
3. 평시 월 비용이 낮은 쪽. 단, 차이가 15% 이내면 동률
4. 동률이면 운영 부담이 낮은 쪽
5. 동률이면 사람이 할 단계가 적은 쪽
6. 동률이면 이전 비용이 낮은 쪽

예외: 금전·규제 데이터(C7, F5)의 내구성·가용성 통제는 비용 비교에서 빼지 않는다(원칙 6).

### 9.5 민감도
가정마다 값을 바꿔 가며 S3~S4를 다시 계산해서, 선택이 바뀌는 경계값을 찾는다. 예: "평시 동시 접속이 400을 넘으면 C5가 선택됨". 가정이 많으면 선택에 영향을 준 가정만 계산한다.

### 9.6 시나리오 요약 (파생)
요구 차원에서 시나리오 수준을 파생해 리포트와 검증·관측 범위에 쓴다. 판정에는 쓰지 않는다.
| 요약 | 파생 근거 |
|---|---|
| 재난/장애 D | F1, F2, F3, C7 |
| 트래픽 폭증 T | D3, D2 |
| 무중단 배포 U | F4, C9 |
| 정합성 C | C2, C3, E4 |
| 보안·규제 S | F5 |
| 관측 O | 위 수준의 최댓값에서 파생(O0~O3) |

### 9.7 출력 `plan.json`
`candidates[]`(ID, 범위별 배정, 조립한 경로[], 범위 사이 위반[], 비용{}, unknown 수, 운영 부담, 사람이 할 단계, 이전 비용, 순위), `chosen`, `rejected[]`(ID, 이유[] — 위반 또는 순위 근거), `sensitivity[]`, `scenario_summary{}`, `no_feasible`(가능한 조합이 없을 때 막는 위반 목록).

## 10. S5 변경

선택한 구성과 현재 상태의 차이를 실제 변경으로 만든다.

### 10.1 변경의 종류
| 종류 | 근거 | 예 |
|---|---|---|
| 코드 | 교체 차이 표, 위생 규칙 | SQLite → PostgreSQL 드라이버·방언·타입·비동기 전환, 세션 저장소 교체, 헬스체크·SIGTERM 처리 추가 |
| 산출물 생성 | 생성 산출물 표, 없는 산출물 | Dockerfile, `.dockerignore`, compose(로컬), Terraform, k8s 매니페스트, 플랫폼 설정, CI |
| 산출물 수정·교체 | `current_assessment`, 기존 산출물 판정 기준 | 개발 서버로 실행하는 Dockerfile 교체, 퍼블릭 DB 엔드포인트 차단 |
| 데이터 이전 | 저장소 교체 | 이전 도구 설정, 행 수·체크섬 검증 스크립트 |
| 사람이 할 단계 | 자동화 불가 단계 | 플랫폼 토큰 첫 발급, 도메인 소유 확인 |

### 10.2 규칙
- 변경 하나 = 커밋 하나. 커밋 메시지와 `changes.json`에 근거(위반 ID, 규칙 ID)를 적는다.
- 생성물의 핵심 설정은 기본값에 맡기지 않고 명시한다(원칙 9). `requires_config[]`는 전부 반영해야 한다.
- 생성한 Terraform·매니페스트에는 근거 주석을 단다. 예: `# multi_az: F1(중단 허용 짧음) → rule CMP-DS-011`
- LLM이 코드를 고친 뒤 기존 테스트와 변경별 검사(예: 세션이 Redis에 저장되는지)를 돌린다. 실패하면 그 변경만 되돌리고 실패로 표시한다.
- 데이터 이전은 실행하지 않고 계획과 스크립트만 만든다. 실행은 S7 배포 단계에서 사용자 승인 후 한다.

### 10.3 출력 `changes.json`
`code[]`, `artifacts[]`(경로, action: create / modify / replace / keep, 근거[]), `data_migration[]`, `human_steps[]`, `branch`, `commits[]`.

## 11. S6 정적 검증

| 대상 | 검사 |
|---|---|
| Dockerfile | 이미지 빌드, 컨테이너 실행 후 헬스체크 응답, SIGTERM을 보내고 유예 시간 안에 종료하는지 |
| Terraform | `terraform validate`, `terraform plan`, plan JSON에 대한 단언(Checkov가 다루지 않는 리소스와 속성), Checkov |
| k8s 매니페스트 | `kustomize build` + kubeconform |
| 플랫폼 설정 | 플랫폼 CLI의 검증 명령(있는 경우) |
| 앱 | 기존 테스트, 교체한 저장소의 컨테이너(testcontainers 등)로 통합 테스트 |
| 정적 위험 | Cloud SQL `edition` 누락처럼 `apply`에서만 드러나는 오류의 정적 검사 |

실패하면 실패 내용을 S5에 넘겨 해당 변경을 고친다(최대 3회). 출력 `verify-static.json`: 검사별 결과, 로그 요약, 재시도 횟수.

## 12. S7 동적 검증

"설정이 있다"와 "실제로 견딘다"는 다르다. 그래서 처방한 구성은 세 단계로 확인한다. 그리고 **관측도 필요한 만큼만 한다**는 원칙(§2-5)을 똑같이 적용한다. 아래의 수준은 §9.6에서 파생한 시나리오 요약이다.

### 12.1 세 단계

| 단계 | 언제, 얼마나 | 무엇을 증명하나 |
|---|---|---|
| A. 능동 검증 | 배포 직후, 수십 분 | 시나리오별 필요 수준을 견딘다. 부하와 장애를 일부러 일으켜서 확인한다 |
| B. 소크(soak) | 검증 통과 후, 수준에 따라 2~24시간 | 짧은 테스트에서는 안 보이는 문제가 없다. 메모리 누수, 커넥션 증가, 큐 지연 누적, 디스크 증가, 실제 시간당 비용과 견적의 차이 |
| C. 운영 관측 | 계속 | 실제 트래픽이 가정과 맞는지, 구성이 시간이 지나도 유지되는지 |

부하 없이 배포만 해 두고 "일정 시간 지켜보는 것"은 거의 아무것도 증명하지 못한다. 트래픽이 없으면 문제가 드러나지 않기 때문이다. 그래서 B는 평시 부하 + 주기적 폭증을 계속 걸면서 지켜보는 방식이다.

### 12.2 A. 능동 검증 (시나리오 × 수준)

판정에 쓰인 규칙의 `verify` ID가 가리키는 검증이다. 어느 검증을 얼마나 강하게 할지는 §9.6의 시나리오 요약 수준으로 정하고, 수준이 L0인 시나리오는 검증하지 않는다.

| 시나리오 | 검증 (예) | 통과 기준 (예) |
|---|---|---|
| T | 가정한 피크까지 스텝 부하(L1·L2), 1분 안에 20배 스파이크(L3) | 피크에서 p95 지연 < 1초, 오류율 < 1%, 확장 완료 시간 기록 |
| D | 부하 중 Pod 강제 종료(L1), 노드 하나 drain·DB 페일오버(L2), Redis·DB 차단과 존 하나 격리(L3) | L1: 자동 복구. L2: 페일오버 동안 오류율 < 5%, RTO 가정 이내. L3: 의존성 장애 중 읽기 유지 |
| D | 백업에서 새 인스턴스로 복원 리허설(L1 이상) | 복원 성공, 걸린 시간 ≤ RTO 가정, 데이터 손실 ≤ RPO 가정 |
| U | 부하 중 롤링 배포(L1), 호환 마이그레이션을 포함한 배포와 실패 버전 배포 시 자동 롤백(L2) | 배포 중 5xx 0건(L2), 실패 버전은 자동으로 되돌아감 |
| C | 같은 웹훅 이벤트 재전송·순서 뒤집기(L2), 마지막 1개 재고에 동시 주문 100건(L3) | 중복 처리 0건, 초과 판매 0건, 결제 금액 합 = 주문 금액 합 |

장애 주입 도구: AWS FIS, Chaos Mesh(티어 2 공통). 결과는 `result.json`의 해당 규칙 판정에 붙어서 상태를 "설정 확인"에서 "동작 확인"으로 바꾼다.

### 12.3 B. 소크

- 길이: 필요 수준의 최댓값으로 정한다. 최대 L1이면 2시간, L2면 6시간, L3면 24시간.
- 부하: 가정한 평시 부하 + 1시간마다 피크 폭증.
- 판정: 처음 30분과 마지막 30분의 메모리, DB 커넥션 수, 큐 지연, p95 지연을 비교한다. 추세가 계속 오르면 실패.
- 비용: 소크 동안 사용한 자원을 가격 스냅샷으로 계산해서 견적과 비교한다. 클라우드 청구 데이터는 몇 시간 늦게 나오므로 자원 사용량 기반으로 계산하고, 나중에 청구 데이터로 확인한다.

### 12.4 C. 운영 관측 (필요한 만큼만)

관측 장치 자체도 비용이다. 수준에 따라 설치하는 것이 다르다.

| 최대 필요 수준 | 설치하는 것 |
|---|---|
| L0~L1 | 외부 가용성 확인(업타임 체크) 1개 + 오류율 알림 |
| L2 | + SLO(가용성, p95 지연) + 여러 창·여러 소진율 알림 (S28) + 대시보드 |
| L3 | + 의존성별 상태 지표(DB, 캐시, 큐 길이) + 합성 사용자 시나리오(로그인 → 쓰기 → 읽기) 주기 실행 |

SLO 목표는 필요 수준에서 나온다(예: T L3 → 피크 p95 < 1초, D L2 → 월 가용성 99.9%).

### 12.5 되먹임: 관측이 다시 진단으로

운영 관측은 알림으로 끝나지 않는다. 일정 기간(기본 2주)마다 실측값으로 가정을 바꿔서 진단을 다시 돌린다.

- 실제 평시·피크 동시 접속 → D2·D3 가정 교체 → S3부터 재판정, 견적 재계산
- 실제 CPU·메모리 사용량 → right-sizing 처방(COST-006)
- 가정보다 트래픽이 훨씬 적으면 → 재판정에서 더 싼 후보가 선택되거나 축소 처방 (비용 절감)
- SLO 위반이 반복되면 → 관련 차원 가정 상향 후 재판정

이 되먹임으로 "처음에는 가정으로 설계하고, 운영하면서 실측으로 맞춰간다"는 흐름이 완성된다. 처음부터 정확한 숫자를 요구하지 않는다는 원칙(§2-3)이 여기서 완성된다.

### 12.6 판정 재실행
S7의 실측값(평시·피크 부하에서의 처리량, 자원 사용량, 확장 시간, 페일오버 시간)으로 가정을 교체하고 S3부터 다시 돌린다. 선택이 바뀌면 결과 JSON에 이전 선택과 바뀐 이유를 함께 남긴다.

### 12.7 검증 결과의 유효성
- 부하 생성기 유효성: `dropped_iterations == 0`이고 생성기 CPU < 80%일 때만 판정에 쓴다.
- 운영과 다른 구성(리밋 완화, 축소 오버레이)에서 얻은 결과는 통제 상태를 바꾸지 못한다.
- 관측 통제도 검증한다: 장애를 주입할 때마다 기대한 알림이 몇 분 만에 왔는지 기록한다.

출력 `verify-dynamic.json`: 검증별 결과, 측정값, 유효성 판정, 알림 도착 시간.

## 13. S8 결과와 리포트

### 13.1 result.json
앞 단계 출력을 모아 하나로 만든다(§14). 판정 부분은 결정적이다.

### 13.2 report.html
1. 요약: 선택한 구성, 평시 월 비용, 현재 대비 바뀌는 것, 사람이 할 단계
2. 이렇게 가정했어요: 가정, 근거, 민감도(가정이 틀리면 결론이 바뀌는 지점)
3. **후보 비교표**: 모든 후보 × 범위. 가능 / 설정 필요 / 불가(위반 근거) / 미확인. 면접 시연의 중심
4. **요청 경로표**: 선택한 구성의 경로 구간(DNS → CDN → LB → 앱 서버 → 데이터)과 구간별 OSI 계층, 타임아웃·keep-alive·본문 한도, 경로 규칙 검사 결과
5. 현재 구성 판정: 유지 / 부분 수정 / 교체 / 과잉과 근거
6. 변경 목록: 코드, 산출물, 데이터 이전, 사람이 할 단계
7. 검증 결과
8. 시나리오 요약(D/T/U/C/S/O)
9. 미확인 값과 버린 추론

설명 문장은 LLM이 쓰되 입력은 판정 결과로 고정한다. 출력 검사기가 문장 속 수치·후보·판정이 result.json과 같은지 확인한다.

### 13.3 사용자 조정
저장소 루트의 `infrafit.yaml`(선택)로 가정과 선호를 고칠 수 있다. 조정한 값은 결과에 "사용자 지정"으로 표시한다.
```yaml
assumptions:
  D2.baseline_concurrency: 200
  G1.plan: { vercel: pro }
preferences:
  cloud: aws          # 클라우드 고정
  region: ap-northeast-2
```

## 14. 결과 JSON

스키마 파일: [`schemas/infrafit.schema.json`](../../../schemas/infrafit.schema.json) (JSON Schema 2020-12). 단계 출력은 같은 파일의 `$defs`로 검증한다: `Intake`, `Inventory`, `Profile`, `Fit`, `Plan`, `Changes`, `VerifyStatic`, `VerifyDynamic`, 그리고 최종 `Result`.

`result.json`의 최상위 구조:

| 키 | 내용 |
|---|---|
| `schema_version` | `"1.0"` |
| `run` | 실행 ID, 저장소, 커밋, 실행 범위, 지식 베이스·규칙·가격 스냅샷 버전, 시작·종료 시각 |
| `summary` | 상태(`decided` / `changed` / `verified_static` / `verified_dynamic` / `no_feasible` / `failed`), 선택 후보, 평시 월 비용, 피크 시간당 비용, 불일치 수, 과잉 수, 사람이 할 단계 수 |
| `workloads` | S1 워크로드 |
| `datastores` | S1 저장소 |
| `profile` | S2 도메인, 차원, 가정, 버린 추론 |
| `current_state` | 현재 구성 요소, 기존 산출물, 현재 구성 판정 |
| `fit` | S3 비교 행렬, 위생 결과 |
| `decision` | S4 후보, 선택, 탈락 이유, 민감도, 시나리오 요약 |
| `changes` | S5 변경 |
| `verification` | S6, S7 결과 |
| `unverified` | 판정이나 생성에 쓰인 미확인 값과 그 영향 |
| `errors` | 단계별 오류 |

모든 판정 항목은 근거로 이어진다: 차원 값 → `evidence[]`(파일·줄·인용), 위반 → 규칙 ID와 능력 값의 출처, 변경 → 위반·규칙 ID.

### 14.1 단계 간 일관성 검사
스키마는 형식만 검사한다. 단계 출력끼리 서로를 올바르게 가리키는지는 `infrafit check-run <run-id>`가 따로 검사하고, 단계가 끝날 때마다 자동으로 돈다.
- S2 이후의 모든 범위 ID는 S1의 `workloads`, `datastores`, `request_paths`에 있다.
- `fit.matrix`의 모든 후보 ID는 지식 베이스에 있는 구성 요소다(`provisional` 포함).
- `fit.matrix`는 각 범위에 대해 해당 계열의 후보를 빠짐없이 갖는다(후보 누락 금지, 원칙 8).
- 모든 위반의 `rule`은 규칙집에 있고, `source`는 지식 베이스나 공식 URL을 가리킨다.
- `plan.chosen`은 `plan.candidates`에 있고, 탈락한 후보는 모두 `rejected`에 이유와 함께 있다.
- `plan.candidates`의 배정은 S3에서 그 범위에 가능으로 나온 후보뿐이다.
- `changes`의 모든 항목은 근거(위반 ID나 규칙 ID)를 하나 이상 갖고, `requires_config`는 모두 `explicit_settings`로 반영됐다.
- `result.unverified`는 판정·생성에 쓰인 `unknown` 능력 값을 빠짐없이 담는다.

### 14.2 단계별 예시
`schemas/examples/<픽스처>/<단계>.json`에 단계마다 예시 출력을 둔다. 스키마 테스트와 일관성 검사 테스트의 입력이 되고, 구현 전에 단계 사이 계약을 사람이 읽고 확인하는 용도다.

## 15. 규칙집

### 15.1 형식
```yaml
id: CMP-CP-002
kind: compare
title: 요청 처리 시간이 플랫폼 요청 타임아웃을 넘으면 불가
scope: workload
when:
  dimension: A2
  op: gt
  capability: CP.request_timeout
then: infeasible
why: >
  플랫폼이 요청을 끊으면 사용자는 504를 받고, 작업은 중간에 멈춘다.
tradeoff: >
  긴 작업을 비동기 작업(큐 + 워커)으로 바꾸면 이 제약을 피할 수 있다. 그 경우 A2가 바뀌므로 다시 판정한다.
verify: [V-A2-001]
sources:
  - ref: capabilities/04-compute-tier0.md#vercel-pro
  - ref: capabilities/05-compute-tier1-2.md#cloud-run
```

```yaml
id: CAP-DS-001
kind: capacity
title: 최대 인스턴스 × 풀 크기가 DB 최대 연결 수를 넘으면 풀러 필요
scope: datastore
when:
  sum_over: workloads_using_this_datastore
  value: max_instances * pool_size
  op: gt
  capability: DS.connections
then: { feasible_with_config: [connection_pooler] }
why: >
  확장이 최대에 이르면 연결이 거부되어 오류가 나고, 연결마다 DB 메모리를 쓴다.
verify: [V-C8-001]
sources:
  - ref: capabilities/01-sql-databases.md
```

### 15.2 ID 체계
`{종류}-{계열}-{번호}`. 종류는 `CMP`(compare), `CAP`(capacity), `TIM`(timing), `CMB`(combination), `OVR`(overprovision), `HYG`(위생), `COST`(비용 함정·반대 방향 규칙).

### 15.3 원칙
- 모든 규칙은 지식 베이스의 능력 값(출처 포함)이나 공식 1차 자료를 인용한다. 설계 원칙에서 직접 나온 규칙만 예외이고, 출처 칸에 원칙 번호를 적는다.
- 모든 규칙은 `verify`에 검증 ID를 하나 이상 갖는다. 검증 방법이 없으면 "설정이 있다"만 확인할 수 있고 "동작한다"는 보장할 수 없기 때문이다.
- 지름길 규칙(능력 비교 없이 특정 후보로 보내는 규칙)은 lint에서 거부한다.
- `infrafit rules lint`가 형식, 출처, 확인 날짜, `verify` 유무를 검사한다.
- `infrafit explain <규칙 ID>`는 규칙 하나를 사람용으로 출력한다(면접 시연용).

## 16. 오류 처리

| 상황 | 동작 |
|---|---|
| 1차 지원 밖 언어 | 탐지는 manifest·인프라 파일까지, 코드 수준 차원은 추론(medium). 결과에 표시 |
| 저장소가 큼 | 제외 경로 적용 후 진행, 제외 목록 기록 |
| LLM 실패 | 탐지 결과와 가정만으로 S2를 끝내고 결과에 "추론 없이 생성됨" 표시. S5는 LLM 없이 할 수 있는 산출물 생성만 |
| 근거 검사 실패 | 해당 추론만 버림 |
| 파서 실패 | 해당 파일을 텍스트 패턴 탐지로 낮추고 신뢰도 medium |
| 능력 값 미확인 | `unknown` 결과, 순위 불이익, `unverified`에 기록 |
| 가능한 조합 없음 | `no_feasible`에 막는 위반을 모아 내고, "요구를 바꾸면 가능한 것"(예: 긴 요청을 비동기로 바꾸기)을 제안 |
| 가격 API 실패 | 마지막 가격 스냅샷 사용, 날짜 표시 |
| S6 반복 실패 | 실패한 변경과 로그를 결과에 남기고 그 변경은 브랜치에서 제외 |

## 17. 테스트

### 17.1 픽스처 저장소
`fixtures/` 아래에 두고, 각각 **단계별 기대 JSON**(골든)을 가진다.

| 픽스처 | 내용 | 기대 결과 (핵심) |
|---|---|---|
| F1 `simple-web-app` | 기존 저장소 스냅샷(커밋 고정) | 워크로드 5개 + 마이그레이션 Job. 큐 워커(A1) + 큐 길이 기반 확장 요구 때문에 Lambda·단일 VM은 위반. 후보 비교표에 모든 컴퓨트가 나옴 |
| F2 `sqlite-erp` | 업무용 시스템: Flask 또는 Express + SQLite(WAL) + `gunicorn -w 4` + `database is locked` 재시도 + 결재·부서 테이블 | C1 = high(근거 세 종류 모두). `ds:local/sqlite/wal` 현재 판정 = replace. PostgreSQL 계열 선택. S5에 드라이버·방언·타입·경쟁 조건 처방 |
| F3 `vibe-shop` | Next.js + SQLite + 인메모리 세션 + 로컬 업로드 + Stripe 웹훅(중복 처리 없음) + 재고 차감(잠금 없음) | B1·B2 위반, C2·C3·E4 처방, Dockerfile·Terraform 생성 |
| F4 `overbuilt-internal` | 사내 도구인데 EKS + 3개 존 NAT + Multi-AZ RDS + 멀티 리전 | 현재 구성 = overprovisioned. 더 싼 후보 선택 |
| F5 `small-blog` | Next.js + Supabase on Vercel, 정적 위주 | 현재 구성 = keep. 변경 없음(위생 항목만) |
| F6 `long-jobs` | Vercel에서 10분짜리 엑셀 생성 + 응답 후 메일 발송 | A2·A4 위반으로 Vercel 불가, Cloud Run은 인스턴스 기반 과금 설정 필요 |

F2~F6은 이 저장소 안에서 만든다.

### 17.2 테스트 종류
- 스키마 테스트: 모든 단계 출력과 `schemas/examples/`가 스키마를 통과
- 일관성 테스트: §14.1 검사가 정상 예시는 통과시키고, 일부러 깨뜨린 예시(범위 ID 누락, 후보 누락, 근거 없는 변경)는 잡아냄
- 경로 테스트: 앱 서버 keep-alive < LB 유휴 타임아웃 같은 경로 규칙이 픽스처에서 잡힘
- 결정성 테스트: `--no-llm`으로 S0~S4를 두 번 돌려 출력이 바이트 단위로 같음
- 골든 테스트: 픽스처 × 단계별 기대 JSON과 비교(시각·실행 ID 제외)
- 규칙 단위 테스트: 규칙마다 걸리는 경우와 안 걸리는 경우
- 탐지기 테스트: semgrep `--test`, 파서별 pytest
- 추론 평가: 픽스처마다 5회 실행해서 도메인 일치(5/5), 근거 검사 통과율(90% 이상), 주요 차원 값 일치율 기록
- 생성 검증: F2·F3의 S5 결과가 S6을 통과

## 18. 구현 순서

| 단계 | 범위 | 완료 기준 |
|---|---|---|
| M1 | 지식 베이스 변환(dimensions, components, artifacts, 네트워크의 YAML화), 요구 조건 변환표, 기본값 표, 스키마와 단계별 예시, 일관성 검사기, S0·S1(요청 경로 포함) | F1~F6 인벤토리 골든 통과, 단계별 예시가 스키마·일관성 검사 통과 |
| M2 | S2(탐지기 + 추론 + 가정), S3, S4 | F2(SQLite)가 replace → PostgreSQL로 결정되고 후보 비교표에 모든 컴퓨트가 근거와 함께 나옴 |
| M3 | 교체 차이 표, S5, S6 | F2의 코드 변경 + Dockerfile + Terraform이 S6 통과 |
| M4 | S7(배포, 부하·장애·소크, 판정 재실행) | F1을 실제 클라우드에 배포해 검증 결과가 result.json에 들어감 |
| M5 | S8 리포트, 웹 UI(GitHub URL 입력 → 결과) | 면접 시연 흐름 완성 |

## 19. 기술 스택과 디렉터리

- Python 3.12, uv, pydantic v2(스키마 생성과 검증), jsonschema, semgrep(OSS CLI), python-hcl2, PyYAML, kustomize, kubeconform, Checkov, Jinja2, pytest, testcontainers
- LLM: Claude Agent SDK(Python). 모델과 SDK 사용법은 구현 계획 단계에서 claude-api 레퍼런스로 확정한다.

```
one-click-deploy-agent/
  infrafit/
    cli.py
    stages/            s0_intake.py … s8_result.py   (단계 하나 = 모듈 하나)
    detect/            탐지기 (manifest, entrypoint, semgrep/, schema, config, infra, repo)
    infer/             Agent SDK 추론, 프롬프트, 근거 검사기
    engine/            규칙 해석기 (compare, capacity, timing, combination, overprovision, hygiene)
    decide/            조합 생성, 비용, 순위, 민감도
    generate/          코드 변경, 산출물 생성
    verify/            정적·동적 검증 실행기
    pricing/           가격 API 클라이언트, 스냅샷
    report/            result.json 조립, report.html, 설명 검사기
  knowledge/           dimensions.yaml, components/, artifacts/, swaps/, defaults.yaml, assumptions.yaml
  rules/               *.yaml
  schemas/             infrafit.schema.json
  prices/              가격 스냅샷
  fixtures/            F1~F6 + 단계별 골든 JSON
  tests/
  docs/
    research/          사람용 지식 베이스 원본
    superpowers/specs/
```

## 20. 출처 목록

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
| S28 | SLO 알림 | 여러 창(window)·여러 소진율(burn rate) 알림 권장: 1시간 창 14.4배(예산 2%) 페이지, 6시간 창 6배(5%) 페이지, 3일 창 1배(10%) 티켓 | https://sre.google/workbook/alerting-on-slos/ |
| S27 | Vercel Functions | 최대 실행 시간 Hobby 300초, Pro·Enterprise 800초(1800초 베타), 요청·응답 본문 4.5MB 제한 | https://vercel.com/docs/functions/limitations |

가격과 한도 수치는 이 날짜 기준이다. 실제 판정에서는 §9.3의 가격 스냅샷 값을 쓰고, 이 표는 규칙의 근거 설명에만 쓴다.
