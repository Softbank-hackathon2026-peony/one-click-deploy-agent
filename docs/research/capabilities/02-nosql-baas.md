# 구성 요소 능력 표 — 문서·키-값·BaaS 데이터베이스

- 작성일: 2026-10-01 (모든 출처 확인일 2026-10-01)
- 형식·능력 키: [README.md](README.md) §1, §2.1 (DS.*). 요구 쪽: [../dimensions.md](../dimensions.md)
- 범위: Firebase(Cloud Firestore Standard/Enterprise, Realtime Database), Supabase(BaaS 플랫폼 관점), Amazon DynamoDB(단일 리전·글로벌 테이블), MongoDB Atlas(Free·Flex / Dedicated), Amazon DocumentDB, Google Cloud Spanner, Google Cloud Bigtable, Appwrite Cloud, PocketBase, Convex, pgvector, Pinecone
- 범위 밖: Postgres 엔진 자체 능력(격리 수준, 잠금, 온라인 DDL)은 [01-sql-databases.md](01-sql-databases.md). Supabase Realtime·Storage·Edge Functions의 세부 능력은 03·04 파일이 맡고, 여기서는 DB와의 관계와 플랜 한도만 적는다.

### 출처 표기 규칙
- 인용은 공식 문서 원문(영어)이다. WebFetch의 추출 텍스트에서 가져왔다. 표나 페이지 구조 때문에 문장으로 인용할 수 없을 때는 `(요약)`이라고 붙였다. 이 경우 값은 해당 페이지에서 읽은 것이지만 문장 그대로는 아니다.
- 서울 가격 중 AWS 값은 AWS 공식 Price List API(`pricing.us-east-1.amazonaws.com/offers/v1.0/aws/<서비스>/current/ap-northeast-2/index.json`, publicationDate 2026-09-11)에서 읽었다. GCP 서울 가격은 cloud.google.com 가격 페이지에 내장된 표에서 읽었다. 읽지 못한 경우 리전을 밝혔다.
- 확인하지 못한 값은 `미확인`, 해당하지 않는 값은 `해당 없음`으로 적었다.

## 목차

