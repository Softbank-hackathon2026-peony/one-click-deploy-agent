# 보안·네트워크·신원·규제

infrafit 설계(§4)의 D/T/U/C 네 시나리오에는 보안 축이 없다. 이 문서는 **새 축 S(보안·규제)** 후보로, 앱 저장소의 코드·설정·IaC에서 읽어낼 수 있는 보안 고려 요소를 모은 카탈로그다. 비밀 노출, BaaS 권한(Supabase·Firebase), 신원·IAM, 네트워크 경계, 전송 구간, 인증·세션, 웹 앱 방어, 엣지 방어, 컨테이너·k8s, 공급망, 데이터 보호·감사, 한국·해외 규제, LLM 앱을 다룬다.
트래픽 확장(T), 장애·DR(D), 배포 파이프라인(U), 정합성(C), 일반 관측은 다른 문서가 맡는다. 겹치는 부분(레이트 리밋의 보안 측면, 비밀 관리·공급망)만 여기서 다룬다.
항목 ID `S-NNN`은 이 카탈로그의 요소 번호다. 설계 문서 §15의 출처 ID(S1~S28)와는 다르다. 출처 확인 날짜는 모두 2026-10-01이다.

## S 축 수준 정의 제안

| 수준 | 이름 | 언제 (필요 수준 조건 예) | 갖춰야 할 통제 (누적) |
|---|---|---|---|
| **L0** 위생 | 공개 콘텐츠만 | 로그인 없음, 사용자 입력 저장 없음, 개인정보 없음 (정적 사이트, 랜딩 페이지) | 커밋·번들에 비밀 없음, HTTPS, 디버그 모드 끔, lock 파일과 의존성 취약점 검사, 기본 보안 헤더 |
| **L1** 기본 | 계정과 일반 개인정보 | 로그인·회원가입이 있음, 이메일·닉네임 등 일반 개인정보 저장 (**기본값**) | L0 + 데이터 접근 제어(RLS·보안 규칙·서버 인가), 안전한 비밀번호 해시, 쿠키 속성, CSRF, 로그인 레이트 리밋, DB·버킷 비공개, 신뢰 프록시 설정, 저장 데이터 암호화, 로그에 PII 없음, 유출 신고 절차 |
| **L2** 강화 | 돈·조직·대량 사용자 | 결제 SDK(토큰화), B2B 신호(조직·팀·청구), 파일 업로드, 도구를 호출하는 LLM 기능, 또는 가정 사용자 수가 많음 | L1 + 워크로드 아이덴티티(정적 키 없음), 프라이빗 네트워크(DB 프라이빗 IP), WAF·봇 관리, 감사 로그 장기 보관, 이미지 스캔·non-root·PSS restricted, 최소 권한 IAM, 서비스 간 인증, 접속기록 보관 |
| **L3** 규제 | 규제 대상 데이터 | 카드 번호를 직접 받음, 의료·금융·주민등록번호 등 민감·고유식별정보, 공공기관 납품, ISMS-P 의무 대상 신호 | L2 + 규제 범위 분리(PCI DSS CDE 등), 고객 관리 키(KMS CMK), 서명 이미지 검증·SLSA, 데이터 레지던시 고정, 규제 인증(ISMS-P, 공공 클라우드 보안 검증) 대응, 정기 접근 권한 검토 |

수준은 누적이다. 다른 축과 마찬가지로 "필요 없음"(L0)도 정당한 답이고, L0 앱에 WAF·KMS CMK·Shield Advanced를 붙이면 과잉으로 지적한다. 단, **비밀 노출과 데이터 접근 제어 누락은 비용 필터로 깎지 않는다**(C 축의 결제 데이터처럼 아끼면 안 되는 곳).

## 목차

- A. 비밀·키 관리 (S-001 ~ S-008)
- B. BaaS·플랫폼 권한 (Supabase·Firebase·Vercel) (S-009 ~ S-018)
- C. 신원·IAM·워크로드 아이덴티티 (S-019 ~ S-024)
- D. 네트워크 경계 (S-025 ~ S-033)
- E. 전송 구간 암호화·인증서 (S-034 ~ S-038)
- F. 인증·세션 (S-039 ~ S-048)
- G. 웹 앱 방어 (S-049 ~ S-063)
- H. 엣지 방어 (WAF·봇·DDoS·프록시) (S-064 ~ S-069)
- I. 컨테이너·Kubernetes (S-070 ~ S-077)
- J. 공급망 (S-078 ~ S-084)
- K. 데이터 보호·감사 (S-085 ~ S-091)
- L. 규제 (한국·해외) (S-092 ~ S-100)
- M. LLM 앱 (S-101 ~ S-104)
- 새 축·규칙 후보

---

## A. 비밀·키 관리

### S-001 커밋된 비밀 (하드코딩된 키·비밀번호)
- **무엇/왜:** API 키, DB 비밀번호, JWT 서명 키가 소스나 git 이력에 들어 있으면 저장소를 읽을 수 있는 모든 사람(공개 저장소면 인터넷 전체)이 그 권한을 갖는다. git은 이력을 지우지 않으므로 파일을 지워도 남는다.
- **실패 양상:** 결제 키로 환불·조회, 클라우드 키로 자원 생성(채굴), DB 직접 접속으로 전체 데이터 유출. 노출 후에는 키를 폐기·교체하기 전까지 계속 유효하다.
- **신호:** 🟢 고엔트로피 문자열과 알려진 키 접두사(`sk_live_`, `AKIA`, `ghp_`, `xoxb-`, `-----BEGIN PRIVATE KEY-----`, `service_role` JWT), `.env`가 저장소에 있고 `.gitignore`에 없음, `docker-compose.yml`의 평문 `POSTGRES_PASSWORD`. 🟡 테스트용 더미인지 실제 키인지는 형식만으로 판단 불가. 🔴 이미 폐기됐는지는 코드로 알 수 없다.
- **시나리오·수준:** 모든 수준 (S L0부터)
- **처방:** 티어0: Vercel/Netlify 환경변수(민감 표시), 노출 키 즉시 폐기·재발급 / 티어1: Secret Manager·AWS Secrets Manager 참조로 주입 / 티어2: External Secrets 등으로 클라우드 비밀 저장소에서 k8s Secret 동기화. 공통: git 이력 정리보다 **키 교체가 먼저**.
- **검증:** gitleaks·trufflehog로 전체 이력 스캔(CI 게이트), GitHub secret scanning 알림 0건.
- **비용 영향:** 중립 (비밀 저장소 비용은 비밀당 소액)
- **출처:** https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html (하드코딩 금지, 커밋 전 탐지, 노출 키 즉시 폐기) · https://docs.github.com/en/code-security/secret-scanning/introduction/about-secret-scanning (전체 git 이력·모든 브랜치 스캔) · https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/ (SECRET_KEY를 소스 관리에 커밋하지 말 것)

### S-002 프론트엔드 번들에 들어간 서버 비밀 (`NEXT_PUBLIC_`·`VITE_` 접두사)
- **무엇/왜:** Next.js는 `NEXT_PUBLIC_` 접두사 변수를 빌드 시 JS 번들에 그대로 박아 넣고, Vite는 `VITE_` 변수를 클라이언트 코드에 노출한다. 바이브코더가 "브라우저에서 안 읽혀서" 접두사를 붙이는 순간 서버 키가 공개된다.
- **실패 양상:** 누구나 개발자 도구나 번들 파일에서 키를 읽는다. OpenAI·Stripe secret·Supabase service_role 키가 들어가면 과금 폭탄, 결제 조작, RLS 우회 전체 데이터 접근.
- **신호:** 🟢 `NEXT_PUBLIC_*`/`VITE_*`/`REACT_APP_*`/`EXPO_PUBLIC_*` 이름에 `SECRET`, `SERVICE_ROLE`, `PRIVATE`, `OPENAI`, `ANTHROPIC`, `STRIPE_SECRET`, `sk_` 값이 붙음. 🟢 `"use client"` 파일이나 `src/`(Vite)에서 `process.env.X`/`import.meta.env.X`로 비밀 이름 참조. 🟡 빌드 산출물(`.next/static`, `dist/`)이 저장소에 있으면 직접 grep.
- **시나리오·수준:** 모든 수준
- **처방:** 티어0: 호출을 Route Handler·Server Action·Edge Function으로 옮기고 접두사 없는 변수로 / 티어1·2: 백엔드 API 뒤로 이동. 공통: 노출된 키는 교체.
- **검증:** 빌드 후 `grep -r "sk_live_\|service_role" .next/static dist/` 0건. semgrep 규칙(접두사 + 비밀 키워드).
- **비용 영향:** 중립 (서버 경유 호출로 함수 실행 비용 소폭 증가)
- **출처:** https://nextjs.org/docs/app/guides/environment-variables ("inlined into any JavaScript sent to the browser") · https://vite.dev/guide/env-and-mode ("`VITE_*` variables should not contain sensitive information such as API keys")

### S-003 빌드 인자·이미지 레이어에 남은 비밀
- **무엇/왜:** Dockerfile의 `ARG`/`ENV`로 넘긴 비밀은 최종 이미지 메타데이터나 레이어에 남는다. 레지스트리에서 이미지를 받은 사람은 누구나 꺼낼 수 있다.
- **실패 양상:** 이미지가 공개 레지스트리나 넓은 권한의 레지스트리에 올라가면 비밀 유출. `docker history`로 확인 가능.
- **신호:** 🟢 `ARG .*(TOKEN|SECRET|PASSWORD|KEY)`, `ENV .*SECRET=`, `COPY .env`, `.dockerignore`에 `.env` 없음. 🟡 `npm config set //registry...:_authToken` 같은 RUN 줄.
- **시나리오·수준:** 모든 수준 (컨테이너를 쓰는 티어1·2)
- **처방:** 티어1·2: BuildKit `RUN --mount=type=secret`, `.dockerignore`에 `.env*` 추가, 런타임 주입으로 전환.
- **검증:** `docker history --no-trunc`와 trivy secret 스캔으로 이미지 검사.
- **비용 영향:** 중립
- **출처:** https://docs.docker.com/build/building/secrets/ (빌드 인자·환경변수는 최종 이미지에 남음, secret mount 사용) · https://trivy.dev/docs/latest/ (이미지 내 secret 스캔) ⚠️출처확인필요

### S-004 비밀 교체(로테이션) 불가 구조
- **무엇/왜:** 키가 코드 상수이거나 여러 서비스에 복사돼 있으면 유출 시 교체에 배포가 필요하고, 교체를 미루게 된다. 세션·JWT 서명 키는 이전 키를 잠깐 함께 허용하는 구조가 필요하다.
- **실패 양상:** 유출 후 교체까지 수 시간~수 일, 그동안 악용. 서명 키를 갑자기 바꾸면 전 사용자 로그아웃.
- **신호:** 🟢 같은 비밀 값이 여러 파일·서비스에 반복, `SECRET_KEY_FALLBACKS`(Django)나 키 ID(`kid`) 처리 없음. 🔴 실제 교체 주기는 코드에 없음 → "교체 절차 미확인" 가정.
- **시나리오·수준:** S L1 이상 (L2부터 자동 교체 권장)
- **처방:** 티어0: 플랫폼 통합 비밀 재발급 절차 문서화 / 티어1·2: Secrets Manager 자동 로테이션, 앱은 시작 시가 아니라 주기적으로 다시 읽기.
- **검증:** 스테이징에서 키 교체 리허설 후 오류율 확인.
- **비용 영향:** 소폭 증가 (로테이션 Lambda 등)
- **출처:** https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html (자동 로테이션, 빠른 폐기) · https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/ (`SECRET_KEY_FALLBACKS`로 교체)

### S-005 약하거나 기본값인 서명 키·세션 비밀
- **무엇/왜:** `secret`, `changeme`, 튜토리얼 예시 값 같은 짧은 HMAC 키는 오프라인 대입으로 풀린다. 풀리면 임의 사용자로 세션·JWT를 위조할 수 있다.
- **실패 양상:** 관리자 토큰 위조, 전체 계정 탈취.
- **신호:** 🟢 `jwt.sign(..., "secret")`, `SECRET_KEY = 'django-insecure-...'`, `session({secret: 'keyboard cat'})`, 32바이트 미만 리터럴. 🟡 env에서 읽지만 기본값 폴백(`process.env.JWT_SECRET || 'dev'`).
- **시나리오·수준:** S L1 이상
- **처방:** 공통: 32바이트 이상 난수를 비밀 저장소에, 기본값 폴백 제거(없으면 기동 실패).
- **검증:** semgrep(리터럴 서명 키, `||` 폴백), Django `check --deploy`.
- **비용 영향:** 중립
- **출처:** https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/ (SECRET_KEY는 큰 난수, 비공개) · https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_Cheat_Sheet.html (HMAC 비밀 강도, `none` 알고리즘 위험)

### S-006 CI·플랫폼 로그에 찍히는 비밀
- **무엇/왜:** `echo $DATABASE_URL`, 디버그용 `console.log(process.env)`, 빌드 로그에 비밀이 그대로 출력되면 로그를 볼 수 있는 모든 사람에게 노출된다.
- **실패 양상:** 공개 저장소의 Actions 로그, 외주 인력이 보는 플랫폼 로그에서 키 유출.
- **신호:** 🟢 `console.log(process.env)`, `print(os.environ)`, 워크플로의 `echo ${{ secrets.* }}`. 🟡 Vercel 비밀이 "민감"으로 표시됐는지는 대시보드 설정이라 🔴.
- **시나리오·수준:** 모든 수준
- **처방:** 티어0: Vercel 민감 환경변수(값 읽기 불가, 32자 이상은 빌드 로그에서 가림), 팀 정책으로 민감 강제 / 티어1·2: CI 마스킹, 로그 필터.
- **검증:** CI 로그 샘플 grep, semgrep 규칙.
- **비용 영향:** 중립
- **출처:** https://vercel.com/docs/environment-variables/sensitive-environment-variables (값 읽기 불가, 빌드 로그 `[REDACTED]`, 팀 정책) · https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html (토큰·키·연결 문자열 로그 제외)

### S-007 환경 간 비밀 공유 (dev = prod)
- **무엇/왜:** 개발·프리뷰·운영이 같은 DB 비밀번호와 API 키를 쓰면, 보안이 약한 개발 환경이나 프리뷰 배포가 뚫릴 때 운영 데이터가 바로 노출된다.
- **실패 양상:** 프리뷰 URL·개발자 노트북 유출이 운영 사고가 됨. 테스트 코드가 운영 데이터를 지움.
- **신호:** 🟢 `.env.development`와 `.env.production`에 같은 값, 하나의 `DATABASE_URL`만 존재. 🟡 overlay/환경별 Secret 이름이 같아도 값은 다를 수 있음(simple-web-app은 이름은 같고 값은 Terraform이 환경별로 만든다고 docs/deploy.md에 명시).
- **시나리오·수준:** S L1 이상
- **처방:** 티어0: Vercel 환경별(Production/Preview/Development) 변수 분리, 프리뷰는 별도 Supabase 프로젝트·브랜치 / 티어1·2: 환경별 계정·프로젝트·네임스페이스와 별도 비밀.
- **검증:** IaC에서 환경별 비밀 리소스가 다른지 확인.
- **비용 영향:** 증가 (별도 개발 DB 비용)
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### S-008 비밀 저장소 접근 권한 과다
- **무엇/왜:** 모든 서비스·사람이 모든 비밀을 읽을 수 있으면 한 곳만 뚫려도 전부 유출된다. k8s에서는 네임스페이스에 Pod를 만들 수 있는 사람이 그 네임스페이스 Secret을 모두 읽을 수 있다.
- **실패 양상:** 하나의 워크로드 침해 → 결제 키까지 탈취.
- **신호:** 🟢 IAM 정책 `secretsmanager:GetSecretValue` + `Resource: "*"`, k8s Role에 `secrets` `get/list` 와일드카드. 🟡 envFrom으로 Secret 전체를 모든 컨테이너에 주입.
- **시나리오·수준:** S L2 이상
- **처방:** 티어1: 서비스별 태스크 역할에 비밀 ARN 단위 권한 / 티어2: 서비스 계정별 Role, 필요한 키만 `secretKeyRef`.
- **검증:** IAM Access Analyzer 정책 검증, `kubectl auth can-i get secrets --as=system:serviceaccount:...`.
- **비용 영향:** 중립
- **출처:** https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html (비밀 접근에 최소 권한) · https://kubernetes.io/docs/concepts/configuration/secret/ (Pod 생성 권한자는 네임스페이스 Secret을 읽을 수 있음)

---

## B. BaaS·플랫폼 권한 (Supabase·Firebase·Vercel)

