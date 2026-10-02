# 컴퓨트 플랫폼별 생성 산출물

- 작성일: 2026-10-01 (모든 출처 확인일 2026-10-01)
- 짝 문서: [04-compute-tier0.md](04-compute-tier0.md), [05-compute-tier1-2.md](05-compute-tier1-2.md) (능력), [../dimensions.md](../dimensions.md) (요구 차원)
- 참고 사례: `simple-web-app/k8s`, `simple-web-app/docs/deploy.md` (k8s·nginx·마이그레이션 Job 구성)

## 범위

에이전트가 플랫폼을 고른 뒤 **직접 생성하는 산출물**과, 생성물을 사람이 리뷰하지 않아도 되도록 **검증하는 명령**을 정리한다. 사용자는 바이브코더이므로 리뷰를 기대할 수 없고, 모든 생성물은 이 문서의 검증 명령을 통과해야 한다. 이미 있는 산출물도 같은 기준으로 판정해서 유지, 부분 수정, 교체 중 하나로 처리한다.

- 파트 1: 플랫폼과 무관한 공통 산출물(Dockerfile, 기존 Dockerfile 판정, 앱 쪽 계약, CI/CD).
- 파트 2: 04·05 문서의 구성 요소별 산출물. 플랜에 따라 산출물이 달라질 때만 플랜을 나눴다.

표기
- `미확인`: 공식 문서를 열었지만 값을 찾지 못했거나, 해당 페이지를 열지 못한 경우다.
- `(추론)`: 인용한 사실에서 이끌어 낸 규칙이다. 규칙으로 옮기기 전에 사람이 검토한다.
- Terraform 리소스 문서는 registry.terraform.io 페이지가 JS로 렌더링되어, 레지스트리가 표시하는 원문(provider 저장소의 `website/docs/r/<name>.html.markdown`)이나 레지스트리 API(`registry.terraform.io/v1/providers/<ns>/<name>`)로 확인했다. 출처에는 레지스트리 URL을 적었다.
- `cloud.google.com/run/docs/*`는 `docs.cloud.google.com/run/docs/*`로 301 리다이렉트된다. 새 주소로 적었다.

## 목차

