# 네트워크 능력 표 — CDN, DNS, WAF·DDoS, 인증서, 출구 NAT·고정 IP, 사설 연결

- 작성일: 2026-10-01 (모든 출처 확인일 2026-10-01, 출구 절 일부 2026-10-02 재확인)
- 형식·능력 키: [README.md](README.md) §1, §2.8 (NW.* 20개). 능력 값마다 OSI 계층(L3 / L4 / L7 / TLS)을 "계층" 열에 적었다.
- 요구 쪽: [../dimensions.md](../dimensions.md). 짝 문서: [09-network-lb-ingress.md](09-network-lb-ingress.md)(로드밸런서·인그레스), [05-compute-tier1-2.md](05-compute-tier1-2.md)(CP.networking), [08-artifacts-compute.md](08-artifacts-compute.md)(컴퓨트 산출물)
- 재료: [../considerations/01-resilience-dr.md](../considerations/01-resilience-dr.md) §9(DNS·인증서·엣지), [../considerations/02-traffic-compute.md](../considerations/02-traffic-compute.md) §6·§8(CDN·레이트 리밋), [../considerations/05-security-compliance.md](../considerations/05-security-compliance.md) §D·§H(네트워크 경계·엣지 방어), [../considerations/06-cost.md](../considerations/06-cost.md) §A·§D(NAT·IPv4·이그레스). 재료에 있던 값도 모두 공식 문서를 다시 열어 확인했다.

## 범위

| 계열 | 구성 요소 |
|---|---|
| 1. CDN | Amazon CloudFront, Google Cloud CDN, Google Media CDN(요약), Cloudflare CDN(프록시), Vercel 엣지 캐시(요약), Netlify 엣지 캐시(요약), Fastly(요약) |
| 2. DNS | Route 53(라우팅 정책, 헬스 체크 기반 장애 조치), Cloud DNS, Cloudflare DNS, 도메인 등록 기관 기본 DNS(요약) |
| 3. WAF·DDoS | AWS WAF, AWS Shield Standard, AWS Shield Advanced, Google Cloud Armor Standard, Cloud Armor Enterprise, Cloudflare WAF·DDoS, Vercel Firewall(요약) |
| 4. 인증서 | AWS Certificate Manager, Google Certificate Manager·Google 관리형 인증서, Let's Encrypt + cert-manager |
| 5. 출구 | AWS NAT Gateway(존 / 리전), NAT 인스턴스(요약), Google Cloud NAT, 고정 출구 IP 방법(Cloud Run, Lambda, ECS Fargate, Vercel, Netlify, Cloudflare Workers, Render, Fly.io, Railway, Heroku), 퍼블릭 IPv4 요금 |
| 6. 사설 연결 | VPC 게이트웨이 엔드포인트, VPC 인터페이스 엔드포인트, PrivateLink(엔드포인트 서비스·리소스 엔드포인트), Lambda VPC 연결, Serverless VPC Access 커넥터, Direct VPC egress, Private Service Connect, Cloud SQL 사설 IP, Memorystore 사설 연결, SaaS DB(Supabase·Neon·PlanetScale·Atlas·Upstash) 사설 연결(요약) |

### 표기
- **[PL]**: AWS Price List 오퍼 파일(`https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/<ServiceCode>/current/ap-northeast-2/index.{json,csv}`, 글로벌 서비스는 해당 리전 파일)을 curl·jq로 읽은 값. GCP는 공식 가격 페이지 원문. 월 환산은 730시간.
- `미확인`: 공식 문서를 열었지만 값을 찾지 못했거나 페이지를 열지 못함. `[충돌]`: 공식 출처끼리 값이 다름(양쪽 인용). `(추론)`: 인용한 사실에서 이끌어 낸 판단.
- "계층" 열: 그 값이 작동하는 계층. DNS는 L7(응용 계층 프로토콜)로 적었다. 출구 NAT·사설 연결 계열은 요청 경로의 **반대 방향**(앱 → 외부·데이터) 연결에 대한 값이다.
- (요약) 표시 구성 요소는 판정 결정값만 채우고 나머지 키는 한 행으로 묶었다.
- Terraform 리소스·인자 이름은 provider 저장소의 레지스트리 원문(`website/docs/r/*.html.markdown`)이나 레지스트리 API로 확인했다. Checkov ID는 https://www.checkov.io/5.Policy%20Index/terraform.html 인덱스와 bridgecrewio/checkov 소스에서 존재를 확인한 것만 적었다. ⚠️출처확인필요

## 목차

0. [요약 비교표](#0-요약-비교표)
1. [CDN](#1-cdn) — [1.1 CloudFront](#11-amazon-cloudfront--표준-배포pay-as-you-go-기본-flat-rate-요금제-선택-가능) · 1.2 Cloud CDN · 1.3 Media CDN · 1.4 Cloudflare · 1.5 Vercel · 1.6 Netlify · 1.7 Fastly
2. [DNS](#2-dns) — 2.1 Route 53 · 2.2 Cloud DNS · 2.3 Cloudflare DNS · 2.4 등록 기관 DNS
3. [WAF·DDoS](#3-wafddos) — 3.1 AWS WAF · 3.2 Shield Standard · 3.3 Shield Advanced · 3.4 Cloud Armor Standard · 3.5 Cloud Armor Enterprise · 3.6 Cloudflare · 3.7 Vercel Firewall
4. [인증서](#4-인증서) — 4.1 ACM · 4.2 Google Certificate Manager·관리형 인증서 · 4.3 Let's Encrypt + cert-manager
5. [출구 NAT·고정 IP](#5-출구-nat고정-ip) — 5.1 NAT GW 존 · 5.2 NAT GW 리전 · 5.3 NAT 인스턴스 · 5.4 Cloud NAT · 5.5 플랫폼별 고정 출구 IP(5.5.1~5.5.10) · 5.6 퍼블릭 IPv4
6. [사설 연결](#6-사설-연결) — 6.1 게이트웨이 엔드포인트 · 6.2 인터페이스 엔드포인트 · 6.3 PrivateLink · 6.4 Lambda VPC · 6.5 VPC Access 커넥터 · 6.6 Direct VPC egress · 6.7 PSC · 6.8 Cloud SQL 사설 IP · 6.9 Memorystore · 6.10 SaaS DB
7. [경로 규칙 후보](#7-경로-규칙-후보)
8. [조사 결과 요약](#8-조사-결과-요약)

---

# 0. 요약 비교표

각 행의 근거는 해당 절의 표에 있다. "최소 고정비"는 서울 기준(없으면 표기한 리전), 트래픽 0일 때 월 비용이다.

### CDN

| 구성 요소 | 계층 | 핵심 판정값 | 서울 | 최소 고정비 |
|---|---|---|---|---|
| 1.1 Amazon CloudFront | L7 | CachingOptimized 최소 1초·기본 86,400초(private 무시 캐시), 레거시 기본 86,400/0/31,536,000; 오리진 응답 30초(≤120)·keep-alive 5초; 쿠키 전달 시 Set-Cookie 캐시·재전송; 무효화 월 1,000경로 무료 후 $0.005/경로 | 엣지 10개 | $0(상시 무료 1 TB·1천만 요청), flat-rate Pro $15 |
| 1.2 Google Cloud CDN | L7 | 기본 CACHE_ALL_STATIC(HTML·JSON 미캐시), 기본 TTL 3,600·최대 86,400; FORCE_CACHE_ALL은 private 무시; Set-Cookie·private·no-store 미캐시; 무효화 약 10초·분당 500건 | 캐시 위치 있음 | 전역 포워딩 규칙 $0.025/시간(ALB 필수) |
| 1.3 Google Media CDN | L7 | 기본 TTL 3,600, 프로토콜 캐시 키 제외, 영업 경유 활성화 | 미확인 | 미확인 |
| 1.4 Cloudflare CDN(프록시) | L7 | HTML·JSON 기본 미캐시, 헤더 없으면 200 = 120분; private/no-store/Set-Cookie 미캐시 단 Edge TTL override 시 무시·Set-Cookie 제거; 524 = 125초; 업로드 100 MB(Free/Pro) | ICN PoP | $0(Free) |
| 1.5 Vercel CDN 캐시 | L7 | s-maxage 필수, Set-Cookie·Authorization·private 있으면 미캐시, 10 MB, 캐시 키에 배포 ID | icn1 | 미확인 |
| 1.6 Netlify CDN 캐시 | L7 | 정적 자산 s-maxage 1년+배포 시 무효화, 동적 기본 미캐시, private 미저장 | 미확인 | 미확인 |
| 1.7 Fastly | L7 | 폴백 TTL 3,600(커스텀 VCL 120), private·Set-Cookie pass, 첫 바이트 15초, 퍼지 약 150 ms | 미확인 | 미확인 |

### DNS

| 구성 요소 | 계층 | 핵심 판정값 | 서울 | 최소 고정비 |
|---|---|---|---|---|
| 2.1 Route 53 | L7(DNS) | 헬스 체크 30/10초·threshold 3·18% 규칙; 전부 비정상이면 전부 정상(fail-open), 장애 조치 둘 다 비정상이면 primary; 별칭 TTL 지정 불가(ELB 60초)·별칭 쿼리 무료; 권장 TTL 60~120(장애 조치) | 글로벌(컨트롤 플레인 us-east-1, 헬스 체커 서울 없음) | 영역 $0.50/월 (+비AWS 헬스 체크 $0.75, 옵션 $1~2) |
| 2.2 Cloud DNS | L7(DNS) | WRR·GEO·FAILOVER; 외부 엔드포인트 헬스 체크는 공개 영역만(3리전×3프로버, 기본 5초); 전부 비정상이면 전부 정상; 기본 TTL 미명시(명시 필수) | 글로벌 | 영역 ≈$0.20/월 (+외부 헬스 체크 ≈$2/월) |
| 2.3 Cloudflare DNS | L7(DNS/프록시) | 프록시 TTL 300초 고정; DNS-only TTL 60~86400(Auto=300); apex CNAME flattening; 헬스 체크는 LB 애드온(Pro 최소 60초) | 글로벌 | DNS 0원, LB ≥$5/월 |
| 2.4 등록 기관 DNS (요약) | L7(DNS) | 헬스 체크·장애 조치 없음(추론); Squarespace 기본 TTL 4시간; Cloudflare Registrar는 Cloudflare NS 고정 | 미확인 | 도메인 요금 포함(미확인) ⚠️근거없음 |

### WAF·DDoS

| 구성 요소 | 계층 | 핵심 판정값 | 서울 | 최소 고정비 |
|---|---|---|---|---|
| 3.1 AWS WAF | L7 | 기본 규칙 없음(default_action 필수) · 레이트 창 60/120/300/600초(기본 300)·최소 10·키 기본 IP(XFF는 첫 값) · 본문 검사 ALB 8 KB 고정, CF 16→64 KB · CommonRuleSet 본문 >8 KB·UA 없음 Block | 있음 | web ACL $5 + 규칙 $1/월 + $0.60/100만 요청 |
| 3.2 Shield Standard | L3/L4 | 자동·무료 · L7 보호 없음 · 비용 보호 없음 | 글로벌 | $0 |
| 3.3 Shield Advanced | L3/L4/L7 | 명시적 보호 필요 · IPv4만 · SRT는 Business/Ent Support 필요 · 비용 보호는 Block 레이트 규칙 조건 | 있음 | $3,000/월 + 1년 약정 + DTO |
| 3.4 Cloud Armor Standard | L3/L4/L7 | 기본 규칙 deny[충돌: TF allow] · OWASP 기본 없음 · interval 10~3600초·throttle 1~1,000,000·ban 1~10,000·근사·리전별 · 본문 8~64 kB | 있음(추론) | 정책 ≈$5 + 규칙 ≈$1/월 + $0.75(글로벌)/$0.60(리전)/100만 ⚠️근거없음 |
| 3.5 Cloud Armor Enterprise | L3/L4/L7 | Adaptive Protection 전체 · 청구 보호 Annual만 · 외부 ALB 자동 계수 | 있음(추론) | Paygo $200/프로젝트/월 / Annual $3,000/월·1년 + 데이터 처리 ⚠️근거없음 |
| 3.6 Cloudflare WAF·DDoS | L3/L4/L7 | DDoS 무제한 전 플랜 · Free Managed Ruleset만 기본(Managed·OWASP는 Pro+) · 레이트 Free 10초·1규칙·IP, 카운터 데이터센터별 | 글로벌 | $0 (Pro $20/월~) |
| 3.7 Vercel Firewall (요약) | L3/L4/L7 | DDoS 전 플랜 · OWASP 관리형 Ent만 · 레이트 창 ≥10초·Hobby 1규칙·리전별 · 차단 요청 미과금 | 글로벌 | $0(플랜 포함) |

### 인증서

| 구성 요소 | 계층 | 핵심 판정값 | 서울 | 최소 고정비 |
|---|---|---|---|---|
| 4.1 ACM | TLS | 유효 198일; DNS 검증 + 사용 중 + CNAME 유지 시 45일 전 자동 갱신; EMAIL 수동·imported 미갱신; CloudFront는 us-east-1 | 있음 | 0원(내보내기 $7/FQDN) |
| 4.2 Google 관리형 인증서 | TLS | 90일, 약 30일 전 갱신; LB 승인은 DNS가 LB IP 가리켜야 발급·와일드카드 불가; DNS 승인은 사전 발급·와일드카드 | 일부(리전 인증서는 DNS 승인) | 0원(100개까지) |
| 4.3 Let's Encrypt + cert-manager | TLS | 90일(classic)→64일(2027-02)→45일(2028-02), shortlived 160시간; cert-manager 2/3 지점 갱신; 등록 도메인 주 50·동일 집합 주 5; 와일드카드는 DNS-01; 만료 메일·OCSP 종료 | 해당 없음 | 0원(미확인) |

### 출구 NAT·고정 IP

| 구성 요소 | 계층 | 핵심 판정값 | 서울 | 최소 고정비 |
|---|---|---|---|---|
| 5.1 AWS NAT GW 존 모드 | L3/L4 | 목적지별 동시 55,000 × IP(≤8, 기본 EIP 2) / 유휴 350초 고정 → RST / 5→100 Gbps, 1M→10M pps / 존 장애 범위 | 있음 | $43.07/월/AZ + $0.059/GB + EIP $3.65 |
| 5.2 AWS NAT GW 리전 모드 | L3/L4 | AZ당 IP ≤32(×55,000) / AZ 자동 확장(최대 60분) / 자동 모드는 EIP 자동 추가 / private NAT 불가 | 있음 | $0.059/시간 × 활성 AZ 수 + $0.059/GB + EIP |
| 5.3 NAT 인스턴스 | L3/L4 | 단일 장애점 / source-dest check 끔 / NAT AMI 지원 종료 / 처리 요금 없음 | 있음 | t4g.nano $3.80 + IPv4 $3.65 ≈ $7.5/월 |
| 5.4 Google Cloud NAT (Public) | L3/L4 | IP당 64,512 포트 / 정적 기본 64포트/VM, DPA 32~65,536 / TCP 1,200초·UDP 30초·TIME_WAIT 30/120초 / 고갈 시 drop(OUT_OF_RESOURCES) | 있음 | $0.0014×VM/시간(상한 $0.044) + $0.045/GiB + IP $0.005/시간 ≈ $4.7/월(VM 1) |
| 5.5.1 Cloud Run 고정 IP | L3 | Direct VPC + all-traffic + NAT MANUAL_ONLY / min_ports = 2×인스턴스 필요 | 있음 | Cloud NAT 비용 |
| 5.5.2 Lambda 고정 IP | L3 | VPC 사설 서브넷 + NAT EIP / 퍼블릭 서브넷은 인터넷 불가 | 있음 | NAT $43.07/월/AZ~ |
| 5.5.3 ECS Fargate 고정 IP | L3 | 사설+NAT EIP / 퍼블릭 IP는 태스크별·가변(추론) | 있음 | NAT 또는 IPv4 $3.65/태스크 ⚠️근거없음 |
| 5.5.4 Vercel Static IPs | L3 | 공유 IP 쌍(리전별), Functions만(Middleware 제외) / Secure Compute 전용 | 미확인 | $100/월/프로젝트 + 전송 |
| 5.5.5 Netlify Private Connectivity | L3 | Enterprise 애드온 / 함수 리전 cmh·fra·lhr | 없음 | 미확인(견적) |
| 5.5.6 Cloudflare Workers | L3/L7 | Dedicated CDN Egress IP(Enterprise), fetch()만, connect() 제외 | 글로벌 | 미확인(견적) |
| 5.5.7 Render | L3 | 기본 리전 공유 CIDR / 전용 IP 세트(3개, Pro+) | 미확인 | 세트당 월 요금(미확인) |
| 5.5.8 Fly.io | L3 | 기본 출구 IP 가변 / static egress IP, IP당 64 Machine | 미확인 | $3.60/월/IPv4 |
| 5.5.9 Railway | L3 | Pro, 공유 가능 IPv4, 리전 이동 시 변경 | 미확인 | 미확인 |
| 5.5.10 Heroku Private Spaces | L3 | 스페이스 전용 고정 IP 목록 | 미확인 | 미확인 |
| 5.6 퍼블릭 IPv4 | L3 | AWS 사용·유휴 동일 $0.005/시간 / GCP 미사용 정적 $0.01 / AWS 750시간 프리티어(사용 중만) / egress-only IGW 무료 | AWS 있음, GCP 서울값 미확인 | $3.65/월/IP |

### 사설 연결

| 구성 요소 | 계층 | 핵심 판정값 | 서울 | 최소 고정비 |
|---|---|---|---|---|
| 6.1 VPC 게이트웨이 엔드포인트 (S3·DynamoDB) | L3 | 대상 S3·DynamoDB만 · 같은 리전·VPC 안만(온프레미스/피어링/TGW 불가) · DNS 변경 없음(라우트+접두사 목록) · 출발지 IP가 사설로 바뀌어 `aws:SourceIp` 무효 | 있음 | $0 |
| 6.2 VPC 인터페이스 엔드포인트 (AWS 서비스) | L4 | 사설 DNS(숨은 PHZ, Terraform 기본 false) · 유휴 350초 고정 · AZ당 10→100Gbps, MTU 8500 · ECR 풀 = ecr.api+ecr.dkr+S3 게이트웨이(+logs, secretsmanager) | 있음 | $0.013/AZ·시간(1개·2AZ 월 $18.98) + $0.01/GB |
| 6.3 PrivateLink 엔드포인트 서비스·리소스 엔드포인트 | L4 | 제공자 NLB/GWLB 필수(리소스 엔드포인트는 RDS 직접, TCP만) · 소비자→제공자 단방향, 앱은 NLB IP만 봄 · 교차 리전(2024-11~) 서울 apne2-az2/az4 미지원 · NLB 커스텀 유휴 시 교차 리전 불가 | 있음 | 서비스 $0 + NLB, 교차 리전 원격 리전당 $0.05/시간, 리소스 엔드포인트 $0.026/시간 |
| 6.4 Lambda VPC 연결 (Hyperplane ENI) | L3/L4 | 퍼블릭 서브넷이어도 인터넷 불가 → NAT · ENI 생성 중 Pending(호출 불가), 14일 유휴 시 Inactive · Function URL은 공용 전용 · VPC 함수 625Mbps 상한 증설 불가 | 있음 | 연결 자체 $0, 실질 NAT 월 $43.07/AZ 또는 엔드포인트 |
| 6.5 Serverless VPC Access 커넥터 | L3 | /28 전용; min 2–max 10, 축소 안 함; IPv6 미지원; 서비스와 같은 리전·프로젝트 | 있음 | e2-micro 2대 ≈ $15.69/월(서울), f1-micro ≈ $13.48, e2-standard-4 ≈ $251 |
| 6.6 Direct VPC egress | L3 | 서브넷 /26 이상, IP 2×인스턴스(잡 1×); 인스턴스 쿼터 100–200; 시작 연결 지연 1분+, Cloud NAT 시 콜드 스타트 30초+ | 있음(추론) | $0 (트래픽만) ⚠️근거없음 |
| 6.7 Private Service Connect | L3/L4 | API용 엔드포인트는 피어링 VPC 접근 불가; 게시 서비스 엔드포인트는 서비스와 같은 리전; 글로벌 액세스 선택 | 있음(추론) | 엔드포인트 $0.01/h ≈ $7.30/월 + $0.01/GiB(게시 서비스) ⚠️근거없음 |
| 6.8 Cloud SQL 사설 IP | L3/L4 | PSA 범위 최소 /24 권장 /16, 전이 피어링 불가; PSC는 공인 IP·PSA 추가 불가, 클라이언트 IP 안 보임; 서버리스는 VPC 연결 필수 | 있음 | PSA $0, PSC ≈ $7.30/월+ |
| 6.9 Memorystore 사설 연결 | L3 | 공인 IP 없음 → 서버리스 VPC 연결 필수; Redis 기본 DIRECT_PEERING(변경 불가); Valkey는 PSC 정책 선행 필수 | 일부(Valkey 있음, Redis 미확인) | 연결 $0(PSA·피어링), Valkey PSC 미확인 |
| 6.10 SaaS DB 사설 연결 | L4 | Supabase Team+·AWS만, Neon Scale·AWS만, PlanetScale Base 포함·GCP PSC 서울 있음, Atlas M10+, Upstash Pro/Enterprise [충돌] | 일부(PlanetScale GCP) | 플랜 조건 + 클라우드 엔드포인트 요금 |

---

# 1. CDN

## 1.1 Amazon CloudFront — 표준 배포(pay-as-you-go 기본, flat-rate 요금제 선택 가능)
- 계열: 네트워크-CDN
- 서울 리전: 글로벌(엣지). 서울 엣지 있음 — https://aws.amazon.com/cloudfront/features/ · "South Korea: Seoul (10)" · 2026-10-01

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L7 | 리버스 프록시(엣지에서 TLS 종단, 오리진에 새 연결) | 오리진으로는 HTTP/1.1로 전달 | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/RequestAndResponseBehaviorCustomOrigin.html · "CloudFront forwards requests to your custom origin using HTTP/1.1." · 2026-10-01 |
| NW.idle_timeout | L7 | 오리진 keep-alive 기본 5초, 범위 1–300초(쿼터, 상향 요청 가능) | 커스텀·VPC 오리진만. 뷰어 쪽 유휴 값은 `미확인`. [충돌] Terraform 문서는 "upper limit of 60"이라고 적음 | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/DownloadDistValuesOrigin.html · "For keep-alive timeout , the default is 5 seconds." · 2026-10-01 / https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cloudfront-limits.html · "Keep-alive timeout per origin ... 1-300 seconds" · 2026-10-01 / https://github.com/hashicorp/terraform-provider-aws/blob/main/website/docs/r/cloudfront_distribution.html.markdown · "By default, AWS enforces an upper limit of `60`." · 2026-10-01 ⚠️출처부적격 |
| NW.request_timeout | L7 | 오리진 응답 타임아웃 기본 30초, 범위 1–120초(쿼터, 상향 요청 가능). 연결 타임아웃 기본 10초×3회(최대 30초). 응답 완료 타임아웃(선택, 미설정 시 상한 없음) | 패킷 사이 대기에도 같은 값 적용. GET/HEAD는 재시도, POST/PUT/PATCH/DELETE/OPTIONS는 재시도 없이 끊음. 초과 시 504. [충돌] 쿼터 페이지 1–120초 vs Terraform 문서 "maximum is 60 seconds" | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/DownloadDistValuesOrigin.html · "For response timeout, the default is 30 seconds." · 2026-10-01 / https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cloudfront-limits.html · "Response timeout per origin ... 1-120 seconds" · 2026-10-01 / https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/RequestAndResponseBehaviorCustomOrigin.html · "CloudFront drops the connection and doesn't try again to contact the origin." · 2026-10-01 |
| NW.websocket | L7 | 지원(모든 배포에서 자동 활성). 유휴 10분이면 끊김 | 오리진 요청 정책에서 `Sec-WebSocket-Key`·`Sec-WebSocket-Version` 전달(또는 AllViewer) 필요. SSE 유휴 한도는 `미확인`(응답 타임아웃 적용으로 추론) | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-working-with.websockets.html · "WebSocket functionality is automatically enabled to work with any distribution." · 2026-10-01 / https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cloudfront-limits.html · "Origin response timeout (idle timeout) 10 minutes" · 2026-10-01 ⚠️근거없음 |
| NW.protocols | L7 | 뷰어: HTTP/1.1, HTTP/2, HTTP/3(TLS 1.3+SNI). gRPC 지원(HTTPS 종단 간, POST 허용, HTTP/2 필요). 오리진: HTTP/1.1 | Terraform `http_version` 기본 `http2` | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/DownloadDistValuesGeneral.html · "For viewers and CloudFront to use HTTP/3, viewers must support TLSv1.3 and Server Name Indication (SNI)." · 2026-10-01 / https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-using-grpc.html · "CloudFront only supports secure (HTTPS-based) gRPC connections." · 2026-10-01 |
| NW.body_size | L7 | 요청 본문 최대 64 GB, 캐시 가능 응답 최대 50 GB(GET만 캐시), 헤더+URL+쿼리 합 32,768바이트, URL 8,192바이트 | 헤더 초과 494, URL 초과 414 | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cloudfront-limits.html · "Maximum size of an HTTP request body. 64 GB" · 2026-10-01 / 같은 페이지 · "Maximum length of a URL 8,192 bytes" · 2026-10-01 |
| NW.draining | — | 해당 없음 | — | — |
| NW.health_check | L7 | 능동 헬스 체크 없음. 오리진 그룹 장애 조치는 요청 단위: 지정 상태 코드(400·403·404·416·429·500·502·503·504) 또는 연결 실패·타임아웃 시 보조 오리진으로 | GET·HEAD·OPTIONS만 장애 조치. POST 등은 장애 조치 안 함(gRPC도 불가) | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/high_availability_origin_failover.html · "CloudFront does not fail over when the viewer sends a different HTTP method (for example POST" · 2026-10-01 |
| NW.tls | TLS | 엣지에서 종단. 사용자 지정 인증서는 ACM us-east-1에서 발급·가져오기. 보안 정책 TLSv1.3_2025 / TLSv1.2_2025 / TLSv1.2_2021 등. 오리진 쪽 자체 서명·무효 인증서면 연결 끊음. 뷰어 mTLS 설정 항목 있음 | `minimum_protocol_version`은 `cloudfront_default_certificate = false`일 때만 | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cnames-and-https-requirements.html · "request (or import) the certificate in the US East (N. Virginia) Region ( us-east-1 )" · 2026-10-01 / https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/RequestAndResponseBehaviorCustomOrigin.html · "returns an invalid certificate or a self-signed certificate, CloudFront drops the TCP connection" · 2026-10-01 |
| NW.client_ip | L7 | `X-Forwarded-For`에 뷰어 IP 추가. `CloudFront-Viewer-Address`(IP:포트)는 오리진 요청 정책으로만 추가 가능 | 캐시 정책에는 넣을 수 없음 | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/RequestAndResponseBehaviorCustomOrigin.html · "adds an X-Forwarded-For header that includes the IP address of the viewer" · 2026-10-01 / https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/adding-cloudfront-headers.html · "CloudFront-Viewer-Address and CloudFront-Viewer-ASN can be added in an origin request policy, but not in a cache policy." · 2026-10-01 |
| NW.routing | L7 | 경로 패턴별 캐시 동작(배포당 75개), 오리진 100개, 오리진 그룹 10개, 대체 도메인 100개 | 배포 앞에 배포를 2단 넘게 두면 403 | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cloudfront-limits.html · "Cache behaviors per distribution 75" · 2026-10-01 |
| NW.scaling | L7 | 배포당 150 Gbps, 250,000 RPS(쿼터, 상향 가능, flat-rate 요금제에는 미적용). 요청 합치기(같은 캐시 키만) 기본 동작 | 캐시 키에 쿠키·헤더가 들어가면 합쳐지지 않음 | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cloudfront-limits.html · "Requests per second per distribution ... 250,000" · 2026-10-01 / https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/RequestAndResponseBehaviorCustomOrigin.html · "CloudFront only collapses requests that share a cache key ." · 2026-10-01 |
| NW.availability | L7 | 글로벌 엣지(애니캐스트 아님, DNS 기반 — 추론). 업타임 SLA는 flat-rate Free/Pro에 없음, Business부터 | | https://aws.amazon.com/cloudfront/pricing/ · "Uptime SLA x x ✓ ✓ ✓" · 2026-10-01 ⚠️근거없음 |
| NW.caching | L7 | **관리형 정책** CachingOptimized(ID 658327ea-…): 최소 1초·기본 86,400초·최대 31,536,000초, 캐시 키에 쿼리·쿠키 없음, 정규화된 Accept-Encoding만. CachingDisabled(ID 4135ea2d-…): 0/0/0. UseOriginCacheControlHeaders: 최소 0·기본 0·최대 31,536,000, 캐시 키에 Host·Origin·X-HTTP-Method-Override 류 + **쿠키 전부**. **레거시 설정**(캐시 정책 미사용): 기본 TTL 86,400·최소 0·최대 31,536,000. **최소 TTL > 0이면 `no-cache`·`no-store`·`private`가 있어도 최소 TTL만큼 캐시**. 기본 캐시 키 = 배포 도메인 + URL 경로(+OPTIONS 메서드 구분) | Set-Cookie: 쿠키를 오리진에 전달(캐시 키에 포함)하면 응답 `Set-Cookie`도 캐시되어 **모든 캐시 히트에 재전송**. 막으려면 오리진이 `Cache-Control: no-cache="Set-Cookie"`. 쿠키 미전달이면 Set-Cookie를 응답에서 제거. 무효화: 경로·태그 단위, 와일드카드 1개=1경로, 초당 150 경로/태그, 와일드카드 초당 1개. 지연 [충돌]: "within a few seconds"(개발자 가이드) vs "several minutes"(백서) | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/using-managed-cache-policies.html · "Minimum TTL: 1 second. ... Default TTL: 86,400 seconds (24 hours)." · 2026-10-01 / https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Expiration.html · "If your minimum TTL is greater than 0, CloudFront uses the cache policy’s minimum TTL, even if the Cache-Control: no-cache , no-store , and/or private directives are present" · 2026-10-01 / https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/DownloadDistValuesCacheBehavior.html · "The default value for Default TTL is 86400 seconds (one day)." · 2026-10-01 / https://docs.aws.amazon.com/whitepapers/latest/build-static-websites-aws/controlling-how-long-amazon-s3-content-is-cached-by-amazon-cloudfront.html · "Minimum TTL (default is 0 seconds)" · 2026-10-01 / https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Cookies.html · "CloudFront also caches the Set-Cookie headers with the object returned from the origin, and sends those Set-Cookie headers to viewers on all cache hits." · 2026-10-01 / https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/understanding-the-cache-key.html · "The URL path of the requested object" · 2026-10-01 / https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Invalidation_Requests.html · "CloudFront forwards the request to all edge locations within a few seconds" · 2026-10-01 / https://docs.aws.amazon.com/whitepapers/latest/build-static-websites-aws/controlling-how-long-amazon-s3-content-is-cached-by-amazon-cloudfront.html · "It takes several minutes from the time you submit one to the time that CloudFront actually expires the content." · 2026-10-01 |
| NW.security | L7 | AWS WAF 웹 ACL 연결(`web_acl_id`), 상시 DDoS 보호(Shield Standard 포함 — 추론), 지역 제한, 서명 URL·쿠키(키 그룹), OAC로 S3 오리진 직접 접근 차단 | flat-rate 요금제는 WAF 웹 ACL 연결 필수·분리 불가 | https://aws.amazon.com/cloudfront/pricing/ · "Always-on DDoS Protection ✓ ✓ ✓ ✓ ✓" · 2026-10-01 / https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html · "We recommend that you use OAC instead because it supports" · 2026-10-01 / https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/flat-rate-pricing-plan.html · "You must have a AWS WAF Web ACL associated with your distribution if you're using a pricing plan." · 2026-10-01 ⚠️근거없음 |
| NW.dns | — | 배포 도메인 `dxxxx.cloudfront.net`, 대체 도메인(CNAME) 배포당 100개. Route 53 별칭은 DNS 절 참조(`미확인` 여기서) | | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cloudfront-limits.html · "Alternate domain names (CNAMEs) per distribution ... 100" · 2026-10-01 |
| NW.egress | — | 해당 없음 | — | — |
| NW.private_connectivity | L7 | VPC 오리진(사설 ALB·EC2를 공개 노출 없이 오리진으로) 지원. flat-rate는 Business 이상 | Terraform `aws_cloudfront_vpc_origin` 존재(Checkov 인덱스에 등장) | https://aws.amazon.com/cloudfront/pricing/ · "Private Origins Within VPC x x ✓ ✓ ✓" · 2026-10-01 |
| NW.regions | — | 글로벌. 서울 엣지 10개 | 요금 지역 "Asia Pacific"에 한국 포함 | https://aws.amazon.com/cloudfront/features/ · "South Korea: Seoul (10)" · 2026-10-01 |
| NW.cost_floor | — | 0원(pay-as-you-go, 상시 무료 1 TB·1,000만 요청/월). flat-rate Free $0 / Pro $15 / Business $200 / Premium $1,000(배포당 월) | 아래 비용 구조 | https://aws.amazon.com/cloudfront/pricing/ · "Monthly price per distribution $0/month ... $15/month ... $200/month ... $1,000/month" · 2026-10-01 |

### 비용 구조
- 상시 무료: 월 1 TB 인터넷 전송, HTTP/HTTPS 요청 1,000만 건, CloudFront Functions 200만 회 — https://aws.amazon.com/cloudfront/pricing/pay-as-you-go/ · "1 TB of data transfer out to the internet per month" · 2026-10-01
- 한국 포함 Asia Pacific 요금 지역 — 같은 페이지 · "Hong Kong, Indonesia, Philippines, Singapore, South Korea, Thailand, Malaysia, and Vietnam" · 2026-10-01
- [PL AmazonCloudFront] `AP-DataTransfer-Out-Bytes`: "$0.120 per GB - first 10 TB / month data transfer out", 다음 40 TB $0.1, 다음 100 TB $0.095, 다음 350 TB $0.09 … 5 PB 초과 $0.060
- [PL] `AP-Requests-Tier2-HTTPS`: "$0.012 per 10,000 HTTPS Requests"; `AP-Requests-Tier1`: "$0.0090 per 10,000 HTTP Requests"
- [PL] `AP-DataTransfer-Out-OBytes`: "$0.060 per GB - All data transfer out to Origin (Asia)" (POST/PUT 본문 등 엣지→오리진 전송)
- [PL] `Invalidations`: "$0.000 per URL - first 1,000 URLs / month." / "$0.005 per URL - over 1,000 URLs / month." — 계정 전체 합산, 와일드카드·태그 1개 = 1경로 (https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/PayingForInvalidation.html · "A path that includes the * wildcard counts as one path" · 2026-10-01)
- [PL] `APN2-Requests-OriginShield`: "$0.009 per 10,000 Origin Shield Requests"(서울 Origin Shield)
- AWS 오리진→CloudFront 전송 무료 — https://aws.amazon.com/cloudfront/pricing/pay-as-you-go/ · "Any cacheable data transferred to CloudFront edge locations from AWS resources incurs no additional charge" · 2026-10-01
- flat-rate: 월 사용 허용량 Free 1M 요청·100 GB, Pro 10M·50 TB, Business 125M·50 TB, Premium 500M·50 TB. 초과 요금 없음, 대신 지속 초과 시 "traffic delivery might be adjusted"(더 먼 엣지·성능 조정). WAF·DDoS로 차단된 요청은 허용량에 안 셈 — https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/flat-rate-pricing-plan.html · "your traffic might be served from fewer or more distant edge locations" · 2026-10-01
- 과금 함정: 버전 파일명 대신 배포마다 다수 경로 무효화 → 1,000경로 초과분 과금. `/*` 한 번이면 1경로.

### 교체 계열 정보
- 캐시 제어 입력: 오리진 `Cache-Control`(`s-maxage` 우선, `max-age`, `Expires`), `stale-while-revalidate`·`stale-if-error` 지원. 뷰어 요청의 `Cache-Control`/`Pragma`는 무시.
- 캐시 키 구성은 캐시 정책(헤더·쿠키·쿼리), 오리진 전달은 오리진 요청 정책으로 분리. 다른 CDN으로 옮길 때 "s-maxage 기반 TTL"은 이식되지만, 최소 TTL 강제·쿠키 기반 캐시 키·Set-Cookie 캐시 동작은 CDN마다 다르다.
- 캐시 태그 무효화 지원(2026-04 출시) — https://aws.amazon.com/about-aws/whats-new/2026/04/cloudfront-invalidation-cache-tag/ · "invalidate all objects sharing a tag in one request" · 2026-10-01

### 함정
- **CachingOptimized(최소 TTL 1초)를 API·HTML 경로에 붙이면 `private`/`no-store` 응답도 최소 1초, 헤더 없는 응답은 86,400초 캐시된다.** 동적 경로는 CachingDisabled 또는 UseOriginCacheControlHeaders(최소 0).
- 최소 TTL > 0 또는 최대 TTL > 0 이면 오리진 장애 시 이전 객체를 계속 내보냄. 막으려면 `Cache-Control: stale-if-error=0` (Expiration.html).
- UseOriginCacheControlHeaders는 **쿠키 전부를 캐시 키에 포함** → 오리진이 캐시 가능한 응답에 `Set-Cookie`를 붙이면 그 Set-Cookie가 캐시되어 같은 쿠키 조합 사용자에게 재전송(세션 고정 위험). 쿠키가 없는 첫 방문자들끼리 같은 키를 공유한다는 점에서 위험(추론). ⚠️근거없음
- 쿠키를 전달하면 `If-Modified-Since`/`If-None-Match` 조건부 요청 미지원 (Cookies.html).
- 오리진 그룹 장애 조치는 GET/HEAD/OPTIONS만. 쓰기 경로의 F1 요구는 CloudFront로 해결 안 됨.
- 오리진 응답 타임아웃 기본 30초 → A2가 "수십 초 이상"이면 504. 상향은 쿼터 요청 + 배포 설정 둘 다 필요.
- 오리진 keep-alive 기본 5초: 오리진(ALB 60초 등) 유휴 타임아웃보다 짧으므로 기본값은 안전(추론). 키울 때는 오리진 유휴 타임아웃보다 작게. ⚠️근거없음
- ACM 인증서는 us-east-1에 있어야 함(서울 리전 인증서 불가).
- S3 웹사이트 엔드포인트를 오리진으로 쓰면 OAC 불가(커스텀 오리진 취급).
- flat-rate 요금제: 실시간 로그·연속 배포(스테이징)·Anycast IP 목록 등 미지원 기능이 있으면 가입 불가.

### 생성 산출물
- Terraform 리소스: `aws_cloudfront_distribution` (https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudfront_distribution), `aws_cloudfront_cache_policy` (https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudfront_cache_policy), `aws_cloudfront_origin_access_control` (https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudfront_origin_access_control), `aws_cloudfront_origin_request_policy` (https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudfront_origin_request_policy), `aws_cloudfront_vpc_origin`(존재 확인: Checkov 인덱스)
- 요구에 따라 반드시 명시할 속성:
  - `ordered_cache_behavior.cache_policy_id` / `default_cache_behavior.cache_policy_id` → C4(개인화 응답·API 경로) 있으면 해당 경로에 CachingDisabled `4135ea2d-6df8-44a3-9df3-4b5a84be39ad` 또는 `min_ttl = 0` 사용자 정책. 정적 자산 경로만 CachingOptimized `658327ea-f89d-4fab-a63d-7e88639e58f6`.
  - `aws_cloudfront_cache_policy.min_ttl`(필수 인자) → F5·C4(개인정보·per-user) 경로면 0. `default_ttl`·`max_ttl` 명시.
  - `parameters_in_cache_key_and_forwarded_to_origin.cookies_config.cookie_behavior` → 세션 쿠키가 있는 앱(B1·F5)이면 캐시 경로에서 `none`, 쿠키 필요한 경로는 CachingDisabled + 오리진 요청 정책으로 전달.
  - `origin.custom_origin_config.origin_read_timeout` → A2 최대 처리 시간 + 여유(기본 30, 쿼터 내 최대 120).
  - `origin.custom_origin_config.origin_keepalive_timeout` → 오리진 유휴 타임아웃보다 작게(기본 5).
  - `origin.custom_origin_config.origin_protocol_policy = "https-only"`, `viewer_protocol_policy = "redirect-to-https"` → F5.
  - `origin_request_policy_id` → A3(웹소켓)이면 AllViewer 또는 `Sec-WebSocket-*` 전달 정책.
  - `origin_group.failover_criteria.status_codes` → F1(읽기 경로 가용성)일 때 `[500, 502, 503, 504]`.
  - `origin.origin_access_control_id` + `aws_cloudfront_origin_access_control { origin_access_control_origin_type = "s3", signing_behavior = "always", signing_protocol = "sigv4" }` → S3 정적 오리진.
  - `viewer_certificate.acm_certificate_arn`(us-east-1) + `minimum_protocol_version = "TLSv1.2_2021"` 이상 → F5.
  - `web_acl_id` → F5·D1 공개 서비스.
  - `http_version = "http2and3"` (선택), `grpc_config.enabled` → gRPC 경로.
- Checkov(실재 확인, https://www.checkov.io/5.Policy%20Index/terraform.html): ⚠️출처확인필요
  - CKV_AWS_68 "CloudFront Distribution should have WAF enabled"
  - CKV_AWS_86 "Ensure CloudFront distribution has Access Logging enabled"
  - CKV_AWS_174 "Verify CloudFront Distribution Viewer Certificate is using TLS v1.2 or higher"
  - CKV_AWS_305 "Ensure CloudFront distribution has a default root object configured"(API 전용 배포에선 오탐 가능 — 추론) ⚠️근거없음
  - CKV_AWS_310 "Ensure CloudFront distributions should have origin failover configured"
  - CKV_AWS_34 "Ensure CloudFront distribution ViewerProtocolPolicy is set to HTTPS"
  - CKV_AWS_216 "Ensure CloudFront distribution is enabled"
  - CKV_AWS_374 "Ensure AWS CloudFront web distribution has geo restriction enabled"
  - CKV_AWS_259 "Ensure CloudFront response header policy enforces Strict Transport Security"
  - CKV2_AWS_32 "Ensure CloudFront distribution has a response headers policy attached"
  - CKV2_AWS_42 "Ensure AWS CloudFront distribution uses custom SSL certificate"
  - CKV2_AWS_46 "Ensure AWS CloudFront Distribution with S3 have Origin Access set to enabled"
  - CKV2_AWS_47 "Ensure AWS CloudFront attached WAFv2 WebACL is configured with AMR for Log4j Vulnerability"
  - CKV2_AWS_54 "Ensure AWS CloudFront distribution is using secure SSL protocols for HTTPS communication"
  - CKV2_AWS_72 "Ensure AWS CloudFront origin protocol policy enforces HTTPS-only"
  - 최소 TTL·Set-Cookie 캐시 관련 체크: 해당 체크 없음
- 배포 후 검증:
  - `curl -sI https://<도메인>/static/app.js` 두 번 → 두 번째 `x-cache: Hit from cloudfront`, `age:` 증가
  - `curl -sI https://<도메인>/api/me -H 'Cookie: session=…'` 두 번 → 둘 다 `x-cache: Miss from cloudfront` 또는 `RefreshHit` 아님, `age` 헤더 없음(개인화 경로 미캐시)
  - `curl -sI https://<도메인>/` 응답에 캐시 히트인데 `set-cookie:`가 있으면 실패(Set-Cookie 캐시)
  - `aws cloudfront get-distribution-config --id <ID> --query 'DistributionConfig.Origins.Items[].CustomOriginConfig.[OriginReadTimeout,OriginKeepaliveTimeout]'` → 기대값
  - `aws cloudfront create-invalidation --distribution-id <ID> --paths '/*'` 후 `aws cloudfront wait invalidation-completed --distribution-id <ID> --id <INV>`
  - `openssl s_client -connect <도메인>:443 -servername <도메인> -tls1_1 </dev/null` → 핸드셰이크 실패(TLS1.2 이상 강제)
  - S3 오리진: `curl -sI https://<bucket>.s3.ap-northeast-2.amazonaws.com/index.html` → 403(OAC로 직접 접근 차단)

---

## 1.2 Google Cloud CDN — 전역 외부 Application Load Balancer 백엔드 서비스/백엔드 버킷
- 계열: 네트워크-CDN
- 서울 리전: 글로벌(엣지). 서울 캐시 위치 있음 — https://cloud.google.com/cdn/docs/locations · "Seoul, South Korea" · 2026-10-01

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L7 | 전역 외부 ALB(또는 클래식 ALB)의 백엔드 서비스·백엔드 버킷에 붙는 캐시 | ALB 없이 단독 사용 불가 | https://cloud.google.com/cdn/docs/overview · "Cloud CDN works with the global external Application Load Balancer or the classic Application Load Balancer" · 2026-10-01 |
| NW.idle_timeout | L7 | ALB 쪽 값을 따름(LB 절 참조). 웹소켓 유휴 = 백엔드 서비스 타임아웃(기본 30초) | | https://cloud.google.com/load-balancing/docs/backend-service · "After this time has passed without any data transmitted, the proxy closes the connection. Default value: 30 seconds" · 2026-10-01 |
| NW.request_timeout | L7 | 백엔드 서비스 타임아웃 기본 30초, 범위 1–2,147,483,647초 | 캐시 미스 시 적용 | https://cloud.google.com/load-balancing/docs/backend-service · "The default value is 30 seconds. The full range of timeout values allowed is 1 - 2,147,483,647 seconds." · 2026-10-01 |
| NW.websocket | L7 | ALB가 별도 설정 없이 프록시(캐시 대상 아님) | 연결 시간 한도는 LB 종류별 백엔드 서비스 타임아웃 | https://cloud.google.com/load-balancing/docs/https · "The load balancer doesn't require any configuration to proxy WebSocket connections." · 2026-10-01 |
| NW.protocols | L7 | HTTP/1.1, HTTP/2, HTTP/3(ALB·Cloud CDN·클라이언트 사이), 백엔드 HTTP/HTTPS/HTTP2/H2C | | https://cloud.google.com/load-balancing/docs/https · "HTTP/3 is supported between the external Application Load Balancer, Cloud CDN, and clients." · 2026-10-01 |
| NW.body_size | L7 | 캐시 가능한 응답 최대 100 GiB(오리진이 Range 지원), Range 미지원이면 10 MiB. 초과분은 캐시 안 하고 전달 | 요청 본문 한도는 ALB 절(`미확인` 여기서) | https://cloud.google.com/cdn/docs/caching · "100 GiB (107,374,182,400 bytes) 10 MiB (10,485,760 bytes)" · 2026-10-01 |
| NW.draining | — | 해당 없음(ALB 백엔드 서비스 설정) | — | — |
| NW.health_check | — | 해당 없음(ALB 헬스 체크). 오리진 불가 시 기본 86,400초까지 stale 제공(serve while stale) | | https://cloud.google.com/cdn/docs/caching · "Serves stale content for up to 24 hours if the origin is unreachable." · 2026-10-01 |
| NW.tls | TLS | ALB 프런트엔드에서 종단(Google 관리 인증서 등, LB·인증서 절 참조) | | https://cloud.google.com/cdn/docs/setting-up-cdn-with-bucket · "We recommend using a Google-managed certificate" · 2026-10-01 |
| NW.client_ip | L7 | `X-Forwarded-For: [<supplied-value>,]<client-ip>,<load-balancer-ip>` | 사용자 지정 응답 헤더 일부는 Cloud CDN과 함께 불가(전역 외부 ALB 표) | https://cloud.google.com/load-balancing/docs/https · "X-Forwarded-For : [<supplied-value>,]<client-ip>,<load-balancer-ip>" · 2026-10-01 |
| NW.routing | L7 | ALB URL 맵(경로·호스트) | LB 절 참조 | https://cloud.google.com/cdn/docs/overview · "If the load balancer URL map routes traffic to a backend service or backend" · 2026-10-01 |
| NW.scaling | L7 | 요청 합치기 기본 활성(엣지 노드당 같은 캐시 키 1회 채움). 처리량 쿼터 `미확인` | 캐시 키가 다르면 합쳐지지 않음 | https://cloud.google.com/cdn/docs/caching · "Request collapsing is enabled by default." · 2026-10-01 |
| NW.availability | L7 | 글로벌 엣지(전역 애니캐스트 IP는 ALB) | SLA `미확인` | https://cloud.google.com/cdn/docs/overview · "The external Application Load Balancer provides the frontend IP" · 2026-10-01 |
| NW.caching | L7 | **캐시 모드 기본 CACHE_ALL_STATIC**(gcloud/REST 생성 시): 헤더 없으면 정적 MIME(css/js/font/image/video/audio/pdf)만 캐시, **HTML·JSON은 기본 미캐시**. USE_ORIGIN_HEADERS: 유효 캐시 지시자 필수. **FORCE_CACHE_ALL: 오리진 지시자 무시하고 성공 응답 전부 캐시(private 포함 위험)**. 기본 TTL 3,600초, 최대 TTL 86,400초, 클라이언트 TTL 3,600초(각 최대 31,622,400초). `--default-ttl=0`이면 매번 재검증. 기본 캐시 키 = 프로토콜 + 호스트 + 경로 + 쿼리 전체. 미캐시 조건: 응답 `Set-Cookie`, `Cache-Control: private`/`no-store`(FORCE_CACHE_ALL 제외), 요청 `no-store`, 요청 `Authorization`(응답이 `public`/`must-revalidate`/`s-maxage`면 캐시), 허용 목록 밖 `Vary`. 네거티브 캐싱 기본 꺼짐. 무효화: 분당 500건, 각 약 10초 반영, 객체 수·크기 무제한, 캐시 태그(요청당 10개) 지원 | 서명 URL로 접근하면 `Cache-Control`과 무관하게 캐시 대상이 될 수 있음 | https://cloud.google.com/cdn/docs/caching · "This behavior is the default for Cloud CDN-enabled backends created by using the Google Cloud CLI or the REST API." · 2026-10-01 / 같은 페이지 · "Unconditionally caches successful responses, overriding any cache directives set by the origin." · 2026-10-01 / 같은 페이지 · "Sets a 1-hour cache duration if the origin provides no headers." · 2026-10-01 / 같은 페이지 · "The absolute maximum time (24 hours) an object remains in the cache." · 2026-10-01 / 같은 페이지 · "Other content types, such as HTML ( text/html ) and JSON ( application/json ), are not cached by default" · 2026-10-01 / 같은 페이지 · "If a response is cacheable based on its MIME type but has a Cache-Control response header of private or no-store , or a Set-Cookie header, it isn't cached." · 2026-10-01 / 같은 페이지 · "The entire query string is part of the cache key." · 2026-10-01 / https://cloud.google.com/cdn/docs/using-ttl-overrides · "31,622,400 seconds (1 year)" · 2026-10-01 / https://cloud.google.com/cdn/docs/cache-invalidation-overview · "You can submit up to 500 invalidation requests per minute. Each invalidation request takes effect in about 10 seconds." · 2026-10-01 |
| NW.security | L7 | 서명 URL·서명 쿠키(기본 캐시 최대 1시간), Cloud Armor는 WAF 절 참조 | | https://cloud.google.com/cdn/docs/using-signed-urls · "A signed URL is a URL that provides limited permission and time to make a request." · 2026-10-01 |
| NW.dns | — | 해당 없음(ALB IP에 A 레코드) | — | — |
| NW.egress | — | 해당 없음 | — | — |
| NW.private_connectivity | — | 해당 없음(백엔드 연결은 ALB) | — | — |
| NW.regions | — | 글로벌, 서울 캐시 위치 있음 | | https://cloud.google.com/cdn/docs/locations · "Seoul, South Korea" · 2026-10-01 |
| NW.cost_floor | — | Cloud CDN 자체 고정비 없음. 전제인 전역 포워딩 규칙 첫 5개 $0.025/시간(≈ $18.25/월, 730시간 기준 추론) | | https://cloud.google.com/load-balancing/pricing · "First 5 forwarding rules $0.025 / 1 hour" · 2026-10-01 ⚠️근거없음 |

### 비용 구조
- 캐시 egress(Asia Pacific, 홍콩 포함, 서울 사용자 해당 — 추론): 0–10 TiB $0.09/GiB, 10–150 TiB $0.06, 150–1,000 TiB $0.05, 그 이상 $0.04 — https://cloud.google.com/cdn/pricing · "Asia Pacific(including Hong Kong) 0 byte to 10 tebibyte $0.09 / 1 gibibyte" · 2026-10-01 ⚠️근거없음
- 캐시 채움: 같은 대륙 안(아시아) $0.02/GiB, 대륙 간 $0.04/GiB — 같은 페이지 · "Inter-region cache fill (for example: between Asia Pacific and North America) $0.04 / 1 gibibyte" · 2026-10-01
- 캐시 조회 요청(GET/HEAD): $0.0075 / 10,000 — 같은 페이지 · "HTTP/HTTPS cache lookup requests $0.0075 / 10,000 count" · 2026-10-01
- 미캐시 응답: 조회 요청 + ALB 데이터 처리 + 일반 Compute/Storage 인터넷 전송 요금.
- 무효화 요금: 가격 페이지에 항목 없음 → `미확인`.
- 무료 등급: `미확인`.

### 교체 계열 정보
- 오리진 헤더 해석은 표준(`s-maxage`, `max-age`, `Expires`, `stale-while-revalidate`). 캐시 태그는 `Cache-Tag` 응답 헤더(태그당 120바이트, 객체당 50개).
- CloudFront에서 옮길 때: CloudFront 최소 TTL 강제 같은 동작은 없고, 대신 FORCE_CACHE_ALL이 같은 위험을 만든다. HTML 기본 미캐시라 CloudFront CachingOptimized보다 기본이 안전.

### 함정
- **FORCE_CACHE_ALL은 `private`·`no-store`를 무시**. 동적 HTML/API 백엔드에 쓰면 사용자 간 응답 누출. 비공개 버킷 접근(private bucket access)을 쓰면 FORCE_CACHE_ALL이 필수라 그 백엔드 버킷에는 정적만 둬야 함.
- 서명 URL로 보호한 개인 데이터는 `private`가 있어도 캐시될 수 있음.
- Cloud Storage 백엔드 버킷은 메타데이터 미지정 시 `Cache-Control: public, max-age=3600`을 보냄 → 배포 직후 1시간 옛 파일.
- Range 미지원 오리진이면 10 MiB 넘는 응답은 캐시 안 됨.
- 콘솔에서 만들 때와 gcloud/REST로 만들 때 기본 캐시 모드 설명이 "gcloud/REST" 기준. Terraform 기본은 `미확인`이므로 `cache_mode`를 항상 명시.
- 무효화 분당 500건 레이트 한도 — 배포마다 경로별로 쏘면 걸림.

### 생성 산출물
- Terraform 리소스: `google_compute_backend_service` (`enable_cdn`, `cdn_policy`) (https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_backend_service), `google_compute_backend_bucket` (https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_backend_bucket). 전제: `google_compute_url_map`, `google_compute_target_https_proxy`, `google_compute_global_forwarding_rule`(LB 절)
- 요구에 따라 반드시 명시할 속성:
  - `enable_cdn = true`
  - `cdn_policy.cache_mode` → C4 개인화·F5가 있는 백엔드 서비스는 `USE_ORIGIN_HEADERS`(또는 `CACHE_ALL_STATIC`), 절대 `FORCE_CACHE_ALL` 금지. 공개 정적 버킷만 `FORCE_CACHE_ALL` 허용.
  - `cdn_policy.default_ttl`, `max_ttl`, `client_ttl` → 명시(기본 3600/86400/3600).
  - `cdn_policy.cache_key_policy.include_host`/`include_protocol`/`include_query_string`/`query_string_whitelist` → 쿼리에 추적 파라미터가 많으면 화이트리스트.
  - `cdn_policy.negative_caching`, `negative_caching_policy` → 404 폭주(D3) 방어 시.
  - `cdn_policy.signed_url_cache_max_age_sec` → 서명 URL 사용 시.
  - `cdn_policy.serve_while_stale` → F1.
  - `cdn_policy.request_coalescing` (기본 활성) → D3.
  - `timeout_sec` (백엔드 서비스) → A2 최대 처리 시간 + 여유, A3 웹소켓 최대 연결 시간.
- Checkov: Cloud CDN(`google_compute_backend_service`의 cdn_policy, `google_compute_backend_bucket`) 관련 체크 없음(인덱스 grep 결과). 인접: CKV_GCP_4 "Ensure no HTTPS or SSL proxy load balancers permit SSL policies with weak cipher suites"(`google_compute_ssl_policy`).
- 배포 후 검증:
  - `curl -sI https://<도메인>/static/app.js` 두 번 → 두 번째 `age:` 헤더 존재(캐시 히트)
  - `curl -sI https://<도메인>/api/me` 두 번 → `age:` 없음
  - `gcloud compute backend-services describe <BS> --global --format='value(enableCDN,cdnPolicy.cacheMode,cdnPolicy.defaultTtl,cdnPolicy.maxTtl,timeoutSec)'` → `True USE_ORIGIN_HEADERS … `
  - `gcloud compute url-maps invalidate-cdn-cache <URL_MAP> --path '/*' --global` → 완료 후 다음 요청 `age:` 없음
  - 로그: `gcloud logging read 'resource.type="http_load_balancer" AND jsonPayload.cacheDecision:*' --limit 5`(캐시 결정 확인, 필드명 `미확인`)

---

## 1.3 Google Media CDN — (요약)
- 계열: 네트워크-CDN
- 서울 리전: 글로벌(위치 목록 `미확인`)

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L7 | 미디어·대용량 다운로드용 엣지 캐시(EdgeCacheService). Cloud CDN과 별개 제품, ALB 불필요(추론) | 사용하려면 영업 담당 통해 활성화 요청 | https://cloud.google.com/media-cdn/docs/overview · "Media CDN is optimized for high-throughput egress workloads, such as streaming video and large file downloads." · 2026-10-01 / 같은 페이지 · "contact your Google Cloud sales representative or account team to get it enabled for your project" · 2026-10-01 ⚠️근거없음 |
| NW.caching | L7 | 기본 CACHE_ALL_STATIC, 기본 TTL 3,600초, `includeProtocol: false`, 호스트·쿼리 포함, 네거티브 캐싱 꺼짐. `no-store`/`private`·`Set-Cookie` 응답은 미캐시. FORCE_CACHE_ALL 있음 | | https://cloud.google.com/media-cdn/docs/caching · "cacheMode : CACHE_ALL_STATIC defaultTtl : 3600s cacheKeyPolicy : includeProtocol : false" · 2026-10-01 / 같은 페이지 · "Does not cache responses that have no-store or private cache-control directives" · 2026-10-01 |
| NW.idle_timeout / NW.request_timeout / NW.websocket / NW.protocols / NW.body_size / NW.draining / NW.health_check / NW.tls / NW.client_ip / NW.routing / NW.scaling / NW.availability / NW.security | — | `미확인` | — | — |
| NW.dns / NW.egress / NW.private_connectivity | — | 해당 없음 | — | — |
| NW.regions | — | 글로벌 | | https://cloud.google.com/media-cdn/docs/overview · "Media CDN uses Google's global edge-caching infrastructure" · 2026-10-01 |
| NW.cost_floor | — | `미확인`(공개 가격표 확인 못 함, 영업 활성화 필요) | | — |

### 비용 구조
- `미확인`. 일반 웹앱에는 해당 없음(판정상 웹 가속은 Cloud CDN 선택).

### 교체 계열 정보
- 캐시 키에서 프로토콜을 기본 제외하는 점이 Cloud CDN과 다름.

### 함정
- 프로젝트 활성화가 영업 경유라 원클릭 배포 경로에 부적합(추론). ⚠️근거없음

### 생성 산출물
- Terraform 리소스: `google_network_services_edge_cache_service`, `google_network_services_edge_cache_origin` (https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/network_services_edge_cache_service) — 첫 리소스 문서 존재 확인, 두 번째는 `미확인`
- 요구에 따라 반드시 명시할 속성: `미확인`(이 계열에서는 생성 대상 아님)
- Checkov: 해당 체크 없음
- 배포 후 검증: `curl -sI https://<도메인>/<영상 세그먼트>` 두 번 → `age:` 증가

---

## 1.4 Cloudflare CDN — 프록시(orange cloud), Free/Pro/Business/Enterprise
- 계열: 네트워크-CDN
- 서울 리전: 글로벌(애니캐스트). 서울 PoP 있음 — https://www.cloudflarestatus.com/api/v2/components.json · "Seoul, South Korea - (ICN)" · 2026-10-01

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L7 | 리버스 프록시(DNS 레코드 `proxied = true`). 클라이언트↔Cloudflare, Cloudflare↔오리진 두 TCP 연결 | DNS-only(회색 구름)면 CDN 아님 | https://developers.cloudflare.com/fundamentals/reference/connection-limits/ · "there are often two established TCP connections" · 2026-10-01 |
| NW.idle_timeout | L4/L7 | 클라이언트 쪽 keep-alive(HTTP/1.1)·HTTP/2 유휴 400초(변경 불가). 오리진 쪽 Proxy Idle Timeout 900초, TCP keep-alive 간격 30초 | | https://developers.cloudflare.com/fundamentals/reference/connection-limits/ · "Connection Keep-Alive HTTP/1.1 | 400" · 2026-10-01 / 같은 페이지 · "Proxy Idle Timeout | 900" · 2026-10-01 |
| NW.request_timeout | L7 | **Proxy Read Timeout 125초**(초과 시 524), Enterprise만 최대 6,000초까지. Proxy Write Timeout 30초. 오리진 TCP 연결 완료 19초(522). (초기 가정의 "100초"는 과거 값: Terraform 문서 "Historically ... 100 seconds") | | https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-5xx-errors/error-524/ · "the origin did not provide an HTTP response before the default 125 seconds" · 2026-10-01 / 같은 페이지 · "Enterprise customers can increase the 524 timeout up to 6,000 seconds" · 2026-10-01 / https://github.com/cloudflare/terraform-provider-cloudflare/blob/main/docs/resources/ruleset.md · "Historically, the timeout value between two read options from Cloudflare to an origin server is 100 seconds." · 2026-10-01 |
| NW.websocket | L7 | 모든 플랜 지원(대시보드 Network에서 On). 유휴 시 종료(값 미공개, Enterprise만 조정), 코드 배포 시 서버 재시작으로 끊길 수 있음 | Argo와 비호환. 연결 수립 후 WAF 검사 없음 | https://developers.cloudflare.com/network/websockets/ · "WebSockets are supported on all Cloudflare plans." · 2026-10-01 / 같은 페이지 · "we may restart servers, which terminates WebSockets connections" · 2026-10-01 |
| NW.protocols | L7 | HTTP/2, HTTP/3, gRPC(프록시 엔드포인트) | 세부 플랜 조건 `미확인` | https://developers.cloudflare.com/network/grpc-connections/ · "Cloudflare offers support for gRPC to protect your APIs on any proxied gRPC endpoints" · 2026-10-01 |
| NW.body_size | L7 | **업로드 최대 Free 100 MB / Pro 100 MB / Business 200 MB / Enterprise 최대 5 GB**. 캐시 가능 파일 Free~Business 512 MB, Enterprise 기본 5 GB. URL 16 KB, 요청 헤더 128 KB | 초과 시 413(추론). 대안: 청크 업로드, DNS-only 레코드 | https://developers.cloudflare.com/cache/concepts/default-cache-behavior/ · "Max upload size | 100 MB | 100 MB | 200 MB | Up to 5 GB" · 2026-10-01 / 같은 페이지 · "Free, Pro and Business customers have a limit of 512 MB." · 2026-10-01 ⚠️근거없음 |
| NW.draining | — | 해당 없음 | — | — |
| NW.health_check | — | 해당 없음(Load Balancing 부가 상품, 월 $5부터) | | https://www.cloudflare.com/plans/application-services/ · "Load Balancing ... Starting at $5 per month" · 2026-10-01 |
| NW.tls | TLS | 엣지 종단. SSL 모드 Flexible이면 Cloudflare→오리진 평문 | `min_tls_version` 존 설정 | https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/flexible/ · "traffic from Cloudflare to the origin server is not" · 2026-10-01 |
| NW.client_ip | L7 | `CF-Connecting-IP`(오리진으로만 전송), `X-Forwarded-For` | | https://developers.cloudflare.com/fundamentals/reference/http-headers/ · "`CF-Connecting-IP` provides the client IP address connecting to Cloudflare to the origin web server." · 2026-10-01 |
| NW.routing | L7 | Cache Rules·Origin Rules 등 규칙 엔진(ruleset phase `http_request_cache_settings` 등) | | https://github.com/cloudflare/terraform-provider-cloudflare/blob/main/docs/resources/ruleset.md · "http_request_cache_settings" · 2026-10-01 |
| NW.scaling | L7 | 캐시 락으로 요청 합치기(데이터센터 단위) | | https://developers.cloudflare.com/cache/concepts/default-cache-behavior/ · "Cloudflare uses a cache lock to avoid sending duplicate requests to your origin." · 2026-10-01 |
| NW.availability | L3/L7 | 글로벌 애니캐스트 | SLA `미확인` | `미확인` ⚠️근거없음 |
| NW.caching | L7 | **기본 캐시 대상은 확장자 기준**(js, css, jpg, png, pdf, woff2 등). **HTML·JSON 기본 미캐시**. 헤더 없을 때 기본 Edge TTL: 200·206·301 = 120분, 302·303 = 20분, 404·410 = 3분. 브라우저 TTL 기본 4시간. Edge TTL 최소값 Free 2시간·Pro 1시간·Business/Ent 1초. **`private`·`no-store`·`no-cache`·`max-age=0`·`Set-Cookie`면 미캐시**. Origin Cache Control은 Free/Pro/Business에서 항상 켜짐. **Cache Rules "Eligible for cache" + Edge TTL "Ignore cache-control header and use this TTL"(override_origin) 또는 Status code TTL이면 Cache-Control을 완전히 무시하고, Set-Cookie를 제거한 뒤 캐시**. 기본 캐시 키 = scheme(오리진 쪽 스킴)+host+URI(쿼리 포함) + Origin 헤더 + method-override 류 헤더. 퍼지: Instant Purge, 단일 URL Free 800 URL/초, 호스트·태그·접두사·전체 Free 5회/분(버킷 25) | Pro 5회/초, Business 10회/초, Ent 50회/초. 요금 `미확인`(문서상 플랜 기능) | https://developers.cloudflare.com/cache/concepts/default-cache-behavior/ · "The Cloudflare CDN does not cache HTML or JSON by default." · 2026-10-01 / 같은 페이지 · "The `Cache-Control` header is set to `private`, `no-store`, `no-cache`, or `max-age=0`." · 2026-10-01 / 같은 페이지 · "200, 206, 301 | 120m" · 2026-10-01 / https://developers.cloudflare.com/cache/how-to/edge-browser-cache-ttl/ · "Minimum Edge Cache TTL | 2 hours | 1 hour | 1 second | 1 second" · 2026-10-01 / https://developers.cloudflare.com/cache/how-to/cache-rules/settings/ · "Completely ignore any cache-control header on the response and instead cache the response" · 2026-10-01 / https://developers.cloudflare.com/cache/concepts/cache-behavior/ · "In this case, Cloudflare removes the `Set-Cookie` and the asset is cached." · 2026-10-01 / https://developers.cloudflare.com/cache/how-to/cache-keys/ · "A default cache key includes: 1. Full URL" · 2026-10-01 / https://developers.cloudflare.com/cache/how-to/purge-cache/ · "Requests | 5 requests per minute | 5 requests per second | 10 requests per second | 50 requests per second" · 2026-10-01 |
| NW.security | L7 | WAF(초기 HTTP 101 요청에 적용), DDoS, 레이트 리밋 — WAF 절 참조 | | https://developers.cloudflare.com/network/websockets/ · "The initial HTTP 101 request is subject to WAF managed rules" · 2026-10-01 |
| NW.dns | — | Cloudflare DNS에서 `proxied` 레코드 필요(DNS 절 참조) | | https://github.com/cloudflare/terraform-provider-cloudflare/blob/main/docs/resources/dns_record.md · "`proxied` (Boolean) Whether the record is receiving the performance and security benefits of Cloudflare." · 2026-10-01 |
| NW.egress | — | 해당 없음 | — | — |
| NW.private_connectivity | — | Cloudflare Tunnel로 공개 IP 없는 오리진 연결 가능(세부는 사설 연결 절) | | https://developers.cloudflare.com/fundamentals/reference/connection-limits/ · "If you are using Cloudflare tunnels" · 2026-10-01 |
| NW.regions | — | 글로벌, 서울 ICN PoP | | https://www.cloudflarestatus.com/api/v2/components.json · "Seoul, South Korea - (ICN)" · 2026-10-01 |
| NW.cost_floor | — | Free 플랜 $0(모든 기능 표에 "Free … Yes"). Pro·Business 월 요금 `미확인` | | https://developers.cloudflare.com/cache/how-to/purge-cache/ · "| Availability | Yes | Yes | Yes | Yes |" · 2026-10-01 |

### 비용 구조
- 최소 고정비: Free $0. Pro/Business 정액 `미확인`(공식 가격 페이지에서 수치 추출 실패).
- 전송량 과금: `미확인`.
- 부가: Load Balancing 월 $5부터, Advanced Certificate Manager 월 $10부터 — https://www.cloudflare.com/plans/application-services/ · "Advanced Certificate Manager ... Starting at $10 per month" · 2026-10-01

### 교체 계열 정보
- 캐시 설정은 Page Rules(구식) → Cache Rules(ruleset). Edge TTL 모드: `respect_origin` / `bypass_by_default` / `override_origin`.
- `s-maxage`로 엣지 TTL, `max-age`로 브라우저 TTL 분리 가능. Origin Cache Control 끄기는 Enterprise 전용.
- 캐시 키에 오리진 스킴이 들어가 SSL 모드(Flexible→Full) 변경 시 캐시 전체 무효화 효과.

### 함정
- **"Cache Everything" + Edge TTL override(Ignore cache-control)를 사이트 전체에 걸면 `private` 응답이 캐시되고 `Set-Cookie`는 제거됨 → 로그인 깨짐·사용자 간 누출(추론: 문서상 cache-control 완전 무시).** ⚠️근거없음
- **524는 125초**(Enterprise 외 변경 불가). A2가 2분 넘으면 비동기 작업 패턴으로 바꾸거나 해당 호스트를 DNS-only로.
- 업로드 100 MB(Free/Pro) — A7 "큼"이면 프리사인드 URL로 스토리지 직접 업로드 또는 업로드 호스트 DNS-only.
- 웹소켓은 Cloudflare 배포 때 끊길 수 있음 → 클라이언트 재접속·하트비트 필수.
- HEAD 요청을 캐시 미스 시 GET으로 변환해 오리진에 보냄.
- Free 플랜 퍼지(태그·호스트·접두사·전체) 분당 5회 — 잦은 배포 + 퍼지 자동화가 막힘. 단일 URL 퍼지는 넉넉.
- SSL Flexible이면 오리진 구간 평문 + 오리진이 HTTPS 리다이렉트하면 무한 리다이렉트(추론). ⚠️근거없음

### 생성 산출물
- Terraform 리소스: `cloudflare_ruleset`(phase `http_request_cache_settings`, action `set_cache_settings`) (https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/ruleset), `cloudflare_zone_setting`(`setting_id`: `websockets`, `max_upload`, `proxy_read_timeout`, `min_tls_version`, `browser_cache_ttl`) (https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/zone_setting), `cloudflare_dns_record`(`proxied = true`) (https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/dns_record)
- 요구에 따라 반드시 명시할 속성:
  - `cloudflare_dns_record.proxied = true` → CDN 사용 시.
  - `cloudflare_ruleset.rules.action_parameters.cache` → 정적 경로만 `true`, API·HTML 개인화 경로(C4·F5)는 `false`(Bypass) 규칙.
  - `action_parameters.edge_ttl.mode` → 개인화 경로에 `override_origin` 금지. 정적 해시 자산에만 `override_origin` + `default`.
  - `action_parameters.browser_ttl.mode` → `respect_origin` 권장.
  - `action_parameters.cache_key.custom_key` → 추적 쿼리 제거 등. `cache_key.cache_deception_armor = true` → F5.
  - `action_parameters.read_timeout` → A2 > 125초일 때(Enterprise 전용).
  - `cloudflare_zone_setting setting_id = "websockets" value = "on"` → A3.
  - `cloudflare_zone_setting setting_id = "min_tls_version"` → F5에서 "1.2".
- Checkov: Cloudflare 리소스 체크 없음(인덱스 grep 결과 0건).
- 배포 후 검증:
  - `curl -sI https://<도메인>/static/app.js` 두 번 → `cf-cache-status: HIT`
  - `curl -sI https://<도메인>/api/me` → `cf-cache-status: DYNAMIC` 또는 `BYPASS`
  - `curl -sI https://<도메인>/login` 응답에 `set-cookie:` 존재 + `cf-cache-status: HIT`이면 실패
  - `dig +short <도메인>` → Cloudflare IP(104.x/172.64.x 등, 오리진 IP 아님)
  - `curl -s -o /dev/null -w '%{http_code}' -X POST --data-binary @101MB.bin https://<도메인>/upload` → Free/Pro에서 413(업로드 한도 확인)
  - 퍼지: `curl -X POST https://api.cloudflare.com/client/v4/zones/<ZONE>/purge_cache -H "Authorization: Bearer $CF_TOKEN" -d '{"files":["https://<도메인>/static/app.js"]}'` 후 `cf-cache-status: MISS`

---

## 1.5 Vercel CDN 캐시 — (요약)
- 계열: 네트워크-CDN
- 서울 리전: 있음(icn1) — https://vercel.com/docs/regions · "icn1 ap-northeast-2 Seoul, South Korea" · 2026-10-01

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L7 | 플랫폼 내장 CDN(모든 플랜) | | https://vercel.com/docs/edge-cache · "CDN caching is available for all deployments and domains on your account, regardless of the pricing plan" · 2026-10-01 |
| NW.body_size | L7 | 캐시 가능 응답 최대 10 MB(스트리밍 함수 20 MB) | | https://vercel.com/docs/edge-cache · "Response doesn't exceed 10MB in content length ( 20MB for streaming Vercel Function responses" · 2026-10-01 |
| NW.caching | L7 | 함수 응답은 `s-maxage` 있어야 캐시. 캐시 조건: GET/HEAD, `Range`·`Authorization` 요청 헤더 없음, 상태 200·404·410·301·302·307·308, **`set-cookie` 없음, `private`·`no-cache`·`no-store` 없음**, `Vary: *` 없음·고카디널리티 Vary(Cookie 등) 없음. 최대 캐시 1년(best-effort). 정적 파일은 배포 수명 동안 자동 캐시. 캐시 키 = 메서드 + URL + 호스트 + **고유 배포 URL** + 스킴(설정 불가) → 새 배포는 캐시 분리. 퍼지: 태그 invalidate(stale 제공 후 백그라운드 갱신) / delete. `CDN-Cache-Control`, `Vercel-CDN-Cache-Control` 지원. 상태 헤더 `x-vercel-cache`. `proxy-revalidate` 미지원 | 리전별로 분리된 캐시 | https://vercel.com/docs/edge-cache · "Response doesn't contain the set-cookie header." · 2026-10-01 / 같은 페이지 · "Response doesn't contain the private , no-cache or no-store directives in the Cache-Control header." · 2026-10-01 / 같은 페이지 · "Request doesn't contain Authorization header." · 2026-10-01 / https://vercel.com/docs/cdn-cache/purge · "The unique deployment URL" · 2026-10-01 / 같은 페이지 · "Cache keys are not configurable." · 2026-10-01 |
| NW.regions | — | 글로벌 CDN, 서울 icn1 | | https://vercel.com/docs/regions · "icn1 ap-northeast-2 Seoul, South Korea" · 2026-10-01 |
| NW.idle_timeout / NW.request_timeout / NW.websocket / NW.protocols / NW.draining / NW.health_check / NW.tls / NW.client_ip / NW.routing / NW.scaling / NW.availability / NW.security / NW.cost_floor | — | `미확인`(컴퓨트 절 소관) | — | — |
| NW.dns / NW.egress / NW.private_connectivity | — | 해당 없음 | — | — |

### 비용 구조
- `미확인`(플랫폼 요금 절 소관).

### 교체 계열 정보
- `s-maxage` 필수 → 다른 CDN으로 옮겨도 의미 유지. `Vercel-CDN-Cache-Control`은 Vercel 전용(다른 CDN에서 무시).

### 함정
- 개인화 응답에 `set-cookie`나 `private`가 있으면 안전하게 미캐시. 반대로 캐시하려던 응답에 미들웨어가 쿠키를 붙이면 영영 MISS(문서: 헤더를 전역 미들웨어 대신 라우트별로 두라는 권고 — 추론 요약). ⚠️근거없음
- 캐시 시간은 보장되지 않음(드물게 요청되는 객체는 퇴출).

### 생성 산출물
- Terraform 리소스: 해당 없음(코드 쪽 `Cache-Control`·`vercel.json` `headers`로 제어)
- 요구에 따라 반드시 명시할 속성: 응답 헤더 `Cache-Control: public, s-maxage=N, stale-while-revalidate=M`(C4 공개 읽기 경로만), 개인화 경로는 `private, no-store`.
- Checkov: 해당 체크 없음
- 배포 후 검증: `curl -sI https://<도메인>/api/x` 두 번 → `x-vercel-cache: HIT`(두 번째), 개인화 경로 `MISS`/`BYPASS`

---

## 1.6 Netlify CDN 캐시 — (요약)
- 계열: 네트워크-CDN
- 서울 리전: `미확인`

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L7 | 플랫폼 내장 CDN | | https://docs.netlify.com/build/caching/caching-overview/ · "Static asset responses on Netlify are cached on Netlify’s global edge nodes" · 2026-10-01 |
| NW.caching | L7 | 정적 자산 기본: `Netlify-CDN-Cache-Control: public, s-maxage=31536000, must-revalidate`, 브라우저 `Cache-Control: public, max-age=0, must-revalidate`. 동적 응답(Functions·Edge Functions·프록시) **기본 미캐시**. **새 배포가 해당 배포 컨텍스트 캐시 전체 무효화**. `private` → 공유 캐시 미저장, `no-store` → 미저장. `Netlify-Vary`(query·header·language·country·cookie)로 캐시 키 조정. 캐시 태그 `Netlify-Cache-Tag`/`Cache-Tag`(응답당 500개). `durable` 지시자로 엣지 간 공유 | 정적 자산은 짧은 `max-age` 지정해도 무시(최대 1년 fresh) | https://docs.netlify.com/build/caching/caching-overview/ · "Netlify-CDN-Cache-Control: public, s-maxage=31536000, must-revalidate" · 2026-10-01 / 같은 페이지 · "responses coming from Netlify Functions , Edge Functions , and proxies are not cached by default" · 2026-10-01 / 같은 페이지 · "all new deploys invalidate the cache for the given deploy context by default" · 2026-10-01 / 같은 페이지 · "using private means we don’t cache the response in our network" · 2026-10-01 |
| NW.idle_timeout / NW.request_timeout / NW.websocket / NW.protocols / NW.body_size / NW.draining / NW.health_check / NW.tls / NW.client_ip / NW.routing / NW.scaling / NW.availability / NW.security / NW.regions / NW.cost_floor | — | `미확인` | — | — |
| NW.dns / NW.egress / NW.private_connectivity | — | 해당 없음 | — | — |

### 비용 구조
- `미확인`.

### 교체 계열 정보
- `Netlify-CDN-Cache-Control` > `CDN-Cache-Control` > `Cache-Control` 순으로 구체적인 것 우선.

### 함정
- 응답의 `Set-Cookie` 처리 문서 확인 못 함 → `미확인`. 함수 응답을 캐시할 때 쿠키 응답은 `private` 명시 필요(추론). ⚠️근거없음

### 생성 산출물
- Terraform 리소스: 해당 없음(`netlify.toml` `[[headers]]` 또는 함수 응답 헤더)
- 요구에 따라 반드시 명시할 속성: 함수 응답 `Netlify-CDN-Cache-Control: public, s-maxage=N, durable`(공개 읽기만), 개인화는 `private`.
- Checkov: 해당 체크 없음
- 배포 후 검증: `curl -sI https://<도메인>/` → `cache-status:` 헤더(이름 `미확인`)와 `netlify-cdn-cache-control` 비노출 확인; 재배포 후 첫 요청 미스

---

## 1.7 Fastly — CDN 서비스(VCL) (요약)
- 계열: 네트워크-CDN
- 서울 리전: `미확인`

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L7 | 리버스 프록시 캐시(VCL 또는 Compute) | | https://www.fastly.com/documentation/guides/concepts/edge-state/cache/cache-freshness/ · "The standard VCL boilerplate (which is also included in any Fastly CDN service that does not use custom VCL)" · 2026-10-01 ⚠️출처확인필요 |
| NW.request_timeout | L7 | `first_byte_timeout` 기본 15,000 ms, `between_bytes_timeout` 기본 10,000 ms, `connect_timeout` 기본 1,000 ms. 초과 시 합성 503 | | https://github.com/fastly/terraform-provider-fastly/blob/main/docs/resources/service_vcl.md · "`first_byte_timeout` (Number) How long to wait for the first bytes in milliseconds. Default `15000`" · 2026-10-01 / https://www.fastly.com/documentation/reference/api/services/backend/ · "If exceeded, the connection is aborted and a synthetic 503 response will be presented instead." · 2026-10-01 ⚠️출처확인필요 |
| NW.caching | L7 | TTL 우선순위: `Surrogate-Control: max-age` > `Cache-Control: s-maxage` > `max-age` > `Expires`. 헤더 없으면 폴백 TTL 3,600초(사용자 지정 VCL이면 120초). 기본 VCL은 **`Cache-Control: private` → pass, `Set-Cookie` → pass**. `no-store` 단독 처리: 보일러플레이트 목록에 없음 → `미확인`(문서 예시는 Fastly 미캐시를 `private`로 설명). URL 퍼지 약 150 ms, soft purge 지원 | | https://www.fastly.com/documentation/guides/full-site-delivery/caching/controlling-caching/ · "the TTL is 3600 seconds. If you use custom VCL or Fiddle , the default is 120 seconds." · 2026-10-01 / https://www.fastly.com/documentation/guides/concepts/edge-state/cache/cache-freshness/ · "If the response has a Set-Cookie header, execute a return(pass) ." · 2026-10-01 / 같은 페이지 · "will not be cached by Fastly (the private directive)" · 2026-10-01 / https://www.fastly.com/documentation/guides/concepts/edge-state/cache/purging/ · "URL purges take around 150ms to complete" · 2026-10-01 ⚠️출처확인필요 |
| NW.idle_timeout / NW.websocket / NW.protocols / NW.body_size / NW.draining / NW.health_check / NW.tls / NW.client_ip / NW.routing / NW.scaling / NW.availability / NW.security / NW.regions / NW.cost_floor | — | `미확인` | — | — |
| NW.dns / NW.egress / NW.private_connectivity | — | 해당 없음 | — | — |

### 비용 구조
- `미확인`.

### 교체 계열 정보
- `Surrogate-Control`은 Fastly가 소비하고 하류(브라우저)에 전달 안 하는 용도(문서 예시). CloudFront·Cloudflare로 옮기면 `s-maxage`로 바꿔야 함(추론). ⚠️근거없음

### 함정
- 첫 바이트 타임아웃 15초 → A2 "수십 초"면 503. CloudFront(30초)·Cloudflare(125초)보다 짧음.
- 사용자 지정 VCL로 바꾸면 폴백 TTL이 3,600 → 120초로 바뀌고 UI 설정 무시.
- `no-store`만 보내고 `private`를 빼면 Fastly가 캐시할 가능성(추론) → 개인화 응답은 `private, no-store` 둘 다. ⚠️근거없음

### 생성 산출물
- Terraform 리소스: `fastly_service_vcl` (https://registry.terraform.io/providers/fastly/fastly/latest/docs/resources/service_vcl) ⚠️출처확인필요
- 요구에 따라 반드시 명시할 속성: `default_ttl`(명시), `backend.first_byte_timeout`(A2 + 여유), `backend.between_bytes_timeout`, `backend.connect_timeout`.
- Checkov: 해당 체크 없음
- 배포 후 검증: `curl -sI https://<도메인>/static/app.js` 두 번 → `x-cache: HIT`, `x-cache-hits` 증가; 개인화 경로 `x-cache: MISS`

---

# 2. DNS

## 2.1 Amazon Route 53 — 공개 호스팅 영역 + 헬스 체크(DNS 장애 조치)
- 계열: 네트워크-DNS
- 서울 리전: 글로벌(권한 DNS 데이터 플레인은 전 세계 PoP, 컨트롤 플레인은 us-east-1. 근거: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/route-53-concepts.html · "the control plane is located in the us-east-1 AWS Region and the data planes are globally distributed" · 2026-10-01)

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L7 | 권한 DNS(이름 해석만). 요청 데이터 경로 밖, 프록시 아님 | 클라이언트는 DNS 응답 IP로 LB/CDN에 직접 연결 (추론) | https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/route-53-concepts.html · "The data plane is the authoritative DNS service. It runs across over 200 Points of Presence (PoP) locations" · 2026-10-01 ⚠️근거없음 |
| NW.idle_timeout | — | 해당 없음 | | — |
| NW.request_timeout | — | 해당 없음 | | — |
| NW.websocket | — | 해당 없음 | | — |
| NW.protocols | — | 해당 없음 (DNS over UDP/TCP 일반 권한 응답. 512바이트 초과 응답은 TCP 재시도 유발) | 응답 크기 줄이려면 다중 값 응답(최대 8개) 권장 | https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/best-practices-dns.html · "If responses are larger than 512 bytes, many DNS resolvers must retry over TCP instead of UDP" · 2026-10-01 |
| NW.body_size | — | 해당 없음 | | — |
| NW.draining | — | 해당 없음 (DNS 변경 후 옛 IP로 가는 트래픽은 TTL 동안 지속 → 옛 엔드포인트는 최소 TTL 이상 유지해야 함, (추론)) | 변경 전파는 보통 1분 미만, GetChange `INSYNC`로 확인 | https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/best-practices-dns.html · "While propagation typically takes less than one minute globally" · 2026-10-01 ⚠️근거없음 |
| NW.health_check | L7 | 엔드포인트 헬스 체크: HTTP/HTTPS/TCP/문자열 일치/계산/CloudWatch 경보. 주기 30초(기본) 또는 10초(빠름, 생성 후 변경 불가). failure_threshold 기본 3(1~10). 18% 초과 체커가 정상이라 보면 정상. HTTP(S): 4초 안 TCP 연결 + 연결 후 2초 안 2xx/3xx. TCP: 10초. 문자열 일치: 상태 코드 후 2초 안 본문 수신, 본문 앞 5,120바이트 안에 문자열(최대 255자). HTTPS 체크는 인증서를 검증하지 않음. 체커 리전 최소 3개. 사설·비라우팅 IP는 체크 불가 | 신규 체크는 데이터 충분할 때까지 정상으로 간주. 비활성화한 체크는 항상 정상 | https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-failover-determining-health-of-endpoints.html · "If more than 18% of health checkers report that an endpoint is healthy, Route 53 considers it healthy." / "must be able to establish a TCP connection with the endpoint within four seconds ... respond with an HTTP status code of 2xx or 3xx within two seconds" / "HTTPS health checks don't validate SSL/TLS certificates" / "The string must appear entirely in the first 5,120 bytes" · 2026-10-01; https://docs.aws.amazon.com/Route53/latest/APIReference/API_HealthCheckConfig.html · "if you don't specify a value for FailureThreshold , the default value is three health checks ... Maximum value of 10" / "If you don't specify a value for RequestInterval , the default value is 30 seconds" · 2026-10-01; https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/health-checks-creating-values.html · "Route 53 cannot check the health of endpoints for which the IP address is in local, private, nonroutable, or multicast ranges" / "You must specify at least three Regions." · 2026-10-01 |
| NW.tls | — | 해당 없음 (TLS 종단 없음). HTTPS 헬스 체크는 TLS 1.0~1.2 지원 엔드포인트 필요, SNI는 HTTPS 기본 on(Terraform 기본값 설명) | 인증서 만료돼도 헬스 체크는 통과 → 인증서 만료 장애를 DNS 장애 조치로 못 잡음 | https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/health-checks-creating-values.html · "If you choose HTTPS, the endpoint must support TLS v1.0, v1.1, or v1.2." · 2026-10-01 |
| NW.client_ip | — | 해당 없음 (지연·지리·IP 기반 라우팅은 리졸버 IP 또는 EDNS0 client-subnet으로 위치 추정) | | https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-policy.html · "How Amazon Route 53 uses EDNS0 to estimate the location of a user" · 2026-10-01 |
| NW.routing | L7 | 단순, 장애 조치(액티브-패시브), 지리 위치, 지리 근접, 지연, IP 기반, 다중 값(정상 레코드 최대 8개 무작위), 가중치. IP 기반 외에는 사설 호스팅 영역에서도 가능. 가중치 0 레코드는 0보다 큰 레코드가 모두 비정상일 때만 고려 | 지리·지리 근접·지연 사용 시 기본(default) 레코드 없으면 일부 클라이언트는 응답 없음 | https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-policy.html · "Multivalue answer routing policy – Use when you want Route 53 to respond to DNS queries with up to eight healthy records selected at random." · 2026-10-01; https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/best-practices-dns.html · "always set a default, unless you want some clients to receive no answer responses" · 2026-10-01 |
| NW.scaling | — | 관리형(쿼리 처리 증설 불필요, (추론)). API는 계정당 초당 5요청 제한 → 레코드 많은 Terraform plan/apply 느려짐 | | https://github.com/hashicorp/terraform-provider-aws/blob/main/website/docs/r/route53_record.html.markdown · "AWS Route 53 enforces a 5 requests-per-second rate limit on all AWS Route 53 APIs for an AWS account" · 2026-10-01 ⚠️출처부적격 ⚠️근거없음 |
| NW.availability | L7 | 데이터 플레인(DNS 응답·헬스 체크)은 100% 가용 설계, SLA 크레딧은 월 가동률 100% 미만부터. 컨트롤 플레인(API·콘솔·레코드 변경)은 us-east-1. 공개 영역 "가속 복구" 켜면 us-east-1 장애 시 약 60분 안에 변경 재개 | SLA는 API·콘솔 제외. 장애 조치는 레코드 변경(컨트롤 플레인)이 아니라 헬스 체크(데이터 플레인)로 구성해야 함 | https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/best-practices-dns.html · "are globally distributed, and are designed for 100% availability" · 2026-10-01; https://aws.amazon.com/route53/sla/ · "Less than 100% but greater than or equal to 99.99% 10%" · 2026-10-01; https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/accelerated-recovery.html · "you can resume making DNS changes within about 60 minutes after AWS detects that the US East (N. Virginia) Region is impaired" · 2026-10-01 |
| NW.caching | — | 해당 없음 (HTTP 캐시 아님. DNS 캐시는 NW.dns의 TTL) | | — |
| NW.security | L7 | DNSSEC 서명(공개 영역, KSK는 고객 KMS 비대칭 키, ZSK는 Route 53 관리). 서명 시 TTL 최대 1주 강제. 다중 공급자 구성 불가. 부모 영역에 DS 필요 | DNSSEC 오류는 영역 전체 해석 불가로 이어짐 → `DNSSECInternalFailure`·`DNSSECKeySigningKeysNeedingAction` 경보 권장 | https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-configuring-dnssec.html · "each KSK is based on an asymmetric customer managed key in AWS KMS" / "Route 53 enforces a TTL of one week for the records" · 2026-10-01 |
| NW.dns | L7 | **TTL**: 비별칭 레코드는 TTL 필수, 권장 범위 60~172,800초. 헬스 체크 대상 레코드는 60 또는 120초, NS·MX 등은 3600~86400초. **별칭**: AWS 리소스 대상이면 TTL 지정 불가(리소스 기본 TTL 사용, ELB는 60초), 같은 영역 레코드 대상이면 그 레코드 TTL. 영역 apex에 생성 가능. AWS 리소스 대상 별칭 쿼리는 무료. **장애 조치 동작**: 헬스 체크 없는 레코드는 항상 정상. 그룹 전체가 비정상이면 전체를 정상으로 간주(fail-open). 장애 조치 레코드는 primary·secondary 모두 비정상이면 primary 반환. secondary에 헬스 체크 없으면 primary 비정상 시 무조건 secondary. 별칭은 `Evaluate Target Health=Yes`여야 대상 상태 반영, No면 대상이 모두 실패해도 그 가지로 계속 보냄 | 장애 조치 체감 시간 ≈ 탐지(주기×failure_threshold, 기본 30×3=90초) + TTL (추론) | https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/best-practices-dns.html · "The recommended range for TTL values is 60 to 172,800 seconds." / "Setting a TTL of 60 or 120 seconds is a common choice for this scenario." · 2026-10-01; https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resource-record-sets-choosing-alias-non-alias.html · "If an alias record points to an AWS resource, you can't set the time to live (TTL); Route 53 uses the default TTL for the resource." / "Route 53 doesn't charge for alias queries to AWS resources." · 2026-10-01; https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/how-elastic-load-balancing-works.html · "The DNS entry also specifies the time-to-live (TTL) of 60 seconds." · 2026-10-01; https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/health-checks-how-route-53-chooses-records.html · "If none of the records in a group of records are healthy ... Route 53 considers all the records in the group to be healthy" / "If Route 53 considers both the primary and secondary records unhealthy, Route 53 returns the primary record." / "Route 53 always responds to DNS queries by using the secondary record. This is true even if the secondary record is unhealthy." · 2026-10-01; https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-failover-complex-configs.html · "If you set Evaluate Target Health to No, Route 53 continues to route traffic to the records that an alias record refers to even if health checks for those records are failing." · 2026-10-01 ⚠️근거없음 |
| NW.egress | — | 해당 없음 | | — |
| NW.private_connectivity | L7 | 사설 호스팅 영역(VPC 연결)으로 VPC 안 이름 해석. 사설 영역 쿼리 무료. 단, 헬스 체크는 사설 IP 대상 불가 → 사설 엔드포인트 장애 조치는 CloudWatch 경보 기반 체크 필요 (추론) | | https://aws.amazon.com/route53/pricing/ · "Queries on private hosted zones are provided at no additional cost to Route 53 customers." · 2026-10-01; https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/health-checks-creating-values.html · "Route 53 cannot check the health of endpoints for which the IP address is in local, private, nonroutable, or multicast ranges." · 2026-10-01 ⚠️근거없음 |
| NW.regions | — | 글로벌 서비스. 헬스 체커 리전 선택지 8개(us-east-1, us-west-1, us-west-2, eu-west-1, ap-southeast-1, ap-southeast-2, ap-northeast-1, sa-east-1) — 서울 없음 | | https://github.com/hashicorp/terraform-provider-aws/blob/main/website/docs/r/route53_health_check.html.markdown · "Valid values are `us-east-1`, `us-west-1`, `us-west-2`, `eu-west-1`, `ap-southeast-1`, `ap-southeast-2`, `ap-northeast-1`, and `sa-east-1`." · 2026-10-01 ⚠️출처부적격 |
| NW.cost_floor | — | 호스팅 영역 $0.50/월(처음 25개, 비례 배분 없음, 생성 12시간 안 삭제 시 무료), 이후 $0.10. 영역당 레코드 10,000개 포함, 초과 $0.0015/레코드·월. 표준 쿼리 $0.40/백만(10억까지), 지연 $0.60, 지리·지리 근접 $0.70, IP 기반 $0.80. 헬스 체크 AWS 엔드포인트 50개 무료 후 $0.50, 비AWS $0.75, 옵션(HTTPS·문자열·10초·지연 측정) 각 $1.00(AWS)/$2.00(비AWS) [PL] | 최소 고정비 ≈ $0.50/월(영역 1개, 별칭만 쓰면 쿼리 0원) | [PL] https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonRoute53/current/index.csv · HostedZone "$0.50 per Hosted Zone for the first 25 Hosted Zones" / DNS-Queries "$0.40 per 1,000,000 queries for the first 1 Billion queries" / LBR-Queries "$0.60 per 1,000,000 LBR queries" / Geo-Queries "$0.70 per 1,000,000 Geo queries" / Cidr-Queries "$0.80 per 1,000,000 queries" / Intra-AWS-DNS-Queries "Queries to Alias records are free of charge" / Health-Check-AWS "First 50 Health Checks of AWS endpoints are free of charge", "$0.50 per Health Check for additional" / Health-Check-Non-AWS "$0.75 per Health Check" / Health-Check-Option-AWS "$1.00 per optional feature" / Health-Check-Option-Non-AWS "$2.00 per optional feature" / Global-RRSets "$0.0015 per extra RRSet within HostedZone" · 2026-10-01; https://aws.amazon.com/route53/pricing/ · "A hosted zone includes up to 10,000 records." / "The monthly hosted zone prices listed above are not prorated for partial months." · 2026-10-01 |

### 비용 구조
- 고정: 호스팅 영역 월 $0.50(비례 배분 없음). 헬스 체크는 AWS 엔드포인트 50개까지 무료이나 옵션 기능(HTTPS·문자열 일치·10초 주기·지연 측정)은 개당 $1/월(AWS), $2/월(비AWS) 추가 [PL].
- 변동: 쿼리 요금(정책별 단가 상이). AWS 리소스(ELB, CloudFront 등) 대상 별칭 A/AAAA 쿼리는 무료. CNAME이 같은 Route 53 영역 레코드를 가리키면 쿼리 2회로 과금.
- TTL을 짧게 하면 쿼리 수(비용) 증가 (공식: "This increases the query volume (and cost).", best-practices-dns).

### 교체 계열 정보
- 같은 계열: Cloud DNS(2.2), Cloudflare DNS(2.3), 등록 기관 DNS(2.4).
- 별칭(무료·apex 지원·대상 IP 자동 추적)은 Route 53 고유 확장. 다른 DNS로 옮기면 apex는 Cloudflare CNAME flattening 또는 Cloud DNS ALIAS 타입 등으로 대체 필요(동작 동일성은 (추론)). ⚠️근거없음
- DNSSEC 사용 중 공급자 이전은 DS 교체 절차 필요(다중 공급자 미지원).

### 함정
- **fail-open**: 그룹 전체가 비정상이면 모두 정상으로 간주 → 전 리전 장애 시 죽은 엔드포인트를 그대로 반환. 장애 조치 primary·secondary 모두 비정상이면 primary 반환.
- secondary에 헬스 체크를 안 걸면 primary 실패 시 secondary가 죽어 있어도 반환.
- 헬스 체크가 없는 레코드는 항상 정상 → 복합 트리에서 한 레코드만 빠져도 장애 조치가 막힘.
- 별칭 `evaluate_target_health=false`면 대상이 모두 실패해도 그 가지로 보냄.
- HTTPS 헬스 체크는 인증서 미검증 → 인증서 만료는 헬스 체크로 탐지 불가.
- 헬스 체커는 서울 리전에서 출발하지 않음, 사설 IP 체크 불가. 보안 그룹·WAF가 Route 53 헬스 체커 IP를 막으면 정상 서버가 비정상 판정 (추론). ⚠️근거없음
- 별칭 레코드는 TTL을 못 정함(ELB 60초 고정). TTL을 길게 쓰던 레코드를 장애 조치로 바꾸면 이전 TTL만큼 캐시가 남음.
- 장애 조치를 "레코드 수정"으로 설계하면 us-east-1 컨트롤 플레인 의존. 헬스 체크(데이터 플레인)로 설계해야 함.
- DNSSEC 켜면 TTL 1주 상한, KSK용 KMS 키 관리 책임, 부모 DS 미지원 등록 기관이면 영역 해석 불가.
- 지리·지연 정책에 기본 레코드 없으면 일부 사용자 NODATA.

### 생성 산출물
- Terraform 리소스: `aws_route53_zone` (https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_zone), `aws_route53_record` (https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record), `aws_route53_health_check` (https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_health_check), `aws_route53_hosted_zone_dnssec`, `aws_route53_key_signing_key`, `aws_route53_query_log` (원문: github.com/hashicorp/terraform-provider-aws `website/docs/r/*.html.markdown`, 프로바이더 최신 6.67.0 확인)
- 요구에 따라 반드시 명시할 속성:
  - `aws_route53_record.alias { name, zone_id, evaluate_target_health }` → ALB/CloudFront 대상이면 항상 별칭(무료·apex). F1(중단 허용 짧음)이면 `evaluate_target_health = true`. `alias`는 `ttl`·`records`와 충돌.
  - `aws_route53_record.ttl` → 비별칭 필수. F1 짧음/장애 조치 대상이면 60, 거의 안 바뀌는 레코드(MX·검증 TXT)는 3600 이상.
  - `failover_routing_policy { type = "PRIMARY" | "SECONDARY" }` + `set_identifier`(라우팅 정책 쓰면 필수) + `health_check_id` → F1 짧음·F2 있음(리전 장애 대비)일 때. secondary에도 `health_check_id` 지정(함정 참고).
  - `weighted_routing_policy { weight }` + `set_identifier` → F4(무중단 배포) 블루/그린·카나리 DNS 분할(단 TTL만큼 지연).
  - `latency_routing_policy { region }` / `geolocation_routing_policy` → D5 여러 지역. 기본(`*`) 레코드 반드시 포함.
  - `aws_route53_health_check { type = "HTTPS", fqdn, port = 443, resource_path, request_interval = 30|10, failure_threshold = 3, regions }` → F1 거의 0이면 `request_interval = 10`(옵션 요금), `failure_threshold` 2~3. `resource_path`는 앱 헬스 엔드포인트(2xx/3xx 2초 안). 문자열 확인 필요 시 `type = "HTTPS_STR_MATCH"`, `search_string`(본문 앞 5120바이트).
  - `aws_route53_hosted_zone_dnssec { hosted_zone_id, signing_status = "SIGNING" }` + `aws_route53_key_signing_key`(us-east-1 KMS ECC 키) → F5 규제·공공일 때.
- Checkov: `CKV2_AWS_38` "Ensure Domain Name System Security Extensions (DNSSEC) signing is enabled for Amazon Route 53 public hosted zones", `CKV2_AWS_39` "Ensure Domain Name System (DNS) query logging is enabled for Amazon Route 53 hosted zones", `CKV2_AWS_23` "Route53 A Record has Attached Resource", `CKV_AWS_377` "Ensure Route 53 domains have transfer lock protection"(aws_route53domains_registered_domain). 헬스 체크 관련 체크는 해당 체크 없음. (https://www.checkov.io/5.Policy%20Index/terraform.html, 2026-10-01) ⚠️출처확인필요
- 배포 후 검증:
  - `dig +noall +answer app.example.com A` → 기대: ALB/CloudFront IP, 별칭이면 TTL ≤ 60.
  - `dig +short NS example.com` → 영역의 `awsdns` 네임서버 4개와 일치(등록 기관 위임 확인).
  - `aws route53 get-health-check-status --health-check-id <id>` → 대부분 체커 `Success: HTTP Status Code 200`.
  - `aws route53 list-resource-record-sets --hosted-zone-id <id> --query "ResourceRecordSets[?Failover]"` → PRIMARY/SECONDARY 각각 `HealthCheckId` 존재.
  - 장애 조치 리허설: `aws route53 update-health-check --health-check-id <id> --inverted` 후 `dig +short @<awsdns NS> app.example.com` → secondary IP (TTL 경과 후 일반 리졸버에서도).
  - DNSSEC: `dig +dnssec example.com SOA` → `RRSIG` 존재, `dig DS example.com +short` → 값 존재.

## 2.2 Google Cloud DNS — 공개/비공개 관리 영역 + 라우팅 정책
- 계열: 네트워크-DNS
- 서울 리전: 글로벌(권한 DNS. 비공개 영역 지리 정책은 쿼리 출처 Google Cloud 리전 기준, 근거: routing-policies-overview)

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L7 | 권한 DNS(데이터 경로 밖) | | https://cloud.google.com/dns/sla · "Serving DNS queries from at least one of the Google managed Authoritative Name Servers" · 2026-10-01 |
| NW.idle_timeout | — | 해당 없음 | | — |
| NW.request_timeout | — | 해당 없음 | | — |
| NW.websocket | — | 해당 없음 | | — |
| NW.protocols | — | 해당 없음 | | — |
| NW.body_size | — | 해당 없음 | | — |
| NW.draining | — | 해당 없음 (장애 조치 정책의 backup `trickle_ratio`로 평시 일부 트래픽 흘려 예열 가능, 0~1, 통상 0.1) | | https://cloud.google.com/dns/docs/routing-policies-overview · "You can configure the percentage of the traffic sent to the backup as a fraction from 0 to 1 ... The typical value is 0.1." · 2026-10-01 |
| NW.health_check | L7 | 내부 LB(내부 ALB 리전·교차 리전, 내부 패스스루 NLB, 내부 프록시 NLB)와 **외부 엔드포인트** 헬스 체크 지원. 외부 엔드포인트 헬스 체크는 **공개 영역에서만**, 지정한 Google Cloud 소스 리전 3곳 × 리전당 프로버 3 = 9개가 체크. 기본 5초 프로브(변경 가능). 외부 fast: SSL/TCP/HTTP, premium: +HTTPS/HTTP2/gRPC·본문 검사. **모든 버킷 비정상이면 모두 정상처럼 동작(fail-open)** | 헬스 체크 대상 IP와 미대상 IP를 섞으면, 대상 IP가 모두 실패 시 미대상 IP를 반환하고 다음 지역 장애 조치 없음 | https://cloud.google.com/dns/docs/routing-policies-overview · "Health checks for external endpoints are only available in public zones." / "These health check probes originate from three Google Cloud source regions that you specify." / "If all policy buckets are unhealthy, Cloud DNS behaves as if all endpoints are healthy." / "When there's a mix and match of health-checked and non-health-checked IP addresses, and all the health-checked IP addresses fail, Cloud DNS returns all the IP addresses that don't have health checking configured." · 2026-10-01; https://cloud.google.com/dns/pricing · "External fast health checks Default 5s probes (configurable) • SSL, TCP, and HTTP protocols" · 2026-10-01 |
| NW.tls | — | 해당 없음 | | — |
| NW.client_ip | — | 해당 없음 | | — |
| NW.routing | L7 | WRR(가중치 라운드 로빈), 지리 위치(GEO, geofence 옵션), 장애 조치(FAILOVER: primary 세트, backup은 지리 정책). 공개·비공개 영역 모두 가능, 단 전달·피어링·역방향·Service Directory 영역은 불가 | geofence 켜면 해당 지역 전부 비정상이어도 다른 지역으로 안 넘김(IP 전부 그대로 반환) | https://cloud.google.com/dns/docs/routing-policies-overview · "You can configure DNS routing policies for resource record sets in private or public zones" / "DNS routing policies can't be configured for the following private zones: Forwarding zones DNS peering zones" / "when geofencing is enabled, this automatic failover doesn't occur" · 2026-10-01 |
| NW.scaling | — | 관리형. 쿼리 처리 증설 불필요 (추론) | | 미확인 ⚠️근거없음 |
| NW.availability | L7 | SLO 100%(권한 네임서버 중 최소 1개 응답 기준), 크레딧 99.5~<100% 10% | | https://cloud.google.com/dns/sla · "the Covered Service will provide a Monthly Uptime Percentage of Serving DNS queries ... of 100%" · 2026-10-01 |
| NW.caching | — | 해당 없음 | | — |
| NW.security | L7 | DNSSEC 관리형 영역 서명 지원. 등록 기관·레지스트리가 DS를 지원해야 효과 | DS를 못 넣으면 Cloud DNS에서 켜도 효과 없음 | https://cloud.google.com/dns/docs/dnssec · "If you cannot add a DS record through your domain registrar to activate DNSSEC, enabling DNSSEC in Cloud DNS has no effect." · 2026-10-01 |
| NW.dns | L7 | **TTL**: 레코드별 지정(양의 정수). 기본값은 문서에 명시 없음 — gcloud `record-sets create`의 `--ttl`은 선택 플래그이나 기본값 미기재, `transaction add`는 `--ttl` 필수, 문서 예시는 300. 라우팅 정책 예시 TTL 30. **ALIAS** 레코드 타입 지원(비표준, BIND 내보내기 시 생략). **장애 조치**: primary 전부 비정상이면 backup 반환, 모두 비정상이면 전체 정상 간주 | gcloud 기본 TTL "300"은 공식 문서로 확인 안 됨(미확인) | https://cloud.google.com/sdk/gcloud/reference/dns/record-sets/create · "--ttl = TTL TTL (time to live) for the record-set." · 2026-10-01; https://cloud.google.com/sdk/gcloud/reference/dns/record-sets/transaction/add · "REQUIRED FLAGS ... --ttl = TTL" · 2026-10-01; https://cloud.google.com/dns/docs/records · "TTL : the time to live (TTL) for the record set in number of seconds—for example, 300" / "Cloud DNS supports the ALIAS record type, which isn't a standard DNS record type" · 2026-10-01; https://cloud.google.com/dns/docs/routing-policies-overview · "When all IP addresses in the active set become unhealthy, Cloud DNS serves the IP addresses from the backup set." · 2026-10-01 |
| NW.egress | — | 해당 없음 | | — |
| NW.private_connectivity | L7 | 비공개 영역(VPC 대상)과 내부 LB 헬스 체크 기반 장애 조치 | 장애 조치 정책 설명이 "VPC 내부 리소스 고가용성" 중심 | https://cloud.google.com/dns/docs/routing-policies-overview · "The failover routing policy lets you set up active backup configurations to provide high availability for internal resources within your VPC network." · 2026-10-01 |
| NW.regions | — | 글로벌. 외부 헬스 체크 소스 리전 3곳 지정 | | https://cloud.google.com/dns/docs/routing-policies-overview · "originate from three Google Cloud source regions that you specify" · 2026-10-01 |
| NW.cost_floor | — | 관리 영역 $0.000273973/시간(≈$0.20/월, 25개까지), 이후 ≈$0.10. 일반 쿼리 $0.40/백만, 라우팅 정책 쿼리 $0.70/백만(10억까지). 외부 fast 헬스 체크 $0.002739726/시간(≈$2/월), premium $0.005479452/시간(≈$4/월), 내부 fast $0.50/월, premium $2.00/월 | 시간 단위 계측, 영역 1시간 미만도 1시간 과금 | https://cloud.google.com/dns/pricing · "Managed zones 0 month to 25 month $0.000273973 / 1 hour" / "Regular queries ... $0.40 / 1,000,000 count" / "Routing policy queries ... $0.70 / 1,000,000 count" / "External fast health checks ... $0.002739726 / 1 hour" / "Internal fast health checks ... $0.50 / 1 month" · 2026-10-01 |

### 비용 구조
- 고정: 영역 ≈ $0.20/월(가격표 예시 "5 * $0.20 = $1.00"), 외부 헬스 체크 ≈ $2(fast)/$4(premium) 월 — Route 53 AWS 엔드포인트 무료 50개와 달리 첫 개부터 과금.
- 변동: 쿼리. 라우팅 정책 레코드 쿼리는 $0.70/백만으로 일반($0.40)보다 비쌈.

### 교체 계열 정보
- Route 53 대비: 별칭 무료 쿼리 개념 없음, ALIAS 타입 지원. 지연 기반 정책 없음(WRR·GEO·FAILOVER만).
- 외부 엔드포인트 헬스 체크가 공개 영역에서 가능해짐 → GCP 외부 ALB 간 리전 장애 조치를 DNS로 구성 가능.

### 함정
- fail-open(전부 비정상 → 전부 정상 간주).
- 헬스 체크 대상·미대상 IP 혼합 시 미대상 IP만 반환, 지역 장애 조치 안 됨.
- 헬스 체크를 쓰려면 내부 LB는 IP가 아니라 포워딩 규칙 이름을 넣어야 함(`--enable-health-checking` 시) — IP만 넣으면 헬스 체크 안 됨.
- geofence 켜면 지역 전체 장애 시에도 넘어가지 않음.
- DNSSEC 영역에서는 `rrdatas`와 `health_checked_targets` 중 하나만 지정 가능(Terraform 문서).
- 기본 TTL에 기대지 말 것. Terraform에서 `ttl` 명시.

### 생성 산출물
- Terraform 리소스: `google_dns_managed_zone` (https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/dns_managed_zone), `google_dns_record_set` (https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/dns_record_set) (원문: github.com/hashicorp/terraform-provider-google `website/docs/r/*.html.markdown`, 프로바이더 최신 8.5.0)
- 요구에 따라 반드시 명시할 속성:
  - `google_dns_managed_zone.dnssec_config { state = "on" }` → F5 규제·공공. `visibility = "private"` + `private_visibility_config` → 내부 전용 이름.
  - `google_dns_record_set.ttl` → F1 짧음이면 30~60, 나머지 300 이상(명시 필수).
  - `routing_policy { wrr { weight, rrdatas | health_checked_targets } }` → F4 카나리.
  - `routing_policy { geo { location, health_checked_targets }, enable_geo_fencing = false }` → D5 여러 지역, F2 장애 대비면 geofence 끔.
  - `routing_policy { primary_backup { primary { internal_load_balancers | external_endpoints }, backup_geo { ... }, trickle_ratio } , health_check }` → F1 짧음·F2 있음. 외부 엔드포인트면 `health_check`(헬스 체크 리소스) 지정, 공개 영역이어야 함.
- Checkov: `CKV_GCP_16` "Ensure that DNSSEC is enabled for Cloud DNS", `CKV_GCP_17` "Ensure that RSASHA1 is not used for the zone-signing and key-signing keys in Cloud DNS DNSSEC" (google_dns_managed_zone). google_dns_record_set 대상 체크는 해당 체크 없음.
- 배포 후 검증:
  - `gcloud dns record-sets list --zone=<zone> --name=app.example.com.` → 정책·TTL 확인.
  - `dig +noall +answer app.example.com @ns-cloud-<x>1.googledomains.com` → 기대 IP와 TTL.
  - `dig +short NS example.com` → `ns-cloud-*.googledomains.com` 4개.
  - 장애 조치 리허설: primary 백엔드 중지 후 `dig +short app.example.com @<cloud dns ns>` → backup IP.

## 2.3 Cloudflare DNS — 무료 권한 DNS(+ 선택: Load Balancing 애드온)
- 계열: 네트워크-DNS
- 서울 리전: 글로벌(애니캐스트 네임서버, 전 플랜 제공. 서울 PoP 여부는 미확인)

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L7 | DNS-only 레코드: 권한 DNS(경로 밖). Proxied 레코드: DNS가 Cloudflare 애니캐스트 IP를 반환하고 HTTP(S)가 Cloudflare 프록시를 통과(L7 종단은 CDN 절 소관) | A/AAAA/CNAME만 프록시 가능 | https://developers.cloudflare.com/dns/proxy-status/ · "Only records used for IP address resolution — A, AAAA, and CNAME records — can be proxied." · 2026-10-01 |
| NW.idle_timeout | — | 해당 없음 (프록시 시 연결 한도는 CDN 절) | | — |
| NW.request_timeout | L7 | 해당 없음(DNS). 프록시 시 Proxy Read Timeout 초과하면 524 — 값은 CDN 절 | | https://developers.cloudflare.com/dns/proxy-status/ · "If your origin does not send an HTTP response within the defined time limit, Cloudflare returns a 524 error." · 2026-10-01 |
| NW.websocket | — | 해당 없음 | | — |
| NW.protocols | — | 해당 없음 (프록시+HTTP/2·3+Universal SSL이면 HTTPS 레코드 자동 생성) | | https://developers.cloudflare.com/dns/proxy-status/ · "Cloudflare automatically generates HTTPS Service (HTTPS) records on the fly" · 2026-10-01 |
| NW.body_size | — | 해당 없음 | | — |
| NW.draining | — | 해당 없음 | | — |
| NW.health_check | L7 | DNS 자체에는 헬스 체크 없음. **Load Balancing 애드온** 모니터: HTTP/HTTPS/TCP/ICMP/UDP-ICMP/SMTP. 최소 주기 Pro 60초·Business 15초·Enterprise 10초(제한 페이지는 비엔터프라이즈 15초). 타임아웃 시 재시도 즉시, `consecutive_up/down`. 모든 풀이 비정상이면 **fallback pool**로 보냄 | API 예시 기본 interval 90, timeout 3, retries 0 | https://developers.cloudflare.com/load-balancing/monitors/create-monitor/ · "Minimum time in seconds is 60 (Pro), 15 (Business), and 10 (Enterprise)." / "When a health check times out, Cloudflare sends retries immediately" · 2026-10-01; https://developers.cloudflare.com/load-balancing/reference/limitations/ · "Monitor intervals | 15s (min), 3600s (max) | 10s (min), 3600s (max)" · 2026-10-01 [충돌: Pro 최소 주기 60초 vs 비엔터프라이즈 15초]; https://developers.cloudflare.com/load-balancing/understand-basics/health-details/ · "Critical: All pools are unhealthy and traffic is going to the Fallback Pool." · 2026-10-01 |
| NW.tls | — | 해당 없음 (프록시 시 엣지 인증서는 CDN 절) | | — |
| NW.client_ip | — | 해당 없음 (프록시 시 원본에 보이는 IP는 Cloudflare — CDN 절) | | — |
| NW.routing | L7 | DNS: 라운드 로빈(같은 이름 다중 레코드)만. Load Balancing: 트래픽 스티어링·엔드포인트 스티어링, 프록시(L7) 또는 DNS-only 모드 | | https://developers.cloudflare.com/load-balancing/understand-basics/proxy-modes/ · "DNS-only load balancers route traffic by returning specific IP addresses in response to a client's DNS query." · 2026-10-01 |
| NW.scaling | — | 관리형 (추론). LB 한도: 비엔터프라이즈 LB 20, 풀 20, 엔드포인트 20 | | https://developers.cloudflare.com/load-balancing/reference/limitations/ · "Load balancers | 20 | custom" · 2026-10-01 ⚠️근거없음 |
| NW.availability | L7 | 글로벌 애니캐스트. SLA 값 미확인. 프록시 LB는 DNS 캐시 영향 없이 더 빠른 장애 조치 | | https://developers.cloudflare.com/load-balancing/understand-basics/proxy-modes/ · "Offers faster failover and more accurate routing, which can otherwise be affected by DNS caching." · 2026-10-01 |
| NW.caching | — | 해당 없음 (HTTP 캐시는 CDN 절) | | — |
| NW.security | L7 | 프록시 시 원본 IP 숨김. DNS-only는 원본 IP 노출. DNSSEC 무료(등록 기관 원클릭) | | https://developers.cloudflare.com/dns/proxy-status/ · "This exposes your origin IP address to anyone who queries the record" · 2026-10-01; https://developers.cloudflare.com/registrar/ · "DNSSEC secures DNS records with cryptographic signatures, and is free to all Cloudflare customers." · 2026-10-01 |
| NW.dns | L7 | **프록시 레코드 TTL = Auto(300초), 변경 불가**. DNS-only: 60초(비엔터프라이즈)/30초(엔터프라이즈) ~ 1일, Auto=300초. Terraform `ttl = 1`이 automatic. **CNAME flattening**: apex CNAME 허용, 최종 IP 반환. 프록시 CNAME은 기본 flatten. 대상에 A/AAAA 없으면 NODATA. 다른 Cloudflare 계정으로 CNAME 시 1014. DNS-only LB의 TTL은 LB `ttl` 필드(회색 구름만 적용) | 프록시 시 장애 조치는 DNS TTL이 아니라 Cloudflare 엣지에서 일어남 (추론) | https://developers.cloudflare.com/dns/manage-dns-records/reference/ttl/ · "proxied records have a TTL of Auto , which is set to 300 seconds. This value cannot be edited." / "For DNS only records, you can choose a TTL between 30 seconds (Enterprise) or 60 seconds (non-Enterprise) and 1 day" · 2026-10-01; https://developers.cloudflare.com/dns/cname-flattening/ · "Cloudflare then returns the final IP address instead of a CNAME record" / "If the final CNAME target has no A/AAAA records (a dangling CNAME), CNAME flattening returns an empty response (NODATA)" · 2026-10-01; https://developers.cloudflare.com/api/resources/load_balancers/methods/create/ · "This only applies to gray-clouded (unproxied) load balancers." · 2026-10-01 ⚠️근거없음 |
| NW.egress | — | 해당 없음 | | — |
| NW.private_connectivity | — | 해당 없음 (Internal DNS·Private origins 별도 제품, 범위 밖) | | — |
| NW.regions | — | 글로벌, 전 플랜 | | https://developers.cloudflare.com/dns/ · "Available on all plans" · 2026-10-01 |
| NW.cost_floor | — | DNS 무료(전 플랜). Load Balancing 애드온 "Starting at $5/mo" | LB 세부 요금(엔드포인트·쿼리 추가)은 공식 문서에서 미확인 | https://developers.cloudflare.com/dns/ · "Available on all plans" · 2026-10-01; https://www.cloudflare.com/plans/ · "Load Balancing Local and global traffic load balancing, geographic routing, health checks, and failover for continuous availability. Starting at $5/mo" · 2026-10-01 |

### 비용 구조
- DNS: 0원(Free 플랜 포함). 헬스 체크 기반 장애 조치가 필요하면 Load Balancing 애드온(≥$5/월). 엔드포인트 수·쿼리 과금 세부는 미확인.

### 교체 계열 정보
- Route 53/Cloud DNS와 달리 무료 DNS만으로는 헬스 체크·장애 조치 없음.
- 프록시를 켜면 DNS가 CDN/WAF 진입점이 됨 → 다른 네트워크 계열(CDN·WAF) 판정과 묶임.
- apex 대상이 AWS ALB/CloudFront 같은 호스트명이면 CNAME flattening으로 대체.

### 함정
- 프록시 레코드 TTL 300초 고정. DNS-only로 바꿔야 TTL 조정 가능하지만 원본 IP 노출.
- DNS-only 레코드로 웹 서비스하면 원본 IP 공개 → 원본 보안 그룹을 Cloudflare IP로 제한하는 설계가 무력화 (추론). ⚠️근거없음
- CNAME flattening "모든 CNAME" 켜면 제3자 도메인 검증용 CNAME(ACM 검증 CNAME 포함 가능성)이 CNAME으로 응답되지 않아 검증 실패 → **ACM DNS 검증 CNAME은 DNS-only로, flatten-all 끔** (추론, 문서는 "verification to fail" 언급). ⚠️근거없음
- 대상 A/AAAA 없는 CNAME은 NODATA.
- Pro 플랜 LB 모니터 최소 60초 → F1 거의 0이면 Business 이상 필요.

### 생성 산출물
- Terraform 리소스: v5 이름은 `cloudflare_dns_record` (https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/dns_record, 원문 github.com/cloudflare/terraform-provider-cloudflare `docs/resources/dns_record.md`, 프로바이더 최신 5.26.0). v4의 `cloudflare_record`는 v5 문서에 없음. LB 필요 시 `cloudflare_load_balancer`, `cloudflare_load_balancer_pool`, `cloudflare_load_balancer_monitor` (이름은 (추론), 미확인). ⚠️근거없음
- 요구에 따라 반드시 명시할 속성:
  - `zone_id`, `name`, `type`, `content`, `ttl`(필수, 1=automatic, 60~86400, 엔터프라이즈 30) → 프록시면 `ttl = 1`.
  - `proxied = true` → 웹 트래픽(원본 IP 은닉·WAF·CDN 필요, F5·보안 요구). `proxied = false` → MX·검증 TXT/CNAME(ACM `_xxx.` CNAME 포함)·비HTTP 서비스.
- Checkov: Cloudflare 리소스 대상 해당 체크 없음 (Policy Index에서 cloudflare 검색 결과 없음).
- 배포 후 검증:
  - `dig +noall +answer app.example.com` → 프록시면 Cloudflare 애니캐스트 IP, TTL 300 이하.
  - `curl -sI https://app.example.com | grep -i -E "server|cf-ray"` → `server: cloudflare`, `cf-ray` 존재(프록시 확인).
  - `dig +short NS example.com` → `*.ns.cloudflare.com`.
  - `dig +short example.com A` (apex CNAME) → IP 반환(flatten), 빈 응답이면 대상 확인.

## 2.4 도메인 등록 기관 기본 DNS — (요약) Route 53 Domains / Cloudflare Registrar / Squarespace Domains
- 계열: 네트워크-DNS
- 서울 리전: 글로벌(근거 없음, (추론)) ⚠️근거없음

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L7 | 권한 DNS(경로 밖) | | (추론) ⚠️근거없음 |
| NW.idle_timeout / NW.request_timeout / NW.websocket / NW.protocols / NW.body_size / NW.draining / NW.tls / NW.client_ip / NW.caching / NW.egress / NW.private_connectivity / NW.scaling | — | 해당 없음 | | — |
| NW.health_check | — | Route 53 Domains·Cloudflare Registrar는 각자 DNS(2.1·2.3)로 귀결. Squarespace 기본 DNS: 헬스 체크 기능 없음 (추론, 문서에 언급 없음) | | 미확인 ⚠️근거없음 |
| NW.routing | — | Squarespace: 단순 레코드만 (추론) | | 미확인 ⚠️근거없음 |
| NW.availability | — | 미확인 | | 미확인 |
| NW.security | L7 | Cloudflare Registrar: 원클릭 DNSSEC, WHOIS 비공개 기본. Squarespace: DS 레코드 편집 지원 | | https://developers.cloudflare.com/registrar/ · "Cloudflare Registrar offers one-click DNSSEC activation." · 2026-10-01 |
| NW.dns | L7 | **Route 53 Domains**: 등록 시 호스팅 영역 자동 생성·과금(2.1 그대로). **Cloudflare Registrar**: Cloudflare 네임서버 강제(타사 NS 불가) → 2.3 그대로. **Squarespace Domains**: 사용자 레코드 기본 TTL 4시간, 사용자 지정 가능, ALIAS 레코드 지원 | Squarespace 기본 TTL 4시간은 장애 조치·이전 시 4시간 캐시 | https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/domain-register.html · "When you register a domain with Route 53, Route 53 automatically creates a hosted zone for the domain and charges a small monthly fee" · 2026-10-01; https://developers.cloudflare.com/registrar/faq/ · "No, all domains on Cloudflare Registrar use Cloudflare nameservers" · 2026-10-01; https://support.squarespace.com/hc/en-us/articles/360002101888-Edit-your-domain-s-DNS-records · "All custom records have a 4-hour TTL by default" / "These include A, AAAA, ALIAS, CNAME" · 2026-10-01 ⚠️출처확인필요 |
| NW.regions | — | 미확인 | | 미확인 |
| NW.cost_floor | — | Cloudflare Registrar: 레지스트리 원가, 마크업 없음(DNS 무료). Route 53 Domains: 도메인 연 요금 + 영역 $0.50/월 | 도메인 요금 자체는 이 표 범위 밖 | https://developers.cloudflare.com/registrar/ · "will only charge you what is paid to the registry for your domain. No markup." · 2026-10-01 |

### 비용 구조
- 등록 기관 DNS는 보통 도메인 요금에 포함(Squarespace 요금 구조는 미확인). Route 53 Domains는 영역 비용 별도.

### 교체 계열 정보
- 헬스 체크·장애 조치·별칭 무료 쿼리가 필요하면 NS를 Route 53/Cloud DNS/Cloudflare로 위임. Cloudflare Registrar는 NS 변경 불가(Cloudflare DNS 고정)이므로 Route 53 장애 조치를 쓰려면 하위 도메인 위임 또는 등록 기관 이전.
- 가비아·후이즈 등 국내 등록 기관 DNS는 공식 문서로 확인하지 않음(일반화 금지).

### 함정
- 등록 기관 기본 TTL이 길면(예: Squarespace 4시간) 클라우드 이전 직후 수 시간 옛 IP로 감.
- 등록 기관 DNS에는 헬스 체크 기반 장애 조치·별칭이 없음 (추론) → F1 짧음이면 부적합 판정. ⚠️근거없음
- apex를 ALB/CloudFront 호스트명으로 향하게 하려면 ALIAS/flatten 지원 필요(Squarespace는 ALIAS 지원, 다른 등록 기관 미확인).

### 생성 산출물
- Terraform 리소스: 등록 기관 DNS는 대상 아님. 위임용 `aws_route53_zone` 후 NS 값을 등록 기관에 수동 입력, 또는 `aws_route53domains_registered_domain`(Route 53 Domains일 때, 이름은 Checkov 인덱스에서 확인).
- 요구에 따라 반드시 명시할 속성: `aws_route53domains_registered_domain.name_server` → 위임 대상 영역 NS (인자 이름 (추론), 미확인). ⚠️근거없음
- Checkov: `CKV_AWS_377` "Ensure Route 53 domains have transfer lock protection"(aws_route53domains_registered_domain). 그 외 해당 체크 없음.
- 배포 후 검증: `dig +trace app.example.com` → TLD에서 위임된 NS가 의도한 DNS 공급자인지. `whois example.com | grep -i "name server"`.

---

# 3. WAF·DDoS

## 3.1 AWS WAF — WAFv2 web ACL(콘솔 새 이름 "protection pack")
- 계열: 네트워크-WAF·DDoS
- 서울 리전: 있음 (Price List `awswaf/current/ap-northeast-2` 오퍼 존재, usagetype `APN2-*`). CloudFront용 web ACL은 us-east-1(Global)에 만들어야 함.

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L7 | 연결 대상 리소스(호스트 서비스)에 붙는 L7 요청 검사기. 자체 프록시·엔드포인트 없음 | 연결 대상: CloudFront 배포, API Gateway REST API, ALB, AppSync GraphQL, Cognito user pool, App Runner, Bedrock AgentCore Gateway, Verified Access, Amplify. 리소스 1개당 web ACL 1개. CloudFront용 web ACL은 다른 리소스 유형에 못 붙임 | https://docs.aws.amazon.com/waf/latest/developerguide/how-aws-waf-works-resources.html · "Amazon API Gateway REST API Application Load Balancer AWS AppSync GraphQL API Amazon Cognito user pool AWS App Runner service ... AWS Verified Access instance AWS Amplify" / "You can associate each AWS resource with only one protection pack (web ACL)" · 2026-10-01 |
| NW.idle_timeout | — | 해당 없음 | 연결 타임아웃은 호스트 서비스(ALB·CloudFront) 값 | — |
| NW.request_timeout | — | 해당 없음 | 호스트 서비스 값 | — |
| NW.websocket | — | 미확인 | WAF 문서에서 WebSocket 프레임 검사 언급 확인 못 함 | — |
| NW.protocols | L7 | gRPC 요청에는 본문 검사 규칙 미적용(그 외 규칙은 적용). ALB HTTP/2 대상: "Inspect immediately"(기본)/"Inspect after sufficient data" | ALB 대상 그룹 속성으로 설정 | https://docs.aws.amazon.com/waf/latest/developerguide/web-acl-setting-body-inspection-limit.html · "AWS WAF does not support request body inspection rules for gRPC traffic" / "Inspect immediately (default)" · 2026-10-01 |
| NW.body_size | L7 | 본문 검사 한도: ALB·AppSync **8 KB 고정**. CloudFront·API GW·Cognito·App Runner·Verified Access **기본 16 KB, 16 KB 단위로 최대 64 KB**. 헤더 8 KB·200개, 쿠키 8 KB·200개. 한도 초과분은 검사 없이 통과(초과 처리 기본 Continue) | 한도는 "검사" 한도이지 차단 한도 아님. 16 KB 초과 검사 시 추가 요금 | https://docs.aws.amazon.com/waf/latest/developerguide/web-acl-setting-body-inspection-limit.html · "For Application Load Balancer and AWS AppSync, the limit is fixed at 8 KB (8,192 bytes). For CloudFront, API Gateway, ... the default limit is 16 KB (16,384 bytes), and you can increase the limit ... up to 64 KB" ; https://docs.aws.amazon.com/waf/latest/developerguide/waf-oversize-request-components.html · "Outside the console, the default option is Continue." / "AWS WAF can inspect at most the first 8 KB (8,192 bytes) of the request headers and at most the first 200 headers" · 2026-10-01 |
| NW.draining | — | 해당 없음 | — | — |
| NW.health_check | — | 해당 없음 | — | — |
| NW.tls | — | 해당 없음(TLS 종단은 호스트 서비스). JA3/JA4 지문은 규칙 조건으로 사용 가능 | Terraform `ja3_fingerprint`/`ja4_fingerprint` 블록 존재 | https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/wafv2_web_acl (원문 GitHub `website/docs/r/wafv2_web_acl.html.markdown`) · "The match status to assign to the web request if the request doesn't have a JA3 fingerprint" · 2026-10-01 |
| NW.client_ip | L3/L7 | **WAF가 보는 IP 기본값 = 요청 출발지(마지막 프록시) IP.** CloudFront 뒤 ALB에 붙은 WAF는 CloudFront 엣지 IP를 봄. `forwarded_ip_config`(header_name 예 `X-Forwarded-For`, fallback MATCH/NO_MATCH)를 **규칙마다** 지정해야 클라이언트 IP 사용. 레이트·geo·ASN 규칙은 헤더의 **첫 번째** 주소 사용(클라이언트가 위조 가능). 헤더 없으면 규칙 미적용. Bot Control·Anti-DDoS AMR만 CloudFront·Cloudflare·Fastly 대역을 자동 인식. **앱으로 전달 헤더**: ALB가 `X-Forwarded-For` 추가(기본 `append`), CloudFront는 `CloudFront-Viewer-Address`(IP:포트) 옵션 헤더. WAF 커스텀 요청 헤더는 `x-amzn-waf-` 접두어로 삽입 | 레이트 규칙의 scope-down 문은 forwarded IP 설정을 상속하지 않음 | https://docs.aws.amazon.com/waf/latest/developerguide/waf-rule-statement-forwarded-ip-address.html · "By default, AWS WAF uses the IP address from the web request origin." / "For geo match, ASN match, and rate-based rules, AWS WAF uses the first address in the header." / "If the header that you specify isn't present in a request, AWS WAF doesn't apply the rule to the request at all." ; https://docs.aws.amazon.com/elasticloadbalancing/latest/application/x-forwarded-headers.html · "The possible values for this attribute are append , preserve , and remove . The default value for this attribute is append ." ; https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/adding-cloudfront-headers.html · "CloudFront-Viewer-Address – Contains the IP address of the viewer and the source port of the request." ; Terraform 원문 · "it prefixes this name `x-amzn-waf-`" · 2026-10-01 |
| NW.routing | — | 해당 없음(Allow/Block/Count/CAPTCHA/Challenge 액션, 커스텀 응답만) | Block 기본 응답 403 | https://docs.aws.amazon.com/waf/latest/developerguide/web-acl-default-action.html · "By default, for the Block action, the AWS resource responds with an HTTP 403 (Forbidden) status code" · 2026-10-01 |
| NW.scaling | L7 | 리전 web ACL당 초당 100,000 요청(기본 쿼터, 증설 가능). CloudFront는 CloudFront 한도 따름. web ACL 최대 5,000 WCU(고정), 기본 가격 1,500 WCU 포함. 레이트 규칙 web ACL당 10개, 규칙당 레이트 제한 고유 IP 10,000개 | 계정·리전당 web ACL 100개 | https://docs.aws.amazon.com/waf/latest/developerguide/limits.html · "Maximum number of requests per second per protection pack (web ACL) 100,000" / "Maximum number of rate-based rules per protection pack (web ACL) 10" / "Maximum number of unique IP addresses that can be rate limited per rate-based rule 10,000" ; https://docs.aws.amazon.com/waf/latest/developerguide/aws-waf-capacity-units.html · "The basic price for a protection pack (web ACL) includes up to 1,500 WCUs." / "The maximum capacity for a protection pack (web ACL) is 5,000 WCUs." · 2026-10-01 |
| NW.availability | — | 리전 서비스(리전 리소스는 같은 리전 web ACL), CloudFront용은 us-east-1에서 생성해 글로벌 적용. SLA 미확인 | — | https://docs.aws.amazon.com/waf/latest/developerguide/how-aws-waf-works-resources.html · "you must use the Region US East (N. Virginia) to create your protection pack (web ACL)" · 2026-10-01 |
| NW.caching | — | 해당 없음 | — | — |
| NW.security | L7 | **기본 동작(default_action)은 생성 시 필수 지정(API·Terraform에 기본값 없음), Allow 또는 Block.** **관리형 규칙 그룹은 API·Terraform으로 만들면 아무것도 들어가지 않음**(콘솔 새 경험의 "Recommended" 선택 시에만 자동 구성). AWSManagedRulesCommonRuleSet 700 WCU, KnownBadInputs 200 WCU. **레이트 기반 규칙**: 평가 창 60/120/300/600초(기본 300), 최소 한도 10, 집계 키 기본 IP(그 외 FORWARDED_IP, ASN, CONSTANT(=Count all, scope-down 필수), CUSTOM_KEYS: 헤더·쿠키·쿼리 인자·쿼리 문자열·라벨 네임스페이스 등), **근사 집계**(최근 요청 가중, 감지 지연 수 분 가능·보통 30초 이내), 설정 변경 시 카운터 리셋(최대 1분 중단), 액션은 Allow 불가 | 집계 키의 요청 구성 요소가 없으면 카운트·제한 안 함 | https://docs.aws.amazon.com/waf/latest/developerguide/web-acl-default-action.html · "When you create and configure a protection pack (web ACL), you must set the protection pack (web ACL) default action." ; https://docs.aws.amazon.com/waf/latest/developerguide/setup-iap-console.html · "AWS WAF generates Recommended for you based on your selections" ; https://docs.aws.amazon.com/waf/latest/developerguide/waf-rule-statement-type-rate-based-high-level-settings.html · "Valid settings are 60 (1 minute), 120 (2 minutes), 300 (5 minutes), and 600 (10 minutes), and 300 (5 minutes) is the default." / "The lowest limit setting allowed is 10." / "You can use any rule action except Allow." ; https://docs.aws.amazon.com/waf/latest/developerguide/waf-rule-statement-type-rate-based-aggregation-options.html · "By default, a rate-based rule aggregates and rate limits requests based on the request IP address." / "All of the request components that you specify in the aggregation key must be present" ; https://docs.aws.amazon.com/waf/latest/developerguide/waf-rule-statement-type-rate-based-caveats.html · "It's not intended for precise request-rate limiting." / "Usually, this delay is below 30 seconds." / "This can pause the rule's rate limiting activities for up to a minute." ; https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-baseline.html · "AWSManagedRulesCommonRuleSet , WCU: 700" · 2026-10-01 |
| NW.dns | — | 해당 없음 | — | — |
| NW.egress | — | 해당 없음 | — | — |
| NW.private_connectivity | — | 해당 없음(내부 ALB에도 연결 가능 여부 문서 확인 못 함 → 미확인) | — | — |
| NW.regions | — | 서울 포함 리전별 + CloudFront(Global=us-east-1) | — | [PL] https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/awswaf/current/ap-northeast-2/index.csv · usagetype `APN2-WebACLV2` "$5.00 per web ACL created (prorated hourly)" · 2026-10-01 |
| NW.cost_floor | — | [PL 서울] web ACL **월 $5**(`APN2-WebACLV2`), 규칙(관리형 규칙 그룹 1개도 1규칙) **월 $1**(`APN2-RuleV2`), 요청 **100만당 $0.60**(`APN2-RequestV2-Tier1`). 시간 단위 비례 | 최소 = web ACL 1 + 규칙 1 ≈ 월 $6 + 요청 | [PL] https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/awswaf/current/ap-northeast-2/index.csv · "$1.00 per rule created (prorated hourly)" / "$0.60 per million requests processed" (APN2-RequestV2-Tier1) ; https://aws.amazon.com/waf/pricing/ · "$1.00 per month (prorated hourly) for each rule group or each managed rule group that you add to your web ACL" · 2026-10-01 |

### 비용 구조
- [PL 서울, 2026-09-14판] web ACL $5/월(`APN2-WebACLV2`), 규칙·규칙 그룹·관리형 규칙 그룹 각 $1/월(`APN2-RuleV2`), 요청 $0.60/100만(`APN2-RequestV2-Tier1`).
- WCU 1,500 초과: 500 WCU마다 100만 요청당 +$0.20. 기본 본문 한도(16 KB) 초과 검사: 추가 16 KB마다 100만 요청당 +$0.30 (PL `APN2-RequestV2-32KB` $0.30, `-48KB` $0.60, `-64KB` $0.90). 출처 https://aws.amazon.com/waf/pricing/ · "You will be charged an additional $0.20 per million requests for each 500 WCUs the Web ACL uses beyond the default allocation of 1500. In addition, you will be charged $0.30 per million requests for each additional 16KB analyzed beyond the default body inspection limit."
- Bot Control: 규칙 그룹 $10/월(`APN2-AMR-BotControl`), Common 첫 1,000만 요청 무료 후 $1/100만, Targeted 첫 100만 무료 후 $10/100만. Fraud Control(ATP·ACFP) $10/월 + 1,000 요청당 $1(Tier1)~$0.05(Tier5). Anti-DDoS AMR $20/월(`APN2-AMR-AntiDDoS`) + $0.15/100만. CAPTCHA 시도 1,000건당 $0.40, Challenge 응답 100만당 $0.40. [PL 서울]
- 로그: CloudWatch Logs·S3·Firehose 요금 별도(대상 서비스 요금).
- ALB 리소스 수준 DDoS 보호: 설정 없는 web ACL을 ALB에 붙이면 WAF 요청 요금 없음(대신 메트릭·샘플 없음). https://docs.aws.amazon.com/waf/latest/developerguide/waf-anti-ddos.html · "If your Application Load Balancer is associated with a web ACL that has no configuration, you will not incur charges from AWS WAF requests"

### 교체 계열 정보
- 같은 계열: Google Cloud Armor(3.4·3.5), Cloudflare WAF(3.6), Vercel Firewall(3.7). 앞단 CDN을 Cloudflare로 두면 AWS WAF는 Cloudflare IP를 보게 되므로 forwarded IP(`CF-Connecting-IP`) 설정이 필요(추론). ⚠️근거없음
- Shield Advanced 구독 시 보호 리소스의 WAF 기본 요금(web ACL·규칙·기본 요청, 1,500 WCU·기본 본문 한도까지)이 포함(3.3).

### 함정
- **기본 규칙이 없다**: Terraform·API로 만든 web ACL은 `default_action { allow {} }` + 규칙 0개면 아무것도 막지 않음. 관리형 규칙 그룹(CommonRuleSet 등)은 명시적으로 `managed_rule_group_statement`를 넣어야 함.
- **CommonRuleSet `SizeRestrictions_BODY`는 8 KB 초과 본문을 Block**: 파일 업로드·큰 JSON(A7)을 받는 앱은 이 규칙을 `rule_action_override`로 Count 처리하지 않으면 업로드가 403. 출처 https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-baseline.html · "SizeRestrictions_BODY Inspects for request bodies that are over 8 KB (8,192 bytes). Rule action: Block"
- **CommonRuleSet `NoUserAgent_HEADER`는 User-Agent 없는 요청 Block**: 서버 간 호출·웹훅·헬스 체크 클라이언트가 UA를 안 보내면 차단. 같은 페이지 · "NoUserAgent_HEADER Inspects for requests that are missing the HTTP User-Agent header. Rule action: Block". 쿼리 2,048 B·URI 1,024 B·쿠키 10,240 B 초과도 Block.
- **본문 검사 한도 밖은 검사 없이 통과**: ALB는 8 KB만 검사하므로 그 뒤의 페이로드는 SQLi/XSS 규칙을 우회. 초과 처리(oversize_handling) 기본 Continue.
- **CloudFront 뒤 ALB의 WAF 레이트 규칙**은 forwarded IP 없이 쓰면 CloudFront 엣지 IP 단위로 집계 → 다수 사용자가 한 키로 묶여 정상 사용자 차단, 또는 반대로 공격자 분산. forwarded IP를 쓰면 XFF **첫 번째** 값(클라이언트 위조 가능) 사용 → 우회 가능. CloudFront 앞단이면 CloudFront 배포에 web ACL을 붙이는 쪽이 원천 IP를 봄(추론). ⚠️근거없음
- **레이트 규칙은 근사**: 정확한 쿼터(예: API 과금 한도)용이 아님. 최소 한도 10/창, 감지·해제 지연 수십 초~수 분.
- CloudFront에는 `aws_wafv2_web_acl_association`을 쓰지 말고 `aws_cloudfront_distribution.web_acl_id`(ARN) 사용, web ACL은 us-east-1 provider + `scope = "CLOUDFRONT"`.
- 로그 대상 이름은 반드시 `aws-waf-logs-` 접두어(CloudWatch 로그 그룹·S3 버킷·Firehose). https://docs.aws.amazon.com/waf/latest/developerguide/logging-cw-logs.html · "Your log group names must start with aws-waf-logs-"
- Terraform 문서 `request_body` 블록 설명의 "Applicable only when scope is ..." 문구가 api_gateway(CLOUDFRONT)·cloudfront(REGIONAL)로 서로 뒤바뀐 것으로 보임(추론, 문서 오기 가능성). ALB는 8 KB 고정이라 `request_body`로 못 늘림. ⚠️근거없음
- API Gateway는 REST만 연결 가능(HTTP API 불가). Terraform 원문 · "an Amazon API Gateway stage (REST only, HTTP is unsupported)"

### 생성 산출물
- Terraform 리소스:
  - `aws_wafv2_web_acl` (https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/wafv2_web_acl)
  - `aws_wafv2_web_acl_association` (https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/wafv2_web_acl_association) — ALB·API GW REST stage·Cognito·AppSync·App Runner·Amplify·AgentCore·Verified Access용
  - `aws_wafv2_web_acl_logging_configuration` (https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/wafv2_web_acl_logging_configuration)
  - CloudFront: `aws_cloudfront_distribution.web_acl_id`
- 요구에 따라 반드시 명시할 속성:
  - `scope` = `REGIONAL`(ALB 등) / `CLOUDFRONT`(us-east-1 provider 필수).
  - `default_action { allow {} }` (일반 공개 앱) / `block {}` (허용 목록 기반 관리 화면, F1 사내 전용).
  - `rule { override_action { none {} } statement { managed_rule_group_statement { vendor_name = "AWS", name = "AWSManagedRulesCommonRuleSet" ... } } }` + `AWSManagedRulesKnownBadInputsRuleSet`(Log4j). A7(본문 > 8 KB 업로드)이면 `rule_action_override { name = "SizeRestrictions_BODY" action_to_use { count {} } }`. 서버 간 API(UA 없음)면 `NoUserAgent_HEADER` count.
  - 레이트 규칙: `rate_based_statement { limit = N(≥10), evaluation_window_sec = 60|120|300|600, aggregate_key_type = "IP"|"FORWARDED_IP"|"CUSTOM_KEYS"|"CONSTANT" }`. 앞단에 CDN·프록시가 있으면(경로 요구) `aggregate_key_type = "FORWARDED_IP"` + `forwarded_ip_config { header_name = "X-Forwarded-For", fallback_behavior = "MATCH" }`. 로그인 brute force 요구(보안)면 `scope_down_statement`로 `/login` 경로 한정. 행동 `action { block {} }`. Shield Advanced 비용 보호(3.3)를 받으려면 CloudFront·ALB web ACL에 Block 모드 레이트 규칙 필수.
  - 모든 규칙과 web ACL에 `visibility_config { cloudwatch_metrics_enabled = true, metric_name, sampled_requests_enabled = true }` (필수 블록).
  - 본문 큰 API(A7)이고 CloudFront·API GW·App Runner·Cognito·Verified Access면 `association_config { request_body { <type> { default_size_inspection_limit = "KB_64" } } }`(요금 증가).
  - 로그: `log_destination_configs = [<aws-waf-logs-... ARN>]`, 개인정보 요구면 `redacted_fields { single_header { name = "authorization" } }`, 비용 절감이면 `logging_filter { default_behavior = "DROP" filter { behavior = "KEEP" requirement = "MEETS_ANY" condition { action_condition { action = "BLOCK" } } } }`.
- Checkov(https://www.checkov.io/5.Policy%20Index/terraform.html 에서 확인): ⚠️출처확인필요
  - CKV_AWS_192 `aws_wafv2_web_acl` — "Ensure WAF prevents message lookup in Log4j2. See CVE-2021-44228 aka log4jshell"
  - CKV2_AWS_31 `aws_wafv2_web_acl` — "Ensure WAF2 has a Logging Configuration"
  - CKV2_AWS_28 `aws_lb`/`aws_alb` — "Ensure public facing ALB are protected by WAF"
  - CKV2_AWS_29 `aws_api_gateway_rest_api`/`aws_api_gateway_stage` — "Ensure public API gateway are protected by WAF"
  - CKV2_AWS_33 `aws_appsync_graphql_api` — "Ensure AppSync is protected by WAF"
  - CKV2_AWS_47 `aws_cloudfront_distribution`/`aws_wafv2_web_acl` — "Ensure AWS CloudFront attached WAFv2 WebACL is configured with AMR for Log4j Vulnerability"
  - CKV2_AWS_76 (ALB), CKV2_AWS_77 (API Gateway), CKV2_AWS_78 (AppSync) — "... attached WAFv2 WebACL is configured with AMR for Log4j Vulnerability"
  - CKV_AWS_68 `aws_cloudfront_distribution` — "CloudFront Distribution should have WAF enabled"
  - CKV_AWS_175 `aws_wafv2_web_acl` — "Ensure WAF has associated rules"
  - CKV_AWS_342 `aws_wafv2_web_acl` — "Ensure WAF rule has any actions"
- 배포 후 검증:
  - `aws wafv2 get-web-acl-for-resource --resource-arn <ALB_ARN> --region ap-northeast-2` → `WebACL.Name` 존재.
  - `aws wafv2 get-logging-configuration --resource-arn <WEBACL_ARN> --region ap-northeast-2` → `LogDestinationConfigs`에 `aws-waf-logs-` ARN.
  - `curl -s -o /dev/null -w '%{http_code}\n' -H 'X-Api-Version: ${jndi:ldap://x.example/a}' https://<host>/` → `403`(KnownBadInputs).
  - `curl -s -o /dev/null -w '%{http_code}\n' -A '' https://<host>/` → CommonRuleSet 사용 시 `403`(NoUserAgent). 앱이 UA 없는 클라이언트를 받아야 하면 200이어야 함(override 확인).
  - `head -c 20000 /dev/urandom | base64 > /tmp/b; curl -s -o /dev/null -w '%{http_code}\n' -X POST --data-binary @/tmp/b https://<host>/upload` → CommonRuleSet 기본이면 403, override했으면 앱 응답.
  - `for i in $(seq 1 300); do curl -s -o /dev/null -w '%{http_code}\n' https://<host>/login; done | sort | uniq -c` → limit 초과 후 30초~수 분 안에 `403` 등장.

## 3.2 AWS Shield Standard — 기본(무료)
- 계열: 네트워크-WAF·DDoS
- 서울 리전: 글로벌(모든 AWS 고객·리전에 자동 적용)

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L3/L4 | 네트워크·전송 계층 DDoS 자동 탐지·완화. 설정 리소스 없음 | Route 53·CloudFront·Global Accelerator에서 특히 넓게 보호 | https://docs.aws.amazon.com/waf/latest/developerguide/ddos-standard-summary.html · "Shield Standard defends against the most common, frequently occurring network and transport layer DDoS attacks" · 2026-10-01 |
| NW.idle_timeout | — | 해당 없음 | — | — |
| NW.request_timeout | — | 해당 없음 | — | — |
| NW.websocket | — | 해당 없음 | — | — |
| NW.protocols | — | 해당 없음 | — | — |
| NW.body_size | — | 해당 없음 | — | — |
| NW.draining | — | 해당 없음 | — | — |
| NW.health_check | — | 해당 없음 | — | — |
| NW.tls | — | 해당 없음 | — | — |
| NW.client_ip | — | 해당 없음(앱에 전달하는 헤더 없음) | — | — |
| NW.routing | — | 해당 없음 | — | — |
| NW.scaling | — | 해당 없음(용량 설정 없음) | — | — |
| NW.availability | L3/L4 | 모든 AWS 고객에 자동 | — | https://docs.aws.amazon.com/waf/latest/developerguide/ddos-standard-summary.html · "All AWS customers benefit from the automatic protection of Shield Standard, at no additional charge." · 2026-10-01 |
| NW.caching | — | 해당 없음 | — | — |
| NW.security | L3/L4 | L3/L4 DDoS만. **L7(HTTP 플러드) 보호 없음** → WAF 레이트 규칙·Anti-DDoS AMR 필요 | CloudFront·Route 53·Global Accelerator는 "all known network and transport layer attacks" 보호 | https://docs.aws.amazon.com/waf/latest/developerguide/ddos-standard-summary.html · "These resources receive comprehensive availability protection against all known network and transport layer attacks." · 2026-10-01 |
| NW.dns | — | 해당 없음 | — | — |
| NW.egress | — | 해당 없음 | — | — |
| NW.private_connectivity | — | 해당 없음 | — | — |
| NW.regions | — | 전 리전 | — | 위 출처 동일 |
| NW.cost_floor | — | $0 | — | https://aws.amazon.com/shield/pricing/ · "Subscription Commitment None 1 Year*" / Standard "No additional cost" · 2026-10-01 |

### 비용 구조
- 무료. 공격으로 늘어난 ALB LCU·CloudFront·데이터 전송 요금 보전(비용 보호)은 없음(Advanced 전용, 3.3).

### 교체 계열 정보
- 상위: Shield Advanced(3.3). L7은 AWS WAF(3.1)로 보완. 타 클라우드 대응: Cloud Armor Standard의 L3/L4 상시 보호(3.4), Cloudflare 무제한 DDoS(3.6).

### 함정
- "Shield가 있으니 DDoS 안전"은 L3/L4 한정. HTTP 요청 폭주는 ALB까지 그대로 도달해 LCU·컴퓨트 비용이 늘 수 있음(추론, Standard에는 비용 보호 없음). ⚠️근거없음

### 생성 산출물
- Terraform 리소스: 해당 없음(자동 적용, 설정 리소스 없음).
- 요구에 따라 반드시 명시할 속성: 해당 없음. L7 보호 요구(보안)가 있으면 3.1의 레이트 규칙을 생성.
- Checkov: 해당 체크 없음.
- 배포 후 검증: `aws shield describe-subscription` → `ResourceNotFoundException`(Advanced 미구독이면 정상, Standard만 적용 중).

## 3.3 AWS Shield Advanced — 구독
- 계열: 네트워크-WAF·DDoS
- 서울 리전: 있음 ([PL] `AWSShield/current/ap-northeast-2` 오퍼에 "Shield Data Transfer Out of ELB in ICN" 존재)

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L3/L4/L7 | L3/L4 강화 탐지·완화 + L7은 AWS WAF web ACL로 수행(자동 L7 완화·Anti-DDoS AMR) | 리소스를 명시적으로 보호 대상으로 추가해야 함(자동 아님) | https://docs.aws.amazon.com/waf/latest/developerguide/ddos-protections-by-resource-type.html · "Shield Advanced protects AWS resources in the network and transport layers (layers 3 and 4) and in the application layer (layer 7)." / "It doesn't automatically protect your resources." · 2026-10-01 |
| NW.idle_timeout | — | 해당 없음 | — | — |
| NW.request_timeout | — | 해당 없음 | — | — |
| NW.websocket | — | 해당 없음 | — | — |
| NW.protocols | L3 | **IPv4만 지원, IPv6 미지원** | — | https://docs.aws.amazon.com/waf/latest/developerguide/ddos-protections-by-resource-type.html · "Shield Advanced supports IPv4, and does not support IPv6." · 2026-10-01 |
| NW.body_size | — | 해당 없음 | — | — |
| NW.draining | — | 해당 없음 | — | — |
| NW.health_check | L7 | Route 53 헬스 체크 연결 시 탐지 개선(호스티드 존 제외). Proactive engagement는 헬스 체크 연결 리소스만 | — | https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html · "Shield Advanced proactive engagement is available only for resources that have health-based detection enabled." · 2026-10-01 |
| NW.tls | — | 해당 없음 | — | — |
| NW.client_ip | L7 | L7 자동 완화는 클라이언트 트래픽 속성 사용 → **CDN 뒤 ALB는 자동 완화 효과 감소**, CloudFront면 배포에 켤 것 권장. 앱 전달 헤더 없음 | — | https://docs.aws.amazon.com/waf/latest/developerguide/ddos-automatic-app-layer-response.html · "For Application Load Balancers that receive any traffic through a content delivery network (CDN), such as Amazon CloudFront, the application-layer automatic mitigation capabilities ... will be reduced." · 2026-10-01 |
| NW.routing | — | 해당 없음 | — | — |
| NW.scaling | — | 리소스 유형별 보호 리소스 계정당 1,000개(증설 가능), 보호 그룹 100개 | — | https://docs.aws.amazon.com/waf/latest/developerguide/shield-limits.html · "Maximum number of protected resources for each resource type ... per account. 1,000" · 2026-10-01 |
| NW.availability | — | 보호 대상: CloudFront, Route 53 호스티드 존, Global Accelerator 표준 가속기, EIP(EC2·NLB 경유), ALB, CLB. **API Gateway·App Runner·Cloud Run류 직접 보호 불가**, GWLB·custom routing GA 불가 | — | https://docs.aws.amazon.com/waf/latest/developerguide/ddos-protections-by-resource-type.html · "You can't use Shield Advanced to protect any other resource type." · 2026-10-01 |
| NW.caching | — | 해당 없음 | — | — |
| NW.security | L3/L4/L7 | SRT(**Business 또는 Enterprise Support 플랜 필요**), 자동 L7 완화(150 WCU 규칙 그룹 추가, 기준선 24시간~30일; 2026-03-26부터 Anti-DDoS AMR이 기본 해법), 비용 보호(서비스 크레딧), Anti-DDoS AMR 포함, Firewall Manager Shield 정책 포함 | 비용 보호 조건: 공격 전에 보호 추가 + CloudFront·ALB에는 web ACL과 **Block 모드 레이트 규칙** 필요, 청구월 다음 15일 내 신청 | https://docs.aws.amazon.com/waf/latest/developerguide/ddos-srt-support.html · "To use the services of the Shield Response Team (SRT), you must be subscribed to the Business Support plan or the Enterprise Support plan ." ; https://docs.aws.amazon.com/waf/latest/developerguide/ddos-automatic-app-layer-response.html · "The time to establish a baseline is between 24 hours and 30 days" / "Starting March 26, 2026, the Anti-DDoS Managed Rule Group (Anti-DDOS AMR) for AWS WAF becomes the default solution" ; https://docs.aws.amazon.com/waf/latest/developerguide/ddos-request-service-credit.html · "you must have associated an AWS WAF web ACL and implemented a rate-based rule in the web ACL in Block mode" · 2026-10-01 |
| NW.dns | L3/L4 | Route 53 호스티드 존 보호 가능 | — | https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-protected-resources.html · "Amazon Route 53 hosted zones." · 2026-10-01 |
| NW.egress | — | 해당 없음(NAT 게이트웨이는 보호 대상 아님) | — | https://docs.aws.amazon.com/waf/latest/developerguide/ddos-protections-by-resource-type.html · "NAT Gateways handle outbound traffic only, whereas Shield Advanced protects against inbound DDoS." · 2026-10-01 |
| NW.private_connectivity | — | 해당 없음 | — | — |
| NW.regions | — | 서울 포함 | — | [PL] https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSShield/current/ap-northeast-2/index.csv · "Shield Data Transfer Out of ELB in ICN - First 100 TB" (APN2-DataTransfer-Shield-Bytes) · 2026-10-01 |
| NW.cost_floor | — | **월 $3,000 + 1년 약정**(조직 단위 1회 과금) + 보호 리소스 DTO 요금 | — | [PL] https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSShield/current/aws-other/index.csv · "$3,000 for First Subscription" ; https://aws.amazon.com/shield/pricing/ · "It requires a 1-year subscription commitment and charges a monthly fee" · 2026-10-01 |

### 비용 구조
- 구독료 월 $3,000(1년 약정, Organizations 통합 결제 패밀리당 1회). [PL aws-other] "$0 for additional Subscriptions".
- 데이터 전송 요금(Shield DTO, 일반 DTO에 추가): [PL 서울] ELB·EIP 첫 100 TB $0.050/GB, 다음 400 TB $0.040, 500 TB 초과 $0.030 (`APN2-DataTransfer-Shield-Bytes`). CloudFront 첫 100 TB $0.025/GB, Global Accelerator 첫 100 TB $0.025/GB (aws-other).
- 포함: 보호 리소스의 WAF 기본 요금(web ACL·규칙·기본 요청, 1,500 WCU·기본 본문 한도까지), 월 500억 요청까지. 제외: Bot Control, CAPTCHA, 1,500 WCU 초과, 본문 확장 검사. https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary.html · "Examples of non-standard AWS WAF costs are those for Bot Control, for the CAPTCHA rule action, for web ACLs that use more than 1,500 WCUs, and for inspecting the request body beyond the default body size."
- SRT를 쓰려면 AWS Business/Enterprise Support 비용 추가.

### 교체 계열 정보
- Cloud Armor Enterprise Annual(월 $3,000·1년, 청구 보호·DDoS 대응 지원, 3.5), Cloudflare Enterprise(3.6). 소규모 앱은 Shield Standard + WAF 레이트 규칙 + CloudFront로 대체가 일반적(추론). ⚠️근거없음

### 함정
- 구독만 하고 `aws_shield_protection`을 안 만들면 보호·비용 보호 없음. 공격 중 추가한 리소스는 비용 보호 대상 아님.
- Terraform `aws_shield_subscription`은 1년 약정 결제를 일으킴. 삭제해도 약정은 남음(추론, 문서상 `skip_destroy`·`auto_renew`만 존재). ⚠️근거없음
- IPv6 트래픽은 보호 밖.
- 자동 L7 완화는 web ACL에 150 WCU를 추가 → 1,500 WCU 넘으면 WAF 추가 요금(그 부분은 Shield에 포함 안 됨).
- SRT는 Support 플랜 없으면 사용 불가.

### 생성 산출물
- Terraform 리소스:
  - `aws_shield_subscription` (https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/shield_subscription) — `auto_renew` ("ENABLED" 기본), `skip_destroy`
  - `aws_shield_protection` (https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/shield_protection) — `name`, `resource_arn`
  - `aws_shield_application_layer_automatic_response` (https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/shield_application_layer_automatic_response) — `resource_arn`(CloudFront·ALB만), `action` = `COUNT`|`BLOCK`
- 요구에 따라 반드시 명시할 속성: 가용성 요구가 높고 비용 상한 보호 필요(비용·보안)일 때만 생성. `aws_shield_protection.resource_arn` = CloudFront ARN 또는 ALB ARN 또는 EIP 할당 ARN. CloudFront·ALB면 3.1 web ACL에 Block 레이트 규칙 동시 생성(비용 보호 조건).
- Checkov: 해당 체크 없음(Shield 전용 체크 확인 못 함; 인덱스상 shield 리소스에 걸린 것은 CKV2_AWS_37·CKV2_AWS_75 오매핑 항목뿐).
- 배포 후 검증: `aws shield describe-subscription --query 'Subscription.{Start:StartTime,Renew:AutoRenew}'` → 값 반환. `aws shield list-protections --query 'Protections[].ResourceArn'` → 대상 ARN 포함. `aws shield describe-protection --resource-arn <ARN>`.

## 3.4 Google Cloud Armor — Standard
- 계열: 네트워크-WAF·DDoS
- 서울 리전: 있음(추론: 백엔드 보안 정책은 글로벌/리전 외부 ALB에 붙으며 리전 정책은 리전 LB와 같은 리전. 가격 페이지에 리전별 차등 없음) ⚠️근거없음

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L3/L4/L7 | 구글 LB(GFE)에 붙는 보안 정책. L3/L4 볼륨 DDoS 상시 보호 + L7 규칙(WAF) | 지원 LB: 글로벌 외부 ALB, 클래식 ALB, 리전 외부 ALB, 리전 내부 ALB(백엔드 정책), 글로벌·클래식 프록시 NLB, 리전 외부 패스스루 NLB(네트워크 엣지 정책), Cloud CDN, Media CDN. 서버리스 NEG(Cloud Run 등)는 LB 경유 시에만 | https://cloud.google.com/armor/docs/armor-enterprise-overview · "Always-on protection from Layer 3 and Layer 4 (L3 and L4) volumetric and network protocol-based DDoS attacks." ; https://cloud.google.com/armor/docs/security-policy-overview · "Cloud Armor also protects serverless NEGs when traffic is routed through a load balancer." · 2026-10-01 |
| NW.idle_timeout | — | 해당 없음(LB 값) | — | — |
| NW.request_timeout | — | 해당 없음 | — | — |
| NW.websocket | — | 미확인 | — | — |
| NW.protocols | L7 | QUIC(HTTP/3) LB와 함께 사용 가능. 프록시 NLB에서는 deny가 새 TCP 연결에만 적용, 상태 코드 무시 | — | https://cloud.google.com/armor/docs/security-policy-overview · "You can optionally use the QUIC protocol with load balancers that use Cloud Armor." / "Cloud Armor enforces the security policy rule deny action only on new connection requests." · 2026-10-01 |
| NW.body_size | L7 | 사전 구성 WAF 규칙 본문 검사 한도 8/16/32/48/64 kB 중 선택(64 kB 지원 2026-02-18 GA). **기본값은 공식 원문에서 확인 못 함(미확인)**. 한도 밖 본문은 검사 안 됨. 본문 검사는 `evaluatePreconfiguredWaf()`와 `request.body`/`request.params` 참조 규칙만 | 초과 본문 차단은 `content-length` 조건 규칙으로 별도 구성 권장 | https://docs.cloud.google.com/armor/docs/configure-waf · "Cloud Armor preconfigured WAF rules can only inspect up to the first 64 kB (either 8 kB, 16 kB, 32 kB, 48 kB, or 64 kB) of a request body." ; https://docs.cloud.google.com/feeds/armor-release-notes.xml · "February 18, 2026 ... inspection up to the first 64 kB ... is Generally Available." ; https://cloud.google.com/armor/docs/security-policy-overview · "The remainder of the request body might contain payloads that would match a WAF rule signature, which your application might accept." · 2026-10-01 |
| NW.draining | — | 해당 없음 | — | — |
| NW.health_check | — | 해당 없음 | — | — |
| NW.tls | L7 | TLS 종단은 LB. JA3/JA4 지문을 레이트 키로 사용 가능 | — | https://docs.cloud.google.com/armor/docs/rate-limiting-overview · "TLS_JA4_FINGERPRINT : JA4 TLS/SSL fingerprint if the client connects using HTTPS , HTTP/2 or HTTP/3" · 2026-10-01 |
| NW.client_ip | L3/L7 | 외부 ALB 뒤에서는 `origin.ip` = 클라이언트 IP(GFE가 종단). **서드파티 CDN 뒤면 `origin.ip` = 마지막 중개자 IP** → `advanced_options_config.user_ip_request_headers`로 `origin.user_ip` 지정(헤더 없거나 무효면 `origin.ip`로 대체). 레이트 키 `XFF_IP`=XFF 첫 번째 IP, `USER_IP`. **앱 전달 헤더**: LB가 `X-Forwarded-For: [<supplied-value>,]<client-ip>,<load-balancer-ip>` 설정 | user IP 헤더는 클라이언트가 조작 가능 → CDN 경유 트래픽만 받도록 검증 필요 | https://docs.cloud.google.com/armor/docs/user-ip-overview · "the client IP in the origin.ip field is the IP address of the last intermediary, not the original client." / "Cloud Armor falls back to the client IP address ( origin.ip ) instead." ; https://docs.cloud.google.com/load-balancing/docs/https · "X-Forwarded-For : [<supplied-value>,]<client-ip>,<load-balancer-ip>" · 2026-10-01 |
| NW.routing | L7 | 액션 allow, deny(403/404/502, 레이트 초과 시 429 포함), redirect(reCAPTCHA·302), throttle, rate_based_ban, 헤더 추가. 정책은 백엔드 서비스 단위 | — | https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_security_policy (원문 GitHub) · "`deny()`: deny access to target, returns the HTTP response code specified" · 2026-10-01 |
| NW.scaling | L7 | 정책·규칙 수는 쿼터 한도(값 미확인) | — | — ⚠️근거없음 |
| NW.availability | L7 | 엣지 보안 정책은 구글 네트워크 최외곽(Cloud CDN 캐시 앞)에서 집행, 백엔드 보안 정책은 캐시 미스 요청에만 | 백엔드 서비스당 백엔드 정책 1 + 엣지 정책 1 | https://cloud.google.com/armor/docs/security-policy-overview · "When edge security policies and backend security policies are attached to the same backend service, backend security policies are enforced only for cache miss requests" · 2026-10-01 |
| NW.caching | L7 | 엣지 정책만 백엔드 버킷·캐시 콘텐츠 보호. 엣지 정책 필터 필드는 IP·ASN·지역·헤더·메서드·경로·쿼리·스킴만(WAF·레이트 불가) | — | https://cloud.google.com/armor/docs/security-policy-overview · "Only edge security policies can be applied to backend buckets." / "Edge security policies support filtering based on only origin.asn , origin.ip , origin.region_code , request.headers , request.method , request.path , request.query , and request.scheme ." · 2026-10-01 |
| NW.security | L7 | **기본 규칙(우선순위 2147483647) 항상 존재. 문서상 기본 규칙 액션 = deny** [충돌: Terraform은 규칙 미지정 생성 시 allow 기본 규칙 추가]. **사전 구성 WAF(OWASP CRS 4.22/3.3: sqli-v422-stable, xss-v422-stable 등, `cve-canary`=Log4j)는 기본 포함 아님 → 규칙으로 `evaluatePreconfiguredWaf()` 직접 추가.** 레이트 리밋: `throttle`(한도 1~1,000,000) / `rate_based_ban`(한도 1~10,000, ban_duration 60~3600초). `interval_sec` ∈ {10,30,60,120,180,240,300,600,900,1200,1800,2700,3600}. 키: ALL·IP·HTTP_HEADER·XFF_IP·HTTP_COOKIE·HTTP_PATH·SNI·REGION_CODE·JA3/JA4·USER_IP·ASN, 최대 3개 조합. **근사, 리전별 독립 집행, 백엔드 서비스별 적용.** LB 생성 시 기본 보안 정책을 고르면 500 요청/60초 throttle. Adaptive Protection: Standard는 **기본 알림만**(서명·추천 규칙 없음) | 키 헤더·쿠키 값은 앞 128바이트 | https://cloud.google.com/armor/docs/security-policy-overview · "The default action for the default rule is deny , but you can change the action to allow ." [충돌] Terraform 원문 · "If no rules are provided when creating a security policy, a default rule with action \"allow\" will be added." ; https://docs.cloud.google.com/armor/docs/rate-limiting-overview · "The value must be 10, 30, 60, 120, 180, 240, 300, 600, 900, 1200, 1800, 2700, or 3600 seconds." / "The minimum value is 1 and the maximum value is 1,000,000." / "The minimum value is 1 request and the maximum value is 10,000 requests." / "the default threshold is 500 requests during each one-minute interval" / "The configured thresholds for throttling and rate-based bans are enforced independently in each of the Google Cloud regions" / "the enforced rate limits are approximate" / "Cloud Armor applies the rate limiting threshold to each associated backend." ; https://cloud.google.com/armor/docs/adaptive-protection-overview · "Full Adaptive Protection alerts are available only if you subscribe to Google Cloud Armor Enterprise. Otherwise, you receive only a basic alert." ; https://cloud.google.com/armor/docs/waf-rules · "These rules are based on the OWASP ModSecurity Core Rule Set (CRS), such as OWASP Core Rule Set 4.22" · 2026-10-01 |
| NW.dns | — | 해당 없음 | — | — |
| NW.egress | — | 해당 없음 | — | — |
| NW.private_connectivity | L7 | 리전 내부 ALB 백엔드 정책 지원(사설 트래픽 L7 필터) | — | https://cloud.google.com/armor/docs/security-policy-overview · "Backend security policies are used with backend services exposed by the following load balancer types: ... Regional internal Application Load Balancer" · 2026-10-01 |
| NW.regions | — | 글로벌 정책(글로벌 LB)·리전 정책(리전 LB) | 요청 요금이 글로벌/리전 정책별로 다름 | https://cloud.google.com/armor/pricing · "Requests (globally scoped security policies) $0.75 / 1,000,000 count" / "Requests (regionally scoped security policies) $0.60 / 1,000,000 count" · 2026-10-01 |
| NW.cost_floor | — | 정책 $0.006849315/시간(≈월 $5, 추론 ×730), 규칙 $0.001369863/시간(≈월 $1), 요청 100만당 글로벌 $0.75·리전 $0.60 | 최소 = 정책 1(+기본 규칙) ≈ 월 $5~6 + 요청 | https://cloud.google.com/armor/pricing · "Security policies $0.006849315 / 1 hour" / "Rules $0.001369863 / 1 hour" · 2026-10-01 ⚠️근거없음 |

### 비용 구조
- 정책 ≈$5/월, 규칙 ≈$1/월(시간 요율 ×730, 추론), 요청 $0.75/100만(글로벌 정책) 또는 $0.60/100만(리전 정책). 데이터 처리 요금 없음. 봇 관리는 reCAPTCHA 요금. 관리형 규칙(Managed rules)은 Preview 동안 무료. ⚠️근거없음
- 계층형(hierarchical) 정책을 Enterprise 미가입 프로젝트에서 만들면 **자동으로 Enterprise Paygo 가입**(월 ≈$200 발생). https://cloud.google.com/armor/pricing · "If you create a hierarchical security policy in a project that isn't enrolled in Cloud Armor Enterprise, your project is automatically enrolled in Cloud Armor Enterprise Paygo."

### 교체 계열 정보
- 상위: Cloud Armor Enterprise(3.5). AWS 대응: AWS WAF(3.1)+Shield Standard(3.2). Cloud Run 직접 URL(*.run.app)은 Cloud Armor를 못 붙이므로 외부 ALB + 서버리스 NEG 구성 필요(출처 위 NW.layer).

### 함정
- **기본 규칙 액션 불일치**: 문서는 deny가 기본, Terraform은 규칙 없이 만들면 allow 기본 규칙 추가. 생성기는 우선순위 2147483647 규칙을 항상 명시해야 함(allow 의도인데 deny로 생성되면 전 트래픽 403).
- **WAF 규칙 기본 없음**: 정책만 붙이면 OWASP 보호 없음. `evaluatePreconfiguredWaf('sqli-v422-stable', {'sensitivity': 1})` 등을 규칙으로 추가. 민감도 1부터 preview 모드로 시작 권장.
- **레이트 한도는 리전별·백엔드 서비스별 독립·근사**: 2개 리전에 배포하면 실효 한도 최대 2배, 백엔드 서비스 2개면 각자 한도.
- `XFF_IP` 키 fallback [충돌]: rate-limiting-overview는 "defaults to IP address", Terraform 문서는 "defaults to `ALL`". `ALL`로 떨어지면 전체 사용자가 한 버킷 → 대량 차단 위험.
- 엣지 정책에는 WAF·레이트 규칙 불가, 백엔드 정책은 캐시 미스에만 → Cloud CDN 캐시 적중 트래픽은 백엔드 정책으로 레이트 제한 안 됨.
- 본문 검사 한도 밖 페이로드는 통과. 업로드 앱(A7)은 한도 64 kB로 올려도 그 이상은 미검사.
- `rate_based_ban` 규칙은 이후 `throttle`로 바꿀 수 없음(반대는 가능).

### 생성 산출물
- Terraform 리소스:
  - `google_compute_security_policy` (https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_security_policy)
  - 연결: `google_compute_backend_service.security_policy` / `.edge_security_policy` (https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_backend_service), 리전 정책은 `google_compute_region_security_policy`(이름만 확인 안 함 → 미확인)
- 요구에 따라 반드시 명시할 속성:
  - `type` = `CLOUD_ARMOR`(백엔드) / `CLOUD_ARMOR_EDGE`(CDN·버킷 앞).
  - 기본 규칙 명시: `rule { priority = 2147483647, action = "allow"|"deny(403)", match { versioned_expr = "SRC_IPS_V1", config { src_ip_ranges = ["*"] } } }`.
  - OWASP: `rule { action = "deny(403)", priority = 1000, match { expr { expression = "evaluatePreconfiguredWaf('sqli-v422-stable', {'sensitivity': 1})" } }, preview = true(초기) }`, Log4j: `evaluatePreconfiguredWaf('cve-canary')`(CKV_GCP_73 충족용).
  - 레이트: `rule { action = "throttle"|"rate_based_ban", rate_limit_options { conform_action = "allow", exceed_action = "deny(429)", enforce_on_key = "IP"|"XFF_IP"|"USER_IP", rate_limit_threshold { count = N, interval_sec = 60 }, ban_duration_sec = 600(ban일 때) } }`. 앞단 서드파티 CDN(경로 요구)이면 `advanced_options_config { user_ip_request_headers = ["CF-Connecting-IP"] }` + `enforce_on_key = "USER_IP"`.
  - 본문 큰 요청(A7): `advanced_options_config { request_body_inspection_size = "64KB", json_parsing = "STANDARD" }`.
  - `adaptive_protection_config { layer_7_ddos_defense_config { enable = true } }` — Standard에서는 기본 알림만.
- Checkov: CKV_GCP_73 `google_compute_security_policy` — "Ensure Cloud Armor prevents message lookup in Log4j2. See CVE-2021-44228 aka log4jshell". 그 외 Cloud Armor 체크 확인 못 함.
- 배포 후 검증:
  - `gcloud compute backend-services describe <BS> --global --format='value(securityPolicy,edgeSecurityPolicy)'` → 정책 URL.
  - `gcloud compute security-policies describe <POLICY> --format='yaml(rules,advancedOptionsConfig,adaptiveProtectionConfig)'` → 2147483647 규칙 action 확인.
  - `curl -s -o /dev/null -w '%{http_code}\n' "https://<host>/?id=1'%20OR%20'1'='1"` → `403`(sqli 규칙 enforce 시).
  - `for i in $(seq 1 200); do curl -s -o /dev/null -w '%{http_code}\n' https://<host>/; done | sort | uniq -c` → 임계 초과 후 `429`.
  - `gcloud logging read 'resource.type="http_load_balancer" AND jsonPayload.enforcedSecurityPolicy.outcome="DENY"' --limit 5`.

## 3.5 Google Cloud Armor — Enterprise (Paygo / Annual)
- 계열: 네트워크-WAF·DDoS
- 서울 리전: 있음(추론, Standard와 같은 LB 범위; 가격 리전 차등 없음) ⚠️근거없음

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L3/L4/L7 | Standard 전체 + Adaptive Protection(L7 전체), 고급 네트워크 DDoS 보호(패스스루 NLB·프로토콜 포워딩·VM 공인 IP), 네트워크 엣지 보안 정책, 위협 인텔리전스, 주소 그룹 | 이름: 2024-04-03 "Managed Protection Plus" → "Cloud Armor Enterprise"(SKU·가격 동일) | https://cloud.google.com/armor/docs/armor-enterprise-overview · "Adaptive Protection for Layer 7 endpoints Advanced network DDoS protection for pass-through endpoints" ; https://docs.cloud.google.com/feeds/armor-release-notes.xml · "\"Cloud Armor Managed Protection Plus\" has been renamed to \"Cloud Armor Enterprise.\" ... SKU IDs and pricing are unchanged." · 2026-10-01 |
| NW.idle_timeout | — | 해당 없음 | — | — |
| NW.request_timeout | — | 해당 없음 | — | — |
| NW.websocket | — | 미확인 | — | — |
| NW.protocols | — | 3.4와 동일 | — | 3.4 참조 |
| NW.body_size | L7 | 3.4와 동일(8~64 kB) | — | 3.4 참조 |
| NW.draining | — | 해당 없음 | — | — |
| NW.health_check | — | 해당 없음 | — | — |
| NW.tls | — | 3.4와 동일 | — | 3.4 참조 |
| NW.client_ip | L3/L7 | 3.4와 동일(`origin.ip`/`origin.user_ip`, LB XFF) | — | 3.4 참조 |
| NW.routing | — | 3.4와 동일 | — | 3.4 참조 |
| NW.scaling | — | 쿼터 한도 내(값 미확인) | — | https://cloud.google.com/armor/docs/armor-enterprise-overview · "Resource limits Up to quota limit" · 2026-10-01 |
| NW.availability | L3/L4/L7 | 보호 리소스 = 등록 프로젝트의 외부 ALB·외부 프록시 NLB 백엔드 서비스·버킷(정책 미부착이어도 계수), 패스스루 NLB 백엔드·대상 풀·프로토콜 포워딩·VM | 고급 네트워크 DDoS를 리전에 켜면 그 리전 공인 VM 전부 계수 | https://cloud.google.com/armor/pricing · "global external Application Load Balancers, regional external Application Load Balancers and global external proxy Network Load Balancers are considered to be protected resources regardless of whether you have attached a security policy to them." · 2026-10-01 |
| NW.caching | — | 해당 없음 | — | — |
| NW.security | L3/L4/L7 | Adaptive Protection 전체(공격 서명·추천 규칙, 자동 배포는 Beta), DDoS 공격 가시성, **DDoS 대응 지원**(2024-09-03 이후 가입자는 posture review 통과 필요), **청구 보호(Annual만)**, 계층형 정책(Annual) | 레이트 규칙 단위는 3.4와 동일 | https://cloud.google.com/armor/docs/armor-enterprise-overview · "Customers who subscribed to Cloud Armor Enterprise after September 3, 2024 aren't eligible for DDoS Response Support until they have successfully completed a DDoS posture review." / "Cloud Armor DDoS bill protection requires your project to be enrolled in Cloud Armor Enterprise Annual." · 2026-10-01 |
| NW.dns | — | Cloud DNS 데이터 처리 "Included" | — | https://cloud.google.com/armor/pricing · "Cloud DNS Included" · 2026-10-01 |
| NW.egress | — | 해당 없음(단, 보호 리소스 인터넷 송신에 데이터 처리 요금) | — | 비용 구조 참조 |
| NW.private_connectivity | — | 해당 없음 | — | — |
| NW.regions | — | 3.4와 동일 | — | — |
| NW.cost_floor | — | **Paygo: 월 $200/프로젝트**(보호 리소스 2개 포함, 추가 리소스당 월 $200) + 데이터 처리 $0.075/GiB(첫 100 TiB, LB). **Annual: 월 $3,000/결제 계정**(리소스 100개 포함, 추가당 월 $30, 12개월 약정) + $0.05/GiB | WAF 정책·규칙·요청 요금 포함 | https://cloud.google.com/armor/docs/armor-enterprise-overview · "$200/month per project $200/month per protected resource after first 2 resources $3000/month per billing account $30/month per protected resource after first 100 resources" ; https://cloud.google.com/armor/pricing · "$0.273972603 / 1 hour" / "$4.109589041 / 1 hour" / "0 gibibyte to 102,400 gibibyte $0.075 / 1 gibibyte, per 1 month / project" · 2026-10-01 |

### 비용 구조
- Paygo: 구독 $0.273972603/시간(≈$200/월), 보호 리소스 3번째부터 같은 요율. 데이터 처리(LB·VM): 첫 100 TiB $0.075/GiB, ~500 TiB $0.06, 이후 $0.05. CDN 경유: $0.0375 → $0.02. 프로젝트 단위 집계.
- Annual: 구독 $4.109589041/시간(≈$3,000/월), 리소스 101번째부터 $0.04109589/시간(≈$30). 데이터 처리 LB·VM $0.05/0.04/0.03, CDN $0.025~$0.01. 결제 계정 단위 집계, 1년 약정.
- 정책·규칙·요청 요금 포함("All included"). 데이터 처리 요금은 LB 데이터 처리 요금과 별개.

### 교체 계열 정보
- AWS Shield Advanced(3.3, 월 $3,000·1년), Cloudflare Enterprise(3.6). 단일 프로젝트 소규모면 Standard + 수동 레이트 규칙이 대부분 충분(추론). ⚠️근거없음

### 함정
- Paygo는 **외부 ALB가 있는 프로젝트를 등록만 해도** 그 LB들이 보호 리소스로 계수 → 리소스 3개부터 개당 월 $200.
- 데이터 처리 요금이 송신 트래픽 전체에 붙음(일반 egress 요금에 추가).
- 계층형 정책 생성 = 자동 Paygo 가입(3.4 비용 구조).
- 청구 보호는 Annual 전용, DDoS 대응 지원은 posture review 조건.

### 생성 산출물
- Terraform 리소스: `google_compute_security_policy`(3.4와 동일) + 프로젝트 등록 리소스 `google_compute_project_cloud_armor_tier`(이름 원문 확인 안 함 → 미확인). 결제 계정 구독은 콘솔·gcloud(Terraform 리소스 미확인).
- 요구에 따라 반드시 명시할 속성: `adaptive_protection_config { layer_7_ddos_defense_config { enable = true, rule_visibility = "STANDARD"|"PREMIUM" } }`. 자동 배포는 google-beta `auto_deploy_config`(Beta).
- Checkov: CKV_GCP_73(3.4와 동일). Enterprise 전용 체크 없음.
- 배포 후 검증: `gcloud compute project-info describe --format='value(cloudArmorTier)'` → `CA_ENTERPRISE_PAYGO` 또는 `CA_ENTERPRISE_ANNUAL`(값 이름은 미확인, 추론). `gcloud compute security-policies describe <POLICY> --format='value(adaptiveProtectionConfig.layer7DdosDefenseConfig.enable)'` → `True`. ⚠️근거없음

## 3.6 Cloudflare WAF·DDoS — Free / Pro / Business / Enterprise
- 계열: 네트워크-WAF·DDoS
- 서울 리전: 글로벌(근거: 프록시 경유 전 트래픽에 데이터센터 단위로 집행, 레이트 카운터도 데이터센터별 — 아래 NW.security. 서울 데이터센터 존재 여부는 이 절에서 미확인)

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L3/L4/L7 | 역방향 프록시(오렌지 구름) 위 WAF·DDoS. **DDoS는 모든 플랜 L3~L7 무제한·무과금** | 프록시 꺼진 레코드(DNS only)는 L7 보호 없음(추론) | https://developers.cloudflare.com/ddos-protection/about/ · "Cloudflare provides unmetered and unlimited distributed denial-of-service (DDoS) protection at layers 3, 4, and 7 to all customers on all plans and services." · 2026-10-01 ⚠️근거없음 |
| NW.idle_timeout | — | 해당 없음(CDN 절 참조) | — | — |
| NW.request_timeout | — | 해당 없음 | — | — |
| NW.websocket | — | 해당 없음(CDN 절 참조) | — | — |
| NW.protocols | — | 해당 없음 | — | — |
| NW.body_size | L7 | 관리형 규칙 본문 검사 한도: Enterprise 128 KB, 기타 유료 플랜은 더 낮음(요청 시 증설), **Free 1 MB**(원문 그대로). 잘림 여부 필드 `http.request.body.truncated` | — | https://developers.cloudflare.com/waf/managed-rules/ · "For Enterprise customers, the maximum body size is 128 KB." / "For users in the Free plan, the limit is 1 MB." · 2026-10-01 |
| NW.draining | — | 해당 없음 | — | — |
| NW.health_check | — | 해당 없음 | — | — |
| NW.tls | L7 | JA3/JA4는 Enterprise Bot Management에서만 레이트 키 | — | https://developers.cloudflare.com/waf/rate-limiting-rules/ · "Only available to Enterprise customers who have purchased Bot Management." · 2026-10-01 |
| NW.client_ip | L3/L7 | WAF·레이트 규칙 IP 키 = `ip.src`(Cloudflare에 접속한 클라이언트 IP). "IP with NAT support" = `cf.unique_visitor_id`(Business+). **앱 전달 헤더**: `CF-Connecting-IP`(클라이언트 IP), `X-Forwarded-For`(기존 값이 있으면 덧붙임), `True-Client-IP`(Enterprise, 관리형 변환으로 추가) | 원본(오리진)은 Cloudflare IP만 허용해야 우회 차단(추론) | https://developers.cloudflare.com/waf/rate-limiting-rules/parameters/ · "IP | `ip.src`" / "IP with NAT support | `cf.unique_visitor_id`" ; https://developers.cloudflare.com/fundamentals/reference/http-headers/ · "`CF-Connecting-IP` provides the client IP address connecting to Cloudflare to the origin web server." / "`True-Client-IP` is only available on an Enterprise plan." · 2026-10-01 ⚠️근거없음 |
| NW.routing | — | 해당 없음(액션: block, challenge, managed_challenge, js_challenge, log, skip 등) | — | https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/ruleset (원문 GitHub `docs/resources/ruleset.md`) · "Available values: \"block\", \"challenge\", ... \"managed_challenge\"" · 2026-10-01 |
| NW.scaling | L7 | 커스텀 규칙 수 Free 5 / Pro 20 / Business 100 / Ent 1,000. 레이트 규칙 수 Free 1 / Pro 2 / Business 5 / Ent 100 | — | https://developers.cloudflare.com/waf/custom-rules/ · "Number of rules | 5 | 20 | 100 | 1,000" ; https://developers.cloudflare.com/waf/rate-limiting-rules/ · "Number of rules | 1 | 2 | 5 | 100" · 2026-10-01 |
| NW.availability | L3/L4/L7 | 글로벌 애니캐스트(추론) | — | — ⚠️근거없음 |
| NW.caching | L7 | 레이트 규칙 캐시 제외(캐시 적중은 안 셈) 옵션 Business 이상 | — | https://developers.cloudflare.com/waf/rate-limiting-rules/ · "Cache exclusion | No | No | Yes | Yes | Yes" · 2026-10-01 |
| NW.security | L7 | **기본으로 켜지는 것**: DDoS 관리형 규칙(전 플랜), **Free Managed Ruleset(Free 플랜에 기본 배포)**. **Cloudflare Managed Ruleset·OWASP Core Ruleset은 Pro 이상, 수동 배포**(Managed Ruleset은 배포해도 일부 규칙만 활성). **레이트 리밋**: 기간 Free **10초 고정**, Pro ≤1분, Business ≤10분, Ent ≤65,535초. 지원 값 10,15,20,30,40,45,60,90,120,180,240,300,480,600,…. 완화 지속 Free 10초, Pro ≤1시간, Business·Ent ≤1일. 카운팅 특성 Free·Pro=IP, Business=IP/IP with NAT, Ent Advanced=헤더·쿠키·쿼리·ASN·국가·경로·JA3/4·JSON·본문 등. **카운터는 데이터센터별(전역 아님), `cf.colo.id` 필수 특성**, 수 초 지연. Free 레이트 규칙 식 필드는 Path·Verified Bot만. Bot Fight Mode: 무료, 커스텀 규칙으로 **우회·Skip 불가**, API·모바일 트래픽 챌린지 가능. Under Attack 모드: 기본 꺼짐, JS 인터스티셜 | — | https://developers.cloudflare.com/waf/get-started/ · "The Free Managed Ruleset is deployed by default on Free plans" / "By default, the Cloudflare Managed Ruleset enables only a subset of rules" ; https://developers.cloudflare.com/waf/managed-rules/ · "Cloudflare Managed Ruleset | No | Yes | Yes | Yes" ; https://developers.cloudflare.com/waf/rate-limiting-rules/ · "Counting periods | 10 s | All supported values up to 1 min" / "Counting characteristics | IP | IP | IP, IP with NAT support" ; https://developers.cloudflare.com/waf/rate-limiting-rules/request-rate/ · "Counters are not shared across data centers, with the exception of data centers associated with the same geographical location." / "you must include the `cf.colo.id` characteristic explicitly." ; https://developers.cloudflare.com/bots/get-started/bot-fight-mode/ · "You cannot bypass or skip Bot Fight Mode using WAF custom rules or Page Rules." / "they may challenge API or mobile app traffic" ; https://developers.cloudflare.com/fundamentals/reference/under-attack-mode/ · "Under Attack mode is turned off by default for your zone." · 2026-10-01 |
| NW.dns | — | 해당 없음(DNS 절 참조) | — | — |
| NW.egress | — | 해당 없음 | — | — |
| NW.private_connectivity | — | 해당 없음 | — | — |
| NW.regions | — | 글로벌 | — | — ⚠️근거없음 |
| NW.cost_floor | — | Free $0(DDoS·Free Managed Ruleset·레이트 1개). Pro $20/월(연간)·$25/월(월간), Business $200/월(연간)·$250/월(월간), Enterprise 계약 | 레이트 규칙은 사용량 과금 없음(구 Rate Limiting만 사용량 과금) | https://www.cloudflare.com/plans/ · "$20 /mo billed annually, or $25/mo billed" / "$200 /mo billed annually, or $250/mo billed monthly" ; https://developers.cloudflare.com/waf/rate-limiting-rules/ · "Cloudflare Rate Limiting (previous version, no longer available): Documentation for the previous version of rate limiting rules (billed based on usage)." · 2026-10-01 |

### 비용 구조
- 플랜 정액. DDoS 완화 트래픽 과금 없음(unmetered). Advanced Rate Limiting·Bot Management·Sensitive Data Detection은 Enterprise 계약.

### 교체 계열 정보
- AWS WAF(3.1)·Cloud Armor(3.4)를 원본 앞에 둔 상태에서 Cloudflare를 추가하면 뒤쪽 WAF는 Cloudflare IP를 봄 → forwarded IP(`CF-Connecting-IP`) 설정 필요. Vercel 앞에 Cloudflare 프록시를 두면 Vercel이 XFF를 덮어씀(3.7).

### 함정
- **Free 플랜 레이트 리밋은 10초 기간·10초 차단·IP 키·Path 조건뿐, 규칙 1개** → "분당 100회" 같은 요구는 Free에서 표현 불가(10초당 N회로만).
- 레이트 카운터가 데이터센터별 → 분산 클라이언트(봇넷)는 전역 한도 초과 가능, IP 키 없이 쓰면 데이터센터당 한도.
- **Terraform `cloudflare_ruleset`은 존·페이즈 진입점 ruleset 전체를 소유** → 대시보드에서 만든 규칙·Free Managed Ruleset 배포를 덮어쓸 수 있음. https://developers.cloudflare.com/terraform/additional-configurations/waf-managed-rulesets/ · "Terraform assumes that it has complete control over account and zone rulesets."
- Bot Fight Mode는 우회 불가 → API·웹훅 수신 앱(서버 간 호출)은 켜면 안 됨(Super Bot Fight Mode는 Skip 가능).
- Under Attack 모드는 JS 실행 필요 → API·모바일 클라이언트 실패.
- 관리형 규칙 본문 한도 밖은 미검사(`http.request.body.truncated`로 차단 규칙 별도).

### 생성 산출물
- Terraform 리소스: `cloudflare_ruleset` (https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/ruleset, provider v5.26.0)
- 요구에 따라 반드시 명시할 속성:
  - 공통: `zone_id`, `kind = "zone"`, `phase`.
  - 관리형 WAF(Pro 이상): `phase = "http_request_firewall_managed"`, `rules = [{ action = "execute", action_parameters = { id = "efb7b8c949ac4650a09736fc376e9aee" }, expression = "true" }]`(Cloudflare Managed Ruleset), OWASP Core Ruleset도 execute.
  - 레이트(보안·brute force): `phase = "http_ratelimit"`, `rules = [{ action = "block", expression = "(http.request.uri.path eq \"/login\")", ratelimit = { characteristics = ["cf.colo.id", "ip.src"], period = 10(Free)|60(Pro), requests_per_period = N, mitigation_timeout = 10(Free)|600 } }]`. Business 이상 + 캐시 많은 사이트면 `requests_to_origin = true`.
- Checkov: 해당 체크 없음(Checkov Terraform 인덱스에 cloudflare_* WAF 체크 확인 못 함).
- 배포 후 검증:
  - `curl -sI https://<host>/ | grep -i -E 'cf-ray|server: cloudflare'` → 존재.
  - `curl -s -H "Authorization: Bearer $CF_TOKEN" https://api.cloudflare.com/client/v4/zones/$ZONE/rulesets/phases/http_ratelimit/entrypoint | jq '.result.rules[].ratelimit'` → 설정값.
  - `for i in $(seq 1 50); do curl -s -o /dev/null -w '%{http_code}\n' https://<host>/login; done | sort | uniq -c` → `429`(차단 기본 응답, 실제 코드는 설정 따름) 등장.
  - `curl -s -o /dev/null -w '%{http_code}\n' "https://<host>/?q=<script>alert(1)</script>"` → 관리형 규칙 배포 시 `403`.

## 3.7 Vercel Firewall — Hobby / Pro / Enterprise (요약)
- 계열: 네트워크-WAF·DDoS
- 서울 리전: 글로벌(플랫폼 엣지; 레이트 카운터 리전별 — 아래)

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L3/L4/L7 | 플랫폼 내장 방화벽. **모든 플랜 L3·L4·L7 DDoS 자동 완화** | — | https://vercel.com/docs/vercel-firewall/ddos-mitigation · "Vercel mitigates against L3, L4, and L7 DDoS attacks regardless of the plan you are on." · 2026-10-01 |
| NW.idle_timeout / NW.request_timeout / NW.websocket / NW.protocols / NW.draining / NW.health_check / NW.tls / NW.dns / NW.egress / NW.private_connectivity / NW.caching | — | 해당 없음(플랫폼 엣지 절 참조) | — | — |
| NW.body_size | — | 미확인 | — | — |
| NW.client_ip | L7 | 방화벽 IP 키 = 클라이언트 IP. **앱 전달 헤더**: `x-forwarded-for`, `x-real-ip`, `x-vercel-forwarded-for`(모두 클라이언트 IP). **Vercel 앞에 프록시를 두면 XFF를 덮어쓰고 외부 IP를 전달하지 않음**(Trusted Proxy는 별도 권한/플랜) | — | https://vercel.com/docs/headers/request-headers · "we currently overwrite the X-Forwarded-For header and do not forward external IPs" / "`x-forwarded-for` could be overwritten if you're using a proxy on top of Vercel." · 2026-10-01 |
| NW.routing | — | 해당 없음(액션 log, deny, challenge, bypass, rate limit, redirect) | — | https://vercel.com/docs/vercel-firewall/vercel-waf/custom-rules · "log, deny, challenge, bypass, or rate limit traffic" · 2026-10-01 |
| NW.scaling | L7 | 커스텀 규칙 Hobby 3 / Pro 40 / Ent 1,000. 레이트 규칙 Hobby 1 / Pro 40 / Ent 1,000(프로젝트당) | — | https://vercel.com/docs/vercel-firewall/vercel-waf/custom-rules · "Custom Rules | Up to 3 | Up to 40 | Up to 1000" ; https://vercel.com/docs/vercel-firewall/vercel-waf/rate-limiting · "Number of rules | 1 per project | 40 per project | 1000 per project" · 2026-10-01 |
| NW.availability | — | 글로벌(추론) | — | — ⚠️근거없음 |
| NW.security | L7 | **기본 켜짐**: DDoS 완화만. **관리형 규칙(OWASP CRS·Bot Protection·AI Bots)은 Enterprise(영업 문의), Bot·AI Bots 규칙은 기본 비활성.** 레이트 리밋: Fixed window(전 플랜)/Token bucket(Ent), 창 **최소 10초**, 최대 10분(Hobby·Pro)/1시간(Ent), UI 기본 60초·100요청, 키 IP·JA4 Digest(Ent는 UA·임의 헤더 추가), **카운터 리전별**. Attack Mode(구 Attack Challenge Mode): 모든 플랜 무료, 알려진 봇·자기 계정 Functions·Cron 통과 | — | https://vercel.com/docs/vercel-firewall/vercel-waf · "Learn how to enable managed rulesets for your project (Enterprise plan)" ; https://vercel.com/docs/vercel-firewall/vercel-waf/custom-rules · "WAF Managed Rulesets | N/A | N/A | Contact sales" ; https://vercel.com/docs/vercel-firewall/vercel-waf/rate-limiting · "Counting window | Minimum: **10s**, Maximum: **10mins**" / "Rate limit counters are tracked on a per-region basis" / "defaults to 60s" ; https://vercel.com/docs/vercel-firewall/attack-mode · "Attack Mode is available for free on all plans" · 2026-10-01 |
| NW.regions | — | 글로벌 | 레이트 리밋 요금은 요청 출발 리전별 | https://vercel.com/docs/vercel-firewall/vercel-waf/rate-limiting · "The pricing is based on the region(s) from which the requests come from." · 2026-10-01 |
| NW.cost_floor | — | DDoS·IP 차단·커스텀 규칙 무료(플랜 포함). **deny·challenge·rate-limit으로 막힌 요청은 CDN Requests·FDT 미과금.** 레이트 리밋: Hobby 허용 요청 100만 포함, Pro 사용량 과금(리전 단가 값 미확인) | — | https://vercel.com/docs/vercel-firewall/vercel-waf/usage-and-pricing · "WAF deny, challenge, or rate-limit mitigated traffic does not incur CDN Requests or Fast Data Transfer (FDT)." ; https://vercel.com/docs/vercel-firewall/ddos-mitigation · "Vercel does not charge customers for traffic that gets blocked with DDoS" · 2026-10-01 |

### 비용 구조
- 플랜 요금에 포함. 레이트 리밋(Pro)·OWASP CRS(요청 수·크기 기준, Ent)는 리전 단가 과금(단가 미확인). 차단된 트래픽 미과금.

### 교체 계열 정보
- Cloudflare(3.6)를 앞에 두면 Vercel이 XFF를 덮어써 클라이언트 IP가 Cloudflare IP가 됨 → Vercel 레이트 리밋 IP 키가 무력화(추론, NW.client_ip 근거). ⚠️근거없음

### 함정
- OWASP 관리형 규칙이 Hobby·Pro에 없음 → SQLi/XSS 방어 요구(보안)가 있으면 Enterprise 또는 앞단 WAF 필요.
- Hobby 레이트 규칙 1개, 카운터 리전별(다리전 분산 공격 시 한도 초과).
- 시스템 완화가 프록시·공유 네트워크를 막으면 24시간 일시 중지 가능(악용 시 보호 꺼짐).

### 생성 산출물
- Terraform 리소스: `vercel_firewall_config` (https://registry.terraform.io/providers/vercel/vercel/latest/docs/resources/firewall_config)
- 요구에 따라 반드시 명시할 속성: `project_id`, `enabled = true`; 레이트(보안) `rules { rule { name, condition_group = [{ conditions = [{ type = "path", op = "pre", value = "/api" }] }], action = { action = "rate_limit", rate_limit = { algo = "fixed_window", window = 60, limit = 100, keys = ["ip"], action = "deny" }, action_duration = "1m" } } }`; Enterprise만 `managed_rulesets { owasp { ... } }`. (`keys` 값 문자열·`type` 값은 원문에 열거 없음 → 미확인)
- Checkov: 해당 체크 없음.
- 배포 후 검증: `curl -sI https://<host>/ | grep -i x-vercel-id` → 존재. `for i in $(seq 1 150); do curl -s -o /dev/null -w '%{http_code}\n' https://<host>/api/x; done | sort | uniq -c` → 한도 초과 후 `429`.

---

# 4. 인증서

## 4.1 AWS Certificate Manager (ACM) — 공개 인증서(통합 서비스용, DNS 검증)
- 계열: 네트워크-인증서
- 서울 리전: 있음 (ACM은 리전 리소스, ap-northeast-2 가격 오퍼 존재 [PL]. 단 CloudFront용은 us-east-1)

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | TLS | 인증서 발급·갱신만. TLS 종단은 ALB/NLB/CloudFront/API Gateway가 수행 | 통합 서비스 밖 사용은 "내보내기 가능" 또는 ACME 인증서(유료) | https://docs.aws.amazon.com/acm/latest/userguide/acm-public-certificates.html · "Use ACM public certificates with integrated AWS services like Elastic Load Balancing, Amazon CloudFront, and Amazon API Gateway." · 2026-10-01 |
| NW.idle_timeout / NW.request_timeout / NW.websocket / NW.protocols / NW.body_size / NW.draining / NW.client_ip / NW.routing / NW.caching / NW.egress / NW.private_connectivity / NW.health_check | — | 해당 없음 | | — |
| NW.tls | TLS | **유효기간 198일**(신규). 이전 395일 인증서는 만료 60일 전 갱신, 갱신본은 198일. **DNS 검증 자동 갱신 조건**: 만료 45일 전 확인 시점에 (1) AWS 서비스에서 사용 중, (2) SAN마다의 ACM CNAME이 공개 DNS에 존재·조회 가능. 충족 시 같은 ARN으로 갱신. 갱신 자격: 서비스에 연결됐거나 발급/갱신 후 내보낸 적 있음. **가져온(imported) 인증서·만료된 인증서는 자격 없음**. **EMAIL 검증**은 45일 전부터 메일 발송, 도메인 소유자가 링크를 눌러야 갱신(수동). 키: RSA_2048(기본), EC_prime256v1, EC_secp384r1. 와일드카드는 가장 왼쪽 한 단계 | 자동 검증 실패 시 Health/EventBridge 이벤트 30·15·7·3·1일 전 | https://docs.aws.amazon.com/acm/latest/userguide/acm-certificate-characteristics.html · "ACM certificates are valid for 198 days." · 2026-10-01; https://docs.aws.amazon.com/acm/latest/userguide/dns-renewal-validation.html · "At 45 days prior to expiration, ACM checks for the following renewal criteria" / "Previously issued certificates with a 395-day validity period renew 60 days before expiration and receive a renewed validity period of 198 days." / "The certificate is currently in use by an AWS service. All required ACM-provided DNS CNAME records (one for each unique Subject Alternative Name) are present and accessible via public DNS." · 2026-10-01; https://docs.aws.amazon.com/acm/latest/userguide/managed-renewal.html · "ELIGIBLE if associated with another AWS service" / "NOT ELIGIBLE if imported ." / "NOT ELIGIBLE if already expired." · 2026-10-01; https://docs.aws.amazon.com/acm/latest/userguide/email-renewal-validation.html · "Renewing a certificate requires action by the domain owner. ACM begins sending renewal notices to the email addresses associated with the domain 45 days before expiration." · 2026-10-01; https://docs.aws.amazon.com/acm/latest/userguide/acm-public-certificates.html · "RSA_2048 (the default if the parameter is not explicitly provided), EC_prime256v1, and EC_secp384r1" · 2026-10-01 |
| NW.scaling | — | 미확인(계정당 인증서 한도 확인 안 함) | | 미확인 |
| NW.availability | — | 리전 리소스. 같은 도메인이라도 리전마다 별도 인증서·별도 갱신 | | https://docs.aws.amazon.com/acm/latest/userguide/managed-renewal.html · "ACM certificates are regional resources . If you have certificates for the same domain name in multiple AWS Regions, each of these certificates must be renewed independently." · 2026-10-01 |
| NW.security | TLS | CT 로그 기록(옵션 `certificate_transparency_logging_preference`). 이벤트: 만료 임박 이벤트를 공개 인증서는 30일 전부터, 사설·가져온 인증서는 45일 전부터 매일(PutAccountConfiguration으로 변경 가능). 2025-06-17 이전 공개 인증서는 내보내기 불가 | | https://docs.aws.amazon.com/acm/latest/userguide/supported-events.html · "starting 45 days prior to expiration for private/imported certificates and 30 days prior to expiration for public certificates. This timing can be changed using the PutAccountConfiguration action" · 2026-10-01; https://docs.aws.amazon.com/acm/latest/userguide/acm-public-certificates.html · "ACM public certificates created prior to June 17, 2025 cannot be exported." · 2026-10-01 |
| NW.dns | L7 | DNS 검증 CNAME(SAN별)을 **영구 유지**해야 자동 갱신 | 영역 이전·CNAME 정리 시 갱신 실패 | https://docs.aws.amazon.com/acm/latest/userguide/dns-renewal-validation.html · "All required ACM-provided DNS CNAME records ... are present and accessible via public DNS." · 2026-10-01 |
| NW.regions | — | CloudFront 뷰어 인증서는 **us-east-1** 필수. ALB 등은 LB와 같은 리전(서울) | | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cnames-and-https-requirements.html · "make sure you request (or import) the certificate in the US East (N. Virginia) Region ( us-east-1 )" · 2026-10-01 |
| NW.cost_floor | — | 통합 서비스용 공개 인증서(내보내기 불가) 무료. 내보내기 가능 공개 인증서 FQDN당 $7, 와일드카드당 $79(발급·갱신마다). ACME 인증서 FQDN당 $1.00(첫 1k), 와일드카드 $5.00, 최대 45일 유효 | | https://aws.amazon.com/certificate-manager/pricing/ · "Public certificate (non-exportable) No cost" / "Exportable public certificate (Per standard fully qualified domain name) $7.00 (upon issuance and again only on certificate renewal)" / "(Per wildcard name) $79.00" / "ACME certificates are valid for a maximum of 45 days." · 2026-10-01 |

### 비용 구조
- 통합 서비스(ELB·CloudFront·API Gateway)용은 0원. EC2/EKS 안 Nginx·쿠버네티스에서 직접 쓰려면 내보내기 가능($7/FQDN·$79/와일드카드, 갱신마다) 또는 ACM ACME($1/FQDN, 45일) — 그 경우 Let's Encrypt(4.3, 무료)와 비교 대상.

### 교체 계열 정보
- Google Certificate Manager(4.2), Let's Encrypt+cert-manager(4.3). ACM 인증서는 AWS 통합 서비스 밖으로 못 옮김(내보내기 가능 인증서 제외).
- ACM 가격표는 "2026~2029 CA/B Forum 일정에 맞춰 더 짧은 유효기간 제공 계획"을 명시 → 유효기간은 계속 줄어듦.

### 함정
- 갱신 조건 "사용 중": 발급만 하고 리스너·배포에 연결하지 않은 인증서는 자동 갱신 안 됨(내보내기 한 경우 제외).
- DNS 검증 CNAME을 지우거나, DNS 공급자 이전 시 CNAME을 옮기지 않으면 45일 전 갱신 실패 → 이벤트는 30일 전부터.
- Cloudflare 등 외부 DNS에서 검증 CNAME을 프록시/flatten하면 검증 실패 가능 (추론). ⚠️근거없음
- EMAIL 검증은 사람이 클릭해야 함 → 무인 운영 금지.
- 가져온 인증서는 자동 갱신 없음.
- CloudFront용 인증서를 서울에 만들면 연결 불가. 멀티 리전이면 리전마다 인증서.
- 유효기간 198일, 갱신 시작 45일 전 → 갱신 실패 대응 여유 45일(이벤트 30일). 이전 "395일·60일" 가정으로 짠 모니터링 임계값은 틀림.
- [충돌] Terraform `aws_acm_certificate` 문서는 (사설 인증서 설명에서) "valid for 395 days ... renewal process will start 60 days before expiration"이라 기술 — ACM 공식 문서(198일·45일)와 다름. 공개 인증서 판정은 ACM 문서 기준.

### 생성 산출물
- Terraform 리소스: `aws_acm_certificate` (https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/acm_certificate), `aws_acm_certificate_validation` (https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/acm_certificate_validation), 검증용 `aws_route53_record`
- 요구에 따라 반드시 명시할 속성:
  - `validation_method = "DNS"` (항상. EMAIL 금지).
  - `domain_name`, `subject_alternative_names` → apex + www 등 모든 호스트.
  - `key_algorithm` → 기본 RSA_2048, 성능 요구 시 `EC_prime256v1`.
  - `lifecycle { create_before_destroy = true }` → F4(배포 중 중단 불가) 시 필수(사용 중 인증서 교체).
  - CloudFront용이면 `provider = aws.us_east_1`(또는 `region = "us-east-1"` 인자, 프로바이더 6.x 문서에 `region` 존재).
  - `options { export = "ENABLED" }` → AWS 통합 서비스 밖에서 써야 할 때만(유료).
  - `aws_route53_record`(for_each `domain_validation_options`, `allow_overwrite = true`, `ttl = 60`) + `aws_acm_certificate_validation.validation_record_fqdns` → 발급 대기(기본 타임아웃 create 75m).
- Checkov: `CKV_AWS_233` "Ensure Create before destroy for ACM certificates", `CKV_AWS_234` "Verify logging preference for ACM certificates", `CKV2_AWS_71` "Ensure AWS ACM Certificate domain name does not include wildcards".
- 배포 후 검증:
  - `aws acm describe-certificate --certificate-arn <arn> --query "Certificate.[Status,RenewalEligibility,InUseBy,NotAfter]"` → `ISSUED`, `ELIGIBLE`, InUseBy 비어 있지 않음.
  - `dig +short _<token>.app.example.com CNAME` → `*.acm-validations.aws.` 값 유지.
  - `openssl s_client -connect app.example.com:443 -servername app.example.com </dev/null 2>/dev/null | openssl x509 -noout -issuer -dates -ext subjectAltName` → Amazon 발급자, notAfter ≈ 발급일+198일, SAN 일치.

## 4.2 Google Certificate Manager + Compute Engine Google 관리형 SSL 인증서
- 계열: 네트워크-인증서
- 서울 리전: 일부 (Certificate Manager: 전역·리전·교차 리전 인증서, DNS 승인이면 리전 인증서 가능. Compute 관리형(클래식)은 전역 외부 ALB·클래식 ALB·외부 프록시 NLB만)

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | TLS | 인증서 발급·갱신. 종단은 Google Cloud LB 대상 프록시 | | https://cloud.google.com/load-balancing/docs/ssl-certificates/google-managed-certs · "To become ACTIVE , the Google-managed SSL certificate must be associated with a load balancer, specifically the load balancer's target proxy." · 2026-10-01 |
| NW.idle_timeout / NW.request_timeout / NW.websocket / NW.protocols / NW.body_size / NW.draining / NW.client_ip / NW.routing / NW.caching / NW.egress / NW.private_connectivity / NW.health_check / NW.scaling | — | 해당 없음 | | — |
| NW.tls | TLS | 공개 Google 관리형 인증서 유효기간 90일(EDGE_CACHE 30일), 변경 불가. 만료 약 1개월 전 자동 갱신 시작, CAA에 허용된 CA 중 선택(갱신 CA가 바뀔 수 있음). **LB 승인**: LB가 완성돼 트래픽을 받아야 발급, 와일드카드·리전 인증서 불가, 도메인을 서비스하는 모든 IP의 443에 인증서가 붙어야 함, CDN 같은 중간 계층은 예측 불가. **DNS 승인**: CNAME 추가로 LB 준비 전 사전 발급 가능, 와일드카드(한 단계) 가능, CNAME이 갱신 권한 — 지우면 갱신 실패. Compute 관리형: A/AAAA가 LB IP를 가리켜야 발급, 최대 60분(DNS 전파 후) | 도메인 100개/인증서(증가 불가), 도메인 길이 64바이트 | https://cloud.google.com/certificate-manager/docs/how-it-works · "The default validity of public Google-managed certificates is 90 days for all scopes except EDGE_CACHE , which has a validity of 30 days." · 2026-10-01; https://cloud.google.com/load-balancing/docs/ssl-certificates/google-managed-certs · "Google Cloud provisions managed certificates valid for 90 days. About one month before expiry, the process to renew your certificate automatically begins." / "To provision SSL certificates, ensure that A and AAAA records point to the load balancer's IP address at a public DNS." / "Provisioning a Google-managed certificate might take up to 60 minutes" · 2026-10-01; https://cloud.google.com/certificate-manager/docs/domain-authorization · "Certificate Manager can only provision certificates after the load balancer has been fully set up and is serving network traffic." / "Certificate Manager can provision certificates in advance, before the target proxy is ready to serve network traffic." / "To revoke these permissions, remove the CNAME record from your DNS configuration." / "Intermediate layers, such as CDN, can cause unpredictable behavior." · 2026-10-01; https://cloud.google.com/certificate-manager/docs/certificates · "Load balancer authorized certificates don't support wildcard domains." · 2026-10-01; https://cloud.google.com/load-balancing/docs/quotas · "Multiple domains per Google-managed SSL certificate 100 This limit cannot be increased." · 2026-10-01 |
| NW.availability | — | 전역(LB 승인·DNS 승인), 리전·교차 리전(DNS 승인·CA Service) | | https://cloud.google.com/certificate-manager/docs/certificates · "Google-managed certificates with load balancer authorization (global) Google-managed certificates with DNS authorization (global, regional, and cross-region)" · 2026-10-01 |
| NW.security | TLS | 갱신마다 새 개인 키. CAA 레코드가 Google 사용 CA를 허용해야 함 | | https://cloud.google.com/certificate-manager/docs/how-it-works · "When a new Google-managed certificate is issued or renewed, Certificate Manager uses a freshly generated private key for the certificate." · 2026-10-01 |
| NW.dns | L7 | LB 승인: A/AAAA가 LB IP를 공개 DNS에서 가리켜야(분할 DNS·DNS 방화벽 방해). DNS 승인: `_acme-challenge` 류 CNAME 영구 유지(per-project 옵션) | | https://cloud.google.com/certificate-manager/docs/domain-authorization · "The target domain must be openly resolvable from the Internet. Split-horizon or DNS firewall environments can interfere with certificate provisioning." · 2026-10-01 |
| NW.regions | — | Certificate Manager 한도: Google 관리형 1000/프로젝트, 리전 관리형 100/리전 | 서울 리전 인증서는 DNS 승인 필요 (추론) | https://cloud.google.com/certificate-manager/docs/quotas · "Google-managed certificates 1000" / "Regional Google-managed certificates 100" · 2026-10-01 ⚠️근거없음 |
| NW.cost_floor | — | Certificate Manager 인증서 100개/월까지 무료, 100~2000개 $0.000273973/시간(≈$0.20/월)·개, 2000+ ≈$0.10. RSA-3072/4096 배포 시 백만 연결당 $0.45(RSA-2048·ECDSA는 무료). Compute 관리형(클래식) 요금은 미확인 | | https://cloud.google.com/certificate-manager/pricing · "Certificate Manager 0 month to 100 month $0.00 (Free)" / "100 month to 2,000 month $0.000273973 / 1 hour" / "There are no per-connection charges for certificates that use RSA-2048, ECDSA P-256, or ECDSA P-384 key types." · 2026-10-01 |

### 비용 구조
- 소규모(인증서 100개 이하)는 0원. RSA 3072/4096 키를 쓰면 연결당 과금.

### 교체 계열 정보
- ACM(4.1)과 달리 DNS 승인 없이도(LB 승인) 발급 가능하지만 와일드카드·리전·사전 발급 불가.
- Cloud Run 도메인 매핑·GKE ManagedCertificate 등은 별도(범위 밖).

### 함정
- LB 승인 인증서는 DNS가 LB IP를 가리키기 전까지 `PROVISIONING`/`FAILED_NOT_VISIBLE` → DNS 전환과 인증서 발급 사이 HTTPS 공백. 무중단 이전(F4)이면 DNS 승인으로 사전 발급.
- 앞단에 Cloudflare 프록시·다른 CDN이 있으면 LB 승인 실패 가능.
- IPv4·IPv6 LB를 따로 두면 둘 다 같은 인증서 필요.
- CAA 레코드에 Google CA(pki.goog) 미포함 시 발급·갱신 실패, 갱신 CA가 바뀔 수 있음.
- 유효기간 90일 → 갱신 시작 약 30일 전.
- Compute 관리형 인증서 도메인 변경 불가 → 새 인증서 만들어 교체.

### 생성 산출물
- Terraform 리소스: `google_certificate_manager_certificate` (https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/certificate_manager_certificate), `google_certificate_manager_dns_authorization`, `google_certificate_manager_certificate_map`, `google_certificate_manager_certificate_map_entry`, 클래식: `google_compute_managed_ssl_certificate` (https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_managed_ssl_certificate)
- 요구에 따라 반드시 명시할 속성:
  - `google_certificate_manager_certificate.managed { domains, dns_authorizations }` → F4(무중단 전환)·와일드카드·리전 LB(서울)일 때 DNS 승인. `location`(기본 global, 서울 리전 LB면 `asia-northeast3`), `scope`(EDGE_CACHE면 30일).
  - `google_certificate_manager_dns_authorization { domain }` → 출력된 CNAME을 `google_dns_record_set`(또는 외부 DNS)로 생성, 영구 유지.
  - `google_compute_managed_ssl_certificate.managed { domains }` → 단순 전역 ALB, DNS 전환 후 발급 대기 허용 시.
- Checkov: Certificate Manager·관리형 SSL 인증서 대상 해당 체크 없음(Policy Index에서 certificate_manager·managed_ssl 검색 결과 없음).
- 배포 후 검증:
  - `gcloud certificate-manager certificates describe <name> --location=global --format="value(managed.state,managed.authorizationAttemptInfo)"` → `ACTIVE`.
  - `gcloud compute ssl-certificates describe <name> --global --format="get(managed.status,managed.domainStatus)"` → `ACTIVE`, 도메인별 `ACTIVE`.
  - `dig +short app.example.com` → LB IP. `dig +short CAA example.com` → 비었거나 `pki.goog` 포함.
  - `openssl s_client -connect app.example.com:443 -servername app.example.com </dev/null 2>/dev/null | openssl x509 -noout -issuer -dates` → Google Trust Services 등, 유효기간 90일.

## 4.3 Let's Encrypt + cert-manager — ACME(쿠버네티스 Ingress/Gateway 등 자체 종단)
- 계열: 네트워크-인증서
- 서울 리전: 해당 없음(외부 CA, 클러스터 위치 무관)

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | TLS | CA(Let's Encrypt) + 클러스터 내 발급·갱신 컨트롤러(cert-manager). 종단은 Ingress 컨트롤러·게이트웨이 | | https://github.com/cert-manager/website/blob/master/content/docs/usage/certificate.md · "cert-manager will automatically renew `Certificate`s." · 2026-10-01 ⚠️출처확인필요 |
| NW.idle_timeout / NW.request_timeout / NW.websocket / NW.protocols / NW.body_size / NW.draining / NW.client_ip / NW.routing / NW.caching / NW.egress / NW.private_connectivity / NW.health_check / NW.availability | — | 해당 없음 | | — |
| NW.tls | TLS | **수명**: `classic`(기본) 90일, `tlsserver` 45일(2026-05-13부터), `shortlived` 160시간(약 6일). 일정: 2027-02-10 classic 64일(승인 재사용 10일), 2028-02-16 classic 45일(승인 재사용 7시간). **cert-manager 갱신 시점**: 기본 수명의 2/3 지점, `renewBefore`(절대값) 또는 `renewBeforePercentage`(권장) 지정 시 그만큼 전. `duration` 기본 90일(발급자가 무시할 수 있음), 최소 1시간, effective renewBefore 최소 5분, `duration > renewBefore`. **만료 알림 이메일 2025-06-04 종료**. **OCSP**: 2025-05-07 인증서에서 OCSP URL 제거, 2025-08-06 OCSP 응답기 종료(CRL로 대체) | Let's Encrypt 권장: ARI 사용, 고정 60일 갱신은 부족, 수명 2/3 지점 갱신 허용 | https://letsencrypt.org/docs/profiles/ · "classic ... Validity Period 90 days" / "tlsserver ... Validity Period 45 days" / "Validity Period 160 hours" · 2026-10-01; https://letsencrypt.org/2025/12/02/from-90-to-45 · "May 13, 2026: Let's Encrypt will switch our tlsserver ACME profile to issue 45-day certificates." / "February 10, 2027: ... issuing 64-day certificates with a 10-day authorization reuse period." / "February 16, 2028: ... issue 45-day certificates with a 7 hour authorization reuse period." / "renewing at a hardcoded interval of 60 days will no longer be sufficient" · 2026-10-01; https://github.com/cert-manager/website/blob/master/content/docs/usage/certificate.md · "By default this will be 2/3 through the X.509 certificate's duration." / "Using `spec.renewBeforePercentage` is recommended to prevent renewal loops" / "minimum value for effective `spec.renewBefore` is 5 minutes" · 2026-10-01; https://letsencrypt.org/2025/01/22/ending-expiration-emails · "We will be ending this service on June 4, 2025." · 2026-10-01; https://letsencrypt.org/2024/12/05/ending-ocsp · "May 7, 2025 ... On this date we will drop OCSP URLs from certificates" / "August 6, 2025 On this date we will turn off our OCSP responders" · 2026-10-01 ⚠️출처확인필요 |
| NW.scaling | — | 레이트 리밋: 등록 도메인당 7일 50개(전역), 동일 식별자 집합 7일 5개, 계정당 3시간 300 주문, 인증서당 식별자 최대 100(classic)/25(tlsserver·shortlived). ARI로 조정된 갱신은 모든 리밋 면제 | 리밋 초과 시 리필 속도로 회복(등록 도메인 202분당 1개) | https://letsencrypt.org/docs/rate-limits/ · "Up to 50 certificates can be issued per registered domain (or IPv4 address, or IPv6 /64 range) every 7 days." / "Up to 5 certificates can be issued per exact same set of identifiers every 7" / "Up to 300 new orders can be created by a single account every 3 hours." / "Renewals coordinated by ARI offer the unique benefit of being exempt from all rate limits." · 2026-10-01 ⚠️출처확인필요 |
| NW.security | TLS | HTTP-01은 포트 80만, 와일드카드 불가. 와일드카드는 DNS-01(TXT) 필요. HTTP-01은 리다이렉트된 HTTPS의 인증서를 검증하지 않음. DNS-PERSIST-01 표준화 진행 중 | | https://letsencrypt.org/docs/challenge-types/ · "The HTTP-01 challenge can only be done on port 80." / "This challenge cannot be used to issue wildcard certificates." · 2026-10-01 ⚠️출처확인필요 |
| NW.dns | L7 | DNS-01: 클러스터가 DNS API(Route 53·Cloud DNS·Cloudflare) 쓰기 권한 필요. 승인 재사용 기간이 30일→7시간으로 줄면 갱신마다 매번 검증 (추론, 일정 근거는 위) | | https://letsencrypt.org/2025/12/02/from-90-to-45 · "We are also reducing the authorization reuse period ... It is currently 30 days, which will be reduced to 7 hours by 2028." · 2026-10-01 ⚠️출처확인필요 ⚠️근거없음 |
| NW.regions | — | 해당 없음 | | — |
| NW.cost_floor | — | 인증서 무료 (cert-manager 오픈소스, 클러스터 자원만) — Let's Encrypt 요금 문서는 확인 안 함 | | 미확인 ⚠️근거없음 |

### 비용 구조
- CA 비용 0(일반적 사실이나 이번에 공식 요금 페이지는 열지 않음 → 미확인). 비용은 cert-manager 실행 자원과 DNS-01용 DNS API 호출.

### 교체 계열 정보
- AWS에서 ALB/CloudFront 종단이면 ACM(무료)이 우선. 클러스터 안 Ingress(Nginx 등)·NLB TCP 패스스루·타 클라우드에서 TLS를 직접 종단할 때 cert-manager.
- ACM ACME 엔드포인트(유료, 45일)도 ACME 클라이언트로 사용 가능 — cert-manager `server`만 바꾸면 (추론). ⚠️근거없음

### 함정
- 만료 알림 메일이 없어졌으므로 자체 모니터링 필수(cert-manager 메트릭/이벤트, 외부 감시).
- 하드코딩 `renewBefore: 720h`(30일)는 45일 인증서에서도 동작하지만 `duration`보다 크면 갱신 루프 → `renewBeforePercentage` 권장. 64일·45일 전환(2027-02, 2028-02)에 대비.
- HTTP-01은 포트 80이 인터넷에서 열려 있어야 함 → ALB/NLB/보안 그룹·Cloudflare 프록시 규칙이 `/.well-known/acme-challenge/`를 막지 않아야 함. 와일드카드·사설 클러스터는 DNS-01.
- 스테이징으로 먼저 시험하지 않으면 동일 집합 7일 5개 리밋에 걸림.
- OCSP Must-Staple 요청은 실패, OCSP 스테이플링을 기대하는 클라이언트/설정 점검.
- shortlived(6일)는 갱신 실패 대응 여유가 매우 짧음.

### 생성 산출물
- Terraform 리소스: 해당 없음(쿠버네티스 매니페스트). Helm으로 cert-manager 설치 시 `helm_release`(선택).
- 매니페스트(필수 필드 원문 확인: https://github.com/cert-manager/website/blob/master/content/docs/configuration/acme/README.md): ⚠️출처확인필요
```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata: { name: letsencrypt-prod }
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: ops@example.com            # 만료 메일은 더 이상 오지 않음
    profile: tlsserver                # 선택: 45일(2026-05-13~). 생략 시 classic
    privateKeySecretRef: { name: letsencrypt-prod-account-key }
    solvers:
      - http01: { ingress: { ingressClassName: nginx } }       # 단일 호스트
      - selector: { dnsZones: ["example.com"] }
        dns01: { route53: { region: ap-northeast-2 } }         # 와일드카드·사설 클러스터
---
apiVersion: cert-manager.io/v1
kind: Certificate
metadata: { name: app-tls, namespace: app }
spec:
  secretName: app-tls
  dnsNames: ["app.example.com"]
  issuerRef: { name: letsencrypt-prod, kind: ClusterIssuer }
  renewBeforePercentage: 33           # 기본 2/3 지점과 동일, 수명 변경에 안전
```
- 요구에 따라 반드시 명시할 속성: `solvers` → 와일드카드·포트 80 미개방·사설이면 `dns01`; `renewBeforePercentage` → 항상(수명 단축 대비); `profile` → 수명 정책 선택; `privateKeySecretRef` → 계정 키 보존.
- Checkov: Terraform 대상 아님, 해당 체크 없음.
- 배포 후 검증:
  - `kubectl get certificate -A` → `READY=True`. `kubectl get certificate app-tls -n app -o jsonpath='{.status.renewalTime}'` → notAfter의 약 2/3 지점.
  - `openssl s_client -connect app.example.com:443 -servername app.example.com </dev/null 2>/dev/null | openssl x509 -noout -issuer -dates -ocsp_uri` → 발급자 Let's Encrypt, 수명 90/45일, OCSP URI 없음.
  - `curl -sI http://app.example.com/.well-known/acme-challenge/test` → 404(경로 도달), 403/연결 거부면 HTTP-01 차단.

---

# 5. 출구 NAT·고정 IP

- 확인일: 모든 출처 2026-10-01 (일부 2026-10-02 재확인). AWS 단가는 Price List 오퍼 파일 `AmazonEC2/current/ap-northeast-2/index.csv`, `AmazonVPC/current/ap-northeast-2/index.json` 을 curl로 받아 읽음(**[PL]**). 월 환산은 730시간.
- 이 계열 공통: 출구 NAT는 **요청 경로의 반대 방향**(앱 → 외부 API·DB·SaaS)에 놓인다. NW.idle_timeout·NW.request_timeout·NW.websocket 등은 "앱이 바깥으로 연 연결"에 대한 값으로 읽는다. 클라이언트 요청 경로 키(NW.caching, NW.tls 종단, NW.client_ip, NW.health_check 등)는 대부분 `해당 없음`.
- 재료(considerations)·초기 가정과 다른 확인 결과(중요): ① AWS NAT 350초 유휴 후 동작은 **RST 반환**이다(조용한 drop 아님). ② Cloud NAT의 엔드포인트 독립 매핑(EIM)은 **기본 비활성**이다. ③ Cloud NAT TCP TIME_WAIT 기본은 생성 시점에 따라 **30초 또는 120초**다.

---

## 5.1 AWS NAT Gateway — 존(zonal) 모드, 퍼블릭 / 프라이빗
- 계열: 네트워크-출구
- 서울 리전: 있음 ([PL] AmazonEC2 ap-northeast-2 `APN2-NatGateway-Hours` 행이 있음)

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L3/L4 | 관리형 SNAT(퍼블릭: 사설 IP → EIP, 프라이빗: 사설 IP → NAT GW 사설 IP). 프록시 아님(연결 종단 안 함). TCP·UDP·ICMP. IPv6는 NAT64 | IPsec 미지원(NAT-T로 UDP 캡슐화는 가능). 보안 그룹 연결 불가, NACL로만 제어 | https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-basics.html · "A NAT gateway supports the following protocols: TCP, UDP, and ICMP." / "You can't associate a security group with a NAT gateway." · 2026-10-01 ; https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-troubleshooting.html · "NAT gateways currently do not support the IPsec protocol." · 2026-10-01 |
| NW.idle_timeout | L4 | **350초 고정**(설정 항목 문서에 없음). 넘으면 연결 만료, 이후 패킷에 **RST 반환**(FIN 아님) | 앱 TCP keepalive < 350초 필요. 지표 `IdleTimeoutCount` | https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-troubleshooting.html · "If a connection that's using a NAT gateway is idle for 350 seconds or more, the connection times out. When a connection times out, a NAT gateway returns an RST packet to any resources behind the NAT gateway that attempt to continue the connection (it does not send a FIN packet)." · 2026-10-01 |
| NW.request_timeout | — | 해당 없음(L7 응답 대기 개념 없음) | — | — |
| NW.websocket | L4 | 외부로 연 장시간 연결(웹소켓 클라이언트, DB, gRPC 스트림)은 350초 유휴 규칙만 적용. 활동이 있으면 지속 | keepalive < 350초 (추론) | https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-troubleshooting.html · "you can enable TCP keepalive on the instance with a value less than 350 seconds." · 2026-10-01 ⚠️근거없음 |
| NW.protocols | L3/L4 | TCP, UDP, ICMP / NAT64(IPv6→IPv4, Route 53 Resolver DNS64와 함께). MTU 8,500(인터넷 쪽은 1,500 권장), PMTUD·MSS 클램핑 | 사용 포트 1024–65535 | https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-basics.html · "For IPv6 traffic, NAT gateway performs NAT64." / "NAT gateways use ports 1024–65535." · 2026-10-01 |
| NW.body_size | — | 해당 없음 | — | — |
| NW.draining | — | 드레이닝 개념 없음. EIP 교체·NAT 교체 시 기존 연결 끊김 (추론) | — | — ⚠️근거없음 |
| NW.health_check | — | 해당 없음(헬스 체크 대상 없음) | — | — |
| NW.tls | — | 해당 없음(TLS 통과) | — | — |
| NW.client_ip | L3 | 외부 목적지가 보는 출발지 = NAT의 EIP(퍼블릭) 또는 NAT의 사설 IP(프라이빗). 내부 원본 IP는 숨겨짐 | 프라이빗 NAT에는 EIP 연결 불가 | https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html · "You can't associate an Elastic IP address with a private NAT gateway." · 2026-10-01 |
| NW.routing | L3 | 사설 서브넷 라우트 테이블 `0.0.0.0/0 → nat-…`, NAT가 있는 퍼블릭 서브넷은 `0.0.0.0/0 → igw-…`. 피어링 너머에서 NAT로 들어오는 경로는 불가 | VGW 경유 VPN/DX → NAT 불가(TGW는 가능) | https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-basics.html · "You can't route traffic to a NAT gateway through a VPC peering connection." · 2026-10-01 |
| NW.scaling | L3/L4 | 대역폭 **5 Gbps → 100 Gbps 자동**, 패킷 **1M pps → 10M pps 자동**(초과 시 drop). **IP 하나당 고유 목적지(목적지 IP+포트+프로토콜)당 동시 연결 55,000**. IP 최대 **8개**(기본 1 + 보조 7) → 고유 목적지당 **440,000**. 퍼블릭 NAT당 EIP 기본 쿼터 **2**(조정 가능) → 기본 상태 최대 110,000. 고갈 시 지표 `ErrorPortAllocation` > 0 | AZ당 NAT 5개(조정 가능). 리전 EIP 5개(조정 가능) | https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-basics.html · "Each IPv4 address can support up to 55,000 simultaneous connections to each unique destination." / "associating up to 8 IPv4 addresses to your NAT gateways (1 primary IPv4 address and 7 secondary IPv4 addresses). You are limited to associating 2 Elastic IP addresses to your public NAT gateway by default." / "A NAT gateway supports 5 Gbps of bandwidth and automatically scales up to 100 Gbps." · 2026-10-01 ; https://docs.aws.amazon.com/vpc/latest/userguide/amazon-vpc-limits.html · "Elastic IP addresses per public NAT gateway 2 Yes" / "NAT gateways per Availability Zone 5 Yes" · 2026-10-01 ; https://docs.aws.amazon.com/vpc/latest/userguide/metrics-dimensions-nat-gateway.html · "ErrorPortAllocation The number of times the NAT gateway could not allocate a source port. A value greater than zero indicates that too many concurrent connections are open through the NAT gateway." · 2026-10-01 |
| NW.availability | L3 | **존 범위**: 한 AZ 안에서만 이중화. 그 AZ가 죽으면 다른 AZ 리소스도 인터넷을 잃음 → AZ마다 NAT + AZ별 라우트 필요 | SLA 수치 미확인 | https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-basics.html · "if the NAT gateway's Availability Zone is down, resources in the other Availability Zones lose internet access." · 2026-10-01 |
| NW.caching | — | 해당 없음 | — | — |
| NW.security | L3/L4 | 인바운드 요청 시작 불가(응답만 통과). SG 불가, NACL만 | — | https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html · "the instances can't receive unsolicited inbound connections from the internet." · 2026-10-01 |
| NW.dns | — | 해당 없음(NAT64 사용 시 Route 53 Resolver DNS64 별도 활성) | — | https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-basics.html · "By using this in conjunction with DNS64 (available on Route 53 resolver)" · 2026-10-01 |
| NW.egress | L3/L4 | **고정 출구 IP = 연결한 EIP**(퍼블릭). 포트 판정식: `동일 (목적지 IP, 포트, 프로토콜)로 동시 연결 수 ≤ 55,000 × NAT의 IP 수(≤8, 기본 EIP 쿼터 2)`. 처리 요금 **$0.059/GB**(서울, 출처·목적지 무관) + 데이터 전송 요금 별도 | 다른 목적지끼리는 한도 공유 안 함. 프라이빗 NAT는 사설 IP로 SNAT(온프레미스 허용 목록용) | https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-basics.html · "A unique destination is identified by a unique combination of destination IP address, the destination port, and protocol (TCP/UDP/ICMP)." · 2026-10-01 ; https://aws.amazon.com/vpc/pricing/ · "Data processing charges apply for each gigabyte processed through the NAT gateway regardless of the traffic's source or destination." · 2026-10-01 |
| NW.private_connectivity | L3 | 프라이빗 NAT(`connectivity_type=private`): 다른 VPC·온프레미스(TGW/VGW 경유)로 허용 목록 IP 대역에서 SNAT. S3·DynamoDB 등 AWS 서비스 트래픽은 게이트웨이/인터페이스 엔드포인트로 NAT 처리 요금 회피 | — | https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-scenarios.html · "You can use a private NAT gateway to enable communication from your VPCs to your on-premises network using a pool of allow-listed addresses." · 2026-10-01 ; https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-pricing.html · "consider creating an interface endpoint or gateway endpoint for these services." · 2026-10-01 |
| NW.regions | — | 서울 있음 | — | [PL] AmazonEC2 ap-northeast-2 · usagetype `APN2-NatGateway-Hours` "$0.059 per NAT Gateway Hour" · 2026-10-01 |
| NW.cost_floor | — | 서울 **$0.059/시간(월 $43.07)/NAT** + **$0.059/GB 처리** + EIP $0.005/시간(월 $3.65/개). AZ 2개 HA = 월 약 **$93.4**(+처리·전송) | 프라이빗 NAT 단가는 오퍼 파일에 별도 행 없음(같은 usagetype 사용 추정, 미확인) | [PL] AmazonEC2 ap-northeast-2 · `APN2-NatGateway-Hours` "$0.059 per NAT Gateway Hour" 0.059 / `APN2-NatGateway-Bytes` "$0.059 per GB Data Processed by NAT Gateways" 0.059 · 2026-10-01 |

### 비용 구조
- 시간 요금(NAT 1개 = AZ 1개) + GB 처리 요금(들어오고 나가는 양방향 모두) + EIP 시간 요금 + 일반 데이터 전송(인터넷 아웃) 요금.
- 예: AZ 2개, 월 100 GB 처리 → 2 × $43.07 + 100 × $0.059 + 2 × $3.65 = 약 $99.3 + 인터넷 아웃 전송료 (추론, 계산). ⚠️근거없음
- 같은 AZ의 NAT를 쓰지 않으면 AZ 간 전송료가 더 붙음(문서 권고).

### 교체 계열 정보
- 같은 계열: 5.2 리전 NAT(AZ 자동 확장, IP 32개/AZ), 5.3 NAT 인스턴스(저비용, 단일 장애점), IPv6 + egress-only IGW(무료, 5.6).
- 출구가 AWS 서비스(S3, ECR, Secrets Manager 등) 위주면 VPC 엔드포인트로 대체 → NAT 처리 요금 감소.

### 함정
- **AZ 하나에 NAT 하나만 두고 모든 AZ 라우트를 거기로 보내면** 그 AZ 장애 시 전체 출구 단절(F1 위반).
- **350초 유휴 후 RST**: DB·외부 API 풀 연결이 조용하면 다음 요청에서 `ECONNRESET`. 풀의 idle timeout < 350초 또는 TCP keepalive < 350초.
- **포트 고갈은 "같은 목적지"에 대한 한도**: LLM·결제 API처럼 IP 하나(또는 소수) 뒤에 있는 외부 API로 대량 동시 연결 시 55,000 × IP 수 초과 → `ErrorPortAllocation`. 기본 EIP 쿼터 2이므로 8까지 쓰려면 쿼터 상향 필요.
- 1M pps 초과 시 자동 확장 전 drop 가능(문서: "Beyond this limit, a NAT gateway will drop packets").
- EIP를 NAT에서 떼면 유휴 EIP로 계속 과금($0.005/시간).

### 생성 산출물
- Terraform 리소스: `aws_nat_gateway` (https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/nat_gateway, 원문 https://github.com/hashicorp/terraform-provider-aws/blob/main/website/docs/r/nat_gateway.html.markdown), `aws_eip` (`domain = "vpc"`), `aws_route`(`nat_gateway_id`), `aws_route_table`, `aws_internet_gateway`, `aws_subnet`.
- 요구에 따라 반드시 명시할 속성:
  - `availability_mode = "zonal"`(기본) + `subnet_id`(퍼블릭 서브넷) + `allocation_id`(EIP) — E1/E3(외부 API가 IP 허용 목록 요구) 시 EIP 필수, 그 EIP 값을 출력(`output`)으로 노출.
  - F1 = 짧아야 함/거의 0 → AZ 수만큼 `aws_nat_gateway` + AZ별 `aws_route_table`(각 사설 서브넷 → 같은 AZ NAT). F1 = 길어도 됨 + G3 = 높음 → NAT 1개 허용.
  - D2/D3 높음 + 단일 외부 목적지 대량 호출 → `secondary_allocation_ids`(EIP 추가, 최대 7) 및 EIP 쿼터 상향 요청.
  - 온프레미스/타 VPC 허용 목록(사설) → `connectivity_type = "private"`, `secondary_private_ip_address_count`.
- Checkov:
  - `CKV2_AWS_19` "Ensure that all EIP addresses allocated to a VPC are attached to EC2 instances" (`aws_eip`; 소스 yaml에서 `aws_nat_gateway`와 연결된 EIP도 통과 처리 확인: https://github.com/bridgecrewio/checkov/blob/main/checkov/terraform/checks/graph_checks/aws/EIPAllocatedToVPCAttachedEC2.yaml) ⚠️출처확인필요
  - `CKV2_AWS_35` "AWS NAT Gateways should be utilized for the default route" (`aws_route`/`aws_route_table`에 `instance_id`로 기본 경로를 보내면 실패 = NAT 인스턴스 사용 탐지)
  - `CKV_AWS_130` "Ensure VPC subnets do not assign public IP by default" (`aws_subnet`, 사설 서브넷 설계와 연관)
  - NAT Gateway 자체(로깅·다중 AZ) 전용 체크: 해당 체크 없음(정책 인덱스에서 `aws_nat_gateway` 로 걸리는 행은 제목 불일치 항목뿐).
- 배포 후 검증:
  - 컨테이너/함수 안에서 `curl -s https://checkip.amazonaws.com` 또는 `curl -s https://ifconfig.me` → 기대값: `aws ec2 describe-nat-gateways --nat-gateway-ids nat-… --query 'NatGateways[].NatGatewayAddresses[].PublicIp'` 결과 중 하나와 같음.
  - `aws ec2 describe-route-tables --filters Name=association.subnet-id,Values=<사설서브넷> --query 'RouteTables[].Routes[?DestinationCidrBlock==\`0.0.0.0/0\`].NatGatewayId'` → 같은 AZ NAT ID.
  - `aws cloudwatch get-metric-statistics --namespace AWS/NATGateway --metric-name ErrorPortAllocation --dimensions Name=NatGatewayId,Value=nat-… --statistics Sum --period 300 --start-time … --end-time …` → 기대값 0. `PacketsDropCount`, `IdleTimeoutCount`도 확인.

---

## 5.2 AWS NAT Gateway — 리전(regional) 모드 (2025 신규)
- 계열: 네트워크-출구
- 서울 리전: 있음 ([PL] `APN2-RegionalNatGateway-Hours`, "Hourly charge for Regional NAT Gateways" 행 존재). 단 "constrained AZ"에서는 미지원.

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L3/L4 | 관리형 SNAT, NAT ID 하나로 여러 AZ. 퍼블릭 서브넷 불필요(자체 라우트 테이블 자동 생성) | **퍼블릭만**(private NAT 미지원) | https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateways-regional.html · "A regional NAT gateway automatically expands across Availability Zones based on your workload presence." / "Regional NAT gateways do not support private NAT." · 2026-10-01 |
| NW.idle_timeout | L4 | 리전 모드 별도 값 문서 없음 → 존 모드와 같은 350초로 추정 | 미확인(리전 모드 명시 없음) | https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-troubleshooting.html · "idle for 350 seconds or more, the connection times out" · 2026-10-01 (추론: 공통 적용) ⚠️근거없음 |
| NW.request_timeout | — | 해당 없음 | — | — |
| NW.websocket | L4 | 5.1과 같음(추론) | — | — ⚠️근거없음 |
| NW.protocols | L3/L4 | 미확인(리전 모드 문서에 프로토콜 별도 기재 없음, 존 모드와 같다고 추정) | — | 미확인 |
| NW.body_size | — | 해당 없음 | — | — |
| NW.draining | — | 존 → 리전 전환 시 **기존 연결 리셋**, 유지보수 창 권장 | — | https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateways-regional.html · "This will reset your existing connections." · 2026-10-01 |
| NW.health_check | — | 해당 없음 | — | — |
| NW.tls | — | 해당 없음 | — | — |
| NW.client_ip | L3 | 출발지 = AZ별 EIP. 자동 모드는 AWS가 EIP를 고르고 **필요 시 추가 할당**(autoScalingIps) → 출구 IP 집합이 늘어날 수 있음 | 허용 목록이 필요하면 수동 모드 또는 IPAM 정책 | https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_NatGateway.html · "autoScalingIps For regional NAT gateways only: Indicates whether AWS automatically allocates additional Elastic IP addresses (EIPs) in an AZ when the NAT gateway needs more ports" · 2026-10-01 |
| NW.routing | L3 | 모든 AZ 사설 서브넷이 같은 NAT ID로 라우트. 자동 생성 라우트 테이블에 IGW 경로 포함. TGW를 라우트 대상으로 지원 | — | https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateways-regional.html · "Use a single NAT ID across all Availability Zones that have network interfaces" · 2026-10-01 |
| NW.scaling | L3/L4 | **AZ당 IP 최대 32개**(존 모드 8), IP당 고유 목적지 동시 연결 55,000 → AZ당 최대 1,760,000. 새 AZ로 확장에 **최대 60분**, 그동안 다른 AZ에서 교차 처리 | 대역폭·pps 수치 리전 모드 별도 명시 없음 | https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateways-regional.html · "Your regional NAT Gateways support up to 32 IP addresses per Availability Zone (compared to 8 for zonal NAT gateways). Each IP address increases the limit on concurrent connections to a popular destination ... by 55,000." / "It may take your regional NAT Gateway up to 60 minutes to expand to a new Availability Zone" · 2026-10-01 |
| NW.availability | L3 | **리전(다중 AZ) 기본 HA**: 워크로드 ENI가 있는 AZ로 자동 확장·축소(자동 모드). 수동 모드는 AZ 확장 직접 관리 | constrained AZ 미지원 | https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateways-regional.html · "Automatically expands and contracts with your workload footprint to maintain zonal affinity which provides high availability by default." · 2026-10-01 |
| NW.caching | — | 해당 없음 | — | — |
| NW.security | L3 | 퍼블릭 서브넷이 필요 없어 사설 리소스 오구성 위험 감소 | — | https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateways-regional.html · "Enhanced security – No public subnets required." · 2026-10-01 |
| NW.dns | — | 해당 없음 | — | — |
| NW.egress | L3/L4 | 포트 판정식: `AZ별 동일 목적지 동시 연결 ≤ 55,000 × 그 AZ의 IP 수(≤32)`. 자동 모드에서는 IP 자동 추가. 고정 IP 허용 목록: **수동 모드**(AZ별 `allocation_ids`)로 IP 집합 고정 | 처리 요금 $0.059/GB(서울) | [PL] AmazonEC2 ap-northeast-2 · usagetype `APN2-RegionalNatGateway-Bytes` "Charge for per GB data processed by NAT Gateways" 0.059 · 2026-10-01 |
| NW.private_connectivity | — | private NAT 미지원 → 사설 허용 목록 용도는 5.1 존 모드 사용 | — | https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateways-regional.html · "we recommend using your NAT Gateways in zonal availability mode for private NAT use cases." · 2026-10-01 |
| NW.regions | — | 서울 있음 | constrained AZ 제외 | [PL] `APN2-RegionalNatGateway-Hours` "Hourly charge for Regional NAT Gateways" · 2026-10-01 |
| NW.cost_floor | — | **AZ당** $0.059/시간 과금(서울) → 활성 AZ 2개 = 월 $86.14, 3개 = 월 $129.21 + $0.059/GB + EIP $3.65/개·월 | 과금 = 구성된 AZ 수 × 시간 | [PL] `APN2-RegionalNatGateway-Hours` 0.0590000000 · 2026-10-01 ; https://aws.amazon.com/vpc/pricing/ · "you are charged for each hour that the NAT Gateway is configured in each availability zone." · 2026-10-01 |

### 비용 구조
- 존 모드 NAT를 AZ마다 둔 것과 시간 요금은 같다(AZ 수 × $0.059). 퍼블릭 서브넷·라우트 관리 비용이 줄어드는 대신 **자동 IP 추가 시 EIP 요금 증가**(추론). ⚠️근거없음

### 교체 계열 정보
- 5.1 존 모드(프라이빗 NAT 필요, constrained AZ, 출구 IP를 엄격히 고정해야 할 때), 5.3 NAT 인스턴스.

### 함정
- **자동 모드 + 외부 IP 허용 목록 = 위험**: AZ 확장·포트 부족 시 EIP가 추가되어 허용 목록 밖 IP로 나갈 수 있음(autoScalingIps). 허용 목록 요구(E1·F5)면 수동 모드 필수 (추론, 근거: API 문서 autoScalingIps). ⚠️근거없음
- 새 AZ로 확장까지 최대 60분 동안 교차 AZ 처리 → AZ 간 전송료·지연 (추론). ⚠️근거없음
- Terraform: `availability_zone_address` 블록을 추가/제거하면 **리소스 재생성**(연결 끊김).
- 존 → 리전 전환 시 기존 IP를 쓰려면 존 NAT를 먼저 삭제해야 함 → 다운타임.

### 생성 산출물
- Terraform 리소스: `aws_nat_gateway` (https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/nat_gateway), `aws_eip`, `aws_route`.
- 요구에 따라 반드시 명시할 속성(원문 확인):
  - `availability_mode = "regional"`, `vpc_id`(필수), `connectivity_type`은 `public`만 허용. `subnet_id`·`allocation_id`·`secondary_allocation_ids`는 **설정 불가**.
  - 고정 출구 IP 허용 목록(E1/E3/F5) → `availability_zone_address { allocation_ids = [...] ; availability_zone = "ap-northeast-2a" }` 를 AZ마다(수동 모드). 생략하면 자동 모드.
  - 읽기 전용 속성: `auto_provision_zones`, `auto_scaling_ips`, `regional_nat_gateway_address`, `route_table_id`.
  - 사설 서브넷 라우트: `aws_route { destination_cidr_block = "0.0.0.0/0", nat_gateway_id = aws_nat_gateway.x.id }` 하나를 모든 AZ 라우트 테이블에.
- Checkov: `CKV2_AWS_19`(EIP 연결 — 리전 모드 `availability_zone_address.allocation_ids` 참조를 그래프 연결로 인식하는지 미확인), `CKV2_AWS_35`. 리전 모드 전용 체크: 해당 체크 없음.
- 배포 후 검증:
  - `aws ec2 describe-nat-gateways --nat-gateway-ids nat-… --query 'NatGateways[].[AvailabilityMode,AutoScalingIps,AutoProvisionZones]'` → 허용 목록 요구 시 `regional, disabled, disabled` 기대(수동 모드).
  - 각 AZ의 태스크에서 `curl -s https://checkip.amazonaws.com` → 해당 AZ에 지정한 EIP 중 하나.
  - CloudWatch `ErrorPortAllocation` Sum = 0.

---

## 5.3 NAT 인스턴스 (요약)
- 계열: 네트워크-출구
- 서울 리전: 있음(EC2 일반 인스턴스, 예 t4g.nano [PL])

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L3/L4 | EC2 위 iptables MASQUERADE 등 직접 구성 SNAT. AWS 제공 NAT AMI(Amazon Linux 2018.03 기반)는 **지원 종료** → 현재 Amazon Linux로 직접 AMI 생성 | 소스/대상 확인(source/dest check) **비활성 필수** | https://docs.aws.amazon.com/vpc/latest/userguide/VPC_NAT_Instance.html · "NAT AMI is built on the last version of the Amazon Linux AMI, 2018.03, which reached the end of standard support on December 31, 2020 and end of maintenance support on December 31, 2023." · 2026-10-01 ; https://docs.aws.amazon.com/vpc/latest/userguide/work-with-nat-instances.html · "you must disable source/destination checks on the NAT instance." · 2026-10-01 |
| NW.idle_timeout | L4 | OS conntrack 설정에 따름 | 미확인 | — |
| NW.scaling | L3/L4 | 인스턴스 크기의 네트워크 성능 한도(t4g.nano "Up to 5 Gigabit"), 포트는 OS 설정 | 자동 확장 없음 | [PL] AmazonEC2 ap-northeast-2 t4g.nano "Network Performance: Up to 5 Gigabit" · 2026-10-01 |
| NW.availability | L3 | **단일 장애점**(인스턴스 1대). AWS는 NAT 게이트웨이로 이전 권고 | ASG·스크립트로 직접 이중화 | https://docs.aws.amazon.com/vpc/latest/userguide/VPC_NAT_Instance.html · "AWS recommends that you migrate to a NAT gateway . NAT gateways provide better availability, higher bandwidth, and requires less administrative effort." · 2026-10-01 |
| NW.egress | L3/L4 | 출구 IP = 인스턴스의 퍼블릭 IP 또는 EIP. 처리 요금 없음(인스턴스·IPv4·전송료만) | 퍼블릭 서브넷 + 퍼블릭 IP 필수 | https://docs.aws.amazon.com/vpc/latest/userguide/VPC_NAT_Instance.html · "it must be in a public subnet ... and it must have a public IP address or an Elastic IP address." · 2026-10-01 |
| NW.security | L3/L4 | 보안 그룹 연결 가능(NAT GW와 달리) | OS 패치 직접 | https://docs.aws.amazon.com/vpc/latest/userguide/work-with-nat-instances.html · "Create a security group for the NAT instance" · 2026-10-01 |
| NW.regions | — | 서울 있음 | — | [PL] `APN2-BoxUsage:t4g.nano` · 2026-10-01 |
| NW.cost_floor | — | t4g.nano **$0.0052/시간(월 $3.80)** + 퍼블릭 IPv4 $3.65 + EBS(미산정) ≈ 월 **$7.5~** | GB 처리 요금 없음 | [PL] AmazonEC2 ap-northeast-2 · "$0.0052 per On Demand Linux t4g.nano Instance Hour" · 2026-10-01 |
| NW.request_timeout, NW.websocket, NW.protocols, NW.body_size, NW.draining, NW.health_check, NW.tls, NW.client_ip, NW.routing, NW.caching, NW.dns, NW.private_connectivity | — | 해당 없음 또는 OS 구성에 따름(미확인) | — | — |

### 비용 구조
- 시간 요금 = 인스턴스 + IPv4. NAT GW 대비 월 약 $35~40 절감(AZ당), 처리 요금 없음 (추론, 계산). ⚠️근거없음

### 교체 계열 정보
- 5.1/5.2 NAT GW(관리형, HA). 비용 최우선(G3 높음) + F1 길어도 됨일 때만 후보.

### 함정
- source/dest check 비활성 누락 → 트래픽 전달 안 됨.
- 인스턴스 재시작·교체 시 퍼블릭 IP(EIP 아니면) 변경 → 허용 목록 깨짐.
- Checkov `CKV2_AWS_35`가 `aws_route.instance_id`로 기본 경로를 보내는 구성을 실패 처리.

### 생성 산출물
- Terraform 리소스: `aws_instance`(`source_dest_check = false`), `aws_eip`(`instance`), `aws_route`(`network_interface_id`), `aws_security_group`.
- Checkov: `CKV2_AWS_35` "AWS NAT Gateways should be utilized for the default route"(실패 예상, 의도적이면 skip 주석), `CKV_AWS_88` "EC2 instance should not have public IP."(NAT 인스턴스는 의도적 위반).
- 배포 후 검증: `aws ec2 describe-instances --instance-ids i-… --query 'Reservations[].Instances[].SourceDestCheck'` → `false`; 사설 서브넷 워크로드에서 `curl -s https://checkip.amazonaws.com` → NAT 인스턴스 EIP.

---

## 5.4 Google Cloud NAT — Public NAT
- 계열: 네트워크-출구
- 서울 리전: 있음(리전 리소스, Cloud Router에 구성. 단가는 리전 공통 — 처리 요금 "same across all regions")

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L3/L4 | 분산 소프트웨어 정의 NAT(Andromeda). **프록시 VM·경로상 장비 아님**, Cloud Router가 제어면. Port Restricted Cone NAT, 엔드포인트 의존 필터링 | IP 조각(fragments) 미지원 | https://docs.cloud.google.com/nat/docs/overview · "Cloud NAT is a distributed, software-defined managed service. It's not based on proxy VMs or appliances." · 2026-10-01 ; https://docs.cloud.google.com/nat/docs/set-up-manage-network-address-translation · "Cloud NAT doesn't support IP fragments." · 2026-10-01 |
| NW.idle_timeout | L4 | 기본값: **TCP established 1,200초**, **TCP transitory 30초**, **UDP 30초**, ICMP 30초, **TCP TIME_WAIT 30초 또는 120초**(게이트웨이 생성 시점에 따라). 모두 변경 가능 | TIME_WAIT ≥ 15초 권장. 실제 값은 `effectiveTcpTimeWaitTimeoutSec`로 확인. [충돌] Terraform 문서는 TIME_WAIT "Defaults to 120s if not set" | https://docs.cloud.google.com/nat/docs/tune-nat-configuration · "1200 seconds (20 minutes)" / "UDP Mapping Idle Timeout ... 30 seconds" / "TCP TIME_WAIT Timeout ... 30 or 120 seconds" · 2026-10-01 ; https://github.com/hashicorp/terraform-provider-google/blob/main/website/docs/r/compute_router_nat.html.markdown · "Timeout (in seconds) for TCP connections that are in TIME_WAIT state. Defaults to 120s if not set." · 2026-10-01 |
| NW.request_timeout | — | 해당 없음 | — | — |
| NW.websocket | L4 | 외부로 연 장시간 연결은 established 유휴 1,200초 규칙. keepalive 권장 | — | https://docs.cloud.google.com/nat/docs/troubleshooting · "Use keepalive mechanisms in your application so that long-running connections can stay open for a longer period." · 2026-10-01 |
| NW.protocols | L3/L4 | TCP·UDP·ICMP. NAT44, NAT64(**Compute Engine VM만**; GKE 노드·서버리스는 IPv4만) | — | https://docs.cloud.google.com/nat/docs/public-nat · "NAT64 is available for Compute Engine VM instances. For Google Kubernetes Engine (GKE) nodes, serverless endpoints, and regional internet network endpoint groups, Cloud NAT translates only IPv4 addresses." · 2026-10-01 |
| NW.body_size | — | 해당 없음 | — | — |
| NW.draining | L3 | 수동 IP는 **drain** 가능(새 연결만 중단). 정적 포트 할당에서 min 포트 축소, DPA→정적 전환, 할당 방식(자동↔수동) 전환은 **기존 연결 즉시 끊김** | `drain_nat_ips` | https://docs.cloud.google.com/nat/docs/ports-and-addresses · "Draining instructs the Public NAT gateway to stop using the NAT IP address for new connections, but continue using it for established connections." / "Switching the assignment method is disruptive, and it breaks all active NAT connections." · 2026-10-01 |
| NW.health_check | — | 해당 없음 | — | — |
| NW.tls | — | 해당 없음 | — | — |
| NW.client_ip | L3 | 외부가 보는 출발지 = NAT IP. 수동(MANUAL_ONLY)이면 예약한 고정 IP 집합, 자동(AUTO_ONLY)이면 **다음 IP 예측 불가** | 허용 목록이면 수동 필수 | https://docs.cloud.google.com/nat/docs/ports-and-addresses · "With automatic allocation, you cannot predict the next IP address that is allocated. If you depend on knowing the set of possible NAT IP addresses ahead of time (for example, to create an allowlist), you should use manual NAT IP address assignment instead." · 2026-10-01 |
| NW.routing | L3 | VPC·리전 단위. 서브넷 범위 선택(`ALL_SUBNETWORKS_ALL_IP_RANGES` / `LIST_OF_SUBNETWORKS`). NAT 규칙(rules)로 목적지별 IP 선택 | EIM 켜면 DPA·NAT 규칙 불가 | https://docs.cloud.google.com/nat/docs/set-up-manage-network-address-translation · "If endpoint-independent mapping (EIM) is enabled, you can't configure dynamic port allocation or NAT rules." · 2026-10-01 |
| NW.scaling | L4 | **NAT IP당 TCP 64,512 + UDP 64,512 포트**(1–1023 미사용). **정적 할당**(Public 기본): VM당 `min_ports_per_vm` 기본 **64**(콘솔 2–57,344), 2의 거듭제곱 단위로 올림. **동적 할당(DPA)**: min 기본 **32**(32–32,768), max 기본 **65,536**(64–65,536), 거의 고갈 시 2배씩 증가. 수용 VM 수 = ⌊NAT IP 수 × 64,512 / VM당 포트⌋ (예: IP 1개·64포트 → 1,008 VM). 게이트웨이당 NAT IP 최대 수동 300 / 자동 2,500 | VM당 동시 연결(같은 목적지 3-튜플) ≤ 할당 포트 수. 닫힌 연결은 TIME_WAIT 동안 재사용 불가 | https://docs.cloud.google.com/nat/docs/ports-and-addresses · "Each NAT IP address on a Cloud NAT gateway (both Public NAT and Private NAT) offers 64,512 TCP source ports and 64,512 UDP source ports." / "the default value is used: 64 for static port allocation and 32 for dynamic port allocation." / "⌊(1 NAT IP address) × (64,512 ports per address) / (64 ports per VM)⌋ = 1,008 VMs" · 2026-10-01 ; https://docs.cloud.google.com/nat/docs/tune-nat-configuration · "MAX_PORTS must be a power of 2 , and can be between 64 and 65536" · 2026-10-01 ; https://docs.cloud.google.com/nat/quota · "NAT IP addresses per gateway 300 manual addresses 2,500 auto-allocated addresses" · 2026-10-01 |
| NW.availability | L3 | 리전 리소스, 특정 VM·물리 장비에 의존하지 않음(존 장애 영향 범위 명시 없음). SLA 미확인 | — | https://docs.cloud.google.com/nat/docs/overview · "It doesn't depend on any VMs in your project or a single physical gateway device." · 2026-10-01 |
| NW.caching | — | 해당 없음 | — | — |
| NW.security | L3/L4 | 요청 없는 인바운드 차단(엔드포인트 의존 필터링). 소스 포트 무작위화는 범위 내 순차 → 보안 수단으로 의존 금지 | — | https://docs.cloud.google.com/nat/docs/public-nat · "Endpoint-Dependent Filtering means that response packets from the internet are allowed to enter only if they are from an IP address and port that a VM had already sent packets to." · 2026-10-01 |
| NW.dns | — | 해당 없음(NAT64 시 DNS64 별도) | — | https://docs.cloud.google.com/nat/docs/public-nat · "You can configure DNS64 to automatically synthesize IPv4-embedded IPv6 addresses" · 2026-10-01 |
| NW.egress | L4 | 포트 판정식: **VM(또는 Cloud Run 인스턴스)당 같은 목적지(IP, 포트, 프로토콜) 동시 연결 ≤ 할당 포트 수**(정적 = `min_ports_per_vm`를 2의 거듭제곱으로 올린 값, DPA = 최대 `max_ports_per_vm`). 필요 NAT IP 수 ≥ ⌈인스턴스 수 × VM당 포트 / 64,512⌉. 고갈 시 **패킷 drop**, 지표 `dropped_sent_packets_count{reason=OUT_OF_RESOURCES}`, `nat_allocation_failed`. **EIM은 기본 비활성**(켜면 `ENDPOINT_INDEPENDENCE_CONFLICT` drop 가능) | 로깅 기본 꺼짐. 고부하 시 로그 throttle | https://docs.cloud.google.com/nat/docs/ports-and-addresses · "The number of NAT source IP address and source port tuples that a Cloud NAT gateway reserves for a VM restricts the number of connections that the VM can make to a unique destination" / "If your gateway runs out of NAT IP addresses, Public NAT drops packets." · 2026-10-01 ; https://docs.cloud.google.com/nat/docs/public-nat · "By default, endpoint-independent mapping is disabled when you create a NAT gateway." · 2026-10-01 ; https://docs.cloud.google.com/nat/docs/monitoring · "OUT_OF_RESOURCES , if Cloud NAT runs out of NAT IP addresses or ports." · 2026-10-01 |
| NW.private_connectivity | L3 | Private NAT(`type=PRIVATE`, NCC·Interconnect·VPN 대상, DPA 기본, 포트 2배 할당). Cloud Run Direct VPC egress·Serverless VPC Access 커넥터 트래픽도 NAT 가능 | Direct VPC: `--vpc-egress=all-traffic`, `endpoint_types=ENDPOINT_TYPE_VM` | https://docs.cloud.google.com/nat/docs/nat-product-interactions · "Cloud NAT gateways can provide NAT for Cloud Run resources that are configured with Direct VPC egress ." · 2026-10-01 |
| NW.regions | — | 서울(asia-northeast3) 있음. 단가 리전 공통 | — | https://cloud.google.com/nat/pricing · "The data processing price is the same across all regions." · 2026-10-01 |
| NW.cost_floor | — | 게이트웨이 **$0.0014 × 사용 VM 수/시간(32대 이상은 $0.044/시간 상한)** + **처리 $0.045/GiB**(인·아웃 모두) + NAT IP **$0.005/시간/개** + 일반 전송료. VM 1대 + IP 1개 ≈ 월 **$4.67**, 상한 도달 + IP 1개 ≈ 월 $35.8 | Cloud Run 인스턴스도 "사용 VM"으로 세는지 미확인(추론: 할당받는 엔드포인트로 계산) | https://cloud.google.com/nat/pricing · "Up to 32 VM instances $0.0014 * the number of VM instances that are using the gateway $0.045 $0.005 More than 32 VM instances $0.044 $0.045 $0.005" · 2026-10-01 ⚠️근거없음 |

### 비용 구조
- 시간 요금(사용 VM 수 비례, 상한 $0.044) + GiB 처리 요금 + NAT IP 시간 요금 + 인터넷 전송료. AWS NAT(AZ당 월 $43)보다 소규모에서 훨씬 쌈 (추론, 계산). ⚠️근거없음

### 교체 계열 정보
- 외부 IP를 VM에 직접(포트 제약 없음, IP당 $0.005/시간). Secure Web Proxy(`ENDPOINT_TYPE_SWG`)는 범위 밖. IPv6-only VM + NAT64.

### 함정
- **정적 할당 기본 64포트**: 한 인스턴스가 같은 외부 API(같은 IP:443)로 동시 64개 넘게 열면 drop. 커넥션 풀·HTTP keep-alive 없는 앱, LLM 스트리밍 다수 호출 시 바로 걸림. TIME_WAIT 동안 포트 재사용 불가가 실효 한도를 더 낮춤.
- **Cloud Run Direct VPC egress**: `min_ports_per_vm`를 Cloud Run 인스턴스 하나에 필요한 포트의 **2배**로 설정(문서 요구). 수동 IP 수는 VM 수 + Cloud Run 인스턴스 수 합계를 감당해야 함 → max-instances가 크면 IP 부족.
- 자동 IP(AUTO_ONLY) → 수동 전환 시 **IP 보존 불가** + 연결 전부 끊김. 허용 목록 요구가 있으면 처음부터 MANUAL_ONLY.
- 정적 포트에서 `min_ports_per_vm` 줄이기 = 즉시 연결 끊김. DPA에서 `max_ports_per_vm` 줄이기 = 즉시 연결 끊김.
- DPA는 포트가 2배로 늘어나는 동안 drop·지연 가능.
- Cloud Run 커넥터 경로: NAT 포트는 커넥터 인스턴스(VM) 단위로 할당되는 것으로 보임(추론; 문서는 Direct VPC 경우만 명시). 커넥터 인스턴스 수가 적으면 포트 병목. ⚠️근거없음

### 생성 산출물
- Terraform 리소스: `google_compute_router` (https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_router), `google_compute_router_nat` (https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_router_nat, 원문 https://github.com/hashicorp/terraform-provider-google/blob/main/website/docs/r/compute_router_nat.html.markdown), `google_compute_address`(region 지정, 외부).
- 요구에 따라 반드시 명시할 속성:
  - E1/E3/F5(외부 허용 목록) → `nat_ip_allocate_option = "MANUAL_ONLY"`, `nat_ips = [google_compute_address.x.self_link]`(주소에 `lifecycle { create_before_destroy = true }` 문서 권고). 아니면 `AUTO_ONLY`.
  - 서브넷 한정 → `source_subnetwork_ip_ranges_to_nat = "LIST_OF_SUBNETWORKS"` + `subnetwork { name, source_ip_ranges_to_nat = ["ALL_IP_RANGES"] }`.
  - D2/D3 높음 또는 외부 API 동시 호출 많음 → `enable_dynamic_port_allocation = true`, `min_ports_per_vm`(2의 거듭제곱 ≥32), `max_ports_per_vm`(≤65536); 이 경우 `enable_endpoint_independent_mapping = false`(상호 배타). 정적이면 `min_ports_per_vm` = 인스턴스당 동시 목적지별 연결 최댓값 이상(Cloud Run Direct VPC는 ×2).
  - A3(장시간 외부 연결) → `tcp_established_idle_timeout_sec`(기본 1200), 빠른 재연결 많음 → `tcp_time_wait_timeout_sec`(≥15).
  - 운영 가시성 → `log_config { enable = true, filter = "ERRORS_ONLY" }`(값: `ERRORS_ONLY` / `TRANSLATIONS_ONLY` / `ALL`).
  - Cloud Run Direct VPC → `endpoint_types = ["ENDPOINT_TYPE_VM"]`; Cloud Run 쪽 `vpc_access { egress = "ALL_TRAFFIC" }`.
- Checkov: Cloud NAT(`google_compute_router_nat`) 로깅·설정 체크 **해당 체크 없음**(정책 인덱스에 해당 리소스 행 없음, https://www.checkov.io/5.Policy%20Index/terraform.html). 관련: `CKV_GCP_40` "Ensure that Compute instances do not have public IP addresses"(NAT 사용 근거). ⚠️출처확인필요
- 배포 후 검증:
  - Cloud Run/VM 안에서 `curl -s https://ifconfig.me` → `gcloud compute addresses describe <NAME> --region=asia-northeast3 --format='value(address)'` 와 같음.
  - `gcloud compute routers get-nat-ip-info <ROUTER> --region=asia-northeast3` / `gcloud compute routers get-nat-mapping-info <ROUTER> --region=asia-northeast3` → IP별 사용 포트·VM 매핑.
  - `gcloud compute routers nats describe <NAT> --router=<ROUTER> --region=asia-northeast3 --format='value(effectiveTcpTimeWaitTimeoutSec,minPortsPerVm,enableDynamicPortAllocation,natIpAllocateOption)'`.
  - 로그: `gcloud logging read 'resource.type="nat_gateway" AND jsonPayload.allocation_status="DROPPED"' --limit=20`(필드명은 로그 스키마 미확인) / 지표 `compute.googleapis.com/nat/dropped_sent_packets_count` reason=`OUT_OF_RESOURCES` 기대 0, `router.googleapis.com/nat/nat_allocation_failed` = false.

---

## 5.5 고정 출구 IP 방법 — 플랫폼별

> 각 하위 절은 판정 핵심 키(NW.egress, NW.client_ip, NW.private_connectivity, NW.regions, NW.cost_floor, NW.scaling)만 채우고, 나머지 NW.* 키(NW.layer 등)는 한 행으로 묶는다(요약 대상).

### 5.5.1 Cloud Run — Direct VPC egress / Serverless VPC Access 커넥터 + Cloud NAT(MANUAL_ONLY)
- 계열: 네트워크-출구
- 서울 리전: 있음

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.egress | L3/L4 | 기본은 **동적 IP 풀**. 고정 IP = VPC 경유(Direct VPC 권장 / 커넥터) + `--vpc-egress=all-traffic` + Cloud NAT 수동 IP | Cloud NAT 경유해도 추가 홉 없음(제어면만) | https://docs.cloud.google.com/run/docs/configuring/static-outbound-ip · "By default, a Cloud Run service connects to external endpoints on the internet using a dynamic IP address pool." / "the packets don't pass through the NAT gateway or the Cloud Router." · 2026-10-01 |
| NW.scaling | L4 | NAT `--min-ports-per-vm` = Cloud Run 인스턴스 하나에 필요한 포트 × **2**. 수동 IP 수는 VM + Cloud Run 인스턴스 합계 감당 | max-instances × 포트 ≤ IP 수 × 64,512 | https://docs.cloud.google.com/nat/docs/nat-product-interactions · "For Public NAT, ensure that the value of the --min-ports-per-vm flag is set to two times the number of ports needed by a single Cloud Run instance." · 2026-10-01 |
| NW.client_ip | L3 | 출발지 = 예약한 NAT IP | 스케일이 크면 IP 여러 개 | 같은 페이지(static-outbound-ip) · "If your Cloud Run workloads scale up to large numbers, you might need to assign multiple static IP addresses to Cloud NAT." · 2026-10-01 |
| NW.private_connectivity | L3 | 같은 VPC 사설 DB 접근 겸용 | — | 같은 페이지 · "requests from your Cloud Run service arrive at your VPC network." · 2026-10-01 |
| NW.regions | — | 서울 있음 | — | 05-compute-tier1-2.md 인용 재사용(https://docs.cloud.google.com/run/docs/locations) · 2026-10-01 |
| NW.cost_floor | — | Cloud NAT 5.4 비용 + 예약 IP $0.005/시간 | — | https://cloud.google.com/nat/pricing · 2026-10-01 |
| 그 외 NW.* | — | 5.4와 같음 | — | — |

- 함정: `--vpc-egress=private-ranges-only`(기본)면 인터넷 트래픽은 NAT를 안 타고 동적 IP로 나감. Cloud NAT 로그에 Cloud Run 리소스 이름 안 보임("Cloud NAT logs for Direct VPC egress don't display the names of Cloud Run resources.").
- 산출물: `google_cloud_run_v2_service.template.vpc_access { network_interfaces {...}; egress = "ALL_TRAFFIC" }` + 5.4 리소스. 검증: 서비스 안 `curl -s https://ifconfig.me` = 예약 IP.

### 5.5.2 AWS Lambda — VPC 사설 서브넷 + NAT Gateway(EIP)
- 계열: 네트워크-출구 / 서울 리전: 있음

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 |
|---|---|---|---|---|
| NW.egress | L3 | 기본(VPC 미연결)은 Lambda 관리 VPC로 인터넷 가능(고정 IP 아님). VPC 연결 시 **사설 서브넷 + NAT GW** 필요. **퍼블릭 서브넷에 붙여도 인터넷 안 됨** | IPv6는 dual-stack + egress-only IGW | https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc-internet.html · "Connecting a function to a public subnet doesn't give it internet access." · 2026-10-01 |
| NW.client_ip | L3 | 출발지 = NAT EIP | — | 같은 페이지 · "For Elastic IP allocation ID, select an elastic IP address or choose Allocate Elastic IP." · 2026-10-01 |
| NW.scaling | L4 | 동시 실행 수 × 실행당 외부 연결 ≤ 55,000 × EIP 수(같은 목적지) (추론, 5.1 식 적용) | — | 5.1 출처 ⚠️근거없음 |
| NW.private_connectivity | L3 | 같은 VPC RDS 등 사설 접근 겸용 | — | 같은 페이지 · "This restricts the function to resources within that VPC, unless the VPC has internet access." · 2026-10-01 |
| NW.regions / NW.cost_floor | — | 서울 있음 / NAT 월 $43.07(AZ당) + EIP $3.65 + $0.059/GB | 문서는 AZ당 NAT 권고("1 per AZ") | [PL] 5.1 |
| 그 외 NW.* | — | 5.1과 같음 | — | — |

- 함정: VPC 연결 후 NAT 없으면 외부 호출이 **타임아웃**(오류 아님). 산출물: `aws_lambda_function.vpc_config { subnet_ids = 사설, security_group_ids }` + 5.1 리소스. 검증: 함수에서 `https://checkip.amazonaws.com` 응답 = EIP.

### 5.5.3 ECS Fargate — 사설 서브넷 + NAT, 또는 퍼블릭 서브넷 공인 IP
- 계열: 네트워크-출구 / 서울 리전: 있음

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 |
|---|---|---|---|---|
| NW.egress | L3 | 태스크마다 ENI 1개. 퍼블릭 서브넷이면 태스크 ENI에 **공인 IP 선택 할당**(태스크별·자동 할당이라 교체 시 바뀜 — 추론, 문서에 EIP 연결 수단 없음). 고정 IP는 사설 서브넷 + NAT EIP | ENI는 Fargate 관리, 수동 수정 불가 | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-task-networking.html · "When using a public subnet, you can optionally assign a public IP address to the task's ENI." / "When using a private subnet, the subnet can have a NAT gateway attached." / "You can't manually detach or modify the ENIs that are created and attached by Fargate." · 2026-10-01 ⚠️근거없음 |
| NW.private_connectivity | L3 | ECR 인터페이스 엔드포인트로 NAT 없이 이미지 풀 가능 | — | 같은 페이지 · "you can configure Amazon ECR to use an interface VPC endpoint and the image pull occurs over the task's private IPv4 address." · 2026-10-01 |
| NW.cost_floor | — | 퍼블릭 IP 방식: 태스크당 IPv4 $3.65/월. NAT 방식: 5.1 | — | [PL] AmazonVPC `APN2-PublicIPv4:InUseAddress` · 2026-10-01 |
| 그 외 NW.* | — | 5.1과 같음 | — | — |

- 함정: 퍼블릭 IP 방식은 태스크 수만큼 IP가 다르고 재배포마다 바뀜 → 허용 목록 불가 (추론). Checkov `CKV_AWS_333` "Ensure ECS services do not have public IP addresses assigned to them automatically". 산출물: `aws_ecs_service.network_configuration { subnets = 사설, assign_public_ip = false }`. ⚠️근거없음

### 5.5.4 Vercel — Static IPs / Secure Compute
- 계열: 네트워크-출구 / 서울 리전: 미확인(리전별 IP 쌍, 지원 리전 목록 미확인)

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 |
|---|---|---|---|---|
| NW.egress | L3 | **Static IPs(공유 풀)**: Pro·Enterprise, Vercel Functions 출구를 공유 고정 IP 쌍으로(관리형 NAT GW). 리전마다 IP 쌍. 빌드 트래픽도 선택. **Routing Middleware는 미적용**. Secure Compute(Enterprise): 전용 VPC 고정 IP | 소수 고객과 IP 공유. 환경별 분리 불가. 컨테이너 이미지·확장 실행 시간 베타 미지원 | https://vercel.com/docs/connectivity/static-ips · "Outbound traffic from your Vercel Functions routes through shared static IP pairs." / "Static IP addresses are shared across a small group of customers in the same region" · 2026-10-01 |
| NW.cost_floor | — | **$100/월/프로젝트**(Pro) + Private Data Transfer(리전 요금). Secure Compute는 별도 견적 | — | 같은 페이지 · "Static IPs are priced at $100/month per project for Pro plus Private Data Transfer" · 2026-10-01 |
| NW.private_connectivity | L3 | Secure Compute: VPC 피어링, 전용 VPC(Enterprise) | Secure Compute 사용 시 Static IPs 무시 | 같은 페이지 · "If your project uses Secure Compute and you have enabled Static IPs, Static IPs will be ignored." · 2026-10-01 |
| 그 외 NW.* | — | 미확인/해당 없음 | — | — |

### 5.5.5 Netlify — Private Connectivity
- 계열: 네트워크-출구 / 서울 리전: **없음**(함수 지원 리전 cmh·fra·lhr)

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 |
|---|---|---|---|---|
| NW.egress | L3 | 빌드·함수가 바뀌지 않는 고정 IP 집합으로 나감 | **Enterprise 애드온** + High-Performance Edge/Build 필요 | https://docs.netlify.com/manage/security/private-connectivity/ · "With Private Connectivity, you can count on the connections coming from a static set of IPs that never change." / "This feature is available as an add-on to Enterprise plans" · 2026-10-01 |
| NW.regions | — | 함수: US East (Ohio), EU (Frankfurt), EU (London) | 서울 없음 | 같은 페이지 · "cmh - US East (Ohio) ... fra - EU (Frankfurt) ... lhr - EU (London)" · 2026-10-01 |
| NW.cost_floor | — | 미확인(Enterprise 견적) | — | — |
| 그 외 NW.* | — | 미확인/해당 없음 | — | — |

### 5.5.6 Cloudflare Workers
- 계열: 네트워크-출구 / 서울 리전: 글로벌(엣지)

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 |
|---|---|---|---|---|
| NW.egress | L3/L7 | 기본 고정 출구 IP 기능 문서 미확인. **Enterprise Dedicated CDN Egress IPs**(Smart Shield): Workers `fetch()`로 오리진 접근 시 적용, **`connect()`(TCP 소켓)에는 미적용** | 계정팀 문의 | https://developers.cloudflare.com/smart-shield/configuration/dedicated-egress-ips/other-products/ · "fetch() requests that access services on your origin will use Dedicated CDN Egress IP addresses." / "Dedicated CDN Egress IPs are not used." · 2026-10-01 ; https://developers.cloudflare.com/smart-shield/configuration/dedicated-egress-ips/ · "Enterprise customers can leverage dedicated egress IPs for layer 7 WAF and CDN services" · 2026-10-01 |
| NW.private_connectivity | L3 | VPC Network 바인딩(`cf1:network`)이면 Workers 출구가 Cloudflare Gateway 정책을 거침(2026-06 변경) | 플랜 요건 미확인 | https://developers.cloudflare.com/changelog/post/2026-06-05-gateway-egress/ · "Workers using a VPC Network binding with network_id: \"cf1:network\" now egress to public Internet destinations through Cloudflare Gateway." · 2026-10-01 |
| NW.cost_floor | — | 미확인(Enterprise) | — | — |
| 그 외 NW.* | — | 미확인/해당 없음 | — | — |

### 5.5.7 Render — 공유 출구 IP 범위 / Dedicated outbound IPs
- 계열: 네트워크-출구 / 서울 리전: 미확인(Render 리전 목록은 이 절에서 확인 안 함)

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 |
|---|---|---|---|---|
| NW.egress | L3 | 기본: **리전 내 모든 서비스가 공유하는 CIDR 범위**(대시보드 Connect → Outbound). 전용: Dedicated IP set(IPv4 3개), **Pro 워크스페이스 이상**, 워크스페이스당 기본 4세트 | 같은 리전 서비스만 사용 | https://render.com/docs/outbound-ip-addresses · "Outbound IP ranges are shared across all services in the same region." · 2026-10-01 ; https://render.com/docs/dedicated-ips · "Each dedicated IP set you create includes three IPv4 addresses." / "Dedicated IPs require a Pro workspace plan or higher." · 2026-10-01 ⚠️출처확인필요 |
| NW.cost_floor | — | IP 세트당 월 요금(금액 미확인) | — | https://render.com/docs/dedicated-ips · "Render bills your workspace monthly for each IP set." · 2026-10-01 ⚠️출처확인필요 |
| 그 외 NW.* | — | 미확인/해당 없음 | — | — |

### 5.5.8 Fly.io — static egress IP
- 계열: 네트워크-출구 / 서울 리전: 미확인(이 절에서 리전 목록 미확인)

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 |
|---|---|---|---|---|
| NW.egress | L3 | 기본 출구 IP **불안정(변경됨)**. 앱 범위 static egress IP(`fly ips allocate-egress --app <app> -r <region>`), 리전마다 최소 1개, **IP 하나당 Machine 최대 64대** | IPv6 함께 할당 | https://docs.fly.io/networking/egress-ips/ · "By default, outbound (egress) IPs from Fly Machines are unstable and may change." / "Each static egress IP can support up to 64 Machines." · 2026-10-01 ⚠️출처확인필요 |
| NW.cost_floor | — | IPv4 **$3.60/월/개**(시간 과금), IPv6 무료 | — | 같은 페이지 · "Each app-scoped IPv4 static egress address costs $3.60/mo, billed hourly." · 2026-10-01 ⚠️출처확인필요 |
| 그 외 NW.* | — | 미확인/해당 없음 | — | — |

### 5.5.9 Railway — Static Outbound IPs
- 계열: 네트워크-출구 / 서울 리전: 미확인

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 |
|---|---|---|---|---|
| NW.egress | L3 | **Pro 플랜** 서비스별 토글, IPv4, 다른 고객과 **공유 가능**, 인바운드 불가, 리전 이동 시 IP 변경, 재배포 필요 | 레거시 단일 IP는 2026-07-13까지 업그레이드 요구 | https://docs.railway.com/reference/static-outbound-ips · "Customers on the Pro plan can enable Static Outbound IPs for any service they wish." / "There is no guarantee that the IPv4 addresses assigned to your service are dedicated." · 2026-10-01 ⚠️출처확인필요 |
| NW.cost_floor | — | 미확인(Pro 플랜 포함 여부 미확인) | — | — |
| 그 외 NW.* | — | 미확인/해당 없음 | — | — |

### 5.5.10 Heroku — Private Spaces
- 계열: 네트워크-출구 / 서울 리전: 미확인

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 |
|---|---|---|---|---|
| NW.egress | L3 | Private Space 앱의 모든 출구가 스페이스 전용 소수 고정 IP 목록에서 나감. Common Runtime 고정 IP: 문서 미확인(애드온 Fixie 등은 이 절에서 미검증) | — | https://devcenter.heroku.com/articles/private-spaces · "All outbound traffic from apps in a Private Space originate from a small, stable list of IP addresses dedicated to the space." · 2026-10-01 |
| NW.cost_floor | — | 미확인 | — | — |
| 그 외 NW.* | — | 미확인/해당 없음 | — | — |

---

## 5.6 퍼블릭 IPv4 주소 요금 (AWS / GCP) 및 IPv6 대안
- 계열: 네트워크-출구
- 서울 리전: 있음(AWS [PL] 서울, GCP는 페이지 기본 표시 리전 값 — 서울 개별값 미확인)

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L3 | 공인 IPv4 주소 자원(EIP, 자동 할당 퍼블릭 IP, GCP 외부 IP) | — | — ⚠️근거없음 |
| NW.egress | L3 | 고정 출구 IP의 실체. AWS EIP는 연결해 두면 재시작에도 유지, GCP 정적(예약) 주소는 리소스 삭제·재생성에도 유지 | — | https://docs.cloud.google.com/run/docs/configuring/static-outbound-ip · "A reserved IP address resource retains the underlying IP address when the resource it is associated with is deleted and re-created" · 2026-10-01 |
| NW.cost_floor | — | **AWS 서울**: 사용 중 $0.005/시간, **유휴도 $0.005/시간**(월 $3.65/개), 연속 블록 $0.008/시간. 초 단위(최소 60초). **AWS 프리티어**: EC2 12개월 프리티어에 사용 중 퍼블릭 IPv4 **월 750시간** 무료(유휴는 제외). **GCP**: 미사용 정적 $0.01/시간, 표준 VM 사용 중 $0.005/시간, 스팟·선점형 VM $0.0025/시간, **Cloud NAT 사용 $0.005/시간**, 포워딩 규칙(LB) 연결 무료 | GCP 값은 페이지 기본 리전(Iowa) 표시값, 서울 값 미확인. AWS 2025-07 이후 신규 프리티어(크레딧제)에서의 적용 여부 미확인 | [PL] AmazonVPC ap-northeast-2 · `APN2-PublicIPv4:InUseAddress` "$0.005 per In-use public IPv4 address per hour" / `APN2-PublicIPv4:IdleAddress` "$0.005 per Idle public IPv4 address per hour" / `APN2-PublicIPv4:ContiguousBlock` "$0.008 per hour per IPv4 address in contiguous IPv4 block" · 2026-10-01 ; https://aws.amazon.com/vpc/pricing/ · "The bill is calculated in one-second increments, with a minimum of 60 seconds." · 2026-10-01 ; https://aws.amazon.com/about-aws/whats-new/2024/02/aws-free-tier-750-hours-free-public-ipv4-addresses/ · "you will get 750 hours public IPv4 address usage per month free when launching any EC2 instance with a public IPv4 address." · 2026-10-01 ; https://cloud.google.com/vpc/pricing · "Static IP address (assigned but unused) $0.01" / "Static and ephemeral IP addresses used by Cloud NAT . $0.005 / 1 hour" / "Static and ephemeral IP addresses in use on preemptible and Spot VM instances $0.0025 / 1 hour" · 2026-10-01 |
| NW.protocols | L3 | IPv6 대안: **AWS egress-only IGW**(IPv6 전용, 무료, 인바운드 차단) + NAT GW의 NAT64·DNS64. **GCP**: 외부 IPv6 주소 무료, Cloud NAT NAT64(VM만) | IPv6 목적지가 IPv4만 지원하면 NAT64 필요 | https://docs.aws.amazon.com/vpc/latest/userguide/egress-only-internet-gateway.html · "There is no charge for an egress-only internet gateway, but there are data transfer charges" · 2026-10-01 ; https://cloud.google.com/vpc/pricing · "You are not charged for external IPv6 address ranges that are assigned to subnets or for external IPv6 addresses that are assigned to VM instances ." · 2026-10-01 |
| NW.client_ip | L3 | GCP 임시(ephemeral) IP는 VM 중지·삭제 시 반납 → 고정 아님 | — | https://cloud.google.com/vpc/pricing · "When the instance is stopped or deleted, Google Cloud releases the ephemeral IP address" · 2026-10-01 |
| NW.regions | — | AWS 서울 [PL] 확인. GCP 서울 개별값 미확인 | — | 위 |
| NW.idle_timeout, NW.request_timeout, NW.websocket, NW.body_size, NW.draining, NW.health_check, NW.tls, NW.routing, NW.scaling, NW.availability, NW.caching, NW.security, NW.dns, NW.private_connectivity | — | 해당 없음 | — | — |

### 비용 구조
- AWS: 2024-02부터 모든 퍼블릭 IPv4 시간 과금. ALB(AZ당 IP), NAT EIP, 퍼블릭 서브넷 태스크 공인 IP 모두 포함 → 소규모 구성 고정비에 IP 수 × $3.65/월 가산.
- GCP: LB 포워딩 규칙 IP는 무료, 미사용 정적 IP는 2배.

### 교체 계열 정보
- IPv6 전용 출구(egress-only IGW / NAT64)로 IPv4 비용 절감. 외부 API가 IPv6 미지원이면 NAT64 필요 → NAT GW 비용 재발생.

### 함정
- AWS 유휴 EIP도 같은 요금($0.005) — NAT 삭제 후 EIP 해제 누락 시 계속 과금. GCP 미사용 정적 IP는 $0.01(2배).
- AWS 750시간 프리티어는 EC2 프리티어 대상·사용 중 IP만(유휴 제외).

### 생성 산출물
- Terraform 리소스: `aws_eip`(`domain = "vpc"`), `aws_egress_only_internet_gateway`, `google_compute_address`(`address_type = "EXTERNAL"`, `region`, `network_tier`).
- 요구: E1/E3 허용 목록 → 예약(정적) 주소만 사용, 출력값으로 IP 노출. G3 높음 → 퍼블릭 IPv4 수 최소화(사설 서브넷 + NAT 1개, 또는 IPv6).
- Checkov: `CKV2_AWS_19`(미연결 EIP 탐지), `CKV_AWS_130`, `CKV_AWS_88`, `CKV_GCP_40`.
- 배포 후 검증: `aws ec2 describe-addresses --query 'Addresses[?AssociationId==null].PublicIp'` → 빈 목록(유휴 EIP 없음); `gcloud compute addresses list --filter='status=RESERVED'` → 의도한 것만.

---

# 6. 사설 연결

## 6.1 AWS VPC 엔드포인트 — Gateway (S3·DynamoDB)
- 계열: 네트워크-사설 연결
- 서울 리전: 있음 (가용성은 리전별 서비스로 제공, 서울 Price List의 VPC 엔드포인트 항목과 함께 확인. 게이트웨이는 별도 과금 SKU 없음 → 무료)

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L3 | 라우트 테이블 대상(라우팅만, 프록시 아님). PrivateLink를 쓰지 않음 | 접두사 목록(prefix list) → 엔드포인트 라우트가 선택한 라우트 테이블에 자동 추가, 수정·삭제 불가 | https://docs.aws.amazon.com/vpc/latest/privatelink/gateway-endpoints.html · "Gateway endpoints do not use AWS PrivateLink, unlike other types of VPC endpoints." / "The destination is a prefix list for the service owned by AWS and the target is the gateway endpoint." · 2026-10-01 |
| NW.idle_timeout | — | 미확인 (게이트웨이 엔드포인트 고유 유휴 타임아웃 문서 없음) | (추론) 프록시가 아니므로 S3·DynamoDB 서버 쪽 타임아웃이 지배 | — ⚠️근거없음 |
| NW.request_timeout | — | 해당 없음 | — | — |
| NW.websocket | — | 해당 없음 | — | — |
| NW.protocols | L4 | S3·DynamoDB 공용 엔드포인트로 가는 TCP 443 트래픽을 라우팅. 대상 서비스는 S3·DynamoDB 둘뿐 | 같은 라우트 테이블에 S3 1개·DynamoDB 1개 라우트, 같은 서비스 라우트 중복 불가 | 같은 페이지 · "You can't have multiple endpoint routes to the same service (Amazon S3 or DynamoDB) in a single route table." / 보안 그룹 예시 "prefix_list_id TCP 443" · 2026-10-01 |
| NW.body_size | — | 해당 없음 | — | — |
| NW.draining | — | 해당 없음 | — | — |
| NW.health_check | — | 해당 없음 | — | — |
| NW.tls | — | 해당 없음(TLS는 클라이언트↔S3/DynamoDB 종단 간, 엔드포인트는 관여 안 함) | — | — |
| NW.client_ip | L3 | S3·DynamoDB가 보는 출발지 IP가 공인 IP → VPC 사설 IP로 바뀜. 엔드포인트 생성·변경 시 기존 TCP 연결이 끊김. `aws:SourceIp` 조건 무효 → `aws:VpcSourceIp` 사용 | 버킷 정책에 `aws:SourceIp`가 있으면 엔드포인트 도입 후 거부됨 | https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints-s3.html · "An endpoint switches network routes, and disconnects open TCP connections." / "You can't use the aws:SourceIp condition in an identity policy or a bucket policy for requests to Amazon S3 that traverse a VPC endpoint." · 2026-10-01 |
| NW.routing | L3 | 최장 접두사 일치. 0.0.0.0/0→IGW가 있어도 같은 리전 S3/DynamoDB는 엔드포인트 경로 우선. 다른 리전 S3는 IGW/NAT로 감 | 연결된 라우트 테이블의 서브넷만 사용, 나머지 서브넷은 공용 경로 | https://docs.aws.amazon.com/vpc/latest/privatelink/gateway-endpoints.html · "Traffic that's destined for the service (Amazon S3 or DynamoDB) in a different Region goes to the internet gateway because prefix lists are specific to a Region." · 2026-10-01 |
| NW.scaling | — | 미확인 (게이트웨이 엔드포인트 대역폭 한도 문서 없음). 리전당 게이트웨이 엔드포인트 20개(조정 가능), VPC당 255 | — | https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints-s3.html · "Your account has a default quota of 20 gateway endpoints per Region, which is adjustable. There is also a limit of 255 gateway endpoints per VPC." · 2026-10-01 |
| NW.availability | L3 | 리전 범위(AZ별 생성 없음). 같은 리전 버킷·테이블만 | — | 같은 페이지 · "A gateway endpoint is available only in the Region where you created it." · 2026-10-01 |
| NW.caching | — | 해당 없음 | — | — |
| NW.security | L3 | 엔드포인트 정책(IAM 정책 언어, 기본 전체 허용, 최대 20,480자) + 버킷 정책 `aws:sourceVpce`/`aws:SourceVpc`. 인스턴스 SG 아웃바운드가 제한돼 있으면 접두사 목록 ID를 허용해야 함, NACL은 접두사 목록 참조 불가(CIDR로) | 정책 변경 반영에 수 분 | https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints-access.html · "The size of an endpoint policy cannot exceed 20,480 characters, including white space." / https://docs.aws.amazon.com/vpc/latest/privatelink/gateway-endpoints.html · "You can't reference prefix lists in network ACL rules" · 2026-10-01 |
| NW.dns | — | DNS 변경 없음: 공용 이름(`s3.ap-northeast-2.amazonaws.com`)이 그대로 공인 IP로 해석되고 라우팅만 바뀜. Amazon DNS 사용 시 VPC의 DNS hostnames·DNS resolution 둘 다 켜야 함. IPv6/dualstack 게이트웨이는 S3만(DynamoDB는 IPv4만) **[충돌]** 아래 참조 | **[충돌]** 일반 페이지는 게이트웨이 엔드포인트 IP 유형에 IPv6/Dualstack을 나열, DynamoDB 페이지는 "IPv4만" | https://docs.aws.amazon.com/vpc/latest/privatelink/gateway-endpoints.html · "Dualstack – Add the service's IPv4 prefix list to your route table and add the service's IPv6 prefix list to your route table." vs https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints-ddb.html · "Gateway endpoints support only IPv4 traffic." · 2026-10-01 |
| NW.egress | L3 | S3·DynamoDB 트래픽을 NAT에서 빼냄 → NAT 처리 요금($0.059/GB 서울) 절감. 그 외 목적지는 여전히 NAT 필요 | — | https://docs.aws.amazon.com/vpc/latest/privatelink/gateway-endpoints.html · "Gateway VPC endpoints provide reliable connectivity to Amazon S3 and DynamoDB without requiring an internet gateway or a NAT device for your VPC." · 2026-10-01 |
| NW.private_connectivity | L3 | **대상: S3·DynamoDB만. 같은 리전만. VPC 안 리소스만**: 온프레미스(VPN·Direct Connect), 피어링 VPC, Transit Gateway 건너편에서는 사용 불가 → 그 경우 인터페이스 엔드포인트(유료). SG: 클라이언트 SG 아웃바운드에 접두사 목록. DNS: 변경 없음(공용 이름 그대로). 요금: 0 | 게이트웨이와 인터페이스(S3)를 함께 두고 인바운드 Resolver 엔드포인트에만 사설 DNS를 켜는 비용 최적화 가능(S3만) | https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints-s3.html · "gateway endpoints do not allow access from on-premises networks, from peered VPCs in other AWS Regions, or through a transit gateway." / "Resources on the other side of a VPN connection, VPC peering connection, transit gateway, or Direct Connect connection in your VPC cannot use a gateway endpoint" · 2026-10-01 |
| NW.regions | — | 리전별. 서울 사용 가능 (추론: 서울 AmazonVPC 오퍼 파일에 엔드포인트 항목 존재, 게이트웨이는 무료라 SKU 없음) | — | [PL] AmazonVPC ap-northeast-2 · "$0.013 per VPC Endpoint Hour" (인터페이스) · 2026-10-01 ⚠️근거없음 |
| NW.cost_floor | — | $0 (시간·GB 요금 없음). 같은 리전 S3↔EC2 전송 요금 별도는 미확인 | — | https://docs.aws.amazon.com/vpc/latest/privatelink/gateway-endpoints.html · "There is no additional charge for using gateway endpoints." · 2026-10-01 |

### 비용 구조
- 엔드포인트 자체 $0. 사설 서브넷이 S3·DynamoDB를 NAT 경유로 부르던 양만큼 NAT 처리 요금이 사라진다(서울 NAT $0.059/GB, [PL] AmazonEC2 ap-northeast-2 "$0.059 per GB Data Processed by NAT Gateways", 05-compute-tier1-2.md §1.3 값 재사용).
- ECR 이미지 레이어는 S3에서 받으므로 ECR 풀 트래픽 대부분이 이 엔드포인트로 무료가 된다(6.2 참조).

### 교체 계열 정보
- 같은 목적: S3/DynamoDB 인터페이스 엔드포인트(6.2, 유료, 온프레미스·피어링·TGW에서 사용 가능), NAT Gateway(유료, 모든 목적지).
- GCP 대응: Private Google Access(서브넷 단위) (추론, 이 절에서 확인 안 함). ⚠️근거없음

### 함정
- 엔드포인트 생성·라우트 테이블 연결 순간 기존 S3/DynamoDB TCP 연결이 끊긴다 → 운영 중 적용 시 재연결 로직 필요.
- 버킷 정책의 `aws:SourceIp`(NAT EIP 허용) 조건은 엔드포인트 도입 후 일치하지 않는다 → `aws:sourceVpce`/`aws:VpcSourceIp`로 바꿔야 함.
- 다른 리전 S3 버킷은 엔드포인트를 타지 않고 NAT/IGW로 간다(사설 서브넷에 NAT가 없으면 실패).
- 라우트 테이블을 지정하지 않은 서브넷(예: Lambda용 별도 서브넷)은 엔드포인트를 쓰지 않는다.
- SG 아웃바운드를 좁혀 둔 경우 S3 접두사 목록(pl-…)을 443으로 열어야 한다.

### 생성 산출물
- Terraform 리소스: `aws_vpc_endpoint` (https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_endpoint, 원문 https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc_endpoint.html.markdown), 선택적으로 `aws_vpc_endpoint_route_table_association`(`route_table_id`, `vpc_endpoint_id`), `aws_vpc_endpoint_policy`.
- 요구에 따라 반드시 명시할 속성:
  - `vpc_endpoint_type = "Gateway"`(기본값이 Gateway지만 명시), `service_name = "com.amazonaws.ap-northeast-2.s3"` 또는 `...dynamodb`.
  - `route_table_ids` → 사설 서브넷 라우트 테이블 **전부**(AZ별 라우트 테이블이면 모두). 이미지 풀(ECR)·S3 업로드(A7)·C5 키-값(DynamoDB) 요구가 있으면 필수.
  - `policy` → F5(민감 데이터)이면 특정 버킷 ARN(+ ECR 레이어 버킷 `arn:aws:s3:::prod-ap-northeast-2-starport-layer-bucket/*`)만 허용하는 정책, 없으면 생략(기본 전체 허용).
  - `ip_address_type` → IPv6/dualstack 서브넷이면 `dualstack`(S3만).
  - 참조 속성: `prefix_list_id`를 SG 이그레스 규칙 대상으로.
- Checkov: `aws_vpc_endpoint` 전용 체크 없음(인덱스에 이 리소스 대상은 CKV2_AWS_37·CKV2_AWS_75처럼 리소스 유형 목록이 잘못 매핑된 항목뿐 → 해당 체크 없음). 관련: CKV2_AWS_11 "Ensure VPC flow logging is enabled in all VPCs"(`aws_vpc`).
- 배포 후 검증:
  - `aws ec2 describe-vpc-endpoints --filters Name=service-name,Values=com.amazonaws.ap-northeast-2.s3 --query 'VpcEndpoints[].[VpcEndpointType,State,RouteTableIds]'` → `Gateway`, `available`, 사설 라우트 테이블 ID 전부.
  - `aws ec2 describe-route-tables --route-table-ids <rtb> --query 'RouteTables[].Routes[?GatewayId!=null && starts_with(GatewayId, `vpce-`)]'` → `DestinationPrefixListId: pl-…`, 대상 `vpce-…`.
  - 사설 서브넷 인스턴스에서 `nslookup s3.ap-northeast-2.amazonaws.com` → **공인 IP**가 나오는 것이 정상(게이트웨이는 DNS를 바꾸지 않음). 그 상태로 `aws s3 ls s3://<bucket> --region ap-northeast-2` 성공, NAT 경로를 막아도 성공해야 함.
  - VPC Flow Logs에서 S3 대상 흐름의 `pkt-dst-aws-service`=`S3`, NAT ENI를 거치지 않는지 확인.

---

## 6.2 AWS VPC 엔드포인트 — Interface (PrivateLink 소비자 측, AWS 서비스 대상)
- 계열: 네트워크-사설 연결
- 서울 리전: 있음 ([PL] AmazonVPC ap-northeast-2 `APN2-VpcEndpoint-Hours`)

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L4 | 서브넷마다 요청자 관리형 ENI를 만들고 DNS로 그 사설 IP에 보냄. TCP·UDP 전달(HTTP 종단 아님) | ENI는 보이지만 직접 관리 불가 | https://docs.aws.amazon.com/vpc/latest/privatelink/create-interface-endpoint.html · "An endpoint network interface is a requester-managed network interface; you can view it in your AWS account, but you can't manage it yourself." / https://docs.aws.amazon.com/vpc/latest/privatelink/concepts.html · "Create an interface endpoint to send TCP or UDP traffic to an endpoint service." · 2026-10-01 |
| NW.idle_timeout | L4 | 350초 고정(유휴 후 패킷은 전달 안 됨). 공식 블로그 값, 개발자 가이드에서는 찾지 못함 | 앱·SDK의 keep-alive 간격 < 350초 필요(장시간 유휴 풀 연결) | https://aws.amazon.com/blogs/networking-and-content-delivery/implementing-long-running-tcp-connections-within-vpc-networking/ · "NAT Gateway, Amazon Virtual Private Cloud (Amazon VPC) Endpoints, and Network Load Balancer (NLB) currently have a fixed idle timeout of 350 seconds." · 2026-10-01 |
| NW.request_timeout | — | 해당 없음(L4 통과) | — | — |
| NW.websocket | — | 해당 없음(AWS 서비스 API 대상) | — | — |
| NW.protocols | L4 | TCP·UDP. MTU 8500 바이트, 초과 패킷 드롭, PMTUD 미지원, MSS 클램핑 | — | https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-limits-endpoints.html · "A VPC endpoint supports an MTU of 8500 bytes." / "Path MTU Discovery (PMTUD) is not supported." · 2026-10-01 |
| NW.body_size | — | 해당 없음 | — | — |
| NW.draining | — | 해당 없음 | — | — |
| NW.health_check | L4 | 리전 DNS 이름은 정상 ENI 중 라운드 로빈 선택. 한 AZ에만 두면 그 AZ 장애 시 다른 AZ 리소스도 접근 상실 | — | https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-access-aws-services.html · "we select a healthy endpoint network interface, using the round robin algorithm" / "if Availability Zone 1 is impaired, the resources in Availability Zone 2 lose access" · 2026-10-01 |
| NW.tls | TLS | 엔드포인트는 TLS를 종단하지 않음. 사설 DNS를 켜면 공용 이름 그대로 써서 서비스 인증서와 이름이 일치 (추론) | — | — ⚠️근거없음 |
| NW.client_ip | L3 | AWS 서비스는 사설 IP·`aws:SourceVpce`로 식별(엔드포인트 경유 시 `aws:SourceIp` 대신 `aws:VpcSourceIp`) | S3 기준 문서, 다른 서비스도 같은 조건 키 (추론) | https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints-s3.html · "Instead, use the aws:VpcSourceIp condition." · 2026-10-01 ⚠️근거없음 |
| NW.routing | L3 | 라우트 테이블 변경 없음, DNS로만 유도. 같은 AZ 고정이 필요하면 존 DNS 이름 사용 | AZ당 서브넷 1개만 선택 가능 | https://docs.aws.amazon.com/vpc/latest/privatelink/create-interface-endpoint.html · "You can select one subnet per Availability Zone. You can't select multiple subnets from the same Availability Zone." · 2026-10-01 |
| NW.scaling | L4 | AZ당 기본 10Gbps, 자동으로 100Gbps까지. 엔드포인트 최대 = AZ 수 × 100Gbps. VPC당 인터페이스+GWLB 엔드포인트 50개(조정 가능) | 그 이상은 지원 요청 | https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-limits-endpoints.html · "each VPC endpoint can support a bandwidth of up to 10 Gbps per Availability Zone, and automatically scales up to 100 Gbps." / "Interface and Gateway Load Balancer endpoints per VPC 50 Yes" · 2026-10-01 |
| NW.availability | L4 | 존 단위 ENI. 운영은 최소 2 AZ 권장. ENI IP는 엔드포인트 수명 동안 불변 | — | https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-access-aws-services.html · "Configure at least two Availability Zones per VPC endpoint" / "The IP addresses of an endpoint network interface will not change during the lifetime of its VPC endpoint." · 2026-10-01 |
| NW.caching | — | 해당 없음 | — | — |
| NW.security | L4 | ENI에 SG 부착(미지정 시 VPC 기본 SG) → 클라이언트 서브넷에서 **인바운드 443** 허용 필요. 엔드포인트 정책은 지원 서비스만(미지원이면 전체 허용) | ECR: "port 443 from the private subnet" | https://docs.aws.amazon.com/vpc/latest/privatelink/create-interface-endpoint.html · "the security group must allow inbound HTTPS traffic." / "By default, we associate the default security group for the VPC." / https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints-access.html · "If an AWS service doesn't support endpoint policies, we allow full access to any endpoint for the service." · 2026-10-01 |
| NW.dns | — | 사설 DNS(`private_dns_enabled`) 켜면 숨겨진 AWS 관리 사설 호스팅 영역이 공용 이름(`<svc>.ap-northeast-2.amazonaws.com`)을 ENI 사설 IP로 해석. VPC DNS hostnames·resolution 둘 다 켜야 함. 엔드포인트 고유 이름(`vpce-….<svc>.ap-northeast-2.vpce.amazonaws.com`)은 공개 해석되지만 사설 IP 반환. 온프레미스는 Route 53 Resolver 인바운드 엔드포인트 필요 | 콘솔은 S3 외 서비스에 기본 켬, Terraform 기본은 `false` | https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-access-aws-services.html · "we create a hidden, AWS-managed private hosted zone for you." / "you can't use the Route 53 Resolver from outside your VPC." / Terraform 원문 · "`private_dns_enabled` ... Defaults to `false`." · 2026-10-01 |
| NW.egress | L4 | AWS API 호출을 NAT에서 빼냄. 서비스가 VPC로 연결을 시작할 수 없음(단방향) | — | https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-access-aws-services.html · "The service can't initiate requests to resources through the VPC endpoint." · 2026-10-01 |
| NW.private_connectivity | L4 | **대상: PrivateLink 통합 AWS 서비스(목록 약 480개 서비스 이름: ecr.api, ecr.dkr, logs, secretsmanager, sts, ssm, kms, sqs, rds(관리 API), lambda 등)**. **리전: 기본 같은 리전, 교차 리전은 일부 서비스만(S3, IAM, ECR api/dkr, KMS, ECS, Lambda, Firehose, Flink, Route 53)이고 리전 DNS만 가능(존 DNS 불가), `vpce:AllowMultiRegion` 권한 필요**. VPC 밖(피어링·TGW·VPN·온프레미스)에서도 사용 가능(게이트웨이와 차이). DNS: 사설 DNS. SG: 엔드포인트 SG 인바운드 443. **ECR 풀 최소 조합: `ecr.api` + `ecr.dkr`(사설 DNS 필수) + S3 게이트웨이**, Fargate awslogs면 `logs`, 시크릿 주입이면 `secretsmanager`(SSM 파라미터면 `ssm`). 풀스루 캐시 첫 풀은 NAT 필요 | 요금: AZ당 시간 + GB (아래) | https://docs.aws.amazon.com/vpc/latest/privatelink/aws-services-cross-region-privatelink-support.html · "You must use regional DNS. Zonal DNS is not supported when accessing AWS services in another Region." / https://docs.aws.amazon.com/AmazonECR/latest/userguide/vpc-endpoints.html · "Amazon ECS tasks hosted on Fargate using platform version 1.4.0 or later require both Amazon ECR VPC endpoints and the Amazon S3 gateway endpoints." / "When you create this endpoint, you must enable a private DNS hostname." / "then you need to create a public subnet in the same VPC, with a NAT gateway" / https://docs.aws.amazon.com/AmazonECS/latest/developerguide/vpc-endpoints.html · "To allow your tasks to pull sensitive data from Secrets Manager, you must create the interface VPC endpoints for Secrets Manager." · 2026-10-01 |
| NW.regions | — | 서울 있음. 교차 리전(AWS 서비스 대상) 지원 | — | [PL] AmazonVPC ap-northeast-2 · usagetype `APN2-VpcEndpoint-Hours` "$0.013 per VPC Endpoint Hour" · 2026-10-01 |
| NW.cost_floor | — | **$0.013/시간 × AZ 수 × 엔드포인트 수**(부분 시간은 1시간). 1개×2AZ = 월 $18.98(730h). 처리 $0.01/GB(리전 합산 1PB까지), $0.006(1~5PB), $0.004(5PB 초과) | 엔드포인트가 있으면 연결 상태와 무관하게 과금 | [PL] AmazonVPC ap-northeast-2 · `APN2-VpcEndpoint-Hours` "$0.013 per VPC Endpoint Hour" / `APN2-VpcEndpoint-Bytes` "$0.01 per GB for upto 1 PB monthly data processed by VPC Endpoints" / https://aws.amazon.com/privatelink/pricing/ · "You will be billed for each hour that your VPC endpoint remains provisioned in each Availability Zone, irrespective of the state of its association" · 2026-10-01 |

### 비용 구조
- 시간: $0.013 × AZ × 엔드포인트. 월(730h) 기준 AZ 하나당 $9.49.
  - ECR 풀만(ecr.api, ecr.dkr, 2 AZ): 월 $37.96 + S3 게이트웨이 $0.
  - Fargate 사설 서브넷 표준 세트(ecr.api, ecr.dkr, logs, secretsmanager, 2 AZ): 월 $75.92. sts·ssm·kms를 더하면 개당 2AZ 월 $18.98씩.
  - 비교: NAT Gateway 서울 $0.059/시간(월 $43.07, AZ당) + $0.059/GB. 2 AZ NAT = 월 $86.14 고정. (추론) 엔드포인트 4개 이하·2AZ이고 외부 인터넷이 필요 없으면 엔드포인트가 싸고, 외부 API(E1) 호출이 있으면 NAT는 어차피 필요해 엔드포인트는 GB 단가 차이($0.059→$0.01)만큼만 이득. ⚠️근거없음
- GB: $0.01/GB(1PB까지). 교차 리전이면 리전 간 전송 별도(서울→도쿄 $0.080/GB, [PL] AWSDataTransfer ap-northeast-2 "$0.080 per GB - Asia Pacific (Seoul) data transfer to Asia Pacific (Tokyo)").
- 다른 AZ의 ENI로 가는 트래픽의 AZ 간 전송 요금 적용 여부: 미확인(서울 AZ 간 $0.01/GB 단가는 [PL] AWSDataTransfer "$0.01 per GB - regional data transfer - in/out/between EC2 AZs or using elastic IPs or ELB").

### 교체 계열 정보
- NAT Gateway(모든 목적지, 시간·GB 더 비쌈), S3/DynamoDB는 게이트웨이 엔드포인트(무료, 6.1).
- GCP 대응: Private Service Connect(Google API 대상), Private Google Access (추론, 이 절에서 미확인). ⚠️근거없음

### 함정
- Terraform `private_dns_enabled` 기본 `false` → 켜지 않으면 SDK가 공용 이름을 공인 IP로 해석해 NAT로 나가거나(NAT 있으면 요금 이중) 실패(NAT 없으면). `ecr.dkr`은 사설 DNS 필수.
- VPC `enable_dns_hostnames`·`enable_dns_support`가 꺼져 있으면 사설 DNS가 동작하지 않는다(aws_vpc 기본 `enable_dns_hostnames=false`는 (추론), 원문 미확인). ⚠️근거없음
- SG 미지정 시 VPC 기본 SG가 붙고, 기본 SG를 막아 둔 경우(CKV2_AWS_12 준수) 모든 호출이 타임아웃.
- ECR 풀에 S3 게이트웨이를 빼먹으면 매니페스트는 받고 레이어에서 멈춘다. 게이트웨이를 사설 라우트 테이블에 연결하지 않아도 같은 증상.
- 유휴 350초: DB가 아닌 AWS API 대상이라 보통 영향 작지만, SQS 롱폴링(최대 20초)은 무관, 장시간 유휴 HTTP 풀은 RST 가능.
- MTU 8500 초과·PMTUD 미지원: 점보 프레임 경로에서 큰 패킷 드롭 가능.
- 교차 리전 엔드포인트는 존 DNS 불가, SCP가 `vpce:AllowMultiRegion`을 막으면 생성 실패.
- 엔드포인트 정책 미지원 서비스는 정책을 넣어도 전체 허용.

### 생성 산출물
- Terraform 리소스: `aws_vpc_endpoint` (https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_endpoint), 선택 `aws_vpc_endpoint_subnet_association`(`vpc_endpoint_id`, `subnet_id`), `aws_security_group`(엔드포인트용).
- 요구에 따라 반드시 명시할 속성:
  - `vpc_endpoint_type = "Interface"`(기본이 Gateway이므로 반드시), `service_name = "com.amazonaws.ap-northeast-2.<svc>"`.
  - `subnet_ids` → AZ당 사설 서브넷 1개씩. F1(중단 허용 짧음)이면 최소 2 AZ, 앱 서브넷과 같은 AZ 집합.
  - `security_group_ids` → 앱(태스크·Lambda) SG를 소스로 TCP 443 인바운드 허용하는 전용 SG.
  - `private_dns_enabled = true` → 거의 항상(`ecr.dkr` 필수). 끄면 앱에 `--endpoint-url` 필요.
  - `policy` → F5이면 리소스·주체 제한 정책(지원 서비스만).
  - `ip_address_type`/`dns_options.dns_record_ip_type` → IPv6/dualstack 서브넷일 때.
  - `service_region` → 교차 리전(D5 여러 지역·F2) 시만, 지원 서비스 목록 확인.
  - 구성 세트: 컨테이너 이미지(ECR) 사용 + NAT 없음 → `ecr.api`, `ecr.dkr`, S3 Gateway(6.1), `logs`; 시크릿(F5) → `secretsmanager`/`ssm`; Lambda가 다른 AWS API 호출 → 해당 서비스 엔드포인트(`sts`, `sqs` 등).
- Checkov: `aws_vpc_endpoint` 전용 체크 없음. 관련: CKV2_AWS_12 "Ensure the default security group of every VPC restricts all traffic"(`aws_vpc`) — 엔드포인트에 SG를 명시하지 않으면 이 체크 준수 상태에서 통신 불가, CKV2_AWS_11 "Ensure VPC flow logging is enabled in all VPCs".
- 배포 후 검증:
  - 사설 서브넷(태스크/Lambda/인스턴스)에서 `nslookup api.ecr.ap-northeast-2.amazonaws.com`, `nslookup <acct>.dkr.ecr.ap-northeast-2.amazonaws.com`, `nslookup logs.ap-northeast-2.amazonaws.com`, `nslookup secretsmanager.ap-northeast-2.amazonaws.com` → **VPC CIDR 안의 사설 IP**(AZ 수만큼). 공인 IP면 사설 DNS 미적용.
  - `aws ec2 describe-vpc-endpoints --filters Name=vpc-id,Values=<vpc> --query 'VpcEndpoints[].[ServiceName,VpcEndpointType,State,PrivateDnsEnabled,length(SubnetIds),Groups[].GroupId]'` → `Interface`, `available`, `true`, 2 이상.
  - `aws ec2 describe-vpc-endpoints --vpc-endpoint-ids <id> --query 'VpcEndpoints[*].DnsEntries'` → 리전·존 이름 + 공용 서비스 이름 항목.
  - `curl -sv https://secretsmanager.ap-northeast-2.amazonaws.com 2>&1 | grep -E "Connected to|subject:"` → 사설 IP로 연결, 인증서 CN이 서비스 이름.
  - NAT 라우트를 뺀 상태에서 ECS 태스크 기동·이미지 풀 성공. VPC Flow Logs에서 대상 주소가 엔드포인트 ENI(`describe-network-interfaces --filters Name=vpc-endpoint-id,...`의 IP), NAT ENI 경유 없음.

---

## 6.3 AWS PrivateLink — 엔드포인트 서비스(제공자 측) · 리소스 엔드포인트 · SaaS
- 계열: 네트워크-사설 연결
- 서울 리전: 있음 ([PL] AmazonVPC ap-northeast-2 엔드포인트 서비스·리소스 엔드포인트 SKU). 단 교차 리전은 서울 AZ apne2-az2·apne2-az4 미지원

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L4 | 제공자는 NLB(또는 GWLB) 앞에 엔드포인트 서비스를 만들고, 소비자는 인터페이스 엔드포인트(6.2와 같은 ENI)로 접속. 리소스 엔드포인트(2024-12)는 LB 없이 RDS·IP·도메인 대상에 직접 | — | https://docs.aws.amazon.com/vpc/latest/privatelink/create-endpoint-service.html · "Endpoint services require either a Network Load Balancer or a Gateway Load Balancer." / https://docs.aws.amazon.com/vpc/latest/privatelink/concepts.html · "Resource endpoints don't require a load balancer, and lets you access the resource directly." · 2026-10-01 |
| NW.idle_timeout | L4 | 소비자 엔드포인트 350초 고정(6.2) + 제공자 NLB TCP 유휴 기본 350초(60~6,000초 조정), NLB TLS 리스너 350초 고정. **NLB 유휴 타임아웃을 바꾸면 교차 리전 불가** | DB 커넥션 풀 유휴 > 350초면 끊김 | https://docs.aws.amazon.com/elasticloadbalancing/latest/network/update-idle-timeout.html · "The default idle timeout value for TCP flows is 350 seconds." / "The connection idle timeout for TLS listeners is 350 seconds and can't be modified." / https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-share-your-services.html · "Cross-Region access is not supported for Network Load Balancers with a custom value configured for the TCP idle timeout." · 2026-10-01 |
| NW.request_timeout | — | 해당 없음(L4) | — | — |
| NW.websocket | L4 | 해당 없음(L4 통과라 TCP 위 웹소켓은 전달, 유휴 350초 적용) (추론) | — | — ⚠️근거없음 |
| NW.protocols | L4 | 엔드포인트 서비스: NLB 리스너 프로토콜(TCP/UDP/TLS). 리소스 엔드포인트: **TCP만**(UDP 불가) | — | https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-access-resources.html · "TCP traffic is supported. UDP traffic is not supported." · 2026-10-01 |
| NW.body_size | — | 해당 없음 | — | — |
| NW.draining | — | 미확인(NLB 대상 그룹 등록 해제 지연은 NLB 절 소관) | — | — |
| NW.health_check | L4 | NLB 대상 그룹 헬스 체크. 소비자 리전 이름은 정상 ENI 라운드 로빈 | — | https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-share-your-services.html · "we select a healthy endpoint network interface, using the round robin algorithm" · 2026-10-01 |
| NW.tls | TLS | PrivateLink는 TLS 종단 안 함. 제공자가 NLB TLS 리스너 또는 백엔드에서 종단. 사설 DNS 이름은 제공자가 도메인 소유 검증 후 사용 | — | https://docs.aws.amazon.com/vpc/latest/privatelink/create-endpoint-service.html · "Before service consumers can use the private DNS name, the service provider must verify that they own the domain." · 2026-10-01 |
| NW.client_ip | L4 | 제공자 앱이 보는 출발지는 **NLB 노드 사설 IP**. 소비자 IP·엔드포인트 ID는 NLB 프록시 프로토콜 v2 헤더로만 | — | https://docs.aws.amazon.com/vpc/latest/privatelink/create-endpoint-service.html · "the source IP addresses provided to the application are the private IP addresses of the load balancer nodes, not the IP addresses of the service consumers." · 2026-10-01 |
| NW.routing | L4 | 소비자 ENI마다 같은 AZ의 NLB 하나를 무작위 고정. 존 이름으로 AZ 고정 가능. NLB 크로스 존 시 AZ 간 전송 요금 | — | 같은 페이지 · "we select one of the Network Load Balancers in the same Availability Zone as the endpoint network interface at random." · 2026-10-01 |
| NW.scaling | L4 | 소비자 엔드포인트 AZ당 10→100Gbps(6.2). 리소스 엔드포인트 VPC당 200개 | — | https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-limits-endpoints.html · "Resource VPC endpoints per VPC 200 Yes" · 2026-10-01 |
| NW.availability | L4 | 서비스는 NLB가 켜진 AZ에서만 제공, 소비자는 공통 AZ만 보임(AZ ID로 맞춰야 함). 리소스 엔드포인트는 리소스 게이트웨이와 AZ가 최소 하나 겹쳐야 함. 교차 리전은 AZ 장애 조치만, 리전 장애 조치 안 함 | — | https://docs.aws.amazon.com/vpc/latest/privatelink/create-endpoint-service.html · "they can see only the Availability Zones that they have in common with the service provider." / https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-share-your-services.html · "It does not manage failover across Regions." · 2026-10-01 |
| NW.caching | — | 해당 없음 | — | — |
| NW.security | L4 | 기본 비공개: 허용 주체(allowed principals) 지정, 수락 필요 여부 선택. NLB SG가 있으면 클라이언트 IP 인바운드 허용 또는 PrivateLink 트래픽 SG 평가 끄기. 연결은 소비자→제공자 방향만(리소스 엔드포인트도 동일) | — | https://docs.aws.amazon.com/vpc/latest/privatelink/concepts.html · "By default, your endpoint service is not available to service consumers." / https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-access-resources.html · "The resource's VPC can't initiate network connections into the endpoint VPC." · 2026-10-01 |
| NW.dns | — | 제공자 서비스 이름 `vpce-svc-….ap-northeast-2.vpce.amazonaws.com`, 소비자 리전/존 이름. 제공자가 사설 DNS 이름을 연결·검증하면 소비자가 기존 이름 그대로 사용. 리소스 엔드포인트 기본 이름 `…vpc-lattice-rsc.<region>.on.aws`, RDS(ARN) 대상은 사설 DNS로 RDS 기본 이름 사용 가능 | — | https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-share-your-services.html · "If a service provider doesn't enable private DNS, then service consumers might need to update their applications" / https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-access-resources.html · "you can continue to make requests to the resource using the DNS name provisioned for the resource by the AWS service" · 2026-10-01 |
| NW.egress | — | 해당 없음 | — | — |
| NW.private_connectivity | L4 | **방식 A 엔드포인트 서비스**: 제공자 NLB/GWLB 필수, 소비자는 인터페이스 엔드포인트. 기본 같은 리전, VPC 피어링·TGW로 다른 리전 접근 가능. **교차 리전(2024-11-26~)**: 제공자가 `supported_regions` 지정, 소비자가 서비스 리전 선택, `vpce:AllowMultiRegion` 필요, **서울 apne2-az2·apne2-az4 미지원**, NLB 커스텀 유휴 타임아웃·UDP 단편화 미지원. **방식 B 리소스 엔드포인트(2024-12-01~)**: NLB 없이 다른 VPC/계정(RAM 공유)의 RDS·IP·도메인에 TCP 직접, ARN 대상은 RDS만, 리소스 게이트웨이 필요. **방식 C SaaS DB**: 공급자가 엔드포인트 서비스를 제공하고 소비자는 인터페이스 엔드포인트만 생성(예: MongoDB Atlas M10 이상, 노드가 있는 리전마다 엔드포인트) | 요금은 아래 | https://docs.aws.amazon.com/vpc/latest/privatelink/create-endpoint-service.html · "Consumers can access your service from other Regions if you enable cross-Region access, or if they use VPC peering or a transit gateway." / https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-share-your-services.html · "Cross-Region access is not supported for the following Availability Zones: use1-az3, usw1-az2, apne1-az3, apne2-az2, and apne2-az4." / https://docs.aws.amazon.com/vpc/latest/privatelink/doc-history.html · "Cross-Region access ... November 26, 2024" / https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-access-resources.html · "The only supported ARN-based resources are Amazon RDS resources." / https://www.mongodb.com/docs/atlas/security-private-endpoint/ · "This feature is available for M10 clusters or higher." · 2026-10-01 |
| NW.regions | — | 서울 있음. 교차 리전 제공자 요금 SKU 서울 존재 | — | [PL] AmazonVPC ap-northeast-2 · `APN2-VpcEndpoint-Service-Hours` "$0.05 per hour per active remote region for a VPCE service" · 2026-10-01 |
| NW.cost_floor | — | 제공자: 엔드포인트 서비스 자체 시간 요금 없음(추론: Price List에 같은 리전 서비스 SKU 없음) + NLB 비용(NLB 절). 교차 리전 활성 원격 리전당 $0.05/시간(월 $36.50). 소비자: 6.2와 같은 $0.013/AZ·시간 + $0.01/GB, 교차 리전이면 리전 간 전송(서울→도쿄 $0.080/GB)을 소비자가 부담. 리소스 엔드포인트: 리소스당 $0.026/시간(월 $18.98) + $0.01/GB, 리소스 게이트웨이 GB 요금 별도(VPC Lattice 가격) | — | [PL] AmazonVPC ap-northeast-2 · `APN2-VpcEndpoint-Resource-Hours` "$0.026 per hour per VPC resource for VPC endpoint of type 'resource'" / `APN2-VpcResource-Consumer-Bytes` "$0.01 per GB for upto 1 PB monthly data processed for VPC resources" / https://aws.amazon.com/privatelink/pricing/ · "The Interface endpoint owner will be charged for each Gigabyte transferred inter-region regardless of the directionality" · 2026-10-01 ⚠️근거없음 |

### 비용 구조
- 제공자(우리가 서비스 공개): NLB 시간+NLCU(NLB 절), 교차 리전을 켜면 원격 리전당 $0.05/시간. 리전 간 전송은 제공자 부담 없음.
- 소비자(우리가 SaaS DB 접속): 인터페이스 엔드포인트 2 AZ 월 $18.98 + $0.01/GB + SaaS 측 PrivateLink 플랜 조건(Atlas M10 이상 등).
- 같은 계정 내 다른 VPC의 RDS 하나를 공유받는 경우: 리소스 엔드포인트 $0.026/시간(월 $18.98) + $0.01/GB + 리소스 게이트웨이 처리 요금(VPC Lattice, 서울 "$0.006 per GB for data processed by VPC resource" 항목이 [PL]에 있으나 리소스 게이트웨이와의 대응은 미확인).

### 교체 계열 정보
- VPC 피어링([PL] 서울 `APN2-VpcPeering-Out-Bytes` $0.01/GB, 시간 요금 없음, CIDR 겹치면 불가 (추론)), Transit Gateway($0.07/첨부·시간 + $0.02/GB [PL]), VPC Lattice 서비스 네트워크($0.0325/서비스·시간 [PL]). ⚠️근거없음
- GCP 대응: Private Service Connect(게시 서비스/소비자 엔드포인트) (추론). ⚠️근거없음

### 함정
- 제공자 앱 로그·레이트 리밋이 NLB 사설 IP만 본다 → 클라이언트별 제한·감사 로그가 무력화. 프록시 프로토콜 v2를 켜면 백엔드가 그 헤더를 반드시 파싱해야 함(안 하면 연결 깨짐 (추론)). ⚠️근거없음
- 계정 간 AZ 이름(ap-northeast-2a)은 물리 AZ가 다를 수 있음 → AZ ID로 맞추지 않으면 소비자 서브넷 AZ에서 서비스가 안 보임.
- 서울에서 교차 리전 PrivateLink는 apne2-az1·az3 서브넷에만 둘 수 있다(az2·az4 미지원).
- DB용 NLB의 TCP 유휴를 350초보다 늘리면 교차 리전 접근 불가, 소비자 쪽 엔드포인트 350초 고정과도 겹쳐 결국 350초가 상한 (추론). ⚠️근거없음
- 리소스 엔드포인트·엔드포인트 서비스 모두 반대 방향(제공자→소비자) 연결 불가: DB가 앱으로 콜백하는 구조(예: 일부 복제·알림) 불가.
- 수락 필요(`acceptance_required=true`)인데 수락 자동화가 없으면 소비자 엔드포인트가 `pendingAcceptance`에 머문다.

### 생성 산출물
- Terraform 리소스(제공자): `aws_vpc_endpoint_service` (https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_endpoint_service), `aws_vpc_endpoint_service_allowed_principal`, `aws_vpc_endpoint_connection_accepter`(수락 필요 시), `aws_lb`(type network).
  - `acceptance_required`(필수) → 외부 계정·SaaS 공개면 `true`, 같은 조직 내부면 `false` 허용.
  - `network_load_balancer_arns` 또는 `gateway_load_balancer_arns`.
  - `allowed_principals` → 소비자 계정/역할 ARN만(와일드카드 금지).
  - `private_dns_name` → 소비자가 기존 이름을 쓰게 할 때(도메인 검증 필요, `aws_vpc_endpoint_service_private_dns_verification`).
  - `supported_ip_address_types` → `ipv4`/`ipv6`.
  - `supported_regions` → D5 여러 지역·F2 재난 대비로 다른 리전 소비자가 있을 때.
- Terraform 리소스(소비자): `aws_vpc_endpoint` `vpc_endpoint_type="Interface"`, `service_name="com.amazonaws.vpce.ap-northeast-2.vpce-svc-…"`(SaaS가 준 이름), `subnet_ids`(공급자와 공통 AZ ID), `security_group_ids`(DB 포트 인바운드), `private_dns_enabled`(공급자가 사설 DNS 제공 시), `service_region`(교차 리전).
- Terraform 리소스(리소스 엔드포인트): `aws_vpclattice_resource_gateway`, `aws_vpclattice_resource_configuration`(제공자), `aws_vpc_endpoint` `vpc_endpoint_type="Resource"` + `resource_configuration_arn`(소비자). 원문: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc_endpoint.html.markdown · "Exactly one of `resource_configuration_arn`, `service_name` or `service_network_arn` is required."
- Checkov: CKV_AWS_123 "Ensure that VPC Endpoint Service is configured for Manual Acceptance"(`aws_vpc_endpoint_service`) — `acceptance_required=false`면 실패. 그 외 해당 체크 없음.
- 배포 후 검증:
  - 제공자: `aws ec2 describe-vpc-endpoint-service-configurations --query 'ServiceConfigurations[].[ServiceName,ServiceState,AcceptanceRequired,AvailabilityZones,SupportedRegions]'` → `Available`, AZ 2개 이상.
  - `aws ec2 describe-vpc-endpoint-connections --filters Name=service-id,Values=<vpce-svc-id> --query 'VpcEndpointConnections[].[VpcEndpointId,VpcEndpointState]'` → `available`(pendingAcceptance 아님).
  - 소비자: `nslookup <provider-private-dns-or-vpce-dns>` → 소비자 VPC 사설 IP. `nc -vz <name> 27017`(또는 DB 포트) 성공.
  - 소비자 계정 AZ ID 확인: `aws ec2 describe-availability-zones --region ap-northeast-2 --query 'AvailabilityZones[].[ZoneName,ZoneId]'` → 교차 리전이면 엔드포인트 서브넷이 apne2-az1/az3인지.
  - 리소스 엔드포인트: `aws ec2 describe-vpc-endpoint-associations --vpc-endpoint-id <id>` → `Accessible`, DNS 이름 확인 후 `psql -h <dns>` 연결.

---

## 6.4 AWS Lambda VPC 연결 — Hyperplane ENI
- 계열: 네트워크-사설 연결
- 서울 리전: 있음 (Lambda는 서울 제공. 05-compute-tier1-2.md Lambda 절 참조)

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L3/L4 | 함수는 Lambda 소유 VPC에서 실행, 고객 VPC에는 Hyperplane ENI가 터널 끝점으로 생김(아웃바운드 전용) | 전용 테넌시 VPC에는 직접 연결 불가 | https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html · "Every Lambda function runs inside a VPC that is owned and managed by the Lambda service." / "Lambda functions can't connect directly to a VPC with dedicated instance tenancy." · 2026-10-01 |
| NW.idle_timeout | L4 | 미확인(Hyperplane ENI 자체 유휴 타임아웃 문서 없음). 인바운드 Lambda API 엔드포인트 쪽은 유휴 연결을 정리하므로 keep-alive 필요 | — | https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc-endpoints.html · "Lambda purges idle connections over time, so you must use a keep-alive directive to maintain persistent connections." · 2026-10-01 |
| NW.request_timeout | — | 해당 없음(함수 타임아웃은 컴퓨팅 절) | — | — |
| NW.websocket | — | 해당 없음 | — | — |
| NW.protocols | L4 | 아웃바운드 TCP/UDP(VPC 안 리소스). IPv6 아웃바운드는 듀얼스택 서브넷 + `Ipv6AllowedForDualStack=true`만, IPv6 전용 서브넷 불가 | 기본 꺼짐 | https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html · "Lambda doesn't support outbound IPv6 connections for IPv6-only subnets in a VPC" · 2026-10-01 |
| NW.body_size | — | 해당 없음 | — | — |
| NW.draining | — | 해당 없음 | — | — |
| NW.health_check | — | Lambda가 ENI 상태 점검 후 삭제·재생성 가능(설계는 ENI 지속성에 의존하지 말 것) | — | https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html · "Lambda might delete and recreate ENIs to load balance network traffic across ENIs or to address issues found in ENI health-checks." · 2026-10-01 |
| NW.tls | — | 해당 없음 | — | — |
| NW.client_ip | L3 | VPC 안 대상(RDS 등)이 보는 출발지 = Hyperplane ENI 사설 IP(서브넷 대역) (추론). 퍼블릭 서브넷이어도 공인 IP 없음 | — | https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html · "Connecting a function to a public subnet doesn't give it internet access or a public IP address." · 2026-10-01 ⚠️근거없음 |
| NW.routing | L3 | 연결 후 아웃바운드는 VPC 라우트 테이블을 따름. 인터넷은 사설 서브넷 → NAT(IPv6는 egress-only IGW) | — | https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc-internet.html · "The private subnets can access the internet through the NAT gateway. Connecting a function to a public subnet doesn't give it internet access." · 2026-10-01 |
| NW.scaling | L4 | ENI는 서브넷+SG 조합당 공유, ENI당 연결·포트 65,000, 넘으면 자동 증설. VPC당 ENI 쿼터 3,000(EFS 등과 공유, 증설 가능). 실행 환경당 대역폭 625Mbps, **증설 요청은 VPC 미연결 함수만** | — | https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html · "Each Hyperplane ENI supports up to 65,000 connections/ports." / https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html · "Elastic network interfaces per virtual private cloud (VPC) ... 3,000" / "625 Mbps. For functions not attached to a VPC, you can request an increase" · 2026-10-01 |
| NW.availability | L3 | 지정한 서브넷 AZ들에 ENI. 여러 AZ 서브넷 지정 필요(05 파일 CP.availability) | — | https://docs.aws.amazon.com/lambda/latest/dg/security-resilience.html · "Lambda runs your function in multiple Availability Zones to ensure that it is available to process events in case of a service interruption in a single zone." · 2026-10-01 |
| NW.caching | — | 해당 없음 | — | — |
| NW.security | L3/L4 | 함수 SG가 ENI에 적용 → RDS SG는 함수 SG를 소스로 DB 포트 허용. 실행 역할에 `AWSLambdaVPCAccessExecutionRole`(ec2:CreateNetworkInterface 등 6개, Resource "*"), 배포자에게 ec2:DescribeSecurityGroups/Subnets/Vpcs/GetSecurityGroupsForVpc. 이 권한은 함수 코드에도 암묵 부여 → `lambda:SourceFunctionArn` 조건 Deny 권장. 조건 키 `lambda:VpcIds`/`SubnetIds`/`SecurityGroupIds`로 VPC 연결 강제 가능 | — | https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html · "You can give your function the permissions it needs by attaching the AWS managed policy AWSLambdaVPCAccessExecutionRole" / "you're also implicitly granting these permissions to your function's code." · 2026-10-01 |
| NW.dns | — | VPC의 Route 53 Resolver 사용 (추론: 문서 직접 인용 미확인) → 사설 호스팅 영역·인터페이스 엔드포인트 사설 DNS가 함수에도 적용 | — | 미확인 ⚠️근거없음 |
| NW.egress | L3 | VPC 연결 시 기본 인터넷 접근 상실. 인터넷·외부 API·VPC 엔드포인트 없는 AWS API는 NAT 필요(서울 NAT $0.059/시간·AZ + $0.059/GB) | — | https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html · "When you attach your function to a VPC, it can only access resources available within that VPC." · 2026-10-01 |
| NW.private_connectivity | L3/L4 | **대상: 같은 VPC의 RDS·ElastiCache·EC2 등(RDS 직접 연결은 함수가 DB와 같은 VPC여야 함)**. 다른 VPC는 피어링·TGW·PrivateLink(6.3)로. **ENI 수명**: 신규/설정 변경 시 ENI 생성 동안 `Pending`(호출 불가, "수 분"), 14일 미사용 시 ENI 회수 → `Inactive`, 다음 호출 실패 후 다시 Pending. VPC 해제 후 ENI 삭제 최대 20분. **콜드 스타트**: 현행 문서는 ENI를 함수 생성·VPC 설정 시 만든다는 표현만, VPC로 인한 콜드 스타트 추가 지연 수치 없음(2019 블로그: 호출 시 생성 제거, 14.8초→933ms 사례). **인바운드**: Function URL은 VPC에 넣어도 공용 인터넷 전용, PrivateLink 미지원 → 사설 호출은 `com.amazonaws.ap-northeast-2.lambda` 인터페이스 엔드포인트로 Invoke API. **RDS Proxy 권장**(잦은 짧은 연결, 운영). SG: 함수 SG→RDS SG 인바운드. 요금: Lambda VPC 연결 자체 별도 요금 표현 없음, VPC·피어링 사용은 EC2 요금 페이지 기준 추가 과금 | **[충돌]** ENI 생성 시간·호출 가능 여부: 현행 문서 "Pending 상태에선 호출 불가, 수 분" vs 2019 블로그 "최대 90초, 생성 중 호출도 성공" | https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html · "while Lambda is creating a Hyperplane ENI, your function remains in the Pending state and you can't invoke it. ... which can take several minutes." / "if a Lambda function remains idle for 14 days, Lambda reclaims any unused Hyperplane ENIs and sets the function state to Inactive." / "Lambda requires up to 20 minutes to delete the attached Hyperplane ENI." / https://aws.amazon.com/blogs/compute/announcing-improved-vpc-networking-for-aws-lambda-functions/ · "This one-time setup can take up to 90 seconds to complete. If your Lambda function is invoked while the shared network interface is still being created, the invocation still succeeds" / https://docs.aws.amazon.com/lambda/latest/dg/urls-configuration.html · "You can access your function URL through the public Internet only. While Lambda functions do support AWS PrivateLink, function URLs do not." / https://docs.aws.amazon.com/lambda/latest/dg/configuration-database.html · "To connect to a database, your function must be in the same Amazon VPC where your database runs." / "We recommend using Amazon RDS Proxy for Lambda functions that make frequent short database connections" · 2026-10-01 |
| NW.regions | — | 서울 있음 | — | 05-compute-tier1-2.md Lambda 절 (서울 [PL] AWSLambda) · 2026-10-01 |
| NW.cost_floor | — | VPC 연결 자체 $0 표기 없음(Lambda 가격 페이지는 "VPC 사용은 EC2 요금 페이지 기준 추가 요금"이라고만 함). 실질 고정비는 NAT(AZ당 월 $43.07) 또는 인터페이스 엔드포인트(AZ·개당 월 $9.49), RDS Proxy(시간 요금, 미확인) | — | https://aws.amazon.com/lambda/pricing/ · "The usage of Amazon Virtual Private Cloud (VPC) or VPC peering, with AWS Lambda functions will incur additional charges as explained on the Amazon Elastic Compute Cloud (EC2) on-demand pricing page." · 2026-10-01 |

### 비용 구조
- Lambda 요금(요청·GB-초)은 VPC 연결과 무관(추론: 가격 페이지에 VPC 연결 단가 없음). ⚠️근거없음
- 연결하는 순간 생기는 부대 비용: 외부 API·인터넷(E1·E2) → NAT 2AZ 월 $86.14 + $0.059/GB. AWS API만이면 인터페이스 엔드포인트(개당 2AZ 월 $18.98)로 대체 가능. S3·DynamoDB는 게이트웨이(무료).
- RDS Proxy 시간 요금은 DB 인스턴스 크기 기준(Lambda 문서 "Amazon RDS charges an hourly rate for proxies based on the database instance size"), 서울 단가 미확인.

### 교체 계열 정보
- Lambda를 VPC 밖에 두고 RDS를 공개(TLS+IP 제한) — F5에서 비권장 (추론). ⚠️근거없음
- Data API(Aurora `rds-data` 인터페이스 엔드포인트 또는 공용 HTTPS)로 VPC 연결 없이 질의 (추론, 서비스 이름 `com.amazonaws.region.rds-data`는 PrivateLink 목록에서 확인). ⚠️근거없음
- GCP 대응: Cloud Run Direct VPC egress / Serverless VPC Access (05 파일).

### 함정
- 퍼블릭 서브넷에 붙이면 인터넷이 된다고 오해: 공인 IP가 없어 외부 API·AWS API(엔드포인트 없음) 호출이 타임아웃.
- VPC 연결 후 Secrets Manager·STS·SQS 등 AWS API 호출도 NAT나 인터페이스 엔드포인트가 없으면 타임아웃(VPC 안 리소스만 접근 가능).
- 14일 유휴 함수는 Inactive → 첫 호출 실패. 월말 배치·드문 웹훅(E4) 함수에 치명적. 재시도 로직 필요.
- `terraform destroy`·VPC 해제 후 Hyperplane ENI 삭제가 최대 20분 → 서브넷·SG 삭제가 `DependencyViolation`으로 멈춤. 실행 역할을 먼저 지우면 ENI가 영영 안 지워짐. Terraform `replace_security_groups_on_destroy`/`replacement_security_group_ids`로 SG 삭제 대기 완화.
- 서브넷·SG 조합이 함수마다 다르면 ENI가 조합 수만큼 생겨 서브넷 IP·VPC ENI 쿼터(3,000) 소비. 같은 조합 재사용 권장.
- VPC 연결 함수는 실행 환경당 625Mbps 대역폭 상한을 올릴 수 없다(A7 대용량 전송).
- Function URL은 VPC 연결과 무관하게 공용 → "VPC 안에 넣었으니 비공개" 판정은 틀림. 사설 진입은 Lambda 인터페이스 엔드포인트+Invoke API 또는 사설 API Gateway (추론). ⚠️근거없음
- 동시성이 높은 함수 × DB 직접 연결 = DB 최대 연결 초과(C8) → RDS Proxy.
- use1-az3(us-east-1)은 Lambda VPC 용량 제한 AZ로 문서에 명시. 서울 해당 AZ 언급 없음.

### 생성 산출물
- Terraform 리소스: `aws_lambda_function` `vpc_config` 블록 (https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function, 원문 https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function.html.markdown), `aws_iam_role_policy_attachment`(`arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole`), `aws_security_group`(함수용·RDS용), 선택 `aws_db_proxy`, `aws_vpc_endpoint`(6.1·6.2), `aws_nat_gateway`.
- 요구에 따라 반드시 명시할 속성:
  - `vpc_config.subnet_ids`(필수) → **사설 서브넷**, F1이면 2 AZ 이상. 외부 API(E1)가 있으면 해당 서브넷 라우트에 NAT 필수.
  - `vpc_config.security_group_ids`(필수) → 함수 전용 SG(이그레스: DB 포트, 443). RDS SG 인바운드 소스로 이 SG.
  - `vpc_config.ipv6_allowed_for_dual_stack` → 듀얼스택 서브넷에서 IPv6 대상이 있을 때만 `true`(기본 `false`).
  - `replace_security_groups_on_destroy = true` + `replacement_security_group_ids` → 반복 배포/정리 환경.
  - C8(요청마다 연결) + D2·D3 높음 → `aws_db_proxy` 경유 엔드포인트를 환경 변수로.
  - Function URL(`aws_lambda_function_url`)을 쓰면 `authorization_type = "AWS_IAM"` (F5·D1 내부).
- Checkov: CKV_AWS_117 "Ensure that AWS Lambda function is configured inside a VPC"(`aws_lambda_function`). 관련: CKV_AWS_258 "Ensure that Lambda function URLs AuthType is not None"(`aws_lambda_function_url`), CKV_AWS_301 "Ensure that AWS Lambda function is not publicly accessible"(`aws_lambda_permission`). CKV2_AWS_* 중 Lambda VPC 전용 체크 없음(인덱스의 CKV2_AWS_37·CKV2_AWS_75는 리소스 매핑 오류 항목).
- 배포 후 검증:
  - `aws lambda get-function-configuration --function-name <fn> --query '[State,LastUpdateStatus,VpcConfig]'` → `Active`, `Successful`, 서브넷·SG가 기대값, `Ipv6AllowedForDualStack` 기대값.
  - `aws ec2 describe-network-interfaces --filters Name=interface-type,Values=lambda Name=vpc-id,Values=<vpc> --query 'NetworkInterfaces[].[NetworkInterfaceId,SubnetId,PrivateIpAddress,Status]'` → 서브넷·SG 조합 수만큼 ENI, `in-use`. (`interface-type=lambda` 필터 값은 (추론), 실패 시 `Name=description,Values="AWS Lambda VPC ENI*"`). ⚠️근거없음
  - 함수 안 TCP 테스트(Python): `socket.create_connection((os.environ["DB_HOST"], 5432), timeout=3)` → 성공, `socket.gethostbyname(DB_HOST)` → VPC 사설 IP. 실패 시 SG(함수 SG→RDS SG)·서브넷 라우트 확인.
  - 같은 함수에서 `urllib.request.urlopen("https://checkip.amazonaws.com", timeout=5)` → NAT 있으면 NAT EIP 반환, 없으면 타임아웃(기대값과 일치하는지).
  - `aws lambda get-function-url-config --function-name <fn>` → `AuthType: AWS_IAM`(있다면), URL은 공용 해석.
  - VPC Flow Logs(Lambda ENI) → RDS 사설 IP:5432 ACCEPT, 거부 시 REJECT 레코드로 SG 판별.

---

## 6.5 Google Serverless VPC Access 커넥터 — 표준 커넥터(f1-micro / e2-micro / e2-standard-4)
- 계열: 네트워크-사설 연결
- 서울 리전: 있음 (공식: "Serverless VPC Access connectors are supported in every region that supports Cloud Run, Cloud Run functions, or App Engine standard environment." · Cloud Run 위치 목록에 "asia-northeast3 (Seoul, South Korea)" … "Subject to Tier 2 pricing" — https://cloud.google.com/run/docs/locations · 2026-10-01)

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L3/L4 | 서버리스 → VPC 라우팅용 관리형 VM 그룹(통과, 프록시 아님). 요청·응답 모두 내부 경로 | 커넥터 → VPC 방향은 응답 트래픽만(인바운드 개시 불가) | https://cloud.google.com/vpc/docs/serverless-vpc-access · "sends internal traffic from your VPC network to your serverless environment only when that traffic is a response to a request that was sent from your serverless environment" · 2026-10-01 |
| NW.idle_timeout | — | 미확인(커넥터 자체 유휴 타임아웃 문서 없음). 대신 유지보수 교체로 **1분 넘는 개별 연결에 의존하지 말 것** | 2주마다 재시작, 교체 1분 전 신규 요청 수신 중단 | https://cloud.google.com/vpc/docs/serverless-vpc-access · "Don't rely on individual connections that last longer than one minute." / "once every two week restarts" · 2026-10-01 |
| NW.request_timeout | — | 해당 없음 | — | — |
| NW.websocket | — | 해당 없음(L3 경로. 장기 연결은 위 1분 교체 위험) | — | — |
| NW.protocols | L3/L4 | TCP·UDP 지원, ICMP는 all-traffic 모드에서 외부 IP만. **IPv6 미지원** | | https://cloud.google.com/vpc/docs/serverless-vpc-access · "Supported networking protocols … TCP UDP ICMP … Supported only for external IP addresses … Note: IPv6 traffic is not supported." · 2026-10-01 |
| NW.body_size | — | 해당 없음 | — | — |
| NW.draining | L3 | 인스턴스 교체 시 1분 카운트다운 후 종료, 교체 실패해도 종료 진행 | 조직 정책 `constraints/compute.trustedImageProjects`가 `serverless-vpc-access-images`를 막으면 인스턴스 수가 0까지 줄 수 있음 | https://cloud.google.com/vpc/docs/serverless-vpc-access · "The platform proceeds with the scheduled shutdown even if a replacement cannot be created." / "could reach zero" · 2026-10-01 |
| NW.health_check | — | 구글이 헬스 체크 방화벽 규칙 자동 생성(35.191.0.0/16, 130.211.0.0/22). 사용자 설정 불가 | Shared VPC 서비스 프로젝트 커넥터는 방화벽 규칙 수동 추가 필요 | https://cloud.google.com/vpc/docs/serverless-vpc-access · "Allows traffic to the connector's VM instances from health check probes ranges ( 35.191.0.0/16 , 130.211.0.0/22 )" · 2026-10-01 |
| NW.tls | — | 해당 없음(L3 통과. 암호화는 앱·DB 책임) | — | — |
| NW.client_ip | L3 | 목적지가 보는 출발지 = 커넥터 /28 대역 IP(서비스별 구분 불가) | 방화벽은 네트워크 태그 `vpc-connector`, `vpc-connector-REGION-NAME` 단위 | https://cloud.google.com/vpc/docs/serverless-vpc-access · "Traffic sent through the connector into your VPC network originates from the subnet or CIDR range that you specify." · 2026-10-01 |
| NW.routing | L3 | 이그레스 설정 `private-ranges-only`(기본: RFC1918·RFC6598·199.36.153.4/30·199.36.153.8/30만 VPC로) / `all-traffic`(전부 VPC로) | 사설 DB만이면 private-ranges-only, 고정 출구 IP(Cloud NAT)면 all-traffic 필수 | https://cloud.google.com/run/docs/configuring/vpc-connectors · "Route only requests to private IPs to the VPC : Default." / "Packets to any other destination are routed from Cloud Run to the internet" · 2026-10-01 |
| NW.scaling | L3 | 인스턴스 min ≥2, max ≤10, max > min(기본 2/10). **축소(scale in) 안 함.** 머신 유형 혼합 불가. 처리량 f1-micro 100–500 Mbps, e2-micro 200–1000, e2-standard-4 3200–16000(추정치) | 줄이려면 커넥터 재생성. f1/e2-micro는 패킷률 높으면 CPU 크레딧·conntrack 고갈로 타임아웃 → 운영은 e2-standard-4 권장 | https://cloud.google.com/vpc/docs/serverless-vpc-access · "The minimum must be at least 2. The maximum can be at most 10" / "Connectors don't scale in." · https://cloud.google.com/run/docs/configuring/vpc-connectors · "We recommend e2-standard-4 instances for production environments that involve high concurrency" · 2026-10-01 |
| NW.availability | L3 | 리전 자원, 인스턴스가 여러 존에 분산. SLA 미확인 | 커넥터는 서비스와 **같은 리전·같은 프로젝트**(Shared VPC 제외) | https://cloud.google.com/vpc/network-pricing · "Serverless VPC Access connector instances are distributed across zones for increased reliability." · https://cloud.google.com/sql/docs/postgres/connect-run · "Unless you're using Shared VPC , a connector must share the same project and region as the resource that uses it" · 2026-10-01 |
| NW.caching | — | 해당 없음 | — | — |
| NW.security | L3 | 숨은 방화벽 규칙(우선순위 100 근처)으로 커넥터 → VPC 전체 허용. 제한하려면 우선순위 100보다 높은(숫자 작은) 규칙 추가 | 연결 대상: VPC, Shared VPC, Interconnect·VPN·VPC 피어링 연결 네트워크. 레거시 네트워크 불가 | https://cloud.google.com/vpc/docs/serverless-vpc-access · "Allows all traffic from the connector's VM instances … to all resources in the connector's VPC network" / "use a priority higher than 100" · 2026-10-01 |
| NW.dns | — | 내부 DNS 사용 가능 | | https://cloud.google.com/vpc/docs/serverless-vpc-access · "send requests to your VPC network by using internal DNS and internal IP addresses" · 2026-10-01 |
| NW.egress | L3 | all-traffic + Cloud NAT로 고정 출구 IP. private-ranges-only면 서브넷에 Public NAT 붙이지 말 것(쓰이지 않는데 과금) | 외부 IP행 트래픽은 private-ranges-only에서 커넥터 미경유 | https://cloud.google.com/run/docs/configuring/vpc-connectors · "Don't associate any Cloud Run subnets with Public NAT . You are charged for Cloud NAT even though traffic to external IP addresses doesn't flow through Cloud NAT using the connector." · 2026-10-01 |
| NW.private_connectivity | L3 | 대상: Cloud Run(서비스·잡), Cloud Run functions, App Engine 표준(PHP 5 제외). App Engine flex·Knative는 불필요. **/28 전용** 서브넷 또는 미사용 /28 CIDR | Assured Workloads에서는 생성 불가 | https://cloud.google.com/vpc/docs/serverless-vpc-access · "You can specify an existing /28 subnet if there are no resources that already use the subnet." · https://cloud.google.com/run/docs/configuring/vpc-connectors · "Creating Serverless VPC Access connectors isn't supported in Assured Workloads environments." · 2026-10-01 |
| NW.regions | — | Cloud Run·functions·App Engine 표준 지원 리전 전부(서울 포함) | | https://cloud.google.com/vpc/docs/serverless-vpc-access · "supported in every region that supports Cloud Run" · 2026-10-01 |
| NW.cost_floor | — | 커넥터 인스턴스 = Compute Engine VM 요금 × 인스턴스 수(최소 2, **0으로 안 내려감**). 서울: e2-micro $0.010745715/h → 최소 2대 ≈ **$15.69/월**, 10대 ≈ $78.4/월. f1-micro $0.009234/h → 2대 ≈ $13.48/월. e2-standard-4 $0.17193144/h → 2대 ≈ $251/월. + 데이터 전송(Compute Engine 네트워크 요금, 서버리스→커넥터는 무료) | Budget spend cap이 워크로드를 멈춰도 커넥터 VM은 계속 과금 | https://cloud.google.com/vpc/network-pricing · "Connector instances bill as Compute Engine VMs" / "Data transfer out to a connector from a serverless resource … is not charged." · https://cloud.google.com/products/compute/pricing/general-purpose · Seoul (asia-northeast3) "e2-micro … $0.010745715 / 1 hour", "f1-micro … $0.009234 / 1 hour" · https://cloud.google.com/run/docs/configuring/vpc-connectors · "the connector VMs continue to incur costs even if a Budget spend cap pauses your workloads" · 2026-10-01 |

### 비용 구조
- 고정비: 인스턴스 수 × 머신 요금(시간). 최소 인스턴스 2 고정, 확장 후 줄지 않으므로 **실제 고정비 = 지금까지 도달한 최대 인스턴스 수 × 단가**. (추론) 트래픽 급증 한 번으로 e2-standard-4가 10대가 되면 서울 기준 월 약 $1,255가 계속 나간다. ⚠️근거없음
- 변동비: 커넥터 → 목적지 데이터 전송(Compute Engine 요금. 다른 존·리전이면 존 간·리전 간 요금). 서울 단가는 이 조사에서 미확인.
- Cloud Run 공식 비교: "With Serverless VPC Access connectors, you pay for two types of charges: Compute … and network egress" (https://cloud.google.com/run/docs/configuring/connecting-vpc · 2026-10-01).

### 교체 계열 정보
- 같은 목적이면 6.6 Direct VPC egress가 공식 권장("We recommend that you enable your Cloud Run service or job to send traffic to a VPC network by using Direct VPC egress"). 커넥터를 남겨야 하는 경우: App Engine 표준(Direct VPC 대상 아님 — Direct VPC 문서는 Cloud Run 서비스·함수·잡·워커 풀만 언급), Cloud NAT와 함께 콜드 스타트 지연을 피해야 할 때, IP 대역이 /26을 못 낼 만큼 부족할 때.
- 마이그레이션 안내 문서 존재: https://cloud.google.com/run/docs/configuring/migrate-direct-vpc (목록에서 확인, 본문 미열람).

### 함정
- **축소 안 됨**: max_instances 기본 10. 반드시 작은 max를 지정한다(축소하려면 재생성 = 다운타임).
- 1분 넘는 개별 연결 의존 금지(2주 주기 교체). DB 커넥션 풀은 재연결·keepalive 검증 필요.
- f1-micro/e2-micro는 패킷률·동시성 높으면 대역폭 한도 전에 타임아웃.
- IPv6 불가: IPv6 전용 목적지(예: Supabase 직접 연결 기본 IPv6)로 가는 경로에 커넥터를 쓰면 안 됨(추론: private-ranges-only면 외부 목적지는 커넥터를 안 타므로 무관, all-traffic이면 IPv6 경로 없음). ⚠️근거없음
- 조직 정책 `compute.trustedImageProjects`가 `serverless-vpc-access-images`를 막으면 커넥터가 점점 0대가 된다.
- private-ranges-only + 서브넷 Public NAT 조합은 과금만 되고 안 쓰인다.

### 생성 산출물
- Terraform 리소스: `google_vpc_access_connector` (https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/vpc_access_connector · 원문 https://raw.githubusercontent.com/hashicorp/terraform-provider-google/main/website/docs/r/vpc_access_connector.html.markdown), `google_cloud_run_v2_service`의 `template.vpc_access`.
- 요구에 따라 반드시 명시할 속성:
  - `name`(최대 25자), `region`(= Cloud Run 서비스 리전), `ip_cidr_range`(/28, 예 `10.8.0.0/28`) 또는 `subnet { name }`(/28 전용 서브넷) — 둘 중 하나.
  - `machine_type`: 기본 `e2-micro`. 운영·고동시성(D3)이면 `e2-standard-4`.
  - `min_instances`(2–9) / `max_instances`(3–10): **항상 명시**. 비용 상한이 중요하면(F1) max를 낮게. `min_throughput`/`max_throughput`과 혼용 불가(후자는 비권장).
  - Cloud Run: `template.vpc_access.connector = google_vpc_access_connector.x.id`, `template.vpc_access.egress = "PRIVATE_RANGES_ONLY"`(사설 DB만) 또는 `"ALL_TRAFFIC"`(고정 출구 IP·Cloud NAT 필요 시).
- Checkov: `google_vpc_access_connector` 대상 체크 없음(Policy Index에서 해당 리소스 행 없음). Cloud Run 관련은 `CKV_GCP_102` "Ensure that GCP Cloud Run services are not anonymously or publicly accessible"(IAM 바인딩 대상, 사설 연결과 무관).
- 배포 후 검증:
  - `gcloud compute networks vpc-access connectors describe NAME --region=asia-northeast3 --format="value(state,machineType,minInstances,maxInstances,ipCidrRange)"` → `READY`, 지정한 머신·min·max·/28.
  - `gcloud run services describe SVC --region=asia-northeast3` → 출력에 커넥터 이름과 egress 설정 포함.
  - Cloud Run 안에서 사설 IP TCP 확인: 잡 또는 디버그 엔드포인트에서 `nc -zv 10.x.x.x 5432`(또는 `timeout 3 bash -c '</dev/tcp/10.x.x.x/5432' && echo ok`) → 성공.

## 6.6 Google Direct VPC egress — Cloud Run 서비스·잡·함수·워커 풀
- 계열: 네트워크-사설 연결
- 서울 리전: 있음(추론: 제한 사항에 리전 제약 문구 없음, Cloud Run이 asia-northeast3 지원. 인스턴스 쿼터는 "100-200, depending on selected region configurations" — https://cloud.google.com/run/quotas · 2026-10-01) ⚠️근거없음

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L3 | Cloud Run 인스턴스가 서브넷 IP를 직접 받아 VPC로 송신(중간 VM 없음). **이그레스 전용**(서비스·잡은 Direct VPC ingress 미지원, 워커 풀만 ingress) | | https://cloud.google.com/run/docs/configuring/vpc-direct-vpc · "Cloud Run services and jobs don't support direct VPC ingress. Worker pools support both Direct VPC egress and Direct VPC ingress." · 2026-10-01 |
| NW.idle_timeout | — | 미확인. 네트워크 유지보수 중 연결 끊김 가능 | 클라이언트가 연결 재설정 처리해야 함 | https://cloud.google.com/run/docs/configuring/vpc-direct-vpc · "might experience connection breaks during networking infrastructure maintenance events" · 2026-10-01 |
| NW.request_timeout | — | 해당 없음 | — | — |
| NW.websocket | — | 해당 없음(L3). 단, **1시간 넘는 잡**은 유지보수 마이그레이션으로 연결 끊김(SIGTSTP 10초 전, 이후 SIGCONT → 재연결) | | https://cloud.google.com/run/docs/configuring/vpc-direct-vpc · "Cloud Run jobs that run for more than 1 hour might experience connection breaks." · 2026-10-01 |
| NW.protocols | L3/L4 | IPv4(RFC1918, RFC6598 100.64/10, Class E 240/4 서브넷). 듀얼스택 서브넷으로 IPv6 가능(커스텀 모드 VPC, NAT64 미지원) | 듀얼스택은 콜드 스타트 지연 증가 | https://cloud.google.com/run/docs/configuring/vpc-direct-vpc · "RFC 1918 … RFC 6598 100.64.0.0/10 Class E 240.0.0.0/4" · https://docs.cloud.google.com/run/docs/configuring/vpc-dual-stack-subnet · "dual-stack subnets might experience elevated cold-start latencies … NAT64 is not supported." · 2026-10-01 |
| NW.body_size | — | 해당 없음 | — | — |
| NW.draining | L3 | 축소 후 리비전 IP를 최대 20분 보유. 잡 태스크는 종료 후 7분 보유. 서브넷 삭제는 사용 중단 후 1–2시간 대기 | | https://cloud.google.com/run/docs/configuring/vpc-direct-vpc · "Cloud Run retains its IP addresses for up to 20 minutes" / "1 IP address for the duration of its execution plus 7 minutes after it completes" · 2026-10-01 |
| NW.health_check | — | 해당 없음. 대신 **시작 시 연결 수립이 1분 이상 지연**될 수 있어 이그레스 대상 연결을 시험하는 HTTP startup probe 권장 | | https://cloud.google.com/run/docs/configuring/vpc-direct-vpc · "You might experience connection establishment delays of a minute or more on instance startup when using Direct VPC egress. We recommend configuring a HTTP startup probe" · 2026-10-01 |
| NW.tls | — | 해당 없음 | — | — |
| NW.client_ip | L3 | 목적지가 보는 출발지 = 서브넷 내 **임시(ephemeral)** IP. 개별 IP로 정책 금지, 서브넷 전체 대역 사용 | | https://cloud.google.com/run/docs/configuring/vpc-direct-vpc · "IP addresses are ephemeral, so don't create policies based on individual IPs." · 2026-10-01 |
| NW.routing | L3 | `--vpc-egress` `private-ranges-only` / `all-traffic`(커넥터와 같은 의미) | 네트워크·서브넷 변경은 새 리비전 배포 | https://cloud.google.com/run/docs/configuring/vpc-direct-vpc · "all-traffic : Sends all outbound traffic through the VPC network. private-ranges-only : Sends only traffic to internal addresses" · 2026-10-01 |
| NW.scaling | L3 | Direct VPC 사용 인스턴스 최대 수 쿼터 **100–200(리전별), 리비전·잡 실행 단위**(상향 요청 가능). 인스턴스당 VPC 이그레스 최대 1 Gbps. IP는 16개(/28) 블록 단위 예약 | 인스턴스 오토스케일이 커넥터보다 느림(새 NIC 생성) | https://cloud.google.com/run/quotas · "Maximum number of container instances using Direct VPC egress 100-200, depending on selected region configurations. per revision and region" / "Maximum bits for egress over Direct VPC 1 Gbps per instance" · https://cloud.google.com/run/docs/configuring/connecting-vpc · "Instance autoscaling is slower, including starting from zero, while creating new VPC network interfaces." · 2026-10-01 |
| NW.availability | — | 미확인(별도 SLA 문서 미열람) | | — |
| NW.caching | — | 해당 없음 | — | — |
| NW.security | L3 | 리비전 단위 네트워크 태그(이그레스 방화벽 세분화). 미지원: VPC 방화벽 규칙 로깅, 패킷 미러링, ingress 방화벽에서 태그·서비스 ID, Resource Manager 태그, NGFW Enterprise L7 검사 | | https://cloud.google.com/run/docs/configuring/vpc-direct-vpc · "The following items are not supported by Direct VPC egress: … VPC firewall rules logging … Packet Mirroring" · 2026-10-01 |
| NW.dns | — | 미확인(VPC 내부 DNS 사용 여부 문장 미확인) | | — |
| NW.egress | L3 | all-traffic + Cloud NAT로 고정 출구 IP 가능. 단 **Cloud NAT 사용 시 콜드 스타트 30초 이상 지연** 가능 → 구글은 Cloud NAT에는 커넥터 권장 | Direct VPC 이그레스(→VPC)는 Cloud Run 아웃바운드 연결 수 한도(초당 700, 분당 5,000) 미적용 | https://cloud.google.com/run/docs/configuring/vpc-direct-vpc · "With Cloud NAT, you might experience cold start delays of 30s or more on instance startup when using Direct VPC egress. For better startup performance, we recommend using Serverless VPC Access connectors with Cloud NAT." · https://cloud.google.com/run/quotas · "Doesn't apply to Direct VPC egress traffic sent to the VPC network." · 2026-10-01 |
| NW.private_connectivity | L3 | 서브넷 IPv4 **/26 이상**. 서비스·워커 풀: 정상 상태 **인스턴스 수 × 2** IP + 리비전 교체 버퍼((구+신) × 2). 잡: 태스크당 1 IP(+7분), 최소 /26 | VPN·VPC 피어링 연결 네트워크 도달 가능, 레거시 네트워크 불가 | https://cloud.google.com/run/docs/configuring/vpc-direct-vpc · "your subnet's IPv4 address range must be /26 or larger" / "Cloud Run uses 2 times (2X) as many IP addresses as the number of instances" · https://cloud.google.com/sql/docs/postgres/connect-run · "Direct VPC egress and Serverless VPC Access both support communication to VPC networks connected using Cloud VPN and VPC Network Peering ." · 2026-10-01 |
| NW.regions | — | 리전 제약 문구 없음(추론: Cloud Run 리전 전부). 쿼터만 리전별 | | https://cloud.google.com/run/quotas · "100-200, depending on selected region configurations" · 2026-10-01 ⚠️근거없음 |
| NW.cost_floor | — | **$0 고정비**(VM 없음). 네트워크 이그레스만(커넥터와 같은 단가) | Budget spend cap 지원 | https://cloud.google.com/run/docs/configuring/connecting-vpc · "With Direct VPC egress, you pay only for network egress (at the same rate as connectors). You do not pay any compute charges." · 2026-10-01 |

### 비용 구조
- 고정비 0, 트래픽만. 공식 비교표 "Compare Direct VPC egress and VPC connectors"(https://cloud.google.com/run/docs/configuring/connecting-vpc):
  | 항목 | Direct VPC egress | 커넥터 |
  |---|---|---|
  | 지연·처리량 | Lower / Higher | Higher / Lower |
  | IP 사용 | "Uses more IP addresses in most cases" | "Uses fewer IP addresses" |
  | 비용 | "No additional VM charges" | "Incurs additional VM charges" |
  | 확장 속도 | 인스턴스 오토스케일이 느림(NIC 생성) | 트래픽 급증 시 커넥터 인스턴스 생성 동안 지연 |
  | 네트워크 태그 | 서비스·잡별 | 커넥터 공유 |
  | Spend caps | 지원 | 미지원 |
  | 출시 단계 | GA | GA |

### 교체 계열 정보
- 6.5 커넥터: IP가 부족(/26 불가)하거나 Cloud NAT + 빠른 콜드 스타트가 필요하거나 App Engine 표준일 때.
- Shared VPC에서는 별도 문서(https://cloud.google.com/run/docs/configuring/shared-vpc-direct-vpc, 검색 결과로만 확인).

### 함정
- 서브넷 크기 계산: 최대 인스턴스 N이면 정상 상태 2N, 리비전 교체 중 최대 4N(구·신 동시) + 16개 블록 단위. /26(64개)은 **최대 인스턴스 약 16 이하**에서만 안전(추론: 64 ÷ 4). ⚠️근거없음
- 시작 시 연결 1분 이상 지연 → 앱이 시작 직후 DB 연결 실패 → 재시도·startup probe 필수.
- Cloud NAT와 조합 시 콜드 스타트 30초 이상.
- 1시간 넘는 잡은 연결 끊김 처리 필요.
- 인스턴스 최대 수 쿼터(100–200)가 Cloud Run `max_instance_count`보다 작으면 그 이상 확장 불가(쿼터 상향 요청).
- 인스턴스당 1 Gbps(VPC행) 초과 시 스로틀.
- 방화벽 로깅·패킷 미러링이 필요하면 쓸 수 없다.

### 생성 산출물
- Terraform 리소스: `google_cloud_run_v2_service` / `google_cloud_run_v2_job` (https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_run_v2_service · 원문 .../website/docs/r/cloud_run_v2_service.html.markdown), `google_compute_subnetwork`(/26 이상).
- 요구에 따라 반드시 명시할 속성:
  - `template.vpc_access.network_interfaces { network, subnetwork, tags }` — "Currently only single network interface is supported."
  - `template.vpc_access.egress`: `PRIVATE_RANGES_ONLY`(사설 DB만) / `ALL_TRAFFIC`(고정 출구 IP 요구, F5류).
  - `connector`와 `network_interfaces`는 택일(추론: 원문에 두 방식이 별도 설명). ⚠️근거없음
  - `template.scaling.max_instance_count` ≤ Direct VPC 쿼터, 서브넷 크기 ≥ 4 × max(추론). ⚠️근거없음
  - `template.containers.startup_probe`: DB 포트 연결을 시험하는 HTTP 프로브(공식 권장).
- Checkov: Direct VPC 설정 대상 체크 없음(미확인). `CKV_GCP_102`(공개 IAM)만.
- 배포 후 검증:
  - `gcloud run services describe SVC --region=asia-northeast3` → "The output should contain the name of your network, subnet, and egress setting"(공식).
  - `gcloud compute networks subnets describe SUBNET --region=asia-northeast3 --format="value(ipCidrRange)"` → 접두 길이 ≤ 26.
  - Cloud Run 안에서 `timeout 3 bash -c '</dev/tcp/<사설IP>/5432' && echo ok` → ok.

## 6.7 Google Private Service Connect — 구글 API용 엔드포인트 / 게시된 서비스용 엔드포인트·백엔드
- 계열: 네트워크-사설 연결
- 서울 리전: 있음(추론: 리전 제약 문구 없음. PlanetScale이 asia-northeast3 서비스 연결을 공개 — 6.10) ⚠️근거없음

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L3/L4 | 엔드포인트 = 소비자 VPC 내부 IP를 가진 포워딩 규칙(구글 API용은 **전역** 포워딩 규칙, 게시 서비스용은 리전). 백엔드 = 소비자 LB + PSC NEG(L7 가능) | | https://cloud.google.com/vpc/docs/configure-private-service-connect-apis · "An endpoint connects to Google APIs and services using a global forwarding rule." · https://cloud.google.com/vpc/docs/private-service-connect · "Placing a load balancer in front of a managed service provides the consumer with more" control · 2026-10-01 |
| NW.idle_timeout | — | 미확인 | | — |
| NW.request_timeout | — | 해당 없음(엔드포인트). 백엔드는 해당 LB 값 | — | — |
| NW.websocket | — | 해당 없음 | — | — |
| NW.protocols | L4 | IPv4 엔드포인트(IPv4·듀얼스택 서브넷), IPv6 /96 엔드포인트 가능 | IP 버전이 연결 가능한 서비스에 영향 | https://cloud.google.com/vpc/docs/about-accessing-vpc-hosted-services-endpoints · "You can use a /96 IPv6 address from an IPv6-only or dual-stack subnet" · 2026-10-01 |
| NW.body_size | — | 해당 없음 | — | — |
| NW.draining | — | 글로벌 액세스 끄면 다른 리전 연결 즉시 종료 | | https://cloud.google.com/vpc/docs/about-accessing-vpc-hosted-services-endpoints · "Turning off global access terminates any connections from regions other than the region where the endpoint is located." · 2026-10-01 |
| NW.health_check | — | 미확인(엔드포인트 자체 헬스 체크 없음. 글로벌 액세스 미지원 서비스에 연결하면 비정상 백엔드로 전송될 수 있음) | | https://cloud.google.com/vpc/docs/about-accessing-vpc-hosted-services-endpoints · "traffic might be sent to unhealthy backends and dropped ( known issue )" · 2026-10-01 |
| NW.tls | — | 해당 없음(엔드포인트는 L4 통과) | — | — |
| NW.client_ip | — | 미확인(Cloud SQL PSC에서는 클라이언트 IP가 Cloud SQL에 보이지 않음 — 6.8) | | — |
| NW.routing | L3 | 게시 서비스 엔드포인트: **서비스와 같은 리전**, 서비스와 **다른 VPC**에 생성. 기본은 같은 리전·같은 VPC 클라이언트만, 글로벌 액세스로 타 리전·온프레미스 | | https://cloud.google.com/vpc/docs/about-accessing-vpc-hosted-services-endpoints · "Private Service Connect endpoints must be created in the same region as the published service" / "By default, the endpoint can be accessed only by clients that are in the same region and the same VPC network" · 2026-10-01 |
| NW.scaling | — | 엔드포인트는 VPC당 PSC 쿼터에 포함. 구글 API 엔드포인트는 생성 후 수정 불가(삭제 후 재생성) | | https://cloud.google.com/vpc/docs/configure-private-service-connect-apis · "Each forwarding rule counts toward the per VPC network quota" / "You can't update an endpoint for Google APIs and services after it is created." · 2026-10-01 |
| NW.availability | — | 미확인 | | — |
| NW.caching | — | 해당 없음 | — | — |
| NW.security | L3 | 구글 API 번들 `all-apis` / `vpc-sc`(VPC-SC 지원 API만). 게시 서비스는 프로듀서 허용 목록으로 승인 | | https://raw.githubusercontent.com/hashicorp/terraform-provider-google/main/website/docs/r/compute_global_forwarding_rule.html.markdown · "`vpc-sc` - APIs that support VPC Service Controls" / "`all-apis` - All supported Google APIs" · 2026-10-01 |
| NW.dns | — | PSC가 Service Directory 네임스페이스·DNS 존 자동 생성. 기존 `p.googleapis.com` 사설 존이 있으면 삭제 후 생성 | | https://cloud.google.com/vpc/docs/configure-private-service-connect-apis · "check if a Cloud DNS private zone exists for p.googleapis.com . If the zone exists, delete it" · 2026-10-01 |
| NW.egress | — | 해당 없음 | — | — |
| NW.private_connectivity | L3 | **구글 API 엔드포인트는 피어링된 VPC에서 접근 불가.** 외부 IP 없는 VM은 서브넷에 Private Google Access 필요 | 구글 API 엔드포인트는 연결된 온프레미스에서 접근 가능 | https://cloud.google.com/vpc/docs/configure-private-service-connect-apis · "Endpoints are not accessible from peered VPC networks." · https://cloud.google.com/vpc/docs/about-accessing-vpc-hosted-services-endpoints · "Endpoints that you use to access Google APIs can be accessed from supported connected on-premises hosts." · 2026-10-01 |
| NW.regions | — | 게시 서비스 = 서비스 리전에 종속 | | 위 NW.routing 출처 |
| NW.cost_floor | — | 구글 API 엔드포인트 $0.01/시간(≈$7.30/월), **데이터 요금 없음**. 게시 서비스 엔드포인트 $0.01/시간 + 소비자 데이터 처리 **$0.01/GiB**(0–1 PiB, 인바운드·아웃바운드 모두), 1–5 PiB $0.006, 5 PiB+ $0.004. 존 간 전송 무료, 글로벌 액세스로 타 리전 접근 시 리전 간 전송 추가. 백엔드 방식은 LB 요금 전부. 리전별 차등 표기 없음 | | https://cloud.google.com/vpc/network-pricing · "Private Service Connect endpoint (forwarding rule) used to access Google APIs $0.01 / 1 hour No data charge" / "0 gibibyte to 1 pebibyte $0.01 / 1 gibibyte" / "Private Service Connect does not charge for inter-zone data transfer" · 2026-10-01 |

### 비용 구조
- 엔드포인트 1개 ≈ $7.30/월 고정 + (게시 서비스면) GiB당 $0.01. Service Directory 요금 별도(단가 미확인). PSC 백엔드(LB 경유)는 LB 시간·처리 요금.
- 서비스 연결 정책 자동화(Cloud SQL·Memorystore)도 소비자 쪽에 PSC 엔드포인트가 생기므로 같은 단가가 적용된다고 봄(추론: 가격표 목차에 "service connectivity automation" 항목 존재, 본문 단가 미확인). ⚠️근거없음

### 교체 계열 정보
- 구글 API 사설 접근만이면 PSC 엔드포인트 대신 서브넷의 Private Google Access(무료, 추론)로 충분한 경우가 많다. 서버리스는 Direct VPC/커넥터 + PGA. ⚠️근거없음
- 게시 서비스 접근: PSC 엔드포인트(L4, 저렴) vs PSC 백엔드(LB, L7 제어·리전 장애 조치).

### 함정
- 구글 API 엔드포인트는 피어링 VPC에서 안 보인다(허브-스포크 피어링 설계에서 실패).
- 게시 서비스 엔드포인트는 서비스와 같은 리전에만 생성. 타 리전 클라이언트는 글로벌 액세스 필요 + 서비스가 글로벌 액세스를 지원해야 함.
- 엔드포인트 IP는 일반(regular) 서브넷에서.

### 생성 산출물
- Terraform 리소스: `google_compute_global_address`(purpose `PRIVATE_SERVICE_CONNECT`, 구글 API용) + `google_compute_global_forwarding_rule`(target `all-apis`/`vpc-sc`, `load_balancing_scheme = ""`) (https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_global_forwarding_rule); 게시 서비스용 `google_compute_address`(INTERNAL) + `google_compute_forwarding_rule` (https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_forwarding_rule).
- 요구에 따라 반드시 명시할 속성(`google_compute_forwarding_rule`): `target` = 서비스 연결 URI, `load_balancing_scheme = ""`("an empty string value (`""`) is also supported for some use cases, for example PSC … regional forwarding rules"), `network`, `ip_address`, 타 리전 클라이언트가 있으면 `allow_psc_global_access = true`, DNS 자동 생성 여부 `no_automate_dns_zone`.
- Checkov: PSC 포워딩 규칙 대상 체크 없음. `CKV2_GCP_37`/`CKV2_GCP_38`(HTTP 프록시 + EXTERNAL 스킴 금지)는 PSC와 무관.
- 배포 후 검증:
  - `gcloud compute forwarding-rules describe EP --region=asia-northeast3 --format="value(IPAddress,pscConnectionStatus)"` → `ACCEPTED`.
  - 구글 API: `gcloud compute forwarding-rules list --filter target="(all-apis OR vpc-sc)" --global`(공식 명령) → 엔드포인트 표시. VM에서 `dig storage-ENDPOINT.p.googleapis.com` → 엔드포인트 IP(추론: DNS 이름 형식은 미열람). ⚠️근거없음

## 6.8 Cloud SQL 사설 IP 연결 — PSA(VPC 피어링) / PSC / Auth Proxy·언어 커넥터 / 공인 IP + authorized networks
- 계열: 네트워크-사설 연결
- 서울 리전: 있음(Cloud SQL 위치 페이지에 asia-northeast3 표기 — https://cloud.google.com/sql/docs/postgres/locations · 2026-10-01)

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L3/L4 | PSA = Cloud SQL VPC와 사용자 VPC의 VPC 피어링. PSC = 서비스 연결 + 소비자 엔드포인트. Auth Proxy·커넥터 = 새 경로 아님(기존 IP 경로 위 TLS·IAM) | | https://cloud.google.com/sql/docs/postgres/private-ip · "Enabling private IP requires setting up a peering connection between the Cloud SQL VPC and your VPC network." · https://cloud.google.com/sql/docs/postgres/sql-proxy · "The Cloud SQL Auth Proxy does not provide a new connectivity path; it relies on existing IP connectivity." · 2026-10-01 |
| NW.idle_timeout | — | 미확인 | | — |
| NW.request_timeout | — | 해당 없음 | — | — |
| NW.websocket | — | 해당 없음 | — | — |
| NW.protocols | L4/TLS | PostgreSQL PSC 포트: 5432(직접), 6432(관리형 PgBouncer), 3307(Auth Proxy). Auth Proxy는 TLS 1.3 | 3307 아웃바운드 방화벽 허용 필요 | https://cloud.google.com/sql/docs/postgres/about-private-service-connect · "TCP port 5432 for direct connections … TCP port 6432 … PgBouncer … TCP port 3307 for connections through Cloud SQL Auth Proxy ." · https://cloud.google.com/sql/docs/postgres/sql-proxy · "encrypts traffic to and from the database using TLS 1.3" · 2026-10-01 |
| NW.body_size | — | 해당 없음 | — | — |
| NW.draining | — | 기존 인스턴스에 사설 IP 추가·네트워크 변경 시 재시작(수 분 다운타임). PSC 아웃바운드 켜기·끄기 약 8분 작업, 다운타임 약 3분 | | https://cloud.google.com/sql/docs/postgres/private-ip · "causes the instance to be restarted, resulting in a few minutes of downtime" · https://cloud.google.com/sql/docs/postgres/about-private-service-connect · "about 8 minutes to complete with an approximate downtime of 3 minutes" · 2026-10-01 |
| NW.health_check | — | 해당 없음 | — | — |
| NW.tls | TLS | `ssl_mode`: `ALLOW_UNENCRYPTED_AND_ENCRYPTED` / `ENCRYPTED_ONLY` / `TRUSTED_CLIENT_CERTIFICATE_REQUIRED`. Auth Proxy·커넥터는 인증서 관리 불필요. 웹앱(Cloud Run)에서 연결할 인스턴스는 `server_ca_mode = GOOGLE_MANAGED_INTERNAL_CA`(인스턴스별 CA) 선택 필수 | Cloud Run 1세대 실행 환경은 per-instance CA 인스턴스만 연결 | https://raw.githubusercontent.com/hashicorp/terraform-provider-google/main/website/docs/r/sql_database_instance.html.markdown · "Supported values are `ALLOW_UNENCRYPTED_AND_ENCRYPTED`, `ENCRYPTED_ONLY`, and `TRUSTED_CLIENT_CERTIFICATE_REQUIRED`" · https://cloud.google.com/sql/docs/postgres/connect-run · "You must select the per-instance CA option ( GOOGLE_MANAGED_INTERNAL_CA ) as the server CA mode for instances that you want to connect to from web applications." · 2026-10-01 |
| NW.client_ip | L3 | PSA: Cloud SQL이 클라이언트 IP 봄. **PSC: 클라이언트 IP 안 보임**(IP 기반 로그·지표·허용 목록 불가) | | https://cloud.google.com/sql/docs/postgres/connect-overview · "Visibility of the client IP address to Cloud SQL … Supported. Not supported." (PSA only / PSC only) · https://cloud.google.com/sql/docs/postgres/configure-private-service-connect · "IP-based allowlisting by using authorized networks isn't supported." · 2026-10-01 |
| NW.routing | L3 | PSA: **전이 피어링 불가** — 직접 피어링된 VPC만. 다른 VPC는 커스텀 광고 경로·중간 프록시(SOCKS5)·Auth Proxy 서비스로 우회. 리전 간 사설 IP 연결은 가능. PSC: 여러 VPC·프로젝트·조직에서 접속(엔드포인트 최대 20개, 넘으면 NCC 전파) | 레거시 네트워크 불가 | https://cloud.google.com/sql/docs/postgres/private-ip · "since VPC Network Peering isn't transitive, it only broadcasts routes between the two VPCs that are directly peered. If you have an additional VPC, it won't be able to access your Cloud SQL resources" / "You can connect through private IP across regions." · https://cloud.google.com/sql/docs/postgres/configure-private-service-connect · "You can set up to 20 Private Service Connect endpoints" · 2026-10-01 |
| NW.scaling | — | PSC 동시 연결 최대 64,512. Cloud Run 인스턴스당 Cloud SQL 연결 100. Auth Proxy 사용 시 Admin API 쿼터 ≈ 2 × 인스턴스 수 × Cloud Run 인스턴스 수 | | https://cloud.google.com/sql/docs/postgres/configure-private-service-connect · "up to 64,512 concurrent connections with Private Service Connect" · https://cloud.google.com/sql/docs/postgres/connect-run · "Cloud Run container instances are limited to 100 connections to a Cloud SQL database." · 2026-10-01 |
| NW.availability | — | 해당 없음(DB 가용성은 01 문서) | — | — |
| NW.caching | — | 해당 없음 | — | — |
| NW.security | L3/TLS | Auth Proxy·커넥터: IAM 인가, authorized networks 불필요, 자동 IAM DB 인증 지원. `connector_enforcement = REQUIRED`면 직접 연결 거부. Context-Aware Access + IAM DB 인증 조합에서는 Auth Proxy 불가 | PSC + connector enforcement면 읽기 복제본 생성 불가 | https://cloud.google.com/sql/docs/postgres/sql-proxy · "secure access to your instances without a need for Authorized networks or for configuring SSL" / "You can't use the Cloud SQL Auth Proxy if you're using context-aware access and IAM database authentication." · 2026-10-01 |
| NW.dns | — | PSC는 DNS 이름으로 연결 권장(네트워크마다 IP 다름). Auth Proxy는 PSC에서 DNS 필요. `dns_names[].connection_type` = PUBLIC / PRIVATE_SERVICES_ACCESS / PRIVATE_SERVICE_CONNECT | | https://cloud.google.com/sql/docs/postgres/about-private-service-connect · "the Cloud SQL Auth Proxy requires DNS" · 2026-10-01 |
| NW.egress | — | 해당 없음(앱 쪽은 6.5/6.6). 공인 IP + authorized networks 방식은 클라이언트 고정 출구 IP 필요 → Cloud Run이면 Cloud NAT(추론) | | — ⚠️근거없음 |
| NW.private_connectivity | L3 | PSA 할당 범위 **최소 /24, 권장 /16**(Cloud SQL 표: /24=50개, /23=100, /22=200, /21=400, /20=800 인스턴스). 리전마다 /24 하나씩 소모. **Cloud Run → 사설 IP는 Direct VPC 또는 커넥터 필수**(서버리스는 Auth Proxy 없이 직접). Auth Proxy로 사설 IP 쓰려면 같은 VPC 접근 가능 자원 + `--private-ip`(공인·사설 둘 다면 기본 공인). PSC 인스턴스: 공인 IP·PSA·authorized networks 추가 불가, `gcloud sql connect`·Cloud Shell·Cloud Build·Datastream 불가 | 사설 IP는 한 번 켜면 제거 불가. Shared VPC는 생성 시에만 사설 IP 지정 | https://cloud.google.com/sql/docs/postgres/private-ip · "The minimum size is a single /24 block (256 addresses), but the recommended size is a /16 block" / "After you configure a Cloud SQL instance to use private IP, you can't remove the private IP capability" / "your application or function connects directly to your instance through Serverless VPC Access without the Cloud SQL Auth Proxy." · https://cloud.google.com/sql/docs/postgres/configure-private-service-connect · "You can't use the gcloud sql connect command, Cloud Shell, Cloud Build, or Datastream to connect to Cloud SQL instances with Private Service Connect enabled." · 2026-10-01 |
| NW.regions | — | 사설 IP 리전 간 연결 가능(리전 간 전송 요금) | | 위 출처 "You can connect through private IP across regions." |
| NW.cost_floor | — | PSA 연결 자체 **$0**(시간·데이터 요금 없음, 프로듀서 쪽 자원·전송만). PSC는 소비자 엔드포인트 $0.01/h + $0.01/GiB(6.7) | | https://cloud.google.com/vpc/network-pricing · "When you create a private services access connection , there are no hourly or data charges for the connection itself." · 2026-10-01 |

### 비용 구조
- PSA: 연결 무료, Cloud SQL 인스턴스 요금만. 앱 쪽 Direct VPC($0) 또는 커넥터(서울 최소 ≈$15.69/월).
- PSC: 엔드포인트 ≈$7.30/월 + GiB당 $0.01. 자동 엔드포인트(서비스 연결 정책)도 엔드포인트 요금 적용(추론). ⚠️근거없음
- 공인 IP 방식: Cloud SQL 공인 IP 요금(단가 미확인) + Cloud Run 고정 출구 IP를 위한 Cloud NAT(05 문서 §1.3).

### 교체 계열 정보
- 공인 IP + Auth Proxy/커넥터(Cloud Run `--add-cloudsql-instances` Unix 소켓): VPC 설정 없이 가능, 공인 IP를 authorized networks에 넣지 않아도 됨("The public IP address does not need to be accessible to any external address"). 단 공인 IP 존재 자체가 CKV_GCP_60 실패.
- PSA vs PSC 지원 기능(connect-overview): 다중 VPC — PSA 불가/PSC 가능; pglogical·dblink·postgres_fdw·외부 복제본·쓰기 엔드포인트 — PSA 가능/PSC 불가; 둘 다 켠 인스턴스는 각각 경로로 지원.
- 켤 수 있는 조합: 공인 IP만 → PSA 추가; PSA만 → PSC 추가; PSA+공인 → PSC 추가. **공인 IP + PSC로 새로 생성은 불가**, PSA+PSC에서 PSA 제거 불가.

### 함정
- **ipv4_enabled 기본값**: Cloud SQL은 "By default, Cloud SQL assigns a public IP address to a new instance."(connect-run). Terraform에서 `ipv4_enabled`를 생략하면 공인 IP가 생길 수 있는데, **Checkov CKV_GCP_60은 `ipv4_enabled` 키가 없으면 PASSED**(소스: 키가 있고 true일 때만 FAILED). → 사설 전용이면 `ipv4_enabled = false` 반드시 명시.
- **CKV_GCP_6은 `ssl_mode = "TRUSTED_CLIENT_CERTIFICATE_REQUIRED"`일 때만 통과**(SQL Server는 `ENCRYPTED_ONLY`). `ENCRYPTED_ONLY`로 두면 실패. TRUSTED_CLIENT_CERTIFICATE_REQUIRED는 클라이언트 인증서를 요구하므로 일반 드라이버 + 비밀번호 직접 연결(Cloud Run → 사설 IP 5432)은 깨진다 → Auth Proxy/언어 커넥터 사용과 묶어야 함(추론: 커넥터는 클라이언트 인증서를 자동 처리). ⚠️근거없음
- `google_sql_database_instance`는 `google_service_networking_connection`을 참조하지 않으므로 `depends_on` 명시 필수("You must explicitly add a `depends_on`").
- `google_service_networking_connection` 삭제는 Cloud SQL이 자원을 보존하는 동안 실패("Producer services (e.g. CloudSQL, Cloud Memstore, etc.) are still using this connection.") → destroy 순서·대기.
- PSA 피어링은 전이 불가: 허브 VPC에 Cloud SQL을 두고 스포크 VPC의 Cloud Run이 접근하면 실패. Cloud Run은 Cloud SQL과 피어링된 그 VPC에 Direct VPC로 붙어야 한다.
- 온프레미스·VPN에서 PSA 대역 접근: 피어링 커스텀 경로 export + Cloud Router 커스텀 광고 필요(Memorystore 문서와 같은 절차, 6.9).
- Auth Proxy는 공인·사설 둘 다 있으면 공인 우선 → `--private-ip` 플래그.
- PSC 인스턴스는 `gcloud sql connect`·Cloud Build 마이그레이션 불가 → 배포 파이프라인의 스키마 마이그레이션 경로 재설계 필요.
- 2026-08 이후 생성 PSC 인스턴스: 허용 프로젝트 목록에서 빼면 기존 연결 즉시 종료.

### 생성 산출물
- Terraform 리소스: `google_compute_global_address`(https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_global_address), `google_service_networking_connection`(.../service_networking_connection), `google_sql_database_instance`(.../sql_database_instance), PSC 수동 시 `google_compute_address` + `google_compute_forwarding_rule`, PSC 자동 시 `google_network_connectivity_service_connection_policy`(service_class `google-cloud-sql`).
- 요구에 따라 반드시 명시할 속성:
  - `google_compute_global_address`: `purpose = "VPC_PEERING"`, `address_type = "INTERNAL"`, `prefix_length = 16`(최소 24; 인스턴스·서비스 수에 따라), `network`.
  - `google_service_networking_connection`: `network`, `service = "servicenetworking.googleapis.com"`, `reserved_peering_ranges = [global_address.name]`, 운영 보호 시 `deletion_policy = "ABANDON"` 검토.
  - `settings.ip_configuration`: `ipv4_enabled = false`(사설 전용, CKV_GCP_60), `private_network = <VPC id>`(PSA), `allocated_ip_range`(여러 범위일 때), `ssl_mode`(CKV_GCP_6 통과는 `TRUSTED_CLIENT_CERTIFICATE_REQUIRED` — 커넥터/Proxy 사용 시), `server_ca_mode = "GOOGLE_MANAGED_INTERNAL_CA"`(Cloud Run 웹앱).
  - PSC: `ip_configuration.psc_config { psc_enabled = true, allowed_consumer_projects = [...], psc_auto_connections { consumer_network, consumer_service_project_id } }`, `ipv4_enabled = false`.
  - `settings.connector_enforcement = "REQUIRED"`: 커넥터·Proxy 강제(직접 연결 차단) 요구 시.
  - `depends_on = [google_service_networking_connection.x]`.
- Checkov: `CKV_GCP_60` "Ensure Cloud SQL database does not have public IP", `CKV_GCP_6` "Ensure all Cloud SQL database instance requires all incoming connections to use SSL", `CKV_GCP_11` "Ensure that Cloud SQL database Instances are not open to the world"(authorized networks 0.0.0.0/0).
- 배포 후 검증:
  - `gcloud sql instances describe INST --format="json(ipAddresses,settings.ipConfiguration)"` → `ipAddresses`에 `type: PRIVATE`만(PRIMARY 없음), `ipv4Enabled: false`, `privateNetwork` 일치. PSC면 `pscServiceAttachmentLink`, `dnsName` 존재.
  - `gcloud services vpc-peerings list --network=VPC` → `servicenetworking.googleapis.com` 피어링과 할당 범위.
  - Cloud Run 안에서 `timeout 3 bash -c '</dev/tcp/<PRIVATE_IP>/5432' && echo ok` → ok. 공인 경로 차단 확인: 로컬에서 같은 명령이 실패.

## 6.9 Memorystore 사설 연결 — Redis 인스턴스(DIRECT_PEERING / PRIVATE_SERVICE_ACCESS), Valkey·Redis Cluster(PSC 서비스 연결 정책)
- 계열: 네트워크-사설 연결
- 서울 리전: 일부 — Valkey 위치 페이지에 asia-northeast3 있음(https://cloud.google.com/memorystore/docs/valkey/locations · 2026-10-01). Redis 인스턴스 위치 페이지에서 서울 문자열 미확인 → `미확인`.

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L3/L4 | Redis: VPC 피어링(직접 또는 PSA). Valkey: **PSC 서비스 연결 자동화만** | 항상 내부 IP | https://cloud.google.com/memorystore/docs/redis/networking · "Memorystore for Redis always uses internal IP addresses" · https://cloud.google.com/memorystore/docs/valkey/networking · "The only networking connectivity method that you can use for Memorystore for Valkey is Private Service Connect service connectivity automation." · 2026-10-01 |
| NW.idle_timeout | — | 미확인 | | — |
| NW.request_timeout | — | 해당 없음 | — | — |
| NW.websocket | — | 해당 없음 | — | — |
| NW.protocols | L4/TLS | Redis 프로토콜. TLS: Redis `transit_encryption_mode` `SERVER_AUTHENTICATION`/`DISABLED`(기본 DISABLED), Valkey `SERVER_AUTHENTICATION`/`TRANSIT_ENCRYPTION_DISABLED`(변경 불가) | | https://raw.githubusercontent.com/hashicorp/terraform-provider-google/main/website/docs/r/redis_instance.html.markdown · "If not provided, TLS is disabled for the instance." · 2026-10-01 |
| NW.body_size | — | 해당 없음 | — | — |
| NW.draining | — | 연결 모드 변경 불가 → 재생성 시 IP 변경 | | https://cloud.google.com/memorystore/docs/redis/networking · "You cannot switch the connection mode of an existing instance. … This results in a change in the IP address of the instance." · 2026-10-01 |
| NW.health_check | — | 해당 없음 | — | — |
| NW.tls | TLS | 위 NW.protocols | | |
| NW.client_ip | — | 미확인 | | — |
| NW.routing | L3 | Redis 직접 피어링: 다른 구글 서비스와 피어링 공유 안 함. PSA: 피어링 공유, Shared VPC·온프레미스(VPN/Interconnect) 지원 | 온프레미스는 피어링 커스텀 경로 import/export + Cloud Router 커스텀 광고 필요. 0.0.0.0/0 기본 경로는 import 불가 | https://cloud.google.com/memorystore/docs/redis/networking · "Access a Redis instance from on-premise networks using VPN Private services access only" / "Default routes (destination 0.0.0.0/0 ) cannot be imported" · 2026-10-01 |
| NW.scaling | — | Valkey 서비스 연결 정책 connection limit ≈ 인스턴스 수 × 2. (네트워크, 리전, 서비스 클래스)마다 정책 1개 | | https://cloud.google.com/memorystore/docs/valkey/networking · "multiply the number of instances … by two" / "you can create only one policy" · 2026-10-01 |
| NW.availability | — | 해당 없음(DB 가용성은 별도 문서) | — | — |
| NW.caching | — | 해당 없음 | — | — |
| NW.security | L3 | Redis AUTH(`auth_enabled`, 기본 false). Valkey `authorization_mode` AUTH_DISABLED / IAM_AUTH | | https://raw.githubusercontent.com/hashicorp/terraform-provider-google/main/website/docs/r/redis_instance.html.markdown · "Default value is "false" meaning AUTH is disabled." · 2026-10-01 |
| NW.dns | — | 미확인 | | — |
| NW.egress | — | 해당 없음 | — | — |
| NW.private_connectivity | L3 | **공인 IP 없음 → Cloud Run 등 서버리스는 Direct VPC(권장) 또는 커넥터 필수.** Redis 직접 피어링 예약 범위 최소 /29(복제본 있으면 /28), 기본 `DIRECT_PEERING`. PSA 모드는 먼저 PSA 연결 필요. Valkey: 정책 서비스 클래스 `gcp-memorystore`, Redis Cluster: `gcp-memorystore-redis`. Valkey는 커스텀 서비스 인스턴스 범위 미지원, 인스턴스와 같은 프로젝트의 정책만 | 정책 서브넷은 같은 리전의 일반 서브넷 | https://cloud.google.com/memorystore/docs/redis/connect-redis-instance-cloud-run · "You can connect to a Redis instance from Cloud Run by using Direct VPC egress ." · https://cloud.google.com/memorystore/docs/redis/networking · "The minimum required block size is /29 for instances without read replicas. The minimum required block size is /28 for instances that have read replicas." · https://cloud.google.com/memorystore/docs/cluster/networking · "use the gcp-memorystore-redis service class" · https://cloud.google.com/vpc/docs/about-service-connection-policies · "they must be in the same region as the service connection policy" · 2026-10-01 |
| NW.regions | — | 위 서울 표기 참조 | | |
| NW.cost_floor | — | 연결 자체: Redis PSA·직접 피어링 무료(PSA 연결 무료 근거). Valkey PSC 엔드포인트 요금 적용 여부·단가 미확인(추론: 6.7 단가) | | https://cloud.google.com/vpc/network-pricing · "there are no hourly or data charges for the connection itself" · 2026-10-01 ⚠️근거없음 |

### 비용 구조
- 연결 비용은 사실상 앱 쪽(Direct VPC $0 / 커넥터 ≈$15.69+/월)과 Memorystore 노드 요금. Valkey PSC 엔드포인트 과금은 미확인.

### 교체 계열 정보
- 공용 엔드포인트가 필요하면 Upstash 등 SaaS Redis(6.10) — 단 사설 연결 조건 다름.
- Redis 인스턴스 → Valkey 이전 시 네트워킹 방식이 피어링 → PSC로 바뀌어 사전 정책 필요.

### 함정
- Redis 인스턴스 기본 `DIRECT_PEERING`: Shared VPC·온프레미스 접근·중앙 IP 관리가 필요하면 생성 시 `PRIVATE_SERVICE_ACCESS` 지정(나중에 변경 불가).
- Valkey는 **서비스 연결 정책이 먼저 없으면 생성 실패**. 정책 생성은 Network Admin 권한.
- 피어링 기반이므로 전이 불가(6.8과 같음): 앱 VPC = Memorystore authorized_network여야 함.
- TLS·AUTH 기본 꺼짐.

### 생성 산출물
- Terraform 리소스: `google_redis_instance`(https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/redis_instance), `google_memorystore_instance`(.../memorystore_instance), `google_network_connectivity_service_connection_policy`(.../network_connectivity_service_connection_policy).
- 요구에 따라 반드시 명시할 속성:
  - `google_redis_instance`: `authorized_network`(= Cloud Run이 붙는 VPC), `connect_mode`(`PRIVATE_SERVICE_ACCESS` 권장, 이 경우 `google_service_networking_connection` 선행), `reserved_ip_range`, `transit_encryption_mode = "SERVER_AUTHENTICATION"`, `auth_enabled = true`.
  - `google_network_connectivity_service_connection_policy`: `service_class = "gcp-memorystore"`(Valkey) / `"gcp-memorystore-redis"`(Redis Cluster) / `"google-cloud-sql"`(Cloud SQL), `network`, `location`(리전), `psc_config { subnetworks = [...], limit }`.
  - `google_memorystore_instance`: `desired_auto_created_endpoints { network, project_id }`(구 `desired_psc_auto_connections`는 deprecated), `transit_encryption_mode = "SERVER_AUTHENTICATION"`, `authorization_mode = "IAM_AUTH"`, `depends_on = [policy]`(추론). ⚠️근거없음
- Checkov: `CKV_GCP_95` "Ensure Memorystore for Redis has AUTH enabled", `CKV_GCP_97` "Ensure Memorystore for Redis uses intransit encryption"(둘 다 `google_redis_instance`). `google_memorystore_instance`·서비스 연결 정책 대상 체크 없음.
- 배포 후 검증:
  - `gcloud redis instances describe INST --region=asia-northeast3 --format="value(connectMode,host,port,authorizedNetwork)"` → 의도한 모드, 내부 IP.
  - `gcloud network-connectivity service-connection-policies list --region=asia-northeast3`(추론: 명령 형식 미열람) → `gcp-memorystore` 정책 존재. ⚠️근거없음
  - Cloud Run 안에서 `timeout 3 bash -c '</dev/tcp/<HOST>/6379' && echo ok` → ok.

## 6.10 SaaS DB 사설 연결 (요약) — Supabase / Neon / PlanetScale / MongoDB Atlas / Upstash
- 계열: 네트워크-사설 연결
- 서울 리전: 일부(PlanetScale GCP PSC asia-northeast3 있음, PlanetScale AWS PrivateLink 목록에 ap-northeast-2 없음. 나머지 서울 사설 연결 미확인)

| 능력 키 | 계층 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|
| NW.layer | L4 | 전부 클라우드 사업자 사설 엔드포인트(AWS PrivateLink/VPC Lattice, GCP PSC) 또는 VPC 피어링 | | 아래 행별 출처 |
| NW.idle_timeout | — | 미확인 | — | — |
| NW.request_timeout | — | 해당 없음 | — | — |
| NW.websocket | — | 해당 없음 | — | — |
| NW.protocols | L4 | Supabase: 직접 IPv6 기본(무료·유료), IPv4 애드온 시 IPv4로 **전환**(듀얼스택 아님). 공유 풀러는 모든 플랜 IPv4 | | https://supabase.com/docs/guides/database/connecting-to-postgres · "The IPv4 add-on is not dual-stack: enabling it swaps the project's IPv6 (AAAA) DNS record for an IPv4 (A) record" / "The shared pooler is IPv4-only on every plan" · 2026-10-01 |
| NW.body_size | — | 해당 없음 | — | — |
| NW.draining | — | 해당 없음 | — | — |
| NW.health_check | — | 해당 없음 | — | — |
| NW.tls | TLS | Upstash: TLS 항상 켜짐. 나머지 미확인 | | https://upstash.com/docs/redis/features/security · "TLS is always enabled on Upstash Redis databases." · 2026-10-01 ⚠️출처확인필요 |
| NW.client_ip | — | 미확인 | — | — |
| NW.routing | L3 | Supabase PrivateLink: AWS VPC가 **같은 리전**, DB(5432)·PgBouncer(6543)만(API·Auth·Storage·Realtime은 공용). Neon: AWS PrivateLink, **같은 AWS 리전**, 리전당 구성 최대 10 | | https://supabase.com/docs/guides/platform/privatelink · "AWS VPC in the same region as your Supabase project" / "It does not support other Supabase services like API, Storage, Auth, or Realtime." · https://neon.com/docs/guides/neon-private-networking · "This endpoint service is available only within the same AWS region as your client application." · 2026-10-01 ⚠️출처확인필요 |
| NW.scaling | — | 해당 없음 | — | — |
| NW.availability | — | 해당 없음 | — | — |
| NW.caching | — | 해당 없음 | — | — |
| NW.security | L3 | Neon IP Allow(Scale 플랜). Upstash IP allowlist(서버리스는 IP를 알 수 없다고 명시) | | https://neon.com/docs/introduction/ip-allow · "Neon's IP Allow feature, available with the Neon Scale plan" · https://upstash.com/docs/redis/features/security · "you can not know the IP addresses in serverless platforms such AWS Lambda and Vercel functions" · 2026-10-01 ⚠️출처확인필요 |
| NW.dns | — | 미확인 | — | — |
| NW.egress | — | Supabase IPv4 애드온: 인바운드만 고정, DB 아웃바운드 IP 비고정 | | https://supabase.com/docs/guides/platform/ipv4-address · "If your database is making outbound connections, the outbound IP address is not static" · 2026-10-01 |
| NW.private_connectivity | L3 | **Supabase**: PrivateLink = **Team·Enterprise만**, AWS 전용(VPC Lattice). **Neon**: AWS PrivateLink, Scale 플랜 [충돌: "Business and Scale"]. **PlanetScale(Vitess 문서)**: AWS PrivateLink + **GCP PSC**, **Base 플랜 포함·추가 요금 없음**, GCP 서울 서비스 연결 `projects/planetscale-production/regions/asia-northeast3/serviceAttachments/edge-gateway-gcp-asia-northeast3`. **MongoDB Atlas**: AWS PrivateLink·Azure Private Link·GCP PSC, **M10 이상 전용 클러스터만**(Free·Flex 불가). **Upstash**: VPC 피어링·AWS PrivateLink [충돌: 보안 문서 "only available for Pro databases" vs 가격 페이지 "VPC peering requires an Enterprise contract"] | Upstash PrivateLink는 AWS만 | https://supabase.com/docs/guides/platform/privatelink · "PrivateLink is available only to Team and Enterprise customers." · https://neon.com/docs/guides/neon-private-networking · "Private Networking is available on Neon's Scale plan." / "You must be a Neon Business and Scale account user" · https://planetscale.com/docs/vitess/connecting/private-connections-gcp · "Private connections are included on the Base plan. There is no additional charge on PlanetScale's end" · https://www.mongodb.com/docs/atlas/security-private-endpoint/ · "This feature is available for M10 clusters or higher." · https://upstash.com/docs/redis/features/security · "VPC Peering is only available for Pro databases." · https://upstash.com/pricing/redis · "VPC peering requires an Enterprise contract." · 2026-10-01 ⚠️출처확인필요 |
| NW.regions | — | PlanetScale AWS PrivateLink 리전: us-east-2, us-east-1, us-west-2, ap-south-1, ap-southeast-1, ap-southeast-2, ap-northeast-1, eu-central-1, eu-west-1, eu-west-2, sa-east-1, ca-central-1(서울 없음). GCP PSC: asia-northeast3, europe-west1, europe-west4, northamerica-northeast1, us-central1, us-east1, us-east4. Neon: 모든 Neon AWS 리전 | | https://planetscale.com/docs/vitess/connecting/private-connections · 리전 표 "ap-northeast-1 com.amazonaws.vpce…" · https://planetscale.com/docs/vitess/connecting/private-connections-gcp · "asia-northeast3 projects/planetscale-production/regions/asia-northeast3/serviceAttachments/edge-gateway-gcp-asia-northeast3" · 2026-10-01 ⚠️출처확인필요 |
| NW.cost_floor | — | Supabase IPv4 애드온 $0.0055/시간(≈$4/월, Pro 이상), 레플리카마다 추가. PlanetScale 사설 연결 추가 요금 없음(클라우드 엔드포인트 요금은 사용자 부담 → GCP PSC $0.01/h + $0.01/GiB, 6.7). Upstash Prod Pack +$200/월(사설 연결 포함 여부 미확인). 나머지 미확인 | | https://supabase.com/docs/guides/platform/manage-your-usage/ipv4 · "$ 0.0055 per hour ( $ 4 per month)." · https://supabase.com/docs/guides/platform/ipv4-address · "Dedicated IPv4 Add-On (Pro Plans+)" · https://upstash.com/pricing/redis · "Prod Pack … +$200/month per database" · 2026-10-01 ⚠️출처확인필요 |

### 비용 구조
- 사설 연결은 대부분 상위 플랜 조건(Supabase Team+, Neon Scale, Atlas M10+, Upstash Pro/Enterprise 충돌) + 클라우드 쪽 엔드포인트 요금. PlanetScale만 Base 플랜 포함.

### 교체 계열 정보
- GCP(Cloud Run 서울)에서 사설로 붙을 수 있는 것: PlanetScale(GCP PSC asia-northeast3), MongoDB Atlas(GCP PSC, M10+, 서울 가용성 미확인). Supabase·Neon·Upstash PrivateLink는 **AWS 전용** → GCP에서는 공용 경로(TLS + 비밀번호/IP 허용)뿐.
- Supabase를 GCP 서버리스에서: 공유 풀러(IPv4, 트랜잭션 모드 6543) 또는 IPv4 애드온.

### 함정
- **Supabase 직접 연결은 기본 IPv6**: IPv6 경로가 없는 실행 환경(커넥터는 IPv6 미지원, Direct VPC는 듀얼스택 서브넷 필요)에서는 직접 연결 실패 → 풀러 또는 IPv4 애드온. Cloud Run 기본 인터넷 이그레스의 IPv6 지원 여부는 미확인.
- Supabase PrivateLink는 DB만 — supabase-js(REST/Auth/Storage)는 계속 공용.
- 사설 엔드포인트는 같은 리전 조건(Supabase, Neon, PSC 게시 서비스) → 앱 리전 ≠ DB 리전이면 불가.
- IP allowlist는 서버리스 출구 IP가 고정이 아니면 무의미 → Cloud NAT 고정 IP 필요(05 문서).
- PlanetScale 문서는 Vitess(MySQL) 경로 기준. Postgres 상품의 사설 연결은 미확인.

### 생성 산출물
- Terraform 리소스: GCP 소비자 쪽 `google_compute_address`(INTERNAL) + `google_compute_forwarding_rule`(target = SaaS 서비스 연결 URI, `load_balancing_scheme = ""`), 사설 DNS `google_dns_managed_zone`(private) + 레코드(PlanetScale 도메인 `gcp-asia-northeast3.private-connect.psdb.cloud`). Atlas는 `mongodbatlas_privatelink_endpoint` 등 공급자 리소스(이 조사에서 Registry 미확인).
- 요구에 따라 반드시 명시할 속성: `target` = 공급자가 공개한 서비스 연결 URI, `network`, `ip_address`, 다른 리전 클라이언트면 `allow_psc_global_access = true`(공급자가 글로벌 액세스 지원 시).
- Checkov: SaaS 사설 연결 대상 체크 없음.
- 배포 후 검증: `gcloud compute forwarding-rules describe EP --region=asia-northeast3 --format="value(pscConnectionStatus)"` → `ACCEPTED`; Cloud Run 안에서 `getent hosts <사설 도메인>` → 엔드포인트 내부 IP, `timeout 3 bash -c '</dev/tcp/<IP>/3306'` → ok. Supabase: `dig AAAA db.<ref>.supabase.co` → IPv6만 나오면 IPv4 전용 환경에서 직접 연결 불가.

---

# 7. 경로 규칙 후보

요청 경로(사용자 → DNS → CDN·WAF → LB·인그레스 → 앱 → 출구 NAT / 사설 연결 → 데이터·외부 API) 위에서 이웃한 구성 요소끼리 성립해야 하는 조건이다. 형식은 `조건 ⇒ 요구` 또는 부등식이다. [대괄호]는 근거가 되는 능력 키와 절 번호, 차원 ID는 [../dimensions.md](../dimensions.md)를 따른다. 규칙 엔진으로 옮기기 전에 `(추론)` 표시 규칙은 사람이 검토한다. ⚠️근거없음

### 7.1 계열을 가로지르는 규칙 (경로 전체)

1. **개인화 응답은 공유 캐시에 남지 않는다.** C4 = 개인화 응답 있음 또는 F5 ≥ 개인정보 ⇒ 그 경로에 걸린 모든 공유 캐시 계층(CDN 캐시 동작, Cloudflare 캐시 규칙, Vercel·Netlify 캐시 헤더)에서 `최소 TTL = 0` ∧ 강제 캐시 모드 없음 ∧ 앱 응답 `Cache-Control: private` 또는 `no-store`. 한 계층이라도 강제 캐시(CloudFront `min_ttl > 0`(CachingOptimized 포함), GCP `FORCE_CACHE_ALL`, Cloudflare Edge TTL override)를 쓰면 위반. [NW.caching 1.1·1.2·1.4]
2. **세션 쿠키는 캐시 히트로 재전송되지 않는다.** 캐시 키에 쿠키가 들어가는 정책(CloudFront `UseOriginCacheControlHeaders`, 쿠키 전달 레거시 설정) ∧ 앱이 캐시 가능 응답에 `Set-Cookie` ⇒ 앱이 `Cache-Control: no-cache="Set-Cookie"` 또는 `private`을 보내야 함. [NW.caching 1.1]
3. **타임아웃 계층은 바깥이 안쪽보다 길다.** A2 최대 처리 시간 `<` 앱 서버 타임아웃 `<` LB 유휴·백엔드 타임아웃(09 문서) `≤` CDN 오리진 응답 타임아웃(CloudFront 30초 기본·120초 상한, GCP 백엔드 서비스 30초, Cloudflare 125초(Ent 6,000초), Fastly 첫 바이트 15초). 어느 한 쌍이라도 뒤집히면 504/524. A2 = 수 분 이상이면 CDN·LB 경로가 아니라 비동기 작업(큐 + 상태 조회)으로 바꾼다. [NW.request_timeout 1.x, 09 문서]
4. **keep-alive는 안쪽이 바깥쪽보다 길다.** 연결을 먼저 여는 쪽(CDN→오리진, LB→앱, 앱→NAT→외부)의 유휴 타임아웃 `<` 받는 쪽 유휴 타임아웃. 앱→외부 연결 풀 유휴·TCP keepalive `<` NAT 유휴(AWS NAT 350초 고정·초과 시 RST, PrivateLink 인터페이스 엔드포인트 350초, Cloud NAT established 1,200초 기본). [NW.idle_timeout 1.1·1.4·5.1·5.4·6.2]
5. **클라이언트 IP는 한 곳에서만 해석하고 신뢰 홉을 고정한다.** CDN·WAF·LB가 겹치면 앱·WAF의 IP 키는 `X-Forwarded-For`의 (신뢰 홉 수로 정한) 위치, `CloudFront-Viewer-Address`, `CF-Connecting-IP`, GCP `user_ip_request_headers` 중 하나로 고정 ∧ 오리진(LB)은 앞단 CDN 대역·비밀 헤더만 수락. 앞단이 둘(Cloudflare → Vercel 등)이면 뒤쪽의 IP 기반 레이트 리밋은 무력화되므로 앞단에 둔다. [NW.client_ip 1.x·3.1·3.4·3.7]
6. **엣지 보호는 우회 경로가 없어야 성립한다.** WAF·Cloud Armor·CDN을 요구(S 축, D3)했으면 오리진 직접 진입점이 닫혀 있어야 함: Cloud Run `ingress = internal-and-cloud-load-balancing` + 기본 `run.app` URL 비활성, ALB SG = CloudFront 관리형 접두사 목록, S3는 OAC, Cloudflare 원본은 Cloudflare IP만 또는 터널. [NW.security 3.x, 05-security S-031]
7. **업로드 크기는 경로의 최소 한도 이하.** A7 최대 요청 본문 `≤ min(CDN 본문 한도(Cloudflare Free·Pro 100 MB, Business 200 MB), WAF 검사 정책(AWS CommonRuleSet `SizeRestrictions_BODY` 8 KB 초과 차단), LB·플랫폼 한도(09·04·05 문서))`. 넘으면 서명 URL 직접 업로드로 바꾸거나 해당 규칙을 count로 override. [NW.body_size 1.4·3.1]
8. **장애 조치는 계층마다 범위가 다르다.** F1(쓰기 경로 중단 거의 0) ⇒ CDN 오리진 그룹(GET·HEAD·OPTIONS만)으로는 충족 불가 → LB·DNS 계층 장애 조치. DNS 장애 조치(Route 53·Cloud DNS)는 모든 대상 비정상 시 fail-open, HTTPS 헬스 체크는 인증서를 검증하지 않음 ⇒ 인증서 만료 감시를 별도로 둔다. 전환 시간 = 탐지(주기 × 임계값) + TTL + 클라이언트 DNS 캐시 ≤ F1 허용 시간. [NW.health_check 1.1·2.1·2.2, NW.dns 2.x]
9. **인증서 자동 갱신 전제가 경로 설정과 맞는다.** ACM DNS 검증 ⇒ 검증 CNAME 영구 유지(Cloudflare면 `proxied = false`) ∧ AWS 서비스에서 사용 중, CloudFront면 us-east-1. Google LB 승인 ⇒ DNS가 그 LB IP를 직접 가리킴(앞단 다른 CDN 프록시 없음). Let's Encrypt HTTP-01 ⇒ 80 포트 `/.well-known/acme-challenge/` 경로가 CDN·WAF·리다이렉트 규칙을 통과. [NW.tls 4.x]
10. **서버리스 + 사설 DB ⇒ 사설 연결 수단 필수.** DB에 공인 엔드포인트가 없음(Cloud SQL `ipv4_enabled = false`, Memorystore 전부, RDS `publicly_accessible = false`) ∧ 컴퓨트가 Cloud Run·Lambda·Cloud Run functions ⇒ Cloud Run `vpc_access`(Direct VPC 또는 커넥터) / Lambda `vpc_config`가 DB와 같은 VPC(PSA·피어링은 **직접** 피어링된 VPC, 전이 불가)에 있어야 함. 티어 0(Vercel·Netlify·Cloudflare Workers)은 서울에서 사설 연결 수단이 없거나 Enterprise 전용이므로 DB를 공인 엔드포인트 + TLS + IP 제한으로 두거나 컴퓨트를 바꾼다. [NW.private_connectivity 6.4~6.10, 5.5.4~5.5.6]
11. **사설 연결을 켜면 인터넷 출구가 사라질 수 있다.** Lambda VPC 연결 ∨ App Runner VPC 커넥터 ∨ Cloud Run `egress = ALL_TRAFFIC` ∧ 앱이 외부 API 호출(E1·E2) ⇒ 사설 서브넷 + NAT(AWS) / Cloud NAT(GCP) 필수. 퍼블릭 서브넷의 Lambda는 인터넷 불가. [NW.egress 5.5.1·5.5.2·6.4]
12. **NAT 포트 용량 ≥ 외부 호출 동시성.** 목적지 d(같은 IP·포트·프로토콜)별 피크 동시 연결 `C_d = 인스턴스 수 × 인스턴스당 d로의 동시 연결`. AWS: `C_d ≤ 55,000 × NAT IP 수`(존 모드 IP ≤ 8, 기본 EIP 쿼터 2). GCP: 인스턴스당 d로의 동시 연결 + TIME_WAIT 포트 `≤ min_ports_per_vm`(기본 64, Cloud Run Direct VPC는 2배 필요) ∧ `NAT IP 수 × 64,512 ≥ (VM + Cloud Run 최대 인스턴스) × VM당 포트`. LLM·결제 등 단일 호스트로 몰리는 호출(E1)에서 먼저 깨진다. [NW.egress·NW.scaling 5.1·5.2·5.4]
13. **IP 허용 목록 요구 ⇒ 고정 출구 IP를 수동 고정.** 상대 SaaS·결제·공공 API가 IP 허용 목록을 요구(E1·E3·F5) ⇒ AWS 존 NAT + EIP 또는 리전 NAT 수동 모드, GCP `nat_ip_allocate_option = MANUAL_ONLY`, 플랫폼 전용 고정 IP 기능(Vercel Static IPs 등). 자동 IP(리전 NAT 자동 모드, GCP AUTO_ONLY, Fargate 퍼블릭 IP, Render·Fly 기본)는 바뀌므로 위반. 엣지 런타임(Vercel Routing Middleware, Workers `connect()`)은 고정 IP 적용 대상이 아님. [NW.egress·NW.client_ip 5.x]
14. **출구 존 장애 범위 ⊇ 컴퓨트 존 범위.** F1 ≥ 짧아야 함 ∧ 컴퓨트 다중 AZ ⇒ AWS 존 NAT를 AZ마다(각 사설 서브넷 기본 경로 → 같은 AZ NAT) 또는 리전 NAT. 인터페이스 엔드포인트 서브넷 AZ 집합 ⊇ 앱 서브넷 AZ 집합. [NW.availability 5.1·6.2]
15. **AWS 서비스 트래픽은 NAT 처리 요금을 타지 않는다.** 사설 서브넷 ∧ S3·ECR·DynamoDB 트래픽 있음 ⇒ S3·DynamoDB 게이트웨이 엔드포인트(무료). NAT 없이 사설 서브넷에서 이미지 풀 ⇒ `ecr.api` + `ecr.dkr`(`private_dns_enabled = true`, Terraform 기본 false) + S3 게이트웨이 (+ `logs`, `secretsmanager`). [NW.private_connectivity 6.1·6.2, NW.cost_floor 5.1]
16. **연결 수 상한은 하류에서 정한다.** 컴퓨트 최대 인스턴스 × 인스턴스당 풀 크기 `≤` DB 최대 연결 수(01 문서) ∧ `≤` Direct VPC 인스턴스 쿼터·서브넷 IP(서비스 인스턴스당 IP 2개, /26 이상) ∧ `≤` NAT 포트 용량(12번). [NW.scaling 6.6·6.8]
17. **레이트 리밋 단위는 제품 단위로 환산한다.** 앱의 레이트 요구(창·키) → AWS WAF 창 ∈ {60,120,300,600}초·limit ≥ 10, Cloud Armor interval 10~3,600초, Cloudflare Free 10초, Vercel ≥ 10초. 모두 근사·지역별 카운터라 정확한 사용자 쿼터(E2·E3 비용 보호)는 앱·API 게이트웨이에서 구현한다. [NW.security 3.x]
18. **DNS TTL은 변경 계획에 맞춘다.** 장애 조치·이전 대상 레코드 TTL ≤ 60~120초(또는 별칭). Cloudflare 프록시 레코드는 TTL 300초 고정이라 TTL 요구는 무의미하고 원본 전환은 Cloudflare 쪽에서. [NW.dns 2.1·2.3]

이하 7.2~7.7은 각 계열 조사에서 나온 규칙 후보 원문이다. 7.1과 겹치는 것은 7.1이 우선한다.

### 7.2 CDN

1. **개인화 응답 × 최소 TTL**: 경로에 C4(개인화)·F5 응답이 있으면 그 경로의 CDN 최소 TTL = 0 이어야 한다. CloudFront `min_ttl > 0`(CachingOptimized=1초 포함) ∧ 개인화 경로 → 위반 [NW.caching].
2. **강제 캐시 모드 금지**: 개인화 경로 백엔드에 대해 GCP `cache_mode ≠ FORCE_CACHE_ALL`, Cloudflare `edge_ttl.mode ≠ override_origin`·Status code TTL 미사용, Fastly는 `Cache-Control`에 `private` 포함 [NW.caching].
3. **Set-Cookie × 캐시 키 쿠키**: CloudFront 캐시 정책이 쿠키를 캐시 키에 포함(UseOriginCacheControlHeaders 포함) ∧ 오리진이 캐시 가능한 응답에 `Set-Cookie` → 오리진이 `Cache-Control: no-cache="Set-Cookie"` 또는 `private`를 내야 함 [NW.caching].
4. **오리진 응답 시간**: 앱 최대 처리 시간(A2) < CDN 오리진 응답 타임아웃 ≤ 그 뒤 LB 타임아웃. CloudFront 30초(≤120), Cloudflare 125초(Ent 6,000), GCP 백엔드 서비스 30초, Fastly 첫 바이트 15초 [NW.request_timeout].
5. **오리진 keep-alive 방향**: CDN의 오리진 keep-alive(CloudFront 5초, Cloudflare Proxy Idle 900초) < 오리진 LB/앱 유휴 타임아웃. Cloudflare 900초는 대부분의 앱 서버 keep-alive보다 길어 520 위험(추론) → 앱 keep-alive 상향 또는 확인 [NW.idle_timeout]. ⚠️근거없음
6. **웹소켓 유휴**: A3=웹소켓이면 앱 하트비트 간격 < CDN 웹소켓 유휴 한도(CloudFront 10분, GCP 백엔드 서비스 타임아웃, Cloudflare 미공개 → 하트비트 필수) ∧ CloudFront는 `Sec-WebSocket-*` 헤더 전달 정책 필수 [NW.websocket].
7. **업로드 크기**: A7 최대 요청 본문 ≤ CDN 본문 한도(Cloudflare Free/Pro 100 MB, Business 200 MB; CloudFront 64 GB). 넘으면 스토리지 직접 업로드 또는 업로드 호스트 CDN 우회 [NW.body_size].
8. **GCP 전제 조합**: Cloud CDN 선택 ⇒ 전역 외부(또는 클래식) ALB 필수 ⇒ 포워딩 규칙 고정비 > 0 (G3 예산 민감이면 비교 대상) [NW.layer, NW.cost_floor].
9. **무효화 예산**: (월 배포 수 × 배포당 무효화 경로 수) ≤ 1,000 (CloudFront 무료) — 넘으면 해시 파일명·`/*` 1경로로. Cloudflare Free는 태그·전체 퍼지 5회/분, GCP는 500회/분 [NW.caching].
10. **장애 조치 범위**: F1(쓰기 경로 중단 불가) 요구는 CloudFront 오리진 그룹으로 충족 불가(GET/HEAD/OPTIONS만) → LB·DNS 계층 장애 조치 필요 [NW.health_check].
11. **클라이언트 IP**: CDN 뒤 앱이 IP 기반 레이트 리밋·감사 로그(F5)를 하면 `X-Forwarded-For`(신뢰 프록시 수 설정)·`CloudFront-Viewer-Address`·`CF-Connecting-IP` 중 하나를 읽도록 코드 수정 + 오리진은 CDN만 허용 [NW.client_ip, NW.security].
12. **인증 헤더 요청**: `Authorization` 헤더를 쓰는 API는 Vercel·GCP(응답이 public/s-maxage 아니면)에서 캐시 안 됨 → C4 "읽기 위주"라도 토큰 인증 API는 CDN 캐시 이득 없음(추론) [NW.caching]. ⚠️근거없음

### 7.3 DNS·인증서

1. `DNS.ttl(장애 조치 대상 레코드) ≤ 120초` 이고 `탐지시간(request_interval × failure_threshold) + TTL ≤ F1 허용 중단 시간` (근거: NW.dns, NW.health_check — Route 53 기본 30×3=90초 + TTL).
2. 장애 조치(F1 짧음·F2 있음) 구성이면 primary·secondary(또는 모든 그룹 레코드)에 헬스 체크가 있어야 함, 별칭이면 `evaluate_target_health = true` (근거: NW.dns 장애 조치 동작).
3. "모든 대상 비정상 → 모두 정상 간주(fail-open)"이므로 DNS 장애 조치만으로 전면 장애를 막는다고 판정하지 말 것: secondary는 다른 리전/정적 페일백 페이지처럼 독립 장애 영역이어야 함 (근거: NW.dns, NW.health_check).
4. HTTPS 헬스 체크(Route 53)는 인증서를 검증하지 않음 → 인증서 만료 감시는 별도(ACM 이벤트·외부 모니터) 필수 (근거: NW.tls, NW.health_check).
5. CloudFront 뷰어 인증서 ⇒ ACM 리전 = us-east-1. ALB 인증서 ⇒ ALB와 같은 리전 (근거: NW.regions 4.1).
6. ACM DNS 검증 인증서 ⇒ 검증 CNAME이 공개 DNS에 영구 존재 ∧ 인증서가 AWS 서비스에 연결(사용 중) — 둘 중 하나라도 거짓이면 자동 갱신 안 됨. 외부 DNS(Cloudflare)면 해당 CNAME `proxied=false` (근거: NW.tls, NW.dns 4.1·2.3).
7. GCP LB 승인 관리형 인증서 ⇒ DNS A/AAAA가 해당 LB IP를 가리키고 앞단에 다른 CDN 프록시가 없어야 발급. F4(무중단 이전)면 DNS 승인으로 사전 발급 (근거: NW.tls, NW.dns 4.2).
8. 와일드카드 인증서 ⇒ Let's Encrypt는 DNS-01, Google은 DNS 승인 필수 (근거: NW.security 4.3, NW.tls 4.2).
9. HTTP-01 사용 ⇒ 인터넷→포트 80 경로(LB 리스너·보안 그룹·WAF·CDN 규칙)가 `/.well-known/acme-challenge/`를 통과시켜야 함 (근거: NW.security 4.3).
10. cert-manager 갱신 창 ≥ 인증서 수명 × 1/3, 그리고 `renewBefore < duration`. 고정 renewBefore 대신 `renewBeforePercentage` (근거: NW.tls 4.3).
11. Cloudflare 프록시 레코드 ⇒ DNS TTL 300초 고정이므로 TTL 기반 요구는 무의미, 장애 조치는 Cloudflare LB(애드온)·원본 측에서. DNS-only로 웹 서비스 ⇒ 원본 IP 노출 (근거: NW.dns, NW.security 2.3).
12. DNSSEC(F5 요구) ⇒ 등록 기관·부모가 DS 지원, 단일 DNS 공급자. Route 53은 TTL 1주 상한 (근거: NW.security 2.1·2.2).

### 7.4 WAF·DDoS

1. WAF 앞에 CDN·프록시가 있으면(경로: CDN → LB+WAF) WAF의 IP 기반 규칙(레이트·geo·IP set)은 forwarded IP를 써야 한다: AWS `forwarded_ip_config` 존재, GCP `user_ip_request_headers` + `enforce_on_key="USER_IP"`. 아니면 CDN 엣지 IP로 집계. 근거: NW.client_ip(3.1, 3.4).
2. forwarded IP를 쓰면 원본(LB)은 CDN IP 대역만 받아야 한다(헤더 위조 차단): `LB 보안 그룹·방화벽 ⊆ CDN IP 범위` 또는 CDN이 넣는 비밀 헤더 검증. 근거: NW.client_ip(3.1 "headers ... can be modified to bypass", 3.4 user IP best practice).
3. 앱 최대 요청 본문(A7) > WAF 본문 검사 한도(ALB 8 KB, CloudFront 기본 16 KB, Cloud Armor 설정값)이면: 초과분 미검사를 수용하거나 크기 차단 규칙 추가. 그리고 AWS CommonRuleSet 사용 시 `A7 > 8 KB ⇒ SizeRestrictions_BODY override=count` 필수(아니면 업로드 403). 근거: NW.body_size, NW.security(3.1).
4. 앱이 User-Agent 없는 클라이언트(서버 간 API·웹훅)를 받으면 AWS CommonRuleSet `NoUserAgent_HEADER`를 count로, Cloudflare Bot Fight Mode는 끔, Under Attack·Attack Mode는 API 경로 제외. 근거: NW.security(3.1, 3.6).
5. 레이트 요구 단위 ↔ 제품 단위: AWS 창 ∈ {60,120,300,600}·limit ≥ 10, Cloud Armor interval ∈ {10…3600}, Cloudflare Free period = 10초, Vercel 창 ≥ 10초. 요구 창이 이 집합에 없으면 가장 가까운 값으로 환산하고 근사·지연(수십 초~수 분)을 허용해야 한다. 정확한 과금 쿼터는 WAF로 구현 금지(앱·API GW에서). 근거: NW.security.
6. 다리전 배포(Cloud Armor 리전별 독립, Vercel 리전별, Cloudflare 데이터센터별)면 실효 한도 ≤ 설정값 × 리전(데이터센터) 수. 근거: NW.security(3.4, 3.6, 3.7).
7. Shield Advanced 비용 보호를 기대하면: `aws_shield_protection` 존재 ∧ (CloudFront·ALB면 연결 web ACL에 Block 레이트 규칙 ≥1). 근거: NW.security(3.3).
8. Cloud Armor 정책 생성 시 기본 규칙(2147483647) 액션을 명시: 공개 앱이면 allow, 의도와 다르면 전 트래픽 403. 근거: NW.security(3.4) [충돌].
9. Cloud Run·서버리스에 Cloud Armor 요구가 있으면 경로에 외부 ALB + 서버리스 NEG가 있어야 하고 `*.run.app` 직접 진입은 차단(ingress 제한). AWS API Gateway HTTP API에는 WAF를 못 붙이므로 REST API 또는 CloudFront 앞단 필요. 근거: NW.layer(3.1, 3.4).
10. Cloudflare → Vercel 경로면 Vercel 방화벽 IP 키가 Cloudflare IP가 된다 → 레이트 리밋은 Cloudflare 쪽에 둔다. 근거: NW.client_ip(3.7).
11. Terraform으로 Cloudflare 진입점 ruleset을 관리하면 대시보드 수동 규칙·Free Managed Ruleset 배포 여부를 import 후 포함해야 한다(덮어쓰기). 근거: 3.6 함정.
12. WAF 로그 대상 이름 접두어 `aws-waf-logs-` 필수(아니면 apply 실패). 근거: 3.1 함정.

### 7.5 출구 NAT·고정 IP

1. **[AWS 포트]** 외부 목적지 d(같은 IP·포트·프로토콜)별 피크 동시 연결 수 `C_d ≤ 55,000 × N_ip` (존: N_ip ≤ 8, 기본 EIP 쿼터 2 / 리전: AZ당 N_ip ≤ 32). 위반 시 `ErrorPortAllocation`. 근거: NW.scaling, NW.egress (5.1, 5.2). 차원 D2·D3·E1.
2. **[GCP 포트]** 인스턴스당 목적지 d별 피크 동시 연결 + TIME_WAIT 중 포트 `≤ 할당 포트`(정적: min_ports_per_vm을 2의 거듭제곱으로 올린 값 / DPA: max_ports_per_vm). Cloud Run Direct VPC면 `min_ports_per_vm ≥ 2 × 인스턴스당 필요 포트`. 근거: 5.4 NW.scaling, 5.5.1.
3. **[GCP IP 수]** `N_nat_ip × 64,512 ≥ (VM 수 + Cloud Run 최대 인스턴스 수) × VM당 포트` (MANUAL_ONLY일 때). 위반 시 OUT_OF_RESOURCES drop. 근거: 5.4 NW.egress.
4. **[유휴 타임아웃]** 앱의 외부 연결 풀 유휴 시간 또는 TCP keepalive 간격 `< NAT 유휴`(AWS 350초 고정 / GCP established 1,200초 기본). AWS는 위반 시 RST. 근거: NW.idle_timeout. 차원 A3·C8.
5. **[허용 목록 → 수동 IP]** E1/E3/F5에 "상대가 IP 허용 목록 요구"면: AWS 존 NAT + EIP 또는 리전 NAT 수동 모드(`availability_zone_address`), GCP `MANUAL_ONLY`. 리전 NAT 자동 모드·GCP AUTO_ONLY·Fargate 퍼블릭 IP·Render 기본 범위·Fly 기본은 금지. 근거: NW.client_ip.
6. **[존 장애]** F1 = 짧아야 함 이상이면 AWS 존 NAT 수 = 워크로드 AZ 수, 각 사설 서브넷 기본 경로 → 같은 AZ NAT (또는 리전 NAT). 근거: 5.1 NW.availability.
7. **[서버리스 사설+인터넷 동시]** Lambda가 VPC 연결 + 인터넷 호출이면 사설 서브넷 + NAT 필수(퍼블릭 서브넷 불가). Cloud Run이 VPC 연결 + 고정 IP면 `vpc-egress=all-traffic` 필수. 근거: 5.5.1, 5.5.2 NW.egress.
8. **[비용]** G3 = 높음이고 F1 = 길어도 됨이면 NAT 1개(또는 NAT 인스턴스) 허용; AWS 서비스 출구(ECR·S3) 비중 크면 VPC 엔드포인트로 NAT 처리 요금 회피. 근거: NW.cost_floor.
9. **[엣지 런타임]** Vercel Routing Middleware, Cloudflare Workers `connect()`는 고정 출구 IP 기능의 적용 대상이 아님 → 해당 경로에서 허용 목록 대상 호출 금지. 근거: 5.5.4, 5.5.6.
10. **[지역]** 고정 출구 IP 기능 지역 ∋ 앱 리전: Netlify Private Connectivity는 서울 없음 → D5=한국 + 고정 IP 요구면 Netlify 불가. 근거: 5.5.5 NW.regions.
11. **[EIM/DPA 배타]** GCP에서 `enable_dynamic_port_allocation = true` ⇒ `enable_endpoint_independent_mapping = false`이며 NAT 규칙과 EIM 동시 불가. 근거: 5.4 NW.routing.

### 7.6 사설 연결 — AWS

1. **사설 서브넷 + NAT 없음 + 컨테이너 이미지(ECR)** ⇒ `ecr.api`·`ecr.dkr`(사설 DNS 켬) 인터페이스 엔드포인트 **그리고** S3 게이트웨이 엔드포인트가 그 서브넷 라우트 테이블에 연결돼 있어야 한다. 하나라도 빠지면 이미지 풀 실패. 근거: 6.2 NW.private_connectivity, 6.1 NW.routing.
2. **Fargate awslogs + NAT 없음** ⇒ `logs` 인터페이스 엔드포인트 필수. **시크릿 주입(F5) + NAT 없음** ⇒ `secretsmanager`(또는 `ssm`) 필수. 근거: 6.2 NW.private_connectivity.
3. **Lambda vpc_config 있음 ∧ 앱이 외부 API 호출(E1·E2) 있음** ⇒ 함수 서브넷 = 사설 ∧ 해당 라우트 테이블 0.0.0.0/0 → NAT. 퍼블릭 서브넷 지정은 위반. 근거: 6.4 NW.egress·NW.routing.
4. **Lambda vpc_config 있음 ∧ 앱이 AWS API 호출** ⇒ 각 서비스에 대해 (NAT 경로) ∨ (인터페이스 엔드포인트 + 사설 DNS) ∨ (S3/DynamoDB 게이트웨이). 근거: 6.4 NW.egress, 6.2, 6.1.
5. **인터페이스 엔드포인트 사용** ⇒ VPC `enableDnsSupport ∧ enableDnsHostnames` = true ∧ `private_dns_enabled` = true ∧ 엔드포인트 SG 인바운드 443 ⊇ 앱 SG/서브넷. 근거: 6.2 NW.dns·NW.security.
6. **엔드포인트 서브넷 AZ 집합 ⊇ 앱(태스크·Lambda) 서브넷 AZ 집합**, F1(중단 허용 짧음)이면 |AZ| ≥ 2. 근거: 6.2 NW.availability·NW.health_check.
7. **PrivateLink 경로(인터페이스 엔드포인트·NLB) 위 장기 연결(DB 풀, C8 상시 풀)** ⇒ 앱·드라이버 TCP keepalive 또는 풀 유휴 회수 < 350초. 근거: 6.2 NW.idle_timeout, 6.3 NW.idle_timeout.
8. **Lambda → RDS 직접 연결** ⇒ 같은 VPC ∧ RDS SG 인바운드 소스 = 함수 SG(DB 포트). C8 요청마다 연결 ∧ D2/D3 높음이면 RDS Proxy 필수. 근거: 6.4 NW.private_connectivity.
9. **게이트웨이 엔드포인트로 S3 접근 ∧ 버킷 정책에 `aws:SourceIp` 조건** ⇒ 불일치(거부). `aws:sourceVpce`/`aws:VpcSourceIp`로 바꿔야 함. 온프레미스·피어링·TGW 건너편 소비자가 S3에 사설 접근해야 하면 게이트웨이 불가 → 인터페이스. 근거: 6.1 NW.client_ip·NW.private_connectivity.
10. **"비공개 인바운드" 요구(D1 내부·F5) ∧ Lambda Function URL** ⇒ 불일치(Function URL은 공용 전용, PrivateLink 미지원). Lambda 인터페이스 엔드포인트+Invoke 또는 사설 API로. 근거: 6.4 NW.private_connectivity.
11. **SaaS DB/다른 계정 서비스에 PrivateLink로 교차 리전 접속(서울 소비자)** ⇒ 엔드포인트 서브넷 AZ ID ∈ {apne2-az1, apne2-az3} ∧ 제공자 NLB TCP 유휴 = 기본(350초) ∧ 리전 DNS 사용. 근거: 6.3 NW.private_connectivity·NW.idle_timeout.
12. **엔드포인트 서비스 제공자의 앱이 클라이언트 IP로 레이트 리밋·감사** ⇒ NLB 프록시 프로토콜 v2 활성 ∧ 백엔드 파싱 구현, 아니면 모든 소비자가 NLB IP로 보임. 근거: 6.3 NW.client_ip.

### 7.7 사설 연결 — GCP·SaaS

1. **서버리스 → 사설 DB 필수 조합**: DB에 공인 IP가 없음(Cloud SQL `ipv4_enabled=false`, Memorystore 전부, PSC 전용) ⇒ Cloud Run에 `vpc_access`(network_interfaces 또는 connector) 존재 AND 그 VPC = DB의 `private_network`/`authorized_network`/PSC 엔드포인트 VPC. (근거 NW.private_connectivity 6.5·6.6·6.8·6.9)
2. **피어링 전이 불가**: DB가 PSA/직접 피어링이면 Cloud Run이 붙는 VPC는 DB와 **직접** 피어링된 VPC여야 한다(허브-스포크 경유 불가). 아니면 PSC로 전환. (6.8 NW.routing, 6.9 NW.routing)
3. **Direct VPC 서브넷 크기**: 서브넷 주소 수 ≥ max(64, 4 × Cloud Run `max_instance_count` + 16)(추론: 2× 정상, 리비전 교체 시 2배, 16 블록). 잡은 ≥ 동시 태스크 수 + 7분 보유분, 최소 /26. (6.6 NW.private_connectivity·NW.draining) ⚠️근거없음
4. **Direct VPC 인스턴스 쿼터**: Cloud Run `max_instance_count` ≤ Direct VPC 쿼터(100–200/리전). 위반 시 확장 정지. (6.6 NW.scaling)
5. **커넥터 비용 상한**: 커넥터 사용 시 `max_instances` 명시 AND 월 고정비 = max_instances × 머신 단가 × 730(축소 안 함)을 예산(F1)과 비교. (6.5 NW.scaling·NW.cost_floor)
6. **커넥터 장기 연결**: 앱 DB 연결 재사용 시간 > 60초이고 커넥터 경유 ⇒ 커넥션 풀의 재연결·검증 필수. 1시간 넘는 Cloud Run 잡 + Direct VPC ⇒ 재연결 로직 필수. (6.5 NW.idle_timeout, 6.6 NW.websocket)
7. **시작 시 연결 지연**: Direct VPC 사용 ⇒ startup probe 또는 DB 연결 재시도. Direct VPC + Cloud NAT ⇒ 콜드 스타트 +30초 이상을 Cloud Run 시작 타임아웃(4분)·지연 SLO와 비교. (6.6 NW.health_check·NW.egress)
8. **이그레스 모드 일치**: 고정 출구 IP 요구(외부 API IP 허용, SaaS IP allowlist) ⇒ `egress = ALL_TRAFFIC` + Cloud NAT. 사설 DB만 ⇒ `PRIVATE_RANGES_ONLY` AND 해당 서브넷에 Public NAT 없음. (6.5 NW.routing·NW.egress)
9. **IP 버전 일치**: 목적지가 IPv6 전용(Supabase 직접 연결 기본) ⇒ 경로에 커넥터 금지, Direct VPC면 듀얼스택 서브넷 필요, 아니면 IPv4 풀러/애드온. (6.5 NW.protocols, 6.10 NW.protocols)
10. **같은 리전 조건**: 커넥터 리전 = Cloud Run 리전(Shared VPC 제외), PSC 게시 서비스 엔드포인트 리전 = 서비스 리전, Supabase/Neon PrivateLink는 AWS 같은 리전. 타 리전 클라이언트 ⇒ `allow_psc_global_access = true`. (6.5 NW.availability, 6.7 NW.routing, 6.10 NW.routing)
11. **Cloud SQL TLS·연결 방식 일치**: `ssl_mode = TRUSTED_CLIENT_CERTIFICATE_REQUIRED`(CKV_GCP_6 통과) ⇒ 앱은 Auth Proxy/언어 커넥터 사용(직접 5432 + 비밀번호 불가). Cloud Run 웹앱 ⇒ `server_ca_mode = GOOGLE_MANAGED_INTERNAL_CA`. (6.8 NW.tls)
12. **Cloud SQL 연결 수**: Cloud Run `max_instance_count` × 인스턴스당 풀 크기(≤100) ≤ Cloud SQL `max_connections`. (6.8 NW.scaling)


---

# 8. 조사 결과 요약

- 구성 요소: **46개**. CDN 7, DNS 4, WAF·DDoS 7, 인증서 3, 출구 15(NAT 4종 + 플랫폼별 고정 출구 IP 10 + 퍼블릭 IPv4), 사설 연결 10. 5.5의 플랫폼 10개를 한 항목으로 세면 37개.
- `미확인`: 파일 전체 출현 159회(표기 설명·규칙 문장 포함). 대부분 (요약) 대상의 묶음 행, 티어 0 플랫폼의 서울 리전·요금, GCP 서울 개별 단가(외부 IP, Media CDN), 일부 유휴 타임아웃·SLA다. 규칙으로 옮기기 전에 판정에 쓰이는 값부터 다시 확인한다.
- `[충돌]` 12건:
  1. CloudFront 오리진 keep-alive 범위: 쿼터 페이지 1–300초 vs Terraform 문서 상한 60.
  2. CloudFront 오리진 응답 타임아웃 범위: 쿼터 페이지 1–120초 vs Terraform 문서 최대 60초.
  3. CloudFront 무효화 지연: 개발자 가이드 "within a few seconds" vs 정적 웹사이트 백서 "several minutes".
  4. Cloudflare LB 모니터 최소 주기: create-monitor 문서 60(Pro)/15(Business)/10(Ent)초 vs limitations 문서 비엔터프라이즈 15초.
  5. ACM 유효기간·갱신 시점: ACM 문서 198일·45일 전 vs Terraform `aws_acm_certificate` 문서 395일·60일 전(사설 인증서 설명).
  6. Cloud Armor 기본 규칙 액션: 문서 deny vs Terraform(규칙 미지정 생성 시) allow.
  7. Cloud Armor `XFF_IP` 키 대체 동작: 문서 IP vs Terraform `ALL`.
  8. Cloud NAT TCP TIME_WAIT 기본: Google 문서 30 또는 120초(생성 시점) vs Terraform 120초.
  9. VPC 게이트웨이 엔드포인트 IPv6: 일반 페이지 IPv6/듀얼스택 지원 vs DynamoDB 페이지 IPv4만.
  10. Lambda ENI 생성 시간: 현행 문서 "several minutes"(Pending, 호출 불가) vs 2019 공식 블로그 "up to 90 seconds".
  11. Neon 사설 연결 플랜: "Scale plan" vs "Business and Scale".
  12. Upstash VPC 피어링: 보안 문서 Pro vs 가격 페이지 Enterprise 계약.
- 판정을 뒤집는 주요 발견:
  1. **CloudFront의 기본 권장 정책이 개인화 응답을 캐시한다.** CachingOptimized는 최소 TTL 1초라 `private`·`no-store`를 무시하고 캐시하고, 헤더 없는 응답은 86,400초 캐시한다. "동적용"으로 보이는 UseOriginCacheControlHeaders는 쿠키 전부를 캐시 키에 넣어 `Set-Cookie`까지 캐시해 재전송한다. Cloudflare도 Edge TTL override를 쓰면 `Set-Cookie`를 지우고 캐시한다.
  2. **NAT 포트는 목적지별로 고갈된다.** AWS NAT는 같은 목적지 기준 IP당 55,000(기본 EIP 2개 → 110,000), 350초 유휴 시 RST. Cloud NAT는 VM당 기본 64포트(정적)라 LLM·결제처럼 단일 호스트로 몰리는 호출에서 먼저 OUT_OF_RESOURCES가 난다. Cloud Run Direct VPC는 필요한 포트의 2배를 요구한다.
  3. **서버리스 사설 연결에는 숨은 고정비와 제약이 있다.** Serverless VPC Access 커넥터는 최소 2대이고 축소하지 않는다(e2-standard-4 2대면 서울 월 약 $251). Direct VPC는 /26 이상 서브넷, 인스턴스당 IP 2개, 인스턴스 쿼터 100–200이다. Cloud SQL·Memorystore의 피어링은 전이가 안 된다. Lambda VPC 함수는 625 Mbps로 고정되고 Function URL은 공용 전용이다. Supabase·Neon·Upstash의 사설 연결은 AWS 전용이라 GCP 서울에서는 공인 경로뿐이다.
  4. **엣지 보호의 기본값은 "보호 없음"이다.** AWS WAF·Cloud Armor는 관리형 규칙을 기본으로 넣지 않는다. AWS CommonRuleSet을 넣으면 8 KB 초과 본문과 User-Agent 없는 요청을 막아 업로드·웹훅이 깨진다. 레이트 리밋은 근사치이고 창 단위(AWS 60–600초, Cloudflare Free 10초 고정)와 지역별 카운터라 정확한 사용자 쿼터로 쓸 수 없다. CDN 뒤 WAF는 forwarded IP 설정 없이는 엣지 IP로 집계한다.
  5. **인증서·DNS의 자동화 전제가 바뀌었다.** ACM 공개 인증서는 198일·45일 전 갱신이고, 검증 CNAME이 남아 있으면서 사용 중이어야 한다. Let's Encrypt는 만료 메일(2025-06)과 OCSP(2025-08)를 끝냈고, 수명을 64일(2027-02)과 45일(2028-02)로 줄인다. Route 53·Cloud DNS 장애 조치는 전부 비정상이면 fail-open이고, HTTPS 헬스 체크는 인증서를 검증하지 않는다.
  6. **Terraform 기본값이 콘솔과 다르다.** `aws_vpc_endpoint.private_dns_enabled`는 기본 false다. Cloud SQL은 `ipv4_enabled`를 생략하면 공인 IP가 생기는데 CKV_GCP_60은 통과한다. `cloudflare_ruleset`은 진입점 ruleset 전체를 덮어쓴다. Checkov가 다루지 않는 리소스(Cloud NAT, Cloud CDN, Cloudflare, Vercel, Certificate Manager, `aws_vpc_endpoint`)는 plan JSON을 직접 검사해야 한다.