### S-009 Supabase 테이블 RLS 미설정
- **무엇/왜:** Supabase는 브라우저가 publishable(anon) 키로 PostgREST에 직접 질의한다. 노출된 스키마의 테이블에 RLS가 없으면 그 키를 가진 누구나 모든 행을 읽고 쓴다. 바이브코더 앱에서 가장 흔하고 피해가 큰 함정이다.
- **실패 양상:** 프로젝트 URL과 공개 키만으로 전체 사용자 테이블 조회·수정·삭제.
- **신호:** 🟢 `supabase/migrations/*.sql`에 `create table public.X`는 있는데 `alter table X enable row level security` 없음. 🟢 `create policy ... using (true)` (모두 허용). 🟡 마이그레이션 없이 대시보드로 만든 테이블은 저장소에 근거가 없음 → 🔴 "RLS 상태 미확인" 가정, Supabase Security Advisor 실행 권고.
- **시나리오·수준:** S L1 이상 (사용자 데이터가 있으면 무조건)
- **처방:** 티어0: 모든 public 테이블 RLS 활성화 + 작업별 정책(`auth.uid() = user_id`), anon·authenticated 기본 권한 회수 후 필요한 것만 부여.
- **검증:** Supabase Security Advisor `0013_rls_disabled_in_public` 0건, `supabase test db`로 정책 테스트(pgTAP).
- **비용 영향:** 중립
- **출처:** https://supabase.com/docs/guides/database/postgres/row-level-security ("A table in an exposed schema without RLS is readable and writable by any role with a grant on it") · https://supabase.com/docs/guides/database/database-advisors (`0013_rls_disabled_in_public`)

### S-010 Supabase secret(service_role) 키의 클라이언트 사용
- **무엇/왜:** secret(이전 이름 service_role) 키는 RLS를 완전히 우회하는 마스터 키다. 브라우저·모바일 앱·공개 저장소에 들어가면 RLS를 아무리 잘 써도 무의미하다.
- **실패 양상:** 전체 DB와 Storage 무제한 접근.
- **신호:** 🟢 클라이언트 코드에서 `createClient(url, SERVICE_ROLE_KEY)`, `NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY`, `sb_secret_` 접두사가 클라이언트 경로에 있음. 🟢 JWT payload `"role":"service_role"`이 저장소에 존재.
- **시나리오·수준:** 모든 수준
- **처방:** 티어0: secret 키는 Route Handler·Edge Function 등 서버에서만, 노출 시 키 재발급(Vercel 통합이면 통합 쪽에서 교체).
- **검증:** 번들 grep, semgrep(클라이언트 파일 + service role).
- **비용 영향:** 중립
- **출처:** https://supabase.com/docs/guides/api/api-keys (secret 키는 RLS를 우회, 브라우저·번들 금지)

### S-011 RLS 정책이 사용자 수정 가능 메타데이터를 신뢰
- **무엇/왜:** `auth.jwt() -> 'user_metadata'`는 사용자가 직접 바꿀 수 있다. 여기서 `role: admin`을 읽어 권한을 주면 누구나 관리자가 된다. `app_metadata`(raw_app_meta_data)는 서버만 쓸 수 있다.
- **실패 양상:** 일반 사용자가 메타데이터를 고쳐 관리자 정책 통과.
- **신호:** 🟢 정책 SQL에 `user_metadata`, `raw_user_meta_data` 참조.
- **시나리오·수준:** S L1 이상
- **처방:** 티어0: 역할은 `app_metadata`나 별도 테이블(`user_roles`)에서 읽기.
- **검증:** Security Advisor `0015_rls_references_user_metadata` 0건.
- **비용 영향:** 중립
- **출처:** https://supabase.com/docs/guides/database/database-advisors (`0015_rls_references_user_metadata`) · https://supabase.com/docs/guides/database/postgres/row-level-security (`auth.jwt()`는 raw_app_meta_data가 더 안전)

### S-012 SECURITY DEFINER 뷰·함수로 RLS 우회
- **무엇/왜:** Postgres 뷰와 `security definer` 함수는 만든 사람(보통 postgres) 권한으로 실행돼 RLS를 무시한다. 공개 스키마에 두면 anon이 우회 경로로 쓴다.
- **실패 양상:** 테이블 RLS는 막혀 있는데 뷰나 RPC를 통해 전체 데이터 노출.
- **신호:** 🟢 마이그레이션에 `create view public.` (security_invoker 없음), `security definer` 함수가 public 스키마에 있고 `grant execute ... to anon`.
- **시나리오·수준:** S L1 이상
- **처방:** 티어0: 뷰에 `with (security_invoker = true)`, definer 함수는 비공개 스키마로 옮기고 실행 권한 회수.
- **검증:** Security Advisor `0010_security_definer_view`, `0028/0029_security_definer_function_executable`.
- **비용 영향:** 중립
- **출처:** https://supabase.com/docs/guides/database/database-advisors

### S-013 Supabase Storage 공개 버킷·정책 누락
- **무엇/왜:** 공개 버킷은 접근 제어 없이 다운로드된다. 프로필 사진은 괜찮지만 신분증·계약서·영수증을 공개 버킷에 두면 URL만 알면 누구나 받는다.
- **실패 양상:** 경로 추측이나 링크 공유로 개인 서류 유출.
- **신호:** 🟢 `storage.createBucket(..., { public: true })`, 마이그레이션 `insert into storage.buckets ... public = true`. 🟡 버킷 이름(`documents`, `ids`, `receipts`)과 공개 여부 조합은 추론. ⚠️근거없음
- **시나리오·수준:** S L1 이상
- **처방:** 티어0: 민감 파일은 비공개 버킷 + `storage.objects` RLS + 짧은 만료 서명 URL.
- **검증:** 익명 세션으로 객체 URL 요청 시 401/403.
- **비용 영향:** 중립
- **출처:** https://supabase.com/docs/guides/storage/security/access-control ("Public buckets are already publicly accessible")

### S-014 Supabase DB 직접 연결: SSL 미강제·IP 제한 없음
- **무엇/왜:** Supabase Postgres는 인터넷에서 직접 접속 가능한 엔드포인트다. SSL 강제와 네트워크 제한(IP 허용 목록)은 선택 설정이며, 네트워크 제한은 PostgREST·Storage·Auth(HTTPS API)에는 적용되지 않는다.
- **실패 양상:** 유출된 DB 비밀번호로 어디서나 접속. 평문 연결 도청.
- **신호:** 🟢 `DATABASE_URL`에 `sslmode=disable` 또는 sslmode 없음. 🔴 SSL 강제·네트워크 제한 설정은 대시보드 → 미확인 가정.
- **시나리오·수준:** S L1 이상 (네트워크 제한은 L2)
- **처방:** 티어0: SSL 강제 켜기(빠른 재시작 발생), 클라이언트는 `verify-full`, 서버 고정 IP가 있으면 네트워크 제한.
- **검증:** `psql "sslmode=disable"` 접속 거부 확인.
- **비용 영향:** 중립 (고정 IP가 필요하면 증가)
- **출처:** https://supabase.com/docs/guides/platform/ssl-enforcement · https://supabase.com/docs/guides/platform/network-restrictions ("They don't apply to HTTPS APIs such as PostgREST, Storage, and Auth")

### S-015 Firebase 보안 규칙 allow all (테스트 모드 방치)
- **무엇/왜:** Firestore·Realtime Database·Storage의 `allow read, write: if true` 또는 기간 한정 테스트 모드 규칙이 운영에 남는 경우가 흔하다. Firebase API 키는 공개라 규칙이 유일한 방어선이다.
- **실패 양상:** 누구나 전체 DB를 읽고 덮어쓰거나 지움.
- **신호:** 🟢 `firestore.rules`/`database.rules.json`/`storage.rules`에 `if true`, `".read": true`, `request.time < timestamp.date(...)`. 🟢 `request.auth != null`만 있고 소유자 검사 없음(로그인한 아무나 남의 데이터 접근).
- **시나리오·수준:** S L1 이상
- **처방:** 티어0: 소유자 기반 규칙(`request.auth.uid == resource.data.author_uid`), 에뮬레이터로 규칙 테스트, 규칙을 저장소에서 배포(`firebase deploy --only firestore:rules`).
- **검증:** `@firebase/rules-unit-testing` 테스트, 콘솔 규칙 경고 확인.
- **비용 영향:** 중립
- **출처:** https://firebase.google.com/docs/rules/insecure-rules (open access는 누구나 DB를 덮어씀, content-owner 규칙 권장)

### S-016 Firebase Storage 업로드 규칙에 크기·형식 검사 없음
- **무엇/왜:** Storage 규칙은 `request.resource.size`와 `contentType`을 검사할 수 있다. 없으면 로그인 사용자가 대용량·실행 파일을 무제한 올린다.
- **실패 양상:** 저장·전송 비용 폭증, 악성 파일 배포 창구.
- **신호:** 🟢 `storage.rules`의 `allow write`에 `request.resource.size` 조건 없음.
- **시나리오·수준:** S L1 이상 (업로드 기능이 있으면)
- **처방:** 티어0: 규칙에 크기 상한과 `contentType.matches('image/.*')`.
- **검증:** 규칙 단위 테스트(6MB 업로드 거부).
- **비용 영향:** 감소 (남용 저장 비용 차단)
- **출처:** https://firebase.google.com/docs/storage/security

### S-017 BaaS 키 남용 방지 부재 (App Check·API 키 제한)
- **무엇/왜:** Firebase API 키는 비밀이 아니지만, 모든 API 키에 API 제한을 걸고 App Check로 "내 앱에서 온 요청"만 받아야 남용을 줄인다. Gemini API 키는 예외로 절대 코드에 넣으면 안 된다.
- **실패 양상:** 스크립트가 공개 키로 Auth·Firestore·Functions를 대량 호출 → 비용과 스팸 계정.
- **신호:** 🟢 `firebase/app-check` 미사용, `initializeAppCheck` 없음. 🟢 클라이언트 코드에 Gemini 키. 🔴 GCP 콘솔의 API 키 제한 → 미확인 가정.
- **시나리오·수준:** S L2 이상 (Gemini 키 노출은 모든 수준)
- **처방:** 티어0: App Check(웹은 reCAPTCHA Enterprise) 적용, API 키를 Firebase API로 제한, Gemini 호출은 서버(또는 Firebase AI Logic + App Check).
- **검증:** App Check 지표에서 미검증 요청 비율 확인 후 enforce.
- **비용 영향:** 소폭 증가 (reCAPTCHA Enterprise 평가 비용)
- **출처:** https://firebase.google.com/docs/projects/api-keys (Firebase 키는 비밀 아님, 모든 키에 API 제한, Gemini 키는 노출 금지) · https://firebase.google.com/docs/app-check

### S-018 프리뷰 배포 URL 공개
- **무엇/왜:** Vercel 등은 브랜치마다 프리뷰 URL을 만든다. 보호하지 않으면 미완성 기능, 디버그 엔드포인트, 운영 DB에 붙은 프리뷰가 인터넷에 열린다. 배포 보호는 Routing Middleware를 포함한 모든 요청에 인증을 요구한다.
- **실패 양상:** 프리뷰에서 인증 우회 기능이나 관리자 화면 노출, 프리뷰가 운영 데이터 변경.
- **신호:** 🔴 배포 보호 설정은 대시보드에 있음 → 기본 가정 "미확인". 🟡 `vercel.json` 존재 + 프리뷰 환경 변수가 운영 DB를 가리킴.
- **시나리오·수준:** S L1 이상
- **처방:** 티어0: Standard Protection + Vercel Authentication(추가 비용 없음), 프리뷰는 별도 DB. 운영 소스맵은 Protected Source Maps.
- **검증:** 로그인하지 않은 브라우저로 프리뷰 URL 접근 시 인증 화면.
- **비용 영향:** 중립 (비밀번호 보호는 Pro에서 프로젝트당 월 $20)
- **출처:** https://vercel.com/docs/deployment-protection

---

## C. 신원·IAM·워크로드 아이덴티티

### S-019 워크로드에 정적 클라우드 키 (IAM 사용자 키·서비스 계정 키 파일)
- **무엇/왜:** 컨테이너에 `AWS_ACCESS_KEY_ID`나 GCP 서비스 계정 JSON을 넣으면 만료 없는 키가 이미지·환경변수·로그로 퍼진다. AWS와 GCP 모두 워크로드에는 임시 자격 증명을 쓰라고 권한다.
- **실패 양상:** 키 유출 시 폐기 전까지 무기한 악용, 감사 로그에서 누가 썼는지 구분 어려움.
- **신호:** 🟢 env에 `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`, `GOOGLE_APPLICATION_CREDENTIALS=*.json`, 저장소의 `*-sa.json`/`"type": "service_account"`. 🟢 Terraform `aws_iam_access_key`, `google_service_account_key`.
- **시나리오·수준:** S L2 이상 (키 파일이 저장소에 있으면 모든 수준, S-001)
- **처방:** 티어1: ECS 태스크 역할 / Cloud Run 서비스 계정 연결 / 티어2: EKS Pod Identity(또는 IRSA), GKE Workload Identity Federation. GCP는 조직 정책으로 키 생성 비활성화.
- **검증:** 컨테이너 env에 키 변수 없음, `aws sts get-caller-identity`가 역할 ARN을 반환.
- **비용 영향:** 중립
- **출처:** https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html ("Require workloads to use temporary credentials with IAM roles") · https://docs.cloud.google.com/iam/docs/best-practices-for-managing-service-account-keys · https://docs.cloud.google.com/kubernetes-engine/docs/concepts/workload-identity · https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html

### S-020 과도한 IAM 권한 (`*:*`, AdministratorAccess)
- **무엇/왜:** 앱 역할에 관리자 권한을 주면 앱 취약점(SSRF, RCE)이 곧 계정 전체 장악이 된다. 최소 권한은 "작업에 필요한 동작만, 특정 자원에, 조건과 함께"다.
- **실패 양상:** 앱 하나 침해 → S3 전체 삭제, IAM 사용자 생성, 채굴 인스턴스.
- **신호:** 🟢 Terraform/정책 JSON의 `"Action": "*"`, `"Resource": "*"`, `AdministratorAccess`, `roles/owner`, `roles/editor` 부여.
- **시나리오·수준:** S L1 이상 (클라우드 자원을 쓰면)
- **처방:** 티어1·2: 서비스별 역할, 자원 ARN 지정, IAM Access Analyzer로 실제 사용 기반 정책 생성.
- **검증:** Access Analyzer 정책 검증, checkov/tfsec 와일드카드 규칙.
- **비용 영향:** 중립
- **출처:** https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html (least-privilege, Access Analyzer 정책 생성)

### S-021 워크로드 간 신원 분리 없음 (노드 역할 공유)
- **무엇/왜:** EKS에서 Pod별 역할 없이 노드 IAM 역할에 권한을 주면 같은 노드의 모든 Pod가 그 권한을 갖는다. IMDS가 막히지 않으면 Pod가 노드 역할 자격 증명까지 가져온다.
- **실패 양상:** 약한 사이드 서비스 침해 → 결제 서비스 권한 획득.
- **신호:** 🟢 노드 그룹 역할에 S3·SQS 등 앱 권한 부착, ServiceAccount에 역할 연결(어노테이션·Pod Identity association) 없음.
- **시나리오·수준:** S L2 이상, 티어2
- **처방:** 티어2: 서비스 계정별 Pod Identity, 노드 역할은 최소(ECR pull, CNI), IMDS 홉 제한 1(S-060).
- **검증:** Pod 안에서 노드 역할 자격 증명 획득 시도가 실패.
- **비용 영향:** 중립
- **출처:** https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html (자격 증명 격리, IMDS 미제한 시 노드 역할 접근 가능)

### S-022 사람 계정: 루트·장기 키·MFA 없음
- **무엇/왜:** 클라우드 콘솔에 루트나 MFA 없는 IAM 사용자로 들어가면 피싱 한 번에 계정 전체를 잃는다. 사람은 IdP 연동 임시 자격 증명과 피싱 내성 MFA를 쓴다.
- **실패 양상:** 계정 탈취 → 모든 자원 삭제·데이터 유출.
- **신호:** 🔴 코드에 거의 없음 → 가정 "MFA 미확인". 🟡 README의 `aws configure` + 개인 키 안내.
- **시나리오·수준:** S L1 이상
- **처방:** 공통: IAM Identity Center/Google Workspace SSO, 루트 MFA·사용 금지, Vercel·Supabase·GitHub 팀 계정 2FA 강제.
- **검증:** 클라우드 보안 점검(Security Hub, Security Command Center) 결과.
- **비용 영향:** 중립
- **출처:** https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html (federation, MFA, root 보호)

### S-023 CI에서 클라우드로 장기 키 사용 (OIDC 미사용)
- **무엇/왜:** GitHub Actions 비밀에 클라우드 액세스 키를 넣는 대신 OIDC로 짧은 토큰을 받으면 저장된 장기 비밀이 사라진다.
- **실패 양상:** 워크플로 침해·포크 PR·로그 노출로 배포 키 유출 → 운영 장악.
- **신호:** 🟢 워크플로에 `secrets.AWS_ACCESS_KEY_ID`, `credentials_json: ${{ secrets.GCP_SA_KEY }}`, `permissions: id-token: write` 없음.
- **시나리오·수준:** S L1 이상 (CI 배포가 있으면)
- **처방:** 티어1·2: `aws-actions/configure-aws-credentials` 역할 위임, GCP Workload Identity Federation, 신뢰 조건에 저장소·브랜치 고정.
- **검증:** 저장소 비밀 목록에 클라우드 키 없음.
- **비용 영향:** 중립
- **출처:** https://docs.github.com/en/actions/reference/security/secure-use (OIDC로 장기 비밀 대체)

