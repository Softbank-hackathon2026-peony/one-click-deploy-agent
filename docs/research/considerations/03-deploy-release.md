# 배포·릴리스·변경 관리

시나리오 U(무중단 배포)를 중심으로, "새 버전을 내보내고 설정·스키마·인프라를 바꾸는 순간"에 깨지는 것들을 모은 카탈로그다. 롤아웃 전략, 기동·종료, 자동 롤백, 스키마 마이그레이션, 버전 간 호환성, 백그라운드 작업, 빌드·공급망 무결성, 설정·비밀, 환경 분리, IaC·변경 통제를 다룬다.
트래픽 확장(T), 장애·DR(D), 데이터 정합성(C), 보안 일반, 비용 최적화, 관측 일반은 다른 문서가 맡는다. 단, 비밀 관리·공급망 무결성·배포 중 지표 기반 자동 중단은 여기서 다룬다.
모든 출처는 2026-10-01에 WebFetch로 직접 열어 확인했다. 열지 못했거나 해당 문장을 찾지 못한 항목은 "일반 원칙(출처 미확인)"으로 적었다.

## 목차

- A. 롤아웃 전략과 용량 (U-001 ~ U-013)
- B. 기동과 헬스체크 (U-014 ~ U-021)
- C. 종료와 연결 드레이닝 (U-022 ~ U-032)
- D. 자동 롤백, 점진 배포, 릴리스 분리 (U-033 ~ U-042)
- E. 스키마 마이그레이션 (U-043 ~ U-060)
- F. 버전 간 호환성: API, 이벤트, 프론트엔드, 세션 (U-061 ~ U-073)
- G. 백그라운드 작업: 워커, 크론, Job (U-074 ~ U-080)
- H. 빌드, 아티팩트, 공급망 (U-081 ~ U-093)
- I. 설정과 비밀 (U-094 ~ U-103)
- J. 환경 분리와 프리뷰 (U-104 ~ U-108)
- K. IaC, GitOps, 변경 통제 (U-109 ~ U-120)
- 새 축·규칙 후보

표기: 🟢 코드·설정으로 확정 / 🟡 힌트, 추론 필요 / 🔴 코드에 없음 → 가정으로 처리. 티어0 = Vercel·Netlify·Supabase·Firebase 등, 티어1 = Cloud Run·ECS Fargate, 티어2 = GKE·EKS.

---

## A. 롤아웃 전략과 용량

### U-001 롤아웃 전략 명시 (RollingUpdate vs Recreate)
- **무엇/왜:** k8s Deployment의 `strategy.type: Recreate`는 기존 Pod를 모두 내린 뒤 새 Pod를 띄운다. 두 버전을 동시에 돌릴 수 없는 앱에만 쓰는 전략이며, 정의상 다운타임이 생긴다.
- **실패 양상:** 배포마다 새 Pod가 Ready가 될 때까지(이미지 풀 + 기동 + readiness) 전체 503. ReadWriteOnce PVC를 붙인 Deployment는 롤링이 막혀 Recreate로 바꾸는 경우가 많아서 이 함정이 함께 온다.
- **신호:** 🟢 `strategy:\n  type: Recreate`. 🟢 Deployment에 `accessModes: [ReadWriteOnce]` PVC 마운트 + replicas 1. 🟡 docker-compose `docker compose up -d`로만 배포(컨테이너 교체 시 끊김).
- **시나리오·수준:** U L1 이상에서 Recreate는 미충족. U L0이면 허용.
- **처방:** 티어1: 기본이 롤링(Cloud Run 리비전 교체, ECS rolling). 티어2: `RollingUpdate`로 바꾸고 RWO 볼륨 의존을 오브젝트 스토리지로 옮김(D-PRE-002와 연동).
- **검증:** 부하 중 롤아웃하며 5xx 수를 셈(P4 U L1).
- **비용 영향:** 중립. 롤링은 서지만큼 일시 자원이 더 든다.
- **출처:** https://kubernetes.io/docs/concepts/workloads/controllers/deployment/ (Recreate: 새 Pod 생성 전에 기존 Pod를 모두 종료)

### U-002 maxSurge/maxUnavailable과 replica 수의 조합
- **무엇/왜:** 기본값은 둘 다 25%이고, maxUnavailable은 내림, maxSurge는 올림으로 절대 수를 계산한다. replica가 적으면 백분율이 의도와 다르게 계산된다.
- **실패 양상:** `maxSurge: 0` + replicas 1이면 maxUnavailable이 1이 되어야 진행되므로 기존 Pod를 먼저 내리고 용량이 0이 된다. `maxUnavailable: 50%` + replicas 2면 한 번에 절반을 내려 피크 중 배포 시 남은 Pod가 과부하된다.
- **신호:** 🟢 `rollingUpdate.maxSurge: 0` 또는 `maxUnavailable`이 replicas와 같음. 🟢 replicas 1 + 전략 미지정(기본 25%: unavailable 0, surge 1 → 안전). 🟡 HPA min 1.
- **시나리오·수준:** U L1 이상.
- **처방:** 티어2: 작은 서비스는 `maxSurge: 1, maxUnavailable: 0`을 명시. 티어1: ECS는 U-011 참고.
- **검증:** `kubectl rollout status` 동안 Ready Pod 수가 desired 아래로 내려가지 않는지 기록(부하 중 롤아웃).
- **비용 영향:** 약간 증가. 롤아웃 동안 서지 Pod만큼.
- **출처:** https://kubernetes.io/docs/concepts/workloads/controllers/deployment/ (기본 25%/25%, maxUnavailable 내림·maxSurge 올림, 둘 다 0일 수 없음)

### U-003 단일 인스턴스 서비스의 배포 중 공백
- **무엇/왜:** replicas 1(또는 Cloud Run max 1, ECS desired 1)은 롤링 자체는 가능해도, 새 인스턴스 기동이 실패하거나 느리면 대체 용량이 없다.
- **실패 양상:** 새 버전 Pod가 CrashLoop인데 maxUnavailable이 1이면 이미 기존 Pod가 내려가 전체 장애. 노드 drain 때도 같은 공백.
- **신호:** 🟢 `replicas: 1` 및 HPA 없음. 🟢 ECS `desired_count = 1`. 🟢 Cloud Run `max_instance_count = 1`(웹소켓·인메모리 상태 때문에 일부러 1로 둔 경우가 많음).
- **시나리오·수준:** U L1 이상이면 경고, U L2 이상이면 최소 2.
- **처방:** 티어1·2: 최소 2개 + maxUnavailable 0. 상태 때문에 1로 묶여 있다면 T-CTL-001(상태 외부화)이 선행 처방.
- **검증:** 일부러 기동 실패 이미지를 배포해도 기존 인스턴스가 응답을 유지하는지 확인.
- **비용 영향:** 증가. 상시 인스턴스 1개분.
- **출처:** https://kubernetes.io/docs/concepts/workloads/controllers/deployment/ · https://kubernetes.io/docs/tasks/run-application/configure-pdb/ (단일 인스턴스는 PDB로도 다운타임을 피할 수 없음)

### U-004 HPA가 있는 Deployment에 `spec.replicas` 하드코딩
- **무엇/왜:** HPA를 쓰면 매니페스트에서 `spec.replicas`를 빼야 한다. 남겨 두면 `kubectl apply`(배포)할 때마다 그 값이 HPA 결정을 덮어쓴다.
- **실패 양상:** 피크 중 HPA가 15개로 늘려 놓았는데 배포가 `replicas: 2`를 적용해 순간적으로 13개가 종료된다. 배포가 곧 장애가 된다.
- **신호:** 🟢 같은 이름의 Deployment에 `spec.replicas` + `HorizontalPodAutoscaler.scaleTargetRef`가 동시에 있음(kustomize build 결과 기준). 🟢 Helm 차트의 `replicaCount`가 autoscaling 활성 시에도 렌더됨.
- **시나리오·수준:** U L1 이상 + HPA 존재.
- **처방:** 티어2: Deployment에서 `replicas` 제거(첫 생성 시 1이 되므로 HPA minReplicas로 즉시 보정). GitOps면 `ignoreDifferences`로 replicas 무시.
- **검증:** 부하로 HPA를 올려 둔 상태에서 배포하고 Pod 수가 떨어지지 않는지 확인.
- **비용 영향:** 중립.
- **출처:** https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/ ("Migrating Deployments and StatefulSets to horizontal autoscaling": spec.replicas 제거 권고)

### U-005 서지 Pod를 받아줄 용량 (쿼터·노드 여유)
- **무엇/왜:** 롤링은 maxSurge만큼 Pod를 더 띄운다. ResourceQuota나 노드 여유가 없으면 서지 Pod가 Pending에 머물고 롤아웃이 멈춘다.
- **실패 양상:** 배포가 `progressDeadlineSeconds`(기본 600초)까지 진행되지 않다가 실패로 표시된다. 자동 롤백은 없으므로 구버전과 Pending 신버전이 섞인 채 방치된다.
- **신호:** 🟢 `ResourceQuota`의 `requests.cpu` 합이 (replicas+surge)×requests보다 작음. 🟡 노드 그룹 max = 현재 노드 수(클러스터 오토스케일러 없음). 🔴 실제 노드 여유.
- **시나리오·수준:** U L1 이상, 티어2.
- **처방:** 티어2: 쿼터를 서지 포함 값으로 계산, Cluster Autoscaler/Karpenter 또는 Autopilot. 티어1: 플랫폼이 용량을 관리하므로 해당 없음(단 계정 할당량 확인).
- **검증:** 쿼터를 최소치로 둔 스테이징에서 배포해 Pending 여부 관찰.
- **비용 영향:** 약간 증가.
- **출처:** https://kubernetes.io/docs/concepts/workloads/controllers/deployment/ (progressDeadlineSeconds 기본 600초, 초과 시 실패로 표시만 하고 자동 롤백하지 않음)

### U-006 minReadySeconds로 "기동 직후 죽는" 버전 걸러내기
- **무엇/왜:** `minReadySeconds` 기본값은 0이라 Ready가 되는 즉시 available로 치고 다음 Pod를 교체한다. 기동 후 수십 초 뒤에 죽는 버그(커넥션 풀 고갈, 지연 초기화 실패)는 롤아웃이 끝난 뒤에 드러난다.
- **실패 양상:** 모든 Pod가 새 버전으로 바뀐 뒤 일제히 CrashLoop. 이미 구버전 ReplicaSet은 0이다.
- **신호:** 🟢 `minReadySeconds` 미설정. 🟡 앱이 기동 후 백그라운드 초기화(캐시 워밍, 외부 연결)를 함.
- **시나리오·수준:** U L2 이상.
- **처방:** 티어2: `minReadySeconds: 10~30`(앱 특성 기준). 티어1(ECS): 헬스체크 유예 + 서킷 브레이커, Cloud Run: 점진 트래픽(U-012).
- **검증:** 기동 20초 후 종료하는 실패 버전을 배포해 롤아웃이 첫 Pod에서 멈추는지 확인.
- **비용 영향:** 중립. 배포 시간이 늘어난다.
- **출처:** https://kubernetes.io/docs/concepts/workloads/controllers/deployment/ (minReadySeconds 기본 0)

### U-007 롤아웃 완료 대기와 실패 판정을 파이프라인이 한다
- **무엇/왜:** `kubectl apply`는 매니페스트 제출만 하고 성공을 기다리지 않는다. k8s는 progressDeadline을 넘겨도 롤백하지 않는다. 파이프라인이 `rollout status --timeout`으로 기다리고 실패 시 조치해야 한다.
- **실패 양상:** CI가 초록색인데 실제로는 새 Pod가 ImagePullBackOff. 다음 배포가 겹쳐 원인 추적이 어려워진다.
- **신호:** 🟢 배포 스크립트에 `kubectl apply`만 있고 `rollout status`가 없음. 🟢 `progressDeadlineSeconds` 미설정(기본 600). 🟢 simple-web-app `docs/deploy.md`는 `rollout status --timeout=300s`를 씀(충족 예).
- **시나리오·수준:** U L1 이상.
- **처방:** 티어2: `kubectl rollout status deploy/x --timeout=...` 실패 시 `kubectl rollout undo`. 티어1: `gcloud run deploy`는 리비전 Ready까지 기다림, ECS는 서킷 브레이커(U-033).
- **검증:** 존재하지 않는 이미지 태그로 배포해 파이프라인이 실패하고 되돌리는지 확인.
- **비용 영향:** 중립.
- **출처:** https://kubernetes.io/docs/concepts/workloads/controllers/deployment/ (진행 기한 초과 시 실패 표시만, `kubectl rollout undo`)

### U-008 롤백할 이전 버전이 남아 있는가 (revisionHistoryLimit, 배포 보존)
- **무엇/왜:** Deployment는 이전 ReplicaSet을 `revisionHistoryLimit`(기본 10)만큼 보관해 `rollout undo`에 쓴다. 0으로 두면 롤백할 대상이 없다. 티어0·1도 이전 배포·리비전 보존 정책이 롤백 가능 범위를 정한다.
- **실패 양상:** 장애 중 "이전 버전으로" 되돌리려는데 이미지·리비전이 지워져 재빌드부터 해야 한다.
- **신호:** 🟢 `revisionHistoryLimit: 0`. 🟢 레지스트리 수명 주기 규칙이 최근 N개만 보관하며 N이 작음. 🟡 Vercel 배포 보존(Deployment Retention) 설정 짧음.
- **시나리오·수준:** U L1 이상.
- **처방:** 티어0: Vercel Instant Rollback(Hobby는 직전 배포만, Pro·Enterprise는 프로덕션에 연결됐던 배포 전부). 티어1: Cloud Run 리비전 유지, ECS 태스크 정의 리비전. 티어2: 기본값 유지 + 레지스트리 보존 ≥ 롤백 창.
- **검증:** 실제로 `rollout undo`/Instant Rollback을 리허설.
- **비용 영향:** 약간 증가(이미지 저장).
- **출처:** https://kubernetes.io/docs/concepts/workloads/controllers/deployment/ (revisionHistoryLimit 기본 10) · https://vercel.com/docs/instant-rollback

### U-009 블루그린 배포의 적용 조건
- **무엇/왜:** 두 개의 완전한 환경을 두고 라우터를 전환한다. 롤백이 라우터 되돌리기로 즉시 끝나는 것이 장점이다. 대신 스키마 변경은 앱 배포와 분리해 두 버전을 모두 지원하게 먼저 바꿔야 한다.
- **실패 양상:** 블루그린을 도입했지만 마이그레이션을 그린 배포에 묶어서, 롤백(블루로 전환) 시 블루가 바뀐 스키마에서 실패.
- **신호:** 🟢 ECS `deployment_controller { type = "CODE_DEPLOY" }`, Argo Rollouts `blueGreen:`. 🟡 두 개의 타깃 그룹/서비스 이름에 blue/green.
- **시나리오·수준:** U L2~L3. 대부분은 롤링 + 자동 롤백으로 충분하므로 L2에서 블루그린을 요구하지 않는다(과잉 방지).
- **처방:** 티어1: ECS 블루/그린(CodeDeploy) 또는 Cloud Run 태그 + 트래픽 100% 전환. 티어2: Argo Rollouts blueGreen.
- **검증:** 전환 직후 실패 지표를 주입하고 이전 환경으로 즉시 전환되는지, 전환 시간 측정.
- **비용 영향:** 증가. 전환 기간 동안 용량 2배.
- **출처:** https://martinfowler.com/bliki/BlueGreenDeployment.html (라우터 전환으로 빠른 롤백, 스키마 변경을 앱 업그레이드와 분리) ⚠️출처부적격

### U-010 카나리 배포 (일부 트래픽 먼저)
- **무엇/왜:** 새 버전을 일부 사용자에게만 먼저 보내 위험을 줄인다. 여러 버전이 동시에 돌기 때문에 스키마는 parallel change여야 한다.
- **실패 양상:** 카나리 없이 전량 배포 → 로직 오류(헬스체크는 통과하지만 결제 실패 등)가 100% 사용자에게 즉시 노출.
- **신호:** 🟢 Argo Rollouts `canary.steps`, Flagger `Canary`, Cloud Run `traffic { percent }` 분할, Gateway API `HTTPRoute` 가중치. 🔴 없으면 미충족.
- **시나리오·수준:** U L3(설계 U-CTL-008).
- **처방:** 티어0: Vercel Rolling Releases(플랜 확인 필요) 또는 피처 플래그로 대체(U-040). 티어1: Cloud Run `--no-traffic` 후 5%→50%→100%. 티어2: Argo Rollouts + 분석(U-034).
- **검증:** 카나리에 오류를 주입해 자동 중단되고 영향이 카나리 비율에 머무는지 확인.
- **비용 영향:** 약간 증가. 분석 도구와 일시 중복 용량.
- **출처:** https://martinfowler.com/bliki/CanaryRelease.html · https://docs.cloud.google.com/run/docs/rollouts-rollbacks-traffic-migration ⚠️출처부적격

### U-011 ECS minimumHealthyPercent / maximumPercent
- **무엇/왜:** ECS 롤링 배포는 두 값으로 동시에 내릴 수 있는 수와 더 띄울 수 있는 수를 정한다. minimumHealthyPercent는 올림, maximumPercent는 내림으로 계산된다.
- **실패 양상:** desired 2, min 75%면 계산 결과가 2라 아무것도 먼저 내릴 수 없고, max도 100%면 띄울 수도 없어 배포가 멈춘다. min 0%면 모든 태스크를 먼저 내려 다운타임.
- **신호:** 🟢 Terraform `aws_ecs_service.deployment_minimum_healthy_percent`, `deployment_maximum_percent`. 🟢 `desired_count`와 함께 계산.
- **시나리오·수준:** U L1 이상, 티어1(ECS).
- **처방:** 티어1: min 100 / max 200(서지 방식). 비용을 아끼려면 desired ≥ 2에서 min 50.
- **검증:** 부하 중 배포하며 healthy 태스크 수 기록.
- **비용 영향:** 서지 방식은 배포 중 일시 증가.
- **출처:** https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-type-ecs.html

### U-012 Cloud Run 리비전: 트래픽 없이 배포하고 태그 URL로 검증
- **무엇/왜:** Cloud Run은 `--no-traffic`으로 새 리비전을 띄우고 태그 URL(`https://tag---service...`)로 먼저 확인한 뒤 트래픽을 옮길 수 있다. 롤백은 이전 리비전에 100%를 주는 것이다.
- **실패 양상:** `gcloud run deploy`가 기본으로 바로 100%를 새 리비전으로 보내서 검증 없이 전량 노출.
- **신호:** 🟢 CI의 `gcloud run deploy`에 `--no-traffic`/`--tag` 없음. 🟢 Terraform `traffic { latest_revision = true percent = 100 }`만 있음.
- **시나리오·수준:** U L2 이상, 티어1(Cloud Run).
- **처방:** 티어1: `--no-traffic --tag canary` → 스모크 → `update-traffic --to-tags canary=10` → 100. 주의: 서비스 수준 최소 인스턴스는 태그 리비전에 할당되지 않는다.
- **검증:** 태그 URL 스모크 테스트를 파이프라인 게이트로.
- **비용 영향:** 중립.
- **출처:** https://docs.cloud.google.com/run/docs/rollouts-rollbacks-traffic-migration

### U-013 새 인스턴스 워밍업 (slow start)
- **무엇/왜:** 새 인스턴스는 JIT, 커넥션 풀, 로컬 캐시가 비어 있어 처음 몇 초가 느리다. 롤링 직후 전체 몫의 트래픽을 받으면 지연이 튄다.
- **실패 양상:** 배포 직후 p95 지연 급등, 타임아웃이 연쇄적으로 재시도를 부른다.
- **신호:** 🟡 JVM/대형 Next.js 서버, 기동 시 캐시 적재. 🟢 ALB 타깃 그룹 `slow_start.duration_seconds` 미설정.
- **시나리오·수준:** U L2 이상 + T L2 이상.
- **처방:** 티어1·2(ALB): slow start(라운드 로빈일 때만 가능, least outstanding requests와 함께 못 씀). 그 외: readiness 전에 앱이 스스로 워밍업.
- **검증:** 부하 중 롤아웃하며 신규 인스턴스 지연 분포 비교.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-target-group-attributes.html (Slow start mode)

---

## B. 기동과 헬스체크

### U-014 readiness probe 존재
- **무엇/왜:** readiness가 실패하면 EndpointSlice에서 Pod IP가 빠져 트래픽을 받지 않는다. 없으면 컨테이너가 시작되자마자 트래픽을 받는다.
- **실패 양상:** 롤링 중 아직 포트를 열지 않았거나 초기화 중인 Pod로 요청이 가서 connection refused/502.
- **신호:** 🟢 Deployment 컨테이너에 `readinessProbe` 없음. 🟢 ECS 타깃 그룹 헬스체크 경로가 `/`이고 앱이 인증 리다이렉트(302)를 줌. 🟢 헬스 엔드포인트 존재 여부(`ops.health_endpoint`).
- **시나리오·수준:** U L1 이상(설계 U-CTL-001).
- **처방:** 티어1: Cloud Run readiness probe(기본 successThreshold 2) 또는 최소 startup probe, ECS는 ALB 헬스체크. 티어2: `readinessProbe.httpGet /readyz`.
- **검증:** 부하 중 롤아웃 5xx 0건(P4 U L1).
- **비용 영향:** 중립.
- **출처:** https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/ · https://docs.cloud.google.com/run/docs/configuring/healthchecks

