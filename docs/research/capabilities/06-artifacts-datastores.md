# 생성 산출물 표 — 06. 저장소 계열 (관계형·문서·키-값·BaaS·벡터)

삭제된 절: 20 PlanetScale Vitess, 31 Appwrite Cloud, 33 Convex, 35 Pinecone, 사유: 부적격 출처 (2026-10-02. 부적격 출처에 기댄 표 행과 줄도 지웠다. 남은 절 번호는 그대로)

- 작성일: 2026-10-01
- 짝 문서: [01-sql-databases.md](01-sql-databases.md), [02-nosql-baas.md](02-nosql-baas.md) (능력), [../dimensions.md](../dimensions.md) (요구)
- 목적: 에이전트가 구성 요소를 고른 뒤 **직접 생성할 산출물**(Terraform, docker-compose, 설정, 앱 쪽 계약)과 그것을 **검증할 명령**을 구성 요소마다 정리한다. 사용자는 생성물을 리뷰하지 못하므로, 각 항목은 "무엇을 생성하는가 + 무엇으로 확인하는가"를 짝으로 적는다.

## 범위

- 대상: 01·02 파일의 구성 요소 중 **교체·도입 대상이 될 수 있는 것** 35개. 관리형·클라우드 서비스, 자체 운영 PostgreSQL, "SQLite WAL로 유지" 처방의 설정 변경을 포함한다.
- 제외: 교체 전 출발점인 SQLite 파일 자체(01 §1.1). Vercel 마켓플레이스 현황(01 §4)은 구성 요소가 아니라서 뺐다.
- 01과 02에 같은 제품이 두 번 나오는 Supabase는 한 절(§13)로 합쳤다. RDS·Aurora·Cloud SQL처럼 변형마다 핵심 속성이 다른 것은 절을 나눴다.

## 출처 규칙과 확인 방법 (2026-10-01)

- 모든 출처는 2026-10-01에 직접 받아 읽은 원문이다. 이 작업 환경에서는 WebFetch 대신 `curl`로 같은 URL의 원문을 받아 읽었다. 확인하지 못한 값은 `미확인`으로 적었다.
- **Terraform Registry 문서**: Registry 문서 페이지(`registry.terraform.io/providers/<ns>/<name>/latest/docs/resources/<slug>`)는 JavaScript로 렌더링된다. 그래서 같은 원문을 Registry 공개 API(`/v2/provider-docs`)로 받아 인자 이름을 확인했다. 표에는 사람이 열 수 있는 Registry 페이지 URL을 적었다. 확인한 provider 버전은 다음과 같다.

  | provider | 버전 (2026-10-01 최신) | 등급(Registry tier) | 비고 |
  |---|---|---|---|
  | hashicorp/aws | 6.67.0 | official | |
  | hashicorp/google, google-beta | 8.5.0 | official | Realtime Database 인스턴스는 beta provider에만 있다 |
  | mongodb/mongodbatlas | 2.19.0 | partner-premier | |
  | appwrite/appwrite | 2.2.0 | partner-premier | |
  | pinecone-io/pinecone | 3.0.0 | partner | |
  | supabase/supabase | 1.11.0 | community | Supabase 조직 저장소 |
  | planetscale/planetscale | 1.11.0 | community | PlanetScale 조직 저장소 |
  | prisma/prisma-postgres | 0.2.0 | community | 저장소 마지막 푸시 2026-01-13 |
  | kislerdm/neon | 0.18.0 | community | **GitHub 저장소 보관(archived)** 상태 (§14) |
  | celest-dev/turso | 0.2.3 | community | **저장소 보관**, 마지막 릴리스 2024-09 (§2) |
  | cyrilgdn/postgresql | 1.27.0 | community | DB 안의 객체(확장·역할) 관리용 |

- 클라우드 서비스의 능력 값(페일오버 시간, 백업 기본값 등)은 01·02 파일에 출처가 있어서, 여기서는 절 번호로 가리킨다.

## 목차

