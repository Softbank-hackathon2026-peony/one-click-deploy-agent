# infrafit 계획 1e: 외부 서비스, 환경별 배포 대상, 배치·실시간·암묵 라우트 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. 시간 예산이 짧다: 작업 2개를 병렬로 구현하고, 리뷰는 마지막에 한 번만 한다.

**Goal:** S1 인벤토리가 담지 못하던 사실을 담는다. (1) 앱이 호출하는 외부 서비스(`external_services[]`). (2) 플랫폼 설정·CI 배포 워크플로를 환경으로 기록하고 compute를 (워크로드, 환경) 단위로 기록한다. (3) 배치·CLI 프로세스, 웹소켓 엔드포인트, 프레임워크가 자동으로 만드는 라우트를 규칙으로 추가한다.

**Spec:** `docs/superpowers/specs/2026-10-01-infrafit-design.md` (§2, §3, §6)

## Global Constraints

- 계획 1~1d의 Global Constraints를 모두 따른다(스키마 검증 후 쓰기, 결정성, 실제 근거 줄, 판단이 필요한 사실은 `candidate`, 탐지 지식은 `knowledge/` YAML, 카탈로그 ID만 출력, `kb lint` 0개, 네트워크는 `git clone`뿐, 문서·주석 한국어, 커밋 영어 + `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`).
- 기대 출력을 어디에도 기록하지 않는다. 테스트는 `tmp_path` 합성 저장소. 골든은 통합 뒤 스크립트로만 다시 만든다.
- 카탈로그에 새 ID를 더할 때는 `docs/research/capabilities/`에 그 구성 요소 절이 있어야 하고 그 문서를 출처로 단다. 없으면 `unmapped`와 label.

---

### Task 1: 외부 서비스와 환경별 배포 대상 (스키마 변경)

**외부 서비스**
1. `knowledge/signatures/external.yaml`: 항목마다 `id`(`ext:<slug>`), `label`, `kind`(`llm-api`|`auth`|`payments`|`messaging`|`email`|`push`|`maps`|`video`|`webhook`|`other`), `when.any`(기존 `dependency`, `code` 조건 + 새 `env` 조건: 환경변수 이름 정규식). `env` 조건은 `.env.example`·`.env.sample`·`.env.template`·`.env.*.example`의 키, compose `environment` 키, k8s `env[].name`, 코드의 `process.env.X`·`os.environ["X"]`·`os.getenv("X")`·`System.getenv("X")`·Spring `${X}`에서 이름을 찾는다. 최소 항목: Anthropic, OpenAI, Google Gemini(google-genai, @google/generative-ai), Supabase Auth(`auth.getUser|signInWith|auth.signUp` 또는 JWKS URL), Firebase(FCM, firebase-admin), Stripe, Toss Payments(`api.tosspayments.com`), Slack webhook(`hooks.slack.com`), Discord webhook(`discord.com/api/webhooks`), SendGrid, Resend, Twilio, Google Maps, YouTube Data API, Notion API. `kb lint`가 형식을 검사한다.
2. 스키마 `Inventory.external_services[]`(필수, 빈 배열 가능): `{id, label, kind, used_by: [워크로드 id], secrets: [환경변수 이름], evidence: [Evidence], status}`. `used_by`는 근거 파일이 code_root 아래에 있는 워크로드(데이터 범위 `used_by` 규칙과 같은 방식), 없으면 빈 배열. `secrets`는 그 항목의 `env` 조건에 맞은 이름. 의존성만으로 맞으면 `candidate`, 코드 사용이나 환경변수까지 맞으면 `confirmed`. 테스트 경로·보조 디렉터리 근거만으로는 만들지 않는다(1d 규칙과 같음).
3. 일관성 검사: `used_by`가 있는 워크로드인지, id 중복 없음.

