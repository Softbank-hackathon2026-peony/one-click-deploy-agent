# infrafit 계획 1b: 리버스 프록시 체인, 환경별 요청 경로, 라우터 접두어, 엔드포인트 공유 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 계획 1의 S1이 빠뜨린 네 가지를 채운다. (1) 컨테이너 안 리버스 프록시(nginx)를 요청 경로에 넣어 `LB → nginx → 앱 서버` 체인을 만든다. (2) kustomize overlay마다 환경을 기록하고 요청 경로를 환경별로 만든다. (3) FastAPI `include_router(prefix=…)`와 Flask `register_blueprint(url_prefix=…)` 접두어를 라우트에 붙인다. (4) 같은 코드를 실행하는 워크로드마다 엔드포인트를 기록하고, 프록시 라우팅으로 실제로 요청이 닿는지(`exposure`)를 표시한다.

**Architecture:** nginx 설정은 crossplane(nginxinc가 만든 nginx 설정 파서)으로 읽는다. 설정 파일과 워크로드의 연결, include 해석, `${VAR}` 치환, upstream 호스트 → 워크로드 해석은 모두 저장소에 있는 근거(Dockerfile COPY, compose 볼륨, k8s Service·ConfigMap, kustomize 렌더 결과)로만 한다. 근거가 없으면 해석하지 않고 미해석으로 남긴다.

**Tech Stack:** Python 3.12, uv, PyYAML, jsonschema, python-hcl2, crossplane, pytest

**Spec:** `docs/superpowers/specs/2026-10-01-infrafit-design.md` (§2 원칙, §6.2 엔드포인트, §6.6 요청 경로, §8.6 현재 요청 경로 검사, §9.8 환경 파생)

**선행:** 계획 1(`docs/superpowers/plans/2026-10-02-infrafit-1-foundation-s0-s1.md`)이 브랜치 `feat/infrafit-plan1`에 구현되어 있다. 판정 기록: `docs/superpowers/notes/2026-10-02-plan1-rulings-and-followups.md`.

## Global Constraints

- 계획 1의 Global Constraints를 모두 따른다(스키마 검증 후 쓰기, 결정성과 정렬, 범위 ID 형식 `^(w|ep|ds|svc|path)-[a-z0-9._-]+$`, 근거는 실제 파일의 실제 줄, 판단이 필요한 사실은 `candidate`, 네트워크는 `git clone`뿐, 문서·주석 한국어, 커밋 영어, 커밋 끝에 `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`).
- 픽스처의 기대 출력을 어디에도 적지 않는다. 테스트는 테스트 안에서 만든 합성 저장소(`tmp_path`)로 규칙을 검증한다. 픽스처 골든은 마지막 작업에서 `scripts/update_golden.py`로만 다시 만든다.
- 새 의존성은 `crossplane` 하나다(`uv add crossplane`). crossplane 호출은 항상 `crossplane.parse(path, single=True, check_ctx=False, check_args=False, comments=False)`로 한다. include는 crossplane이 따라가지 않게 하고(`single=True`) 이 계획의 규칙으로 직접 해석한다.
- 새 구성 요소 ID를 만들지 않는다. 리버스 프록시 구간은 카탈로그에 이미 있는 `nw:proxy/nginx/default`를 쓴다.

## 파일 구조

```
infrafit/detect/
  endpoints.py     수정: 라우터 접두어(작업 1), 공유 워크로드·exposure(작업 4)
  environments.py  신규: 환경 목록과 환경별 렌더 객체(작업 2)
  nginx.py         신규: nginx 설정 찾기·연결·파싱·upstream 해석(작업 3)
  paths.py         수정: 환경별 경로(작업 2), 프록시 체인(작업 4)
infrafit/stages/s1_inventory.py  수정: environments, 프록시 경로 조립
infrafit/consistency.py          수정: 새 필드 검사
schemas/infrafit.schema.json     수정: Inventory.environments, RequestPath.environment, Endpoint.exposure
knowledge/defaults.yaml          수정: nginx 구간 기본값
tests/test_endpoints_prefix.py, tests/test_environments.py, tests/test_nginx.py, tests/test_proxy_paths.py
```

