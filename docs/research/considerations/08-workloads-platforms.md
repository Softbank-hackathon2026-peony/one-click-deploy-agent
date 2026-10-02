# 워크로드 유형·도메인·플랫폼

- 작성일·확인일: 2026-10-01
- 담당 영역: W (워크로드 유형·도메인·플랫폼별 특화 요소)
- 상위 문서: `docs/superpowers/specs/2026-10-01-infrafit-design.md` (시나리오 D/T/U/C × L0~L3, §4.2 필요 수준 규칙, §4.3 가정, §7.1 도메인, §9 티어)

## 범위

다른 카탈로그(장애/DR, 트래픽, 배포, 정합성, 보안, 비용, 관측)는 시나리오별 **일반 통제**를 다룬다. 이 문서는 그 위에 얹히는 **"어떤 종류의 앱이냐, 어떤 플랫폼 위에 있느냐"에 따라 달라지는 요소**만 다룬다. 결과물은 두 가지 규칙의 재료다.

1. **도메인·워크로드 → 필요 수준·가정 매핑** (`rules/domains.yaml`, `rules/assumptions.yaml`, `rules/levels/*.yaml`)
2. **티어 선택·제외 규칙** (`rules/tiers/*.yaml`) — 플랫폼 수치 한도와 함정

수치는 모두 2026-10-01에 공식 문서를 열어 확인한 값이다. 확인하지 못한 항목은 "일반 원칙(출처 미확인)"으로 표시했다. 판정 시에는 이 문서의 수치가 아니라 규칙 YAML의 `sources.checked_at`을 기준으로 다시 확인해야 한다(설계 §8.3).

### 신호 표시
- 🟢 결정적 탐지 가능: 의존성·설정·스키마에서 기계적으로 확정 (탐지기, 신뢰도 high)
- 🟡 후보 신호: 탐지기가 후보로 올리고 ② 추론이 확정해야 함 (신뢰도 medium)
- 🔴 위험 신호: 발견되면 해당 플랫폼·수준에서 곧바로 "부족" 또는 "티어 제외"로 이어짐

### 항목 ID
- W-001 ~ W-049: 파트 1 워크로드 유형별 요소
- W-050 ~ W-099: 파트 3 플랫폼별 제약과 함정

## 목차

