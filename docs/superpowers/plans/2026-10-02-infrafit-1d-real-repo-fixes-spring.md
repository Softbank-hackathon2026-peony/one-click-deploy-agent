# infrafit 계획 1d: 실제 저장소에서 드러난 탐지 오류 수정과 Spring 지원 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 실제 저장소 12개에 S1을 돌려 드러난 오류를 고친다. (1) 리버스 프록시·서드파티 이미지를 앱 워크로드로 잡지 않는다. (2) 엔드포인트 추출의 누락·오탐(테스트 파일, 루트 앱, Fastify 플러그인, Flask `add_url_rule`)을 고친다. (3) Spring Boot(Java/Kotlin, Gradle/Maven)를 지원한다.

**Architecture:** 이미지 분류 지식은 코드가 아니라 `knowledge/images.yaml`에 둔다. 워크로드 종류에 `reverse-proxy`를 더해 엔드포인트 배정·사용 주체 추측에서 뺀다. JVM 의존성은 `group:artifact` 이름으로 기존 `Manifests`에 넣어 기존 시그니처 엔진을 그대로 쓴다.

**Tech Stack:** Python 3.12, uv, PyYAML, jsonschema, python-hcl2, crossplane, pytest

**Spec:** `docs/superpowers/specs/2026-10-01-infrafit-design.md` (§2 원칙, §3 지식 베이스, §6 S1)

**선행:** 계획 1·1b·1c가 `feat/infrafit-plan1`에 구현되어 있다.

## Global Constraints

- 계획 1·1b·1c의 Global Constraints를 모두 따른다(스키마 검증 후 쓰기, 결정성과 정렬, 근거는 실제 파일의 실제 줄, 판단이 필요한 사실은 `candidate`, 네트워크는 `git clone`뿐, 문서·주석 한국어, 커밋 영어, 커밋 끝에 `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`).
- 픽스처·실제 저장소의 기대 출력을 어디에도 적지 않는다. 테스트는 `tmp_path` 합성 저장소로 규칙을 검증한다. 골든은 마지막 작업에서 스크립트로만 다시 만든다. 작업 사이에는 골든·스키마 예시 테스트만 실패할 수 있다.
- 탐지 지식(이미지 분류, 시그니처)은 `knowledge/` YAML에 둔다. 출력의 구성 요소 ID는 카탈로그에 있는 것만 쓴다. 카탈로그에 없으면 `unmapped`로 남긴다. 카탈로그에 새 ID를 더할 때는 `docs/research/capabilities/` 문서를 출처로 단다.
- `uv run infrafit kb lint` 0개 문제를 유지한다.

---

### Task 1: 리버스 프록시·서드파티 이미지 분류

**Files:** Create `knowledge/images.yaml`; Modify `infrafit/kb.py`, `infrafit/kb_lint.py`, `infrafit/detect/workloads.py`, `infrafit/detect/endpoints.py`, `infrafit/detect/components.py`, `infrafit/detect/paths.py`, `schemas/infrafit.schema.json`; Test `tests/test_images.py`

**규칙**

