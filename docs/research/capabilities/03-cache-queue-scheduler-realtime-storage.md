# 구성 요소 능력 표 03 — 캐시, 큐·스트림·작업, 스케줄러, 실시간 연결, 파일 저장소

- 작성일: 2026-10-01
- 형식과 능력 키: [README.md](README.md) (CA.*, QU.*, SC.*, RT.*, FS.*만 사용)
- 요구 쪽 차원: [../dimensions.md](../dimensions.md) — 주로 B1(프로세스 메모리 상태), B2(로컬 디스크), B3(단일 실행), B4(인스턴스 간 조정), A1·A3·A4·A7, C3·C7, E4, F1·F3·F5, G3

## 범위

1. **현재 상태(교체 전 출발점)**: 프로세스 메모리, 앱 프로세스 안 작업 큐, 컨테이너 로컬 디스크, 앱 프로세스 안 스케줄러. 이 능력("인스턴스 간 공유 불가" 등)이 있어야 불일치를 판정할 수 있다.
2. **캐시·키-값**: Redis/Valkey 자체 운영, ElastiCache(노드 기반·서버리스), MemoryDB, Memorystore(Redis Basic·Standard / Valkey / Redis Cluster), Upstash Redis, Vercel KV·Edge Config(Global Config), Cloudflare Workers KV
3. **큐·스트림·작업**: SQS(표준·FIFO), SNS, EventBridge, Pub/Sub, Cloud Tasks, Kafka(MSK·Confluent), Redis Streams, BullMQ, Celery, Sidekiq, Postgres 기반 큐(SKIP LOCKED·pg-boss), Inngest, Trigger.dev, QStash, Vercel Queues
4. **스케줄러**: Kubernetes CronJob, Cloud Scheduler, EventBridge Scheduler, Vercel Cron, Supabase Cron(pg_cron), Cloudflare Cron Triggers, GitHub Actions schedule
5. **실시간**: Socket.IO(어댑터 없음 / Redis 어댑터), Supabase Realtime, Firebase Realtime Database(요약), Pusher, Ably, API Gateway WebSocket, AppSync, Durable Objects
6. **파일 저장소**: S3, GCS, R2, Supabase Storage, Vercel Blob, Firebase Storage, EFS, Filestore, 블록 볼륨(EBS·PD·K8s PV) 다중 연결 제약 (컨테이너 로컬 디스크는 파트 1)

## 출처 규칙

- 모든 출처의 확인일은 2026-10-01이다. 표의 출처 칸에 날짜가 빠진 행도 같은 날 직접 연 페이지다.
- 가격은 서울(ap-northeast-2 / asia-northeast3)을 우선했다.
  - AWS 서울 가격은 AWS Price List API(`https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/<서비스>/current/ap-northeast-2/index.json`)에서 읽었다.
  - GCP 가격 페이지는 WebFetch가 표를 잘라 먹어, 같은 URL을 HTTP로 받아 본문에서 숫자를 뽑았다.
  - 월 환산은 730시간 기준이다.
- 확인하지 못한 값은 `미확인`, 공식 출처 없이 일반 원리로 쓴 값은 `일반 원칙(출처 미확인)`으로 표시했다.
- considerations 파일에서 가져온 URL은 다시 연 것만 썼다. 다시 열지 않은 것은 "재확인 안 함"으로 표시했다.

## 목차

