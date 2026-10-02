# 구성 요소 능력 표 — 01. 관계형 DB

삭제된 절: 3.4 MySQL — PlanetScale Vitess, 사유: 부적격 출처 (2026-10-02. 부적격 출처에 기댄 표 행과 줄도 지웠다. 남은 절 번호는 그대로)

- 작성일: 2026-10-01
- 형식·능력 키: [README.md](README.md) §1, §2.1 (DS.* 15개)
- 요구 쪽: [../dimensions.md](../dimensions.md) (C1~C9, B2, D2·D3·D5, F1~F5, G3)
- 범위: SQLite(롤백 저널 / WAL), libSQL·Turso, LiteFS, PostgreSQL(자체 운영, RDS 3종, Aurora 2종, Cloud SQL 2종, AlloyDB, Supabase, Neon, PlanetScale Postgres, Prisma Postgres), MySQL(RDS, Aurora, Cloud SQL, PlanetScale Vitess), Vercel 마켓플레이스 현황
- 출처 규칙: 모든 출처는 2026-10-01에 직접 연 페이지다. 인용은 원문(영어) 그대로 짧게 옮겼다. 확인 못 한 값은 `미확인`.
  - sqlite.org는 이 작업 환경에서 IPv6 주소만 응답해 접속이 안 되었고, 공식 미러 `www3.sqlite.org`에서 같은 경로의 페이지를 열었다. 표에는 정식 URL(`www.sqlite.org`)로 적는다.
  - cloud.google.com 문서는 `docs.cloud.google.com`으로 리디렉션된다. 둘 다 같은 페이지다.
  - [PL] = AWS Price List 공개 오퍼 파일 `https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonRDS/current/ap-northeast-2/index.json` (publicationDate 2026-10-01T06:02:30Z). 월 금액은 시간 단가 × 730시간으로 계산했다.
  - GCP 가격 페이지는 기본 표시 리전(us-central1, Iowa)만 정적 HTML에 들어 있어 **서울(asia-northeast3) 단가는 미확인**이다. GCP 금액은 모두 us-central1 값이다.

## 목차

