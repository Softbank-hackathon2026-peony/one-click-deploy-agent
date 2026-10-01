# 구성 요소 능력 표

- 작성일: 2026-10-01
- 짝 문서: [../dimensions.md](../dimensions.md) (앱 특성 차원 = 요구 쪽)

## 0. 역할

판정 = 앱 특성 프로필(요구) × 구성 요소 능력(이 표). 요구가 능력을 넘으면 교체, 능력이 요구보다 훨씬 크면 축소다.
모든 구성 요소는 **아래 능력 키로만** 기술한다. 그래야 기계적으로 비교할 수 있다.

### 표에 없는 구성 요소
표는 자주 나오는 구성 요소를 빠르고 정확하게 처리하기 위한 것이다. 표에 없는 구성 요소를 만나면, 에이전트가 같은 능력 키로 공식 문서를 찾아 프로필을 채운다(출처 인용 필수, 근거 검사 통과 필수). 결과는 캐시하고, 사람이 검토하면 표에 추가한다.

## 1. 기술 형식

구성 요소마다 아래 형식을 쓴다.

```
## <구성 요소> — <변형/플랜> (예: PostgreSQL — Amazon RDS, Multi-AZ 인스턴스)
- 계열: 저장소-관계형 / 저장소-문서 / 캐시 / 큐 / 스케줄러 / 실시간 / 파일 저장소 / 컴퓨트-티어0 / 컴퓨트-티어1 / 컴퓨트-티어2
- 서울 리전: 있음 / 없음 / 일부 (근거)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 다수 | 행 단위 잠금 | https://… "…" |

### 비용 구조
최소 월 고정비(서울 우선, 없으면 리전 명시), 변동 단위, 무료 등급, 과금 함정.

### 교체 계열 정보
코드를 바꿀 때 필요한 정보: API 형태(동기/비동기, 언어별 대표 클라이언트), 질의 언어·방언, 일관성 모델, 같은 계열로 갈아탈 때 이식되는 것과 안 되는 것.

### 함정
문서에 있는 기본값이나 제약 중 판정을 뒤집는 것.
```

값을 확인하지 못하면 `미확인`이라고 쓴다. 지어내지 않는다. 해당 없는 키는 `해당 없음`.

## 2. 능력 키

괄호 안은 [dimensions.md](../dimensions.md)의 대응 차원이다.

### 2.1 저장소 (DS) — 관계형, 문서, 키-값, BaaS DB

| 키 | 뜻 |
|---|---|
| DS.concurrent_writers | 동시에 쓸 수 있는 주체 수와 잠금 단위 (C1) |
| DS.row_contention | 행 잠금, 원자적 갱신(`x = x + 1`), 낙관적 동시성 지원 (C2) |
| DS.transactions | 트랜잭션 범위(단일 행/다중 행/다중 테이블·문서), 격리 수준, 제약 (C3) |
| DS.replication | 복제 방식(동기/비동기), 읽기 복제본, 쓰기 후 읽기 보장 (C3, C4) |
| DS.query_models | 지원하는 질의: 조인, 전문 검색, 지리, 벡터, JSON, 시계열 (C5) |
| DS.size_limits | 저장 용량, 행·문서·항목 크기 한도, 플랜 한도 (C6) |
| DS.backup | 자동 백업 여부, 주기, 보존 기간, PITR 단위와 최악 RPO (C7, F3) |
| DS.connections | 최대 연결 수(기본값과 결정 방식), 내장·제공 풀러 (C8) |
| DS.schema_change | 스키마 변경 시 잠금 동작, 온라인 변경 수단 (C9) |
| DS.availability | 고가용성 구성, 자동 페일오버, 페일오버 시간, 존·리전 범위 (F1, F2) |
| DS.multi_host_access | 여러 앱 인스턴스·호스트에서 동시에 접근 가능한가, 접근 방식(네트워크/파일) (B2) |
| DS.security | 저장 암호화, 감사 로그, 네트워크 격리, 행 수준 권한 (F5) |
| DS.regions | 서울 리전 등 제공 지역 (D5) |
| DS.scaling | 수직·수평 확장 방식, 확장 중 중단 여부 (D2, D3) |
| DS.cost_floor | 최소 월 고정비, scale-to-zero 여부 (G3) |