### S-024 서비스 간 인증 없음 (내부망이면 안전하다는 가정)
- **무엇/왜:** 내부 API가 "클러스터 안에서만 부른다"는 이유로 인증 없이 열려 있으면, 한 Pod 침해나 SSRF로 내부 API를 마음대로 호출한다. 헤더(`X-User-Id`)로 사용자 신원을 넘길 때는 그 헤더를 프록시만 넣을 수 있어야 한다.
- **실패 양상:** 내부 관리 API 호출, 사용자 신원 헤더 위조로 타인 행세.
- **신호:** 🟢 백엔드가 `X-User-Id` 같은 헤더를 신뢰하는데 NetworkPolicy·mTLS·서명 토큰 없음. 🟢 simple-web-app은 nginx가 `proxy_set_header X-User-Id`로 덮어쓰고 NetworkPolicy로 `/internal/verify`를 nginx Pod에서만 닿게 함(충족 예). 🟡 Cloud Run 서비스 간 호출에 ID 토큰 사용 여부.
- **시나리오·수준:** S L2 이상
- **처방:** 티어1: Cloud Run 내부 서비스는 invoker IAM + ID 토큰, ECS는 Service Connect + SG 참조 / 티어2: NetworkPolicy + (필요 시) 서비스 메시 mTLS.
- **검증:** 다른 Pod에서 내부 엔드포인트 호출 시 차단, 위조 헤더로 요청 시 무시됨(P4 테스트).
- **비용 영향:** 중립 (메시 도입 시 증가)
- **출처:** https://kubernetes.io/docs/concepts/services-networking/network-policies/ · https://docs.cloud.google.com/run/docs/authenticating/public (invoker IAM 검사)

---

## D. 네트워크 경계

### S-025 퍼블릭 DB 엔드포인트
- **무엇/왜:** RDS `publicly_accessible = true`, Cloud SQL 공인 IP + `0.0.0.0/0` 승인 네트워크는 DB 포트를 인터넷에 연다. 비밀번호 하나가 유일한 방어가 된다.
- **실패 양상:** 무차별 대입, DB 엔진 취약점 직접 공격, 유출 비밀번호로 즉시 접속.
- **신호:** 🟢 Terraform `publicly_accessible = true`, `ipv4_enabled = true` + `authorized_networks { value = "0.0.0.0/0" }`, 보안 그룹 5432/3306 인바운드 `0.0.0.0/0`. 🟢 docker-compose `ports: "5432:5432"`(개발용이면 경고만).
- **시나리오·수준:** S L1 이상
- **처방:** 티어0: S-014 / 티어1: RDS 프라이빗 서브넷 + 앱 SG 참조, Cloud SQL 프라이빗 IP 또는 Auth Proxy / 티어2: 같음 + 클러스터 노드 SG만 허용.
- **검증:** 외부에서 `nc -z db-host 5432` 실패, checkov `CKV_AWS_17` 류 규칙.
- **비용 영향:** 중립 (프라이빗 연결에 NAT·VPC 커넥터 비용이 생길 수 있음)
- **출처:** https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html ("Hiding a DB instance in a VPC from the internet", Public access 옵션) · https://docs.cloud.google.com/sql/docs/postgres/configure-private-ip

### S-026 퍼블릭 S3/GCS 버킷
- **무엇/왜:** 버킷 정책 `Principal: "*"`, `allUsers` 바인딩, 공개 ACL은 객체를 인터넷에 공개한다. S3는 새 버킷이 기본 비공개지만 정책으로 열 수 있고, Block Public Access로 막는다. GCS는 public access prevention으로 막는다.
- **실패 양상:** 업로드 파일·백업·로그 대량 유출, 쓰기 공개면 악성 파일 호스팅.
- **신호:** 🟢 `aws_s3_bucket_public_access_block` 없음 또는 `false`, 정책 `"Principal": "*"`, `acl = "public-read"`, GCS `member = "allUsers"`, `public_access_prevention` 미설정.
- **시나리오·수준:** S L1 이상 (정적 웹 호스팅용 공개 버킷은 의도된 예외로 표시)
- **처방:** 티어1·2: 계정·버킷 수준 BPA 네 설정 모두 켜기, 공개가 필요하면 CloudFront OAC/Cloud CDN 뒤에, 사용자 파일은 서명 URL.
- **검증:** IAM Access Analyzer for S3 공개 버킷 0건, 익명 GET 403.
- **비용 영향:** 중립
- **출처:** https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html (네 설정 모두 켜기 권장, Security Hub S3.8) · https://docs.cloud.google.com/storage/docs/public-access-prevention

### S-027 프라이빗 서브넷 없이 앱·DB가 공인 IP
- **무엇/왜:** VPC를 만들 때 퍼블릭 서브넷만 쓰면 모든 인스턴스·태스크가 공인 IP를 갖는다. LB만 퍼블릭, 앱·DB는 프라이빗이 기본 구조다.
- **실패 양상:** SG 실수 한 번이 직접 노출로 이어짐.
- **신호:** 🟢 Terraform `map_public_ip_on_launch = true`인 서브넷에 앱·DB 배치, ECS `assign_public_ip = true`, DB 서브넷 그룹이 퍼블릭 서브넷.
- **시나리오·수준:** S L2 이상 (L1은 SG 최소화로 대체 가능)
- **처방:** 티어1: 퍼블릭(ALB)·프라이빗(태스크)·DB 서브넷 3계층 / 티어2: 프라이빗 노드 그룹, GKE 프라이빗 노드.
- **검증:** 앱·DB 리소스에 공인 IP 없음(describe 결과).
- **비용 영향:** 증가 (NAT Gateway 필요, COST-002와 연동)
- **출처:** https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html (웹 서버는 퍼블릭, DB는 프라이빗 서브넷) · https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html (LB → 웹 → DB SG 참조 예)

### S-028 보안 그룹·방화벽 `0.0.0.0/0` 관리 포트
- **무엇/왜:** SSH(22)·RDP(3389)·DB·Redis·k8s API를 전 인터넷에 열면 자동화된 스캔과 대입 공격 대상이 된다. AWS 예시도 LB만 `0.0.0.0/0`, 나머지는 SG 참조다.
- **실패 양상:** 서버 장악, Redis 무인증 접근으로 데이터 유출.
- **신호:** 🟢 `cidr_blocks = ["0.0.0.0/0"]` + `from_port` 22/3389/5432/6379/6443, GCP `source_ranges = ["0.0.0.0/0"]` + 같은 포트.
- **시나리오·수준:** S L1 이상
- **처방:** 티어1·2: SSM Session Manager/IAP 터널로 대체, 인바운드는 SG 참조로.
- **검증:** checkov/tfsec, 외부 포트 스캔.
- **비용 영향:** 중립
- **출처:** https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html (SG 참조 구조) · SSM·IAP 대체는 일반 원칙(출처 미확인) ⚠️근거없음

### S-029 k8s NetworkPolicy 없음 (Pod 간 전부 허용)
- **무엇/왜:** k8s Pod는 기본적으로 격리되지 않는다. 정책이 없으면 침해된 Pod가 DB·Redis·내부 API 어디든 닿는다. 정책을 써도 CNI가 지원하지 않으면 효과가 없다.
- **실패 양상:** 측면 이동, 내부 엔드포인트 직접 호출.
- **신호:** 🟢 매니페스트에 `NetworkPolicy` 없음. 🟢 simple-web-app `k8s/base/networkpolicy.yaml`은 앱 서비스 인그레스를 nginx·monitoring 네임스페이스로 제한(충족). 🟡 default-deny와 egress 정책은 없음(부분 충족). 🔴 CNI 정책 지원(GKE Dataplane V2, EKS VPC CNI 정책 기능)은 클러스터 설정.
- **시나리오·수준:** S L2 이상, 티어2
- **처방:** 티어2: 네임스페이스 default-deny ingress + 서비스별 허용, 민감 워크로드 egress 제한, CNI 정책 기능 켜기.
- **검증:** 임의 Pod에서 `curl` 차단 확인(k8s/tests 스모크에 추가).
- **비용 영향:** 중립
- **출처:** https://kubernetes.io/docs/concepts/services-networking/network-policies/ (기본 비격리, 플러그인 필요, default-deny 예)

### S-030 egress 무제한 (아웃바운드 통제 없음)
- **무엇/왜:** 앱이 어디로든 나갈 수 있으면 침해 시 데이터 반출, 채굴 풀 접속, SSRF 확장이 쉽다. L3에서는 아웃바운드를 알려진 목적지로 제한한다.
- **실패 양상:** 데이터 대량 반출이 탐지되지 않음.
- **신호:** 🟢 SG 기본 egress `0.0.0.0/0` 그대로, NetworkPolicy에 Egress 타입 없음. 🟡 외부 API 목록은 코드의 호스트 문자열로 추론 가능.
- **시나리오·수준:** S L3 (L2는 권장)
- **처방:** 티어1: SG egress를 VPC 엔드포인트·필요한 포트로 / 티어2: egress NetworkPolicy, 이그레스 게이트웨이·프록시.
- **검증:** 허용 목록 밖 도메인 접속 실패.
- **비용 영향:** 증가 (이그레스 프록시·방화벽 운영)
- **출처:** https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html (네트워크 계층에서 아웃바운드를 필요한 목적지로 제한) · https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html (기본 아웃바운드 전부 허용 규칙)

### S-031 LB를 우회하는 기본 URL·오리진 직접 접근
- **무엇/왜:** Cloud Run의 `run.app` 기본 URL, ALB 뒤 태스크의 공인 IP, CDN 뒤 오리진 도메인이 열려 있으면 WAF·Cloud Armor·레이트 리밋을 건너뛴다.
- **실패 양상:** WAF를 달아 놓고도 우회 경로로 공격 성공.
- **신호:** 🟢 Cloud Run `ingress = "all"` + LB·Cloud Armor 구성 동시 존재, `default_uri_disabled` 미설정. 🟡 오리진 도메인이 코드·문서에 노출.
- **시나리오·수준:** S L2 이상 (WAF를 쓸 때)
- **처방:** 티어1: Cloud Run ingress `internal-and-cloud-load-balancing` + 기본 URL 비활성화, ECS는 ALB SG에서만 인바운드 / 티어2: Ingress만 외부 노출.
- **검증:** 기본 URL 요청이 거부되는지 확인.
- **비용 영향:** 중립
- **출처:** https://docs.cloud.google.com/run/docs/securing/ingress ("The default run.app URL bypasses load balancers and security layers")

### S-032 Cloud Run·함수의 의도치 않은 공개 호출
- **무엇/왜:** 내부 워커·크론 대상 서비스에 `allUsers` invoker를 주거나 IAM 검사를 끄면 인터넷 누구나 호출한다.
- **실패 양상:** 내부 배치 엔드포인트 반복 호출로 비용·데이터 변경.
- **신호:** 🟢 `--allow-unauthenticated`, Terraform `member = "allUsers"` + `roles/run.invoker`가 워커·크론 서비스에 적용. 🟡 서비스 이름(`worker`, `cron`, `internal`)으로 내부용 추론. ⚠️근거없음
- **시나리오·수준:** S L1 이상
- **처방:** 티어1: 내부 서비스는 invoker IAM 유지 + Scheduler/Pub/Sub 서비스 계정에만 부여.
- **검증:** 익명 호출 403.
- **비용 영향:** 감소 (남용 호출 차단)
- **출처:** https://docs.cloud.google.com/run/docs/authenticating/public

### S-033 관리 도구·대시보드 인터넷 노출
- **무엇/왜:** Adminer·pgAdmin·Redis Commander·Grafana·Kubernetes Dashboard·Bull Board·Flower를 인증 없이 또는 기본 비밀번호로 공개 경로에 두는 경우.
- **실패 양상:** 데이터 열람·삭제, 큐 조작, 클러스터 장악.
- **신호:** 🟢 compose/k8s에 `adminer`, `dpage/pgadmin4`, `rediscommander`, `kubernetes-dashboard` 이미지 + 외부 포트·Ingress, Express에 `/admin/queues`(bull-board) 무인증 마운트, `GF_SECURITY_ADMIN_PASSWORD=admin`.
- **시나리오·수준:** S L1 이상
- **처방:** 티어1·2: 외부 노출 제거, IAP/VPN/포트포워딩으로만 접근. 앱 내 관리 화면은 S-047.
- **검증:** 외부에서 경로 접근 시 404/401.
- **비용 영향:** 중립
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

---

## E. 전송 구간 암호화·인증서

### S-034 HTTPS 미강제 (HTTP 리다이렉트 없음)
- **무엇/왜:** HTTP로도 응답하면 쿠키·토큰이 평문으로 오갈 수 있다. 쿠키에 `Secure`를 붙였다면 HTTP에서는 로그인이 깨진다(simple-web-app이 `COOKIE_SECURE=true`라서 HTTP를 301로 돌린다고 docs/deploy.md에 명시).
- **실패 양상:** 공용 와이파이 도청, 세션 탈취.
- **신호:** 🟢 Ingress에 `ssl-redirect`/`redirectToHttps` 없음, ALB 80 리스너가 forward. 🟢 simple-web-app은 AWS `alb.ingress.kubernetes.io/ssl-redirect`, GCP `FrontendConfig redirectToHttps` (충족). 🟡 티어0 플랫폼은 기본 HTTPS.
- **시나리오·수준:** 모든 수준
- **처방:** 티어0: 기본 제공 / 티어1: ALB 80→443 리다이렉트, Cloud Run 기본 HTTPS / 티어2: Ingress 리다이렉트 어노테이션.
- **검증:** `curl -I http://...` 301 + `Location: https://`.
- **비용 영향:** 중립
- **출처:** https://expressjs.com/en/advanced/best-practice-security.html (TLS 사용) · https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/ (HTTPS 후 SESSION/CSRF_COOKIE_SECURE) ⚠️출처확인필요

### S-035 HSTS 헤더 없음
- **무엇/왜:** HSTS는 브라우저가 이 도메인에 HTTP로 접속하지 않게 만든다. 첫 리다이렉트 순간의 다운그레이드를 막는다. `preload`는 되돌리기 어려우므로 신중히.
- **실패 양상:** SSL 스트리핑으로 첫 요청 가로채기.
- **신호:** 🟢 응답 헤더 설정(helmet, nginx `add_header Strict-Transport-Security`, `next.config.js headers()`, Django `SECURE_HSTS_SECONDS`)이 없음. 🟢 simple-web-app nginx 템플릿에 HSTS 없음(LB에서 넣는지 🔴 미확인).
- **시나리오·수준:** S L1 이상
- **처방:** 공통: `max-age=63072000; includeSubDomains`부터, preload는 모든 서브도메인 HTTPS 확인 후.
- **검증:** 응답 헤더 검사(P4 스모크).
- **비용 영향:** 중립
- **출처:** https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Strict_Transport_Security_Cheat_Sheet.html (권장 값, preload의 영구적 영향)

### S-036 인증서 수동 관리·자동 갱신 없음
- **무엇/왜:** 수동 발급 인증서는 만료로 서비스가 멈춘다. Let's Encrypt는 수명을 90일에서 단계적으로 45일(2028년 2월)까지 줄이고 있어 수동 갱신은 더 위험해진다.
- **실패 양상:** 인증서 만료 → 전 사용자 접속 불가(가용성 사고이자 보안 경고 무시 습관 유발).
- **신호:** 🟢 저장소의 `*.pem`/`*.crt` + nginx `ssl_certificate` 고정 경로, k8s `kubernetes.io/tls` Secret을 수동 생성. 🟢 cert-manager `Certificate`, GCP `ManagedCertificate`, ACM ARN 사용은 자동(충족).
- **시나리오·수준:** 모든 수준 (TLS를 직접 종단할 때)
- **처방:** 티어0: 플랫폼 자동 / 티어1: ACM, Google 관리형 인증서 / 티어2: cert-manager 또는 클라우드 관리형 인증서.
- **검증:** 만료 30일 전 알림, 인증서 만료일 모니터링.
- **비용 영향:** 중립 (ACM 공인 인증서는 LB 연동 시 무료로 알려져 있으나 이 문서에서는 미확인)
- **출처:** https://cert-manager.io/docs/ (만료 전 자동 갱신) · https://letsencrypt.org/2025/12/02/from-90-to-45/ ⚠️출처확인필요

### S-037 DB·캐시 연결 평문 (내부 TLS 없음)
- **무엇/왜:** VPC 안이라도 DB·Redis 연결을 TLS 없이 쓰면 같은 네트워크의 침해 지점에서 도청·변조가 가능하다. ElastiCache는 노드 기반 클러스터에서 전송 암호화를 명시적으로 켜야 하고, AUTH는 클라이언트 인증을 제공한다.
- **실패 양상:** 내부 스니핑으로 세션·개인정보 유출, Redis 무인증 접근.
- **신호:** 🟢 `redis://`(not `rediss://`), Terraform `transit_encryption_enabled` 없음/false, `auth_token` 없음, Postgres URL에 `sslmode=disable`.
- **시나리오·수준:** S L2 이상 (L3 필수)
- **처방:** 티어1·2: ElastiCache TLS + AUTH/RBAC, Memorystore 전송 암호화 + AUTH, RDS `rds.force_ssl`.
- **검증:** 평문 연결 시도 거부.
- **비용 영향:** 소폭 증가 (TLS 처리 오버헤드, 문서에 성능 영향 언급)
- **출처:** https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/in-transit-encryption.html (명시적 활성화, AUTH, 2026-04-28부터 TLS 1.2 최소)