0. [요약 비교표](#0-요약-비교표)
1. [SQLite 계열](#1-sqlite-계열)
   - 1.1 SQLite — 기본(롤백 저널) · 1.2 SQLite — WAL · 1.3 libSQL·Turso Cloud · 1.4 LiteFS
2. [PostgreSQL](#2-postgresql)
   - 2.1 자체 운영 · 2.2 RDS Single-AZ · 2.3 RDS Multi-AZ 인스턴스 · 2.4 RDS Multi-AZ DB 클러스터 · 2.5 Aurora PG 프로비저닝 · 2.6 Aurora PG Serverless v2 · 2.7 Cloud SQL 단일 · 2.8 Cloud SQL HA · 2.9 AlloyDB · 2.10 Supabase Free · 2.11 Supabase Pro/Team · 2.12 Neon Free · 2.13 Neon Launch/Scale · 2.14 PlanetScale Postgres · 2.15 Prisma Postgres
3. [MySQL](#3-mysql)
   - 3.1 RDS for MySQL · 3.2 Aurora MySQL · 3.3 Cloud SQL for MySQL · 3.4 PlanetScale Vitess(삭제됨)
4. [Vercel 마켓플레이스 현황](#4-vercel-마켓플레이스-현황)
5. [교체 계열 정보 (공통 재료)](#5-교체-계열-정보-공통-재료)
   - 5.1 엔진 기준값 · 5.2 드라이버 · 5.3 ORM · 5.4 SQL 방언 차이 · 5.5 데이터 이전 도구
6. [판정을 뒤집는 발견](#6-판정을-뒤집는-발견)

---

## 0. 요약 비교표

값의 근거는 각 절의 표에 있다. "최악 RPO"는 같은 리전·같은 존 장애가 아닌 **논리적 손상(잘못된 쓰기·삭제)에서 백업/PITR로 되돌릴 때** 잃을 수 있는 최대 구간이다. 존 장애에서의 RPO는 "복제·HA" 열을 본다.

| 구성 요소 | 동시 쓰기 (C1) | 여러 호스트 접근 (B2) | 최대 연결 기본값 (C8) | 복제·HA (F1, C3) | 페일오버 시간 | 최악 RPO (F3) | 서울 (D5) | 최소 월 고정비 (G3, 서울 우선) | 플랜 함정 |
|---|---|---|---|---|---|---|---|---|---|
| SQLite 롤백 저널 | 1 (파일 단위 EXCLUSIVE 잠금, 쓰는 동안 읽기도 막힘) | 불가 (같은 호스트 프로세스만) | 해당 없음 (파일) | 없음 | 해당 없음 | 백업 수단을 따로 두지 않으면 무한 | 해당 없음 | 0 (앱 호스트 디스크) | 다중 인스턴스면 DB가 갈라짐 |
| SQLite WAL | 1 (읽기·쓰기 동시 가능) | 불가 ("same host computer", 네트워크 FS 불가) | 해당 없음 | 없음 | 해당 없음 | 위와 같음 | 해당 없음 | 0 | 위와 같음 + 체크포인트 기아로 WAL 무한 증가 |
| libSQL·Turso Cloud | 1 (기본). `BEGIN CONCURRENT`(MVCC)는 2026-08 조기 미리보기 | 가능 (HTTP/WebSocket 원격, 임베디드 복제본) | 미확인 | S3 Express One Zone에 커밋 후 응답 | 미확인 | PITR 창: Free 1일 / Dev 10일 / Scaler 30일 (RPO 수치 미확인) | 없음 (가장 가까운 곳 도쿄) | $0 (Free) / $4.99 (Developer) | Seoul 없음 |
| LiteFS | 1 (주 노드 1개만) | 읽기는 전 노드, 쓰기는 주 노드로 전달 | 해당 없음 | 비동기 복제, Consul 리스 | 미확인 | 페일오버 때 미복제 쓰기 유실 가능 + 백업 직접 구성 | 미확인 | 노드 비용만 | LiteFS Cloud(백업) 2024-10-15 종료, pre-1.0 |
| PostgreSQL 자체 운영 | 다수 (행 잠금, MVCC) | 가능 (네트워크) | 100 (재시작해야 변경) | 스트리밍 복제 기본 비동기, 자동 페일오버 없음 | 직접 구성 (Patroni 등) | `archive_timeout`·백업 설계에 따름 | 호스트에 따름 | VM 비용 | 백업·HA를 직접 만들어야 함 |
| RDS PG Single-AZ | 다수 | 가능 | `LEAST(메모리/9531392, 5000)` (t4g.micro 112 미만) | 없음 (읽기 복제본은 비동기) | 인스턴스 장애 시 복구 대기 (수치 미확인) | 5분 (로그 업로드 주기) | 있음 | **$20.9** (t4g.micro $18.25 + gp3 20GB $2.62) | API·CLI 생성 시 백업 보존 1일 |
| RDS PG Multi-AZ 인스턴스 | 다수 | 가능 | 위와 같음 | 동기 대기 복제본 1개 (읽기 불가) | 60~120초 | 존 장애 0 / 논리 손상 5분 | 있음 | **$42.5** (t4g.micro $37.23 + gp3 20GB $5.24) | 대기 복제본으로 읽기 분산 불가 |
| RDS PG Multi-AZ DB 클러스터 | 다수 | 가능 | 위와 같음 | 반동기 (리더 1개 이상 확인), 읽기 가능 리더 2개 | 35초 미만 | 존 장애 0 / 논리 손상 5분 | 있음 | **$579.5** (m6gd.large 3노드 $571.6 + gp3 20GB $7.86) | 인스턴스 클래스 제한 (t 계열 없음, 서울 최저 m6gd.large) |
| Aurora PG 프로비저닝 | 다수 (쓰기 인스턴스 1개) | 가능 | `LEAST(메모리/9531392, 5000)` | 스토리지 3AZ 6사본 동기, 복제본 최대 15 | 복제본 있으면 60초 미만 (흔히 30초 미만), 없으면 10분 미만 | 존 장애 0 / 논리 손상 미확인 (연속 백업) | 있음 | **$82.5+** (t4g.medium $0.113/h, 스토리지 $0.12/GB·I/O 별도) | I/O 과금 (Standard) |
| Aurora PG Serverless v2 | 다수 (쓰기 1) | 가능 | 최대 ACU로 결정 (1ACU 189 … 32ACU 이상 5,000), 최소 0·0.5ACU면 최대 2,000 | 위와 같음 | 위와 같음 + 일시정지 재개 약 15초 (24시간 넘으면 30초 이상) | 위와 같음 | 있음 | **0 ACU면 스토리지만** / 0.5 ACU 상시면 $73 | RDS Proxy·열린 연결이 있으면 일시정지 안 됨 |
| Cloud SQL PG 단일 | 다수 | 가능 | 메모리별 25 / 50 / 100 / 200 / 400 … 1,000 | 없음 | 존 장애 시 복구 대기 | PITR 로그 보존 Enterprise 7일 / Plus 35일 (RPO 수치 미확인) | 있음 | **$7.7+** (db-f1-micro, us-central1, SLA 제외) / 전용 1vCPU 3.75GB 약 $49.3 | 공유 코어는 SLA 제외 |
| Cloud SQL PG HA | 다수 | 가능 | 위와 같음 | 두 존 디스크 동기 복제 (대기 읽기 불가) | 약 60초 (Enterprise Plus 계획 작업 1초 미만) | 존 장애 0 | 있음 | 단일의 2배 (f1-micro HA $15.3, us-central1) | 커넥터 사용 시 Cloud Run 인스턴스당 100 연결 |
| AlloyDB | 다수 (주 인스턴스 1) | 가능 | 인스턴스 크기별 기본 100~1,000 | HA 기본: 두 존 노드 + 리전 로그 동기 기록 | 약 60초 (PG18 핫 스탠바이 신규 약 15초) | 존 장애 0 / PITR 마이크로초 단위, 기본 14일 | 있음 | **약 $113.6** (c4a-highmem-1 단일 노드, us-central1) / HA 약 $227 | 30일 무료 체험 후 과금 |
| Supabase Free | 다수 (PostgreSQL) | 가능 | 직접 60 / 풀러 200 (Nano) | 없음 | 해당 없음 | **백업 없음** | 있음 (ap-northeast-2) | $0 | **1주 비활성 시 일시정지**, 500MB |
| Supabase Pro/Team | 다수 | 가능 | Micro 60/200, Small 90/400, Medium 120/600 … | 읽기 복제본 비동기. 관리형 HA는 미확인 | 미확인 | 일일 백업 24시간 / PITR 애드온 2분 | 있음 | **$25** (Pro, Micro 크레딧 포함) / PITR 쓰면 약 $130 | 컴퓨트 변경 시 2분 미만 중단, 지출 상한이 컴퓨트·PITR 미포함 |
| Neon Free | 다수 | 가능 | 0.25CU 104 … / 풀러 10,000 클라이언트 | 핫 스탠바이 없음, WAL은 다중 AZ 세이프키퍼 | 컴퓨트 재스케줄 수초~2분, AZ 장애 1~10분 | 복원 창 6시간 (1GB 한도) | **없음** (싱가포르가 가장 가까움) | $0 | 5분 뒤 scale-to-zero 고정, 0.5GB/프로젝트 |
| Neon Launch/Scale | 다수 | 가능 | 위와 같음, 9CU 이상 4,000 상한 | 위와 같음 | 위와 같음 | 복원 창 Launch 7일 / Scale 30일 | 없음 | 사용량제. 0.25CU 상시면 Launch 약 $19.3 | 서울 없음 → 대륙 간 지연 |
| PlanetScale Postgres | 다수 | 가능 | 미확인 (PgBouncer 6432 제공) | HA: 주 1 + 복제본 2, 3AZ, 복제본 1개 이상 확인 후 커밋 | 미확인 (검색 요약은 30초 미만, 원문 미확인) | PITR 기본 2일 창, 현재 5분 전까지 | 있음 (GCP asia-northeast3) | $5 (PS-5 단일 노드) / HA $15 (us-east-1 가격) | 무료 플랜 없음, 단일 노드는 HA 없음 ⚠️근거없음 |
| Prisma Postgres | 다수 (PG17) | 가능 (TCP·HTTP) | 풀 연결 Starter 100 / Pro 500 / Business 1,000 | 미확인 | 미확인 | 일일 스냅샷 7일 (Business 30일), Free 백업 없음 | 없음 (도쿄 ap-northeast-1) | $0 (Free) / $10 (Starter) | `npx create-db` DB는 24시간 뒤 삭제 |
| RDS MySQL | 다수 (InnoDB 행 잠금) | 가능 | `메모리/12582880` (t3.micro 약 60) | Single / Multi-AZ 동기 / 클러스터 반동기 | 60~120초 / 클러스터 35초 미만 | 5분 | 있음 | $20.9 (t4g.micro, 8.4 기준) | **8.0은 2026-08-01부터 확장 지원 요금 (t4g.micro 2vCPU면 +$175/월)** |
| Aurora MySQL | 다수 (쓰기 1) | 가능 | 클래스별 표 (t4g.medium 90, r6g.large 1,000), 최대 16,000 | Aurora PG와 같음 | Aurora PG와 같음 | 미확인 (Backtrack 별도) | 있음 | $82.5+ (t4g.medium) | |
| Cloud SQL MySQL | 다수 | 가능 | 메모리 기반 (수치 미확인) | HA 동기 | 약 60초 | Cloud SQL PG와 같음 | 있음 | Cloud SQL PG와 같음 | |

---

## 1. SQLite 계열

### 1.1 SQLite — 기본(롤백 저널 모드)
- 계열: 저장소-관계형 (임베디드, 파일)
- 서울 리전: 해당 없음 (앱이 도는 호스트의 디스크에 있음)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | **1** (DB 파일 전체 잠금). 커밋 중에는 읽기도 막힘 | 잠금 단위 = 데이터베이스 파일 | https://www.sqlite.org/whentouse.html "it will only allow one writer at any instant in time" · https://www.sqlite.org/lockingv3.html "Only one EXCLUSIVE lock is allowed on the file and no other locks of any kind are allowed to coexist with an EXCLUSIVE lock." · 2026-10-01 |
| DS.transactions | 다중 행·다중 테이블 트랜잭션, **SERIALIZABLE** (쓰기를 실제로 직렬화). 기본 `DEFERRED`, `IMMEDIATE`로 시작 시 바로 쓰기 잠금 | `busy_timeout`이 지나면 `SQLITE_BUSY` | https://www.sqlite.org/isolation.html "SQLite implements serializable transactions by actually serializing the writes." · https://www.sqlite.org/lang_transaction.html "The default transaction behavior is DEFERRED." · https://www.sqlite.org/c3ref/busy_timeout.html "After at least "ms" milliseconds of sleeping, the handler returns 0 which causes sqlite3_step() to return SQLITE_BUSY." · 2026-10-01 |
| DS.replication | 없음 | 복제는 LiteFS·libSQL 같은 별도 계층 | https://www.sqlite.org/whentouse.html "SQLite only supports one writer at a time per database file." (복제 기능 언급 없음) · 2026-10-01 |
| DS.query_models | 조인, JSON 함수 기본 내장(3.38+, JSONB), FTS5 전문 검색 | 벡터·지리는 확장 필요 (미확인) | https://www.sqlite.org/json1.html "The JSON functions and operators are built into SQLite by default, as of SQLite version 3.38." · https://www.sqlite.org/fts5.html (FTS5 문서) · 2026-10-01 |
| DS.size_limits | DB 최대 약 281TB, 문자열·BLOB·행 최대 기본 10억 바이트, 열 기본 2000 | 컴파일 옵션으로 변경 | https://www.sqlite.org/limits.html "The default value of this macro is 1 billion" · "database file can grow to be as large as about 281 terabytes" · "The default setting for SQLITE_MAX_COLUMN is 2000." · 2026-10-01 |
| DS.backup | 자동 백업 없음. Online Backup API, `VACUUM INTO`로 사본 생성 | 주기·보존은 직접 구성. 없으면 최악 RPO = 마지막 수동 사본 이후 전부 | https://www.sqlite.org/backup.html "The Online Backup API was created to address these concerns." · https://www.sqlite.org/lang_vacuum.html "a new database is created in a file named by the argument to the INTO clause" · 2026-10-01 |
| DS.connections | 해당 없음 (서버 없음, 같은 호스트 프로세스가 파일을 직접 엶) | | https://www.sqlite.org/wal.html "All processes using a database must be on the same host computer" · 2026-10-01 |
| DS.schema_change | ALTER TABLE은 RENAME, RENAME COLUMN, ADD COLUMN, DROP COLUMN만. 그 외는 "새 테이블 생성 → 복사 → 삭제 → 이름 변경" 12단계 절차. DDL은 트랜잭션 안에서 실행 | 큰 테이블 재작성 중 DB 전체 쓰기 잠금 | https://www.sqlite.org/lang_altertable.html "SQLite supports a limited subset of ALTER TABLE." · "The 12-step generalized ALTER TABLE procedure above will work even if the schema change causes the information stored in the table to change." · 2026-10-01 |
| DS.availability | HA 없음. 호스트·디스크와 운명 공동체 | | https://www.sqlite.org/whentouse.html "if the website is write-intensive or is so busy that it requires multiple servers, then consider using an enterprise-class client/server database engine instead of SQLite" · 2026-10-01 |
| DS.multi_host_access | **불가.** 네트워크 파일시스템 위 공유는 잠금 문제로 손상 위험 | 컨테이너 여러 개 = DB 여러 개 | https://www.sqlite.org/useovernet.html "This simple, "remote database" approach is usually not the best way to use a single SQLite database from multiple systems" · "This has led to database corruption." · 2026-10-01 |
| DS.security | 공개판에는 저장 암호화 없음 (상용 SEE 필요). 감사 로그·행 권한 없음 | 파일 권한에 의존 | https://www.sqlite.org/see/doc/trunk/www/readme.wiki "the public version of SQLite will not be able to read or write an encrypted database file" · 2026-10-01 |
| DS.regions | 해당 없음 | | — |
| DS.scaling | 수직 확장만 (호스트 교체). 수평 확장 불가 | | https://www.sqlite.org/whentouse.html (위 인용) · 2026-10-01 |
| DS.cost_floor | 0 (호스트 디스크 비용에 포함) | | — ⚠️근거없음 |

#### 비용 구조
- 고정비 0. 단, 영속 디스크가 필요하면 플랫폼의 볼륨 비용과 "단일 인스턴스 고정" 제약이 따라온다(컴퓨트 표 CP.local_disk).

#### 교체 계열 정보
- API: Node `better-sqlite3`(동기), `sqlite3`(비동기 콜백, 2026-07-01 보관 처리), Python 표준 `sqlite3`(동기, `qmark`), `aiosqlite`(스레드로 감싼 비동기). §5.2.
- 방언: 동적 타이핑, 불리언 0/1, 날짜 타입 없음, `LIKE` ASCII 대소문자 무시, FK 기본 꺼짐. §5.4.
- 이식: SQL 대부분은 그대로, 타입 엄격성·날짜·불리언·잠금 문법·DDL이 바뀐다.

#### 함정
- 외래 키 제약이 **연결마다 꺼져 있다**(`PRAGMA foreign_keys = ON` 필요). SQLite에서 "잘 돌던" 앱이 PostgreSQL로 옮기면 FK 위반이 처음 드러난다. https://www.sqlite.org/foreignkeys.html "Foreign key constraints are disabled by default (for backwards compatibility), so must be enabled separately for each database connection." (2026-10-01)
- Django는 `database is locked`를 "SQLite가 너무 가벼워진 지점"으로 본다. 고통 흔적 신호로 그대로 쓸 수 있다. https://docs.djangoproject.com/en/stable/ref/databases/ "At a certain point SQLite becomes too "lite" for real-world applications" (2026-10-01)

### 1.2 SQLite — WAL 모드
- 계열: 저장소-관계형 (임베디드, 파일)
- 서울 리전: 해당 없음

1.1과 다른 키만 적는다. 나머지(행 경합, 크기, 백업, 스키마 변경, 보안, 비용)는 1.1과 같다.

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | **1.** 읽기와 쓰기는 동시에 가능 | WAL 파일이 하나라서 쓰기 하나 | https://www.sqlite.org/wal.html "since there is only one WAL file, there can only be one writer at a time." · "writers and readers can run at the same time" · 2026-10-01 |
| DS.row_contention | 1.1과 같음 | | 1.1 출처 |
| DS.transactions | 1.1과 같음 (SERIALIZABLE) | WAL에서도 읽기→쓰기 업그레이드 시 `SQLITE_BUSY` | https://www.sqlite.org/isolation.html "Transactions in SQLite are SERIALIZABLE." · 2026-10-01 |
| DS.replication | 없음 | | 1.1 출처 |
| DS.query_models | 1.1과 같음 | | 1.1 출처 |
| DS.size_limits | 1.1과 같음 + WAL 파일이 체크포인트 실패 시 무한 증가 | 자동 체크포인트 기본 1000페이지 | https://www.sqlite.org/wal.html "no checkpoints will be able to complete and hence the WAL file will grow without bound" · 2026-10-01 |
| DS.backup | 1.1과 같음 | 파일 복사 시 `-wal` 파일까지 함께여야 함 (Backup API 권장) | https://www.sqlite.org/backup.html · 2026-10-01 |
| DS.connections | 해당 없음 | | — |
| DS.schema_change | 1.1과 같음 | | 1.1 출처 |
| DS.availability | 없음 | | — ⚠️근거없음 |
| DS.multi_host_access | **불가.** 공유 메모리가 필요해 네트워크 FS에서 동작하지 않음 | 같은 호스트의 여러 프로세스(예: `gunicorn -w 4`)는 가능 | https://www.sqlite.org/wal.html "All processes using a database must be on the same host computer; WAL does not work over a network filesystem." · 2026-10-01 |
| DS.security | 1.1과 같음 | | 1.1 출처 |
| DS.regions | 해당 없음 | | — |
| DS.scaling | 1.1과 같음 | | — |
| DS.cost_floor | 0 | | — ⚠️근거없음 |

#### 비용 구조
- 1.1과 같음.

#### 함정
- WAL은 "읽기가 쓰기를 막지 않는다"를 해결할 뿐, 쓰기 동시성(C1)을 높이지 않는다. C1이 중간 이상이면 WAL로 바꾸는 것은 교체 대안이 아니다.
- 긴 읽기 트랜잭션이 겹치면 체크포인트가 끝나지 않아 WAL이 계속 커진다(위 인용).

### 1.3 libSQL · Turso Cloud
- 계열: 저장소-관계형 (SQLite 호환, 원격 + 임베디드 복제본)
- 서울 리전: **없음** (AWS 지역 목록에 ap-northeast-2 없음, 가장 가까운 곳 도쿄 `aws-ap-northeast-1`)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.query_models | SQLite와 같음 + 벡터 | 벡터 세부 미확인 | 미확인 |
| DS.connections | 원격 HTTP/WebSocket. 연결 수 한도 미확인 | | 미확인 ⚠️근거없음 |
| DS.schema_change | SQLite와 같음 (제한적 ALTER TABLE) | | 1.1 출처 |
| DS.security | 미확인 | | 미확인 |

#### 비용 구조
- 행 읽기·쓰기·저장량 과금(초과분: Developer 쓰기 $1/백만 행, 저장 $0.75/GB).

#### 교체 계열 정보
- 드라이버: `@libsql/client`(원격·임베디드). SQL은 SQLite 방언 그대로라 SQLite → Turso는 드라이버·연결 문자열 교체가 중심이다. 쓰기 동시성 문제는 기본 모드에서는 그대로 남는다.

#### 함정
- "SQLite를 원격으로" 바꿔도 C1(쓰기 동시성)은 해결되지 않는다(기본 모드 단일 쓰기). MVCC는 미리보기다.
- 서울 리전이 없다. 서울 사용자 앱이면 모든 쓰기가 도쿄 왕복이다.

### 1.4 LiteFS (Fly.io의 SQLite 복제 계층)
- 계열: 저장소-관계형 (SQLite 복제 FUSE 파일시스템)
- 서울 리전: 미확인 (Fly.io 리전에 따름)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.row_contention | SQLite와 같음 | | 1.1 출처 |
| DS.transactions | SQLite와 같음 | | 1.1 출처 |
| DS.query_models | SQLite와 같음 | | 1.1 출처 |
| DS.size_limits | SQLite와 같음 + 노드 볼륨 크기 | | — |
| DS.connections | 해당 없음 | | — |
| DS.schema_change | SQLite와 같음 | | 1.1 출처 |
| DS.security | SQLite와 같음 | | — |
| DS.regions | 미확인 | | 미확인 |

#### 비용 구조
- 노드(Fly Machine) × 볼륨. 관리형 백업 상품이 없어져 백업 저장소 비용을 따로 잡아야 한다.

#### 교체 계열 정보
- 앱 코드는 SQLite 그대로. 쓰기 요청을 주 노드로 보내는 라우팅(프록시 또는 앱 내부 전달)이 추가된다.

#### 함정
- 읽기 위주 앱을 여러 리전에 펼치는 용도다. C1(쓰기 동시성)이 높으면 해결책이 아니다.
- pre-1.0이며 관리형 백업이 끝났다. F3(데이터 손실 허용)이 "분 단위" 이하면 부적합.

---

## 2. PostgreSQL

### 2.1 PostgreSQL — 자체 운영 (컨테이너·VM)
- 계열: 저장소-관계형
- 서울 리전: 호스트에 따름

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 다수. MVCC로 읽기·쓰기가 서로 막지 않음 | 같은 행 갱신만 대기 | https://www.postgresql.org/docs/current/mvcc-intro.html "reading never blocks writing and writing never blocks reading" · 2026-10-01 |
| DS.row_contention | 행 잠금(`SELECT … FOR UPDATE`, `SKIP LOCKED`), 원자적 갱신, SERIALIZABLE에서 충돌 시 재시도 | | https://www.postgresql.org/docs/current/explicit-locking.html "there are row-level locks" · https://www.postgresql.org/docs/current/sql-select.html "[ NOWAIT \| SKIP LOCKED ]" · 2026-10-01 |
| DS.transactions | 다중 행·테이블. 기본 **READ COMMITTED**, SERIALIZABLE은 직렬화 실패 시 재시도 필요 | | https://www.postgresql.org/docs/current/transaction-iso.html "Read Committed is the default isolation level in PostgreSQL." · "Applications using this level must be prepared to retry transactions due to serialization failures." · 2026-10-01 |
| DS.replication | 스트리밍 복제 **기본 비동기**, 동기 복제 설정 가능(`synchronous_standby_names`). 복제본은 결국 일관 | | https://www.postgresql.org/docs/current/warm-standby.html "PostgreSQL streaming replication is asynchronous by default." · 2026-10-01 |
| DS.query_models | 조인, JSONB, 전문 검색, 확장(PostGIS·pgvector) | 확장 설치는 운영자 몫 | https://www.postgresql.org/docs/current/textsearch-intro.html "Full Text Searching (or just text search) provides the capability to identify natural-language documents" · https://www.postgresql.org/docs/current/datatype-json.html · 2026-10-01 |
| DS.size_limits | DB 크기 무제한, 테이블 32TB, 필드 1GB | BLCKSZ 8192 기준 | https://www.postgresql.org/docs/current/limits.html "relation size \| 32 TB" · "field size \| 1 GB" · 2026-10-01 |
| DS.backup | 연속 아카이빙 + 베이스 백업으로 PITR. `archive_timeout`으로 미아카이브 데이터의 최대 나이 제한 | 최악 RPO = 아카이브 주기 설계값 | https://www.postgresql.org/docs/current/continuous-archiving.html "To put a limit on how old unarchived data can be, you can set archive_timeout" · 2026-10-01 |
| DS.connections | `max_connections` 기본 **보통 100**, 서버 시작 시에만 변경. 풀러 없음(PgBouncer 별도) | 슈퍼유저 예약분 제외 | https://www.postgresql.org/docs/current/runtime-config-connection.html "The default is typically 100 connections" · "This parameter can only be set at server start." · 2026-10-01 |
| DS.schema_change | `ALTER TABLE`은 별도 표기 없으면 ACCESS EXCLUSIVE(읽기까지 막음). 비휘발 기본값 `ADD COLUMN`은 메타데이터만. `CREATE INDEX CONCURRENTLY`는 쓰기를 막지 않지만 트랜잭션 블록 안에서 불가 | `lock_timeout` 기본 0 → 잠금 대기 무한 | https://www.postgresql.org/docs/current/sql-altertable.html "An ACCESS EXCLUSIVE lock is acquired unless explicitly noted." · https://www.postgresql.org/docs/current/sql-createindex.html "CREATE INDEX CONCURRENTLY cannot" (be performed within a transaction block) · 2026-10-01 |
| DS.availability | 자동 페일오버 **없음** (Patroni 등 외부 도구 필요) | | https://www.postgresql.org/docs/current/warm-standby-failover.html "PostgreSQL does not provide the system software required to identify a failure on the primary and notify the standby database server." · 2026-10-01 |
| DS.multi_host_access | 가능 (TCP) | | — ⚠️근거없음 |
| DS.security | RLS 내장. 저장 암호화·감사(pgaudit)는 운영자가 구성 | | https://www.postgresql.org/docs/current/ddl-rowsecurity.html "tables can have row security policies that restrict, on a per-user basis, which rows can be returned" · 2026-10-01 |
| DS.regions | 호스트에 따름 | | — |
| DS.scaling | 수직(재시작), 읽기 복제본 | | — ⚠️근거없음 |
| DS.cost_floor | VM·디스크 비용. 서울 EC2 t4g.micro $0.0104/시간 (≈ $7.6/월) | 06-cost.md [PL] 값을 재사용, 이번에 재조회하지 않음 | considerations/06-cost.md COST-017 (Price List AmazonEC2) |

#### 비용 구조
- 고정비는 VM 하나로 가장 싸지만, 백업 저장소·모니터링·HA를 직접 만들어야 한다(G2 운영 역량).

#### 교체 계열 정보
- §5 전체. 매니지드 PostgreSQL로 옮길 때는 확장(extension) 지원 목록, 슈퍼유저 권한 부재, 파라미터 변경 방식(파라미터 그룹·플래그)이 바뀐다.

#### 함정
- 컨테이너로 띄우고 볼륨·백업을 안 붙이면 SQLite와 같은 단일 장애점이다(considerations/01 D-013).

### 2.2 PostgreSQL — Amazon RDS, Single-AZ
- 계열: 저장소-관계형
- 서울 리전: 있음 ([PL] ap-northeast-2에 단가 존재)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 다수 (엔진 2.1과 같음) | | 2.1 출처 |
| DS.row_contention | 2.1과 같음 | | 2.1 출처 |
| DS.transactions | 2.1과 같음 | | 2.1 출처 |
| DS.replication | 읽기 복제본 **비동기**, 원본당 최대 15개 | | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_ReadRepl.html "Amazon RDS copies them asynchronously to the read replica." · https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Limits.html "Read replicas per primary \| Each supported Region: 15" · 2026-10-01 |
| DS.query_models | 2.1과 같음 (지원 확장은 RDS 목록) | 확장 목록 미확인 | 2.1 출처 |
| DS.size_limits | 최대 **64 TiB**, 스토리지 자동 확장 | 늘리기만 가능(06-cost 참고) | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Storage.html "You can create Db2, MySQL, MariaDB, and PostgreSQL RDS DB instances with up to 64 tebibytes (TiB) of storage." · 2026-10-01 |
| DS.backup | 자동 백업 보존 0~35일 (0=비활성). **API·CLI 생성 시 기본 1일**, 콘솔 7일. PITR: 트랜잭션 로그를 **5분마다** S3 업로드 → 최악 RPO 약 5분. 복원은 새 인스턴스 | | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_WorkingWithAutomatedBackups.BackupRetention.html "the default backup retention period is one day" · https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PIT.html "RDS uploads transaction logs for DB instances to Amazon S3 every five minutes." · 2026-10-01 |
| DS.connections | 기본 `LEAST({DBInstanceClassMemory/9531392}, 5000)`. DBInstanceClassMemory는 OS·관리 프로세스 몫을 뺀 값이라 공칭 메모리보다 작음 (t4g.micro 1GiB면 112 미만). 풀러: RDS Proxy(유료) | 범위 6~262143 | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Limits.html "LEAST({DBInstanceClassMemory/9531392}, 5000)" · "this memory size is smaller than the value in gibibytes (GiB)" · 2026-10-01 |
| DS.schema_change | 엔진과 같음(2.1). 메이저 업그레이드 등은 Blue/Green으로 전환 1분 미만 | | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/blue-green-deployments-overview.html "The switchover typically takes under a minute with no data loss" · 2026-10-01 |
| DS.availability | 단일 존. 자동 페일오버 없음 | 존 장애 시 백업·스냅샷 복원 | (Multi-AZ 문서와 대비) https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZSingleStandby.html · 2026-10-01 |
| DS.multi_host_access | 가능 (VPC 네트워크) | | — ⚠️근거없음 |
| DS.security | KMS 저장 암호화(AES-256, 백업·복제본·스냅샷 포함), IAM DB 인증, VPC 격리, RLS(엔진) | 암호화는 생성 시 선택 | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Overview.Encryption.html "Amazon RDS encrypted DB instances use the industry standard AES-256 encryption algorithm" · https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAMDBAuth.html "IAM database authentication works with MariaDB, MySQL, and PostgreSQL." · 2026-10-01 |
| DS.regions | 서울 있음 | | [PL] APN2-InstanceUsage:db.t4g.micro (PostgreSQL) |
| DS.scaling | 인스턴스 클래스 변경 시 **중단 발생**. 읽기 복제본으로 읽기 확장 | | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_ModifyInstance.Settings.html "Downtime occurs during this change." (DB instance class) · 2026-10-01 |
| DS.cost_floor | 서울 db.t4g.micro **$0.025/시간 ≈ $18.25/월** + gp3 $0.131/GB-월 (20GB ≈ $2.62) → **약 $20.9/월**. scale-to-zero 없음 | 퍼블릭 접근이면 IPv4 $0.005/시간(≈$3.65) 추가 | [PL] "APN2-InstanceUsage:db.t4g.micro" 0.025, "$0.131 per GB-month of provisioned GP3 storage running PostgreSQL"; AmazonVPC [PL] "$0.005 per In-use public IPv4 address per hour" |

#### 비용 구조
- 인스턴스 시간 + 프로비저닝 스토리지 + 무료 할당 초과 백업($0.095/GB-월, [PL]) + RDS Proxy($0.018/vCPU-시간, [PL]). 엔진 표준 지원이 끝난 버전은 확장 지원 요금(PostgreSQL 1~2년차 $0.120/vCPU-시간, [PL]).

#### 교체 계열 정보
- 엔진은 커뮤니티 PostgreSQL이라 드라이버·SQL은 2.1과 같다. 바뀌는 것: 슈퍼유저 대신 `rds_superuser`, 파라미터 그룹으로 설정 변경, 확장 허용 목록.

#### 함정
- Terraform/API로 만들면 백업 보존 기본 1일. "주말에 발견한 손상"을 복구 못 한다.
- 인스턴스 크기 변경이 중단을 만든다(F4). Single-AZ는 이를 가릴 대기 복제본이 없다.

### 2.3 PostgreSQL — Amazon RDS, Multi-AZ 인스턴스 (대기 1개)
- 계열: 저장소-관계형
- 서울 리전: 있음

2.2와 다른 키만 적는다.

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 2.2와 같음 | | |
| DS.row_contention | 2.2와 같음 | | |
| DS.transactions | 2.2와 같음 | | |
| DS.replication | 다른 AZ에 **동기** 대기 복제본. **대기는 읽기 불가** | 동기 복제로 쓰기 지연 증가 가능 | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZSingleStandby.html "automatically provisions and maintains a synchronous standby replica in a different Availability Zone" · "You can't use a standby replica to serve read traffic." · 2026-10-01 |
| DS.query_models | 2.2와 같음 | | |
| DS.size_limits | 2.2와 같음 | | |
| DS.backup | 2.2와 같음 (PITR 최악 RPO 약 5분). 존 장애 RPO는 동기 복제로 0 | | 2.2 출처 |
| DS.connections | 2.2와 같음 | | |
| DS.schema_change | 2.2와 같음 | | |
| DS.availability | 자동 페일오버 **보통 60~120초**, DNS 레코드를 대기 쪽으로 변경 → 기존 연결 재접속 필요 | JVM DNS TTL 60초 이하 권장 | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZ.Failover.html "Failover times are typically 60–120 seconds." · "automatically changes the Domain Name System (DNS) record of the DB instance to point to the standby DB instance" · 2026-10-01 |
| DS.multi_host_access | 2.2와 같음 | | |
| DS.security | 2.2와 같음 | | |
| DS.regions | 서울 있음 | | [PL] APN2-Multi-AZUsage:db.t4g.micro |
| DS.scaling | 2.2와 같음 (클래스 변경 중단은 대기 복제본으로 줄어듦, 수치 미확인) | | |
| DS.cost_floor | 서울 db.t4g.micro **$0.051/시간 ≈ $37.23** + Multi-AZ gp3 $0.262/GB-월 (20GB ≈ $5.24) → **약 $42.5/월** | | [PL] "APN2-Multi-AZUsage:db.t4g.micro" 0.051, "$0.262 per GB-month of provisioned GP3 storage for Multi-AZ deployments running PostgreSQL" |

#### 비용 구조
- 인스턴스·스토리지 모두 Single-AZ의 약 2배.

#### 교체 계열 정보
- 앱 코드 변경 없음. 연결 풀의 재연결(사전 핑, 연결 수명 제한)이 필요하다.

#### 함정
- "Multi-AZ니까 읽기 분산"은 틀리다(대기 읽기 불가). 읽기 확장(C4)은 읽기 복제본(비동기) 또는 2.4.

### 2.4 PostgreSQL — Amazon RDS, Multi-AZ DB 클러스터 (읽기 가능 대기 2개)
- 계열: 저장소-관계형
- 서울 리전: 있음 (지원 리전 표에 Asia Pacific (Seoul))

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 다수 (쓰기 인스턴스 1개) | | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/multi-az-db-clusters-concepts.html "A Multi-AZ DB cluster has a writer DB instance and two reader DB instances in three separate Availability Zones" · 2026-10-01 |
| DS.row_contention | 2.1과 같음 | | |
| DS.transactions | 2.1과 같음 | 리더에서 읽으면 복제 지연만큼 오래된 값 | |
| DS.replication | **반동기**: 리더 1개 이상 확인 후 커밋. 리더는 읽기 가능 | 모든 리더 적용 완료는 보장 안 함 | 같은 문서 "semisynchronous replication, which requires acknowledgment from at least one reader DB instance in order for a change to be committed" · 2026-10-01 |
| DS.query_models | 2.1과 같음 | | |
| DS.size_limits | 2.2와 같음 | | |
| DS.backup | 보존 1~35일(0 불가). PITR 2.2와 같음 | | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_WorkingWithAutomatedBackups.BackupRetention.html "For a Multi-AZ DB cluster, you can set the backup retention period to between 1 and 35 days." · 2026-10-01 |
| DS.connections | 2.2와 같음 | | |
| DS.schema_change | 2.1과 같음 | | |
| DS.availability | 페일오버 **보통 35초 미만** | | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/multi-az-db-clusters-concepts-failover.html "Failover times are typically under 35 seconds." · 2026-10-01 |
| DS.multi_host_access | 가능 (쓰기·읽기 엔드포인트) | | ⚠️근거없음 |
| DS.security | 2.2와 같음 | | |
| DS.regions | 서울 있음 (PostgreSQL 17·18 전 버전) | | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.RDS_Fea_Regions_DB-eng.Feature.MultiAZDBClusters.html "Asia Pacific (Seoul) \| All PostgreSQL 18 versions \| All PostgreSQL 17 versions" · 2026-10-01 |
| DS.scaling | 지원 클래스만: db.c6gd, m5d, m6gd, m6id, m6idn, m8gd, r5d, r6gd, r6id, r6idn, r8gd, x2iedn (t 계열 없음) | medium은 c6gd만 | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/multi-az-db-clusters-concepts.html "Multi-AZ DB cluster deployments are supported for the following DB instance classes" · 2026-10-01 |
| DS.cost_floor | 서울 최저 db.m6gd.large 클러스터 **$0.783/시간 ≈ $571.6** + gp3 $0.393/GB-월 (20GB ≈ $7.86) → **약 $579.5/월** | c6gd.medium 클러스터는 서울 가격표에 없음 | [PL] "APN2-Multi-AZClusterUsage:db.m6gd.large" 0.783, "$0.393 per GB-month of provisioned GP3 storage Multi-AZ (readable standbys) deployments running PostgreSQL" |

#### 비용 구조
- 3노드 시간 + 3배 스토리지. 2.3 대비 최소 약 14배.

#### 교체 계열 정보
- 읽기 엔드포인트를 쓰려면 ORM에 읽기 라우팅(Prisma `readReplicas`, Django `DATABASE_ROUTERS`)을 추가한다.

#### 함정
- 바이브코더 규모(C1 중간, F1 짧아야 함)에서는 2.3이 대부분 충분하다. 2.4는 "페일오버 35초 미만 + 읽기 확장"이 동시에 필요할 때만.

### 2.5 PostgreSQL — Amazon Aurora, 프로비저닝
- 계열: 저장소-관계형
- 서울 리전: 있음

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 다수 (클러스터당 주 인스턴스 1개) | | https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.Overview.html "Each Aurora DB cluster has one primary DB instance." · 2026-10-01 |
| DS.row_contention | 2.1과 같음 | | |
| DS.transactions | 2.1과 같음 | | |
| DS.replication | 스토리지는 쓰기 시 3AZ의 6개 노드에 **동기** 복제. Aurora 복제본(최대 15)은 같은 볼륨을 읽고 지연은 보통 100ms 미만 | 복제본 읽기는 지연만큼 오래될 수 있음 | https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Concepts.AuroraHighAvailability.html "Aurora synchronously replicates the data across Availability Zones to six storage nodes" · https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.Replication.html "This lag is usually much less than 100 milliseconds" · 2026-10-01 |
| DS.query_models | 2.1과 같음 | | |
| DS.size_limits | 클러스터 볼륨 최대 256 TiB(특정 버전), 사용량 과금, 삭제하면 줄어듦 | | https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.Overview.StorageReliability.html "an Aurora cluster volume can grow up to 256 tebibytes (TiB) for specific engine versions" · 2026-10-01 |
| DS.backup | 연속·증분 자동 백업, 보존 1~35일, 보존 기간 내 임의 시점 복원 | 최신 복원 가능 시점 간격 수치 미확인 → 최악 RPO 미확인 | https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.Managing.Backups.html "Aurora automated backups are continuous and incremental" · "from 1–35 days" · 2026-10-01 |
| DS.connections | 기본 `LEAST({DBInstanceClassMemory/9531392},5000)` | | https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraPostgreSQL.Managing.html "LEAST({DBInstanceClassMemory/9531392},5000)" · 2026-10-01 |
| DS.schema_change | 2.1과 같음 | | |
| DS.availability | 복제본이 있으면 승격, **보통 60초 미만, 흔히 30초 미만**. 복제본이 없으면 같은 AZ에 재생성, **보통 10분 미만** | 클러스터 엔드포인트 사용 | https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Concepts.AuroraHighAvailability.html "service is typically restored in less than 60 seconds, and often less than 30 seconds" · "which typically takes less than 10 minutes" · 2026-10-01 |
| DS.multi_host_access | 가능. RDS Data API(HTTP)도 서울에서 Aurora PG 16.1+ 지원 | | https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/data-api.html "provides a secure HTTP endpoint" · https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Concepts.Aurora_Fea_Regions_DB-eng.Feature.Data_API.html "Asia Pacific (Seoul) \| Version 17.4 and higher \| Version 16.1 and higher" · 2026-10-01 |
| DS.security | 2.2와 같음 | | |
| DS.regions | 서울 있음. 글로벌 데이터베이스로 다른 리전 복제 지연 보통 1초 미만 | 비동기 | https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-global-database.html "with latency typically under a second" · 2026-10-01 |
| DS.scaling | 쓰기는 수직, 읽기는 복제본 최대 15 | | https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.Replication.html "An Aurora DB cluster can contain up to 15 Aurora Replicas." · 2026-10-01 |
| DS.cost_floor | 서울 db.t4g.medium **$0.113/시간 ≈ $82.5/월** + 스토리지 $0.12/GB-월 + I/O $0.24/백만 요청 (Standard). I/O-Optimized: 인스턴스 $0.147, 스토리지 $0.27 | scale-to-zero 없음 | [PL] "APN2-InstanceUsage:db.t4g.medium" (Aurora PostgreSQL) 0.113, "USD 0.120 per GB-month of consumed storage for Aurora PostgreSQL", "USD 0.24 per 1 million I/O requests for Aurora PostgreSQL" |

#### 비용 구조
- 인스턴스 + 사용 스토리지 + I/O(Standard). 백업 초과분 $0.023/GB-월([PL]).

#### 교체 계열 정보
- RDS PG와 코드 호환. Data API를 쓰면 드라이버가 AWS SDK로 바뀐다(HTTP, 서버리스 친화).

#### 함정
- 최소 인스턴스가 RDS보다 크다(t4g.medium). 소규모면 2.3이 싸다.
- 복제본이 없는 Aurora는 "스토리지는 3AZ지만 컴퓨트 복구는 최대 10분"이다.

### 2.6 PostgreSQL — Amazon Aurora Serverless v2
- 계열: 저장소-관계형
- 서울 리전: 있음 (Aurora PG 17.4+ / 18.3+ 등, 지원 표 참조)

2.5와 다른 키만 적는다.

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 2.5와 같음 | | |
| DS.row_contention | 2.5와 같음 | | |
| DS.transactions | 2.5와 같음 | | |
| DS.replication | 2.5와 같음 | 승격 티어 0·1이 아닌 리더는 쓰기와 함께 확장되지 않아 복제 지연 커질 수 있음 | https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2.setting-capacity.html "the readers don't scale along with the writer DB instance when the promotion tier of the readers isn't 0 or 1" · 2026-10-01 |
| DS.query_models | 2.5와 같음 | | |
| DS.size_limits | 용량 0~256 ACU, 1 ACU ≈ 2GiB 메모리 | | https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2.how-it-works.html "Aurora serverless offers capacity from 0 ACUs to 256 ACUs." · "Each ACU is a combination of approximately 2 gibibytes (GiB) of memory" · 2026-10-01 |
| DS.backup | 2.5와 같음 | | |
| DS.connections | **최대 ACU로 결정** (현재 ACU 아님). 기본값 표: 최대 1ACU 189, 4ACU 823, 8ACU 1,669, 16ACU 3,360, 32ACU 이상 5,000. 최소 0·0.5 ACU면 최대 2,000 상한. 최대 ACU 변경 후 재부팅해야 반영 | | https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2.setting-capacity.html "it uses the memory size based on the maximum Aurora capacity units (ACUs) for the DB instance, not the current ACU value" · "the maximum value of max_connections is capped at 2,000" · 2026-10-01 |
| DS.schema_change | 2.1과 같음 | | |
| DS.availability | 2.5와 같음 + 자동 일시정지 후 재개 **약 15초**, 24시간 넘게 정지면 **30초 이상** | 일시정지 간격 300초~86,400초 | https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2-auto-pause.html "the typical time to resume might be approximately 15 seconds" · "the resume time can be 30 seconds or longer" · 2026-10-01 |
| DS.multi_host_access | 2.5와 같음 | | |
| DS.security | 2.2와 같음 | | |
| DS.regions | 서울 있음 | | https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Concepts.Aurora_Fea_Regions_DB-eng.Feature.ServerlessV2.html "Asia Pacific (Seoul) \| Version 18.3 and higher \| Version 17.4 and higher" (0 ACU 지원 표) · 2026-10-01 |
| DS.scaling | 최소~최대 ACU 사이 자동 확장 | 확장 속도 수치 미확인 | 같은 문서 · 2026-10-01 |
| DS.cost_floor | 서울 **$0.20/ACU-시간**. 최소 0 ACU면 정지 중 인스턴스 요금 0(스토리지만), 최소 0.5 ACU 상시면 **≈ $73/월** | RDS Proxy가 붙으면 프록시가 연결을 유지 | [PL] "USD 0.2 per Aurora Capacity Unit hour running Aurora PostgreSQL Serverless v2"; https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2-auto-pause.html "the proxy maintains an open connection to each DB instance in the cluster" · 2026-10-01 |

#### 비용 구조
- ACU-시간 + 스토리지 + I/O. 확장 지원 버전은 ACU당 추가($0.102/ACU-시간 1~2년차, [PL]).

#### 교체 계열 정보
- 2.5와 같음. 일시정지를 쓰면 연결 타임아웃을 15초(하루 넘으면 30초) 이상으로.

#### 함정
- 최소 0.5 ACU의 `max_connections`는 최대 ACU로 정해지지만 2,000 상한이 걸린다.
- "scale-to-zero"는 RDS Proxy나 상시 연결(풀의 유휴 연결 포함)이 있으면 일어나지 않는다.

### 2.7 PostgreSQL — Google Cloud SQL, 단일(존) 인스턴스
- 계열: 저장소-관계형
- 서울 리전: 있음 (asia-northeast3)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 다수 (엔진 2.1) | | 2.1 출처 |
| DS.row_contention | 2.1과 같음 | | |
| DS.transactions | 2.1과 같음 | | |
| DS.replication | 읽기 복제본(비동기 전제), 교차 리전 복제본 | 복제본이 주보다 작으면 `max_connections`가 크게 상속될 수 있음 | https://docs.cloud.google.com/sql/docs/postgres/replication "it might inherit a larger value of max_connections based on the size of the primary instance" · 2026-10-01 |
| DS.query_models | 2.1과 같음 | | |
| DS.size_limits | 전용 vCPU 인스턴스 최대 64TB, 자동 증가 기본 켜짐(늘리기만). 공유 코어 최대 3,062GiB | | https://docs.cloud.google.com/sql/docs/postgres/instance-settings "Instances with at least one unshared vCPU can have up to 64 TB." · "Enable automatic storage increases \| Y \| On (default value)" · 2026-10-01 |
| DS.backup | 일일 자동 백업(4시간 창), 보존 기본 7개. PITR 로그 보존 Enterprise 최대 7일 / Enterprise Plus 최대 35일. PITR은 항상 새 인스턴스 | 최악 RPO 수치 미확인 | https://docs.cloud.google.com/sql/docs/postgres/backup-recovery/backing-up "The number can't be less than the default (seven)." · https://docs.cloud.google.com/sql/docs/editions-intro "Point-in-time log retention \| Up to 35 days \| Up to 7 days" · https://docs.cloud.google.com/sql/docs/postgres/backup-recovery/pitr "A point-in-time recovery always creates a new instance" · 2026-10-01 |
| DS.connections | 메모리별 기본: ~0.5GB 25, ~1.7GB 50, 3.75GB~ 100, 6GB~ 200, 7.5GB~ 400, 15GB~ 500, 30GB~ 600, 60GB~ 800, 120GB 이상 1,000. **Cloud Run 내장 연결은 인스턴스당 100**. 관리형 풀링은 Enterprise Plus만 | | https://docs.cloud.google.com/sql/docs/postgres/flags "tiny (~0.5) \| 25 \| small (~1.7) \| 50 \| from 3.75 to 100" · https://docs.cloud.google.com/sql/docs/postgres/quotas "Cloud Run container instances are limited to 100 connections per Cloud SQL database" · https://docs.cloud.google.com/sql/docs/postgres/managed-connection-pooling "Your instance must be a Cloud SQL Enterprise Plus edition instance." · 2026-10-01 |
| DS.schema_change | 2.1과 같음 | | |
| DS.availability | 존 인스턴스는 자동 페일오버 없음. Enterprise 계획 작업은 수 분 중단, Enterprise Plus는 1초 미만 | SLA: Plus 99.99%, Enterprise 99.95% | https://docs.cloud.google.com/sql/docs/editions-intro "Availability SLA \| 99.99% (includes maintenance) \| 99.95% (excludes maintenance)" · "Sub-second downtime" · 2026-10-01 |
| DS.multi_host_access | 가능 (사설 IP, Auth Proxy·커넥터) | | — ⚠️근거없음 |
| DS.security | 기본 Google 관리 키, CMEK 선택, IAM DB 인증 | | https://docs.cloud.google.com/sql/docs/postgres/instance-settings "Google-owned and Google-managed encryption key (default value) Cloud KMS key" · 2026-10-01 |
| DS.regions | 서울 asia-northeast3 | | https://docs.cloud.google.com/sql/docs/postgres/locations "asia-northeast3 \| Seoul" · 2026-10-01 |
| DS.scaling | 수직(머신 유형 변경, Enterprise는 수 분 중단) | | 위 editions-intro · 2026-10-01 |
| DS.cost_floor | **us-central1 기준** db-f1-micro $0.0105/시간 ≈ $7.67/월 (SLA 제외), 전용 1vCPU·3.75GB ≈ $49.3/월 (vCPU $0.0413 + 메모리 $0.007/GiB-시간). SSD $0.000232877/GiB-시간 ≈ $0.17/GB-월. **서울 단가 미확인** | 공유 코어는 SLA 대상 아님 | https://cloud.google.com/sql/pricing "db-f1-micro* … $0.0105 / 1 hour" · "*Shared CPU machine types (db-f1-micro and db-g1-small) are not covered by the Cloud SQL SLA." · 2026-10-01 |

#### 비용 구조
- vCPU·메모리·스토리지 시간 과금(초 단위). CUD 1년 25%, 3년 52%.

#### 교체 계열 정보
- 엔진 PostgreSQL. 연결은 Cloud SQL Auth Proxy·언어별 커넥터 또는 사설 IP.

#### 함정
- Cloud Run 내장 연결 100/인스턴스 × 최대 인스턴스가 `max_connections`(작은 인스턴스 25~100)를 쉽게 넘는다.

### 2.8 PostgreSQL — Google Cloud SQL, HA (리전)
- 계열: 저장소-관계형
- 서울 리전: 있음

2.7과 다른 키만 적는다.

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 2.7과 같음 | | |
| DS.row_contention | 2.7과 같음 | | |
| DS.transactions | 2.7과 같음 | | |
| DS.replication | 두 존의 디스크에 **동기** 복제 후 커밋 보고. 대기는 읽기를 받지 않음(읽기는 복제본) | | https://docs.cloud.google.com/sql/docs/postgres/high-availability "all writes made to the primary instance are replicated to disks in both zones before a transaction is reported as committed" · 2026-10-01 |
| DS.query_models | 2.7과 같음 | | |
| DS.size_limits | 2.7과 같음 | | |
| DS.backup | 2.7과 같음. 존 장애 RPO 0 | | |
| DS.connections | 2.7과 같음 | | |
| DS.schema_change | 2.7과 같음 | | |
| DS.availability | 페일오버 중 **약 60초** 사용 불가, 공유 고정 IP 유지 | Enterprise Plus 계획 작업 1초 미만 | 같은 문서 "you can expect the instance to be unavailable for about sixty seconds" · "Through a shared static IP address with the primary instance" · 2026-10-01 |
| DS.multi_host_access | 2.7과 같음 | | |
| DS.security | 2.7과 같음 | | |
| DS.regions | 서울 있음 | | ⚠️근거없음 |
| DS.scaling | 2.7과 같음 | | |
| DS.cost_floor | 단일의 2배 (us-central1: HA vCPU $0.0826, HA 메모리 $0.014/GiB-시간, HA db-f1-micro $0.021/시간 ≈ $15.3/월). **서울 단가 미확인** | | https://cloud.google.com/sql/pricing "HA db-f1-micro* … $0.021 / 1 hour" · 2026-10-01 |

#### 비용 구조 / 교체 계열 정보
- 2.7과 같음. 앱 변경 없음(IP 유지), 재연결 로직만 필요.

#### 함정
- HA 대기는 읽기 확장이 아니다(2.3과 같은 오판).

### 2.9 AlloyDB for PostgreSQL
- 계열: 저장소-관계형
- 서울 리전: 있음 (asia-northeast3)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 다수 (주 인스턴스 1) | | https://docs.cloud.google.com/alloydb/docs/overview "a primary instance and multiple load-balanced read pool instances" · 2026-10-01 |
| DS.row_contention | 2.1과 같음 | | |
| DS.transactions | 2.1과 같음 | | |
| DS.replication | HA: 다른 존의 대기 노드 + 리전 로그 저장소에 WAL **동기** 기록. 읽기 풀 노드 최대 20 | | https://docs.cloud.google.com/alloydb/docs/high-availability "No data loss occurs during failover due to synchronous WAL writes to the regional log persistor." · https://docs.cloud.google.com/alloydb/quotas "Read pool nodes per cluster" 20 · 2026-10-01 |
| DS.query_models | PG + 컬럼형 엔진, 벡터 검색(AlloyDB AI) | | https://docs.cloud.google.com/alloydb/docs/overview "a columnar engine that accelerates analytical queries" · "integrates vector search" · 2026-10-01 |
| DS.size_limits | 클러스터 저장 기본 16TiB, 최대 128TiB | | https://docs.cloud.google.com/alloydb/quotas "The default value for this quota is 16 TiB per cluster. The maximum supported value is 128 TiB per cluster." · 2026-10-01 |
| DS.backup | 연속 백업 기본 켜짐, 마이크로초 단위 PITR, 기본 14일 창(1~35일) + 일일 백업 | | https://docs.cloud.google.com/alloydb/docs/backup/overview "with microsecond granularity" · "By default, AlloyDB lets you choose any point in time up to 14 days into the past." · 2026-10-01 |
| DS.connections | 기본 `max_connections`는 인스턴스 크기별 100~1,000 | 크기별 정확한 표는 미확인 | https://docs.cloud.google.com/alloydb/quotas "Default limit varies by instance size" · 2026-10-01 |
| DS.schema_change | 2.1과 같음 | | |
| DS.availability | 감지 최대 30초 + 대기 기동 30초 미만 → **약 60초**. PG18 신규 인스턴스는 핫 스탠바이 | 존(비HA) 인스턴스는 긴 중단 가능 | https://docs.cloud.google.com/alloydb/docs/high-availability "This detection can take up to 30 seconds" · "typically takes less than 30 seconds" · 2026-10-01 |
| DS.multi_host_access | 가능 | | — ⚠️근거없음 |
| DS.security | 미확인 (CMEK·IAM 세부 이번에 미열람) | | 미확인 |
| DS.regions | 서울 있음 | | https://docs.cloud.google.com/alloydb/docs/locations "asia-northeast3 \| Seoul" · 2026-10-01 |
| DS.scaling | 머신 유형 변경, 읽기 풀 노드 추가 | 최대 288 vCPU | https://cloud.google.com/alloydb/pricing "up to 288 vCPUs and 2232 GiB of memory per node" · 2026-10-01 |
| DS.cost_floor | **us-central1 기준** 최소 c4a-highmem-1(1 vCPU·8GB): vCPU $0.06608 + 메모리 $0.0112/GiB-시간 → ≈ $0.156/시간 ≈ **$113.6/월**(존 인스턴스 1노드). HA는 2노드라 ≈ $227/월. 스토리지 $0.0004109/GiB-시간 ≈ $0.30/GB-월. **서울 단가 미확인**. 30일 무료 체험 클러스터 | | https://cloud.google.com/alloydb/pricing "A high availability primary instance uses two nodes" · https://docs.cloud.google.com/alloydb/docs/choose-machine-type "c4a-highmem-1 \| 1 \| 8 GB RAM" · 2026-10-01 |

#### 비용 구조
- 노드 vCPU·메모리 + 사용 스토리지(공유) + 백업 저장.

#### 교체 계열 정보
- PG 호환. Google DMS가 PostgreSQL → AlloyDB 동종 이전을 지원(§5.5).

#### 함정
- 바이브코더 규모에서는 Cloud SQL HA보다 고정비가 크다. 분석·벡터 요구(C5)가 있을 때만 후보.

### 2.10 PostgreSQL — Supabase, Free 플랜
- 계열: 저장소-관계형 (BaaS 동봉)
- 서울 리전: 있음 (ap-northeast-2)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 다수 (PostgreSQL) | | 2.1 출처 |
| DS.row_contention | 2.1과 같음 | 클라이언트 SDK 다중 호출은 원자적이지 않음 → `rpc()` 함수로 | considerations/04 C-099 |
| DS.transactions | 2.1과 같음 | | |
| DS.replication | 없음 | | — ⚠️근거없음 |
| DS.query_models | 2.1과 같음 (pgvector 등 확장 제공) | 확장 목록 미확인 | — |
| DS.size_limits | DB **500MB**, 이그레스 5GB | Nano 컴퓨트 | https://supabase.com/pricing (Free "500 MB") · 2026-10-01 |
| DS.backup | **자동 백업 없음** | 직접 `db dump` | https://supabase.com/docs/guides/platform/backups (Free 플랜 자동 백업 없음) · 2026-10-01 |
| DS.connections | Nano: 직접 60 / 풀러 클라이언트 200 | | https://supabase.com/docs/guides/platform/compute-and-disk (Nano "60 \| 200") · 2026-10-01 |
| DS.schema_change | 2.1과 같음 | | |
| DS.availability | HA 없음. **1주 비활성 시 프로젝트 일시정지** | | https://supabase.com/pricing "After 1 week of inactivity" · 2026-10-01 |
| DS.multi_host_access | 가능 (직접 IPv6 / 풀러 IPv4 / REST) | | https://supabase.com/docs/guides/database/connecting-to-postgres · 2026-10-01 |
| DS.security | RLS(노출 스키마는 RLS 필수), SOC2 대상 아님 | | https://supabase.com/pricing (SOC2 Team 이상) · 2026-10-01 |
| DS.regions | 서울 있음 | | https://supabase.com/docs/guides/platform/regions "Northeast Asia (Seoul), ap-northeast-2" · 2026-10-01 |
| DS.scaling | 불가 (Nano 고정, 유료 전환 필요) | | https://supabase.com/docs/guides/platform/compute-and-disk "You cannot launch Nano instances on paid plans" · 2026-10-01 |
| DS.cost_floor | $0. 조직당 무료 프로젝트 2개 | | https://supabase.com/pricing · 2026-10-01 |

#### 비용 구조 / 교체 계열 정보
- 2.11 참고. Supabase는 표준 Postgres 접속을 주므로 다른 PG로 이전이 쉽다(RLS·`auth` 스키마 의존은 남음).

#### 함정
- 사용자 생성 데이터(C7)가 있으면 Free는 "백업 없음 + 일시정지"로 바로 미충족.

### 2.11 PostgreSQL — Supabase, Pro / Team
- 계열: 저장소-관계형 (BaaS 동봉)
- 서울 리전: 있음

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 다수 | | 2.1 출처 |
| DS.row_contention | 2.10과 같음 | | |
| DS.transactions | 2.1과 같음. 트랜잭션 모드 풀러(6543)는 준비된 문장 미지원 | | https://supabase.com/docs/guides/database/connecting-to-postgres "Transaction mode does not support prepared statements." · 2026-10-01 |
| DS.replication | 읽기 복제본 **비동기** | 페일오버 수단으로 문서화되지 않음 | https://supabase.com/docs/guides/platform/read-replicas "Replication is asynchronous to ensure that transactions on the Primary aren't blocked." · 2026-10-01 |
| DS.query_models | 2.10과 같음 | | |
| DS.size_limits | 디스크 8GB 포함 후 $0.125/GB, 줄일 수 없음, gp3 최대 64TB | | https://supabase.com/pricing "8 GB disk size per project included, then $0.125 per GB" · https://supabase.com/docs/guides/platform/compute-and-disk "You can increase disk size but cannot decrease it" · 2026-10-01 |
| DS.backup | 일일 백업 Pro 7일 / Team 14일 / Enterprise 30일 → 최악 RPO 24시간. PITR 애드온: WAL 2분 간격 → **최악 RPO 2분**, Small 이상 필요, 7일 $100/월(14일·28일 최대 $400). 복원 중 프로젝트 접근 불가 | | https://supabase.com/docs/guides/platform/backups "By default, we back up WAL files at two-minute intervals." · "must also use at least a Small compute add-on" · "The project is inaccessible during this process" · 2026-10-01 |
| DS.connections | 컴퓨트별 직접/풀러: Micro 60/200, Small 90/400, Medium 120/600, Large 160/800, XL 240/1,000, 2XL 380/1,500 … 16XL 500/12,000. 전용 풀러(PgBouncer)는 유료 플랜, 트랜잭션 모드만 | | https://supabase.com/docs/guides/platform/compute-and-disk (표) · https://supabase.com/docs/guides/database/connecting-to-postgres · 2026-10-01 |
| DS.schema_change | 2.1과 같음 | | |
| DS.availability | 관리형 HA(다중 노드 자동 페일오버): **미확인.** Multigres는 2026-06 오픈소스 알파, "Multigres for Supabase is coming soon" | 컴퓨트 변경 시 보통 2분 미만 중단 | https://supabase.com/blog/multigres-v0-1-alpha "This is an open-source-only release. Multigres for Supabase is coming soon." · https://supabase.com/docs/guides/platform/compute-and-disk "usually applied with less than 2 minutes of downtime" · 2026-10-01 |
| DS.multi_host_access | 가능. 직접 연결은 기본 IPv6, IPv4는 애드온 또는 풀러 | IPv4 애드온 가격 미확인 | https://supabase.com/docs/guides/database/connecting-to-postgres · 2026-10-01 |
| DS.security | RLS, SOC2·ISO27001은 Team 이상, HIPAA는 유료 애드온 | | https://supabase.com/pricing · 2026-10-01 |
| DS.regions | 서울 있음 | | 2.10 출처 |
| DS.scaling | 컴퓨트 애드온 단계 변경(2분 미만 중단), 읽기 복제본 | | 위 출처 |
| DS.cost_floor | **Pro $25/월**(컴퓨트 크레딧 $10 = Micro ≈ $10 포함). Small ≈ $15, Medium ≈ $60. PITR 쓰면 Pro + Small 차액 + $100 ≈ **$130/월**. Team $599/월 | 일시정지 없음 | https://supabase.com/pricing "$10/month in compute credits" · "Projects on paid plans aren't paused for inactivity" · 2026-10-01 |

#### 비용 구조
- 플랜 + 컴퓨트 애드온(프로젝트마다) + 디스크·이그레스 + PITR. 지출 상한은 컴퓨트·PITR을 막지 않는다(considerations/06 COST-060).

#### 교체 계열 정보
- `@supabase/supabase-js`의 `from()`은 PostgREST(HTTP)이고, 서버 코드는 표준 PG 드라이버도 쓸 수 있다. Supabase를 떠날 때 `auth.uid()` 기반 RLS 정책과 `rpc()` 호출이 이식 비용이다.

#### 함정
- 서버리스에서 직접 연결(5432)을 쓰면 Micro 60연결이 금방 찬다. 트랜잭션 풀러(6543) + `prepare: false`가 필요하다.
- F1이 "짧아야 함"이면 Supabase 단일 인스턴스는 HA 근거가 없다(미확인).

### 2.12 PostgreSQL — Neon, Free
- 계열: 저장소-관계형 (서버리스, 스토리지·컴퓨트 분리)
- 서울 리전: **없음** (AWS 아시아: 싱가포르, 시드니)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 다수 (PostgreSQL) | | 2.1 출처 |
| DS.query_models | 2.1과 같음 | 확장 목록 미확인 | — |
| DS.schema_change | 2.1과 같음 | | |
| DS.multi_host_access | 가능 (TCP, HTTP, WebSocket) | | — ⚠️근거없음 |

#### 비용 구조 / 교체 계열 정보
- 2.13 참고. 표준 PG라 이식성 높음. `@neondatabase/serverless` HTTP 모드에서 `pg`(WebSocket/TCP)로 바꾸면 대화형 트랜잭션이 가능해진다.

#### 함정
- 서울 사용자 앱이면 싱가포르 왕복 지연. Vercel 기본 리전(iad1)과 겹치면 더 나빠진다.

### 2.13 PostgreSQL — Neon, Launch / Scale
- 계열: 저장소-관계형
- 서울 리전: 없음

2.12와 다른 키만 적는다.

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 2.12와 같음 | | |
| DS.row_contention | 2.12와 같음 | | |
| DS.transactions | 2.12와 같음 | | |
| DS.replication | 2.12와 같음 (읽기 복제본 제공 여부 세부 미확인) | | |
| DS.query_models | 2.12와 같음 | | |
| DS.connections | 2.12와 같음 | | |
| DS.schema_change | 2.1과 같음 | | |
| DS.multi_host_access | 2.12와 같음 | | |
| DS.regions | 서울 없음 | | 2.12 출처 |

#### 함정
- scale-to-zero 상태에서 첫 요청 지연(수백 ms)과 세션 상태 초기화. 상시 연결 풀을 두면 0으로 내려가지 않는다(비용 가정과 어긋남).

### 2.14 PostgreSQL — PlanetScale Postgres
- 계열: 저장소-관계형
- 서울 리전: 있음 (GCP `gcp-asia-northeast3`)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.row_contention | 2.1과 같음 | | |
| DS.transactions | 2.1과 같음 | PgBouncer(6432) 경유 시 세션 기능 제약 | |
| DS.query_models | 2.1과 같음 (확장 목록 미확인) | | |
| DS.size_limits | 미확인 | Metal은 SKU에 스토리지 포함 | 미확인 |
| DS.schema_change | 2.1과 같음 | | |
| DS.multi_host_access | 가능 | | — ⚠️근거없음 |
| DS.security | 미확인 | | 미확인 |
| DS.scaling | 클러스터 SKU 변경 (중단 여부 미확인) | | 미확인 ⚠️근거없음 |

#### 함정
- $5 단일 노드는 HA·읽기 복제본이 없다. F1이 "짧아야 함"이면 HA SKU($15~) 이상.

### 2.15 PostgreSQL — Prisma Postgres
- 계열: 저장소-관계형 (서버리스)
- 서울 리전: **없음** (아시아: ap-northeast-1 도쿄, ap-southeast-1)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.row_contention | 2.1과 같음 | | |
| DS.transactions | 2.1과 같음 (HTTP 서버리스 드라이버 경유 시 제약 미확인) | | 미확인 |
| DS.replication | 미확인 | | 미확인 |
| DS.query_models | 2.1과 같음 | 확장 목록 미확인 | |
| DS.schema_change | 2.1과 같음 | | |
| DS.availability | 미확인 | | 미확인 |
| DS.security | 미확인 | | 미확인 |
| DS.scaling | 미확인 | | 미확인 |

#### 함정
- 코딩 에이전트가 `npx create-db`로 만든 DB를 그대로 쓰면 하루 뒤 사라진다.

---

## 3. MySQL

### 3.1 MySQL — Amazon RDS for MySQL (Single-AZ / Multi-AZ 인스턴스 / Multi-AZ DB 클러스터)
- 계열: 저장소-관계형
- 서울 리전: 있음 (세 배포 모두)

배포 옵션별 차이(복제·페일오버·비용)는 PostgreSQL 2.2~2.4와 같은 문서·같은 단가다. 엔진 고유 값만 적는다.

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 다수 (InnoDB 행 잠금) | | https://dev.mysql.com/doc/refman/8.4/en/innodb-locking.html "InnoDB implements standard row-level locking" · 2026-10-01 |
| DS.row_contention | 행 잠금 + 갭·넥스트키 잠금 (REPEATABLE READ에서 범위 잠금 → 데드락 패턴이 PG와 다름) | | 같은 문서 "A next-key lock is a combination of a record lock on the index record and a gap lock" · 2026-10-01 |
| DS.transactions | 기본 **REPEATABLE READ** | | https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html "The default isolation level for InnoDB is REPEATABLE READ." · 2026-10-01 |
| DS.replication | Single-AZ: 읽기 복제본 비동기(최대 15) / Multi-AZ 인스턴스: 동기 대기(읽기 불가) / 클러스터: 반동기 | | 2.2~2.4 출처 |
| DS.query_models | 조인, JSON, InnoDB 전문 검색 | | 미확인 (세부 미열람) ⚠️근거없음 |
| DS.size_limits | 64 TiB | | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Storage.html · 2026-10-01 |
| DS.backup | 2.2와 같음 (5분 로그 업로드, API 기본 1일) | | 2.2 출처 |
| DS.connections | 기본 `{DBInstanceClassMemory/12582880}` (≈ MB/12). t3.micro 약 60, 8GiB 클래스 약 630 | 범위 1~100000 | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Limits.html "{DBInstanceClassMemory/12582880}" · "the default maximum number of connections for a MySQL DB instance running on a db.t3.micro DB instance class is approximately 60" · 2026-10-01 |
| DS.schema_change | 온라인 DDL: 열 추가·삭제·이름 변경 등 `ALGORITHM=INSTANT`, 동시 DML 허용. **DDL은 암묵적 커밋**(트랜잭션 DDL 아님) | INSTANT 미지원 작업과 섞을 수 없음 | https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html "Adding a column Yes* \| Yes \| No* \| Yes*" · https://dev.mysql.com/doc/refman/8.4/en/implicit-commit.html "implicitly end any transaction active in the current session" · 2026-10-01 |
| DS.availability | 2.2~2.4와 같음 (60~120초 / 35초 미만) | | 2.3·2.4 출처 |
| DS.multi_host_access | 가능 | | ⚠️근거없음 |
| DS.security | KMS 암호화, IAM DB 인증 | | 2.2 출처 |
| DS.regions | 서울 있음 (Multi-AZ 클러스터 "All available versions") | | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.RDS_Fea_Regions_DB-eng.Feature.MultiAZDBClusters.html "Asia Pacific (Seoul) \| All available versions" · 2026-10-01 |
| DS.scaling | 2.2와 같음 | | |
| DS.cost_floor | 서울 db.t4g.micro $0.025/시간(Single) / $0.051(Multi-AZ), 클러스터 m6gd.large $0.783 — PG와 동일. **MySQL 8.0은 2026-07-31 표준 지원 종료, 2026-08-01부터 확장 지원 요금 $0.120/vCPU-시간**(t4g.micro 2 vCPU → ≈ **$175/월 추가**). 8.4는 2029-07-31까지 표준 | | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/MySQL.Concepts.VersionMgmt.html "MySQL 5.7 and 8.0 are now only available under RDS Extended Support." · [PL] "USD 0.120 per hour per vCPU running RDS Extended Support for MySQL 8 in Year 1, Year 2" · 2026-10-01 |

#### 비용 구조
- PG와 같음 + 버전에 따라 확장 지원 요금. 확장 지원 요금은 vCPU 기준이라 작은 인스턴스일수록 인스턴스 요금보다 훨씬 크다.

#### 교체 계열 정보
- MySQL → PostgreSQL 방언 차이는 §5.4. 드라이버 Node `mysql2`, Python `PyMySQL`.

#### 함정
- `engine_version = "8.0"`인 RDS MySQL은 지금 확장 지원 과금 중이다. t4g.micro 기준 인스턴스 요금($18)의 약 10배가 붙는다.

### 3.2 MySQL — Amazon Aurora MySQL (프로비저닝 / Serverless v2)
- 계열: 저장소-관계형
- 서울 리전: 있음 (Serverless v2: Aurora MySQL 3.02.0+)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 다수 (쓰기 인스턴스 1) | | 2.5 출처 |
| DS.row_contention | 3.1과 같음 (InnoDB) | | |
| DS.transactions | 3.1과 같음 | | |
| DS.replication | 2.5와 같음 (6사본 동기 스토리지, 복제본 최대 15, 지연 100ms 미만) | | 2.5 출처 |
| DS.query_models | 3.1과 같음 | | |
| DS.size_limits | 2.5와 같음 / Serverless v2는 2.6과 같음 | | |
| DS.backup | 2.5와 같음 (연속 백업 1~35일). Backtrack(MySQL 전용) 별도 | 최악 RPO 미확인 | https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.Managing.Backups.html · 2026-10-01 |
| DS.connections | 클래스별 기본값 표: t3/t4g.medium 90, t4g.large 135, r3.large 1,000 … (메모리 2배마다 +1,000), 최대 16,000. Serverless v2: 최대 1ACU 90, 4ACU 135, 8ACU 1,000, 16ACU 2,000, 32ACU 3,000, 64ACU 4,000, 128ACU 5,000 | | https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraMySQL.Managing.Performance.html "up to 16,000" · "db.t4g.medium \| 90" · https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2.setting-capacity.html (표) · 2026-10-01 |
| DS.schema_change | 인스턴트 DDL(`ALGORITHM=INSTANT`) 지원(커뮤니티 MySQL 8과 호환) | | https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraMySQL.Managing.FastDDL.html "Aurora MySQL version 3 is compatible with the instant DDL from community MySQL 8." · 2026-10-01 |
| DS.availability | 2.5·2.6과 같음 | | |
| DS.multi_host_access | 가능. Data API: 서울 Aurora MySQL 3.07+ | | https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Concepts.Aurora_Fea_Regions_DB-eng.Feature.Data_API.html "Asia Pacific (Seoul) \| Version 3.07 and higher" · 2026-10-01 |
| DS.security | 2.2와 같음 | | |
| DS.regions | 서울 있음 | | https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Concepts.Aurora_Fea_Regions_DB-eng.Feature.ServerlessV2.html "Asia Pacific (Seoul) \| Version 3.02.0 and higher" · 2026-10-01 |
| DS.scaling | 2.5·2.6과 같음 | | |
| DS.cost_floor | 서울 db.t4g.medium $0.113/시간 ≈ $82.5/월 + 스토리지 $0.12/GB·I/O $0.24/백만. Serverless v2 $0.20/ACU-시간 | Aurora MySQL 3의 표준 지원 종료일 미확인 | [PL] "APN2-InstanceUsage:db.t4g.medium" (Aurora MySQL) 0.113, "USD 0.2 per Aurora Capacity Unit hour running Aurora MySQL Serverless v2" |

#### 함정
- RDS MySQL 8.0 확장 지원을 피하려고 Aurora MySQL로 옮기는 경우, Aurora MySQL 3의 지원 일정은 이번에 확인하지 못했다(미확인).

### 3.3 MySQL — Google Cloud SQL for MySQL (단일 / HA)
- 계열: 저장소-관계형
- 서울 리전: 있음

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 다수 (InnoDB) | | 3.1 출처 |
| DS.row_contention | 3.1과 같음 | | |
| DS.transactions | 3.1과 같음 | | |
| DS.replication | HA: 두 존 디스크 동기 복제 후 커밋 | | https://docs.cloud.google.com/sql/docs/mysql/high-availability "replicated to disks in both zones before a transaction is reported as committed" · 2026-10-01 |
| DS.query_models | 3.1과 같음 | | |
| DS.size_limits | 2.7과 같음 (64TB) | | 2.7 출처 |
| DS.backup | 2.7과 같음 (일일, 7개, PITR 로그 7일/35일) | MySQL PITR은 바이너리 로그 기반 | 2.7 출처 |
| DS.connections | 메모리로 결정. 기본값 수치 **미확인**. Cloud Run 인스턴스당 100 | | https://docs.cloud.google.com/sql/docs/mysql/quotas "The amount of available memory determines the connection limits for the instance." · 2026-10-01 |
| DS.schema_change | 3.1과 같음 (엔진) | | |
| DS.availability | HA 페일오버 약 60초, 기존 연결 종료 후 재연결 | | https://docs.cloud.google.com/sql/docs/mysql/high-availability "it will take approximately 60 seconds for connections to the primary instance to be reestablished" · 2026-10-01 |
| DS.multi_host_access | 가능 | | ⚠️근거없음 |
| DS.security | 2.7과 같음 | | |
| DS.regions | 서울 있음 | | 2.7 출처 |
| DS.scaling | 2.7과 같음 | | |
| DS.cost_floor | 2.7·2.8과 같음 (MySQL·PostgreSQL 같은 가격표, us-central1 기준, 서울 미확인) | | https://cloud.google.com/sql/pricing "MySQL and PostgreSQL pricing" · 2026-10-01 |

---

## 4. Vercel 마켓플레이스 현황

- **Vercel Postgres는 더 이상 없다.** 기존 DB는 2024-12에 Neon으로 자동 이전되었고, 새 프로젝트는 마켓플레이스 통합을 쓴다. https://vercel.com/docs/postgres "Vercel Postgres is no longer available. If you had an existing Vercel Postgres database, we automatically moved it to Neon in December 2024." (2026-10-01)
- 마켓플레이스 데이터베이스 범주의 관계형 제공자(2026-10-01): Postgres 계열 Neon, Supabase, Nile, Prisma Postgres, Thin Backend / MySQL 계열 TiDB Cloud. 그 외 Turso(libSQL) 등. https://vercel.com/marketplace/category/database (2026-10-01)
- 표에 넣지 않은 것: Nile, Thin Backend, TiDB Cloud — 바이브코더 저장소에서 마주치면 README §0 "표에 없는 구성 요소" 절차로 채운다.

---

## 5. 교체 계열 정보 (공통 재료)

이 절은 "교체 차이 표"의 재료다. 각 구성 요소 절의 "교체 계열 정보"는 여기를 가리킨다.

### 5.1 엔진 기준값 비교

| 항목 | SQLite | PostgreSQL | MySQL 8.4 (InnoDB) | 출처 |
|---|---|---|---|---|
| 동시 쓰기 | 1 (파일 잠금) | 다수 (행 잠금, MVCC) | 다수 (행 잠금 + 갭 잠금) | §1.1, §2.1, §3.1 |
| 기본 격리 수준 | SERIALIZABLE | READ COMMITTED | REPEATABLE READ | https://www.sqlite.org/isolation.html · https://www.postgresql.org/docs/current/transaction-iso.html · https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html |
| 행 잠금 문법 | 없음 (`FOR UPDATE` 무시) | `FOR UPDATE`, `SKIP LOCKED` | `FOR UPDATE` (세부 미열람) | Django DB 노트, PG sql-select |
| 기본 최대 연결 | 해당 없음 | 100 | 151 | https://dev.mysql.com/doc/refman/8.4/en/server-system-variables.html "Default Value 151" (max_connections) · 2026-10-01 |
| 외래 키 강제 | **기본 꺼짐** (연결마다 켜야 함) | 항상 | 항상 (InnoDB) | https://www.sqlite.org/foreignkeys.html |
| DDL 트랜잭션 | 트랜잭션 안에서 실행 (12단계 절차가 트랜잭션 사용) | 트랜잭션 블록 안에서 실행 가능 (예외: `CREATE INDEX CONCURRENTLY`) | **암묵적 커밋** | https://www.sqlite.org/lang_altertable.html "Start a transaction." · https://www.postgresql.org/docs/current/sql-createindex.html "a regular CREATE INDEX command can be performed within a transaction block, but CREATE INDEX CONCURRENTLY cannot" · https://dev.mysql.com/doc/refman/8.4/en/implicit-commit.html |
| 기본 SQL 모드·엄격성 | 동적 타이핑 (STRICT 테이블은 3.37+) | 정적 타이핑 | `STRICT_TRANS_TABLES` 포함 (8.4 기본) | https://www.sqlite.org/datatype3.html · https://dev.mysql.com/doc/refman/8.4/en/sql-mode.html "The default SQL mode in MySQL 8.4 includes these modes: ONLY_FULL_GROUP_BY, STRICT_TRANS_TABLES, …" |

PostgreSQL의 "트랜잭션 DDL 전반" 원칙을 직접 명시한 문서 문장은 이번에 찾지 못했다(위 인용은 `CREATE INDEX` 사례). 일반 원칙으로 쓰되 출처는 미확인으로 둔다. ⚠️근거없음

### 5.2 드라이버 (언어별 대표, 동기/비동기)

| 언어 | 드라이버 | 대상 DB | 동기/비동기 | 플레이스홀더 | 교체 시 주의 | 출처 (2026-10-01) |
|---|---|---|---|---|---|---|
| Node | `@libsql/client` | libSQL/Turso | 비동기 | SQLite 규칙 | 원격·임베디드 | §1.3 |
| Python | `sqlite3` (표준) | SQLite | **동기** (DB-API) | `qmark` (`?`) 고정 | `connect(timeout=5.0)` 기본 | https://docs.python.org/3/library/sqlite3.html "Hard-coded to "qmark"." · "connect(database, timeout=5.0, …)" |

### 5.3 ORM

| ORM | DB 전환 방식 | 교체 시 바뀌는 것 | 출처 (2026-10-01) |
|---|---|---|---|
| Django ORM | `DATABASES.ENGINE` | SQLite에서 `select_for_update()`는 효과 없음 → PG로 가면 실제 잠금이 걸림(동작 변화). SQLite는 `timeout`·`transaction_mode: IMMEDIATE`로 완화만 가능 | https://docs.djangoproject.com/en/stable/ref/databases/ "SQLite does not support the SELECT ... FOR UPDATE syntax. Calling it will have no effect." |

### 5.4 SQL 방언 차이 (코드가 바뀌는 지점)

| 항목 | SQLite | PostgreSQL | MySQL 8.4 | SQLite→PG | SQLite→MySQL | MySQL→PG | 출처 (2026-10-01) |
|---|---|---|---|---|---|---|---|
| 플레이스홀더 | `?`, `?NNN`, `:name`, `@name`, `$name` | 프로토콜 `$1` (드라이버별: `pg`·asyncpg `$1`, psycopg `%s`) | `?` (mysql2), `%s` (PyMySQL) | `?` → `$1` 또는 `%s` | 대부분 그대로 (`?`) | `?` → `$1` | https://www.sqlite.org/lang_expr.html "?NNN … :AAAA … @AAAA" · §5.2 |
| upsert | `INSERT … ON CONFLICT … DO UPDATE` (3.24+, PG 문법 기반) | `INSERT … ON CONFLICT` | `INSERT … ON DUPLICATE KEY UPDATE` | 거의 그대로 (PG는 충돌 대상 지정 필요) | 문법 교체 | 문법 교체 | https://www.sqlite.org/lang_upsert.html "UPSERT in SQLite follows the syntax established by PostgreSQL" · "PostgreSQL requires the second form, but SQLite accepts either." · https://www.postgresql.org/docs/current/sql-insert.html · https://dev.mysql.com/doc/refman/8.4/en/insert-on-duplicate.html |
| 자동 증가 | `INTEGER PRIMARY KEY` = ROWID 별칭, `AUTOINCREMENT`는 보통 불필요 | `serial`(표기 편의) 또는 표준 identity 열 | `AUTO_INCREMENT` | 타입·DDL 교체, 시퀀스 값 이전 후 재설정 필요 | `AUTO_INCREMENT` | `AUTO_INCREMENT` → identity/serial | https://www.sqlite.org/autoinc.html "a column with type INTEGER PRIMARY KEY is an alias for the ROWID" · https://www.postgresql.org/docs/current/datatype-numeric.html "smallserial, serial and bigserial are not true types" · https://dev.mysql.com/doc/refman/8.4/en/example-auto-increment.html |
| 날짜·시간 | 날짜 타입 없음, TEXT/REAL/INTEGER에 저장, `date()`·`datetime()`·`strftime()` | `timestamp(tz)`, `now()`(트랜잭션 시작 시각), `date_trunc` | `NOW()`, `DATE_FORMAT` | 문자열 날짜 → 타입 변환, `strftime` → `to_char`/`date_trunc` | `strftime` → `DATE_FORMAT` | `NOW()` 같음, `DATE_FORMAT` → `to_char` | https://www.sqlite.org/datatype3.html "SQLite does not have a storage class set aside for storing dates and/or times." · https://www.sqlite.org/lang_datefunc.html · https://www.postgresql.org/docs/current/functions-datetime.html "now ( ) → timestamp with time zone Current date and time (start of current transaction)" · https://dev.mysql.com/doc/refman/8.4/en/date-and-time-functions.html |
| 불리언 | 별도 타입 없음, 0/1 정수 | `boolean` | `BOOLEAN` = `TINYINT(1)` | `= 1` 비교·정수 컬럼을 `boolean`으로 | 그대로 (0/1) | `TINYINT(1)` → `boolean`, `= 1` 비교 수정 | https://www.sqlite.org/datatype3.html "Boolean values are stored as integers 0 (false) and 1 (true)." · https://www.postgresql.org/docs/current/datatype-boolean.html · https://dev.mysql.com/doc/refman/8.4/en/numeric-type-syntax.html "These types are synonyms for TINYINT(1)." |
| 타입 엄격성 | 동적 타이핑 (아무 값이나 저장, STRICT 테이블은 선택) | 정적 | 엄격 모드 기본 | 잘못 들어간 값(정수 컬럼의 문자열 등)이 이전 시 실패 → 데이터 정제 단계 필요 | 엄격 모드에서 같은 문제 | 비교적 적음 | https://www.sqlite.org/datatype3.html "SQLite uses a more general dynamic type system." · https://www.sqlite.org/stricttables.html |
| `LIKE` 대소문자 | ASCII는 대소문자 무시(기본), ASCII 밖은 구분 | **구분**, 무시하려면 `ILIKE` | 기본 콜레이션 `utf8mb4_0900_ai_ci`라 **무시** | 검색이 갑자기 대소문자 구분 → `ILIKE`/`lower()`/citext | 같음(무시) | `LIKE` → `ILIKE` | https://www.sqlite.org/lang_expr.html "SQLite only understands upper/lower case for ASCII characters by default." · https://www.postgresql.org/docs/current/functions-matching.html "The key word ILIKE can be used instead of LIKE to make the match case-insensitive" · https://dev.mysql.com/doc/refman/8.4/en/case-sensitivity.html "nonbinary string comparisons are case-insensitive by default" |
| `RETURNING` | 지원 (3.35+, PG 모델) | 지원 | **없음** (INSERT 문서에 RETURNING 없음) | 그대로 | `LAST_INSERT_ID()`·별도 조회로 | 오히려 단순화 가능 | https://www.sqlite.org/lang_returning.html "supported by SQLite since version 3.35" · https://www.postgresql.org/docs/current/sql-insert.html · https://dev.mysql.com/doc/refman/8.4/en/insert.html (RETURNING 없음) |
| 트랜잭션 DDL | 가능 | 가능 (예외 있음) | 불가 (암묵적 커밋) | 그대로 | 마이그레이션 중간 실패 시 부분 적용 남음 | 개선 | §5.1 |
| FK 강제 | 기본 꺼짐 | 항상 | 항상 | **숨어 있던 FK 위반이 이전 시 드러남** | 같음 | (PlanetScale FK 미사용이었다면 같음) | https://www.sqlite.org/foreignkeys.html |
| `ALTER TABLE` | 제한적 (12단계 재작성) | 대부분 지원, ACCESS EXCLUSIVE | INSTANT/INPLACE 온라인 DDL | 마이그레이션 도구 출력이 달라짐 | 같음 | 잠금 동작이 달라짐(`lock_timeout` 필요) | §1.1, §2.1, §3.1 |
| 행 잠금 | 없음 (DB 잠금) | `FOR UPDATE` | `FOR UPDATE` + 갭 잠금 | 직렬화가 사라지며 경쟁 조건 노출 → C2면 잠금 처방 | 같음 | 데드락 패턴 변화 | §5.1 |

### 5.5 데이터 이전 도구

| 도구 | 지원 경로 | 성격 | 출처 (2026-10-01) |
|---|---|---|---|
| AWS DMS | 소스: Oracle, SQL Server, PostgreSQL, MySQL 호환, MongoDB, S3 등. **SQLite 소스 없음** | 연속 복제 가능 | https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Source.html (소스 목록) |
| Google Database Migration Service | 동종: → Cloud SQL MySQL/PostgreSQL, → AlloyDB. 이종: Oracle·SQL Server → PG. **MySQL→PG, SQLite 미지원** | | https://docs.cloud.google.com/database-migration/docs/overview |
| Prisma Migrate | 스키마만 (새 공급자로 초기 마이그레이션 생성), 데이터 이전 없음 | | §5.3 Prisma 출처 |

---

## 6. 판정을 뒤집는 발견

1. **RDS for MySQL 8.0은 2026-08-01부터 확장 지원 요금이 붙는다.** 서울 $0.120/vCPU-시간, db.t4g.micro(2 vCPU)면 월 약 $175가 인스턴스 요금(약 $18)에 더해진다. MySQL 8.0 앱의 "가장 싼 후보"는 RDS MySQL 8.0이 아니다(8.4 업그레이드 또는 PostgreSQL 교체 비용과 비교).
2. **SQLite WAL은 쓰기 동시성을 높이지 않는다.** WAL은 읽기와 쓰기의 상호 차단만 없앤다(쓰기는 여전히 하나). LiteFS·Turso 기본 모드도 단일 쓰기다. Turso의 다중 쓰기(`BEGIN CONCURRENT`)는 2026-08 조기 미리보기다. C1이 중간 이상이면 SQLite 계열 안에서는 해결되지 않는다.
3. **서울 리전이 없는 서버리스 Postgres가 많다.** Neon(싱가포르), Prisma Postgres(도쿄), Turso(도쿄)는 서울 리전이 없다. 서울 리전이 있는 것: RDS·Aurora·Cloud SQL·AlloyDB·Supabase·PlanetScale(GCP). D5가 "한 지역(한국)"이면 후보에서 먼저 거른다.
4. **최악 RPO 값은 구성마다 크게 다르다.** RDS PITR 5분, Supabase PITR 2분(애드온 $100/월~), Supabase 일일 백업 24시간, Supabase Free·Prisma Postgres Free 백업 없음, Neon Free 복원 창 6시간, PlanetScale Postgres PITR은 현재 5분 전까지. 존 장애 RPO 0은 동기 복제(Multi-AZ, Cloud SQL HA, AlloyDB, Aurora 스토리지)만 준다.
5. **"HA 켬"의 비용 계단이 크다.** 서울 RDS PostgreSQL: Single-AZ 약 $21 → Multi-AZ 인스턴스 약 $42(60~120초) → Multi-AZ DB 클러스터 약 $580(35초 미만, t 계열 불가). Supabase는 관리형 HA를 문서로 확인하지 못했다(Multigres는 오픈소스 알파). F1 "짧아야 함"의 가장 싼 근거 있는 선택은 RDS Multi-AZ 인스턴스 또는 Cloud SQL HA다.

그 밖에 판정에 쓰이는 기본값: RDS API 생성 백업 보존 1일, Cloud Run → Cloud SQL 내장 연결 인스턴스당 100, Aurora Serverless v2의 `max_connections`는 최대 ACU로 정해지고 최소 0·0.5 ACU면 2,000 상한, Aurora Serverless v2 일시정지 재개 15초(하루 넘으면 30초 이상), `npx create-db`로 만든 Prisma Postgres는 24시간 뒤 삭제, node-sqlite3 저장소 보관(유지보수 중단).
