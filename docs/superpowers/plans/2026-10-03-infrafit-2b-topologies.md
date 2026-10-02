# infrafit 계획 2b: 배포 형태(토폴로지) 전체를 후보로 — 워크로드별 판정, VM compose, 관리형 쿠버네티스

**Goal:** 추천이 요구에 맞는 배포 형태를 고르게 한다. (1) 워크로드마다 따로 판정한다(웹·워커·게이트웨이·마이그레이션 작업). (2) 형태(토폴로지) 세 가지를 모두 후보로 둔다: **단일 VM + docker compose**(워크로드와 DB·캐시를 한 VM에), **서비스형 플랫폼**(워크로드마다 Lambda / Cloud Run / ECS), **관리형 쿠버네티스**(EKS / GKE에 워크로드 전부). (3) 확장 요구(레플리카·HPA·KEDA·부하 테스트)를 코드에서 읽어 판정과 비용에 반영한다.

**원칙:** 한 컨테이너·한 인스턴스를 가정하지 않는다(메모리 `recommender-decides-platform`). 플랫폼 선택은 사용자에게 묻지 않고 알고리즘이 한다. 능력·비용 값은 README §3 출처 정책(적격 공식 출처, 줄에 있는 원문 인용)만 쓴다. `main`에서만 작업한다.

## 작업

### Task A — 지식 (knowledge/, docs/research/ 만 수정)
- 관리형 쿠버네티스 후보: 연구 문서 `capabilities/05-compute-tier1-2.md` §5.1 GKE Autopilot, §6.1 EKS 관리형 노드 그룹(필요하면 §6.3 Auto Mode)에서 적격 인용이 있는 값만 `knowledge/capabilities.yaml`에 넣는다. 키: 기존 CP.* + `CP.horizontal_scaling`(bool), `CP.multi_workload`(bool: 여러 워크로드를 한 클러스터에), `COST.monthly_floor_usd`(컨트롤 플레인 + 최소 노드, 서울, 계산식과 인용), `COST.per_replica_usd`(가능하면). 없으면 공식 문서(WebFetch, docs.aws.amazon.com / cloud.google.com)에서 명시 문장을 원문 인용해 연구 문서에 새 줄로 추가한 뒤 쓴다.
- VM 안 데이터 저장소: `ds:vm/compose-postgres`, `ca:vm/compose-redis`(카탈로그 추가). VM compute와만 짝지을 수 있고 추가 비용 0(VM 비용에 포함)이라는 사실, 영속성은 VM 디스크(EBS/PD) 능력을 따른다는 사실을 공식 출처(Docker 공식 이미지 문서의 볼륨 영속, EBS/PD 영속)로 남긴다. 백업은 사용자가 설정해야 한다는 `requires_config`.
- 서비스형 플랫폼의 확장: Lambda·Cloud Run·ECS의 `CP.horizontal_scaling`(공식 인용).
- `kb lint` 0, 테스트.

### Task B — 탐지 (infrafit/detect/, infrafit/profile/, knowledge/profile_detectors.yaml, knowledge/signatures/ 만 수정)
- 확장 요구 차원(D2/D3 + 새 값): HPA `minReplicas/maxReplicas`, Deployment `replicas`, KEDA ScaledObject, compose `deploy.replicas`, 부하 테스트 스크립트(k6/locust/artillery) → 워크로드별 `scaling: {min, max, autoscale: bool}`와 D2 근거. 없으면 가정 D2=낮음(지금과 같음).
- Supabase를 접속 URL로 쓰는 경우 탐지(`SUPABASE_DB_URL`, `*.supabase.co`, `pooler.supabase.com` 등) → 데이터 범위가 Supabase(BaaS)로 기록되게.
- 일회성 실행(batch)만 있는 저장소는 S4가 `not_deployable`(“사람이 실행하는 도구”)로 낼 수 있게 S2에 `A1` 근거를 남긴다.
- 테스트(합성 저장소).

### Task C — 엔진 (infrafit/fit/, infrafit/stages/s3_fit.py, s4_recommend.py, schemas, rules.yaml) — A·B 이후
- 범위: 앱 워크로드마다 compute 범위. `w-app` 집계는 설명용으로만.
- 조합 = 토폴로지 3종 × 클라우드:
  - VM compose: 모든 워크로드 + (Postgres/Redis → `vm/compose-*` 또는 관리형) 한 VM. 확장 요구(min>1 또는 autoscale)가 있으면 위반(단일 VM은 수평 확장 불가, 출처 필요) 또는 `feasible_with_config`가 아니다 → 탈락 사유로.
  - 서비스형: 워크로드마다 Lambda / Cloud Run(두 과금) / ECS 중 같은 클라우드에서 규칙을 통과한 것. 비용 = 워크로드별 바닥 비용 × 최소 레플리카(+ ALB 등 공유 비용 1회).
  - 쿠버네티스: 클러스터 1개(EKS 또는 GKE) + 워크로드 전부. 비용 = 컨트롤 플레인 + 최소 노드(또는 레플리카 합에 따른 값, 출처 있는 단가만).
- 규칙: 확장 요구 × `CP.horizontal_scaling`, B1(메모리 상태) × 레플리카>1이면 위반(“인스턴스 간 공유 안 됨”, B1 근거), 기존 규칙은 워크로드별로.
- 순위: 기존(실현 가능 → 비용 확정 → 낮은 비용 → 모르는 셀 → …). 결과에 토폴로지 이름과 워크로드별 배치를 낸다. AgentCore 대상 매핑: 워크로드별 target.
- 스키마 최소 확장, `check-run`, 테스트.

### Task D — QA 다시 (컨트롤러)
- 블라인드 심사 조건에서 단일 VM 편향을 없앤다: 선택지에 토폴로지 3종(+EKS/GKE), 저장소가 밝힌 확장 요구(HPA·레플리카)는 따르고, 없는 경우만 저트래픽 가정.
- 13개 저장소 비교, 불일치 검토.