### S-038 TLS 검증 끄기 (`rejectUnauthorized: false`, `verify=False`)
- **무엇/왜:** 개발 중 인증서 오류를 없애려고 검증을 끄고 운영에 그대로 두는 경우. 암호화는 되지만 상대가 누구인지 확인하지 않는다.
- **실패 양상:** 중간자 공격으로 결제·API 통신 가로채기.
- **신호:** 🟢 `rejectUnauthorized: false`, `NODE_TLS_REJECT_UNAUTHORIZED=0`, `requests.get(..., verify=False)`, `ssl: { rejectUnauthorized: false }`(pg), `sslmode=require`(검증 없음).
- **시나리오·수준:** 모든 수준
- **처방:** 공통: CA 번들 지정(RDS CA 등), `verify-full`.
- **검증:** semgrep 규칙.
- **비용 영향:** 중립
- **출처:** https://supabase.com/docs/guides/platform/ssl-enforcement (`verify-full` 권장) · 그 외 일반 원칙(출처 미확인) ⚠️근거없음

---

## F. 인증·세션

### S-039 세션 쿠키 속성 (Secure·HttpOnly·SameSite)
- **무엇/왜:** `Secure`는 HTTPS에서만, `HttpOnly`는 JS 접근 차단(XSS 시 세션 탈취 방지), `SameSite`는 교차 사이트 요청에 쿠키 동봉을 줄인다. `__Host-` 접두사는 HTTPS와 호스트에 묶는다.
- **실패 양상:** XSS 한 번에 세션 탈취, HTTP 노출, CSRF.
- **신호:** 🟢 `res.cookie(..., {httpOnly: false})` 또는 옵션 없음, `SESSION_COOKIE_SECURE = False`, `SameSite=None` + Secure 없음, `cookie_secure` 기본값 false. 🟢 simple-web-app auth `httponly=True, secure=settings.cookie_secure(기본 True), samesite="lax"` (충족). 🟡 토큰을 `localStorage`에 저장(S-046).
- **시나리오·수준:** S L1 이상
- **처방:** 공통: `HttpOnly; Secure; SameSite=Lax`(또는 Strict), 가능하면 `__Host-` 이름.
- **검증:** 로그인 응답의 `Set-Cookie` 검사(P4).
- **비용 영향:** 중립
- **출처:** https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html

### S-040 세션 고정·로그인 후 세션 ID 재발급 없음
- **무엇/왜:** 로그인 전후 세션 ID가 같으면 공격자가 미리 심은 ID로 피해자 세션을 공유한다. 로그인과 권한 상승 시 재발급해야 한다. 유휴·절대 만료도 필요하다.
- **실패 양상:** 세션 하이재킹, 로그아웃 안 되는 영구 세션.
- **신호:** 🟢 Express `req.session.regenerate` 없이 `req.session.user = ...`, Django는 `login()`이 자동 처리. 🟢 만료 설정(`maxAge`, `SESSION_COOKIE_AGE`) 없음 또는 매우 김. 🟡 로그아웃 시 서버 세션 삭제 여부.
- **시나리오·수준:** S L1 이상
- **처방:** 공통: 로그인 시 재발급, 유휴 만료 + 절대 만료, 서버 측 세션 무효화.
- **검증:** 로그인 전후 쿠키 값 비교 테스트.
- **비용 영향:** 중립
- **출처:** https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html (인증 후 재발급, 유휴 15~30분·절대 4~8시간 예)

### S-041 CSRF 방어 없음 (쿠키 인증 + 상태 변경 요청)
- **무엇/왜:** 쿠키로 인증하는 앱은 다른 사이트가 사용자의 브라우저로 요청을 보내게 만들 수 있다. 토큰, SameSite, Fetch Metadata(`Sec-Fetch-Site`), 커스텀 헤더 요구 중 하나 이상이 필요하다. Next.js Server Action은 Origin과 Host를 비교한다.
- **실패 양상:** 피해자 몰래 비밀번호 변경, 송금, 글 작성.
- **신호:** 🟢 Express에 csrf 미들웨어·Origin 검사 없음 + 쿠키 세션 + POST 라우트, Django `@csrf_exempt` 남용, `CSRF_TRUSTED_ORIGINS = ['*']`. 🟡 SameSite=Lax만 있으면 부분 충족.
- **시나리오·수준:** S L1 이상
- **처방:** 공통: 프레임워크 내장 CSRF, 또는 `Sec-Fetch-Site`/Origin 검사 + SameSite. 리버스 프록시 뒤 Next.js는 `serverActions.allowedOrigins` 확인.
- **검증:** 다른 Origin에서 POST 시 403 테스트.
- **비용 영향:** 중립
- **출처:** https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html · https://nextjs.org/docs/app/guides/data-security (Server Action Origin/Host 비교, allowedOrigins)

### S-042 약한 비밀번호 해시 (평문, MD5/SHA-256 단일, 낮은 파라미터)
- **무엇/왜:** 비밀번호는 느린 전용 해시로 저장해야 한다. OWASP 권장: Argon2id(최소 19MiB, 반복 2, 병렬 1), bcrypt는 work factor 10 이상·72바이트 제한, PBKDF2-HMAC-SHA256은 600,000회 이상. 한국 개인정보 안전성 확보조치 기준도 비밀번호 일방향 암호화를 요구한다.
- **실패 양상:** DB 유출 시 대부분의 비밀번호가 빠르게 복원되고, 다른 서비스로 크리덴셜 스터핑이 이어진다.
- **신호:** 🟢 `crypto.createHash('sha256').update(password)`, `hashlib.md5(password`, `bcrypt.hash(pw, 4)`, 평문 `password` 컬럼에 그대로 저장. 🟢 simple-web-app은 argon2(argon2-cffi 기본 파라미터)(충족). 🟡 bcrypt 72바이트 초과 입력 처리.
- **시나리오·수준:** S L1 이상 (자체 로그인이 있으면)
- **처방:** 공통: Argon2id 또는 bcrypt(cost ≥ 10), 로그인 시 재해시로 점진 업그레이드. 해시는 CPU를 많이 써 T 축 격리(T-CTL-008)와 함께 판단.
- **검증:** semgrep(약한 해시 함수 + password 변수), 단위 테스트로 파라미터 확인.
- **비용 영향:** 증가 (로그인당 CPU·메모리, 격리 워크로드 비용)
- **출처:** https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html · https://www.law.go.kr/행정규칙/개인정보의안전성확보조치기준 (제7조 암호화 — 조문 제목 수준만 확인)

### S-043 로그인 무차별 대입·크리덴셜 스터핑 방어 없음
- **무엇/왜:** 로그인·비밀번호 재설정·OTP 검증·계정 삭제(비밀번호 재확인) 경로에 IP 기준과 계정 기준 제한이 없으면 대입 공격과 유출 비밀번호 대입이 무제한이다. MFA가 가장 효과적이고, 레이트 리밋·CAPTCHA·유출 비밀번호 차단이 보조한다.
- **실패 양상:** 대량 계정 탈취, argon2 해시로 CPU 포화(가용성까지 영향).
- **신호:** 🟢 `/login`, `/signin`, `/auth/*` 라우트에 rate limiter(`express-rate-limit`, `slowapi`, nginx `limit_req`) 없음. 🟢 simple-web-app은 nginx `auth_login`·`auth_sensitive` 존(IP 기준)과 auth 서비스 `login_limiter.py`(충족 신호). 🟡 Supabase/Firebase Auth는 플랫폼 레이트 리밋이 있으나 서버에서 대리 호출하면 서버 IP로 묶임.
- **시나리오·수준:** S L1 이상 (T 축 T-CTL-007과 겹치며 보안 측면은 여기)
- **처방:** 티어0: Supabase Auth 레이트 리밋 조정, 서버 대리 호출 시 `Sb-Forwarded-For` 전달, CAPTCHA 켜기 / 티어1·2: 엣지·앱 이중 제한(IP + 계정), 실패 누적 시 지연·CAPTCHA, 유출 비밀번호 검사.
- **검증:** 같은 계정으로 N회 실패 후 429·지연 확인(P4).
- **비용 영향:** 중립 (WAF 봇 기능을 쓰면 증가)
- **출처:** https://cheatsheetseries.owasp.org/cheatsheets/Credential_Stuffing_Prevention_Cheat_Sheet.html · https://supabase.com/docs/guides/auth/rate-limits · https://expressjs.com/en/advanced/best-practice-security.html (로그인 브루트포스 방지) ⚠️출처확인필요

### S-044 계정 열거 (가입·로그인·재설정 응답 차이)
- **무엇/왜:** "존재하지 않는 이메일"과 "비밀번호 틀림"을 다르게 응답하면 유효 계정 목록을 만들 수 있고, 스터핑·피싱 정확도가 올라간다.
- **실패 양상:** 사용자 목록 수집, 표적 공격.
- **신호:** 🟢 응답 문자열 `"User not found"` vs `"Wrong password"`, 재설정 API가 미가입 이메일에 404. 🟡 응답 시간 차이는 코드로 판단 어려움.
- **시나리오·수준:** S L1 이상
- **처방:** 공통: 동일한 일반 메시지와 상태 코드.
- **검증:** 존재·비존재 계정 응답 비교 테스트.
- **비용 영향:** 중립
- **출처:** https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html

### S-045 MFA 없음 (관리자·B2B)
- **무엇/왜:** 관리자 계정과 B2B 조직 관리자는 탈취 시 피해가 크다. OWASP는 MFA를 가장 강한 방어로 든다.
- **실패 양상:** 관리자 계정 하나로 전체 데이터 접근.
- **신호:** 🟢 관리자 역할이 있는데 TOTP/WebAuthn 라이브러리·Supabase MFA(`mfa.enroll`)·Firebase MFA 사용 없음. 🔴 IdP 설정은 미확인.
- **시나리오·수준:** S L2 이상 (관리자 MFA), S L3 전 사용자 선택 제공
- **처방:** 티어0: Supabase Auth MFA, Firebase Auth MFA, Clerk 등 / 티어1·2: IdP 연동.
- **검증:** 관리자 로그인 시 2단계 요구 테스트.
- **비용 영향:** 소폭 증가 (SMS MFA는 건당 비용)
- **출처:** https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html

### S-046 JWT 오용 (`none`·검증 생략·localStorage·긴 만료)
- **무엇/왜:** `jwt.decode`로 검증 없이 읽기, 알고리즘 미고정, 만료 없는 토큰, 폐기 불가 구조. 브라우저 `localStorage` 저장은 XSS 한 번에 토큰이 넘어간다.
- **실패 양상:** 토큰 위조·재사용, 로그아웃·권한 회수 불가.
- **신호:** 🟢 `jwt.decode(` 결과로 인가, `algorithms` 인자 없음, `expiresIn` 없음 또는 `'365d'`, `localStorage.setItem('token'`.
- **시나리오·수준:** S L1 이상
- **처방:** 공통: `jwt.verify` + 알고리즘 고정, 짧은 액세스 토큰 + 갱신 토큰(HttpOnly 쿠키), 폐기 목록이 필요하면 서버 세션 고려.
- **검증:** semgrep(`jwt.decode` 후 인가 사용), `alg: none` 토큰 거부 테스트.
- **비용 영향:** 중립
- **출처:** https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_Cheat_Sheet.html (`none` 알고리즘, HMAC 비밀, 폐기 어려움) · 저장 위치 권고는 일반 원칙(출처 미확인) ⚠️근거없음

### S-047 관리자 페이지·관리 API 노출 (인가 누락)
- **무엇/왜:** `/admin` 화면은 숨기거나 UI에서 리다이렉트할 뿐 API·Server Action에 권한 검사가 없는 경우가 흔하다. Next.js는 페이지 수준 인증이 그 안의 Server Action으로 이어지지 않는다고 명시한다.
- **실패 양상:** 일반 사용자나 익명이 관리 API를 직접 호출해 데이터 삭제·권한 변경.
- **신호:** 🟢 `app/admin/**`, `/api/admin/*`, Django `admin/` 기본 경로 공개, Server Action·Route Handler에 `auth()`/역할 검사 없음, 클라이언트 측 `if (user.isAdmin)`만 존재. 🟡 미들웨어에만 의존(S-061).
- **시나리오·수준:** S L1 이상
- **처방:** 공통: 서버 측 데이터 접근 계층에서 인증 + 인가, 관리 경로는 IP 제한·IAP·별도 도메인 고려.
- **검증:** 일반 사용자 세션으로 관리 API 호출 시 403 테스트.
- **비용 영향:** 중립
- **출처:** https://nextjs.org/docs/app/guides/data-security ("A page-level authentication check does not extend to the Server Actions defined within it")

### S-048 OAuth 리다이렉트 URI·state 검증 미흡
- **무엇/왜:** 소셜 로그인 콜백에서 `state` 검증이 없거나 리다이렉트 허용 목록이 와일드카드면 로그인 CSRF와 토큰 탈취가 가능하다. Supabase·Firebase의 허용 리다이렉트 URL에 `*`를 넣는 경우가 흔하다.
- **실패 양상:** 공격자 계정으로 로그인시키기, 인가 코드 유출.
- **신호:** 🟢 `supabase/config.toml`의 `additional_redirect_urls`에 와일드카드, 자체 구현 OAuth에서 `state` 미검증. 🔴 대시보드 설정은 미확인.
- **시나리오·수준:** S L1 이상 (소셜 로그인이 있으면)
- **처방:** 공통: 정확한 리다이렉트 URL 목록, 검증된 라이브러리(Auth.js, Supabase Auth) 사용.
- **검증:** 허용되지 않은 redirect_to로 로그인 시 거부.
- **비용 영향:** 중립
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

---

## G. 웹 앱 방어

### S-049 CORS 오설정 (임의 Origin 반사 + credentials)
- **무엇/왜:** 브라우저는 credentials 요청에 `Access-Control-Allow-Origin: *`를 막지만, 서버가 요청 Origin을 그대로 반사하고 `Allow-Credentials: true`를 주면 아무 사이트나 로그인 사용자의 데이터를 읽는다.
- **실패 양상:** 악성 사이트 방문만으로 개인정보 API 응답 탈취.
- **신호:** 🟢 `cors({ origin: true, credentials: true })`, `origin: (o, cb) => cb(null, true)`, FastAPI `allow_origins=["*"], allow_credentials=True`, Django `CORS_ALLOW_ALL_ORIGINS = True` + credentials, 정규식 `.*example.com`(접미사 미고정).
- **시나리오·수준:** S L1 이상
- **처방:** 공통: 정확한 Origin 허용 목록, 같은 도메인 구조면 CORS 자체를 끄기.
- **검증:** `Origin: https://evil.example` 요청 시 ACAO 헤더 없음.
- **비용 영향:** 중립
- **출처:** https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS (credentials 요청에 와일드카드 금지) ⚠️출처부적격

### S-050 보안 헤더 없음 (CSP·frame-ancestors·nosniff)
- **무엇/왜:** CSP는 XSS 피해를 줄이고, `frame-ancestors`는 클릭재킹을 막는다(X-Frame-Options 대체). Express는 helmet으로 한 번에 설정한다.
- **실패 양상:** XSS가 곧 계정 탈취, 투명 iframe 클릭 유도.
- **신호:** 🟢 helmet 미사용, `next.config.js`에 `headers()` 없음, nginx `add_header Content-Security-Policy` 없음, `x-powered-by` 노출.
- **시나리오·수준:** S L1 이상 (CSP 엄격 모드는 L2)
- **처방:** 티어0: `next.config.js` headers / Vercel `vercel.json` headers / 티어1·2: 앱 미들웨어 또는 nginx·LB 응답 헤더.
- **검증:** 응답 헤더 검사, CSP report-only 단계 후 강제.
- **비용 영향:** 중립
- **출처:** https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html · https://expressjs.com/en/advanced/best-practice-security.html (helmet, x-powered-by 끄기) ⚠️출처확인필요

### S-051 운영 디버그 모드 (Django `DEBUG=True`, Flask debug, Werkzeug 디버거)
- **무엇/왜:** Django DEBUG는 소스 일부, 지역 변수, 설정을 오류 페이지에 노출한다. Flask/Werkzeug 디버거는 브라우저에서 임의 Python 코드 실행을 허용한다(PIN은 보안 장치가 아님).
- **실패 양상:** 비밀 설정 노출, 원격 코드 실행.
- **신호:** 🟢 `DEBUG = True`(env 분기 없음), `app.run(debug=True)`, `FLASK_DEBUG=1`, `flask run --debug`가 Dockerfile CMD, `uvicorn --reload`가 운영 CMD, `NODE_ENV` 미설정으로 Express 개발 모드.
- **시나리오·수준:** 모든 수준
- **처방:** 공통: 운영 설정 분리, gunicorn/uvicorn 프로덕션 실행, Django `check --deploy` CI 게이트.
- **검증:** 존재하지 않는 경로·오류 유발 시 일반 오류 페이지.
- **비용 영향:** 중립
- **출처:** https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/ · https://flask.palletsprojects.com/en/stable/debugging/

### S-052 에러 응답에 스택 트레이스·내부 정보
- **무엇/왜:** 예외 메시지, SQL, 파일 경로, 라이브러리 버전이 응답에 나가면 공격 정찰 자료가 된다. 전역 오류 처리기로 일반 메시지만 보내고 상세는 서버 로그에.
- **실패 양상:** 스키마·내부 호스트 노출, 취약 버전 식별.
- **신호:** 🟢 `res.status(500).json({ error: err.stack })`, `res.send(err.message)`, FastAPI `detail=str(e)`, Next.js API에서 `error.toString()` 반환. 🟢 simple-web-app은 nginx가 5xx를 고정 JSON으로 치환(충족 신호).
- **시나리오·수준:** S L1 이상
- **처방:** 공통: 전역 오류 처리기, 요청 ID만 반환(simple-web-app의 `X-Request-ID` 패턴).
- **검증:** 오류 유발 테스트에서 응답 본문에 스택 없음.
- **비용 영향:** 중립
- **출처:** https://cheatsheetseries.owasp.org/cheatsheets/Error_Handling_Cheat_Sheet.html