**환경별 배포 대상**
4. 환경 `kind`에 `platform`, `ci-deploy`를 더한다. 
5. `platform` 환경: 플랫폼 설정 파일(vercel.json, netlify.toml, render.yaml, fly.toml, railway.json/toml, app.yaml(GAE), Procfile은 제외) 하나가 환경 하나. 이름은 `<플랫폼>`(루트) 또는 `<플랫폼>/<디렉터리>`. 멤버는 그 설정이 배포하는 워크로드: render.yaml은 서비스의 `rootDir`·`dockerfilePath`·`dockerContext`로 워크로드의 code_root/Dockerfile과 맞춘다. 그 외는 설정 파일 디렉터리가 code_root를 포함하는 워크로드(1b F2의 "k8s·compose 워크로드 제외" 규칙은 이 환경에는 적용하지 않는다). 멤버가 없으면 환경을 만들지 않는다.
6. `ci-deploy` 환경: `.github/workflows/*.yml`의 job step 중 배포 명령을 찾는다. 배포 패턴은 `knowledge/deploy.yaml`에 둔다: `match`(`run` 정규식 또는 `uses` 패턴), `compute`(카탈로그 ID 또는 `unmapped`+label), `target`(워크로드를 찾는 방법: `--source <dir>`, `--image <image>`, `-f <compose file>`, `dockerfile`/`context` 입력 등). 최소: `gcloud run deploy`, `google-github-actions/deploy-cloudrun`, `aws ecs update-service`·`aws-actions/amazon-ecs-deploy-task-definition`, `aws ssm send-command`(EC2, 같은 워크플로의 compose 파일), `fly deploy`·`superfly/flyctl-actions`, `vercel deploy`·`amondnet/vercel-action`, `railway up`, `kubectl apply`·`helm upgrade`. 워크플로 하나의 배포 step 하나가 환경 하나, 이름은 `ci/<워크플로 파일 stem>`(step이 여럿이면 `ci/<stem>/<job>`). 워크플로 `on`에 `push`·`release`·`schedule`·`workflow_run`이 없으면(수동 실행만) 환경의 `manual: true`. 대상 워크로드를 못 찾으면 그 환경의 멤버는 비우고 `unmapped`에 `deploy-target:<label>`.
7. 스키마: 환경 객체에 선택 필드 `manual: boolean`, `members: [워크로드 id]`(platform·ci-deploy만). `current_components[]`에 선택 필드 `environment`(환경 이름). platform·ci-deploy 환경의 멤버마다 compute 구성 요소를 `environment`와 함께 하나씩 기록한다(`status`: 설정·명령이 대상을 직접 가리키면 confirmed, 추측이면 candidate). 기존 환경 없는 compute 기록은 그대로 둔다.
8. 카탈로그: Cloud Run, ECS, EC2, Fly, Render, Railway, GAE 등 필요한 compute ID가 카탈로그에 없고 연구 문서(`docs/research/capabilities/04-*`, `05-*`)에 절이 있으면 더한다.
9. 일관성 검사: `current_components[].environment`와 `members`가 존재하는 이름·워크로드인지.

**테스트(합성 저장소)**: 외부 서비스(의존성만 → candidate, 의존성+env → confirmed, used_by, secrets), render.yaml + compose가 함께 있는 저장소(두 환경, compute 둘), `gcloud run deploy api --source server` 워크플로(수동 실행만 → manual), ECS·SSM 패턴, 대상 못 찾음 → unmapped.

**Commit:** 의미 단위로 여러 개.

---

### Task 2: 배치·CLI, 웹소켓, 암묵 라우트 (규칙만)

1. **배치·CLI 워크로드**: 저장소에 워크로드가 하나도 없을 때만, 테스트·보조 디렉터리가 아닌 곳의 진입점을 `candidate` 워크로드로 만든다: Python `if __name__ == "__main__":`가 있는 파일 또는 패키지 `__main__.py`, package.json `bin`, `pyproject` `[project.scripts]`. 종류는 GitHub Actions 워크플로 `on: schedule`이 그 진입점을 실행하면 `scheduled`(근거: cron 줄, 스케줄러 구성 요소는 카탈로그에 있으면 기록), 아니면 `worker`. 이름은 파일·스크립트 이름. 진입점이 여럿이면 디렉터리마다 하나(경로 순 첫 번째).
2. **웹소켓 엔드포인트**: Spring `registry.addEndpoint("/x")`(STOMP), `@ServerEndpoint("/x")`, FastAPI `@app.websocket`(이미 있음), socket.io 서버(`new Server(` / `io(` + `path` 옵션, 없으면 `/socket.io`)를 method `WEBSOCKET` 엔드포인트로 낸다. 그런 엔드포인트가 있는 web 워크로드는 종류를 바꾸지 않는다. 실시간 시그니처: Spring websocket starter + `@EnableWebSocketMessageBroker`/`enableSimpleBroker` → realtime 데이터 범위(카탈로그 ID가 없으면 unmapped label `spring-stomp-simple-broker`).
3. **암묵 라우트**: `knowledge/implicit_routes.yaml`에 프레임워크가 자동으로 만드는 라우트: FastAPI `/docs`, `/redoc`, `/openapi.json`(생성자에 `docs_url=None` 등이 있으면 해당 것 제외), Spring actuator(`/actuator/health`, `management.endpoints.web.base-path` 반영), springdoc(`/swagger-ui.html`, `/v3/api-docs`, `springdoc.*path` 반영), prometheus-fastapi-instrumentator `.expose(` → `/metrics`, @fastify/swagger `routePrefix`. 모두 `status: candidate`, framework는 해당 프레임워크, 근거는 의존성 줄 또는 설정·호출 줄, 그 프레임워크 워크로드에 배정.

**테스트(합성 저장소)**: 각 규칙마다 하나 이상, 워크로드가 있는 저장소에서 배치 규칙이 동작하지 않음.

**Commit:** 의미 단위로 여러 개.

---

### Task 3: 통합과 확인 (컨트롤러)

- 두 작업 브랜치를 합치고 충돌을 푼다. `uv run pytest`, `kb lint` 통과, 골든을 스크립트로 다시 만들고 변화를 규칙으로 설명한다.
- 실제 저장소 12개 analyze + check-run.
- 최종 리뷰 한 번, Critical·Important만 고친다.