이미지 분류 지식
1. `knowledge/images.yaml`: 항목마다 `match`(이미지 이름 패턴 목록: 레지스트리·태그·다이제스트를 뗀 마지막 이름 또는 `저장소/이름`에 대한 fnmatch), `role`(`reverse-proxy` | `datastore` | `cache` | `queue` | `infra` | `dev-tool`), 선택 `component`(카탈로그 ID), 선택 `hosting_hint`(카탈로그 ID, 함께 쓰인 저장소의 호스팅 후보). 기존 `INFRA_IMAGE_TOKENS`의 내용을 이 파일로 옮긴다. 최소 항목: nginx·nginx-unprivileged·openresty(reverse-proxy, `nw:proxy/nginx/default`), caddy·traefik·haproxy·envoy(reverse-proxy, component 없음), postgres(datastore, `ds:unspecified/postgresql/default`), mysql·mariadb, mongo, redis·valkey(cache, `ca:unspecified/redis/default`), memcached, rabbitmq, temporalio/*(infra), cloud-sql-proxy(infra, hosting_hint `ds:gcp/cloudsql-postgres/single`), minio, localstack·mailhog·mailpit·adminer·pgadmin·dpage/pgadmin4(dev-tool). 카탈로그에 없는 component는 쓰지 않는다.
2. `kb.images()` 로더와 `kb lint` 검사(필수 키, role 값, component·hosting_hint가 카탈로그에 있는지).

워크로드
3. compose 서비스·k8s 워크로드의 이미지(또는 빌드 Dockerfile 마지막 FROM)가 `reverse-proxy`로 분류되면 워크로드 종류 `reverse-proxy`(스키마 enum에 추가). 그 외 분류(`datastore`, `cache`, `queue`, `infra`, `dev-tool`)면 워크로드가 아니다.
4. 분류된 compose 서비스 중 `datastore`/`cache`/`queue`는 같은 component의 데이터 범위가 있으면 그 범위의 근거에 compose 줄을 더한다. 없으면 새 데이터 범위를 `status: candidate`로 만든다. `used_by`는 그 서비스를 `depends_on`(목록·맵 형식)하는 앱 워크로드, 없으면 사용 주체 규칙(규칙 7) 그대로. `infra`는 component가 있으면 `current_components`에 candidate로, 없으면 `unmapped`에 `image:<이름>`과 compose 줄 근거로 남긴다. `hosting_hint`가 있으면 `unmapped`에 `hosting-hint:<id>`를 그 compose 줄 근거로 남긴다(호스팅 판단은 S2·S3 몫). `dev-tool`은 무시한다.
5. k8s·compose에서 앱 워크로드(종류가 `reverse-proxy`가 아닌 것)가 하나도 없으면 코드 탐지(`_from_code`)도 실행해 합친다.
6. 그래도 앱 워크로드가 없으면, 어떤 워크로드에도 연결되지 않은 Dockerfile 중 마지막 체인에 CMD나 ENTRYPOINT가 있고 마지막 FROM이 reverse-proxy 이미지가 아니며 `.devcontainer/` 아래가 아닌 것마다 워크로드를 `status: candidate`로 만든다. 이름은 Dockerfile 디렉터리 이름, 파일 이름이 `<x>.Dockerfile`/`Dockerfile.<x>`면 `<x>`. 종류는 `is_worker(이름, 명령)`이면 worker, 아니면 web. code_root는 빌드 컨텍스트 후보 규칙(1b F3)과 같은 방식으로 Dockerfile 디렉터리.
7. 이미지만 있는(빌드 없는) compose·k8s 앱 워크로드에 Dockerfile이 연결되지 않았고, 저장소에 어떤 워크로드에도 연결되지 않은 앱 Dockerfile(규칙 6의 조건)이 정확히 하나면 그것을 연결한다(code_root, 명령). 이렇게 정한 code_root로 배정한 엔드포인트는 `candidate`.

배정과 경로
8. 엔드포인트 배정(`_owners`, `_assign`)과 데이터 범위 `used_by` 추측에서 `reverse-proxy`·`static-frontend` 워크로드를 뺀다.
9. 요청 경로: `reverse-proxy` 워크로드는 nginx 해석(`ProxyServer`)이 있으면 1b 규칙 그대로, 없으면 앞 구간 + `reverse-proxy` 구간(component는 이미지 분류의 component, 없으면 `unmapped`, 설정은 기본값만).

**테스트(합성 저장소)**
- compose `web`(앱 이미지) + `nginx`(nginx:alpine, 설정 마운트) → nginx는 `reverse-proxy`, 엔드포인트는 web에 `confirmed`/`candidate` 규칙대로, 데이터 범위 used_by에 nginx 없음.
- compose가 temporal·cloud-sql-proxy·postgres만 있고 `docker/worker.Dockerfile`(CMD `node dist/workers/cloud.js`) → 워크로드 `worker`(worker, candidate), temporal은 unmapped, postgres 데이터 범위에 compose 근거.
- compose `postgres` + 앱 `depends_on: [postgres]`, 의존성 시그니처 없음 → postgres 데이터 범위 candidate, used_by 앱.
- 루트 Dockerfile 하나 + compose `web: image: registry/x:latest` → web에 Dockerfile 연결, 명령·code_root 채워짐.
- `.devcontainer/Dockerfile`, dev-tool 이미지는 무시.
- kb lint: 잘못된 role, 카탈로그에 없는 component를 잡는다.

**Commit:** `feat: classify proxy and third-party images and recover app workloads`

---

### Task 2: 엔드포인트 추출 수정

**Files:** Modify `infrafit/detect/endpoints.py`, `infrafit/detect/signatures.py`; Test `tests/test_endpoints_real.py`

**규칙**
1. 테스트 경로 제외: 경로 조각에 `tests`, `test`, `__tests__`, `e2e`, `spec`, `testing`이 있거나, 파일 이름이 `test_*.py`, `*_test.py`, `conftest.py`, `*.test.*`, `*.spec.*`, `*Test.java`, `*Test.kt`, `*Tests.java`, `*Tests.kt`인 파일은 엔드포인트 추출과 시그니처 `code` 조건 평가에서 뺀다(`src/test/` 포함). 판정 함수는 하나로 공유한다.
2. 루트 디렉터리 앱: `app_dir`/`code_root`가 `""`(저장소 루트)인 것도 유효한 뿌리다(`None`만 "모름"). 가장 깊은 뿌리 규칙(1b P4)은 그대로라서 하위 디렉터리 워크로드가 있으면 그쪽이 이긴다.
3. Express 계열 서버 변수: 기존 `_SERVER_VAR`에 더해, 파일이 속한 가장 가까운 `package.json`에 express·fastify·koa·hono·@koa/router 중 하나가 있으면, 함수 매개변수 이름이 `app`, `router`, `server`, `fastify`, `instance`, `api`인 것도 서버 변수로 본다(`function x(fastify, opts)`, `async (fastify) =>`, `export default async function (app)` 등). `X.route({ method: 'GET', url: '/x' })`(method가 문자열 또는 문자열 배열) 형태도 추출한다.
4. 프레임워크 이름: Express 계열 추출 결과의 `framework`를 그 파일의 가장 가까운 `package.json` 의존성으로 정한다(fastify, koa, hono, express 순으로 있는 것). 없으면 `express`.
5. Flask `add_url_rule`: `X.add_url_rule("/r", ...)`(첫 인자 문자열 상수, `methods=[...]` 키워드, 없으면 GET)를 데코레이터 라우트와 같은 규칙으로 추출한다. X의 Blueprint `url_prefix`와 `register_blueprint(url_prefix=)` 연결(1b 작업 1)도 같이 적용한다.

**테스트(합성 저장소)**
- `tests/test_x.py` 안의 FastAPI 앱 라우트는 나오지 않는다. 시그니처 code 조건도 테스트 파일에서 일치하지 않는다.
- compose `build: .`인 루트 앱의 엔드포인트가 `confirmed`.
- Fastify 플러그인 파일(`export async function routes(fastify) { fastify.get('/a', ...) }`) + `fastify.route({method:['GET','HEAD'], url:'/b'})` → `/a` GET, `/b` GET·HEAD, framework `fastify`.
- 의존성에 express가 없는 디렉터리의 `function f(app) { app.get(...) }`는 추출하지 않는다.
- Blueprint(url_prefix `/v1`) + `bp.add_url_rule("/x", view_func=f, methods=["POST"])` + `app.register_blueprint(bp, url_prefix="/api")` → `POST /api/v1/x`.

**Commit:** `fix: exclude tests, own root apps, and read fastify plugins and flask url rules`

---

### Task 3: Spring Boot 지원

**Files:** Modify `infrafit/detect/manifests.py`, `infrafit/detect/workloads.py`, `infrafit/detect/endpoints.py`, `infrafit/detect/paths.py`, `knowledge/signatures/*.yaml`, `knowledge/defaults.yaml`, `knowledge/components/catalog.yaml`; Test `tests/test_spring.py`

**규칙**

의존성
1. Gradle: `build.gradle`, `build.gradle.kts`에서 `implementation|api|runtimeOnly|compileOnly|annotationProcessor|kapt|developmentOnly|testImplementation|testRuntimeOnly`(`test*`는 건너뜀) 뒤의 `"g:a[:v]"`/`'g:a[:v]'`/`group: 'g', name: 'a'` 좌표를 `g:a` 이름으로 `Manifests.add`. `plugins { id("org.springframework.boot") }`·`id 'org.springframework.boot'`·`apply plugin: 'org.springframework.boot'`는 `org.springframework.boot` 이름으로 더한다. 줄 번호는 좌표가 있는 줄.
2. Maven: `pom.xml`의 `<dependency>`(scope `test` 제외)마다 `groupId:artifactId`, 줄은 artifactId 줄. `<parent>`가 `spring-boot-starter-parent`면 `org.springframework.boot`도 더한다.
3. 시그니처(`knowledge/signatures`): 카탈로그에 있는 component에만 JVM 의존성 조건을 더한다. 최소: Postgres(`org.postgresql:postgresql`), MySQL(`com.mysql:mysql-connector-j`, `mysql:mysql-connector-java`), MariaDB 계열은 MySQL 카탈로그 ID가 있으면 거기로, SQLite(`org.xerial:sqlite-jdbc`), Redis 캐시(`org.springframework.boot:spring-boot-starter-data-redis`), SQS(`software.amazon.awssdk:sqs`, `io.awspring.cloud:spring-cloud-aws-starter-sqs`). 설정 파일 조건: `**/application*.yml`·`**/application*.yaml`·`**/application*.properties`에서 `jdbc:postgresql://`, `jdbc:mysql://`, `jdbc:sqlite:`. 카탈로그에 없는 것(WebSocket/STOMP, Kafka, RabbitMQ 등)은 `watchlist.yaml`에 더해 `unmapped`로 보이게 한다.