### S-053 API 문서·스키마 운영 노출 (`/docs`, `/openapi.json`, GraphQL introspection)
- **무엇/왜:** FastAPI는 기본으로 `/docs`, `/redoc`, `/openapi.json`을 연다. 내부 전용 엔드포인트까지 지도처럼 공개되고, Swagger UI에서 바로 호출된다.
- **실패 양상:** 숨겨진 관리 API 발견·호출.
- **신호:** 🟢 `FastAPI()` 생성자에 `docs_url=None`/`openapi_url=None` 없음, Apollo `introspection: true` 운영, `swagger-ui-express` 무조건 마운트.
- **시나리오·수준:** S L1 이상 (공개 API 제품이면 의도된 공개로 표시)
- **처방:** 공통: 운영에서 끄거나 인증 뒤로. simple-web-app처럼 엣지에서 내부 경로 404 처리.
- **검증:** 운영 URL `/docs` 404.
- **비용 영향:** 중립
- **출처:** https://fastapi.tiangolo.com/tutorial/metadata/ (`docs_url=None`, `openapi_url=None`)

### S-054 IDOR (객체 소유권 확인 없음)
- **무엇/왜:** `/api/orders/123`에서 로그인만 확인하고 주문 주인인지 확인하지 않으면 ID만 바꿔 남의 데이터를 본다. Supabase의 RLS 누락(S-009)과 같은 문제의 서버 버전.
- **실패 양상:** 전 사용자 주문·메시지·파일 열람·수정.
- **신호:** 🟢 `findUnique({ where: { id: params.id } })` 후 `userId` 비교 없음, `Model.objects.get(pk=pk)`에 사용자 필터 없음. 🟡 순차 정수 ID는 위험을 키움.
- **시나리오·수준:** S L1 이상
- **처방:** 공통: 쿼리에 소유자 조건(`where: { id, ownerId: session.user.id }`), 데이터 접근 계층에서 일괄 강제.
- **검증:** 두 사용자 계정으로 교차 접근 테스트(P4 자동화 가능).
- **비용 영향:** 중립
- **출처:** https://cheatsheetseries.owasp.org/cheatsheets/Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet.html · https://nextjs.org/docs/app/guides/data-security (IDOR 예시)

### S-055 대량 할당 (Mass assignment)
- **무엇/왜:** 요청 본문 전체를 모델에 넣으면(`update({ data: req.body })`) 사용자가 `role`, `isAdmin`, `credits`, `price`를 함께 보내 바꾼다.
- **실패 양상:** 권한 상승, 잔액·가격 조작.
- **신호:** 🟢 `prisma.user.update({ data: req.body })`, `Object.assign(user, req.body)`, Supabase `update(body)` + RLS에 컬럼 제한 없음, Django `fields = '__all__'` ModelForm/Serializer.
- **시나리오·수준:** S L1 이상
- **처방:** 공통: 허용 필드 목록 또는 DTO(zod/pydantic 스키마로 파싱 후 필요한 필드만).
- **검증:** 추가 필드 포함 요청 시 무시·거부 테스트.
- **비용 영향:** 중립
- **출처:** https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html

### S-056 서버 컴포넌트·액션이 과다한 데이터를 클라이언트로 전달
- **무엇/왜:** Next.js에서 DB 행 전체를 Client Component props나 Server Action 반환값으로 넘기면 해시된 비밀번호, 이메일, 내부 필드가 HTML/RSC 페이로드에 실린다.
- **실패 양상:** 페이지 소스에서 다른 사용자의 개인정보·내부 필드 노출.
- **신호:** 🟢 `"use client"` 컴포넌트 props 타입이 DB 모델 전체(`user: User`), Server Action이 `return db.user.update(...)` 결과 그대로 반환, `server-only` 미사용.
- **시나리오·수준:** S L1 이상
- **처방:** 티어0(Next.js): 데이터 접근 계층 + DTO, `import 'server-only'`, 필요 시 React taint API.
- **검증:** 렌더링된 페이지·RSC 응답에서 민감 필드 grep.
- **비용 영향:** 중립
- **출처:** https://nextjs.org/docs/app/guides/data-security

### S-057 오픈 리다이렉트
- **무엇/왜:** `?next=`, `?redirect=`, `?returnTo=` 값을 검증 없이 리다이렉트하면 정상 도메인 링크로 피싱 사이트에 보낸다. OAuth 흐름과 결합하면 토큰 유출로 커진다.
- **실패 양상:** 신뢰받는 도메인을 이용한 피싱, 로그인 후 악성 사이트 이동.
- **신호:** 🟢 `res.redirect(req.query.next)`, `redirect(searchParams.get('redirect'))`, `return RedirectResponse(request.query_params['next'])`.
- **시나리오·수준:** S L1 이상
- **처방:** 공통: 상대 경로만 허용(`/`로 시작하고 `//` 아님) 또는 허용 목록 매핑.
- **검증:** `?next=https://evil.example` 요청 시 내부 기본 경로로 이동.
- **비용 영향:** 중립
- **출처:** https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html

### S-058 파일 업로드 검증 없음
- **무엇/왜:** 확장자 허용 목록, 시그니처 검사(Content-Type은 위조 가능), 서버 생성 파일명, 크기 제한, 웹 루트 밖·별도 스토리지 저장, 필요 시 악성코드 스캔이 필요하다.
- **실패 양상:** 웹셸 업로드 후 실행, 경로 조작으로 파일 덮어쓰기, HTML·SVG 업로드로 저장형 XSS, 디스크·비용 고갈.
- **신호:** 🟢 `multer({ dest: 'public/uploads' })`, `file.originalname`으로 저장, `limits` 없음, `UploadFile` 저장 시 확장자 검사 없음, SVG 허용 + 같은 오리진 서빙. 🟢 simple-web-app nginx `client_max_body_size 64k`(크기 제한 신호).
- **시나리오·수준:** S L2 (업로드 기능이 있으면 L2 조건)
- **처방:** 티어0: Supabase/Firebase Storage 규칙으로 크기·형식 제한, 서명 업로드 URL / 티어1·2: S3/GCS 직접 업로드 + 별도 도메인으로 서빙 + 비동기 스캔.
- **검증:** 금지 형식·대용량·경로 문자 파일 업로드 테스트.
- **비용 영향:** 증가 (스캔 사용 시)
- **출처:** https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html

### S-059 SSRF (사용자 URL을 서버가 가져옴)
- **무엇/왜:** 링크 미리보기, 이미지 URL 가져오기, 웹훅 테스트, LLM의 웹 읽기 도구는 사용자가 준 URL로 서버가 요청한다. 내부망·메타데이터 엔드포인트(169.254.169.254)·localhost로 향하게 할 수 있다.
- **실패 양상:** 클라우드 자격 증명 탈취, 내부 관리 API 호출.
- **신호:** 🟢 `fetch(req.body.url)`, `axios.get(userUrl)`, `requests.get(url)`에서 url이 요청 값, 리다이렉트 따라가기 기본값. 🟡 LLM 도구로 URL 열기(S-103).
- **시나리오·수준:** S L1 이상 (해당 기능이 있으면)
- **처방:** 공통: 허용 목록, 해석된 IP가 사설·링크로컬·루프백이면 거부(DNS 재바인딩 고려), 리다이렉트 끄기, 아웃바운드 제한(S-030), IMDSv2(S-060).
- **검증:** `http://169.254.169.254/`, `http://localhost:...` 입력 시 거부 테스트.
- **비용 영향:** 중립
- **출처:** https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html

### S-060 IMDSv1 허용·홉 제한 미설정
- **무엇/왜:** EC2 IMDSv2는 PUT으로 세션 토큰을 받아야 하고 `X-Forwarded-For`가 있는 PUT을 거부해 SSRF·오픈 프록시를 통한 자격 증명 탈취를 막는다. 응답 홉 제한 기본 1은 컨테이너에서 노드 메타데이터 접근을 막는 데 쓰인다.
- **실패 양상:** SSRF 한 줄로 인스턴스·노드 역할 자격 증명 유출.
- **신호:** 🟢 Terraform `metadata_options { http_tokens = "optional" }` 또는 블록 없음, 시작 템플릿 `http_put_response_hop_limit > 1`(EKS 노드).
- **시나리오·수준:** S L1 이상 (EC2·EKS 노드가 있으면)
- **처방:** 티어2(EKS EC2 노드)·EC2: `http_tokens = "required"`, Pod Identity를 쓰면 홉 제한 1로 Pod의 노드 IMDS 접근 차단.
- **검증:** IMDSv1 요청이 401, Pod에서 노드 IMDS 접근 실패.
- **비용 영향:** 중립
- **출처:** https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html · https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html

### S-061 미들웨어에만 의존한 인가 (Next.js middleware 우회 CVE)
- **무엇/왜:** Next.js 미들웨어만으로 인증을 걸면 미들웨어가 우회될 때 전부 뚫린다. CVE-2025-29927은 `x-middleware-subrequest` 헤더로 미들웨어를 건너뛰는 취약점이었다(15.2.3, 14.2.25 등에서 수정, Vercel 호스팅은 자동 보호). 자체 호스팅(Docker, `next start`)이 영향을 받았다.
- **실패 양상:** 보호 페이지·API 무인증 접근.
- **신호:** 🟢 `package.json`의 `next` 버전이 취약 범위, `middleware.ts`에서만 인증하고 Route Handler·Server Action·데이터 계층에 검사 없음. 🟡 자체 호스팅 여부는 Dockerfile·`output: 'standalone'`으로 추론. ⚠️근거없음
- **시나리오·수준:** S L1 이상
- **처방:** 공통: Next.js 업그레이드, 데이터 접근 계층에서 다시 인가, 자체 호스팅이면 엣지에서 해당 헤더 제거.
- **검증:** 의존성 스캐너(S-079), 해당 헤더를 넣은 요청 테스트.
- **비용 영향:** 중립
- **출처:** https://github.com/vercel/next.js/security/advisories/GHSA-f82v-jwr5-mffw · https://nextjs.org/docs/app/guides/data-security

### S-062 웹훅 서명 검증 없음
- **무엇/왜:** 결제·인증 웹훅 엔드포인트는 공개 URL이다. 서명(Stripe `Stripe-Signature` + 엔드포인트 비밀)을 원문 본문으로 검증하지 않으면 누구나 "결제 완료" 이벤트를 위조한다. 중복 처리(C-CTL-002)와는 별개다.
- **실패 양상:** 결제 없이 유료 기능·상품 획득, 계정 상태 조작.
- **신호:** 🟢 웹훅 라우트에 `constructEvent`/`Webhook.construct_event`/`svix.verify` 없음, `express.json()`이 웹훅 라우트보다 먼저 적용(원문 손실), `whsec_` 비밀 미사용.
- **시나리오·수준:** S L2 (결제 SDK가 있으면)
- **처방:** 공통: 공식 SDK 검증 함수 + 원문 본문, 타임스탬프 허용 오차.
- **검증:** 서명 없는·잘못된 서명 요청 400 테스트.
- **비용 영향:** 중립
- **출처:** https://docs.stripe.com/webhooks/signature

### S-063 운영 소스맵·`.git`·환경 파일 정적 노출
- **무엇/왜:** 운영에 공개 소스맵을 올리면 원본 코드(주석, 내부 API 경로)가 보인다. 정적 서버 루트에 `.git`, `.env`, 백업 파일이 함께 배포되는 경우도 있다.
- **실패 양상:** 내부 로직·하드코딩된 값·숨은 엔드포인트 노출.
- **신호:** 🟢 `productionBrowserSourceMaps: true`, Vite `build.sourcemap: true` + 별도 보호 없음, Dockerfile `COPY . /usr/share/nginx/html`, `.dockerignore`에 `.git`·`.env` 없음.
- **시나리오·수준:** S L1 이상
- **처방:** 티어0: Vercel Protected Source Maps 또는 소스맵을 오류 추적 도구에만 업로드 / 티어1·2: 빌드 산출물만 복사, `.dockerignore`.
- **검증:** `/.git/HEAD`, `/.env`, `*.map` 요청 404.
- **비용 영향:** 중립
- **출처:** https://vercel.com/docs/deployment-protection (Protected Source Maps) · 그 외 일반 원칙(출처 미확인) ⚠️근거없음

---

## H. 엣지 방어 (WAF·봇·DDoS·프록시)

### S-064 신뢰 프록시 설정 오류와 X-Forwarded-For 스푸핑
- **무엇/왜:** LB 뒤 앱은 `X-Forwarded-For`로 클라이언트 IP를 얻는다. 모든 프록시를 신뢰(`trust proxy: true`)하면서 마지막 프록시가 헤더를 덮어쓰지 않으면 클라이언트가 IP를 위조해 IP 기준 레이트 리밋·차단·감사 로그를 무력화한다. 반대로 신뢰를 안 하면 모든 요청이 LB IP 하나로 보여 레이트 리밋이 전원을 막는다.
- **실패 양상:** 로그인 레이트 리밋 우회(무차별 대입 재개), 감사 로그 IP 위조, 또는 정상 사용자 전원 차단.
- **신호:** 🟢 Express `app.set('trust proxy', true)`, uvicorn `--forwarded-allow-ips='*'`, Django `X-Forwarded-For` 직접 파싱(첫 값 사용), nginx `real_ip_header X-Forwarded-For` + `set_real_ip_from 0.0.0.0/0`. 🟢 simple-web-app은 `REAL_IP_FROM`(VPC CIDR, GCP LB IP/32)만 신뢰 + `real_ip_recursive on`(충족). 🔴 실제 LB 홉 수는 플랫폼 구성.
- **시나리오·수준:** S L1 이상 (IP 기준 통제가 있으면)
- **처방:** 티어0: 플랫폼이 주는 IP 헤더 사용(Vercel 등), Supabase 서버 대리 호출은 `Sb-Forwarded-For` / 티어1·2: 신뢰 대역을 LB CIDR·홉 수로 고정.
- **검증:** 임의 `X-Forwarded-For`를 넣은 요청이 레이트 리밋 키를 바꾸지 못함(simple-web-app tests/nginx 패턴).
- **비용 영향:** 중립
- **출처:** https://expressjs.com/en/guide/behind-proxies.html · https://nginx.org/en/docs/http/ngx_http_realip_module.html · https://supabase.com/docs/guides/auth/rate-limits (`Sb-Forwarded-For`) ⚠️출처확인필요

### S-065 WAF 없음 (공개 API·로그인·결제)
- **무엇/왜:** 관리형 WAF 규칙은 OWASP Top 10 유형의 흔한 공격 패턴과 알려진 악성 IP를 엣지에서 거른다. 앱 수정 없이 붙는 방어층이지만 오탐과 비용이 있다.
- **실패 양상:** 자동 스캐너의 대량 공격이 앱까지 도달, 패치 전 취약점 노출 시간 증가.
- **신호:** 🟢 Terraform `aws_wafv2_web_acl` 연결 없음, `google_compute_security_policy` 없음. 🔴 Vercel WAF 설정은 대시보드.
- **시나리오·수준:** S L2 이상 (L1 과잉)
- **처방:** 티어0: Vercel WAF 관리 규칙·커스텀 규칙 / 티어1·2: AWS WAF(ALB·CloudFront) 관리 규칙, Cloud Armor 사전 구성 규칙.
- **검증:** count 모드로 1~2주 관찰 후 block, 오탐 지표.
- **비용 영향:** 증가 (웹 ACL·규칙·요청량 과금)
- **출처:** https://docs.cloud.google.com/armor/docs/cloud-armor-overview · https://vercel.com/docs/vercel-firewall

### S-066 봇·스크래핑·가입 남용 관리
- **무엇/왜:** 공개 가입, 쿠폰, 선착순, LLM 기능은 봇의 표적이다. 레이트 리밋만으로는 분산 봇을 못 막는다. 봇 관리는 챌린지·CAPTCHA·토큰 재사용 탐지를 쓴다.
- **실패 양상:** 가짜 계정 대량 생성, 쿠폰·재고 싹쓸이, LLM 비용 폭탄.
- **신호:** 🟡 공개 가입 + 무료 크레딧·쿠폰·선착순(T 축 신호와 공유), CAPTCHA(Turnstile, reCAPTCHA, hCaptcha) 미사용.
- **시나리오·수준:** S L2 이상
- **처방:** 티어0: Vercel Bot Protection·Attack Mode, Supabase Auth CAPTCHA / 티어1·2: AWS WAF Bot Control(추가 요금), Cloud Armor + reCAPTCHA.
- **검증:** 자동화 브라우저로 가입 시도 시 챌린지.
- **비용 영향:** 증가 (Bot Control은 별도 요금)
- **출처:** https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-bot.html · https://vercel.com/docs/vercel-firewall

