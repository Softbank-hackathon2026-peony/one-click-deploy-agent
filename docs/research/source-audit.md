# 출처 신뢰성 감사 — infrafit 조사 문서와 지식 베이스

- 작성일: 2026-10-02
- 대상: `docs/research/**/*.md` 21개 파일(약 23,000줄), `knowledge/defaults.yaml`, `knowledge/components/catalog.yaml`, `knowledge/signatures/*.yaml`, `knowledge/images.yaml`
- 이 감사는 출처를 새로 찾거나 주장 내용을 고치지 않았다. 웹을 열지 않았다. 조사 문서에는 표시(⚠️)만 덧붙였다.
- 최종 판정(2026-10-02): 사용자의 최종 규칙(§1 마지막)으로 이전 B·애매 판정과 이전 A 발행처를 다시 판정했다. ` ⚠️출처확인필요` 표시는 더 이상 없다. 남은 표시는 ` ⚠️출처부적격`(쓸 수 없음)과 ` ⚠️근거없음`(출처 없음) 둘이다.

## 1. 규칙 (사용자 지시)

처음 지시(요약 그대로):

> 주장은 **그 주장의 주제를 소유한 당사자의 공식 출판물**이 출처일 때만 쓸 수 있다. 공급사가 자기 제품에 대해 쓴 문서·가격표·API 레퍼런스·공식 블로그, 소프트웨어 프로젝트 자신의 문서나 공식 저장소(코드, README, 변경 기록), 표준 기구의 원문(IETF RFC, W3C, ISO, OWASP 자체 출판물, PCI SSC, 법령은 정부·법령 사이트), 클라우드 공급자의 가격 API가 여기에 해당한다. 그 밖의 것 — 개인 블로그·사이트(martinfowler.com, microservices.io, brendangregg.com, martin.kleppmann.com …), 커뮤니티 포럼·Q&A(answers.netlify.com, Stack Overflow, Reddit …), 뉴스(zdnet …), 비공식 미러(EUR-Lex 대신 gdpr-info.eu …), 다른 회사 제품에 대해 쓴 공급사 글(예: koyeb.com이 Heroku를 설명), 커뮤니티 선언문, 다른 대상의 사실을 말하는 데 쓴 제3자 라이브러리 문서 — 는 **허용하지 않으며**, 그것이 뒷받침하는 주장은 틀렸거나 쓸 수 없는 것으로 다룬다. 출처가 없는 주장("인용 미확인", "(추론)", 근거 없는 추론, "미확인" 값)도 판단 근거로 쓸 수 없다.
>
> 억지로 맞추지 않는다. 부적격 출처를 "사실상 공식"으로 재분류하지 않는다. 대체 출처를 찾지 않는다. 판단은 도메인이 아니라 **인용 하나하나(그 주장의 주제를 발행처가 소유하는가)** 로 한다. 예: github.com/yannh/kubeconform은 kubeconform 동작에는 공식이지만 쿠버네티스 API 사실에는 아니다. koyeb.com은 Koyeb에는 공식이지만 Heroku에는 아니다. 판단이 안 서면 "애매 — 사용자 결정"으로 두고, 애매함을 허용 쪽으로 풀지 않는다. "미확인"이 *값을 모른다*는 뜻(정직한 공백)인 경우와 *출처 없이 사실로 적은 주장*을 구분해 따로 센다.

수정 지시(2026-10-02, 위의 허용 기준을 대체):

> 출처는 (1) 공식 — 주장 주제의 소유자가 발행 — **이고** (2) 팀원과 면접관이 권위 있다고 알아볼 발행처여야 한다. 덜 알려진 발행처는 자기 제품에 대한 글이라도 받아들이지 않는다. 사용자가 명시한 부적격 출처: martinfowler.com, microservices.io, brendangregg.com, martin.kleppmann.com, principlesofchaos.org, answers.netlify.com, zdnet.co.kr, gdpr-info.eu, koyeb.com(Koyeb 자신에 대한 주장 포함 전부), 12factor.net.
>
> - **A**: 공식이고 널리 알려진 발행처 — 주요 클라우드(AWS, Google Cloud·Firebase·sre.google, Microsoft Azure), 표준 기구(IETF/RFC, W3C, OWASP, PCI SSC, law.go.kr 같은 정부 법령 사이트), 모든 백엔드 엔지니어가 아는 주류 소프트웨어의 공식 문서·저장소(Kubernetes, Docker, PostgreSQL, MySQL, Redis, MongoDB, SQLite, nginx, Node.js, Python, Django, Flask, FastAPI, Spring, Next.js, React/Vite, Terraform/HashiCorp, GitHub, Prometheus, Grafana, OpenTelemetry, Cloudflare, Stripe, Vercel, Netlify, Supabase, Heroku, DigitalOcean).
> - **B**: 공식이지만 청중이 모를 수 있는 발행처(fly.io, render.com, railway, replit, convex, turso, neon, planetscale, upstash, appwrite, pocketbase, inngest, trigger.dev, pusher, ably, pinecone, celery, bullmq, keda, karpenter, chaos-mesh, k3s, checkov, 단일 관리자 GitHub 저장소, 라이브러리 문서 사이트 등). 발행처별로 건수를 모아 사용자가 발행처 단위로 받아들일지 정한다. 감사자가 정하지 않는다.
> - **C**: 허용 안 함 — 비공식이거나 사용자가 지정한 부적격 출처.
>
> 표시: C에만 기대는 줄은 ` ⚠️출처부적격`, B에만 기대는 줄은 ` ⚠️출처확인필요`, 출처 없이 사실을 적은 줄은 ` ⚠️근거없음`.

최종 지시(2026-10-02, 위 A/B 구분을 대체하는 구속 규칙):

