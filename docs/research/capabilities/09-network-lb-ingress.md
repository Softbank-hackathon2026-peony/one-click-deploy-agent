# 네트워크 능력 표 ①: 로드밸런서, API 게이트웨이, 쿠버네티스 인그레스·Gateway, 플랫폼 내장 엣지 프록시

삭제된 절: 5.3 Caddy, 5.4 Traefik, 6.4 Render 엣지 프록시, 6.6 Fly.io 프록시, 사유: 부적격 출처 (2026-10-02. 부적격 출처에 기댄 표 행과 줄도 지웠다. 남은 절 번호는 그대로)

- 작성일: 2026-10-01
- 짝 문서: [README.md](README.md) §2.8 NW.* 능력 키, [../dimensions.md](../dimensions.md) (A2, A3, A7, D3, F1, F4, F5)
- 재료: [05-compute-tier1-2.md](05-compute-tier1-2.md) §1.3, [08-artifacts-compute.md](08-artifacts-compute.md), ../considerations/02-traffic-compute.md (T-079), 03-deploy-release.md (U-027, 타이밍 정렬), 05-security-compliance.md (S-064)

## 범위

요청 경로(사용자 → 엣지 프록시 → 로드밸런서·게이트웨이·인그레스 → 앱)에서 **연결을 받아 넘기는 구성 요소**를 다룬다. CDN 캐시, DNS, WAF, 인증서 발급, 출구 NAT, 사설 연결은 [10-network-edge-egress.md](10-network-edge-egress.md)에서 다룬다. 이 파일에서 해당 키는 대부분 `해당 없음(10 문서)`으로 적는다.

이 표의 용도는 두 가지다.
1. **경로 불일치 판정.** 같은 경로에 놓인 구성 요소끼리 숫자를 비교한다(§9 "경로 부등식 규칙 후보").
2. **산출물 생성.** 구성 요소마다 끝에 "생성 산출물" 절을 둔다.

표기 규칙은 다음과 같다.
- 값 앞의 `[L3]`·`[L4]`·`[L7]`·`[TLS]`는 그 값이 작동하는 OSI 계층이다.
- 출처는 `URL · "원문 인용" · 2026-10-01` 형식이다.
- `미확인`은 연 공식 페이지에서 값을 찾지 못한 경우다.
- `[충돌]`은 공식 페이지끼리 값이 다른 경우다.
- `[PL]`은 AWS Price List 오퍼 파일이다. `https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/<서비스>/current/ap-northeast-2/index.json`을 curl과 jq로 읽었다(AWSELB 게시일 2026-09-11, AmazonApiGateway 게시일 2026-09-21).
- 월 비용은 730시간 기준이다.

## 목차

