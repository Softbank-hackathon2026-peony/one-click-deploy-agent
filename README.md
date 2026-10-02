# one-click-deploy-agent (`infrafit`)

저장소 하나를 받아 **지금 무엇으로 어떻게 돌아가는지 파악하고**, 그 앱에 **필요한 만큼의 인프라를 근거와 함께 추천**하는 도구다. 최종 목표는 사용자와 대화로 구성을 정한 뒤 코드를 고치고 Dockerfile·Terraform 같은 산출물을 만들어 검증까지 하는 것이다.

- 설계 문서: [docs/superpowers/specs/2026-10-01-infrafit-design.md](docs/superpowers/specs/2026-10-01-infrafit-design.md)
- 구현 계획과 판정 기록: [docs/superpowers/plans/](docs/superpowers/plans/), [docs/superpowers/notes/2026-10-02-plan1-rulings-and-followups.md](docs/superpowers/notes/2026-10-02-plan1-rulings-and-followups.md)
- 출처 감사: [docs/research/source-audit.md](docs/research/source-audit.md)

---

## 1. 왜 만들었나

바이브코딩으로 앱을 만드는 사람은 Dockerfile, Kubernetes, Terraform을 모르는 경우가 많다. 그래서 "인프라를 어떻게 할까요?"라고 물어도 답할 수 없다. 반대로 이미 인프라를 만들어 둔 저장소도 있는데, 그게 앱에 맞는 구성이라는 보장은 없다. 예를 들어 SQLite로 동시 쓰기를 받고 있거나, 사내 도구 하나에 EKS와 Multi-AZ RDS를 붙여 둔 경우다.

이 도구는 그 사이를 메운다.

1. **사용자에게 묻지 않고 코드에서 현재 상태를 읽는다.** 어떤 프로세스가 돌고, 어떤 엔드포인트가 있고, 어떤 DB·캐시·큐·외부 서비스를 쓰고, 이미 어떤 배포 산출물이 있는지 본다.
2. **앱의 요구와 후보 구성 요소의 능력을 맞춰 보고 추천한다.** 요구는 동시 쓰기, 요청 처리 시간, 상태 보유, 데이터 중요도 같은 35개 차원이다. 후보는 Lambda, VM, 관리형 컨테이너, Kubernetes, PaaS 전부다.
3. **추천이 왜 그런지 설명할 수 있어야 한다.** "왜 Lambda가 아니고 이것인가"에 대해 비교표와 위반 근거, 그리고 그 근거의 공식 출처로 답한다.

## 2. 왜 이렇게 만들었나

| 결정 | 이유 |
|---|---|
| **판단은 규칙이, LLM은 추출·설명만 한다** | 같은 입력이면 같은 판정이 나와야 검증하고 설명할 수 있다. 결론이 모델의 감에 달려 있으면 팀원과 심사위원을 설득할 수 없다. |
| **상황을 나열하지 않고 "요구 차원 × 구성 요소 능력"으로 판정한다** | "결제가 있으면 X", "트래픽 폭증이면 Y" 같은 상황은 끝없이 늘어난다. 차원 35개와 능력 키라는 두 유한 목록, 그리고 그 사이의 비교 규칙만 두면 처음 보는 조합도 판정할 수 있다. |
| **모든 후보를 비교하고 지름길 규칙을 두지 않는다** | "서비스가 5개 이상이면 k8s" 같은 규칙은 근거가 없다. 탈락은 항상 "어떤 요구가 어떤 능력을 넘었나"로 설명한다. |
| **기존 인프라도 같은 기준으로 판정한다** | 이미 있다는 사실은 유지할 이유가 아니다. 유지·수정·교체 중 하나로 판정하고, 교체 비용은 반영하되 거부권으로 쓰지 않는다. |
| **필요한 만큼만, 비용을 거름망으로** | 재해 대비나 무중단 배포가 필요 없는 서비스도 많다. 요구보다 훨씬 큰 능력은 과잉으로 판정한다. 단, 금전·규제 데이터처럼 아끼면 안 되는 곳은 규칙에 명시한다. |
| **고정된 단계, 단계마다 고정된 JSON** | 단계는 S0 접수 → S1 인벤토리 → S2 프로필 → S3 적합성 → S4 추천 → S5 결정 대화 → S6 변경 → S7 정적 검증 → S8 동적 검증 → S9 결과다. 출력은 [schemas/infrafit.schema.json](schemas/infrafit.schema.json)으로 검증해야 다음 단계로 간다. |
| **모든 사실에 `파일:줄` 근거, 추측은 `candidate`** | 코드에서 확인한 사실과 추측을 구분해야 다음 단계가 추측을 확인하거나 사용자에게 드러낼 수 있다. |
| **탐지 지식은 코드가 아니라 `knowledge/` YAML에 둔다** | 시그니처, 이미지 분류, 배포 패턴, 기본값, 구성 요소 목록이 여기에 해당한다. 규칙과 근거를 코드와 분리해 리뷰·감사할 수 있게 한다. `infrafit kb lint`가 형식과 카탈로그 일관성을 검사한다. |