### U-015 readiness가 "실제 준비"를 반영하는가
- **무엇/왜:** 포트가 열렸다고 준비된 것은 아니다. Cloud Run은 TCP startup probe를 자동으로 넣는데(타임아웃 240초), 이는 포트 오픈만 본다.
- **실패 양상:** 프레임워크가 포트를 먼저 열고 DB 풀·설정 로드를 나중에 끝내는 경우, 첫 요청들이 500.
- **신호:** 🟢 probe가 `tcpSocket`만 씀. 🟢 `/health`가 상수 200을 반환(핸들러 본문 `return {"ok": true}`만). 🟡 앱이 기동 시 비동기 초기화(lifespan, `app.on('ready')`).
- **시나리오·수준:** U L1 이상.
- **처방:** 앱: `/readyz`가 초기화 완료 플래그를 확인. 단 공유 의존성 상태는 U-016 참고.
- **검증:** 초기화를 일부러 5초 지연시키고 롤아웃 중 오류 측정.
- **비용 영향:** 중립.
- **출처:** https://docs.cloud.google.com/run/docs/configuring/healthchecks (기본 TCP startup probe, timeoutSeconds 240·periodSeconds 240·failureThreshold 1)

### U-016 readiness가 공유 의존성(DB)에 묶여 있는가
- **무엇/왜:** readiness에서 DB를 확인하면, DB가 잠깐 느려질 때 모든 Pod가 동시에 unready가 되어 엔드포인트가 0이 된다. 배포 중 마이그레이션 잠금(U-049)과 겹치면 특히 위험하다.
- **실패 양상:** 마이그레이션이 테이블을 잠근 몇 초 동안 readiness가 전부 실패 → LB에 대상 없음 → 전체 503(ALB는 정상 대상이 없으면 fail-open이지만 k8s Service는 그렇지 않다).
- **신호:** 🟢 readiness 핸들러가 `SELECT 1`/`redis.ping()`을 호출. 🟡 readiness와 liveness가 같은 경로.
- **시나리오·수준:** U L2 이상(liveness 쪽은 D-CTL-004).
- **처방:** readiness는 "이 인스턴스가 요청을 처리할 수 있는가"(로컬 상태)만 본다. 의존성 장애는 앱 수준 디그레이드로 다룬다.
- **검증:** DB에 `LOCK TABLE`을 10초 걸고 엔드포인트 수가 0이 되는지 관찰.
- **비용 영향:** 중립.
- **출처:** https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/ (readiness 실패 시 모든 Service의 EndpointSlice에서 제거). 의존성을 보지 말라는 권고 자체는 일반 원칙(출처 미확인). ⚠️근거없음

### U-017 느린 기동에는 startup probe
- **무엇/왜:** startup probe가 성공할 때까지 liveness·readiness를 실행하지 않는다. 기동이 `initialDelaySeconds + failureThreshold × periodSeconds`보다 길면 startup probe를 두라고 k8s 문서가 권한다.
- **실패 양상:** liveness가 기동 중인 컨테이너를 죽여 CrashLoop. 롤아웃이 끝나지 않고, 부하가 높을 때(기동이 더 느려질 때)만 재현된다.
- **신호:** 🟢 `livenessProbe.initialDelaySeconds`가 크고(예: 60) startupProbe 없음. 🟡 JVM, 대형 모델 로딩, 기동 시 마이그레이션(U-046).
- **시나리오·수준:** U L1 이상.
- **처방:** 티어1: Cloud Run startup probe(최대 failureThreshold × periodSeconds ≤ 600초). 티어2: `startupProbe` + 짧은 liveness.
- **검증:** CPU limit을 낮춰 기동을 느리게 한 상태에서 롤아웃.
- **비용 영향:** 중립.
- **출처:** https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/ · https://docs.cloud.google.com/run/docs/configuring/healthchecks

### U-018 기동 시간 자체를 줄인다
- **무엇/왜:** 12-Factor는 기동이 몇 초 안에 끝나기를 권한다. 기동 시간은 롤아웃 길이, 롤백 속도, 스케일아웃 속도를 함께 정한다.
- **실패 양상:** 기동 90초인 서비스를 20개 롤링하면 배포 30분. 그동안 두 버전이 섞여 있고 롤백도 같은 시간이 든다.
- **신호:** 🟡 이미지 크기(U-087), 기동 시 원격 설정 다운로드, 대형 의존성 import. 🔴 실측 기동 시간은 P4에서 측정.
- **시나리오·수준:** U L2 이상.
- **처방:** 멀티 스테이지 빌드, 지연 import, 기동 시 작업 제거(U-019).
- **검증:** 컨테이너 시작부터 Ready까지 시간을 P4에서 기록하고 롤아웃 시간 예측과 비교.
- **비용 영향:** 감소. 빠른 기동은 최소 인스턴스를 줄일 여지를 준다.
- **출처:** https://12factor.net/disposability ⚠️출처부적격

### U-019 기동 명령에 빌드·설치·마이그레이션을 넣지 않는다
- **무엇/왜:** `CMD npm run build && npm start`, `npm install`을 엔트리포인트에서 실행, `prisma migrate deploy && node server.js` 같은 패턴은 기동을 느리게 하고 인스턴스마다 다른 결과를 낼 수 있다. 빌드·릴리스·실행 단계 분리 위반이다.
- **실패 양상:** 롤링 중 새 Pod 다섯 개가 동시에 빌드해 CPU 부족으로 probe 실패, 레지스트리 장애 시 기동 불가, 인스턴스마다 다른 의존성 버전.
- **신호:** 🟢 Dockerfile `CMD`/`ENTRYPOINT`/`Procfile`/`package.json` `start` 스크립트에 `build`, `install`, `migrate`, `prisma generate`, `collectstatic`. 🟢 Vercel 이외 플랫폼에서 `next build`가 start에 포함.
- **시나리오·수준:** U L1 이상.
- **처방:** 빌드는 이미지 빌드 단계로, 마이그레이션은 별도 단계(U-046)로.
- **검증:** 컨테이너 시작 로그에 빌드·설치 출력이 없는지 정적 검사.
- **비용 영향:** 감소(기동 CPU).
- **출처:** https://12factor.net/build-release-run ⚠️출처부적격

### U-020 로드밸런서 쪽 준비 상태와 Pod Ready의 정렬 (readiness gate)
- **무엇/왜:** Pod가 Ready가 되어도 ALB/NEG 타깃 등록과 헬스체크 통과는 조금 늦다. 그 사이 롤링이 이전 Pod를 내리면 LB에 정상 대상이 없을 수 있다.
- **실패 양상:** 롤아웃 막바지에 타깃 그룹이 initial/draining 대상만 가진 순간이 생겨 502/503.
- **신호:** 🟢 AWS Load Balancer Controller + `target-type: ip`인데 네임스페이스에 `elbv2.k8s.aws/pod-readiness-gate-inject=enabled` 라벨 없음. 🟢 simple-web-app은 이 라벨을 배포 계약으로 문서화(충족 예). GKE NEG는 readiness gate를 자동 주입.
- **시나리오·수준:** U L2 이상, 티어2.
- **처방:** 티어2(AWS): 네임스페이스 라벨 후 Pod 재생성. 티어2(GKE): 컨테이너 네이티브 LB(NEG) 사용.
- **검증:** 부하 중 롤아웃하며 ALB `HTTPCode_ELB_5XX_Count` 확인.
- **비용 영향:** 중립.
- **출처:** https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/deploy/pod_readiness_gate/

### U-021 실행 중인 버전을 밖에서 확인할 수 있는가
- **무엇/왜:** 롤아웃이 끝났는지, 카나리가 어느 버전인지, 롤백이 적용됐는지 확인하려면 응답이나 엔드포인트에 빌드 ID(커밋 SHA)가 드러나야 한다.
- **실패 양상:** "고쳤는데 그대로"라는 보고가 캐시 문제인지 배포 실패인지 구분이 안 된다.
- **신호:** 🟢 `/version`·`/healthz`가 `GIT_SHA`/`BUILD_ID`를 반환, 응답 헤더 `x-app-version`. 🟢 이미지 라벨 `org.opencontainers.image.revision`. 🔴 없으면 미충족.
- **시나리오·수준:** U L2 이상.
- **처방:** 빌드 인자로 SHA를 넣어 헤더·로그·지표 라벨에 노출(U-035의 버전별 지표에도 쓰임).
- **검증:** 배포 후 스모크가 기대 SHA를 확인.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

---

## C. 종료와 연결 드레이닝

### U-022 SIGTERM을 받으면 새 요청을 멈추고 진행 중인 요청을 마친다
- **무엇/왜:** 12-Factor는 SIGTERM에 우아하게 종료하라고 한다: 포트 수신을 멈추고 현재 요청을 끝낸 뒤 종료. 유예 시간이 지나면 SIGKILL이 온다.
- **실패 양상:** 롤링·스케일인·노드 교체마다 처리 중인 요청이 끊겨 5xx, 업로드 실패, 반쯤 처리된 쓰기.
- **신호:** 🟢 Node: `process.on('SIGTERM'` 없음 + `app.listen` 사용. 🟢 Python: uvicorn/gunicorn은 기본 처리, 커스텀 루프는 `signal.signal(SIGTERM` 확인. 🟢 simple-web-app worker는 `loop.add_signal_handler(SIGTERM)`(충족 예). 사실 ID `ops.sigterm_handler`.
- **시나리오·수준:** U L1 이상(설계 U-CTL-002).
- **처방:** Node: SIGTERM → `server.close()`(새 연결 거부, v19부터 유휴 연결도 닫음) → 타이머 후 `closeAllConnections()`. Next.js `next start`는 SIGTERM에 진행 중 요청과 `after()`를 마친다.
- **검증:** 긴 요청(5초) 도중 Pod 삭제 → 응답 정상 완료 확인.
- **비용 영향:** 중립.
- **출처:** https://12factor.net/disposability · https://nodejs.org/api/http.html · https://nextjs.org/docs/app/guides/self-hosting ⚠️출처부적격

### U-023 셸 형식 CMD/ENTRYPOINT와 npm이 신호를 삼킨다 (PID 1)
- **무엇/왜:** 셸 형식 ENTRYPOINT는 `/bin/sh -c`의 하위 명령으로 실행되어 신호를 전달하지 않는다. 앱이 PID 1이 아니므로 SIGTERM을 받지 못한다.
- **실패 양상:** 앱에 SIGTERM 핸들러가 있어도 호출되지 않고, 유예 시간(k8s 30초, Cloud Run 10초) 내내 기다렸다가 SIGKILL. 배포가 느려지고 진행 중 요청은 결국 끊긴다.
- **신호:** 🟢 `CMD npm start`(셸 형식), `CMD ["sh","-c","node server.js"]`, `ENTRYPOINT` 스크립트에 `exec` 없음. 🟡 `CMD ["npm","start"]`(npm이 자식에게 신호를 전달하는지는 npm 버전에 따름, 출처 미확인 → `node` 직접 실행 권장). ⚠️근거없음
- **시나리오·수준:** U L1 이상.
- **처방:** exec 형식 `CMD ["node","server.js"]`, 래퍼 스크립트 끝에 `exec "$@"`, 필요 시 tini/`--init`.
- **검증:** `docker stop` 시간이 유예 시간 전체(기본 10초)인지 즉시인지 측정.
- **비용 영향:** 중립.
- **출처:** https://docs.docker.com/reference/dockerfile/ (셸 형식은 신호를 전달하지 않고 실행 파일이 PID 1이 아님)

### U-024 preStop 지연으로 엔드포인트 제거 전파를 기다린다
- **무엇/왜:** Pod 종료 시 preStop 실행, SIGTERM 전송, 엔드포인트 제거가 **동시에** 일어난다. kube-proxy·LB가 제거를 반영하기 전에 앱이 수신을 멈추면 그 사이 들어온 요청이 실패한다.
- **실패 양상:** 롤링 중 소량이지만 꾸준한 502/connection refused. 부하가 클수록 비율이 커진다.
- **신호:** 🟢 `lifecycle.preStop` 없음. 🟢 preStop이 있지만 이미지에 `sleep`이 없음(distroless) → k8s 1.30+ `preStop.sleep` 필드 사용 여부. 🟢 simple-web-app nginx `preStop: sleep 15`(충족 예).
- **시나리오·수준:** U L2 이상(설계 U-CTL-006).
- **처방:** 티어2: `preStop: sleep 5~15` (LB 종류에 따라). 티어1: 플랫폼이 처리하므로 해당 없음.
- **검증:** 고정 RPS 부하 중 롤아웃 5xx 0건.
- **비용 영향:** 중립. 종료가 몇 초 길어진다.
- **출처:** https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/ (preStop·SIGTERM·엔드포인트 제거가 동시 진행, preStop은 유예 시간에 포함)

### U-025 종료 유예 시간 예산: preStop + 최장 요청 ≤ terminationGracePeriodSeconds
- **무엇/왜:** preStop 시간은 유예 시간(k8s 기본 30초)에 포함된다. preStop 15초 + 최장 요청 20초면 30초를 넘어 SIGKILL.
- **실패 양상:** 긴 요청이 유예 시간 끝에 잘린다. 플랫폼별로 상한이 달라 같은 앱도 결과가 다르다: Cloud Run은 SIGTERM 후 10초, ECS는 `stopTimeout` 기본 30초·최대 120초(Fargate).
- **신호:** 🟢 `terminationGracePeriodSeconds` vs `preStop` sleep vs 앱 요청 타임아웃(`server.timeout`, gunicorn `--timeout`). 🟢 ECS `stopTimeout`. 🟡 업로드·보고서 생성 경로.
- **시나리오·수준:** U L1 이상.
- **처방:** 규칙: `grace ≥ preStop + 앱 최장 요청 + 5초`. Cloud Run에서 10초 안에 못 끝나는 요청은 비동기 작업으로 전환.
- **검증:** 최장 요청 길이 요청을 보내는 중 종료.
- **비용 영향:** 중립.
- **출처:** https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/ · https://docs.cloud.google.com/run/docs/container-contract · https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definition_parameters.html (stopTimeout 기본 30초, 최대 120초)

### U-026 LB 드레이닝 시간 정렬 (ALB deregistration delay, GKE connectionDraining)
- **무엇/왜:** ALB는 타깃 해제 시 기본 300초 드레이닝한다. 대상이 그 전에 연결을 끊으면 클라이언트는 5xx를 받는다. GKE BackendConfig의 `drainingTimeoutSec`은 **기본 0(드레이닝 끔)** 이다.
- **실패 양상:** (a) ALB 기본 300초인데 Pod 유예 30초 → 롤아웃·스케일인이 불필요하게 길어지고 끊긴 연결은 5xx. (b) GKE에서 드레이닝 미설정 → 종료 Pod의 진행 중 요청이 즉시 끊김.
- **신호:** 🟢 Ingress 어노테이션 `deregistration_delay.timeout_seconds` 없음(기본 300). 🟢 GKE `BackendConfig.spec.connectionDraining` 없음. 🟢 simple-web-app은 양쪽 30초로 맞춤(충족 예).
- **시나리오·수준:** U L2 이상, 티어1(ECS+ALB)·티어2.
- **처방:** 드레이닝 ≈ 유예 시간, preStop < 드레이닝 < grace.
- **검증:** 롤아웃 중 ELB 5xx와 타깃 상태 전이(draining→unused) 시간 측정.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-target-group-attributes.html (기본 300초, 대상이 먼저 끊으면 500대 오류) · https://docs.cloud.google.com/kubernetes-engine/docs/how-to/ingress-configuration (0~3600초, 기본 0 = 비활성)

### U-027 keep-alive 유휴 타임아웃: 앱 > LB
- **무엇/왜:** ALB 유휴 타임아웃 기본은 60초이고, AWS는 앱의 유휴 타임아웃을 LB보다 길게 두라고 권한다. Node `keepAliveTimeout` 기본은 5초다.
- **실패 양상:** 앱이 5초 뒤 유휴 연결을 닫는 순간 LB가 그 연결로 요청을 보내면 502. 평시에도 간헐적이고, 배포 직후 연결 재사용이 몰릴 때 늘어난다.
- **신호:** 🟢 Node/Express에서 `server.keepAliveTimeout` 미설정 + ALB 사용. 🟢 uvicorn `--timeout-keep-alive` 미설정(기본값은 출처 미확인). 🟢 ALB `idle_timeout.timeout_seconds`. ⚠️근거없음
- **시나리오·수준:** U L1 이상(배포와 무관하게도 발생하지만 배포 시 두드러짐).
- **처방:** Node: `server.keepAliveTimeout = 65000`, `headersTimeout`은 그보다 크게. Python: 서버 keep-alive를 LB 유휴 타임아웃보다 길게.
- **검증:** 61초 간격 요청 패턴의 부하로 502 발생 여부.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-load-balancer-attributes.html (기본 60초, 앱 유휴 타임아웃을 더 크게) · https://nodejs.org/api/http.html (keepAliveTimeout 기본 5000ms)

### U-028 웹소켓·SSE 같은 장기 연결의 배포 중 처리
- **무엇/왜:** 장기 연결은 드레이닝 시간 안에 자연 종료되지 않는다. 종료 시 서버가 먼저 닫고 클라이언트가 지수 백오프로 재연결해야 한다. Cloud Run 웹소켓은 요청 타임아웃(최대 60분)을 받는다.
- **실패 양상:** 배포마다 모든 사용자의 채팅·알림 연결이 동시에 끊기고 동시에 재연결 → 재연결 폭주로 새 Pod 과부하, 끊긴 사이 메시지 유실.
- **신호:** 🟢 `socket.io`, `ws`, `@fastify/websocket`, FastAPI `WebSocket`, `EventSource`, `text/event-stream`. 🟢 클라이언트 재연결 옵션(`reconnectionDelayMax`, 지터) 유무.
- **시나리오·수준:** U L2 이상 + 실시간 기능.
- **처방:** 서버: SIGTERM 시 close 프레임 + 재연결 지시, 연결을 단계적으로 끊기. 클라이언트: 지터 있는 백오프, 마지막 수신 ID로 재개. 티어0 서버리스 함수는 장기 연결 부적합(TIER-001).
- **검증:** 연결 1,000개를 유지한 채 롤아웃하고 재연결 시간·메시지 손실 측정.
- **비용 영향:** 중립.
- **출처:** https://docs.cloud.google.com/run/docs/triggering/websockets (웹소켓도 요청 타임아웃 적용, 최대 60분, 클라이언트가 재연결을 처리해야 함) · 재연결 지터는 일반 원칙(출처 미확인) ⚠️근거없음

### U-029 긴 요청(업로드, 보고서, LLM 스트리밍)과 유예 시간
- **무엇/왜:** 유예 시간보다 긴 동기 요청은 배포 때마다 잘린다. 플랫폼마다 상한이 다르므로(U-025) 긴 작업은 비동기 작업 + 상태 조회로 바꾸는 편이 낫다.
- **실패 양상:** 배포 때마다 진행 중 업로드 실패, LLM 응답 스트림 중간 절단, 결제 후속 처리 누락.
- **신호:** 🟢 라우트 타임아웃 설정이 60초 이상, `maxDuration` 큰 값, 멀티파트 업로드 핸들러, `openai`/`anthropic` 스트리밍 호출. 🟡 PDF·이미지 처리 라이브러리.
- **시나리오·수준:** U L2 이상.
- **처방:** 업로드는 오브젝트 스토리지 사전 서명 URL로 직접, 장시간 작업은 큐로(T-CTL-006과 연결).
- **검증:** 가장 긴 경로 요청 중 롤아웃.
- **비용 영향:** 중립~약간 증가(큐).
- **출처:** https://docs.cloud.google.com/run/docs/container-contract (SIGTERM 후 10초) · https://12factor.net/disposability ⚠️출처부적격