---

### 작업 1: 라우터 접두어

**Files:** Modify `infrafit/detect/endpoints.py`; Test `tests/test_endpoints_prefix.py`

**Interfaces:**
- Consumes: `extract_endpoints(snap, workloads) -> list[dict]`(계획 1), 내부 `_python(snap)`, `_prefixes(tree)`.
- Produces: 같은 시그니처. 라우트에 include 접두어가 붙는다.

**규칙**
1. 한 파이썬 파일 안에서 `X.include_router(R, prefix="/p")`(FastAPI) 또는 `X.register_blueprint(R, url_prefix="/p")`(Flask)를 찾는다. 키워드 값이 문자열 상수일 때만 쓴다.
2. `R`이 이름(`router`)이면 같은 파일에서 그 이름에 붙은 데코레이터 라우트에 접두어를 붙인다.
3. `R`이 속성(`routes.router`)이면 같은 파일의 import로 모듈 파일을 찾는다. `from . import routes`, `from .routes import router`(이 경우 `R`은 이름), `from pkg import routes`, `import pkg.routes as routes`를 지원한다. 모듈 파일은 상대 import면 현재 파일의 디렉터리 기준, 절대 import면 현재 파일에서 위로 올라가며 `pkg/routes.py` 또는 `pkg/routes/__init__.py`가 있는 첫 위치로 찾는다. 못 찾으면 접두어를 적용하지 않는다.
4. 접두어는 연결된다. `app.include_router(api, prefix="/api")`이고 `api.include_router(users.router, prefix="/users")`이면 `users.router`의 라우트는 `/api/users…`다. 순환과 깊이 5 초과는 끊는다.
5. 라우터 자체의 `APIRouter(prefix=…)`/`Blueprint(url_prefix=…)` 접두어(계획 1)는 include 접두어 뒤에 붙는다.
6. 같은 라우터가 서로 다른 접두어로 두 번 include되면 접두어마다 엔드포인트를 하나씩 낸다.
7. 결합 시 `/`가 겹치거나 빠지지 않게 한다(`"/api" + "/x"`, `"/api/" + "/x"` → `/api/x`; 라우트가 `""`이면 접두어 그대로).

**테스트(합성 저장소)**
- 같은 파일 include(prefix) → 접두어가 붙는다.
- `from . import routes` + `app.include_router(routes.router, prefix="/api")` + `routes.py`의 `APIRouter(prefix="/users")` → `/api/users/…`.
- 2단 연결, 같은 라우터 두 번 include, 모듈을 못 찾는 경우(접두어 없이 기존 결과), Flask `register_blueprint`.
- 순환 include가 멈춘다.

**Commit:** `feat: apply include_router and register_blueprint prefixes to routes`

---

### 작업 2: 환경과 환경별 요청 경로

**Files:** Create `infrafit/detect/environments.py`; Modify `infrafit/detect/paths.py`, `infrafit/stages/s1_inventory.py`, `infrafit/consistency.py`, `schemas/infrafit.schema.json`; Test `tests/test_environments.py`

**Interfaces:**
- Consumes: `build_overlays`가 만든 `ParsedArtifact`(path `<leaf>/kustomization.yaml#build`, `parsed`, `objects`), `build_source`, `is_build_path`.
- Produces:
  - `infrafit.detect.environments.Environment` dataclass: `name: str`, `source: str`(kustomization.yaml 실제 경로), `rendered: bool`, `objects: list[dict]`(렌더 결과, 렌더 실패면 `[]`). `to_dict(snap)` → `{"name", "rendered", "source": Evidence}`.
  - `detect_environments(artifacts: list[ParsedArtifact]) -> list[Environment]` — 이름순 정렬.
  - `env_slug(name: str) -> str` — `/`를 `-`로, 나머지는 `workloads.slug` 규칙.
  - `workload_in(env: Environment, w: WorkloadInfo) -> bool`
  - `paths.build_paths(snap, workloads, artifacts, compute, environments, proxy=None) -> list[dict]` (`proxy`는 작업 4에서 채운다. 이 작업에서는 인자만 받는다.)