## 3. 판단 근거와 출처 정책

추천과 판정의 근거는 [docs/research/](docs/research/)의 조사 문서다(요구 차원, 구성 요소 능력, 고려 요소). 엔진은 이를 옮긴 [knowledge/](knowledge/)를 읽는다.

**출처는 "책임을 공식 자료로 넘길 수 있는가"를 기준으로 고른다.** 팀원과 심사위원이 모르는 출처는 설득력이 없으므로, 공식이어도 인정하지 않는다. 인용은 아래 두 조건을 **모두** 만족해야 쓸 수 있다.

1. **공식:** 그 주장의 대상을 소유한 주체가 직접 발행했다. 예를 들어 AWS 한도는 AWS 문서, nginx 동작은 nginx.org다. 다른 회사 제품을 설명하는 비교 글은 공식이 아니다.
2. **널리 알려진 발행 주체:** 아래 기준 중 하나에 해당한다.
   - 주요 클라우드(AWS, Google Cloud, Microsoft Azure), 표준 기구(IETF RFC, W3C, OWASP, PCI SSC), 정부 법령 사이트
   - [Stack Overflow 2025 개발자 설문](https://survey.stackoverflow.co/2025/technology) 기술 목록에 있는 기술(PostgreSQL, Redis, Docker, Kubernetes, Next.js, FastAPI, Spring Boot, Vercel, Supabase, Railway 등)
   - [CNCF](https://www.cncf.io/projects/) graduated·incubating 프로젝트(Kubernetes, Prometheus, Envoy, Argo, KEDA, cert-manager 등)
   - Apache 재단 최상위 프로젝트(Tomcat, Kafka 등)
   - 위 기준을 통과한 프레임워크의 공식 문서가 공식 실행 서버로 안내하는 도구(FastAPI의 uvicorn, Flask·Django의 gunicorn)
   - 예외: 감사 전에 주류 소프트웨어로 확인한 nginx, Grafana, Stripe도 인정한다([source-audit.md §10](docs/research/source-audit.md))

개인 블로그와 사이트(martinfowler.com, microservices.io 등), 커뮤니티 포럼, 뉴스, 비공식 미러, 덜 알려진 공급사(Render, Fly.io, Neon, Upstash, Koyeb 등), 12factor.net, MDN은 인정하지 않는다.

**감사 결과** (URL 4,377건, [source-audit.md](docs/research/source-audit.md)):

| 등급 | 건수 |
|---|---|
| 인정 | 3,588 |
| 부적격 | 704 |
| 출처가 아닌 URL(예시 주소 등) | 85 |

- **부적격 출처 주장 삭제:** 부적격 출처에만 기댄 주장은 설득력이 없으므로 조사 문서에서 지웠다(2026-10-02, [source-audit.md §11](docs/research/source-audit.md)). 표시가 붙은 줄 553개를 모두 지웠고, 그 결과 고려 요소 110개(878 → 768)와 능력 근거가 남지 않은 구성 요소 27개(226 → 199, 예: Render·Fly.io·Replit·Koyeb·Appwrite·Convex·Pinecone·Upstash·Caddy·Traefik·Fastly)가 빠졌다. 지운 ID와 절 이름은 각 파일 맨 위에 적었다.
- **근거 없음 표시:** 출처 없이 사실로 쓴 줄(추론 포함)에는 ` ⚠️근거없음`을 붙였다. 이런 줄은 판정 근거로 쓰지 않는다. 표시 말고 내용은 바꾸지 않았다.
- **유도 사실(정의상/유도):** 공식 문장이 값을 직접 말하지 않아도, 적격 인용 하나에서 한 단계로 이끌 수 있는 결론은 쓸 수 있다(2026-10-03 승인). 공급자 인용 값과 섞지 않고 `source.basis: derived`, 전제 인용(`from`), 이끈 이유(`reasoning`, 한 문장)로 따로 적는다. `infrafit kb lint`는 전제 인용이 조사 문서 줄에 있는지와 reasoning이 있는지를 검사한다. 판정 결과에서 이런 값을 쓴 위반·설정·통과 설명에는 "정의상/유도"와 reasoning이 붙는다. 목록: [post-response-work.md §4](docs/research/post-response-work.md).
- **기본값 표:** [knowledge/defaults.yaml](knowledge/defaults.yaml)에서 인용 문서에 그 내용이 없거나, 공식 문서끼리 값이 다르거나, 추론인 값은 뺐다. RDS `multi_az`, 백업 보존 기간, Spring Tomcat keep-alive가 여기에 해당한다.
- **구성 요소:** 능력 근거가 부적격인 구성 요소는 [knowledge/components/catalog.yaml](knowledge/components/catalog.yaml)에 `recommendable: false`와 이유를 달았다. 예를 들어 저장소가 Fly.io를 쓰고 있으면 그 사실은 현재 상태로 보고한다. 그러나 근거가 없으므로 추천 후보로는 쓰지 않는다.
- **남은 공백:** 출처 필드가 없는 시그니처·이미지 분류 가정은 감사 보고서 §8에 목록으로 남겼다.

## 4. 현재 구현 범위

| 단계 | 상태 |
|---|---|
| S0 접수 | 구현 |
| S1 인벤토리 | 구현 |
| S2~S9 | 설계 완료, 미구현 |

S1이 `inventory.json`에 기록하는 것:
- **워크로드:** web, worker, scheduled, static-frontend, migration-job, reverse-proxy. 출처는 k8s, compose, 코드, Dockerfile이고, 배치·CLI 진입점은 후보로 기록한다.
- **엔드포인트:** FastAPI, Flask(`add_url_rule` 포함), Django, Express·Fastify(플러그인 패턴), Next.js, Spring(Java·Kotlin), 웹소켓, 프레임워크 자동 라우트(후보). 환경별로 nginx 라우팅상 실제로 요청이 닿는지(`exposure`)도 기록한다.
- **데이터 저장소·캐시·큐·파일 저장소와 그 사용 주체**
- **외부 서비스:** LLM API, 인증, 결제, 웹훅 등. 사용 워크로드와 비밀값 환경변수 이름을 함께 기록한다.
- **환경:**
  - kustomize overlay, docker compose(override·변형 파일 병합)
  - 플랫폼 설정(vercel.json, render.yaml 등)
  - CI 배포 워크플로(Cloud Run, ECS, EC2/SSM 등). 환경별 compute를 따로 기록한다.
- **요청 경로:** `LB → nginx(다단 체인) → 앱 서버` 구간과 구간별 설정을 기록한다. 설정에는 근거 줄을 달고, 없으면 출처 있는 기본값을 쓴다.
- **기존 산출물:** Dockerfile, compose, k8s(kustomize 렌더 포함), Terraform, CI, 플랫폼 설정. 매핑하지 못한 의존성도 남긴다.
- **배포 단위(`deploy_units`):** 프로젝트가 정의한 "같이 떠야 하는 컨테이너 묶음"([다중 컨테이너 계약 §1](docs/superpowers/specs/2026-10-03-multi-container-contract.md)). 출처는 compose(기본 파일 + override) → k8s → 코드 순이다. 빌드마다 이미지 하나, 서비스 이름 그대로의 컨테이너, 저장소 컨테이너, 진입 컨테이너(entry)를 적는다. 비밀값([knowledge/secrets.yaml](knowledge/secrets.yaml))은 이름만 남기고, 정하지 못한 값은 `unresolved`에 적는다.

## 5. 검증 방법

- **테스트:** 362개. 전부 테스트 안에서 만든 합성 저장소로 규칙을 검증한다.
- **픽스처 6개와 골든 스냅샷:** 골든은 엔진 출력을 저장한 회귀 스냅샷이다. 기대값이 아니다. 정답을 미리 적어 두면 엔진이 실제로 동작하지 않고 그 값을 맞추는 쪽으로 만들어질 수 있어서, 픽스처의 기대 출력은 어디에도 기록하지 않는다.
- **실제 저장소 12개:** 코드와 결과를 대조하는 독립 감사로 틀린 사실을 찾아 고쳤다. 대상 스택은 Python, Node, Java·Kotlin(Spring), Next.js, 정적 사이트, 배치다.
- **결정성과 일관성 검사:** 같은 입력이면 `meta`를 뺀 출력이 바이트 단위로 같다. 단계 출력은 스키마 검증과 일관성 검사(참조 무결성, 근거 파일·줄 존재)를 통과해야 쓴다.

## 6. 사용법

```bash
uv sync
uv run infrafit analyze <로컬 경로 또는 GitHub URL> --out out --until S1
uv run infrafit check-run out/<run-id>      # 스키마·일관성 검사
uv run infrafit kb lint                      # 지식 베이스 형식 검사
uv run pytest                                # 테스트
uv run python scripts/update_golden.py       # 의도한 변경 뒤 골든 스냅샷 갱신
```

## 7. 한계와 다음 단계

- S2(요구 프로필), S3(적합성), S4(추천)가 다음 구현 대상이다. 조사 문서의 `⚠️` 표시 줄은 이 단계의 규칙 근거로 쓰지 않는다.
- 아는 S1 한계:
  - README에만 적힌 배포 명령은 읽지 않는다.
  - 내부 nginx server 블록을 `listen`·`server_name`으로 고르지 않는다.
  - compose `profiles`를 무시한다.
  - kustomize `namePrefix`가 붙으면 워크로드가 나뉜다.
  - 나머지는 판정 기록 문서에 있다.
