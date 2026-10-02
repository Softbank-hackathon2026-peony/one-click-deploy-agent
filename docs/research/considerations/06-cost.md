# 비용·과금 구조

삭제된 항목: COST-078, COST-080, COST-091, 사유: 부적격 출처 (2026-10-02, 3개 삭제. 남은 항목 ID는 그대로)

infrafit의 비용 축(모든 판정을 거르는 필터, 설계 문서 §2 원칙 5, §8.4 COST, §9)에 쓰일 고려 요소 카탈로그다. 고정비·변동비·할인·right-sizing·미사용 자원·플랫폼(Vercel/Supabase/Firebase) 초과 과금·외부 API 폭증·예산 가드레일을 다루고, "아끼면 안 되는 곳"은 반대 방향 규칙으로 따로 묶었다.
가격은 2026-10-01 확인 기준이다. AWS 서울(ap-northeast-2) 단가는 AWS Price List API 오퍼 파일을 직접 받아 읽었다(아래 "가격 원천" 참고). GCP 단가는 공식 가격 페이지의 기본 표(us-central1)만 확인했고, 서울(asia-northeast3)은 Cloud Run 기준 **Tier 2(더 비싼 등급)** 리전이라는 점만 확인했다. 월 환산은 730시간 기준이다.

## 가격 원천 (이 문서 전체에 공통)
- **[PL]** AWS Price List 오퍼 파일 (curl로 직접 조회, 2026-10-01). 형식: `https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/{서비스코드}/current/ap-northeast-2/index.json` (EC2는 `index.csv`). 조회한 서비스코드: AmazonEC2(게시 2026-09-25), AmazonVPC(2026-09-17), AmazonRDS(2026-10-01), AmazonS3(2026-09-28), AmazonEKS, AWSELB, AmazonECS(Fargate), AWSLambda, AmazonCloudWatch, AmazonECR, AmazonElastiCache, AWSDataTransfer, AWSSecretsManager, awskms. CloudFront는 전역 파일 `.../AmazonCloudFront/current/index.json`. 이것은 설계 문서 S20의 Price List와 같은 원천이다.
- **[GCP-HTML]** GCP 가격 페이지는 WebFetch가 잘려서, 같은 공식 URL을 curl로 받아 HTML 표의 기본값(us-central1)을 읽었다.

## 하위 분류 목차
- A. 고정비·기본 요금 (COST-001 ~ COST-010)
- B. 컴퓨트 right-sizing·스케일링·k8s 노드 낭비 (COST-011 ~ COST-022)
- C. 할인 수단 (COST-023 ~ COST-029)
- D. 데이터 전송 함정 (COST-030 ~ COST-038)
- E. 스토리지·레지스트리 (COST-039 ~ COST-047)
- F. DB·캐시 (COST-048 ~ COST-060)
- G. 관측 도구 비용 (COST-061 ~ COST-067)
- H. 서버리스·PaaS 비용 곡선과 플랜 한도 (COST-068 ~ COST-077)
- I. 외부 API·사용량 폭증·키 유출 (COST-078 ~ COST-085)
- J. 거버넌스·가시성·청구 구조 (COST-086 ~ COST-095)
- K. 아끼면 안 되는 곳 (반대 방향 규칙) (COST-096 ~ COST-102)
- 새 축·규칙 후보

> 번호는 이 카탈로그 안의 번호다. 설계 문서 §8.4의 COST-001~009와 번호가 겹치므로, 규칙집으로 옮길 때는 대응표(맨 끝 절)를 보고 ID를 다시 매긴다.

---

## A. 고정비·기본 요금

### COST-001 쿠버네티스 컨트롤 플레인 고정비
- **무엇/왜:** EKS·GKE는 노드와 별개로 클러스터마다 시간당 관리비를 받는다. 트래픽이 0이어도 나가는 순수 고정비라 작은 앱에서는 전체 청구의 큰 비율이 된다.
- **실패 양상:** T≤1·D≤1 앱이 티어 2를 쓰면 클러스터 1개만으로 월 약 $73이 깔린다. 환경(dev/stg/prod)을 클러스터로 나누면 3배.
- **신호:** 🟢 `aws_eks_cluster`, `google_container_cluster` 개수 / 🟢 환경별 별도 클러스터(디렉터리 `envs/dev`, `envs/prod`에 각각 클러스터 리소스) / 🟡 서비스 수 < 5
- **관련 수준:** T≤1 & D≤1 & 서비스 < 5 이면 과잉(설계 TIER-004와 연동). 환경별 클러스터는 U≤1이면 과잉.
- **처방:** 티어 1(Cloud Run/Fargate)로 견적 비교 / 티어 2 유지 시 namespace로 환경 분리, GKE는 무료 크레딧이 적용되는 존 클러스터 또는 Autopilot 1개.
- **검증:** Price List `AmazonEKS` `APN2-AmazonEKS-Hours:perCluster`, Infracost `aws_eks_cluster` 라인.
- **비용 영향:** EKS 서울 $0.10/시간 = 월 $73/클러스터. GKE $0.10/시간 = 월 $73, 단 결제 계정당 월 $74.40 크레딧(존 클러스터·Autopilot 1개 상당, 리전 클러스터에는 적용 안 됨).
- **출처:** [PL] AmazonEKS; https://aws.amazon.com/eks/pricing/ ; https://cloud.google.com/kubernetes-engine/pricing

### COST-002 EKS·GKE 확장 지원(Extended Support) 요금
- **무엇/왜:** k8s 마이너 버전의 표준 지원(EKS 14개월)이 끝난 클러스터는 자동으로 확장 지원 요금이 붙는다. 버전 업그레이드를 미루는 것만으로 컨트롤 플레인 비용이 6배가 된다.
- **실패 양상:** 아무도 안 건드린 클러스터가 월 $73 → $438로 뛴다.
- **신호:** 🟢 Terraform `aws_eks_cluster.version`이 낡은 값 / 🟢 `upgrade_policy { support_type = "EXTENDED" }` / 🟢 GKE `release_channel { channel = "EXTENDED" }` / 🔴 실제 클러스터 버전(코드에 버전 미고정 시)
- **관련 수준:** 수준 무관. 모든 티어 2 구성에 경고.
- **처방:** 티어 2: 버전 업그레이드 계획을 처방, EKS `support_type = "STANDARD"`로 확장 지원 자동 진입을 막을지 검토(막으면 강제 업그레이드됨) / 티어 1: 해당 없음.
- **검증:** Price List `APN2-AmazonEKS-Hours:extendedSupport`; EKS 버전 달력과 Terraform 버전 비교.
- **비용 영향:** 서울 확장 지원 추가 $0.50/시간(표준 $0.10 + $0.50 = $0.60, EKS 가격 페이지의 "$0.60 per cluster per hour"와 일치) = 월 약 $438/클러스터.
- **출처:** [PL] AmazonEKS; https://aws.amazon.com/eks/pricing/ ; https://cloud.google.com/kubernetes-engine/pricing (Extended 채널 추가 관리비 언급)

### COST-003 NAT Gateway 시간 요금과 AZ별 배치
- **무엇/왜:** NAT Gateway는 개당 시간 요금 + GB당 처리 요금이다. Terraform 모듈 기본값이 AZ마다 하나씩 만드는 경우가 많아, 트래픽이 거의 없는 앱에서 고정비 1위가 된다.
- **실패 양상:** 3 AZ × NAT = 월 약 $129, 트래픽이 없어도 나간다.
- **신호:** 🟢 `aws_nat_gateway` 개수 / 🟢 `terraform-aws-modules/vpc`의 `one_nat_gateway_per_az = true`, `single_nat_gateway = false` / 🟢 GCP `google_compute_router_nat`
- **관련 수준:** D≤1이면 AZ별 NAT는 과잉(단일 NAT 또는 리전 NAT). D≥2면 AWS 권장 구성이므로 유지하고 비용만 표시(COST-099 참고).
- **처방:** 티어 1: Fargate·Cloud Run을 퍼블릭 서브넷/직접 이그레스로 두어 NAT 자체를 없앨 수 있는지 검토 / 티어 2: D≤1이면 단일 NAT, S3·ECR 트래픽은 엔드포인트로(COST-031).
- **검증:** Infracost `aws_nat_gateway`; 소크 중 `BytesOutToDestination` 지표로 처리량 측정.
- **비용 영향:** 서울 $0.059/시간(월 $43.07/개) + $0.059/GB. us-east-1 $0.045/$0.045. 리전 NAT Gateway도 서울 $0.059/시간(AZ당 과금). GCP Cloud NAT는 VM당 $0.0014/시간(32대 상한, 이후 게이트웨이 $0.044/시간) + $0.045/GiB + IP $0.005/시간(us-central1 표).
- **출처:** [PL] AmazonEC2 `APN2-NatGateway-Hours`, `APN2-RegionalNatGateway-Hours`; https://aws.amazon.com/vpc/pricing/ ; https://cloud.google.com/nat/pricing

### COST-004 퍼블릭 IPv4 주소 과금
- **무엇/왜:** AWS는 사용 중이든 유휴든 모든 퍼블릭 IPv4에 시간 요금을 받는다. EC2 노드마다 퍼블릭 IP, 퍼블릭 RDS, NAT·ALB의 IP가 모두 쌓인다.
- **실패 양상:** 노드 10대 + ALB(AZ당 IP) + NAT 3개면 IP만 월 $50 이상. 유휴 EIP는 순수 낭비.
- **신호:** 🟢 `associate_public_ip_address = true`, `map_public_ip_on_launch = true` / 🟢 `aws_eip` 중 연결 안 된 것 / 🟢 `aws_db_instance.publicly_accessible = true`
- **관련 수준:** 수준 무관. 노드에 퍼블릭 IP는 보안상으로도 불필요(보안 담당과 공유).
- **처방:** 티어 2: 노드는 프라이빗 서브넷, 유휴 EIP 삭제 / 티어 1: 플랫폼 관리 IP라 해당 적음 / IPv6 듀얼스택 검토.
- **검증:** Price List `APN2-PublicIPv4:InUseAddress`; 청구서 "Public IPv4 Address" 항목; `ec2 describe-addresses`.
- **비용 영향:** 서울 $0.005/시간 = 월 $3.65/개(사용 중·유휴 동일).
- **출처:** [PL] AmazonVPC; https://aws.amazon.com/vpc/pricing/

### COST-005 로드밸런서 시간 요금과 LB 남발
- **무엇/왜:** ALB/NLB는 개당 시간 요금 + LCU 요금이다. k8s에서 `Service type: LoadBalancer`를 서비스마다 쓰면 서비스 수만큼 LB가 생긴다.
- **실패 양상:** 서비스 5개 = LB 5개 = 고정비 월 약 $82 + LCU. Ingress 하나로 묶으면 1개.
- **신호:** 🟢 매니페스트 `type: LoadBalancer` 개수 / 🟢 `aws_lb` 개수 / 🟢 Ingress에 `alb.ingress.kubernetes.io/group.name` 없음 / 🟡 dev 환경에도 LB
- **관련 수준:** T≤1에서 LB 2개 이상이면 과잉 의심.
- **처방:** 티어 2: Ingress 1개로 통합(ALB IngressGroup, GKE Gateway) / 티어 1: Cloud Run·App Runner 기본 엔드포인트로 LB 생략 가능한지 검토.
- **검증:** Price List `AWSELB`; Infracost; 청구서 LoadBalancerUsage.
- **비용 영향:** 서울 ALB·NLB $0.0225/시간(월 $16.43/개) + ALB LCU $0.008/LCU-시간, NLB $0.006. Classic LB $0.025/시간.
- **출처:** [PL] AWSELB; https://aws.amazon.com/elasticloadbalancing/pricing/

### COST-006 인터페이스 VPC 엔드포인트 남발
- **무엇/왜:** 인터페이스 엔드포인트(PrivateLink)는 엔드포인트×AZ마다 시간 요금이 붙는다. "보안상 전부 엔드포인트로" 만들면 NAT보다 비싸질 수 있다.
- **실패 양상:** 서비스 6개(ECR api/dkr, logs, sts, secretsmanager, ssm) × 3 AZ = 월 약 $171 고정비.
- **신호:** 🟢 `aws_vpc_endpoint` 중 `vpc_endpoint_type = "Interface"` 개수 × `subnet_ids` 수
- **관련 수준:** T≤1 & 트래픽 적음이면 과잉. 보안 규제(사설망 강제) 신호가 있으면 유지.
- **처방:** 티어 2: S3·DynamoDB는 무료 게이트웨이 엔드포인트, 나머지는 트래픽량과 NAT 처리비를 비교해 선택 / D≤1이면 엔드포인트 AZ 수 축소.
- **검증:** Price List `APN2-VpcEndpoint-Hours`, `APN2-VpcEndpoint-Bytes`; 엔드포인트별 `BytesProcessed`.
- **비용 영향:** 서울 $0.013/시간/AZ(월 $9.49) + $0.01/GB(1PB까지).
- **출처:** [PL] AmazonVPC; https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints-s3.html

### COST-007 Transit Gateway·VPC 분리 과잉
- **무엇/왜:** 작은 앱에 "엔터프라이즈 랜딩존" 템플릿을 쓰면 Transit Gateway와 여러 VPC가 따라온다. 첨부(attachment)마다 시간 요금 + GB 처리 요금.
- **실패 양상:** VPC 3개 연결만으로 월 약 $153 + 트래픽 $0.02/GB.
- **신호:** 🟢 `aws_ec2_transit_gateway`, `aws_ec2_transit_gateway_vpc_attachment` / 🟢 `aws_vpc` 3개 이상
- **관련 수준:** 서비스 < 5 & 단일 팀이면 과잉.
- **처방:** 티어 2: 단일 VPC, 필요 시 VPC 피어링(시간 요금 없음, GB당 과금) / 티어 1: 해당 없음.
- **검증:** Price List `APN2-TransitGateway-Hours`, `APN2-TransitGateway-Bytes`; Infracost.
- **비용 영향:** 서울 첨부당 $0.07/시간(월 $51.1) + $0.02/GB. VPC 피어링 $0.01/GB(in/out 각각).
- **출처:** [PL] AmazonVPC

### COST-008 최소 인스턴스·min replicas 고정비
- **무엇/왜:** 최소 인스턴스(Cloud Run `min-instances`, Lambda provisioned concurrency, HPA `minReplicas`, ECS `desiredCount`)는 유휴 시간에도 과금된다. 콜드 스타트를 피하는 대가다.
- **실패 양상:** T≤1 사내 도구가 `minReplicas: 3`이면 24시간 3배 비용. 반대로 T=3에 min 0이면 장애(COST-097).
- **신호:** 🟢 `minReplicas`, `run.googleapis.com/min-instances`/`min_instance_count`, `aws_lambda_provisioned_concurrency_config`, `desired_count` / 🟡 업무 시간 외 트래픽 0 신호(사내 도구, SSO만)
- **관련 수준:** T≤1 & U≤1이면 min=0 또는 1이 적정. T=3 & 1분 램프면 min ≥ 기준 인스턴스 필수(TIER-003).
- **처방:** 티어 0/1: min 0(scale-to-zero) 또는 업무 시간대만 min 상향 / 티어 2: `minReplicas` = PDB 만족 최소값(2) 이하로 낮출지 U 수준과 함께 판단.
- **검증:** Cloud Run 가격표 idle 요율; 소크 중 유휴 시간 비율 × 단가.
- **비용 영향:** Cloud Run(us-central1, 요청 기반) 최소 인스턴스 유휴 요율 vCPU $0.0000025/초, 메모리 $0.0000025/GiB초 → 1 vCPU·512MiB 하나 상시 = 월 약 $9.9. Lambda 프로비저닝 동시성 서울 $0.0000051254/GB초 → 1GB × 10 동시성 상시 = 월 약 $134.7. Seoul Cloud Run은 Tier 2라 이보다 비쌈(가격 API 필요).
- **출처:** https://cloud.google.com/run/pricing ; [PL] AWSLambda `APN2-Lambda-Provisioned-Concurrency`

### COST-009 시크릿·키 관리 항목당 요금
- **무엇/왜:** Secrets Manager는 시크릿 1개당 월 요금, KMS는 고객 관리 키 1개당 월 요금이다. 환경변수 하나하나를 별도 시크릿으로 만들면 개수가 폭증한다.
- **실패 양상:** 환경 3개 × 시크릿 30개 = 90개 = 월 $36. 큰 돈은 아니지만 "필요한 만큼" 원칙 위반 신호.
- **신호:** 🟢 `aws_secretsmanager_secret` 개수 / 🟢 `aws_kms_key` 개수(서비스별 키) / 🟡 같은 앱의 값을 키별로 분리
- **관련 수준:** 수준 무관. 정보성 경고.
- **처방:** 앱별로 JSON 시크릿 1개에 묶기 / 비밀이 아닌 설정은 SSM Parameter Store 표준 파라미터(무료 등급)나 ConfigMap / KMS는 AWS 관리 키로 충분한지 검토(규제 신호 없으면).
- **검증:** Price List; Infracost.
- **비용 영향:** 서울 Secrets Manager $0.40/시크릿/월 + $0.05/1만 API 호출. KMS $1/키 버전/월 + $0.03/1만 요청.
- **출처:** [PL] AWSSecretsManager, awskms