- [0. 요약 비교표](#0-요약-비교표)
- [1. AWS](#1-aws)
  - 1.1 Application Load Balancer
  - 1.2 Network Load Balancer
  - 1.3 Gateway Load Balancer (요약)
  - 1.4 API Gateway — HTTP API
  - 1.5 API Gateway — REST API
  - 1.6 API Gateway — WebSocket API
  - 1.7 Lambda Function URL
  - 1.8 ECS Express Mode가 만드는 ALB
  - 1.9 AWS Load Balancer Controller (Ingress·Service 어노테이션)
- [2. Google Cloud](#2-google-cloud)
  - 2.1 전역 외부 Application LB (EXTERNAL_MANAGED)
  - 2.2 리전 외부 Application LB
  - 2.3 클래식 Application LB (GKE Ingress 기본)
  - 2.4 외부 패스스루 Network LB
  - 2.5 외부 프록시 Network LB
  - 2.6 내부 LB (내부 Application LB, 내부 패스스루 NLB)
  - 2.7 Cloud Run 기본 엔드포인트(`*.run.app`)와 도메인 매핑
  - 2.8 GKE Gateway API (GatewayClass별)
  - 2.9 서버리스 NEG
- [3. Azure](#3-azure) — 3.1 Container Apps 내장 인그레스 (요약)
- [4. 쿠버네티스](#4-쿠버네티스)
  - 4.1 ingress-nginx (은퇴, 아카이브)
  - 4.2 Gateway API 구현 대표: Envoy Gateway
  - 4.3 Service type LoadBalancer
- [5. 자체 운영 리버스 프록시](#5-자체-운영-리버스-프록시)
  - 5.1 nginx
  - 5.2 Envoy
  - 5.3 Caddy — 삭제됨(부적격 출처, 2026-10-02)
  - 5.4 Traefik — 삭제됨(부적격 출처, 2026-10-02)
- [6. 티어 0 플랫폼 내장 엣지 프록시](#6-티어-0-플랫폼-내장-엣지-프록시)
  - 6.1 Vercel
  - 6.2 Netlify
  - 6.3 Cloudflare (프록시 모드)
  - 6.4 Render — 삭제됨(부적격 출처, 2026-10-02)
  - 6.5 Railway
  - 6.6 Fly.io (fly-proxy) — 삭제됨(부적격 출처, 2026-10-02)
- [7. 앱 서버 기본값 (부등식의 반대편)](#7-앱-서버-기본값-부등식의-반대편)
- [8. 조사 결과 요약](#8-조사-결과-요약)
- [9. 경로 부등식 규칙 후보](#9-경로-부등식-규칙-후보)

---

## 0. 요약 비교표

- "유휴"는 클라이언트 쪽 또는 LB↔앱 쪽 유휴 연결 타임아웃이다. GCP L7은 둘이 다르므로 함께 적는다.
- "백엔드 타임아웃"은 앱 응답을 기다리는 최대 시간이다.
- "드레이닝"은 대상을 뺄 때 진행 중 연결을 기다리는 기본값이다.

| 구성 요소 | 계층 | 유휴 타임아웃 (기본 / 최대) | 백엔드 타임아웃 | 웹소켓 | 본문 한도 | 드레이닝 기본 | 클라이언트 IP | 트래픽 분할 | 서울 | 최소 비용 (월) |
|---|---|---|---|---|---|---|---|---|---|---|
| AWS ALB | L7 종단 | 60초 / 4,000초 (클라이언트 keepalive 3,600초) | 별도 없음, 유휴 60초가 상한 | 지원, 지속 한도 미확인 | 미확인 (Lambda 대상 1 MB) | 300초 (0~3,600) | XFF append | 대상 그룹 가중치 0~999 | 있음 | $16.43 + LCU $0.008/시간 |
| AWS NLB | L4 통과(TLS 종단 가능) | TCP 350초 (60~6,000), TLS 350초 고정, UDP 120초 고정 | 해당 없음 | TCP 통과(명시 문구 미확인) | 없음(L4) | 300초 | 원본 IP 보존(instance, UDP), PROXY v2 | 미확인 | 있음 | $16.43 + NLCU $0.006/시간 ⚠️근거없음 |
| AWS GWLB | L3 통과 | TCP 350초, UDP 120초 | 해당 없음 | 해당 없음 | 해당 없음 | 미확인 | 원본 패킷 그대로 | 해당 없음 | 있음 | $9.13 + GLCU $0.004/시간 |
| API GW HTTP API | L7 종단 | 미확인 | **30초 고정** | 없음 | 10 MB | 해당 없음 | `sourceIp` | 없음 (카나리 미지원) | 있음 | $0 + $1.23/100만 |
| API GW REST API | L7 종단 | 310초 | 29초 (Regional·Private는 상향 가능) / 스트리밍 15분 | 없음 | 10 MB | 해당 없음 | `sourceIp` | 스테이지 카나리 % | 있음 | $0 + $3.50/100만 |
| API GW WebSocket | L7 종단 | 10분 | 통합 29초 | 연결 최대 2시간 | 메시지 128 KB | 해당 없음 | `sourceIp` | 없음 | 있음 | $0 + 메시지 $1.14/100만 + 연결 분 |
| Lambda Function URL | L7 종단 | 미확인 | 함수 타임아웃 (최대 900초) | 미확인(지원 문구 없음) | 6 MB (스트리밍 200 MB) | 해당 없음 | `requestContext.http.sourceIp` | 별칭 가중치(2버전) | 미확인 | $0 |
| ECS Express ALB | L7 | ALB와 같음으로 추정, Express 값은 미확인 | 미확인 | 지원 | 미확인 | 미확인 | XFF | Express 카나리 | 있음 | ALB와 같음, 25개 서비스가 공유 |
| AWS LB Controller | (ALB/NLB 생성) | 어노테이션으로 ALB 값 지정 | — | — | — | 어노테이션 | ip 모드 + readiness gate | `actions.*` 가중치 | 있음 | ALB/NLB 비용 |
| GCP 전역 외부 ALB | L7 종단 (GFE) | 클라이언트 610초 (5~1,200), 백엔드 **600초 고정** | 30초 (1~86,400 실효) | 활성 연결 24시간 | 미확인 (헤더 60 KiB) | API 기본 미확인 / TF 300 | XFF `<client>,<lb>` + 커스텀 헤더 | 가중치 0~1000 | 전역 | 전달 규칙 $18.25 (us-central1 기준) |
| GCP 리전 외부 ALB | L7 종단 (Envoy) | 클라이언트 [충돌] 600/610초, 백엔드 600초 | 30초, `routeAction.timeout` 우선 | 활성 연결은 타임아웃 무시 | 미확인 | 미확인 (0=꺼짐) | XFF + 커스텀 헤더 | 있음 | 미확인 | $18.25 + $0.008/GiB (us-central1) |
| GCP 클래식 ALB (GKE Ingress) | L7 종단 | 클라이언트 610초 고정, 백엔드 600초 | **30초** | **백엔드 타임아웃에 끊김** | 미확인 (헤더 64 KiB) | **0** | XFF | **없음** | 전역 | $18.25 |
| GCP 외부 패스스루 NLB | L4 통과 (DSR) | 연결 추적 60초 고정 | 무시됨 | TCP 통과 | 없음 | 미확인 (0=꺼짐) | 원본 IP 보존 | 없음 | 미확인 | $18.25 |
| GCP 외부 프록시 NLB | L4 프록시 (TLS 종단 가능) | 백엔드 타임아웃 = 유휴 30초 | (유휴) | TCP 통과, 30초 유휴에 끊김 | 없음 | 미확인 (0=꺼짐) | PROXY v1 (기본 꺼짐) | 없음 | 미확인 | $18.25 |
| GCP 내부 ALB / 내부 패스스루 NLB | L7 / L4 | ALB 610초(5~1,200)·백엔드 600초 / NLB 600초 | 30초 / 무시 | 활성 연결 유지 | 미확인 | 미확인 (0=꺼짐) | XFF 2개 추가 / 보존 | ALB 있음 | 미확인 | 프록시 3개 $54.75 + $0.008/GiB (us-central1) |
| Cloud Run `*.run.app` | L7 종단 | 미확인 | 300초 (최대 3,600) | 요청 타임아웃까지 | HTTP/1 32 MiB, HTTP/2 무제한 | 미확인 | XFF 미확인 | 리비전 % + 태그 | 있음 (도메인 매핑은 **서울 없음**) | $0 |
| GKE Gateway (managed 클래스) | L7 | 백엔드 LB에 따름 | `GCPBackendPolicy` 30초 | 전역 managed는 24시간 | 미확인 | **0** | XFF | `backendRefs.weight` (gxlb 제외) | 있음 | LB 비용 |
| 서버리스 NEG | (ALB 백엔드) | — | **60분 고정** (변경 불가) | ALB 규칙 | — | 해당 없음 | ALB와 같음 | URL 맵 | — | LB 비용 |
| Azure Container Apps 인그레스 | L7 (Envoy) | 프리미엄 4~30분 | **240초** | 지원, 한도 미확인 | 미확인 | 프리미엄 종료 유예 [충돌] | XFF append | 리비전 가중치 | Korea Central | $0 |
| ingress-nginx | L7 | 클라이언트 75초, upstream 60초 | proxy-read 60초 | 60초 무응답에 끊김 | **1m** | worker-shutdown 240초 | XFF 무시(기본) | canary-weight | — | 노드·LB |
| Envoy Gateway | L7 | 클라이언트 1시간, 업스트림 1시간 | **15초** (Envoy 라우트 기본) | 지원 | 버퍼 32 KiB (본문 한도 아님) | drain 60초 | `clientIPDetection` 설정 필요 | `backendRefs.weight` | — | 노드·LB |
| k8s Service LoadBalancer | L4 | 클라우드 LB에 따름 | — | 통과 | 없음 | — | `Cluster`(기본)는 IP 숨김, `Local`은 보존 | 없음 | — | 클라우드 LB |
| nginx | L7 | 클라이언트 75초, upstream 60초 | proxy_read 60초 | 헤더 수동 설정, 60초 무응답에 끊김 | **1m** | — | real_ip 수동 | upstream weight | — | — |
| Envoy | L7 | 1시간 / 스트림 5분 | **15초** | `upgrade_configs` 필요 | 버퍼 1 MiB | drain 5초 | 설정 | 가중치 클러스터 | — | — |
| Vercel 엣지 | L7 | 미확인 | 외부 rewrite 120초 | 함수 WS 베타(최대 실행 시간까지) | 함수 4.5 MB | — | XFF **덮어씀** | Rolling Releases % | 04 문서 | 04 문서 |
| Netlify 엣지 | L7 | 미확인 | 프록시 rewrite **26초** | 미확인 | 함수 6 MB | — | `context.ip` | 분기 split(정적만) | 04 문서 | 04 문서 |
| Cloudflare 프록시 | L7 | 클라이언트 400초, 오리진 900초 | **125초** (Ent 최대 6,000) | 모든 플랜, 재시작 시 끊김 | 100 MB (Free·Pro) | — | `CF-Connecting-IP`, XFF append | LB 애드온 가중치 | 미확인 | 04 문서 |
| Railway | L7 | HTTP/1.1 60초 | 15분 (무전송 5분) | 무기한 | 크기 미확인 (업로드 5분 내) | 미확인 | `X-Real-IP` | 없음 | 04 문서 | 04 문서 |

---

## 1. AWS

공통 출처 약어는 쓰지 않는다. 모든 행에 전체 URL을 적는다. Terraform 인자 확인은 Registry 문서의 원본 마크다운(`https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/<리소스>.html.markdown`, provider v6.67.0)으로 했다.

## 1.1 AWS Application Load Balancer — 인터넷 대상, HTTPS 리스너
- 계열: 네트워크-로드밸런서 (L7)
- 서울 리전: 있음 ([PL] AWSELB ap-northeast-2 · "$0.0225 per Application LoadBalancer-hour (or partial hour)" · 2026-10-01)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| NW.layer | [L7] 종단 프록시. 클라이언트 연결과 대상 연결이 따로다. 대상 연결은 keep-alive로 재사용하고 다중화한다. 미리 열어 두는 연결은 없다 | — | https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/how-elastic-load-balancing-works.html · "The keep-alive header is supported on backend connections by default." / "Classic Load Balancers use pre-open connections, but Application Load Balancers do not." · 2026-10-01 |
| NW.idle_timeout | [L7] 유휴 타임아웃 기본 **60초**, 1~4,000초, 변경 가능. 클라이언트 keepalive 기간은 기본 3,600초(60~604,800). HTTP/2 PING은 유휴를 리셋하지 않는다. **앱 유휴 타임아웃 > LB 유휴 타임아웃이어야 한다**(아니면 502) | 대상 쪽 연결에도 같은 유휴 값이 적용된다 | https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_LoadBalancerAttribute.html · "The valid range is 1-4000 seconds. The default is 60 seconds." / "client_keep_alive.seconds … valid range is 60-604800 seconds. The default is 3600 seconds." · https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-load-balancer-attributes.html · "configure the idle timeout of your application to be larger than the idle timeout configured for the load balancer" / "Application Load Balancers do not support HTTP/2 PING frames. These do not reset the connection idle timeout." · 2026-10-01 |
| NW.request_timeout | [L7] 별도의 백엔드 응답 타임아웃이 없다. 응답 바이트가 유휴 타임아웃(기본 60초) 넘게 오지 않으면 끊긴다(504). 그래서 실질 상한은 유휴 타임아웃이다 | 별도 "요청 타임아웃" 속성이 없다는 문장은 미확인 | https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-load-balancer-attributes.html · "By default, Elastic Load Balancing sets the idle timeout value for your load balancer to 60 seconds." · 2026-10-01 |
| NW.websocket | [L7] 웹소켓 기본 지원. 지속 한도는 문서에 없다(미확인). 데이터가 유휴 타임아웃보다 길게 없으면 끊긴다. 업그레이드 뒤에는 리스너 규칙과 WAF가 적용되지 않는다. 헬스 체크는 웹소켓을 지원하지 않는다. SSE는 일반 HTTP 응답이라 유휴 규칙만 적용된다(추론) | Lambda 대상은 웹소켓 불가 | https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-listeners.html · "Application Load Balancers provide native support for WebSockets." · https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/how-elastic-load-balancing-works.html · "if there is a connection upgrade… listener routing rules and AWS WAF integrations no longer apply" · https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html · "Health checks do not support WebSockets." · 2026-10-01 ⚠️근거없음 |
| NW.protocols | [L7] 프런트: HTTP/0.9·1.0·1.1, HTTP/2(HTTPS 리스너만, 연결당 병렬 128). HTTP/3은 미확인. 대상: 기본 HTTP/1.1, HTTP/2·gRPC 선택(HTTPS 리스너 + instance/ip 대상) | — | https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/how-elastic-load-balancing-works.html · "support the following protocols on front-end connections: HTTP/0.9, HTTP/1.0, HTTP/1.1, and HTTP/2" · https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-target-groups.html · "By default, Application Load Balancers send requests to targets using HTTP/1.1… using HTTP/2 or gRPC." · 2026-10-01 |
| NW.body_size | [L7] 요청 줄 16K, 단일 헤더 16K, 요청 헤더 전체 64K, 응답 헤더 전체 32K. 모두 조정 불가. **본문 한도는 문서에 없다(미확인)**. Lambda 대상은 요청·응답 각 1 MB | — | https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-limits.html · "Request line 16 K No / Single header 16 K No / Entire response header 32 K / Entire request header 64 K" · https://docs.aws.amazon.com/elasticloadbalancing/latest/application/lambda-functions.html · "maximum size of the request body… is 1 MB… response JSON… is 1 MB. WebSockets are not supported." · 2026-10-01 |
| NW.draining | [L7] 등록 해제 지연 기본 **300초**, 0~3,600초. slow start 기본 0(꺼짐), 30~900초. LOR·weighted_random과 함께 쓸 수 없다 | ECS stopTimeout 최대 120초보다 길다(05 문서) | https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_TargetGroupAttribute.html · "The range is 0-3600 seconds. The default value is 300 seconds." / "The range is 30-900 seconds (15 minutes). The default is 0 seconds (disabled)." · 2026-10-01 |
| NW.health_check | [L7] 기본값: HTTP, 경로 `/`(gRPC는 `/AWS.ALB/healthcheck`), 간격 30초, 타임아웃 5초, 정상 5회, 비정상 2회, 매처 200. **전부 비정상이면 fail-open**(모든 대상으로 보낸다). 대상 그룹 정상 임계(`target_group_health.*`)로 DNS 장애 조치나 비정상 라우팅 기준을 바꿀 수 있다. [충돌] Terraform `health_check` 기본값은 정상 3·비정상 3·타임아웃 6초(HTTP)로 AWS 문서(5/2/5초)와 다르다 | 생성 시 명시해야 한다 | https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html · "If a target group contains only unhealthy registered targets, the load balancer routes requests to all those targets… fails open." · https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lb_target_group.html.markdown · "`healthy_threshold`… Defaults to 3." · 2026-10-01 |
| NW.tls | [TLS] ALB에서 종단, ACM 인증서. 기본 보안 정책은 [충돌] 생성 방법에 따라 다르다: 콘솔은 `ELBSecurityPolicy-TLS13-1-2-Res-PQ-2025-09`, CLI·CFN·CDK·Terraform은 `ELBSecurityPolicy-2016-08`(TLS 1.0 허용). mTLS: passthrough(기본) / verify | — | https://docs.aws.amazon.com/elasticloadbalancing/latest/application/describe-ssl-policies.html · "Console – The default security policy is ELBSecurityPolicy-TLS13-1-2-Res-PQ-2025-09… Other methods… ELBSecurityPolicy-2016-08" · https://docs.aws.amazon.com/elasticloadbalancing/latest/application/mutual-authentication.html · "Mutual TLS passthrough… Mutual TLS verify" · 2026-10-01 |
| NW.client_ip | [L7] `X-Forwarded-For` 처리 모드 append(기본) / preserve / remove. `X-Forwarded-Proto`·`X-Forwarded-Port`를 붙인다. 앱은 마지막 1홉(ALB)을 신뢰해야 한다(S-064) | `xff_client_port` 기본 꺼짐 | https://docs.aws.amazon.com/elasticloadbalancing/latest/application/x-forwarded-headers.html · "The possible values are append, preserve, and remove. The default is append." · 2026-10-01 |
| NW.routing | [L7] 호스트·경로·헤더 규칙. forward 액션에 대상 그룹 최대 5개, 가중치 0~999(카나리·블루/그린). 대상 그룹 고정(AWSALBTG). 리다이렉트·고정 응답 | 리스너당 규칙 100 | https://docs.aws.amazon.com/elasticloadbalancing/latest/application/rule-action-types.html · "Each target group weight is a value from 0 to 999." · https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-limits.html · "Target Groups per Action per Application Load Balancer 5 No" · 2026-10-01 |
| NW.scaling | [L7] 자동 확장(LCU). 예약 LCU(사전 증설 수단, 단가 $0.008/예약 LCU-시간). 리전당 ALB 50, ALB당 대상 1,000 | — | [PL] AWSELB ap-northeast-2 · "$0.008 per reserved Application load balancer capacity unit-hour" · https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-limits.html · "Application Load Balancers per Region 50 Yes" · 2026-10-01 |
| NW.availability | [L7] 존 2개 이상. 교차 영역은 LB 수준에서 항상 켜짐(대상 그룹 단위로 끌 수 있음). SLA 99.99% | — | https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-target-group-attributes.html · "cross-zone load balancing is always turned on at the load balancer level, and cannot be turned off" · https://aws.amazon.com/elasticloadbalancing/sla/ · "Less than 99.99% but greater than or equal to 99.0% 10%" · 2026-10-01 |
| NW.caching | 해당 없음 | — | — |
| NW.security | [L7] AWS WAF 연동(WAF fail-open 기본 꺼짐). desync 완화 기본 defensive. 잘못된 헤더 필드 버림 기본 꺼짐. 삭제 보호 기본 꺼짐 | — | https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_LoadBalancerAttribute.html · "waf.fail_open.enabled… The default is false." / "routing.http.drop_invalid_header_fields.enabled… The default is false." · https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-load-balancer-attributes.html · "The default is the defensive mode" · 2026-10-01 |
| NW.dns | 해당 없음(10 문서). ALB는 DNS 이름만 주고 IP가 바뀐다. 고정 IP가 필요하면 NLB를 앞에 둔다(추론) | — | — ⚠️근거없음 |
| NW.egress | 해당 없음(10 문서) | — | — |
| NW.private_connectivity | [L3] 내부 ALB(`internal = true`). PrivateLink 노출은 NLB 경유(10 문서) | — | — |
| NW.regions | 서울 있음 | — | [PL] AWSELB ap-northeast-2 · 2026-10-01 |
| NW.cost_floor | 서울 **$0.0225/시간(월 $16.43)** + LCU $0.008/시간. LCU = 새 연결 25/초, 활성 연결 3,000/분, 처리 1 GB/시간(Lambda 대상은 0.4 GB), 규칙 평가 1,000/초 중 가장 큰 값. + 공인 IPv4 $0.005/시간/개(05 문서). mTLS 트러스트 스토어 $0.005/시간 | — | [PL] AWSELB ap-northeast-2 · "$0.0225 per Application LoadBalancer-hour (or partial hour)" / "$0.008 per used Application load balancer capacity unit-hour (or partial hour)" / "$0.005 per associated Application load balancer Trust Store unit-hour" · https://aws.amazon.com/elasticloadbalancing/pricing/ · "An LCU contains: 25 new connections per second. 3,000 active connections per minute" · 2026-10-01 |

### 비용 구조
- 최소 월 고정비: $16.43 + 공인 IPv4(AZ 수만큼, 개수 근거 미확인) + LCU 최소분.
- 변동: 4개 차원 중 최대 LCU. 웹소켓이 많은 앱은 활성 연결 차원(3,000/LCU)이 지배한다.
- 무료 등급: 미확인.
- 과금 함정: ECS Express는 VPC당 ALB 하나를 서비스 25개가 공유해 서비스당 비용이 내려간다(1.8).

### 교체 계열 정보
- ALB ↔ GCP 전역 외부 ALB 차이:
  - 유휴 의미: ALB는 유휴 60초 하나다. GCP는 백엔드 요청 타임아웃 30초와 keepalive 600초가 따로다.
  - fail-open: ALB는 fail-open이다. GCP는 502·503을 낸다.
  - 웹소켓: ALB는 유휴로만 끊는다. GCP 클래식은 백엔드 타임아웃에 끊는다.
- ALB → API Gateway HTTP API: 30초 고정, 10 MB, 웹소켓 없음.

### 함정
- 앱 keep-alive가 60초보다 짧으면(uvicorn 5, Node 5, gunicorn 2) 간헐 502가 난다(§9 R1).
- 등록 해제 지연 300초는 ECS stopTimeout 최대 120초보다 길다. 배포가 대상마다 최대 5분 늦어진다.
- Terraform 헬스 체크 기본값이 AWS 문서와 다르다(3/3/6초).
- Terraform 리스너 기본 TLS 정책 `ELBSecurityPolicy-2016-08`은 TLS 1.0을 허용한다(Checkov CKV_AWS_103 실패).
- 대상 그룹이 전부 비정상이면 fail-open이다. readiness가 DB에 묶여 있어도 사이트가 완전히 꺼지지는 않는다. 대신 비정상 인스턴스로 요청이 간다.

### 생성 산출물
- Terraform 리소스: `aws_lb`(`load_balancer_type = "application"`), `aws_lb_target_group`, `aws_lb_listener`(HTTPS + HTTP 301 리다이렉트), `aws_lb_listener_rule`, `aws_acm_certificate`, `aws_acm_certificate_validation`, `aws_wafv2_web_acl_association`(F5).
- 요구에 따라 반드시 명시할 속성:
  - A2·A3: `aws_lb.idle_timeout`(기본 60). 기준은 "요청 최장 무전송 구간 + 여유"이고, 웹소켓은 하트비트 간격보다 크게 둔다. 그리고 **앱 keep-alive를 이 값보다 크게** 바꾸는 코드 수정이 짝으로 나간다.
  - `aws_lb.client_keep_alive`(기본 3600).
  - F4:
    - `aws_lb_target_group.deregistration_delay`(기본 300 → 최장 요청 시간 이상, stopTimeout 이하. 보통 30~60).
    - `slow_start`(A5가 무거우면 30~).
  - F4·F1: `aws_lb_target_group.health_check { path, matcher = "200", interval, timeout, healthy_threshold, unhealthy_threshold }`. Terraform 기본값이 AWS와 다르므로 전부 명시한다.
  - 프로토콜: `protocol_version`(gRPC면 `GRPC`).
  - F5:
    - `aws_lb_listener.ssl_policy`(예: `ELBSecurityPolicy-TLS13-1-2-2021-06`, 정책 이름 원문은 describe-ssl-policies 문서로 확인).
    - `aws_lb.drop_invalid_header_fields = true`, `desync_mitigation_mode = "defensive"` 이상, `enable_deletion_protection = true`.
    - `xff_header_processing_mode = "append"`(기본값이지만 명시).
  - 카나리: `aws_lb_listener.default_action { type = "forward" forward { target_group { arn, weight } … stickiness { enabled, duration } } }`.
- Checkov가 보지 않는 것: `idle_timeout`, `deregistration_delay`와 앱 값의 부등식. plan JSON에서 직접 비교한다(§9).
- 배포 후 검증:
  - `aws elbv2 describe-load-balancer-attributes --load-balancer-arn <ARN>`으로 `idle_timeout.timeout_seconds`, `routing.http.xff_header_processing.mode`를 확인한다.
  - `aws elbv2 describe-target-group-attributes --target-group-arn <ARN>`으로 `deregistration_delay.timeout_seconds`를 확인한다.
  - `aws elbv2 describe-target-health`로 전부 healthy인지 확인한다.
  - 유휴 경계 시험: 같은 연결로 (LB 유휴 − 1)초 간격 요청을 반복하고 502가 0건인지 본다. 롤링 배포 중 스모크도 한다.

---

## 1.2 AWS Network Load Balancer
- 계열: 네트워크-로드밸런서 (L4)
- 서울 리전: 있음 ([PL] AWSELB ap-northeast-2 · "$0.0225 per Network LoadBalancer-hour (or partial hour)" · 2026-10-01)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| NW.layer | [L4] 연결 단위 통과(TCP·UDP). TLS 리스너는 [TLS] 종단. 프로토콜: TCP, TLS, UDP, TCP_UDP, QUIC, TCP_QUIC | — | https://docs.aws.amazon.com/elasticloadbalancing/latest/network/load-balancer-listeners.html · "Protocols: TCP, TLS, UDP, TCP_UDP, QUIC, TCP_QUIC" / "With a TCP listener, the load balancer passes encrypted traffic through to the targets without decrypting it." · 2026-10-01 |
| NW.idle_timeout | [L4] TCP 기본 **350초**, 60~6,000초(리스너 속성 `tcp.idle_timeout.seconds`). [TLS] TLS 리스너 350초 고정. UDP 120초 고정 | — | https://docs.aws.amazon.com/elasticloadbalancing/latest/network/network-load-balancers.html · "default idle timeout value for TCP flows is 350 seconds, but can be updated to any value between 60-6000 seconds" · https://docs.aws.amazon.com/elasticloadbalancing/latest/network/update-idle-timeout.html · "The connection idle timeout for TLS listeners is 350 seconds and can't be modified." · 2026-10-01 |
| NW.request_timeout | 해당 없음(L4, 요청 개념 없음) | — | — |
| NW.websocket | [L4] TCP 통과라 프로토콜과 무관하게 연결은 유휴 350초 안에서 유지된다(추론, 웹소켓 명시 문구 미확인) | — | 미확인 ⚠️근거없음 |
| NW.protocols | [L4] 위 NW.layer. HTTP/2·gRPC는 TCP 통과로 앱이 처리 | — | 같은 출처 |
| NW.body_size | 해당 없음(L4) | — | — |
| NW.draining | [L4] 등록 해제 지연 기본 300초. 해제 시 연결 종료(`deregistration_delay.connection_termination.enabled`) 기본 false. 비정상 대상 연결 종료 기본 true, 드레이닝 간격 기본 0 | — | https://docs.aws.amazon.com/elasticloadbalancing/latest/network/edit-target-group-attributes.html · "changes the state of a deregistering target to unused after 300 seconds" · https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_TargetGroupAttribute.html · "target_health_state.unhealthy.connection_termination.enabled… The default is true." · 2026-10-01 |
| NW.health_check | [L4] 기본 TCP, 간격 30초, 타임아웃 HTTP 6초·TCP/HTTPS 10초, 정상 5, 비정상 2. **모든 존에서 전부 비정상이면 fail-open** | — | https://docs.aws.amazon.com/elasticloadbalancing/latest/network/target-group-health-checks.html · "If all targets fail health checks at the same time in all enabled Availability Zones, the load balancer fails open." · 2026-10-01 |
| NW.tls | [TLS] TLS 리스너에서 종단 가능(ACM). TCP 리스너는 통과 | — | https://docs.aws.amazon.com/elasticloadbalancing/latest/network/load-balancer-listeners.html · 2026-10-01 |
| NW.client_ip | [L4] 원본 IP 보존: instance 대상은 켜짐. ip 대상(TCP·TLS)은 꺼짐. UDP·TCP_UDP·QUIC은 항상 켜짐. PROXY protocol v2(`proxy_protocol_v2.enabled`) 기본 false | ip 대상이면 PROXY v2나 보존 속성을 켜야 한다 | https://docs.aws.amazon.com/elasticloadbalancing/latest/network/edit-target-group-attributes.html · "Instance type target groups: Enabled… IP type target groups (TCP, TLS): Disabled" · https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_TargetGroupAttribute.html · "proxy_protocol_v2.enabled… The default is false." · 2026-10-01 |
| NW.routing | [L4] 포트 단위 리스너 → 대상 그룹. 가중치 분할은 미확인 | — | 미확인 ⚠️근거없음 |
| NW.scaling | [L4] 자동. 리전당 NLB 50, NLB당 대상 3,000, AZ당 500 | — | https://docs.aws.amazon.com/elasticloadbalancing/latest/network/load-balancer-limits.html · "Network Load Balancers per Region 50 Yes" · 2026-10-01 |
| NW.availability | [L4] AZ별 노드. **교차 영역 기본 꺼짐** → AZ마다 대상이 고르지 않으면 쏠린다. AZ당 탄력적 IP(고정 IP) | — | https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_LoadBalancerAttribute.html · "The default for Network Load Balancers and Gateway Load Balancers is false." · https://docs.aws.amazon.com/elasticloadbalancing/latest/network/create-network-load-balancer.html · "you can select an Elastic IP address for each Availability Zone." · 2026-10-01 |
| NW.caching | 해당 없음 | — | — |
| NW.security | [L4] 보안 그룹 지원. **생성 시 붙이지 않으면 나중에 붙일 수 없다**. WAF 없음 | — | https://docs.aws.amazon.com/elasticloadbalancing/latest/network/load-balancer-security-groups.html · "If you create a Network Load Balancer without associating any security groups, you can't associate them… later on." · 2026-10-01 |
| NW.dns | 해당 없음(10 문서). AZ별 고정 IP로 A 레코드가 가능하다 | — | — |
| NW.egress | 해당 없음 | — | — |
| NW.private_connectivity | [L4] PrivateLink 엔드포인트 서비스의 앞단(10 문서) | — | — |
| NW.regions | 서울 있음 | — | [PL] · 2026-10-01 |
| NW.cost_floor | 서울 $0.0225/시간(월 $16.43) + NLCU $0.006/시간. NLCU(TCP) = 새 연결 800/초, 활성 100,000, 1 GB/시간. TLS는 새 연결 50/초, 활성 3,000 | — | [PL] AWSELB ap-northeast-2 · "$0.006 per used Network load balancer capacity unit-hour (or partial hour)" · https://aws.amazon.com/elasticloadbalancing/pricing/ · "an NLCU contains: • 800 new TCP connections per second. • 100,000 active TCP connections" · 2026-10-01 |

### 비용 구조
월 $16.43 + NLCU. 장시간 연결이 많을 때 ALB보다 싸다(활성 연결 100,000/NLCU 대 3,000/LCU).

### 교체 계열 정보
ALB → NLB로 바꾸면 L7 기능이 사라진다: 경로 라우팅, XFF, WAF, HTTP 헬스 체크 외 L7. 클라이언트 IP는 PROXY v2나 IP 보존으로 받는다. 이때 앱 쪽에 PROXY 파싱이 필요하다(uvicorn `--proxy-headers`는 PROXY protocol이 아님, 별도 처리 필요 — 추론). ⚠️근거없음

### 함정
- ip 대상(EKS·Fargate)에서 원본 IP 보존이 기본 꺼짐이다.
- 보안 그룹을 나중에 붙일 수 없다.
- 교차 영역 기본 꺼짐.
- PROXY v2를 켜면 앱(또는 앞단 nginx)이 반드시 파싱해야 한다. 아니면 모든 요청이 400이 된다(추론). ⚠️근거없음

### 생성 산출물
- Terraform 리소스: `aws_lb`(`load_balancer_type = "network"`), `aws_lb_target_group`(`protocol = "TCP"`), `aws_lb_listener`(`tcp_idle_timeout_seconds`, 기본 350, 60~6000).
- 반드시 명시할 속성:
  - A3: `aws_lb_listener.tcp_idle_timeout_seconds`.
  - 클라이언트 IP: `aws_lb_target_group.preserve_client_ip`(기본값 문서에 명시 없음) 또는 `proxy_protocol_v2 = true`.
  - F4: `deregistration_delay`, `connection_termination`(기본 false).
  - F1: `aws_lb.enable_cross_zone_load_balancing = true`(NLB 기본 false).
  - F5: `aws_lb.security_groups`(생성 시에만).
- Checkov:
  - CKV_AWS_152 "Ensure that Load Balancer (Network/Gateway) has cross-zone load balancing enabled"
  - CKV_AWS_91, CKV_AWS_150
  - CKV_AWS_103(TLS 리스너)
- 배포 후 검증:
  - `aws elbv2 describe-listener-attributes --listener-arn <ARN>`(명령 원문 미확인) ⚠️근거없음
  - `describe-target-group-attributes`
  - 앱 로그에서 원본 IP가 찍히는지 본다.

---

## 1.3 AWS Gateway Load Balancer (요약)
- 계열: 네트워크-로드밸런서 (L3, 보안 어플라이언스 삽입용). 웹 앱 진입점이 아니다.
- 서울 리전: 있음 ([PL] AWSELB ap-northeast-2 · "$0.0125 per Gateway LoadBalancer-hour (or partial hour) in Asia Pacific (Seoul)" · 2026-10-01)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| NW.layer | [L3] 투명 통과. GENEVE 6081 캡슐화로 방화벽 어플라이언스에 넘긴다 | — | https://docs.aws.amazon.com/elasticloadbalancing/latest/gateway/introduction.html · "operates at the third layer of the Open Systems Interconnection (OSI) model, the network layer" · https://docs.aws.amazon.com/elasticloadbalancing/latest/gateway/target-groups.html · "Protocol: GENEVE Port: 6081" · 2026-10-01 |
| NW.idle_timeout | [L3] TCP 350초(60~6,000, 5-튜플 고정일 때만 변경), UDP 등 120초 고정 | — | https://docs.aws.amazon.com/elasticloadbalancing/latest/gateway/gateway-load-balancers.html · "default idle timeout value for TCP flows is 350 seconds" / "UDP flows to 120 seconds. This cannot be changed." · 2026-10-01 |
| NW.request_timeout / NW.websocket / NW.protocols / NW.body_size | 해당 없음 | — | — |
| NW.draining / NW.health_check | 미확인 | — | — |
| NW.tls / NW.client_ip / NW.routing | 해당 없음(패킷 그대로 전달) | — | — |
| NW.scaling / NW.availability | 미확인 | — | — |
| NW.caching / NW.dns / NW.egress | 해당 없음 | — | — |
| NW.security | [L3] 서드파티 방화벽 삽입 수단 | — | 위 introduction |
| NW.private_connectivity | GWLB 엔드포인트(라우팅 테이블로 삽입, 10 문서) | — | — |
| NW.regions | 서울 있음 | — | [PL] |
| NW.cost_floor | $0.0125/시간(월 $9.13) + GLCU $0.004/시간 | — | [PL] AWSELB ap-northeast-2 · "$0.0040 per used Gateway load balancer capacity unit-hour" · 2026-10-01 |

### 비용 구조 / 교체 계열 정보 / 함정
- 판정에서는 "요구 F5가 서드파티 방화벽 의무일 때만" 나온다. 일반 웹 앱에는 과잉이다.
- 함정: 경로에 들어가면 TCP 350초 유휴가 앱 앞에 하나 더 생긴다.

### 생성 산출물
- `aws_lb`(`load_balancer_type = "gateway"`), `aws_lb_target_group`(`protocol = "GENEVE"`, `port = 6081`), `aws_vpc_endpoint`(`vpc_endpoint_type = "GatewayLoadBalancer"`). 마지막 리소스의 인자 원문은 미확인.
- Checkov CKV_AWS_152(교차 영역).
- 검증: 어플라이언스 헬스, 라우팅 테이블.

---

## 1.4 AWS API Gateway — HTTP API
- 계열: 네트워크-API 게이트웨이 (L7, 관리형)
- 서울 리전: 있음 ([PL] AmazonApiGateway ap-northeast-2 · "$1.23/million requests - API Gateway HTTP API (first 300 million)" · 2026-10-01)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| NW.layer | [L7] 종단 프록시(관리형). Regional 엔드포인트만 | — | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html · "Edge-optimized Yes No Regional Yes Yes Private Yes No" · 2026-10-01 |
| NW.idle_timeout | 미확인 | — | 미확인 |
| NW.request_timeout | [L7] 통합 타임아웃 **최대 30초, 상향 불가**(50~30,000 ms) | — | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html · "Maximum integration timeout 30 seconds No" · 2026-10-01 |
| NW.websocket | 없음(WebSocket API는 별도 제품, 1.6). SSE 같은 응답 스트리밍 지원 문구는 미확인 | — | — |
| NW.protocols | [L7] HTTPS. 통합: Lambda, HTTP 프록시, VPC 링크(ALB·NLB·Cloud Map) | 통합 목록 인용 미확인 | — ⚠️근거없음 |
| NW.body_size | [L7] 페이로드 10 MB, 요청 줄 + 헤더 10,240바이트(조정 불가). Lambda 통합이면 실효 6 MB | — | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html · "Total combined size of request line and header values 10240 bytes" / "Payload size 10 MB" · 2026-10-01 |
| NW.draining | 해당 없음(관리형) | — | — |
| NW.health_check | 해당 없음(대상 헬스 체크 없음) | — | — |
| NW.tls | [TLS] 사용자 지정 도메인은 TLS_1_2만. mTLS 지원(S3 트러스트 스토어) | — | https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-custom-domain-tls-version.html · "API Gateway only supports the TLS_1_2 security policy for HTTP or WebSocket APIs." · https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html · "Mutual TLS authentication Yes Yes" · 2026-10-01 |
| NW.client_ip | [L7] `$context.identity.sourceIp`, Lambda v2 페이로드 `requestContext.http.sourceIp`. HTTP 통합으로 XFF가 전달되는지는 미확인(XFF는 매핑할 수 없는 예약 헤더) | — | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-logging-variables.html · "The source IP address of the immediate TCP connection making the request" · https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-parameter-mapping.html · "The following headers are reserved… X-Forwarded-For X-Forwarded-Host X-Forwarded-Proto" · 2026-10-01 |
| NW.routing | [L7] 경로·메서드 라우트. **카나리 배포 없음** | — | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html · "Canary release deployments Yes No" · 2026-10-01 |
| NW.scaling | [L7] 계정·리전 스로틀 10,000 RPS, 버스트 5,000(일부 리전 2,500/1,250) | — | https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html · "10,000 requests per second (RPS)… maximum bucket capacity of 5,000 requests" · 2026-10-01 |
| NW.availability | 리전 서비스. SLA 미확인 | — | — ⚠️근거없음 |
| NW.caching | 없음(REST만 캐시) | — | — ⚠️근거없음 |
| NW.security | WAF 직접 연결은 REST만(CKV2_AWS_29가 REST 대상). JWT·Lambda 권한 부여자 | 권한 부여자 인용 미확인 | — ⚠️근거없음 |
| NW.dns / NW.egress | 해당 없음(10 문서) | — | — |
| NW.private_connectivity | VPC 링크로 사설 ALB·NLB에 연결(인용 미확인) | — | 미확인 ⚠️근거없음 |
| NW.regions | 서울 있음 | — | [PL] |
| NW.cost_floor | **$0 고정** + $1.23/100만 요청(첫 3억), 이후 $1.11 | — | [PL] AmazonApiGateway ap-northeast-2 · "$1.11/million requests - API Gateway HTTP API (more than 300 million)" · 2026-10-01 |

### 비용 구조
고정비 0, 요청당 과금이다. 월 1,300만 요청쯤에서 ALB 고정비($16.43)와 비슷해진다(계산, 추론). ⚠️근거없음

### 교체 계열 정보
- 30초 상한 때문에 A2가 "수 분"이면 ALB나 함수 URL(900초)로 옮긴다.
- 반대로 ALB에서 이쪽으로 오면 10 MB, 30초, 웹소켓 없음을 확인한다.

### 함정
- 30초는 고정이다. REST와 달리 상향 요청이 불가능하다.
- XFF가 예약 헤더다. 앱이 XFF로 IP를 읽던 코드는 HTTP 통합에서 확인이 필요하다.

### 생성 산출물
- Terraform: `aws_apigatewayv2_api`(`protocol_type = "HTTP"`), `aws_apigatewayv2_integration`(`timeout_milliseconds`, HTTP 50~30,000, 기본 30초), `aws_apigatewayv2_route`, `aws_apigatewayv2_stage`(`auto_deploy`, `access_log_settings`, `default_route_settings` 스로틀), `aws_apigatewayv2_domain_name`, `aws_lambda_permission`.
- 반드시 명시: A2용 `timeout_milliseconds`, F5용 `aws_apigatewayv2_route.authorization_type`, D3용 스테이지 스로틀(`throttling_rate_limit`·`throttling_burst_limit`, 인자 원문 미확인). ⚠️근거없음
- Checkov:
  - CKV_AWS_76 "Ensure API Gateway has Access Logging enabled"(apigatewayv2_stage 포함)
  - CKV_AWS_309 "Ensure API GatewayV2 routes specify an authorization type"
  - CKV2_AWS_51 "Ensure AWS API Gateway endpoints uses client certificate authentication"(공개 웹은 사유와 함께 건너뜀)
  - 참고: CKV_AWS_95는 Terraform 체크가 아니다(CloudFormation 전용).
- 배포 후 검증: 29초 넘는 핸들러로 503/504 확인, `aws apigatewayv2 get-stage`.

---

## 1.5 AWS API Gateway — REST API (Regional)
- 계열: 네트워크-API 게이트웨이 (L7)
- 서울 리전: 있음 ([PL] AmazonApiGateway ap-northeast-2 · "$3.50/million requests - first 333 million requests/month" · 2026-10-01)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| NW.layer | [L7] 종단. 엔드포인트 Edge(Terraform 기본 EDGE) / Regional / Private | — | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html · "Edge-optimized Yes No Regional Yes Yes Private Yes No" · 2026-10-01 |
| NW.idle_timeout | [L7] 유휴 연결 310초(조정 불가) | — | https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html · "Idle connection timeout 310 seconds No" · 2026-10-01 |
| NW.request_timeout | [L7] 통합 50 ms~**29초**. Regional·Private는 29초 넘게 올릴 수 있으나 계정 스로틀이 줄 수 있다. Edge는 불가. [충돌] 상한: Terraform 문서는 300,000 ms(BUFFERED)·900,000 ms(STREAM). AWS API 참조는 "50~29,000"(상향 가능) | 응답 스트리밍(STREAM): 최대 15분, 유휴 5분(Regional·Private), Edge 30초 | https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html · "You can raise the integration timeout to greater than 29 seconds, but this might require a reduction in your Region-level throttle quota" · https://docs.aws.amazon.com/apigateway/latest/developerguide/response-transfer-mode.html · "You can stream your response for up to 15 minutes." · https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/api_gateway_integration.html.markdown · "maximum value is 300,000 when `response_transfer_mode` is `BUFFERED`, and 900,000 when… `STREAM`" · https://docs.aws.amazon.com/apigateway/latest/api/API_PutIntegration.html · "Custom timeout between 50 and 29,000 milliseconds" · 2026-10-01 |
| NW.websocket | 없음 | — | — ⚠️근거없음 |
| NW.protocols | [L7] HTTPS. 스트리밍은 HTTP_PROXY·AWS_PROXY 통합만 | — | 위 response-transfer-mode · 2026-10-01 |
| NW.body_size | [L7] 페이로드 10 MB, 헤더 20,480바이트(Private API 8,000) | — | https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html · 2026-10-01 |
| NW.draining / NW.health_check | 해당 없음 | — | — |
| NW.tls | [TLS] 사용자 지정 도메인 TLS_1_0 / TLS_1_2 / 강화 SecurityPolicy_* 선택. mTLS 지원 | — | https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-custom-domain-tls-version.html · 2026-10-01 |
| NW.client_ip | [L7] `$context.identity.sourceIp` | — | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-logging-variables.html · 2026-10-01 |
| NW.routing | [L7] 리소스·메서드. **스테이지 카나리**(트래픽 %) | — | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html · "Canary release deployments Yes No" · 2026-10-01 |
| NW.scaling | 10,000 RPS / 버스트 5,000 | — | https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html · 2026-10-01 |
| NW.availability | 리전. SLA 미확인 | — | — ⚠️근거없음 |
| NW.caching | [L7] 전용 캐시(0.5 GB $0.02/시간 ~), 캐시 켜면 시간당 고정비 | — | [PL] AmazonApiGateway ap-northeast-2 · "API Gateway Dedicated Cache: 0.5GB - Asia Pacific (Seoul)" 0.02 · 2026-10-01 |
| NW.dns / NW.egress | 해당 없음 | — | — |
| NW.private_connectivity | Private API(VPC 엔드포인트), VPC 링크 | 인용 미확인 | — ⚠️근거없음 |
| NW.regions | 서울 있음 | — | [PL] |
| NW.cost_floor | $0 + $3.50/100만(첫 3.33억), $3.19, $2.71, $1.72 단계 | — | [PL] AmazonApiGateway ap-northeast-2 · 2026-10-01 |

### 비용 구조 / 교체 계열 정보 / 함정
- 요청당 HTTP API의 약 2.8배다. 카나리·WAF·캐시·스트리밍이 필요할 때만 고른다.
- 함정: Terraform `endpoint_configuration.types` 기본이 EDGE다. EDGE면 29초를 올릴 수 없고 스트리밍 유휴가 30초다. 서울 사용자 대상이면 REGIONAL을 명시한다.

### 생성 산출물
- Terraform: `aws_api_gateway_rest_api`(`endpoint_configuration { types = ["REGIONAL"] }`), `aws_api_gateway_resource`, `aws_api_gateway_method`, `aws_api_gateway_integration`(`timeout_milliseconds` 기본 29,000, `response_transfer_mode` BUFFERED/STREAM), `aws_api_gateway_deployment`, `aws_api_gateway_stage`(`canary_settings { percent_traffic }`), `aws_api_gateway_method_settings`, `aws_wafv2_web_acl_association`.
- Checkov:
  - CKV_AWS_76
  - CKV_AWS_73 "Ensure API Gateway has X-Ray Tracing enabled"
  - CKV_AWS_120 "Ensure API Gateway caching is enabled"(캐시 불필요하면 건너뜀)
  - CKV_AWS_206 "Ensure API Gateway Domain uses a modern security Policy"
  - CKV_AWS_217 "Ensure Create before destroy for API deployments"
  - CKV_AWS_237 "Ensure Create before destroy for API Gateway"
  - CKV_AWS_59 "Ensure there is no open access to back-end resources through API"
  - CKV2_AWS_4 "Ensure API Gateway stage have logging level defined as appropriate"
  - CKV2_AWS_29 "Ensure public API gateway are protected by WAF"
  - CKV2_AWS_53 "Ensure AWS API gateway request is validated"
  - CKV2_AWS_70 "Ensure API gateway method has authorization or API key set"
- 검증: `aws apigateway get-stage`로 카나리 설정을 확인한다. 30초 이상 핸들러로 504를 확인한다.

---

## 1.6 AWS API Gateway — WebSocket API
- 계열: 네트워크-API 게이트웨이 / 실시간 (L7)
- 서울 리전: 있음 ([PL] AmazonApiGateway ap-northeast-2 · "$1.14/million messages - first 1 billion messages/month" · 2026-10-01)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| NW.layer | [L7] 종단. 연결은 게이트웨이가 들고 있고, 백엔드는 메시지마다 호출된다(연결 관리형) | — | https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-execution-service-websocket-limits-table.html · 2026-10-01 |
| NW.idle_timeout | [L7] **10분**(조정 불가) | — | 같은 페이지 · "Idle Connection Timeout 10 minutes" · 2026-10-01 |
| NW.request_timeout | [L7] 통합 50 ms~29초 | — | 같은 페이지 · 2026-10-01 |
| NW.websocket | [L7] 연결 최대 **2시간**(조정 불가), 새 연결 500/초 | 2시간마다 재연결 코드 필요 | 같은 페이지 · "Connection duration for WebSocket API… 2 hours" · 2026-10-01 |
| NW.protocols | WSS | — | — ⚠️근거없음 |
| NW.body_size | [L7] 프레임 32 KB, 메시지 128 KB | — | 같은 페이지 · "WebSocket frame size 32 KB… Message payload size 128 KB" · 2026-10-01 |
| NW.draining / NW.health_check | 해당 없음 | — | — |
| NW.tls | [TLS] TLS_1_2만(사용자 지정 도메인) | — | https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-custom-domain-tls-version.html · 2026-10-01 |
| NW.client_ip | `$context.identity.sourceIp`(WebSocket 컨텍스트 변수 인용 미확인) | — | 미확인 ⚠️근거없음 |
| NW.routing | 라우트 선택 식(`$connect`, `$disconnect`, `$default`). 가중치 없음 | 인용 미확인 | — ⚠️근거없음 |
| NW.scaling | 스로틀 10,000 RPS(계정 공유) | — | https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html · 2026-10-01 |
| NW.availability / NW.caching / NW.dns / NW.egress / NW.private_connectivity | 미확인 / 해당 없음 | — | — |
| NW.security | 권한 부여자는 `$connect`에서만(인용 미확인) | — | — ⚠️근거없음 |
| NW.regions | 서울 있음 | — | [PL] |
| NW.cost_floor | $0 + 메시지 $1.14/100만(10억 초과 $0.94) + 연결 분 $0.285/100만 | — | [PL] AmazonApiGateway ap-northeast-2 · "$0.285/million connection minutes" · 2026-10-01 |

### 비용 구조 / 교체 계열 정보 / 함정
- 교체 시 코드 변경이 크다. `socket.io`/`ws` 서버 코드가 "메시지마다 함수 호출 + 연결 ID로 `@connections` POST" 모델로 바뀐다(03 문서 실시간 절).
- 함정: 2시간 강제 종료와 10분 유휴. 클라이언트 하트비트는 10분 미만이어야 한다.

### 생성 산출물
- Terraform: `aws_apigatewayv2_api`(`protocol_type = "WEBSOCKET"`, `route_selection_expression`), `aws_apigatewayv2_route`(`$connect` 등), `aws_apigatewayv2_integration`(`timeout_milliseconds` 50~29,000), `aws_apigatewayv2_stage`.
- Checkov: CKV_AWS_76, CKV_AWS_309.
- 검증: `wscat`으로 연결 후 10분 무전송 시 종료되는지 확인한다(도구 이름은 일반 도구, 공식 근거 없음).

---

## 1.7 AWS Lambda Function URL
- 계열: 네트워크-함수 진입점 (L7, 관리형)
- 서울 리전: Lambda는 있음. Function URL의 서울 제공 여부는 미확인(05 문서와 같음)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| NW.layer | [L7] 종단, 공용 인터넷 전용 | — | https://docs.aws.amazon.com/lambda/latest/dg/urls-configuration.html (05 문서 인용 "You can access your function URL through the public Internet only.") · 2026-10-01 |
| NW.idle_timeout | 미확인 | — | — |
| NW.request_timeout | [L7] 함수 타임아웃 최대 900초. URL 고유 타임아웃은 문서에 없다 | — | https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html · "Function timeout 900 seconds (15 minutes)." · 2026-10-01 |
| NW.websocket | 미확인(지원 문구 없음). 응답 스트리밍(RESPONSE_STREAM)은 Node.js 관리형 런타임 | 클라이언트가 끊어도 함수는 계속 과금 | https://docs.aws.amazon.com/lambda/latest/dg/configuration-response-streaming.html (05 문서) · 2026-10-01 |
| NW.protocols | [L7] HTTPS | — | — ⚠️근거없음 |
| NW.body_size | [L7] 동기 요청·응답 각 6 MB, 스트리밍 응답 200 MB, 요청 줄 + 헤더 1 MB | — | https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html · "1 MB for the total combined size of request line and header values" · 2026-10-01 |
| NW.draining / NW.health_check | 해당 없음 | — | — |
| NW.tls | [TLS] AWS 관리. 사용자 지정 도메인은 URL 자체로 불가(CloudFront 경유, 10 문서, 인용 미확인) | — | — ⚠️근거없음 |
| NW.client_ip | [L7] `requestContext.http.sourceIp` | — | https://docs.aws.amazon.com/lambda/latest/dg/urls-invocation.html · `"sourceIp": "123.123.123.123"` · 2026-10-01 |
| NW.routing | 별칭에 URL을 붙이면 별칭 가중치로 2개 버전 분할(05 문서) | — | https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html · "You can point an alias to a maximum of two Lambda function versions." · 2026-10-01 |
| NW.scaling | [L7] URL 고유 한도 없음. 최대 RPS = 예약 동시성 × 10, 넘으면 429 | — | https://docs.aws.amazon.com/lambda/latest/dg/urls-configuration.html · "maximum request rate per second (RPS) is equivalent to 10 times the configured reserved concurrency" · 2026-10-01 |
| NW.availability | 멀티 AZ(05 문서) | — | — |
| NW.caching / NW.dns / NW.egress | 해당 없음 | — | — |
| NW.security | 인증 유형 `NONE` / `AWS_IAM`, CORS | — | https://docs.aws.amazon.com/lambda/latest/api/API_CreateFunctionUrlConfig.html · "Valid Values: NONE \| AWS_IAM" · 2026-10-01 |
| NW.private_connectivity | 없음(공용 전용) | — | 위 urls-configuration |
| NW.regions | 미확인 | — | — |
| NW.cost_floor | URL 자체 추가 요금 없음(별도 단가 행 없음, 05 문서) | — | — |

### 비용 구조 / 교체 계열 정보 / 함정
- 가장 싼 HTTP 진입점이다. 다만 커스텀 도메인·WAF가 필요하면 CloudFront가 앞에 붙는다(10 문서).
- 함정: `invoke_mode` 기본 BUFFERED에서는 SSE가 버퍼링되어 스트림이 아니다.

### 생성 산출물
- Terraform: `aws_lambda_function_url`(`authorization_type` 필수 AWS_IAM/NONE, `invoke_mode` BUFFERED 기본/RESPONSE_STREAM, `cors`), `aws_lambda_alias`.
- 반드시 명시: A3·스트리밍이면 `invoke_mode = "RESPONSE_STREAM"`. F5면 `authorization_type`.
- Checkov: CKV_AWS_258 "Ensure that Lambda function URLs AuthType is not None"(공개 웹은 사유와 함께 건너뜀).
- 검증: `aws lambda get-function-url-config`. 6 MB 초과 업로드가 413인지 확인한다.

---

## 1.8 ECS Express Mode가 만드는 ALB
- 계열: 네트워크-로드밸런서 (L7, 자동 생성)
- 서울 리전: 있음(05 문서 §3.2)

런타임 능력은 1.1과 같다. 아래는 Express가 만드는 **기본값**만 적는다. 출처는 모두 https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-work.html · 2026-10-01이다.

| 능력 키 | 값 | 조건·한도 | 출처 (인용) |
|---|---|---|---|
| NW.layer | [L7] ALB, HTTPS 리스너 443, 호스트 헤더 규칙, ACM 인증서 자동 | — | "Application Load Balancer with HTTPS listener, listener rules, and target groups" / "rule-type: host-header" |
| NW.idle_timeout | **미확인**(Express 문서·모범 사례·고급 설정·문제 해결 페이지에 없음). ALB 기본 60초일 것으로 추정 | — | — |
| NW.request_timeout | 1.1과 같음 | — | — |
| NW.websocket | 1.1과 같음 | — | — |
| NW.protocols | [L7] 대상 HTTP, HTTP1, 포트 80(컨테이너 포트 기본 80) | — | "target-type: ip" |
| NW.body_size | 1.1과 같음 | — | — |
| NW.draining | **미확인**. stopTimeout 30초, healthCheckGracePeriod 300초 | — | "healthCheckGracePeriodSeconds: 300" |
| NW.health_check | [L7] 경로 `/`, 간격 30, 타임아웃 5, 정상 5, 비정상 2 | — | "health-check-path: (default "/")" |
| NW.tls | [TLS] ACM 자동 발급. 정책 이름 미확인 | — | — ⚠️근거없음 |
| NW.client_ip | XFF(1.1) | — | — |
| NW.routing | [L7] 호스트 헤더로 서비스 구분. 카나리 배포 내장 | — | "canary deployment" |
| NW.scaling / NW.availability | 1.1과 같음 | — | — |
| NW.security | [L7] [충돌] desync 완화 "Off"로 표기. ALB API 허용값은 monitor/defensive/strictest(기본 defensive)뿐이다. 액세스 로그 꺼짐 | — | "desync-mitigation-mode: Off - HTTP desync mitigation is disabled" / "access-logs.enabled: false" |
| NW.private_connectivity | 사설 서브넷을 주면 내부 ALB | — | "Creates an Internal load balancer… when private subnets are provided" |
| NW.caching / NW.dns / NW.egress | 해당 없음 | — | — |
| NW.regions | 서울 있음 | — | 05 문서 |
| NW.cost_floor | ALB와 같음($16.43 + LCU). VPC당 최대 25개 서비스가 ALB 하나를 공유 | — | "Up to 25 Express Mode services in the same VPC can share an Application Load Balancer." |

### 함정
- 유휴 60초를 바꾸는 Express 전용 인자가 문서에 없다(미확인). 바꾸려면 생성된 ALB를 직접 수정해야 하고, 그러면 드리프트가 생긴다(추론). ⚠️근거없음
- 액세스 로그 꺼짐 → CKV_AWS_91 실패.

### 생성 산출물
- Terraform: `aws_ecs_express_gateway_service`처럼 Express 전용 리소스 이름이 있는지는 **미확인**(08 문서 P23 참고).
- 생성된 ALB 속성을 바꿀 때: `aws elbv2 modify-load-balancer-attributes`로 `idle_timeout.timeout_seconds`를 설정하고 사람 단계로 기록한다.
- 검증: `aws elbv2 describe-load-balancer-attributes`.

---

## 1.9 AWS Load Balancer Controller — EKS Ingress(ALB)·Service(NLB)
- 계열: 네트워크-쿠버네티스 인그레스 컨트롤러 (ALB·NLB를 만든다)
- 서울 리전: 해당 없음(EKS 서울 있음, 05 문서). 최신 v3.5.0(2026-08-03, GitHub releases API)

런타임 능력은 1.1(ALB)·1.2(NLB)와 같다. 이 절은 **어노테이션 기본값이 AWS 기본값과 다른 점**을 적는다. 출처는 https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/guide/ingress/annotations/ (I), https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/guide/service/annotations/ (S), https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/deploy/pod_readiness_gate/ (R) · 2026-10-01이다.

| 능력 키 | 값 | 조건·한도 | 출처 (인용) |
|---|---|---|---|
| NW.layer | Ingress → ALB [L7], Service(`aws-load-balancer-type: external`) → NLB [L4] | — | S · "reconciles those service resources with this annotation set to either nlb-ip or external" |
| NW.idle_timeout | [L7] `alb.ingress.kubernetes.io/load-balancer-attributes: idle_timeout.timeout_seconds=<초>`(미지정 시 ALB 기본 60). `client_keep_alive.seconds`도 같은 어노테이션 | — | I · "load-balancer-attributes: idle_timeout.timeout_seconds=600" |
| NW.request_timeout | ALB와 같음 | — | — |
| NW.websocket | ALB와 같음 | — | — |
| NW.protocols | `backend-protocol-version`(어노테이션 원문 미확인) | — | — ⚠️근거없음 |
| NW.body_size | ALB와 같음 | — | — |
| NW.draining | [L7] `alb.ingress.kubernetes.io/target-group-attributes: deregistration_delay.timeout_seconds=30`(미지정 시 300). readiness gate: 네임스페이스 라벨 `elbv2.k8s.aws/pod-readiness-gate-inject: enabled`, **ip 대상에서만** | Pod 종료와 대상 해제 순서를 맞춘다 | I · "deregistration_delay.timeout_seconds=30" / R · "only works with target-type: ip" |
| NW.health_check | [L7] **컨트롤러 기본값**: 간격 15, 타임아웃 5, 정상 2, 비정상 2, 경로 `/`, 성공 코드 200(gRPC 12). AWS 기본값(30/5/5/2)과 다르다 | — | I · "healthcheck-interval-seconds integer '15'" |
| NW.tls | `certificate-arn`, `ssl-policy`, `listen-ports`, `ssl-redirect`(08 문서) | — | I |
| NW.client_ip | ALB: XFF. NLB: `aws-load-balancer-proxy-protocol: "*"`(v2), 또는 `aws-load-balancer-target-group-attributes: preserve_client_ip.enabled=true` | — | S · "Set to '*' to enable proxy protocol v2." |
| NW.routing | [L7] `alb.ingress.kubernetes.io/actions.<이름>`으로 가중치 forward(`forwardConfig.targetGroups[].weight`, `targetGroupStickinessConfig`). `group.name`으로 Ingress 여러 개가 ALB 하나 공유(63자) | — | I · "forward-multiple-tg: forward to multiple targetGroups with different weights and stickiness config" |
| NW.scaling / NW.availability | ALB·NLB와 같음 | — | — |
| NW.security | **`scheme` 기본 internal**(ALB·NLB 모두). 인터넷 노출은 `internet-facing` 명시. **`target-type` 기본 instance**(ALB), NLB도 LoadBalancerClass 사용 시 기본 instance | — | I · "alb.ingress.kubernetes.io/scheme internal \| internet-facing internal" / "instance \| ip instance" / S · "If not specified, default is internal." |
| NW.caching / NW.dns / NW.egress / NW.private_connectivity | 해당 없음 | — | — |
| NW.regions | EKS 리전 | — | — ⚠️근거없음 |
| NW.cost_floor | 생성된 ALB/NLB 비용. `group.name`으로 공유하면 줄어든다 | — | — ⚠️근거없음 |

### 함정
- 기본 `scheme: internal` → 외부에서 접속이 안 되는 "배포 성공, 접속 실패"가 난다.
- 기본 `target-type: instance` → readiness gate가 동작하지 않는다. 롤링 중 502가 난다(03 문서).
- EKS Auto Mode는 어노테이션 일부를 무시하고 IngressClassParams를 쓴다(08 문서 P32).

### 생성 산출물
- k8s 매니페스트(`networking.k8s.io/v1` Ingress, `spec.ingressClassName: alb`) + Helm으로 컨트롤러 설치(`helm_release`, 차트 이름 미확인).
- 반드시 명시할 어노테이션:
  - `scheme`, `target-type: ip`, `healthcheck-path`
  - `load-balancer-attributes: idle_timeout.timeout_seconds=…`(A2·A3)
  - `target-group-attributes: deregistration_delay.timeout_seconds=…`(F4)
  - `certificate-arn`, `ssl-policy`, `ssl-redirect: "443"`(F5)
- Checkov: 어노테이션 값을 검사하는 규칙은 확인하지 못했다(미확인). kubeconform + 커스텀 정책(Rego·grep)으로 위 키가 있는지 검사한다.
- 배포 후 검증: `kubectl get ingress`로 주소를 확인한다. `aws elbv2 describe-load-balancer-attributes`로 어노테이션이 반영됐는지 본다. `kubectl get pod -o yaml`로 readiness gate 조건(`target-health.elbv2.k8s.aws/…`)을 확인한다(조건 이름 원문 미확인). ⚠️근거없음

---

## 2. Google Cloud

GCP 출처 URL은 `cloud.google.com`에서 `docs.cloud.google.com`으로 리다이렉트된다. 자주 쓰는 페이지는 다음과 같다.

| 약칭 | URL |
|---|---|
| RD | https://docs.cloud.google.com/load-balancing/docs/https/request-distribution |
| HO | https://docs.cloud.google.com/load-balancing/docs/https |
| BS | https://docs.cloud.google.com/load-balancing/docs/backend-service |
| HC | https://docs.cloud.google.com/load-balancing/docs/health-check-concepts |
| QU | https://docs.cloud.google.com/load-balancing/docs/quotas |
| FE | https://docs.cloud.google.com/load-balancing/docs/features |
| CD | https://docs.cloud.google.com/load-balancing/docs/enabling-connection-draining |
| SSLP | https://docs.cloud.google.com/load-balancing/docs/ssl-policies-concepts |
| PR | https://cloud.google.com/vpc/network-pricing |
| SLA | https://cloud.google.com/compute/sla (load-balancing/sla에서 리다이렉트) |
| TFG | https://raw.githubusercontent.com/hashicorp/terraform-provider-google/main/website/docs/r/<리소스>.html.markdown (provider v8.5.0) |

표 안에서는 위 약칭 대신 **전체 URL**을 적는다. 다만 같은 표 안에서 반복될 때는 "같은 RD"처럼 줄인다.

**GCP 가격 공통:**
- 전달 규칙은 처음 5개 $0.025/시간(월 $18.25), 추가 규칙 $0.01/시간이다.
- 리전 데이터 처리는 수신·송신 각 $0.008/GiB다.
- 이 값은 정적 HTML의 기본 리전(Iowa) 값이다. **서울(asia-northeast3) 단가는 미확인**이다(페이지가 리전별 가격을 JS로 불러온다).
- 출처: https://cloud.google.com/vpc/network-pricing · "First 5 forwarding rules $0.025 / 1 hour" / "Inbound data processed by load balancer $0.008 / 1 gibibyte" · 2026-10-01.

**GCP L7 공통 keepalive 규칙(판정에 가장 중요):**
- GFE·Envoy는 백엔드 keepalive가 600초 고정이다.
- 그래서 앱 서버 keepalive가 **600초보다 커야** 한다. 문서 예시는 620초다.
- 출처: https://docs.cloud.google.com/load-balancing/docs/https/request-distribution · "you must configure your backend software so that its HTTP keepalive (TCP idle) timeout value is greater than 600 seconds." / "fixed at 10 minutes (600 seconds) and cannot be changed" · https://docs.cloud.google.com/load-balancing/docs/https/troubleshooting-ext-https-lbs · "The recommended value is 620 seconds." · 2026-10-01

## 2.1 GCP 전역 외부 Application Load Balancer (EXTERNAL_MANAGED)
- 계열: 네트워크-로드밸런서 (L7, 전역 애니캐스트)
- 서울 리전: 해당 없음(전역). 백엔드는 서울 리전에 둘 수 있다.

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| NW.layer | [L7] 종단 프록시(GFE), 전역 애니캐스트(Premium 티어) | — | https://docs.cloud.google.com/load-balancing/docs/https · "Global Anycast external IP addresses over Premium Tier" · 2026-10-01 |
| NW.idle_timeout | [L7] 클라이언트 HTTP keepalive 기본 **610초**, 5~1,200초 변경 가능(`httpKeepAliveTimeoutSec`). 백엔드 keepalive **600초 고정**(백엔드 버킷 360초). 그 밖의 고정값: 연결 수립 4.5초, 클라이언트 TLS 10초, QUIC 유휴 min(클라이언트, 240초) | 앱 keepalive > 600초 | https://docs.cloud.google.com/load-balancing/docs/https/request-distribution · "The default value for the client HTTP keepalive timeout is 610 seconds." / "you can configure ... between 5 and 1200 seconds." / "fixed at 10 minutes (600 seconds) and cannot be changed" · 2026-10-01 |
| NW.request_timeout | [L7] 백엔드 서비스 타임아웃 기본 **30초**. 설정 범위 1~2,147,483,647초, 실효 최대 86,400초. **요청 첫 바이트부터 응답 마지막 바이트까지**다(유휴가 아님). 서버리스 NEG는 60분 고정(2.9) | 다운로드·스트리밍 응답 전체 시간이 30초에 묶인다 | https://docs.cloud.google.com/load-balancing/docs/backend-service · "The default value is 30 seconds. The full range of timeout values allowed is 1 - 2,147,483,647 seconds." · 같은 RD · "GFEs impose an effective maximum backend service timeout of 86,400 seconds (1 day)." / "maximum amount of time allowed between the load balancer sending the first byte of a request ... returning the last byte" · 2026-10-01 |
| NW.websocket | [L7] **활성 웹소켓은 백엔드 타임아웃을 무시하고 24시간에 종료**. 유휴 웹소켓은 백엔드 타임아웃에 종료 | — | 같은 RD · "automatically closed after 24 hours (86,400 seconds)" · 2026-10-01 |
| NW.protocols | [L7] 클라이언트 HTTP/1.1·HTTP/2·HTTP/3(클라이언트↔LB만). 백엔드 HTTP·HTTPS·HTTP2·H2C. gRPC는 HTTP/2 종단 간 필요. 백엔드 HTTP/2 동시 스트림 100 | — | https://docs.cloud.google.com/load-balancing/docs/https · "HTTP/3 is supported for connections between clients and the load balancer, not connections between the load balancer and its backends." / "If the server advertises a value higher than 100 , the load balancer uses 100" · 2026-10-01 |
| NW.body_size | [L7] 요청 URL + 헤더 60 KiB 이하. 백엔드 응답 헤더 약 128 KB. 커스텀 헤더 요청 16 + 응답 16, 총 8 KB. **본문 한도는 문서에 없다(미확인)** | — | https://docs.cloud.google.com/load-balancing/docs/quotas · "combined size of the request URL and request header must be less than or equal to 60 KiB" / "Maximum backend response header size for external Application Load Balancers About 128 KB" · 2026-10-01 |
| NW.draining | [L7] 연결 드레이닝 0~3,600초, **0이면 꺼짐**. API 기본값은 미확인. Terraform `connection_draining_timeout_sec` 스키마 기본은 300 | — | https://docs.cloud.google.com/load-balancing/docs/enabling-connection-draining · "The timeout duration must be from 0 to 3600 seconds, inclusive." / "A setting of 0 disables connection draining." · 2026-10-01 |
| NW.health_check | [L7] 기본 간격 5초, 타임아웃 5초, 임계 2. **전부 비정상이면 HTTP 503 반환**(fail-open 아님) | — | https://docs.cloud.google.com/load-balancing/docs/health-check-concepts · "Returns an HTTP 503 status code to clients when all backends are unhealthy." · 2026-10-01 |
| NW.tls | [TLS] Google 관리 인증서(Compute Engine 또는 Certificate Manager). SSL 정책이 없으면 COMPATIBLE 프로필, **최소 TLS 1.0**. 최소 1.3은 RESTRICTED 필요. 프런트 mTLS·백엔드 mTLS 지원 | — | https://docs.cloud.google.com/load-balancing/docs/ssl-policies-concepts · "the COMPATIBLE profile selected, and the minimum TLS version set to 1.0" · https://docs.cloud.google.com/load-balancing/docs/features · "Frontend mTLS ... YES" · 2026-10-01 |
| NW.client_ip | [L7] `X-Forwarded-For: [<supplied-value>,]<client-ip>,<load-balancer-ip>` → 클라이언트 IP는 **끝에서 두 번째**. 커스텀 요청 헤더 `{client_ip_address}` 가능 | 앱은 신뢰 홉 2 | https://docs.cloud.google.com/load-balancing/docs/https · "X-Forwarded-For : [<supplied-value>,]<client-ip>,<load-balancer-ip>" / "--custom-request-header=x-forwarded-for:{client_ip_address},{server_ip_address}" · 2026-10-01 |
| NW.routing | [L7] URL 맵 호스트·경로. `weightedBackendServices` 가중치 분할(0~1000), 재시도(최대 25, perTryTimeout 최대 24시간), 이상치 감지, 헤더 변환 | — | https://docs.cloud.google.com/load-balancing/docs/features · "Traffic splitting ... YES (Only global and regional modes)" · 같은 RD · "The maximum number of retries ... is 25." · 2026-10-01 |
| NW.scaling | [L7] 자동(사전 증설 불필요, 문구 미확인). URL 맵 1 MB | — | https://docs.cloud.google.com/load-balancing/docs/quotas · "1 MB for each global external ... URL map" · 2026-10-01 ⚠️근거없음 |
| NW.availability | [L7] 전역 애니캐스트. SLA Premium 99.99% | — | https://cloud.google.com/compute/sla · "Load balancing >= 99.99%" · 2026-10-01 |
| NW.caching | Cloud CDN 연동(10 문서) | — | — |
| NW.security | Cloud Armor 백엔드·엣지 정책 | — | https://docs.cloud.google.com/load-balancing/docs/features · 2026-10-01 |
| NW.dns / NW.egress | 해당 없음(10 문서) | — | — |
| NW.private_connectivity | 백엔드: 인스턴스 그룹, 존 NEG(GKE 컨테이너 네이티브), 서버리스 NEG, PSC NEG | — | — ⚠️근거없음 |
| NW.regions | 전역 | — | — ⚠️근거없음 |
| NW.cost_floor | 전달 규칙 $0.025/시간(**월 $18.25**, Iowa 기준). 전역 데이터 처리 요금 없음. 서울 단가 미확인 | — | https://cloud.google.com/vpc/network-pricing · "There are no global data processing charges." · 2026-10-01 |

### 비용 구조
월 $18.25 + 이그레스(10 문서). 같은 프로젝트의 처음 5개 규칙은 같은 단가다.

### 교체 계열 정보
- 클래식(2.3)에서 이쪽으로 옮기면 웹소켓 24시간, 가중치 분할, H2C, 이상치 감지를 얻는다.
- Terraform `load_balancing_scheme`은 v8.0.0부터 기본값이 `EXTERNAL_MANAGED`다(v7까지는 `EXTERNAL`=클래식). provider 버전에 따라 만들어지는 LB가 달라진다.
- `EXTERNAL_MANAGED` 백엔드는 `EXTERNAL` 전달 규칙에 붙일 수 있지만 반대는 안 된다.

### 함정
- 백엔드 타임아웃 30초가 **응답 전체 시간**이다. A2가 "수십 초"인 리포트 다운로드·스트리밍 응답이 30초에 잘린다.
- 앱 keepalive가 600초보다 짧으면 간헐 502가 난다. uvicorn, Node, gunicorn, Puma, Tomcat 기본값이 **모두** 이 조건을 어긴다(§9 R2).
- 모든 백엔드가 비정상이면 503이다. readiness가 DB 상태에 묶이면 DB 장애가 곧 전체 503이다(AWS ALB는 fail-open).
- SSL 정책이 없으면 TLS 1.0이다.

### 생성 산출물
- Terraform(TFG): `google_compute_global_address`, `google_compute_backend_service`, `google_compute_health_check`, `google_compute_url_map`, `google_compute_target_https_proxy`, `google_compute_managed_ssl_certificate` 또는 Certificate Manager(`certificate_map`), `google_compute_ssl_policy`, `google_compute_global_forwarding_rule`, `google_compute_security_policy`(Cloud Armor).
- 반드시 명시할 속성:
  - 공통: `google_compute_backend_service.load_balancing_scheme = "EXTERNAL_MANAGED"`. provider 기본값이 버전마다 다르므로 명시한다. 전달 규칙도 같다.
  - A2: `google_compute_backend_service.timeout_sec`(기본 30). 응답 전체 시간 + 여유로 둔다.
  - A3: `google_compute_target_https_proxy.http_keep_alive_timeout_sec`(610, 5~1200).
  - F4: `connection_draining_timeout_sec`(Terraform 300 vs 콘솔·API 미확인 → 명시).
  - F1: `google_compute_health_check { check_interval_sec, timeout_sec, healthy_threshold, unhealthy_threshold, http_health_check { request_path } }`.
  - F5: `google_compute_ssl_policy { profile = "MODERN" or "RESTRICTED", min_tls_version = "TLS_1_2" }`(기본 COMPATIBLE·TLS_1_0) + `target_https_proxy.ssl_policy`. `security_policy`.
  - 카나리: `google_compute_url_map … route_action { weighted_backend_services { backend_service, weight } }`(0~1000).
  - 클라이언트 IP: `custom_request_headers = ["X-Client-IP:{client_ip_address}"]`(선택).
- 앱 쪽 짝 변경: keepalive > 600초. 예: uvicorn `--timeout-keep-alive 620`, Node `server.keepAliveTimeout = 620000`, gunicorn `--keep-alive 620`(비 sync 워커).
- Checkov: CKV_GCP_4 "Ensure no HTTPS or SSL proxy load balancers permit SSL policies with weak cipher suites"(`google_compute_ssl_policy`)만 존재. backend_service, target_https_proxy, url_map을 보는 GCP 체크는 없다(129 리소스 체크 + 38 그래프 체크 목록 확인) → `timeout_sec`, `load_balancing_scheme`, `connection_draining_timeout_sec`, ssl_policy 연결은 plan JSON 커스텀 검사로 본다.
- 배포 후 검증:
  - `gcloud compute backend-services describe <이름> --global`로 `timeoutSec`, `connectionDraining.drainingTimeoutSec`, `loadBalancingScheme`를 본다.
  - `gcloud compute target-https-proxies describe <이름>`으로 `httpKeepAliveTimeoutSec`를 본다.
  - 35초 응답 엔드포인트로 504가 없는지 확인한다.
  - 웹소켓을 31초 이상 활성으로 유지해 본다.

---

## 2.2 GCP 리전 외부 Application Load Balancer
- 계열: 네트워크-로드밸런서 (L7, 리전, Envoy 기반)
- 서울 리전: 미확인(리전 목록 페이지를 열지 않음)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| NW.layer | [L7] 종단, 관리형 Envoy, 프록시 전용 서브넷(`REGIONAL_MANAGED_PROXY`) 필요. 네트워크 티어 [충돌]: HO는 "Premium 또는 Standard", PR·서버리스 NEG 문서는 "Standard만" | — | https://docs.cloud.google.com/load-balancing/docs/https/request-distribution · "The regional external Application Load Balancer is a managed service implemented on the Envoy proxy." · https://docs.cloud.google.com/load-balancing/docs/https · "can be configured in either Premium or Standard Tier." · https://cloud.google.com/vpc/network-pricing · "uses only the Standard Network Tier" · 2026-10-01 |
| NW.idle_timeout | [L7] 클라이언트 keepalive [충돌]: RD 표는 610초, RD 본문과 Terraform은 600초. 변경은 **대상 프록시를 다시 만들어야** 가능. Terraform 범위 5~600 [충돌](문서 5~1,200). 백엔드 keepalive 600초 고정 | 앱 keepalive > 600초 | 같은 RD · "sets both the client HTTP keepalive timeout and the backend keepalive timeout to a default value of 600 seconds each" / "Create a new target proxy" · https://raw.githubusercontent.com/hashicorp/terraform-provider-google/main/website/docs/r/compute_region_target_https_proxy.html.markdown · "a default value (600 seconds) will be used" · 2026-10-01 |
| NW.request_timeout | [L7] 백엔드 서비스 타임아웃 30초. **`routeAction.timeout`이 있으면 그것이 우선** | — | 같은 RD · "When routeAction.timeout is supplied, the backend service timeout is ignored" · 2026-10-01 |
| NW.websocket | [L7] 활성 연결은 타임아웃을 무시한다. 유휴 연결은 타임아웃에 종료된다. 최대 지속 시간은 미확인 | — | 같은 RD · 2026-10-01 |
| NW.protocols | [L7] HTTP/1.1·HTTP/2, **HTTP/3 없음**. 백엔드 HTTP·HTTPS·HTTP2·H2C | — | https://docs.cloud.google.com/load-balancing/docs/https · 2026-10-01 |
| NW.body_size | 헤더 한도 미확인. 응답 헤더 약 128 KB | — | https://docs.cloud.google.com/load-balancing/docs/quotas · 2026-10-01 |
| NW.draining | 2.1과 같음(0~3,600, 0=꺼짐) | — | https://docs.cloud.google.com/load-balancing/docs/enabling-connection-draining · 2026-10-01 |
| NW.health_check | 전부 비정상이면 **503** | — | https://docs.cloud.google.com/load-balancing/docs/health-check-concepts · 2026-10-01 |
| NW.tls | [TLS] **Certificate Manager 인증서만**(Compute Engine 관리 인증서 불가). SSL 정책 기본 TLS 1.0 | — | https://docs.cloud.google.com/load-balancing/docs/features · "regional external Application Load Balancers support only Certificate Manager Google-managed certificates." · 2026-10-01 |
| NW.client_ip | 2.1과 같음(XFF, 커스텀 헤더) | — | — |
| NW.routing | 가중치 분할·재시도(리전 기본 재시도 1)·이상치 감지 지원 | — | https://docs.cloud.google.com/load-balancing/docs/features · "YES (Only global and regional modes)" · 2026-10-01 |
| NW.scaling | 프록시 전용 서브넷 크기가 프록시 수를 제한(인용 미확인) | — | — ⚠️근거없음 |
| NW.availability | 리전. Standard 티어 SLA 99.9% | — | https://cloud.google.com/compute/sla · "Load balancing >= 99.9%" · 2026-10-01 |
| NW.caching | 없음(Cloud CDN은 전역만, 인용 미확인) | — | — ⚠️근거없음 |
| NW.security | Cloud Armor 리전 백엔드 정책 | — | 같은 FE · 2026-10-01 |
| NW.dns / NW.egress / NW.private_connectivity | 해당 없음(10 문서) | — | — |
| NW.regions | 미확인 | — | — |
| NW.cost_floor | 전달 규칙 $0.025/시간 + 데이터 처리 수신·송신 $0.008/GiB(Iowa). 프록시 인스턴스 요금이 붙는지 미확인(가격 페이지의 프록시 인스턴스 절은 내부 ALB만 명시) | — | https://cloud.google.com/vpc/network-pricing · 2026-10-01 |

### 함정
- keepalive를 바꾸려면 대상 프록시를 다시 만들어야 한다 → Terraform에서 replace가 일어난다.
- 문서와 Terraform의 keepalive 기본값·범위가 서로 다르다.
- HTTP/3이 없다.

### 생성 산출물
- Terraform: `google_compute_subnetwork`(`purpose = "REGIONAL_MANAGED_PROXY"`, `role = "ACTIVE"`), `google_compute_region_backend_service`(`load_balancing_scheme = "EXTERNAL_MANAGED"`, `timeout_sec`, `connection_draining_timeout_sec`), `google_compute_region_url_map`, `google_compute_region_target_https_proxy`(`http_keep_alive_timeout_sec`), `google_compute_forwarding_rule`(`network_tier`), `google_compute_region_health_check`, Certificate Manager 인증서.
- Checkov: CKV_GCP_4(ssl_policy)만 존재. 나머지는 커스텀 검사.
- 검증: `gcloud compute backend-services describe <이름> --region <리전>`.

---

## 2.3 GCP 클래식 Application Load Balancer (EXTERNAL) — GKE Ingress `gce` 클래스 기본
- 계열: 네트워크-로드밸런서 (L7, GFE)
- 서울 리전: 해당 없음(전역, Premium) / Standard 티어면 리전

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| NW.layer | [L7] 종단(GFE). GKE Ingress(`gce`)가 만드는 LB | — | https://docs.cloud.google.com/kubernetes-engine/docs/concepts/ingress · "Ingress for external Application Load Balancers deploys the classic Application Load Balancer." · 2026-10-01 |
| NW.idle_timeout | [L7] 클라이언트 keepalive 610초, **변경 불가**. 백엔드 keepalive 600초 고정 | 앱 keepalive > 600초 | https://docs.cloud.google.com/load-balancing/docs/https/request-distribution · 표에서 클래식은 "NO" · 2026-10-01 |
| NW.request_timeout | [L7] 백엔드 타임아웃 **30초**(BackendConfig `timeoutSec`로 변경) | — | https://docs.cloud.google.com/kubernetes-engine/docs/how-to/ingress-configuration · "If you do not specify a value, the default value is 30 seconds." · 2026-10-01 |
| NW.websocket | [L7] **유휴든 활성이든 백엔드 타임아웃에 종료**. 기본값이면 30초마다 끊긴다 | 웹소켓이면 `timeoutSec`를 세션 최대 길이로 늘려야 한다 | 같은 RD · "Websocket connections, whether idle or active, automatically close after the backend service times out." · 2026-10-01 |
| NW.protocols | [L7] HTTP/1.1·HTTP/2, HTTP/3은 Premium만. **H2C 없음** | — | https://docs.cloud.google.com/load-balancing/docs/https · "H2C isn't supported for classic Application Load Balancers." · 2026-10-01 |
| NW.body_size | [L7] URL + 헤더 **64 KiB**. 응답 헤더 약 128 KB. 본문 미확인 | — | https://docs.cloud.google.com/load-balancing/docs/quotas · 2026-10-01 |
| NW.draining | [L7] BackendConfig `connectionDraining.drainingTimeoutSec` 기본 **0(꺼짐)**, 0~3,600 | 롤링 중 진행 요청이 끊긴다 | https://docs.cloud.google.com/kubernetes-engine/docs/how-to/ingress-configuration · "The default value is 0, which also disables connection draining." · 2026-10-01 |
| NW.health_check | [L7] 전부 비정상이면 **HTTP 502**. BackendConfig `healthCheck`: 간격 5, 임계 2, 경로 `/`, 포트 80 | — | https://docs.cloud.google.com/load-balancing/docs/health-check-concepts · "Returns an HTTP 502 status code to clients when all backends are unhealthy." · 2026-10-01 |
| NW.tls | [TLS] ManagedCertificate(08 문서: 최대 60분, 와일드카드 불가). FrontendConfig `sslPolicy`, `redirectToHttps`(기본 301). 기본 TLS 1.0 | FrontendConfig는 외부 Ingress에만 | https://docs.cloud.google.com/kubernetes-engine/docs/how-to/ingress-configuration · "FrontendConfig can only be used with External Ingresses." · 2026-10-01 |
| NW.client_ip | [L7] XFF(2.1과 같은 형식). **커스텀 요청 헤더 미지원** | — | https://docs.cloud.google.com/load-balancing/docs/features · "YES (Only global and regional modes)" · 2026-10-01 |
| NW.routing | [L7] 호스트·경로만. **가중치 분할·재시도·이상치 감지 없음** | — | 같은 FE · 2026-10-01 |
| NW.scaling | URL 맵 64 KB | — | https://docs.cloud.google.com/load-balancing/docs/quotas · "64 KB for each classic" · 2026-10-01 |
| NW.availability | Premium 99.99% | — | https://cloud.google.com/compute/sla · 2026-10-01 |
| NW.caching | Cloud CDN(10 문서) | — | — |
| NW.security | Cloud Armor 백엔드·엣지 | — | 같은 FE |
| NW.dns / NW.egress / NW.private_connectivity | 해당 없음 | — | — |
| NW.regions | 전역 | — | — ⚠️근거없음 |
| NW.cost_floor | 전달 규칙 $18.25/월(Iowa 기준) | — | https://cloud.google.com/vpc/network-pricing · 2026-10-01 |

### 함정
- **웹소켓 30초 끊김**(타임아웃 기본값).
- 드레이닝 0.
- 전부 비정상이면 502.
- 가중치 분할이 없다.
- keepalive 610초는 고정이다.
- GKE 문서도 managed 클래스를 권장한다(2.8).

### 생성 산출물
- k8s: `Ingress`(`ingressClassName: gce` 또는 어노테이션), `BackendConfig`(`cloud.google.com/v1`), `FrontendConfig`, `ManagedCertificate`. Service에 `cloud.google.com/backend-config` 어노테이션(키 원문은 08 문서 기준, 이번 미확인).
- 반드시 명시할 필드:
  - A2·A3: `BackendConfig.spec.timeoutSec`.
  - F4: `connectionDraining.drainingTimeoutSec`(기본 0 → 30 등).
  - F1: `healthCheck { type, requestPath, port }`(Pod probe에서 추론하지 않는 경우가 있다).
  - F5: `FrontendConfig.sslPolicy`·`redirectToHttps`.
- Checkov: 해당 규칙 없음(미확인) → kubeconform + 커스텀 검사.
- 검증: `kubectl describe ingress`로 백엔드 상태를 본다. `gcloud compute backend-services list/describe`로 `timeoutSec`를 확인한다. 웹소켓을 31초 유지해 본다.

---

## 2.4 GCP 외부 패스스루 Network Load Balancer
- 계열: 네트워크-로드밸런서 (L4, 통과)
- 서울 리전: 미확인(리전 목록 미열람)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| NW.layer | [L4] **프록시 아님**, 직접 서버 반환(DSR), Maglev 기반. 리전 `EXTERNAL`. 전역 패스스루(`EXTERNAL_PASSTHROUGH`)도 있음 | — | https://docs.cloud.google.com/load-balancing/docs/network/networklb-backend-service · "are not proxies ... This process is known as direct server return (DSR)." · 2026-10-01 |
| NW.idle_timeout | [L4] 연결 추적 **60초 고정**(변경 불가) | 장시간 유휴 TCP는 앱 쪽 keepalive 필요 | https://docs.cloud.google.com/load-balancing/docs/network/ext-netlb-traffic-distribution · "expire 60 seconds after the load balancer processes the last packet ... can't be modified." · 2026-10-01 |
| NW.request_timeout | 백엔드 서비스 타임아웃을 설정해도 **무시됨** | — | https://docs.cloud.google.com/load-balancing/docs/backend-service · "the value is ignored. Backend service timeout has no meaning for these passthrough" · 2026-10-01 |
| NW.websocket | [L4] TCP 통과. 60초 연결 추적 유휴 주의 | — | 위 · 2026-10-01 |
| NW.protocols | [L4] TCP, UDP, L3_DEFAULT(ESP, GRE, ICMP, ICMPv6 추가) | — | https://docs.cloud.google.com/load-balancing/docs/features · 2026-10-01 |
| NW.body_size | 해당 없음 | — | — |
| NW.draining | 0~3,600(공통) | — | https://docs.cloud.google.com/load-balancing/docs/enabling-connection-draining · 2026-10-01 |
| NW.health_check | [L4] **전부 비정상이면 fail-open**(모든 백엔드로). 장애 조치 정책이 트래픽을 버리도록 설정된 경우는 예외 | — | https://docs.cloud.google.com/load-balancing/docs/network/ext-netlb-traffic-distribution · "When all backends are unhealthy, the set of eligible backends consists of all backends." · 2026-10-01 |
| NW.tls | 해당 없음(앱이 종단) | — | — |
| NW.client_ip | [L4] **원본 IP 보존** | — | https://docs.cloud.google.com/load-balancing/docs/network/networklb-backend-service · "The load balancer preserves the source IP addresses of incoming packets." · 2026-10-01 |
| NW.routing | 없음 | — | — ⚠️근거없음 |
| NW.scaling | 미확인 | — | — |
| NW.availability | 리전 | — | — ⚠️근거없음 |
| NW.security | Cloud Armor 네트워크 엣지 보안 정책 | — | https://docs.cloud.google.com/load-balancing/docs/features · 2026-10-01 |
| NW.caching / NW.dns / NW.egress / NW.private_connectivity | 해당 없음 | — | — |
| NW.regions | 미확인 | — | — |
| NW.cost_floor | 전달 규칙 $0.025/시간 + 데이터 처리 $0.008/GiB(Iowa) | — | https://cloud.google.com/vpc/network-pricing · 2026-10-01 |

### 생성 산출물
- k8s Service type LoadBalancer(GKE 기본, 4.3) 또는 Terraform `google_compute_region_backend_service`(`load_balancing_scheme = "EXTERNAL"`, `protocol = "TCP"`) + `google_compute_forwarding_rule` + `google_compute_region_health_check`.
- Checkov: 해당 없음.
- 검증: 앱 로그의 원본 IP, 60초 무전송 TCP 유지 시험.

---

## 2.5 GCP 외부 프록시 Network Load Balancer (전역·리전·클래식)
- 계열: 네트워크-로드밸런서 (L4 프록시, TLS 종단 가능)
- 서울 리전: 미확인

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| NW.layer | [L4] 프록시(연결 종단). 전역·리전 `EXTERNAL_MANAGED`, 클래식 `EXTERNAL`. 리전은 TCP만, 전역·클래식은 SSL [TLS] 또는 TCP | — | https://docs.cloud.google.com/load-balancing/docs/features · "Regional mode: TCP only Global and classic mode: SSL or TCP" · 2026-10-01 |
| NW.idle_timeout | [L4] **백엔드 서비스 타임아웃 = 유휴 타임아웃**, 기본 30초 | 장시간 유휴 TCP·웹소켓은 30초에 끊긴다 | https://docs.cloud.google.com/load-balancing/docs/backend-service · "length of time the load balancer keeps the TCP connection open in the absence of any data transmitted" · 2026-10-01 |
| NW.request_timeout | 해당 없음(위 유휴로 대체) | — | — |
| NW.websocket | [L4] TCP로 통과. 30초 유휴에 종료(추론) | — | — ⚠️근거없음 |
| NW.protocols | [L4] TCP / SSL | — | 같은 FE |
| NW.body_size | 해당 없음 | — | — |
| NW.draining | 0~3,600 | — | 공통 CD |
| NW.health_check | [L4] 전부 비정상이면 **새 연결을 끊는다** | — | https://docs.cloud.google.com/load-balancing/docs/health-check-concepts · "Terminates new client TCP connections when all backends are unhealthy." · 2026-10-01 |
| NW.tls | [TLS] SSL 프록시(전역·클래식). SSL 정책은 대상 SSL 프록시에서만 | — | 같은 FE |
| NW.client_ip | [L4] **기본은 보존 안 함**. PROXY protocol v1(`--proxy-header=PROXY_V1`) | 앱이 PROXY v1을 파싱해야 한다 | https://docs.cloud.google.com/load-balancing/docs/tcp · "By default, the target proxy does not preserve the original client IP address" · https://docs.cloud.google.com/load-balancing/docs/tcp/setting-up-tcp · "enable PROXY protocol version 1" · 2026-10-01 |
| NW.routing | 백엔드 서비스 하나(리전은 TLS 라우트 Preview로 여러 개) | — | https://docs.cloud.google.com/load-balancing/docs/tcp · "TLS routes are only available for regional external proxy Network Load Balancers." · 2026-10-01 |
| NW.scaling / NW.availability | 미확인 / 전역(Premium) 또는 리전 | — | — |
| NW.security | Cloud Armor(전역·클래식만) | — | 같은 FE |
| NW.caching / NW.dns / NW.egress / NW.private_connectivity | 해당 없음 | — | — |
| NW.regions | 미확인 | — | — |
| NW.cost_floor | 전달 규칙 $18.25/월(Iowa) | — | https://cloud.google.com/vpc/network-pricing · 2026-10-01 |

### 생성 산출물
- Terraform: `google_compute_backend_service`(`protocol = "TCP"` 또는 `"SSL"`, `timeout_sec` = 유휴), `google_compute_target_tcp_proxy`/`google_compute_target_ssl_proxy`(`proxy_header = "PROXY_V1"`), `google_compute_global_forwarding_rule`.
- 마지막 두 리소스의 인자 원문은 미확인이다.
- Checkov: CKV_GCP_4(SSL 정책).
- 검증: `timeout_sec`보다 긴 무전송 연결 시험.

---

## 2.6 GCP 내부 LB (내부 Application LB 리전·교차 리전 / 내부 패스스루 NLB)
- 계열: 네트워크-로드밸런서 (L7 / L4, 사설)
- 서울 리전: 미확인

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| NW.layer | [L7] 내부 ALB `INTERNAL_MANAGED`(Envoy, 프록시 전용 서브넷), 리전·교차 리전. [L4] 내부 패스스루 NLB `INTERNAL`(선택적 전역 접근) | — | https://docs.cloud.google.com/load-balancing/docs/l7-internal · https://docs.cloud.google.com/load-balancing/docs/backend-service · 2026-10-01 |
| NW.idle_timeout | [L7] 클라이언트 keepalive 610초(5~1,200), 백엔드 600초 고정. [충돌] Terraform은 교차 리전 내부 기본 600, 최대 600. [L4] 내부 패스스루 NLB 기본 유휴 600초(변경 가능) | — | https://docs.cloud.google.com/load-balancing/docs/l7-internal · "The default client HTTP keepalive timeout value is 610 seconds. You can configure the timeout with a value between 5 and 1200 seconds." · https://docs.cloud.google.com/load-balancing/docs/internal/int-netlb-traffic-distribution · "the load balancer uses a default idle timeout of 600 seconds" · 2026-10-01 |
| NW.request_timeout | [L7] 백엔드 30초(서버리스 NEG 60분). [L4] 무시 | — | 같은 l7-internal · 2026-10-01 |
| NW.websocket | [L7] 활성 연결은 타임아웃을 무시하고, 유휴 연결은 타임아웃에 종료된다 | — | 같은 l7-internal · "active websocket connections don't follow the backend service timeout. Idle websocket connections are closed after the backend service timeout." · 2026-10-01 |
| NW.protocols | [L7] HTTP/1.1·2, gRPC. [L4] TCP·UDP·L3_DEFAULT | — | — ⚠️근거없음 |
| NW.body_size | [L7] 요청·응답 헤더 각 60 KB | — | https://docs.cloud.google.com/load-balancing/docs/quotas · 2026-10-01 |
| NW.draining | 0~3,600 | — | 공통 CD |
| NW.health_check | [L7] 전부 비정상이면 503. [L4] fail-open | — | https://docs.cloud.google.com/load-balancing/docs/health-check-concepts · https://docs.cloud.google.com/load-balancing/docs/internal/int-netlb-traffic-distribution · "When all backends are unhealthy, the set of eligible backends consists of all backends." · 2026-10-01 |
| NW.tls | [TLS] Certificate Manager(`certificate_manager_certificates`는 INTERNAL_MANAGED 전용) | — | TFG compute_target_https_proxy · 2026-10-01 |
| NW.client_ip | [L7] XFF에 IP 2개를 덧붙인다. [L4] 원본 보존 | — | 같은 l7-internal · "The load balancer appends two IP addresses to the X-Forwarded-For header" · 2026-10-01 |
| NW.routing | [L7] 가중치 분할 지원 | — | 같은 FE |
| NW.scaling | 프록시 인스턴스 최소 3개 | — | https://cloud.google.com/vpc/network-pricing · "each load balancer is allocated at least three proxy instances" · 2026-10-01 |
| NW.availability | 리전 / 교차 리전(전역 접근 기본 켜짐) | — | https://docs.cloud.google.com/load-balancing/docs/features · "In cross-region mode, global access is enabled by default." · 2026-10-01 |
| NW.private_connectivity | VPC 안에서만. PSC 서비스 게시의 앞단(10 문서) | — | — |
| NW.caching / NW.security / NW.dns / NW.egress | 해당 없음 / Cloud Armor 내부 정책 미확인 | — | — |
| NW.regions | 미확인 | — | — |
| NW.cost_floor | [L7] 내부 ALB 프록시 인스턴스 $0.025/시간 × 최소 3 = **$0.075/시간(월 $54.75)** + $0.008/GiB (us-central1) | — | https://cloud.google.com/vpc/network-pricing · "Per proxy instance* $0.025 / 1 hour" · 2026-10-01 |

### 함정
- 내부 ALB는 최소 프록시 3개라 외부 ALB보다 고정비가 크다.
- 서비스 간 내부 호출에도 keepalive > 600초 규칙이 같이 적용된다.

### 생성 산출물
- Terraform: `google_compute_subnetwork`(`purpose = "REGIONAL_MANAGED_PROXY"`), `google_compute_region_backend_service`(`load_balancing_scheme = "INTERNAL_MANAGED"`), `google_compute_region_url_map`, `google_compute_region_target_http(s)_proxy`, `google_compute_forwarding_rule`(`load_balancing_scheme = "INTERNAL_MANAGED"`). GKE에서는 Ingress `gce-internal` 또는 Gateway `gke-l7-rilb`.
- Checkov: 해당 없음.
- 검증: VPC 내부 VM에서 curl.

---

## 2.7 Cloud Run 기본 엔드포인트(`*.run.app`)와 도메인 매핑
- 계열: 네트워크-플랫폼 내장 진입점 (L7)
- 서울 리전: Cloud Run 있음(05 문서). **도메인 매핑은 asia-northeast3 미지원**

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| NW.layer | [L7] 종단(Google 프런트엔드, 상세 미확인) | — | — ⚠️근거없음 |
| NW.idle_timeout | 미확인 | — | — |
| NW.request_timeout | [L7] 기본 **300초**, 최대 3,600초 | — | https://docs.cloud.google.com/run/docs/configuring/request-timeout · "set by default to 5 minutes (300 seconds) and can be extended up to 60 minutes (3600 seconds)." · 2026-10-01 |
| NW.websocket | [L7] 지원, **요청 타임아웃에 묶인다**(최대 60분) | 재연결 필수 | https://docs.cloud.google.com/run/docs/triggering/websockets · "subject to request timeouts (currently up to 60 minutes and defaults to 5 minutes)" · 2026-10-01 |
| NW.protocols | [L7] 클라이언트 HTTP/2 요청을 **HTTP/1로 다운그레이드**(gRPC 제외). 종단 간 HTTP/2는 컨테이너가 h2c를 말해야 한다 | — | https://docs.cloud.google.com/run/docs/configuring/http2 · "Cloud Run downgrades those requests from HTTP/2 to HTTP/1 with the exception of native gRPC traffic" · 2026-10-01 |
| NW.body_size | [L7] HTTP/1 요청 **32 MiB**, HTTP/2 서버면 무제한. 응답 32 MiB(chunked·스트리밍이면 적용 안 됨). HTTP/2 연결당 스트림 100. 헤더 크기 미확인 | — | https://docs.cloud.google.com/run/quotas · "Maximum HTTP/1 request size 32 MiB ... No limit if using HTTP/2 server." / "Limit applies if not using Transfer-Encoding: chunked or streaming." · 2026-10-01 |
| NW.draining | SIGTERM 10초(05 문서) | — | — |
| NW.health_check | 시작·생존 프로브(05 문서). 엔드포인트 수준 fail 동작 미확인 | — | — |
| NW.tls | [TLS] `*.run.app` 관리. 도메인 매핑 인증서는 보통 약 15분, 최대 24시간. **TLS 1.0·1.1 비활성화 불가**, 와일드카드·자체 인증서 불가 | — | https://docs.cloud.google.com/run/docs/mapping-custom-domains · "usually takes about 15 minutes but can take up to 24 hours." · 2026-10-01 |
| NW.client_ip | XFF 제공 여부 **미확인**(문서에 X-Forwarded-Proto만 언급) | — | https://docs.cloud.google.com/run/docs/triggering/https-request · 2026-10-01 |
| NW.routing | [L7] 리비전별 % 분할(합 100), 태그 URL로 테스트·점진 이전·롤백 | — | https://docs.cloud.google.com/run/docs/rollouts-rollbacks-traffic-migration · "Note that the percentages must add up to 100." / "Use tags for testing, traffic migration and rollbacks" · 2026-10-01 |
| NW.scaling | 인스턴스당 동시 요청 최대 1,000(05 문서) | — | https://docs.cloud.google.com/run/quotas · 2026-10-01 |
| NW.availability | 리전(05 문서) | — | — |
| NW.caching / NW.security | 없음 / Cloud Armor는 외부 LB를 앞에 둬야 함(10 문서) | — | — |
| NW.dns | 도메인 매핑: **Preview, 운영 비권장**. 지원 리전 asia-east1, asia-northeast1, asia-southeast1, europe-north1, europe-west1, europe-west4, us-central1, us-east1, us-east4, us-west1. 서울 없음. 64자 제한, `/`만 매핑 | 서울은 전역 외부 ALB + 서버리스 NEG로 도메인을 붙인다 | https://docs.cloud.google.com/run/docs/mapping-custom-domains · "Cloud Run domain mappings are in the preview launch stage ... not recommended for production services." / "Domain mapping is available in the following regions:" · 2026-10-01 |
| NW.egress / NW.private_connectivity | 05 문서 | — | — |
| NW.regions | 서울 있음, 도메인 매핑은 없음 | — | 위 |
| NW.cost_floor | $0(엔드포인트 자체 요금 없음, 05 문서) | — | — |

### 함정
- 서울에서 커스텀 도메인 = 외부 ALB 고정비(월 $18.25~)가 추가된다.
- 도메인 매핑은 TLS 1.0을 끌 수 없다(F5 요건 충돌).
- 웹소켓은 최대 60분이다.

### 생성 산출물
- 도메인 매핑을 쓰는 경우(지원 리전): `google_cloud_run_domain_mapping`(`spec.route_name`, `spec.certificate_mode` 기본 AUTOMATIC, `spec.force_override`).
- 서울: 2.1 + 2.9 조합.
- 반드시 명시할 속성은 `google_cloud_run_v2_service.template.timeout`(A2·A3)과 `traffic` 블록(카나리)이다. 정확한 블록 이름은 08 문서 P19를 따른다.
- Checkov: Cloud Run v2 대상 체크 없음(08 문서).
- 검증: `gcloud run services describe <이름> --region <리전>`으로 timeout·traffic을 본다. 301초 요청으로 504를 확인한다.

---

## 2.8 GKE Gateway API (GatewayClass별)
- 계열: 네트워크-쿠버네티스 Gateway (L7, Google 관리형 LB 생성)
- 서울 리전: GKE 서울 있음(05 문서)

| GatewayClass | 만드는 LB | HTTPRoute 가중치 분할 | 출처 |
|---|---|---|---|
| `gke-l7-global-external-managed` (-mc) | 전역 외부 ALB (2.1) | 있음 | https://docs.cloud.google.com/kubernetes-engine/docs/how-to/gatewayclass-capabilities · 2026-10-01 |
| `gke-l7-regional-external-managed` (-mc) | 리전 외부 ALB (2.2) | 있음 | 같음 |
| `gke-l7-rilb` (-mc) | 리전 내부 ALB (2.6) | 있음 | 같음 |
| `gke-l7-cross-regional-internal-managed-mc` | 교차 리전 내부 ALB | 있음 | 같음 |
| `gke-l7-gxlb` (-mc) | **클래식 ALB (2.3)** | **없음**(표의 traffic splitting·backendRef.weight 칸이 비어 있음) | 같음 · https://docs.cloud.google.com/kubernetes-engine/docs/concepts/gateway-api · "Global external Application Load Balancer(s) built on the classic Application Load Balancer" · 2026-10-01 |

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| NW.layer | [L7] 위 표의 LB | — | 위 |
| NW.idle_timeout | 해당 LB의 값(전역 managed 610/600초) | — | 2.1 |
| NW.request_timeout | [L7] `GCPBackendPolicy.spec.default.timeoutSec` 기본 **30초**. HTTPRoute `timeouts` 필드 지원 여부는 미확인 | — | https://docs.cloud.google.com/kubernetes-engine/docs/how-to/configure-gateway-resources · "The timeoutSec field defaults to 30 seconds." · 2026-10-01 |
| NW.websocket | 클래스에 따름: global-external-managed는 활성 24시간, gxlb는 30초 | — | 2.1, 2.3 |
| NW.protocols | 해당 LB | — | — |
| NW.body_size | 해당 LB | — | — |
| NW.draining | [L7] `GCPBackendPolicy.spec.default.connectionDraining.drainingTimeoutSec` 0~3,600, **기본 0(꺼짐)** | — | https://docs.cloud.google.com/kubernetes-engine/docs/how-to/configure-gateway-resources · "The default value is 0, which also disables connection draining." · 2026-10-01 |
| NW.health_check | [L7] `HealthCheckPolicy`. 정책이 없으면 간격 15초, 정책이 있는데 생략하면 5초. 임계 2. **Pod probe에서 추론하지 않는다** | readiness 경로를 따로 지정해야 한다 | 같은 configure-gateway-resources · "default is 15 seconds if no HealthCheckPolicy is specified, and is 5 seconds when a HealthCheckPolicy is specified" · 2026-10-01 |
| NW.tls | `GCPGatewayPolicy.sslPolicy`, Certificate Manager | — | 같은 페이지 |
| NW.client_ip | XFF(2.1) | — | — |
| NW.routing | [L7] HTTPRoute `backendRefs.weight`(gxlb 제외), 헤더 매칭 | Gateway API 스펙: weight 기본 1, 0~1,000,000, 비율 | https://raw.githubusercontent.com/kubernetes-sigs/gateway-api/main/apis/v1/shared_types.go · "Weight is not a percentage… If unspecified, weight defaults to 1." · 2026-10-01 |
| NW.scaling / NW.availability | 해당 LB | — | — |
| NW.security | `GCPBackendPolicy.securityPolicy`(Cloud Armor), `iap` | — | 같은 페이지 |
| NW.caching / NW.dns / NW.egress / NW.private_connectivity | 해당 없음 | — | — |
| NW.regions | GKE 서울 있음 | — | — ⚠️근거없음 |
| NW.cost_floor | 해당 LB 비용 | — | — |

### 함정
- 드레이닝 기본 0.
- `HealthCheckPolicy`가 없으면 `/`를 15초 간격으로 친다.
- gxlb를 고르면 클래식이 되어 웹소켓 30초 문제와 분할 불가가 돌아온다.

### 생성 산출물
- k8s: `Gateway`(`gatewayClassName: gke-l7-global-external-managed`), `HTTPRoute`(`backendRefs[].weight`), `GCPBackendPolicy`(`spec.default.timeoutSec`, `connectionDraining.drainingTimeoutSec`, `securityPolicy`, `logging`), `HealthCheckPolicy`(`requestPath`), `GCPGatewayPolicy`(`sslPolicy`).
- 반드시 명시: A2·A3 `timeoutSec`, F4 `drainingTimeoutSec`, F1 `HealthCheckPolicy`, F5 `sslPolicy`.
- Checkov: 해당 없음(미확인) → kubeconform(CRD 카탈로그) + 커스텀 검사.
- 검증: `kubectl get gateway`로 `PROGRAMMED` 조건을 본다. `gcloud compute backend-services describe`로 `timeoutSec`·드레이닝을 확인한다.

---

## 2.9 GCP 서버리스 NEG (Cloud Run을 LB 백엔드로)
- 계열: 네트워크-LB 백엔드 어댑터
- 서울 리전: Cloud Run 서울 있음

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| NW.layer | [L7] ALB 전용(전역, 클래식, 리전 외부, 리전·교차 리전 내부). **프록시·패스스루 NLB 불가** | — | https://docs.cloud.google.com/load-balancing/docs/negs/serverless-neg-concepts · "Serverless NEGs are not supported by proxy Network Load Balancers and passthrough Network Load Balancers." · 2026-10-01 |
| NW.idle_timeout | 앞단 ALB의 값 | — | — |
| NW.request_timeout | [L7] **60분 고정, 변경 불가**. `timeout_sec`를 설정하면 오류. 실제 상한은 Cloud Run 요청 타임아웃(300초 기본) | 둘 중 작은 값 | 같은 serverless-neg-concepts · "the default timeout is 60 minutes. This timeout is not configurable." / "Timeout sec is not supported for a backend service with Serverless network endpoint groups" · 2026-10-01 |
| NW.websocket | ALB 규칙 + Cloud Run 요청 타임아웃 | — | — ⚠️근거없음 |
| NW.protocols | 백엔드 프로토콜 설정은 무시됨 | — | 같은 페이지 |
| NW.body_size | Cloud Run 32 MiB(HTTP/1) | — | 2.7 |
| NW.draining | 해당 없음 | — | — |
| NW.health_check | **지원 안 함** | 비정상 리비전을 LB가 빼지 못한다 | 같은 페이지 · "Health checks are not supported for serverless backends." · 2026-10-01 |
| NW.tls | 앞단 ALB | — | — |
| NW.client_ip | 앞단 ALB의 XFF | — | — |
| NW.routing | URL 맵. 이상치 감지는 전역 외부·교차 리전 내부 ALB만(클래식 불가). 분산 모드·세션 어피니티 없음 | — | 같은 페이지 · "only available for a cross-region internal Application Load Balancer, global external Application Load Balancer, and not for a classic" · 2026-10-01 |
| NW.scaling | 리전 LB 경유 시 프로젝트당 5,000 QPS, 리전 백엔드 서비스당 NEG 1개 | — | 같은 페이지 · 2026-10-01 |
| NW.availability / NW.caching / NW.security / NW.dns / NW.egress / NW.private_connectivity | 앞단 ALB | — | — |
| NW.regions | Cloud Run 리전 | — | — ⚠️근거없음 |
| NW.cost_floor | 일반 LB 요금. 서버리스 송신 데이터는 과금하지 않음 | — | https://cloud.google.com/vpc/network-pricing · "you will not be charged for serverless outbound data transfer" · 2026-10-01 |

### 생성 산출물
- Terraform: `google_compute_region_network_endpoint_group`(`network_endpoint_type = "SERVERLESS"` 기본, `cloud_run { service }`), `google_compute_backend_service`(**`timeout_sec` 설정 금지**, `load_balancing_scheme = "EXTERNAL_MANAGED"`), 그리고 2.1의 나머지.
- 검사: plan JSON에서 서버리스 NEG 백엔드에 `timeout_sec`가 있으면 오류다(커스텀).
- 검증: `gcloud compute network-endpoint-groups describe`.

---

## 3. Azure

## 3.1 Azure Container Apps 내장 인그레스 (요약)
- 계열: 네트워크-플랫폼 내장 인그레스 (L7, Envoy 기반은 미확인)
- 서울 리전: Korea Central 있음(05 문서 §4.1)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| NW.layer | [L7] 종단(HTTP). 외부 TCP 인그레스 [L4]는 사용자 VNet 필요 | — | https://learn.microsoft.com/en-us/azure/container-apps/ingress-overview · "HTTPS endpoints that always use TLS 1.2 or 1.3, terminated at the ingress point" · 2026-10-01 |
| NW.idle_timeout | [L7] 기본 인그레스 값 미확인. **프리미엄 인그레스**는 유휴 요청 타임아웃 4~30분(기본 4분). 프리미엄은 Consumption이 아닌 워크로드 프로필 필요 | — | https://learn.microsoft.com/en-us/azure/container-apps/ingress-environment-configuration · "Idle request timeouts in minutes." · 2026-10-01 |
| NW.request_timeout | [L7] **240초** | — | https://learn.microsoft.com/en-us/azure/container-apps/ingress-overview · "Request time out is 240 seconds" · 2026-10-01 |
| NW.websocket | [L7] 지원. 240초가 웹소켓에 적용되는지 미확인 | — | 같은 ingress-overview · "Support for WebSocket and gRPC" · 2026-10-01 |
| NW.protocols | [L7] HTTP/1.1, HTTP/2, WebSocket, gRPC. Terraform `transport` auto/http/http2/tcp | — | 같은 페이지 |
| NW.body_size | 미확인. 프리미엄: 요청 헤더 개수 기본 100 | — | 같은 ingress-environment-configuration · 2026-10-01 |
| NW.draining | [L7] 프리미엄 종료 유예 0~3,600, 기본 500. [충돌] 표는 초, CLI·포털 설명은 "분"이다. 컨테이너 SIGTERM 30초(05 문서) | — | 같은 페이지 · "The amount of time (in seconds) for the container app to finish processing requests" vs "Enter the termination grace period in minutes." · 2026-10-01 |
| NW.health_check | 프로브(05 문서). 인그레스 fail 동작 미확인 | — | — |
| NW.tls | [TLS] TLS 1.2·1.3만. 클라이언트 인증서 모드 require/accept/ignore | — | 같은 ingress-overview |
| NW.client_ip | [L7] XFF **덧붙임**. 가장 오른쪽 IP만 신뢰할 수 있다. X-Forwarded-Proto는 덮어씀 | 앱 신뢰 홉 1 | 같은 ingress-overview · "If specified in initial request, it is appended to. Only the rightmost IP is provided by Azure Container Apps." · 2026-10-01 |
| NW.routing | [L7] 리비전 가중치(합 100%, 다중 리비전 모드), 레이블. 세션 어피니티는 단일 리비전 + HTTP에서만 | — | https://learn.microsoft.com/en-us/azure/container-apps/traffic-splitting · "The combined weight of all traffic split rules must equal 100%." · https://learn.microsoft.com/en-us/azure/container-apps/sticky-sessions · 2026-10-01 |
| NW.scaling | 프리미엄: 인그레스 프록시 최대 10개(기본) | — | 같은 ingress-environment-configuration |
| NW.availability | 존 중복은 환경 생성 시(05 문서) | — | — |
| NW.security | IP 제한 Allow 또는 Deny(혼합 불가) | — | https://learn.microsoft.com/en-us/azure/container-apps/ip-restrictions · "You can't combine allow rules and deny rules." · 2026-10-01 |
| NW.caching / NW.dns / NW.egress / NW.private_connectivity | 해당 없음 / 05 문서 | — | — |
| NW.regions | Korea Central | — | 05 문서 |
| NW.cost_floor | 인그레스 별도 요금 없음($0). 프리미엄 인그레스는 워크로드 프로필 노드 비용 | — | 05 문서 |

### 생성 산출물
- Terraform `azurerm_container_app`의 `ingress` 블록(https://raw.githubusercontent.com/hashicorp/terraform-provider-azurerm/main/website/docs/r/container_app.html.markdown · 2026-10-01):
  - `external_enabled`(기본 false)
  - `target_port`(필수)
  - `transport`(기본 auto)
  - `allow_insecure_connections`
  - `client_certificate_mode`
  - `ip_security_restriction { action, ip_address_range }`
  - `traffic_weight { percentage, latest_revision, revision_suffix, label }`. 문서: "The cumulative values for `weight` must equal 100 exactly and explicitly."
  - 템플릿 수준 `termination_grace_period_seconds`, `revision_mode`.
- Checkov: `azurerm_container_app*` 대상 체크 없음(08 문서).
- 검증: `az containerapp ingress show`(명령 원문 미확인). 241초 요청으로 타임아웃을 확인한다. ⚠️근거없음

---

## 4. 쿠버네티스

## 4.1 ingress-nginx (kubernetes/ingress-nginx) — **은퇴, 저장소 아카이브**
- 계열: 네트워크-쿠버네티스 인그레스 컨트롤러 (L7, nginx)
- 서울 리전: 해당 없음
- **상태:** 저장소 `archived: true`. 마지막 릴리스는 controller-v1.15.1(2026-03-19)이다. 2026년 3월 이후 릴리스·버그 수정·보안 패치가 없다.
- 출처:
  - https://kubernetes.io/blog/2025/11/11/ingress-nginx-retirement/ · "Best-effort maintenance will continue until March 2026. Afterward, there will be no further releases, no bugfixes"
  - GitHub API `repos/kubernetes/ingress-nginx` · `"archived": true`
  - README · "If you are not already using ingress-nginx, you should not be deploying it… identify a Gateway API implementation"
  - 모두 확인일 2026-10-01.
- 블로그는 후속 제품을 지명하지 않는다("Consider migrating to Gateway API"). NGINX Gateway Fabric이 공식 후속이라는 문구는 미확인이다.

**판정 규칙:** 새로 생성하지 않는다. 기존 사용은 "교체 필요(보안 패치 없음)"로 표시한다. 대상은 4.2(Gateway API 구현), 클라우드 관리형(1.9, 2.3, 2.8), Traefik의 ingress-nginx 호환 provider(5.4, 부적격 출처로 삭제됨)다.

값은 ConfigMap 문서(https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/docs/user-guide/nginx-configuration/configmap.md = CM)와 소스(`internal/ingress/controller/config/config.go` = SRC), 어노테이션 문서(`.../annotations.md` = ANN)에서 확인했다(2026-10-01).

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| NW.layer | [L7] 종단 프록시. 앞에 클라우드 L4 LB(Service LoadBalancer, 4.3) | — | — |
| NW.idle_timeout | [L7] 클라이언트 `keep-alive` **75초**, `keep-alive-requests` 1,000. 업스트림 `upstream-keepalive-timeout` **60초**, `upstream-keepalive-connections` 320, `upstream-keepalive-requests` 10,000, `upstream-keepalive-time` 1h | 앱 keepalive > 60초 | CM / SRC · `KeepAlive: 75` · 2026-10-01 |
| NW.request_timeout | [L7] `proxy-read-timeout` 60초, `proxy-send-timeout` 60초(둘 다 **연속 읽기·쓰기 사이 간격**), `proxy-connect-timeout` **5초**. 어노테이션 `nginx.ingress.kubernetes.io/proxy-read-timeout` 등(단위 없는 초) | — | CM / SRC · `ProxyConnectTimeout: 5,` / ANN · "All timeout values are unitless and in seconds" · 2026-10-01 |
| NW.websocket | [L7] 별도 설정 없이 지원. 끊김을 막으려면 read/send 타임아웃을 늘린다(문서 권장 3,600 이상) | 60초 무전송에 끊긴다 | https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/docs/user-guide/miscellaneous.md · "The only requirement to avoid the close of connections is the increase of the values of `proxy-read-timeout` and `proxy-send-timeout`." · 2026-10-01 |
| NW.protocols | [L7] HTTP/1.1·HTTP/2, gRPC(어노테이션) | 인용 미확인 | — ⚠️근거없음 |
| NW.body_size | [L7] `proxy-body-size` **1m**(넘으면 413). `client-header-buffer-size` 1k, `large-client-header-buffers` 4 8k. 헤더·본문 타임아웃 60초 | 업로드 앱은 반드시 올린다 | CM · 2026-10-01 |
| NW.draining | [L7] `worker-shutdown-timeout` 240초 | — | CM / SRC · 2026-10-01 |
| NW.health_check | Pod readiness를 엔드포인트로 따른다(k8s). 전부 비정상이면 503(nginx 기본, 인용 미확인) | — | — ⚠️근거없음 |
| NW.tls | [TLS] Secret 기반, cert-manager 연동(인용 미확인) | — | — ⚠️근거없음 |
| NW.client_ip | [L7] `use-forwarded-headers` **false**: 들어온 X-Forwarded-*를 무시하고 직접 본 값으로 채운다. `compute-full-forwarded-for` false, `use-proxy-protocol` false, `proxy-real-ip-cidr` 0.0.0.0/0. 앞단 L4 LB가 원본 IP를 가리면 Service `externalTrafficPolicy: Local` 필요 | — | CM · "If false, NGINX ignores incoming X-Forwarded-* headers, filling them with the request information it sees." · https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/docs/deploy/baremetal.md · "set the value of the `externalTrafficPolicy`… to `Local`" · 2026-10-01 |
| NW.routing | [L7] 호스트·경로. 카나리: `nginx.ingress.kubernetes.io/canary: "true"` + `canary-weight`(0~`canary-weight-total`, 기본 100). 우선순위 header → cookie → weight | — | ANN · "canary-by-header -> canary-by-cookie -> canary-weight" · 2026-10-01 |
| NW.scaling | 컨트롤러 레플리카 수(HPA) | — | — ⚠️근거없음 |
| NW.availability | 레플리카 분산 | — | — ⚠️근거없음 |
| NW.security | 보안 패치 없음(은퇴) | **판정 결정적** | 위 블로그 |
| NW.caching / NW.dns / NW.egress / NW.private_connectivity | 해당 없음 | — | — |
| NW.regions | 해당 없음 | — | — |
| NW.cost_floor | 컨트롤러 Pod + 앞단 L4 LB(1.2/2.4) | — | — |

### 함정
- 본문 1m: 업로드 413.
- 웹소켓·SSE 60초 무전송 끊김.
- 업스트림 keepalive 60초 > 앱 keepalive 5초 → 간헐 502(§9 R3).
- 은퇴 → 보안 패치 없음.

### 생성 산출물
- **생성하지 않는다.** 기존 매니페스트를 읽어 어노테이션 값을 4.2(HTTPRoute + 정책)나 5.4(Traefik, 부적격 출처로 삭제됨)로 옮긴다.
- 마이그레이션 산출물에서 대응 키:
  - `proxy-read-timeout` → `HTTPRoute.timeouts.request`/`backendRequest`
  - `canary-weight` → `backendRefs.weight`
  - `proxy-body-size` → 구현별 정책. Envoy Gateway에서의 키 원문은 미확인.
- 검증: 기존 Ingress 목록 `kubectl get ingress -A -o jsonpath='{..ingressClassName}'`에서 nginx를 찾는다.

---

## 4.2 Gateway API 구현 대표 — Envoy Gateway (v1.9.2, Gateway API v1.6.2)
- 계열: 네트워크-쿠버네티스 Gateway (L7, Envoy)
- 서울 리전: 해당 없음
- Gateway API 등재 구현: Cilium, Envoy Gateway, Istio, NGINX Gateway Fabric(v2.7.2, Active), Traefik 등(https://gateway-api.sigs.k8s.io/implementations/ · 2026-10-01).

출처 약어: EG = `https://raw.githubusercontent.com/envoyproxy/gateway/main/api/v1alpha1/<파일>`, GA = `https://raw.githubusercontent.com/kubernetes-sigs/gateway-api/main/apis/v1/httproute_types.go`.

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| NW.layer | [L7] 종단 프록시(Envoy). 앞에 Service LoadBalancer [L4] | — | — ⚠️근거없음 |
| NW.idle_timeout | [L7] ClientTrafficPolicy `timeouts.http.idleTimeout` 기본 **1시간**, `streamIdleTimeout` 5분. BackendTrafficPolicy `timeout.http.connectionIdleTimeout`(업스트림) 기본 **1시간** | 업스트림 1시간 > 앱 keepalive → 앱이 먼저 닫는 경쟁(§9 R3) | EG timeout_types.go · "Default: 1 hour." / "Default: 5 minutes." · 2026-10-01 |
| NW.request_timeout | [L7] **기본 15초**(Envoy 라우트 기본값). HTTPRoute `timeouts.request`가 BackendTrafficPolicy보다 우선. Gateway API 스펙상 미지정 시 동작은 구현마다 다르다, "0s"는 비활성 | **긴 요청은 15초에 504** | https://raw.githubusercontent.com/envoyproxy/gateway/main/site/content/en/latest/tasks/traffic/http-timeouts.md · "The default request timeout is set to 15 seconds in Envoy Proxy." · GA · "When this field is unspecified, request timeout behavior is implementation-specific." · 2026-10-01 |
| NW.websocket | [L7] HTTP/1.1 웹소켓 업그레이드 기본 허용. 지속 한도는 라우트 타임아웃에 걸리는지 미확인 | — | https://raw.githubusercontent.com/envoyproxy/gateway/main/internal/xds/translator/listener.go · "Allow websocket upgrades for HTTP 1.1" · 2026-10-01 |
| NW.protocols | [L7] HTTP/1.1·2, gRPC(GRPCRoute) | 인용 미확인 | — ⚠️근거없음 |
| NW.body_size | [L7] 최대 요청 헤더 **60 KiB**(상한 8,192 KiB). 연결 버퍼 32,768바이트(본문 한도 아님). 본문 한도 기본값 미확인 | — | EG clienttrafficpolicy_types.go · "Default: 60Ki bytes." / EG connection_types.go · "Default: 32768 bytes." · 2026-10-01 |
| NW.draining | [L7] EnvoyProxy `shutdown.drainTimeout` **60초**, `minDrainDuration` 10초 | terminationGracePeriodSeconds(기본 30)보다 길다 → 확인 필요 | EG envoyproxy_types.go · "If unspecified, defaults to 60 seconds." · 2026-10-01 |
| NW.health_check | 엔드포인트 readiness. 능동 헬스 체크는 BackendTrafficPolicy(인용 미확인) | — | — ⚠️근거없음 |
| NW.tls | [TLS] Gateway 리스너 TLS. 최소 버전 기본 미확인 | — | — ⚠️근거없음 |
| NW.client_ip | [L7] `clientIPDetection`: xForwardedFor(numTrustedHops 또는 trustedCIDRs), customHeader, directSourceIP 중 정확히 하나. PROXY protocol 기본 꺼짐(`proxyProtocol`, `enableProxyProtocol`은 deprecated) | 클라우드 L4 LB 뒤면 PROXY나 `externalTrafficPolicy: Local` | EG clienttrafficpolicy_types.go · "Exactly one of XForwardedFor, CustomHeader, or DirectSourceIP must be set." · 2026-10-01 |
| NW.routing | [L7] `backendRefs.weight`(기본 1, 0~1,000,000, 비율). `timeouts.backendRequest` ≤ `timeouts.request` | — | https://raw.githubusercontent.com/kubernetes-sigs/gateway-api/main/apis/v1/shared_types.go · "If unspecified, weight defaults to 1." · GA · "must be no more than the value of the Request timeout" · 2026-10-01 |
| NW.scaling | Envoy 프록시 Deployment 레플리카 | — | — ⚠️근거없음 |
| NW.availability | 레플리카 분산 | — | — ⚠️근거없음 |
| NW.security | SecurityPolicy(인증·CORS·레이트 리밋, 인용 미확인) | — | — ⚠️근거없음 |
| NW.caching / NW.dns / NW.egress / NW.private_connectivity | 해당 없음 | — | — |
| NW.regions | 해당 없음 | — | — |
| NW.cost_floor | 프록시 Pod + 앞단 L4 LB | — | — |

### 함정
- **요청 타임아웃 15초**가 ALB(60초), GKE(30초)보다 짧다. ingress-nginx(60초)에서 옮기면 15~60초 걸리던 요청이 504가 된다.
- 업스트림 유휴 1시간.

### 생성 산출물
- Helm으로 설치(`helm_release`, 차트 위치 미확인) + `GatewayClass`(`controllerName: gateway.envoyproxy.io/gatewayclass-controller`, 원문 미확인), `Gateway`, `HTTPRoute`(`timeouts.request`, `timeouts.backendRequest`, `backendRefs[].weight`), `ClientTrafficPolicy`(`timeouts.http.idleTimeout`, `clientIPDetection`), `BackendTrafficPolicy`(`timeout.http.requestTimeout`, `timeout.http.connectionIdleTimeout`), `EnvoyProxy`(`shutdown.drainTimeout`). ⚠️근거없음
- 반드시 명시:
  - A2: `HTTPRoute.spec.rules[].timeouts.request`. 기본 15초를 그대로 두지 않는다.
  - A3·R3: `BackendTrafficPolicy.timeout.http.connectionIdleTimeout` < 앱 keepalive.
  - F5: `clientIPDetection`.
  - F4: `drainTimeout` ≤ terminationGracePeriodSeconds.
- Checkov: 해당 없음 → kubeconform(Gateway API·EG CRD) + 커스텀.
- 검증: `kubectl get gateway`(PROGRAMMED), `egctl config envoy-proxy route`(명령 원문 미확인). 20초 응답 엔드포인트로 504가 없는지 확인한다. ⚠️근거없음

---

## 4.3 쿠버네티스 Service type LoadBalancer
- 계열: 네트워크-쿠버네티스 L4 진입점(클라우드 L4 LB 생성)
- 서울 리전: 해당 없음

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| NW.layer | [L4] 클라우드 L4 LB. EKS는 1.9 컨트롤러로 NLB, GKE는 패스스루 NLB(2.4, 인용 미확인) | — | — ⚠️근거없음 |
| NW.idle_timeout | 클라우드 LB 값(AWS NLB 350초, GCP 패스스루 60초 연결 추적) | — | 1.2, 2.4 |
| NW.request_timeout / NW.body_size | 해당 없음 | — | — |
| NW.websocket | 통과 | — | — ⚠️근거없음 |
| NW.protocols | TCP/UDP | — | — ⚠️근거없음 |
| NW.draining | 클라우드 LB 값 | — | — ⚠️근거없음 |
| NW.health_check | `Local`일 때 로컬 엔드포인트가 없는 노드는 패킷을 버린다 | — | https://raw.githubusercontent.com/kubernetes/website/main/content/en/docs/tutorials/services/source-ip.md · "If there are no local endpoints, packets sent to the node are dropped" · 2026-10-01 |
| NW.tls | 해당 없음(통과) | — | — |
| NW.client_ip | [L4] `externalTrafficPolicy: Cluster`(**기본**)는 클라이언트 IP를 가린다. `Local`은 보존하지만 트래픽이 불균형할 수 있다 | — | https://raw.githubusercontent.com/kubernetes/website/main/content/en/docs/tasks/access-application-cluster/create-external-load-balancer.md · "`Cluster` (default) and `Local`. `Cluster` obscures the client source IP" / "`Local` preserves the client source IP and avoids a second hop… but risks potentially imbalanced traffic spreading." · 2026-10-01 |
| NW.routing | 없음 | — | — ⚠️근거없음 |
| 나머지 키 | 클라우드 LB 값 / 해당 없음 | — | — |
| NW.cost_floor | 클라우드 L4 LB 1개(AWS $16.43, GCP $18.25) | — | 1.2, 2.4 |

### 생성 산출물
- `kubernetes_service_v1` 또는 매니페스트 `Service`(`type: LoadBalancer`, `externalTrafficPolicy: Local`이면 클라이언트 IP 보존). Terraform 리소스 이름의 Registry 원문은 미확인이다.
- 검증: `kubectl get svc`로 EXTERNAL-IP를 확인하고, 앱 로그로 원본 IP를 본다.

---

## 5. 자체 운영 리버스 프록시

앱 앞에 리버스 프록시로 흔히 생성된다(단일 VM + compose, 05 문서 경량 구성). 프록시는 **양쪽에 두 개의 부등식**을 만든다.
- 앞단 LB 유휴 < 프록시 클라이언트 keepalive
- 프록시 업스트림 keepalive < 앱 keepalive

5.x의 NW.regions·NW.cost_floor·NW.dns·NW.egress·NW.private_connectivity·NW.caching은 모두 `해당 없음`(호스트 비용)이다. 표에서는 생략하지 않고 한 행으로 묶는다.

## 5.1 nginx (mainline 1.31.6, stable 1.30.5)
- 계열: 네트워크-리버스 프록시 (L7)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| NW.layer | [L7] 종단 프록시. `stream` 모듈로 [L4]도 가능 | — | — ⚠️근거없음 |
| NW.idle_timeout | [L7] 클라이언트 `keepalive_timeout` **75초**. 업스트림: **1.29.7부터 `proxy_http_version` 기본 1.1, upstream keepalive 기본 켜짐(워커당 32)**, upstream `keepalive_timeout` 60초, `keepalive_requests` 1,000, `keepalive_time` 1h. 1.29.7 전에는 1.0이라 업스트림 재사용이 없었다 | 1.29.7+에서 nginx↔앱 구간에 R3 경쟁이 새로 생긴다 | https://nginx.org/en/docs/http/ngx_http_core_module.html · "Default: keepalive_timeout 75s;" · https://nginx.org/en/docs/http/ngx_http_proxy_module.html · "Since 1.29.7, version 1.1 is used by default. Before 1.29.7, version 1.0 was used by default." · https://nginx.org/en/docs/http/ngx_http_upstream_module.html · "Since 1.29.7, keepalive connections are enabled by default, with a default limit of 32 connections per each worker process." · https://nginx.org/en/CHANGES · "now ngx_http_proxy_module supports keepalive by default" · 2026-10-01 |
| NW.request_timeout | [L7] `proxy_read_timeout` 60초, `proxy_send_timeout` 60초(연속 두 읽기·쓰기 사이), `proxy_connect_timeout` 60초 | — | https://nginx.org/en/docs/http/ngx_http_proxy_module.html · 2026-10-01 |
| NW.protocols | [L7] HTTP/1.x·2·3(빌드에 따라), 업스트림 HTTP/1.x(1.29.7+ 기본 1.1), gRPC(`grpc_pass`) | — | — |
| NW.body_size | [L7] `client_max_body_size` **1m**, `client_header_buffer_size` 1k, `large_client_header_buffers` 4 8k, 헤더·본문 타임아웃 60초 | — | https://nginx.org/en/docs/http/ngx_http_core_module.html · 2026-10-01 |
| NW.draining | 우아한 종료 `nginx -s quit`(인용 미확인) | — | — ⚠️근거없음 |
| NW.health_check | 수동(passive) `max_fails`/`fail_timeout`(인용 미확인). 능동 체크는 상용 | — | — ⚠️근거없음 |
| NW.tls | [TLS] 설정에 따름 | — | — |
| NW.client_ip | [L7] realip 모듈: `set_real_ip_from` 기본 없음, `real_ip_header` 기본 X-Real-IP, `real_ip_recursive` off. `listen … proxy_protocol` | S-064: 신뢰 CIDR만 | https://nginx.org/en/docs/http/ngx_http_realip_module.html · https://nginx.org/en/docs/http/ngx_http_core_module.html · "allows specifying that all connections accepted on this port should use the PROXY protocol" · 2026-10-01 |
| NW.routing | [L7] location, upstream `weight`(인용 미확인) | — | — ⚠️근거없음 |
| NW.scaling / NW.availability / NW.security | 호스트 / 단일 호스트 / `limit_req`(02 문서 T-089(삭제됨)) | — | — |
| NW.caching / NW.dns / NW.egress / NW.private_connectivity / NW.regions / NW.cost_floor | 해당 없음(호스트 비용) | — | — |

### 함정
- 1m 업로드 한도.
- 웹소켓 헤더 누락으로 업그레이드가 실패한다.
- 1.29.7 이상으로 올리면 업스트림 keepalive가 기본으로 켜진다. 앱 keepalive가 60초보다 짧으면 이전에 없던 502가 생긴다.

### 생성 산출물
- `nginx.conf` 템플릿에 반드시 명시할 지시어:
  - A2: `proxy_read_timeout`
  - A3: `proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade"; proxy_http_version 1.1`
  - A7: `client_max_body_size`
  - R3: `upstream { keepalive N; keepalive_timeout < 앱 keepalive; }` 또는 앱 keepalive 상향
  - R1: `keepalive_timeout > 앞단 LB 유휴`
  - S-064: `set_real_ip_from <LB CIDR>; real_ip_header X-Forwarded-For; real_ip_recursive on`
- 정적 검사: `nginx -t`.
- 검증: 61초 무전송 웹소켓 유지, 1 MB 초과 업로드.

---

## 5.2 Envoy (v1.39.1, 독립 실행)
- 계열: 네트워크-리버스 프록시 (L7)

출처 약어: RC = https://raw.githubusercontent.com/envoyproxy/envoy/main/api/envoy/config/route/v3/route_components.proto, HCM = `.../extensions/filters/network/http_connection_manager/v3/http_connection_manager.proto`, PR = `.../config/core/v3/protocol.proto` (모두 envoyproxy/envoy main, 2026-10-01).

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| NW.layer | [L7] 종단, [L4] tcp_proxy | — | — ⚠️근거없음 |
| NW.idle_timeout | [L7] HttpProtocolOptions `idle_timeout` 기본 **1시간**(HCM 다운스트림·클러스터 업스트림 공용 메시지), `stream_idle_timeout` 5분 | 업스트림 1시간 > 앱 keepalive | PR · "If not specified, this defaults to ``1 hour``." / HCM · "If not specified, this defaults to ``5 minutes``." · 2026-10-01 |
| NW.request_timeout | [L7] 라우트 `timeout` 기본 **15초**(0이면 비활성). HCM `request_timeout` 비활성 | — | RC · "Specifies the upstream timeout for the route. If not specified, the default is 15s." · 2026-10-01 |
| NW.websocket | [L7] HCM 또는 라우트 `upgrade_configs`에 `websocket`을 명시해야 한다 | 라우트 타임아웃 15초가 웹소켓에도 걸리는지는 미확인 | HCM · "The case-insensitive name of this upgrade, e.g. "websocket"" · 2026-10-01 |
| NW.protocols | HTTP/1.1·2·3, gRPC | — | — ⚠️근거없음 |
| NW.body_size | [L7] `max_request_headers_kb` **60 KiB**. 연결 버퍼 `per_connection_buffer_limit_bytes` 1 MiB(본문 버퍼링 필터 사용 시 한도 역할) | — | HCM · "If unconfigured, the default max request headers allowed is 60 KiB." · listener.proto · "an implementation defined default is applied (1MiB)." · 2026-10-01 |
| NW.draining | [L7] HCM `drain_timeout` 5초 | — | HCM · "The default grace period is 5000 milliseconds (5 seconds)" · 2026-10-01 |
| NW.health_check | 능동·수동(이상치 감지) 지원, 기본 없음(인용 미확인) | — | — ⚠️근거없음 |
| NW.tls | 설정 | — | — ⚠️근거없음 |
| NW.client_ip | `use_remote_address`, `xff_num_trusted_hops`(인용 미확인) | — | — ⚠️근거없음 |
| NW.routing | 가중치 클러스터(인용 미확인) | — | — ⚠️근거없음 |
| 나머지 | 해당 없음(호스트) | — | — |

### 생성 산출물
- `envoy.yaml`에 명시할 항목:
  - 라우트 `timeout`(A2)
  - `upgrade_configs: [{upgrade_type: websocket}]`(A3)
  - 클러스터 `typed_extension_protocol_options` … `common_http_protocol_options.idle_timeout` < 앱 keepalive(R3)
- 정적 검사: `envoy --mode validate -c envoy.yaml`.

---

## 6. 티어 0 플랫폼 내장 엣지 프록시

플랫폼 자체 한도(함수 실행 시간, 메모리)는 [04-compute-tier0.md](04-compute-tier0.md)에 있다. 여기에는 **프록시 계층**의 값만 적는다. 서울·비용 키는 `04 문서`로 대체한다.

## 6.1 Vercel 엣지 네트워크(CDN 프록시)
- 계열: 네트워크-플랫폼 내장 엣지 프록시 (L7)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| NW.layer | [L7] 종단 | — | — ⚠️근거없음 |
| NW.idle_timeout | 미확인 | — | — |
| NW.request_timeout | [L7] 외부 목적지 rewrite·routes(프록시) **120초**(모든 플랜). 넘으면 `ROUTER_EXTERNAL_TARGET_ERROR`. 함수는 04 문서. Edge 런타임은 25초 안에 첫 바이트, 이후 300초까지 스트림 | — | https://vercel.com/docs/limits.md · "proxied request (`rewrites` or `routes` with an external destination)… maximum timeout is **120 seconds** (2 minutes)." · https://vercel.com/docs/functions/limitations.md · "must begin sending a response within 25 seconds… continue streaming data for up to 300 seconds." · 2026-10-01 |
| NW.websocket | [L7] 함수 웹소켓 **Public Beta**. 한 인스턴스에 고정되고, 함수 최대 실행 시간에 끊긴다 | — | https://vercel.com/docs/functions/websockets.md · "WebSocket connections close when a Vercel Function reaches its maximum duration." · 2026-10-01 |
| NW.protocols | HTTP/2·3 미확인 | — | — ⚠️근거없음 |
| NW.body_size | [L7] 함수 요청·응답 **4.5 MB**(넘으면 413). URL 14 KB, 헤더 개별 16 KB·합계 32 KB | — | https://vercel.com/docs/functions/limitations.md · "maximum payload size for the request body or the response body of a Vercel Function is **4.5 MB**" · https://vercel.com/docs/errors/request_header_too_large.md · "individual request headers must not exceed 16 KB… combined size of all headers… must not exceed 32 KB." · https://vercel.com/docs/errors/url_too_long.md · "(**14 KB**)" · 2026-10-01 |
| NW.draining | 배포 원자 전환, Skew Protection(`?dpl=`·`x-deployment-id`로 배포 고정, 수명·플랜 미확인) | — | https://vercel.com/docs/skew-protection.md · 2026-10-01 |
| NW.health_check | 해당 없음 | — | — |
| NW.tls | [TLS] TLS 1.2·1.3 | — | https://vercel.com/docs/cdn-security/encryption.md · "Vercel supports TLS version 1.2 and TLS version 1.3." · 2026-10-01 |
| NW.client_ip | [L7] **XFF를 덮어쓰고 외부 IP를 전달하지 않는다**(스푸핑 방지). `x-vercel-forwarded-for`·`x-real-ip` 같은 값. Enterprise Trusted Proxy 애드온으로 예외 | 앞에 Cloudflare 등을 두면 원래 클라이언트 IP가 사라진다 | https://vercel.com/docs/headers/request-headers.md · "we currently overwrite the X-Forwarded-For header and **do not forward external IPs**… to prevent IP spoofing." · 2026-10-01 |
| NW.routing | [L7] Rolling Releases(방문자 일부 %, 예 5%). 플랜 조건 미확인 | — | https://vercel.com/docs/rolling-releases.md · "Vercel directs a configurable fraction of your visitors, for example, 5%, to the new deployment." · 2026-10-01 |
| 나머지 | 04 문서 / 10 문서 | — | — |

### 생성 산출물
- `vercel.json` `rewrites`(외부 프록시면 120초 한도를 판정에 넣음). Terraform `vercel/vercel` provider 리소스는 08 문서 P1 참조(이번 미확인).
- 검증: 4.5 MB 초과 업로드 413, 헤더 32 KB 초과 431(상태 코드 미확인).

---

## 6.2 Netlify 엣지(CDN 프록시)
- 계열: 네트워크-플랫폼 내장 엣지 프록시 (L7)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| NW.layer | [L7] 종단 | — | — ⚠️근거없음 |
| NW.idle_timeout | 미확인 | — | — |
| NW.request_timeout | [L7] 프록시 rewrite **26초**. 함수 동기 60초(04 문서) | 외부 API를 `/api/*` 프록시로 붙인 구성은 26초가 상한 | https://docs.netlify.com/manage/routing/redirects/rewrites-proxies.md · "Proxy rewrite requests will time out after 26 seconds." · 2026-10-01 |
| NW.websocket | 미확인(문서 421쪽 전수 검색에서 언급 없음) | — | — |
| NW.protocols | [L7] HTTP/2(HTTPS, 서버 푸시 없음). HTTP/3 미확인 | — | https://docs.netlify.com/manage/domains/secure-domains-with-https/https-ssl.md · "Netlify supports HTTP/2… does not include server push capability." · 2026-10-01 |
| NW.body_size | 프록시 한도 미확인. 함수 버퍼 6 MB, 스트리밍 응답 20 MB | — | https://docs.netlify.com/build/functions/configuration.md · "Buffered request/response payload \| 6 MB" · 2026-10-01 |
| NW.draining / NW.health_check | 해당 없음 | — | — |
| NW.tls | 최소 TLS 미확인. 프록시 요청에 `x-nf-sign` JWS 서명 헤더(오리진 검증용) | — | https://docs.netlify.com/manage/routing/redirects/rewrites-proxies.md · "Netlify will send the JWS as an HMAC HS256 encoded `x-nf-sign` header" · 2026-10-01 |
| NW.client_ip | 함수 `context.ip`. 프록시가 오리진에 보내는 IP 헤더는 미확인 | — | https://docs.netlify.com/build/functions/api.md · "A string containing the client IP address." · 2026-10-01 |
| NW.routing | [L7] 분기 기반 Split Testing(%). **프록시·함수 응답에는 제대로 동작하지 않는다**. 사이트 간 내부 rewrite 1홉 | — | https://docs.netlify.com/manage/monitoring/split-testing.md · "Split Testing doesn't work properly for responses from proxies or functions." · 2026-10-01 |
| 나머지 | 04 문서 | — | — |

### 생성 산출물
- `netlify.toml` `[[redirects]] status = 200`(프록시). 26초를 넘는 경로가 있으면 직접 호출로 바꾼다.
- 검증: 27초 응답 엔드포인트.

---

## 6.3 Cloudflare 프록시 모드(주황 구름)
- 계열: 네트워크-엣지 리버스 프록시 (L7, 애니캐스트)

| 능력 키 | 값 | 조건·한도 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|
| NW.layer | [L7] 종단, 전역 애니캐스트 | — | — ⚠️근거없음 |
| NW.idle_timeout | [L7] 클라이언트 쪽 Keep-Alive HTTP/1.1 400초, HTTP/2 유휴 400초. 오리진 쪽 **Proxy Idle Timeout 900초**(초과 시 520, 변경 불가), 오리진 HTTP/2 유휴 900초 | 오리진 keepalive > 900초여야 경쟁이 없다(R2와 같은 원리, 추론) | https://developers.cloudflare.com/fundamentals/reference/connection-limits/index.md · "Proxy Idle Timeout \| 900 \| 520 \| No" / "Connection Keep-Alive HTTP/1.1 \| 400" · 2026-10-01 ⚠️근거없음 |
| NW.request_timeout | [L7] **Proxy Read Timeout 기본 125초** → 524. Enterprise만 최대 6,000초. Proxy Write 30초(변경 불가). 오리진 TCP 연결 19초(522), ACK 90초 | 2분 넘는 동기 요청은 524 | https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-5xx-errors/error-524/index.md · "did not provide an HTTP response before the default 125 seconds Proxy Read Timeout" / "Enterprise customers can increase the 524 timeout up to 6,000 seconds" · 2026-10-01 |
| NW.websocket | [L7] 모든 플랜 지원. **서버 재시작 시 끊긴다**(재연결 필수). 유휴 타임아웃 수치는 미확인 | — | https://developers.cloudflare.com/network/websockets/index.md · "WebSockets are supported on all Cloudflare plans." / "we may restart servers, which terminates WebSockets connections." · 2026-10-01 |
| NW.protocols | [L7] 클라이언트 HTTP/3(모든 플랜), 오리진 HTTP/3 미지원. 오리진 HTTP/2 기본 켜짐(스트림 수 [충돌] 200 vs 100, Enterprise 1) | — | https://developers.cloudflare.com/speed/optimization/protocol/http3/index.md · "HTTP/3 connection to the origin is not yet supported." · https://developers.cloudflare.com/speed/optimization/protocol/http2-to-origin/index.md · "HTTP/2 connection to the origin is enabled by default." · 2026-10-01 |
| NW.body_size | [L7] 업로드 Free·Pro **100 MB**, Business 200 MB, Enterprise 최대 5 GB. URL 16 KB, 요청 헤더 합계 128 KB, 응답 헤더 합계 128 KB | 대용량 업로드는 서명 URL로 저장소에 직접(03 문서) | https://developers.cloudflare.com/cache/concepts/default-cache-behavior/index.md · "Max upload size \| 100 MB \| 100 MB \| 200 MB \| Up to 5 GB" · https://developers.cloudflare.com/fundamentals/reference/connection-limits/index.md · "URLs have a limit of 16 KB. Request headers have a total limit of 128 KB." · 2026-10-01 |
| NW.draining / NW.health_check | 해당 없음(Load Balancing 애드온은 헬스 체크 있음, 10 문서) | — | — |
| NW.tls | [TLS] 최소 TLS 버전 설정 가능(기본값 미확인). 오리진 TLS 모드는 10 문서 | — | https://developers.cloudflare.com/ssl/edge-certificates/additional-options/minimum-tls/index.md · 2026-10-01 |
| NW.client_ip | [L7] `CF-Connecting-IP`(클라이언트 IP). XFF는 **덧붙임**. `True-Client-IP`는 Enterprise만 | 오리진은 Cloudflare IP 대역만 신뢰하고 `CF-Connecting-IP`를 쓴다 | https://developers.cloudflare.com/fundamentals/reference/http-headers/index.md · "provides the client IP address connecting to Cloudflare to the origin web server." / "`True-Client-IP` is only available on an Enterprise plan." · 2026-10-01 |
| NW.routing | Load Balancing 애드온 가중치 0~1(0.01 단위) | — | https://developers.cloudflare.com/load-balancing/understand-basics/traffic-steering/origin-level-steering/index.md · "set the Weight to a number between 0 and 1 (expressed in increments of .01)" · 2026-10-01 |
| NW.availability / NW.caching / NW.security / NW.dns | 10 문서 | — | — |
| NW.regions / NW.cost_floor | 서울 PoP 미확인 / 04 문서 | — | — |

### 함정
- 125초 524는 ALB 유휴를 4,000초로 늘려도 앞에서 먼저 끊긴다. 경로 최솟값이 이긴다(§9 R4).
- 오리진 keepalive 900초.

### 생성 산출물
- Cloudflare Terraform provider의 DNS 레코드(`proxied = true`) 리소스는 10 문서에서 다룬다(리소스 이름은 provider 버전에 따라 다름, 미확인).
- Enterprise가 아니면 Proxy Read Timeout은 바꿀 수 없다 → 긴 요청은 비동기 작업 + 폴링으로 코드를 바꾼다.
- 검증: 126초 응답으로 524를 확인한다.

---

## 6.5 Railway 엣지 프록시
- 계열: 네트워크-플랫폼 내장 엣지 프록시 (L7)
- 출처: 마지막 두 행을 빼면 https://docs.railway.com/networking/public-networking/specs-and-limits.md · 2026-10-01

| 능력 키 | 값 | 조건·한도 | 출처 (인용) |
|---|---|---|---|
| NW.layer | [L7] 종단 | — | — ⚠️근거없음 |
| NW.idle_timeout | [L7] HTTP/1.1 요청 사이 유휴 **60초**(HTTP/2·웹소켓 제외) | 앱 keepalive > 60초 | "Idle HTTP/1.1 connections are closed after 60 seconds between requests." |
| NW.request_timeout | [L7] 데이터가 계속 오가면 최대 **15분**, 무전송 5분이면 종료 | — | "HTTP requests can run for up to 15 minutes if data keeps transferring… otherwise closed after 5 minutes with no data transferred." |
| NW.websocket | [L7] HTTP/1.1 웹소켓, **지속·유휴 한도에서 제외(무기한)** | — | "Websocket connections are exempt from these duration and inactivity limits, and can stay open indefinitely" |
| NW.protocols | HTTP/1.1·HTTP/2 | — | 같은 페이지 |
| NW.body_size | [L7] 업로드는 5분 안에 끝나야 한다(크기 한도 문구 없음). 헤더 합계 32 KB | — | "Request bodies must finish uploading within 5 minutes." / "Max 32 KB combined header size." |
| NW.draining | `RAILWAY_DEPLOYMENT_OVERLAP_SECONDS`·`RAILWAY_DEPLOYMENT_DRAINING_SECONDS`, 기본값 미확인 | — | https://docs.railway.com/deployments/deployment-teardown.md · 2026-10-01 |
| NW.health_check | 배포 시에만(기본 300초), **지속 감시 아님** | — | https://docs.railway.com/deployments/healthchecks.md · "**_not used for continuous monitoring_**" · 2026-10-01 |
| NW.tls | [TLS] TLS 1.2 이상, SNI 필수 | — | "All traffic must be HTTPS and use TLS 1.2 or above, and TLS SNI is mandatory" |
| NW.client_ip | [L7] `X-Real-IP`. XFF 동작 미확인 | — | "`X-Real-IP` for identifying client's remote IP." |
| NW.routing | 가중치 없음. 레플리카에 무작위, 가까운 리전 우선 | — | https://docs.railway.com/deployments/scaling.md · "Railway will randomly distribute public traffic to the replicas of that region." · 2026-10-01 |
| NW.scaling | 동시 연결 10,000, 도메인당 약 11,000 RPS, 연결당 요청 10,000 | — | "Maximum Connections \| 10,000 concurrent connections" |
| 나머지 | 04 문서 | — | — |

### 생성 산출물
- `railway.json`(08 문서). 앱 짝 변경: keepalive > 60초, IP는 `X-Real-IP`.

---

## 7. 앱 서버 기본값 (부등식의 반대편)

경로 규칙(§9)에서 LB 값과 비교할 앱 쪽 값이다. 코드에 설정이 없으면 이 기본값이 적용된 것으로 본다(02 문서 §제안 5의 `defaulted: true`).

| 서버 | keep-alive 유휴 기본 | 요청·작업 타임아웃 기본 | 헤더·본문 한도 기본 | 프록시 헤더 신뢰 기본 | 출처 (URL · 짧은 인용 · 2026-10-01) |
|---|---|---|---|---|---|
| uvicorn | **5초**(`--timeout-keep-alive`) | 요청 타임아웃 설정 없음. 우아한 종료 무제한(`None`) | h11 불완전 이벤트 16 KB. 본문 한도 설정 없음 | `--proxy-headers` 켜짐, 신뢰 IP 127.0.0.1·::1 → LB 뒤에서는 클라이언트 IP가 LB IP로 보인다 | https://uvicorn.dev/settings/ · "Close Keep-Alive connections if no new data is received within this timeout (in seconds). Default: 5" / "Otherwise, 127.0.0.1 and ::1 are trusted." · 2026-10-01 |
| gunicorn | **2초**(`keepalive`). **sync 워커는 keep-alive 미지원**(매 응답 후 연결 닫음) | 워커 무응답 `timeout` **30초** → 강제 재시작. `graceful_timeout` 30초 | 요청 줄 4,094, 헤더 100개, 헤더 필드 8,190 | `forwarded_allow_ips` "127.0.0.1,::1" | https://gunicorn.org/reference/settings/ · "Default: 2 The number of seconds to wait for requests on a Keep-Alive connection." / "sync worker does not support persistent connections and will ignore this option." / "When Gunicorn is deployed behind a load balancer, it often makes sense to set this to a higher value." / "Default: 30 Workers silent for more than this many seconds are killed and restarted." · 2026-10-01 |
| Node.js http | **5초**(`keepAliveTimeout`) + `keepAliveTimeoutBuffer` 1초(v24.6.0·v22.19.0부터) = 실제 소켓 6초 | `requestTimeout` 300초(v18+), `headersTimeout` min(requestTimeout, 60초), `server.timeout` 0 | 헤더 16 KiB. 본문 한도 없음(프레임워크가 정함) | 해당 없음(프레임워크) | https://nodejs.org/api/http.html · "Default: 5000 (5 seconds)." / "socketTimeout = keepAliveTimeout + keepAliveTimeoutBuffer" / "Default: 300000" · https://nodejs.org/api/cli.html · "Defaults to 16 KiB." · 2026-10-01 |
| Next.js `next start` | 옵션 `--keepAliveTimeout`. 미지정이면 Node 기본(5초)이 그대로 적용(소스) | Node와 같음 | Server Actions 본문 1 MB, Pages API `bodyParser.sizeLimit` 1mb, `proxyClientMaxBodySize` 10 MB | — | https://nextjs.org/docs/app/api-reference/cli/next · "configure Next's underlying HTTP server with keep-alive timeouts that are larger than the downstream proxy's timeouts." · https://raw.githubusercontent.com/vercel/next.js/canary/packages/next/src/server/lib/start-server.ts · `if (keepAliveTimeout) { server.keepAliveTimeout = keepAliveTimeout` · https://nextjs.org/docs/app/api-reference/config/next-config-js/serverActions · "By default, the maximum size of the request body sent to a Server Action is 1MB" · 2026-10-01 |
| Express | Node와 같음 | Node와 같음 | `express.json()` **100kb** | `trust proxy` **false** | https://raw.githubusercontent.com/expressjs/body-parser/master/README.md · "Defaults to `'100kb'`." · https://expressjs.com/en/guide/behind-proxies.html · "This is the default setting." · 2026-10-01 |
| Django (+gunicorn/uvicorn) | 서버에 따름(runserver는 운영 금지) | 서버에 따름 | `DATA_UPLOAD_MAX_MEMORY_SIZE` 2.5 MB, `FILE_UPLOAD_MAX_MEMORY_SIZE` 2.5 MB | `SECURE_PROXY_SSL_HEADER` None, `USE_X_FORWARDED_HOST` False | https://docs.djangoproject.com/en/stable/ref/settings/ · "Default: 2621440 (i.e. 2.5 MB). The maximum size in bytes that a request body may be" · 2026-10-01 |
| Go net/http | `IdleTimeout` 0 → `ReadTimeout` 사용, 둘 다 0이면 **무제한**. keep-alive 항상 켜짐 | `ReadTimeout`·`WriteTimeout` 0 = 무제한. Shutdown은 무기한 대기 | 헤더 1 MB | 해당 없음 | https://pkg.go.dev/net/http · "If zero, the value of ReadTimeout is used. If negative, or if zero and ReadTimeout is zero or negative, there is no timeout." / "DefaultMaxHeaderBytes = 1 << 20 // 1 MB" · 2026-10-01 |
| Spring Boot + Tomcat | `keepAliveTimeout` = `connectionTimeout`. Tomcat 코드 기본 **60초**(배포판 server.xml은 20초). Boot 기본값 명시는 없음 → 60초로 추론 | 우아한 종료 기본 켜짐, 단계당 30초 | 헤더 8 KB, multipart 파일 1 MB·요청 10 MB | `forward-headers-strategy` 클라우드 플랫폼이면 NATIVE, 아니면 NONE | https://tomcat.apache.org/tomcat-10.1-doc/config/http.html · "The default value is 60000 (i.e. 60 seconds) but note that the standard server.xml that ships with Tomcat sets this to 20000" / "The default value is to use the value that has been set for the connectionTimeout attribute." · https://docs.spring.io/spring-boot/how-to/webserver.html · "defaults to NATIVE . In all other instances, it defaults to NONE ." · 2026-10-01 ⚠️근거없음 |
| Bun.serve | **10초**(`idleTimeout`, 최대 255). **실행 중이지만 아직 바이트를 쓰지 않은 요청도 유휴로 센다** | — | `maxRequestBodySize` 128 MB | — | https://bun.sh/docs/api/http (→ /docs/runtime/http/server) · "By default, Bun.serve closes connections after 10 seconds of inactivity." / "That includes in-flight requests where your handler is still running but hasn't written any bytes" · 2026-10-01 |
| Deno.serve | 미확인 | 미확인 | 미확인 | — | https://docs.deno.com/runtime/fundamentals/http_server/ · 2026-10-01 |
| Flask/Werkzeug 개발 서버 | 운영 금지 | — | — | — | https://flask.palletsprojects.com/en/stable/deploying/ · "Do not use the development server when deploying to production." · 2026-10-01 |
| 쿠버네티스 Pod | — | `terminationGracePeriodSeconds` 기본 30초 | — | — | https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/ · "The default terminationGracePeriodSeconds setting is 30 seconds." · 2026-10-01 |

---

## 8. 조사 결과 요약

- 구성 요소 **28개**(원래 32개. 5.3 Caddy·5.4 Traefik·6.4 Render·6.6 Fly.io는 2026-10-02에 부적격 출처로 삭제):
  - AWS 9: ALB, NLB, GWLB, API GW 3종, Function URL, Express ALB, LB Controller
  - GCP 9: 전역·리전·클래식 ALB, 패스스루·프록시 NLB, 내부 LB, Cloud Run 엔드포인트·도메인 매핑, GKE Gateway, 서버리스 NEG
  - Azure 1
  - 쿠버네티스 3: ingress-nginx, Envoy Gateway, Service LB
  - 자체 프록시 2: nginx, Envoy
  - 티어 0 엣지 4: Vercel, Netlify, Cloudflare, Railway
  - §7 앱 서버 기본값 12행은 별도다(원래 14행, Puma·Hypercorn 행 삭제).
- (삭제 전 기준) 능력 행 482개 중 값 전체가 `미확인`인 행은 22개다. 값의 일부(세부 수치나 인용)만 `미확인`인 행은 80개다. 이 중 판정에 직접 쓰이는 것은 다음과 같다: ALB 본문 한도, ECS Express ALB 유휴·드레이닝, Fly 유휴 기본값, Netlify·Fly 웹소켓, Cloud Run XFF, GCP 서울 단가.
- AWS 단가는 Price List 오퍼 파일(서울)을 읽었다. GCP는 가격 페이지 정적 HTML의 Iowa 값이고 **서울 단가는 미확인**이다.
- Checkov ID는 정책 인덱스 또는 Checkov 소스에서 존재를 확인한 것만 적었다.
  - CKV_AWS_95는 Terraform 체크가 아니라 CloudFormation 전용이다.
  - GCP 쪽 LB 체크는 CKV_GCP_4 하나뿐이다. backend_service, target_https_proxy, url_map을 보는 체크는 없다.
- 주요 [충돌]:
  - Terraform `aws_lb_target_group.health_check` 기본값(3/3/6초)과 AWS 문서(5/2/5초)
  - ALB 기본 TLS 정책(콘솔 vs CLI·Terraform)
  - REST API 통합 타임아웃 상한(Terraform 300,000/900,000 ms vs API 참조 29,000 ms)
  - ECS Express desync "Off"
  - GCP 리전 외부 ALB의 keepalive 기본(600/610)·범위(5~600/5~1,200)와 네트워크 티어
  - Azure 프리미엄 인그레스 종료 유예 단위(초/분)
  - Cloudflare 오리진 HTTP/2 스트림 수(200/100)
- 2026-10-01 기준으로 이전 문서·통념과 달라진 값:
  - ingress-nginx 은퇴·아카이브
  - nginx 1.29.7 업스트림 keepalive 기본 켜짐
  - Node `keepAliveTimeoutBuffer` 1초
  - Cloudflare Proxy Read 125초(100초 아님)
  - Cloudflare Enterprise 업로드 최대 5 GB
  - Vercel 웹소켓 베타
  - Terraform google provider v8의 `load_balancing_scheme` 기본 `EXTERNAL_MANAGED`

---

## 9. 경로 부등식 규칙 후보

- 표기: `앱` = §7 값, `LB` = §1~6 값. 모든 규칙은 **경로 위 인접한 두 구성 요소 쌍마다** 적용한다.
  - 예: 사용자 → Cloudflare → ALB → nginx → uvicorn이면 (Cloudflare, ALB), (ALB, nginx), (nginx, uvicorn) 세 쌍이다.
- 값이 코드·IaC에 없으면 기본값으로 계산하고 `defaulted: true`를 붙인다.
- "위반 예"는 기본값끼리의 결과다.

### R1. 앱(하류) keep-alive 유휴 > LB(상류) 업스트림 유휴 — 간헐 502
- 규칙: `downstream.keepalive_idle > upstream.backend_idle_timeout`. 같으면 위반으로 본다(경계 경쟁).
- 근거: AWS "configure the idle timeout of your application to be larger than the idle timeout configured for the load balancer"(1.1). Next.js도 "keep-alive timeouts that are larger than the downstream proxy's timeouts"라고 쓴다(§7).
- AWS ALB(60초) 뒤 위반 예:

| 앱 서버 | keep-alive 기본 | 결과 |
|---|---|---|
| uvicorn | 5 | 위반 |
| Node·Express·Next | 5+1 | 위반 |
| Bun | 10 | 위반 |
| Spring/Tomcat | 60 | 같음 → 위반 |
| Go (ReadTimeout만 설정, 예: 10) | 10 | 위반 |
| Go 기본 | 무제한 | 통과 |

- gunicorn sync는 keep-alive를 지원하지 않아 연결을 매번 닫는다. 재사용 경쟁은 없지만 연결 비용이 크다. 비 sync 워커는 2초라 위반이다.
- Railway(HTTP/1.1 60초)와 nginx 클라이언트 쪽(75초, 앞단 ALB 60초 < 75초면 통과)에도 같은 규칙을 적용한다.
- 처방: 앱 keep-alive = LB 유휴 + 5~15초. 예: uvicorn `--timeout-keep-alive 65`, Node `server.keepAliveTimeout = 65000` + `headersTimeout`을 그보다 크게.

### R2. GCP L7 백엔드 keepalive 600초 고정 → 앱 keep-alive > 600초 (권장 620)
- 대상: 2.1, 2.2, 2.3, 2.6, 2.8의 백엔드.
- §7의 어떤 기본값도 통과하지 못한다. Go 기본(무제한)만 통과한다.
- LB 쪽에서 바꿀 수 없으므로 **반드시 앱 코드·실행 인자 변경**이 산출물에 포함된다.
- nginx를 사이에 두면 nginx `keepalive_timeout`(75초)도 620초로 올린다(GCP 문서 예시).
- Cloudflare → 오리진 구간도 같은 원리다. Cloudflare Proxy Idle 900초 → 오리진 keep-alive > 900초가 이상적이다(추론, Cloudflare 문서에 권고 문장은 미확인). ⚠️근거없음

### R3. 프록시 업스트림 유휴 < 앱 keep-alive — 프록시가 앱 앞에 있을 때
- 규칙: `proxy.upstream_idle < app.keepalive_idle`(R1과 같은 원리, 프록시가 클라이언트 쪽).

| 프록시 | 업스트림 유휴 기본 | 앱 uvicorn 5초 / Node 6초와의 관계 |
|---|---|---|
| nginx ≥1.29.7 | 60초(keepalive 기본 켜짐) | 위반 |
| nginx <1.29.7 | 재사용 없음(HTTP/1.0) | 해당 없음 |
| ingress-nginx | 60초 | 위반 |
| Envoy / Envoy Gateway | 1시간 | 위반 |

- 처방: 앱 keep-alive를 올리거나 프록시 업스트림 유휴를 앱보다 짧게 둔다(예: nginx `upstream { keepalive_timeout 4s; }`).

### R4. 요청 처리 시간(A2) < 경로 위 모든 요청·응답 타임아웃의 최솟값
- 규칙: `A2.max_handler_seconds < min(path[*].request_timeout)`.
- 각 구성 요소의 기본값:

| 구성 요소 | 기본 요청 타임아웃 |
|---|---|
| Envoy·Envoy Gateway | 15초 |
| Netlify 프록시 | 26초 |
| API GW REST | 29초 |
| API GW HTTP | 30초(고정) |
| GCP ALB·GKE Ingress·Gateway | 30초(응답 전체) |
| gunicorn 워커 | 30초(넘으면 워커가 죽음) |
| ALB | 60초(무전송) |
| ingress-nginx·nginx `proxy_read` | 60초(무전송) |
| Vercel 외부 rewrite | 120초 |
| Cloudflare | 125초 |
| Azure CA | 240초 |
| Cloud Run | 300초 |
| Node `requestTimeout` | 300초 |
| Lambda | 900초 |
| Railway | 15분 |
| 서버리스 NEG | 60분 |

- 주의: "무전송 간격" 타임아웃(ALB, nginx)과 "응답 전체" 타임아웃(GCP 백엔드, API GW, Cloudflare 첫 바이트 기준)을 구분한다.
- 스트리밍 응답은 앞의 것만 피할 수 있다.
- 처방:
  - 값을 올린다(가능한 구성 요소만).
  - 고정 한도(API GW HTTP 30초, Cloudflare 비 Enterprise 125초, Netlify 26초)에 걸리면 **비동기 작업 + 폴링/웹훅으로 코드를 바꾼다**(03 문서 큐).

### R5. 장시간 연결(A3): 하트비트 간격 < 경로 최소 유휴, 세션 길이 ≤ 경로 최소 강제 종료
- 하트비트 간격 < `min(path[*].idle)`. 각 유휴 한도:
  - ALB 60초
  - nginx·ingress-nginx `proxy_read` 60초
  - GCP 프록시 NLB 30초
  - GCP 패스스루 NLB 연결 추적 60초
  - API GW WebSocket 10분
  - Railway 5분(HTTP. 웹소켓은 제외)
  - Envoy `stream_idle_timeout` 5분
- 세션 길이 ≤ `min(path[*].max_duration)`. 각 강제 종료 한도:
  - GCP 클래식 ALB·gxlb: **백엔드 타임아웃(기본 30초)**
  - API GW WebSocket 2시간
  - GCP 전역 managed ALB 24시간
  - Cloud Run 요청 타임아웃(최대 60분)
  - Vercel 함수 최대 실행 시간
  - Cloudflare(재시작 시 종료)
- 클라이언트 재연결 코드가 없고 경로에 강제 종료가 있으면 위반이다.

### R6. 요청 본문 크기(A7) ≤ 경로 최소 본문 한도, 그리고 앱 프레임워크 한도와 정합
- 경로 쪽 한도:

| 구성 요소 | 본문 한도 |
|---|---|
| ALB → Lambda 대상 | 1 MB |
| nginx·ingress-nginx | 1m |
| Next Server Actions | 1 MB |
| Vercel 함수 | 4.5 MB |
| Lambda·Function URL | 6 MB |
| Netlify 함수 | 6 MB |
| API GW | 10 MB |
| Cloud Run HTTP/1 | 32 MiB |
| Cloudflare Free·Pro | 100 MB |

- 앱 쪽 한도: Express json 100kb, Django 2.5 MB, Spring multipart 1 MB, Bun 128 MB.
- 상류 한도 > 하류 한도면 사용자에게 413이 다른 계층에서 나와 원인 추적이 어렵다. 한도를 명시적으로 맞추거나, 대용량은 서명 URL 직접 업로드로 코드를 바꾼다.

### R7. 헤더 크기: 경로 최소 헤더 한도 ≥ 앱이 받는 최대 헤더(쿠키 포함)
- 경로 쪽 한도:
  - gunicorn 필드 8,190바이트
  - Tomcat 8 KB
  - nginx 버퍼 8k
  - API GW HTTP 10,240바이트(요청 줄 포함)
  - Node 16 KiB
  - Vercel 개별 16 KB·합계 32 KB
  - Railway 32 KB
  - ALB 64K
  - GCP 60/64 KiB
  - Envoy 60 KiB
  - Cloudflare 128 KB
- 큰 세션 쿠키(JWT 다수)를 쓰는 앱은 가장 작은 한도에서 400·431이 난다.

### R8. 드레이닝과 종료 순서: 대상 해제 반영 ≤ preStop < 드레이닝 ≤ 종료 유예
- 규칙(03 문서 타이밍 정렬과 같음): `preStop_sleep ≥ LB 해제 전파 시간`, `LB.draining ≥ 최장 진행 요청`, `LB.draining ≤ preStop + 앱 드레인 ≤ terminationGrace(ECS stopTimeout)`.
- 기본값 위반 예:
  - GCP BackendConfig·GCPBackendPolicy 드레이닝 **0** → 진행 중 요청이 끊긴다.
  - ALB 300초 > ECS stopTimeout 최대 120초 → 대상은 계속 draining인데 태스크는 이미 SIGKILL. 배포가 대상마다 최대 5분 늘어난다.
  - Envoy Gateway drain 60초 > 쿠버네티스 grace 30초.
  - uvicorn 우아한 종료 무제한.

### R9. 클라이언트 IP: 앱의 신뢰 홉 수 = 경로의 프록시 홉 수, 신뢰 대상 = 바로 앞 홉의 CIDR
- 경로별 클라이언트 IP 위치:
  - ALB(XFF append): 마지막 값.
  - GCP ALB: 끝에서 두 번째(`<client>,<lb>`).
  - Azure CA: 가장 오른쪽.
  - Cloudflare: `CF-Connecting-IP`.
  - Vercel: XFF 덮어씀 → 앞단 프록시 IP는 사라진다.
  - Railway: `X-Real-IP`.
  - NLB ip 대상·GCP 프록시 NLB: PROXY protocol이 필요하다.
  - k8s Service `Cluster`: IP를 잃는다.
- 앱 기본값:
  - uvicorn·gunicorn: 127.0.0.1만 신뢰 → LB IP가 기록된다. 레이트 리밋이 전원을 한 IP로 본다.
  - Express: `trust proxy` false.
- 위반 판정: `trust proxy: true`나 `--forwarded-allow-ips='*'`(스푸핑, 05 문서 S-064), 또는 신뢰 없음(전원 같은 IP).
- 처방: 신뢰 CIDR = 바로 앞 LB 서브넷이나 Cloudflare IP 대역, 홉 수를 명시한다.

### R10. 헬스 체크 실패 시 동작과 readiness 설계
- 전부 비정상일 때 동작:
  - AWS ALB·NLB, GCP 패스스루 NLB: **fail-open**.
  - GCP 클래식 ALB: **502**.
  - GCP managed ALB: **503**.
  - GCP 프록시 NLB: 연결 거부.
  - 서버리스 NEG: 헬스 체크 없음.
  - Railway: 배포 시에만 확인.
- fail-open이 아닌 LB에서 readiness가 DB·외부 의존성에 묶여 있으면 의존성 장애가 곧 전체 장애다(F1 판정에 반영). readiness는 프로세스 자체 상태만 보게 한다(08 문서).
- 헬스 체크 기본 경로 `/`가 인증·리다이렉트(301/302)를 반환하면 ALB 매처 200에서 비정상이 된다. 경로를 명시한다.

### R11. 트래픽 분할 요구(F4 카나리) ⊆ 경로가 지원하는 분할
- 분할 없음: API GW HTTP API, GCP 클래식 ALB·gxlb, Railway, Netlify(프록시·함수).
- 카나리 요구가 있으면 managed 클래스·ALB 가중치·Cloud Run 리비전 %·Azure 리비전 가중치로 교체한다.

### R12. 프로토콜 정합
- gRPC: 종단 간 HTTP/2가 필요하다.
  - ALB는 대상 `protocol_version = GRPC`.
  - GCP 클래식은 H2C 불가.
  - Cloud Run은 기본 HTTP/1 다운그레이드(gRPC 제외).
- SSE 스트리밍은 경로 위 버퍼링을 해제해야 한다(nginx `X-Accel-Buffering: no`, Lambda `RESPONSE_STREAM`).
- 웹소켓은 nginx에 Upgrade 헤더, Envoy에 `upgrade_configs`가 필요하다.

### R13. 최소 TLS 버전(F5) ≤ 경로의 실제 최소
- 기본값이 TLS 1.0을 허용하는 구성 요소:
  - GCP SSL 정책 없음(COMPATIBLE·TLS 1.0)
  - Cloud Run 도메인 매핑(1.0·1.1 끌 수 없음)
  - ALB Terraform 기본 `ELBSecurityPolicy-2016-08`
  - API GW REST TLS_1_0 선택 가능
- F5가 "결제·의료·공공"이면 정책을 명시하거나 구성 요소를 교체한다(도메인 매핑 → ALB).