### S-067 DDoS 보호 수준 판단 (Shield Standard vs Advanced, Cloud Armor)
- **무엇/왜:** AWS Shield Standard는 모든 고객에게 추가 비용 없이 L3/L4 방어를 제공하고, CloudFront·Route 53 앞단에서 효과가 크다. Cloud Armor는 L3/L4 자동, L7은 정책 구성이 필요하다. Vercel은 모든 플랜에 플랫폼 DDoS 완화가 있다. 고가 옵션(Shield Advanced 등)은 L3에서만 검토.
- **실패 양상:** L7 폭주로 서비스 중단과 오토스케일 비용 폭증(Denial of Wallet).
- **신호:** 🟢 오리진이 CDN 없이 직접 공개, ALB만 있고 CloudFront 없음. 🟡 T 축 L3 신호와 결합해 판단.
- **시나리오·수준:** S L2 이상 (L7 정책), Shield Advanced류는 S L3 + T L3에서만
- **처방:** 티어0: 기본 제공 / 티어1·2: CDN 앞단 + WAF 레이트 기반 규칙, Cloud Armor 레이트 리밋.
- **검증:** P4 부하 테스트 중 레이트 규칙 발동 확인.
- **비용 영향:** 증가 (CDN·WAF), 과잉 시 큰 고정비
- **출처:** https://docs.aws.amazon.com/waf/latest/developerguide/ddos-standard-summary.html · https://docs.cloud.google.com/armor/docs/cloud-armor-overview · https://vercel.com/docs/vercel-firewall

### S-068 레이트 리밋 키 설계의 보안 측면
- **무엇/왜:** 레이트 리밋은 T 축의 용량 보호이기도 하지만 보안에서는 "누구 기준으로 세는가"가 핵심이다. IP만 쓰면 NAT 뒤 사용자들이 함께 막히고 분산 공격은 통과한다. 계정 기준만 쓰면 여러 계정을 도는 스터핑이 통과한다. 민감 동작(로그인, 재설정, 계정 삭제, OTP)은 별도 예산이 필요하다.
- **실패 양상:** 민감 경로가 일반 예산을 공유해 무차별 대입 허용, 또는 정상 사용자 차단.
- **신호:** 🟢 simple-web-app nginx는 로그인(IP), 계정 삭제(IP, 별도 존), 쓰기(세션 쿠키), 읽기(IP)로 나눔(충족 예). 🟢 단일 전역 리미터만 있음 → 미충족.
- **시나리오·수준:** S L1 이상 (민감 경로 분리), S L2 (IP + 계정 이중 키)
- **처방:** 공통: 경로별 존, 민감 경로 IP + 계정 키, 429 + Retry-After.
- **검증:** 경로별 한도 테스트(simple-web-app tests/nginx/test_ratelimit.py 패턴).
- **비용 영향:** 중립 (분산 리미터에 Redis가 필요하면 증가)
- **출처:** https://cheatsheetseries.owasp.org/cheatsheets/Credential_Stuffing_Prevention_Cheat_Sheet.html (IP 기준 제한과 그 한계) · https://nextjs.org/docs/app/guides/data-security (비싼 동작 레이트 리밋)

### S-069 호스트 헤더 검증 (`ALLOWED_HOSTS`, 와일드카드 서버)
- **무엇/왜:** Host 헤더를 검증하지 않으면 비밀번호 재설정 메일 링크가 공격자 도메인으로 만들어지거나 캐시가 오염된다. Django는 DEBUG=False일 때 `ALLOWED_HOSTS`를 요구한다.
- **실패 양상:** 재설정 링크 탈취, 캐시 포이즈닝.
- **신호:** 🟢 `ALLOWED_HOSTS = ['*']`, 메일 링크를 `request.headers.host`로 생성, nginx `server_name _`만 있고 기본 서버 거부 없음(LB가 호스트 라우팅하면 완화).
- **시나리오·수준:** S L1 이상
- **처방:** 공통: 허용 호스트 고정, 링크는 설정값 도메인으로 생성.
- **검증:** `Host: evil.example` 요청 시 400.
- **비용 영향:** 중립
- **출처:** https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/ (ALLOWED_HOSTS, 와일드카드 피하기)

---

## I. 컨테이너·Kubernetes

### S-070 컨테이너 root 실행
- **무엇/왜:** 컨테이너 탈출이나 앱 RCE 시 root면 피해가 커진다. Dockerfile `USER`와 k8s `runAsNonRoot`로 막는다.
- **실패 양상:** 파일시스템 변조, 탈출 취약점과 결합 시 노드 장악.
- **신호:** 🟢 Dockerfile에 `USER` 없음, `securityContext.runAsNonRoot` 없음. 🟢 simple-web-app auth Dockerfile `USER 10001`, 매니페스트 `runAsNonRoot: true`, nginx는 unprivileged 이미지(충족).
- **시나리오·수준:** S L1 이상 (티어1·2)
- **처방:** 티어1: Dockerfile `USER`, ECS `user` 필드 / 티어2: Pod securityContext.
- **검증:** `docker run ... id -u` ≠ 0, PSA restricted 경고 0.
- **비용 영향:** 중립
- **출처:** https://docs.docker.com/build/building/best-practices/ · https://kubernetes.io/docs/concepts/security/pod-security-standards/

### S-071 읽기 전용 루트 파일시스템·권한 상승 차단·capability 제거
- **무엇/왜:** `readOnlyRootFilesystem`, `allowPrivilegeEscalation: false`, `capabilities.drop: [ALL]`, seccomp `RuntimeDefault`는 침해 후 행동 범위를 줄인다. PSS restricted의 요구 항목이다.
- **실패 양상:** 침해 후 도구 설치·바이너리 변조·지속성 확보.
- **신호:** 🟢 각 항목 존재 여부. 🟢 simple-web-app 앱 컨테이너는 `readOnlyRootFilesystem: true`, nginx는 drop ALL + allowPrivilegeEscalation false이나 readOnlyRootFilesystem은 꺼 둠(kustomization 주석, 부분 충족). 🟡 seccompProfile 명시 여부 확인 필요.
- **시나리오·수준:** S L2 이상
- **처방:** 티어1: ECS `readonlyRootFilesystem` / 티어2: securityContext + 쓰기 경로만 emptyDir.
- **검증:** kubeconform + kube-linter/kubescape, PSA restricted enforce.
- **비용 영향:** 중립
- **출처:** https://kubernetes.io/docs/concepts/security/pod-security-standards/

### S-072 Pod Security Admission 미적용 (privileged·hostPath·hostNetwork)
- **무엇/왜:** 네임스페이스 라벨 `pod-security.kubernetes.io/enforce`로 PSS 수준을 강제한다. 없으면 누군가 privileged Pod나 hostPath 마운트를 배포해 노드를 장악할 수 있다.
- **실패 양상:** 노드 루트 획득, 다른 Pod 비밀 탈취.
- **신호:** 🟢 Namespace 매니페스트에 PSA 라벨 없음, 워크로드에 `privileged: true`, `hostPath`, `hostNetwork: true`.
- **시나리오·수준:** S L2 이상, 티어2
- **처방:** 티어2: 앱 네임스페이스 `enforce: restricted`(최소 baseline), `warn`·`audit` 병행.
- **검증:** 위반 Pod apply가 거부됨.
- **비용 영향:** 중립
- **출처:** https://kubernetes.io/docs/concepts/security/pod-security-admission/ · https://kubernetes.io/docs/concepts/security/pod-security-standards/

### S-073 RBAC 과다·서비스 계정 토큰 자동 마운트
- **무엇/왜:** 앱 Pod는 대부분 k8s API를 부를 필요가 없다. 기본 서비스 계정 토큰이 마운트돼 있고 그 계정에 넓은 권한이 있으면 침해 시 클러스터 API를 쓴다. 와일드카드 Role과 cluster-admin 바인딩은 피한다.
- **실패 양상:** Secret 열람, 워크로드 생성으로 측면 이동.
- **신호:** 🟢 `automountServiceAccountToken` 미설정, Role/ClusterRole에 `"*"`, `cluster-admin` ClusterRoleBinding, `system:masters`.
- **시나리오·수준:** S L2 이상, 티어2
- **처방:** 티어2: 앱 SA `automountServiceAccountToken: false`, 필요한 컨트롤러만 네임스페이스 Role.
- **검증:** `kubectl auth can-i --list --as=system:serviceaccount:ns:sa`.
- **비용 영향:** 중립
- **출처:** https://kubernetes.io/docs/concepts/security/rbac-good-practices/

### S-074 k8s Secret 저장 암호화
- **무엇/왜:** k8s Secret은 기본적으로 etcd에 암호화 없이 저장된다. 관리형 클러스터는 대체로 해결해 준다: EKS는 1.28 이상에서 모든 API 데이터를 KMS v2 봉투 암호화(AWS 소유 키, 원하면 CMK). 자체 구축 클러스터는 직접 켜야 한다.
- **실패 양상:** etcd 백업·스냅샷 유출 시 비밀 평문 노출.
- **신호:** 🟢 EKS 버전 < 1.28 + `encryption_config` 없음, kubeadm/kind 운영. 🟡 GKE 애플리케이션 레이어 암호화(CMEK) 여부는 L3에서만 요구.
- **시나리오·수준:** S L2 이상 (CMK는 L3)
- **처방:** 티어2: EKS 1.28+ 기본, L3는 CMK 지정 / GKE L3는 애플리케이션 레이어 비밀 암호화(출처 미확인). ⚠️근거없음
- **검증:** 클러스터 암호화 설정 조회.
- **비용 영향:** 중립 (CMK는 키당 월 $1 + 요청 과금)
- **출처:** https://kubernetes.io/docs/concepts/configuration/secret/ · https://docs.aws.amazon.com/eks/latest/userguide/envelope-encryption.html

### S-075 이미지 취약점 스캔 없음
- **무엇/왜:** 베이스 이미지 OS 패키지와 언어 의존성의 알려진 CVE를 배포 전에 잡는다. Trivy는 취약점, 설정 오류, 비밀, SBOM을 한 번에 다룬다.
- **실패 양상:** 알려진 RCE가 있는 이미지가 그대로 운영.
- **신호:** 🟢 CI에 trivy/grype/docker scout 단계 없음, ECR `scan_on_push` 없음. 🟡 오래된 베이스 태그(`node:14`, `python:3.8`).
- **시나리오·수준:** S L2 이상 (L1은 의존성 스캔 S-079로 충분)
- **처방:** 티어1·2: CI 스캔 + 심각도 기준 게이트, 레지스트리 스캔 켜기.
- **검증:** CI 실패 기준(CRITICAL 0) 동작 확인.
- **비용 영향:** 중립~소폭 증가 (레지스트리 고급 스캔 과금)
- **출처:** https://trivy.dev/docs/latest/ ⚠️출처확인필요

### S-076 이미지 서명·검증
- **무엇/왜:** 레지스트리나 CI 침해로 바뀐 이미지가 배포되지 않도록 서명하고, 배포 시 서명을 검증한다. 서명은 태그가 아니라 다이제스트에 한다.
- **실패 양상:** 변조 이미지가 정상 배포 경로로 운영 진입.
- **신호:** 🟢 CI에 `cosign sign` 없음, 클러스터에 서명 검증 정책(Kyverno·Binary Authorization 등) 없음.
- **시나리오·수준:** S L3 (L2 과잉)
- **처방:** 티어1·2: cosign keyless 서명(CI OIDC) + 배포 시 검증 정책.
- **검증:** 서명 없는 이미지 배포 거부 테스트.
- **비용 영향:** 소폭 증가 (운영 부담)
- **출처:** https://docs.sigstore.dev/cosign/signing/signing_with_containers/ ⚠️출처확인필요

### S-077 베이스 이미지 다이제스트 고정·최소 이미지
- **무엇/왜:** `FROM node:20` 같은 태그는 게시자가 바꿀 수 있다. 다이제스트 고정은 재현성과 공급망 무결성을 준다. 멀티 스테이지로 빌드 도구를 운영 이미지에서 빼면 공격 표면이 준다.
- **실패 양상:** 같은 커밋인데 다른 이미지, 침해된 태그 유입, 셸·컴파일러가 남은 이미지.
- **신호:** 🟢 `FROM x:tag`에 `@sha256:` 없음, `:latest`, 단일 스테이지에 빌드 도구 포함. 🟢 simple-web-app `FROM python:3.12-slim`(태그만, 부분 충족).
- **시나리오·수준:** S L2 이상 (latest 금지는 L1)
- **처방:** 티어1·2: 다이제스트 고정 + Renovate/Dependabot로 갱신, 멀티 스테이지, slim/distroless.
- **검증:** hadolint DL3006/DL3007 류 규칙.
- **비용 영향:** 중립 (작은 이미지는 전송·저장 감소)
- **출처:** https://docs.docker.com/build/building/best-practices/

---

## J. 공급망

### S-078 lock 파일 없음·CI에서 lock 무시
- **무엇/왜:** lock 파일이 없거나 CI가 `npm install`로 lock을 갱신하면 빌드마다 다른 의존성이 들어오고, 악성 새 버전이 자동 유입된다. `npm ci`는 lock과 package.json이 다르면 실패한다.
- **실패 양상:** 탈취된 패키지 새 버전이 다음 배포에 자동 포함.
- **신호:** 🟢 `package-lock.json`/`pnpm-lock.yaml`/`yarn.lock`/`uv.lock`/`poetry.lock` 없음, CI·Dockerfile에 `npm install`(not `npm ci`), `pip install -r requirements.txt`에 버전 범위. 🟢 simple-web-app은 `requirements.lock`·`uv.lock`·`package-lock.json` 존재(충족).
- **시나리오·수준:** 모든 수준
- **처방:** 공통: lock 커밋, `npm ci`/`pnpm install --frozen-lockfile`/`uv sync --frozen`.
- **검증:** CI 로그에서 frozen 설치 확인.
- **비용 영향:** 중립
- **출처:** https://docs.npmjs.com/cli/v11/commands/npm-ci ⚠️출처확인필요

### S-079 의존성 취약점 검사·자동 갱신 없음
- **무엇/왜:** 알려진 취약 버전(예: S-061의 Next.js)을 계속 쓰는 것이 가장 흔한 침해 경로다. Dependabot 보안 업데이트, `npm audit`, `pip-audit`, OSV 스캐너로 잡는다.
- **실패 양상:** 공개 익스플로잇이 있는 취약점이 몇 달씩 운영에 남음.
- **신호:** 🟢 `.github/dependabot.yml`·`renovate.json` 없음, CI에 audit 단계 없음. 🟡 lock 파일의 알려진 취약 버전은 오프라인 DB로 직접 판정 가능.
- **시나리오·수준:** 모든 수준
- **처방:** 공통: Dependabot 보안 업데이트 + CI audit(HIGH 이상 실패).
- **검증:** 스캐너 결과 HIGH/CRITICAL 0.
- **비용 영향:** 중립
- **출처:** https://docs.github.com/en/code-security/dependabot/dependabot-security-updates/about-dependabot-security-updates · https://expressjs.com/en/advanced/best-practice-security.html (npm audit) ⚠️출처확인필요

### S-080 GitHub Actions 서드파티 액션 태그 참조
- **무엇/왜:** `uses: some/action@v3`는 태그가 옮겨지면 다른 코드가 실행된다. 전체 커밋 SHA 고정이 가장 안전하다. 이 워크플로가 비밀과 배포 권한을 갖는다면 공급망 공격의 직통로다.
- **실패 양상:** 탈취된 액션이 CI 비밀·배포 토큰 유출.
- **신호:** 🟢 `uses:` 뒤가 40자 SHA가 아님(공식 `actions/*`는 위험이 낮다고 볼지 규칙에서 결정).
- **시나리오·수준:** S L1 이상 (CI가 비밀을 가지면)
- **처방:** 공통: SHA 고정 + Dependabot `github-actions` 생태계로 갱신.
- **검증:** zizmor/actionlint 류 정적 검사(출처 미확인). ⚠️근거없음
- **비용 영향:** 중립
- **출처:** https://docs.github.com/en/actions/reference/security/secure-use

### S-081 워크플로 토큰 권한·`pull_request_target` 위험
- **무엇/왜:** `GITHUB_TOKEN` 기본 쓰기 권한, 포크 PR 코드를 비밀이 있는 컨텍스트에서 실행하는 `pull_request_target`은 저장소 장악으로 이어질 수 있다.
- **실패 양상:** 외부 PR 하나로 비밀 유출·main 브랜치 변조.
- **신호:** 🟢 워크플로 최상위 `permissions:` 없음 또는 `write-all`, `on: pull_request_target` + PR head 체크아웃.
- **시나리오·수준:** S L1 이상 (공개 저장소면 필수)
- **처방:** 공통: 최상위 `permissions: contents: read`, 잡별 상향, `pull_request_target` 대신 `workflow_run`.
- **검증:** 정적 검사.
- **비용 영향:** 중립
- **출처:** https://docs.github.com/en/actions/reference/security/secure-use

### S-082 SBOM 미생성
- **무엇/왜:** 새 취약점이 공개됐을 때 "우리 이미지에 그 라이브러리가 있나"를 바로 답하려면 배포물별 SBOM이 필요하다. 규제·B2B 고객이 요구하기도 한다.
- **실패 양상:** 사고 대응 시 영향 범위 파악 지연.
- **신호:** 🟢 CI에 SBOM 생성(trivy `--format cyclonedx`, syft, `docker buildx --sbom`) 없음.
- **시나리오·수준:** S L2 이상 (B2B), S L3 필수
- **처방:** 티어1·2: 빌드 시 SBOM 생성·이미지에 첨부.
- **검증:** 릴리스 아티팩트에 SBOM 존재.
- **비용 영향:** 중립
- **출처:** https://trivy.dev/docs/latest/ (SBOM 생성) ⚠️출처확인필요