- [0. 요약 비교표](#0-요약-비교표)
- [파트 1. 현재 상태(교체 전 출발점)](#파트-1-현재-상태교체-전-출발점): 프로세스 메모리 · 앱 프로세스 안 작업 큐 · 컨테이너 로컬 디스크 · 앱 프로세스 안 스케줄러
- [파트 2. 캐시·키-값](#파트-2-캐시키-값): Redis/Valkey 자체 운영 · ElastiCache 노드 기반 · ElastiCache Serverless · MemoryDB · Memorystore Redis Basic · Memorystore Redis Standard · Memorystore Valkey · Memorystore Redis Cluster · Upstash Redis · Vercel KV · Vercel Edge Config(Global Config) · Cloudflare Workers KV
- [파트 3. 큐·스트림·작업](#파트-3-큐스트림작업): SQS 표준 · SQS FIFO · SNS · EventBridge · Pub/Sub · Cloud Tasks · MSK · Confluent Cloud · Redis Streams · BullMQ · Celery · Sidekiq · Postgres 큐 · Inngest · Trigger.dev · QStash · Vercel Queues
- [파트 4. 스케줄러](#파트-4-스케줄러): Kubernetes CronJob · Cloud Scheduler · EventBridge Scheduler · Vercel Cron · Supabase Cron · Cloudflare Cron Triggers · GitHub Actions schedule
- [파트 5. 실시간 연결](#파트-5-실시간-연결): Socket.IO(어댑터 없음) · Socket.IO(Redis 어댑터) · Supabase Realtime · Firebase RTDB · Pusher · Ably · API Gateway WebSocket · AppSync · Durable Objects
- [파트 6. 파일 저장소](#파트-6-파일-저장소): S3 · GCS · R2 · Supabase Storage · Vercel Blob · Firebase Storage · EFS · Filestore · 블록 볼륨 제약
- [7. 판정을 뒤집는 발견](#7-판정을-뒤집는-발견)

---

# 0. 요약 비교표

각 칸은 아래 상세 표의 요약이다. 판정에는 상세 표의 조건·한도를 함께 본다.

## 0.1 현재 상태 (교체 전 출발점)

| 구성 요소 | 인스턴스 간 공유 | 재시작·재배포 시 | 단일 실행(B3) | 판정에 쓰는 차원 |
|---|---|---|---|---|
| 프로세스 메모리(MemoryStore, Map, 인메모리 레이트 리밋) | **불가**(같은 호스트 다중 워커끼리도) | 소멸. MemoryStore는 메모리 누수 | 해당 없음 | B1, B4 |
| 앱 프로세스 안 작업 큐(BackgroundTasks, 응답 뒤 Promise) | 불가 | 진행 중 작업 유실 | 해당 없음 | A4, F4 |
| 컨테이너 로컬 디스크(Cloud Run 인메모리 FS, Fargate 임시 20~200 GiB, emptyDir) | **불가** | 소멸 | 해당 없음 | B2, A7 |
| 앱 프로세스 안 스케줄러(node-cron, APScheduler, 웹 안 beat) | 해당 없음 | 프로세스가 없으면 누락 | **인스턴스·워커 수만큼 중복** | B3 |

## 0.2 캐시·키-값

| 구성 요소 | 영속성 | 기본 퇴출 | 페일오버 유실 | 인스턴스 간 공유 | 서울 | 최소 월 고정비 |
|---|---|---|---|---|---|---|
| Redis/Valkey 자체 운영 | RDB 기본(분 단위 손실), AOF 꺼짐 | `noeviction`, maxmemory 0 | 승인된 쓰기 유실 가능 | 가능 | 아무 VM | VM 비용(미확인) |
| ElastiCache 노드 기반 | 없음 + 일일 백업(Valkey 9 이상 durability 선택) | `volatile-lru` | 소량(비동기). primary 재부팅 시 비워짐 | 가능 | 있음 | t4g.micro Valkey 약 $14 / Redis 약 $17.5 |
| ElastiCache Serverless | 다중 AZ 복제 + 일일 백업 | `volatile-lru` **고정** | 미확인 | 가능(TLS) | 있음 | Valkey 약 $7.4 / **Redis OSS 약 $110** |
| MemoryDB | Multi-AZ 트랜잭션 로그 | `noeviction` | **없음** | 가능 | 있음 | t4g.small Valkey 약 $35.8 (Multi-AZ 약 $71.5) |
| Memorystore Redis Basic | 기본 없음(RDB 선택) | `volatile-lru` | 복제 없음 → 전부 | 가능(VPC) | 있음 | 약 $47.45 (1 GiB) |
| Memorystore Redis Standard | 기본 없음(RDB 선택) | `volatile-lru` | 있음(비동기) | 가능(VPC) | 있음 | 약 $83.22 (1 GiB) |
| Memorystore Valkey | RDB 또는 AOF(everysec) | `volatile-lru` | 있음(비동기) | 가능 | 있음 | 약 $28.78 (pico 1노드), HA 약 2배 |
| Memorystore Redis Cluster | RDB 또는 AOF | `volatile-lru` | 있음(비동기) | 가능(클러스터 클라이언트) | 있음 | 약 $29.78 (nano, SLA 없음), 운영 HA 약 $267 |
| Upstash Redis | 항상 켜짐(블록 스토리지) | 꺼짐(가득 차면 쓰기 거부) | 최종 일관성 | 가능(TCP·REST) | **없음(도쿄)** | $0 / $10 / SLA +$200 |
| Vercel KV | 종료(2024-12 Upstash로 이전) | — | — | — | — | — |
| Vercel Edge Config(Global Config) | 영속 + 백업 | 해당 없음 | 전파 최대 10초 | **설정 전용(세션 불가)** | 전역 | $0 고정 |
| Cloudflare Workers KV | 영속 | 해당 없음 | 최종 일관성 60초 이상, 같은 키 쓰기 1회/초 | 읽기 위주만 | 전역 | $0 / Paid $5 |

## 0.3 큐·스트림·작업

| 구성 요소 | 전달 보장 | 순서 | 중복 제거 기간 | 최대 메시지 | 최대 보존 | 서울 | 최소 월 고정비 |
|---|---|---|---|---|---|---|---|
| SQS 표준 | 최소 1회 | 최선 노력 | 없음 | 1 MiB | 14일(기본 4일) | 있음 | $0 (100만 요청 무료, $0.40/백만) |
| SQS FIFO | 조건부 정확히 1회 | 그룹 안 엄격 | 5분 | 1 MiB | 14일 | 있음 | $0 ($0.50/백만) |
| SNS | 재시도 후 버림(DLQ 선택). FIFO+SQS FIFO는 조건부 정확히 1회 | FIFO만 | FIFO 5분 | 256 KiB | 보존 없음(FIFO 아카이브) | 있음 | $0 |
| EventBridge | 재시도 후 버림(DLQ 선택) | 미확인 | 새 버스 300초 | 미확인(64KB 단위 과금) | 아카이브 1~365일 | 있음 | $0 ($1/백만) |
| Pub/Sub | 최소 1회(정확히 1회: pull + 같은 리전) | 순서 키 | 정확히 1회 구독만 | 10 MB | 31일(기본 7일) | 있음 | $0 (10 GiB 무료, $40/TiB) |
| Cloud Tasks | 최소 1회 | 미확인 | 작업 이름 24시간 | 1 MiB | 31일 | 있음 | $0 (100만 무료, $0.40/백만) |
| Kafka — MSK | 최소 1회(EOS는 Kafka 안에서) | 파티션 안 | 멱등 프로듀서 | Serverless 8 MiB | 설정(무제한 가능) | 있음 | t3.small 3대 약 $125 / Serverless 약 $672 |
| Kafka — Confluent Cloud | 같음 | 파티션 안 | 멱등 프로듀서 | 미확인 | Basic 5 TB | 미확인 | Basic $0부터 |
| Redis Streams | 최소 1회(XACK) | 스트림 안 | 없음 | 512 MB(값) | 메모리·MAXLEN | Redis를 따름 | Redis 비용 |
| BullMQ | 최소 1회(stalled 재처리) | 미확인 | jobId(제거 전까지) | Redis 한도 | Redis 메모리 | Redis를 따름 | Redis 비용(`noeviction` 필수) |
| Celery | **기본 최대 1회**(acks_late면 최소 1회) | 미확인 | 없음 | 브로커 | 브로커 | 브로커를 따름 | 브로커 비용 |
| Sidekiq OSS | **크래시 시 유실**(Pro super_fetch로 회수) | 미확인 | 없음 | Redis 한도 | Dead set 6개월 | Redis를 따름 | Redis 비용 |
| Postgres 큐(SKIP LOCKED, pg-boss) | 업무 트랜잭션과 원자적 enqueue | ORDER BY(엄격 아님) | 유니크 제약 / singleton | DB 행 | DB 용량 | DB를 따름 | **$0 추가** |
| Inngest | 단계 재시도(기본 4회) | 미확인 | 24시간 | 256 KiB(Free) / 3 MiB | 실행 30~90일 | 미확인 | $0 (동시 5) / Pro $99 |
| Trigger.dev | 미확인 | 미확인 | 미확인 | 3 MB | TTL 14일 | 미확인 | $0($5 크레딧) / $10 / $50 |
| QStash | 최소 1회 | 미확인 | 10분 | 1 MB(Free) / 10 MB | DLQ 3~7일 | **없음(EU·US)** | $0 (하루 1,000) |
| Vercel Queues(베타) | 최소 1회(3 AZ) | 대략 순서, FIFO 아님 | 메시지 TTL 동안(최대 7일) | 100 MB | 7일(기본 24시간) | 있음(icn1) | $0 (Hobby 100만 operation) |

## 0.4 스케줄러

| 구성 요소 | 최소 주기 | 중복 가능 | 누락 가능 | 재시도 | 대상·최대 실행 | 서울 | 비용 |
|---|---|---|---|---|---|---|---|
| 앱 프로세스 안 스케줄러 | 제한 없음 | **예(인스턴스 수만큼)** | 예(scale-to-zero, 크래시) | 없음 | 같은 프로세스 | — | $0 |
| Kubernetes CronJob | 1분 | 예(드물게 2회, 기본 `Allow`로 겹침) | 예(드물게 0회, 100회 누락 시 중단) | Job backoffLimit | 컨테이너, 제한 없음 | 클러스터 | 클러스터 비용 |
| Cloud Scheduler | 1분(문구 미확인) | 예(드묾) | 미확인 | 설정 가능 | HTTP·Pub/Sub, HTTP 30분 | 있음 | 3잡 무료, $0.10/잡/월 ⚠️근거없음 |
| EventBridge Scheduler | 1분(60초 정밀도) | 예(최소 1회) | DST 봄 전환 건너뜀 | 설정 가능 + DLQ | 270개 AWS 서비스, 페이로드 256 KB | 있음 | 월 1,400만 무료 |
| Vercel Cron | **Hobby 하루 1회(±59분)** / Pro 1분 | 예 | **예(최선 노력)** | **없음** | 함수 maxDuration | 함수 리전 | 포함 |
| Supabase Cron(pg_cron) | 1초 | 아니오(작업당 1개, 다음은 대기) | 미확인 | 없음(미확인) | SQL·함수·HTTP(pg_net), 10분 이하 권장 | 있음 | 포함 |
| Cloudflare Cron Triggers | 1분 | 미확인 | 미확인 | 미확인 | Worker, CPU Free 10ms / Paid 30초~15분 | 전역 | Free / $5 |
| GitHub Actions schedule | 5분 | 미확인 | **예(고부하 시 드롭)**, 60일 비활성 시 정지 | 없음 | 러너 스크립트 | — | 공개 무료 |

## 0.5 실시간 연결

| 구성 요소 | 동시 연결 한도 | 인스턴스 간 전파 | 메시지 크기 | 연결 지속 한도 | 서울 | 최소 월 비용 |
|---|---|---|---|---|---|---|
| Socket.IO 어댑터 없음 | 서버 자원(미확인) | **같은 프로세스만** | — | 플랫폼을 따름 | — | $0 |
| Socket.IO Redis 어댑터 | 서버 수 × 서버당 | Redis pub/sub(끊기면 유실) / Streams(유실 없음) | — | 플랫폼을 따름(+스티키 세션) | Redis를 따름 | Redis 비용 |
| Supabase Realtime | **Free 200 / Pro 500** / 상한 해제 10,000 | 관리형 | Broadcast 256 KB(Free) / 3 MB | 미확인 | 있음 | 플랜 포함 |
| Firebase RTDB | DB당 200,000 | 관리형 | 쓰기 16 MB(SDK) | 미확인 | **없음(싱가포르)** | 미확인 |
| Pusher Channels | 100(무료) / 500 / 2,000 … | 관리형(HTTP trigger) | **10 KB** | 미확인 | **없음(도쿄)** | $0 / $49 |
| Ably | 200(무료) / 10,000 / 50,000 | 관리형, 채널 순서 보장 | 64 KiB / 256 KiB | 상태 TTL 2분 | 미확인 | $0 / $29 + 사용량 |
| API Gateway WebSocket | 상한 없음(신규 500/초) | **브로드캐스트 없음**(연결 ID별 POST) | 프레임 32 KB, 메시지 128 KB | **2시간, 유휴 10분** | 있음 | $0 ($1.14/백만 메시지) |
| AppSync | 미확인(연결 2,000/초) | 관리형 | 구독 240 KB / Event 1.2 MB | 미확인 | 있음 | $0 ($2/백만) |
| Durable Objects | 객체당 미확인(1,000 요청/초 소프트) | 객체(방) 안 | 수신 32 MiB | Hibernation | 보장 없음(힌트) | Free / $5 |

## 0.6 파일 저장소

| 구성 요소 | 내구성·복제 범위 | 일관성 | 인스턴스 간 공유 | 최대 객체·업로드 | 서울 | 최소 월 고정비 |
|---|---|---|---|---|---|---|
| 컨테이너 로컬 디스크 | 없음 | 로컬 POSIX | **불가** | Cloud Run=메모리, Fargate 20~200 GiB | — | $0 |
| Amazon S3 | 11 nines, 3 AZ 이상 | 강한 일관성 | 가능 | **약 50 TB**, PUT 5 GB, 서명 URL 7일 | 있음 | $0 ($0.025/GB, 송신 $0.126/GB) |
| GCS | 11 nines, 리전 2존 이상 | 강한 일관성 | 가능 | 5 TiB, 같은 이름 쓰기 1회/초 | 있음 | $0 (서울 저장 단가 미확인) |
| Cloudflare R2 | 11 nines | 강한 일관성(캐시 예외) | 가능 | 5 TiB, 단일 5 GiB | 힌트만(apac) | $0 ($0.015/GB, **송신 무료**) |
| Supabase Storage | 미확인 | 미확인(동시 업로드 규칙 있음) | 가능 | **Free 50 MB** / Pro 500 GB | 있음 | 플랜 포함(Pro 100 GB) |
| Vercel Blob | 11 nines(S3 기반) | CDN 전파 최대 60초 | 가능 | 5 TB, **서버 업로드 4.5 MB** | 있음(icn1) | $0 (Hobby 1 GB) |
| Firebase Storage | GCS를 따름 | 강한 일관성 | 가능 | 5 TiB | 미확인 | **Blaze 필수** |
| Amazon EFS | Regional 다중 AZ / One Zone | 미확인(NFS) | **가능(NFS)** | 미확인 | 있음 | $0 ($0.33/GB, S3의 13배) |
| Google Filestore | 존 / 리전 티어 | 미확인(NFS) | 가능(NFS) | **최소 1 TiB** | 있음 | 1 TiB 약 $164(미국 리전 계산) |
| 블록 볼륨(EBS·PD·RWO) | 단일 AZ | 다중 쓰기 시 손상 | **기본 1대**(io1/io2·Hyperdisk 제한적) | — | 있음 | 미확인 |


---

# 파트 1. 현재 상태(교체 전 출발점)

## 프로세스 메모리 — 세션 MemoryStore, 인메모리 캐시(전역 Map·lru-cache·LocMemCache·SimpleCache), 인메모리 레이트 리밋 (현재 상태)
- 계열: 캐시 (교체 전 출발점)
- 서울 리전: 해당 없음 (앱 프로세스 안에 있음. 지역은 컴퓨트를 따름)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CA.persistence | 없음. 프로세스가 재시작하거나 재배포되면 사라짐 | 세션, 캐시, 카운터 모두 해당 | https://express-rate-limit.mintlify.app/reference/stores · "will be inconsistent across reboots or in deployments with multiple process or servers" · 2026-10-01 ⚠️출처확인필요 |
| CA.eviction | express-session MemoryStore: 정리 없음(메모리 누수). lru-cache: `max`/`maxSize`/`ttl` 중 하나가 필수. 전역 Map: 상한 없음 | 상한을 두지 않으면 OOM으로 이어짐 | https://github.com/expressjs/session · "It will leak memory under most conditions" · 2026-10-01 / https://github.com/isaacs/node-lru-cache · "At least one of 'max', 'ttl', or 'maxSize' is required, to prevent unsafe unbounded storage." · 2026-10-01 ⚠️출처확인필요 |
| CA.consistency | 복제 없음. 인스턴스마다 값이 따로 놀아서 일관성이 없음 | — | https://docs.djangoproject.com/en/stable/topics/cache/ · "each process will have its own private cache instance, which means no cross-process caching is possible" · 2026-10-01 |
| CA.shared_state | **불가.** 인스턴스 2개 이상에서 세션·락·레이트 리밋 저장소로 쓸 수 없음 (B1 불일치의 근거) | gunicorn `-w N`처럼 같은 호스트의 다중 워커에서도 공유되지 않음 | https://github.com/expressjs/session · "does not scale past a single process, and is meant for debugging and developing" · 2026-10-01 / https://express-rate-limit.mintlify.app/reference/stores · "This one does not synchronize it's state across instances." · 2026-10-01 ⚠️출처확인필요 |
| CA.pubsub | 없음 (프로세스 안 EventEmitter뿐, 인스턴스 간 전파 불가) | — | https://docs.djangoproject.com/en/stable/topics/cache/ · "no cross-process caching is possible" · 2026-10-01 |
| CA.availability | 프로세스와 생명을 같이함. HA 없음 | — | https://github.com/expressjs/session · "purposely not designed for a production environment" · 2026-10-01 ⚠️출처확인필요 |
| CA.connections | 해당 없음 (네트워크 연결 없음) | — | 해당 없음 |
| CA.limits | 프로세스 힙 크기가 상한. Flask-Caching SimpleCache는 로컬 dict라 스레드 안전하지만 프로세스 사이 공유는 안 됨 | — | https://flask-caching.readthedocs.io/en/latest/backends/ · "Uses a local python dictionary for caching. All operations are protected by a lock, making it thread-safe." · 2026-10-01 ⚠️출처확인필요 |
| CA.regions / CA.cost_floor | 컴퓨트를 따름 / 추가 비용 0 | 인스턴스 메모리를 소비함 | 해당 없음 |

### 비용 구조
추가 고정비는 0이다. 대신 인스턴스 메모리를 쓰므로 캐시가 커지면 인스턴스 크기가 커진다. Django는 따로 지정하지 않으면 LocMemCache를 기본 캐시로 쓴다. 출처: https://docs.djangoproject.com/en/stable/topics/cache/ · "This is the default cache if another is not specified in your settings file." · 2026-10-01

### 교체 계열 정보
- Node 세션: `express-session` MemoryStore를 `connect-redis`로 바꾼다. 클라이언트는 `redis`(node-redis)이고, 바꿀 지점은 `session({ store: new RedisStore({ client, prefix }) })` 한 곳이다. 기본 TTL은 86400초이고, 쿠키에 만료가 있으면 그 값을 따른다. 출처: https://github.com/tj/connect-redis · "sessions expire after 86400 seconds (one day)" · 2026-10-01 ⚠️출처확인필요
- Node 레이트 리밋: `express-rate-limit` 기본 MemoryStore를 `rate-limit-redis`로 바꾼다. 출처: https://express-rate-limit.mintlify.app/reference/stores · "A Redis-backed store, more suitable for large or demanding deployments." · 2026-10-01 ⚠️출처확인필요
- Django: `CACHES.BACKEND`를 `django.core.cache.backends.redis.RedisCache`로, `LOCATION`을 Redis URL로 바꾸고 redis-py(+hiredis)를 설치한다. 출처: https://docs.djangoproject.com/en/stable/topics/cache/ · "redis-py is the binding supported natively by Django" · 2026-10-01
- Flask: `CACHE_TYPE`을 SimpleCache에서 RedisCache로 바꾸고 `CACHE_REDIS_URL`을 넣는다. 세션은 Flask-Session의 Redis 백엔드를 쓴다(Flask-Session 문서는 미확인).
- 전역 Map·lru-cache: 공유가 필요한 키만 Redis로 옮긴다. 인스턴스별 L1 캐시로 남길 경우 무효화를 pub/sub로 전파해야 한다(B4).

### 함정
- 같은 VM 안의 다중 워커(gunicorn `-w 4`, PM2 cluster)만으로도 B1 불일치가 생긴다. 인스턴스 수가 1이라고 안전하지 않다.
- MemoryStore는 정리 로직이 없어 누수가 생기므로 단일 인스턴스에서도 운영용으로 부적합하다.
- 인메모리 레이트 리밋은 인스턴스 N개면 실제 한도가 N배가 된다.

---

## 앱 프로세스 안 작업 큐 — FastAPI BackgroundTasks, 응답 뒤 실행되는 Promise·setTimeout, 인메모리 큐 (현재 상태)
- 계열: 큐 (교체 전 출발점)
- 서울 리전: 해당 없음 (컴퓨트를 따름)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| QU.delivery | 보장 없음. 응답 뒤 같은 프로세스에서 실행되므로 프로세스가 죽으면 작업이 사라짐 | "재시작 시 유실"이라고 명시한 문구는 미확인. 같은 프로세스에서 실행된다는 문서 내용에서 유도한 값임 | https://fastapi.tiangolo.com/tutorial/background-tasks/ · "you don't necessarily need it to be run by the same process" (Celery 권고 문맥) · 2026-10-01 |
| QU.ordering | 보장 없음 | — | 미확인 ⚠️근거없음 |
| QU.dedup | 없음 | — | 미확인 ⚠️근거없음 |
| QU.retention | 없음 (프로세스 메모리에만 있음). 메시지 크기 한도는 프로세스 메모리 | — | 미확인 (명시 문구 없음) ⚠️근거없음 |
| QU.retry_dlq | 없음 (직접 구현해야 함) | — | 미확인 ⚠️근거없음 |
| QU.throughput | 웹 요청과 같은 CPU·이벤트 루프를 나눠 씀 | 무거운 계산은 별도 도구 권고 | https://fastapi.tiangolo.com/tutorial/background-tasks/ · "If you need to perform heavy background computation … you might benefit from using other bigger tools like Celery." · 2026-10-01 |
| QU.consumer_scaling | 불가. 작업자와 웹이 한 몸이라 큐 길이로 확장할 수 없음. 다중 서버 분산이 안 됨 | — | https://fastapi.tiangolo.com/tutorial/background-tasks/ · "they allow you to run background tasks in multiple processes, and especially, in multiple servers" (외부 큐 쪽 설명) · 2026-10-01 |
| QU.availability / QU.regions / QU.cost_floor | 프로세스와 같음 / 컴퓨트를 따름 / 0 | — | 해당 없음 |

### 비용 구조
추가 비용은 0이다. 다만 요청 기반 과금 플랫폼(Cloud Run 요청 기반 과금, 서버리스 함수)에서는 응답 뒤에 CPU가 주어지지 않을 수 있다. 이는 컴퓨트 표 CP.cpu_outside_request(A4)와 맞춰 봐야 한다.

### 교체 계열 정보
- Python: BackgroundTasks를 Celery(브로커 Redis/RabbitMQ), RQ, Dramatiq, 또는 SQS/Cloud Tasks로 바꾼다. 핸들러는 `enqueue(job, payload)`만 하고 별도 워커 프로세스(A1에 워커 추가)가 처리한다. 작업은 멱등이어야 한다(최소 1회 전달).
- Node: 응답 뒤 Promise와 setTimeout을 BullMQ(Redis), SQS, QStash, Inngest로 바꾼다. 작업 인자는 직렬화 가능해야 하고, 클로저로 잡은 메모리 객체에 의존하면 안 된다.
- 바뀌는 점: 작업 인자 직렬화, 재시도와 멱등키, 워커 엔트리포인트 추가, 실패 큐 모니터링.

### 함정
- FastAPI 문서는 "작은 작업(메일 발송)은 BackgroundTasks로 충분"하다고 적고 있다. 하지만 배포 중 종료 신호(F4)나 scale-in 때 진행 중인 작업이 유실되는 문제는 별개로 판정해야 한다.
- await 하지 않은 Promise는 서버리스에서 응답 직후 실행이 동결되거나 중단될 수 있다(플랫폼별로 컴퓨트 표 참조).

---

## 컨테이너 로컬 디스크 — Cloud Run 인메모리 FS, ECS Fargate 임시 스토리지, Kubernetes emptyDir (현재 상태)
- 계열: 파일 저장소 (교체 전 출발점)
- 서울 리전: 해당 없음 (컴퓨트를 따름)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| FS.durability | **없음.** Cloud Run은 인스턴스가 멈추면 사라짐. Fargate는 태스크 단위 임시 스토리지. emptyDir은 Pod가 노드에서 제거되면 영구 삭제(컨테이너 크래시로는 지워지지 않음) | 재배포·축소·노드 교체 때마다 유실 | https://docs.cloud.google.com/run/docs/container-contract · "Data written to the file system doesn't persist when the instance stops." / https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-task-storage.html · "each Amazon ECS task hosted on Linux containers on AWS Fargate receives the following ephemeral storage" / https://kubernetes.io/docs/concepts/storage/volumes/ · "When a Pod is removed from a node for any reason, the data in the emptyDir is deleted permanently" |
| FS.consistency | 같은 인스턴스 안에서는 POSIX 파일 시스템 | 다른 인스턴스는 볼 수 없음 | (아래 FS.shared_access 근거와 같음) |
| FS.shared_access | **불가.** 인스턴스·태스크·Pod마다 따로. Fargate는 같은 태스크 안 컨테이너끼리만 공유 | B2 불일치의 근거 | Fargate 문서 · "This can be mounted and shared among containers that use the volumes, mountPoints, and volumesFrom parameters in the task definition" (태스크 안 공유만 기술) |
| FS.object_limits | Cloud Run: 쓰기가 인스턴스 메모리를 소비하고, 다 쓰면 인스턴스가 죽음. Fargate: 기본 20 GiB, 최대 200 GiB(이미지 크기 포함) | 업로드 크기는 플랫폼 요청 본문 한도(CP.request_size)가 먼저 걸림 | Cloud Run 문서 · "It is an in-memory file system, so writing to it uses the instance's memory." · "you can potentially use up all the memory allocated to your instance" / Fargate 문서 · "receive a minimum of 20 GiB of ephemeral storage … up to a maximum of 200 GiB" |
| FS.versioning_lifecycle | 없음 | — | 해당 없음 ⚠️근거없음 |
| FS.delivery | 앱이 직접 서빙(`express.static('uploads')` 등). CDN 연동 없음 | — | 해당 없음 ⚠️근거없음 |
| FS.regions / FS.cost_floor | 컴퓨트를 따름 / 추가비 $0 (Cloud Run은 메모리로 과금됨) | — | 해당 없음 |

### 비용 구조
추가 비용은 없습니다. Cloud Run은 디스크가 아니라 메모리를 쓰므로 메모리 등급을 올려야 할 수 있습니다.

### 교체 계열 정보
- 업로드: `multer.diskStorage` / Django `FileSystemStorage` / Flask `save()` → (1) 서명 URL로 브라우저가 객체 저장소에 직접 업로드(S3 `PutObject` presign, GCS V4 signed URL, R2 S3 호환, Vercel Blob client upload, Supabase TUS), 또는 (2) `multer-s3`·`django-storages`로 서버 경유 업로드(본문 한도 확인).
- 서빙: `express.static('uploads')` → 공개 버킷 + CDN, 또는 비공개 버킷 + 서명 GET URL.
- DB 컬럼: 로컬 경로 → 객체 키(버킷 이름은 설정으로). 기존 파일은 이전 스크립트로 업로드.
- SQLite 파일도 이 범주(B2)이며, 처방은 파일 저장소가 아니라 관계형 DB 교체(01 파일)입니다.

### 함정
- 인스턴스가 1대여도 재배포마다 파일이 사라집니다.
- Cloud Run에서 큰 파일을 디스크에 쓰면 메모리 부족으로 인스턴스가 죽습니다.

---

## 앱 프로세스 안 스케줄러 — node-cron, APScheduler, 웹 프로세스 안 celery beat (현재 상태)
- 계열: 스케줄러 (교체 전 출발점)
- 서울 리전: 해당 없음

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| SC.frequency | 라이브러리 제한 없음(초 단위 가능) | 프로세스가 살아 있을 때만 | 해당 없음 ⚠️근거없음 |
| SC.semantics | **인스턴스·워커 수만큼 중복 실행.** APScheduler는 잡 스토어를 여러 프로세스가 공유하면 중복 실행이나 누락이 생김. celery beat는 반드시 하나만. node-cron 4는 `distributed: true`(기본은 환경 변수 플래그, HA는 Redis 코디네이터)와 `noOverlap`을 제공하지만 상태를 영속하지 않아 크래시 후 정확히 1회는 보장하지 않음. scale-to-zero면 프로세스가 없어 **누락** | 재시도 없음 | https://apscheduler.readthedocs.io/en/3.x/faq.html · "Sharing a persistent job store among two or more processes will lead to incorrect scheduler behavior like duplicate execution or the scheduler missing jobs" / https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html · "You have to ensure only a single scheduler is running for a schedule at a time, otherwise you'd end up with duplicate tasks." / https://github.com/node-cron/node-cron · "`distributed: true` ensures only one instance executes each scheduled fire. Out of the box it uses an env-var flag; for high availability, plug in a Redis coordinator" · "node-cron coordinates but does not persist state to a database" ⚠️출처확인필요 |
| SC.target | 같은 프로세스의 함수. 실행 시간 제한 없음(대신 웹 요청과 CPU를 나눠 씀) | — | 해당 없음 ⚠️근거없음 |
| SC.cost_floor | $0 | — | 해당 없음 ⚠️근거없음 |

### 비용 구조
추가 비용은 없습니다. 다만 크론 때문에 최소 인스턴스를 1 이상으로 유지하면 그만큼 고정비가 생깁니다.

### 교체 계열 정보
- node-cron / APScheduler → 외부 스케줄러(Cloud Scheduler, EventBridge Scheduler, Kubernetes CronJob, Vercel Cron) + 인증된 HTTP 엔드포인트(공유 비밀 헤더 `CRON_SECRET`, 또는 OIDC 토큰 검증) + 중복 방지.
- 중복 방지 수단: 실행 창(예: `job_name + 예정 시각`)을 유니크 키로 DB에 기록, Postgres `pg_try_advisory_lock`, Redis `SET key NX PX`. 외부 스케줄러는 모두 최소 1회이므로 이 단계가 필수입니다.
- celery beat → 별도 프로세스 1개(replicas 1)로 분리하거나 외부 스케줄러로 대체.
- 작업 본문이 길면 엔드포인트는 큐에 넣기만 하고 워커가 처리(스케줄러 HTTP 제한 시간 회피).

### 함정
- gunicorn `-w 4` 하나만으로 하루 1회 메일이 4번 나갑니다(인스턴스 1대여도 발생).
- node-cron `distributed`의 기본 모드는 환경 변수로 실행 담당 인스턴스를 지정하는 방식이라 그 인스턴스가 죽으면 누락됩니다.

---

# 파트 2. 캐시·키-값

## Redis / Valkey — 자체 운영 (VM·컨테이너, OSS)
- 계열: 캐시
- 서울 리전: 해당 없음 (어느 VM에서든 실행 가능)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CA.persistence | 기본은 RDB 스냅샷만 켜짐(3600초/1변경, 300초/100변경, 60초/10000변경). AOF는 꺼져 있음(`appendonly no`). RDB만 쓰면 최근 몇 분을 잃을 수 있음. AOF를 켜면 기본 `everysec`로 최대 1초 손실 | 컨테이너 임시 디스크에 dump.rdb를 쓰면 재시작 시 사라짐 | https://raw.githubusercontent.com/redis/redis/unstable/redis.conf · "Unless specified otherwise, by default Redis will save the DB: After 3600 seconds … After 300 seconds … After 60 seconds" / "appendonly no" · 2026-10-01 / https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/ · "you should be prepared to lose the latest minutes of data" · "you may lose 1 second of data" · 2026-10-01 / https://valkey.io/topics/persistence/ · "By default Valkey saves snapshots of the dataset on disk" · 2026-10-01 ⚠️출처확인필요 |
| CA.eviction | 기본 `maxmemory` 0(64비트에서 무제한), 기본 정책 `noeviction`. 메모리가 차면 쓰기 명령이 오류를 냄 | `volatile-*`는 TTL 키가 없으면 noeviction처럼 동작 | https://redis.io/docs/latest/develop/reference/eviction/ · "Set maxmemory to zero … This is the default behavior for 64-bit systems" · "noeviction: Keys are not evicted but the server will return an error" · 2026-10-01 / https://raw.githubusercontent.com/redis/redis/unstable/redis.conf · "The default is: # maxmemory-policy noeviction" · 2026-10-01 |
| CA.consistency | 비동기 복제. WAIT를 써도 CP 시스템이 아니며 페일오버 때 승인된 쓰기를 잃을 수 있음 | `min-replicas-to-write`로 손실 창을 줄일 수 있음 | https://redis.io/docs/latest/operate/oss_and_stack/management/replication/ · "Redis uses by default asynchronous replication" · "acknowledged writes can still be lost during a failover" · 2026-10-01 |
| CA.shared_state | 가능 (세션, 락, 레이트 리밋). 원자적 INCR 지원 | 락은 페일오버 손실에 유의 | https://redis.io/docs/latest/develop/data-types/strings/ · "multiple clients issuing INCR against the same key will never enter into a race condition" · 2026-10-01 |
| CA.pubsub | Pub/Sub는 최대 1회 전달(끊기면 유실). Streams는 영속이며 최소 1회 전달 지원. 7.0부터 샤드 Pub/Sub | — | https://redis.io/docs/latest/develop/pubsub/ · "Redis' Pub/Sub exhibits at-most-once message delivery semantics" · "Messages in streams are persisted, and support both at-most-once as well as at-least-once" · 2026-10-01 |
| CA.availability | 직접 구성해야 함. Sentinel은 최소 3개를 독립 장애 영역에 두어야 함. 승인된 쓰기 보존은 보장하지 않음 | 영속성을 끈 마스터가 자동 재시작하면 복제본까지 비워질 수 있음 | https://redis.io/docs/latest/operate/oss_and_stack/management/sentinel/ · "You need at least three Sentinel instances for a robust deployment." · "does not guarantee that acknowledged writes are retained during failures" · 2026-10-01 / https://redis.io/docs/latest/operate/oss_and_stack/management/replication/ · "the replica will be emptied as well" · 2026-10-01 |
| CA.connections | 기본 `maxclients` 10,000 (OS fd 한도에 따라 줄어듦). TCP 연결만 가능하고 HTTP 엔드포인트 없음 | Pub/Sub 클라이언트 출력 버퍼 하드 32MB, 소프트 8MB/60초 | https://redis.io/docs/latest/develop/reference/clients/ · "The default is 10,000 clients." · "Pub/Sub clients have a default hard limit of 32 megabytes" · 2026-10-01 |
| CA.limits | 문자열 값 최대 512MB. 쿼리 버퍼 1GB | 단일 스레드라 느린 명령에 주의 | https://redis.io/docs/latest/develop/data-types/strings/ · "A value can't be bigger than 512 MB." · 2026-10-01 / https://redis.io/docs/latest/develop/reference/clients/ · "reaches 1 GB" · 2026-10-01 |
| CA.regions / CA.cost_floor | 아무 VM / VM 비용만 듦(서울 VM 최소가는 이 조사 범위에서 미확인. 컴퓨트 표 참조) | — | 미확인 |

### 비용 구조
라이선스 비용은 없다. 비용은 VM 또는 컨테이너 1대 이상과 디스크다. HA를 하려면 Redis 2대 이상과 Sentinel 3개가 필요하다. 운영 부담(패치, 백업 크론, 모니터링)이 숨은 비용이다.

### 교체 계열 정보
- 대표 클라이언트: Node `redis`(node-redis)와 `ioredis`, Python `redis-py`, Java `Jedis`(동기)와 `Lettuce`(비동기·리액티브), Go `go-redis`. 공식 예제에 나오는 클라이언트다. 출처: https://redis.io/docs/latest/develop/data-types/strings/ · "JavaScript (Node.js): node-redis client … Python: redis-py client … Go: go-redis client" · 2026-10-01
- Redis에서 Valkey로는 프로토콜이 호환되어 클라이언트를 그대로 쓴다. 자체 운영에서 관리형으로 옮길 때는 TLS(서버리스는 TLS 필수)와 클러스터 모드(키 해시 슬롯, 다중 키 명령 제약)를 확인해야 한다.

### 함정
- 기본값이 `noeviction`이라 캐시 용도로 쓰면 메모리가 찼을 때 쓰기 오류가 난다. 반대로 큐·세션 용도에 `allkeys-lru`를 쓰면 데이터가 조용히 사라진다. 캐시와 큐·세션 인스턴스는 분리하는 것이 좋다.
- 컨테이너로 띄우고 볼륨이 없으면 기본 RDB가 있어도 재시작 시 데이터가 0이 된다.
- WAIT를 쓰더라도 강한 일관성은 아니다. 금전성 데이터의 원장으로 쓰면 안 된다.

---

## Redis / Valkey — Amazon ElastiCache, 노드 기반 (Valkey / Redis OSS)
- 계열: 캐시
- 서울 리전: 있음 (https://docs.aws.amazon.com/general/latest/gr/elasticache-service.html · "Asia Pacific (Seoul) | ap-northeast-2 | elasticache.ap-northeast-2.amazonaws.com" · 2026-10-01)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CA.persistence | 기본은 영속성 없음. AOF는 꺼져 있고 수정할 수 없음(2.8.22 이후 미지원). 자동 백업은 하루 1회이고 보존 최대 35일, 0이면 비활성. **Valkey 9.0 이상은 생성 시 durability(Multi-AZ 트랜잭션 로그)를 선택할 수 있음** | durability는 클러스터 모드 활성, Multi-AZ, 지원 인스턴스 계열(R/M/C 그래비톤)에서만 가능. 기존 클러스터에는 켤 수 없음 | https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/ParameterGroups.Engine.html · "appendonly | Default: off Modifiable: No" · 2026-10-01 / https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/backups-automatic.html · "ElastiCache creates a backup of the cache on a daily basis" · "The maximum backup retention limit is 35 days." · 2026-10-01 / https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/Durability.Limitations.html · "Durability for ElastiCache is supported on Valkey 9.0 or later." · "You cannot enable durability on an existing non-durable cluster." · 2026-10-01 |
| CA.eviction | 기본 파라미터 그룹은 `volatile-lru`(TTL 있는 키만 퇴출). 노드 메모리의 25%를 예약 | 커스텀 파라미터 그룹에서 변경 가능 | https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/ParameterGroups.Engine.html · "maxmemory-policy … Default: volatile-lru" · "reserved-memory-percent | Default: 25" · 2026-10-01 |
| CA.consistency | 비동기 복제라 페일오버 때 소량 유실 가능. durability 동기 쓰기는 무손실, 비동기 쓰기는 최대 10초 손실. **primary를 재부팅하면 데이터가 비워지고 복제본도 따라 비워짐** | — | https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/AutoFailover.html · "Valkey and Redis OSS replication is asynchronous. Therefore, when a primary node fails over to a replica, a small amount of data might be lost" · "When the primary is rebooted, it's cleared of data when it comes back online." · 2026-10-01 / https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/durability.html · "the risk of losing up to 10 seconds of uncommitted data during a failure" · 2026-10-01 |
| CA.shared_state | 가능 (세션, 락, 레이트 리밋) | 페일오버 유실을 감안해야 함 | https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/WhatIs.corecomponents.html · "your application will cache frequently accessed data" · 2026-10-01 |
| CA.pubsub | Pub/Sub와 Streams 지원(엔진 기능). Pub/Sub 출력 버퍼 기본값이 있음 | — | https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/RedisConfiguration.html · "pubsub 32mb 8mb 60" (서버리스 표. 노드 기반은 파라미터 그룹) · 2026-10-01 |
| CA.availability | Multi-AZ 자동 페일오버는 복제본 1개 이상 필요. 쓰기 재개는 보통 수 초. 복제본이 없으면 새 primary가 빈 상태로 시작 | 클러스터 모드 활성이면 Multi-AZ 기본. Redis OSS의 Multi-AZ와 AOF는 함께 쓸 수 없음 | https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/AutoFailover.html · "Writes can resume within seconds." · "If no replicas exist, the new primary starts empty and data is lost" · 2026-10-01 |
| CA.connections | maxclients 65,000. **t4g.micro와 t3.micro는 20,000**, t3.small·medium은 46,000. 수정 불가. TCP(VPC 안) | — | https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/ParameterGroups.Engine.html · "Default: 65000 … t4g.micro Default: 20000 … Modifiable: No" · 2026-10-01 |
| CA.limits | 샤드당 노드 6(primary 1 + 복제본 5), 클러스터 모드 클러스터당 노드 90, 리전당 노드 300 | 값 크기는 엔진 한도(512MB)를 따름 | https://docs.aws.amazon.com/general/latest/gr/elasticache-service.html · "Nodes per shard | Each supported Region: 6 | No" · 2026-10-01 |
| CA.regions / CA.cost_floor | 서울 있음 / cache.t4g.micro Valkey $0.0192/시간이면 약 $14.0/월, Redis OSS $0.024/시간이면 약 $17.5/월(1노드, HA 없음). Multi-AZ 2노드 Valkey는 약 $28/월 | 서울(APN2) 온디맨드 | AWS Price List API (Bash curl) https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonElastiCache/current/ap-northeast-2/index.json · "$0.0192 per T4G Micro Cache node-hour (or partial hour) running Valkey" · "$0.024 per T4G Micro Cache node-hour … running Redis" · 2026-10-01 |

### 비용 구조
- 고정비는 노드 시간 × 노드 수다. Valkey는 노드 기반에서 다른 엔진보다 20% 싸다. 출처: https://aws.amazon.com/elasticache/pricing/ · "20% lower price on ElastiCache node-based as compared to other supported engines" · 2026-10-01
- 백업 저장은 서울 $0.085/GB-월(Price List 같은 URL · "$0.085 per GB-month of snapshot storage for Valkey" · 2026-10-01).
- 과금 함정: 구버전 Redis OSS에는 Extended Support 요금이 붙는다. 서울 t4g.micro 기준 1~2년차 +$0.019/시간, 3년차 +$0.038/시간(Price List · "ExtendedSupportYr1_Yr2-NodeUsage:cache.t4g.micro" · 2026-10-01).

### 교체 계열 정보
자체 운영 Redis와 같은 클라이언트를 쓴다. 클러스터 모드 활성이면 클러스터 지원 클라이언트(ioredis Cluster, redis-py `RedisCluster`, Lettuce cluster, go-redis `ClusterClient`)가 필요하고, 다중 키 명령은 해시 태그로 같은 슬롯에 모아야 한다. VPC 안에서만 접근할 수 있으므로 Vercel처럼 VPC 밖에 있는 컴퓨트에서는 접근 경로가 필요하다(컴퓨트 표 CP.networking).

### 함정
- 기본 `volatile-lru`이므로 TTL 없는 키(세션 ttl 미설정, BullMQ 키)만 있으면 사실상 noeviction이 되어 메모리가 찼을 때 쓰기 오류가 난다. 반대로 큐와 캐시를 한 노드에 섞으면 TTL 있는 큐 키가 퇴출된다.
- 노드 기반은 "영속 저장소"가 아니다. 단일 노드는 장애가 나면 빈 캐시로 돌아오고, primary 재부팅은 복제본까지 비운다. 세션 손실이 허용되지 않으면 복제본 + Multi-AZ, 또는 durability(Valkey 9 이상, 지원 계열)나 MemoryDB가 필요하다.
- t4g.micro의 연결 한도는 20,000이다(65,000 아님).

---

## Redis / Valkey — Amazon ElastiCache Serverless (Valkey / Redis OSS)
- 계열: 캐시
- 서울 리전: 있음 (Price List에 APN2 서버리스 항목 존재: "APN2-CachedData:Valkey $0.101 per GB-hour" · 2026-10-01)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CA.persistence | 다중 AZ 복제(메모리)와 자동 백업(하루 1회, 선택). durability 미지원. AOF 없음 | 서버리스 스냅샷은 캐시당 하루 24회 한도 | https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/WhatIs.corecomponents.html · "automatically replicates your data across multiple Availability Zones (AZ)" · 2026-10-01 / https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/Durability.Limitations.html · "Durability is not supported with ElastiCache Serverless." · 2026-10-01 |
| CA.eviction | `volatile-lru` 고정(수정 불가). 슬롯당 32GiB를 넘으면 퇴출하고, 퇴출할 키가 없으면 OOM | — | https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/RedisConfiguration.html · "maxmemory-policy | volatile-lru" · "all Valkey or Redis OSS configuration is not modifiable" · 2026-10-01 |
| CA.consistency | 6379 primary 포트는 쓰기와 읽기. 6380 읽기 포트는 최종적 일관성. 페일오버 손실량은 미확인 | — | https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/RedisConfiguration.html · "the read port allows lower-latency eventually-consistent reads using the READONLY command" · 2026-10-01 |
| CA.shared_state | 가능 (세션, 락, 레이트 리밋) | TLS 클라이언트 필수, 클러스터 모드 | https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/WhatIs.corecomponents.html · "runs … in cluster mode and is only compatible with clients that support TLS" · 2026-10-01 |
| CA.pubsub | Pub/Sub 가능(출력 버퍼 32MiB/8MiB/60초). **키스페이스 알림 미지원** | — | https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/RedisConfiguration.html · "Keyspace events are currently not supported on serverless caches." · 2026-10-01 |
| CA.availability | 다중 AZ, 캐시당 99.99% SLA, 노드 교체 자동 | — | https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/WhatIs.corecomponents.html · "It offers a 99.99% availability SLA for every cache." · 2026-10-01 |
| CA.connections | maxclients 65,000. 프록시 계층 뒤의 단일 엔드포인트. VPC 엔드포인트 또는 퍼블릭 엔드포인트. 유휴 연결은 부하 분산 때문에 끊길 수 있음 | — | https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/RedisConfiguration.html · "maxclients | 65000" · "they may be disconnected during steady-state for load balancing purposes" · 2026-10-01 / https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/WhatIs.corecomponents.html · "With a public endpoint, your application connects to the cache directly over the internet, without a VPC." · 2026-10-01 |
| CA.limits | 캐시당 5,000GiB, 15,000,000 ECPU/초, 슬롯당 30K ECPU/초(READONLY 시 90K), 키 이름 4KiB, 요청 원소 512MiB, 인자 39,999개, 리전당 캐시 40개 | — | https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/RedisConfiguration.html · "Size per cache | 5,000 GiB" · "ECPU per cache | 15,000,000 ECPU/second" · "Key name length | 4 KiB" · "proto-max-bulk-len | 512 MiB" · 2026-10-01 / https://docs.aws.amazon.com/general/latest/gr/elasticache-service.html · "Serverless Caches per Region | Each supported Region: 40" · 2026-10-01 |
| CA.regions / CA.cost_floor | 서울 있음 / 최소 과금 저장량: Valkey 100MB, Redis OSS 1GB. 서울에서 Valkey는 0.1GB × $0.101 × 730 ≈ **$7.4/월**, Redis OSS는 1GB × $0.151 × 730 ≈ **$110/월**. 여기에 ECPU 비용(Valkey $0.0027/백만, Redis $0.0041/백만)이 더해짐 | scale-to-zero 없음 | https://aws.amazon.com/elasticache/pricing/ · "Valkey: 100 MB per cache" · "Redis OSS/Memcached: 1 GB per cache" · 2026-10-01 / Price List (Bash curl, AmazonElastiCache ap-northeast-2) · "$0.101 per GB-hour for Valkey data storage" · "$0.151 per GB-hour for Redis data storage" · "$0.0027 per million Valkey ECPUs" · 2026-10-01 |

### 비용 구조
과금은 GB-시간 저장량 + ECPU다. 1KB 단순 GET/SET이 1 ECPU다. 출처: https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/WhatIs.corecomponents.html · "Simple reads and writes require 1 ECPU for each kilobyte (KB) of data transferred." · 2026-10-01. Valkey 서버리스는 다른 엔진보다 33% 싸다(pricing 페이지 "33% lower price on ElastiCache Serverless"). 문서 본문(corecomponents)에는 "Each ElastiCache Serverless cache is metered for a minimum of 1 GB"라고 되어 있어 pricing 페이지의 Valkey 100MB와 서로 다르다. pricing 페이지가 엔진별로 구분하므로 Valkey 100MB를 채택했다.

### 교체 계열 정보
노드 기반과 같고, TLS와 클러스터 모드 클라이언트가 필수다. 파라미터를 수정할 수 없으므로 퇴출 정책을 바꿔야 하는 용도(큐 전용 noeviction 등)에는 맞지 않는다.

### 함정
- **Redis OSS 엔진을 고르면 최소 약 $110/월(서울)이다.** 같은 서버리스라도 Valkey(약 $7/월)와 15배 차이가 난다. 소규모 앱의 "가장 싼 공유 상태 저장소" 판정이 엔진 선택 하나로 뒤집힌다.
- `volatile-lru` 고정이고 durability도 없으므로 BullMQ·Celery 브로커처럼 유실되면 안 되는 큐 저장소로는 부적합하다. 퇴출 정책을 바꿀 수 없다.
- 키스페이스 알림이 없으므로 그것에 의존하는 라이브러리(일부 세션 만료 이벤트, 지연 작업 구현)는 동작하지 않는다.

---

## Redis / Valkey 호환 — Amazon MemoryDB
- 계열: 캐시 (영속 인메모리 DB)
- 서울 리전: 있음 (https://docs.aws.amazon.com/memorydb/latest/devguide/regionsandazs.html · "Asia Pacific (Seoul) Region ap-northeast-2 | memory-db.ap-northeast-2.amazonaws.com" · 2026-10-01)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CA.persistence | 로그 방식. 쓰기는 Multi-AZ 트랜잭션 로그에 영속된 뒤 응답함. 노드 재시작이나 복구 때도 데이터 유지 | 쓰기 지연은 한 자릿수 ms | https://docs.aws.amazon.com/memorydb/latest/devguide/what-is-memorydb.html · "stores data durably across multiple Availability Zones (AZs) using a Multi-AZ transactional log" · "microsecond read and single-digit millisecond write latency" · 2026-10-01 |
| CA.eviction | 기본 `noeviction` (Redis OSS 6 파라미터 그룹 기준. Valkey 7 그룹은 변경 목록에 없어 같은 값으로 보이나 명시 문구는 미확인) | — | https://docs.aws.amazon.com/memorydb/latest/devguide/parametergroups.redis.html · "maxmemory-policy … Default: noeviction" · 2026-10-01 |
| CA.consistency | primary는 강한 일관성이고 **페일오버를 거쳐도 유지됨(승인된 쓰기 유실 없음)**. 복제본은 최종적 일관성 | — | https://docs.aws.amazon.com/memorydb/latest/devguide/consistency.html · "Successful write operations are durably stored in a distributed Multi-AZ transactional logs before returning to clients." · "Such strong consistency is preserved across primary failovers." · 2026-10-01 |
| CA.shared_state | 가능. 세션, 락, 레이트 리밋, 큐 브로커로 쓸 수 있음(유실 없음) | — | 위 consistency 출처 |
| CA.pubsub | Pub/Sub와 Streams(엔진 기능). Pub/Sub 출력 버퍼 하드 32MiB, 소프트 8MiB/60초 | — | https://docs.aws.amazon.com/memorydb/latest/devguide/parametergroups.redis.html · "client-output-buffer-limit-pubsub-hard-limit … Default: 33554432" · 2026-10-01 |
| CA.availability | 복제본이 있으면 노드가 AZ에 분산됨. Multi-Region 옵션 있음 | 복제본 없는 단일 노드 샤드만 단일 AZ 가능 | https://docs.aws.amazon.com/memorydb/latest/devguide/regionsandazs.html · "Any cluster that has at least one replica must be spread across AZs." · 2026-10-01 |
| CA.connections | maxclients 65,000(수정 불가). VPC 안에서만 접근 | — | https://docs.aws.amazon.com/memorydb/latest/devguide/parametergroups.redis.html · "maxclients … Default: 65000 … Non modifiable." · "All MemoryDB instance types must be created in an Amazon Virtual Private Cloud VPC." · 2026-10-01 |
| CA.limits | 요청 원소 최대 512MiB, 쿼리 버퍼 1GiB. 최소 노드 db.t4g.small의 maxmemory는 약 1.47GB | — | https://docs.aws.amazon.com/memorydb/latest/devguide/parametergroups.redis.html · "proto-max-bulk-len … Default: 536870912" · "db.t4g.small | 1471026299" · 2026-10-01 |
| CA.regions / CA.cost_floor | 서울 있음 / db.t4g.small Valkey $0.049/시간이면 약 $35.8/월, Redis OSS $0.070/시간이면 약 $51.1/월(1노드). 복제본 1개를 더한 Multi-AZ Valkey는 약 $71.5/월. 쓰기량 과금: Redis OSS $0.20/GB, Valkey는 10TB/월까지 $0 | 서울 온디맨드 | Price List (Bash curl) https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonMemoryDB/current/ap-northeast-2/index.json · "$0.049 per General purpose t4g.small node hour in Asia Pacific (Seoul) running Valkey" · "$0.200 per GB for Data Written in Asia Pacific (Seoul)" · "$0 for Data Written … upto 10TB/month for Valkey" · 2026-10-01 |

### 비용 구조
노드 시간 + 쓰기 GB(Redis OSS) + 클러스터 용량의 100%를 넘는 스냅샷 저장(서울 $0.023/GB-월)이다. Valkey는 30% 싸다. 출처: https://aws.amazon.com/memorydb/pricing/ · "There is no additional charge for snapshot storage of up to 100% of your total MemoryDB cluster storage." · 2026-10-01. 무료 등급의 구체 한도는 미확인이다.

### 교체 계열 정보
Redis/Valkey 클라이언트를 그대로 쓰며 클러스터 모드 클라이언트가 필요하다. ElastiCache에서 MemoryDB로 바꿔도 코드 변경은 엔드포인트 정도다. 바뀌는 것은 쓰기 지연(µs에서 한 자릿수 ms)과 비용이다.

### 함정
- 기본 `noeviction`이므로 캐시 용도로 쓰면 메모리가 찼을 때 쓰기 오류가 난다. MemoryDB는 "유실 불가 상태 저장소"용이고 순수 캐시로는 과잉이다.
- 최소 노드가 t4g.small이라 고정비가 ElastiCache t4g.micro의 2.5배 이상이다.
- 쓰기 과금(Redis OSS $0.20/GB)은 쓰기가 많은 큐·스트림에서 커진다. Valkey를 고르면 10TB/월까지 무료다.

---

## Redis — Google Memorystore for Redis, Basic 티어
- 계열: 캐시
- 서울 리전: 있음 (가격 페이지 지역 목록에 "Seoul (asia-northeast3)", 서울 가격표 존재)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CA.persistence | 기본은 없음. RDB 스냅샷은 켜야 하는 선택 기능이고 주기는 1h/6h/12h/24h. AOF는 문서에 없음 | Basic은 재시작하면 데이터가 전부 사라질 수 있음 | https://docs.cloud.google.com/memorystore/docs/redis/rdb-snapshots "The intervals you can set are `1h`, `6h`, `12h`, and `24h`." · https://docs.cloud.google.com/memorystore/docs/redis/redis-tiers "Provides a cache with no replication" (Basic). 요약 문장: 콜드 재시작과 전체 데이터 손실을 견딜 수 있는 앱용 |
| CA.eviction | `volatile-lru` (TTL 있는 키만 퇴출함. TTL 없는 키만 있으면 메모리가 차는 순간 쓰기 오류) | 변경 가능 | https://docs.cloud.google.com/memorystore/docs/redis/supported-redis-configurations "The default maxmemory policy for Memorystore for Redis is `volatile-lru`." · https://redis.io/docs/latest/develop/reference/eviction/ "The `volatile-xxx` policies behave like `noeviction` if no keys have an associated expiration." |
| CA.consistency | 복제 없음. 노드 하나 | 노드가 죽으면 데이터 유실 | https://docs.cloud.google.com/memorystore/docs/redis/redis-tiers "Provides a cache with no replication" |
| CA.shared_state | 가능(네트워크 공유). 다만 재시작 때 세션과 락이 사라짐 | VPC 사설 IP로만 접근 | https://docs.cloud.google.com/memorystore/docs/redis/memorystore-for-redis-overview "Redis instances are protected from the internet using private IPs" |
| CA.pubsub | 미확인 (차단 명령 목록 페이지를 열지 못함) | — | 미확인 |
| CA.availability | HA 없음. 자동 페일오버 없음. 단일 존 | Basic에서 Standard로 티어를 바꿀 수 없음(가져오기·내보내기로 새 인스턴스를 만들어야 함) | https://docs.cloud.google.com/memorystore/docs/redis/redis-tiers "Tier migration isn't supported" |
| CA.connections | maxclients 65,000, 변경 불가 | TCP(RESP) 연결. HTTP API 없음 | https://docs.cloud.google.com/memorystore/docs/redis/supported-redis-configurations (maxclients 기본값 65000, 수정 불가로 표기) |
| CA.limits | 1 GB부터 300 GB | 용량 티어 M1~M5 | https://docs.cloud.google.com/memorystore/docs/redis/redis-tiers "Maximum 300 GB primary size" |
| CA.regions / CA.cost_floor | 서울 있음. 서울 Basic M1은 GiB당 시간 $0.065, 1 GiB 최소 기준 약 $47.45/월 | 쓰지 않아도 프로비저닝한 용량만큼 과금 | https://cloud.google.com/memorystore/docs/redis/pricing 서울 표 "Basic M1 (1 to 4 GiB) $0.065 / 1 gibibyte hour", "$47.45 / 1 gibibyte month" · "Whether you use the instance or not, you are charged based on the provisioned capacity." |

### 비용 구조
최소 월 고정비는 서울 기준 약 $47.45(1 GiB Basic)다. 프로비저닝한 GiB와 시간으로 과금하고 초 단위로 올림한다. 무료 등급과 scale-to-zero는 없다. 함정: M1(1~4 GiB) 단가가 가장 비싸다. 작은 인스턴스일수록 GiB당 단가가 높다.

### 교체 계열 정보
Redis OSS 프로토콜(7.2 이하)이라 클라이언트를 바꿀 필요가 없다(ioredis, node-redis, redis-py, Jedis/Lettuce). 바꾸는 지점: express-session MemoryStore를 connect-redis로, 인메모리 레이트 리밋을 rate-limit-redis로, 인메모리 Map 캐시를 Redis GET/SET+TTL로 옮긴다. 사설 IP 전용이라 Cloud Run이나 GKE에서 VPC 연결(Direct VPC egress 또는 커넥터)이 필요하다.

### 함정
- 기본 퇴출이 `volatile-lru`라서 TTL 없는 세션·큐 키가 메모리를 채우면 쓰기 오류가 난다.
- Basic은 HA가 없다. 세션을 Basic에 두면 정비 이벤트에서 전원이 로그아웃될 수 있다.
- 티어를 바꾸려면 새 인스턴스를 만들어야 한다.

---

## Redis — Google Memorystore for Redis, Standard 티어(HA)
- 계열: 캐시
- 서울 리전: 있음 (위와 같은 가격표)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CA.persistence | 기본 없음. RDB 스냅샷 선택(1h/6h/12h/24h) | AOF는 문서에 없음 | https://docs.cloud.google.com/memorystore/docs/redis/rdb-snapshots "The intervals you can set are `1h`, `6h`, `12h`, and `24h`." |
| CA.eviction | `volatile-lru` | 주 노드 메모리의 10%를 복제 백로그용으로 예약 | https://docs.cloud.google.com/memorystore/docs/redis/supported-redis-configurations "The default maxmemory policy for Memorystore for Redis is `volatile-lru`." · https://docs.cloud.google.com/memorystore/docs/redis/product-constraints "Standard Tier Memorystore for Redis instances reserve 10% of primary-node memory for replication backlog usage." |
| CA.consistency | 비동기 복제. **페일오버 때 확인 응답을 받은 쓰기도 유실될 수 있음** | — | https://docs.cloud.google.com/memorystore/docs/redis/high-availability-for-memorystore-for-redis "Because of the asynchronous nature of the Redis replication protocol, acknowledged writes might be lost during a failover." |
| CA.shared_state | 가능(세션, 레이트 리밋). 분산 락은 비동기 복제 때문에 페일오버 시 안전성이 깨질 수 있음 | — | 위 HA 문서와 같음 |
| CA.pubsub | 미확인 | — | 미확인 |
| CA.availability | 존을 넘는 복제와 자동 페일오버. 자동 복구 때 약 30초, 정비 때 약 15초 쓸 수 없음. 읽기 복제본은 최대 5개(M2 이상) | — | https://docs.cloud.google.com/memorystore/docs/redis/high-availability-for-memorystore-for-redis (자동 복구 약 30초, 정비 약 15초) · https://docs.cloud.google.com/memorystore/docs/redis/redis-tiers "Provides redundancy and availability using replication" · https://cloud.google.com/memorystore/docs/redis/pricing "Read replicas are only supported on M2 and higher memory tiers." |
| CA.connections | 65,000, 변경 불가 | TCP | https://docs.cloud.google.com/memorystore/docs/redis/supported-redis-configurations |
| CA.limits | 1~300 GB | 쓰기 대역폭 16 Gbps | https://docs.cloud.google.com/memorystore/docs/redis/redis-tiers "Maximum 300 GB primary size" |
| CA.regions / CA.cost_floor | 서울 Standard M1은 GiB당 시간 $0.114, 약 $83.22/월(1 GiB) | 읽기 복제본은 노드별로 추가 과금 | https://cloud.google.com/memorystore/docs/redis/pricing 서울 표 "Standard M1 (1 to 4 GiB) $0.114 / 1 gibibyte hour", "$83.22 / 1 gibibyte month" |

### 비용 구조
서울 1 GiB HA의 최소 월 고정비는 약 $83.22다. 1년·3년 CUD 할인은 M2 이상에만 있다(M1은 "-"로 표기).

### 교체 계열 정보
Basic과 같다. 페일오버 뒤 연결이 끊기므로 클라이언트 재연결 설정을 확인해야 한다.

### 함정
- HA여도 비동기 복제다. 페일오버 때 마지막 쓰기가 유실될 수 있으니, 정확해야 하는 카운터·잔액·큐의 유일한 저장소로 쓰면 안 된다.
- 판정 규칙: "세션 공유"는 충족하고, "유실 0 큐"는 미충족이다.

---

## Valkey — Google Memorystore for Valkey (클러스터 모드 켬/끔)
- 계열: 캐시
- 서울 리전: 있음 (Valkey 가격 페이지에 서울 가격표가 있음)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CA.persistence | RDB(1~24시간 주기) 또는 AOF(appendfsync 기본 `everysec`) 중 하나만 고름. 기본으로 켜져 있는지는 미확인 | 둘을 동시에 쓸 수 없음. RDB 최악 유실 = 주기 + 저장 시간 | https://docs.cloud.google.com/memorystore/docs/valkey/about-rdb-persistence "snapshot interval ranging from a minimum of 1 hour to a maximum of 24 hours" · https://docs.cloud.google.com/memorystore/docs/valkey/about-aof-persistence "`everysec`… (the default)", "you can't enable both persistence modes at the same time" |
| CA.eviction | `volatile-lru` | 변경 가능 | https://docs.cloud.google.com/memorystore/docs/valkey/supported-instance-configurations "The default maxmemory policy for Memorystore for Valkey is `volatile-lru`." |
| CA.consistency | 비동기 복제. 예기치 못한 페일오버 때 확인된 쓰기가 유실될 수 있음. WAIT으로 보완 | — | https://docs.cloud.google.com/memorystore/docs/valkey/ha-and-replicas "acknowledged writes may be lost due to the asynchronous nature of Valkey's replication protocol" |
| CA.shared_state | 가능 | 클러스터 모드를 켜면 클러스터를 아는 클라이언트가 필요 | https://docs.cloud.google.com/memorystore/docs/valkey/product-overview "can be created in both Cluster Mode Enabled and Cluster Mode Disabled modes" |
| CA.pubsub | 있음. PUBLISH, SUBSCRIBE, SSUBSCRIBE, XADD, XREADGROUP 지원 | 클러스터 모드 켬/끔 모두 | https://docs.cloud.google.com/memorystore/docs/valkey/supported-commands (지원 명령 목록에 "PUBLISH", "SUBSCRIBE", "SSUBSCRIBE", "XADD", "XREADGROUP") |
| CA.availability | HA에는 샤드마다 복제본 1개 이상 필요. 존에 분산 배치. 샤드당 복제본 0~5개 | 복제본 0개면 HA 없음 | https://docs.cloud.google.com/memorystore/docs/valkey/ha-and-replicas "you must provision at least 1 replica for every shard", "distributes the primary and replica VMs of shards across multiple zones" |
| CA.connections | 노드 유형별: shared-core-nano 5,000(최대 5,000), standard-small 16,000(최대 32,000), highmem-medium 32,000(최대 64,000) | maxclients 변경 가능 | https://docs.cloud.google.com/memorystore/docs/valkey/instance-node-specification (노드 사양 표) |
| CA.limits | 노드당 1.25~110 GB. shared-core-nano는 1.4 GB이고 SLA 없음 | nano는 개발·테스트용 | https://docs.cloud.google.com/memorystore/docs/valkey/instance-node-specification "has no SLA, making it unsuitable for production workloads" |
| CA.regions / CA.cost_floor | 서울: shared-core-nano $0.0408/시간(약 $29.78/월), custom-pico $0.039424/시간(약 $28.78/월), standard-small $0.183/시간(약 $133.59/월), 모두 노드당 | HA = 주 노드 + 복제본 1개 이상이라 최소 2배 | https://cloud.google.com/memorystore/valkey/pricing 서울 표 "shared-core-nano 1.4 GB $0.0408 / 1 hour", "custom-pico 1.25 GB $0.039424 / 1 hour", "standard-small 6.5 GB $0.183 / 1 hour" |

### 비용 구조
노드·시간 단위로 과금한다. 서울에서 가장 싼 단일 노드는 custom-pico로 약 $28.78/월이다. HA를 갖춘 최소 구성(pico 2노드)은 계산상 약 $57.6/월이다(가격표 단가 × 2로 계산한 값). 영속성 저장소는 GB·시간 단위로 따로 과금한다(서울 표에 "$0.00012778 / 1 gigabyte hour" 등이 있으나 어느 항목인지는 페이지에서 확정하지 못함).

### 교체 계열 정보
Redis OSS와 호환된다(지원 버전 7.2, 8.0, 9.0, 9.1). ioredis, node-redis, redis-py, valkey-glide를 쓴다. 클러스터 모드를 켜면 ioredis `Cluster`나 redis-py `RedisCluster`가 필요하고, 여러 키를 다루는 연산은 해시 태그로 같은 슬롯에 모아야 한다(교차 슬롯 제약은 Redis 일반 사항이며 이 문서에서는 미확인).

### 함정
- 가장 싼 nano는 SLA가 없어 운영용으로 부적합하다.
- AOF 기본 everysec이라도 최대 약 1초 분량은 유실될 수 있고, 비동기 복제 유실도 따로 있다.
- 기본 퇴출이 `volatile-lru`다.

---

## Redis Cluster — Google Memorystore for Redis Cluster
- 계열: 캐시
- 서울 리전: 있음 (Redis Cluster 가격 페이지에 서울 가격표가 있음)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CA.persistence | AOF 또는 RDB 중 하나 | 기본 상태는 미확인 | https://docs.cloud.google.com/memorystore/docs/cluster/persistence-overview "You can either enable AOF or RDB persistence for your instance, not both." |
| CA.eviction | `volatile-lru` | — | https://docs.cloud.google.com/memorystore/docs/cluster/supported-instance-configurations (기본 maxmemory 정책 "volatile-lru") |
| CA.consistency | 비동기 복제. 예기치 못한 페일오버 때 확인된 쓰기 유실 가능 | — | https://docs.cloud.google.com/memorystore/docs/cluster/ha-and-replicas "acknowledged writes may be lost due to the asynchronous nature of Redis's replication protocol" |
| CA.shared_state | 가능. 클러스터 모드만 있어 클라이언트가 탐색 엔드포인트로 노드를 찾아야 함 | 클러스터 미지원 라이브러리는 바로 쓸 수 없음 | https://docs.cloud.google.com/memorystore/docs/cluster/memorystore-for-redis-cluster-overview "Your client also uses the discovery endpoint for cluster node discovery." |
| CA.pubsub | 있음. PUBLISH, SUBSCRIBE, SSUBSCRIBE, XADD, XREADGROUP | — | https://docs.cloud.google.com/memorystore/docs/cluster/supported-commands (지원 명령 목록) |
| CA.availability | 샤드마다 복제본 1개 이상이면 HA. 여러 존에 분산 | — | https://docs.cloud.google.com/memorystore/docs/cluster/ha-and-replicas "you must provision at least 1 replica for every shard", "distributed across multiple zones to safeguard against a zonal outage" |
| CA.connections | nano 5,000. standard-small 16,000(최대 32,000). highmem-xlarge 이상 64,000 | 노드당 | https://docs.cloud.google.com/memorystore/docs/cluster/cluster-node-specification (노드 유형별 연결 표) |
| CA.limits | 최대 27,500 GB(250 샤드). nano는 1.12 GB 고정 | Redis 7.x 기반, 명령 일부만 지원 | https://docs.cloud.google.com/memorystore/docs/cluster/cluster-node-specification "27,500 GB", "The redis-shared-core-nano node type has a hard limit of 1.12 GB" · https://docs.cloud.google.com/memorystore/docs/cluster/memorystore-for-redis-cluster-overview "supports a subset of the total Redis command library" |
| CA.regions / CA.cost_floor | 서울: redis-shared-core-nano $0.0408/시간(약 $29.78/월), redis-standard-small $0.183/시간(약 $133.59/월), 노드당 | 운영용 HA는 standard-small 2노드 이상, 약 $267/월(계산값) | https://cloud.google.com/memorystore/cluster/pricing 서울 표 "redis-shared-core-nano 1.4 GB $0.0408 / 1 hour", "redis-standard-small 6.5 GB $0.183 / 1 hour" |

### 비용 구조
노드·시간 단위로 과금한다. nano는 SLA가 없다. 운영용 최소 HA는 서울 기준 약 $267/월(standard-small × 2)로 계산된다.

### 교체 계열 정보
클러스터를 지원하는 클라이언트가 필요하다(ioredis Cluster, redis-py RedisCluster, Lettuce). BullMQ나 Sidekiq처럼 여러 키를 쓰는 라이브러리는 해시 태그·prefix 설정을 확인해야 한다(라이브러리 쪽 요건은 미확인).

### 함정
- 노드 1개의 소형 앱에는 과잉이다. 클러스터 모드 전용이라 연결 코드를 바꿔야 한다.
- 개요 페이지에는 Valkey로 옮기라는 공지가 없다(2026-10-01 확인).

---

## Upstash Redis — 서버리스(Free / Pay as You Go / Fixed)
- 계열: 캐시
- 서울 리전: **없음.** 지원 지역 목록의 AWS 아시아는 ap-south-1, ap-southeast-1, ap-northeast-1(도쿄), ap-southeast-2이고, GCP는 asia-northeast1(도쿄)뿐이다. 가장 가까운 곳은 도쿄다.

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CA.persistence | 항상 켜짐. 모든 쓰기를 메모리와 블록 스토리지(EBS 등)에 함께 저장 | 메모리에서 퇴출돼도 디스크에 남아 있음 | https://upstash.com/docs/redis/features/durability "In Upstash, persistence is always enabled… Every write operation is consistently stored in both memory and the block storage provided by cloud providers, such as AWS's EBS." ⚠️출처확인필요 |
| CA.eviction | 기본은 퇴출 꺼짐. 최대 데이터 크기에 닿으면 쓰기 거부. 켜면 optimistic-volatile 방식 | — | https://upstash.com/docs/redis/features/eviction "By default eviction is disabled, and Upstash Redis will reject write operations once the maximum data size limit has been reached." ⚠️출처확인필요 |
| CA.consistency | 리더 기반 비동기 전파, 최종 일관성. 같은 연결 안에서만 인과 일관성. 분할 시 LWW. Strong Consistency는 폐기됨 | 리더 선출 중 쓰기가 잠시 막힘 | https://upstash.com/docs/redis/features/consistency "asynchronously propagated to the backup replicas", "can provide only **Eventual Consistency**", "we decided to deprecate this feature" ⚠️출처확인필요 |
| CA.shared_state | 가능(세션, 레이트 리밋). @upstash/ratelimit 제공. REST로도 접근 가능해 서버리스·엣지에 적합 | 강한 락 보장은 없음(최종 일관성) | https://upstash.com/docs/redis/features/restapi "Access your Upstash Redis database over HTTP, from serverless and edge runtimes where TCP connections are restricted." ⚠️출처확인필요 |
| CA.pubsub | 있음. TCP SUBSCRIBE, REST `/subscribe`(SSE). **블로킹 명령(BLPOP, BRPOP, BZPOPMAX 등)은 REST 미지원** | 블로킹 명령을 쓰는 큐 라이브러리는 TCP 필요 | https://upstash.com/docs/redis/features/restapi "The `SUBSCRIBE` endpoint works using Server Send Events", "Blocking commands (BLPOP - BRPOP - BRPOPLPUSH) are not supported." ⚠️출처확인필요 |
| CA.availability | 유료 플랜은 복제. 멀티 존 HA와 가동률 SLA는 Prod Pack(+$200/월/DB)에서만 | Free는 복제·SLA 없음 | https://upstash.com/docs/redis/features/durability "except for the free tier, all paid tier databases provide extra redundancy by replicating data to multiple instances" · https://upstash.com/docs/redis/features/replication "When Prod Pack is enabled, replicas … are deployed across multiple availability zones" · https://upstash.com/docs/redis/overall/pricing (Prod Pack "+$200/month per database", Uptime SLA·Multi-Zone HA) ⚠️출처확인필요 |
| CA.connections | TCP 동시 연결 한도 숫자는 미확인. REST 클라이언트(@upstash/redis)를 쓰면 연결 문제 없음 | 초과하면 "ERR max concurrent connections exceeded" | https://upstash.com/docs/redis/troubleshooting/max_concurrent_connections "use @upstash/redis client which is REST based so it does not have any connection related problems" ⚠️출처확인필요 |
| CA.limits | Free·PAYG: 초당 명령 10,000, 요청 10 MB, 레코드 100 MB. 최대 데이터: Free 256 MB, PAYG 100 GB. Fixed 250MB 플랜은 250 MB, 초당 10,000 | Fixed 상위 티어는 한도가 더 큼 | https://upstash.com/docs/redis/overall/pricing "Max request size 10 MB", "Max record size 100 MB", "Max commands per second 10,000", "Max data size 256 MB 100 GB 250 MB" ⚠️출처확인필요 |
| CA.regions / CA.cost_floor | 서울 없음(도쿄). Free $0(256 MB, 월 50만 명령, 10 GB 대역폭). PAYG는 10만 명령당 $0.2, 저장 GB당 $0.25(첫 1 GB 무료). Fixed 250MB $10/월 | 운영 SLA를 원하면 +$200/월 | https://upstash.com/docs/redis/overall/pricing "$0.2 per 100K commands", "$0.25 per GB", "Fixed 250MB $10/month" · https://upstash.com/docs/redis/features/globaldatabase (지역 표, 서울 없음) ⚠️출처확인필요 |

### 비용 구조
scale-to-zero에 가깝다(PAYG는 사용량만 과금). 최소 고정비: 무료 $0, 고정 플랜 $10/월, 운영 SLA까지 넣으면 +$200/월. 함정: PAYG는 명령 수 과금이라, BullMQ처럼 계속 폴링하는 워커를 붙이면 유휴 상태에서도 명령 수가 쌓인다(일반 원리, Upstash 문서의 BullMQ 비용 문구는 미확인).

### 교체 계열 정보
TCP(ioredis, redis-py 그대로, TLS `rediss://`)와 REST(`@upstash/redis`, `upstash-redis` Python)를 함께 지원한다. Vercel·Cloudflare Workers·Lambda에서는 REST 클라이언트를 권장한다. 세션은 connect-redis + ioredis(TCP) 또는 REST 기반 어댑터. 레이트 리밋은 `@upstash/ratelimit`. 블로킹 명령은 REST에서 쓸 수 없다.

### 함정
- 서울 리전이 없어 서울 앱 서버에서 도쿄 왕복 지연이 생긴다(지연 수치는 미확인).
- 최종 일관성이고 Strong Consistency는 폐기됐다. 분산 락·재고 차감의 근거로 쓰면 안 된다.
- 기본 퇴출이 꺼져 있어 가득 차면 쓰기가 거부된다. 캐시 용도라면 퇴출을 켜야 한다.
- 무료 등급은 복제가 없다.

---

## Vercel KV — 현황(종료)
- 계열: 캐시
- 서울 리전: 해당 없음(제품 종료)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CA.persistence | 해당 없음. 제품 종료. 기존 스토어는 2024년 12월 Upstash Redis로 자동 이전됨 | 새 프로젝트는 Marketplace Redis 사용 | https://vercel.com/docs/storage/vercel-kv (→ /docs/redis) "Vercel KV is no longer available. If you had an existing Vercel KV store, we automatically moved it to Upstash Redis in December 2024." |
| CA.eviction / consistency / shared_state / pubsub / availability / connections / limits / regions / cost_floor | 해당 없음. Upstash Redis 항목을 따른다 | — | 위와 같음 |

### 교체 계열 정보
코드에 `@vercel/kv`가 있으면 실제 백엔드는 Upstash다. `@upstash/redis`로 옮기는 것이 정석이다(`@vercel/kv` 패키지 상태는 미확인). 환경 변수 `KV_REST_API_URL`·`KV_REST_API_TOKEN` 이름 처리 방식은 미확인.

### 함정
"Vercel KV를 쓴다"는 신호는 곧 "Upstash Redis, 서울 리전 없음, 최종 일관성"으로 바꿔 판정해야 한다.

---

## Vercel Edge Config → Global Config (이름 변경)
- 계열: 캐시(읽기 최적화 설정 저장소)
- 서울 리전: 해당 없음(전역 복제, 가장 가까운 지역에서 읽음)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CA.persistence | 영속. 변경할 때마다 백업 자동 저장. 백업 보존: Hobby 7일, Pro 90일, Enterprise 365일 | — | https://vercel.com/docs/edge-config/edge-config-limits (→ /docs/global-config/global-config-limits) "Backup retention 7 days / 90 days / 365 days" |
| CA.eviction | 해당 없음. 크기를 넘는 갱신은 거부됨 | — | 같은 페이지 "Updates to items in your Global Config will be rejected if the resulting size … would exceed your account plan's limits." |
| CA.consistency | 쓰기 전파에 전역 최대 10초. 자주 바뀌거나 쓴 직후 읽어야 하는 데이터에는 부적합 | — | 같은 페이지 "it may take up to 10 seconds for the update to be globally propagated. You should avoid using Global Configs for frequently updated data" |
| CA.shared_state | **불가**(세션, 락, 레이트 리밋 카운터 용도로 못 씀). 플래그·리다이렉트·IP 차단 목록 용도 | 쓰기 한도: Hobby 월 250회, Pro·Enterprise 시간당 100회 | https://vercel.com/docs/global-config/migration-guide "Writes 250 per month (unchanged) / 100 per hour (was 480 per day)" |
| CA.pubsub | 없음 | — | https://vercel.com/docs/edge-config (pub/sub 기능 언급 없음, 용도 "feature flags, A/B testing, critical redirects, and IP blocking") |
| CA.availability | Vercel이 호스팅하며 배포와 거의 같은 가용성 | — | https://vercel.com/docs/edge-config "Global Config is hosted by Vercel, and has nearly identical uptime characteristics to your deployment" |
| CA.connections | SDK·REST 읽기. 프로젝트당 연결 스토어 1개(Hobby) / 3개(Pro·Enterprise) | — | https://vercel.com/docs/global-config/migration-guide "The per-project connection limit is unchanged: 1 on Hobby, and 3 on Pro and Enterprise." |
| CA.limits | 스토어당 1 MB(전 플랜). 키 이름 256자. 읽기 P99 15ms 이내 | — | https://vercel.com/docs/edge-config/edge-config-limits "Maximum store size 1 MB" · https://vercel.com/docs/edge-config "within 15ms at P99, or often less than 1ms" |
| CA.regions / CA.cost_floor | 전역. Pro 단가: Reads $3.00, Writes $5.00(과금 단위는 페이지에 표기되지 않아 미확인). Hobby 포함량은 미확인 | — | https://vercel.com/docs/pricing "Global Config Reads (formerly known as Edge Config Reads) $3.00", "Global Config Writes … $5.00" |

### 비용 구조
Pro에서 읽기·쓰기 횟수로 과금한다(단가 단위 미확인). 고정비는 없다.

### 교체 계열 정보
`@vercel/edge-config`는 `@vercel/global-config`로 대체(drop-in)되고, 환경 변수 `EDGE_CONFIG`는 `GLOBAL_CONFIG`로 바뀐다. 기존 패키지·변수는 계속 동작한다. 다만 새로 연결한 스토어는 `GLOBAL_CONFIG`만 만들기 때문에 구 SDK로는 읽지 못한다.

### 함정
- 문서와 출처에서 이름이 Global Config로 바뀌었다(구 URL은 리다이렉트됨).
- 세션·캐시 대체재가 아니다. 1 MB, 쓰기 시간당 100회, 전파 최대 10초다.
- 새 스토어를 구 SDK와 함께 쓰면 읽기에 실패한다.

---

## Cloudflare Workers KV
- 계열: 캐시(전역 최종 일관성 키-값)
- 서울 리전: 해당 없음(Cloudflare 전역 네트워크. 리전 선택 개념 없음)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CA.persistence | 영속 저장소(스냅샷·로그 개념 없음). TTL 최소 60초 | 내구성 보장 문구는 미확인 | https://developers.cloudflare.com/kv/api/write-key-value-pairs/ "The minimum value is 60" (expirationTtl) |
| CA.eviction | 해당 없음(용량 기반 퇴출 없음, 저장량 과금) | Free는 계정당 1 GB | https://developers.cloudflare.com/kv/platform/limits/ "Storage per account 1 GB (Free)" |
| CA.consistency | 최종 일관성. 다른 지역에 보이기까지 60초 이상 걸릴 수 있음. 원자 연산·트랜잭션 없음 | 같은 위치에서는 즉시 보임 | https://developers.cloudflare.com/kv/concepts/how-kv-works/ "Changes may take up to 60 seconds or more to be visible in other global network locations", "not ideal for applications where you need support for atomic operations" |
| CA.shared_state | 읽기 위주 공유 상태(설정, 캐시, 세션 조회)에만 적합. **레이트 리밋 카운터나 락에는 부적합**(같은 키 쓰기 초당 1회, 최종 일관성). 강한 일관성이 필요하면 Durable Objects 권장 | — | https://developers.cloudflare.com/kv/concepts/how-kv-works/ (Durable Objects 권장) · https://developers.cloudflare.com/kv/api/write-key-value-pairs/ "Writes made to the same key within 1 second will cause rate limiting (`429`) errors." |
| CA.pubsub | 없음 | — | https://developers.cloudflare.com/kv/concepts/how-kv-works/ (KV 기능에 pub/sub 없음) |
| CA.availability | Cloudflare 전역 네트워크. SLA 수치는 미확인 | — | 미확인 ⚠️근거없음 |
| CA.connections | Workers 바인딩(`env.NS.get/put`) 또는 REST API. 호출 한 번당 작업 1,000회 | — | https://developers.cloudflare.com/kv/platform/limits/ "Operations per Worker invocation 1000" |
| CA.limits | 값 25 MiB, 키 512 바이트, 메타데이터 1,024 바이트. 같은 키 쓰기 초당 1회. Free는 하루 읽기 10만·쓰기 1,000 | 네임스페이스 1,000개 | https://developers.cloudflare.com/kv/platform/limits/ "25 MiB", "512 bytes", "1 per second", "100,000 reads per day", "1,000 writes per day" |
| CA.regions / CA.cost_floor | Free $0. Paid는 Workers Paid 최소 $5/월. 포함량: 읽기 월 1천만(+$0.50/백만), 쓰기 월 1백만(+$5.00/백만), 저장 1 GB(+$0.50/GB-월) | 데이터 전송 무료. null 결과도 과금 | https://developers.cloudflare.com/kv/platform/pricing/ "10 million/month, + $0.50/million", "1 million/month, + $5.00/million", "1 GB, + $0.50/ GB-month" · https://developers.cloudflare.com/workers/platform/pricing/ "a minimum charge of $5 USD per month for an account" |

### 비용 구조
Free $0(하루 한도). Paid는 $5/월부터. 쓰기가 읽기보다 10배 비싸다.

### 교체 계열 정보
Workers 바인딩 API(`get`, `put`, `delete`, `list`), Workers 밖에서는 REST API로 쓴다. Redis 프로토콜이 아니라 Redis 명령(INCR, 리스트, 집합, pub/sub)을 옮겨 올 수 없다. 원자 카운터·락·세션 쓰기가 잦으면 Durable Objects(또는 D1, Upstash)로 가야 한다.

### 함정
- 같은 키에 초당 1회를 넘겨 쓰면 429가 난다.
- 전역 전파에 60초 이상 걸릴 수 있다. 로그인 직후 세션 쓰기 → 다른 지역 읽기가 실패할 수 있다.
- Free는 하루 쓰기 1,000회라 세션 저장소로 쓰면 바로 바닥난다.

---

# 파트 3. 큐·스트림·작업

## Amazon SQS — 표준 큐
- 계열: 큐
- 서울 리전: 있음 (Price List 서울 항목 "$0.40 per million Amazon SQS standard requests in Tier1 in Asia Pacific (Seoul)")

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| QU.delivery | 최소 1회. 중복 전달 가능. 가시성 타임아웃 안에서도 중복 가능 | 여러 AZ에 저장한 뒤 응답 | https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues.html · "Standard queues ensure at-least-once message delivery, but … more than one copy of a message might be delivered" · "redundantly stores the message in multiple availability zones (AZs) before acknowledging it" |
| QU.ordering | 최선 노력. 순서 뒤바뀜 가능 | — | 같은 문서 · "messages may occasionally arrive out of order" |
| QU.dedup | 없음(소비자 멱등 필요) | — | 같은 문서 · "as long as your application can handle messages that might arrive more than once" |
| QU.retention | 보존 기본 4일, 60초~14일. 메시지 최대 1 MiB(그 이상은 S3 확장 클라이언트로 2 GB). 지연 최대 15분 | — | https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html · "By default, a message is retained for 4 days. The minimum is 60 seconds (1 minute). The maximum is 1,209,600 seconds (14 days)." · "The maximum is 1,048,576 bytes (1 MiB)." |
| QU.retry_dlq | 가시성 타임아웃 기본 30초, 최대 12시간(처음 수신 시점부터, 연장해도 초기화 안 됨). DLQ는 `maxReceiveCount`. 표준 큐 DLQ는 원래 큐 넣은 시각 기준으로 만료 | in-flight 약 12만 개 | https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html · "The default visibility timeout for a queue is 30 seconds" · "maximum limit of 12 hours from when the message is first received. Extending the timeout doesn't reset this 12-hour limit." · "approximately 120,000 in-flight messages" / https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html · "the expiration of a message is always based on its original enqueue timestamp" |
| QU.throughput | 사실상 무제한 | — | quotas-messages · "nearly unlimited number of API calls per second, per action" |
| QU.consumer_scaling | Lambda 이벤트 소스(기본 동시 5에서 분당 +300, 최대 1,250). KEDA `aws-sqs-queue`(기본 큐 길이 목표 5, in-flight 포함) | — | https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-scaling.html · "increases the number of processes … by up to 300 more concurrent invokes per minute. The maximum … is 1,250." / https://keda.sh/docs/2.21/scalers/aws-sqs/ (queueLength 기본 5, scaleOnInFlight 기본 true) ⚠️출처확인필요 |
| QU.availability / QU.regions / QU.cost_floor | 다중 AZ / 서울 있음 / **$0 고정비.** 월 100만 요청 무료, 이후 서울 $0.40/백만. 64KB 단위로 1요청 | 같은 리전 전송 무료 | https://aws.amazon.com/sqs/pricing/ · "All customers can make 1 million Amazon SQS requests for free each month." · "Each 64 KB chunk of a payload is billed as 1 request" / Price List https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSQueueService/current/ap-northeast-2/index.json · "$0.40 per million Amazon SQS standard requests in Tier1 in Asia Pacific (Seoul)" |

### 비용 구조
고정비 0, 요청 단위 과금. 빈 큐를 짧은 폴링으로 돌리면 요청이 쌓이므로 롱 폴링(최대 20초)을 씁니다.

### 교체 계열 정보
- 클라이언트: Node `@aws-sdk/client-sqs`, Python `boto3`, Java AWS SDK v2, Go `aws-sdk-go-v2`. 라이브러리: Node `sqs-consumer`, Celery SQS 브로커.
- 앱 프로세스 큐 → SQS: 핸들러는 `SendMessage`, 워커는 롱 폴링 + 처리 후 `DeleteMessage` + 가시성 연장(하트비트) + 멱등키(메시지 ID 또는 비즈니스 키 유니크 제약).
- DB 쓰기와 함께 보내야 하면 트랜잭셔널 아웃박스(04 문서 C 영역).

### 함정
- 처리 시간이 가시성 타임아웃보다 길면 같은 작업이 다른 워커에서 또 실행됩니다.
- 12시간 넘는 작업은 SQS로 붙잡아 둘 수 없습니다.
- DLQ 보존 기간을 원래 큐보다 짧게 두면 DLQ에 들어가자마자 사라질 수 있습니다.

---

## Amazon SQS — FIFO 큐
- 계열: 큐
- 서울 리전: 있음 (Price List "$0.50 per million Amazon SQS FIFO requests in Tier1 in Asia Pacific (Seoul)")

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| QU.delivery | 정확히 1회 처리(조건: 5분 중복 제거 창 안의 재전송, 가시성 타임아웃 안 삭제). 가시성 타임아웃이 지나면 재전달 | — | https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues-exactly-once-processing.html · "If you retry the SendMessage action within the 5-minute deduplication interval, Amazon SQS doesn't introduce any duplicates into the queue." |
| QU.ordering | 메시지 그룹 ID 안에서 엄격한 순서. 그룹의 메시지가 처리 중이면 다음 메시지는 대기 | `MessageGroupId` 필수 | https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html · "messages with the same message group ID are processed in a strict sequence" |
| QU.dedup | 중복 제거 ID 또는 본문 SHA-256(내용 기반). 창 5분 | 속성은 해시에 안 들어감 | FIFO-queues-exactly-once-processing · "use a SHA-256 hash to generate the message deduplication ID using the body of the message—but not the attributes" |
| QU.retention | 표준 큐와 같음(최대 14일, 1 MiB). DLQ로 옮기면 넣은 시각이 초기화됨 | FIFO DLQ는 순서를 깨뜨림 | quotas-messages / sqs-dead-letter-queues · "For FIFO queues, the enqueue timestamp resets when the message is moved to a dead-letter queue." · "Don't use a dead-letter queue with a FIFO queue if you don't want to break the exact order" |
| QU.retry_dlq | 표준 큐와 같음. in-flight 최대 12만 | — | https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-fifo.html · "FIFO queues support a maximum of 120,000 in-flight messages" |
| QU.throughput | 파티션당 API 액션별 300 TPS(배치 시 3,000 메시지/초). 고처리량 모드: 서울은 "기타 리전" 기본 2,400 TPS(배치 24,000 메시지/초) | 서울은 목록에 없어 기타 리전 값 적용으로 판단 | quotas-messages · "Each partition in a FIFO queue is limited to 300 transactions per second" · "All other AWS Regions: Default throughput of 2,400 TPS." |
| QU.consumer_scaling | Lambda 동시 실행이 메시지 그룹 수로 제한됨 | — | services-sqs-scaling · "For FIFO queues, concurrent invocations are capped either by the number of message group IDs … or the maximum concurrency setting—whichever is lower." |
| QU.availability / QU.regions / QU.cost_floor | 다중 AZ / 서울 있음 / $0 고정비, 서울 $0.50/백만 | — | Price List(위 URL) |

### 비용 구조
표준보다 요청 단가가 25% 높습니다(서울 $0.50 vs $0.40/백만).

### 교체 계열 정보
표준 큐와 같은 SDK. 보낼 때 `MessageGroupId`와 `MessageDeduplicationId`(또는 내용 기반)를 넣어야 합니다. 큐 이름은 `.fifo`로 끝나야 합니다. Celery는 `apply_async`에 두 속성을 넘겨야 합니다.

### 함정
- "정확히 1회"는 보내는 쪽 중복 제거(5분)일 뿐입니다. 소비자가 처리 후 삭제 전에 죽으면 다시 처리됩니다.
- 그룹 ID를 하나만 쓰면 처리량이 직렬화됩니다.

---

## Amazon SNS — 표준 / FIFO 토픽
- 계열: 큐 (pub/sub 팬아웃)
- 서울 리전: 있음 (https://docs.aws.amazon.com/general/latest/gr/sns.html · "Asia Pacific (Seoul) | ap-northeast-2 | sns.ap-northeast-2.amazonaws.com")

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| QU.delivery | 표준: 재시도 후 실패 시 버림(DLQ 붙이면 보존). FIFO + SQS FIFO 구독: 조건부 정확히 1회. 필터를 쓰면 최대 1회 | 재시도 가능 오류는 5xx, 429 | https://docs.aws.amazon.com/sns/latest/dg/sns-message-delivery-retries.html · "When the delivery policy is exhausted, Amazon SNS stops retrying the delivery and discards the message—unless a dead-letter queue is attached" / https://docs.aws.amazon.com/sns/latest/dg/fifo-message-dedup.html · "When you configure message filtering, Amazon SNS FIFO topics support at-most-once delivery" |
| QU.ordering | 표준: 보장 없음(문서 문구 미확인). FIFO: 메시지 그룹 안 순서 | — | https://docs.aws.amazon.com/sns/latest/dg/sns-fifo-topics.html · "ensure strict message ordering and deduplication" ⚠️근거없음 |
| QU.dedup | FIFO만: 5분 창 | — | fifo-message-dedup · "within the five minute deduplication interval, is accepted but not delivered" |
| QU.retention | **보존 없음**(즉시 전달). 표준 토픽 아카이브는 N/A, FIFO만 아카이브·재생. 메시지 최대 256 KiB(확장 라이브러리로 2 GB). FIFO 과금 설명에는 최대 1 MiB 언급 | — | https://docs.aws.amazon.com/general/latest/gr/sns.html · "The maximum message size is 262,144 bytes (256 KiB)." · "ArchivePolicy … Standard topics: N/A / FIFO topics: Yes" / https://aws.amazon.com/sns/pricing/ · "up to 1 MiB" (FIFO 과금 문구) |
| QU.retry_dlq | SQS·Lambda 대상: 23일에 걸쳐 100,015회. HTTP/S 기본: 3회(정책으로 최대 100회, 총 3,600초 이내). 구독별 DLQ | — | sns-message-delivery-retries · "Total attempts: 100,015 times, over 23 days" · "numRetries … 0 to 100 Default: 3" · "cannot be greater than 3,600 seconds" |
| QU.throughput | 서울 계정당 Publish: 표준 1,500 메시지/초, FIFO 3,000(조정 가능). FIFO 그룹당 300 | — | sns.html · "Asia Pacific (Seoul) Region … 1,500 messages per second | 3,000 messages per second" |
| QU.consumer_scaling | 해당 없음(구독 대상이 확장. 보통 SNS→SQS→워커) | — | 해당 없음 |
| QU.availability / QU.regions / QU.cost_floor | 서울 있음 / $0 고정비. 서울 표준 API $0.50/백만, HTTP 전달 10만 건 무료 후 $0.06/10만, SQS·Lambda 전달 무료. FIFO $0.36/백만 + $0.0204/GB | — | Price List https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonSNS/current/ap-northeast-2/index.json · "$0.50 per 1,000,000 Amazon SNS API Requests" · "$0.06 per 100,000 Amazon SNS HTTP/HTTPS Notifications" · "$0.36 per 1,000,000 SNS FIFO Publish API Requests in Asia Pacific (Seoul)" |

### 비용 구조
고정비 0. 64KB 단위 과금.

### 교체 계열 정보
`@aws-sdk/client-sns`, `boto3`. 인스턴스 간 캐시 무효화 전파(B4)에 쓰려면 인스턴스마다 SQS 큐를 구독시켜야 해서 번거롭고, 보통 Redis pub/sub가 더 단순합니다.

### 함정
SNS 단독으로는 큐가 아닙니다. 구독자가 내려가 있으면 재시도 후 사라지므로 SNS→SQS 팬아웃으로 씁니다.

---

## Amazon EventBridge — 이벤트 버스
- 계열: 큐 (이벤트 라우팅)
- 서울 리전: 있음 (쿼터 표에 ap-northeast-2 값 존재)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| QU.delivery | 최소 1회로 보고 설계(재시도 기반). 재시도 소진 시 버림(DLQ 선택) | "at-least-once" 문구는 버스 문서에서 미확인 | https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-retry-policy.html · "If an event isn't delivered after all retry attempts are exhausted, the event is dropped" |
| QU.ordering | 미확인 | — | 미확인 |
| QU.dedup | 새 Custom Event Bus: 중복 제거 창 300초 고정. Classic: 미확인 | — | https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-quota.html · "Deduplication window | Not configurable | 300 seconds" |
| QU.retention | 버스 자체는 보존 안 함(아카이브 선택, 새 버스 보존 1~365일). 이벤트 크기 256 KB(64KB 단위 과금) | 256 KB 수치는 이번에 연 쿼터 페이지에서 미확인 | eb-quota · "StorageConfiguration.RetentionPeriodInDays | 1 to 365 days" / https://aws.amazon.com/eventbridge/pricing/ · "Each 64 KB chunk counts as one billable event" |
| QU.retry_dlq | Classic 규칙 대상 기본: 24시간, 185회. 새 버스: 기본 5회, 최대 185회, 기본 최대 나이 300초 | — | eb-rule-retry-policy · "By default, EventBridge retries sending the event for 24 hours and up to 185 times" / eb-quota · "RetryPolicy.MaxRetryAttempts | 0 to 185, default 5" |
| QU.throughput | 서울 PutEvents 600 TPS, 호출 1,100/초(조정 가능). 규칙당 대상 5 | — | eb-quota · "ap-northeast-2: 600 per second" · "ap-northeast-2: 1,100 per second" |
| QU.consumer_scaling | 해당 없음(대상이 Lambda·SQS 등) | — | 해당 없음 |
| QU.availability / QU.regions / QU.cost_floor | 서울 있음 / $0 고정비. 커스텀 이벤트 $1.00/백만, AWS 관리 이벤트 무료 | 요금은 페이지 기준(리전 미표기) | https://aws.amazon.com/eventbridge/pricing/ · "$1.00/M" · "AWS management events are ingested by the event bus for free." |

### 비용 구조
고정비 0. 아카이브는 $0.10/GB 처리 + $0.023/GB-월.

### 교체 계열 정보
`@aws-sdk/client-eventbridge` `PutEvents`. 작업 큐 대체가 아니라 서비스 간 이벤트 라우팅용입니다.

### 함정
2026년에 새 "Custom Event Bus"와 "Custom Event Bus - Classic"이 나뉘어 기본 재시도(5회 vs 185회)가 다릅니다. 어느 버스인지 먼저 확인합니다.

---

## Google Cloud Pub/Sub
- 계열: 큐 (pub/sub, 스트림)
- 서울 리전: 있음(전역 서비스, 기본은 게시자와 가까운 리전에 저장. 저장 정책으로 제한 가능) (https://docs.cloud.google.com/pubsub/docs/resource-location-restriction · "Pub/Sub automatically stores the messages in the nearest Google Cloud region")

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| QU.delivery | 기본 최소 1회. 정확히 1회는 pull 구독 + 같은 리전 연결에서만(push·export 미지원, 지연 증가) | 정확히 1회 처리량: us-central1 외 180,000 메시지/분 | https://docs.cloud.google.com/pubsub/docs/exactly-once-delivery · "The exactly-once delivery guarantee only applies when subscribers connect to the service in the same region." · "Push and export subscriptions don't support exactly-once delivery." / https://docs.cloud.google.com/pubsub/quotas |
| QU.ordering | 순서 키 안에서 순서(같은 리전에서 게시해야 함). 재전달 시 뒤 메시지도 함께 재전달. 키당 1 MBps | 키가 다르면 순서 없음 | https://docs.cloud.google.com/pubsub/docs/ordering · "you must publish all messages with the same ordering key in the same region" · "The publishing throughput on each ordering key is limited to 1 MBps." |
| QU.dedup | 정확히 1회 구독을 켰을 때만. 게시 쪽 중복 제거 ID는 미확인 | — | exactly-once-delivery |
| QU.retention | 구독 미확인 메시지 기본 7일(10분~31일). 토픽 보존 최대 31일. 메시지 최대 10 MB | 확인한 메시지 보존은 추가 비용 | https://docs.cloud.google.com/pubsub/docs/subscription-properties (기본 7일, 10분~31일) / https://docs.cloud.google.com/pubsub/quotas · "10MB (the data field)" · "up to 31 days from the time of publication" |
| QU.retry_dlq | ack 기한 기본 10초, 최대 600초. 재시도: 즉시 또는 지수 백오프(최대 600초). DLQ 최대 전달 시도 5~100(기본 5). 구독은 31일 비활성 시 만료(기본) | — | subscription-properties · ack 기한 "10–600 seconds" · "the longest backoff duration that you can specify is 600 seconds" · 만료 "Default value = 31 days" / https://docs.cloud.google.com/pubsub/docs/handling-failures (기본 5, 최대 100) |
| QU.throughput | 리전 크기별 게시 200 MB/s~4 GB/s | — | quotas 페이지 |
| QU.consumer_scaling | KEDA `gcp-pubsub` 스케일러가 있다는 것은 일반 지식(이번에 미확인). Cloud Run push 구독은 요청 기반 확장 | — | 미확인 ⚠️근거없음 |
| QU.availability / QU.regions / QU.cost_floor | 서울 저장 가능 / **$0 고정비.** 월 10 GiB 무료, 이후 $40/TiB(모든 리전). 요청당 최소 1,000바이트 과금. 보존 저장 $0.27/GiB-월 | — | https://cloud.google.com/pubsub/pricing · "the first 10 GiB of throughput … is free. After that, the price is $40 per TiB in all Google Cloud regions." · "Storage costs of $0.27 per GiB-month" |

### 비용 구조
고정비 0. 작은 메시지는 1KB 최소 과금이라 배치로 보내는 편이 쌉니다.

### 교체 계열 정보
Node `@google-cloud/pubsub`, Python `google-cloud-pubsub`, Go `cloud.google.com/go/pubsub`. Cloud Run 워커는 push 구독(HTTP)으로 받으면 상시 워커가 필요 없지만 이때는 정확히 1회를 쓸 수 없습니다.

### 함정
- ack 기한 최대 600초. 그보다 긴 작업은 기한을 연장(클라이언트 라이브러리의 lease 관리)해야 합니다.
- 31일 동안 비활성인 구독은 기본으로 사라집니다.

---

## Google Cloud Tasks
- 계열: 큐 (HTTP 작업 디스패치)
- 서울 리전: 있음 (https://docs.cloud.google.com/tasks/docs/locations · "asia-northeast3 | Seoul, South Korea")

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| QU.delivery | 최소 1회. 드물게 여러 번 실행 → 핸들러 멱등 필요 | — | https://docs.cloud.google.com/tasks/docs/dual-overview · "Cloud Tasks is designed to provide 'at least once' delivery" |
| QU.ordering | 미확인(문서에 순서 보장 문구 없음) | — | 미확인 |
| QU.dedup | 작업 이름으로 중복 제거. 삭제·실행 후 최대 24시간 같은 이름 거부. 이름을 쓰면 지연 증가 | — | https://docs.cloud.google.com/tasks/docs/quotas · "Up to 24 hours" / https://docs.cloud.google.com/tasks/docs/creating-http-target-tasks · "the processing necessary for this can add increased latency" |
| QU.retention | 작업 최대 31일 보관, 예약 최대 30일 후. 작업 최대 1 MiB | — | quotas · "31 days" · "30 days from current date and time" · 1 MiB |
| QU.retry_dlq | 큐별 재시도 설정. HTTP 대상 디스패치 기한 기본 10분, 최대 30분. DLQ 없음(미확인) | — | creating-http-target-tasks · "the default timeout is 10 minutes, with a maximum of 30 minutes" |
| QU.throughput | 큐당 최대 500 작업/초 디스패치 | 큐 여러 개로 분산 | quotas · "500 tasks per second per queue" |
| QU.consumer_scaling | HTTP 푸시라 대상(Cloud Run 등)이 요청 기반으로 확장. 큐가 디스패치 속도·동시성으로 백프레셔 | — | (위 문서 근거, 동시성 설정 상세 미확인) |
| QU.availability / QU.regions / QU.cost_floor | 서울 있음 / $0 고정비. 월 100만 작업 무료, 이후 $0.40/백만(32 KB 단위) | — | https://cloud.google.com/tasks/pricing · "0 count to 1,000,000 count $0.00 (Free)" · "$0.40 / 1,000,000 count" · "Billable operations (chunked at 32 KB)" |

### 비용 구조
고정비 0.

### 교체 계열 정보
Node `@google-cloud/tasks`, Python `google-cloud-tasks`. OIDC 토큰으로 Cloud Run 핸들러 인증. FastAPI `BackgroundTasks`/응답 후 작업(A4) → Cloud Tasks에 HTTP 작업 생성 + 별도 내부 엔드포인트가 Cloud Run 요청 기반 과금에서 가장 작은 변경입니다.

### 함정
30분 넘는 작업은 HTTP 대상으로 처리할 수 없습니다(Cloud Run Jobs 등으로 분리).

---

## Kafka — Amazon MSK (Provisioned / Serverless)
- 계열: 큐 (로그 스트림)
- 서울 리전: 있음 (https://docs.aws.amazon.com/msk/latest/developerguide/serverless.html · "MSK Serverless is available in … Asia Pacific (Seoul)")

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| QU.delivery | 기본 최소 1회. 멱등 프로듀서 + 트랜잭션 + read_committed로 Kafka 안에서 정확히 1회. 외부 시스템까지는 협조 필요 | — | https://kafka.apache.org/42/design/design/ · "Kafka guarantees at-least-once delivery by default" · "exactly-once delivery for other destination systems generally requires cooperation with such systems" ⚠️출처확인필요 |
| QU.ordering | 파티션 안 순서 | 일반 Kafka 설계(같은 문서) | 같은 문서 ⚠️출처확인필요 |
| QU.dedup | 멱등 프로듀서(프로듀서 재전송 중복만) | — | 같은 문서 ⚠️출처확인필요 |
| QU.retention | 설정 가능(Serverless 최대 무제한). 메시지 최대: Serverless 8 MiB, Provisioned는 브로커 설정(기본값 미확인) | — | https://docs.aws.amazon.com/msk/latest/developerguide/limits.html · "Maximum retention duration | Unlimited" · "Maximum message size | 8 MiB" |
| QU.retry_dlq | 브로커 기능 없음. 컨슈머가 오프셋 커밋·재시도 토픽·DLQ 토픽을 직접 구현 | — | 일반 원칙(출처 미확인) ⚠️근거없음 |
| QU.throughput | Serverless 클러스터당 입력 200 MBps, 출력 400 MBps, 파티션당 5/10 MBps, 연결 3,000. Provisioned IAM 연결 브로커당 3,000(t3는 연결 생성 4/초) | — | limits.html · "Maximum ingress throughput | 200 MBps" · "Maximum number of client connections | 3000" · "4 per second (t3 instance size)" |
| QU.consumer_scaling | 파티션 수가 컨슈머 병렬도의 상한. KEDA kafka 스케일러(랙 기반)는 이번에 미확인 | — | 미확인 ⚠️근거없음 |
| QU.availability / QU.regions / QU.cost_floor | 서울 있음 / Provisioned kafka.t3.small $0.0569/브로커-시간(3브로커 ≈ $125/월 + 스토리지 $0.114/GB-월). Serverless $0.92/클러스터-시간(≈ $672/월) + $0.0018/파티션-시간 | t3는 개발·저처리량용 | Price List https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonMSK/current/ap-northeast-2/index.json · "$0.0569 per broker hour for Kafka.t3.small in Asia Pacific (Seoul)" · "$0.92 per cluster-hour for serverless cluster in Asia Pacific (Seoul)" / https://docs.aws.amazon.com/msk/latest/developerguide/broker-instance-sizes.html · "Use T3 brokers for low-cost development" |

### 비용 구조
Serverless는 이름과 달리 클러스터 시간 고정비가 있어 서울 최소 약 $672/월입니다. 3브로커 수는 고가용 배치 관례에 따른 계산이며 문서 문구는 미확인입니다.

### 교체 계열 정보
Node `kafkajs`(유지보수 상태 미확인) 또는 `@confluentinc/kafka-javascript`, Python `confluent-kafka`, Java 공식 클라이언트. MSK Serverless는 IAM 인증 필수.

### 함정
작업 큐 대체로는 과잉입니다(메시지 단위 재시도·지연·DLQ가 없음). 이벤트 스트림·재처리가 요구일 때만 후보입니다.

---

## Kafka — Confluent Cloud (요약)
- 계열: 큐 (로그 스트림)
- 서울 리전: 미확인

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| QU.delivery | Kafka 의미론(MSK와 같음) | — | https://kafka.apache.org/42/design/design/ ⚠️출처확인필요 |
| QU.ordering | 파티션 안 순서 | — | 같은 문서 ⚠️출처확인필요 |
| QU.dedup | 멱등 프로듀서 | — | 같은 문서 ⚠️출처확인필요 |
| QU.retention | Basic 저장 한도 5 TB, Standard 이상 무한 저장 | — | https://www.confluent.io/confluent-cloud/pricing/ · "5 TB storage limit" · "Infinite storage" ⚠️출처확인필요 |
| QU.retry_dlq | 컨슈머 구현 | — | 일반 원칙(출처 미확인) ⚠️근거없음 |
| QU.throughput | eCKU 단위 자동 확장 | 수치 미확인 | 같은 가격 페이지 · "All tiers offer autoscaling" ⚠️출처확인필요 |
| QU.consumer_scaling | 미확인 | — | 미확인 |
| QU.availability / QU.regions / QU.cost_floor | SLA Basic 99.5% / 리전 미확인 / Basic $0부터(첫 eCKU 무료, 이후 $0.14/eCKU-시간, 전송 $0.05/GB), Standard 약 $385/월부터 | — | 같은 가격 페이지 · "Starting at $0/Month" · "Starting at ~$385/Month" ⚠️출처확인필요 |

### 비용 구조
소량이면 Basic이 MSK보다 쌉니다.

### 교체 계열 정보
Kafka 프로토콜이라 클라이언트는 MSK와 같고 인증 방식(API 키, SASL/PLAIN)만 다릅니다.

### 함정
리전·데이터 위치(서울)를 확인하지 못했습니다.

---

## Redis Streams (Redis/Valkey 위의 스트림)
- 계열: 큐
- 서울 리전: 아래에 놓는 Redis를 따름(ElastiCache·Memorystore 서울 있음, Upstash 없음)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| QU.delivery | 컨슈머 그룹 + XACK로 최소 1회. ack 전 메시지는 PEL에 남음 | 내구성은 Redis 영속성·복제를 따름(비동기 복제 → 페일오버 유실 가능) | https://redis.io/docs/latest/develop/pubsub/ · "Messages in streams are persisted, and support both at-most-once as well as at-least-once" / https://redis.io/docs/latest/develop/data-types/streams/ |
| QU.ordering | 스트림 안 ID 순서 | — | streams 문서 |
| QU.dedup | 없음 | — | streams 문서(기능 없음) |
| QU.retention | `MAXLEN`/`XTRIM`으로 직접 자름. 메모리가 한도 | 값 512 MB 한도는 Redis 공통 | streams 문서 (`XADD … MAXLEN ~ 1000`) |
| QU.retry_dlq | `XAUTOCLAIM`/`XCLAIM`으로 죽은 컨슈머 메시지 회수, 전달 횟수 카운터로 독 메시지 식별. DLQ는 직접 구현 | — | streams 문서 (XAUTOCLAIM, delivery counter) |
| QU.throughput | 단일 스레드 Redis 한도 | 수치 미확인 | 미확인 ⚠️근거없음 |
| QU.consumer_scaling | KEDA `redis-streams` 스케일러(대기 항목 수 기반) | — | https://keda.sh/docs/2.21/scalers/redis-streams/ (considerations 02에서 인용, 이번에 재확인 안 함 → 미확인) ⚠️출처확인필요 |
| QU.availability / QU.regions / QU.cost_floor | Redis를 따름 / 같음 / Redis 비용(캐시 계열 표) | — | 캐시 계열 표 참조 |

### 비용 구조
이미 Redis가 있으면 추가 비용이 없습니다.

### 교체 계열 정보
ioredis/redis-py의 `xadd`, `xreadgroup`, `xack`, `xautoclaim`. 보통 직접 쓰기보다 BullMQ·Celery 같은 라이브러리를 씁니다.

### 함정
퇴출 정책이 `volatile-lru`/`allkeys-lru`인 캐시용 Redis에 두면 스트림이 퇴출될 수 있습니다(TTL이 없으면 volatile은 퇴출하지 않지만 메모리 가득 시 쓰기 오류).

---

## BullMQ (Node, Redis 기반)
- 계열: 큐 (작업 큐 라이브러리)
- 서울 리전: Redis를 따름

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| QU.delivery | 최소 1회. 락 갱신 실패 시 stalled로 판정해 다른 워커가 재처리 | CPU를 오래 잡는 작업은 stalled가 됨 | https://docs.bullmq.io/guide/workers/stalled-jobs · "A stalled job is moved back to the waiting status and will be processed again by another worker" ⚠️출처확인필요 |
| QU.ordering | 기본 FIFO(우선순위·지연 지원). 엄격한 보장 문구는 미확인 | — | 미확인 ⚠️근거없음 |
| QU.dedup | 사용자 지정 jobId: 큐에 같은 ID가 있으면 무시. **제거된(removeOnComplete) 작업은 중복으로 보지 않음** | — | https://docs.bullmq.io/guide/jobs/job-ids · "if you add a job with an existing id then that job will just be ignored" · "Jobs that are removed from the queue … will not be considered as duplicates" ⚠️출처확인필요 |
| QU.retention | Redis 메모리가 한도. 완료·실패 작업 자동 제거 권장 | — | https://docs.bullmq.io/guide/going-to-production (auto-removal 권장) ⚠️출처확인필요 |
| QU.retry_dlq | attempts + backoff 설정. 최대 stall 초과 시 failed 집합(DLQ 역할) | 기본값 미확인 | stalled-jobs 문서 · "if it has reached its maximum number of stalls, it will be moved to the failed set" ⚠️출처확인필요 |
| QU.throughput | Redis 한도 | 미확인 | 미확인 ⚠️근거없음 |
| QU.consumer_scaling | 워커 프로세스를 늘림. 큐 길이 기반 오토스케일은 외부(KEDA 등)로 | — | 미확인 ⚠️근거없음 |
| QU.availability / QU.regions / QU.cost_floor | Redis를 따름 / 같음 / 라이브러리 무료(Pro 유료판 가격 미확인) + Redis 비용 | — | — |

### 비용 구조
Redis 비용만. 큐 전용 Redis는 `noeviction`이어야 하므로 캐시와 따로 두면 Redis가 2개가 됩니다.

### 교체 계열 정보
- 응답 뒤 `setTimeout`/await 안 한 Promise → `queue.add(name, data, { jobId, attempts, backoff })` + 별도 `Worker` 프로세스(Procfile `worker:`).
- ioredis 연결에 `maxRetriesPerRequest: null` 필수, SIGTERM 시 `worker.close()`.
- 반복 작업은 Job Scheduler(`upsertJobScheduler`)로 node-cron 대체 가능(인스턴스 수와 무관하게 하나만 생성).

### 함정
- **`maxmemory-policy noeviction`이 아니면 동작이 깨집니다.** ElastiCache 기본(`volatile-lru`)과 서버리스(고정 `volatile-lru`), Memorystore 기본(`volatile-lru`)은 그대로 쓰면 안 됩니다.
- 영속성은 AOF(약 1초)를 권장합니다. 영속 없는 Redis면 재시작 시 큐가 비워집니다.
- `upsertJobScheduler`는 "마지막 작업이 처리되기 시작할 때만 다음 작업을 생성"하므로 작업이 밀리면 실행이 건너뛰어집니다.

출처: https://docs.bullmq.io/guide/going-to-production · "maxmemory-policy setting to noeviction" / https://docs.bullmq.io/guide/job-schedulers · "The scheduler will only generate new jobs when the last job begins processing" · 2026-10-01 ⚠️출처확인필요

---

## Celery (Python) — 브로커별: RabbitMQ / Redis / SQS
- 계열: 큐 (작업 큐 라이브러리)
- 서울 리전: 브로커를 따름

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| QU.delivery | **기본은 실행 직전 ack → 최대 1회**(워커가 죽으면 그 작업은 다시 실행되지 않음). `acks_late=True`면 실행 후 ack → 최소 1회(멱등 필요). 워커 비정상 종료 재전달은 `task_reject_on_worker_lost` | — | https://docs.celeryq.dev/en/stable/userguide/tasks.html · "a task invocation that already started is never executed again" · "messages for this task will be acknowledged after the task has been executed" ⚠️출처확인필요 |
| QU.ordering | 보장 안 함(브로커·동시성에 따름, 문구 미확인) | — | 미확인 ⚠️근거없음 |
| QU.dedup | 없음. SQS FIFO 브로커면 `MessageDeduplicationId` 전달 | — | https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/sqs.html (FIFO 속성 요구) ⚠️출처확인필요 |
| QU.retention | 브로커를 따름(SQS 최대 14일 등) | — | — |
| QU.retry_dlq | `max_retries` 기본 3, `default_retry_delay` 180초. Redis 브로커 가시성 타임아웃 기본 1시간: ETA/countdown이 이보다 길면 **반복 재실행**. SQS 브로커 가시성 기본 30분(최대 12시간) | — | tasks.html (max_retries 3, 180초) / https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html · "The default visibility timeout for Redis is 1 hour." · "it will be executed again, and again in a loop" ⚠️출처확인필요 |
| QU.throughput | 브로커를 따름 | — | — |
| QU.consumer_scaling | 워커 수 확장(KEDA는 브로커 큐 길이 기준) | — | 미확인 ⚠️근거없음 |
| QU.availability / QU.regions / QU.cost_floor | 브로커를 따름 / 같음 / 라이브러리 무료 + 브로커 비용 | 브로커 상태: RabbitMQ·Redis·SQS 모두 Stable, SQS는 모니터링·원격 제어 없음 | https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/index.html · "Amazon SQS | Stable | No | No" ⚠️출처확인필요 |

### 비용 구조
브로커 비용. SQS 브로커면 고정비 0(빈 큐 폴링 요청 과금 주의).

### 교체 계열 정보
- FastAPI `BackgroundTasks` → `@celery.task` + `task.delay()` + 워커 프로세스 분리. 가벼운 대안: RQ, arq(asyncio), Dramatiq(출처 미확인). ⚠️근거없음
- Redis 브로커: 퇴출 정책 `noeviction` 또는 `allkeys-lru`가 아니면 키 소실로 `InconsistencyError` 가능(문서 권고).
- 결과 백엔드가 필요하면 별도(SQS에는 결과 백엔드 없음).
- celery beat는 프로세스 1개만(스케줄러 계열 참고).

### 함정
- 기본 ack가 "실행 전"이라 배포 중 워커가 죽으면 작업이 조용히 사라집니다. 반대로 `acks_late`를 켜면 중복 실행이 생깁니다. 둘 중 무엇을 택했는지가 판정 포인트입니다.
- Redis 브로커 + 1시간 넘는 ETA = 무한 재실행.

---

## Sidekiq (Ruby, Redis 기반)
- 계열: 큐 (작업 큐 라이브러리)
- 서울 리전: Redis를 따름

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| QU.delivery | **OSS: BRPOP으로 꺼내므로 처리 중 크래시하면 작업 영구 유실.** Pro `super_fetch`는 완료 전까지 Redis에 보관해 회수(회수 시점 5분~3시간) | — | https://github.com/sidekiq/sidekiq/wiki/Reliability · "If Sidekiq crashes while processing that job, it is lost forever." ⚠️출처확인필요 |
| QU.ordering | 미확인 | — | 미확인 |
| QU.dedup | OSS 없음(Enterprise unique jobs는 미확인) | — | 미확인 ⚠️근거없음 |
| QU.retention | Redis 메모리. Dead set 기본 10,000개 또는 6개월 | — | https://github.com/sidekiq/sidekiq/wiki/Error-Handling · "The Dead set is limited by default to 10,000 jobs or 6 months" ⚠️출처확인필요 |
| QU.retry_dlq | 기본 25회, 약 20일에 걸쳐 재시도 후 Dead set | — | Error-Handling · "Sidekiq will perform 25 retries over approximately 20 days." ⚠️출처확인필요 |
| QU.throughput | 단일 Redis로 2만+ 작업/초 사례 | — | https://github.com/sidekiq/sidekiq/wiki/Using-Redis · "20,000+ jobs/sec with a single Redis instance" ⚠️출처확인필요 |
| QU.consumer_scaling | 프로세스·스레드 확장 | — | 미확인 ⚠️근거없음 |
| QU.availability / QU.regions / QU.cost_floor | Redis를 따름 / 같음 / OSS 무료, Pro·Enterprise 가격 미확인 | — | 미확인 |

### 비용 구조
Redis 비용(+ Pro 라이선스, 미확인).

### 교체 계열 정보
Redis는 캐시가 아닌 영속 저장소로 따로 둬야 합니다(`noeviction`). 재시도가 길어 작업이 멱등이어야 합니다.

### 함정
OSS Sidekiq을 그대로 여러 인스턴스로 늘리면 배포·축소 때마다 처리 중 작업이 사라질 수 있습니다(F4).

출처: https://github.com/sidekiq/sidekiq/wiki/Using-Redis · "it's important that Sidekiq be run against a Redis instance that is not configured as a cache but as a persistent store" · 2026-10-01 ⚠️출처확인필요

---

## Postgres 기반 큐 — `FOR UPDATE SKIP LOCKED`, pg-boss(Node)
- 계열: 큐
- 서울 리전: 쓰는 Postgres를 따름

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| QU.delivery | 작업 행을 잠그고 처리 후 커밋. 업무 쓰기와 **같은 트랜잭션으로 넣을 수 있음**(아웃박스 불필요). 처리 결과의 외부 부수효과는 최소 1회로 설계 | pg-boss "exactly-once" 문구는 README에서 확인 못 함 → 미확인 | https://www.postgresql.org/docs/current/sql-select.html · "can be used to avoid lock contention with multiple consumers accessing a queue-like table" / https://github.com/timgit/pg-boss · "job processing gets the safety of guaranteed atomic commits" ⚠️출처확인필요 |
| QU.ordering | `ORDER BY` + 우선순위. SKIP LOCKED는 일관되지 않은 뷰(엄격한 순서 아님) | — | sql-select · "Skipping locked rows provides an inconsistent view of the data" |
| QU.dedup | 유니크 제약(직접) / pg-boss singleton·debounce 정책 | — | https://github.com/timgit/pg-boss (README 기능 목록) ⚠️출처확인필요 |
| QU.retention | DB 저장 용량 한도. 정리(archival) 필요 | — | — ⚠️근거없음 |
| QU.retry_dlq | pg-boss: 지수 백오프 재시도, DLQ + redrive | — | pg-boss README · "dead letter queues with redrive, automatic retries with exponential backoff" ⚠️출처확인필요 |
| QU.throughput | DB 쓰기 처리량 한도. 폴링이 DB 부하·연결을 씀 | 수치 미확인 | 미확인 ⚠️근거없음 |
| QU.consumer_scaling | 워커 수 확장(연결 수 C8 한도 주의) | — | — ⚠️근거없음 |
| QU.availability / QU.regions / QU.cost_floor | DB를 따름 / 같음 / **추가 고정비 $0**(기존 DB 사용) | pg-boss: Node 22.12+, PostgreSQL 13+ | pg-boss README · "Node 22.12 or higher, or Bun" ⚠️출처확인필요 |

### 비용 구조
이미 Postgres가 있으면 새 구성 요소가 필요 없어 가장 싸고 운영이 단순합니다.

### 교체 계열 정보
Node pg-boss(cron 스케줄도 클러스터당 1회), Python은 Procrastinate·Django-Q 등(출처 미확인), Ruby Solid Queue·GoodJob, Elixir Oban, Go River(모두 출처 미확인). 직접 구현: `SELECT … FOR UPDATE SKIP LOCKED LIMIT n`. ⚠️근거없음

### 함정
- Supabase 트랜잭션 풀러(PgBouncer transaction mode)에서는 LISTEN/NOTIFY·advisory lock 기반 기능이 제한될 수 있습니다(01 파일 DS.connections 참고, 이 파일에서는 미확인).
- 처리량이 높아지면 테이블 bloat와 vacuum이 병목입니다.

---

## Inngest (서버리스 내구 함수)
- 계열: 큐 (이벤트 기반 작업 실행)
- 서울 리전: 미확인 (문서에 리전 언급 없음)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| QU.delivery | 단계(step) 단위 재시도로 내구 실행. 함수 기본 재시도 4회(최대 20) | 전달 보장 명칭 미확인 | https://www.inngest.com/docs/features/inngest-functions/error-retries/retries · "The default is four retries after the initial attempt." ⚠️출처확인필요 |
| QU.ordering | 미확인 | — | 미확인 |
| QU.dedup | 이벤트 ID 24시간, 함수 idempotency 키 24시간 | — | https://www.inngest.com/docs/guides/handling-idempotency · "Event IDs will only be used to prevent duplicate execution for a 24 hour period." ⚠️출처확인필요 |
| QU.retention | 이벤트 최대: Free 256 KiB, Pro 이상 3 MiB. 단계 출력 4 MiB. 함수 실행 최대 Free 30일, Pro 90일 | — | https://www.inngest.com/docs/usage-limits/inngest ⚠️출처확인필요 |
| QU.retry_dlq | 단계 재시도. 단계 타임아웃 최대 2시간(호스트 타임아웃에 종속) | — | 같은 문서 ⚠️출처확인필요 |
| QU.throughput | 동시 단계: Free 5, Pro 100, Business 500. 월 이벤트 Free 50만 | — | 같은 문서 / https://www.inngest.com/pricing · "5 included" ⚠️출처확인필요 |
| QU.consumer_scaling | 플랫폼이 HTTP로 내 함수(서버리스)를 호출 → 플랫폼 확장을 따름 | — | (구조 설명, 문구 미확인) ⚠️근거없음 |
| QU.availability / QU.regions / QU.cost_floor | 미확인 / 미확인 / Free 월 5만 실행, Pro $99/월부터 | — | https://www.inngest.com/pricing · "50k /mo included" · "$99 /mo" ⚠️출처확인필요 |

### 비용 구조
Free로 시작 가능. 동시 5단계 한도가 실제 병목입니다.

### 교체 계열 정보
`inngest` SDK(TS, Python, Go). 핸들러에서 `inngest.send(event)`, 작업은 `createFunction` + `step.run`. Vercel 등 서버리스에서 응답 후 작업(A4)·긴 작업(A2)을 쪼개는 용도.

### 함정
단계 하나의 실행 시간은 결국 호스트 플랫폼(Vercel 함수 등)의 최대 실행 시간에 묶입니다.

---

## Trigger.dev (관리형 작업 실행)
- 계열: 큐 (작업 실행 플랫폼, 자체 컴퓨트)
- 서울 리전: 미확인

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| QU.delivery | 미확인 | — | 미확인 |
| QU.ordering | 미확인 | — | 미확인 |
| QU.dedup | 미확인(idempotency key 기능 문서 미확인) | — | 미확인 |
| QU.retention | 페이로드 3 MB, 출력 10 MB(128 KB 넘으면 객체 저장소로 오프로드). 실행 TTL 최대 14일 | — | https://trigger.dev/docs/limits · "Must not exceed 3MB" · "Must not exceed 10MB" ⚠️출처확인필요 |
| QU.retry_dlq | 미확인 | — | 미확인 |
| QU.throughput | 동시 실행 Free 10, Hobby 25, Pro 100+. 스케줄 Free 10, Hobby 100, Pro 1,000+ | — | trigger.dev/docs/limits · "10 concurrent runs" ⚠️출처확인필요 |
| QU.consumer_scaling | 플랫폼이 컨테이너를 띄워 실행(내 서버 불필요) | — | 미확인(문구) ⚠️근거없음 |
| QU.availability / QU.regions / QU.cost_floor | 미확인 / 미확인 / Free $0(월 $5 크레딧), Hobby $10, Pro $50. 컴퓨트 초당 과금(Micro $0.0000169/초) + 실행당 $0.000025 | — | https://trigger.dev/pricing · "$5 / month free credits" · "$0.25 per 10,000 runs" ⚠️출처확인필요 |

### 비용 구조
작업 컴퓨트를 Trigger.dev가 제공하므로 서버리스 실행 시간 한도를 피할 수 있습니다.

### 교체 계열 정보
`@trigger.dev/sdk`의 `task()` 정의 + `tasks.trigger()`. 코드가 Trigger.dev 쪽에서 배포·실행됩니다(별도 배포 파이프라인).

### 함정
로그 보존 Free 1일. 데이터가 외부 플랫폼에서 실행되므로 F5(민감 데이터) 검토가 필요합니다.

---

## Upstash QStash (HTTP 메시지 큐·스케줄러)
- 계열: 큐
- 서울 리전: **없음.** EU, US 두 리전만(SDK 기본 EU)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| QU.delivery | 최소 1회(HTTP 푸시) | — | https://upstash.com/docs/qstash/features/retry (at-least-once) ⚠️출처확인필요 |
| QU.ordering | 미확인 | — | 미확인 |
| QU.dedup | `Upstash-Deduplication-Id` 또는 내용 기반. 창 10분 | — | https://upstash.com/docs/qstash/features/deduplication · "The deduplication window is 10 minutes." ⚠️출처확인필요 |
| QU.retention | 메시지 최대 Free 1 MB, PAYG 10 MB, Fixed 50 MB. 지연 PAYG 최대 1년. DLQ 보존 Free 3일, PAYG 7일 | — | https://upstash.com/docs/qstash/overall/pricing ⚠️출처확인필요 |
| QU.retry_dlq | 기본 3회, `min(86400, e^(2.5n))`초 백오프. 재시도도 메시지로 과금. DLQ 있음 | — | https://upstash.com/docs/qstash/features/retry · "By default, we retry a failed delivery 3 times." ⚠️출처확인필요 |
| QU.throughput | Free 하루 1,000 메시지 | — | pricing 문서 · "1,000" ⚠️출처확인필요 |
| QU.consumer_scaling | HTTP 푸시 → 대상 플랫폼 확장 | — | — ⚠️근거없음 |
| QU.availability / QU.regions / QU.cost_floor | 미확인 / EU·US / Free $0, PAYG $1/10만 메시지, Fixed 1M $180/월 | — | https://upstash.com/docs/qstash/howto/multi-region · "EU region" "US region" / pricing 문서 · "$1 per 100K messages" ⚠️출처확인필요 |

### 비용 구조
고정비 0. 재시도마다 메시지 1건 과금.

### 교체 계열 정보
`@upstash/qstash`(`publishJSON`, `Receiver`로 서명 검증), Python `qstash`. 스케줄(크론) 기능도 있어 Vercel Hobby 크론 제약 우회에 쓰입니다(스케줄 기능 상세 미확인).

### 함정
서울 리전이 없어 메시지가 EU/US를 거쳐 돌아옵니다(지연·데이터 위치).

---

## Vercel Queues (베타)
- 계열: 큐
- 서울 리전: 있음(19개 리전에서 선택. icn1 포함) (https://vercel.com/docs/regions · "icn1 | ap-northeast-2 | Seoul, South Korea")

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| QU.delivery | 최소 1회. 3개 AZ 동기 복제 후 응답. 소비자 타임아웃·AZ 페일오버 때 중복 가능 | **공개 베타** | https://vercel.com/docs/queues/concepts · "Vercel Queues provides at-least-once delivery semantics." · "synchronously written to three separate availability zones" / https://vercel.com/docs/queues · "(Beta)" |
| QU.ordering | 대략적 쓰기 순서. FIFO 보장 없음. 재시도 메시지는 새 메시지보다 뒤 | — | concepts · "No FIFO guarantee." |
| QU.dedup | 멱등키: 원본 메시지 수명(TTL) 동안 중복 제거(최대 7일) | 멱등키 send는 2배 과금 | concepts · "The deduplication window lasts for the entire lifetime of the original message (up to its TTL)." |
| QU.retention | TTL 기본 24시간, 60초~7일. 메시지 최대 100 MB. 지연 최대 7일 | 4 KiB 단위 과금 | https://vercel.com/docs/queues/pricing (Limits 표) |
| QU.retry_dlq | 가시성 타임아웃 기본 60초, 최대 60분. 재시도 무제한(기본, `maxDeliveries`로 제한). **내장 DLQ 없음** | 실패 배포가 TTL 동안 계속 재시도·과금 | concepts · "Vercel Queues doesn't have a built-in dead-letter queue." · "maxDeliveries | Unlimited" |
| QU.throughput | 자동 확장(수치 없음). 그룹당 최대 동시성 무제한(기본) | — | pricing Limits · "Max concurrency per consumer group | 1 | Unlimited | Unlimited" |
| QU.consumer_scaling | push 모드: Vercel 함수가 자동 호출(Fluid compute). poll 모드: 외부 워커 | — | concepts (Delivery) |
| QU.availability / QU.regions / QU.cost_floor | 3 AZ / 19개 리전(서울 포함), 리전 장애 시 인근 리전에 임시 저장(엄격한 데이터 상주 미지원) / 고정비 0, Hobby 월 100만 operation 포함, 단가는 리전별 | — | concepts · "Strict data residency … is not supported yet." / pricing · "First 1,000,000" |

### 비용 구조
operation 과금 + push 소비자 함수 컴퓨트. 타임아웃으로 실패한 전달은 함수 `maxDuration` 전체가 과금됩니다.

### 교체 계열 정보
`@vercel/queue`(`send`, `handleCallback`), Python `vercel-queue`. 소비자는 `vercel.json`의 `experimentalTriggers: [{ type: "queue/v2beta", topic }]`. Vercel 문서에 Celery를 Vercel Queues 위에서 돌리는 가이드가 있습니다(상세 미확인).

### 함정
- 토픽이 배포 ID로 분리되어, 롤백해도 이전 배포의 소비자가 메시지 TTL 동안 계속 실행됩니다(배포 삭제로 중단).
- 베타라 SLA·가격이 바뀔 수 있습니다.

---

# 파트 4. 스케줄러

앱 프로세스 안 스케줄러(현재 상태)는 파트 1에 있다.

## Kubernetes CronJob
- 계열: 스케줄러
- 서울 리전: 클러스터를 따름 (EKS·GKE 서울 있음, 01·05 파일)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| SC.frequency | 최소 1분(cron 5필드) | `timeZone` 필드 지원 | https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/ (Schedule Syntax: minute 0-59) |
| SC.semantics | "실행 시각마다 대략 1회": 드물게 **두 번 또는 0번.** `concurrencyPolicy` 기본 `Allow`(이전 실행이 안 끝나도 새로 시작). 놓친 일정이 100개를 넘으면 더 이상 일정 잡지 않음. `startingDeadlineSeconds`로 늦은 시작 허용 범위 | 재시도는 Job의 `backoffLimit` | 같은 문서 · "Allow (default)" · "Jobs may run twice or not at all in rare circumstances" · "If more than 100 scheduled times are missed" |
| SC.target | 컨테이너 Job(실행 시간 제한 없음, `activeDeadlineSeconds`로 설정) | — | 같은 문서 |
| SC.cost_floor | 클러스터 비용(EKS 컨트롤 플레인 등, 05 파일). 실행 중 Pod 자원 | — | 05 파일 참조 |

### 비용 구조
클러스터가 이미 있으면 추가 고정비 없음.

### 교체 계열 정보
node-cron 본문을 별도 엔트리포인트(`node jobs/daily.js`)로 빼서 같은 이미지로 CronJob 실행. `concurrencyPolicy: Forbid` + 멱등 처리.

### 함정
기본 `Allow`라 느린 작업이 쌓이면 동시에 여러 개가 돕니다.

---

## Google Cloud Scheduler
- 계열: 스케줄러
- 서울 리전: 있음 (https://docs.cloud.google.com/scheduler/docs/locations · "asia-northeast3 | Seoul, South Korea")

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| SC.frequency | 최소 1분(unix-cron). 최소 주기 문구는 문서에서 미확인 | 프로젝트·리전당 잡 5,000 | https://docs.cloud.google.com/scheduler/quotas · "Number of jobs (per region): 5000" |
| SC.semantics | 최소 1회. 드물게 여러 번 실행. `X-CloudScheduler-ScheduleTime` 헤더로 실행 식별. 재시도는 재시도 설정(횟수·백오프) | 누락에 대한 문구 미확인 | https://docs.cloud.google.com/scheduler/docs/overview · "Cloud Scheduler is designed to provide 'at least once' delivery" · "in some rare circumstances, it is possible for a job to run multiple times" |
| SC.target | HTTP/S, Pub/Sub, App Engine. HTTP 대상 실행 최대 30분(초과 시 타임아웃 후 재시도). 페이로드 1 MB | OIDC/OAuth 토큰 첨부 가능 | quotas · "Job duration … 30 minutes" · "1 MB total" |
| SC.cost_floor | 결제 계정당 월 3잡 무료, 이후 잡당 $0.10/31일(실행 횟수 무관) | — | https://cloud.google.com/scheduler/pricing · "Each Google billing account gets 3 jobs per month free." · "A job is billed $0.10/job/31 days" |

### 비용 구조
사실상 무료~수 달러.

### 교체 계열 정보
APScheduler/node-cron → Cloud Scheduler HTTP 잡 + Cloud Run 엔드포인트(OIDC 검증, `--no-allow-unauthenticated`) + 실행 창 유니크 키. 30분 넘는 작업은 Cloud Run Jobs를 트리거.

### 함정
Cloud Run 요청 기반 과금에서 엔드포인트가 응답한 뒤 백그라운드로 계속 처리하면 CPU가 없습니다(A4). 작업이 끝난 뒤 응답해야 합니다.

---

## Amazon EventBridge Scheduler
- 계열: 스케줄러
- 서울 리전: 있음(쿼터 표의 "기타 리전" 값 적용. 서울 엔드포인트 문구는 이번에 미확인)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| SC.frequency | rate(분 단위)·cron(분 단위)·일회성. 정밀도 60초(1:00이면 1:00:00~1:00:59) | IANA 시간대·DST 처리 | https://docs.aws.amazon.com/scheduler/latest/UserGuide/schedule-types.html · "All schedule types on EventBridge Scheduler invoke their targets with 60 second precision." |
| SC.semantics | 최소 1회. 재시도 횟수·최대 보존 시간 설정, DLQ. DST 봄 전환 때 존재하지 않는 시각은 **건너뜀** | 기본 재시도 값(185회/24시간)은 이번에 연 페이지에서 미확인 | https://docs.aws.amazon.com/scheduler/latest/UserGuide/what-is-scheduler.html · "EventBridge Scheduler provides at-least-once event delivery to targets" / schedule-types · "your schedule invocation is skipped" |
| SC.target | 템플릿 대상(SQS, SNS, Lambda, EventBridge) + 범용 대상 270개 서비스·6,000개 API. 입력 페이로드 256 KB. HTTP 엔드포인트 직접 호출은 미확인(API destination 경유 여부 미확인) | 기타 리전 호출 500 TPS | what-is-scheduler · "target more than 270 AWS services and over 6,000 API operations" / https://docs.aws.amazon.com/scheduler/latest/UserGuide/scheduler-quotas.html · "The maximum size of a target's Input payload is 256 KB." |
| SC.cost_floor | 월 1,400만 호출 무료, 이후 $1.00/백만 | — | https://aws.amazon.com/eventbridge/pricing/ · "14,000,000 invocations per month for free" |

### 비용 구조
일반 크론 사용량은 무료 범위.

### 교체 계열 정보
node-cron → EventBridge Scheduler → (ECS RunTask 또는 Lambda 또는 SQS) → 작업. 컨테이너 앱이면 SQS에 메시지를 넣고 워커가 처리하는 방식이 단순합니다.

### 함정
일회성 스케줄은 실행 후에도 쿼터에 남으므로 `ActionAfterCompletion`으로 삭제합니다.

---

## Vercel Cron Jobs — Hobby / Pro / Enterprise
- 계열: 스케줄러
- 서울 리전: 해당 없음(대상 함수의 리전을 따름)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| SC.frequency | **Hobby: 하루 1회, 정밀도 ±59분**(시간 단위). Pro·Enterprise: 분당 1회, 분 단위 정밀도. 모든 플랜 프로젝트당 100개 | Hobby에서 더 잦은 식은 배포 실패 | https://vercel.com/docs/cron-jobs/usage-and-pricing · "Hobby | 100 cron jobs | Once per day | Per-hour (±59 min)" · "Pro | 100 cron jobs | Once per minute | Per-minute" |
| SC.semantics | **최선 노력: 누락 가능, 같은 실행 중복 가능, 실패해도 재시도 안 함.** 이전 실행이 안 끝나면 겹쳐 실행 가능 | 리다이렉트를 따라가지 않음 | https://vercel.com/docs/cron-jobs/manage-cron-jobs · "Cron job delivery is best effort." · "can also occasionally invoke the same scheduled run more than once" · "Vercel will not retry an invocation if a cron job fails." |
| SC.target | 프로덕션 배포의 함수 경로(GET). 실행 시간 = 함수 `maxDuration`. `CRON_SECRET`이 Authorization 헤더로 전달 | — | manage-cron-jobs · "The duration limits for Cron jobs are identical to those of Vercel Functions." |
| SC.cost_floor | 모든 플랜 포함(함수 사용량만 과금) | Hobby는 비상업 용도 제한(01 README 확인 사항) | usage-and-pricing · "Cron jobs are included in all plans." |

### 비용 구조
크론 자체는 무료, 함수 실행 비용만.

### 교체 계열 정보
`vercel.json`의 `crons: [{ path, schedule }]` + 라우트에서 `Bearer ${CRON_SECRET}` 검증 + Redis 락(동시 실행 방지) + 마지막 성공 이후 미처리분을 처리하는 조정형 로직(누락 대비).

### 함정
- Hobby에서 "매시간" 같은 요구는 표현할 수 없습니다(QStash·외부 스케줄러로 우회).
- 누락이 공식적으로 가능하므로 "정확히 그 시각 1회"가 필요한 작업(정산 등)은 조정형으로 바꿔야 합니다.

---

## Supabase Cron (pg_cron)
- 계열: 스케줄러
- 서울 리전: 있음(DB 안에서 실행, 프로젝트 리전을 따름. Supabase 서울은 02 파일)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| SC.frequency | 매초 ~ 연 1회(pg_cron `[1-59] seconds` 간격) | Supabase 권고: 동시 실행 8개 이하, 작업당 10분 이하 | https://supabase.com/docs/guides/cron · "can run anywhere from every second to once a year" / https://github.com/citusdata/pg_cron · "[1-59] seconds" ⚠️출처확인필요 |
| SC.semantics | 작업마다 한 번에 하나만 실행: 이전 실행이 안 끝나면 다음 실행은 **대기 후 실행**(중복 동시 실행 없음). DB 하나에서 돌므로 앱 인스턴스 수와 무관. 재시도 없음(미확인) | `cron.max_running_jobs` 기본 32, 시간대 GMT 기본 | pg_cron README · "only one instance of each specific job at a time" · "it's queued and starts as soon as the first one completes" ⚠️출처확인필요 |
| SC.target | SQL, DB 함수, HTTP(pg_net, Edge Functions 호출) | 실행 이력 `cron.job_run_details` | https://supabase.com/docs/guides/cron |
| SC.cost_floor | 추가 비용 없음(DB 자원 사용) | — | 해당 없음 ⚠️근거없음 |

### 비용 구조
DB 플랜에 포함.

### 교체 계열 정보
`select cron.schedule('name', '*/5 * * * *', $$ select net.http_post(...) $$)`. 앱 프로세스 크론 → DB 크론으로 옮기면 인스턴스 수에 따른 중복이 사라집니다. 일반 RDS/Cloud SQL에서도 pg_cron 확장 지원 여부를 확인(01 파일).

### 함정
`cron.job_run_details`가 계속 쌓이므로 정리 작업이 필요합니다(Supabase 문서 권고, 상세 미확인).

---

## Cloudflare Cron Triggers
- 계열: 스케줄러
- 서울 리전: 해당 없음(전역 네트워크)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| SC.frequency | 분 단위 cron(UTC). 계정당 Free 5개, Paid 250개 | 변경 전파 최대 15분 | https://developers.cloudflare.com/workers/configuration/cron-triggers/ · "Cron Triggers execute on UTC time." · "may take several minutes (up to 15 minutes) to propagate" / https://developers.cloudflare.com/workers/platform/limits/ |
| SC.semantics | 미확인(중복·누락·재시도 의미론이 문서에 명시되지 않음. `noRetry()` API 존재) | — | cron-triggers 문서(`controller.noRetry()`) |
| SC.target | Worker `scheduled` 핸들러. CPU 시간 Free 10ms, Paid는 주기 1시간 미만 30초 / 1시간 이상 15분. 벽시계 최대 15분 | — | https://developers.cloudflare.com/workers/platform/limits/ |
| SC.cost_floor | Free $0, Paid $5/월 최소 | — | (Workers Paid 최소 $5, 캐시 계열 KV 항목 출처) |

### 비용 구조
Workers 요금에 포함.

### 교체 계열 정보
`export default { scheduled(controller, env, ctx) { … } }` + `wrangler` `triggers.crons`. 내 백엔드를 HTTP로 호출하는 외부 스케줄러로 쓸 수 있습니다.

### 함정
Free의 CPU 10ms로는 작업 자체를 돌리기 어렵고 HTTP 호출 트리거 정도만 가능합니다.

---

## GitHub Actions `schedule`
- 계열: 스케줄러
- 서울 리전: 해당 없음

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| SC.frequency | 최소 5분 | IANA 시간대 지원 | https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows · "The shortest interval you can run scheduled workflows is once every 5 minutes." |
| SC.semantics | **고부하 때 지연, 충분히 높으면 드롭(누락).** 매시 정각이 고부하. 공개 저장소는 60일 활동 없으면 자동 비활성화. 기본 브랜치 최신 커밋에서 실행 | 중복 실행 방지는 `concurrency` 설정 | 같은 문서 · "If the load is sufficiently high enough, some queued jobs may be dropped." · "scheduled workflows are automatically disabled when no repository activity has occurred in 60 days" |
| SC.target | 러너에서 임의 스크립트(HTTP 호출 등) | 잡 최대 실행 시간 미확인 | — ⚠️근거없음 |
| SC.cost_floor | 공개 저장소 표준 러너 무료. 비공개는 Free 플랜 월 2,000분, Linux 2코어 $0.006/분 | — | https://docs.github.com/en/billing/concepts/product-billing/github-actions · "In public repositories" · "2,000" · "$0.006" |

### 비용 구조
대부분 무료.

### 교체 계열 정보
운영 크론 대체로는 부적합(누락 가능). 백업 검증·리포트 같은 비핵심 작업에만.

### 함정
"매시 정각" 스케줄은 가장 붐비는 시간이라 지연·누락이 잦습니다.

---

# 파트 5. 실시간 연결

## Socket.IO — 어댑터 없음 (기본 인메모리 어댑터)
- 계열: 실시간 (현재 상태로 자주 나옴)
- 서울 리전: 해당 없음(앱 서버를 따름)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| RT.connections | 서버 프로세스 자원 한도(라이브러리 한도 없음, 수치 미확인). 연결 지속은 플랫폼 CP.long_connection을 따름 | — | 미확인 |
| RT.fanout | **같은 서버 프로세스에 붙은 클라이언트에게만 전파.** 2대 이상이면 방(room) 브로드캐스트가 일부에만 감 | B4 불일치의 근거 | https://socket.io/docs/v4/adapter/ · "when scaling to multiple Socket.IO servers, you will need to replace the default in-memory adapter by another implementation" ⚠️출처확인필요 |
| RT.limits | HTTP long-polling을 쓰면 **스티키 세션 필수.** WebSocket 전용(`transports: ["websocket"]`)이면 스티키 불필요 | — | https://socket.io/docs/v4/using-multiple-nodes/ (long-polling은 여러 HTTP 요청, WebSocket은 단일 TCP 연결) ⚠️출처확인필요 |
| RT.cost_floor | $0(앱 서버 비용) | — | 해당 없음 ⚠️근거없음 |

### 비용 구조
추가 비용 없음.

### 교체 계열 정보
같은 계열 안에서는 어댑터만 추가하면 됩니다(아래). 관리형으로 바꾸면 서버는 REST로 게시하고 클라이언트 SDK가 바뀝니다.

### 함정
`gunicorn`/`pm2 -i max`/Node cluster로 프로세스만 늘려도 같은 문제가 생깁니다.

---

## Socket.IO — Redis 어댑터 / Redis Streams 어댑터
- 계열: 실시간
- 서울 리전: Redis를 따름

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| RT.connections | 앱 서버 수 × 서버당 연결 | 수치 미확인 | 미확인 ⚠️근거없음 |
| RT.fanout | Redis pub/sub로 다른 서버에 전달. Redis 7 샤드 pub/sub용 `createShardedAdapter`. **Redis 연결이 끊긴 동안 다른 서버로 가는 패킷은 유실.** Streams 어댑터는 재연결 후 이어받아 유실 없음, 연결 상태 복구 지원(maxLen 기본 10,000) | 공식 어댑터: Redis, Redis Streams, MongoDB, Postgres, Cluster, GCP Pub/Sub, AWS SQS, Azure Service Bus | https://socket.io/docs/v4/redis-adapter/ · "packets will only be sent to the clients that are connected to the current server" (Redis 끊김 시) / https://socket.io/docs/v4/redis-streams-adapter/ · "This adapter will properly handle any temporary disconnection to the Redis server and resume the stream without losing any packets" ⚠️출처확인필요 |
| RT.limits | 어댑터를 써도 long-polling이면 스티키 세션 필수(아니면 HTTP 400) | — | redis-streams-adapter 문서(스티키 세션 필요) ⚠️출처확인필요 |
| RT.cost_floor | Redis 비용(캐시 계열 표) | — | — ⚠️근거없음 |

### 비용 구조
Redis 1대 추가. 캐시 Redis와 같이 써도 되지만 pub/sub 출력 버퍼 한도(32 MB 하드)를 고려합니다.

### 교체 계열 정보
```js
import { createAdapter } from "@socket.io/redis-adapter";
io.adapter(createAdapter(pubClient, subClient));
```
+ LB 스티키 세션(ALB 대상 그룹 stickiness, nginx `ip_hash`) 또는 클라이언트 `transports: ["websocket"]`. 방 목록·온라인 사용자 같은 서버 메모리 상태는 Redis로 옮겨야 합니다(B1).

### 함정
- 서버리스(Lambda, Vercel 함수)에는 맞지 않습니다. 장시간 연결을 유지할 컴퓨트가 필요합니다(CP.long_connection).
- Cloud Run은 요청 타임아웃(최대 60분)마다 재연결됩니다(컴퓨트 표).

---

## Supabase Realtime (Broadcast / Presence / Postgres Changes)
- 계열: 실시간
- 서울 리전: 있음(프로젝트 리전, 02 파일)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| RT.connections | 동시 연결: **Free 200, Pro 500**, Pro(지출 상한 해제)·Team 10,000, Enterprise 10,000+ | 연결당 채널 100 | https://supabase.com/docs/guides/realtime/limits (표: Concurrent connections 200 / 500 / 10,000) |
| RT.fanout | 관리형 채널(서버가 전파). 앱 인스턴스 수와 무관 | — | 같은 문서 |
| RT.limits | 초당 메시지 Free 100, Pro 500, 지출 상한 해제 2,500. 채널 조인/초 같은 비율. Broadcast 페이로드 Free 256 KB, Pro 이상 3,000 KB. Postgres Changes 페이로드 1,024 KB(넘으면 64바이트 이하 필드만) | — | 같은 문서 |
| RT.cost_floor | 플랜 포함(Free 동시 200·월 200만 메시지, Pro 500·500만). 초과: 피크 연결 1,000개당 $10, 메시지 백만당 $2.50 | Free는 초과 과금 없이 차단 | https://supabase.com/docs/guides/realtime/pricing · "$10 per 1,000 peak connections" · "$2.50 per 1 million messages" |

### 비용 구조
Pro 기본 500 연결. 지출 상한을 켜 둔 Pro는 500을 넘을 수 없습니다.

### 교체 계열 정보
`@supabase/supabase-js`의 `supabase.channel('room').on('broadcast', …).subscribe()`, 서버에서는 REST/서버 SDK로 broadcast. Socket.IO 방 → 채널, emit → `channel.send({ type: 'broadcast' })`.

### 함정
"Pro"라도 지출 상한이 켜져 있으면 동시 연결 500이 상한입니다. A3(장시간 연결)·D2가 크면 플랜 설정까지 확인해야 합니다.

---

## Firebase Realtime Database 리스너 (요약)
- 계열: 실시간
- 서울 리전: **없음**(us-central1, europe-west1, asia-southeast1만) (https://firebase.google.com/docs/database/locations)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| RT.connections | DB 인스턴스당 동시 연결 200,000(Spark 100,000) | 넘으면 샤딩(DB 인스턴스 추가) | https://firebase.google.com/docs/database/usage/limits · "Simultaneous connections: 200,000" |
| RT.fanout | DB 값 변경을 리스너에 전파(관리형) | — | 같은 문서 |
| RT.limits | 쓰기 1,000/초, 쓰기량 64 MB/분, SDK 단일 쓰기 16 MB | — | 같은 문서 · "Write rate: 1,000 writes/second" |
| RT.cost_floor | 미확인(가격 페이지 미열람) | — | 미확인 |

### 비용 구조
미확인.

### 교체 계열 정보
Firestore 스냅샷 리스너의 연결 한도는 이번에 확인하지 못했습니다(quotas 페이지에 없음, 미확인).

### 함정
서울 리전이 없어 싱가포르 왕복 지연이 생깁니다.

---

## Pusher Channels
- 계열: 실시간 (관리형 pub/sub WebSocket)
- 서울 리전: **없음.** 공개 클러스터 중 가장 가까운 곳은 ap3(도쿄)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| RT.connections | Sandbox(무료) 100, Startup 500, Pro 2,000, Business 5,000 … Growth Plus 30,000 | — | https://pusher.com/channels/pricing/ ⚠️출처확인필요 |
| RT.fanout | 서버가 HTTP API로 trigger → 관리형 전파. 한 trigger에 채널 100개 | 배치 10개/호출 | https://pusher.com/docs/channels/library_auth_reference/rest-api/ ⚠️출처확인필요 |
| RT.limits | 이벤트 데이터 10 KB(초과 413). 일 메시지 Sandbox 20만, Startup 100만 | — | rest-api 문서 · "The event data should not be larger than 10KB." / pricing ⚠️출처확인필요 |
| RT.cost_floor | Sandbox $0, Startup $49/월, Pro $99/월 | — | https://pusher.com/channels/pricing/ ⚠️출처확인필요 |

### 비용 구조
연결 수 계단식 고정 요금.

### 교체 계열 정보
서버 `pusher`(Node)/`pusher`(Python) `trigger(channel, event, data)`, 클라이언트 `pusher-js`. 비공개 채널은 서버 인증 엔드포인트 필요.

### 함정
10 KB 메시지 한도. 서울 리전 없음(https://pusher.com/docs/channels/miscellaneous/clusters/ · "ap3 in Tokyo"). ⚠️출처확인필요

---

## Ably
- 계열: 실시간
- 서울 리전: 미확인

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| RT.connections | Free 200, Standard 10,000, Pro 50,000, Enterprise 무제한. 신규 연결/초 Free 42, Standard 250 | — | https://ably.com/docs/platform/pricing/limits ⚠️출처확인필요 |
| RT.fanout | 관리형 채널. Realtime 클라이언트로 게시 시 채널 안 순서 보장. 멱등 게시로 정확히 1회 | REST 게시는 순서 문제 가능 | https://ably.com/docs/platform/architecture/message-ordering · "Ably delivers messages to persistently connected subscribers on a channel in the order they were published" ⚠️출처확인필요 |
| RT.limits | 메시지 Free 64 KiB, Pro 256 KiB. 연결당 송수신 50 메시지/초. 연결 상태 TTL 2분 | — | ably limits 문서 ⚠️출처확인필요 |
| RT.cost_floor | Free(월 600만 메시지). Standard $29/월 + 메시지 $2.50/백만 + 연결 $1.00/백만 분 | — | https://ably.com/pricing · "$29 / month" ⚠️출처확인필요 |

### 비용 구조
기본료 + 사용량.

### 교체 계열 정보
`ably` SDK(Node, Python 등). 서버 REST 게시, 클라이언트 토큰 인증.

### 함정
리전·데이터 위치 미확인.

---

## AWS API Gateway WebSocket API
- 계열: 실시간
- 서울 리전: 있음 (Price List 서울 항목 존재)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| RT.connections | 동시 연결 한도 없음. 신규 연결 계정·리전당 500/초(조정 가능) → 2시간이면 최대 360만 | — | https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-execution-service-websocket-limits-table.html · "API Gateway doesn't enforce a quota on concurrent connections." |
| RT.fanout | **브로드캐스트 없음.** 백엔드가 연결 ID를 저장(DynamoDB 등)하고 `@connections` POST로 하나씩 보냄 | — | https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-websocket-api-overview.html · "You can use the @connections API to send a POST request." |
| RT.limits | **연결 최대 2시간, 유휴 10분**(코드 1001). 프레임 32 KB, 메시지 128 KB. 통합 타임아웃 29초 | — | limits-table · "Connection duration for WebSocket API | 2 hours" · "Idle Connection Timeout | 10 minutes" · "WebSocket frame size | 32 KB" |
| RT.cost_floor | 고정비 0. 서울 메시지 $1.14/백만(첫 10억), 연결 $0.285/백만 분 | 32 KB 단위 과금 여부 미확인 | Price List https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonApiGateway/current/ap-northeast-2/index.json · "$1.14/million messages - first 1 billion messages/month" · "$0.285/million connection minutes" |

### 비용 구조
고정비 0. 연결 1,000개를 한 달 유지하면 약 4,380만 분 ≈ $12.5(계산).

### 교체 계열 정보
Socket.IO 프로토콜과 호환되지 않습니다. 클라이언트는 표준 WebSocket, 서버는 Lambda `$connect`/`$disconnect`/`$default` 라우트 + 연결 테이블 + `ApiGatewayManagementApi.postToConnection`. 방 개념은 직접 구현.

### 함정
2시간마다 강제 종료, 10분 유휴 종료 → 클라이언트 재연결·하트비트 필수.

---

## AWS AppSync (GraphQL 구독 / Event API)
- 계열: 실시간
- 서울 리전: 있음 (https://docs.aws.amazon.com/general/latest/gr/appsync.html · "Asia Pacific (Seoul) | ap-northeast-2 | appsync-realtime-api.ap-northeast-2.amazonaws.com")

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| RT.connections | 동시 연결 상한 미확인. 연결 요청 API당 2,000/초(조정 가능). 연결당 구독 200 | — | appsync.html · "Rate of connections per API | Each supported Region: 2,000 per second" |
| RT.fanout | 관리형 팬아웃. 외부 발신 메시지 API당 1,000,000/초(5 KB 단위) | — | appsync.html · "Rate of outbound messages per API | 1,000,000 per second" |
| RT.limits | GraphQL 구독 페이로드 240 KB. Event API 게시 1.2 MB, 연결당 게시 25/초, 배치 5 | 연결 지속 한도 미확인 | appsync.html · "Subscription payload size | 240 Kilobytes" · "Publish payload size | 1.2 Megabytes" |
| RT.cost_floor | 고정비 0. 서울 실시간 업데이트 $2/백만, 연결 $0.08/백만 분, Event API 작업 $1/백만 | — | Price List https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSAppSync/current/ap-northeast-2/index.json · "$2 per million real-time updates in Asia Pacific (Seoul)" · "$0.08 per million minutes of connection" |

### 비용 구조
고정비 0. 연결 분 단가가 API Gateway WebSocket보다 낮습니다($0.08 vs $0.285/백만 분).

### 교체 계열 정보
Event API: 서버가 HTTP로 채널에 게시, 클라이언트는 Amplify `events.connect('/default/room')`. Socket.IO 방 → 채널 네임스페이스/세그먼트(최대 5단계).

### 함정
AWS 인증 모델(API 키, Cognito, IAM, Lambda 권한 부여) 연동이 필요합니다.

---

## Cloudflare Durable Objects (WebSocket Hibernation)
- 계열: 실시간
- 서울 리전: 보장 없음. 위치 힌트 `apac-ne` 등은 최선 노력, 첫 `get()` 요청 근처에 생성

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| RT.connections | 객체당 연결 상한 미확인. 객체 수 제한 없음 → 방마다 객체 하나로 분산 | 객체당 소프트 한도 1,000 요청/초 | https://developers.cloudflare.com/durable-objects/platform/limits/ · "An individual Object has a soft limit of 1,000 requests per second." |
| RT.fanout | 같은 객체(방)에 붙은 소켓에 객체가 직접 전파. 객체 간 전파는 직접 구현 | — | https://developers.cloudflare.com/durable-objects/best-practices/websockets/ |
| RT.limits | 수신 메시지 32 MiB. CPU 요청당 기본 30초(최대 5분). Hibernation 중 duration 과금 없음 | — | limits 문서 · "32 MiB (only for received messages)" / websockets 문서 · "Billable Duration (GB-s) charges do not accrue during hibernation" |
| RT.cost_floor | Free(SQLite 백엔드만, 일 10만 요청). Paid $5/월 최소, 요청 백만 포함 후 $0.15/백만, 수신 WebSocket 메시지는 20:1로 요청 환산 | — | https://developers.cloudflare.com/durable-objects/platform/pricing/ · "20:1 ratio is applied to incoming WebSocket messages" |

### 비용 구조
Hibernation을 쓰면 유휴 연결이 거의 무료입니다.

### 교체 계열 정보
Socket.IO 서버 → Worker가 `idFromName(roomId)`로 객체에 라우팅, 객체에서 `state.acceptWebSocket(ws)` + `webSocketMessage` 핸들러. 클라이언트는 표준 WebSocket(Socket.IO 클라이언트 호환 안 됨, 미확인).

### 함정
위치는 힌트일 뿐이라 한국 사용자 방이 다른 지역에 생길 수 있습니다(https://developers.cloudflare.com/durable-objects/reference/data-location/ · "Hints are a best effort and not a guarantee.").

---

# 파트 6. 파일 저장소

컨테이너 로컬 디스크(현재 상태)는 파트 1에 있다.

## Amazon S3 — S3 Standard (범용 버킷)
- 계열: 파일 저장소
- 서울 리전: 있음 (Price List 서울 "$0.025 per GB - first 50 TB / month of storage used")

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| FS.durability | 99.999999999% 설계, 최소 3개 AZ에 저장(One Zone-IA·Express One Zone 제외) | — | https://docs.aws.amazon.com/AmazonS3/latest/userguide/DataDurability.html · "across a minimum of three Availability Zones" · "Designed to provide 99.999999999% durability" |
| FS.consistency | PUT·DELETE 후 강한 읽기 일관성(LIST 포함). 같은 키 동시 쓰기는 마지막 쓰기 승리, 객체 잠금 없음(조건부 쓰기 `If-None-Match`로 덮어쓰기 방지 가능). 버킷 설정은 최종 일관성 | — | https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html · "strong read-after-write consistency for PUT and DELETE requests" · "Amazon S3 does not support object locking for concurrent writers." |
| FS.shared_access | 가능(HTTP API, 모든 인스턴스·서버리스) | — | 같은 문서 |
| FS.object_limits | **객체 최대 약 50 TB(48.8 TiB)**, 단일 PUT 5 GB, 멀티파트 5 MiB~5 GiB 파트 × 최대 10,000, 100 MB 이상이면 멀티파트 권장. 서명 URL 최대 7일(CLI/SDK), 콘솔 12시간 | 임시 자격 증명으로 서명하면 그 만료가 먼저 옴(문서 문구 미확인) | https://docs.aws.amazon.com/AmazonS3/latest/userguide/upload-objects.html · "you can upload a single object up to 5 GB" · "up to 50 TB in size" / https://docs.aws.amazon.com/AmazonS3/latest/userguide/qfacts.html · "Maximum object size | 48.8 TiB" / https://docs.aws.amazon.com/AmazonS3/latest/userguide/ShareObjectPreSignedURL.html · "the maximum expiration time for a presigned URL is 7 days" ⚠️근거없음 |
| FS.versioning_lifecycle | 버전 관리, 수명 주기(전환·만료), Object Lock(WORM), 복제 | 버전 관리 처음 켤 때 15분 대기 권장 | Welcome.html · "S3 Object Lock – Prevent Amazon S3 objects from being deleted or overwritten" · "wait for 15 minutes after enabling versioning" |
| FS.delivery | CloudFront 연동. 서울 인터넷 송신 첫 10 TB $0.126/GB(전역 무료 등급 이후) | — | Price List AWSDataTransfer ap-northeast-2 · "$0.126 per GB - first 10 TB / month data transfer out beyond the global free tier" |
| FS.regions / FS.cost_floor | 서울 있음 / 고정비 $0. 저장 $0.025/GB-월, PUT·COPY·POST·LIST $0.0045/1,000, GET $0.0035/10,000 | — | Price List https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonS3/current/ap-northeast-2/index.json · "$0.0045 per 1,000 PUT, COPY, POST, or LIST requests" · "$0.0035 per 10,000 GET and all other requests" |

### 비용 구조
고정비 0. 비용 대부분은 송신(이그레스)입니다. 미완료 멀티파트 업로드는 수명 주기 규칙으로 정리하지 않으면 계속 과금됩니다(considerations 06).

### 교체 계열 정보
- Node `@aws-sdk/client-s3` + `@aws-sdk/s3-request-presigner`(`getSignedUrl(PutObjectCommand)`), `@aws-sdk/lib-storage`(멀티파트), `multer-s3`. Python `boto3` `generate_presigned_url`/`generate_presigned_post`, `django-storages`. Java/Go AWS SDK.
- `multer.diskStorage` → 서명 URL 발급 API + 브라우저 PUT + 완료 콜백에서 DB에 객체 키 저장.
- R2·GCS(XML API)·Supabase Storage(S3 호환 엔드포인트)도 S3 API로 이식 가능.

### 함정
- 같은 키를 여러 요청이 덮어쓰면 마지막 것이 이깁니다. 사용자 업로드는 키에 UUID를 넣습니다.
- 퍼블릭 액세스 차단이 기본이라 공개 서빙은 CloudFront OAC나 서명 URL로 합니다.

---

## Google Cloud Storage — Standard
- 계열: 파일 저장소
- 서울 리전: 있음 (가격 페이지 위치 목록 "Seoul (asia-northeast3)")

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| FS.durability | 11 nines 설계. 리전 버킷은 최소 2개 존에 저장 후 성공 응답. 이중·멀티 리전 선택 가능 | — | https://docs.cloud.google.com/storage/docs/availability-durability · "designed for at least 99.999999999% (11 9's) annual durability" |
| FS.consistency | 객체 쓰기·메타데이터·삭제 후 읽기, 목록 모두 강한 전역 일관성. 공개 캐시 객체와 IAM 변경(약 1분)은 예외 | — | https://docs.cloud.google.com/storage/docs/consistency · "Cloud Storage provides strong global consistency for the following operations" |
| FS.shared_access | 가능(HTTP API) | — | — ⚠️근거없음 |
| FS.object_limits | 객체 최대 5 TiB. 같은 객체 이름 쓰기 초당 1회. XML 멀티파트 10,000 파트. V4 서명 URL 최대 7일 | — | https://docs.cloud.google.com/storage/quotas · "Maximum object size: 5 TiB" · "One write per second" / https://docs.cloud.google.com/storage/docs/access-control/signed-urls · "The longest expiration value is 604800 seconds (7 days)." |
| FS.versioning_lifecycle | 객체 버전 관리, 수명 주기. **소프트 삭제 기본 7일(7~90일), 삭제된 객체도 보존 기간 동안 저장 과금** | — | https://docs.cloud.google.com/storage/docs/soft-delete · "Soft delete is enabled by default for all buckets … with a default retention duration of 7 days." · "continue to accrue storage charges" |
| FS.delivery | Cloud CDN 연동. 인터넷 송신(아시아 목적지) 0~10 TiB $0.12/GiB | — | https://cloud.google.com/storage/pricing · "Data transfer to Asia Destinations … 0 gibibyte to 10 tebibyte $0.12 / 1 gibibyte" |
| FS.regions / FS.cost_floor | 서울 있음 / 고정비 $0. 단일 리전 Standard 작업 Class A $0.005/1,000, Class B $0.0004/1,000. **서울 저장 단가 미확인**(표가 동적 로딩). Always Free 5 GB-월은 US 3개 리전만 | — | 같은 가격 페이지 · "Standard storage $0.005 $0.0065 $0.0004 $0.0005" · "Always Free quotas apply to usage in US-WEST1, US-CENTRAL1, and US-EAST1 regions" |

### 비용 구조
고정비 0. 임시 파일이 많은 버킷은 소프트 삭제를 끄는 편이 쌉니다.

### 교체 계열 정보
Node `@google-cloud/storage`(`file.getSignedUrl({ version: 'v4', action: 'write' })`), Python `google-cloud-storage`, `django-storages[google]`. Cloud Run에서는 서비스 계정 서명(IAM signBlob) 권한 필요(상세 미확인).

### 함정
같은 객체 이름에 초당 1회 넘게 쓰면 스로틀됩니다(카운터 JSON 같은 용도 금지).

---

## Cloudflare R2
- 계열: 파일 저장소
- 서울 리전: 리전 선택 없음. 위치 힌트 `apac`(최선 노력)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| FS.durability | 11 nines 설계. 지역 내 여러 데이터센터에 복제·이레이저 코딩 | — | https://developers.cloudflare.com/r2/reference/durability/ · "R2 is designed to provide 99.999999999% (eleven 9s) of annual durability." |
| FS.consistency | 쓰기 후 읽기·목록·삭제 강한 전역 일관성. 커스텀 도메인 캐시를 켜면 캐시 TTL 동안 예외 | — | https://developers.cloudflare.com/r2/reference/consistency/ |
| FS.shared_access | 가능(S3 호환 API, Workers 바인딩) | — | — ⚠️근거없음 |
| FS.object_limits | 객체 5 TiB, 단일 업로드 5 GiB, 멀티파트 10,000 파트. 같은 키 동시 쓰기 초당 1회 | — | https://developers.cloudflare.com/r2/platform/limits/ |
| FS.versioning_lifecycle | 수명 주기 규칙 있음(이번에 미확인). 버전 관리 미확인 | — | 미확인 ⚠️근거없음 |
| FS.delivery | **송신(이그레스) 무료.** 커스텀 도메인으로 CDN 캐시 | — | https://developers.cloudflare.com/r2/pricing/ · "Egress (data transfer to Internet)" "Free" |
| FS.regions / FS.cost_floor | 위치 힌트(apac 등, 보장 아님), 관할(eu, fedramp, us) / 고정비 $0. Standard $0.015/GB-월, Class A $4.50/백만, Class B $0.36/백만. 무료 10 GB-월, A 100만, B 1,000만 | — | https://developers.cloudflare.com/r2/reference/data-location/ · "Location Hints are a best effort and not a guarantee" / r2 pricing |

### 비용 구조
송신이 많은 서비스(이미지·영상)에서 S3 대비 비용이 크게 줄어듭니다.

### 교체 계열 정보
S3 호환 엔드포인트(`https://<account>.r2.cloudflarestorage.com`, region `auto`)로 `@aws-sdk/client-s3`·`boto3`를 그대로 사용. 서명 URL도 S3 방식.

### 함정
서울 리전을 지정할 수 없습니다(데이터 위치 요건 F5 확인).

---

## Supabase Storage
- 계열: 파일 저장소
- 서울 리전: 있음(프로젝트 리전을 따름, 02 파일)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| FS.durability | 미확인(내부 저장소 문서 미열람) | — | 미확인 |
| FS.consistency | 같은 경로 동시 업로드: 기본은 첫 번째만 성공(400/409), `x-upsert`면 마지막 완료가 승리. CDN 캐시 무효화 지연 미확인 | — | https://supabase.com/docs/guides/storage/uploads/standard-uploads · "the first uploader succeeds while others get a 400 Asset Already Exists error" |
| FS.shared_access | 가능(HTTP API, RLS로 권한) | — | https://supabase.com/docs/guides/storage/security/access-control (considerations 05 출처, 재확인 안 함) |
| FS.object_limits | 파일 최대 **Free 50 MB**, Pro·Team 500 GB. 표준 업로드는 6 MB 이하 권장, 그 이상은 TUS 재개 업로드(청크 6 MB 고정, 업로드 URL 24시간 유효) | 전역·버킷별 한도 설정 | https://supabase.com/docs/guides/storage/uploads/file-limits / https://supabase.com/docs/guides/storage/uploads/resumable-uploads · "it must be set to 6MB (for now)" |
| FS.versioning_lifecycle | 미확인 | — | 미확인 |
| FS.delivery | 내장 CDN. 공개 버킷이 캐시 적중률 높음(비공개는 사용자별 권한 검사로 미스). Free 대역폭 10 GB(캐시 5 + 비캐시 5) | — | https://supabase.com/docs/guides/storage/cdn/fundamentals · "This leads to a better cache hit rate compared to private buckets." / https://supabase.com/docs/guides/storage/serving/bandwidth · "10 GB of bandwidth (5 GB cached + 5 GB uncached)" |
| FS.regions / FS.cost_floor | 서울 있음 / 플랜 포함: Free 1 GB, Pro 100 GB, 초과 $0.0213/GB-월. Pro 플랜 기본료는 02 파일 | — | https://supabase.com/docs/guides/platform/manage-your-usage/storage-size · "$0.0213 per GB per month" |

### 비용 구조
Pro 플랜에 포함된 100 GB 안에서는 추가 비용 없음.

### 교체 계열 정보
`supabase.storage.from('bucket').upload(path, file)` / `createSignedUploadUrl` / `createSignedUrl`, 큰 파일은 `tus-js-client`·Uppy. S3 호환 엔드포인트로 S3 SDK 사용 가능(상세 미확인).

### 함정
Free 플랜 파일 한도 50 MB. 큰 업로드(A7)가 있으면 플랜이 판정에 들어갑니다.

---

## Vercel Blob
- 계열: 파일 저장소
- 서울 리전: 있음(19개 리전에서 생성 시 선택, icn1 포함. 생성 후 변경 불가)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| FS.durability | 11 nines, 가용성 99.99%(S3 기반) | — | https://vercel.com/docs/vercel-blob · "Vercel Blob offers 99.999999999% (11 nines) durability." · "leverages Amazon S3" |
| FS.consistency | 덮어쓰기·삭제가 CDN 캐시에 전파되는 데 **최대 60초**(+브라우저 캐시). 비공개 blob은 `useCache: false`로 즉시 읽기. 기본은 덮어쓰기 금지(`allowOverwrite`), ETag 조건부 쓰기 지원 | — | 같은 문서 · "the changes may take up to 60 seconds to propagate through our cache" |
| FS.shared_access | 가능(여러 프로젝트가 한 스토어 공유) | — | 같은 문서 |
| FS.object_limits | 파일 최대 5 TB, 100 MB 이상 멀티파트 권장. **서버 업로드는 함수 요청 본문 4.5 MB 한도** → 클라이언트 업로드 사용. 캐시되는 blob 최대 512 MB | 작업 속도 한도 Hobby 고급 15/초, Pro 75/초 | https://vercel.com/docs/vercel-blob/usage-and-pricing · "Maximum File Size: 5TB" · "Cache Size Limit: 512 MB per blob" / https://vercel.com/docs/vercel-blob/server-upload · "Vercel has a 4.5 MB request body size limit on Vercel Functions." |
| FS.versioning_lifecycle | 미확인(버전 관리·수명 주기 언급 없음) | — | 미확인 |
| FS.delivery | Vercel CDN 캐시(기본 최대 1개월). 공개 blob은 직접 URL, 비공개는 함수 경유 | — | vercel-blob 문서 · "caches all blobs (private and public) for up to 1 month by default" |
| FS.regions / FS.cost_floor | 19개 리전 / 고정비 $0. Hobby 무료 1 GB·단순 1만·고급 2,000·전송 10 GB(초과 시 30일 차단). Pro는 리전별 단가(예시 iad1: 저장 $0.023/GB, 고급 작업 $5.00/백만, 전송 $0.05/GB). 서울 단가 미확인 | — | usage-and-pricing (Hobby 포함량, 가격 예시) |

### 비용 구조
비공개 blob은 함수 경유라 Blob 전송 + Fast Data Transfer가 이중으로 붙습니다.

### 교체 계열 정보
`@vercel/blob`의 `put()`(서버), `upload()` + `handleUpload`(클라이언트 업로드 토큰), `get()`, `del()`. Python `vercel.blob`. Vercel 밖에서는 `BLOB_READ_WRITE_TOKEN`.

### 함정
Hobby는 한도를 넘으면 30일 동안 Blob을 쓸 수 없습니다.

---

## Cloud Storage for Firebase
- 계열: 파일 저장소
- 서울 리전: 미확인(새 기본 버킷 위치 선택지 미확인)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| FS.durability | GCS를 따름(위 GCS 항목) | — | GCS availability-durability |
| FS.consistency | GCS를 따름 | — | GCS consistency |
| FS.shared_access | 가능. 클라이언트 SDK 직접 접근은 보안 규칙으로 통제 | — | https://firebase.google.com/docs/storage/security (considerations 05 출처, 재확인 안 함) |
| FS.object_limits | GCS 5 TiB | — | GCS quotas |
| FS.versioning_lifecycle | GCS를 따름 | — | — |
| FS.delivery | GCS 송신 요금 | — | — ⚠️근거없음 |
| FS.regions / FS.cost_floor | 미확인 / **Blaze(종량제) 플랜 필수.** Spark 프로젝트는 Storage 접근이 402/403으로 막힘. 구 `*.appspot.com` 버킷은 Blaze에서도 5 GB 저장·일 1 GB 다운로드 무료, 2024-09 이후 새 버킷(`*.firebasestorage.app`)은 GCS 요금 | — | https://firebase.google.com/docs/storage/faqs-storage-changes-announced-sept-2024 · "No-cost usage is still available even on the Blaze pricing plan." |

### 비용 구조
Blaze 필수(카드 등록), 사용량 과금.

### 교체 계열 정보
웹 `firebase/storage`의 `uploadBytesResumable`, 서버 `firebase-admin`(GCS 클라이언트). GCS로 그대로 이식 가능.

### 함정
무료 Spark 플랜에 머문 프로젝트는 Storage를 쓸 수 없습니다.

---

## Amazon EFS (NFS 공유 파일 시스템)
- 계열: 파일 저장소
- 서울 리전: 있음 (Price List 서울 "USD $0.33 per GB-Mo for Standard storage (APN2)")

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| FS.durability | Regional: 여러 AZ. One Zone: 단일 AZ | — | https://docs.aws.amazon.com/efs/latest/ug/how-it-works.html (Regional·One Zone 설명) |
| FS.consistency | NFSv4.1 파일 시스템 의미론(일관성 상세 문구 미확인) | — | 미확인 ⚠️근거없음 |
| FS.shared_access | **가능.** 여러 AZ의 여러 인스턴스가 동시 마운트(EC2, ECS, Fargate, EKS, Lambda) | VPC 안 마운트 타깃 필요 | how-it-works · "You can access your EFS file system concurrently from multiple NFS clients" |
| FS.object_limits | 파일 크기 한도 미확인. 업로드는 앱이 파일로 씀(서명 URL 없음) | — | 미확인 ⚠️근거없음 |
| FS.versioning_lifecycle | 수명 주기로 IA 전환, AWS Backup | — | how-it-works (AWS Backup) |
| FS.delivery | CDN 직접 연동 없음(앱이 서빙) | — | 해당 없음 ⚠️근거없음 |
| FS.regions / FS.cost_floor | 서울 있음 / 고정비 $0. Standard $0.33/GB-월(S3의 13배), IA $0.0272, Elastic 처리량 읽기 $0.03/GB, 쓰기 $0.07/GB. One Zone $0.176 | — | Price List https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEFS/current/ap-northeast-2/index.json |

### 비용 구조
저장 단가가 S3보다 훨씬 비싸고 읽기·쓰기 처리량도 과금됩니다.

### 교체 계열 정보
코드 변경이 거의 없습니다(`uploads/` 경로를 EFS 마운트로). 그래서 "코드 수정 최소"가 요구일 때의 후보이지만, SQLite를 EFS에 두는 것은 NFS 잠금 문제로 처방이 아닙니다(01 파일).

### 함정
지연이 로컬 디스크보다 큽니다. 작은 파일을 많이 쓰는 워크로드는 느려집니다(수치 미확인).

---

## Google Filestore (NFS)
- 계열: 파일 저장소
- 서울 리전: 있음 (가격 페이지 위치 목록 "Seoul (asia-northeast3)")

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| FS.durability | Basic·Zonal: 단일 존. Regional·Enterprise: 리전(존 장애 대비) | — | https://docs.cloud.google.com/filestore/docs/service-tiers · "Designed for regional availability and resilience against zone outages" |
| FS.consistency | NFS 의미론(상세 미확인) | — | 미확인 ⚠️근거없음 |
| FS.shared_access | 가능(NFSv3, NFSv4.1) | — | service-tiers · "NFSv3, NFSv4.1" |
| FS.object_limits | **최소 용량: Basic HDD 1 TiB, Basic SSD 2.5 TiB**, Zonal·Regional 1 TiB(일부 리전 100 GiB) | — | service-tiers (최소 용량) |
| FS.versioning_lifecycle | 백업, 스냅샷 | — | service-tiers |
| FS.delivery | 해당 없음 | — | — |
| FS.regions / FS.cost_floor | 서울 있음 / Basic HDD 단가 예시 오리건 $0.16/GiB-월 → 1 TiB 최소 ≈ $164/월(미국 리전 계산). 서울 단가 미확인 | 쓰지 않아도 프로비저닝 용량 과금 | https://cloud.google.com/filestore/pricing · "The unit cost for a Basic HDD service tier instance in the Oregon region is $0.16 per GiB per month." |

### 비용 구조
최소 용량 때문에 작은 앱의 업로드 폴더용으로는 과잉입니다.

### 교체 계열 정보
Cloud Run·GKE에 NFS 볼륨으로 마운트(Cloud Run 볼륨 마운트 상세 미확인).

### 함정
"업로드 폴더 공유"만이 요구라면 GCS가 거의 항상 싸고 단순합니다.

---

## 블록 볼륨 다중 연결 제약 — Amazon EBS, GCP Persistent Disk/Hyperdisk, Kubernetes PV 접근 모드
- 계열: 파일 저장소 (제약 정리)
- 서울 리전: 있음(EBS·PD 모두. io1 Multi-Attach는 서울 지원)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| FS.durability | 단일 AZ·존 볼륨(존 장애 시 접근 불가) | 리전 PD 등 예외는 미확인 | https://docs.aws.amazon.com/ebs/latest/userguide/ebs-volumes-multi.html (같은 AZ 제약) |
| FS.consistency | 블록 장치. 여러 호스트가 일반 파일 시스템(ext4, XFS)으로 동시에 쓰면 **데이터 손상** | 클러스터 파일 시스템 필요 | ebs-volumes-multi · "Standard file systems, such as XFS and EXT4, are not designed to be accessed simultaneously by multiple servers" / https://docs.cloud.google.com/compute/docs/disks/sharing-disks-between-vms · "If you use single-instance file systems, such as EXT4, XFS, or NTFS, on a disk in multi-writer mode, you might experience data loss" |
| FS.shared_access | **기본 1대.** EBS Multi-Attach는 io1/io2만, 같은 AZ의 Nitro 인스턴스 최대 16대. GCP 다중 쓰기는 Hyperdisk(Balanced, Balanced HA, Extreme)만 8~16대. 읽기 전용 공유는 PD 여러 대 가능. Kubernetes `ReadWriteOnce`는 **노드 하나**(같은 노드의 여러 Pod는 가능), 여러 노드 쓰기는 `ReadWriteMany`(EFS·Filestore 같은 NFS 계열) | — | ebs-volumes-multi · "can be attached to up to 16 instances built on the Nitro System that are in the same Availability Zone" · "Multi-Attach is supported exclusively on Provisioned IOPS SSD (io1 and io2) volumes" / https://kubernetes.io/docs/concepts/storage/persistent-volumes/ · "ReadWriteOnce - the volume can be mounted as read-write by a single node" |
| FS.object_limits | 해당 없음(볼륨 크기) | — | — |
| FS.versioning_lifecycle | 스냅샷 | — | — ⚠️근거없음 |
| FS.delivery | 해당 없음 | — | — |
| FS.regions / FS.cost_floor | 서울 있음 / 볼륨 GB 단가(이번에 미확인), Multi-Attach 추가 요금 없음 | — | ebs-volumes-multi · "There are no additional charges for using Amazon EBS Multi-Attach." |

### 비용 구조
미확인(볼륨 단가).

### 교체 계열 정보
"디스크를 붙여서 인스턴스를 늘린다"는 처방은 성립하지 않습니다. RWO 볼륨을 쓰는 Deployment는 replicas를 2로 올리면 다른 노드의 Pod가 마운트하지 못해 Pending이 됩니다. 업로드 파일 → 객체 저장소, 공유 POSIX가 꼭 필요하면 EFS/Filestore(RWX).

### 함정
- RWO 볼륨에 SQLite를 두고 replicas를 늘리면 같은 노드에 스케줄된 Pod끼리는 마운트가 되어 오히려 잠금 문제가 숨겨진 채 진행될 수 있습니다.
- 롤링 업데이트에서 새 Pod가 다른 노드에 뜨면 볼륨 분리를 기다리며 배포가 멈춥니다(Recreate 전략 필요).

---

# 7. 판정을 뒤집는 발견

1. **관리형 Redis의 기본 퇴출 정책은 큐에 안전하지 않다.** ElastiCache 노드 기반, ElastiCache Serverless, Memorystore(Redis, Valkey, Cluster)의 기본값은 모두 `volatile-lru`다. 서버리스는 이 값을 바꿀 수도 없다. 반면 BullMQ와 Sidekiq은 `noeviction`을 요구하고, Celery는 `noeviction`이나 `allkeys-lru`를 요구한다. 그래서 "Redis를 붙이면 큐도 해결된다"고 볼 수 없다. 큐 전용 Redis를 따로 두고 파라미터 그룹을 바꾸거나, Postgres 큐나 SQS를 써야 한다. MemoryDB와 자체 운영 Redis만 기본값이 `noeviction`이다.
2. **큐로 옮겨도 내구성이 보장되지 않는다.** 두 가지 경우가 있다.
   - Celery는 기본으로 실행 직전에 ack한다. 그래서 워커가 죽으면 그 작업은 다시 실행되지 않는다(최대 1회).
   - Sidekiq OSS는 BRPOP으로 작업을 꺼내므로 처리 중에 크래시하면 작업이 영구히 사라진다.
   F4(배포 중단 허용)와 C7(데이터 중요도)이 높다면 `acks_late`와 멱등키, 또는 Sidekiq Pro나 다른 큐가 처방에 함께 들어가야 한다.
3. **외부 스케줄러는 모두 "최소 1회"이거나 "최선 노력"이다.** 각각의 성질은 다음과 같다.
   - Vercel Cron: 누락될 수 있고, 중복될 수 있고, 실패해도 재시도하지 않는다. Hobby는 하루 1회이고 시각이 ±59분 어긋난다.
   - GitHub Actions: 부하가 높으면 실행을 드롭한다.
   - Kubernetes CronJob: 드물게 0회 또는 2회 실행되고, 기본값 `Allow`라 실행이 겹친다.
   그래서 B3(단일 실행) 처방은 "스케줄러 교체"만으로 끝나지 않는다. 실행 창 유니크 키나 락, 그리고 조정형 로직이 함께 있어야 한다. 작업당 동시 실행이 1개로 보장되는 것은 pg_cron뿐이다.
4. **서울 리전이 없는 후보가 많다.** Upstash Redis(도쿄), QStash(EU·US), Pusher(도쿄), Firebase RTDB(싱가포르)에는 서울 리전이 없다. R2와 Durable Objects는 위치 힌트만 줄 수 있다. D5(지역)와 F5(데이터 위치) 요구가 있으면 이 후보들은 탈락한다. 서울에 있는 대안은 ElastiCache·Memorystore, SQS·Cloud Tasks, Vercel Queues(icn1), API Gateway WebSocket·AppSync, S3·GCS·Vercel Blob(icn1)이다.
5. **실시간·업로드 한도가 플랜과 설정에 묶여 있다.** 다음 값이 A3과 A7 판정을 바꾼다.
   - Supabase Realtime: 동시 연결이 Free 200, Pro 500이다. 지출 상한을 해제해야 10,000이 된다.
   - API Gateway WebSocket: 연결은 최대 2시간, 유휴 10분이면 끊긴다. 브로드캐스트 기능도 없다.
   - Vercel Blob: 서버 업로드는 4.5 MB까지다. 큰 파일은 클라이언트 업로드를 써야 한다.
   - Supabase Storage: Free 플랜은 파일당 50 MB까지다.
6. **엔진 하나로 최소비가 15배 차이 난다.** 서울 ElastiCache Serverless의 최소비는 Valkey가 약 $7.4/월이고 Redis OSS가 약 $110/월이다. 최소 과금 저장량이 Valkey는 100MB, Redis OSS는 1GB이기 때문이다. 공유 상태 저장소(B1)를 가장 싸게 충족하는 관리형 후보는 Valkey 서버리스다. 다만 퇴출 정책이 `volatile-lru`로 고정이어서 세션 키에는 TTL이 있어야 한다.
7. **S3 객체 최대 크기는 이제 약 50 TB다(48.8 TiB).** 예전의 "5 TB"를 전제로 한 규칙은 고쳐야 한다. 단일 PUT 한도는 여전히 5 GB다.
8. **블록 볼륨으로는 수평 확장을 할 수 없다.** RWO 볼륨, 그리고 EBS·PD의 기본 연결은 노드 하나에만 붙는다. 그래서 B2 처방은 객체 저장소다. 공유 POSIX가 꼭 필요하면 EFS나 Filestore(RWX)를 쓴다. 다만 EFS 저장 단가는 S3의 13배이고, Filestore는 최소 1 TiB부터라 비싸다.