### U-030 요청 응답 후 남는 백그라운드 작업
- **무엇/왜:** 응답을 보낸 뒤 `await` 없이 실행한 프로미스, `setTimeout`, 스레드 작업은 종료 시 사라진다. Next.js `after()`는 `next start`에서 종료 신호를 받으면 끝까지 실행하고, 플랫폼은 10~30초 드레인을 두라고 권한다.
- **실패 양상:** 이메일·웹훅 후속 처리·분석 이벤트가 배포 때마다 일부 유실. 서버리스에서는 응답 후 실행이 보장되지 않는다.
- **신호:** 🟢 핸들러에서 `void promise`, `.then()` 체인 미대기, FastAPI `BackgroundTasks`, `threading.Thread(daemon=True)`. 🟢 Next.js `after()` 사용(셀프호스팅이면 드레인 시간 확인).
- **시나리오·수준:** U L1 이상(데이터 유실 측면은 C 담당과 공유).
- **처방:** 반드시 끝나야 하는 일은 큐로. 셀프호스팅 Next.js는 드레인 시간을 유예 시간에 반영.
- **검증:** 백그라운드 작업이 있는 요청 직후 종료하고 작업 완료 여부 확인.
- **비용 영향:** 중립.
- **출처:** https://nextjs.org/docs/app/guides/self-hosting (`after` 절: SIGTERM 후 진행 중 요청과 `after()` 완료, 드레인 10~30초 권장)

### U-031 사이드카 종료 순서 (DB 프록시, 서비스 메시)
- **무엇/왜:** Cloud SQL Auth Proxy, Istio/Envoy 같은 사이드카가 앱보다 먼저 죽으면 앱의 마지막 요청이 DB·네트워크에 닿지 못한다. 네이티브 사이드카(`initContainers` + `restartPolicy: Always`)는 앱 뒤에 종료된다.
- **실패 양상:** 롤아웃 중 종료되는 Pod에서 "connection refused to 127.0.0.1:5432" 오류가 몰림.
- **신호:** 🟢 `containers:`에 `cloud-sql-proxy`/`istio-proxy`가 일반 컨테이너로 있음. 🟢 k8s 버전 ≥ 1.33인데 네이티브 사이드카 미사용.
- **시나리오·수준:** U L2 이상, 티어2.
- **처방:** 네이티브 사이드카로 전환, 또는 프록시의 종료 지연 옵션 사용.
- **검증:** 롤아웃 중 종료 Pod의 DB 오류 로그 수.
- **비용 영향:** 중립.
- **출처:** https://kubernetes.io/docs/concepts/workloads/pods/sidecar-containers/ (사이드카는 앱보다 먼저 시작하고 나중에 종료, v1.33 stable)

### U-032 노드·플랫폼 업그레이드도 배포다
- **무엇/왜:** 노드 업그레이드와 drain은 자발적 중단이라 PDB가 제한한다. 반대로 Deployment 롤링 업데이트는 PDB가 제한하지 않는다. 두 메커니즘을 혼동하면 어느 한쪽이 무방비다.
- **실패 양상:** PDB가 없어 노드 업그레이드 때 한 서비스의 Pod가 모두 같은 노드에서 동시 퇴거. 또는 `minAvailable: 1` + replica 1로 drain이 영원히 막혀 업그레이드 실패.
- **신호:** 🟢 PDB 없음(설계 U-CTL-005). 🟢 `minAvailable`이 replicas와 같음. 🟢 simple-web-app은 worker에 `maxUnavailable: 1`로 이 문제를 피함(충족 예).
- **시나리오·수준:** U L2 이상, 티어2.
- **처방:** 티어2: replicas ≥ 2 서비스에 `maxUnavailable: 1` PDB, `unhealthyPodEvictionPolicy: AlwaysAllow`. 티어1: 플랫폼 관리.
- **검증:** 부하 중 `kubectl drain` 실행해 오류율 측정(P4 D L2와 공유).
- **비용 영향:** 중립.
- **출처:** https://kubernetes.io/docs/concepts/workloads/pods/disruptions/ (롤링 업데이트는 PDB의 제한을 받지 않음) · https://kubernetes.io/docs/tasks/run-application/configure-pdb/

---

## D. 자동 롤백, 점진 배포, 릴리스 분리

### U-033 기동 실패 시 자동 롤백 (배포 서킷 브레이커)
- **무엇/왜:** ECS 배포 서킷 브레이커는 태스크가 RUNNING에 이르지 못하거나 헬스체크에 실패한 횟수가 임계치에 닿으면 배포를 FAILED로 두고, 옵션으로 마지막 COMPLETED 배포로 롤백한다. 기본 임계치는 desired × 50%이며 최소 3, 최대 200으로 묶인다. 롤링 업데이트(ECS) 컨트롤러 전용이다.
- **실패 양상:** 서킷 브레이커가 없으면 ECS는 실패하는 태스크를 계속 띄우며 배포가 끝나지 않는다. k8s는 기본으로 자동 롤백이 없다(U-007).
- **신호:** 🟢 Terraform `deployment_circuit_breaker { enable = true rollback = true }`. 🟢 Argo Rollouts/Flagger 사용. 🔴 k8s 기본 Deployment만 있으면 파이프라인 스크립트 확인 필요.
- **시나리오·수준:** U L2 이상(설계 U-CTL-007).
- **처방:** 티어0: Vercel은 빌드 실패 시 승격되지 않음(런타임 오류는 수동 Instant Rollback). 티어1: ECS 서킷 브레이커 + rollback, Cloud Run은 새 리비전이 Ready가 아니면 트래픽을 옮기지 않음. 티어2: 파이프라인의 `rollout status` 실패 → `rollout undo`, 또는 Argo Rollouts.
- **검증:** 기동 즉시 종료하는 이미지 배포 → 자동으로 이전 버전 복귀(P4 U L2).
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-circuit-breaker.html

### U-034 지표 기반 자동 중단 (오류율·지연으로 롤백)
- **무엇/왜:** 헬스체크는 통과하지만 비즈니스 로직이 깨진 버전은 서킷 브레이커가 못 잡는다. ECS는 CloudWatch 알람이 ALARM이면 배포를 실패 처리하고 롤백할 수 있고(베이크 시간 기본 5분 미만), Argo Rollouts는 AnalysisTemplate의 실패 한도를 넘으면 카나리를 중단하고 트래픽을 0으로 돌린다.
- **실패 양상:** 결제 버튼이 500을 내는 버전이 /healthz는 통과해 전량 배포된 채로 수십 분.
- **신호:** 🟢 ECS `alarms { alarm_names, enable, rollback }`. 🟢 `AnalysisTemplate`, Flagger `metrics`. 🔴 없으면 미충족.
- **시나리오·수준:** U L3(설계 U-CTL-008), 결제가 있으면 U L2에서도 권장.
- **처방:** 티어1: ECS 배포 알람(`HTTPCode_ELB_5XX_Count` 등 AWS 권장 지표). 티어2: Argo Rollouts + Prometheus 성공률 쿼리. 주의: 배포 시작 시점에 이미 ALARM이면 ECS는 그 배포 동안 알람을 무시한다.
- **검증:** 일정 비율로 500을 내는 버전 배포 → 자동 중단과 복귀 시간 측정.
- **비용 영향:** 약간 증가(알람·지표).
- **출처:** https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-alarm-failure.html · https://argo-rollouts.readthedocs.io/en/stable/features/analysis/ ⚠️출처확인필요

### U-035 버전별로 나뉜 지표
- **무엇/왜:** 카나리 판단은 "새 버전의 오류율 vs 구버전 오류율"이다. 지표에 버전 라벨이 없으면 카나리 5%의 오류가 전체 평균에 묻힌다.
- **실패 양상:** 카나리가 오류 100%여도 전체 오류율은 5% 증가에 그쳐 임계치 아래로 통과.
- **신호:** 🟢 지표 라벨에 `version`/`revision`/`pod-template-hash`, Cloud Run은 리비전별 지표 기본 제공. 🔴 앱 지표에 버전 없음.
- **시나리오·수준:** U L3.
- **처방:** 빌드 SHA를 지표·로그 공통 라벨로(U-021). 분석 쿼리는 버전 필터 사용.
- **검증:** 카나리에만 오류를 주입해 분석이 잡는지 확인.
- **비용 영향:** 약간 증가(지표 카디널리티).
- **출처:** https://argo-rollouts.readthedocs.io/en/stable/features/analysis/ (분석 쿼리 예시) · 버전 라벨 원칙은 일반 원칙(출처 미확인) ⚠️출처확인필요 ⚠️근거없음

### U-036 롤백이 실제로 가능한 상태인가 (스키마·설정·외부 상태)
- **무엇/왜:** 앱 롤백은 코드만 되돌린다. Vercel Instant Rollback은 환경 변수를 되돌리지 않고, 외부 API·DB·CMS 변경도 그대로라고 명시한다. contract 단계 마이그레이션 뒤에는 이전 코드가 없는 컬럼을 찾는다.
- **실패 양상:** 롤백했더니 더 크게 깨진다: 이전 코드가 삭제된 컬럼 조회, 새 env 이름을 읽지 못함, 새 포맷으로 쓴 캐시를 못 읽음.
- **신호:** 🟢 같은 PR에 파괴적 마이그레이션(`db.migration.destructive`)과 그 컬럼을 쓰지 않게 하는 코드 변경이 함께 있음. 🟢 env 이름 변경(`.env.example` diff).
- **시나리오·수준:** U L2 이상.
- **처방:** "직전 버전으로 롤백 가능"을 배포 불변식으로: 파괴적 변경은 한 릴리스 늦게(U-044), env는 추가 후 제거.
- **검증:** 배포 후 즉시 롤백 리허설을 P4 U L2에 포함.
- **비용 영향:** 중립.
- **출처:** https://vercel.com/docs/instant-rollback · https://martinfowler.com/bliki/ParallelChange.html ⚠️출처부적격

### U-037 Vercel Instant Rollback 후 자동 승격이 꺼진다
- **무엇/왜:** Vercel은 롤백 뒤 프로덕션 도메인 자동 할당을 끈다. 이후 main에 푸시해도 프로덕션에 반영되지 않으며 "Undo Rollback" 또는 `vercel promote`로 되살려야 한다. 크론도 롤백된 배포의 정의로 되돌아간다.
- **실패 양상:** 핫픽스를 머지했는데 프로덕션은 계속 롤백된 버전. 팀은 수정이 배포됐다고 믿는다.
- **신호:** 🟢 `vercel.json` 존재 + 런북에 promote 절차 없음. 🔴 실제 롤백 상태는 코드에 없음.
- **시나리오·수준:** U L1 이상, 티어0.
- **처방:** 런북에 "롤백 후 수정 배포는 promote로" 명시, 배포 후 스모크가 SHA 확인(U-021).
- **검증:** 스테이징 프로젝트에서 롤백 → 푸시 → 반영 여부 확인.
- **비용 영향:** 중립.
- **출처:** https://vercel.com/docs/instant-rollback · https://vercel.com/docs/cron-jobs/manage-cron-jobs (롤백 시 크론 정의도 되돌아감)

### U-038 배포 후 자동 스모크 테스트
- **무엇/왜:** 헬스체크는 프로세스 생존만 본다. 로그인 → 쓰기 → 읽기 같은 핵심 경로를 배포 직후 자동으로 돌려야 지표가 쌓이기 전에 문제를 잡는다.
- **실패 양상:** 트래픽이 적은 시간대 배포 후 몇 시간 뒤 첫 사용자가 발견.
- **신호:** 🟢 CI에 배포 후 단계(`smoke`, `k6 run`, `playwright`) 존재. 🟢 simple-web-app `k8s/tests/smoke.sh`(로컬, 충족 예). 🔴 없음.
- **시나리오·수준:** U L1 이상(L1은 수동 확인 허용, L2부터 자동).
- **처방:** 티어0: Vercel 배포 이벤트에 연결한 체크. 티어1: 태그 URL(U-012) 대상 스모크. 티어2: 롤아웃 후 Job 또는 Argo Rollouts 사전 분석.
- **검증:** 핵심 경로를 깨는 변경으로 스모크가 실패하는지 확인.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인). 설계 문서 §17.4의 합성 사용자 시나리오와 같은 스크립트를 재사용. ⚠️근거없음

### U-039 롤백 절차가 명령 하나로 정의돼 있는가
- **무엇/왜:** 장애 중에는 절차를 새로 짤 여유가 없다. `kubectl rollout undo`, `gcloud run services update-traffic --to-revisions R=100`, ECS 이전 태스크 정의, Vercel Instant Rollback 중 이 앱에 맞는 것을 미리 정해 둔다.
- **실패 양상:** "이전 이미지 태그가 뭐였지?"부터 찾느라 복구 지연. `latest` 태그라면 이전 버전을 특정할 수도 없다(U-081).
- **신호:** 🟢 README/docs/Makefile에 rollback 타깃. 🟢 GitOps면 Git revert가 곧 롤백. 🔴 없음.
- **시나리오·수준:** U L1 이상.
- **처방:** 티어별 롤백 명령을 리포트에 생성해 넣는다.
- **검증:** P4에서 롤백 명령 실행 시간 측정.
- **비용 영향:** 중립.
- **출처:** https://kubernetes.io/docs/concepts/workloads/controllers/deployment/ (`kubectl rollout undo`) · https://docs.cloud.google.com/run/docs/rollouts-rollbacks-traffic-migration

### U-040 피처 플래그로 배포와 릴리스를 분리 + 킬 스위치
- **무엇/왜:** 릴리스 토글은 미완성 코드를 꺼진 상태로 배포하게 해 주고, 운영 토글은 문제 기능을 배포 없이 끈다. 배포 롤백보다 빠르고 범위가 좁다.
- **실패 양상:** 위험한 기능 하나 때문에 전체 롤백 → 같이 나간 다른 수정도 되돌아감. 롤백 자체가 스키마 때문에 불가능할 때(U-036) 대안이 없다.
- **신호:** 🟢 `launchdarkly`, `@openfeature`, `unleash`, `growthbook`, `flagsmith`, `posthog` 플래그 API, Vercel Flags. 🟡 `process.env.FEATURE_*` 분기(배포 필요하므로 킬 스위치로는 약함).
- **시나리오·수준:** U L2 이상 권장, U L3에서 카나리 대체·보완.
- **처방:** 티어 공통: 플래그 서비스 또는 DB/설정 저장소 기반 토글. env 기반 플래그는 재배포가 필요하다는 점을 리포트에 표시(U-097).
- **검증:** 플래그를 끄는 데 걸리는 시간과 반영 범위 측정.
- **비용 영향:** 증가(SaaS 플래그 서비스) 또는 중립(자체 구현).
- **출처:** https://martinfowler.com/articles/feature-toggles.html ⚠️출처부적격

### U-041 피처 플래그 부채
- **무엇/왜:** 토글은 유지 비용이 있는 재고다. 릴리스 토글은 짧게 살아야 하고, 만료일·제거 작업·개수 상한을 두라고 권한다.
- **실패 양상:** 오래된 플래그 조합이 테스트되지 않은 경로를 만들고, 누군가 오래된 플래그를 잘못 켜서 죽은 코드가 되살아남.
- **신호:** 🟢 플래그 키 수, 코드에서 항상 true로 평가되는 플래그. 🟡 Git 이력상 오래된 플래그 참조.
- **시나리오·수준:** U L2 이상 + 플래그 사용 중.
- **처방:** 플래그에 만료일, CI에서 만료 플래그 검사.
- **검증:** 정적 검사로 만료 플래그 0개.
- **비용 영향:** 감소(정리 시).
- **출처:** https://martinfowler.com/articles/feature-toggles.html ⚠️출처부적격

### U-042 배포 동결과 유지보수 창 (플랫폼 자동 업그레이드 포함)
- **무엇/왜:** 대형 이벤트(예고된 오픈, 연말 성수기) 동안은 변경을 멈춘다. 이때 앱 배포만 막고 플랫폼 자동 업그레이드를 잊기 쉽다. GKE는 유지보수 창과 제외 기간을 두며, "업그레이드 없음" 제외는 최대 90일이다.
- **실패 양상:** 티켓 오픈 당일 GKE 노드 자동 업그레이드가 돌아 Pod가 재배치되며 지연 폭증.
- **신호:** 🟢 Terraform `maintenance_policy { recurring_window / maintenance_exclusion }`. 🟢 EKS·RDS 유지보수 창 설정. 🟡 T L2 신호(예고된 이벤트) + 유지보수 설정 없음.
- **시나리오·수준:** U L2 이상 + T L2 이상.
- **처방:** 티어2: 이벤트 기간 유지보수 제외, CI에 동결 기간 체크. 티어1: Cloud SQL/RDS 유지보수 창을 저트래픽 시간으로.
- **검증:** IaC에 이벤트 기간이 제외로 들어갔는지 정적 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.cloud.google.com/kubernetes-engine/docs/concepts/maintenance-windows-and-exclusions

---

## E. 스키마 마이그레이션

### U-043 스키마 변경이 마이그레이션 파일로 버전 관리되는가
- **무엇/왜:** 운영 스키마를 대시보드나 `db push`로 바꾸면 이력이 없어 다른 환경을 재현할 수 없고 마이그레이션이 어긋난다. Supabase 문서는 마이그레이션을 쓰기 시작했으면 작은 변경도 모두 마이그레이션 파일로 하라고 한다.
- **실패 양상:** 스테이징과 운영 스키마가 달라 배포 후에만 터지는 오류, 새 환경 생성 불가, 마이그레이션 적용 시 "이미 존재" 충돌.
- **신호:** 🟢 `prisma/schema.prisma` 있으나 `prisma/migrations/` 없음 + 스크립트에 `prisma db push`. 🟢 `supabase/` 있으나 `supabase/migrations/` 없음. 🟢 Django 앱에 `migrations/` 누락, SQLAlchemy `create_all()`을 운영 기동 시 호출. 사실 ID `db.migration_tool`.
- **시나리오·수준:** U L1 이상(데이터가 있으면).
- **처방:** Prisma `migrate dev`로 마이그레이션 생성 후 운영은 `migrate deploy`. Supabase `supabase migration new`/`db diff`. Alembic 도입.
- **검증:** 빈 DB에 마이그레이션 전체 적용 결과 스키마 = 운영 스키마(diff 0).
- **비용 영향:** 중립.
- **출처:** https://supabase.com/docs/guides/deployment/database-migrations · https://www.prisma.io/docs/orm/prisma-client/deployment/deploy-database-changes-with-prisma-migrate ⚠️출처확인필요

### U-044 파괴적 스키마 변경은 expand → migrate → contract로 나눈다
- **무엇/왜:** 롤링·카나리·블루그린 모두 구버전과 신버전이 같은 DB를 동시에 쓴다. 컬럼 삭제·이름 변경·NOT NULL 추가는 구버전을 깨므로, 먼저 두 버전을 모두 지원하게 확장하고, 클라이언트를 옮긴 뒤, 마지막에 축소한다.
- **실패 양상:** `ALTER TABLE ... RENAME COLUMN` 배포 순간부터 롤링이 끝날 때까지 구버전 Pod 전부가 500. 롤백도 불가(U-036).
- **신호:** 🟢 마이그레이션 SQL에 `DROP COLUMN`, `RENAME COLUMN`, `RENAME TO`, `ALTER COLUMN ... SET NOT NULL`, `ALTER COLUMN ... TYPE`, `DROP TABLE` (사실 `db.migration.destructive`). 🟢 같은 PR에서 해당 필드의 코드 사용 제거.
- **시나리오·수준:** U L2 이상(설계 U-CTL-003).
- **처방:** 3개 릴리스로 분리: (1) 새 컬럼 추가 + 이중 쓰기, (2) 백필 + 읽기 전환, (3) 이전 컬럼 삭제. Prisma도 확장·축소 2단계 예시를 제공.
- **검증:** 마이그레이션 적용 후 **구버전** 이미지로 통합 테스트 실행(N-1 호환 테스트).
- **비용 영향:** 중립(일시적으로 컬럼 중복 저장).
- **출처:** https://martinfowler.com/bliki/ParallelChange.html · https://www.prisma.io/docs/guides/data-migration ⚠️출처부적격 ⚠️출처확인필요