워크로드
4. 빌드 파일 디렉터리마다, 의존성에 `org.springframework.boot:spring-boot-starter-web`이 있으면 web 워크로드(프레임워크 `spring-mvc`), `...-starter-webflux`면 web(`spring-webflux`), Spring Boot(`org.springframework.boot` 또는 `spring-boot-starter*`)만 있으면 worker(`candidate`). 이름은 `settings.gradle(.kts)`의 `rootProject.name`(루트 모듈) 또는 pom `artifactId`, 없으면 디렉터리 이름(루트면 `app`). code_root는 빌드 파일 디렉터리. 근거는 해당 의존성 줄. 다른 코드 워크로드와 같은 우선순위(`_from_code`)로 다룬다. 멀티 모듈이면 web 의존성이 있는 모듈마다 워크로드.
5. 명령: 연결된 Dockerfile(code_root 또는 이미지 규칙)의 마지막 체인 ENTRYPOINT+CMD, 없으면 비운다.

엔드포인트
6. `*.java`, `*.kt`(테스트 제외, 작업 2 규칙 1)에서 `@RestController` 또는 `@Controller`가 붙은 클래스를 찾는다. 클래스 `@RequestMapping`의 경로(인자 문자열, `value =`/`path =`, 배열 `{..}`/`[..]`)를 접두어로 쓴다. 메서드의 `@GetMapping`/`@PostMapping`/`@PutMapping`/`@DeleteMapping`/`@PatchMapping`(인자 없으면 `""`), `@RequestMapping(method = [RequestMethod.X, ...])`(method 없으면 `ANY`)를 라우트로 낸다. 경로가 여럿이면 각각. 경로 변수 `{id}`는 그대로. 결합은 기존 `_join`. 근거는 메서드 어노테이션 줄, framework는 워크로드 규칙 4의 프레임워크(모르면 `spring`).
7. 정규식 기반 파서로 충분하다: 클래스 선언 앞의 어노테이션 묶음과 메서드 선언 앞의 어노테이션 묶음을 순서대로 읽는다. 중첩 클래스·주석 안의 어노테이션은 처리하지 않아도 되지만 예외를 내면 안 된다.