### COST-010 RDS·ElastiCache 엔진 확장 지원 요금
- **무엇/왜:** 표준 지원이 끝난 DB 엔진 메이저 버전(예: PostgreSQL 11/12, Redis OSS 구버전)은 자동으로 vCPU당 확장 지원 요금이 붙는다. 3년차에는 두 배.
- **실패 양상:** db.m7g.large(2 vCPU) PostgreSQL 12를 방치하면 인스턴스비와 별도로 월 약 $175 추가.
- **신호:** 🟢 `aws_db_instance.engine_version`/`aws_rds_cluster.engine_version`이 지원 종료 버전 / 🟢 `aws_elasticache_*` `engine_version` 구버전 / 🔴 실제 실행 버전
- **관련 수준:** 수준 무관.
- **처방:** 메이저 업그레이드 계획(U≥2면 블루/그린 배포로) / 업그레이드 불가 시 비용을 리포트에 명시.
- **검증:** Price List `APN2-ExtendedSupport:Yr1-Yr2:PostgreSQL12` 등.
- **비용 영향:** 서울 RDS for PostgreSQL 확장 지원 1~2년차 $0.120/vCPU-시간, 3년차 $0.240. Aurora Serverless v2는 ACU당 $0.102(1~2년차). ElastiCache Redis OSS 확장 지원 cache.t4g.micro +$0.019/시간(1~2년차).
- **출처:** [PL] AmazonRDS, AmazonElastiCache

---

## B. 컴퓨트 right-sizing·스케일링·k8s 노드 낭비

### COST-011 requests 과다 설정 (실사용 대비)
- **무엇/왜:** k8s 스케줄러와 클러스터 오토스케일러는 실제 사용량이 아니라 **requests**로 노드를 잡는다. requests가 실사용의 몇 배면 노드가 비어 있어도 새 노드가 생긴다.
- **실패 양상:** CPU requests 1000m, 실사용 100m → 노드 비용 10배. 가장 흔한 k8s 낭비.
- **신호:** 🟢 매니페스트 `resources.requests.cpu/memory` 값 / 🟡 프레임워크 기본 런타임(Node 단일 스레드인데 cpu 2) / 🔴 실사용량(P4 측정 필요)
- **관련 수준:** 수준 무관. 설계 §8.4 COST-006(실측의 2배 이상 → right-sizing)과 같은 규칙.
- **처방:** 티어 2: VPA `updateMode: "Off"`로 추천만 받아 requests 조정, GKE Autopilot이면 Pod requests가 곧 청구액 / 티어 1: Cloud Run·Fargate 태스크 크기 축소.
- **검증:** P4 소크 중 `container_cpu_usage_seconds_total` P95 vs requests; VPA 추천값.
- **비용 영향:** GKE Autopilot(us-central1) vCPU $0.0445/시간, 메모리 $0.0049225/GiB-시간 → 불필요한 0.5 vCPU·1GiB requests를 Pod 3개가 가지면 월 약 $59.5 낭비.
- **출처:** https://docs.cloud.google.com/kubernetes-engine/docs/concepts/cluster-autoscaler ("based on the resource requests (rather than actual resource utilization)"); https://kubernetes.io/docs/concepts/workloads/autoscaling/vertical-pod-autoscale/ ; https://cloud.google.com/kubernetes-engine/pricing

### COST-012 requests 미설정 (과소 → 장애, 과금 불명)
- **무엇/왜:** requests가 없으면 스케줄러가 노드를 과밀하게 채우고 OOM·스로틀링이 난다. Autopilot은 기본값을 강제로 채워 넣어 예측과 다른 청구가 나온다.
- **실패 양상:** 피크 때 노드 압박으로 Pod 축출 → 재시작 폭풍. 비용 견적 자체가 불가능.
- **신호:** 🟢 컨테이너에 `resources` 블록 없음 / 🟢 `LimitRange` 없음
- **관련 수준:** T≥1이면 결함(견적 불가 → 비용 필터 작동 불가).
- **처방:** 티어 2: 실측 기반 requests + LimitRange 기본값 / 티어 1: 태스크 CPU·메모리 명시.
- **검증:** P4 부하 시험에서 OOMKilled·throttling 지표.
- **비용 영향:** 직접 비용보다 견적 정확도 문제. 장애 비용은 다른 축.
- **출처:** https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/ (설계 S26, 이번 작업에서 재열람 안 함)

### COST-013 노드 크기 선택 (bin packing 손실)
- **무엇/왜:** 노드가 너무 작으면 DaemonSet·시스템 Pod 오버헤드 비율이 커지고, 너무 크면 마지막 노드가 반쯤 빈다. Pod 크기 분포에 맞는 노드 크기가 있다.
- **실패 양상:** t3.small 노드 10대에서 DaemonSet(로그·CNI·모니터링)이 노드마다 0.3 vCPU를 먹으면 용량의 15% 증발.
- **신호:** 🟢 노드 그룹 `instance_types` / 🟢 DaemonSet 개수와 requests / 🟢 가장 큰 Pod requests > 노드 할당 가능량의 50%
- **관련 수준:** 티어 2 전용. 수준 무관.
- **처방:** 티어 2: (Pod requests 합 + DaemonSet × 노드 수)로 노드 크기별 총비용을 계산해 최소값 선택, Karpenter로 혼합 크기 허용 / 티어 1: 해당 없음.
- **검증:** P4에서 노드 할당률(`kube_node_status_allocatable` 대비 requests 합).
- **비용 영향:** 서울 t3.small $0.026/시간, t3.medium $0.052, m7g.large $0.1003. 노드 수 × 오버헤드 비율로 산정.
- **출처:** 일반 원칙(출처 미확인). 단가는 [PL] AmazonEC2. ⚠️근거없음

### COST-014 클러스터 오토스케일러 축소 프로필·통합(consolidation)
- **무엇/왜:** 기본 프로필은 여유 노드를 오래 남긴다. GKE `optimize-utilization`이나 Karpenter `WhenEmptyOrUnderutilized`는 덜 찬 노드를 적극 제거·교체한다.
- **실패 양상:** 야간에 Pod가 줄어도 노드가 그대로 남아 하루 절반이 유휴.
- **신호:** 🟢 GKE `cluster_autoscaling { autoscaling_profile = "BALANCED" }`(기본) / 🟢 Karpenter NodePool `disruption.consolidationPolicy: WhenEmpty` 또는 `consolidateAfter: Never` / 🟢 오토스케일러 자체 없음(고정 노드 수)
- **관련 수준:** T≤2에서 적극 축소가 유리. T=3이면 여유 용량(T-CTL-009)과 충돌하므로 축소 프로필을 보수적으로.
- **처방:** 티어 2: T≤2면 `OPTIMIZE_UTILIZATION`/`WhenEmptyOrUnderutilized` + PDB로 안전 확보 / T=3이면 balanced + 자리표시 Pod.
- **검증:** 일 평균 노드 수 vs 일 평균 requests 합.
- **비용 영향:** 유휴 노드 시간 × 노드 단가. 예: m7g.large 2대가 하루 12시간 놀면 월 약 $73.
- **출처:** https://docs.cloud.google.com/kubernetes-engine/docs/concepts/cluster-autoscaler ; https://karpenter.sh/docs/concepts/disruption/

### COST-015 고정 크기 노드 그룹 (오토스케일 없음)
- **무엇/왜:** `min = max = desired`인 노드 그룹은 피크 기준으로 상시 운영된다.
- **실패 양상:** 피크 3배 가정이면 평시 용량의 2/3가 낭비.
- **신호:** 🟢 `aws_eks_node_group.scaling_config { min_size == max_size }` / 🟢 GKE `node_count` 고정, `autoscaling` 블록 없음
- **관련 수준:** T≥1이면 오토스케일 필수(T-CTL-002). T=0이면 고정이 맞다.
- **처방:** 티어 2: 클러스터 오토스케일러 또는 Karpenter / 티어 1로 내리는 견적도 함께.
- **검증:** Infracost 노드 그룹 비용 vs P4 피크·평시 측정.
- **비용 영향:** (max − 평시 필요 노드) × 노드 단가 × 730.
- **출처:** 일반 원칙(출처 미확인). 설계 S6(HPA), S14 참고. ⚠️근거없음

### COST-016 HPA 상한 미설정 또는 과대 (비용 상한 없음)
- **무엇/왜:** 오토스케일 상한이 없거나 터무니없이 크면, 봇 트래픽·무한 재시도·DDoS가 그대로 청구서가 된다. 상한은 비용 가드레일이다.
- **실패 양상:** Cloud Run `max-instances` 기본(100) 또는 Lambda 동시성 무제한 상태에서 공격 트래픽 → 하룻밤에 수백~수천 달러.
- **신호:** 🟢 HPA `maxReplicas` 과대 / 🟢 Cloud Run `max_instance_count` 없음 / 🟢 Lambda `reserved_concurrent_executions` 없음 / 🟢 ECS `max_capacity` 과대
- **관련 수준:** 모든 수준에서 상한 필수. 값은 T 가정의 피크 × 1.5 정도 + DB 커넥션 한도(T-CTL-003).
- **처방:** 티어 0: 플랫폼 지출 한도(COST-088) / 티어 1·2: 피크 가정 기반 상한 + 레이트 리밋.
- **검증:** 상한 × 인스턴스 단가 × 시간 = "최악의 시간당 비용"을 리포트에 표시.
- **비용 영향:** 예: Fargate 1 vCPU·2GB 태스크 서울 $0.0568/시간 × 상한 200 = 시간당 $11.4.
- **출처:** 일반 원칙(출처 미확인). 단가는 [PL] AmazonECS. ⚠️근거없음

### COST-017 버스터블 인스턴스(t계열) CPU 크레딧 함정
- **무엇/왜:** t3/t4g는 싸지만 기준 성능 이상을 계속 쓰면 크레딧이 바닥난다. `unlimited` 모드면 초과 vCPU 시간이 추가 과금된다.
- **실패 양상:** 상시 CPU 50% 쓰는 워커를 t3.small(unlimited)에 두면 m계열보다 비싸지거나, standard 모드면 스로틀링.
- **신호:** 🟢 `instance_type = "t3.*"/"t4g.*"` + `credit_specification { cpu_credits = "unlimited" }` / 🟡 상시 워커·배치가 t계열
- **관련 수준:** 수준 무관. 상시 고부하 워크로드에 t계열이면 경고.
- **처방:** 티어 2: 상시 부하는 m/c계열, 간헐 부하만 t계열 / 티어 1: Fargate는 해당 없음.
- **검증:** CloudWatch `CPUCreditBalance`, `CPUSurplusCreditsCharged`.
- **비용 영향:** 서울 t4g.medium $0.0416/시간 vs m7g.large $0.1003. 초과 크레딧 단가는 이번에 확인 못 함.
- **출처:** 일반 원칙(출처 미확인). 인스턴스 단가는 [PL] AmazonEC2. ⚠️근거없음

### COST-018 ARM(Graviton·Ampere) 미사용
- **무엇/왜:** 같은 크기에서 ARM 인스턴스가 싸다. 멀티 아키텍처 이미지만 있으면 대부분의 웹 앱은 그대로 돈다.
- **실패 양상:** 별 이유 없이 x86을 써서 매달 약 20%를 더 냄.
- **신호:** 🟢 `instance_types`가 x86(m7i, c7i, t3) / 🟢 Fargate `runtime_platform.cpu_architecture` 없음(X86_64 기본) / 🟢 Lambda `architectures` 없음 / 🟢 Dockerfile·CI에 `--platform linux/arm64` 빌드 없음 / 🟡 네이티브 바이너리 의존성(x86 전용 휠)
- **관련 수준:** 수준 무관. 설계 §8.4 COST-005.
- **처방:** 티어 1: Fargate ARM, Lambda arm64 / 티어 2: m7g/c7g/t4g 노드 그룹 + `docker buildx` 멀티 아키텍처.
- **검증:** 같은 부하에서 P4 성능 비교 후 단가 비교.
- **비용 영향:** 서울 m7i.large $0.1239 vs m7g.large $0.1003(−19%), t3.micro $0.013 vs t4g.micro $0.0104(−20%), Fargate vCPU $0.04656 vs ARM $0.03725(−20%), Lambda GB초 $0.0000166667 vs ARM $0.0000133334(−20%), ElastiCache·RDS도 g계열이 저렴.
- **출처:** [PL] AmazonEC2, AmazonECS, AWSLambda; 설계 S23 https://aws.amazon.com/ec2/graviton/ (이번 작업에서 재열람 안 함)

### COST-019 이전 세대 인스턴스 사용
- **무엇/왜:** 구세대(m4, c4, t2, r5 등)는 신세대보다 가격 대비 성능이 나쁘고 때로 단가 자체도 높다.
- **실패 양상:** 같은 일을 더 비싸게, 더 느리게.
- **신호:** 🟢 `instance_type`/`instance_class` 접두사가 m4·c4·t2·r4·db.m4·db.t2·cache.t2 등
- **관련 수준:** 수준 무관.
- **처방:** 같은 계열 최신 세대(가급적 g계열)로 교체 견적.
- **검증:** Price List로 두 인스턴스 시간 단가 직접 비교.
- **비용 영향:** 서울 m6i.large $0.118 → m6g.large $0.094 → m7g.large $0.1003 처럼 세대·아키텍처별 차이를 가격 API로 계산.
- **출처:** [PL] AmazonEC2. 세대 교체 권고 자체는 일반 원칙(출처 미확인). ⚠️근거없음

### COST-020 Fargate·Cloud Run 태스크 크기 조합 과대
- **무엇/왜:** Fargate는 vCPU와 메모리를 따로 과금하고, 허용 조합이 정해져 있어 메모리만 필요해도 vCPU가 따라온다. Cloud Run도 CPU·메모리 각각 과금.
- **실패 양상:** 0.25 vCPU면 충분한 API를 1 vCPU·2GB로 띄워 4배 비용.
- **신호:** 🟢 ECS 태스크 정의 `cpu`, `memory` / 🟢 Cloud Run `resources.limits.cpu/memory` / 🟡 Node.js·Python 단일 프로세스인데 vCPU 2 이상
- **관련 수준:** 수준 무관.
- **처방:** 티어 1: P4 실측 P95 기반 최소 조합, 동시성 설정과 함께 조정.
- **검증:** 소크 중 CPU·메모리 사용률.
- **비용 영향:** 서울 Fargate(x86) 0.25 vCPU·0.5GB = 월 약 $10.4/태스크, 1 vCPU·2GB = 월 약 $41.4/태스크.
- **출처:** [PL] AmazonECS `APN2-Fargate-vCPU-Hours:perCPU` $0.04656, `APN2-Fargate-GB-Hours` $0.00511

### COST-021 Cloud Run 동시성(concurrency) 1 설정
- **무엇/왜:** 동시성을 1로 두면 요청마다 인스턴스가 필요해 인스턴스 수가 요청 동시성과 같아진다. I/O 위주 웹 앱은 인스턴스 하나가 수십 요청을 처리할 수 있다.
- **실패 양상:** 인스턴스 시간이 수십 배로 늘어 요청 기반 과금이 폭증.
- **신호:** 🟢 `containerConcurrency: 1`, `max_instance_request_concurrency = 1` / 🟡 스레드 안전하지 않은 라이브러리 사용(정당한 이유)
- **관련 수준:** 수준 무관. 정당한 이유(전역 상태, CPU 바운드)가 없으면 경고.
- **처방:** 티어 1: 기본값(80×vCPU 근처)에서 시작해 P4로 조정.
- **검증:** P4에서 동시성별 지연·비용 곡선.
- **비용 영향:** 인스턴스 시간 ∝ 1/동시성. 요청 기반 과금(us-central1) vCPU $0.000024/초.
- **출처:** https://cloud.google.com/run/pricing ; 설계 S2(동시성 기본값)

### COST-022 Lambda 메모리 크기 기본값 방치
- **무엇/왜:** Lambda는 메모리 × 실행 시간으로 과금하고 CPU는 메모리에 비례한다. 너무 작으면 느려서 오히려 비싸고, 너무 크면 낭비다.
- **실패 양상:** 128MB로 무거운 작업 → 실행 시간 길어짐 + 타임아웃. 3008MB로 단순 프록시 → 23배 단가.
- **신호:** 🟢 `aws_lambda_function.memory_size` / 🟢 `timeout` 대비 실제 실행 시간(로그) / 🟡 SAM·Serverless Framework 기본값 그대로
- **관련 수준:** 수준 무관.
- **처방:** 티어 1/0: 메모리별 실행 시간 측정 후 GB초 최소점 선택, arm64.
- **검증:** CloudWatch `Duration` × 메모리 → GB초 계산.
- **비용 영향:** 서울 $0.0000166667/GB초, 요청 $0.20/100만. 1GB·100ms 요청 100만 건 = 약 $1.87.
- **출처:** [PL] AWSLambda

---

## C. 할인 수단

### COST-023 Savings Plans·Reserved Instances 미적용 (상시 기준 부하)
- **무엇/왜:** 24시간 돌아가는 기준 용량에는 1년·3년 약정 할인이 크다. Compute Savings Plans는 EC2·Fargate·Lambda에 공통 적용된다.
- **실패 양상:** 1년 이상 운영할 상시 노드·태스크를 온디맨드로 계속 지불.
- **신호:** 🔴 약정 여부는 코드에 없음(청구 데이터 필요) / 🟡 운영 기간이 길다는 신호(production 환경, 고정 min 용량)
- **관련 수준:** 평시 최소 용량에만 적용. T 피크분에는 적용하지 않는다.
- **처방:** 티어 1·2: "평시 최소 용량의 70~80%만 약정" 권고(과약정은 COST-029) / 티어 0: 해당 없음.
- **검증:** Cost Explorer Savings Plans 추천, Price List Reserved 단가.
- **비용 영향:** 서울 m7g.large 온디맨드 $0.1003 → 1년 표준 RI 선결제 없음 $0.0656(−35%), 3년 선결제 없음 $0.0453(−55%). Compute SP 최대 66%, EC2 Instance SP 최대 72%(AWS 문구).
- **출처:** [PL] AmazonEC2 Reserved 항목; https://aws.amazon.com/savingsplans/compute-pricing/