### U-045 ORM이 "이름 변경"을 "삭제 + 추가"로 생성하는 함정
- **무엇/왜:** 스키마 파일에서 필드 이름을 바꾸면 마이그레이션 생성기가 기존 컬럼 삭제와 새 컬럼 추가로 해석할 수 있다. 데이터가 사라진다.
- **실패 양상:** 배포 후 해당 컬럼 데이터 전부 NULL. 백업 복원 외 방법 없음.
- **신호:** 🟢 같은 마이그레이션 파일에 같은 테이블의 `DROP COLUMN "a"`와 `ADD COLUMN "b"`가 함께 있고 타입이 같음.
- **시나리오·수준:** 모든 수준(데이터가 있으면).
- **처방:** 생성된 SQL을 리뷰해 `RENAME`으로 고치되, 무중단이 필요하면 U-044 단계로.
- **검증:** 마이그레이션 lint에서 같은 파일 DROP+ADD 패턴 경고.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인). Prisma 문서에서 생성된 마이그레이션을 직접 편집할 수 있다는 점은 확인(https://www.prisma.io/docs/orm/prisma-migrate/workflows/customizing-migrations)했으나 rename→drop/add 동작을 명시한 문장은 찾지 못함. ⚠️출처확인필요 ⚠️근거없음

### U-046 마이그레이션 실행 위치: 앱 기동이 아니라 별도 단계
- **무엇/왜:** 마이그레이션 같은 일회성 관리 작업은 같은 릴리스·같은 설정으로 별도 프로세스에서 돌린다. Prisma는 `migrate deploy`를 CI/CD 파이프라인에서 실행하라고 권한다. 앱 기동마다 돌리면 replica 수만큼 동시에 실행되고, 실패 시 모든 Pod가 기동 실패한다.
- **실패 양상:** 마이그레이션이 오래 걸리면 startup/liveness probe가 Pod를 죽이고 다시 시작 → 마이그레이션이 중간에 끊기고 재시도 반복. 롤링 중 새 Pod가 스키마를 바꾸는 동안 구 Pod가 계속 트래픽을 받아 충돌.
- **신호:** 🟢 `start`/`CMD`/`entrypoint.sh`에 `migrate deploy`, `alembic upgrade head`, `manage.py migrate`, `knex migrate:latest`. 🟢 앱 코드에서 `runMigrations()` 호출. 🟢 k8s `Job`/`initContainer`, ECS 일회성 태스크, Cloud Run Job 존재 여부. simple-web-app은 `db-migrate` Job(충족 예).
- **시나리오·수준:** U L2 이상(설계 U-CTL-004). U L1에서는 잠금이 있으면 허용.
- **처방:** 티어0: Vercel은 빌드 단계에서 실행하는 경우가 많으나 프리뷰 빌드 문제(U-105) 주의 → CI 단계 권장. 티어1: Cloud Run Job / ECS run-task를 배포 전에. 티어2: Job 또는 Argo CD PreSync 훅.
- **검증:** 마이그레이션에 `pg_sleep(60)`을 넣어 배포해 앱 Pod가 영향받지 않는지 확인.
- **비용 영향:** 중립.
- **출처:** https://12factor.net/admin-processes · https://www.prisma.io/docs/orm/prisma-client/deployment/deploy-database-changes-with-prisma-migrate ⚠️출처부적격 ⚠️출처확인필요

### U-047 동시 실행 직렬화 (마이그레이션 잠금)
- **무엇/왜:** 여러 인스턴스·여러 파이프라인이 같은 마이그레이션을 동시에 돌리면 이중 적용이나 이력 테이블 충돌이 난다. advisory lock 등으로 한 번에 하나만 돌게 해야 한다.
- **실패 양상:** 두 Pod가 같은 `CREATE TABLE`을 동시에 실행해 하나가 실패하고 기동 실패 → CrashLoop. 이력 테이블에 중복 행.
- **신호:** 🟢 자체 마이그레이션 러너에 `pg_advisory_lock`/`pg_advisory_xact_lock` 사용(simple-web-app `board/migrate.py`, 충족 예). 🟡 도구 내장 잠금 여부(Prisma·Alembic·Django 각각 다름, 이번 조사에서 공식 문장 확인 못 함). 🟢 CI 배포 job에 concurrency 그룹(U-119).
- **시나리오·수준:** U L1 이상 + 인스턴스 2개 이상.
- **처방:** 별도 단계 1회 실행(U-046)이 가장 확실. 앱 기동 실행을 유지한다면 잠금 확인.
- **검증:** 마이그레이션 러너를 동시에 3개 실행해 한 번만 적용되는지.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인). 도구별 잠금 동작은 공식 문서에서 확인하지 못함. ⚠️근거없음

### U-048 마이그레이션과 롤아웃의 순서
- **무엇/왜:** "마이그레이션 완료 후 앱 롤아웃"이 기본이다. 동시에 시작하면 새 코드가 아직 없는 컬럼을 조회한다. 동시 진행을 택하면 새 코드도 이전 스키마에서 동작해야 한다.
- **실패 양상:** 새 Pod가 마이그레이션보다 먼저 Ready → 새 컬럼 조회 500. simple-web-app 문서도 "첫 배포에서는 테이블이 만들어지기 전 몇 초 동안 API가 5xx를 낼 수 있다"고 적는다.
- **신호:** 🟢 `kubectl apply -k`가 Job과 Deployment를 함께 적용(simple-web-app `docs/deploy.md` 5단계, 의도적 차이로 문서화). 🟢 Argo CD `PreSync` 훅 / sync-wave 음수 값 사용 여부.
- **시나리오·수준:** U L2 이상.
- **처방:** 티어2: Argo CD PreSync 훅 또는 파이프라인에서 Job 완료 대기 후 Deployment 적용. 티어1: 배포 전 Job 실행.
- **검증:** 컬럼 추가 마이그레이션 + 그 컬럼을 읽는 코드를 한 번에 배포하며 5xx 측정.
- **비용 영향:** 중립.
- **출처:** https://argo-cd.readthedocs.io/en/stable/user-guide/sync-waves/ (PreSync로 DB 마이그레이션 먼저, 웨이브 순서) ⚠️출처확인필요

### U-049 DDL 잠금 대기에 `lock_timeout`을 건다
- **무엇/왜:** 대부분의 `ALTER TABLE`은 ACCESS EXCLUSIVE 잠금을 잡고, 이 잠금은 일반 `SELECT`까지 막는다. 잠금 요청은 충돌하는 잠금이 풀릴 때까지 무기한 기다리며, 그 사이 뒤에 온 쿼리들도 줄을 선다. `lock_timeout` 기본값 0은 무제한이다.
- **실패 양상:** 오래 도는 분석 쿼리 하나 때문에 `ALTER TABLE`이 대기 → 그 뒤의 모든 읽기·쓰기가 대기 → 커넥션 풀 고갈 → 전체 장애. 정작 DDL 자체는 1ms짜리였다.
- **신호:** 🟢 마이그레이션 SQL에 `ALTER TABLE`이 있고 `SET lock_timeout` 없음. 🟢 마이그레이션 러너가 세션 설정을 하지 않음.
- **시나리오·수준:** U L2 이상 + PostgreSQL.
- **처방:** 마이그레이션 세션에 `SET lock_timeout = '3s'`(값은 서비스 기준) + 실패 시 재시도. postgresql.conf 전역 설정은 권장되지 않으므로 세션/역할 단위로.
- **검증:** 다른 세션에서 `BEGIN; SELECT ... FOR SHARE`를 잡아 둔 채 마이그레이션 → 빠르게 실패하고 앱 쿼리는 계속 처리되는지.
- **비용 영향:** 중립.
- **출처:** https://www.postgresql.org/docs/current/explicit-locking.html (ACCESS EXCLUSIVE는 SELECT도 막음, 무기한 대기) · https://www.postgresql.org/docs/current/runtime-config-client.html (lock_timeout 기본 0, 전역 설정 비권장)

### U-050 인덱스는 `CREATE INDEX CONCURRENTLY`로, 그런데 트랜잭션 밖에서
- **무엇/왜:** 일반 `CREATE INDEX`는 끝날 때까지 쓰기를 막는다. `CONCURRENTLY`는 쓰기를 막지 않지만 트랜잭션 블록 안에서 실행할 수 없고, 실패하면 INVALID 인덱스를 남긴다.
- **실패 양상:** 큰 테이블 인덱스 생성 수 분 동안 INSERT/UPDATE 전부 대기. 또는 `CONCURRENTLY`를 썼는데 마이그레이션 도구가 파일 전체를 트랜잭션으로 감싸 즉시 오류.
- **신호:** 🟢 `CREATE INDEX`/`CREATE UNIQUE INDEX`에 `CONCURRENTLY` 없음 + 대상 테이블이 사용자 데이터. 🟢 러너가 파일 전체를 `conn.transaction()`으로 감쌈(simple-web-app `board/migrate.py`가 모든 파일을 한 트랜잭션에서 실행 → 이 러너로는 `CONCURRENTLY`를 쓸 수 없음). 🟢 Django 마이그레이션 `atomic = False` 여부, `AddIndexConcurrently`.
- **시나리오·수준:** U L2 이상 + PostgreSQL + 데이터 증가 예상.
- **처방:** 비트랜잭션 마이그레이션 경로 마련(Django `atomic = False`, 러너에 파일별 no-transaction 표시), 실패 시 `DROP INDEX` 후 재시도 또는 `REINDEX INDEX CONCURRENTLY`.
- **검증:** 100만 행 테이블에 인덱스 생성 중 쓰기 지연 측정.
- **비용 영향:** 중립.
- **출처:** https://www.postgresql.org/docs/current/sql-createindex.html · https://docs.djangoproject.com/en/5.2/topics/migrations/ (PostgreSQL에서 기본 트랜잭션, `atomic = False`)

### U-051 테이블 재작성을 유발하는 DDL
- **무엇/왜:** 컬럼 타입 변경, volatile 기본값(`clock_timestamp()` 등), stored generated 컬럼, identity 컬럼 추가는 테이블 전체를 다시 쓴다(ACCESS EXCLUSIVE 상태로). 상수 기본값 추가는 메타데이터만 바꿔 빠르다.
- **실패 양상:** 1,000만 행 테이블 `ALTER COLUMN TYPE bigint`가 수십 분 동안 테이블을 완전히 잠금 → 해당 기능 전면 중단.
- **신호:** 🟢 `ALTER COLUMN ... TYPE`, `ADD COLUMN ... DEFAULT (now()|random()|gen_random_uuid()|clock_timestamp())`, `GENERATED ALWAYS AS ... STORED`, `GENERATED ... AS IDENTITY`. 🔴 테이블 크기(가정으로 처리).
- **시나리오·수준:** U L2 이상.
- **처방:** 새 컬럼 추가 → 배치 백필(U-053) → 전환 → 이전 컬럼 삭제. volatile 기본값은 기본값 없이 추가 후 UPDATE, 그다음 기본값 설정.
- **검증:** 스테이징에서 운영 규모 데이터로 마이그레이션 시간과 잠금 시간 측정.
- **비용 영향:** 중립.
- **출처:** https://www.postgresql.org/docs/current/sql-altertable.html · https://www.postgresql.org/docs/current/ddl-alter.html

### U-052 제약 조건은 `NOT VALID` 후 `VALIDATE CONSTRAINT`
- **무엇/왜:** FK·CHECK 추가는 전체 행 검사를 하며 잠금을 오래 잡는다. `NOT VALID`로 추가하면 기존 행 검사를 건너뛰고, 나중의 `VALIDATE CONSTRAINT`는 더 약한 SHARE UPDATE EXCLUSIVE 잠금으로 검사한다. `SET NOT NULL`도 전체 스캔을 한다.
- **실패 양상:** FK 추가 마이그레이션 동안 두 테이블 쓰기 정지(ADD FOREIGN KEY는 참조 테이블에도 잠금).
- **신호:** 🟢 `ADD CONSTRAINT ... FOREIGN KEY|CHECK` without `NOT VALID`. 🟢 `SET NOT NULL` on 기존 테이블.
- **시나리오·수준:** U L2 이상 + PostgreSQL.
- **처방:** 2단계: `ADD CONSTRAINT ... NOT VALID` → 다음 마이그레이션에서 `VALIDATE CONSTRAINT`. NOT NULL은 CHECK (col IS NOT NULL) NOT VALID → VALIDATE → SET NOT NULL 순(최신 PG에서 검사 생략 여부는 버전별 확인 필요, 출처 미확인). ⚠️근거없음
- **검증:** 대형 테이블 대상 잠금 시간 측정.
- **비용 영향:** 중립.
- **출처:** https://www.postgresql.org/docs/current/sql-altertable.html (VALIDATE CONSTRAINT는 SHARE UPDATE EXCLUSIVE, NOT VALID 2단계 권장)

### U-053 데이터 백필은 스키마 마이그레이션과 분리하고 배치로
- **무엇/왜:** Django는 PostgreSQL에서 마이그레이션 전체를 한 트랜잭션으로 실행하고, Prisma 예시도 백필을 같은 트랜잭션에 넣는다. 작은 테이블은 괜찮지만 큰 테이블 전체 UPDATE를 한 트랜잭션으로 하면 행 잠금·WAL 폭증·복제 지연이 난다.
- **실패 양상:** 백필 UPDATE가 수백만 행 잠금을 쥔 채 30분 → 해당 행을 쓰려는 사용자 요청 타임아웃, 마이그레이션 Job `activeDeadlineSeconds` 초과로 롤백되어 처음부터 다시.
- **신호:** 🟢 마이그레이션에 조건 없는 `UPDATE table SET`, Django `RunPython`에서 `.objects.all()` 루프, Prisma `dataTransform`. 🔴 테이블 크기.
- **시나리오·수준:** U L2 이상.
- **처방:** 백필은 별도 Job으로 PK 범위 배치 + 커밋, 진행 상황 저장(재시작 가능), 실행 중에도 이중 쓰기 유지.
- **검증:** 운영 규모 데이터 스테이징에서 백필 중 앱 p95 지연 측정.
- **비용 영향:** 중립.
- **출처:** https://docs.djangoproject.com/en/5.2/topics/migrations/ · https://www.prisma.io/docs/guides/data-migration · 배치 분할은 일반 원칙(출처 미확인) ⚠️출처확인필요 ⚠️근거없음

### U-054 마이그레이션에도 `statement_timeout`과 실행 시간 상한
- **무엇/왜:** 예상보다 오래 걸리는 마이그레이션은 중단되고 알려져야 한다. `statement_timeout` 기본 0은 무제한이다. 실행 단계에도 상한(k8s Job `activeDeadlineSeconds` 등)이 필요하다.
- **실패 양상:** 마이그레이션이 몇 시간째 돌며 배포 파이프라인이 무한 대기, 아무도 모름.
- **신호:** 🟢 Job `activeDeadlineSeconds`(simple-web-app 600초, 충족 예), `backoffLimit`. 🟢 마이그레이션 세션 `statement_timeout`.
- **시나리오·수준:** U L2 이상.
- **처방:** 마이그레이션 세션 statement_timeout(DDL 몇 초, 백필은 배치당), Job 데드라인, 실패 시 로그 출력 후 중단(simple-web-app 배포 스크립트 패턴).
- **검증:** `pg_sleep`을 넣은 마이그레이션이 데드라인에 끊기는지.
- **비용 영향:** 중립.
- **출처:** https://www.postgresql.org/docs/current/runtime-config-client.html · https://kubernetes.io/docs/concepts/workloads/controllers/job/

### U-055 DDL이 트랜잭션에 안 들어가는 DB (MySQL)
- **무엇/왜:** MySQL은 스키마 변경을 트랜잭션으로 감싸지 못한다. 마이그레이션 중간에 실패하면 일부만 적용된 상태가 남아 사람이 직접 정리해야 한다.
- **실패 양상:** 5개 문장 중 3번째에서 실패 → 재실행하면 1·2번이 "이미 존재"로 실패 → 배포 정지.
- **신호:** 🟢 `provider = "mysql"`(Prisma), Django `ENGINE` mysql, PlanetScale.
- **시나리오·수준:** U L1 이상 + MySQL.
- **처방:** 마이그레이션 하나에 DDL 하나, 멱등 DDL(`IF NOT EXISTS`), 온라인 스키마 변경 도구(도구별 출처 미확인). ⚠️근거없음
- **검증:** 중간 문장을 일부러 실패시켜 재실행 가능성 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.djangoproject.com/en/5.2/topics/migrations/ (MySQL은 스키마 변경 트랜잭션 미지원)

### U-056 다운 마이그레이션 대신 전진 수정(forward fix) 전략
- **무엇/왜:** 데이터를 지우는 변경은 "되돌리기 마이그레이션"으로 복구되지 않는다. expand/contract를 지키면 앱 롤백만으로 충분하고, 스키마는 앞으로만 간다.
- **실패 양상:** 장애 중 `migrate down`을 실행해 새 컬럼에 쌓인 데이터까지 삭제.
- **신호:** 🟢 `down` 마이그레이션에 `DROP`. 🟢 런북에 `migrate down`/`alembic downgrade`.
- **시나리오·수준:** U L2 이상.
- **처방:** 운영 롤백 절차에서 다운 마이그레이션 제외, contract 단계는 충분히 늦게.
- **검증:** 런북 정적 검사.
- **비용 영향:** 중립.
- **출처:** https://martinfowler.com/bliki/ParallelChange.html · forward-fix 원칙은 일반 원칙(출처 미확인) ⚠️출처부적격 ⚠️근거없음

### U-057 마이그레이션을 배포 전에 검증한다 (CI)
- **무엇/왜:** 마이그레이션 오류는 배포 중에 처음 발견하면 비싸다. CI에서 빈 DB 적용, 운영 스키마 사본 적용, 위험 DDL 정적 검사를 돈다. Prisma 문서는 운영 적용 전 마이그레이션 파일이 손으로 수정되거나 지워지지 않았는지 확인하라고 한다.
- **실패 양상:** 운영에서만 존재하는 데이터(NULL, 중복)가 제약 추가를 실패시켜 배포 중단.
- **신호:** 🟢 CI에 testcontainers/서비스 컨테이너로 Postgres + 마이그레이션 적용 단계(simple-web-app은 testcontainers 사용). 🟢 `prisma migrate diff`, `manage.py makemigrations --check`, `alembic check`. 🔴 위험 DDL 린터(squawk 등, 출처 미확인). ⚠️근거없음
- **시나리오·수준:** U L2 이상.
- **처방:** CI 단계: (1) 빈 DB에 전체 적용, (2) 스키마 drift 검사, (3) 위험 DDL 패턴 검사(U-044~U-052 신호 재사용).
- **검증:** 위험 DDL을 넣은 PR이 CI에서 막히는지.
- **비용 영향:** 중립.
- **출처:** https://www.prisma.io/docs/orm/prisma-migrate/workflows/development-and-production ⚠️출처확인필요

### U-058 Supabase·BaaS의 마이그레이션 단일 실행자
- **무엇/왜:** Supabase는 `supabase db push`로 원격에 적용하며, 팀은 한 번에 한 사람만 push하도록 조율하거나 main 머지 시 CI가 push하게 하라고 한다.
- **실패 양상:** 두 개발자가 각자 로컬에서 운영 DB로 push → 순서 꼬임, 이력 테이블 불일치(`migration repair` 필요).
- **신호:** 🟢 `supabase/migrations/` 존재 + CI 워크플로에 `supabase db push` 없음. 🟢 README에 "로컬에서 db push".
- **시나리오·수준:** U L1 이상, 티어0.
- **처방:** 티어0: GitHub Actions에서 main 머지 시 `supabase db push`, 또는 Supabase Branching.
- **검증:** 운영 DB 자격 증명이 CI 외부에 없는지 확인.
- **비용 영향:** 중립.
- **출처:** https://supabase.com/docs/guides/deployment/database-migrations

### U-059 DB 연결 문자열 전환 (DB 이전, 풀러 도입, 자격 증명 교체)
- **무엇/왜:** `DATABASE_URL`을 바꾸는 순간은 배포와 같다. 인스턴스마다 바뀌는 시점이 달라 잠시 두 DB에 나눠 쓰는 구간이 생기고, env는 재시작해야 반영된다(U-097).
- **실패 양상:** 새 DB로 전환하는 롤링 동안 일부 인스턴스는 구 DB에 쓰기 → 데이터 분기. 풀러(PgBouncer 트랜잭션 모드)로 바꾸며 prepared statement 오류.
- **신호:** 🟢 `DATABASE_URL`과 `DIRECT_URL`(Prisma) 분리 여부, 커넥션 문자열에 `pgbouncer=true`. 🟡 이전 계획 문서.
- **시나리오·수준:** U L2 이상 + DB 이전/풀러 처방(T-PRE-003)이 나온 경우.
- **처방:** 구 DB 읽기 전용 전환 → 복제 동기화 확인 → 전환 → 구 DB 차단 순. 풀러는 마이그레이션 전용 직결 URL 분리.
- **검증:** 전환 리허설 중 쓰기가 구 DB에 도달하지 않는지 확인.
- **비용 영향:** 일시 증가(병행 운영).
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### U-060 운영 데이터 고유 상태에 의존하는 마이그레이션
- **무엇/왜:** 유니크 인덱스 추가, enum 값 제거, NOT NULL 추가는 운영 데이터에 위반 행이 있으면 실패한다. 개발 DB에는 그런 데이터가 없어 CI가 통과한다.
- **실패 양상:** 배포 중 마이그레이션 실패 → U-048 순서에 따라 앱은 이미 새 버전 또는 배포 정지.
- **신호:** 🟢 `CREATE UNIQUE INDEX`, `ADD CONSTRAINT ... UNIQUE`, enum 값 제거, `SET NOT NULL`. 
- **시나리오·수준:** U L2 이상.
- **처방:** 마이그레이션 앞에 위반 행 검사 쿼리(사전 점검 Job), 또는 운영 스냅샷(마스킹)으로 CI 검증.
- **검증:** 위반 데이터를 심은 스테이징에서 사전 점검이 배포를 막는지.
- **비용 영향:** 중립.
- **출처:** https://www.postgresql.org/docs/current/sql-createindex.html (유니크 위반 시 CONCURRENTLY 빌드 실패와 INVALID 인덱스)