- [요약표](#요약표)
- [파트 1. 공통 산출물](#파트-1-공통-산출물)
  - [1.1 Dockerfile 생성 규칙](#11-dockerfile-생성-규칙)
  - [1.2 기존 Dockerfile 판정 기준](#12-기존-dockerfile-판정-기준)
  - [1.3 앱 쪽 계약](#13-앱-쪽-계약)
  - [1.4 CI/CD](#14-cicd)
  - [1.5 공통 검증 명령](#15-공통-검증-명령)
- [파트 2. 플랫폼별](#파트-2-플랫폼별)
  - 티어 0: [Vercel Functions](#p1-vercel-functions-hobby--pro--enterprise) · [Vercel Edge](#p2-vercel-edge-runtime) · [Netlify Functions](#p3-netlify-functions) · [Netlify Edge](#p4-netlify-edge-functions) · [Cloudflare Workers](#p5-cloudflare-workers--pages-functions) · [Durable Objects](#p6-cloudflare-durable-objects) · [Cloudflare Containers](#p7-cloudflare-containers) · [Railway](#p8-railway) · [Render](#p9-render) · [Fly.io](#p10-flyio-machines) · [Firebase App Hosting](#p11-firebase-app-hosting) · [Cloud Functions for Firebase](#p12-cloud-functions-for-firebase) · [Supabase Edge](#p13-supabase-edge-functions) · [Replit](#p14-replit-deployments) · [Heroku](#p15-heroku) · [DigitalOcean](#p16-digitalocean-app-platform) · [Koyeb](#p17-koyeb)
  - 티어 1: [Cloud Run 서비스](#p18-cloud-run-서비스-요청-기반--인스턴스-기반) · [Cloud Run Jobs](#p19-cloud-run-jobs) · [워커 풀](#p20-cloud-run-워커-풀) · [Cloud Run functions](#p21-cloud-run-functions) · [ECS Fargate](#p22-ecs-on-fargate-일반-서비스--fargate-spot) · [ECS Express](#p23-ecs-express-mode) · [App Runner](#p24-aws-app-runner) · [Lambda URL](#p25-lambda--function-url) · [Lambda API GW](#p26-lambda--api-gateway) · [Azure Container Apps](#p27-azure-container-apps)
  - 티어 2: [쿠버네티스 공통](#k-쿠버네티스-공통-산출물) · [GKE Autopilot](#p28-gke-autopilot) · [GKE Standard](#p29-gke-standard-존--리전) · [EKS MNG](#p30-eks--관리형-노드-그룹--cluster-autoscaler) · [EKS Karpenter](#p31-eks--karpenter) · [EKS Auto Mode](#p32-eks--auto-mode) · [EKS Fargate](#p33-eks--fargate-프로필) · [k3s](#p34-vm-위-k3s)
  - 기준선: [EC2 + compose](#p35-단일-vm--docker-compose--ec2) · [GCE + compose](#p36-단일-vm--docker-compose--compute-engine)
- [생성 자동화를 막는 발견](#생성-자동화를-막는-발견)

## 요약표

- **IaC 수단**: Terraform provider(공식 / 파트너 / 커뮤니티 / 보관됨 / 없음).
- **자동화 불가**: 사람이 한 번은 해야 하는 단계가 있는지 여부. 계정 생성과 결제 수단 등록은 모든 플랫폼에 공통이라 뺐다.
- **CI 인증**: GitHub OIDC로 받는 단기 자격 증명인지, 저장해 두는 정적 토큰인지.

| # | 플랫폼 | IaC 수단 | 설정 파일 | CI 인증 | 자동화 불가 단계 |
|---|---|---|---|---|---|
| 1 | Vercel Functions | `vercel/vercel` (프로젝트·환경변수·도메인·메모리) | `vercel.json` (또는 `vercel.toml`/`vercel.ts`) | 토큰 (OIDC 배포 미지원) | 있음: Git 앱 설치, 토큰 발급, Secure Compute 네트워크 생성 |
| 2 | Vercel Edge | 위와 같음 | 위와 같음 + 라우트 `runtime` | 토큰 | 위와 같음. 신규 생성 금지(폐지 권고) |
| 3 | Netlify Functions | `netlify/netlify` (사이트 생성 불가) | `netlify.toml` | 토큰 | 있음: 사이트 생성, Git 연결, 리전 설정(UI) |
| 4 | Netlify Edge | 위와 같음 | `netlify.toml` `[[edge_functions]]` | 토큰 | 위와 같음 |
| 5 | Cloudflare Workers | `cloudflare/cloudflare` v5 (번들링은 Wrangler) | `wrangler.jsonc` | 토큰 | 있음: API 토큰 발급, 존(도메인) 온보딩 |
| 6 | Durable Objects | Terraform 첫 apply 실패 문제 → Wrangler | `wrangler.jsonc` `exports` (또는 레거시 `migrations`) | 토큰 | 위와 같음 |
| 7 | Cloudflare Containers | **없음** (Wrangler 전용) | `wrangler.jsonc` `containers` + Dockerfile | 토큰 | 위와 같음 |
| 8 | Railway | 커뮤니티 provider | `.railway/railway.ts` (`railway.json`은 2026-12-01 종료) | 토큰 | 있음: 토큰 발급, GitHub 앱 승인(`미확인`) |
| 9 | Render | `render-oss/render` (파트너) | `render.yaml` | API 키 | 있음: Blueprint 최초 생성과 Git 연결(대시보드) |
| 10 | Fly.io | **보관됨**(`fly-apps/fly`, 비권장) → flyctl | `fly.toml` | 배포 토큰 | 있음: DNS 레코드 |
| 11 | Firebase App Hosting | `hashicorp/google` `google_firebase_app_hosting_backend` | `apphosting.yaml` + `firebase.json` | OIDC 가능(ADC) | 있음: GitHub 앱 연결(Git 배포 시) |
| 12 | Cloud Functions for Firebase | `hashicorp/google` (2세대 = `google_cloudfunctions2_function`) / Firebase CLI | `firebase.json` + 코드 옵션 | OIDC 가능(ADC) | 없음(추론) ⚠️근거없음 |
| 13 | Supabase Edge | `supabase/supabase` (커뮤니티 등급, 함수 포함) | `supabase/config.toml` | 액세스 토큰 | 있음: 액세스 토큰 발급 |
| 14 | Replit | **없음** | `.replit` | **없음**(UI 게시) | 있음: 게시 버튼, 결제 수단 → 사실상 자동화 불가 |
| 15 | Heroku | `heroku/heroku` (파트너) | `Procfile`, `app.json`, `heroku.yml` | API 키 | 있음: 카드 등록으로 계정 인증 |
| 16 | DigitalOcean App Platform | `digitalocean/digitalocean` `digitalocean_app` | `.do/app.yaml` | 토큰 | 있음: GitHub 앱 승인(`미확인`) |
| 17 | Koyeb | `koyeb/koyeb` (파트너) | 없음(CLI 플래그 / Terraform) | 토큰 | 토큰 발급 |
| 18 | Cloud Run 서비스 | `hashicorp/google` | (선택) Knative `service.yaml` | OIDC (WIF) | 서울 도메인 매핑 불가 → LB 필요. DNS |
| 19 | Cloud Run Jobs | `hashicorp/google` | (선택) job YAML | OIDC | 없음 |
| 20 | Cloud Run 워커 풀 | `hashicorp/google` | (선택) `worker-pool.yaml` | OIDC | 없음 |
| 21 | Cloud Run functions | `hashicorp/google` | 없음(Functions Framework) | OIDC | 없음 |
| 22 | ECS Fargate (+Spot) | `hashicorp/aws` + 모듈 | 태스크 정의 JSON | OIDC | DNS 위임(도메인이 외부에 있을 때) |
| 23 | ECS Express Mode | `hashicorp/aws` `aws_ecs_express_gateway_service` | 없음 | OIDC | 위와 같음 |
| 24 | App Runner | `hashicorp/aws` | `apprunner.yaml`(`미확인`) | OIDC | **신규 고객 불가 → 생성 금지** |
| 25 | Lambda Function URL | `hashicorp/aws` | (선택) SAM `template.yaml` | OIDC | 없음 |
| 26 | Lambda + API Gateway | `hashicorp/aws` | (선택) SAM | OIDC | 없음 |
| 27 | Azure Container Apps | `hashicorp/azurerm` | (선택) ACA YAML | OIDC | 없음 |
| 28 | GKE Autopilot | `hashicorp/google` | k8s 매니페스트(Kustomize) | OIDC | DNS |
| 29 | GKE Standard | `hashicorp/google` | k8s 매니페스트 | OIDC | DNS |
| 30 | EKS MNG | `hashicorp/aws` + `terraform-aws-modules/eks` | k8s 매니페스트 + 컨트롤러 Helm | OIDC | DNS |
| 31 | EKS Karpenter | 위와 같음 + Karpenter Helm | + NodePool/EC2NodeClass | OIDC | DNS |
| 32 | EKS Auto Mode | 위와 같음 (`compute_config`) | + IngressClass/IngressClassParams | OIDC | DNS |
| 33 | EKS Fargate | 위와 같음 (`aws_eks_fargate_profile`) | k8s 매니페스트 | OIDC | DNS |
| 34 | k3s on VM | VM 리소스만(클러스터는 스크립트) | k8s 매니페스트 | 클라우드 OIDC + SSH/kubeconfig | 노드 OS 운영, DNS |
| 35 | EC2 + compose | `hashicorp/aws` `aws_instance` | `compose.yaml`, `Caddyfile` | OIDC + SSM/SSH | DNS, 서버 운영 |
| 36 | GCE + compose | `hashicorp/google` `google_compute_instance` | `compose.yaml`, `Caddyfile` | OIDC + SSH | DNS, 서버 운영 |

---

# 파트 1. 공통 산출물

## 1.1 Dockerfile 생성 규칙

컨테이너를 받는 플랫폼(Cloud Run, ECS, ACA, k8s, Render·Railway·Fly·Koyeb·DO의 Docker 모드, Cloudflare Containers, Lambda 이미지, VM)이면 모두 Dockerfile을 생성한다. Vercel·Netlify·Workers·Supabase Edge·Firebase Functions는 Dockerfile을 쓰지 않는다.

### 1.1.1 모든 런타임 공통 규칙

| # | 규칙 | 생성 형태 | 출처 (확인 2026-10-01) |
|---|---|---|---|
| D1 | 멀티스테이지. 최종 단계에는 실행에 필요한 파일만 둔다 | `FROM … AS deps` → `AS build` → 런타임 단계, `COPY --from=build` | https://docs.docker.com/build/building/best-practices/ · "Split your Dockerfile instructions into distinct stages to make sure that the resulting output only contains the files that are needed to run the application." · https://docs.docker.com/build/building/multi-stage/ |
| D2 | 베이스 이미지 태그를 고정한다. `latest`와 태그 없는 이미지는 금지. 가능하면 다이제스트로 고정 | `FROM node:24.13.0-slim` (또는 `@sha256:…`) | best-practices · "By pinning your images to a digest, you're guaranteed to always use the same image version, even if a publisher replaces the tag" |
| D3 | lock 파일로 재현 가능하게 빌드한다. lock이 없으면 먼저 생성하고 커밋한다 | Node `npm ci`(lock 필수, 불일치 시 실패), pnpm `--frozen-lockfile`(`미확인`), uv `uv sync --locked`, pip `requirements.lock` | https://docs.npmjs.com/cli/v11/commands/npm-ci · lock이 맞지 않으면 "exit with an error, instead of updating the package lock" · https://docs.astral.sh/uv/guides/integration/docker/ ⚠️출처확인필요 |
| D4 | 의존성 레이어를 소스보다 먼저 복사해 캐시를 살린다. 캐시 마운트를 쓴다 | `COPY package.json package-lock.json ./` → `RUN --mount=type=cache,target=/root/.npm npm ci` | https://docs.docker.com/build/cache/optimize/ · "Cache mounts are a way to specify a persistent cache location to be used during builds." |
| D5 | `.dockerignore`를 함께 생성한다(`.git`, `node_modules`, `.venv`, `.env*`, 빌드 산출물) | 빌드 컨텍스트 루트에 둔다 | best-practices · "use a `.dockerignore` file" · https://docs.docker.com/build/concepts/context/ |
| D6 | non-root 사용자로 실행한다. UID를 숫자로 고정한다(k8s `runAsNonRoot` 검증과 Checkov CKV_K8S_40 때문) | `USER node` / `USER 10001` / distroless `nonroot` | best-practices · "If a service can run without privileges, use `USER` to change to a non-root user." · https://docs.docker.com/reference/dockerfile/ · "When the user doesn't have a primary group then the image will be run with the `root` group." |
| D7 | `CMD`/`ENTRYPOINT`는 exec(JSON 배열) 형식. 셸 형식은 신호를 전달하지 않는다 | `CMD ["node","server.js"]` | https://docs.docker.com/reference/dockerfile/ · shell form "starts your `ENTRYPOINT` as a subcommand of `/bin/sh -c`, which does not pass signals." / "will not be the container's `PID 1`, and will not receive Unix signals" |
| D8 | 패키지 매니저(`npm start`, `yarn start`)를 거쳐 실행하지 않는다. 신호를 삼킨다 | 런타임 바이너리를 직접 호출 | https://github.com/nodejs/docker-node/blob/main/docs/BestPractices.md · `CMD ["node","index.js"]` 권장, npm이 SIGTERM을 삼킨다고 설명 |
| D9 | PID 1 문제: 자식 프로세스를 띄우는 앱(Node, 셸 래퍼)은 init을 둔다. 플랫폼이 `--init`을 줄 수 없으면 `tini`를 이미지에 넣는다 | `docker run --init` 또는 `ENTRYPOINT ["/usr/bin/tini","--"]` | https://docs.docker.com/reference/cli/docker/container/run/ · "an init process should be used as the PID 1 in the container" · docker-node BestPractices · "Node.js was not designed to run as PID 1" |
| D10 | 종료 신호는 SIGTERM(기본값)을 그대로 쓴다. Fly는 기본 SIGINT라 `fly.toml` `kill_signal`로 맞춘다(P10) | `STOPSIGNAL`은 생략 | https://docs.docker.com/reference/dockerfile/ · STOPSIGNAL "The default is `SIGTERM` if not defined." |
| D11 | 포트는 환경변수 `PORT`로 받고 `0.0.0.0`에 바인드한다. `EXPOSE`는 기본값(8080)만 문서화한다 | `ENV PORT=8080`, 앱이 `process.env.PORT` / `$PORT`를 읽음 | https://docs.cloud.google.com/run/docs/container-contract · "must listen for requests on `0.0.0.0`" (05 문서 §1.1) |
| D12 | `HEALTHCHECK`는 Docker·compose·ECS 컨테이너 헬스체크용으로만 넣는다. k8s·Cloud Run은 이 지시어를 쓰지 않고 자체 probe를 쓴다(추론). 이미지에 `curl`이 없으면 런타임 자체로 검사한다 | `HEALTHCHECK --interval=30s --timeout=3s --start-period=10s CMD ["node","healthcheck.js"]` | https://docs.docker.com/reference/dockerfile/ · 기본값 interval 30s, timeout 30s, start-period 0s, retries 3. "There can only be one `HEALTHCHECK` instruction in a Dockerfile." ⚠️근거없음 |
| D13 | 파이프가 있는 `RUN`은 `set -o pipefail` | `SHELL ["/bin/bash","-o","pipefail","-c"]` | best-practices · "Prepend `set -o pipefail &&`" · hadolint DL4006 ⚠️출처확인필요 |
| D14 | 비밀 값을 `ENV`/`ARG`에 넣지 않는다. 런타임 환경변수나 비밀 저장소로 주입한다 | — | https://12factor.net/config · "the codebase could be made open source at any moment, without compromising any credentials." ⚠️출처부적격 |
| D15 | 로그는 stdout/stderr로, 버퍼링 없이 | Python `ENV PYTHONUNBUFFERED=1` | https://docs.python.org/3/using/cmdline.html · "equivalent to specifying the -u option" (stdout/stderr 비버퍼) · https://12factor.net/logs ⚠️출처부적격 |
| D16 | 개발 서버 금지(`next dev`, `vite`, `flask run`, `manage.py runserver`, `uvicorn --reload`, `nodemon`) | 아래 런타임별 운영 서버 | Flask · "Do not use the development server when deploying to production." (https://flask.palletsprojects.com/en/stable/deploying/) · Django · "DO NOT USE THIS SERVER IN A PRODUCTION SETTING." (https://docs.djangoproject.com/en/stable/ref/django-admin/) |

### 1.1.2 런타임별 규칙

#### Next.js (standalone)
- `next.config`에 `output: 'standalone'`을 추가한다. 이 출력은 `node_modules` 없이 실행되고, `next start` 대신 쓸 수 있는 `server.js`를 함께 만든다. 모노레포면 `outputFileTracingRoot`를 설정한다.
- `public`과 `.next/static`은 자동으로 복사되지 않으므로 직접 복사한다(CDN에 두지 않을 때).
- 실행은 `PORT`와 `HOSTNAME=0.0.0.0` 환경변수로 한다.
- 인스턴스가 2개 이상이면 다음을 함께 생성한다.
  - 모든 인스턴스에 같은 `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY`(16·24·32바이트 AES 키를 base64로). 키는 빌드 출력에 들어간다.
  - 같은 빌드(같은 이미지)로 모든 컨테이너를 띄운다.
  - 롤링 배포 중 버전 차이(skew)를 막으려면 `deploymentId`.
  - 인스턴스 간 공유 `cacheHandler`(04 문서 Vercel 교체 계열).
- `NEXT_PUBLIC_*`는 빌드 시점에 코드에 박힌다. 환경마다 값이 다르면 환경별로 빌드하거나, 런타임 환경변수로 바꾼다.
- 드레인 시간은 10~30초를 권장한다. SIGTERM이나 SIGINT를 받으면 기다렸다가 종료한다.

```dockerfile
# 생성 템플릿 (vercel/next.js examples/with-docker 기준으로 축약)
ARG NODE_VERSION=24.13.0-slim
FROM node:${NODE_VERSION} AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci

FROM node:${NODE_VERSION} AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:${NODE_VERSION} AS runner
WORKDIR /app
ENV NODE_ENV=production PORT=8080 HOSTNAME=0.0.0.0
COPY --from=build --chown=node:node /app/.next/standalone ./
COPY --from=build --chown=node:node /app/.next/static ./.next/static
COPY --from=build --chown=node:node /app/public ./public
USER node
EXPOSE 8080
CMD ["node", "server.js"]
```

출처 (확인 2026-10-01)
- https://nextjs.org/docs/app/api-reference/config/next-config-js/output · "a minimal `server.js` file is also output which can be used instead of `next start`." / "does not copy the `public` or `.next/static` folders by default"
- https://nextjs.org/docs/app/guides/self-hosting · "Platforms should allow a configurable drain period (10-30 seconds is recommended)" / "all instances must use the same encryption key"
- https://github.com/vercel/next.js/blob/canary/examples/with-docker/Dockerfile · `USER node`, `CMD ["node", "server.js"]`. 예전 예제의 `nextjs` uid 1001 사용자는 더 이상 쓰지 않는다.

#### Node.js 일반 (Express, Fastify, NestJS, Remix 서버)
- `ENV NODE_ENV=production`과 `npm ci --omit=dev`(런타임 단계)를 쓴다. `--omit=dev` 플래그의 원문은 `미확인`.
- `USER node`.
- `CMD ["node","dist/main.js"]`. `npm start`는 금지(D8).
- 앱이 `SIGTERM`을 받으면 `server.close()`를 호출하고 DB 풀을 닫게 한다(1.3).
- 출처: https://github.com/nodejs/docker-node/blob/main/docs/BestPractices.md · "Run with `NODE_ENV` set to `production`."

#### Python 공통 (uv / pip)
- uv: uv 이미지를 고정(`COPY --from=ghcr.io/astral-sh/uv:0.12.21 /uv /uvx /bin/`)한다.
- 의존성 레이어는 `uv sync --locked --no-install-project`, 그다음 `uv sync --locked --no-editable`로 설치한다.
- 환경변수 `UV_COMPILE_BYTECODE=1`, `UV_LINK_MODE=copy`를 둔다.
- 최종 단계에는 `.venv`만 복사하고, `.dockerignore`에 `.venv`를 넣는다.
- pip: `requirements.lock`(해시 고정)과 `pip install --no-cache-dir`(hadolint DL3042).
- `ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1`.
- 출처: https://docs.astral.sh/uv/guides/integration/docker/ (확인 2026-10-01) ⚠️출처확인필요

#### FastAPI / Starlette (ASGI)
- 실행 형태는 플랫폼에 따라 다르다.
  - **오토스케일러가 프로세스를 늘리는 플랫폼**(Cloud Run, ECS, ACA, k8s, Render, Railway, Fly): 컨테이너당 Uvicorn 프로세스 1개.
    - `CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8080","--proxy-headers","--forwarded-allow-ips=*","--timeout-graceful-shutdown","8"]`
    - `PORT`를 읽으려면 셸이 필요하다. 이때도 `exec`로 PID 1을 넘긴다: `CMD ["sh","-c","exec uvicorn … --port ${PORT:-8080}"]`
    - 또는 FastAPI CLI 형식 `CMD ["fastapi","run","app/main.py","--proxy-headers","--port","8080"]`.
  - **단일 VM**: `--workers N`(Uvicorn 자체) 또는 Gunicorn + `uvicorn-worker`.
    - `uvicorn.workers` 모듈은 deprecated이므로 `uvicorn-worker` 패키지를 쓴다.
- `--forwarded-allow-ips=*`는 LB 뒤에서만 쓴다. 문서는 "Only trust clients you can actually trust!"라고 경고한다. LB 대역을 알면 그 대역을 넣는다(추론). ⚠️근거없음
- `--timeout-graceful-shutdown`은 플랫폼 종료 유예보다 짧게 잡는다(1.3.2 표).
- `tiangolo/uvicorn-gunicorn-fastapi` 이미지는 deprecated다. 공식 Python 이미지로 빌드한다.

출처 (확인 2026-10-01)
- https://fastapi.tiangolo.com/deployment/docker/ · "Always use the exec form of the CMD instruction" / 쿠버네티스에서는 "a single Uvicorn process per container"
- https://uvicorn.dev/deployment/ · "The `uvicorn.workers` module is deprecated" ⚠️출처확인필요
- https://uvicorn.dev/settings/ · "--timeout-graceful-shutdown <int>" ⚠️출처확인필요

#### Django (WSGI) / Flask
- 실행: `gunicorn project.wsgi:application --bind 0.0.0.0:$PORT --workers N --graceful-timeout G --timeout T --access-logfile -`
  - Flask는 `gunicorn app:app …`.
  - 기본 바인드가 `127.0.0.1:8000`이라 컨테이너에서는 `--bind`가 필수다.
- 워커 수
  - Gunicorn 문서 기준은 2~4 × 코어 또는 `(2 × 코어) + 1`이다.
  - 생성 규칙: 할당 vCPU가 1 미만이면 2, 그 외에는 `2 × vCPU + 1`로 잡고 메모리 한도로 상한을 둔다(추론). ⚠️근거없음
  - `DATABASE` 연결 수 = 인스턴스 최대 수 × 워커 × 풀 크기. 이 값을 DB `max_connections`와 맞춘다(simple-web-app `docs/deploy.md` "DB 커넥션 계산" 참고).
- `--graceful-timeout`은 기본 30초다. 플랫폼 종료 유예보다 짧게 둔다(예: Cloud Run 10초 → 8초).
- Django
  - `DEBUG=False`, `ALLOWED_HOSTS`와 `SECRET_KEY`는 환경변수로 받는다.
  - CI에서 `python manage.py check --deploy`를 실행한다.
  - 정적 파일은 빌드 단계에서 `collectstatic`으로 모은다. 플래그 원문은 `미확인`.

출처 (확인 2026-10-01)
- https://gunicorn.org/reference/settings/ · workers "generally in the 2-4 x $(NUM_CORES) range" / graceful_timeout "Default: 30" ⚠️출처확인필요
- https://gunicorn.org/signals/ · "TERM — graceful shutdown; waits for workers to finish requests up to graceful_timeout." ⚠️출처확인필요
- https://docs.djangoproject.com/en/stable/howto/deployment/checklist/ · "DEBUG must never be enabled in production"
- https://docs.djangoproject.com/en/stable/howto/deployment/wsgi/gunicorn/

#### Go
- 빌드 단계는 `CGO_ENABLED=0 GOOS=linux go build`다.
- 최종 단계는 `gcr.io/distroless/static-debian13`(또는 `base-debian12`)과 `USER nonroot:nonroot`다.
- distroless에는 셸이 없어 `ENTRYPOINT`가 반드시 exec 형식이어야 한다. 셸이 없으므로 `HEALTHCHECK`는 앱 바이너리의 서브커맨드로 둔다(추론). ⚠️근거없음
- 출처: https://docs.docker.com/guides/golang/build-images/ · https://github.com/GoogleContainerTools/distroless · "distroless images by default do not contain a shell" (확인 2026-10-01) ⚠️출처확인필요

#### Ruby on Rails
- Rails 7.1 이상은 새 앱에 운영용 Dockerfile을 생성한다. 이 Dockerfile이 있으면 1.2 기준으로 판정해서 유지를 우선한다.
- 출처: https://guides.rubyonrails.org/7_1_release_notes.html · "Rails will now include Docker-related files in the application." (확인 2026-10-01) ⚠️출처확인필요
- Rails 8 Dockerfile의 세부 내용은 `미확인`.

#### 정적 SPA (Vite·CRA 빌드 결과)
- 컨테이너가 필요하면 빌드 단계 + nginx-unprivileged(포트 8080)로 만든다. 이미지 이름은 `미확인`.
- 티어 0(Vercel·Netlify·Cloudflare Pages)이나 오브젝트 스토리지 + CDN이 더 싸다(추론). ⚠️근거없음

## 1.2 기존 Dockerfile 판정 기준

판정 순서
1. 정적 검사를 돌린다: `hadolint Dockerfile`, `checkov -f Dockerfile --framework dockerfile`.
2. 아래 신호 표에 적용한다.
3. 1.5의 동작 검증(빌드, 기동, 헬스, SIGTERM)을 돌린다.

교체 신호가 하나라도 있거나, 부분 수정이 4개 이상 쌓이면 교체한다(추론, 임계값은 검토 대상). 교체할 때도 기존 파일에 담긴 비표준 단계(시스템 패키지, 빌드 인자, 추가 COPY)는 새 파일로 옮긴다. ⚠️근거없음

| 신호 | 탐지 | 판정 | 근거 규칙 |
|---|---|---|---|
| 개발 서버 실행 (`next dev`, `npm run dev`, `vite`, `flask run`, `runserver`, `--reload`, `nodemon`) | CMD/ENTRYPOINT 문자열 | 단일 단계이고 devDependencies까지 들어 있으면 **교체**. 그 외에는 **부분 수정**(CMD 교체) | D16 |
| 단일 단계에 빌드 도구·devDependencies·소스 전체 포함 (Node/Next/Go) | `FROM` 1개 + `npm install`/`go build` | **교체** | D1 |
| 단일 단계지만 Python slim + 런타임 의존성만 | `FROM python:*-slim` 1개, 컴파일러 없음 | **유지** 가능 (예: simple-web-app `services/board/Dockerfile`) | D1은 권장 |
| root 실행 (`USER` 없음, 또는 마지막 USER가 root) | hadolint DL3002 / Checkov CKV_DOCKER_3·CKV_DOCKER_8 | **부분 수정** (사용자 추가 + `USER`) | D6 |
| `latest` 태그 또는 태그 없음 | DL3007·DL3006 / CKV_DOCKER_7 | **부분 수정** (태그 고정) | D2 |
| 셸 형식 CMD/ENTRYPOINT | DL3025 | **부분 수정** (exec 형식, 필요하면 `sh -c "exec …"`) | D7 |
| `npm start`/`yarn start` 실행 | CMD 문자열 | **부분 수정** | D8 |
| lock 파일 없음 / `npm install` 사용 | 저장소에 lock 없음, Dockerfile 문자열 | **부분 수정** (lock 생성 + `npm ci`) | D3 |
| 포트 하드코딩, `localhost`/`127.0.0.1` 바인드 | CMD 인자, 앱 코드 | **부분 수정** (`PORT`, `0.0.0.0`) | D11 |
| `ENV`/`ARG`에 비밀 값 | 키 이름 패턴(`*_KEY`, `*_SECRET`, `PASSWORD`) + 값 존재 | **교체** + 비밀 회전 안내 (이미지 레이어에 남는다) | D14 |
| `ADD`로 로컬 파일 복사 | DL3020 / CKV_DOCKER_4 | **부분 수정** | — |
| apt 버전 미고정, 캐시 미삭제 | DL3008·DL3009 | 경고만 (유지) | — |
| HEALTHCHECK 없음 | CKV_DOCKER_2 | 플랫폼이 compose·ECS면 **부분 수정**, k8s·Cloud Run이면 무시 | D12 |
| 22번 포트 노출 | CKV_DOCKER_1 | **부분 수정** | — |
| `.dockerignore` 없음 | 파일 존재 | **부분 수정** (생성) | D5 |
| 기동 시 마이그레이션 (`CMD ["sh","-c","migrate && serve"]`) | CMD 문자열 | **부분 수정** (마이그레이션을 1.3.5 위치로 이동) | 1.3.5 |
| 이미지가 플랫폼 한도를 넘음 (Lambda 압축 해제 10GB 등) | `docker image inspect` 크기 | **교체** (멀티스테이지로 축소) | P25 |

검사 규칙 ID (실제 존재 확인)
- hadolint: DL3002, DL3006, DL3007, DL3008, DL3009, DL3013, DL3018, DL3020, DL3025, DL3042, DL4006. 출처는 https://github.com/hadolint/hadolint README(확인 2026-10-01). ⚠️출처확인필요
- Checkov Dockerfile: CKV_DOCKER_1(22번 포트), _2(HEALTHCHECK), _3(사용자 생성), _4(ADD 대신 COPY), _5(update 단독 사용), _6(MAINTAINER), _7(latest가 아닌 태그), _8(마지막 USER가 root가 아님), _9(APT), _10(절대 경로 WORKDIR), _11(FROM 별칭 중복). 출처는 https://www.checkov.io/5.Policy%20Index/dockerfile.html (확인 2026-10-01). ⚠️출처확인필요

## 1.3 앱 쪽 계약

플랫폼을 바꿔도 같은 이미지가 돌게 하는 앱 코드 쪽 약속이다. 에이전트는 코드에서 이 계약이 있는지 탐지하고, 없으면 코드 변경을 생성한다.

### 1.3.1 헬스체크 엔드포인트

| 엔드포인트 | 성격 | 내용 | 누가 쓰나 |
|---|---|---|---|
| `/healthz` | **얕은**(liveness) | 프로세스가 응답할 수 있는가. 외부 의존성은 보지 않는다. 항상 200, 수 ms 안에 응답 | k8s livenessProbe, Cloud Run liveness probe, Docker `HEALTHCHECK` |
| `/readyz` | **깊은**(readiness) | DB `SELECT 1`, 캐시 ping 등 필수 의존성을 짧은 타임아웃(1~2초)으로 확인한다. 종료 중이면 503 | k8s readinessProbe, Cloud Run startup·readiness probe, 배포 후 스모크 |
| LB 헬스체크 (ALB 대상 그룹, GCP BackendConfig, Render `healthCheckPath`, Railway `healthcheckPath`, DO `health_check`, Fly `checks`) | 플랫폼별 | 기본은 `/healthz`. DB 장애 때 모든 인스턴스가 빠지면 정적 페이지도 못 낸다 → 의존성 확인은 readiness 쪽에만 둔다(추론) | — ⚠️근거없음 |

- 근거: https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/ · "The liveness probe passes when the app itself is healthy, but the readiness probe additionally checks that each required back-end service is available." / "Incorrect implementation of liveness probes can lead to cascading failures." (확인 2026-10-01)
- "liveness는 외부 의존성을 보면 안 된다"는 문장 자체는 공식 문서에서 찾지 못했다. 위 인용에서 이끌어 낸 규칙이다(추론). ⚠️근거없음
- Cloud Run
  - liveness나 startup probe를 명시하지 않으면 TCP startup probe가 자동으로 들어간다.
  - HTTP probe는 2xx와 3xx를 성공으로 본다.
  - startup 허용 시간은 최대 600초다.
  - 출처: https://docs.cloud.google.com/run/docs/configuring/healthchecks (확인 2026-10-01)

### 1.3.2 SIGTERM 처리와 플랫폼별 유예 시간

앱 쪽 처리 순서(모든 플랫폼 공통)
1. SIGTERM을 받으면 readiness를 503으로 바꾼다.
2. 새 연결을 받지 않는다.
3. 진행 중인 요청을 마무리한다.
4. 큐 소비자는 메시지 수신을 멈추고, 처리 중인 메시지를 확인(ack)하거나 반환한다.
5. DB·Redis 풀을 닫는다.
6. exit 0으로 끝낸다.

3~6단계의 총 시간은 **플랫폼 유예 시간에서 여유분을 뺀 값**으로 잡는다. 서버 설정(Gunicorn `--graceful-timeout`, Uvicorn `--timeout-graceful-shutdown`, Node 종료 타이머)에 이 값을 넣는다.

| 플랫폼 | 종료 신호 → 강제 종료 | 설정 키 | 앱 쪽 목표값 (추론) ⚠️근거없음 |
|---|---|---|---|
| Vercel Functions | SIGTERM 후 500ms (컨테이너 이미지 함수 30초) | 없음 | 정리 작업 불가로 간주. `waitUntil`/`after`로 처리 |
| Lambda | 확장(extension) 없으면 0ms, 내부 확장 500ms, 외부 확장 2,000ms | 없음 (Lambda Web Adapter가 graceful shutdown 제공) | 정리 불가로 간주 |
| Cloud Run (서비스·잡·워커 풀) | SIGTERM → 10초 → SIGKILL, 조정 불가 | 없음 | 8초 |
| Fly.io | 기본 SIGINT, 5초 / 최대 300초 | `kill_signal = "SIGTERM"`, `kill_timeout` | `kill_timeout` − 2초 |
| Railway | `미확인`(04 문서: 기본 0초) | `drainingSeconds`(Config as Code) | `drainingSeconds` − 2초 |
| Heroku | 30초, 바꿀 수 없음(설정 문서 없음) | 없음 | 25초 |
| Render | 기본 30초, 최대 300초 | `maxShutdownDelaySeconds` | 설정값 − 5초 |
| Koyeb | 30초 (설정 가능 여부 `미확인`) | `미확인` | 25초 |
| DigitalOcean App Platform | 기본 120초, 최대 600초. 드레인 기본 15초, 최대 110초 | `termination.grace_period_seconds`, `termination.drain_seconds` | grace − 5초 |
| ECS Fargate | `stopTimeout` 기본 30초, 최대 120초. ALB 등록 해제 지연 기본 300초 | `stopTimeout`, `deregistration_delay` | stopTimeout − 5초 |
| Fargate Spot | 2분 경고 + SIGTERM | `stopTimeout` ≤ 120 | 위와 같음 |
| Azure Container Apps | 30초 (기본) | `termination_grace_period_seconds` | 25초 |
| Kubernetes (GKE·EKS·k3s) | `terminationGracePeriodSeconds` 기본 30초. preStop 시간도 여기에 포함 | `terminationGracePeriodSeconds`, `preStop` | grace − preStop − 5초 |
| Cloudflare Containers | SIGTERM → 최대 15분 → SIGKILL | `미확인` | — |
| docker compose (VM) | `stop_grace_period` 기본 10초 | `stop_grace_period` | 설정값 − 2초 |

출처: 각 플랫폼 절. k8s의 preStop은 "the hook must complete before the TERM signal to stop the container can be sent." / "The Pod's termination grace period countdown begins before the PreStop hook is executed" (https://kubernetes.io/docs/concepts/containers/container-lifecycle-hooks/, 확인 2026-10-01).

### 1.3.3 설정의 환경변수화
- 모든 환경 의존 값(DB URL, Redis URL, 외부 API 키, 허용 호스트, 쿠키 Secure 여부, 로그 레벨)은 환경변수로 읽는다. 비밀 값은 플랫폼 비밀 저장소에서 주입한다(각 플랫폼 "주변 자원").
  - 출처: https://12factor.net/config · "The twelve-factor app stores config in environment variables" (확인 2026-10-01) ⚠️출처부적격
- 빌드 시점에 값이 박히는 변수(`NEXT_PUBLIC_*`, Vite `VITE_*`)는 따로 표시한다. 이미지 하나를 여러 환경에 승격하려면 런타임에 주입하는 방식으로 바꾼다. Next.js 문서는 런타임 env로 "a singular Docker image that can be promoted through multiple environments"가 가능하다고 한다.
- 에이전트는 `.env.example`을 생성한다. 실제 값은 저장소에 쓰지 않는다.

### 1.3.4 stdout 로그
- 로그를 파일에 쓰는 설정(`logging.FileHandler`, `winston` file transport, `access.log`)은 stdout으로 바꾼다. JSON 한 줄 형식을 권장한다(추론: Cloud Logging·CloudWatch가 필드를 파싱한다). ⚠️근거없음
- 출처: https://12factor.net/logs · "A twelve-factor app never concerns itself with routing or storage of its output stream." (확인 2026-10-01) ⚠️출처부적격

### 1.3.5 마이그레이션 실행 위치

**앱 기동 시점에는 실행하지 않는다.** 인스턴스가 여러 개면 동시에 실행되고, 시간이 기동 제한(Cloud Run 4분 포트 대기 등)을 잡아먹는다(추론). 배포 직전에 **단일 실행 단계**로 돌린다. ⚠️근거없음

| 플랫폼 | 위치 | 키 / 명령 |
|---|---|---|
| Railway | 배포 전 명령 | `deploy.preDeployCommand` (IaC `preDeploy`) |
| Render | 배포 전 명령 | `preDeployCommand` |
| Fly.io | 릴리스 명령 | `[deploy] release_command` |
| Heroku | release 단계 | `Procfile`의 `release:` (타임아웃 1시간, 0이 아닌 코드면 릴리스 중단) |
| DigitalOcean | 배포 전 잡 | `jobs[].kind: PRE_DEPLOY` |
| Koyeb | `미확인` | CI 단계에서 별도 실행 |
| Vercel / Netlify / Cloudflare / Supabase | CI 단계 | 배포 명령 전에 `prisma db migrate` 등 실행 (DB가 CI에서 닿아야 함) |
| Cloud Run | Cloud Run Job | `gcloud run jobs execute migrate --wait` |
| ECS | 일회성 태스크 | `amazon-ecs-deploy-task-definition`의 `run-task: true` ("Task will run before the service is updated if both are provided") 또는 `aws ecs run-task` |
| ACA | Container Apps Job | `azurerm_container_app_job` + `az containerapp job start` |
| Kubernetes | Job | simple-web-app `k8s/base/db-migrate.yaml` 형태(`backoffLimit`, `activeDeadlineSeconds`, Complete/Failed 중 먼저 오는 쪽을 기다림) |
| VM + compose | 일회성 서비스 | `docker compose run --rm migrate` |

- 스키마 변경은 이전 버전 코드와 호환되게 쓴다(컬럼 추가 → 코드 배포 → 이전 컬럼 제거). 마이그레이션과 롤링 배포가 겹치기 때문이다(simple-web-app `docs/deploy.md` "주의").
- Prisma 명령은 버전마다 다르다.
  - ORM 8에서는 `prisma migrate deploy`가 `prisma db migrate`로, `prisma db push`가 `prisma db update`로 바뀌었다. 저장소의 Prisma 버전을 읽고 명령을 고른다.
  - ORM 7 이하는 `prisma migrate deploy`를 쓰고, `migrate dev`는 운영에서 금지된다.
- 출처 (확인 2026-10-01)
  - https://www.prisma.io/docs/orm/migrations/applying-a-migration · `prisma db migrate` "replaces Prisma ORM 7's prisma migrate deploy" ⚠️출처확인필요
  - https://www.prisma.io/docs/orm/v7/prisma-migrate/workflows/development-and-production · "`migrate dev` is a development command and should never be used in a production environment." ⚠️출처확인필요
  - https://docs.cloud.google.com/run/docs/overview/what-is-cloud-run · Jobs 용도 "Run a script to perform database migrations"
  - Django: `migrate`를 별도 배포 단계로 두라는 공식 문장은 `미확인`.

## 1.4 CI/CD

### 1.4.1 파이프라인 단계 (GitHub Actions 기준)

```
검증(lint·test·hadolint·checkov·terraform validate·kubeconform)
  → 빌드(buildx, 태그 = git sha)
  → 레지스트리 푸시(불변 태그)
  → 마이그레이션(1.3.5 위치, 실패 시 중단)
  → 배포(트래픽 없이 새 리비전 → 스모크 → 트래픽 전환, 지원 플랫폼만)
  → 스모크 테스트(/readyz + 핵심 경로 1~2개, 실패 시 롤백)
```

- 태그는 git sha로 붙이고, 레지스트리는 태그 불변으로 만든다(ECR `image_tag_mutability = "IMMUTABLE"`, Artifact Registry `docker_config.immutable_tags`). 롤백은 이전 sha로 다시 배포하는 방식이다.
- `permissions`는 최소로 준다. OIDC를 쓰려면 `id-token: write`가 필요하다.
- 무트래픽 배포를 지원하는 플랫폼: Cloud Run(`--no-traffic --tag`, `deploy-cloudrun`의 `no_traffic`·`tag` 입력), Fly `strategy = "bluegreen"`/`canary`, ECS(서킷 브레이커 자동 롤백), k8s(롤아웃 + readiness). 그 외 플랫폼은 배포 후 스모크가 실패하면 이전 배포로 되돌린다(Vercel instant rollback, Render·Railway 재배포 등).

### 1.4.2 공식 액션과 버전 (GitHub API `releases/latest`, 확인 2026-10-01)

| 액션 | 최신 | 사용 | OIDC 입력 |
|---|---|---|---|
| actions/checkout | v7.0.1 | `@v7` | — |
| docker/setup-buildx-action | v4.4.1 | `@v4` | — |
| docker/login-action | v4.6.0 | `@v4` | — |
| docker/build-push-action | v7.4.0 | `@v7` | — |
| docker/metadata-action | v6.2.0 | `@v6` | — |
| google-github-actions/auth | v3 | `@v3` | `workload_identity_provider`, `service_account` |
| google-github-actions/setup-gcloud | v3.0.1 | `@v3` | — |
| google-github-actions/deploy-cloudrun | v3 | `@v3` | 입력 `service`/`job`/`image`/`region`/`env_vars`/`secrets`/`flags`/`no_traffic`/`tag` |
| google-github-actions/get-gke-credentials | v3.0.0 | `@v3` | `cluster_name`, `location` |
| aws-actions/configure-aws-credentials | v6.3.0 | `@v6` | `role-to-assume`, `aws-region`, `audience` |
| aws-actions/amazon-ecr-login | v2.1.7 | `@v2` | — |
| aws-actions/amazon-ecs-render-task-definition | v1.9.0 | `@v1` | — |
| aws-actions/amazon-ecs-deploy-task-definition | v2.6.3 | `@v2` | `wait-for-service-stability`, `run-task` |
| aws-actions/amazon-ecs-deploy-express-service | v1.2.2 | `@v1` | `service-name`, `image`, `execution-role-arn`, `infrastructure-role-arn` |
| azure/login | v3.1.0 | `@v3` | `client-id`, `tenant-id`, `subscription-id` |
| azure/container-apps-deploy-action | v2 (2024-10-17, action.yml이 node16) | `@v2` | `acrName`, `containerAppName`, `resourceGroup`, `imageToDeploy` |
| hashicorp/setup-terraform | v4.0.1 | `@v4` | — |
| cloudflare/wrangler-action | v4.1.3 | `@v4` | 토큰(`apiToken`, `accountId`) |
| superfly/flyctl-actions/setup-flyctl | 문서 예시 `@master` (릴리스 태그 `미확인`) | — | 토큰(`FLY_API_TOKEN`) |
| digitalocean/app_action/deploy | `@v2` | — | 토큰(`DIGITALOCEAN_ACCESS_TOKEN`) |
| supabase/setup-cli | 문서 예시 `@v1` | — | 토큰(`SUPABASE_ACCESS_TOKEN`) |
| railwayapp/config | 존재 확인, 버전 `미확인` | — | 토큰 |

- azure/container-apps-deploy-action은 2024년 이후 릴리스가 없고 node16 런타임이다(추론: 러너에서 경고나 실패가 날 수 있다). 대안은 `az containerapp update --image`를 직접 호출하는 것이다. ⚠️근거없음

### 1.4.3 클라우드 인증: OIDC (정적 키 금지)

| 클라우드 | 신뢰 설정 (IaC) | 워크플로 | 출처 (확인 2026-10-01) |
|---|---|---|---|
| GCP | `google_iam_workload_identity_pool` + `google_iam_workload_identity_pool_provider` (issuer `https://token.actions.githubusercontent.com/`, `attribute_mapping`에 `google.subject` 필수, `attribute_condition`으로 조직·저장소 제한. 숫자 `*_id` 필드 권장) + 서비스 계정에 `roles/iam.workloadIdentityUser` | `google-github-actions/auth@v3` | https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines · "you must use an attribute condition that restricts access to tokens issued by your GitHub organization" |
| AWS | `aws_iam_openid_connect_provider` (url `https://token.actions.githubusercontent.com`, `client_id_list = ["sts.amazonaws.com"]`) + 역할 신뢰 정책 `token.actions.githubusercontent.com:sub = repo:<org>/<repo>:ref:refs/heads/<branch>` | `aws-actions/configure-aws-credentials@v6` | https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws · `thumbprint_list`는 GitHub에 대해 사용되지 않음(provider 문서) |
| Azure | 앱 등록 또는 사용자 할당 ID + 페더레이션 자격 증명(리소스 이름 `미확인`) | `azure/login@v3` | 페더레이션 자격 증명 Terraform 리소스 `미확인` |

- GitHub 문서: "requires a `permissions` setting with `id-token: write`" / "No cloud secrets: You won't need to duplicate your cloud credentials as long-lived GitHub secrets." (https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-cloud-providers, 확인 2026-10-01)
- Checkov로 OIDC 신뢰 범위를 검사한다: CKV_GCP_118("Ensure IAM workload identity pool provider is restricted"), CKV_GCP_125("Ensure GCP GitHub Actions OIDC trust policy is configured securely").

**OIDC를 쓸 수 없는 플랫폼**: Vercel, Netlify, Cloudflare, Railway, Render, Fly, Heroku, DigitalOcean, Koyeb, Supabase는 GitHub OIDC로 배포 인증을 받지 못한다(열어 본 CI 문서 기준). Vercel은 "Vercel doesn't support OIDC for authenticating the GitHub Actions deployment itself."라고 명시한다(https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel). 이들 플랫폼은 정적 토큰을 GitHub Environment secret에 넣고 다음 규칙을 따른다(추론). ⚠️근거없음
- 범위가 가장 좁은 토큰을 쓴다(Railway 프로젝트 토큰은 환경 단위, Fly `fly tokens create deploy`는 앱 단위 배포 토큰).
- `environment` 보호 규칙(브랜치 제한)을 건다.
- 만료일을 둔다(Fly `-x`).

### 1.4.4 워크플로 골격 (Cloud Run 예)

```yaml
name: deploy
on: { push: { branches: [main] } }
permissions: { contents: read, id-token: write }
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v7
      - uses: google-github-actions/auth@v3
        with:
          workload_identity_provider: ${{ vars.WIF_PROVIDER }}
          service_account: ${{ vars.DEPLOY_SA }}
      - uses: google-github-actions/setup-gcloud@v3
      - run: gcloud auth configure-docker asia-northeast3-docker.pkg.dev --quiet
      - uses: docker/setup-buildx-action@v4
      - uses: docker/build-push-action@v7
        with: { push: true, tags: "${{ vars.IMAGE }}:${{ github.sha }}" }
      - run: gcloud run jobs deploy migrate --image ${{ vars.IMAGE }}:${{ github.sha }} --region asia-northeast3 && gcloud run jobs execute migrate --region asia-northeast3 --wait
      - uses: google-github-actions/deploy-cloudrun@v3
        id: deploy
        with: { service: app, region: asia-northeast3, image: "${{ vars.IMAGE }}:${{ github.sha }}", no_traffic: true, tag: "sha-${{ github.sha }}" }
      - run: curl -fsS --retry 5 "${{ steps.deploy.outputs.url }}/readyz"   # 태그 URL 출력 이름은 미확인
      - run: gcloud run services update-traffic app --region asia-northeast3 --to-latest
```

- `gcloud run jobs deploy`는 공식 문서에서 열어 확인하지 않았다(`미확인`). 확인된 형태는 `gcloud run jobs execute JOB --wait --region=REGION`이다.
- `deploy-cloudrun`에서 태그 URL이 어느 출력으로 나오는지 `미확인`이다. 생성기는 `gcloud run services describe`로 태그 URL을 읽는 방식을 대안으로 둔다.

## 1.5 공통 검증 명령

생성물마다 아래를 실행해서 모두 통과해야 "검증됨"으로 표시한다. 명령은 모두 CI와 로컬 양쪽에서 돈다.

| 대상 | 명령 | 통과 기준 |
|---|---|---|
| Dockerfile 정적 | `hadolint Dockerfile` / `checkov -f Dockerfile --framework dockerfile` | 1.2 표의 교체·부분 수정 규칙 위반 0건 |
| 빌드 | `docker build -t app:ci .` | 성공 |
| non-root | `docker image inspect app:ci --format '{{.Config.User}}'` | 빈 값, `root`, `0`이 아님 |
| 기동·헬스 | `docker run -d --name app -e PORT=8080 -p 8080:8080 --env-file .env.ci app:ci` → `curl -fsS --retry 10 --retry-connrefused localhost:8080/healthz` | 200 |
| 포트 계약 | `-e PORT=9090 -p 9090:9090`으로 다시 실행 → 9090에서 200 | `PORT`를 따른다 |
| SIGTERM | `time docker stop -t 30 app` → `docker inspect app --format '{{.State.ExitCode}}'` | 30초보다 훨씬 빨리 끝나고 종료 코드가 0 또는 143(SIGTERM). 137이면 SIGKILL로 끝난 것(PID 1이 신호를 받지 못함) (추론: 코드 의미는 128+신호 번호 관례) ⚠️근거없음 |
| 진행 중 요청 | 느린 엔드포인트 호출 중 `docker stop` → 그 요청이 200으로 끝나는가 | 드레인 동작 (추론) ⚠️근거없음 |
| compose | `docker compose config --quiet` | 오류 없음 (https://docs.docker.com/reference/cli/docker/compose/config/ · "only validate the configuration, don't print anything") |
| Terraform | `terraform fmt -check` → `terraform init -backend=false` → `terraform validate` → `terraform plan` (실제 계정) | validate 성공, plan에 의도하지 않은 destroy 없음 |
| Terraform 정적 | `checkov -d infra/ --framework terraform` | 각 플랫폼 절의 Checkov ID 통과(예외는 사유와 함께 `#checkov:skip=`) |
| k8s | `kubectl kustomize <overlay> \| kubeconform -strict -summary -schema-location default -schema-location '<CRD 카탈로그>'` → `kubectl apply --dry-run=server -k <overlay>` | 오류 없음 |
| k8s 정적 | `checkov -d k8s/ --framework kubernetes` | P-K 절의 ID |
| 배포 후 스모크 | `curl -fsS https://<url>/readyz` + 핵심 경로. 실패하면 롤백 | 200 |

- kubeconform 플래그: `-strict`("disallow additional properties not in schema or duplicated keys"), `-summary`, `-schema-location`(여러 번 지정 가능), `-ignore-missing-schemas`. CRD 카탈로그 예: `https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json`. 최신 v0.8.0. 출처는 https://github.com/yannh/kubeconform (확인 2026-10-01). ⚠️출처확인필요
- `docker stop`의 SIGTERM → 타임아웃 → SIGKILL 동작을 설명하는 docker stop 문서 원문은 열지 않았다(`미확인`). Dockerfile 레퍼런스의 "doesn't receive a `SIGTERM` from `docker stop`"(셸 형식일 때)만 확인했다.

---

# 파트 2. 플랫폼별

각 절의 "핵심 설정"은 [dimensions.md](../dimensions.md) 차원 ID(A1~G3)와 연결했다. 능력값의 근거는 04·05 문서에 있고, 이 문서는 산출물과 키 이름의 근거만 적는다.

## 티어 0

## P1. Vercel Functions (Hobby · Pro · Enterprise)
- **산출물 목록:**
  - 설정 파일 `vercel.json`
    - `$schema: https://openapi.vercel.sh/vercel.json`
    - `vercel.toml`이나 `vercel.ts`도 쓸 수 있지만 한 프로젝트에 하나만 둔다.
    - 기존 파일이 있으면 그 형식을 유지한다.
  - Next.js 라우트별 `export const maxDuration`.
  - Terraform `vercel/vercel`(v5.18.0)
    - 리소스: `vercel_project`, `vercel_project_environment_variable`(또는 `vercel_project_environment_variables`), `vercel_project_domain`, `vercel_project_crons`, `vercel_dns_record`, `vercel_oidc_federation_policy`
    - `vercel_project.resource_config`(`fluid`, `function_default_cpu_type`, `function_default_regions`, `function_default_timeout`)가 메모리·CPU를 정하는 유일한 IaC 경로다. `vercel.json`에서는 메모리를 정할 수 없다.
    - 배포는 Terraform `vercel_deployment`보다 CLI가 단순하다(추론). ⚠️근거없음
  - CI 단계: `vercel pull --yes --environment=production` → `vercel build --prod` → `vercel deploy --prebuilt --prod`. 마이그레이션은 deploy 앞의 별도 단계다.
  - Dockerfile은 없다.
- **요구 수준에 따라 바뀌는 핵심 설정:**
  - D5 한 지역: `regions: ["icn1"]`. 기본값은 `iad1`이라 서울 DB를 쓰면 반드시 넣는다. Hobby는 1개, Pro는 5개(문서 간 3/5 `[충돌]`), Enterprise는 전체 리전이다.
  - A2: `functions["api/**"].maxDuration`(Hobby 최대 300, Pro·Enterprise 최대 800, 베타 1800). Next.js는 `export const maxDuration`. 요구가 한도를 넘으면 플랫폼을 바꾼다.
  - A6: 메모리는 `vercel_project.resource_config` 또는 대시보드에서 정한다. Hobby는 변경할 수 없다.
  - B3: `crons: [{ path, schedule }]`. 시간대는 UTC이고 Hobby는 하루 1회(±59분)다. 이보다 잦은 식은 배포가 실패한다.
  - F1: `functionFailoverRegions`(Enterprise만).
  - A4: 코드에서 `waitUntil`이나 Next.js `after()`를 쓴다. 함수 시간 안에서만 동작한다.
  - C8: DB 풀에 `attachDatabasePool` 적용.
- **함께 필요한 주변 자원:**
  - DB·캐시: Marketplace(Neon, Upstash 등)의 환경변수 주입 또는 외부 DB 공개 엔드포인트 + 풀러.
  - 사설 연결: Secure Compute(Enterprise, AWS VPC 피어링, 일부 팀은 셀프서비스 불가).
  - 비밀: `vercel env add NAME production`(production은 기본 sensitive). Terraform은 `vercel_project_environment_variable`(`sensitive`).
  - 도메인: `vercel_project_domain` + DNS.
  - 외부 클라우드 접근: Vercel OIDC 페더레이션(`VERCEL_OIDC_TOKEN`)으로 AWS·GCP 역할을 맡는다(밖으로 나가는 인증만).
  - **자동화 불가 단계**: Git 연동 앱 설치(`vercel_project.git_repository`의 전제 조건), CI용 `VERCEL_TOKEN` 발급, Secure Compute 네트워크 생성(대시보드나 영업 담당).
- **검증 명령:**
  - `npx vercel build`(로컬에서 `.vercel/output` 생성 성공 = 설정과 빌드 검증)
  - JSON 스키마 검증(`ajv validate -s https://openapi.vercel.sh/vercel.json -d vercel.json`, 도구 사용은 추론) ⚠️근거없음
  - `terraform validate`
  - 배포 후 `curl -fsS $(vercel deploy --prebuilt)/api/health`(deploy의 stdout은 항상 배포 URL)
  - Checkov 규칙은 없다(`미확인`: Vercel provider 대상 체크를 찾지 못함).
- **출처 (확인 2026-10-01):**
  - https://vercel.com/docs/project-configuration/vercel-json · "Memory cannot be set in `vercel.json` with Fluid compute enabled."
  - https://vercel.com/docs/functions/configuring-functions/duration
  - https://vercel.com/docs/functions/configuring-functions/region · "Deploying to more regions than your plan allows causes the deployment to fail before the build step."
  - https://vercel.com/docs/cron-jobs · https://vercel.com/docs/cli/build · https://vercel.com/docs/cli/deploy · https://vercel.com/docs/cli/env
  - https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel
  - https://vercel.com/docs/oidc
  - https://vercel.com/docs/networking/secure-compute
  - https://registry.terraform.io/providers/vercel/vercel/latest (레지스트리 API로 리소스 목록 확인)

## P2. Vercel Edge runtime
- **산출물 목록:** P1과 같고, 라우트에 `export const runtime = 'edge'`를 둔다. **새로 생성하지 않는다.** Vercel이 Node.js 이전을 권고하고, Next.js 16.3부터 `runtime = 'edge'`를 지원하지 않는다. 기존 코드에 있으면 판정은 **교체**(Node.js 런타임으로)다.
- **요구 수준에 따라 바뀌는 핵심 설정:** A2: 25초 안에 응답을 시작해야 하고 스트리밍은 300초까지다. 넘으면 Node.js 함수로 옮긴다.
- **함께 필요한 주변 자원:** P1과 같다. Secure Compute는 Edge를 지원하지 않는다.
- **검증 명령:** `grep -r "runtime = 'edge'"`로 탐지한 뒤 P1과 같다.
- **출처 (확인 2026-10-01):** https://vercel.com/docs/functions/runtimes/edge · "We recommend migrating from edge to Node.js for improved performance and reliability." / "Starting in Next.js 16.3, setting `runtime = 'edge'` is no longer supported."

## P3. Netlify Functions
- **산출물 목록:**
  - 설정 파일 `netlify.toml`
    - `[build] command, publish`
    - `[functions] directory = "netlify/functions", node_bundler = "esbuild"`
    - `[functions."name"] schedule`
    - `[[redirects]]`, `[[headers]]`, `[context.production]`
    - 이 파일이 UI 설정보다 우선한다.
  - 함수 코드 안의 `export const config = { schedule, path, region }`.
  - Terraform `netlify/netlify`(v0.4.4)
    - 관리 대상: `environment_variable`, `site_build_settings`, `site_domain_settings`, `dns_record`, `dns_zone` 등
    - **사이트를 생성하는 리소스는 없다.** `site`는 data source뿐이다. 사이트는 CLI(`netlify sites:create`, 명령 원문 `미확인`)나 UI로 만들고 Terraform은 설정만 맡는다.
  - CI 단계: `netlify deploy --prod --site $NETLIFY_SITE_ID --auth $NETLIFY_AUTH_TOKEN`. 기본으로 빌드까지 한다. 빌드를 건너뛰려면 `--no-build`.
- **요구 수준에 따라 바뀌는 핵심 설정:**
  - D5: 함수 리전은 기본 `cmh`(오하이오)다. Pro 이상은 UI, 함수별 `config.region`, 또는 `[functions.x] region`으로 `nrt`(도쿄) 등을 고를 수 있다. 서울은 없다. 리전을 바꾸면 재배포가 필요하다.
  - A2: 동기 60초는 고정이다. 백그라운드 함수(15분)는 파일 이름 규칙으로 정한다(`-background` 접미사, 원문 `미확인`).
  - B3: 예약 함수는 UTC 기준이고, 게시된 배포에서만 돌며, 실행 시간은 30초다.
  - A6: `memory`·`vcpu` 설정은 크레딧 기반 Pro·Enterprise에서만 가능하다.
- **함께 필요한 주변 자원:**
  - 비밀: `netlify env:set KEY value --scope functions --context production`, 또는 Terraform `netlify_environment_variable`.
  - 사설 DB: Private Connectivity(Enterprise 애드온, 함수 리전은 `cmh`·`fra`·`lhr`만).
  - 도메인: `site_domain_settings` + DNS.
  - **자동화 불가 단계**
    - 사이트 생성(Terraform으로 불가)
    - Git 연결: `netlify init --manual`이면 deploy key와 webhook을 Git 제공자에 직접 등록해야 한다.
    - 개인 액세스 토큰 발급(UI)
    - 리전 지정(UI)
- **검증 명령:** `netlify build --dry`, `netlify build --context deploy-preview`, `terraform validate`, 배포 후 스모크(`netlify deploy --json` 출력의 URL, 필드 이름 `미확인`). Checkov 규칙은 `미확인`.
- **출처 (확인 2026-10-01):**
  - https://docs.netlify.com/build/configure-builds/file-based-configuration/ · "settings specified in netlify.toml override any corresponding settings in the Netlify UI."
  - https://docs.netlify.com/build/functions/configuration.md · "Synchronous execution limit | 60 seconds | No"
  - https://docs.netlify.com/build/functions/scheduled-functions/
  - https://cli.netlify.com/commands/deploy/ · "Build your project (unless –no-build is specified)"
  - https://docs.netlify.com/api-and-cli-guides/cli-guides/get-started-with-cli.md
  - https://docs.netlify.com/manage/security/private-connectivity.md
  - https://registry.terraform.io/providers/netlify/netlify/latest

## P4. Netlify Edge Functions
- **산출물 목록:** `netlify.toml`의 `[[edge_functions]] path = "/admin" function = "auth"` 또는 인라인 `export const config = { path }`. 디렉터리는 `netlify/edge-functions/`. 나머지는 P3와 같다.
- **요구 수준에 따라 바뀌는 핵심 설정:** A2와 A6: 요청당 CPU 50ms, 메모리 512MB. 인증·리다이렉트 같은 가벼운 로직만 둔다. 무거운 처리가 탐지되면 P3로 옮긴다.
- **함께 필요한 주변 자원:** P3와 같다. 고정 IP는 불가(04 문서).
- **검증 명령:** P3와 같다.
- **출처 (확인 2026-10-01):** https://docs.netlify.com/build/edge-functions/declarations/ · https://docs.netlify.com/build/edge-functions/limits.md · "CPU execution time per request: 50 ms"

## P5. Cloudflare Workers · Pages Functions
- **산출물 목록:**
  - 설정 파일 `wrangler.jsonc`. 새 프로젝트에 권장되고, 일부 새 기능은 JSON 설정에서만 쓸 수 있다.
    - 키: `main`, `compatibility_date`(필수, `yyyy-mm-dd`), `compatibility_flags`, `triggers.crons`, `observability.enabled`, `placement.mode = "smart"`, `limits.cpu_ms`
    - 바인딩: D1, R2, KV, Hyperdrive, Queues
  - 신규 프로젝트는 Workers로 만든다. Pages는 기존 것을 유지하는 경우만 쓴다("Start new projects with Workers.").
  - Terraform `cloudflare/cloudflare`(v5.26.0)
    - 리소스: `cloudflare_worker` + `cloudflare_worker_version` + `cloudflare_workers_deployment`(베타, `cloudflare_workers_script`보다 권장), `cloudflare_workers_route`, `cloudflare_workers_custom_domain`, `cloudflare_workers_cron_trigger`, `cloudflare_d1_database`, `cloudflare_r2_bucket`, `cloudflare_hyperdrive_config`, `cloudflare_queue`, `cloudflare_workers_kv_namespace`
    - Terraform은 번들링을 하지 않는다. 공식 권장은 Terraform이 Worker와 Deployment를 관리하고, 빌드와 버전은 Wrangler가 관리하는 분담이다.
  - CI 단계: `cloudflare/wrangler-action@v4`(`apiToken`, `accountId`) 또는 `npx wrangler deploy`. 마이그레이션(D1이면 `wrangler d1 migrations apply`, 명령 원문 `미확인`)은 deploy 앞에 둔다.
- **요구 수준에 따라 바뀌는 핵심 설정:**
  - A2와 A6: `limits.cpu_ms`(Paid 기본 30,000, 최대 300,000).
  - B3: `triggers.crons`. 끄려면 `crons = []`로 둔다. 주석 처리만 하면 트리거가 꺼지지 않는다.
  - D5와 C8: `placement.mode = "smart"`(DB 가까이 실행), 또는 `placement.region = "aws:ap-northeast-2"` 형태(값 형식은 문서 예시 `"aws:us-east-1"` 기준).
  - A4: `ctx.waitUntil()`은 응답 후 최대 30초다.
  - 런타임 호환: `compatibility_date`가 2026-08-04 이후면 `nodejs_compat`이 기본으로 켜진다.
- **함께 필요한 주변 자원:**
  - 비밀: `wrangler secret put KEY`, `wrangler secret bulk`, 또는 `deploy --secrets-file`.
  - 사설 DB: Hyperdrive(Postgres·MySQL, Free·Paid), Workers VPC(Cloudflare Tunnel 경유).
  - 도메인: `cloudflare_workers_custom_domain`(존이 Cloudflare에 있어야 함).
  - **자동화 불가 단계:** API 토큰 발급(대시보드의 "Edit Cloudflare Workers" 템플릿), 도메인 존 온보딩(네임서버 변경), Workers Paid 구독.
- **검증 명령:**
  - `npx wrangler deploy --dry-run --outdir build`(컴파일만 하고 배포하지 않음)
  - `npx wrangler types --check`
  - `npx wrangler check startup`(시작 단계 분석)
  - `terraform validate`
  - 배포 후 `curl`
  - 설정 파일만 검증하는 별도 명령은 문서에 없다.
  - Checkov 규칙은 `미확인`.
- **출처 (확인 2026-10-01):**
  - https://developers.cloudflare.com/workers/wrangler/configuration/ · "Cloudflare recommends using `wrangler.jsonc` for new projects"
  - https://developers.cloudflare.com/workers/configuration/compatibility-flags/
  - https://developers.cloudflare.com/workers/platform/limits/
  - https://developers.cloudflare.com/workers/runtime-apis/context/
  - https://developers.cloudflare.com/workers/platform/infrastructure-as-code/
  - https://developers.cloudflare.com/workers/wrangler/commands/workers/
  - https://developers.cloudflare.com/workers/ci-cd/external-cicd/github-actions/
  - https://developers.cloudflare.com/hyperdrive/ · https://developers.cloudflare.com/workers-vpc/ · https://developers.cloudflare.com/pages/
  - https://registry.terraform.io/providers/cloudflare/cloudflare/latest

## P6. Cloudflare Durable Objects
- **산출물 목록:**
  - `wrangler.jsonc`: `durable_objects.bindings` + **`exports`**(선언형, 신규 권장). 레거시는 `migrations`(`new_sqlite_classes`)이고, 한 Worker에는 둘 중 하나만 쓸 수 있다.
  - DO 클래스 코드.
  - Terraform: DO 마이그레이션은 첫 apply에서 실패하는 문제가 있다(공식 문서 "running this in Terraform will fail the first time the plan is applied"). DO는 **Wrangler로만** 배포한다.
- **요구 수준에 따라 바뀌는 핵심 설정:**
  - A3: 웹소켓 하이버네이션 API(코드).
  - F4: 배포할 때마다 모든 연결이 끊긴다(04 문서). 클라이언트 재연결 코드를 생성한다.
  - D5: 위치 힌트(`locationHint`, 키 원문 `미확인`).
- **함께 필요한 주변 자원:** P5와 같다.
- **검증 명령:** `wrangler deploy --dry-run`, `wrangler types --check`.
- **출처 (확인 2026-10-01):** https://developers.cloudflare.com/durable-objects/reference/durable-objects-migrations/ · "The `exports` field replaces the imperative `migrations` array" · https://developers.cloudflare.com/workers/platform/infrastructure-as-code/

## P7. Cloudflare Containers
- **산출물 목록:**
  - Dockerfile(파트 1)
  - `wrangler.jsonc`의 `containers: [{ class_name, image: "./Dockerfile", instance_type, max_instances }]`
    - `instance_type`: 기본 `lite`, 그 밖에 `basic`, `standard-1`~`standard-4`
    - `max_instances`: 기본 20
  - DO 클래스(컨테이너 수명 제어)
  - **Terraform 경로가 없다.** `cloudflare_worker_version.containers`에는 `class_name`만 있고 이미지·인스턴스 타입 설정이 없다. 배포는 `wrangler deploy` 하나다. 로컬에서 Docker가 돌고 있어야 하며, Wrangler가 이미지를 빌드해 푸시한다.
- **요구 수준에 따라 바뀌는 핵심 설정:**
  - A6: `instance_type`.
  - D2와 D3: `max_instances`.
  - A5: `sleepAfter`(기본 10분).
  - 준비 신호: `defaultPort`. 컨테이너가 이 포트를 열 때까지 요청을 막는다.
  - F4: SIGTERM 후 최대 15분.
  - B2: 재시작하면 디스크가 초기화된다. 영속 데이터는 R2·D1로 옮긴다.
- **함께 필요한 주변 자원:** P5와 같다. Workers Paid 구독이 필요하다.
- **검증 명령:**
  - 파트 1 docker 검증 + `wrangler deploy --dry-run`.
  - 운영 외(non-production) Workers Builds는 기본으로 `wrangler versions upload`를 쓰는데, 이 명령은 이미지를 갱신하지 않는다. 스모크 테스트에서 이미지 버전을 확인한다.
- **출처 (확인 2026-10-01):** https://developers.cloudflare.com/containers/ · "Available on Workers Paid plan" · https://developers.cloudflare.com/containers/get-started/ · https://developers.cloudflare.com/containers/faq/ · https://developers.cloudflare.com/workers/wrangler/configuration/

## P8. Railway
- **산출물 목록:**
  - **`.railway/railway.ts`**(Infrastructure as Code, GA, 패키지는 `npm install railway`)
    - `railway.json`과 `railway.toml`(Config as Code)은 deprecated다.
    - 기존 파일은 이미 쓰던 서비스에 한해 **2026-12-01까지만** 동작하고, 새 서비스는 쓸 수 없다.
    - 기존 `railway.json`이 있으면 판정은 **교체**(railway.ts로 이전)다.
  - Dockerfile(파트 1). Railpack 자동 빌드 대신 Dockerfile로 재현성을 확보한다(추론). ⚠️근거없음
  - CLI: `railway config plan`, `railway config apply`. GitHub Action `railwayapp/config`.
  - Terraform: 공식 provider는 없다. 커뮤니티 `terraform-community-providers/railway`(v0.6.2, 리소스 `railway_project`, `railway_environment`, `railway_service`, `railway_service_domain`, `railway_custom_domain`, `railway_variable` 등)가 있다. 신규 생성에는 쓰지 않는다(추론: 공식 IaC가 생겼고 커뮤니티 provider는 유지 보장이 없다). ⚠️근거없음
  - CI 단계: `RAILWAY_TOKEN=… railway up --service <id> --ci`, 또는 `railway config apply`.
- **요구 수준에 따라 바뀌는 핵심 설정:** 이름은 railway.ts 키이고, 괄호 안은 레거시 railway.json 키다.
  - F1과 D2: `replicas`(`deploy.multiRegionConfig.<region>.numReplicas`).
  - C9: `preDeploy`(`deploy.preDeployCommand`). 마이그레이션 위치다.
  - F4: `healthcheck`, `healthcheckTimeout`(`deploy.healthcheckPath`, `healthcheckTimeout`).
  - F4: 드레인과 겹침 배포는 `deploy.drainingSeconds`, `deploy.overlapSeconds`. railway.ts에 대응하는 키는 `미확인`.
  - B3: `deploy.cronSchedule`. railway.ts 키는 `미확인`.
  - B2: `volumeMounts`. 볼륨을 붙이면 레플리카를 쓸 수 없다(04 문서).
  - 재시작 정책은 `deploy.restartPolicyType`(`ON_FAILURE`/`ALWAYS`/`NEVER`).
- **함께 필요한 주변 자원:**
  - DB: Railway Postgres 플러그인 또는 외부 DB(서울 리전 없음, 싱가포르).
  - 비밀: 서비스 변수(railway.ts 또는 커뮤니티 provider `railway_variable`).
  - 도메인: 커스텀 도메인 + DNS.
  - 고정 IP는 Pro에서만.
  - **자동화 불가 단계:** 프로젝트 토큰 발급, GitHub 앱 승인(`미확인`).
- **검증 명령:**
  - `railway config plan`(적용 전 차이)
  - 레거시 파일이면 `$schema` `https://railway.com/railway.schema.json`으로 JSON 스키마 검증(추론) ⚠️근거없음
  - 파트 1 docker 검증
  - 배포 후 스모크
- **출처 (확인 2026-10-01):**
  - https://docs.railway.com/config-as-code · "continue to work for services that already use them until 2026-12-01 (hard cutoff)." ⚠️출처확인필요
  - https://docs.railway.com/infrastructure-as-code · "Config as Code (`railway.json` / `railway.toml`) is deprecated. Infrastructure as Code is the replacement." ⚠️출처확인필요
  - https://docs.railway.com/infrastructure-as-code/reference ⚠️출처확인필요
  - https://docs.railway.com/reference/config-as-code ⚠️출처확인필요
  - https://docs.railway.com/cli/deploying ⚠️출처확인필요
  - https://registry.terraform.io/providers/terraform-community-providers/railway/latest ⚠️출처확인필요

## P9. Render
- **산출물 목록:**
  - 설정 파일 `render.yaml`(Blueprint)
    - `services[]`의 `type`: `web`/`worker`/`cron`/`pserv`
    - `runtime: docker`, `dockerfilePath`, `healthCheckPath`, `preDeployCommand`, `numInstances` 또는 `scaling`, `region: singapore`, `plan`, `envVars`, `maxShutdownDelaySeconds`, `disk`
    - `databases[]`
  - Dockerfile(파트 1).
  - Terraform `render-oss/render`(파트너, v1.9.1): `render_web_service`, `render_background_worker`, `render_cron_job`, `render_private_service`, `render_postgres`, `render_keyvalue`, `render_env_group`, `render_env_group_link`, `render_registry_credential`, `render_project`.
  - **Blueprint와 Terraform 중 하나만** 고른다. 같은 자원을 여러 Blueprint로 관리하지 말라는 문서 경고가 있다. Terraform과 Blueprint를 섞는 문제는 (추론)이다. ⚠️근거없음
  - CI 단계: 이미지를 레지스트리에 푸시한 뒤 `render deploys create <service> --wait`(`RENDER_API_KEY`), 또는 deploy hook URL에 `imgURL`을 넘긴다.
- **요구 수준에 따라 바뀌는 핵심 설정:**
  - F4: `maxShutdownDelaySeconds`(기본 30, 최대 300).
  - F4: `healthCheckPath`(웹 서비스만).
  - C9: `preDeployCommand`(빌드 후, 시작 전 실행).
  - D2와 D3: `scaling.minInstances`, `maxInstances`, `targetCPUPercent`(오토스케일은 Pro 워크스페이스, 04 문서), 또는 `numInstances`.
  - B2: `disk`. 붙이면 인스턴스 1개가 되고 무중단 배포를 할 수 없다(04 문서). 디스크가 필요하면 오브젝트 스토리지로 바꾸는 쪽을 우선한다.
  - D5: `region: singapore`(서울 없음).
  - B3: `type: cron` + `schedule`.
- **함께 필요한 주변 자원:**
  - DB: `databases` 또는 `render_postgres`. Free Postgres는 30일 뒤 만료된다(04 문서).
  - 비밀: `envVars`의 `sync: false`는 Blueprint 최초 생성 때만 값 입력을 요청한다.
  - Env Group, 커스텀 도메인 + DNS.
  - **자동화 불가 단계:** Blueprint 최초 생성("New > Blueprint" 후 저장소 Connect), Git 제공자 연결, API 키 발급. API나 CLI로 Blueprint를 생성할 수 있는지는 `미확인`.
- **검증 명령:**
  - `render blueprints validate render.yaml`
  - API Validate Blueprint 엔드포인트(`valid` 필드)
  - SchemaStore JSON Schema 검증
  - `terraform validate`
  - 파트 1 docker 검증
  - 배포 후 스모크
- **출처 (확인 2026-10-01):**
  - https://render.com/docs/blueprint-spec · "Validate your Blueprint file with the following Render CLI command: `render blueprints validate render.yaml`" ⚠️출처확인필요
  - https://render.com/docs/deploys · "default 30 seconds" ⚠️출처확인필요
  - https://render.com/docs/cli · https://render.com/docs/deploy-hooks · https://render.com/docs/infrastructure-as-code ⚠️출처확인필요
  - https://registry.terraform.io/providers/render-oss/render/latest ⚠️출처확인필요

## P10. Fly.io Machines
- **산출물 목록:**
  - 설정 파일 `fly.toml`
    - `app`, `primary_region = "nrt"`, `kill_signal`, `kill_timeout`
    - `[build] dockerfile`
    - `[deploy] release_command`, `strategy`
    - `[http_service]`(`internal_port`, `force_https`, `auto_stop_machines`, `auto_start_machines`, `min_machines_running`, `[http_service.concurrency]`), `[[http_service.checks]]`
    - `[[vm]] size/memory`, `[processes]`, `[[mounts]]`
  - Dockerfile(파트 1).
  - Terraform `fly-apps/fly`는 2024-03-01에 저장소가 보관되었고 공식적으로 비권장이다. **생성하지 않는다.** IaC 대신 `fly.toml` + flyctl을 쓴다.
  - CI 단계: `superfly/flyctl-actions/setup-flyctl@master` → `flyctl deploy --remote-only`(`FLY_API_TOKEN`).
- **요구 수준에 따라 바뀌는 핵심 설정:**
  - F4
    - `kill_signal = "SIGTERM"`. 기본이 SIGINT라 파트 1 규칙과 맞추려면 반드시 넣는다.
    - `kill_timeout`(기본 5초, 최대 300초).
    - `strategy`: `rolling`/`bluegreen`/`canary`/`immediate`. bluegreen은 헬스체크가 있어야 한다(추론). ⚠️근거없음
  - A5와 G3: `auto_stop_machines = "stop"|"suspend"|"off"`, `min_machines_running`(주 리전에서만 적용).
  - A1과 A4: 상시 워커가 있으면 `[processes]`에 `worker`를 두고 `auto_stop_machines = "off"`로 한다.
  - D2: `[http_service.concurrency] type = "requests", soft_limit, hard_limit`.
  - A6: `[[vm]] size = "shared-cpu-1x"`, `memory = "1gb"`.
  - C9: `release_command`(머신을 만들거나 갱신하기 전에 실행).
  - B2: `[[mounts]]`. 볼륨은 머신 1대에 고정되고 복제되지 않는다(04 문서).
  - D5: `primary_region = "nrt"`(서울 없음).
- **함께 필요한 주변 자원:**
  - 비밀: `fly secrets set`(명령 원문 `미확인`).
  - 사설 네트워크: 6PN(앱 간, 원문 `미확인`).
  - DB: 외부 관리형 DB 또는 Fly 제공 Postgres(`미확인`).
  - 인증서: `fly certs add example.com` 후 DNS A/AAAA 또는 CNAME 설정.
  - 배포 토큰: `fly tokens create deploy -x 999999h`. 만료를 짧게 두는 것을 권장한다(추론). ⚠️근거없음
  - **자동화 불가 단계:** DNS 레코드 설정(외부 DNS일 때), 결제 수단(`미확인`).
- **검증 명령:**
  - `fly config validate --strict`(알 수 없는 섹션·키도 검사, Fly 플랫폼 기준 검증)
  - 파트 1 docker 검증. 컨테이너 신호는 `kill_signal`과 같게 맞춘다.
  - 배포 후 `fly status`(명령 원문 `미확인`)와 `curl`
- **출처 (확인 2026-10-01):**
  - https://docs.fly.io/reference/configuration/ · "You can set it up to a maximum of 300 seconds (5 minutes)." / release_command "run a one-off task, like a database migration, before any of your deployed Machines are created or updated" ⚠️출처확인필요
  - https://docs.fly.io/flyctl/config-validate/ ⚠️출처확인필요
  - https://docs.fly.io/launch/continuous-deployment-with-github-actions/ ⚠️출처확인필요
  - https://docs.fly.io/networking/custom-domain/ ⚠️출처확인필요
  - https://github.com/fly-apps/terraform-provider-fly · "not a recommended method of deployment to Fly.io." ⚠️출처확인필요

## P11. Firebase App Hosting
- **산출물 목록:**
  - `apphosting.yaml`
    - `runConfig`: `cpu`, `memoryMiB`, `minInstances`, `maxInstances`, `concurrency`, `vpcAccess`
    - `env[]`: `variable`, `value`, `secret`, `availability: [BUILD, RUNTIME]`
    - `scripts.buildCommand`, `scripts.runCommand`
  - 환경별 `apphosting.<env>.yaml`.
  - `firebase.json`의 `apphosting` 항목: `backendId`, `rootDir`, `ignore`.
  - Terraform `google_firebase_app_hosting_backend`. 필수 인자는 `backend_id`, `location`, `serving_locality`, `service_account`, `app_id`이고, Git 연결용 `codebase.repository`는 선택이다.
  - Dockerfile은 없다(빌드는 플랫폼이 한다).
  - CI 단계: `firebase deploy --only apphosting:<backendId>`(firebase-tools 14.4.0 이상, 소스 배포). 인증은 ADC(`google-github-actions/auth@v3`)를 쓰고, `login:ci` 토큰 방식은 더 이상 권장되지 않는다.
- **요구 수준에 따라 바뀌는 핵심 설정:**
  - A5: `runConfig.minInstances`(기본 0).
  - D2: `maxInstances`(기본 100), `concurrency`(기본 80).
  - A6: `cpu`, `memoryMiB`(기본 512).
  - C8과 F5: `vpcAccess.egress` + `connector` 또는 `networkInterfaces`(사설 DB 연결).
  - D5: 리전은 us-central1, us-east4, us-east5, asia-east1, asia-southeast1, europe-west4뿐이고 **서울은 없다.** 서울 DB와 함께 쓰려면 Cloud Run(P18)이 낫다(추론). ⚠️근거없음
  - 하부가 Cloud Run이라 종료 유예는 10초라고 보는 것은 (추론)이다. App Hosting 문서에 값은 `미확인`. ⚠️근거없음
- **함께 필요한 주변 자원:** Blaze 요금제, Secret Manager(`env[].secret`, 버전 고정 `secret@5`), 서비스 계정, VPC 커넥터 또는 Direct VPC, 커스텀 도메인(리소스 이름 `미확인`).
  - **자동화 불가 단계:** Git 배포를 쓰면 Developer Connect UI에서 Firebase GitHub 앱을 설치해야 한다. CLI 소스 배포를 쓰면 이 단계를 건너뛸 수 있다.
- **검증 명령:**
  - `terraform validate`
  - `apphosting.yaml`을 검증하는 전용 명령은 `미확인`.
  - 로컬 빌드는 프레임워크 빌드 명령(`npm run build`)으로 대신한다.
  - 배포 후 스모크.
  - Checkov 규칙은 `미확인`.
- **출처 (확인 2026-10-01):** https://firebase.google.com/docs/app-hosting/configure · https://firebase.google.com/docs/app-hosting/alt-deploy · https://firebase.google.com/docs/app-hosting/about-app-hosting · https://firebase.google.com/docs/cli · https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/firebase_app_hosting_backend

## P12. Cloud Functions for Firebase
- **산출물 목록:**
  - `firebase.json`의 `functions`: `source`, `codebase`, `ignore`, `predeploy`, `runtime`.
  - 함수 코드 옵션: `setGlobalOptions({...})`와 함수별 옵션 `{ region, timeoutSeconds, memory, maxInstances, minInstances, secrets }`. `setGlobalOptions`에 이 키를 모두 넣는 예시는 `미확인`.
  - 환경 파일 `.env`, `.env.<projectId>`.
  - CI 단계: `firebase deploy --only functions`(ADC 인증).
  - Terraform: 2세대 함수는 `google_cloudfunctions2_function`(P21)으로도 관리할 수 있지만, Firebase SDK 트리거 코드와 둘 중 하나만 쓴다(추론). ⚠️근거없음
- **요구 수준에 따라 바뀌는 핵심 설정:**
  - D5: `region: "asia-northeast3"`(서울, 1세대·2세대 모두 지원). 기본은 `us-central1`이다.
  - A2: `timeoutSeconds`. HTTP·callable은 최대 3600초, 예약·태스크 큐는 1800초, 그 밖의 이벤트 함수는 540초다. Hosting을 경유하면 60초다(04 문서).
  - A5: `minInstances`.
  - D2: `maxInstances`.
  - A6: `memory`.
  - C8: 2세대 함수의 동시성은 옵션 `concurrency`(원문 `미확인`).
- **함께 필요한 주변 자원:**
  - 비밀: `firebase functions:secrets:set NAME` + `defineSecret`.
  - `functions.config()`는 2027년 3월 이후 동작하지 않는다. 쓰고 있으면 **부분 수정**(params·secrets로 이전).
  - Blaze 요금제, 서비스 계정.
- **검증 명령:**
  - 함수 코드 타입 검사(`tsc --noEmit`)
  - `firebase emulators:start --only functions`(명령 원문 `미확인`)
  - 배포 후 스모크
- **출처 (확인 2026-10-01):** https://firebase.google.com/docs/functions/manage-functions · https://firebase.google.com/docs/functions/locations · https://firebase.google.com/docs/functions/organize-functions · https://firebase.google.com/docs/functions/config-env

## P13. Supabase Edge Functions
- **산출물 목록:**
  - `supabase/config.toml`의 `[functions.<name>]`: `verify_jwt`, `import_map`, `entrypoint`, `static_files`, `enabled`.
  - 함수 코드 `supabase/functions/<name>/index.ts`.
  - Terraform `supabase/supabase`(v1.11.0, 커뮤니티 등급)
    - 리소스: `supabase_project`, `supabase_settings`, **`supabase_edge_function`**(`entrypoint`, `project_ref`, `slug`), **`supabase_edge_function_secrets`**
    - `supabase_edge_function_secrets`는 비밀 값을 state에 평문으로 저장한다. 비밀은 CLI로 넣는다(추론). ⚠️근거없음
  - CI 단계: `supabase/setup-cli@v1` → `supabase functions deploy --project-ref $PROJECT_ID`(`SUPABASE_ACCESS_TOKEN`). DB 마이그레이션은 `supabase db push`(명령 원문 `미확인`)로 별도 단계에서 한다.
- **요구 수준에 따라 바뀌는 핵심 설정:**
  - F5: `verify_jwt`. 웹훅 수신 함수(E4)만 `false`로 두고 서명 검증 코드를 생성한다. false면 "anyone to invoke your Edge Function without a valid JWT"가 된다.
  - A2: 벽시계 150초(Free) / 400초(Pro), CPU 2초. 설정 키는 없고 넘으면 플랫폼을 바꾼다(04 문서).
  - D5: 프로젝트를 만들 때 리전을 `ap-northeast-2`로 정한다(`supabase_project.region`, 키 원문 `미확인`).
- **함께 필요한 주변 자원:**
  - 비밀: `supabase secrets set --env-file .env`. 재배포 없이 즉시 반영되고, `SUPABASE_` 접두사는 예약되어 있다.
  - 기본 주입: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_DB_URL`.
  - **자동화 불가 단계:** 액세스 토큰 발급. Free 프로젝트는 1주 동안 활동이 없으면 정지된다(04 문서).
- **검증 명령:**
  - `deno check supabase/functions/<name>/index.ts`(도구 사용은 추론) ⚠️근거없음
  - `supabase functions serve`(로컬, 원문 `미확인`)
  - `terraform validate`
  - 배포 후 `curl -H "Authorization: Bearer $ANON_KEY" https://<ref>.supabase.co/functions/v1/<name>`(URL 형식 `미확인`)
- **출처 (확인 2026-10-01):** https://supabase.com/docs/guides/functions/function-configuration · https://supabase.com/docs/guides/functions/deploy · https://supabase.com/docs/guides/functions/secrets · https://github.com/supabase/terraform-provider-supabase/tree/v1.11.0/docs/resources

## P14. Replit Deployments
- **산출물 목록:**
  - `.replit`의 `[deployment]`: `run`, `build`, `ignorePorts`, `deploymentTarget`. 값은 문서 예시 `'cloudrun'`만 확인했고 autoscale/vm/scheduled 값은 `미확인`.
  - `[[ports]] localPort/externalPort`.
  - 정적 배포는 `[[deployment.rewrites]]`, `[[deployment.responseHeaders]]`.
  - **Terraform, 배포 CLI, API, GitHub Action 모두 확인되지 않았다.** 게시는 UI의 "Publish" 버튼으로 한다.
- **요구 수준에 따라 바뀌는 핵심 설정:** 배포 유형(Autoscale / Reserved VM / Scheduled)은 UI에서 고른다. A1: 상시 워커면 Reserved VM. B3: Scheduled(공개 URL 없음).
- **함께 필요한 주변 자원:** Replit Secrets(UI), 결제 수단.
  - **자동화 불가 단계:** 게시와 설정 전부. 에이전트는 Replit을 **최종 목적지로 선택하지 않는다.** 기존 앱이면 `.replit`의 `run`과 `build`만 운영 서버로 고치고(1.2 기준) 게시 절차를 안내한다(추론). ⚠️근거없음
- **검증 명령:** `run` 명령을 로컬에서 실행하고 헬스체크를 확인한다(파트 1과 같은 방식). 플랫폼 검증 명령은 없다.
- **출처 (확인 2026-10-01):** https://docs.replit.com/replit-workspace/configuring-repl · https://docs.replit.com/features/publishing/deployment-types · https://docs.replit.com/cloud-services/deployments/scheduled-deployments · https://docs.replit.com/learn/projects-and-artifacts/replit-deployments · https://docs.replit.com/references/deployment-customization/static-deployments-advanced ⚠️출처확인필요

## P15. Heroku
- **산출물 목록:**
  - `Procfile`(`web: …`, `worker: …`, `release: <migrate>`).
  - 컨테이너로 배포하면 `heroku.yml`(`setup`/`build`/`release`/`run`, `heroku stack:set container`, Cedar 세대만 해당) + Dockerfile.
  - `app.json`(addons, env, formation, scripts.postdeploy). 새 앱을 만들 때만 처리된다.
  - Fir 세대는 `project.toml`을 쓴다. Fir에서 heroku.yml을 지원하는지는 `미확인`.
  - Terraform `heroku/heroku`(파트너): `heroku_app`, `heroku_build`, `heroku_formation`, `heroku_addon`, `heroku_config`, `heroku_app_config_association`, `heroku_app_release`, `heroku_domain`, `heroku_pipeline`.
  - CI 단계: `HEROKU_API_KEY`로 `git push` 또는 `heroku_build`. 공식 GitHub Action은 `미확인`.
- **요구 수준에 따라 바뀌는 핵심 설정:**
  - F4: 종료는 30초로 고정된다. 넘으면 SIGKILL과 R12 오류가 난다.
  - F4: 무중단 배포는 `heroku features:enable preboot`(Standard·Performance dyno만).
  - C9: `release:` 프로세스(1시간 타임아웃, 실패하면 릴리스 중단).
  - D2: `heroku_formation` `quantity`, `size`.
  - A2: 첫 바이트 30초는 바꿀 수 없다(04 문서).
  - D5: 서울은 없다.
- **함께 필요한 주변 자원:** `heroku_addon`(Postgres, Redis), Config Vars(`heroku_config`의 `sensitive_vars`, 키 원문 `미확인`), `heroku_domain` + DNS, Private Spaces(사설 연결, 별도 계약).
  - **자동화 불가 단계:** 신용카드로 계정을 인증해야 한다. 인증 전에는 앱 생성·배포·커스텀 도메인이 불가하다.
- **검증 명령:**
  - `heroku local`(Procfile 실행, 원문 `미확인`)
  - 파트 1 docker 검증(container stack)
  - `terraform validate`
  - 배포 후 스모크
- **출처 (확인 2026-10-01):** https://devcenter.heroku.com/articles/procfile · https://devcenter.heroku.com/articles/release-phase · https://devcenter.heroku.com/articles/build-docker-images-heroku-yml · https://devcenter.heroku.com/articles/app-json-schema · https://devcenter.heroku.com/articles/dyno-shutdown-behavior · https://devcenter.heroku.com/articles/preboot · https://devcenter.heroku.com/articles/authentication · https://devcenter.heroku.com/articles/account-verification · https://registry.terraform.io/providers/heroku/heroku/latest

## P16. DigitalOcean App Platform
- **산출물 목록:**
  - `.do/app.yaml`(App spec)
    - `services[]`: `dockerfile_path`, `http_port`, `instance_count`, `instance_size_slug`, `health_check`, `liveness_health_check`, `autoscaling`, `termination`
    - `workers[]`, `jobs[]`(`kind: PRE_DEPLOY`|`POST_DEPLOY`|`FAILED_DEPLOY`|`SCHEDULED`)
    - `envs[]`(`type: SECRET`), `region: sgp`
  - Dockerfile(파트 1).
  - Terraform `digitalocean/digitalocean`(v2.103.0) `digitalocean_app`. spec을 HCL로 옮긴 형태다.
  - CI 단계: `digitalocean/app_action/deploy@v2`(`token`, `app_spec_location: .do/app.yaml`).
- **요구 수준에 따라 바뀌는 핵심 설정:**
  - F4: `termination.grace_period_seconds`(기본 120, 최대 600), `termination.drain_seconds`(기본 15, 최대 110).
  - F4: `health_check.http_path`. 비우면 TCP로 검사한다. `initial_delay_seconds`, `failure_threshold`.
  - C9: `jobs[].kind: PRE_DEPLOY`.
  - D2와 D3: `autoscaling.min_instance_count`, `max_instance_count`, `metrics.cpu.percent`, 또는 `instance_count`(1~250).
  - A6: `instance_size_slug`(기본 `basic-xxs`).
  - A2: 기본 30초, 최대 100초(04 문서). 키는 `미확인`.
  - D5: `region: sgp`(서울 없음).
- **함께 필요한 주변 자원:**
  - 관리형 DB: `databases[]` 또는 `digitalocean_database_cluster`(리소스 이름 `미확인`).
  - VPC 연결: 고정 IP와 동시에 쓸 수 없다(04 문서).
  - 도메인: `domains[]`(키 원문 `미확인`).
  - **자동화 불가 단계:** GitHub 앱 승인(`미확인`), API 토큰 발급.
- **검증 명령:**
  - `doctl apps spec validate .do/app.yaml`
  - `terraform validate`
  - 파트 1 docker 검증
  - 배포 후 스모크
  - Checkov 규칙은 `미확인`.
- **출처 (확인 2026-10-01):** https://docs.digitalocean.com/products/app-platform/reference/app-spec/ · https://docs.digitalocean.com/reference/doctl/reference/apps/spec/validate/ · https://github.com/digitalocean/app_action · https://registry.terraform.io/providers/digitalocean/digitalocean/latest

## P17. Koyeb
- **산출물 목록:**
  - **설정 파일이 확인되지 않았다**(koyeb.yaml은 `미확인`).
  - Terraform `koyeb/koyeb`(파트너, v0.2.0)
    - 리소스: `koyeb_app`, `koyeb_service`, `koyeb_secret`, `koyeb_domain`, `koyeb_volume`
    - `koyeb_service.definition`의 블록: `instance_types`, `scalings`, `ports`, `routes`, `env`, `regions`, `git`
    - `health_checks`와 `docker` 블록은 `미확인`(문서 API 400 응답).
  - CLI: `koyeb deploy <path> <app>/<service> --instance-type --regions --min-scale --max-scale --ports --routes --checks <PORT>:http:<PATH> --checks-grace-period --archive-builder docker`.
  - CI: `koyeb-community/koyeb-actions@v2` + `koyeb/action-git-deploy`(`KOYEB_API_TOKEN`).
  - Dockerfile(파트 1).
- **요구 수준에 따라 바뀌는 핵심 설정:**
  - F4: 헬스체크 `--checks`. grace 기본 5초(5~900), 간격 60초, 재시작 한도 3, 타임아웃 5초.
  - F4: SIGTERM 후 30초. 바꿀 수 있는지 `미확인`.
  - D2와 A5: `scalings { min max }`(유료는 min 0 가능, 04 문서).
  - D5: `regions`(도쿄 `tyo`, 값 형식 `미확인`).
  - C9: 마이그레이션 훅이 `미확인`이므로 CI 단계에서 실행한다.
- **함께 필요한 주변 자원:** `koyeb_secret`, `koyeb_domain` + DNS, 외부 DB.
  - **자동화 불가 단계:** API 토큰 발급.
- **검증 명령:** `terraform validate`, 파트 1 docker 검증, 배포 후 스모크.
- **출처 (확인 2026-10-01):** https://www.koyeb.com/docs/build-and-deploy/cli/reference · https://www.koyeb.com/docs/integrations/infrastructure-as-code/terraform · https://www.koyeb.com/docs/run-and-scale/health-checks · https://www.koyeb.com/docs/reference/instances · https://github.com/koyeb/action-git-deploy · https://registry.terraform.io/providers/koyeb/koyeb/latest ⚠️출처부적격

## 티어 1

## P18. Cloud Run 서비스 (요청 기반 · 인스턴스 기반)
과금 모드가 달라도 산출물은 같다. 키 하나(`cpu_idle`)만 다르다.

- **산출물 목록:**
  - Dockerfile(파트 1).
  - Terraform `hashicorp/google`
    - `google_project_service`(run, artifactregistry, secretmanager, iam 등)
    - `google_artifact_registry_repository`(`docker_config.immutable_tags = true`, `cleanup_policies`)
    - `google_service_account`(런타임용, 배포용 각각)
    - `google_cloud_run_v2_service`
    - `google_cloud_run_v2_service_iam_member`(`roles/run.invoker`, 공개 서비스면 `allUsers`)
    - `google_secret_manager_secret` + `_version`
    - WIF 풀과 프로바이더(1.4.3)
  - 선택: Knative 형식 `service.yaml` + `gcloud run services replace`(Terraform 대신).
  - CI 단계: 빌드 → AR 푸시 → 마이그레이션 Job(P19) → `deploy-cloudrun@v3`(`no_traffic`, `tag`) → 태그 URL 스모크 → `update-traffic --to-latest`.
  - Terraform과 CI가 같은 서비스의 이미지를 함께 바꾸면 드리프트가 생긴다. Terraform 쪽에 `lifecycle { ignore_changes = [template[0].containers[0].image, client, client_version] }`를 둔다(추론). ⚠️근거없음
- **요구 수준에 따라 바뀌는 핵심 설정 (`google_cloud_run_v2_service`):**
  - A4: `template.containers.resources.cpu_idle`
    - `true`는 요청 기반 과금, `false`는 인스턴스 기반 과금이다.
    - **함정:** `resources` 블록을 쓰면(cpu·memory 지정) 기본값이 사라진다. 요청 기반을 원하면 `cpu_idle = true`도 명시해야 한다.
    - gcloud에서는 `--cpu-throttling` / `--no-cpu-throttling`.
  - A5: `template.scaling.min_instance_count`(기본 0), `startup_cpu_boost = true`. 서비스 수준 `scaling.min_instance_count`는 트래픽을 받는 모든 리비전에 나눠진다.
  - D2와 C8: `template.scaling.max_instance_count`(= DB 연결 상한 ÷ 인스턴스당 풀). `template.max_instance_request_concurrency`(기본 80×vCPU, CPU 집약이면 낮춘다).
  - A2: `template.timeout`(기본 300s, 최대 3600s). 형식은 `"900s"`.
  - A6: `resources.limits = { cpu = "1", memory = "512Mi" }`.
  - F4: `startup_probe`. startup probe를 주면 다른 probe는 그것이 성공할 때까지 꺼진다. 명시하지 않으면 TCP startup probe가 자동으로 붙는다. `liveness_probe`는 `/healthz`. 종료 유예 10초는 조정할 수 없다.
  - F5와 C8: `template.vpc_access`
    - Direct VPC egress가 권장이다: `network_interfaces { network, subnetwork }`.
    - 대안은 `connector`이고, `egress = "PRIVATE_RANGES_ONLY"|"ALL_TRAFFIC"`.
    - 고정 출구 IP(E1)가 필요하면 `ALL_TRAFFIC` + Cloud NAT `MANUAL_ONLY`.
  - C8: Cloud SQL 소켓은 `template.volumes { cloud_sql_instance { instances = [...] } }`이고 `/cloudsql/<connection>`으로 마운트된다.
  - F5: `ingress = "INGRESS_TRAFFIC_ALL"|"INGRESS_TRAFFIC_INTERNAL_ONLY"|"INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"`. LB 뒤에 두면 `default_uri_disabled = true`. `invoker_iam_disabled`(공개 서비스).
  - 운영 안전: `deletion_protection`(기본 true). 생성 시 유지하고 삭제 절차를 따로 안내한다.
  - 비밀: `env { value_source { secret_key_ref { secret, version } } }`. 버전을 고정하는 것이 권장이고, env는 인스턴스가 시작될 때 해석된다.
- **함께 필요한 주변 자원:**
  - 레지스트리: Artifact Registry(`asia-northeast3`).
  - 네트워크: VPC + 서브넷(Direct VPC는 /26 이상, 05 문서), 또는 `google_vpc_access_connector`(`ip_cidr_range` /28, `min_instances` 2~9, `max_instances` 3~10).
  - 고정 IP: `google_compute_router_nat`(`nat_ip_allocate_option = "MANUAL_ONLY"`, `nat_ips`) + `google_compute_address`.
  - 사설 DB: Cloud SQL Private IP + Direct VPC, 또는 Cloud SQL 커넥터 소켓. 런타임 SA에 Cloud SQL Client 역할.
  - 도메인과 인증서
    - **서울(asia-northeast3)은 Cloud Run 도메인 매핑 지원 리전이 아니다.** 매핑 자체도 Preview이고 운영용이 아니다.
    - 서울에서는 전역 외부 Application LB + 서버리스 NEG + Google 관리 인증서를 생성한다(`google_compute_region_network_endpoint_group`, `google_compute_backend_service`, `google_compute_url_map`, `google_compute_target_https_proxy`, `google_compute_managed_ssl_certificate`, `google_compute_global_forwarding_rule`). 리소스 이름의 원문 확인은 `미확인`.
    - LB 고정비는 월 약 $18이다(05 문서).
  - 비밀: Secret Manager + 런타임 SA에 Secret Accessor.
  - IAM: 런타임 SA(최소 권한), 배포 SA(`roles/run.developer`, `roles/iam.serviceAccountUser`, AR writer — 역할 이름은 `미확인`), WIF.
- **검증 명령:**
  - `terraform validate` / `plan`
  - Checkov
    - **`google_cloud_run_v2_*`를 대상으로 하는 체크가 없다.** CKV_GCP_102는 v1 `google_cloud_run_service_iam_*`만 본다.
    - 공개 접근 검사는 커스텀 정책으로 한다: `allUsers` + `roles/run.invoker`가 의도된 경우만 허용(추론). ⚠️근거없음
    - 사용할 수 있는 ID: CKV_GCP_84·CKV_GCP_101(AR), CKV_GCP_118·CKV_GCP_125(WIF).
  - 파트 1 docker 검증. PORT는 8080, SIGTERM 후 10초 안에 종료되어야 한다.
  - `gcloud run services describe app --region asia-northeast3 --format='value(status.conditions)'`
  - 태그 URL 스모크
- **출처 (확인 2026-10-01):**
  - https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_run_v2_service · `cpu_idle` "if `resources` is set, this field must be explicitly set to true to preserve the default behavior."
  - https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_run_v2_service_iam
  - https://docs.cloud.google.com/run/docs/configuring/billing-settings
  - https://docs.cloud.google.com/run/docs/configuring/healthchecks
  - https://docs.cloud.google.com/run/docs/container-contract
  - https://docs.cloud.google.com/run/docs/mapping-custom-domains · "Cloud Run domain mappings are in the preview launch stage … not production-ready"
  - https://docs.cloud.google.com/run/docs/configuring/services/secrets
  - https://docs.cloud.google.com/sql/docs/postgres/connect-run
  - https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/vpc_access_connector · https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_router_nat · https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/artifact_registry_repository
  - https://www.checkov.io/5.Policy%20Index/terraform.html ⚠️출처확인필요

## P19. Cloud Run Jobs
- **산출물 목록:** Terraform `google_cloud_run_v2_job`. 마이그레이션 Job과 정기 작업 Job을 만든다. 정기 실행에는 `google_cloud_scheduler_job`을 더한다. 이미지는 서비스와 같은 것을 쓴다.
- **요구 수준에 따라 바뀌는 핵심 설정:**
  - C9(마이그레이션)
    - `template.task_count = 1`, `parallelism = 1`.
    - `template.template.max_retries`: 기본 3이다. 마이그레이션이 멱등이 아니면 0으로 둔다(추론). ⚠️근거없음
    - `template.template.timeout`: 시도당 적용된다.
  - B3(정기 작업): Cloud Scheduler `http_target` POST `https://run.googleapis.com/v2/projects/P/locations/R/jobs/J:run` + `oauth_token`(GCP 엔드포인트). `time_zone = "Asia/Seoul"`.
  - C8: `template.template.volumes.cloud_sql_instance`, `vpc_access`(서비스와 같다).
  - A2: 태스크는 최대 168시간(05 문서).
- **함께 필요한 주변 자원:** P18과 같다. 실행 SA, Scheduler 호출 SA(`roles/run.invoker`).
- **검증 명령:** `terraform validate`. CI에서 `gcloud run jobs execute migrate --region asia-northeast3 --wait`를 돌리고 종료 코드가 0인지 본다. 실패하면 배포를 중단한다.
- **출처 (확인 2026-10-01):** https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_run_v2_job · https://docs.cloud.google.com/run/docs/execute/jobs · https://docs.cloud.google.com/run/docs/execute/jobs-on-schedule · https://docs.cloud.google.com/python/django/run (마이그레이션을 Job으로 실행하는 예) · https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_scheduler_job

## P20. Cloud Run 워커 풀
- **산출물 목록:** Terraform `google_cloud_run_v2_worker_pool`(GA provider). 대안은 `gcloud run worker-pools deploy` 또는 `worker-pools replace worker-pool.yaml`. Dockerfile은 큐 소비자 엔트리포인트용이다(같은 이미지에 다른 `command`).
- **요구 수준에 따라 바뀌는 핵심 설정:**
  - A1(상시 워커): `scaling.scaling_mode = "MANUAL"`(기본), `scaling.manual_instance_count`.
  - 큐 길이 기반 확장(QU.consumer_scaling): `scaling_mode = "AUTOMATIC"`. 지표 조건은 `미확인`.
  - F4: 10초 안에 메시지를 반환하고 종료한다.
  - URL이 없으므로 HTTP probe 대상이 없다. 헬스는 프로세스 생존으로 판단한다(추론). ⚠️근거없음
- **함께 필요한 주변 자원:** P18과 같다(VPC, 비밀, SA). 큐(Pub/Sub, Redis)는 03 문서를 따른다.
- **검증 명령:** `terraform validate`. 파트 1 docker 검증은 HTTP 헬스 대신 SIGTERM 종료만 확인한다. 배포 후 큐에 시험 메시지를 넣어 처리되는지 확인한다(추론). ⚠️근거없음
- **출처 (확인 2026-10-01):** https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_run_v2_worker_pool · https://docs.cloud.google.com/run/docs/deploy-worker-pools

## P21. Cloud Run functions
- **산출물 목록:**
  - Dockerfile은 없다. Functions Framework 엔트리포인트(코드)를 쓰고, 소스를 GCS에 올리거나 저장소에서 빌드한다.
  - Terraform `google_cloudfunctions2_function`
    - `build_config`: `runtime`, `entry_point`, `source.storage_source`
    - `service_config`: `max_instance_count`, `min_instance_count`, `timeout_seconds`, `available_memory`, `max_instance_request_concurrency`, `vpc_connector`, `vpc_connector_egress_settings`, `service_account_email`, `secret_environment_variables`
- **요구 수준에 따라 바뀌는 핵심 설정:**
  - A2: `timeout_seconds`(기본 60, HTTP 최대 3600).
  - C8과 D2: `max_instance_request_concurrency`(기본 1). Cloud Run 서비스(80×vCPU)와 다르다. DB 연결 계산에 반영한다.
  - A6: `available_memory`(기본 256M).
  - A5: `min_instance_count`.
  - F5: `ingress_settings`(CKV_GCP_124가 검사).
- **함께 필요한 주변 자원:** 소스 버킷, Cloud Build(빌드 비용), VPC 커넥터, SA, Secret Manager.
- **검증 명령:**
  - `terraform validate`
  - Checkov: CKV_GCP_107(함수 IAM 공개 금지), CKV_GCP_124(과도한 ingress), CKV2_GCP_10(1세대 HTTP 트리거 보안).
  - 로컬에서 Functions Framework로 실행한 뒤 `curl`(명령 원문 `미확인`).
  - 배포 후 스모크.
- **출처 (확인 2026-10-01):** https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloudfunctions2_function · https://docs.cloud.google.com/functions/docs/functions-framework · https://www.checkov.io/5.Policy%20Index/terraform.html ⚠️출처확인필요

## P22. ECS on Fargate (일반 서비스 + Fargate Spot)
- **산출물 목록:**
  - Dockerfile(파트 1). `HEALTHCHECK` 대신 태스크 정의 `healthCheck`를 써도 된다.
  - Terraform `hashicorp/aws`(v6.67.0)
    - 클러스터와 실행
      - `aws_ecs_cluster`(`setting { name = "containerInsights" value = "enhanced" }`)
      - `aws_ecs_task_definition`(`requires_compatibilities = ["FARGATE"]`, `network_mode = "awsvpc"`, `cpu`, `memory`, `execution_role_arn`, `task_role_arn`, `runtime_platform`, `container_definitions = jsonencode([...])`)
      - `aws_ecs_service`
      - `aws_appautoscaling_target` + `aws_appautoscaling_policy`
      - `aws_cloudwatch_log_group`(`retention_in_days`, 키 원문 `미확인`)
    - LB와 인증서: `aws_lb`, `aws_lb_target_group`, `aws_lb_listener`(HTTPS + HTTP 301), `aws_acm_certificate` + `aws_acm_certificate_validation` + `aws_route53_record`
    - 레지스트리: `aws_ecr_repository` + `aws_ecr_lifecycle_policy`
    - 비밀: `aws_secretsmanager_secret` 또는 `aws_ssm_parameter`(`SecureString`)
    - IAM: OIDC provider + 배포 역할
    - 모듈: `terraform-aws-modules/vpc`, `terraform-aws-modules/ecs`를 쓸 수 있다.
  - CI 단계: `configure-aws-credentials@v6` → `amazon-ecr-login@v2` → `build-push-action@v7` → `amazon-ecs-render-task-definition@v1` → `amazon-ecs-deploy-task-definition@v2`(`run-task: true`로 마이그레이션을 먼저 실행, `wait-for-service-stability: true`).
  - Terraform과 CI가 태스크 정의를 함께 바꾸므로 드리프트가 생긴다. 서비스에 `lifecycle { ignore_changes = [task_definition, desired_count] }`를 둔다. `desired_count`는 공식 문서도 권장한다. `task_definition`은 (추론)이다. ⚠️근거없음
- **요구 수준에 따라 바뀌는 핵심 설정:**
  - F4(배포)
    - `deployment_circuit_breaker { enable = true, rollback = true }`.
    - `deployment_minimum_healthy_percent = 100`(기본), `deployment_maximum_percent = 200`(기본).
    - `health_check_grace_period_seconds`(기본 0): 기동이 무거우면(A5) 늘린다.
    - `wait_for_steady_state = true`.
  - F4(종료)
    - 컨테이너 정의 `stopTimeout`(기본 30, Fargate 최대 120).
    - `aws_lb_target_group.deregistration_delay`(기본 300 → 30~60으로 낮춘다. 롤아웃 속도 때문이다. simple-web-app은 30).
    - 두 값의 관계: 앱 드레인 시간 ≤ stopTimeout, deregistration_delay ≥ 진행 중 요청의 최대 시간(추론). ⚠️근거없음
  - F4(헬스)
    - 컨테이너 정의 `healthCheck { command = ["CMD-SHELL","curl -f http://localhost:8080/healthz || exit 1"], interval = 30, timeout = 5, retries = 3, startPeriod }`. 이미지에 curl이 없으면 런타임 명령으로 바꾼다.
    - `aws_lb_target_group.health_check { path = "/healthz", matcher = "200", interval, healthy_threshold }`.
  - A2와 A3: `aws_lb.idle_timeout`(기본 60, 1~4000). 웹소켓·SSE·긴 요청이면 늘린다.
  - D2와 D3: `aws_appautoscaling_policy`. 지표는 `ECSServiceAverageCPUUtilization` 또는 `ALBRequestCountPerTarget`(`resource_label` 필요).
  - F1: 서브넷 2~3 AZ. 새 서비스는 `availability_zone_rebalancing`이 기본 `DISABLED`이므로 `"ENABLED"`로 둔다.
  - F5: `network_configuration { assign_public_ip = false }`(기본 DISABLED, CKV_AWS_333). 컨테이너 `readonlyRootFilesystem = true`(CKV_AWS_336), `user`는 숫자 UID.
  - **충돌:** ECS Exec(`enable_execute_command = true`)는 `readonlyRootFilesystem`과 함께 쓸 수 없다. 운영 디버깅이 필요하면 CKV_AWS_336을 사유와 함께 건너뛴다.
  - G3(Spot)
    - `capacity_provider_strategy { capacity_provider = "FARGATE_SPOT", weight }`, 안정분은 `FARGATE` + `base`.
    - Spot은 2분 경고와 SIGTERM을 주고 온디맨드로 대체하지 않는다. 그래서 `stopTimeout` ≤ 120으로 두고, 웹 서비스는 FARGATE `base ≥ 1`을 섞는다(추론). ⚠️근거없음
- **함께 필요한 주변 자원:**
  - 네트워크: VPC, 공용 서브넷(ALB), 사설 서브넷(태스크).
    - 출구가 필요하면 NAT Gateway(AZ당 월 $43, 05 문서).
    - **NAT 없이 사설 서브넷에서 실행하려면 VPC 엔드포인트가 필수다**: `ecr.api`, `ecr.dkr`(Interface), `s3`(Gateway), `logs`(awslogs), `secretsmanager`(비밀). 엔드포인트 SG는 443 인바운드를 연다. Fargate는 ECS 인터페이스 엔드포인트가 필요 없다.
    - 외부 API 호출(E1)이 있으면 NAT가 필요하다.
  - 사설 DB: RDS를 사설 서브넷에 두고, SG에서 태스크 SG의 5432 인바운드만 허용한다.
  - 도메인: Route 53 + ACM DNS 검증.
  - IAM
    - 실행 역할: ECR pull, 로그, 비밀 읽기.
    - 태스크 역할: 앱 권한. 실행 역할과 분리한다(CKV_AWS_249).
    - GitHub OIDC 배포 역할.
- **검증 명령:**
  - `terraform validate` / `plan`
  - Checkov
    - ECR: CKV_AWS_51, CKV_AWS_163, CKV_AWS_136
    - ECS: CKV_AWS_65, CKV_AWS_249, CKV_AWS_336, CKV_AWS_332, CKV_AWS_333
    - LB: CKV_AWS_2, CKV_AWS_103, CKV_AWS_131, CKV_AWS_91, CKV_AWS_150
  - 파트 1 docker 검증. `docker stop -t 30`으로 stopTimeout을 흉내 낸다.
  - 배포 후
    - `aws ecs wait services-stable --cluster C --services S`(15초 간격으로 40번 확인, 실패하면 255)
    - `aws ecs describe-services --query 'services[0].deployments[0].rolloutState'`가 `COMPLETED`인지
    - ALB DNS로 스모크
- **출처 (확인 2026-10-01):**
  - https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_service · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_task_definition · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/appautoscaling_policy
  - https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_target_group · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_listener
  - https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecr_repository · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_endpoint
  - https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definition_parameters.html · "The maximum value is 120 seconds."
  - https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service_definition_parameters.html
  - https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-circuit-breaker.html
  - https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-capacity-providers.html · "Fargate doesn't replace Spot capacity with on-demand capacity."
  - https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-exec.html
  - https://docs.aws.amazon.com/AmazonECR/latest/userguide/vpc-endpoints.html · "require both Amazon ECR VPC endpoints and the Amazon S3 gateway endpoints."
  - https://docs.aws.amazon.com/AmazonECS/latest/developerguide/vpc-endpoints.html
  - https://docs.aws.amazon.com/cli/latest/reference/ecs/wait/services-stable.html
  - https://github.com/aws-actions/amazon-ecs-deploy-task-definition
  - https://www.checkov.io/5.Policy%20Index/terraform.html ⚠️출처확인필요

## P23. ECS Express Mode
- **산출물 목록:**
  - Dockerfile.
  - Terraform `aws_ecs_express_gateway_service`(provider 6.23.0에서 추가)
    - 필수: `execution_role_arn`, `infrastructure_role_arn`, `primary_container { image }`
    - 선택: `container_port`(기본 80), `health_check_path`(기본 `/`), `cpu`(1024), `memory`(2048), `scaling_target`, `network_configuration`, `wait_for_steady_state`(기본 false)
    - 시크릿은 `value_from`
  - ECR, 역할 2개.
  - CI: `aws-actions/amazon-ecs-deploy-express-service@v1`, 또는 CLI `aws ecs create-express-gateway-service`.
  - ALB·인증서·오토스케일·로그 그룹은 Express가 만든다.
- **요구 수준에 따라 바뀌는 핵심 설정:**
  - F4
    - `health_check_path = "/healthz"`. 기본 `/`는 앱 루트가 무거우면 문제가 된다.
    - `container_port = 8080`. 기본 80이라 파트 1의 PORT 규칙과 맞춘다.
    - `wait_for_steady_state = true`.
  - D2: `scaling_target { minTaskCount, maxTaskCount }`(기본 1~20, CPU 60%).
  - F5와 C8: `network_configuration.subnets`. 기본은 공용 서브넷 + 공인 IP다. 사설 DB면 사설 서브넷 + NAT를 직접 둔다(05 문서).
  - 배포 전략은 카나리로 고정이라 바꿀 수 없다(05 문서).
- **함께 필요한 주변 자원:** ECR, 실행 역할, 인프라 역할, VPC(기본 VPC 사용 가능), 사설 서브넷이면 NAT, 커스텀 도메인(Route 53 연결 방식은 `미확인`). 로그 그룹은 만료가 없으므로 보존 기간을 따로 설정한다(05 문서 함정).
- **검증 명령:** `terraform validate`, 파트 1 docker 검증(포트 8080 또는 80 일치 확인), 배포 후 `*.ecs.<region>.on.aws` URL 스모크, `aws ecs wait services-stable`. Checkov는 ECR 체크만 해당한다. Express 리소스 대상 체크는 `미확인`.
- **출처 (확인 2026-10-01):** https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_express_gateway_service · https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-overview.html · https://docs.aws.amazon.com/apprunner/latest/dg/apprunner-availability-change.html (CLI 예시)

## P24. AWS App Runner
- **산출물 목록:** **새로 생성하지 않는다.** 신규 고객을 받지 않고 새 기능도 계획되어 있지 않다. 기존 `aws_apprunner_service`가 있으면 판정은 **교체**(P23 Express Mode, AWS 공식 권장 이전 대상)다. 유지할 때만 `health_check_configuration { protocol = "HTTP", path = "/healthz" }`(기본 TCP)를 부분 수정한다.
- **요구 수준에 따라 바뀌는 핵심 설정:** A2: 120초(05 문서). A3: 웹소켓을 지원하지 않는다. 둘 다 교체 신호다.
- **함께 필요한 주변 자원:** 해당 없음(교체).
- **검증 명령:** 교체 후 P23과 같다.
- **출처 (확인 2026-10-01):** https://docs.aws.amazon.com/apprunner/latest/dg/apprunner-availability-change.html · "AWS App Runner is no longer open to new customers." / "We recommend that customers explore Amazon Elastic Container Service (Amazon ECS) Express Mode" · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/apprunner_service

## P25. Lambda — Function URL
- **산출물 목록:**
  - 컨테이너 이미지 방식(웹 앱을 그대로 옮길 때 권장, 추론) ⚠️근거없음
    - Dockerfile + **AWS Lambda Web Adapter**: `COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:1.1.0 /lambda-adapter /opt/extensions/lambda-adapter`.
    - 앱은 일반 웹 서버로 둔다(`AWS_LWA_PORT`, 없으면 `PORT`. 기본 8080).
  - 이미지 요건
    - 읽기 전용 파일 시스템이고, 쓰기는 `/tmp`만 된다.
    - Linux만 된다.
    - 압축 해제 기준 10GB 이하다.
    - 멀티 아키텍처 이미지는 안 된다(단일 플랫폼으로 빌드: `--platform linux/arm64`).
    - AWS 베이스 이미지가 아니면 런타임 인터페이스 클라이언트가 필요하다. Web Adapter를 쓰면 대신한다(추론). ⚠️근거없음
  - Terraform: `aws_lambda_function`(`package_type = "Image"`, `image_uri`, `timeout`, `memory_size`, `vpc_config`, `reserved_concurrent_executions`), `aws_lambda_function_url`(`authorization_type`, `invoke_mode`), ECR, IAM 실행 역할.
  - 대안 IaC: SAM `template.yaml`.
- **요구 수준에 따라 바뀌는 핵심 설정:**
  - A2: `timeout`(기본 3초, 최대 900). **기본 3초는 웹 앱에 거의 항상 부족하다.** 반드시 설정한다.
  - A6: `memory_size`(기본 128). 1,769MB가 vCPU 1개다(05 문서).
  - A7과 A3: `invoke_mode = "RESPONSE_STREAM"`(스트리밍 응답 200MB), Web Adapter `AWS_LWA_INVOKE_MODE = response_stream`. 동기 응답은 6MB까지다.
  - D2와 C8: `reserved_concurrent_executions`. 인스턴스당 동시성이 1이므로 DB 연결 = 동시 실행 수다. RDS Proxy를 더한다(추론). ⚠️근거없음
  - F5: `authorization_type = "AWS_IAM"`(기본 공개 `NONE`이면 CKV_AWS_258이 실패). 공개 웹 앱은 `NONE` + 앱 인증으로 하고 사유와 함께 건너뛴다.
  - F4: 확장이 없으면 종료 시간이 0ms다. Web Adapter는 graceful shutdown을 지원한다. 응답 후 작업(A4)은 불가하다(동결).
  - F5와 C8: `vpc_config { subnet_ids, security_group_ids }`. VPC 안에서 외부로 나가려면 NAT가 필요하다(추론). ⚠️근거없음
- **함께 필요한 주변 자원:** ECR, 실행 역할(`AWSLambdaBasicExecutionRole` 계열, 이름 원문 `미확인`), 사설 DB면 VPC + SG + RDS Proxy, 비밀(Secrets Manager + 확장 또는 SDK), 커스텀 도메인은 CloudFront 앞단(`미확인`).
- **검증 명령:**
  - `terraform validate`
  - `sam validate --lint`(SAM 경로)
  - Checkov: CKV_AWS_45, CKV_AWS_50, CKV_AWS_115, CKV_AWS_116, CKV_AWS_117, CKV_AWS_173, CKV_AWS_272, CKV_AWS_258
  - 로컬: 파트 1 docker 검증. Web Adapter가 있어도 일반 컨테이너로 돈다. 확장은 Lambda 밖에서 동작하지 않는다(추론). ⚠️근거없음
  - 배포 후: `curl` 함수 URL, 또는 `aws lambda invoke --function-name F --cli-binary-format raw-in-base64-out --payload '{}' out.json`.
- **출처 (확인 2026-10-01):**
  - https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function · `timeout` "Defaults to 3. Valid between 1 and 900."
  - https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function_url
  - https://docs.aws.amazon.com/lambda/latest/dg/images-create.html · "maximum uncompressed image size of 10 GB"
  - https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html · "0 ms – A function with no registered extensions"
  - https://github.com/awslabs/aws-lambda-web-adapter
  - https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-validate.html
  - https://docs.aws.amazon.com/cli/latest/reference/lambda/invoke.html

## P26. Lambda — API Gateway
- **산출물 목록:** P25의 함수 + `aws_apigatewayv2_api`(`protocol_type = "HTTP"|"WEBSOCKET"`), `aws_apigatewayv2_integration`(`integration_type = "AWS_PROXY"`, `payload_format_version = "2.0"`, 기본 1.0), `aws_apigatewayv2_route`, `aws_apigatewayv2_stage`(`auto_deploy = true`, HTTP API만), `aws_lambda_permission`. REST API(v1) 리소스의 세부 인자는 `미확인`.
- **요구 수준에 따라 바뀌는 핵심 설정:**
  - A2: HTTP API는 30초로 고정이다(05 문서). 넘으면 Function URL(P25, 900초)이나 컨테이너로 옮긴다.
  - A3: `protocol_type = "WEBSOCKET"` + `route_selection_expression = "$request.body.action"`. 연결 상태는 DynamoDB 등 외부에 둔다(추론). ⚠️근거없음
  - A7: API Gateway 10MB와 Lambda 6MB 중 작은 쪽이 적용된다(05 문서).
  - Web Adapter를 쓰면 `payload_format_version`과 어댑터 호환을 확인한다. 어댑터는 REST, HTTP, ALB를 지원한다.
- **함께 필요한 주변 자원:** P25와 같다. 커스텀 도메인은 `aws_apigatewayv2_domain_name` + ACM(인자 원문 `미확인`).
- **검증 명령:** P25와 같다. 배포 후 `curl https://<api-id>.execute-api.ap-northeast-2.amazonaws.com/<path>`.
- **출처 (확인 2026-10-01):** https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/apigatewayv2_api · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/apigatewayv2_integration · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/apigatewayv2_stage · https://github.com/awslabs/aws-lambda-web-adapter

## P27. Azure Container Apps
- **산출물 목록:**
  - Dockerfile.
  - Terraform `hashicorp/azurerm`
    - `azurerm_resource_group`, `azurerm_log_analytics_workspace`
    - `azurerm_container_app_environment`(`log_analytics_workspace_id`, `infrastructure_subnet_id`, `workload_profile`, `zone_redundancy_enabled`)
    - `azurerm_container_registry`(`admin_enabled = false`)
    - `azurerm_user_assigned_identity` + AcrPull 역할 할당(`7f951dda-4ed3-4680-a7ca-43fe172d538d`)
    - `azurerm_container_app`
    - `azurerm_container_app_job`(마이그레이션)
    - `azurerm_key_vault` + 비밀
  - 선택: ACA YAML(`az containerapp create|update --yaml`). 환경 생성은 YAML 입력을 지원하지 않는다.
  - CI 단계: `azure/login@v3`(OIDC) → 빌드·ACR 푸시 → `az containerapp job start`(마이그레이션) → `az containerapp update --image` 또는 `azure/container-apps-deploy-action@v2`.
- **요구 수준에 따라 바뀌는 핵심 설정 (`azurerm_container_app`):**
  - A5와 G3: `template.min_replicas`(기본 0). ingress를 끄고 min과 규칙이 모두 없으면 0으로 줄어든 뒤 다시 깨어나지 못한다. 워커는 반드시 min ≥ 1이나 KEDA 규칙을 둔다.
  - D2: `template.max_replicas`(기본 10, 최대 1,000), `http_scale_rule { concurrent_requests }`(기본 10).
  - F4
    - `template.termination_grace_period_seconds`(기본 30).
    - `liveness_probe` / `readiness_probe` / `startup_probe`: `transport`는 `HTTP`/`HTTPS`/`TCP`이고, exec와 gRPC는 지원하지 않는다.
  - A2: 인그레스 240초(05 문서). 설정 키는 `미확인`.
  - F5: `ingress { external_enabled (기본 false), target_port, transport = "auto" }`. 공개 앱은 `external_enabled = true`.
  - 비밀: `secret { name, key_vault_secret_id, identity }`(Key Vault Secrets User 역할). 버전 없는 URI면 30분 안에 최신 버전을 반영한다.
  - 이미지 pull: `registry { server, identity }`(사용자 할당 ID 권장). 시스템 할당 ID는 앱을 만들 때 쓸 수 없다.
- **함께 필요한 주변 자원:**
  - ACR, 사용자 할당 ID, Log Analytics.
  - VNet + 서브넷(consumption 전용은 /23, 워크로드 프로필은 /27).
  - 사설 DB: Azure Database for PostgreSQL 사설 액세스(`미확인`).
  - Key Vault.
  - 커스텀 도메인 + 관리 인증서(리소스 `미확인`).
  - GitHub OIDC 페더레이션 자격 증명(`미확인`).
- **검증 명령:**
  - `terraform validate` / `plan`
  - Checkov: ACR은 CKV_AZURE_137, 138, 139, 163, 164, 165, 166, 167, 233, 237. **`azurerm_container_app*` 대상 체크는 0건**이다. 공개 인그레스와 min_replicas는 커스텀 정책으로 검사한다.
  - 파트 1 docker 검증
  - 배포 후 `az containerapp show --query properties.latestRevisionName`(쿼리 경로 `미확인`)과 FQDN 스모크
- **출처 (확인 2026-10-01):**
  - https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/container_app · https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/container_app_job · https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/container_app_environment
  - https://learn.microsoft.com/en-us/azure/container-apps/scale-app · "your container app scales to zero and has no way of starting back up."
  - https://learn.microsoft.com/en-us/azure/container-apps/health-probes
  - https://learn.microsoft.com/en-us/azure/container-apps/application-lifecycle-management · "If your application doesn't respond within 30 seconds to the `SIGTERM` message"
  - https://learn.microsoft.com/en-us/azure/container-apps/azure-resource-manager-api-spec
  - https://learn.microsoft.com/en-us/azure/container-apps/managed-identity-image-pull
  - https://learn.microsoft.com/en-us/azure/container-apps/manage-secrets
  - https://www.checkov.io/5.Policy%20Index/terraform.html ⚠️출처확인필요

## 티어 2

## K. 쿠버네티스 공통 산출물

P28~P34에 공통이다. 구성은 simple-web-app `k8s/`(base + overlays + components)를 기준 사례로 삼는다.

**매니페스트 (Kustomize)**

| 종류 | 생성 규칙 | 연결 차원 |
|---|---|---|
| `Namespace` | 환경별(prod/dev). AWS면 `elbv2.k8s.aws/pod-readiness-gate-inject: enabled` 라벨 | — |
| `Deployment` | `resources.requests`/`limits` 필수(HPA와 Autopilot 과금이 requests 기준). `securityContext { runAsNonRoot, runAsUser: 10001, seccompProfile: RuntimeDefault }`, 컨테이너 `allowPrivilegeEscalation: false`, `readOnlyRootFilesystem: true`(+`/tmp` emptyDir), `capabilities.drop: [ALL]` | A6, F5 |
| probe | `startupProbe`(기동이 무거울 때, A5), `readinessProbe` `/readyz`(period 5, timeout 3), `livenessProbe` `/healthz`(timeout 5, failureThreshold 6: CPU가 부족할 때 재시작 폭주 방지, simple-web-app 실측) | F4 |
| 종료 | `terminationGracePeriodSeconds: 30`, `lifecycle.preStop: exec sleep 5~15`(LB가 대상에서 빼는 시간). preStop + 앱 드레인 < grace | F4 |
| `topologySpreadConstraints` | `topology.kubernetes.io/zone`, `maxSkew: 1`, `whenUnsatisfiable: ScheduleAnyway`(존이 하나여도 스케줄은 막지 않음) | F1 |
| `Service` | ClusterIP, 이름 있는 포트 | — |
| `Ingress` / `Gateway` | 클라우드별(P28~P33) | A2, A3 |
| `HorizontalPodAutoscaler` (autoscaling/v2) | CPU 60%, `behavior.scaleUp` 즉시, `scaleDown.stabilizationWindowSeconds: 300`(기본) | D2, D3 |
| `PodDisruptionBudget` | 웹은 `minAvailable: 1`, 최소 1개로 도는 워커는 `maxUnavailable: 1`(drain이 막히지 않게) | F1 |
| `Job` (마이그레이션) | `backoffLimit`(기본 6), `activeDeadlineSeconds`, `restartPolicy: Never`, `ttlSecondsAfterFinished`. Job은 Pod 템플릿을 바꿀 수 없으므로 배포마다 삭제 후 적용 | C9 |
| `CronJob` | B3. `concurrencyPolicy: Forbid`(필드 원문 `미확인`) | B3 |
| KEDA `ScaledObject` (선택) | 큐 길이 기반 워커 확장. 기본값은 `pollingInterval` 30, `cooldownPeriod` 300, `minReplicaCount` 0, `maxReplicaCount` 100. 최신 v2.21.0 | QU.consumer_scaling |
| `NetworkPolicy` | 기본 거부 + 필요한 경로만 허용(CNI 지원 필요) | F5 |
| `ConfigMap`/`Secret` | 비밀은 클라우드 비밀 저장소 → Terraform이 Secret 생성, 또는 External Secrets(`미확인`) | — |

**CI 단계**
1. `kustomize edit set image <name>=<registry>/<name>:<sha>`
2. 마이그레이션 Job 삭제 후 `kubectl apply -k <overlay>`
3. Job이 Complete나 Failed가 될 때까지 대기(실패하면 로그를 남기고 중단)
4. `kubectl rollout status deployment/<d> --timeout=300s`
5. 스모크(simple-web-app `docs/deploy.md` "클라우드 배포 절차")

**검증 명령**
- `kubectl kustomize <overlay> | kubeconform -strict -summary -schema-location default -schema-location '<CRD 카탈로그 URL>'`. BackendConfig, ScaledObject 같은 CRD 때문에 카탈로그를 지정한다.
- `kubectl apply --dry-run=server -k <overlay>`
- `checkov -d k8s --framework kubernetes`
  - 대상 ID: CKV_K8S_8(liveness), CKV_K8S_9(readiness), CKV_K8S_10/11/12/13(CPU·메모리 requests/limits), CKV_K8S_14(latest 태그), CKV_K8S_20(권한 상승), CKV_K8S_22(읽기 전용 FS), CKV_K8S_23(root), CKV_K8S_28(NET_RAW), CKV_K8S_29(securityContext), CKV_K8S_31(seccomp), CKV_K8S_37(capabilities), CKV_K8S_38(SA 토큰), CKV_K8S_40(높은 UID), CKV_K8S_43(다이제스트)
  - CKV_K8S_15(imagePullPolicy Always)와 CKV_K8S_43(다이제스트)은 sha 태그 운영과 충돌할 수 있다. 정책에 따라 건너뛴다(추론). ⚠️근거없음

**출처 (확인 2026-10-01)**
- https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/ · "A Pod is granted a term to terminate gracefully, which defaults to 30 seconds."
- https://kubernetes.io/docs/concepts/containers/container-lifecycle-hooks/
- https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/
- https://kubernetes.io/docs/concepts/workloads/pods/disruptions/
- https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/ · "If some of the Pod's containers do not have the relevant resource request set, CPU utilization for the Pod will not be defined"
- https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/
- https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
- https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/job-v1/ · https://kubernetes.io/docs/concepts/workloads/controllers/ttlafterfinished/
- https://kubernetes.io/docs/tasks/configure-pod-container/security-context/
- https://keda.sh/docs/latest/reference/scaledobject-spec/ ⚠️출처확인필요
- https://github.com/yannh/kubeconform ⚠️출처확인필요
- https://kubernetes.io/docs/reference/kubectl/generated/kubectl_apply/
- https://www.checkov.io/5.Policy%20Index/kubernetes.html ⚠️출처확인필요

## P28. GKE Autopilot
- **산출물 목록:**
  - Terraform
    - `google_container_cluster`(`enable_autopilot = true`, `location` = 리전, `deletion_protection`, `release_channel { channel = "REGULAR" }`, `private_cluster_config { enable_private_nodes = true }`)
    - `google_artifact_registry_repository`
    - `google_compute_global_address`(LB 고정 IP)
    - 서비스 계정과 IAM 바인딩(Workload Identity principal)
    - Cloud SQL, Memorystore(01·03 문서)
  - k8s: 공통(K) + `Ingress`(GCE) + `BackendConfig` + `FrontendConfig` + `ManagedCertificate`, 또는 Gateway API(`Gateway` `gatewayClassName: gke-l7-global-external-managed` + `HTTPRoute` + `GCPBackendPolicy` + `HealthCheckPolicy`).
  - CI: `google-github-actions/auth@v3` → `get-gke-credentials@v3` → K의 CI 단계.
- **요구 수준에 따라 바뀌는 핵심 설정:**
  - A6과 G3: `resources.requests`가 곧 과금이다.
    - 기본값은 0.5 vCPU / 2 GiB다.
    - CPU:메모리 비율은 1:1~1:6.5다.
    - 최소 CPU는 50m(버스팅 지원 클러스터) 또는 250m다.
    - 생성기는 이 범위 안의 값을 명시한다.
  - A2와 A3
    - Ingress: `BackendConfig.spec.timeoutSec`(기본 30). 클래식 ALB는 웹소켓도 이 시간에 끊는다(05 문서).
    - Gateway: `GCPBackendPolicy.spec.default.timeoutSec`(기본 30). 관리형 전역 LB의 활성 웹소켓은 24시간까지 유지된다(05 문서).
  - F4
    - `BackendConfig.connectionDraining.drainingTimeoutSec`(simple-web-app은 30). Gateway 쪽 드레인은 기본 0(꺼짐)이므로 명시한다.
    - 컨테이너 네이티브 LB(1.17+ 기본)는 readiness gate를 자동으로 넣는다.
  - F4: 헬스체크는 `BackendConfig.healthCheck.requestPath` 또는 `HealthCheckPolicy`.
  - F5: `FrontendConfig.redirectToHttps`, `ManagedCertificate`(발급에 최대 60분, 와일드카드 불가).
  - F1: Autopilot은 항상 리전 클러스터다. 생성 후 바꿀 수 없다.
- **함께 필요한 주변 자원:**
  - VPC와 서브넷(보조 범위), Cloud NAT(사설 노드의 외부 출구).
  - Cloud SQL 사설 IP 또는 Auth Proxy(`미확인`).
  - Workload Identity: Autopilot은 항상 켜져 있다. principal `principal://iam.googleapis.com/projects/NUM/locations/global/workloadIdentityPools/PROJECT.svc.id.goog/subject/ns/NS/sa/KSA`에 역할을 준다.
  - 도메인 A 레코드 → 전역 고정 IP.
  - `REAL_IP_FROM`에 LB IP를 넣는다(simple-web-app 계약).
- **검증 명령:**
  - `terraform validate` / `plan`
  - Checkov: GKE는 CKV_GCP_1, 7, 8, 12, 13, 18, 20, 21, 23, 25, 61, 64, 65, 66, 69, 70, 123, CKV2_GCP_19. Autopilot은 노드 풀 체크(CKV_GCP_9, 10, 22, 68, 71, 72)가 해당 없을 수 있다(추론). ⚠️근거없음
  - K의 검증 명령
  - 배포 후 `kubectl get managedcertificate`가 Active인지, 도메인 스모크
- **출처 (확인 2026-10-01):**
  - https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/container_cluster · "On version 5.0.0+ of the provider, you must explicitly set `deletion_protection = false`" (삭제할 때)
  - https://docs.cloud.google.com/kubernetes-engine/docs/concepts/types-of-clusters · "All Autopilot clusters are _regional_"
  - https://docs.cloud.google.com/kubernetes-engine/docs/concepts/autopilot-resource-requests
  - https://docs.cloud.google.com/kubernetes-engine/docs/how-to/ingress-configuration · timeoutSec "the default value is 30 seconds."
  - https://docs.cloud.google.com/kubernetes-engine/docs/how-to/managed-certs
  - https://docs.cloud.google.com/kubernetes-engine/docs/how-to/deploying-gateways · https://docs.cloud.google.com/kubernetes-engine/docs/how-to/configure-gateway-resources
  - https://docs.cloud.google.com/kubernetes-engine/docs/how-to/workload-identity
  - https://docs.cloud.google.com/kubernetes-engine/docs/how-to/container-native-load-balancing
  - https://www.checkov.io/5.Policy%20Index/terraform.html ⚠️출처확인필요

## P29. GKE Standard (존 · 리전)
- **산출물 목록:**
  - P28과 같다. 다른 점은 다음과 같다.
    - `google_container_cluster`: `remove_default_node_pool = true`, `initial_node_count = 1`, `workload_identity_config { workload_pool = "<project>.svc.id.goog" }`
    - `google_container_node_pool`: `autoscaling { min_node_count, max_node_count }` 또는 `total_*`, `management { auto_repair, auto_upgrade }`, 노드 SA
    - Gateway를 쓰려면 클러스터에서 Gateway API를 켠다(`--gateway-api=standard`, Terraform 키는 `미확인`).
- **요구 수준에 따라 바뀌는 핵심 설정:**
  - F1
    - `location`이 존이면 존 클러스터, 리전이면 리전 클러스터다. 생성 후 바꿀 수 없다.
    - 리전 클러스터는 노드 풀을 3개 존에 복제하므로 `initial_node_count`와 `min_node_count`는 **존당** 값이다(1 → 3노드). G3 고정비에 바로 반영된다.
  - D2와 D3: 노드 풀 `autoscaling`. `node_count`와 함께 쓰지 않는다.
  - A6: `node_config.machine_type`. GPU면 `guest_accelerator`(키 원문 `미확인`).
  - 나머지(A2, A3, F4, F5)는 P28과 같다.
- **함께 필요한 주변 자원:** P28과 같다. Workload Identity는 `workload_identity_config`로 켜야 한다. 노드에 GKE 메타데이터 서버 설정이 필요하다(CKV_GCP_69).
- **검증 명령:** P28 + 노드 풀 체크 CKV_GCP_9, 10, 22, 68, 71, 72.
- **출처 (확인 2026-10-01):** https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/container_cluster · https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/container_node_pool · "Minimum number of nodes per zone in the NodePool." · https://docs.cloud.google.com/kubernetes-engine/docs/concepts/types-of-clusters · "can't be updated after cluster creation"

## P30. EKS — 관리형 노드 그룹 + Cluster Autoscaler
- **산출물 목록:**
  - Terraform
    - `terraform-aws-modules/eks`(v21.26.0) 또는 직접 작성
      - `aws_eks_cluster`(`access_config { authentication_mode = "API" }`, `endpoint_public_access`, 비밀 암호화)
      - `aws_eks_node_group`(`scaling_config { desired_size, min_size, max_size }`, `instance_types`(기본 `t3.medium`))
      - `aws_eks_addon`(vpc-cni, coredns, kube-proxy, eks-pod-identity-agent, metrics-server — 애드온 이름 원문 `미확인`)
      - `aws_eks_pod_identity_association`(앱과 컨트롤러 권한)
    - VPC 모듈, ECR, RDS, ElastiCache
    - Helm으로 AWS Load Balancer Controller(v3.5.0)와 Cluster Autoscaler를 설치한다(`helm_release`, 차트 이름 `미확인`).
  - k8s: 공통(K) + `Ingress`(`ingressClassName: alb`, 어노테이션 아래).
  - CI: `configure-aws-credentials@v6` → ECR 푸시 → `aws eks update-kubeconfig --name C --region ap-northeast-2` → K의 CI 단계.
- **요구 수준에 따라 바뀌는 핵심 설정:**
  - Ingress 어노테이션
    - `alb.ingress.kubernetes.io/scheme: internet-facing`(기본 internal)
    - `target-type: ip`(권장, readiness gate 조건)
    - `healthcheck-path: /healthz`
    - `certificate-arn`, `listen-ports`, `ssl-redirect: "443"`
  - F4
    - `target-group-attributes: deregistration_delay.timeout_seconds=30` + 네임스페이스 라벨 `elbv2.k8s.aws/pod-readiness-gate-inject=enabled`(ip 모드에서만).
    - preStop `sleep`. EKS 모범 사례도 "PreStop hook can be a simple Exec handler such as `sleep 10`."라고 적는다.
  - A2와 A3: `load-balancer-attributes: idle_timeout.timeout_seconds=<초>`(ALB 기본 60).
  - D2와 D3: 노드 그룹 `min_size`/`max_size` + Cluster Autoscaler. `lifecycle { ignore_changes = [scaling_config[0].desired_size] }`(공식 예시).
  - F1: 노드 그룹 서브넷을 3 AZ에 걸치고, Pod에 topologySpread(K)를 둔다.
- **함께 필요한 주변 자원:**
  - VPC(공용 서브넷은 ALB, 사설 서브넷은 노드), NAT(AZ당), 또는 VPC 엔드포인트(P22 목록 + EKS용, `미확인`).
  - ACM + Route 53.
  - ECR.
  - Pod Identity(OIDC provider 없이 동작) 또는 IRSA.
  - metrics-server(HPA 필수, simple-web-app 사전 요구).
  - NetworkPolicy를 쓰려면 VPC CNI의 network policy 기능을 켠다.
- **검증 명령:**
  - `terraform validate` / `plan`
  - Checkov: CKV_AWS_37, CKV_AWS_38, CKV_AWS_39, CKV_AWS_58, CKV_AWS_100, CKV_AWS_339 + ECR 체크
  - K의 검증 명령
  - 배포 후
    - `kubectl get ingress`에서 ALB 주소 확인
    - `aws elbv2 describe-target-health`(명령 원문 `미확인`)
    - 스모크
- **출처 (확인 2026-10-01):**
  - https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/eks_cluster · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/eks_node_group · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/eks_pod_identity_association · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/eks_addon
  - https://github.com/terraform-aws-modules/terraform-aws-eks ⚠️출처확인필요
  - https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/guide/ingress/annotations/ · https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/deploy/pod_readiness_gate/ · "this only works with `target-type: ip`"
  - https://docs.aws.amazon.com/eks/latest/best-practices/load-balancing.html
  - https://docs.aws.amazon.com/cli/latest/reference/eks/update-kubeconfig.html
  - https://www.checkov.io/5.Policy%20Index/terraform.html ⚠️출처확인필요

## P31. EKS — Karpenter
- **산출물 목록:**
  - P30과 같지만 Cluster Autoscaler 대신 Karpenter를 둔다.
    - 모듈의 karpenter 서브모듈 또는 Helm
    - 컨트롤러를 띄울 작은 관리형 노드 그룹이나 Fargate 프로필
  - `NodePool`(`karpenter.sh/v1`)
  - `EC2NodeClass`(`karpenter.k8s.aws/v1`, 필수: `subnetSelectorTerms`, `securityGroupSelectorTerms`, `amiSelectorTerms`(alias 예 `al2023@v20240807`), `role` 또는 `instanceProfile`)
- **요구 수준에 따라 바뀌는 핵심 설정:**
  - G3: `disruption.consolidationPolicy`(`WhenEmptyOrUnderutilized`/`WhenEmpty`), `consolidateAfter`.
  - F1과 F4
    - `disruption.budgets`(정의하지 않으면 `nodes: 10%`).
    - `expireAfter`(기본 720h). 노드가 만료되면 Pod가 옮겨지므로 PDB와 graceful shutdown이 필수다. budget은 만료된 노드의 종료를 막지 않는다.
    - 중단되면 안 되는 Pod에는 `karpenter.sh/do-not-disrupt` 어노테이션을 둔다.
  - A6과 G3: NodePool `requirements`(인스턴스 패밀리, `capacity-type` spot/on-demand, 키 원문 `미확인`).
- **함께 필요한 주변 자원:** P30과 같다. 노드 IAM 역할, Karpenter 컨트롤러 권한(Pod Identity), 서브넷과 SG 태그(셀렉터 대상), 인터럽션 큐(SQS, `미확인`).
- **검증 명령:** P30 + kubeconform에 Karpenter CRD 스키마를 넣는다(카탈로그). 배포 후 `kubectl get nodeclaims`(리소스 이름 `미확인`).
- **출처 (확인 2026-10-01):** https://karpenter.sh/docs/concepts/disruption/ · "By default, `expireAfter` is set to `720h` (30 days)." / "If undefined, Karpenter will default to one budget with `nodes: 10%`." · https://karpenter.sh/docs/concepts/nodeclasses/ ⚠️출처확인필요

## P32. EKS — Auto Mode
- **산출물 목록:**
  - `aws_eks_cluster`
    - `compute_config { enabled = true, node_pools = ["general-purpose","system"], node_role_arn }`. `node_role_arn`은 Auto Mode를 켠 뒤 바꿀 수 없다.
    - `kubernetes_network_config.elastic_load_balancing.enabled = true`
    - `storage_config.block_storage.enabled = true`
  - 모듈 v21은 Auto Mode가 기본이다. 끄려면 `compute_config = { enabled = false }`를 명시해야 한다.
  - **LB 컨트롤러를 따로 설치하지 않는다.** `IngressClass`(`spec.controller: eks.amazonaws.com/alb`) + `IngressClassParams`(`eks.amazonaws.com/v1`)를 생성한다.
  - GPU나 특수 인스턴스가 필요하면 사용자 NodePool을 둔다(05 문서).
- **요구 수준에 따라 바뀌는 핵심 설정:**
  - Ingress
    - `kubernetes.io/ingress.class` 어노테이션은 지원하지 않으므로 `spec.ingressClassName`을 쓴다.
    - `group.name`은 IngressClass에서만 지정한다.
    - IngressClass에 붙인 어노테이션은 무시되므로 IngressClassParams로 옮긴다.
    - targetType 기본은 `ip`다.
    - 기존 P30 매니페스트를 그대로 쓰면 일부 어노테이션이 무시되므로 **부분 수정**한다.
  - F4: 노드 수명은 최대 21일(05 문서). PDB와 graceful shutdown이 필수다.
  - 나머지는 P30과 같다.
- **함께 필요한 주변 자원:** P30에서 LB 컨트롤러와 Cluster Autoscaler를 뺀 것. 노드 IAM 역할.
- **검증 명령:** P30과 같다. 정적 검사(grep 또는 커스텀 정책, 추론)로 지원하지 않는 어노테이션을 찾는다. ⚠️근거없음
- **출처 (확인 2026-10-01):** https://docs.aws.amazon.com/eks/latest/userguide/auto-configure-alb.html · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/eks_cluster · https://github.com/terraform-aws-modules/terraform-aws-eks · "to disable EKS Auto Mode you will have to explicitly set: compute_config = { enabled = false }" ⚠️출처확인필요

## P33. EKS — Fargate 프로필
- **산출물 목록:** P30 + `aws_eks_fargate_profile`(`subnet_ids` = 사설 서브넷만, `selector { namespace }` 필수, `pod_execution_role_arn`은 `eks-fargate-pods.amazonaws.com`이 맡을 수 있는 역할). 노드 그룹은 없거나 시스템용만 둔다. LB 컨트롤러는 Helm으로 설치한다.
- **요구 수준에 따라 바뀌는 핵심 설정:**
  - Ingress `target-type: ip`가 필수다(Fargate에는 NodePort가 없다, 05 문서).
  - A6: Pod `resources.requests`로 Fargate 크기가 정해진다(05 문서).
  - B2: EBS를 쓸 수 없고 EFS 정적 프로비저닝만 된다(05 문서).
  - DaemonSet은 동작하지 않는다(로그 수집 방식이 바뀜, `미확인`).
- **함께 필요한 주변 자원:** 사설 서브넷 + NAT가 필수다(05 문서). 그 밖에는 P30과 같다.
- **검증 명령:** P30과 같다.
- **출처 (확인 2026-10-01):** https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/eks_fargate_profile

## P34. VM 위 k3s
- **산출물 목록:**
  - VM: Terraform `aws_instance` 또는 `google_compute_instance` + 보안 그룹·방화벽(80, 443, 6443은 관리 IP만).
  - 설치 스크립트(user_data / `metadata_startup_script`): `curl -sfL https://get.k3s.io | sh -`.
    - HA는 서버 3대(홀수)다. 첫 서버는 `--cluster-init`, 나머지는 `--server https://<ip>:6443`으로 붙는다.
    - 에이전트는 `K3S_URL`, `K3S_TOKEN`으로 합류한다.
  - k8s: 공통(K). Ingress는 기본 Traefik이고 ServiceLB를 쓴다. 인증서는 cert-manager(`미확인`) 또는 Traefik ACME(`미확인`).
  - CI: kubeconfig(`/etc/rancher/k3s/k3s.yaml`)를 안전하게 전달해야 한다. 이것이 자동화의 약한 고리다(추론). ⚠️근거없음
- **요구 수준에 따라 바뀌는 핵심 설정:**
  - F1: 단일 서버면 VM 장애가 곧 서비스 중단이다. 3대 HA는 비용이 3배다.
  - B2: 기본 스토리지는 local-path(`/var/lib/rancher/k3s/storage`)라 노드에 고정된다. DB는 관리형 DB로 뺀다.
  - Traefik 설정은 `HelmChartConfig`로 바꾸고, 끄려면 `--disable=traefik`.
  - `metadata_startup_script`를 바꾸면 GCE 인스턴스가 재생성되고, `aws_instance.user_data`를 바꾸면 인스턴스가 중지 후 시작된다. 설치 스크립트를 바꾸면 클러스터가 내려간다.
- **함께 필요한 주변 자원:** VM, 고정 IP, DNS, 백업(etcd 스냅샷, `미확인`), OS 패치. 운영 부담은 05 문서 G2를 따른다.
  - **자동화 불가 단계:** 노드 OS와 k3s 업그레이드 운영(사람이 맡는다).
- **검증 명령:** `terraform validate`, K의 검증 명령. 설치 후 `kubectl get nodes`가 Ready인지 확인한다.
- **출처 (확인 2026-10-01):** https://docs.k3s.io/quick-start · https://docs.k3s.io/datastore/ha-embedded · "must be comprised of an odd number of server nodes" · https://docs.k3s.io/networking/networking-services · https://docs.k3s.io/add-ons/storage · https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_instance · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/instance ⚠️출처확인필요

## 기준선

## P35. 단일 VM + docker compose — EC2
- **산출물 목록:**
  - Dockerfile.
  - `compose.yaml`
    - `services.<app>`: `image`, `restart: unless-stopped`, `healthcheck`, `stop_grace_period`, `read_only`, `user`, `env_file`
    - `depends_on: { db: { condition: service_healthy } }`
    - `migrate` 일회성 서비스
  - 리버스 프록시 `Caddyfile`(자동 HTTPS, HTTP를 HTTPS로 리다이렉트).
  - Terraform
    - `aws_instance`(`user_data`로 Docker 설치와 compose 기동, `user_data_replace_on_change`)
    - `aws_eip`(고정 IP), `aws_security_group`(80/443, SSH는 막고 SSM 사용)
    - `aws_iam_instance_profile`(ECR pull, SSM)
    - `aws_route53_record`
    - EBS 스냅샷 정책(`aws_dlm_lifecycle_policy`, `미확인`)
  - CI: OIDC → ECR 푸시 → SSM Run Command로 `docker compose pull && docker compose run --rm migrate && docker compose up -d`(SSM 명령 원문 `미확인`).
- **요구 수준에 따라 바뀌는 핵심 설정:**
  - F4: `stop_grace_period`(기본 10초). `up -d`로 재생성하는 동안 짧은 중단이 생긴다. 무중단이 필요하면(F4 "불가") 이 기준선은 맞지 않는다(추론). ⚠️근거없음
  - F4: `healthcheck { test, interval, timeout, retries, start_period }`, `restart: unless-stopped`.
  - F1: 단일 AZ, 단일 인스턴스다. F1이 "짧아야 함" 이상이면 교체한다.
  - B2: EBS 영속. 단일 AZ다(05 문서).
  - user_data를 바꾸면 기본으로 인스턴스가 중지 후 시작된다. `user_data_replace_on_change = true`면 삭제 후 재생성된다.
- **함께 필요한 주변 자원:** 탄력적 IP, Route 53, ECR, SSM(SSH 대신), CloudWatch 에이전트(로그, `미확인`), 백업. 인증서는 Caddy가 Let's Encrypt나 ZeroSSL에서 받는다. 80/443을 외부에 열고, A 레코드가 VM을 가리켜야 한다.
  - **자동화 불가 단계:** OS 패치와 디스크 관리 등 서버 운영.
- **검증 명령:**
  - `docker compose config --quiet`
  - `caddy validate --config Caddyfile`(명령 원문 `미확인`)
  - `terraform validate`
  - 파트 1 docker 검증
  - 배포 후 `curl https://<domain>/readyz`
  - Checkov는 `aws_instance` 체크가 있지만 이번에 ID를 확인하지 않았다(`미확인`).
- **출처 (확인 2026-10-01):** https://docs.docker.com/reference/compose-file/services/ · https://raw.githubusercontent.com/compose-spec/compose-spec/main/05-services.md · "Default value is 10 seconds for the container to exit before sending SIGKILL" · https://docs.docker.com/reference/cli/docker/compose/config/ · https://caddyserver.com/docs/automatic-https · https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/instance ⚠️출처확인필요

## P36. 단일 VM + docker compose — Compute Engine
- **산출물 목록:** P35와 같다. Terraform만 다르다.
  - `google_compute_instance`: Container-Optimized OS 이미지 또는 일반 이미지 + `metadata_startup_script`. 스크립트를 바꾸면 인스턴스가 재생성된다. `allow_stopping_for_update`.
  - `google_compute_address`, `google_compute_firewall`(80/443).
  - 서비스 계정(AR reader).
  - COS에는 Docker, containerd, cloud-init이 미리 설치되어 있고 패키지 매니저가 없다. compose를 쓰려면 별도 배치가 필요하다(`미확인`).
- **요구 수준에 따라 바뀌는 핵심 설정:** P35와 같다. B2는 PD 영속(존)이다.
- **함께 필요한 주변 자원:** 고정 외부 IP, Cloud DNS 또는 외부 DNS, Artifact Registry, OS Login이나 IAP SSH(`미확인`), 스냅샷 일정(`미확인`).
  - **자동화 불가 단계:** 서버 운영.
- **검증 명령:** P35와 같다(`terraform validate`, compose config, 스모크).
- **출처 (확인 2026-10-01):** https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_instance · "forces the instance to be recreated (thus re-running the script) if it is changed." · https://docs.cloud.google.com/container-optimized-os/docs/concepts/features-and-benefits · "come pre-installed with the Docker and containerd runtimes and `cloud-init`"

---

## 생성 자동화를 막는 발견

1. **Railway Config as Code 종료**
   - `railway.json`과 `railway.toml`은 deprecated다. 기존 서비스도 **2026-12-01에 읽히지 않게 된다.**
   - 생성 대상은 `.railway/railway.ts`(IaC)다.
   - 기존 `railway.json`은 판정이 교체다. railway.ts에 드레인, 겹침 배포, 크론 키가 있는지는 `미확인`이다.
2. **서울 Cloud Run에는 도메인 매핑이 없다**
   - 도메인 매핑 지원 리전에 asia-northeast3가 없고, 기능 자체도 Preview(운영 비권장)다.
   - 서울 Cloud Run에 커스텀 도메인을 붙이려면 전역 외부 LB + 서버리스 NEG + 관리 인증서를 생성해야 한다(월 약 $18 고정비 추가).
   - Terraform `cpu_idle`도 함정이다. `resources`를 쓰면 기본값이 사라져 요청 기반 과금을 의도해도 명시해야 한다.
3. **정적 검사 공백**
   - Checkov에는 `google_cloud_run_v2_*`(CKV_GCP_102는 v1 IAM만)와 `azurerm_container_app*`을 대상으로 하는 체크가 없다. 공개 접근, min 인스턴스 같은 핵심 위험을 커스텀 정책으로 직접 써야 한다.
   - CKV_AWS_336(읽기 전용 루트 FS)과 ECS Exec는 함께 쓸 수 없다.
   - CKV_K8S_15·43은 sha 태그 운영과 충돌할 수 있다.
4. **티어 0 대부분은 OIDC가 불가하고, IaC가 일부만 된다**
   - Vercel, Netlify, Cloudflare, Railway, Render, Fly, Heroku, DO, Koyeb, Supabase는 정적 토큰만 받는다. 첫 토큰 발급은 사람이 해야 한다.
   - IaC 공백
     - Netlify Terraform은 사이트를 만들 수 없다.
     - Cloudflare Containers는 Terraform 경로가 없고, DO 마이그레이션은 Terraform 첫 apply에서 실패한다.
     - Fly provider는 보관되었다.
     - Replit은 API·CLI·IaC가 전혀 없다(사실상 생성 대상에서 제외).
     - Render Blueprint 최초 생성과 Firebase App Hosting GitHub 연결은 대시보드에서 해야 한다.
   - Vercel 메모리는 `vercel.json`으로 정할 수 없고 Terraform `resource_config`나 대시보드로만 정한다.
5. **기본값이 앱 계약을 깨는 곳**
   - 종료 유예
     - Lambda는 확장이 없으면 종료 0ms다.
     - Vercel은 500ms다.
     - Fly는 기본 신호가 SIGINT(5초)라 `kill_signal`을 생성하지 않으면 SIGTERM 처리 코드가 동작하지 않는다.
   - 타임아웃·포트·헬스 기본값
     - Lambda `timeout` 기본 3초.
     - ECS Express `container_port` 기본 80, `health_check_path` 기본 `/`.
     - ALB `deregistration_delay` 300초, GKE Ingress·Gateway 백엔드 30초.
     - 생성기는 이 값을 항상 명시해야 한다.
   - 추가로, Prisma ORM 8에서 마이그레이션 명령이 `prisma db migrate`로 바뀌었다. 버전을 보고 명령을 골라야 한다.