### COST-024 GCP CUD·SUD 이해 (E2는 SUD 없음)
- **무엇/왜:** GCP는 N1/N2/N2D/C2 등에 자동 지속 사용 할인(SUD)을 주지만 E2 등에는 없다. 약정(CUD)은 리소스 기반과 지출 기반(Compute flexible, GKE·Cloud Run·GCE 공통)이 있고 **취소 불가**.
- **실패 양상:** "GCP는 자동 할인되니까" 하고 E2 노드를 상시 운영 → 할인 0.
- **신호:** 🟢 `machine_type = "e2-*"` 상시 노드 / 🔴 약정 보유 여부
- **관련 수준:** 평시 최소 용량.
- **처방:** 티어 2 GKE: 상시 노드는 CUD, 또는 SUD 적용 계열 비교 / 티어 1 Cloud Run: 항상 1개 이상 켜져 있으면 Cloud Run CUD(가격표에 1년·3년 열 존재).
- **검증:** Billing Catalog API의 CUD SKU; Cloud Run 가격표 CUD 열.
- **비용 영향:** SUD 최대 30%(N1)·20%(N2/N2D/C2). 리소스 기반 CUD 최대 55%(메모리 최적화 70%). Cloud SQL CUD 1년 25%·3년 52%(vCPU 단가 $0.0413 → $0.030975 / $0.019824). Cloud Run 인스턴스 기반 vCPU $0.000018 → Flexible CUD 3년 $0.00000972.
- **출처:** https://docs.cloud.google.com/compute/docs/sustained-use-discounts ; https://docs.cloud.google.com/compute/docs/instances/committed-use-discounts-overview ; https://cloud.google.com/sql/pricing ; https://cloud.google.com/run/pricing

### COST-025 상태 없는 워커·배치에 Spot 미사용
- **무엇/왜:** 중단을 견디는(멱등·재시도 가능) 작업은 Spot으로 크게 아낄 수 있다.
- **실패 양상:** 야간 배치·큐 워커를 온디맨드로 돌려 최대 수 배 지불.
- **신호:** 🟢 큐 소비자·CronJob·Job 워크로드 / 🟢 노드 그룹 `capacity_type = "ON_DEMAND"`만 / 🟢 ECS `capacity_provider_strategy`에 FARGATE_SPOT 없음 / 🟡 C-CTL-004(큐 소비자 멱등) 충족 여부
- **관련 수준:** C≥2 워커는 멱등이 확인될 때만. 웹 앞단(T≥2)은 Spot 단독 금지, 온디맨드 base + Spot 혼합.
- **처방:** 티어 1: Fargate Spot(2분 전 SIGTERM, `stopTimeout` ≤ 120초) / 티어 2: Spot 노드 그룹 + 여러 인스턴스 타입, GKE Spot Pod.
- **검증:** P4 장애 주입으로 Spot 중단 시 작업 유실 없는지.
- **비용 영향:** EC2 Spot 최대 90%(AWS 문구), Fargate Spot 최대 70%(설계 S22), GKE Autopilot Spot vCPU $0.0133 vs 일반 $0.0445(−70%, us-central1).
- **출처:** https://aws.amazon.com/ec2/spot/ ; https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-capacity-providers.html ; https://cloud.google.com/kubernetes-engine/pricing

### COST-026 Spot을 단일 태스크·상태 있는 워크로드에 사용 (과소 방향)
- **무엇/왜:** Fargate Spot은 용량이 없으면 온디맨드로 대체하지 않고 대기한다. 태스크 1개 서비스는 중단 시 용량이 돌아올 때까지 멈춘다.
- **실패 양상:** 비용 아끼려다 서비스 중단.
- **신호:** 🟢 `FARGATE_SPOT` weight만 있고 `FARGATE` base 없음 + `desired_count = 1` / 🟢 StatefulSet이 Spot 노드에 / 🟢 DB·브로커가 Spot
- **관련 수준:** D≥1이면 상태 있는 워크로드의 Spot 금지. T≥1 웹 서비스는 온디맨드 base ≥ 1.
- **처방:** `capacity_provider_strategy`에 FARGATE base=1 + FARGATE_SPOT weight / k8s는 nodeAffinity로 상태 있는 Pod를 온디맨드에.
- **검증:** P4 Spot 중단 주입.
- **비용 영향:** 장애 비용이 절감액을 압도.
- **출처:** https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-capacity-providers.html ("Fargate doesn't replace Spot capacity with on-demand capacity", "A service with only one task is interrupted until capacity is available")

### COST-027 RDS·ElastiCache 예약 노드 미검토
- **무엇/왜:** DB와 캐시는 오토스케일이 거의 없어 24시간 상시 → 예약 할인 효과가 가장 확실한 곳.
- **실패 양상:** 1년 이상 운영할 DB를 온디맨드로.
- **신호:** 🔴 예약 보유 여부 / 🟢 production DB 인스턴스 존재
- **관련 수준:** D≥1 production DB.
- **처방:** 운영 6개월 이상 안정되면 1년 예약 권고. 크기를 바꿀 계획이면 보류.
- **검증:** Price List RDS·ElastiCache Reserved 단가.
- **비용 영향:** ElastiCache 예약 최대 48.2%(선결제 없음)~55%(전액 선결제). RDS 예약 단가는 가격 API로 조회(이번 작업에서는 미확인).
- **출처:** https://aws.amazon.com/elasticache/pricing/

### COST-028 Cloud Run 과금 방식(요청 기반 vs 인스턴스 기반) 선택
- **무엇/왜:** 요청 기반은 요청 처리 중에만 과금(단가 높음), 인스턴스 기반은 인스턴스 수명 전체 과금(단가 낮음). 트래픽이 꾸준히 높으면 인스턴스 기반이 싸고, 간헐적이면 요청 기반이 싸다.
- **실패 양상:** 상시 바쁜 서비스를 요청 기반으로 두면 33% 비싼 단가. 반대로 한산한 서비스를 인스턴스 기반 + min 인스턴스로 두면 유휴비 지불.
- **신호:** 🟢 `run.googleapis.com/cpu-throttling: "false"` 또는 Terraform `cpu_idle = false`(인스턴스 기반) / 🟢 백그라운드 작업(요청 밖 CPU 필요) 존재
- **관련 수준:** T≥2 & 꾸준한 트래픽 → 인스턴스 기반 검토. T≤1 간헐 → 요청 기반.
- **처방:** 티어 1: P4 트래픽 프로필로 두 방식 견적 비교.
- **검증:** 활성 시간 비율 = 요청 처리 중 인스턴스 시간 / 전체 인스턴스 시간. us-central1 기준 활성 비율이 약 75%를 넘으면 인스턴스 기반이 유리($0.000018/$0.000024).
- **비용 영향:** us-central1 vCPU 요청 기반 $0.000024/초 + 요청 $0.40/100만 vs 인스턴스 기반 $0.000018/초. 1 vCPU·512MiB 상시 인스턴스 기반 = 월 약 $49.9.
- **출처:** https://cloud.google.com/run/pricing ; 설계 S2(billing-settings)

### COST-029 과약정 (약정이 실사용을 넘음)
- **무엇/왜:** Savings Plans·CUD·RI는 사용하지 않아도 약정액을 낸다. 아키텍처 전환(티어 2→1, x86→ARM) 계획과 충돌하면 손해다.
- **실패 양상:** 약정 직후 티어를 바꾸거나 right-sizing을 해서 미사용 약정이 남음.
- **신호:** 🔴 약정 정보는 청구 데이터에만 / 🟡 이번 리포트가 티어 변경·right-sizing을 처방함
- **관련 수준:** 모든 축소 처방과 함께 경고.
- **처방:** "right-sizing·티어 결정 → 2~3개월 안정 → 약정" 순서. EC2 Instance SP·표준 RI보다 Compute SP·Flexible CUD(전환 유연)를 우선.
- **검증:** Cost Explorer 약정 사용률(utilization).
- **비용 영향:** 미사용 약정액 = 순손실. GCP 약정은 구매 후 취소 불가.
- **출처:** https://docs.cloud.google.com/compute/docs/instances/committed-use-discounts-overview ("You can't cancel a commitment after its purchase"); https://aws.amazon.com/savingsplans/compute-pricing/

---

## D. 데이터 전송 함정

### COST-030 인터넷 이그레스 (서울은 미국보다 비쌈)
- **무엇/왜:** 클라우드에서 인터넷으로 나가는 트래픽은 GB당 과금이고 서울 단가는 미국 리전보다 높다. 이미지·동영상·대용량 다운로드가 있는 앱은 이그레스가 컴퓨트보다 커진다.
- **실패 양상:** 사용자 업로드 이미지를 S3에서 직접 서빙 → 트래픽 증가에 비례해 청구 폭증.
- **신호:** 🟢 S3 버킷 퍼블릭 읽기·presigned GET 다수 / 🟢 앱이 파일 스트리밍(`send_file`, `res.download`) / 🟡 미디어 업로드 기능 / 🔴 월간 전송량
- **관련 수준:** T 수준과 비례. T≥2 + 미디어면 CDN 필수.
- **처방:** 티어 0: 플랫폼 CDN 활용 / 티어 1·2: CloudFront·Cloud CDN 앞단(COST-034), 이미지 리사이즈·압축.
- **검증:** P4에서 응답 바이트 측정 × 가정 트래픽; 청구서 DataTransfer-Out-Bytes.
- **비용 영향:** 서울 EC2·S3 → 인터넷 $0.126/GB(첫 10TB, 전역 무료 등급 이후), 다음 40TB $0.122. 1TB = 약 $126. CloudFront Asia Pacific 구간 $0.120/GB.
- **출처:** [PL] AWSDataTransfer `APN2-DataTransfer-Out-Bytes`; [PL] AmazonCloudFront `AP-DataTransfer-Out-Bytes`

### COST-031 NAT 경유 S3·ECR 접근 (게이트웨이 엔드포인트 미사용)
- **무엇/왜:** 프라이빗 서브넷의 앱이 S3를 NAT로 접근하면 GB당 NAT 처리비가 붙는다. S3 게이트웨이 엔드포인트는 무료다. ECR 이미지 pull도 레이어가 S3에서 오므로 같은 효과가 있다.
- **실패 양상:** 노드가 이미지 pull·S3 백업으로 월 2TB를 NAT 경유 → 서울 약 $121 불필요 지출.
- **신호:** 🟢 `aws_nat_gateway` 있고 `aws_vpc_endpoint`(service_name `*.s3`, type Gateway) 없음 / 🟢 앱이 S3 SDK 사용 / 🟢 EKS·ECS 프라이빗 서브넷
- **관련 수준:** 수준 무관. 거의 항상 이득.
- **처방:** 티어 2·1(ECS): S3 게이트웨이 엔드포인트 추가(라우트 테이블 연결), ECR은 인터페이스 엔드포인트 비용과 NAT 처리비 비교.
- **검증:** VPC Flow Logs 또는 NAT `BytesOutToDestination`에서 S3 접두사 비중.
- **비용 영향:** 서울 NAT 처리 $0.059/GB를 0으로. 게이트웨이 엔드포인트는 "no additional charge".
- **출처:** https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints-s3.html ; [PL] AmazonEC2 `APN2-NatGateway-Bytes`

### COST-032 AZ 간 전송 (chatty 서비스, DB·캐시 교차 AZ)
- **무엇/왜:** 같은 리전이라도 AZ를 넘는 트래픽은 양방향 각각 과금된다. 마이크로서비스 간 호출, 앱↔캐시, 앱↔DB가 AZ를 넘으면 쌓인다.
- **실패 양상:** 서비스 간 월 10TB 교차 AZ = 약 $200(양방향). 로그·메트릭 수집기가 다른 AZ로 보내도 마찬가지.
- **신호:** 🟢 `topologySpreadConstraints`로 분산 + Service에 `trafficDistribution`/topology-aware routing 없음 / 🟢 캐시·DB가 단일 AZ인데 앱은 다중 AZ / 🟡 서비스 간 호출이 많은 구조
- **관련 수준:** D≥2면 교차 AZ 분산은 필요한 비용(줄이지 말고 라우팅만 최적화). D≤1이면 단일 AZ도 선택지.
- **처방:** 티어 2: 존 인지 라우팅(설계 COST-003), 수집기 DaemonSet은 같은 노드로 / 티어 1: 플랫폼이 관리.
- **검증:** VPC Flow Logs AZ 쌍별 바이트; 청구서 `DataTransfer-Regional-Bytes`.
- **비용 영향:** 서울 $0.01/GB(방향별). GCP 같은 리전 다른 존 $0.01/GiB.
- **출처:** [PL] AWSDataTransfer `APN2-DataTransfer-Regional-Bytes`; https://cloud.google.com/vpc/network-pricing ; 설계 S25

### COST-033 리전 간 전송 (복제·백업 복사·멀티 리전)
- **무엇/왜:** 리전 간 복제(S3 CRR, DB 리전 간 복제본, 스냅샷 복사)는 GB당 전송료가 붙고, 대상 리전에 저장비도 이중으로 든다.
- **실패 양상:** D≤1 앱에 S3 CRR + 크로스 리전 읽기 복제본 → 저장비 2배 + 전송비.
- **신호:** 🟢 `aws_s3_bucket_replication_configuration` 대상 다른 리전 / 🟢 `aws_db_instance.replicate_source_db`가 다른 리전 ARN / 🟢 `aws_rds_global_cluster` / 🟢 provider alias 여러 리전
- **관련 수준:** D≤2면 과잉(설계 COST-007). D=3에서만 정당.
- **처방:** D≤2: 같은 리전 백업 + 필요 시 백업만 주기적으로 다른 리전 복사(전체 복제 대신) / D=3: 유지하고 비용 표시.
- **검증:** 복제 바이트 지표 × 단가.
- **비용 영향:** 서울 → 도쿄·버지니아 등 $0.080/GB.
- **출처:** [PL] AWSDataTransfer `APN2-APN1-AWS-Out-Bytes`, `APN2-USE1-AWS-Out-Bytes`

### COST-034 CDN 부재 또는 CDN 요금제 선택
- **무엇/왜:** 정적 자산·이미지를 오리진에서 직접 내보내면 이그레스·컴퓨트 둘 다 든다. CloudFront는 AWS 오리진에서의 전송이 무료이고, 2025년 이후 정액(flat-rate) 요금제가 생겨 초과 과금 없이 쓸 수 있다.
- **실패 양상:** CDN 없이 피크를 오리진이 받아 컴퓨트 증설 + 이그레스 과금.
- **신호:** 🟢 `aws_cloudfront_distribution`·`google_compute_backend_bucket(enable_cdn)` 없음 + 정적 자산·업로드 서빙 / 🟢 캐시 헤더(`Cache-Control`) 미설정
- **관련 수준:** T≥2면 필수에 가까움(T-CTL-004와 연결). T≤1이어도 미디어가 크면 권장.
- **처방:** 티어 0: Vercel·Netlify는 내장 CDN / 티어 1·2: CloudFront 앞단, 트래픽이 예측되면 정액 요금제 검토.
- **검증:** 캐시 적중률, 오리진 바이트 감소량.
- **비용 영향:** CloudFront 정액 Free $0(요청 100만·100GB), Pro $15/월(요청 1천만·50TB), Business $200/월, "no overage charges". 종량제 Asia Pacific $0.120/GB(첫 10TB), HTTP 요청 $0.0090/1만. AWS 오리진→CloudFront 전송 무료.
- **출처:** https://aws.amazon.com/cloudfront/pricing/ ; [PL] AmazonCloudFront; [PL] AWSDataTransfer `APN2-CloudFront-Out-Bytes` $0.00

### COST-035 컨테이너 이미지 pull 트래픽 (큰 이미지, 외부 레지스트리)
- **무엇/왜:** 노드가 자주 교체되거나 스케일 아웃할 때마다 이미지를 받는다. 이미지가 크고 Docker Hub 등 외부 레지스트리면 NAT 처리비 + 콜드 스타트 지연.
- **실패 양상:** 2GB 이미지 × 하루 100회 pull = 월 6TB NAT 경유 → 약 $354.
- **신호:** 🟢 Dockerfile 멀티 스테이지 없음, `FROM` 큰 베이스(full OS, CUDA) / 🟢 매니페스트 이미지가 `docker.io/...` / 🟢 `imagePullPolicy: Always`
- **관련 수준:** T≥2(잦은 스케일 아웃)일수록 영향 큼.
- **처방:** 멀티 스테이지·slim/distroless, 같은 리전 ECR/Artifact Registry로 미러, `IfNotPresent`.
- **검증:** 이미지 크기 × pull 횟수.
- **비용 영향:** NAT 처리 서울 $0.059/GB; 같은 리전 ECR→EC2 전송은 무료로 알려짐(이번 작업에서 미확인).
- **출처:** [PL] AmazonEC2 NAT 단가. 나머지는 일반 원칙(출처 미확인). ⚠️근거없음

### COST-036 GCP 네트워크 등급 (Premium 기본)
- **무엇/왜:** GCP 인터넷 이그레스는 기본이 Premium Tier이고, Standard Tier는 공용 인터넷을 써서 더 싸다. 사용자 대부분이 같은 국가면 Standard로 충분할 수 있다.
- **실패 양상:** 한국 사용자만 있는 서비스에 Premium 이그레스 단가 지불.
- **신호:** 🟢 `google_compute_global_address`·포워딩 규칙 `network_tier` 미지정(PREMIUM) / 🟡 UI 언어·통화가 단일 국가
- **관련 수준:** T≤2, 단일 국가 사용자.
- **처방:** 티어 2(GKE)·GCE: Standard Tier 검토(리전 LB 필요) / Cloud Run은 해당 제약 확인 필요.
- **검증:** Billing Catalog API로 두 등급 asia-northeast3 SKU 비교.
- **비용 영향:** "Standard Tier ... is more economical than Premium Tier"(공식 문구). 구체 단가는 이번 작업에서 미확인.
- **출처:** https://cloud.google.com/vpc/network-pricing