**규칙**
1. 환경 = kustomize 최종 overlay(`build_overlays`가 낸 `#build` 산출물) 하나. 이름은 leaf 디렉터리 경로에서 마지막 `overlays/`까지를 뗀 나머지다(`k8s/overlays/aws/prod` → `aws/prod`). 경로에 `overlays/`가 없으면 leaf 디렉터리 경로 전체다. 렌더에 실패한 leaf도 `rendered: false`로 목록에 넣는다(공백이 보이게).
2. 워크로드 `w`가 환경에 있다 = 렌더 객체 중 워크로드 종류(Deployment, StatefulSet, DaemonSet, Job, CronJob)의 `metadata.name`이 `w.name`과 같거나, 라벨 `app.kubernetes.io/name`이 `w.name`과 같다.
3. 요청 경로: 경로를 만드는 워크로드마다, 그 워크로드가 있는 렌더된 환경마다 경로 하나. `environment`는 환경 이름, id는 `path-<워크로드 이름 부분>.<env_slug>`. 로드밸런서 구간은 그 환경의 렌더 객체에 있는 Ingress만 본다. 엣지 구간(플랫폼 설정)은 환경과 무관하게 계획 1 규칙 그대로다.
4. 렌더된 환경 어디에도 없는 워크로드(코드·compose 워크로드, overlay가 없는 k8s)는 계획 1처럼 경로 하나, `environment: null`, id `path-<워크로드 이름 부분>`. 이때 로드밸런서 구간은 계획 1 규칙 그대로(모든 k8s 산출물, 경로 순 첫 Ingress)다.
5. 스키마:
   - `Inventory.environments`(필수): `{name: string, rendered: boolean, source: Evidence}` 배열.
   - `RequestPath.environment`(필수): `string` 또는 `null`.
6. 일관성 검사: 경로 id는 `environment`가 null이면 `path-<워크로드 id[2:]>`, 아니면 `path-<워크로드 id[2:]>.<env_slug(environment)>`와 같아야 한다. `environment`는 `environments[].name` 중 하나여야 한다. 환경 이름은 중복될 수 없다.

**테스트(합성 저장소, kustomize 렌더는 `runner`를 가짜로 바꾸거나 `Environment`를 직접 만들어서)**
- overlay 두 개(각자 다른 클래스의 Ingress) → 워크로드 경로 두 개, 각 경로의 로드밸런서가 자기 환경의 Ingress다.
- 한 overlay에만 있는 워크로드 → 그 환경 경로 하나.
- overlay가 없으면 `environments == []`, 경로 environment null(계획 1과 같은 결과).
- 렌더 실패 leaf → `rendered: false`, 그 환경 경로 없음.
- 일관성 검사: 잘못된 id, 없는 환경 이름, 중복 환경 이름을 각각 잡는다.

**Commit:** `feat: record kustomize environments and build request paths per environment`

---

### 작업 3: nginx 설정 읽기와 upstream 해석

**Files:** Create `infrafit/detect/nginx.py`; Modify `pyproject.toml`(crossplane); Test `tests/test_nginx.py`