---

## F. 버전 간 호환성: API, 이벤트, 프론트엔드, 세션

### U-061 API는 직전 버전(N-1)과 동시에 돌 수 있어야 한다
- **무엇/왜:** 롤링·카나리 동안 구버전과 신버전 서버가 섞여 있고, 브라우저에는 구버전 프론트가 떠 있다. 요청 필드 필수화, 응답 필드 제거·이름 변경은 그 구간에 바로 깨진다.
- **실패 양상:** 신버전 프론트가 새 필드를 보내는데 요청이 구버전 서버로 가서 400. 또는 구버전 프론트가 사라진 응답 필드를 읽어 화면 오류.
- **신호:** 🟡 같은 PR에서 API 스키마(zod/pydantic 모델, OpenAPI)의 필수 필드 추가·필드 제거와 프론트 변경이 함께 있음. 🟢 모노레포에서 프론트와 API가 별도 배포 단위.
- **시나리오·수준:** U L1 이상(L1은 순서만 맞추면 됨), U L2에서 규칙으로 검사.
- **처방:** 필드 추가는 선택으로 시작, 제거는 다음 릴리스. 서버 먼저 배포 → 프론트 배포 순서. 티어0은 Skew Protection(U-070)으로 일부 완화.
- **검증:** 구버전 클라이언트 테스트 스위트를 신버전 서버에 실행(그 반대도).
- **비용 영향:** 중립.
- **출처:** https://vercel.com/docs/skew-protection (버전 스큐 정의와 필수 필드 추가 예시) · https://martinfowler.com/bliki/ParallelChange.html ⚠️출처부적격

### U-062 오래 사는 외부 클라이언트(모바일 앱, SDK, 웹훅 소비자)
- **무엇/왜:** 모바일 앱은 사용자가 업데이트하지 않으면 몇 달 전 버전이 계속 API를 부른다. 웹 프론트처럼 새로고침으로 해결되지 않는다.
- **실패 양상:** API 필드 제거 배포 후 구버전 앱 사용자 전원이 크래시. 강제 업데이트 장치가 없으면 복구 수단 없음.
- **신호:** 🟢 `expo`, `react-native`, `flutter`, `ios/`, `android/` 디렉터리. 🟢 공개 API 문서, `/v1/` 경로. 🟡 API 키 발급 기능.
- **시나리오·수준:** U L2 이상 + 외부 클라이언트 존재.
- **처방:** URL 또는 헤더 기반 API 버전, 폐기 일정, 최소 지원 앱 버전 검사(강제 업데이트 응답).
- **검증:** 지원하는 가장 오래된 클라이언트 계약 테스트를 CI에 유지.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### U-063 이벤트·메시지 스키마 호환
- **무엇/왜:** 큐·스트림 메시지는 생산자와 소비자가 따로 배포되고, 큐에 남아 있는 동안 버전이 섞인다. Protobuf 규칙: 필드 번호 재사용 금지, 삭제한 번호는 reserved, 필드 추가·삭제는 wire-safe, 번호 변경은 unsafe.
- **실패 양상:** 소비자를 먼저 배포했더니 아직 구 형식인 메시지를 못 읽고 DLQ로. JSON 메시지 필드 이름 변경으로 신규 소비자가 KeyError.
- **신호:** 🟢 `bullmq`, `celery`, `kafkajs`, `@aws-sdk/client-sqs`, Redis Streams `XADD`. 🟢 `.proto`, Avro 스키마, 메시지 타입 정의 파일 변경. 🟢 메시지에 `version`/`schema_version` 필드 유무.
- **시나리오·수준:** U L2 이상 + 비동기 메시징.
- **처방:** 메시지 버전 필드, 소비자는 알 수 없는 필드 무시(관대한 수신), 생산자 형식 변경은 소비자가 양쪽을 다 읽게 된 뒤.
- **검증:** 구 형식 메시지를 큐에 넣은 상태로 신규 소비자 배포.
- **비용 영향:** 중립.
- **출처:** https://protobuf.dev/programming-guides/proto3/ (메시지 타입 업데이트 규칙) ⚠️출처확인필요

### U-064 큐에 남은 작업과 생산자·소비자 배포 순서
- **무엇/왜:** 작업 큐에는 구버전 코드가 넣은 페이로드가 배포 후에도 남는다. 작업 함수 이름·인자를 바꾸면 남은 작업이 실패한다.
- **실패 양상:** Celery 태스크 이름 변경 후 큐에 남은 수천 건이 "unregistered task"로 실패. BullMQ 잡 데이터 구조 변경으로 워커 예외 반복.
- **신호:** 🟢 태스크 함수 이름/시그니처 변경 diff, `@app.task(name=...)` 미지정(모듈 경로가 이름이 됨, 출처 미확인). 🟢 웹과 워커가 같은 이미지(simple-web-app board 이미지를 board-api·board-worker가 공유). ⚠️근거없음
- **시나리오·수준:** U L2 이상 + 워커.
- **처방:** 작업 이름 고정, 인자 추가는 기본값과 함께, 큐를 비운 뒤 구 핸들러 제거. 소비자 먼저(양쪽 읽기) → 생산자 배포.
- **검증:** 구버전으로 큐를 채운 뒤 신버전 워커 배포, 실패율 측정.
- **비용 영향:** 중립.
- **출처:** https://protobuf.dev/programming-guides/proto3/ (호환 변경 원칙) · 작업 큐 이름 고정은 일반 원칙(출처 미확인) ⚠️출처확인필요 ⚠️근거없음

### U-065 프론트엔드 해시 청크와 구버전 클라이언트 (배포 중 청크 로드 실패)
- **무엇/왜:** SPA는 해시가 붙은 청크를 지연 로드한다. 새 배포가 이전 자산을 지우면, 배포 전에 페이지를 연 사용자가 다음 화면으로 갈 때 이전 해시의 청크를 요청해 404가 난다. Vite는 이때 `vite:preloadError` 이벤트를 낸다.
- **실패 양상:** 배포 직후 "Failed to fetch dynamically imported module"/`ChunkLoadError`가 급증, 화면이 하얗게 멈춤. 롤링 중에는 HTML은 신버전, 청크 요청은 구버전 Pod로 가서도 같은 일이 생긴다.
- **신호:** 🟢 Vite/webpack 빌드 + 라우트 지연 로드(`lazy(() => import(`). 🟢 자산을 컨테이너 이미지 안에서 서빙(simple-web-app nginx: 이미지 교체 시 이전 해시 파일이 사라짐). 🟢 `vite:preloadError`/`ChunkLoadError` 핸들러 유무.
- **시나리오·수준:** U L1 이상 + SPA.
- **처방:** (1) 자산을 오브젝트 스토리지/CDN에 누적 업로드하고 이전 버전을 일정 기간 보존, (2) `vite:preloadError`에서 1회 새로고침, (3) 티어0은 플랫폼이 이전 배포 자산을 보존(Vercel Skew Protection, U-070).
- **검증:** 구버전 페이지를 연 브라우저를 유지한 채 배포 → 다른 라우트로 이동 → 오류 여부(Playwright로 자동화).
- **비용 영향:** 약간 증가(자산 보존 저장).
- **출처:** https://vite.dev/guide/build (Load Error Handling: 새 배포가 이전 자산을 지우면 import 오류, `vite:preloadError`)

### U-066 HTML은 재검증, 해시 자산은 immutable
- **무엇/왜:** 해시가 든 자산은 `max-age=31536000, immutable`로 길게, 진입 HTML은 `no-cache`로 매번 재검증해야 배포가 사용자에게 반영된다. Next.js는 해시 자산에 immutable을 자동으로 붙인다.
- **실패 양상:** `index.html`이 CDN·브라우저에 길게 캐시되어 배포 후에도 구버전 화면, 또는 구 HTML이 이미 지운 청크를 가리켜 U-065와 결합.
- **신호:** 🟢 nginx/`vercel.json`/`firebase.json`/CloudFront 동작에서 HTML 캐시 헤더. 🟢 simple-web-app nginx: `/assets/` immutable, `/index.html` no-cache(충족 예). 🟢 `Cache-Control` 미설정 + CDN 기본 TTL.
- **시나리오·수준:** U L1 이상 + 정적 프론트.
- **처방:** 위 두 헤더 + CDN에서 HTML 캐시 금지 또는 배포 시 무효화.
- **검증:** 배포 후 `curl -I`로 헤더 확인, 새 빌드 ID가 즉시 보이는지.
- **비용 영향:** 감소(자산 캐시 적중 증가).
- **출처:** https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control · https://nextjs.org/docs/app/guides/self-hosting (immutable 자산 헤더는 덮어쓸 수 없음) ⚠️출처부적격

### U-067 셀프호스팅 Next.js의 버전 스큐: `deploymentId`
- **무엇/왜:** 여러 인스턴스·롤링 배포에서 Next.js는 자산 누락, Server Function ID 불일치, 프리페치 데이터 비호환을 겪을 수 있다. `deploymentId`를 설정하면 클라이언트와 서버의 배포 ID를 비교해 불일치 시 전체 새로고침한다.
- **실패 양상:** 롤링 중 클라이언트 내비게이션이 실패하거나 "Failed to find Server Action".
- **신호:** 🟢 `next` 의존성 + Dockerfile/`output: 'standalone'`(Vercel 외 배포) + `next.config`에 `deploymentId` 없음.
- **시나리오·수준:** U L1 이상, 티어1·2의 Next.js.
- **처방:** `deploymentId: process.env.DEPLOYMENT_VERSION`(커밋 SHA). 새로고침 시 컴포넌트 상태가 사라짐을 감안.
- **검증:** 롤링 도중 클라이언트 내비게이션 오류율 측정.
- **비용 영향:** 중립.
- **출처:** https://nextjs.org/docs/app/guides/self-hosting (Version Skew, Deployment identifier)

### U-068 Next.js 다중 인스턴스: Server Actions 암호화 키와 빌드 ID 일관성
- **무엇/왜:** Next.js는 빌드마다 Server Function 암호화 키를 새로 만든다. 인스턴스마다 키가 다르면 한 인스턴스가 암호화한 것을 다른 인스턴스가 못 푼다. 환경마다 다시 빌드하면 빌드 ID도 달라진다.
- **실패 양상:** 같은 이미지를 쓰지 않거나 인스턴스별로 빌드하면 "Failed to find Server Action" 간헐 오류. 롤링 중 구·신 인스턴스 사이에서도 발생.
- **신호:** 🟢 `"use server"` 사용 + 셀프호스팅 + `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY` 미설정. 🟢 환경별 재빌드 파이프라인 + `generateBuildId` 없음.
- **시나리오·수준:** U L1 이상 + 인스턴스 2개 이상.
- **처방:** 빌드 시 `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY`(16/24/32바이트 base64) 고정, 한 번 빌드한 이미지를 모든 인스턴스에(U-084).
- **검증:** 인스턴스 2개 뒤에서 Server Action을 반복 호출해 오류 0.
- **비용 영향:** 중립.
- **출처:** https://nextjs.org/docs/app/guides/self-hosting (Multi-Server Deployments, Build Cache)

### U-069 인스턴스 간에 공유되지 않는 프레임워크 캐시 (ISR, revalidateTag)
- **무엇/왜:** 셀프호스팅 Next.js 캐시는 기본으로 인스턴스 로컬(메모리 50MB + 디스크)이다. `revalidateTag()`는 호출한 인스턴스만 무효화한다. 배포 직후 새 Pod는 빈 캐시로 시작한다.
- **실패 양상:** 관리자가 글을 고쳤는데 Pod마다 다른 버전이 보임. 롤아웃 직후 모든 페이지가 캐시 미스로 원본(DB)에 몰림.
- **신호:** 🟢 `revalidate`, `revalidateTag`, `revalidatePath`, `'use cache'` 사용 + 셀프호스팅 + `cacheHandler` 미설정.
- **시나리오·수준:** U L2 이상 + 인스턴스 2개 이상(T 담당과 경계: 여기서는 배포·다중 버전 일관성 관점).
- **처방:** Redis 등 공유 `cacheHandler` + `refreshTags()`로 태그 동기화, `cacheMaxMemorySize: 0`.
- **검증:** 2개 인스턴스에서 revalidate 후 양쪽 응답 일치.
- **비용 영향:** 증가(공유 캐시 저장소).
- **출처:** https://nextjs.org/docs/app/guides/self-hosting (Configuring Caching, Multi-Instance Cache Coordination)

### U-070 Vercel Skew Protection 설정 확인
- **무엇/왜:** Vercel은 프레임워크가 관리하는 요청(정적 자산, 클라이언트 내비게이션, Server Actions, 프리페치)에 배포 ID를 붙여 같은 배포로 보낸다. Pro·Enterprise에서 쓸 수 있고, 2024-11-19 이후 생성된 지원 프레임워크 프로젝트는 기본 활성, 기본 최대 수명은 배포 생성 후 1일이다. 직접 쓴 `fetch()`는 자동으로 고정되지 않는다.
- **실패 양상:** Hobby 플랜이거나 오래된 프로젝트라 꺼져 있어 U-065와 같은 청크 오류. 대시보드처럼 하루 넘게 열어 두는 화면은 1일이 지나면 404. `--prebuilt` 배포에서는 쓸 수 없다.
- **신호:** 🟢 `vercel.json` + Next.js(14.1.4 미만이면 `useDeploymentId` 설정 필요). 🟢 클라이언트 컴포넌트의 `fetch('/api/...')`(고정 안 됨). 🟢 CI의 `vercel deploy --prebuilt`. 🔴 플랜·대시보드 설정은 코드에 없음 → 가정.
- **시나리오·수준:** U L1 이상, 티어0.
- **처방:** 티어0: 설정 활성 확인, 장시간 화면이면 최대 수명 상향 또는 `__vdpl` 쿠키 고정, 커스텀 fetch에 `x-deployment-id`.
- **검증:** 배포 전 탭을 연 채 배포 후 내비게이션과 커스텀 fetch 확인.
- **비용 영향:** 중립(Pro 플랜 필요 시 증가).
- **출처:** https://vercel.com/docs/skew-protection

### U-071 서비스 워커 캐시가 구버전을 붙잡는다
- **무엇/왜:** 새 서비스 워커는 이전 워커가 제어하는 클라이언트가 모두 닫힐 때까지 대기한다. `skipWaiting()`으로 바로 교체하면 구버전으로 로드된 페이지를 새 워커가 제어하게 되어 섞인다.
- **실패 양상:** (a) 사용자가 탭을 닫지 않아 며칠째 구버전 앱, 구 API 호출로 오류. (b) skipWaiting으로 구 페이지가 새 캐시의 자산을 받아 깨짐.
- **신호:** 🟢 `navigator.serviceWorker.register`, `workbox`, `next-pwa`, `vite-plugin-pwa`, `skipWaiting`, `clientsClaim`. 🟢 `sw.js` 캐시 헤더.
- **시나리오·수준:** U L1 이상 + PWA.
- **처방:** 새 워커 대기 시 "새 버전 있음" 안내 후 사용자 동의로 교체, 네비게이션 요청은 network-first, 비상 시 자기 해제(kill switch) 워커 준비.
- **검증:** 구 워커가 설치된 브라우저로 배포 후 동작 확인.
- **비용 영향:** 중립.
- **출처:** https://web.dev/articles/service-worker-lifecycle ⚠️출처확인필요

### U-072 세션·쿠키·서명 키 호환
- **무엇/왜:** 세션 저장 형식, 쿠키 이름·도메인, 서명 키를 바꾸면 배포 순간 모든 사용자가 로그아웃되거나, 롤링 중 구·신 인스턴스가 서로의 세션을 못 읽는다. Django는 `SECRET_KEY`를 바꾸면 세션·비밀번호 재설정 토큰·서명이 무효화되며, `SECRET_KEY_FALLBACKS`로 무중단 교체를 지원한다.
- **실패 양상:** 키 교체 배포 후 전원 강제 로그아웃, 진행 중 결제 플로우 실패. 롤링 중에는 요청이 어느 Pod로 가느냐에 따라 로그인 상태가 깜빡임.
- **신호:** 🟢 `SECRET_KEY`, `SESSION_SECRET`, `express-session` `secret`(배열 지원 여부), `iron-session` password, NextAuth/Auth.js `AUTH_SECRET`, JWT 서명 키 변경 diff. 🟢 세션 직렬화 객체 구조 변경.
- **시나리오·수준:** U L1 이상(로그인 있는 앱).
- **처방:** 새 키로 서명 + 이전 키로 검증(fallback/키 배열/JWKS의 `kid`) → 만료 주기 지난 뒤 이전 키 제거.
- **검증:** 키 교체 배포 전후로 기존 세션 쿠키가 유효한지 테스트.
- **비용 영향:** 중립.
- **출처:** https://docs.djangoproject.com/en/5.2/ref/settings/ (SECRET_KEY, SECRET_KEY_FALLBACKS). 다른 프레임워크의 키 배열 지원은 일반 원칙(출처 미확인). ⚠️근거없음

### U-073 API 스키마의 하위 호환 깨짐을 CI에서 잡는다
- **무엇/왜:** OpenAPI/GraphQL 스키마 diff로 필수 필드 추가, 필드 제거, 타입 변경을 자동 탐지하면 U-061·U-062를 사람 리뷰에 의존하지 않는다.
- **실패 양상:** 리뷰에서 놓친 필드 제거가 배포 후 구 클라이언트를 깨뜨림.
- **신호:** 🟢 `openapi.yaml`/`openapi.json`, FastAPI 자동 스키마, `schema.graphql`. 🟢 CI에 스키마 diff 단계 유무.
- **시나리오·수준:** U L2 이상 + 외부 소비자.
- **처방:** CI에서 main 브랜치 스키마와 PR 스키마를 비교해 breaking change면 실패(도구는 oasdiff, GraphQL Inspector 등, 출처 미확인). ⚠️근거없음
- **검증:** 필드 제거 PR이 실패하는지.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

---

## G. 백그라운드 작업: 워커, 크론, Job

### U-074 워커가 SIGTERM에 진행 중 작업을 마치거나 큐에 돌려준다
- **무엇/왜:** 12-Factor는 워커가 종료 시 현재 작업을 큐에 돌려주라고 한다(RabbitMQ NACK 등). Celery는 TERM에 warm shutdown으로 실행 중 작업을 마치고 종료한다. QUIT(cold)는 즉시 중단하며 `acks_late`가 없으면 작업을 잃을 수 있다.
- **실패 양상:** 배포마다 처리 중이던 작업이 사라지거나(조기 ack), 반쯤 처리된 채 다른 워커가 다시 처리(중복, C 담당과 연결).
- **신호:** 🟢 워커 엔트리포인트의 신호 처리(simple-web-app `board/worker.py` SIGTERM → stop 이벤트, 충족 예). 🟢 Celery `acks_late`, `task_reject_on_worker_lost`. 🟢 BullMQ `worker.close()` 호출 유무.
- **시나리오·수준:** U L1 이상 + 워커.
- **처방:** 새 작업 가져오기 중단 → 현재 작업 완료 또는 반환 → 연결 종료. 처리 후 ack.
- **검증:** 작업 처리 중 워커 Pod 삭제 → 작업이 정확히 한 번 완료되는지(C의 멱등성과 함께).
- **비용 영향:** 중립.
- **출처:** https://12factor.net/disposability · https://docs.celeryq.dev/en/stable/userguide/workers.html ⚠️출처부적격 ⚠️출처확인필요

### U-075 워커 유예 시간과 최장 작업 길이
- **무엇/왜:** 작업이 유예 시간보다 길면 warm shutdown도 SIGKILL로 끝난다. Celery 5.5의 soft shutdown은 시간 제한 후 cold shutdown으로 넘어간다. Spot 중단 통보(설계 S22: Fargate Spot 2분, GKE Spot 30초)도 같은 제약이다.
- **실패 양상:** 10분짜리 리포트 작업이 배포 때마다 처음부터 재시작 → 배포를 자주 하면 영원히 안 끝남.
- **신호:** 🟢 워커 Deployment `terminationGracePeriodSeconds`(simple-web-app worker 30초) vs 작업 타임아웃 설정(`time_limit`, `lockDuration`). 🟡 대용량 처리 작업 이름(`export`, `report`, `transcode`).
- **시나리오·수준:** U L2 이상 + 긴 작업.
- **처방:** 작업을 짧은 단위로 쪼개 체크포인트, 또는 워커 grace를 최장 작업 + 여유로(ECS는 최대 120초라 긴 작업은 분할 필수).
- **검증:** 최장 작업 실행 중 롤아웃 → 완료·재개 여부.
- **비용 영향:** 중립.
- **출처:** https://docs.celeryq.dev/en/stable/userguide/workers.html · https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definition_parameters.html ⚠️출처확인필요