### COST-037 퍼블릭 IP로 같은 리전 서비스 호출 (내부 경로 미사용)
- **무엇/왜:** 같은 VPC·리전인데 퍼블릭 엔드포인트(EIP, 퍼블릭 LB 주소)로 호출하면 AZ 내라도 리전 내 전송료가 붙거나 NAT를 탄다.
- **실패 양상:** 서비스 간 호출을 퍼블릭 도메인으로 해서 NAT·전송비 이중 과금.
- **신호:** 🟢 앱 설정에 내부 서비스 URL이 퍼블릭 도메인(`https://api.example.com`)으로 / 🟢 k8s 서비스 간 호출이 Ingress 호스트 경유
- **관련 수준:** 수준 무관.
- **처방:** 클러스터 내부 DNS(`svc.cluster.local`), 프라이빗 LB, Cloud Run 내부 ingress.
- **검증:** Flow Logs.
- **비용 영향:** 서울 "using elastic IPs or ELB" 리전 전송 $0.01/GB + NAT 경유 시 $0.059/GB.
- **출처:** [PL] AWSDataTransfer `APN2-DataTransfer-Regional-Bytes` 설명문("in/out/between EC2 AZs or using elastic IPs or ELB")

### COST-038 업로드를 앱 서버 경유 (presigned URL 미사용)
- **무엇/왜:** 사용자 업로드를 앱 서버가 받아 S3에 다시 올리면, 앱 컴퓨트 시간·메모리·LB LCU·(NAT 경유 시) 처리비가 모두 든다. 플랫폼 함수는 본문 크기 제한(4.5MB)도 있다.
- **실패 양상:** 대용량 업로드 시 함수 실행 시간 과금 + 실패.
- **신호:** 🟢 multer·`request.files`로 받아서 `putObject` / 🟢 업로드 라우트가 서버리스 함수
- **관련 수준:** T≥1 & 업로드 기능.
- **처방:** 모든 티어: presigned PUT/POST로 클라이언트 → 스토리지 직접 업로드.
- **검증:** 업로드 경로 실행 시간·바이트.
- **비용 영향:** 데이터 인바운드 자체는 무료($0.000/GB), 절감은 컴퓨트·NAT 쪽.
- **출처:** [PL] AWSDataTransfer `APN2-DataTransfer-In-Bytes` $0; 설계 S27(Vercel 4.5MB). 패턴 자체는 일반 원칙(출처 미확인). ⚠️근거없음

---

## E. 스토리지·레지스트리

### COST-039 EBS gp2 → gp3
- **무엇/왜:** gp3는 GB당 단가가 gp2보다 약 20% 낮고, 크기와 무관하게 3,000 IOPS·125 MiB/s 기본 성능을 준다. Elastic Volumes로 중단 없이 바꿀 수 있다.
- **실패 양상:** 오래된 템플릿·AMI 기본값으로 gp2를 계속 써서 매달 20% 더 냄. IOPS를 위해 볼륨을 키우는 낭비도 동반.
- **신호:** 🟢 `aws_ebs_volume.type = "gp2"` / 🟢 `root_block_device { volume_type = "gp2" }` / 🟢 `launch_template` `block_device_mappings.ebs.volume_type = "gp2"` / 🟢 k8s StorageClass `type: gp2` 또는 EKS 기본 `gp2` StorageClass 사용 / 🟢 RDS `storage_type = "gp2"`
- **관련 수준:** 수준 무관. 거의 항상 이득.
- **처방:** 티어 2: StorageClass gp3 기본화, 노드 루트 볼륨 gp3 / RDS `storage_type = "gp3"`.
- **검증:** Price List 두 단가 비교, Infracost diff.
- **비용 영향:** 서울 EBS gp2 $0.114/GB-월 vs gp3 $0.0912(−20%). 1TB면 월 약 $23 절감. RDS PostgreSQL은 서울 gp2·gp3 모두 $0.131/GB-월(단가 동일, 대신 gp3는 기본 IOPS 분리).
- **출처:** [PL] AmazonEC2 `APN2-EBS:VolumeUsage.gp2/.gp3`, [PL] AmazonRDS `APN2-RDS:GP2-Storage/GP3-Storage`; https://aws.amazon.com/blogs/storage/migrate-your-amazon-ebs-volumes-from-gp2-to-gp3-and-save-up-to-20-on-costs/

### COST-040 프로비저닝 IOPS(io1/io2) 과잉
- **무엇/왜:** io1/io2는 GB당 + IOPS당 과금이다. gp3로 충분한 부하(1.6만 IOPS 이하)에 io2를 쓰면 IOPS 요금이 본체보다 커진다.
- **실패 양상:** RDS io1 1만 IOPS(Multi-AZ) = 서울 IOPS 요금만 월 $2,400.
- **신호:** 🟢 `storage_type = "io1"/"io2"`, `iops = N` / 🟢 `aws_ebs_volume.type = "io2"`
- **관련 수준:** T≤2이고 측정된 IOPS가 gp3 범위면 과잉.
- **처방:** gp3 + 필요한 만큼 추가 IOPS(서울 EBS $0.0057/IOPS-월, RDS gp3 $0.023/IOPS-월).
- **검증:** CloudWatch `ReadIOPS`/`WriteIOPS` P99.
- **비용 영향:** 서울 RDS PostgreSQL io1 IOPS $0.108/IOPS-월(Single-AZ), $0.24(Multi-AZ); io1 저장 $0.135/GB-월. EBS io2 $0.0666/IOPS-월.
- **출처:** [PL] AmazonRDS, AmazonEC2

### COST-041 분리된(unattached) 디스크·고아 PV
- **무엇/왜:** 인스턴스·Pod를 지워도 볼륨은 남는다. k8s PV의 `reclaimPolicy: Retain`이나 `deleteOnTermination = false`는 고아 디스크를 만든다.
- **실패 양상:** 테스트용 PVC를 지웠는데 EBS가 수십 개 남아 매달 과금.
- **신호:** 🟢 StorageClass `reclaimPolicy: Retain` / 🟢 `delete_on_termination = false` / 🔴 실제 고아 볼륨(계정 조회 필요)
- **관련 수준:** D≥1 데이터 볼륨은 Retain이 정당할 수 있음(실수 삭제 방지). 스크래치·캐시 볼륨은 Delete.
- **처방:** 볼륨 용도별 StorageClass 분리, 정기 고아 볼륨 점검(`describe-volumes --filters Name=status,Values=available`).
- **검증:** 계정 조회 또는 AWS Compute Optimizer·Trusted Advisor(이번 작업에서 미확인).
- **비용 영향:** 서울 gp3 $0.0912/GB-월. 100GB 볼륨 20개 = 월 약 $182.
- **출처:** [PL] AmazonEC2. 점검 방법은 일반 원칙(출처 미확인). ⚠️근거없음

### COST-042 스냅샷·백업 누적 (보존 정책 없음)
- **무엇/왜:** 수동 스냅샷과 AMI 스냅샷은 자동 삭제되지 않는다. 자동 백업 보존 기간을 넘는 수동 스냅샷이 해마다 쌓인다.
- **실패 양상:** 매일 수동 스냅샷 스크립트 + 삭제 없음 → 1년 뒤 스냅샷 비용이 볼륨 비용을 넘음.
- **신호:** 🟢 `aws_ebs_snapshot`·`aws_db_snapshot` 생성 스크립트·Lambda에 삭제 로직 없음 / 🟢 `aws_dlm_lifecycle_policy` 없음 / 🟢 AWS Backup `lifecycle { delete_after }` 없음 / 🟢 RDS `backup_retention_period` 35(최대)인데 D≤1
- **관련 수준:** D≥1에는 보존 7일 이상 필수(D-CTL-001), D L1 가정 RPO 24시간이면 7~14일로 충분. 그 이상은 규제 신호가 있을 때만.
- **처방:** DLM·AWS Backup 수명 주기, 오래된 스냅샷은 Archive 티어(90일 이상 보관 시).
- **검증:** 스냅샷 총량 GB; Price List.
- **비용 영향:** 서울 EBS 스냅샷 $0.05/GB-월, 아카이브 $0.0125/GB-월(90일 미만 삭제 시 조기 삭제 요금). RDS 무료 할당 초과 백업 $0.095/GB-월, Aurora 백업 $0.023/GB-월.
- **출처:** [PL] AmazonEC2 `APN2-EBS:SnapshotUsage`, `APN2-EBS:SnapshotArchiveStorage`; [PL] AmazonRDS `APN2-RDS:ChargedBackupUsage`, `APN2-Aurora:BackupUsage`

### COST-043 오브젝트 스토리지 클래스·수명 주기 정책 부재
- **무엇/왜:** 로그·백업·오래된 업로드를 Standard에 영원히 두면 비싸다. 접근 패턴이 명확하면 수명 주기로 IA·Glacier로 옮기고, 불명확하면 Intelligent-Tiering.
- **실패 양상:** 몇 년 치 로그·백업이 Standard에 남아 저장비가 선형 증가.
- **신호:** 🟢 `aws_s3_bucket_lifecycle_configuration` 없음 / 🟢 버킷 이름·접두사가 `logs/`, `backup/`, `archive/` / 🟢 GCS `lifecycle_rule` 없음
- **관련 수준:** D 수준이 정하는 보존 기간 이후는 삭제, 보존 기간 안에서는 저렴한 클래스로.
- **처방:** 로그: 30일 후 IA·90일 후 Glacier IR·보존 기간 후 Expire / 사용자 업로드: Intelligent-Tiering 검토.
- **검증:** S3 Storage Lens·버킷 크기 지표 × 클래스별 단가.
- **비용 영향:** 서울 S3 Standard $0.025/GB-월(첫 50TB), Intelligent-Tiering IA 계층 $0.0138, Glacier Instant Retrieval $0.005, Glacier Flexible $0.0045. GCS(us-central1) Standard 약 $0.020/GiB-월, Nearline 약 $0.010, Coldline 약 $0.004, Archive 약 $0.0012(시간당 단가 × 730).
- **출처:** [PL] AmazonS3; https://cloud.google.com/storage/pricing ; https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-transition-general-considerations.html

### COST-044 최소 보관 기간·작은 객체 전환의 역효과
- **무엇/왜:** IA·Glacier 계열은 최소 보관 기간이 있어 일찍 지우면 남은 기간 요금을 낸다. 128KB 미만 작은 객체는 전환 요청비가 절감액보다 크고, Glacier는 객체당 40KB 메타데이터 오버헤드가 붙는다.
- **실패 양상:** 7일 뒤 지울 임시 파일을 IA로 옮겨 30일치 요금, 수백만 개 썸네일을 Glacier로 옮겨 요청비 폭탄.
- **신호:** 🟢 수명 주기 `transition` 일수 < 30(IA) 또는 < 90(Glacier IR) 후 곧 `expiration` / 🟢 `ObjectSizeGreaterThan` 필터 없이 작은 객체 접두사 전환 / 🟡 썸네일·JSON 이벤트 등 작은 객체 다수
- **관련 수준:** 수준 무관.
- **처방:** 짧게 살 데이터는 Standard에서 바로 만료, 작은 객체는 묶거나 크기 필터.
- **검증:** S3 Inventory 객체 크기 분포.
- **비용 영향:** 서울 IA 조기 삭제 $0.0138/GB-월 비례, Glacier IR 90일 미만 $0.005/GB-월 비례, Glacier IR 전환 요청 $0.02/1,000건. GCS 최소 보관 Nearline 30일·Coldline 90일·Archive 365일.
- **출처:** https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-transition-general-considerations.html ; [PL] AmazonS3 `APN2-EarlyDelete-*`, `APN2-Requests-Tier4`; https://cloud.google.com/storage/pricing

### COST-045 완료되지 않은 멀티파트 업로드·이전 버전 누적
- **무엇/왜:** 중단된 멀티파트 업로드 조각과 버전 관리 버킷의 이전 버전은 보이지 않는 곳에서 저장비를 낸다.
- **실패 양상:** 대용량 업로드 실패가 반복되는 앱에서 수백 GB 조각이 누적. 버전 관리를 켜고 덮어쓰기가 잦으면 저장량 배수 증가.
- **신호:** 🟢 수명 주기에 `abort_incomplete_multipart_upload` 없음 / 🟢 `aws_s3_bucket_versioning { status = "Enabled" }` + `noncurrent_version_expiration` 없음
- **관련 수준:** D≥1이면 버전 관리 자체는 정당(실수 삭제 복구). 이전 버전 만료 기간만 붙인다.
- **처방:** `AbortIncompleteMultipartUpload` 7일 + 이전 버전 30일(D 수준에 맞춰) 만료.
- **검증:** S3 Storage Lens 이전 버전·미완료 업로드 바이트.
- **비용 영향:** Standard 단가 그대로 과금(서울 $0.025/GB-월). AWS는 "minimize your storage costs" 위해 해당 규칙을 모범 사례로 권장.
- **출처:** https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpu-abort-incomplete-mpu-lifecycle-config.html ; [PL] AmazonS3

### COST-046 컨테이너 레지스트리 이미지 누적 (수명 주기 정책 없음)
- **무엇/왜:** CI가 커밋마다 이미지를 푸시하면 레지스트리 용량이 계속 늘어난다. 태그 없는 이미지도 남는다.
- **실패 양상:** 하루 20번 배포 × 500MB = 월 300GB 증가 → 1년 뒤 월 수백 달러.
- **신호:** 🟢 `aws_ecr_repository` 있고 `aws_ecr_lifecycle_policy` 없음 / 🟢 Artifact Registry `cleanup_policies` 없음 / 🟢 CI가 `:${GITHUB_SHA}` 태그로 푸시
- **관련 수준:** U≥2면 롤백용으로 최근 N개(예: 10~30개) 보존 필요. 그 이상은 낭비.
- **처방:** ECR 수명 주기 `imageCountMoreThan` + untagged `sinceImagePushed` 만료 / Artifact Registry 정리 정책.
- **검증:** 레포별 저장 GB.
- **비용 영향:** 서울 ECR $0.10/GB-월(아카이브 $0.10→$0.07, 조회 $0.03/GB). Artifact Registry는 0.5GiB 무료 후 과금(단가 표는 이번에 미확인).
- **출처:** [PL] AmazonECR; https://docs.aws.amazon.com/AmazonECR/latest/userguide/LifecyclePolicies.html ; https://cloud.google.com/artifact-registry/pricing

### COST-047 S3 요청 요금 (작은 객체·LIST 남발)
- **무엇/왜:** S3는 저장비 외에 요청당 과금한다. 작은 객체를 대량으로 쓰거나 LIST를 폴링하면 요청비가 저장비를 넘는다.
- **실패 양상:** 이벤트를 객체 하나씩 PUT(초당 100건) → 월 약 2.6억 건 → PUT 요금만 월 약 $1,170.
- **신호:** 🟢 루프 안 `putObject`/`upload_fileobj` / 🟢 주기적 `listObjectsV2` 폴링 / 🟡 S3를 큐·DB처럼 사용
- **관련 수준:** T≥2에서 영향 큼.
- **처방:** 배치로 묶어 쓰기, 이벤트는 큐·스트림, LIST 대신 이벤트 알림.
- **검증:** CloudWatch 요청 지표 × 단가.
- **비용 영향:** 서울 PUT·COPY·POST·LIST $0.0045/1,000건, GET $0.0035/10,000건.
- **출처:** [PL] AmazonS3 `APN2-Requests-Tier1`, `APN2-Requests-Tier2`

---

## F. DB·캐시

### COST-048 DB 인스턴스 크기 과대
- **무엇/왜:** DB는 "혹시 몰라" 크게 잡기 쉽고, 오토스케일이 없어 과대분이 24시간 과금된다.
- **실패 양상:** 사용자 100명 앱에 db.r7g.large(서울 월 약 $209) — db.t4g.small(월 약 $37)로 충분.
- **신호:** 🟢 `instance_class`, Cloud SQL `tier` / 🟡 도메인 가정(T L1 평시 50동시) 대비 크기 / 🔴 CPU·메모리 실측
- **관련 수준:** T≤1이면 버스터블(t4g) 소형이 기본, T≥2면 측정 후 결정.
- **처방:** 티어 1·2: P4 실측(CPU P95 < 40%, 버퍼 캐시 적중률)으로 한 단계씩 축소 / 티어 0: Supabase compute 애드온 단계 조정.
- **검증:** CloudWatch `CPUUtilization`, `FreeableMemory`; Cloud SQL 지표.
- **비용 영향:** 서울 RDS PostgreSQL Single-AZ 시간 단가 db.t4g.micro $0.025 / t4g.small $0.051 / t4g.medium $0.102 / m7g.large $0.2344 / r7g.large $0.2869. Cloud SQL(us-central1) vCPU $0.0413/시간 + 메모리 $0.007/GiB-시간, db-f1-micro $0.0105/시간.
- **출처:** [PL] AmazonRDS; https://cloud.google.com/sql/pricing

### COST-049 Multi-AZ·HA는 인스턴스·스토리지 2배
- **무엇/왜:** RDS Multi-AZ(대기 1개)와 Cloud SQL HA는 인스턴스 시간과 스토리지 단가가 정확히 약 2배다. D≥2에만 필요하다.
- **실패 양상:** D≤1 앱(사내 도구, 데모)에 Multi-AZ → DB 비용 2배.
- **신호:** 🟢 `aws_db_instance.multi_az = true` / 🟢 Cloud SQL `availability_type = "REGIONAL"` / 🟢 Multi-AZ DB 클러스터(`db_cluster_instance_class`, 읽기 가능 대기 2개)
- **관련 수준:** D≤1이면 과잉. D≥2 또는 C=3이면 필수(COST-096).
- **처방:** D≤1: Single-AZ + 자동 백업·PITR(D-CTL-001로 RPO 충족) / D≥2: 유지.
- **검증:** Price List로 두 배포 옵션 단가.
- **비용 영향:** 서울 db.t4g.micro $0.025 → $0.051, db.r7g.large $0.2869 → $0.5738(월 약 $209 → $419), gp3 스토리지 $0.131 → $0.262/GB-월. Multi-AZ DB 클러스터(읽기 가능 대기 2개) gp3 $0.393/GB-월. Cloud SQL HA vCPU $0.0413 → $0.0826, db-f1-micro $0.0105 → $0.021.
- **출처:** [PL] AmazonRDS; https://cloud.google.com/sql/pricing ("HA prices are applied for instances configured for high availability")

