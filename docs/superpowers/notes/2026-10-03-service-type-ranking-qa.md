# 서비스 유형별 순위 QA (2026-10-03)

픽스처 6개를 `scripts/qa_ranking.py`로 돌린 표. 새 순위(이 브랜치)와 기존 순위(main, `git worktree`)를 비교한다.

## 새 순위

| 픽스처 | 유형 | coverage | 근거 | 1~3위 (월 USD, decided_by) |
|---|---|---|---|---|
| f1-simple-web-app | stateful | partial | stateful:datastores@services/auth/pyproject.toml:9,datastores@services/auth/pyproject.toml:10; background:A1@k8s/base/board-worker.yaml:4 | C1 kubernetes:gke (193.65, cost)<br>C2 services:cloud-run (229.96, certainty)<br>C3 kubernetes:eks (None, config_burden) |
| f2-sqlite-erp | stateful | full | stateful:B2@db.py:8,datastores@db.py:8 | C1 vm-compose:compute-engine (None, cost)<br>C2 vm-compose:ec2 (None, cost)<br>C3 kubernetes:gke (None, cost) |
| f3-vibe-shop | stateful | full | stateful:B1@lib/session.ts:1,B2@package.json:6 | C1 vm-compose:compute-engine (None, cost)<br>C2 vm-compose:ec2 (None, cost)<br>C3 kubernetes:gke (None, cost) |
| f4-overbuilt-internal | stateful | full | stateful:datastores@package.json:5 | C1 services:lambda (20.9, cost)<br>C2 services:cloud-run (53.61, cost)<br>C3 kubernetes:gke (69.04, certainty) |
| f5-small-blog | stateful | full | stateful:datastores@package.json:6 | C1 services:lambda (None, name)<br>C2 services:cloud-run (None, cost)<br>C3 vm-compose:compute-engine (None, cost) |
| f6-long-jobs | long_request | partial | long_request:A2@app/api/export/route.ts:5; stateful:datastores@package.json:9; background:A4@app/api/signup/route.ts:9 | C1 services:cloud-run (12.21, cost)<br>C2 vm-compose:compute-engine (20.64, cost)<br>C3 vm-compose:ec2 (20.7, cost) |

## 기존 순위 (main)

| 픽스처 | 유형 | coverage | 근거 | 1~3위 (월 USD, decided_by) |
|---|---|---|---|---|
| f1-simple-web-app | - | - | - | C1 kubernetes:gke (193.65, -)<br>C2 services:cloud-run (229.96, -)<br>C3 kubernetes:eks (None, -) |
| f2-sqlite-erp | - | - | - | C1 vm-compose:compute-engine (None, -)<br>C2 vm-compose:ec2 (None, -)<br>C3 kubernetes:gke (None, -) |
| f3-vibe-shop | - | - | - | C1 vm-compose:compute-engine (None, -)<br>C2 vm-compose:ec2 (None, -)<br>C3 kubernetes:gke (None, -) |
| f4-overbuilt-internal | - | - | - | C1 services:lambda (20.9, -)<br>C2 services:cloud-run (53.61, -)<br>C3 kubernetes:gke (69.04, -) |
| f5-small-blog | - | - | - | C1 services:lambda (None, -)<br>C2 services:cloud-run (None, -)<br>C3 vm-compose:compute-engine (None, -) |
| f6-long-jobs | - | - | - | C1 services:cloud-run (12.21, -)<br>C2 vm-compose:compute-engine (20.64, -)<br>C3 vm-compose:ec2 (20.7, -) |

## 1위가 바뀐 픽스처

없음. 여섯 픽스처 모두 1~3위의 조합과 순서가 main과 같고, 비용 값도 같다. 바뀐 것은 유형·coverage·decided_by 열이 채워진 것뿐이다.

판정은 "맞음/의심" 대상이 없다. 다만 순위가 그대로라는 사실은 이 픽스처들이 새 기준 순서를 시험하지 못한다는 뜻이기도 하다(아래 참고).

## 참고: 유형별 관찰

- f1-simple-web-app: 상태 저장, coverage partial. 근거는 인증 서비스의 데이터 저장소 의존성이고, 백그라운드(A1 워커 `board-worker`)는 `unprioritized`로 밀렸다. 즉 워커의 상시 응답 기준은 순위에 안 쓰였다. 1위 GKE는 데이터 안전이 동률이라 cost에서 갈렸다.
- f6-long-jobs: 장시간 처리, coverage partial. 상태 저장(데이터 저장소)과 백그라운드(A4)가 밀렸다. 1위 Cloud Run이 비용으로 갈린 것은 처리 시간 여유(`request_headroom`)가 1~3위 모두 0으로 동률이었다는 뜻이다.
- f2, f3, f4, f5: 상태 저장, coverage full. 1위가 모두 cost 또는 name에서 갈렸다. f2·f3은 상위 후보 합이 모두 null(`None`)이라 비용 비교가 모르는 비용 구성 요소 수와 부분합으로 내려간다.
- f5-small-blog: 1위 Lambda가 `name`으로 갈렸다. Lambda와 Cloud Run 모두 합이 null이고 모르는 수까지 같아 조합 이름이 마지막 동률 깨기였다. 순위가 이름순으로 결정되는 것은 근거가 약하다.
- "default" coverage 픽스처는 없다. 여섯 모두 어떤 유형에 걸렸다.

## 사람 확인 필요

1. f6 1위 Cloud Run이 `cost`로 갈렸다. 후보 criteria를 직접 확인하니 상위 3개 모두 `request_headroom` 0(동률)이고 certainty도 같아 비용이 첫 갈림 기준이 맞다. 맞음(코드 문제 아님). 다만 이 픽스처도 처리 시간 여유 기준이 순위를 가르지는 않았다.
2. f5 1위 Lambda의 `name` 동률 깨기. 비용 합이 null이라 비용 비교가 의미가 없는 상태에서 이름순이 1위를 정한다. 확인: 상위 3개 모두 모르는 비용 구성 요소 1개, 합 null. 가설: 비용 구성 요소 단가 부재. 비용 데이터 보강 전까지는 이 결과를 근거 있는 추천으로 읽으면 안 된다.
3. 유형이 상태 저장인 픽스처가 5/6이다. 상태 저장 판정 근거에 `datastores` 차원이 포함돼 데이터 저장소가 하나라도 있으면 걸리는 것으로 보인다. 실제로 유형을 구분하는 픽스처(실시간·백그라운드·가벼운 웹)가 없어 이 세 유형의 기준 순서는 이 QA로 검증되지 않았다.