### U-076 배포 중 크론 중복 실행 (서지 Pod, 동시 실행 정책)
- **무엇/왜:** 앱 프로세스 안의 스케줄러(`node-cron`, APScheduler)는 replica 1이어도 롤링 서지 구간에 구·신 Pod가 동시에 같은 시각에 실행한다. k8s CronJob은 `concurrencyPolicy` 기본 `Allow`이고, 문서는 CronJob이 Job을 두 번 만들거나 안 만들 수 있으니 작업을 멱등하게 하라고 한다.
- **실패 양상:** 배포가 정각과 겹치면 정산·알림 메일 이중 발송. 이전 실행이 끝나지 않았는데 다음 실행이 겹쳐 같은 데이터를 동시에 처리.
- **신호:** 🟢 `node-cron`, `cron` 패키지, `APScheduler`, `setInterval` 기반 스케줄러가 웹 프로세스에 있음(사실 `cron.no_lock`, T-PRE-002와 공유). 🟢 CronJob에 `concurrencyPolicy` 미지정. 🟢 `startingDeadlineSeconds` 미지정.
- **시나리오·수준:** U L1 이상 + 예약 작업.
- **처방:** 스케줄러를 웹에서 분리(CronJob/Cloud Scheduler/EventBridge), `concurrencyPolicy: Forbid`, 작업 내 분산 락 + 멱등 처리.
- **검증:** 실행 시각에 맞춰 롤아웃 → 실행 횟수 1회 확인.
- **비용 영향:** 중립.
- **출처:** https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/

### U-077 플랫폼 크론(Vercel)의 중복·누락과 배포·롤백 영향
- **무엇/왜:** Vercel 크론은 최선 노력 전달이라 가끔 실행되지 않거나 같은 회차가 두 번 호출될 수 있고, 실패해도 재시도하지 않는다. 실행이 간격보다 길면 두 번째 인스턴스가 겹친다. 새 배포는 실행 중 크론을 끊지 않으며, Instant Rollback 시 크론 정의도 되돌아간다. Hobby는 하루 1회, 지정 시간 안 아무 때나.
- **실패 양상:** 크론 정의를 바꾼 배포를 롤백했더니 이전 스케줄로 돌아가 신규 작업이 안 돔. 중복 호출로 포인트 이중 지급.
- **신호:** 🟢 `vercel.json` `crons`. 🟢 크론 라우트에 `CRON_SECRET` 검사 유무, 락·멱등 처리 유무.
- **시나리오·수준:** U L1 이상, 티어0.
- **처방:** 티어0: 락 + 멱등 재조정(마지막 성공 이후 미처리분 처리), `CRON_SECRET` 검증.
- **검증:** 크론 라우트를 연속 2회 호출해 결과가 같은지.
- **비용 영향:** 중립.
- **출처:** https://vercel.com/docs/cron-jobs/manage-cron-jobs

### U-078 일회성 Job(마이그레이션 등)의 재실행·정리 설정
- **무엇/왜:** k8s Job의 Pod 템플릿은 생성 후 바꿀 수 없어서, 같은 이름의 Job을 다시 적용하려면 지워야 한다. `backoffLimit` 기본 6, `ttlSecondsAfterFinished`로 정리, `podFailurePolicy`로 재시도할 실패와 아닌 실패를 나눈다.
- **실패 양상:** 두 번째 배포에서 `kubectl apply`가 "field is immutable"로 실패. 또는 실패한 마이그레이션이 기본 6회(설정에 따라 더) 재시도되며 매번 부분 적용 시도.
- **신호:** 🟢 고정 이름 Job + 배포 스크립트에 사전 삭제 없음(simple-web-app은 `delete job --ignore-not-found` 후 적용, 충족 예). 🟢 `backoffLimit`(simple-web-app 10), `ttlSecondsAfterFinished` 유무.
- **시나리오·수준:** U L2 이상, 티어2.
- **처방:** Job 이름에 SHA 접미사 또는 사전 삭제, Argo CD 훅 `BeforeHookCreation`, 마이그레이션은 재시도해도 안전하게(멱등 DDL) 또는 `backoffLimit` 작게.
- **검증:** 같은 매니페스트를 두 번 연속 배포.
- **비용 영향:** 중립.
- **출처:** https://kubernetes.io/docs/concepts/workloads/controllers/job/ · https://argo-cd.readthedocs.io/en/stable/user-guide/sync-waves/ ⚠️출처확인필요

### U-079 장시간 배치·Job이 배포를 가로지를 때
- **무엇/왜:** 배치는 시작한 시점의 이미지로 끝까지 돈다. 그 사이 contract 마이그레이션이 나가면 구 코드 배치가 사라진 컬럼을 만난다. 노드 drain에도 중단된다.
- **실패 양상:** 새벽 배치가 2시간째 도는 중 배포된 컬럼 삭제로 배치 실패, 재시작 시 처음부터.
- **신호:** 🟢 CronJob/Job + 긴 `activeDeadlineSeconds`. 🟡 배치 이름(`nightly`, `export`, `sync`).
- **시나리오·수준:** U L2 이상.
- **처방:** contract 단계 전 진행 중 배치 완료 확인(배포 전 점검), 배치는 체크포인트·재개 가능하게.
- **검증:** 배치 실행 중 contract 마이그레이션 배포 리허설.
- **비용 영향:** 중립.
- **출처:** https://martinfowler.com/bliki/ParallelChange.html (모든 사용처를 옮긴 뒤 contract) · 나머지는 일반 원칙(출처 미확인) ⚠️출처부적격 ⚠️근거없음

### U-080 웹·워커·Job이 이미지를 공유할 때의 배포 단위
- **무엇/왜:** 한 이미지를 웹, 워커, 마이그레이션 Job이 함께 쓰면 하나의 커밋이 세 워크로드를 동시에 바꾼다. 배포 순서(Job → 워커 → 웹 등)와 호환 범위를 명시해야 한다.
- **실패 양상:** 웹이 새 작업 형식을 넣기 시작했는데 워커 롤아웃은 아직 → U-064 실패. 한쪽만 롤백하면 버전이 어긋남.
- **신호:** 🟢 여러 Deployment가 같은 `image:`를 쓰고 `command`만 다름(simple-web-app board-api/board-worker/db-migrate). 🟢 배포 스크립트의 롤아웃 순서.
- **시나리오·수준:** U L2 이상.
- **처방:** 순서를 파이프라인에 고정(마이그레이션 → 소비자 → 생산자), 롤백도 세트로.
- **검증:** 순서를 뒤집은 배포에서 오류가 나는지(호환성 테스트로 활용).
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

---

## H. 빌드, 아티팩트, 공급망

### U-081 이미지 태그는 불변 (`latest` 금지)
- **무엇/왜:** k8s 문서는 운영에서 `:latest`를 피하라고 한다. 어떤 버전이 도는지 추적하기 어렵고 롤백이 어렵다. 태그를 생략하거나 `latest`면 `imagePullPolicy` 기본이 Always가 되고, 그 외는 IfNotPresent라서 같은 태그를 덮어쓰면 노드마다 다른 이미지가 돈다.
- **실패 양상:** 같은 `:latest`인데 새 노드에 뜬 Pod만 신버전 → 재현 불가 버그. 롤백할 이전 버전을 특정할 수 없음.
- **신호:** 🟢 `image: ...:latest` 또는 태그 없음, compose `image: app:latest`, ECS 태스크 정의 `:latest`. 🟢 CI가 같은 태그(`dev`, `staging`)를 덮어씀(simple-web-app dev overlay `dev` 자리표시자 → 파이프라인이 SHA로 교체하는지 확인 필요).
- **시나리오·수준:** U L1 이상.
- **처방:** 커밋 SHA 태그(`kustomize edit set image ...:$SHA`), 레지스트리 태그 불변(U-083).
- **검증:** 렌더된 매니페스트에 `:latest`·태그 없음 0건(정적 검사).
- **비용 영향:** 약간 증가(이미지 저장, 수명 주기 정책으로 관리).
- **출처:** https://kubernetes.io/docs/concepts/containers/images/

### U-082 다이제스트 고정과 버전 일관성
- **무엇/왜:** 태그는 변할 수 있지만 다이제스트는 특정 이미지를 유일하게 가리킨다. ECS는 기본으로 태그를 다이제스트로 해석해 서비스의 모든 태스크가 같은 이미지를 쓰게 한다(`versionConsistency`).
- **실패 양상:** 배포 도중 누군가 같은 태그를 다시 푸시 → 한 배포 안에서 Pod마다 다른 코드.
- **신호:** 🟢 `image@sha256:`, kustomize `images[].digest`. 🟢 ECS `versionConsistency: disabled`.
- **시나리오·수준:** U L2 이상.
- **처방:** 티어2: 파이프라인이 빌드 결과 다이제스트를 매니페스트에 기록. 티어1: ECS 기본 유지, Cloud Run은 배포 시 다이제스트로 해석(출처 미확인). ⚠️근거없음
- **검증:** 실행 중 Pod의 imageID가 모두 같은지.
- **비용 영향:** 중립.
- **출처:** https://kubernetes.io/docs/concepts/containers/images/ · https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-type-ecs.html (Container image resolution)

### U-083 레지스트리에서 태그 덮어쓰기 금지
- **무엇/왜:** ECR은 저장소 단위로 태그 불변을 켤 수 있고, 켜면 기존 태그로 푸시할 때 `ImageTagAlreadyExistsException`을 낸다. 예외 필터로 일부 태그만 가변으로 둘 수 있다.
- **실패 양상:** 실수로 운영 태그를 다른 빌드로 덮어써 롤백 대상이 오염.
- **신호:** 🟢 Terraform `aws_ecr_repository.image_tag_mutability = "IMMUTABLE"` 유무. 🟢 Artifact Registry 불변 태그 설정(출처 미확인). ⚠️근거없음
- **시나리오·수준:** U L2 이상.
- **처방:** 티어1·2: 저장소 불변 태그 + 수명 주기 정책.
- **검증:** 같은 태그 재푸시가 거부되는지.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-tag-mutability.html

### U-084 한 번 빌드해서 환경을 따라 승격한다 (빌드 시 인라인 설정 주의)
- **무엇/왜:** 빌드·릴리스·실행을 나누고 릴리스는 고유 ID를 가진 불변 단위여야 한다. 그런데 Next.js `NEXT_PUBLIC_*`, Vite `VITE_*`는 빌드 시 번들에 박힌다. 그래서 환경마다 다시 빌드하게 되고, 스테이징에서 검증한 산출물과 운영 산출물이 달라진다.
- **실패 양상:** 스테이징 빌드는 통과했는데 운영 재빌드에서 의존성이 바뀌어 실패. 또는 운영 이미지에 스테이징 API 주소가 박힘.
- **신호:** 🟢 CI가 환경별로 `next build`/`docker build`를 따로 실행. 🟢 `NEXT_PUBLIC_API_URL` 등 환경별로 다른 공개 변수. 🟢 Dockerfile `ARG`로 환경 값 주입.
- **시나리오·수준:** U L2 이상.
- **처방:** 서버 측 런타임 env로 읽기(Next.js는 동적 렌더링에서 런타임 env 사용 가능), 공개 설정은 런타임 `/config.json`. 부득이하면 SHA별 산출물 보관.
- **검증:** 스테이징과 운영의 이미지 다이제스트가 같은지.
- **비용 영향:** 감소(빌드 시간).
- **출처:** https://12factor.net/build-release-run · https://nextjs.org/docs/app/guides/self-hosting (Environment Variables: NEXT_PUBLIC_은 빌드 시 인라인, 런타임 env로 단일 이미지 승격 가능) ⚠️출처부적격