### COST-050 읽기 복제본 과다 (트래픽 근거 없음)
- **무엇/왜:** 읽기 복제본은 원본과 같은 인스턴스 요금을 낸다. 읽기 부하 근거 없이 "확장성" 명목으로 두는 경우가 많다. 비동기라 정합성 위험도 있다(S11).
- **실패 양상:** 복제본 2개 = DB 비용 3배, 실제 읽기 분산 코드도 없음.
- **신호:** 🟢 `replicate_source_db` 리소스 개수 / 🟢 Aurora 리더 인스턴스 수 / 🟢 앱에 읽기 전용 엔드포인트 설정 없음(복제본을 아무도 안 씀)
- **관련 수준:** T≤1이면 과잉. T≥2에서도 캐시(T-CTL-004)가 먼저. C=3 쓰기 직후 읽기는 원본에서(C-CTL-006).
- **처방:** 앱이 복제본을 실제로 쓰는지 확인 → 안 쓰면 삭제, 쓰면 캐시와 비용 비교.
- **검증:** 복제본 `DatabaseConnections`, `ReadIOPS`.
- **비용 영향:** 복제본당 원본 Single-AZ 단가와 동일(Cloud SQL: "Read replicas ... are charged at the same rate as stand-alone instances").
- **출처:** https://cloud.google.com/sql/pricing ; 설계 S11

### COST-051 Aurora Standard vs I/O-Optimized 선택
- **무엇/왜:** Aurora Standard는 I/O 요청마다 과금, I/O-Optimized는 I/O 무료 대신 인스턴스·스토리지 단가가 높다. AWS 기준선은 "I/O 지출이 전체의 25% 이상이면 I/O-Optimized".
- **실패 양상:** I/O가 적은 앱에 I/O-Optimized → 인스턴스 30%·스토리지 2.25배 더 냄. 반대로 I/O 폭증 앱에 Standard → 예측 불가 청구.
- **신호:** 🟢 `aws_rds_cluster.storage_type = "aurora-iopt1"`(I/O-Optimized) 또는 미지정(Standard) / 🔴 I/O 비중(청구 데이터)
- **관련 수준:** 수준 무관. 실측 기반.
- **처방:** 1개월 청구에서 `StorageIOUsage` 비중 계산 → 25% 기준. Standard → I/O-Optimized 전환은 30일에 한 번만 가능.
- **검증:** Cost Explorer `Aurora:StorageIOUsage` 비중.
- **비용 영향:** 서울 Aurora PostgreSQL db.r7g.large Standard $0.333/시간 vs I/O-Optimized $0.433; 스토리지 $0.12 vs $0.27/GB-월; Standard I/O $0.24/100만 요청. Serverless v2 ACU $0.20 vs $0.26.
- **출처:** https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.Overview.StorageReliability.html ; [PL] AmazonRDS

### COST-052 서버리스 DB 최소 용량 (scale-to-zero 여부)
- **무엇/왜:** Aurora Serverless v2는 최소 ACU를 0으로 두면 유휴 시 일시 정지되어 인스턴스 요금이 0이 된다. 0.5 이상이면 상시 과금. 단, RDS Proxy를 붙이면 프록시가 연결을 유지해 일시 정지가 안 된다.
- **실패 양상:** 개발용 Aurora Serverless를 min 0.5 ACU로 두어 서울 월 약 $73 상시. 또는 auto-pause를 켰는데 RDS Proxy·열린 커넥션 때문에 한 번도 안 멈춤.
- **신호:** 🟢 `serverlessv2_scaling_configuration { min_capacity = 0.5 }` / 🟢 `seconds_until_auto_pause` / 🟢 같은 클러스터에 `aws_db_proxy` / 🟡 앱이 커넥션 풀을 상시 유지
- **관련 수준:** T=0 또는 dev 환경이면 min 0 권장. T≥1 production은 재개 지연(약 15초, 24시간 이상 정지 시 30초 이상)이 허용될 때만.
- **처방:** dev/사내 도구: min 0 + 연결 재시도 / production: min ≥ 평시 필요 ACU.
- **검증:** `ServerlessDatabaseCapacity`가 0인 시간 비율.
- **비용 영향:** 서울 Serverless v2 $0.20/ACU-시간(0.5 ACU 상시 = 월 $73). 정지 중 인스턴스 요금 0, 스토리지는 과금.
- **출처:** https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2-auto-pause.html ; [PL] AmazonRDS `APN2-Aurora:ServerlessV2Usage`

### COST-053 개발·스테이징 DB 상시 가동
- **무엇/왜:** 비운영 DB는 업무 시간에만 필요하다. RDS는 최대 7일 정지할 수 있고(7일 뒤 자동 재시작), 정지 중에도 스토리지·백업·퍼블릭 IPv4는 과금된다.
- **실패 양상:** dev·stg DB가 주 168시간 중 40시간만 쓰이는데 전부 과금.
- **신호:** 🟢 환경 이름(`dev`, `staging`)이 붙은 `aws_db_instance`·Cloud SQL / 🟢 스케줄러(Instance Scheduler, `activation_policy`) 없음
- **관련 수준:** 비운영 환경 전부.
- **처방:** Instance Scheduler on AWS(태그 기반 EC2·RDS 시작/정지), Cloud SQL `activation_policy = NEVER` 스케줄, 또는 Aurora min 0(COST-052).
- **검증:** 환경별 인스턴스 시간.
- **비용 영향:** 주 40시간만 가동 시 인스턴스 비용 약 76% 절감(168→40시간). 정지 중 스토리지·백업·IPv4는 계속 과금.
- **출처:** https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_StopInstance.html ; https://docs.aws.amazon.com/solutions/instance-scheduler-on-aws/

### COST-054 RDS Proxy 비용과 필요성
- **무엇/왜:** RDS Proxy는 원본 DB의 vCPU 수에 비례해 과금된다. 서버리스에서 커넥션 폭증을 막는 데 필요하지만(T-PRE-003), 상시 컨테이너 몇 개에는 앱 내 풀로 충분하다.
- **실패 양상:** 컨테이너 2개짜리 앱에 프록시를 붙여 비용만 증가 + Aurora auto-pause 방해.
- **신호:** 🟢 `aws_db_proxy` / 🟢 컴퓨트가 Lambda·Cloud Run 대량 스케일인지 여부
- **관련 수준:** T≥2 & (최대 인스턴스 × 풀 크기 > max_connections)일 때만 필요(T-CTL-003). 그 외 과잉.
- **처방:** 상시 컨테이너: 앱 풀 크기 조정 / 서버리스·대량 스케일: 프록시 또는 PgBouncer 사이드카.
- **검증:** 최대 커넥션 계산식.
- **비용 영향:** 서울 $0.018/vCPU-시간(db.m7g.large 2 vCPU면 월 약 $26), Serverless v2는 $0.025/ACU-시간.
- **출처:** [PL] AmazonRDS `APN2-RDS:ProxyUsage`; 설계 S8

### COST-055 DB 스토리지 자동 확장 상한과 단방향성
- **무엇/왜:** RDS 스토리지 자동 확장은 늘어나기만 하고 줄지 않는다. 한 번의 대량 임포트·로그 테이블 폭주가 영구 비용이 된다.
- **실패 양상:** 일시적 데이터 폭증으로 1TB까지 늘어난 뒤 데이터를 지워도 1TB 과금 지속(RDS). Aurora는 사용량 기준이라 줄어듦.
- **신호:** 🟢 `max_allocated_storage` 없음 또는 과대 / 🟢 앱이 DB에 로그·이벤트를 무기한 적재(감사 테이블, `events` 테이블 TTL 없음)
- **관련 수준:** 수준 무관.
- **처방:** `max_allocated_storage` 상한, 로그성 데이터는 파티션·TTL·오브젝트 스토리지로.
- **검증:** `FreeStorageSpace` 추이.
- **비용 영향:** 서울 RDS gp3 $0.131/GB-월(Multi-AZ $0.262). 줄일 때는 새 인스턴스로 이전 필요.
- **출처:** Aurora 사용량 기반 축소는 https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.Overview.StorageReliability.html . RDS 비축소 특성은 일반 원칙(출처 미확인, 이번 작업에서 미열람). ⚠️근거없음

### COST-056 캐시 과잉 (T≤1인데 매니지드 Redis)
- **무엇/왜:** 캐시는 T≥2(읽기 많은 경로)의 통제다. 트래픽이 작은 앱에 클러스터 모드·복제본 있는 Redis는 DB보다 비싸질 수 있다.
- **실패 양상:** 사내 도구에 cache.r7g.large 2노드 = 서울 월 약 $383.
- **신호:** 🟢 `aws_elasticache_replication_group.num_cache_clusters ≥ 2`, `cluster_mode` / 🟢 Memorystore `tier = "STANDARD_HA"` / 🟡 캐시 키 사용처가 세션 하나뿐
- **관련 수준:** T≤1이면 과잉(세션 외부화가 목적이면 가장 작은 노드 1개 또는 DB 세션 테이블). T≥2면 정당.
- **처방:** T≤1: cache.t4g.micro 1개 또는 서버리스 Valkey / T≥2: 크기를 메모리 사용량에 맞춤.
- **검증:** `DatabaseMemoryUsagePercentage`, 적중률.
- **비용 영향:** 서울 cache.t4g.micro Redis OSS $0.024/시간(월 $17.5), Valkey $0.0192(월 $14.0), cache.r7g.large Redis $0.262 / Valkey $0.2096.
- **출처:** [PL] AmazonElastiCache

### COST-057 ElastiCache 엔진 선택 (Valkey가 더 쌈)
- **무엇/왜:** 같은 노드 타입에서 Valkey가 Redis OSS보다 약 20% 싸고, 서버리스 최소 과금 저장량도 Valkey 100MB vs Redis OSS 1GB다.
- **실패 양상:** 호환되는 클라이언트로 Redis OSS를 그대로 선택해 20% 추가. 서버리스 Redis OSS는 최소 1GB 과금 때문에 빈 캐시도 월 약 $110.
- **신호:** 🟢 `engine = "redis"` / 🟢 `aws_elasticache_serverless_cache.engine = "redis"`
- **관련 수준:** 수준 무관.
- **처방:** Valkey로 견적(Redis 명령 호환 범위 확인).
- **검증:** Price List 엔진별 단가.
- **비용 영향:** 서울 서버리스 저장 Redis OSS $0.151/GB-시간 × 최소 1GB = 월 약 $110.2, Valkey $0.101/GB-시간 × 최소 0.1GB = 월 약 $7.4(+ECPU 요금).
- **출처:** https://aws.amazon.com/elasticache/pricing/ ; [PL] AmazonElastiCache `APN2-CachedData:Redis/Valkey`

### COST-058 DB를 관리형으로 둘지 vs 컨테이너 안 DB
- **무엇/왜:** 비용을 아끼려고 k8s 안에 Postgres StatefulSet을 두면 인스턴스비는 줄지만 백업·페일오버·업그레이드를 직접 해야 한다. 비용 필터가 이걸 고르면 D 축을 망가뜨린다.
- **실패 양상:** D≥1 데이터를 PVC 하나에 두고 백업 없음 → 노드 장애 시 데이터 유실.
- **신호:** 🟢 `postgres`/`mysql` 이미지를 쓰는 StatefulSet·Deployment / 🟢 docker-compose의 `db` 서비스를 그대로 배포
- **관련 수준:** D=0(임시 데이터)이면 허용. D≥1이면 관리형 또는 검증된 오퍼레이터 + 백업 통제 필수.
- **처방:** D≥1: 관리형 DB 견적을 기본으로, 컨테이너 DB는 dev 전용.
- **검증:** D-CTL-001 충족 여부.
- **비용 영향:** 서울 db.t4g.micro Single-AZ 월 약 $18.3 + 스토리지. 이 정도 차이로 D 수준을 포기할 이유가 드물다.
- **출처:** [PL] AmazonRDS. 판단은 설계 원칙 5("아끼면 안 되는 곳은 규칙이 명시").

### COST-059 Cloud SQL 공유 코어 vs 전용 vCPU
- **무엇/왜:** db-f1-micro·db-g1-small은 매우 싸지만 SLA 대상이 아닌 공유 CPU다. T≤1·D≤1 앱에는 충분하고, D≥2에는 부적합.
- **실패 양상:** 사내 도구에 2 vCPU·8GiB HA(us-central1 월 약 $202) — db-g1-small(월 약 $25.6)로 충분.
- **신호:** 🟢 `google_sql_database_instance.settings.tier`
- **관련 수준:** T≤1 & D≤1이면 공유 코어 권장. D≥2면 전용 vCPU + HA.
- **처방:** 티어 1 GCP 견적에서 수준별 tier 매핑.
- **검증:** Cloud SQL CPU 사용률.
- **비용 영향:** us-central1 db-f1-micro $0.0105/시간(월 $7.7), db-g1-small $0.035(월 $25.6), 전용 2 vCPU·8GiB 약 $0.1386/시간(월 $101), HA 2배. SSD 약 $0.17/GiB-월.
- **출처:** https://cloud.google.com/sql/pricing

### COST-060 Supabase 컴퓨트 애드온·디스크 단계
- **무엇/왜:** Supabase Pro는 Micro 컴퓨트 크레딧($10)을 포함하고, 그 이상은 애드온 요금이다. 디스크는 8GB 포함 후 GB당. 스펜드 캡은 컴퓨트·IPv4·PITR 등을 막지 않는다.
- **실패 양상:** "느려서" Large로 올렸다가 내리지 않아 월 $110 고정. 스펜드 캡을 켜 두었으니 안전하다고 오해.
- **신호:** 🟢 `supabase/config.toml` 또는 Supabase Terraform provider의 `instance_size` / 🟡 프로젝트 수(프로젝트마다 컴퓨트 과금) / 🔴 대시보드 설정
- **관련 수준:** T≤1이면 Micro·Small. T≥2는 P4 측정 후.
- **처방:** 티어 0: 크기 단계 right-sizing, 쓰지 않는 브랜치·프로젝트 정리.
- **검증:** Supabase 사용량 페이지.
- **비용 영향:** 컴퓨트 월 Micro $10 / Small $15 / Medium $60 / Large $110 / XL $210. 디스크 8GB 초과 $0.125/GB. 스펜드 캡 제외 항목: Compute, Branching Compute, Read Replica Compute, Custom Domain, 추가 Disk IOPS/Throughput, IPv4, Log Drain, MFA Phone, PITR.
- **출처:** https://supabase.com/pricing ; https://supabase.com/docs/guides/platform/cost-control

---

## G. 관측 도구 비용

### COST-061 로그 수집 요금 (서울 CloudWatch는 GB당 $0.76)
- **무엇/왜:** 로그는 "수집(ingest)" 단계에서 GB당 과금된다. CloudWatch Logs 서울 단가는 Cloud Logging보다 높고 무료 할당도 작다. 디버그 로그·요청 본문 로깅·헬스체크 로그가 주범이다.
- **실패 양상:** 요청마다 2KB 로그 × 월 1억 요청 = 200GB → 서울 월 약 $152. 디버그 레벨로 배포하면 10배.
- **신호:** 🟢 `LOG_LEVEL=debug`·`logging.level.root=DEBUG`가 production 설정에 / 🟢 요청·응답 본문 로깅 미들웨어(morgan `combined` + body) / 🟢 헬스체크 경로 로그 제외 없음 / 🟢 VPC Flow Logs·ALB 액세스 로그를 CloudWatch로 / 🔴 실제 로그량
- **관련 수준:** 수준 무관. 단 감사·보안 로그는 줄이지 말 것(COST-100).
- **처방:** INFO 기본, 헬스체크 로그 제외, 샘플링, 대량 로그는 Infrequent Access 클래스(서울 $0.38/GB) 또는 S3 직행.
- **검증:** P4 소크 중 로그 바이트/요청 × 가정 트래픽.
- **비용 영향:** 서울 CloudWatch Logs 표준 수집 $0.76/GB, IA $0.38/GB, 보관 $0.0314/GB-월. Cloud Logging $0.50/GiB(프로젝트당 월 50GiB 무료, 30일 보관 포함).
- **출처:** [PL] AmazonCloudWatch `APN2-DataProcessing-Bytes`, `APN2-DataProcessingIA-Bytes`, `APN2-TimedStorage-ByteHrs`; https://cloud.google.com/stackdriver/pricing

### COST-062 로그 보존 기간 기본값 "영구"
- **무엇/왜:** CloudWatch Logs 로그 그룹은 기본적으로 무기한 보관된다. Lambda·ECS가 자동 생성한 로그 그룹도 마찬가지다.
- **실패 양상:** 몇 년 치 로그가 쌓여 보관비가 매달 증가.
- **신호:** 🟢 `aws_cloudwatch_log_group`에 `retention_in_days` 없음 / 🟢 로그 그룹을 Terraform으로 만들지 않음(서비스가 자동 생성 → 영구) / 🟢 Cloud Logging 버킷 `retention_days` > 30
- **관련 수준:** D·보안 요구가 정하는 보존 기간(예: 감사 1년)만큼만. 일반 앱 로그는 14~30일.
- **처방:** 모든 로그 그룹을 IaC로 선언하고 보존 기간 설정, 장기 보관은 S3 Glacier로 내보내기.
- **검증:** `storedBytes` 합계.
- **비용 영향:** 서울 보관 $0.0314/GB-월. Cloud Logging 30일 초과 보존 $0.01/GiB-월.
- **출처:** https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Working-with-log-groups-and-streams.html ("By default, log data is stored in CloudWatch Logs indefinitely"); https://cloud.google.com/stackdriver/pricing

