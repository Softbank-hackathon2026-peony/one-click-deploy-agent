# infrafit 계획 1c: compose 환경, 환경별 exposure, 다단 프록시 체인 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 계획 1b가 남긴 세 공백을 메운다. (1) docker compose 구성을 환경으로 기록해, k8s와 compose가 함께 있어도 compose의 요청 경로·프록시 해석이 남게 한다. (2) 엔드포인트 `exposure`를 환경별 값으로 바꾼다. (3) 프록시 뒤의 프록시를 따라가 요청 경로와 exposure를 끝까지 잇는다.

**Architecture:** `Environment`에 종류(`kustomize`/`compose`)를 더하고, compose 서비스를 근거 규칙으로 워크로드에 대응시킨다. 경로·프록시 해석·exposure는 모두 환경 단위로 계산한다. 다단 프록시는 "대상이 다시 프록시인 route"를 재귀로 따라간다.

**Tech Stack:** Python 3.12, uv, PyYAML, jsonschema, python-hcl2, crossplane, pytest

**Spec:** `docs/superpowers/specs/2026-10-01-infrafit-design.md` (§2 원칙 7, §6.2, §6.6, §8.6, §9.8)

**선행:** 계획 1, 1b가 `feat/infrafit-plan1`에 구현되어 있다. 판정 기록: `docs/superpowers/notes/2026-10-02-plan1-rulings-and-followups.md`.

## Global Constraints

- 계획 1·1b의 Global Constraints를 모두 따른다(스키마 검증 후 쓰기, 결정성과 정렬, 범위 ID 형식 `^(w|ep|ds|svc|path)-[a-z0-9._-]+$`, 근거는 실제 파일의 실제 줄, 판단이 필요한 사실은 `candidate`, 네트워크는 `git clone`뿐, 문서·주석 한국어, 커밋 영어, 커밋 끝에 `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`).
- 픽스처의 기대 출력을 어디에도 적지 않는다. 테스트는 `tmp_path` 합성 저장소로 규칙을 검증한다. 골든은 마지막 작업에서 `scripts/update_golden.py`로만 다시 만든다. 작업 1~3 사이에는 새 필드 때문에 골든·스키마 예시 테스트가 실패할 수 있다(그 외 테스트는 모두 통과).
- 새 의존성 없음.

---

### Task 1: compose 환경

**Files:** Modify `infrafit/detect/environments.py`, `infrafit/detect/paths.py`, `infrafit/detect/nginx.py`, `infrafit/stages/s1_inventory.py`, `infrafit/consistency.py`, `schemas/infrafit.schema.json`; Test `tests/test_compose_env.py`

**Interfaces:**
- Consumes: compose `ParsedArtifact`(서비스 맵), `workloads.compose_build`/`dockerfile_for_image`, `Environment`, `workload_in`, `find_proxies`, `build_paths`.
- Produces:
  - `Environment`에 `kind: str`(`"kustomize"`/`"compose"`)와 `services: dict[str, dict]`(compose 환경의 병합된 서비스 정의, kustomize는 빈 맵), `members: dict[str, str]`(compose 환경: 워크로드 id → 서비스 이름) 추가. `to_dict`에 `kind`.
  - `detect_environments(artifacts, workloads)` — compose 환경 포함, 이름순.
  - `workload_in(env, w)` — compose 환경이면 `w.id in env.members`.
  - `env_command(env, w, artifacts) -> str` — 그 환경에서 워크로드가 실행하는 명령.

**규칙**

