# 생성 산출물 표 07: 캐시, 큐·스트림·작업, 스케줄러, 실시간 연결, 파일 저장소

- 작성일: 2026-10-01
- 짝 문서: [03-cache-queue-scheduler-realtime-storage.md](03-cache-queue-scheduler-realtime-storage.md)(능력), [README.md](README.md)(능력 키), [../dimensions.md](../dimensions.md)(요구 차원)
- 이 문서의 역할: 판정 결과로 구성 요소가 정해진 뒤 에이전트가 **무엇을 생성하고 무엇으로 검증하는가**를 적는다. 사용자는 생성물을 리뷰할 수 없다. 그래서 각 항목은 "검증 명령으로 확인되는가"를 기준으로 썼다.

## 범위

- 03 파일의 구성 요소 58개 중 **교체·도입 대상이 될 수 있는 51개**를 다룬다.
- 제외한 7개:
  - 교체 전 출발점 4개: 프로세스 메모리, 앱 프로세스 안 작업 큐, 컨테이너 로컬 디스크, 앱 프로세스 안 스케줄러
  - Socket.IO 어댑터 없음: 출발점이다. 도입 대상은 "Socket.IO Redis 어댑터"다.
  - Vercel KV: 2024-12에 종료됐다(03 파일). 도입 대상은 Upstash Redis다.
  - 블록 볼륨 다중 연결 제약(EBS·PD·RWO): 도입 대상이 아니라 B2 처방을 막는 제약이다.

## 출처 규칙과 확인 방법

- 모든 확인일은 **2026-10-01**이다.
- **Terraform 리소스 이름과 인자 이름**은 Terraform Registry에서 확인했다.
  - 리소스 목록: Registry API `https://registry.terraform.io/v1/providers/<namespace>/<name>`(최신 버전의 문서 목록)
  - 리소스 문서 본문: Registry API `https://registry.terraform.io/v2/provider-docs/<id>`
  - 두 API 모두 Registry 문서 페이지(`https://registry.terraform.io/providers/<ns>/<name>/latest/docs/resources/<slug>`)와 같은 원문을 돌려준다. 출처 칸에는 이 문서 페이지 URL을 쓴다.
  - 확인한 provider 버전: hashicorp/aws 6.67.0, hashicorp/google 8.5.0, hashicorp/google-beta 8.5.0, cloudflare/cloudflare 5.26.0, vercel/vercel 5.18.0, supabase/supabase 1.11.0, upstash/upstash 2.1.0(2025-08-27 게시), confluentinc/confluent 2.88.0, hashicorp/kubernetes 3.2.1, integrations/github 6.13.0, ably/ably 1.1.0
  - **provider가 없다는 판정**은 Registry API에서 `pusher/pusher`, `inngest/inngest`, `triggerdotdev/trigger`, `triggerdotdev/triggerdev`가 404를 돌려준 것에 근거한다. 다른 네임스페이스의 커뮤니티 provider가 있는지는 확인하지 않았다(`미확인`).
- **Checkov 규칙 ID**는 Checkov 저장소의 공식 정책 색인 `https://raw.githubusercontent.com/bridgecrewio/checkov/main/docs/5.Policy%20Index/terraform.md`에서 리소스 타입별로 뽑았다. 색인에 있는 ID만 적었다. ⚠️출처확인필요
  - 색인에는 거의 모든 리소스에 `CKV2_AWS_37`(CodeCommit 승인 규칙)과 `CKV2_AWS_75`(CORS)가 붙어 있다. 색인을 만드는 방식 때문에 생긴 잡음으로 보여서 적지 않았다.
  - Cloudflare, Vercel, Supabase, Upstash 리소스에 대한 Checkov 규칙은 색인에 **0건**이다.
- 앱 쪽 계약과 로컬 개발 문서는 WebFetch로 연 페이지만 출처로 썼다. 연 페이지에 그 내용이 없으면 `미확인`으로 적었다.
- 03 파일의 능력 값(기본 퇴출 정책 등)을 인용할 때는 "(03)"으로 표시했다. 그 값의 출처는 03 파일에 있다.

## 목차