- [파트 1. 워크로드 유형별 요소](#파트-1-워크로드-유형별-요소)
  - 실시간: W-001 ~ W-005
  - 미디어·업로드: W-006 ~ W-010
  - AI·LLM: W-011 ~ W-016
  - 백그라운드·배치·크론: W-017 ~ W-020
  - 메시지 발송(이메일·푸시·SMS): W-021 ~ W-024
  - 검색·분석·리포트: W-025 ~ W-027
  - 멀티테넌트 SaaS·공개 API·웹훅 발송: W-028 ~ W-032
  - IoT·게임·커머스·예약: W-033 ~ W-036
  - 콘텐츠·Next.js: W-037 ~ W-038
  - 사내 도구·재난 알림·규제·위치: W-039 ~ W-042
  - 추가 유형(협업 편집, 코드 실행, 크롤러, 모바일 백엔드): W-043 ~ W-046
- [파트 2. 도메인 → 필요 수준·가정 매핑](#파트-2-도메인--필요-수준가정-매핑)
- [파트 3. 플랫폼별 제약과 함정](#파트-3-플랫폼별-제약과-함정)
  - 티어 0: Vercel W-050 ~ W-056, Netlify W-057 ~ W-058, Cloudflare W-059 ~ W-062, Supabase W-063 ~ W-066, Firebase W-067 ~ W-068, Railway W-069 ~ W-070, Render W-071 ~ W-073, Fly.io W-074 ~ W-075, Replit W-076
  - 티어 1: Cloud Run W-077 ~ W-079, ECS Fargate·App Runner W-080 ~ W-082, Azure Container Apps W-083
  - 티어 2: GKE·EKS W-084 ~ W-087
  - 플랫폼 교차 비교: W-088 ~ W-093
- [플랫폼 한도 요약표](#플랫폼-한도-요약표)
- [새 축·규칙 후보](#새-축규칙-후보)

---

## 파트 1. 워크로드 유형별 요소

### 실시간 (웹소켓·SSE·채팅·프레즌스)

### W-001 웹소켓 브로드캐스트의 인스턴스 간 팬아웃
- **해당:** 실시간 채팅, 알림, 협업, 라이브 대시보드 (socket.io, ws, Django Channels, FastAPI WebSocket)
- **무엇/왜:** 웹소켓 서버가 2대 이상이 되면 A 인스턴스에 붙은 사용자에게 B 인스턴스에서 생긴 메시지가 전달되지 않는다. 인스턴스 사이를 잇는 어댑터(Redis Pub/Sub 등)가 필요하다.
- **실패 양상:** 1대일 때는 정상, 오토스케일로 2대가 되는 순간 "일부 사용자만 메시지를 못 받음". 부하 테스트 없이 운영에서 처음 드러난다.
- **신호:** 🟢 `socket.io`/`ws`/`channels` 의존성 + `@socket.io/redis-adapter`·`channels_redis` 부재 (`ws.no_shared_adapter`) · 🟢 `io.emit`/`io.to(room).emit`/`group_send` 호출 · 🔴 위 조합 + HPA·min/max instances > 1
- **시나리오·수준:** T≥1 (T-CTL-001 상태 없음, T-PRE-001). 티어 0 Vercel에서도 같은 문제(W-054).
- **처방:** 티어 0: 관리형 실시간(Supabase Realtime, Pusher/Ably) 또는 Vercel Marketplace Redis · 티어 1: Cloud Run은 Memorystore Redis Pub/Sub 또는 Firestore 실시간 리스너, ECS는 ElastiCache · 티어 2: Redis + 어댑터, 연결 수 지표로 HPA
- **검증:** 인스턴스 2개 강제(min=2) 후 서로 다른 인스턴스에 붙은 두 클라이언트 사이 메시지 도달률 100% 확인
- **비용 영향:** 최소 Redis 1개(월 수십 달러 수준) 추가
- **출처:** https://socket.io/docs/v4/using-multiple-nodes/ ("Without an adapter, broadcasts on one server won't reach clients connected to other servers"), https://docs.cloud.google.com/run/docs/triggering/websockets (Redis Pub/Sub 또는 Firestore로 인스턴스 간 동기화 권장)

### W-002 HTTP 롱폴링 폴백과 스티키 세션
- **해당:** socket.io(기본 전송이 롱폴링으로 시작), SockJS, SignalR 폴백
- **무엇/왜:** 롱폴링은 한 세션이 여러 HTTP 요청으로 이루어지므로 같은 서버로 가야 한다. 스티키 세션이 없으면 핸드셰이크 오류가 난다. 클라이언트를 웹소켓 전용으로 두면 스티키 세션이 필요 없다.
- **실패 양상:** 인스턴스가 2대 이상일 때 "Session ID unknown"/400 오류, 연결이 반복해서 끊겼다 붙음. Cloud Run·ACA의 세션 어피니티는 best effort라 근본 해결이 아니다.
- **신호:** 🟢 `socket.io-client` 사용 + `transports: ['websocket']` 미설정 · 🟡 Nginx/Ingress에 `sticky`/`affinity` 설정 유무
- **시나리오·수준:** T≥1. 티어 0 Vercel은 `transports: ['websocket']`이 필수(공식 예제에 "required" 주석).
- **처방:** 코드: 클라이언트 `transports: ['websocket']` (P2 코드 처방) · 티어 1: 세션 어피니티는 보조 수단으로만 · 티어 2: Ingress 쿠키 어피니티는 롱폴링 유지 시에만
- **검증:** 인스턴스 3개에서 연결 100개 생성, 핸드셰이크 오류율 0%
- **비용 영향:** 없음(코드 한 줄)
- **출처:** https://socket.io/docs/v4/using-multiple-nodes/ ("When you configure the Socket.IO client to not use HTTP long-polling ... sticky sessions are no longer required"), https://vercel.com/docs/functions/websockets, https://docs.cloud.google.com/run/docs/configuring/session-affinity (best effort) ⚠️출처부적격

### W-003 배포·축소 시 대량 재연결 (재연결 폭풍)
- **해당:** 장시간 연결(웹소켓, SSE, MQTT)을 가진 모든 서비스
- **무엇/왜:** 롤링 배포, 스케일 인, 노드 교체 때 연결이 한꺼번에 끊기고 클라이언트가 동시에 재접속한다. 재접속마다 인증·구독 복원 쿼리가 실행되어 DB에 순간 폭증을 만든다.
- **실패 양상:** 배포할 때마다 DB CPU 스파이크, 인증 서버 429, 일부 클라이언트는 재접속 루프. 연결이 플랫폼 최대 시간에 닿아도 같은 일이 주기적으로 생긴다.
- **신호:** 🟢 웹소켓 의존성 · 🟡 클라이언트 재연결 코드에 지수 백오프·지터 없음(`setTimeout(connect, 1000)` 고정) · 🔴 서버 SIGTERM 핸들러에서 연결을 즉시 끊음
- **시나리오·수준:** U≥1 (배포가 곧 대량 재연결), T≥2
- **처방:** 코드: 지수 백오프 + 지터, 서버는 SIGTERM 때 "재연결하라" 메시지 후 분산 종료 · 티어 1/2: 종료 유예 시간을 연결 정리 시간보다 길게(W-088), 롤링 maxSurge를 작게 · 티어 2: Karpenter `do-not-disrupt`로 노드 정리 시점 통제(W-087)
- **검증:** P4 U 검증에서 연결 1,000개 유지 중 롤링 배포, DB 커넥션·CPU 스파이크와 재접속 완료 시간 기록
- **비용 영향:** 거의 없음. 대신 DB를 스파이크 기준으로 키우는 과잉을 막는다.
- **출처:** https://render.com/docs/websocket (배포로 인스턴스가 교체되면 연결이 닫힘, 핑과 지수 백오프 재연결 권장), https://vercel.com/docs/functions/websockets (최대 실행 시간에 연결 종료, 재연결·재구독 권장)

### W-004 프레즌스·타이핑 상태의 저장 위치와 만료
- **해당:** 채팅, 협업 도구, 접속자 표시
- **무엇/왜:** "누가 온라인인가"를 프로세스 메모리에 두면 인스턴스마다 다른 답이 나오고, 인스턴스가 죽으면 영원히 온라인으로 남는다. TTL이 있는 공유 저장소가 필요하다.
- **실패 양상:** 접속자 수가 인스턴스 수만큼 부정확, 크래시 후 유령 접속자.
- **신호:** 🟡 `onlineUsers = new Map()`/`set()`이 모듈 최상위에 있음 (`state.inmem_cache` 변형) · 🟡 `presence`, `typing`, `lastSeen` 식별자
- **시나리오·수준:** T≥1 (상태 없음 통제), C0 (프레즌스는 잃어도 되는 데이터라 정합성 수준을 올리지 않음)
- **처방:** 티어 0: Supabase Realtime Presence 또는 Redis · 티어 1/2: Redis 키 TTL(하트비트 주기 × 2~3)
- **검증:** 인스턴스 강제 종료 후 TTL 안에 접속자 목록에서 사라지는지
- **비용 영향:** W-001의 Redis를 공유하면 0
- **출처:** https://vercel.com/docs/functions/websockets ("Store durable state, presence, counters, rooms, and pub/sub coordination in an external data store")

### W-005 SSE·스트리밍 응답과 중간 프록시 버퍼링·유휴 타임아웃
- **해당:** SSE 알림, LLM 토큰 스트리밍, Next.js 스트리밍(Suspense, PPR)
- **무엇/왜:** 스트리밍 응답은 앞단(Nginx, LB)이 버퍼링하면 끝날 때 한꺼번에 도착한다. 또 토큰 사이 공백이 LB 유휴 타임아웃(ALB 기본 60초)보다 길면 연결이 끊긴다.
- **실패 양상:** 로컬에서는 글자가 흘러나오는데 배포하면 한참 뒤 한 번에 표시, 또는 긴 생각 단계에서 502/연결 종료.
- **신호:** 🟢 `text/event-stream`, `ReadableStream`, `streamText`, `StreamingResponse`(FastAPI), `EventSource` · 🟢 Nginx 설정에 `proxy_buffering` 미설정 · 🔴 ECS+ALB인데 `idle_timeout.timeout_seconds` 기본(60) + 하트비트 없음
- **시나리오·수준:** T≥1, 티어별 제외 조건(W-090)
- **처방:** 코드: 15~30초 간격 하트비트 코멘트(`:\n\n`) · 티어 1 ECS: ALB 유휴 타임아웃 상향(1~4000초 범위) · 티어 2: Ingress 버퍼링 끄기, `X-Accel-Buffering: no`
- **검증:** 60초 이상 지연 후 첫 토큰을 내는 테스트 엔드포인트로 연결 유지 확인
- **비용 영향:** 없음
- **출처:** https://nextjs.org/docs/app/guides/self-hosting (nginx는 `X-Accel-Buffering: no`, LB와 프록시가 청크 응답을 버퍼링하지 않아야 함), https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-load-balancer-attributes.html (유휴 타임아웃 기본 60초, 범위 1~4000초) ⚠️출처부적격

### 미디어·업로드

### W-006 업로드가 앱 서버를 통과함 → 서명 URL 직접 업로드
- **해당:** 이미지·동영상·문서 업로드가 있는 모든 앱
- **무엇/왜:** 파일 본문이 앱 함수/컨테이너를 통과하면 플랫폼 본문 한도에 걸리고, 업로드 시간 동안 인스턴스와 커넥션을 점유한다. 클라이언트가 오브젝트 스토리지로 직접 올리고 앱은 서명 URL만 발급하는 구조가 표준이다.
- **실패 양상:** Vercel 4.5MB 초과 시 413 `FUNCTION_PAYLOAD_TOO_LARGE`, Netlify 6MB(바이너리는 base64로 실효 약 4.5MB), Cloud Run HTTP/1 32MiB 초과 시 거절. 업로드 몰리면 웹 인스턴스가 업로드에 묶여 일반 요청 지연.
- **신호:** 🟢 `multer`, `busboy`, `formidable`, `UploadFile`(FastAPI), `request.FILES`(Django) · 🟢 `@aws-sdk/s3-request-presigner`, `generate_presigned_url`, `createSignedUploadUrl`(Supabase) 부재 · 🔴 위 + 티어 0 서버리스 함수
- **시나리오·수준:** TIER-001(본문 한도), D≥1(D-PRE-002 로컬 디스크 업로드와 함께), T≥2
- **처방:** 티어 0: Vercel Blob 클라이언트 업로드, Supabase Storage 서명 업로드 URL · 티어 1: S3/GCS 서명 URL(PUT) · 티어 2: 동일 + 업로드 완료 이벤트로 후처리 큐
- **검증:** 10MB·100MB 파일 업로드 E2E, 업로드 중 앱 인스턴스 CPU·연결 수 변화 없음 확인
- **비용 영향:** 앱 컴퓨트 감소, 스토리지 요청 비용만 발생
- **출처:** https://vercel.com/docs/functions/limitations (4.5MB, 413), https://docs.netlify.com/build/functions/configuration/ (6MB 버퍼 페이로드, base64로 실효 약 4.5MB), https://docs.cloud.google.com/run/quotas (HTTP/1 요청 최대 32MiB), https://docs.aws.amazon.com/AmazonS3/latest/userguide/ShareObjectPreSignedURL.html

### W-007 대용량 업로드 재개: 멀티파트 + 미완료 업로드 정리
- **해당:** 동영상, 원본 사진, 데이터셋, 백업 파일 업로드
- **무엇/왜:** 100MB 이상은 멀티파트 업로드가 AWS 권장이다. 네트워크가 끊겨도 끊긴 파트만 다시 보낸다. 대신 완료·중단되지 않은 멀티파트의 파트는 계속 과금되므로 수명주기 규칙으로 정리해야 한다.
- **실패 양상:** 모바일에서 큰 동영상 업로드가 계속 처음부터 재시작, 버킷에 보이지 않는 미완료 파트가 쌓여 스토리지 비용 증가.
- **신호:** 🟢 `CreateMultipartUpload`, `@aws-sdk/lib-storage`(`Upload`), `tus-js-client`, `@uppy/aws-s3` · 🟡 Terraform `aws_s3_bucket_lifecycle_configuration`에 `abort_incomplete_multipart_upload` 없음 · 🟡 업로드 크기 제한 상수 ≥ 100MB
- **시나리오·수준:** D≥1(업로드 데이터 보존), 비용 필터
- **처방:** 티어 공통: 클라이언트 멀티파트(파트 5MiB 이상, 최대 10,000파트) + `AbortIncompleteMultipartUpload` 7일 규칙 · 티어 0: Supabase Storage/Vercel Blob의 멀티파트 옵션
- **검증:** 업로드 중 네트워크 차단 후 재개해 완료되는지, 수명주기 규칙 존재 확인
- **비용 영향:** 미완료 파트 누적 비용 제거
- **출처:** https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html (100MB 이상 권장, 파트 번호 1~10,000, 완료/중단 전까지 파트 저장 과금, `AbortIncompleteMultipartUpload` 수명주기 권장)

### W-008 이미지 리사이즈·동영상 트랜스코딩을 요청 경로에서 분리
- **해당:** 썸네일 생성, 동영상 HLS 변환, PDF 미리보기
- **무엇/왜:** `sharp`·`ffmpeg`는 CPU·메모리를 크게 쓰고 수 초~수십 분 걸린다. 웹 요청 안에서 돌리면 같은 인스턴스의 다른 요청이 밀리고, 트랜스코딩은 함수 최대 실행 시간을 넘는다.
- **실패 양상:** 업로드 몰릴 때 웹 p95 급등(T L3 실패), 긴 동영상 변환 중 함수 타임아웃(504)으로 반쯤 만들어진 결과물.
- **신호:** 🟢 `sharp`, `jimp`, `Pillow`, `fluent-ffmpeg`, `ffmpeg-static`, `@ffmpeg-installer` (`heavy.image`) · 🔴 위 호출이 HTTP 핸들러 안에 있음 · 🟡 Next.js `next/image` 대량 사용 + Vercel Hobby(이미지 변환 월 5K 포함)
- **시나리오·수준:** T≥3 (T-CTL-008 무거운 작업 격리), TIER-001(실행 시간)
- **처방:** 티어 0: 관리형 이미지 변환(Vercel Image Optimization, Cloudflare Images 등) 또는 외부 동영상 서비스 · 티어 1: 업로드 이벤트 → Cloud Run Jobs(작업 최대 168시간) / ECS 태스크 · 티어 2: 별도 Deployment/Job + 큐 길이 기반 KEDA
- **검증:** 업로드 폭증 중 일반 API p95가 기준(1초) 이내인지
- **비용 영향:** 워커 분리로 웹 인스턴스 과대 산정 방지. 워커는 Spot 대상(COST-004)
- **출처:** https://docs.cloud.google.com/run/quotas (작업 태스크 최대 168시간, GPU 사용 시 1시간), https://vercel.com/docs/limits/fair-use-guidelines (Hobby 이미지 변환 월 5K, Pro $0.05/1K 변환)

### W-009 미디어 전송 비용(egress)과 CDN
- **해당:** 이미지·동영상을 많이 내보내는 서비스
- **무엇/왜:** 미디어 서비스의 지배 비용은 컴퓨트가 아니라 전송량이다. 플랫폼별 포함 전송량과 초과 단가가 크게 다르고, 오브젝트 스토리지에 따라 egress가 0인 곳(Cloudflare R2)도 있다.
- **실패 양상:** 트래픽이 조금 늘었는데 청구서가 컴퓨트의 수 배. Supabase Free 5GB egress·Vercel Hobby 100GB 초과 시 제한.
- **신호:** 🟢 `<video>`, HLS(`.m3u8`), `hls.js`, `video.js` · 🟡 오브젝트 스토리지 URL을 CDN 없이 직접 노출 · 🟡 `Cache-Control` 미설정 정적 미디어 라우트
- **시나리오·수준:** 비용 필터(COST), T≥2(캐시가 원본 부하를 흡수)
- **처방:** 티어 0: 플랫폼 CDN 캐시 헤더, 대용량은 R2처럼 egress 무료 스토리지 검토 · 티어 1/2: CloudFront/Cloud CDN 앞단 + 긴 TTL + 불변 파일명
- **검증:** CDN 캐시 적중률 ≥ 90%, 원본 egress 추이
- **비용 영향:** 전송 비용이 최대 항목이 되는 도메인에서 가장 큰 절감 레버
- **출처:** https://developers.cloudflare.com/r2/pricing/ (R2 egress 무료, 스토리지 $0.015/GB-월), https://supabase.com/pricing (Free 5GB egress, Pro 250GB 포함 후 $0.09/GB), https://vercel.com/docs/limits/fair-use-guidelines (Hobby Fast Data Transfer 100GB)

### W-010 서명 URL의 수명과 캐시 키
- **해당:** 비공개 파일 다운로드(영수증, 의료 기록, 유료 콘텐츠)
- **무엇/왜:** 서명 URL은 만료가 있고(SigV4 CLI·SDK 최대 7일, 콘솔 12시간), 임시 자격 증명으로 서명하면 그 자격 증명이 만료될 때 URL도 무효가 된다. 서명 쿼리가 매번 달라 CDN 캐시 적중이 0이 되기도 한다.
- **실패 양상:** 이메일로 보낸 다운로드 링크가 몇 시간 만에 403, 페이지 HTML을 캐시했더니 만료된 URL을 계속 내보냄, CDN 캐시가 전혀 안 먹음.
- **신호:** 🟢 `getSignedUrl`, `generate_presigned_url`, `createSignedUrl` · 🟡 `expiresIn` 값이 매우 김(>1일) 또는 서명 URL을 DB에 저장
- **시나리오·수준:** C1(링크 유효성), 보안 영역과 교차
- **처방:** 공통: URL은 요청 시점에 짧게(분 단위) 발급, DB에는 오브젝트 키만 저장 · 티어 1/2: CDN 서명 쿠키/URL로 캐시와 접근 제어 분리
- **검증:** 저장된 링크 재사용 테스트, 만료 후 403 확인
- **비용 영향:** 캐시 적중률 개선 시 egress 절감
- **출처:** https://docs.aws.amazon.com/AmazonS3/latest/userguide/ShareObjectPreSignedURL.html (콘솔 최대 12시간, CLI 최대 7일, URL은 생성자의 자격 증명을 사용)

### AI·LLM 앱

### W-011 LLM 스트리밍·긴 생성과 플랫폼 요청 타임아웃
- **해당:** 챗봇, 에이전트, 문서 요약, 코드 생성
- **무엇/왜:** 추론 모델·에이전트 루프·도구 호출이 겹치면 응답이 수 분 걸린다. 스트리밍이어도 플랫폼의 최대 실행 시간이 응답 전체에 적용된다(Vercel은 스트리밍 응답 포함이라고 명시).
- **실패 양상:** 긴 답변 중간에 끊김(Vercel 504 `FUNCTION_INVOCATION_TIMEOUT`, ACA 240초, Netlify 스트리밍 60초, Supabase Edge Function Free 150초 벽시계). 사용자는 "답이 잘렸다"고 느끼고 재시도 → 토큰 비용 2배.
- **신호:** 🟢 `openai`, `@anthropic-ai/sdk`, `ai`(Vercel AI SDK), `langchain`, `llamaindex` (`heavy.llm_call`) · 🟢 `maxDuration`, `export const runtime = 'edge'` · 🟡 에이전트 루프(`while`/`for` + tool call) · 🔴 에이전트 루프 + Hobby/Netlify/ACA
- **시나리오·수준:** TIER-001/TIER-002 확장: "예상 최대 처리 시간 > 플랫폼 상한"이면 제외
- **처방:** 티어 0: Vercel Pro `maxDuration` 800초(1800초 베타), 그 이상은 비동기화(W-013) · 티어 1: Cloud Run 타임아웃 최대 3600초로 설정 + 재연결 허용 · 티어 2: Ingress/LB 타임아웃 상향
- **검증:** 가장 긴 프롬프트·도구 체인으로 p99 처리 시간 측정 후 상한과 비교
- **비용 영향:** 잘림→재시도로 인한 토큰 이중 지출 방지
- **출처:** https://vercel.com/docs/functions/limitations (Hobby 300초, Pro/Ent 800초, 1800초 베타, 스트리밍 응답 포함, Edge 런타임은 25초 안에 응답 시작·300초까지 스트리밍), https://learn.microsoft.com/en-us/azure/container-apps/ingress-overview (요청 타임아웃 240초), https://docs.netlify.com/build/functions/api/ (스트리밍 60초·20MB), https://supabase.com/docs/guides/functions/limits (Free 150초, 유료 400초)

### W-012 LLM 프로바이더 레이트 리밋·지출 한도
- **해당:** 외부 LLM API를 호출하는 모든 앱
- **무엇/왜:** 프로바이더는 조직 단위로 분당 요청·입력 토큰·출력 토큰 한도(RPM/ITPM/OTPM, OpenAI는 RPM/TPM/RPD/TPD)와 월 지출 상한을 둔다. 우리 앱의 오토스케일은 이 한도를 늘리지 못한다. 트래픽 폭증 = 429 폭증이다.
- **실패 양상:** T L2/L3 이벤트에서 인스턴스는 늘었는데 LLM 응답은 429. Anthropic 월 지출 상한 도달 시 다음 달 1일까지 429가 `retry-after` 없이 계속(재시도로는 회복 안 됨). 새 조직은 Evaluation 등급으로 더 낮은 한도에서 시작.
- **신호:** 🟢 LLM SDK 의존성 · 🟡 SDK `maxRetries` 기본값만 사용, 429 처리 없음 · 🔴 사용자별 호출 한도 없음 + 공개 가입
- **시나리오·수준:** T≥2이면 외부 API 한도를 용량 계획에 포함 (새 축 후보 참조), COST-008
- **처방:** 공통: 사용자·테넌트별 한도, 요청 큐 + 동시 호출 상한, `retry-after` 존중 백오프, 프롬프트 캐싱(Anthropic은 대부분 모델에서 캐시 읽기 토큰이 ITPM에 미포함), 비실시간 작업은 Batch API · 티어 1/2: 큐 워커로 LLM 호출 격리
- **검증:** 피크 가정 × 평균 토큰으로 필요 ITPM/OTPM 계산 → 현재 등급 한도와 비교, 429 주입 시 디그레이드 동작 확인
- **비용 영향:** 한도 초과로 인한 장애 대신 대기열 지연으로 전환. 캐싱은 비용도 절감
- **출처:** https://platform.claude.com/docs/en/api/rate-limits (RPM/ITPM/OTPM, 토큰 버킷, 429 + `retry-after`, 월 지출 상한 Start $500·Build $1,000·Scale $200,000, 상한 도달 시 `retry-after` 없는 429), https://developers.openai.com/api/docs/guides/rate-limits (RPM/RPD/TPM/TPD/IPM, 지수 백오프 + 지터, Batch API) ⚠️출처부적격

### W-013 긴 AI 작업의 비동기화 (작업 ID + 폴링/웹훅)
- **해당:** 문서 일괄 임베딩, 긴 에이전트 작업, 영상·음성 생성, 리포트 생성
- **무엇/왜:** 사용자 요청 안에서 끝낼 수 없는 작업은 "접수 → 작업 ID 반환 → 워커 처리 → 상태 조회/알림"으로 바꿔야 한다. 플랫폼 한도와 무관하게 동작하고, 재시도·멱등성을 설계할 자리가 생긴다.
- **실패 양상:** 요청 타임아웃, 브라우저 닫으면 작업 유실, 재시도 시 중복 생성.
- **신호:** 🟡 임베딩 루프(`embeddings.create` in loop), `for doc in documents` + LLM 호출 · 🟢 `bullmq`, `celery`, `rq`, `inngest`, `trigger.dev`, `@vercel/workflow` 존재 여부(있으면 충족 후보)
- **시나리오·수준:** C≥2 (작업 큐 → 멱등 소비 C-CTL-004), TIER-001
- **처방:** 티어 0: Vercel Workflows(실행 시간 제한 없이 일시정지·재개), Supabase는 pg 큐 + 크론 · 티어 1: Cloud Tasks/Pub/Sub → Cloud Run, SQS → ECS 워커, 장시간은 Cloud Run Jobs · 티어 2: 큐 + KEDA
- **검증:** 작업 중 워커 강제 종료 → 재처리되고 결과 중복 없음
- **비용 영향:** 큐·워커 고정비 소폭. 재시도 낭비 감소
- **출처:** https://vercel.com/docs/functions/limitations (무제한 실행이 필요하면 Vercel Workflows 안내), https://docs.cloud.google.com/run/quotas (작업 최대 168시간)

### W-014 GPU 필요 여부와 리전
- **해당:** 자체 모델 추론(Whisper, 임베딩, Stable Diffusion, 로컬 LLM)
- **무엇/왜:** 외부 API를 쓰면 GPU가 필요 없다. 자체 추론일 때만 GPU 티어가 필요하고, GPU는 리전이 제한적이며 과금 방식이 다르다(Cloud Run GPU는 인스턴스 기반 과금 필수).
- **실패 양상:** 기본 리전(서울)에 GPU가 없어 배포 실패 또는 멀리 떨어진 리전에 배치되어 지연·전송비 증가. 최소 인스턴스 1로 두면 GPU 유휴 비용이 월 수백 달러.
- **신호:** 🟢 `torch`, `transformers`, `diffusers`, `vllm`, `onnxruntime-gpu`, `faster-whisper` · 🟢 Dockerfile `nvidia/cuda` 베이스 · 🟡 `.to("cuda")`
- **시나리오·수준:** 티어 제외 조건: GPU 필요 → Vercel/Netlify/Workers/Supabase 함수 제외. Cloud Run GPU는 리전 확인 필수
- **처방:** 티어 0: 외부 추론 API로 대체 권고 · 티어 1: Cloud Run GPU(L4, RTX PRO 6000) 0으로 축소 허용 · 티어 2: GPU 노드 풀 + 0 스케일(Karpenter/EKS Auto Mode GPU 지원)
- **검증:** 콜드 스타트(모델 로드 포함) 시간 측정, 유휴 시 0 인스턴스 확인
- **비용 영향:** GPU 최소 인스턴스는 가장 큰 단일 비용 항목이 될 수 있음
- **출처:** https://docs.cloud.google.com/run/docs/configuring/services/gpu (L4·RTX PRO 6000, 제공 리전 목록에 서울 없음: L4는 싱가포르·뭄바이(초대)·벨기에·네덜란드·아이오와·북버지니아, 인스턴스 기반 과금 필수, 드라이버 포함 약 5초 기동), https://docs.aws.amazon.com/eks/latest/userguide/automode.html (Auto Mode GPU 지원)

### W-015 벡터 검색: 별도 벡터 DB 대신 pgvector 우선
- **해당:** RAG, 의미 검색, 추천
- **무엇/왜:** 이미 Postgres가 있으면 pgvector로 충분한 경우가 많다. 별도 벡터 DB는 동기화·비용·운영 대상이 하나 늘어난다. 다만 HNSW 인덱스 빌드는 메모리를 많이 쓰고, 인덱싱 가능한 차원 수에 한계(vector 2,000, halfvec 4,000)가 있다.
- **실패 양상:** 소규모 앱에 관리형 벡터 DB 추가로 고정비 과잉, 또는 pgvector HNSW 빌드가 `maintenance_work_mem`을 넘어 매우 느려지고 작은 DB 인스턴스가 메모리 압박.
- **신호:** 🟢 `pgvector`, `vector(` 컬럼, `@pinecone-database/pinecone`, `weaviate`, `qdrant-client`, `chromadb` · 🟡 임베딩 차원 상수(1536, 3072 등)
- **시나리오·수준:** 비용 필터(과잉 탐지), D≥1(임베딩은 재생성 가능 → 원본 문서만 백업 대상)
- **처방:** 티어 0: Supabase pgvector · 티어 1/2: RDS/Cloud SQL pgvector, 3072차원은 halfvec 또는 차원 축소
- **검증:** 인덱스 빌드 시간·메모리, recall@k
- **비용 영향:** 별도 벡터 DB 제거 시 고정비 절감
- **출처:** https://github.com/pgvector/pgvector (HNSW는 속도-재현율이 더 좋고 빌드 메모리 많음, IVFFlat은 빌드 빠름, `maintenance_work_mem`, vector 2,000차원·halfvec 4,000차원 인덱싱) ⚠️출처부적격

### W-016 토큰 비용이 트래픽에 비례 (요청당 유료 외부 API)
- **해당:** LLM, 음성 인식, 번역, 지도 지오코딩 등 호출 건당 과금 API
- **무엇/왜:** 인프라 비용은 오토스케일 상한으로 묶이지만, 외부 API 비용은 상한이 없다. 공개 가입 + 로그인 없는 LLM 엔드포인트는 남용 시 비용 폭주.
- **실패 양상:** 봇이 무료 챗봇을 두드려 하루에 월 예산 소진, 또는 프로바이더 지출 상한 도달로 서비스 정지(W-012).
- **신호:** 🟢 LLM SDK + 🔴 인증 미들웨어 없는 라우트에서 호출 · 🟡 사용자별 사용량 테이블(`usage`, `credits`) 부재
- **시나리오·수준:** COST-008(원칙 5), T≥3이면 레이트 리밋(T-CTL-007)과 결합. 크레딧 차감이 있으면 C3(잔액 차감 패턴)
- **처방:** 공통: 인증 필수, 사용자·IP 한도, 일일 예산 차단기, 프롬프트 캐싱 · 크레딧 모델이면 잔액 차감 잠금(C-CTL-005)
- **검증:** 한도 초과 요청이 429로 막히는지, 예산 차단기 동작
- **비용 영향:** 상한 없는 변동비를 상한 있는 비용으로 전환
- **출처:** 설계 원칙 5(§2), https://platform.claude.com/docs/en/api/rate-limits (사용자 정의 지출 한도·워크스페이스 한도, 캐시 읽기 토큰의 ITPM 제외) ⚠️출처부적격

### 백그라운드·배치·크론

### W-017 응답 후 백그라운드 작업 (fire-and-forget)
- **해당:** 응답을 보낸 뒤 이메일 발송, 로그·분석 전송, 캐시 갱신
- **무엇/왜:** 서버리스·요청 기반 과금 플랫폼에서는 응답이 끝나면 CPU가 거의 회수되거나 실행이 끊긴다. `promise`를 await 하지 않고 던지는 코드는 로컬에서는 되지만 배포하면 조용히 유실된다.
- **실패 양상:** 가입 확인 메일이 가끔 안 감, 분석 이벤트 누락. Cloud Run 요청 기반 과금에서는 응답 후 CPU 제한, Vercel `waitUntil`도 함수 최대 실행 시간 안에서만 실행.
- **신호:** 🟡 HTTP 핸들러 안에서 await 없는 async 호출(`sendEmail(...)` 후 `return res`) · 🟢 `waitUntil`, `after()`(Next.js), `BackgroundTasks`(FastAPI), `setImmediate`/`process.nextTick` · 🔴 위 + Cloud Run 요청 기반 과금
- **시나리오·수준:** C≥1(유실), 티어 1 Cloud Run이면 "인스턴스 기반 과금 필요" 조건
- **처방:** 티어 0: Next.js `after()`/`waitUntil`(짧은 작업만) · 티어 1: Cloud Run 인스턴스 기반 과금 또는 Cloud Tasks로 분리, ECS는 상시 실행이라 영향 적음 · 티어 2: 큐 + 워커. 중요 작업은 모두 큐로(W-013)
- **검증:** 응답 직후 인스턴스 축소를 유발하고 후속 작업 완료율 측정
- **비용 영향:** 인스턴스 기반 과금 전환 시 유휴 비용 증가 → 큐 분리가 보통 더 쌈
- **출처:** https://docs.cloud.google.com/run/docs/configuring/billing-settings (요청 기반 과금은 요청 처리 중에만 CPU 할당, 백그라운드 작업에는 인스턴스 기반 과금 권장, 인스턴스 기반은 최소 512MiB), https://vercel.com/docs/functions/functions-api-reference/vercel-functions-package (`waitUntil` 프로미스는 함수와 같은 타임아웃, 타임아웃 시 취소), https://nextjs.org/docs/app/guides/self-hosting (`after`는 SIGTERM 시 마무리, 10~30초 드레인 권장)

### W-018 크론의 중복 실행과 실행 시각 정밀도
- **해당:** 정산, 리마인더 발송, 만료 처리, 랭킹 집계
- **무엇/왜:** 앱 프로세스 안의 크론(`node-cron`, APScheduler)은 인스턴스 수만큼 실행된다. 관리형 스케줄러도 "최소 1회" 전달이라 드물게 두 번 실행된다. 일부 무료 플랜은 실행 빈도·정밀도가 낮다.
- **실패 양상:** 인스턴스 3대 → 리마인더 메일 3통, 정산 3번. Vercel Hobby는 하루 1회만 허용되고 지정 시각 ±59분에 실행, 더 잦은 표현식은 배포 실패.
- **신호:** 🟢 `node-cron`, `cron`, `agenda`, `APScheduler`, `celery beat`, `@nestjs/schedule` (`process.cron`, `cron.no_lock`) · 🟢 `vercel.json`의 `crons` 표현식 · 🔴 프로세스 내 크론 + 인스턴스 >1
- **시나리오·수준:** T-PRE-002, C≥2(멱등)
- **처방:** 티어 0: Vercel Cron(Hobby는 일 1회 제약 확인), Supabase pg_cron · 티어 1: Cloud Scheduler → Cloud Run Jobs / EventBridge Scheduler → ECS 태스크 · 티어 2: CronJob(`concurrencyPolicy: Forbid`) · 공통: 실행 키(예: `X-CloudScheduler-ScheduleTime` + 작업명)로 중복 제거
- **검증:** 같은 스케줄 실행 이벤트를 두 번 주입해 부수효과 1회 확인
- **비용 영향:** 없음
- **출처:** https://vercel.com/docs/cron-jobs/usage-and-pricing (Hobby 일 1회, ±59분, Pro 분 단위), https://docs.cloud.google.com/scheduler/docs/overview ("at least once", 드물게 여러 번 실행, `X-CloudScheduler-ScheduleTime`으로 중복 제거)

### W-019 DB 테이블 기반 작업 큐: `SKIP LOCKED`
- **해당:** Redis 없이 Postgres로 작업 큐를 구현한 앱(graphile-worker, pg-boss, Django-Q ORM 브로커, 직접 구현)
- **무엇/왜:** 소규모에서는 Postgres 큐가 가장 싼 선택이다. 단 여러 워커가 같은 행을 집지 않도록 `FOR UPDATE SKIP LOCKED`가 필요하다. 없으면 중복 처리 또는 잠금 경합.
- **실패 양상:** 워커 2대가 같은 작업을 처리(중복 메일·중복 결제 요청), 또는 `FOR UPDATE`만 써서 워커들이 줄 서서 대기.
- **신호:** 🟢 `pg-boss`, `graphile-worker`, `procrastinate` · 🟡 `jobs`/`tasks` 테이블 + `status = 'pending'` 조회 후 업데이트 · 🔴 `SELECT ... WHERE status='pending' LIMIT` 후 별도 `UPDATE`(잠금 없음)
- **시나리오·수준:** C≥2(C-CTL-004), 비용 필터(Redis·SQS 추가를 피하는 근거)
- **처방:** 공통: `SELECT ... FOR UPDATE SKIP LOCKED` + 처리 멱등. 처리량이 커지면 티어 1 SQS/Pub/Sub, 티어 2 Redis Streams + KEDA
- **검증:** 워커 4개 동시 실행, 작업 1,000건 중복 처리 0건
- **비용 영향:** 별도 큐 서비스 없이 시작 가능(절감)
- **출처:** https://www.postgresql.org/docs/current/sql-select.html ("SKIP LOCKED ... can be used to avoid lock contention with multiple consumers accessing a queue-like table")

### W-020 긴 배치·워커의 종료 유예와 체크포인트
- **해당:** 수십 분 이상 걸리는 배치, 큐 워커, 데이터 마이그레이션 작업
- **무엇/왜:** 배포·축소·Spot 회수·노드 교체 때 SIGTERM 후 유예 시간 안에 끝내지 못하면 강제 종료된다. 플랫폼마다 유예 시간이 짧고(Cloud Run 10초, ECS 기본 30초·최대 120초), k8s 노드 정리 도구는 장기 실행 Pod를 옮길 수 있다.
- **실패 양상:** 50분짜리 작업이 49분에 죽고 처음부터 다시 → 영원히 끝나지 않음, 반쯤 쓴 결과.
- **신호:** 🟡 루프 처리 코드에 진행 상태 저장(오프셋, 커서) 없음 · 🟢 `stopTimeout`, `terminationGracePeriodSeconds` 값 · 🟢 Karpenter `NodePool`의 `consolidationPolicy`, Pod `karpenter.sh/do-not-disrupt` 부재
- **시나리오·수준:** U≥1(U-CTL-002), COST-004(Spot 전제 조건)
- **처방:** 코드: 청크 단위 처리 + 체크포인트 + 멱등 재개 · 티어 1: 장시간 작업은 Cloud Run Jobs/ECS RunTask(서비스와 분리) · 티어 2: Job + `do-not-disrupt` 어노테이션 + `terminationGracePeriodSeconds`
- **검증:** 작업 중간에 SIGTERM 주입, 재개 후 결과 일치
- **비용 영향:** 체크포인트가 있어야 Spot(최대 70% 할인) 사용 가능
- **출처:** https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definition_parameters.html (`stopTimeout` 기본 30초, 최대 120초), https://karpenter.sh/docs/concepts/disruption/ (`do-not-disrupt`, 만료·중단은 이 어노테이션을 무시, 기본 `expireAfter` 720h), 설계 S3(Cloud Run 10초)

### 메시지 발송 (이메일·푸시·SMS)

### W-021 이메일 발송 평판: 인증·구독 해지·스팸률
- **해당:** 가입 인증, 비밀번호 재설정, 뉴스레터, 마케팅 메일
- **무엇/왜:** Gmail은 하루 5,000통 이상 보내는 발신자에게 SPF·DKIM·DMARC, From 도메인 정렬, 원클릭 구독 해지, 스팸 신고율 0.3% 미만을 요구한다. 트랜잭션 메일과 마케팅 메일을 같은 도메인·IP로 보내면 마케팅 평판이 비밀번호 재설정 메일까지 스팸함으로 보낸다.
- **실패 양상:** 인프라는 멀쩡한데 "인증 메일이 안 와요" 문의 폭증. 재난·예약 확인처럼 메일이 핵심 경로인 도메인에서는 사실상 장애.
- **신호:** 🟢 `nodemailer`, `@sendgrid/mail`, `resend`, `postmark`, `@aws-sdk/client-sesv2`, `django.core.mail` · 🟡 SMTP를 앱에서 직접(`smtp.gmail.com`) · 🟡 `List-Unsubscribe` 헤더 부재(마케팅 메일)
- **시나리오·수준:** D≥3 도메인이면 발송 경로도 의존성(D-CTL-005), 보안·운영 교차
- **처방:** 공통: 전문 발송 서비스(HTTP API) + 도메인 인증 3종 + 트랜잭션/마케팅 서브도메인 분리 · 대량 발송은 큐(W-013)
- **검증:** DNS에서 SPF/DKIM/DMARC 레코드 확인, 테스트 메일 헤더의 인증 결과
- **비용 영향:** 발송 서비스 건당 과금. 평판 손상의 복구 비용이 훨씬 큼
- **출처:** https://support.google.com/a/answer/81126 (일 5,000통 이상 대량 발신자 요건: SPF·DKIM·DMARC, 원클릭 구독 해지, 스팸률 0.30% 미만, 2024-02-01 시행) ⚠️출처부적격

### W-022 발송 서비스의 초기 제한 (SES 샌드박스 등)
- **해당:** Amazon SES를 새로 쓰는 앱
- **무엇/왜:** 새 SES 계정은 리전마다 샌드박스 상태다. 검증된 주소로만, 24시간 200통, 초당 1통만 보낼 수 있다. 프로덕션 접근 요청 검토에 최대 24시간 이상 걸린다.
- **실패 양상:** 배포 직후 실제 사용자에게 메일이 전혀 안 감. 리전을 바꿔 배포하면 다시 샌드박스.
- **신호:** 🟢 `@aws-sdk/client-ses(v2)`, `boto3.client('ses')` · 🟡 Terraform에 SES 아이덴티티만 있고 프로덕션 접근 근거 없음
- **시나리오·수준:** P3 배포 체크리스트(배포 전 사전 작업), 티어 1/2 AWS 경로
- **처방:** 배포 전 프로덕션 접근 요청 단계를 P3 실행기 사전 조건에 넣음. 대안: 이미 쓰는 외부 발송 서비스 유지
- **검증:** `aws sesv2 get-account`의 `ProductionAccessEnabled`
- **비용 영향:** 없음(시간 지연)
- **출처:** https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html (샌드박스: 검증 주소만, 24시간 200통, 초당 1통, 리전별, 검토 24시간 내 1차 응답)

### W-023 푸시 대량 발송: 프로젝트·기기별 쿼터
- **해당:** 모바일 앱 백엔드, 재난 알림, 이벤트 알림
- **무엇/왜:** FCM은 프로젝트당 분당 60만 건 기본 쿼터, 안드로이드 단일 기기에 분당 240건·시간당 5,000건, collapsible 메시지는 기기당 버스트 20건 후 3분마다 1건 보충. 초과 시 429. 대량 발송은 앱 서버에서 루프로 보내지 말고 큐로 속도를 조절하거나 토픽을 써야 한다.
- **실패 양상:** 100만 명에게 한 번에 보내다 429 → 재시도 폭주 → 일부만 수신. 재난 알림에서 치명적.
- **신호:** 🟢 `firebase-admin`(`messaging().send`, `sendEach`), `apns2`, `expo-server-sdk`, `web-push` · 🔴 사용자 목록 전체 루프 안에서 `send` 호출
- **시나리오·수준:** T≥3 도메인(재난)에서는 발송 처리량이 T 용량 계획의 일부. C≥2(중복 발송 방지 멱등 키)
- **처방:** 공통: 발송 큐 + 속도 제한 워커 + 429 백오프, 전체 공지는 토픽 메시지 · 티어 1/2: 큐 길이 기반 워커 확장
- **검증:** 가정한 수신자 수 / 쿼터로 발송 완료 시간 계산, 스테이징에서 429 주입
- **비용 영향:** FCM 자체는 무료. 워커 비용 소폭
- **출처:** https://firebase.google.com/docs/cloud-messaging/throttling-and-quotas (분당 60만 건, 기기당 분당 240·시간당 5,000, collapsible 버스트 20·3분당 1, 429)

### W-024 SMS·인증번호 발송: 건당 비용과 남용
- **해당:** 휴대폰 인증, 2FA, 알림톡/SMS 알림
- **무엇/왜:** SMS는 건당 과금이고 국가별 단가 차이가 크다. 공개된 "인증번호 보내기" 엔드포인트는 봇이 고단가 국가 번호로 대량 요청하는 남용(SMS 펌핑) 대상이 된다. 국가별 발신번호 등록 규제가 있다.
- **실패 양상:** 하룻밤에 SMS 비용 수천 달러, 발신번호 미등록으로 국내 발송 차단.
- **신호:** 🟢 `twilio`, `@vonage/server-sdk`, `aws-sdk` SNS `publish`(PhoneNumber), 국내 SMS·알림톡 SDK(`solapi` 등) · 🔴 인증 없는 `/send-otp`, `/verify/phone` 라우트 + 레이트 리밋 없음
- **시나리오·수준:** T≥1이라도 레이트 리밋 필수(T-CTL-007을 이 경로에는 수준 무관하게 적용 제안), 비용 필터
- **처방:** 공통: 번호·IP·기기별 한도, 허용 국가 목록, CAPTCHA, 일일 예산 차단기
- **검증:** 같은 번호·IP로 반복 요청 시 차단
- **비용 영향:** 남용 차단이 곧 비용 상한
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### 검색·분석·리포트

### W-025 전문 검색: 엔진 추가 전 Postgres FTS, 추가 시 동기화 경로
- **해당:** 상품 검색, 게시글 검색, 문서 검색
- **무엇/왜:** 별도 검색 엔진(Elasticsearch/OpenSearch, Meilisearch, Algolia)은 DB와의 동기화 문제를 만든다. "DB 쓰기 후 검색 엔진 쓰기"를 같은 요청에서 하면 한쪽만 성공하는 이중 쓰기 불일치가 생긴다. 규모가 작으면 Postgres 전문 검색(tsvector + GIN)으로 충분하다. 단 Postgres 기본 설정에 한국어 형태소 분석 설정이 없어 한국어는 별도 확장·엔진 검토가 필요하다(이 부분은 우리 추론). ⚠️근거없음
- **실패 양상:** 삭제한 상품이 검색에 계속 노출, 검색 엔진 장애 시 글쓰기까지 실패, 작은 앱에 검색 클러스터 고정비.
- **신호:** 🟢 `@elastic/elasticsearch`, `@opensearch-project/opensearch`, `meilisearch`, `algoliasearch`, `typesense` · 🟢 `tsvector`, `to_tsquery`, `SearchVectorField`(Django) · 🔴 같은 핸들러에서 DB 커밋 후 검색 인덱스 쓰기(트랜잭션 밖)
- **시나리오·수준:** C≥2(아웃박스/CDC로 동기화), D(검색 인덱스는 재생성 가능 → 백업 대상 아님, 재색인 시간이 RTO에 포함), 비용 필터
- **처방:** 티어 0: Postgres FTS 또는 Algolia 같은 SaaS · 티어 1/2: 아웃박스 테이블 → 워커 → 검색 엔진, 엔진 장애 시 DB LIKE 검색으로 디그레이드
- **검증:** 검색 엔진 차단 중 쓰기 성공, 복구 후 인덱스 따라잡기
- **비용 영향:** 검색 클러스터는 최소 수십~수백 달러/월 고정비 → 과잉 탐지 대상
- **출처:** https://www.postgresql.org/docs/current/textsearch-intro.html (tsvector·tsquery·GIN, 언어별 사전 구성)

### W-026 분석·이벤트 수집: 쓰기 폭증과 저장소 분리
- **해당:** 클릭 추적, 자체 분석, 로그성 이벤트, A/B 테스트 이벤트
- **무엇/왜:** 이벤트는 사용자 행동 하나당 여러 건이라 트랜잭션 테이블보다 쓰기량이 한두 자릿수 크다. 운영 OLTP DB에 행 단위로 넣으면 커넥션과 WAL을 잡아먹어 핵심 쓰기를 느리게 한다. 이벤트는 C0(잃어도 됨)이므로 버퍼·배치 삽입이 허용된다.
- **실패 양상:** 트래픽 폭증 시 결제 같은 핵심 쓰기가 이벤트 INSERT와 경쟁해 느려짐, DB 디스크 급증.
- **신호:** 🟡 `events`/`page_views`/`analytics` 테이블 + 요청마다 INSERT · 🟢 `posthog-node`, `@segment/analytics-node`, `clickhouse`, `@clickhouse/client`, `timescaledb`
- **시나리오·수준:** C 판정에서 이 경로는 C0로 분리(§4.2 C L0 조건의 부분 적용), T≥2이면 핵심 DB에서 분리
- **처방:** 티어 0: 외부 분석 SaaS · 티어 1/2: 큐/버퍼 → 배치 삽입, 대량이면 컬럼형 저장소(BigQuery, ClickHouse) · 공통: 이벤트 쓰기 실패가 요청 실패로 번지지 않게
- **검증:** 피크 부하에서 핵심 쓰기 p95와 이벤트 경로 분리 전후 비교
- **비용 영향:** OLTP DB 증설 회피
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### W-027 파일·리포트 생성 (PDF·엑셀·헤드리스 브라우저)
- **해당:** 영수증·인보이스 PDF, 엑셀 내보내기, 스크린샷, 대량 CSV
- **무엇/왜:** 헤드리스 Chromium(Puppeteer/Playwright)은 수백 MB 바이너리와 1GB 이상 메모리를 쓴다. 대량 내보내기는 메모리에 모두 올리면 OOM. 함수 번들 크기(Vercel 250MB 기본)와 메모리(Hobby 2GB) 한도를 넘기 쉽다.
- **실패 양상:** 배포 시 번들 크기 초과 실패, 큰 리포트 요청 때 OOM으로 인스턴스 재시작(같은 인스턴스의 다른 요청도 실패).
- **신호:** 🟢 `puppeteer`, `playwright`, `@sparticuz/chromium`, `pdfkit`, `exceljs`, `reportlab`, `weasyprint`, `openpyxl` · 🔴 전체 결과를 메모리 배열로 모은 뒤 파일 생성(스트리밍 아님)
- **시나리오·수준:** T≥3(T-CTL-008 격리), TIER-001(번들·메모리·시간)
- **처방:** 티어 0: 작은 PDF는 라이브러리 방식, 브라우저 렌더링은 외부 서비스 · 티어 1/2: 별도 워커 + 결과를 스토리지에 저장 + 다운로드 링크(W-010)
- **검증:** 최대 크기 리포트 생성 시 메모리 최고치 측정
- **비용 영향:** 무거운 작업만 큰 메모리 워커로 → 웹 인스턴스 과대 산정 방지
- **출처:** https://vercel.com/docs/functions/limitations (번들 250MB, Python 500MB, 대형 함수 5GB 베타, 메모리 Hobby 2GB·Pro 4GB)

### 멀티테넌트 SaaS·공개 API·웹훅 발송

### W-028 테넌트 격리: 인증과 별개의 통제
- **해당:** B2B SaaS, 조직·워크스페이스 모델
- **무엇/왜:** 인증·인가가 있어도 쿼리에 `tenant_id` 조건이 하나 빠지면 다른 회사 데이터가 보인다. 격리는 인증과 별도 통제다. 공유 DB(풀 모델)면 Postgres RLS가 마지막 방어선이 되지만, 테이블 소유자·슈퍼유저는 기본적으로 RLS를 우회한다. 앱이 소유자 역할로 접속하면 RLS가 있어도 무효다.
- **실패 양상:** 고객 A가 고객 B의 청구서를 봄 → B2B에서는 계약 해지·법적 문제. D/T 장애보다 치명적.
- **신호:** 🟢 스키마에 `tenant_id`/`organization_id`/`workspace_id` · 🟢 `ENABLE ROW LEVEL SECURITY`, `CREATE POLICY` · 🔴 RLS는 있는데 `FORCE ROW LEVEL SECURITY` 없음 + 앱이 테이블 소유자 계정으로 접속 · 🟡 Supabase `service_role` 키를 클라이언트·공용 경로에서 사용
- **시나리오·수준:** C≥2 (새 하위 통제 후보: 테넌트 격리), D2(B2B 계약 신호 → §4.2 D L2)
- **처방:** 공통: 모든 쿼리 경로에 테넌트 컨텍스트 강제(ORM 미들웨어) + RLS + 앱 전용 비소유자 역할 · 고급: 큰 고객은 사일로(전용 DB/스키마)
- **검증:** 테넌트 A 토큰으로 B 리소스 ID 직접 요청하는 교차 테넌트 테스트(P4 C 검증 추가 후보)
- **비용 영향:** 풀 모델 유지 시 0, 사일로는 테넌트 수 비례
- **출처:** https://docs.aws.amazon.com/whitepapers/latest/saas-architecture-fundamentals/tenant-isolation.html ("authenticated does not mean that your system has achieved isolation"), https://www.postgresql.org/docs/current/ddl-rowsecurity.html (슈퍼유저·`BYPASSRLS`·테이블 소유자 우회, `FORCE ROW LEVEL SECURITY`)

### W-029 시끄러운 이웃과 테넌트별 한도
- **해당:** 멀티테넌트 SaaS, 공개 API, 공유 워커 큐
- **무엇/왜:** 한 테넌트의 대량 가져오기·리포트·API 폭주가 공유 DB·큐·외부 API 한도(W-012)를 독점하면 모든 테넌트가 느려진다. 사용자 단위 레이트 리밋만으로는 부족하고 테넌트 단위 한도와 공정 큐가 필요하다.
- **실패 양상:** 큰 고객이 CSV 100만 행을 올린 순간 다른 고객 화면이 멈춤, 큐 지연 수 시간.
- **신호:** 🟡 `import`/`bulk`/`export` 라우트 + 테넌트 모델 · 🟡 큐 작업에 테넌트 키 없음 · 🟢 `plan`/`tier` 컬럼(요금제별 한도의 근거)
- **시나리오·수준:** T≥2(B2B 이벤트성 부하), T-CTL-007 확장(테넌트 기준)
- **처방:** 공통: 테넌트별 레이트 리밋(429 + `Retry-After`), 무거운 작업은 테넌트별 동시 실행 상한, 요금제별 쿼터 · 티어 2: 큰 테넌트 전용 워커 풀
- **검증:** 한 테넌트 폭주 중 다른 테넌트 p95 유지
- **비용 영향:** 전체 증설 대신 격리로 해결 → 절감
- **출처:** https://www.rfc-editor.org/rfc/rfc6585#section-4 (429 Too Many Requests, Retry-After), https://platform.claude.com/docs/en/api/rate-limits (워크스페이스별 한도로 다른 워크스페이스 보호하는 예시: 같은 패턴의 공식 사례)

### W-030 모바일 백엔드: 구버전 앱 호환
- **해당:** iOS/Android 앱의 API 서버
- **무엇/왜:** 웹은 배포하면 모든 사용자가 새 코드를 받지만, 모바일은 구버전 앱이 수개월~수년 남는다. API·스키마 변경의 expand/contract 기간이 웹보다 훨씬 길어야 하고, 최소 지원 버전·강제 업데이트 장치가 필요하다.
- **실패 양상:** 필드 이름 변경 배포 직후 구버전 앱 크래시, 앱스토어 심사 기간 동안 핫픽스 불가.
- **신호:** 🟢 `X-App-Version`/`app_version` 헤더 처리, `/v1/`·`/v2/` 경로 · 🟡 저장소에 `ios/`, `android/`, `react-native`, `expo`, `flutter` 동시 존재 · 🟡 `min_supported_version` 설정 부재
- **시나리오·수준:** U≥2(U-CTL-003의 contract 단계 지연: 구버전 점유율 기준), 새 축 후보(클라이언트 배포 통제 불가)
- **처방:** 공통: API 버전 + 최소 버전 응답(강제 업데이트), 필드 삭제는 구버전 사용률 임계치 이하에서만
- **검증:** 이전 릴리스 앱 빌드로 신규 API 계약 테스트
- **비용 영향:** 구버전 엔드포인트 유지 비용 소폭
- **출처:** 일반 원칙(출처 미확인). expand/contract 자체는 설계 S9(https://martinfowler.com/bliki/ParallelChange.html) ⚠️출처부적격 ⚠️근거없음

### W-031 공개 API 제공: 키·쿼터·버전·멱등성
- **해당:** 개발자용 공개 API, 파트너 API
- **무엇/왜:** 외부 개발자의 스크립트는 버그가 있어도 우리가 고칠 수 없다. 무한 재시도 루프, 동시 대량 호출이 일상이다. 키별 쿼터, 429 + `Retry-After`, 쓰기 API의 `Idempotency-Key`, 버전 고정이 기본 통제다.
- **실패 양상:** 한 파트너의 재시도 루프가 전체 API를 마비, 재시도 POST로 주문 중복 생성, 응답 형식 변경으로 파트너 연동 일제히 장애.
- **신호:** 🟢 `ApiKey`/`api_keys` 테이블, `X-API-Key`, `openapi.yaml`/`swagger` · 🟢 `express-rate-limit`, `rate-limiter-flexible`, `slowapi`, `django-ratelimit` · 🔴 공개 POST 엔드포인트에 멱등성 키 처리 없음
- **시나리오·수준:** T-CTL-007을 T 수준과 무관하게 필수로(규칙 후보), C≥2(C-CTL-003)
- **처방:** 티어 0: 플랫폼 방화벽 레이트 리밋 + 앱 키별 쿼터 · 티어 1/2: API 게이트웨이 사용 계획 또는 Redis 토큰 버킷
- **검증:** 키 하나로 한도 초과 → 429 + `Retry-After`, 같은 멱등성 키 재전송 → 같은 응답
- **비용 영향:** Redis 공유 시 거의 0
- **출처:** https://www.rfc-editor.org/rfc/rfc6585#section-4 (429, Retry-After), 설계 S12(Stripe Idempotency-Key, https://docs.stripe.com/api/idempotent_requests)

### W-032 웹훅 발송자 역할
- **해당:** 고객 서버로 이벤트를 보내는 SaaS(결제 알림, 상태 변경 통지)
- **무엇/왜:** 수신자 서버는 느리거나 죽어 있다. 요청 경로에서 동기로 보내면 고객 장애가 우리 장애가 된다. 표준 관행은 큐 + 지수 백오프 재시도(며칠에 걸침) + 서명 + `webhook-id`(수신자 중복 제거용) + 15~30초 타임아웃.
- **실패 양상:** 한 고객 엔드포인트가 30초씩 응답 안 해 워커 전체가 막힘, 재시도 시 수신자가 중복 처리, 서명 없어 위조 이벤트 주입.
- **신호:** 🟡 `webhook_url`/`callback_url` 컬럼 + 핸들러 안에서 `fetch(webhookUrl)` · 🔴 위 호출에 타임아웃 없음(`ext.no_timeout`) · 🟢 `svix`, `standardwebhooks` 의존성(충족 후보)
- **시나리오·수준:** C≥2, D≥2(고객 장애 격리), T≥2(팬아웃)
- **처방:** 공통: 아웃박스 → 발송 워커, 엔드포인트별 동시성 상한·서킷 브레이커, `410 Gone`이면 비활성화 · 티어 0: 관리형 웹훅 서비스
- **검증:** 수신자 지연·5xx 주입 시 다른 고객 발송 지연 없음, 재시도 시 같은 `webhook-id`
- **비용 영향:** 워커·큐 소폭
- **출처:** https://github.com/standard-webhooks/standard-webhooks/blob/main/spec/standard-webhooks.md (`webhook-id`·`webhook-timestamp`·`webhook-signature`, 즉시·5초·5분·30분 … 최대 24시간 간격 재시도와 지터, 15~30초 타임아웃 권장, 410은 수신 중단 신호) ⚠️출처부적격

### IoT·게임·커머스·예약

### W-033 IoT·텔레메트리: 장시간 연결과 연결 폭풍
- **해당:** 센서 수집, 디바이스 관리, 차량 텔레메트리
- **무엇/왜:** 디바이스 수는 고정적이지만 모두 장시간 연결을 유지하고, 정전·네트워크 복구 시 한꺼번에 재접속한다. 직접 MQTT 브로커를 운영하면 연결 상태가 있는 서비스가 되어 티어 0/1 서버리스와 맞지 않는다. 관리형 브로커에도 연결당·계정당 한도가 있다.
- **실패 양상:** 지역 정전 복구 후 수만 대 동시 재접속 → 브로커·인증 과부하, 텔레메트리 쓰기 폭증으로 DB 정체.
- **신호:** 🟢 `mqtt`, `aedes`, `paho-mqtt`, `@aws-sdk/client-iot`, `aws-iot-device-sdk` · 🟢 `Device`/`Telemetry`/`Reading` 테이블, `timescaledb`
- **시나리오·수준:** T2(사용자 수는 고정이지만 재연결 폭풍은 예고 없음 → 재접속 램프를 가정에 반영), C0~1(텔레메트리), C2(명령 전달)
- **처방:** 티어 0: 부적합(장시간 브로커) → 관리형 IoT 브로커 · 티어 1: AWS IoT Core + 규칙으로 큐/시계열 DB 적재 · 티어 2: 자체 브로커(EMQX 등) StatefulSet은 이미 k8s 운영 중일 때만
- **검증:** 가정 디바이스 수 × 재접속 램프로 연결 폭풍 테스트
- **비용 영향:** 관리형 브로커는 메시지·연결 시간 과금
- **출처:** https://docs.aws.amazon.com/general/latest/gr/iot-core.html (페이로드 128KB, 클라이언트 ID당 초당 연결 1회, 연결당 초당 publish 100, 계정당 초당 연결 3,000(일부 리전 100), 웹소켓 연결 최대 24시간, keep-alive 최대 1200초)

### W-034 게임·랭킹: 핫 키와 정렬 집합
- **해당:** 리더보드, 실시간 투표, 좋아요 카운터, 조회수
- **무엇/왜:** "전체 랭킹 1개 행/키"에 모든 사용자가 동시에 쓰면 DB 행 잠금 경합이나 단일 키 병목(핫 키)이 생긴다. 랭킹은 Redis 정렬 집합(ZADD/ZINCRBY O(log N))이 표준이고, 카운터는 샤딩하거나 주기 집계한다. Firestore는 단일 문서 쓰기 빈도 한도가 있어 카운터에 특히 불리하다.
- **실패 양상:** 이벤트 시작 시 `UPDATE leaderboard SET score = score + 1` 행 잠금 대기로 전체 API 지연, 점수 누락.
- **신호:** 🟢 `zadd`/`zincrby`/`zrevrange` · 🟡 `score`/`rank`/`leaderboard`/`vote_count` 컬럼 + `UPDATE ... + 1` · 🔴 단일 행 카운터 + T≥2 신호(시즌 오픈, 이벤트)
- **시나리오·수준:** T≥2, C2(점수 중복 제출 멱등)
- **처방:** 티어 0: Upstash 같은 서버리스 Redis · 티어 1/2: 매니지드 Redis 정렬 집합, DB에는 주기 스냅샷
- **검증:** 동일 키에 동시 쓰기 1,000건, 최종 값 일치·지연
- **비용 영향:** Redis 1개
- **출처:** https://redis.io/docs/latest/develop/data-types/sorted-sets/ (ZADD O(log N), 리더보드 용례)

### W-035 커머스·티켓팅 선착순: 대기열과 입장 제어
- **해당:** 한정 판매, 콘서트 티켓, 수강 신청, 쿠폰 선착순
- **무엇/왜:** 예고된 시각에 수요가 용량의 수십~수백 배로 몰린다. 오토스케일은 1분 램프를 따라가지 못한다. 앞단 대기열(가상 대기실)로 입장 속도를 용량에 맞추고, 재고 차감은 잠금·조건부 갱신으로 초과 판매를 막아야 한다.
- **실패 양상:** 오픈 1분 안에 5xx 폭주, 초과 판매(재고 −37), 새로고침 폭탄으로 회복 불가.
- **신호:** 🟡 `open_at`, `sale_starts_at`, `starts_at`, "선착순", "오픈", "한정" 문구 · 🟢 `stock`/`inventory`/`seats_remaining` + 차감 코드(`concurrency.decrement_no_lock`) · 🟢 대기열 라이브러리·서비스 SDK
- **시나리오·수준:** T3(선착순 → §4.2 T L3), C3(재고 차감), U3(C3 & T≥2)
- **처방:** 공통: 대기열 토큰(Redis 기반 또는 CDN 대기실) + 조건부 차감(`UPDATE ... WHERE stock > 0`) + 사전 증설(T-CTL-005) · 티어 1: 최소 인스턴스 상향 스케줄 · 티어 2: 자리표시 Pod로 노드 여유(T-CTL-009)
- **검증:** P4 C 검증 "마지막 재고 1개에 동시 주문 100건" + T L3 스파이크
- **비용 영향:** 이벤트 시간대만 증설 → 시간당 피크 비용으로 산정
- **출처:** 일반 원칙(출처 미확인). 하위 통제는 설계 T-CTL-005/006/009, C-CTL-005의 출처를 따름 ⚠️근거없음

### W-036 예약 시스템: 이중 예약 방지
- **해당:** 숙소·식당·병원·회의실 예약, 시간 슬롯 예약
- **무엇/왜:** "조회 → 비어 있으면 INSERT"는 동시 요청 두 개가 모두 통과한다. 슬롯이 이산적이면 (자원, 슬롯) 유니크 제약으로 충분하고, 시간 구간이 자유로우면 Postgres 배제 제약(EXCLUDE USING gist, 구간 겹침 `&&`)이 DB 차원에서 겹침을 막는다.
- **실패 양상:** 같은 방에 두 팀 예약, 같은 진료 시간에 두 환자.
- **신호:** 🟢 `Reservation`/`Booking`/`Appointment` 테이블 + `start_at`/`end_at` 또는 `tstzrange` · 🔴 겹침 검사 SELECT 후 INSERT, 유니크·배제 제약 없음 · 🟢 `EXCLUDE USING gist`
- **시나리오·수준:** C3(좌석 차감 패턴과 동급으로 다룸 → §4.2 C L3에 "예약 슬롯" 추가 후보), T2(예약 오픈 시각)
- **처방:** 공통: 유니크 제약 또는 배제 제약 + 충돌 시 사용자에게 재선택 안내, 임시 홀드는 TTL
- **검증:** 같은 슬롯 동시 예약 100건 → 성공 1건
- **비용 영향:** 없음(DB 제약)
- **출처:** https://www.postgresql.org/docs/current/ddl-constraints.html (Exclusion Constraints: 두 행이 지정 연산자로 비교될 때 하나는 거짓이어야 함, `EXCLUDE USING gist (c WITH &&)`)

### 콘텐츠·Next.js

### W-037 정적 생성·ISR과 다중 인스턴스 캐시
- **해당:** 블로그, 문서 사이트, 상품 상세, 마케팅 페이지
- **무엇/왜:** 대부분 정적으로 만들 수 있는 콘텐츠는 CDN이 트래픽 폭증을 흡수하므로 T 처방이 거의 필요 없다(과잉 탐지 근거). 다만 Next.js를 직접 호스팅하면 ISR 캐시가 인스턴스마다 따로 있어 `revalidatePath` 호출이 받은 인스턴스에만 반영된다. 정적 내보내기(`output: 'export'`)는 ISR을 지원하지 않는다.
- **실패 양상:** 글을 고쳤는데 새로고침할 때마다 옛 글/새 글이 번갈아 보임(인스턴스별 캐시), 컨테이너 재시작마다 캐시 소실로 원본 부하 급증.
- **신호:** 🟢 `export const revalidate`, `generateStaticParams`, `revalidatePath`, `revalidateTag`, `getStaticProps` · 🟢 `next.config`의 `cacheHandler` 유무 · 🔴 ISR 사용 + 티어 1/2 다중 인스턴스 + `cacheHandler` 없음
- **시나리오·수준:** T 판정 완화(정적 비율 높으면 T1 유지로 충분), C1(콘텐츠 일관성)
- **처방:** 티어 0: Vercel·Netlify는 플랫폼이 공유 캐시 제공(유지 권고, TIER-005) · 티어 1/2: Redis 등 공유 `cacheHandler` + `cacheMaxMemorySize: 0`, 또는 인스턴스 1개 + CDN
- **검증:** 인스턴스 2개에서 `revalidatePath` 후 모든 인스턴스 응답의 `x-nextjs-cache`와 내용 확인
- **비용 영향:** 정적화가 가장 싼 T 대책
- **출처:** https://nextjs.org/docs/app/guides/incremental-static-regeneration (다중 인스턴스에서 기본 파일 시스템 캐시는 인스턴스별, 온디맨드 재검증은 받은 인스턴스만 무효화, 정적 내보내기 미지원), https://nextjs.org/docs/app/guides/self-hosting (custom cache handler)

### W-038 Next.js를 여러 인스턴스로 돌릴 때의 숨은 공유 상태
- **해당:** Vercel 밖(티어 1/2)으로 옮기는 Next.js 앱
- **무엇/왜:** Server Actions는 빌드마다 다른 암호화 키를 쓰므로 인스턴스마다 빌드를 따로 하면 "Failed to find Server Action" 오류가 난다. 롤링 배포 중 구·신 버전이 섞이면 자산 누락(버전 차이)이 생긴다. Vercel에서는 플랫폼이 처리해 주던 부분이다.
- **실패 양상:** 티어 1로 이전 직후 간헐적 폼 제출 실패, 배포 중 화면 깨짐.
- **신호:** 🟢 `'use server'` 사용 · 🟢 `next.config`의 `deploymentId`, `generateBuildId` 유무 · 🟡 `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY` 미설정
- **시나리오·수준:** U≥1(배포 중 오류), 티어 0 → 1 이전 비용(`migration_effort`)에 반영
- **처방:** 티어 1/2: 이미지 하나를 빌드해 모든 인스턴스에 사용, `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY` 고정, `deploymentId` 설정, 앞단 프록시 스트리밍 버퍼링 끄기(W-005)
- **검증:** 롤링 배포 중 Server Action 호출 오류율 0
- **비용 영향:** 없음. 이전 작업량 +small
- **출처:** https://nextjs.org/docs/app/guides/self-hosting (Server Functions encryption key, deploymentId와 version skew, 같은 빌드로 여러 컨테이너 기동)

### 사내 도구·재난 알림·규제·위치

### W-039 사내 도구: SSO와 네트워크 제한
- **해당:** 백오피스, 관리자 대시보드, 사내 업무 시스템
- **무엇/왜:** 사용자 수가 직원 수로 고정되어 T0~1이면 충분하다. 대신 공개 인터넷 노출 자체가 위험이므로 SSO와 IP 제한·사설 네트워크가 핵심 통제다. 일부 저가 플랜은 사설 네트워크·IP 제한을 지원하지 않는다.
- **실패 양상:** 과잉(멀티 AZ EKS) 또는 반대로 관리자 페이지가 공개 URL로 노출되어 크리덴셜 스터핑 대상.
- **신호:** 🟢 `next-auth` + Azure AD/Okta/Google Workspace(`hd` 파라미터), `passport-saml`, `python3-saml`, `django-allauth` SSO 공급자 · 🟢 회원가입 라우트 부재 · 🟡 `admin`, `internal`, `backoffice` 이름
- **시나리오·수준:** T0(§4.2 T L0), U0 가능, COST-001 과잉 탐지의 주요 대상
- **처방:** 티어 0: 플랫폼 접근 보호(배포 보호·SSO) · 티어 1: ACA 내부 환경·인그레스, Cloud Run IAP/내부 인그레스, ECS 내부 ALB · 티어 2는 기본 제외(TIER-004)
- **검증:** 외부 IP에서 접근 차단 확인, SSO 없는 로그인 경로 없음
- **비용 영향:** 최소 구성이 정답인 도메인 → 축소 처방 중심
- **출처:** https://learn.microsoft.com/en-us/azure/container-apps/ingress-overview (내부 환경은 공개 엔드포인트 없음, IP 제한, 인증 내장), https://render.com/docs/free (Free 웹 서비스는 사설 네트워크 트래픽 수신 불가)

### W-040 재난·공공 알림: 폭증과 장애가 동시에 온다
- **해당:** 재난 문자 연동 서비스, 대피소 안내, 공공 공지, 속보
- **무엇/왜:** 다른 도메인은 장애와 폭증이 독립이지만 여기서는 같은 사건이 둘을 동시에 만든다. 사용자는 저대역폭·혼잡 네트워크에서 접속한다. 핵심 정보는 동적 렌더링 없이 CDN에서 나가는 정적 폴백(가벼운 HTML)으로 보장하고, 원본·DB·외부 API가 죽어도 마지막 정상 데이터를 보여줘야 한다.
- **실패 양상:** 지진 직후 트래픽 50배 + 같은 리전 장애 → 완전 불통, 무거운 SPA 번들이 혼잡망에서 로드 안 됨.
- **신호:** 🟡 "재난", "대피", "경보", "shelter", "evacuation", "earthquake", "alert" 문구 · 🟢 공공 API 호출(기상·재난 데이터) · 🟢 푸시·SMS 발송 SDK(W-023, W-024)
- **시나리오·수준:** D3, T3 (§4.2). 가정: 피크 ×20은 이 도메인에 과소일 수 있음(새 축·규칙 후보 참조)
- **처방:** 공통: 핵심 페이지 정적 생성 + 긴 CDN TTL + stale-while-revalidate, 가벼운 텍스트 전용 페이지, 외부 데이터는 마지막 정상값 캐시 · 티어 0: 정적 호스팅 + 다중 리전 CDN이 오히려 유리 · 티어 1/2: 원본 장애 시 CDN이 stale 응답
- **검증:** 원본 차단 상태에서 핵심 페이지 응답(P4 D L3), 3G 스로틀링 조건에서 첫 화면 시간
- **비용 영향:** 정적화는 싸고, 다중 리전 원본은 비쌈 → 정적 폴백 우선
- **출처:** 일반 원칙(출처 미확인). 설계 §4.1 D L3 정의, https://vercel.com/docs/regions (리전 장애 시 다음 리전으로 자동 우회, 함수 리전 페일오버는 Enterprise) ⚠️근거없음

### W-041 규제 데이터(의료·금융): 계약·감사·데이터 위치
- **해당:** 의료 기록, 결제·계좌, 개인 신용 정보
- **무엇/왜:** 규제 데이터는 "기술적으로 가능한가"보다 "그 서비스를 규제 데이터에 써도 되는가"가 먼저다. 예: 미국 HIPAA는 클라우드와 BAA를 맺고 BAA 대상(eligible) 서비스만 PHI에 써야 한다. AWS는 ECS·Fargate·EKS·RDS·S3를 대상 목록에 두지만 App Runner는 목록에서 확인되지 않았다. Supabase는 호스팅 플랫폼에서 BAA 체결 시 지원, 자체 호스팅은 미지원. 한국 개인정보보호법·전자금융 규정의 세부 요건은 이 문서 범위에서 확인하지 못했다.
- **실패 양상:** 기술적으로 잘 돌아가는 구성을 규제 때문에 전부 다시 옮김(가장 비싼 이전), 감사 로그 부재로 사고 조사 불가.
- **신호:** 🟢 FHIR/HL7 라이브러리(`fhir`, `@medplum/core`, `hl7`), `Patient`/`MedicalRecord`/`Prescription` 테이블 · 🟢 `Ledger`/`Transaction`/`Balance`/`KYC` · 🟡 주민번호·계좌번호 패턴 필드
- **시나리오·수준:** D3(의료 → §4.2 D L3), C3(금융), 티어 제외 조건: "BAA/규제 대상 아님"인 플랫폼 제외(규칙 후보)
- **처방:** 공통: 감사 로그(누가 언제 무엇을 조회), 저장·전송 암호화, 데이터 리전 고정 · 티어 선택: 규제 대상 서비스 목록 확인 후 후보 제한
- **검증:** 플랫폼 계약(BAA 등) 존재를 사용자 확인 항목으로 리포트에 표시(코드로 확인 불가 → "미확인")
- **비용 영향:** 규제 대응 플랜은 상위 요금제가 많음
- **출처:** https://aws.amazon.com/compliance/hipaa-eligible-services-reference/ (BAA 필요, ECS·Fargate·EKS·RDS·S3 대상, App Runner는 목록에서 확인 안 됨), https://supabase.com/docs/guides/security/hipaa-compliance (BAA 체결 필요, 자체 호스팅 미지원)

### W-042 지도·위치 서비스
- **해당:** 주변 검색, 배달·모빌리티 위치 추적, 지오펜싱
- **무엇/왜:** 위치 갱신은 이동 중인 사용자 수 × 갱신 주기만큼 쓰기를 만든다(분석 이벤트와 비슷한 쓰기 폭증). 반경 검색은 공간 인덱스(PostGIS GiST 등) 없으면 전체 스캔. 지도·지오코딩 API는 호출 건당 과금(W-016).
- **실패 양상:** 출퇴근 시간 위치 쓰기로 DB 쓰기 포화, `lat BETWEEN` 조건 전체 스캔, 지오코딩 비용 폭주.
- **신호:** 🟢 `postgis`, `geography(`, `ST_DWithin`, `h3-js`, `@turf/turf`, `mapbox-gl`, `leaflet`, 카카오·네이버 지도 SDK · 🟡 `lat`/`lng` 컬럼 + 인덱스 없음 · 🟡 위치 업데이트 라우트 호출 주기 상수
- **시나리오·수준:** T≥2(통근 시간대 예측 가능 피크), C1(최신 위치는 덮어써도 됨), 비용 필터
- **처방:** 공통: 최신 위치는 Redis(GEO) 또는 덮어쓰기, 이력은 배치 적재, 공간 인덱스, 지오코딩 결과 캐시
- **검증:** 가정 이동 사용자 × 주기 부하에서 DB 쓰기 IOPS
- **비용 영향:** 외부 지도 API가 최대 변동비가 될 수 있음
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### 추가 유형

### W-043 협업 편집(동시 편집, 화이트보드): 문서별 단일 조정자
- **해당:** 노션·피그마 류 동시 편집, 공유 화이트보드, 멀티플레이 커서
- **무엇/왜:** 같은 문서를 편집하는 사람들의 변경을 한 곳에서 순서화(또는 CRDT 병합)해야 한다. 일반 무상태 서버 + Redis Pub/Sub로도 가능하지만, "문서 하나 = 조정자 하나" 모델(Cloudflare Durable Objects 등)이 더 단순하다. Durable Objects의 웹소켓 하이버네이션은 유휴 연결에 실행 시간 과금이 없다.
- **실패 양상:** 두 인스턴스가 같은 문서 변경을 각자 저장해 마지막 저장자가 덮어씀, 유휴 연결에도 서버 비용 지속.
- **신호:** 🟢 `yjs`, `y-websocket`, `automerge`, `@liveblocks/*`, `@tiptap/extension-collaboration`, `partykit` · 🟡 문서 저장이 소켓 메시지마다 DB UPDATE
- **시나리오·수준:** C2(병합 일관성), T1, D1(문서 스냅샷 백업)
- **처방:** 티어 0: Cloudflare Durable Objects + 하이버네이션, 또는 관리형 협업 서비스 · 티어 1/2: y-websocket 서버 + Redis + 문서별 라우팅, 주기 스냅샷
- **검증:** 두 클라이언트 동시 편집 후 최종 문서 일치
- **비용 영향:** 하이버네이션 사용 시 유휴 연결 비용 0에 가까움
- **출처:** https://developers.cloudflare.com/durable-objects/best-practices/websockets/ (하이버네이션 중 Duration(GB-s) 과금 없음, 연결 유지, 첨부 데이터 16,384바이트)

### W-044 사용자 코드·에이전트 코드 실행(샌드박스)
- **해당:** 코딩 교육, AI 에이전트의 코드 실행, 온라인 저지, 노트북 서비스
- **무엇/왜:** 신뢰할 수 없는 코드를 웹 서버와 같은 프로세스·컨테이너에서 실행하면 비밀·DB 접근 권한이 그대로 노출된다. 실행마다 격리된 샌드박스가 필요하고, 이는 플랫폼 선택을 크게 좁힌다.
- **실패 양상:** 사용자 코드가 환경변수의 DB 비밀번호를 읽음, 무한 루프로 인스턴스 독점.
- **신호:** 🔴 `child_process.exec`/`eval`/`vm.runInNewContext`/`subprocess`에 사용자 입력 전달 · 🟢 `e2b`, `@vercel/sandbox`, `dockerode`, `judge0` 관련 코드
- **시나리오·수준:** 보안 영역 교차, T-CTL-008(격리), 티어 0 서버리스 함수에서 직접 실행 금지
- **처방:** 티어 0: 관리형 샌드박스(Vercel Sandbox 등) · 티어 1: ACA dynamic sessions 같은 격리 세션 · 티어 2: gVisor/Kata 런타임 노드 풀 + 네트워크 정책(TIER-004 "네트워크 정책 필요" 해당)
- **검증:** 샌드박스에서 메타데이터 엔드포인트·DB 접근 시도 차단
- **비용 영향:** 세션당 과금(ACA 코드 인터프리터 세션은 할당 시간 1시간 단위 과금)
- **출처:** https://learn.microsoft.com/en-us/azure/container-apps/billing (dynamic sessions: 코드 인터프리터는 할당~해제 시간을 1시간 단위로 과금, 커스텀 컨테이너는 Dedicated 플랜)

### W-045 크롤러·외부 연동 수집기: 고정 egress IP와 상대방 레이트 리밋
- **해당:** 스크래핑, 외부 API 동기화, 파트너사 IP 허용 목록이 필요한 연동(은행·공공 API)
- **무엇/왜:** 상대방이 IP 허용 목록을 요구하면 고정 송신 IP가 필요하다. 서버리스·관리형 컨테이너는 기본적으로 송신 IP가 바뀌므로 NAT·정적 IP 옵션(유료)이 필요하다. 상대방 레이트 리밋을 넘으면 차단당한다.
- **실패 양상:** 배포·확장 때마다 송신 IP가 바뀌어 파트너 API 403, 수집 작업이 상대 한도를 넘어 IP 차단.
- **신호:** 🟡 README/설정에 "IP whitelist", "허용 IP" · 🟢 `puppeteer`/`playwright`/`scrapy`/`cheerio` + 스케줄 · 🟢 `PROXY_URL`, `HTTPS_PROXY` 환경변수
- **시나리오·수준:** D≥1(외부 의존성), 비용 필터(정적 IP·NAT 비용, COST-002와 연결)
- **처방:** 티어 0: 플랫폼 정적 IP 옵션(유료) · 티어 1: Cloud Run/ECS + NAT 게이트웨이 고정 IP · 티어 2: 동일
- **검증:** 재배포 전후 송신 IP 동일
- **비용 영향:** Fly.io 정적 egress IP 시간당 $0.005(월 약 $3.60), AWS NAT 서울 시간당 $0.059 + GB당 $0.059(S18)
- **출처:** https://docs.fly.io/about/pricing/ (Static Egress IPs $0.005/시간), 설계 S18(NAT Gateway 요금) ⚠️출처부적격

### W-046 모바일 백엔드의 푸시 토큰·오프라인 동기화
- **해당:** 모바일 앱, PWA
- **무엇/왜:** 모바일은 오프라인에서 쓰고 나중에 동기화한다. 같은 쓰기가 네트워크 재시도로 여러 번 도착하므로 클라이언트 생성 ID(멱등성 키)가 필요하다. 푸시 토큰은 앱 재설치·만료로 계속 바뀌며, 무효 토큰을 정리하지 않으면 발송 실패율과 비용이 쌓인다.
- **실패 양상:** 지하철에서 쓴 메모가 3개로 중복 저장, 푸시 실패율 40%.
- **신호:** 🟢 `react-native`, `expo`, `flutter`, `@react-native-firebase/messaging` · 🟡 `device_tokens`/`push_tokens` 테이블 + 무효 토큰 삭제 코드 부재 · 🟡 클라이언트 측 UUID 생성 없이 서버 자동 증가 ID만 사용
- **시나리오·수준:** C2(클라이언트 재시도 경로 → §4.2 C L2), W-030과 함께 U2
- **처방:** 공통: 클라이언트 생성 UUID + 업서트, 발송 응답의 무효 토큰 삭제
- **검증:** 같은 요청 3회 재전송 후 레코드 1개
- **비용 영향:** 없음
- **출처:** 일반 원칙(출처 미확인). 멱등성 키 관행은 설계 S12(https://docs.stripe.com/api/idempotent_requests) ⚠️근거없음

---

## 파트 2. 도메인 → 필요 수준·가정 매핑

### 2.1 읽는 법
- 수준은 §4.2 규칙을 이 도메인의 **전형적인 신호**에 적용했을 때 나오는 **기본값 제안**이다. 실제 판정은 코드 신호로 다시 계산되며, 여러 규칙이 걸리면 높은 쪽을 쓴다.
- U는 §4.2 U 규칙(T=0 & D≤1 → U0, T≥2 또는 C≥2 또는 마이그레이션 → U2, C=3 & T≥2 → U3)을 적용한 결과다.
- 평시 동시 접속 기본값과 피크 배수는 **설계 가정 제안이며 공식 출처가 없다**(§4.3의 T 수준별 배수 ×3/×10/×20과 맞춰 정했다). 근거 칸은 왜 그 값인지에 대한 추론이다. ⚠️근거없음
- 굵게 표시한 도메인은 §7.1 목록에 없는 **추가 제안**이다.

### 2.2 수준과 가정

| 도메인 | D | T | U | C | 평시 동시 접속 | 피크 배수·램프 | 근거 |
|---|---|---|---|---|---|---|---|
| 커뮤니티 | 1 | 1 | 1 | 1 (알림 큐·웹훅 있으면 2) | 50 | ×3, 10분 | 사용자 생성 글 → D1. 저녁 시간대 완만한 증가. 바이럴 글은 읽기 위주라 캐시로 흡수 |
| 커머스 | 2 | 2 | 3 (C3 & T2) | 3 | 100 | ×10, 예고 시각 | 결제 → D2·C3. 세일·쿠폰·라이브 커머스는 예고 이벤트 → T2. 선착순 문구가 있으면 T3 |
| 예약·티켓팅 | 2 | 3 (선착순 없으면 2) | 3 | 3 | 30 | ×20, 1분 (오픈 시각) | 좌석·슬롯 차감 → C3(W-036). 티켓 오픈은 1분 안에 수십 배. 평시는 낮음 |
| 사내 도구 | 1 | 0 | 0 | 1 | 20 | ×1 (고정) | 공개 가입 없음·SSO → T0. 사용자 = 직원 수 이하. 업무 시작 시각 소폭 집중은 여유 용량으로 흡수 |
| 콘텐츠·블로그 | 0 (DB 없음, MD 파일) / 1 (CMS DB) | 1 | 1 | 0~1 | 50 | ×3, 10분 | 정적 생성이면 폭증을 CDN이 흡수(W-037). 쓰기는 작성자만 |
| SaaS B2B | 2 | 1 | 2 (C≥2) | 2 (구독 결제 SDK 있으면 3) | 30 | ×3, 10분 (업무 시작 시각) | 조직·청구 모델 → D2(§4.2). 웹훅·작업 큐 흔함 → C2. 사용자 수는 계약 좌석으로 상한 |
| 재난·공공 알림 | 3 | 3 | 2 (T≥2) | 2 (중복 발송 방지) | 20 | ×20, 1분 (규칙 기본). 실제는 더 클 수 있음 | D3·T3(§4.2). 평시 거의 0, 사건 시 폭증 + 장애 동시(W-040) |
| 실시간·채팅 | 1 | 1 (라이브 이벤트형이면 3) | 1 | 2 (메시지 재전송 중복 제거) | 동시 **연결** 100 | ×3, 10분 | 지표가 요청 수가 아니라 연결 수. 메시지 클라이언트 재시도 → C2 |
| 기타 | 1 | 1 | 1 | 1 | 50 | ×3, 10분 | §4.3 기본값 |
| **AI·LLM 앱** | 1 | 1 (런칭 이벤트면 2) | 1 | 1 (크레딧 차감 있으면 3) | 20 | ×3, 10분 | 처리량 상한이 우리 인프라가 아니라 프로바이더 한도(W-012). 크레딧 = 잔액 차감 |
| **교육·시험(LMS)** | 2 | 2 | 2 | 2 | 30 | ×10, 시험 시작 시각 | 제출물·성적은 잃으면 안 됨. 시험·수강 신청 시작 시각 예고. 제출 재시도 중복 |
| **핀테크·금융** | 2 | 1 | 2 | 3 | 30 | ×3, 10분 | 잔액·이체 → C3. 규제(W-041)는 수준이 아니라 티어 제외 조건으로 다룸 |
| **헬스케어·의료** | 3 | 1 | 2 | 2 (처방·재고 차감 있으면 3) | 20 | ×3, 10분 | §4.2 D L3(의료). 예약 기능 있으면 W-036 적용 |
| **미디어·UGC 공유** | 1 | 1 | 1 | 1 | 50 | ×3, 10분 | 원본 파일 보존 → D1. 비용 지배 항목은 egress(W-009) |
| **게임·랭킹·투표** | 1 | 2 (시즌·이벤트 오픈) | 2 | 2 | 50 | ×10, 예고 시각 | 핫 키(W-034). 점수 중복 제출 |
| **IoT·텔레메트리** | 1 | 2 (재연결 폭풍) | 2 | 1 (명령 경로는 2) | 디바이스 수 (기본 100) | ×10, 1분 (정전 복구 재접속) | 디바이스 수는 고정이지만 재접속은 예고 없이 동시(W-033) |
| **공개 API·개발자 플랫폼** | 2 | 1 (+ 레이트 리밋 필수) | 2 | 2 | 클라이언트 50 | ×3, 10분 | 외부 스크립트 재시도 → 멱등성. 고객 계약 → D2 |
| **지도·위치·모빌리티** | 1 | 2 (통근 시간대) | 2 | 1 (위치는 덮어쓰기) | 50 | ×10, 30분 | 예측 가능한 일일 피크. 위치 쓰기 폭증(W-042) |
| **랜딩·포트폴리오·데모** | 0 | 1 | 1 | 0 | 10 | ×3, 10분 | 영속 데이터 없음. 정적 호스팅이 정답, 그 이상은 과잉 |

### 2.3 도메인을 알아보는 코드 신호

| 도메인 | 라우트·파일명 | 스키마 테이블·컬럼 | 라이브러리 | 문구(README·UI) |
|---|---|---|---|---|
| 커뮤니티 | `/board`, `/posts`, `/feed`, `/thread`, `/comments` | `Post`, `Comment`, `Like`, `Follow`, `Report` | (특정 라이브러리 없음) 마크다운 에디터, `sanitize-html` | 게시판, 커뮤니티, 댓글, 팔로우, feed |
| 커머스 | `/cart`, `/checkout`, `/products/[id]`, `/orders` | `Product`, `Order`, `OrderItem`, `Cart`, `Inventory`/`stock`, `Coupon` | `stripe`, `@tosspayments/*`, `portone`/`iamport`, `@shopify/*`, `medusa` | 장바구니, 결제, 주문, 쿠폰, 세일, 배송 |
| 예약·티켓팅 | `/book`, `/reserve`, `/tickets`, `/events/[id]/seats`, `/queue` | `Reservation`, `Booking`, `Seat`, `Slot`, `TimeSlot`, `Ticket`, `tstzrange`, `open_at` | 캘린더(`fullcalendar`, `react-big-calendar`), 대기열 SDK | 예약, 예매, 좌석, 선착순, 오픈, 매진 |
| 사내 도구 | `/admin/*`만 존재, 가입 라우트 없음 | `Employee`, `Department`, `Approval` | `passport-saml`, `next-auth`(AzureAD/Okta/Google `hd`), `@retool/*`, `react-admin` | 사내, 백오피스, 관리자, internal, 결재 |
| 콘텐츠·블로그 | `content/**/*.md(x)`, `/blog/[slug]`, `/rss.xml`, `sitemap` | `Article`, `Tag` (또는 DB 없음) | `contentlayer`, `next-mdx-remote`, `@sanity/client`, `contentful`, `gray-matter`, `astro`, `hugo`·`jekyll` 설정 | 블로그, 글, 포스트, 문서, docs |
| SaaS B2B | `/org/[slug]`, `/workspace`, `/settings/billing`, `/invite`, `/members` | `Organization`, `Workspace`, `Team`, `Membership`, `tenant_id`, `Plan`, `Subscription`, `Invoice`, `Seat` | `stripe`(Billing), `@clerk/*` 조직 기능, `casl`/`oso`(RBAC) | 팀, 워크스페이스, 요금제, 좌석, 초대, B2B |
| 재난·공공 알림 | `/alerts`, `/shelters`, `/evacuation`, `/map` | `Alert`, `Shelter`, `Incident`, `Region` | 지도 SDK, `firebase-admin` 메시징, SMS SDK, 공공 데이터 API 클라이언트 | 재난, 대피, 경보, 지진, 태풍, 긴급, 안전 |
| 실시간·채팅 | `/chat`, `/rooms/[id]`, `/ws`, `/socket.io` | `Message`, `Room`, `Channel`, `Participant`, `ReadReceipt` | `socket.io`, `ws`, `pusher`, `ably`, `@supabase/realtime-js`, `channels` | 채팅, 메시지, 실시간, 접속 중, 입력 중 |
| AI·LLM 앱 | `/api/chat`, `/api/generate`, `/api/embed` | `Conversation`, `Message(role)`, `Embedding`, `vector(` , `credits`, `usage` | `openai`, `@anthropic-ai/sdk`, `ai`, `langchain`, `llamaindex`, `pgvector` | AI, 챗봇, 어시스턴트, 생성, 요약, RAG |
| 교육·시험 | `/courses`, `/lessons`, `/quiz`, `/exam`, `/submit` | `Course`, `Enrollment`, `Quiz`, `Exam`, `Submission`, `Grade`, `deadline` | `scorm`/`xapi` 라이브러리, 코드 실행 샌드박스(W-044) | 강의, 수강, 시험, 과제, 마감, 성적 |
| 핀테크·금융 | `/transfer`, `/accounts`, `/ledger` | `Account`, `Ledger`, `Transaction`, `Balance`, `Transfer`, `KYC` | `plaid`, 오픈뱅킹 SDK, `decimal.js`/`Decimal` | 송금, 계좌, 잔액, 정산, 이체 |
| 헬스케어·의료 | `/patients`, `/appointments`, `/records` | `Patient`, `Appointment`, `Prescription`, `MedicalRecord`, `Diagnosis` | `fhir`, `@medplum/*`, `hl7` | 환자, 진료, 처방, 의료, 병원, HIPAA |
| 미디어·UGC | `/upload`, `/media/[id]`, `/watch` | `Media`, `Video`, `Asset`, `Thumbnail`, `duration` | `multer`, `sharp`, `fluent-ffmpeg`, `@mux/*`, `hls.js`, `tus-js-client`, `@uppy/*` | 업로드, 동영상, 갤러리, 스트리밍 |
| 게임·랭킹 | `/leaderboard`, `/match`, `/vote` | `Score`, `Leaderboard`, `Match`, `Season`, `Vote` | `ioredis`(`zadd`), `colyseus`, `phaser` | 랭킹, 순위, 시즌, 투표, 점수 |
| IoT·텔레메트리 | `/devices`, `/telemetry`, `/ingest` | `Device`, `Telemetry`, `Reading`, `Sensor`, 하이퍼테이블 | `mqtt`, `aedes`, `paho-mqtt`, `aws-iot-device-sdk`, `timescaledb` | 디바이스, 센서, 측정, 원격 제어 |
| 공개 API | `/v1/*`, `/api-keys`, `/docs` | `ApiKey`, `Usage`, `Quota`, `RateLimit` | `openapi`/`swagger-ui`, `express-rate-limit`, `slowapi`, `svix` | API, 개발자, SDK, 레이트 리밋, 키 발급 |
| 지도·위치 | `/nearby`, `/locations`, `/track` | `Location`, `lat`/`lng`, `geography`, `Route` | `postgis`, `h3-js`, `@turf/turf`, `mapbox-gl`, `leaflet`, 카카오·네이버 지도 SDK | 주변, 지도, 위치, 배달, 경로 |
| 랜딩·데모 | 페이지 몇 개, API 라우트 없음 | 없음 | `output: 'export'`, 정적 사이트 생성기 | 소개, 포트폴리오, 데모, 해커톤 |

### 2.4 도메인 분류 보조 규칙 제안
- **복합 도메인**: 신호가 두 도메인에 걸치면(예: 커뮤니티 + 커머스) §4.2대로 시나리오별 최고 수준을 쓰고, 평시 동시 접속은 큰 쪽을 쓴다.
- **연결 수 지표 도메인**(실시간·채팅, IoT): 가정 키를 `traffic.baseline_concurrency` 대신 `traffic.baseline_connections`로 따로 둔다(새 축 후보 참조).
- **외부 한도 지배 도메인**(AI·LLM): 피크 용량을 인스턴스가 아니라 프로바이더 한도로 계산하는 보조 가정 `external.llm_tpm_limit`을 둔다.

---

## 파트 3. 플랫폼별 제약과 함정

공통 원칙: 티어 0은 "현재 플랫폼 유지"가 기본(TIER-005). 아래 항목은 (1) 유지가 불가능해지는 조건(티어 제외), (2) 유지하되 고쳐야 할 설정, (3) 다른 티어로 옮길 때의 이전 비용 근거로 쓴다.

### 티어 0 — Vercel

### W-050 Vercel 함수 최대 실행 시간·본문 한도·메모리
- **해당:** Vercel Functions (Fluid compute, 2025-04-23 이후 새 프로젝트 기본)
- **무엇/왜:** 최대 실행 시간 Hobby 300초(기본·최대), Pro/Enterprise 기본 300초·최대 800초·확장 1800초(베타, 특정 런타임만, Secure Compute·Static IP와 병용 불가). 요청·응답 본문 4.5MB. 메모리 Hobby 2GB/1vCPU, Pro 최대 4GB/2vCPU. 번들 250MB(Python 500MB). 동시성은 Hobby·Pro 30,000까지 자동 확장. 과금은 활성 CPU 시간 + 프로비저닝 메모리 시간(I/O 대기는 활성 CPU에 미포함).
- **실패 양상:** 504 `FUNCTION_INVOCATION_TIMEOUT`, 413 `FUNCTION_PAYLOAD_TOO_LARGE`.
- **신호:** 🟢 `vercel.json`, `.vercel/`, `maxDuration` 값 · 🔴 상시 워커 프로세스(`process.worker`), 300/800초 초과 작업, 4.5MB 초과 업로드 경로
- **시나리오·수준:** TIER-001 (이미 설계에 있음, 수치 갱신 근거)
- **처방:** 티어 0 유지: 업로드는 W-006, 긴 작업은 W-013(Vercel Workflows), 워커는 외부 큐 서비스 · 불가하면 티어 1
- **검증:** `vercel.json`/라우트 설정의 `maxDuration` ≤ 플랜 상한
- **비용 영향:** LLM 호출처럼 I/O 대기가 긴 작업은 활성 CPU 과금이라 상대적으로 유리
- **출처:** https://vercel.com/docs/functions/limitations

### W-051 Vercel Hobby는 상업적 사용 금지
- **해당:** Vercel Hobby 플랜
- **무엇/왜:** Hobby는 비상업적 개인 용도만 허용된다. 방문자에게 결제를 받거나, 광고를 넣거나, 제품·서비스 판매를 광고하거나, 돈을 받고 만든 사이트는 상업적 사용이다(기부 요청은 제외). 즉 결제 신호가 있으면 Hobby 유지가 정책상 불가능하다.
- **실패 양상:** 기술적으로는 동작하지만 약관 위반 → 계정·배포 정지 위험. 비용 견적이 $0으로 잘못 나옴.
- **신호:** 🟢 결제 SDK(`stripe`, `@tosspayments/*`), 광고 스크립트(`adsbygoogle`) + Vercel 배포 신호 · 🟡 Vercel 팀 플랜은 코드로 알 수 없음 → "미확인"으로 표시
- **시나리오·수준:** 티어 비용 산정 규칙: 결제·광고 신호 + Vercel → 최소 Pro 요금으로 견적
- **처방:** 티어 0: Pro 플랜 기준으로 견적, 리포트에 정책 근거 표시
- **검증:** 사용자 확인 항목(플랜은 저장소에 없음)
- **비용 영향:** 견적 하한이 Pro 월 기본료로 올라감
- **출처:** https://vercel.com/docs/limits/fair-use-guidelines ("Hobby teams are restricted to non-commercial personal use only", 상업적 사용 예시)

### W-052 Vercel Hobby 크론: 하루 1회, ±59분
- **해당:** Vercel Cron Jobs (`vercel.json`의 `crons`)
- **무엇/왜:** 프로젝트당 100개까지 가능하지만 Hobby는 하루 1회만, 지정 시각에서 최대 59분 늦게 실행. 더 잦은 표현식은 배포 자체가 실패한다. Pro는 분 단위.
- **실패 양상:** `*/5 * * * *` 크론이 있는 저장소를 Hobby에 배포하면 배포 실패. 리마인더가 최대 1시간 늦음.
- **신호:** 🟢 `vercel.json` `crons[].schedule` 파싱 → 하루 1회 초과 여부 · 🟢 시각 정밀도가 중요한 이름(`reminder`, `expire`, `settle`)
- **시나리오·수준:** 티어 0 Hobby 제외 조건(시간당 이상 크론), W-018
- **처방:** Pro 또는 외부 스케줄러(Cloud Scheduler, GitHub Actions 스케줄 등) · 크론 핸들러는 멱등
- **검증:** 크론 표현식 정적 분석
- **비용 영향:** Pro 전환 또는 외부 스케줄러 소액
- **출처:** https://vercel.com/docs/cron-jobs/usage-and-pricing

### W-053 Vercel 함수 기본 리전은 iad1(워싱턴) — 서울 DB면 지연
- **해당:** Vercel Functions + 한국 사용자·서울 DB
- **무엇/왜:** 함수는 기본적으로 `iad1`에서 실행된다. 서울(`icn1`, ap-northeast-2) 리전이 있지만 설정해야 한다. DB가 서울이고 함수가 미국이면 쿼리마다 태평양 왕복. 여러 리전 지정은 Pro 이상.
- **실패 양상:** 페이지당 쿼리 10개 × 왕복 약 150ms 이상 → 체감 수 초. 부하 테스트에서 처리량이 이유 없이 낮음.
- **신호:** 🟢 `vercel.json`의 `regions` 미설정 또는 `iad1` · 🟢 DB 접속 문자열 호스트 리전(`ap-northeast-2`, `aws-0-ap-northeast-2.pooler.supabase.com`)
- **시나리오·수준:** T≥1 (설정 처방), 리전 추론(§4.3 서울 기본)과 불일치 탐지
- **처방:** 티어 0: `regions: ["icn1"]`, DB와 같은 리전
- **검증:** 함수 응답 헤더의 리전, 쿼리 지연 측정
- **비용 영향:** 리전별 요금 차이(지역 가격 페이지) 외 거의 없음
- **출처:** https://vercel.com/docs/regions (19개 컴퓨트 리전, `icn1` = ap-northeast-2 서울, 기본 `iad1`, 함수는 DB와 같은 리전 권장), https://vercel.com/docs/functions/limitations (여러 리전은 Pro·Enterprise)

### W-054 Vercel 웹소켓: 베타, 함수 최대 실행 시간까지만 유지
- **해당:** Vercel Functions에서 웹소켓 서버
- **무엇/왜:** Vercel Functions는 웹소켓을 지원한다(문서 권한 표기 "WebSockets (Beta)", Fluid compute 필요). 연결 하나는 한 인스턴스에 고정되지만, 함수 최대 실행 시간에 도달하면 닫히고, 재연결이 같은 인스턴스로 간다는 보장이 없으며, 배포 후 새 연결은 새 배포·기존 연결은 구 배포에 남는다. 연결이 열려 있는 동안 함수 사용량이 과금된다.
- **실패 양상:** 300초/800초마다 모든 연결이 끊김(W-003), 인스턴스 메모리의 방·접속자 상태 불일치(W-001, W-004).
- **신호:** 🟢 Vercel 배포 + `ws`/`socket.io` · 🟢 `experimental_upgradeWebSocket` · 🔴 서버 메모리에 방 상태 저장
- **시나리오·수준:** 티어 0 유지 가능 조건: 재연결 처리 + 외부 상태 저장. 연결이 오래 유지돼야 하고 비용이 문제면 관리형 실시간 서비스 또는 티어 1
- **처방:** 티어 0: Redis(Marketplace)로 상태·Pub/Sub 외부화, 클라이언트 재연결 · 대안: Supabase Realtime, Pusher/Ably, Durable Objects
- **검증:** maxDuration 경과 시 재연결·재구독 성공
- **비용 영향:** 유휴 연결도 함수 시간 과금 → 연결 많고 메시지 드문 앱은 하이버네이션형(W-043)이 쌈
- **출처:** https://vercel.com/docs/functions/websockets, https://vercel.com/kb/guide/do-vercel-serverless-functions-support-websocket-connections

### W-055 Vercel 파일 디스크립터 1,024 공유와 DB 커넥션 풀
- **해당:** Vercel Functions(Fluid compute)에서 DB·HTTP 연결을 많이 여는 앱
- **무엇/왜:** 파일 디스크립터 1,024개를 한 인스턴스의 동시 실행 전체가 공유한다(런타임 사용분 포함). Fluid compute는 한 인스턴스가 여러 요청을 동시에 처리하므로 요청마다 DB 연결을 새로 열면 디스크립터와 DB `max_connections`가 동시에 고갈된다. 함수가 일시 정지되기 전에 유휴 풀 연결을 놓아주는 `attachDatabasePool`이 제공된다.
- **실패 양상:** "too many open files", DB "too many connections"(Postgres 기본 100, 설계 S8).
- **신호:** 🟢 `db.connect_per_request` · 🟢 `attachDatabasePool` 사용 여부 · 🟢 DB URL이 풀러(6543 포트, `pgbouncer=true`)인지
- **시나리오·수준:** T-PRE-003, T-CTL-003
- **처방:** 티어 0: 모듈 범위 풀 + `attachDatabasePool` + 트랜잭션 풀러(W-064)
- **검증:** 동시 요청 200에서 DB 연결 수 상한 유지
- **비용 영향:** 없음. DB 증설 회피
- **출처:** https://vercel.com/docs/functions/limitations (1,024 디스크립터 공유, 연결 풀 권장), https://vercel.com/docs/functions/functions-api-reference/vercel-functions-package (`attachDatabasePool`)

### W-056 Vercel 구 프로젝트(Fluid compute 아님)는 한도가 더 낮음
- **해당:** 2025-04-23 이전에 만든, Fluid compute를 켜지 않은 Vercel 프로젝트
- **무엇/왜:** 레거시 한도는 Hobby 기본 10초·최대 60초, Pro 기본 15초·최대 300초, Enterprise 최대 900초. 웹소켓·대형 함수도 Fluid compute가 필요하다. 저장소만 보고 신규 기준 한도를 적용하면 오판한다.
- **실패 양상:** "Vercel은 300초까지"라고 판정했는데 실제로는 10초 타임아웃.
- **신호:** 🟡 `vercel.json`의 `fluid` 설정, 프로젝트 생성일(저장소에서 확인 불가 → 미확인)
- **시나리오·수준:** TIER-001 판정 시 "Fluid 여부 미확인"이면 보수적으로 레거시 한도도 함께 표시
- **처방:** Fluid compute 활성화(설정 변경)
- **검증:** 대시보드 설정 확인(사용자 확인 항목)
- **비용 영향:** 과금 모델이 활성 CPU 기반으로 바뀜
- **출처:** https://vercel.com/docs/limits (레거시 기본·최대 실행 시간 표), https://vercel.com/docs/functions/websockets (Fluid compute 필요)

### 티어 0 — Netlify

### W-057 Netlify Functions 한도: 동기 60초·백그라운드 15분·스케줄 30초
- **해당:** Netlify Functions, Background Functions, Scheduled Functions
- **무엇/왜:** 동기 실행 60초, 스케줄 함수 30초, 백그라운드 함수 15분. 버퍼 페이로드 6MB(바이너리는 base64로 실효 약 4.5MB), 스트리밍 응답 20MB·60초, 백그라운드 페이로드 256KB. 메모리 기본 1024MB(1~4GB 조절은 크레딧 기반 Pro 이상). 기본 리전 `cmh`(오하이오), 리전 변경은 Pro 이상.
- **실패 양상:** LLM 스트리밍 60초에서 끊김(W-011), 30초 넘는 정기 작업 실패, 무료 플랜에서 한국 사용자 → 미국 함수 지연.
- **신호:** 🟢 `netlify.toml`, `netlify/functions/`, `-background` 접미사 파일, `schedule(` · 🔴 60초 넘는 동기 처리 경로
- **시나리오·수준:** TIER-001 Netlify 버전: 동기 > 60초 또는 스케줄 > 30초 → 해당 경로만 백그라운드/외부로, 상시 워커는 제외
- **처방:** 티어 0: 긴 작업은 백그라운드 함수(15분) + 결과 저장, 리전은 Pro에서 서울 인접 리전 · 불가 시 티어 1
- **검증:** 함수 설정 정적 분석
- **비용 영향:** 크레딧 소비(W-058)
- **출처:** https://docs.netlify.com/build/functions/configuration/, https://docs.netlify.com/build/functions/api/

### W-058 Netlify 크레딧 기반 요금
- **해당:** Netlify Free/Pro
- **무엇/왜:** Free는 월 300크레딧, Pro는 월 $20에 3,000크레딧. 컴퓨트 GB-시간당 10크레딧, 대역폭 GB당 20크레딧, 웹 요청 1만 건당 2크레딧. 크레딧 소진 시 동작(일시 중지 여부)은 가격 페이지에서 확인하지 못했다.
- **실패 양상:** 대역폭 비중이 큰 미디어 사이트는 크레딧이 빨리 소진.
- **신호:** 🟢 Netlify 배포 신호 + 대용량 정적 미디어
- **시나리오·수준:** 비용 산정 입력
- **처방:** 견적에 크레딧 환산 단가 사용, 미디어는 외부 스토리지·CDN(W-009)
- **검증:** 월 예상 대역폭 × 20크레딧
- **비용 영향:** 대역폭 GB당 약 $0.13(Pro 팩 환산)
- **출처:** https://www.netlify.com/pricing/

### 티어 0 — Cloudflare Workers/Pages

### W-059 Workers CPU 시간·메모리 한도
- **해당:** Cloudflare Workers, Pages Functions(같은 과금·한도)
- **무엇/왜:** CPU 시간 Free 요청당 10ms, Paid 기본 30초·최대 5분(벽시계 시간은 클라이언트 연결 중 제한 없음, 응답 후 `waitUntil` 30초). 메모리 isolate당 128MB. 워커 크기 64MiB. 서브요청 Free 50, Paid 10,000. 요청 본문은 Cloudflare 계정 플랜에 따라 Free/Pro 100MB.
- **실패 양상:** 비밀번호 해시(bcrypt), 이미지 처리, 큰 JSON 파싱이 Free 10ms를 넘어 오류. 128MB 메모리 초과.
- **신호:** 🟢 `wrangler.toml`/`wrangler.jsonc` · 🔴 `bcrypt`/`argon2`/`sharp`(`heavy.password_hash`, `heavy.image`) + Workers Free · 🟡 Node 전용 모듈(`fs`, 네이티브 애드온)
- **시나리오·수준:** 티어 0 Workers 제외 조건: 무거운 CPU 작업이 요청 경로에 있음(Free), 128MB 초과
- **처방:** Paid 플랜(CPU 한도 상향), 무거운 작업은 외부·큐
- **검증:** 로컬 `wrangler dev`로 CPU 시간 측정
- **비용 영향:** Paid 월 $5부터
- **출처:** https://developers.cloudflare.com/workers/platform/limits/, https://developers.cloudflare.com/workers/platform/pricing/

### W-060 Workers에서 기존 Postgres/MySQL 연결 → Hyperdrive
- **해당:** Workers에서 리전 DB(RDS, Cloud SQL, Supabase, Neon) 사용
- **무엇/왜:** Workers는 요청마다 짧게 실행되는 isolate라 요청마다 DB 연결을 열면 연결 수가 폭증하고 연결 설정 지연이 크다. Hyperdrive가 연결 풀링과 인기 쿼리 캐싱을 제공한다.
- **실패 양상:** DB "too many connections", 요청마다 수백 ms 연결 지연.
- **신호:** 🟢 `wrangler` 설정 + `pg`/`postgres`/`mysql2` · 🟢 `hyperdrive` 바인딩 유무
- **시나리오·수준:** T-PRE-003의 Workers 버전
- **처방:** 티어 0: Hyperdrive 바인딩, 또는 HTTP 기반 DB 드라이버
- **검증:** 동시 요청 시 DB 연결 수
- **비용 영향:** 소액
- **출처:** https://developers.cloudflare.com/hyperdrive/

### W-061 Workers의 웹소켓 → Durable Objects + 하이버네이션
- **해당:** Cloudflare에서 실시간 기능
- **무엇/왜:** 상태가 있는 웹소켓 조정은 Durable Objects로 한다. 하이버네이션 API를 쓰면 유휴 시 객체가 메모리에서 빠지고 연결은 유지되며, 그동안 Duration 과금이 없다. 아웃바운드 웹소켓은 동시 연결 6개 한도에 포함된다.
- **실패 양상:** 하이버네이션 없이 일반 웹소켓을 붙잡으면 유휴 연결에도 과금.
- **신호:** 🟢 `durable_objects` 바인딩, `acceptWebSocket`, `webSocketMessage`
- **시나리오·수준:** 실시간 도메인의 티어 0 후보
- **처방:** Hibernation API 사용, 연결별 데이터는 `serializeAttachment`(16KB)
- **검증:** 유휴 시간 중 Duration 지표 0
- **비용 영향:** DO Paid 월 100만 요청·40만 GB-s 포함, 초과 $0.15/백만 요청·$12.50/백만 GB-s
- **출처:** https://developers.cloudflare.com/durable-objects/best-practices/websockets/, https://developers.cloudflare.com/workers/platform/pricing/

### W-062 Workers 크론·큐 소비자 실행 시간
- **해당:** Cron Triggers, Queue Consumers
- **무엇/왜:** 크론 트리거 CPU는 Free 10ms, Paid는 1시간 미만 주기이면 30초, 1시간 이상 주기이면 15분. 크론·큐 소비자·DO 알람 벽시계 시간 15분.
- **실패 양상:** 5분마다 도는 크론 안에서 30초 넘는 집계 → 실패.
- **신호:** 🟢 `wrangler`의 `triggers.crons` 주기 + 핸들러 작업량
- **시나리오·수준:** W-018, TIER-001 Workers 버전
- **처방:** 작업 분할 + Queues로 팬아웃
- **검증:** 주기·예상 실행 시간 대조
- **비용 영향:** 없음
- **출처:** https://developers.cloudflare.com/workers/platform/limits/

### 티어 0 — Supabase

### W-063 Supabase Edge Functions 한도
- **해당:** Supabase Edge Functions
- **무엇/왜:** 벽시계 시간 Free 150초·유료 400초, 요청당 CPU 2초(비동기 I/O 제외), 메모리 256MB, 요청 유휴 타임아웃 150초(응답 시작 안 하면 504).
- **실패 양상:** 무거운 CPU 작업(2초) 초과, LLM 응답 첫 바이트가 150초 넘으면 504.
- **신호:** 🟢 `supabase/functions/*/index.ts`
- **시나리오·수준:** TIER-001 Supabase 버전
- **처방:** 무거운 작업은 DB 큐 + 외부 워커
- **검증:** 함수별 최대 처리 시간 측정
- **비용 영향:** 호출 수 기반
- **출처:** https://supabase.com/docs/guides/functions/limits

### W-064 Supabase DB 연결 방식: 직접(IPv6) vs 풀러(세션 5432·트랜잭션 6543)
- **해당:** Supabase Postgres에 서버리스·컨테이너에서 접속
- **무엇/왜:** 직접 연결(`db.<ref>.supabase.co:5432`)은 기본 IPv6라 IPv4만 되는 환경(일부 컨테이너 플랫폼, 사내망)에서 실패한다. IPv4 애드온을 켜면 IPv4 전용이 된다. 공유 풀러는 IPv4 전용이며 세션 모드(5432)와 트랜잭션 모드(6543)가 있다. 서버리스는 트랜잭션 모드 + 클라이언트 풀 1 + 준비된 문장 끄기(Prisma `pgbouncer=true`, postgres.js `prepare: false`)가 공식 권장이다.
- **실패 양상:** 배포 직후 "connect ENETUNREACH"(IPv6), 트랜잭션 모드에서 "prepared statement already exists" 오류.
- **신호:** 🟢 `DATABASE_URL` 호스트·포트(`:6543`, `pooler.supabase.com`), `pgbouncer=true`, `prepare: false` · 🔴 서버리스 + 직접 연결 5432
- **시나리오·수준:** T-PRE-003, T-CTL-003, 티어 이전 시(티어 1 컨테이너) 연결 방식 재설정
- **처방:** 서버리스: 6543 + 준비된 문장 끄기 · 상시 컨테이너: 직접 연결(IPv6 가능 시) 또는 세션 풀러
- **검증:** 대상 플랫폼에서 연결 테스트, 동시 요청 시 연결 수
- **비용 영향:** IPv4 애드온 유료(금액 미확인)
- **출처:** https://supabase.com/docs/guides/database/connecting-to-postgres

### W-065 Supabase Free: 1주 무활동 일시 중지, 백업 없음
- **해당:** Supabase Free 플랜
- **무엇/왜:** Free는 DB 500MB, egress 5GB, 스토리지 1GB, 활성 프로젝트 2개, **1주 무활동 시 일시 중지**, 백업 미포함. Pro는 월 $25부터, 일일 백업 7일 보관, PITR은 애드온(7일 보관당 월 $100), 무활동 중지 없음.
- **실패 양상:** 트래픽 적은 서비스가 주말 지나 접속 불가(사용자는 장애로 인식). 데이터 손상 시 복구 수단 없음 → D L1 미충족.
- **신호:** 🟢 `@supabase/supabase-js`, `supabase/config.toml` · 🟡 플랜은 저장소에서 확인 불가 → "미확인", 사용자 생성 데이터 있으면 Free 가정 시 D1 미충족으로 표시
- **시나리오·수준:** D≥1이면 Free 불충분(D-CTL-001 백업). D≥2(RPO 5분)이면 PITR 애드온 필요
- **처방:** D1: Pro(일일 백업) · D2: Pro + PITR · Multi-AZ 수준 HA 여부는 이 문서에서 확인 못 함
- **검증:** 백업 목록 확인(사용자 확인), 복원 리허설(P4)
- **비용 영향:** D1 = 월 $25~, D2 = +월 $100(PITR)
- **출처:** https://supabase.com/pricing

### W-066 Supabase Realtime 한도: 동시 연결 Free 200·Pro 500
- **해당:** Supabase Realtime(Broadcast, Presence, Postgres Changes)
- **무엇/왜:** 동시 연결 Free 200·Pro 500, 초당 메시지 Free 100·Pro 500, 초당 채널 참여 Free 100·Pro 500, Broadcast 페이로드 Free 256KB·Pro 3,000KB. 실시간·채팅 도메인의 평시 동시 연결 100 × 피크 ×3 = 300이면 Free는 이미 초과.
- **실패 양상:** 피크에 새 사용자 연결 거부, 메시지 지연.
- **신호:** 🟢 `supabase.channel(`, `.on('broadcast'`, `postgres_changes`
- **시나리오·수준:** T≥1 실시간 도메인에서 가정한 피크 연결 수와 비교하는 티어 규칙
- **처방:** 피크 연결 > 한도면 상위 플랜·한도 상향 요청 또는 별도 실시간 서비스
- **검증:** 가정 피크 연결 수로 부하
- **비용 영향:** 플랜 상향
- **출처:** https://supabase.com/docs/guides/realtime/limits

### 티어 0 — Firebase

### W-067 Cloud Functions for Firebase: Blaze 필수, 2세대 HTTP 60분
- **해당:** Firebase Functions
- **무엇/왜:** 함수를 배포하려면 종량제 Blaze 플랜이 필요하다. 2세대 HTTP 함수 최대 60분, 이벤트 함수 540초(1세대는 모두 540초). 요청 32MB(1세대 10MB), 응답 비스트리밍 32MB·스트리밍 10MB.
- **실패 양상:** 무료(Spark)로 시작한 프로젝트가 함수 추가 시 결제 등록 필요, 1세대 함수에서 9분 넘는 작업 실패.
- **신호:** 🟢 `firebase.json`, `functions/` + `firebase-functions` 버전(`v2/` import 여부)
- **시나리오·수준:** TIER-001 Firebase 버전, 비용 산정(Blaze 전제)
- **처방:** 2세대로 이전, 예산 알림 설정
- **검증:** import 경로 정적 분석(`firebase-functions/v2`)
- **비용 영향:** 종량제(무료 할당 후 과금)
- **출처:** https://firebase.google.com/docs/functions/quotas

### W-068 Firestore 무료 할당·문서 한도·벤더 종속
- **해당:** Cloud Firestore
- **무엇/왜:** 무료 할당은 하루 읽기 5만, 쓰기 2만, 삭제 2만, 저장 1GiB, 월 전송 10GiB. 문서 최대 1MiB, 트랜잭션 270초(유휴 60초). PITR·백업·복원은 결제 필요. 데이터 모델과 쿼리 API가 Firestore 고유라 다른 DB로의 이전 비용이 가장 크다(이전 비용은 우리 추론). ⚠️근거없음
- **실패 양상:** 피드 화면 하나가 문서 수십 개를 읽어 일일 읽기 할당을 오전에 소진, 카운터 문서 핫스팟(W-034).
- **신호:** 🟢 `firebase/firestore`, `firebase-admin` `firestore()` · 🟡 `onSnapshot` 다수 사용(읽기 과금 증가)
- **시나리오·수준:** D≥1이면 백업 기능 위해 결제 필요, 이전 비용 `large`
- **처방:** 유지 권고(TIER-005)가 기본. 읽기 비용 최적화(캐시·집계 문서)
- **검증:** 화면당 읽기 수 × 일일 사용자로 할당 대비
- **비용 영향:** 읽기 건수 비례
- **출처:** https://firebase.google.com/docs/firestore/quotas

### 티어 0 — Railway

### W-069 Railway HTTP 요청 15분·무전송 5분, 웹소켓 무기한
- **해당:** Railway 서비스 공개 네트워킹
- **무엇/왜:** HTTP 요청은 데이터가 계속 오가면 최대 15분, 5분간 전송이 없으면 닫힘. 요청 본문은 5분 안에 업로드를 끝내야 하고 헤더 합계 32KB. 웹소켓(HTTP/1.1)은 유휴여도 무기한 유지. 도메인당 동시 연결 1만, 약 초당 11,000 요청.
- **실패 양상:** 느린 모바일 회선의 대용량 업로드가 5분에서 실패, 5분 넘게 아무것도 안 보내는 긴 LLM 생각 단계에서 연결 종료.
- **신호:** 🟢 `railway.json`/`railway.toml`, `RAILWAY_` 환경변수
- **시나리오·수준:** TIER-002 Railway 버전(15분 초과 요청), 웹소켓 도메인에는 유리
- **처방:** 하트비트(W-005), 업로드는 서명 URL(W-006)
- **검증:** 설정·경로 정적 분석
- **비용 영향:** 없음
- **출처:** https://docs.railway.com/networking/public-networking/specs-and-limits

### W-070 Railway 요금·한도와 앱 슬리핑
- **해당:** Railway Free/Hobby/Pro
- **무엇/왜:** Trial $5 일회성, Free 월 $1 크레딧, Hobby 월 $5(사용량 $5 포함), Pro 월 $20(사용량 $20 포함). RAM GB당 월 $10, vCPU당 월 $20, egress GB당 $0.05, 볼륨 GB당 월 $0.15. 서비스당 레플리카 Free 1·Hobby 6·Pro 42, 볼륨 Free 0.5GB·Hobby 5GB·Pro 1TB. 서버리스(앱 슬리핑)를 켜면 아웃바운드 트래픽이 없을 때 5~10분 뒤 잠들고 첫 요청에 콜드 부트.
- **실패 양상:** Free 레플리카 1개 → D2(존 분산) 불가, 슬리핑으로 첫 요청 지연. 볼륨 상한으로 업로드 저장 실패.
- **신호:** 🟢 Railway 신호 + 볼륨 마운트 설정 · 🟡 레플리카 수 설정
- **시나리오·수준:** D≥2이면 Free 제외, T3(1분 램프)면 슬리핑 끔
- **처방:** 레플리카 ≥2(Hobby 이상), 슬리핑은 T≤1 저트래픽에서만
- **검증:** 설정 확인
- **비용 영향:** 상시 컨테이너 1개(0.5vCPU·512MB)는 약 월 $15 수준(단가로 계산한 우리 추정)
- **출처:** https://docs.railway.com/reference/pricing/plans, https://docs.railway.com/reference/app-sleeping

### 티어 0 — Render

### W-071 Render Free: 15분 유휴 스핀다운, Postgres 30일 만료
- **해당:** Render Free 인스턴스·Free Postgres·Free Key Value
- **무엇/왜:** Free 웹 서비스는 15분간 인바운드 트래픽이 없으면 내려가고, 다시 올라오는 데 약 1분. 워크스페이스당 월 750 인스턴스 시간, 소진 시 다음 달까지 정지. Free Postgres는 생성 30일 후 만료(14일 유예 후 삭제). Free Key Value는 디스크에 저장하지 않아 재시작 시 데이터 소실. Free 웹 서비스는 영속 디스크 불가, 사설 네트워크 트래픽 수신 불가.
- **실패 양상:** 첫 방문자 1분 대기(사실상 장애), 한 달 뒤 DB 삭제 → 데이터 전부 유실.
- **신호:** 🟢 `render.yaml`의 `plan: free`, `type: pserv`/`databases` 플랜
- **시나리오·수준:** D≥1이면 Free Postgres 제외(🔴), T≥1 공개 서비스면 Free 웹 비권장, Free Key Value를 세션 저장소로 쓰면 T-CTL-001 미충족
- **처방:** 유료 인스턴스·유료 Postgres
- **검증:** `render.yaml` 플랜 정적 분석
- **비용 영향:** 유료 최저 플랜 비용(금액은 이 문서에서 미확인)
- **출처:** https://render.com/docs/free ⚠️출처부적격

### W-072 Render 영속 디스크: 스케일 아웃 불가 + 무중단 배포 불가
- **해당:** Render 서비스에 Persistent Disk 연결
- **무엇/왜:** 디스크가 붙은 서비스는 인스턴스를 여러 개로 늘릴 수 없고, 배포 때 기존 인스턴스를 먼저 멈춰서 수 초 다운타임이 생긴다. 디스크는 빌드·사전 배포 명령·일회성 작업·크론에서 접근 불가. 일일 스냅샷 최소 7일 보관.
- **실패 양상:** 로컬 업로드·SQLite를 디스크로 "해결"하는 순간 T(오토스케일)와 U(무중단)를 동시에 포기.
- **신호:** 🟢 `render.yaml`의 `disk:` 블록 · 🟢 `db.sqlite_file`, `state.upload.local_fs`
- **시나리오·수준:** T≥1 또는 U≥1이면 "디스크 의존" 구성 부족 판정, D-PRE-001/002 처방 우선
- **처방:** 오브젝트 스토리지·매니지드 DB로 이전 후 디스크 제거
- **검증:** 디스크 제거 후 인스턴스 2개 + 무중단 배포 확인
- **비용 영향:** 매니지드 DB 비용 추가, 대신 확장 가능
- **출처:** https://render.com/docs/disks ⚠️출처부적격

### W-073 Render 웹소켓과 종료 유예
- **해당:** Render 웹 서비스의 웹소켓
- **무엇/왜:** 웹소켓 고정 타임아웃은 없지만 인스턴스 교체(배포) 때 닫힌다. 교체 시 SIGTERM 후 기본 30초, 최대 300초까지 늘릴 수 있는 종료 유예. 관리형 PaaS 중 유예 상한이 긴 편이다.
- **실패 양상:** 배포마다 전원 재연결(W-003).
- **신호:** 🟢 Render + 웹소켓 의존성
- **시나리오·수준:** U≥1 실시간 도메인
- **처방:** 유예 시간 상향 + 서버 측 정리 메시지 + 클라이언트 백오프
- **검증:** 배포 중 재연결 완료 시간
- **비용 영향:** 없음
- **출처:** https://render.com/docs/websocket, https://render.com/docs/web-services (웹소켓·무중단 배포 지원) ⚠️출처부적격

### 티어 0 — Fly.io

### W-074 Fly 볼륨은 한 물리 서버에 묶이고 복제되지 않음
- **해당:** Fly Machines + Fly Volumes(직접 운영 DB, SQLite, 업로드 저장)
- **무엇/왜:** 볼륨은 머신이 올라간 물리 서버의 NVMe 일부이며 그 하드웨어에 묶인다. Fly는 볼륨 간 데이터를 자동 복제하지 않는다. 일일 스냅샷 기본 5일(1~60일 설정)이지만 최신 데이터가 없을 수 있어 자체 백업을 권장한다. 앱당 볼륨 최소 2개를 권장한다.
- **실패 양상:** 호스트 하드웨어 고장 → 볼륨 위 SQLite·업로드 유실, 마지막 스냅샷 이후 데이터 손실(RPO 최대 24시간).
- **신호:** 🟢 `fly.toml`의 `[mounts]` · 🟢 `db.sqlite_file` + Fly · 🔴 볼륨 1개 + 사용자 데이터
- **시나리오·수준:** D≥1: 스냅샷만으로는 RPO 24시간 수준(D1 경계). D≥2: 볼륨 위 단일 DB 불가 → 매니지드 Postgres 또는 복제 구성
- **처방:** 매니지드 Postgres 이전(D-PRE-001) 또는 LiteFS류 복제 + 외부 백업
- **검증:** 머신 파괴 후 복원 리허설
- **비용 영향:** 볼륨 GB당 월 $0.15, 스냅샷 GB당 월 $0.08(월 10GB 무료)
- **출처:** https://docs.fly.io/volumes/overview/, https://docs.fly.io/about/pricing/ ⚠️출처부적격

### W-075 Fly 자동 정지·시작과 최소 머신
- **해당:** Fly Machines `auto_stop_machines`, `min_machines_running`
- **무엇/왜:** 프록시가 유휴 머신을 stop 또는 suspend(더 빠른 재개)하고 요청이 오면 자동 시작한다. `min_machines_running`은 주 리전에서 유지할 최소 머신 수다. 정지된 머신은 rootfs GB당 30일 $0.15만 과금된다. shared-cpu-1x 256MB는 애시번 기준 시간당 약 $0.00205(월 약 $1.49).
- **실패 양상:** T3 1분 램프에서 정지 머신 기동 지연, 두 설정 중 하나만 켜서 머신이 영원히 꺼지거나 영원히 켜짐.
- **신호:** 🟢 `fly.toml`의 `auto_stop_machines`, `auto_start_machines`, `min_machines_running`
- **시나리오·수준:** TIER-003의 Fly 버전: T3이면 `min_machines_running` ≥ 평시 필요 대수
- **처방:** 두 설정을 함께 켜고/끄기, T3이면 최소 머신 상향
- **검증:** 스파이크 테스트에서 첫 요청 지연
- **비용 영향:** 최소 머신 상시 비용
- **출처:** https://docs.fly.io/launch/autostop-autostart/, https://docs.fly.io/about/pricing/ ⚠️출처부적격

### 티어 0 — Replit

### W-076 Replit 배포 유형과 파일 시스템 비영속
- **해당:** Replit Deployments (Autoscale, Reserved VM, Static, Scheduled)
- **무엇/왜:** Autoscale은 사용량에 따라 자원을 늘리고 줄인다(유휴 축소 → 콜드 스타트). 상시 실행이 필요한 웹소켓·백그라운드 워커는 Reserved VM. 정기 작업은 Scheduled. 배포된 앱의 파일 시스템에 쓴 데이터에 의존하지 말라고 공식 문서가 경고한다. 바이브코딩 저장소에서 SQLite·로컬 업로드가 흔한 곳이다.
- **실패 양상:** 재배포·축소 후 업로드 파일·SQLite 데이터 소실.
- **신호:** 🟢 `.replit`, `replit.nix`, `[deployment]` 섹션의 `deploymentTarget` · 🔴 `db.sqlite_file`/`state.upload.local_fs` + Replit
- **시나리오·수준:** D≥1이면 로컬 파일 데이터 → D-PRE-001/002 필수, 웹소켓·워커면 Autoscale 제외
- **처방:** 외부 DB·스토리지, 상시 연결은 Reserved VM
- **검증:** 재배포 후 데이터 유지
- **비용 영향:** Reserved VM은 상시 비용(금액 미확인)
- **출처:** https://docs.replit.com/cloud-services/deployments/about-deployments ⚠️출처부적격

### 티어 1 — Google Cloud Run

### W-077 Cloud Run 요청 한도·과금 모드·세션 어피니티
- **해당:** Cloud Run 서비스
- **무엇/왜:** 요청 타임아웃 기본 300초·최대 3600초(15분 초과 시 재시도·재연결 내성 권장), 웹소켓도 요청 타임아웃 적용. HTTP/1 요청·응답 최대 32MiB(HTTP/2는 요청 크기 상한 미표기). 인스턴스당 동시 요청 최대 1000, 메모리 최대 32GiB, vCPU 최대 8, 쓰기 가능한 인메모리 파일 시스템(디스크 쓰기가 메모리를 먹음), 컨테이너 기동 타임아웃 4분. 요청 기반 과금(기본)은 요청 처리 중에만 CPU, 인스턴스 기반 과금은 수명 내내(최소 512MiB). 활성 웹소켓 연결이 있으면 인스턴스 기반으로 과금된다. 세션 어피니티는 쿠키(30일 TTL) 기반 best effort.
- **실패 양상:** /tmp에 큰 파일을 쓰다 메모리 초과로 인스턴스 종료, 응답 후 백그라운드 작업 정지(W-017), 60분 넘는 연결 끊김.
- **신호:** 🟢 `service.yaml`/Terraform `google_cloud_run_v2_service`의 `timeout`, `max_instance_request_concurrency`, `cpu_idle`, `session_affinity`, `min_instance_count` · 🟡 `/tmp` 대량 쓰기
- **시나리오·수준:** TIER-002(60분), TIER-003(최소 인스턴스), W-017(과금 모드)
- **처방:** 긴 작업 → Cloud Run Jobs(W-079), 백그라운드 → 인스턴스 기반 과금 또는 Cloud Tasks, 대용량 → 서명 URL
- **검증:** 설정 정적 분석 + 부하 중 인스턴스 메모리
- **비용 영향:** 인스턴스 기반 과금은 유휴 시간도 과금
- **출처:** https://docs.cloud.google.com/run/docs/configuring/request-timeout, https://docs.cloud.google.com/run/quotas, https://docs.cloud.google.com/run/docs/configuring/billing-settings, https://docs.cloud.google.com/run/docs/triggering/websockets, https://docs.cloud.google.com/run/docs/configuring/session-affinity

### W-078 Cloud Run GPU는 서울 리전에 없음
- **해당:** Cloud Run GPU(자체 모델 추론) ⚠️근거없음
- **무엇/왜:** L4·RTX PRO 6000 Blackwell 제공 리전 목록에 서울(`asia-northeast3`)이 없다(가까운 곳은 싱가포르). GPU는 인스턴스 기반 과금 필수, 0으로 축소는 가능, 최소 인스턴스는 전액 과금. 존 중복 옵션은 기본이 용량 예약(비쌈).
- **실패 양상:** 서울 기본 리전으로 Terraform 적용 시 실패, 또는 앱은 서울·GPU는 싱가포르로 분리되어 지연·전송비.
- **신호:** W-014 신호 + 리전 추론 결과가 서울
- **시나리오·수준:** 티어 1 GCP 제외 또는 리전 분리 조건
- **처방:** GPU 서비스만 싱가포르 등 가능 리전, 또는 외부 추론 API · 존 중복은 D≥2일 때만
- **검증:** 리전·GPU 조합 사전 검증
- **비용 영향:** 존 중복 끄면 저렴, 대신 best-effort 페일오버
- **출처:** https://docs.cloud.google.com/run/docs/configuring/services/gpu

### W-079 Cloud Run Jobs로 배치 분리 (최대 168시간)
- **해당:** 배치, 마이그레이션, 대량 처리
- **무엇/왜:** 서비스(요청 60분 상한)와 달리 Jobs는 태스크 최대 168시간(GPU는 1시간), 실행당 태스크 최대 1만, 재시도 최대 10회, 항상 인스턴스 기반 과금. 마이그레이션 작업 분리(U-CTL-004)의 자연스러운 자리.
- **실패 양상:** 배치를 서비스 엔드포인트로 호출해 60분에서 끊김.
- **신호:** 🟢 `process.worker`/`process.cron` + Cloud Run 대상 · 🟢 `google_cloud_run_v2_job`
- **시나리오·수준:** U-CTL-004, W-013, W-020
- **처방:** Cloud Scheduler → Cloud Run Jobs, 태스크 인덱스로 분할
- **검증:** 작업 실행 기록
- **비용 영향:** 실행 시간만 과금
- **출처:** https://docs.cloud.google.com/run/quotas, https://docs.cloud.google.com/run/docs/configuring/billing-settings (Jobs는 인스턴스 기반 과금)

### 티어 1 — AWS ECS Fargate / App Runner

### W-080 ECS Fargate + ALB: 유휴 타임아웃 60초, 종료 유예 최대 120초, 임시 저장소
- **해당:** ECS on Fargate 서비스 + Application Load Balancer
- **무엇/왜:** ALB 연결 유휴 타임아웃 기본 60초(1~4000초), 앱의 keep-alive 타임아웃은 ALB보다 길게 해야 502를 피한다. HTTP/2 PING은 유휴 타이머를 리셋하지 않는다. 컨테이너 `stopTimeout` 기본 30초·최대 120초. 태스크 임시 저장소 기본 20GiB·최대 200GiB(이미지 포함, 비영속). Cloud Run과 달리 상시 실행이라 응답 후 백그라운드 작업이 동작한다.
- **실패 양상:** Node 기본 `keepAliveTimeout`(5초) < ALB 60초 → 간헐적 502. SSE·LLM 스트림이 60초 무응답에서 끊김. 2분 넘는 정리 작업 강제 종료.
- **신호:** 🟢 Terraform `aws_lb` `idle_timeout`, `aws_ecs_task_definition`의 `stopTimeout`, `ephemeral_storage` · 🟡 `server.keepAliveTimeout` 설정 부재(Node), gunicorn `--keep-alive`
- **시나리오·수준:** U-CTL-002, U-CTL-006, W-005
- **처방:** 앱 keep-alive > ALB 유휴 타임아웃, 스트리밍 경로는 하트비트 또는 유휴 타임아웃 상향, 장기 정리는 120초 내 분할
- **검증:** 부하 중 502 비율, 설정 정적 분석
- **비용 영향:** 없음
- **출처:** https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-load-balancer-attributes.html, https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definition_parameters.html, https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-task-storage.html

### W-081 App Runner는 신규 고객에게 닫힘 → 후보에서 제외
- **해당:** AWS App Runner
- **무엇/왜:** AWS는 App Runner를 신규 고객에게 닫았다. 기존 고객은 계속 쓰고 새 서비스도 만들 수 있지만 새 기능 계획은 없다. 이전 대상으로 ECS Express Mode를 권장하고 Route 53 가중치 기반 이전 가이드를 제공한다. 또한 AWS HIPAA 대상 서비스 목록에서 App Runner를 확인하지 못했다(W-041).
- **실패 양상:** 신규 계정에 App Runner 처방 → 생성 불가.
- **신호:** 🟢 Terraform `aws_apprunner_service`, `apprunner.yaml`
- **시나리오·수준:** 티어 규칙: 신규 구성 후보에서 App Runner 제외. 기존 사용 중이면 TIER-005로 유지하되 "신규 기능 없음" 경고와 이전 경로 표시
- **처방:** 신규: ECS Express Mode(W-082) · 기존: 유지 + 장기 이전 계획
- **검증:** 해당 없음(정책)
- **비용 영향:** ECS Express Mode는 ALB 고정비 발생
- **출처:** https://docs.aws.amazon.com/apprunner/latest/dg/apprunner-availability-change.html

### W-082 ECS Express Mode: 티어 1 AWS의 기본 경로
- **해당:** Amazon ECS Express Mode
- **무엇/왜:** 이미지와 IAM 역할 2개로 API 한 번 호출하면 Fargate 서비스, ALB, 오토스케일, 네트워킹을 계정 안에 만들어 준다. Express Mode 자체 추가 요금은 없고 생성된 자원만 과금. 자원이 사용자 계정에 남아 이후 세부 조정(서킷 브레이커 등 U-CTL-007)이 가능하다. GitHub Actions 배포 액션이 있다.
- **실패 양상:** 해당 없음. 단 ALB 고정비가 저트래픽 앱에는 상대적으로 큼.
- **신호:** 🟢 `create-express-gateway-service`, `amazon-ecs-deploy-express-service` 액션
- **시나리오·수준:** 티어 1 AWS 후보 정의(P3 실행기 대상)
- **처방:** P3 티어 1 AWS 산출물을 Express Mode 기준으로 생성하는 안 검토
- **검증:** 생성된 서비스의 최소·최대 태스크, 헬스 체크 경로
- **비용 영향:** Fargate + ALB 시간당 요금 + LCU
- **출처:** https://docs.aws.amazon.com/apprunner/latest/dg/apprunner-availability-change.html (Express Mode 설명과 요금 언급)

### 티어 1 — Azure Container Apps

### W-083 Azure Container Apps: 요청 타임아웃 240초, 무료 할당, 유휴 요율
- **해당:** Azure Container Apps (Consumption 플랜)
- **무엇/왜:** HTTP 인그레스 요청 타임아웃 240초(웹소켓·gRPC 지원, 세션 어피니티 지원, 리비전 간 트래픽 분할 내장). 구독당 월 18만 vCPU-초, 36만 GiB-초, HTTP 요청 200만 건 무료. 0으로 축소 시 과금 없음. 최소 레플리카 > 0이면 조건(요청 없음, CPU 0.01 미만, 네트워크 1,000B/s 미만)을 만족할 때 유휴 요율. 내부 전용 환경으로 사내 도구에 적합(W-039).
- **실패 양상:** 240초 넘는 LLM·리포트 요청 실패(W-011).
- **신호:** 🟢 Bicep/Terraform `azurerm_container_app`, `containerapp.yaml`
- **시나리오·수준:** TIER-002 ACA 버전: 처리 시간 > 240초 경로 → 비동기화 또는 제외
- **처방:** 긴 작업은 ACA Jobs, 카나리는 트래픽 분할(U-CTL-008)
- **검증:** 경로별 최대 처리 시간
- **비용 영향:** 무료 할당이 Cloud Run 요청 기반 무료 등급(S21)과 같은 규모
- **출처:** https://learn.microsoft.com/en-us/azure/container-apps/ingress-overview, https://learn.microsoft.com/en-us/azure/container-apps/billing

### 티어 2 — GKE / EKS

### W-084 GKE Autopilot: Pod 단위 과금과 워크로드 제약
- **해당:** GKE Autopilot
- **무엇/왜:** 일반 워크로드는 Pod가 요청한 자원 기준 과금이라 requests 과대 설정이 곧 비용(COST-006). 특권 Pod는 허용 목록 필요, DaemonSet 제한적 지원, 노드 직접 접근 불가, 리소스 요청은 정해진 범위. 클러스터는 기본 리전 단위(존 분산 D-CTL-003 유리), 워크로드가 없으면 노드 0까지 축소.
- **실패 양상:** 관측 에이전트 DaemonSet·특권 사이드카가 거부됨, 요청을 크게 잡아 비용 과다.
- **신호:** 🟢 Terraform `enable_autopilot = true` · 🔴 매니페스트에 `privileged: true`, `hostPath`, 커스텀 DaemonSet
- **시나리오·수준:** 티어 2 GCP 기본 후보(TIER-004 통과 시), 특권 요구가 있으면 Standard
- **처방:** requests를 P4 실측으로 조정, 특권 요구 제거
- **검증:** 매니페스트 검증(드라이런)
- **비용 영향:** 무료 등급 크레딧(S5)은 존 클러스터·Autopilot만
- **출처:** https://docs.cloud.google.com/kubernetes-engine/docs/concepts/autopilot-overview, 설계 S5·S24

### W-085 EKS 버전 연장 지원 요금 6배
- **해당:** Amazon EKS
- **무엇/왜:** 클러스터 요금은 표준 지원(릴리스 후 14개월) 시간당 $0.10, 이후 12개월 연장 지원은 시간당 $0.60. 업그레이드를 미루면 컨트롤 플레인 비용이 월 약 $73 → 약 $438로 뛴다(시간당 요금 × 730시간, 우리 계산).
- **실패 양상:** "아무것도 안 바꿨는데" 청구 증가, 소규모 앱에 과도한 고정비.
- **신호:** 🟢 Terraform `aws_eks_cluster`의 `version`, `upgrade_policy`
- **시나리오·수준:** COST 규칙 후보: EKS 버전이 표준 지원 밖이면 비용 경고 + 업그레이드 처방
- **처방:** 정기 업그레이드, 또는 T≤1·D≤1이면 티어 1로 하향(COST-001)
- **검증:** 버전과 지원 종료일 대조
- **비용 영향:** 클러스터당 월 약 $365 차이
- **출처:** https://aws.amazon.com/eks/pricing/

### W-086 EKS Auto Mode: 노드 최대 21일 수명, SSH 불가, 관리 수수료
- **해당:** EKS Auto Mode
- **무엇/왜:** 컴퓨트 오토스케일(Karpenter 기반), 로드밸런싱, EBS CSI, Pod 네트워킹·네트워크 정책, GPU 플러그인을 AWS가 관리한다. 노드는 최대 21일 수명 후 자동 교체되고(줄일 수 있음), SSH·SSM 접근이 막힌 불변 AMI(Bottlerocket). EC2 비용에 관리 수수료가 추가된다. PDB를 존중하지만 21일 한도에서는 막는 PDB가 개입을 요구할 수 있다.
- **실패 양상:** 장기 실행 작업·웹소켓이 노드 교체로 주기적 중단, PDB가 너무 엄격하면 업그레이드 정체.
- **신호:** 🟢 Terraform `compute_config { enabled = true }`(EKS Auto Mode) · 🟡 `minAvailable`이 레플리카 수와 같은 PDB
- **시나리오·수준:** 티어 2 AWS 후보, W-020과 결합(장기 작업 체크포인트 필수)
- **처방:** PDB는 `maxUnavailable: 1` 류로, 장기 작업은 체크포인트
- **검증:** 노드 교체 시뮬레이션(drain) 중 오류율
- **비용 영향:** EC2 + 관리 수수료(인스턴스 유형별)
- **출처:** https://docs.aws.amazon.com/eks/latest/userguide/automode.html, https://aws.amazon.com/eks/pricing/

### W-087 Karpenter 통합(consolidation)과 장기 실행 워크로드
- **해당:** EKS + Karpenter(자체 설치 또는 Auto Mode)
- **무엇/왜:** 기본 정책 `WhenEmptyOrUnderutilized`는 활용도가 낮은 노드를 적극 정리해 비용을 줄이지만 그 위의 Pod를 옮긴다. `karpenter.sh/do-not-disrupt` 어노테이션(영구 또는 기간)으로 보호할 수 있으나 만료(`expireAfter` 기본 720h)·중단·노드 수리·수동 삭제는 막지 못한다. 한 노드의 Pod들이 서로 다른 PDB에 속하면 모든 PDB가 동시에 허용해야 정리된다.
- **실패 양상:** 웹소켓 서버·배치가 통합 때마다 이동(W-003), 엄격한 PDB 하나 때문에 노드가 영원히 정리되지 않아 비용 누수.
- **신호:** 🟢 `NodePool`의 `disruption.consolidationPolicy`, `expireAfter`, `budgets` · 🟢 Pod 어노테이션
- **시나리오·수준:** T-CTL-009(빠른 노드 프로비저닝 수단), U-CTL-005, COST
- **처방:** 상태 연결·배치 워크로드는 별도 NodePool(`WhenEmpty`) 또는 `do-not-disrupt` 기간 지정 + `terminationGracePeriod`
- **검증:** 통합 이벤트 중 연결 끊김 수, 미정리 노드 수
- **비용 영향:** 통합이 주된 절감 수단 → 끄지 말고 워크로드별로 분리
- **출처:** https://karpenter.sh/docs/concepts/disruption/

### 플랫폼 교차 비교

### W-088 플랫폼별 종료 유예 시간 비교 (U-CTL-002 입력)
- **해당:** 모든 티어
- **무엇/왜:** SIGTERM 후 강제 종료까지의 시간이 플랫폼마다 다르다. 앱의 "진행 중 요청 마무리 + 연결 정리" 시간이 이 값보다 길면 무중단 배포가 깨진다.
  - Cloud Run: 10초 (설계 S3)
  - Kubernetes: 기본 30초(`terminationGracePeriodSeconds`로 조정, 설계 S6)
  - ECS: `stopTimeout` 기본 30초, 최대 120초
  - Render: 기본 30초, 최대 300초
  - Next.js 권장 드레인: 10~30초
- **실패 양상:** Cloud Run에서 20초 걸리는 정리 → 매 배포 진행 중 요청 실패.
- **신호:** 🟢 `ops.sigterm_handler` + 핸들러 안 대기 시간 상수 · 🟢 플랫폼 설정 값
- **시나리오·수준:** U≥1, 티어 비교 시 "필요 유예 > 플랫폼 상한"이면 경고
- **처방:** 정리 시간을 상한 아래로, 장기 작업은 W-020
- **검증:** 부하 중 롤링 배포 5xx 0건(P4 U L2)
- **비용 영향:** 없음
- **출처:** https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definition_parameters.html, https://render.com/docs/websocket, https://nextjs.org/docs/app/guides/self-hosting, 설계 S3·S6

### W-089 플랫폼별 요청 본문 한도 비교 (TIER-001 일반화)
- **해당:** 업로드·대용량 API가 앱을 통과하는 경우
- **무엇/왜:** 
  - Vercel Functions: 요청·응답 4.5MB
  - Netlify Functions: 버퍼 6MB(바이너리 실효 약 4.5MB), 백그라운드 256KB
  - Cloud Run: HTTP/1 32MiB (HTTP/2는 상한 미표기)
  - Firebase Functions 2세대: 요청 32MB
  - Cloudflare Workers: 계정 플랜 Free/Pro 100MB, Business 200MB
  - Railway: 크기 대신 "5분 안에 업로드 완료"
- **실패 양상:** 413 또는 연결 종료.
- **신호:** 🟢 업로드 미들웨어의 `limits.fileSize`/`bodyParser` 한도 상수 · 🟢 `MAX_UPLOAD_SIZE` 류 환경변수
- **시나리오·수준:** TIER-001을 "앱 최대 본문 > 플랫폼 한도 → 서명 URL 처방 또는 제외"로 일반화
- **처방:** W-006
- **검증:** 한도 상수 vs 표
- **비용 영향:** 없음
- **출처:** https://vercel.com/docs/functions/limitations, https://docs.netlify.com/build/functions/configuration/, https://docs.cloud.google.com/run/quotas, https://firebase.google.com/docs/functions/quotas, https://developers.cloudflare.com/workers/platform/limits/, https://docs.railway.com/networking/public-networking/specs-and-limits

### W-090 플랫폼별 최대 요청 처리 시간 비교 (TIER-002 일반화)
- **해당:** 긴 동기 요청(LLM, 리포트, 내보내기)
- **무엇/왜:** 
  - Vercel: Hobby 300초, Pro 800초(1800초 베타), Edge 25초 내 응답 시작
  - Netlify: 동기 60초, 스트리밍 60초, 백그라운드 15분
  - Supabase Edge: Free 150초, 유료 400초(유휴 150초)
  - Cloudflare Workers: 벽시계 무제한(연결 유지 시), CPU Paid 최대 5분
  - Firebase 2세대 HTTP: 60분
  - Railway: 15분(무전송 5분)
  - Azure Container Apps: 240초
  - Cloud Run: 기본 300초, 최대 3600초
  - ECS + ALB: ALB 유휴 60초 기본(데이터가 흐르면 유지), 최대 4000초
- **실패 양상:** 504/연결 종료.
- **신호:** 🟢 `maxDuration`, `timeout` 설정 · 🟡 LLM 에이전트 루프, 대량 내보내기
- **시나리오·수준:** TIER-002를 플랫폼별 수치 표로 확장
- **처방:** W-011, W-013
- **검증:** 경로별 p99 처리 시간 vs 표
- **비용 영향:** 없음
- **출처:** https://vercel.com/docs/functions/limitations, https://docs.netlify.com/build/functions/configuration/, https://supabase.com/docs/guides/functions/limits, https://developers.cloudflare.com/workers/platform/limits/, https://firebase.google.com/docs/functions/quotas, https://docs.railway.com/networking/public-networking/specs-and-limits, https://learn.microsoft.com/en-us/azure/container-apps/ingress-overview, https://docs.cloud.google.com/run/docs/configuring/request-timeout, https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-load-balancer-attributes.html

### W-091 "장애처럼 보이는" 무료 플랜 동작
- **해당:** 티어 0 무료·저가 플랜 전반
- **무엇/왜:** 무료 플랜의 비용 절감 장치가 사용자에게는 장애로 보인다: Render Free 15분 유휴 스핀다운(약 1분 기동)·월 750시간 소진 시 정지, Supabase Free 1주 무활동 일시 중지, Render Free Postgres 30일 만료, Railway 슬리핑, Vercel Hobby 상업 사용 금지, Firestore 일일 할당 소진.
- **실패 양상:** D·T 수준 요구와 정면 충돌. 리포트에 "$0"으로 나오지만 실제로는 요구 수준 미달.
- **신호:** 🟡 플랜은 대부분 저장소에 없음(`render.yaml`의 `plan:` 정도만 확인 가능) → "미확인"으로 표시하고 무료 가정 시 영향 표시
- **시나리오·수준:** 규칙 후보: D≥1 또는 T≥1(공개 서비스)이면 위 무료 플랜은 "필요 수준 미충족"으로 판정, 견적은 최저 유료 플랜부터
- **처방:** 최저 유료 플랜으로 견적
- **검증:** 사용자 확인 항목
- **비용 영향:** 견적 하한 상승(정직한 견적)
- **출처:** https://render.com/docs/free, https://supabase.com/pricing, https://docs.railway.com/reference/app-sleeping, https://vercel.com/docs/limits/fair-use-guidelines, https://firebase.google.com/docs/firestore/quotas

### W-092 서울 리전 가용성
- **해당:** 리전 추론이 서울(§4.3 기본)인 경우
- **무엇/왜:** 서울에서 실행 가능한지가 플랫폼마다 다르다. 확인된 것: Vercel `icn1` 있음(설정 필요, 기본 `iad1`), Netlify Functions 기본 `cmh`(오하이오)이고 리전 변경은 Pro 이상(서울 제공 여부는 미확인), Cloud Run GPU는 서울 없음, Fly·Railway·Render의 서울 리전 여부는 이번에 확인하지 못했다. 서울 DB + 미국 함수 조합은 W-053의 지연 문제를 만든다.
- **실패 양상:** 데이터 위치 요구(W-041) 위반, 지연 증가.
- **신호:** 🟢 플랫폼 설정의 리전 값 · 🟢 DB 접속 문자열 리전
- **시나리오·수준:** 티어 규칙 후보: "앱·DB 리전 불일치" 경고, 데이터 위치 요구 시 서울 불가 플랫폼 제외
- **처방:** 앱과 DB 리전 일치
- **검증:** 설정 정적 분석
- **비용 영향:** 리전별 단가 차이
- **출처:** https://vercel.com/docs/regions, https://docs.netlify.com/build/functions/configuration/, https://docs.cloud.google.com/run/docs/configuring/services/gpu. Fly·Railway·Render 서울 여부는 출처 미확인 ⚠️근거없음

### W-093 벤더 종속과 이전 경로 (migration_effort 산정)
- **해당:** 티어 0 → 1 → 2 이전 비용 계산
- **무엇/왜:** 이전 비용(§5 `migration_effort`)은 "고유 API 사용량"으로 추정할 수 있다. 공식 문서 근거가 있는 이전 경로: App Runner → ECS Express Mode(DNS 가중치 이전 가이드), Next.js on Vercel → 자체 호스팅(공유 캐시·암호화 키·deploymentId 필요, W-038), Supabase는 표준 Postgres 접속을 제공(W-064)해 DB 이전이 상대적으로 쉬움. Firestore 데이터 모델, Workers 런타임 API(Durable Objects, KV), Vercel 고유 API(`@vercel/functions`, `experimental_upgradeWebSocket`)는 이전 시 코드 수정이 필요하다(난이도 등급은 우리 추론). ⚠️근거없음
- **실패 양상:** 절감액보다 이전 비용이 더 큰데 이전 처방.
- **신호:** 🟢 고유 SDK import 수: `firebase/firestore`, `@vercel/functions`, `@vercel/kv`, `@vercel/blob`, `cloudflare:workers`, `__STATIC_CONTENT`, Supabase `rpc(`/RLS 정책 수
- **시나리오·수준:** TIER-005(유지 vs 교체)의 이전 비용 입력
- **처방:** 고유 API 호출 지점 수로 `none/small/medium/large` 등급: 0곳 none, 1~5곳 small, 6~20곳 medium, 그 이상 또는 데이터 모델 변경 large(임계값은 제안)
- **검증:** 픽스처 F4(`small-blog`)에서 `none`/`small` 판정 확인
- **비용 영향:** 이전 인건비를 판정에 포함(원칙 6)
- **출처:** https://docs.aws.amazon.com/apprunner/latest/dg/apprunner-availability-change.html, https://nextjs.org/docs/app/guides/self-hosting, https://supabase.com/docs/guides/database/connecting-to-postgres. 등급 임계값은 설계 원칙 6(§2) 기반 제안

---

## 플랫폼 한도 요약표

2026-10-01 확인값. 빈칸은 이번에 확인하지 못한 값.

| 플랫폼 | 최대 요청 시간 | 요청 본문 | 웹소켓 | 응답 후 백그라운드 | 상시 워커 | 영속 디스크 | DB 연결 권장 | 무료/저가 함정 |
|---|---|---|---|---|---|---|---|---|
| Vercel | Hobby 300초, Pro 800초(1800 베타) | 4.5MB | 베타, maxDuration까지 | `waitUntil`/`after` (함수 시간 내) | 불가 | 없음 | 모듈 풀 + `attachDatabasePool` + 풀러 | Hobby 비상업, 크론 일 1회 |
| Netlify | 동기 60초, 백그라운드 15분 | 6MB(바이너리 약 4.5MB) | | 백그라운드 함수 | 불가 | 없음 | | 크레딧 300/월(Free) |
| Cloudflare Workers | 벽시계 무제한, CPU Free 10ms·Paid 5분 | 100MB(Free/Pro 계정) | Durable Objects | `waitUntil` 30초 | 불가(DO 알람·큐로 대체) | 없음(KV/D1/R2) | Hyperdrive | Free 일 10만 요청 |
| Supabase Edge | Free 150초, 유료 400초 | | (Realtime 별도) | 벽시계 시간 내 | 불가 | 없음 | 트랜잭션 풀러 6543 | Free 1주 무활동 중지, 백업 없음 |
| Firebase Functions 2세대 | HTTP 60분, 이벤트 540초 | 32MB | | | 불가 | 없음 | | Blaze 필수 |
| Railway | 15분(무전송 5분) | 5분 내 업로드 | 무기한 | 가능 | 가능 | 볼륨(Free 0.5GB) | | Free 레플리카 1, 슬리핑 |
| Render | | | 지원(배포 시 끊김) | 가능 | 가능(유료) | 유료, 붙이면 스케일 아웃·무중단 불가 | | Free 15분 스핀다운, Postgres 30일 만료 |
| Fly.io | | | 지원 | 가능 | 가능 | 볼륨(단일 호스트, 복제 없음) | | 자동 정지 시 콜드 스타트 |
| Replit | | | Reserved VM | Reserved VM | Reserved VM | 비영속 | | Autoscale 축소 |
| Cloud Run | 기본 300초, 최대 3600초 | HTTP/1 32MiB | 지원(타임아웃 적용, 인스턴스 과금) | 인스턴스 기반 과금 필요 | 인스턴스 기반 과금 / Jobs | 없음(인메모리 FS) | 풀러 또는 커넥터 | 요청 기반 무료 등급(S21) |
| ECS Fargate | ALB 유휴 60초(최대 4000초) | | 지원 | 가능 | 가능 | 임시 20~200GiB(비영속), EFS | RDS Proxy(S8) | ALB 고정비 |
| App Runner | | | | | | | | **신규 고객 불가** |
| Azure Container Apps | 240초 | | 지원 | 가능(min>0) | 가능 / Jobs | | | 월 18만 vCPU-초 무료 |
| GKE Autopilot | Ingress·LB 설정 | | 지원 | 가능 | 가능 | PV | | 특권·DaemonSet 제한 |
| EKS (+Auto Mode) | Ingress·LB 설정 | | 지원 | 가능 | 가능 | EBS PV | RDS Proxy | 연장 지원 $0.60/시간, Auto Mode 노드 21일 |

---

## 새 축·규칙 후보

### A. 새 가정 키(§4.3 확장)
1. **`traffic.baseline_connections`** — 실시간·IoT 도메인은 동시 요청이 아니라 동시 **연결 수**가 용량을 결정한다. T 판정과 티어 한도(Supabase Realtime 200/500, Railway 1만 연결 등)를 이 값으로 비교한다. 근거: W-001, W-033, W-066.
2. **`traffic.reconnect_ramp_seconds`** — 배포·정전 복구 시 재접속이 몰리는 시간. 예고 없는 램프이므로 T 수준이 낮아도 T-CTL-003(커넥션 풀)과 백오프 통제를 요구. 근거: W-003, W-033.
3. **`external.<provider>_limit`** (예: LLM ITPM/OTPM, FCM 분당 60만, SES 초당 발송) — 외부 한도를 용량 계획에 포함. 피크 가정 × 단위 사용량 > 외부 한도이면 "큐 + 백오프" 처방. 근거: W-012, W-022, W-023.
4. **`traffic.peak_multiplier` 도메인 재정의** — 재난·공공 알림은 T3 기본 ×20이 과소일 가능성. 도메인별로 ×20보다 큰 값을 둘 수 있게 `rules/assumptions.yaml`에서 덮어쓰기 허용(값은 실측 되먹임 §17.5로 보정).

### B. 새 수준 규칙 후보(§4.2 확장)
5. **C-L3 조건에 "예약 슬롯 겹침" 추가** — 좌석 차감과 같은 성격. 신호: `Reservation`/`Booking` + 시간 구간 컬럼. 근거: W-036.
6. **C-L3 조건에 "크레딧·포인트 차감" 명시** — AI 앱 크레딧, 게임 재화. 근거: W-016.
7. **C-L2 하위 통제 "테넌트 격리"** — B2B 신호가 있으면 수준과 별개로 필수 통제: 테넌트 컨텍스트 강제 + RLS FORCE + 비소유자 역할. P4 검증에 교차 테넌트 접근 테스트 추가. 근거: W-028.
8. **T-CTL-007(레이트 리밋)을 T 수준 무관 필수로 만드는 경로 목록** — SMS/OTP 발송, 공개 API, 로그인 없는 LLM 호출. 수준이 아니라 "남용 시 비용·평판 손실" 기준. 근거: W-016, W-024, W-031.
9. **U-L2 조건에 "모바일 클라이언트 존재" 추가** — 구버전 클라이언트가 남으므로 expand/contract가 필수. 근거: W-030.
10. **C 판정에서 경로별 분리** — 분석 이벤트·텔레메트리·프레즌스 경로는 C0으로 분리해 전체 C 수준을 끌어올리지 않게 한다(§4.2 C L0 조건의 경로 단위 적용). 근거: W-004, W-026, W-033.

### C. 새 티어 규칙 후보(§8.4 TIER 확장)
11. **TIER-006 플랫폼 수치 표 기반 제외** — TIER-001/002를 W-089·W-090 표로 일반화: `max(경로 처리 시간) > 플랫폼 상한` 또는 `max(본문) > 플랫폼 한도`이면 해당 경로 처방(비동기화·서명 URL) 후에도 남으면 제외.
12. **TIER-007 신규 불가 플랫폼 제외** — App Runner는 신규 구성 후보에서 제외, 기존 사용 시 유지 + 경고. 근거: W-081.
13. **TIER-008 무료 플랜 하한** — D≥1 또는 공개 서비스(T≥1)면 Render Free(Postgres 30일 만료·스핀다운), Supabase Free(1주 중지·백업 없음), Vercel Hobby(결제·광고 신호 시 비상업 조항)를 "수준 미충족"으로 보고 최저 유료 플랜으로 견적. 근거: W-051, W-065, W-071, W-091.
14. **TIER-009 디스크 의존 구성 제외** — Render 디스크·Fly 단일 볼륨·Replit 파일 시스템에 사용자 데이터가 있으면 T≥1/U≥1/D≥2와 충돌 → 매니지드 DB·스토리지 처방 선행. 근거: W-072, W-074, W-076.
15. **TIER-010 GPU·리전 조합** — 자체 추론 + 서울 리전이면 Cloud Run GPU 불가(서울 미제공) → 리전 분리 또는 외부 API. 근거: W-014, W-078.
16. **TIER-011 규제 데이터 플랫폼 제한** — 의료·금융 신호가 있으면 BAA·규제 대상 목록에 있는 서비스만 후보. 코드로 계약 확인 불가 → 리포트에 "사용자 확인 필요". 근거: W-041.
17. **TIER-012 앱·DB 리전 불일치 경고** — Vercel 기본 `iad1` + 서울 DB 등. 근거: W-053, W-092.

### D. 새 비용 규칙 후보
18. **COST-010 EKS 연장 지원 경고** — 버전이 표준 지원 밖이면 클러스터당 시간당 $0.60. 근거: W-085.
19. **COST-011 미완료 멀티파트 정리 규칙 부재** — 업로드 신호 + 수명주기 규칙 없음. 근거: W-007.
20. **COST-012 egress 지배 도메인** — 미디어 신호가 있으면 견적에서 전송 비용을 별도 항목으로 강조, CDN·무료 egress 스토리지 비교. 근거: W-009.
21. **COST-013 과잉 검색·벡터 인프라** — 소규모 데이터에 전용 검색 클러스터·벡터 DB가 있으면 Postgres FTS/pgvector로 축소 제안. 근거: W-015, W-025.

### E. 새 탐지 사실(fact ID) 후보
`rt.longpoll_enabled`, `rt.presence_inmem`, `upload.through_app`, `upload.multipart`, `media.transcode_in_request`, `llm.agent_loop`, `llm.no_user_quota`, `bg.fire_and_forget`, `cron.in_process`, `queue.db_no_skip_locked`, `mail.provider`, `push.loop_send`, `sms.unauth_endpoint`, `search.dual_write`, `tenant.rls_not_forced`, `api.public_no_idempotency`, `webhook.outbound_sync`, `counter.single_row_hot`, `booking.no_exclusion`, `next.isr_no_shared_cache`, `next.server_actions_key_unset`, `platform.plan`(대부분 "미확인"), `platform.region`, `db.conn_mode`(direct/session/transaction).

### F. 이 문서에서 확인하지 못한 것(후속 조사)
- Netlify 크레딧 소진 시 동작, Netlify 서울 리전 제공 여부
- Fly.io·Railway·Render의 서울(또는 도쿄) 리전 제공 여부와 Render 유료 플랜 단가
- Render HTTP 요청 타임아웃 수치
- Supabase Pro의 DB 고가용성(존 장애 대비) 구성 여부와 IPv4 애드온 가격
- 한국 개인정보보호법·전자금융감독규정의 클라우드·국외 이전 요건
- SMS 발송(국내 발신번호 등록제, 알림톡) 공식 문서