compose 환경 만들기
1. 디렉터리마다 기본 파일(`docker-compose.yml`, `docker-compose.yaml`, `compose.yml`, `compose.yaml`)이 있으면 환경 하나. 같은 디렉터리의 `compose.override.*`는 `compose.*` 기본 파일 위에만, `docker-compose.override.*`는 `docker-compose.*` 기본 파일 위에만 병합한다(docker 동작). 이름은 루트면 `compose`, 아니면 `compose/<디렉터리>`. `source`는 기본 파일. `.devcontainer/` 아래 compose 파일은 환경을 만들지 않는다. 서비스 ↔ 워크로드 대응(5~7) 뒤에 대응한 워크로드가 하나도 없는 compose 환경은 버린다.
2. 같은 디렉터리의 변형 파일 `docker-compose.<x>.yml`, `compose.<x>.yaml`, `docker-compose-<x>.yml` 등(`override` 파일이 아님)은 기본 파일 + 변형 파일만 병합한 별도 환경이다(`docker compose -f <기본> -f <변형>`과 같다. override는 개발 설정을 담으므로 넣지 않는다). 이름은 `compose.<x>`(루트) 또는 `compose.<x>/<디렉터리>`. `source`는 변형 파일. 기본 파일이 없으면 변형 파일만으로 만든다. 변형 파일은 파싱에 성공하고 서비스가 하나 이상 있어야 환경을 만든다.
3. 병합(docker compose 규칙): 서비스 단위로, `environment`는 변수 이름 단위(목록·맵 형식 모두, 값 없는 `KEY`는 호스트 값을 받으므로 알 수 없음 = 없음), `volumes`는 컨테이너 경로 단위(같은 경로면 뒤 파일이 이긴다), `ports`·`expose`는 겹치지 않게 덧붙이고, 그 밖의 키는 뒤 파일의 값이 앞 파일의 값을 덮는다. 파싱에 실패한 파일은 건너뛴다. 서비스가 하나도 없으면 환경을 만들지 않는다.
4. `rendered`는 compose 환경에서 항상 true.

서비스 ↔ 워크로드 대응(환경마다)
5. 먼저 이름: 서비스 이름 == 워크로드 이름.
6. 남은 서비스와 남은 워크로드 사이에서, 서비스의 빌드 Dockerfile(`compose_build`로 구한 경로) == 워크로드의 Dockerfile(이미지 → Dockerfile 규칙 또는 code_root의 Dockerfile)이거나, 서비스 `image`와 워크로드 `image`가 태그·레지스트리를 뗀 마지막 이름으로 같으면 후보. 한 워크로드에 후보 서비스가 정확히 하나이고 그 서비스의 후보 워크로드도 하나일 때만 대응한다. 이미 5에서 다른 워크로드에 대응한 서비스는 후보가 아니다.
7. 워크로드가 compose에서 왔으면(source `compose`) 그 compose 파일이 속한 환경들에서 이름으로 대응한다(5와 같음).

명령
8. `env_command`: compose 환경 → 서비스 `command`(목록은 공백으로 이음), 없으면 서비스 빌드 Dockerfile의 마지막 체인 ENTRYPOINT+CMD. kustomize 환경 → 렌더 객체에서 워크로드 객체(`is_workload_doc`)의 컨테이너(이미지가 워크로드 이미지와 같은 것, 없으면 첫 컨테이너) `command`+`args`(`command` 없이 `args`만 있으면 이미지 최종 체인 ENTRYPOINT + `args`, 둘 다 없으면 이미지 CMD). 둘 다 없으면 `w.command`.
9. 경로의 `app-server` 구간은 그 경로 환경의 `env_command`로 만든다(environment null이면 `w.command`, 계획 1과 같음).