### 2.2 캐시·키-값 (CA)

| 키 | 뜻 |
|---|---|
| CA.persistence | 영속성(없음/스냅샷/로그), 재시작 시 데이터 |
| CA.eviction | 메모리 가득 시 동작(퇴출 정책 기본값) |
| CA.consistency | 복제 방식, 페일오버 시 유실 가능성 |
| CA.shared_state | 세션·락·레이트 리밋 저장소로 쓸 수 있는가 (B1, B4) |
| CA.pubsub | pub/sub·스트림 지원 (B4) |
| CA.availability | HA, 페일오버, 존 범위 |
| CA.connections | 연결 수 한도, 서버리스에서 연결 방식(HTTP 등) |
| CA.limits | 메모리·키·값 크기 한도, 처리량 한도 |
| CA.regions / CA.cost_floor | 지역, 최소 고정비 |

### 2.3 큐·스트림·작업 (QU)

| 키 | 뜻 |
|---|---|
| QU.delivery | 전달 보장(최소 1회/최대 1회/정확히 1회의 조건) (C3, E4) |
| QU.ordering | 순서 보장 범위 |
| QU.dedup | 중복 제거 수단과 기간 |
| QU.retention | 메시지 보존 기간, 최대 메시지 크기 |
| QU.retry_dlq | 재시도, 가시성 타임아웃, DLQ |
| QU.throughput | 처리량 한도 |
| QU.consumer_scaling | 큐 길이 기반 확장과의 연동 |
| QU.availability / QU.regions / QU.cost_floor | 가용성, 지역, 최소 고정비 |

### 2.4 스케줄러 (SC)

| 키 | 뜻 |
|---|---|
| SC.frequency | 최소 주기, 플랜별 제한 (B3) |
| SC.semantics | 중복 실행·누락 가능성, 재시도 (B3) |
| SC.target | 실행 대상(HTTP, 컨테이너 작업, 함수)과 최대 실행 시간 |
| SC.cost_floor | 비용 |

### 2.5 실시간 연결 (RT)

| 키 | 뜻 |
|---|---|
| RT.connections | 동시 연결 한도 (A3) |
| RT.fanout | 인스턴스 간 메시지 전파 방식 (B4) |
| RT.limits | 메시지 크기·빈도 한도, 연결 지속 한도 |
| RT.cost_floor | 비용 구조 |

### 2.6 파일 저장소 (FS)

| 키 | 뜻 |
|---|---|
| FS.durability | 내구성, 복제 범위 (C7) |
| FS.consistency | 쓰기 후 읽기 일관성 |
| FS.shared_access | 여러 인스턴스에서 접근 가능한가 (B2) |
| FS.object_limits | 객체·업로드 크기 한도, 업로드 방식(서명 URL, 멀티파트) (A7) |
| FS.versioning_lifecycle | 버전 관리, 수명 주기, 삭제 보호 |
| FS.delivery | CDN 연동, 이그레스 비용 |
| FS.regions / FS.cost_floor | 지역, 비용 |

### 2.7 컴퓨트 (CP) — 티어 0·1·2 공통

| 키 | 뜻 |
|---|---|
| CP.process_types | 웹 / 상시 워커 / 정기 작업 / 장시간 연결 지원 (A1) |
| CP.request_timeout | 최대 요청 처리 시간, LB 유휴 타임아웃 (A2) |
| CP.long_connection | 웹소켓·SSE 지원과 지속 한도 (A3) |
| CP.cpu_outside_request | 응답 후·요청 밖에서 CPU가 주어지는가 (A4) |
| CP.cold_start | 콜드 스타트, 최소 인스턴스, scale-to-zero (A5) |
| CP.instance_size | 인스턴스당 최대 CPU·메모리, GPU(서울 여부) (A6) |
| CP.request_size | 요청·응답 본문 한도 (A7) |
| CP.local_disk | 로컬 디스크 성격(임시/영속), 크기, 영속 볼륨 부착 가능 여부와 그때의 제약 (B2) |
| CP.scaling | 최대 인스턴스, 확장 신호, 확장 속도 (D2, D3) |
| CP.concurrency | 인스턴스당 동시 요청 처리 |
| CP.shutdown | 종료 신호와 유예 시간 (F4) |
| CP.deploy | 무중단 배포 방식, 롤백, 트래픽 분할 (F4) |
| CP.availability | 멀티 존 배치, 리전 장애 대비 (F1, F2) |
| CP.networking | DB로의 사설 연결, 고정 출구 IP (F5, E1) |
| CP.regions | 서울 리전 (D5) |
| CP.plan_limits | 플랜별 제약(상업 이용, 크론 빈도, 실행 시간 등) (G1) |
| CP.ops_burden | 운영해야 하는 것(노드, 업그레이드, 네트워크) (G2) |
| CP.cost_floor | 최소 월 고정비, 과금 단위 (G3) |