### S-083 빌드 출처 증명 (SLSA)
- **무엇/왜:** SLSA Build L1은 출처 기록, L2는 호스팅 빌드 + 서명된 출처, L3는 빌드 간섭과 서명 자격 증명 접근을 막는 강화 빌드다. 개발자 노트북에서 빌드해 푸시하는 구조는 L0다.
- **실패 양상:** 누가 어떤 소스로 만든 이미지인지 증명 불가, 내부자·탈취된 PC 빌드 유입.
- **신호:** 🟢 README·Makefile에 로컬 `docker build && docker push`만 있음, CI에서 provenance 생성 없음(`actions/attest-build-provenance` 류 — 출처 미확인). ⚠️근거없음
- **시나리오·수준:** S L3 (L2는 "CI에서만 빌드" 정도)
- **처방:** 티어1·2: CI 빌드 + 서명된 provenance, 배포 시 검증.
- **검증:** 이미지에 provenance attestation 존재.
- **비용 영향:** 중립
- **출처:** https://slsa.dev/spec/v1.0/levels ⚠️출처확인필요

### S-084 설치 스크립트·타이포스쿼팅 의존성
- **무엇/왜:** npm `postinstall` 스크립트는 설치 시 임의 코드를 실행한다. 이름이 비슷한 가짜 패키지, 갓 만들어진 무명 패키지는 공급망 공격의 흔한 형태다. 바이브코딩에서는 LLM이 존재하지 않는 패키지 이름을 제안하기도 한다.
- **실패 양상:** CI·개발자 머신에서 비밀 탈취, 백도어 포함.
- **신호:** 🟡 manifest의 의존성 이름을 레지스트리 메타데이터(생성일, 다운로드 수)와 대조해야 함 → 오프라인이면 🔴. 🟢 `.npmrc`에 `ignore-scripts` 없음.
- **시나리오·수준:** S L2 이상
- **처방:** 공통: 새 의존성 리뷰, 필요 없는 설치 스크립트 차단, 내부 레지스트리 프록시.
- **검증:** 의존성 추가 PR에 자동 평판 검사.
- **비용 영향:** 중립
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

---

## K. 데이터 보호·감사

### S-085 저장 데이터 암호화 (DB·스토리지·디스크)
- **무엇/왜:** RDS는 생성 시에만 암호화를 켤 수 있고, 켜면 로그·자동 백업·복제본·스냅샷이 모두 암호화된다. 나중에 켜려면 스냅샷 암호화 복사 후 복원(=이전 작업)이 필요하다. 그래서 처음부터 켜는 것이 싸다.
- **실패 양상:** 스냅샷·디스크 유출 시 평문 데이터, 규제 위반.
- **신호:** 🟢 Terraform `storage_encrypted` 없음/false(RDS), `aws_ebs_volume encrypted = false`, S3 SSE 설정 제거. 🟡 GCP·Supabase는 기본 암호화(출처 미확인). ⚠️근거없음
- **시나리오·수준:** S L1 이상 (기본 키), S L3 (고객 관리 키)
- **처방:** 티어1·2: `storage_encrypted = true`(AWS 관리 키로 시작), L3는 CMK.
- **검증:** `describe-db-instances` `StorageEncrypted: true`, checkov.
- **비용 영향:** 중립 (CMK는 키당 월 $1 + 요청)
- **출처:** https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Overview.Encryption.html

### S-086 KMS 키 삭제·비활성화 위험 (고객 관리 키의 함정)
- **무엇/왜:** CMK를 쓰면 키 관리 실수가 곧 가용성·데이터 손실이다. RDS는 키를 잃으면 접근 불가 상태가 되고 7일 안에 복구하지 못하면 백업으로만 복원 가능하다. EKS는 CMK 삭제 시 복구 불가다. L3가 아니면 AWS 관리 키가 더 안전한 선택일 수 있다.
- **실패 양상:** 키 비활성화 → DB·클러스터 사용 불가, 삭제 → 영구 손실.
- **신호:** 🟢 `aws_kms_key` + `deletion_window_in_days` 최소값, 키 정책에 `kms:*`를 넓게 부여, 여러 클러스터·DB가 한 키 공유.
- **시나리오·수준:** S L3 (CMK를 쓸 때만)
- **처방:** 티어1·2: 키 관리 권한 분리, 삭제 대기 기간 최대, 키 상태 알람.
- **검증:** 키 정책 검토, CloudWatch 알람 존재.
- **비용 영향:** 중립
- **출처:** https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Overview.Encryption.html · https://docs.aws.amazon.com/eks/latest/userguide/envelope-encryption.html

### S-087 백업·스냅샷의 암호화와 공유 설정
- **무엇/왜:** 백업은 원본만큼 민감하지만 공유·복사가 쉽다. 공개 스냅샷, 다른 계정 공유, 암호화 안 된 덤프 파일(`pg_dump`를 S3에 평문 업로드)이 흔한 유출 경로다. 불변 백업(랜섬웨어 대비)은 D 축 담당.
- **실패 양상:** 공개 스냅샷에서 전체 DB 복원.
- **신호:** 🟢 백업 스크립트가 `pg_dump | aws s3 cp`(SSE·버킷 BPA 없음), 스냅샷 `shared_accounts`/public 속성.
- **시나리오·수준:** S L1 이상
- **처방:** 티어1·2: 관리형 백업 사용(암호화 상속), 덤프는 암호화 버킷 + BPA.
- **검증:** 스냅샷 공개 여부 점검, 버킷 정책 점검.
- **비용 영향:** 중립
- **출처:** https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Overview.Encryption.html (암호화된 인스턴스의 백업·스냅샷 암호화) · 공유 관련은 일반 원칙(출처 미확인) ⚠️근거없음

### S-088 로그에 개인정보·비밀 기록
- **무엇/왜:** 요청 본문 전체 로깅, 오류 시 사용자 객체 덤프, 쿼리 로그에 비밀번호·토큰·전화번호·주민번호가 남는다. 로그는 접근 권한이 넓고 보관이 길어 2차 유출 창구가 된다. 로그 주입(CR/LF)도 막아야 한다.
- **실패 양상:** 로그 시스템 접근자에게 개인정보 노출, 유출 사고 범위 확대, 규제 위반.
- **신호:** 🟢 `logger.info(req.body)`, `console.log(user)`, morgan `:req[authorization]`, Prisma `log: ['query']` 운영 활성화, `print(request.json())`. 🟢 simple-web-app은 uvicorn `--no-access-log`와 별도 관측 모듈(부분 신호).
- **시나리오·수준:** S L1 이상
- **처방:** 공통: 구조화 로그 + 필드 허용 목록/마스킹, 세션 ID는 해시로, 운영 쿼리 로그 끄기.
- **검증:** 테스트 요청 후 로그에서 민감 값 grep.
- **비용 영향:** 감소 (로그 양 감소)
- **출처:** https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html

### S-089 클라우드 감사 로그 (CloudTrail·Cloud Audit Logs)
- **무엇/왜:** 사고 조사에는 "누가 언제 무엇을 바꿨나"가 필요하다. CloudTrail 이벤트 기록은 관리 이벤트 90일만 무료로 남고, 더 길게·데이터 이벤트까지 남기려면 trail을 만든다. GCP Admin Activity 로그는 항상 켜져 있고 무료지만 Data Access 로그는 기본 꺼짐(BigQuery 제외)이고 비용이 생긴다.
- **실패 양상:** 침해 후 범위·원인 파악 불가, 규제 보관 의무 미충족.
- **신호:** 🟢 Terraform `aws_cloudtrail` 없음, GCP `google_project_iam_audit_config` 없음. 🔴 콘솔로 만든 trail은 미확인.
- **시나리오·수준:** S L2 이상 (L1은 기본 90일로 충분하다고 볼 수 있음)
- **처방:** 티어1·2: 조직/멀티 리전 trail → 별도 계정 S3(쓰기 전용), GCP는 민감 서비스 Data Access 로그 선택적 활성화.
- **검증:** trail 상태·로그 파일 무결성 검증.
- **비용 영향:** 증가 (저장·데이터 이벤트 과금)
- **출처:** https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-event-history.html · https://docs.cloud.google.com/logging/docs/audit

### S-090 개인정보처리시스템 접속기록 보관 (한국)
- **무엇/왜:** 개인정보 안전성 확보조치 기준은 개인정보취급자의 처리시스템 접속기록(누가, 언제, 무엇을 처리)을 보관·점검하도록 요구한다. 검색으로 확인한 바로는 1년 이상, 5만 명 이상이나 고유식별·민감정보 처리 시스템은 2년 이상이다(원문 수치 직접 미확인). 앱 관리자 화면의 조회·다운로드 기록이 대상이다.
- **실패 양상:** 내부자 유출 추적 불가, 점검 시 과태료.
- **신호:** 🟢 관리자 화면·내부 도구가 있는데 감사 테이블·감사 로그(누가 어떤 사용자 레코드를 조회·수정·다운로드) 없음. 🟡 한국 사용자 대상 신호(ko 로케일, 원화, 한국 결제·본인인증 SDK).
- **시나리오·수준:** S L2 이상 (한국 대상 + 개인정보), S L3 (2년 기준)
- **처방:** 공통: 관리자 행위 감사 로그(append-only 테이블 또는 별도 로그 저장소), 보관 기간 설정, 월 1회 점검 절차.
- **검증:** 관리자 조회 후 감사 레코드 생성 테스트, 보관 정책 확인.
- **비용 영향:** 소폭 증가 (로그 저장)
- **출처:** https://www.law.go.kr/행정규칙/개인정보의안전성확보조치기준 (제8조 접속기록 — 조문 제목 수준만 확인, 보관 기간 수치는 검색 요약 기준이라 원문 재확인 필요) ⚠️근거없음

### S-091 데이터 최소화·보관 기간·파기
- **무엇/왜:** 쓰지 않는 개인정보(주민번호, 생년월일 전체, 원본 신분증 이미지)를 모으지 않고, 목적이 끝나면 파기한다. 저장하지 않은 데이터는 유출되지 않는다.
- **실패 양상:** 유출 시 피해 규모 확대, 규제 위반.
- **신호:** 🟢 스키마에 `ssn`, `resident_number`, `rrn`, `card_number`, `cvv` 컬럼, 탈퇴 처리에서 실제 삭제 없음(soft delete만). 🟢 simple-web-app은 계정 삭제 API와 테스트(`test_delete_account.py`)가 있음.
- **시나리오·수준:** S L1 이상 (민감 컬럼이 있으면 S L3 신호)
- **처방:** 공통: 수집 항목 축소, 탈퇴·보관 기간 경과 시 파기 배치, 가명처리.
- **검증:** 탈퇴 후 DB·스토리지·로그에서 사용자 데이터 잔존 검사.
- **비용 영향:** 감소
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

---

## L. 규제 (한국·해외)

### S-092 개인정보 유출 신고 72시간 체계
- **무엇/왜:** 한국은 1천 명 이상 유출, 민감·고유식별정보 유출, 외부 불법 접근에 의한 유출이면 알게 된 때부터 72시간 안에 개인정보보호위원회 또는 KISA에 신고해야 한다(미신고 시 과태료). GDPR도 감독기관에 72시간 이내 통지를 요구한다. 신고하려면 먼저 "유출을 알아챌" 수단(감사 로그, 이상 탐지)이 있어야 한다.
- **실패 양상:** 유출을 늦게 알거나 범위를 몰라 기한 초과 → 과태료와 신뢰 손실.
- **신호:** 🔴 절차는 코드에 없음 → 가정 "사고 대응 절차 미확인". 🟡 한국 사용자 대상 + 개인정보 저장 신호면 이 항목 활성.
- **시나리오·수준:** S L1 이상 (개인정보를 저장하면)
- **처방:** 공통: 사고 대응 런북(누가 판단, 72시간 타임라인, 신고 채널), S-089·S-090 로그와 연결.
- **검증:** 탁상 훈련 기록.
- **비용 영향:** 중립
- **출처:** https://pipc.go.kr/np/default/page.do?mCode=D030040000 (신고 기준과 72시간) · https://gdpr-info.eu/art-33-gdpr/ (GDPR 제33조 72시간 — 비공식 정리 사이트이며 EUR-Lex 원문은 이번에 열지 못함) ⚠️출처부적격

### S-093 개인정보 국외 이전 (해외 리전·해외 SaaS)
- **무엇/왜:** 한국 개인정보보호법 제28조의8은 국외 제공·처리위탁·보관을 "이전"으로 보고, 별도 동의, 계약 이행에 필요한 처리위탁·보관(처리방침 공개 등), 인증, 적정성 인정 등 요건을 둔다. Vercel·Supabase·Firebase 기본 리전이 미국이거나, 해외 LLM API·분석 도구로 개인정보를 보내는 경우가 바이브코더 앱에서 흔한 국외 이전이다.
- **실패 양상:** 처리방침 미공개·동의 누락으로 법 위반, 리전 이전 비용 발생.
- **신호:** 🟢 Supabase 프로젝트 리전·Vercel 함수 리전 설정(`vercel.json` `regions`), Firebase `locationId`, Terraform 리전이 한국 외 + 한국 사용자 신호. 🟢 개인정보를 OpenAI·Anthropic 등 해외 API로 전송하는 코드. 🔴 처리방침 공개 여부는 저장소 밖.
- **시나리오·수준:** S L1 이상 (한국 사용자 + 개인정보 + 해외 처리)
- **처방:** 티어0: 서울 리전 선택 가능한 서비스는 서울(설계 문서 기본 리전과 일치), 불가하면 처리방침에 국외 이전 항목 / 티어1·2: `ap-northeast-2`/`asia-northeast3`.
- **검증:** 리전 설정 확인, 처리방침 항목 체크리스트.
- **비용 영향:** 중립~증가 (서울 리전이 더 비싼 경우)
- **출처:** https://www.privacy.go.kr/front/contents/cntntsView.do?contsNo=367 (개인정보 포털, 제28조의8 이전 요건)

### S-094 데이터 레지던시 고정 (규제·계약상 국내 보관)
- **무엇/왜:** 공공, 금융, 의료, 일부 B2B 계약은 데이터를 국내에 두도록 요구한다. 그때는 DB만이 아니라 백업, 로그, CDN 캐시, 오류 추적 도구, LLM 호출까지 리전을 맞춰야 한다.
- **실패 양상:** 백업·로그만 해외 리전에 복제돼 계약 위반.
- **신호:** 🟢 백업 복제 대상 리전, 로그 싱크 리전, Sentry·Datadog 사이트 설정(`us`/`eu`), 멀티 리전 DR이 해외. 🟡 도메인(공공·금융·의료) 추론. ⚠️근거없음
- **시나리오·수준:** S L3
- **처방:** 티어1·2: 모든 데이터 경로를 국내 리전에 고정, 조직 정책으로 리전 제한(GCP resource locations, AWS SCP).
- **검증:** 리전 목록 자동 점검.
- **비용 영향:** 증가 (D 축의 해외 DR 선택지 제한)
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### S-095 ISMS·ISMS-P 의무 대상 여부
- **무엇/왜:** 정보통신망법 제47조에 따라 정보통신서비스 부문 전년도 매출 100억 원 이상, 전년도 일평균 이용자 100만 명 이상 등은 ISMS 인증 의무 대상이고, 처음 대상이 되면 다음 해 8월 31일까지 취득해야 한다. 코드로 매출은 알 수 없지만, 가정 사용자 수와 도메인으로 "검토 필요" 경고는 낼 수 있다.
- **실패 양상:** 의무 대상인데 미인증 → 과태료, 대기업·공공 고객 계약 불가.
- **신호:** 🔴 매출·이용자 수는 코드에 없음 → 가정값(T 축 가정)으로 경고만. 🟡 B2B 대기업 고객 신호.
- **시나리오·수준:** S L3 (해당 가정일 때)
- **처방:** 공통: 인증 범위를 줄이는 구조(관리형 서비스, 계정 분리), 이 카탈로그 L2~L3 통제가 인증 항목과 상당 부분 겹침.
- **검증:** 해당 없음(법무·컨설팅 판단).
- **비용 영향:** 증가 (인증 비용·운영 인력)
- **출처:** https://isms-p.or.kr/cert/aply/selectCertTrgtDetail.do (ISMS-P 인증 대상 안내 페이지 — 운영 주체가 KISA인지 이번에 확인하지 못함; KISA 도메인 isms.kisa.or.kr은 접속 실패)

### S-096 공공기관 납품: CSAP → 국정원 클라우드 보안검증 전환
- **무엇/왜:** 공공기관에 클라우드 서비스를 공급하려면 그동안 CSAP(클라우드 서비스 보안인증)가 필요했다. 2026년 4월 보도에 따르면 CSAP를 해체하고 공공 보안요건은 국정원 "클라우드 보안검증"으로, 민간 요건은 ISMS로 통합하며 새 제도는 2027년 7월 시행, 2027년 6월까지 CSAP 취득분은 5년 유효를 인정한다. 공공 도메인 앱이면 사용하는 클라우드·SaaS가 해당 인증·검증을 받았는지가 티어 선택을 제약한다.
- **실패 양상:** 인증 없는 플랫폼(예: 일부 해외 BaaS)으로 만든 서비스는 공공 납품 불가 → 재구축.
- **신호:** 🟡 도메인 추론(공공·지자체·학교), README의 "공공기관", `.go.kr` 도메인. 🔴 계약 조건은 저장소 밖.
- **시나리오·수준:** S L3 (공공 도메인)
- **처방:** 공통: 티어 규칙에 "공공 납품이면 인증·검증 받은 클라우드 리전·서비스만" 제약 추가. 제도 전환기라 시점 확인 필수.
- **검증:** 해당 없음(조달 요건 확인).
- **비용 영향:** 증가 (선택 가능한 플랫폼 축소)
- **출처:** https://zdnet.co.kr/view/?no=20260420130424 (언론 보도, 1차 자료 아님. 국정원·과기정통부 원문 지침은 미확인) ⚠️출처부적격

