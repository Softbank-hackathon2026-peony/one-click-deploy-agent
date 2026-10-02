# 컴퓨트 티어 0 — PaaS·서버리스 플랫폼 능력 표

삭제된 절: 5 Render(5.1·5.2), 6 Fly.io, 9 Replit(9.1~9.3), 12 Koyeb(12.1·12.2), 사유: 부적격 출처 (2026-10-02. 부적격 출처에 기댄 표 행과 줄도 지웠다. 남은 절 번호는 그대로)

- 작성일: 2026-10-01 (모든 값의 확인일 2026-10-01)
- 형식: [README.md](README.md) §1, 능력 키: README §2.7 `CP.*` 18개
- 요구 쪽 차원: [../dimensions.md](../dimensions.md)
- 재료: [../considerations/08-workloads-platforms.md](../considerations/08-workloads-platforms.md) 파트 3, [06-cost.md](../considerations/06-cost.md), [03-deploy-release.md](../considerations/03-deploy-release.md). 재료의 값은 모두 공식 문서를 다시 열어 확인했고, 바뀐 값은 새 값으로 적었다.

## 범위

바이브코더가 처음 배포하는 PaaS·서버리스 플랫폼(티어 0). 플랜에 따라 판정이 바뀌면 플랜별로 나눴다. 관리형 컨테이너·함수(Cloud Run, ECS, Azure Container Apps 등)와 쿠버네티스는 [05-compute-tier1-2.md](05-compute-tier1-2.md)에서 다룬다.

표기
- `미확인`: 공식 문서에서 찾지 못한 값. 추측하지 않았다.
- `(추론)`: 인용한 사실에서 우리가 이끌어 낸 결론. 판정 규칙에 쓰기 전에 사람이 검토해야 한다.
- 문서끼리 값이 다르면 두 값을 모두 적고 `[충돌]`이라고 표시했다.

## 생성 도구의 기본 배포 대상

저장소만 보고 플랫폼을 알 수 없을 때 생성 도구의 흔적(`.bolt/`, `lovable` 태그, v0 생성 주석 등)이 있으면 아래 기본값을 G1(현재 플랫폼) 가정으로 쓴다.

| 생성 도구 | 기본 배포 대상 | 이 문서 항목 | 출처 (URL · 인용 · 2026-10-01) |
|---|---|---|---|
| v0 (Vercel) | Vercel. v0 계정 = Vercel 계정. 게시하면 Vercel 프로젝트가 자동 생성됨. 업그레이드하지 않으면 Hobby | §1 Vercel | https://v0.app/docs/vercel-integration · "v0 accounts are just Vercel accounts." / "a corresponding Vercel Project is automatically created" · 2026-10-01 |

## 목차