요청 경로
8. 카탈로그에 `nw:app/spring-boot-tomcat/default`(이름 "Spring Boot 내장 Tomcat", 출처 `docs/research/capabilities/09-network-lb-ingress.md`)를 더하고, `knowledge/defaults.yaml`에 hop 기본값 `keep_alive_timeout` 60(같은 출처, Tomcat `keepAliveTimeout` = `connectionTimeout` 기본 60초)을 더한다.
9. `spring-mvc` 워크로드의 `app-server` 구간은 명령과 무관하게 `nw:app/spring-boot-tomcat/default`. `application*.yml|yaml|properties`의 `server.tomcat.keep-alive-timeout` 또는 `server.tomcat.connection-timeout`(앞이 우선; `20s`/`20000`(ms)/`PT20S` 형식을 초로)이 있으면 명시값과 그 줄 근거. 근거가 없으면 기본값, 구간 근거는 web 의존성 줄. `spring-webflux`는 `unmapped`.

**테스트(합성 저장소)**
- Kotlin Gradle(kts, plugins 블록, BOM 스타터, `rootProject.name`) + `@RestController @RequestMapping("/api/v1/users")` + `@GetMapping("/{id}")`, `@PostMapping` → 워크로드 이름·종류, `GET /api/v1/users/{id}`, `POST /api/v1/users`.
- Maven(pom, parent, test scope 제외) + Java `@RequestMapping(value = {"/a", "/b"}, method = RequestMethod.GET)` → 두 라우트.
- `org.postgresql:postgresql` + `spring-boot-starter-data-redis` → postgres·redis 데이터 범위. `application.yml`의 `jdbc:postgresql://`만 있어도 postgres.
- `application.yml`의 `server.tomcat.keep-alive-timeout: 20s` → app-server 구간 20(명시, 근거 줄). 없으면 60(기본값).
- `src/test/java`의 컨트롤러는 나오지 않는다.
- 깨진 pom/gradle 파일 → 예외 없음.

**Commit:** `feat: support spring boot gradle and maven projects`

---

### Task 4: 골든 갱신과 실제 저장소 재검증

- [ ] `uv run pytest`, `uv run infrafit kb lint` 통과. 골든·예시를 `scripts/update_golden.py`로 다시 만들고 픽스처별 변화를 작업 1~3 규칙으로 설명한다.
- [ ] 실제 저장소 12개(`/tmp/realrepos/*`)에 analyze + check-run을 다시 돌린다(예외 없음, 0개 문제).
- [ ] 독립 감사: 저장소 코드와 inventory를 대조해 틀린·빠진·가짜 사실을 다시 판정한다. 감사 결과는 대화에만 보고하고 저장소에 기대값으로 남기지 않는다.

**Commit:** `test: regenerate goldens after image classification, endpoint fixes and spring support`
