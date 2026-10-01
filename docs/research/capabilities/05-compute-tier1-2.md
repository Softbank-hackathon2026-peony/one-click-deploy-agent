# 컴퓨트 티어 1·2 능력 표 (관리형 컨테이너, 함수, 쿠버네티스)

- 작성일: 2026-10-01
- 형식·능력 키: [README.md](README.md) §1, §2.7 (CP.* 18개)
- 요구 쪽: [../dimensions.md](../dimensions.md)
- 출처 원칙: 모든 값은 2026-10-01에 공식 문서를 직접 열어 확인했다. AWS 서울 단가는 Price List 오퍼 파일(`https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/{AmazonECS|AmazonEKS|AWSELB|AmazonVPC|AWSLambda|AmazonApiGateway}/current/ap-northeast-2/index.json`, EC2·NAT는 같은 경로의 `AmazonEC2/.../index.csv`)을 curl로 받아 읽었다(표에서 **[PL]**). GCP 서울 단가는 가격 페이지에 들어 있는 리전 표(JSON)에서 읽었다. Azure Korea Central 단가는 Azure 소매 가격 API(`https://prices.azure.com/api/retail/prices`)에서 읽었다. 확인하지 못한 값은 `미확인`이다.
- 월 환산은 730시간(= 2,628,000초) 기준이다. "평가"라고 적은 값은 문서 인용이 아닌 판단이다(주로 CP.ops_burden).

## 범위

| 티어 | 구성 요소·모드 |
|---|---|
| 1 | Cloud Run 서비스(요청 기반 과금 / 인스턴스 기반 과금), Cloud Run Jobs, Cloud Run 워커 풀, Cloud Run functions(= Cloud Functions 2세대), ECS on Fargate(일반 서비스 / Express Mode / Fargate Spot), AWS App Runner, AWS Lambda(Function URL / API Gateway 경유), Azure Container Apps |
| 2 | GKE Autopilot, GKE Standard(존 / 리전), Amazon EKS(관리형 노드 그룹 / Karpenter / Auto Mode / Fargate 프로필), VM 위 k3s(요약) |
| 기준선 | 단일 VM + docker compose (EC2 / Compute Engine) |

## 목차

