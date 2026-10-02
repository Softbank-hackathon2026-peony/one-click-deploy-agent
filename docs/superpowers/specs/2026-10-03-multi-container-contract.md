# 여러 컨테이너 배포 계약 (v1)

작성 2026-10-03. InfraFit → agentcore → 빌드 → Terraform-worker → MainServer 가 같이 쓰는 형식.

## 왜

지금 파이프라인은 "앱 = 이미지 1개" 를 전제한다 (Worker `a91ba4d` 의 모듈 입력 `image_uri`, agentcore `analyze.py:122` 의 compose·k8s 차단).
그래서 DB·캐시·워커·마이그레이션·nginx 를 가진 앱은 InfraFit 이 S1 에서 다 찾아도 중간에 버려지고 `supported=false` 가 된다.
이 계약은 **컨테이너 여러 개**를 끝까지 전달한다. 레플리카·스케일링(인스턴스 여러 개)은 이 문서 범위가 아니다.

## 1. InfraFit S1 `deploy_units` (inventory.json, 새 최상위 필드)

프로젝트가 스스로 정의한 "같이 떠야 하는 컨테이너 묶음". 출처 우선순위: compose → k8s → 코드에서 찾은 워크로드 1개.

```json
"deploy_units": {
  "source": {"kind": "compose", "path": "docker-compose.yml"},
  "images": [
    {"id": "board", "context": "services/board", "dockerfile": "services/board/Dockerfile",
     "evidence": {"path": "docker-compose.yml", "line": 10}}
  ],
  "containers": [
    {"id": "board-worker", "workload": "w-board-worker", "image": "board",
     "command": "python -m board.worker", "ports": [], "env": {"REDIS_URL": "redis://redis:6379/0"},
     "env_names": ["DATABASE_URL", "REDIS_URL"], "depends_on": ["postgres", "redis", "migrate"],
     "one_shot": false, "evidence": {"path": "docker-compose.yml", "line": 79}}
  ],
  "datastores": [
    {"id": "postgres", "datastore": "ds-postgresql", "image": "postgres:16-alpine", "ports": [5432],
     "env_names": ["POSTGRES_PASSWORD", "POSTGRES_USER", "POSTGRES_DB"], "evidence": {"path": "docker-compose.yml", "line": 15}}
  ],
  "entry": {"container": "nginx", "port": 8080, "why": "유일하게 호스트 포트를 연 web/proxy 컨테이너"}
}
```

- `id` 는 원래 서비스 이름 그대로 (컨테이너끼리 이 이름으로 접속한다. 바꾸면 nginx upstream·DB 주소가 깨진다)
- `images[].id` 는 같은 build(context+dockerfile)를 쓰는 컨테이너가 공유한다 (`board-api`·`board-worker`·`migrate` → `board`)
- `image` 가 레지스트리 이미지(빌드 없음)면 `images` 에 넣지 않고 컨테이너에 `"registry_image": "redis:7-alpine"`
- `one_shot`: `restart: "no"` 이거나 다른 서비스가 `condition: service_completed_successfully` 로 기다리는 컨테이너 (마이그레이션)
- `env` 는 비밀이 아닌 값만. 비밀로 보이는 키·값(키 이름 규칙은 기존 secret 판정과 같음)은 `env_names` 에만
- `datastores` 는 inventory `datastores`/`external_services` 와 이미지로 연결한 컨테이너 (postgres, mysql, redis, mongo …)
- `entry`: 호스트 포트를 연 web/proxy 컨테이너. 여럿이면 proxy 우선, 없으면 null
- 못 정하면 필드를 비우고 `unresolved: [{field, why}]` 에 적는다 (지어내지 않음)

## 2. agentcore analyze 응답 `recommendation`

기존 필드(`cloud`, `architecture`, `container_port`, `health_path`, `env`, …)는 컨테이너 1개 앱을 위해 그대로 둔다.
컨테이너가 2개 이상이면 아래를 추가하고 `architecture` 는 여러 컨테이너를 받는 실행기(v1: `ec2_compose`)가 된다.

```json
"deploy_units": { ...InfraFit 것을 검사·보완한 결과... },
"build_files": {"images": {"board": {"dockerfile": "services/board/Dockerfile", "generated": false},
                           "frontend": {"dockerfile": "Dockerfile.pawploy.frontend", "generated": true}}}
```

- 프로젝트에 Dockerfile 이 있으면 그대로 쓴다. 없을 때만 LLM 이 그 context 용 Dockerfile 을 만든다
- `supported=false` 는 "실행할 수 있는 실행기가 없는 컨테이너가 있을 때" 만

## 3. 빌드 (CodeBuild buildspec / 로컬 docker build)

`images[]` 마다 빌드·푸시. 결과는 `{"board": "<ECR>@sha256:…", "frontend": "…"}`.

## 4. Terraform-worker job target (`ec2_compose`)

```json
{"cloud": "aws", "architecture": "ec2_compose",
 "images": {"board": "<ECR>@sha256:…", "frontend": "<ECR>@sha256:…"},
 "terraform_uri": "s3://…/aws/"}
```

- 모듈 입력: `name`, `images`(map), `size`, `health_path` + 모듈 안의 `compose.yaml.tftpl` (agentcore **코드**가 deploy_units 로 렌더, LLM 아님)
- 출력은 기존과 같음: `endpoint`, `health_url`, `resource_id`
- 데이터 저장소 컨테이너 비밀번호는 모듈의 `random_password` 로 만들고 템플릿에 넣는다
- 헬스체크는 `entry` 컨테이너 → 인스턴스 80번

## 5. 로컬 (MainServer `feat/local-e2e`)

같은 `compose.yaml.tftpl` 을 로컬 값(이미지 id, 비밀번호)으로 렌더해 `docker compose up` → `entry` 헬스체크.

## 다음 (이 문서 범위 밖)

- k8s 만 있는 프로젝트를 EKS/GKE 로, compose 프로젝트를 ECS 서비스 여러 개로 (같은 deploy_units 사용)
- 관리형 DB·캐시(RDS/ElastiCache) 로 바꾸는 경우: `datastores[].mode = managed`
- 레플리카·스케일링