경로·프록시
10. 요청 경로는 1b 규칙 그대로 환경마다 만든다. compose 환경에는 로드밸런서·엣지 구간이 없다.
11. `find_proxies`의 환경 범위는 compose 환경도 포함한다. compose 환경 E에서 프록시 워크로드 P의 변수 = P의 Dockerfile ENV < E에서 P에 대응한 서비스의 `environment`. 호스트 해석은 E의 서비스 이름 → `members`의 역대응으로 워크로드를 찾는다(대응하지 않은 서비스면 target None). k8s Service 해석은 compose 환경에서 쓰지 않는다.
11-1. 설정 파일 경로 매핑은 환경마다 만든다. kustomize 환경·null → 워크로드 Dockerfile의 COPY/ADD 매핑(environment null이고 워크로드가 compose에서 왔으면 1b처럼 그 서비스의 바인드 마운트도 더한다). compose 환경 → Dockerfile 매핑 위에 그 환경에서 대응한 서비스의 바인드 마운트를 덮어쓴다(같은 컨테이너 경로면 마운트가 이긴다, docker 동작). 진입 설정·include·location 해석은 그 환경의 매핑으로 한다.
12. 워크로드가 어떤 환경에도 없을 때만 environment null 범위를 쓴다(1b와 같음).

스키마·일관성
13. `Inventory.environments[]`에 `kind`(필수, `kustomize`/`compose`).
14. 일관성 검사는 1b 그대로(경로 id·환경 이름).

**테스트(합성 저장소)**
- 루트 `docker-compose.yml` + `docker-compose.override.yml`(환경변수 덮어쓰기) + `docker-compose.prod.yml` → 환경 `compose`, `compose.prod`, 병합 결과가 규칙 3대로.
- k8s 워크로드 `api`, `api-verify`(같은 이미지)와 compose 서비스 `api` → `api`만 compose 환경에 있음. compose 서비스 `migrate`와 k8s 워크로드 `db-migrate`(같은 Dockerfile, 다른 이름, 유일 후보) → 대응.
- compose 서비스가 이미지 설정 파일과 같은 컨테이너 경로에 다른 파일을 바인드 마운트 → compose 환경은 마운트 파일, kustomize 환경은 이미지 파일로 해석.
- compose nginx가 `${UP}`(compose environment `UP=api:8000`)로 프록시, k8s overlay에서는 ConfigMap이 `UP=api-verify:8000` → 환경마다 다른 target.
- compose 환경의 app-server 구간이 서비스 `command`의 설정을 쓰고, kustomize 환경은 렌더 객체의 `args`를 쓴다(`--timeout-keep-alive` 값이 다르게).
- compose만 있는 저장소 → 환경 `compose`, 경로 id `path-<w>.compose`.
- 깨진 compose 파일, 서비스가 없는 compose 파일 → 예외 없음, 환경 없음.

**Commit:** `feat: record docker compose configurations as environments`

---

### Task 2: 환경별 exposure

**Files:** Modify `infrafit/detect/endpoints.py`, `infrafit/consistency.py`, `schemas/infrafit.schema.json`; Test `tests/test_proxy_paths.py`(추가)

**Interfaces:**
- Produces: `Endpoint.exposure`가 `[{ "environment": string|null, "value": "routed"|"not-routed" }]` 배열로 바뀐다(선택 필드, 비어 있으면 쓰지 않음). 정렬은 `(environment is not None, environment or "")`.

**규칙**
1. 환경 E(또는 null)마다, E의 route 중 워크로드 W를 target으로 하는 것이 있으면 W의 엔드포인트마다 E에 대한 값을 1b 규칙 8~10(+ P6, P7, F1)으로 계산하되, E의 server·route만 쓴다.
2. 그런 route가 없는 환경은 배열에 넣지 않는다.
3. 일관성 검사: `exposure[].environment`는 `environments[].name` 중 하나이거나 null이고, 한 엔드포인트 안에서 중복되지 않는다.

**테스트**
- 두 overlay에서 nginx 설정은 같고 ConfigMap으로 다른 upstream → 엔드포인트 exposure가 환경마다 다르게.
- compose 환경은 바인드 마운트한 nginx 설정(`/debug/`를 proxy)을, kustomize 환경은 이미지에 COPY한 설정(`/debug/` 없음)을 쓰는 합성 저장소 → `/debug/x`가 compose에서 routed, kustomize 환경에서 not-routed.
- 프록시가 없는 저장소는 exposure 없음(계획 1과 같음).

**Commit:** `feat: record endpoint exposure per environment`

---