**Interfaces:**
- Consumes: `Snapshot`, `ParsedArtifact`(dockerfile, compose, k8s), `WorkloadInfo`, `Environment`(작업 2), `artifacts._d`, `evidence`.
- Produces:
  - `ProxyRoute` dataclass:
    - `proxy: str`(프록시 워크로드 id), `environment: str | None`
    - `location: tuple[str, str]`(수식어 `""`,`=`,`~`,`~*`,`^~`,`@`, 패턴), `internal: bool`
    - `upstream: str`(proxy_pass의 호스트 부분 원문), `uri: str | None`(proxy_pass에 붙은 URI, 없으면 None)
    - `target: str | None`(해석된 워크로드 id, 못 하면 None), `status: str`(`confirmed`/`candidate`)
    - `subrequests: list[str]`(`auth_request` 대상 location 패턴)
    - `settings: list[dict]`(SettingFact, 근거 포함)
  - `ProxyServer` dataclass: `proxy`, `environment`, `settings`(server 단위), `locations: list[LocationInfo]`(선택 알고리즘용: 수식어, 패턴, `proxies: bool`, `internal`, 원래 순서)
  - `find_proxies(snap, workloads, artifacts, environments) -> tuple[list[ProxyServer], list[ProxyRoute]]` — 정렬해서 반환.

**규칙**

설정 파일 후보
1. 파일 이름이 `nginx.conf`, `*.conf`, `*.conf.template`, `*.conf.tmpl`이고 crossplane 파싱 상태가 `ok`이며 `server`, `upstream`, `location`, `proxy_pass` 중 하나를 포함하는 파일.

워크로드와 연결(경로 매핑 = 컨테이너 경로 → 저장소 경로)
2. Dockerfile: 워크로드의 Dockerfile(계획 1의 이미지 → Dockerfile 규칙, 또는 `code_root`의 Dockerfile)의 마지막 단계에서 `--from=`이 없는 `COPY`/`ADD`. 원본 경로는 빌드 컨텍스트 기준인데, 저장소 루트 기준과 Dockerfile 디렉터리 기준 중 스냅숏에 실제로 있는 쪽을 쓴다(둘 다 있으면 Dockerfile 디렉터리). 원본이 디렉터리면 아래 파일 전부, 대상이 `/`로 끝나고 원본이 파일이면 대상 + 파일 이름.
3. compose: 서비스의 `volumes` 중 `./x:/y` 형태의 바인드 마운트(compose 파일 디렉터리 기준). 이 서비스에 해당하는 워크로드(이름 같음)에 연결한다.
4. nginx 공식 이미지의 템플릿 규칙: 컨테이너 경로 `/etc/nginx/templates/X.template`은 `/etc/nginx/conf.d/X`로도 매핑한다.
5. 매핑으로 연결된 설정은 `confirmed`. 어떤 워크로드와도 연결되지 않은 설정이 있고 nginx 기반 워크로드(이미지나 Dockerfile 마지막 FROM에 `nginx` 포함)가 정확히 하나면 그 워크로드에 연결하고 `candidate`. 그 외는 연결하지 않는다.
6. 진입 설정: 연결된 파일 중 컨테이너 경로가 `/etc/nginx/nginx.conf`이거나 `/etc/nginx/conf.d/*.conf`(템플릿 매핑 포함)인 것. 그런 파일이 없으면 `server` 블록을 가진 연결 파일 전부.

include
7. `include` 인자(glob 허용)는 컨테이너 경로다. 상대 경로는 `/etc/nginx/` 기준이다. 같은 워크로드의 경로 매핑으로 저장소 파일을 찾아 그 자리에 펼친다(지시어 상속상 include 위치의 블록에 들어간 것으로 본다). 찾지 못한 include는 건너뛴다(런타임 생성 파일일 수 있다). 펼친 지시어의 근거는 원래 파일·줄이다. 깊이 10에서 끊는다.

location과 설정
8. `server` 블록마다 location 목록을 원래 순서로 모은다(중첩 location 포함). location의 실효 설정은 location → server → http 순으로 처음 나오는 값이다(nginx 상속). 대상 키: `proxy_read_timeout`, `proxy_send_timeout`, `proxy_connect_timeout`, `client_max_body_size`, `proxy_http_version`, `keepalive_timeout`. 시간 값은 초 단위 정수로 바꾼다(`15s`→15, `2m`→120, 단위 없음 → 초). 크기 값은 원문 문자열. upstream 블록의 `keepalive` 값은 `upstream_keepalive`로, 그 upstream으로 가는 route의 설정에 넣는다. 각 SettingFact의 `evidence`는 지시어가 있는 파일·줄이다.
9. `proxy_pass` 대상: `http(s)://NAME[:port][/uri]`. `NAME`이 같은 설정의 `upstream` 이름이면 그 upstream의 `server` 인자들(여러 개면 각각 route 하나), 아니면 `NAME[:port]` 자체가 호스트다. `uri`는 호스트 뒤 경로(없으면 None). 대상에 nginx 변수(`$x`)가 있으면 해석하지 않는다(`target` None).
10. `auth_request /X`가 있는 location은 `subrequests`에 `/X`를 기록한다.