0. [요약 비교표](#0-요약-비교표)
1. [Cloud Firestore — Standard 에디션](#1-cloud-firestore--standard-에디션)
2. [Cloud Firestore — Enterprise 에디션(MongoDB 호환)](#2-cloud-firestore--enterprise-에디션mongodb-호환)
3. [Firebase Realtime Database](#3-firebase-realtime-database)
4. [Supabase — BaaS 플랫폼(Free / Pro / Team)](#4-supabase--baas-플랫폼free--pro--team)
5. [Amazon DynamoDB — 단일 리전 테이블(온디맨드 / 프로비저닝)](#5-amazon-dynamodb--단일-리전-테이블온디맨드--프로비저닝)
6. [Amazon DynamoDB — 글로벌 테이블(MREC / MRSC)](#6-amazon-dynamodb--글로벌-테이블mrec--mrsc)
7. [MongoDB Atlas — Free·Flex](#7-mongodb-atlas--freeflex)
8. [MongoDB Atlas — Dedicated(M10+)](#8-mongodb-atlas--dedicatedm10)
9. [Amazon DocumentDB — 인스턴스 기반 클러스터(Elastic·Serverless 병기)](#9-amazon-documentdb--인스턴스-기반-클러스터elasticserverless-병기)
10. [Google Cloud Spanner](#10-google-cloud-spanner)
11. [Google Cloud Bigtable](#11-google-cloud-bigtable)
12. [Appwrite Cloud(Free / Pro)](#12-appwrite-cloudfree--pro)
13. [PocketBase — 자체 호스팅](#13-pocketbase--자체-호스팅)
14. [Convex(Free·Starter / Professional)](#14-convexfreestarter--professional)
15. [pgvector — Postgres 확장](#15-pgvector--postgres-확장)
16. [Pinecone — Serverless](#16-pinecone--serverless)
17. [판정에 쓰는 교차 규칙 메모](#17-판정에-쓰는-교차-규칙-메모)

---

## 0. 요약 비교표

각 칸의 근거는 본문 항목에 있다. "직접 접근"은 브라우저·모바일 클라이언트가 서버 없이 DB를 호출할 수 있는지를 뜻한다.

| 구성 요소 | 서울 | 트랜잭션 범위·한도 | 경합·쓰기 한도 | 조인·질의 제약 | 문서/항목 크기 | 백업·PITR 기본 | 직접 접근·보안 기본 | 무료 플랜 함정 | 최소 고정비 |
|---|---|---|---|---|---|---|---|---|---|
| Firestore Standard | 있음(asia-northeast3) | 다문서 직렬화, 270초(유휴 60초), 오프라인 시 실패 | 단일 문서 갱신률 제한("unlimited rate" 아님), 새 컬렉션 500 ops/s → 5분마다 +50% | 조인 없음, OR/IN 30개, 집계는 인덱스 1000건당 1읽기 | 1 MiB | PITR 꺼짐(켜면 7일), 예약 백업 최대 14주 | 직접(Security Rules), 서버 SDK는 규칙 우회 | Spark 일 5만 읽기/2만 쓰기 | $0 (건당 과금, scale-to-zero) |
| Firestore Enterprise | 있음 | 270초/60초, 기본 낙관적 동시성 | Standard와 같은 문서 경합 모델 | 파이프라인으로 서버 측 조인, 전문 검색(Preview) | 16 MiB(Mongo 호환) | Standard와 같음 | 직접(Native 모드 SDK) | 일 5만 읽기 단위/4만 쓰기 단위 | $0 (4 KiB 읽기·1 KiB 쓰기 단위) |
| Realtime Database | **없음**(us-central1, europe-west1, asia-southeast1) | 단일 서브트리만 | DB당 약 1,000 writes/s, 20만 연결 → 샤딩 | 정렬·필터 중 하나만, 조인·집계 없음 | 값 10 MB, 깊이 32 | 자동 백업 Blaze만(일일 JSON), PITR 미확인 | 직접(규칙), 테스트 모드 공개 | Spark 동시 연결 100 | $0 (저장 $5/GB) |
| Supabase | 있음(ap-northeast-2) | supabase-js는 호출 간 트랜잭션 없음 → `rpc()` 함수 | Postgres 그대로, 연결 수는 컴퓨트 크기에 묶임(Nano/Micro 60) | Postgres 전체(FK 임베딩, FTS, PostGIS, pgvector) | DB Free 500 MB(초과 시 읽기 전용) | Free 백업 없음, Pro 일일 7일, PITR 유료(Small 이상) | 직접(Data API + RLS), RLS 없으면 노출 | 1주 비활동 시 일시정지, 2개 프로젝트 | Pro $25/월 |
| DynamoDB 단일 리전 | 있음 | 최대 100개 쓰기 액션, 4 MB, 같은 계정·리전, 2배 비용 | 파티션당 1,000 WCU/3,000 RCU, 충돌은 예외(트랜잭션은 SDK 재시도 안 함) | 조인 없음, Scan은 전체 읽기 과금, GSI 20개 | 400 KB | PITR 꺼짐(켜면 1~35일, 초 단위) | 서버 전용(IAM), 클라이언트는 STS 임시 자격 | 상시 무료 25 GB | $0 (온디맨드, 서울 쓰기 $0.68/100만) |
| DynamoDB 글로벌 테이블 | 있음(MRSC 포함) | **리전 간 트랜잭션 없음**, MRSC는 트랜잭션 미지원 | MREC 최종 쓰기 우선, MRSC 동시 쓰기 충돌 예외 | 단일 리전과 같음 | 400 KB | 리전별 | 서버 전용 | 해당 없음 | 복제 쓰기 리전마다 과금 |
| Atlas Free·Flex | GCP 서울만(AWS 서울은 M10+) | 다문서 60초 기본 | Free 100 ops/s, Flex 500 ops/s 하드 한도 | `$lookup`(미확인), Search/Vector 인덱스 Free 3·Flex 10 | 16 MiB | Free 백업 불가, Flex 일일 스냅샷 8개·PITR 없음 | 서버 전용(App Services EOL), IP 목록 기본 거부 | Free 30일 비활동 일시정지, 0.5 GB | Free $0, Flex $8~30 |
| Atlas Dedicated | 있음(AWS·GCP) | 60초 기본, WriteConflict 재시도 | 문서 단위 원자성 | 집계 파이프라인, Search, Vector | 16 MiB | 연속 백업(PITR) 신규 기본 켜짐(유료) | 서버 전용, 감사 M10+ | 해당 없음 | M10 약 $57/월 |
| DocumentDB | 있음 | 다문서 1분, 32 MB 로그, 스냅샷 격리; Elastic은 트랜잭션 없음 | 단일 프라이머리 쓰기 | Mongo API 일부(버전별 차이 큼) | 16 MiB | 자동 백업 끌 수 없음(기본 1일, 최대 35일), PITR 최근 5분 이전까지 | VPC 전용 | 무료 등급 없음(30일 체험) | t4g.medium 약 $84/월(서울) |
| Spanner | 있음(regional-asia-northeast3) | 직렬화+외부 일관성, 커밋당 8만 뮤테이션·100 MiB | 잠금 + wound-wait, 클라이언트 라이브러리 자동 재시도 | SQL 조인(쿼리당 20), FTS·벡터는 Enterprise | 셀 10 MiB | 버전 보존 기본 1시간(최대 7일) | 서버 전용(IAM) | 90일 무료 체험 후 삭제 | 100 PU Standard 약 $66/월(아이오와) |
| Bigtable | 있음(asia-northeast3) | **단일 행만** | 단일 행 원자성, 조건부 쓰기는 단일 클러스터 라우팅만 | 행 키 범위 스캔만, SQL은 읽기 전용·조인 없음 | 셀 권장 10 MB, 행 100 MB | 백업(최대 90~365일), PITR 없음 | 서버 전용(IAM) | 없음 | 노드 1개 약 $475/월(아이오와) |
| Appwrite Cloud | **없음**(SGP·SYD 등) | 트랜잭션: Free 100·Pro 1,000 작업 | 충돌 시 커밋 실패(자동 재시도 없음), 원자적 증감 있음 | 관계 지원, DocumentsDB 전문 검색 | 미확인 | Free 없음, Pro 일일 7일 | 직접(권한 모델), 서버 키는 권한 우회 | 7일 비활동 일시정지, 90일 후 삭제 | Pro $25/월 |
| PocketBase | 호스팅 위치 따름 | 단일 쓰기 트랜잭션(SQLite WAL) | **동시 쓰기 1개** | 필터·관계 확장 6단계 | 미확인 | 내장 백업(ZIP, S3), 수동 설정 | 직접(API 규칙), 기본 superuser 전용 | 해당 없음 | VPS 비용만 |
| Convex | **없음**(미 동부, EU, 시드니, 캐나다) | 뮤테이션 = 트랜잭션, 1초, 쓰기 1.6만 문서·16 MiB | OCC 직렬화 자동 재실행, 동시 뮤테이션 16(Free)/256(Pro) | 조인은 코드로, 벡터 검색은 액션에서만 | 1 MiB | 주기 백업 유료 플랜 | 함수 경유만(RLS 없음, 함수에서 권한 검사) | 한도 초과 시 쓰기 실패 | $0 / Pro $25/개발자 |
| pgvector | 호스트 Postgres 따름 | Postgres 따름 | Postgres 따름 | 근사 인덱스는 **사후 필터**(재현율 하락) | 인덱스 차원 vector 2,000 / halfvec 4,000 | Postgres 따름 | Postgres 따름 | 해당 없음 | 호스트 비용 |
| Pinecone | **없음**(Starter는 us-east-1만) | 없음 | 네임스페이스당 upsert 100 req/s | 메타데이터 필터, 결과적 일관성 | 메타데이터 40 KB | Starter 백업 불가 | 서버 API 키 | 2 GB, 쿼터 도달 시 읽기 차단 | $0 / Standard 최소 $50/월 |

---

## 1. Cloud Firestore — Standard 에디션

- 계열: 저장소-문서
- 서울 리전: 있음 (https://firebase.google.com/docs/firestore/locations · "asia-northeast3 Seoul" · 2026-10-01)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 다수, 문서 단위 잠금 | 서버 클라이언트 라이브러리는 비관적 잠금이 기본. 잠금을 잡고 있으면 다른 쓰기는 대기한다 | https://docs.cloud.google.com/firestore/native/docs/transaction-data-contention · "Pessimistic transactions use database locks to prevent other operations from modifying data." / "other write operations must wait for the transaction to release its lock." |
| DS.row_contention | 원자적 증가(`FieldValue.increment`), 트랜잭션 경합 시 ABORTED 후 재시도. 단일 문서 갱신률에 상한 있음(수치는 워크로드 의존) | 카운터는 샤딩 권장(샤드 10개 = 10배). 과거 "문서당 초당 1회" 수치는 현재 문서에서 미확인 | https://docs.cloud.google.com/firestore/native/docs/transaction-data-contention · "ABORTED: Too much contention on these documents. Please try again." / https://firebase.google.com/docs/firestore/solutions/counters · "you can't update a single document at an unlimited rate" / https://firebase.google.com/docs/firestore/best-practices · "The exact maximum rate that an app can update a single document depends highly on the workload." |
| DS.transactions | 다문서·다컬렉션 트랜잭션, 직렬화 격리 | 최대 270초, 유휴 60초 만료. 문서 하나에 필드 변환 500개(커밋당). 쓰기 문서 수 상한(과거 500)은 현재 쿼터 페이지에서 미확인. 오프라인이면 실패. 모바일·웹 SDK는 항상 낙관적 동시성을 흉내 내고, 충돌하면 트랜잭션 함수를 다시 실행한다 | https://firebase.google.com/docs/firestore/quotas · "Time limit for a transaction 270 seconds, with a 60-second idle expiration time" / https://docs.cloud.google.com/firestore/native/docs/transaction-data-contention · "Firestore guarantees serializable isolation of transactions." "The mobile and web SDKs behave independently of this setting as they always emulate optimistic concurrency." / https://firebase.google.com/docs/firestore/manage-data/transactions · "Transactions will fail when the client is offline." |
| DS.replication | 동기 복제, 강한 일관성. 리전 위치는 리전 내 다중 존, 멀티 리전 위치(eur3, nam5, nam7)도 있음 | 서울은 리전 위치뿐. 별도 읽기 복제본 개념 없음 | https://firebase.google.com/docs/firestore/locations · "Data in a regional location is replicated in multiple zones within a region." / https://firebase.google.com/docs/firestore · "automatic multi-region data replication, strong consistency guarantees, atomic batch operations, and ACID transaction support." |
| DS.query_models | 키·필터·정렬 질의, 집계(count/sum/average), 벡터 KNN(최대 2048차원, 벡터 인덱스 필요). **조인 없음, 전문 검색 없음**. 모든 질의에 인덱스 필요 | OR 분리항·IN 최대 30개. 집계는 실시간 리스너·오프라인 미지원(요약). 지리 질의 네이티브 지원은 미확인(해법 문서만 있음) | https://docs.cloud.google.com/firestore/native/docs/editions-overview · "All queries require covered indexes" / Text search Standard "No" (요약) / https://firebase.google.com/docs/firestore/query-data/queries · "These queries are limited to 30 disjunctions based on the query's disjunctive normal form." / https://firebase.google.com/docs/firestore/vector-search · 2048차원, EUCLIDEAN·COSINE·DOT_PRODUCT (요약) |
| DS.size_limits | 문서 1 MiB, 맵·배열 깊이 20, 하위 컬렉션 깊이 100, 프로젝트당 DB 100개 | DB 전체 용량 상한은 미확인(명시 없음) | https://firebase.google.com/docs/firestore/quotas · "Maximum size for a document 1 MiB (1,048,576 bytes)" / "Maximum number of databases per project 100" |
| DS.backup | **PITR 기본 꺼짐**(켜면 최대 7일). 끈 상태에서는 최근 1시간 버전만 읽을 수 있음. 예약 백업은 일·주 단위이고 보존은 최대 14주. 복원은 새 DB로만 | 관리형 내보내기·가져오기는 Blaze 요금제 필요. PITR 저장에는 무료 등급이 없음 | https://firebase.google.com/docs/firestore/pitr · "The PITR feature is disabled by default." / https://firebase.google.com/docs/firestore/backups · "Set this to a value up to 14 weeks" "A restore operation writes the data from a backup to a new Cloud Firestore database." / https://firebase.google.com/docs/firestore/manage-data/export-import · "Firebase projects must be on the Blaze plan to use the managed export and import service." |
| DS.connections | DB 연결 개념 없음(SDK, gRPC/HTTP). 동시 연결 상한 없음 | 클라이언트별 스냅샷 리스너 수 상한은 미확인 | https://firebase.google.com/docs/database/rtdb-vs-firestore · "No limits on concurrent connections or overall database writes/second rate. Has limits on write rates to individual documents or indexes." |
| DS.schema_change | 스키마 없음. 단일 필드 인덱스는 자동, 복합 인덱스는 수동 생성 | 스키마 변경은 앱 코드와 데이터 백필 책임 | https://firebase.google.com/docs/firestore/data-model · "Cloud Firestore is schemaless" / https://firebase.google.com/docs/firestore/query-data/index-overview · "By default, Cloud Firestore automatically creates single-field indexes for each field present within a collection." |
| DS.availability | 관리형, 존 장애 자동 대응. SLA는 리전 99.99%, 멀티 리전 99.999% | cloud.google.com/firestore/sla 원문은 잘려서 SLA 페이지에서는 확인하지 못함(위치 문서의 표로 확인) | https://firebase.google.com/docs/firestore/locations · "Cloud Firestore Multi-Region >= 99.999% Cloud Firestore Regional >= 99.99%" |
| DS.multi_host_access | 가능. 클라이언트 SDK와 서버 라이브러리가 인터넷으로 접근 | 해당 없음 | https://firebase.google.com/docs/firestore/quickstart · "Your authenticated application servers (C#, Go, Java, Node.js, PHP, Python, or Ruby) can still access your database." |
| DS.security | 클라이언트는 Security Rules로 통제. 시작 모드는 테스트(누구나 읽고 씀)와 프로덕션(모두 거부) 중 선택. **서버 라이브러리는 규칙을 우회**하고 IAM으로 통제. 저장 시 암호화는 기본. CMEK는 허용 목록(기본 쿼터 0). 데이터 액세스 감사 로그 있음. App Check 연동 | 규칙의 행 수준 권한 = RLS 대응물. 서버 경로에는 앱 코드의 권한 검사가 필요 | https://firebase.google.com/docs/firestore/quickstart · Test mode "allows anyone to read and overwrite your data" / Production mode "Denies all reads and writes from mobile and web clients." / https://firebase.google.com/docs/firestore/security/get-started · "The server client libraries bypass all Cloud Firestore Security Rules" / https://firebase.google.com/docs/firestore/quotas · CMEK DB "0 ... behind an allowlist" (요약) |
| DS.regions | 서울 리전 위치 있음. 멀티 리전은 eur3·nam5·nam7(아시아 멀티 리전 없음) | 위치는 생성 후 변경 불가인지 미확인 | https://firebase.google.com/docs/firestore/locations · "asia-northeast3 Seoul" |
| DS.scaling | 자동 수평 확장. 새 컬렉션은 500 ops/s로 시작해 5분마다 50%씩 늘리는 램프 권장. 순차 ID는 핫스팟을 만듦 | 예고 없는 폭증(D3)이 새 컬렉션·좁은 키 범위에 몰리면 지연·오류 | https://firebase.google.com/docs/firestore/best-practices · "We recommend starting with a maximum of 500 operations per second to a new collection and then increasing traffic by 50% every 5 minutes." |
| DS.cost_floor | $0, 건당 과금(scale-to-zero). 무료: 일 읽기 5만, 쓰기 2만, 삭제 2만, 저장 1 GiB | 서울 정가: 읽기 $0.038, 쓰기 $0.115, 삭제 $0.013(각 10만 건당), 저장 $0.192/GiB·월. 같은 페이지의 다른 표에는 $0.036/$0.108/$0.012로 나와 있어 차이를 해소하지 못함 | https://firebase.google.com/docs/firestore/quotas · "Document reads: 50,000 per day" "Document writes: 20,000 per day" / https://cloud.google.com/firestore/pricing · asia-northeast3 표 (요약) |

### 비용 구조
- 최소 월 고정비 $0. 변동 단위는 문서 읽기·쓰기·삭제 건수, 저장 GiB·월, 네트워크 출구. 무료 등급은 일 단위로 초기화된다.
- 과금 함정(https://firebase.google.com/docs/firestore/pricing):
  - 집계: "You are charged one read operation for each batch of up to 1000 index entries read by a query."
  - 결과 없는 질의도 과금: "There is a minimum charge of one document read for each query that you perform, even if the query returns no results."
  - 리스너: "you are charged for a read each time a document in the result set is added or updated." 오프라인 지속성이 켜진 상태에서 30분 넘게 끊기면 재연결 시 새 질의로 과금.
  - 결과: 목록 화면에 리스너를 많이 쓰거나 페이지마다 전체 컬렉션을 읽는 코드는 사용자 수에 비례해 읽기 수가 폭증한다. 예산 알림은 서비스를 멈추지 않는다(considerations/06 인용: "Budget alerts do not pause services.").
- PITR 저장에는 무료 등급이 없다.

### 교체 계열 정보
- SDK 형태: 클라이언트가 직접 접근한다(Web, Swift/Obj-C, Android Kotlin/Java, Flutter, Unity, C++). 오프라인 캐시와 실시간 리스너를 제공한다. 서버 라이브러리는 Node.js, Java, Python, Go, C#, PHP, Ruby로 제공되며 IAM 인증을 쓴다.
- 질의: 고유 API(SQL 아님). 일관성: 강한 일관성.
- 관계형으로 옮길 때 바뀌는 것:
  1. Security Rules를 서버 API의 권한 검사 또는 Postgres RLS로 옮긴다(Supabase로 가면 RLS로 대응 가능).
  2. 비정규화한 중복 필드와 하위 컬렉션을 정규화 테이블과 조인으로 바꾼다.
  3. `onSnapshot` 리스너를 Supabase Realtime, SSE, 웹소켓 등으로 대체한다.
  4. 오프라인 캐시를 대체해야 한다.
  5. `runTransaction`을 DB 트랜잭션으로 바꾼다.
- 관계형에서 옮겨올 때: 조인을 비정규화하거나 다중 질의로 바꾸고, 서버 권한 검사를 규칙으로 옮긴다. 30개 분리항 한도와 인덱스 선생성을 설계에 반영해야 한다.
- 내보내기: 관리형 export/import로 GCS에 내보낸다(Blaze 필요). BigQuery로 적재할 수 있다("You can also load Cloud Firestore exports into BigQuery.").

### 함정
- PITR이 기본으로 꺼져 있어 C7이 사용자 생성·금전 데이터면 바로 미충족이다.
- 서버 라이브러리(Admin SDK 포함)는 규칙을 우회한다. "규칙이 있으니 안전"은 클라이언트 경로에만 해당한다.
- 서버 SDK(비관적 잠금)와 모바일·웹 SDK(낙관적 동시성)의 경합 동작이 다르다. 재고 차감을 클라이언트 트랜잭션으로 하면 재실행이 반복되고, 오프라인이면 실패한다.
- 단일 문서 카운터·랭킹(C2 핫 문서)은 구조적으로 불리하다. 샤딩 카운터나 외부 저장소가 필요하다.
- 복원은 새 DB로만 된다. 앱의 DB ID 설정을 바꿔야 한다.

---

## 2. Cloud Firestore — Enterprise 에디션(MongoDB 호환)

- 계열: 저장소-문서
- 서울 리전: 있음 (https://cloud.google.com/firestore/enterprise/pricing · 서울 단가 표 존재 (요약) · 2026-10-01; 위치 목록은 Standard와 공유되는지 별도 확인하지 못함)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 다수, 문서 단위. 기본은 낙관적 동시성 | 서버 라이브러리는 DB의 동시성 모드 설정을 따름 | https://docs.cloud.google.com/firestore/native/docs/transaction-data-contention · Enterprise 기본 낙관적 (요약) |
| DS.row_contention | 낙관적 충돌 시 중단 후 재시도. 단일 문서 핫스팟 제약은 Standard와 같은 모델 | 문서당 갱신률 수치는 미확인 | 위와 같음 (요약) |
| DS.transactions | 다문서 트랜잭션, 270초/유휴 60초 | 직렬화 격리(Firestore 공통) | https://firebase.google.com/docs/firestore/enterprise/quotas · 270초/60초 (요약) |
| DS.replication | Firestore 공통(동기·강한 일관성) | Enterprise 전용 문구는 미확인 | https://firebase.google.com/docs/firestore · "strong consistency guarantees" |
| DS.query_models | 고급 질의 엔진(180개 넘는 스테이지·연산자). 인덱스 없이도 질의 가능. 파이프라인으로 **서버 측 조인**(상관 서브쿼리). 전문 검색(Preview). MongoDB 드라이버 호환 | 인덱스 없는 질의는 스캔 비용이 그대로 과금 | https://docs.cloud.google.com/firestore/native/docs/editions-overview · "More than 180 stages and operators" "performed with or without an index" / https://firebase.google.com/docs/firestore/enterprise/pipelines-overview · "Relational Joins: Perform server-side joins across collections and subcollections using correlated subqueries." |
| DS.size_limits | 문서 16 MiB(MongoDB 호환), Native 모드는 1 MiB | | https://docs.cloud.google.com/firestore/native/docs/editions-overview · "16 MiB with MongoDB compatibility" "1 MiB with Firestore in Native mode" |
| DS.backup | 예약 백업 최대 14주, PITR 7일(기본 꺼짐) | 백업 문서가 두 에디션 모두에 적용된다고 확인 | https://firebase.google.com/docs/firestore/backups · "Set this to a value up to 14 weeks" / https://firebase.google.com/docs/firestore/pitr · "disabled by default" |
| DS.connections | Native 모드는 SDK. MongoDB 호환 모드의 연결 한도는 미확인 | | 미확인 |
| DS.schema_change | 스키마 없음. 인덱스는 선택 | | https://docs.cloud.google.com/firestore/native/docs/editions-overview · "performed with or without an index" |
| DS.availability | Firestore 공통 SLA로 추정되지만 Enterprise 별도 수치는 미확인 | | 미확인 |
| DS.multi_host_access | 가능(서버·웹·모바일 SDK) | | https://docs.cloud.google.com/firestore/native/docs/editions-overview · "Supports Firestore in Native mode: server-side, web, and mobile SDKs with real-time and offline support" |
| DS.security | Security Rules(Native SDK) + IAM. Firestore 공통 | MongoDB 호환 접근의 인증 방식은 미확인 | https://firebase.google.com/docs/firestore/security/get-started · "The server client libraries bypass all Cloud Firestore Security Rules" |
| DS.regions | 서울 가격 표 있음 | | https://cloud.google.com/firestore/enterprise/pricing (요약) |
| DS.scaling | 자동(관리형) | 램프 규칙이 Enterprise에도 적용되는지 미확인 | 미확인 |
| DS.cost_floor | $0. 읽기는 4 KiB 단위, 쓰기는 1 KiB 단위로 과금. 무료: 일 읽기 단위 5만, 쓰기 단위 4만, 1 GiB | 서울: 읽기 단위 $0.0642/100만, 쓰기 단위 $0.3339/100만, 저장 $0.3072/GiB·월, 실시간 업데이트 $0.3853/100만. 같은 페이지의 다른 표($0.0545/$0.2834)와 차이를 해소하지 못함 | https://firebase.google.com/docs/firestore/enterprise/pricing · "calculated in 4 KiB tranches" "Writes are measured in 1 KiB units" / https://firebase.google.com/docs/firestore/enterprise/quotas · "Read units: 50,000 per day" "Write units: 40,000 per day" |

### 비용 구조
- 고정비 $0. 문서 수가 아니라 읽고 쓴 바이트 단위로 과금하므로 큰 문서와 인덱스 없는 스캔이 비싸다. 실시간 업데이트에는 별도 단가가 붙는다.

### 교체 계열 정보
- Native 모드 SDK는 Standard와 같다(클라이언트 직접 접근, 리스너, 오프라인). MongoDB 드라이버로도 접근할 수 있어 Mongo 앱을 옮겨오기 쉽다. 다만 MongoDB 호환 범위의 세부 사항은 미확인이다.
- Standard → Enterprise 전환 경로는 미확인.

### 함정
- 같은 "Firestore"라도 에디션마다 질의 능력(조인, 인덱스 없는 질의), 문서 크기, 과금 단위가 다르다. 판정 전에 에디션을 먼저 식별해야 한다.

---

## 3. Firebase Realtime Database

- 계열: 저장소-문서(JSON 트리) / 실시간
- 서울 리전: **없음** (https://firebase.google.com/docs/database/locations · 목록이 us-central1, europe-west1, asia-southeast1뿐 (요약) · 2026-10-01)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 다수. 잠금 단위는 경로(서브트리) | 개별 데이터 쓰기율에 로컬 한도 없음, DB 전체로 약 1,000 writes/s | https://firebase.google.com/docs/database/rtdb-vs-firestore · "No local limits on write rates to individual pieces of data." |
| DS.row_contention | 원자적 증가 연산 있음. 트랜잭션은 서브트리 단위 | 트랜잭션 초기값이 로컬 캐시에 없으면 null로 시작할 수 있음 | https://firebase.google.com/docs/database/web/read-and-write · "we can use an atomic increment operation instead of a transaction." |
| DS.transactions | 단일 서브트리만 원자적. 여러 경로에 걸친 트랜잭션 없음 | 다중 경로 갱신(update)은 원자적 쓰기지만 조건부가 아님(문구 미확인). 시간 한도 미확인 | https://firebase.google.com/docs/database/rtdb-vs-firestore · "Transactions are atomic on a specific data subtree." |
| DS.replication | 리전 단일, 존 단위 가용성 | 읽기 복제본 없음 | https://firebase.google.com/docs/database/rtdb-vs-firestore · "Realtime Database is a regional solution." "Databases are limited to zonal availability within a region." |
| DS.query_models | 속성 하나로 정렬 **또는** 필터(둘 다는 불가). 깊은 조회(서브트리 전체 반환). 조인·집계·전문·벡터 없음 | | https://firebase.google.com/docs/database/rtdb-vs-firestore · "Queries can sort or filter on a property, but not both." "Queries are deep by default: they always return the entire subtree." |
| DS.size_limits | 트리 깊이 32, 키 768바이트, 문자열 값 10 MB, 단일 응답 256 MB, SDK 쓰기 16 MB, REST 쓰기 256 MB, 쓰기 처리량 64 MB/분, 질의 타임아웃 15분 | | https://firebase.google.com/docs/database/usage/limits · 표 (요약) |
| DS.backup | 자동 백업은 Blaze만(일일 JSON을 GCS에). PITR 없음(미확인) | 백업 기능 자체는 무료, 저장 비용 별도 | https://firebase.google.com/docs/database/backups · "Blaze plan users can set up their Firebase Realtime Database for automatic backups" |
| DS.connections | DB당 동시 연결 20만. Spark 요금제는 100 | 초과하면 DB를 샤딩(여러 DB) | https://firebase.google.com/docs/database/usage/limits · "200,000" / https://firebase.google.com/pricing · Spark "100" (요약) |
| DS.schema_change | 스키마 없음, `.validate` 규칙으로 검증 | | https://firebase.google.com/docs/database/security/core-syntax (요약) |
| DS.availability | 관리형 단일 리전·존 단위. "typical uptime 99.95%". 공식 SLA 수치는 미확인 | | https://firebase.google.com/docs/database/rtdb-vs-firestore · "Typical uptime performance of 99.95%." |
| DS.multi_host_access | 가능(클라이언트 SDK, Admin SDK, REST) | | https://firebase.google.com/docs/database/admin/start · "Complete read and write access to a project's Realtime Database" |
| DS.security | 규칙 기반, 기본은 접근 불가. 테스트 모드는 공개였다가 기간이 지나면 전부 거부로 바뀜. Admin SDK는 전체 권한 | 감사 로그·CMEK는 미확인 | https://firebase.google.com/docs/database/security/core-syntax · "Access is disallowed by default." / https://firebase.google.com/docs/database/web/start · "your database rules will deny all requests" |
| DS.regions | 서울 없음(가장 가까운 곳은 싱가포르 asia-southeast1) | | https://firebase.google.com/docs/database/locations (요약) |
| DS.scaling | DB당 연결 약 20만, 쓰기 약 1,000/s. 그 이상은 여러 DB로 샤딩(Blaze) | | https://firebase.google.com/docs/database/rtdb-vs-firestore · "Scale to around 200,000 concurrent connections and 1,000 writes/second in a single database. Scaling beyond that requires sharding your data across multiple databases." |
| DS.cost_floor | $0. 저장 1 GB 무료 후 $5/GB·월, 다운로드 360 MB/일 무료 후 $1/GB | SSL·프로토콜 오버헤드도 다운로드로 과금 | https://firebase.google.com/pricing · "Then $5/GB" "Then $1/GB" / https://firebase.google.com/docs/database/usage/billing · "There is a cost associated with the SSL encryption overhead necessary for secure connections." |

### 비용 구조
- 저장 단가($5/GB)가 Firestore보다 크게 높고 다운로드량으로 과금한다. 깊은 조회 때문에 상위 경로를 구독하면 하위 전체가 내려와 전송비가 폭증한다.

### 교체 계열 정보
- 클라이언트 직접 접근 SDK(Web, iOS, Android, Flutter 등)와 Admin SDK, REST를 제공한다.
- Firestore나 관계형으로 옮기려면 JSON 트리 경로 구조를 컬렉션이나 테이블로 바꾸고, 정렬·필터 질의를 재작성하고, 리스너를 대체하고, 규칙을 서버 권한 검사로 옮겨야 한다.
- 내보내기: 콘솔 JSON 내보내기와 가져오기, 일일 JSON 백업(Blaze).

### 함정
- 서울 리전이 없다. D5나 국내 데이터 위치(F5) 요구가 있으면 즉시 불일치다.
- 쓰기 처리량은 DB 단위로 약 1,000/s 상한이다. 샤딩은 앱 코드가 맡는다.
- PITR이 없다. 일일 백업도 Blaze에서 직접 켜야 한다.

---

## 4. Supabase — BaaS 플랫폼(Free / Pro / Team)

- 계열: 저장소-관계형(Postgres) + BaaS(Auth·Storage·Realtime·Edge Functions)
- 서울 리전: 있음 (https://supabase.com/docs/guides/platform/regions · "Northeast Asia (Seoul), ap-northeast-2" · 2026-10-01)
- Postgres 엔진의 능력(격리, 잠금, DDL)은 01 파일을 따른다. 아래는 플랫폼이 더하거나 제한하는 부분이다.

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 다수(Postgres 행 잠금). 실질 상한은 컴퓨트 크기별 연결 수 | Supabase 자체 서비스(PostgREST, Auth, Storage)도 연결 예산을 나눠 씀. 풀 크기를 최대 연결의 40% 넘게 올리지 말라고 권고 | https://supabase.com/docs/guides/database/connection-management · "you should be conscientious about raising your pool size past 40% of the Database Max Connections." |
| DS.row_contention | Postgres 그대로(`UPDATE ... SET x = x + 1`, `SELECT FOR UPDATE`). 단 **supabase-js는 여러 호출을 한 트랜잭션으로 묶지 않음**. 원자적 처리는 Postgres 함수를 `rpc()`로 호출 | `security definer` 함수는 `search_path` 고정 필요 | https://supabase.com/docs/reference/javascript/rpc · "supabase-js does not group multiple queries into one transaction" / https://supabase.com/docs/guides/database/functions · "you can call them from your app with rpc()" |
| DS.transactions | 다중 행·다중 테이블(Postgres). 클라이언트에서는 함수 하나 = 한 번의 호출 단위로만 원자성 확보 | "PostgREST 요청 1건 = 트랜잭션 1건" 원문은 미확인(postgrest.org 응답 429) | https://supabase.com/docs/reference/javascript/rpc · 위와 같음 |
| DS.replication | 기본은 단일 인스턴스. 읽기 복제본은 Pro 이상 + Small 컴퓨트 이상 + PG15 이상. 비동기·읽기 전용 | 복제본 컴퓨트는 프라이머리와 같은 크기(그만큼 과금) | https://supabase.com/docs/guides/platform/read-replicas/getting-started · "Read Replicas are available for all projects on the Pro, Team and Enterprise plans." / https://supabase.com/docs/guides/platform/read-replicas · "Replication is asynchronous to ensure that transactions on the Primary aren't blocked." |
| DS.query_models | Postgres 전체. Data API(REST/GraphQL)는 FK 기반 임베딩(조인), 전문 검색, PostGIS, pgvector, Realtime Postgres Changes 제공 | Postgres Changes는 이벤트마다 구독자 수만큼 권한 검사를 하고 단일 스레드로 처리. 구독자 약 3,000명 이상이면 Broadcast 권장(요약) | https://supabase.com/docs/guides/database/joins-and-nesting · "Data API detects foreign key relationships and allows nested/embedded queries." / https://supabase.com/docs/guides/realtime/postgres-changes · "When you make a single change to a table with 100 subscribed users, Realtime performs 100 authorization checks" |
| DS.size_limits | Free: DB 500 MB(**초과하면 읽기 전용**), 파일 1 GB, 업로드 50 MB. Pro: 디스크 8 GB 포함(90%에서 50% 자동 확장), 파일 100 GB, 업로드 최대 500 GB | 디스크는 늘릴 수만 있고 줄일 수 없음. 컴퓨트별 최대 DB 크기(Nano 500 MB, Micro 10 GB, Small 50 GB …) | https://supabase.com/docs/guides/platform/database-size · "Free Plan projects enter read-only mode when your database size exceeds 500 MB." / https://supabase.com/docs/guides/storage/uploads/file-limits · "For Free projects, the limit can't exceed 50 MB." / https://supabase.com/docs/guides/platform/compute-and-disk · "you can increase disk size but cannot decrease it" |
| DS.backup | **Free 백업 없음**. Pro는 일일 백업 7일, Team 14일, Enterprise 최대 30일. PITR은 유료 애드온(Pro+, Small 컴퓨트 이상)이고 최악 RPO 2분 | PITR 7일 약 $100/월, 14일 $200, 28일 $400. 스펜드 캡 밖 | https://supabase.com/docs/guides/platform/backups · "We recommend that free tier plan projects regularly export their data using the Supabase CLI" / "can access the last 7 days of daily backups" / "Pro, Team and Enterprise Plan projects can enable PITR as an add-on" / https://supabase.com/pricing · "$100 per month per 7 days retention" |
| DS.connections | 직접 연결 최대 수와 풀러 클라이언트 수가 컴퓨트에 묶임: Nano/Micro 60/200, Small 90/400, Medium 120/600, Large 160/800 … 16XL 500/12,000. 내장 풀러 Supavisor(세션 5432, 트랜잭션 6543) | 직접 연결은 기본 IPv6. IPv4가 필요하면 공유 풀러 또는 IPv4 애드온(Pro+). 전용 풀러는 유료 플랜 | https://supabase.com/docs/guides/platform/compute-and-disk · 표 "Database Connections / Pooler Clients" (요약) / https://supabase.com/docs/guides/database/connecting-to-postgres · "Returns your connection to the pool after each transaction" |
| DS.schema_change | Postgres DDL(01 파일). 플랫폼은 마이그레이션 + 브랜칭(PR마다 프리뷰 DB, 병합 시 삭제) 제공 | 브랜치 컴퓨트는 스펜드 캡 밖. 브랜치 단가 미확인 | https://supabase.com/docs/guides/deployment/branching · "Applies pending database migrations and vault secrets to your branch" |
| DS.availability | 프로젝트당 Postgres 인스턴스 1개. 표준 플랜에 자동 페일오버 HA는 문서로 확인되지 않음. SLA(99.9%)는 Enterprise 계약 고객에만 적용 | HA(Multigres)는 문서 404라 미확인 | https://supabase.com/docs/guides/platform/compute-and-disk · "Every project on the Supabase Platform comes with its own dedicated Postgres instance." / https://supabase.com/sla · "will apply to the Services for Enterprise Customers specified in an Order Form" |
| DS.multi_host_access | 가능. 클라이언트는 Data API(HTTPS) + RLS, 서버는 Postgres 연결 문자열(직접, 풀러) | 네트워크 제한은 HTTPS API에 적용되지 않음 | https://supabase.com/docs/guides/platform/network-restrictions · "They don't apply to HTTPS APIs such as PostgREST, Storage, and Auth, or to Supabase client libraries like supabase-js." |
| DS.security | **노출 스키마의 테이블에 RLS가 없으면 권한 있는 역할 누구나 읽고 씀**. 기존 프로젝트에서는 새 `public` 테이블이 세 역할에 모든 권한을 갖고 시작(자동 grant를 회수하는 쪽으로 기본값 변경 예정, 날짜 없음). service_role·secret 키는 RLS 우회. Postgres 연결은 SSL 비강제가 기본, HTTP API는 SSL 강제. 플랫폼 감사 로그는 Team/Enterprise. SOC 2 Type 2, HIPAA는 BAA + 애드온 | 저장 암호화 문구는 미확인 | https://supabase.com/docs/guides/database/postgres/row-level-security · "A table in an exposed schema without RLS is readable and writable by any role with a grant on it." / "It bypasses RLS, so keep it server-side" / https://supabase.com/docs/guides/platform/ssl-enforcement · "supports connecting to the Postgres DB without SSL enabled" / https://supabase.com/docs/guides/security/platform-audit-logs · "Platform Audit Logs are only available on the Team and Enterprise plans." |
| DS.regions | 서울 있음(전체 17개 리전, 도쿄·싱가포르 포함) | | https://supabase.com/docs/guides/platform/regions · "Northeast Asia (Seoul), ap-northeast-2" |
| DS.scaling | 수직(Nano~16XL, 최대 64 vCPU/256 GB). 변경 시 보통 2분 미만 중단. 디스크 변경은 약 4시간 쿨다운. 수평은 읽기 복제본만 | 유료 플랜에서는 Nano 불가(Micro부터) | https://supabase.com/docs/guides/platform/compute-and-disk · "Compute instance changes are usually applied with less than 2 minutes of downtime" |
| DS.cost_floor | Free $0(활성 프로젝트 2개, 1주 비활동 시 일시정지). Pro $25/월부터(컴퓨트 크레딧 $10 포함 = Micro 1개). Team $599/월부터. scale-to-zero 없음(유료) | 스펜드 캡이 기본으로 켜져 있음(초과 사용 차단). 캡 밖 항목: 컴퓨트, 브랜치, 복제본, PITR, IPv4, MFA Phone 등 | https://supabase.com/pricing · "Limit of 2 active projects" "After 1 week of inactivity" "from $25/month" "$10/month in compute credits" "Spend caps are on by default" / https://supabase.com/docs/guides/platform/cost-control · "further usage of that item is disallowed until the next billing cycle" |

### 비용 구조
- 최소 고정비: Free $0(프로덕션 부적합), Pro $25/월(Micro 포함). Small은 약 $15, Medium 약 $60, Large 약 $110/월(컴퓨트 표 기준, 크레딧 $10 차감 전).
- 변동: 이그레스(포함량 Free 5+5 GB, Pro 250+250 GB, 초과 시 비캐시 $0.09/GB, 캐시 $0.03/GB), MAU(Free 5만, Pro 10만, 초과 $0.00325/MAU), 디스크 $0.125/GB, Realtime 메시지(Pro 500만 포함 후 100만당 $2.50), 동시 연결(Pro 500 포함 후 1,000당 $10), Edge Function 호출(Pro 200만 포함 후 100만당 $2).
  - 출처: https://supabase.com/docs/guides/platform/manage-your-usage/egress · "$0.09 per GB per month"
  - 출처: https://supabase.com/docs/guides/platform/manage-your-usage/monthly-active-users · "$0.00325 per MAU"
- 과금 함정:
  - 스펜드 캡이 켜져 있으면 한도 도달 시 서비스가 차단되어 장애가 된다.
  - 캡을 끄면 상한이 없다.
  - PITR($100/월~)과 읽기 복제본(프라이머리와 같은 컴퓨트)이 고정비를 크게 올린다.
- 플랫폼 한도(DB와 같은 프로젝트에 묶임):
  - Realtime 동시 연결: Free 200, Pro 500(캡 끄면 1만), Team 1만. 초당 메시지: 100 / 500 / 2,500 (https://supabase.com/docs/guides/realtime/limits)
  - Edge Functions: 메모리 256 MB, CPU 2초, 벽시계 Free 150초·유료 400초 (https://supabase.com/docs/guides/functions/limits · "Maximum CPU Time: 2s")
  - Auth: 내장 SMTP는 "2 emails per hour" (https://supabase.com/docs/guides/auth/rate-limits)
  - 로그 보존: Free 1일, Pro 7일, Team 28일 (https://supabase.com/pricing)

### 교체 계열 정보
- SDK: JavaScript, Flutter, Swift, Kotlin, Python, C#(https://supabase.com/docs/reference).
  - 클라이언트 직접 접근: publishable/anon 키 + RLS. 서버 접근: secret/service_role 키 또는 표준 `postgresql://` 연결.
  - 레거시 anon/service_role JWT 키는 2026년 말까지 단계적으로 폐지된다(요약, https://supabase.com/docs/guides/getting-started/api-keys).
- 이식성: "a full Postgres database, not a Postgres abstraction"(https://supabase.com/docs/guides/database/overview). 스키마·데이터·SQL은 다른 Postgres로 그대로 옮겨진다.
- Supabase를 떠날 때 바뀌는 것(추론, 근거는 각 행):
  1. Data API + RLS로 된 클라이언트 직접 접근을 서버 API의 권한 검사로 바꿔야 한다. RLS를 유지해도 `auth.uid()`는 Supabase Auth JWT에 의존한다.
  2. Realtime(Postgres Changes, Broadcast)을 대체해야 한다.
  3. Storage API를 S3 등으로 바꿔야 한다.
  4. Edge Functions(Deno)를 대체해야 한다.
- Firestore에서 옮겨올 때 바뀌는 것: Security Rules를 RLS 정책으로 바꾸고, 비정규화 데이터를 FK와 임베딩 조인으로 바꾸고, `onSnapshot`을 Realtime 구독으로 바꾸고, `runTransaction`을 `rpc()` 함수로 바꾼다.
- 내보내기(https://supabase.com/docs/guides/platform/migrating-within-supabase/backup-restore): `supabase db dump`로 역할, 스키마, 데이터(`--use-copy --data-only`)를 내보낸다.
  - 덤프에 포함되지 않는 것: Storage 객체, Edge Functions, auth·storage 스키마 변경(트리거, RLS), Vault 키.

### 함정
- Free는 1주 비활동이면 일시정지되고 백업이 없다. 500 MB를 넘으면 읽기 전용이 된다. 사용자 생성 데이터가 있는 공개 서비스에는 부적합하다.
- 자동 페일오버 HA가 없다(표준 플랜). SLA도 Enterprise에만 있다. F1이 "짧아야 함" 이상이면 불일치다.
- RLS가 꺼진 노출 테이블은 anon 키만으로 읽고 쓸 수 있다. 규칙 판정은 마이그레이션 SQL에서 `enable row level security`가 있는지 확인한다.
- 직접 연결은 IPv6가 기본이다. IPv4만 되는 호스트(일부 PaaS)에서는 풀러를 쓰거나 애드온이 필요하다. 서버리스에서는 트랜잭션 모드 풀러(6543)를 쓴다.
- 컴퓨트를 바꿀 때 약 2분간 중단된다.

---

## 5. Amazon DynamoDB — 단일 리전 테이블(온디맨드 / 프로비저닝)

- 계열: 저장소-문서(키-값)
- 서울 리전: 있음 (AWS Price List API ap-northeast-2 · "$0.68 per million write request units (Asia Pacific (Korea))" · 2026-10-01)
- 이하 DG = https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 무제한 HTTP 클라이언트. 항목 단위 원자적 쓰기 | 파티션 처리량 한도가 실질 상한 | DG WorkingWithItems.html · "All these operations are atomic." |
| DS.row_contention | 원자 카운터(`UpdateItem` ADD), 조건부 쓰기(버전 속성으로 낙관적 잠금). 파티션당 1,000 WCU/3,000 RCU. 진행 중인 트랜잭션과 충돌하면 `TransactionConflictException` | 원자 카운터는 멱등이 아님. 조건 실패도 WCU를 소비 | DG WorkingWithItems.html · "an atomic counter—a numeric attribute that is incremented, unconditionally, without interfering with other write requests." "With an atomic counter, the updates are not idempotent." / DG bp-partition-key-design.html · "maximum capacity of 3,000 read units per second and 1,000 write units per second." |
| DS.transactions | `TransactWriteItems`: 쓰기 액션 최대 100개, 합계 4 MB, 같은 계정·리전. 단일 항목 연산과는 직렬화 격리, 다중 읽기(BatchGet/Query/Scan)와는 read-committed. 클라이언트 토큰 멱등 10분 | 항목마다 준비·커밋 두 번씩 처리(2배 비용). 취소돼도 용량 소비. 취소(`TransactionCanceledException`)는 SDK가 재시도하지 않음 | DG transaction-apis.html · "groups up to 100 write actions in a single all-or-nothing operation" "The aggregate size of the items in the transaction cannot exceed 4 MB." "A client token is valid for 10 minutes" "AWS SDKs do not retry the request." |
| DS.replication | 리전 내 3개 AZ 자동 복제. 읽기는 결과적 일관성이 기본이고 강한 일관성은 선택(2배 비용). **GSI·스트림 읽기는 결과적 일관성만** | | DG HowItWorks.ReadConsistency.html · "eventually consistent (default) and strongly consistent reads. All reads from GSIs and streams are eventually consistent." / DG Introduction.html · "automatically replicates your data across three Availability Zones" |
| DS.query_models | 키 질의(Query), 전체 Scan, GSI(기본 20개)·LSI(5개, 생성 시만), PartiQL 부분 집합, 벡터 인덱스(테이블당 5개). **조인 없음**, 서버 측 집계 없음(문구 미확인) | Scan은 필터와 무관하게 읽은 양만큼 과금, 페이지당 1 MB | DG Introduction.html · "DynamoDB doesn't support a JOIN operator." / DG Scan.html · "a Scan consumes the same amount of read capacity, regardless of whether a filter expression is present." / DG ServiceQuotas.html · "default quota of 20 global secondary indexes per table." |
| DS.size_limits | 항목 400 KB, 중첩 32단계, 테이블 크기 실질 무제한. LSI가 있으면 파티션 키 값당 10 GB | | DG WorkingWithItems.html · "The maximum size of an individual item is 400 KB." / DG LSI.html · "10 GB size limit per partition key value." |
| DS.backup | **PITR 기본 꺼짐**. 켜면 1~35일, 초 단위. 복원은 항상 새 테이블로. 온디맨드 전체 백업, AWS Backup 연동 | S3 내보내기에는 PITR 필요. PITR 비용은 보존 기간과 무관(테이블 크기 기준) | DG PointInTimeRecovery_Howitworks.html · "DISABLED by default until you enable PITR" "between 1 and 35 days" "always restores to a new table." |
| DS.connections | 연결 개념 없음(HTTPS API + IAM 서명). 서버리스에서 연결 고갈 문제 없음 | 명시적 "연결 한도 없음" 문구는 미확인 | DG Introduction.html · "there are no user names or passwords for accessing DynamoDB" |
| DS.schema_change | 기본 키 외 스키마 없음. GSI는 나중에 추가 가능(백필 중 새 GSI에는 오토스케일링 미적용). LSI와 키 스키마는 생성 후 변경 불가(키 스키마 문구 미확인) | 접근 패턴이 바뀌면 GSI 추가나 데이터 재적재 필요 | DG HowItWorks.CoreComponents.html · "neither the attributes nor their data types need to be defined beforehand." |
| DS.availability | 리전 내 다중 AZ, 유지보수 창 없음. SLA 99.99%(글로벌 테이블은 99.999%) | | https://aws.amazon.com/dynamodb/sla/ · "at least 99.99% if the Standard SLA applies" (요약) / DG Introduction.html · "there are no maintenance windows." |
| DS.multi_host_access | 가능(리전 HTTPS 엔드포인트) | | DG Introduction.html (요약) |
| DS.security | IAM. **저장 암호화 기본**(AWS 소유 키). `dynamodb:LeadingKeys`로 파티션 키 = 사용자 ID 수준의 항목 접근 제어. VPC 게이트웨이·인터페이스 엔드포인트. CloudTrail | | DG EncryptionAtRest.html · "All user data stored in Amazon DynamoDB is fully encrypted at rest." / DG specifying-conditions.html · "allows users to access only the items where the partition key value matches their user ID" |
| DS.regions | 서울 있음 | | AWS Price List API ap-northeast-2 (APN2 SKU) |
| DS.scaling | 온디맨드(기본·권장): 직전 피크의 2배까지 즉시 수용, 30분 안에 2배를 넘으면 스로틀 가능. 새 테이블은 4,000 쓰기/12,000 읽기/s. 프로비저닝: 오토스케일링(목표 20~90%, 2분 지속 후 반응, 그 사이 스로틀). 적응형 용량 자동, 버스트 300초 | 테이블 기본 쿼터 40,000 RRU/WRU(상향 가능). 프로비저닝→온디맨드 전환은 24시간에 4회 | DG on-demand-capacity-mode.html · "instantly accommodates up to double the previous peak traffic on a table." "throttling can occur if you exceed double your previous peak within 30 minutes." / DG burst-adaptive-capacity.html · "Adaptive capacity is enabled automatically for every DynamoDB table" |
| DS.cost_floor | $0(온디맨드, 트래픽 없으면 처리량 과금 없음). 상시 무료 25 GB + 프로비저닝 25 WCU/25 RCU | 서울: 쓰기 $0.68/100만 WRU, 읽기 $0.1355/100만 RRU, 저장 $0.27075/GB·월(25 GB 초과분), PITR $0.2166/GB·월, 온디맨드 백업 $0.1083/GB·월 | AWS Price List API ap-northeast-2 · "$0.68 per million write request units (Asia Pacific (Korea))" "$0.1355 per million read request units" / DG Introduction.html · "25 GB of storage... 25 provisioned Write and 25 provisioned Read Capacity Units" |

### 비용 구조
- 고정비 $0(온디맨드). 프로비저닝은 설정한 용량만큼 시간당 과금한다(서울 단가는 이 문서에서 미확인).
- 과금 함정:
  - Scan은 반환량이 아니라 읽은 양으로 과금한다.
  - 트랜잭션 쓰기는 1 KB당 2 WRU다(https://aws.amazon.com/dynamodb/pricing/on-demand/ · "Transactional writes require 2 WRUs per 1 KB" (요약)).
  - 강한 일관성 읽기는 2배다.
  - GSI마다 쓰기가 증폭된다("A table with many global secondary indexes incurs higher costs for write activity", DG GSI.html). 인덱스 키가 바뀌면 쓰기가 2번 일어난다.
  - 실패한 조건부 쓰기와 취소된 트랜잭션도 과금된다.

### 교체 계열 정보
- SDK: AWS SDK(서버 측), HTTPS + SigV4.
  - 브라우저나 모바일 직접 접근은 웹 ID 연동으로 STS 임시 자격을 받아야 한다(DG WIF.html · "obtain temporary security credentials from AWS Security Token Service"). 이 경우 LeadingKeys 조건으로 권한을 건다.
  - 언어 목록 원문은 미확인.
- 질의 방언: DynamoDB API 또는 PartiQL 부분 집합. 일관성: 결과적 일관성 기본, 강한 일관성 선택.
- 관계형에서 옮겨올 때: 접근 패턴 중심의 비정규화 또는 단일 테이블 설계가 필요하다("We recommend that you denormalize your data model to reduce database round trips", DG Introduction.html).
  - 조인은 사전 결합 항목이나 GSI로 바꾼다.
  - 다중 행 SQL 트랜잭션은 `TransactWriteItems`(100개 한도)로 바꾼다.
  - 재고 차감 같은 경합은 조건부 쓰기로 바꾼다.
- 관계형으로 옮길 때: 단일 테이블의 항목 유형을 여러 테이블로 정규화해야 한다. 조건부 쓰기는 `UPDATE ... WHERE`나 트랜잭션으로 바꾼다.
- 내보내기·가져오기:
  - S3로 내보내기: PITR이 필요하고, RCU를 소비하지 않으며, 형식은 DynamoDB JSON이나 Ion이다.
  - S3에서 가져오기: 새 테이블로만 가능하다("Import into existing tables is not currently supported.", DG S3DataImport.HowItWorks.html).

### 함정
- PITR이 기본으로 꺼져 있다. S3 내보내기도 PITR이 있어야 된다.
- 트랜잭션 취소는 SDK가 재시도하지 않는다. 앱 코드에 재시도와 멱등 토큰이 없으면 재고 차감 같은 흐름에서 오류가 사용자에게 그대로 노출된다.
- GSI는 결과적 일관성만 지원한다. "쓰기 직후 GSI로 조회"하는 흐름(C3 쓰기 후 읽기)은 깨질 수 있다.
- 온디맨드에서도 직전 피크의 2배를 넘는 급격한 폭증(D3)은 스로틀될 수 있다.

---

## 6. Amazon DynamoDB — 글로벌 테이블(MREC / MRSC)

- 계열: 저장소-문서(키-값), 다중 리전
- 서울 리전: 있음. MRSC 지원 리전에도 포함 (DG V2globaltables_HowItWorks.html · "Asia Pacific (Seoul)" · 2026-10-01)
- 단일 리전과 같은 키는 5절을 따른다. 아래는 글로벌 테이블이 바꾸는 값이다.

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 모든 복제본이 읽기·쓰기 가능(멀티 액티브) | | DG GlobalTables.html · "Any global table replica can serve reads and writes." |
| DS.row_contention | MREC: 최종 쓰기 우선(last writer wins). MRSC: 리전 간 동시 쓰기는 `ReplicatedWriteConflictException` | | DG V2globaltables_HowItWorks.html · "last writer wins" (요약) / ReplicatedWriteConflictException (요약) |
| DS.transactions | **리전 간 트랜잭션 없음**. 다른 리전에서는 부분 완료된 트랜잭션이 보일 수 있음. MRSC는 트랜잭션 연산 자체를 지원하지 않음 | | DG transaction-apis.html · "Transactions aren't supported across Regions in global tables." / DG V2globaltables_HowItWorks.html · "Global tables configured for multi-Region strong consistency (MRSC) do not support transaction operations" |
| DS.replication | MREC(기본): 비동기, 보통 1초 이내. MRSC: 쓰기를 반환하기 전에 최소 한 다른 리전에 동기 복제, 정확히 3개 리전(복제본 2 + 증인 1 가능) | MRSC는 TTL·LSI 미지원. 기존 테이블은 비어 있어야 전환 가능. 일관성 모드는 생성 후 변경 불가 | DG V2globaltables_HowItWorks.html · "asynchronously replicated to all other replicas, typically within a second or less" "synchronously replicated to at least one other Region before the write operation returns" "A MRSC global table must be deployed in exactly three Regions." |
| DS.query_models | 단일 리전과 같음 | | 5절 |
| DS.size_limits | 단일 리전과 같음 | | 5절 |
| DS.backup | 리전별 PITR 설정(단일 리전과 같은 규칙) | 글로벌 테이블 전용 문구는 미확인 | 미확인 |
| DS.connections | 연결 없음(HTTPS) | | 5절 |
| DS.schema_change | 단일 리전과 같음. MRSC는 LSI 불가 | | DG V2globaltables_HowItWorks.html (요약) |
| DS.availability | SLA 99.999% | | https://aws.amazon.com/dynamodb/sla/ · "at least 99.999% if the Global Tables SLA applies" (요약) |
| DS.multi_host_access | 여러 리전의 앱이 각자 가까운 복제본에 접근 | | DG GlobalTables.html |
| DS.security | 단일 리전과 같음 | | 5절 |
| DS.regions | 서울 포함, MRSC 가능 | | DG V2globaltables_HowItWorks.html · "Asia Pacific (Seoul)" |
| DS.scaling | 리전마다 단일 리전과 같은 규칙 | | 5절 |
| DS.cost_floor | 복제 쓰기를 복제본 리전마다 과금(서울 $0.68/100만 복제 WRU) | 저장도 리전마다 과금 | AWS Price List API ap-northeast-2 (요약) |

### 비용 구조
- 쓰기 비용이 리전 수만큼 늘어난다. 저장도 리전마다 과금된다.

### 교체 계열 정보
- 코드는 단일 리전과 같다. 다만 리전별 엔드포인트를 선택해야 하고, 충돌 처리(MREC는 최종 쓰기 우선)를 설계에 반영해야 한다.

### 함정
- F2(재난 대비) 때문에 글로벌 테이블로 가면 리전 간 트랜잭션을 잃는다(C3와 F2가 충돌). MRSC는 트랜잭션을 아예 못 쓴다.
- MREC에서 같은 항목을 두 리전에서 동시에 갱신하면 한쪽 쓰기가 조용히 사라진다(최종 쓰기 우선).

---

## 7. MongoDB Atlas — Free·Flex

- 계열: 저장소-문서
- 서울 리전: 일부. GCP asia-northeast3는 Free·Flex·M10+ 모두 가능하지만 **AWS ap-northeast-2는 M10+만** (https://www.mongodb.com/docs/atlas/reference/google-gcp/ · "asia-northeast3 Seoul, Korea ASIA_NORTHEAST_3 ✓ ✓ ✓" / https://www.mongodb.com/docs/atlas/reference/amazon-aws/ (요약) · 2026-10-01)
- 참고: Atlas 문서는 "Atlas Core"와 "Atlas Infinite" 에디션으로 나뉘었고, Free 클러스터는 "formerly known as M0"이다.

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 다수, 문서 단위 원자성 | **Free 100 ops/s, Flex 500 ops/s 하드 한도** | https://www.mongodb.com/docs/manual/core/transactions/ · "In MongoDB, an operation on a single document is atomic." / https://www.mongodb.com/docs/atlas/reference/free-shared-limitations/ · "Free clusters: 100 operations per second" / https://www.mongodb.com/docs/atlas/reference/flex-limitations/ · "limit the number of read and write operations to 500 operations per second." |
| DS.row_contention | 문서 단위 원자 갱신. 트랜잭션 중 외부 쓰기와 충돌하면 WriteConflict, 일시 오류는 TransientTransactionError(재시도 로직 필요). 잠금 획득 대기 기본 5 ms | `$inc` 원문은 미확인 | https://www.mongodb.com/docs/manual/core/transactions-production-consideration/ (요약) |
| DS.transactions | 다문서·다컬렉션 트랜잭션, 기본 60초(`transactionLifetimeLimitSeconds`). 단독 배포에서는 미지원(Atlas는 레플리카셋) | Free·Flex 한도 페이지에 트랜잭션 제한은 없음(나열되지 않음) | https://www.mongodb.com/docs/manual/core/transactions-production-consideration/ · "Standalone deployments do not support transactions." |
| DS.replication | 3노드 레플리카셋, 기본 write concern `w: "majority"` | 보조 노드 읽기의 지연 허용은 `maxStalenessSeconds`(원문 미확인) | https://www.mongodb.com/docs/manual/core/replica-set-write-concern/ (요약) |
| DS.query_models | 문서 질의, 집계 파이프라인. Atlas Search/Vector Search 인덱스는 Free 3개, Flex 10개. Free는 서버 측 JS(`$where`, map-reduce) 불가 | `$lookup`·지리 질의 원문은 미확인 | https://www.mongodb.com/docs/atlas/atlas-search/limitations/ · "3 indexes (regardless of type, search or vector)" / https://www.mongodb.com/docs/atlas/reference/free-shared-limitations/ · "Free clusters don't support server-side JavaScript." |
| DS.size_limits | 문서 16 MiB. Free 저장 0.5 GB, DB 100·컬렉션 500, 전송 7일 기준 10 GB 입·출. Flex 저장 5 GB(비압축 BSON + 인덱스) | 저장 자동 확장 없음 | https://www.mongodb.com/docs/manual/reference/limits/ · "The maximum BSON document size is 16 mebibytes (MiB)." / free-shared-limitations · "Free clusters: 0.5 GB" / flex-limitations · "Flex clusters limit the maximum total data storage space to 5 GB." |
| DS.backup | **Free 백업 불가**(mongodump 권장). Flex는 일일 스냅샷, 최근 8개 보존. 연속 백업·PITR·온디맨드 스냅샷 없음 | | free-shared-limitations · "You can't enable backups on Free clusters." / https://www.mongodb.com/docs/atlas/backup/cloud-backup/flex-cluster-backup/ · "Atlas retains the last 8 daily snapshots." / flex-limitations · "Flex clusters don't support Continuous Backup and Point-in-Time Restore." |
| DS.connections | 최대 500 연결(Free·Flex) | | free-shared-limitations · "Free clusters can only have a maximum of 500 connections." / flex-limitations · "Flex clusters have a maximum of 500 connections." |
| DS.schema_change | 스키마 없음(선택적 스키마 검증) | Prisma Migrate는 MongoDB 미지원(`db push` 사용) | https://www.prisma.io/docs/orm/overview/databases/mongodb (요약) |
| DS.availability | 3노드 레플리카셋. SLA 적용 티어는 미확인(SLA 법률 페이지 404). **Free는 30일 비활동 시 자동 일시정지** | | free-shared-limitations · "Atlas automatically pauses Free clusters after 30 days of inactivity" |
| DS.multi_host_access | IP 접근 목록에 있는 호스트면 가능(드라이버 연결) | 서버리스·동적 IP 플랫폼은 0.0.0.0/0을 열어야 하는 경우가 생김(추론) | https://www.mongodb.com/docs/atlas/security/ip-access-list/ · "Atlas only allows client connections to the cluster from entries in the project's IP access list." |
| DS.security | IP 목록 기본 거부, TLS 필수. Free는 네트워크 피어링·프라이빗 엔드포인트·감사 불가. Flex는 프라이빗 엔드포인트·감사·고객 키 암호화 불가 | 행 수준 권한 없음(앱에서 처리) | https://www.mongodb.com/docs/atlas/setup-cluster-security.md · "Atlas requires TLS" / free-shared-limitations · "Free clusters don't support private endpoints." "You can't configure database auditing on Free clusters." |
| DS.regions | 서울은 GCP에서만 Free·Flex 가능 | | 위 서울 리전 근거 |
| DS.scaling | 저장 자동 확장 없음. Flex → Dedicated 업그레이드로 확장 | | free-shared-limitations · "Free clusters don't provide automatically scaling storage." |
| DS.cost_floor | Free $0(프로젝트당 1개). Flex는 $8/월(0~100 ops/s)에서 단계적으로 $30/월(400~500 ops/s)까지 | | https://www.mongodb.com/pricing · "Up to $30/month" / https://www.mongodb.com/docs/atlas/billing/atlas-flex-costs/ (요약) / https://www.mongodb.com/docs/atlas/reference/atlas-limits.md · "You can deploy only one Free cluster ... per project" |

### 비용 구조
- Free $0, Flex $8~30/월(ops/s 구간 과금, 500 ops/s에서 하드 상한). 전송량 한도가 있다.

### 교체 계열 정보
- SDK: 서버 전용 MongoDB 드라이버. Atlas App Services와 Data API는 EOL이다("Atlas App Services has reached its end-of-life status and is no longer actively supported by MongoDB.", https://www.mongodb.com/docs/atlas/app-services/data-api/data-api-deprecation.md). 클라이언트 직접 접근 경로는 없다고 보고 서버 API가 필요하다. 정확한 EOL 날짜는 미확인.
- Prisma: 중첩 쓰기에 트랜잭션을 쓰며 레플리카셋이 필요하다. Migrate는 미지원이다.
- 내보내기: mongodump·mongoexport.

### 함정
- AWS 서울에서는 Free·Flex를 만들 수 없다. Vercel이나 AWS 기반 앱이 "서울 + 무료"를 원하면 GCP 서울을 써야 한다.
- Free 100 ops/s, Flex 500 ops/s는 하드 한도다. D3 폭증 시 거부된다.
- Free는 백업이 없고 30일 비활동 시 일시정지된다. Flex는 PITR이 없다(최악 RPO 약 1일, 일일 스냅샷 기준 추론).

---

## 8. MongoDB Atlas — Dedicated(M10+)

- 계열: 저장소-문서
- 서울 리전: 있음(AWS ap-northeast-2 M10+, GCP asia-northeast3) (https://www.mongodb.com/docs/atlas/reference/amazon-aws/ (요약) · 2026-10-01)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 다수, 문서 단위(단일 프라이머리 쓰기) | | https://www.mongodb.com/docs/manual/core/transactions/ · "an operation on a single document is atomic." |
| DS.row_contention | 문서 단위 원자 갱신, WriteConflict·TransientTransactionError 재시도 | | https://www.mongodb.com/docs/manual/core/transactions-production-consideration/ (요약) |
| DS.transactions | 다문서·다컬렉션, 60초 기본. oplog 항목당 16 MB | 데이터 모델링으로 분산 트랜잭션 필요성을 줄이라고 권고 | https://www.mongodb.com/docs/manual/core/transactions/ · "modeling your data appropriately will minimize the need for distributed transactions." |
| DS.replication | 3노드 레플리카셋, `w: "majority"` 기본. `w: 1`이면 프라이머리 교체 시 롤백 가능 | | https://www.mongodb.com/docs/atlas/reference/atlas-limits.md · "Your M10 Atlas Core cluster has three nodes" / https://www.mongodb.com/docs/manual/reference/write-concern/ · "Data can be rolled back if the primary steps down" (considerations/04 인용) |
| DS.query_models | 집계 파이프라인, Atlas Search(전문), Vector Search(6.0.11/7.0.2 이상) | `$lookup`·지리 원문은 미확인 | https://www.mongodb.com/docs/atlas/atlas-vector-search/vector-search-overview/ · "supports ANN search on Atlas Clusters running MongoDB v6.0.11, v7.0.2, or later" |
| DS.size_limits | 문서 16 MiB, 저장은 티어별(구체 수치 미확인) | | https://www.mongodb.com/docs/manual/reference/limits/ |
| DS.backup | 연속 클라우드 백업(PITR)이 신규 클러스터에서 기본 켜짐. Core에서 켜면 월 비용 증가 | PITR 보존 기본값은 미확인 | https://www.mongodb.com/docs/atlas/backup/cloud-backup/dedicated-cluster-backup/ · "Enabling continuous cloud backups increases the monthly cost" (요약 포함) |
| DS.connections | 노드당 M10 1,500, M20/M30 3,000, M40 6,000(노드당 10개 예약). M10/M20은 새 연결 15/s 제한 | 매뉴얼의 "200 concurrent" 문구와 충돌하며, atlas-limits를 우선함 | https://www.mongodb.com/docs/atlas/reference/atlas-limits.md · "three nodes with a 1500 connection limit per node." |
| DS.schema_change | 스키마 없음(선택적 검증) | | 해당 없음 |
| DS.availability | 3노드 자동 페일오버. SLA 99.995%(적용 티어 원문 미확인) | | https://www.mongodb.com/cloud/atlas/reliability · "99.995% Uptime SLA: Atlas guarantees high availability for production workloads" |
| DS.multi_host_access | 가능(IP 목록, 피어링, 프라이빗 엔드포인트) | | https://www.mongodb.com/docs/atlas/security/ip-access-list/ |
| DS.security | IP 목록 기본 거부, TLS 필수, 감사(M10+), 고객 키 암호화, 프라이빗 엔드포인트 | 행 수준 권한 없음 | https://www.mongodb.com/docs/atlas/setup-cluster-security.md · "Atlas requires TLS" |
| DS.regions | 서울 AWS·GCP | | 위와 같음 |
| DS.scaling | 반응형 오토스케일링(모든 Dedicated Core 티어), 예측형은 M30+ | | https://www.mongodb.com/docs/atlas/cluster-autoscaling-compute-core/ · "reactive auto-scaling is available for all dedicated Atlas Core cluster tiers" |
| DS.cost_floor | M10 $0.08/시간(약 $56.94/월) | 리전별 단가는 미확인(가격 페이지 기본값) | https://www.mongodb.com/pricing · M10 $0.08/hr (요약) |

### 비용 구조
- M10이 최소 약 $57/월이다. 연속 백업, 전송, 추가 저장은 별도로 과금된다. 상시 과금이며 scale-to-zero가 없다.

### 교체 계열 정보
- MongoDB 드라이버(서버 전용)를 쓴다. 다른 MongoDB, DocumentDB, Firestore Enterprise로 옮길 때 호환 범위를 확인해야 한다.
- 관계형으로 옮길 때: 임베디드 문서를 정규화 테이블로 바꾸고, `$lookup`을 조인으로, 집계 파이프라인을 SQL `GROUP BY`로 바꾼다. Prisma를 쓰고 있다면 provider를 바꾸고 스키마를 재작성해야 한다.
- 내보내기: mongodump/mongorestore, 백업 스냅샷.

### 함정
- 연결 문자열에 `w=1`이 있으면 페일오버 때 쓰기가 롤백될 수 있다(C7·F3).
- Prisma로 MongoDB를 쓰면 Migrate를 쓸 수 없어 스키마 변경 관리(C9)가 약하다.

---

## 9. Amazon DocumentDB — 인스턴스 기반 클러스터(Elastic·Serverless 병기)

- 계열: 저장소-문서(MongoDB API 호환)
- 서울 리전: 있음 (https://docs.aws.amazon.com/documentdb/latest/developerguide/limits.html · "Asia Pacific (Seoul) | ap-northeast-2 | 4" · 2026-10-01)
- 이하 DD = https://docs.aws.amazon.com/documentdb/latest/developerguide/

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 클러스터당 프라이머리 1개(쓰기), 복제본 최대 15개(읽기 전용). Elastic 클러스터는 최대 32 샤드로 쓰기 분산 | | DD replication.html · "A single Amazon DocumentDB cluster supports a single primary instance and up to 15 replica instances." |
| DS.row_contention | 다문서 CRUD 문장도 원자성 보장, `$inc` 지원. 문서 수준 쓰기 잠금 타임아웃 1분(변경 불가) | WriteConflict 오류 의미는 미확인 | DD functional-differences.html · "guarantee atomicity and consistency, even for operations that modify multiple documents." / DD transactions.html · "Document-level write locks are subject to a 1 minute timeout" |
| DS.transactions | 4.0 이상: 여러 문서·컬렉션·DB에 걸친 트랜잭션, 스냅샷 격리. 실행 1분, 세션 30분, 트랜잭션 로그 32 MB 미만 | t3/t4g.medium의 열린 트랜잭션 50개. 트랜잭션 안에서 커서 불가. **Elastic 클러스터는 ACID 트랜잭션 미지원** | DD transactions.html · "Transactions have a one minute execution limit and sessions have a 30-minute timeout." "the transaction log size must be less than 32MB." "supports snapshot isolation by default" |
| DS.replication | 저장 볼륨에 3개 AZ로 6개 사본. 복제본은 결과적 일관성(보통 100 ms 미만, 대개 50 ms 이하). 글로벌 클러스터(리전 간) | | DD replication.html · "Replica instances are eventually consistent... usually much less than 100 milliseconds" / DD what-is.html · "replicates six copies of your data across three Availability Zones." |
| DS.query_models | MongoDB 3.6/4.0/5.0/8.0 API. 집계(최대 500 스테이지), `$lookup`, 지리(2dsphere), `$text`(5.0/8.0, Elastic 불가), 벡터(5.0+ 인덱스, `$vectorSearch`는 8.0) | `$where`·캡드 컬렉션·해시/와일드카드 인덱스 미지원. 8.0.2 미만은 retryable writes를 꺼야 함 | DD functional-differences.html · "retryable writes are not supported and you must disable them" "does not guarantee implicit result sort ordering" (요약 포함) |
| DS.size_limits | 문서 16 MiB, 클러스터 256 TiB(8.0, 이전 128 TiB), 컬렉션 32 TiB, 인덱스 64/컬렉션. Elastic 4 PiB | | DD limits.html · "256 TiB for Engine Version 8.0 and beyond (128 TiB for earlier engine versions)" |
| DS.backup | **자동 백업은 끌 수 없음**. 보존 기본 1일(1~35일). 보존 기간 안의 임의의 초로 복원 가능하지만 최근 5분 이전까지만. 복원은 새 클러스터로(인스턴스는 따로 추가) | Elastic은 PITR 미지원 | DD backup_restore-compare_automatic_manual_snapshots.html · "By default, new clusters have a backup retention period of 1 day." "You can't disable automatic backups" / DD what-is.html · "restore your cluster to any second during your retention period, up to the last 5 minutes." |
| DS.connections | 인스턴스별: t3/t4g.medium 1,000(활성 102), r6g.large 3,400(활성 1,100), r6g.xlarge 7,000, 최대 60,000. 내장 풀러 없음 | Elastic: min(300,000, 샤드 수 × 연결 쿼터) | DD limits.html (요약) |
| DS.schema_change | 유연 스키마, `$jsonSchema` 검증(4.0+). 컬렉션당 인덱스 빌드는 한 번에 하나, 기본은 포그라운드 | | DD functional-differences.html · "allows only one index build to occur on a collection at any given time." |
| DS.availability | 복제본이 있으면 페일오버 보통 30초 이내. 복제본이 없으면 같은 AZ에 새 인스턴스를 최선 노력으로 생성(시간 미확인). SLA 다중 AZ 99.99%, 단일 AZ 99.9% | | DD failover.html · "Failover typically completes within 30 seconds from start to finish." / https://aws.amazon.com/documentdb/sla/ (요약) |
| DS.multi_host_access | 가능, 단 VPC 안에서만(클러스터·리더 엔드포인트) | | DD what-is.html · "Amazon DocumentDB instances run only in the Amazon VPC environment." |
| DS.security | VPC 전용, 전송 중 TLS 기본 켜짐, KMS 저장 암호화(기본 여부 미확인). **감사 기본 꺼짐**(켜면 CloudWatch Logs). 사용자/암호 + RBAC | 행 수준 권한 없음 | DD security.encryption.ssl.html · "By default, encryption in transit is enabled for newly created Amazon DocumentDB clusters." / DD event-auditing.html · "By default, auditing is disabled on Amazon DocumentDB" |
| DS.regions | 서울 있음(Elastic, Serverless, T3/T4G 포함) | | DD limits.html |
| DS.scaling | 수직: 인스턴스 변경 수 분. 읽기: 복제본 수 분 안에 추가. 저장 10 GB 단위 자동 증가. Serverless: 0.5~256 DCU(1 DCU 약 2 GiB), 0 축소는 명시 없음. Elastic: 샤드 수평 확장 | | DD what-is.html · "Compute scaling operations typically complete in a few minutes." / DD docdb-serverless.html · "each DCU corresponds to approximately 2 GiB of memory" |
| DS.cost_floor | 서울: db.t4g.medium $0.11543/시간(약 $84/월), t3.medium $0.119/시간. I/O $0.24/100만, 저장 $0.12/GB·월(I/O 최적화는 $0.36). Serverless $0.0992/DCU·시간. 무료 등급 없음(30일 체험) | 초 단위 과금, 최소 10분 | AWS Price List API ap-northeast-2 · "$0.11543 per db.t4g.medium instance hour" / DD what-is.html · "billed in one second increments, with a minimum of 10 minutes." |

### 비용 구조
- 인스턴스 시간 과금이고 유휴여도 과금된다. 복제본마다 인스턴스 비용이 추가된다. Standard 스토리지는 I/O 요청이 별도로 과금된다. T 계열 CPU 크레딧 초과분은 vCPU·시간당 $0.09다.

### 교체 계열 정보
- MongoDB 드라이버와 도구를 그대로 쓴다("you can run the same application code and use the same drivers and tools that you use with MongoDB", DD what-is.html). VPC 전용이라 클라이언트 직접 접근은 불가하고 서버 전용이다.
- MongoDB에서 옮겨올 때 확인할 것: 미지원 연산자와 인덱스, 엔진 버전별 기능 차이(8.0 전용 연산 다수), 8.0.2 미만의 retryable writes 비활성화. DMS로 옮길 수 있다.
- 내보내기: mongodump, mongorestore, mongoexport, mongoimport(Database Tools 100.11.0 이하). admin DB는 덤프되지 않으므로 사용자·역할을 다시 만들어야 한다.

### 함정
- "MongoDB 호환"이라는 이름과 달리 엔진 버전마다 지원 범위가 다르다. retryable writes 기본값(드라이버에서 켜짐)이 4.0/5.0에서 오류를 낸다.
- Elastic 클러스터는 트랜잭션과 PITR이 없다. C3 요구가 있으면 Elastic 선택은 불일치다.
- 복제본 없는 단일 인스턴스는 빠른 페일오버가 없다.
- 감사가 기본으로 꺼져 있다.

---

## 10. Google Cloud Spanner

- 계열: 저장소-관계형(분산, GoogleSQL / PostgreSQL 방언)
- 서울 리전: 있음 (https://docs.cloud.google.com/spanner/docs/instance-configurations · "regional-asia-northeast3 Seoul" · 2026-10-01)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 다수, 행(셀) 단위 잠금, 분산 | | https://docs.cloud.google.com/spanner/docs/transactions · "locking read-write transactions" (요약) |
| DS.row_contention | 잠금 기반, 교착은 wound-wait로 해소, 중단된 트랜잭션은 클라이언트 라이브러리가 자동 재시도. 읽기 전용 트랜잭션은 잠금 없음 | 비활성 약 10초 후 잠금이 해제될 수 있음 | https://docs.cloud.google.com/spanner/docs/transactions · "wound-wait algorithm for deadlock detection" "Read-only transactions don't write, they don't hold locks and they don't block other transactions." |
| DS.transactions | 다중 행·다중 테이블, 기본 직렬화 + 외부 일관성(repeatable read 선택 가능). 커밋당 뮤테이션 80,000(인덱스 포함), 커밋 크기 100 MiB. 대량 처리용 Partitioned DML | | https://docs.cloud.google.com/spanner/quotas · "Mutations per commit (for Mutation API) (including indexes): 80,000" "Commit size (including indexes and change streams): 100 MiB" |
| DS.replication | 동기(Paxos). 리전 구성은 존 3개에 읽기·쓰기 복제본 3개, 쓰기 쿼럼 2/3. 멀티 리전은 Enterprise Plus | | https://docs.cloud.google.com/spanner/docs/instance-configurations · "three read-write replicas, each within a different Google Cloud zone" "Multi-region configurations are available with the Spanner Enterprise Plus edition." |
| DS.query_models | SQL 조인(쿼리당 최대 20), GoogleSQL/PostgreSQL 방언. 전문 검색·벡터·그래프는 Enterprise 이상 | | https://docs.cloud.google.com/spanner/docs/editions-overview (요약) / https://docs.cloud.google.com/spanner/quotas · 조인 20 (요약) |
| DS.size_limits | 셀 10 MiB, 키 8 KiB, DB당 테이블 5,000. 저장은 노드당 10 TiB(100 PU당 1,024 GiB), 100 PU당 DB 10개 | | https://docs.cloud.google.com/spanner/quotas · "10 TiB per node" "1024.0 GiB per 100 processing units" |
| DS.backup | 버전 보존(PITR) 기본 1시간, 최대 7일. 백업은 모든 에디션, 증분 백업은 Enterprise | 백업은 최소 24시간 과금 | https://docs.cloud.google.com/spanner/docs/pitr · "By default, your database retains all versions of its data and schema for one hour. You can increase this time limit to as long as seven days." |
| DS.connections | 세션 기반(gRPC). 최신 라이브러리는 멀티플렉스 세션이 기본이고, gRPC 채널 하나에 동시 요청 100개 | 하드 세션 한도는 명시 없음 | https://docs.cloud.google.com/spanner/docs/sessions · "enabled by default" "one gRPC channel can handle up to 100 concurrent requests" |
| DS.schema_change | 무중단 스키마 변경(장기 실행 작업, 검증이 큰 변경은 수 시간) | | https://docs.cloud.google.com/spanner/docs/schema-updates · "Spanner lets you make schema updates with no downtime." |
| DS.availability | SLA 리전 99.99%, 듀얼·멀티 리전 99.999%. 무료 체험 인스턴스는 SLA 없음 | | https://cloud.google.com/spanner/sla · "Regional Instance >= 99.99%" "Multi-Regional Instance >= 99.999%" / https://docs.cloud.google.com/spanner/docs/free-trial-instance · "SLAs don't apply to free trial instances" |
| DS.multi_host_access | 가능(클라이언트 라이브러리, PGAdapter) | | https://docs.cloud.google.com/spanner/docs/pgadapter |
| DS.security | IAM(원문 미확인), CMEK(모든 에디션, 무료 체험 제외) | 행 수준 권한 미확인 | https://docs.cloud.google.com/spanner/docs/editions-overview · "CMEK" (요약) / free-trial-instance · "Free trial instances don't support customer-managed encryption keys (CMEK)" |
| DS.regions | 서울 리전 구성 있음. asia1 멀티 리전의 증인 리전이기도 함 | | https://docs.cloud.google.com/spanner/docs/instance-configurations |
| DS.scaling | 처리 단위(PU) 100 단위로 온라인 증감(수 분). 1,000 PU = 1노드. 관리형 오토스케일러는 Enterprise. **일시정지 기능 없음** | | https://docs.cloud.google.com/spanner/docs/compute-capacity · "1000 PUs being equal to 1 node" "Spanner lacks a suspend function." (요약 포함) |
| DS.cost_floor | 아이오와 노드·시간: Standard $0.90, Enterprise $1.23, Enterprise Plus $1.71. 최소 100 PU Standard는 약 $0.09/시간(약 $66/월, 계산값). 저장 SSD 약 $0.30/GiB·월. 서울 단가는 미확인 | 프로비저닝은 최소 1시간 과금. 90일 무료 체험(10 GiB) | https://cloud.google.com/spanner/pricing · "Standard $0.90 / 1 hour" "billed for a minimum of one hour" / free-trial-instance · "at no cost for 90 days" |

### 비용 구조
- 상시 과금(scale-to-zero와 일시정지 없음). 최소 100 PU다. 멀티 리전에는 Enterprise Plus가 필요해 단가가 약 1.9배다. 백업은 최소 24시간 과금된다. 무료 체험은 90일 뒤 30일 유예를 거쳐 데이터가 삭제되고, 백업도 지원하지 않는다.

### 교체 계열 정보
- 서버 전용이다. 클라이언트 라이브러리(Java, Go, Node, Python 등. 목록 원문은 미확인)나 PGAdapter(node-postgres, Prisma, Drizzle, psycopg, JDBC 지원)를 쓴다("PGAdapter translates the PostgreSQL wire protocol into the Spanner gRPC protocol").
- Postgres에서 옮겨올 때: PostgreSQL 방언을 쓰더라도 순차 키를 피해야 한다(핫스팟). 인터리브 테이블 설계, 확장(extension) 미지원 여부(미확인)도 검토해야 한다.
- 내보내기: Dataflow로 GCS에 Avro나 CSV로 내보낸다(Dataflow·GCS 비용 별도). 출처: https://docs.cloud.google.com/spanner/docs/export · "The export process uses Dataflow and writes data to a folder in a Cloud Storage bucket."

### 함정
- 바이브코더 규모(C1·D2 낮음)에는 고정비가 과잉이다. 축소 판정 대상이다.
- 멀티 리전, 오토스케일러, 전문·벡터 검색은 상위 에디션이 필요하다.
- 무료 체험 인스턴스를 프로덕션으로 쓰면 120일 뒤 데이터가 삭제된다.

---

## 11. Google Cloud Bigtable

- 계열: 저장소-문서(와이드 컬럼 키-값)
- 서울 리전: 있음 (https://docs.cloud.google.com/bigtable/docs/locations · asia-northeast3-a/b/c (요약) · 2026-10-01)
- 참고: 에디션(Enterprise, Enterprise Plus)이 2026-04-22에 도입되었다(에디션 페이지 기준).

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 다수, 행 단위 원자성 | | https://docs.cloud.google.com/bigtable/docs/writes · "A single-row write is atomic." |
| DS.row_contention | 단일 행 ReadModifyWrite(증가)·CheckAndMutate(조건부). **실패해도 재시도하지 않음**. 다중 클러스터 라우팅에서는 조건부 쓰기 불가 | | https://docs.cloud.google.com/bigtable/docs/writes · "ReadModifyWriteRow requests are atomic. They are not retried if they fail for any reason." |
| DS.transactions | **단일 행만**. MutateRows는 항목별 원자적이고 요청 전체는 원자적이지 않음 | | https://docs.cloud.google.com/bigtable/docs/writes · "Each entry in a MutateRows request is atomic, but the request as a whole is not." |
| DS.replication | 클러스터 간 복제는 기본 결과적 일관성(수 초~수 분). 단일 클러스터 라우팅이면 쓰기 후 읽기 보장. 최대 8개 리전 | | https://docs.cloud.google.com/bigtable/docs/replication-overview · "By default, replication for Bigtable is eventually consistent." |
| DS.query_models | 행 키 하나만 인덱싱, 키 범위 스캔. GoogleSQL은 읽기 전용(INSERT/UPDATE/DELETE, 서브쿼리, JOIN, UNION, CTE 미지원). 연속 구체화 뷰 | 보조 인덱스 없음 | https://docs.cloud.google.com/bigtable/docs/overview · "A single value in each row is indexed. This value is known as the row key." / https://docs.cloud.google.com/bigtable/docs/googlesql-overview · "doesn't support ... INSERT, UPDATE, or DELETE ... subqueries, JOIN, UNION, and CTEs" |
| DS.size_limits | 하드 한도: 행 키 4 KB, 셀 100 MB, 행 256 MB. 권장: 셀 10 MB, 행 100 MB. 인스턴스당 테이블 1,000. 노드당 SSD 5 TB, HDD 16 TB | | https://docs.cloud.google.com/bigtable/quotas (요약) |
| DS.backup | 표준·핫 백업. 보존 최대 90일(Enterprise)·365일(Enterprise Plus), 자동 백업 최대 90일. PITR 없음. 기존 테이블로 복원 불가 | | https://docs.cloud.google.com/bigtable/docs/backups · "You can't restore from a backup to an existing table." |
| DS.connections | gRPC 클라이언트, 연결 한도는 미확인 | | 미확인 |
| DS.schema_change | 컬럼 패밀리만 정의(테이블당 100), 나머지는 스키마 없음 | | https://docs.cloud.google.com/bigtable/quotas (요약) |
| DS.availability | SLA: 3개 이상 리전 다중 클러스터 라우팅 99.999%, 3개 미만 99.99%, 단일 클러스터 라우팅·존 인스턴스 99.9% | | https://cloud.google.com/bigtable/sla · "Zonal instance (single cluster) >= 99.9%" |
| DS.multi_host_access | 가능(클라이언트 라이브러리) | | 해당 없음 |
| DS.security | IAM(프로젝트, 인스턴스, 테이블, 백업, 승인된 뷰 수준). `allUsers` 부여 불가. CMEK | | https://docs.cloud.google.com/bigtable/docs/access-control (요약) |
| DS.regions | 서울 3개 존 | | https://docs.cloud.google.com/bigtable/docs/locations |
| DS.scaling | 노드 수 오토스케일링(최대는 최소의 10배 이내), 확장 중에도 요청 계속 처리 | | https://docs.cloud.google.com/bigtable/docs/autoscaling · "All requests continue to reach the cluster while scaling and rebalancing are in progress." |
| DS.cost_floor | 클러스터당 최소 1노드. 아이오와 Enterprise $0.65/노드·시간(약 $475/월, 계산값), Enterprise Plus $0.85. SSD 약 $0.17/GiB·월. 서울 단가는 미확인 | 유휴여도 과금, 노드당 최소 1시간 | https://cloud.google.com/bigtable/pricing · "Enterprise $0.65 / 1 hour" "Charges apply even if your cluster is inactive." |

### 비용 구조
- 노드 1개가 상시 과금된다(약 $475/월, 아이오와). 대용량 시계열·이벤트 데이터용이다. 작은 앱에는 과잉이다.

### 교체 계열 정보
- 서버 전용 클라이언트 라이브러리를 쓰며 HBase API와 호환된다(원문 미확인). 행 키 설계가 질의 전부를 좌우하므로 관계형과의 상호 이식은 사실상 데이터 모델을 다시 짜야 한다.
- 내보내기: Dataflow 템플릿으로 Avro, Parquet, SequenceFile로 내보내고 가져온다.

### 함정
- 다중 리전 HA(다중 클러스터 라우팅)를 켜면 조건부 쓰기와 증가 연산을 쓸 수 없다. C2와 F2가 충돌한다.
- SQL은 읽기 전용이다.

---

## 12. Appwrite Cloud(Free / Pro)

- 계열: 저장소-문서(BaaS). Dedicated DB(관리형 Postgres) 옵션이 있다.
- 서울 리전: **없음** (https://appwrite.io/docs/products/network/regions · FRA, NYC, SYD, SFO, SGP, TOR (요약) · 2026-10-01)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 서버리스 DB는 미확인. Dedicated DB는 쓰기 프라이머리 1개 + 읽기 복제본, 커넥션 풀러 | | https://appwrite.io/products/databases · "Dedicated databases run behind a connection pooler with a primary for writes and read replicas" |
| DS.row_contention | 원자적 숫자 증감 지원. 트랜잭션 커밋 전에 외부 수정이 있으면 충돌로 실패(자동 재시도 없음, 다시 읽고 재구성) | | https://appwrite.io/docs/products/databases/tablesdb/atomic-numeric-operations · "Safely increment and decrement numeric fields without race conditions." / https://appwrite.io/docs/products/databases/documentsdb/transactions (요약) |
| DS.transactions | 여러 작업을 모아 원자적으로 커밋. 트랜잭션당 작업 수 Free 100, Pro 1,000. 스키마 작업(인덱스 생성 등)은 포함 불가 | 격리 수준 미확인 | https://appwrite.io/docs/products/databases/documentsdb/transactions · "Stage multiple database operations and commit them atomically." "Schema operations (for example, creating or deleting indexes) are not included in transactions." |
| DS.replication | 서버리스 미확인. Dedicated는 비동기·동기·쿼럼 선택, HA 복제본은 기본가의 50%씩 추가 | | https://appwrite.io/products/databases (요약) / https://appwrite.io/pricing (요약) |
| DS.query_models | TablesDB(관계형 스타일, 관계), DocumentsDB(JSON, 필터, 전문 검색), VectorsDB(임베딩), 관리형 Postgres(SQL, pgvector) | 조인 대신 관계("without custom joins") | https://appwrite.io/products/databases · "Relational-style tables, columns, and indexes" "Flexible JSON documents with filters and full-text search" "link related tables without custom joins" |
| DS.size_limits | Free: 저장 2 GB, 대역폭 5 GB, DB 1개, 프로젝트 2개. Pro 수치는 미확인(가격 표가 클라이언트 렌더링) | 문서·행 크기는 미확인 | https://appwrite.io/blog/post/best-free-hosting-platforms-you-probably-havent-tried-in-2026 · "2 GB storage" "1 Database" |
| DS.backup | Free 없음. 유료 플랜은 일일 백업 7일 보존. Dedicated DB는 PITR 7일(기본가 +20%) | | https://appwrite.io/blog/post/introducing-database-backups · "available on Appwrite Cloud for all paid plans" "a daily backup that is stored for 7 days" |
| DS.connections | 서버리스는 REST/SDK(연결 개념 없음, 추론). Dedicated는 네이티브 연결 문자열 | | https://appwrite.io/products/databases (요약) |
| DS.schema_change | 컬렉션·속성 정의(스키마 있음). 스키마 작업은 트랜잭션 밖 | 속성 변경 시 잠금 동작 미확인 | https://appwrite.io/docs/products/databases/documentsdb/transactions |
| DS.availability | SLA: Free 없음, Pro 99.5%, Scale 99.9%, Enterprise 99.95% | | https://appwrite.io/docs/advanced/billing/uptime-sla (요약) |
| DS.multi_host_access | 가능(관리형 API) | | 해당 없음 |
| DS.security | 권한 모델: 서버 SDK나 콘솔로 권한 없이 만들면 아무도 접근 불가. 클라이언트 SDK로 만들면 생성자에게 읽기·수정·삭제 권한. 서버 API 키는 권한 무시 | 감사·암호화 미확인 | https://appwrite.io/docs/advanced/security/permissions · "If you create a resource using a Server SDK or the Appwrite Console without explicit permissions, no one can access it by default" |
| DS.regions | 서울·도쿄 없음, 가장 가까운 곳은 싱가포르. 데이터는 리전 안에 머묾 | | https://appwrite.io/docs/products/network/regions · "All data remains within the region" |
| DS.scaling | 서버리스 관리형(세부 미확인). Dedicated는 Micro $10 ~ 4XL $960/월 | | https://appwrite.io/pricing (요약) |
| DS.cost_floor | Free $0. Pro $25/월(프로젝트 단위, 2025-09-01부터). Dedicated DB $10/월부터 | 대역폭 초과 100 GB당 $15 | https://appwrite.io/blog/post/appwrite-pricing-update (요약) / https://appwrite.io/pricing · "From $10/mo per database" |

### 비용 구조
- Free $0, Pro $25/월/프로젝트. Dedicated DB는 HA 복제본마다 +50%, PITR +20%다.

### 교체 계열 정보
- 클라이언트 SDK는 권한 모델 아래에서 직접 접근하고, 서버 SDK는 API 키로 접근하며 권한을 우회한다. SDK 언어 목록은 미확인이다.
- 마이그레이션 도구: Firebase, Supabase, Nhost에서 가져오기와 Cloud와 자체 호스팅 간 이동을 지원한다. `$createdAt`·`$updatedAt` 같은 필드는 옮겨지지 않을 수 있다("Certain fields, such as `$createdAt` and `$updatedAt`, may not be transferred.", https://appwrite.io/docs/advanced/migrations).
- 관계형으로 옮길 때: SDK 호출을 SQL이나 ORM으로 바꾸고, 문서 권한을 서버 권한 검사나 RLS로 바꾼다.

### 함정
- Free 프로젝트는 개발 활동 없이 7일이 지나면 일시정지된다(백업, 크론, 예약 함수도 중단). 90일 동안 정지 상태면 삭제된다(https://appwrite.io/changelog/entry/2026-02-20-1 · "Projects on the Free plan with no development activity for 7 consecutive days will be automatically paused." / https://appwrite.io/changelog/entry/2026-06-29 · "Free projects that stay paused for 90 days will be deleted").
- 서울 리전이 없다.

---

## 13. PocketBase — 자체 호스팅

- 계열: 저장소-관계형(내장 SQLite) + BaaS(인증, 파일, 실시간)
- 서울 리전: 호스팅 위치에 따름(해당 없음)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | **동시 쓰기 1개**(SQLite WAL, 단일 writer/트랜잭션) | 트랜잭션 안에서 다른 DB 핸들을 쓰면 교착 가능 | https://pocketbase.io/faq/ · "PocketBase uses embedded SQLite (in WAL mode)" / https://pocketbase.io/docs/js-database/ · "we allow only a single writer/transaction at a time and it could result in a deadlock" |
| DS.row_contention | 쓰기가 직렬화되므로 경합은 대기로 나타남 | 원자적 증감 연산자 지원은 미확인 | https://pocketbase.io/docs/js-database/ (위와 같음) |
| DS.transactions | `$app.runInTransaction`(서버 확장 코드). Batch API는 단일 읽기·쓰기 트랜잭션(대시보드에서 명시적으로 켜야 함, 다른 질의가 대기열에 쌓임) | | https://pocketbase.io/docs/js-database/ · "The DB operations are persisted only if the transaction completes without throwing an error." / https://pocketbase.io/docs/api-records/ · "other queries may queue up and it could degrade the performance" |
| DS.replication | 내장 복제 없음(미확인). 5 GB 넘는 DB는 SQLite 백업 + rsync 고려(요약) | | https://pocketbase.io/docs/going-to-production/ (요약) |
| DS.query_models | 필터 규칙, 관계 확장(6단계), 실시간 구독. 전문·벡터는 미확인 | | https://pocketbase.io/docs/api-records/ (요약) |
| DS.size_limits | 디스크와 SQLite 한도에 따름(미확인) | | 미확인 |
| DS.backup | 내장 백업(`pb_data` 전체 ZIP 스냅샷, 로컬 또는 S3). 자동 일정은 직접 설정. PITR 없음 | | https://pocketbase.io/docs/going-to-production/ · "The generated backup represents a full snapshot as ZIP archive of your pb_data directory." |
| DS.connections | 내장 DB라 외부 연결 없음. 실시간 연결 1만 개 이상 처리 가능(소형 VPS 예시) | | https://pocketbase.io/faq/ · "PocketBase can easily serve 10 000+ persistent realtime connections on a cheap $4 Hetzner CAX11 VPS" |
| DS.schema_change | 대시보드에서 컬렉션을 바꾸면 마이그레이션 파일이 자동 생성되고(`pb_migrations`), `serve` 때 적용 | | https://pocketbase.io/docs/js-migrations/ · "every collection configuration change from the Dashboard (or Web API) will generate the related migration file automatically" |
| DS.availability | 단일 서버, SLA 없음. 자원봉사로 유지되는 개인 오픈소스(요약) | 서버 재시작·배포 = 중단 | https://pocketbase.io/faq/ (요약) |
| DS.multi_host_access | **불가(단일 서버)**. 확장은 수직만 | 여러 인스턴스가 같은 파일을 공유하는 구성은 문서상 근거 없음(설계상 불가로 추론) | https://pocketbase.io/faq/ · "Only on a single server, aka. vertical." |
| DS.security | API 규칙: 잠금(null)이 **기본**이며 superuser만 접근 가능. 빈 문자열이면 누구나 접근. 내장 레이트 리미터, superuser IP 허용 목록, MFA, 설정 암호화 | | https://pocketbase.io/docs/api-rules-and-filters/ · "only by an authorized superuser (this is the default)" "anyone will be able to perform the action" |
| DS.regions | 호스팅 위치 따름 | | 해당 없음 |
| DS.scaling | 수직만 | | https://pocketbase.io/faq/ · "Only on a single server, aka. vertical." |
| DS.cost_floor | 소프트웨어 무료(MIT), 서버 비용만(FAQ 예시 $4 VPS) | | https://github.com/pocketbase/pocketbase (요약) / https://pocketbase.io/faq/ |

### 비용 구조
- VPS와 영속 디스크 비용만 든다. 티어 0 플랫폼(영속 디스크 없음)에는 올릴 수 없다. 영속 볼륨을 붙일 수 있는 단일 인스턴스 호스트가 필요하다(CP.local_disk와 대조).

### 교체 계열 정보
- REST 비슷한 API와 실시간 구독을 제공한다. JS·Dart SDK로 클라이언트가 직접 접근한다(SDK 사실은 추론, 근거 미확인). Go나 JS 훅으로 확장할 수 있다.
- Postgres(Supabase 등)로 옮길 때: SDK 호출을 Data API나 SQL로 바꾸고, API 규칙을 RLS나 서버 권한 검사로 바꾸고, 인증을 이전하고, 실시간 구독을 대체한다. SQLite 데이터는 표준 도구로 옮긴다(추론).
- 내보내기: `pb_data` ZIP 백업(SQLite 파일 포함).

### 함정
- 단일 쓰기와 단일 서버 구조다. C1 "중간" 이상이나 B2(인스턴스 2개 이상)가 필요하면 즉시 교체 대상이다. SQLite 판정 규칙과 같다.
- v1.0 전이라 하위 호환이 보장되지 않는다(https://github.com/pocketbase/pocketbase · "full backward compatibility is not guaranteed before reaching v1.0.0").

---

## 14. Convex(Free·Starter / Professional)

- 계열: 저장소-문서(반응형 BaaS, 서버 함수 내장)
- 서울 리전: **없음** (https://docs.convex.dev/production/regions · aws-us-east-1, aws-eu-west-1, aws-ap-southeast-2, aws-ca-central-1 (요약) · 2026-10-01)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 동시 뮤테이션 Free/Starter 16, Professional 256(배포 클래스 S16/S256, 최대 D2048) | | https://docs.convex.dev/production/state/limits (요약) |
| DS.row_contention | OCC(낙관적 동시성 제어). 충돌하면 트랜잭션을 자동으로 다시 실행. 진정한 직렬화 | 같은 문서에 몰리는 쓰기는 재실행이 반복됨(추론) | https://docs.convex.dev/database/advanced/occ · "true serializability" / on conflict "we can simply re-run the transaction" (요약 포함) |
| DS.transactions | 뮤테이션 1개 = 트랜잭션 1개(항상 원자적). 트랜잭션당 읽기 16 MiB, 스캔 32,000 문서, 인덱스 범위 4,096, 쓰기 16 MiB·16,000 문서. 질의·뮤테이션 1초 | 액션(외부 호출)은 트랜잭션이 아님(10분/30분) | https://docs.convex.dev/database/advanced/occ · "always be guaranteed to be atomic" / https://docs.convex.dev/production/state/limits · "1 second" "16,000" (요약) |
| DS.replication | 미확인 | | 미확인 |
| DS.query_models | 인덱스 기반 문서 질의, 조인은 함수 코드로. 전문 검색(질의당 16단어, 결과 1,024). 벡터 검색(2~4096차원, 결과 최대 256, 액션에서만, 필터는 등호·OR) | 벡터 검색은 일관적이고 최신 | https://docs.convex.dev/search/vector-search · "vector searches can only be performed in a Convex action" "Vector search is consistent and fully up-to-date" |
| DS.size_limits | 문서 1 MiB, 필드 1,024, 중첩 16. Free/Starter: DB 0.5 GB, 파일 1 GB, 함수 호출 100만. Professional: 50 GB, 100 GB, 2,500만 | | https://docs.convex.dev/production/state/limits · document "1 MiB" (요약) / https://www.convex.dev/pricing (요약) |
| DS.backup | 수동 백업 7일 보존. 주기 백업은 유료 플랜(일일 7일, 주간 14일). Free/Starter는 배포당 최대 2개. 복원은 파괴적 | | https://docs.convex.dev/database/backup-restore · "Daily backups are stored for 7 days. Weekly backups are stored for 14 days." |
| DS.connections | DB 직접 연결 없음. 클라이언트는 함수 호출(웹소켓·HTTP). 동시 질의 16/256 | | https://docs.convex.dev/production/state/limits (요약) |
| DS.schema_change | 스키마는 선택. 스키마를 추가·변경한 첫 푸시에서 기존 문서 전체를 검증하고, 불일치가 있으면 푸시 실패 | | https://docs.convex.dev/database/schemas · "If there are documents that fail validation, the push will fail." |
| DS.availability | SLA는 Business·Enterprise만 | | https://www.convex.dev/pricing (요약) |
| DS.multi_host_access | 관리형 API(해당 없음). 자체 호스팅 가능(SQLite·Postgres 백엔드) | | https://github.com/get-convex/convex-backend · "Self-hosted Convex works well with ... Sqlite, Postgres" |
| DS.security | RLS 없음. 공개 함수 시작 부분에서 인증·권한을 코드로 검사. 클라이언트는 DB에 직접 접근하지 않음 | | https://docs.convex.dev/auth · "simply write code that checks if the user is logged in and if they are allowed to do the requested action at the beginning of each public function." |
| DS.regions | 미 동부, EU 서부, 시드니, 캐나다. 한국·일본 없음. 배포 리전은 변경 불가 | | https://docs.convex.dev/production/regions · "An existing deployment's region cannot be changed." |
| DS.scaling | 배포 클래스(S16 ~ D2048) | | https://docs.convex.dev/production/state/limits (요약) |
| DS.cost_floor | Free/Starter $0(종량 과금). Professional $25/개발자·월. Business 월 최소 $2,500 | 함수 호출 초과 100만당 $2.20(Starter), $2.00(Pro) | https://www.convex.dev/pricing · "$25 per developer/month" "$2,500 monthly minimum" |

### 비용 구조
- 개발자 수에 비례하는 좌석 과금이다. 함수 호출, 저장, 대역폭은 종량 과금된다. 벡터 검색은 질의마다 인덱스 크기 기준으로 과금된다(요약).

### 교체 계열 정보
- 클라이언트(React 등 TypeScript)는 query·mutation·action 함수만 호출한다. 질의 결과는 반응형으로 자동 갱신된다.
- 관계형으로 옮길 때: Convex 함수를 API 서버와 SQL로 다시 작성하고, 반응형 구독을 대체하고, 함수 안의 권한 검사를 옮긴다. OCC 자동 재실행에 기댄 코드는 명시적 트랜잭션과 재시도로 바꾼다.
- 내보내기: `npx convex export`(JSONL, `_storage` 포함 가능), CSV/JSON 가져오기, Fivetran 스트리밍 내보내기.

### 함정
- 뮤테이션은 1초 안에 끝나야 하고 문서 쓰기 16,000개가 상한이다. 대량 배치는 액션이나 분할이 필요하다.
- Free 한도를 넘으면 새 쓰기가 실패할 수 있다("After these limits are hit on the Free plan, new mutations that attempt to commit more insertions or updates may fail.", https://docs.convex.dev/production/state/limits).
- 서울 리전이 없고, 배포를 만든 뒤에는 리전을 바꿀 수 없다.

---

## 15. pgvector — Postgres 확장

- 계열: 저장소-관계형의 확장(벡터 질의 능력만 더함)
- 서울 리전: 호스트 Postgres를 따름(Supabase, RDS, Cloud SQL 서울 제공 여부는 01 파일)
- 출처: https://github.com/pgvector/pgvector (README, 0.8.x)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 호스트 Postgres 따름 | | 해당 없음 |
| DS.row_contention | 호스트 Postgres 따름 | | 해당 없음 |
| DS.transactions | 호스트 Postgres 따름(벡터와 원본 데이터가 한 트랜잭션에 들어감) | | 해당 없음 |
| DS.replication | 호스트 Postgres 따름 | | 해당 없음 |
| DS.query_models | 기본은 정확한 최근접 검색(재현율 완전). 근사 인덱스는 HNSW(빠른 질의, 느린 빌드, 메모리 많음), IVFFlat(빠른 빌드, 메모리 적음, 질의 성능 낮음, 데이터로 학습 필요). **근사 인덱스는 필터를 스캔 뒤에 적용** | 0.8.0부터 반복 인덱스 스캔으로 보완. 테넌트 간 인덱스를 공유하면 재현율에 영향 | https://github.com/pgvector/pgvector · "By default, pgvector performs exact nearest neighbor search, which provides perfect recall." "With approximate indexes, filtering is applied *after* the index is scanned." |
| DS.size_limits | 인덱스 가능 차원: vector 2,000, halfvec 4,000, bit 64,000, sparsevec 비영 원소 1,000. 저장은 vector 16,000차원까지 | | https://github.com/pgvector/pgvector · "`vector` - up to 2,000 dimensions" "`halfvec` - up to 4,000 dimensions" |
| DS.backup | 호스트 Postgres 따름 | | 해당 없음 |
| DS.connections | 호스트 Postgres 따름 | | 해당 없음 |
| DS.schema_change | 인덱스 생성은 Postgres DDL. 근사 인덱스를 추가하면 질의 결과가 달라짐 | | https://github.com/pgvector/pgvector · "you will see different results for queries after adding an approximate index." |
| DS.availability | 호스트 Postgres 따름 | | 해당 없음 |
| DS.multi_host_access | 호스트 Postgres 따름 | | 해당 없음 |
| DS.security | 호스트 Postgres 따름(RLS 적용 가능) | | 해당 없음 |
| DS.regions | 호스트 따름 | | 해당 없음 |
| DS.scaling | 호스트 Postgres 따름. HNSW 인덱스 메모리가 인스턴스 크기를 정함 | | https://github.com/pgvector/pgvector · "uses more memory" |
| DS.cost_floor | 추가 비용 없음(확장). Postgres 13+ | | https://github.com/pgvector/pgvector · "supports Postgres 13+" |

### 비용 구조
- 별도 과금이 없다. 인덱스 메모리 때문에 컴퓨트를 키워야 할 수 있다.

### 교체 계열 정보
- SQL(`<->`, `<=>`, `<#>` 연산자)로 쓴다. 메타데이터 필터는 `WHERE` 절이다. Pinecone 등에서 옮겨오면 벡터와 메타데이터를 다시 적재하고 필터를 SQL로 바꿔야 한다.

### 함정
- 1536차원 이상 임베딩은 vector 인덱스 한도(2,000)에 가깝다. 3072차원 같은 큰 임베딩은 halfvec이나 차원 축소가 필요하다(4,000 한도 기준 추론).
- 선택적 필터와 근사 인덱스를 함께 쓰면 결과가 k개보다 적게 나온다(기본 ef_search 40에서 조건이 10%만 맞으면 평균 4행).

---

## 16. Pinecone — Serverless

- 계열: 저장소-문서(벡터 전용)
- 서울 리전: **없음** (https://docs.pinecone.io/troubleshooting/available-cloud-regions · AWS us-east-1·us-west-2·eu-west-1·eu-central-1·ap-southeast-1, GCP us-central1·europe-west4, Azure eastus2 (요약) · 2026-10-01)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| DS.concurrent_writers | 네임스페이스당 upsert 100 요청/초(모든 플랜) | | https://docs.pinecone.io/reference/api/database-limits/rate-limits (요약) |
| DS.row_contention | 해당 없음(레코드 덮어쓰기, 잠금 없음) | | 해당 없음 |
| DS.transactions | 해당 없음 | | 해당 없음 |
| DS.replication | 결과적 일관성(upsert 후 질의 반영에 지연) | 복제 구성은 미확인 | https://docs.pinecone.io/reference/api/known-limitations.md · "Pinecone is eventually consistent, so there can be a slight delay before upserted records are available to query." |
| DS.query_models | 밀집·희소 벡터, 전문 검색(BM25, Lucene 문법), 메타데이터 필터(`$eq`, `$gt`, `$in`, `$and`, `$or`, `$not`), 네임스페이스 멀티테넌시 | | https://docs.pinecone.io/guides/index-data/indexing-overview (요약) |
| DS.size_limits | 차원 최대 20,000, upsert 배치 1,000건·2 MB, 메타데이터 40 KB, top_k 10,000. Starter: 저장 2 GB, 프로젝트 1개, 인덱스 5개, 인덱스당 네임스페이스 100, 월 읽기 100만 RU·쓰기 200만 WU | | https://docs.pinecone.io/reference/api/database-limits/operation-limits · "20,000" (요약) / https://docs.pinecone.io/reference/api/database-limits/object-limits (요약) |
| DS.backup | Starter 백업 불가. Standard는 프로젝트당 500개, Enterprise 1,000개. 일·주·월 예약. $0.10/GB·월 | | https://docs.pinecone.io/guides/manage-data/back-up-an-index · "daily, weekly, or monthly frequency" / object-limits (요약) |
| DS.connections | API·SDK(연결 개념 없음, 추론) | | 해당 없음 |
| DS.schema_change | 차원·메트릭은 인덱스 생성 시 고정(제자리 변경 미확인) | | https://docs.pinecone.io/guides/index-data/indexing-overview (요약) |
| DS.availability | Enterprise만 99.95% SLA, 그 외는 미확인 | | https://www.pinecone.io/pricing/ · "99.95% Uptime SLA" |
| DS.multi_host_access | 가능(API) | | 해당 없음 |
| DS.security | RBAC, 감사 로그, 프라이빗 엔드포인트, CMEK는 Enterprise 전용 | | https://www.pinecone.io/pricing/ (요약) |
| DS.regions | 서울·도쿄 없음. **Starter는 AWS us-east-1만** | | https://docs.pinecone.io/troubleshooting/available-cloud-regions · "On the Starter plan, you can create serverless indexes in the `us-east-1` region of AWS only." |
| DS.scaling | 서버리스 사용량 기반, 유휴 인덱스는 비용 없음 | | https://docs.pinecone.io/guides/manage-cost/understanding-cost · "Idle indexes cost nothing." |
| DS.cost_floor | 월 최소: Starter $0, Builder $20(정액), Standard $50, Enterprise $500. 저장 $0.33/GB·월, 읽기 100만 RU당 $16~18, 쓰기 100만 WU당 $4~4.50 | | https://docs.pinecone.io/guides/manage-cost/understanding-cost · Starter "$0/month" Standard "$50/month" (요약) |

### 비용 구조
- 질의 비용이 네임스페이스 크기에 비례한다("a query uses 1 RU for every 1 GB of namespace size, with a minimum of 0.25 RUs per query.", understanding-cost). Starter와 Builder는 할당량에 도달하면 읽기가 차단된다(https://docs.pinecone.io/release-notes/2026.md · "reads that return record data are blocked once the allowance is reached").

### 교체 계열 정보
- 서버 측 API 키와 SDK(Python, Node 등. 목록 원문 미확인)를 쓴다.
- pgvector로 옮길 때: 벡터와 메타데이터를 다시 적재하고, 필터를 SQL `WHERE`로 바꾸고, 사후 필터 재현율 문제를 검토한다. 원본 데이터와 같은 트랜잭션에 넣을 수 있게 된다(이점).

### 함정
- 원본 DB와 벡터 저장소가 분리되어 있어 동기화(이중 쓰기) 정합성 문제가 생긴다(C3). 결과적 일관성이라 upsert 직후 검색에 안 나올 수 있다.
- Starter는 미국 리전만 쓸 수 있고 백업이 없다.

---

## 17. 판정에 쓰는 교차 규칙 메모

이 절은 위 값에서 바로 나오는 비교 규칙이다. 새 사실은 없다.

| 요구(차원) | 능력 미달 구성 요소 | 근거 키 |
|---|---|---|
| C2 행 경합 + C3 강한 불변식(재고 차감) | RTDB(서브트리 트랜잭션), Bigtable(단일 행), DynamoDB 글로벌 MRSC(트랜잭션 없음), DocumentDB Elastic(트랜잭션 없음), PocketBase(단일 writer, 처리량), Supabase를 supabase-js 다중 호출로 쓰는 코드 | DS.transactions, DS.row_contention |
| C2 단일 핫 레코드(카운터·랭킹) | Firestore(문서 갱신률), DynamoDB(파티션 1,000 WCU), Convex(OCC 재실행) | DS.row_contention |
| C5 조인 | Firestore Standard, RTDB, DynamoDB, Bigtable | DS.query_models |
| C7·F3 사용자 생성 데이터 이상 | 기본 꺼짐: Firestore PITR, DynamoDB PITR. 없음: Supabase Free, Atlas Free, Appwrite Free, Pinecone Starter. PITR 없음: Atlas Flex, RTDB | DS.backup |
| F1 짧은 중단 | Supabase 표준 플랜(HA·SLA 없음), PocketBase(단일 서버), DocumentDB 단일 인스턴스 | DS.availability |
| D5 국내·서울 | RTDB, Appwrite, Convex, Pinecone 서울 없음. Atlas Free·Flex는 GCP 서울만 | DS.regions |
| D1 공개 사용자 + 무료 플랜 | Supabase Free(1주 정지), Appwrite Free(7일 정지, 90일 후 삭제), Atlas Free(30일 정지, 100 ops/s), Spanner 무료 체험(120일 뒤 삭제) | DS.cost_floor |
| G3 예산 민감 + 낮은 부하 | Spanner(최소 약 $66/월), Bigtable(약 $475/월), DocumentDB(약 $84/월): 축소 후보 | DS.cost_floor |
| B2 인스턴스 2개 이상 | PocketBase | DS.multi_host_access |