### COST-063 지표 카디널리티 폭발
- **무엇/왜:** 레이블 값 조합마다 별도 시계열이 생긴다. user_id·URL 전체 경로·요청 ID를 레이블로 쓰면 시계열이 무한히 늘어 비용과 저장이 폭발한다.
- **실패 양상:** CloudWatch 커스텀 지표에 user_id 차원 → 사용자 1만 명 = 지표 1만 개 = 서울 월 $3,000. Prometheus는 메모리 폭발.
- **신호:** 🟢 지표 레이블·차원에 `user_id`, `email`, `request_id`, `path`(정규화 없음), `ip` / 🟢 `prom-client`·Micrometer 태그에 동적 값 / 🟢 EMF(`_aws.CloudWatchMetrics`) Dimensions에 고유 ID
- **관련 수준:** 수준 무관.
- **처방:** 경로는 라우트 템플릿(`/users/:id`)으로, 고유 ID는 로그·트레이스로.
- **검증:** 시계열 수(`prometheus_tsdb_head_series`), CloudWatch 지표 수.
- **비용 영향:** 서울 CloudWatch 커스텀 지표 첫 1만 개 $0.30/지표-월, 다음 24만 개 $0.10. GCP Cloud Monitoring $0.258/MiB(150MiB 무료), Managed Prometheus $0.06/100만 샘플.
- **출처:** https://prometheus.io/docs/practices/naming/ ("Do not use labels to store dimensions with high cardinality"); [PL] AmazonCloudWatch `APN2-CW:MetricMonitorUsage`; https://cloud.google.com/stackdriver/pricing

### COST-064 트레이스 100% 샘플링
- **무엇/왜:** 모든 요청을 트레이스하면 스팬 수가 요청 수 × 서비스 수만큼 늘어난다. 샘플링은 가시성을 크게 잃지 않고 비용을 줄이는 가장 효과적인 방법이다.
- **실패 양상:** 월 1억 요청 × 스팬 10개 = 10억 스팬 → Cloud Trace 기준 월 약 $200, 상용 APM은 훨씬 큼.
- **신호:** 🟢 OTel `OTEL_TRACES_SAMPLER=always_on` 또는 `parentbased_always_on`(기본) / 🟢 `traces_sample_rate: 1.0`(Sentry) / 🟢 X-Ray 샘플링 규칙 `fixed_rate = 1`
- **관련 수준:** U≥3(카나리 자동 중단)·D≥3는 오류 트레이스를 놓치면 안 되므로 tail 샘플링(오류·지연은 전부, 정상은 일부).
- **처방:** 헤드 샘플링 1~10% + 오류 트레이스 보존(tail 샘플링은 수집기 운영 비용 고려).
- **검증:** 스팬 수 × 단가.
- **비용 영향:** Cloud Trace $0.20/100만 스팬(월 250만 스팬 무료).
- **출처:** https://opentelemetry.io/docs/concepts/sampling/ ("Sampling is one of the most effective ways to reduce the costs of observability"); https://cloud.google.com/stackdriver/pricing

### COST-065 관측 스택 과잉 (T≤1에 자체 운영 Prometheus·Loki·Grafana 풀스택)
- **무엇/왜:** 작은 앱에 자체 운영 관측 스택을 올리면 그 스택이 앱보다 많은 노드를 먹는다. 설계 §17.4 "필요한 만큼만"과 같은 원칙.
- **실패 양상:** 앱 Pod 2개, 관측 Pod 10개(Prometheus 2·Loki·Grafana·Alertmanager·exporter들) → 노드 1~2대 추가.
- **신호:** 🟢 `kube-prometheus-stack`, `loki`, `tempo` Helm 차트 / 🟢 Prometheus `retention` 길게 + PVC 큼 / 🟡 앱 워크로드 requests 합보다 관측 requests 합이 큼
- **관련 수준:** T≤1 & D≤1이면 매니지드 기본 지표·로그로 충분(과잉). T≥2·U≥2(지표 기반 롤백)면 정당.
- **처방:** 티어 1: 플랫폼 기본 관측 / 티어 2: 매니지드 Prometheus·GKE 기본 지표, 자체 스택은 축소.
- **검증:** namespace별 requests 합.
- **비용 영향:** 추가 노드 수 × 노드 단가(서울 m7g.large 월 약 $73).
- **출처:** 일반 원칙(출처 미확인). 설계 §17.4. ⚠️근거없음

### COST-066 알람·대시보드·합성 모니터링 개수
- **무엇/왜:** CloudWatch 알람·복합 알람·캐너리는 개당 과금이다. 지표마다 알람을 기계적으로 만들면 쌓인다. 비용보다 "알람 피로"가 더 큰 문제.
- **실패 양상:** 알람 500개 = 서울 월 $50 + 노이즈.
- **신호:** 🟢 `aws_cloudwatch_metric_alarm` 개수 / 🟢 `aws_synthetics_canary` 실행 주기 1분
- **관련 수준:** SLO 소진율 알림(설계 S28)으로 대체 가능.
- **처방:** SLO 기반 소수 알람, 캐너리 주기 5~15분.
- **검증:** 알람 수 × 단가.
- **비용 영향:** 서울 표준 알람 $0.10/알람-월, 복합 알람 $0.50, 캐너리 실행 $0.0019/회(1분 주기 = 월 약 $83/캐너리).
- **출처:** [PL] AmazonCloudWatch `APN2-CW:AlarmMonitorUsage`, `APN2-CW:CompositeAlarmMonitorUsage`, `APN2-CW:Canary-runs`

### COST-067 VPC Flow Logs·ALB 액세스 로그 전량 수집
- **무엇/왜:** 네트워크 로그는 양이 매우 많다. CloudWatch로 보내면 벤디드 로그 수집 요금이 붙고, S3로 보내면 훨씬 싸다.
- **실패 양상:** 상시 Flow Logs를 CloudWatch에 전량 → 로그 비용이 컴퓨트를 넘음.
- **신호:** 🟢 `aws_flow_log.log_destination_type = "cloud-watch-logs"` / 🟢 `traffic_type = "ALL"` / 🟢 GCP 서브넷 `log_config` 샘플링 1.0
- **관련 수준:** 보안 요구가 있으면 유지하되 S3 + 수명 주기. 없으면 문제 조사 시에만.
- **처방:** S3 대상 + Parquet + 수명 주기, GCP는 샘플링 비율 축소.
- **검증:** 벤디드 로그 바이트.
- **비용 영향:** 서울 벤디드 로그 CloudWatch 표준 수집 첫 10TB $0.76/GB(IA $0.38). Cloud Logging 벤디드 네트워크 로그 $0.25/GiB(무료 할당 없음).
- **출처:** [PL] AmazonCloudWatch `APN2-VendedLog-Bytes`; https://cloud.google.com/stackdriver/pricing

---

## H. 서버리스·PaaS 비용 곡선과 플랜 한도

### COST-068 서버리스 비용 역전점 (꾸준히 높은 트래픽은 컨테이너가 쌈)
- **무엇/왜:** Lambda·요청 기반 Cloud Run은 낮고 들쭉날쭉한 트래픽에 싸지만, 요청이 꾸준히 많으면 상시 컨테이너가 싸다. 역전점을 계산해 티어 선택에 넣어야 한다.
- **실패 양상:** 하루 종일 바쁜 API를 Lambda로 → 컨테이너 대비 수 배. 반대로 하루 100건 API를 상시 Fargate로 → 고정비 낭비.
- **신호:** 🟢 `aws_lambda_function`·Vercel Functions·Cloud Run 요청 기반 / 🟡 T 가정의 평시 RPS / 🔴 실제 요청 분포
- **관련 수준:** T≥2 & 평시 트래픽 꾸준 → 컨테이너 견적 우선. T≤1·간헐 → 서버리스.
- **처방:** ⑥ 티어 단계에서 두 견적을 함께 계산하고 역전 RPS를 리포트에 표시.
- **검증:** P4 소크 실측 RPS·요청당 실행 시간.
- **비용 영향:** 서울 예시(계산값): Lambda 1GB·100ms = 요청당 약 $0.00000187(컴퓨트 $0.00000167 + 요청 $0.0000002). Fargate 1 vCPU·2GB 1개 = 월 약 $41.4 → 월 약 2,200만 요청(평균 약 8.5 RPS)에서 같아진다. 컨테이너 1개가 그 이상을 동시에 처리할 수 있으면 그 RPS 위로는 컨테이너가 싸다.
- **출처:** [PL] AWSLambda, AmazonECS. 역전점 계산은 이 문서의 계산(일반 원칙). ⚠️근거없음

### COST-069 Vercel 플랜 한도와 초과 과금
- **무엇/왜:** Hobby는 비상업 전용이고 추가 사용량을 살 수 없다(한도 도달 시 제한). Pro는 월 $20 + $20 사용 크레딧 후 종량 과금이다.
- **실패 양상:** 상업 서비스를 Hobby로 운영(약관 위반 + 한도 도달 시 중단). Pro에서 바이럴·봇 트래픽으로 전송량·함수 실행 초과 과금.
- **신호:** 🟢 `vercel.json`, `.vercel/` / 🟢 결제·구독 SDK가 있는데(상업 신호) 플랜 가정 Hobby / 🟡 대용량 정적 자산·동영상을 `public/`에 / 🔴 실제 플랜
- **관련 수준:** C≥1 결제·상업 신호면 Hobby 불가. T≥2면 초과 과금 견적 필수.
- **처방:** 티어 0: Pro + Spend Management(COST-088), 대용량 미디어는 외부 스토리지·CDN.
- **검증:** Vercel Usage 대시보드; 가정 트래픽 × 단가.
- **비용 영향:** Hobby: CDN 요청 100만·Fast Data Transfer 100GB·함수 호출 100만·Active CPU 4시간·Provisioned Memory 360GB-시간/월. Pro: Fast Data Transfer 1TB 포함 후 $0.15/GB부터, CDN 요청 1,000만 포함 후 $2/100만부터, 함수 호출 $0.60/100만부터, Active CPU $0.128/시간부터, 메모리 $0.0106/GB-시간부터.
- **출처:** https://vercel.com/pricing

### COST-070 Vercel 이미지 최적화·ISR·미들웨어 과금
- **무엇/왜:** Next.js `<Image>` 최적화, 짧은 revalidate의 ISR, 모든 경로에 걸린 미들웨어는 요청마다 플랫폼 과금 항목을 만든다.
- **실패 양상:** 사용자 업로드 이미지를 매번 다른 크기로 최적화 → 변환 과금 폭증. `matcher` 없는 미들웨어가 정적 자산 요청까지 실행.
- **신호:** 🟢 `next.config.js` `images.remotePatterns` 와일드카드·`images.unoptimized` 미설정 / 🟢 `export const revalidate = 1` 같은 짧은 값 / 🟢 `middleware.ts`에 `config.matcher` 없음
- **관련 수준:** T≥1.
- **처방:** 티어 0: 이미지 TTL·크기 고정·형식 제한, revalidate 늘리기, 미들웨어 matcher로 범위 제한.
- **검증:** Vercel Usage의 Image Optimization·Middleware 항목.
- **비용 영향:** 단가는 이번 작업에서 미확인(가격 페이지에 항목 존재). Vercel 문서 "How to reduce Vercel Image Optimization costs" 존재 확인.
- **출처:** https://vercel.com/docs/spend-management (관련 문서 링크로 이미지 최적화 비용 절감 가이드 확인). 단가는 출처 미확인. ⚠️근거없음

### COST-071 Supabase 무료 플랜 함정 (1주 비활성 정지, 500MB)
- **무엇/왜:** Supabase Free는 1주 비활성 시 프로젝트가 정지되고, DB 500MB·이그레스 5GB 한도다. 데모가 실사용으로 넘어가는 순간 한도에 부딪힌다.
- **실패 양상:** 주말 지나 접속하니 서비스 정지. DB 용량 초과로 쓰기 실패.
- **신호:** 🟢 `@supabase/supabase-js` 사용 / 🟡 공개 가입·결제 신호(실사용) / 🔴 실제 플랜
- **관련 수준:** D≥1 또는 T≥1 공개 서비스면 Free는 부적합(정지 = 가용성 장애).
- **처방:** 티어 0: Pro($25/월, Micro 컴퓨트 크레딧 포함, 스펜드 캡 기본 켜짐).
- **검증:** Supabase 사용량.
- **비용 영향:** Free: DB 500MB, MAU 5만, 이그레스 5GB + 캐시 5GB, 스토리지 1GB, 활성 프로젝트 2개, 1주 비활성 정지. Pro: MAU 10만 후 $0.00325/MAU, 이그레스 250GB 후 $0.09/GB, 캐시 이그레스 $0.03/GB, 스토리지 100GB 후 $0.0213/GB.
- **출처:** https://supabase.com/pricing

### COST-072 Firebase Blaze 요금 폭탄 (무한 트리거·클라이언트 직접 쿼리)
- **무엇/왜:** Firebase는 클라이언트가 DB를 직접 읽으므로 비효율적인 리스너·쿼리가 그대로 읽기 과금이 된다. Cloud Functions 트리거가 자기 자신을 다시 트리거하면 무한 루프. 예산 알림은 서비스를 멈추지 않는다.
- **실패 양상:** `onDocumentWritten`이 같은 문서를 다시 써서 무한 루프 → 하룻밤 수천 달러. 목록 화면마다 컬렉션 전체 실시간 리스너.
- **신호:** 🟢 `functions.firestore.document(...).onWrite`/`onDocumentWritten` 안에서 같은 경로에 쓰기 / 🟢 클라이언트 `onSnapshot(collection(...))` 필터·limit 없음 / 🟢 `firebase.json` + Blaze 전용 기능(Functions) 사용
- **관련 수준:** 수준 무관. Blaze 사용 시 필수 점검.
- **처방:** 티어 0: 트리거 멱등·가드, 쿼리 `limit`, 예산 알림 + Pub/Sub로 결제 비활성화 자동화, 스펜드 캡 예산(지원 서비스에 한해).
- **검증:** Firebase Usage and billing 대시보드, 에뮬레이터로 사전 테스트.
- **비용 영향:** Firestore 무료 읽기 5만/일·쓰기 2만/일, Functions 호출 200만/월 무료 후 $0.40/100만, Hosting 전송 360MB/일 무료 후 $0.15/GB, Storage 다운로드 1GB/일 후 $0.12/GB. "Budget alerts do not pause services." 스펜드 캡 예산은 Firebase AI Logic, App Hosting, Cloud Functions for Firebase, Extensions만.
- **출처:** https://firebase.google.com/pricing ; https://firebase.google.com/docs/projects/billing/avoid-surprise-bills

### COST-073 Netlify 크레딧 기반 요금제
- **무엇/왜:** Netlify는 배포·대역폭·컴퓨트·요청을 크레딧으로 환산한다. 프로덕션 배포 자체가 크레딧을 먹어서, 커밋마다 프로덕션 배포하면 크레딧이 빠진다.
- **실패 양상:** 하루 수십 번 main 브랜치 배포 → 배포만으로 크레딧 소진.
- **신호:** 🟢 `netlify.toml` / 🟢 CI가 main 푸시마다 프로덕션 배포 / 🟡 대용량 자산
- **관련 수준:** U 수준과 연동(배포 빈도).
- **처방:** 티어 0: 배포 묶기, 대역폭 큰 자산은 외부 CDN.
- **검증:** Netlify 사용량.
- **비용 영향:** Free 300 크레딧, Pro $20/월 3,000 크레딧. 프로덕션 배포 15크레딧(약 $0.10), 대역폭 20크레딧/GB(약 $0.13/GB), 컴퓨트 10크레딧/GB-시간, 요청 2크레딧/1만.
- **출처:** https://www.netlify.com/pricing/

### COST-074 Lambda·Cloud Functions 재시도·재귀 루프
- **무엇/왜:** 비동기 이벤트 소스는 실패 시 자동 재시도한다. S3 업로드 이벤트를 받은 함수가 같은 버킷에 결과를 쓰면 재귀 호출. 독성 메시지는 무한 재시도.
- **실패 양상:** 재귀로 호출 수 기하급수 → 한도·요금 폭발.
- **신호:** 🟢 S3 이벤트 트리거 버킷 = 함수가 쓰는 버킷(접두사 필터 없음) / 🟢 SQS 트리거에 DLQ(`redrive_policy`) 없음 / 🟢 `maximum_retry_attempts` 미설정
- **관련 수준:** C≥2(큐 소비)와 연결.
- **처방:** 입력·출력 버킷 분리 또는 접두사 필터, DLQ, 재시도 상한, 동시성 상한(COST-016).
- **검증:** 호출 수 급증 알람.
- **비용 영향:** 서울 Lambda 요청 $0.20/100만 + GB초 요금. 루프는 상한 없이 증가.
- **출처:** 일반 원칙(출처 미확인). 단가 [PL] AWSLambda. ⚠️근거없음

### COST-075 장기 실행 작업을 함수 실행 시간으로 과금
- **무엇/왜:** 함수는 I/O 대기 시간까지 메모리 × 시간으로 과금된다. 외부 API(LLM 등) 응답을 수십 초 기다리는 함수는 "기다리는 데" 돈을 낸다. Vercel Fluid의 Active CPU처럼 대기 시간을 덜 과금하는 모델도 있다.
- **실패 양상:** LLM 스트리밍 30초 × 1GB × 요청 수 → 함수 비용이 LLM 비용에 근접.
- **신호:** 🟢 함수 안 `await fetch(LLM)`·외부 API 장시간 대기 / 🟢 `maxDuration` 큰 값 / 🟢 웹소켓·SSE를 함수에서 유지
- **관련 수준:** TIER-001(최대 실행 시간)과 연동.
- **처방:** 티어 0: 대기 시간 과금이 적은 런타임 모드 확인 / 티어 1: 동시성 높은 컨테이너로 이전 / 작업 큐 + 웹훅 콜백.
- **검증:** 함수 Duration 분포.
- **비용 영향:** 서울 Lambda 1GB × 30초 = 요청당 $0.0005 → 100만 건 $500.
- **출처:** [PL] AWSLambda; https://vercel.com/pricing (Active CPU·Provisioned Memory 분리 과금). 대기 과금 해석은 이 문서의 추론. ⚠️근거없음