- [요약 비교표](#요약-비교표)
- [1. Vercel](#1-vercel)
  - [1.1 Functions — Hobby](#11-vercel-functions--hobby-fluid-compute-nodejspythonbun)
  - [1.2 Functions — Pro](#12-vercel-functions--pro-fluid-compute)
  - [1.3 Functions — Enterprise](#13-vercel-functions--enterprise-fluid-compute)
  - [1.4 Edge runtime](#14-vercel--edge-runtime-전-플랜)
- [2. Netlify](#2-netlify)
  - [2.1 Functions — Free·Personal](#21-netlify-functions--free--personal)
  - [2.2 Functions — Pro·Enterprise](#22-netlify-functions--pro--enterprise-크레딧-기반)
  - [2.3 Edge Functions](#23-netlify--edge-functions)
- [3. Cloudflare](#3-cloudflare)
  - [3.1 Workers·Pages Functions — Free](#31-cloudflare-workers--pages-functions--free)
  - [3.2 Workers·Pages Functions — Paid](#32-cloudflare-workers--pages-functions--paid)
  - [3.3 Durable Objects](#33-cloudflare--durable-objects)
  - [3.4 Containers](#34-cloudflare--containers-workers-paid)
- [4. Railway](#4-railway)
  - [4.1 Free·Trial](#41-railway--free--trial)
  - [4.2 Hobby](#42-railway--hobby)
  - [4.3 Pro](#43-railway--pro)
- 5. Render — 삭제됨(부적격 출처, 2026-10-02)
- 6. Fly.io Machines — 삭제됨(부적격 출처, 2026-10-02)
- [7. Firebase](#7-firebase)
  - [7.1 App Hosting](#71-firebase-app-hosting--blaze)
  - [7.2 Cloud Functions for Firebase](#72-cloud-functions-for-firebase--blaze-2세대1세대)
- [8. Supabase Edge Functions](#8-supabase-edge-functions)
  - [8.1 Free](#81-supabase-edge-functions--free)
  - [8.2 Pro 이상](#82-supabase-edge-functions--pro-이상)
- 9. Replit Deployments — 삭제됨(부적격 출처, 2026-10-02)
- [10. Heroku](#10-heroku)
  - [10.1 Eco·Basic](#101-heroku--eco--basic-dyno-common-runtime)
  - [10.2 Standard·Performance](#102-heroku--standard--performance-dyno)
- [11. DigitalOcean App Platform](#11-digitalocean--app-platform)
- 12. Koyeb — 삭제됨(부적격 출처, 2026-10-02)
- [교차 관찰](#교차-관찰)

## 요약 비교표

판정에 결정적인 키만 뽑았다. 셀 안의 값은 아래 각 항목에서 출처와 함께 다시 나온다.

| 플랫폼·플랜 | 최대 요청 시간 (A2) | 웹소켓·장시간 연결 (A3) | 응답 후 CPU (A4) | 상시 워커 (A1) | 크론 최소 주기 (B3) | 본문 한도 (A7) | 로컬 디스크·볼륨 (B2) | 종료 유예 (F4) | 서울 (D5) | 플랜 함정 (G1) | 지출 한도 도달 시 | 최소 월비용 (G3) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Vercel Hobby | 300초 (레거시 60초) | 베타, 300초에 끊김 | `waitUntil`/`after`, 함수 시간 안에서만 | 불가 | 하루 1회, ±59분 | 4.5MB | `/tmp` 500MB 임시, 볼륨 없음 | SIGTERM 후 500ms | `icn1` 있음, 기본 `iad1` | **비상업 전용**, 한도 초과 시 최대 30일 대기 | 무료 한도 도달 시 일시 정지 | $0 |
| Vercel Pro | 800초 (베타 1800초) | 베타, 800초에 끊김 | 함수 시간 안에서만 | 불가 (Queues 베타·Workflows) | 1분 | 4.5MB | `/tmp` 500MB 임시 | 500ms (컨테이너 이미지 30초) | `icn1` 있음 | 리전 3개 또는 5개 `[충돌]`, 고정 IP 월 $100 | 일시 정지를 켜면 프로덕션 전체 503, 수동 재개 | 월 $20/좌석 |
| Vercel Enterprise | 800초 (베타 1800초) | 베타 | 함수 시간 안에서만 | 불가 | 1분 | 4.5MB | `/tmp` 500MB | 500ms | `icn1` 있음 | 리전 간 페일오버는 Enterprise만 | Pro와 같음 | 별도 계약 |
| Vercel Edge runtime | 25초 안에 응답 시작, 스트리밍 300초 | `미확인` | 함수 시간 안에서만 | 불가 | 해당 없음 | 4.5MB | 파일 시스템 없음 | `미확인` | 요청 근처에서 실행 | **폐지 권고**, Next.js 16.3부터 미지원 | 플랜 따름 | 플랜 따름 |
| Netlify Free·Personal | 동기 60초, 백그라운드 15분 | 공식 `미확인` (포럼: 미지원) | `waitUntil`, 함수 시간 안에서만 | 불가 | 1분 (실행 30초) | 6MB, 바이너리 약 4.5MB | 임시 | `미확인` | **없음** (기본 오하이오 `cmh`, 변경 불가) | Python 런타임 없음 | **팀 전체 프로젝트 정지**, Free는 크레딧 구매 불가 | $0 / $9 |
| Netlify Pro·Enterprise | 동기 60초, 백그라운드 15분 | 공식 `미확인` | 함수 시간 안에서만 | 불가 | 1분 (실행 30초) | 6MB | 임시 | `미확인` | **없음** (가장 가까운 곳 도쿄 `nrt`) | 고정 IP는 Enterprise 애드온 | 자동 충전 안 켜면 팀 전체 정지 | 월 $20 |
| Netlify Edge Functions | CPU 50ms, 응답 헤더 40초 | `미확인` | `미확인` | 불가 | 해당 없음 | `미확인` | 없음 | `미확인` | `미확인` | 고정 IP 불가 | 플랜 따름 | 플랜 따름 |
| Cloudflare Workers Free | CPU 10ms, 벽시계 무제한(연결 유지 중) | `WebSocketPair` 가능, 조정은 DO | `waitUntil` 응답 후 30초 | 불가 | 1분 (CPU 10ms) | 100MB (계정 Free/Pro) | 요청마다 사라지는 메모리 FS | `미확인` | `미확인` (가장 가까운 데이터센터) | 하루 10만 요청, 초과 시 오류 | 상한 초과분 오류 | $0 |
| Cloudflare Workers Paid | CPU 기본 30초·최대 5분, 벽시계 무제한 | 위와 같음 | 응답 후 30초 | 불가 (DO 알람·Queues·Workflows) | 1분 (CPU 30초/15분) | 100MB~5GB (계정 플랜) | 메모리 FS | `미확인` | `미확인` | — | **지출 상한 없음** (예산 알림만) | 월 $5 |
| Cloudflare Durable Objects | CPU 30초~5분 | 웹소켓 + 하이버네이션, **배포마다 전부 끊김** | 알람 15분 | 객체 단위 상주 | 해당 없음 | 수신 메시지 32MiB | 객체당 SQLite 10GB(Free 1GB) | `미확인` | 서울 지정 불가 (`apac-ne` 힌트) | 생성 후 위치 고정 | 상한 없음 | Paid $5에 포함 |
| Cloudflare Containers | 앞단 Worker 따름 | DO 통해 가능 | 컨테이너 실행 중 가능 | 가능 (DO가 수명 제어) | Worker 크론 | Worker 따름 | **재시작 시 초기화**, 2~20GB | SIGTERM 후 15분 | `미확인` | Workers Paid 전용 | 상한 없음 | 월 $5 + 사용량 |
| Railway Free·Trial | 15분 (무전송 5분) | 무기한 | 가능 (슬리핑 켜면 제한) | 가능 | 5분 | 크기 한도 없음, 5분 내 업로드 | 볼륨 0.5GB, 붙이면 레플리카 불가 | 기본 0초 | **없음** (싱가포르) | 레플리카 1, 0.5GB RAM | 크레딧 소진 시 워크로드 정지 | $0 (월 $1 크레딧) |
| Railway Hobby | 15분 | 무기한 | 가능 | 가능 | 5분 | 5분 내 업로드 | 볼륨 5GB, 레플리카 불가·재배포 시 다운타임 | 기본 0초, 조정 가능 | **없음** | 레플리카 6, 고정 IP 불가 | 하드 한도 시 전체 오프라인 | 월 $5 |
| Railway Pro | 15분 | 무기한 | 가능 | 가능 | 5분 | 5분 내 업로드 | 볼륨 1TB 또는 50GB `[충돌]` | 기본 0초 | **없음** | 레플리카 42, 고정 IP 가능 | 하드 한도 시 전체 오프라인 | 월 $20 |
| Firebase App Hosting | `미확인` | `미확인` | `미확인` | 불가 | 해당 없음 | `미확인` | `미확인` | `미확인` | **없음** (대만·싱가포르) | Blaze 필수, Node.js만 | 선택형 지출 상한 시 그달 정지 | $0 고정비 |
| Cloud Functions for Firebase | 2세대 HTTP 60분, 이벤트 540초, **Hosting 경유 60초** | `미확인` | **없음** | 불가 | `미확인` | 32MB (1세대 10MB) | 메모리 소비하는 임시 | `미확인` | `asia-northeast3` 있음 | Blaze 필수 | 선택형 상한 시 그달 정지 | $0 고정비 |
| Supabase Edge Free | 벽시계 150초, CPU 2초, 유휴 150초 | 가능, 150초 한도 | `EdgeRuntime.waitUntil`, 한도 안 | 불가 | 1분 (pg_cron) | `미확인` | `/tmp` 256MB, 호출마다 초기화 | `미확인` | `ap-northeast-2` 지정 가능 | **1주 무활동 시 프로젝트 정지** | 해당 없음 (한도 초과 시 `미확인`) | $0 |
| Supabase Edge Pro | 벽시계 400초, CPU 2초 | 가능, 400초 한도 | 한도 안 | 불가 | 1분 | `미확인` | `/tmp` 512MB | `미확인` | 지정 가능 | — | **기본 켜진 상한: 할당 초과 시 호출 차단** | 월 $25 |
| Heroku Eco·Basic | **첫 바이트 30초**, 이후 55초 유휴 | 지원, 55초 유휴 | 가능 (Eco는 30분 유휴 시 잠듦) | 가능 | 10분 (Scheduler) | 명시 없음 | 임시, **매일 재시작** | 30초 | **없음** | dyno 1개, Eco는 개인 앱만, 무중단 배포 불가 | 지출 상한 언급 없음 | 월 $5 |
| Heroku Standard·Performance | 30초 / 55초 | 지원 | 가능 | 가능 | 10분 | 명시 없음 | 임시, 매일 재시작 | 30초 | **없음** (도쿄는 Private Spaces만) | 오토스케일은 Performance 이상 | 언급 없음 | 월 $25 |
| DigitalOcean App Platform | 기본 30초, 최대 100초 (PHP 문서 근거) | 지원, 한도 `미확인` | 가능 | 가능 | **15분** | 업로드 600초 타임아웃 | 임시 4GiB, 볼륨 없음 | 기본 120초, 최대 600초 | **없음** (싱가포르) | 고정 IP와 VPC 동시 사용 불가 | `미확인` | 월 $5 |

---

## 1. Vercel

공통 사실(플랜과 무관하게 같은 값)은 각 플랜 표에 반복해 적었다. 기계 비교가 플랜 단위로 이루어지기 때문이다. 2025-04-23 이후 생성 프로젝트는 Fluid compute가 기본이다. 그 전 프로젝트는 레거시 한도가 적용되며, 저장소만으로는 둘 중 무엇인지 알 수 없다(재료 W-056).

### 1.1 Vercel Functions — Hobby (Fluid compute, Node.js·Python·Bun)
- 계열: 컴퓨트-티어0
- 서울 리전: 있음 (`icn1`). 기본은 `iad1`이라 직접 설정해야 한다. https://vercel.com/docs/regions

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | 웹(함수)과 정기 작업(Cron이 함수 호출). 상시 워커 없음. 장시간 연결은 웹소켓 베타 | 무한 실행 작업은 Workflows로 보내라고 안내 | https://vercel.com/docs/cron-jobs/usage-and-pricing · "Cron jobs invoke Vercel Functions." · https://vercel.com/docs/functions/limitations · "For workloads that require unlimited execution time, use Vercel Workflows" · 2026-10-01 |
| CP.request_timeout | 기본 300초, 최대 300초 | 스트리밍 응답도 포함. 초과 시 504 `FUNCTION_INVOCATION_TIMEOUT`. 레거시(비 Fluid) 프로젝트는 기본 10초·최대 60초. 외부 오리진 rewrite 프록시는 120초 | https://vercel.com/docs/functions/limitations · "time spent processing the request and sending the response, including streamed responses" · https://vercel.com/docs/limits (레거시 표, Proxied Request Timeout) · 2026-10-01 |
| CP.long_connection | 웹소켓 베타. 연결은 인스턴스 하나에 고정되고 최대 실행 시간(300초)에 닫힘. 재연결이 같은 인스턴스로 간다는 보장 없음 | Fluid compute 필요. 연결 중 함수 사용량 과금. SSE도 무한 스트리밍 불가 | https://vercel.com/docs/functions/websockets · "WebSocket connections close when a Vercel Function reaches its maximum duration." · https://vercel.com/docs/functions/runtimes · "it isn't possible to stream indefinitely." · 2026-10-01 |
| CP.cpu_outside_request | 함수 최대 실행 시간 안에서만. `waitUntil`·`after()`로 응답 후 작업 가능, 시간 초과 시 취소 | 요청 취소를 켜면 `waitUntil`/`after` 밖의 작업은 사라짐 | https://vercel.com/docs/functions/functions-api-reference/vercel-functions-package · "Promises passed to `waitUntil()` will have the same timeout as the function itself." · 2026-10-01 |
| CP.cold_start | scale-to-zero. 바이트코드 캐시와 프로덕션 사전 예열로 콜드 스타트 완화. 최소 인스턴스 설정 `미확인`. 유휴 함수는 2주(프리뷰 48시간) 안에 보관되고, 보관 후 첫 기동은 최소 1초 더 걸림 | | https://vercel.com/docs/fluid-compute · "function pre-warming on production deployments" · https://vercel.com/docs/functions/runtimes · "at least 1 second longer than usual" · 2026-10-01 |
| CP.instance_size | 2GB / 1vCPU 고정. GPU 없음(`미확인`) | 번들 250MB(Python 500MB). 파일 디스크립터 1,024개를 동시 실행 전체가 공유 | https://vercel.com/docs/functions/limitations · "1,024 shared across concurrent executions" · 2026-10-01 |
| CP.request_size | 요청·응답 본문 각 4.5MB | 초과 시 413 `FUNCTION_PAYLOAD_TOO_LARGE` | https://vercel.com/docs/functions/limitations · "The maximum payload size for the request body or the response body of a Vercel Function is 4.5 MB" · 2026-10-01 |
| CP.local_disk | 읽기 전용 파일 시스템과 쓰기 가능한 `/tmp` 최대 500MB(임시). 영속 볼륨 없음 | 영속 저장은 Blob·Marketplace DB | https://vercel.com/docs/functions/runtimes · "Read-only filesystem with writable `/tmp` scratch space up to 500 MB" · 2026-10-01 |
| CP.scaling | 동시 실행 최대 30,000. 리전당 10초마다 1,000씩 확장 | 초과 시 503 `FUNCTION_THROTTLED`. 급증 시 확장에 수 분 걸릴 수 있음 | https://vercel.com/docs/functions/concurrency-scaling · "scale to a maximum of 30,000 on Hobby and Pro" / "1000 concurrent executions per 10 seconds, per region" · 2026-10-01 |
| CP.concurrency | 한 인스턴스가 여러 요청을 동시에 처리(Node.js·Python). 인스턴스당 상한 `미확인` | | https://vercel.com/docs/fluid-compute · "Optimized concurrency in fluid compute is available when using Node.js or Python runtimes." · 2026-10-01 |
| CP.shutdown | SIGTERM 후 500ms | 컨테이너 이미지 함수는 30초 | https://vercel.com/docs/functions/functions-api-reference · "Your code can run for up to 500 milliseconds (30 seconds for container images) after receiving a SIGTERM signal." · 2026-10-01 |
| CP.deploy | 배포마다 새 URL로 교체. 즉시 롤백은 바로 이전 배포로만. Rolling Releases·Skew Protection 없음 | 무중단 배포를 직접 명시한 문장은 `미확인` | https://vercel.com/docs/instant-rollback · "Hobby users can roll back to the immediately previous deployment" · 2026-10-01 |
| CP.availability | 기본 다중 AZ 이중화. 리전 1개. 리전 간 페일오버 없음 | | https://vercel.com/docs/functions/configuring-functions/region · "Vercel Functions have multiple availability zone redundancy by default." (Hobby "Single region") · 2026-10-01 |
| CP.networking | 고정 출구 IP·VPC 피어링 불가(Pro·Enterprise 기능). DB는 공개 엔드포인트와 풀러로 연결. `attachDatabasePool`로 정지 전 유휴 연결 반환 | | https://vercel.com/docs/networking/static-ips (Pro·Enterprise 전용) · https://vercel.com/docs/functions/functions-api-reference/vercel-functions-package · "ensures that idle pool clients are properly released before functions suspend" · 2026-10-01 |
| CP.regions | 컴퓨트 리전 19개, 서울 `icn1`·도쿄 `hnd1`·오사카 `kix1`. 새 프로젝트 기본 `iad1` | | https://vercel.com/docs/regions · "icn1 \| ap-northeast-2 \| Seoul, South Korea" / "Vercel Functions default to running in the `iad1` (Washington, D.C., USA) region" · 2026-10-01 |
| CP.plan_limits | **비상업 개인 용도만**(결제·광고·유료 제작 사이트는 상업). 크론 하루 1회·±59분, 더 잦으면 배포 실패. 프로젝트당 크론 100개. 비 Next.js·SvelteKit 프레임워크는 배포당 함수 12개. 하루 배포 100회. 런타임 로그 1시간. 한도 초과 시 대부분 30일 대기 | | https://vercel.com/docs/limits/fair-use-guidelines · "Hobby teams are restricted to non-commercial personal use only." · https://vercel.com/docs/cron-jobs/usage-and-pricing · "Cron expressions that would run more frequently will fail during deployment." · https://vercel.com/docs/plans/hobby · "you will have to wait until 30 days have passed" · 2026-10-01 |
| CP.ops_burden | 서버·노드 관리 없음. 리전·`maxDuration`·크론 설정과 DB 연결 관리만 남음 (추론, 명시 문장 `미확인`) | | 위 문서들의 범위에서 추론 ⚠️근거없음 |
| CP.cost_floor | $0. 포함량: 호출 100만, 활성 CPU 4시간, 프로비저닝 메모리 360GB-시간, Fast Data Transfer 100GB | 무료 한도 도달 시 프로젝트 자동 일시 정지 | https://vercel.com/docs/plans/hobby · https://vercel.com/changelog/spend-management-now-pauses-production-deployments-by-default · "automatically paused when reaching the included free tier limits" · 2026-10-01 |

#### 비용 구조
최소 월 고정비 $0. 변동 단위는 없음(포함량 초과 시 일시 정지·대기). 과금 함정: 저장소에 결제·광고 신호가 있으면 Hobby를 쓸 수 없어 견적 하한이 Pro 월 $20으로 올라간다.

#### 교체 계열 정보
컨테이너(티어 1)로 옮길 때 바뀌는 지점:
- `@vercel/functions`: `waitUntil`, `getEnv`, `getDeadline`, `geolocation`, `ipAddress`, `getCache`, `invalidateByTag`, `attachDatabasePool`, `experimental_upgradeWebSocket`("this API only works on the Vercel platform"). https://vercel.com/docs/functions/functions-api-reference/vercel-functions-package
- `vercel.json`: `crons`(→ 외부 스케줄러), `regions`, `functions.maxDuration`, `functionFailoverRegions`, `experimentalTriggers`(Queues).
- 저장소: Vercel Blob, Global Config(이전 Edge Config). KV·Postgres는 더 이상 Vercel 자체 상품이 아니고 Marketplace(Upstash, Neon 등)가 환경변수로 자격 증명을 주입한다. https://vercel.com/docs/storage
- `@vercel/queue`, `workflow` SDK(`'use workflow'`, `'use step'`).
- Next.js 자체 호스팅: 여러 인스턴스면 공유 `cacheHandler`, 모든 인스턴스에 같은 `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY`, `deploymentId` 설정이 필요하다. `after`는 `next start`에서 완전 지원. 권장 드레인 10~30초. https://nextjs.org/docs/app/guides/self-hosting
- 종속 정도: Next.js 표준 API만 쓰면 낮음, 위 Vercel 전용 API·Workflow를 쓰면 중간~높음 (추론). ⚠️근거없음

#### 함정
- 2025-04-23 전 프로젝트는 최대 60초. "Vercel은 300초"로 판정하면 틀린다.
- 함수 리전 기본값이 미국이라 서울 DB와 함께 쓰면 쿼리마다 태평양을 왕복한다.
- 웹소켓은 300초마다 모든 연결이 끊긴다.
- 종료 유예가 500ms라 진행 중인 응답 후 작업은 정리할 시간이 거의 없다.

### 1.2 Vercel Functions — Pro (Fluid compute)
- 계열: 컴퓨트-티어0
- 서울 리전: 있음 (`icn1`, 설정 필요). https://vercel.com/docs/regions

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | 웹(함수)과 정기 작업. 상시 워커 없음. 백그라운드는 Queues(베타, 최소 1회 전달, 소비자도 함수)나 Workflows. 컨테이너 이미지 함수(베타)도 요청 기반으로 축소됨 | 컨테이너 이미지는 트래픽 없으면 프로덕션 5분, 프리뷰 30초 뒤 축소 | https://vercel.com/docs/queues · "at-least-once delivery" · https://vercel.com/docs/workflows · "Pause for minutes or months" · https://vercel.com/docs/functions/container-images · "Functions not receiving any traffic for 5 minutes in production environments … will automatically scale down." · 2026-10-01 |
| CP.request_timeout | 기본 300초, 최대 800초. 확장 1800초(베타) | 800초 초과는 함수 단위 설정 + 특정 Node.js·Bun·Python 버전만, Secure Compute·고정 IP와 병용 불가. 레거시 프로젝트는 기본 15초·최대 300초 | https://vercel.com/docs/functions/limitations · "Values above 800 seconds require function-level configuration and are only supported for specific Node.js, Bun, and Python runtime versions." · https://vercel.com/docs/limits · 2026-10-01 |
| CP.long_connection | 웹소켓 베타, 최대 실행 시간(최대 800초)에 닫힘. 배포 뒤 기존 연결은 이전 배포에 남음 | 연결 중 과금 | https://vercel.com/docs/functions/websockets · "existing connections remain on the previous deployment" · 2026-10-01 |
| CP.cpu_outside_request | 함수 최대 실행 시간 안에서만(`waitUntil`·`after`) | | https://vercel.com/docs/functions/functions-api-reference/vercel-functions-package · "If the function times out, the promises will be cancelled." · 2026-10-01 |
| CP.cold_start | scale-to-zero, 사전 예열. 최소 인스턴스 `미확인` | | https://vercel.com/docs/fluid-compute · "function pre-warming on production deployments" · 2026-10-01 |
| CP.instance_size | 기본 2GB/1vCPU, 최대 4GB/2vCPU(Performance). GPU `미확인` | 대형 함수 최대 5GB 번들(베타, Secure Compute·고정 IP와 병용 불가) | https://vercel.com/docs/functions/limitations · "Large functions support up to 5 GB Beta" · https://vercel.com/docs/fluid-compute · 2026-10-01 |
| CP.request_size | 4.5MB | | https://vercel.com/docs/functions/limitations · "4.5 MB" · 2026-10-01 |
| CP.local_disk | `/tmp` 500MB 임시, 볼륨 없음 | | https://vercel.com/docs/functions/runtimes · "writable `/tmp` scratch space up to 500 MB" · 2026-10-01 |
| CP.scaling | 동시 실행 최대 30,000, 리전당 10초마다 1,000 | 초과 시 503 | https://vercel.com/docs/functions/concurrency-scaling · "scale to a maximum of 30,000 on Hobby and Pro" · 2026-10-01 |
| CP.concurrency | 인스턴스 공유 동시 처리(Node.js·Python), 상한 `미확인` | | https://vercel.com/docs/fluid-compute · "multiple invocations to share a single function instance" · 2026-10-01 |
| CP.shutdown | SIGTERM 후 500ms(컨테이너 이미지 30초) | | https://vercel.com/docs/functions/functions-api-reference · "up to 500 milliseconds (30 seconds for container images)" · 2026-10-01 |
| CP.deploy | 이전 프로덕션 배포 어느 것으로든 즉시 롤백. Rolling Releases는 Pro 팀당 프로젝트 1개. Skew Protection(기본 최대 1일) | 롤백 뒤 프로덕션 도메인 자동 할당이 멈추고, 환경변수는 갱신되지 않으며, 크론은 이전 상태로 돌아감 | https://vercel.com/docs/rolling-releases · "Pro teams can use Rolling Releases for one project." · https://vercel.com/docs/skew-protection · "The default maximum age is one day" · https://vercel.com/docs/instant-rollback · 2026-10-01 |
| CP.availability | 다중 AZ 기본. 여러 리전 배치 가능(개수 `[충돌]` 3 또는 5). 리전 장애 시 자동 페일오버는 Enterprise만 | | https://vercel.com/docs/functions/configuring-functions/region · Pro "5 regions" · https://vercel.com/docs/fluid-compute · Pro "Up to 3" · 2026-10-01 |
| CP.networking | 고정 출구 IP: 프로젝트당 월 $100 + Private Data Transfer, 아웃바운드 전용, 공유 VPC. VPC 피어링(Secure Compute)은 Enterprise만 | 고정 IP는 1800초 확장·대형 함수·컨테이너 이미지와 병용 불가 | https://vercel.com/docs/networking/static-ips · "$100.00/month per project, plus Private Data Transfer" · 2026-10-01 |
| CP.regions | `icn1` 있음, 기본 `iad1` | | https://vercel.com/docs/regions · 2026-10-01 |
| CP.plan_limits | 상업 이용 가능. 크론 1분 단위·분 정밀도, 프로젝트당 100개. 런타임 로그 1일 | | https://vercel.com/docs/cron-jobs/usage-and-pricing · Pro "Once per minute" · https://vercel.com/docs/limits · 2026-10-01 |
| CP.ops_burden | 서버 관리 없음. 지출 관리·리전·롤링 릴리스 설정 (추론) | | 추론 ⚠️근거없음 |
| CP.cost_floor | 월 $20 플랫폼 요금(배포 좌석 1개 포함, $20 사용량 크레딧). 추가 배포 좌석 월 $20. 활성 CPU 시간당 $0.128부터, 프로비저닝 메모리 GB-시간당 $0.0106부터, 호출 100만 건당 $0.60. CDN 요청 100만·전송 1TB 포함 | 지출 알림 기본 $200. 한도 설정만으로는 사용이 멈추지 않음 | https://vercel.com/docs/plans/pro-plan · "$20/month Pro platform fee — 1 deploying team seat included — $20/month in usage credit" · https://vercel.com/docs/limits/fair-use-guidelines · "Starting at $0.128 per hour" · 2026-10-01 |

#### 비용 구조
최소 월 $20(좌석 1개). 변동: 활성 CPU, 프로비저닝 메모리, 호출, 데이터 전송. I/O 대기는 활성 CPU에 들어가지 않아 LLM 호출처럼 기다리는 작업에 유리하다.
지출 한도 동작: 한도 금액을 정해도 "Pause Production Deployments"를 켜지 않으면 사용은 계속된다. 켜면 프로덕션 배포가 503 `DEPLOYMENT_PAUSED`로 멈추고, 한도를 올려도 프로젝트마다 손으로 재개해야 한다. 지출은 몇 분 간격으로 확인해서 정지가 즉시 일어나지 않는다. 좌석·Marketplace 통합·애드온은 한도 밖이다. 일시 정지가 지금 기본으로 켜져 있는지는 `미확인`(2024 변경 기록은 기본이라고 하고, 현재 문서는 켜져 있는지 확인하라고 한다). https://vercel.com/docs/spend-management · "Setting a spend amount does not stop usage on its own." / "Projects won't automatically unpause if you increase the spend amount, you must resume each project manually."

#### 교체 계열 정보
§1.1과 같다. 추가로 Queues(`@vercel/queue`, `experimentalTriggers`)·Workflows·Rolling Releases 설정은 컨테이너 환경에서 큐 서비스·워커로 바꿔야 한다.

#### 함정
- 지출 한도 일시 정지는 비용 통제가 곧 전체 장애가 되는 구조다(F1과 충돌).
- 800초를 넘는 1800초는 베타이고 고정 IP와 함께 쓸 수 없다. 고정 IP가 필요한 앱은 800초가 상한이다.

### 1.3 Vercel Functions — Enterprise (Fluid compute)
- 계열: 컴퓨트-티어0
- 서울 리전: 있음 (`icn1`)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | Pro와 같음(함수, 크론, Queues 베타, Workflows) | | https://vercel.com/docs/queues · https://vercel.com/docs/workflows · 2026-10-01 |
| CP.request_timeout | 기본 300초, 최대 800초, 확장 1800초(베타) | 레거시 프로젝트는 기본 15초, 최대 900초 | https://vercel.com/docs/functions/limitations · https://vercel.com/docs/limits · 2026-10-01 |
| CP.long_connection | 웹소켓 베타, 최대 실행 시간에 닫힘 | | https://vercel.com/docs/functions/websockets · 2026-10-01 |
| CP.cpu_outside_request | 함수 시간 안에서만 | | https://vercel.com/docs/functions/functions-api-reference/vercel-functions-package · 2026-10-01 |
| CP.cold_start | scale-to-zero, 사전 예열. 최소 인스턴스 `미확인` | | https://vercel.com/docs/fluid-compute · 2026-10-01 |
| CP.instance_size | 최대 4GB/2vCPU | | https://vercel.com/docs/functions/limitations · 2026-10-01 |
| CP.request_size | 4.5MB | | https://vercel.com/docs/functions/limitations · 2026-10-01 |
| CP.local_disk | `/tmp` 500MB 임시 | | https://vercel.com/docs/functions/runtimes · 2026-10-01 |
| CP.scaling | 동시 실행 최대 100,000 | | https://vercel.com/docs/functions/concurrency-scaling · "100,000 on Enterprise" · 2026-10-01 |
| CP.concurrency | 인스턴스 공유 동시 처리, 상한 `미확인` | | https://vercel.com/docs/fluid-compute · 2026-10-01 |
| CP.shutdown | SIGTERM 후 500ms | | https://vercel.com/docs/functions/functions-api-reference · 2026-10-01 |
| CP.deploy | 롤백(이전 프로덕션 배포 어느 것이든), Rolling Releases, Skew Protection | | https://vercel.com/docs/rolling-releases · "Vercel offers Rolling Releases on Pro and Enterprise." · 2026-10-01 |
| CP.availability | 모든 리전 사용 가능. Node.js 함수의 리전 간 자동 페일오버(`functionFailoverRegions`) | | https://vercel.com/docs/functions/configuring-functions/region · "Enterprise teams can enable multi-region redundancy" · https://vercel.com/docs/regions · "Vercel functions can automatically failover to a different region" · 2026-10-01 |
| CP.networking | Secure Compute(IP 허용 목록, VPC 피어링, 완전 격리), 고정 IP | Secure Compute는 컨테이너 이미지·1800초와 병용 불가 | https://vercel.com/docs/networking/static-ips · "IP allowlisting, VPC Peering, full isolation" · 2026-10-01 |
| CP.regions | `icn1` 있음 | | https://vercel.com/docs/regions · 2026-10-01 |
| CP.plan_limits | 크론 1분. Edge 코드 크기 4MB | | https://vercel.com/docs/cron-jobs/usage-and-pricing · https://vercel.com/docs/functions/runtimes/edge · 2026-10-01 |
| CP.ops_burden | 서버 관리 없음 (추론) | | 추론 ⚠️근거없음 |
| CP.cost_floor | 별도 계약(공개 가격 `미확인`) | | https://vercel.com/docs/networking/static-ips · Secure Compute "custom pricing" · 2026-10-01 |

#### 비용 구조
공개 최소 금액 `미확인`. 지출 관리 동작은 Pro와 같다(§1.2).

#### 교체 계열 정보
§1.1과 같다. Secure Compute로 연결한 사설 DB는 이전 대상 클라우드의 VPC 연결로 다시 구성해야 한다.

#### 함정
리전 장애 대비(F2)가 필요하면 Vercel에서는 Enterprise만 충족한다.

### 1.4 Vercel — Edge runtime (전 플랜)
- 계열: 컴퓨트-티어0
- 서울 리전: 요청에 가장 가까운 리전에서 실행. https://vercel.com/docs/functions/runtimes/edge

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | 웹만 | | https://vercel.com/docs/functions/runtimes/edge · 2026-10-01 |
| CP.request_timeout | 25초 안에 응답을 시작해야 하고, 스트리밍은 최대 300초 | | https://vercel.com/docs/functions/runtimes/edge · "must begin sending a response within 25 seconds to maintain streaming capabilities beyond this period, and can continue streaming data for up to 300 seconds." · 2026-10-01 |
| CP.long_connection | `미확인` | 웹소켓 문서는 Fluid compute(Node.js 등)를 요구 | https://vercel.com/docs/functions/websockets · 2026-10-01 |
| CP.cpu_outside_request | `waitUntil`, 함수 시간 안에서만 | | https://vercel.com/docs/functions/functions-api-reference/vercel-functions-package · 2026-10-01 |
| CP.cold_start | `미확인` | | — |
| CP.instance_size | 코드 크기(gzip 후) Hobby 1MB, Pro 2MB, Enterprise 4MB. 메모리 `미확인` | | https://vercel.com/docs/functions/runtimes/edge · 2026-10-01 |
| CP.request_size | 4.5MB | | https://vercel.com/docs/functions/limitations · 2026-10-01 |
| CP.local_disk | 파일 시스템 없음 | | https://vercel.com/docs/functions/runtimes/edge · "you can't read or write to the filesystem" · 2026-10-01 |
| CP.scaling | `미확인` | | — |
| CP.concurrency | `미확인` | | — |
| CP.shutdown | `미확인` | | — |
| CP.deploy | 플랜별 롤백 규칙(§1.1~1.3) | | https://vercel.com/docs/instant-rollback · 2026-10-01 |
| CP.availability | 모든 플랜에서 다른 리전으로 재라우팅 | | https://vercel.com/docs/functions/runtimes/edge · "on all plans" · 2026-10-01 |
| CP.networking | 고정 IP·Secure Compute 대상 아님 (`미확인`) | | — ⚠️근거없음 |
| CP.regions | 요청에 가장 가까운 리전 | | https://vercel.com/docs/functions/runtimes/edge · "execute in the region closest to the incoming request" · 2026-10-01 |
| CP.plan_limits | **Node.js로 이전 권고. Next.js 16.3부터 `runtime = 'edge'` 미지원** | `require`·`eval` 불가 | https://vercel.com/docs/functions/runtimes/edge · "We recommend migrating from edge to Node.js" / "Starting in Next.js 16.3, setting `runtime = 'edge'` is no longer supported." · 2026-10-01 |
| CP.ops_burden | 서버 관리 없음 (추론) | | 추론 ⚠️근거없음 |
| CP.cost_floor | 플랜 요금에 포함 | | https://vercel.com/docs/plans/pro-plan · 2026-10-01 |

#### 비용 구조
플랜 요금을 따른다.

#### 교체 계열 정보
Edge 코드는 Web API만 쓰므로 Node.js 런타임으로 바꾸면 대부분 그대로 돌아간다(추론). 다만 `export const runtime = 'edge'` 선언 제거가 필수다. ⚠️근거없음

#### 함정
Edge를 쓰는 저장소는 이전 판단과 별개로 런타임 교체(Edge → Node.js) 처방이 먼저 나온다.

## 2. Netlify

Functions 언어는 TypeScript·JavaScript·Go다. **Python 함수 런타임이 없다.** https://docs.netlify.com/build/functions/overview/

### 2.1 Netlify Functions — Free · Personal
- 계열: 컴퓨트-티어0
- 서울 리전: 없음. 기본 `cmh`(오하이오)이고, 리전 변경은 Pro 이상이다. 아시아 선택지는 `nrt`(도쿄)·`sin`·`syd`. https://docs.netlify.com/build/functions/configuration/

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | 웹(동기 함수), 백그라운드 함수(15분, 202 반환), 정기 함수. 상시 워커 없음 | 정기·백그라운드 함수는 모든 플랜에서 사용 가능 | https://docs.netlify.com/build/functions/overview/ · "ephemeral runtime environments" · https://docs.netlify.com/build/functions/scheduled-functions/ · "all pricing plans… including free tiers" · 2026-10-01 |
| CP.request_timeout | 동기 60초, 스트리밍 60초, 정기 30초, 백그라운드 15분 | | https://docs.netlify.com/build/functions/configuration/ · "Synchronous execution limit: 60 seconds" / "Background execution limit: 15 minutes" · https://docs.netlify.com/build/functions/api/ · 2026-10-01 |
| CP.cpu_outside_request | `context.waitUntil()`로 함수 실행 시간 한도 안에서만, 그 시간도 과금 | | https://docs.netlify.com/build/functions/api/ · "Function can run until its execution time limit, including all async work" · 2026-10-01 |
| CP.cold_start | 요청 기반 임시 실행 환경(scale-to-zero). 최소 인스턴스 `미확인` | | https://docs.netlify.com/build/functions/overview/ · 2026-10-01 |
| CP.instance_size | 메모리 1024MB 고정. 1~4GB·0.5~2vCPU 조정은 크레딧 기반 Pro·Enterprise만 | | https://docs.netlify.com/build/functions/configuration/ · "Available on: Credit-based Pro and Enterprise plans only" · 2026-10-01 |
| CP.request_size | 버퍼 요청·응답 6MB(바이너리 실효 약 4.5MB). 스트리밍 응답 20MB. 백그라운드 페이로드 256KB | | https://docs.netlify.com/build/functions/configuration/ · "Buffered request/response payload: 6 MB (effectively 4.5 MB for binary payloads" · 2026-10-01 |
| CP.local_disk | 임시, 볼륨 없음 | 영속 저장은 Netlify Blobs | https://docs.netlify.com/build/functions/overview/ · 2026-10-01 |
| CP.scaling | `미확인` | | — |
| CP.concurrency | `미확인` | | — |
| CP.shutdown | `미확인` | | — |
| CP.deploy | 원자적 배포. 이전 배포를 다시 게시해 즉시 롤백. 이전 배포 보존 Free 30일, 유료 90일. 분할 테스트 있음 | | https://docs.netlify.com/deploy/manage-deploys/manage-deploys-overview/ · "Rollbacks are instantaneous." · 2026-10-01 |
| CP.availability | `미확인` (함수는 단일 리전 `cmh`) | | https://docs.netlify.com/build/functions/configuration/ · 2026-10-01 |
| CP.networking | 고정 출구 IP 불가(Enterprise Private Connectivity 애드온 전용) | | https://docs.netlify.com/manage/security/private-connectivity/ · 2026-10-01 |
| CP.regions | 서울 없음, 오하이오 고정 | | https://docs.netlify.com/build/functions/configuration/ · "Default: cmh (US East, Ohio)" · 2026-10-01 |
| CP.plan_limits | Free 월 300크레딧, Personal 월 1,000크레딧. Free는 크레딧 하드 한도이며 추가 구매 불가, 동시 빌드 1개. 정기 함수 최소 1분·UTC·게시된 배포에서만 실행. 상업 이용 제한 `미확인` | | https://www.netlify.com/pricing/ · https://docs.netlify.com/manage/accounts-and-billing/billing/billing-for-credit-based-plans/credit-based-pricing-plans/ · "credit hard limit" · 2026-10-01 |
| CP.ops_burden | 서버 관리 없음 (추론) | | 추론 ⚠️근거없음 |
| CP.cost_floor | Free $0, Personal 월 $9. 프로덕션 배포 15크레딧, 컴퓨트 GB-시간당 10크레딧, 대역폭 GB당 20크레딧, 요청 1만 건당 2크레딧. Personal 자동 충전 500크레딧 $5 | | https://www.netlify.com/pricing/ · 2026-10-01 |

#### 비용 구조
최소 $0(Free) / 월 $9(Personal). 변동 단위는 크레딧이고, 프로덕션 배포 한 번에도 15크레딧이 든다.
지출 한도 동작: 크레딧이 떨어지면 **팀의 모든 프로젝트가 일시 정지**되고 방문자는 "Site not available"을 보며 배포도 멈춘다. Free는 크레딧을 살 수 없다. https://docs.netlify.com/manage/accounts-and-billing/billing/resume-paused-projects/ · "all projects owned by that team enter a paused state"

#### 교체 계열 정보
- 함수 형식: `export default async (req, context)` + `export const config`(경로·스케줄). 컨테이너에서는 일반 HTTP 서버 라우트로 바꾼다.
- `netlify.toml`(리다이렉트·헤더·함수 설정), `-background` 접미사 함수 → 큐 + 워커.
- 플랫폼 전용 API: `context.*`, Netlify Blobs `getStore()`, Netlify Database `getDatabase()`.
- Next.js는 OpenNext 어댑터(opennextjs-netlify)로 실행된다. 렌더링·API는 함수, 미들웨어는 Edge Function, 캐시는 Netlify 캐시, 이미지는 Netlify Image CDN이다. https://docs.netlify.com/build/frameworks/framework-setup-guides/nextjs/overview/
- 종속 정도: 함수 형식은 Web 표준 `Request`/`Response` 기반이라 낮음~중간, Blobs·DB를 쓰면 중간 (추론). ⚠️근거없음

#### 함정
- 크레딧 소진은 사이트 하나가 아니라 팀 전체 정지다.
- Python 백엔드는 Netlify Functions로 옮길 수 없다.
- 한국 사용자 + 서울 DB인데 함수가 오하이오에서 실행된다. Free·Personal은 리전을 바꿀 수 없다.

### 2.2 Netlify Functions — Pro · Enterprise (크레딧 기반)
- 계열: 컴퓨트-티어0
- 서울 리전: 없음. 리전을 바꿀 수 있지만 아시아는 `nrt`(도쿄)·`sin`·`syd`뿐이다. https://docs.netlify.com/build/functions/configuration/

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | 동기 함수, 백그라운드 함수, 정기 함수. 상시 워커 없음 | | https://docs.netlify.com/build/functions/background-functions/ · 2026-10-01 |
| CP.request_timeout | 동기 60초, 정기 30초, 백그라운드 15분 | 플랜이 올라가도 같음 | https://docs.netlify.com/build/functions/configuration/ · 2026-10-01 |
| CP.cpu_outside_request | `waitUntil`, 함수 시간 한도 안에서만 | | https://docs.netlify.com/build/functions/api/ · 2026-10-01 |
| CP.cold_start | scale-to-zero. 최소 인스턴스 `미확인` | | — ⚠️근거없음 |
| CP.instance_size | 메모리 1~4GB, 0.5~2vCPU | | https://docs.netlify.com/build/functions/configuration/ · "Credit-based Pro and Enterprise plans only" · 2026-10-01 |
| CP.request_size | 6MB(바이너리 약 4.5MB), 스트리밍 20MB, 백그라운드 256KB | | https://docs.netlify.com/build/functions/configuration/ · 2026-10-01 |
| CP.local_disk | 임시, 볼륨 없음 | | https://docs.netlify.com/build/functions/overview/ · 2026-10-01 |
| CP.scaling | `미확인` | | — |
| CP.concurrency | `미확인` | | — |
| CP.shutdown | `미확인` | | — |
| CP.deploy | 원자적 배포, 즉시 롤백, 이전 배포 90일 보존 | | https://docs.netlify.com/deploy/manage-deploys/manage-deploys-overview/ · 2026-10-01 |
| CP.availability | Enterprise "99.99% SLA". 함수 멀티 리전 `미확인` | | https://www.netlify.com/pricing/ · "99.99% SLA" · 2026-10-01 |
| CP.networking | 고정 출구 IP: Enterprise Private Connectivity 애드온, 리전 `cmh`·`fra`·`lhr`만. Edge Functions에는 적용 안 됨 | | https://docs.netlify.com/manage/security/private-connectivity/ · 2026-10-01 |
| CP.regions | 서울 없음, 도쿄 `nrt` 선택 가능 | | https://docs.netlify.com/build/functions/configuration/ · 2026-10-01 |
| CP.plan_limits | Pro 월 3,000크레딧, 정기 함수 최소 1분 | | https://www.netlify.com/pricing/ · 2026-10-01 |
| CP.ops_burden | 서버 관리 없음 (추론) | | 추론 ⚠️근거없음 |
| CP.cost_floor | Pro 월 $20(3,000크레딧), 자동 충전 1,500크레딧 $10. Enterprise 별도 계약 | | https://www.netlify.com/pricing/ · 2026-10-01 |

#### 비용 구조
최소 월 $20. 대역폭이 GB당 20크레딧이라 미디어 비중이 큰 사이트는 크레딧이 빨리 떨어진다.
지출 한도 동작: 크레딧이 떨어지면 팀 전체 일시 정지(§2.1과 같은 문서). 자동 충전을 켜면 이를 피할 수 있다. https://docs.netlify.com/manage/accounts-and-billing/billing/resume-paused-projects/

#### 교체 계열 정보
§2.1과 같다.

#### 함정
Pro로 올려도 동기 60초는 그대로다. A2가 "수 분"이면 백그라운드 함수(15분) + 결과 폴링으로 구조를 바꾸거나 티어 1로 간다.

### 2.3 Netlify — Edge Functions
- 계열: 컴퓨트-티어0
- 서울 리전: `미확인`

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | 웹(요청 가로채기·응답 변환)만 | | https://docs.netlify.com/build/edge-functions/api/ · 2026-10-01 |
| CP.request_timeout | 요청당 CPU 50ms, 응답 헤더 타임아웃 40초 | | https://docs.netlify.com/build/edge-functions/limits/ · "CPU execution time per request: 50 ms" · 2026-10-01 |
| CP.long_connection | `미확인` (API 페이지에 "WebSocket API"가 있지만 들어오는 연결을 받는지는 명시 없음) | | https://docs.netlify.com/build/edge-functions/api/ · 2026-10-01 |
| CP.cpu_outside_request | `미확인` | | — |
| CP.cold_start | `미확인` | | — |
| CP.instance_size | 메모리 512MB | Deno 런타임. 네이티브 바이너리 패키지(Prisma 등)는 동작하지 않을 수 있음 | https://docs.netlify.com/build/edge-functions/limits/ · 2026-10-01 |
| CP.request_size | `미확인` | | — |
| CP.local_disk | 없음 (`미확인`, 파일 시스템 언급 없음) | | — ⚠️근거없음 |
| CP.scaling | `미확인` | | — |
| CP.concurrency | `미확인` | | — |
| CP.shutdown | `미확인` | | — |
| CP.deploy | 사이트 배포와 함께 원자적 배포·롤백 | | https://docs.netlify.com/deploy/manage-deploys/manage-deploys-overview/ · 2026-10-01 |
| CP.availability | `미확인` | | — |
| CP.networking | 고정 출구 IP 불가 | | https://docs.netlify.com/manage/security/private-connectivity/ · 2026-10-01 |
| CP.regions | `미확인` | | — |
| CP.plan_limits | 플랜별 차이 `미확인` | | — ⚠️근거없음 |
| CP.ops_burden | 서버 관리 없음 (추론) | | 추론 ⚠️근거없음 |
| CP.cost_floor | 크레딧 요금에 포함 | | https://www.netlify.com/pricing/ · 2026-10-01 |

#### 비용 구조
플랜 크레딧을 따른다.

#### 교체 계열 정보
Deno 기반이다. Next.js 미들웨어가 여기에 매핑되므로, 컨테이너에서는 Next.js 서버가 미들웨어를 직접 실행한다(추론). ⚠️근거없음

#### 함정
CPU 50ms는 인증 토큰 검증 정도만 감당한다. 무거운 로직이 미들웨어에 있으면 실패한다.

## 3. Cloudflare

Pages Functions는 Workers와 똑같이 과금되고 Free 하루 10만 요청을 함께 쓴다. 정적 자산 요청은 무료·무제한이다. Workers가 기능이 더 많고(Durable Objects, Cron), Pages는 폐지되지 않았다. https://developers.cloudflare.com/pages/functions/pricing/ · https://developers.cloudflare.com/workers/static-assets/migration-guides/migrate-from-pages/

### 3.1 Cloudflare Workers · Pages Functions — Free
- 계열: 컴퓨트-티어0
- 서울 리전: `미확인`. 요청에 가장 가까운 데이터센터에서 실행되고, 서울 데이터센터 존재 여부는 이번에 확인하지 않았다.

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | 웹(요청 처리), 크론 트리거. 상시 워커 없음 | 크론 트리거 계정당 5개 | https://developers.cloudflare.com/workers/platform/limits/ · 2026-10-01 |
| CP.request_timeout | CPU 요청당 10ms. 벽시계 시간은 클라이언트가 연결돼 있는 동안 제한 없음 | 크론·큐 소비자·DO 알람 벽시계 15분 | https://developers.cloudflare.com/workers/platform/limits/ · 2026-10-01 |
| CP.long_connection | `WebSocketPair`로 웹소켓 서버 가능. 방 단위 조정은 Durable Objects 권장. 연결 시간 한도 명시 없음 | | https://developers.cloudflare.com/workers/runtime-apis/websockets/ · 2026-10-01 |
| CP.cpu_outside_request | `waitUntil` 응답 후 30초(요청 안의 모든 호출이 공유), 넘으면 취소 | 더 긴 작업은 Queues 권장 | https://developers.cloudflare.com/workers/runtime-apis/context/ · "a 30-second time limit after invocation end" · 2026-10-01 |
| CP.cold_start | 사실상 없음(isolate 기동) | | https://developers.cloudflare.com/workers/reference/how-workers-works/ · "roughly 100 times faster than traditional Node processes" · 2026-10-01 |
| CP.instance_size | isolate당 메모리 128MB, Worker 크기 64MiB(압축 후 Free 한도는 `미확인`) | `worker_threads`·`child_process`는 동작하지 않는 스텁 | https://developers.cloudflare.com/workers/platform/limits/ · https://developers.cloudflare.com/workers/runtime-apis/nodejs/ · 2026-10-01 |
| CP.request_size | 요청 본문은 Cloudflare 계정 플랜을 따름: Free·Pro 100MB, Business 200MB, Enterprise 최대 5GB. 응답 한도 없음(캐시 512MB) | | https://developers.cloudflare.com/workers/platform/limits/ · 2026-10-01 |
| CP.local_disk | 메모리 가상 파일 시스템. `/tmp`는 요청마다 따로이고 영속 아님 | 영속 저장은 KV·D1·R2·DO | https://developers.cloudflare.com/workers/runtime-apis/nodejs/fs/ · "not persistent and unique to each request" · 2026-10-01 |
| CP.scaling | 최대 인스턴스 `미확인`. 하루 10만 요청 | 초과 시 오류 | https://developers.cloudflare.com/workers/platform/pricing/ · "further operations of that type will fail with an error" · 2026-10-01 |
| CP.concurrency | isolate 하나가 여러 요청을 동시에 처리. 두 요청이 같은 인스턴스로 간다는 보장 없음 → 전역 상태 신뢰 불가 | | https://developers.cloudflare.com/workers/reference/how-workers-works/ · 2026-10-01 |
| CP.shutdown | `미확인` (배포 중 진행 요청 처리 방식 미확인) | | — |
| CP.deploy | 트래픽 비율 기반 점진 배포, 사용자 버전 고정. 최근 100개 버전으로 롤백(DO 클래스 변경·바인딩 리소스 삭제가 사이에 있으면 불가) | | https://developers.cloudflare.com/workers/configuration/versions-and-deployments/gradual-deployments/ · https://developers.cloudflare.com/workers/configuration/versions-and-deployments/rollbacks/ · 2026-10-01 |
| CP.availability | 전 세계 데이터센터 분산 실행 (추론, how-workers-works) | | https://developers.cloudflare.com/workers/reference/how-workers-works/ · 2026-10-01 ⚠️근거없음 |
| CP.networking | DB: Hyperdrive(연결 풀링·쿼리 캐시, Free 포함), 사설 DB는 Workers VPC + Cloudflare Tunnel. 서브요청 50개, 동시 외부 연결 6개 | 고정 출구 IP: `fetch()`만 Dedicated CDN Egress IP 대상, `connect()`(TCP) 제외. 필요 플랜 `미확인` | https://developers.cloudflare.com/hyperdrive/ · https://developers.cloudflare.com/smart-shield/configuration/dedicated-egress-ips/other-products/ · 2026-10-01 |
| CP.regions | 요청에 가장 가까운 데이터센터. Smart Placement·배치 힌트로 백엔드 근처로 이동 가능(`aws:ap-northeast-2` 허용 여부 `미확인`) | | https://developers.cloudflare.com/workers/configuration/placement/ · 2026-10-01 |
| CP.plan_limits | 하루 10만 요청, CPU 10ms, 서브요청 50, 크론 5개(최소 1분, UTC, 변경 반영 최대 15분) | | https://developers.cloudflare.com/workers/platform/limits/ · https://developers.cloudflare.com/workers/configuration/cron-triggers/ · 2026-10-01 |
| CP.ops_burden | 서버 관리 없음. 대신 Workers 런타임 제약(Node 호환 플래그)에 맞춰 코드를 써야 함 (추론) | | 추론 ⚠️근거없음 |
| CP.cost_floor | $0 | | https://developers.cloudflare.com/workers/platform/pricing/ · 2026-10-01 |

#### 비용 구조
$0. 한도를 넘으면 과금되지 않고 오류가 난다.

#### 교체 계열 정보
- 런타임: Workers 런타임 API, `nodejs_compat`(호환 날짜 2026-08-04부터 기본). 컨테이너에서는 Node.js 표준 서버로 바꾼다.
- 바인딩: KV, D1, R2, Durable Objects, Queues, Hyperdrive → 각각 Redis/Postgres/S3 호환 스토리지/별도 실시간 서버/큐/직접 연결로 교체.
- `wrangler.toml`/`wrangler.jsonc`의 `triggers.crons` → 외부 스케줄러.
- Next.js: vinext(Next 16) 권장, OpenNext 어댑터도 문서에 있음. https://developers.cloudflare.com/workers/framework-guides/web-apps/nextjs/
- 종속 정도: 바인딩을 쓰면 높음, 순수 `fetch` 핸들러면 중간 (추론). ⚠️근거없음

#### 함정
비밀번호 해시(bcrypt), 이미지 처리, 큰 JSON 파싱은 Free의 CPU 10ms를 넘는다.

### 3.2 Cloudflare Workers · Pages Functions — Paid
- 계열: 컴퓨트-티어0
- 서울 리전: `미확인` (§3.1과 같음)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | 웹, 크론, Queues 소비자, Workflows(인스턴스가 영원히 실행 가능, sleep 최대 365일). 상시 워커 프로세스는 없음 | 크론 트리거 계정당 250개 | https://developers.cloudflare.com/workflows/reference/limits/ · "A Workflow instance can run forever" · 2026-10-01 |
| CP.request_timeout | CPU 기본 30초, 최대 5분. 벽시계는 연결 유지 중 제한 없음. 크론·큐 소비자·DO 알람 벽시계 15분 | | https://developers.cloudflare.com/workers/platform/limits/ · 2026-10-01 |
| CP.long_connection | `WebSocketPair` 가능, 조정은 Durable Objects | | https://developers.cloudflare.com/workers/runtime-apis/websockets/ · 2026-10-01 |
| CP.cpu_outside_request | `waitUntil` 응답 후 30초 | | https://developers.cloudflare.com/workers/runtime-apis/context/ · 2026-10-01 |
| CP.cold_start | 사실상 없음 | | https://developers.cloudflare.com/workers/reference/how-workers-works/ · 2026-10-01 |
| CP.instance_size | isolate당 128MB, Worker 64MiB | | https://developers.cloudflare.com/workers/platform/limits/ · 2026-10-01 |
| CP.request_size | 계정 플랜 따라 100MB~5GB | | https://developers.cloudflare.com/workers/platform/limits/ · 2026-10-01 |
| CP.local_disk | 요청마다 사라지는 메모리 FS | | https://developers.cloudflare.com/workers/runtime-apis/nodejs/fs/ · 2026-10-01 |
| CP.scaling | 최대 인스턴스 `미확인`. Queues 큐당 초당 5,000 메시지 | | https://developers.cloudflare.com/queues/platform/limits/ · 2026-10-01 |
| CP.concurrency | isolate 공유, 인스턴스 고정 보장 없음 | | https://developers.cloudflare.com/workers/reference/how-workers-works/ · 2026-10-01 |
| CP.shutdown | `미확인` | | — |
| CP.deploy | 점진 배포, 100개 버전 롤백 | | https://developers.cloudflare.com/workers/configuration/versions-and-deployments/gradual-deployments/ · 2026-10-01 |
| CP.availability | 전 세계 분산 (추론) | | https://developers.cloudflare.com/workers/reference/how-workers-works/ · 2026-10-01 ⚠️근거없음 |
| CP.networking | Hyperdrive, Workers VPC + Tunnel. 서브요청 10,000. 고정 IP는 `fetch()`만 | | https://developers.cloudflare.com/hyperdrive/configuration/connect-to-private-database-vpc/ · 2026-10-01 |
| CP.regions | 가장 가까운 데이터센터, Smart Placement | | https://developers.cloudflare.com/workers/configuration/placement/ · 2026-10-01 |
| CP.plan_limits | 크론 최소 1분. 크론 CPU: 1시간 미만 주기는 30초, 1시간 이상 주기는 15분(재료 W-062 값, 이번에 limits 페이지에서 15분 벽시계만 재확인) | Queues 메시지 128KB, 보존 최대 14일, 재시도 100회 | https://developers.cloudflare.com/workers/configuration/cron-triggers/ · https://developers.cloudflare.com/queues/platform/limits/ · 2026-10-01 |
| CP.ops_burden | 서버 관리 없음 (추론) | | 추론 ⚠️근거없음 |
| CP.cost_floor | 월 $5. 요청 1,000만 포함 후 100만당 $0.30, CPU 3,000만 ms 포함 후 100만 ms당 $0.02. Queues 100만 작업당 $0.40 | | https://developers.cloudflare.com/workers/platform/pricing/ · "$5 USD per month" · 2026-10-01 |

#### 비용 구조
최소 월 $5, 요청 수와 CPU 시간 비례.
지출 한도 동작: **상한이 없다.** 예산 알림은 정보 제공용이고 사용을 멈추지 않는다. https://developers.cloudflare.com/billing/manage/budget-alerts/ · "Budget alerts are informational only. They do not pause or cap usage."

#### 교체 계열 정보
§3.1과 같다. Workflows(`step.do`, `step.sleep`)는 컨테이너 환경에서 Temporal류 워크플로 엔진이나 DB 기반 작업 큐로 바꿔야 한다(추론). ⚠️근거없음

#### 함정
CPU 시간 한도는 벽시계가 아니다. 외부 API 응답을 오래 기다리는 작업은 유리하고, CPU를 쓰는 작업은 5분에서 끊긴다.

### 3.3 Cloudflare — Durable Objects
- 계열: 컴퓨트-티어0 (상태가 있는 단일 조정자. 실시간 계열 능력도 겸함)
- 서울 리전: 지정 불가. 위치 힌트에 `apac`·`apac-ne`·`apac-se`가 있다. https://developers.cloudflare.com/durable-objects/reference/data-location/

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | 객체 단위 상주 조정자(웹소켓 방, 동시 편집), 알람으로 정기 실행 | Free는 SQLite 기반 객체만 | https://developers.cloudflare.com/durable-objects/platform/limits/ · 2026-10-01 |
| CP.request_timeout | CPU 기본 30초, 최대 5분. 알람 벽시계 15분 | | https://developers.cloudflare.com/durable-objects/platform/limits/ · 2026-10-01 |
| CP.long_connection | 웹소켓 + 하이버네이션: 객체가 메모리에서 빠져도 연결 유지, 그동안 Duration 과금 없음. **코드 업데이트 시 모든 웹소켓 끊김.** 연결별 첨부 데이터 최대 16,384바이트 | 객체당 최대 웹소켓 수 `미확인` | https://developers.cloudflare.com/durable-objects/best-practices/websockets/ · "Code updates disconnect all WebSockets." / "Billable Duration (GB-s) charges do not accrue" · 2026-10-01 |
| CP.cpu_outside_request | 알람으로 요청 밖 실행 | | https://developers.cloudflare.com/workers/platform/limits/ · 2026-10-01 |
| CP.cold_start | 하이버네이션 후 재활성 지연 `미확인` | | — ⚠️근거없음 |
| CP.instance_size | 객체당 초당 약 1,000 요청(소프트). 메모리 128MB(Workers와 같음, 추론) | | https://developers.cloudflare.com/durable-objects/platform/limits/ · 2026-10-01 ⚠️근거없음 |
| CP.request_size | 수신 메시지 최대 32MiB | | https://developers.cloudflare.com/durable-objects/platform/limits/ · 2026-10-01 |
| CP.local_disk | 객체당 SQLite 저장소 10GB(Free 1GB), 영속 | | https://developers.cloudflare.com/durable-objects/platform/limits/ · 2026-10-01 |
| CP.scaling | 객체 수로 수평 확장, 한 객체는 단일 스레드 (추론, 초당 1,000 요청 소프트 한도) | | https://developers.cloudflare.com/durable-objects/platform/limits/ · 2026-10-01 ⚠️근거없음 |
| CP.concurrency | 객체 하나는 한 곳에서 한 번에 하나의 버전만 실행 | | https://developers.cloudflare.com/workers/configuration/versions-and-deployments/gradual-deployments/ · 2026-10-01 |
| CP.shutdown | `미확인` (배포 시 웹소켓 끊김은 확인) | | https://developers.cloudflare.com/durable-objects/best-practices/websockets/ · 2026-10-01 |
| CP.deploy | 점진 배포 중에도 객체당 버전 하나. DO 클래스 변경 전으로는 롤백 불가 | | https://developers.cloudflare.com/workers/configuration/versions-and-deployments/rollbacks/ · 2026-10-01 |
| CP.availability | 생성 후 위치가 바뀌지 않음 → 객체 하나는 한 곳에만 있음 | | https://developers.cloudflare.com/durable-objects/reference/data-location/ · "do not currently change locations after they are created" · 2026-10-01 |
| CP.networking | Workers와 같음 | | https://developers.cloudflare.com/hyperdrive/ · 2026-10-01 |
| CP.regions | 위치 힌트(`apac-ne` 등), 관할(eu, us, fedramp). 서울 지정 없음 | | https://developers.cloudflare.com/durable-objects/reference/data-location/ · 2026-10-01 |
| CP.plan_limits | Free: SQLite 기반만, 1GB | | https://developers.cloudflare.com/durable-objects/platform/limits/ · 2026-10-01 |
| CP.ops_burden | 서버 없음. 객체 분할 설계 필요 (추론) | | 추론 ⚠️근거없음 |
| CP.cost_floor | Workers Paid $5에 포함. 100만 요청당 $0.15, 100만 GB-초당 $12.50, SQLite GB-월 $0.20 | | https://developers.cloudflare.com/workers/platform/pricing/ · 2026-10-01 |

#### 비용 구조
요청·Duration·저장 과금. 하이버네이션을 쓰지 않으면 유휴 연결에도 Duration이 쌓인다.

#### 교체 계열 정보
DO는 다른 플랫폼에 같은 개념이 없다. 컨테이너로 옮기면 웹소켓 서버 + Redis pub/sub + 외부 DB로 다시 설계한다(추론). 종속 정도 높음. ⚠️근거없음

#### 함정
배포할 때마다 모든 웹소켓이 끊긴다. 배포가 잦은 실시간 앱은 재연결 폭풍(재료 W-003) 처리가 필수다.

### 3.4 Cloudflare — Containers (Workers Paid)
- 계열: 컴퓨트-티어0 (Worker 코드가 제어하는 컨테이너)
- 서울 리전: `미확인`. "Region:Earth"에 배포되고 위치를 직접 지정하는 방법은 확인하지 못했다. https://developers.cloudflare.com/containers/

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | 컨테이너(웹·작업). Durable Object를 통해 Worker 코드가 시작·제어. 2026-04-13 GA | Workers Paid 전용 | https://developers.cloudflare.com/changelog/post/2026-04-13-containers-sandbox-ga/ · "Containers and Sandboxes are now generally available." · 2026-10-01 |
| CP.request_timeout | 앞단 Worker·DO 한도를 따름 (추론). 컨테이너 자체 요청 한도 `미확인` | | — ⚠️근거없음 |
| CP.long_connection | DO를 통해 웹소켓 전달 가능 (추론, 공식 인용 `미확인`) | | — ⚠️근거없음 |
| CP.cpu_outside_request | 컨테이너가 실행 중이면 가능, 실행 중인 시간 과금 | | https://developers.cloudflare.com/containers/pricing/ · 2026-10-01 |
| CP.cold_start | 보통 1~3초 | | https://developers.cloudflare.com/containers/platform-details/architecture/ · 2026-10-01 |
| CP.instance_size | lite(1/16 vCPU, 256MiB, 디스크 2GB) ~ standard-4(4 vCPU, 12GiB, 20GB). 사용자 지정은 vCPU당 3GiB 이상. 계정 상한 메모리 6TiB, vCPU 1,500 | | https://developers.cloudflare.com/containers/platform-details/limits/ · 2026-10-01 |
| CP.request_size | 앞단 Worker 한도 (추론) | | — ⚠️근거없음 |
| CP.local_disk | 임시. 재시작하면 이미지에서 새 디스크 | | https://developers.cloudflare.com/containers/platform-details/architecture/ · "fresh disk from the container image" · 2026-10-01 |
| CP.scaling | 컨테이너 클래스마다 최대 인스턴스 수 지정 | | https://developers.cloudflare.com/containers/ · 2026-10-01 |
| CP.concurrency | `미확인` | | — |
| CP.shutdown | SIGTERM 후 최대 15분 대기, 그다음 SIGKILL | | https://developers.cloudflare.com/containers/platform-details/architecture/ · "waits up to 15 minutes" · 2026-10-01 |
| CP.deploy | 배포 시 Worker 코드가 컨테이너 롤아웃보다 먼저 반영됨 | 신·구 버전 불일치 구간 생김 | https://developers.cloudflare.com/containers/platform-details/architecture/ · 2026-10-01 |
| CP.availability | 컨테이너와 그 DO가 같은 위치에서 실행된다는 보장 없음 | | https://developers.cloudflare.com/containers/platform-details/architecture/ · 2026-10-01 |
| CP.networking | `미확인` | | — |
| CP.regions | "Region:Earth" | | https://developers.cloudflare.com/containers/ · 2026-10-01 |
| CP.plan_limits | Workers Paid 전용 | | https://developers.cloudflare.com/changelog/post/2026-04-13-containers-sandbox-ga/ · 2026-10-01 |
| CP.ops_burden | 이미지 관리 + DO 제어 코드 작성 (추론) | | 추론 ⚠️근거없음 |
| CP.cost_floor | 10ms 단위 과금. 메모리 25GiB-시간/월 포함 후 GiB-초당 $0.0000025, CPU 375 vCPU-분 포함 후 vCPU-초당 $0.000020(활성 사용만), 디스크 200GB-시간 포함 후 GB-초당 $0.00000007. 이그레스 북미·유럽 $0.025/GB(1TB 포함), 그 외 $0.04~0.05/GB | Workers Paid 월 $5 필요 | https://developers.cloudflare.com/containers/pricing/ · 2026-10-01 |

#### 비용 구조
월 $5 + 실행 시간 비례. 지출 상한 없음(§3.2).

#### 교체 계열 정보
컨테이너 이미지 자체는 이식된다. 바뀌는 것은 앞단 Worker·DO 제어 코드와 바인딩뿐이다. 종속 정도 낮음~중간 (추론). ⚠️근거없음

#### 함정
디스크가 재시작마다 초기화되므로 SQLite·업로드 저장 용도로 쓸 수 없다.

## 4. Railway

서울·도쿄 리전이 없다. 리전은 `us-west2`(캘리포니아), `us-east4-eqdc4a`(버지니아), `europe-west4-drams3a`(암스테르담), `asia-southeast1-eqsg3a`(싱가포르) 4곳이다. https://docs.railway.com/reference/deployment-regions

### 4.1 Railway — Free · Trial
- 계열: 컴퓨트-티어0
- 서울 리전: 없음 (가장 가까운 곳 싱가포르)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | 상시 컨테이너(웹·워커), 크론 서비스 | 크론은 최소 5분 간격, 이전 실행이 남아 있으면 건너뜀, 작업 후 종료해야 함 | https://docs.railway.com/reference/cron-jobs · "Scheduled runs must be at least 5 minutes apart in UTC." / "Railway will skip the new cron job." · 2026-10-01 |
| CP.request_timeout | 데이터가 오가면 최대 15분, 5분간 전송 없으면 닫힘 | 요청 사이 유휴 HTTP/1.1 연결은 60초 | https://docs.railway.com/networking/public-networking/specs-and-limits · "HTTP requests can run for up to 15 minutes if data keeps transferring" / "closed after 5 minutes with no data transferred" · 2026-10-01 |
| CP.long_connection | 웹소켓 무기한(유휴여도) | 도메인당 동시 연결 1만, 약 초당 11,000 요청 | https://docs.railway.com/networking/public-networking/specs-and-limits · "can stay open indefinitely, even while idle" · 2026-10-01 |
| CP.cpu_outside_request | 가능(상시 컨테이너, 추론). 서버리스(앱 슬리핑)를 켜면 아웃바운드 트래픽이 없을 때 잠듦 | | https://docs.railway.com/reference/app-sleeping · 2026-10-01 ⚠️근거없음 |
| CP.cold_start | 기본 상시 실행. 슬리핑을 켜면 마지막 아웃바운드 후 5~10분 뒤 잠들고 첫 요청 지연(502 가능) | | https://docs.railway.com/reference/app-sleeping · "a service sleeps somewhere between 5 and 10 minutes after its last outbound traffic" · 2026-10-01 |
| CP.instance_size | Free 서비스당 0.5GB RAM·1 vCPU, Trial 1GB·2 vCPU. GPU `미확인` | | https://docs.railway.com/reference/pricing/plans · 2026-10-01 |
| CP.request_size | 크기 한도 명시 없음. 본문은 5분 안에 업로드 완료, 헤더 합계 32KB | | https://docs.railway.com/networking/public-networking/specs-and-limits · "Request bodies must finish uploading within 5 minutes." · 2026-10-01 |
| CP.local_disk | 임시 저장 1GB. 볼륨 0.5GB. 볼륨을 붙이면 레플리카 불가, 서비스당 볼륨 1개, 재배포 시 짧은 다운타임 | | https://docs.railway.com/reference/pricing/plans · https://docs.railway.com/reference/volumes · "Replicas cannot be used with volumes" · 2026-10-01 |
| CP.scaling | 레플리카 Free 1, Trial 2. 수동 수평 확장만, 자동 수평 확장 문서 없음 | | https://docs.railway.com/reference/scaling · "Scale horizontally by manually increasing the number of replicas" · 2026-10-01 |
| CP.concurrency | 해당 없음(앱 프로세스가 처리) | | — |
| CP.shutdown | SIGTERM 후 기본 0초 만에 SIGKILL. `RAILWAY_DEPLOYMENT_DRAINING_SECONDS`로 조정(최대 `미확인`) | | https://docs.railway.com/reference/deployments · "By default, it is given 0 seconds to gracefully shutdown before being forcefully stopped with a SIGKILL." · 2026-10-01 |
| CP.deploy | 헬스체크 통과 후 `Active`로 전환(무중단). 플랜 보존 기간 안의 배포로 롤백. 트래픽 분할 `미확인` | 볼륨이 있으면 재배포 시 다운타임 | https://docs.railway.com/reference/deployments · "Railway will mark the deployment as `Active` when the healthcheck succeeds" · 2026-10-01 |
| CP.availability | 레플리카 1개라 존 분산 불가 (추론) | | https://docs.railway.com/reference/pricing/plans · 2026-10-01 ⚠️근거없음 |
| CP.networking | 사설 네트워크 `*.railway.internal`(WireGuard). 고정 출구 IP 불가(Pro 전용) | | https://docs.railway.com/reference/private-networking · https://docs.railway.com/reference/static-outbound-ips · 2026-10-01 |
| CP.regions | 서울 없음 | | https://docs.railway.com/reference/deployment-regions · 2026-10-01 |
| CP.plan_limits | Trial 1회성 $5 크레딧. Free "$0 / month", "For running small apps". 상업 이용 조항 `미확인` | 크레딧 소진 시 워크로드 정지 | https://docs.railway.com/reference/pricing/plans · "we will stop all of your workloads" · 2026-10-01 |
| CP.ops_burden | 낮음. Railpack이 설정 없이 소스에서 빌드 | | https://docs.railway.com/reference/railpack · 2026-10-01 |
| CP.cost_floor | $0. 단가: RAM GB당 월 $10, vCPU당 월 $20, 이그레스 GB당 $0.05, 볼륨 GB당 월 $0.15 | | https://docs.railway.com/reference/pricing/plans · "$10 / GB / month" · 2026-10-01 |

#### 비용 구조
$0, 크레딧 범위 안에서만 실행. 상시 컨테이너 0.5vCPU·512MB는 단가 계산상 약 월 $15(재료 W-070의 추정, 추론). ⚠️근거없음

#### 교체 계열 정보
- 이미 컨테이너라 코드 변경은 적다. 빌드는 Railpack → Dockerfile.
- 플랫폼 환경변수: `RAILWAY_PUBLIC_DOMAIN`, `RAILWAY_PRIVATE_DOMAIN`, `RAILWAY_REPLICA_ID`, `RAILWAY_VOLUME_MOUNT_PATH`, `RAILWAY_TCP_PROXY_*`. https://docs.railway.com/reference/variables
- 내부 DNS `*.railway.internal` → 대상 플랫폼의 서비스 디스커버리.
- 볼륨 데이터 이전.
- 종속 정도: 낮음.

#### 함정
- 종료 유예 기본 0초: 배포마다 진행 중 요청이 끊긴다.
- 레플리카 1개 + 볼륨 → 무중단·확장 모두 불가.

### 4.2 Railway — Hobby
- 계열: 컴퓨트-티어0
- 서울 리전: 없음

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | 웹·워커·크론(최소 5분) | | https://docs.railway.com/reference/cron-jobs · 2026-10-01 |
| CP.request_timeout | 15분, 무전송 5분 | | https://docs.railway.com/networking/public-networking/specs-and-limits · 2026-10-01 |
| CP.long_connection | 웹소켓 무기한 | | https://docs.railway.com/networking/public-networking/specs-and-limits · 2026-10-01 |
| CP.cpu_outside_request | 가능(상시 컨테이너, 추론) | | — ⚠️근거없음 |
| CP.cold_start | 기본 상시. 슬리핑 선택 시 5~10분 후 잠듦 | | https://docs.railway.com/reference/app-sleeping · 2026-10-01 |
| CP.instance_size | 서비스당 최대 48GB RAM·48 vCPU | | https://docs.railway.com/reference/pricing/plans · 2026-10-01 |
| CP.request_size | 5분 안 업로드, 헤더 32KB | | https://docs.railway.com/networking/public-networking/specs-and-limits · 2026-10-01 |
| CP.local_disk | 임시 100GB. 볼륨 5GB. 볼륨 부착 시 레플리카 불가·재배포 다운타임. 증설은 무중단, 축소 불가 | 볼륨 백업 수동·자동 | https://docs.railway.com/reference/volumes · "there will be a small amount of downtime when re-deploying a service that has a volume attached, even if there is a healthcheck endpoint configured" · 2026-10-01 |
| CP.scaling | 레플리카 6. 수동 수평 확장, 멀티 리전 레플리카 가능 | | https://docs.railway.com/reference/pricing/plans · https://docs.railway.com/reference/scaling · 2026-10-01 |
| CP.concurrency | 해당 없음 | | — |
| CP.shutdown | 기본 0초, `RAILWAY_DEPLOYMENT_DRAINING_SECONDS`로 조정 | | https://docs.railway.com/reference/deployments · 2026-10-01 |
| CP.deploy | 헬스체크 기반 무중단, 롤백 | | https://docs.railway.com/reference/deployments · 2026-10-01 |
| CP.availability | 레플리카 여러 개·멀티 리전 가능. 리전 안 멀티 존 `미확인` | | https://docs.railway.com/reference/scaling · 2026-10-01 |
| CP.networking | 사설 네트워크. 고정 출구 IP 불가 | | https://docs.railway.com/reference/static-outbound-ips · 2026-10-01 |
| CP.regions | 서울 없음 | | https://docs.railway.com/reference/deployment-regions · 2026-10-01 |
| CP.plan_limits | 월 $5(사용량 $5 포함) | | https://docs.railway.com/reference/pricing/plans · 2026-10-01 |
| CP.ops_burden | 낮음 | | https://docs.railway.com/reference/railpack · 2026-10-01 |
| CP.cost_floor | 월 $5, 구독료는 항상 청구 | 하드 한도 최소 $10 | https://docs.railway.com/reference/pricing/plans · "always pay the $5 subscription fee" · https://docs.railway.com/reference/usage-limits · 2026-10-01 |

#### 비용 구조
월 $5 + 사용량($5 포함 후). 지출 한도 동작: 하드 한도에 닿으면 **모든 워크로드가 오프라인**이 된다. 소프트 알림(75/90/100%)은 리소스에 영향이 없다. https://docs.railway.com/reference/usage-limits · "all your workloads will be taken offline"

#### 교체 계열 정보
§4.1과 같다.

#### 함정
하드 한도는 비용 통제가 전체 장애로 바뀌는 지점이다.

### 4.3 Railway — Pro
- 계열: 컴퓨트-티어0
- 서울 리전: 없음

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | 웹·워커·크론(최소 5분) | | https://docs.railway.com/reference/cron-jobs · 2026-10-01 |
| CP.request_timeout | 15분, 무전송 5분 | | https://docs.railway.com/networking/public-networking/specs-and-limits · 2026-10-01 |
| CP.long_connection | 웹소켓 무기한 | | https://docs.railway.com/networking/public-networking/specs-and-limits · 2026-10-01 |
| CP.cpu_outside_request | 가능(추론) | | — ⚠️근거없음 |
| CP.cold_start | 기본 상시 | | https://docs.railway.com/reference/app-sleeping · 2026-10-01 |
| CP.instance_size | 서비스 합계 1TB RAM·1,000 vCPU, 레플리카당 24 vCPU·24GB | | https://docs.railway.com/reference/scaling · "each of your replicas can utilize up to 24 vCPU and 24GB of memory" · 2026-10-01 |
| CP.request_size | 5분 안 업로드 | | https://docs.railway.com/networking/public-networking/specs-and-limits · 2026-10-01 |
| CP.local_disk | 임시 100GB. 볼륨 `[충돌]` 요금 페이지 1TB, 볼륨 페이지 50GB. 부착 시 레플리카 불가·재배포 다운타임 | | https://docs.railway.com/reference/pricing/plans · https://docs.railway.com/reference/volumes · 2026-10-01 |
| CP.scaling | 레플리카 42, 수동 | | https://docs.railway.com/reference/pricing/plans · 2026-10-01 |
| CP.concurrency | 해당 없음 | | — |
| CP.shutdown | 기본 0초, 조정 가능 | | https://docs.railway.com/reference/deployments · 2026-10-01 |
| CP.deploy | 헬스체크 기반 무중단, 롤백 | | https://docs.railway.com/reference/deployments · 2026-10-01 |
| CP.availability | 멀티 리전 레플리카(가장 가까운 리전으로 보낸 뒤 레플리카에 무작위 분배) | | https://docs.railway.com/reference/scaling · 2026-10-01 |
| CP.networking | 고정 출구 IPv4(다른 고객과 공유될 수 있고 리전을 옮기면 바뀜) | | https://docs.railway.com/reference/static-outbound-ips · "Static Outbound IPs let customers on the Pro plan assign permanent outbound IPv4 addresses" · 2026-10-01 |
| CP.regions | 서울 없음 | | https://docs.railway.com/reference/deployment-regions · 2026-10-01 |
| CP.plan_limits | 월 $20(사용량 $20 포함) | | https://docs.railway.com/reference/pricing/plans · 2026-10-01 |
| CP.ops_burden | 낮음 | | — ⚠️근거없음 |
| CP.cost_floor | 월 $20 | | https://docs.railway.com/reference/pricing/plans · 2026-10-01 |

#### 비용 구조
월 $20 + 사용량. 지출 한도 동작은 Hobby와 같다(하드 한도 시 전체 오프라인).

#### 교체 계열 정보
§4.1과 같다.

#### 함정
고정 IP가 전용이 아닐 수 있어, 상대방 허용 목록이 "우리만의 IP"를 요구하면 맞지 않는다.

## 7. Firebase

Firebase의 컴퓨트는 모두 종량제 Blaze 플랜이 필요하다. 예산 알림은 서비스를 멈추지 않는다. 별도로 켜는 "spend cap budget"은 App Hosting·Cloud Functions·AI Logic·Extensions에 적용되고, 100%에 닿으면 그달 남은 기간 해당 서비스를 정지한다. https://firebase.google.com/docs/projects/billing/avoid-surprise-bills · "Budget alerts do not pause services" / "pause that service for the rest of the month"

### 7.1 Firebase App Hosting — Blaze
- 계열: 컴퓨트-티어0 (Cloud Build + Cloud Run + Cloud CDN)
- 서울 리전: 없음. us-central1, us-east4, us-east5, asia-east1(대만), asia-southeast1(싱가포르), europe-west4만. https://firebase.google.com/docs/app-hosting/about-app-hosting

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | 웹만(Node.js 앱). 워커·크론 기능 문서 없음 | | https://firebase.google.com/docs/app-hosting/frameworks-tooling · "your Node.js app runs in a Cloud Run revision" · 2026-10-01 |
| CP.request_timeout | `미확인` (`runConfig`에 타임아웃 키 없음) | | https://firebase.google.com/docs/app-hosting/configure · 2026-10-01 |
| CP.long_connection | `미확인` | | — |
| CP.cpu_outside_request | `미확인` | | — |
| CP.cold_start | `minInstances` 기본 0(scale-to-zero), 설정으로 상시 유지 | | https://firebase.google.com/docs/app-hosting/configure · "minInstances – Number of containers to always keep alive (default 0)" · 2026-10-01 |
| CP.instance_size | 메모리 128~32,768MiB(기본 512). 4GiB 초과는 CPU 2 이상, 24GiB 초과는 CPU 8 이상. `cpu` 기본값 문서 표기 "default 0"(오기로 보임). CPU 1 미만이면 동시성 1 | | https://firebase.google.com/docs/app-hosting/configure · "memoryMiB … (default 512)" · 2026-10-01 |
| CP.request_size | `미확인` | | — |
| CP.local_disk | `미확인`, 볼륨 옵션 없음 | | https://firebase.google.com/docs/app-hosting/configure · 2026-10-01 |
| CP.scaling | `maxInstances` 기본 100 | | https://firebase.google.com/docs/app-hosting/configure · "(default of 100)" · 2026-10-01 |
| CP.concurrency | 인스턴스당 기본 80 | | https://firebase.google.com/docs/app-hosting/configure · "Maximum number of requests that each serving instance can receive (default 80)" · 2026-10-01 |
| CP.shutdown | `미확인` | | — |
| CP.deploy | 라이브 브랜치에 푸시하면 자동 롤아웃. 새 리비전이 정상이면 트래픽 전환. 재빌드 없이 즉시 롤백. 트래픽 분할 언급 없음 | | https://firebase.google.com/docs/app-hosting/rollouts · "Roll back instantly without rebuilding" · https://firebase.google.com/docs/app-hosting/about-app-hosting · 2026-10-01 |
| CP.availability | `미확인` | | — |
| CP.networking | `vpcAccess`로 direct VPC egress 또는 서버리스 커넥터. 고정 출구 IP `미확인` | | https://firebase.google.com/docs/app-hosting/configure · "direct VPC egress or serverless connector" · 2026-10-01 |
| CP.regions | 서울·도쿄 없음 | | https://firebase.google.com/docs/app-hosting/about-app-hosting · 2026-10-01 |
| CP.plan_limits | Blaze 필수(Spark 불가). Next.js 13.5+, Angular 18.2+ 사전 구성, 그 외는 어댑터 필요 | | https://firebase.google.com/docs/app-hosting/costs · "App Hosting requires a project that's on the pay-as-you-go Blaze pricing plan" · 2026-10-01 |
| CP.ops_burden | 낮음(git push → Cloud Native Buildpacks 빌드) | | https://firebase.google.com/docs/app-hosting/frameworks-tooling · 2026-10-01 |
| CP.cost_floor | `minInstances` 0이면 고정비 $0. 월 무료: vCPU-초 18만, GiB-초 36만, 요청 200만, 빌드 2,500분, 이그레스 10GiB. 이그레스 캐시 GiB당 $0.15, 비캐시 $0.20. 예시: 방문 1만 약 $0.01, 100만 약 $69.58 | | https://firebase.google.com/docs/app-hosting/costs · 2026-10-01 |

#### 비용 구조
고정비 $0(최소 인스턴스 0일 때), 사용량 비례. 지출 한도 동작은 §7 머리말 참고.

#### 교체 계열 정보
- 결과물이 Cloud Run 위 Node 앱이므로 Cloud Run(티어 1)으로 가는 이전 비용이 가장 낮다(추론). ⚠️근거없음
- `apphosting.yaml`/`apphosting.<env>.yaml`의 `runConfig`·환경변수 → 대상 플랫폼 설정. 비밀은 Cloud Secret Manager.
- 종속 정도: 낮음 (추론). ⚠️근거없음

#### 함정
서울이 없다. 한국 사용자·서울 DB면 대만(asia-east1)이 가장 가깝다.

### 7.2 Cloud Functions for Firebase — Blaze (2세대·1세대)
- 계열: 컴퓨트-티어0 (2세대는 Cloud Run + Eventarc 기반)
- 서울 리전: 있음. `asia-northeast3`(1세대·2세대). 이벤트 함수는 리전을 지정하지 않으면 `us-central1`. https://firebase.google.com/docs/functions/locations

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | HTTP 함수, 이벤트 함수, 정기 함수(Cloud Scheduler가 호출). 상시 워커 없음 | | https://firebase.google.com/docs/functions/schedule-functions · "a scheduler job and an HTTP function are created automatically" · 2026-10-01 |
| CP.request_timeout | 2세대 HTTP 60분, 이벤트 540초. 1세대 540초. **Firebase Hosting rewrite로 호출하면 60초** | | https://firebase.google.com/docs/functions/quotas · "60 minutes for HTTP functions" · https://firebase.google.com/docs/hosting/functions · "Firebase Hosting is subject to a 60-second request timeout." · 2026-10-01 |
| CP.long_connection | `미확인`. 아웃바운드 유휴 타임아웃: VPC 10분, 인터넷 20분 | | https://firebase.google.com/docs/functions/networking · 2026-10-01 |
| CP.cpu_outside_request | 없음 | | https://firebase.google.com/docs/functions/tips · "Any code run after graceful termination cannot access the CPU and will not make any progress" · 2026-10-01 |
| CP.cold_start | 최소 인스턴스 설정 가능, 없으면 scale-to-zero | | https://firebase.google.com/docs/functions/manage-functions · "set a minimum number of container instances to be kept warm" · 2026-10-01 |
| CP.instance_size | `[충돌]` 할당량 페이지: 2세대 32GiB, 1세대 8GiB. 버전 비교 페이지: 2세대 16GiB/4vCPU, 1세대 8GB/2vCPU | | https://firebase.google.com/docs/functions/quotas · https://firebase.google.com/docs/functions/version-comparison · "Up to 16GiB RAM with 4 vCPU" · 2026-10-01 |
| CP.request_size | 요청 2세대 32MB, 1세대 10MB. 2세대 응답 비스트리밍 32MB, 스트리밍 10MB. Eventarc 이벤트 512KB | | https://firebase.google.com/docs/functions/quotas · 2026-10-01 |
| CP.local_disk | 메모리를 쓰는 임시 파일, 때때로 호출 사이에 남음. 볼륨 없음 | | https://firebase.google.com/docs/functions/tips · "Files that you write consume memory available to your function" · 2026-10-01 |
| CP.scaling | 리전당 함수 1,000개(2세대는 Cloud Run 서비스 수만큼 차감). 1세대 백그라운드 동시 호출 3,000. 최대 인스턴스 설정 | | https://firebase.google.com/docs/functions/quotas · 2026-10-01 |
| CP.concurrency | 2세대 인스턴스당 최대 1,000, 1세대 1. 기본값 `미확인` | | https://firebase.google.com/docs/functions/version-comparison · "Up to 1000 concurrent requests per function instance" · 2026-10-01 |
| CP.shutdown | 유예 시간 `미확인` | | https://firebase.google.com/docs/functions/tips · 2026-10-01 |
| CP.deploy | 2세대 리비전 간 트래픽 분할. 롤백 방법 `미확인` | | https://firebase.google.com/docs/functions/version-comparison · "Ability to split traffic between revisions" · 2026-10-01 |
| CP.availability | `미확인` | | — |
| CP.networking | 전역 클라이언트 재사용 권장. VPC·고정 IP `미확인` | | https://firebase.google.com/docs/functions/networking · 2026-10-01 |
| CP.regions | 서울 `asia-northeast3` 있음(Tier 2 가격) | | https://firebase.google.com/docs/functions/locations · "You are encouraged to set specific regions instead of relying on Firebase defaults" · 2026-10-01 |
| CP.plan_limits | Blaze 필수. 정기 함수는 이전 실행이 끝나기 전에 다음이 실행될 수 있음. 최소 주기 `미확인` | | https://firebase.google.com/docs/functions/quotas · "your project be on the Blaze pricing plan" · https://firebase.google.com/docs/functions/schedule-functions · "a function may be triggered multiple times" · 2026-10-01 |
| CP.ops_burden | 낮음 | | — ⚠️근거없음 |
| CP.cost_floor | 고정비 $0. 월 무료: 호출 200만(이후 100만당 $0.40), GB-초 40만, CPU-초 20만, 이그레스 5GB(이후 GB당 $0.12). Scheduler 작업당 월 $0.10, 계정당 3개 무료 | | https://firebase.google.com/pricing · https://firebase.google.com/docs/functions/schedule-functions · "$0.10 (USD) per month" · 2026-10-01 |

#### 비용 구조
고정비 $0, 종량제. 무료(Spark)로 시작한 프로젝트도 함수를 추가하면 결제 수단 등록이 필요하다.

#### 교체 계열 정보
- `firebase-functions` 트리거(`onRequest`, `onDocumentWritten`, `onSchedule`, `firebase-functions/v2`) → 일반 HTTP 서버와 Eventarc/PubSub 푸시 엔드포인트로 바꾼다(추론). ⚠️근거없음
- `RuntimeOptions`, `onInit()` 훅 → 서버 기동 코드.
- 종속 정도: HTTP만 쓰면 낮음, Firestore·Auth 이벤트 트리거가 많으면 높음 (추론). ⚠️근거없음

#### 함정
- Hosting rewrite 뒤의 함수는 60분이 아니라 60초다.
- 응답 후 CPU가 없어서, 응답 뒤 메일 발송 같은 fire-and-forget 작업은 실행되지 않는다.

## 8. Supabase Edge Functions

Deno 기반 V8 isolate이며 호출마다 새 isolate가 뜬다. https://supabase.com/docs/guides/functions/architecture

### 8.1 Supabase Edge Functions — Free
- 계열: 컴퓨트-티어0
- 서울 리전: 있음(`ap-northeast-2`를 `x-region` 헤더나 `forceFunctionRegion`으로 지정). 기본은 사용자에게 가장 가까운 리전. https://supabase.com/docs/guides/functions/regional-invocation

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | HTTP 함수만. 정기 실행은 Postgres `pg_cron` + `pg_net`으로 함수 호출 | 1분 미만 주기 `미확인` | https://supabase.com/docs/guides/functions/schedule-functions · "In combination with the pg_net extension, this allows us to invoke Edge Functions periodically" · 2026-10-01 |
| CP.request_timeout | 벽시계 150초, CPU 2초(비동기 I/O 제외), 요청 유휴 150초(응답을 시작하지 않으면 504) | | https://supabase.com/docs/guides/functions/limits · "Free plan: 150s" / "Maximum CPU Time: 2s" / "Request idle timeout: 150s" · 2026-10-01 |
| CP.long_connection | 웹소켓 서버 가능. 지속 시간은 벽시계·CPU·메모리 한도에 묶임(150초). 브라우저는 인증 헤더를 못 보내 JWT를 쿼리·프로토콜로 전달 | | https://supabase.com/docs/guides/functions/websockets · "Edge Functions supports hosting WebSocket servers" · 2026-10-01 |
| CP.cpu_outside_request | `EdgeRuntime.waitUntil(promise)`, 한도 안에서 | | https://supabase.com/docs/guides/functions/background-tasks · "The Function instance continues to run until the promise provided to waitUntil completes" · 2026-10-01 |
| CP.cold_start | 호출마다 새 isolate, 밀리초 단위. 최소 인스턴스 없음(추론) | | https://supabase.com/docs/guides/functions/architecture · "A new V8 isolate is spun up for each invocation" · 2026-10-01 ⚠️근거없음 |
| CP.instance_size | 메모리 256MB. Web Worker·Node vm 불가. 멀티스레드 라이브러리(libvips, sharp) 불가 | | https://supabase.com/docs/guides/functions/limits · "Maximum Memory: 256MB" · 2026-10-01 |
| CP.request_size | `미확인` | | — |
| CP.local_disk | `/tmp` 최대 256MB, 호출마다 초기화. 볼륨 없음(S3·Storage 버킷 마운트 가능) | | https://supabase.com/docs/guides/functions/ephemeral-storage · "Ephemeral storage will reset on each function invocation" · 2026-10-01 |
| CP.scaling | 같은 엣지 위치에서 여러 isolate 동시 실행, 최대 `미확인`. 프로젝트당 함수 100개. 번들 CLI 로컬 20MB, 서버 측 5MB | | https://supabase.com/docs/guides/functions/architecture · https://supabase.com/docs/guides/functions/limits · 2026-10-01 |
| CP.concurrency | 호출당 isolate 1개 | | https://supabase.com/docs/guides/functions/architecture · 2026-10-01 |
| CP.shutdown | `beforeunload` 이벤트로 종료 통지, 유예 시간 `미확인` | | https://supabase.com/docs/guides/functions/background-tasks · "to be notified when the Function is about to be shut down" · 2026-10-01 |
| CP.deploy | `supabase functions deploy`가 ESZip으로 묶어 전 세계 배포. 롤백·트래픽 분할 `미확인` | | https://supabase.com/docs/guides/functions/architecture · 2026-10-01 |
| CP.availability | 리전을 고정하면 다른 리전으로 자동 재라우팅 안 됨 | | https://supabase.com/docs/guides/functions/regional-invocation · "requests will NOT be automatically re-routed to another region" · 2026-10-01 |
| CP.networking | 아웃바운드 25·587 포트 차단. `SUPABASE_URL`, `SUPABASE_DB_URL` 등 자동 주입. 고정 IP `미확인` | | https://supabase.com/docs/guides/functions/limits · "Outgoing connections to ports 25 and 587 are not allowed" · https://supabase.com/docs/guides/functions/secrets · 2026-10-01 |
| CP.regions | 16개 리전, 서울 포함 | | https://supabase.com/docs/guides/functions/regional-invocation · 2026-10-01 |
| CP.plan_limits | **1주 무활동 시 프로젝트 정지**, 활성 프로젝트 2개. 커스텀 도메인 없이 `text/html` GET 응답은 `text/plain`으로 바뀜(웹 페이지 호스팅 불가) | | https://supabase.com/pricing · "Free projects are paused after 1 week of inactivity" · https://supabase.com/docs/guides/functions/limits · "GET requests that return text/html will be rewritten to text/plain" · 2026-10-01 |
| CP.ops_burden | 낮음 | | — ⚠️근거없음 |
| CP.cost_floor | $0, 호출 50만 포함 | | https://supabase.com/pricing · https://supabase.com/docs/guides/functions/pricing · 2026-10-01 |

#### 비용 구조
$0. 할당 초과 시 동작은 `미확인`(Free에는 지출 상한 개념 대신 할당이 있음).

#### 교체 계열 정보
- Deno 런타임: `Deno.serve`, `Deno.env.get`, ESZip 번들 → 컨테이너에서 Deno를 그대로 쓰거나 Node HTTP 서버로 이식.
- `EdgeRuntime.waitUntil` → 일반 백그라운드 작업 또는 큐.
- 자동 주입 `SUPABASE_*` 환경변수 → 직접 설정.
- `pg_cron` + `pg_net` 호출은 URL만 바꿔 유지 가능.
- 종속 정도: 낮음~중간 (추론). ⚠️근거없음

#### 함정
- CPU 2초: 이미지 처리·비밀번호 해시가 들어가면 실패한다.
- 1주 무활동 정지는 사용자에게 장애로 보인다.

### 8.2 Supabase Edge Functions — Pro 이상
- 계열: 컴퓨트-티어0
- 서울 리전: 있음(지정 필요)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | HTTP 함수, `pg_cron` 정기 호출 | | https://supabase.com/docs/guides/functions/schedule-functions · 2026-10-01 |
| CP.request_timeout | 벽시계 400초, CPU 2초, 유휴 150초 | | https://supabase.com/docs/guides/functions/limits · "Paid plans: 400s" · 2026-10-01 |
| CP.long_connection | 웹소켓 가능, 400초 한도 | | https://supabase.com/docs/guides/functions/websockets · 2026-10-01 |
| CP.cpu_outside_request | `EdgeRuntime.waitUntil`, 한도 안 | | https://supabase.com/docs/guides/functions/background-tasks · 2026-10-01 |
| CP.cold_start | 호출마다 새 isolate | | https://supabase.com/docs/guides/functions/architecture · 2026-10-01 |
| CP.instance_size | 256MB | | https://supabase.com/docs/guides/functions/limits · 2026-10-01 |
| CP.request_size | `미확인` | | — |
| CP.local_disk | `/tmp` 최대 512MB, 호출마다 초기화 | | https://supabase.com/docs/guides/functions/ephemeral-storage · "Up to 512MB" · 2026-10-01 |
| CP.scaling | 프로젝트당 함수 Pro 1,000, Team 2,000 | | https://supabase.com/docs/guides/functions/limits · 2026-10-01 |
| CP.concurrency | 호출당 isolate 1개 | | https://supabase.com/docs/guides/functions/architecture · 2026-10-01 |
| CP.shutdown | `beforeunload`, 유예 `미확인` | | https://supabase.com/docs/guides/functions/background-tasks · 2026-10-01 |
| CP.deploy | ESZip 전 세계 배포, 롤백 `미확인` | | https://supabase.com/docs/guides/functions/architecture · 2026-10-01 |
| CP.availability | 리전 고정 시 재라우팅 없음 | | https://supabase.com/docs/guides/functions/regional-invocation · 2026-10-01 |
| CP.networking | 25·587 차단, 고정 IP `미확인` | | https://supabase.com/docs/guides/functions/limits · 2026-10-01 |
| CP.regions | 서울 포함 16개 | | https://supabase.com/docs/guides/functions/regional-invocation · 2026-10-01 |
| CP.plan_limits | 무활동 정지 없음. **지출 상한이 Pro에서 기본으로 켜져 있고, 할당을 넘으면 다음 결제 주기까지 해당 항목 사용 차단**(Edge Function 호출 포함) | | https://supabase.com/pricing · "Spend caps are on by default on the Pro Plan" · https://supabase.com/docs/guides/platform/cost-control · "further usage of that item is disallowed until the next billing cycle" · 2026-10-01 |
| CP.ops_burden | 낮음 | | — ⚠️근거없음 |
| CP.cost_floor | 월 $25, 호출 200만 포함 후 100만당 $2 | | https://supabase.com/pricing · https://supabase.com/docs/guides/functions/pricing · "then $2 per 1 Million" · 2026-10-01 |

#### 비용 구조
월 $25(DB 포함 프로젝트 요금). 기본 지출 상한 때문에 할당을 넘으면 함수가 멈춘다. 상한을 끄면 초과분 과금.

#### 교체 계열 정보
§8.1과 같다.

#### 함정
Pro 기본 설정에서 호출 200만을 넘으면 함수가 그달 내내 차단된다. 트래픽 폭증(D3)이 있는 앱은 상한을 끄고 알림으로 바꿔야 한다.

## 10. Heroku

상품 상태: 2026-02-06 Salesforce 발표로 "sustaining engineering" 모델(안정성·보안·지원 중심, 신규 기능 없음)로 바뀌었고, 신규 고객에게 Enterprise 계약을 더 이상 제공하지 않는다. 카드 결제 고객의 가격은 그대로다. 무료 등급은 없다. https://www.heroku.com/blog/an-update-on-heroku/ · "sustaining engineering model focused on stability, security, reliability, and support" / "Enterprise Account contracts will no longer be offered to new customers"

리전: Common Runtime은 `us`·`eu`뿐. Private Spaces에 tokyo·singapore 등이 있다. 서울 없음. https://devcenter.heroku.com/articles/regions

### 10.1 Heroku — Eco · Basic dyno (Common Runtime)
- 계열: 컴퓨트-티어0
- 서울 리전: 없음

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | Procfile의 web, worker, one-off. Scheduler 애드온 10분·1시간·1일 | Scheduler: 건너뛰거나 두 번 실행될 수 있음, 주기보다 오래 실행 안 됨 | https://devcenter.heroku.com/articles/scheduler · "every 10 minutes, every hour, or every day" / "a job may be skipped … may run twice" · 2026-10-01 |
| CP.request_timeout | **첫 바이트 30초**, 이후 바이트마다 55초 롤링 창. keep-alive 유휴 90초. 변경 불가 | | https://devcenter.heroku.com/articles/request-timeout · "terminate the request if it takes longer than 30 seconds" / "each byte … resets a rolling 55 second window" · 2026-10-01 |
| CP.long_connection | 웹소켓 지원, 55초 유휴 규칙 적용 | | https://devcenter.heroku.com/articles/http-routing · "WebSocket functionality is fully supported" · 2026-10-01 |
| CP.cpu_outside_request | 가능. Eco 웹 dyno는 30분 웹 트래픽 없으면 잠듦 | | https://devcenter.heroku.com/articles/eco-dyno-hours · "receives no web traffic in a 30-minute period, it sleeps" · 2026-10-01 |
| CP.cold_start | Eco 30분 유휴 시 잠듦, 월 1,000시간 소진 시 그달 남은 기간 잠듦. Basic은 잠들지 않음(추론) | | https://devcenter.heroku.com/articles/eco-dyno-hours · "forced to sleep for the rest of the month" · 2026-10-01 ⚠️근거없음 |
| CP.instance_size | 0.5GB | | https://devcenter.heroku.com/articles/dyno-types · 2026-10-01 |
| CP.request_size | 본문 한도 명시 없음. 헤더 8,192바이트, 응답 버퍼 1MB | | https://devcenter.heroku.com/articles/http-routing · 2026-10-01 |
| CP.local_disk | 임시. 재시작하면 사라지고, dyno는 하루 1회 이상 재시작(24시간 + 최대 216분) | | https://devcenter.heroku.com/articles/dynos · "Any files written get discarded the moment the dyno stops or restarts" · https://devcenter.heroku.com/articles/dyno-restarts · 2026-10-01 |
| CP.scaling | 프로세스 종류당 dyno 1개, 수평 확장 불가 | | https://devcenter.heroku.com/articles/dynos · "Horizontal scaling is unavailable for Eco and Basic dynos" · 2026-10-01 |
| CP.concurrency | 해당 없음(앱 프로세스) | | — |
| CP.shutdown | SIGTERM 후 30초, 그다음 SIGKILL | | https://devcenter.heroku.com/articles/dyno-shutdown-behavior · "Process failed to exit within 30 seconds of SIGTERM" · 2026-10-01 |
| CP.deploy | Preboot(무중단) 불가 → 배포 시 짧은 중단 (추론). 롤백 `미확인` | | https://devcenter.heroku.com/articles/preboot · "only available on the Common Runtime to apps that are using standard and performance dynos" · 2026-10-01 ⚠️근거없음 |
| CP.availability | dyno 1개 | | https://devcenter.heroku.com/articles/dynos · 2026-10-01 |
| CP.networking | 고정 출구 IP 문서 404, `미확인` | | — ⚠️근거없음 |
| CP.regions | us·eu | | https://devcenter.heroku.com/articles/regions · 2026-10-01 |
| CP.plan_limits | Eco는 개인 앱만, 실행 dyno 최대 2개 | | https://devcenter.heroku.com/articles/eco-dyno-hours · "Only personal apps can use Eco dynos" · 2026-10-01 |
| CP.ops_burden | 낮음(buildpack, Procfile) | | — ⚠️근거없음 |
| CP.cost_floor | Eco 월 $5(공유 1,000시간), Basic 월 $7. Postgres Essential-0 월 $5 | | https://devcenter.heroku.com/articles/dyno-types · https://www.heroku.com/pricing/ · 2026-10-01 |

#### 비용 구조
월 $5~7. 지출 상한 기능은 가격 페이지에 언급이 없다(`미확인`).

#### 교체 계열 정보
- Procfile 항목 → 컨테이너 명령. Buildpack → Dockerfile.
- `DATABASE_URL` 등 애드온 환경변수는 이름이 표준적이라 대부분 이어진다.
- Scheduler → 대상 플랫폼 크론.
- 종속 정도: 낮음.

#### 함정
- 30초 첫 바이트 한도는 티어 0 중 가장 엄격하다. A2가 "수십 초" 이상이면 바로 불일치.
- 매일 재시작 + 임시 디스크라 로컬 파일 상태(B2)는 하루를 못 넘긴다.
- 상품이 기능 동결 상태라 신규 구성 후보로는 낮은 순위 (추론). ⚠️근거없음

### 10.2 Heroku — Standard · Performance dyno
- 계열: 컴퓨트-티어0
- 서울 리전: 없음 (도쿄는 Private Spaces)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | web, worker, one-off, Scheduler(최소 10분) | | https://devcenter.heroku.com/articles/scheduler · 2026-10-01 |
| CP.request_timeout | 첫 바이트 30초, 55초 롤링 | | https://devcenter.heroku.com/articles/request-timeout · 2026-10-01 |
| CP.long_connection | 웹소켓 지원, 55초 유휴 | | https://devcenter.heroku.com/articles/http-routing · 2026-10-01 |
| CP.cpu_outside_request | 가능 | | — ⚠️근거없음 |
| CP.cold_start | 잠들지 않음 (추론, 잠듦은 Eco 규칙) | | https://devcenter.heroku.com/articles/eco-dyno-hours · 2026-10-01 ⚠️근거없음 |
| CP.instance_size | Standard-2X 1GB ~ Performance-2XL 126GB. GPU 없음(`미확인`) | | https://devcenter.heroku.com/articles/dyno-types · 2026-10-01 |
| CP.request_size | 헤더 8,192바이트, 응답 버퍼 1MB | | https://devcenter.heroku.com/articles/http-routing · 2026-10-01 |
| CP.local_disk | 임시, 매일 재시작 | | https://devcenter.heroku.com/articles/dyno-restarts · 2026-10-01 |
| CP.scaling | Cedar 총 100 dyno, Performance는 종류당 10. Fir 255. 오토스케일은 Performance·Private·Shield만 | | https://devcenter.heroku.com/articles/dyno-scaling-and-process-limits · https://devcenter.heroku.com/articles/scaling · 2026-10-01 |
| CP.concurrency | 해당 없음 | | — |
| CP.shutdown | SIGTERM 후 30초 | | https://devcenter.heroku.com/articles/dyno-shutdown-behavior · 2026-10-01 |
| CP.deploy | Preboot로 무중단 배포. 롤백 `미확인` | | https://devcenter.heroku.com/articles/preboot · 2026-10-01 |
| CP.availability | `미확인` | | — |
| CP.networking | Private Spaces 존재, 고정 IP `미확인` | | https://devcenter.heroku.com/articles/regions · 2026-10-01 |
| CP.regions | Common Runtime us·eu, Private Spaces 도쿄·싱가포르 등 | | https://devcenter.heroku.com/articles/regions · 2026-10-01 |
| CP.plan_limits | 기능 동결(sustaining engineering), 신규 Enterprise 계약 불가 | | https://www.heroku.com/blog/an-update-on-heroku/ · 2026-10-01 |
| CP.ops_burden | 낮음 | | — ⚠️근거없음 |
| CP.cost_floor | Standard-1X 월 $25, Performance-M 월 $250 | | https://devcenter.heroku.com/articles/dyno-types · 2026-10-01 |

#### 비용 구조
최소 월 $25(무중단 배포 가능한 최저 단계). 지출 상한 `미확인`.

#### 교체 계열 정보
§10.1과 같다.

#### 함정
상위 dyno로 올려도 30초 라우터 한도는 그대로다.

## 11. DigitalOcean — App Platform
- 계열: 컴퓨트-티어0
- 서울 리전: 없음. NYC, AMS, SFO, SGP, LON, FRA, TOR, BLR, SYD, ATL, RIC, MKC, MEM. https://docs.digitalocean.com/products/app-platform/details/availability/

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | services, workers, jobs(`PRE_DEPLOY`/`POST_DEPLOY`/`SCHEDULED`) | 정기 작업 최소 15분 간격, 실행 중에만 과금 | https://docs.digitalocean.com/products/app-platform/reference/app-spec/ · https://docs.digitalocean.com/products/app-platform/how-to/manage-jobs/ · "(minimum every 15 minutes)" · 2026-10-01 |
| CP.request_timeout | 기본 30초, 최대 100초(PHP 지원 문서 근거, 플랫폼 전체 한도의 공식 근거는 약함). 파일 업로드 600초 타임아웃 | | https://docs.digitalocean.com/support/my-php-app-is-timing-out-and-throwing-5xx-errors/ · "You can set the execution time to a maximum of `100` seconds" · https://docs.digitalocean.com/products/app-platform/details/limits/ · "File uploads to apps timeout after 600 seconds." · 2026-10-01 ⚠️근거없음 |
| CP.long_connection | 웹소켓 지원(DO 공식 샘플 저장소, 보관됨). 지속 한도 `미확인` | | https://github.com/digitalocean/sample-websocket · 2026-10-01 |
| CP.cpu_outside_request | 가능(상시 컨테이너, 추론) | | — ⚠️근거없음 |
| CP.cold_start | scale-to-zero 문서 없음 (`미확인`) | | — ⚠️근거없음 |
| CP.instance_size | 월 $5 공유 1 CPU/512MiB ~ 전용 8 CPU/32GiB(월 $392) | | https://docs.digitalocean.com/products/app-platform/details/pricing/ · 2026-10-01 |
| CP.request_size | `미확인` | | — |
| CP.local_disk | 임시 4GiB, 가득 차면 비정상으로 판정돼 교체. 볼륨 없음 | | https://docs.digitalocean.com/products/app-platform/details/limits/ · "limited to 4 GiB, and if it is filled to capacity, the container is detected as unhealthy and replaced" · 2026-10-01 |
| CP.scaling | 컨테이너 250개. 요청 기반 오토스케일(초당 요청 또는 P95 지연) 최대 100. CPU 기반은 전용 CPU만. 5분 창 `[충돌]` 가격 페이지는 공유 플랜 오토스케일 "No" | | https://docs.digitalocean.com/products/app-platform/how-to/scale-app/ · https://docs.digitalocean.com/products/app-platform/details/pricing/ · 2026-10-01 |
| CP.concurrency | 해당 없음 | | — |
| CP.shutdown | 유예 1~600초(기본 120), 드레인 1~110초(기본 15) | | https://docs.digitalocean.com/products/app-platform/reference/app-spec/ · 2026-10-01 |
| CP.deploy | 최근 성공 배포 10개로 롤백. 무중단 문구 `미확인` | | https://docs.digitalocean.com/products/app-platform/details/features/ · 2026-10-01 |
| CP.availability | `미확인` | | — |
| CP.networking | 전용 출구 IP 가능, VPC 가능, **둘을 동시에 켤 수 없음** | | https://docs.digitalocean.com/products/app-platform/how-to/enable-vpc/ · "VPC network access and dedicated egress IPs cannot be enabled at the same time" · 2026-10-01 |
| CP.regions | 서울·도쿄 없음, 싱가포르 SGP | | https://docs.digitalocean.com/products/app-platform/details/availability/ · 2026-10-01 |
| CP.plan_limits | 정적 앱 3개 무료, 크론 최소 15분 | | https://docs.digitalocean.com/products/app-platform/details/pricing/ · 2026-10-01 |
| CP.ops_burden | 낮음 | | — ⚠️근거없음 |
| CP.cost_floor | 컨테이너 월 $5. 개발용 DB 월 $7(512MB) | | https://docs.digitalocean.com/products/app-platform/details/pricing/ · 2026-10-01 |

#### 비용 구조
최소 월 $5. 지출 한도 동작 `미확인`.

#### 교체 계열 정보
- 앱 스펙(`.do/app.yaml`)의 services·workers·jobs가 컨테이너 서비스·워커·크론으로 1:1 대응한다.
- Buildpack 빌드 → Dockerfile.
- 종속 정도: 낮음.

#### 함정
- 요청 100초 상한(근거 약함)과 크론 15분 최소 주기.
- DB를 VPC로 붙이면 고정 출구 IP를 못 쓴다. 외부 API가 IP 허용 목록을 요구하면 충돌.

## 교차 관찰

판정 규칙을 만들 때 쓸 수 있는, 위 항목들에서 바로 나오는 사실.

1. **서울 리전이 있는 티어 0은 Vercel(`icn1`), Supabase Edge Functions(`ap-northeast-2`), Cloud Functions for Firebase(`asia-northeast3`)뿐이다.** Netlify·Railway·Render·Fly·Heroku·DigitalOcean·Koyeb·Firebase App Hosting은 서울이 없다. Cloudflare는 요청 근처에서 실행되지만 서울 데이터센터는 확인하지 않았다. Replit은 문서가 충돌한다.
2. **지출 한도가 곧 서비스 정지인 플랫폼**: Vercel(일시 정지 켰을 때, 수동 재개), Netlify(크레딧 소진 시 팀 전체), Railway(하드 한도), Supabase Pro(기본 상한), Replit, Firebase(선택형 상한). 반대로 Cloudflare는 상한이 아예 없고, Render는 빌드만 멈춘다.
3. **종료 유예가 사실상 없는 기본값**: Vercel 500ms, Railway 0초, Fly 5초(SIGINT). 긴 유예: Cloudflare Containers 15분, DigitalOcean 최대 600초, Render·Fly 최대 300초.
4. **볼륨을 붙이면 확장·무중단을 잃는 플랫폼**: Render(인스턴스 1개, 배포 다운타임), Railway(레플리카 불가, 재배포 다운타임), Fly(머신 1대, 복제 없음), Koyeb(스케일 1, 프리뷰). 볼륨이 아예 없는 플랫폼: Vercel, Netlify, Cloudflare Workers, Firebase, Supabase Edge, Replit(게시마다 초기화), Heroku(매일 재시작), DigitalOcean.
5. **최대 요청 시간 순서(짧은 것부터)**: Netlify Edge CPU 50ms·Workers Free CPU 10ms → Vercel Edge 25초(시작) → Heroku 30초(첫 바이트) → Netlify 60초 → Firebase Hosting 경유 60초 → DigitalOcean 100초·Koyeb 100초 → Supabase 150/400초 → Vercel 300/800초 → Railway 15분 → Firebase 2세대 60분 → Render 100분 → Cloudflare 벽시계 무제한(CPU 5분).
6. **문서 간 충돌**(사람 확인 필요): Vercel Pro 리전 수(3 vs 5), Railway Pro 볼륨(1TB vs 50GB), Firebase 2세대 메모리(32GiB vs 16GiB), Replit 리전(미국만 vs 아시아 선택)과 Autoscale 기본료($1 vs $2), DigitalOcean 공유 CPU 오토스케일 가능 여부.
