# 트래픽·컴퓨트·확장·성능

시나리오 T(트래픽 폭증)를 중심으로, 앱이 "더 많은 요청을 받기 위해" 갖춰야 하는 조건과 놓치기 쉬운 병목을 모은 카탈로그다. 수평 확장의 전제, 오토스케일 신호와 속도, 용량 확보, 데이터 계층 병목, 캐시·전송, 요청 처리 런타임, 과부하 보호 장치, 플랫폼 한도를 다룬다.
장애·DR·백업(D), 배포·마이그레이션(U), 정합성·멱등성(C), 보안·네트워크·규제, 비용 최적화, 관측·운영은 다른 문서가 맡는다. 다만 각 항목의 비용 영향은 적었다. 수치는 모두 2026-10-01에 공식 문서를 직접 열어 확인한 값이며, 확인하지 못한 항목은 "출처 미확인"으로 표시했다.

신호 표시: 🟢 코드·설정으로 확정 / 🟡 힌트, 추론 필요 / 🔴 코드에 없음, 가정으로 처리

## 목차
1. [확장 전제: 상태와 프로세스 모델](#1-확장-전제-상태와-프로세스-모델) — T-001 ~ T-009
2. [오토스케일 신호와 동작](#2-오토스케일-신호와-동작) — T-010 ~ T-020
3. [콜드 스타트와 기동 속도](#3-콜드-스타트와-기동-속도) — T-021 ~ T-027
4. [용량 확보: 노드·사전 증설·쿼터](#4-용량-확보-노드사전-증설쿼터) — T-028 ~ T-039
5. [데이터 계층 병목](#5-데이터-계층-병목) — T-040 ~ T-060
6. [캐시와 전송](#6-캐시와-전송) — T-061 ~ T-073
7. [요청 처리와 런타임](#7-요청-처리와-런타임) — T-074 ~ T-088
8. [보호 장치: 리밋·백프레셔·대기열](#8-보호-장치-리밋백프레셔대기열) — T-089 ~ T-098
9. [새 축·규칙 후보](#새-축규칙-후보)

---

## 1. 확장 전제: 상태와 프로세스 모델

### T-001 프로세스 무상태: 인메모리 세션 금지
- **무엇/왜:** 인스턴스를 늘리려면 어떤 요청이 어떤 인스턴스로 가도 같은 결과가 나와야 한다. 세션을 프로세스 메모리에 두면 수평 확장이 곧 로그인 풀림이 된다.
- **실패 양상:** 2번째 인스턴스가 뜨는 순간 사용자 절반이 로그아웃되거나 "세션 없음" 401을 받는다. 스케일 다운·재시작 때마다 세션이 사라진다. 우회로 sticky session을 켜면 부하가 특정 인스턴스에 쏠린다.
- **신호:** 🟢 `express-session` 기본 `MemoryStore`(store 옵션 없음), Flask 서버측 세션 기본값, `new Map()`·전역 dict에 사용자 키 저장, Django `SESSION_ENGINE`이 `cache`+`LocMemCache`. 🟢 반대 신호(충족): `connect-redis`, `SESSION_ENGINE=...cached_db`/redis, JWT 무상태 쿠키. 🟡 ALB `stickiness.enabled=true`, Cloud Run session affinity 설정은 상태 의존의 힌트.
- **시나리오·수준:** T L1 이상 (설계 T-CTL-001)
- **처방:** 티어0: 플랫폼 세션(Supabase Auth·Firebase Auth) 또는 서명 쿠키. 티어1/2: Redis(Memorystore·ElastiCache)나 DB 세션 저장소로 이전.
- **검증:** 인스턴스 2개 이상으로 띄우고 로그인 후 LB 라운드로빈으로 20회 요청 → 401 0건. 인스턴스 하나를 강제 종료한 뒤에도 세션 유지.
- **비용 영향:** 증가(소) — Redis 최소 인스턴스 비용. 대신 sticky 해제로 인스턴스 활용률 개선.
- **출처:** https://12factor.net/processes ("sticky sessions are a violation of twelve-factor", 세션 상태는 Memcached·Redis 같은 저장소로) · https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-target-group-attributes.html (sticky session은 "servers that maintain state information"용, 확장 시 불균등 분배 가능성 명시) — 2026-10-01 확인 ⚠️출처부적격

### T-002 로컬 디스크 업로드·파일 상태 금지
- **무엇/왜:** 업로드 파일을 컨테이너 로컬 디스크에 쓰면 다른 인스턴스에서 보이지 않고 재시작 때 사라진다. 큰 업로드가 앱 인스턴스를 통과하는 것 자체도 확장 병목이다.
- **실패 양상:** 인스턴스 A에 올린 이미지를 인스턴스 B가 404로 응답. 서버리스(Vercel·Cloud Run)에서는 쓰기 자체가 실패하거나 다음 요청에 없다. 업로드 트래픽이 웹 인스턴스의 대역폭·메모리를 잡아먹는다.
- **신호:** 🟢 `multer({ dest: 'uploads/' })`, `diskStorage`, `fs.writeFile`로 `public/`·`uploads/` 저장, Django `FileSystemStorage`/`MEDIA_ROOT` + 클라우드 스토리지 백엔드 없음, FastAPI `UploadFile` 후 `open(path,'wb')`. 🟢 충족: `@aws-sdk/s3-request-presigner`, `getSignedUrl`, `django-storages`, Supabase Storage·Firebase Storage SDK.
- **시나리오·수준:** T L1 이상 (D 영역의 D-PRE-002와 함께 판정)
- **처방:** 티어0: Supabase Storage/Vercel Blob 직접 업로드. 티어1/2: S3/GCS 서명 URL로 브라우저가 직접 업로드하고 앱은 메타데이터만 기록.
- **검증:** 2개 인스턴스에서 업로드→다른 인스턴스로 조회 성공. 업로드 부하 중 앱 인스턴스 메모리·대역폭이 늘지 않음.
- **비용 영향:** 감소 — 앱 인스턴스가 바이트를 중계하지 않아 컴퓨트·이그레스가 준다(스토리지 비용은 별도).
- **출처:** https://12factor.net/processes · https://docs.aws.amazon.com/AmazonS3/latest/userguide/PresignedUrlUploadObject.html (자격 증명 없이 서명 URL로 업로드, SDK로 최대 7일 만료) — 2026-10-01 확인 ⚠️출처부적격

### T-003 인스턴스별 인메모리 카운터·캐시의 확장 왜곡
- **무엇/왜:** 레이트 리밋 카운터, 중복 방지 집합, 메모리 캐시가 프로세스 안에 있으면 인스턴스 수만큼 한도가 늘고 캐시가 쪼개진다. 오토스케일이 보호 장치를 약하게 만든다.
- **실패 양상:** 리밋 10r/s가 인스턴스 20개에서 실효 200r/s가 된다. 캐시 적중률이 인스턴스 수에 반비례해 DB 부하가 확장할수록 오히려 늘어난다. 캐시 무효화가 한 인스턴스에만 반영된다.
- **신호:** 🟢 `express-rate-limit` 기본 `MemoryStore`, `slowapi` 기본 `memory://`, `lru-cache`·`node-cache`·`functools.lru_cache`·`cachetools`를 DB 결과 캐시에 사용. 🟢 nginx `limit_req_zone`(nginx 인스턴스마다 별도 공유 메모리 존). 🟢 충족: `rate-limit-redis`, `storage_uri="redis://..."`.
- **시나리오·수준:** T L2 이상 (L3에서 리밋이 핵심 통제이므로 필수)
- **처방:** 티어0: 플랫폼 WAF 리밋 또는 Upstash 등 외부 저장소. 티어1/2: Redis 기반 카운터, 또는 리밋 값을 `rate / 최대 인스턴스 수`로 문서화하고 엣지(WAF·Cloud Armor)에 전역 리밋을 둔다.
- **검증:** 인스턴스 1개와 N개에서 같은 부하로 429 발생 시점 비교. 차이가 N배이면 실패.
- **비용 영향:** 중립~증가(소) — Redis 호출 비용.
- **출처:** https://12factor.net/processes (메모리는 "brief, single-transaction cache"로만) · https://nginx.org/en/docs/http/ngx_http_limit_req_module.html (존은 공유 메모리 영역, 64비트에서 1MB당 약 8천 상태) — 2026-10-01 확인. nginx 존이 Pod마다 따로라는 점은 공유 메모리 범위에서 나온 추론이며 simple-web-app `docs/deploy.md`가 같은 결론을 기록함. ⚠️출처부적격

### T-004 Next.js 자체 호스팅 멀티 인스턴스 캐시 공유
- **무엇/왜:** Next.js의 ISR·데이터 캐시는 기본적으로 인스턴스 로컬 파일시스템과 메모리(기본 50MB)에 저장된다. 컨테이너를 여러 개 띄우면 캐시가 인스턴스마다 따로 놀고 `revalidatePath`/`revalidateTag`는 호출을 받은 인스턴스만 무효화한다.
- **실패 양상:** 글을 수정했는데 새로고침할 때마다 옛 내용과 새 내용이 번갈아 보인다. 스케일 아웃할 때마다 새 인스턴스가 빈 캐시로 시작해 원본 DB에 몰린다.
- **신호:** 🟢 `next.config.*`에 `output: 'standalone'` + Dockerfile + `revalidate`/`revalidateTag` 사용 + `cacheHandler` 없음. 🟢 k8s Deployment `replicas`>1 또는 HPA가 Next.js 이미지를 대상으로 함. 🟢 충족: `cacheHandler`/`cacheHandlers` 설정, `@neshca/cache-handler`, Redis 핸들러.
- **시나리오·수준:** T L1 이상 (자체 호스팅인 경우만. Vercel 티어0은 해당 없음)
- **처방:** 티어0: Vercel 유지 시 해당 없음. 티어1/2: Redis 기반 `cacheHandler` + `cacheMaxMemorySize: 0`, `refreshTags()` 구현으로 태그 무효화 동기화.
- **검증:** 인스턴스 2개에서 `revalidateTag` 호출 후 양쪽 인스턴스 응답의 `x-nextjs-cache` 헤더와 내용이 같아지는지 확인.
- **비용 영향:** 증가(소) — 공유 캐시 저장소.
- **출처:** https://nextjs.org/docs/app/guides/self-hosting ("each pod will have a copy of the cache", 기본 메모리 50MB, `refreshTags()`) · https://nextjs.org/docs/app/guides/incremental-static-regeneration ("default file-system cache is per-instance. On-demand revalidation only invalidates the instance that receives the call") — 2026-10-01 확인

### T-005 Next.js 멀티 인스턴스 일관성 키(Server Actions 암호화 키·빌드 ID)
- **무엇/왜:** Next.js는 빌드마다 Server Action 암호화 키를 새로 만든다. 인스턴스마다 다른 빌드를 쓰거나 키가 다르면 한 인스턴스가 암호화한 액션을 다른 인스턴스가 풀지 못한다.
- **실패 양상:** 스케일 아웃 후 폼 제출이 간헐적으로 "Failed to find Server Action"으로 실패. 부하가 클수록(인스턴스가 많을수록) 실패율이 오른다.
- **신호:** 🟢 `'use server'` 사용 + 자체 호스팅(Dockerfile) + `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY` 미설정. 🟡 환경별로 재빌드하는 CI(빌드 ID 불일치 가능성) + `generateBuildId`/`deploymentId` 없음.
- **시나리오·수준:** T L1 이상 (자체 호스팅 Next.js)
- **처방:** 티어1/2: 이미지 1개를 모든 인스턴스가 공유, `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY`와 `deploymentId` 고정.
- **검증:** 인스턴스 3개에서 Server Action 100회 호출 → 실패 0건.
- **비용 영향:** 중립.
- **출처:** https://nextjs.org/docs/app/guides/self-hosting (Multi-Server Deployments 절) — 2026-10-01 확인

### T-006 웹소켓·실시간 연결의 수평 확장(공유 어댑터 + 고정 라우팅)
- **무엇/왜:** 웹소켓 브로드캐스트는 연결이 붙어 있는 인스턴스의 클라이언트에게만 간다. 인스턴스가 여럿이면 Pub/Sub 어댑터로 메시지를 공유해야 하고, Socket.IO 롱폴링은 sticky가 필요하다.
- **실패 양상:** 채팅·알림이 같은 인스턴스에 붙은 사용자에게만 보인다. Socket.IO 롱폴링 단계에서 HTTP 400이 반복된다. Cloud Run에서는 요청 타임아웃에 도달하면 연결이 끊긴다.
- **신호:** 🟢 `socket.io` + `@socket.io/redis-adapter`·`@socket.io/redis-streams-adapter` 없음, `ws` 서버에서 전역 `clients` Set으로 브로드캐스트, Django Channels `InMemoryChannelLayer`. 🟢 Cloud Run 서비스에 `--session-affinity` 없음.
- **시나리오·수준:** T L1 이상 (설계 T-PRE-001)
- **처방:** 티어0: Supabase Realtime·Firebase 등 관리형 실시간(T-061 한도 확인). 티어1: Cloud Run + Memorystore Pub/Sub + 세션 어피니티 + 재연결 로직, 타임아웃 최대 60분. 티어2: Redis 어댑터 + Ingress 쿠키 어피니티.
- **검증:** 인스턴스 2개에 클라이언트를 나눠 붙이고 한쪽에서 보낸 메시지가 전원에게 도착하는지. 인스턴스 하나 종료 후 자동 재연결.
- **비용 영향:** 증가 — Redis + 상시 연결 때문에 Cloud Run은 인스턴스 기반 과금이 된다.
- **출처:** https://socket.io/docs/v4/redis-adapter/ (어댑터 없으면 브로드캐스트가 현재 서버에만, sticky 없으면 HTTP 400) · https://docs.cloud.google.com/run/docs/triggering/websockets (요청 타임아웃 적용, Redis Pub/Sub 권장, 세션 어피니티는 best-effort) — 2026-10-01 확인

### T-007 프로세스 타입 분리(web / worker / scheduler)
- **무엇/왜:** HTTP 처리와 백그라운드 작업이 한 프로세스에 있으면 둘 중 하나의 부하가 다른 하나를 굶기고, 확장 신호도 섞인다. 프로세스 타입을 나눠야 각자 다른 신호로 확장한다.
- **실패 양상:** 이메일 발송·이미지 처리 배치가 돌 때 API 지연이 튄다. 웹 인스턴스를 늘리면 백그라운드 작업도 같이 복제돼 중복 실행된다.
- **신호:** 🟢 웹 서버 프로세스 안에서 `setInterval`, `node-cron`, `APScheduler`, `BackgroundTasks`로 긴 작업, `celery worker`와 웹이 한 컨테이너 `CMD`(supervisord 등). 🟢 충족: Procfile/compose/k8s에 `web`·`worker` 별도 정의.
- **시나리오·수준:** T L2 이상 (L1에서도 장시간 작업이 있으면 권장)
- **처방:** 티어0: Vercel Cron + 큐 서비스(외부), Supabase Edge Functions 스케줄. 티어1: Cloud Run 서비스 + Cloud Run Jobs/워커 서비스, ECS 서비스 분리. 티어2: Deployment 분리 + CronJob.
- **검증:** 워커에 부하를 주는 동안 웹 p95 변화가 허용 범위 이내.
- **비용 영향:** 증가(소) — 워커 최소 인스턴스. 대신 웹을 작게 유지.
- **출처:** https://12factor.net/concurrency (web/worker 프로세스 타입, 프로세스 모델로 수평 확장) — 2026-10-01 확인 ⚠️출처부적격

### T-008 인프로세스 스케줄러의 중복 실행
- **무엇/왜:** 크론을 앱 프로세스 안에서 돌리면 인스턴스 수만큼 같은 작업이 실행된다. 확장할수록 작업 부하와 부작용이 곱해진다.
- **실패 양상:** 오토스케일로 10개가 되면 "매시 정각 집계"가 10번 돌아 DB가 정각마다 폭주한다. 알림이 10번 발송된다.
- **신호:** 🟢 `node-cron`, `cron` 패키지, `APScheduler`, `@nestjs/schedule`, `django-crontab`을 웹 진입점에서 등록 + 분산 락(`redlock`, `pg_advisory_lock`) 없음 + HPA/Cloud Run max>1.
- **시나리오·수준:** T L1 이상 (설계 T-PRE-002)
- **처방:** 티어0: Vercel Cron Jobs / Supabase `pg_cron`. 티어1: Cloud Scheduler → Cloud Run Jobs, EventBridge Scheduler → ECS 태스크. 티어2: k8s CronJob(`concurrencyPolicy: Forbid`).
- **검증:** 인스턴스 3개로 띄우고 스케줄 1주기 동안 작업 실행 로그가 1건인지.
- **비용 영향:** 감소 — 중복 실행 제거.
- **출처:** https://12factor.net/concurrency (프로세스 타입 분리) — 2026-10-01 확인. "인스턴스 수만큼 중복 실행"은 프로세스 모델에서 나온 추론. ⚠️출처부적격 ⚠️근거없음

### T-009 SQLite·파일 DB의 단일 쓰기 한계
- **무엇/왜:** SQLite는 동시에 쓰는 주체를 하나만 허용하고 네트워크 파일시스템 위에서는 잠금이 불안정하다. 여러 인스턴스가 쓰는 순간 확장 불가 구조가 된다.
- **실패 양상:** 인스턴스를 늘리면 `SQLITE_BUSY`/"database is locked"가 급증한다. 인스턴스마다 다른 DB 파일을 보게 되어 데이터가 갈라진다(컨테이너 로컬 디스크).
- **신호:** 🟢 `sqlite3`, `better-sqlite3`, Prisma `provider = "sqlite"`, Django `ENGINE: django.db.backends.sqlite3`, `DATABASE_URL=file:`. 🟡 볼륨 마운트로 공유하려는 시도(EFS·NFS).
- **시나리오·수준:** T L1 이상 (D-PRE-001과 같은 처방이므로 D 담당과 합친다)
- **처방:** 티어0: Supabase/Neon Postgres. 티어1/2: Cloud SQL·RDS Postgres.
- **검증:** 인스턴스 2개 이상에서 동시 쓰기 부하 → 잠금 오류 0건.
- **비용 영향:** 증가 — 관리형 DB 고정비.
- **출처:** https://www.sqlite.org/whentouse.html ("only allow one writer at any instant", 여러 서버가 필요한 사이트는 클라이언트/서버 DB 고려) — 2026-10-01 확인

---

## 2. 오토스케일 신호와 동작

### T-010 오토스케일 설정과 상한의 존재
- **무엇/왜:** 증가를 흡수하려면 자동으로 늘어나는 장치가 있어야 하고, 폭주·비용 사고를 막으려면 상한이 있어야 한다.
- **실패 양상:** 고정 replicas 2개에서 트래픽 3배에 지연이 수십 초로 늘고 타임아웃. 반대로 상한이 없으면 봇 트래픽에 인스턴스가 끝없이 늘어 비용 폭탄과 DB 커넥션 고갈(T-040).
- **신호:** 🟢 k8s `HorizontalPodAutoscaler` 존재 여부, `minReplicas`/`maxReplicas`. 🟢 Cloud Run `autoscaling.knative.dev/maxScale`, Terraform `max_instance_count`, `scaling { max_instance_count }`. 🟢 ECS `aws_appautoscaling_target`. 🔴 티어0(Vercel)은 플랫폼 자동이므로 상한만 확인.
- **시나리오·수준:** T L1 이상 (설계 T-CTL-002)
- **처방:** 티어0: 플랫폼 자동 + 지출 한도. 티어1: Cloud Run max instances(처음엔 작게), ECS target tracking. 티어2: HPA + 노드 오토스케일러(T-028).
- **검증:** 단계 부하로 인스턴스 수가 늘고 줄어드는지, 상한에서 멈추는지 기록.
- **비용 영향:** 감소(평시 축소) / 상한이 비용 상한 역할.
- **출처:** https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/ · https://docs.cloud.google.com/run/docs/configuring/max-instances (리비전당 기본 100, 비용·백엔드 연결 수 제한 용도, 처음엔 3으로 시작 권장, 스파이크 시 잠시 초과 가능) — 2026-10-01 확인

### T-011 CPU requests 미설정으로 HPA가 동작하지 않음
- **무엇/왜:** HPA의 CPU 사용률은 requests 대비 비율이다. 컨테이너에 requests가 없으면 사용률이 정의되지 않아 HPA가 그 지표로 아무것도 하지 않는다. 노드 오토스케일러도 requests로 판단한다.
- **실패 양상:** HPA가 있는데 `<unknown>/60%`로 표시되고 트래픽 폭증에도 replica가 그대로. 사이드카 하나에만 requests가 없어도 계산이 깨질 수 있다.
- **신호:** 🟢 Deployment `resources.requests.cpu` 누락(특히 사이드카·init 아님 컨테이너), HPA `type: Utilization`. 🟡 LimitRange가 기본 requests를 넣는지 확인 필요. 🟢 `ContainerResource` 지표를 쓰면 특정 컨테이너만 기준.
- **시나리오·수준:** T L1 이상, 티어2
- **처방:** 티어2: 모든 컨테이너에 requests 지정, 사이드카가 있으면 `ContainerResource` 지표 사용.
- **검증:** `kubectl get hpa`에서 현재 값이 숫자로 표시되는지 정적 검사 + 부하 시 스케일 발생.
- **비용 영향:** 중립(정확한 bin packing으로 장기적으로 감소).
- **출처:** https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/ ("If a container lacks a resource request, CPU utilization is undefined and the autoscaler won't act on that metric") · https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/ — 2026-10-01 확인

### T-012 확장 신호와 병목의 불일치(CPU가 아닌 워크로드)
- **무엇/왜:** I/O 대기가 대부분인 API(외부 API·LLM 호출, DB 대기), 단일 스레드 런타임(Node, 단일 워커 Python)은 CPU가 낮은 채로 포화된다. 이때 CPU 기반 오토스케일은 늘어나지 않는다.
- **실패 양상:** 요청 대기열과 p95가 폭증하는데 CPU는 30%라 HPA가 움직이지 않는다. 멀티 vCPU 인스턴스에서 단일 스레드 앱이 vCPU 하나만 쓰면 평균 CPU가 낮아 확장이 일어나지 않는다.
- **신호:** 🟢 HPA `metrics`가 `cpu` 하나 + 앱이 `fetch`/`openai`/`anthropic` SDK 위주, 또는 Node 단일 프로세스(cluster 미사용)에 `cpu: 2` 이상. 🟢 충족: `Pods`/`Object`/`External` 지표(RPS·동시 요청), Cloud Run 동시성 기반 확장, ECS `ALBRequestCountPerTarget`.
- **시나리오·수준:** T L2 이상
- **처방:** 티어1: Cloud Run은 동시성 기반이므로 `concurrency`를 앱 실제 병렬도에 맞춤(T-074). ECS는 요청 수 target tracking. 티어2: Prometheus Adapter/KEDA로 RPS·in-flight 요청 기반 HPA, 또는 CPU 목표값을 낮게.
- **검증:** 외부 API 지연을 주입(예: 2초)한 상태로 부하 → 인스턴스가 늘어나는지.
- **비용 영향:** 증가(정확히 필요한 만큼 늘어남).
- **출처:** https://docs.cloud.google.com/run/docs/about-concurrency ("A single-threaded application on a multi-vCPU instance may max out one vCPU while others idle") · https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale-walkthrough/ (RPS·큐 메시지 등 사용자 지표, 메트릭 어댑터 필요) · https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-autoscaling-targettracking.html — 2026-10-01 확인

### T-013 큐 워커는 큐 길이로 확장
- **무엇/왜:** 큐 소비자는 밀린 작업량이 진짜 부하다. CPU로 확장하면 작업이 쌓여도 워커가 늘지 않거나, 대기 중인 I/O 때문에 늦게 반응한다.
- **실패 양상:** 큐 길이가 수만 건으로 불어나 처리 지연이 수십 분인데 워커는 1개. 반대로 빈 큐에도 워커가 상시 N개.
- **신호:** 🟢 `bullmq`, `celery`, `rq`, SQS `ReceiveMessage`, Redis Streams `XREADGROUP` 소비자 + KEDA `ScaledObject` 없음 + CPU HPA. 🟢 충족: KEDA `redis-streams`(`streamLength`/`pendingEntriesCount`/`lagCount`), `aws-sqs-queue` 스케일러.
- **시나리오·수준:** T L3 (설계 T-CTL-010), 큐가 있으면 L2부터 권장
- **처방:** 티어1: Cloud Run 워커 풀/Jobs, ECS 서비스에 큐 지표 step scaling. 티어2: KEDA ScaledObject(Redis Streams·SQS).
- **검증:** 큐에 N만 건 투입 후 워커 수 증가 시간과 소진 시간 측정.
- **비용 영향:** 감소 — 빈 큐에서 0~1개로 축소 가능.
- **출처:** https://keda.sh/docs/2.21/scalers/redis-streams/ (PEL·XLEN·lag 세 방식, lag은 Redis 7+) · https://keda.sh/docs/2.21/concepts/scaling-deployments/ — 2026-10-01 확인

### T-014 HPA 확장·축소 동작(behavior) 튜닝
- **무엇/왜:** 기본 HPA는 확장은 즉시(안정화 0초), 축소는 300초 안정화다. 스파이크가 반복되는 서비스는 축소를 너무 빨리 하면 다음 파도에 다시 콜드 스타트를 맞고, 너무 느리면 비용이 샌다. 확장 정책(15초당 100% 등)이 피크 램프보다 느리면 따라가지 못한다.
- **실패 양상:** 1분 안에 20배가 오는 L3 시나리오에서 15초마다 2배씩만 늘어 1분 동안 16배에 못 미친다. 축소 안정화를 0으로 바꾸면 플래핑(늘었다 줄었다 반복).
- **신호:** 🟢 HPA `behavior.scaleUp.policies`(`Percent`/`Pods`, `periodSeconds`), `scaleDown.stabilizationWindowSeconds`. 🔴 behavior 미지정이면 기본값으로 판정.
- **시나리오·수준:** T L2 이상 (L3는 필수 검토)
- **처방:** 티어2: L3이면 `scaleUp` `Percent 100 / 15s`와 `Pods 4+ / 15s`를 `selectPolicy: Max`로, 축소는 기본 300초 유지 또는 더 길게. simple-web-app `k8s/base/hpa.yaml`이 예시.
- **검증:** 스파이크 부하에서 "부하 시작 → 목표 replica 도달" 시간 기록, 반복 파도 사이의 replica 수 그래프.
- **비용 영향:** 축소 지연만큼 증가, 대신 재확장 콜드 스타트 감소.
- **출처:** https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/ (sync 15초, 축소 안정화 기본 300초, 확장 0초, tolerance 10%) — 2026-10-01 확인

### T-015 스케일 속도 예산(가용 시간 = 피크 램프)
- **무엇/왜:** 실제 확장 시간은 지표 수집 + HPA 주기(15초) + Pod 기동 + (노드 부족 시) 노드 부팅의 합이다. 피크가 도달하는 시간보다 길면 그 사이는 기존 용량으로 버텨야 한다.
- **실패 양상:** T L3 가정(1분 안에 20배)인데 노드 부팅만 80~120초가 걸려, 첫 2분간 Pending Pod와 5xx가 쌓인다.
- **신호:** 🟡 이미지 크기, 앱 기동 시간(헬스체크 통과까지), 노드 오토스케일러 종류에서 추정. 🔴 실제 기동 시간은 P4 측정으로 채운다.
- **시나리오·수준:** T L2 이상, L3 필수
- **처방:** 티어1: 최소 인스턴스(T-021) + 기동 최적화(T-022). 티어2: 노드 여유 용량(T-029), 이미지 스트리밍(T-023), 최소 replica를 피크/램프 비율에 맞게.
- **검증:** P4 스파이크 테스트에서 "부하 시작→새 Pod Ready→새 노드 Ready" 타임라인 기록, 가정 램프와 비교.
- **비용 영향:** 증가 — 여유 용량·최소 인스턴스로 시간을 산다.
- **출처:** https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/ (sync 15초) · https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md (CA 반응 소규모 클러스터 최대 30초, 노드 프로비저닝 시간은 클라우드 공급자에 달림) · https://docs.cloud.google.com/kubernetes-engine/docs/how-to/capacity-provisioning ("Each new node takes approximately 80 to 120 seconds to boot") — 2026-10-01 확인

### T-016 scale-to-zero와 첫 요청 지연
- **무엇/왜:** 0까지 축소하면 비용은 0이지만 첫 요청은 콜드 스타트를 맞는다. KEDA는 0↔1을 직접 결정하고 폴링 간격(기본 30초)만큼 늦게 깨어난다.
- **실패 양상:** 새벽에 0으로 줄었다가 예고 이벤트 시작 순간 모든 요청이 콜드 스타트 + 폴링 지연을 동시에 맞는다. 큐 워커는 첫 메시지가 최대 30초+기동 시간 동안 처리되지 않는다.
- **신호:** 🟢 KEDA `minReplicaCount: 0`(기본값), Cloud Run min instances 0(기본), `pollingInterval` 미지정. 🟢 HPA `minReplicas: 0`.
- **시나리오·수준:** T L2 이상에서 사용자 대면 경로는 0 금지. T L0~L1은 비용상 0 허용.
- **처방:** 티어1: 사용자 대면 서비스 min ≥1. 티어2: KEDA `minReplicaCount: 1` 또는 `idleReplicaCount`, 사용자 대면은 0 금지.
- **검증:** 0 상태에서 첫 요청 지연 측정, 큐에 메시지 1건 넣고 처리까지 시간 측정.
- **비용 영향:** min 1 유지 시 증가(소).
- **출처:** https://keda.sh/docs/2.21/concepts/scaling-deployments/ (pollingInterval 30초, cooldownPeriod 300초, minReplicaCount 기본 0, 0↔1은 KEDA가 결정) · https://docs.cloud.google.com/run/docs/configuring/min-instances — 2026-10-01 확인

### T-017 상한(maxReplicas·max instances)을 하류 용량에 맞춤
- **무엇/왜:** 앱 계층의 상한은 DB 커넥션, 외부 API 한도, 노드 수가 감당할 수 있는 수준이어야 한다. 앱만 무한히 늘면 병목이 하류로 이동해 전체가 무너진다.
- **실패 양상:** 피크에 Cloud Run이 100개로 늘어 각 인스턴스가 풀 10개씩 → DB `too many connections`로 전 인스턴스가 실패.
- **신호:** 🟢 HPA `maxReplicas`·Cloud Run max와 풀 크기·DB `max_connections`를 함께 읽어 곱셈(T-040). 🟡 외부 SaaS 한도는 코드에 없으면 가정.
- **시나리오·수준:** T L2 이상 (설계 T-CTL-003)
- **처방:** 티어1: max instances = (DB 허용 커넥션 − 여유) / 인스턴스당 풀. 티어2: 동일 계산을 리포트에 표로(simple-web-app `docs/deploy.md`의 DB 커넥션 계산 방식).
- **검증:** 상한까지 부하를 올려 DB 연결 수 최대값이 한도 미만인지.
- **비용 영향:** 상한이 비용 상한을 겸한다.
- **출처:** https://docs.cloud.google.com/run/docs/configuring/max-instances ("limit the number of connections to a backing service, such as to a database") — 2026-10-01 확인

### T-018 ECS·Application Auto Scaling 특성
- **무엇/왜:** ECS 서비스 자동 확장은 CloudWatch 경보 기반 target tracking이다. 지표가 부족하면 아무것도 하지 않고, 배포 중에는 축소를 끈다. 여러 정책이 있으면 하나라도 확장 신호면 확장한다.
- **실패 양상:** 새 서비스에 지표가 아직 없어 첫 스파이크에 반응하지 않는다. CPU 정책만 두어 I/O 바운드 경로가 포화돼도 그대로(T-012).
- **신호:** 🟢 Terraform `aws_appautoscaling_policy` `TargetTrackingScaling`, `predefined_metric_type` 값(`ECSServiceAverageCPUUtilization`, `ALBRequestCountPerTarget`), `disable_scale_in`.
- **시나리오·수준:** T L1 이상, 티어1(ECS)
- **처방:** 티어1: CPU + `ALBRequestCountPerTarget` 두 정책 병행, 예고 이벤트는 scheduled action(T-031).
- **검증:** 부하 시 경보 발생→태스크 증가 지연 측정.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-autoscaling-targettracking.html (지표 부족 시 미확장, 배포 중 scale-in 중지, 여러 정책 중 하나라도 확장 준비면 확장) — 2026-10-01 확인

### T-019 서버리스 함수의 동시성·스케일 속도 한도(Lambda)
- **무엇/왜:** Lambda는 리전당 계정 동시성 기본 1,000, 함수별 10초마다 1,000 실행 환경까지 늘어나고, RPS는 동시성의 10배로 제한된다. 계정 내 모든 함수가 이 풀을 공유한다.
- **실패 양상:** 한 함수의 폭주(또는 배치)가 계정 동시성을 다 써서 다른 핵심 함수가 429로 거절된다. 짧은 함수(20ms)라도 RPS 한도 10,000에서 막힌다.
- **신호:** 🟢 `serverless.yml`, SAM/CDK `aws_lambda_function`, `reserved_concurrent_executions` 미설정. 🔴 계정 쿼터 실제값은 코드에 없으므로 기본 1,000 가정.
- **시나리오·수준:** T L2 이상, Lambda 사용 시
- **처방:** 핵심 함수에 reserved concurrency, 하류 보호 목적 상한도 reserved로. L3 피크 계산 = RPS × 평균 지속시간으로 쿼터 증설을 미리 요청.
- **검증:** 피크 동시성 계산표 + 부하 테스트 중 `Throttles` 지표 0.
- **비용 영향:** reserved는 무료, provisioned는 증가.
- **출처:** https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html (계정 기본 1,000, RPS 한도 = 동시성 × 10, 비예약 최소 100) · https://docs.aws.amazon.com/lambda/latest/dg/scaling-behavior.html (함수별 10초마다 1,000 실행 환경, 초과 시 429) — 2026-10-01 확인

### T-020 Vercel 함수 동시성·파일 디스크립터 한도
- **무엇/왜:** Vercel Functions(Fluid compute)는 Hobby·Pro 30,000, Enterprise 100,000+ 동시성까지 자동 확장한다. 인스턴스당 파일 디스크립터 1,024개를 동시 실행이 공유한다. 함수가 아무리 늘어도 하류(DB)가 이 확장을 받아야 한다.
- **실패 양상:** 함수는 수천 개로 늘었는데 요청마다 DB 연결을 열어 Postgres가 즉시 포화(T-041). 한 인스턴스가 동시 요청마다 소켓을 열어 "too many open files".
- **신호:** 🟢 `vercel.json`, `next.config.*`, Route Handler에서 요청마다 `new Client()`/`new PrismaClient()`/`postgres()`. 🟡 Fluid compute 여부(2025-04-23 이후 신규 프로젝트 기본 활성).
- **시나리오·수준:** 티어0 사용 시 T L1 이상
- **처방:** 티어0: 모듈 스코프 클라이언트 재사용 + 트랜잭션 풀러(Supavisor 6543), 하류 보호용 레이트 리밋.
- **검증:** 동시 1,000 요청에서 DB 연결 수가 풀러 한도 이내, `EMFILE` 0건.
- **비용 영향:** 중립(활성 CPU 과금이라 I/O 대기는 과금 안 됨).
- **출처:** https://vercel.com/docs/functions/limitations (동시성 30,000/100,000+, FD 1,024 공유, 최대 실행 시간 Hobby 300초·Pro 800초, 본문 4.5MB) · https://vercel.com/docs/fluid-compute — 2026-10-01 확인

---

## 3. 콜드 스타트와 기동 속도

### T-021 최소 인스턴스·프로비저닝된 동시성
- **무엇/왜:** 피크 램프가 콜드 스타트보다 짧으면 처음 들어온 사용자는 기동을 기다린다. 최소 인스턴스는 따뜻한 용량을 상시 유지한다.
- **실패 양상:** 1분 안에 20배 스파이크에서 처음 수십 초 동안 콜드 스타트 지연(수 초)과 타임아웃이 몰린다.
- **신호:** 🟢 Cloud Run `min_instance_count`/`autoscaling.knative.dev/minScale`, Lambda `provisioned_concurrent_executions`, Firebase `minInstances`, HPA `minReplicas`. 🔴 없으면 0으로 가정.
- **시나리오·수준:** T L3 & 티어1은 필수(설계 TIER-003), L2는 예고 시각 전에 상향(T-031)
- **처방:** 티어0: Firebase `minInstances`, Vercel은 Fluid 사전 워밍(제어 불가). 티어1: Cloud Run min ≥ 피크/램프 비율에 따라, 고가용 목적이면 3 이상. Lambda provisioned concurrency(할당에 1~2분). 티어2: `minReplicas`.
- **검증:** 0 부하 → 스파이크 즉시 시작, 첫 10초 p95 비교(min 0 대 min N).
- **비용 영향:** 증가 — Cloud Run 최소 인스턴스는 요청 기반 과금에서 유휴 요율, 인스턴스 기반은 전액. Provisioned concurrency 추가 과금.
- **출처:** https://docs.cloud.google.com/run/docs/configuring/min-instances (유휴 과금, 고가용성엔 최소 3 권장, 용량 부족 시 최소치 아래로 내려갈 수 있음) · https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html (provisioned는 1~2분 준비, 분당 6,000) · https://firebase.google.com/docs/functions/manage-functions — 2026-10-01 확인

### T-022 기동 시간 단축(지연 초기화·CPU 부스트·의존성 축소)
- **무엇/왜:** 인스턴스가 빨리 뜰수록 같은 스파이크를 적은 여유 용량으로 받는다. 기동 중 무거운 초기화(모델 로딩, 전체 캐시 예열, 거대한 import)는 확장 속도를 직접 깎는다.
- **실패 양상:** 기동에 30초 걸리는 앱은 HPA가 즉시 반응해도 30초 동안 새 용량이 없다. 기동 중 CPU 제한으로 더 느려진다.
- **신호:** 🟢 모듈 최상위에서 대형 모델/파일 로드, `import` 대량, Spring 등 무거운 프레임워크. 🟢 Cloud Run `startup-cpu-boost` 미설정. 🟡 이미지 크기(수 GB).
- **시나리오·수준:** T L2 이상
- **처방:** 티어1: Cloud Run startup CPU boost(1 vCPU 인스턴스는 기동 중 2 vCPU, 기동 후 10초까지), 지연 초기화, 전역 클라이언트 재사용. 티어2: CPU requests를 기동 피크 고려해 설정, 무거운 초기화는 lazy.
- **검증:** 컨테이너 시작→readiness 통과 시간을 10회 측정한 p95.
- **비용 영향:** 부스트 시간만큼 소폭 증가, 대신 최소 인스턴스를 줄일 수 있다.
- **출처:** https://docs.cloud.google.com/run/docs/configuring/services/cpu (startup CPU boost) · https://docs.cloud.google.com/run/docs/tips/general (지연 초기화, 전역 변수 재사용, 의존성 축소) — 2026-10-01 확인

### T-023 이미지 크기와 이미지 풀 시간
- **무엇/왜:** 새 노드는 이미지가 캐시에 없으므로 전체를 내려받아야 한다. 큰 이미지는 확장 경로마다 수십 초를 더한다.
- **실패 양상:** 노드가 늘어난 뒤에도 Pod가 `ContainerCreating`에서 20~30초 머문다.
- **신호:** 🟢 Dockerfile 단일 스테이지, `FROM node:latest`/`python:3.x`(slim 아님), `node_modules` 개발 의존성 포함, ML 모델을 이미지에 포함. 🟢 GKE 이미지 스트리밍(`--enable-image-streaming`) 여부.
- **시나리오·수준:** T L2 이상, 티어2에서 큼
- **처방:** 티어1/2: 멀티 스테이지 + slim/distroless, 모델은 오브젝트 스토리지에서 지연 로드. 티어2(GKE): 이미지 스트리밍(Autopilot은 자동, Artifact Registry 필요).
- **검증:** 빈 노드에서 Pod 생성→Running 시간 측정.
- **비용 영향:** 감소(레지스트리 저장·전송 감소).
- **출처:** https://docs.cloud.google.com/kubernetes-engine/docs/how-to/image-streaming (327MB 이미지 풀 약 1.5초 대 약 24초 예시) — 2026-10-01 확인

### T-024 기동이 느린 앱의 startupProbe
- **무엇/왜:** 기동이 느린 앱에 liveness만 있으면 기동 중에 죽여 버린다. 부하 중 확장된 Pod가 CPU 경합으로 더 느리게 뜨면 재시작 루프가 된다.
- **실패 양상:** 스파이크 때 새 Pod가 `CrashLoopBackOff`로 늘지 못하고, 기존 Pod도 probe 지연으로 재시작되는 연쇄(simple-web-app에서 로컬 관찰된 현상).
- **신호:** 🟢 `livenessProbe` 있음 + `startupProbe` 없음 + `initialDelaySeconds` 짧음 + 기동 시간이 긴 런타임. 🟢 probe `timeoutSeconds: 1`(기본).
- **시나리오·수준:** T L2 이상, 티어2
- **처방:** 티어2: `startupProbe`로 기동 대기 분리, liveness `timeoutSeconds`·`failureThreshold` 여유. 티어1: Cloud Run startup probe.
- **검증:** CPU 제약(노드 포화) 상태에서 스케일 아웃 → 새 Pod 재시작 0회.
- **비용 영향:** 중립.
- **출처:** https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/ (startup probe가 성공할 때까지 liveness·readiness 비활성) — 2026-10-01 확인

### T-025 새 인스턴스 워밍(LB slow start·콜드 캐시)
- **무엇/왜:** 방금 뜬 인스턴스는 JIT·커넥션 풀·로컬 캐시가 비어 있다. LB가 곧바로 몫 전체를 보내면 새 인스턴스가 느리게 응답한다. 재시작 직후 캐시가 비어 원본에 몰리는 것도 같은 문제다.
- **실패 양상:** 스케일 아웃 직후 p99가 오히려 튄다. 대규모 재시작 후 캐시 미스 폭주로 DB 과부하(SRE "cold cache").
- **신호:** 🟢 ALB 대상 그룹 `slow_start.duration_seconds` 미설정, 라우팅 알고리즘. 🟡 앱이 기동 시 풀을 미리 채우지 않음(`pool.min=0`).
- **시나리오·수준:** T L3
- **처방:** 티어1/2(AWS): 대상 그룹 slow start(라운드로빈에서만 가능). 공통: 기동 시 커넥션 풀 최소치 확보, 캐시 계층은 공유 캐시(Redis)로 인스턴스 재시작 영향 제거.
- **검증:** 스케일 아웃 시점 전후 p99 비교.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-target-group-attributes.html (slow start는 요청을 선형 증가, least outstanding requests·weighted random과는 함께 못 씀) · https://sre.google/sre-book/addressing-cascading-failures/ (cold cache 위험, 점진적 램프) — 2026-10-01 확인

### T-026 서버리스에서 클라이언트·연결을 핸들러 밖에서 재사용
- **무엇/왜:** 함수 핸들러 안에서 DB·HTTP 클라이언트를 만들면 요청마다 TLS 핸드셰이크와 연결이 생긴다. 지연이 늘고 DB 연결이 폭증한다.
- **실패 양상:** 같은 트래픽인데 DB 연결 수가 요청 수에 비례해 늘고 `too many connections`. 개발 중 Next.js 핫 리로드로 PrismaClient가 계속 생성.
- **신호:** 🟢 `export async function GET() { const prisma = new PrismaClient() ... }`, 핸들러 안 `createClient(`, `new Pool(`. 🟢 충족: `globalThis.prisma ??= new PrismaClient()`, 모듈 스코프 초기화.
- **시나리오·수준:** T L1 이상 (티어0·티어1 서버리스)
- **처방:** 티어0/1: 모듈 스코프 생성, 풀 크기 1(서버리스 + 트랜잭션 풀러), dev는 global 캐싱.
- **검증:** 정적 검사(핸들러 내부 생성자 호출) + 동시 100 요청에서 DB 연결 수.
- **비용 영향:** 감소.
- **출처:** https://supabase.com/docs/guides/database/connecting-to-postgres ("Create the client once at module scope, not per request", 풀 크기 1) · https://www.prisma.io/docs/orm/prisma-client/setup-and-configuration/databases-connections (핸들러 밖 인스턴스화, 핫 리로드 global 저장) — 2026-10-01 확인

### T-027 Vercel Fluid compute 활성 여부
- **무엇/왜:** Fluid compute는 한 인스턴스가 여러 호출을 동시에 처리하고(Node·Python), 프로덕션에서 사전 워밍·바이트코드 캐시로 콜드 스타트를 줄인다. 오래된 프로젝트는 꺼져 있을 수 있다.
- **실패 양상:** I/O 위주(LLM 호출) 함수가 호출마다 인스턴스를 따로 잡아 콜드 스타트와 비용이 늘어난다.
- **신호:** 🟢 `vercel.json`의 `"fluid": true/false`. 🟡 프로젝트 생성 시기(2025-04-23 이후 기본 활성), 대시보드 설정은 코드에 없으므로 가정.
- **시나리오·수준:** 티어0 & T L1 이상
- **처방:** 티어0: `fluid: true`, 전역 상태가 동시 요청 사이에서 공유되므로 요청별 데이터를 전역에 두지 않는다.
- **검증:** 동일 부하에서 인스턴스 수·콜드 스타트 횟수 비교.
- **비용 영향:** 감소(활성 CPU 과금 + 인스턴스 재사용).
- **출처:** https://vercel.com/docs/fluid-compute — 2026-10-01 확인

---

## 4. 용량 확보: 노드·사전 증설·쿼터

### T-028 노드 오토스케일러(CA·Karpenter·Autopilot)
- **무엇/왜:** HPA는 Pod를 늘릴 뿐, 노드가 없으면 Pod는 Pending이다. 노드 계층 자동 확장이 없으면 HPA 상한은 종이 위의 숫자다.
- **실패 양상:** 피크에 Pod 수십 개가 Pending, 실제 처리 용량은 고정 노드 수에서 멈춘다.
- **신호:** 🟢 EKS: `cluster-autoscaler` Deployment, Karpenter `NodePool`, 관리형 노드 그룹 `scaling_config { max_size }`. GKE: 노드 풀 `autoscaling {}` 블록, Autopilot. 🟢 노드 그룹 `min=max`이면 고정.
- **시나리오·수준:** T L1 이상, 티어2
- **처방:** 티어2(EKS): Karpenter(노드 그룹 없이 Pending Pod에 맞는 인스턴스를 직접 생성) 또는 CA. GKE: Autopilot 또는 노드 풀 오토스케일링.
- **검증:** HPA 상한까지 부하 → Pending 지속 시간 기록.
- **비용 영향:** 감소(평시 노드 축소).
- **출처:** https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md (unschedulable Pod 기준, 스캔 10초, 축소는 10분 미사용 + requests 50% 미만) · https://karpenter.sh/docs/concepts/ — 2026-10-01 확인

### T-029 노드 여유 용량(저우선순위 자리표시 Pod)
- **무엇/왜:** 노드 부팅(80~120초)은 1분 램프보다 길다. 음수 우선순위의 pause Pod로 빈 자리를 미리 잡아 두면, 실제 Pod가 이를 선점해 즉시 스케줄되고 CA가 그 뒤에 노드를 보충한다.
- **실패 양상:** 여유 용량 없이 L3 스파이크를 맞으면 첫 2분간 새 Pod가 Pending.
- **신호:** 🟢 `PriorityClass` 음수 `value` + `pause` 이미지 Deployment(예: `overprovisioning`). 🔴 없으면 미충족.
- **시나리오·수준:** T L3 & 티어2 (설계 T-CTL-009)
- **처방:** 티어2: 가장 큰 앱 Pod 이상 requests의 자리표시 Pod N개(예고 이벤트는 Job으로 한시 확보). GKE Autopilot은 자리표시 Pod requests도 과금.
- **검증:** 스파이크 시 첫 신규 Pod의 Pending→Running 시간이 노드 부팅 시간보다 확연히 짧은지.
- **비용 영향:** 증가 — 자리표시 Pod requests만큼 상시 비용.
- **출처:** https://docs.cloud.google.com/kubernetes-engine/docs/how-to/capacity-provisioning · https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md (priority -10 pause Pod로 overprovisioning) · https://kubernetes.io/docs/concepts/scheduling-eviction/pod-priority-preemption/ — 2026-10-01 확인

### T-030 노드 그룹 상한과 HPA 상한 합의 정합
- **무엇/왜:** 모든 HPA가 상한에 도달했을 때 필요한 requests 합이 노드 그룹 최대 용량을 넘으면 마지막 확장분은 영원히 Pending이다.
- **실패 양상:** 리포트상 "최대 20 Pod"인데 노드 상한 때문에 실제로는 12 Pod에서 멈춘다.
- **신호:** 🟢 Σ(maxReplicas × Pod requests) 대 노드 그룹 `max_size` × 노드 allocatable(인스턴스 타입). 🟢 GKE `--max-nodes`/`--total-max-nodes`, Karpenter `NodePool.spec.limits`.
- **시나리오·수준:** T L1 이상, 티어2 (정적 계산으로 판정 가능)
- **처방:** 티어2: 노드 상한을 계산값 + 시스템 Pod 여유로. 설계 §9.3의 노드 수 계산과 같은 식을 쓴다.
- **검증:** 정적 계산 + 상한 부하 시 Pending 0.
- **비용 영향:** 중립(상한일 뿐, 평시 비용은 그대로).
- **출처:** https://docs.cloud.google.com/kubernetes-engine/docs/concepts/cluster-autoscaler (requests 기준 결정, 노드 풀 min/max) · https://karpenter.sh/docs/concepts/ — 2026-10-01 확인

### T-031 예고 이벤트 사전 증설 스케줄
- **무엇/왜:** 오픈 시각·티켓 판매처럼 시각을 아는 이벤트는 반응형 확장보다 먼저 늘려 두는 것이 싸고 확실하다.
- **실패 양상:** 오픈 시각 정각에 반응형 확장이 시작돼 첫 1~3분이 장애 구간이 된다.
- **신호:** 🟡 도메인 신호(예약·쿠폰·오픈·`startAt`·`openAt` 필드, 카운트다운 UI). 🟢 충족: KEDA `cron` 트리거, Application Auto Scaling `scheduled action`, Cloud Scheduler로 min instances 변경, k8s CronJob이 HPA min 패치.
- **시나리오·수준:** T L2 (설계 T-CTL-005)
- **처방:** 티어1: ECS/Lambda scheduled scaling, Cloud Run은 스케줄러로 min instances 상향. 티어2: KEDA cron 트리거(활성 구간 동안 하한 역할).
- **검증:** 이벤트 리허설에서 정각 이전에 목표 replica 도달 확인.
- **비용 영향:** 증가(이벤트 구간만).
- **출처:** https://keda.sh/docs/2.21/scalers/cron/ (start/end/desiredReplicas, 다른 트리거와 함께면 동적 하한) · https://docs.aws.amazon.com/autoscaling/application/userguide/application-auto-scaling-scheduled-scaling.html — 2026-10-01 확인

### T-032 로드밸런서 사전 용량(ALB LCU 예약)
- **무엇/왜:** ALB는 자동 확장하지만 급격한 스파이크는 확장 시간이 필요하다. 예고 이벤트나 갑작스러운 스파이크에는 최소 용량을 예약할 수 있다.
- **실패 양상:** 앱은 충분한데 LB 단에서 지연·5xx(`ELB 5xx`)가 먼저 난다.
- **신호:** 🟢 Terraform `aws_lb`의 용량 예약 설정 여부. 🟡 T L2/L3 도메인 + AWS.
- **시나리오·수준:** T L3 또는 T L2 대규모 이벤트, AWS
- **처방:** 티어1/2(AWS): 이벤트 전 LCU 예약(최소 100 LCU), `PeakLCUs`로 산정. GCP 전역 LB는 해당 기능 확인 안 함(출처 미확인). ⚠️근거없음
- **검증:** 스파이크 테스트 중 LB 5xx와 타깃 5xx 분리 측정.
- **비용 영향:** 증가 — 예약 LCU 과금.
- **출처:** https://docs.aws.amazon.com/elasticloadbalancing/latest/application/capacity-unit-reservation.html (예정 이벤트·스파이크용, 최소 100 LCU) — 2026-10-01 확인

### T-033 클라우드 계정 컴퓨트 쿼터
- **무엇/왜:** 오토스케일 상한이 아무리 커도 계정 쿼터(vCPU 수, 인스턴스 수)가 먼저 막는다. 새 계정은 기본값이 작다.
- **실패 양상:** 피크에 노드 생성이 `VcpuLimitExceeded`로 실패, CA가 계속 재시도. 새 AWS 계정은 Standard 온디맨드 기본 vCPU 쿼터가 작아 노드 몇 대에서 막힌다.
- **신호:** 🔴 쿼터는 코드에 없다. 🟢 계산: Σ(최대 노드 × 노드 vCPU) 또는 Fargate 태스크 vCPU 합을 리포트에 내고 "쿼터 확인 필요"로 가정 표시.
- **시나리오·수준:** T L2 이상 (L3 필수)
- **처방:** 티어1/2: 이벤트 전에 Service Quotas 증설 요청, 리포트에 필요 vCPU 명시.
- **검증:** `aws service-quotas get-service-quota`/GCP 쿼터 조회 결과 ≥ 계산값.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html (On-Demand 쿼터는 vCPU 기준, 페이지 표기상 Standard 기본값 5, 사용량에 따라 자동 증가·요청 가능) — 2026-10-01 확인

### T-034 서버리스·컨테이너 플랫폼 인스턴스 한도
- **무엇/왜:** Cloud Run은 리비전당 max instances 기본 100이고 프로젝트·리전별 한도가 따로 있다. 인스턴스당 동시 요청 최대 1,000, 최대 8 vCPU·32GiB.
- **실패 양상:** 피크 계산상 150 인스턴스가 필요한데 기본 상한 100에서 429/503.
- **신호:** 🟢 Cloud Run `max_instance_count` 미설정(기본 100), `containerConcurrency`. 🔴 프로젝트 쿼터는 가정.
- **시나리오·수준:** T L2 이상, 티어1
- **처방:** 티어1: 필요 인스턴스 = 피크 동시 요청 / concurrency 계산 후 max와 쿼터 확인.
- **검증:** 계산표 + 상한 부하 테스트.
- **비용 영향:** 중립.
- **출처:** https://docs.cloud.google.com/run/docs/configuring/max-instances (리비전당 기본 100) · https://docs.cloud.google.com/run/quotas (인스턴스당 동시 요청 1,000, 8 vCPU, 32GiB, HTTP/1 요청 32MiB, 타임아웃 60분) — 2026-10-01 확인

### T-035 EKS 서브넷 IP 고갈
- **무엇/왜:** VPC CNI는 Pod마다 VPC IP를 준다. 서브넷이 작으면 노드·Pod가 더 이상 생성되지 않는다. 확장의 숨은 상한이다.
- **실패 양상:** 피크에 노드는 떴는데 Pod가 IP 할당 실패로 `ContainerCreating`에 머문다. 웜 풀이 IP를 미리 잡아 실제보다 빨리 고갈된다.
- **신호:** 🟢 Terraform VPC 서브넷 CIDR(`/24` 등 작은 크기) + EKS + VPC CNI, `ENABLE_PREFIX_DELEGATION` 미설정, `WARM_ENI_TARGET` 기본. 🟢 계산: 최대 Pod 수 + 노드 + LB·RDS 등 VPC 내 IP 소비 대 서브넷 가용 IP.
- **시나리오·수준:** T L2 이상, 티어2(EKS)
- **처방:** 티어2: 서브넷을 성장 고려해 크게(eksctl 기본 /19), prefix delegation, 보조 CIDR(100.64.0.0/10) 커스텀 네트워킹, 또는 IPv6.
- **검증:** 정적 계산 + 상한 부하 시 IP 할당 오류 0.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/eks/latest/best-practices/ip-opt.html — 2026-10-01 확인

### T-036 GKE 확장 한계(IP·노드 풀)
- **무엇/왜:** GKE 클러스터 오토스케일러는 IP가 부족하면 노드를 추가하지 못한다. Pod 범위·노드 범위가 작으면 같은 문제가 생긴다.
- **실패 양상:** 노드 확장이 IP 부족으로 실패하고 Pending Pod가 남는다.
- **신호:** 🟢 Terraform `ip_allocation_policy`의 Pod·서비스 보조 범위 크기, `max_pods_per_node`.
- **시나리오·수준:** T L2 이상, 티어2(GKE)
- **처방:** 티어2: 최대 노드 × 노드당 Pod 수를 담을 보조 범위 크기.
- **검증:** 정적 계산.
- **비용 영향:** 중립.
- **출처:** https://docs.cloud.google.com/kubernetes-engine/docs/concepts/cluster-autoscaler (IP 고갈 시 스케일업 실패, 최대 15,000 노드) — 2026-10-01 확인

### T-037 노드 오토스케일러는 requests로 판단한다(과소 requests의 함정)
- **무엇/왜:** CA·GKE 오토스케일러는 실제 사용량이 아니라 requests 합으로 노드를 늘리고 줄인다. requests가 실제보다 작으면 노드가 과밀해져 CPU 경합과 OOM이 생기고, 스케일업도 늦어진다.
- **실패 양상:** 피크에 노드 CPU 100%인데 requests 합은 50%라 노드가 늘지 않는다. 같은 노드의 Pod들이 서로 굶긴다.
- **신호:** 🟢 requests가 limits의 1/4 미만, 또는 requests가 매우 작은 값(`cpu: 10m`). 🔴 실측은 P4.
- **시나리오·수준:** T L2 이상, 티어2
- **처방:** 티어2: P4 실측으로 requests를 p95 사용량 근처로(COST-006과 반대 방향의 하한 점검).
- **검증:** 피크 부하 중 노드 CPU 사용률 대 requests 합 비교.
- **비용 영향:** 증가(정직한 requests는 노드를 더 쓴다).
- **출처:** https://docs.cloud.google.com/kubernetes-engine/docs/concepts/cluster-autoscaler ("based on the resource requests (rather than actual resource utilization)") — 2026-10-01 확인

### T-038 핵심 워크로드 우선순위(PriorityClass)
- **무엇/왜:** 용량이 모자라는 순간 누가 먼저 자리를 얻을지 정해야 한다. 우선순위가 없으면 배치 작업이 사용자 대면 Pod의 자리를 차지할 수 있다.
- **실패 양상:** 피크에 리포트 생성 Job이 노드를 차지해 API Pod가 Pending.
- **신호:** 🟢 `priorityClassName` 없음 + 같은 클러스터에 배치/워커/API 혼재.
- **시나리오·수준:** T L3, 티어2
- **처방:** 티어2: API > 워커 > 배치 > 자리표시 순 PriorityClass, 배치는 `preemptionPolicy: Never` 고려.
- **검증:** 노드 포화 상태에서 API 스케일 아웃 시 배치 Pod가 선점되는지.
- **비용 영향:** 중립.
- **출처:** https://kubernetes.io/docs/concepts/scheduling-eviction/pod-priority-preemption/ — 2026-10-01 확인

### T-039 Fargate·ECS 태스크 기동 속도와 서비스 한도
- **무엇/왜:** Fargate는 노드 관리가 없지만 태스크 기동 시간(이미지 풀 포함)과 계정의 vCPU·태스크 실행 속도 한도가 확장 속도를 정한다.
- **실패 양상:** 피크에 태스크 시작 API가 스로틀되거나 vCPU 쿼터에 막혀 원하는 수까지 못 늘어난다.
- **신호:** 🟢 `aws_ecs_service` `launch_type = "FARGATE"`, `desired_count`, 오토스케일 max. 🔴 쿼터 값은 가정.
- **시나리오·수준:** T L2 이상, 티어1(ECS)
- **처방:** 티어1: 이벤트 전 쿼터 확인·증설, 최소 태스크 수 상향, 이미지 경량화.
- **검증:** 0→N 태스크 기동 시간 측정.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인). ECS 쿼터 페이지(https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-quotas.html)는 열었으나 구체 수치는 별도 General Reference로 넘겨 이번에 확인하지 못함. ⚠️근거없음

---

## 5. 데이터 계층 병목

### T-040 최대 인스턴스 × 풀 크기 ≤ DB 최대 커넥션
- **무엇/왜:** 앱 계층이 늘어날 때 DB 연결은 인스턴스 수 × 풀 크기로 늘어난다. Postgres `max_connections`는 보통 100(슈퍼유저 예약 3)이고 재시작해야 바뀐다. 작은 관리형 인스턴스는 더 작다.
- **실패 양상:** 피크에 `FATAL: sorry, too many clients already` / `remaining connection slots are reserved`로 모든 인스턴스가 동시에 DB를 잃는다. 확장이 장애를 만든다.
- **신호:** 🟢 풀 설정: SQLAlchemy `pool_size`+`max_overflow`(기본 5+10), `pg.Pool({max})`(node-postgres 기본 10), Prisma `connection_limit`, Django 스레드 수, `asyncpg.create_pool(max_size=)`. 🟢 인스턴스 상한(HPA max, Cloud Run max, 워커 수). 🟢 DB 쪽 `max_connections` 파라미터 그룹 / 인스턴스 크기. 🔴 DB 크기를 모르면 기본값 가정.
- **시나리오·수준:** T L2 이상 필수 (설계 T-CTL-003), L1도 계산 표시
- **처방:** 티어0: Supabase 컴퓨트 크기별 직접 연결 한도(Micro 60, Small 90, Medium 120 …) 안에서, 넘으면 풀러(Supavisor). 티어1: Cloud Run은 인스턴스당 Cloud SQL 100 연결 한도도 있음, max instances 조정 또는 풀러. 티어2: 계산표 + PgBouncer/RDS Proxy.
- **검증:** 정적 곱셈 + 상한 부하 시 `pg_stat_activity` 최대값 < 한도.
- **비용 영향:** 풀러 도입 시 증가(소), DB 크기 상향 시 증가.
- **출처:** https://www.postgresql.org/docs/current/runtime-config-connection.html (기본 보통 100, superuser_reserved 3, 서버 시작 시에만 변경) · https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Limits.html (RDS PostgreSQL 기본 `LEAST({DBInstanceClassMemory/9531392}, 5000)`) · https://docs.cloud.google.com/sql/docs/postgres/quotas (Cloud Run 인스턴스당 Cloud SQL 100 연결) · https://supabase.com/docs/guides/platform/compute-and-disk (크기별 직접 연결·풀러 클라이언트 표) — 2026-10-01 확인. 라이브러리 기본 풀 크기(SQLAlchemy 5+10, node-postgres 10)는 이번에 공식 문서로 재확인하지 않음.

### T-041 서버리스·짧은 연결은 커넥션 풀러로
- **무엇/왜:** 서버리스 함수는 수천 개로 늘고 각자 연결을 연다. 트랜잭션 모드 풀러가 많은 클라이언트 연결을 적은 DB 연결로 다중화한다.
- **실패 양상:** Vercel·Lambda에서 트래픽이 조금만 늘어도 DB 연결 한도에 도달. 연결 생성 자체의 CPU·메모리 오버헤드로 DB가 느려진다.
- **신호:** 🟢 Supabase 연결 문자열 포트 5432(직접/세션) + 서버리스 런타임. 🟢 충족: 포트 6543(트랜잭션 모드), `pgbouncer=true`, RDS Proxy 엔드포인트, Neon pooled 호스트(`-pooler`).
- **시나리오·수준:** T L1 이상 & 서버리스 (설계 T-PRE-003)
- **처방:** 티어0: Supavisor 트랜잭션 모드(6543) + 풀 크기 1 + prepared statement 끄기. 티어1: RDS Proxy(초과 연결은 대기·거절로 셰딩), Cloud SQL은 PgBouncer 사이드카/별도 서비스. 티어2: PgBouncer Deployment.
- **검증:** 동시 1,000 함수 호출에서 DB 백엔드 연결 수가 풀 크기 이내.
- **비용 영향:** 증가(소) — RDS Proxy 과금, PgBouncer 컴퓨트.
- **출처:** https://supabase.com/docs/guides/database/connecting-to-postgres · https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rds-proxy.html (풀링, 즉시 처리 못하면 대기·스로틀, 한도 초과 시 거절) · https://www.pgbouncer.org/features.html — 2026-10-01 확인

### T-042 트랜잭션 풀링과 호환되지 않는 기능
- **무엇/왜:** 트랜잭션 모드 풀러에서는 세션 상태가 유지되지 않는다. `SET`, `LISTEN`, 세션 advisory lock, `WITH HOLD` 커서, SQL `PREPARE`가 깨진다. RDS Proxy는 이런 상태 변경 시 세션을 고정(pinning)해 다중화가 사라진다.
- **실패 양상:** 풀러 도입 후 간헐적 "prepared statement does not exist", `LISTEN` 알림 누락, 분산 락이 다른 연결에서 풀림. RDS Proxy에서 16KB 넘는 문장이나 세션 변경으로 pinning이 늘어 풀링 효과가 없다.
- **신호:** 🟢 `pg_advisory_lock(`(세션 락), `LISTEN `/`pg_notify` 소비, `SET search_path`/`SET statement_timeout`(세션), asyncpg 기본 statement cache, Prisma `pgbouncer=true` 누락.
- **시나리오·수준:** T L2 이상 (풀러를 처방할 때 동반 점검)
- **처방:** prepared statement 끄기(`prepare: false`, asyncpg `statement_cache_size=0`) 또는 PgBouncer `max_prepared_statements` 활성, 세션 락은 `pg_advisory_xact_lock`, `LISTEN`은 직접 연결로 분리.
- **검증:** 풀러 경유 통합 테스트 + 부하 중 오류 0, RDS Proxy pinning 지표 확인.
- **비용 영향:** 중립.
- **출처:** https://www.pgbouncer.org/features.html (트랜잭션 풀링에서 깨지는 기능 목록, `max_prepared_statements`) · https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rds-proxy.html (16KB 넘는 문장은 pinning) · https://supabase.com/docs/guides/database/connecting-to-postgres ("Transaction mode does not support prepared statements") — 2026-10-01 확인

### T-043 풀 크기 과대(크게 잡을수록 느려짐)
- **무엇/왜:** DB가 동시에 효율적으로 처리할 수 있는 활성 연결은 코어 수 근처다. 풀을 크게 잡으면 DB 내부 경합만 늘어난다. 앱 쪽에서 줄 세우는 편이 빠르다.
- **실패 양상:** "느리니까 풀을 100으로"가 DB CPU 컨텍스트 스위칭과 락 경합을 키워 p95를 악화시킨다.
- **신호:** 🟢 풀 크기 ≥ 50, `pool_size × 인스턴스`가 DB vCPU의 수십 배. 🟢 풀 획득 타임아웃(`pool_timeout`, `connectionTimeoutMillis`) 미설정(무한 대기).
- **시나리오·수준:** T L2 이상
- **처방:** 공통: DB 측 활성 연결 목표 ≈ (코어 × 2) + 디스크 수, 앱 풀은 작게 + 획득 타임아웃으로 빠른 실패.
- **검증:** 풀 크기를 바꿔가며 같은 부하의 처리량·p95 곡선 비교.
- **비용 영향:** 감소(DB 크기 상향을 피함).
- **출처:** https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing (공식 라이브러리 위키. `connections = ((core_count * 2) + effective_spindle_count)`, 풀 축소로 응답 ~100ms→~2ms 사례) — 2026-10-01 확인. 프레임워크 공식 문서가 아니라 커넥션 풀 라이브러리 위키이므로 규칙에는 "권장 시작점"으로만 쓴다. ⚠️출처부적격

### T-044 Django 요청마다 연결(CONN_MAX_AGE=0)·스레드당 연결
- **무엇/왜:** Django는 기본 `CONN_MAX_AGE=0`이라 요청마다 DB 연결을 열고 닫는다. 스레드마다 연결을 가지므로 워커×스레드×인스턴스가 연결 수다.
- **실패 양상:** 트래픽이 늘면 연결 생성 비용이 지연의 큰 몫을 차지하고, 스레드를 늘리면 연결 한도를 넘는다.
- **신호:** 🟢 `settings.py`에 `CONN_MAX_AGE` 없음, `OPTIONS: {"pool": ...}` 없음, gunicorn `--threads`·`--workers`.
- **시나리오·수준:** T L1 이상 (Django)
- **처방:** `CONN_MAX_AGE` 양수 + `CONN_HEALTH_CHECKS=True`, 또는 psycopg 풀(`OPTIONS.pool`, 이때 `CONN_MAX_AGE=0`). 외부 풀러 사용 시 풀러에 맡김.
- **검증:** 부하 중 초당 신규 연결 수(`pg_stat_database`의 세션 수 증가율) 비교.
- **비용 영향:** 감소.
- **출처:** https://docs.djangoproject.com/en/stable/ref/databases/ (CONN_MAX_AGE 기본 0, psycopg pool, 스레드 수만큼 연결 필요) — 2026-10-01 확인

### T-045 N+1 쿼리
- **무엇/왜:** 목록 1번 + 항목마다 1번씩 쿼리하면, 페이지 크기·트래픽에 곱해 DB 왕복이 늘어난다. 평시엔 안 보이다가 폭증 때 DB를 먼저 쓰러뜨린다.
- **실패 양상:** 목록 API 하나가 요청당 51쿼리. 트래픽 10배면 DB QPS 510배 증가 체감.
- **신호:** 🟢 Django: 루프 안 `obj.related.field`, `select_related`/`prefetch_related` 없음. 🟢 Prisma: `for ... await prisma.x.findUnique` / `Promise.all(items.map(... findUnique))`, `include` 없음. 🟢 SQLAlchemy lazy 관계 + 루프 접근, `selectinload`/`joinedload` 없음. 🟢 GraphQL resolver에서 DataLoader 없음. 🟢 Supabase JS 루프 안 `.from().select()`.
- **시나리오·수준:** T L1 이상 (L2부터 위험 등급 상향)
- **처방:** 공통: 즉시 로딩(`select_related`/`prefetch_related`, `include`, `selectinload`), 배치 조회(`WHERE id IN`), DataLoader.
- **검증:** 테스트에서 요청당 쿼리 수 단언(`django_assert_num_queries`, 쿼리 로그 카운트), 부하 중 DB QPS/요청 비율.
- **비용 영향:** 감소 — DB 크기 상향 회피.
- **출처:** https://docs.djangoproject.com/en/stable/ref/models/querysets/ (select_related는 JOIN으로 한 쿼리, prefetch_related는 별도 일괄 조회) — 2026-10-01 확인

### T-046 인덱스 누락(순차 스캔)
- **무엇/왜:** WHERE·JOIN·ORDER BY 컬럼에 인덱스가 없으면 테이블 전체를 읽는다. 데이터가 작을 땐 문제없다가 데이터·트래픽이 함께 자라면 급격히 느려진다. 반대로 인덱스는 쓰기 비용을 늘린다.
- **실패 양상:** 사용자 수 증가에 비례해 목록 쿼리 지연이 선형 증가, DB CPU 100%.
- **신호:** 🟢 마이그레이션·스키마에서 FK 컬럼(`user_id`, `post_id`)에 인덱스 없음(Postgres는 FK에 자동 인덱스를 만들지 않음 — 이 부분은 이번에 문서 재확인 안 함), 자주 쓰는 필터(`status`, `created_at`) 정렬 컬럼 인덱스 없음. 🟢 Prisma `@@index`, Django `Meta.indexes`/`db_index`, SQL `CREATE INDEX` 유무. 🟡 쿼리 패턴은 ORM 호출에서 추론. ⚠️근거없음
- **시나리오·수준:** T L1 이상
- **처방:** 공통: 쿼리 패턴별 복합 인덱스, `EXPLAIN`으로 확인, `pg_stat_statements`로 상위 쿼리 추적, 안 쓰는 인덱스 제거. 티어0(Supabase): `index_advisor`.
- **검증:** 대표 쿼리 `EXPLAIN (ANALYZE)`에 `Seq Scan` 없음(대형 테이블), 시드 데이터 100만 행에서 p95.
- **비용 영향:** 감소(읽기), 쓰기·저장소는 소폭 증가.
- **출처:** https://www.postgresql.org/docs/current/indexes-intro.html (인덱스 없으면 전체 스캔, 인덱스는 쓰기 오버헤드, 안 쓰는 인덱스 제거) · https://www.postgresql.org/docs/current/pgstatstatements.html · https://supabase.com/docs/guides/database/query-optimization — 2026-10-01 확인

### T-047 Supabase RLS 정책의 성능
- **무엇/왜:** RLS 정책은 행마다 평가된다. 정책이 거르는 컬럼에 인덱스가 없거나 `auth.uid()`를 행마다 호출하면 단순 조회도 순차 스캔이 된다. 바이브코더 앱에서 가장 흔한 숨은 병목이다.
- **실패 양상:** 테이블이 커질수록 모든 클라이언트 쿼리가 느려지고 Supabase DB CPU가 상시 높다.
- **신호:** 🟢 `supabase/migrations/*.sql`의 `create policy ... using (auth.uid() = user_id)`(select로 감싸지 않음) + `user_id` 인덱스 없음.
- **시나리오·수준:** 티어0(Supabase) & T L1 이상
- **처방:** 티어0: 정책 컬럼 인덱스, `(select auth.uid())`로 감싸기, 쿼리에도 명시적 필터 추가, 필요 시 security definer 함수.
- **검증:** 대표 쿼리 EXPLAIN 비교, 대량 시드 후 p95.
- **비용 영향:** 감소(컴퓨트 업그레이드 회피).
- **출처:** https://supabase.com/docs/guides/database/postgres/row-level-security ("Add an index on every column your policies filter on", select 래핑으로 initPlan 캐시) — 2026-10-01 확인 ⚠️출처부적격

### T-048 오프셋 페이지네이션
- **무엇/왜:** `OFFSET n`은 건너뛴 행도 서버에서 계산한다. 깊은 페이지일수록 느리고, 봇·크롤러가 깊은 페이지를 긁으면 DB가 무거워진다. ORDER BY가 유일하지 않으면 결과도 불안정하다. Firestore는 건너뛴 문서도 읽기로 과금한다.
- **실패 양상:** `?page=5000` 요청이 수 초. 무한 스크롤 중 새 글이 들어오면 중복·누락.
- **신호:** 🟢 `.offset(`, `OFFSET`, Prisma `skip:`, Django 슬라이스 `[start:end]` + `Paginator`, Supabase `.range(from, to)`, Firestore `.offset(`. 🟢 충족: 커서(`WHERE (created_at, id) < (...)`, Prisma `cursor:`, Firestore `startAfter`).
- **시나리오·수준:** T L2 이상 (목록이 핫 경로면 L1부터)
- **처방:** 공통: 키셋(커서) 페이지네이션 + `(정렬키, id)` 복합 인덱스, 최대 페이지 깊이 제한. simple-web-app 게시판이 커서 방식.
- **검증:** 깊은 페이지 요청 지연이 첫 페이지와 같은 수준인지.
- **비용 영향:** 감소(Firestore는 직접 과금 감소).
- **출처:** https://www.postgresql.org/docs/current/queries-limit.html ("rows skipped by an OFFSET clause still have to be computed") · https://firebase.google.com/docs/firestore/best-practices (offset은 건너뛴 문서도 지연·과금, 커서 사용) — 2026-10-01 확인

### T-049 상한 없는 조회(페이지 크기·전체 로드)
- **무엇/왜:** `limit` 없는 목록 API나 클라이언트가 정하는 무제한 `limit`은 데이터가 늘수록 응답 크기·메모리·DB 시간을 무한히 키운다.
- **실패 양상:** `?limit=100000` 한 번에 앱 메모리가 터지고 OOM 재시작. 데이터 성장만으로 어느 날 갑자기 느려진다.
- **신호:** 🟢 `findMany()`에 `take` 없음, `.all()` 후 Python에서 슬라이스, `SELECT *` + LIMIT 없음, `limit = req.query.limit`을 상한 없이 사용. 🟢 Django 대량 루프에 `.iterator()` 없음.
- **시나리오·수준:** T L1 이상
- **처방:** 공통: 서버측 최대 페이지 크기(예: 100) 강제, 대량 처리는 스트리밍·`iterator()`.
- **검증:** 큰 `limit` 요청이 상한으로 잘리는지 테스트.
- **비용 영향:** 감소.
- **출처:** https://docs.djangoproject.com/en/stable/ref/models/querysets/ (`iterator()`는 캐시 없이 평가해 메모리 절약) — 2026-10-01 확인. 상한 강제 자체는 일반 원칙. ⚠️근거없음

### T-050 DB 쪽 타임아웃(statement / idle in transaction / lock)
- **무엇/왜:** Postgres의 `statement_timeout`, `idle_in_transaction_session_timeout`, `lock_timeout`은 기본 0(무제한)이다. 느린 쿼리 하나나 열린 채 방치된 트랜잭션이 연결과 락을 붙잡아 풀 전체를 고갈시킨다.
- **실패 양상:** 폭증 때 느린 쿼리가 쌓여 풀이 가득 차고, 새 요청은 풀 대기에서 타임아웃. 앱이 트랜잭션 중 외부 API를 기다리는 동안 행 락이 유지돼 다른 쓰기가 줄 선다.
- **신호:** 🟢 DB 파라미터 그룹·`ALTER ROLE ... SET statement_timeout` 부재, 연결 문자열 `options=-c statement_timeout=` 없음. 🟢 트랜잭션 블록 안에서 `fetch`/`requests`/LLM 호출.
- **시나리오·수준:** T L2 이상
- **처방:** 공통: 역할·DB 단위 `statement_timeout`(API 경로는 요청 타임아웃보다 짧게), `idle_in_transaction_session_timeout`, 마이그레이션은 `lock_timeout`. PG17+는 `transaction_timeout`도 가능.
- **검증:** `pg_sleep`이 들어간 쿼리가 설정 시간에 취소되는지, 부하 중 `idle in transaction` 세션 수.
- **비용 영향:** 중립.
- **출처:** https://www.postgresql.org/docs/current/runtime-config-client.html (세 값 모두 기본 0=비활성, idle-in-transaction은 락 보유·vacuum 방해 방지) — 2026-10-01 확인

### T-051 읽기 복제본으로 읽기 분산
- **무엇/왜:** 읽기 비중이 압도적이고 캐시로 못 거르는 쿼리(검색·개인화 목록)는 읽기 복제본으로 옮겨 주 DB를 쓰기에 집중시킨다. 복제는 비동기이고 RDS는 복제본 자동 확장을 하지 않는다.
- **실패 양상:** 읽기 폭증이 주 DB CPU를 다 써서 쓰기(결제·글쓰기)까지 느려진다. 복제본을 쓰면서 쓰기 직후 읽기를 복제본에서 하면 방금 쓴 데이터가 안 보인다(C 영역과 연결).
- **신호:** 🟢 단일 `DATABASE_URL`만 존재, ORM 라우터(`DATABASE_ROUTERS`, Prisma `readReplicas` 확장) 없음. 🟢 충족: `aws_db_instance` `replicate_source_db`, Cloud SQL 읽기 복제본.
- **시나리오·수준:** T L2 이상, 캐시(T-061)로 해결되지 않는 읽기 경로가 있을 때만(과잉 주의)
- **처방:** 티어1/2: 복제본 1개 + 읽기 전용 경로 라우팅, 쓰기 후 읽기는 주 DB(C-CTL-006).
- **검증:** 부하 중 주 DB 읽기 비중 감소, `ReplicaLag` 관찰.
- **비용 영향:** 증가 — 복제본은 같은 인스턴스 요율.
- **출처:** https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_ReadRepl.html (읽기 확장 용도, 비동기, 복제본 자동 확장 미지원, 같은 요율 과금) — 2026-10-01 확인

### T-052 핫 파티션·순차 키 (NoSQL)
- **무엇/왜:** DynamoDB는 파티션당 초당 3,000 RCU / 1,000 WCU가 상한이다. Firestore는 순차적으로 증가하는 필드를 인덱싱하면 컬렉션 쓰기가 초당 500으로 제한된다. 키 분포가 쏠리면 전체 용량과 무관하게 한 파티션에서 막힌다.
- **실패 양상:** 이벤트 ID 하나·날짜 키 하나에 쓰기가 몰려 `ProvisionedThroughputExceededException`/경합 오류. 테이블 전체 용량은 남아도는데 실패.
- **신호:** 🟢 DynamoDB 파티션 키가 저카디널리티(`status`, `date`, 고정 `eventId`), Firestore 문서 ID를 `Date.now()`/순번으로 생성, 타임스탬프 필드 인덱싱(단일 필드 인덱스 예외 미설정).
- **시나리오·수준:** T L2 이상 (NoSQL 사용 시)
- **처방:** 티어0(Firestore): 자동 ID, 타임스탬프 인덱스 예외, 새 컬렉션은 500/50/5 규칙(초당 500에서 시작해 5분마다 50%씩)으로 램프. DynamoDB: 고카디널리티 키, 쓰기 샤딩(접미사).
- **검증:** 단일 키 집중 부하 테스트에서 스로틀 0.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html · https://firebase.google.com/docs/firestore/best-practices — 2026-10-01 확인

### T-053 단일 행·문서 핫스팟(카운터·재고·좋아요)
- **무엇/왜:** 조회수·좋아요 수·남은 수량을 한 행(문서)에 `UPDATE ... SET count = count + 1`로 갱신하면, 폭증 시 모든 쓰기가 그 행의 락 하나에 줄 선다.
- **실패 양상:** 인기 글 하나에 좋아요가 몰리면 해당 행 락 대기로 API 전체 풀이 묶인다. Firestore 단일 문서는 쓰기 속도가 제한되어 경합 오류.
- **신호:** 🟢 `increment(`, `F('count') + 1`, `UPDATE ... SET .* = .* \+ 1`, Firestore `FieldValue.increment` 대상이 고정 문서. 🟡 이벤트성 도메인(투표·선착순)과 결합 시 위험 상향.
- **시나리오·수준:** T L2 이상 (선착순·재고 차감은 C L3와 함께 판정)
- **처방:** 공통: Redis `INCR`로 흡수 후 주기적 반영, 샤딩된 카운터, 큐로 직렬화(T-095).
- **검증:** 단일 행에 동시 1,000 갱신 부하 → p95와 락 대기 시간.
- **비용 영향:** 증가(소) — Redis.
- **출처:** https://firebase.google.com/docs/firestore/best-practices (단일 문서 최대 갱신 속도는 워크로드에 따라 다르며 경합 유발) — 2026-10-01 확인. Postgres 행 락 대기 부분은 일반 원칙(출처 미확인). ⚠️근거없음

### T-054 오브젝트 스토리지 요청률(S3 prefix)
- **무엇/왜:** S3는 파티션된 prefix당 초당 최소 3,500 쓰기 / 5,500 읽기를 처리하고, 그 이상은 점진적으로 확장하며 그 사이 503 Slow Down을 낸다.
- **실패 양상:** 모든 업로드를 `uploads/` 한 prefix에 몰아 이벤트 피크에 503. CDN 없이 S3에서 직접 이미지를 서빙하면 읽기 한도에 걸린다.
- **신호:** 🟢 S3 키가 고정 prefix + 순차 이름, 프런트가 S3 URL을 직접 참조(CloudFront 없음).
- **시나리오·수준:** T L3 (또는 미디어 중심 앱 L2)
- **처방:** 티어1/2: 키에 분산 prefix, 읽기는 CDN(CloudFront) 앞단, SDK 재시도 사용.
- **검증:** 업로드 스파이크 중 503 비율.
- **비용 영향:** CDN 추가 시 요청당 비용 변화(대체로 감소).
- **출처:** https://docs.aws.amazon.com/AmazonS3/latest/userguide/optimizing-performance.html — 2026-10-01 확인

### T-055 Redis 단일 스레드와 느린 명령
- **무엇/왜:** Redis는 명령을 하나씩 처리한다. `KEYS`, 큰 집합의 `SMEMBERS`/`SUNION`/`SORT`, 큰 값 하나가 모든 클라이언트를 멈춘다. 캐시·세션·큐를 한 Redis에 몰면 하나의 느린 명령이 전부를 막는다.
- **실패 양상:** 캐시 무효화 코드의 `KEYS cache:*`가 피크에 수백 ms 블로킹, 세션 확인까지 타임아웃.
- **신호:** 🟢 `redis.keys(`, `KEYS `, 큰 리스트·해시 전체 조회, 요청마다 여러 왕복(파이프라인·`MGET` 없음). 🟢 충족: `scan_iter`/`SCAN`.
- **시나리오·수준:** T L2 이상
- **처방:** 공통: `SCAN`, 키 태깅 대신 버전 키, 파이프라인/`MGET`, 역할별 Redis 분리(캐시 대 큐·세션).
- **검증:** 부하 중 `SLOWLOG GET`, `redis-cli --latency`.
- **비용 영향:** 분리 시 증가(소).
- **출처:** https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency/ (단일 스레드, KEYS는 디버깅용, SCAN 사용, 파이프라인·MGET 권장) — 2026-10-01 확인

### T-056 Redis 메모리 정책: 캐시와 큐·세션의 분리
- **무엇/왜:** `maxmemory` 기본 0(64비트에서 무제한), 정책 `noeviction`이면 메모리가 차는 순간 쓰기가 오류다. 캐시 용도면 `allkeys-lru`가 일반적 기본값이지만, 같은 인스턴스에 큐·세션이 있으면 이것들이 축출된다.
- **실패 양상:** 캐시가 메모리를 채워 큐 `XADD`가 OOM 오류(noeviction) → 쓰기 경로 전면 실패. 반대로 LRU에서 세션·큐 메시지가 조용히 사라진다.
- **신호:** 🟢 Terraform `aws_elasticache_parameter_group` `maxmemory-policy`, Memorystore `redis_configs`, 코드에서 같은 `REDIS_URL`로 캐시(`setex`)와 큐(`XADD`/`LPUSH`)·세션 모두 사용.
- **시나리오·수준:** T L2 이상 (Redis에 캐시와 영속성 필요 데이터가 섞일 때)
- **처방:** 캐시 전용 인스턴스는 `allkeys-lru`/`allkeys-lfu`, 큐·세션 인스턴스는 `noeviction` + 메모리 경보. 한 인스턴스면 캐시 키에만 TTL + `volatile-*`(Redis 문서는 분리를 권장). simple-web-app은 noeviction 하나로 운영하며 캐시에 TTL을 둔다.
- **검증:** 메모리를 채우는 부하에서 큐 쓰기 실패 0, 세션 유실 0.
- **비용 영향:** 분리 시 증가(소).
- **출처:** https://redis.io/docs/latest/develop/reference/eviction/ (maxmemory 0 기본, noeviction은 쓰기 오류, allkeys-lru 기본 권장, 캐시와 영속 키는 두 인스턴스로 분리 고려) — 2026-10-01 확인

### T-057 같은 순간 대량 만료(TTL 지터)
- **무엇/왜:** 같은 TTL로 한꺼번에 채운 캐시는 같은 순간 만료된다. Redis 자체도 같은 초에 대량 만료가 몰리면 블로킹될 수 있고, 앱은 동시에 원본으로 몰린다.
- **실패 양상:** 배포·예열 정확히 N초 후 DB 부하가 주기적으로 튄다.
- **신호:** 🟢 고정 TTL 상수(`ex=3600`)로 일괄 예열, `EXPIREAT`에 같은 시각. 🟢 충족: TTL에 무작위 지터.
- **시나리오·수준:** T L2 이상
- **처방:** 공통: TTL ± 10~20% 지터, 스탬피드 보호(T-062)와 함께.
- **검증:** 예열 후 만료 시점 부근 DB QPS 그래프가 평탄한지.
- **비용 영향:** 중립.
- **출처:** https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency/ ("many keys expiring at the same moment can be a source of latency") — 2026-10-01 확인. 앱 측 동시 미스 부분은 일반 원칙. ⚠️근거없음

### T-058 관리형 실시간 서비스 연결 한도(Supabase Realtime 등)
- **무엇/왜:** BaaS 실시간 기능은 플랜별 동시 연결·초당 메시지·채널 조인 한도가 있다. 앱 서버를 아무리 늘려도 이 한도가 상한이다.
- **실패 양상:** Supabase Pro 기본(지출 한도 켜짐) 500 동시 연결을 넘는 순간 `too_many_connections`, 메시지 초과 시 연결 끊김 후 재연결 폭주.
- **신호:** 🟢 `supabase.channel(`, `.on('postgres_changes'`, Firebase `onSnapshot` 다수 구독. 🔴 플랜은 코드에 없으므로 가정(무료/Pro).
- **시나리오·수준:** 티어0 & T L2 이상
- **처방:** 티어0: 플랜 상향 또는 지출 한도 해제(Pro no spend cap 10,000 연결), 구독 수 축소(페이지당 채널 1개), 꼭 실시간이 필요 없는 화면은 폴링+캐시.
- **검증:** 가정 피크 동시 사용자 × 사용자당 연결 수 ≤ 한도, 부하 중 오류 코드 관찰.
- **비용 영향:** 증가 — 플랜 상향.
- **출처:** https://supabase.com/docs/guides/realtime/limits (Free 200 / Pro 500 / Pro no spend cap·Team 10,000 연결, 초당 메시지 100/500/2,500) — 2026-10-01 확인

### T-059 쓰기 경로를 큐로 평탄화
- **무엇/왜:** 쓰기 폭증을 DB가 즉시 처리하게 하면 DB가 상한이다. 큐에 넣고 202를 돌려준 뒤 워커가 일괄 처리하면 DB 부하가 평탄해지고 배치로 효율도 오른다.
- **실패 양상:** 폭증 시 쓰기 요청이 DB 락·커넥션 대기로 타임아웃, 읽기까지 함께 느려진다.
- **신호:** 🟢 POST 핸들러에서 바로 `INSERT`/`create`, 큐 라이브러리(`bullmq`, `celery`, SQS, Redis Streams) 부재. 🟢 충족: `XADD`/`send_message` 후 `202`.
- **시나리오·수준:** T L3 (설계 T-CTL-006), 즉시 일관성이 필요 없는 쓰기만. 결제·재고처럼 즉시 결과가 필요한 쓰기는 C 규칙 우선.
- **처방:** 티어0: Supabase Queues(pgmq)·외부 큐. 티어1: Pub/Sub·SQS + 워커 서비스. 티어2: Redis Streams/SQS + KEDA 워커.
- **검증:** 쓰기 스파이크 중 DB 쓰기 TPS가 평탄하고 큐 길이가 증가 후 소진되는지.
- **비용 영향:** 증가(큐·워커), DB 크기 상향 회피로 상쇄 가능.
- **출처:** https://keda.sh/docs/2.21/scalers/redis-streams/ · https://sre.google/sre-book/addressing-cascading-failures/ (큐는 작게, 용량 초과 시 거절) — 2026-10-01 확인. "큐가 쓰기를 평탄화한다"는 설계 문서 T-CTL-006(S7)의 원칙.

### T-060 큐 자체의 한도(백프레셔 없는 무한 큐)
- **무엇/왜:** 큐는 시간을 사는 장치지 용량을 늘리는 장치가 아니다. 길이 상한이 없으면 처리 지연이 끝없이 늘고 메모리(Redis)가 찬다.
- **실패 양상:** 큐 지연이 사용자 기대(수 초)를 넘어 몇 십 분, Redis OOM으로 큐 전체 장애.
- **신호:** 🟢 `XADD`에 `MAXLEN` 없음 + 앱에서 길이 확인 없음, BullMQ 큐 길이 검사 없음. 🟢 충족: 길이 확인 후 `503 + Retry-After`(simple-web-app `QUEUE_MAX_LEN`).
- **시나리오·수준:** T L3
- **처방:** 공통: 최대 길이 또는 최대 대기 시간, 초과 시 즉시 거절(503/429 + Retry-After).
- **검증:** 워커를 멈추고 쓰기 부하 → 상한에서 거절이 시작되는지, Redis 메모리 한도 이내.
- **비용 영향:** 중립.
- **출처:** https://sre.google/sre-book/addressing-cascading-failures/ ("small queue lengths relative to the thread pool size", 초과 시 503) — 2026-10-01 확인

---

## 6. 캐시와 전송

### T-061 읽기 핫 경로의 앱 캐시
- **무엇/왜:** 같은 데이터를 많은 사용자가 읽는 경로(목록 첫 페이지, 인기 글, 설정)는 짧은 TTL 캐시만으로 DB 부하를 수십 배 줄인다.
- **실패 양상:** 폭증 시 동일 쿼리가 DB에 초당 수천 번, DB가 먼저 쓰러진다.
- **신호:** 🟢 GET 핸들러가 매번 DB 조회, Redis·`unstable_cache`·`use cache`·`django.core.cache` 사용 없음. 🟡 엔드포인트 이름(`/posts`, `/feed`, `/products`)과 인증 불필요 여부로 읽기 핫 경로 추정.
- **시나리오·수준:** T L2 이상 (설계 T-CTL-004)
- **처방:** 티어0: Next.js `revalidate`/`use cache`, Vercel CDN 캐시(T-064). 티어1/2: Redis 캐시(짧은 TTL) + 무효화 경로.
- **검증:** 부하 중 캐시 적중률(`keyspace_hits/(hits+misses)`), DB QPS 대 요청 RPS 비율.
- **비용 영향:** 감소(DB) / 증가(소, Redis).
- **출처:** https://redis.io/docs/latest/develop/reference/eviction/ (Redis 캐시 용도, 적중률 계산) · https://nextjs.org/docs/app/guides/incremental-static-regeneration — 2026-10-01 확인

### T-062 캐시 스탬피드(동시 미스) 방지
- **무엇/왜:** 인기 키가 만료되는 순간 수백 요청이 동시에 원본을 조회한다. 캐시가 있는데도 피크마다 DB가 튄다.
- **실패 양상:** TTL 3초 캐시가 3초마다 DB에 수백 쿼리 폭탄을 만든다. 재시작 직후 빈 캐시에서 같은 일.
- **신호:** 🟢 `get → miss → db → set` 패턴에 락(`SET NX`)·single-flight·요청 합치기 없음. 🟢 충족: `SET key NX PX`, `stale-while-revalidate`, Next.js ISR(백그라운드 재생성), CDN 요청 합치기.
- **시나리오·수준:** T L2 이상, L3 필수
- **처방:** 공통: 미스 시 락 1개만 원본 조회 + 나머지는 stale 반환(simple-web-app `cache:*`/`stale:*`), HTTP 레벨에서는 `stale-while-revalidate`. 티어1(GCP): Cloud CDN 요청 합치기(기본 활성).
- **검증:** 인기 키를 강제 만료시키고 동시 500 요청 → 원본 쿼리 1~소수.
- **비용 영향:** 감소.
- **출처:** https://www.rfc-editor.org/rfc/rfc5861 (stale-while-revalidate: 백그라운드 재검증 동안 stale 반환) · https://docs.cloud.google.com/cdn/docs/caching (request coalescing 기본 활성) · https://sre.google/sre-book/addressing-cascading-failures/ (cold cache) — 2026-10-01 확인

### T-063 정적 자산: 해시 파일명 + immutable + CDN
- **무엇/왜:** JS·CSS·이미지를 앱 서버가 매번 서빙하면 폭증 때 앱 용량을 자산 전송에 쓴다. 해시가 붙은 파일은 1년 `immutable`로 CDN·브라우저에 맡긴다.
- **실패 양상:** 페이지 하나에 자산 30개 → 앱 RPS가 30배. 캐시 헤더가 없으면 브라우저가 휴리스틱으로 캐시해 배포 후 옛 파일이 섞인다.
- **신호:** 🟢 Express `express.static` 옵션에 `maxAge`/`immutable` 없음, nginx 정적 location에 `expires`/`Cache-Control` 없음, 빌드 산출물 해시 파일명(`index-DXzgUePv.js`) 존재 여부. 🟢 티어0(Vercel·Next.js)는 자동 `max-age=31536000, immutable`.
- **시나리오·수준:** T L1 이상
- **처방:** 티어0: 기본 충족. 티어1/2: CloudFront/Cloud CDN 앞단, 해시 자산 `public, max-age=31536000, immutable`, HTML은 `no-cache`.
- **검증:** 응답 헤더 정적 검사 + CDN 적중률.
- **비용 영향:** 감소 — 앱 컴퓨트·이그레스 감소(CDN 전송비는 추가).
- **출처:** https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching (해시 URL + 1년 max-age + immutable, Cache-Control 없으면 휴리스틱 캐시) · https://vercel.com/docs/caching/cdn-cache · https://nextjs.org/docs/app/guides/self-hosting — 2026-10-01 확인 ⚠️출처부적격

### T-064 동적 응답의 CDN 캐시(s-maxage)와 캐시 불가 조건
- **무엇/왜:** 로그인과 무관한 API·SSR 페이지는 `s-maxage` 몇 초만으로도 엣지에서 대부분을 흡수한다. 그러나 `Set-Cookie`, `Authorization` 요청 헤더, `private`/`no-store`, `Vary: Cookie`가 붙으면 CDN이 캐시하지 않는다.
- **실패 양상:** 캐시 헤더를 넣었는데 미들웨어가 모든 응답에 세션 쿠키를 갱신(`Set-Cookie`)해서 적중률 0%.
- **신호:** 🟢 Route Handler·API 응답의 `Cache-Control`, 전역 미들웨어의 `Set-Cookie`/`res.cookie`, `Vary` 설정, `x-vercel-cache` 기대값. 🟢 CloudFront 캐시 정책 TTL.
- **시나리오·수준:** T L2 이상 (공개 읽기 경로가 있을 때)
- **처방:** 티어0: `Cache-Control: public, s-maxage=N, stale-while-revalidate=M`(Vercel은 GET/HEAD, 200 등, 10MB 이하, Set-Cookie·Authorization 없음일 때만 캐시). 티어1/2: CloudFront/Cloud CDN `USE_ORIGIN_HEADERS`.
- **검증:** 두 번째 요청의 `x-vercel-cache: HIT`/`X-Cache: Hit from cloudfront`/`Age` 헤더.
- **비용 영향:** 감소.
- **출처:** https://vercel.com/docs/caching/cdn-cache (캐시 가능 조건, Vary: Cookie 비캐시, 지역별 캐시) · https://docs.cloud.google.com/cdn/docs/caching (Set-Cookie·private 비캐시, 기본 TTL 3,600초) — 2026-10-01 확인

### T-065 의도치 않은 동적 렌더링(Next.js)
- **무엇/왜:** Next.js에서 `cookies()`, `headers()`, `searchParams`, `fetch(..., { cache: 'no-store' })`, `revalidate = 0`을 쓰면 라우트가 동적 렌더링이 되어 요청마다 서버 함수가 돈다. 레이아웃에 하나만 있어도 하위 전체가 동적이 된다.
- **실패 양상:** 정적이어야 할 마케팅·목록 페이지가 요청마다 함수 실행 + DB 조회. 트래픽이 곧 함수 비용과 DB 부하.
- **신호:** 🟢 `app/layout.tsx`에서 `cookies()`/`headers()` 호출, `export const dynamic = 'force-dynamic'`, `cache: 'no-store'`, `revalidate = 0`. 🟢 빌드 출력의 라우트 표시(ƒ Dynamic).
- **시나리오·수준:** 티어0/Next.js & T L1 이상
- **처방:** 개인화 부분만 클라이언트 컴포넌트나 별도 경로로 분리, 나머지는 ISR(`revalidate` 높게) 또는 `use cache`.
- **검증:** `next build` 출력에서 핫 경로가 Static/ISR인지, 응답 `Cache-Control`이 `private, no-cache, no-store`가 아닌지.
- **비용 영향:** 감소(큰 폭).
- **출처:** https://nextjs.org/docs/app/guides/incremental-static-regeneration (`revalidate` 0 또는 `no-store`가 있으면 동적, 높은 revalidate 권장) · https://nextjs.org/docs/app/guides/self-hosting (동적 페이지는 `private, no-cache, no-store`) — 2026-10-01 확인

### T-066 캐시 키 폭발(고카디널리티 Vary·쿼리스트링)
- **무엇/왜:** `Vary: User-Agent`/`Cookie`, 추적 파라미터(`utm_*`)가 캐시 키에 들어가면 사실상 매 요청이 다른 키라 적중률이 0에 가깝다.
- **실패 양상:** CDN을 붙였는데 원본 부하가 그대로.
- **신호:** 🟢 `Vary: User-Agent`, `Vary: Cookie`, CloudFront 캐시 정책에 모든 쿼리스트링·쿠키 포함.
- **시나리오·수준:** T L2 이상
- **처방:** 공통: 필요한 헤더만 Vary, 캐시 키에서 추적 파라미터 제외.
- **검증:** CDN 적중률 지표.
- **비용 영향:** 감소.
- **출처:** https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching ("Avoid Vary: User-Agent") · https://vercel.com/docs/caching/cdn-cache (Vary는 엔트리를 곱으로 늘림, Cookie는 캐시 안 함) — 2026-10-01 확인 ⚠️출처부적격

### T-067 CDN 최소 TTL이 private 응답을 캐시하는 함정
- **무엇/왜:** CloudFront 캐시 정책의 최소 TTL이 0보다 크면 원본이 `no-cache`/`no-store`/`private`를 보내도 최소 TTL만큼 캐시한다. 성능 튜닝으로 최소 TTL을 올리면 개인 응답이 남에게 보일 수 있다.
- **실패 양상:** 개인화 API 응답이 다른 사용자에게 노출(보안 사고이자 캐시 설정 사고).
- **신호:** 🟢 Terraform `aws_cloudfront_cache_policy` `min_ttl > 0`이 동적·인증 경로 behavior에 적용.
- **시나리오·수준:** CDN 사용 시 모든 수준 (보안 담당과 공유)
- **처방:** 동적·인증 경로 behavior는 `min_ttl = 0` + CachingDisabled 정책, 공개 경로만 TTL.
- **검증:** 로그인 사용자 A·B로 같은 개인 API 호출 → 응답이 섞이지 않음.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Expiration.html ("If your minimum TTL is greater than 0, CloudFront uses the cache policy's minimum TTL, even if the Cache-Control: no-cache, no-store, and/or private directives are present") — 2026-10-01 확인

### T-068 응답 압축(gzip·Brotli)
- **무엇/왜:** JSON·HTML·JS는 압축으로 크기가 크게 준다. 대역폭이 상한이 되는 폭증 상황(모바일 망, 인스턴스 이그레스 한도)에서 처리량을 늘린다.
- **실패 양상:** 큰 JSON 목록이 무압축으로 전송돼 인스턴스 대역폭(예: Cloud Run 표준 이그레스 600Mbps)과 모바일 지연이 병목.
- **신호:** 🟢 nginx `gzip on` 여부와 `gzip_types`, Express `compression()` 미들웨어, CloudFront `Compress`/`EnableAcceptEncodingBrotli`. 🟢 티어0는 플랫폼 기본.
- **시나리오·수준:** T L1 이상
- **처방:** 엣지(CDN)에서 압축하는 것을 우선(앱 CPU 절약), 아니면 리버스 프록시에서. CloudFront는 1,000~10,000,000바이트 객체만 압축하고 `Content-Length`가 필요.
- **검증:** `Accept-Encoding: br, gzip` 요청의 `Content-Encoding` 응답 헤더.
- **비용 영향:** 감소(전송량).
- **출처:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/ServingCompressedFiles.html · https://docs.cloud.google.com/run/quotas (인스턴스 이그레스 대역폭) — 2026-10-01 확인

### T-069 큰 요청 본문과 플랫폼 본문 한도
- **무엇/왜:** 플랫폼마다 요청 본문 한도가 있다(Vercel 4.5MB, Cloud Run HTTP/1 32MiB, Express 기본 100kb). 큰 업로드를 앱이 받으면 한도에 걸리고 메모리·시간을 점유한다.
- **실패 양상:** 사진 업로드가 Vercel에서 413 `FUNCTION_PAYLOAD_TOO_LARGE`. Express에서 JSON 한도를 50mb로 올려 폭증 시 메모리 폭발.
- **신호:** 🟢 `bodyParser.json({ limit: '50mb' })`, `express.json({limit})`, Next.js `bodyParser.sizeLimit`, `client_max_body_size`, 파일 업로드 경로가 앱 함수를 통과.
- **시나리오·수준:** T L1 이상 (설계 TIER-001: 4.5MB 초과 본문은 티어0 함수 불가)
- **처방:** 업로드는 서명 URL 직행(T-002), 앱 본문 한도는 작게 유지(프록시에서도 제한).
- **검증:** 한도 초과 요청이 앱 도달 전 413으로 거절되는지.
- **비용 영향:** 감소.
- **출처:** https://vercel.com/docs/functions/limitations · https://docs.cloud.google.com/run/quotas · https://expressjs.com/en/resources/middleware/body-parser.html (기본 100kb, 초과 413, 높은 한도는 메모리 증가) — 2026-10-01 확인

### T-070 이미지 최적화를 요청 경로에서 하는 비용
- **무엇/왜:** `next/image` 자체 호스팅은 런타임에 이미지를 변환한다(sharp). CPU·메모리 집약 작업이 웹 인스턴스에서 돈다. 신규 이미지가 몰리면 웹 경로가 느려진다.
- **실패 양상:** 상품 목록 첫 노출 때 이미지 변환으로 CPU 포화, API 지연. glibc 리눅스에서 sharp 메모리 과다 사용.
- **신호:** 🟢 `next/image` + 자체 호스팅(Dockerfile) + `images.loader` 없음/`unoptimized` 아님, 서버 코드 `sharp(`, `Pillow` 리사이즈.
- **시나리오·수준:** T L2 이상 (이미지 중심 앱)
- **처방:** 이미지 CDN/외부 로더, 업로드 시 사전 변환(워커), `minimumCacheTTL`로 재변환 감소.
- **검증:** 새 이미지 대량 요청 중 웹 API p95 영향.
- **비용 영향:** 외부 이미지 서비스 비용 vs 웹 컴퓨트 절약.
- **출처:** https://nextjs.org/docs/app/guides/self-hosting (Image Optimization 절, 런타임 최적화, glibc 메모리 설정) — 2026-10-01 확인

### T-071 스트리밍 응답(SSE·LLM 토큰) 버퍼링
- **무엇/왜:** LLM 토큰 스트리밍·SSE·Next.js 스트리밍은 중간 프록시가 버퍼링하면 첫 바이트가 끝까지 지연되고 연결이 오래 붙어 있는다. 연결 수가 곧 동시성이다.
- **실패 양상:** nginx 기본 버퍼링으로 스트리밍이 한 번에 몰려 오고, 응답 시간 동안 인스턴스 동시성 슬롯을 점유해 확장이 커진다.
- **신호:** 🟢 `text/event-stream`, `ReadableStream`, `StreamingResponse`, AI SDK `streamText` + nginx `proxy_buffering` 기본, `X-Accel-Buffering` 없음. 🟢 ALB+Lambda(버퍼링).
- **시나리오·수준:** T L1 이상 (스트리밍 사용 시)
- **처방:** 프록시 버퍼링 끄기(`X-Accel-Buffering: no`), LB가 청크 전송 지원 확인, 스트림 연결 수를 동시성 계산에 포함.
- **검증:** 첫 토큰 도착 시간(TTFB) 측정, 동시 스트림 N개에서 인스턴스 수.
- **비용 영향:** 연결 유지 시간만큼 증가(Cloud Run 요청 기반은 응답 끝까지 과금).
- **출처:** https://nextjs.org/docs/app/guides/self-hosting (Streaming and Suspense 절, nginx `X-Accel-Buffering: no`, 일부 LB 버퍼링) — 2026-10-01 확인 ⚠️출처부적격

### T-072 함수·컴퓨트 리전과 DB 리전 불일치
- **무엇/왜:** Vercel Functions는 기본 `iad1`(미국 동부)에서 돈다. DB가 서울(Supabase `ap-northeast-2`)이면 쿼리마다 태평양을 왕복한다. N+1과 겹치면 요청당 수 초가 된다.
- **실패 양상:** 로컬에서는 빠른데 배포 후 모든 API가 수백 ms~수 초. 폭증 시 함수 실행 시간이 길어져 동시성·비용이 같이 늘어난다.
- **신호:** 🟢 `vercel.json` `regions` 미설정(기본 iad1) + Supabase URL/DB 호스트의 리전(`*.supabase.co` 프로젝트 리전은 코드에 없을 수 있음 → 🟡), `DATABASE_URL` 호스트의 리전 문자열(`ap-northeast-2.rds.amazonaws.com`, `aws-0-ap-northeast-2.pooler.supabase.com`).
- **시나리오·수준:** 모든 수준 (지연), T L1 이상에서 비용·동시성 영향
- **처방:** 티어0: 함수 리전을 DB 리전으로(`regions: ["icn1"]`). 티어1/2: 컴퓨트·DB·캐시를 같은 리전에.
- **검증:** 배포 환경에서 단순 쿼리 1개 API의 서버 처리 시간 측정(Server-Timing).
- **비용 영향:** 감소(실행 시간 단축).
- **출처:** https://vercel.com/docs/functions/limitations ("Runs in a single region by default (`iad1`)", Pro·Enterprise는 복수 리전) — 2026-10-01 확인

### T-073 지역 분산 사용자: 엣지 캐시 우선, 멀티 리전은 마지막
- **무엇/왜:** 사용자가 여러 대륙에 있으면 첫 수단은 CDN 캐시(정적·공개 응답)이고, 동적 처리까지 가까이 두려면 멀티 리전 + 지연 기반 라우팅이 필요하다. 후자는 데이터 일관성·비용 부담이 크다.
- **실패 양상:** 해외 사용자 TTFB가 수백 ms. 반대로 국내 전용 서비스에 멀티 리전을 깔면 과잉(COST-007).
- **신호:** 🟡 i18n 로케일 수(`next-intl`, `i18next` 로케일 목록), 통화·국가 선택. 🟢 Route 53 latency 레코드, 복수 리전 Terraform.
- **시나리오·수준:** T L2 이상이고 사용자 분포가 다국적일 때. 멀티 리전 동적 처리는 T L3 + D L3에서만 검토
- **처방:** 티어0: Vercel CDN + 함수 리전 최적화. 티어1/2: CloudFront/Cloud CDN, 필요 시 Route 53 지연 기반 라우팅으로 리전 분산.
- **검증:** 대륙별 합성 측정 TTFB.
- **비용 영향:** CDN 증가(소), 멀티 리전은 큰 증가.
- **출처:** https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-policy-latency.html · https://vercel.com/docs/caching/cdn-cache — 2026-10-01 확인

---

## 7. 요청 처리와 런타임

### T-074 인스턴스 동시성·워커 수 설정
- **무엇/왜:** 한 인스턴스가 동시에 처리할 요청 수가 앱의 실제 병렬도와 맞아야 한다. Cloud Run 기본은 CLI/Terraform에서 80×vCPU(최대 1,000), uvicorn은 기본 워커 1개. 너무 높으면 한 인스턴스가 과부하, 너무 낮으면 인스턴스가 과하게 늘어난다.
- **실패 양상:** 동기 Python(gunicorn sync 워커 1개)에 Cloud Run concurrency 80 → 요청 79개가 줄 서서 타임아웃. 반대로 concurrency 1은 스파이크 때 인스턴스 기동 폭주.
- **신호:** 🟢 Cloud Run `containerConcurrency`/`max_instance_request_concurrency`, uvicorn `--workers`/`WEB_CONCURRENCY`, gunicorn `-w`/`--threads`/`-k uvicorn.workers.UvicornWorker`, Node `cluster`/PM2 `instances`. 🟢 Firebase Functions 2nd gen `concurrency`(기본 80, 1 vCPU 이상 필요).
- **시나리오·수준:** T L1 이상
- **처방:** 티어1: 동기 앱은 concurrency = 워커×스레드, 비동기 앱은 기본값에서 측정 후 조정, concurrency>1이면 1 vCPU 이상. 티어2: 프로세스 수를 CPU requests에 맞춤.
- **검증:** concurrency 값을 바꿔가며 인스턴스당 처리량·p95 측정.
- **비용 영향:** 적정값이 인스턴스 수를 최소화.
- **출처:** https://docs.cloud.google.com/run/docs/about-concurrency · https://docs.cloud.google.com/run/docs/configuring/services/cpu (concurrency>1이면 최소 1 vCPU) · https://uvicorn.dev/settings/ (workers 기본 `$WEB_CONCURRENCY` 또는 1) · https://firebase.google.com/docs/functions/manage-functions — 2026-10-01 확인

### T-075 이벤트 루프 블로킹(Node·Python async)
- **무엇/왜:** Node와 Python asyncio는 요청을 하나의 루프에서 처리한다. 동기 I/O나 CPU 작업 하나가 루프를 막으면 그 인스턴스의 모든 요청이 멈춘다.
- **실패 양상:** FastAPI `async def` 안의 `requests.get`/동기 DB 드라이버, Node의 `fs.readFileSync`·`crypto.pbkdf2Sync`·큰 `JSON.parse` 하나로 인스턴스 전체 지연. CPU는 낮아 오토스케일도 안 됨(T-012).
- **신호:** 🟢 Node 서버 코드의 `*Sync(` 호출(`readFileSync`, `pbkdf2Sync`, `execSync`, `zlib.*Sync`), `bcrypt.hashSync`. 🟢 FastAPI/Starlette `async def` 핸들러 안 `requests.`, `time.sleep`, `psycopg2`, 동기 SQLAlchemy `Session`. 🟢 중첩 수량자 정규식(ReDoS).
- **시나리오·수준:** T L1 이상
- **처방:** 비동기 API 사용, 동기 코드는 `def` 핸들러(FastAPI가 스레드풀에서 실행)나 `run_in_threadpool`, CPU 작업은 worker_threads/별도 워크로드(T-076).
- **검증:** 정적 검사 + 부하 중 이벤트 루프 지연(`perf_hooks.monitorEventLoopDelay`, asyncio debug slow callback).
- **비용 영향:** 감소.
- **출처:** https://nodejs.org/en/learn/asynchronous-work/dont-block-the-event-loop (동기 API 금지, 워커 풀 기본 4) · https://fastapi.tiangolo.com/async/ ("Calling blocking code inside async def blocks the event loop", def는 외부 스레드풀) — 2026-10-01 확인

### T-076 무거운 작업 격리(비밀번호 해시·이미지·PDF·LLM 후처리)
- **무엇/왜:** argon2/bcrypt 해시, 이미지·PDF 변환, 대형 연산은 CPU를 독점한다. 일반 API와 같은 인스턴스에 있으면 로그인 폭주가 모든 읽기를 늦춘다.
- **실패 양상:** 이벤트 오픈 시 로그인 폭주 → 해시가 CPU를 다 써서 세션 확인·목록 API까지 타임아웃(simple-web-app이 auth-verify를 분리한 이유).
- **신호:** 🟢 `argon2`, `bcrypt`, `passlib`, `sharp`, `Pillow`, `puppeteer`/`playwright`(PDF), `ffmpeg`가 API 서비스 의존성에 있음 + 별도 워크로드 없음. 🟢 해시 동시성 제한(세마포어) 없음.
- **시나리오·수준:** T L3 (설계 T-CTL-008), L2에서 권장
- **처방:** 티어0: 관리형 인증(Supabase Auth 등)으로 해시 자체를 외부화. 티어1: 별도 Cloud Run 서비스/큐 워커. 티어2: 별도 Deployment + HPA, 인스턴스당 동시 해시 수 제한 + 대기 초과 시 503.
- **검증:** 로그인 스파이크 중 읽기 API p95가 기준선 대비 크게 나빠지지 않음.
- **비용 영향:** 증가(소) — 별도 워크로드 최소 인스턴스.
- **출처:** https://nodejs.org/en/learn/asynchronous-work/dont-block-the-event-loop (crypto CPU 집약, 별도 워커 풀) · https://12factor.net/concurrency — 2026-10-01 확인 ⚠️출처부적격

### T-077 LLM·유료 외부 API 호출 경로
- **무엇/왜:** LLM 호출은 지연이 길고(수 초~수십 초) 공급자 레이트 리밋(RPM·입력/출력 토큰)과 급증 제한(acceleration limit)이 있다. 트래픽 폭증이 그대로 공급자 429와 비용 폭증으로 이어진다.
- **실패 양상:** 피크에 429가 쏟아지고 앱이 즉시 재시도해 상황 악화. 갑작스러운 사용량 급증 자체가 acceleration limit 429를 부른다. 월 지출 한도 도달 시 다음 달까지 전면 중단.
- **신호:** 🟢 `@anthropic-ai/sdk`, `anthropic`, `openai`, `ai`(Vercel AI SDK), `langchain` 사용 + 사용자별 한도·큐·캐시 없음, `retry-after` 처리 없음. 🔴 공급자 티어는 가정.
- **시나리오·수준:** T L1 이상 (COST-008과 함께)
- **처방:** 사용자별 요청·토큰 한도, `retry-after` 존중 + 지터 백오프, 동일 프롬프트 응답 캐시와 프롬프트 캐싱, 급증 대비 큐로 평탄화, 스트리밍(T-071).
- **검증:** 공급자 429를 모킹 주입 → 앱이 재시도 폭주 없이 사용자에게 대기 응답.
- **비용 영향:** 증가 요인 통제(큰 감소 가능).
- **출처:** https://platform.claude.com/docs/en/api/rate-limits (RPM·ITPM·OTPM, 토큰 버킷, 429 + `retry-after`, 급증 시 acceleration limit, 티어별 월 지출 한도, 캐시된 입력 토큰은 대부분 모델에서 ITPM 미포함) — 2026-10-01 확인 ⚠️출처부적격

### T-078 타임아웃 계층 정렬(클라이언트 > LB > 앱 > DB)
- **무엇/왜:** 바깥 계층 타임아웃이 안쪽보다 짧으면 사용자는 포기했는데 서버는 계속 일한다. 안쪽에 타임아웃이 없으면 느린 하류가 스레드·연결을 끝없이 붙잡는다. 데드라인을 하류로 전파해야 헛일을 줄인다.
- **실패 양상:** LB 60초에 끊겼는데 앱은 5분짜리 쿼리를 계속 실행, 재시도까지 겹쳐 같은 작업이 3중으로 돈다.
- **신호:** 🟢 LB `idle_timeout`, Cloud Run `timeout`(기본 300초, 최대 3,600초), Vercel `maxDuration`(기본 300초), 앱 서버 timeout, HTTP 클라이언트 `timeout`(axios 기본 0=무제한 — 이번에 문서 미확인), `fetch`에 `AbortSignal.timeout` 없음, Python `requests` `timeout=` 없음, DB `statement_timeout`(T-050).
- **시나리오·수준:** T L2 이상 (L1은 외부 호출 타임아웃만)
- **처방:** 공통: 바깥 > 안쪽 순으로 감소하는 예산, 외부 호출마다 명시 타임아웃, 남은 시간을 하류로 전달.
- **검증:** 하류 지연 주입(예: DB `pg_sleep`, 외부 API 지연) → 앱이 예산 안에 실패 응답하고 자원 회수.
- **비용 영향:** 감소(헛일 제거).
- **출처:** https://sre.google/sre-book/addressing-cascading-failures/ (deadline propagation) · https://builder.aws.com/content/3EumjoZascWd1oZiEgL8ORlv3qE/timeouts-retries-and-backoff-with-jitter (지연 백분위수로 타임아웃 선택) · https://docs.cloud.google.com/run/quotas · https://vercel.com/docs/functions/limitations — 2026-10-01 확인

### T-079 앱 keep-alive 타임아웃 < LB idle 타임아웃이면 502
- **무엇/왜:** LB는 백엔드 연결을 재사용한다. 앱이 LB보다 먼저 유휴 연결을 닫으면 LB가 닫히는 중인 연결에 요청을 보내 502가 난다. ALB 기본 idle 60초인데 uvicorn 기본 keep-alive는 5초다.
- **실패 양상:** 부하가 낮다가 높아지는 순간마다 간헐적 502가 소량 발생. 원인 찾기가 매우 어렵다.
- **신호:** 🟢 ALB `idle_timeout.timeout_seconds`(기본 60) 대 uvicorn `--timeout-keep-alive`(기본 5), gunicorn `--keep-alive`, Node `server.keepAliveTimeout`, nginx `keepalive_timeout`(nginx가 앱 앞에 있으면 nginx↔앱 구간도 같은 원리).
- **시나리오·수준:** T L1 이상 (LB 뒤 자체 서버)
- **처방:** 앱 keep-alive > LB idle(예: ALB 60초면 앱 65~75초).
- **검증:** 저부하↔고부하를 반복하는 부하로 502 0건.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-load-balancer-attributes.html ("configure the idle timeout of your application to be larger than the idle timeout configured for the load balancer. Otherwise ... 502", 기본 60초, 1~4,000초) · https://uvicorn.dev/settings/ (keep-alive 기본 5초) — 2026-10-01 확인. Node·gunicorn 기본값은 이번에 수치 미확인.

### T-080 플랫폼 요청 최대 시간과 장시간 작업
- **무엇/왜:** 요청 경로에 수 분짜리 작업이 있으면 플랫폼 상한(Vercel 300초 기본/Pro 800초, Cloud Run 최대 60분)에 걸리고, 그동안 동시성 슬롯을 점유해 확장 수요가 커진다.
- **실패 양상:** 보고서 생성이 504 `FUNCTION_INVOCATION_TIMEOUT`. 폭증 시 장시간 요청이 슬롯을 다 차지해 짧은 요청까지 대기.
- **신호:** 🟢 `maxDuration` 상향, `export const maxDuration = 800`, 핸들러 안 긴 루프·대량 외부 호출. 🟢 Cloud Run `timeout` 3600.
- **시나리오·수준:** T L1 이상 (설계 TIER-001/002)
- **처방:** 작업 큐 + 상태 조회(202 + 폴링/웹훅), Vercel은 Workflows, Cloud Run Jobs.
- **검증:** 최장 경로 실행 시간 측정 대 상한, 장시간 작업 중 짧은 요청 p95.
- **비용 영향:** 감소.
- **출처:** https://vercel.com/docs/functions/limitations · https://docs.cloud.google.com/run/quotas — 2026-10-01 확인

### T-081 재시도 폭증 방지(백오프·지터·재시도 예산·한 계층만)
- **무엇/왜:** 여러 계층이 각각 재시도하면 곱으로 늘어난다(3계층 × 3회 재시도 = DB에 64배). 과부하 때 재시도가 과부하를 고착시킨다.
- **실패 양상:** DB가 잠깐 느려지자 프런트·API·SDK가 동시에 재시도해 회복 불능. 클라이언트들이 같은 간격으로 재시도해 파도 모양 부하.
- **신호:** 🟢 `axios-retry`, `p-retry`, `tenacity`, `urllib3 Retry`, TanStack Query 기본 재시도(3회, 지수 백오프, 지터 언급 없음), SDK 기본 재시도 + 서버측 재시도 동시 존재. 🟢 고정 간격 `setTimeout(retry, 1000)`.
- **시나리오·수준:** T L2 이상
- **처방:** 공통: 재시도는 한 계층에서만, 지수 백오프 + 지터, 재시도 예산(요청당 최대 3회, 전체의 10% 이내), 4xx·429는 `Retry-After` 존중, 비멱등 요청 재시도는 C 규칙과 함께.
- **검증:** 하류 503 주입 중 하류 도착 요청 수가 원래 요청의 1.1배 근처인지.
- **비용 영향:** 감소.
- **출처:** https://sre.google/sre-book/addressing-cascading-failures/ (4^3=64배 예시, 지수 백오프·재시도 예산) · https://sre.google/sre-book/handling-overload/ (요청당 3회, 클라이언트당 재시도 10%) · https://builder.aws.com/content/3EumjoZascWd1oZiEgL8ORlv3qE/timeouts-retries-and-backoff-with-jitter · https://tanstack.com/query/latest/docs/framework/react/guides/query-retries — 2026-10-01 확인

### T-082 아웃바운드 연결 재사용과 플랫폼 아웃바운드 한도
- **무엇/왜:** 외부 API를 요청마다 새 연결로 부르면 TLS 핸드셰이크 지연과 소켓 고갈이 생긴다. Node `http.Agent`는 문서상 `keepAlive` 기본 false다. Cloud Run은 인스턴스당 아웃바운드 연결 생성 속도·열린 연결 수 한도가 있다.
- **실패 양상:** 피크에 외부 호출 지연이 두 배, `EADDRNOTAVAIL`/소켓 고갈, 플랫폼 아웃바운드 한도 오류.
- **신호:** 🟢 요청마다 `new https.Agent()`/`axios.create()`, Python 핸들러 안 `requests.get`(Session 재사용 없음), `httpx.AsyncClient()`를 요청마다 생성.
- **시나리오·수준:** T L2 이상
- **처방:** 전역 클라이언트·keep-alive 에이전트, 연결 풀 크기 상한.
- **검증:** 부하 중 초당 신규 TCP 연결 수.
- **비용 영향:** 감소.
- **출처:** https://nodejs.org/api/http.html (`new Agent` 옵션 `keepAlive` 기본 false) · https://docs.cloud.google.com/run/quotas (인스턴스당 아웃바운드 연결 초당 700·분당 5,000, 열린 연결 50,000) — 2026-10-01 확인

### T-083 메모리 한도와 런타임 힙 설정 정렬(GC)
- **무엇/왜:** 컨테이너 메모리 한도를 넘으면 커널이 OOM으로 죽인다. 런타임(Node V8, Go GC)은 컨테이너 한도를 모르고 힙을 키울 수 있다. 부하가 오를수록 동시 요청의 메모리가 쌓여 피크에 집단 OOM이 난다.
- **실패 양상:** 피크에 Pod가 차례로 OOMKilled → 남은 Pod로 부하 집중 → 연쇄 OOM. 또는 한도 근처에서 GC가 폭주해 응답이 멈춘다(Go 한도 과소 설정 시 thrashing).
- **신호:** 🟢 k8s `resources.limits.memory`, Cloud Run memory, Node `--max-old-space-size`/`NODE_OPTIONS`, Go `GOMEMLIMIT`, Python 워커 수 × 워커당 메모리. 🟢 uvicorn `--limit-max-requests`(누수 완화).
- **시나리오·수준:** T L2 이상
- **처방:** 힙 상한을 컨테이너 한도의 일부로(Go는 한도의 90~95%), 동시성 × 요청당 메모리 ≤ 한도, 누수 의심 시 워커 재활용.
- **검증:** 피크 부하 + 큰 응답 경로 동시 호출 중 OOMKilled 0, 메모리 그래프 상한 여유.
- **비용 영향:** 정확한 한도로 중립~증가.
- **출처:** https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/ (메모리 한도는 OOM kill로 사후 강제) · https://go.dev/doc/gc-guide (GOMEMLIMIT 소프트 한도, 5~10% 여유, 과소 설정 시 thrashing) · https://nodejs.org/api/cli.html (`--max-old-space-size`) · https://uvicorn.dev/settings/ — 2026-10-01 확인

### T-084 CPU limit 스로틀링
- **무엇/왜:** k8s CPU limit은 커널 스로틀링으로 강제된다. limit을 requests에 너무 가깝게 두면 순간 버스트(기동, GC, TLS)에서 스로틀되어 지연 꼬리가 길어지고 probe가 실패한다.
- **실패 양상:** 평균 CPU는 낮은데 p99와 probe 타임아웃이 튀고, 그 때문에 재시작.
- **신호:** 🟢 `limits.cpu`가 `requests.cpu`와 같거나 매우 작음(예: 250m)인데 단일 스레드가 아닌 런타임. 🟡 지연 꼬리 원인은 실측 필요.
- **시나리오·수준:** T L2 이상, 티어2
- **처방:** 티어2: 지연 민감 서비스는 CPU limit을 넉넉히 또는 두지 않고 requests로 보장(팀 정책에 따라), 기동 시엔 startupProbe.
- **검증:** 컨테이너 `cpu.stat`의 throttled 비율, p99 비교.
- **비용 영향:** 중립(requests 기준 과금·배치).
- **출처:** https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/ ("CPU limits are enforced by CPU throttling") — 2026-10-01 확인

### T-085 LB 라우팅 알고리즘(요청 비용이 불균등할 때)
- **무엇/왜:** 라운드로빈은 요청 비용이 비슷할 때만 공평하다. 수 ms 요청과 수 초 요청(LLM, 리포트)이 섞이면 일부 인스턴스에 무거운 요청이 몰린다.
- **실패 양상:** 평균 사용률은 낮은데 특정 인스턴스만 포화되어 p99가 높다.
- **신호:** 🟢 ALB 대상 그룹 `load_balancing.algorithm.type` 기본(round_robin) + 지연 편차 큰 경로 혼재. 🟡 경로별 처리 시간 편차는 코드 추론(LLM·파일 처리 경로).
- **시나리오·수준:** T L2 이상
- **처방:** 티어1/2(AWS): `least_outstanding_requests`(slow start와 병행 불가), 또는 무거운 경로를 별도 서비스로 분리(T-076).
- **검증:** 혼합 부하에서 인스턴스별 in-flight 요청 편차.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-target-group-attributes.html — 2026-10-01 확인

### T-086 클러스터 내부 DNS 병목
- **무엇/왜:** Pod가 많고 외부 호출이 잦으면 CoreDNS 질의가 폭증한다. UDP 연결 추적 경쟁으로 5초 단위 DNS 지연이 생기고, 피크에 외부 호출 지연이 이유 없이 튄다.
- **실패 양상:** 스케일 아웃 후 외부 API 호출 p99가 5초 근처로 튐, CoreDNS CPU 포화.
- **신호:** 🟢 NodeLocal DNSCache DaemonSet(`node-local-dns`) 없음 + Pod 수 많음(HPA 상한 합 큼) + 외부 호스트 호출 다수. 🟢 CoreDNS 오토스케일러 유무.
- **시나리오·수준:** T L3, 티어2
- **처방:** 티어2: NodeLocal DNSCache, CoreDNS 수평 오토스케일, 앱 측 연결 재사용(T-082)으로 조회 자체 감소.
- **검증:** 부하 중 DNS 조회 지연 분포.
- **비용 영향:** 증가(소, 노드당 DaemonSet).
- **출처:** https://kubernetes.io/docs/tasks/administer-cluster/nodelocaldns/ (conntrack 경쟁, DNS 타임아웃 꼬리 지연 감소) — 2026-10-01 확인

### T-087 DNS TTL과 트래픽 전환 속도
- **무엇/왜:** 레코드 TTL이 길면 LB·리전 변경이 리졸버 캐시 때문에 늦게 반영된다. 이벤트 직전 인프라를 바꾸거나 트래픽을 다른 엔드포인트로 돌리는 계획이 있으면 TTL을 미리 낮춰 둬야 한다. 짧은 TTL은 조회 비용·지연을 늘린다.
- **실패 양상:** 새 LB로 옮겼는데 사용자 일부가 하루 넘게 옛 IP로 접속.
- **신호:** 🟢 Terraform `aws_route53_record` `ttl`(예: 86400), Cloud DNS `ttl`. 🟢 alias 레코드 사용 여부.
- **시나리오·수준:** T L2 이상 (예고 이벤트 전 인프라 변경 시)
- **처방:** 변경 전 TTL을 300초 수준으로 낮추고, 확인 후 다시 올림.
- **검증:** 변경 후 여러 리졸버에서 조회 결과 수렴 시간.
- **비용 영향:** 짧은 TTL은 DNS 쿼리 비용 증가(소).
- **출처:** https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resource-record-sets-values-basic.html (긴 TTL은 비용·지연 감소 대신 변경 반영이 느림, 변경 전 300초 권장) — 2026-10-01 확인

### T-088 클라이언트 폴링·동기화된 요청 파도
- **무엇/왜:** 프런트가 모든 사용자에게 같은 간격으로 폴링하거나, 탭 포커스 복귀 때 일제히 재요청하면 사용자 수에 비례하는 상시 부하와 동기화된 파도가 생긴다.
- **실패 양상:** 동시 접속 1만 명 × 5초 폴링 = 상시 2,000 RPS. 이벤트 공지 후 모두가 동시에 새로고침.
- **신호:** 🟢 TanStack Query `refetchInterval`, `setInterval(fetch`, SWR `refreshInterval`, `refetchOnWindowFocus` 기본(활성). 🟢 실시간 구독 대신 짧은 폴링.
- **시나리오·수준:** T L2 이상
- **처방:** 폴링 간격에 지터, 캐시 가능한 폴링 엔드포인트(CDN `s-maxage`), 필요 시 SSE/실시간 구독, 서버가 `Retry-After`로 간격 조절.
- **검증:** 가정 동시 접속 × 폴링 주기로 RPS 계산 + 부하 테스트에 포함.
- **비용 영향:** 감소.
- **출처:** https://tanstack.com/query/latest/docs/framework/react/guides/query-retries (재시도 지수 백오프, 지터 언급 없음) — 2026-10-01 확인. 폴링 부하 계산과 지터 권장은 일반 원칙(출처 미확인). ⚠️출처부적격 ⚠️근거없음

---

## 8. 보호 장치: 리밋·백프레셔·대기열

### T-089 레이트 리밋(사용자 기준 + IP 기준)
- **무엇/왜:** 한 클라이언트가 용량을 독점하지 못하게 하고, 폭증 때 공정하게 나눈다. CGNAT·공용 와이파이 뒤에서는 IP 하나에 많은 사용자가 있으므로 IP 리밋은 느슨하게, 로그인 사용자 리밋은 엄격하게.
- **실패 양상:** 리밋이 없으면 스크립트 하나가 전체를 잡아먹는다. IP 리밋만 빡빡하면 재난·행사장에서 정상 사용자 대량 차단.
- **신호:** 🟢 `express-rate-limit`, `slowapi`, `django-ratelimit`, nginx `limit_req`, `@upstash/ratelimit`, WAF rate-based rule. 🟢 키: `req.ip`만 쓰는지, 사용자 ID/세션 키를 쓰는지. 🟢 프록시 뒤 실제 IP(`trust proxy`, `set_real_ip_from`) 설정 여부(없으면 모든 사용자가 LB IP 하나로 묶임).
- **시나리오·수준:** T L3 필수(설계 T-CTL-007), L1부터 로그인·가입에는 권장
- **처방:** 티어0: Vercel WAF/Upstash 리밋. 티어1/2: 엣지(WAF·Cloud Armor) 거친 IP 리밋 + 앱/게이트웨이의 사용자 리밋. 429 + `Retry-After`.
- **검증:** 단일 사용자 과다 요청 → 429, 같은 IP의 다른 사용자는 정상.
- **비용 영향:** 감소(남용 차단).
- **출처:** https://nginx.org/en/docs/http/ngx_http_limit_req_module.html (leaky bucket, burst/nodelay, 기본 상태 코드 503이므로 429로 바꿔야 함, 빈 키는 미집계) · https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/429 — 2026-10-01 확인 ⚠️출처부적격

### T-090 엣지 레이트 리밋의 근사성과 창 크기
- **무엇/왜:** WAF·Cloud Armor 리밋은 근사치이고 평가 창이 길다(AWS WAF 60~600초, 최소 한도 10). 초 단위 스파이크 제어에는 느리고, 정확한 쿼터 강제용이 아니다.
- **실패 양상:** WAF 리밋만 믿었는데 5분 창이라 첫 1분 폭주는 그대로 통과. 리전별로 따로 계산돼 합계가 한도를 넘는다(Cloud Armor).
- **신호:** 🟢 `aws_wafv2_web_acl` `rate_based_statement` `evaluation_window_sec`·`limit`, Cloud Armor `rate_limit_options` `interval_sec`.
- **시나리오·수준:** T L3
- **처방:** 엣지는 거친 남용 차단(IP·ASN), 정밀한 초 단위·사용자 단위 리밋은 게이트웨이·앱에서. 둘을 겹친다.
- **검증:** 짧은 버스트 부하에서 엣지·앱 각각의 차단 시점 기록.
- **비용 영향:** WAF 규칙·요청당 과금 증가.
- **출처:** https://docs.aws.amazon.com/waf/latest/developerguide/waf-rule-statement-type-rate-based-high-level-settings.html (창 60/120/300/600초, 기본 300, 최소 한도 10, 정확한 일치 보장 안 함) · https://docs.cloud.google.com/armor/docs/rate-limiting-overview (throttle·rate_based_ban, 근사치, 리전별 독립, 쿼터 강제용 아님) — 2026-10-01 확인

### T-091 백프레셔·로드 셰딩(동시 처리 한도와 빠른 거절)
- **무엇/왜:** 용량을 넘는 요청을 줄 세우면 지연만 늘고 결국 모두 타임아웃된다(처리량은 있는데 유효 처리량은 0). 동시 처리 한도를 두고 넘으면 즉시 503/429로 거절하면 받은 요청은 제시간에 끝난다.
- **실패 양상:** 피크에 모든 요청이 30초 대기 후 타임아웃, 오토스케일이 따라잡아도 이미 쌓인 대기열 때문에 회복이 늦다.
- **신호:** 🟢 uvicorn `--limit-concurrency`, 세마포어(`asyncio.Semaphore`, `p-limit`) + 대기 타임아웃, 서버 `maxConnections`, RDS Proxy 연결 대기 한도. 🔴 대부분 앱에는 없음 → 미충족으로 가정.
- **시나리오·수준:** T L3 (설계 T-CTL-006과 같은 축)
- **처방:** 공통: 인스턴스당 in-flight 상한 + 대기 시간 상한(예: 해시 슬롯 5초) 초과 시 503 + `Retry-After`. 티어1: Cloud Run concurrency가 1차 상한.
- **검증:** 용량 2배 부하에서 수락된 요청의 p95가 기준 이내, 나머지는 빠른 거절.
- **비용 영향:** 중립(상한까지 확장 비용은 그대로).
- **출처:** https://uvicorn.dev/settings/ (`--limit-concurrency` 초과 시 503) · https://sre.google/sre-book/addressing-cascading-failures/ (in-flight 초과 시 503) · https://sre.google/sre-book/handling-overload/ — 2026-10-01 확인

### T-092 요청 중요도별 셰딩·디그레이드
- **무엇/왜:** 과부하 때 모든 요청을 똑같이 거절하면 결제·로그인 같은 핵심 경로도 함께 죽는다. 중요도를 나눠 부가 기능(추천, 통계, 미리보기)부터 끄거나 캐시 결과로 대체한다.
- **실패 양상:** 피크에 추천 API가 DB를 잡아먹어 주문이 실패.
- **신호:** 🟡 기능 플래그(`unleash`, `launchdarkly`, `flagsmith`) 존재 여부, 경로별 리밋 차등. 🔴 대부분 없음.
- **시나리오·수준:** T L3
- **처방:** 경로를 핵심/부가로 분류해 부가 경로에 더 낮은 리밋, 과부하 플래그로 부가 기능 차단, 캐시 결과로 대체.
- **검증:** 과부하 주입 중 핵심 경로 성공률 유지, 부가 경로만 저하.
- **비용 영향:** 감소(피크 용량 축소 가능).
- **출처:** https://sre.google/sre-book/handling-overload/ (CRITICAL_PLUS·CRITICAL·SHEDDABLE 구분, 낮은 중요도부터 거절) · https://sre.google/sre-book/addressing-cascading-failures/ (graceful degradation) — 2026-10-01 확인

### T-093 선착순·오픈 이벤트 대기열(virtual waiting room)
- **무엇/왜:** 선착순·티켓 오픈처럼 수요가 용량을 몇 배 넘는 것이 확실하면, 다 받으려 확장하기보다 입장 속도를 정해 대기열로 보내는 편이 공정하고 싸다.
- **실패 양상:** 오픈 순간 전원이 결제 단계까지 들어와 DB·결제 연동이 동시에 무너지고, 새로고침 폭주로 상황 악화.
- **신호:** 🟡 도메인(티켓·한정판·수강신청·쿠폰), `openAt`/`saleStart` 필드, 재고 수량 필드, 카운트다운. 🟢 충족: Cloudflare Waiting Room 설정, 자체 토큰 대기열.
- **시나리오·수준:** T L3 (선착순 신호)
- **처방:** 티어0/1/2 공통: 엣지 대기열(Cloudflare Waiting Room: 활성 사용자 수·분당 신규 사용자 기준, FIFO), 또는 Redis 기반 입장 토큰. AWS의 Virtual Waiting Room 솔루션은 2026-10-01 기준 제공 중단 페이지만 남아 있음.
- **검증:** 용량 5배 부하에서 입장 사용자의 p95 유지, 대기열 길이와 입장 속도 기록.
- **비용 영향:** 감소(피크 확장 대신 입장 제어). 대기열 서비스 비용 추가.
- **출처:** https://developers.cloudflare.com/waiting-room/about/ · https://aws.amazon.com/solutions/implementations/virtual-waiting-room-on-aws/ (해당 솔루션 "no longer available") — 2026-10-01 확인

### T-094 봇·크롤러 트래픽
- **무엇/왜:** 공개 서비스의 상당한 트래픽은 크롤러·스크래퍼·AI 에이전트다. 비싼 경로(검색, 깊은 페이지, LLM 엔드포인트)를 봇이 두드리면 사람 트래픽 없이도 확장·비용이 터진다.
- **실패 양상:** 새벽에 인스턴스가 최대까지 늘고 DB CPU 100%, 원인은 단일 스크래퍼의 깊은 페이지네이션.
- **신호:** 🟢 `robots.txt` 부재/전체 허용, 공개 검색·목록 API에 리밋 없음, 오프셋 페이지(T-048). 🟢 충족: WAF Bot Control, Vercel BotID/방화벽, Cloudflare Bot 관리.
- **시나리오·수준:** T L1 이상(공개 서비스), 비용 축
- **처방:** 티어0: 플랫폼 봇 방어. 티어1/2: WAF Bot Control(공통·표적 보호 수준, 추가 과금) 또는 Cloud Armor, 비싼 경로에 인증·리밋.
- **검증:** 액세스 로그의 User-Agent·ASN 분포, 봇 차단 후 비용 비교.
- **비용 영향:** 감소(봇 제거) / 보호 서비스 비용 증가.
- **출처:** https://docs.aws.amazon.com/waf/latest/developerguide/waf-bot-control.html — 2026-10-01 확인

### T-095 핫 키 쓰기 직렬화(선착순 재고·투표)
- **무엇/왜:** 같은 자원에 동시 쓰기가 몰리는 경로는 DB 락 대신 단일 지점(Redis 원자 연산, 단일 소비자 큐)으로 직렬화해 처리량을 높인다. 정합성 규칙(C L3)은 그대로 지킨다.
- **실패 양상:** 마지막 100개 재고에 1만 명이 동시에 들어와 행 락 대기로 풀 고갈, 결과적으로 정상 주문까지 실패.
- **신호:** 🟢 `SELECT ... FOR UPDATE` 핫 행 + 높은 동시성 경로, 재고 필드 차감. 🟢 충족: Redis `DECR`/Lua 선점 후 비동기 확정, 단일 파티션 큐.
- **시나리오·수준:** T L3 & C L3 (C 담당과 함께 판정)
- **처방:** Redis 원자 선점 → 큐 → DB 확정(아웃박스는 C 영역), 대기열(T-093)과 결합.
- **검증:** 동시 1만 요청에서 처리량·초과 판매 0(C 검증과 동시).
- **비용 영향:** 증가(소).
- **출처:** 일반 원칙(출처 미확인). 관련 근거로 T-053의 Firestore 단일 문서 경합 문서만 확인. ⚠️근거없음

### T-096 CPU 집약 경로의 인스턴스당 동시성 제한
- **무엇/왜:** 해시·이미지 변환처럼 CPU를 쓰는 작업은 인스턴스당 동시 실행 수를 코어 수 근처로 제한해야 메모리·CPU가 폭주하지 않는다. 대기가 길면 빨리 거절해 다른 인스턴스로 가게 한다.
- **실패 양상:** 해시 100개가 동시에 돌아 메모리 한도 초과 OOM(argon2는 메모리 집약), 인스턴스가 죽으며 부하가 다른 인스턴스로 이동해 연쇄.
- **신호:** 🟢 `argon2`/`bcrypt`/`sharp` 호출 주변에 세마포어·`p-limit` 없음, argon2 `memory_cost`·`parallelism` 값.
- **시나리오·수준:** T L3
- **처방:** 인스턴스당 동시 N(예: 4) + 대기 상한 초과 시 503 + `Retry-After`(simple-web-app `HASH_CONCURRENCY`, `HASH_QUEUE_TIMEOUT_SECONDS`).
- **검증:** 로그인 스파이크 중 OOMKilled 0, 거절은 빠르게.
- **비용 영향:** 중립.
- **출처:** https://nodejs.org/en/learn/asynchronous-work/dont-block-the-event-loop (작업 시간 편차를 줄이고 CPU 작업은 별도 풀로) · https://sre.google/sre-book/addressing-cascading-failures/ — 2026-10-01 확인

### T-097 429/503 응답과 Retry-After 계약
- **무엇/왜:** 서버가 거절할 때 언제 다시 오라고 알려야 클라이언트가 동기화된 재시도로 되돌아오지 않는다. 클라이언트도 이 값을 따라야 한다.
- **실패 양상:** 503만 주고 시간 정보가 없어 클라이언트가 즉시 재시도, 거절이 부하를 키운다.
- **신호:** 🟢 거절 응답에 `Retry-After` 헤더 유무(`res.set('Retry-After'`, `headers={"Retry-After": ...}`), nginx `limit_req_status 429`. 🟢 프런트가 429/503에서 `Retry-After`를 읽는지.
- **시나리오·수준:** T L2 이상
- **처방:** 서버: 429/503 + `Retry-After`(약간의 지터). 클라이언트: 존중 + 사용자에게 대기 표시.
- **검증:** 리밋 초과 시 헤더 존재 정적·동적 확인, 클라이언트 재시도 간격 관찰.
- **비용 영향:** 감소.
- **출처:** https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/429 (RFC 6585, Retry-After) · https://platform.claude.com/docs/en/api/rate-limits (실제 API 사례: 429 + retry-after) — 2026-10-01 확인 ⚠️출처부적격

### T-098 하류 SaaS·API 게이트웨이 스로틀 한도
- **무엇/왜:** 앱 앞의 API Gateway, 뒤의 결제·메일·지도·인증 SaaS 모두 계정 단위 스로틀이 있다. 앱이 확장해도 이들이 상한이다. API Gateway는 계정·리전 단위 토큰 버킷으로 제한하고 429를 준다.
- **실패 양상:** 이벤트 피크에 이메일 인증 SaaS 한도로 가입이 막히고, 앱은 재시도로 더 두드린다.
- **신호:** 🟢 `aws_api_gateway_*`/`aws_apigatewayv2_*` 스테이지 스로틀 설정, 외부 SDK(`@sendgrid/mail`, `resend`, `twilio`, `stripe`) 호출이 요청 경로에 동기적으로 있음. 🔴 각 SaaS 한도는 가정.
- **시나리오·수준:** T L2 이상
- **처방:** 요청 경로의 외부 호출을 큐로 비동기화(메일·알림), 사전 한도 상향 요청, 클라이언트 측 토큰 버킷으로 송신 속도 제한.
- **검증:** 외부 호출 모킹에 429 주입 → 사용자 경로는 성공(비동기 처리).
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html (토큰 버킷, 계정·리전 단위, 429, 최선 노력) — 2026-10-01 확인. 계정 기본 수치는 별도 쿼터 페이지로 넘어가 이번에 확인하지 않음.

---

## 새 축·규칙 후보

설계 문서의 4개 시나리오(D/T/U/C)와 1차 규칙 목록에 바로 넣기 어렵거나, 반영을 제안하는 항목이다.

1. **"성능 위생(지연)" 축 또는 T L0에서도 적용되는 공통 규칙군.** N+1(T-045), 인덱스 누락(T-046), RLS 성능(T-047), 함수·DB 리전 불일치(T-072), 상한 없는 조회(T-049)는 트래픽 폭증이 없어도(T L0 사내 도구여도) 사용자 체감 지연을 만든다. 지금 구조에서는 T L1 이상에만 걸리므로, 수준과 무관한 "모든 수준" 규칙 범주(가칭 `PERF-*`)를 두거나 T 규칙에 `applies_at: all` 속성을 허용할 것을 제안한다.

2. **"하류 용량 정합" 계산 규칙을 독립 규칙 종류로.** T-017·T-030·T-040·T-058·T-098은 모두 "앱 상한 × 단위 소비 ≤ 하류 한도" 형태다(DB 연결, 노드 용량, Realtime 연결, SaaS 한도, 계정 vCPU 쿼터). 규칙 종류 표(§8.2)에 `capacity`(정적 곱셈 검사)를 추가하면 같은 엔진으로 일관되게 판정하고, 리포트에 "최악값 계산표"(simple-web-app `docs/deploy.md`의 601 커넥션 표 형식)를 자동 생성할 수 있다.

3. **스케일 속도 예산을 가정 표(§4.3)에 연결.** T L3 가정이 "1분 안에 20배"인데, 노드 부팅만 80~120초(GKE 문서)라 티어2는 여유 용량 없이는 원리상 불가능하다. 규칙: `T=3 & 티어2 & 노드 여유 용량 없음 → 위험`은 이미 T-CTL-009에 있으나, 근거 수치(80~120초)와 "부하 시작→Ready" 측정을 P4의 필수 산출물로 명시하고, 측정값이 가정 램프보다 길면 자동으로 min replicas 상향을 처방하도록 되먹임(§17.5)에 넣을 것을 제안한다.

4. **"과잉 보호" 비용 규칙.** 이 영역 처방(읽기 복제본 T-051, 멀티 리전 T-073, LCU 예약 T-032, 자리표시 Pod T-029, WAF Bot Control T-094, provisioned concurrency T-021)은 비용이 크다. COST-001처럼 "T≤1인데 읽기 복제본·LCU 예약·자리표시 Pod가 있음 → 과잉" 규칙을 COST 범주에 추가할 것을 제안한다.

5. **플랫폼 기본값 함정 규칙(코드에 아무것도 없는 것이 위험 신호).** 리전 기본 iad1(T-072), uvicorn keep-alive 5초 대 ALB 60초(T-079), Postgres 타임아웃 0(T-050), Redis maxmemory 0·noeviction(T-056), KEDA min 0(T-016), Express 세션 MemoryStore(T-001), nginx limit_req 기본 503(T-089). 탐지기는 "설정이 있는 것"뿐 아니라 "설정이 없어서 기본값이 적용되는 것"을 사실로 내야 한다. 사실 모델(§5)에 `defaulted: true`와 기본값 출처를 담는 필드를 추가할 것을 제안한다.

6. **봇·AI 에이전트 트래픽은 T와 보안 사이의 별도 축 후보.** 봇(T-094)은 의도된 사용자 증가가 아닌데 T의 확장·비용을 움직인다. "공개 비싼 경로 노출도"(인증 없는 검색·LLM·깊은 목록 엔드포인트 수)를 별도 지표로 계산해 T 수준과 보안 담당 양쪽에 입력으로 줄 것을 제안한다.

7. **선착순(T-093·T-095)은 T와 C가 동시에 L3가 되는 복합 시나리오.** 대기열은 T 통제, 재고 차감 정합성은 C 통제지만 처방이 서로 얽힌다(Redis 선점→큐→DB 확정). 규칙 형식에 "다른 시나리오 통제와 묶어 처방" 관계(`co_requires: [C-CTL-005]`)를 추가할 것을 제안한다.

8. **실시간 연결 수는 RPS와 다른 용량 단위.** 웹소켓·SSE·LLM 스트리밍(T-006, T-058, T-071)은 "동시 연결 수 × 연결 시간"이 용량이다. 가정 표에 T 수준별 "동시 연결 수" 기본값(예: 동시 접속 = 평시 동시 사용자 × 탭당 연결 수)을 추가해야 Cloud Run 인스턴스 기반 과금, Supabase Realtime 한도 판정이 가능하다.