### COST-076 프리뷰·브랜치 환경 누적
- **무엇/왜:** PR마다 프리뷰 환경(Vercel 프리뷰, Supabase 브랜치, 임시 namespace·DB)을 만들면 닫힌 PR의 자원이 남는다. Supabase 브랜치 컴퓨트는 스펜드 캡 밖이다.
- **실패 양상:** 닫힌 PR 30개의 브랜치 DB가 계속 과금.
- **신호:** 🟢 CI의 PR 이벤트로 환경 생성(`on: pull_request` + `terraform apply`/`supabase branches create`) + `closed` 이벤트 정리 단계 없음
- **관련 수준:** 수준 무관.
- **처방:** PR 닫힘 시 자동 삭제 잡, TTL 라벨.
- **검증:** 환경 수 추이.
- **비용 영향:** 환경당 고정비(예: 서울 db.t4g.micro 월 $18.3, Supabase Branching Compute) × 남은 수.
- **출처:** https://supabase.com/docs/guides/platform/cost-control (Branching Compute가 스펜드 캡 제외 항목). 패턴 자체는 일반 원칙. ⚠️근거없음

### COST-077 플랫폼 내 매니지드 애드온 마크업 (마켓플레이스 DB·Redis)
- **무엇/왜:** PaaS 마켓플레이스로 붙인 DB·Redis는 편하지만 별도 청구이고, 지출 한도에서 빠지는 경우가 있다(Vercel Spend Management는 Marketplace 통합을 포함하지 않음).
- **실패 양상:** 지출 한도를 걸었는데 마켓플레이스 애드온 요금은 계속 증가.
- **신호:** 🟢 Vercel 통합 환경변수(`KV_URL`, `POSTGRES_URL`, `UPSTASH_*`) / 🔴 실제 통합 목록
- **관련 수준:** 수준 무관.
- **처방:** 티어 0: 애드온별 별도 예산·알림, 직접 계약 가격과 비교.
- **검증:** 통합 공급자 청구서.
- **비용 영향:** 공급자별(이번 작업에서 미확인).
- **출처:** https://vercel.com/docs/spend-management ("It does not include seats, integrations (such as Marketplace), or separate add-ons")

---

## I. 외부 API·사용량 폭증·키 유출

### COST-079 사용자별·키별 사용량 한도 부재
- **무엇/왜:** 유료 외부 API를 쓰는 기능에 사용자별 한도가 없으면, 악성 사용자 한 명이나 스크립트가 월 예산을 하루에 쓴다. 레이트 리밋(T-CTL-007)은 초 단위, 비용 한도는 일·월 단위다.
- **실패 양상:** 무료 가입 → 자동화 스크립트로 LLM·SMS 엔드포인트 반복 호출 → 청구 폭탄.
- **신호:** 🟢 LLM·SMS·지도 호출 경로에 사용자별 카운터·쿼터 테이블 없음 / 🟢 비로그인 사용자도 호출 가능 / 🟢 공급자 콘솔 측 한도 설정 코드·문서 없음
- **관련 수준:** 공개 가입(T≥1) + 유료 API면 필수.
- **처방:** 사용자별 일일 토큰·호출 쿼터(DB·Redis 카운터), 무료 플랜 별도 한도, 공급자 측 지출 한도·조직 한도 설정.
- **검증:** P4에서 한도 초과 시 429/402 반환 확인.
- **비용 영향:** 상한 = (사용자 수 × 사용자 한도 × 단가)로 계산 가능해진다. 한도 없으면 상한 없음.
- **출처:** 원칙 5(설계 §2). 공급자 한도 기능은 출처 미확인. ⚠️근거없음

### COST-081 SMS·전화 인증 비용과 SMS 펌핑
- **무엇/왜:** SMS는 건당 과금이고 국가별 단가 차이가 크다. 공격자가 가입·OTP 엔드포인트로 고가 국가 번호에 대량 발송시키는 "SMS 펌핑"이 알려진 수법이다. Supabase MFA Phone은 스펜드 캡 밖이다.
- **실패 양상:** 봇이 OTP 요청을 반복 → 하루 수천 건 해외 SMS.
- **신호:** 🟢 Twilio·SNS `Publish`(PhoneNumber)·Firebase Phone Auth·Supabase phone auth / 🟢 OTP 엔드포인트에 CAPTCHA·레이트 리밋·국가 허용 목록 없음
- **관련 수준:** 공개 가입 + SMS면 필수 통제.
- **처방:** 국가 허용 목록, 번호·IP별 레이트 리밋, CAPTCHA, 월 지출 한도, 가능하면 이메일·패스키 우선.
- **검증:** 발송 국가 분포 모니터링.
- **비용 영향:** AWS SMS 단가는 국가·통신사별로 다르며 공식 페이지는 "change frequently"라고만 명시(단가는 이번에 확인 못 함).
- **출처:** https://aws.amazon.com/sns/sms-pricing/ (국가별 변동 문구 확인); https://supabase.com/docs/guides/platform/cost-control (MFA Phone 제외 항목); SMS 펌핑 개념은 출처 미확인. ⚠️근거없음

### COST-082 지도·외부 유료 API 무료 한도 초과
- **무엇/왜:** 지도 API는 SKU별 월 무료 호출이 있고 그 뒤 종량 과금이다. 지도를 매 페이지 로드마다 그리거나 지오코딩을 캐시하지 않으면 무료 한도를 쉽게 넘는다. 클라이언트 키는 노출되므로 리퍼러 제한이 필수.
- **실패 양상:** 주소 → 좌표 변환을 요청마다 호출 → 무료 1만 건 초과 후 과금.
- **신호:** 🟢 `@googlemaps/js-api-loader`, `maps.googleapis.com` / 🟢 같은 주소 지오코딩 결과를 저장하지 않음 / 🟢 API 키가 프런트 코드에 있고 제한 설정 문서 없음
- **관련 수준:** T≥1.
- **처방:** 지오코딩 결과 DB 캐시(약관 허용 범위), 정적 지도 대체, API 키 HTTP 리퍼러·API 제한, 할당량 상한.
- **검증:** Cloud 콘솔 API 사용량.
- **비용 영향:** Google Maps 종량제 Essentials SKU당 월 1만 건 무료(Pro 5천, Enterprise 1천), 구독형 Starter $100/월(5만 호출), Essentials $275/월(10만 호출). 예산 알림은 Maps 사용도 자동으로 막지 않는다.
- **출처:** https://mapsplatform.google.com/pricing/ ; https://docs.cloud.google.com/billing/docs/how-to/budgets ("doesn't automatically cap Google Cloud or Google Maps Platform usage")

### COST-083 이메일 발송 비용과 남용
- **무엇/왜:** 트랜잭션 이메일은 싸지만, 가입 스팸·대량 알림·첨부 파일이 붙으면 늘어나고, 반송률이 높으면 계정 정지 위험까지 있다.
- **실패 양상:** 봇 가입으로 인증 메일 대량 발송 → 비용보다 평판·정지 피해가 큼.
- **신호:** 🟢 `@aws-sdk/client-ses`, `nodemailer`, Resend·SendGrid SDK / 🟢 가입 엔드포인트에 CAPTCHA·레이트 리밋 없음 / 🟢 이메일에 대용량 첨부
- **관련 수준:** 공개 가입.
- **처방:** 가입 레이트 리밋·CAPTCHA, 첨부 대신 링크, 일일 발송 상한.
- **검증:** 발송량·반송률.
- **비용 영향:** SES 아웃바운드 $0.10/1,000건(à la carte), 첨부 $0.12/GB, 전용 IP $24.95/월.
- **출처:** https://aws.amazon.com/ses/pricing/

### COST-084 키 유출로 인한 요금 폭탄 (클라우드·LLM·결제 키)
- **무엇/왜:** 저장소·프런트 번들에 클라우드 액세스 키·LLM API 키가 들어가면 도용당해 채굴·대량 호출에 쓰인다. 바이브코더가 가장 자주 겪는 "요금 폭탄"이다. 비용 축에서는 탐지 + 가드레일(예산·한도)로 피해 상한을 만든다.
- **실패 양상:** 공개 저장소에 AWS 키 푸시 → 수 시간 내 모든 리전에 고가 인스턴스 생성. 프런트에 `NEXT_PUBLIC_OPENAI_API_KEY` → 누구나 토큰 사용.
- **신호:** 🟢 `AKIA[0-9A-Z]{16}`, `sk-ant-`, `sk-`, `AIza` 패턴이 커밋된 파일에 / 🟢 `.env` 파일이 git에 추적됨, `.gitignore`에 `.env` 없음 / 🟢 `NEXT_PUBLIC_`·`VITE_`·`EXPO_PUBLIC_` 접두사에 비밀 키 / 🟢 서비스 롤 키(Supabase `service_role`)가 클라이언트 코드에
- **관련 수준:** 수준 무관, 최우선(보안 담당과 공유하되 비용 축은 "피해 상한" 통제를 맡는다).
- **처방:** 키 회전, 서버 측 프록시로만 호출, GitHub push protection(공개 저장소 사용자 수준 기본 활성), 예산 알림 + 자동 차단(COST-086~089), IAM 최소 권한·미사용 리전 비활성(SCP).
- **검증:** 시크릿 스캐너 결과, 저장소 히스토리 스캔.
- **비용 영향:** 상한 없음(계정 전체 한도까지).
- **출처:** https://docs.github.com/en/code-security/secret-scanning/introduction/about-push-protection ; 키 유출과 청구 사례 자체는 출처 미확인(AWS re:Post 문서는 403으로 열지 못함). ⚠️근거없음

### COST-085 Firebase·Supabase 공개 키 + 느슨한 규칙 = 남이 쓰는 DB
- **무엇/왜:** Firebase 웹 API 키와 Supabase anon 키는 공개가 전제다. 대신 보안 규칙·RLS가 막아야 하는데, 규칙이 열려 있으면 누구나 대량 읽기·쓰기로 과금을 일으킨다.
- **실패 양상:** `allow read, write: if true;` → 외부에서 컬렉션 전체 반복 읽기 → 읽기 과금 폭증.
- **신호:** 🟢 `firestore.rules`/`storage.rules`에 `if true` 또는 `request.time < timestamp.date(...)`(테스트 모드) / 🟢 Supabase 테이블에 RLS 비활성(`alter table ... enable row level security` 없음) / 🟢 App Check 미설정
- **관련 수준:** 수준 무관.
- **처방:** 규칙·RLS 강화, Firebase App Check, 키의 API 제한, 예산 알림.
- **검증:** 규칙 에뮬레이터 테스트.
- **비용 영향:** Firestore 무료 읽기 5만/일 초과분부터 과금, 상한 없음.
- **출처:** https://firebase.google.com/docs/projects/billing/avoid-surprise-bills ; https://firebase.google.com/pricing . 규칙 패턴 자체는 일반 원칙(출처 미확인). ⚠️근거없음

---

## J. 거버넌스·가시성·청구 구조

### COST-086 예산 알림 부재 (AWS Budgets·GCP 예산)
- **무엇/왜:** 예산 알림이 없으면 이상 비용을 월말 청구서로 처음 안다. AWS Budgets 기본 알림은 무료다. 단 예산은 알림일 뿐 사용을 막지 않는다.
- **실패 양상:** 키 유출·루프·설정 실수를 몇 주 뒤에야 발견.
- **신호:** 🟢 `aws_budgets_budget` 없음 / 🟢 `google_billing_budget` 없음 / 🟢 알림 수신자(SNS·이메일·Pub/Sub) 없음
- **관련 수준:** 모든 수준에서 필수(가장 싼 보험).
- **처방:** 월 예산 + 50/80/100% 실제·예측 알림, GCP는 Pub/Sub 알림 + 결제 비활성화 자동화(비운영 프로젝트), AWS는 Budgets Actions(IAM·SCP 적용, 인스턴스 정지).
- **검증:** Terraform에 예산 리소스 존재, 테스트 알림.
- **비용 영향:** AWS Budgets 일반 예산·알림 무료, 액션 예산 2개까지 무료 이후 $0.10/일, 예산 보고서 $0.01/건. GCP 예산은 "doesn't automatically cap", 비용 보고 지연이 있어 가용 자금보다 낮게 설정 권고.
- **출처:** https://aws.amazon.com/aws-cost-management/aws-budgets/pricing/ ; https://docs.cloud.google.com/billing/docs/how-to/budgets

### COST-087 비용 이상 탐지(Cost Anomaly Detection) 미설정
- **무엇/왜:** 고정 예산은 "평소보다 갑자기 오른 것"을 늦게 잡는다. 이상 탐지는 서비스·계정·리전별 패턴 이탈을 잡는다. 다만 최대 24시간 지연이 있고 새 서비스는 10일 이력이 필요하다.
- **실패 양상:** 예산 안이지만 특정 리전에 의문의 EC2 비용이 매일 증가.
- **신호:** 🟢 `aws_ce_anomaly_monitor`, `aws_ce_anomaly_subscription` 없음
- **관련 수준:** production 계정 전부.
- **처방:** AWS 관리형 모니터 + 일일 요약 알림(Slack). 실시간 차단이 필요하면 별도 가드레일(동시성 상한·SCP).
- **검증:** 알림 구독 존재.
- **비용 영향:** 하루 약 3회 실행, Cost Explorer 기반이라 최대 24시간 지연.
- **출처:** https://docs.aws.amazon.com/cost-management/latest/userguide/manage-ad.html

### COST-088 플랫폼 지출 한도 설정 (Vercel Spend Management·Supabase Spend Cap)
- **무엇/왜:** PaaS는 자체 지출 한도 기능이 있다. Vercel은 한도 도달 시 알림·웹훅·프로덕션 일시 정지를 고를 수 있고, 몇 분 간격으로 확인하므로 즉시 멈추지는 않는다. Supabase Pro는 스펜드 캡이 기본 켜짐이고 초과 사용을 차단한다.
- **실패 양상:** 한도 없이 바이럴·봇 트래픽 → 예상 밖 청구. 반대로 한도가 서비스를 멈춰 가용성 장애(COST-101).
- **신호:** 🔴 대부분 대시보드 설정(코드에 없음) / 🟡 Vercel 웹훅 수신 엔드포인트 코드(`x-vercel-signature` 검증) 존재 여부
- **관련 수준:** 모든 티어 0. D≥2·T≥2면 "정지" 대신 "알림 + 수동 판단"을 권고.
- **처방:** Vercel: On-Demand Budget 설정(새 팀 기본 $200), 50/75/100% 알림, D≤1이면 Pause Production 허용 / Supabase: 스펜드 캡 유지하되 캡 제외 항목(컴퓨트 등) 따로 감시.
- **검증:** 설정 화면 확인을 체크리스트로 리포트에 포함.
- **비용 영향:** Vercel Spend Management는 Pro에서 추가 비용 없음, 좌석·마켓플레이스 통합·애드온은 한도 밖.
- **출처:** https://vercel.com/docs/spend-management ; https://vercel.com/pricing ; https://supabase.com/pricing ; https://supabase.com/docs/guides/platform/cost-control

### COST-089 미사용 리전 방치 (도용 시 피해 확대)
- **무엇/왜:** 쓰지 않는 리전이 열려 있으면 키 유출 시 공격자가 감시 밖 리전에 자원을 만든다. 서울만 쓰면 나머지 리전 사용을 막는 것이 비용 가드레일이다.
- **실패 양상:** 서울 대시보드만 보다가 다른 리전 GPU 인스턴스 비용을 월말에 발견.
- **신호:** 🟢 AWS Organizations SCP `aws:RequestedRegion` 제한 없음 / 🟡 provider가 단일 리전만 사용(제한 근거)
- **관련 수준:** 수준 무관. D=3 멀티 리전이면 허용 목록에 포함.
- **처방:** SCP로 허용 리전 제한(전역 서비스 예외), GCP 조직 정책 `gcp.resourceLocations`.
- **검증:** 정책 존재.
- **비용 영향:** 피해 상한 축소(정량화 불가).
- **출처:** 일반 원칙(출처 미확인). ⚠️근거없음

### COST-090 비용 할당 태그·라벨 부재
- **무엇/왜:** 태그가 없으면 어떤 환경·서비스가 돈을 쓰는지 나눌 수 없어 right-sizing 대상도 못 찾는다. AWS 비용 할당 태그는 리소스에 붙이는 것만으로는 부족하고 결제 콘솔에서 **활성화**해야 보고서에 나온다(최대 24시간).
- **실패 양상:** 청구서가 서비스별 합계만 보여 dev와 prod 비용을 구분 못 함.
- **신호:** 🟢 Terraform provider `default_tags` 없음 / 🟢 리소스에 `Environment`·`Service`·`Owner` 태그 없음 / 🟢 k8s·GKE `resource_labels` 없음 / 🟢 `aws_ce_cost_allocation_tag` 활성화 리소스 없음
- **관련 수준:** 모든 수준(환경이 2개 이상이면 필수).
- **처방:** provider `default_tags`로 일괄, 태그 활성화, k8s는 namespace·라벨 기반 비용 할당(OpenCost 등은 출처 미확인). ⚠️근거없음
- **검증:** Cost Explorer 태그별 그룹핑.
- **비용 영향:** 직접 비용 없음. 낭비 탐지의 전제.
- **출처:** https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/cost-alloc-tags.html ("You must activate both types of tags separately before they can appear in Cost Explorer")