### Task 3: 다단 프록시 체인

**Files:** Modify `infrafit/detect/paths.py`, `infrafit/detect/endpoints.py`; Test `tests/test_proxy_chain.py`

**규칙**

경로
1. 환경 E에서 워크로드 X로 가는 "상류 체인"을 이렇게 찾는다: E의 route 중 target이 X인 것의 프록시 P(여럿이면 id 순 첫 번째, 1b 규칙 5). P 자신의 앞 구간(엣지·LB)이 E에 있으면 체인은 거기서 끝난다. 없으면 P를 target으로 하는 프록시를 같은 방식으로 다시 찾는다. 순환이면 끊고, 깊이 5에서 끊는다.
2. X의 경로 = 체인 맨 위 프록시의 앞 구간 + 체인의 프록시마다 `reverse-proxy` 구간(위에서 아래 순서, 각 구간 설정은 그 프록시에서 다음 프록시(또는 X)로 가는 route들의 설정, 1b 규칙 4·P5) + (X가 프록시가 아니면) X의 `app-server` 구간, (X가 프록시면) X 자신의 server 단위 `reverse-proxy` 구간.
3. X 자신의 앞 구간이 E에 있으면 1b 규칙 5대로 X의 앞 구간을 쓴다(체인을 따라가지 않는다).

exposure
4. 체인을 지나는 요청: 맨 위 프록시 P_top에 들어온 외부 요청 r이 P_top에서 다음 프록시 P1로 전달 경로 f1이 되면, P1에서 f1을 외부 요청처럼 다시 `select_location`하고 전달한다(P1 안의 internal location은 P1이 받은 요청에서도 선택되면 404). 이것을 X에 닿을 때까지 반복한다. 마지막 전달 경로가 X 엔드포인트의 라우트와 같으면 그 환경에서 routed.
5. 후보 외부 요청 생성(F1의 역매핑)은 체인의 각 단계에서 아래에서 위로 적용한다: X의 엔드포인트 경로 r_X에서 시작해, 각 프록시의 외부 접두어 location L(uri U)에 대해 r이 U로 시작하면 `L.pattern + r[len(U):]`을 위 단계의 후보로 더한다(그대로의 r도 후보). 후보는 반드시 4의 전방 검사로 확인한다.
6. P6(subrequest 무조건 도달)은 체인 맨 위 프록시에서만이 아니라, 체인의 각 프록시에서 그 프록시로 실제로 요청이 들어오는 경우(위 단계에서 그 프록시로 가는 route가 있는 경우)에 적용한다.

**테스트**
- `Ingress → nginx A → nginx B → app`: app 경로가 `load-balancer → reverse-proxy(A) → reverse-proxy(B) → app-server`, 각 reverse-proxy 구간 설정이 해당 route의 값.
- A가 `/api/`를 B로 `proxy_pass http://b/`(접두어 제거), B가 `/v1/`을 app으로 → app의 `/v1/users`가 외부 `/api/v1/users`로 routed.
- B에 `location /internal/ { internal; }`가 있으면 그 아래 엔드포인트는 not-routed.
- A ↔ B 순환 프록시 → 예외 없이 끝남.
- 단일 프록시 저장소의 결과는 Task 2 결과와 같다.

**Commit:** `feat: follow chained reverse proxies in request paths and exposure`

---

### Task 4: 골든 갱신과 확인

- [ ] `uv run pytest`, `uv run infrafit kb lint` 통과.
- [ ] `uv run python scripts/update_golden.py`로 골든·예시를 다시 만든다(손으로 고치지 않는다). 픽스처별 diff를 Task 1~3 규칙으로 설명한다. 설명되지 않는 변화는 원인을 고친다.
- [ ] 외부 저장소 `simple-web-app`(현재 HEAD)와 이 저장소에 `analyze` + `check-run`: 예외 없음, 0개 문제.

**Commit:** `test: regenerate goldens after compose environments and proxy chains`