- [요약표](#요약표)
- [0. 공통 재료](#0-공통-재료)
  - 0.1 PostgreSQL 앱 쪽 계약(드라이버별) · 0.2 풀러 경유 주의 · 0.3 비밀 주입 · 0.4 PostgreSQL 로컬 compose · 0.5 PostgreSQL 데이터 이전·검증 · 0.6 MySQL 공통 · 0.7 MongoDB 공통 · 0.8 생성물 검증 공통 절차
- 관계형
  - [1. SQLite — WAL로 유지 (설정 처방)](#1-sqlite--wal로-유지-설정-처방)
  - [2. libSQL · Turso Cloud](#2-libsql--turso-cloud) · [3. LiteFS](#3-litefs)
  - [4. PostgreSQL — 자체 운영](#4-postgresql--자체-운영-컨테이너vm)
  - [5. RDS PG Single-AZ](#5-postgresql--amazon-rds-single-az) · [6. RDS PG Multi-AZ 인스턴스](#6-postgresql--amazon-rds-multi-az-인스턴스) · [7. RDS PG Multi-AZ DB 클러스터](#7-postgresql--amazon-rds-multi-az-db-클러스터)
  - [8. Aurora PG 프로비저닝](#8-postgresql--amazon-aurora-프로비저닝) · [9. Aurora PG Serverless v2](#9-postgresql--amazon-aurora-serverless-v2)
  - [10. Cloud SQL PG 단일](#10-postgresql--cloud-sql-단일존) · [11. Cloud SQL PG HA](#11-postgresql--cloud-sql-ha리전) · [12. AlloyDB](#12-alloydb-for-postgresql)
  - [13. Supabase](#13-supabase-free--pro--team) · [14. Neon](#14-neon-free--launch--scale) · [15. PlanetScale Postgres](#15-planetscale-postgres) · [16. Prisma Postgres](#16-prisma-postgres)
  - [17. RDS MySQL](#17-mysql--amazon-rds-for-mysql) · [18. Aurora MySQL](#18-mysql--amazon-aurora-mysql) · [19. Cloud SQL MySQL](#19-mysql--cloud-sql-for-mysql) · 20. PlanetScale Vitess — 삭제됨(부적격 출처, 2026-10-02)
- 문서·키-값·BaaS·벡터
  - [21. Firestore Standard](#21-cloud-firestore--standard) · [22. Firestore Enterprise](#22-cloud-firestore--enterprisemongodb-호환) · [23. Realtime Database](#23-firebase-realtime-database)
  - [24. DynamoDB 단일 리전](#24-amazon-dynamodb--단일-리전) · [25. DynamoDB 글로벌 테이블](#25-amazon-dynamodb--글로벌-테이블)
  - [26. Atlas Free·Flex](#26-mongodb-atlas--freeflex) · [27. Atlas Dedicated](#27-mongodb-atlas--dedicatedm10) · [28. DocumentDB](#28-amazon-documentdb)
  - [29. Spanner](#29-google-cloud-spanner) · [30. Bigtable](#30-google-cloud-bigtable)
  - 31. Appwrite Cloud — 삭제됨(부적격 출처, 2026-10-02) · [32. PocketBase](#32-pocketbase--자체-호스팅) · 33. Convex — 삭제됨(부적격 출처, 2026-10-02)
  - [34. pgvector](#34-pgvector--postgres-확장) · 35. Pinecone — 삭제됨(부적격 출처, 2026-10-02)
- [36. 생성 자동화를 막는 발견](#36-생성-자동화를-막는-발견)

---

## 요약표

- **Terraform**: 공식 = HashiCorp 공식 provider. 파트너 = Registry partner 등급. 커뮤니티 = community 등급(제조사 조직 저장소 포함). 없음 = 사용 가능한 provider 없음.
- **핵심 속성 수**: 각 절 "요구 수준에 따라 바뀌는 핵심 속성"에 적은 항목 수.
- **자동화 불가 단계**: Terraform으로 만들 수 없어서 CLI·API·대시보드를 써야 하는 단계가 있는지 표시한다. "CLI"는 공식 CLI로 자동화할 수 있는 경우, "수동"은 대시보드에서만 할 수 있거나 API를 확인하지 못한 경우다.

| # | 구성 요소 | Terraform | 핵심 속성 수 | 자동화 불가 단계 |
|---|---|---|---|---|
| 1 | SQLite WAL 유지 (설정) | 해당 없음 (DB 리소스 없음, 컴퓨트 쪽 볼륨만) | 7 | 없음 (앱 설정·PRAGMA) |
| 2 | libSQL · Turso Cloud | 커뮤니티 (보관된 저장소) | 5 | 있음 — 토큰 발급 CLI, 플랜 수동 |
| 3 | LiteFS | 없음 (Fly provider 보관·비권장) | 5 | 있음 — flyctl·설정 파일 전부 |
| 4 | PostgreSQL 자체 운영 | VM만 공식 / DB 객체는 커뮤니티 | 8 | 있음 — HA·백업 직접 구축 |
| 5 | RDS PG Single-AZ | 공식 | 16 | 없음 |
| 6 | RDS PG Multi-AZ 인스턴스 | 공식 | 17 | 없음 |
| 7 | RDS PG Multi-AZ DB 클러스터 | 공식 | 14 | 없음 |
| 8 | Aurora PG 프로비저닝 | 공식 | 13 | 없음 |
| 9 | Aurora PG Serverless v2 | 공식 | 16 | 없음 |
| 10 | Cloud SQL PG 단일 | 공식 | 14 | 없음 |
| 11 | Cloud SQL PG HA | 공식 | 15 | 없음 |
| 12 | AlloyDB | 공식 | 12 | 없음 |
| 13 | Supabase | 커뮤니티 (제조사) | 9 | 있음 — 플랜·PITR·IPv4 애드온 수동, RLS는 CLI 마이그레이션 |
| 14 | Neon | 커뮤니티 (보관, 공식 이관 중) | 9 | 있음 — 플랜 수동 |
| 15 | PlanetScale Postgres | 커뮤니티 (제조사) | 8 | 있음 — **DB 생성 리소스 없음**(CLI) |
| 16 | Prisma Postgres | 커뮤니티 (제조사) | 3 | 있음 — 플랜·백업 수동 |
| 17 | RDS MySQL | 공식 | 14 | 없음 |
| 18 | Aurora MySQL | 공식 | 12 | 없음 |
| 19 | Cloud SQL MySQL | 공식 | 14 | 없음 |
| 21 | Firestore Standard | 공식 | 9 | 있음 — Blaze 전환 수동 |
| 22 | Firestore Enterprise | 공식 | 8 | 있음 — Blaze 전환 수동 |
| 23 | Realtime Database | 공식 (beta provider) | 4 | 있음 — 규칙 배포 CLI, 일일 백업 수동 |
| 24 | DynamoDB 단일 리전 | 공식 | 10 | 없음 |
| 25 | DynamoDB 글로벌 테이블 | 공식 | 16 | 없음 |
| 26 | Atlas Free·Flex | 파트너 | 6 | 없음 (조직·결제 연결은 수동) |
| 27 | Atlas Dedicated | 파트너 | 10 | 없음 (조직·결제 연결은 수동) |
| 28 | DocumentDB | 공식 | 12 | 없음 |
| 29 | Spanner | 공식 | 9 | 없음 |
| 30 | Bigtable | 공식 | 8 | 없음 |
| 32 | PocketBase | 없음 | 5 | 있음 — 관리자 생성·백업 설정 수동 |
| 34 | pgvector | 커뮤니티 (`postgresql_extension`) | 4 | 없음 (단, DB에 네트워크로 닿아야 함) |

- 합계 **31개 구성 요소**(원래 35개. #20 PlanetScale Vitess, #31 Appwrite, #33 Convex, #35 Pinecone은 능력 근거가 부적격 출처뿐이라 2026-10-02에 삭제): Terraform 공식 19, 파트너 2, 커뮤니티 7, 없음·해당 없음 3. 커뮤니티 8에는 VM만 공식이고 DB 객체는 커뮤니티 provider로 다루는 #4와 커뮤니티 provider로 확장만 켜는 #34가 포함된다.
- 자동화 불가 단계가 있는 것은 **11개**다.

---

## 0. 공통 재료

PostgreSQL 계열 15개, MySQL 4개, MongoDB 계열 4개는 앱 쪽 계약·로컬 개발·이전 절차가 대부분 같다. 각 절은 이 절을 가리키고, 다른 점만 적는다.

### 0.1 PostgreSQL 앱 쪽 계약 (드라이버별)

에이전트가 생성하는 환경변수 이름은 **`DATABASE_URL` 하나**를 기본으로 하고, 마이그레이션용 직결 주소가 따로 필요하면 `DIRECT_URL`을 추가한다(Prisma 문서의 관례). 연결 문자열은 `postgresql://USER:PASSWORD@HOST:PORT/DB` 형식이다. 비밀번호에 특수문자가 있으면 퍼센트 인코딩해야 한다.

| 드라이버·ORM | 연결 문자열 / 설정 | TLS | 풀러(트랜잭션 모드) 경유 시 | 출처 (2026-10-01) |
|---|---|---|---|---|
| Django | `DATABASES["default"]`: `ENGINE="django.db.backends.postgresql"`, `OPTIONS`는 드라이버 연결 인자로 그대로 전달 → `OPTIONS={"sslmode": "require"}` | `OPTIONS.sslmode` | `DISABLE_SERVER_SIDE_CURSORS = True`. 내장 풀(`OPTIONS.pool`)은 psycopg에서만 동작. `CONN_MAX_AGE` 기본 0(요청마다 연결) | https://docs.djangoproject.com/en/stable/ref/databases/ ("passes the content of OPTIONS as keyword arguments to the connection constructor", "DISABLE_SERVER_SIDE_CURSORS") · https://docs.djangoproject.com/en/stable/ref/settings/ (`CONN_MAX_AGE` "Default: 0") |

### 0.2 풀러 경유 주의 (C8)

- 트랜잭션 모드 풀러(Supabase 6543, Neon `-pooler`, PgBouncer `pool_mode=transaction`, RDS Proxy)를 쓰면 **세션 상태가 유지되지 않는다**. Neon 문서는 `SET`/`RESET`, `PREPARE`/`DEALLOCATE` 등을 제한 항목으로 든다(https://neon.com/docs/connect/connection-pooling). Supabase 문서도 "Transaction mode does not support prepared statements"라고 적는다(https://supabase.com/docs/guides/database/connecting-to-postgres). ⚠️근거없음
- 생성 규칙은 다음과 같다.
  1. 런타임은 풀러 URL, 마이그레이션은 직결 URL을 쓴다(환경변수 두 개).
  2. 0.1 표의 준비문 끄기 설정을 함께 넣는다.
  3. `statement_timeout` 같은 세션 설정은 앱의 `SET`이 아니라 DB·역할 수준 파라미터로 둔다.

### 0.3 비밀 주입 (F5)

- **AWS**: 기본은 `aws_db_instance.manage_master_user_password = true`다. RDS가 비밀번호를 만들어 Secrets Manager에 저장하고, 비밀 ARN은 `master_user_secret[0].secret_arn`으로 나온다.
  - RDS 문서에 따르면 이 비밀은 **기본 7일마다 교체된다**("rotates the secret every seven days by default"). 그래서 기동할 때 비밀번호를 환경변수로 한 번만 읽는 앱은 7일 뒤 인증에 실패할 수 있다. 앱이 연결 실패 시 비밀을 다시 읽게 하거나, 앱 전용 역할을 따로 만들어야 한다.
  - RDS가 관리하는 비밀의 JSON 키 구성은 이번에 확인하지 못했다(미확인). Secrets Manager의 교체 템플릿 형식에는 `host`·`username`·`password` 등이 있다. 그래서 `DATABASE_URL`은 Terraform 출력(`address`, `port`)과 비밀 값을 합쳐 만든다.
  - 직접 만드는 경우 `aws_secretsmanager_secret` + `aws_secretsmanager_secret_version.secret_string_wo`(쓰기 전용, 상태 파일에 남지 않음)를 쓴다.
  - 출처: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rds-secrets-manager.html · https://docs.aws.amazon.com/secretsmanager/latest/userguide/reference_secret_json_structure.html · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret_version
- **GCP**: `google_secret_manager_secret` + `google_secret_manager_secret_version`. Cloud Run 공식 예제는 `DB_USER`, `DB_PASS`, `DB_NAME`, `INSTANCE_UNIX_SOCKET`(또는 `INSTANCE_HOST`)를 환경변수로 받는다(https://cloud.google.com/sql/docs/postgres/connect-run). 컴퓨트 쪽에서 비밀을 환경변수로 연결하는 리소스는 컴퓨트 산출물 문서가 맡는다.
- **SaaS DB**(Supabase, Neon, PlanetScale, Prisma Postgres, Atlas, Turso, Pinecone): Terraform 출력의 민감 값(예: `neon_project.connection_uri`, `prisma-postgres_database.direct_url`)을 클라우드 비밀 저장소에 넣는다. 이렇게 하면 **Terraform 상태 파일에 평문 비밀이 남는다**. 원격 상태 저장소에 암호화와 접근 제한을 걸어야 한다.

### 0.4 PostgreSQL 로컬 compose (로컬과 운영의 메이저 버전 일치)

```yaml
services:
  db:
    image: postgres:17          # 운영 engine_version / database_version 의 메이저와 같게
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/pg_password
      POSTGRES_DB: app
    volumes:
      - pgdata:/var/lib/postgresql/data   # 17 이하. 18 이상은 /var/lib/postgresql 에 마운트
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d app"]
      interval: 5s
      retries: 10
    secrets: [pg_password]
```

- 이미지와 태그: Docker Hub 공식 `postgres`에 2026-10-01 기준 `18`(18.6), `17`(17.11), `16`(16.15), `15`(15.19) 태그가 있다. `19beta4`는 베타다.
- **PostgreSQL 18부터 이미지의 `PGDATA`가 `/var/lib/postgresql/18/docker`로 바뀌었다.** 그래서 마운트 위치도 달라진다. 17 이하에서 `/var/lib/postgresql`에 마운트하면 컨테이너를 다시 만들 때 데이터가 남지 않는다. 메이저 버전을 올릴 때 compose 템플릿도 함께 바꿔야 한다.
- 헬스체크: `pg_isready`는 연결을 받으면 0, 거부(기동 중 등)면 1, 응답이 없으면 2를 돌려준다.
- 비밀: 이미지는 `POSTGRES_PASSWORD_FILE` 등 `_FILE` 변형을 지원한다.
- 출처: https://hub.docker.com/_/postgres (태그 목록은 Docker Hub API로 확인) · https://github.com/docker-library/docs/blob/master/postgres/content.md · https://www.postgresql.org/docs/current/app-pg-isready.html (2026-10-01)

### 0.5 PostgreSQL 데이터 이전·검증

| 출발 → 도착 | 산출물 | 비고 | 출처 (2026-10-01) |
|---|---|---|---|
| Prisma 앱의 SQLite → PG | pgloader로 데이터를 옮기고, 스키마는 `migrations` 폴더를 새 공급자로 다시 만든다(01 §5.3) | 동적 타이핑 때문에 이전이 실패하면 정제 단계가 필요하다(01 §5.4) | 01 §5.3 |
| PG → 관리형 PG | `pg_dump --no-owner --no-privileges` → `psql`/`pg_restore` | Supabase 문서는 역할이 이전되지 않는다고 명시한다. 덤프·복원에는 세션 모드 풀러를 쓰라고 권고한다 | https://supabase.com/docs/guides/platform/migrating-to-supabase/postgres |
| MySQL·PG → RDS/Aurora (연속 복제) | `aws_dms_replication_instance`, `aws_dms_endpoint`(`ssl_mode` 기본 `none` → `require`), `aws_dms_replication_task`(`migration_type`, `table_mappings`, `replication_task_settings`) | `ValidationSettings.EnableValidation = true`로 켜면 DMS가 원본과 대상의 행을 하나씩 비교한다 | https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/dms_replication_task · https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Validating.html |
| PG·MySQL → Cloud SQL / AlloyDB | `google_database_migration_service_connection_profile`, `google_database_migration_service_migration_job` | 동종 이전만 지원한다(01 §5.5) | https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/database_migration_service_migration_job |

- **검증(에이전트가 자동 실행)**: 이전 전후로 테이블마다 다음 값을 비교한다.
  1. `SELECT count(*)`
  2. 기본 키 최댓값
  3. 기본 키 순서로 정렬한 행 문자열의 해시(예: PG `md5(string_agg(t::text, '' ORDER BY id))`)

  SQLite는 문자열 표현이 달라 행 해시를 그대로 비교할 수 없다. 숫자 열 합계와 행 수 비교로 대신한다. 이 검증 절차는 이 문서가 정한 것이고, 특정 도구 문서에서 가져온 것이 아니다.
- **네트워크 함정**: `publicly_accessible = false`(또는 사설 IP만)로 만든 DB에는 에이전트 PC에서 pgloader나 `pg_dump`로 직접 닿을 수 없다. 이전 작업은 VPC 안의 일회성 작업(컨테이너 태스크·Job)으로 실행해야 한다. 그래서 이전 작업을 실행할 컴퓨트 리소스도 생성 대상에 넣어야 한다.

### 0.6 MySQL 공통

- 로컬: 공식 이미지 `mysql:8.4`(8.4.11)와 `mysql:9.7`이 있다. 운영 8.4면 `8.4`를 쓴다. 헬스체크는 `mysqladmin ping`이다. 이 명령은 "Access denied"여도 0을 돌려준다(서버가 살아 있다는 뜻). 출처: https://hub.docker.com/_/mysql · https://dev.mysql.com/doc/refman/8.4/en/mysqladmin.html.
- 이전 → PG: pgloader(MySQL 소스 지원), DMS(MySQL 소스 지원).

### 0.7 MongoDB 공통 (Atlas, DocumentDB, Firestore Enterprise의 Mongo 호환)

- 연결 문자열: `mongodb+srv://…`(SRV, Atlas) 또는 `mongodb://…`. 출처: https://www.mongodb.com/docs/manual/reference/connection-string/.
- 로컬: 공식 이미지 `mongo:8.0`(8.0.32) / `mongo:7.0`이 있다. 이미지 기본값은 **인증 없음**이므로 `MONGO_INITDB_ROOT_USERNAME`/`_PASSWORD`를 지정한다. 헬스체크는 `mongosh --eval 'db.runCommand({ping:1})'`이다. 출처: https://github.com/docker-library/docs/blob/master/mongo/content.md.
- Atlas 로컬: Atlas CLI 로컬 배포 또는 Docker Compose 예제가 있다(https://www.mongodb.com/docs/atlas/cli/current/atlas-cli-deploy-docker/). 이미지 이름은 이번에 확인하지 못했다(미확인).
- 이전: `mongodump` → `mongorestore <연결 문자열> <dump>`(`--nsInclude`로 범위 지정). 출처: https://www.mongodb.com/docs/database-tools/mongorestore/.
- 검증: 컬렉션마다 `countDocuments()`와 표본 문서를 비교한다.

### 0.8 생성물 검증 공통 절차 (모든 절에 적용)

1. `terraform fmt -check`, `terraform validate`.
2. `terraform plan -out=tfplan -detailed-exitcode`. 종료 코드는 0 = 변경 없음, 2 = 변경 있음이다. 그다음 `terraform show -json tfplan`을 기계적으로 검사한다. 확인 포인트는 다음 세 가지다.
   - DB 리소스(`aws_db_instance`, `aws_rds_cluster`, `google_sql_database_instance`, `aws_dynamodb_table` …)의 `actions`에 `delete`가 들어가 있으면(교체 포함) **즉시 중단**한다.
   - 핵심 속성 값이 이 문서의 요구 수준 표와 같은지 확인한다.
   - 민감 값이 출력(`output`)에 평문으로 노출되지 않았는지 확인한다.
3. `checkov -d . --framework terraform`. 각 절에 적은 규칙 ID가 통과해야 한다. 요구 수준 때문에 일부러 끈 규칙(예: Single-AZ에서 CKV_AWS_157)은 `#checkov:skip=<ID>:<근거>` 주석으로 근거를 남긴다.
4. 배포 후 연결 확인: 앱과 같은 네트워크 위치에서 `psql "$DATABASE_URL" -c 'select 1'`(MySQL은 `mysql -e 'select 1'`, Mongo는 `mongosh "$URI" --eval 'db.runCommand({ping:1})'`)을 실행한다. 클라우드 API로 핵심 속성을 다시 읽어 Terraform 값과 대조한다.

- 출처: https://developer.hashicorp.com/terraform/cli/commands/validate · https://developer.hashicorp.com/terraform/cli/commands/plan (`-detailed-exitcode`) · https://www.checkov.io/2.Basics/CLI%20Command%20Reference.html · https://www.postgresql.org/docs/current/app-psql.html (2026-10-01)

---

## 1. SQLite — WAL로 유지 (설정 처방)

01 §6-2에 따르면 이 처방은 C1(쓰기 동시성)이 "낮음"이고 B2가 단일 인스턴스로 충분할 때만 성립한다. C1이 중간 이상이면 이 절이 아니라 §5 이후로 간다.

- **Terraform:** DB 리소스는 없다. 생성 대상은 컴퓨트 쪽의 **영속 볼륨과 인스턴스 1개 고정**이며, 컴퓨트 산출물 문서가 맡는다(CP.local_disk).
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `PRAGMA journal_mode=WAL`: 한 번 설정하면 DB 파일에 남는다("The WAL journaling mode is persistent").
  2. `PRAGMA busy_timeout=<ms>`: 연결마다 설정한다. C1 고통 흔적(`database is locked`)을 완화할 뿐 해결하지 않는다.
  3. `PRAGMA foreign_keys=ON`: 연결마다 설정한다(기본 꺼짐, 01 §1.1). 나중에 PG로 옮길 때 FK 위반이 한꺼번에 드러나는 것을 막는다.
  4. `PRAGMA synchronous`: C7이 "사용자 생성" 이상이면 `NORMAL`로 낮추지 않는다. 문서에 따르면 WAL + `NORMAL`은 일관성은 지키지만 "does lose durability"(전원 손실 시 커밋된 트랜잭션이 사라질 수 있음).
  5. Django: `OPTIONS = {"transaction_mode": "IMMEDIATE", "timeout": 20, "init_command": "PRAGMA …"}`. `IMMEDIATE`로 해야 타임아웃까지 기다린 뒤 실패한다.
  6. 백업 작업(F3): 주기적으로 `VACUUM INTO` 또는 Online Backup API로 사본을 만들어 외부 저장소에 둔다. 파일 복사로 백업하면 `-wal` 파일이 빠질 수 있다(01 §1.2).
  7. 인스턴스 수 최대 1: WAL은 "same host computer"에서만 동작한다. 볼륨 공유로 여러 인스턴스를 띄우지 않는다.
- **앱 쪽 계약:** DB 파일 경로 하나를 영속 볼륨 안 경로로 둔다. 환경변수 이름(예: `DATABASE_URL=file:/data/app.db`, SQLAlchemy `sqlite:////data/app.db`)은 관례이며 출처는 미확인이다. TLS·풀러는 해당 없음.
- **로컬 개발 대응:** compose 서비스가 필요 없다. 앱 컨테이너에 같은 경로로 볼륨을 마운트한다.
- **데이터 이전 단계:** 해당 없음(유지). 나중에 교체할 때는 0.5의 SQLite → PG 경로를 따른다.
- **검증 명령:** `sqlite3 /data/app.db 'PRAGMA journal_mode;'` → `wal`, `PRAGMA integrity_check;` → `ok`. 배포 계획에서 최대 인스턴스가 1인지 확인한다. Checkov 규칙 없음.
- **출처:** https://www.sqlite.org/pragma.html (미러 www3.sqlite.org에서 열람, "The WAL journaling mode is persistent", "WAL mode does lose durability") · https://www.sqlite.org/wal.html · https://docs.djangoproject.com/en/stable/ref/databases/ ("transaction_mode", "init_command") · 2026-10-01

## 2. libSQL · Turso Cloud

- **Terraform:** 제조사 공식 provider는 없다. 커뮤니티 provider는 두 개다.
  - `celest-dev/turso` 0.2.3: 저장소가 보관 상태이고 마지막 릴리스가 2024-09다. 리소스는 `turso_group`(`name`, `primary`, `locations`)과 `turso_database`(`group`, `name`, `size_limit`, `seed`)다.
  - `jpedroh/turso` 1.2.0: "unofficial", 2025-10.

  두 provider 모두 **인증 토큰 리소스가 없다**. 대안은 공식 Turso CLI(`turso db create`, `turso db tokens create <db> [--expiration 7d] [--read-only]`)다. 플랜(PITR 기간이 플랜에 묶임)은 대시보드에서 바꿔야 하는 **자동화 불가 단계**다. 이 문서의 권고는 보관된 provider 대신 CLI를 스크립트로 쓰는 것이다.
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `turso_group.primary`: D5. 서울이 없어 가장 가까운 곳이 `aws-ap-northeast-1`(도쿄)이다(01 §1.3).
  2. `turso_database.size_limit`: C6.
  3. 토큰 `--expiration`: F5. `never`를 피한다.
  4. 읽기 경로 전용 `--read-only` 토큰: F5.
  5. 플랜: F3. PITR이 Free 1일부터 Pro 90일까지이며 수동이다.
- **앱 쪽 계약:** `TURSO_DATABASE_URL`(`libsql://…` 또는 `turso://[db]-[org].turso.io`), `TURSO_AUTH_TOKEN`. 클라이언트는 `@libsql/client`의 `createClient({ url, authToken })`다. 임베디드 복제본은 `syncUrl`·`syncInterval`을 쓴다(01 §1.3). SQL 방언은 SQLite 그대로라 ORM 방언을 바꿀 필요가 없다. C1은 해결되지 않는다(01 §6-2).
- **로컬 개발 대응:** `turso dev`(기본 `http://127.0.0.1:8080`). 데이터를 남기려면 `--db-file local.db`를 준다. compose용 공식 이미지는 이번에 확인하지 못했다(미확인).
- **데이터 이전 단계:** `turso_database.seed`의 `type`이 `database`(기존 DB), `dump`(업로드한 덤프 URL)를 지원한다. SQLite 파일을 직접 올리는 CLI 옵션은 미확인이다. 검증은 테이블별 `count(*)` 비교다.
- **검증 명령:** `terraform validate`(provider를 쓸 때). Checkov 규칙 없음. 배포 후 앱 환경에서 `select 1`을 실행하고, 토큰 만료일을 기록한다.

## 3. LiteFS

01 §1.4에 따르면 LiteFS는 pre-1.0이고 관리형 백업이 끝났다. F3가 "분 단위" 이하면 부적합하다. 교체 후보로 권하지 않지만, 출발점에서 이미 쓰고 있는 경우를 위해 적는다.

- **Terraform:** 사실상 없다. `fly-apps/fly` provider는 저장소가 보관 상태이고 README가 "not currently maintained, and is not a recommended method of deployment"라고 밝힌다. 대안은 `flyctl` + `fly.toml` + `litefs.yml`이며, 전부 **Terraform 밖의 단계**다.
- **요구 수준에 따라 바뀌는 핵심 속성 (`litefs.yml`):**
  1. `fuse.dir`: 앱이 여는 DB 경로.
  2. `data.dir`: 볼륨 경로.
  3. `lease.type`: `consul`(자동 승격) 또는 `static`. F1.
  4. `proxy` 절: 쓰기 요청을 주 노드로 전달한다. 웹소켓은 지원하지 않는다(01 §1.4).
  5. Fly Machine autostop/autostart를 끈다: 켜 두면 데이터 손실 위험이 있다(01 §1.4).
- **앱 쪽 계약:** SQLite 그대로이며 DB 경로만 FUSE 마운트 아래로 바꾼다. 쓰기 라우팅은 프록시가 맡는다.
- **로컬 개발 대응:** 없음(FUSE 필요). 로컬은 일반 SQLite 파일로 대체한다.
- **데이터 이전 단계:** 기존 SQLite 파일을 가져오는 명령은 미확인이다. 백업은 직접 구성해야 한다(오프사이트 사본).
- **검증 명령:** 미확인. Checkov 규칙 없음.

## 4. PostgreSQL — 자체 운영 (컨테이너·VM)

- **Terraform:** DB 자체를 다루는 리소스는 없다. VM(`aws_instance`/`google_compute_instance`)과 디스크는 컴퓨트 산출물 문서가 맡는다. DB 안의 객체(데이터베이스, 역할, 확장)는 커뮤니티 `cyrilgdn/postgresql`의 `postgresql_extension` 등으로 다룰 수 있지만, **Terraform 실행 위치에서 DB로 네트워크 연결이 돼야 한다.** 자동 페일오버(Patroni 등)와 WAL 아카이브는 직접 구축해야 하므로 **자동화 불가 단계(직접 설계)**가 남는다(01 §2.1).
- **요구 수준에 따라 바뀌는 핵심 속성 (compose·`postgresql.conf`):**
  1. 이미지 메이저 고정(`postgres:17` 등): 운영과 로컬을 같게 한다.
  2. 데이터 볼륨 경로: 18 이상은 `/var/lib/postgresql`, 17 이하는 `/var/lib/postgresql/data`(0.4).
  3. `max_connections`: C8. 서버 시작 시에만 바뀐다(01 §2.1).
  4. `statement_timeout`: A2·C8.
  5. `lock_timeout`: C9. 기본 0이면 DDL이 잠금을 무한히 기다린다(01 §2.1).
  6. `idle_in_transaction_session_timeout`: C8.
  7. `archive_mode`·`archive_command`·`archive_timeout`: F3. 최악 RPO가 이 값으로 정해진다(01 §2.1).
  8. 포트 비공개: 호스트 포트를 퍼블릭으로 바인딩하지 않는다. 원격 접속이 필요하면 `ssl=on`. F5.
- **앱 쪽 계약:** 0.1과 같다. 같은 호스트의 compose 네트워크 안이라면 TLS 없이 서비스 이름(`db:5432`)으로 접속한다.
- **로컬 개발 대응:** 0.4와 같다(운영과 같은 compose 파일을 쓴다).
- **데이터 이전 단계:** 0.5와 같다. SQLite에서 옮기면 pgloader를 같은 compose 네트워크 안의 일회성 서비스로 실행한다.
- **검증 명령:** `docker compose config`(정적 검사), `docker compose up -d` 후 `docker compose ps`가 healthy인지 확인, `psql -c 'show max_connections; show lock_timeout;'`. 백업이 실제로 복원되는지 리허설한다(복원 → `count(*)` 비교). Checkov 규칙 없음(Terraform 리소스 없음).

## 5. PostgreSQL — Amazon RDS, Single-AZ

- **Terraform (hashicorp/aws 6.67.0):** `aws_db_instance`, `aws_db_subnet_group`, `aws_db_parameter_group`, `aws_security_group` + `aws_vpc_security_group_ingress_rule`(앱 SG에서만 5432 허용). 선택 리소스는 `aws_kms_key`, `aws_secretsmanager_secret`·`_version`(직접 관리 시), `aws_db_proxy`(C8이 "요청마다 연결"일 때)다. 자동화 불가 단계는 없다.
- **요구 수준에 따라 바뀌는 핵심 속성 (Registry 인자 이름):**
  1. `engine = "postgres"`, `engine_version = "17"`: 메이저만 주면 `auto_minor_version_upgrade`가 켜진 상태에서 접두어로 쓸 수 있다. RDS 표준 지원 종료일은 PG13이 2026-02-28로 이미 지났고, PG14가 2027-02-28, PG17이 2030-02-28이다. 신규는 17 또는 18로 둔다(G3).
  2. `engine_lifecycle_support = "open-source-rds-extended-support-disabled"`: **Terraform 기본값은 `open-source-rds-extended-support`**(연장 지원 자동 가입)다. 끄면 표준 지원 종료 후 자동 메이저 업그레이드가 된다(AWS 문서). G3과 F4 사이의 선택이다.
  3. `backup_retention_period >= 7`: C7·F3. **Registry 문서의 기본값은 `0`**(백업 꺼짐)이고, 01 §2.2의 AWS 문서는 "API·CLI 생성 시 1일"이다. 두 값이 [충돌]하므로 반드시 명시한다.
  4. `backup_window`: 업무 시간 밖(UTC)으로 둔다. D4.
  5. `deletion_protection = true`: 기본 `false`.
  6. `skip_final_snapshot = false` + `final_snapshot_identifier`: 삭제 시 스냅샷을 남긴다.
  7. `delete_automated_backups = false`: 기본 `true`라서 인스턴스를 삭제하면 자동 백업도 사라진다. C7.
  8. `publicly_accessible = false`: 기본 `false`지만 명시한다. F5.
  9. `storage_encrypted = true`(+ `kms_key_id`): **기본 `false`**. 생성 후 바꿀 수 없다(01 §2.2 "암호화는 생성 시 선택"). F5.
  10. `storage_type = "gp3"`, `allocated_storage`, `max_allocated_storage`: `storage_type` 기본은 `gp2`다. `max_allocated_storage`를 정하면 스토리지 자동 확장이 켜진다. C6.
  11. `manage_master_user_password = true`: 0.3 참조. 7일 교체 주의.
  12. `parameter_group_name` → `aws_db_parameter_group`(`family = "postgres17"`): `rds.force_ssl = 1`(PG15 이상 기본 1), `statement_timeout`, `lock_timeout`, `idle_in_transaction_session_timeout`, `log_min_duration_statement`를 넣는다. 정적 파라미터(`max_connections` 등)는 `apply_method = "pending-reboot"`이다. Registry 문서는 AWS 기본값과 `apply_method`가 엇갈리면 오류가 난다고 경고한다.
  13. `ca_cert_identifier = "rds-ca-rsa2048-g1"`: 앱 TLS 검증용 번들은 `global-bundle.pem`이다.
  14. `apply_immediately`: 인스턴스 클래스 변경은 중단을 만든다(01 §2.2). F4가 "불가"면 `false`로 두고 유지보수 창에 적용한다.
  15. `iam_database_authentication_enabled`: F5가 높을 때 켠다.
  16. `performance_insights_enabled`, `monitoring_interval`, `enabled_cloudwatch_logs_exports = ["postgresql"]`: 운영 가시성용이며 Checkov 대상이다.
- **앱 쪽 계약:** 0.1과 같다.
  - `DATABASE_URL=postgresql://USER:PASS@<aws_db_instance.address>:5432/<db>?sslmode=verify-full&sslrootcert=/app/global-bundle.pem`
  - PG15 이상은 `rds.force_ssl` 기본값이 1이라 **TLS 없는 연결이 거부된다.** 로컬에서 TLS 없이 쓰던 앱은 운영에서 처음 실패한다. CA 번들 `https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem`을 이미지에 포함한다.
  - 비밀은 Secrets Manager → 컴퓨트 환경변수 경로로 주입한다(0.3).
- **로컬 개발 대응:** `postgres:<engine_version 메이저>`(0.4). 운영 TLS 강제를 로컬에서 재현하지 않으므로 `sslmode`를 환경변수로 분리한다.
- **데이터 이전 단계:** 0.5와 같다. 대상이 VPC 안이므로 이전 작업도 VPC 안에서 실행한다.
- **검증 명령:**
  - `terraform plan`에서 `aws_db_instance`에 `forces replacement`가 없어야 한다. `storage_encrypted`, `engine`, 서브넷 그룹을 바꾸면 교체가 일어난다.
  - Checkov:
    - 통과해야 하는 규칙: CKV_AWS_16(암호화), CKV_AWS_17(비공개), CKV_AWS_133(백업), CKV_AWS_293(삭제 보호), CKV_AWS_211(CA), CKV_AWS_226(마이너 업그레이드), CKV_AWS_161(IAM 인증), CKV_AWS_129(로그), CKV_AWS_118(향상된 모니터링), CKV_AWS_353·354(PI), CKV2_AWS_30(쿼리 로깅), CKV2_AWS_60(스냅샷 태그 복사), CKV2_AWS_69(전송 중 암호화)
    - 근거와 함께 건너뛰는 규칙: CKV_AWS_157(Multi-AZ, 이 변형에서는 의도적으로 끔)
  - 배포 후:
    - `aws rds describe-db-instances --db-instance-identifier <id> --query 'DBInstances[0].[MultiAZ,BackupRetentionPeriod,DeletionProtection,PubliclyAccessible,StorageEncrypted,EngineVersion]'`로 핵심 속성을 다시 읽는다.
    - VPC 안에서 `psql "$DATABASE_URL" -c 'select 1'`을 실행한다.
    - `sslmode=disable`로 접속이 **거부되는지** 확인한다.
- **출처:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/db_instance · …/db_parameter_group · …/db_subnet_group · …/vpc_security_group_ingress_rule · …/db_proxy · https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/PostgreSQL.Concepts.General.SSL.html ("rds.force_ssl parameter default value is 1 (on) for RDS for PostgreSQL version 15 and later") · https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.SSL.html (global-bundle.pem) · https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/extended-support.html · https://docs.aws.amazon.com/AmazonRDS/latest/PostgreSQLReleaseNotes/postgresql-release-calendar.html · https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rds-secrets-manager.html · Checkov 색인 · 2026-10-01

## 6. PostgreSQL — Amazon RDS, Multi-AZ 인스턴스

- **Terraform:** §5와 같다.
- **요구 수준에 따라 바뀌는 핵심 속성:** §5의 16개에 다음 하나를 더한다.
  - `multi_az = true`: F1이 "짧아야 함"일 때 켠다. 페일오버는 60~120초이고, 대기 인스턴스는 읽기를 받지 않는다(01 §2.3).

  §5의 `apply_immediately` 판단이 완화된다. 클래스를 바꿀 때 대기 인스턴스가 중단을 줄이지만, 그 수치는 01 §2.3에서 미확인이다.
- **앱 쪽 계약:** §5에 더해, 페일오버가 DNS 변경으로 이뤄지므로 다음을 생성한다.
  - 연결 풀의 재연결 설정: 사전 핑과 연결 수명 제한(SQLAlchemy `pool_pre_ping=True`·`pool_recycle`, node-postgres는 오류 시 재연결).
  - JVM이면 DNS TTL 60초 이하(01 §2.3).
- **로컬 개발 대응:** §5와 같다.
- **데이터 이전 단계:** §5와 같다.
- **검증 명령:** §5와 같고, CKV_AWS_157이 **통과**해야 한다. 배포 후 `MultiAZ = true`를 확인한다. 장애 조치 리허설은 `aws rds reboot-db-instance --force-failover`로 하고, 앱이 자동으로 재연결하는지 본다.
- **출처:** §5 출처 · 01 §2.3 · 2026-10-01

## 7. PostgreSQL — Amazon RDS, Multi-AZ DB 클러스터

- **Terraform:** `aws_rds_cluster`(`engine = "postgres"`. Registry 문서에 따르면 `mysql`·`postgres`가 Multi-AZ DB 클러스터다), `aws_rds_cluster_parameter_group`, `aws_db_subnet_group`, SG. 인스턴스 리소스는 따로 두지 않는다(`db_cluster_instance_class`로 지정).
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `db_cluster_instance_class`: Multi-AZ DB 클러스터에서 필수다. t 계열은 쓸 수 없고 서울 최저는 m6gd.large다(01 §2.4). G3.
  2. `storage_type`: 필수이며 **기본값이 `io1`**이다. gp3를 쓰려면 명시한다(`io1`, `io2`, `gp3`). 바꾸면 교체된다. G3.
  3. `iops`: Multi-AZ DB 클러스터는 `storage_type`과 함께 필수다.
  4. `allocated_storage`: 필수.
  5. `engine_version` + `engine_lifecycle_support`: §5와 같다.
  6. `backup_retention_period`: 기본 1, 범위 1~35. 7 이상으로 둔다.
  7. `deletion_protection = true`: 기본 `false`.
  8. `storage_encrypted = true`: provisioned 기본값이 `false`다.
  9. `manage_master_user_password = true`.
  10. `db_cluster_parameter_group_name`: §5의 파라미터와 같은 내용을 넣는다.
  11. `availability_zones`: 3개를 명시한다. Registry 문서에 따르면 3개보다 적게 주면 다음 apply에서 교체 차이가 생긴다.
  12. `final_snapshot_identifier`: 생략하면 최종 스냅샷이 만들어지지 않는다(Registry 문서).
  13. `iam_database_authentication_enabled`.
  14. `copy_tags_to_snapshot`, `enabled_cloudwatch_logs_exports`.
- **앱 쪽 계약:** 쓰기는 `endpoint`, 읽기는 `reader_endpoint`다. 읽기 라우팅을 쓰려면 ORM 설정이 필요하다(Prisma `readReplicas`, Django `DATABASE_ROUTERS`, 01 §2.4). 리더는 반동기라 복제 지연만큼 오래된 값을 읽을 수 있다. 쓰기 직후 읽는 경로(C3)는 쓰기 엔드포인트로 고정한다.
- **로컬 개발 대응:** §5와 같다(로컬은 단일 인스턴스).
- **데이터 이전 단계:** §5와 같다.
- **검증 명령:**
  - Checkov: CKV_AWS_96(이름은 Aurora지만 `aws_rds_cluster` 대상 암호화 검사), CKV_AWS_133, CKV_AWS_139(삭제 보호), CKV_AWS_162(IAM 인증), CKV_AWS_313(태그 복사), CKV_AWS_324(로그), CKV_AWS_327(CMK), CKV2_AWS_8(AWS Backup 계획), CKV2_AWS_27(PG 쿼리 로깅). CKV_AWS_326(backtracking)은 Aurora MySQL 전용이라 건너뛴다.
  - 배포 후: `aws rds describe-db-clusters --query 'DBClusters[0].[MultiAZ,BackupRetentionPeriod,DeletionProtection,StorageEncrypted,StorageType]'`.
- **출처:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/rds_cluster · …/rds_cluster_parameter_group · Checkov 색인 · 01 §2.4 · 2026-10-01

## 8. PostgreSQL — Amazon Aurora, 프로비저닝

- **Terraform:** `aws_rds_cluster`(`engine = "aurora-postgresql"`), `aws_rds_cluster_instance`(쓰기 1 + 리더 N), `aws_rds_cluster_parameter_group`, `aws_db_parameter_group`(인스턴스 수준), `aws_db_subnet_group`, SG.
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `aws_rds_cluster_instance` 개수: F1. 복제본이 있으면 승격이 60초 미만, 없으면 재생성에 10분 미만이 걸린다(01 §2.5). "짧아야 함"이면 2개 이상이다.
  2. `aws_rds_cluster_instance.instance_class`: 최소 `db.t4g.medium`(01 §2.5). G3.
  3. `promotion_tier`: 기본 0이며, 낮을수록 먼저 승격된다.
  4. `storage_type`: `""`(Standard, I/O 과금) 또는 `aurora-iopt1`(I/O-Optimized). G3·C4.
  5. `engine_version` + `engine_lifecycle_support`: Aurora에도 적용된다(Registry 문서).
  6. `backup_retention_period`: 기본 1이며 7 이상으로 둔다.
  7. `deletion_protection = true`.
  8. `storage_encrypted = true`: provisioned 기본값이 `false`다.
  9. `manage_master_user_password = true`.
  10. `db_cluster_parameter_group_name`: §5의 파라미터와 같다.
  11. `publicly_accessible = false`: 인스턴스 리소스 쪽 인자다.
  12. `enable_http_endpoint`: Data API. 서버리스 컴퓨트에서 TCP 연결 대신 쓸 때 켠다(01 §2.5).
  13. `final_snapshot_identifier`.
- **앱 쪽 계약:** 0.1과 같다. `endpoint`(쓰기)와 `reader_endpoint`를 쓴다. Data API를 쓰면 드라이버가 AWS SDK로 바뀐다(01 §2.5).
- **로컬 개발 대응:** `postgres:<Aurora 엔진 메이저>`. Aurora 고유 기능(Data API)은 로컬에 대응물이 없다(미확인).
- **데이터 이전 단계:** §5와 같다.
- **검증 명령:**
  - Checkov: §7의 클러스터 규칙에 인스턴스 규칙을 더한다. 인스턴스 규칙은 CKV_AWS_17, CKV_AWS_118, CKV_AWS_226, CKV_AWS_353·354다. CKV_AWS_388(Aurora PG 로컬 파일 읽기 취약점)은 색인상 `aws_db_instance` 대상이다.
  - 배포 후: `aws rds describe-db-clusters`로 `DBClusterMembers` 수와 `IsClusterWriter`를 확인한다. `aws rds failover-db-cluster`로 리허설한다.
- **출처:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/rds_cluster · …/rds_cluster_instance · Checkov 색인 · 01 §2.5 · 2026-10-01

## 9. PostgreSQL — Amazon Aurora Serverless v2

- **Terraform:** §8과 같다. `aws_rds_cluster`에 `serverlessv2_scaling_configuration` 블록을 넣고, `aws_rds_cluster_instance.instance_class = "db.serverless"`로 둔다. Registry 문서에 따르면 이 블록은 `engine_mode = "provisioned"`(기본값)일 때만 유효하다.
- **요구 수준에 따라 바뀌는 핵심 속성:** §8의 13개 중 `instance_class`를 `"db.serverless"`로 고정하고, 다음 셋을 더한다.
  1. `serverlessv2_scaling_configuration.min_capacity`: 0~256, 0.5 단위다. **0이면 자동 일시정지**가 된다. 재개에 약 15초가 걸린다(01 §2.6). F1이 "짧아야 함"이면 0.5 이상이다. D4·G3.
  2. `max_capacity`: C8. `max_connections`가 최대 ACU로 정해진다(01 §2.6).
  3. `seconds_until_auto_pause`: 300~86400. `min_capacity = 0`일 때 쓴다.
- **앱 쪽 계약:** §8과 같다. 일시정지 재개 중 첫 연결이 지연되므로 연결 타임아웃을 20초 이상으로 둔다(01 §2.6의 15초 근거). RDS Proxy나 열린 연결이 있으면 일시정지되지 않는다(01 §2.6). 상시 풀을 가진 앱은 0 ACU로 비용을 아낄 수 없다.
- **로컬 개발 대응:** §8과 같다.
- **데이터 이전 단계:** §5와 같다. 대량 적재 중에는 `max_capacity`까지 확장되므로 비용 상한을 확인한다.
- **검증 명령:** §8과 같다. 배포 후 `describe-db-clusters`의 `ServerlessV2ScalingConfiguration`을 확인한다. 유휴 후 재개 시간을 측정해 앱 타임아웃보다 짧은지 본다.
- **출처:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/rds_cluster (`serverlessv2_scaling_configuration`, "range of `0` up to `256` in steps of `0.5`", `seconds_until_auto_pause` "300 through 86400") · 01 §2.6 · 2026-10-01

## 10. PostgreSQL — Cloud SQL, 단일(존)

- **Terraform (hashicorp/google 8.5.0):** `google_sql_database_instance`, `google_sql_database`, `google_sql_user`, `google_secret_manager_secret`·`_version`. 사설 IP를 쓰면 `google_compute_global_address`와 `google_service_networking_connection`을 추가한다. API 활성화는 `google_project_service`로 한다.
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `database_version = "POSTGRES_17"`: `POSTGRES_18`까지 지원한다. EOL 메이저는 2025-05-01부터 extended support 요금이 붙는다(Cloud SQL 문서). G3.
  2. `settings.edition = "ENTERPRISE"`: **명시가 필수다.** 생략하면 `POSTGRES_16` 이상은 `ENTERPRISE_PLUS`가 기본이다. 이때 `db-f1-micro`·`db-g1-small`·`db-custom-*` 같은 tier는 "Invalid Tier … for (ENTERPRISE_PLUS) Edition" 오류로 **생성에 실패한다.** 01 §0의 최소 비용($7.7+)은 Enterprise에서만 성립한다. G3.
  3. `settings.tier`: 공유 코어는 SLA 대상이 아니다(01 §2.7).
  4. `settings.availability_type = "ZONAL"`: 기본값이다.
  5. `settings.backup_configuration.enabled = true` + `start_time`.
  6. `settings.backup_configuration.point_in_time_recovery_enabled = true`: 생성 후 켜면 DB가 재시작된다. F3.
  7. `transaction_log_retention_days`: Enterprise 1~7, Enterprise Plus 최대 35.
  8. `backup_retention_settings.retained_backups` / `retention_unit`: C7.
  9. `deletion_protection = true`: **Terraform 수준**이며, 미설정이면 destroy가 실패한다.
  10. `settings.deletion_protection_enabled = true`: **GCP 수준**이며, 콘솔·gcloud 삭제도 막는다. 두 인자는 별개다.
  11. `settings.ip_configuration.ipv4_enabled = false` + `private_network`: F5. 둘 중 하나는 반드시 켜야 한다.
  12. `settings.ip_configuration.ssl_mode = "ENCRYPTED_ONLY"`: **기본값은 `ALLOW_UNENCRYPTED_AND_ENCRYPTED`**다. F5.
  13. `settings.database_flags { name, value }`: `max_connections` 등. Cloud SQL이 허용하는 플래그 이름(예: `statement_timeout`)은 이번에 확인하지 못했다(미확인). C8·C9.
  14. `disk_autoresize`: 기본 `true`. `disk_size`를 함께 주면 이후 apply가 디스크를 줄이려다 **인스턴스 삭제를 시도한다.** `lifecycle.ignore_changes = [settings[0].disk_size]`가 필요하다(Registry 문서 경고).
- **앱 쪽 계약:**
  - Cloud Run: 유닉스 소켓 `/cloudsql/<connection_name>`을 쓴다. 일부 드라이버는 `/.s.PGSQL.5432` 접미사를 직접 붙여야 한다. 공식 예제의 환경변수는 `DB_USER`, `DB_PASS`, `DB_NAME`, `INSTANCE_UNIX_SOCKET`이다. 소켓 연결은 "automatically encrypted"다. Prisma는 `?host=/cloudsql/<connection_name>` 형식이다.
  - **Cloud Run 인스턴스당 Cloud SQL 연결 상한은 100이다.** 풀 크기 × 인스턴스 수를 계산한다(01 §2.8).
  - VM·GKE: 사설 IP + `sslmode=require` 또는 Cloud SQL Auth Proxy·언어 커넥터.
- **로컬 개발 대응:** `postgres:<메이저>`(0.4). 소켓 경로 대신 TCP로 쓰도록 `DB_HOST`/`INSTANCE_UNIX_SOCKET` 둘 중 하나만 설정하는 분기 코드를 생성한다.
- **데이터 이전 단계:** 0.5와 같다. 동종 연속 이전은 Database Migration Service 리소스로 한다.
- **검증 명령:**
  - `terraform plan`에서 `edition`과 `tier` 조합 오류는 plan이 아니라 **apply 시점**에 난다(Registry 문서 "fails at create time"). 그래서 정적 규칙으로 "PG16 이상 + 공유 코어 tier면 `edition = "ENTERPRISE"` 필수"를 따로 검사한다.
  - Checkov:
    - 일반: CKV_GCP_6(SSL), CKV_GCP_11(공개 안 됨), CKV_GCP_14(백업), CKV_GCP_60(공용 IP 없음), CKV_GCP_79(최신 메이저)
    - PG 플래그: CKV_GCP_51~57, CKV_GCP_108~111, CKV2_GCP_13~17
  - 배포 후: `gcloud sql instances describe <name> --format='value(settings.edition,settings.availabilityType,settings.backupConfiguration.pointInTimeRecoveryEnabled,settings.ipConfiguration.sslMode,settings.deletionProtectionEnabled)'`.
- **출처:** https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/sql_database_instance · …/sql_database · …/sql_user · …/secret_manager_secret · …/service_networking_connection · …/compute_global_address · https://cloud.google.com/sql/docs/postgres/connect-run · https://cloud.google.com/sql/docs/postgres/configure-ssl-instance · https://cloud.google.com/sql/docs/postgres/extended-support · https://cloud.google.com/sql/docs/editions-intro · Checkov 색인 · 2026-10-01

## 11. PostgreSQL — Cloud SQL, HA(리전)

- **Terraform:** §10과 같다.
- **요구 수준에 따라 바뀌는 핵심 속성:** §10의 14개에 다음 하나를 더한다.
  - `settings.availability_type = "REGIONAL"`: Registry 문서는 "ensure that `settings.backup_configuration.enabled` is set to `true`"와 PG의 `point_in_time_recovery_enabled = true`를 **전제 조건**으로 적는다. 페일오버는 약 60초다(01 §2.8).

  F4가 "불가"인 경우의 추가 판단도 있다. Enterprise Plus는 계획 작업 중단이 1초 미만이지만(01 §2.8, Cloud SQL 에디션 문서 "Sub-second downtime"), 공유 코어 tier를 쓸 수 없어 비용 계단이 생긴다.
- **앱 쪽 계약:** §10과 같다. 페일오버 뒤 재연결 설정은 §6과 같다.
- **로컬 개발 대응:** §10과 같다.
- **데이터 이전 단계:** §10과 같다.
- **검증 명령:** §10과 같다. 배포 후 `availabilityType = REGIONAL`을 확인한다. 리허설은 `gcloud sql instances failover <name>`이다(명령은 gcloud 참조 기준, 세부 옵션 미확인).
- **출처:** §10 출처 · 01 §2.8 · 2026-10-01

## 12. AlloyDB for PostgreSQL

- **Terraform:** `google_alloydb_cluster`, `google_alloydb_instance`(`instance_type = "PRIMARY"`, 읽기는 `"READ_POOL"`), 사설 서비스 접근(`google_compute_global_address` + `google_service_networking_connection`) 또는 PSC, `google_secret_manager_secret`.
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `google_alloydb_cluster.database_version`.
  2. `continuous_backup_config.enabled`: 미설정이면 `true`다.
  3. `continuous_backup_config.recovery_window_days`: 미설정이면 14일이다. F3·C7.
  4. `automated_backup_policy`: **기본 비활성**. 장기 보존이 필요하면 `time_based_retention` 또는 `quantity_based_retention`과 함께 켠다.
  5. `deletion_protection = true`: Terraform 수준이며, 미설정이면 삭제가 실패한다.
  6. `deletion_policy`: `PREVENT`/`DEFAULT`/`FORCE`/`ABANDON`.
  7. `initial_user.password`: 비밀 저장소 값을 참조한다.
  8. `network_config.network` 또는 `psc_config`: F5.
  9. `google_alloydb_instance.availability_type`: **기본 `REGIONAL`**(HA)이다. 비용을 줄이려면 `ZONAL`을 명시한다. F1↔G3.
  10. `machine_config.cpu_count`: G3.
  11. `client_connection_config.ssl_config.ssl_mode = "ENCRYPTED_ONLY"`, `require_connectors`: F5.
  12. `network_config.enable_public_ip = false`.
- **앱 쪽 계약:** 0.1과 같다. 사설 IP + TLS, 또는 AlloyDB Auth Proxy·언어 커넥터(IAM 인증)를 쓴다. 커넥터를 쓰면 드라이버 생성 코드가 바뀐다(커넥터 라이브러리 → 드라이버). 세부 API는 미확인이다.
- **로컬 개발 대응:** `postgres:<database_version 메이저>`. AlloyDB 고유 기능(컬럼형 엔진 등)은 로컬에 대응물이 없다.
- **데이터 이전 단계:** 0.5와 같다. Google DMS가 → AlloyDB 동종 이전을 지원한다(01 §5.5).
- **검증 명령:** Checkov 색인에 AlloyDB 규칙은 **없다**. 위 속성을 plan JSON에서 직접 검사한다. 배포 후 `gcloud alloydb clusters describe <cluster> --region <r>`로 백업 설정을 확인한다.
- **출처:** https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/alloydb_cluster ("AutomatedBackupPolicy is disabled by default", "defaults to 14 days") · …/alloydb_instance ("Defaults to REGIONAL") · https://cloud.google.com/alloydb/docs/connection-overview · Checkov 색인 · 2026-10-01

## 13. Supabase (Free / Pro / Team)

01 §2.10·2.11과 02 §4를 합친 절이다.

- **Terraform:** `supabase/supabase` 1.11.0(community 등급, Supabase 조직 저장소). 리소스는 다음과 같다.
  - `supabase_project`: `organization_id`, `name`, `database_password`, `region`, `instance_size`
  - `supabase_settings`: `database`, `network`, `pooler`, `api`, `auth`, `storage`는 직렬화한 JSON이고, `ssl_enforcement`는 불리언이다.
  - 그 밖에 `supabase_branch`, `supabase_apikey`, `supabase_edge_function`, `supabase_edge_function_secrets`, `supabase_third_party_auth`.

  **자동화 불가 단계(provider에 리소스 없음)는 다음과 같다.** Management API로 가능한지는 미확인이다.
  1. 조직 플랜 전환(Free → Pro)
  2. PITR 애드온
  3. IPv4 애드온
  4. 스펜드 캡 끄기
  5. 읽기 복제본

  RLS 정책과 스키마는 Terraform이 아니라 `supabase/migrations/*.sql` + `supabase db push`(CLI)로 적용한다.
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `supabase_project.region = "ap-northeast-2"`: D5.
  2. `instance_size`: C8. 연결 수가 크기에 묶인다(02 §4 표). 변경 시 2분 미만 중단이 있다. F4.
  3. `supabase_settings.ssl_enforcement = true`: **Postgres 연결은 기본적으로 SSL을 강제하지 않는다**(02 §4). F5.
  4. `supabase_settings.network`: `restrictions` CIDR 목록. HTTPS API에는 적용되지 않는다(02 §4). F5.
  5. `supabase_settings.database`: 예 `statement_timeout`. C9·A2.
  6. `supabase_project.legacy_api_keys_enabled = false`: 레거시 `anon`/`service_role` 키는 2026년 말 폐지 예정이다.
  7. 마이그레이션 SQL의 `alter table … enable row level security` + 정책: 노출 테이블에 RLS가 없으면 anon 키만으로 읽고 쓸 수 있다(02 §4). F5. 생성기가 **모든 `public` 테이블에 대해 반드시 생성해야 하는 산출물**이다.
  8. 플랜(수동): Free는 백업 없음, 1주 비활동 시 일시정지, 500MB 초과 시 읽기 전용이다. C7이 "사용자 생성" 이상이면 Pro 이상이 전제다.
  9. PITR 애드온(수동): F3 "분 단위", RPO 2분, 월 약 $100부터(01 §2.11).
- **앱 쪽 계약:**
  - 서버 직결: `postgresql://postgres:[PW]@db.[REF].supabase.co:5432/postgres`. **IPv6 전용**이다(IPv4 애드온이 없을 때).
  - 세션 풀러: `postgresql://postgres.[REF]:[PW]@[POOLER-HOST]:5432/postgres`. IPv4 환경에서 직결 대신 쓴다.
  - 트랜잭션 풀러: `…:6543/postgres`. 서버리스용이며 **준비문을 쓸 수 없다**(0.2).
  - 클라이언트(브라우저·모바일)에는 publishable 키(`sb_publishable_…`)만 둔다. secret 키(`sb_secret_…`)는 RLS를 우회하므로 서버 비밀로만 주입한다.
  - `SUPABASE_URL` 같은 환경변수 이름은 관례이며 출처는 미확인이다.
- **로컬 개발 대응:** `supabase init` → `supabase start`(Docker로 전체 스택: Postgres, Auth, Storage 등). Docker Hub `supabase/postgres`에는 `15.19.x`, `17.11.x` 태그가 있다. 로컬 메이저 버전을 정하는 `config.toml` 키 이름은 이번에 확인하지 못했다(미확인).
- **데이터 이전 단계:** PG → Supabase는 `pg_dump --no-owner --no-privileges`를 세션 풀러로 실행한다. 역할은 옮겨지지 않는다. SQLite → Supabase는 pgloader(0.5)로 하되, 대상이 IPv6 직결이면 실행 위치의 네트워크를 확인한다. Firestore → Supabase는 02 §4의 변환 목록을 따르며, 공식 이전 도구는 이번에 확인하지 못했다(미확인).
- **검증 명령:**
  - `terraform validate`. Checkov 규칙 없음.
  - 정적 검사: 마이그레이션 SQL에서 `create table public.*`마다 `enable row level security`가 있는지 확인한다.
  - 배포 후: anon(publishable) 키로 각 테이블을 `GET /rest/v1/<table>` 호출해 **빈 결과나 401이 나오는지** 본다(RLS 동작 확인). `psql`로 세 연결 문자열을 각각 `select 1` 해 본다.
- **출처:** https://registry.terraform.io/providers/supabase/supabase/latest/docs/resources/project · …/settings · …/branch · https://supabase.com/docs/guides/database/connecting-to-postgres · https://supabase.com/docs/guides/getting-started/api-keys ("deprecating the anon and service_role keys by the end of 2026") · https://supabase.com/docs/guides/local-development/cli/getting-started · https://supabase.com/docs/guides/platform/migrating-to-supabase/postgres · https://hub.docker.com/r/supabase/postgres · 2026-10-01

## 14. Neon (Free / Launch / Scale)

- **Terraform:** `kislerdm/neon` 0.18.0을 쓴다. 상태가 엇갈리므로 [충돌]로 둔다.
  - GitHub 저장소는 **2026-09-11에 보관(archived)**됐다. README는 "officially maintained and distributed as **neondatabase/neon**"이라고 적는다.
  - 2026-10-01에 Registry에서 `neondatabase/neon`을 조회하면 결과가 없다.
  - Neon 문서는 여전히 `kislerdm/neon`을 "community-maintained … not officially supported"로 안내한다.

  생성기는 provider 소스를 변수로 두고 이관을 추적해야 한다. 리소스는 `neon_project`(기본 브랜치·컴퓨트·DB·역할 포함), `neon_branch`, `neon_endpoint`, `neon_role`, `neon_database`, `neon_branch_backup_schedule`이다. 플랜은 **수동**이다.
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `region_id`: **서울이 없다**(01 §2.12). D5에서 먼저 걸러진다.
  2. `pg_version`: 로컬 이미지 메이저와 맞춘다.
  3. `history_retention_seconds`: PITR 창. 플랜 상한이 있다(Free 6시간, 01 §2.12). F3.
  4. `default_endpoint_settings.suspend_timeout_seconds`: A5·D4. 0으로 축소되면 콜드 스타트가 생긴다.
  5. `autoscaling_limit_min_cu` / `autoscaling_limit_max_cu`: C8·G3.
  6. `quota`: 초과 시 컴퓨트가 중단된다. G3↔F1.
  7. `allowed_ips`, `block_public_connections`: F5.
  8. `store_password`.
  9. `enable_logical_replication`: 이전용이다.
- **앱 쪽 계약:**
  - 출력 `connection_uri`(직결)와 `connection_uri_pooler`(풀러)는 민감 값이다. 각각 `DIRECT_URL`, `DATABASE_URL`로 주입한다(0.2).
  - 연결 문자열에 `?sslmode=require&channel_binding=require`를 붙인다. Neon은 TLS를 필수로 요구한다.
  - 풀러는 PgBouncer 트랜잭션 모드이며 `SET`·`PREPARE`가 제한된다. 클라이언트는 최대 10,000이다.
  - 서버리스 드라이버(`@neondatabase/serverless`) HTTP 모드는 대화형 트랜잭션이 불가하다(01 §5.2).
- **로컬 개발 대응:** 두 가지다.
  - 오프라인이 아닌 방식: `neondatabase/neon_local`(클라우드 브랜치로 라우팅하는 프록시, `NEON_API_KEY` 필요, 임시 브랜치 생성·삭제).
  - 오프라인: `postgres:<pg_version>`(0.4).
- **데이터 이전 단계:** 0.5와 같다. 덤프·복원과 마이그레이션은 직결 URL로 한다. Neon 문서의 사용처 표가 "Schema migrations — Direct"라고 적는다.
- **검증 명령:** `terraform validate`. Checkov 규칙 없음. 배포 후 풀러와 직결 각각 `select 1`을 실행하고, `sslmode=disable` 접속이 거부되는지 확인한다.

## 15. PlanetScale Postgres

- **Terraform:** `planetscale/planetscale` 1.11.0. 리소스는 `planetscale_postgres_branch`, `planetscale_postgres_bouncer`, `planetscale_postgres_backup_policy`, `planetscale_postgres_branch_role`, `planetscale_postgres_read_only_replica`, `planetscale_postgres_branch_backup`다. **데이터베이스 자체를 만드는 리소스가 없다**(모든 리소스가 `database` 슬러그를 입력으로 받는다). DB 생성은 `pscale database create`(CLI) 또는 대시보드로 하는 **자동화 불가 단계**다. 조직 결제도 수동이다.
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `planetscale_postgres_branch.cluster_size`: 단일 노드는 HA가 없다(01 §2.14). F1·G3.
  2. `major_version`.
  3. `region`: GCP 서울 지원(01 §2.14). 바꾸면 교체된다. D5.
  4. `parameters = { pgconf = { max_connections = "…" , statement_timeout = "…" } }`: 생략한 파라미터는 기본값으로 되돌아간다. C8·C9.
  5. `deletion_protected = true`.
  6. `planetscale_postgres_backup_policy`: `frequency_unit`/`frequency_value`, `retention_unit`/`retention_value`, `target = "production"`. F3·C7.
  7. `planetscale_postgres_bouncer.bouncer_size`, `target`(`primary`/`replica`/`replica_az_affinity`): C8.
  8. `planetscale_postgres_branch_role.ttl`: F5.
- **앱 쪽 계약:**
  - `planetscale_postgres_branch_role`의 출력 `access_host_url`, `username`, `password`로 `DATABASE_URL`을 만든다. 비밀번호는 생성 시에만 나온다.
  - 이름 붙인 바운서는 사용자명 뒤에 `|bouncer이름`을 붙여 접속한다. PgBouncer 포트는 6432다(01 §2.14).
  - TLS 요구값은 이번에 확인하지 못했다(미확인).
- **로컬 개발 대응:** 공식 에뮬레이터는 없다(미확인). `postgres:<major_version>`(0.4)을 쓴다.
- **데이터 이전 단계:** 0.5의 `pg_dump`/`pg_restore`를 쓴다. `pscale database` 명령에 엔진별 dump·restore·migration 하위 명령이 있지만, 세부는 미확인이다.
- **검증 명령:** `terraform validate`. Checkov 규칙 없음. 배포 후 `select 1`과 `show max_connections`를 확인한다.

## 16. Prisma Postgres

- **Terraform:** `prisma/prisma-postgres` 0.2.0(community, 저장소 마지막 푸시 2026-01-13). 리소스는 `prisma-postgres_project`(`name`), `prisma-postgres_database`(`project_id`, `name`, `region`), `prisma-postgres_connection`(`database_id`, `name`)이다. 다음이 **자동화 불가 단계(수동)**다.
  - 백업 설정과 플랜(Free 백업 없음, Starter·Pro 일일 7일, 01 §2.15)
  - 삭제 보호와 연결 수 한도(provider에 인자 없음)
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `prisma-postgres_database.region`: **서울이 없다**(도쿄, 01 §2.15). D5.
  2. 플랜(수동): C7·F3.
  3. 연결 수(플랜별 100/500/1,000, 01 §2.15): C8.
- **앱 쪽 계약:** 출력 두 가지를 쓴다.
  - `connection_string`: `prisma+postgres://…`, Accelerate 경유. Prisma Client 전용이다.
  - `direct_url`: `postgresql://user:pass@host:5432/db`. 다른 드라이버와 마이그레이션용이다.

  Prisma가 아닌 드라이버(SQLAlchemy 등)는 `direct_url`만 쓸 수 있다.
- **로컬 개발 대응:** `prisma dev`(로컬 Prisma Postgres, Prisma 문서 색인). 다른 방법은 `postgres:17`(01 §0의 PG17 기준).
- **데이터 이전 단계:** 0.5와 같다(대상 `direct_url`). `npx create-db`로 만든 DB는 24시간 뒤 삭제되므로 이전 대상으로 쓰지 않는다(01 §2.15).
- **검증 명령:** `terraform validate`. Checkov 규칙 없음. `direct_url`로 `select 1`.

## 17. MySQL — Amazon RDS for MySQL

- **Terraform:** §5와 같다(`engine = "mysql"`). 변형은 Single-AZ / `multi_az = true` / `aws_rds_cluster`(`engine = "mysql"`, Multi-AZ DB 클러스터)이고 속성 차이는 §5~7과 같다.
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `engine_version = "8.4"`: **8.0은 2026-08-01부터 연장 지원 요금이 붙는다.** t4g.micro 기준 월 약 +$175다(01 §6-1). G3.
  2. `engine_lifecycle_support = "open-source-rds-extended-support-disabled"`: Registry 문서상 RDS for MySQL에 적용된다.
  3. `backup_retention_period >= 7`.
  4. `deletion_protection = true`.
  5. `skip_final_snapshot = false`.
  6. `delete_automated_backups = false`.
  7. `publicly_accessible = false`.
  8. `storage_encrypted = true`.
  9. `storage_type = "gp3"`, `max_allocated_storage`.
  10. `manage_master_user_password = true`.
  11. `multi_az`: F1.
  12. `parameter_group_name`(`family = "mysql8.4"`): TLS 강제 파라미터 이름(`require_secure_transport`)이 RDS에서 유효한지는 이번에 확인하지 못했다(미확인). F5.
  13. `ca_cert_identifier`.
  14. `enabled_cloudwatch_logs_exports`(`error`, `slowquery` 등. 허용 값은 API 문서 참조, 세부 미확인).
- **앱 쪽 계약:** 0.6과 같다. `DATABASE_URL=mysql://USER:PASS@<address>:3306/<db>`. TLS 검증용 `global-bundle.pem`은 §5와 같다.
- **로컬 개발 대응:** `mysql:8.4`, 헬스체크 `mysqladmin ping`(0.6).
- **데이터 이전 단계:** MySQL → RDS MySQL은 `mysqldump` 또는 DMS(0.5)로 한다. SQLite → MySQL 공식 도구는 이번에 확인하지 못했다(미확인. pgloader는 PG 대상만).
- **검증 명령:** Checkov는 §5의 `aws_db_instance` 규칙에서 PG 전용(CKV2_AWS_30, CKV_AWS_250, CKV_AWS_388)을 뺀 것이다. 클러스터면 CKV_AWS_325(MySQL 감사 로그)를 더한다. 배포 후 `describe-db-instances`로 `EngineVersion`이 8.4.x인지 확인한다.
- **출처:** §5 출처(Registry `db_instance` "This setting applies only to RDS for MySQL and RDS for PostgreSQL") · 01 §3.1, §6 · Checkov 색인 · 2026-10-01

## 18. MySQL — Amazon Aurora MySQL

- **Terraform:** §8과 같다(`engine = "aurora-mysql"`, Serverless v2는 §9와 같다).
- **요구 수준에 따라 바뀌는 핵심 속성:** §8의 13개 중 다음 차이가 있다.
  - `backtrack_window`: Aurora MySQL 전용. 0~259200초, 기본 0이다. 논리 손상을 빠르게 되돌리는 용도이며 F3 보조 수단이다. CKV_AWS_326 대상이다.
  - `enabled_cloudwatch_logs_exports`에 `audit`을 넣는다. CKV_AWS_325 대상이다.

  나머지는 §8과 같다. 이 절에서 센 핵심 속성은 12개다.
- **앱 쪽 계약:** 0.6과 같다. `endpoint`와 `reader_endpoint`를 쓴다.
- **로컬 개발 대응:** `mysql:<Aurora 호환 메이저>`. Aurora 버전과 MySQL 메이저의 대응은 이번에 확인하지 못했다(미확인).
- **데이터 이전 단계:** §17과 같다.
- **검증 명령:** §8과 같고 CKV_AWS_325, CKV_AWS_326을 더한다.
- **출처:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/rds_cluster (`backtrack_window` "Only available for `aurora` and `aurora-mysql`") · Checkov 색인 · 2026-10-01

## 19. MySQL — Cloud SQL for MySQL

- **Terraform:** §10과 같다(`database_version = "MYSQL_8_4"`).
- **요구 수준에 따라 바뀌는 핵심 속성:** §10과 같은 항목에서 다음이 다르다.
  - PITR은 `backup_configuration.binary_log_enabled = true`로 켠다. Registry 문서는 MySQL HA(`REGIONAL`)의 전제로 이 값을 요구한다. `point_in_time_recovery_enabled`는 PG·SQL Server 전용이다.
  - `edition` 기본값 규칙(PG16+만 Enterprise Plus 기본)은 MySQL에는 적용되지 않는다. 문서는 "all others default to ENTERPRISE"라고 적는다.
  - 플래그로 `local_infile = off`를 둔다(CKV_GCP_50). §10의 13번 `database_flags`에 포함된다.

  이 절에서 센 핵심 속성은 §10과 같은 14개다(PITR 인자만 바뀜).
- **앱 쪽 계약:** 0.6과 같다. Cloud Run 소켓 경로 규칙은 §10과 같다(MySQL 소켓 접미사는 미확인).
- **로컬 개발 대응:** `mysql:8.4`.
- **데이터 이전 단계:** Google DMS가 → Cloud SQL MySQL 동종 이전을 지원한다(01 §5.5).
- **검증 명령:** Checkov는 CKV_GCP_6, 11, 14, 60, 79, CKV_GCP_50(`local_infile` off), CKV2_GCP_7(관리자 접속 제한), CKV2_GCP_20(MySQL PITR)이다.
- **출처:** §10 출처 · Checkov 색인 · 2026-10-01

## 21. Cloud Firestore — Standard

- **Terraform:** `google_firestore_database`, `google_firestore_index`(복합 인덱스), `google_firestore_field`, `google_firestore_backup_schedule`, `google_firebaserules_ruleset` + `google_firebaserules_release`(`name = "cloud.firestore"`), `google_project_service`(API). Firebase 프로젝트 연결은 `google_firebase_project`다. **Blaze 요금제 전환(결제 계정 연결)은 이 문서 범위에서 리소스를 확인하지 못했다.** 관리형 export/import와 PITR 비용이 Blaze를 전제로 하므로 수동 단계로 둔다(02 §1).
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `location_id = "asia-northeast3"`: D5. 생성 후 변경 가능 여부는 미확인이다(02 §1).
  2. `type = "FIRESTORE_NATIVE"`.
  3. `database_edition = "STANDARD"`.
  4. `point_in_time_recovery_enablement = "POINT_IN_TIME_RECOVERY_ENABLED"`: **기본 꺼짐**(02 §1). 켜면 7일이다. C7·F3.
  5. `google_firestore_backup_schedule`: `retention` 최대 14주, `daily_recurrence` 또는 `weekly_recurrence`. C7.
  6. `delete_protection_state = "DELETE_PROTECTION_ENABLED"`: 기본값 `UNSPECIFIED`는 "currently equivalent to DELETE_PROTECTION_DISABLED"다.
  7. `deletion_policy`: **기본 `ABANDON`**. `terraform destroy`를 해도 DB가 남는다. 의도한 동작인지 명시한다.
  8. `concurrency_mode`: `OPTIMISTIC`/`PESSIMISTIC`. C2. 서버 라이브러리 동작이 바뀐다(02 §1).
  9. 보안 규칙 `google_firebaserules_ruleset.source.files.content`: 프로덕션 기본은 전부 거부다. **테스트 모드 규칙을 생성하지 않는다.** F5.
- **앱 쪽 계약:**
  - 서버: Admin SDK가 ADC로 인증한다. 클라우드 런타임은 서비스 계정을 쓰고, 그 밖에서는 `GOOGLE_APPLICATION_CREDENTIALS`(키 파일 경로)를 쓴다. 서버 SDK는 규칙을 우회하므로 서버 코드의 권한 검사가 필요하다(02 §1).
  - 클라이언트: Firebase 설정 객체(공개 값) + 규칙.
  - 기본 DB가 아니면 DB ID를 설정해야 한다. 복원은 새 DB로만 되므로 DB ID를 환경변수로 뺀다(02 §1).
- **로컬 개발 대응:** Firebase Local Emulator Suite. Firestore 에뮬레이터 기본 포트는 8080이고, SDK `useEmulator(host, 8080)` 또는 `FIRESTORE_EMULATOR_HOST`를 쓴다. 공식 Docker 이미지는 확인하지 못했다(미확인). compose에서는 firebase-tools를 설치한 컨테이너를 직접 만들어야 한다.
- **데이터 이전 단계:** 관리형 export/import(GCS, Blaze 필요). Firestore → 관계형은 02 §1의 변환 목록에 따른 **사용자 정의 스크립트**가 필요하며 공식 도구는 미확인이다. 검증은 컬렉션별 문서 수 대 테이블 행 수 비교다.
- **검증 명령:** Checkov 색인에 Firestore 규칙은 **없다**. plan JSON에서 4·6·9를 직접 검사한다. 배포 후 `gcloud firestore databases describe --database='(default)'`로 PITR과 삭제 보호를 확인한다. 규칙은 에뮬레이터 + 규칙 단위 테스트로 검증하며, 테스트 도구 세부는 미확인이다.
- **출처:** https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/firestore_database · …/firestore_backup_schedule ("up to 14 weeks") · …/firestore_index · …/firebaserules_ruleset · …/firebaserules_release · https://firebase.google.com/docs/emulator-suite/connect_firestore · https://firebase.google.com/docs/admin/setup · https://firebase.google.com/docs/firestore/manage-data/export-import · 2026-10-01

## 22. Cloud Firestore — Enterprise(MongoDB 호환)

- **Terraform:** §21과 같다(`database_edition = "ENTERPRISE"`, `type`은 `FIRESTORE_NATIVE`여야 한다).
- **요구 수준에 따라 바뀌는 핵심 속성:** §21의 1~2, 4~7, 9에 다음 하나를 더한다(8개).
  - `database_edition = "ENTERPRISE"`: 질의 능력, 문서 크기(16 MiB), 과금 단위가 바뀐다(02 §2). 기본 동시성 모드는 낙관적이다.
- **앱 쪽 계약:** Native SDK는 §21과 같다. MongoDB 드라이버로 접근할 때의 연결 문자열과 인증 방식은 미확인이다(02 §2).
- **로컬 개발 대응:** Native 모드는 §21 에뮬레이터를 쓴다. Enterprise 고유 기능(파이프라인 조인)을 에뮬레이터가 지원하는지는 미확인이다.
- **데이터 이전 단계:** Mongo 앱에서 옮겨 오면 0.7의 `mongodump`/`mongorestore`를 쓸 수 있는지가 관건인데, 호환 범위가 미확인이다.
- **검증 명령:** §21과 같다.
- **출처:** §21 출처 · 02 §2 · 2026-10-01

## 23. Firebase Realtime Database

- **Terraform:** `google_firebase_database_instance`. **beta 리소스**이므로 `google-beta` provider가 필요하다. 다음 항목은 Terraform 밖이다.
  - 보안 규칙 배포: `google_firebaserules_release`의 예시는 `cloud.firestore`와 `firebase.storage`만 다룬다. RTDB 규칙 배포 방법(CLI `firebase deploy` 대상명)은 이번에 원문을 확인하지 못했다(미확인).
  - 일일 백업 설정(Blaze만): **수동**.
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `region`: **서울이 없다**(02 §3). D5에서 먼저 걸러진다.
  2. `instance_id`: 전역 고유 ID이며 삭제 후 재사용할 수 없다.
  3. `type`: 기본 DB 하나는 삭제할 수 없다. 추가 DB(샤딩)는 Blaze만 된다. D2·C1.
  4. `desired_state`: `ACTIVE`/`DISABLED`.
- **앱 쪽 계약:** `databaseURL`(인스턴스 URL) + Admin SDK(ADC)를 쓴다. 클라이언트는 규칙으로 통제한다.
- **로컬 개발 대응:** Firebase Local Emulator Suite의 Database 에뮬레이터. 포트와 환경변수는 이번에 확인하지 못했다(미확인).
- **데이터 이전 단계:** 콘솔 JSON 내보내기·가져오기(02 §3). 관계형으로 옮기려면 사용자 정의 스크립트가 필요하다.
- **검증 명령:** Checkov 규칙 없음. 배포 후 규칙이 "전부 거부" 또는 인증 조건인지 확인한다.
- **출처:** https://registry.terraform.io/providers/hashicorp/google-beta/latest/docs/resources/firebase_database_instance ("This resource is in beta", "Creating user Databases is only available for projects on the Blaze plan") · …/firebaserules_release · 2026-10-01

## 24. Amazon DynamoDB — 단일 리전

- **Terraform:** `aws_dynamodb_table`. 프로비저닝 오토스케일링을 쓰면 `aws_appautoscaling_target`·`aws_appautoscaling_policy`를 추가한다. CMK는 `aws_kms_key`로 만든다.
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `billing_mode = "PAY_PER_REQUEST"`: **Terraform 기본값은 `PROVISIONED`**다. AWS가 권장하는 온디맨드가 아니고 `read_capacity`·`write_capacity`가 필수가 된다. 01·02의 "고정비 $0" 판단은 이 값을 명시해야 성립한다. G3·D3.
  2. `on_demand_throughput`: 최대 처리량 상한. 비용 폭주를 막는다. G3·E2.
  3. `point_in_time_recovery { enabled = true }`: 블록이 없으면 `false`다. 새 테이블에서는 켜는 데 최대 10분이 걸린다. C7·F3.
  4. `point_in_time_recovery.recovery_period_in_days`: 기본 35.
  5. `deletion_protection_enabled = true`: 기본 `false`.
  6. `server_side_encryption { enabled, kms_key_arn }`: 지정하지 않으면 AWS 소유 키로 암호화된다. F5가 "규제"면 CMK를 쓴다.
  7. `hash_key`/`range_key`/`attribute`: 바꾸면 **교체**된다(Forces new resource). 접근 패턴(C5)으로 정한다.
  8. `global_secondary_index`: GSI는 결과적 일관성만 지원한다(02 §5). C3. 개수만큼 쓰기 비용이 늘어난다.
  9. `ttl`: C6.
  10. `stream_enabled` / `stream_view_type`: 글로벌 테이블과 이벤트 처리의 전제다.
- **앱 쪽 계약:** AWS SDK는 연결 문자열이 없다. 테이블 이름 환경변수(이름은 관례, 예 `TABLE_NAME`)와 IAM 역할을 쓴다. 로컬 엔드포인트를 바꿀 수 있게 `AWS_ENDPOINT_URL_DYNAMODB` 같은 엔드포인트 재정의를 둔다(환경변수 이름은 미확인, SDK `endpoint` 옵션은 공통). 트랜잭션 취소는 SDK가 재시도하지 않으므로 재시도 코드와 멱등 토큰을 생성한다(02 §5).
- **로컬 개발 대응:** 공식 이미지 `amazon/dynamodb-local`(최신 3.3.1). AWS 문서의 compose 예는 `image: amazon/dynamodb-local:latest`, `command: "-jar DynamoDBLocal.jar -sharedDb -dbPath ./data"`, 포트 8000이다. 헬스체크 명령은 공식 예에 없다(미확인). 대안은 `aws dynamodb list-tables --endpoint-url http://localhost:8000` 성공 여부다.
- **데이터 이전 단계:**
  - S3 → 새 테이블: `import_table { input_format = "CSV"|"DYNAMODB_JSON"|"ION", s3_bucket_source {…} }`. 기존 테이블로는 가져올 수 없다(02 §5).
  - RDB → DynamoDB: DMS 대상 `engine_name = "dynamodb"`. 다만 단일 테이블 설계 변환은 사용자 정의다.
  - 검증: 항목 수(`Scan`의 `Select=COUNT`는 전체 읽기 과금) 또는 S3 export 행 수 비교.
- **검증 명령:**
  - Checkov:
    - 기본: CKV_AWS_28(PITR)
    - F5 "규제"일 때: CKV_AWS_119(CMK)
    - 프로비저닝일 때: CKV2_AWS_16(오토스케일링). 온디맨드면 근거를 달아 건너뛴다.
  - 배포 후: `aws dynamodb describe-continuous-backups --table-name <t>`(PITR 상태), `aws dynamodb describe-table --query 'Table.[BillingModeSummary,DeletionProtectionEnabled,SSEDescription]'`.
- **출처:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/dynamodb_table ("Defaults to `PROVISIONED`", "If the `point_in_time_recovery` block is not provided, this defaults to `false`", `deletion_protection_enabled` "Defaults to `false`", `import_table`) · …/appautoscaling_target · https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.DownloadingAndRunning.html · https://hub.docker.com/r/amazon/dynamodb-local · Checkov 색인 · 2026-10-01

## 25. Amazon DynamoDB — 글로벌 테이블

- **Terraform:** `aws_dynamodb_table` + `replica { region_name … }` 블록(Global Tables V2). 다른 방법으로 `aws_dynamodb_table_replica`를 쓸 수 있다.
- **요구 수준에 따라 바뀌는 핵심 속성:** §24의 10개에 다음을 더한다.
  1. `stream_enabled = true`, `stream_view_type = "NEW_AND_OLD_IMAGES"`: Registry 예시의 전제다.
  2. `replica.region_name`: D5·F2.
  3. **`replica.point_in_time_recovery = true`**: 복제본마다 **기본 `false`**다. 원본 테이블의 PITR이 복제본으로 이어지지 않는다. C7.
  4. `replica.deletion_protection_enabled = true`: 복제본마다 기본 `false`.
  5. `replica.consistency_mode = "STRONG"`(MRSC): 기본 `EVENTUAL`이다. 복제본 1개와 함께 쓰려면 `global_table_witness`가 필요하다. MRSC는 트랜잭션을 지원하지 않는다(02 §6). C3.
  6. `replica.kms_key_arn`.
- **앱 쪽 계약:** §24와 같다. 리전별 엔드포인트를 고르는 설정이 추가된다. MREC는 최종 쓰기가 우선하므로 C2가 "있음"이면 쓰기 리전을 하나로 고정한다(02 §6).
- **로컬 개발 대응:** §24와 같다. 다중 리전 동작은 로컬에서 재현되지 않는다.
- **데이터 이전 단계:** §24와 같다.
- **검증 명령:** Checkov는 CKV_AWS_28과 CKV_AWS_165(글로벌 테이블 PITR, `aws_dynamodb_global_table` 대상), CKV_AWS_271(`aws_dynamodb_table_replica` CMK)이다. **`replica` 블록 안의 PITR을 검사하는 규칙은 색인에서 찾지 못했다.** 그래서 plan JSON에서 직접 검사한다. 배포 후 리전마다 `describe-continuous-backups`를 실행한다.
- **출처:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/dynamodb_table (`replica` 블록: "Whether to enable Point In Time Recovery for the replica. Default is `false`", `consistency_mode` "Default value is `EVENTUAL`") · …/dynamodb_table_replica · Checkov 색인 · 2026-10-01

## 26. MongoDB Atlas — Free·Flex

- **Terraform:** `mongodb/mongodbatlas` 2.19.0(partner-premier). 리소스는 다음과 같다.
  - 클러스터: Flex는 `mongodbatlas_flex_cluster`(또는 `mongodbatlas_advanced_cluster`의 `provider_name = "FLEX"`), Free(M0)는 `mongodbatlas_advanced_cluster`(`provider_name = "TENANT"`, `instance_size = "M0"`).
  - 그 밖에 `mongodbatlas_project`, `mongodbatlas_database_user`, `mongodbatlas_project_ip_access_list`.

  조직 생성과 결제 수단 연결은 이번에 리소스를 확인하지 못했다. API 키 발급을 포함해 수동으로 둔다.
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `provider_settings.region_name` / `backing_provider_name`: 서울은 GCP만 된다(02 §7). D5.
  2. 등급(M0 / Flex): Free는 백업이 없고 30일 비활동 시 일시정지된다. Flex는 일일 스냅샷만 있다(02 §7). C7이 "사용자 생성" 이상이면 Dedicated(§27)로 간다.
  3. `termination_protection_enabled = true`.
  4. `mongodbatlas_project_ip_access_list.cidr_block`: 기본 거부다(02 §7). **`0.0.0.0/0`을 생성하지 않는다.** 서버리스 컴퓨트처럼 출구 IP가 고정되지 않으면 이 지점에서 막힌다(CP.networking). F5.
  5. `mongodbatlas_database_user.roles`: 앱 DB에 대해 `readWrite`만 준다. `password_wo` 사용. F5.
  6. Flex 처리량 한도(500 ops/s, 02 §7): D2. 속성으로 바꿀 수 없으며 등급 변경으로만 바뀐다.
- **앱 쪽 계약:** 출력 `connection_strings.standard_srv`(`mongodb+srv://…`) + 사용자·비밀번호로 `MONGODB_URI`를 만든다. 이 이름은 관례이며 출처는 미확인이다(0.7).
- **로컬 개발 대응:** 0.7과 같다.
- **데이터 이전 단계:** 0.7의 `mongodump`/`mongorestore`. M0 → Flex → Dedicated 업그레이드는 `provider_name` 변경으로 한다(Registry 문서).
- **검증 명령:** `terraform validate`. Checkov 색인에 Atlas 규칙은 **없다**. plan JSON에서 `cidr_block != "0.0.0.0/0"`을 검사한다. 배포 후 `mongosh "$MONGODB_URI" --eval 'db.runCommand({ping:1})'`.
- **출처:** https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs/resources/advanced_cluster · …/flex_cluster · …/project_ip_access_list · …/database_user · 2026-10-01

## 27. MongoDB Atlas — Dedicated(M10+)

- **Terraform:** `mongodbatlas_advanced_cluster`(`cluster_type = "REPLICASET"`, `replication_specs[].region_configs[]`), `mongodbatlas_cloud_backup_schedule`, `mongodbatlas_backup_compliance_policy`(선택), `mongodbatlas_database_user`, `mongodbatlas_project_ip_access_list` 또는 프라이빗 엔드포인트 리소스.
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `region_configs.provider_name` / `region_name`: 서울은 AWS·GCP 둘 다 된다(02 §8). D5.
  2. `electable_specs.instance_size`(M10 …), `node_count`: G3·D2.
  3. `region_configs.priority`: 다중 리전 선거. F2.
  4. `backup_enabled = true`.
  5. `pit_enabled = true`: 연속 백업(PITR). F3.
  6. `mongodbatlas_cloud_backup_schedule`: 보존 정책. C7.
  7. `termination_protection_enabled = true`.
  8. `mongo_db_major_version` / `version_release_system`: 기본값은 `LTS`다. 로컬 이미지와 맞추려면 메이저를 고정한다.
  9. `advanced_configuration.minimum_enabled_tls_protocol`: F5.
  10. `encryption_at_rest_provider`: 고객 키를 쓸 때. F5.
- **앱 쪽 계약:** §26과 같다. 트랜잭션 재시도(WriteConflict)는 드라이버 콜백 API를 쓴다(02 §8).
- **로컬 개발 대응:** `mongo:<mongo_db_major_version>`을 단일 노드 레플리카셋으로 띄운다(0.7).
- **데이터 이전 단계:** 0.7과 같다. 무중단 이전은 Atlas 라이브 마이그레이션이지만 세부는 미확인이다.
- **검증 명령:** §26과 같고 `pit_enabled = true`, `termination_protection_enabled = true`를 plan에서 검사한다. 배포 후 `atlas clusters describe <name>`(Atlas CLI)을 실행한다.
- **출처:** https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs/resources/advanced_cluster (`pit_enabled`, `backup_enabled`, `version_release_system` "defaults to `LTS`") · …/cloud_backup_schedule · …/backup_compliance_policy · https://www.mongodb.com/docs/atlas/cli/current/command/atlas-clusters-describe/ · 2026-10-01

## 28. Amazon DocumentDB

- **Terraform:** `aws_docdb_cluster`, `aws_docdb_cluster_instance`, `aws_docdb_subnet_group`, `aws_docdb_cluster_parameter_group`, SG. Elastic 클러스터는 `aws_docdbelastic_cluster`다(트랜잭션 없음, 02 §9).
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `engine_version`: 바꾸면 중단이 생긴다(Registry). 로컬 Mongo 호환 버전을 이 값으로 정한다.
  2. `backup_retention_period`: 기본 1이며 7 이상으로 둔다. CKV_AWS_360.
  3. `preferred_backup_window`.
  4. `deletion_protection = true`: 기본 `false`.
  5. `storage_encrypted = true`: **기본 `false`**. CKV_AWS_74.
  6. `kms_key_id`: CKV_AWS_182.
  7. `manage_master_user_password = true`.
  8. `db_cluster_parameter_group_name`: 기본 파라미터 그룹은 수정할 수 없으므로 **사용자 정의 그룹을 생성**한다. `tls = enabled`(CKV_AWS_90)와 감사 로그(CKV_AWS_104)를 넣는다.
  9. `enabled_cloudwatch_logs_exports`: CKV_AWS_85.
  10. `aws_docdb_cluster_instance` 개수와 `promotion_tier`: F1.
  11. `instance_class`: 서울 t4g.medium이 월 약 $84다(02 §9). G3.
  12. `skip_final_snapshot = false`.
- **앱 쪽 계약:**
  - 공식 예: `mongodb://USER:PASS@<cluster-endpoint>:27017/?tls=true&tlsCAFile=global-bundle.pem&replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false`
  - **`retryWrites=false`가 필수다.** Mongo 드라이버 기본값과 다르다.
  - TLS 번들 `global-bundle.pem`을 이미지에 포함한다.
  - 클러스터는 VPC 전용이므로 컴퓨트도 같은 VPC에 있어야 한다.
- **로컬 개발 대응:** 공식 에뮬레이터는 없다(미확인). `mongo:<호환 버전>`은 API 차이(02 §9 "버전별 차이 큼") 때문에 로컬 통과가 운영 통과를 보장하지 않는다.
- **데이터 이전 단계:** 0.7의 `mongodump`/`mongorestore`, 또는 DMS(대상 `engine_name = "docdb"`). DocumentDB 이전 가이드: https://docs.aws.amazon.com/documentdb/latest/developerguide/docdb-migration.html.
- **검증 명령:** Checkov는 CKV_AWS_74, 85, 90, 104, 182, 360이다. 배포 후 `aws docdb describe-db-clusters --query 'DBClusters[0].[StorageEncrypted,BackupRetentionPeriod,DeletionProtection]'`. VPC 안에서 `mongosh` ping을 실행한다.
- **출처:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/docdb_cluster ("The default is `false`" storage_encrypted, `backup_retention_period` "Default `1`") · …/docdb_cluster_instance · …/docdb_cluster_parameter_group · …/docdbelastic_cluster · https://docs.aws.amazon.com/documentdb/latest/developerguide/security.encryption.ssl.html ("By default, encryption in transit is enabled for newly" created clusters, 기본 파라미터 그룹 수정 불가) · https://docs.aws.amazon.com/documentdb/latest/developerguide/connect_programmatically.html · Checkov 색인 · 2026-10-01

## 29. Google Cloud Spanner

- **Terraform:** `google_spanner_instance`, `google_spanner_database`(`ddl` 포함 가능), 백업 일정은 인스턴스의 `default_backup_schedule_type`으로 정한다.
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `config = "regional-asia-northeast3"`: D5·F2. 멀티 리전 config를 쓸지 결정한다.
  2. `num_nodes` | `processing_units` | `autoscaling_config` 중 하나: 100 PU부터(02 §10). G3·D2.
  3. `edition`: `STANDARD`/`ENTERPRISE`/`ENTERPRISE_PLUS`. 전문·벡터 검색은 Enterprise다(02 §10).
  4. `instance_type`: `FREE_INSTANCE`는 백업·백업 일정을 쓸 수 없다. 90일 체험 후 삭제된다(02 §10).
  5. `default_backup_schedule_type = "AUTOMATIC"`: 미설정이나 `NONE`이면 새 DB에 백업 일정이 생기지 않는다. C7.
  6. `google_spanner_database.version_retention_period`: 기본 `1h`, 최대 7일. PITR 창이다. F3.
  7. `deletion_protection`: Terraform 수준이며 **기본 `true`**.
  8. `enable_drop_protection = true`: GCP 수준이며 **기본 `false`**. CKV_GCP_120.
  9. `database_dialect`: `GOOGLE_STANDARD_SQL`(기본) 또는 `POSTGRESQL`. 앱 질의 방언과 드라이버가 바뀐다.
- **앱 쪽 계약:** 클라이언트 라이브러리(gRPC) + ADC. `projects/<p>/instances/<i>/databases/<d>` 경로를 환경변수로 둔다(이름은 관례). PG 방언이면 PGAdapter 경유 가능성은 미확인이다.
- **로컬 개발 대응:** 공식 에뮬레이터 이미지 `gcr.io/cloud-spanner-emulator/emulator`, 포트 9010(gRPC)·9020(REST), 앱 쪽 `SPANNER_EMULATOR_HOST=localhost:9010`.
- **데이터 이전 단계:** Spanner 이전 개요 문서를 따른다(도구 세부 미확인). 검증은 테이블별 행 수 비교다.
- **검증 명령:** Checkov는 CKV_GCP_119(삭제 보호), CKV_GCP_120(drop 보호), CKV_GCP_93(CSEK, F5 "규제"일 때)이다. 배포 후 `gcloud spanner databases describe <db> --instance <i>`로 `versionRetentionPeriod`와 `enableDropProtection`을 확인한다.
- **출처:** https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/spanner_instance · …/spanner_database ("Default value is 1h", "Defaults to false" drop protection, deletion_protection "Defaults to true") · https://cloud.google.com/spanner/docs/emulator · https://cloud.google.com/spanner/docs/migration-overview · Checkov 색인 · 2026-10-01

## 30. Google Cloud Bigtable

- **Terraform:** `google_bigtable_instance`(`cluster` 블록), `google_bigtable_table`(`column_family`, `automated_backup_policy`), 필요하면 `google_bigtable_app_profile`(이번에 열람하지 않음, 미확인).
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `cluster.zone`: 서울 존. 클러스터가 여러 개면 서로 다른 존이어야 한다. F1·D5.
  2. `cluster.num_nodes` 또는 `autoscaling_config { min_nodes, max_nodes, cpu_target }`: 노드 1개가 월 약 $475다(02 §11). G3.
  3. `cluster.storage_type`: 기본 `SSD`.
  4. `cluster.kms_key_name`: F5. CKV_GCP_85.
  5. `deletion_protection`: Terraform 수준. CKV_GCP_122.
  6. `google_bigtable_table.deletion_protection = "PROTECTED"`.
  7. `automated_backup_policy { retention_period, frequency }`: 생략하면 자동 백업이 꺼진다. C7.
  8. `split_keys`: 바꾸면 **테이블 전체가 삭제·재생성**된다(Registry 경고). C6.
- **앱 쪽 계약:** 클라이언트 라이브러리 + ADC, 프로젝트·인스턴스·테이블 ID. 단일 행 트랜잭션만 있으므로 C3이 "트랜잭션 필요"면 부적합하다(02 §11).
- **로컬 개발 대응:** `gcloud beta emulators bigtable start`(기본 `localhost:8086`), 앱 쪽 `BIGTABLE_EMULATOR_HOST`. Docker로도 실행할 수 있으나 공식 이미지 이름은 미확인이다.
- **데이터 이전 단계:** 미확인(공식 도구를 이번에 열람하지 않음).
- **검증 명령:** Checkov는 CKV_GCP_85, CKV_GCP_122다. 배포 후 `gcloud bigtable instances describe <i>`. `split_keys` 변경이 plan에 나타나면 중단한다.
- **출처:** https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/bigtable_instance · …/bigtable_table (`split_keys` 경고, `automated_backup_policy`) · https://cloud.google.com/bigtable/docs/emulator · Checkov 색인 · 2026-10-01

## 32. PocketBase — 자체 호스팅

- **Terraform:** 없다. VM이나 컨테이너 호스트(컴퓨트 산출물)와 영속 볼륨만 Terraform으로 만든다. 다음이 **자동화 불가 단계**다.
  - 슈퍼유저 생성: `pocketbase superuser create EMAIL PASS`. CLI로 스크립트화할 수 있다.
  - 대시보드 Settings > Backups 설정(S3 저장소, 주기). API로 가능하다는 문구는 있으나 세부는 미확인이다.
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. 인스턴스 1개 고정: SQLite WAL 기반이라 동시 쓰기가 1이다(02 §13). C1이 중간 이상이면 기각한다.
  2. 영속 볼륨 `/pb/pb_data`: 공식 Dockerfile 예의 마운트 지점이다. B2.
  3. 백업: 내장 백업(ZIP)을 S3 호환 저장소로 보낸다. **"5GB+면 다른 전략 고려"**라는 문서 경고가 있다. C7·C6.
  4. `serve --http=0.0.0.0:8080` 앞에 리버스 프록시(TLS)를 둔다. F5.
  5. 컬렉션 API 규칙: 기본은 superuser 전용이다(02 §13). F5.
- **앱 쪽 계약:** PocketBase URL(공개) + SDK. 관리자 자격은 서버에만 둔다.
- **로컬 개발 대응:** 같은 바이너리와 Dockerfile을 쓴다(공식 이미지는 없고 문서의 Dockerfile 예시를 쓴다).
- **데이터 이전 단계:** `pb_data` 디렉터리 복사(앱 정지 상태) 또는 백업 ZIP 복원. 다른 저장소에서 옮겨 오는 도구는 미확인이다.
- **검증 명령:** `docker build` 성공, 컨테이너 기동 후 HTTP 헬스 엔드포인트(경로 미확인) 또는 `/` 200 확인, 볼륨 마운트 확인. Checkov 규칙 없음(Dockerfile 검사 규칙은 이 문서 범위 밖).
- **출처:** https://pocketbase.io/docs/going-to-production/ ("mount a volume at /pb/pb_data", "Backups can be stored locally (default) or in a S3 compatible storage", "consider a different backup strategy", `superuser create`) · 2026-10-01

## 34. pgvector — Postgres 확장

- **Terraform:** 호스트 Postgres의 리소스(§4~16)에 더해, 확장 활성화는 `cyrilgdn/postgresql`의 `postgresql_extension { name = "vector" }`로 할 수 있다. 다만 **Terraform 실행 위치에서 DB로 연결이 돼야 한다.** 사설 DB(§5·10 기본값)에서는 실행할 수 없으므로 **앱 마이그레이션에 `CREATE EXTENSION vector;`를 넣는 쪽을 기본값**으로 한다.
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. 확장 버전: 로컬 이미지 `0.8.6-pg18` 등과 운영 호스트의 버전을 맞춘다. 관리형 호스트의 지원 버전은 01 §2.2에서 "확장 목록 미확인"이다.
  2. 인덱스 종류(HNSW/IVFFlat)와 차원 한도(`vector` 2,000, `halfvec` 4,000, 02 §15): C5.
  3. 근사 인덱스의 사후 필터로 재현율이 떨어지는 문제에 대한 질의 설계(02 §15): C5.
  4. 호스트 인스턴스 메모리: 인덱스 크기. G3.
- **앱 쪽 계약:** 호스트 Postgres의 계약(0.1)과 같다. ORM의 벡터 타입 지원은 이번에 확인하지 못했다(미확인).
- **로컬 개발 대응:** `pgvector/pgvector:pg18`(`pg17` 등 메이저별 태그, `0.8.6-pg18-trixie` 고정 태그). README에 따르면 "This adds pgvector to the Postgres image"이므로 0.4의 compose에서 이미지 이름만 바꾼다.
- **데이터 이전 단계:** 0.5와 같다. 덤프에 `CREATE EXTENSION`이 포함되는지 확인하고, 대상 호스트가 확장을 허용하는지 먼저 확인한다.
- **검증 명령:** `psql -c "select extversion from pg_extension where extname='vector'"`. Checkov 규칙 없음.

---

## 36. 생성 자동화를 막는 발견

1. **Terraform 기본값이 클라우드 콘솔 기본값보다 위험하다.** 아래 기본값 때문에 생성기는 이 문서의 "핵심 속성"을 **모두 명시**해야 하고, plan JSON 검사로 확인해야 한다. Checkov는 일부만 잡는다. 예를 들어 Firestore, AlloyDB, Atlas, DynamoDB 복제본 PITR에는 규칙이 없다.
   - `aws_db_instance`: `backup_retention_period` 기본 0, `storage_encrypted` 기본 false, `storage_type` 기본 gp2, `engine_lifecycle_support` 기본 연장 지원 가입.
   - `aws_dynamodb_table`: `billing_mode` 기본 `PROVISIONED`, PITR 기본 false, 복제본마다 PITR false.
   - `aws_docdb_cluster`: `storage_encrypted` 기본 false.
   - Multi-AZ DB 클러스터: `storage_type` 기본 io1.
   - `google_sql_database_instance`: `ssl_mode` 기본 `ALLOW_UNENCRYPTED_AND_ENCRYPTED`.
   - Firestore: `deletion_policy` 기본 ABANDON.
2. **Cloud SQL PostgreSQL 16 이상은 `edition`을 생략하면 Enterprise Plus가 되어 저가 tier로 생성이 실패한다.** 이 오류는 `terraform plan`이 아니라 apply 때 나므로, 정적 규칙을 따로 둬야 한다. 01의 "Cloud SQL 최소 $7.7" 판단은 `edition = "ENTERPRISE"`를 명시해야 성립한다.
3. **로컬과 운영의 차이가 처음 배포에서 터지는 지점이 정해져 있다.** 생성기는 로컬에서 통과한 것을 운영 통과로 간주하면 안 되고, 배포 후 연결 검증(0.8-4)을 필수 단계로 둬야 한다.
   - RDS PG 15 이상은 `rds.force_ssl = 1`이 기본이라 TLS 없는 연결이 거부된다.
   - 트랜잭션 풀러(Supabase 6543, Neon pooler)는 준비문을 막는다(드라이버별 설정 필요).
   - Prisma + MongoDB는 레플리카셋이 필요하다.
   - DocumentDB는 `retryWrites=false`가 필수다.
   - postgres 18 이미지는 볼륨 경로가 바뀌었다.
4. **사설 DB가 기본값이 되면 에이전트 자신이 DB에 닿을 수 없다.** 그래서 다음 작업을 VPC 안에서 실행할 **일회성 작업 리소스**를 함께 생성해야 한다.
   - 데이터 이전(pgloader, `pg_dump`)
   - DB 안 객체 생성(`postgresql_extension`, RLS 정책)
   - 배포 후 연결 검증

   또 RDS가 관리하는 마스터 비밀번호는 7일마다 바뀌므로, 기동 때 한 번 읽는 앱은 일주일 뒤 실패한다. 앱 전용 역할과 비밀 재조회 코드가 필요하다.
5. **SaaS 저장소의 Terraform 경로가 불안정하거나 비어 있다.**
   - Neon provider 저장소는 2026-09-11에 보관됐고, 공식 이관처 `neondatabase/neon`은 Registry에 없다.
   - Turso·Fly provider는 보관됐다.
   - PlanetScale은 DB 생성 리소스가 없다.
   - Supabase는 플랜·PITR·IPv4 애드온 리소스가 없다.
   - Convex·PocketBase는 provider가 없다.

   그래서 SaaS 저장소를 고르면 "Terraform + CLI 스크립트 + 수동 단계"가 섞인다. 수동 단계는 사용자가 리뷰할 수 없으므로, 판정 단계에서 **"자동화 불가 단계 수"를 비용·능력과 함께 후보 순위에 반영**해야 한다. 서울 리전이 없는 SaaS(Neon, Turso, Prisma Postgres, Convex, Appwrite, Pinecone, RTDB)는 D5에서 먼저 걸러지므로 이 문제가 줄어든다.