### S-097 PCI DSS 범위: 카드 데이터를 직접 받는가, 토큰화하는가
- **무엇/왜:** 카드 번호를 자체 폼으로 받아 서버를 거치면 앱 전체가 PCI DSS 범위에 들어간다. 결제대행(PG)의 호스팅 결제창·리다이렉트·iframe을 쓰면 SAQ A 같은 가벼운 자가평가 대상이 될 수 있다. 2025년 개정된 SAQ A는 상점 사이트가 스크립트 공격에 취약하지 않음을 확인하는 적격 기준을 추가했다.
- **실패 양상:** 직접 처리 시 막대한 준수 비용과 유출 책임, 결제 페이지 스크립트 변조(카드 스키밍).
- **신호:** 🟢 폼 필드·API 스키마에 `cardNumber`, `pan`, `cvc`/`cvv`, `expiry` + 자체 서버 전송, DB 컬럼 `card_number`. 🟢 Stripe Elements/Checkout, 토스페이먼츠 결제위젯, 아임포트(포트원) 사용은 토큰화(범위 축소). 🟡 결제 페이지에 서드파티 스크립트 다수.
- **시나리오·수준:** 직접 처리 → S L3, 토큰화 → S L2
- **처방:** 공통: PG 호스팅 결제창·Elements로 전환해 카드 데이터가 서버를 지나지 않게, 결제 페이지 CSP와 스크립트 무결성 관리.
- **검증:** 서버 로그·DB에 PAN 패턴(Luhn 검사) 0건.
- **비용 영향:** 감소 (토큰화로 준수 범위 축소)
- **출처:** https://blog.pcisecuritystandards.org/important-updates-announced-for-merchants-validating-to-self-assessment-questionnaire-a (SAQ A 적격 기준 변경)

### S-098 GDPR 적용 (EU 사용자 대상)
- **무엇/왜:** EU 밖 사업자라도 EU 내 정보주체에게 재화·서비스를 제공하면(유료 여부 무관) GDPR이 적용된다. 유출 통지 72시간, 국외 이전 장치, 정보주체 권리(삭제·열람) 구현이 따라온다.
- **실패 양상:** 과징금, EU 고객 계약 불가.
- **신호:** 🟡 EU 언어 로케일(de, fr, es 등), 유로 통화, EU 배송 국가 목록, 쿠키 동의 배너 라이브러리 존재 여부.
- **시나리오·수준:** S L2 이상 (EU 대상 신호가 있으면)
- **처방:** 공통: 쿠키·추적 동의, 삭제·내보내기 기능, 리전·이전 장치 검토.
- **검증:** 계정 삭제·데이터 내보내기 E2E 테스트.
- **비용 영향:** 증가 (EU 리전·법무)
- **출처:** https://gdpr-info.eu/art-3-gdpr/ (제3조(2)(a) — 비공식 정리 사이트, EUR-Lex 원문은 이번에 열지 못함) ⚠️출처부적격

### S-099 민감정보·고유식별정보 처리 (주민번호·건강·생체)
- **무엇/왜:** 주민등록번호, 여권·운전면허 번호, 건강·생체 정보는 한국법상 별도 동의·암호화 의무가 붙고, 유출 시 1명이라도 신고 대상이 된다(S-092). 주민번호는 법령 근거 없이 수집 자체가 제한된다.
- **실패 양상:** 유출 시 최고 수준 제재, 수집 자체가 위법일 수 있음.
- **신호:** 🟢 스키마·폼 필드 `rrn`, `resident_registration`, `jumin`, `passport_no`, `diagnosis`, `blood_type`, 얼굴·지문 이미지 저장, 주민번호 정규식(`\d{6}-?[1-4]\d{6}`).
- **시나리오·수준:** S L3
- **처방:** 공통: 수집 중단 또는 본인확인기관 연동(CI/DI 사용), 컬럼 단위 암호화, 접근 기록.
- **검증:** DB·로그에 주민번호 패턴 0건.
- **비용 영향:** 증가
- **출처:** https://pipc.go.kr/np/default/page.do?mCode=D030040000 (민감·고유식별정보 유출 시 신고 대상) · 수집 제한·암호화 의무 세부는 원문 미확인(출처 미확인) ⚠️근거없음

### S-100 개인정보 안전성 확보조치의 클라우드 매핑
- **무엇/왜:** 한국 개인정보 안전성 확보조치 기준(접근 권한 관리, 접근 통제, 암호화, 접속기록, 악성 프로그램 방지 등)을 이 카탈로그 통제로 매핑하면, 별도 체크리스트 없이 진단 결과로 준수 근거를 보일 수 있다. 예: 접근 통제 ↔ S-025/S-028/S-045, 암호화 ↔ S-042/S-085/S-037, 접속기록 ↔ S-090.
- **실패 양상:** 기술 통제는 있는데 증빙이 없어 점검에서 미흡 판정.
- **신호:** 🟡 한국 사용자 + 개인정보 신호 → 매핑 리포트 생성.
- **시나리오·수준:** S L1 이상 (한국 대상)
- **처방:** 공통: 리포트에 "안전성 확보조치 매핑" 표 섹션 추가.
- **검증:** 매핑 항목별 통제 상태(met/unmet/unknown).
- **비용 영향:** 중립
- **출처:** https://www.law.go.kr/행정규칙/개인정보의안전성확보조치기준 (조문 제목 수준만 확인, 세부 매핑은 원문 재확인 필요)

---

## M. LLM 앱

### S-101 LLM API 키 노출·호출 한도 없음 (Denial of Wallet)
- **무엇/왜:** LLM 호출은 요청당 비용이 크고 사용량에 비례한다. 키가 클라이언트에 있거나(S-002), 서버 경유여도 사용자별 한도가 없으면 누군가 무제한 호출해 청구서를 키운다. OWASP는 이를 Unbounded Consumption(LLM10)으로 분류한다.
- **실패 양상:** 하룻밤 사이 수천 달러 청구, 공급자 계정 정지.
- **신호:** 🟢 `openai`/`@anthropic-ai/sdk`/`@google/generative-ai` 호출이 클라이언트 파일에 있음, 서버 호출 경로에 사용자별 레이트 리밋·토큰 상한(`max_tokens`)·입력 길이 제한 없음, 익명 사용자도 호출 가능. (COST-008과 연동)
- **시나리오·수준:** S L1 이상 (LLM 호출이 있으면)
- **처방:** 공통: 서버 경유, 사용자·IP별 한도, 입력 길이·`max_tokens` 상한, 공급자 콘솔 지출 한도·알림, 익명 호출에 CAPTCHA.
- **검증:** 한도 초과 시 429 테스트, 공급자 대시보드 한도 설정 확인(🔴).
- **비용 영향:** 감소 (남용 차단)
- **출처:** https://genai.owasp.org/llmrisk/llm102025-unbounded-consumption/ · https://firebase.google.com/docs/projects/api-keys (Gemini 키 노출 금지)

### S-102 프롬프트 인젝션 (직접·간접)
- **무엇/왜:** 사용자 입력이나 LLM이 읽는 외부 콘텐츠(웹페이지, 업로드 문서, 이메일)에 숨은 지시가 시스템 프롬프트를 뒤집는다. 완벽한 방지책은 아직 없으므로 피해 범위를 줄이는 설계가 핵심이다.
- **실패 양상:** 시스템 프롬프트·다른 사용자 데이터 유출, 의도하지 않은 도구 호출, 잘못된 출력을 그대로 실행.
- **신호:** 🟢 사용자 입력을 시스템 프롬프트에 문자열 연결, 외부 문서를 RAG로 넣으면서 구분자·출처 표시 없음, LLM 출력을 `eval`·SQL·셸·HTML에 그대로 사용(`dangerouslySetInnerHTML`).
- **시나리오·수준:** S L1 이상 (LLM이 있으면), 도구 호출이 있으면 S L2
- **처방:** 공통: 출력 형식을 코드로 검증(JSON 스키마), 외부 콘텐츠 분리 표시, 출력은 데이터로만 취급(실행 금지), 민감 데이터는 LLM 컨텍스트에 넣지 않음, 적대적 테스트.
- **검증:** 인젝션 테스트 세트로 회귀 테스트.
- **비용 영향:** 소폭 증가 (검증 단계)
- **출처:** https://genai.owasp.org/llmrisk/llm01-prompt-injection/

### S-103 과도한 에이전시 (LLM 도구의 권한 과다)
- **무엇/왜:** LLM에게 DB 쓰기, 메일 발송, 결제, 임의 URL 가져오기 도구를 주면 인젝션 한 번이 실제 행동이 된다. 도구는 최소로, 권한은 호출 사용자 권한으로, 고위험 동작은 사람 승인으로. 인가는 LLM이 아니라 백엔드가 한다.
- **실패 양상:** 인젝션으로 다른 사용자 데이터 삭제, 스팸 발송, SSRF(S-059).
- **신호:** 🟢 tool/function 정의에 `execute_sql`, `run_shell`, `send_email`, `fetch_url` 같은 범용 도구, 도구 실행이 서비스 계정(관리자) 권한, 승인 단계 없음.
- **시나리오·수준:** S L2 (도구 호출 LLM이 있으면 L2 조건)
- **처방:** 공통: 좁은 전용 도구, 사용자 범위 자격 증명(RLS 적용 클라이언트), 쓰기 동작 확인 단계, 도구별 레이트 리밋.
- **검증:** 인젝션 시나리오로 고위험 도구 호출 차단 확인.
- **비용 영향:** 중립
- **출처:** https://genai.owasp.org/llmrisk/llm062025-excessive-agency/

### S-104 LLM 공급자로 개인정보 전송
- **무엇/왜:** 대화·문서에 담긴 개인정보가 해외 LLM API로 나가면 국외 이전(S-093)이 되고, 공급자의 보관·학습 정책이 영향을 준다. 프롬프트 로깅 도구(LangSmith 등)도 같은 경로다.
- **실패 양상:** 처리방침 미기재 국외 이전, 공급자 측 보관으로 유출 범위 확대.
- **신호:** 🟢 사용자 프로필·주문 내역을 프롬프트에 포함하는 코드, LLM 관측 SDK 사용. 🟡 공급자 리전·데이터 보관 설정은 🔴.
- **시나리오·수준:** S L1 이상 (한국 사용자 + 개인정보 + LLM)
- **처방:** 공통: 프롬프트에 넣기 전 마스킹·가명처리, 필요한 필드만, 처리방침에 국외 이전·위탁 기재, 가능하면 국내 리전 엔드포인트.
- **검증:** 프롬프트 로그 샘플에서 PII 패턴 검사.
- **비용 영향:** 중립
- **출처:** https://www.privacy.go.kr/front/contents/cntntsView.do?contsNo=367 (국외 이전 요건) · https://genai.owasp.org/llmrisk/llm01-prompt-injection/ (민감 콘텐츠 필터링)

---

## 새 축·규칙 후보

### 1. S 축을 다섯 번째 시나리오로 추가
설계 §4의 `scenario: Literal["D", "T", "U", "C"]`에 `"S"`를 더한다. 다른 축과 같은 L0~L3 누적 구조를 쓰되, 두 가지가 다르다.
- **비용 필터 예외 목록:** S-001, S-002, S-009, S-010, S-015(비밀 노출, 데이터 접근 제어 누락)는 COST-009처럼 "절감 대상 아님"으로 고정한다. 이 항목들은 대부분 추가 비용이 없어서 비용 필터와 충돌하지도 않는다.
- **현재 수준 계산 시 "미확인" 비중이 크다:** 대시보드 설정(Supabase RLS 상태, Vercel 배포 보호, API 키 제한)은 저장소에 없다. 미확인을 미충족으로 치면 거의 모든 티어0 앱이 S L0이 된다. 그래서 S 축은 리포트에서 **"코드로 확인됨 / 플랫폼에서 확인 필요"를 나눠 보여주고**, 확인 방법(Supabase Security Advisor 실행 등)을 처방으로 낸다.

### 2. 필요 수준 규칙 (level) 후보

| ID | 조건 → 결정 | 근거 항목 |
|---|---|---|
| S-L0-001 | 인증 라이브러리·로그인 라우트 없음, 사용자 데이터 쓰기 없음 → S L0 | |
| S-L1-001 | 로그인·가입이 있거나 이메일·전화번호 등 개인정보 저장 (**기본값**) → S L1 | S-039~S-044 |
| S-L2-001 | 결제 SDK(토큰화), B2B 신호, 파일 업로드, 도구 호출 LLM, EU 대상 신호 → S L2 | S-058, S-062, S-097, S-098, S-103 |
| S-L3-001 | 카드 번호 필드 직접 처리, 주민번호·건강정보 컬럼, 공공 도메인 추론, ISMS 의무 가정 → S L3 | S-095~S-099 |

### 3. 다른 축과의 연결 규칙 후보
- **S×T:** 로그인 레이트 리밋(S-043)과 argon2 격리(T-CTL-008)는 같은 경로를 다룬다. S≥1이면 T-CTL-007의 "로그인 경로" 부분은 T 수준과 무관하게 필요하다(보안 이유).
- **S×D:** CMK(S-086)를 쓰면 키 손실이 D 축 장애 원인이 된다. S L3 + CMK이면 D 축에 "키 상태 알람" 통제를 추가한다. 반대로 S≤2이면 CMK는 과잉(COST 규칙).
- **S×TIER:** 공공 납품(S-096)이나 데이터 레지던시(S-094)면 서울 리전이 없는 티어0 서비스를 후보에서 제외한다. 바이브코더의 티어0 유지(TIER-005)를 막는 몇 안 되는 규칙이다.
- **S×COST:** S L1 앱에 WAF Bot Control·Shield Advanced·CMK·서비스 메시가 있으면 과잉 처방(축소)을 낸다.

### 4. 탐지기 확장 후보 (설계 §6.2)
| 탐지기 | 추가 사실 ID 예 |
|---|---|
| config | `secret.client_exposed`(NEXT_PUBLIC_/VITE_ + 비밀 키워드), `secret.service_role_in_client`, `secret.default_fallback`, `cookie.insecure_attrs`, `cors.reflect_with_credentials`, `debug.enabled_in_prod`, `proxy.trust_all` |
| schema | `baas.rls_missing`(Supabase 마이그레이션), `baas.security_definer_public`, `firebase.rules_open`, `pii.sensitive_column`(rrn, card_number, cvv) |
| code (semgrep) | `authz.idor_candidate`, `mass_assignment`, `redirect.open`, `ssrf.user_url_fetch`, `webhook.no_signature`, `jwt.decode_no_verify`, `hash.weak_password`, `llm.client_side_call`, `llm.no_user_quota`, `log.pii` |
| infra | `tf.db.public`, `tf.bucket.public`, `tf.sg.open_admin_port`, `tf.imds.v1_allowed`, `tf.iam.wildcard`, `tf.static_cloud_key`, `k8s.netpol.default_deny`, `k8s.psa.level`, `k8s.sa.automount`, `docker.user_root`, `docker.base_unpinned` |
| repo | `ci.actions_unpinned`, `ci.oidc`, `ci.dep_scan`, `ci.image_scan`, `repo.lockfile` |

외부 정적 도구(gitleaks, semgrep, checkov, trivy, kube-linter)의 결과를 사실로 가져오는 어댑터를 두면 규칙 수를 크게 줄일 수 있다. 이 도구들은 결정적이므로 설계 원칙 1(같은 사실 → 같은 판정)과 맞는다.

### 5. P4 검증 후보 (S 축)
- 교차 사용자 접근 테스트(IDOR·RLS): 두 계정으로 서로의 리소스 조회·수정 시도.
- 익명 접근 테스트: 공개 키만으로 Supabase 테이블·Storage, Firebase 경로 읽기 시도.
- 헤더 검사: HSTS, CSP, `Set-Cookie` 속성, CORS 반사.
- 위조 헤더 테스트: `X-Forwarded-For`, `X-User-Id`, `x-middleware-subrequest`를 넣어 레이트 리밋·인가 우회 시도.
- 로그인 대입 테스트: 실패 N회 후 429.
- 노출 경로 스캔: `/docs`, `/.git/HEAD`, `/.env`, `*.map`, `/admin`.

### 6. 이번에 확인하지 못한 것 (후속 조사)
- 한국 법령 원문: law.go.kr 페이지가 본문을 렌더링하지 않아 조문 제목만 확인했다. 안전성 확보조치 기준의 보관 기간·암호화 대상 수치는 원문 재확인이 필요하다.
- KISA(isms.kisa.or.kr) 접속 실패. CSAP→국정원 검증 전환은 언론 보도만 확인했다.
- GDPR은 EUR-Lex 원문을 열지 못해 비공식 정리 사이트를 인용했다.
- PCI DSS SAQ A 원문 PDF는 열지 않았고 PCI SSC 블로그만 확인했다.