`${VAR}` 치환(환경별)
11. 호스트 문자열의 `${VAR}`/`$VAR`(nginx 변수가 아닌 envsubst 형식은 `${…}`만)를 프록시 워크로드의 환경 변수로 치환한다. 우선순위(뒤가 이긴다): Dockerfile 마지막 단계 `ENV`(`ENV A=b C=d`, `ENV A b` 모두) → environment가 null이면 compose 서비스 `environment`(목록·맵) → 해당 환경 렌더 객체의 그 워크로드 컨테이너 `env[].value`와 `envFrom[].configMapRef` → 같은 렌더 결과의 ConfigMap `data`(이름은 렌더된 이름 그대로 비교). environment가 null이고 k8s 원문 산출물이면 원문 ConfigMap을 이름으로 찾는다. 치환하지 못한 변수가 남으면 `target` None.
12. 환경 목록이 있고 프록시 워크로드가 그 환경에 있으면(작업 2 규칙 2) 환경마다 route를 따로 만든다. 그 외는 environment null로 한 번 만든다.

호스트 → 워크로드
13. 포트를 뗀 호스트 이름 `h`로 찾는다. (a) 같은 환경(또는 null이면 원문 k8s 산출물)의 Service `metadata.name == h` → `spec.selector`가 비어 있지 않고 워크로드 객체의 pod template 라벨에 모두 들어 있는 워크로드. 여러 개면 id 순 첫 번째이고 `candidate`. (b) compose 서비스 이름 `h` → 같은 이름의 워크로드. (c) 이름이 `h`인 워크로드. (d) 못 찾으면 `target` None. (a)~(c)로 하나를 찾으면 `confirmed`(설정 연결이 `candidate`면 `candidate`).

**테스트(합성 저장소)**
- Dockerfile `COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template` + `COPY nginx/snippets/ /etc/nginx/snippets/` + 설정의 `include /etc/nginx/snippets/p.conf` → 스니펫의 `proxy_pass`와 `proxy_read_timeout`이 그 location의 route·설정으로 잡히고, 근거가 스니펫 파일 줄이다.
- `upstream u { server ${UP}; keepalive 16; }` + Dockerfile `ENV UP=a:80` → 환경 null에서 `a`로 해석, `upstream_keepalive` 16.
- 같은 설정, overlay 두 개에서 ConfigMap(envFrom)이 `UP`을 각각 `a:80`, `b:80`으로 덮어씀 → 환경마다 다른 target.
- Service selector → Deployment 라벨로 해석(Service 이름과 Deployment 이름이 다를 때).
- compose 바인드 마운트 `./nginx.conf:/etc/nginx/nginx.conf` + `proxy_pass http://api:8000` → compose 서비스 `api` 워크로드.
- 상속: server의 `proxy_read_timeout 30s`, location에서 덮지 않음 → 30. location에서 `5s`면 5.
- `proxy_pass http://u/internal/x;` → `uri == "/internal/x"`. `proxy_pass http://$backend;` → target None.
- 연결 안 된 설정 + nginx 기반 워크로드 하나 → `candidate`. 둘이면 연결 안 됨.
- 찾지 못하는 include, 깨진 설정 파일, include 순환이 예외 없이 처리된다.

**Commit:** `feat: parse nginx reverse proxy configs and resolve upstreams to workloads`

---