0. [요약 비교표](#0-요약-비교표)
1. [공통: 교체 계약과 LB 기본값](#1-공통-교체-계약과-lb-기본값)
2. 티어 1 — Google Cloud
   - [2.1 Cloud Run 서비스 — 요청 기반 과금](#21-cloud-run-서비스--요청-기반-과금)
   - [2.2 Cloud Run 서비스 — 인스턴스 기반 과금](#22-cloud-run-서비스--인스턴스-기반-과금)
   - [2.3 Cloud Run Jobs](#23-cloud-run-jobs)
   - [2.4 Cloud Run 워커 풀](#24-cloud-run-워커-풀)
   - [2.5 Cloud Run functions (Cloud Functions 2세대)](#25-cloud-run-functions-cloud-functions-2세대)
3. 티어 1 — AWS
   - [3.1 ECS on Fargate — 일반 서비스 (ALB)](#31-ecs-on-fargate--일반-서비스-alb)
   - [3.2 ECS on Fargate — Express Mode](#32-ecs-on-fargate--express-mode)
   - [3.3 ECS on Fargate — Fargate Spot](#33-ecs-on-fargate--fargate-spot)
   - [3.4 AWS App Runner (신규 고객 불가)](#34-aws-app-runner--신규-고객-불가)
   - [3.5 AWS Lambda — Function URL](#35-aws-lambda--function-url)
   - [3.6 AWS Lambda — API Gateway 경유 (REST / HTTP / WebSocket API)](#36-aws-lambda--api-gateway-경유-rest--http--websocket-api)
4. 티어 1 — Azure
   - [4.1 Azure Container Apps — 워크로드 프로필 환경, Consumption 프로필](#41-azure-container-apps--워크로드-프로필-환경-consumption-프로필)
5. 티어 2 — GKE
   - [5.1 GKE Autopilot](#51-gke-autopilot)
   - [5.2 GKE Standard — 존 클러스터](#52-gke-standard--존-클러스터)
   - [5.3 GKE Standard — 리전 클러스터](#53-gke-standard--리전-클러스터)
6. 티어 2 — EKS
   - [6.1 EKS — 관리형 노드 그룹 + Cluster Autoscaler](#61-eks--관리형-노드-그룹--cluster-autoscaler)
   - [6.2 EKS — Karpenter](#62-eks--karpenter)
   - [6.3 EKS — Auto Mode](#63-eks--auto-mode)
   - [6.4 EKS — Fargate 프로필](#64-eks--fargate-프로필)
   - [6.5 VM 위 경량 쿠버네티스 — k3s (요약)](#65-vm-위-경량-쿠버네티스--k3s-요약)
7. 기준선
   - [7.1 단일 VM + docker compose — EC2](#71-단일-vm--docker-compose--ec2)
   - [7.2 단일 VM + docker compose — Compute Engine](#72-단일-vm--docker-compose--compute-engine)
8. [판정을 뒤집는 발견](#8-판정을-뒤집는-발견)

---

## 0. 요약 비교표

값은 아래 각 절의 표에서 가져왔다(출처는 각 절). "LB"는 그 플랫폼의 기본 진입 로드밸런서다. 월 고정비는 서울, 트래픽 0일 때 꺼지지 않는 최소 구성 기준이며 데이터 처리·이그레스는 뺐다.

| 플랫폼·모드 | 최대 요청 시간 / LB 유휴 | 웹소켓 지속 | 요청 밖 CPU (A4) | scale-to-zero / 최소 | 인스턴스당 최대 vCPU·메모리 | GPU (서울) | 본문 한도 | 로컬 디스크 / 영속 볼륨 | 동시성 기본 | 종료 유예 | 서울 | 최소 월 고정비 (서울) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Cloud Run 서비스 · 요청 기반 | 기본 300초, 최대 3,600초 | 요청 타임아웃까지(최대 60분), 연결 중엔 인스턴스 과금 | **없음** (요청·기동·종료 때만) | 예 / min 0 | 8 vCPU · 32 GiB | 있음, 서울 **없음** | HTTP/1 요청·응답 32 MiB, HTTP/2 무제한 | 메모리 FS(메모리 차감) / GCS FUSE·NFS, 임시 디스크 Preview | 80×vCPU(gcloud·Terraform), 최대 1,000 | SIGTERM 후 10초 | 있음(Tier 2) | $0 (min 1 시 약 $13.8) |
| Cloud Run 서비스 · 인스턴스 기반 | 같음 | 같음 | **있음** | 예 / min 0 | 8 vCPU · 32 GiB | L4·RTX PRO 6000, 서울 **없음** | 같음 | 같음 | 같음 | 10초 | 있음(Tier 2) | $0 (min 1 시 약 $59.9) |
| Cloud Run Jobs | 태스크 기본 10분, 최대 168시간(GPU 1시간) | 해당 없음 | 있음 | 실행 때만 | 8 vCPU · 32 GiB | 서울 없음 | 해당 없음 | 메모리 FS | 해당 없음 | 10초 | 있음 | $0 |
| Cloud Run 워커 풀 | 해당 없음(상시) | 해당 없음(URL 없음) | 있음 | 수동 인스턴스 수 | 미확인(서비스와 같다고 가정 안 함) | 서울 없음 | 해당 없음 | 메모리 FS | 해당 없음 | 10초 | 있음 | 1 vCPU·0.5 GiB 1개 약 $37.4 |
| Cloud Run functions | HTTP 60분, 이벤트 9분 | 서비스와 같음 | 서비스와 같음 | 예 | 문서 간 불일치(미확인) | 서울 없음 | 요청 32 MB, 스트리밍 응답 10 MB | 메모리 FS | 최대 1,000 | 10초 | 있음 | $0 + 빌드 비용 |
| ECS Fargate · 일반 | 제한 없음 / ALB 유휴 기본 60초(1~4,000초) | ALB 유휴 타임아웃 내 무기한 | 있음 | 아니오 / desired ≥1 | 32 vCPU · 244 GB | **불가** | ALB 헤더 64K, 본문 미확인 | 임시 20~200 GiB / EFS, EBS(태스크당 1개, 종료 시 삭제) | 앱이 결정 | stopTimeout 기본 30초, 최대 120초 + ALB 드레인 300초 | 있음 | 약 $27(0.25 vCPU 태스크 1 + ALB) + NAT $43/AZ(사설 시) |
| ECS Express Mode | 같음(ALB 자동 생성) | 같음 | 있음 | 아니오 / min 1 | 기본 1 vCPU·2 GB | 불가 | 같음 | 같음 | 앱 | 30초 | 있음 | 약 $58(1 vCPU·2 GB 1 + ALB) |
| Fargate Spot | 같음 | 같음 | 있음 | 아니오 | 일반과 같음 | 불가 | 같음 | 같음 | 앱 | **2분 경고** + SIGTERM | 미확인 | 최대 70% 할인(서울 단가 미확인) |
| App Runner | **120초**(본문 읽기 포함) | 미지원(로드맵 "not planned") | 유휴 시 메모리만 과금 | 아니오 / min 1 | 4 vCPU · 12 GB | 불가 | 미확인 | 임시 3 GB | 100(최대 200) | 미확인 | **없음** | 신규 고객 불가 |
| Lambda · Function URL | **900초** | 미지원(스트리밍 응답만) | **없음**(동결) | 예 | 10,240 MB(1,769 MB = 1 vCPU) | 불가 | 동기 6 MB, 스트리밍 응답 200 MB | /tmp 512 MB~10 GB / EFS | **1** | 0~2초 | 있음 | $0 |
| Lambda · API Gateway | REST 29초(리전·사설은 상향 가능), HTTP API **30초 고정** | WebSocket API 최대 2시간, 유휴 10분 | 없음 | 예 | 같음 | 불가 | 10 MB(API GW) + 6 MB(Lambda) | 같음 | 1 | 같음 | 있음 | $0 + 요청당 |
| Azure Container Apps | **240초**(기본 인그레스) | 지원, 240초 적용 여부 미확인 | 있음(유휴 요율) | 예 / min 0 | 4 vCPU · 8 GiB | 서울 **없음** | 미확인 | 임시 1~8 GiB / Azure Files | HTTP 규칙 10 | **30초** | 있음(Korea Central) | $0 (min 1 시 약 $11.8) |
| GKE Autopilot | Ingress 기본 **30초**(BackendConfig로 변경) | 클래식 ALB: 백엔드 타임아웃에 끊김(기본 30초) / 관리형 Gateway: 24시간 | 있음 | 노드 0까지, Pod는 HPA 하한 | 일반 30 vCPU·110 GiB, Balanced 222 vCPU | 있음, 서울 존 a·b·c에 L4/T4 등 | 헤더 60 KiB, 본문 미확인 | Pod 임시 10 GiB / PD(RWO) | 앱 | 30초(업그레이드 시 최대 600초) | 있음 | Pod 0.5 vCPU·2 GiB 약 $30 + LB 약 $18(요금 무료 크레딧 상쇄) |
| GKE Standard · 존 | 같음 | 같음 | 있음 | **노드 0 불가**(최소 1) | VM 크기 | 있음 | 같음 | 노드 디스크 / PD(RWO) | 앱 | 30초 | 있음 | e2-medium 1대 $31.4 + LB 약 $18 |
| GKE Standard · 리전 | 같음 | 같음 | 있음 | 노드 0 불가, 기본 9노드 | VM 크기 | 있음 | 같음 | 같음 | 앱 | 30초 | 있음 | 요금 $73(크레딧 없음) + 존당 1노드 이상 |
| EKS · 관리형 노드 그룹 | ALB 유휴 60초 / NLB TCP 350초 | ALB 유휴 내 | 있음 | 노드 최소값까지 | 인스턴스 크기 | 있음(G4dn·G5·G6·P4d·P5 등) | ALB 헤더 64K | EBS(단일 AZ, RWO) / EFS | 앱 | 30초 + ALB 드레인 300초 | 있음 | 약 $212(요금 $73 + t3.medium 2 + EBS + ALB + NAT 1) |
| EKS · Karpenter | 같음 | 같음 | 있음 | 노드 0 가능(컨트롤러용 노드는 별도) | 같음 | 있음 | 같음 | 같음 | 앱 | 30초, 노드 만료 30일 | 있음 | MNG와 비슷(컨트롤러용 노드 필요) |
| EKS · Auto Mode | 같음(대상 ip 기본) | 같음 | 있음 | 노드 축소 | 기본 풀 C·M·R만, GPU는 사용자 풀 | 있음(사용자 NodePool) | 같음 | EBS(전용 프로비저너) | 앱 | 30초, 노드 수명 최대 21일 | 있음 | 약 $195(요금 + c6g.large 1 + 관리비 + ALB + NAT) |
| EKS · Fargate 프로필 | 같음(대상 ip 필수) | 같음 | 있음(요청만큼) | 아니오 | 16 vCPU · 120 GB | **불가** | 같음 | 임시 20~175 GiB / EFS(정적), EBS 불가 | 앱 | 30초 | 있음 | 요금 $73 + Pod + NAT(사설 서브넷 필수) |
| k3s on VM | 자체 Traefik 설정 | 자체 설정 | 있음 | 아니오 | VM 크기 | VM에 따름 | 자체 설정 | local-path(노드 고정) | 앱 | 30초 | VM 리전 | VM 1대(t3.small 약 $24.5), HA는 서버 3대 |
| 단일 VM · EC2 | 없음(LB 없으면) | 무기한 | 있음 | 아니오 | 인스턴스 크기 | 있음 | 리버스 프록시 설정 | EBS 영속(단일 AZ) | 앱 | compose 10초 | 있음 | t4g.small 약 $20.7 / t3.small 약 $24.5 |
| 단일 VM · Compute Engine | 없음 | 무기한 | 있음 | 아니오 | e2 최대 32 vCPU·128 GB | 있음(존별) | 프록시 설정 | PD 영속(존) | 앱 | compose 10초 | 있음 | e2-small $15.7 + 디스크·IP(미확인) |

---

## 1. 공통: 교체 계약과 LB 기본값

### 1.1 티어 0 → 티어 1 공통 산출물
티어 1 플랫폼은 모두 "OCI 이미지 + HTTP 포트 + 종료 신호"라는 같은 계약을 쓴다(Lambda·functions는 예외, 해당 절 참고).

| 산출물·변경 | 내용 | 근거 |
|---|---|---|
| Dockerfile | 단일 프로세스, `PORT` 환경변수로 리슨, `0.0.0.0` 바인드. Cloud Run은 기동 후 4분 안에 포트를 열어야 한다 | https://docs.cloud.google.com/run/docs/container-contract · "The ingress container within an instance must listen for requests on `0.0.0.0` on the port to which requests are sent." · 2026-10-01 |
| SIGTERM 처리 | PID 1이 신호를 받아야 한다. 셸 래퍼 엔트리포인트면 앱이 강제 종료된다. 받은 뒤 새 요청 거절, 진행 중 요청 마무리, DB 풀 닫기 | https://docs.aws.amazon.com/eks/latest/best-practices/application.html · "When the Pod is terminated, the Python application will be killed abruptly." · 2026-10-01 |
| 헬스체크 | 준비(readiness)와 생존(liveness)을 분리. ALB·GKE LB는 헬스체크 경로로 대상을 뺀다 | 각 절 |
| 환경변수·시크릿 | 티어 0 대시보드 변수 → 플랫폼 시크릿 저장소(Secret Manager, Secrets Manager, Key Vault) | 이 표 범위 밖 |
| 플랫폼 전용 API 대체 | `@vercel/functions` `waitUntil`, Netlify 백그라운드 함수, Supabase Edge 런타임 등은 큐·워커 또는 요청 밖 CPU가 있는 모드로 바꾼다 | [04-compute-tier0.md](04-compute-tier0.md) |
| 상태 분리 | 메모리 세션·로컬 파일은 인스턴스가 2개 이상이 되는 순간 깨진다(B1, B2). Redis·오브젝트 스토리지로 | [03-cache-queue-scheduler-realtime-storage.md](03-cache-queue-scheduler-realtime-storage.md) |

### 1.2 티어 1 → 티어 2 공통 추가 산출물
Deployment·Service·Ingress(또는 Gateway) 매니페스트, `resources.requests`(노드 오토스케일러와 Autopilot 과금이 requests로 판단), readinessProbe·livenessProbe·startupProbe, `preStop` + `terminationGracePeriodSeconds`, PodDisruptionBudget, HPA. 그리고 클러스터 자체(IaC, 업그레이드 주기, 애드온).

### 1.3 로드밸런서 기본값 (여러 절이 참조)

| 항목 | 값 | 출처 (URL · 인용 · 2026-10-01) |
|---|---|---|
| AWS ALB 유휴 타임아웃 | 기본 60초, 1~4,000초 | https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-load-balancer-attributes.html · "By default, Elastic Load Balancing sets the idle timeout value for your load balancer to 60 seconds." / "The valid range is 1 through 4000 seconds." · 2026-10-01 |
| ALB 클라이언트 keepalive | 기본 3,600초 | 같은 페이지 · "sets the HTTP client keepalive duration value for load balancers to 3600 seconds, or 1 hour." · 2026-10-01 |
| ALB HTTP/2 PING | 유휴 타임아웃을 리셋하지 않음 | 같은 페이지 · "Application Load Balancers do not support HTTP/2 PING frames. These do not reset the connection idle timeout." · 2026-10-01 |
| ALB 웹소켓 | 기본 지원, 연결 단위 고정 | https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-listeners.html · "Application Load Balancers provide native support for WebSockets." · 2026-10-01 |
| ALB 헤더 한도 | 요청 줄 16K, 단일 헤더 16K, 전체 요청 헤더 64K, 응답 헤더 32K(조정 불가). 본문 한도는 문서에서 찾지 못함 → 미확인 | https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-limits.html · "Entire request header \| 64 K \| No" · 2026-10-01 |
| ALB 등록 해제 지연 | 기본 300초, 0~3,600초 | https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-target-groups.html · "The range is 0–3600 seconds. The default value is 300 seconds." · 2026-10-01 |
| AWS NLB TCP 유휴 | 기본 350초, 60~6,000초 | https://docs.aws.amazon.com/elasticloadbalancing/latest/network/network-load-balancers.html · "The default idle timeout value for TCP flows is 350 seconds, but can be updated to any value between 60-6000 seconds." · 2026-10-01 |
| ALB 서울 단가 | $0.0225/시간(월 $16.43) + $0.008/LCU-시간 | [PL] AWSELB ap-northeast-2 · "$0.0225 per Application LoadBalancer-hour (or partial hour)" · 2026-10-01 |
| NAT Gateway 서울 | $0.059/시간(월 $43.07, AZ당) + $0.059/GB | [PL] AmazonEC2 ap-northeast-2 · "$0.059 per NAT Gateway Hour" / "$0.059 per GB Data Processed by NAT Gateways" · 2026-10-01 |
| NAT Gateway 존 범위 | AZ 하나에 생성, AZ마다 두어야 존 장애에 견딤. 탄력적 IP 연결(기본 2개) = 고정 출구 IP | https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-basics.html · "Each NAT gateway is created in a specific Availability Zone and implemented with redundancy in that zone." · 2026-10-01 |
| AWS 공인 IPv4 서울 | $0.005/시간(월 $3.65/개, 사용 중·유휴 동일) | [PL] AmazonVPC ap-northeast-2 · "$0.005 per In-use public IPv4 address per hour" · 2026-10-01 |
| GCP 외부 Application LB 백엔드 타임아웃 | 서버리스 NEG 외 기본 30초 | https://docs.cloud.google.com/load-balancing/docs/https/request-distribution · "Except for serverless NEGs, the default value for the backend service timeout is 30 seconds." · 2026-10-01 |
| GCP 클래식 ALB 웹소켓 | 유휴·활성 관계없이 백엔드 타임아웃에 종료 | 같은 페이지 · "Websocket connections, whether idle or active, automatically close after the backend service times out." · 2026-10-01 |
| GCP 전역 외부 ALB(관리형) 웹소켓 | 활성 연결은 타임아웃 무시, 24시간에 종료 | 같은 페이지 · "Active websocket connections don't use the configured backend service timeout ... automatically closed after 24 hours (86,400 seconds)." · 2026-10-01 |
| GCP LB 헤더 한도 | URL + 요청 헤더 60 KiB 이하. 본문 한도 미확인 | https://docs.cloud.google.com/load-balancing/docs/quotas · "The combined size of the request URL and request header must be less than or equal to 60 KiB." · 2026-10-01 |
| GCP 포워딩 규칙 | 처음 5개 $0.025/시간(월 약 $18.25), 추가 $0.01/시간. 서울 단가 별도 표기 미확인 | https://cloud.google.com/vpc/network-pricing · "First 5 forwarding rules $0.025 / 1 hour" · 2026-10-01 |
| GCP Cloud NAT | VM당 $0.0014/시간(32대까지), 처리 $0.045/GiB, NAT IP $0.005/시간 | https://cloud.google.com/nat/pricing · "Up to 32 VM instances $0.0014 * the number of VM instances that are using the gateway $0.045 $0.005" · 2026-10-01 |

---

## 2.1 Cloud Run 서비스 — 요청 기반 과금
- 계열: 컴퓨트-티어1
- 서울 리전: 있음, **Tier 2 요금** (https://docs.cloud.google.com/run/docs/locations · "Subject to Tier 2 pricing asia-east2 (Hong Kong) asia-northeast3 (Seoul, South Korea) …" · 2026-10-01)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | 웹(HTTP·gRPC·웹소켓). 상시 워커는 **부적합**(요청 밖 CPU 없음) → 워커 풀이나 인스턴스 기반 과금으로. 정기 작업은 Cloud Scheduler → HTTP 호출 또는 Jobs | 앱 안 스케줄러(B3)는 CPU가 없어 돌지 않는다 | https://docs.cloud.google.com/run/docs/configuring/billing-settings · "CPU is only allocated during request processing." · 2026-10-01 |
| CP.request_timeout | 기본 300초, 최대 3,600초. Cloud Run 자체 진입점이라 별도 LB 유휴 타임아웃 없음(외부 LB를 앞에 두면 서버리스 NEG 규칙 적용) | 15분 넘으면 재시도·멱등성 권장 | https://docs.cloud.google.com/run/docs/configuring/request-timeout · "set by default to 5 minutes (300 seconds) and can be extended up to 60 minutes (3600 seconds)" · 2026-10-01 |
| CP.long_connection | 웹소켓 지원. 스트림 하나 = 요청 하나라 요청 타임아웃(최대 60분)에 끊김 → 클라이언트 재연결 필수. **열린 웹소켓이 있는 인스턴스는 인스턴스 기반 과금으로 청구**. SSE도 일반 HTTP 응답이라 같은 타임아웃(SSE 전용 문서는 없음) | 세션 어피니티는 최선 노력 | https://docs.cloud.google.com/run/docs/triggering/websockets · "WebSockets streams are HTTP requests, which are still subject to the request timeout configured for your Cloud Run service." / "A Cloud Run instance that has any open WebSocket connection is considered active, so CPU is allocated and the service is billed as instance-based billing." · 2026-10-01 |
| CP.cpu_outside_request | **없음.** 요청 처리·기동·종료 중에만 CPU. 응답 뒤 작업(A4)은 멈추거나 극도로 느려진다 | — | https://docs.cloud.google.com/run/docs/configuring/billing-settings · "CPU is only allocated during request processing." · 2026-10-01 |
| CP.cold_start | 기본 scale-to-zero, min-instances 기본 0. 최소 인스턴스도 재시작될 수 있음. 시작 CPU 부스트: 기동 + 10초 동안 vCPU 증설(부스트분 과금). 부스트 기본 켜짐 여부 미확인 | 유휴 인스턴스는 최대 15분 유지 | https://docs.cloud.google.com/run/docs/about-instance-autoscaling · "when a revision does not receive any traffic, by default, it is scaled to zero instances" / https://docs.cloud.google.com/run/docs/configuring/min-instances · "Minimum instances can be restarted at any time." · 2026-10-01 |
| CP.instance_size | 최대 8 vCPU, 32 GiB(8 vCPU는 4~32 GiB). GPU는 인스턴스 기반 과금에서만(§2.2) | — | https://docs.cloud.google.com/run/quotas · "The maximum amount of vCPU you can configure is 8 vCPU." · 2026-10-01 |
| CP.request_size | HTTP/1 요청 32 MiB, 응답 32 MiB. HTTP/2 서버면 제한 없음. HTTP/1 인바운드 인스턴스당 초당 800건 | 큰 업로드(A7)는 서명 URL로 | https://docs.cloud.google.com/run/quotas · "Maximum HTTP/1 request size: 32 MiB per request" / "No limit if using HTTP/2 server" · 2026-10-01 |
| CP.local_disk | 쓰기 가능한 파일시스템은 **메모리 위**(쓰면 메모리 차감, 인스턴스 종료 시 소멸). 인메모리 볼륨은 컨테이너 메모리 차감. 임시 디스크 1~100 Gi는 **Preview**(2세대 실행 환경). Cloud Storage FUSE·NFS 볼륨 마운트 지원(해당 문서 인용 미확인) | 영속 블록 볼륨 없음 → SQLite·업로드 저장(B2) 불가 | https://docs.cloud.google.com/run/docs/container-contract · "It is an in-memory file system, so writing to it uses the instance's memory. Data written to the file system doesn't persist when the instance stops." / https://docs.cloud.google.com/run/docs/configuring/services/ephemeral-disk (Preview) · 2026-10-01 |
| CP.scaling | 리비전당 최대 인스턴스 기본 100, 급증 시 잠시 초과 가능. 오토스케일러 목표 CPU·동시성 60%. 대기 요청은 max(평균 기동 시간 × 3.5, 10초)까지 보류. 절대 상한 미확인 | max-instances는 DB 연결 상한과 맞출 것 | https://docs.cloud.google.com/run/docs/configuring/max-instances · "By default, Cloud Run sets 100 instances for each revision." / "this maximum setting can be exceeded for a brief period" · 2026-10-01 |
| CP.concurrency | 기본 **80 × vCPU**(gcloud·Terraform 배포), 콘솔 배포는 80. 최대 1,000. 1로 두면 Lambda처럼 요청당 인스턴스 | — | https://docs.cloud.google.com/run/docs/about-concurrency · "maximum concurrency that is 80 times the number of vCPUs" / "You can increase this to a maximum of 1,000." · 2026-10-01 |
| CP.shutdown | SIGTERM → **10초** → SIGKILL | 조정 불가 | https://docs.cloud.google.com/run/docs/container-contract · "sends a SIGTERM signal to all the containers in an instance, indicating the start of a 10 second period before the actual shutdown" · 2026-10-01 |
| CP.deploy | 불변 리비전, 비율 트래픽 분할, `--no-traffic` 후 점진 이전, `update-traffic`로 즉시 롤백, 태그 URL. 진행 중 요청은 완료. 서킷 브레이커형 자동 롤백 없음(헬스체크 실패 리비전은 트래픽을 받지 않음, 인용 미확인) | 리비전 최대 1,000개 보관 | https://docs.cloud.google.com/run/docs/rollouts-rollbacks-traffic-migration · "When you change traffic for revisions, all requests being processed will continue to completion." · 2026-10-01 |
| CP.availability | 리전 안 멀티 존 기본(존 중복은 GPU 서비스만 끌 수 있음). 멀티 리전은 외부 LB + 서버리스 NEG(인용 미확인) | — | https://docs.cloud.google.com/run/docs/zonal-redundancy · "Data and traffic are automatically load balanced across zones within a region." · 2026-10-01 |
| CP.networking | Direct VPC egress(권장) 또는 Serverless VPC Access 커넥터로 사설 DB 접근. 고정 출구 IP = Cloud NAT + 예약 IP + `--vpc-egress=all-traffic`. Direct VPC는 인스턴스당 IP 2개, /26 이상 서브넷 | Cloud NAT 사용 시 콜드 스타트 지연 가능 | https://docs.cloud.google.com/run/docs/configuring/static-outbound-ip · "route all outbound traffic through a VPC network that has a Cloud NAT gateway configured with the static IP address" · 2026-10-01 |
| CP.regions | asia-northeast3 있음(Tier 2). 서울에서 도메인 매핑 제외 여부는 미확인(제외라면 LB 필요) | — | https://docs.cloud.google.com/run/docs/locations · "Subject to Tier 2 pricing … asia-northeast3 (Seoul, South Korea)" · 2026-10-01 |
| CP.plan_limits | 프로젝트·리전당 서비스 1,000개, 최대 인스턴스 할당량 100(상향 가능), 인스턴스당 열린 파일 25,000, 아웃바운드 연결 초당 700 | — | https://docs.cloud.google.com/run/quotas · "Maximum number of services: 1000 per project and region" · 2026-10-01 |
| CP.ops_burden | 낮음(평가): 노드·OS·LB·인증서 관리 없음. 남는 일은 이미지, 리비전, IAM, VPC 연결, max-instances 산정 | — | https://cloud.google.com/run/pricing · "requires low operations because Site Reliability Engineers do a lot in the background" · 2026-10-01 |
| CP.cost_floor | **$0**(scale-to-zero). 서울 활성 vCPU $0.0000336/초, 유휴(최소 인스턴스) vCPU $0.0000035/초, 메모리 $0.0000035/GiB초, 요청 $0.40/100만. min 1(1 vCPU·0.5 GiB) 유휴 상시 ≈ **월 $13.8** | 100 ms 단위 올림. 무료 등급(아래)은 Tier 1 단가로 적용 | https://cloud.google.com/run/pricing (페이지 내 리전 표) · "Idle instances that are not minimum instances are not charged." · 2026-10-01 |

### 비용 구조
- 최소 월 고정비: $0. 최소 인스턴스를 두면 유휴 요율(서울 vCPU $0.0000035/초)로 과금.
- 변동 단위: 요청 처리 중 vCPU·초, GiB·초, 요청 수.
- 무료 등급: 월 180,000 vCPU초, 360,000 GiB초, 요청 200만 건(결제 계정당). "CPU - First 180,000 vCPU-seconds free per month RAM - First 360,000 GiB-seconds free per month Requests - 2 million requests free per month" (https://cloud.google.com/run/pricing, 2026-10-01).
- 과금 함정: 서울은 Tier 2라 활성 CPU가 Tier 1($0.000024)보다 40% 비싸다. 가격 페이지 JSON에 서울 표가 두 개 있고 하나는 Tier 1 값과 같다. 이 문서는 CUD 열이 있는 주 표(Tier 2 값)를 썼다. 웹소켓을 열어 두면 인스턴스 기반으로 과금된다.

### 교체 계열 정보
- 티어 0에서 올 때: Dockerfile(또는 소스 배포 buildpack), `PORT` 리슨, SIGTERM 10초 안에 마무리, 로컬 파일 → GCS, 메모리 세션 → Memorystore 등. `waitUntil`/`after` 같은 응답 후 작업은 이 모드에서 동작하지 않으므로 Cloud Tasks·Pub/Sub로 빼거나 §2.2로 간다.
- 티어 2(GKE)로 갈 때: 같은 이미지가 그대로 돈다. 추가로 Deployment·Service·Ingress, requests, probe, preStop. Cloud Run의 동시성 제한·max-instances는 HPA와 앱 내 동시성 한도로 바꿔야 한다. Cloud Run 전용: 리비전 태그 URL, 내장 IAM 호출자 인증(`roles/run.invoker`)은 IAP나 앱 인증으로 대체.

### 함정
- A4 "응답 후 작업 있음"이면 이 모드는 불일치다. 기본값이 이 모드다.
- 로컬 파일 쓰기는 메모리를 먹어 OOM으로 인스턴스가 죽는다.
- 기본 동시성이 80×vCPU라 CPU 집약 핸들러는 인스턴스 하나에 몰려 지연이 커진다.

---

## 2.2 Cloud Run 서비스 — 인스턴스 기반 과금
- 계열: 컴퓨트-티어1
- 서울 리전: 있음, Tier 2 (§2.1과 같은 출처)

§2.1과 다른 키는 굵게 표시했다. 나머지 값과 출처는 §2.1과 같다.

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | **웹 + 응답 후 백그라운드 작업 + 앱 안 비동기 처리**. 상시 워커는 가능하나 인스턴스가 유휴 시 언제든 종료될 수 있어 min-instances ≥1 필요. 순수 풀 기반 워커는 워커 풀(§2.4)이 더 쌈 | — | https://docs.cloud.google.com/run/docs/configuring/billing-settings · "allocates CPU even outside of request processing, letting you execute short-lived background tasks and other asynchronous processing work after returning responses" · 2026-10-01 |
| CP.request_timeout | 기본 300초, 최대 3,600초 | — | https://docs.cloud.google.com/run/docs/configuring/request-timeout · "can be extended up to 60 minutes (3600 seconds)" · 2026-10-01 |
| CP.long_connection | 웹소켓 지원, 요청 타임아웃(최대 60분)에 끊김 | 과금은 원래 인스턴스 기반 | https://docs.cloud.google.com/run/docs/triggering/websockets · "WebSockets streams are HTTP requests, which are still subject to the request timeout" · 2026-10-01 |
| CP.cpu_outside_request | **있음**: 인스턴스 수명 전체에 CPU. 단, 유휴 인스턴스는 언제든 종료될 수 있음 | 종료 시 SIGTERM 10초 | https://docs.cloud.google.com/run/docs/configuring/billing-settings · "CPU is allocated for the entire container instance lifecycle." / "Idle instances...can be shut down at any time" · 2026-10-01 |
| CP.cold_start | 기본 scale-to-zero 가능(min 0). GPU 서비스도 0으로 줄일 수 있음 | — | https://docs.cloud.google.com/run/docs/configuring/services/gpu · "Services that are set to instance-based billing can still scale to zero." · 2026-10-01 |
| CP.instance_size | 8 vCPU·32 GiB. **GPU: NVIDIA L4(24 GB), RTX PRO 6000 Blackwell(96 GB), 인스턴스당 1개. L4는 최소 4 CPU·16 GiB. 서울(asia-northeast3)은 두 GPU 모두 목록에 없음**(L4: asia-southeast1, asia-south1(초대), europe-west1, europe-west4, us-central1, us-east4) | — | https://docs.cloud.google.com/run/docs/configuring/services/gpu · "You can configure one GPU per Cloud Run instance." · 2026-10-01 |
| CP.request_size | HTTP/1 32 MiB, HTTP/2 무제한 | — | https://docs.cloud.google.com/run/quotas · "Maximum HTTP/1 request size: 32 MiB per request" · 2026-10-01 |
| CP.local_disk | 메모리 FS, 임시 디스크 Preview, 영속 블록 볼륨 없음 | — | https://docs.cloud.google.com/run/docs/container-contract · "It is an in-memory file system" · 2026-10-01 |
| CP.scaling | 리비전당 기본 최대 100 | — | https://docs.cloud.google.com/run/docs/configuring/max-instances · "By default, Cloud Run sets 100 instances for each revision." · 2026-10-01 |
| CP.concurrency | 80 × vCPU(gcloud·Terraform), 최대 1,000 | — | https://docs.cloud.google.com/run/docs/about-concurrency · "maximum concurrency that is 80 times the number of vCPUs" · 2026-10-01 |
| CP.shutdown | SIGTERM → 10초 → SIGKILL | — | https://docs.cloud.google.com/run/docs/container-contract · "indicating the start of a 10 second period before the actual shutdown" · 2026-10-01 |
| CP.deploy | 리비전·트래픽 분할·태그·즉시 롤백 | — | https://docs.cloud.google.com/run/docs/rollouts-rollbacks-traffic-migration · "all requests being processed will continue to completion" · 2026-10-01 |
| CP.availability | 리전 내 멀티 존 기본. GPU 서비스는 존 중복 끄기 가능(더 쌈) | — | https://docs.cloud.google.com/run/docs/zonal-redundancy · "Data and traffic are automatically load balanced across zones within a region." · 2026-10-01 |
| CP.networking | Direct VPC egress, Cloud NAT 고정 IP | — | https://docs.cloud.google.com/run/docs/configuring/static-outbound-ip · "configured with the static IP address" · 2026-10-01 |
| CP.regions | 서울 있음(Tier 2), GPU는 서울 없음 | — | https://docs.cloud.google.com/run/docs/locations · "asia-northeast3 (Seoul, South Korea)" · 2026-10-01 |
| CP.plan_limits | §2.1과 같음 | — | https://docs.cloud.google.com/run/quotas · "Maximum number of services: 1000 per project and region" · 2026-10-01 |
| CP.ops_burden | 낮음(평가), §2.1과 같음 | — | https://cloud.google.com/run/pricing · "requires low operations" · 2026-10-01 |
| CP.cost_floor | **$0**(min 0). 서울 vCPU $0.0000216/초, 메모리 $0.0000024/GiB초, 요청 요금 없음, 인스턴스 수명 전체 과금(최소 1분). min 1(1 vCPU·0.5 GiB) 상시 ≈ **월 $59.9**(무료 등급 전) | 같은 페이지 서울 두 번째 표는 $0.000018/$0.000002 | https://cloud.google.com/run/pricing · "from the time the container is started to when it is terminated, with a minimum of 1 minute" · 2026-10-01 |

### 비용 구조
- 최소 월 고정비: $0(min 0). 실제로 백그라운드 작업이 끝나기 전에 인스턴스가 사라지지 않게 하려면 min ≥1 → 서울 약 $59.9/월(1 vCPU·0.5 GiB).
- 무료 등급: 월 240,000 vCPU초, 450,000 GiB초. "CPU - First 240,000 vCPU-seconds free per month RAM - First 450,000 GiB-seconds free per month" (https://cloud.google.com/run/pricing, 2026-10-01).
- GPU(us-central1): L4 존 중복 없음 $0.0001867/초, 있음 $0.0002909/초(같은 페이지). 서울은 GPU 없음.
- 과금 함정: 요청이 없어도 인스턴스가 살아 있는 동안 전부 과금. 트래픽이 드문 앱은 요청 기반보다 비싸다.

### 교체 계열 정보
- §2.1에서 이 모드로 바꾸는 데 코드 변경은 없다(설정 `--no-cpu-throttling` / billing 설정 변경). A4 불일치를 해결하는 가장 싼 경로.
- 응답 후 작업이 10초 종료 유예 안에 끝난다는 보장이 없으면 결국 큐 + 워커(Cloud Tasks, Pub/Sub + 워커 풀)로 옮긴다.

### 함정
- "인스턴스 기반 = 상시 실행"이 아니다. min 0이면 유휴 후 내려가고 SIGTERM 10초만 준다.
- GPU가 필요한 앱(A6)은 서울에서 이 플랫폼을 쓸 수 없다. 가장 가까운 GPU 리전은 asia-southeast1(싱가포르).

---

## 2.3 Cloud Run Jobs
- 계열: 컴퓨트-티어1 (실행 완료형 작업)
- 서울 리전: 있음 (Cloud Run 리전 목록, Tier 2)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | 정기 작업·배치 전용. 포트를 열면 안 됨. 일정 실행은 Cloud Scheduler(unix-cron) | 웹·장시간 연결 불가 | https://docs.cloud.google.com/run/docs/execute/jobs-on-schedule · "execute Cloud Run jobs on a schedule using Cloud Scheduler" · 2026-10-01 |
| CP.request_timeout | 태스크 기본 10분, 최대 **168시간(7일)**, GPU 태스크 1시간. 재시도마다 적용 | — | https://docs.cloud.google.com/run/docs/configuring/task-timeout · "By default, each task runs for a maximum of 10 minutes" / "up to 168 hours (7 days). For tasks using GPUs, the maximum available timeout is 1 hour." · 2026-10-01 |
| CP.long_connection | 해당 없음 | — | — |
| CP.cpu_outside_request | 있음(실행 중 항상 CPU) | — | https://cloud.google.com/run/pricing · "Cloud Run jobs are billed at the Instance-based billing rate, for the entire lifetime of any instance started" · 2026-10-01 |
| CP.cold_start | 실행마다 컨테이너 기동(상시 인스턴스 없음) | — | https://cloud.google.com/run/pricing · "for the entire lifetime of any instance started, with a minimum of 1 minute" · 2026-10-01 |
| CP.instance_size | 8 vCPU·32 GiB(서비스와 같은 할당량 표), GPU 가능하나 서울 없음 | — | https://docs.cloud.google.com/run/quotas · "The maximum amount of vCPU you can configure is 8 vCPU." · 2026-10-01 |
| CP.request_size | 해당 없음 | — | — |
| CP.local_disk | 메모리 FS(서비스와 같음) | — | https://docs.cloud.google.com/run/docs/container-contract · "It is an in-memory file system" · 2026-10-01 |
| CP.scaling | 작업당 태스크 최대 10,000, 재시도 최대 10, 실행 중 실행 1,000. 병렬도는 리전별(콘솔 표시) | — | https://docs.cloud.google.com/run/quotas · "Maximum number of tasks in a single job: 10,000" · 2026-10-01 |
| CP.concurrency | 해당 없음(태스크 단위) | — | — |
| CP.shutdown | SIGTERM → 10초 → SIGKILL | — | https://docs.cloud.google.com/run/docs/container-contract · "indicating the start of a 10 second period before the actual shutdown" · 2026-10-01 |
| CP.deploy | 작업 정의 갱신(트래픽 개념 없음) | — | 미확인 |
| CP.availability | 존 중복 여부 미확인 | — | 미확인 |
| CP.networking | Direct VPC egress(태스크당 IP 1개, 종료 후 7분 유지). **1시간 넘는 작업은 연결이 끊길 수 있음** | — | https://docs.cloud.google.com/run/docs/configuring/vpc-direct-vpc · "Cloud Run jobs that run for more than 1 hour might experience connection breaks" · 2026-10-01 |
| CP.regions | 서울 있음 | — | https://docs.cloud.google.com/run/docs/locations · "asia-northeast3 (Seoul, South Korea)" · 2026-10-01 |
| CP.plan_limits | 프로젝트·리전당 작업 1,000개 | — | https://docs.cloud.google.com/run/quotas · "Maximum number of tasks in a single job: 10,000" · 2026-10-01 |
| CP.ops_burden | 낮음(평가). 중복 실행 방지(B3)는 Scheduler 재시도·작업 멱등성으로 직접 | — | — |
| CP.cost_floor | $0. 서울 vCPU $0.0000216/초, 메모리 $0.0000024/GiB초(인스턴스 기반 요율, 최소 1분). "Delayed Jobs" SKU 서울 $0.00001512 / $0.00000168(동적 가격) | — | https://cloud.google.com/run/pricing · "with a minimum of 1 minute" · 2026-10-01 |

### 비용 구조
실행 시간만 과금, 최소 1분. 무료 등급은 인스턴스 기반과 같음. Cloud Scheduler 요금은 별도([03](03-cache-queue-scheduler-realtime-storage.md)).

### 교체 계열 정보
- 티어 0 크론(Vercel Cron 등 HTTP 호출)에서 올 때: 핸들러를 "실행 후 종료하는 프로세스" 엔트리포인트로 분리. `CLOUD_RUN_TASK_INDEX`·`CLOUD_RUN_TASK_COUNT` 환경변수로 분할(인용 미확인).
- 티어 2로 갈 때: Kubernetes CronJob/Job으로 1:1 대응.

### 함정
- 앱 서버 안의 `node-cron`·APScheduler(B3)를 그대로 두고 서비스 인스턴스를 늘리면 중복 실행된다. Jobs로 분리하는 것이 처방.

---

## 2.4 Cloud Run 워커 풀
- 계열: 컴퓨트-티어1 (상시 풀 기반 워커)
- 서울 리전: 있음(Cloud Run 리전). 워커 풀 전용 리전 제한은 미확인
- 상태: **GA(2026-04-14)** (https://docs.cloud.google.com/run/docs/release-notes · "Support for worker pools is in General Availability (GA)." · 2026-10-01)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | 상시 백그라운드 워커(Pub/Sub, Kafka 등 풀 기반). **URL·LB 엔드포인트 없음** → 웹 불가 | — | https://docs.cloud.google.com/run/docs/deploy-worker-pools · "worker pools do not have a load balanced endpoint/URL and do not support autoscaling" · 2026-10-01 |
| CP.request_timeout | 해당 없음(요청 없음) | — | — |
| CP.long_connection | 아웃바운드 장시간 연결은 가능, 인바운드 공개 연결 없음. Direct VPC ingress로 인스턴스별 사설 IP(2026-02-05부터) | — | https://docs.cloud.google.com/run/docs/release-notes · 2026-10-01 (인용 미확인) |
| CP.cpu_outside_request | 있음(항상 활성 과금) | — | https://docs.cloud.google.com/run/docs/configuring/workerpools/manual-scaling · "all the instances that you requested are billed as active instances, even if they happen to be idle" · 2026-10-01 |
| CP.cold_start | 수동 인스턴스 수. 0으로 둘 수 있는지 미확인 | — | 미확인 |
| CP.instance_size | 미확인(서비스 한도와 같은지 확인 못 함). GPU L4·RTX PRO 6000 지원, 서울 없음 | — | https://docs.cloud.google.com/run/docs/release-notes · 2026-10-01 |
| CP.request_size | 해당 없음 | — | — |
| CP.local_disk | 메모리 FS | — | https://docs.cloud.google.com/run/docs/container-contract · "It is an in-memory file system" · 2026-10-01 |
| CP.scaling | **오토스케일 없음**(수동). 외부 지표(CREMA, Prometheus, Pub/Sub)로 별도 구성 시에만 | 큐 길이 기반 확장(QU.consumer_scaling)은 직접 | https://docs.cloud.google.com/run/docs/deploy-worker-pools · "do not support autoscaling" · 2026-10-01 |
| CP.concurrency | 해당 없음 | — | — |
| CP.shutdown | SIGTERM → 10초 → SIGKILL(서비스·작업·워커 풀 공통) | — | https://docs.cloud.google.com/run/docs/container-contract · "indicating the start of a 10 second period before the actual shutdown" · 2026-10-01 |
| CP.deploy | 리비전 + 인스턴스 분할(instance split)·롤백 | — | https://docs.cloud.google.com/run/docs/deploy-worker-pools · "instance splits and rollbacks" · 2026-10-01 |
| CP.availability | 존 중복 미확인 | — | 미확인 |
| CP.networking | Direct VPC egress·ingress | — | https://docs.cloud.google.com/run/docs/release-notes · 2026-10-01 (인용 미확인) |
| CP.regions | 서울: Cloud Run 리전이므로 있음으로 보되 워커 풀 가격표 서울 단가로 확인 | — | https://cloud.google.com/run/pricing (서울 워커 풀 단가 존재) · 2026-10-01 |
| CP.plan_limits | 프로젝트·리전당 워커 풀 1,000개 | — | https://docs.cloud.google.com/run/quotas · 2026-10-01 (인용 미확인) |
| CP.ops_burden | 낮음(평가), 단 확장 로직은 직접 | — | — |
| CP.cost_floor | 서울 vCPU $0.000013493/초, 메모리 $0.000001482/GiB초. 1 vCPU·0.5 GiB 1개 상시 ≈ **월 $37.4** | 무료 등급 월 384,204 vCPU초, 728,744 GiB초 | https://cloud.google.com/run/pricing · "CPU - First 384,204 vCPU-seconds free per month" · 2026-10-01 |

### 비용 구조
인스턴스 수 × 상시 요율. 같은 상시 1 vCPU를 인스턴스 기반 서비스로 돌리는 것보다 약 37% 싸다(서울 $0.0000216 대비 $0.000013493).

### 교체 계열 정보
- 티어 0에서 올 때: 상시 워커가 없던 플랫폼(Vercel 등)에서 큐 소비 코드를 별도 엔트리포인트로 분리. HTTP 서버 불필요.
- 티어 2로 갈 때: 레플리카 수가 고정된 Deployment(+ KEDA)로 대응.

### 함정
- 오토스케일이 없으므로 D3(폭증)가 있는 큐 소비에는 외부 스케일러가 필요하다.

---

## 2.5 Cloud Run functions (Cloud Functions 2세대)
- 계열: 컴퓨트-티어1 (함수, 내부적으로 Cloud Run 서비스)
- 서울 리전: 있음(Cloud Run 리전과 같음, Tier 2)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | HTTP 함수, 이벤트 함수(Eventarc). 상시 워커 불가 | — | https://docs.cloud.google.com/run/docs/functions/comparison · "a Cloud Run service that is deployed from source code" · 2026-10-01 |
| CP.request_timeout | HTTP 최대 60분, **이벤트 함수 최대 9분(540초)** | — | https://docs.cloud.google.com/run/docs/functions/comparison · "Up to 9 minutes for event-driven functions created with the Cloud Functions v2 API" / https://docs.cloud.google.com/functions/quotas · "540 seconds for event-driven functions" · 2026-10-01 |
| CP.long_connection | Cloud Run 서비스와 같은 규칙(요청 타임아웃까지) | — | https://docs.cloud.google.com/run/docs/triggering/websockets · "still subject to the request timeout" · 2026-10-01 |
| CP.cpu_outside_request | 기본 요청 기반(없음). Cloud Run 서비스이므로 과금 설정 변경 가능 | — | https://docs.cloud.google.com/run/docs/configuring/billing-settings · "CPU is only allocated during request processing." · 2026-10-01 |
| CP.cold_start | scale-to-zero, min-instances 설정 가능 | — | https://docs.cloud.google.com/run/docs/configuring/min-instances · "Minimum instances can be restarted at any time." · 2026-10-01 |
| CP.instance_size | 미확인: 비교 페이지 "Up to 16 GiB RAM with 4 vCPU", functions 할당량 페이지 32 GiB로 불일치 | — | https://docs.cloud.google.com/run/docs/functions/comparison · 2026-10-01 |
| CP.request_size | 요청 32 MB, 응답 32 MB(비스트리밍)·10 MB(스트리밍), Eventarc 이벤트 512 KB | — | https://docs.cloud.google.com/functions/quotas · "10MB for streaming responses. 32MB for non-streaming responses" · 2026-10-01 |
| CP.local_disk | 메모리 FS | — | https://docs.cloud.google.com/run/docs/container-contract · "It is an in-memory file system" · 2026-10-01 |
| CP.scaling | HTTP 기본 최대 100, 1,000까지. Cloud Run 서비스 할당량(리전당 1,000) 공유 | — | https://docs.cloud.google.com/functions/quotas · 2026-10-01 (인용 미확인) |
| CP.concurrency | 인스턴스당 최대 1,000 | 기본값 미확인 | https://docs.cloud.google.com/run/docs/functions/comparison · "Up to 1000 concurrent requests per function instance" · 2026-10-01 |
| CP.shutdown | SIGTERM → 10초 | — | https://docs.cloud.google.com/run/docs/container-contract · "10 second period" · 2026-10-01 |
| CP.deploy | Cloud Run 리비전·트래픽 분할 | — | https://docs.cloud.google.com/run/docs/functions/comparison · "a Cloud Run service that is deployed from source code" · 2026-10-01 |
| CP.availability | 리전 내 멀티 존(Cloud Run과 같음) | — | https://docs.cloud.google.com/run/docs/zonal-redundancy · "automatically load balanced across zones within a region" · 2026-10-01 |
| CP.networking | Cloud Run과 같음(Direct VPC egress, Cloud NAT) | — | https://docs.cloud.google.com/run/docs/configuring/static-outbound-ip · 2026-10-01 |
| CP.regions | 서울 있음 | — | https://docs.cloud.google.com/run/docs/locations · "asia-northeast3 (Seoul, South Korea)" · 2026-10-01 |
| CP.plan_limits | 이벤트 9분 상한, 서비스 할당량 공유 | — | https://docs.cloud.google.com/functions/quotas · "540 seconds for event-driven functions" · 2026-10-01 |
| CP.ops_burden | 가장 낮음(평가): Dockerfile도 없음 | — | — |
| CP.cost_floor | $0 + **배포마다 Cloud Build·Artifact Registry 요금**(무료 등급 안이어도) | — | https://cloud.google.com/run/pricing · "you will incur charges for deploying your functions, even when your use of Cloud Run falls within the free tier" · 2026-10-01 |

### 비용 구조
Cloud Run 요청 기반 요율 + 빌드·레지스트리·Eventarc.

### 교체 계열 정보
- Firebase Functions 2세대(티어 0)와 같은 런타임이다. Firebase에서 올 때는 트리거 선언만 바뀐다.
- Cloud Run 서비스로 갈 때: 함수 프레임워크(`functions-framework`) 엔트리를 일반 HTTP 서버로 바꾸고 Dockerfile 추가. 이벤트 함수는 Eventarc → Cloud Run 서비스 트리거로 대응.

### 함정
- 이벤트 함수 9분 상한은 HTTP 60분과 다르다. 긴 이벤트 처리는 Jobs나 서비스로.

---

## 3.1 ECS on Fargate — 일반 서비스 (ALB)
- 계열: 컴퓨트-티어1
- 서울 리전: 있음 (https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate-Regions.html · "Asia Pacific (Seoul) \| ap-northeast-2" · 2026-10-01)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | 웹(REPLICA 서비스 + ALB), 상시 워커(LB 없는 서비스), 정기 작업(EventBridge Scheduler → RunTask), 장시간 연결. DAEMON 전략은 불가 | — | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs_service-options.html · "Fargate tasks do not support the `DAEMON` scheduling strategy." / https://docs.aws.amazon.com/AmazonECS/latest/developerguide/tasks-scheduled-eventbridge-scheduler.html · "Rate-based ... Cron-based ... One-time schedules" · 2026-10-01 |
| CP.request_timeout | Fargate 자체 상한 없음(명시 문구는 미확인). 실질 상한은 **ALB 유휴 타임아웃 기본 60초**(1~4,000초) | 앱 keep-alive는 ALB 유휴보다 길게 | https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-load-balancer-attributes.html · "By default, Elastic Load Balancing sets the idle timeout value for your load balancer to 60 seconds." · 2026-10-01 |
| CP.long_connection | 웹소켓·HTTP/2 ALB 기본 지원. 데이터가 오가는 한 지속, 유휴 타임아웃 넘게 조용하면 끊김. 웹소켓은 본래 고정(sticky) | — | https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-listeners.html · "Application Load Balancers provide native support for WebSockets." · 2026-10-01 |
| CP.cpu_outside_request | 있음(태스크가 떠 있는 동안 항상 CPU, 초 단위 과금) | 최소 1분 | https://aws.amazon.com/fargate/pricing/ · "Pricing is calculated per second with a 1-minute minimum." · 2026-10-01 |
| CP.cold_start | scale-to-zero 없음(desired ≥1 유지가 일반적). 태스크 기동 시간 수치 미확인. SOCI 지연 로딩으로 이미지 풀 단축 | SOCI는 플랫폼 1.4.0 + ECR | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-tasks-services.html · "With SOCI, containers only spend a few seconds on the image pull before they can start" · 2026-10-01 |
| CP.instance_size | 0.25~**32 vCPU**. 16 vCPU는 32~120 GB, 32 vCPU는 60/120/244 GB(Linux, 플랫폼 1.4.0+). **GPU 불가** | — | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-tasks-services.html · "32768 (32 vCPU) This option requires Linux platform `1.4.0` or later. \| 60 GB, 120 GB, 244 GB" / https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definition_parameters.html · "`gpu` This parameter isn't supported for containers that are hosted on Fargate." · 2026-10-01 |
| CP.request_size | ALB 헤더 64K, 요청 줄 16K. 본문 한도 미확인 | §1.3 | https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-limits.html · "Entire request header \| 64 K \| No" · 2026-10-01 |
| CP.local_disk | 임시 스토리지 최소 20 GiB, 최대 200 GiB(태스크 종료 시 소멸). 영속: **EFS**(여러 태스크 공유). EBS는 태스크당 새 볼륨 1개, 서비스 태스크면 종료 시 **삭제** | — | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-task-storage.html · "receive a minimum of 20 GiB of ephemeral storage. The total amount of ephemeral storage can be increased, up to a maximum of 200 GiB." / https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ebs-volumes.html · "Volumes that are attached to tasks that are managed by a service aren't preserved and are always deleted upon task termination." · 2026-10-01 |
| CP.scaling | Application Auto Scaling(대상 추적: CPU, 메모리, ALB 요청 수). 서비스당 분당 500 태스크 기동(신규 리전 125). 배포 중엔 축소 중지 | Fargate 온디맨드 기동 버스트 100, 지속 초당 20 | https://docs.aws.amazon.com/general/latest/gr/ecs-service.html · "The maximum number of tasks that can be provisioned per service per minute on Fargate" · 2026-10-01 |
| CP.concurrency | 앱이 결정(ECS 차원 설정 없음) | ALB HTTP/2 연결당 128 스트림 | https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-listeners.html · "You can send up to 128 requests in parallel using one HTTP/2 connection." · 2026-10-01 |
| CP.shutdown | SIGTERM 후 `stopTimeout` 기본 **30초**, 최대 **120초**. 그 전에 ALB 등록 해제 지연 기본 300초 동안 새 연결 차단·진행 연결 유지 | — | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definition_parameters.html · "If the parameter isn't specified, then the default value of 30 seconds is used. The maximum value is 120 seconds." · 2026-10-01 |
| CP.deploy | 롤링(기본), 블루/그린, 선형, 카나리(ECS 컨트롤러, ALB·NLB·Service Connect 필요). **배포 서킷 브레이커 + 자동 롤백**(롤링 전용, 실패 임계 기본 desired의 50%, 3~200) | — | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs_service-options.html · "Rolling updates are the default deployment strategy for services" / https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-circuit-breaker.html · "The deployment circuit breaker is only supported for Amazon ECS services that use the rolling update (`ECS`) deployment controller." · 2026-10-01 |
| CP.availability | 여러 AZ 서브넷에 최선 노력 분산(배치 전략 미지원). ALB는 교차 영역 항상 켜짐. 리전 장애 대비는 없음 | 태스크 ≥2, 서브넷 ≥2 AZ | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-placement.html · "Fargate will try its best to spread tasks across accessible Availability Zones." · 2026-10-01 |
| CP.networking | awsvpc 전용(태스크마다 ENI·사설 IP) → 같은 VPC의 RDS에 사설 연결. 사설 서브넷 + NAT Gateway(탄력적 IP)로 고정 출구 IP. 사설 서브넷 이미지 풀은 NAT 또는 ECR VPC 엔드포인트 | — | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-tasks-services.html · "For a Fargate task in a private subnet to pull container images, you need a NAT gateway in the subnet" · 2026-10-01 |
| CP.regions | 서울 있음 | — | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate-Regions.html · "Asia Pacific (Seoul) \| ap-northeast-2" · 2026-10-01 |
| CP.plan_limits | 서비스당 태스크 5,000, 클러스터당 서비스 5,000. **Fargate 온디맨드 vCPU 기본 할당량 6**(조정 가능, 신규 계정은 더 낮을 수 있음) | — | https://docs.aws.amazon.com/general/latest/gr/ecs-service.html · "Fargate On-Demand vCPU resource count \| Each supported Region: 6" · 2026-10-01 |
| CP.ops_burden | 중간(평가): VPC·서브넷·NAT, ALB·대상 그룹·리스너·인증서, 태스크 정의, 오토스케일 정책, IAM 역할 2개, 로그 그룹을 직접 구성. 노드·OS 패치는 없음 | — | — |
| CP.cost_floor | 서울 vCPU $0.04656/시간, 메모리 $0.00511/GB-시간(ARM $0.03725 / $0.00409), 임시 스토리지 20 GiB 초과분 $0.000127/GB-시간. 0.25 vCPU·0.5 GB 1개 ≈ 월 $10.4, 1 vCPU·2 GB ≈ 월 $41.4. **+ ALB 월 $16.43 + LCU** + 공인 IPv4 $3.65/개. 사설 서브넷이면 NAT 월 $43.07/AZ | — | [PL] AmazonECS ap-northeast-2 · "AWS Fargate - vCPU - Asia Pacific (Seoul)" 0.04656 / "AWS Fargate - Memory - Asia Pacific (Seoul)" 0.00511 · 2026-10-01 |

### 비용 구조
- 최소 월 고정비(서울): 태스크 1개(0.25 vCPU·0.5 GB) $10.4 + ALB $16.4 ≈ **$27** + 공인 IPv4. 멀티 AZ로 태스크 2개면 약 $37. 사설 서브넷 + NAT 1개면 +$43(AZ마다 두면 ×AZ 수).
- 변동: 태스크 vCPU·GB 초, ALB LCU($0.008/LCU-시간), NAT 처리 $0.059/GB.
- 무료 등급: 없음.
- 함정: NAT 1개를 여러 AZ가 공유하면 그 AZ 장애 때 전부 인터넷이 끊긴다(§1.3). 그래서 AZ마다 두면 고정비가 AZ 수만큼 늘어난다.

### 교체 계열 정보
- 티어 0에서 올 때: Dockerfile, ECR 푸시, 태스크 정의(포트·헬스체크·환경변수·시크릿 ARN), 서비스·ALB·대상 그룹. **헬스체크 계약**: ALB 대상 그룹 경로(기본 `/`) 200 응답. **SIGTERM**: 30초(최대 120초) 안에 종료, ALB 등록 해제 지연(300초)과 맞추려면 앱에서 SIGTERM 후 잠시 요청을 계속 받거나 해제 지연을 줄인다. **keep-alive**: 앱 keep-alive > ALB 유휴 60초(안 그러면 502).
- 티어 2(EKS)로 갈 때: 같은 이미지. 태스크 정의 → Deployment, 서비스 오토스케일 → HPA, ALB → AWS Load Balancer Controller Ingress. IAM 태스크 역할 → Pod Identity. 서킷 브레이커 → `progressDeadlineSeconds` + 수동/도구 롤백.

### 함정
- ALB 유휴 60초 기본값은 Vercel·Cloud Run(300초)보다 짧다. 티어 0에서 1~4분 걸리던 핸들러가 이전 후 504가 된다.
- 신규 계정 Fargate vCPU 할당량 6은 1 vCPU 태스크 6개에서 막힌다. 롤링 배포는 최대 200%로 잠시 두 배를 띄우므로 실제로는 3개부터 막힐 수 있다.

---

## 3.2 ECS on Fargate — Express Mode
- 계열: 컴퓨트-티어1
- 서울 리전: 있음(ECS·Fargate가 있는 모든 리전) (https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-overview.html · "available in all AWS Regions where Amazon ECS and Fargate are supported." · 2026-10-01)

이미지와 IAM 역할 2개로 Fargate 서비스, ALB(HTTPS), 대상 그룹, 보안 그룹, 오토스케일, 로그 그룹, 롤백 알람, ACM 인증서, `*.ecs.<region>.on.aws` URL을 한 번에 만든다. 런타임 능력은 §3.1과 같고 기본값과 바꿀 수 없는 설정이 다르다.

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | **HTTP 웹·API 전용**(상태 없는 앱). 워커·정기 작업은 일반 ECS로 | — | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-overview.html · "Web applications and APIs - Stateless containerized applications that serve HTTP requests" · 2026-10-01 |
| CP.request_timeout | ALB 유휴 60초 기본(Express가 바꾸는지는 미확인) | — | https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-load-balancer-attributes.html · "sets the idle timeout value for your load balancer to 60 seconds" · 2026-10-01 |
| CP.long_connection | ALB 웹소켓 지원 | — | https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-listeners.html · "native support for WebSockets" · 2026-10-01 |
| CP.cpu_outside_request | 있음 | — | https://aws.amazon.com/fargate/pricing/ · "Pricing is calculated per second with a 1-minute minimum." · 2026-10-01 |
| CP.cold_start | **최소 1 태스크 상시**, scale-to-zero 여부 미확인 | — | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-work.html · "desiredMinTaskCount: 1 - Minimum number of tasks to maintain" · 2026-10-01 |
| CP.instance_size | 기본 1 vCPU·2 GB(x86_64/ARM64), 포트 80. 사용자 태스크 정의 허용(2026-07부터). GPU 불가 | — | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-work.html · "cpu: 1024 - 1 vCPU unit allocated to the task" · 2026-10-01 |
| CP.request_size | ALB와 같음, 본문 미확인 | — | https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-limits.html · "Entire request header \| 64 K \| No" · 2026-10-01 |
| CP.local_disk | 임시 20 GiB(Fargate 기본). 영속 볼륨을 Express에서 지정할 수 있는지 미확인 | 상태 없는 앱 전제 | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-task-storage.html · "receive a minimum of 20 GiB of ephemeral storage" · 2026-10-01 |
| CP.scaling | 기본 min 1, max 20, CPU 60% 목표. 지표 CPU·메모리·대상당 요청 수 | — | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-work.html · "autoScalingTargetValue: 60 - Target CPU utilization percentage for scaling" / "desiredMaxTaskCount: 20" · 2026-10-01 |
| CP.concurrency | 앱이 결정 | — | — |
| CP.shutdown | stopTimeout 30초. 등록 해제 지연은 ALB 기본 300초로 보이나 Express 전용 확인 미확인 | — | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-work.html · "stopTimeout: 30 seconds - Time between SIGTERM and SIGKILL signals." · 2026-10-01 |
| CP.deploy | **카나리 고정** + 5XX 롤백 알람. 배포 전략 변경 불가. 헬스체크 30초 간격, 유예 300초 | — | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-work.html · "Note that deployment strategy can not be updated on Express Mode services." · 2026-10-01 |
| CP.availability | AZ 재균형 켜짐, 운영은 3 AZ 권장. 공용 서브넷 2 AZ 이상 필요 | — | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-best-practices.html · "we recommend running in three availability zones to follow availability best practices." · 2026-10-01 |
| CP.networking | 기본: 기본 VPC **공용 서브넷 + 공인 IP**. 사설 서브넷을 주면 내부 ALB가 되고 NAT는 직접 구성. VPC의 첫 Express 서비스가 ALB 서브넷을 고정. VPC당 ALB 하나를 최대 25개 서비스가 공유 | — | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-work.html · "This is disabled if you provide a private subnet, and you are then responsible for configuring a NAT gateway" / "Up to 25 Express Mode services in the same VPC can share an Application Load Balancer." · 2026-10-01 |
| CP.regions | 서울 있음 | — | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-overview.html · "available in all AWS Regions where Amazon ECS and Fargate are supported." · 2026-10-01 |
| CP.plan_limits | Fargate vCPU 할당량 6(§3.1). 로드밸런서 구성·배포 전략은 Express로 갱신 불가 | — | https://docs.aws.amazon.com/general/latest/gr/ecs-service.html · "Fargate On-Demand vCPU resource count \| Each supported Region: 6" · 2026-10-01 |
| CP.ops_burden | 낮음~중간(평가): 생성은 한 번 호출. 자원은 계정에 남아 이후 세부 조정은 일반 ECS와 같다 | — | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-overview.html · "There is no additional charge for using an Amazon ECS Express Mode service." · 2026-10-01 |
| CP.cost_floor | Express 추가 요금 없음. 기본 1 vCPU·2 GB 1개 월 $41.4 + ALB $16.4 ≈ **월 $58** + 공인 IPv4(태스크·ALB) + LCU + 로그 | — | [PL] AmazonECS·AWSELB ap-northeast-2 · 2026-10-01 |

### 비용 구조
위 표. ALB는 VPC의 Express 서비스 25개까지 공유하므로 서비스가 늘면 서비스당 ALB 비용이 내려간다. CloudWatch 로그 그룹이 만료 없이 남아 보관 요금이 계속 쌓인다.

### 교체 계열 정보
- App Runner의 공식 이전 대상이다(§3.4). 티어 0에서 올 때 산출물은 이미지 + 포트 + 헬스체크 경로뿐이라 가장 짧다.
- 일반 ECS(§3.1)로 넘어갈 때 자원이 이미 계정에 있으므로 재생성 없이 서비스 설정을 직접 바꾼다.

### 함정
- 기본 배치가 공용 서브넷 + 공인 IP다. DB를 사설로 두려면 사설 서브넷 + NAT를 직접 붙여야 하고 그 순간 NAT 고정비가 생긴다.
- 로그 그룹 "never expire" 기본값 (https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-best-practices.html · "CloudWatch Log Groups created by Express Mode are configured to never expire and are retained when the Express Mode service is deleted." · 2026-10-01).

---

## 3.3 ECS on Fargate — Fargate Spot
- 계열: 컴퓨트-티어1
- 서울 리전: 미확인(Spot 전용 리전 표를 찾지 못함)

§3.1과 런타임 능력이 같고 중단·용량·가격만 다르다.

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | 중단 가능한 워커·배치에 적합. 웹은 온디맨드 base와 섞을 때만 | — | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-capacity-providers.html · "A service with only one task is interrupted until capacity is available." · 2026-10-01 |
| CP.request_timeout | §3.1과 같음(ALB 60초) | — | https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-load-balancer-attributes.html · "60 seconds" · 2026-10-01 |
| CP.long_connection | 지원하나 중단 시 끊김 | — | 같은 출처(§3.1) |
| CP.cpu_outside_request | 있음 | — | https://aws.amazon.com/fargate/pricing/ · "Pricing is calculated per second with a 1-minute minimum." · 2026-10-01 |
| CP.cold_start | scale-to-zero 없음. 용량 부족 시 태스크가 뜨지 않을 수 있음 | — | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-capacity-providers.html · "Fargate doesn't replace Spot capacity with on-demand capacity." · 2026-10-01 |
| CP.instance_size | §3.1과 같음. x86_64(플랫폼 1.3.0+), ARM64(1.4.0+). Windows 미지원 여부 명시 미확인 | — | https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_CapacityProviderStrategyItem.html · "`FARGATE_SPOT` supports Linux tasks with the ARM64 architecture on platform version 1.4.0 or later." · 2026-10-01 |
| CP.request_size | §3.1과 같음 | — | §1.3 |
| CP.local_disk | §3.1과 같음 | — | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-task-storage.html · "minimum of 20 GiB" · 2026-10-01 |
| CP.scaling | 캐퍼시티 프로바이더 전략(base/weight)으로 온디맨드와 혼합 | — | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-capacity-providers.html · 2026-10-01 (인용 미확인) |
| CP.concurrency | 앱 | — | — |
| CP.shutdown | **2분 경고**(EventBridge 이벤트 + SIGTERM). stopTimeout ≤120초 지정 가능 | — | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-capacity-providers.html · "The warning is sent as a task state change event to Amazon EventBridge and as a SIGTERM signal to the running task." · 2026-10-01 |
| CP.deploy | §3.1과 같음 | — | — |
| CP.availability | 단일 태스크 서비스는 용량이 돌아올 때까지 중단. 온디맨드로 자동 대체 안 됨 | — | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-capacity-providers.html · "Fargate doesn't replace Spot capacity with on-demand capacity." · 2026-10-01 |
| CP.networking | §3.1과 같음 | — | — |
| CP.regions | 서울 미확인 | — | 미확인 |
| CP.plan_limits | Fargate Spot vCPU 기본 할당량 6 | — | https://docs.aws.amazon.com/general/latest/gr/ecs-service.html · "Fargate Spot vCPU resource count \| Each supported Region: 6" · 2026-10-01 |
| CP.ops_burden | §3.1 + 중단 대비 설계(평가) | — | — |
| CP.cost_floor | 온디맨드 대비 최대 70% 할인. 서울 Spot 단가 미확인(Price List 오퍼 파일에 없음, 변동가) | — | https://aws.amazon.com/fargate/pricing/ · "at up to a 70% discount off the regular Fargate price." · 2026-10-01 |

### 비용 구조
변동 Spot 가격. ALB·NAT 고정비는 §3.1과 같다.

### 교체 계열 정보
SIGTERM 2분 안에 작업 체크포인트·큐 반납 처리가 필요하다. 코드 변경은 그 처리뿐이다.

### 함정
- 태스크 1개 서비스를 Spot에 두면 F1(중단 허용 짧음)과 바로 불일치.
- EKS Fargate에는 Spot이 없다(§6.4).

---

## 3.4 AWS App Runner — 신규 고객 불가
- 계열: 컴퓨트-티어1
- 서울 리전: **없음** (https://docs.aws.amazon.com/general/latest/gr/apprunner.html 엔드포인트 표에 ap-northeast-2 없음 · 2026-10-01. Price List `AWSAppRunner` region_index에도 ap-northeast-2 없음 [PL])
- 상태: **신규 고객에게 닫힘**, 새 기능 계획 없음. 이전 대상으로 ECS Express Mode 권장 (https://docs.aws.amazon.com/apprunner/latest/dg/apprunner-availability-change.html · "we decided to close AWS App Runner to new customers." / "we do not plan to introduce new features." · 2026-10-01). 마감일은 API 참조 기준 2026-03-31 (https://docs.aws.amazon.com/apprunner/latest/api/API_CreateAutoScalingConfiguration.html · "will no longer be open to new customers starting March 31, 2026" · 2026-10-01). 이 저장소 considerations/README의 "2026-04-30"과 다르다.

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | 웹 전용, 상태 없는 앱. 워커·정기 작업 없음 | — | https://docs.aws.amazon.com/apprunner/latest/dg/develop.html · "Currently App Runner doesn't support a stateful app." · 2026-10-01 |
| CP.request_timeout | **120초**(본문 읽기·응답 쓰기 포함) | — | https://docs.aws.amazon.com/apprunner/latest/dg/develop.html · "There is a total of 120 seconds request timeout limit on the HTTP requests." · 2026-10-01 |
| CP.long_connection | HTTP 1.0/1.1만. 웹소켓 미지원(공식 로드맵 이슈 "Closed as not planned") | — | https://docs.aws.amazon.com/apprunner/latest/dg/develop.html · "App Runner provides support for HTTP 1.0 and HTTP 1.1 to the container instances." / https://github.com/aws/apprunner-roadmap/issues/13 · 2026-10-01 |
| CP.cpu_outside_request | 유휴(프로비저닝) 인스턴스는 메모리만 과금, CPU는 활성일 때만 → 요청 밖 CPU를 보장하지 않음 | — | https://docs.aws.amazon.com/apprunner/latest/dg/manage-autoscaling.html · "You pay for the memory usage of all the provisioned instances. You pay for the CPU usage of only the active subset." · 2026-10-01 |
| CP.cold_start | MinSize 기본 1(1~25), scale-to-zero 없음 | — | https://docs.aws.amazon.com/apprunner/latest/api/API_CreateAutoScalingConfiguration.html · "Default: `1` ... Valid Range: Minimum value of 1. Maximum value of 25." · 2026-10-01 |
| CP.instance_size | 0.25 vCPU·0.5 GB ~ 4 vCPU·12 GB, GPU 없음 | — | https://docs.aws.amazon.com/apprunner/latest/dg/architecture.html · "4 vCPU \| 12 GB" · 2026-10-01 |
| CP.request_size | 미확인 | — | 미확인 |
| CP.local_disk | 임시 3 GB(이미지 포함), 영속 볼륨 없음 | — | https://docs.aws.amazon.com/apprunner/latest/dg/develop.html · "App Runner provides you with 3 GB of ephemeral storage" · 2026-10-01 |
| CP.scaling | MaxSize 기본 25. Fargate 온디맨드 vCPU 할당량을 공유 | — | https://docs.aws.amazon.com/apprunner/latest/api/API_CreateAutoScalingConfiguration.html · "Default: `25`" · 2026-10-01 |
| CP.concurrency | MaxConcurrency 기본 100(1~200) | — | 같은 페이지 · "Default: `100` ... Minimum value of 1. Maximum value of 200." · 2026-10-01 |
| CP.shutdown | 미확인 | — | 미확인 |
| CP.deploy | 자동·수동 배포, 배포 중 프로비저닝 인스턴스 2배 | — | https://docs.aws.amazon.com/apprunner/latest/api/API_CreateAutoScalingConfiguration.html · "App Runner temporarily doubles the number of provisioned instances during deployments" · 2026-10-01 |
| CP.availability | MinSize를 늘리면 더 많은 AZ에 분산 | — | 같은 페이지 · "Configure a higher `MinSize` to increase the spread of your App Runner service over more Availability Zones" · 2026-10-01 |
| CP.networking | 기본 공용 출구. VPC 커넥터를 붙이면 아웃바운드 전체가 VPC로 가고 인터넷은 NAT 필요 | — | https://docs.aws.amazon.com/apprunner/latest/dg/network-vpc.html · "When you connect your service to a VPC, the outbound traffic doesn't have access to the public internet." · 2026-10-01 |
| CP.regions | 서울 없음(11개 리전) | — | https://docs.aws.amazon.com/general/latest/gr/apprunner.html · 2026-10-01 |
| CP.plan_limits | 리전당 서비스 30(조정 가능), VPC 커넥터 10. 신규 고객 생성 불가 | — | https://docs.aws.amazon.com/general/latest/gr/apprunner.html · "Services \| Each supported Region: 30" · 2026-10-01 |
| CP.ops_burden | 낮음(평가), 단 서비스 종료 방향 | — | — |
| CP.cost_floor | (us-east-1 등) 프로비저닝 $0.007/GB-시간, 활성 시 +$0.064/vCPU-시간 + $0.007/GB-시간. 도쿄 $0.081 / $0.009. 서울 해당 없음 | — | https://aws.amazon.com/apprunner/pricing/ · "$0.064 / vCPU-hour" · 2026-10-01 |

### 비용 구조
서울 없음. 신규 구성 후보에서 제외.

### 교체 계열 정보
기존 사용자 → ECS Express Mode(§3.2). AWS가 Route 53 가중치 기반 이전 가이드를 제공한다(availability-change 페이지). 코드 변경은 거의 없고 `apprunner.yaml` 빌드 설정을 Dockerfile로 바꾸는 것이 주된 일이다.

### 함정
- 신규 계정 처방에 App Runner를 넣으면 생성 자체가 실패한다.

---

## 3.5 AWS Lambda — Function URL
- 계열: 컴퓨트-티어1 (함수)
- 서울 리전: 있음 (https://docs.aws.amazon.com/general/latest/gr/lambda-service.html · "Asia Pacific (Seoul) \| ap-northeast-2 \| lambda.ap-northeast-2.amazonaws.com" · 2026-10-01). Function URL·응답 스트리밍의 서울 제공 여부 미확인

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | 짧은 요청·이벤트 핸들러. 상시 워커·장시간 연결 서버 불가. 정기 실행은 EventBridge(문서 미확인) | — | https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html · "Lambda is designed for short-lived compute tasks that do not retain or rely upon state between invocations." · 2026-10-01 |
| CP.request_timeout | 함수 타임아웃 최대 **900초**. Function URL 고유 타임아웃은 문서에서 찾지 못함 → 함수 타임아웃이 상한 | Managed Instances는 비동기·이벤트 소스만 5,400초 | https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html · "900 seconds (15 minutes)." · 2026-10-01 |
| CP.long_connection | 웹소켓 서버 불가(Function URL 문서에 지원 언급 없음 → 미확인). 응답 스트리밍은 Node.js 관리형 런타임만, VPC 안에선 Function URL 스트리밍 불가. **클라이언트가 끊어도 함수는 계속 돌고 과금** | — | https://docs.aws.amazon.com/lambda/latest/dg/configuration-response-streaming.html · "Lambda supports response streaming on Node.js managed runtimes." / "streamed responses are not interrupted or stopped when the invoking client connection is broken. Customers are billed for the full function duration" · 2026-10-01 |
| CP.cpu_outside_request | **없음**: 호출이 끝나면 실행 환경 동결. 미완료 백그라운드 작업은 환경이 재사용될 때에만 이어짐 | — | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html · "Background processes or callbacks that were initiated by your Lambda function and did not complete when the function ended resume if Lambda reuses the execution environment." · 2026-10-01 |
| CP.cold_start | 호출의 1% 미만, 100 ms 미만 ~ 1초 이상. Init 10초 제한. 프로비저닝 동시성(유료), SnapStart(Java 11+, Python 3.12+, .NET 8+; Node.js 없음; 프로비저닝 동시성·EFS·/tmp>512 MB와 함께 불가) | — | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html · "Cold starts typically occur in under 1% of invocations. The duration of a cold start varies from under 100 ms to over 1 second." / https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html · "SnapStart does not support provisioned concurrency, Amazon Elastic File System (Amazon EFS), Amazon S3 Files, or ephemeral storage greater than 512 MB." · 2026-10-01 |
| CP.instance_size | 메모리 128~10,240 MB, 1,769 MB = 1 vCPU. 최대 vCPU 수 미확인. 이미지 10 GB. **GPU 없음** | — | https://docs.aws.amazon.com/lambda/latest/dg/configuration-memory.html · "You can configure memory between 128 MB and 10,240 MB in 1-MB increments. At 1,769 MB, a function has the equivalent of one vCPU" · 2026-10-01 |
| CP.request_size | 동기 요청·응답 각 **6 MB**, 스트리밍 응답 200 MB(6 MB 이후 2 MBps), 비동기 1 MB | — | https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html · "6 MB each for request and response (synchronous) 200 MB for each streamed response (synchronous) 1 MB (asynchronous)" · 2026-10-01 |
| CP.local_disk | /tmp 512 MB~10,240 MB(임시, 동결 동안 유지). EFS 또는 S3 Files 마운트(둘 중 하나) | — | https://docs.aws.amazon.com/lambda/latest/dg/configuration-filesystem.html · "A Lambda function can use either Amazon EFS or Amazon S3 Files, but not both." · 2026-10-01 |
| CP.scaling | 함수당 10초마다 실행 환경 1,000개 추가. 계정 기본 동시 실행 1,000(신규 계정은 더 낮음). 동기 RPS 상한 = 동시성 × 10 | — | https://docs.aws.amazon.com/lambda/latest/dg/scaling-behavior.html · "your concurrency scaling rate is 1,000 execution environment instances every 10 seconds (or 10,000 requests per second every 10 seconds)" · 2026-10-01 |
| CP.concurrency | 실행 환경당 **1 호출** | Managed Instances는 다중 | https://docs.aws.amazon.com/lambda/latest/dg/lambda-managed-instances.html · "one execution environment can run a maximum of one invoke at a time" · 2026-10-01 |
| CP.shutdown | Shutdown 단계: 확장 없음 0 ms, 내부 확장 500 ms, 외부 확장 2,000 ms 후 SIGKILL. 실행 환경은 몇 시간마다 재활용 | 앱 코드에 SIGTERM 유예 없음 | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html · "2,000 ms – A function with one or more registered external extensions" · 2026-10-01 |
| CP.deploy | 버전 + 별칭. 가중치 별칭으로 최대 2개 버전 분할. CodeDeploy(SAM)로 점진 이전·알람 롤백 | — | https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html · "You can point an alias to a maximum of two Lambda function versions." · 2026-10-01 |
| CP.availability | 자동 멀티 AZ | VPC 연결 시 여러 AZ 서브넷 지정 | https://docs.aws.amazon.com/lambda/latest/dg/security-resilience.html · "Lambda runs your function in multiple Availability Zones to ensure that it is available to process events in case of a service interruption in a single zone." · 2026-10-01 |
| CP.networking | 기본 인터넷 가능. VPC에 붙이면 인터넷은 사설 서브넷 + NAT 필요(고정 IP는 NAT의 탄력적 IP). **Function URL은 공용 인터넷 전용** | — | https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc-internet.html · "Connecting a function to a public subnet doesn't give it internet access." / https://docs.aws.amazon.com/lambda/latest/dg/urls-configuration.html · "You can access your function URL through the public Internet only." · 2026-10-01 |
| CP.regions | 서울 있음, SnapStart 서울 포함(뉴질랜드·타이베이 제외), Managed Instances 서울 GA | — | https://docs.aws.amazon.com/general/latest/gr/lambda-service.html · "ap-northeast-2" · 2026-10-01 |
| CP.plan_limits | 환경변수 4 KB, 파일 디스크립터 1,024, 프로세스·스레드 1,024, 레이어 5, zip 50 MB(압축)/250 MB(해제) | — | https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html · "10 GB (maximum uncompressed image size, including all layers)" · 2026-10-01 |
| CP.ops_burden | 낮음(평가): 서버 없음. 남는 일은 동시성 할당량, VPC·NAT, DB 연결(RDS Proxy) | — | — |
| CP.cost_floor | **$0**. 서울 x86 $0.0000166667/GB초(티어 1), ARM $0.0000133334, 요청 $0.20/100만, 프로비저닝 동시성 $0.0000051254/GB초(1 GB × 1 상시 ≈ 월 $13.5) | 무료 월 100만 요청 + 40만 GB초 | [PL] AWSLambda ap-northeast-2 · "AWS Lambda - Total Compute - Asia Pacific (Seoul)-Tier-1" 0.0000166667 / https://aws.amazon.com/lambda/pricing/ · "one million requests and 400,000 GB-seconds per month" · 2026-10-01 |

### 비용 구조
요청 + GB초. Function URL 자체는 추가 요금 없음(별도 단가 행 없음, 인용 미확인). 스트리밍 응답 6 MB 초과분 $0.008/GB(가격 페이지).

### 교체 계열 정보
- 티어 0 함수(Vercel·Netlify)에서 올 때: 핸들러 시그니처 변경(이벤트 객체) 또는 Lambda Web Adapter로 일반 HTTP 서버를 그대로. DB 연결은 핸들러 밖에서 생성하고 RDS Proxy.
- 컨테이너(ECS·Cloud Run)로 갈 때: 핸들러 → HTTP 서버 + Dockerfile, 동시성 1 가정(전역 상태 안전성)이 깨지므로 전역 변수 경쟁을 점검. `context.getRemainingTimeInMillis` 등 Lambda 전용 API 제거.

### 함정
- 동시성이 1이라 요청마다 DB 연결을 열면 DB 연결이 동시 실행 수만큼 늘어난다(C8).
- Lambda Managed Instances(서울 GA)는 다중 동시성·콜드 스타트 없음 대신 기본 3개 인스턴스 상시, EC2 단가 + 15% 관리비로 scale-to-zero가 없다 (https://docs.aws.amazon.com/lambda/latest/dg/lambda-managed-instances.html · "Scales to minimum execution environments configured without traffic." · 2026-10-01).
- 응답 스트리밍은 Python 등에서 기본 지원이 아니다.

---

## 3.6 AWS Lambda — API Gateway 경유 (REST / HTTP / WebSocket API)
- 계열: 컴퓨트-티어1 (함수 + 관리형 진입점)
- 서울 리전: 있음 (API Gateway 서울 단가 [PL] AmazonApiGateway ap-northeast-2 · 2026-10-01)

함수 쪽 능력은 §3.5와 같다. 진입점 한도가 판정을 바꾼다.

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | 웹 API, WebSocket API(연결 관리형). 상시 워커 불가 | — | https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-execution-service-websocket-limits-table.html · 2026-10-01 |
| CP.request_timeout | REST 통합 타임아웃 50 ms~**29초**(리전·사설 API는 상향 가능, 계정 스로틀 감소 가능, 엣지 최적화는 불가). **HTTP API 30초 고정**. REST 응답 스트리밍은 최대 15분(유휴 5분, 엣지 30초) | — | https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html · "You can raise the integration timeout to greater than 29 seconds, but this might require a reduction in your Region-level throttle quota for your account." / https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html · "Maximum integration timeout \| 30 seconds \| No" / https://docs.aws.amazon.com/apigateway/latest/developerguide/response-transfer-mode.html · "You can stream your response for up to 15 minutes." · 2026-10-01 |
| CP.long_connection | WebSocket API: 연결 최대 **2시간**, 유휴 **10분**, 프레임 32 KB, 메시지 128 KB, 통합 타임아웃 29초 | 조정 불가 | https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-execution-service-websocket-limits-table.html · "Connection duration for WebSocket API \| 2 hours \| No" / "Idle Connection Timeout \| 10 minutes \| No" · 2026-10-01 |
| CP.cpu_outside_request | 없음(§3.5) | — | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html · "resume if Lambda reuses the execution environment" · 2026-10-01 |
| CP.cold_start | §3.5와 같음 | — | — |
| CP.instance_size | §3.5와 같음 | — | — |
| CP.request_size | API Gateway 페이로드 REST 10 MB, HTTP API 10 MB(조정 불가). 함수 쪽 6 MB가 더 작으므로 실효 6 MB | — | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html · "Payload size \| 10 MB \| No" · 2026-10-01 |
| CP.local_disk | §3.5와 같음 | — | — |
| CP.scaling | §3.5 + API Gateway 계정 스로틀 기본 10,000 RPS(버스트 5,000) | — | https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html · "API Gateway has a default throttle limit of 10,000 requests per second, whereas Lambda has a default concurrency limit of 1,000." · 2026-10-01 |
| CP.concurrency | 1(§3.5) | — | — |
| CP.shutdown | §3.5와 같음 | — | — |
| CP.deploy | 스테이지 + 카나리 배포(REST, 인용 미확인) + Lambda 별칭 가중치 | — | https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html · "maximum of two Lambda function versions" · 2026-10-01 |
| CP.availability | 리전 서비스, 멀티 AZ(Lambda 쪽 인용) | — | https://docs.aws.amazon.com/lambda/latest/dg/security-resilience.html · "multiple Availability Zones" · 2026-10-01 |
| CP.networking | REST 사설 API·VPC 링크 지원(인용 미확인). 함수 쪽은 §3.5 | — | 미확인 |
| CP.regions | 서울 있음 | — | [PL] AmazonApiGateway ap-northeast-2 · 2026-10-01 |
| CP.plan_limits | REST 유휴 연결 310초, 스로틀 10,000 RPS | — | https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html · "Idle connection timeout \| 310 seconds \| No" · 2026-10-01 |
| CP.ops_burden | 낮음(평가) | — | — |
| CP.cost_floor | $0 + 요청당. 서울 REST $3.50/100만(첫 3.33억), HTTP API $1.23/100만, WebSocket 메시지 $1.14/100만 + 연결 분 $0.285/100만 | — | [PL] AmazonApiGateway ap-northeast-2 · "$1.23/million requests - API Gateway HTTP API (first 300 million)" / "$3.50/million requests - first 333 million requests/month" · 2026-10-01 |

### 비용 구조
Lambda 요금 + API Gateway 요청 요금. 고정비 0.

### 교체 계열 정보
- Function URL(900초)에서 API Gateway로 옮기면 29~30초 상한이 생긴다. 반대로 API Gateway에서 30초 넘는 요청이 필요하면 Function URL, ALB → Lambda, 또는 컨테이너로.
- 웹소켓 앱(socket.io)은 API Gateway WebSocket API의 `$connect`/`$disconnect`/`@connections` 모델로 다시 써야 한다. socket.io 서버를 그대로 옮길 수 없다.

### 함정
- HTTP API의 30초는 늘릴 수 없다. A2 "수 분"이면 불일치.
- WebSocket API 2시간 강제 종료 → 재연결 로직 필수.

---

## 4.1 Azure Container Apps — 워크로드 프로필 환경, Consumption 프로필
- 계열: 컴퓨트-티어1
- 서울 리전: 있음(Korea Central). 근거: Azure 소매 가격 API에 koreacentral Consumption·Dedicated 미터 존재, Flexible 프로필 리전 목록에 Korea Central (https://learn.microsoft.com/en-us/azure/container-apps/workload-profiles-overview · 2026-10-01). 리전별 제품 페이지는 열지 않음.
- 모드 메모: 레거시 "Consumption 전용" 환경은 2 vCPU·4 GiB 상한이고 NAT·UDR·사설 엔드포인트가 없다. 아래는 기본값인 워크로드 프로필 환경 기준이다.

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | 앱(HTTP, TCP, KEDA 기반 백그라운드 워커) + Jobs(수동·cron 일정·이벤트). cron은 UTC | Jobs는 인그레스·Dapr 없음 | https://learn.microsoft.com/en-us/azure/container-apps/jobs · "Cron expressions in scheduled jobs are evaluated in Coordinated Universal Time (UTC)." · 2026-10-01 |
| CP.request_timeout | HTTP 인그레스 **240초**. Premium 인그레스는 유휴 요청 타임아웃 4~30분(기본 4분, Dedicated D 계열 2노드 이상 필요) | — | https://learn.microsoft.com/en-us/azure/container-apps/ingress-overview · "Request time out is 240 seconds" / https://learn.microsoft.com/en-us/azure/container-apps/ingress-environment-configuration · "Idle request timeouts in minutes. \| 4 \| 30 \| 4" · 2026-10-01 |
| CP.long_connection | HTTP/1.1·HTTP/2·웹소켓·gRPC 지원. 240초 한도가 웹소켓에 적용되는지 미확인. 외부 TCP 인그레스는 사용자 VNet 필요 | — | https://learn.microsoft.com/en-us/azure/container-apps/ingress-overview · "Support for WebSocket and gRPC" / "External TCP ingress is only supported for Container Apps environments that use a virtual network." · 2026-10-01 |
| CP.cpu_outside_request | 있음: 레플리카가 떠 있는 동안 CPU(동결 없음). minReplicas 이하 유휴 레플리카는 유휴 요율 | 유휴 판정: vCPU < 0.01, 수신 < 1,000 B/s | https://learn.microsoft.com/en-us/azure/container-apps/billing · "The replica is using less than 0.01 vCPU cores." · 2026-10-01 |
| CP.cold_start | 기본 minReplicas 0 / max 10 → scale-to-zero. 0으로 줄기 전 쿨다운 300초. 인그레스도 스케일 규칙도 없으면 0이 된 뒤 다시 뜨지 않음 | — | https://learn.microsoft.com/en-us/azure/container-apps/scale-app · "If ingress is disabled and you don't define a minReplicas or a custom scale rule, your container app scales to zero and has no way of starting back up." · 2026-10-01 |
| CP.instance_size | Consumption 0.25~**4 vCPU**, 0.5~**8 GiB**(1:2 고정), linux/amd64만, 이미지 8 GB. Dedicated D4~D32·E4~E32(최대 256 GiB). **서버리스 GPU는 Korea Central 미지원**(지원 17개 리전 목록에 없음) | — | https://learn.microsoft.com/en-us/azure/container-apps/containers · "Apps using the Consumption plan in a Consumption only environment are limited to a maximum of 2 cores and 4Gi of memory." / https://learn.microsoft.com/en-us/azure/container-apps/gpu-serverless-overview · 2026-10-01 |
| CP.request_size | 미확인 | — | 미확인 |
| CP.local_disk | 임시 스토리지 vCPU에 비례 1/2/4/8 GiB. 영속: Azure Files(SMB, NFS는 사용자 VNet). Blob·NetApp 마운트 불가 | — | https://learn.microsoft.com/en-us/azure/container-apps/storage-mounts · "Azure Container Apps doesn't support mounting file shares from Azure NetApp Files or Azure Blob Storage." · 2026-10-01 |
| CP.scaling | 리비전당 최대 1,000 레플리카. 확장 단계 1→4→8→16→32…, 축소 안정화 300초, KEDA 폴링 30초. 수직 확장 없음. VNet /27이면 Consumption 레플리카 약 90개로 제한 | — | https://learn.microsoft.com/en-us/azure/container-apps/scale-app · "Maximum replicas configurable are 1,000." / "Vertical scaling isn't supported." · 2026-10-01 |
| CP.concurrency | HTTP 규칙 `concurrentRequests` 기본 **10**(초과 시 레플리카 추가). 레플리카 자체는 다중 요청 처리 | — | https://learn.microsoft.com/en-us/azure/container-apps/scale-app · "concurrentRequests \| When the number of HTTP requests exceeds this value, the app adds another replica. ... \| 10 \| 1 \| n/a" · 2026-10-01 |
| CP.shutdown | SIGTERM 후 **30초**에 SIGKILL. 앱별 terminationGracePeriodSeconds 설정 여부 미확인 | — | https://learn.microsoft.com/en-us/azure/container-apps/application-lifecycle-management · "If your application doesn't respond within 30 seconds to the SIGTERM message, then SIGKILL terminates your container." · 2026-10-01 |
| CP.deploy | 리비전: 단일 모드(새 리비전 준비 후 전환, 기본), 다중 모드(% 트래픽 분할), 레이블(Preview). 비활성 리비전 100개 보관 → 이전 리비전으로 트래픽 되돌려 롤백 | — | https://learn.microsoft.com/en-us/azure/container-apps/revisions · "The existing active revision isn't deactivated until the new revision is ready." · 2026-10-01 |
| CP.availability | 존 중복은 **환경 생성 시에만** 설정 가능(VNet 필요, minReplicas ≥2, 추가 요금 없음). 단일 리전 | — | https://learn.microsoft.com/en-us/azure/reliability/reliability-container-apps · "Enable zone redundancy during environment creation. This setting can't be changed after the environment is created." · 2026-10-01 |
| CP.networking | VNet 통합(/27 이상), NAT Gateway로 고정 출구 IP, UDR, 사설 엔드포인트. 기본 출구 IP는 바뀔 수 있음. 네트워크 유형은 생성 후 변경 불가 | — | https://learn.microsoft.com/en-us/azure/container-apps/networking · "Outbound IPs might change over time." / "the NAT gateway provides a static public IP address for your environment." · 2026-10-01 |
| CP.regions | Korea Central 있음, 서버리스 GPU는 없음 | — | https://prices.azure.com/api/retail/prices (armRegionName koreacentral) · 2026-10-01 |
| CP.plan_limits | 구독별 기본 할당량(환경 수, 환경당 Consumption 코어). 숫자 기본값은 문서에서 제거되어 미확인 | — | https://learn.microsoft.com/en-us/azure/container-apps/quotas · "Your default quotas depend on factors that include the age and type of your subscription and your service usage." · 2026-10-01 |
| CP.ops_burden | 낮음~중간(평가): 노드 없음. 환경 유형·VNet·서브넷 크기·존 중복을 생성 시 한 번에 맞게 정해야 함 | — | — |
| CP.cost_floor | **$0**(scale-to-zero). Korea Central: 활성 vCPU $0.000024/초, 유휴 vCPU $0.000003/초, 메모리 $0.000003/GiB초(API가 활성·유휴 같은 반올림값 반환), 요청 $0.40/100만. min 1(0.5 vCPU·1 GiB) 유휴 상시 ≈ 월 $11.8(무료 할당 전). 사설 엔드포인트·계획 유지보수 각 $0.135/시간 | 무료: 월 180,000 vCPU초, 360,000 GiB초, 요청 200만 | https://learn.microsoft.com/en-us/azure/container-apps/billing · "The first 180,000 vCPU-seconds and 360,000 GiB-seconds in each subscription per calendar month are free." · 2026-10-01 |

### 비용 구조
위 표. Dedicated 프로필은 관리비 $0.10/시간 + vCPU $0.057077/시간 + 메모리 $0.004978/GiB-시간(Korea Central, 가격 API). Premium 인그레스를 쓰면 D 계열 노드 2개 이상 고정비.

### 교체 계열 정보
- 티어 0에서 올 때: Dockerfile, 대상 포트, 프로브, SIGTERM 30초. KEDA 스케일 규칙으로 큐 워커를 같은 플랫폼에 둘 수 있다.
- 티어 2(AKS 등)로 갈 때: KEDA·Dapr 개념이 그대로 이식된다. 리비전 트래픽 분할 → 서비스 메시나 Ingress 가중치.

### 함정
- 기본 인그레스 240초는 Cloud Run(최대 3,600초)보다 짧다.
- 존 중복·네트워크 유형을 나중에 바꿀 수 없어 환경을 새로 만들어 이전해야 한다.

---

## 5.1 GKE Autopilot
- 계열: 컴퓨트-티어2
- 서울 리전: 있음 (https://cloud.google.com/kubernetes-engine/pricing · Autopilot 가격 목록에 "Seoul (asia-northeast3)" · 2026-10-01)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | Deployment(웹·워커), CronJob/Job, 장시간 연결. CronJob은 상황에 따라 한 일정에 Job을 여러 개 만들 수 있고 `concurrencyPolicy` 기본은 Allow(중복 실행 허용). DaemonSet·특권 컨테이너는 제한 | — | https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/ · "in certain circumstances, a single CronJob can create multiple concurrent Jobs." / "`Allow` (default): The CronJob allows concurrently running Jobs" · 2026-10-01 |
| CP.request_timeout | GKE Ingress → **클래식 Application LB, 백엔드 타임아웃 기본 30초**. BackendConfig `timeoutSec`로 변경. Gateway API는 클래스별 LB | — | https://docs.cloud.google.com/kubernetes-engine/docs/how-to/ingress-configuration · "If you do not specify a value, the default value is 30 seconds." / https://docs.cloud.google.com/kubernetes-engine/docs/concepts/ingress · "Ingress for external Application Load Balancers deploys the classic Application Load Balancer." · 2026-10-01 |
| CP.long_connection | 클래식 ALB(Ingress 기본): 웹소켓이 유휴·활성 관계없이 **백엔드 타임아웃(기본 30초)에 종료**. Gateway `gke-l7-global-external-managed`(전역 외부 ALB): 활성 웹소켓 24시간. 클라이언트 keepalive 610초 | — | https://docs.cloud.google.com/load-balancing/docs/https/request-distribution · "Websocket connections, whether idle or active, automatically close after the backend service times out." · 2026-10-01 |
| CP.cpu_outside_request | 있음(Pod는 항상 실행, 요청 단위 CPU 제한 없음) | GCP 문서 인용 없음(쿠버네티스 일반 동작) | 미확인(인용) |
| CP.cold_start | 워크로드가 없으면 **노드 0까지** 축소. Pod 0은 HPA로 자동 아님(KEDA 등 필요). 새 노드 부팅 약 80~120초 | — | https://docs.cloud.google.com/kubernetes-engine/docs/concepts/autopilot-overview · "If a cluster has no running workloads, Autopilot can automatically scale the cluster down to zero nodes." / https://docs.cloud.google.com/kubernetes-engine/docs/how-to/capacity-provisioning · "Each new node takes approximately 80 to 120 seconds to boot." · 2026-10-01 |
| CP.instance_size | requests 미지정 시 0.5 vCPU·2 GiB·임시 1 GiB. 범용 최대 30 vCPU·110 GiB, Balanced 222 vCPU, Scale-Out 54 vCPU. GPU: T4·L4·A100·H100·H200·RTX PRO 6000 등. 서울 존: a=G2(L4), b=A2·G2·N1+T4, c=A3 High·A3 Edge·N1+T4 | — | https://docs.cloud.google.com/kubernetes-engine/docs/concepts/autopilot-resource-requests · "30 vCPU" / https://docs.cloud.google.com/compute/docs/gpus/gpu-regions-zones · "asia-northeast3-b Seoul, South Korea, APAC Standard • A2 Standard • G2 • N1+T4" · 2026-10-01 |
| CP.request_size | LB: URL + 요청 헤더 60 KiB 이하. 본문 한도 미확인 | — | https://docs.cloud.google.com/load-balancing/docs/quotas · "must be less than or equal to 60 KiB" · 2026-10-01 |
| CP.local_disk | Pod 임시 스토리지 10 MiB~10 GiB(더 크면 일반 임시 볼륨). 영속: PD 기반 PV는 **ReadWriteOnce**(RWX 불가), 리전 PD는 2개 존 복제. RWO 볼륨을 쓰는 Deployment는 1 레플리카여도 비권장 | — | https://docs.cloud.google.com/kubernetes-engine/docs/concepts/persistent-volumes · "Even Deployments with one replica using ReadWriteOnce volume are not recommended." · 2026-10-01 |
| CP.scaling | HPA(Pod) + Autopilot 노드 자동 프로비저닝. 오토스케일은 **실사용이 아닌 requests 기준**. 노드 부팅 80~120초 | — | https://docs.cloud.google.com/kubernetes-engine/docs/concepts/cluster-autoscaler · "based on the resource requests (rather than actual resource utilization)" · 2026-10-01 |
| CP.concurrency | 앱이 결정(서버 워커·스레드 수) | — | — |
| CP.shutdown | terminationGracePeriodSeconds 기본 30초. 노드 업그레이드 시 최대 600초(Spot 25초), PDB 1시간 존중. Spot Pod 선점 시 최대 15초 | — | https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/ · "which defaults to 30 seconds." / https://docs.cloud.google.com/kubernetes-engine/docs/concepts/cluster-upgrades-autopilot · "terminationGracePeriodSeconds is limited to 10 minutes (600 seconds) for most Pods except for Spot Pods , which are limited to 25 seconds." · 2026-10-01 |
| CP.deploy | 롤링 업데이트 maxSurge·maxUnavailable 기본 25%, `kubectl rollout undo`. 트래픽 분할은 Gateway 가중치 등 별도 | — | https://kubernetes.io/docs/concepts/workloads/controllers/deployment/ · "The default value is 25%." · 2026-10-01 |
| CP.availability | **리전 클러스터가 기본**. SLA: 컨트롤 플레인 99.95%, 여러 존 Pod 99.9% | — | https://docs.cloud.google.com/kubernetes-engine/docs/concepts/autopilot-overview · "New Autopilot clusters are regional clusters that have a publicly accessible IP address." / https://cloud.google.com/kubernetes-engine/sla · "Autopilot Cluster (control plane) 99.95% Autopilot Pods in Multiple Zones 99.9%" · 2026-10-01 |
| CP.networking | VPC 네이티브 기본(Pod IP가 VPC 별칭 IP) → Cloud SQL 사설 IP 연결. 사설 노드의 인터넷은 Cloud NAT(고정 IP는 NAT IP 예약, 인용 미확인) | — | https://docs.cloud.google.com/kubernetes-engine/docs/concepts/network-isolation · "To allow egress traffic to the internet, enable Cloud NAT or a custom NAT solution." · 2026-10-01 |
| CP.regions | 서울 있음 | — | https://cloud.google.com/kubernetes-engine/pricing · "Seoul (asia-northeast3)" · 2026-10-01 |
| CP.plan_limits | 범용 최소 requests: 버스팅 지원 클러스터 50m·52 MiB, 아니면 250m·512 MiB. CPU:메모리 1:1~1:6.5 | — | https://docs.cloud.google.com/kubernetes-engine/docs/concepts/autopilot-resource-requests · "Clusters that support bursting : 50m CPU Clusters that don't support bursting : 250m CPU" · 2026-10-01 |
| CP.ops_burden | 중간(평가): 노드는 Google 관리, 항상 릴리스 채널, **자동 업그레이드 끌 수 없음**(유지보수 창·제외로 시점만 조절). 매니페스트·Ingress·HPA·PDB는 직접 | — | https://docs.cloud.google.com/kubernetes-engine/docs/concepts/cluster-upgrades-autopilot · "You can't disable automatic upgrades, however you can control their timing with maintenance windows and exclusions ." · 2026-10-01 |
| CP.cost_floor | 클러스터 요금 $0.10/시간(월 $73) — 결제 계정당 월 $74.40 크레딧으로 Autopilot 1개 상쇄. Pod requests 초 단위 과금: 서울 범용 vCPU $0.0571/시간, 메모리 $0.0063215/GiB-시간. 기본 0.5 vCPU·2 GiB Pod 1개 ≈ 월 $30.1. + 외부 LB 포워딩 규칙 약 $18.25 | 시스템 DaemonSet·대기 Pod 무과금 | https://cloud.google.com/kubernetes-engine/pricing · "The GKE free tier provides $74.40 in monthly credits per billing account, which is equivalent to one free Autopilot or zonal Standard cluster per month." / "you are charged in one-second increments for the CPU, memory, and ephemeral storage resources that your running Pods request" · 2026-10-01 |

### 비용 구조
- 최소 월 고정비(서울): 요금 $73 − 크레딧 $74.40 = 0(첫 클러스터) + Pod 2개(멀티 존, 0.25 vCPU·0.5 GiB 최소) ≈ 월 $25.5, 기본 requests(0.5·2 GiB)면 ≈ $60 + LB 약 $18. Cloud NAT를 쓰면 + IP $0.005/시간 + $0.045/GiB.
- Spot Pod: 서울 vCPU $0.0171/시간, 메모리 $0.0018964/GiB-시간. GPU 프리미엄 서울 L4 $0.0860414/GPU-시간(노드 가격 별도).
- 함정: requests를 안 쓰면 Pod마다 0.5 vCPU·2 GiB가 과금된다.

### 교체 계열 정보
- 티어 1(Cloud Run)에서 올 때: 같은 이미지. 추가: Deployment(requests 필수), Service, Ingress/Gateway + BackendConfig(timeoutSec, 헬스체크 경로), HPA, PDB, readiness/liveness/startup probe, `preStop`. Cloud Run 동시성·max-instances → 앱 동시성 + HPA maxReplicas. Cloud Run IAM 호출자 → IAP 또는 앱 인증.
- 티어 0에서 바로 오는 것은 비권장(평가): §1.1 + §1.2 전부.

### 함정
- Ingress 기본값으로 웹소켓을 붙이면 30초마다 끊긴다. Cloud Run(최대 60분)에서 옮겨 올 때 가장 흔히 깨지는 지점.
- 업그레이드를 끌 수 없고 업그레이드 때 grace가 600초로 잘린다(장시간 작업 Pod 주의).

---

## 5.2 GKE Standard — 존 클러스터
- 계열: 컴퓨트-티어2
- 서울 리전: 있음(asia-northeast3, Compute Engine 서울 단가 존재 · https://cloud.google.com/products/compute/pricing/general-purpose · 2026-10-01)

§5.1과 같은 쿠버네티스 동작(CronJob, 롤링, Ingress 30초, 웹소켓)은 출처를 다시 적지 않고 "§5.1"로 표시했다.

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | 모든 워크로드(DaemonSet·특권 포함). CronJob 중복 가능성 §5.1 | — | https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/ · "`Allow` (default)" · 2026-10-01 |
| CP.request_timeout | Ingress 30초 기본(§5.1) | — | https://docs.cloud.google.com/kubernetes-engine/docs/how-to/ingress-configuration · "the default value is 30 seconds." · 2026-10-01 |
| CP.long_connection | §5.1과 같음 | — | https://docs.cloud.google.com/load-balancing/docs/https/request-distribution · "Websocket connections, whether idle or active, automatically close after the backend service times out." · 2026-10-01 |
| CP.cpu_outside_request | 있음 | 쿠버네티스 일반 동작 | 미확인(인용) |
| CP.cold_start | 클러스터 오토스케일러는 **자동으로 0노드로 줄이지 않음**(최소 1노드 상시). 노드 부팅 80~120초 | — | https://docs.cloud.google.com/kubernetes-engine/docs/concepts/cluster-autoscaler · "the cluster autoscaler never _automatically_ scales down a cluster to zero nodes. One or more nodes must always be available in the cluster to run system Pods." · 2026-10-01 |
| CP.instance_size | 노드 VM 크기(E2 최대 32 vCPU·128 GB 등). GPU는 존별(§5.1 서울 존 목록) | — | https://docs.cloud.google.com/compute/docs/gpus/gpu-regions-zones · "asia-northeast3-b … G2 • N1+T4" · 2026-10-01 |
| CP.request_size | LB 헤더 60 KiB, 본문 미확인 | — | https://docs.cloud.google.com/load-balancing/docs/quotas · "60 KiB" · 2026-10-01 |
| CP.local_disk | 노드 부트 디스크(임시). PD PV는 RWO·**존 단위**(존 클러스터는 한 존) | — | https://docs.cloud.google.com/kubernetes-engine/docs/concepts/persistent-volumes · "PersistentVolume resources that are backed by Compute Engine persistent disks don't support this access mode." · 2026-10-01 |
| CP.scaling | HPA + 클러스터 오토스케일러(노드 풀 min/max, requests 기준), 최대 15,000노드 | — | https://docs.cloud.google.com/kubernetes-engine/docs/concepts/cluster-autoscaler · "based on the resource requests (rather than actual resource utilization)" · 2026-10-01 |
| CP.concurrency | 앱 | — | — |
| CP.shutdown | 30초 기본. 서지 업그레이드는 PDB·grace를 최대 1시간 존중. Spot VM 노드는 기본 30초(앱 15초 + 시스템 15초), 최대 120초 | — | https://docs.cloud.google.com/kubernetes-engine/docs/concepts/cluster-upgrades · "GKE respects the Pod's PodDisruptionBudget and GracefulTerminationPeriod settings for up to one hour." / https://docs.cloud.google.com/kubernetes-engine/docs/concepts/spot-vms · "This period is split into 15 seconds for your Pods to shut down" · 2026-10-01 |
| CP.deploy | 롤링 25%/25%, rollout undo | — | https://kubernetes.io/docs/concepts/workloads/controllers/deployment/ · "The default value is 25%." · 2026-10-01 |
| CP.availability | **단일 컨트롤 플레인**, SLA 99.5%. 컨트롤 플레인 업그레이드 중 워크로드 배포·변경 불가. 노드도 한 존 | — | https://docs.cloud.google.com/kubernetes-engine/docs/concepts/cluster-upgrades · "Zonal clusters have only a single control plane. During the upgrade, your workloads continue to run, but you cannot deploy new workloads" / https://cloud.google.com/kubernetes-engine/sla · "Zonal Cluster (control plane) 99.5%" · 2026-10-01 |
| CP.networking | §5.1과 같음(VPC 네이티브, Cloud NAT) | — | https://docs.cloud.google.com/kubernetes-engine/docs/concepts/alias-ips · "VPC-native is the default network mode for all new clusters" · 2026-10-01 |
| CP.regions | 서울 있음 | — | https://cloud.google.com/products/compute/pricing/general-purpose · 2026-10-01 |
| CP.plan_limits | 클러스터 요금 $0.10/시간, 무료 크레딧 적용 대상 | — | https://cloud.google.com/kubernetes-engine/pricing · "A flat cluster management fee of $0.10 per cluster per hour (charged in 1 second increments) applies to all GKE clusters" · 2026-10-01 |
| CP.ops_burden | 높음(평가): 노드 풀, 업그레이드 전략(서지·블루그린), 유지보수 창, 노드 크기·오토스케일 범위, 노드 OS 이미지 | — | https://docs.cloud.google.com/kubernetes-engine/docs/concepts/cluster-upgrades · "GKE honors maintenance windows and exclusions during automatic upgrades when possible." · 2026-10-01 |
| CP.cost_floor | 요금 $73 − 크레딧(첫 클러스터 0) + 노드 1대: 서울 e2-medium $0.04298286/시간 ≈ 월 $31.4(e2-small $15.7) + 부트 디스크(서울 PD 단가 미확인) + LB 약 $18.25 | 노드 초 단위, 최소 1분 | https://cloud.google.com/products/compute/pricing/general-purpose · "$0.04298286 / 1 hour" (e2-medium, Seoul) · 2026-10-01 |

### 비용 구조
가장 싼 쿠버네티스 출발점(요금 크레딧 + 노드 1대). 서울 E2는 Iowa보다 약 28% 비싸다(e2-medium $0.04298 대 $0.03351).

### 교체 계열 정보
§5.1과 같음. Autopilot → Standard로 가면 노드 풀 정의, 노드 크기, 업그레이드 전략이 추가 산출물.

### 함정
- 존 클러스터는 존 장애 시 컨트롤 플레인과 노드가 함께 멈춘다. F1 "짧아야 함"이면 불일치.

---

## 5.3 GKE Standard — 리전 클러스터
- 계열: 컴퓨트-티어2
- 서울 리전: 있음

§5.2와 다른 키만 값이 다르다(굵게).

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | §5.2와 같음 | — | https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/ · "`Allow` (default)" · 2026-10-01 |
| CP.request_timeout | Ingress 30초 기본 | — | https://docs.cloud.google.com/kubernetes-engine/docs/how-to/ingress-configuration · "the default value is 30 seconds." · 2026-10-01 |
| CP.long_connection | §5.1과 같음 | — | https://docs.cloud.google.com/load-balancing/docs/https/request-distribution · 2026-10-01 |
| CP.cpu_outside_request | 있음 | — | 미확인(인용) |
| CP.cold_start | 노드 0 자동 축소 없음. **기본 노드 풀 9노드(존당 3)** | — | https://docs.cloud.google.com/kubernetes-engine/docs/concepts/regional-clusters · "The default node pool created for regional Standard clusters consists of nine nodes (three per zone)" · 2026-10-01 |
| CP.instance_size | VM 크기. **GPU는 요청 GPU가 있는 존이 하나 이상인 리전 선택** | — | https://docs.cloud.google.com/kubernetes-engine/docs/concepts/regional-clusters · "choose a region that has at least one zone where the requested GPUs are available." · 2026-10-01 |
| CP.request_size | §5.2와 같음 | — | https://docs.cloud.google.com/load-balancing/docs/quotas · "60 KiB" · 2026-10-01 |
| CP.local_disk | PD RWO(존 단위) → Pod가 다른 존으로 옮기면 볼륨이 따라가지 않음. 리전 PD는 2개 존 복제 | — | https://docs.cloud.google.com/kubernetes-engine/docs/concepts/persistent-volumes · 2026-10-01 (인용 §5.1) |
| CP.scaling | §5.2와 같음(노드 풀은 존마다 복제) | — | https://docs.cloud.google.com/kubernetes-engine/docs/concepts/cluster-autoscaler · 2026-10-01 |
| CP.concurrency | 앱 | — | — |
| CP.shutdown | §5.2와 같음 | — | https://docs.cloud.google.com/kubernetes-engine/docs/concepts/cluster-upgrades · "for up to one hour." · 2026-10-01 |
| CP.deploy | §5.2와 같음 | — | https://kubernetes.io/docs/concepts/workloads/controllers/deployment/ · "The default value is 25%." · 2026-10-01 |
| CP.availability | **컨트롤 플레인과 노드를 여러 존에 복제**, SLA 99.95% | — | https://docs.cloud.google.com/kubernetes-engine/docs/concepts/regional-clusters · "Regional clusters replicate the cluster's control plane and nodes across multiple zones within a single region." / https://cloud.google.com/kubernetes-engine/sla · "Regional Cluster (control plane) 99.95%" · 2026-10-01 |
| CP.networking | §5.1과 같음. 존 간 트래픽 과금 | — | https://docs.cloud.google.com/kubernetes-engine/docs/concepts/regional-clusters · 2026-10-01 (인용 미확인) |
| CP.regions | 서울 있음(3개 존) | — | https://docs.cloud.google.com/compute/docs/gpus/gpu-regions-zones · "asia-northeast3-b Seoul, South Korea" · 2026-10-01 |
| CP.plan_limits | **무료 크레딧 적용 안 됨** | — | https://cloud.google.com/kubernetes-engine/pricing · "cannot be applied to ... the cluster fee for Regional clusters" · 2026-10-01 |
| CP.ops_burden | 높음(평가), §5.2와 같음 | — | — |
| CP.cost_floor | 요금 월 $73(상쇄 없음) + 존당 노드 1대 이상: e2-medium 3대 ≈ 월 $94.1 + LB 약 $18.25 → **약 $185**. 기본 9노드면 e2-medium 기준 약 $282 | — | https://cloud.google.com/kubernetes-engine/pricing · "$0.10 per cluster per hour" · 2026-10-01 |

### 비용 구조
고정비가 가장 큰 GKE 구성. 기본 노드 수(9)를 그대로 두는 것이 대표적 과잉(dimensions.md §2.2 "사내 도구인데 3개 존").

### 교체 계열 정보
§5.1과 같음.

### 함정
- 리전 클러스터 + 존 단위 PD 조합에서 존 장애 시 상태 Pod는 다른 존으로 못 옮긴다.

---

## 6.1 EKS — 관리형 노드 그룹 + Cluster Autoscaler
- 계열: 컴퓨트-티어2
- 서울 리전: 있음 (https://docs.aws.amazon.com/general/latest/gr/eks.html · "Asia Pacific (Seoul) ap-northeast-2 eks.ap-northeast-2.amazonaws.com" · 2026-10-01)

EKS 네 모드 공통 사항(컨트롤 플레인, 버전 수명, ALB 컨트롤러)은 이 절에 출처를 적고 §6.2~6.4는 다른 점만 적는다.

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | 모든 워크로드(Deployment, DaemonSet, CronJob/Job, 장시간 연결). CronJob 중복 가능성은 §5.1 | — | https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/ · "`Allow` (default): The CronJob allows concurrently running Jobs" · 2026-10-01 |
| CP.request_timeout | AWS Load Balancer Controller가 만드는 **ALB 유휴 기본 60초**(어노테이션 `load-balancer-attributes: idle_timeout.timeout_seconds=N`로 변경). NLB TCP 350초 | — | https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/guide/ingress/annotations/ · "alb.ingress.kubernetes.io/load-balancer-attributes: idle_timeout.timeout_seconds=600" / https://docs.aws.amazon.com/elasticloadbalancing/latest/application/application-load-balancers.html · "The idle timeout value, in seconds. The default is 60 seconds." · 2026-10-01 |
| CP.long_connection | ALB 웹소켓 지원, 유휴 타임아웃 내 무기한. 노드 축소·교체 때 끊김 | — | https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-listeners.html · "native support for WebSockets" · 2026-10-01 |
| CP.cpu_outside_request | 있음(Pod 상시 실행) | EKS 문서 인용 없음 | 미확인(인용) |
| CP.cold_start | 노드 그룹 최소값까지 축소(0 가능 여부는 CA 설정, 인용 미확인). 노드 프로비저닝 시간 미확인 | — | 미확인 |
| CP.instance_size | EC2 인스턴스 크기. 서울 GPU 계열: G4dn, G5, G5g, G6, G6e, G6f, Gr6, G7e, Inf1, Inf2, P4d, P5, P5en, P6-B300 등(AZ별 차이) | — | https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-regions.html · "Accelerated Computing: F2 \| G4dn \| G5 \| G5g \| G6 \| G6e \| ... \| P4d \| P5 \| P5en \| P6-B300" / "An instance type that is supported in a Region might not be supported in all of the Availability Zones" · 2026-10-01 |
| CP.request_size | ALB 헤더 64K, 본문 미확인 | — | https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-limits.html · "Entire request header \| 64 K \| No" · 2026-10-01 |
| CP.local_disk | 노드 EBS(임시 성격). 영속: EBS CSI(RWO, **단일 AZ** — 볼륨과 인스턴스가 같은 AZ). 여러 AZ에 EBS 상태 워크로드를 두면 AZ마다 노드 그룹 + `--balance-similar-node-groups`. RWX는 EFS | — | https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html · "you should configure multiple node groups, each scoped to a single Availability Zone" / https://docs.aws.amazon.com/ebs/latest/userguide/ebs-volumes.html · "The volume and instance must be in the same Availability Zone." · 2026-10-01 |
| CP.scaling | HPA(metrics-server 필요) + Cluster Autoscaler(노드 그룹 = ASG, 자동 태그). MNG 클러스터당 30개, 그룹당 노드 450(조정 가능). VPC CNI라 서브넷 IP가 Pod 수 상한 | — | https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html · "automatically tagged for auto-discovery by the Kubernetes Cluster Autoscaler" · 2026-10-01 |
| CP.concurrency | 앱. ALB HTTP/2 연결당 128 스트림 | — | https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-target-groups.html · "The maximum number of streams per client HTTP/2 connection is 128." · 2026-10-01 |
| CP.shutdown | terminationGracePeriodSeconds 기본 30초, **preStop 시작부터 계산**. ALB 등록 해제 지연 기본 300초. 노드 업그레이드 드레인 15분 타임아웃. **AZRebalance·desired 감소 때는 PDB 무시** | — | https://docs.aws.amazon.com/eks/latest/best-practices/application.html · "The terminationGracePeriodSeconds value applies from when the PreStop hook action begins executing, not when the SIGTERM signal is sent." / https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html · "Pod disruption budgets aren't respected when terminating a node with AZRebalance or reducing the desired node count." · 2026-10-01 |
| CP.deploy | 롤링(maxUnavailable 25% 기본), `kubectl rollout undo`. ALB 대상과 무중단을 맞추려면 **Pod readiness gate** 필요(네임스페이스 레이블) | — | https://docs.aws.amazon.com/eks/latest/best-practices/application.html · "Kubernetes sets 25% max unavailable by default" / https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/deploy/pod_readiness_gate/ · "The pod readiness gate is needed under certain circumstances to achieve full zero downtime rolling deployments." · 2026-10-01 |
| CP.availability | 컨트롤 플레인: API 서버 2개 이상 + etcd 3개를 3 AZ에. SLA 99.95%(API 엔드포인트). 노드는 그룹 서브넷 AZ에 | — | https://docs.aws.amazon.com/eks/latest/userguide/eks-architecture.html · "at least two API server instances and three etcd instances across three AWS Availability Zones within an AWS Region" · 2026-10-01 |
| CP.networking | VPC CNI: Pod마다 VPC 사설 IP → RDS 사설 연결. 사설 서브넷 노드는 NAT 또는 ECR·S3 VPC 엔드포인트로 이미지 풀. 고정 출구 IP = NAT 탄력적 IP(§1.3) | — | https://docs.aws.amazon.com/eks/latest/userguide/managing-vpc-cni.html · "assigns a private IPv4 or IPv6 address from your VPC to each Pod" · 2026-10-01 |
| CP.regions | 서울 있음 | — | https://docs.aws.amazon.com/general/latest/gr/eks.html · "ap-northeast-2" · 2026-10-01 |
| CP.plan_limits | 표준 지원 14개월 + 연장 12개월. **연장 지원 기본 켜짐** → 업그레이드 안 하면 $0.10 → **$0.60/시간**. 연장 종료 시 컨트롤 플레인 자동 업그레이드(알림 없음), MNG 노드는 구버전에 남음 | — | https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html · "A minor version is under standard support in Amazon EKS for the first 14 months after it's released." / "Extended support is enabled by default." / "You won't receive any notification before the update." · 2026-10-01 |
| CP.ops_burden | 높음(평가): 버전 업그레이드(연 1회 이상), 노드 AMI 패치 배포, 애드온(VPC CNI, CoreDNS, kube-proxy, EBS CSI, LB 컨트롤러, metrics-server, CA), IAM(Pod Identity), 서브넷 IP 계획 | — | https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html · "you're responsible for deploying these patched AMI versions to your managed node groups" · 2026-10-01 |
| CP.cost_floor | 컨트롤 플레인 $0.10/시간(월 $73). MNG 추가 요금 없음. t3.medium $0.052/시간(월 $37.96) × 2 + gp3 20 GB × 2($0.0912/GB-월) + ALB $16.43 + NAT 1개 $43.07 ≈ **월 $212** | 연장 지원 시 요금 월 $438 | [PL] AmazonEKS ap-northeast-2 · "Amazon EKS cluster usage in Asia Pacific (Seoul)" 0.10 / "Amazon EKS extended support usage in Asia Pacific (Seoul)" 0.50 / https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html · "There are no additional costs to use Amazon EKS managed node groups" · 2026-10-01 |

### 비용 구조
위 표. 3 AZ마다 NAT를 두면 NAT만 월 $129. EKS는 무료 크레딧이 없다(GKE와 다름).

### 교체 계열 정보
- ECS(§3.1)에서 올 때: 태스크 정의 → Deployment·Service, 서비스 오토스케일 → HPA, 태스크 역할 → Pod Identity, ALB 대상 그룹 → LB 컨트롤러 Ingress(`target-type`), 서킷 브레이커 → 롤아웃 감시. SIGTERM 계약은 같지만 기본 유예가 30초로 같아도 preStop 시간이 그 안에 포함된다.
- 티어 0에서 바로 오는 것은 비권장(평가).

### 함정
- 등록 해제 지연 300초 vs Pod grace 30초 불일치: preStop sleep + `deregistration_delay` 단축 없이는 배포 중 502/504.
- 연장 지원 자동 과금($0.60/시간)은 업그레이드를 미루기만 해도 생긴다.

---

## 6.2 EKS — Karpenter
- 계열: 컴퓨트-티어2
- 서울 리전: 있음(EKS와 같음)

§6.1과 다른 키만 적는다. 적지 않은 키(request_timeout, long_connection, request_size, concurrency, deploy, networking, regions, plan_limits의 버전 정책)는 §6.1과 같은 값·출처다.

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | §6.1과 같음 | — | §6.1 |
| CP.request_timeout | ALB 60초(§6.1) | — | §6.1 |
| CP.long_connection | §6.1과 같음. 노드 만료·통합(consolidation) 때 끊김 | — | §6.1 |
| CP.cpu_outside_request | 있음 | — | 미확인(인용) |
| CP.cold_start | 부하에 맞는 노드를 **1분 안에** 기동 | — | https://docs.aws.amazon.com/eks/latest/userguide/autoscaling.html · "Karpenter launches right-sized compute resources (for example, Amazon EC2 instances) in response to changing application load in under a minute." · 2026-10-01 |
| CP.instance_size | 기본은 리전의 모든 인스턴스 유형. GPU는 NodePool로 | — | https://docs.aws.amazon.com/eks/latest/best-practices/karpenter.html · "By default, Karpenter will use all Instance Types EC2 offers in the region" · 2026-10-01 |
| CP.request_size | §6.1 | — | §6.1 |
| CP.local_disk | §6.1과 같음(EBS 단일 AZ) | — | §6.1 |
| CP.scaling | 대기 Pod 기준 노드 직접 생성(ASG 없음), 통합으로 축소. **클러스터 전역 상한 설정 불가**(NodePool별 limits만) | — | https://docs.aws.amazon.com/eks/latest/best-practices/karpenter.html · "It is not possible to set a global limit for the whole cluster." · 2026-10-01 |
| CP.concurrency | 앱 | — | — |
| CP.shutdown | Pod 30초 기본. 노드 `expireAfter` 기본 **720시간(30일)**, 중단 예산 기본 노드 10%. `karpenter.sh/do-not-disrupt`로 보호. Spot 중단 처리는 SQS 큐 필요 | — | https://karpenter.sh/docs/concepts/disruption/ · "By default, expireAfter is set to 720h (30 days)." / "If undefined, Karpenter will default to one budget with nodes: 10%." · 2026-10-01 |
| CP.deploy | §6.1 | — | §6.1 |
| CP.availability | §6.1 + 컨트롤러는 Karpenter가 관리하지 않는 노드(MNG 또는 Fargate)에서 실행해야 함. **Karpenter에는 AWS SLA 없음** | — | https://docs.aws.amazon.com/eks/latest/best-practices/karpenter.html · "Do not run Karpenter on a node that is managed by Karpenter." / https://docs.aws.amazon.com/eks/latest/userguide/autoscaling.html · "There is no AWS Service Level Agreement (SLA) for Karpenter" · 2026-10-01 |
| CP.networking | §6.1 | — | §6.1 |
| CP.regions | 서울 있음 | — | §6.1 |
| CP.plan_limits | §6.1(버전 정책) | — | §6.1 |
| CP.ops_burden | 높음(평가): §6.1 + Karpenter 자체 설치·업그레이드(OSS), NodePool·EC2NodeClass, 중단 큐 | — | https://docs.aws.amazon.com/eks/latest/userguide/autoscaling.html · "There is no AWS Service Level Agreement (SLA) for Karpenter" · 2026-10-01 |
| CP.cost_floor | 요금 $73 + 컨트롤러용 노드(MNG 소형 또는 Fargate Pod) + 워크로드 노드 + ALB + NAT ≈ §6.1과 비슷(정확한 최소 구성 단가는 미확인) | — | [PL] AmazonEKS ap-northeast-2 · 2026-10-01 |

### 비용 구조
노드 크기를 Pod requests에 맞춰 골라 대규모에서 절감. 소규모에서는 컨트롤러 노드 때문에 MNG보다 싸지 않다(평가). NodePool limits가 없으면 비용 상한이 없다.

### 교체 계열 정보
MNG(§6.1)에서 올 때 앱 코드 변경 없음. 노드 중단이 잦아지므로 PDB·preStop·재연결이 필수가 된다.

### 함정
- 30일 노드 만료 + 통합으로 장시간 연결·싱글톤 Pod가 주기적으로 끊긴다.

---

## 6.3 EKS — Auto Mode
- 계열: 컴퓨트-티어2
- 서울 리전: 있음(서울 Auto Mode 관리비 SKU 존재 [PL] AmazonEKS ap-northeast-2 · 2026-10-01)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | 모든 워크로드, DaemonSet 지원 | — | https://docs.aws.amazon.com/eks/latest/userguide/automode.html · "Rather than modify services installed on your nodes, you can instead use Kubernetes DaemonSets." · 2026-10-01 |
| CP.request_timeout | 내장 ALB 연동, 유휴 60초 기본. `group.name` Ingress 어노테이션 미지원(IngressClassParams로) | — | https://docs.aws.amazon.com/eks/latest/userguide/auto-configure-alb.html · "Not supported / Specify groups in IngressClass only" · 2026-10-01 |
| CP.long_connection | §6.1과 같음, 노드 교체(최대 21일) 때 끊김 | — | §6.1 |
| CP.cpu_outside_request | 있음 | — | 미확인(인용) |
| CP.cold_start | Karpenter 기반 노드 생성(시간 수치 미확인). 노드 0까지 축소 여부 인용 미확인 | — | https://docs.aws.amazon.com/eks/latest/userguide/autoscaling.html · "EKS Auto Mode builds upon Karpenter." · 2026-10-01 |
| CP.instance_size | CPU 1개 초과, nano·micro·small 제외. **기본 내장 풀은 C·M·R, 온디맨드, 5세대 이상만(GPU·Spot 제외)** → GPU(g4dn·g5·g6·p4d·p5 등)는 사용자 NodePool | — | https://docs.aws.amazon.com/eks/latest/userguide/auto-cost-control.html · "No accelerated (P, G, Inf, Trn) or exotic instance types are permitted." · 2026-10-01 |
| CP.request_size | §6.1 | — | §6.1 |
| CP.local_disk | EBS는 `ebs.csi.eks.amazonaws.com` 프로비저너만. 기존 볼륨은 스냅샷 이전 필요 | — | https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi.html · "EKS Auto Mode requires storage classes to use ebs.csi.eks.amazonaws.com as the provisioner." · 2026-10-01 |
| CP.scaling | Karpenter 기반 자동 확장·통합. 내장 풀은 CPU·메모리 상한 없음, 지속 실패 시 다른 허용 유형으로 대체 기동 | — | https://docs.aws.amazon.com/eks/latest/userguide/auto-cost-control.html · "when sustained launch failures occur, EKS Auto Mode will launch from any remaining available instance type" · 2026-10-01 |
| CP.concurrency | 앱 | — | — |
| CP.shutdown | Pod 30초 기본. **노드 최대 수명 21일**(줄일 수 있음), 자동 교체 | — | https://docs.aws.amazon.com/eks/latest/userguide/automode.html · "nodes launched by EKS Auto Mode have a maximum lifetime of 21 days (which you can reduce)" · 2026-10-01 |
| CP.deploy | §6.1. ALB 대상 유형 기본 `ip` | — | https://docs.aws.amazon.com/eks/latest/userguide/auto-configure-alb.html · "Valid values are instance and ip. The default is ip." · 2026-10-01 |
| CP.availability | §6.1(컨트롤 플레인 3 AZ) | — | §6.1 |
| CP.networking | VPC CNI·네트워크 정책 내장. IMDSv2 홉 1 고정. 노드 SSH·SSM 접근 불가 | — | https://docs.aws.amazon.com/eks/latest/userguide/automode.html · "Prevents direct access to the nodes by disallowing SSH or SSM access." · 2026-10-01 |
| CP.regions | 서울 있음 | — | [PL] AmazonEKS ap-northeast-2 · "$0.00624 per hour for EKS Auto Mode management of t3.medium in Asia Pacific (Seoul)" · 2026-10-01 |
| CP.plan_limits | §6.1 버전 정책 + 인스턴스별 관리비 | — | https://aws.amazon.com/eks/pricing/ · "a management fee that varies based on the EC2 instance type launched, in addition to your regular EC2 instance costs" · 2026-10-01 |
| CP.ops_burden | 중간(평가): AWS가 컴퓨트 오토스케일, Pod 네트워킹, ELB 연동, EBS 드라이버, 노드 OS 패치(주간 AMI) 관리. 남는 일: 클러스터 버전 업그레이드, 매니페스트, NodePool(GPU 등) | — | https://docs.aws.amazon.com/eks/latest/userguide/automode.html · "AWS manages compute autoscaling, Pod networking with network policy enforcement, Elastic Load Balancing integration, and storage drivers configuration." · 2026-10-01 |
| CP.cost_floor | 요금 $73 + 노드 1대(예: c6g.large $0.077 + 관리비 $0.00924 = 월 $63.0, 기본 풀에서 Graviton 허용 여부는 미확인) + ALB $16.43 + NAT $43.07 ≈ **월 $195** + EBS | — | [PL] AmazonEC2 ap-northeast-2 · "$0.077 per On Demand Linux c6g.large Instance Hour" / [PL] AmazonEKS · "EKS-Auto:c6g.large-management-hours" 0.00924 · 2026-10-01 |

### 비용 구조
노드 단가 + 약 12% 관리비(c6g.large 기준 $0.00924/$0.077). GPU 노드도 관리비(g5.xlarge $0.09649/시간, g6.xlarge $0.07719/시간 [PL]).

### 교체 계열 정보
MNG·Karpenter에서 올 때: StorageClass 프로비저너 교체 + 볼륨 스냅샷 이전, Ingress `group.name` → IngressClassParams, LB 컨트롤러 직접 설치분 제거.

### 함정
- 21일 노드 수명: 노드에 붙은 장시간 상태(로컬 캐시, 연결)가 최소 3주마다 초기화.
- 기본 풀에 상한이 없어 용량 부족 시 더 비싼 유형으로 넘어갈 수 있다.

---

## 6.4 EKS — Fargate 프로필
- 계열: 컴퓨트-티어2
- 서울 리전: 있음 (https://aws.amazon.com/about-aws/whats-new/2020/10/amazon-eks-adds-fargate-support-10-additional-aws-regions/ · "...Asia Pacific (Seoul), and Asia Pacific (Hong Kong) regions." · 2026-10-01)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | Deployment, Job. **DaemonSet·특권 컨테이너·HostPort·HostNetwork 불가** | — | https://docs.aws.amazon.com/eks/latest/userguide/fargate.html · "Daemonsets aren't supported on Fargate." · 2026-10-01 |
| CP.request_timeout | ALB 60초. **대상 유형 `ip` 필수**(LB 컨트롤러 기본은 `instance`) | — | https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/guide/ingress/annotations/ · "target-type / instance \| ip / instance" · 2026-10-01 |
| CP.long_connection | §6.1과 같음. AWS가 주기적으로 Pod를 패치·축출 | — | https://docs.aws.amazon.com/eks/latest/userguide/fargate.html · "there are times when Pods must be deleted if they aren't successfully evicted" · 2026-10-01 |
| CP.cpu_outside_request | 있음, 단 요청한 만큼만(버스트 불가) | — | https://docs.aws.amazon.com/eks/latest/userguide/fargate.html · "No – The Pod can be re-deployed using a larger vCPU and memory configuration though." · 2026-10-01 |
| CP.cold_start | scale-to-zero 없음(노드 개념 없음, Pod 기동 시간 미확인) | — | 미확인 |
| CP.instance_size | 최대 16 vCPU·120 GB, requests = limits, Pod마다 256 MB 추가(1 vCPU·8 GB → 2 vCPU·9 GB로 과금). **GPU·Arm·Windows 없음** | — | https://docs.aws.amazon.com/eks/latest/userguide/fargate-pod-configuration.html · "16 vCPU \| Between 32 GB and 120 GB in 8-GB increments" / https://docs.aws.amazon.com/eks/latest/userguide/fargate.html · "GPUs aren't currently available on Fargate." · 2026-10-01 |
| CP.request_size | §6.1 | — | §6.1 |
| CP.local_disk | 임시 20 GiB 기본, 최대 175 GiB(Pod 종료 시 삭제). **EBS 불가**, EFS 정적 프로비저닝만 | — | https://docs.aws.amazon.com/eks/latest/userguide/fargate-pod-configuration.html · "each Pod running on Fargate receives a default 20 GiB of ephemeral storage" / https://docs.aws.amazon.com/eks/latest/userguide/fargate.html · "You can't mount Amazon EBS volumes to Fargate Pods." · 2026-10-01 |
| CP.scaling | HPA. 노드 오토스케일러 불필요. Fargate 온디맨드 vCPU 할당량 기본 6 | — | https://docs.aws.amazon.com/general/latest/gr/eks.html · "Fargate On-Demand vCPU resource count \| 6" · 2026-10-01 |
| CP.concurrency | 앱 | — | — |
| CP.shutdown | Pod 30초 기본(§6.1) | — | https://docs.aws.amazon.com/eks/latest/best-practices/application.html · "This grace period is 30 seconds by default" · 2026-10-01 |
| CP.deploy | §6.1 | — | §6.1 |
| CP.availability | §6.1 컨트롤 플레인. Fargate SLA 미확인 | — | 미확인 |
| CP.networking | **사설 서브넷 전용**(NAT 필요), IMDS 없음 | — | https://docs.aws.amazon.com/eks/latest/userguide/fargate.html · "Pods that run on Fargate are only supported on private subnets" · 2026-10-01 |
| CP.regions | 서울 있음 | — | 위 whats-new · 2026-10-01 |
| CP.plan_limits | **EKS에서 Fargate Spot 미지원**. 컨트롤 플레인 업그레이드 시 Fargate Pod는 재배포로 직접 갱신 | — | https://docs.aws.amazon.com/eks/latest/userguide/fargate.html · "Amazon EKS doesn't support Fargate Spot." / https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html · "you must still update the Fargate nodes yourself" · 2026-10-01 |
| CP.ops_burden | 중간(평가): 노드 없음. 남는 일: 클러스터 업그레이드, Pod 재배포, 프로필 셀렉터, 사설 서브넷·NAT | — | — |
| CP.cost_floor | 요금 $73 + Pod 과금(이미지 다운로드 시작부터, 최소 1분; 서울 vCPU $0.04656/시간, GB $0.00511/시간) + **NAT 필수** $43.07 + ALB $16.43. 앱 Pod 0.25 vCPU·0.5 GB(→ 1 GB 과금) ≈ 월 $12.2. CoreDNS도 Fargate Pod로 과금 → **월 약 $145 + CoreDNS** | — | [PL] AmazonEKS ap-northeast-2 · "AWS Fargate - vCPU - Asia Pacific (Seoul)" 0.04656 · 2026-10-01 |

### 비용 구조
위 표. 256 MB 오버헤드로 반올림되어 같은 크기의 ECS Fargate보다 비쌀 수 있다.

### 교체 계열 정보
ECS Fargate에서 올 때 같은 격리 모델이다. Ingress `target-type: ip`, Fargate 프로필 셀렉터(네임스페이스·레이블), requests = limits 명시가 필요.

### 함정
- 할당량 6 vCPU + 256 MB 반올림 + CoreDNS Pod로 작은 배포도 막힐 수 있다.
- 노드가 없다는 이유로 고르면 NAT 고정비와 EBS 불가에서 걸린다.

---

## 6.5 VM 위 경량 쿠버네티스 — k3s (요약)
- 계열: 컴퓨트-티어2 (자체 운영)
- 서울 리전: VM을 둔 리전(EC2·Compute Engine 서울 모두 가능)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | 모든 쿠버네티스 워크로드 | — | https://docs.k3s.io/installation/requirements · 2026-10-01 |
| CP.request_timeout | 기본 내장 Traefik 인그레스 설정에 따름(기본값 미확인). 앞에 클라우드 LB를 두면 그 LB 값 | — | 미확인 |
| CP.long_connection | Traefik 설정에 따름(미확인) | — | 미확인 |
| CP.cpu_outside_request | 있음 | — | 미확인(인용) |
| CP.cold_start | 노드 오토스케일 없음(VM 고정) | — | 평가 |
| CP.instance_size | VM 크기. 서버 최소 2코어·2 GB, 에이전트 1코어·512 MB | — | https://docs.k3s.io/installation/requirements · server "2 cores" "2 GB"; agent "1 core" "512 MB" · 2026-10-01 |
| CP.request_size | Traefik 설정(미확인) | — | 미확인 |
| CP.local_disk | Local Path Provisioner: 볼륨이 **노드에 고정**(노드 장애 시 Pod 이동 불가). 분산 저장은 Longhorn | — | https://docs.k3s.io/add-ons/storage · "Note that this does result in permanently binding the pod to the node hosting the volume" · 2026-10-01 |
| CP.scaling | HPA만(노드 증설은 수동) | — | 평가 |
| CP.concurrency | 앱 | — | — |
| CP.shutdown | Pod 30초 기본(쿠버네티스) | — | https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/ · "which defaults to 30 seconds." · 2026-10-01 |
| CP.deploy | 롤링 25%(쿠버네티스) | — | https://kubernetes.io/docs/concepts/workloads/controllers/deployment/ · "The default value is 25%." · 2026-10-01 |
| CP.availability | 기본 데이터스토어 SQLite는 **서버 1대 전용**. HA는 임베디드 etcd 서버 **3대 이상**(홀수) | — | https://docs.k3s.io/datastore · "SQLite cannot be used on clusters with multiple servers." / https://docs.k3s.io/datastore/ha-embedded · "Three or more server nodes that will serve the Kubernetes API and run other control plane services" · 2026-10-01 |
| CP.networking | ServiceLB(Klipper)가 모든 노드의 80/443을 hostPort로 점유. 포트 6443(API), UDP 8472(VXLAN), 10250 | — | https://docs.k3s.io/networking/networking-services · "ports 80 and 443 will not be usable for other HostPort or NodePort pods" · 2026-10-01 |
| CP.regions | VM 리전 | — | — |
| CP.plan_limits | 없음(자체 운영) | — | — |
| CP.ops_burden | **가장 높음**(평가): OS 패치, k3s 업그레이드, etcd 백업, 인증서, 저장소, LB, 모니터링 전부 직접 | — | — |
| CP.cost_floor | VM 1대: EC2 t3.small $0.026/시간(월 $18.98) + gp3 20 GB $1.82 + 공인 IPv4 $3.65 ≈ **월 $24.5**. HA는 서버 3대(×3) | — | [PL] AmazonEC2 ap-northeast-2 · "$0.026 per On Demand Linux t3.small Instance Hour" · 2026-10-01 |

### 비용 구조
VM 비용뿐. 관리형 컨트롤 플레인 요금·LB 요금이 없는 대신 운영 시간이 비용이다.

### 교체 계열 정보
매니페스트는 관리형 쿠버네티스와 대부분 호환. 이전 시 바뀌는 것: Ingress 클래스(Traefik → 클라우드 LB), StorageClass(local-path → EBS/PD), ServiceLB → 클라우드 LB.

### 함정
- 단일 서버 k3s는 "쿠버네티스를 쓰지만 단일 VM과 같은 가용성"이다(F1 판정은 단일 VM과 동일).

---

## 7.1 단일 VM + docker compose — EC2
- 계열: 컴퓨트-티어2(기준선, 바이브코더 대안)
- 서울 리전: 있음

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | 모두(웹, 상시 워커, cron, 장시간 연결). 컨테이너 재시작 기본은 `no` → `restart:` 지정 필요 | — | https://docs.docker.com/reference/compose-file/services/ · "no: The default restart policy. It does not restart the container under any circumstances." · 2026-10-01 |
| CP.request_timeout | 플랫폼 상한 없음(리버스 프록시·앞단 LB 설정에 따름). ALB를 붙이면 60초 기본 | — | 평가 / §1.3 |
| CP.long_connection | 제한 없음(프록시 설정에 따름) | — | 평가 |
| CP.cpu_outside_request | 있음 | — | 평가 |
| CP.cold_start | 해당 없음(상시). scale-to-zero 없음 | — | 평가 |
| CP.instance_size | 인스턴스 유형 크기. 서울 GPU: g4dn.xlarge $0.647/시간, g5.xlarge $1.237, g6.xlarge $0.9896 | AZ별 제공 차이 | [PL] AmazonEC2 ap-northeast-2 · "$0.9896 per On Demand Linux g6.xlarge Instance Hour" · 2026-10-01 |
| CP.request_size | 리버스 프록시 설정(nginx 기본 등, 미확인) | — | 미확인 |
| CP.local_disk | EBS: **인스턴스와 독립적으로 영속**, 같은 AZ에서만 연결. 인스턴스 스토어는 정지·종료 시 소멸 | 인스턴스 1대만 쓰므로 B2(로컬 파일·SQLite)와 맞음, 대신 확장 불가 | https://docs.aws.amazon.com/ebs/latest/userguide/ebs-volumes.html · "EBS volumes persist independently from the running life of an EC2 instance." / https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-store-lifetime.html · "the data does not persist if the instance is stopped, hibernated, or terminated" · 2026-10-01 |
| CP.scaling | 오토스케일 없음(수직 확장 = 유형 변경, 재시작 필요) | — | 평가 |
| CP.concurrency | 앱 | — | — |
| CP.shutdown | compose `stop_grace_period` 기본 **10초** 후 SIGKILL | — | https://docs.docker.com/reference/compose-file/services/ · "Default value is 10 seconds for the container to exit before sending SIGKILL." · 2026-10-01 |
| CP.deploy | `docker compose up -d`로 컨테이너 교체 = **배포 중 순단**(무중단·롤백 수단 없음, 직접 구성) | — | 평가 |
| CP.availability | 단일 AZ. 인스턴스 수준 SLA 99.5%. AWS 예약 이벤트(재부팅·정지·폐기) | — | https://aws.amazon.com/compute/sla/ · "Single EC2 Instance available with an Instance-Level Uptime Percentage of at least 99.5%" / https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/monitoring-instances-status-check_sched.html · "AWS can schedule events to reboot, stop, and retire your instances." · 2026-10-01 |
| CP.networking | 같은 VPC의 RDS에 사설 연결. 고정 IP = 탄력적 IP(리전당 기본 5개, 유휴도 과금) | — | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/elastic-ip-addresses-eip.html · "An Elastic IP address is static; it does not change over time." · 2026-10-01 |
| CP.regions | 서울 있음 | — | [PL] AmazonEC2 ap-northeast-2 · 2026-10-01 |
| CP.plan_limits | 계정 vCPU 할당량(미확인) | — | 미확인 |
| CP.ops_burden | 높음(평가): OS 패치, Docker 업데이트, TLS 인증서, 백업(EBS 스냅샷), 모니터링, 디스크 가득 참 | — | — |
| CP.cost_floor | t4g.small $0.0208/시간(월 $15.18) 또는 t3.small $0.026(월 $18.98) + gp3 20 GB $1.82 + 공인 IPv4 $3.65 → **월 $20.7~24.5**. LB·NAT 없음 | — | [PL] AmazonEC2 ap-northeast-2 · "$0.0208 per On Demand Linux t4g.small Instance Hour" / "$0.0912 per GB-month of General Purpose (gp3) provisioned storage - Asia Pacific (Seoul)" · 2026-10-01 |

### 비용 구조
가장 싼 상시 구성. 고정비가 낮은 대신 가용성(F1)·배포(F4)·확장(D3) 능력이 없다.

### 교체 계열 정보
- 티어 0에서 올 때: `docker-compose.yml`, Dockerfile, 리버스 프록시(TLS). 로컬 파일·SQLite가 그대로 동작하므로 코드 변경이 가장 적다(그래서 바이브코더가 고른다).
- 티어 1로 갈 때: compose 서비스 하나하나를 플랫폼 서비스로 분리(웹 / 워커 / cron → Jobs·Scheduler), 볼륨 데이터(SQLite·uploads)를 관리형 DB·오브젝트 스토리지로, compose 내부 DNS 이름(`db`, `redis`)을 관리형 엔드포인트 환경변수로, SIGTERM 유예 10초 → 플랫폼 값.

### 함정
- compose `restart` 기본 `no`: 재부팅 후 앱이 안 뜬다.
- 같은 VM에 DB를 두면 VM 장애 = 데이터 위험(C7·F3)이고 백업은 직접 해야 한다.

---

## 7.2 단일 VM + docker compose — Compute Engine
- 계열: 컴퓨트-티어2(기준선)
- 서울 리전: 있음(asia-northeast3)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| CP.process_types | 모두 | — | https://docs.docker.com/reference/compose-file/services/ · "no: The default restart policy." · 2026-10-01 |
| CP.request_timeout | 상한 없음(프록시 설정). 외부 ALB를 붙이면 30초 기본 | — | §1.3 |
| CP.long_connection | 제한 없음 | — | 평가 |
| CP.cpu_outside_request | 있음 | — | 평가 |
| CP.cold_start | 해당 없음 | — | 평가 |
| CP.instance_size | E2 최대 e2-standard-32(32 vCPU·128 GB), VM당 PD 합계 257 TiB. GPU: 서울 존 a=G2(L4), b=A2·G2·N1+T4, c=A3·N1+T4. GPU VM은 라이브 마이그레이션 안 됨 | — | https://docs.cloud.google.com/compute/docs/general-purpose-machines · "the total Persistent Disk capacity can't exceed 257 TiB" / https://docs.cloud.google.com/compute/docs/instances/live-migration-process · "VM instances with GPUs attached must be set to stop and optionally restart." · 2026-10-01 |
| CP.request_size | 프록시 설정(미확인) | — | 미확인 |
| CP.local_disk | Persistent Disk 영속(존 단위) | — | https://docs.cloud.google.com/kubernetes-engine/docs/concepts/persistent-volumes · 2026-10-01 (PD 존 단위는 GKE 문서 기준, VM 문서 인용 미확인) |
| CP.scaling | 없음 | — | 평가 |
| CP.concurrency | 앱 | — | — |
| CP.shutdown | compose 10초 | — | https://docs.docker.com/reference/compose-file/services/ · "Default value is 10 seconds for the container to exit before sending SIGKILL." · 2026-10-01 |
| CP.deploy | 순단 배포(직접 구성) | — | 평가 |
| CP.availability | 단일 인스턴스 SLA ≥99.9%, 여러 존 ≥99.99% | — | https://cloud.google.com/compute/sla · "A Single Instance of all other families** >= 99.9%" · 2026-10-01 |
| CP.networking | VPC 사설 IP로 Cloud SQL 사설 연결. 고정 외부 IP 예약(단가 미확인) | — | 미확인 |
| CP.regions | 서울 있음 | — | https://cloud.google.com/products/compute/pricing/general-purpose · 2026-10-01 |
| CP.plan_limits | 무료 e2-micro는 **미국 3개 리전만**(서울 아님) | — | https://cloud.google.com/free/docs/free-cloud-features · "1 non-preemptible e2-micro VM instance per month in one of the following US regions" · 2026-10-01 |
| CP.ops_burden | 높음(평가), §7.1과 같음 | — | — |
| CP.cost_floor | 서울 e2-micro $0.010745715/시간(월 $7.84), e2-small $0.02149143(월 $15.69), e2-medium $0.04298286(월 $31.38) + 디스크·외부 IP(서울 단가 미확인) | — | https://cloud.google.com/products/compute/pricing/general-purpose · "$0.04298286 / 1 hour" (e2-medium, Seoul) · 2026-10-01 |

### 비용 구조
§7.1과 같은 성격. 서울에는 무료 VM이 없다.

### 교체 계열 정보
§7.1과 같음. GCP 쪽 티어 1 대상은 Cloud Run 서비스 + Jobs + Cloud SQL + GCS.

### 함정
- GPU VM은 호스트 유지보수 때 정지된다(라이브 마이그레이션 없음).

---

## 8. 판정을 뒤집는 발견

1. **Cloud Run 요청 기반 과금은 A4(응답 후 작업)와 불일치하는 기본값이다.** "CPU is only allocated during request processing." 처방은 인스턴스 기반 과금(서울 min 1 기준 월 약 $59.9) 또는 큐 + 워커 풀(월 약 $37.4). 웹소켓을 하나라도 열어 두면 자동으로 인스턴스 기반 요율로 과금된다.
2. **서울에는 서버리스 GPU가 없다.** Cloud Run GPU(L4·RTX PRO 6000)와 Azure Container Apps 서버리스 GPU 모두 서울 리전 목록에 없고, Fargate·Lambda·EKS Fargate는 GPU 자체가 없다. A6 "GPU 필요" + D5 "한 지역(한국)"이면 티어 2(GKE의 서울 G2·N1+T4, EKS·EC2의 G4dn·G5·G6)나 VM이 사실상 유일한 서울 선택지다.
3. **타임아웃 기본값이 플랫폼마다 크게 달라 이전 후 504·끊김이 생긴다.** Cloud Run 300초(최대 3,600초), ACA 240초, App Runner 120초, ALB 유휴 60초, API Gateway HTTP API 30초(고정), **GKE Ingress 30초이고 클래식 ALB는 웹소켓을 30초에 끊는다**. Cloud Run → GKE 이전 시 웹소켓 앱은 BackendConfig `timeoutSec` 또는 관리형 Gateway가 필수다.
4. **App Runner는 신규 고객에게 닫혔고 서울에 없다**(API 문서 기준 2026-03-31 마감, 이 저장소 다른 문서의 2026-04-30과 다름). AWS 티어 1 기본은 ECS Express Mode. 단, Express Mode는 ALB를 항상 만들고(월 $16.4 + 태스크 min 1) 기본으로 공용 서브넷에 공인 IP로 배치된다.
5. **고정비 함정이 기본값에 숨어 있다.** EKS 연장 지원은 기본 켜짐이라 업그레이드를 미루면 클러스터 요금이 $73 → $438/월이 된다. GKE 리전 Standard는 무료 크레딧이 없고 기본 9노드다. Fargate·EKS Fargate는 신규 계정 vCPU 할당량 6에서 막힌다. EKS Fargate·Express(사설) 구성은 NAT($43/AZ)가 필수다. 반대로 GKE Autopilot·존 Standard는 결제 계정당 클러스터 1개 요금이 크레딧으로 상쇄된다.