> 인용은 **공식**(주장 주제의 소유자가 발행)이고, **발행처가 다음 중 하나 이상을 충족할 때만** 적격(A)이다.
>
> 1. Stack Overflow 2025 개발자 설문의 기술 목록에 있다. 사용자 검증 목록 — 클라우드·도구: Docker, npm, AWS, Pip, Kubernetes, Microsoft Azure, Homebrew, Vite, Google Cloud, Make, Yarn, Cloudflare, NuGet, APT, Webpack, Terraform, Maven, Cargo, Gradle, pnpm, Firebase, Prometheus, Ansible, Podman, Chocolatey, Composer, MSBuild, Digital Ocean, Vercel, Poetry, Datadog, Pacman, Netlify, Bun, Supabase, Heroku, Ninja, Splunk, New Relic, Railway, IBM Cloud, Yandex Cloud. 데이터베이스: PostgreSQL, MySQL, SQLite, Microsoft SQL Server, Redis, MongoDB, MariaDB, Elasticsearch, Oracle, DynamoDB, BigQuery, Supabase, Cloud Firestore, H2, Firebase Realtime Database, Microsoft Access, Cosmos DB, Snowflake, InfluxDB, Databricks SQL, DuckDB, Cassandra, Neo4J, Valkey, ClickHouse, IBM DB2, Amazon Redshift, CockroachDB, PocketBase, Datomic. 웹 프레임워크: Node.js, React, jQuery, Next.js, Express, ASP.NET Core, Angular, Vue.js, FastAPI, Spring Boot, Flask, ASP.NET, WordPress, Django, Laravel, AngularJS, Svelte, Blazor, NestJS, Ruby on Rails, Astro, Deno, Symfony, Nuxt.js, Fastify, Axum, Phoenix, Drupal. 프로그래밍 언어의 공식 사이트(Python, Go, Java 등)도 해당한다.
> 2. CNCF 졸업 또는 인큐베이팅 프로젝트(사용자 검증: Envoy, Argo, cert-manager, KEDA, Chaos Mesh, Kubernetes, Prometheus, OpenTelemetry, Helm, containerd. Karpenter는 쿠버네티스 공식 하위 프로젝트(kubernetes-sigs)로 인정. k3s, Traefik, Trivy는 아님).
> 3. Apache Software Foundation 최상위 프로젝트(Tomcat, Kafka 등).
> 4. A 프레임워크의 공식 문서가 공식 배포·실행 서버로 제시하는 도구: uvicorn(FastAPI 문서), gunicorn(Flask·Django 문서). waitress, uWSGI, mod_wsgi도 같은 경우 해당하나 조사 문서에 그 인용이 없다.
> 5. 표준 기구와 정부 법령 사이트, 주요 클라우드 자체 문서(AWS, sre.google을 포함한 Google Cloud, Azure), GitHub 자체 문서. MDN은 해당하지 않는다(C 유지).
>
> 그 밖의 이전 B는 모두 C(허용 안 함)다(Render, Fly.io, Replit, Neon, Upstash, Appwrite, Convex, PlanetScale, Pinecone, Turso, Prisma, Celery, BullMQ, Socket.IO, Traefik, Caddy, Trivy, Sentry, Let's Encrypt, k3s, Inngest, Ably, Pusher, Lovable, Bolt, Trigger.dev, 단일 관리자 저장소 등). 사용자가 이미 지정한 부적격 출처는 C로 남는다. 애매 4건(builder.aws.com 2건, web.dev 2건)은 C다.
>
> 줄 표시: ` ⚠️출처확인필요`가 붙었던 줄은, 그 줄의 B 인용이 모두 A가 되면 표시를 지우고, C가 된 인용에만 기대면 ` ⚠️출처부적격`으로 바꾼다. 섞여 있으면 A 인용이 하나라도 그 주장을 뒷받침할 때만 표시를 지우고, 아니면 ` ⚠️출처부적격`. ` ⚠️근거없음`은 그대로 둔다.

**검증 메모.** SO 2025 목록과 CNCF 등급은 사용자가 확인해 준 목록을 그대로 썼다. 목록 밖이지만 기준 2에 해당한다고 감사자가 판단한 것은 Istio·OPA(둘 다 CNCF 졸업)뿐이고 §5.1에 따로 적었다. 이 감사는 웹을 열지 않았다.

## 2. 방법

1. **URL 추출.** 21개 파일에서 `https?://` 문자열 4,377개를 뽑았다(코드 블록 안 포함, `source-audit.md` 제외). 파일·줄·URL을 기록했다.
2. **발행처 판정.** 호스트로 1차 분류하고, 호스트만으로는 발행처가 정해지지 않는 곳은 경로로 나눴다.
   - `github.com`·`raw.githubusercontent.com`: 저장소 조직으로 판정(예: `kubernetes`, `hashicorp`, `docker-library`, `nodejs`, `vercel`, `cloudflare`, `supabase`, `digitalocean`, `aws`·`awslabs`·`aws-actions`, `open-telemetry`, `compose-spec`, `redis` → A, 나머지 → B, `koyeb` → C).
   - `registry.terraform.io`: provider 네임스페이스로 판정(`hashicorp`, `cloudflare`, `vercel`, `supabase`, `mongodb`, `integrations`(GitHub), `netlify`, `heroku`, `digitalocean` → A, 그 밖의 provider → B, `koyeb` → C). Terraform 인자 이름·기본값은 provider 자신이 주제이므로 provider 문서를 그 주제의 공식 출처로 봤다.
   - `hub.docker.com`: `/_/`(Docker 공식 이미지) → A, `r/amazon` → AWS(A), `r/supabase` → A, `r/pgvector`·`r/valkey` → B.
   - 수정 지시가 A 목록에 넣은 sre.google(구글의 일반 SRE 원칙)과 같은 취급으로, AWS Well-Architected·백서·Builders' Library와 GCP 아키텍처 문서도 A로 셌다(주요 클라우드의 공식 출판물). 이 판단이 맞지 않으면 §6의 "판단 메모"를 보라.
   - 수정 지시의 A 목록에 없는 발행처는 널리 알려져 있어 보여도(Express, Apache Kafka, Go, npm, Let's Encrypt, OpenAI, Anthropic 등) 감사자가 A로 올리지 않고 B로 두었다. 받아들일지는 §5 표에서 발행처 단위로 결정한다.
3. **주제 소유 검사(인용 단위).** 발행처가 A나 B여도 그 인용이 *다른 대상*의 사실을 말하면 C로 내렸다. 찾는 방법:
   - 주요 공급사 도메인(AWS, GCP, Vercel, Cloudflare, Supabase, Neon 등) 인용 중, 같은 줄에 그 공급사가 소유하지 않은 제품 이름이 나오는 291줄을 뽑아 모두 읽었다.
   - 라이브러리·프레임워크 문서, GitHub 저장소, Terraform provider, 다른 공급사 비교 글(render.com의 경쟁사 비교, appwrite 블로그 등) 인용은 전부 문맥을 읽었다.
   - 그 결과 C로 내린 인용 11건(§4 표의 "주제 불일치")과 애매 4건(§6)을 표에 적었다. 비교 글이라도 자기 제품 수치를 인용한 경우(render.com 비교 페이지의 Render 한도 등)는 소유자 발행으로 보고 B로 두었다.
4. **줄 표시.** 줄마다 그 줄의 인용 등급을 모았다.
   - C 인용이 하나라도 있으면 그 C가 뒷받침하는 주장이 있으므로 ` ⚠️출처부적격`.
   - B(또는 애매) 인용이 하나라도 있으면 그 B만 뒷받침하는 주장이 있으므로 ` ⚠️출처확인필요`. A와 함께 있어도 붙였다. 해당 발행처를 받아들이기로 하면 그 표시는 지우면 된다.
   - 출처 칸이 약어·짧은 이름(`EG`, `RP`, `CM`, `같은 문서`, `free-shared-limitations` 같은 페이지 이름)인 표 행은, 문서 안의 약어 정의나 같은 절에서 앞서 나온 URL로 발행처를 정했다. 다른 절·문서를 가리키는 교차 참조(`2.1 출처`, `§6.1`, `05 문서`)는 참조 대상의 판정을 따르므로 표시하지 않았다(대상 절에 표시가 있다).
   - 표 행은 마지막 `|` 바로 앞(마지막 칸 끝)에 표시를 넣었다. 마지막 `|` 뒤에 붙이면 마크다운 표에서 보이지 않기 때문이다. 그 밖의 줄은 줄 끝에 붙였다.
   - 고려 요소 카탈로그(considerations/)는 항목마다 출처를 `- **출처:**` 줄 하나에 모아 두므로, 표시도 그 출처 줄에 붙었다. 표시는 그 항목(무엇/왜·신호·처방) 전체에 적용된다고 읽는다.
5. **근거 없는 주장.** 두 가지를 셌다.
   - 명시적 표시: `(추론)`, `추론이다`, `출처 미확인`, `인용 미확인`, `원문 미확인`, `검색 요약`, `일반 원칙`, `일반 지식`, `(평가)` 등이 붙은 줄. 머리말의 표기 설명 줄과 "모델 추론·도메인 추론" 같은 다른 뜻의 "추론"은 뺐다.
   - capabilities 표에서 출처 칸이 비어 있거나 `—`인데 값 칸이 사실을 말하는 행(값이 `미확인`·`해당 없음`이거나 다른 절을 가리키는 행은 제외).
   - dimensions.md와 capabilities/README.md는 전부 읽고 출처 없는 사실 서술을 직접 골랐다.
   - "값을 모른다"는 뜻의 `미확인`(정직한 공백)은 표시하지 않고 파일별로 줄 수만 셌다.
6. **지식 베이스.** defaults.yaml 16개 값과 catalog 52개 항목의 근거 절을 찾아, 그 절의 인용 등급과 표시 수를 셌다. 시그니처·이미지 파일은 출처 필드가 없어 연결된 카탈로그 항목의 판정을 따른다.
7. **최종 재판정(2026-10-02).** 이전 분류 결과(인용 4,377건, 발행처 이름 포함)를 그대로 다시 읽어 발행처마다 최종 규칙의 기준을 매겼다(§5.1·§5.2). 이전 A 발행처도 다섯 기준으로 다시 검사했고, nginx·Grafana·Stripe는 어느 기준에도 들지 않아 C로 내렸다(§5.3). 그다음 ` ⚠️출처확인필요` 줄 670개를 다시 표시했다: B 인용이 모두 A가 된 줄 165개는 표시를 지우고, C가 된 인용만 남은 줄 442개(이전 A가 Stripe뿐인 줄 포함)는 ` ⚠️출처부적격`으로 바꾸고, A와 C가 섞인 63줄은 하나씩 읽어 정했다(표시 지움 49, ⚠️출처부적격 14, §5.4). 이전 A 중 C로 내린 세 발행처에만 기대던 34줄에는 ` ⚠️출처부적격`을 붙였다(4줄은 이미 붙어 있었음). 표시 말고 조사 문서의 글자는 바꾸지 않았다.

**한계.** A로 분류한 3,420건 중 위 3번의 검사 대상(291줄 + 문맥 검토 대상)이 아닌 인용은 URL 경로가 그 공급사 제품 문서인지까지만 확인했고, 주장 문장을 하나씩 읽지는 않았다. 고려 요소 카탈로그의 근거 없는 주장은 명시적 표시만 셌다(항목 출처 줄이 있는 항목의 개별 문장이 그 출처에 실제로 있는지는 확인하지 않았다).

## 3. 집계

### 3.1 URL 언급 등급 (최종)

| 등급 | 뜻 | 건수 | 이전 감사 |
|---|---|---|---|
| A | 최종 규칙 충족 (§1) | 3,529 | A 3,420 |
| C | 허용 안 함 (§4, §5.2, §5.3) | 763 | C 107 |
| 출처 아님 | 예시 호스트, 자리표시자(`<도메인>` 등), localhost, 예시로 쓴 API 엔드포인트(`checkip.amazonaws.com`, OIDC 발급자 URL 등), 코드 블록 안 URL | 85 | 85 |
| 합계 | | 4,377 | B 761, 애매 4 포함 |

이전 B 761건 중 168건이 A, 593건이 C가 됐다. 애매 4건은 C, 이전 A 중 59건(nginx 13, Grafana 17, Stripe 29)이 C가 됐다.

### 3.2 파일별 (최종)

| 파일 | A | C | 출처 아님 | ⚠️출처부적격 줄 | ⚠️근거없음 줄 | `미확인` 포함 줄(값 공백, 표시 안 함) |
|---|---|---|---|---|---|---|
| dimensions.md | 0 | 0 | 0 | 0 | 5 | 0 |
| capabilities/01-sql-databases.md | 179 | 80 | 0 | 73 | 26 | 73 |
| capabilities/02-nosql-baas.md | 192 | 60 | 0 | 53 | 27 | 71 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md | 239 | 61 | 2 | 63 | 47 | 151 |
| capabilities/04-compute-tier0.md | 387 | 136 | 0 | 116 | 78 | 184 |
| capabilities/05-compute-tier1-2.md | 343 | 6 | 1 | 5 | 85 | 85 |
| capabilities/06-artifacts-datastores.md | 72 | 49 | 3 | 20 | 1 | 60 |
| capabilities/07-artifacts-services.md | 120 | 41 | 8 | 14 | 2 | 71 |
| capabilities/08-artifacts-compute.md | 213 | 50 | 14 | 33 | 49 | 101 |
| capabilities/09-network-lb-ingress.md | 237 | 34 | 4 | 41 | 96 | 162 |
| capabilities/10-network-edge-egress.md | 568 | 39 | 41 | 28 | 125 | 160 |
| capabilities/README.md | 0 | 0 | 1 | 0 | 1 | 2 |
| considerations/01-resilience-dr.md | 147 | 2 | 1 | 2 | 23 | 23 |
| considerations/02-traffic-compute.md | 147 | 25 | 0 | 15 | 9 | 8 |
| considerations/03-deploy-release.md | 115 | 40 | 2 | 31 | 41 | 43 |
| considerations/04-data-consistency.md | 100 | 67 | 0 | 35 | 18 | 19 |
| considerations/05-security-compliance.md | 133 | 12 | 6 | 9 | 21 | 31 |
| considerations/06-cost.md | 101 | 3 | 2 | 3 | 23 | 27 |
| considerations/07-observability-verification.md | 105 | 30 | 0 | 25 | 46 | 36 |
| considerations/08-workloads-platforms.md | 129 | 27 | 0 | 16 | 13 | 20 |
| considerations/README.md | 2 | 1 | 0 | 1 | 0 | 3 |
| **합계** | 3529 | 763 | 85 | 583 | 736 | 1330 |

표시를 붙인 줄은 ⚠️출처부적격 583줄, ⚠️근거없음 736줄이다(한 줄에 둘 다 붙은 경우가 있다). ⚠️출처확인필요는 0줄이다.

## 4. 허용 안 함(C) 인용

| 파일:줄 | URL | 주장 (100자 이내) | 이유 |
|---|---|---|---|
| capabilities/01-sql-databases.md:70 | https://docs.djangoproject.com/en/stable/ref/databases/ | SQLite에는 SELECT … FOR UPDATE 문법이 없다 | 주제 불일치: Django 문서로 SQLite 문법(FOR UPDATE 미지원)을 서술 — SQLite의 소유자가 아님 |
| capabilities/04-compute-tier0.md:274 | https://answers.netlify.com/t/does-netlify-support-websocket-proxying/11230 | 2.1 Netlify Functions — Free · — CP.long_connection: 공식 문서 `미확인`. 포럼 직원 답변(2020)은 웹소켓 프록시 미지원 | answers.netlify.com (커뮤니티 포럼) |
| capabilities/04-compute-tier0.md:315 | https://answers.netlify.com/t/does-netlify-support-websocket-proxying/11230 | 2.2 Netlify Functions — Pro · — CP.long_connection: 공식 `미확인` | answers.netlify.com (커뮤니티 포럼) |
| capabilities/04-compute-tier0.md:1132 | https://www.koyeb.com/docs/reference/regions | 리전: FRA, WAS, SIN, TYO, PAR, aws-us-east-1, SFO(프리뷰). 서울 없음. Free는 FRA·WAS만, Eco는 WAS·FRA·SIN만. | Koyeb (사용자 지정 부적격 출처) |
| capabilities/04-compute-tier0.md:1140 | https://www.koyeb.com/docs/reference/instances | 12.1 Koyeb — Free 인스턴스 — CP.process_types: 웹 서비스만(Worker 불가). 기본 크론 `미확인` | Koyeb (사용자 지정 부적격 출처) |
| capabilities/04-compute-tier0.md:1141 | https://www.koyeb.com/docs/reference/edge-network | 12.1 Koyeb — Free 인스턴스 — CP.request_timeout: HTTP 100초 | Koyeb (사용자 지정 부적격 출처) |
| capabilities/04-compute-tier0.md:1142 | https://www.koyeb.com/docs/reference/edge-network | 12.1 Koyeb — Free 인스턴스 — CP.long_connection: 웹소켓·gRPC 최대 12시간(클라이언트 keep-alive 필요) | Koyeb (사용자 지정 부적격 출처) |
| capabilities/04-compute-tier0.md:1143 | https://www.koyeb.com/docs/run-and-scale/scale-to-zero | 12.1 Koyeb — Free 인스턴스 — CP.cpu_outside_request: 실행 중엔 가능, 1시간 유휴 시 잠듦 | Koyeb (사용자 지정 부적격 출처) |
| capabilities/04-compute-tier0.md:1144 | https://www.koyeb.com/docs/run-and-scale/scale-to-zero | 12.1 Koyeb — Free 인스턴스 — CP.cold_start: 1시간 유휴 후 잠듦, 깨어나는 데 1~5초 | Koyeb (사용자 지정 부적격 출처) |
| capabilities/04-compute-tier0.md:1145 | https://www.koyeb.com/docs/reference/instances | 12.1 Koyeb — Free 인스턴스 — CP.instance_size: 512MB RAM, 0.1 vCPU, SSD 2GB | Koyeb (사용자 지정 부적격 출처) |
| capabilities/04-compute-tier0.md:1147 | https://www.koyeb.com/docs/reference/instances | 12.1 Koyeb — Free 인스턴스 — CP.local_disk: 영속 여부 `미확인`, 볼륨 불가 | Koyeb (사용자 지정 부적격 출처) |
| capabilities/04-compute-tier0.md:1148 | https://www.koyeb.com/docs/reference/instances | 12.1 Koyeb — Free 인스턴스 — CP.scaling: 사용자 지정 스케일링 불가 | Koyeb (사용자 지정 부적격 출처) |
| capabilities/04-compute-tier0.md:1150 | https://www.koyeb.com/docs/reference/instances | 12.1 Koyeb — Free 인스턴스 — CP.shutdown: SIGTERM 후 30초, SIGKILL | Koyeb (사용자 지정 부적격 출처) |
| capabilities/04-compute-tier0.md:1151 | https://www.koyeb.com/docs/reference/deployments | 12.1 Koyeb — Free 인스턴스 — CP.deploy: 새 배포가 정상이면 이전 배포 중지, 헬스체크 실패 시 이전 배포 유지 | Koyeb (사용자 지정 부적격 출처) |
| capabilities/04-compute-tier0.md:1151 | https://www.koyeb.com/docs/run-and-scale/health-checks | 12.1 Koyeb — Free 인스턴스 — CP.deploy: 새 배포가 정상이면 이전 배포 중지, 헬스체크 실패 시 이전 배포 유지 | Koyeb (사용자 지정 부적격 출처) |
| capabilities/04-compute-tier0.md:1152 | https://www.koyeb.com/docs/reference/instances | 12.1 Koyeb — Free 인스턴스 — CP.availability: 인스턴스 1개 | Koyeb (사용자 지정 부적격 출처) |
| capabilities/04-compute-tier0.md:1154 | https://www.koyeb.com/docs/reference/regions | 12.1 Koyeb — Free 인스턴스 — CP.regions: FRA·WAS만 | Koyeb (사용자 지정 부적격 출처) |
| capabilities/04-compute-tier0.md:1155 | https://www.koyeb.com/docs/reference/instances | 12.1 Koyeb — Free 인스턴스 — CP.plan_limits: 조직당 Free 인스턴스 1개, Worker·볼륨·사용자 지정 스케일링 불가 | Koyeb (사용자 지정 부적격 출처) |
| capabilities/04-compute-tier0.md:1157 | https://www.koyeb.com/pricing | 12.1 Koyeb — Free 인스턴스 — CP.cost_floor: $0 | Koyeb (사용자 지정 부적격 출처) |
| capabilities/04-compute-tier0.md:1174 | https://www.koyeb.com/docs/reference/services | 12.2 Koyeb — 유료 인스턴스 — CP.process_types: Web Service, Worker. 기본 크론 `미확인` | Koyeb (사용자 지정 부적격 출처) |
| capabilities/04-compute-tier0.md:1175 | https://www.koyeb.com/docs/reference/edge-network | 12.2 Koyeb — 유료 인스턴스 — CP.request_timeout: 100초 | Koyeb (사용자 지정 부적격 출처) |
| capabilities/04-compute-tier0.md:1176 | https://www.koyeb.com/docs/reference/edge-network | 12.2 Koyeb — 유료 인스턴스 — CP.long_connection: 최대 12시간 | Koyeb (사용자 지정 부적격 출처) |
| capabilities/04-compute-tier0.md:1177 | https://www.koyeb.com/docs/run-and-scale/scale-to-zero | 12.2 Koyeb — 유료 인스턴스 — CP.cpu_outside_request: 가능(scale-to-zero 끄면) | Koyeb (사용자 지정 부적격 출처) |
| capabilities/04-compute-tier0.md:1178 | https://www.koyeb.com/docs/run-and-scale/scale-to-zero | 12.2 Koyeb — 유료 인스턴스 — CP.cold_start: scale-to-zero 프리뷰: 기본 5분 유휴(유료는 6~12시간까지), 깨어나는 데 1~5초, Light  | Koyeb (사용자 지정 부적격 출처) |
| capabilities/04-compute-tier0.md:1179 | https://www.koyeb.com/docs/reference/instances | 12.2 Koyeb — 유료 인스턴스 — CP.instance_size: nano(0.25 vCPU/256MB) ~ 5xlarge(40 vCPU/128GB). GPU 있음(도쿄 G | Koyeb (사용자 지정 부적격 출처) |
| capabilities/04-compute-tier0.md:1181 | https://www.koyeb.com/docs/reference/volumes | 12.2 Koyeb — 유료 인스턴스 — CP.local_disk: 볼륨 프리뷰: 서비스 스케일 1에서만, 1~10GB, 워싱턴·프랑크푸르트만, 재배포 시 다운타임, 이중화 없음, | Koyeb (사용자 지정 부적격 출처) |
| capabilities/04-compute-tier0.md:1182 | https://www.koyeb.com/docs/run-and-scale/autoscaling | 12.2 Koyeb — 유료 인스턴스 — CP.scaling: CPU·메모리·초당 요청·동시 연결·P95 지연 기반 오토스케일. 늘릴 땐 한 번에, 줄일 땐 분당 약 1개 | Koyeb (사용자 지정 부적격 출처) |
| capabilities/04-compute-tier0.md:1184 | https://www.koyeb.com/docs/reference/instances | 12.2 Koyeb — 유료 인스턴스 — CP.shutdown: SIGTERM 후 30초 | Koyeb (사용자 지정 부적격 출처) |
| capabilities/04-compute-tier0.md:1185 | https://www.koyeb.com/docs/reference/deployments | 12.2 Koyeb — 유료 인스턴스 — CP.deploy: 헬스체크 통과 후 전환, 실패 시 이전 유지 | Koyeb (사용자 지정 부적격 출처) |
| capabilities/04-compute-tier0.md:1188 | https://www.koyeb.com/docs/reference/regions | 12.2 Koyeb — 유료 인스턴스 — CP.regions: 도쿄·싱가포르 있음, 서울 없음 | Koyeb (사용자 지정 부적격 출처) |
| capabilities/04-compute-tier0.md:1189 | https://www.koyeb.com/pricing | 12.2 Koyeb — 유료 인스턴스 — CP.plan_limits: Pro 월 $29(컴퓨트 $10 포함), Scale 월 $299 | Koyeb (사용자 지정 부적격 출처) |
| capabilities/04-compute-tier0.md:1191 | https://www.koyeb.com/docs/reference/instances | 12.2 Koyeb — 유료 인스턴스 — CP.cost_floor: Eco nano 월 $1.61, Standard micro 월 $5.36 | Koyeb (사용자 지정 부적격 출처) |
| capabilities/08-artifacts-compute.md:106 | https://12factor.net/config | 1.1.1 모든 런타임 공통 규칙 — D14: 비밀 값을 `ENV`/`ARG`에 넣지 않는다. 런타임 환경변수나 비밀 저장소로 주입한다 | 12factor.net (사용자 지정 부적격 출처, 커뮤니티 선언문) |
| capabilities/08-artifacts-compute.md:107 | https://12factor.net/logs | 1.1.1 모든 런타임 공통 규칙 — D15: 로그는 stdout/stderr로, 버퍼링 없이 | 12factor.net (사용자 지정 부적격 출처, 커뮤니티 선언문) |
| capabilities/08-artifacts-compute.md:309 | https://12factor.net/config | 1.3.3 설정의 환경변수화 | 12factor.net (사용자 지정 부적격 출처, 커뮤니티 선언문) |
| capabilities/08-artifacts-compute.md:315 | https://12factor.net/logs | 1.3.4 stdout 로그 | 12factor.net (사용자 지정 부적격 출처, 커뮤니티 선언문) |
| capabilities/08-artifacts-compute.md:914 | https://www.koyeb.com/docs/build-and-deploy/cli/reference | P17. Koyeb | Koyeb (사용자 지정 부적격 출처) |
| capabilities/08-artifacts-compute.md:914 | https://www.koyeb.com/docs/integrations/infrastructure-as-code/terraform | P17. Koyeb | Koyeb (사용자 지정 부적격 출처) |
| capabilities/08-artifacts-compute.md:914 | https://www.koyeb.com/docs/run-and-scale/health-checks | P17. Koyeb | Koyeb (사용자 지정 부적격 출처) |
| capabilities/08-artifacts-compute.md:914 | https://www.koyeb.com/docs/reference/instances | P17. Koyeb | Koyeb (사용자 지정 부적격 출처) |
| capabilities/08-artifacts-compute.md:914 | https://github.com/koyeb/action-git-deploy | P17. Koyeb | Koyeb (사용자 지정 부적격 출처) |
| capabilities/08-artifacts-compute.md:914 | https://registry.terraform.io/providers/koyeb/koyeb/latest | P17. Koyeb | Koyeb (사용자 지정 부적격 출처) |
| capabilities/09-network-lb-ingress.md:1091 | https://nextjs.org/docs/app/guides/self-hosting | SSE는 proxy_buffering off 또는 X-Accel-Buffering: no | 주제 불일치: Next.js 문서로 nginx 버퍼링 동작(X-Accel-Buffering)을 서술 — nginx 소유자가 아님 |
| capabilities/10-network-edge-egress.md:131 | https://github.com/hashicorp/terraform-provider-aws/blob/main/website/docs/r/cloudfront… | [충돌] CloudFront keep-alive "upper limit of 60" | 주제 불일치: provider 문서로 CloudFront 한도를 서술 — AWS 문서 아님 |
| capabilities/10-network-edge-egress.md:499 | https://github.com/hashicorp/terraform-provider-aws/blob/main/website/docs/r/route53_re… | Route 53 API는 계정당 초당 5요청 제한 | 주제 불일치: Terraform provider 문서로 Route 53 API 한도를 서술 — Route 53의 소유자(AWS)가 아님 |
| capabilities/10-network-edge-egress.md:506 | https://github.com/hashicorp/terraform-provider-aws/blob/main/website/docs/r/route53_he… | Route 53 헬스 체커 리전 8개, 서울 없음 | 주제 불일치: provider 인자 허용값으로 Route 53 헬스 체커 리전을 서술 — AWS 문서 아님 |
| considerations/02-traffic-compute.md:31 | https://12factor.net/processes | T-001 프로세스 무상태: 인메모리 세션 금지 | 12factor.net (사용자 지정 부적격 출처, 커뮤니티 선언문) |
| considerations/02-traffic-compute.md:41 | https://12factor.net/processes | T-002 로컬 디스크 업로드·파일 상태 금지 | 12factor.net (사용자 지정 부적격 출처, 커뮤니티 선언문) |
| considerations/02-traffic-compute.md:51 | https://12factor.net/processes | T-003 인스턴스별 인메모리 카운터·캐시의 확장 왜곡 | 12factor.net (사용자 지정 부적격 출처, 커뮤니티 선언문) |
| considerations/02-traffic-compute.md:91 | https://12factor.net/concurrency | T-007 프로세스 타입 분리(web / worker / scheduler) | 12factor.net (사용자 지정 부적격 출처, 커뮤니티 선언문) |
| considerations/02-traffic-compute.md:101 | https://12factor.net/concurrency | T-008 인프로세스 스케줄러의 중복 실행 | 12factor.net (사용자 지정 부적격 출처, 커뮤니티 선언문) |
| considerations/02-traffic-compute.md:467 | https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing | DB 활성 연결 ≈ (코어×2)+디스크 수, 풀 축소 사례 | 주제 불일치: 커넥션 풀 라이브러리 위키로 DB 일반의 적정 동시 연결 수를 서술 — DB의 소유자가 아님 |
| considerations/02-traffic-compute.md:507 | https://supabase.com/docs/guides/database/postgres/row-level-security | 정책이 거르는 열마다 인덱스, select 래핑으로 initPlan 캐시 | 주제 불일치: Supabase 문서로 PostgreSQL RLS 성능(인덱스·initPlan)을 서술 |
| considerations/02-traffic-compute.md:671 | https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching | T-063 정적 자산: 해시 파일명 + immutable + CDN | MDN (Mozilla) — HTTP·ECMAScript 표준의 소유자가 아님 |
| considerations/02-traffic-compute.md:701 | https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching | T-066 캐시 키 폭발(고카디널리티 Vary·쿼리스트링) | MDN (Mozilla) — HTTP·ECMAScript 표준의 소유자가 아님 |
| considerations/02-traffic-compute.md:751 | https://nextjs.org/docs/app/guides/self-hosting | nginx 기본 버퍼링이 스트리밍을 막음, X-Accel-Buffering: no | 주제 불일치: Next.js 문서로 nginx·LB 버퍼링 동작을 서술 |
| considerations/02-traffic-compute.md:805 | https://12factor.net/concurrency | T-076 무거운 작업 격리(비밀번호 해시·이미지·PDF·LLM 후처리) | 12factor.net (사용자 지정 부적격 출처, 커뮤니티 선언문) |
| considerations/02-traffic-compute.md:939 | https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/429 | T-089 레이트 리밋(사용자 기준 + IP 기준) | MDN (Mozilla) — HTTP·ECMAScript 표준의 소유자가 아님 |
| considerations/02-traffic-compute.md:1019 | https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/429 | T-097 429/503 응답과 Retry-After 계약 | MDN (Mozilla) — HTTP·ECMAScript 표준의 소유자가 아님 |
| considerations/03-deploy-release.md:116 | https://martinfowler.com/bliki/BlueGreenDeployment.html | U-009 블루그린 배포의 적용 조건 | martinfowler.com (개인 사이트) |
| considerations/03-deploy-release.md:126 | https://martinfowler.com/bliki/CanaryRelease.html | U-010 카나리 배포 (일부 트래픽 먼저) | martinfowler.com (개인 사이트) |
| considerations/03-deploy-release.md:210 | https://12factor.net/disposability | U-018 기동 시간 자체를 줄인다 | 12factor.net (사용자 지정 부적격 출처, 커뮤니티 선언문) |
| considerations/03-deploy-release.md:220 | https://12factor.net/build-release-run | U-019 기동 명령에 빌드·설치·마이그레이션을 넣지 않는다 | 12factor.net (사용자 지정 부적격 출처, 커뮤니티 선언문) |
| considerations/03-deploy-release.md:254 | https://12factor.net/disposability | U-022 SIGTERM을 받으면 새 요청을 멈추고 진행 중인 요청을 마친다 | 12factor.net (사용자 지정 부적격 출처, 커뮤니티 선언문) |
| considerations/03-deploy-release.md:324 | https://12factor.net/disposability | U-029 긴 요청(업로드, 보고서, LLM 스트리밍)과 유예 시간 | 12factor.net (사용자 지정 부적격 출처, 커뮤니티 선언문) |
| considerations/03-deploy-release.md:398 | https://martinfowler.com/bliki/ParallelChange.html | U-036 롤백이 실제로 가능한 상태인가 (스키마·설정·외부 상태) | martinfowler.com (개인 사이트) |
| considerations/03-deploy-release.md:438 | https://martinfowler.com/articles/feature-toggles.html | U-040 피처 플래그로 배포와 릴리스를 분리 + 킬 스위치 | martinfowler.com (개인 사이트) |
| considerations/03-deploy-release.md:448 | https://martinfowler.com/articles/feature-toggles.html | U-041 피처 플래그 부채 | martinfowler.com (개인 사이트) |
| considerations/03-deploy-release.md:482 | https://martinfowler.com/bliki/ParallelChange.html | U-044 파괴적 스키마 변경은 expand → migrate → contract로 나눈다 | martinfowler.com (개인 사이트) |
| considerations/03-deploy-release.md:502 | https://12factor.net/admin-processes | U-046 마이그레이션 실행 위치: 앱 기동이 아니라 별도 단계 | 12factor.net (사용자 지정 부적격 출처, 커뮤니티 선언문) |
| considerations/03-deploy-release.md:602 | https://martinfowler.com/bliki/ParallelChange.html | U-056 다운 마이그레이션 대신 전진 수정(forward fix) 전략 | martinfowler.com (개인 사이트) |
| considerations/03-deploy-release.md:656 | https://martinfowler.com/bliki/ParallelChange.html | U-061 API는 직전 버전(N-1)과 동시에 돌 수 있어야 한다 | martinfowler.com (개인 사이트) |
| considerations/03-deploy-release.md:706 | https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control | U-066 HTML은 재검증, 해시 자산은 immutable | MDN (Mozilla) — HTTP·ECMAScript 표준의 소유자가 아님 |
| considerations/03-deploy-release.md:790 | https://12factor.net/disposability | U-074 워커가 SIGTERM에 진행 중 작업을 마치거나 큐에 돌려준다 | 12factor.net (사용자 지정 부적격 출처, 커뮤니티 선언문) |
| considerations/03-deploy-release.md:840 | https://martinfowler.com/bliki/ParallelChange.html | U-079 장시간 배치·Job이 배포를 가로지를 때 | martinfowler.com (개인 사이트) |
| considerations/03-deploy-release.md:894 | https://12factor.net/build-release-run | U-084 한 번 빌드해서 환경을 따라 승격한다 (빌드 시 인라인 설정 주의) | 12factor.net (사용자 지정 부적격 출처, 커뮤니티 선언문) |
| considerations/03-deploy-release.md:904 | https://12factor.net/dependencies | U-085 lock 파일과 고정된 설치 (재현 가능한 빌드) | 12factor.net (사용자 지정 부적격 출처, 커뮤니티 선언문) |
| considerations/03-deploy-release.md:998 | https://12factor.net/config | U-094 설정 외부화 (12-Factor III) | 12factor.net (사용자 지정 부적격 출처, 커뮤니티 선언문) |
| considerations/03-deploy-release.md:1008 | https://12factor.net/config | U-095 저장소에 커밋된 `.env`·하드코딩 비밀 | 12factor.net (사용자 지정 부적격 출처, 커뮤니티 선언문) |
| considerations/03-deploy-release.md:1102 | https://12factor.net/config | U-104 dev/staging/prod 분리 (데이터·자격 증명까지) | 12factor.net (사용자 지정 부적격 출처, 커뮤니티 선언문) |
| considerations/03-deploy-release.md:1142 | https://12factor.net/dev-prod-parity | U-108 개발·운영 백엔드 서비스 동일성 (dev/prod parity) | 12factor.net (사용자 지정 부적격 출처, 커뮤니티 선언문) |
| considerations/04-data-consistency.md:122 | https://microservices.io/patterns/data/transactional-outbox.html | C-009 트랜잭션 안의 외부 호출 | microservices.io (개인 사이트) |
| considerations/04-data-consistency.md:256 | https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number… | C-022 큰 정수 ID·금액의 JavaScript 정밀도 | MDN (Mozilla) — HTTP·ECMAScript 표준의 소유자가 아님 |
| considerations/04-data-consistency.md:554 | https://microservices.io/patterns/data/event-sourcing.html | C-051 원장(ledger)은 덧붙이기만 | microservices.io (개인 사이트) |
| considerations/04-data-consistency.md:578 | https://microservices.io/patterns/communication-style/idempotent-consumer.html | C-053 웹훅 이벤트 중복 제거 | microservices.io (개인 사이트) |
| considerations/04-data-consistency.md:632 | https://microservices.io/patterns/communication-style/idempotent-consumer.html | C-058 at-least-once 소비자의 멱등성 | microservices.io (개인 사이트) |
| considerations/04-data-consistency.md:776 | https://microservices.io/patterns/data/transactional-outbox.html | C-072 이중 쓰기(DB + 큐·캐시·검색·메일) | microservices.io (개인 사이트) |
| considerations/04-data-consistency.md:786 | https://microservices.io/patterns/data/transactional-outbox.html | C-073 트랜잭셔널 아웃박스 | microservices.io (개인 사이트) |
| considerations/04-data-consistency.md:816 | https://microservices.io/patterns/data/saga.html | C-076 사가와 보상 트랜잭션 | microservices.io (개인 사이트) |
| considerations/04-data-consistency.md:826 | https://microservices.io/patterns/data/saga.html | C-077 사가의 격리 부재 대응 | microservices.io (개인 사이트) |
| considerations/04-data-consistency.md:968 | https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html | C-090 펜싱 토큰 | martin.kleppmann.com (개인 블로그) |
| considerations/04-data-consistency.md:1042 | https://supabase.com/docs/guides/database/postgres/row-level-security | USING vs WITH CHECK, UPDATE는 둘 다 적용 | 주제 불일치: Supabase 문서로 PostgreSQL RLS 의미론(USING/WITH CHECK)을 서술 — PostgreSQL 소유자가 아님 |
| considerations/04-data-consistency.md:1092 | https://supabase.com/docs/guides/database/postgres/row-level-security | 뷰는 기본적으로 RLS를 우회, security_invoker = true | 주제 불일치: Supabase 문서로 PostgreSQL 뷰의 RLS 우회 동작을 서술 |
| considerations/04-data-consistency.md:1190 | https://microservices.io/patterns/data/event-sourcing.html | C-111 감사 로그 | microservices.io (개인 사이트) |
| considerations/04-data-consistency.md:1210 | https://microservices.io/patterns/data/event-sourcing.html | C-113 이벤트 소싱 채택 여부(과잉 판정 포함) | microservices.io (개인 사이트) |
| considerations/05-security-compliance.md:551 | https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS | S-049 CORS 오설정 (임의 Origin 반사 + credentials) | MDN (Mozilla) — HTTP·ECMAScript 표준의 소유자가 아님 |
| considerations/05-security-compliance.md:1001 | https://gdpr-info.eu/art-33-gdpr/ | S-092 개인정보 유출 신고 72시간 체계 | gdpr-info.eu (비공식 법령 미러) |
| considerations/05-security-compliance.md:1041 | https://zdnet.co.kr/view/?no=20260420130424 | S-096 공공기관 납품: CSAP → 국정원 클라우드 보안검증 전환 | zdnet.co.kr (언론 보도) |
| considerations/05-security-compliance.md:1061 | https://gdpr-info.eu/art-3-gdpr/ | S-098 GDPR 적용 (EU 사용자 대상) | gdpr-info.eu (비공식 법령 미러) |
| considerations/07-observability-verification.md:46 | https://12factor.net/logs | O-001 로그를 stdout으로 내보내기 | 12factor.net (사용자 지정 부적격 출처, 커뮤니티 선언문) |
| considerations/07-observability-verification.md:188 | https://www.brendangregg.com/usemethod.html | O-015 USE 자원 지표(사용률·포화·오류) | brendangregg.com (개인 사이트) |
| considerations/07-observability-verification.md:1052 | https://principlesofchaos.org/ | V-027 정상 상태(steady state) 정의 | principlesofchaos.org (커뮤니티 선언문) |
| considerations/07-observability-verification.md:1062 | https://principlesofchaos.org/ | V-028 가설과 통과 기준 | principlesofchaos.org (커뮤니티 선언문) |
| considerations/07-observability-verification.md:1072 | https://principlesofchaos.org/ | V-029 블래스트 반경 제한 | principlesofchaos.org (커뮤니티 선언문) |
| considerations/07-observability-verification.md:1092 | https://principlesofchaos.org/ | V-031 대조군 비교 | principlesofchaos.org (커뮤니티 선언문) |
| considerations/08-workloads-platforms.md:107 | https://nextjs.org/docs/app/guides/self-hosting | nginx는 X-Accel-Buffering: no, LB·프록시가 청크 응답을 버퍼링하지 않아야 함 | 주제 불일치: Next.js 문서로 nginx·LB 버퍼링 동작을 서술 |
| considerations/08-workloads-platforms.md:394 | https://martinfowler.com/bliki/ParallelChange.html | W-030 모바일 백엔드: 구버전 앱 호환 | martinfowler.com (개인 사이트) |

합계 107건. 이 인용만 기대는 줄에는 ` ⚠️출처부적격`을 붙였다. 이 표는 처음 감사의 C 판정이다. 최종 규칙으로 C가 된 발행처는 §5.2·§5.3에 발행처 단위로 적었다(인용 단위 목록은 싣지 않는다).

## 5. 최종 발행처 판정 (이전 B·애매·이전 A 재검사)

이전 감사의 B 발행처 109곳과 애매 4건을 최종 규칙(§1)으로 판정했다. A로 올린 발행처의 인용만 남은 줄은 표시를 지웠고, C로 내린 발행처에만 기대는 줄은 ` ⚠️출처부적격`으로 바꿨다. 둘이 섞인 줄은 §5.4 규칙으로 정했다. 언급 수는 URL 언급(약어로 가리킨 행 제외) 기준이다.

### 5.1 A로 올림 (최종 규칙 충족)

| 발행처 | 언급: capabilities | 언급: considerations | 충족 기준 |
|---|---|---|---|
| Railway | 66 | 6 | SO 2025 (Railway) |
| PocketBase | 18 | 0 | SO 2025 (PocketBase) |
| Express | 5 | 6 | SO 2025 (Express) |
| Chaos Mesh | 0 | 9 | CNCF incubating |
| KEDA | 3 | 5 | CNCF graduated |
| Karpenter | 3 | 5 | 쿠버네티스 공식 하위 프로젝트(kubernetes-sigs) |
| uvicorn | 3 | 4 | FastAPI 공식 문서가 실행 서버로 제시 |
| cert-manager | 3 | 2 | CNCF graduated |
| Valkey | 3 | 0 | SO 2025 (Valkey) |
| Apache Kafka | 2 | 1 | Apache 최상위 프로젝트 (SO 2025 목록 밖, ASF로 충족) |
| npm | 1 | 2 | SO 2025 (npm) |
| gunicorn | 3 | 0 | Flask·Django 공식 문서가 배포 서버로 제시 |
| Envoy / Envoy Gateway | 3 | 0 | CNCF graduated (Envoy) |
| Argo CD | 0 | 3 | CNCF graduated (Argo) |
| Go | 1 | 1 | 프로그래밍 언어 공식 사이트 |
| Argo Rollouts | 0 | 2 | CNCF graduated (Argo) |
| Ruby on Rails | 1 | 0 | SO 2025 (Ruby on Rails) |
| Apache Tomcat | 1 | 0 | Apache 최상위 프로젝트 |
| Bun | 1 | 0 | SO 2025 (Bun) |
| Deno | 1 | 0 | SO 2025 (Deno) |
| pip (PyPA) | 0 | 1 | SO 2025 (Pip) |
| OPA Gatekeeper | 0 | 1 | CNCF graduated (OPA 하위 프로젝트, 사용자 검증 목록 밖) |
| Elastic | 0 | 1 | SO 2025 (Elasticsearch) |
| Istio | 0 | 1 | CNCF graduated (사용자 검증 목록 밖, 감사자 확인) |

24곳, 언급 168건. Istio와 OPA Gatekeeper는 사용자가 준 검증 목록에는 없지만 CNCF 졸업 프로젝트(Istio 2023, OPA 2021)라서 기준 2로 올렸다. 웹을 열지 않고 감사자가 아는 사실로 판단했으므로, 받아들이지 않으면 두 줄(considerations/03:1226, considerations/07:1326)을 ` ⚠️출처부적격`으로 바꾸면 된다. Envoy Gateway·Argo Rollouts·OPA Gatekeeper는 해당 CNCF 프로젝트 조직의 하위 프로젝트로, Karpenter는 kubernetes-sigs 하위 프로젝트로 셌다.

### 5.2 C로 내림 (최종 규칙 미충족)

| 발행처 | 언급: capabilities | 언급: considerations | 비고 |
|---|---|---|---|
| Render | 58 | 8 | 사용자 지정 |
| Fly.io | 48 | 5 | 사용자 지정 |
| Prisma | 21 | 20 | 사용자 지정 |
| Replit | 38 | 1 | 사용자 지정 |
| Upstash | 28 | 0 | 사용자 지정 |
| Neon | 27 | 0 | 사용자 지정 |
| Appwrite | 23 | 0 | 사용자 지정 |
| Convex | 23 | 0 | 사용자 지정 |
| Checkov | 18 | 1 | Bridgecrew/Palo Alto 제품, SO 2025·CNCF·ASF 아님 |
| PlanetScale | 19 | 0 | 사용자 지정 |
| Pinecone | 17 | 0 | 사용자 지정 |
| Turso | 15 | 0 | 사용자 지정 |
| BullMQ | 11 | 2 | 사용자 지정 |
| Celery | 9 | 4 | 사용자 지정 |
| 토스페이먼츠 | 0 | 12 | SO 2025 목록 밖 |
| k3s | 10 | 0 | 사용자 지정: CNCF 졸업·인큐베이팅 아님 |
| Let's Encrypt | 7 | 2 | 사용자 지정 |
| pgvector | 8 | 1 | PostgreSQL 확장(별도 프로젝트), SO 2025 목록 밖 |
| Inngest | 8 | 0 | 사용자 지정 |
| Socket.IO | 5 | 3 | 사용자 지정 |
| Ably | 7 | 0 | 사용자 지정 |
| Anthropic | 0 | 7 | SO 2025 목록 밖 |
| Fastly | 7 | 0 | SO 2025 목록 밖 |
| Confluent | 6 | 0 | Kafka 상용 공급사(ASF 아님) |
| Sidekiq | 6 | 0 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| Traefik | 6 | 0 | 사용자 지정 |
| Pusher | 5 | 0 | 사용자 지정 |
| node-postgres | 4 | 0 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| Sentry | 0 | 3 | 사용자 지정 |
| Trigger.dev | 3 | 0 | 사용자 지정 |
| Trivy | 0 | 3 | 사용자 지정 |
| asyncpg | 3 | 0 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| celest-dev/turso (단일 관리자, 보관됨) | 3 | 0 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| connect-redis | 3 | 0 | Express 프로젝트가 아닌 별도 저장소(tj/connect-redis) |
| express-rate-limit | 3 | 0 | Express 프로젝트가 아닌 별도 저장소 |
| kubeconform (단일 관리자) | 2 | 1 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| pg-boss (단일 관리자) | 3 | 0 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| psycopg | 3 | 0 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| Bolt | 2 | 0 | 사용자 지정 |
| Caddy | 2 | 0 | 사용자 지정 |
| LocalStack | 2 | 0 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| Lovable | 2 | 0 | 사용자 지정 |
| PgBouncer | 0 | 2 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| Protocol Buffers (Google) | 0 | 2 | Google Cloud 문서가 아님, SO 2025 목록 밖 |
| SLSA (OpenSSF) | 0 | 2 | 표준 기구 출판물로 보지 않음(OpenSSF 프로젝트) |
| SQLAlchemy | 2 | 0 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| Sigstore | 0 | 2 | OpenSSF 프로젝트, CNCF 아님 |
| TanStack Query | 0 | 2 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| better-sqlite3 | 2 | 0 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| cyrilgdn/postgresql (단일 관리자) | 2 | 0 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| kislerdm/neon (단일 관리자, 보관됨) | 2 | 0 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| pgloader | 2 | 0 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| terraform-aws-modules (커뮤니티) | 2 | 0 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| uv (Astral) | 2 | 0 | SO 2025 목록 밖(Pip·Poetry만 있음) |
| APScheduler | 1 | 0 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| Debezium | 0 | 1 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| Drizzle ORM | 1 | 0 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| External Secrets Operator | 0 | 1 | CNCF sandbox(졸업·인큐베이팅 아님) |
| FinOps Foundation | 0 | 1 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| Flask-Caching | 1 | 0 | Flask(pallets) 프로젝트가 아닌 pallets-eco 확장 |
| Google AI Studio/Gemini API | 1 | 0 | Google Cloud 문서가 아님 |
| Google Workspace 도움말 | 0 | 1 | Google Cloud 문서가 아님 |
| Hypercorn | 1 | 0 | FastAPI 문서의 공식 실행 서버(uvicorn)가 아님 |
| MinIO | 1 | 0 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| OpenAI | 0 | 1 | SO 2025 목록 밖 |
| Pact | 0 | 1 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| Puma | 1 | 0 | Rails 문서가 제시하는 서버라는 인용이 조사 문서에 없음 |
| PyMySQL | 1 | 0 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| Sequelize | 1 | 0 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| Squarespace | 1 | 0 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| Standard Webhooks | 0 | 1 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| TypeORM | 1 | 0 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| aiosqlite | 1 | 0 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| distroless (Google) | 1 | 0 | Google Cloud 문서가 아닌 GoogleContainerTools 저장소 |
| django-storages | 1 | 0 | Django 프로젝트가 아닌 jazzband 확장 |
| hadolint | 1 | 0 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| lru-cache (단일 관리자) | 1 | 0 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| mysql2 (node) | 1 | 0 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| node-cron | 1 | 0 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| node-sqlite3 | 1 | 0 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| pg_cron (Citus) | 1 | 0 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| postgres.js | 1 | 0 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| terraform-community-providers/railway (커뮤니티) | 1 | 0 | Railway 자신이 아닌 커뮤니티 provider |
| web-vitals (Google Chrome) | 0 | 1 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| web.dev (Google Chrome) | 0 | 1 | SO 2025·CNCF·ASF·공식 실행 서버 어디에도 해당 없음 |
| web.dev (Google Chrome) (애매) | 0 | 2 | 사용자 결정: 애매 4건은 C |
| builder.aws.com (AWS Builder Center) (애매) | 0 | 2 | 사용자 결정: 애매 4건은 C |

85곳 + 애매 2곳, 언급 597건.

### 5.3 이전 A 중 최종 규칙에 못 미친 발행처

이전 감사는 수정 지시의 A 목록을 그대로 썼다. 최종 규칙은 "다섯 기준 중 하나 이상"을 요구하므로 이전 A 발행처도 다시 검사했다. 아래 셋은 사용자가 준 SO 2025 목록·CNCF·ASF·공식 실행 서버·표준 기구/정부/주요 클라우드/GitHub 어디에도 들지 않는다. 규칙의 문언대로 C로 내렸다. 이 판정은 사용자가 뒤집을 수 있다(특히 nginx: Flask 문서가 리버스 프록시로 소개하지만 기준 4는 "실행 서버"만 다룬다).

| 발행처 | 언급: capabilities | 언급: considerations | 이 발행처(이전 A)에만 기대어 ` ⚠️출처부적격`이 된 줄 (4줄은 다른 C 인용 때문에 이미 표시돼 있었음) |
|---|---|---|---|
| Stripe | 0 | 29 | 12줄: con/04:276, con/04:400, con/04:444, con/04:484, con/04:494, con/04:524, con/04:534, con/04:544, con/04:578, con/04:588, con/05:681, con/08:578 |
| Grafana | 0 | 17 | 14줄: con/07:786, con/07:796, con/07:806, con/07:816, con/07:826, con/07:836, con/07:846, con/07:858, con/07:868, con/07:878, con/07:918, con/07:928, con/07:990, con/07:1010 |
| nginx | 9 | 4 | 8줄: cap/09:1089, cap/09:1090, cap/09:1091, cap/09:1093, cap/09:1097, con/02:51, con/02:939, con/07:156 |

이 세 발행처와 다른 A 출처가 함께 있는 7줄(considerations/04:360·370·380·474·934, considerations/07:1082, considerations/08:405)은 A 출처(AWS·IETF·PostgreSQL·Redis)가 항목의 주된 주장을 뒷받침하므로 표시하지 않았다. 지식 베이스 영향: nginx 기본값 5개를 지웠다(§8.1).

### 5.4 A와 C가 섞인 줄

규칙: 그 줄(표 행이면 그 행의 값, 고려 요소면 그 항목의 무엇/왜, capabilities 절의 출처 줄이면 그 절의 주제)의 주된 주장을 A 인용이 하나라도 뒷받침하면 표시를 지웠다. 주된 주장이 C 발행처의 제품·동작이거나, 한 행에 여러 제품 값을 나란히 적어 C 제품의 값이 그 C 출처에만 기대면 ` ⚠️출처부적격`으로 바꿨다. 표시를 지운 줄에서도 "비고"의 C 세부는 쓸 수 없다.

| 파일:줄 | 결정 | 근거 |
|---|---|---|
| capabilities/03-cache-queue-scheduler-realtime-storage.md:145 | 표시 지움 | express-session 문서(Express)가 프로세스 메모리 저장소의 무한 증가를 말함; lru-cache 세부는 C |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:147 | 표시 지움 | express-session 문서(Express)가 단일 프로세스 한정을 말함; express-rate-limit 세부는 C |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:933 | 표시 지움 | PostgreSQL 문서가 큐 테이블 잠금 패턴을 말함; pg-boss 문구는 C |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:1158 | 표시 지움 | Supabase 문서가 빈도 범위를 말함; pg_cron 문법은 C |
| capabilities/06-artifacts-datastores.md:122 | ⚠️출처부적격 | 행의 주제가 psycopg 3 드라이버(준비문 설정)이고 그 부분은 psycopg 문서뿐 |
| capabilities/06-artifacts-datastores.md:128 | 표시 지움 | Supabase 문서가 트랜잭션 모드의 세션 상태 제약을 말함; Neon 목록은 C |
| capabilities/06-artifacts-datastores.md:211 | 표시 지움 | Terraform·psql 문서가 검증 절차를 뒷받침; Checkov 단계는 C |
| capabilities/07-artifacts-services.md:146 | ⚠️출처부적격 | LocalStack·MinIO 행은 C 출처뿐 |
| capabilities/07-artifacts-services.md:166 | 표시 지움 | Redis·Valkey 이미지 문서가 절의 주제를 뒷받침; BullMQ AOF 권장은 C |
| capabilities/07-artifacts-services.md:193 | 표시 지움 | 주제는 ElastiCache(AWS·Terraform); Celery 연결 문자열은 C |
| capabilities/07-artifacts-services.md:214 | 표시 지움 | 주제는 ElastiCache 서버리스(AWS·Terraform); BullMQ·connect-redis 세부는 C |
| capabilities/07-artifacts-services.md:314 | 표시 지움 | 주제는 Memorystore Cluster(Terraform google); BullMQ·Sidekiq 세부는 C |
| capabilities/07-artifacts-services.md:398 | 표시 지움 | 주제는 SQS(Terraform aws); Celery 설정 세부는 C |
| capabilities/07-artifacts-services.md:588 | ⚠️출처부적격 | 절의 주제가 Celery 설정이고 Celery 문서뿐 |
| capabilities/07-artifacts-services.md:831 | ⚠️출처부적격 | 절의 주제가 Socket.IO Redis 어댑터이고 Socket.IO·connect-redis 문서뿐 |
| capabilities/07-artifacts-services.md:997 | 표시 지움 | 주제는 S3(Terraform aws); django-storages 세부는 C |
| capabilities/08-artifacts-compute.md:95 | 표시 지움 | npm 문서가 lock 기반 재현 빌드를 말함; uv 명령은 C |
| capabilities/08-artifacts-compute.md:211 | ⚠️출처부적격 | distroless(셸 없음)가 핵심 주장이고 distroless 저장소뿐 |
| capabilities/08-artifacts-compute.md:1027 | 표시 지움 | 주제는 Cloud Functions(GCP·Terraform); Checkov ID는 C |
| capabilities/08-artifacts-compute.md:1429 | 표시 지움 | 주제는 EKS Auto Mode(AWS·Terraform); terraform-aws-modules 인용은 C |
| capabilities/08-artifacts-compute.md:1458 | ⚠️출처부적격 | 절의 주제가 k3s이고 k3s 문서뿐 |
| capabilities/08-artifacts-compute.md:1492 | 표시 지움 | 주제는 EC2 위 compose(Docker·Terraform); Caddy 자동 HTTPS는 C |
| capabilities/10-network-edge-egress.md:674 | ⚠️출처부적격 | Squarespace Domains 값은 Squarespace 문서뿐(같은 행의 Route 53·Cloudflare는 A) |
| capabilities/10-network-edge-egress.md:1178 | ⚠️출처부적격 | Let's Encrypt 인증서 수명 일정이 행의 핵심이고 Let's Encrypt 문서뿐 |
| capabilities/10-network-edge-egress.md:2166 | ⚠️출처부적격 | Neon PrivateLink 값은 Neon 문서뿐(같은 행의 Supabase는 A) |
| capabilities/10-network-edge-egress.md:2173 | ⚠️출처부적격 | Neon·PlanetScale·Upstash 값은 각 사 문서뿐(같은 행의 Supabase·MongoDB는 A) |
| capabilities/10-network-edge-egress.md:2175 | ⚠️출처부적격 | Upstash 비용 값은 Upstash 문서뿐(같은 행의 Supabase는 A) |
| considerations/01-resilience-dr.md:924 | ⚠️출처부적격 | 항목 핵심(만료 알림 이메일 중단)이 Let's Encrypt 문서뿐 |
| considerations/02-traffic-compute.md:81 | 표시 지움 | Cloud Run 문서가 인스턴스 간 Pub/Sub 공유를 말함; Socket.IO sticky 세부는 C |
| considerations/02-traffic-compute.md:289 | 표시 지움 | Supabase 문서가 모듈 범위 클라이언트 생성을 말함 |
| considerations/02-traffic-compute.md:447 | 표시 지움 | Supabase·RDS Proxy 문서가 풀링을 말함 |
| considerations/02-traffic-compute.md:457 | 표시 지움 | Supabase·RDS Proxy 문서가 트랜잭션 풀링 제약을 말함 |
| considerations/02-traffic-compute.md:825 | 표시 지움 | sre.google·Cloud Run·Vercel 문서가 타임아웃 설계를 뒷받침 |
| considerations/02-traffic-compute.md:855 | 표시 지움 | sre.google이 재시도 예산·백오프를 말함 |
| considerations/03-deploy-release.md:472 | 표시 지움 | Supabase 문서가 마이그레이션 파일 관리를 말함 |
| considerations/03-deploy-release.md:572 | 표시 지움 | Django 문서가 데이터 마이그레이션을 말함 |
| considerations/03-deploy-release.md:800 | 표시 지움 | ECS 태스크 정의 문서가 종료 유예를 말함; Celery 종료 모드는 C |
| considerations/03-deploy-release.md:1048 | 표시 지움 | Kubernetes 문서가 Secret 평문 저장·외부 저장소 권고를 말함 |
| considerations/03-deploy-release.md:1112 | ⚠️출처부적격 | 핵심 위험(빌드 단계 prisma migrate deploy)이 Prisma 문서뿐 |
| considerations/03-deploy-release.md:1226 | 표시 지움 | Gatekeeper 문서가 어드미션 단계 정책 강제를 말함; Checkov 단계는 C |
| considerations/04-data-consistency.md:42 | 표시 지움 | Django 문서가 autocommit·atomic을 말함; Prisma 8 API는 C |
| considerations/04-data-consistency.md:52 | 표시 지움 | Django·PostgreSQL 문서가 lost update를 말함; Prisma 세부는 C |
| considerations/04-data-consistency.md:92 | 표시 지움 | PostgreSQL 문서가 격리 수준·배타 제약을 말함; Prisma 세부는 C |
| considerations/04-data-consistency.md:102 | 표시 지움 | PostgreSQL 문서가 재시도 필요를 말함; Prisma 세부는 C |
| considerations/04-data-consistency.md:142 | 표시 지움 | Django 문서가 중첩 = savepoint를 말함; Prisma 비중첩은 C |
| considerations/04-data-consistency.md:162 | 표시 지움 | PostgreSQL 문서가 ON CONFLICT 원자성을 말함; Prisma 세부는 C |
| considerations/04-data-consistency.md:236 | 표시 지움 | RFC 9562·PostgreSQL 문서가 UUIDv7을 말함; Prisma 세부는 C |
| considerations/04-data-consistency.md:286 | 표시 지움 | Firestore 문서가 다문서 원자성을 말함; Prisma 세부는 C |
| considerations/04-data-consistency.md:296 | 표시 지움 | MongoDB 문서가 write concern 롤백을 말함; Prisma 세부는 C |
| considerations/04-data-consistency.md:390 | 표시 지움 | DynamoDB·Powertools 문서가 키 보존 기간을 말함; Stripe·토스 값은 C |
| considerations/04-data-consistency.md:434 | 표시 지움 | PostgreSQL 문서가 금액 타입을 말함; Prisma 매핑은 C |
| considerations/04-data-consistency.md:732 | 표시 지움 | Redis 문서가 noeviction·AOF를 말함; BullMQ 권장은 C |
| considerations/04-data-consistency.md:1200 | 표시 지움 | SQS 문서가 보존 기간 설정을 말함; Stripe·토스 값은 C |
| considerations/05-security-compliance.md:67 | 표시 지움 | Docker 문서가 빌드 인자·환경변수 잔존을 말함; Trivy 스캔은 C |
| considerations/05-security-compliance.md:413 | 표시 지움 | cert-manager 문서가 자동 갱신을 말함; Let's Encrypt 수명 단축은 C |
| considerations/07-observability-verification.md:106 | 표시 지움 | OWASP·CloudWatch 문서가 로그 마스킹을 말함; Sentry 세부는 C |
| considerations/08-workloads-platforms.md:63 | 표시 지움 | Cloud Run 문서가 인스턴스 간 동기화를 말함; Socket.IO 문구는 C |
| considerations/08-workloads-platforms.md:74 | ⚠️출처부적격 | 항목 핵심(롱폴링 = 스티키 필요)이 Socket.IO 문서뿐 |
| considerations/08-workloads-platforms.md:85 | 표시 지움 | Vercel 문서가 연결 종료·재연결을 말함; Render 세부는 C |
| considerations/08-workloads-platforms.md:383 | 표시 지움 | RFC 6585가 429·Retry-After를 말함; Anthropic 예시는 C |
| considerations/08-workloads-platforms.md:499 | 표시 지움 | Azure Container Apps 문서가 내부 환경·IP 제한을 말함; Render Free 세부는 C |
| considerations/08-workloads-platforms.md:1108 | 표시 지움 | ECS·Next.js 문서가 종료 유예를 말함; Render 값은 C |
| considerations/08-workloads-platforms.md:1156 | 표시 지움 | Supabase·Railway·Vercel·Firestore 문서가 무료 플랜 동작을 말함; Render Free 값은 C |

63줄: 표시 지움 49, ⚠️출처부적격 14.

## 6. 애매 — 최종 결정

| 파일:줄 | URL | 결정 |
|---|---|---|
| considerations/01-resilience-dr.md:1152 | https://web.dev/articles/offline-cookbook | C (사용자 결정) |
| considerations/02-traffic-compute.md:825 | https://builder.aws.com/content/3EumjoZascWd1oZiEgL8ORlv3qE/timeouts-retries-and-backof… | C (사용자 결정). 같은 출처 줄의 sre.google·Cloud Run·Vercel 문서가 항목을 뒷받침하므로 표시는 지움(§5.4) |
| considerations/02-traffic-compute.md:855 | https://builder.aws.com/content/3EumjoZascWd1oZiEgL8ORlv3qE/timeouts-retries-and-backof… | C (사용자 결정). sre.google이 항목을 뒷받침하므로 표시는 지움(§5.4) |
| considerations/03-deploy-release.md:756 | https://web.dev/articles/service-worker-lifecycle | C (사용자 결정) |

**판단 메모 (사용자가 뒤집을 수 있는 것).**

1. **주요 클라우드의 일반 원칙 문서.** AWS Well-Architected·백서·Builders' Library·아키텍처 블로그, GCP 아키텍처 문서는 최종 규칙 기준 5("주요 클라우드 자체 문서, sre.google 포함")로 A다.
2. **Terraform provider 문서.** 인자 이름·기본값처럼 provider 자신의 동작은 provider 문서를 공식으로 봤다(hashicorp/* provider는 Terraform, 기준 1). 클라우드 서비스 자체의 한도를 말하는 경우는 C(§4의 HashiCorp 3건). 그 밖의 provider는 발행처 판정을 따른다(Upstash·Ably·Confluent·PlanetScale 등 C, 단일 관리자 provider C).
3. **공급사의 자기 제품 글.** 자기 제품 수치를 말하면 소유자 발행으로 보고 발행처 판정을 따랐다(Railway A, Render·Fly.io·Appwrite C).
4. **Supabase 문서의 PostgreSQL 설명**, **Next.js 문서의 nginx 설명**은 주제 불일치로 C(§4) 그대로다.
5. **nginx·Grafana·Stripe.** 이전 수정 지시는 A 목록에 넣었지만 최종 규칙의 다섯 기준에 들지 않아 C로 내렸다(§5.3). 이 결정이 엔진에 미치는 영향(nginx 기본값 5개 삭제)은 §8.1에 있다.

## 7. 근거 없는 주장

### 7.1 파일별 수

| 파일 | ⚠️근거없음 줄 (출처 없이 사실 서술) | 그중 명시적 표시(추론·출처 미확인 등) | 그중 표 출처 칸 빈 행 | `미확인` 포함 줄 (값 공백 — 별도) |
|---|---|---|---|---|
| dimensions.md | 5 | 0 | 0 | 0 |
| capabilities/01-sql-databases.md | 26 | 4 | 22 | 73 |
| capabilities/02-nosql-baas.md | 27 | 17 | 10 | 71 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md | 47 | 6 | 41 | 151 |
| capabilities/04-compute-tier0.md | 78 | 32 | 46 | 184 |
| capabilities/05-compute-tier1-2.md | 85 | 29 | 56 | 85 |
| capabilities/06-artifacts-datastores.md | 1 | 0 | 0 | 60 |
| capabilities/07-artifacts-services.md | 2 | 2 | 0 | 71 |
| capabilities/08-artifacts-compute.md | 49 | 49 | 0 | 101 |
| capabilities/09-network-lb-ingress.md | 96 | 20 | 76 | 162 |
| capabilities/10-network-edge-egress.md | 125 | 107 | 18 | 160 |
| capabilities/README.md | 1 | 0 | 0 | 2 |
| considerations/01-resilience-dr.md | 23 | 23 | 0 | 23 |
| considerations/02-traffic-compute.md | 9 | 9 | 0 | 8 |
| considerations/03-deploy-release.md | 41 | 41 | 0 | 43 |
| considerations/04-data-consistency.md | 18 | 18 | 0 | 19 |
| considerations/05-security-compliance.md | 21 | 21 | 0 | 31 |
| considerations/06-cost.md | 23 | 23 | 0 | 27 |
| considerations/07-observability-verification.md | 46 | 46 | 0 | 36 |
| considerations/08-workloads-platforms.md | 13 | 13 | 0 | 20 |
| considerations/README.md | 0 | 0 | 0 | 3 |

표시 수와 별개로, 다음은 출처 표시가 아예 없는 설계·가정 문장이라 표시하지 않았다: considerations/ 각 파일 끝의 "새 축·규칙 후보" 절, 08-workloads-platforms.md 파트 2의 도메인별 기본 수준·가정 표(가정으로 명시됨), capabilities 요약 비교표(각 절 표를 요약).

### 7.2 capabilities/와 dimensions.md의 근거 없는 주장 목록

| 파일:줄 | 주장 (100자 이내) | 유형 |
|---|---|---|
| dimensions.md:85 | 평시 동시성(D2)과 폭증 형태(D3)는 별개다. 업무용 시스템은 폭증이 없어도 평시 동시 쓰기가 높다. SQLite 시나리오는 D3가 아니라 D2와 C1에서 걸린다. | 출처 없이 사실 서술 |
| dimensions.md:123 | 2.1 SQLite 업무 시스템 — 능력: SQLite: 한 순간에 쓰기 하나, 같은 호스트의 프로세스만 공유(WAL), 매니지드 HA 없음 | 출처 없이 사실 서술(SQLite 능력 요약) |
| dimensions.md:135 | 2.2 같은 틀로 나오는 다른 경우 — Cloud Run에서 웹소켓 채팅: A3 장시간 연결 | 출처 없이 사실 서술(Cloud Run 최대 60분) |
| dimensions.md:136 | 2.2 같은 틀로 나오는 다른 경우 — Vercel에서 10분짜리 엑셀 생성: A2 수 분 | 출처 없이 사실 서술(Vercel 실행 시간) |
| dimensions.md:137 | 2.2 같은 틀로 나오는 다른 경우 — Cloud Run 요청 기반 과금에서 응답 후 메일 발송: A4 있음 | 출처 없이 사실 서술(Cloud Run 요청 밖 CPU) |
| capabilities/01-sql-databases.md:52 | 0. 요약 비교표 — PlanetScale Postgres: 다수 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/01-sql-databases.md:83 | 1.1 SQLite — 기본 — DS.cost_floor: 0 (호스트 디스크 비용에 포함) | 표 출처 칸 비어 있음 |
| capabilities/01-sql-databases.md:114 | 1.2 SQLite — WAL 모드 — DS.availability: 없음 | 표 출처 칸 비어 있음 |
| capabilities/01-sql-databases.md:119 | 1.2 SQLite — WAL 모드 — DS.cost_floor: 0 | 표 출처 칸 비어 있음 |
| capabilities/01-sql-databases.md:144 | 1.3 libSQL · Turso Cloud — DS.connections: 원격 HTTP/WebSocket. 연결 수 한도 미확인 | 표 출처 칸 비어 있음 |
| capabilities/01-sql-databases.md:215 | 2.1 PostgreSQL — 자체 운영 — DS.multi_host_access: 가능 (TCP) | 표 출처 칸 비어 있음 |
| capabilities/01-sql-databases.md:218 | 2.1 PostgreSQL — 자체 운영 — DS.scaling: 수직(재시작), 읽기 복제본 | 표 출처 칸 비어 있음 |
| capabilities/01-sql-databases.md:246 | 2.2 PostgreSQL — Amazon RDS, S — DS.multi_host_access: 가능 (VPC 네트워크) | 표 출처 칸 비어 있음 |
| capabilities/01-sql-databases.md:311 | 2.4 PostgreSQL — Amazon RDS, M — DS.multi_host_access: 가능 (쓰기·읽기 엔드포인트) | 표 출처 칸 비어 있음 |
| capabilities/01-sql-databases.md:408 | 2.7 PostgreSQL — Google Cloud — DS.multi_host_access: 가능 (사설 IP, Auth Proxy·커넥터) | 표 출처 칸 비어 있음 |
| capabilities/01-sql-databases.md:443 | 2.8 PostgreSQL — Google Cloud — DS.regions: 서울 있음 | 표 출처 칸 비어 있음 |
| capabilities/01-sql-databases.md:469 | 2.9 AlloyDB for PostgreSQL — DS.multi_host_access: 가능 | 표 출처 칸 비어 있음 |
| capabilities/01-sql-databases.md:493 | 2.10 PostgreSQL — Supabase, Fr — DS.replication: 없음 | 표 출처 칸 비어 있음 |
| capabilities/01-sql-databases.md:560 | 2.12 PostgreSQL — Neon, Free — DS.multi_host_access: 가능 (TCP, HTTP, WebSocket) | 표 출처 칸 비어 있음 |
| capabilities/01-sql-databases.md:611 | 2.14 PostgreSQL — PlanetScale — DS.backup: PITR: 기본 2일 전 ~ **현재 5분 전** (자동 백업 주기는 원문 미확인) | 명시적 표시(추론·출처 미확인 등) |
| capabilities/01-sql-databases.md:614 | 2.14 PostgreSQL — PlanetScale — DS.availability: 자동 승격(커스텀 오퍼레이터). 페일오버 시간 원문 미확인 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/01-sql-databases.md:615 | 2.14 PostgreSQL — PlanetScale — DS.multi_host_access: 가능 | 표 출처 칸 비어 있음 |
| capabilities/01-sql-databases.md:618 | 2.14 PostgreSQL — PlanetScale — DS.scaling: 클러스터 SKU 변경 (중단 여부 미확인) | 표 출처 칸 비어 있음 |
| capabilities/01-sql-databases.md:665 | 3.1 MySQL — Amazon RDS for MyS — DS.query_models: 조인, JSON, InnoDB 전문 검색 | 표 출처 칸 비어 있음 |
| capabilities/01-sql-databases.md:671 | 3.1 MySQL — Amazon RDS for MyS — DS.multi_host_access: 가능 | 표 출처 칸 비어 있음 |
| capabilities/01-sql-databases.md:727 | 3.3 MySQL — Google Cloud SQL f — DS.multi_host_access: 가능 | 표 출처 칸 비어 있음 |
| capabilities/01-sql-databases.md:739 | 3.4 MySQL — PlanetScale Vitess — DS.concurrent_writers: 다수 | 표 출처 칸 비어 있음 |
| capabilities/01-sql-databases.md:740 | 3.4 MySQL — PlanetScale Vitess — DS.row_contention: InnoDB 기반 (세부 미확인) | 표 출처 칸 비어 있음 |
| capabilities/01-sql-databases.md:749 | 3.4 MySQL — PlanetScale Vitess — DS.multi_host_access: 가능 (MySQL 프로토콜, `@planetscale/database` HTTP  | 표 출처 칸 비어 있음 |
| capabilities/01-sql-databases.md:752 | 3.4 MySQL — PlanetScale Vitess — DS.scaling: 수평 샤딩(Vitess) | 표 출처 칸 비어 있음 |
| capabilities/01-sql-databases.md:784 | PostgreSQL의 "트랜잭션 DDL 전반" 원칙을 직접 명시한 문서 문장은 이번에 찾지 못했다(위 인용은 `CREATE INDEX` 사례). 일반 원칙으로 쓰되 출처는 미확인으 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/02-nosql-baas.md:128 | 2. Cloud Firestore — Enterpris — DS.connections: Native 모드는 SDK. MongoDB 호환 모드의 연결 한도는 미확인 | 표 출처 칸 비어 있음 |
| capabilities/02-nosql-baas.md:130 | 2. Cloud Firestore — Enterpris — DS.availability: Firestore 공통 SLA로 추정되지만 Enterprise 별도 수치는 미확인 | 표 출처 칸 비어 있음 |
| capabilities/02-nosql-baas.md:134 | 2. Cloud Firestore — Enterpris — DS.scaling: 자동(관리형) | 표 출처 칸 비어 있음 |
| capabilities/02-nosql-baas.md:158 | 3. Firebase Realtime Database — DS.transactions: 단일 서브트리만 원자적. 여러 경로에 걸친 트랜잭션 없음 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/02-nosql-baas.md:231 | Supabase를 떠날 때 바뀌는 것(추론, 근거는 각 행): | 명시적 표시(추론·출처 미확인 등) |
| capabilities/02-nosql-baas.md:261 | 5. Amazon DynamoDB — 단일 리전 테이블 — DS.query_models: 키 질의(Query), 전체 Scan, GSI(기본 20개)·LSI(5개, 생성 시만),  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/02-nosql-baas.md:265 | 5. Amazon DynamoDB — 단일 리전 테이블 — DS.schema_change: 기본 키 외 스키마 없음. GSI는 나중에 추가 가능(백필 중 새 GSI에는 오토스케일링 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/02-nosql-baas.md:318 | 6. Amazon DynamoDB — 글로벌 테이블 — DS.backup: 리전별 PITR 설정(단일 리전과 같은 규칙) | 표 출처 칸 비어 있음 |
| capabilities/02-nosql-baas.md:351 | 7. MongoDB Atlas — Free·Flex — DS.replication: 3노드 레플리카셋, 기본 write concern `w: "majority"` | 명시적 표시(추론·출처 미확인 등) |
| capabilities/02-nosql-baas.md:358 | 7. MongoDB Atlas — Free·Flex — DS.multi_host_access: IP 접근 목록에 있는 호스트면 가능(드라이버 연결) | 명시적 표시(추론·출처 미확인 등) |
| capabilities/02-nosql-baas.md:375 | Free는 백업이 없고 30일 비활동 시 일시정지된다. Flex는 PITR이 없다(최악 RPO 약 1일, 일일 스냅샷 기준 추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/02-nosql-baas.md:394 | 8. MongoDB Atlas — Dedicated — DS.schema_change: 스키마 없음(선택적 검증) | 표 출처 칸 비어 있음 |
| capabilities/02-nosql-baas.md:395 | 8. MongoDB Atlas — Dedicated — DS.availability: 3노드 자동 페일오버. SLA 99.995%(적용 티어 원문 미확인) | 명시적 표시(추론·출처 미확인 등) |
| capabilities/02-nosql-baas.md:474 | 10. Google Cloud Spanner — DS.security: IAM(원문 미확인), CMEK(모든 에디션, 무료 체험 제외) | 명시적 표시(추론·출처 미확인 등) |
| capabilities/02-nosql-baas.md:509 | 11. Google Cloud Bigtable — DS.connections: gRPC 클라이언트, 연결 한도는 미확인 | 표 출처 칸 비어 있음 |
| capabilities/02-nosql-baas.md:512 | 11. Google Cloud Bigtable — DS.multi_host_access: 가능(클라이언트 라이브러리) | 표 출처 칸 비어 있음 |
| capabilities/02-nosql-baas.md:522 | 서버 전용 클라이언트 라이브러리를 쓰며 HBase API와 호환된다(원문 미확인). 행 키 설계가 질의 전부를 좌우하므로 관계형과의 상호 이식은 사실상 데이터 모델을 다시 짜야 한 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/02-nosql-baas.md:545 | 12. Appwrite Cloud — DS.connections: 서버리스는 REST/SDK(연결 개념 없음, 추론). Dedicated는 네이티브 연결 문자열 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/02-nosql-baas.md:548 | 12. Appwrite Cloud — DS.multi_host_access: 가능(관리형 API) | 표 출처 칸 비어 있음 |
| capabilities/02-nosql-baas.md:585 | 13. PocketBase — 자체 호스팅 — DS.multi_host_access: **불가(단일 서버)**. 확장은 수직만 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/02-nosql-baas.md:595 | REST 비슷한 API와 실시간 구독을 제공한다. JS·Dart SDK로 클라이언트가 직접 접근한다(SDK 사실은 추론, 근거 미확인). Go나 JS 훅으로 확장할 수 있다. | 명시적 표시(추론·출처 미확인 등) |
| capabilities/02-nosql-baas.md:596 | Postgres(Supabase 등)로 옮길 때: SDK 호출을 Data API나 SQL로 바꾸고, API 규칙을 RLS나 서버 권한 검사로 바꾸고, 인증을 이전하고, 실시간 구독 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/02-nosql-baas.md:613 | 14. Convex — DS.row_contention: OCC(낙관적 동시성 제어). 충돌하면 트랜잭션을 자동으로 다시 실행. 진정한 직렬화 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/02-nosql-baas.md:674 | 1536차원 이상 임베딩은 vector 인덱스 한도(2,000)에 가깝다. 3072차원 같은 큰 임베딩은 halfvec이나 차원 축소가 필요하다(4,000 한도 기준 추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/02-nosql-baas.md:693 | 16. Pinecone — Serverless — DS.connections: API·SDK(연결 개념 없음, 추론) | 표 출처 칸 비어 있음 |
| capabilities/02-nosql-baas.md:696 | 16. Pinecone — Serverless — DS.multi_host_access: 가능(API) | 표 출처 칸 비어 있음 |
| capabilities/02-nosql-baas.md:706 | 서버 측 API 키와 SDK(Python, Node 등. 목록 원문 미확인)를 쓴다. | 명시적 표시(추론·출처 미확인 등) |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:97 | 0.4 스케줄러 — Cloud Scheduler: 1분(문구 미확인) | 명시적 표시(추론·출처 미확인 등) |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:178 | 앱 프로세스 안 작업 큐 — FastAPI Backgr — QU.ordering: 보장 없음 | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:179 | 앱 프로세스 안 작업 큐 — FastAPI Backgr — QU.dedup: 없음 | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:180 | 앱 프로세스 안 작업 큐 — FastAPI Backgr — QU.retention: 없음 (프로세스 메모리에만 있음). 메시지 크기 한도는 프로세스 메모리 | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:181 | 앱 프로세스 안 작업 큐 — FastAPI Backgr — QU.retry_dlq: 없음 (직접 구현해야 함) | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:210 | 컨테이너 로컬 디스크 — Cloud Run 인메모리 F — FS.versioning_lifecycle: 없음 | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:211 | 컨테이너 로컬 디스크 — Cloud Run 인메모리 F — FS.delivery: 앱이 직접 서빙(`express.static('uploads')` 등). CDN 연동 없음 | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:235 | 앱 프로세스 안 스케줄러 — node-cron, APS — SC.frequency: 라이브러리 제한 없음(초 단위 가능) | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:237 | 앱 프로세스 안 스케줄러 — node-cron, APS — SC.target: 같은 프로세스의 함수. 실행 시간 제한 없음(대신 웹 요청과 CPU를 나눠 씀) | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:238 | 앱 프로세스 안 스케줄러 — node-cron, APS — SC.cost_floor: $0 | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:577 | Cloudflare Workers KV — CA.availability: Cloudflare 전역 네트워크. SLA 수치는 미확인 | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:661 | Amazon SNS — 표준 / FIFO 토픽 — QU.ordering: 표준: 보장 없음(문서 문구 미확인). FIFO: 메시지 그룹 안 순서 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:718 | Google Cloud Pub/Sub — QU.consumer_scaling: KEDA `gcp-pubsub` 스케일러가 있다는 것은 일반 지식(이번에 미확인). Cloud Run | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:769 | Kafka — Amazon MSK — QU.retry_dlq: 브로커 기능 없음. 컨슈머가 오프셋 커밋·재시도 토픽·DLQ 토픽을 직접 구현 | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:771 | Kafka — Amazon MSK — QU.consumer_scaling: 파티션 수가 컨슈머 병렬도의 상한. KEDA kafka 스케일러(랙 기반)는 이번에 미확인 | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:795 | Kafka — Confluent Cloud — QU.retry_dlq: 컨슈머 구현 | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:822 | Redis Streams — QU.throughput: 단일 스레드 Redis 한도 | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:844 | BullMQ — QU.ordering: 기본 FIFO(우선순위·지연 지원). 엄격한 보장 문구는 미확인 | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:848 | BullMQ — QU.throughput: Redis 한도 | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:849 | BullMQ — QU.consumer_scaling: 워커 프로세스를 늘림. 큐 길이 기반 오토스케일은 외부(KEDA 등)로 | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:876 | Celery — 브로커별: RabbitMQ / Red — QU.ordering: 보장 안 함(브로커·동시성에 따름, 문구 미확인) | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:881 | Celery — 브로커별: RabbitMQ / Red — QU.consumer_scaling: 워커 수 확장(KEDA는 브로커 큐 길이 기준) | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:888 | FastAPI `BackgroundTasks` → `@celery.task` + `task.delay()` + 워커 프로세스 분리. 가벼운 대안: RQ, arq(asyncio),  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:907 | Sidekiq — QU.dedup: OSS 없음(Enterprise unique jobs는 미확인) | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:911 | Sidekiq — QU.consumer_scaling: 프로세스·스레드 확장 | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:936 | Postgres 기반 큐 — `FOR UPDATE SK — QU.retention: DB 저장 용량 한도. 정리(archival) 필요 | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:938 | Postgres 기반 큐 — `FOR UPDATE SK — QU.throughput: DB 쓰기 처리량 한도. 폴링이 DB 부하·연결을 씀 | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:939 | Postgres 기반 큐 — `FOR UPDATE SK — QU.consumer_scaling: 워커 수 확장(연결 수 C8 한도 주의) | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:946 | Node pg-boss(cron 스케줄도 클러스터당 1회), Python은 Procrastinate·Django-Q 등(출처 미확인), Ruby Solid Queue·GoodJob | 명시적 표시(추론·출처 미확인 등) |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:966 | Inngest — QU.consumer_scaling: 플랫폼이 HTTP로 내 함수(서버리스)를 호출 → 플랫폼 확장을 따름 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:992 | Trigger.dev — QU.consumer_scaling: 플랫폼이 컨테이너를 띄워 실행(내 서버 불필요) | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:1018 | Upstash QStash — QU.consumer_scaling: HTTP 푸시 → 대상 플랫폼 확장 | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:1161 | Supabase Cron — SC.cost_floor: 추가 비용 없음(DB 자원 사용) | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:1204 | GitHub Actions `schedule` — SC.target: 러너에서 임의 스크립트(HTTP 호출 등) | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:1229 | Socket.IO — 어댑터 없음 — RT.cost_floor: $0(앱 서버 비용) | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:1248 | Socket.IO — Redis 어댑터 / Redis — RT.connections: 앱 서버 수 × 서버당 연결 | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:1251 | Socket.IO — Redis 어댑터 / Redis — RT.cost_floor: Redis 비용(캐시 계열 표) | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:1436 | Amazon S3 — S3 Standard — FS.object_limits: **객체 최대 약 50 TB(48.8 TiB)**, 단일 PUT 5 GB, 멀티파트 5 MiB~5 G | 명시적 표시(추론·출처 미확인 등) |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:1463 | Google Cloud Storage — Standar — FS.shared_access: 가능(HTTP API) | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:1488 | Cloudflare R2 — FS.shared_access: 가능(S3 호환 API, Workers 바인딩) | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:1490 | Cloudflare R2 — FS.versioning_lifecycle: 수명 주기 규칙 있음(이번에 미확인). 버전 관리 미확인 | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:1566 | Cloud Storage for Firebase — FS.delivery: GCS 송신 요금 | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:1587 | Amazon EFS — FS.consistency: NFSv4.1 파일 시스템 의미론(일관성 상세 문구 미확인) | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:1589 | Amazon EFS — FS.object_limits: 파일 크기 한도 미확인. 업로드는 앱이 파일로 씀(서명 URL 없음) | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:1591 | Amazon EFS — FS.delivery: CDN 직접 연동 없음(앱이 서빙) | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:1612 | Google Filestore — FS.consistency: NFS 의미론(상세 미확인) | 표 출처 칸 비어 있음 |
| capabilities/03-cache-queue-scheduler-realtime-storage.md:1640 | 블록 볼륨 다중 연결 제약 — Amazon EBS, G — FS.versioning_lifecycle: 스냅샷 | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:95 | 요약 비교표 — Fly.io Machines: 프록시 유휴 타임아웃 설정 가능, 기본값 `미확인` | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:137 | 1.1 Vercel Functions — Hobby — CP.ops_burden: 서버·노드 관리 없음. 리전·`maxDuration`·크론 설정과 DB 연결 관리만 남음 (추론, | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:150 | 종속 정도: Next.js 표준 API만 쓰면 낮음, 위 Vercel 전용 API·Workflow를 쓰면 중간~높음 (추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:180 | 1.2 Vercel Functions — Pro — CP.ops_burden: 서버 관리 없음. 지출 관리·리전·롤링 릴리스 설정 (추론) | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:216 | 1.3 Vercel Functions — Enterpr — CP.ops_burden: 서버 관리 없음 (추론) | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:247 | 1.4 Vercel — Edge runtime — CP.networking: 고정 IP·Secure Compute 대상 아님 (`미확인`) | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:250 | 1.4 Vercel — Edge runtime — CP.ops_burden: 서버 관리 없음 (추론) | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:257 | Edge 코드는 Web API만 쓰므로 Node.js 런타임으로 바꾸면 대부분 그대로 돌아간다(추론). 다만 `export const runtime = 'edge'` 선언 제거가  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:288 | 2.1 Netlify Functions — Free · — CP.ops_burden: 서버 관리 없음 (추론) | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:300 | 종속 정도: 함수 형식은 Web 표준 `Request`/`Response` 기반이라 낮음~중간, Blobs·DB를 쓰면 중간 (추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:317 | 2.2 Netlify Functions — Pro · — CP.cold_start: scale-to-zero. 최소 인스턴스 `미확인` | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:329 | 2.2 Netlify Functions — Pro · — CP.ops_burden: 서버 관리 없음 (추론) | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:355 | 2.3 Netlify — Edge Functions — CP.local_disk: 없음 (`미확인`, 파일 시스템 언급 없음) | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:363 | 2.3 Netlify — Edge Functions — CP.plan_limits: 플랜별 차이 `미확인` | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:364 | 2.3 Netlify — Edge Functions — CP.ops_burden: 서버 관리 없음 (추론) | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:371 | Deno 기반이다. Next.js 미들웨어가 여기에 매핑되므로, 컨테이너에서는 Next.js 서버가 미들웨어를 직접 실행한다(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:398 | 3.1 Cloudflare Workers · Pages — CP.availability: 전 세계 데이터센터 분산 실행 (추론, how-workers-works) | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:402 | 3.1 Cloudflare Workers · Pages — CP.ops_burden: 서버 관리 없음. 대신 Workers 런타임 제약(Node 호환 플래그)에 맞춰 코드를 써야  | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:413 | 종속 정도: 바인딩을 쓰면 높음, 순수 `fetch` 핸들러면 중간 (추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:436 | 3.2 Cloudflare Workers · Pages — CP.availability: 전 세계 분산 (추론) | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:440 | 3.2 Cloudflare Workers · Pages — CP.ops_burden: 서버 관리 없음 (추론) | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:448 | §3.1과 같다. Workflows(`step.do`, `step.sleep`)는 컨테이너 환경에서 Temporal류 워크플로 엔진이나 DB 기반 작업 큐로 바꿔야 한다(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:463 | 3.3 Cloudflare — Durable Objec — CP.cold_start: 하이버네이션 후 재활성 지연 `미확인` | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:464 | 3.3 Cloudflare — Durable Objec — CP.instance_size: 객체당 초당 약 1,000 요청(소프트). 메모리 128MB(Workers와 같음, 추론 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:467 | 3.3 Cloudflare — Durable Objec — CP.scaling: 객체 수로 수평 확장, 한 객체는 단일 스레드 (추론, 초당 1,000 요청 소프트 한도) | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:475 | 3.3 Cloudflare — Durable Objec — CP.ops_burden: 서버 없음. 객체 분할 설계 필요 (추론) | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:482 | DO는 다른 플랫폼에 같은 개념이 없다. 컨테이너로 옮기면 웹소켓 서버 + Redis pub/sub + 외부 DB로 다시 설계한다(추론). 종속 정도 높음. | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:494 | 3.4 Cloudflare — Containers — CP.request_timeout: 앞단 Worker·DO 한도를 따름 (추론). 컨테이너 자체 요청 한도 `미확인` | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:495 | 3.4 Cloudflare — Containers — CP.long_connection: DO를 통해 웹소켓 전달 가능 (추론, 공식 인용 `미확인`) | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:499 | 3.4 Cloudflare — Containers — CP.request_size: 앞단 Worker 한도 (추론) | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:509 | 3.4 Cloudflare — Containers — CP.ops_burden: 이미지 관리 + DO 제어 코드 작성 (추론) | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:516 | 컨테이너 이미지 자체는 이식된다. 바뀌는 것은 앞단 Worker·DO 제어 코드와 바인딩뿐이다. 종속 정도 낮음~중간 (추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:534 | 4.1 Railway — Free · Trial — CP.cpu_outside_request: 가능(상시 컨테이너, 추론). 서버리스(앱 슬리핑)를 켜면 아웃바운드 트래픽이 없을  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:543 | 4.1 Railway — Free · Trial — CP.availability: 레플리카 1개라 존 분산 불가 (추론) | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:551 | $0, 크레딧 범위 안에서만 실행. 상시 컨테이너 0.5vCPU·512MB는 단가 계산상 약 월 $15(재료 W-070의 추정, 추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:573 | 4.2 Railway — Hobby — CP.cpu_outside_request: 가능(상시 컨테이너, 추론) | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:607 | 4.3 Railway — Pro — CP.cpu_outside_request: 가능(추론) | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:620 | 4.3 Railway — Pro — CP.ops_burden: 낮음 | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:681 | 5.2 Render — 유료 인스턴스 — CP.cold_start: 스핀다운 없음(스핀다운은 Free만, 추론) | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:716 | 6. Fly.io — Machines — CP.long_connection: 공식 문서 인용 `미확인` | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:731 | 6. Fly.io — Machines — CP.cost_floor: 초 단위: shared-cpu-1x 256MB $0.00000075/초(약 월 $1.94, 추론), 512MB  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:734 | 종량제 월 청구 또는 선불 크레딧. 최소 상시 머신 1대 약 월 $2(추론). 지출 상한 기능 `미확인`. | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:781 | 결과물이 Cloud Run 위 Node 앱이므로 Cloud Run(티어 1)으로 가는 이전 비용이 가장 낮다(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:783 | 종속 정도: 낮음 (추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:810 | 7.2 Cloud Functions for Fireba — CP.ops_burden: 낮음 | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:817 | `firebase-functions` 트리거(`onRequest`, `onDocumentWritten`, `onSchedule`, `firebase-functions/v2`) →  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:819 | 종속 정도: HTTP만 쓰면 낮음, Firestore·Auth 이벤트 트리거가 많으면 높음 (추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:839 | 8.1 Supabase Edge Functions — — CP.cold_start: 호출마다 새 isolate, 밀리초 단위. 최소 인스턴스 없음(추론) | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:851 | 8.1 Supabase Edge Functions — — CP.ops_burden: 낮음 | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:862 | 종속 정도: 낮음~중간 (추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:890 | 8.2 Supabase Edge Functions — — CP.ops_burden: 낮음 | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:926 | 9.1 Replit — Autoscale — CP.deploy: 롤백 `미확인` | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:928 | 9.1 Replit — Autoscale — CP.networking: 고정 출구 IP `미확인` | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:931 | 9.1 Replit — Autoscale — CP.ops_burden: 낮음 | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:941 | 종속 정도: 코드는 낮음, 파일 시스템에 데이터가 있으면 이전 필수 (추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:964 | 9.2 Replit — Reserved VM — CP.availability: 단일 VM (추론) | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:968 | 9.2 Replit — Reserved VM — CP.ops_burden: 낮음 | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:990 | 9.3 Replit — Scheduled — CP.cold_start: 실행마다 기동 (추론) | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:1000 | 9.3 Replit — Scheduled — CP.regions: `[충돌]` | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:1001 | 9.3 Replit — Scheduled — CP.plan_limits: 최소 주기 `미확인`, 중복·누락 보장 `미확인` | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:1002 | 9.3 Replit — Scheduled — CP.ops_burden: 낮음 | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:1030 | 10.1 Heroku — Eco · Basic dyno — CP.cold_start: Eco 30분 유휴 시 잠듦, 월 1,000시간 소진 시 그달 남은 기간 잠듦. Basic은  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:1037 | 10.1 Heroku — Eco · Basic dyno — CP.deploy: Preboot(무중단) 불가 → 배포 시 짧은 중단 (추론). 롤백 `미확인` | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:1039 | 10.1 Heroku — Eco · Basic dyno — CP.networking: 고정 출구 IP 문서 404, `미확인` | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:1042 | 10.1 Heroku — Eco · Basic dyno — CP.ops_burden: 낮음(buildpack, Procfile) | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:1057 | 상품이 기능 동결 상태라 신규 구성 후보로는 낮은 순위 (추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:1068 | 10.2 Heroku — Standard · Perfo — CP.cpu_outside_request: 가능 | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:1069 | 10.2 Heroku — Standard · Perfo — CP.cold_start: 잠들지 않음 (추론, 잠듦은 Eco 규칙) | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:1081 | 10.2 Heroku — Standard · Perfo — CP.ops_burden: 낮음 | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:1100 | 11. DigitalOcean — App Platfor — CP.request_timeout: 기본 30초, 최대 100초(PHP 지원 문서 근거, 플랫폼 전체 한도의 공식 근거는 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/04-compute-tier0.md:1102 | 11. DigitalOcean — App Platfor — CP.cpu_outside_request: 가능(상시 컨테이너, 추론) | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:1103 | 11. DigitalOcean — App Platfor — CP.cold_start: scale-to-zero 문서 없음 (`미확인`) | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:1115 | 11. DigitalOcean — App Platfor — CP.ops_burden: 낮음 | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:1153 | 12.1 Koyeb — Free 인스턴스 — CP.networking: 사설 네트워크 있음, 고정 IP `미확인` | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:1156 | 12.1 Koyeb — Free 인스턴스 — CP.ops_burden: 낮음 | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:1186 | 12.2 Koyeb — 유료 인스턴스 — CP.availability: 멀티 리전 배치 가능 여부 `미확인` | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:1187 | 12.2 Koyeb — 유료 인스턴스 — CP.networking: 사설 네트워크, 고정 IP `미확인` | 표 출처 칸 비어 있음 |
| capabilities/04-compute-tier0.md:1190 | 12.2 Koyeb — 유료 인스턴스 — CP.ops_burden: 낮음 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:138 | 2.1 Cloud Run 서비스 — 요청 기반 과금 — CP.local_disk: 쓰기 가능한 파일시스템은 **메모리 위**(쓰면 메모리 차감, 인스턴스 종료 시 소멸). 인메모리 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/05-compute-tier1-2.md:142 | 2.1 Cloud Run 서비스 — 요청 기반 과금 — CP.deploy: 불변 리비전, 비율 트래픽 분할, `--no-traffic` 후 점진 이전, `update-traffic | 명시적 표시(추론·출처 미확인 등) |
| capabilities/05-compute-tier1-2.md:143 | 2.1 Cloud Run 서비스 — 요청 기반 과금 — CP.availability: 리전 안 멀티 존 기본(존 중복은 GPU 서비스만 끌 수 있음). 멀티 리전은 외부 LB +  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/05-compute-tier1-2.md:147 | 2.1 Cloud Run 서비스 — 요청 기반 과금 — CP.ops_burden: 낮음(평가): 노드·OS·LB·인증서 관리 없음. 남는 일은 이미지, 리비전, IAM, VPC 연 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/05-compute-tier1-2.md:191 | 2.2 Cloud Run 서비스 — 인스턴스 기반 과금 — CP.ops_burden: 낮음(평가), §2.1과 같음 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/05-compute-tier1-2.md:227 | 2.3 Cloud Run Jobs — CP.deploy: 작업 정의 갱신(트래픽 개념 없음) | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:228 | 2.3 Cloud Run Jobs — CP.availability: 존 중복 여부 미확인 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:232 | 2.3 Cloud Run Jobs — CP.ops_burden: 낮음(평가). 중복 실행 방지(B3)는 Scheduler 재시도·작업 멱등성으로 직접 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:239 | 티어 0 크론(Vercel Cron 등 HTTP 호출)에서 올 때: 핸들러를 "실행 후 종료하는 프로세스" 엔트리포인트로 분리. `CLOUD_RUN_TASK_INDEX`·`CLOU | 명시적 표시(추론·출처 미확인 등) |
| capabilities/05-compute-tier1-2.md:256 | 2.4 Cloud Run 워커 풀 — CP.long_connection: 아웃바운드 장시간 연결은 가능, 인바운드 공개 연결 없음. Direct VPC ingress로 인스턴스별  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/05-compute-tier1-2.md:258 | 2.4 Cloud Run 워커 풀 — CP.cold_start: 수동 인스턴스 수. 0으로 둘 수 있는지 미확인 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:266 | 2.4 Cloud Run 워커 풀 — CP.availability: 존 중복 미확인 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:267 | 2.4 Cloud Run 워커 풀 — CP.networking: Direct VPC egress·ingress | 명시적 표시(추론·출처 미확인 등) |
| capabilities/05-compute-tier1-2.md:269 | 2.4 Cloud Run 워커 풀 — CP.plan_limits: 프로젝트·리전당 워커 풀 1,000개 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/05-compute-tier1-2.md:270 | 2.4 Cloud Run 워커 풀 — CP.ops_burden: 낮음(평가), 단 확장 로직은 직접 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:299 | 2.5 Cloud Run functions — CP.scaling: HTTP 기본 최대 100, 1,000까지. Cloud Run 서비스 할당량(리전당 1,000) 공유 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/05-compute-tier1-2.md:307 | 2.5 Cloud Run functions — CP.ops_burden: 가장 낮음(평가): Dockerfile도 없음 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:344 | 3.1 ECS on Fargate — 일반 서비스 — CP.ops_burden: 중간(평가): VPC·서브넷·NAT, ALB·대상 그룹·리스너·인증서, 태스크 정의, 오토스케일 정 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:380 | 3.2 ECS on Fargate — Express M — CP.concurrency: 앱이 결정 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:387 | 3.2 ECS on Fargate — Express M — CP.ops_burden: 낮음~중간(평가): 생성은 한 번 호출. 자원은 계정에 남아 이후 세부 조정은 일반 ECS와  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/05-compute-tier1-2.md:419 | 3.3 ECS on Fargate — Fargate S — CP.scaling: 캐퍼시티 프로바이더 전략(base/weight)으로 온디맨드와 혼합 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/05-compute-tier1-2.md:420 | 3.3 ECS on Fargate — Fargate S — CP.concurrency: 앱 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:425 | 3.3 ECS on Fargate — Fargate S — CP.regions: 서울 미확인 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:427 | 3.3 ECS on Fargate — Fargate S — CP.ops_burden: §3.1 + 중단 대비 설계(평가) | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:465 | 3.4 AWS App Runner — 신규 고객 불가 — CP.ops_burden: 낮음(평가), 단 서비스 종료 방향 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:501 | 3.5 AWS Lambda — Function URL — CP.ops_burden: 낮음(평가): 서버 없음. 남는 일은 동시성 할당량, VPC·NAT, DB 연결(RDS Prox | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:505 | 요청 + GB초. Function URL 자체는 추가 요금 없음(별도 단가 행 없음, 인용 미확인). 스트리밍 응답 6 MB 초과분 $0.008/GB(가격 페이지). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/05-compute-tier1-2.md:537 | 3.6 AWS Lambda — API Gateway 경 — CP.deploy: 스테이지 + 카나리 배포(REST, 인용 미확인) + Lambda 별칭 가중치 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/05-compute-tier1-2.md:539 | 3.6 AWS Lambda — API Gateway 경 — CP.networking: REST 사설 API·VPC 링크 지원(인용 미확인). 함수 쪽은 §3.5 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:542 | 3.6 AWS Lambda — API Gateway 경 — CP.ops_burden: 낮음(평가) | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:581 | 4.1 Azure Container Apps — 워크로 — CP.ops_burden: 낮음~중간(평가): 노드 없음. 환경 유형·VNet·서브넷 크기·존 중복을 생성 시 한 번에  | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:606 | 5.1 GKE Autopilot — CP.cpu_outside_request: 있음(Pod는 항상 실행, 요청 단위 CPU 제한 없음) | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:612 | 5.1 GKE Autopilot — CP.concurrency: 앱이 결정(서버 워커·스레드 수) | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:616 | 5.1 GKE Autopilot — CP.networking: VPC 네이티브 기본(Pod IP가 VPC 별칭 IP) → Cloud SQL 사설 IP 연결. 사설 노드의 인터넷은  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/05-compute-tier1-2.md:619 | 5.1 GKE Autopilot — CP.ops_burden: 중간(평가): 노드는 Google 관리, 항상 릴리스 채널, **자동 업그레이드 끌 수 없음**(유지보수 창·제외로  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/05-compute-tier1-2.md:629 | 티어 0에서 바로 오는 것은 비권장(평가): §1.1 + §1.2 전부. | 명시적 표시(추론·출처 미확인 등) |
| capabilities/05-compute-tier1-2.md:648 | 5.2 GKE Standard — 존 클러스터 — CP.cpu_outside_request: 있음 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:654 | 5.2 GKE Standard — 존 클러스터 — CP.concurrency: 앱 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:661 | 5.2 GKE Standard — 존 클러스터 — CP.ops_burden: 높음(평가): 노드 풀, 업그레이드 전략(서지·블루그린), 유지보수 창, 노드 크기·오토스케일 범위,  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/05-compute-tier1-2.md:686 | 5.3 GKE Standard — 리전 클러스터 — CP.cpu_outside_request: 있음 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:692 | 5.3 GKE Standard — 리전 클러스터 — CP.concurrency: 앱 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:696 | 5.3 GKE Standard — 리전 클러스터 — CP.networking: §5.1과 같음. 존 간 트래픽 과금 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/05-compute-tier1-2.md:699 | 5.3 GKE Standard — 리전 클러스터 — CP.ops_burden: 높음(평가), §5.2와 같음 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:724 | 6.1 EKS — 관리형 노드 그룹 + Cluster — CP.cpu_outside_request: 있음(Pod 상시 실행) | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:725 | 6.1 EKS — 관리형 노드 그룹 + Cluster — CP.cold_start: 노드 그룹 최소값까지 축소(0 가능 여부는 CA 설정, 인용 미확인). 노드 프로비저닝 시간 미 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:737 | 6.1 EKS — 관리형 노드 그룹 + Cluster — CP.ops_burden: 높음(평가): 버전 업그레이드(연 1회 이상), 노드 AMI 패치 배포, 애드온(VPC CNI, | 명시적 표시(추론·출처 미확인 등) |
| capabilities/05-compute-tier1-2.md:745 | 티어 0에서 바로 오는 것은 비권장(평가). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/05-compute-tier1-2.md:764 | 6.2 EKS — Karpenter — CP.cpu_outside_request: 있음 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:770 | 6.2 EKS — Karpenter — CP.concurrency: 앱 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:777 | 6.2 EKS — Karpenter — CP.ops_burden: 높음(평가): §6.1 + Karpenter 자체 설치·업그레이드(OSS), NodePool·EC2NodeClas | 명시적 표시(추론·출처 미확인 등) |
| capabilities/05-compute-tier1-2.md:781 | 노드 크기를 Pod requests에 맞춰 골라 대규모에서 절감. 소규모에서는 컨트롤러 노드 때문에 MNG보다 싸지 않다(평가). NodePool limits가 없으면 비용 상한이 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/05-compute-tier1-2.md:800 | 6.3 EKS — Auto Mode — CP.cpu_outside_request: 있음 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:801 | 6.3 EKS — Auto Mode — CP.cold_start: Karpenter 기반 노드 생성(시간 수치 미확인). 노드 0까지 축소 여부 인용 미확인 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/05-compute-tier1-2.md:806 | 6.3 EKS — Auto Mode — CP.concurrency: 앱 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:813 | 6.3 EKS — Auto Mode — CP.ops_burden: 중간(평가): AWS가 컴퓨트 오토스케일, Pod 네트워킹, ELB 연동, EBS 드라이버, 노드 OS 패치(주간 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/05-compute-tier1-2.md:838 | 6.4 EKS — Fargate 프로필 — CP.cold_start: scale-to-zero 없음(노드 개념 없음, Pod 기동 시간 미확인) | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:843 | 6.4 EKS — Fargate 프로필 — CP.concurrency: 앱 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:850 | 6.4 EKS — Fargate 프로필 — CP.ops_burden: 중간(평가): 노드 없음. 남는 일: 클러스터 업그레이드, Pod 재배포, 프로필 셀렉터, 사설 서브넷·NAT | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:874 | 6.5 VM 위 경량 쿠버네티스 — k3s — CP.cpu_outside_request: 있음 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:875 | 6.5 VM 위 경량 쿠버네티스 — k3s — CP.cold_start: 노드 오토스케일 없음(VM 고정) | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:877 | 6.5 VM 위 경량 쿠버네티스 — k3s — CP.request_size: Traefik 설정(미확인) | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:879 | 6.5 VM 위 경량 쿠버네티스 — k3s — CP.scaling: HPA만(노드 증설은 수동) | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:880 | 6.5 VM 위 경량 쿠버네티스 — k3s — CP.concurrency: 앱 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:885 | 6.5 VM 위 경량 쿠버네티스 — k3s — CP.regions: VM 리전 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:886 | 6.5 VM 위 경량 쿠버네티스 — k3s — CP.plan_limits: 없음(자체 운영) | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:887 | 6.5 VM 위 경량 쿠버네티스 — k3s — CP.ops_burden: **가장 높음**(평가): OS 패치, k3s 업그레이드, etcd 백업, 인증서, 저장소, LB, 모니터 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:909 | 7.1 단일 VM + docker compose — E — CP.long_connection: 제한 없음(프록시 설정에 따름) | 명시적 표시(추론·출처 미확인 등) |
| capabilities/05-compute-tier1-2.md:910 | 7.1 단일 VM + docker compose — E — CP.cpu_outside_request: 있음 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:911 | 7.1 단일 VM + docker compose — E — CP.cold_start: 해당 없음(상시). scale-to-zero 없음 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/05-compute-tier1-2.md:913 | 7.1 단일 VM + docker compose — E — CP.request_size: 리버스 프록시 설정(nginx 기본 등, 미확인) | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:915 | 7.1 단일 VM + docker compose — E — CP.scaling: 오토스케일 없음(수직 확장 = 유형 변경, 재시작 필요) | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:916 | 7.1 단일 VM + docker compose — E — CP.concurrency: 앱 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:918 | 7.1 단일 VM + docker compose — E — CP.deploy: `docker compose up -d`로 컨테이너 교체 = **배포 중 순단**(무중단·롤백 수단  | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:922 | 7.1 단일 VM + docker compose — E — CP.plan_limits: 계정 vCPU 할당량(미확인) | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:923 | 7.1 단일 VM + docker compose — E — CP.ops_burden: 높음(평가): OS 패치, Docker 업데이트, TLS 인증서, 백업(EBS 스냅샷), 모니 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:947 | 7.2 단일 VM + docker compose — C — CP.long_connection: 제한 없음 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:948 | 7.2 단일 VM + docker compose — C — CP.cpu_outside_request: 있음 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:949 | 7.2 단일 VM + docker compose — C — CP.cold_start: 해당 없음 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/05-compute-tier1-2.md:951 | 7.2 단일 VM + docker compose — C — CP.request_size: 프록시 설정(미확인) | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:952 | 7.2 단일 VM + docker compose — C — CP.local_disk: Persistent Disk 영속(존 단위) | 명시적 표시(추론·출처 미확인 등) |
| capabilities/05-compute-tier1-2.md:953 | 7.2 단일 VM + docker compose — C — CP.scaling: 없음 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:954 | 7.2 단일 VM + docker compose — C — CP.concurrency: 앱 | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:956 | 7.2 단일 VM + docker compose — C — CP.deploy: 순단 배포(직접 구성) | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:958 | 7.2 단일 VM + docker compose — C — CP.networking: VPC 사설 IP로 Cloud SQL 사설 연결. 고정 외부 IP 예약(단가 미확인) | 표 출처 칸 비어 있음 |
| capabilities/05-compute-tier1-2.md:961 | 7.2 단일 VM + docker compose — C — CP.ops_burden: 높음(평가), §7.1과 같음 | 표 출처 칸 비어 있음 |
| capabilities/06-artifacts-datastores.md:128 | 트랜잭션 모드 풀러(Supabase 6543, Neon `-pooler`, PgBouncer `pool_mode=transaction`, RDS Proxy)를 쓰면 **세션 상태가 | PgBouncer·RDS Proxy 부분은 출처 없음 |
| capabilities/07-artifacts-services.md:663 | 로컬 개발 대응:** 로컬 개발 서버는 `미확인`이다. QStash가 localhost를 부를 수 없으므로 터널이 필요하다(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/07-artifacts-services.md:788 | Terraform:** provider `cloudflare/cloudflare`. `cloudflare_workers_cron_trigger`(`script_name`, `sch | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:55 | 요약표 — 12: Cloud Functions for Firebase | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:104 | 1.1.1 모든 런타임 공통 규칙 — D12: `HEALTHCHECK`는 Docker·compose·ECS 컨테이너 헬스체크용으로만 넣는다. k8s·Cloud Run은 이 지시어를 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:178 | `--forwarded-allow-ips=*`는 LB 뒤에서만 쓴다. 문서는 "Only trust clients you can actually trust!"라고 경고한다. LB 대 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:193 | 생성 규칙: 할당 vCPU가 1 미만이면 2, 그 외에는 `2 × vCPU + 1`로 잡고 메모리 한도로 상한을 둔다(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:210 | distroless에는 셸이 없어 `ENTRYPOINT`가 반드시 exec 형식이어야 한다. 셸이 없으므로 `HEALTHCHECK`는 앱 바이너리의 서브커맨드로 둔다(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:220 | 티어 0(Vercel·Netlify·Cloudflare Pages)이나 오브젝트 스토리지 + CDN이 더 싸다(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:229 | 교체 신호가 하나라도 있거나, 부분 수정이 4개 이상 쌓이면 교체한다(추론, 임계값은 검토 대상). 교체할 때도 기존 파일에 담긴 비표준 단계(시스템 패키지, 빌드 인자, 추가 C | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:265 | 1.3.1 헬스체크 엔드포인트 — LB 헬스체크 (ALB 대상 그룹, GCP BackendConfig, Render `healthCheckPath`, Railway `healthc | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:268 | "liveness는 외부 의존성을 보면 안 된다"는 문장 자체는 공식 문서에서 찾지 못했다. 위 인용에서 이끌어 낸 규칙이다(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:287 | 1.3.2 SIGTERM 처리와 플랫폼별 유예 시간 — 플랫폼: 종료 신호 → 강제 종료 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:314 | 로그를 파일에 쓰는 설정(`logging.FileHandler`, `winston` file transport, `access.log`)은 stdout으로 바꾼다. JSON 한 줄 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:319 | 앱 기동 시점에는 실행하지 않는다.** 인스턴스가 여러 개면 동시에 실행되고, 시간이 기동 제한(Cloud Run 4분 포트 대기 등)을 잡아먹는다(추론). 배포 직전에 **단일  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:390 | azure/container-apps-deploy-action은 2024년 이후 릴리스가 없고 node16 런타임이다(추론: 러너에서 경고나 실패가 날 수 있다). 대안은 `az  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:403 | OIDC를 쓸 수 없는 플랫폼**: Vercel, Netlify, Cloudflare, Railway, Render, Fly, Heroku, DigitalOcean, Koyeb,  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:451 | 1.5 공통 검증 명령 — SIGTERM: `time docker stop -t 30 app` → `docker inspect app --format '{{.State.ExitCo | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:452 | 1.5 공통 검증 명령 — 진행 중 요청: 느린 엔드포인트 호출 중 `docker stop` → 그 요청이 200으로 끝나는가 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:481 | 배포는 Terraform `vercel_deployment`보다 CLI가 단순하다(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:501 | JSON 스키마 검증(`ajv validate -s -d vercel.json`, 도구 사용은 추론) | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:646 | Dockerfile(파트 1). Railpack 자동 빌드 대신 Dockerfile로 재현성을 확보한다(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:648 | Terraform: 공식 provider는 없다. 커뮤니티 `terraform-community-providers/railway`(v0.6.2, 리소스 `railway_projec | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:666 | 레거시 파일이면 `$schema` ``으로 JSON 스키마 검증(추론) | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:685 | Blueprint와 Terraform 중 하나만** 고른다. 같은 자원을 여러 Blueprint로 관리하지 말라는 문서 경고가 있다. Terraform과 Blueprint를 섞는  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:728 | `strategy`: `rolling`/`bluegreen`/`canary`/`immediate`. bluegreen은 헬스체크가 있어야 한다(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:741 | 배포 토큰: `fly tokens create deploy -x 999999h`. 만료를 짧게 두는 것을 권장한다(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:770 | D5: 리전은 us-central1, us-east4, us-east5, asia-east1, asia-southeast1, europe-west4뿐이고 **서울은 없다.** 서울 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:771 | 하부가 Cloud Run이라 종료 유예는 10초라고 보는 것은 (추론)이다. App Hosting 문서에 값은 `미확인`. | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:788 | Terraform: 2세대 함수는 `google_cloudfunctions2_function`(P21)으로도 관리할 수 있지만, Firebase SDK 트리거 코드와 둘 중 하나만 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:812 | `supabase_edge_function_secrets`는 비밀 값을 state에 평문으로 저장한다. 비밀은 CLI로 넣는다(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:823 | `deno check supabase/functions/<name>/index.ts`(도구 사용은 추론) | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:837 | 자동화 불가 단계:** 게시와 설정 전부. 에이전트는 Replit을 **최종 목적지로 선택하지 않는다.** 기존 앱이면 `.replit`의 `run`과 `build`만 운영 서버로 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:933 | Terraform과 CI가 같은 서비스의 이미지를 함께 바꾸면 드리프트가 생긴다. Terraform 쪽에 `lifecycle { ignore_changes = [template[0 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:967 | 공개 접근 검사는 커스텀 정책으로 한다: `allUsers` + `roles/run.invoker`가 의도된 경우만 허용(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:989 | `template.template.max_retries`: 기본 3이다. 마이그레이션이 멱등이 아니면 0으로 둔다(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:1004 | URL이 없으므로 HTTP probe 대상이 없다. 헬스는 프로세스 생존으로 판단한다(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:1006 | 검증 명령:** `terraform validate`. 파트 1 docker 검증은 HTTP 헬스 대신 SIGTERM 종료만 확인한다. 배포 후 큐에 시험 메시지를 넣어 처리되는지 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:1045 | Terraform과 CI가 태스크 정의를 함께 바꾸므로 드리프트가 생긴다. 서비스에 `lifecycle { ignore_changes = [task_definition, desir | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:1055 | 두 값의 관계: 앱 드레인 시간 ≤ stopTimeout, deregistration_delay ≥ 진행 중 요청의 최대 시간(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:1066 | Spot은 2분 경고와 SIGTERM을 주고 온디맨드로 대체하지 않는다. 그래서 `stopTimeout` ≤ 120으로 두고, 웹 서비스는 FARGATE `base ≥ 1`을 섞는 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:1135 | 컨테이너 이미지 방식(웹 앱을 그대로 옮길 때 권장, 추론) | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:1143 | AWS 베이스 이미지가 아니면 런타임 인터페이스 클라이언트가 필요하다. Web Adapter를 쓰면 대신한다(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:1150 | D2와 C8: `reserved_concurrent_executions`. 인스턴스당 동시성이 1이므로 DB 연결 = 동시 실행 수다. RDS Proxy를 더한다(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:1153 | F5와 C8: `vpc_config { subnet_ids, security_group_ids }`. VPC 안에서 외부로 나가려면 NAT가 필요하다(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:1159 | 로컬: 파트 1 docker 검증. Web Adapter가 있어도 일반 컨테이너로 돈다. 확장은 Lambda 밖에서 동작하지 않는다(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:1174 | A3: `protocol_type = "WEBSOCKET"` + `route_selection_expression = "$request.body.action"`. 연결 상태는 Dy | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:1263 | CKV_K8S_15(imagePullPolicy Always)와 CKV_K8S_43(다이제스트)은 sha 태그 운영과 충돌할 수 있다. 정책에 따라 건너뛴다(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:1313 | Checkov: GKE는 CKV_GCP_1, 7, 8, 12, 13, 18, 20, 21, 23, 25, 61, 64, 65, 66, 69, 70, 123, CKV2_GCP_19. | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:1428 | 검증 명령:** P30과 같다. 정적 검사(grep 또는 커스텀 정책, 추론)로 지원하지 않는 어노테이션을 찾는다. | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:1449 | CI: kubeconfig(`/etc/rancher/k3s/k3s.yaml`)를 안전하게 전달해야 한다. 이것이 자동화의 약한 고리다(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/08-artifacts-compute.md:1478 | F4: `stop_grace_period`(기본 10초). `up -d`로 재생성하는 동안 짧은 중단이 생긴다. 무중단이 필요하면(F4 "불가") 이 기준선은 맞지 않는다(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/09-network-lb-ingress.md:78 | 0. 요약 비교표 — AWS NLB: L4 통과(TLS 종단 가능) | 명시적 표시(추론·출처 미확인 등) |
| capabilities/09-network-lb-ingress.md:125 | 1.1 AWS Application Load Balan — NW.websocket: [L7] 웹소켓 기본 지원. 지속 한도는 문서에 없다(미확인). 데이터가 유휴 타임아웃보다 길게 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/09-network-lb-ingress.md:137 | 1.1 AWS Application Load Balan — NW.dns: 해당 없음(10 문서). ALB는 DNS 이름만 주고 IP가 바뀐다. 고정 IP가 필요하면 NLB를 앞에  | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:208 | 1.2 AWS Network Load Balancer — NW.websocket: [L4] TCP 통과라 프로토콜과 무관하게 연결은 유휴 350초 안에서 유지된다(추론, 웹소켓 명 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:215 | 1.2 AWS Network Load Balancer — NW.routing: [L4] 포트 단위 리스너 → 대상 그룹. 가중치 분할은 미확인 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:230 | ALB → NLB로 바꾸면 L7 기능이 사라진다: 경로 라우팅, XFF, WAF, HTTP 헬스 체크 외 L7. 클라이언트 IP는 PROXY v2나 IP 보존으로 받는다. 이때 앱 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/09-network-lb-ingress.md:236 | PROXY v2를 켜면 앱(또는 앞단 nginx)이 반드시 파싱해야 한다. 아니면 모든 요청이 400이 된다(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/09-network-lb-ingress.md:251 | `aws elbv2 describe-listener-attributes --listener-arn <ARN>`(명령 원문 미확인) | 명시적 표시(추론·출처 미확인 등) |
| capabilities/09-network-lb-ingress.md:296 | 1.4 AWS API Gateway — HTTP API — NW.protocols: [L7] HTTPS. 통합: Lambda, HTTP 프록시, VPC 링크(ALB·NLB·Clou | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:304 | 1.4 AWS API Gateway — HTTP API — NW.availability: 리전 서비스. SLA 미확인 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:305 | 1.4 AWS API Gateway — HTTP API — NW.caching: 없음(REST만 캐시) | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:306 | 1.4 AWS API Gateway — HTTP API — NW.security: WAF 직접 연결은 REST만(CKV2_AWS_29가 REST 대상). JWT·Lambda 권한  | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:308 | 1.4 AWS API Gateway — HTTP API — NW.private_connectivity: VPC 링크로 사설 ALB·NLB에 연결(인용 미확인) | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:313 | 고정비 0, 요청당 과금이다. 월 1,300만 요청쯤에서 ALB 고정비($16.43)와 비슷해진다(계산, 추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/09-network-lb-ingress.md:325 | 반드시 명시: A2용 `timeout_milliseconds`, F5용 `aws_apigatewayv2_route.authorization_type`, D3용 스테이지 스로틀(`t | 명시적 표시(추론·출처 미확인 등) |
| capabilities/09-network-lb-ingress.md:344 | 1.5 AWS API Gateway — REST API — NW.websocket: 없음 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:352 | 1.5 AWS API Gateway — REST API — NW.availability: 리전. SLA 미확인 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:356 | 1.5 AWS API Gateway — REST API — NW.private_connectivity: Private API(VPC 엔드포인트), VPC 링크 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:392 | 1.6 AWS API Gateway — WebSocke — NW.protocols: WSS | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:396 | 1.6 AWS API Gateway — WebSocke — NW.client_ip: `$context.identity.sourceIp`(WebSocket 컨텍스트 변수 인용 미확인 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:397 | 1.6 AWS API Gateway — WebSocke — NW.routing: 라우트 선택 식(`$connect`, `$disconnect`, `$default`). 가중치 없음 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:400 | 1.6 AWS API Gateway — WebSocke — NW.security: 권한 부여자는 `$connect`에서만(인용 미확인) | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:425 | 1.7 AWS Lambda Function URL — NW.protocols: [L7] HTTPS | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:428 | 1.7 AWS Lambda Function URL — NW.tls: [TLS] AWS 관리. 사용자 지정 도메인은 URL 자체로 불가(CloudFront 경유, 10 문서, 인용  | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:467 | 1.8 ECS Express Mode가 만드는 ALB — NW.tls: [TLS] ACM 자동 발급. 정책 이름 미확인 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:478 | 유휴 60초를 바꾸는 Express 전용 인자가 문서에 없다(미확인). 바꾸려면 생성된 ALB를 직접 수정해야 하고, 그러면 드리프트가 생긴다(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/09-network-lb-ingress.md:500 | 1.9 AWS Load Balancer Controll — NW.protocols: `backend-protocol-version`(어노테이션 원문 미확인) | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:510 | 1.9 AWS Load Balancer Controll — NW.regions: EKS 리전 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:511 | 1.9 AWS Load Balancer Controll — NW.cost_floor: 생성된 ALB/NLB 비용. `group.name`으로 공유하면 줄어든다 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:526 | 배포 후 검증: `kubectl get ingress`로 주소를 확인한다. `aws elbv2 describe-load-balancer-attributes`로 어노테이션이 반영됐는 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/09-network-lb-ingress.md:578 | 2.1 GCP 전역 외부 Application Load — NW.scaling: [L7] 자동(사전 증설 불필요, 문구 미확인). URL 맵 1 MB | 명시적 표시(추론·출처 미확인 등) |
| capabilities/09-network-lb-ingress.md:583 | 2.1 GCP 전역 외부 Application Load — NW.private_connectivity: 백엔드: 인스턴스 그룹, 존 NEG(GKE 컨테이너 네이티브), 서버리스 N | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:584 | 2.1 GCP 전역 외부 Application Load — NW.regions: 전역 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:639 | 2.2 GCP 리전 외부 Application Load — NW.scaling: 프록시 전용 서브넷 크기가 프록시 수를 제한(인용 미확인) | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:641 | 2.2 GCP 리전 외부 Application Load — NW.caching: 없음(Cloud CDN은 전역만, 인용 미확인) | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:681 | 2.3 GCP 클래식 Application Load B — NW.regions: 전역 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:720 | 2.4 GCP 외부 패스스루 Network Load B — NW.routing: 없음 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:722 | 2.4 GCP 외부 패스스루 Network Load B — NW.availability: 리전 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:744 | 2.5 GCP 외부 프록시 Network Load Ba — NW.websocket: [L4] TCP로 통과. 30초 유휴에 종료(추론) | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:776 | 2.6 GCP 내부 LB — NW.protocols: [L7] HTTP/1.1·2, gRPC. [L4] TCP·UDP·L3_DEFAULT | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:807 | 2.7 Cloud Run 기본 엔드포인트와 도메인 매핑 — NW.layer: [L7] 종단(Google 프런트엔드, 상세 미확인) | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:868 | 2.8 GKE Gateway API — NW.regions: GKE 서울 있음 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:893 | 2.9 GCP 서버리스 NEG — NW.websocket: ALB 규칙 + Cloud Run 요청 타임아웃 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:903 | 2.9 GCP 서버리스 NEG — NW.regions: Cloud Run 리전 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:950 | 검증: `az containerapp ingress show`(명령 원문 미확인). 241초 요청으로 타임아웃을 확인한다. | 명시적 표시(추론·출처 미확인 등) |
| capabilities/09-network-lb-ingress.md:977 | 4.1 ingress-nginx — **은퇴, 저장소 — NW.protocols: [L7] HTTP/1.1·HTTP/2, gRPC(어노테이션) | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:980 | 4.1 ingress-nginx — **은퇴, 저장소 — NW.health_check: Pod readiness를 엔드포인트로 따른다(k8s). 전부 비정상이면 503(nginx  | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:981 | 4.1 ingress-nginx — **은퇴, 저장소 — NW.tls: [TLS] Secret 기반, cert-manager 연동(인용 미확인) | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:984 | 4.1 ingress-nginx — **은퇴, 저장소 — NW.scaling: 컨트롤러 레플리카 수(HPA) | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:985 | 4.1 ingress-nginx — **은퇴, 저장소 — NW.availability: 레플리카 분산 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1016 | 4.2 Gateway API 구현 대표 — Envoy — NW.layer: [L7] 종단 프록시(Envoy). 앞에 Service LoadBalancer [L4] | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1020 | 4.2 Gateway API 구현 대표 — Envoy — NW.protocols: [L7] HTTP/1.1·2, gRPC(GRPCRoute) | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1023 | 4.2 Gateway API 구현 대표 — Envoy — NW.health_check: 엔드포인트 readiness. 능동 헬스 체크는 BackendTrafficPolicy(인용  | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1024 | 4.2 Gateway API 구현 대표 — Envoy — NW.tls: [TLS] Gateway 리스너 TLS. 최소 버전 기본 미확인 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1027 | 4.2 Gateway API 구현 대표 — Envoy — NW.scaling: Envoy 프록시 Deployment 레플리카 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1028 | 4.2 Gateway API 구현 대표 — Envoy — NW.availability: 레플리카 분산 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1029 | 4.2 Gateway API 구현 대표 — Envoy — NW.security: SecurityPolicy(인증·CORS·레이트 리밋, 인용 미확인) | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1039 | Helm으로 설치(`helm_release`, 차트 위치 미확인) + `GatewayClass`(`controllerName: gateway.envoyproxy.io/gateway | 명시적 표시(추론·출처 미확인 등) |
| capabilities/09-network-lb-ingress.md:1046 | 검증: `kubectl get gateway`(PROGRAMMED), `egctl config envoy-proxy route`(명령 원문 미확인). 20초 응답 엔드포인트로 50 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/09-network-lb-ingress.md:1056 | 4.3 쿠버네티스 Service type LoadBal — NW.layer: [L4] 클라우드 L4 LB. EKS는 1.9 컨트롤러로 NLB, GKE는 패스스루 NLB(2.4, 인 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1059 | 4.3 쿠버네티스 Service type LoadBal — NW.websocket: 통과 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1060 | 4.3 쿠버네티스 Service type LoadBal — NW.protocols: TCP/UDP | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1061 | 4.3 쿠버네티스 Service type LoadBal — NW.draining: 클라우드 LB 값 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1065 | 4.3 쿠버네티스 Service type LoadBal — NW.routing: 없음 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1088 | 5.1 nginx — NW.layer: [L7] 종단 프록시. `stream` 모듈로 [L4]도 가능 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1094 | 5.1 nginx — NW.draining: 우아한 종료 `nginx -s quit`(인용 미확인) | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1095 | 5.1 nginx — NW.health_check: 수동(passive) `max_fails`/`fail_timeout`(인용 미확인). 능동 체크는 상용 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1098 | 5.1 nginx — NW.routing: [L7] location, upstream `weight`(인용 미확인) | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1127 | 5.2 Envoy — NW.layer: [L7] 종단, [L4] tcp_proxy | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1131 | 5.2 Envoy — NW.protocols: HTTP/1.1·2·3, gRPC | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1134 | 5.2 Envoy — NW.health_check: 능동·수동(이상치 감지) 지원, 기본 없음(인용 미확인) | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1135 | 5.2 Envoy — NW.tls: 설정 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1136 | 5.2 Envoy — NW.client_ip: `use_remote_address`, `xff_num_trusted_hops`(인용 미확인) | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1137 | 5.2 Envoy — NW.routing: 가중치 클러스터(인용 미확인) | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1156 | 5.3 Caddy — NW.layer: [L7] 종단, 자동 HTTPS | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1160 | 5.3 Caddy — NW.protocols: HTTP/1.1·2·3, 업스트림 h2c 가능(인용 미확인) | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1164 | 5.3 Caddy — NW.tls: [TLS] 자동 HTTPS(ACME) | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1166 | 5.3 Caddy — NW.routing: `lb_policy` 기본 random(가중치 정책 인용 미확인) | 명시적 표시(추론·출처 미확인 등) |
| capabilities/09-network-lb-ingress.md:1185 | 5.4 Traefik v3 — NW.layer: [L7] 종단, TCP 라우터 [L4] | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1187 | 5.4 Traefik v3 — NW.request_timeout: [L7] `respondingTimeouts.readTimeout` **60초**(요청 읽기, v3), `writ | 명시적 표시(추론·출처 미확인 등) |
| capabilities/09-network-lb-ingress.md:1189 | 5.4 Traefik v3 — NW.protocols: HTTP/1.1·2·3, gRPC(인용 미확인) | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1192 | 5.4 Traefik v3 — NW.health_check: 서비스 healthCheck(인용 미확인) | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1193 | 5.4 Traefik v3 — NW.tls: ACME 자동(인용 미확인) | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1215 | 6.1 Vercel 엣지 네트워크 — NW.layer: [L7] 종단 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1219 | 6.1 Vercel 엣지 네트워크 — NW.protocols: HTTP/2·3 미확인 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1239 | 6.2 Netlify 엣지 — NW.layer: [L7] 종단 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1262 | 6.3 Cloudflare 프록시 모드 — NW.layer: [L7] 종단, 전역 애니캐스트 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1263 | 6.3 Cloudflare 프록시 모드 — NW.idle_timeout: [L7] 클라이언트 쪽 Keep-Alive HTTP/1.1 400초, HTTP/2 유휴 400초. 오리진  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/09-network-lb-ingress.md:1291 | 6.4 Render 엣지 프록시 — NW.layer: [L7] 종단 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1292 | 6.4 Render 엣지 프록시 — NW.idle_timeout: 수치 미확인. 문서가 Node `keepAliveTimeout`·`headersTimeout`을 120초 정도로  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/09-network-lb-ingress.md:1314 | 6.5 Railway 엣지 프록시 — NW.layer: [L7] 종단 | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1341 | 6.6 Fly.io 프록시 — NW.websocket: 지원(한도 미확인) | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1348 | 6.6 Fly.io 프록시 — NW.routing: 가중치 분할 미확인(`fly-replay` 동적 라우팅만) | 표 출처 칸 비어 있음 |
| capabilities/09-network-lb-ingress.md:1358 | 검증: `fly config validate`(명령 원문 미확인). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/09-network-lb-ingress.md:1375 | 7. 앱 서버 기본값 — Spring Boot + Tomcat: `keepAliveTimeout` = `connectionTimeout`. Tomcat 코드 기본 **60초**(배 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/09-network-lb-ingress.md:1454 | Cloudflare → 오리진 구간도 같은 원리다. Cloudflare Proxy Idle 900초 → 오리진 keep-alive > 900초가 이상적이다(추론, Cloudflar | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:63 | DNS — 2.4 등록 기관 DNS (요약): L7(DNS) | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:72 | WAF·DDoS — 3.4 Cloud Armor Standard: 기본 규칙 deny[충돌: TF allow] · OWASP 기본 없음 · interval 10~3600초·thro | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:73 | WAF·DDoS — 3.5 Cloud Armor Enterprise: Adaptive Protection 전체 · 청구 보호 Annual만 · 외부 ALB 자동 계수 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:95 | 출구 NAT·고정 IP — 5.5.3 ECS Fargate 고정 IP: 사설+NAT EIP / 퍼블릭 IP는 태스크별·가변(추론) | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:114 | 사설 연결 — 6.6 Direct VPC egress: 서브넷 /26 이상, IP 2×인스턴스(잡 1×); 인스턴스 쿼터 100–200; 시작 연결 지연 1분+, Cloud NAT | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:115 | 사설 연결 — 6.7 Private Service Connect: API용 엔드포인트는 피어링 VPC 접근 불가; 게시 서비스 엔드포인트는 서비스와 같은 리전; 글로벌 액세스 선택 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:133 | 1.1 Amazon CloudFront — 표준 배포 — NW.websocket: 지원(모든 배포에서 자동 활성). 유휴 10분이면 끊김 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:142 | 1.1 Amazon CloudFront — 표준 배포 — NW.availability: 글로벌 엣지(애니캐스트 아님, DNS 기반 — 추론). 업타임 SLA는 flat-rate F | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:144 | 1.1 Amazon CloudFront — 표준 배포 — NW.security: AWS WAF 웹 ACL 연결(`web_acl_id`), 상시 DDoS 보호(Shield Stand | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:171 | UseOriginCacheControlHeaders는 **쿠키 전부를 캐시 키에 포함** → 오리진이 캐시 가능한 응답에 `Set-Cookie`를 붙이면 그 Set-Cookie가  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:175 | 오리진 keep-alive 기본 5초: 오리진(ALB 60초 등) 유휴 타임아웃보다 짧으므로 기본값은 안전(추론). 키울 때는 오리진 유휴 타임아웃보다 작게. | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:199 | CKV_AWS_305 "Ensure CloudFront distribution has a default root object configured"(API 전용 배포에선 오탐 가능  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:248 | 1.2 Google Cloud CDN — 전역 외부 A — NW.cost_floor: Cloud CDN 자체 고정비 없음. 전제인 전역 포워딩 규칙 첫 5개 $0.025/시간(≈  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:251 | 캐시 egress(Asia Pacific, 홍콩 포함, 서울 사용자 해당 — 추론): 0–10 TiB $0.09/GiB, 10–150 TiB $0.06, 150–1,000 TiB  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:298 | 1.3 Google Media CDN — — NW.layer: 미디어·대용량 다운로드용 엣지 캐시(EdgeCacheService). Cloud CDN과 별개 제품, ALB 불필요( | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:312 | 프로젝트 활성화가 영업 경유라 원클릭 배포 경로에 부적합(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:333 | 1.4 Cloudflare CDN — 프록시, Free — NW.body_size: **업로드 최대 Free 100 MB / Pro 100 MB / Business 200 MB / | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:340 | 1.4 Cloudflare CDN — 프록시, Free — NW.availability: 글로벌 애니캐스트 | 표 출처 칸 비어 있음 |
| capabilities/10-network-edge-egress.md:360 | "Cache Everything" + Edge TTL override(Ignore cache-control)를 사이트 전체에 걸면 `private` 응답이 캐시되고 `Set-Coo | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:366 | SSL Flexible이면 오리진 구간 평문 + 오리진이 HTTPS 리다이렉트하면 무한 리다이렉트(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:410 | 개인화 응답에 `set-cookie`나 `private`가 있으면 안전하게 미캐시. 반대로 캐시하려던 응답에 미들웨어가 쿠키를 붙이면 영영 MISS(문서: 헤더를 전역 미들웨어 대 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:439 | 응답의 `Set-Cookie` 처리 문서 확인 못 함 → `미확인`. 함수 응답을 캐시할 때 쿠키 응답은 `private` 명시 필요(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:465 | `Surrogate-Control`은 Fastly가 소비하고 하류(브라우저)에 전달 안 하는 용도(문서 예시). CloudFront·Cloudflare로 옮기면 `s-maxage` | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:470 | `no-store`만 보내고 `private`를 빼면 Fastly가 캐시할 가능성(추론) → 개인화 응답은 `private, no-store` 둘 다. | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:488 | 2.1 Amazon Route 53 — 공개 호스팅 영 — NW.layer: 권한 DNS(이름 해석만). 요청 데이터 경로 밖, 프록시 아님 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:494 | 2.1 Amazon Route 53 — 공개 호스팅 영 — NW.draining: 해당 없음 (DNS 변경 후 옛 IP로 가는 트래픽은 TTL 동안 지속 → 옛 엔드포인트는 최소  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:499 | 2.1 Amazon Route 53 — 공개 호스팅 영 — NW.scaling: 관리형(쿼리 처리 증설 불필요, (추론)). API는 계정당 초당 5요청 제한 → 레코드 많은 Te | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:503 | 2.1 Amazon Route 53 — 공개 호스팅 영 — NW.dns: **TTL**: 비별칭 레코드는 TTL 필수, 권장 범위 60~172,800초. 헬스 체크 대상 레코드는  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:505 | 2.1 Amazon Route 53 — 공개 호스팅 영 — NW.private_connectivity: 사설 호스팅 영역(VPC 연결)으로 VPC 안 이름 해석. 사설 영역 쿼리  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:516 | 별칭(무료·apex 지원·대상 IP 자동 추적)은 Route 53 고유 확장. 다른 DNS로 옮기면 apex는 Cloudflare CNAME flattening 또는 Cloud D | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:525 | 헬스 체커는 서울 리전에서 출발하지 않음, 사설 IP 체크 불가. 보안 그룹·WAF가 Route 53 헬스 체커 IP를 막으면 정상 서버가 비정상 판정 (추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:567 | 2.2 Google Cloud DNS — 공개/비공개 — NW.scaling: 관리형. 쿼리 처리 증설 불필요 (추론) | 표 출처 칸 비어 있음 |
| capabilities/10-network-edge-egress.md:625 | 2.3 Cloudflare DNS — 무료 권한 DNS — NW.scaling: 관리형 (추론). LB 한도: 비엔터프라이즈 LB 20, 풀 20, 엔드포인트 20 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:629 | 2.3 Cloudflare DNS — 무료 권한 DNS — NW.dns: **프록시 레코드 TTL = Auto(300초), 변경 불가**. DNS-only: 60초(비엔터프라이즈) | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:645 | DNS-only 레코드로 웹 서비스하면 원본 IP 공개 → 원본 보안 그룹을 Cloudflare IP로 제한하는 설계가 무력화 (추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:646 | CNAME flattening "모든 CNAME" 켜면 제3자 도메인 검증용 CNAME(ACM 검증 CNAME 포함 가능성)이 CNAME으로 응답되지 않아 검증 실패 → **ACM | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:651 | Terraform 리소스: v5 이름은 `cloudflare_dns_record` (, 원문 github.com/cloudflare/terraform-provider-cloudfl | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:664 | 서울 리전: 글로벌(근거 없음, (추론)) | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:668 | 2.4 도메인 등록 기관 기본 DNS — Route — NW.layer: 권한 DNS(경로 밖) | 표 출처 칸 비어 있음 |
| capabilities/10-network-edge-egress.md:670 | 2.4 도메인 등록 기관 기본 DNS — Route — NW.health_check: Route 53 Domains·Cloudflare Registrar는 각자 DNS(2.1·2. | 표 출처 칸 비어 있음 |
| capabilities/10-network-edge-egress.md:671 | 2.4 도메인 등록 기관 기본 DNS — Route — NW.routing: Squarespace: 단순 레코드만 (추론) | 표 출처 칸 비어 있음 |
| capabilities/10-network-edge-egress.md:687 | 등록 기관 DNS에는 헬스 체크 기반 장애 조치·별칭이 없음 (추론) → F1 짧음이면 부적합 판정. | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:692 | 요구에 따라 반드시 명시할 속성: `aws_route53domains_registered_domain.name_server` → 위임 대상 영역 NS (인자 이름 (추론), 미확인 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:735 | 같은 계열: Google Cloud Armor(3.4·3.5), Cloudflare WAF(3.6), Vercel Firewall(3.7). 앞단 CDN을 Cloudflare로 두 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:743 | CloudFront 뒤 ALB의 WAF 레이트 규칙**은 forwarded IP 없이 쓰면 CloudFront 엣지 IP 단위로 집계 → 다수 사용자가 한 키로 묶여 정상 사용자  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:747 | Terraform 문서 `request_body` 블록 설명의 "Applicable only when scope is ..." 문구가 api_gateway(CLOUDFRONT)·c | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:817 | "Shield가 있으니 DDoS 안전"은 L3/L4 한정. HTTP 요청 폭주는 ALB까지 그대로 도달해 LCU·컴퓨트 비용이 늘 수 있음(추론, Standard에는 비용 보호 없 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:859 | Cloud Armor Enterprise Annual(월 $3,000·1년, 청구 보호·DDoS 대응 지원, 3.5), Cloudflare Enterprise(3.6). 소규모 앱 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:863 | Terraform `aws_shield_subscription`은 1년 약정 결제를 일으킴. 삭제해도 약정은 남음(추론, 문서상 `skip_destroy`·`auto_renew`만 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:879 | 서울 리전: 있음(추론: 백엔드 보안 정책은 글로벌/리전 외부 ALB에 붙으며 리전 정책은 리전 LB와 같은 리전. 가격 페이지에 리전별 차등 없음) | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:894 | 3.4 Google Cloud Armor — Stand — NW.scaling: 정책·규칙 수는 쿼터 한도(값 미확인) | 표 출처 칸 비어 있음 |
| capabilities/10-network-edge-egress.md:902 | 3.4 Google Cloud Armor — Stand — NW.cost_floor: 정책 $0.006849315/시간(≈월 $5, 추론 ×730), 규칙 $0.001369863/ | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:905 | 정책 ≈$5/월, 규칙 ≈$1/월(시간 요율 ×730, 추론), 요청 $0.75/100만(글로벌 정책) 또는 $0.60/100만(리전 정책). 데이터 처리 요금 없음. 봇 관리는  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:941 | 서울 리전: 있음(추론, Standard와 같은 LB 범위; 가격 리전 차등 없음) | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:972 | AWS Shield Advanced(3.3, 월 $3,000·1년), Cloudflare Enterprise(3.6). 단일 프로젝트 소규모면 Standard + 수동 레이트 규칙 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:984 | 배포 후 검증: `gcloud compute project-info describe --format='value(cloudArmorTier)'` → `CA_ENTERPRISE_PA | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:992 | 3.6 Cloudflare WAF·DDoS — Free — NW.layer: 역방향 프록시(오렌지 구름) 위 WAF·DDoS. **DDoS는 모든 플랜 L3~L7 무제한·무과금 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1001 | 3.6 Cloudflare WAF·DDoS — Free — NW.client_ip: WAF·레이트 규칙 IP 키 = `ip.src`(Cloudflare에 접속한 클라이언트 IP). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1004 | 3.6 Cloudflare WAF·DDoS — Free — NW.availability: 글로벌 애니캐스트(추론) | 표 출처 칸 비어 있음 |
| capabilities/10-network-edge-egress.md:1010 | 3.6 Cloudflare WAF·DDoS — Free — NW.regions: 글로벌 | 표 출처 칸 비어 있음 |
| capabilities/10-network-edge-egress.md:1052 | 3.7 Vercel Firewall — Hobby / — NW.availability: 글로벌(추론) | 표 출처 칸 비어 있음 |
| capabilities/10-network-edge-egress.md:1061 | Cloudflare(3.6)를 앞에 두면 Vercel이 XFF를 덮어써 클라이언트 IP가 Cloudflare IP가 됨 → Vercel 레이트 리밋 IP 키가 무력화(추론, NW. | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1104 | Cloudflare 등 외부 DNS에서 검증 CNAME을 프록시/flatten하면 검증 실패 가능 (추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1139 | 4.2 Google Certificate Manager — NW.regions: Certificate Manager 한도: Google 관리형 1000/프로젝트, 리전 관리형 10 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1181 | 4.3 Let's Encrypt + cert-manag — NW.dns: DNS-01: 클러스터가 DNS API(Route 53·Cloud DNS·Cloudflare) 쓰기 권한  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1183 | 4.3 Let's Encrypt + cert-manag — NW.cost_floor: 인증서 무료 (cert-manager 오픈소스, 클러스터 자원만) — Let's Encrypt | 표 출처 칸 비어 있음 |
| capabilities/10-network-edge-egress.md:1190 | ACM ACME 엔드포인트(유료, 45일)도 ACME 클라이언트로 사용 가능 — cert-manager `server`만 바꾸면 (추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1253 | 5.1 AWS NAT Gateway — 존 모드, 퍼블 — NW.websocket: 외부로 연 장시간 연결(웹소켓 클라이언트, DB, gRPC 스트림)은 350초 유휴 규칙만 적용 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1256 | 5.1 AWS NAT Gateway — 존 모드, 퍼블 — NW.draining: 드레이닝 개념 없음. EIP 교체·NAT 교체 시 기존 연결 끊김 (추론) | 표 출처 칸 비어 있음 |
| capabilities/10-network-edge-egress.md:1273 | 예: AZ 2개, 월 100 GB 처리 → 2 × $43.07 + 100 × $0.059 + 2 × $3.65 = 약 $99.3 + 인터넷 아웃 전송료 (추론, 계산). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1313 | 5.2 AWS NAT Gateway — 리전 모드 — NW.idle_timeout: 리전 모드 별도 값 문서 없음 → 존 모드와 같은 350초로 추정 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1315 | 5.2 AWS NAT Gateway — 리전 모드 — NW.websocket: 5.1과 같음(추론) | 표 출처 칸 비어 있음 |
| capabilities/10-network-edge-egress.md:1334 | 존 모드 NAT를 AZ마다 둔 것과 시간 요금은 같다(AZ 수 × $0.059). 퍼블릭 서브넷·라우트 관리 비용이 줄어드는 대신 **자동 IP 추가 시 EIP 요금 증가**(추론 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1340 | 자동 모드 + 외부 IP 허용 목록 = 위험**: AZ 확장·포트 부족 시 EIP가 추가되어 허용 목록 밖 IP로 나갈 수 있음(autoScalingIps). 허용 목록 요구(E1 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1341 | 새 AZ로 확장까지 최대 60분 동안 교차 AZ 처리 → AZ 간 전송료·지연 (추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1377 | 시간 요금 = 인스턴스 + IPv4. NAT GW 대비 월 약 $35~40 절감(AZ당), 처리 요금 없음 (추론, 계산). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1419 | 5.4 Google Cloud NAT — Public — NW.cost_floor: 게이트웨이 **$0.0014 × 사용 VM 수/시간(32대 이상은 $0.044/시간 상한)**  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1422 | 시간 요금(사용 VM 수 비례, 상한 $0.044) + GiB 처리 요금 + NAT IP 시간 요금 + 인터넷 전송료. AWS NAT(AZ당 월 $43)보다 소규모에서 훨씬 쌈 ( | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1433 | Cloud Run 커넥터 경로: NAT 포트는 커넥터 인스턴스(VM) 단위로 할당되는 것으로 보임(추론; 문서는 Direct VPC 경우만 명시). 커넥터 인스턴스 수가 적으면 포 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1481 | 5.5.2 AWS Lambda — VPC 사설 서브넷 — NW.scaling: 동시 실행 수 × 실행당 외부 연결 ≤ 55,000 × EIP 수(같은 목적지) (추론, 5.1 식  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1493 | 5.5.3 ECS Fargate — 사설 서브넷 + N — NW.egress: 태스크마다 ENI 1개. 퍼블릭 서브넷이면 태스크 ENI에 **공인 IP 선택 할당**(태스크별·자동 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1498 | 함정: 퍼블릭 IP 방식은 태스크 수만큼 IP가 다르고 재배포마다 바뀜 → 허용 목록 불가 (추론). Checkov `CKV_AWS_333` "Ensure ECS services  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1574 | 5.6 퍼블릭 IPv4 주소 요금 및 IPv6 대안 — NW.layer: 공인 IPv4 주소 자원(EIP, 자동 할당 퍼블릭 IP, GCP 외부 IP) | 표 출처 칸 비어 있음 |
| capabilities/10-network-edge-egress.md:1610 | 6.1 AWS VPC 엔드포인트 — Gateway — NW.idle_timeout: 미확인 (게이트웨이 엔드포인트 고유 유휴 타임아웃 문서 없음) | 표 출처 칸 비어 있음 |
| capabilities/10-network-edge-egress.md:1627 | 6.1 AWS VPC 엔드포인트 — Gateway — NW.regions: 리전별. 서울 사용 가능 (추론: 서울 AmazonVPC 오퍼 파일에 엔드포인트 항목 존재, 게이트웨이는 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1636 | GCP 대응: Private Google Access(서브넷 단위) (추론, 이 절에서 확인 안 함). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1676 | 6.2 AWS VPC 엔드포인트 — Interface — NW.tls: 엔드포인트는 TLS를 종단하지 않음. 사설 DNS를 켜면 공용 이름 그대로 써서 서비스 인증서와 이름이 일치 | 표 출처 칸 비어 있음 |
| capabilities/10-network-edge-egress.md:1677 | 6.2 AWS VPC 엔드포인트 — Interface — NW.client_ip: AWS 서비스는 사설 IP·`aws:SourceVpce`로 식별(엔드포인트 경유 시 `aws:So | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1693 | 비교: NAT Gateway 서울 $0.059/시간(월 $43.07, AZ당) + $0.059/GB. 2 AZ NAT = 월 $86.14 고정. (추론) 엔드포인트 4개 이하·2A | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1699 | GCP 대응: Private Service Connect(Google API 대상), Private Google Access (추론, 이 절에서 미확인). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1703 | VPC `enable_dns_hostnames`·`enable_dns_support`가 꺼져 있으면 사설 DNS가 동작하지 않는다(aws_vpc 기본 `enable_dns_host | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1741 | 6.3 AWS PrivateLink — 엔드포인트 서비 — NW.websocket: 해당 없음(L4 통과라 TCP 위 웹소켓은 전달, 유휴 350초 적용) (추론) | 표 출처 칸 비어 있음 |
| capabilities/10-network-edge-egress.md:1757 | 6.3 AWS PrivateLink — 엔드포인트 서비 — NW.cost_floor: 제공자: 엔드포인트 서비스 자체 시간 요금 없음(추론: Price List에 같은 리전 서비스 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1765 | VPC 피어링([PL] 서울 `APN2-VpcPeering-Out-Bytes` $0.01/GB, 시간 요금 없음, CIDR 겹치면 불가 (추론)), Transit Gateway($ | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1766 | GCP 대응: Private Service Connect(게시 서비스/소비자 엔드포인트) (추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1769 | 제공자 앱 로그·레이트 리밋이 NLB 사설 IP만 본다 → 클라이언트별 제한·감사 로그가 무력화. 프록시 프로토콜 v2를 켜면 백엔드가 그 헤더를 반드시 파싱해야 함(안 하면 연결 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1772 | DB용 NLB의 TCP 유휴를 350초보다 늘리면 교차 리전 접근 불가, 소비자 쪽 엔드포인트 350초 고정과도 겹쳐 결국 350초가 상한 (추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1811 | 6.4 AWS Lambda VPC 연결 — Hyperp — NW.client_ip: VPC 안 대상(RDS 등)이 보는 출발지 = Hyperplane ENI 사설 IP(서브넷 대역 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1817 | 6.4 AWS Lambda VPC 연결 — Hyperp — NW.dns: VPC의 Route 53 Resolver 사용 (추론: 문서 직접 인용 미확인) → 사설 호스팅 영역·인터 | 표 출처 칸 비어 있음 |
| capabilities/10-network-edge-egress.md:1824 | Lambda 요금(요청·GB-초)은 VPC 연결과 무관(추론: 가격 페이지에 VPC 연결 단가 없음). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1829 | Lambda를 VPC 밖에 두고 RDS를 공개(TLS+IP 제한) — F5에서 비권장 (추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1830 | Data API(Aurora `rds-data` 인터페이스 엔드포인트 또는 공용 HTTPS)로 VPC 연결 없이 질의 (추론, 서비스 이름 `com.amazonaws.region. | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1840 | Function URL은 VPC 연결과 무관하게 공용 → "VPC 안에 넣었으니 비공개" 판정은 틀림. 사설 진입은 Lambda 인터페이스 엔드포인트+Invoke API 또는 사설 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1856 | `aws ec2 describe-network-interfaces --filters Name=interface-type,Values=lambda Name=vpc-id,Values= | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1892 | 고정비: 인스턴스 수 × 머신 요금(시간). 최소 인스턴스 2 고정, 확장 후 줄지 않으므로 **실제 고정비 = 지금까지 도달한 최대 인스턴스 수 × 단가**. (추론) 트래픽 급 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1904 | IPv6 불가: IPv6 전용 목적지(예: Supabase 직접 연결 기본 IPv6)로 가는 경로에 커넥터를 쓰면 안 됨(추론: private-ranges-only면 외부 목적지는 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1923 | 서울 리전: 있음(추론: 제한 사항에 리전 제약 문구 없음, Cloud Run이 asia-northeast3 지원. 인스턴스 쿼터는 "100-200, depending on sel | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1945 | 6.6 Google Direct VPC egress — — NW.regions: 리전 제약 문구 없음(추론: Cloud Run 리전 전부). 쿼터만 리전별 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1965 | 서브넷 크기 계산: 최대 인스턴스 N이면 정상 상태 2N, 리비전 교체 중 최대 4N(구·신 동시) + 16개 블록 단위. /26(64개)은 **최대 인스턴스 약 16 이하**에서 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1978 | `connector`와 `network_interfaces`는 택일(추론: 원문에 두 방식이 별도 설명). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1979 | `template.scaling.max_instance_count` ≤ Direct VPC 쿼터, 서브넷 크기 ≥ 4 × max(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:1989 | 서울 리전: 있음(추론: 리전 제약 문구 없음. PlanetScale이 asia-northeast3 서비스 연결을 공개 — 6.10) | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:2016 | 서비스 연결 정책 자동화(Cloud SQL·Memorystore)도 소비자 쪽에 PSC 엔드포인트가 생기므로 같은 단가가 적용된다고 봄(추론: 가격표 목차에 "service con | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:2019 | 구글 API 사설 접근만이면 PSC 엔드포인트 대신 서브넷의 Private Google Access(무료, 추론)로 충분한 경우가 많다. 서버리스는 Direct VPC/커넥터 +  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:2033 | 구글 API: `gcloud compute forwarding-rules list --filter target="(all-apis OR vpc-sc)" --global`(공식 명령 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:2057 | 6.8 Cloud SQL 사설 IP 연결 — PSA / — NW.egress: 해당 없음(앱 쪽은 6.5/6.6). 공인 IP + authorized networks 방식은 클라이 | 표 출처 칸 비어 있음 |
| capabilities/10-network-edge-egress.md:2064 | PSC: 엔드포인트 ≈$7.30/월 + GiB당 $0.01. 자동 엔드포인트(서비스 연결 정책)도 엔드포인트 요금 적용(추론). | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:2074 | CKV_GCP_6은 `ssl_mode = "TRUSTED_CLIENT_CERTIFICATE_REQUIRED"`일 때만 통과**(SQL Server는 `ENCRYPTED_ONLY`) | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:2123 | 6.9 Memorystore 사설 연결 — Redis — NW.cost_floor: 연결 자체: Redis PSA·직접 피어링 무료(PSA 연결 무료 근거). Valkey PSC  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:2143 | `google_memorystore_instance`: `desired_auto_created_endpoints { network, project_id }`(구 `desired_p | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:2147 | `gcloud network-connectivity service-connection-policies list --region=asia-northeast3`(추론: 명령 형식 미열 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:2201 | 요청 경로(사용자 → DNS → CDN·WAF → LB·인그레스 → 앱 → 출구 NAT / 사설 연결 → 데이터·외부 API) 위에서 이웃한 구성 요소끼리 성립해야 하는 조건이다. | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:2232 | 5. **오리진 keep-alive 방향**: CDN의 오리진 keep-alive(CloudFront 5초, Cloudflare Proxy Idle 900초) < 오리진 LB/앱  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:2239 | 12. **인증 헤더 요청**: `Authorization` 헤더를 쓰는 API는 Vercel·GCP(응답이 public/s-maxage 아니면)에서 캐시 안 됨 → C4 "읽기  | 명시적 표시(추론·출처 미확인 등) |
| capabilities/10-network-edge-egress.md:2304 | 3. **Direct VPC 서브넷 크기**: 서브넷 주소 수 ≥ max(64, 4 × Cloud Run `max_instance_count` + 16)(추론: 2× 정상, 리비전 | 명시적 표시(추론·출처 미확인 등) |
| capabilities/README.md:204 | 생성 원칙(조사에서 나옴): Terraform·플랫폼 기본값은 콘솔보다 위험한 경우가 많으므로 핵심 속성은 항상 명시한다. Checkov가 다루지 않는 리소스는 plan JSON을 | 출처 없이 일반화 |

## 8. 지식 베이스 점검 (엔진이 이미 쓰는 값)

이 절이 가장 중요하다. 아래 값과 항목은 이미 엔진(S1)이 쓰고 있다. 최종 규칙으로 다시 판정하고, 쓸 수 없는 기본값은 `knowledge/defaults.yaml`에서 지웠다.

### 8.1 defaults.yaml (16개 → 8개)

| # | 대상 · 키 = 값 | 근거가 된 조사 문서의 주장 | 그 주장의 출처 (최종 등급) | 판정 | 조치 |
|---|---|---|---|---|---|
| 1 | k8s Deployment `terminationGracePeriodSeconds` = 30 | "The default terminationGracePeriodSeconds setting is 30 seconds." (09:1381, defaults.yaml에 URL 직접 기재) | kubernetes.io (A) | 적격 | 유지 |
| 2 | k8s CronJob `concurrencyPolicy` = Allow | considerations/03:803, capabilities/03:1070 "Allow (default)" | kubernetes.io (A) | 적격 | 유지 |
| 3 | terraform `aws_db_instance.backup_retention_period` = 0 | capabilities/06:294 Registry 기본값 `0`과 AWS 문서 "API·CLI 생성 시 1일"이 [충돌] | hashicorp/aws provider (A)와 AWS RDS 문서 (A)가 서로 다름 | 확정 불가 | **삭제** |
| 4 | terraform `aws_db_instance.multi_az` = false | 인용된 capabilities/06에 `multi_az` 기본값을 말하는 문장이 없다 | 없음 | 근거없음 | **삭제** |
| 5 | terraform `aws_db_instance.storage_encrypted` = false | capabilities/06:300 "기본 `false`", 06:938 | hashicorp/aws provider (A: Terraform, provider 자신의 인자 기본값) | 적격 | 유지 |
| 6 | uvicorn `timeout_keep_alive` = 5 | capabilities/09:1368 "Default: 5" | uvicorn.dev (A: 기준 4) | 적격 | 유지 |
| 7 | gunicorn `keepalive` = 2 | capabilities/09:1369 "Default: 2" | gunicorn.org (A: 기준 4) | 적격 | 유지 |
| 8 | Node.js http `keep_alive_timeout` = 5 | capabilities/09:1370 "Default: 5000 (5 seconds)." | nodejs.org (A) | 적격 | 유지 |
| 9 | Spring Boot 내장 Tomcat `keep_alive_timeout` = 60 | capabilities/09:1375 "Boot 기본값 명시는 없음 → 60초로 추론" | tomcat.apache.org (A: ASF)지만 Boot 값은 추론 | 근거없음(추론) | **삭제** |
| 10 | AWS ALB `idle_timeout` = 60 | capabilities/09:123 "The default is 60 seconds." | docs.aws.amazon.com (A) | 적격 | 유지 |
| 11 | GCP 클래식 ALB(GKE Ingress) `backend_timeout` = 30 | capabilities/09:667 | docs.cloud.google.com (A) | 적격 | 유지 |
| 12 | nginx `proxy_read_timeout` = 60 | capabilities/09:1090 | nginx.org (C: 최종 규칙 미충족, §5.3) | 부적격 | **삭제** |
| 13 | nginx `proxy_send_timeout` = 60 | capabilities/09:1090 | nginx.org (C) | 부적격 | **삭제** |
| 14 | nginx `proxy_connect_timeout` = 60 | capabilities/09:1090 | nginx.org (C) | 부적격 | **삭제** |
| 15 | nginx `client_max_body_size` = 1m | capabilities/09:1093 | nginx.org (C) | 부적격 | **삭제** |
| 16 | nginx `keepalive_timeout` = 75 | capabilities/09:1089 | nginx.org (C) | 부적격 | **삭제** |

**결과: 유지 8, 삭제 8(#3 A끼리 충돌, #4 근거없음, #9 추론, #12~16 nginx.org 부적격).** 삭제한 키는 S1이 더 이상 `defaulted: true` 값으로 채우지 않는다. 설정 파일에 값이 명시된 경우만 기록된다. nginx 5개 삭제는 §5.3의 판정(nginx.org를 C로 봄)에 따른 것이라, 사용자가 nginx를 A로 받아들이면 되돌리면 된다.

### 8.2 components/catalog.yaml (59개 항목)

catalog 항목은 ID·이름·`source` 파일만 가진다(능력 값은 계획 3에서 채움). 그래서 "그 항목이 기대는 주장"은 `source` 파일 안에서 그 구성 요소를 기술한 절 전체다. 능력 근거가 적격이 아닌 항목(근거 절의 출처가 C, 근거 절 없음, 핵심 주장이 출처 없음)에는 `recommendable: false`와 짧은 `reason`을 달았다. 항목은 catalog에 남는다(S1이 현재 상태로는 계속 보고한다). `infrafit kb lint`는 `recommendable`이 불리언인지, `false`면 `reason`이 있는지 검사한다. 표의 recommendable 칸 `—`는 필드가 없다는 뜻(추천 가능)이다.

| catalog ID | 근거 절 (파일:줄) | 인용 줄 수 A / C | ⚠️출처부적격 / ⚠️근거없음 | recommendable | 판정 |
|---|---|---|---|---|---|
| `ds:local/sqlite/default` | 01:63–96 | 15 / 1 | 1 / 1 | — | 적격; Django로 SQLite 문법을 말한 1줄은 C; 근거없음 1줄 |
| `ds:local/sqlite/wal` | 01:97–130 | 5 / 1 | 1 / 2 | — | 적격; better-sqlite3 1줄은 C; 근거없음 2줄 |
| `ds:unspecified/postgresql/default` | 01:199–229, 772–785 | 17 / 0 | 0 / 3 | — | 적격; 근거없음 3줄 |
| `ds:unspecified/mysql/default` | 01:772–785, 653–685 | 14 / 0 | 0 / 3 | — | 적격; 일반 MySQL 절 없음(§5.1 엔진 기준값·§3.1로 셈); 근거없음 3줄 |
| `ds:unspecified/mongodb/default` | 02:340–378, 379–415 | 30 / 1 | 1 / 5 | — | 적격; 자체 운영 절 없음(Atlas 절로 셈), Prisma 1줄은 C; 근거없음 5줄 |
| `ds:supabase/postgres/unspecified-plan` | 01:484–511, 512–543 | 19 / 0 | 0 / 1 | — | 적격; 근거없음 1줄 |
| `ds:firebase/firestore/standard` | 02:61–113 | 17 / 0 | 0 / 0 | — | 적격 |
| `ds:aws/rds-postgres/single-az` | 01:230–261 | 10 / 0 | 0 / 1 | — | 적격; 근거없음 1줄 |
| `ds:aws/rds-postgres/multi-az-instance` | 01:262–294 | 4 / 0 | 0 / 0 | — | 적격 |
| `ds:gcp/cloudsql-postgres/single` | 01:392–422 | 9 / 0 | 0 / 1 | — | 적격; 근거없음 1줄 |
| `ds:gcp/cloudsql-postgres/ha` | 01:423–452 | 3 / 0 | 0 / 1 | — | 적격; 근거없음 1줄 |
| `ca:local/process-memory/default` | 03:138–170 | 7 / 6 | 4 / 0 | — | 적격; B1 핵심(express-session MemoryStore 비공유)은 Express(A). express-rate-limit·lru-cache·Flask-Caching·connect-redis 세부는 C |
| `ca:unspecified/redis/default` | 03:257–286 | 9 / 0 | 0 / 0 | — | 적격; Valkey A |
| `ca:aws/elasticache/node-based` | 03:287–317 | 11 / 0 | 0 / 0 | — | 적격 |
| `ca:gcp/memorystore/redis` | 03:376–404, 405–432 | 16 / 0 | 0 / 0 | — | 적격 |
| `qu:unspecified/redis-streams/default` | 03:811–836 | 6 / 0 | 0 / 1 | — | 적격; KEDA A; 근거없음 1줄 |
| `qu:lib/bullmq/default` | 03:837–868 | 0 / 5 | 5 / 3 | false | 근거 절이 BullMQ 문서(C)에만 기댐; 근거없음 3줄 |
| `qu:lib/celery/default` | 03:869–898 | 0 / 4 | 4 / 3 | false | 근거 절이 Celery 문서(C)에만 기댐; 근거없음 3줄 |
| `qu:aws/sqs/standard` | 03:597–626 | 8 / 0 | 0 / 0 | — | 적격; KEDA A |
| `sc:local/in-process/default` | 03:229–254 | 0 / 1 | 1 / 3 | false | 근거가 APScheduler·node-cron·Celery 문서(C)와 출처 없는 값뿐; 근거없음 3줄 |
| `sc:k8s/cronjob/default` | 03:1063–1084 | 4 / 0 | 0 / 0 | — | 적격 |
| `sc:vercel/cron/unspecified-plan` | 03:1129–1151 | 4 / 0 | 0 / 0 | — | 적격 |
| `sc:github/actions-schedule/default` | 03:1196–1217 | 3 / 0 | 0 / 1 | — | 적격; 근거없음 1줄 |
| `rt:lib/socketio/no-adapter` | 03:1220–1241 | 0 / 2 | 2 / 1 | false | 근거 절이 Socket.IO 문서(C)에만 기댐; 근거없음 1줄 |
| `rt:lib/socketio/redis-adapter` | 03:1242–1268 | 0 / 2 | 2 / 2 | false | 근거 절이 Socket.IO 문서(C)에만 기댐; 근거없음 2줄 |
| `rt:lib/ws/default` | 03 문서에 `ws` 절 없음 | — | — | false | 조사 문서에 ws 절이 없음 |
| `fs:local/container-disk/default` | 03:200–228 | 4 / 0 | 0 / 2 | — | 적격; 근거없음 2줄 |
| `fs:aws/s3/default` | 03:1427–1454 | 7 / 0 | 0 / 1 | — | 적격; 근거없음 1줄 |
| `fs:gcp/gcs/default` | 03:1455–1479 | 6 / 0 | 0 / 1 | — | 적격; 근거없음 1줄 |
| `fs:supabase/storage/default` | 03:1505–1529 | 5 / 0 | 0 / 0 | — | 적격 |
| `cp:vercel/functions/unspecified-plan` | 04:115–157, 158–193, 194–227 | 58 / 0 | 0 / 4 | — | 적격; 근거없음 4줄 |
| `cp:netlify/functions/unspecified-plan` | 04:266–306, 307–341 | 30 / 2 | 2 / 4 | — | 적격; 웹소켓 미지원 2줄은 커뮤니티 포럼(C); 근거없음 4줄 |
| `cp:fly/machines/default` | 04:708–747 | 0 / 18 | 18 / 3 | false | 근거 절이 Fly.io 문서(C)에만 기댐; 근거없음 3줄 |
| `cp:render/web/unspecified-plan` | 04:637–670, 671–707 | 0 / 34 | 34 / 1 | false | 근거 절이 Render 문서(C)에만 기댐; 근거없음 1줄 |
| `cp:railway/service/unspecified-plan` | 04:525–563, 564–597, 598–631 | 50 / 0 | 0 / 6 | — | 적격; Railway A(SO 2025); 근거없음 6줄 |
| `cp:k8s/deployment/unspecified-cluster` | 05 문서에 일반 쿠버네티스 절 없음 | — | — | false | 조사 문서에 일반 쿠버네티스 절이 없음 |
| `cp:aws/eks/unspecified` | 05:713–752, 753–790, 791–827, 828–864 | 50 / 0 | 0 / 15 | — | 적격; Karpenter A; 근거없음 15줄 |
| `cp:gcp/gke/unspecified` | 05:597–636, 637–674, 675–712 | 49 / 0 | 0 / 12 | — | 적격; 근거없음 12줄 |
| `cp:local/compose/default` | 05:901–938, 939–974 | 16 / 0 | 0 / 19 | — | 적격; 근거없음 19줄 |
| `cp:docker/container/unspecified-host` | 05 문서에 일반 컨테이너 절 없음 | — | — | false | 조사 문서에 일반 컨테이너 절이 없음 |
| `cp:gcp/cloud-run/unspecified` | 05:125–166, 167–209 | 39 / 0 | 0 / 5 | — | 적격; 근거없음 5줄 |
| `cp:aws/ecs/unspecified` | 05:322–362, 363–402, 403–441 | 48 / 0 | 0 / 7 | — | 적격; 근거없음 7줄 |
| `cp:aws/ec2/docker-compose` | 05:901–938 | 8 / 0 | 0 / 9 | — | 적격; 근거없음 9줄 |
| `nw:app/uvicorn/default` | 09:1368 | 1 / 0 | 0 / 0 | — | 적격; uvicorn A(기준 4) |
| `nw:app/gunicorn/default` | 09:1369 | 1 / 0 | 0 / 0 | — | 적격; gunicorn A(기준 4) |
| `nw:app/node-http/default` | 09:1370 | 1 / 0 | 0 / 0 | — | 적격 |
| `nw:app/next-start/default` | 09:1371 | 1 / 0 | 0 / 0 | — | 적격 |
| `nw:app/flask-dev/default` | 09:1380 | 1 / 0 | 0 / 0 | — | 적격 |
| `nw:app/django-runserver/default` | 09:1373 | 1 / 0 | 0 / 0 | — | 적격 |
| `nw:app/spring-boot-tomcat/default` | 09:1375 | 1 / 0 | 0 / 1 | false | Spring Boot 기본 keep-alive 값이 조사 문서의 추론(출처 없음); 근거없음 1줄 |
| `nw:proxy/nginx/default` | 09:1083–1119 | 0 / 5 | 5 / 4 | false | 근거 절이 nginx.org(최종 규칙 미충족, C)에 기댐; 근거없음 4줄 |
| `nw:aws/alb/default` | 09:116–198 | 16 / 1 | 1 / 2 | — | 적격; Checkov 1줄은 C; 근거없음 2줄 |
| `nw:gcp/classic-alb/gke-ingress` | 09:659–703 | 15 / 0 | 0 / 1 | — | 적격; 근거없음 1줄 |
| `nw:k8s/ingress-nginx/default` | 09:956–1006 | 10 / 0 | 0 / 5 | — | 적격; 근거없음 5줄 |
| `nw:vercel/edge-proxy/default` | 09:1210–1233 | 7 / 0 | 0 / 2 | — | 적격; 근거없음 2줄 |
| `nw:netlify/edge-proxy/default` | 09:1234–1256 | 6 / 0 | 0 / 1 | — | 적격; 근거없음 1줄 |
| `nw:fly/proxy/default` | 09:1333–1361 | 0 / 8 | 8 / 3 | false | 근거 절이 Fly.io 문서(C)에만 기댐; 근거없음 3줄 |
| `nw:render/proxy/default` | 09:1286–1307 | 0 / 6 | 6 / 2 | false | 근거 절이 Render 문서(C)에만 기댐; 근거없음 2줄 |
| `nw:railway/proxy/default` | 09:1308–1332 | 12 / 0 | 0 / 1 | — | 적격; Railway A(SO 2025); 근거없음 1줄 |

**요약.** `recommendable: false` 14개: 근거 출처가 C인 것 9개(`qu:lib/bullmq`, `qu:lib/celery`, `sc:local/in-process`, `rt:lib/socketio/no-adapter`, `rt:lib/socketio/redis-adapter`, `cp:fly/machines`, `cp:render/web`, `nw:fly/proxy`, `nw:render/proxy`), nginx.org 판정에 따른 것 1개(`nw:proxy/nginx`), 근거 절이 없는 것 3개(`rt:lib/ws`, `cp:k8s/deployment/unspecified-cluster`, `cp:docker/container/unspecified-host`), 핵심 값이 추론인 것 1개(`nw:app/spring-boot-tomcat`). 이전 B 의존이던 `cp:railway/service`, `nw:railway/proxy`, `nw:app/uvicorn`, `nw:app/gunicorn`은 A가 되어 추천 가능으로 남았다. 근거없음 줄이 많은 절(`cp:local/compose/default` 19줄, `cp:aws/eks/unspecified` 15줄, `cp:gcp/gke/unspecified` 12줄)은 핵심 능력 값이 A 출처에 있어 표시하지 않았다.

### 8.3 signatures/*.yaml — 출처 없는 가정 (보고만, 파일은 고치지 않음)

시그니처에는 `source`·`ref` 필드가 없다. 각 시그니처는 catalog 항목 하나로 이어지므로 능력 판정은 §8.2를 따른다. 시그니처 자체가 깔고 있는 사실 주장 중 적격 출처가 없는 것:

| 파일 · ID | 시그니처가 깔고 있는 사실 주장 | 출처 (최종) | 판정 |
|---|---|---|---|
| datastores.yaml · SIG-DS-MYSQL | "MariaDB는 MySQL 호환이라 MySQL 구성 요소로 본다"(주석) — MariaDB JDBC 드라이버·`jdbc:mariadb://`를 MySQL로 분류 | 조사 문서에 MariaDB 절·인용 없음 | 근거없음 |
| realtime.yaml · SIG-RT-WS | `ws` 의존성 → `rt:lib/ws/default` | 03 문서에 `ws` 절 없음 | 근거없음 |
| realtime.yaml · SIG-RT-SOCKETIO | `socket.io`·`@socket.io/redis-adapter` → Socket.IO 구성 요소 | Socket.IO 문서 (C) | 부적격 |
| queue.yaml · SIG-QU-BULLMQ, SIG-QU-CELERY | 패키지 → BullMQ·Celery 구성 요소 | BullMQ·Celery 문서 (C) | 부적격 |
| scheduler.yaml · SIG-SC-INPROC | `node-cron`·APScheduler 등 → 앱 프로세스 안 스케줄러 | APScheduler·node-cron 문서 (C) | 부적격 |
| datastores.yaml · SIG-DS-SQLITE / SIG-DS-POSTGRES / SIG-DS-MYSQL / SIG-DS-MONGO | 패키지 이름이 그 DB의 드라이버라는 사실(`better-sqlite3`, `postgres`=postgres.js, `pg`, `psycopg`, `asyncpg`, `mysql2`, `pymysql`, `aiosqlite`, `mongoose`, `motor` 등) | capabilities/01 §5.2 드라이버 표의 드라이버 문서는 모두 C(better-sqlite3, node-sqlite3, postgres.js, node-postgres, psycopg, asyncpg, mysql2, PyMySQL, aiosqlite). `motor`·`mongoose`·`mysqlclient`·`sqlite-jdbc`·Spring JDBC URL은 조사 문서에 인용 없음 | 부적격 또는 근거없음 |
| cache.yaml · SIG-CA-SESSION-EXPRESS-MEMORY | express-session 기본 MemoryStore → 프로세스 메모리 | express-session 저장소(Express, A) | 적격 |
| 나머지 (SIG-CA-REDIS, SIG-DS-SUPABASE, SIG-DS-FIRESTORE, SIG-QU-SQS, SIG-SC-K8S-CRONJOB, SIG-SC-VERCEL-CRON, files.yaml 등) | 코드 패턴 → 구성 요소 연결 | 연결된 catalog 항목의 절 | §8.2 판정을 따른다 |
| watchlist.yaml | 패키지 목록만 있고 사실 주장 없음 | — | 해당 없음 |
| external.yaml | 패키지·환경변수·호스트 이름 → 외부 서비스(Anthropic, OpenAI, Stripe, 토스페이먼츠 등) 연결 | `source`·`ref` 없음, 조사 문서 인용 없음 | 근거없음(패키지 정체에 대한 주장) |

`knowledge/deploy.yaml`(CI 배포 명령 → 컴퓨트)과 `knowledge/implicit_routes.yaml`(프레임워크 암묵 라우트, 예: FastAPI 문서 화면 경로)도 `source`·`ref`가 없고 조사 문서를 인용하지 않는다. 프레임워크 기본 라우트 같은 사실 주장을 담고 있으므로 같은 기준이면 근거없음이다.

### 8.4 images.yaml — 출처 없는 가정 (보고만, 파일은 고치지 않음)

`images.yaml`에는 `source`·`ref` 필드가 없다. 이미지 이름 → 역할·구성 요소 연결은 설계 규칙이지만, 몇몇 연결은 사실 주장을 깔고 있다.

| 항목 | 깔고 있는 사실 주장 | 판정 |
|---|---|---|
| `nginx`, `nginx-unprivileged`, `openresty` → `nw:proxy/nginx/default` | 이 이미지들이 nginx 기본값을 그대로 가진다 | nginx.org는 C(§5.3), 나머지 두 이미지는 조사 문서 인용 없음 → 부적격·근거없음 |
| `postgis`, `timescaledb*`, `pgvector/*` → `ds:unspecified/postgresql/default` | PostgreSQL 능력을 그대로 가진다 | postgis·timescaledb는 근거없음, pgvector는 C(pgvector 저장소) |
| `valkey`, `valkey-cluster`, `redis-stack*`, `redis-cluster`, `redis-sentinel` → `ca:unspecified/redis/default` | Redis(자체 운영) 능력을 그대로 가진다 | valkey는 A(valkey.io·Docker Hub valkey, SO 2025), 나머지는 근거없음 |
| `cloud-sql-proxy` 등 → `hosting_hint: ds:gcp/cloudsql-postgres/single` | 이 프록시가 있으면 Cloud SQL이다 | 근거없음(판단은 S2·S3에 맡긴다고 적혀 있어 힌트로만 쓰임) |
| 그 밖의 역할 분류(infra, dev-tool, queue) | 구성 요소 능력과 연결되지 않음 | 해당 없음 |

## 9. 문제 영역 요약

1. **컴퓨트 티어 0.** Railway는 A가 됐지만 Render·Fly.io·Replit·Koyeb 절은 C에만 기댄다(capabilities/04의 ⚠️출처부적격 116줄). 엔진 catalog의 `cp:fly`, `cp:render`와 같은 플랫폼 프록시 항목은 `recommendable: false`다.
2. **서드파티 데이터·큐·실시간 서비스.** Neon·Upstash·PlanetScale·Turso·Convex·Appwrite·Pinecone·Prisma·BullMQ·Celery·Socket.IO 문서가 모두 C라서 capabilities/01·02·03·06·07의 해당 절은 쓸 수 없다.
3. **배포·릴리스와 데이터 정합성의 패턴 출처.** martinfowler.com·microservices.io·12factor.net(§4), 결제 항목의 Stripe·토스페이먼츠(§5.3·§5.2)가 C라서 considerations/03·04의 해당 항목은 쓸 수 없다.
4. **근거 없는 판정 값.** capabilities/10(근거없음 줄이 가장 많음), 09, 05(ops_burden "(평가)"), 08("(추론)" 처방)에 출처 없는 값이 몰려 있다.
5. **지식 베이스.** defaults.yaml에서 8개를 지웠다(§8.1). catalog 14개 항목은 `recommendable: false`다(§8.2). nginx 판정(§5.3)과 Istio·OPA 판정(§5.1)은 사용자가 뒤집을 수 있다.

## 10. 정정 (2026-10-02, 컨트롤러)

- nginx·Grafana·Stripe를 C로 내린 §5.3 판정을 되돌린다. 세 발행처는 사용자가 확인한 A 목록에 있었고, 최종 규칙은 B 발행처를 나누려고 만든 것이지 기존 A를 다시 내리라는 지시가 아니었다.
  - §5.3 표의 34줄 중 이 판정으로 붙은 30줄의 ` ⚠️출처부적격`을 지웠다(4줄은 다른 이유로 이미 붙어 있었으므로 그대로).
  - 엔진 쪽 변경(nginx 기본값 5개 삭제, `nw:proxy/nginx` 추천 불가 표시, f1 골든)은 되돌렸다.
  - §5.4의 "이전 A가 Stripe뿐인 줄"이 ⚠️출처부적격이 된 경우는 개별로 다시 보지 않았다. Stripe에 관한 주장만 있는 줄은 표시를 지워도 된다.
- Istio·OPA Gatekeeper의 CNCF graduated 여부를 cncf.io/projects에서 확인했다(둘 다 graduated). A 유지.
- 이 정정으로 §3 집계는 nginx 13·Grafana 17·Stripe 29건이 다시 A가 된 만큼 달라진다(A 3,588, C 704).