### 작업 4: 프록시 체인 경로, 공유 워크로드, exposure

**Files:** Modify `infrafit/detect/paths.py`, `infrafit/detect/endpoints.py`, `infrafit/stages/s1_inventory.py`, `infrafit/consistency.py`, `schemas/infrafit.schema.json`, `knowledge/defaults.yaml`; Test `tests/test_proxy_paths.py`

**Interfaces:**
- Consumes: 작업 2 `build_paths(..., environments, proxy)`, 작업 3 `find_proxies`, `ProxyRoute`, `ProxyServer`.
- Produces:
  - `paths.build_paths(snap, workloads, artifacts, compute, environments, proxy: tuple[list[ProxyServer], list[ProxyRoute]] | None)`
  - `endpoints.extract_endpoints(snap, workloads, routes: list[ProxyRoute] | None = None, servers: list[ProxyServer] | None = None)`
  - `endpoints.select_location(locations, request_path) -> LocationInfo | None` — nginx location 선택 알고리즘.

**규칙**

기본값
1. `knowledge/defaults.yaml`에 `artifact: hop`, `component: "nw:proxy/nginx/default"` 항목을 추가한다: `proxy_read_timeout` 60, `proxy_send_timeout` 60, `proxy_connect_timeout` 60, `client_max_body_size` `"1m"`, `keepalive_timeout` 75. 출처는 `{ref: docs/research/capabilities/09-network-lb-ingress.md}`. `infrafit kb lint` 0개 문제를 유지한다.

경로
2. 경로를 만드는 워크로드에 nginx 프록시 워크로드(작업 3에서 `ProxyServer`를 가진 워크로드)를 더한다(계획 1은 `web`만).
3. 프록시 워크로드 P의 경로(환경 E): P의 앞 구간(엣지·로드밸런서, 작업 2 규칙) + `reverse-proxy` 구간(component `nw:proxy/nginx/default`, 설정은 P의 server 단위 실효 설정 + 기본값, 근거는 설정 파일).
4. 대상 워크로드 T의 경로(환경 E): E(또는 null)에서 T를 target으로 하는 route가 있고 T 자신의 앞 구간이 E에서 없으면, 경로 = P의 앞 구간 + `reverse-proxy` 구간 + T의 `app-server` 구간. `reverse-proxy` 구간 설정은 T로 가는 route들의 실효 설정 + 기본값이다. 같은 키의 값이 route마다 다르면 값마다 SettingFact를 하나씩 두고 각자 근거를 단다(같은 값은 하나로 합친다). 정렬은 (key, 값의 문자열).
5. T로 가는 프록시가 여럿이면 프록시 워크로드 id 순 첫 번째를 쓴다. T 자신의 앞 구간(자기 Ingress)이 E에 있으면 계획 1·작업 2 규칙의 경로를 그대로 쓴다.
6. 경로 id와 environment는 작업 2 규칙 그대로다.

공유 워크로드
7. 핸들러 파일이 여러 web 워크로드의 `app_dir` 또는 `code_root` 아래에 있으면 그 워크로드마다 엔드포인트를 하나씩 낸다(근거로 정했으므로 `confirmed`). 이 조건에 맞는 워크로드가 없을 때만 계획 1의 점수·대체 규칙을 쓴다. 엔드포인트 id는 워크로드별 순번 규칙 그대로다.

