# InfraFit QA 후속 (2026-10-03)

QA에서 나온 네 항목을 고치고, 재현 픽스처 두 개(f7·f8)를 추가했다. 전(before)은 후속 작업 시작 전 커밋(`311eea6`)의 워크트리에서 같은 픽스처를 돌린 값이고, 후(after)는 현재 `main`이다.

## 항목별 전후

| 항목 | 전 | 후 |
|---|---|---|
| Procfile `beat` (f7) | `beat: celery … beat` 가 워크로드가 아니다. 워크로드는 `web`·`worker` 둘뿐 | `scheduled` 워크로드(진입점 `Procfile:3`)와 컨테이너가 생긴다. 알 수 없는 Procfile 타입도 명령이 `celery [옵션] beat` 모양일 때만 `scheduled` (`worker -Q beat` 는 아님) |
| 코드 경로 저장소 (f7) | `deploy_units.datastores` 가 비어 있고 컨테이너 `env` 도 `{}` | `redis`(`redis:7-alpine`) 저장소 컨테이너가 생기고 모든 앱 컨테이너가 `depends_on: [redis]`, `env.REDIS_URL = redis://redis:6379/0` (코드의 `os.environ.get("REDIS_URL", …)` 에서 찾은 이름에만). postgres 등 비밀번호가 필요한 저장소는 컨테이너 없이 `unresolved` |
| sleep A2 (f7) | `/slow` 의 `time.sleep(40)` 을 못 봐서 A2 `1초 미만` (assumption) | A2 `수십 초` (detector, `app.py:16`). 순위 유형이 `stateful` → `long_request` |
| 웹소켓 unknown (f8) | 플랫폼 능력 표가 모르는 후보도 아무 표시 없이 순위에 섞인다 | 모르는 후보(ecs-fargate `B1`/`CP.single_instance_config`; 처음에는 compute-engine·ec2 `A3`/`CP.websocket` 도 있었으나 아래 후속에서 두 VM compose 에 `CP.websocket` 유도 값을 넣어 해소)에 `unknown` 이 붙고 `recommended` 는 `unknown` 없는 첫 후보(C1 gke)다. 모든 후보에 `unknown` 이면 `recommended: null`, `outcome: unverified` |

기타: memcached 의 `image` 필드는 카탈로그 컴포넌트가 없어 해석되지 않는 죽은 설정이라 뺐다(`knowledge/images.yaml`, 설계 문서 §2). 픽스처 골든은 이 변경으로 바뀌지 않았다.

## qa_ranking (f7·f8)

`scripts/qa_ranking.py` 의 새 행. f1~f6 행은 바뀌지 않았다.

| 픽스처 | 유형 | coverage | 근거 | 1~3위 (월 USD, decided_by) |
|---|---|---|---|---|
| f7-celery-redis | long_request | partial | long_request:A2@app.py:16; stateful:datastores@requirements.txt:2,datastores@requirements.txt:3; background:A1@Procfile:3,A1@Procfile:2 | C1 vm-compose:ec2 (20.7, name)<br>C2 vm-compose:compute-engine (20.64, cost)<br>C3 vm-compose:ec2 (38.2, cost) |
| f8-socketio-chat | realtime | partial | realtime:A3@package.json:6,A1@package.json:6; stateful:B1@package.json:6,datastores@package.json:6 | C1 kubernetes:gke (31.11, cost)<br>C2 kubernetes:eks (140.16, scaling)<br>C3 vm-compose:compute-engine (20.64, cost) |

전(`311eea6`)의 같은 행:

| 픽스처 | 유형 | coverage | 근거 | 1~3위 (월 USD, decided_by) |
|---|---|---|---|---|
| f7-celery-redis | stateful | partial | stateful:datastores@requirements.txt:2,datastores@requirements.txt:3; background:A1@Procfile:2 | C1 vm-compose:ec2 (38.2, cost)<br>C2 services:ecs-fargate,lambda (55.24, cost)<br>C3 vm-compose:compute-engine (68.09, cost) |
| f8-socketio-chat | realtime | partial | realtime:A3@package.json:6,A1@package.json:6; stateful:B1@package.json:6,datastores@package.json:6 | C1 kubernetes:gke (31.11, cost)<br>C2 kubernetes:eks (140.16, always_on)<br>C3 services:cloud-run (13.8, certainty) |

## 관찰과 사람 확인 필요

1. f7 1위 ec2 (20.7)는 `decided_by: name` 이고 2위 compute-engine (20.64)이 더 싸다. 비용 비교가 이 둘을 가르지 못했다는 뜻으로 읽히지만 원인은 확인하지 않았다(비용 합이 일부 모르는 값을 포함할 수 있다). [서비스 유형별 순위 QA](2026-10-03-service-type-ranking-qa.md) 의 `name` 동률 깨기 항목과 같은 종류이고, 이번 변경으로 새로 생긴 것은 아니다. 근거 있는 추천으로 읽지 말 것.
2. f8 에는 Lambda 후보가 아예 없다(`rejected` 도 비어 있다). 처음에는 `unknown`(`CP.websocket`)이 vm-compose 의 compute-engine·ec2 에 붙었으나, 두 컴포넌트에 `CP.websocket: true`(derived, 플랫폼 프록시 없음)를 넣어 지금은 해소됐다. 남은 `unknown` 은 ecs-fargate 의 B1(`CP.single_instance_config`) 하나다. 그 결과 vm-compose 가 추천 후보 풀에 들어와 f8 순위가 gke, eks, compute-engine(C3), ec2(C4), cloud-run(C5), ecs-fargate(C6) 로 바뀌었고 `recommended` 는 여전히 C1 gke 다. 그래서 "Lambda 후보에 `unknown`" 이라는 예상과는 다르다. 확인: 후보 생성이 이 저장소(상시 서버 프로세스)에 Lambda 를 만들지 않는 이유는 이번 범위에서 조사하지 않았다.
3. f8 `recommended` 는 gke(C1)로 전과 같다. `unknown` 은 순위를 바꾸지 않고 추천 선택에만 영향을 준다. `unverified` 결과는 이 픽스처에서 나오지 않는다(clean 후보가 있다).
4. f7 은 한 저장소에서 beat·코드 경로 저장소·sleep A2 세 항목을 함께 재현한다. 전후 비교에서 `deploy_units` 출처가 `{kind: code, path: Procfile}` 인 것도 확인했다.