### COST-092 무료 등급·크레딧 함정
- **무엇/왜:** AWS 신규 무료 플랜은 크레딧($100 + 최대 $100) 기반이고, 무료 플랜 계정은 6개월 또는 크레딧 소진 시 닫힌다. 유료 플랜으로 바꾸면 크레딧 이후 종량 과금. GKE 무료 크레딧은 존 클러스터 1개 상당뿐이고, Cloud Run 무료 등급은 요청 기반·결제 계정 합산이다. 견적이 무료 등급에 의존하면 성장 즉시 비용이 튄다.
- **실패 양상:** "무료로 돌아가던" 앱이 크레딧 만료·계정 종료로 갑자기 멈추거나 과금 시작.
- **신호:** 🟡 견적이 무료 등급 한도 안에 있음 / 🔴 계정 생성일·플랜
- **관련 수준:** D≥1 데이터가 무료 플랜 계정에 있으면 계정 종료 위험을 경고.
- **처방:** 리포트에 "무료 등급 적용 전/후" 두 견적을 함께 표시.
- **검증:** 가격 API에서 무료 등급 SKU 분리.
- **비용 영향:** Cloud Run 요청 기반 무료 월 18만 vCPU초·36만 GiB초·요청 200만, 인스턴스 기반 무료 24만 vCPU초·45만 GiB초. GKE 무료 월 $74.40. ALB 무료 등급 750시간(신규).
- **출처:** https://aws.amazon.com/free/ ; https://cloud.google.com/run/pricing ; https://cloud.google.com/kubernetes-engine/pricing ; https://aws.amazon.com/elasticloadbalancing/pricing/

### COST-093 환율·부가세 (견적은 USD, 청구는 원화 + VAT)
- **무엇/왜:** 가격 API는 USD 세전 단가다. 한국 계정은 AWS Korea LLC가 부가세 세금계산서를 발행하고, 사업자등록번호를 입력하지 않으면 B2C로 보고 부가세를 부과한다. 환율 변동도 월 비용을 흔든다.
- **실패 양상:** 견적 $100을 13만 원으로 생각했는데 청구는 VAT 포함 + 환율 상승분.
- **신호:** 🔴 코드에 없음 → 가정 / 🟡 UI 통화가 KRW(리전 추론과 같은 신호)
- **관련 수준:** 모든 수준. 리포트 표시 규칙.
- **처방:** 리포트에 "세전 USD" 명시 + KRW 환산(환산 기준일 표시) + 부가세 별도 표기.
- **검증:** 청구서 대조.
- **비용 영향:** 한국 부가세율 10%는 일반 원칙(AWS 페이지에 세율 미기재, 출처 미확인). ⚠️근거없음
- **출처:** https://aws.amazon.com/tax-help/south-korea1/ ; GCP 가격 페이지 "If you pay in a currency other than USD, the prices listed in your currency on Cloud Platform SKUs apply"(https://cloud.google.com/run/pricing)

### COST-094 지원 플랜 비용 (사용량 비례 최소 요금)
- **무엇/왜:** AWS 유료 지원 플랜은 최소 월 요금 + 월 사용액의 %다. 작은 앱에 상위 플랜을 붙이면 인프라보다 지원비가 큰 경우도 있다. 2026-10-01 현재 플랜 이름이 Business Support+ / Enterprise / Unified Operations로 바뀌어 있다.
- **실패 양상:** 월 $200 쓰는 계정에 Enterprise($5,000 최소).
- **신호:** 🔴 계정 설정(코드에 없음)
- **관련 수준:** D≥2·C=3 production은 Business Support+ 수준 권장, 그 외는 기본 지원.
- **처방:** 리포트에 수준별 권장 지원 플랜과 비용 표시.
- **검증:** 청구서 Support 항목.
- **비용 영향:** Business Support+ 계정당 최소 $29/월, 월 사용액 $10K까지 9%, $10K~$80K 7%. Enterprise 최소 $5,000/월(사용액 $150K까지 10%). Unified Operations 최소 $50,000/월.
- **출처:** https://aws.amazon.com/premiumsupport/pricing/

### COST-095 개발·검증 환경의 야간·주말 상시 가동
- **무엇/왜:** dev·stg의 노드·태스크·DB가 24시간 돈다. 업무 시간만 켜면 3/4 가까이 줄인다. 설계 P4의 검증 환경(부하·장애 주입용)도 끝나면 내려야 한다.
- **실패 양상:** stg 클러스터가 prod와 같은 크기로 상시 가동 → 인프라 비용 2배.
- **신호:** 🟢 `envs/dev`·`staging` 디렉터리에 prod와 같은 노드 수·인스턴스 크기 / 🟢 스케일 다운 CronJob·스케줄 없음 / 🟢 Cloud Run dev 서비스 min-instances > 0
- **관련 수준:** 비운영 환경 전부.
- **처방:** 티어 2: 야간 노드 그룹 0 스케일(스케줄 액션), Karpenter NodePool 제한 / 티어 1: min 0 / DB: COST-053 / P4 환경: 검증 후 `terraform destroy`.
- **검증:** 환경별 시간당 비용 × 가동 시간.
- **비용 영향:** 주 40시간 가동 시 약 76% 절감(시간 비례 자원 한정).
- **출처:** https://docs.aws.amazon.com/solutions/instance-scheduler-on-aws/ ; https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_StopInstance.html

---

## K. 아끼면 안 되는 곳 (반대 방향 규칙)

이 절의 규칙은 비용 필터가 "더 싼 구성"을 고르려 할 때 **거부권**을 가진다. 설계 §8.4 COST-009와 같은 종류다.

### COST-096 C=3·D≥2 데이터의 Multi-AZ·동기 복제는 절감 대상 아님
- **무엇/왜:** 결제·재고(C=3)나 D≥2 데이터는 동기 대기 복제본이 커밋된 쓰기를 지킨다. Multi-AZ를 끄면 비용은 절반이지만 RPO 0을 잃는다.
- **실패 양상:** 비용 최적화 도구가 "Multi-AZ 해제로 월 $209 절감"을 권하고 그대로 적용 → AZ 장애 시 결제 데이터 유실.
- **신호:** 🟢 `multi_az = true` + 결제 SDK(`stripe`, 토스페이먼츠) / 🟢 Cloud SQL `REGIONAL` + 재고 차감 패턴
- **관련 수준:** C=3 또는 D≥2면 유지 필수.
- **처방:** 축소 처방 생성 금지, 리포트에 "필요한 비용" 라벨. 대신 인스턴스 크기·예약 할인으로 절감.
- **검증:** P4 AZ 장애 주입에서 데이터 유실 0.
- **비용 영향:** 서울 db.r7g.large Multi-AZ 월 약 $419(Single-AZ 대비 +$209).
- **출처:** [PL] AmazonRDS; 설계 S10, C-CTL-006

### COST-097 T=3 & 급격한 램프의 최소 인스턴스·여유 용량
- **무엇/왜:** 예고 없는 20배 폭증(T=3)에서 scale-to-zero나 min 1은 콜드 스타트 동안 요청을 잃는다. 최소 인스턴스·자리표시 Pod 비용은 보험료다.
- **실패 양상:** 유휴비를 아끼려고 min 0 → 재난·속보 트래픽 첫 1분에 실패 폭발(가장 써야 할 때 죽음).
- **신호:** 🟢 T=3 판정 + `min_instance_count = 0`, `minReplicas: 1`, 자리표시 Pod 없음
- **관련 수준:** T=3(설계 TIER-003, T-CTL-009).
- **처방:** 축소 금지. min ≥ 평시 기준 인스턴스, 티어 2는 저우선순위 자리표시 Pod.
- **검증:** P4 1분 램프 부하 시험 통과.
- **비용 영향:** Cloud Run(us-central1) 1 vCPU·512MiB 유휴 min 인스턴스 월 약 $9.9/개. 자리표시 Pod는 노드 1대분(서울 m7g.large 월 약 $73).
- **출처:** https://cloud.google.com/run/pricing ; 설계 S14, S21

### COST-098 백업 보존·PITR은 D≥1에서 절감 대상 아님
- **무엇/왜:** 백업 저장비는 작고, 없을 때의 손실은 전부다. 백업 보존 기간을 1일로 줄이거나 PITR을 끄는 절감은 거부한다. Supabase PITR은 스펜드 캡 밖의 유료 애드온이라 "비용 때문에 안 켬"이 흔하다.
- **실패 양상:** 보존 1일(RDS API·CLI 기본) → 주말에 발견한 데이터 손상을 복구 못 함.
- **신호:** 🟢 `backup_retention_period` < 7 / 🟢 `skip_final_snapshot = true`(production) / 🟢 `deletion_protection = false`(production)
- **관련 수준:** D≥1(D-CTL-001).
- **처방:** 보존 ≥ 7일, final snapshot, 삭제 보호. 비용은 COST-042 수명 주기로 관리.
- **검증:** P4 복원 리허설(D-CTL-006).
- **비용 영향:** 서울 RDS 무료 할당 초과 백업 $0.095/GB-월. 10GB DB면 월 $1 미만 수준.
- **출처:** [PL] AmazonRDS; 설계 S10; https://supabase.com/docs/guides/platform/cost-control (PITR 캡 제외)

### COST-099 D≥2의 AZ별 NAT·다중 AZ 노드
- **무엇/왜:** 단일 NAT는 그 AZ가 죽으면 다른 AZ의 아웃바운드도 함께 끊긴다. D≥2(AZ 하나가 죽어도 동작)에서 NAT·노드를 한 AZ로 모으는 절감은 목표와 모순이다.
- **실패 양상:** NAT 2개 절약(월 약 $86) → AZ 장애 시 외부 결제 API 호출 불가.
- **신호:** 🟢 D≥2 판정 + `single_nat_gateway = true` / 🟢 노드 그룹 서브넷이 1개 AZ
- **관련 수준:** D≥2.
- **처방:** AZ별 NAT 유지(AWS 권장), 비용은 리전 NAT Gateway·엔드포인트(COST-031)로 처리량 쪽에서 절감.
- **검증:** P4 AZ 장애 주입.
- **비용 영향:** 서울 NAT 1개당 월 $43.07.
- **출처:** 설계 S18; [PL] AmazonEC2

### COST-100 감사·보안 로그는 샘플링·삭제 대상 아님
- **무엇/왜:** 로그 비용 절감(COST-061~062)은 앱 디버그 로그에 적용한다. 인증·권한 변경·결제 이벤트·CloudTrail 같은 감사 로그를 샘플링하거나 짧게 보관하면 사고 조사와 규제 대응이 불가능하다.
- **실패 양상:** 로그 비용 줄이려 CloudTrail 비활성 → 키 유출 사고 시 무엇이 만들어졌는지 추적 불가.
- **신호:** 🟢 감사 로그 경로가 일반 로그와 같은 샘플링·보존 정책 / 🟢 `aws_cloudtrail` 없음
- **관련 수준:** C≥2·D≥2·결제가 있으면 필수.
- **처방:** 감사 로그는 별도 그룹·버킷, 저렴한 클래스(S3 + 수명 주기)로 길게 보관.
- **검증:** 보존 정책 분리 여부.
- **비용 영향:** S3 Glacier IR 서울 $0.005/GB-월 수준으로 장기 보관 가능.
- **출처:** [PL] AmazonS3. 감사 로그 필요성은 일반 원칙(출처 미확인). ⚠️근거없음

### COST-101 지출 한도의 "자동 정지"가 가용성 목표와 충돌
- **무엇/왜:** Vercel "Pause Production Deployments"는 한도 도달 시 모든 프로젝트의 프로덕션을 503으로 내린다(수동 재개 필요). Supabase 스펜드 캡은 초과 사용을 차단한다. D≥2·T≥2 서비스에서 이 동작은 스스로 만든 장애다.
- **실패 양상:** 이벤트 날(T=2) 트래픽이 몰리자 지출 한도에 걸려 서비스 전체 정지.
- **신호:** 🔴 대시보드 설정 / 🟡 D≥2 또는 T≥2 판정 + 티어 0
- **관련 수준:** D≥2·T≥2면 자동 정지 대신 알림 + 사전 증액. D≤1·T≤1이면 자동 정지가 합리적 보험.
- **처방:** 수준별 권고를 리포트에 분기. T≥2 이벤트 전 한도 상향 체크리스트.
- **검증:** 설정 체크리스트.
- **비용 영향:** 가용성 손실 vs 초과 과금의 선택.
- **출처:** https://vercel.com/docs/spend-management ("your production deployments stop serving traffic", "Projects need to be resumed on an individual basis"); https://supabase.com/docs/guides/platform/cost-control

### COST-102 PDB를 만족하는 최소 복제 수(2)는 축소 대상 아님
- **무엇/왜:** U≥2에서 PDB와 롤링 배포가 동작하려면 최소 2개 복제본이 필요하다. right-sizing이 "평균 사용률이 낮으니 1개로"를 권하면 무중단 배포·노드 드레인이 깨진다.
- **실패 양상:** replicas 1 + PDB minAvailable 1 → 노드 드레인이 영원히 막히거나, PDB 없이 배포마다 다운타임.
- **신호:** 🟢 U≥2 판정 + `replicas: 1`/`minReplicas: 1`
- **관련 수준:** U≥2(U-CTL-005), D≥2(존 분산).
- **처방:** 복제 수는 2로 고정하고 Pod 크기를 줄여서 절감.
- **검증:** P4 롤링 배포 중 오류율 0.
- **비용 영향:** Pod 1개 추가분(예: Fargate 0.25 vCPU·0.5GB 서울 월 약 $10.4).
- **출처:** 설계 S6(PDB); [PL] AmazonECS

---

## 설계 문서 §8.4 COST 규칙과의 대응

| 설계 ID | 이 카탈로그 |
|---|---|
| COST-001 (T≤1 & D≤1인데 티어 2) | COST-001, COST-065, COST-068 |
| COST-002 (AZ별 NAT) | COST-003, COST-031, COST-099 |
| COST-003 (AZ 간 트래픽) | COST-032 |
| COST-004 (Spot) | COST-025, COST-026 |
| COST-005 (Graviton) | COST-018 |
| COST-006 (requests 2배 이상) | COST-011, COST-012 |
| COST-007 (D≤1 멀티 리전) | COST-033 |
| COST-008 (유료 외부 API) | COST-078 ~ COST-082 |
| COST-009 (C=3 단일 AZ 절감 금지) | COST-096 |

## 새 축·규칙 후보

1. **"최악의 시간당 비용"(비용 상한) 지표를 리포트 필수 출력으로.** 평시 월 비용·피크 시간당 비용(§9.3) 외에, 오토스케일 상한 × 단가 + 외부 API 사용자 한도 × 사용자 수로 계산한 "공격·버그가 나도 이 이상은 안 나간다"는 상한을 낸다. 상한이 계산되지 않으면(HPA max·Lambda 동시성·사용자 한도 중 하나라도 없음) 그 자체를 결함으로 본다(COST-016, COST-079). 비용 축에 "상한 존재" 통제를 두는 셈이다.
2. **비용 가드레일 수준 G0~G2를 별도 통제 묶음으로.** G0 아무것도 없음 / G1 예산 알림 + 이상 탐지 + 비용 태그 / G2 자동 차단(동시성 상한, 사용자 한도, 지출 한도, 허용 리전 SCP). 공개 가입 + 유료 외부 API 또는 티어 0 Blaze·Pro면 G2 필요. 시나리오 수준과 같은 방식으로 "필요/현재/차이"를 계산할 수 있다.
3. **반대 방향 규칙(kind: cost_floor) 종류 신설.** COST-096~102처럼 비용 필터의 절감 처방을 거부하는 규칙을 `kind: cost`와 분리해 `cost_floor`로 두면, ⑥ 티어 선택 단계에서 "이 BOM 항목은 빼면 안 됨"을 기계적으로 표시할 수 있다.
4. **지출 한도와 가용성의 상호작용 규칙.** Vercel 자동 정지·Supabase 캡처럼 "비용 통제가 장애를 만드는" 경우를 D·T 수준과 교차해 판정(COST-101). 현재 설계에는 비용 → 가용성 방향의 충돌을 다루는 규칙이 없다.
5. **가격 원천 메모.** AWS Price List 오퍼 파일(curl로 공개 접근, 인증 불필요)로 서울 단가를 결정적으로 얻을 수 있었다. 반면 GCP 가격 페이지는 기본 표가 us-central1뿐이고 서울(asia-northeast3)은 Cloud Run 기준 Tier 2 리전이므로, GCP 서울 견적은 Billing Catalog API(API 키 필요) 없이는 불가능하다. P1 구현에서 GCP는 "API 키 없으면 us-central1 단가 × 경고"로 처리하는 규칙이 필요하다.
6. **외부 API 비용을 BOM에 포함.** 현재 §9.2 BOM은 클라우드 자원만 다룬다. LLM·SMS·지도·이메일을 `external_api` BOM 항목(단가 × 요청당 사용량 × 가정 트래픽)으로 넣어야 사용자 1,000명당 비용이 현실과 맞는다(COST-091(삭제됨)).
7. **플랜 한도 사실(fact) 추가.** 티어 0 판정에 Vercel Hobby 비상업 제한, Supabase Free 1주 비활성 정지, AWS 무료 플랜 6개월 종료를 "티어 제외 조건"으로 넣는다(결제·공개 가입 신호와 결합). 현재 TIER 규칙은 기술적 한도(실행 시간, 본문 크기)만 다룬다.
8. **약정 순서 규칙.** right-sizing·티어 변경 처방이 하나라도 있으면 약정(Savings Plans·CUD) 처방을 보류(COST-029). 처방 간 순서 의존성을 표현하는 필드(`after: [...]`)가 규칙 형식에 필요할 수 있다.
9. **비운영 환경 축.** 현재 시나리오×수준은 production 기준이다. dev·stg·프리뷰·P4 검증 환경의 비용(COST-053, 076, 095)은 별도 "환경 수명 주기" 통제로 다루는 것이 자연스럽다.
10. **관측 비용과 §17.4 연결.** P4가 설치하는 운영 관측 설정 자체가 비용(COST-061~067)이므로, 관측 처방에도 비용 견적과 샘플링·보존 기본값을 규칙으로 붙인다.