- [0. 요약표](#0-요약표)
- [1. 공통 산출물 패턴](#1-공통-산출물-패턴)
- [파트 2. 캐시·키-값](#파트-2-캐시키-값): Redis/Valkey 자체 운영 · ElastiCache 노드 기반 · ElastiCache Serverless · MemoryDB · Memorystore Redis Basic · Memorystore Redis Standard · Memorystore Valkey · Memorystore Redis Cluster · Upstash Redis · Vercel Edge Config · Cloudflare Workers KV
- [파트 3. 큐·스트림·작업](#파트-3-큐스트림작업): SQS 표준 · SQS FIFO · SNS · EventBridge · Pub/Sub · Cloud Tasks · MSK · Confluent Cloud · Redis Streams · BullMQ · Celery · Sidekiq · Postgres 큐 · Inngest · Trigger.dev · QStash · Vercel Queues
- [파트 4. 스케줄러](#파트-4-스케줄러): Kubernetes CronJob · Cloud Scheduler · EventBridge Scheduler · Vercel Cron · Supabase Cron · Cloudflare Cron Triggers · GitHub Actions schedule
- [파트 5. 실시간 연결](#파트-5-실시간-연결): Socket.IO Redis 어댑터 · Supabase Realtime · Firebase RTDB · Pusher · Ably · API Gateway WebSocket · AppSync · Durable Objects
- [파트 6. 파일 저장소](#파트-6-파일-저장소): S3 · GCS · R2 · Supabase Storage · Vercel Blob · Firebase Storage · EFS · Filestore
- [7. 생성 자동화에서 걸리는 발견](#7-생성-자동화에서-걸리는-발견)

---

# 0. 요약표

열의 뜻은 다음과 같다.
- **Terraform**: 가능 = 공식·제공사 provider에 필요한 리소스가 있음 / 일부 = 핵심 설정 일부가 Terraform 밖에 있음 / 불가 = provider 없음 또는 해당 리소스 없음 / 해당 없음 = 라이브러리라서 하부 저장소를 따름
- **핵심 속성 수**: 각 절의 "요구 수준에 따라 바뀌는 핵심 속성" 항목 수
- **자동화 불가 단계**: Terraform이나 CLI로 끝낼 수 없어서 대시보드 수동 작업이 필요한 단계가 있는가

| # | 구성 요소 | Terraform | 핵심 속성 수 | 자동화 불가 단계 | Checkov 규칙 |
|---|---|---|---|---|---|
| 1 | Redis/Valkey 자체 운영 | 일부(VM만, Redis 설정은 파일) | 5 | 없음 | 없음 |
| 2 | ElastiCache 노드 기반 | 가능 | 8 | 없음 | 있음 |
| 3 | ElastiCache Serverless | 가능 | 5 | 없음 | 없음 |
| 4 | MemoryDB | 가능 | 6 | 없음 | 있음 |
| 5 | Memorystore Redis Basic | 가능 | 6 | 없음 | 있음 |
| 6 | Memorystore Redis Standard | 가능 | 7 | 없음 | 있음 |
| 7 | Memorystore Valkey | 가능 | 8 | 없음 | 없음 |
| 8 | Memorystore Redis Cluster | 가능 | 7 | 없음 | 없음 |
| 9 | Upstash Redis | 가능 | 4 | 있음(계정·API 키) | 없음 |
| 10 | Vercel Edge Config | 가능 | 3 | 있음(API 토큰) | 없음 |
| 11 | Cloudflare Workers KV | 가능 | 3 | 있음(API 토큰) | 없음 |
| 12 | SQS 표준 | 가능 | 7 | 없음 | 있음 |
| 13 | SQS FIFO | 가능 | 5 | 없음 | 있음 |
| 14 | SNS | 가능 | 5 | 있음(HTTP(S) 구독 확인) | 있음 |
| 15 | EventBridge | 가능 | 4 | 없음 | 없음 |
| 16 | Pub/Sub | 가능 | 8 | 없음 | 있음 |
| 17 | Cloud Tasks | 가능 | 6 | 없음 | 없음 |
| 18 | Kafka — MSK | 가능 | 6 | 없음 | 있음 |
| 19 | Kafka — Confluent Cloud | 가능 | 5 | 있음(계정·Cloud API 키) | 없음 |
| 20 | Redis Streams | 해당 없음(Redis를 따름) | 3 | 없음 | 없음 |
| 21 | BullMQ | 해당 없음(Redis를 따름) | 5 | 없음 | 없음(맞춤 규칙 필요) |
| 22 | Celery | 해당 없음(브로커를 따름) | 6 | 없음 | 없음 |
| 23 | Sidekiq | 해당 없음(Redis를 따름) | 4 | 없음 | 없음 |
| 24 | Postgres 큐(SKIP LOCKED, pg-boss) | 해당 없음(DB를 따름) | 3 | 없음 | 없음 |
| 25 | Inngest | **불가** | 3 | 있음(계정·키·앱 동기화) | 없음 |
| 26 | Trigger.dev | **불가** | 3 | 있음(계정·토큰·환경변수) | 없음 |
| 27 | Upstash QStash | 가능 | 4 | 있음(계정·API 키) | 없음 |
| 28 | Vercel Queues(베타) | **불가**(vercel.json) | 3 | 없음(배포로 반영) | 없음 |
| 29 | Kubernetes CronJob | 가능 | 7 | 없음 | 있음 |
| 30 | Cloud Scheduler | 가능 | 6 | 없음 | 없음 |
| 31 | EventBridge Scheduler | 가능 | 7 | 없음 | 있음 |
| 32 | Vercel Cron | 일부(켜기·끄기만, 정의는 vercel.json) | 4 | 없음 | 없음 |
| 33 | Supabase Cron(pg_cron) | **불가**(SQL 마이그레이션) | 3 | 없음 | 없음 |
| 34 | Cloudflare Cron Triggers | 가능 | 3 | 있음(API 토큰) | 없음 |
| 35 | GitHub Actions schedule | 일부(파일·시크릿은 가능) | 4 | 있음(PAT·앱 설치) | 없음 |
| 36 | Socket.IO Redis 어댑터 | 해당 없음(Redis + LB 스티키) | 4 | 없음 | 없음 |
| 37 | Supabase Realtime | **불가**(SQL·클라이언트 설정) | 3 | 없음 | 없음 |
| 38 | Firebase RTDB | 일부(인스턴스만, 규칙은 CLI) | 4 | 없음(CLI로 가능) | 없음 |
| 39 | Pusher Channels | **불가** | 3 | 있음(앱 생성·키 발급) | 없음 |
| 40 | Ably | 가능 | 4 | 있음(Control API 토큰) | 없음 |
| 41 | API Gateway WebSocket | 가능 | 6 | 없음 | 있음 |
| 42 | AppSync(Event API / GraphQL) | 가능 | 4 | 없음 | 있음(GraphQL만) |
| 43 | Durable Objects | 일부(`[충돌]`, wrangler 권장) | 3 | 없음 | 없음 |
| 44 | Amazon S3 | 가능 | 8 | 없음 | 있음 |
| 45 | GCS | 가능 | 7 | 없음 | 있음 |
| 46 | Cloudflare R2 | 일부(S3 API 토큰 발급 미확인) | 5 | 있음(API 토큰, 미확인) | 없음 |
| 47 | Supabase Storage | **불가**(버킷·RLS는 SQL) | 4 | 없음 | 없음 |
| 48 | Vercel Blob | 가능 | 4 | 없음 | 없음 |
| 49 | Firebase Storage | 가능 | 4 | 있음(Blaze 결제, 미확인) | 있음(하부 GCS) |
| 50 | Amazon EFS | 가능 | 7 | 없음 | 있음 |
| 51 | Google Filestore | 가능 | 4 | 없음 | 없음 |

- 합계 51개. Terraform 가능 32, 일부 6, 불가 7, 해당 없음 6.
- 서드파티 SaaS(Upstash, Vercel, Cloudflare, Confluent, Ably, Inngest, Trigger.dev, Pusher, GitHub)는 **provider 인증용 계정·토큰을 사람이 한 번 만들어 넣어야** 한다. Terraform이 있어도 이 첫 단계는 자동화할 수 없다.

---

# 1. 공통 산출물 패턴

구성 요소마다 반복되는 것은 여기서 한 번만 적는다.

### 1.1 검증 단계(모든 구성 요소)

| 단계 | 명령 | 확인 포인트 |
|---|---|---|
| 정적 | `terraform fmt -check`, `terraform validate` | 필수 인자 누락, 상충 인자(예: `auth_token`이 `transit_encryption_enabled` 없이 쓰임) |
| 계획 | `terraform plan -out=tfplan` 후 `terraform show -json tfplan` | 리소스 개수, `replace`(재생성) 여부, 아래 절의 "핵심 속성" 값이 계획에 그대로 들어갔는가를 JSON 경로로 단언 |
| 정책 | `checkov -d . --framework terraform` 또는 `checkov -f tfplan.json` | 아래 절에 적은 규칙 ID. Cloudflare·Vercel·Supabase·Upstash는 규칙이 없으므로 **맞춤 검사**(plan JSON 단언)가 유일한 장치다 |
| 배포 후 | 구성 요소별 왕복 시험 | 아래 절의 "배포 후" 항목 |

### 1.2 Redis 계열을 큐로 쓸 때의 공통 계약

03 §7-1의 결론대로 BullMQ·Sidekiq은 `maxmemory-policy noeviction`이 필요하다. Celery는 `noeviction` 또는 `allkeys-lru`가 필요하다. 그래서 큐용 Redis를 생성할 때는 다음을 **plan JSON 단언**으로 검사한다. Checkov에는 이것을 검사하는 규칙이 없다.

- ElastiCache 노드 기반: `aws_elasticache_parameter_group.parameter[name="maxmemory-policy"].value == "noeviction"`이고, 복제 그룹의 `parameter_group_name`이 그 그룹을 가리킴
- Memorystore Redis: `google_redis_instance.redis_configs["maxmemory-policy"]`
- Memorystore Valkey: `google_memorystore_instance.engine_configs["maxmemory-policy"]`
- Memorystore Redis Cluster: `google_redis_cluster.redis_configs["maxmemory-policy"]`
- ElastiCache Serverless: 퇴출 정책을 바꿀 인자가 없다(03: `volatile-lru` 고정). **큐 용도이면 생성을 거부한다.**
- Upstash: `upstash_redis_database.eviction == false`

배포 후에는 `redis-cli -u "$REDIS_URL" CONFIG GET maxmemory-policy`로 확인한다. 관리형 서비스는 `CONFIG` 명령을 막는 경우가 있다(서비스별 허용 여부 `미확인`). 막혀 있으면 plan 단언만으로 확인한다.

### 1.3 docker-compose 공통 이미지

| 용도 | 이미지 | 비고 |
|---|---|---|
| Redis | `redis`(Docker 공식 이미지) | Redis 8.0부터 RSALv2·SSPLv1·AGPLv3 중 선택하는 3중 라이선스. 7.2.4 이하는 BSD. 영속성 예시: `redis-server --save 60 1`. 이미지 문서에 헬스체크 안내는 없다 |
| Valkey | `valkey/valkey`(Valkey 커뮤니티 공식, 태그 `9`, `9.1-alpine` 등) | `valkey-server --save 60 1` 또는 `VALKEY_EXTRA_FLAGS`. 데이터는 `/data`. 헬스체크 안내는 없다 |
| 헬스체크(생성 규칙) | `test: ["CMD", "redis-cli", "ping"]` / `["CMD", "valkey-cli", "ping"]` | 이미지 문서에 없는 **생성 규칙**이다. `-cli` 바이너리가 이미지에 들어 있는지는 `미확인`이므로 생성 후 `docker compose up --wait`로 확인한다 |
| AWS 에뮬레이션 | `localstack/localstack` | **2026.03.0부터 커뮤니티 이미지와 Pro 이미지를 하나로 합쳤고, 시작할 때 `LOCALSTACK_AUTH_TOKEN`이 필요하다.** 무료 Hobby 플랜은 비상업 용도만 허용한다. 계정 없이 시작하던 유예 변수 `LOCALSTACK_ACKNOWLEDGE_ACCOUNT_REQUIREMENT=1`은 2026-04-06까지만 통했다 |
| S3 호환 | MinIO | **저장소가 "더 이상 유지보수하지 않음"으로 보관됐다.** 커뮤니티판은 소스로만 배포하고 바이너리도 내지 않는다. 기존 바이너리는 업데이트가 없다. 생성물의 기본값으로 쓰지 않는다 |

출처(2026-10-01): https://hub.docker.com/_/redis · https://hub.docker.com/r/valkey/valkey · https://blog.localstack.cloud/localstack-for-aws-release-2026-03-0/ · https://docs.localstack.cloud/getting-started/auth-token/ · https://github.com/minio/minio ⚠️출처확인필요

---

# 파트 2. 캐시·키-값

## Redis / Valkey — 자체 운영 (VM·컨테이너, OSS)

- **Terraform:** Redis 전용 리소스는 없다. VM(`aws_instance`, `google_compute_instance`)이나 컨테이너 서비스로 띄우고, `redis.conf`나 명령행 인자는 Terraform 밖의 **생성 파일**로 둔다. VM·컨테이너 리소스의 상세는 05 파일(컴퓨트)의 범위다.
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `maxmemory`와 `maxmemory-policy`: 03에 따르면 기본값은 `maxmemory 0`, `noeviction`이다. 캐시 용도이면 `allkeys-lru`와 메모리 상한을 둔다. 큐 용도이면 `noeviction`을 유지한다(B1·B4, QU.delivery).
  2. 영속성: 기본은 RDB다(03, 분 단위 손실). C7이 "사용자 생성" 이상이거나 큐 용도이면 `appendonly yes`, `appendfsync everysec`를 쓴다. BullMQ 문서도 AOF 매초를 권장한다(CA.persistence, F3).
  3. `requirepass` 또는 ACL 사용자(F5).
  4. TLS: OSS Redis는 빌드 옵션과 인증서가 필요해서 생성 난도가 높다(`미확인`). 같은 VPC의 사설망으로만 노출하는 것을 기본으로 한다.
  5. 볼륨: `/data`를 영속 볼륨에 둔다. 컨테이너 로컬 디스크에 두면 B2 문제가 다시 생긴다.
- **앱 쪽 계약:** `REDIS_URL=redis://:<password>@<host>:6379/0`. 클라이언트 설정은 [BullMQ](#bullmq-node-redis-기반), [connect-redis](#socketio--redis-어댑터--redis-streams-어댑터) 절을 따른다.
- **로컬 개발 대응:** 위 1.3의 `redis`나 `valkey/valkey` 이미지. 운영과 같은 `--appendonly yes --maxmemory-policy noeviction` 인자를 compose에도 넣어서 차이를 줄인다.
- **검증 명령:**
  - 정적: compose 파일에 `docker compose config`
  - 배포 후: `redis-cli -u $REDIS_URL CONFIG GET maxmemory-policy`, `CONFIG GET appendonly`. 재시작한 뒤 키가 남아 있는지 확인한다(SET → 재시작 → GET).
- **출처:** https://hub.docker.com/_/redis · https://hub.docker.com/r/valkey/valkey · https://docs.bullmq.io/guide/going-to-production (2026-10-01) ⚠️출처확인필요

## Redis / Valkey — Amazon ElastiCache, 노드 기반

- **Terraform:** provider `hashicorp/aws`
  - `aws_elasticache_replication_group`: 단일 노드라도 이것을 쓴다. 복제·페일오버·TLS 인자가 여기에만 있다.
  - `aws_elasticache_parameter_group`, `aws_elasticache_subnet_group`
  - RBAC를 쓸 때: `aws_elasticache_user`, `aws_elasticache_user_group`
  - 보안 그룹: `aws_security_group`
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `aws_elasticache_parameter_group`: `family`(엔진 버전에 맞는 값, 값 목록 `미확인`)와 `parameter { name = "maxmemory-policy" value = "noeviction" }`. 03에 따르면 기본값은 `volatile-lru`라서 큐 용도이면 필수다. 세션 캐시 용도이면 기본값을 두고 세션 키에 TTL을 준다(B1).
  2. `engine`(`valkey`/`redis`)과 `engine_version`. 03 §7-6에 따라 비용 차이가 크다(G3).
  3. `transit_encryption_enabled = true`와 `auth_token`. 레지스트리 문서에 따르면 `auth_token`은 `transit_encryption_enabled = true`일 때만 쓸 수 있다. 상태 파일에 값을 남기지 않으려면 `auth_token_wo` + `auth_token_wo_version`을 쓴다. 기존 그룹에 토큰을 추가할 때 `auth_token_update_strategy`가 기본 `ROTATE`이면 비밀번호 없는 접속도 계속 허용된다. 즉시 강제하려면 `SET`을 쓴다(F5).
  4. `at_rest_encryption_enabled`: 기본값은 `engine = "redis"`면 `false`, `valkey`면 `true`다.
  5. `automatic_failover_enabled`, `multi_az_enabled`, `num_cache_clusters >= 2`. 레지스트리 문서에 따르면 `multi_az_enabled`에는 자동 페일오버가 필요하고, 둘 중 하나라도 켜면 노드가 2개 이상이어야 한다(F1, CA.availability).
  6. `snapshot_retention_limit`(0이면 백업 꺼짐)과 `snapshot_window`(C7, F3)
  7. `durability`(`default`/`async`/`sync`/`disabled`): **cluster mode와 Valkey 9.0 이상이 필요하다.** 큐·세션의 무손실 요구(F3 = 0)를 노드 기반 ElastiCache로 맞출 수 있는 유일한 인자다. `sync`이면 Multi-AZ 트랜잭션 로그에 기록된 뒤에 응답한다.
  8. `cluster_mode`와 `num_node_groups`: 클러스터 모드를 켜면 BullMQ는 해시 태그 prefix가 필요하고 Sidekiq은 권장되지 않는다(아래 절).
- **앱 쪽 계약:**
  - TLS를 켜면 `REDIS_URL=rediss://:<auth_token>@<primary_endpoint_address>:6379`이다. `primary_endpoint_address`는 Terraform 출력이다(클러스터 모드면 `configuration_endpoint_address`).
  - ioredis는 `tls: {}`, node-redis는 `rediss://` URL을 쓴다.
  - Celery는 `rediss://...?ssl_cert_reqs=required`, 또는 `broker_use_ssl = {'ssl_cert_reqs': ssl.CERT_REQUIRED}`를 쓴다.
- **로컬 개발 대응:** `valkey/valkey` 또는 `redis` 이미지. 로컬은 TLS 없이 `redis://`를 쓴다. 운영만 `rediss://`이므로 URL은 환경변수로 받아야 한다. 코드에 하드코딩된 `redis://localhost`는 생성 시 바꾼다.
- **검증 명령:**
  - plan 단언: `parameter_group_name`이 noeviction 그룹을 가리킴(큐 용도), `transit_encryption_enabled == true`, F1이 "짧아야 함"이면 `automatic_failover_enabled`와 `multi_az_enabled`가 모두 `true`
  - Checkov: `CKV_AWS_29`(저장 암호화), `CKV_AWS_30`(전송 암호화), `CKV_AWS_31`(전송 암호화와 auth token), `CKV_AWS_191`(KMS CMK), `CKV2_AWS_50`(Multi-AZ 자동 페일오버). `aws_elasticache_cluster`를 쓰면 `CKV_AWS_134`(자동 백업), `CKV_AWS_322`, `CKV_AWS_323`
  - 배포 후: 같은 VPC의 앱 태스크에서 `redis-cli --tls -h <endpoint> -a <token> PING`. 앱 인스턴스 2개에서 세션 쓰기와 읽기를 교차로 확인한다(B1).
- **출처:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/elasticache_replication_group · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/elasticache_parameter_group · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/elasticache_subnet_group · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/elasticache_user · https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/WhatIs.corecomponents.html · https://docs.celeryq.dev/en/stable/userguide/configuration.html (2026-10-01) ⚠️출처확인필요

## Redis / Valkey — Amazon ElastiCache Serverless

- **Terraform:** provider `hashicorp/aws`. `aws_elasticache_serverless_cache`, 선택으로 `aws_elasticache_user_group`, 그리고 보안 그룹.
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `engine`(`valkey`/`redis`/`memcached`)과 `major_engine_version`. 03에 따르면 Valkey는 약 $7.4/월, Redis OSS는 약 $110/월부터다(G3).
  2. `cache_usage_limits`(`data_storage` 최대값, `ecpu_per_second`): 비용 상한이다(G3).
  3. `snapshot_retention_limit`, `daily_snapshot_time`(C7)
  4. `security_group_ids`, `subnet_ids`(F5)
  5. `user_group_id`: 접근 제어
  - **퇴출 정책을 바꾸는 인자가 없다.** 03에 따르면 `volatile-lru`로 고정이다. 그래서 큐(BullMQ·Sidekiq) 용도이면 이 구성 요소를 고르지 않는다(1.2).
- **앱 쪽 계약:**
  - AWS 문서: 서버리스는 클러스터 모드로 동작하고, **TLS를 지원하는 클라이언트만** 접속할 수 있으며, 항상 전송·저장 암호화를 한다. 그래서 URL은 `rediss://<endpoint>:6379`다.
  - 클러스터 모드이므로 여러 키를 다루는 명령에는 해시 태그가 필요하다. BullMQ는 `prefix: '{app}'`처럼 쓴다.
  - 세션 키에는 TTL을 준다(connect-redis 기본 `ttl` 86400초).
- **로컬 개발 대응:** `valkey/valkey`. 로컬은 단일 노드라서 해시 태그 오류(CROSSSLOT)가 재현되지 않는다. 클러스터 모드 차이는 로컬에서 잡히지 않는다.
- **검증 명령:**
  - plan: `engine`, `cache_usage_limits`가 있는지
  - Checkov: 색인에 서버리스 전용 규칙이 없다.
  - 배포 후: TLS 클라이언트로 `PING`. 여러 키 명령(BullMQ 작업 추가 → 처리)이 CROSSSLOT 오류 없이 왕복하는지 확인한다.
- **출처:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/elasticache_serverless_cache · https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/WhatIs.corecomponents.html · https://docs.bullmq.io/bull/patterns/redis-cluster · https://github.com/tj/connect-redis (2026-10-01) ⚠️출처확인필요

## Redis / Valkey 호환 — Amazon MemoryDB

- **Terraform:** provider `hashicorp/aws`. `aws_memorydb_cluster`, `aws_memorydb_acl`, `aws_memorydb_user`, `aws_memorydb_parameter_group`, `aws_memorydb_subnet_group`
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `engine`(`redis`/`valkey`)과 `node_type`(G3)
  2. `tls_enabled`: 기본값 `true`, 바꾸면 재생성된다. `false`이면 `acl_name`이 `open-access`여야 한다(F5).
  3. `acl_name`(필수)과 `aws_memorydb_user`(`access_string`, 비밀번호)
  4. `num_replicas_per_shard`(기본 1, 최대 5)와 `num_shards`(F1, D2)
  5. `snapshot_retention_limit`: **기본값 0이라 자동 백업이 꺼져 있다**(C7)
  6. `parameter_group_name`: 03에 따르면 기본이 `noeviction`이라 큐 용도에 바로 맞는다.
- **앱 쪽 계약:** `REDIS_URL=rediss://<user>:<password>@<cluster_endpoint>:6379`. 클러스터 모드 클라이언트가 필요한지는 `미확인`(MemoryDB 문서를 열지 않음). 샤드가 1개여도 BullMQ prefix에 해시 태그를 주는 것을 생성 기본값으로 한다.
- **로컬 개발 대응:** `valkey/valkey`(MemoryDB의 트랜잭션 로그 내구성은 재현되지 않는다).
- **검증 명령:**
  - Checkov: `CKV_AWS_201`(KMS CMK 저장 암호화), `CKV_AWS_202`(전송 암호화), `CKV_AWS_278`(스냅샷 CMK)
  - plan 단언: C7이 "사용자 생성" 이상이면 `snapshot_retention_limit > 0`
  - 배포 후: 큐 작업 왕복. 노드를 장애 조치한 뒤 작업이 유실되지 않는지 확인하는 것은 운영 시험이다(선택).
- **출처:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/memorydb_cluster · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/memorydb_acl · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/memorydb_user · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/memorydb_parameter_group (2026-10-01)

## Redis — Google Memorystore for Redis, Basic 티어

- **Terraform:** provider `hashicorp/google`
  - `google_redis_instance`(`tier = "BASIC"`)
  - `connect_mode = "PRIVATE_SERVICE_ACCESS"`이면 `google_service_networking_connection`
  - Cloud Run에서 접속하려면 VPC 연결 수단이 필요하다(`google_vpc_access_connector` 또는 Direct VPC egress, 05 파일 범위).
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `memory_size_gb`(G3)
  2. `redis_configs = { "maxmemory-policy" = "noeviction" }`: 큐 용도. 03에 따르면 기본값은 `volatile-lru`다.
  3. `auth_enabled`: 기본값 `false`. 켜면 출력 `auth_string`을 앱 비밀로 넘긴다(F5).
  4. `transit_encryption_mode`: 기본값 `DISABLED`, 켜려면 `SERVER_AUTHENTICATION`(F5)
  5. `persistence_config { persistence_mode = "RDB", rdb_snapshot_period = ... }`: 03에 따르면 기본은 영속성 없음이다(C7).
  6. `connect_mode`: 기본 `DIRECT_PEERING`, 또는 `PRIVATE_SERVICE_ACCESS`
  - Basic은 복제가 없다(03). F1이 "짧아야 함"이면 Standard로 올린다.
- **앱 쪽 계약:**
  - TLS를 켜면 서버 인증서를 검증해야 한다. 출력 `server_ca_certs`의 CA를 앱에 넘겨야 한다. 생성물은 CA 파일 경로 환경변수(예: `REDIS_CA_CERT`, 이름은 생성 규칙)와 클라이언트 `tls.ca` 설정을 함께 만든다.
  - URL은 `rediss://:<auth_string>@<host>:<port>`다.
- **로컬 개발 대응:** `redis` 이미지(TLS 없음)
- **검증 명령:**
  - Checkov: `CKV_GCP_95`(AUTH 켬), `CKV_GCP_97`(전송 암호화)
  - plan 단언: `redis_configs["maxmemory-policy"]`
  - 배포 후: 서버리스 컴퓨트(Cloud Run)에서 VPC 경로로 `PING`. VPC 연결이 빠지면 여기서 실패한다.
- **출처:** https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/redis_instance · https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/service_networking_connection · https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/vpc_access_connector (2026-10-01)

## Redis — Google Memorystore for Redis, Standard 티어(HA)

- **Terraform:** Basic과 같은 `google_redis_instance`에 `tier = "STANDARD_HA"`
- **요구 수준에 따라 바뀌는 핵심 속성:** Basic의 6개에 다음을 더한다.
  1. `tier = "STANDARD_HA"`(F1)
  2. `replica_count`와 `read_replicas_mode`: 기본 `READ_REPLICAS_DISABLED`이고 **생성할 때만 지정할 수 있다**(C4). 나중에 읽기 확장이 필요하면 재생성해야 하므로 판정 단계에서 미리 정한다.
  - 같은 인자이므로 표의 핵심 속성 수는 7로 셌다(`memory_size_gb`, `redis_configs`, `auth_enabled`, `transit_encryption_mode`, `persistence_config`, `tier`, `read_replicas_mode`/`replica_count`).
- **앱 쪽 계약:** Basic과 같다. 03에 따르면 비동기 복제라서 페일오버할 때 유실이 있을 수 있다. 큐 작업은 멱등이어야 한다.
- **로컬 개발 대응:** Basic과 같다.
- **검증 명령:** Basic과 같다(`CKV_GCP_95`, `CKV_GCP_97`). plan에서 `read_replicas_mode` 변경이 `replace`로 표시되는지 확인하고, 운영 중 재생성을 막는다.
- **출처:** https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/redis_instance (2026-10-01)

## Valkey — Google Memorystore for Valkey (클러스터 모드 켬/끔)

- **Terraform:** provider `hashicorp/google`(`google-beta`에도 있음)
  - `google_memorystore_instance`
  - `google_network_connectivity_service_connection_policy`: Private Service Connect 연결 정책. 레지스트리 예시가 이것을 `depends_on`으로 둔다.
  - IAM 인증을 쓰면 앱 서비스 계정에 `roles/memorystore.dbConnectionUser`
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `mode`: `CLUSTER` / `CLUSTER_DISABLED`. 클러스터면 BullMQ 해시 태그가 필요하고 Sidekiq은 비권장이다.
  2. `engine_configs = { "maxmemory-policy" = "noeviction" }`: 큐 용도
  3. `persistence_config { mode = "AOF", aof_config { append_fsync = ... } }`: 03에 따르면 RDB나 AOF everysec를 고를 수 있다(C7, F3).
  4. `authorization_mode`: **값은 `AUTH_DISABLED`와 `IAM_AUTH`뿐이다.** 정적 비밀번호를 고를 수 있는 값이 없다(F5).
  5. `transit_encryption_mode`: 레지스트리 예시는 `TRANSIT_ENCRYPTION_DISABLED`를 쓴다. 켜는 값의 이름은 `미확인`이다.
  6. `node_type`(`SHARED_CORE_NANO` 등)과 `shard_count`, `replica_count`(G3, F1)
  7. `zone_distribution_config`: 기본 `MULTI_ZONE`(F1)
  8. `desired_auto_created_endpoints`: 예전 `desired_psc_auto_connections`는 deprecated다.
  - `deletion_protection_enabled`도 있다.
- **앱 쪽 계약:**
  - `IAM_AUTH`이면 **IAM 액세스 토큰을 AUTH 비밀번호로 쓴다.** 토큰은 기본 1시간 후 만료되고 최대 12시간까지 늘릴 수 있다. 이미 인증된 연결은 계속 쓸 수 있지만 **새 연결에는 유효한 토큰이 필요하다.**
  - 그래서 앱 코드에 "토큰을 받아 오고 재연결할 때 갱신하는" 연결 팩토리를 생성해야 한다. 정적 `REDIS_URL`만으로는 안 된다.
  - `AUTH_DISABLED`이면 네트워크 격리(PSC)에만 의존한다.
- **로컬 개발 대응:** `valkey/valkey`. IAM 토큰 경로는 로컬에서 재현되지 않으므로 "토큰 공급자"를 환경변수로 끌 수 있게 생성한다.
- **검증 명령:**
  - Checkov: 이 리소스에 대한 규칙은 색인에 없다. plan 단언으로 `authorization_mode`, `transit_encryption_mode`, `engine_configs`를 검사한다.
  - 배포 후: 새 인스턴스를 띄운 뒤 1시간 넘게 지나서 **새 연결**이 성공하는지 확인한다(토큰 갱신 경로 확인).
- **출처:** https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/memorystore_instance · https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/network_connectivity_service_connection_policy · https://docs.cloud.google.com/memorystore/docs/valkey/about-iam-auth (2026-10-01)

## Redis Cluster — Google Memorystore for Redis Cluster

- **Terraform:** provider `hashicorp/google`. `google_redis_cluster`, `google_network_connectivity_service_connection_policy`. 선택으로 `google_redis_cluster_user_created_connections`, `google_redis_cluster_acl_policy`
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `authorization_mode`: 기본 `AUTH_MODE_DISABLED`, 또는 `AUTH_MODE_IAM_AUTH`(F5)
  2. `transit_encryption_mode`: 기본 `TRANSIT_ENCRYPTION_MODE_DISABLED`(F5)
  3. `redis_configs`: `maxmemory-policy`
  4. `persistence_config`: RDB 또는 AOF(C7)
  5. `psc_configs`: 필수, 현재 1개만 지원
  6. `node_type`, `shard_count`, `replica_count`(G3, F1)
  7. `zone_distribution_config`, `deletion_protection_enabled`
- **앱 쪽 계약:**
  - 클러스터 클라이언트가 필요하다(ioredis `Cluster`, redis-py `RedisCluster`).
  - BullMQ는 해시 태그 prefix가 필요하다.
  - **Sidekiq 문서는 Redis Cluster를 권장하지 않는다.** Sidekiq 앱이면 이 구성 요소를 고르지 않는다.
  - IAM 인증이면 Valkey 절과 같은 토큰 갱신 계약이 필요하다.
- **로컬 개발 대응:** 단일 노드 `redis`. CROSSSLOT 오류는 재현되지 않는다(`미확인`: 로컬 클러스터 이미지).
- **검증 명령:** Checkov 규칙 없음. plan 단언으로 대신한다. 배포 후 여러 키 명령으로 왕복을 확인한다.
- **출처:** https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/redis_cluster · https://docs.bullmq.io/bull/patterns/redis-cluster · https://github.com/sidekiq/sidekiq/wiki/Using-Redis (2026-10-01) ⚠️출처확인필요

## Upstash Redis — 서버리스

- **Terraform:** provider `upstash/upstash`(2.1.0, 마지막 게시 2025-08-27). `upstash_redis_database`
  - **자동화 불가 단계:** provider 인증(계정 이메일과 API 키)은 Upstash 콘솔에서 사람이 발급한다.
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `region`과 `primary_region`, `read_regions`(D5)
     - provider 문서의 `primary_region` 허용 목록은 `us-east-1, us-west-1, us-west-2, eu-central-1, eu-west-1, sa-east-1, ap-southeast-1, ap-southeast-2`다. **03이 말하는 도쿄(ap-northeast-1)가 이 목록에 없다.** 실제로 허용되는지는 `미확인`이므로 `terraform apply` 전에 `plan`과 API 응답으로 확인해야 한다.
  2. `eviction`(bool): 큐 용도이면 `false`. 03에 따르면 꺼져 있으면 가득 찼을 때 쓰기를 거부한다.
  3. `tls`: 새 DB는 기본으로 켜져 있고 끌 수 없다.
  4. `budget`, `prod_pack`(G3, F1)
  - `multizone`은 deprecated다.
- **앱 쪽 계약:**
  - 출력: `endpoint`, `port`, `password`, `rest_token`, `read_only_rest_token`
  - TCP 접속: Upstash 문서에 "토큰이 곧 DB 비밀번호"이고 `redis-cli --tls`로 접속한다고 나온다. 그래서 `rediss://default:<password>@<endpoint>:<port>`다. 사용자 이름 `default`는 `미확인`이다.
  - REST 접속 환경변수 이름 `UPSTASH_REDIS_REST_URL`과 `UPSTASH_REDIS_REST_TOKEN`은 연 페이지에서 확인하지 못했다(`미확인`).
- **로컬 개발 대응:** TCP 클라이언트를 쓰면 `redis` 이미지로 대체한다. REST 클라이언트(`@upstash/redis`)의 로컬 대체재는 `미확인`이다.
- **검증 명령:**
  - Checkov 규칙 없음. plan 단언: `eviction == false`(큐), `region`
  - 배포 후: `redis-cli --tls -a <password> -h <endpoint> -p <port> PING`
- **출처:** https://registry.terraform.io/providers/upstash/upstash/latest/docs/resources/redis_database · https://upstash.com/docs/redis/overall/getstarted (2026-10-01) ⚠️출처확인필요

## Vercel Edge Config (Global Config)

- **Terraform:** provider `vercel/vercel`. `vercel_edge_config`, `vercel_edge_config_item`(`key`, `value` 또는 `value_json`), `vercel_edge_config_token`(출력 `connection_string`, `token`), `vercel_project_environment_variable`
  - **자동화 불가 단계:** provider 인증용 Vercel API 토큰은 사람이 발급한다.
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. 저장하는 항목(`vercel_edge_config_item`): 기능 플래그나 리다이렉트처럼 읽기 위주의 설정만 둔다. 03에 따르면 **세션 저장소로는 쓸 수 없다**(B1). B1 처방으로 이것을 생성하면 판정 오류다.
  2. 토큰 범위: 프로젝트마다 토큰 하나
  3. 환경(`target`: production/preview/development)
- **앱 쪽 계약:** `connection_string`을 `EDGE_CONFIG` 환경변수로 넣는다. 레지스트리 문서: "Edge Config 클라이언트 SDK는 기본으로 `process.env.EDGE_CONFIG`를 찾는다."
- **로컬 개발 대응:** 에뮬레이터 `미확인`. `vercel env pull`로 개발 환경 값을 받아서 실제 Edge Config를 읽는다.
- **검증 명령:** plan 단언(항목 키). 배포 후 앱에서 키를 읽는 엔드포인트를 호출한다. 03에 따르면 값을 바꾼 뒤 전파까지 최대 10초다.
- **출처:** https://registry.terraform.io/providers/vercel/vercel/latest/docs/resources/edge_config · https://registry.terraform.io/providers/vercel/vercel/latest/docs/resources/edge_config_item · https://registry.terraform.io/providers/vercel/vercel/latest/docs/resources/edge_config_token · https://registry.terraform.io/providers/vercel/vercel/latest/docs/resources/project_environment_variable (2026-10-01)

## Cloudflare Workers KV

- **Terraform:** provider `cloudflare/cloudflare`(v5)
  - `cloudflare_workers_kv_namespace`(`title`, `jurisdiction`), `cloudflare_workers_kv`(초기 키)
  - Worker 쪽 바인딩은 `cloudflare_workers_script`(또는 `cloudflare_worker` + `cloudflare_worker_version`)의 `bindings`에 `type = "kv_namespace"`로 넣는다.
  - **자동화 불가 단계:** Cloudflare API 토큰 발급
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. 용도: 03에 따르면 최종 일관성이 60초 이상이고 같은 키 쓰기는 초당 1회라서 읽기 위주만 가능하다. 세션·레이트 리밋·락(B1, B4)에는 쓰지 않는다.
  2. `jurisdiction`: 데이터 위치(F5)
  3. 바인딩 이름: 코드의 `env.<NAME>`과 일치해야 한다.
- **앱 쪽 계약:** Worker 코드에서 `env.<BINDING>.get/put`. 바인딩 이름은 wrangler 설정 파일과 Terraform 바인딩에 같은 값을 쓴다.
- **로컬 개발 대응:** `wrangler dev`가 KV를 로컬에서 흉내 내는지는 연 문서로 확인하지 못했다(`미확인`).
- **검증 명령:** Checkov 규칙 없음. plan에서 바인딩 이름을 단언한다. 배포 후 쓰기 → 60초 뒤 다른 위치에서 읽기를 확인한다.
- **출처:** https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/workers_kv_namespace · https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/workers_kv · https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/workers_script (2026-10-01)

---

# 파트 3. 큐·스트림·작업

## Amazon SQS — 표준 큐

- **Terraform:** provider `hashicorp/aws`
  - `aws_sqs_queue`(본 큐와 DLQ 두 개), `aws_sqs_queue_redrive_policy`, `aws_sqs_queue_redrive_allow_policy`, `aws_sqs_queue_policy`
  - 소비자가 Lambda이면 `aws_lambda_event_source_mapping`
  - 앱 IAM 역할 정책(`sqs:SendMessage`, `ReceiveMessage`, `DeleteMessage`, `ChangeMessageVisibility`)
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `visibility_timeout_seconds`: 0~43200, **기본 30초**. 작업의 최대 처리 시간(A2)보다 길어야 한다. 짧으면 처리 중에 다시 전달돼서 중복 실행된다(QU.retry_dlq).
  2. `message_retention_seconds`: 60~1209600(14일), 기본 345600(4일)(QU.retention, F4: 소비자가 중단돼도 견딜 시간)
  3. `redrive_policy`(JSON `deadLetterTargetArn`, `maxReceiveCount`): DLQ. 레지스트리는 별도 리소스 `aws_sqs_queue_redrive_policy`를 권장한다(QU.retry_dlq).
  4. `receive_wait_time_seconds`: 0~20, 기본 0. 20으로 두면 롱 폴링이 돼서 비용이 줄어든다(G3).
  5. `max_message_size`: 1024~1048576, **Terraform 문서상 기본 262144(256 KiB)**. 03에 따르면 서비스 최대는 1 MiB다. 큰 페이로드는 S3에 두고 키만 보낸다.
  6. `sqs_managed_sse_enabled` 또는 `kms_master_key_id`(F5)
  7. `delay_seconds`: 0~900
- **앱 쪽 계약:**
  - 환경변수 `SQS_QUEUE_URL`(이름은 생성 규칙), `AWS_REGION`
  - 소비자는 처리가 끝난 뒤에 `DeleteMessage`를 호출하고 멱등키로 중복을 막는다(03: 최소 1회).
  - Celery를 SQS 브로커로 쓸 때:
    - `broker_url = 'sqs://'`(자격 증명은 IAM 역할)
    - `broker_transport_options = {'region': 'ap-northeast-2', 'visibility_timeout': ..., 'predefined_queues': {...}}`
    - **Celery의 SQS 기본 리전은 `us-east-1`이다.** 리전을 빠뜨리면 서울 큐를 찾지 못한다.
    - Celery 쪽 `visibility_timeout` 기본은 30분이다. Terraform 큐 속성의 기본(30초)과 다르므로 두 값을 같게 생성한다.
    - Terraform이 만든 큐를 쓰려면 `predefined_queues`에 넣는다.
    - SQS 브로커는 원격 제어와 이벤트(모니터링)를 지원하지 않는다.
- **로컬 개발 대응:** `localstack/localstack`. **2026.03부터 `LOCALSTACK_AUTH_TOKEN`이 필요하다**(1.3). 토큰이 없는 대체재(ElasticMQ 등)는 `미확인`이다.
- **검증 명령:**
  - plan 단언: `visibility_timeout_seconds >= 작업 최대 시간`, DLQ 연결 존재, `maxReceiveCount`
  - Checkov: `CKV_AWS_27`(암호화), `CKV2_AWS_73`(CMK, 과잉일 수 있음), `CKV_AWS_168`·`CKV_AWS_72`·`CKV_AWS_387`(큐 정책이 공개·와일드카드가 아님)
  - 배포 후: 메시지 왕복(send → receive → delete). 일부러 실패시킨 메시지가 `maxReceiveCount` 후 DLQ에 도착하는지 확인한다.
- **출처:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sqs_queue · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sqs_queue_redrive_policy · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sqs_queue_policy · https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/sqs.html (2026-10-01) ⚠️출처확인필요

## Amazon SQS — FIFO 큐

- **Terraform:** 표준 큐와 같은 리소스에 `fifo_queue = true`
- **요구 수준에 따라 바뀌는 핵심 속성:** 표준 큐의 속성에 다음을 더한다.
  1. `fifo_queue = true`, 그리고 `name`이 `.fifo`로 끝나야 한다(레지스트리 문서)
  2. `content_based_deduplication`: 본문 해시로 5분 중복 제거(QU.dedup). 끄면 앱이 `MessageDeduplicationId`를 보내야 한다.
  3. `deduplication_scope`: `queue`(기본) / `messageGroup`
  4. `fifo_throughput_limit`: `perQueue`(기본) / `perMessageGroupId`(QU.throughput)
  5. DLQ: FIFO 큐의 DLQ도 FIFO여야 하는지는 레지스트리 문서에서 확인하지 못했다(`미확인`). 같은 FIFO로 생성하는 것을 기본으로 한다.
- **앱 쪽 계약:** 보낼 때 `MessageGroupId`가 필수다(순서 단위, C2: 같은 주문·계정 ID를 그룹으로). 03에 따르면 "정확히 1회"는 조건부이므로 소비자 멱등성은 그대로 필요하다.
- **로컬 개발 대응:** 표준 큐와 같다.
- **검증 명령:** 표준 큐 규칙과 같다. 배포 후 같은 `MessageDeduplicationId`로 두 번 보냈을 때 한 번만 수신되는지 확인한다.
- **출처:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sqs_queue (2026-10-01)

## Amazon SNS — 표준 / FIFO 토픽

- **Terraform:** provider `hashicorp/aws`. `aws_sns_topic`, `aws_sns_topic_subscription`, `aws_sns_topic_policy`, 구독 대상 큐의 `aws_sqs_queue_policy`(SNS가 SQS에 보낼 수 있도록)
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `fifo_topic`, `content_based_deduplication`: FIFO 토픽은 이메일·SMS·HTTP(S) 같은 고객 관리 엔드포인트에 전달할 수 없다(QU.ordering).
  2. `kms_master_key_id`(F5)
  3. 구독 `protocol`: `sqs`/`lambda`/`firehose`/`sms`/`application`. **`email`, `email-json`, `http`, `https`는 Terraform이 "부분 지원"한다.**
  4. 구독 `redrive_policy`: 구독별 DLQ(QU.retry_dlq). 03에 따르면 재시도 후 버린다.
  5. `raw_message_delivery`: 기본 `false`. 끄면 소비자가 SNS 봉투(JSON)를 풀어야 한다.
  - `archive_policy`: FIFO 토픽 아카이브
- **앱 쪽 계약:** 발행자는 `SNS_TOPIC_ARN`(이름은 생성 규칙)을 쓴다. SQS 소비자는 `raw_message_delivery` 값에 맞춰 파싱한다. HTTP(S) 구독을 받는 엔드포인트는 구독 확인 메시지를 처리해야 한다.
- **자동화 불가 단계:** HTTP(S)·이메일 구독은 상대가 확인해야 활성화된다. Terraform만으로 끝나지 않는다.
- **로컬 개발 대응:** localstack(토큰 필요)
- **검증 명령:**
  - Checkov: `CKV_AWS_26`(토픽 암호화), `CKV_AWS_169`(토픽 정책 비공개), `CKV_AWS_385`(교차 계정 금지)
  - 배포 후: 발행 → 구독 SQS에서 수신
- **출처:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic_subscription · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic_policy (2026-10-01)

## Amazon EventBridge — 이벤트 버스

- **Terraform:** provider `hashicorp/aws`
  - `aws_cloudwatch_event_bus`, `aws_cloudwatch_event_rule`, `aws_cloudwatch_event_target`
  - 선택: `aws_cloudwatch_event_archive`, `aws_cloudwatch_event_bus_policy`
  - HTTP 대상: `aws_cloudwatch_event_connection` + `aws_cloudwatch_event_api_destination`
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. 대상의 `retry_policy`(`maximum_event_age_in_seconds`, `maximum_retry_attempts`)(QU.retry_dlq)
  2. 대상의 `dead_letter_config`(SQS ARN): 03에 따르면 재시도한 뒤 버리므로 C7이 높으면 필수다.
  3. `aws_cloudwatch_event_archive`: 재생(03: 1~365일)
  4. HTTP 대상이면 `aws_cloudwatch_event_connection.authorization_type`(`API_KEY`/`BASIC`/`OAUTH_CLIENT_CREDENTIALS`)과 `aws_cloudwatch_event_api_destination.invocation_rate_limit_per_second`(기본 300). 앱 엔드포인트의 E3·D2에 맞춘다.
- **앱 쪽 계약:** 발행자는 `PutEvents`(버스 이름 환경변수). HTTP 대상 엔드포인트는 연결의 인증 헤더(API 키)를 검증하고 멱등이어야 한다(최소 1회).
- **로컬 개발 대응:** localstack(토큰 필요)
- **검증 명령:** Checkov 색인에 EventBridge 고유 규칙이 없다(잡음 규칙만). plan 단언으로 대상마다 DLQ가 있는지 검사한다. 배포 후 시험 이벤트를 발행해서 대상이 수신하는지 확인한다.
- **출처:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_bus · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_rule · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_target · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_connection · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_api_destination (2026-10-01)

## Google Cloud Pub/Sub

- **Terraform:** provider `hashicorp/google`
  - `google_pubsub_topic`, `google_pubsub_subscription`, DLQ용 토픽과 구독
  - IAM: `google_pubsub_topic_iam_member`, `google_pubsub_subscription_iam_member`
  - push로 Cloud Run을 부르면 `google_cloud_run_v2_service_iam_member`(`roles/run.invoker`)
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `ack_deadline_seconds`: 처리 시간보다 길게(A2, QU.retry_dlq)
  2. `message_retention_duration`, `retain_acked_messages`(QU.retention)
  3. `enable_message_ordering`: 순서 키(QU.ordering)
  4. `enable_exactly_once_delivery`: 03에 따르면 pull 방식이고 같은 리전일 때만 정확히 1회다(QU.delivery).
  5. `dead_letter_policy { dead_letter_topic, max_delivery_attempts }`: 5~100. 설정하지 않으면 DLQ가 꺼져 있다. DLQ로 전달하려면 Pub/Sub 서비스 에이전트에 게시·구독 권한을 줘야 하는지는 `미확인`(관련 문서를 열지 않음)이다.
  6. `retry_policy { minimum_backoff }`: 0~600초, 기본 10초. 설정하지 않으면 "가능한 한 빨리" 재시도한다.
  7. `push_config { push_endpoint, oidc_token { service_account_email, audience } }`: push 구독의 인증(F5)
  8. 토픽 `kms_key_name`(F5)
- **앱 쪽 계약:**
  - pull 소비자: 처리한 뒤 ack. 멱등키 필요.
  - push 소비자: 엔드포인트가 OIDC 토큰을 검증하고 2xx로 ack한다. Cloud Run 비공개 서비스면 invoker 권한으로 막는다.
  - 환경변수: `PUBSUB_TOPIC`, `PUBSUB_SUBSCRIPTION`(이름은 생성 규칙)
- **로컬 개발 대응:**
  - 에뮬레이터: `gcloud beta emulators pubsub start --project=<id>`, 기본 포트 8085. 앱은 `PUBSUB_EMULATOR_HOST`를 쓴다.
  - **에뮬레이터는 정확히 1회 전달을 지원하지 않고, 데드레터 전달이 동작하지 않으며, IAM과 보존 기간 설정도 없다.** 이 속성들은 로컬에서 검증할 수 없다.
  - 컨테이너 이미지 URI는 연 문서에 없었다(`미확인`).
- **검증 명령:**
  - Checkov: `CKV_GCP_83`(CSEK 암호화, 과잉일 수 있음), `CKV_GCP_99`(토픽 IAM 비공개)
  - plan 단언: 구독마다 `dead_letter_policy`가 있고, push 구독이면 `oidc_token`이 있는지
  - 배포 후: 실제 Pub/Sub에서 발행 → 수신 → 실패 반복 → DLQ 토픽 도착(에뮬레이터로는 확인할 수 없다)
- **출처:** https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/pubsub_topic · https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/pubsub_subscription · https://docs.cloud.google.com/pubsub/docs/emulator (2026-10-01)

## Google Cloud Tasks

- **Terraform:** provider `hashicorp/google`
  - `google_cloud_tasks_queue`, `google_cloud_tasks_queue_iam`
  - 작업을 실행할 서비스 계정 `google_service_account`
  - 그 계정에 대한 `roles/iam.serviceAccountUser`: Cloud Tasks 서비스 에이전트에 부여
  - 대상 Cloud Run의 `roles/run.invoker`
  - 앱 계정에 Enqueuer 역할
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `rate_limits.max_dispatches_per_second`: 외부 한도(E3)와 다운스트림 보호
  2. `rate_limits.max_concurrent_dispatches`: 동시 처리 상한(D2, DS.connections 보호)
  3. `retry_config.max_attempts`(-1 이상), `max_retry_duration`, 백오프(QU.retry_dlq). 03에 따르면 DLQ가 따로 없다.
  4. `http_target.oidc_token`(큐 단위). 큐 수준에서 쓰려면 서비스 계정 이메일과 audience를 **둘 다** 지정해야 한다(F5).
  5. 작업 이름 중복 제거: 03에 따르면 24시간(QU.dedup). 앱이 결정적 이름을 주면 지연이 늘 수 있다.
  6. `stackdriver_logging_config`: 관측
- **앱 쪽 계약:**
  - 생산자: `HttpRequest`에 `oidc_token(service_account_email, audience)`를 넣어 작업을 만든다.
  - 소비 엔드포인트: 멱등이어야 하고 성공하면 2xx를 돌려준다. `X-CloudTasks-TaskRetryCount` 같은 헤더로 재시도 횟수를 본다.
  - 환경변수: `TASKS_QUEUE`, `TASKS_LOCATION`, `TASKS_SA_EMAIL`, `TASKS_TARGET_URL`(이름은 생성 규칙)
- **로컬 개발 대응:** 공식 에뮬레이터는 `미확인`이다. 로컬에서는 큐 대신 엔드포인트를 직접 호출하도록 어댑터를 생성한다.
- **검증 명령:** Checkov 규칙 없음. plan 단언으로 IAM 바인딩 3종(enqueuer, serviceAccountUser, run.invoker)이 있는지 검사한다. 이 중 하나가 빠지면 작업이 403으로 끝없이 재시도된다. 배포 후 작업을 만들고 대상 로그에서 수신을 확인한다.
- **출처:** https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_tasks_queue · https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_tasks_queue_iam · https://docs.cloud.google.com/tasks/docs/creating-http-target-tasks (2026-10-01)

## Kafka — Amazon MSK (Provisioned / Serverless)

- **Terraform:** provider `hashicorp/aws`
  - `aws_msk_cluster` 또는 `aws_msk_serverless_cluster`
  - `aws_msk_configuration`, SCRAM이면 `aws_msk_scram_secret_association`
  - 토픽: `aws_msk_topic`(Registry 목록에 있음, 인자는 `미확인`)
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `kafka_version`, `number_of_broker_nodes`: 클라이언트 서브넷 수의 배수여야 한다(F1).
  2. `encryption_info.encryption_in_transit.client_broker`: `TLS`(기본) / `TLS_PLAINTEXT` / `PLAINTEXT`(F5)
  3. `in_cluster`: 기본 `true`
  4. `client_authentication`: IAM/SCRAM/TLS. `unauthenticated`는 끈다. 서버리스는 `client_authentication`이 **필수**다.
  5. 서버리스 `vpc_config`
  6. 로깅 설정
- **앱 쪽 계약:** 부트스트랩 브로커 주소(Terraform 출력)를 환경변수로 넘긴다. IAM 인증을 쓰면 언어별 MSK IAM 인증 플러그인이 필요하다(라이브러리 이름 `미확인`). 소비자 오프셋 커밋은 처리한 뒤에 한다.
- **로컬 개발 대응:** Kafka 공식 이미지 이름은 `미확인`이다. IAM 인증은 로컬에서 재현되지 않는다.
- **검증 명령:**
  - Checkov: `CKV_AWS_80`(로깅), `CKV_AWS_81`(저장·전송 암호화), `CKV_AWS_291`(노드 비공개)
  - 배포 후: 같은 VPC에서 생산·소비 왕복
- **출처:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/msk_cluster · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/msk_serverless_cluster (2026-10-01)

## Kafka — Confluent Cloud

- **Terraform:** provider `confluentinc/confluent`
  - `confluent_environment`, `confluent_kafka_cluster`, `confluent_kafka_topic`
  - `confluent_service_account`, `confluent_api_key`, `confluent_role_binding`, `confluent_kafka_acl`
  - **자동화 불가 단계:** Confluent Cloud 계정과 provider용 Cloud API 키는 사람이 만든다.
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `availability`: `SINGLE_ZONE`/`MULTI_ZONE`/`LOW`/`HIGH`(F1)
  2. `cloud`(`AWS`/`AZURE`/`GCP`)와 `region`: **서울 리전이 제공되는지는 `미확인`**(03도 미확인)(D5)
  3. 클러스터 유형 블록: `basic`/`standard`/`enterprise`/`dedicated`(G3)
  4. 토픽 `partitions_count`(기본 6)와 `config`(보존 기간 등)(QU.retention, QU.throughput)
  5. 서비스 계정별 API 키와 역할 바인딩(F5)
- **앱 쪽 계약:** 부트스트랩 서버, `confluent_api_key`의 key/secret(SASL)을 앱 비밀로 넘긴다.
- **로컬 개발 대응:** `미확인`
- **검증 명령:** Checkov 규칙 없음. 배포 후 생산·소비 왕복
- **출처:** https://registry.terraform.io/providers/confluentinc/confluent/latest/docs/resources/confluent_kafka_cluster · https://registry.terraform.io/providers/confluentinc/confluent/latest/docs/resources/confluent_kafka_topic · https://registry.terraform.io/providers/confluentinc/confluent/latest/docs/resources/confluent_environment · https://registry.terraform.io/providers/confluentinc/confluent/latest/docs/resources/confluent_api_key · https://registry.terraform.io/providers/confluentinc/confluent/latest/docs/resources/confluent_service_account (2026-10-01) ⚠️출처확인필요

## Redis Streams (Redis/Valkey 위의 스트림)

- **Terraform:** 별도 리소스가 없다. 고른 Redis 구성 요소(파트 2)를 따른다.
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. 하부 Redis의 퇴출 정책: `noeviction`. 스트림 키가 퇴출되면 메시지가 사라진다.
  2. 하부 Redis의 영속성(AOF)과 페일오버 유실(03: 비동기 복제)(C7)
  3. 앱 쪽 `MAXLEN` 또는 `MINID` 트리밍: 메모리 상한(CA.limits)
- **앱 쪽 계약:** `XADD`와 `XREADGROUP`, 처리한 뒤 `XACK`. 멈춘 메시지는 `XAUTOCLAIM`으로 회수한다. 소비자 그룹을 만드는 일(`XGROUP CREATE ... MKSTREAM`)은 기동할 때 멱등하게 한다.
- **로컬 개발 대응:** `redis`/`valkey/valkey`
- **검증 명령:** 1.2의 plan 단언. 배포 후 소비자를 처리 중에 죽인 뒤 다른 소비자가 회수하는지 확인한다.
- **출처:** 연 문서 없음. 하부 Redis 절의 출처를 따른다. 명령 의미는 `미확인`(Redis 문서를 이번에 열지 않음).

## BullMQ (Node, Redis 기반)

- **Terraform:** 해당 없음. 하부 Redis를 따른다. 단 ElastiCache Serverless는 제외한다(퇴출 정책 고정).
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. 하부 Redis `maxmemory-policy noeviction`: BullMQ 문서는 "BullMQ는 Redis가 키를 임의로 퇴출하면 제대로 동작할 수 없다"고 쓴다.
  2. 하부 Redis AOF: 문서는 "1초마다면 대부분 충분하다"고 쓴다(C7).
  3. 클러스터 모드이면 해시 태그 prefix: `new Queue('q', { prefix: '{myprefix}' })`
  4. 하부 Redis TLS·AUTH(F5)
  5. 동시성(`concurrency`)과 워커 프로세스 수(D2, QU.consumer_scaling)
- **앱 쪽 계약:**
  - **Worker용 ioredis 연결은 `maxRetriesPerRequest: null`이어야 한다.** null이 아니면 Worker에 넘길 때 BullMQ가 예외를 던진다.
  - Queue(생산자)는 `enableOfflineQueue: false`로 빨리 실패시킨다. Worker는 켜 둔다.
  - `SIGINT`·`SIGTERM`을 받으면 `worker.close()`를 호출한다(F4, CP.shutdown).
  - `REDIS_URL`은 운영이 `rediss://`, 로컬이 `redis://`다.
- **로컬 개발 대응:** `redis --maxmemory-policy noeviction --appendonly yes`
- **검증 명령:**
  - Checkov 규칙 없음. **1.2의 맞춤 단언이 필수다.**
  - 정적: 생성 코드에서 `new Worker(` 근처의 연결 옵션에 `maxRetriesPerRequest: null`이 있는지 grep이나 AST로 검사한다.
  - 배포 후: 작업 추가 → 완료 이벤트. 처리 중에 Worker를 SIGTERM으로 끄고 재시작한 뒤 작업이 stalled 재처리로 완료되는지 확인한다.
- **출처:** https://docs.bullmq.io/guide/connections · https://docs.bullmq.io/guide/going-to-production · https://docs.bullmq.io/bull/patterns/redis-cluster (2026-10-01) ⚠️출처확인필요

## Celery (Python) — 브로커별: RabbitMQ / Redis / SQS

- **Terraform:** 해당 없음. 브로커를 따른다.
  - Redis: 파트 2
  - SQS: 위 SQS 절
  - RabbitMQ 관리형: `aws_mq_broker`(`engine_type = "RabbitMQ"`, 인증 `simple`만, `ldap`은 RabbitMQ에서 미지원)
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `task_acks_late = True`: 기본은 실행 **직전에** ack한다. 03에 따르면 기본은 최대 1회다(QU.delivery, C7).
  2. `task_reject_on_worker_lost = True`: `acks_late`를 켜도 워커 프로세스가 갑자기 죽으면 ack된다. 이 값을 켜야 다시 큐에 들어간다.
  3. `broker_transport_options['visibility_timeout']`(Redis·SQS): 가장 긴 작업과 ETA/countdown보다 길게. SQS 기본은 30분, AWS 최대는 12시간이다.
  4. Redis 브로커의 퇴출 정책: 03에 따르면 `noeviction` 또는 `allkeys-lru`
  5. TLS: `rediss://...?ssl_cert_reqs=required` 또는 `broker_use_ssl = {'ssl_cert_reqs': ssl.CERT_REQUIRED, ...}`(F5)
  6. SQS 브로커: `broker_transport_options['region']`. **기본 `us-east-1`이다.**
- **앱 쪽 계약:** `CELERY_BROKER_URL`(프레임워크 관례, 이름은 생성 규칙), `broker_connection_retry_on_startup`. beat(스케줄러)는 워커와 분리해서 **한 개만** 실행한다(B3, 03).
- **로컬 개발 대응:** Redis 브로커면 `redis` 이미지. SQS 브로커면 localstack(토큰 필요). RabbitMQ 이미지는 `미확인`이다.
- **검증 명령:**
  - 정적: 생성한 Celery 설정 파일에 `task_acks_late`, `task_reject_on_worker_lost`, `visibility_timeout`, SQS면 `region`이 있는지 단언
  - 배포 후: 작업 실행 중에 워커를 `kill -9`로 죽인 뒤 다른 워커가 다시 실행하는지 확인한다.
- **출처:** https://docs.celeryq.dev/en/stable/userguide/configuration.html · https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/sqs.html · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/mq_broker (2026-10-01) ⚠️출처확인필요

## Sidekiq (Ruby, Redis 기반)

- **Terraform:** 해당 없음. 하부 Redis를 따른다. **클러스터 모드 Redis는 제외한다**(ElastiCache Serverless, Memorystore Redis Cluster, Valkey `mode = CLUSTER`).
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. 하부 Redis `maxmemory-policy noeviction`: Sidekiq 문서 "Redis가 Sidekiq 데이터를 조용히 버리지 않도록"
  2. 클러스터 모드 금지: Sidekiq 문서는 Redis Cluster가 작업 시스템에 필요한 트랜잭션을 보장하지 못한다며 권장하지 않는다. Sentinel이나 페일오버가 있는 관리형 Redis를 권한다.
  3. `network_timeout`, `pool_timeout`: 기본 1초. 클라우드에서는 5초 정도로 늘린다.
  4. 03에 따르면 OSS는 크래시하면 작업이 유실된다. C7이 높으면 Sidekiq Pro(super_fetch)나 다른 큐를 판정에 올린다.
- **앱 쪽 계약:** `REDIS_URL` 환경변수. 다른 이름을 쓰려면 `REDIS_PROVIDER=<변수명>`. `config/initializers/sidekiq.rb`에 server와 client 블록을 둘 다 둔다.
- **로컬 개발 대응:** `redis` 이미지에 `noeviction`
- **검증 명령:** 1.2의 맞춤 단언, 그리고 클러스터 모드 리소스와 Sidekiq를 함께 생성하면 거부한다. 배포 후 작업 왕복
- **출처:** https://github.com/sidekiq/sidekiq/wiki/Using-Redis (2026-10-01) ⚠️출처확인필요

## Postgres 기반 큐 — `FOR UPDATE SKIP LOCKED`, pg-boss(Node)

- **Terraform:** 해당 없음. 기존 Postgres를 쓴다(01 파일). 새 인프라를 만들지 않는다(03: 추가 비용 $0).
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. DB 연결 수 예산: 워커 수 × 풀 크기를 더한다(C8, DS.connections).
  2. Postgres 버전: pg-boss는 **PostgreSQL 13 이상, Node 22.12 이상(또는 Bun)**이 필요하다.
  3. 보존 정책과 아카이브: 큐 테이블이 계속 커진다(C6)
- **앱 쪽 계약:**
  - 업무 트랜잭션 안에서 작업을 넣는다. pg-boss는 기존 트랜잭션 안에서 작업을 만들 수 있고 Drizzle·Knex·Kysely·Prisma 어댑터가 있다.
  - 재시도와 지수 백오프, DLQ와 재전달, cron 스케줄을 지원한다. cron이 여러 인스턴스에서 한 번만 실행되는지는 연 페이지에서 확인하지 못했다(`미확인`).
  - `start()`가 스키마를 자동으로 만드는지는 `미확인`이다. 마이그레이션 CLI가 있다는 것까지는 확인했다.
- **로컬 개발 대응:** Postgres 이미지(01 파일 범위)
- **검증 명령:** 배포 후 작업을 넣고 두 워커가 같은 작업을 동시에 가져가지 않는지 확인한다(동시 소비 시험).
- **출처:** https://github.com/timgit/pg-boss (2026-10-01) ⚠️출처확인필요

## Inngest (서버리스 내구 함수)

- **Terraform:** **불가.** Registry에서 `inngest/inngest` provider는 404다.
  - **자동화 불가 단계:** 계정 생성, 환경별 Event Key·Signing Key 발급, 앱 동기화(serve 엔드포인트 등록)
  - 앱 동기화를 CLI나 API로 할 수 있는지는 `미확인`이다(문서상 "serve handler로 동기화").
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. 환경별 키 분리: 문서상 "환경마다 자체 event key와 signing key"(F5)
  2. 함수 동시성과 재시도 설정: 코드 안에 있다. 03에 따르면 Free는 동시 5개, 기본 재시도 4회다(D2, QU.retry_dlq).
  3. serve 엔드포인트의 플랫폼 실행 시간 한도(A2, CP.request_timeout)
- **앱 쪽 계약:**
  - `INNGEST_EVENT_KEY`: 이벤트 전송
  - `INNGEST_SIGNING_KEY`: Inngest와 주고받는 요청 서명
  - `INNGEST_SIGNING_KEY_FALLBACK`: 키 교체 중에만, SDK 3.18.0 이상
  - `INNGEST_DEV=1`: 로컬 Dev 모드. `INNGEST_BASE_URL`은 보통 설정하지 않는다.
- **로컬 개발 대응:** `npx --ignore-scripts=false inngest-cli@latest dev`(포트 8288), 또는 Docker 이미지 `inngest/inngest`: `docker run -p 8288:8288 -p 8289:8289 inngest/inngest inngest dev -u http://host.docker.internal:3000/api/inngest`
- **검증 명령:** 정적으로 운영 환경변수에 `INNGEST_DEV`가 없는지 검사한다(있으면 서명 검증 동작이 바뀐다). 배포 후 시험 이벤트를 보내고 실행 기록을 확인한다(대시보드 또는 API, API는 `미확인`).
- **출처:** https://www.inngest.com/docs/sdk/environment-variables · https://www.inngest.com/docs/dev-server · https://www.inngest.com/docs/platform/environments (2026-10-01) ⚠️출처확인필요

## Trigger.dev (관리형 작업 실행)

- **Terraform:** **불가.** Registry에서 `triggerdotdev/*` provider는 404다.
  - **자동화 불가 단계:** 계정·프로젝트 생성, Production API 키(`TRIGGER_SECRET_KEY`) 발급, CI용 `TRIGGER_ACCESS_TOKEN` 발급
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. 작업 코드의 재시도·동시성·머신 크기(설정 이름 `미확인`)
  2. 환경변수 동기화 방식: 대시보드 수동 / `syncEnvVars` 확장 / `syncVercelEnvVars` 확장
  3. 배포 경로: CLI(`npx trigger.dev@latest deploy`)
- **앱 쪽 계약:** 백엔드에서 작업을 트리거할 때 `TRIGGER_SECRET_KEY`(Production 환경의 "Trigger only" 키)를 쓴다. 작업 코드가 쓰는 비밀은 Trigger.dev 쪽에도 있어야 한다. 배포 대상이 둘이 된다.
- **로컬 개발 대응:** `npx trigger.dev dev`가 있다고 알려져 있으나 연 페이지에서 확인하지 못했다(`미확인`).
- **검증 명령:** CI에서 `npx trigger.dev@latest deploy`의 종료 코드. 배포 후 시험 작업을 트리거해서 완료를 확인한다.
- **출처:** https://trigger.dev/docs/deployment/overview (2026-10-01) ⚠️출처확인필요

## Upstash QStash (HTTP 메시지 큐·스케줄러)

- **Terraform:** provider `upstash/upstash`. `upstash_qstash_topic_v2`(`name`, `endpoints`), `upstash_qstash_endpoint`, `upstash_qstash_schedule_v2`(`cron`, `destination`, `retries`, `callback`, `delay`, `method`, `body`, `forward_headers`)
  - **자동화 불가 단계:** Upstash 계정과 API 키
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `retries`: 재시도 횟수(QU.retry_dlq)
  2. `callback`: 실패·완료 콜백
  3. `delay`: 지연
  4. 리전: 03에 따르면 **서울이 없다(EU·US)**(D5, F5). provider 리소스에 리전 인자는 없다.
- **앱 쪽 계약:**
  - 수신 엔드포인트는 `Upstash-Signature` 헤더를 `QSTASH_CURRENT_SIGNING_KEY`와 `QSTASH_NEXT_SIGNING_KEY`로 검증한다(SDK `Receiver.verify()`).
  - 수동으로 검증할 때 확인할 클레임: `iss = "Upstash"`, `sub` = 내 URL, `exp`/`nbf`, `body` SHA-256
  - 발행자는 `QSTASH_TOKEN`을 쓴다.
  - 최소 1회 전달이므로 멱등이어야 한다(03).
- **로컬 개발 대응:** 로컬 개발 서버는 `미확인`이다. QStash가 localhost를 부를 수 없으므로 터널이 필요하다(추론). ⚠️근거없음
- **검증 명령:** Checkov 규칙 없음. 배포 후 서명 없이 엔드포인트를 호출하면 401이 나오는지, QStash 발행 → 수신 → 2xx가 왕복하는지 확인한다.
- **출처:** https://registry.terraform.io/providers/upstash/upstash/latest/docs/resources/qstash_topic_v2 · https://registry.terraform.io/providers/upstash/upstash/latest/docs/resources/qstash_schedule_v2 · https://registry.terraform.io/providers/upstash/upstash/latest/docs/resources/qstash_endpoint · https://upstash.com/docs/qstash/howto/signature (2026-10-01) ⚠️출처확인필요

## Vercel Queues (베타)

- **Terraform:** **불가.** vercel provider에 큐 리소스가 없다(provider 리소스 목록 100개 확인). 소비자는 `vercel.json`으로 구성하고 배포로 반영한다.
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. 소비자 트리거: `vercel.json`의 `functions["<경로>"].experimentalTriggers = [{ "type": "queue/v2beta", "topic": "<토픽>" }]`. **이름에 `experimental`과 `v2beta`가 들어 있다. 베타 동안 바뀔 수 있다.**
  2. 메시지 TTL과 지연: 03에 따르면 기본 24시간, 최대 7일(QU.retention)
  3. 멱등키로 발행 중복 제거(QU.dedup)
- **앱 쪽 계약:** `@vercel/queue`의 `send('<topic>', payload)`와 `handleCallback(async (msg, metadata) => ...)`. Python SDK는 `vercel-queue`다. 인증 방식(OIDC 등)은 `미확인`이다. 토픽을 미리 만들어야 하는지는 `미확인`이다(문서 예시에는 생성 단계가 없다).
- **로컬 개발 대응:** `미확인`. poll 모드로 Vercel 밖에서 소비할 수 있다.
- **검증 명령:** 정적으로 `vercel.json`의 JSON 스키마(`https://openapi.vercel.sh/vercel.json`)를 검증한다. 배포 후 send → 소비자 로그 확인
- **출처:** https://vercel.com/docs/queues (2026-10-01)

---

# 파트 4. 스케줄러

공통 계약(03 §7-3): 외부 스케줄러는 모두 "최소 1회"이거나 "최선 노력"이다. 그래서 스케줄러가 호출하는 엔드포인트나 작업에는 항상 다음을 생성한다.
1. 호출자 인증(아래 절별)
2. **실행 창 유니크 키**(예: `job_name + 예정 시각`을 DB 유니크 제약이나 Redis `SET NX EX`로)
3. 조정형 로직("마지막 성공 이후 미처리분 처리")

## Kubernetes CronJob

- **Terraform:** provider `hashicorp/kubernetes`. `kubernetes_cron_job_v1`. YAML 매니페스트로 생성할 수도 있다.
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `schedule`과 `timezone`: 없으면 kube-controller-manager의 시간대를 따른다. `.spec.timeZone`은 1.27부터 stable이다(B3, D4).
  2. `concurrency_policy`: **기본 `Allow`**. 겹치면 안 되면 `Forbid`, 최신만 필요하면 `Replace`(SC.semantics)
  3. `starting_deadline_seconds`: 놓친 실행을 얼마나 늦게까지 시작할지. 놓친 실행은 실패로 센다.
  4. `backoff_limit`: 재시도 횟수
  5. `active_deadline_seconds`: 최대 실행 시간(A2)
  6. `successful_jobs_history_limit`(기본 3), `failed_jobs_history_limit`(기본 1), `ttl_seconds_after_finished`
  7. `suspend`
  - 문서상 CronJob 이름은 52자 이하다. 100회 넘게 놓치면 더 이상 예약하지 않는다. 작업은 멱등이어야 한다.
- **앱 쪽 계약:** 앱 이미지에 단일 실행 진입점(예: `node scripts/job.js`)을 생성한다. **웹 프로세스 안의 스케줄러(node-cron 등)는 제거하거나 환경변수로 끈다.** 남겨 두면 B3 중복이 그대로 남는다.
- **로컬 개발 대응:** 진입점을 `docker compose run --rm app <job 명령>`으로 직접 실행한다.
- **검증 명령:**
  - Checkov: `CKV_K8S_21`(default 네임스페이스 금지)
  - plan 단언: `concurrency_policy != "Allow"`(B3), `timezone`이 있는지
  - 배포 후: `kubectl create job --from=cronjob/<name> <name>-manual`로 즉시 실행해서 종료 코드를 확인한다.
- **출처:** https://registry.terraform.io/providers/hashicorp/kubernetes/latest/docs/resources/cron_job_v1 · https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/ (2026-10-01)

## Google Cloud Scheduler

- **Terraform:** provider `hashicorp/google`
  - `google_cloud_scheduler_job`
  - 호출용 `google_service_account`
  - `google_cloud_run_v2_service_iam_member`(`roles/run.invoker`)
  - 그 서비스 계정에 대한 `roles/iam.serviceAccountUser`(actAs)
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `schedule`과 `time_zone`(tz 데이터베이스 이름)(D4)
  2. `attempt_deadline`: 핸들러가 이 안에 응답하지 않으면 `DEADLINE_EXCEEDED`로 실패하고 재시도한다(A2).
  3. `retry_config.retry_count`(5 이하), 백오프(SC.semantics)
  4. `http_target.oidc_token { service_account_email, audience }`: Cloud Run 같은 비 googleapis 대상은 OIDC를 쓰고, `*.googleapis.com`은 OAuth 토큰을 쓴다(F5).
  5. `audience`: 비우면 대상 URI를 쓴다. **URL 쿼리 파라미터가 audience에 들어가면 안 된다.**
  6. `pubsub_target`: HTTP 대신 Pub/Sub로 보낼 때
  - `paused`도 있다.
- **앱 쪽 계약:** Cloud Run 비공개 서비스이면 invoker 권한으로 인증한다. 핸들러는 `attempt_deadline`보다 빨리 2xx를 돌려주고, 긴 작업은 Cloud Tasks나 Job으로 넘긴다. 실행 창 유니크 키가 필요하다(03: 드물게 중복).
- **로컬 개발 대응:** 에뮬레이터가 없다(`미확인`). 엔드포인트를 직접 호출한다.
- **검증 명령:**
  - Checkov 규칙 없음
  - plan 단언: `oidc_token`이 있고 `audience`에 `?`가 없는지, invoker IAM이 있는지
  - 배포 후: `gcloud scheduler jobs run <job>`으로 즉시 실행하고 대상 로그에서 200을 확인한다.
- **출처:** https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_scheduler_job · https://docs.cloud.google.com/scheduler/docs/http-target-auth · https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_run_v2_service_iam (2026-10-01)

## Amazon EventBridge Scheduler

- **Terraform:** provider `hashicorp/aws`. `aws_scheduler_schedule`, `aws_scheduler_schedule_group`, `aws_iam_role`(스케줄러가 대상을 부르는 역할), DLQ용 `aws_sqs_queue`
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `schedule_expression`과 `schedule_expression_timezone`: **기본 UTC**. 한국 업무 시간이면 `Asia/Seoul`(D4)
  2. `flexible_time_window { mode = "OFF" | "FLEXIBLE" }`: 필수
  3. `target.arn`과 `target.role_arn`: 필수. 범용 대상은 `arn:aws:scheduler:::aws-sdk:<서비스>:<API>` 형식이다(예: `sqs:sendMessage`).
  4. `target.retry_policy.maximum_retry_attempts`: 0~185, **기본 185**(SC.semantics)
  5. `target.retry_policy.maximum_event_age_in_seconds`: 60~86400, 기본 86400
  6. `target.dead_letter_config { arn }`: SQS DLQ
  7. `action_after_completion`: `NONE` / `DELETE`(일회성 일정)
- **앱 쪽 계약:**
  - 대상은 AWS 서비스 API다. **앱의 HTTPS 엔드포인트를 직접 부르는 대상 형식은 확인하지 못했다(`미확인`).**
  - 그래서 생성 기본값은 "스케줄러 → SQS sendMessage → 앱 워커" 또는 "스케줄러 → ECS RunTask / Lambda"다.
  - HTTP가 꼭 필요하면 EventBridge 규칙 + API destination(위 EventBridge 절)을 쓴다.
  - 기본 재시도가 185회이므로 소비자는 반드시 멱등이어야 한다.
- **로컬 개발 대응:** 작업 진입점을 직접 실행한다.
- **검증 명령:**
  - Checkov: `CKV_AWS_297`(CMK, 과잉일 수 있음)
  - plan 단언: `schedule_expression_timezone`이 명시됐는지, `dead_letter_config`가 있는지
  - 배포 후: 1분 뒤 일회성 일정(`at(...)`, `action_after_completion = "DELETE"`)을 만들어 대상 도착을 확인한다.
- **출처:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/scheduler_schedule · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/scheduler_schedule_group (2026-10-01)

## Vercel Cron Jobs

- **Terraform:** 일부. `vercel_project_crons`는 **프로젝트의 크론을 켜고 끄기만 한다**(`enabled`, `project_id`). 크론 정의는 `vercel.json`의 `crons` 배열(`path`, `schedule`)에 두고 배포로 반영한다. 비밀은 `vercel_project_environment_variable`로 넣는다.
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `schedule`: **Hobby는 하루 1회만 허용하고, 더 자주 실행하는 식은 배포가 실패한다.** 실행 시각은 그 시간 안 아무 때나다(±59분). Pro 이상은 지정한 분 안에 실행된다(SC.frequency, G1).
  2. `CRON_SECRET` 환경변수: 16자 이상 무작위(F5)
  3. 실행 시간: 함수 `maxDuration`을 따른다(A2).
  4. 겹침 방지 락: 실행이 주기보다 길면 두 번째 인스턴스가 시작될 수 있다(B3).
- **앱 쪽 계약:**
  - Vercel이 `Authorization: Bearer <CRON_SECRET>`를 보낸다. 핸들러는 이 값을 비교하고, 다르면 401을 돌려준다.
  - `x-vercel-cron-schedule` 헤더로 어떤 일정인지 알 수 있다.
  - **실패해도 재시도하지 않는다. 전달은 최선 노력이고, 같은 실행이 두 번 올 수도 있다.** 그래서 멱등·조정형 로직과 락이 필요하다.
  - **리다이렉트를 따라가지 않는다**(3xx는 그대로 종료). 경로가 리다이렉트되면 조용히 아무 일도 하지 않는다.
- **로컬 개발 대응:** `vercel dev`나 `next dev`는 크론을 지원하지 않는다. 로컬에서는 엔드포인트를 직접 호출한다.
- **검증 명령:**
  - 정적: `vercel.json` 스키마 검증, Hobby 플랜이면 하루 1회를 넘는 식이 없는지 검사
  - plan 단언: `CRON_SECRET` 환경변수 리소스가 있는지
  - 배포 후: 헤더 없이 호출하면 401, 올바른 Bearer로 호출하면 200인지 확인한다. `vercel crons` CLI로 즉시 실행할 수 있다(관련 문서 링크로만 확인).
- **출처:** https://vercel.com/docs/cron-jobs/manage-cron-jobs · https://registry.terraform.io/providers/vercel/vercel/latest/docs/resources/project_crons · https://registry.terraform.io/providers/vercel/vercel/latest/docs/resources/project_environment_variable (2026-10-01)

## Supabase Cron (pg_cron)

- **Terraform:** **불가.** supabase provider의 리소스는 `apikey`, `branch`, `edge_function`, `edge_function_secrets`, `project`, `settings`, `third_party_auth`뿐이다. 크론은 SQL 마이그레이션으로 만든다.
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `cron.schedule('<이름>', '<주기>', '<SQL>')`: 03에 따르면 최소 1초, 작업당 동시 1개(SC.frequency, SC.semantics)
  2. HTTP 대상이면 `net.http_post(...)`(pg_net)와 헤더. 비밀을 Vault에서 읽는 방식은 연 페이지에서 확인하지 못했다(`미확인`).
  3. 해제: `cron.unschedule('<이름>')`. 마이그레이션을 다시 실행해도 안전하도록 "있으면 해제하고 다시 등록"하는 순서로 생성한다.
- **앱 쪽 계약:** Edge Function을 부르면 함수가 헤더 키를 검증한다(문서 예시는 publishable key를 `apikey` 헤더로 보낸다).
- **로컬 개발 대응:** Supabase CLI 로컬 스택(`supabase start`, 연 문서로 확인하지 못함 `미확인`)
- **검증 명령:** 마이그레이션을 적용한 뒤 `select * from cron.job`으로 등록됐는지 확인한다. 실행 기록은 `cron.job_run_details`에서 본다(테이블 이름 `미확인`).
- **출처:** https://supabase.com/docs/guides/cron/quickstart · https://registry.terraform.io/providers/supabase/supabase/latest/docs/resources/settings (2026-10-01)

## Cloudflare Cron Triggers

- **Terraform:** provider `cloudflare/cloudflare`. `cloudflare_workers_cron_trigger`(`script_name`, `schedules[].cron`). Wrangler 설정의 `[triggers] crons = [...]`로 정의할 수도 있다. 두 경로를 동시에 쓰면 서로 덮어쓸 수 있으므로 하나만 생성한다(추론). ⚠️근거없음
  - **자동화 불가 단계:** Cloudflare API 토큰
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. cron 식: 5필드에 Quartz 확장(`L`, `W`)을 쓴다. **요일이 1~7(일~토)이라 다른 시스템과 다르다.** 기존 cron 식을 옮길 때 요일 변환이 필요하다.
  2. 시간대: **UTC 고정**. 한국 시각 09:00이면 `0 0 * * *`(D4)
  3. 실행 한도: 03에 따르면 CPU Free 10ms, Paid 30초~15분(A2, G1)
  - 변경이 반영되기까지 최대 15분 걸린다.
- **앱 쪽 계약:** Worker에 `scheduled(controller, env, ctx)` 핸들러를 생성한다.
- **로컬 개발 대응:** `wrangler dev` 후 `curl "http://localhost:8787/cdn-cgi/local/scheduled?cron=*+*+*+*+*"`
- **검증 명령:** Checkov 규칙 없음. 정적으로 요일 필드(0이 들어 있으면 경고)와 UTC 변환을 검사한다. 배포 후 대시보드의 "Cron Events"에서 최근 100회를 본다. 반영에 15분이 걸리므로 그 뒤에 확인한다.
- **출처:** https://developers.cloudflare.com/workers/configuration/cron-triggers/ · https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/workers_cron_trigger (2026-10-01)

## GitHub Actions `schedule`

- **Terraform:** 일부. 워크플로 파일은 리포지토리 커밋으로 생성한다. Terraform으로 하려면 `integrations/github`의 `github_repository_file`을 쓴다. 엔드포인트 비밀은 `github_actions_secret`(`secret_name`, `value`; `plaintext_value`는 deprecated)과 `github_actions_variable`로 넣는다.
  - **자동화 불가 단계:** provider 인증(PAT 또는 GitHub App 설치)
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `on.schedule[].cron`: **최소 5분**(SC.frequency)
  2. `timezone`: IANA 이름을 지원하고 기본은 UTC다. DST로 건너뛴 시간은 다음 유효 시각으로 밀린다.
  3. 공개 리포지토리는 **60일 동안 활동이 없으면 예약 워크플로가 자동으로 꺼진다.** 운영 스케줄러로 쓰면 조용히 멈출 위험이 있다.
  4. 부하가 높으면 지연된다(03: 드롭될 수 있다). 기본 브랜치의 최신 커밋에서 실행된다.
- **앱 쪽 계약:** 워크플로가 앱 엔드포인트를 `Authorization: Bearer ${{ secrets.<NAME> }}`로 호출한다. 앱은 이 헤더를 검증하고, 실행 창 유니크 키를 둔다.
- **로컬 개발 대응:** 해당 없음(엔드포인트를 직접 호출한다)
- **검증 명령:** 정적으로 워크플로 YAML을 검증한다(`actionlint` 같은 도구, 이번에 확인하지 않음 `미확인`). `workflow_dispatch`를 함께 생성해서 배포 후 `gh workflow run <file>`로 즉시 실행해 본다.
- **출처:** https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows · https://registry.terraform.io/providers/integrations/github/latest/docs/resources/actions_secret · https://registry.terraform.io/providers/integrations/github/latest/docs/resources/actions_variable (2026-10-01)

---

# 파트 5. 실시간 연결

## Socket.IO — Redis 어댑터 / Redis Streams 어댑터

- **Terraform:** 해당 없음. 하부 Redis(파트 2)와 **로드밸런서 스티키 세션**을 생성한다.
  - AWS ALB: `aws_lb_target_group.stickiness`
  - Cloud Run: `google_cloud_run_v2_service.template.session_affinity`
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. 스티키 세션: Socket.IO 문서 — 어댑터를 써도 필요하고, 없으면 HTTP 400이 난다(RT.fanout, A3).
  2. 어댑터 종류: pub/sub 어댑터는 Redis 연결이 끊기면 다른 서버로 가는 패킷이 사라진다. 03에 따르면 Streams 어댑터는 유실이 없다(C7).
  3. Redis 7 이상의 클러스터·서버리스이면 `createShardedAdapter()`(샤딩 pub/sub)
  4. 플랫폼 연결 지속 한도(A3, 05 파일)
- **앱 쪽 계약:** `@socket.io/redis-adapter`, `const pubClient = createClient({ url }); const subClient = pubClient.duplicate(); await Promise.all([pubClient.connect(), subClient.connect()]); new Server({ adapter: createAdapter(pubClient, subClient) })`. 같은 앱의 세션 저장소가 connect-redis이면 그것도 **node-redis(`redis` 패키지) 클라이언트만** 받는다(`new RedisStore({ client, prefix })`, 기본 prefix `sess:`, 기본 ttl 86400초). ioredis를 쓰는 기존 코드라면 클라이언트를 하나 더 만들어야 한다.
- **로컬 개발 대응:** `redis` 이미지와 앱 인스턴스 2개를 compose에 두고, 앞에 스티키를 지원하는 프록시를 둔다(프록시 이미지는 생성 규칙, `미확인`).
- **검증 명령:** 배포 후 인스턴스 A에 붙은 클라이언트가 보낸 메시지를 인스턴스 B에 붙은 클라이언트가 받는지 확인한다(인스턴스 2개 이상으로 강제). plan 단언으로 스티키 설정이 있는지 검사한다.
- **출처:** https://socket.io/docs/v4/redis-adapter/ · https://github.com/tj/connect-redis · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_target_group · https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_run_v2_service (2026-10-01) ⚠️출처확인필요

## Supabase Realtime (Broadcast / Presence / Postgres Changes)

- **Terraform:** **불가.** provider에 Realtime 리소스가 없다. 비공개 채널 권한은 `realtime.messages` 테이블의 RLS 정책(SQL 마이그레이션)으로 만든다.
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. 플랜과 동시 연결: 03에 따르면 Free 200, Pro 500, 지출 상한을 풀면 10,000(RT.connections, A3)
  2. 비공개 채널: 클라이언트 `private: true`와 `realtime.messages` RLS(F5)
  3. 서버 발행 경로: REST `POST /realtime/v1/api/broadcast/{topic}/events/{event}` 또는 DB 함수 `realtime.send()`, `realtime.broadcast_changes()`
- **앱 쪽 계약:** `supabase.channel('<topic>', { config: { private: true } }).on('broadcast', ...)`. 바이너리 메시지는 supabase-js 2.91.0 이상에서만 받는다. 메시지는 3일 뒤 자동 삭제된다. 환경변수 이름(`SUPABASE_URL` 등)은 `미확인`이다.
- **로컬 개발 대응:** Supabase CLI `config.toml`의 `[realtime] enabled`(기본 true)
- **검증 명령:** 배포 후 인증 안 된 클라이언트가 비공개 채널 구독에 실패하고, 인증된 두 클라이언트 사이에 메시지가 왕복하는지 확인한다.
- **출처:** https://supabase.com/docs/guides/realtime/broadcast · https://supabase.com/docs/guides/local-development/cli/config (2026-10-01)

## Firebase Realtime Database 리스너

- **Terraform:** 일부. `google_firebase_database_instance`(**beta, `google-beta` provider로 쓰라는 경고가 문서에 있다**). `google_firebase_project`도 필요하다. **보안 규칙은 Terraform으로 배포할 수 없다.** `firebaserules_release`는 Firestore(`cloud.firestore`)와 Storage(`firebase.storage/<bucket>`)용이다. RTDB 규칙은 `firebase deploy --only database`, RTDB 전용 REST 인터페이스, 또는 Admin SDK `setRules()`로 배포한다.
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `region`: 03에 따르면 서울이 없다(싱가포르)(D5, F5)
  2. `instance_id`: 전역에서 고유하고 삭제한 뒤 재사용할 수 없다.
  3. `type`: 기본 DB는 프로젝트당 1개이고 지울 수 없다. **사용자 DB를 만들려면 Blaze 플랜이 필요하다**(G3).
  4. 보안 규칙 파일(`database.rules.json`, `firebase.json`에서 참조)(F5)
- **앱 쪽 계약:** 클라이언트 SDK 설정(databaseURL). 서버에서 쓰면 Admin SDK
- **로컬 개발 대응:** Firebase 에뮬레이터 `firebase emulators:start`. RTDB 포트 9000, Node 16 이상과 **Java 11 이상**이 필요하다. CI는 `FIREBASE_TOKEN`을 쓴다.
- **검증 명령:** 규칙은 에뮬레이터 테스트(`firebase emulators:exec`)로 확인한다. 배포 후 인증 안 된 쓰기가 거부되는지 확인한다.
- **출처:** https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/firebase_database_instance · https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/firebaserules_release · https://firebase.google.com/docs/rules/manage-deploy · https://firebase.google.com/docs/emulator-suite/install_and_configure (2026-10-01)

## Pusher Channels

- **Terraform:** **불가.** Registry에서 `pusher/pusher`는 404다.
  - **자동화 불가 단계:** 앱 생성, 클러스터 선택, 자격 증명 발급(대시보드)
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. 클러스터: 03에 따르면 서울이 없다(도쿄). 클러스터 목록은 연 페이지에서 확인하지 못했다(`미확인`)(D5).
  2. 플랜별 동시 연결: 03에 따르면 100(무료)부터(RT.connections)
  3. 메시지 크기: 03에 따르면 10 KB(RT.limits)
- **앱 쪽 계약:** `APP_ID`, `APP_KEY`, `APP_SECRET`, `APP_CLUSTER`(문서의 자리표시자 이름). 비공개·프레즌스 채널에는 서버 인증 엔드포인트가 필요하다(기본 `/pusher/user-auth`). `useTLS: true`
- **로컬 개발 대응:** `미확인`(실제 Pusher 앱의 개발용 인스턴스를 쓴다)
- **검증 명령:** 배포 후 인증 엔드포인트가 인증 없는 요청을 거부하는지, 서버 trigger → 클라이언트 수신이 되는지 확인한다.
- **출처:** https://pusher.com/docs/channels/server_api/authenticating-users/ (2026-10-01) ⚠️출처확인필요

## Ably

- **Terraform:** provider `ably/ably`. `ably_app`(`tls_only` 등), `ably_api_key`(`capabilities`), `ably_namespace`(`authenticated`, `persisted`, `persist_last`, `tls_only`, `batching_enabled`, `conflation_enabled` 등). 연동 규칙 리소스(`ably_rule_*`)도 있다.
  - **자동화 불가 단계:** provider 인증용 Control API 토큰
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `ably_api_key.capabilities`: 키별 채널·동작 권한(F5)
  2. `ably_namespace.authenticated`, `identified`: 익명 접속 금지
  3. `persisted` / `persist_last`: 메시지 보존(C7)
  4. `tls_only`
- **앱 쪽 계약:** **API 키는 서버에만 둔다**(환경변수 이름 `ABLY_API_KEY`는 생성 규칙). 클라이언트는 `authUrl` 또는 `authCallback`으로 서버에서 토큰(JWT 권장)을 받는다. 토큰 수명은 최대 24시간이고, 회수 가능한 토큰은 1시간이다.
- **로컬 개발 대응:** `미확인`
- **검증 명령:** Checkov 규칙 없음. 정적으로 프런트엔드 번들에 API 키 형식 문자열이 없는지 검사한다. 배포 후 토큰 발급 → 구독 → 발행 왕복
- **출처:** https://registry.terraform.io/providers/ably/ably/latest/docs/resources/app · https://registry.terraform.io/providers/ably/ably/latest/docs/resources/api_key · https://registry.terraform.io/providers/ably/ably/latest/docs/resources/namespace · https://ably.com/docs/auth/token (2026-10-01) ⚠️출처확인필요

## AWS API Gateway WebSocket API

- **Terraform:** provider `hashicorp/aws`
  - `aws_apigatewayv2_api`(`protocol_type = "WEBSOCKET"`)
  - `aws_apigatewayv2_route`(`$connect`, `$disconnect`, `$default`), `aws_apigatewayv2_integration`, `aws_apigatewayv2_stage`
  - `aws_lambda_function`, 연결 ID 저장소(DynamoDB, 02 파일)
  - 백엔드가 `@connections`를 호출할 IAM 권한
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `route_selection_expression`: 예 `$request.body.action`
  2. `$connect` 라우트의 `authorization_type`: WebSocket에서는 `NONE`/`AWS_IAM`/`CUSTOM`(Lambda authorizer)(F5)
  3. 스테이지 `default_route_settings`의 `throttling_burst_limit`, `throttling_rate_limit`(D3)
  4. 스테이지 접근 로그
  5. 연결 수명: 03에 따르면 최대 2시간, 유휴 10분. 클라이언트 재연결과 하트비트를 생성해야 한다(A3, RT.limits).
  6. 브로드캐스트가 없다(03). 연결 ID 목록을 저장하고 하나씩 POST하는 팬아웃 코드가 필요하다(RT.fanout).
- **앱 쪽 계약:**
  - 백엔드는 `POST https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/@connections/{connection_id}`를 SigV4로 서명해서 호출한다(`ApiGatewayManagementApiClient` + `PostToConnectionCommand`). `GET`(상태)과 `DELETE`(끊기)도 있다.
  - 끊긴 연결에 보내면 `GoneException`이 난다. 이때 저장소에서 그 연결을 지운다.
  - IAM 동작 이름(`execute-api:ManageConnections`)은 연 페이지에 없었다(`미확인`).
- **로컬 개발 대응:** `미확인`
- **검증 명령:**
  - Checkov: `CKV_AWS_309`(라우트 인증 유형 지정), `CKV_AWS_76`(스테이지 접근 로그), `CKV2_AWS_51`(클라이언트 인증서, WebSocket에는 과잉일 수 있음)
  - 배포 후: `wscat` 같은 도구로 2개를 연결하고 팬아웃을 확인한다(도구는 생성 규칙). 11분 동안 유휴로 두면 끊기는지, 클라이언트가 다시 연결하는지 확인한다.
- **출처:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/apigatewayv2_api · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/apigatewayv2_route · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/apigatewayv2_stage · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/apigatewayv2_integration · https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-how-to-call-websocket-api-connections.html (2026-10-01)

## AWS AppSync (GraphQL 구독 / Event API)

- **Terraform:** provider `hashicorp/aws`
  - Event API: `aws_appsync_api`(`event_config`), `aws_appsync_channel_namespace`
  - GraphQL: `aws_appsync_graphql_api`, `aws_appsync_datasource`, `aws_appsync_resolver`
  - API 키 인증이면 `aws_appsync_api_key`
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. Event API `event_config.auth_provider[].auth_type`: `API_KEY`/`AWS_IAM`/`AMAZON_COGNITO_USER_POOLS`/`OPENID_CONNECT`/`AWS_LAMBDA`(F5)
  2. `event_config.connection_auth_mode`(필수), 그리고 네임스페이스별 발행·구독 인증
  3. GraphQL `authentication_type`(같은 값 목록)
  4. 로깅과 WAF(F5)
- **앱 쪽 계약:** Event API는 HTTP나 WebSocket으로 발행하고 WebSocket으로 구독한다. 와일드카드 채널(`namespace/channel/*`)을 쓸 수 있다. EventBridge·Lambda에서 직접 발행할 수 있다. 클라이언트 라이브러리(Amplify 등)는 연 페이지에 명시되지 않았다(`미확인`).
- **로컬 개발 대응:** `미확인`
- **검증 명령:**
  - Checkov(GraphQL만): `CKV_AWS_193`(로깅), `CKV_AWS_194`(필드 로그), `CKV2_AWS_33`(WAF)
  - Checkov(캐시): `CKV_AWS_214`, `CKV_AWS_215`
  - Event API(`aws_appsync_api`)용 규칙은 색인에 없다.
  - 배포 후: 두 클라이언트로 구독·발행 왕복
- **출처:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/appsync_api · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/appsync_channel_namespace · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/appsync_graphql_api · https://docs.aws.amazon.com/appsync/latest/eventapi/event-api-welcome.html (2026-10-01)

## Cloudflare Durable Objects (WebSocket Hibernation)

- **Terraform:** 일부, `[충돌]`.
  - Terraform 쪽: `cloudflare_workers_script`에 `migrations`(`new_sqlite_classes`, `renamed_classes`, `transferred_classes`, `steps`)와 `bindings`(`type = "durable_object_namespace"`, `class_name`) 인자가 있다.
  - Cloudflare 문서 쪽: "Durable Object 수명 주기 변경은 `wrangler deploy`로만 적용된다"(`wrangler versions upload`로는 안 된다). 변경은 원자적이라 점진 배포할 수 없고, 롤백은 수명 주기 변경 경계를 넘을 수 없다. 또 예전 `migrations` 배열은 deprecated이고 새 `exports` 필드로 바뀌었으며, 한 번 바꾸면 되돌릴 수 없다.
  - 둘의 관계(Terraform API 경로로 적용해도 되는가)는 `미확인`이다. **생성 기본값은 wrangler 설정 + `wrangler deploy`로 한다.**
  - **자동화 불가 단계:** Cloudflare API 토큰
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. 클래스 선언(`exports` 또는 legacy `new_sqlite_classes`): SQLite 저장소
  2. 바인딩 `durable_objects.bindings[{ name, class_name }]`
  3. 위치 힌트: 03에 따르면 서울을 보장하지 않는다(D5, F5)
- **앱 쪽 계약:** Worker가 `env.<BINDING>.idFromName(roomId)`로 방 단위 객체에 라우팅한다(API 이름은 `미확인`). 객체 안에서 WebSocket Hibernation API를 쓴다.
- **로컬 개발 대응:** `wrangler dev`(DO 지원 여부 `미확인`)
- **검증 명령:** 배포 후 같은 방에 붙은 두 클라이언트 사이의 메시지 왕복. 클래스 이름을 바꿀 때는 롤백할 수 없으므로 배포 전에 사람에게 알린다.
- **출처:** https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/workers_script · https://developers.cloudflare.com/durable-objects/reference/durable-objects-migrations/ (2026-10-01)

---

# 파트 6. 파일 저장소

공통 계약(B2, A7): 로컬 디스크(`uploads/`)를 객체 저장소로 바꿀 때 생성물은 다음 세 가지를 바꾼다.
1. 저장 코드: 파일 쓰기 → SDK 업로드
2. 큰 파일: 서버를 거치지 않는 직접 업로드(서명 URL·클라이언트 토큰). 플랫폼의 본문 한도(CP.request_size)를 피한다.
3. 읽기: 정적 경로 → 서명 GET URL 또는 CDN

## Amazon S3 — S3 Standard (범용 버킷)

- **Terraform:** provider `hashicorp/aws`
  - `aws_s3_bucket`, `aws_s3_bucket_public_access_block`, `aws_s3_bucket_ownership_controls`, `aws_s3_bucket_versioning`, `aws_s3_bucket_lifecycle_configuration`, `aws_s3_bucket_cors_configuration`, `aws_s3_bucket_server_side_encryption_configuration`, `aws_s3_bucket_policy`
  - 앱 역할의 IAM 정책
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `aws_s3_bucket_public_access_block`: `block_public_acls`, `block_public_policy`, `ignore_public_acls`, `restrict_public_buckets`. **Terraform 리소스의 네 인자 기본값은 모두 `false`다.** 명시적으로 `true`를 써야 한다(F5).
  2. `aws_s3_bucket_ownership_controls.object_ownership = "BucketOwnerEnforced"`: ACL을 끈다.
  3. `aws_s3_bucket_versioning.status = "Enabled"`: C7이 "사용자 생성" 이상일 때(FS.versioning_lifecycle)
  4. 수명 주기: `abort_incomplete_multipart_upload.days_after_initiation`(멀티파트 잔여물), `noncurrent_version_expiration.noncurrent_days`(버전 관리 비용), 필요하면 `expiration`(C6, G3)
  5. CORS(서명 URL로 브라우저 업로드할 때)(A7)
     - `allowed_methods`: 값은 `GET`/`PUT`/`HEAD`/`POST`/`DELETE`
     - `allowed_origins`: 앱 도메인, `*` 금지
     - `allowed_headers`
     - `expose_headers`: 멀티파트면 `ETag`
     - `max_age_seconds`
  6. `aws_s3_bucket_server_side_encryption_configuration.sse_algorithm`: `AES256` / `aws:kms` / `aws:kms:dsse`(F5)
  7. `force_destroy`: 기본 `false`. 사용자 데이터 버킷은 `false`를 유지한다.
  8. `object_lock_enabled`: 규제 데이터(F5)일 때만
- **앱 쪽 계약:**
  - 자격 증명은 IAM 역할(정적 키 금지). django-storages는 설정이 없으면 boto3 기본 세션(IAM 역할 포함)을 찾는다.
  - Django: `STORAGES = {"default": {"BACKEND": "storages.backends.s3.S3Storage", ...}}`
    - `AWS_STORAGE_BUCKET_NAME`(필수), `AWS_S3_REGION_NAME`
    - `AWS_DEFAULT_ACL`: 기본 `None` = 비공개
    - `AWS_QUERYSTRING_AUTH`: 기본 `True` = 서명 URL
    - `AWS_QUERYSTRING_EXPIRE`: 기본 3600
    - `AWS_S3_FILE_OVERWRITE`: **기본 `True`라서 같은 이름 파일을 덮어쓴다.** 사용자 업로드는 `False`나 무작위 키
    - `AWS_S3_SIGNATURE_VERSION`: 기본 `s3v4`
  - boto3:
    - `generate_presigned_url('put_object' | 'get_object', Params=..., ExpiresIn=...)`
    - `generate_presigned_post(bucket, key, Fields=..., Conditions=[["content-length-range", 0, N]], ExpiresIn=...)`
    - **서명 URL은 만든 주체의 자격 증명을 쓴다.** 임시 자격 증명(IAM 역할)이 만료되면 `ExpiresIn`이 남아 있어도 URL이 무효가 된다. 역할 세션보다 긴 만료를 주면 안 된다.
- **로컬 개발 대응:**
  - **기본 대체재 두 개가 모두 막혔다.** MinIO는 보관됐고 바이너리를 배포하지 않는다. LocalStack은 auth token이 필요하고 무료 플랜은 비상업 용도만 허용한다.
  - 토큰 없이 쓸 수 있는 S3 호환 대체재는 이번 조사에서 확인하지 못했다(`미확인`).
  - 생성 규칙: 저장 계층을 인터페이스로 분리하고, 로컬은 파일시스템 구현(django-storages 대신 `FileSystemStorage`)을 쓴다. S3 경로는 개발용 실제 버킷으로 검증한다.
- **검증 명령:**
  - Checkov(통과해야 함): `CKV_AWS_53`, `CKV_AWS_54`, `CKV_AWS_55`, `CKV_AWS_56`(공개 차단 4종), `CKV2_AWS_6`(공개 차단 존재), `CKV_AWS_20`, `CKV_AWS_57`(공개 ACL 없음), `CKV_AWS_70`(Principal `*` 없음), `CKV2_AWS_65`(ACL 비활성), `CKV_AWS_19`(저장 암호화), `CKV_AWS_300`(멀티파트 중단 기간), `CKV2_AWS_61`(수명 주기), `CKV_AWS_21`(C7이 높을 때 버전 관리)
  - Checkov(작은 앱에는 과잉이라 **명시적 건너뛰기 목록**이 필요함): `CKV_AWS_18`(접근 로그), `CKV_AWS_144`(교차 리전 복제), `CKV_AWS_145`(KMS), `CKV2_AWS_62`(이벤트 알림), `CKV_AWS_143`(Object Lock)
  - 배포 후:
    - 인스턴스 A에서 서명 PUT으로 업로드 → 인스턴스 B에서 서명 GET으로 읽기(B2)
    - 익명 GET이 403인지
    - 브라우저 출처에서 CORS preflight가 통과하는지
- **출처:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_public_access_block · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_ownership_controls · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_versioning · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_lifecycle_configuration · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_cors_configuration · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_server_side_encryption_configuration · https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html · https://docs.aws.amazon.com/boto3/latest/guide/s3-presigned-urls.html (2026-10-01) ⚠️출처확인필요

## Google Cloud Storage — Standard

- **Terraform:** provider `hashicorp/google`. `google_storage_bucket`, `google_storage_bucket_iam_member`. 서명할 서비스 계정에 대한 IAM(아래 미확인 참고)
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `location`: 서울은 `asia-northeast3`(D5)
  2. `uniform_bucket_level_access = true`: 기본 `false`(F5)
  3. `public_access_prevention = "enforced"`: `inherited`이면 조직 정책을 따른다(F5).
  4. `versioning { enabled = true }`(C7)
  5. `lifecycle_rule { action { type = "Delete" | "SetStorageClass" | "AbortIncompleteMultipartUpload" } condition { age, num_newer_versions, ... } }`
     - **`num_newer_versions = 0`은 Terraform에서 무시된다는 버그가 문서에 있다**(`send_num_newer_versions_if_zero` 필요).
     - `age = 0`도 `send_age_if_zero`가 필요하다.
  6. `cors { origin, method, response_header, max_age_seconds }`(A7)
  7. `soft_delete_policy.retention_duration_seconds`: 기본 604800(7일), 범위 7~90일, 끄려면 0(C7, G3)
  - `force_destroy`(기본 false), `retention_policy`도 있다.
- **앱 쪽 계약:**
  - V4 서명 URL은 **최대 604800초(7일)**이고 **XML API 엔드포인트로만** 쓸 수 있다.
  - Cloud Run처럼 개인 키 파일이 없는 환경에서 서명하는 방법(IAM signBlob)과 필요 권한은 연 페이지에 없었다(`미확인`). 생성 전에 확인해야 하는 위험 항목이다.
  - django-storages의 GCS 백엔드는 이번에 열지 않았다(`미확인`).
- **로컬 개발 대응:** 공식 GCS 에뮬레이터는 `미확인`이다. Firebase Storage 에뮬레이터(포트 9199)는 Firebase SDK용이다.
- **검증 명령:**
  - Checkov: `CKV_GCP_114`(공개 접근 방지 enforced), `CKV_GCP_29`(균일 접근), `CKV_GCP_78`(버전 관리), `CKV_GCP_28`(IAM 공개 아님), `CKV_GCP_62`·`CKV_GCP_63`(접근 로그, 과잉일 수 있음)
  - 배포 후: 서명 PUT → 다른 인스턴스에서 서명 GET. 익명 GET이 거부되는지 확인한다.
- **출처:** https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_bucket · https://docs.cloud.google.com/storage/docs/access-control/signed-urls (2026-10-01)

## Cloudflare R2

- **Terraform:** provider `cloudflare/cloudflare`. `cloudflare_r2_bucket`(`name`, `location`, `jurisdiction`, `storage_class`), `cloudflare_r2_bucket_cors`, `cloudflare_r2_bucket_lifecycle`, 선택으로 `cloudflare_r2_custom_domain`, `cloudflare_r2_bucket_lock`
  - **S3 API용 액세스 키(R2 API 토큰)를 Terraform이나 API로 발급할 수 있는지는 `미확인`이다.** 확인되기 전에는 자동화 불가 단계로 본다.
  - **자동화 불가 단계:** provider 인증 API 토큰
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `location`: 힌트만 준다(03)(D5)
  2. `jurisdiction`(F5)
  3. `cloudflare_r2_bucket_cors.rules[].allowed.methods`, `origins`, `headers`, `expose_headers`, `max_age_seconds`: 브라우저에서 서명 URL을 쓰면 필수다(A7).
  4. `cloudflare_r2_bucket_lifecycle.rules[]`: `abort_multipart_uploads_transition`, `delete_objects_transition`, `storage_class_transitions`
  5. 공개 접근: 커스텀 도메인 또는 관리형 도메인(`cloudflare_r2_managed_domain`)을 쓸지
- **앱 쪽 계약:**
  - S3 SDK의 `endpoint_url = https://<ACCOUNT_ID>.r2.cloudflarestorage.com`, `region = "auto"`
  - 서명 URL은 `GET`/`HEAD`/`PUT`/`DELETE`만 지원하고, **POST(HTML 폼 업로드)는 지원하지 않는다.** 그래서 boto3 `generate_presigned_post` 기반 코드는 R2에서 동작하지 않고 서명 PUT으로 바꿔야 한다.
  - 만료는 1초~7일
  - django-storages S3 백엔드에는 `AWS_S3_ENDPOINT_URL`을 지정한다(설정 이름은 연 페이지 범위 밖, `미확인`).
- **로컬 개발 대응:** S3와 같은 문제(1.3)
- **검증 명령:** Checkov 규칙 없음. plan 단언으로 CORS 규칙과 수명 주기가 있는지 검사한다. 배포 후 서명 PUT → GET 왕복
- **출처:** https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/r2_bucket · https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/r2_bucket_cors · https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/r2_bucket_lifecycle · https://developers.cloudflare.com/r2/api/s3/presigned-urls/ (2026-10-01)

## Supabase Storage

- **Terraform:** **불가**(버킷 단위). supabase provider에 버킷 리소스가 없다. `supabase_settings.storage`(직렬화된 JSON)로 프로젝트 수준 저장소 설정을 넣을 수 있지만 JSON 키는 `미확인`이다.
  - 버킷은 SQL(`insert into storage.buckets (id, name, public) values (...)`), JS 클라이언트(`supabase.storage.createBucket`), 또는 대시보드로 만든다.
  - 접근 정책은 `storage.objects`의 RLS 정책을 SQL 마이그레이션으로 만든다(정책 문법은 연 페이지에 없어 `미확인`).
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `public`(기본 false)(F5)
  2. `file_size_limit`: 03에 따르면 Free는 파일당 50 MB(A7, G1)
  3. `allowed_mime_types`
  4. RLS 정책(F5)
- **앱 쪽 계약:** `supabase.storage.from('<bucket>').upload(...)`. 서명 업로드 URL API는 `미확인`이다.
- **로컬 개발 대응:** Supabase CLI `config.toml`
  - `[storage] file_size_limit`: 기본 50MiB
  - `[storage.buckets.<name>]`: `public`, `file_size_limit`, `allowed_mime_types`, `objects_path`
  - **이 설정은 로컬 개발용이다.** 원격 프로젝트에 반영되는지는 `미확인`이다. 그래서 운영 버킷은 SQL 마이그레이션으로 따로 만든다.
- **검증 명령:** 마이그레이션을 적용한 뒤 `select id, public, file_size_limit from storage.buckets`. 배포 후 익명 업로드가 거부되고 인증 업로드는 허용되는지 확인한다.
- **출처:** https://supabase.com/docs/guides/storage/buckets/creating-buckets · https://supabase.com/docs/guides/local-development/cli/config · https://registry.terraform.io/providers/supabase/supabase/latest/docs/resources/settings (2026-10-01)

## Vercel Blob

- **Terraform:** provider `vercel/vercel`. `vercel_blob_store`(`name`, `access` = `public`/`private`, `region`), `vercel_blob_project_connection`(`blob_store_id`, `project_id`, `env_var_prefix`, `environments`; 출력 `read_write_token_env_var_name`)
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `access`: `private`이면 인증된 전달(F5)
  2. `region`: 03에 따르면 서울(icn1) 가능(D5)
  3. `environments`: **로컬에서 쓰려면 Development를 포함해야 `vercel env pull`로 받아진다.**
  4. 업로드 경로: 서버 업로드는 4.5 MB까지다. 넘으면 클라이언트 업로드(A7)
- **앱 쪽 계약:**
  - 기본은 OIDC다: `BLOB_STORE_ID` + `VERCEL_OIDC_TOKEN`(자동 교체)
  - `BLOB_READ_WRITE_TOKEN`(장기 정적 토큰)은 `handleUpload`로 클라이언트 토큰을 만들 때와 Vercel 밖에서 실행되는 코드에 필요하다. `handleUploadPresigned`는 OIDC로 동작하고 `BLOB_WEBHOOK_PUBLIC_KEY`로 콜백을 검증한다.
  - 클라이언트: `upload(name, file, { access, handleUploadUrl: '/api/.../upload' })`
  - 서버: `handleUpload({ body, request, onBeforeGenerateToken, onUploadCompleted })`
    - **`onBeforeGenerateToken`에서 사용자 인증을 하지 않으면 누구나 업로드할 수 있다.** 생성 코드에 인증 검사를 반드시 넣는다.
    - `allowedContentTypes`, `addRandomSuffix`, `tokenPayload`
- **로컬 개발 대응:** 에뮬레이터가 없다. Development 환경 토큰으로 실제 저장소를 쓴다. **`onUploadCompleted` 콜백은 localhost에서 동작하지 않는다.** ngrok 같은 터널을 쓰고 `VERCEL_BLOB_CALLBACK_URL`을 지정한다.
- **검증 명령:** Checkov 규칙 없음. 정적으로 `onBeforeGenerateToken` 본문에 인증 호출이 있는지 검사한다. 배포 후 미인증 토큰 요청이 400/401인지, 5 MB 넘는 파일의 클라이언트 업로드 후 콜백이 오는지 확인한다(콜백은 200을 받을 때까지 5회 재시도한다).
- **출처:** https://registry.terraform.io/providers/vercel/vercel/latest/docs/resources/blob_store · https://registry.terraform.io/providers/vercel/vercel/latest/docs/resources/blob_project_connection · https://vercel.com/docs/vercel-blob/client-upload (2026-10-01)

## Cloud Storage for Firebase

- **Terraform:** provider `hashicorp/google`
  - `google_storage_bucket`, `google_firebase_storage_bucket`(`bucket_id`)
  - `google_firebaserules_ruleset`, `google_firebaserules_release`(`name = "firebase.storage/<bucket>"`)
  - `google_firebase_project`
  - **자동화 불가 단계:** 03에 따르면 Blaze 플랜이 필요하다. 결제 계정 연결을 Terraform으로 끝낼 수 있는지는 `미확인`이다.
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. 보안 규칙(`ruleset` 본문): 예 `allow read, write: if request.auth != null`(F5)
  2. 하부 버킷의 `location`, `versioning`, `lifecycle_rule`(GCS 절)
  3. 업로드 크기와 콘텐츠 유형 제한은 규칙 안에서(A7)
  4. 하부 버킷의 공개 접근 방지 여부: Firebase 다운로드 URL과의 관계는 `미확인`
- **앱 쪽 계약:** Firebase SDK의 `storageBucket` 설정. 에뮬레이터 연결 환경변수 이름은 `미확인`이다.
- **로컬 개발 대응:** Firebase 에뮬레이터, Storage 포트 9199(Java 11 이상)
- **검증 명령:** 규칙은 에뮬레이터 테스트로 확인한다. Checkov는 하부 `google_storage_bucket` 규칙(GCS 절)을 적용한다. 배포 후 미인증 업로드가 거부되는지 확인한다.
- **출처:** https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/firebase_storage_bucket · https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/firebaserules_ruleset · https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/firebaserules_release · https://firebase.google.com/docs/rules/manage-deploy · https://firebase.google.com/docs/emulator-suite/install_and_configure (2026-10-01)

## Amazon EFS (NFS 공유 파일 시스템)

- **Terraform:** provider `hashicorp/aws`
  - `aws_efs_file_system`, `aws_efs_mount_target`(AZ마다), `aws_efs_access_point`, `aws_efs_backup_policy`, `aws_efs_file_system_policy`, 보안 그룹
  - ECS에서 마운트하려면 `aws_ecs_task_definition`의 `volume.efs_volume_configuration`
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `encrypted = true`(F5)
  2. `throughput_mode`: 기본 `bursting`. 문서상 AWS는 대부분 `elastic`을 권장한다(D2).
  3. `performance_mode`: `generalPurpose`(기본) / `maxIO`
  4. `availability_zone_name`: 지정하면 One Zone이 된다(F1과 맞바꿈, G3)
  5. `lifecycle_policy`: 저빈도 계층으로 옮겨 비용 절감. 03에 따르면 저장 단가가 S3의 13배다(G3).
  6. `aws_efs_access_point`의 `posix_user`, `root_directory`(F5)
  7. `aws_efs_backup_policy.status = "ENABLED"`(C7)
  - `protection`(복제 덮어쓰기 보호)도 있다.
- **앱 쪽 계약:** 앱은 마운트 경로(예: `/mnt/data`, 환경변수 `DATA_DIR`)에 POSIX로 쓴다. 코드 변경이 가장 적은 B2 처방이다. 03에 따르면 일관성은 `미확인`(NFS)이므로 SQLite 같은 파일 잠금 의존은 이 처방에서 제외한다(01 파일 판정).
- **로컬 개발 대응:** compose의 이름 있는 볼륨(NFS 의미는 재현되지 않는다)
- **검증 명령:**
  - Checkov: `CKV_AWS_42`(암호화), `CKV_AWS_184`(CMK, 과잉일 수 있음), `CKV_AWS_329`(액세스 포인트 루트 디렉터리), `CKV_AWS_330`(액세스 포인트 사용자)
  - 배포 후: 태스크 A에서 파일을 쓰고 태스크 B에서 읽기
- **출처:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/efs_file_system · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/efs_mount_target · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/efs_access_point · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/efs_backup_policy · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_task_definition (2026-10-01)

## Google Filestore (NFS)

- **Terraform:** provider `hashicorp/google`. `google_filestore_instance`. Cloud Run에서 마운트하려면 `google_cloud_run_v2_service`의 `template.volumes.nfs`와 VPC 연결
- **요구 수준에 따라 바뀌는 핵심 속성:**
  1. `tier`: `BASIC_HDD`, `BASIC_SSD`, `ZONAL`, `REGIONAL`, `ENTERPRISE` 등(F1, G3)
  2. `file_shares.capacity_gb`: **BASIC_HDD 최소 1024 GiB, BASIC_SSD 최소 2560 GiB**(G3: 03의 최소 비용 근거)
  3. `networks`(필수, 1개)(F5)
  4. `deletion_protection_enabled`(C7)
- **앱 쪽 계약:** EFS와 같다(마운트 경로에 POSIX로 쓴다).
- **로컬 개발 대응:** compose 이름 있는 볼륨
- **검증 명령:** Checkov 규칙 없음. plan 단언으로 G3이 "높음"인데 Filestore가 생성되면 경고한다(최소 용량 비용). 배포 후 인스턴스 2개에서 교차 읽기·쓰기
- **출처:** https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/filestore_instance · https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_run_v2_service (2026-10-01)

---

# 7. 생성 자동화에서 걸리는 발견

1. **큐에 맞는 Redis 설정은 정책 도구로 검사되지 않는다.** Checkov 색인에는 `maxmemory-policy`를 보는 규칙이 없다. ElastiCache Serverless는 이 값을 바꿀 인자 자체가 없다. 그래서 "큐 용도 Redis = noeviction" 검사는 plan JSON 맞춤 단언(1.2)으로만 할 수 있다. 서버리스와 큐 라이브러리의 조합은 생성 단계에서 거부해야 한다.
   - 클러스터 모드(ElastiCache Serverless, Memorystore Cluster, Valkey `CLUSTER`)를 고르면 BullMQ는 해시 태그 prefix가 필요하고 Sidekiq은 비권장이다.
   - 클러스터 모드 여부는 **앱 코드 생성과 인프라 선택을 묶어서** 판단해야 한다.
2. **로컬 개발 대체재 두 개가 막혔다.**
   - LocalStack은 2026.03부터 auth token이 필요하고, 무료 플랜은 비상업 용도만 허용한다.
   - MinIO는 저장소가 보관됐고 바이너리를 배포하지 않는다.
   - 그래서 "docker-compose만으로 S3·SQS를 재현"하는 기본 산출물을 만들 수 없다.
   - Pub/Sub 에뮬레이터는 정확히 1회 전달과 DLQ를 재현하지 못한다. 로컬에서는 검증할 수 없는 속성이 생긴다. 이 속성은 배포 후 검증으로 옮겨야 한다.
3. **Terraform으로 끝나지 않는 구성 요소가 많다.**
   - Terraform 불가: Inngest, Trigger.dev, Pusher, Vercel Queues, Supabase Cron·Realtime·Storage 버킷
   - 일부만 가능: Vercel Cron(켜기·끄기만), RTDB 규칙(CLI), Durable Objects(`[충돌]`, wrangler 권장)
   - 서드파티는 provider 인증 토큰을 사람이 처음에 한 번 만들어야 한다.
   - 그래서 산출물은 Terraform 외에 **`vercel.json`, wrangler 설정, SQL 마이그레이션, CLI 배포 명령, 사람 체크리스트**까지 포함해야 한다.
4. **보안 기본값이 꺼져 있거나 앱 코드를 바꿔야 하는 경우가 많다.**
   - `aws_s3_bucket_public_access_block`의 네 인자 기본값이 `false`다.
   - Memorystore Redis의 AUTH와 TLS 기본값이 꺼져 있다. TLS를 켜면 앱에 CA 인증서를 넘겨야 한다.
   - MemoryDB의 자동 백업 기본값이 0이다.
   - Memorystore Valkey와 Redis Cluster의 인증은 IAM 토큰뿐이다(1시간 만료, 새 연결마다 필요). 정적 `REDIS_URL` 계약이 깨지고 앱 코드에 토큰 갱신 연결 팩토리를 생성해야 한다.
   - Vercel Blob `handleUpload`는 인증 검사를 앱이 직접 넣지 않으면 공개 업로드가 된다.
5. **앱 계약 쪽 기본값이 인프라 기본값과 어긋난다.** 생성할 때 양쪽을 같은 값으로 맞춰야 한다.
   - Celery SQS는 기본 리전이 `us-east-1`이고 가시성 타임아웃 기본이 30분이다. SQS 큐 Terraform 기본은 30초다.
   - django-storages는 같은 이름 파일을 기본으로 덮어쓴다.
   - boto3 서명 URL은 IAM 역할 자격 증명이 만료되면 무효가 된다.
   - R2는 presigned POST를 지원하지 않는다.
   - Cloudflare Cron은 UTC 고정에 요일 1~7이다.
   - EventBridge Scheduler는 기본 UTC에 재시도 185회다.
   - Vercel Hobby는 하루 1회를 넘는 cron 식이면 배포가 실패한다.
   - connect-redis는 node-redis만 받는다.
   - 이것들은 Checkov로 잡히지 않는다. 생성 코드 정적 검사(grep·AST)와 배포 후 왕복 시험으로 확인해야 한다.

부가 발견:
- Upstash provider 문서의 `primary_region` 목록에 도쿄가 없다(마지막 게시 2025-08).
- GCS 서명 URL을 키 파일 없이 만드는 경로(signBlob)는 연 문서로 확인하지 못했다.
- EventBridge Scheduler가 HTTPS를 직접 부를 수 있는지 확인하지 못했다.
- 위 세 가지는 생성 전에 다시 확인할 항목이다.