### U-085 lock 파일과 고정된 설치 (재현 가능한 빌드)
- **무엇/왜:** 의존성을 완전하고 정확하게 선언해야 한다. `npm ci`는 lock 파일이 필수이고 package.json과 어긋나면 갱신하지 않고 실패한다. pip 해시 검사 모드는 모든 의존성을 `==`로 고정하고 해시를 요구한다.
- **실패 양상:** 같은 커밋인데 오늘 빌드는 마이너 업데이트된 의존성을 받아 깨짐. 롤백 빌드가 원래와 다른 코드를 만듦.
- **신호:** 🟢 lock 파일(`package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `uv.lock`, `poetry.lock`, `requirements.lock`) 없음 또는 `.gitignore`에 있음. 🟢 Dockerfile·CI가 `npm install`(ci 아님), `pip install -r requirements.txt`(버전 범위). 🟢 simple-web-app: `requirements.lock` + `npm ci`(충족 예).
- **시나리오·수준:** U L1 이상.
- **처방:** lock 커밋, CI·Dockerfile에서 `npm ci`/`pnpm install --frozen-lockfile`/`uv sync --frozen`, pip는 `--require-hashes` 고려.
- **검증:** 같은 커밋 두 번 빌드한 결과 의존성 트리 동일.
- **비용 영향:** 중립.
- **출처:** https://12factor.net/dependencies · https://docs.npmjs.com/cli/v11/commands/npm-ci · https://pip.pypa.io/en/stable/topics/secure-installs/ ⚠️출처부적격 ⚠️출처확인필요

### U-086 베이스 이미지 고정과 정기 갱신
- **무엇/왜:** 이미지 태그는 발행자가 다른 이미지로 옮길 수 있다. 일관성을 원하면 다이제스트로 고정하고, 대신 Dependabot 등으로 갱신 PR을 받아 보안 패치를 놓치지 않는다.
- **실패 양상:** `FROM node:22-alpine`이 어느 날 바뀌어 네이티브 모듈 빌드 실패. 반대로 고정만 하고 갱신하지 않아 취약한 베이스로 수년.
- **신호:** 🟢 `FROM image:tag`에 `@sha256` 없음(simple-web-app `python:3.12-slim`, `node:22-alpine`, `nginx-unprivileged:1.27-alpine` 모두 태그만). 🟢 `.github/dependabot.yml`에 `package-ecosystem: docker` 유무.
- **시나리오·수준:** U L2 이상(공급망 무결성).
- **처방:** 다이제스트 고정 + Dependabot/Renovate 자동 PR, `--pull`로 주기적 재빌드.
- **검증:** 정적 검사: 모든 FROM에 다이제스트.
- **비용 영향:** 중립.
- **출처:** https://docs.docker.com/build/building/best-practices/

### U-087 이미지 크기, 멀티 스테이지, `.dockerignore`
- **무엇/왜:** 멀티 스테이지는 빌드 도구를 최종 이미지에서 빼고, `.dockerignore`는 빌드 컨텍스트에서 불필요한 파일을 뺀다. 이미지가 크면 풀 시간이 늘어 롤아웃·스케일아웃·롤백이 모두 느려진다.
- **실패 양상:** 2GB 이미지라 새 노드에서 풀에 1분 이상 → 배포 중 서지 Pod가 늦게 Ready, 피크 중 확장 지연.
- **신호:** 🟢 단일 스테이지 Dockerfile에 `npm install`(devDependencies 포함)·컴파일러. 🟢 `.dockerignore` 없음 + `COPY . .`. 🟢 Next.js `output: 'standalone'` 미사용.
- **시나리오·수준:** U L2 이상.
- **처방:** 멀티 스테이지, 런타임 의존성만, `.dockerignore`(node_modules, .git, .env*).
- **검증:** 이미지 크기와 콜드 노드 풀 시간 측정.
- **비용 영향:** 감소(저장·전송).
- **출처:** https://docs.docker.com/build/building/best-practices/

### U-088 이미지 안에 비밀이 들어간다
- **무엇/왜:** `.dockerignore` 없이 `COPY . .`를 하면 로컬 `.env`가 이미지 레이어에 들어간다. `ARG`/`ENV`로 넘긴 토큰도 이미지 메타데이터·히스토리에 남는다. 이미지를 받을 수 있는 사람은 모두 비밀을 읽는다.
- **실패 양상:** 공개 레지스트리나 넓은 권한의 레지스트리에서 운영 DB 비밀번호 유출.
- **신호:** 🟢 `.env` 파일 존재 + `.dockerignore`에 `.env` 없음 + `COPY . .`. 🟢 Dockerfile `ARG .*(TOKEN|SECRET|KEY|PASSWORD)`, `ENV ...SECRET=`. 🟢 `npm config set //registry...:_authToken` in RUN.
- **시나리오·수준:** 모든 수준.
- **처방:** `.dockerignore`, BuildKit secret mount(`RUN --mount=type=secret`, 출처 미확인), 런타임 주입. ⚠️근거없음
- **검증:** `docker history`와 이미지 파일시스템에서 비밀 패턴 스캔.
- **비용 영향:** 중립.
- **출처:** https://docs.docker.com/build/building/best-practices/ (.dockerignore) · 비밀 레이어 잔존은 일반 원칙(출처 미확인) ⚠️근거없음

### U-089 멀티 아키텍처 이미지
- **무엇/왜:** 컨테이너는 호스트 커널을 공유하므로 아키텍처가 다르면 에뮬레이션 없이 실행되지 않는다. Apple Silicon 노트북에서 빌드한 arm64 이미지를 amd64 노드에 올리면 기동 실패한다. `docker buildx build --platform linux/amd64,linux/arm64`로 매니페스트 리스트를 만든다.
- **실패 양상:** 로컬 빌드·푸시 후 배포 → 모든 Pod `exec format error` CrashLoop. Graviton(ARM) 노드로 옮기려다 같은 문제.
- **신호:** 🟢 배포 문서에 로컬 `docker build && docker push`(simple-web-app `docs/deploy.md` 클라우드 절차 1단계). 🟢 CI에 `--platform`/`docker/setup-qemu-action` 없음. 🟡 네이티브 모듈(sharp, bcrypt, argon2).
- **시나리오·수준:** U L1 이상(이미지 직접 빌드 시).
- **처방:** CI에서만 빌드·푸시, 대상 노드 아키텍처 명시, ARM 전환(COST-005) 시 멀티 플랫폼.
- **검증:** `docker manifest inspect`로 플랫폼 목록 확인.
- **비용 영향:** 감소 가능(ARM 노드).
- **출처:** https://docs.docker.com/build/building/multi-platform/

### U-090 CI 파이프라인 자체의 무결성 (액션 SHA 고정, 최소 권한, OIDC)
- **무엇/왜:** GitHub는 액션을 전체 커밋 SHA로 고정하는 것만이 불변 릴리스로 쓰는 유일한 방법이라고 한다. `GITHUB_TOKEN`은 기본 읽기 전용으로 두고, 클라우드 인증은 장기 비밀 대신 OIDC로. `pull_request_target`·`workflow_run`에서 신뢰하지 않는 코드를 체크아웃하지 않는다.
- **실패 양상:** 사용하던 액션의 태그가 악성 커밋으로 옮겨져 배포 자격 증명 탈취. 장기 AWS 키가 저장소 비밀에 있어 유출 시 피해 범위가 큼.
- **신호:** 🟢 `uses: org/action@v4`(태그, simple-web-app CI가 이 형태). 🟢 `permissions:` 미설정(simple-web-app은 `contents: read`, 충족). 🟢 `AWS_ACCESS_KEY_ID` 비밀 사용 vs `aws-actions/configure-aws-credentials` + `id-token: write`. 🟢 `pull_request_target`.
- **시나리오·수준:** U L1 이상(배포 파이프라인이 있으면).
- **처방:** SHA 고정 + Dependabot으로 갱신, 잡별 최소 권한, OIDC 페더레이션.
- **검증:** 정적 검사(워크플로 YAML).
- **비용 영향:** 중립.
- **출처:** https://docs.github.com/en/actions/reference/security/secure-use

### U-091 빌드 출처 증명과 이미지 서명, 배포 시 검증
- **무엇/왜:** SLSA Build L1은 빌드 방법을 보여주는 출처 증명(provenance), L2는 호스팅 빌드 플랫폼이 서명한 증명, L3는 빌드 간 격리와 서명 키 보호를 요구한다. Cosign은 이미지를 (가능하면 다이제스트 기준으로) 서명하며 OIDC 기반 키리스 서명을 지원한다.
- **실패 양상:** 누군가 레지스트리에 직접 푸시한 이미지가 CI 산출물인 척 배포됨.
- **신호:** 🟢 CI에 `cosign sign`, `actions/attest-build-provenance`, `docker buildx --provenance`. 🟢 클러스터 정책(Kyverno/Gatekeeper/Binary Authorization)으로 서명 검증. 🔴 없음.
- **시나리오·수준:** U L3 또는 규제·B2B(D L2 이상과 함께).
- **처방:** 티어1: Cloud Run Binary Authorization(출처 미확인). 티어2: 서명 검증 어드미션 정책. 바이브코더 앱(U L1)에는 과잉이므로 요구하지 않는다. ⚠️근거없음
- **검증:** 서명 없는 이미지 배포가 거부되는지.
- **비용 영향:** 중립~약간 증가.
- **출처:** https://slsa.dev/spec/v1.0/levels · https://docs.sigstore.dev/cosign/signing/signing_with_containers/ ⚠️출처확인필요

### U-092 테스트·검증 통과가 배포의 전제
- **무엇/왜:** 배포 잡이 테스트 잡에 의존(`needs`)하지 않으면 실패한 커밋도 배포된다. 플랫폼 Git 연동(Vercel 등)은 CI 결과와 무관하게 빌드·배포한다.
- **실패 양상:** 테스트가 빨간데 main 푸시로 Vercel이 프로덕션 배포.
- **신호:** 🟢 배포 워크플로에 `needs: [test]` 없음. 🟢 Vercel Git 연동 + 브랜치 보호 규칙의 필수 체크 없음(🔴 GitHub 설정은 코드에 없음). 🟢 simple-web-app `images` 잡이 `needs: [backend, frontend, k8s]`(충족 예).
- **시나리오·수준:** U L1 이상.
- **처방:** 브랜치 보호 + 필수 체크, 배포 잡 `needs`, Vercel은 Git 연동 대신 CI에서 `vercel deploy`(단 `--prebuilt`는 Skew Protection 불가, U-070) 또는 배포 보호 규칙.
- **검증:** 실패 테스트 커밋이 배포되지 않는지.
- **비용 영향:** 중립.
- **출처:** https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments (배포 브랜치 제한) · `needs` 원칙은 일반 원칙(출처 미확인) ⚠️근거없음

### U-093 런타임 버전 고정 (Node, Python)
- **무엇/왜:** 플랫폼 기본 런타임 버전이 바뀌거나 로컬·CI·운영 버전이 다르면 같은 코드가 다르게 동작한다.
- **실패 양상:** 플랫폼 기본 Node 메이저가 올라간 날 재배포에서 네이티브 모듈 빌드 실패.
- **신호:** 🟢 `package.json` `engines.node`, `.nvmrc`, `.python-version`, `pyproject` `requires-python`, Dockerfile 베이스 태그의 메이저 버전. 🟢 CI `node-version`과 Dockerfile 버전 불일치.
- **시나리오·수준:** U L1 이상.
- **처방:** 한 곳에서 버전을 정하고 CI·Dockerfile·플랫폼 설정이 따른다.
- **검증:** 정적 비교.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

---

## I. 설정과 비밀

### U-094 설정 외부화 (12-Factor III)
- **무엇/왜:** 배포마다 달라지는 모든 것(DB 주소, 외부 API 키, 도메인)은 코드에서 분리해 환경 변수로. 판별 기준: 지금 당장 오픈소스로 공개해도 자격 증명이 새지 않는가.
- **실패 양상:** 코드에 `localhost:5432`, 운영 도메인이 박혀 있어 환경마다 코드를 고쳐 배포 → 스테이징 검증이 무의미.
- **신호:** 🟢 사실 `config.localhost_hardcoded`, `secret.hardcoded`. 🟢 `if (process.env.NODE_ENV === 'production') { url = 'https://...' }` 같은 환경 이름 분기(그룹화된 설정, 12-Factor가 경고하는 방식).
- **시나리오·수준:** U L1 이상.
- **처방:** env로 이동, 환경 이름 분기 대신 개별 변수.
- **검증:** 같은 이미지를 env만 바꿔 두 환경에 띄움.
- **비용 영향:** 중립.
- **출처:** https://12factor.net/config ⚠️출처부적격

### U-095 저장소에 커밋된 `.env`·하드코딩 비밀
- **무엇/왜:** 커밋된 비밀은 Git 이력에 영원히 남는다. GitHub 푸시 보호는 푸시 단계에서 비밀을 막지만 이미 들어간 비밀은 교체해야 한다.
- **실패 양상:** 공개 저장소의 Supabase `service_role` 키·Stripe 비밀 키 유출 → 데이터 탈취·결제 악용. 비공개라도 협업자·CI 로그 경유 유출.
- **신호:** 🟢 `.env`, `.env.production`, `.env.local`이 Git 추적 중. 🟢 `sk_live_`, `service_role`, `AKIA`, `-----BEGIN PRIVATE KEY-----` 패턴. 🟢 `.gitignore`에 `.env` 없음.
- **시나리오·수준:** 모든 수준(L0 포함).
- **처방:** 즉시 교체(회전) → 이력 정리 → 비밀 저장소로(U-099) → 푸시 보호 활성.
- **검증:** gitleaks류 스캔 0건(도구 출처 미확인), 교체 후 이전 키로 요청 시 거부. ⚠️근거없음
- **비용 영향:** 중립.
- **출처:** https://12factor.net/config · https://docs.github.com/en/code-security/secret-scanning/introduction/about-push-protection ⚠️출처부적격

### U-096 클라이언트 번들에 들어가는 "공개" 변수에 비밀을 넣는다
- **무엇/왜:** `NEXT_PUBLIC_*`는 빌드 시 자바스크립트 번들에 인라인되어 브라우저로 간다. `VITE_*`도 같은 방식이다(Vite 문서 미확인). 이름만 env일 뿐 공개 값이다.
- **실패 양상:** `NEXT_PUBLIC_OPENAI_API_KEY`, `VITE_SUPABASE_SERVICE_ROLE_KEY`가 누구나 볼 수 있는 번들에 노출 → 과금 폭탄, RLS 우회.
- **신호:** 🟢 `NEXT_PUBLIC_.*(SECRET|SERVICE_ROLE|PRIVATE|_KEY)` 중 공개 키가 아닌 것, `VITE_.*SECRET`, `REACT_APP_.*SECRET`. 🟢 클라이언트 컴포넌트에서 서버 전용 키 사용.
- **시나리오·수준:** 모든 수준.
- **처방:** 서버 라우트/서버 액션으로 이동, 키 교체.
- **검증:** 빌드 산출물(`.next/static`, `dist/`)에서 비밀 패턴 스캔.
- **비용 영향:** 감소(악용 비용 방지).
- **출처:** https://nextjs.org/docs/app/guides/self-hosting (Environment Variables: NEXT_PUBLIC_은 빌드 시 번들에 인라인)

### U-097 설정·비밀 변경이 언제 반영되는가 (재배포·재시작 필요)
- **무엇/왜:** env로 주입한 ConfigMap 값은 자동 갱신되지 않아 Pod 재시작이 필요하다. Vercel 환경 변수 변경은 이전 배포에 적용되지 않고 새 배포에만 적용된다. Cloud Run의 env 비밀은 인스턴스 시작 시 한 번 해석된다.
- **실패 양상:** 키를 교체했다고 생각했는데 실행 중 인스턴스는 옛 키 → 옛 키 폐기 순간 장애. 일부 인스턴스만 재시작되어 값이 섞임.
- **신호:** 🟢 `envFrom: configMapRef`/`secretKeyRef` + 설정 변경 시 롤아웃 트리거 없음(U-098). 🟢 `vercel.json` + 설정 변경 런북에 재배포 없음.
- **시나리오·수준:** U L1 이상.
- **처방:** 설정 변경 = 배포로 취급: k8s는 해시 접미사(U-098) 또는 `rollout restart`, Vercel은 변경 후 재배포, Cloud Run은 새 리비전.
- **검증:** 설정 변경 후 모든 인스턴스가 새 값을 쓰는지(/version에 설정 해시 노출 등).
- **비용 영향:** 중립.
- **출처:** https://kubernetes.io/docs/concepts/configuration/configmap/ · https://vercel.com/docs/environment-variables · https://docs.cloud.google.com/run/docs/configuring/services/secrets

### U-098 설정 변경을 롤아웃으로 연결 (kustomize 해시 접미사)
- **무엇/왜:** kustomize `configMapGenerator`는 내용 기반 해시를 이름에 붙이고 워크로드 참조도 바꿔, 설정이 바뀌면 Deployment 템플릿이 바뀌어 롤링 업데이트가 일어난다. 롤백하면 이전 ConfigMap도 함께 돌아간다.
- **실패 양상:** 평범한 `ConfigMap` 리소스를 수정하면 Pod가 재시작되지 않아 U-097, 또 잘못된 설정이 즉시 롤백되지 않음.
- **신호:** 🟢 kustomization에 `configMapGenerator`/`secretGenerator` 사용 여부, `disableNameSuffixHash: true`. 🟢 Helm 템플릿의 `checksum/config` 어노테이션 유무.
- **시나리오·수준:** U L2 이상, 티어2.
- **처방:** generator + 해시(기본값 유지), 또는 Helm 체크섬 어노테이션.
- **검증:** 설정만 바꾼 배포가 롤아웃을 일으키는지.
- **비용 영향:** 중립.
- **출처:** https://kubectl.docs.kubernetes.io/references/kustomize/kustomization/configmapgenerator/

### U-099 비밀 저장소 (k8s Secret 평문 YAML 금지)
- **무엇/왜:** k8s Secret은 기본으로 etcd에 암호화되지 않은 채 저장되고, base64는 암호화가 아니다. 문서는 저장 시 암호화, 최소 권한 RBAC, 외부 비밀 저장소 사용을 권한다.
- **실패 양상:** `kind: Secret` YAML이 Git에 커밋되어 base64 디코딩 한 번으로 유출.
- **신호:** 🟢 Git에 `kind: Secret` + `data:`/`stringData:`. 🟢 `ExternalSecret`, `SecretProviderClass`, `SealedSecret`, SOPS 파일 유무. 🟢 simple-web-app은 Secret을 Terraform이 만들고 매니페스트는 이름만 참조(충족 예, Terraform state 보호는 U-111).
- **시나리오·수준:** U L1 이상(비밀이 있으면).
- **처방:** 티어0: 플랫폼 env(암호화 저장). 티어1: Secret Manager/Secrets Manager 참조. 티어2: External Secrets Operator 또는 Secrets Store CSI.
- **검증:** 렌더된 매니페스트에 Secret 값 0건.
- **비용 영향:** 약간 증가(Secret Manager 호출·저장).
- **출처:** https://kubernetes.io/docs/concepts/configuration/secret/ · https://external-secrets.io/latest/api/externalsecret/ ⚠️출처확인필요

### U-100 무중단 비밀 교체
- **무엇/왜:** 비밀을 한 번에 바꾸면 인스턴스마다 반영 시점이 달라(U-097) 일부가 실패한다. 두 자격 증명을 겹쳐 유효하게 두고 옮긴 뒤 이전 것을 폐기한다. AWS Secrets Manager는 관리형 교체와 Lambda 교체를 제공하고, Vercel은 무중단 교체 절차를 문서로 둔다.
- **실패 양상:** DB 비밀번호 교체 직후 재시작 안 된 Pod 전부 인증 실패.
- **신호:** 🟢 Secrets Manager `rotation_rules`, 앱이 시작 시 한 번만 비밀을 읽음. 🟡 장기 미교체 비밀.
- **시나리오·수준:** U L2 이상.
- **처방:** 이중 사용자(교대) 전략 또는 앱이 주기적으로 비밀을 다시 읽음, 서명 키는 U-072 방식.
- **검증:** 부하 중 비밀 교체 리허설 → 오류 0.
- **비용 영향:** 약간 증가.
- **출처:** https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotating-secrets.html · https://vercel.com/docs/environment-variables (rotating secrets 안내 링크)

### U-101 Cloud Run 비밀을 env로 쓰면서 `latest` 버전 참조
- **무엇/왜:** env 비밀은 인스턴스 시작 시 해석되므로 Google은 `latest` 대신 특정 버전 고정을 권한다. `latest`면 새 비밀 버전을 만드는 순간부터 새로 뜨는 인스턴스만 새 값을 받아 같은 리비전 안에서 값이 섞인다. 볼륨 마운트는 읽을 때마다 최신을 가져온다.
- **실패 양상:** 오토스케일된 인스턴스만 새 키를 써서 간헐 인증 오류, 롤백해도 비밀은 그대로.
- **신호:** 🟢 Terraform `secret_key_ref { version = "latest" }` + env 방식, `gcloud run deploy --set-secrets=VAR=secret:latest`.
- **시나리오·수준:** U L1 이상, 티어1(Cloud Run).
- **처방:** 버전 고정 후 교체 시 새 리비전 배포, 또는 볼륨 마운트 + 앱이 파일 재읽기.
- **검증:** 비밀 새 버전 생성 후 인스턴스 간 값 일치 여부.
- **비용 영향:** 중립.
- **출처:** https://docs.cloud.google.com/run/docs/configuring/services/secrets

### U-102 필수 설정을 기동 시 검증 (fail fast)
- **무엇/왜:** 필수 env가 빠졌을 때 첫 요청에서 터지면 readiness를 통과한 Pod가 트래픽을 받은 뒤 실패한다. 기동 시 검증하면 롤아웃이 첫 Pod에서 멈추고 자동 롤백(U-033)이 동작한다.
- **실패 양상:** 새 env를 추가했는데 운영에 안 넣어 배포 직후 해당 기능 전부 500, 헬스체크는 정상.
- **신호:** 🟢 `zod`/`envalid`/`@t3-oss/env-nextjs`, pydantic `BaseSettings`, Django `environ` 필수 변수 사용 여부. 🟢 `process.env.X!`/`os.environ.get("X")` 산발 사용.
- **시나리오·수준:** U L1 이상.
- **처방:** 설정 스키마를 한 모듈에서 기동 시 파싱, 실패 시 프로세스 종료.
- **검증:** 필수 env 하나를 뺀 배포가 롤아웃 단계에서 실패하는지.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### U-103 코드가 읽는 env와 선언된 env의 불일치
- **무엇/왜:** `.env.example`(또는 플랫폼 설정)에 없는 변수를 코드가 읽으면 새 환경을 만들 때 빠진다. 반대로 더 이상 안 쓰는 비밀이 남아 노출면을 키운다.
- **실패 양상:** 프리뷰·스테이징·재해 복구 환경을 새로 만들 때 기능 일부가 조용히 꺼짐.
- **신호:** 🟢 탐지기 `env.required`(코드 참조) − `.env.example` 키 집합의 차이. 🟢 k8s 매니페스트 env 목록과 비교.
- **시나리오·수준:** U L1 이상.
- **처방:** CI에서 차집합 검사, U-102 스키마를 단일 진실로.
- **검증:** 차집합 0.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

---

## J. 환경 분리와 프리뷰

### U-104 dev/staging/prod 분리 (데이터·자격 증명까지)
- **무엇/왜:** 환경 분리는 코드 브랜치가 아니라 DB, 캐시, 비밀, 외부 서비스 키까지 나뉘어야 의미가 있다. Vercel은 Production·Preview·Development·사용자 정의 환경별로 변수를 따로 둔다.
- **실패 양상:** 스테이징에서 돌린 마이그레이션·테스트 메일이 운영 DB·실제 고객에게.
- **신호:** 🟢 overlay/환경 디렉터리 존재(simple-web-app `aws/{prod,dev}`, 네임스페이스·Secret 분리, 충족 예). 🟢 Terraform 워크스페이스/디렉터리 분리. 🟡 모든 환경이 같은 `DATABASE_URL` 값(비밀 값은 보통 코드에 없음 → 🔴 가정).
- **시나리오·수준:** U L2 이상(L1은 운영 하나 + 로컬 허용).
- **처방:** 티어0: Vercel 환경별 변수 + Supabase 프로젝트 분리 또는 브랜칭. 티어1·2: 계정/프로젝트 또는 네임스페이스 + 별도 DB 인스턴스.
- **검증:** 스테이징 자격 증명으로 운영 DB 접속 불가.
- **비용 영향:** 증가(스테이징 상시 비용). L1이면 스테이징 없이 프리뷰로 대체 고려.
- **출처:** https://vercel.com/docs/environment-variables · https://12factor.net/config ⚠️출처부적격

### U-105 프리뷰 배포가 운영 DB·운영 비밀을 쓴다 (빌드 단계 마이그레이션 포함)
- **무엇/왜:** Vercel Preview 변수를 따로 설정하지 않으면 프리뷰가 운영 값을 쓰도록 구성되기 쉽다. 여기에 `"build": "prisma migrate deploy && next build"`가 겹치면 **모든 PR 프리뷰 빌드가 운영 DB에 마이그레이션을 적용**한다.
- **실패 양상:** 아직 리뷰도 안 된 PR의 파괴적 마이그레이션이 운영 DB에 적용 → 운영 장애. 프리뷰에서의 테스트 결제·삭제가 운영 데이터에.
- **신호:** 🟢 `package.json` `build`/`vercel-build`/`postinstall`에 `migrate deploy`/`db push`/`supabase db push`. 🟢 `vercel.json` + 마이그레이션 디렉터리. 🔴 Preview 환경 변수 값(대시보드) → "프리뷰가 운영 DB를 공유한다"고 가정하고 위험 표시.
- **시나리오·수준:** 모든 수준(데이터가 있으면). 바이브코더 앱에서 가장 흔한 고위험 패턴.
- **처방:** 티어0: 마이그레이션을 빌드에서 빼고 main 머지 후 CI 단계로, Preview에는 별도 DB(Supabase 브랜치, U-106).
- **검증:** 프리뷰 빌드 로그에 마이그레이션 실행 0, 프리뷰 env의 DB 호스트 ≠ 운영.
- **비용 영향:** 증가(프리뷰 DB).
- **출처:** https://vercel.com/docs/environment-variables (Preview 환경 변수는 비프로덕션 브랜치 배포에 적용) · https://www.prisma.io/docs/orm/prisma-client/deployment/deploy-database-changes-with-prisma-migrate (migrate deploy는 CI/CD 파이프라인에서). 두 사실의 결합은 우리 추론이다. ⚠️출처확인필요 ⚠️근거없음

### U-106 프리뷰용 DB 브랜치
- **무엇/왜:** Supabase Branching은 PR마다 별도 인스턴스와 자격 증명을 만들고 마이그레이션을 적용하며, 기본으로 운영 데이터를 복사하지 않는다. PR이 머지·종료되면 삭제된다.
- **실패 양상:** 없으면 U-105, 또는 모든 PR이 공유 스테이징 DB에서 서로의 마이그레이션과 충돌.
- **신호:** 🟢 `supabase/config.toml` + `seed.sql`, Neon 브랜치 연동, CI에서 PR별 DB 생성. 🔴 없음.
- **시나리오·수준:** U L2 이상 + 마이그레이션 있음 + 프리뷰 사용.
- **처방:** 티어0: Supabase Branching(또는 Neon 브랜치, 출처 미확인). 티어1·2: PR별 일회성 DB(컨테이너) 또는 공유 스테이징 + 직렬화. ⚠️근거없음
- **검증:** PR 프리뷰의 DB가 PR 종료 후 사라지는지.
- **비용 영향:** 증가(브랜치 사용량).
- **출처:** https://supabase.com/docs/guides/deployment/branching

### U-107 프리뷰 배포의 접근 보호와 수명
- **무엇/왜:** 프리뷰 URL은 미완성 기능, 디버그 설정, 때로는 운영 데이터를 노출한다. Vercel Deployment Protection의 Standard Protection은 프로덕션 도메인을 제외한 모든 배포를 보호한다. Firebase Hosting 프리뷰 채널은 기본 7일 후 만료되며 최대 30일까지 늘릴 수 있다.
- **실패 양상:** 검색 엔진·외부인이 프리뷰 URL로 관리자 기능에 접근, 오래된 프리뷰가 옛 취약 코드로 계속 살아 있음.
- **신호:** 🟢 `firebase.json` + `hosting:channel:deploy --expires`. 🔴 Vercel 보호 설정은 대시보드 → 가정.
- **시나리오·수준:** U L1 이상 + 프리뷰 사용.
- **처방:** 티어0: Standard Protection(Vercel Authentication), 프리뷰 채널 만료. 티어1·2: 프리뷰 환경 인증 프록시 + TTL 자동 삭제.
- **검증:** 비로그인 상태로 프리뷰 URL 접근 시 차단.
- **비용 영향:** 중립(Vercel Password Protection은 Pro에서 프로젝트당 월 $20).
- **출처:** https://vercel.com/docs/deployment-protection · https://firebase.google.com/docs/hosting/manage-hosting-resources

### U-108 개발·운영 백엔드 서비스 동일성 (dev/prod parity)
- **무엇/왜:** 로컬은 SQLite, 운영은 PostgreSQL처럼 백엔드 서비스가 다르면 어댑터가 있어도 작은 비호환이 쌓여 운영에서만 실패한다. 12-Factor는 이 유혹을 거부하라고 한다.
- **실패 양상:** 로컬에선 되던 마이그레이션(SQLite는 대부분의 ALTER가 제한적)·대소문자 비교·JSON 연산이 운영 Postgres에서 실패.
- **신호:** 🟢 Prisma `provider = "sqlite"` + 운영 Postgres 설정, 테스트에 SQLite 인메모리 + 운영 Postgres. 🟢 docker-compose 없음. 🟢 simple-web-app은 testcontainers로 실제 Postgres/Redis(충족 예).
- **시나리오·수준:** U L1 이상.
- **처방:** docker-compose/testcontainers로 같은 엔진·같은 메이저 버전.
- **검증:** CI가 운영과 같은 DB 엔진으로 마이그레이션·테스트.
- **비용 영향:** 중립.
- **출처:** https://12factor.net/dev-prod-parity ⚠️출처부적격

---

## K. IaC, GitOps, 변경 통제

### U-109 인프라가 코드로 정의되어 있는가
- **무엇/왜:** 콘솔에서 클릭으로 만든 인프라는 재현·리뷰·롤백이 불가능하다. 설계 문서 §4.4처럼 IaC가 없으면 인프라 통제는 "미확인/미충족"이 되고 처방은 "새로 구성"이 된다.
- **실패 양상:** 장애 후 같은 환경을 다시 만들 수 없음, 누가 언제 보안 그룹을 바꿨는지 모름.
- **신호:** 🟢 `*.tf`, `Pulumi.yaml`, `cdk.json`, `template.yaml`, `serverless.yml`, k8s 매니페스트. 🟢 simple-web-app은 k8s 매니페스트는 있고 Terraform은 인프라 프로젝트 몫(DB·Secret 미정의).
- **시나리오·수준:** U L2 이상(티어1·2). 티어0은 `vercel.json`/`firebase.json`이 그 역할.
- **처방:** P3 실행기가 Terraform을 생성.
- **검증:** 빈 계정에 `terraform apply`로 환경 재현.
- **비용 영향:** 중립.
- **출처:** 원칙 §4.4(설계 문서) · 일반 원칙(출처 미확인) ⚠️근거없음

### U-110 Terraform 원격 상태 + 잠금 + 버전 관리
- **무엇/왜:** 백엔드가 지원하면 Terraform은 상태를 쓰는 모든 작업에 잠금을 건다. S3 백엔드는 `use_lockfile = true`로 S3 네이티브 잠금을 쓰고, DynamoDB 잠금은 폐기 예정이다. 실수·삭제 복구를 위해 버킷 버전 관리를 강하게 권한다.
- **실패 양상:** 로컬 상태 파일로 두 사람이 동시에 apply → 상태 손상, 리소스 중복 생성 또는 고아 리소스. 상태 파일 분실 시 전체 인프라를 다시 import.
- **신호:** 🟢 `backend "s3"`/`"gcs"`/`"remote"` 없음(로컬 상태). 🟢 S3 백엔드에 `use_lockfile` 없음 또는 `dynamodb_table`만 있음(폐기 예정). 🟢 상태 버킷 `versioning` 비활성.
- **시나리오·수준:** U L1 이상 + Terraform 사용.
- **처방:** S3(`use_lockfile = true`, 버전 관리, 암호화) 또는 GCS 백엔드(GCS 잠금 출처 미확인). `force-unlock`은 자기 잠금에만. ⚠️근거없음
- **검증:** 두 터미널에서 동시 `plan`/`apply` → 두 번째가 잠금 대기.
- **비용 영향:** 미미한 증가.
- **출처:** https://developer.hashicorp.com/terraform/language/state/locking · https://developer.hashicorp.com/terraform/language/backend/s3

### U-111 상태 파일·plan 파일 노출
- **무엇/왜:** Terraform 상태에는 DB 비밀번호 등 민감 값이 평문으로 들어갈 수 있다. 상태·plan 파일을 커밋하거나 넓은 권한 버킷에 두면 비밀 유출이다.
- **실패 양상:** `terraform.tfstate`가 Git에 커밋되어 `aws_db_instance` 비밀번호 유출.
- **신호:** 🟢 `*.tfstate`, `*.tfstate.backup`, `*.tfplan` 추적 중, `.gitignore`에 없음. 🟢 상태 버킷 IAM이 넓음.
- **시나리오·수준:** 모든 수준 + Terraform.
- **처방:** 커밋 제거 + 노출된 비밀 교체, 상태 버킷 경로 단위 IAM 제한(S3 백엔드 문서의 권한 예시).
- **검증:** 저장소 스캔, 버킷 정책 검토.
- **비용 영향:** 중립.
- **출처:** https://developer.hashicorp.com/terraform/language/backend/s3 (상태는 민감 데이터, 경로 단위 IAM)

### U-112 드리프트 감지
- **무엇/왜:** 장애 대응 중 콘솔에서 바꾼 설정은 다음 apply 때 되돌아가거나, 코드와 실제가 어긋난 채 남는다. `terraform plan -detailed-exitcode`는 변경이 있으면 2를 반환하고, `-refresh-only`는 바깥 변경을 상태에 반영하는 계획을 만든다.
- **실패 양상:** 핫픽스로 늘린 인스턴스 크기가 다음 무관한 apply에서 조용히 원복 → 같은 장애 재발.
- **신호:** 🟢 스케줄된 워크플로에 `terraform plan -detailed-exitcode`. 🟢 GitOps 자동 동기화(Argo CD self-heal). 🔴 없음.
- **시나리오·수준:** U L2 이상 + IaC.
- **처방:** 매일 drift plan → 종료 코드 2면 알림, 콘솔 변경은 코드로 역반영.
- **검증:** 콘솔에서 태그 하나 바꾸고 다음 drift 검사가 잡는지.
- **비용 영향:** 중립.
- **출처:** https://developer.hashicorp.com/terraform/cli/commands/plan

### U-113 인프라 변경도 PR에서 plan을 보고 머지 후 한 경로로 apply
- **무엇/왜:** 사람이 로컬에서 apply하면 리뷰되지 않은 변경, 다른 브랜치 기준 apply가 섞인다. Prisma가 운영 마이그레이션을 로컬에서 하지 말라는 것과 같은 원리다.
- **실패 양상:** 오래된 브랜치에서 apply → 최근 변경 되돌림.
- **신호:** 🟢 CI에 `terraform plan` PR 코멘트 + main에서만 `apply`. 🟢 README에 "로컬에서 terraform apply".
- **시나리오·수준:** U L2 이상.
- **처방:** PR plan, 보호된 환경(U-117)에서 apply, OIDC 자격(U-090).
- **검증:** 운영 apply 권한이 CI 역할에만 있는지.
- **비용 영향:** 중립.
- **출처:** https://www.prisma.io/docs/orm/prisma-client/deployment/deploy-database-changes-with-prisma-migrate (운영 변경은 CI/CD에서, 로컬 비권장 — 같은 원칙의 DB 쪽 근거) · Terraform 쪽은 일반 원칙(출처 미확인) ⚠️출처확인필요 ⚠️근거없음

### U-114 파괴적 IaC 변경 보호
- **무엇/왜:** `prevent_destroy`는 리소스를 파괴하는 계획을 거부한다(설정 블록 자체를 지우면 막지 못함). `create_before_destroy`는 교체 시 새 것을 먼저 만든다. 이름 변경 하나가 DB "교체"(삭제 후 생성)로 계획될 수 있다.
- **실패 양상:** 속성 하나 바꿨는데 plan이 `-/+ aws_db_instance` → 리뷰어가 놓치고 apply → 데이터베이스 재생성.
- **신호:** 🟢 DB·버킷·KMS 리소스에 `lifecycle { prevent_destroy = true }` 없음. 🟢 RDS `deletion_protection`, ALB `deletion_protection.enabled`(기본 비활성) 미설정.
- **시나리오·수준:** U L1 이상 + 영속 데이터(D와 경계).
- **처방:** 상태 리소스에 `prevent_destroy` + 삭제 보호, CI에서 plan의 delete/replace 액션 검출 시 별도 승인.
- **검증:** DB 교체를 유발하는 변경 PR이 차단되는지.
- **비용 영향:** 중립.
- **출처:** https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle · https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-load-balancer-attributes.html (삭제 보호 기본 비활성)

### U-115 매니페스트 정적 검증 (스키마)
- **무엇/왜:** kubeconform은 매니페스트를 JSON 스키마로 검증하고, `-strict`는 스키마에 없는 속성·중복 키를 거부한다. 오타 필드(`readinesProbe`)는 그냥 무시되어 probe가 없는 것과 같다.
- **실패 양상:** 들여쓰기 실수로 `preStop`이 엉뚱한 위치 → 적용은 되지만 무시되어 U-024 효과 없음.
- **신호:** 🟢 CI에 `kubeconform`(simple-web-app `make k8s-validate`, 충족 예), `-strict` 여부, CRD 스키마 위치.
- **시나리오·수준:** U L1 이상, 티어2.
- **처방:** `kustomize build | kubeconform -strict -summary`, CRD는 `-schema-location` 추가.
- **검증:** 오타 필드 PR이 실패하는지.
- **비용 영향:** 중립.
- **출처:** https://github.com/yannh/kubeconform ⚠️출처확인필요

### U-116 정책 코드화 (Checkov, OPA Gatekeeper)
- **무엇/왜:** "probe 필수, latest 금지, 리소스 요청 필수, 삭제 보호" 같은 규칙을 PR 단계(Checkov: Terraform·CloudFormation·Kubernetes·Helm·CDK 등)와 클러스터 어드미션 단계(Gatekeeper: OPA 정책을 웹훅으로 강제하고 기존 리소스 감사)에서 강제한다.
- **실패 양상:** 리뷰어가 놓친 규칙 위반이 운영에 들어가고, 수동 `kubectl apply`는 CI 검사를 우회.
- **신호:** 🟢 `.checkov.yaml`, CI의 `checkov -d`, `ConstraintTemplate`, Kyverno `ClusterPolicy`. 🔴 없음.
- **시나리오·수준:** U L2 이상(티어1·2). 바이브코더 단일 서비스엔 PR 단계 검사만으로 충분(어드미션은 과잉 가능).
- **처방:** infrafit 규칙집의 U 통제를 Checkov/OPA 정책으로 내보내 재사용(새 축 후보 참고). cdk-nag는 출처 미확인. ⚠️근거없음
- **검증:** 위반 매니페스트가 PR과 어드미션에서 모두 거부되는지.
- **비용 영향:** 중립.
- **출처:** https://www.checkov.io/ · https://open-policy-agent.github.io/gatekeeper/website/docs/ ⚠️출처확인필요

### U-117 운영 배포 승인과 환경 보호 규칙
- **무엇/왜:** GitHub Environments는 필수 검토자(최대 6명·팀, 한 명 승인으로 충분), 자기 승인 금지, 대기 타이머, 배포 가능한 브랜치·태그 제한을 제공하고, 환경 비밀은 규칙을 통과한 잡에만 열린다. 단, GitHub Free에서는 공개 저장소에서만 쓸 수 있고 비공개로 바꾸면 보호 규칙과 환경 비밀이 무시된다.
- **실패 양상:** 아무 브랜치에서나 운영 배포 워크플로 실행, 운영 비밀이 모든 잡에 노출. 비공개 저장소 Free 플랜에서 규칙을 설정했다고 믿었으나 실제로는 무시됨.
- **신호:** 🟢 워크플로 잡 `environment: production` 유무. 🔴 보호 규칙 자체는 GitHub 설정(코드에 없음) → 가정. 🟢 저장소 공개 여부(가능하면 API).
- **시나리오·수준:** U L2 이상(L1은 브랜치 제한만).
- **처방:** `environment: production` + 필수 검토자(팀 규모가 1명이면 대기 타이머·브랜치 제한만).
- **검증:** 다른 브랜치에서 운영 배포 시도가 막히는지.
- **비용 영향:** 비공개 저장소면 Team/Pro 플랜 필요 → 증가.
- **출처:** https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments

### U-118 GitOps: 원하는 상태를 Git에, 동기화는 컨트롤러가
- **무엇/왜:** Argo CD 같은 GitOps 도구는 Git을 단일 진실로 두고 클러스터를 맞춘다. 롤백은 Git revert, 드리프트는 자동 감지(U-112). PreSync 훅과 sync wave로 마이그레이션 순서(U-048)를 선언할 수 있다.
- **실패 양상:** 없으면 누가 언제 무엇을 `kubectl apply`했는지 모르고, 장애 중 수동 수정이 다음 배포에서 사라짐.
- **신호:** 🟢 `Application`/`ApplicationSet`(Argo CD), `Kustomization`/`HelmRelease`(Flux, 출처 미확인). 🟢 CI가 직접 `kubectl apply`. ⚠️근거없음
- **시나리오·수준:** U L2 이상, 티어2. 단일 서비스·티어1에서는 과잉(티어1은 플랫폼 리비전 이력으로 충분).
- **처방:** 티어2: Argo CD + PreSync 마이그레이션 훅 + HPA 관리 필드(replicas) 무시 설정(U-004).
- **검증:** 클러스터에서 수동 변경 → 자동 되돌림 또는 OutOfSync 표시.
- **비용 영향:** 약간 증가(컨트롤러 리소스).
- **출처:** https://argo-cd.readthedocs.io/en/stable/user-guide/sync-waves/ ⚠️출처확인필요

### U-119 배포 직렬화 (동시 배포 금지)
- **무엇/왜:** 두 커밋의 배포가 겹치면 마이그레이션 순서가 꼬이고 이미지 지정이 뒤섞인다. GitHub Actions `concurrency` 그룹은 같은 그룹에서 한 번에 하나만 실행하고, 기본으로 대기 중인 이전 실행을 취소한다. 실행 중인 배포를 취소(`cancel-in-progress: true`)하면 절반만 적용된 상태가 남을 수 있다.
- **실패 양상:** 빠르게 두 번 머지 → 두 번째 배포가 첫 번째 마이그레이션 도중 시작. 또는 cancel-in-progress로 마이그레이션 Job 대기 중 파이프라인이 끊김.
- **신호:** 🟢 배포 워크플로에 `concurrency:` 없음. 🟢 배포 잡에 `cancel-in-progress: true`. 🟢 simple-web-app CI는 PR만 취소하고 main 푸시는 끝까지 실행(충족 예).
- **시나리오·수준:** U L1 이상.
- **처방:** `concurrency: { group: deploy-production, cancel-in-progress: false }`.
- **검증:** 연속 두 번 머지 시 배포가 순차 실행되는지.
- **비용 영향:** 중립.
- **출처:** https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency

### U-120 운영으로 가는 경로가 하나뿐인가
- **무엇/왜:** CI 파이프라인 외에 개인 노트북의 `vercel --prod`, `kubectl apply`, `gcloud run deploy`, `supabase db push`가 가능하면 위의 모든 게이트(U-092, U-117, U-119)가 우회된다.
- **실패 양상:** 금요일 밤 노트북에서 직접 배포한 테스트 안 된 빌드가 운영에.
- **신호:** 🟢 README/Makefile에 운영 대상 수동 배포 명령. 🔴 개인 자격 증명 권한은 코드에 없음 → 가정.
- **시나리오·수준:** U L2 이상.
- **처방:** 운영 쓰기 권한을 CI 역할(OIDC)에만, 사람은 읽기 + 긴급 절차(break-glass)만.
- **검증:** 개인 자격 증명으로 운영 배포 시도 시 거부.
- **비용 영향:** 중립.
- **출처:** https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments (배포 브랜치·환경 비밀 제한) · 단일 경로 원칙은 일반 원칙(출처 미확인) ⚠️근거없음

---

## 새 축·규칙 후보

이 영역을 정리하며 설계 문서(§4, §8.4)의 현재 U 통제 8개로는 표현하기 어려웠던 것들이다.

1. **"N-1 호환" 불변식을 U L2의 중심 통제로.** 현재 U-CTL-003(expand/contract)은 DB만 본다. 실제로는 DB 스키마(U-044), API(U-061), 메시지(U-063·U-064), 프론트 자산(U-065), 세션 키(U-072), 설정 이름(U-036)이 모두 같은 불변식 "직전 버전과 동시에 돌 수 있고, 직전 버전으로 롤백할 수 있다"의 사례다. 통제 하나(`U-CTL-N1`)에 하위 검사 여러 개를 두고, P4 검증은 "마이그레이션 적용 후 구버전 이미지로 통합 테스트"(U-044 검증) 하나로 대표할 수 있다.

2. **마이그레이션 위험도를 정적 점수로.** `db.migration.destructive` 하나로는 부족하다. 탐지기에 (a) 잠금 범주(ACCESS EXCLUSIVE / 재작성 / 전체 스캔 / 약한 잠금), (b) `lock_timeout` 유무, (c) 트랜잭션 래핑 여부와 `CONCURRENTLY` 충돌, (d) 같은 파일 DROP+ADD(이름 변경 의심), (e) 백필 UPDATE를 넣어 사실 `db.migration.lock_risk`를 만들면 U-049~U-053을 하나의 규칙군으로 판정할 수 있다. 테이블 크기는 코드에 없으므로 가정 `data.largest_table_rows`(도메인별 기본값)를 추가해야 한다.

3. **타이밍 정렬 규칙(숫자 부등식)을 한 곳에.** preStop < LB 드레이닝 ≤ terminationGrace, 앱 keep-alive > LB idle, grace ≥ 최장 요청, 워커 grace ≥ 최장 작업, 플랫폼 상한(Cloud Run 10초, ECS stopTimeout 최대 120초, k8s 기본 30초). 이것들은 모두 "탐지한 숫자들의 부등식"이라 결정적 규칙에 잘 맞는다. `kind: timing` 같은 규칙 종류를 두고 플랫폼별 상수 표를 출처와 함께 관리하는 것을 제안한다.

4. **"프리뷰가 운영을 건드린다"를 독립 위험으로.** U-105(빌드 단계 마이그레이션 + Preview env 공유)는 U 수준과 무관하게 데이터를 망가뜨린다. 시나리오 U의 수준 규칙보다는 D/C와 같은 무조건 위험(L0에서도 표시)으로 분류하는 편이 맞다. 같은 범주: 커밋된 비밀(U-095), 공개 변수의 비밀(U-096), 이미지 안 비밀(U-088), 상태 파일 커밋(U-111).

5. **플랫폼 기본값이 오히려 함정인 목록을 규칙 입력으로.** GKE BackendConfig 드레이닝 기본 0(비활성), ALB deregistration 기본 300초, Node keepAliveTimeout 5초, k8s CronJob `concurrencyPolicy: Allow`, `minReadySeconds: 0`, `lock_timeout`/`statement_timeout` 0, Vercel Skew Protection 기본 최대 수명 1일, Vercel 롤백 후 자동 승격 꺼짐, GitHub Free 비공개 저장소의 환경 보호 무시. "설정이 없음"을 "기본값이 적용됨"으로 바꿔 판정하려면 플랫폼별 기본값 표(`rules/platform_defaults.yaml`)가 필요하다.

6. **티어0 판정에 플랜 정보를 가정으로.** Skew Protection(Pro 이상), Instant Rollback 범위(Hobby는 직전 배포만), 크론 빈도(Hobby 하루 1회), Password Protection 가격, GitHub 환경 보호(Team/Pro)처럼 플랜에 따라 통제 충족 여부가 갈린다. 코드에서는 알 수 없으므로 가정 `platform.plan`(기본값 무료 플랜)을 두고, 무료 플랜이면 해당 통제를 "미충족 + 플랜 업그레이드 비용"으로 처방하면 비용 필터와 자연스럽게 연결된다.

7. **과잉 판정 규칙 후보(비용 필터).** U L1 앱에 블루그린(U-009), 서명 검증 어드미션(U-091), Gatekeeper(U-116), GitOps 컨트롤러(U-118), 상시 스테이징 환경(U-104)이 있으면 과잉으로 표시하고 더 싼 대안(롤링 + 자동 롤백, PR 단계 Checkov, 플랫폼 리비전 이력, 프리뷰 환경)을 제시한다.

8. **P4 U 검증 시나리오 확장 제안.** 현재 P4 U는 "부하 중 롤링, 실패 버전 자동 롤백"이다. 추가 후보: (a) 구버전 브라우저 탭 유지 후 배포 → 청크 오류 0(U-065), (b) 마이그레이션 중 장기 트랜잭션을 잡아 두기 → 앱 쿼리 대기 없음(U-049), (c) 배포를 크론 시각에 맞춰 → 실행 1회(U-076), (d) 비밀 교체 리허설 → 오류 0(U-100), (e) 롤백 직후 구버전으로 정상 동작(U-036).

9. **simple-web-app(F1) 골든 판정에 반영할 발견.** 충족: readiness/liveness, preStop 15초와 드레이닝 30초 정렬, readiness gate 계약, 마이그레이션 Job 분리와 advisory lock, Job 데드라인, kubeconform, lock 파일 + `npm ci`, CI 최소 권한, 배포 concurrency, dev/prod 분리, HTML no-cache·자산 immutable. 미충족·주의: 마이그레이션과 앱 롤아웃 동시 시작(U-048, 문서화된 의도적 차이), 마이그레이션 러너가 모든 파일을 한 트랜잭션으로 감싸 `CREATE INDEX CONCURRENTLY` 불가(U-050), `lock_timeout` 없음(U-049), `minReadySeconds`·`startupProbe` 없음(U-006·U-017), nginx 이미지 교체 시 이전 해시 자산 소실(U-065), 베이스 이미지·액션 태그 고정(다이제스트·SHA 아님, U-086·U-090), 로컬 빌드·푸시 절차로 인한 아키텍처 불일치 가능성(U-089), 자동 롤백·지표 기반 중단 없음(U-033·U-034).