## 3. 파일

| 파일 | 계열 |
|---|---|
| [01-sql-databases.md](01-sql-databases.md) | 관계형 DB |
| [02-nosql-baas.md](02-nosql-baas.md) | 문서·키-값·BaaS DB |
| [03-cache-queue-scheduler-realtime-storage.md](03-cache-queue-scheduler-realtime-storage.md) | 캐시, 큐, 스케줄러, 실시간, 파일 저장소 |
| [04-compute-tier0.md](04-compute-tier0.md) | 컴퓨트 티어 0 (PaaS·서버리스 플랫폼) |
| [05-compute-tier1-2.md](05-compute-tier1-2.md) | 컴퓨트 티어 1·2 (관리형 컨테이너, 함수, 쿠버네티스) |

## 4. 조사 결과 (2026-10-01)

| 파일 | 구성 요소 수 | 비고 |
|---|---|---|
| 01-sql-databases.md | 23 | SQLite(기본·WAL), libSQL·Turso, LiteFS, PostgreSQL 13종(자체 운영, RDS 3종, Aurora 2종, Cloud SQL 2종, AlloyDB, Supabase 2종, Neon 2종, PlanetScale Postgres, Prisma Postgres), MySQL 4종. §5에 드라이버·ORM·방언 차이·이전 도구(교체 차이 표 재료) |
| 02-nosql-baas.md | 16 | Firestore 2종, Realtime Database, Supabase, DynamoDB 2종, Atlas 2종, DocumentDB, Spanner, Bigtable, Appwrite, PocketBase, Convex, pgvector, Pinecone |
| 03-cache-queue-scheduler-realtime-storage.md | 58 | 교체 전 출발점 4(프로세스 메모리, 앱 안 작업 큐, 로컬 디스크, 앱 안 스케줄러), 캐시 12, 큐 17, 스케줄러 7, 실시간 9, 파일 저장소 9 |
| 04-compute-tier0.md | 29 | Vercel 4, Netlify 3, Cloudflare 4, Railway 3, Render 2, Fly.io, Firebase 2, Supabase Edge 2, Replit 3, Heroku 2, DigitalOcean, Koyeb 2. 생성 도구(v0, Lovable, Bolt, AI Studio)의 기본 배포 대상 포함 |
| 05-compute-tier1-2.md | 22 | Cloud Run(과금 모드별), ECS Fargate·Express Mode·Spot, App Runner, Lambda, Cloud Run functions, Azure Container Apps, GKE Autopilot·Standard, EKS(노드 그룹, Karpenter, Auto Mode, Fargate), 경량 k8s, 단일 VM + compose |

- 합계 **148개 구성 요소**.
- 값을 확인하지 못한 칸은 `미확인`, 공식 페이지끼리 값이 다르면 `[충돌]`로 표시했다. 규칙으로 옮기기 전에 판정에 쓰이는 미확인·충돌 값부터 다시 확인한다.
- 일부 가격은 공식 Price List 파일(AWS)이나 공식 가격 페이지 원문(GCP)을 curl로 받아 읽었다. GCP 서울 가격 중 일부는 us-central1 값이며 파일에 표시했다.
- 아직 없는 것: 구성 요소별 **생성 산출물**(Terraform 리소스, 핵심 속성, 앱 쪽 계약, 로컬 개발 대응, 검증 명령). 별도 파일로 채운다.