exposure
8. 워크로드 W를 target으로 하는 route가 어느 환경에서든 하나라도 있으면 W의 엔드포인트마다 `exposure`를 정한다. 없으면 `exposure`를 쓰지 않는다.
9. 판정: 엔드포인트 라우트에서 매개변수(`{x}`, `:x`, `[x]`, `<x>`, `<int:x>`)를 `x1`로 바꾼 요청 경로 `r`을 만든다. 그 W를 target으로 하는 route를 가진 프록시의 각 server에서
   - `select_location(server.locations, r)`이 고른 location이 W로 proxy하고 `internal`이 아니며 `uri`가 None이면 → 닿음.
   - 고른 location이 `uri`를 가진 채 W로 proxy하면 → 전달 경로는 `uri` + (prefix location이면 `r`에서 location 접두어를 뗀 나머지, 아니면 없음)이고, 이 전달 경로가 엔드포인트 라우트(매개변수 치환 후)와 같은 W의 엔드포인트가 닿음.
   - 고른 location의 `subrequests`마다, 그 이름의 internal location이 proxy하는 대상·`uri`로 같은 방식의 전달 경로를 만들고 그 엔드포인트가 닿음.
   - 메서드는 보지 않는다.
   하나라도 닿으면 `routed`, 아니면 `not-routed`.
10. `select_location`은 nginx 규칙을 따른다: `=` 정확 일치가 있으면 그것. 아니면 가장 긴 접두어 일치를 기억하고, 그것이 `^~`면 그것. 아니면 정규식 location(`~` 대소문자 구분, `~*` 무시)을 설정 순서대로 검사해 첫 일치. 없으면 기억한 접두어. 명명 location(`@x`)과 internal location은 외부 요청 선택 대상이 아니다. 중첩 location은 바깥 location을 고른 뒤 그 안에서 같은 규칙을 다시 적용한다.
11. 스키마: `Endpoint.exposure`(선택): `"routed"` 또는 `"not-routed"`.
12. 일관성 검사: `reverse-proxy` 구간의 component가 카탈로그에 있어야 한다(기존 검사로 충분). 같은 (workload, method, route, handler.path, handler.line) 엔드포인트가 한 워크로드에 두 번 나오지 않는다.

**테스트(합성 저장소)**
- LB(Ingress → 프록시 Service) + nginx 프록시 + 앱 두 개(각자 upstream) → 앱 경로가 `load-balancer → reverse-proxy → app-server` 순서, 프록시 경로는 `load-balancer → reverse-proxy`.
- 같은 키의 값이 location마다 다를 때(`proxy_read_timeout` 15s와 60s) → 값마다 SettingFact, 각자 근거.
- 같은 code_root를 쓰는 워크로드 두 개 → 엔드포인트가 각각 나온다.
- exposure: `location /internal/ { return 404; }` + `location /api/ { proxy_pass http://a; }` → `/api/x`는 routed, `/internal/y`는 not-routed. `location = /_v { internal; proxy_pass http://b/internal/v; }` + `location /api/ { auth_request /_v; proxy_pass http://a; }` → b의 `/internal/v`는 routed, b의 다른 엔드포인트는 not-routed.
- `select_location`: `=` 우선, `^~` 우선, 정규식이 일반 접두어를 이김, 정규식 순서, 명명·internal 제외, 중첩.
- 프록시가 없는 저장소는 계획 1과 같은 엔드포인트·경로(exposure 없음).

**Commit:** `feat: chain request paths through reverse proxies and mark endpoint exposure`

---

### 작업 5: 골든 갱신과 실제 저장소 확인

**Files:** `fixtures/*/golden/*`, `schemas/examples/f2-sqlite-erp/*`(스크립트 산출물만)

- [ ] `uv run pytest`와 `uv run infrafit kb lint`가 통과한다.
- [ ] `uv run python scripts/update_golden.py`로 골든과 예시를 다시 만든다. 손으로 고치지 않는다.
- [ ] 보고서에 픽스처별 골든 diff 요약을 쓰고, 각 변화가 작업 1~4의 어느 규칙에서 나왔는지 적는다. 규칙으로 설명되지 않는 변화가 있으면 원인을 고친 뒤 다시 만든다.
- [ ] 외부 저장소 `/Users/jerry/Desktop/workspace/projects/softbank-hackerton/simple-web-app`(현재 HEAD)와 이 저장소 자체에 `uv run infrafit analyze … --out /tmp/plan1b --run-id a`, `check-run`을 돌려 예외 없음, 0개 문제를 확인한다.

**Commit:** `test: regenerate goldens after proxy and environment support`
