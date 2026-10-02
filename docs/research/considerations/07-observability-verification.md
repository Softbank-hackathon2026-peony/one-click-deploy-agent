# 관측·운영·검증 방법

이 문서는 infrafit 규칙집의 **O 축(관측·운영) 후보**와 **P4 검증 기법 카탈로그(V)**를 모은다. D/T/U/C·보안·비용의 기술 통제 자체는 다루지 않는다. 여기서 다루는 것은 "그 통제가 동작하는지 어떻게 보고(O), 어떻게 증명하고(V), 어떻게 운영하나"이다.
모든 항목은 설계 문서 §2-4 "필요한 만큼만"을 따른다. 필요 수준은 **최대 필요 수준**(D/T/U/C 중 가장 높은 값, §17.4) 또는 특정 시나리오 수준으로 적는다. 관측 장치도 비용이므로 과잉이면 축소 대상이다.
출처는 2026-10-01에 WebFetch로 직접 연 페이지만 URL로 적었다. 열지 못했거나 공식 1차 자료가 없는 항목은 "일반 원칙(출처 미확인)"으로 표시했다.

표기: 티어0 = 현재 플랫폼 유지(Vercel·Supabase 등), 티어1 = 관리형 컨테이너(Cloud Run·ECS Fargate), 티어2 = 쿠버네티스(GKE·EKS). 신호의 🟢 = 충족 신호, 🟡 = 부분·모호, 🔴 = 결함 신호.
예시 앱 근거는 `simple-web-app`(이하 SWA)의 실제 파일 경로로 적었다.

## 목차

**A. 관측·운영 요소 (O-001 ~ O-072)**
- A1. 로그 (O-001 ~ O-012)
- A2. 지표 (O-013 ~ O-030)
- A3. 트레이스·에러 추적·프로파일링 (O-031 ~ O-036)
- A4. SLI/SLO와 알림 (O-037 ~ O-046)
- A5. 외부·사용자 관점 관측 (O-047 ~ O-051)
- A6. 헬스 체크와 앱 런타임 계약 (O-052 ~ O-058)
- A7. 운영 준비도(사람·절차·주변 감시) (O-059 ~ O-072)

**B. 검증 방법 요소 (V-001 ~ V-063)**
- B1. 부하 테스트 종류 (V-001 ~ V-007)
- B2. 부하 모델·생성기·데이터 (V-008 ~ V-020)
- B3. 결과 해석 (V-021 ~ V-026)
- B4. 혼돈 실험 설계 (V-027 ~ V-031)
- B5. 장애 주입 종류 (V-032 ~ V-045)
- B6. 배포·정합성·기능 검증 (V-046 ~ V-055)
- B7. 복구·운영 절차 검증 (V-056 ~ V-063)

**새 축·규칙 후보** (문서 끝)

---

# A. 관측·운영 요소

## A1. 로그

### O-001 로그를 stdout으로 내보내기
- **무엇/왜:** 프로세스는 로그를 파일이 아니라 stdout/stderr 이벤트 스트림으로 쓰고, 수집·보관은 실행 환경이 맡는다. 컨테이너·서버리스 플랫폼의 로그 수집기는 stdout만 자동으로 가져간다.
- **실패 양상:** 컨테이너 안 파일에 쓴 로그는 Pod 재시작·스케일 인과 함께 사라지고, 디스크를 채워 장애를 만든다(임시 저장소 축출). 장애 시 볼 로그가 없다.
- **신호:** 🔴 `logging.FileHandler`, `winston.transports.File`, `fs.createWriteStream('*.log')`, `RotatingFileHandler` (탐지 사실 `ops.file_logging`) / 🟢 `StreamHandler(sys.stdout)`, `console.log`, pino 기본 출력 (SWA `services/board/src/board/observability.py`의 `logging.StreamHandler(sys.stdout)`) / 🟡 파일과 stdout 동시 기록
- **필요 수준:** 모든 수준(L0 포함). 비용이 거의 없고 이후 모든 관측의 전제다.
- **처방:** 티어0: 플랫폼 로그 뷰어가 stdout을 받으므로 파일 핸들러만 제거. 티어1: Cloud Run·ECS(awslogs 드라이버)는 stdout 자동 수집. 티어2: 노드 수집기(GKE 기본 Cloud Logging, EKS는 Fluent Bit DaemonSet)로 stdout 수집.
- **검증:** 배포 후 요청 1건을 보내고 해당 로그 줄이 플랫폼 로그 뷰어에 1분 안에 나타나는지 확인. Pod를 지운 뒤에도 과거 로그가 조회되는지 확인.
- **비용 영향:** 중립(수집 자체는 무료 등급 안이 많음). 파일 로그로 인한 디스크 비용·장애는 감소.
- **출처:** https://12factor.net/logs ("each running process writes its event stream, unbuffered, to stdout", 2026-10-01 확인) ⚠️출처부적격

### O-002 구조화 로그(JSON 한 줄)
- **무엇/왜:** 로그 한 줄을 JSON 객체 하나로 쓰면 수집기가 필드로 색인해서 `status=500 AND route=/api/x` 같은 질의가 가능하다. 텍스트 로그는 검색만 되고 집계가 어렵다.
- **실패 양상:** 장애 중 "어느 라우트에서, 어떤 사용자군에서 오류가 났나"를 정규식으로 뒤져야 한다. 로그 기반 지표(오류 수)를 만들 수 없다.
- **신호:** 🟢 `JsonFormatter`, `python-json-logger`, `structlog`, `pino`, `winston.format.json()`, nginx `log_format ... escape=json` (SWA perf 브랜치 `nginx/default.conf.template`의 `log_format perf escape=json`) / 🔴 `print()`·`console.log` 문자열 결합 로그만 존재 / 🟡 JSON이지만 필드 이름이 서비스마다 다름(`msg` vs `message`, `ts` vs `time`)
- **필요 수준:** 최대 필요 수준 L1 이상. L0(사내 고정 사용자, 영속 데이터 없음)이면 텍스트 로그로도 충분.
- **처방:** 티어0: 플랫폼이 JSON을 파싱하는지 확인하고 로거만 교체. 티어1: Cloud Run은 stdout의 한 줄 JSON을 `jsonPayload`로 받는다(`severity` 필드를 쓰면 심각도로 인식). ECS는 CloudWatch Logs Insights가 JSON 필드를 자동 인식. 티어2: 수집기 파서 설정 + 같은 필드 규약을 서비스 공통 라이브러리로.
- **검증:** 로그 뷰어에서 JSON 필드(`route`, `status`, `request_id`)로 필터 질의가 되는지 확인. 여러 줄 스택 트레이스가 한 레코드로 들어오는지 확인(O-011).
- **비용 영향:** 소폭 증가(필드 이름만큼 바이트 증가). 장애 조사 시간은 크게 감소.
- **출처:** https://docs.cloud.google.com/logging/docs/structured-logging (jsonPayload vs textPayload, Cloud Run·GKE 통합 에이전트가 stdout을 구조화 로그로 전송, 2026-10-01 확인)

### O-003 로그 레벨과 심각도 필드
- **무엇/왜:** 레벨(DEBUG/INFO/WARN/ERROR)을 환경변수로 바꿀 수 있어야 하고, 플랫폼이 이해하는 심각도 필드로 내보내야 오류 로그만 골라 알림·지표로 만들 수 있다.
- **실패 양상:** 프로덕션에서 DEBUG가 켜져 로그 비용이 폭증하거나, 반대로 모든 로그가 INFO로 들어와 오류만 고를 수 없다. stderr 전체가 ERROR로 분류되는 플랫폼에서 경고가 오류로 오인된다.
- **신호:** 🟢 `LOG_LEVEL` 환경변수 참조 + `root.setLevel(level)` (SWA `configure_logging(level)`) / 🔴 레벨 하드코딩 `DEBUG`, `logging.basicConfig(level=logging.DEBUG)` / 🟡 레벨 필드 이름이 플랫폼 규약(`severity`)과 다름
- **필요 수준:** 최대 필요 수준 L1 이상.
- **처방:** 티어0/1/2 공통: `LOG_LEVEL` 기본 INFO, GCP는 `severity` 키로 매핑, AWS는 레벨 필드로 Logs Insights 필터.
- **검증:** `LOG_LEVEL=WARN`으로 재배포 후 INFO 로그가 사라지는지, ERROR 로그만 필터하는 질의가 결과를 내는지 확인.
- **비용 영향:** 감소(불필요한 DEBUG 차단).
- **출처:** 일반 원칙(출처 미확인). 심각도 필드 인식은 https://docs.cloud.google.com/logging/docs/structured-logging 문서 범위이나 `severity` 키 세부는 이번에 직접 확인하지 못함. ⚠️근거없음

### O-004 요청 ID 생성·전파·응답 헤더
- **무엇/왜:** 진입점(LB·nginx·앱)에서 요청마다 ID를 만들고, 하위 서비스 호출에 전달하고, 모든 로그 줄과 응답 헤더에 싣는다. 사용자가 보고한 오류 한 건을 로그 전체에서 바로 찾을 수 있다.
- **실패 양상:** "아까 저장이 안 됐어요" 신고를 받아도 수천 줄 중 어느 줄인지 모른다. 서비스 간 로그를 이을 수 없다.
- **신호:** 🟢 nginx `add_header X-Request-ID $request_id always;` + 앱 미들웨어가 `x-request-id`를 받아 contextvar에 넣고 응답에 되돌림 (SWA `nginx/default.conf.template`, `observability.py`의 `RequestContextMiddleware`, 테스트 `test_request_id_is_echoed`) / 🟡 ID는 만들지만 하위 HTTP 클라이언트 호출에 전달하지 않음 / 🔴 요청 ID 개념 없음
- **필요 수준:** 최대 필요 수준 L1 이상. 서비스가 2개 이상이면 L1에서도 필수.
- **처방:** 티어0: 플랫폼 요청 ID(Vercel `x-vercel-id` 등)를 로그에 싣기. 티어1: Cloud Run은 `X-Cloud-Trace-Context`/`traceparent`, ALB는 `X-Amzn-Trace-Id`를 받아 로그 필드로. 티어2: 인그레스(nginx `$request_id`)에서 생성. 장기적으로는 O-005의 traceparent로 통일.
- **검증:** 요청 1건에 임의 ID를 넣어 보내고, 진입점·각 서비스 로그에서 같은 ID가 모두 검색되는지 확인. 응답 헤더에 같은 ID가 있는지 확인.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인). 상관 키를 로그에 넣는 원리는 https://opentelemetry.io/docs/specs/otel/logs/ 의 TraceId·SpanId 상관 설명과 같다. ⚠️근거없음

### O-005 W3C traceparent / OpenTelemetry 컨텍스트 전파
- **무엇/왜:** 표준 헤더 `traceparent`(`version-traceid-parentid-flags`)로 트레이스 컨텍스트를 서비스 사이에 넘기면, 벤더가 달라도 한 요청의 전 구간이 이어진다. OpenTelemetry의 기본 전파기가 W3C TraceContext다.
- **실패 양상:** 자체 `X-Request-ID`만 쓰면 관리형 LB·APM·외부 SaaS의 트레이스와 이어지지 않는다. 비동기 큐를 건너면 컨텍스트가 끊긴다.
- **신호:** 🟢 `opentelemetry-*` 의존성 + `TraceContextTextMapPropagator`, `@opentelemetry/auto-instrumentations-node`, 큐 메시지 속성에 `traceparent` 저장 / 🟡 `X-Request-ID`만 있음(SWA 현재 상태) / 🔴 서비스 3개 이상인데 전파 수단 없음
- **필요 수준:** 최대 필요 수준 L2 이상이고 서비스(배포 단위)가 2개 이상일 때. 단일 서비스 L1에는 과잉.
- **처방:** 티어0: 플랫폼 내장 트레이싱(Vercel OTel 통합 등) 우선. 티어1: OTel SDK 자동 계측 + Cloud Trace / X-Ray(ADOT). 티어2: OTel Collector를 DaemonSet/게이트웨이로, 인그레스에서 traceparent 생성.
- **검증:** 진입 요청에 `traceparent`를 넣어 보내고, 트레이스 뷰에서 같은 trace-id 아래 모든 서비스 스팬이 하나의 트리로 보이는지 확인. 큐를 거치는 쓰기 경로도 워커 스팬이 이어지는지 확인.
- **비용 영향:** 증가(트레이스 수집·저장). 샘플링(O-032)으로 통제.
- **출처:** https://www.w3.org/TR/trace-context/ (W3C Recommendation 2021-11-23, traceparent 4개 필드), https://opentelemetry.io/docs/concepts/context-propagation/ (기본 전파기는 W3C TraceContext), 2026-10-01 확인

### O-006 로그와 트레이스 상관(로그에 trace_id 싣기)
- **무엇/왜:** 로그 레코드에 trace_id·span_id를 넣으면 트레이스에서 해당 로그로, 로그에서 트레이스로 바로 이동한다.
- **실패 양상:** 느린 트레이스를 찾아도 그때 무슨 예외가 났는지 로그를 시간대로 추정해야 한다.
- **신호:** 🟢 로거 포매터에 `trace_id`/`span_id` 필드, `opentelemetry-instrumentation-logging`, GCP `logging.googleapis.com/trace` 필드 / 🟡 request_id만 로그에 있음 / 🔴 트레이싱은 있는데 로그에 상관 키 없음
- **필요 수준:** O-005를 도입한 경우(최대 필요 수준 L2 이상)에만.
- **처방:** 티어1: Cloud Run은 trace 필드를 로그에 넣으면 Logs Explorer와 Trace가 연결된다. ECS는 ADOT + X-Ray trace id 필드. 티어2: OTel 로그 브리지.
- **검증:** 임의 트레이스 하나를 열어 "관련 로그" 링크로 같은 요청의 로그가 나오는지 확인.
- **비용 영향:** 중립(필드 몇 바이트).
- **출처:** https://opentelemetry.io/docs/specs/otel/logs/ ("including TraceId and SpanId in the LogRecords", 2026-10-01 확인)

### O-007 로그의 PII·비밀 마스킹
- **무엇/왜:** 비밀번호, 세션 ID, 토큰, 카드·계좌 정보, 주민·여권 번호, 건강 정보는 로그에 남기지 않는다. 로그는 접근 권한이 넓고 보존이 길어서 유출 경로가 된다.
- **실패 양상:** 요청 본문 전체를 로깅하는 디버그 코드가 프로덕션에 남아 비밀번호가 평문으로 쌓인다. 에러 추적 SaaS로 쿠키·헤더가 넘어간다.
- **신호:** 🔴 `logger.info(request.body)`, `log(req.headers)`, `console.log(user)`, Sentry `send_default_pii=True`, 로그에 `password`·`authorization`·`cookie` 키 / 🟢 로거 필터·`before_send` 스크러빙, 허용 목록 방식 필드 로깅 / 🟡 nginx 로그에 쿼리스트링 전체(`$request_uri`)를 남기는데 쿼리에 토큰이 올 수 있음 (SWA perf 로그의 `"uri":"$request_uri"`)
- **필요 수준:** 개인정보를 저장하면 모든 수준(C≥1 또는 가입 기능 존재). 결제·의료면 L1부터 자동 마스킹까지.
- **처방:** 티어0/1/2 공통: 코드에서 허용 목록 로깅 + 에러 추적 SDK 스크러빙. 추가로 AWS는 CloudWatch Logs 데이터 보호 정책(수집 시점 마스킹, `logs:Unmask` 권한자만 원문), GCP는 Sensitive Data Protection 연동.
- **검증:** 테스트 계정으로 가입·로그인·결제 흐름을 실행하고 로그·에러 추적에서 해당 비밀번호·이메일·토큰 문자열을 검색해 0건인지 확인. AWS는 `LogEventsWithFindings` 지표가 0인지.
- **비용 영향:** 소폭 증가(데이터 보호 정책은 스캔 과금). 유출 사고 비용은 크게 감소.
- **출처:** https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html (제외할 데이터 목록), https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/mask-sensitive-log-data.html (수집 시점 마스킹, 정책 설정 이전 로그는 마스킹 안 됨), https://docs.sentry.io/platforms/python/data-management/sensitive-data/ (SDK에서 보내기 전에 스크러빙 권장), 2026-10-01 확인 ⚠️출처확인필요

### O-008 로그 주입 방지와 외부 입력 상관 ID 검증
- **무엇/왜:** 사용자 입력(헤더·경로·본문)을 로그에 넣을 때 CR/LF·구분자를 제거하거나 JSON 인코딩한다. 클라이언트가 보낸 `X-Request-ID`도 외부 입력이므로 길이·문자 집합을 제한한다.
- **실패 양상:** 공격자가 줄바꿈을 넣어 가짜 로그 줄을 만들거나, 매우 긴 헤더로 로그 비용을 키운다. 상관 ID 위조로 조사를 오도한다.
- **신호:** 🟡 `request.headers.get("x-request-id") or uuid4()`처럼 클라이언트 값을 그대로 신뢰 (SWA `observability.py` 50행) / 🟢 JSON 포매터 사용(줄바꿈이 이스케이프됨), 정규식 `^[A-Za-z0-9-]{1,64}$` 검사 / 🔴 문자열 포매팅으로 사용자 입력을 텍스트 로그에 삽입
- **필요 수준:** 최대 필요 수준 L1 이상(공개 서비스).
- **처방:** 공통: 구조화 로거로 인코딩, 외부 상관 ID는 형식 검사 후 불합격이면 새로 발급. 신뢰 경계(인그레스)에서만 ID를 생성하고 외부 값은 버리는 것도 방법.
- **검증:** `X-Request-ID: a%0d%0afake` 및 10KB 길이 헤더로 요청 후 로그가 한 레코드이고 ID가 새로 발급됐는지 확인.
- **비용 영향:** 중립.
- **출처:** https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html ("sanitization on all event data to prevent log injection attacks e.g. carriage return (CR), line feed (LF)", 2026-10-01 확인)

### O-009 로그 보존 기간 명시
- **무엇/왜:** 로그 보존 기간은 조사 가능 기간이자 비용이다. AWS CloudWatch Logs는 기본이 **무기한 보존**이고, GCP `_Default` 버킷은 기본 30일(1~3650일 조정)이다. IaC에서 명시해야 한다.
- **실패 양상:** AWS에서 보존 기간을 안 정하면 로그 저장 비용이 매달 누적된다. 반대로 짧게 잡으면 사고 2주 뒤 감사 요청에 답할 수 없다.
- **신호:** 🔴 Terraform `aws_cloudwatch_log_group`에 `retention_in_days` 없음, ECS `awslogs-create-group`으로 자동 생성된 로그 그룹 / 🟢 `retention_in_days = 30` 등 명시, GCP `google_logging_project_bucket_config.retention_days` / 🟡 결제·감사 데이터인데 7일
- **필요 수준:** 최대 필요 수준 L1 이상. 기본값 권장: L1 14~30일, L2 30~90일, 결제·감사 로그(C=L3)는 규정 기간.
- **처방:** 티어0: 플랫폼 보존 기간 확인(요금제별로 짧음 → 필요하면 외부 드레인). 티어1/2: 로그 그룹·버킷 보존 기간을 IaC로, 장기 보관은 오브젝트 스토리지 아카이브.
- **검증:** IaC plan 결과에 모든 로그 그룹의 보존 값이 있는지 lint. 배포 후 `aws logs describe-log-groups`에서 `retentionInDays` 없는 그룹 0개.
- **비용 영향:** 감소(무기한 → 기한). 보존 기간 연장 시 증가.
- **출처:** https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Working-with-log-groups-and-streams.html ("By default, log data is stored in CloudWatch Logs indefinitely"), https://docs.cloud.google.com/logging/quotas (`_Default` 30일, `_Required` 400일), 2026-10-01 확인

### O-010 로그 볼륨 통제(헬스 체크 제외·샘플링)
- **무엇/왜:** 헬스 체크·지표 수집·정적 파일 요청 로그는 양만 많고 쓸모가 적다. 성공 요청은 샘플링하고 오류·느린 요청은 전부 남긴다. 로그 수집은 GB 단위 과금이다.
- **실패 양상:** 프로브가 초당 수 번 찍히는 로그가 전체의 대부분이 되어 비용을 키우고 진짜 로그를 묻는다. 폭증 시 로그 수집 자체가 병목·비용 폭탄이 된다.
- **신호:** 🟢 nginx `location = /nginx-health { access_log off; }` (SWA), 앱 미들웨어에서 `/healthz` 로그 제외, 수집기 exclusion filter / 🔴 프로브 주기 1~5초 + 모든 요청 INFO 로그 + 고트래픽(T≥2) / 🟡 오류도 함께 샘플링해서 버림
- **필요 수준:** T≥2(트래픽이 큼)에서 필요. T≤1이면 무료 등급 안이라 신경 쓸 필요 적음.
- **처방:** 티어0: 플랫폼 로그 드레인 요금 확인. 티어1: GCP 로그 제외 필터(무료 할당 프로젝트당 월 50GiB), AWS는 표준 수집 GB당 $0.50(us-east-1)이므로 Infrequent Access 로그 클래스 검토. 티어2: Fluent Bit 필터로 프로브 로그 드롭.
- **검증:** P4 소크 동안 시간당 로그 바이트를 측정하고 피크 트래픽 기준 월 로그 비용을 환산해 리포트에 표시. 오류 요청이 샘플링으로 빠지지 않는지 오류 주입으로 확인.
- **비용 영향:** 감소.
- **출처:** https://aws.amazon.com/cloudwatch/pricing/ (표준 로그 수집 GB당 $0.50, 무료 5GB), https://cloud.google.com/stackdriver/pricing (Cloud Logging 프로젝트당 월 50GiB 무료), 2026-10-01 확인

### O-011 예외·스택 트레이스를 한 레코드로
- **무엇/왜:** 여러 줄 스택 트레이스를 텍스트로 찍으면 수집기가 줄마다 별도 레코드로 쪼갠다. 예외는 JSON 필드(`exc`) 하나에 담는다.
- **실패 양상:** 오류 하나가 30개 레코드로 흩어져 검색·집계·알림이 깨지고 레코드 수 과금이 늘어난다.
- **신호:** 🟢 포매터가 `formatException`을 JSON 필드로 (SWA `payload["exc"]`) / 🔴 `traceback.print_exc()`, `console.error(err.stack)` 텍스트 출력, uvicorn·gunicorn 기본 로거가 JSON 포매터를 우회 / 🟡 앱 로그는 JSON인데 프레임워크·서버 로그는 텍스트
- **필요 수준:** 최대 필요 수준 L1 이상.
- **처방:** 공통: 프레임워크·WSGI/ASGI 서버 로거까지 같은 JSON 핸들러로 통일(uvicorn `log_config`, Node는 pino-http).
- **검증:** 의도적으로 500을 일으키는 테스트 요청 후 로그 뷰어에서 한 레코드에 스택 전체가 들어 있는지 확인.
- **비용 영향:** 감소(레코드 수).
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### O-012 계층별 타이밍 액세스 로그(LB·프록시·앱)
- **무엇/왜:** 프록시 로그에 전체 처리 시간(`$request_time`), 업스트림 연결 시간(`$upstream_connect_time`), 업스트림 응답 시간(`$upstream_response_time`)을 함께 남기면 "느림"이 네트워크·프록시 대기·앱 중 어디서 생겼는지 가를 수 있다.
- **실패 양상:** p95가 나빠졌을 때 앱 지표는 정상이라 원인을 못 찾는다(실제로는 프록시 큐잉이나 커넥션 수립 지연).
- **신호:** 🟢 nginx `log_format`에 `$request_time`, `$upstream_response_time`, `$upstream_connect_time`, auth_request 시간 (SWA perf 브랜치 `rt`/`urt`/`uct`/`vt`) / 🟢 ALB 액세스 로그 활성화(`access_logs { enabled = true }`) / 🔴 기본 combined 포맷만
- **필요 수준:** T≥2 또는 U≥2에서 필요. L1에는 LB 기본 지표로 충분.
- **처방:** 티어0: 해당 없음(플랫폼 지표 사용). 티어1: ALB 액세스 로그(S3) 또는 Cloud Run 요청 로그의 `latency` 필드. 티어2: 인그레스 nginx `log_format` 확장.
- **검증:** P4 부하 중 `rt - urt` 분포를 계산해 프록시 대기 시간이 따로 보이는지 확인. 앱 Server-Timing 합계(O-024)와 `urt`가 대체로 일치하는지 교차 확인.
- **비용 영향:** 소폭 증가(로그 필드).
- **출처:** https://nginx.org/en/docs/http/ngx_http_upstream_module.html (`$upstream_response_time`, `$upstream_connect_time` 정의, 2026-10-01 확인)

## A2. 지표

### O-013 RED 지표(요청률·오류율·지연)
- **무엇/왜:** 요청을 받는 모든 서비스는 라우트별 요청 수(Rate), 오류 수(Errors), 지연 분포(Duration)를 낸다. SLO·알림·용량 판단의 원재료다.
- **실패 양상:** "느려졌다"는 사용자 신고로만 장애를 안다. HPA·카나리·P4가 볼 지표가 없다.
- **신호:** 🟢 `http_requests_total{method,route,status}` Counter + `http_request_duration_seconds` Histogram (SWA `observability.py`), OTel `http.server.request.duration` / 🟡 LB·플랫폼 기본 지표만 있음(라우트 구분 없음) / 🔴 아무 지표 없음
- **필요 수준:** L0~L1: 플랫폼·LB 기본 지표(요청 수·5xx·지연)로 충족. L2 이상: 앱 수준 라우트별 RED.
- **처방:** 티어0: 플랫폼 분석(Vercel Observability 등). 티어1: Cloud Run 기본 요청 지표 / ALB `HTTPCode_Target_5XX_Count`·`TargetResponseTime`, L2부터 OTel·Prometheus 클라이언트. 티어2: Prometheus(관리형 GMP·AMP) 스크레이프.
- **검증:** 알려진 개수의 요청(예: 200건 성공, 10건 500)을 보내고 지표 증가량이 정확히 일치하는지 확인(SWA `test_metrics_and_request_id` 방식).
- **비용 영향:** L2 이상에서 증가(시계열 수 과금). L1은 플랫폼 기본 지표라 무료.
- **출처:** https://opentelemetry.io/docs/specs/semconv/http/http-metrics/ (`http.server.request.duration` 히스토그램, 2026-10-01 확인). "RED"라는 이름 자체는 일반 원칙(출처 미확인). ⚠️근거없음

### O-014 네 가지 골든 시그널(지연·트래픽·오류·포화)
- **무엇/왜:** 사용자 대면 시스템은 지연, 트래픽, 오류, 포화 네 가지만 봐도 대부분의 문제를 잡는다. 포화(얼마나 꽉 찼나)는 RED에 없는 앞선 경고다.
- **실패 양상:** 오류율이 오르기 전 포화(풀 대기, 큐 길이, CPU 스로틀링) 신호를 놓쳐 미리 증설하지 못한다.
- **신호:** 🟢 RED + 포화 지표(커넥션 풀 대기, 큐 길이, 이벤트 루프 지연, CPU 스로틀) / 🟡 RED만 있음
- **필요 수준:** 최대 필요 수준 L2 이상에서 네 가지 모두. L1은 트래픽·오류·지연(플랫폼 기본)만.
- **처방:** 공통: 서비스마다 대시보드 첫 줄에 네 신호 고정(O-059).
- **검증:** P4 스트레스 테스트에서 포화 지표가 오류율보다 먼저 오르는지(선행 지표로 쓸 수 있는지) 시계열로 확인.
- **비용 영향:** 소폭 증가.
- **출처:** https://sre.google/sre-book/monitoring-distributed-systems/ (네 가지 골든 시그널 정의, 2026-10-01 확인)

### O-015 USE 자원 지표(사용률·포화·오류)
- **무엇/왜:** 자원(CPU, 메모리, 디스크, 네트워크, 커넥션 풀, 스레드 풀)마다 사용률·포화·오류를 본다. 원인 분석용이고 알림용이 아니다.
- **실패 양상:** 지연이 올라도 어떤 자원이 병목인지 모른다. CPU limit 스로틀링, 메모리 한도 근접을 놓쳐 OOMKilled로 이어진다.
- **신호:** 🟢 컨테이너 CPU·메모리·스로틀(`container_cpu_cfs_throttled_periods_total`), 노드 지표 수집 / 🟡 CPU만 봄 / 🔴 k8s인데 metrics-server조차 불안정(SWA 로컬 부하 시 HPA 지표 `<unknown>`)
- **필요 수준:** 최대 필요 수준 L1 이상(플랫폼 기본), 자원 단위 세부는 L2 이상.
- **처방:** 티어0: 플랫폼 제공 범위만. 티어1: Cloud Run·ECS 기본 CPU/메모리 사용률(무료). 티어2: GKE 시스템 지표 / EKS Container Insights(유료) 또는 관리형 Prometheus + kube-state-metrics.
- **검증:** P4에서 StressChaos(V-040)로 CPU를 채웠을 때 사용률·스로틀 지표가 해당 Pod에서 올라가는지 확인.
- **비용 영향:** 티어2에서 증가(Container Insights·시계열).
- **출처:** https://www.brendangregg.com/usemethod.html ("For every resource, check utilization, saturation, and errors", 2026-10-01 확인) ⚠️출처부적격

### O-016 지연은 히스토그램으로(평균 금지, 버킷 설계)
- **무엇/왜:** 평균 지연은 꼬리 지연을 숨긴다. 지연은 버킷 히스토그램으로 모아야 여러 인스턴스를 합쳐 백분위를 계산할 수 있다. Summary의 미리 계산된 분위수는 인스턴스 간 평균을 낼 수 없다.
- **실패 양상:** 평균 100ms인데 1%가 5초인 상황을 놓친다. Pod별 p95를 평균 내서 틀린 숫자로 SLO를 판정한다. 버킷이 SLO 경계(예: 300ms)와 맞지 않아 판정이 부정확하다.
- **신호:** 🟢 `Histogram` + SLO 임계 근처 버킷 / 🔴 `Summary`의 quantile을 `avg()`로 합침, 평균만 기록(`Gauge` last latency) / 🟡 기본 버킷인데 SLO 임계(예: 300ms, 1s)가 버킷 경계가 아님
- **필요 수준:** 최대 필요 수준 L2 이상(지연 SLO가 생기는 수준).
- **처방:** 공통: 히스토그램 + SLO 임계를 버킷 경계로 추가. OTel 권장 버킷 `[0.005 ... 10]`초에 SLO 값 포함 여부 확인. 가능하면 네이티브/지수 히스토그램.
- **검증:** 알려진 분포(예: 10%를 1초 지연시키는 HTTPChaos)로 부하를 걸고 `histogram_quantile` 결과와 부하 생성기(k6)의 p95가 버킷 오차 안에서 일치하는지 확인.
- **비용 영향:** 소폭 증가(버킷 수 × 라벨 조합).
- **출처:** https://prometheus.io/docs/practices/histograms/ ("aggregating the precomputed quantiles from a summary rarely makes sense"), https://opentelemetry.io/docs/specs/semconv/http/http-metrics/ (권장 버킷), https://sre.google/sre-book/monitoring-distributed-systems/ (평균 vs 꼬리), 2026-10-01 확인

### O-017 지표 카디널리티 통제(라우트 템플릿, 무한 라벨 금지)
- **무엇/왜:** 라벨 값 조합 하나가 시계열 하나다. 실제 URL 경로·사용자 ID·이메일을 라벨로 쓰면 시계열이 폭발해 수집기가 죽거나 요금이 폭증한다. 라벨은 라우트 템플릿(`/posts/{id}`)처럼 유한해야 한다.
- **실패 양상:** 크롤러가 무작위 경로를 두드릴 때마다 새 시계열이 생겨 Prometheus 메모리 부족, 관리형 지표 요금 폭증.
- **신호:** 🟢 `request.scope["route"].path` 같은 템플릿 사용 + 매칭 안 되면 `"unmatched"` (SWA `_route_template`) / 🔴 `labels(path=request.url.path)`, `labels(user_id=...)`, `req.originalUrl`을 라벨로 / 🟡 status 라벨에 원시 코드 전체(괜찮음) + 에러 메시지 문자열 라벨(위험)
- **필요 수준:** 앱 지표를 내는 모든 수준(L2 이상에서 보통 도입).
- **처방:** 공통: 라벨 허용 목록, 경로는 템플릿만. 티어1/2: 수집 단계에서 라벨 드롭(relabel), 관리형 지표 시계열 수 알림.
- **검증:** P4에서 무작위 경로 1만 개로 요청한 뒤 `count({__name__="http_requests_total"})` 시계열 수가 늘지 않는지 확인.
- **비용 영향:** 감소(폭발 방지). CloudWatch 사용자 지표는 지표당 월 $0.30(첫 1만 개)이므로 직접적.
- **출처:** https://prometheus.io/docs/practices/naming/ ("every unique combination of key-value label pairs represents a new time series"), https://opentelemetry.io/docs/specs/semconv/http/http-metrics/ (`http.route`는 저카디널리티, URI 경로로 대체 금지), https://aws.amazon.com/cloudwatch/pricing/, 2026-10-01 확인

### O-018 DB 커넥션 풀 지표
- **무엇/왜:** 풀의 사용 중·유휴·대기 수와 대기 시간, 획득 타임아웃 수를 낸다. T-CTL-003(인스턴스 × 풀 ≤ max_connections)이 실제로 맞는지 운영 중에 보는 유일한 방법이다.
- **실패 양상:** 스케일 아웃 후 DB 커넥션 고갈로 전체가 멈추는데, 앱 지표에는 "지연 증가"로만 보인다.
- **신호:** 🟢 SQLAlchemy pool 이벤트 계측, `pg_stat_activity` 수 수집, RDS `DatabaseConnections` 알림 / 🔴 풀 크기 설정 없음 + 커넥션 지표 없음 / 🟡 DB 쪽 연결 수만 보고 앱 쪽 대기는 안 봄
- **필요 수준:** T≥2 또는 D≥2 (풀러가 필요해지는 수준). L3는 의존성별 상태 지표로 필수(§17.4).
- **처방:** 티어0: Supabase 대시보드 연결 수. 티어1: RDS `DatabaseConnections`·Cloud SQL `num_backends` 지표 + max_connections의 80% 알림. 티어2: 앱 풀 지표 + PgBouncer 지표(`cl_waiting`).
- **검증:** P4 스파이크 중 DB 연결 수가 `max_instances × pool_size` 예측과 일치하는지, 소크 동안 단조 증가(누수)하지 않는지 확인(§17.3 판정 항목).
- **비용 영향:** 소폭 증가.
- **출처:** 일반 원칙(출처 미확인). `max_connections` 근거는 설계 문서 S8(이번 작업에서 재확인 안 함). ⚠️근거없음

### O-019 느린 쿼리와 쿼리별 통계
- **무엇/왜:** 쿼리 텍스트 단위로 호출 수·총 시간·평균 시간을 모으면 "어떤 쿼리가 DB 시간을 먹나"를 바로 안다. Postgres는 `pg_stat_statements`(공유 메모리, 재시작 필요)와 `log_min_duration_statement`(기본 -1, 꺼짐)를 쓴다.
- **실패 양상:** 데이터가 늘며 인덱스 없는 쿼리가 서서히 느려지는데 원인 쿼리를 모른다.
- **신호:** 🟢 Terraform 파라미터 그룹에 `shared_preload_libraries = pg_stat_statements`, `log_min_duration_statement` 설정, RDS Performance Insights / Cloud SQL Query Insights 활성화 / 🔴 DB 있음 + 아무것도 없음
- **필요 수준:** D≥1 또는 C≥1이고 T≥2. 작은 L1 서비스는 관리형 기본 대시보드로 충분.
- **처방:** 티어0: Supabase 쿼리 성능 화면. 티어1: Cloud SQL Query Insights / RDS Performance Insights(무료 보존 기간 범위). 티어2: 동일 + `pg_stat_statements` 익스포터.
- **검증:** P4 부하 후 상위 10개 쿼리 목록이 나오는지, 의도적으로 넣은 느린 쿼리(`pg_sleep`)가 로그에 찍히는지 확인.
- **비용 영향:** 소폭 증가(로그량·Insights 장기 보존 유료).
- **출처:** https://www.postgresql.org/docs/current/pgstatstatements.html (shared_preload_libraries 필요, 재시작), https://www.postgresql.org/docs/current/runtime-config-logging.html (`log_min_duration_statement` 기본 -1), 2026-10-01 확인

### O-020 큐 길이·가장 오래된 메시지 나이·DLQ 크기
- **무엇/왜:** 큐는 길이보다 **가장 오래된 메시지의 나이(lag)**가 사용자 체감과 직결된다. DLQ(실패 메시지) 크기는 조용한 데이터 유실 신호다.
- **실패 양상:** 워커가 죽거나 느려져도 API는 202를 계속 돌려주므로 아무도 모른다. DLQ에 쌓인 글·주문이 영영 처리되지 않는다.
- **신호:** 🟢 `queue_length`, `queue_lag_seconds`, `dlq_size` 게이지 (SWA `worker_metrics.py`), SQS `ApproximateAgeOfOldestMessage` 알림, KEDA 스케일러 / 🔴 큐 사용(BullMQ·Celery·SQS) + 워커 지표 없음 / 🟡 길이만 있고 나이·DLQ 없음
- **필요 수준:** 비동기 큐가 있으면(C≥2 신호) L2부터. T=L3(큐 + 백프레셔)에서는 필수.
- **처방:** 티어1: SQS·Pub/Sub 기본 지표(무료)로 나이·DLQ 알림. 티어2: 워커 `/metrics` + KEDA 같은 지표로 확장(T-CTL-010).
- **검증:** P4에서 워커를 0으로 줄이고(또는 Pod kill) 쓰기 부하를 건 뒤 lag 지표가 오르고 알림이 오는지, 워커 복구 후 lag가 0으로 돌아오는지 확인. 처리 불가 메시지를 넣어 DLQ 지표가 1 오르는지 확인.
- **비용 영향:** 중립~소폭 증가.
- **출처:** 일반 원칙(출처 미확인). SQS 지표 이름은 이번에 공식 페이지를 열어 확인하지 못함. ⚠️근거없음

### O-021 캐시 적중률(누적이 아닌 구간 비율)
- **무엇/왜:** 캐시 적중·미스를 **카운터**로 내고 비율은 질의에서 `rate()`로 계산해야 최근 구간의 적중률을 본다. 프로세스 시작 이후 누적 비율 게이지는 오래 산 Pod에서 변화가 거의 보이지 않는다.
- **실패 양상:** 캐시 키 버그·Redis 장애로 적중률이 0이 돼도 누적 게이지는 천천히 내려가 몇 시간 동안 정상처럼 보인다. 폭증 시 DB가 갑자기 맞는다.
- **신호:** 🟡 `Gauge("cache_hit_ratio", "... 프로세스 시작 이후 누적")` (SWA `services/board/src/board/metrics.py`) / 🟢 `cache_requests_total{result="hit|miss"}` Counter / 🔴 캐시 있음(T-CTL-004) + 지표 없음
- **필요 수준:** 캐시를 처방한 경우(T≥2).
- **처방:** 공통: 카운터 2개로 교체, 대시보드에서 5분 창 비율. 관리형 Redis 서버 측 `keyspace_hits/misses`도 함께.
- **검증:** P4에서 Redis를 차단(V-037)했을 때 적중률이 1분 안에 0 근처로 떨어지는지 확인.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인). 카운터 + rate 방식은 https://prometheus.io/docs/practices/histograms/ 의 집계 원리와 같은 맥락. ⚠️근거없음

### O-022 이벤트 루프 지연(Node·Python asyncio)
- **무엇/왜:** 단일 스레드 이벤트 루프에서 CPU 작업(해시, JSON 대용량 파싱, 동기 I/O)이 루프를 막으면 그 프로세스의 모든 요청이 함께 늦어진다. 루프 지연은 CPU 사용률보다 정확한 포화 지표다.
- **실패 양상:** CPU 50%인데 p99가 수 초. argon2 해시 같은 무거운 작업이 같은 프로세스에서 읽기 요청을 막는다(T-CTL-008의 원인).
- **신호:** 🟢 Node `perf_hooks.monitorEventLoopDelay()`, `prom-client` 기본 지표(`nodejs_eventloop_lag_seconds`), Python 주기 sleep 오차 측정 `event_loop_lag_seconds` Histogram (SWA perf 브랜치 `monitor_loop_lag`) / 🔴 async 프레임워크(FastAPI·Express)인데 루프 지연 지표 없음 + `heavy.password_hash`·`heavy.image` 사실 존재
- **필요 수준:** T≥2이고 런타임이 이벤트 루프 기반일 때.
- **처방:** 공통: 루프 지연 히스토그램 노출 + 대시보드. 지연이 크면 처방은 T-CTL-008(무거운 작업 격리) 또는 워커 스레드.
- **검증:** P4에서 무거운 경로(로그인)에 부하를 걸었을 때 루프 지연 p99와 읽기 p95가 함께 오르는지, 격리 후에는 읽기가 영향받지 않는지 비교.
- **비용 영향:** 중립.
- **출처:** https://nodejs.org/api/perf_hooks.html (`monitorEventLoopDelay` 존재·용도 확인, 세부 옵션은 페이지 요약에서 잘림), 2026-10-01 확인. Python 측은 일반 원칙(asyncio 문서 접속 실패 503). ⚠️근거없음

### O-023 런타임 메모리·GC 지표
- **무엇/왜:** 힙 사용량, GC 횟수·정지 시간, RSS를 낸다. 소크(§17.3)의 메모리 누수 판정과 메모리 limit 설정(right-sizing)의 근거다.
- **실패 양상:** 서서히 늘어나는 메모리로 며칠마다 OOMKilled → 재시작이 반복되는데 "가끔 튄다"로만 보인다. JVM·Node 힙 한도와 컨테이너 limit 불일치.
- **신호:** 🟢 `prom-client` collectDefaultMetrics, `prometheus_client` 프로세스 지표(`process_resident_memory_bytes`), JVM Micrometer / 🟡 컨테이너 메모리만 봄 / 🔴 Node인데 `--max-old-space-size`가 limit보다 큼
- **필요 수준:** 최대 필요 수준 L2 이상(소크 판정이 들어가는 수준). L1은 컨테이너 메모리로 충분.
- **처방:** 공통: 언어 클라이언트 기본 지표 활성화(대부분 한 줄).
- **검증:** 소크 처음 30분과 마지막 30분의 RSS·힙 비교, 추세가 계속 오르면 실패(§17.3).
- **비용 영향:** 소폭 증가(시계열 수십 개).
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### O-024 Server-Timing으로 구간별 처리 시간 남기기(외부에는 숨김)
- **무엇/왜:** 앱이 응답마다 `Server-Timing: db;dur=12, redis;dur=3`처럼 구간 시간을 붙이면 프록시 로그 한 줄로 요청별 병목 구간을 안다. 트레이싱 없이 얻는 가장 싼 요청 단위 분해다. 다만 헤더는 내부 구조를 드러내므로 외부 응답에서는 지운다.
- **실패 양상:** 지연 원인을 요청 단위로 분해할 수단이 없거나, 반대로 DB 구조·타이밍이 외부에 노출된다.
- **신호:** 🟢 앱 `response.headers["Server-Timing"]` + nginx `proxy_hide_header Server-Timing` + 로그에 `$upstream_http_server_timing` (SWA perf 브랜치) / 🔴 `Server-Timing`을 외부로 그대로 노출 + `Timing-Allow-Origin: *` / 🟡 구간 합계와 전체 시간 차이가 큼(계측 누락)
- **필요 수준:** T≥2에서 트레이싱(O-005) 대신 쓰는 저비용 선택지. 트레이싱이 있으면 선택.
- **처방:** 티어0: 플랫폼이 헤더를 그대로 노출하는지 확인 후 숨김. 티어1/2: 프록시에서 로그 후 제거.
- **검증:** 외부에서 `curl -I` 했을 때 헤더가 없는지, 프록시 로그에는 있는지 확인. 일부러 넣은 지연(예: DB 100ms)이 해당 구간 값으로 나타나는지 교정 테스트(SWA `test_timing` 방식).
- **비용 영향:** 소폭 증가(로그 바이트).
- **출처:** https://www.w3.org/TR/server-timing/ (정의, "expose potentially sensitive application and infrastructure information" 경고와 `Timing-Allow-Origin`, 2026-10-01 확인)

### O-025 외부 의존성 호출 지표
- **무엇/왜:** 결제·메일·LLM 등 외부 API 호출마다 지연·오류·타임아웃·재시도 수를 의존성 이름 라벨로 낸다. 외부 장애와 내 장애를 가른다.
- **실패 양상:** 외부 결제사 지연으로 스레드·커넥션이 묶여 전체가 느려지는데 원인을 모른다. 재시도 폭주가 보이지 않는다.
- **신호:** 🟢 HTTP 클라이언트 계측(OTel `http.client.request.duration`), `dependency` 라벨 / 🔴 `ext.no_timeout` 사실 + 지표 없음 / 🟡 오류는 로그에만
- **필요 수준:** D≥3(디그레이드 경로 필요) 또는 C≥3(결제)에서 필수. 외부 유료 API(COST-008)가 있으면 호출 수 지표는 L1부터.
- **처방:** 공통: OTel HTTP 클라이언트 자동 계측 또는 래퍼에 카운터·히스토그램.
- **검증:** HTTPChaos(V-039)로 외부 호출에 지연을 넣고 해당 의존성 지표만 오르는지 확인.
- **비용 영향:** 소폭 증가.
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### O-026 설계된 거절(백프레셔 503·레이트 리밋 429) 별도 집계
- **무엇/왜:** 큐 한도 초과 503(`QUEUE_FULL`)과 리밋 429는 설계된 동작이다. 장애성 5xx와 섞으면 오류율 SLO가 오염되고, 빼버리면 사용자가 거절당하는 양을 놓친다. 별도 지표로 낸다.
- **실패 양상:** 폭증 때 백프레셔가 정상 동작했는데 오류율 알림이 울려 온콜이 오판한다. 또는 리밋이 너무 빡빡해 정상 사용자를 막는데 아무도 모른다.
- **신호:** 🟢 응답 본문 `code`로 구분 집계(SWA k6 `backpressure_503`, `rate_limited_429`, `server_errors`에서 백프레셔 제외), nginx `limit_req_status 429` + 로그 / 🔴 모든 5xx를 하나로 / 🟡 앱은 구분하지만 LB 지표는 구분 안 함
- **필요 수준:** T=L3(큐·리밋 처방)일 때.
- **처방:** 공통: 거절 사유 라벨(`reason=queue_full|rate_limited`) + SLO 정의에서 제외 여부를 명시(가용성 SLI에서는 "유효 요청"에서 리밋 거절을 뺄지 결정).
- **검증:** P4 스파이크에서 k6의 거절 카운트와 서버 지표의 거절 카운트가 일치하는지 확인.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인). SLI의 "유효 이벤트" 개념은 https://sre.google/workbook/implementing-slos/ 참조. ⚠️근거없음

### O-027 컨테이너 재시작·OOMKilled·종료 코드 감시
- **무엇/왜:** 재시작 수와 마지막 종료 사유(OOMKilled, exit 137, liveness 실패)는 "자동 복구가 장애를 가리는" 상황을 드러낸다.
- **실패 양상:** liveness가 부하 중 Pod를 계속 죽여 재시작이 폭주하는데 서비스는 "대체로 됨"으로 보인다(SWA 로컬 부하: 재시작 9 → 90, 전부 exit 137).
- **신호:** 🟢 `kube_pod_container_status_restarts_total` 증가율 알림, `last_terminated_reason` / 🔴 티어2 + 재시작 지표 없음 / 🟡 ECS 태스크 중지 사유(`stoppedReason`)를 보지 않음
- **필요 수준:** 최대 필요 수준 L1 이상(티어1·2).
- **처방:** 티어1: ECS 태스크 상태 변경 이벤트(EventBridge) / Cloud Run 인스턴스 종료 로그. 티어2: kube-state-metrics 또는 GKE 기본 지표 + 재시작률 알림(티켓 등급).
- **검증:** PodChaos(V-032)·메모리 압박(V-040) 후 재시작 수와 종료 사유가 기록되는지 확인.
- **비용 영향:** 중립.
- **출처:** https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/ (Terminated 상태의 exit code·reason, OOMKilled), 2026-10-01 확인

### O-028 배치·크론 작업의 마지막 성공 시각
- **무엇/왜:** 배치는 "실패"보다 "안 돌았음"이 더 흔하다. 마지막 성공 시각 지표를 내고, 사용자 영향이 생기기 전 시간(보통 주기의 2배 이상)을 넘으면 알린다.
- **실패 양상:** 크론이 스케줄러 변경·권한 만료로 조용히 멈춰 정산·메일·정리 작업이 몇 주째 안 돌았다.
- **신호:** 🟢 `job_last_success_timestamp_seconds`, Pushgateway, 외부 하트비트(dead man's snitch류) / 🔴 `process.cron` 사실 + 성공 기록 없음
- **필요 수준:** 크론·배치가 있으면 L1부터(특히 백업·정산 배치).
- **처방:** 티어0: 플랫폼 크론 실행 기록 + 실패 알림. 티어1: Cloud Scheduler/EventBridge Scheduler 실행 실패 알림 + 성공 시각 지표. 티어2: CronJob `status.lastSuccessfulTime` 감시.
- **검증:** 크론을 일시 정지하고 임계 시간 뒤 알림이 오는지 확인.
- **비용 영향:** 중립.
- **출처:** https://prometheus.io/docs/practices/alerting/ (배치 작업은 최근 성공하지 않았을 때 알림, 2주기 이상 여유, 2026-10-01 확인)

### O-029 지표·내부 엔드포인트의 외부 노출 차단
- **무엇/왜:** `/metrics`, `/healthz`, `/readyz`, 디버그 엔드포인트는 내부 수집기만 접근해야 한다. 외부에 열리면 내부 구조·트래픽 정보가 새고, 지표 엔드포인트 반복 호출로 부하를 만들 수 있다.
- **실패 양상:** 크롤러가 `/metrics`를 수집해 내부 라우트·버전이 노출된다. 무거운 깊은 헬스 체크를 외부에서 두드려 DB 부하.
- **신호:** 🟢 nginx `location ~ ^/(healthz|readyz|metrics)$ { return 404; }`, `location /internal/ { return 404; }` (SWA), 지표를 별도 포트로(`start_http_server`) / 🔴 공개 라우터에 `/metrics` 그대로, `/debug/pprof` 노출, Spring Actuator 전체 노출
- **필요 수준:** 앱 지표 엔드포인트가 있으면 모든 수준.
- **처방:** 공통: 별도 포트 또는 인그레스 차단 + NetworkPolicy로 모니터링 네임스페이스만 허용(SWA `networkpolicy.yaml`).
- **검증:** 외부 URL로 `/metrics`·`/healthz`·`/internal/*` 요청 시 404/403인지 P4 스모크에 포함.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### O-030 프로세스 모델에 맞는 지표 수집(멀티 프로세스·워커 분리)
- **무엇/왜:** gunicorn·PM2 같은 멀티 워커 프로세스에서 Prometheus 클라이언트는 프로세스별 메모리에 지표를 둔다. 스크레이프가 매번 다른 워커에 걸려 값이 튄다. 별도 프로세스(큐 워커)의 지표는 그 프로세스가 직접 노출해야 한다.
- **실패 양상:** 카운터가 오르내리며 rate가 엉망, 워커 지표가 API 엔드포인트에 섞이거나 아예 수집되지 않는다.
- **신호:** 🟢 `PROMETHEUS_MULTIPROC_DIR`, 워커는 `start_http_server`로 별도 노출 + 주석 "board-api의 /metrics에 섞이지 않도록" (SWA `worker_metrics.py`) / 🔴 `gunicorn -w 4` + 기본 레지스트리, PM2 cluster 모드 + prom-client 기본
- **필요 수준:** 앱 지표를 쓰는 수준(L2 이상)에서 프로세스 모델이 멀티 워커일 때.
- **처방:** 공통: 컨테이너당 단일 프로세스(수평 확장은 레플리카로) 또는 멀티프로세스 모드. OTel은 OTLP push로 회피 가능.
- **검증:** 요청 N건 후 카운터 합계가 N인지 여러 번 스크레이프해서 확인.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

## A3. 트레이스·에러 추적·프로파일링

### O-031 분산 트레이싱 도입 기준
- **무엇/왜:** 트레이싱은 서비스 간 호출 경로의 지연을 분해한다. 단일 서비스 + DB면 Server-Timing·로그로 충분하고, 서비스가 여러 개이거나 비동기 경로가 있을 때 값이 크다.
- **실패 양상:** 도입하지 않으면 다단 호출에서 병목을 못 찾는다. 반대로 단일 서비스에 무거운 APM을 붙이면 비용만 든다(과잉).
- **신호:** 🟢 OTel SDK + Collector/관리형 백엔드 / 🟡 서비스 4개 이상 + 트레이싱 없음 / 🔴(과잉) 단일 서비스 L1에 유료 APM 에이전트
- **필요 수준:** 최대 필요 수준 L2 이상이면서 배포 단위 2개 이상(또는 큐 경로). L3면 필수.
- **처방:** 티어0: 플랫폼 기본 트레이싱. 티어1: Cloud Trace / X-Ray(ADOT) — 관리형, 샘플링 기본. 티어2: OTel Collector → 관리형 백엔드.
- **검증:** P4 부하 중 의존성 지연을 주입(V-036)하고 트레이스에서 해당 스팬이 지연 원인으로 보이는지 확인.
- **비용 영향:** 증가(스팬 수 과금). 샘플링 필수.
- **출처:** https://opentelemetry.io/docs/concepts/context-propagation/ (2026-10-01 확인). 도입 기준 자체는 일반 원칙(출처 미확인). ⚠️근거없음

### O-032 트레이스 샘플링(헤드 vs 테일)
- **무엇/왜:** 헤드 샘플링은 시작 시점에 확률로 결정해 싸고 단순하지만 오류 트레이스를 보장하지 못한다. 테일 샘플링은 전체를 보고 오류·느린 트레이스를 골라 남기지만 상태 저장·운영 부담이 크다.
- **실패 양상:** 100% 샘플링으로 비용 폭증, 또는 1% 헤드 샘플링으로 정작 오류 트레이스가 없다.
- **신호:** 🟢 `OTEL_TRACES_SAMPLER=parentbased_traceidratio` + 비율 설정, Collector `tail_sampling` 프로세서 / 🔴 샘플러 기본 `always_on` + 고트래픽 / 🟡 서비스마다 샘플링 비율이 다르고 parent-based가 아님(트레이스가 중간에 끊김)
- **필요 수준:** 트레이싱을 도입한 경우(L2 이상). 테일 샘플링은 L3·고트래픽에서만.
- **처방:** L2: parent-based 확률 헤드 샘플링(예: 5~10%). L3: 헤드로 줄인 뒤 오류·느린 트레이스 테일 샘플링 병행.
- **검증:** 오류 주입 시 오류 트레이스가 실제로 남는지 확인(헤드만 쓰면 남는 비율이 샘플률과 같은지).
- **비용 영향:** 감소(샘플링 없을 때 대비).
- **출처:** https://opentelemetry.io/docs/concepts/sampling/ (헤드·테일 정의와 장단점, 병행 가능, 2026-10-01 확인)

### O-033 에러 추적(Sentry 등)
- **무엇/왜:** 예외를 지문(fingerprint)으로 묶어 "새 오류 종류", 발생 빈도, 영향받은 사용자 수를 보여준다. 로그로는 "새로운 종류의 오류"를 알기 어렵다.
- **실패 양상:** 배포 후 특정 브라우저·경로에서만 나는 예외를 사용자 신고 전까지 모른다.
- **신호:** 🟢 `sentry-sdk`, `@sentry/nextjs`, `@sentry/node` 의존성 + DSN 환경변수 / 🔴 프론트엔드가 있고 공개 서비스인데 오류 수집 없음 / 🟡 DSN 하드코딩, 샘플링 1.0 고정
- **필요 수준:** 최대 필요 수준 L1 이상(무료 등급으로 충분한 경우 많음). 바이브코더 앱의 첫 관측 장치로 비용 대비 효과가 가장 크다.
- **처방:** 티어0/1/2 공통: 관리형 에러 추적 SaaS 무료 등급 또는 GCP Error Reporting(로그 기반, 별도 SDK 불필요)·CloudWatch Logs 패턴. PII 스크러빙(O-007) 함께.
- **검증:** 배포 직후 테스트 예외를 일부러 던지는 비공개 경로(또는 SDK 테스트 이벤트)로 이슈가 생성되고 알림이 오는지 확인.
- **비용 영향:** 소폭 증가(무료 등급 초과 시).
- **출처:** https://docs.sentry.io/product/issues/ (지문 기반 이슈 그룹화, 2026-10-01 확인) ⚠️출처확인필요

### O-034 릴리스 버전 태깅과 릴리스 건강도
- **무엇/왜:** 모든 로그·지표·오류에 배포 버전(커밋 SHA)을 붙이면 "이 버전부터 오류가 늘었다"를 즉시 안다. 카나리·자동 롤백 판단의 전제다.
- **실패 양상:** 오류 증가가 배포 탓인지 트래픽 탓인지 모른 채 롤백을 망설인다.
- **신호:** 🟢 `release=GIT_SHA` SDK 설정, `build_info{version=...}` 지표, 이미지 태그 = 커밋 SHA / 🔴 이미지 태그 `latest`만, 버전 정보 없음
- **필요 수준:** U≥2(자동 롤백)에서 필수, U=L3(카나리)는 버전별 지표 분리 필수.
- **처방:** 공통: CI가 SHA를 빌드 인자·환경변수로 주입, 모든 텔레메트리 리소스 속성(`service.version`)에 포함.
- **검증:** 배포 직후 지표·오류 화면에서 새 버전 값으로 필터가 되는지 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.sentry.io/product/releases/health/ (crash-free sessions·users, 릴리스 채택, 2026-10-01 확인) ⚠️출처확인필요

### O-035 연속 프로파일링
- **무엇/왜:** 운영 중 CPU·힙 프로파일을 저오버헤드로 계속 수집해 "어느 함수가 CPU를 먹나"를 본다. 비용 최적화(right-sizing)와 성능 회귀 원인 찾기에 쓴다.
- **실패 양상:** CPU 사용량이 버전마다 늘어도 원인 함수를 찾으려면 재현 환경이 필요하다.
- **신호:** 🟢 `google-cloud-profiler`, `@google-cloud/profiler`, Pyroscope 에이전트 / 🟡 디버그용 `cProfile`·`--prof`만
- **필요 수준:** T=L3 또는 비용 상위 서비스(COST-006 right-sizing 대상)에서 선택. L1~L2에는 과잉.
- **처방:** 티어1: Cloud Profiler(오버헤드 수집 중 5% 미만, 평균 0.5% 미만). 티어2: 동일 또는 오픈소스 Pyroscope. 티어0: 해당 없음.
- **검증:** P4 부하 중 프로파일에 알려진 무거운 함수(argon2 해시 등)가 상위로 나오는지 확인.
- **비용 영향:** 소폭 증가.
- **출처:** https://docs.cloud.google.com/profiler/docs/about-profiler (저오버헤드, 지원 언어 Go·Java·Node.js·Python, 2026-10-01 확인)

### O-036 텔레메트리 파이프라인 자체의 보호(Collector 메모리 제한)
- **무엇/왜:** 폭증 때 텔레메트리도 폭증한다. 수집기(OTel Collector, Fluent Bit)가 OOM으로 죽으면 가장 필요할 때 관측이 끊긴다. 메모리 제한·배치·백프레셔를 둔다.
- **실패 양상:** 장애 한가운데서 로그·트레이스가 사라져 사후 분석이 불가능하다. 수집기가 노드 메모리를 먹어 앱 Pod가 축출된다.
- **신호:** 🟢 Collector 파이프라인 첫 프로세서 `memory_limiter`, `batch`, 수집기 resources.limits / 🔴 Collector 설정에 memory_limiter 없음 / 🟡 사이드카 수집기가 Pod마다(자원 낭비)
- **필요 수준:** 자체 Collector를 운영하는 경우(티어2, L2 이상).
- **처방:** 티어0/1: 관리형 수집(신경 쓸 것 없음). 티어2: memory_limiter 첫 번째 + 수집기 자체 지표(드롭 수) 감시.
- **검증:** P4 스파이크 동안 수집기 드롭 지표·재시작 수가 0인지, 로그 손실 비율(보낸 요청 수 대비 로그 줄 수)을 측정.
- **비용 영향:** 중립.
- **출처:** https://github.com/open-telemetry/opentelemetry-collector/blob/main/processor/memorylimiterprocessor/README.md ("add it as the first processor in a pipeline", 2026-10-01 확인)

## A4. SLI/SLO와 알림

### O-037 SLI 정의(좋은 이벤트 / 유효 이벤트, 측정 위치)
- **무엇/왜:** SLI는 "좋은 이벤트 수 / 유효 이벤트 수"로 정의한다(예: 1초 안에 성공한 요청 / 전체 요청). 처음에는 가장 적은 작업으로 얻는 곳(LB 지표·로그)에서 재고, 나중에 사용자 가까이로 옮긴다.
- **실패 양상:** 헬스 체크 요청·봇·리밋 거절을 분모에 섞어 SLI가 실제 사용자 경험과 무관해진다. 앱 내부에서만 재서 LB 앞단 장애(인증서 만료, LB 설정 오류)를 놓친다.
- **신호:** 🟢 SLI 정의 파일(OpenSLO, Terraform `google_monitoring_slo`, CloudWatch Application Signals SLO) / 🟡 "가용성 99.9%" 문구만 README에 / 🔴 SLO 언급 없음 + 최대 필요 수준 L2 이상
- **필요 수준:** 최대 필요 수준 L2 이상(§17.4). L0~L1은 업타임 체크 + 오류율 알림으로 대신한다.
- **처방:** 티어0: 플랫폼 분석 + 외부 업타임으로 근사. 티어1: Cloud Monitoring 서비스·SLO(LB/Cloud Run 지표 기반) / CloudWatch Application Signals SLO(지연·가용성 자동 수집). 티어2: 관리형 Prometheus 기록 규칙 + SLO 도구.
- **검증:** P4에서 알려진 오류 비율(예: 2%)을 주입하고 SLI 값이 98% 근처로 계산되는지 확인. 헬스 체크 트래픽이 분모에서 빠졌는지 확인.
- **비용 영향:** 소폭 증가.
- **출처:** https://sre.google/workbook/implementing-slos/ ("good events divided by the total number of events", 측정 위치 권고), https://docs.cloud.google.com/stackdriver/docs/solutions/slo-monitoring, https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-ServiceLevelObjectives.html, 2026-10-01 확인

### O-038 SLO 목표를 필요 수준에서 도출 + 에러 예산 정책
- **무엇/왜:** SLO 목표는 감이 아니라 필요 수준에서 나온다(예: D L2 → 월 가용성 99.9%, T L3 → 피크 p95 < 1초, §17.4). 예산을 다 쓰면 무엇을 멈추고 누가 결정하는지 문서로 정한다.
- **실패 양상:** 목표가 너무 높으면(99.99%) 인프라 과잉·알림 폭주, 너무 낮으면 사용자 이탈. 예산 소진 후에도 기능 배포를 계속해 같은 장애가 반복된다.
- **신호:** 🟢 `SLO.md`/`error-budget-policy.md`, SLO 리소스의 `goal` 값이 수준 표와 일치 / 🔴 L1 서비스에 99.99% 목표(과잉) / 🟡 SLO는 있는데 정책 없음
- **필요 수준:** 최대 필요 수준 L2 이상. 정책 문서는 L3에서 필수.
- **처방:** 공통: infrafit이 수준 → SLO 목표 표로 자동 생성, 리포트에 근거 표시. 정책 기본안: 예산 소진 시 신뢰성 작업 우선 + 비긴급 배포 동결.
- **검증:** P4 결과(브레이크포인트·장애 주입 중 오류율)로 이 SLO가 현재 구성에서 달성 가능한지 계산해 리포트에 표시.
- **비용 영향:** 목표 상향 시 증가, 과잉 목표 하향 시 감소.
- **출처:** https://sre.google/workbook/implementing-slos/ (에러 예산 정책: 소진 시 조치와 책임자 명시, 2026-10-01 확인)

### O-039 여러 창·여러 소진율 알림
- **무엇/왜:** 임계값 알림(오류율 > 1%) 대신 에러 예산 소진 속도로 알린다. 99.9% 기준 시작점: 1시간 창(+5분 짧은 창) 14.4배 → 페이지, 6시간(+30분) 6배 → 페이지, 3일(+6시간) 1배 → 티켓. 짧은 창은 긴 창의 1/12.
- **실패 양상:** 짧은 스파이크마다 깨우거나(오탐), 서서히 새는 장애를 며칠간 못 잡는다(미탐). 장애가 끝났는데도 긴 창 때문에 알림이 계속 울린다.
- **신호:** 🟢 burn rate 알림 정책 2~3개(Cloud Monitoring `select_slo_burn_rate`, CloudWatch SLO burn rate alarm, Prometheus 기록 규칙) / 🔴 `error_rate > 0.01 for 1m` 단일 알림만 + L2 이상 / 🟡 소진율 알림은 있는데 짧은 창 없음
- **필요 수준:** 최대 필요 수준 L2 이상(§17.4 표).
- **처방:** 티어1: Cloud Monitoring SLO burn rate 정책 / CloudWatch Application Signals burn rate 알람. 티어2: Prometheus 규칙 생성기(sloth·pyrra류) 또는 관리형 SLO.
- **검증:** P4에서 SLO를 14.4배 이상 소진하는 오류율(99.9% 기준 약 1.44%)을 10분간 주입해 페이지가 5분 안팎에 오는지, 0.5% 주입에는 페이지가 오지 않는지 확인.
- **비용 영향:** 소폭 증가(알림 정책 과금은 작음). 오탐 감소로 운영 비용 감소.
- **출처:** https://sre.google/workbook/alerting-on-slos/ (권장 창·배수, 1/12 규칙), 설계 문서 S28과 동일 페이지, 2026-10-01 확인

### O-040 저트래픽 서비스의 SLO·알림 처리
- **무엇/왜:** 요청이 적으면 오류 몇 건으로 예산이 크게 줄어 burn rate 알림이 쉽게 울린다. 합성 트래픽으로 분모를 채우거나, 관련 서비스를 묶거나, 페이지 대신 티켓으로 낮춘다.
- **실패 양상:** 밤에 요청 20건 중 1건 실패로 새벽 페이지. 혹은 이를 피하려 알림을 꺼서 진짜 장애를 놓친다.
- **신호:** 🟡 T=L0~L1 가정 트래픽(평시 동시 50 이하) + burn rate 페이지 알림 / 🟢 최소 요청 수 조건(`AND request_count > N`), 합성 체크 병행
- **필요 수준:** SLO 알림을 쓰는 L2 서비스 중 트래픽 가정이 낮은 경우.
- **처방:** 공통: 최소 이벤트 수 조건 + 합성 모니터링(O-048)으로 분모 보강, 저트래픽 시간대는 티켓 등급.
- **검증:** 저트래픽 재현(초당 0.1 요청)에서 1건 실패로 페이지가 오지 않는지 확인.
- **비용 영향:** 합성 체크만큼 소폭 증가.
- **출처:** https://sre.google/workbook/alerting-on-slos/ (저트래픽 서비스: 합성 트래픽, 서비스 묶기, "do you really need to page an engineer?", 2026-10-01 확인)

### O-041 증상 기반 알림(원인 알림은 대시보드로)
- **무엇/왜:** 페이지는 사용자가 느끼는 증상(오류율, 지연, 가용성)에만 건다. CPU 80%, Pod 재시작 같은 원인 지표는 대시보드·티켓으로 보낸다. 모든 페이지는 즉시 행동할 수 있어야 한다.
- **실패 양상:** CPU 알림이 매일 울리지만 사용자 영향은 없어서 모두 무시하게 되고, 진짜 장애 알림도 묻힌다.
- **신호:** 🔴 페이지 대상 알림에 `cpu > 80`, `memory > 80`, `pod restarted` / 🟢 페이지는 SLO·업타임만, 원인 지표는 `severity=ticket`
- **필요 수준:** 알림이 생기는 모든 수준(L1부터).
- **처방:** 공통: infrafit이 생성하는 알림은 L1: 업타임 실패 + 5xx 비율, L2+: SLO 소진율. 자원 알림은 용량(O-070) 티켓으로.
- **검증:** 알림 목록을 lint해서 페이지 등급 알림이 증상 지표만 참조하는지 검사. P4에서 CPU 스트레스만 주고(사용자 영향 없음) 페이지가 안 오는지 확인.
- **비용 영향:** 중립.
- **출처:** https://prometheus.io/docs/practices/alerting/ ("alert on symptoms"), https://sre.google/sre-book/monitoring-distributed-systems/ ("Every page should be actionable"), 2026-10-01 확인

### O-042 알림 피로 줄이기(그룹핑·억제·알림/사건 1:1)
- **무엇/왜:** 한 사건에 알림 하나가 목표다. 같은 원인 알림을 묶고(그룹핑), 상위 장애가 있으면 하위 알림을 억제하고(인히비션), 계획된 작업 중에는 묵음 처리한다. 교대당 사건 2건이 상한이라는 기준도 있다.
- **실패 양상:** 클러스터 장애 하나에 수백 개 알림 → 온콜이 핵심을 못 본다. 반복 오탐으로 알림 채널을 음소거한다.
- **신호:** 🟢 Alertmanager `group_by`, `inhibit_rules`, CloudWatch 복합 알람 / 🔴 서비스·Pod마다 개별 알림 + 그룹핑 없음 / 🟡 알림 수 대비 사건 수 기록 없음
- **필요 수준:** 최대 필요 수준 L2 이상(알림이 여러 개 생기는 수준).
- **처방:** 티어1: CloudWatch 복합 알람 / Cloud Monitoring 정책 통합. 티어2: Alertmanager 그룹핑·억제. 공통: 월 1회 알림 리뷰(알림 수/사건 수).
- **검증:** P4 존 장애 주입(V-034) 동안 받은 알림 수를 세고 사건 1건당 알림 수를 리포트에 기록.
- **비용 영향:** 중립.
- **출처:** https://prometheus.io/docs/alerting/latest/alertmanager/ (그룹핑·억제·사일런스), https://sre.google/sre-book/being-on-call/ (12시간 교대당 최대 2건, 알림/사건 1:1 지향), https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html (복합 알람으로 소음 감소), 2026-10-01 확인

### O-043 지표가 끊겼을 때의 알림 동작(누락 데이터)
- **무엇/왜:** 서버가 죽으면 오류 지표도 안 나온다. "데이터 없음"을 정상으로 처리하면 완전 장애에 알림이 오지 않는다. 지표마다 누락 처리 방식을 의도적으로 고른다. CloudWatch 기본값은 `missing`(INSUFFICIENT_DATA)이다.
- **실패 양상:** 서비스 전체가 내려가 요청 지표가 0건이 되자 오류율 알람이 "데이터 부족" 상태로 조용히 머문다.
- **신호:** 🔴 오류율·지연 알람에 `treat_missing_data = "notBreaching"`, Prometheus 규칙에 `absent()` 대응 없음 / 🟢 연속 보고 지표는 `breaching`, 오류만 보고하는 지표는 `notBreaching`, `absent(up{job="api"})` 규칙
- **필요 수준:** 알림을 쓰는 모든 수준(L1부터).
- **처방:** 티어1: Terraform `treat_missing_data` 명시. 티어2: `up == 0`·`absent()` 규칙. 공통: 외부 업타임 체크(O-047)가 최종 방어선.
- **검증:** P4에서 서비스를 0 레플리카로 내리고 지표 기반 알림과 업타임 알림이 모두 오는지 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/alarms-and-missing-data.html (네 가지 처리 방식, 기본 `missing`, 롤백 알람은 breaching 권장 예시), 2026-10-01 확인

### O-044 알림 파이프라인 종단 확인(워치독)
- **무엇/왜:** 알림 규칙은 몇 달간 안 울리다가 정작 필요할 때 경로가 깨져 있다. 항상 울리는 워치독 알림(dead man's switch)이나 주기적 시험 발송으로 "알림이 실제로 사람에게 도착하는지"를 확인한다.
- **실패 양상:** 슬랙 웹훅 만료, 이메일 주소 퇴사자, SNS 구독 미확인으로 모든 알림이 허공으로 간다.
- **신호:** 🟢 Alertmanager `Watchdog` 알림 + 외부 하트비트 서비스, 정기 `set-alarm-state` 시험 / 🔴 알림 채널 1개 + 시험 기록 없음
- **필요 수준:** 최대 필요 수준 L2 이상. L1은 배포 직후 1회 시험 발송.
- **처방:** 공통: 배포 파이프라인 마지막에 시험 알림 1회(P4 단계 C 시작 조건). L2+: 워치독 상시.
- **검증:** CloudWatch `SetAlarmState`로 ALARM을 강제해 알림 수신 확인(V-058). 수신 확인까지의 시간을 기록.
- **비용 영향:** 중립.
- **출처:** https://prometheus.io/docs/practices/alerting/ (모니터링 시스템 자체 감시, 알림 파이프라인 종단 블랙박스 확인 권장), https://sre.google/workbook/monitoring/ (알림 규칙은 몇 달간 안 울리므로 테스트 필요), 2026-10-01 확인

### O-045 알림 대상(액션)의 존재와 다중 채널
- **무엇/왜:** 알람이 가리키는 SNS 토픽·알림 채널이 실제로 존재하고 구독이 확인됐는지 검증한다. CloudWatch는 지정한 액션을 검증하지 않는다. L3는 채널을 2개 이상(메신저 + 전화/SMS)으로.
- **실패 양상:** Terraform으로 알람은 만들었는데 SNS 구독 이메일 확인을 안 해서 알림이 한 통도 안 간다.
- **신호:** 🔴 `alarm_actions = []`, SNS 이메일 구독 + 확인 절차 없음, 채널 1개 + L3 / 🟢 알림 채널 리소스 + 확인 상태 점검
- **필요 수준:** 알림을 쓰는 모든 수준. 다중 채널은 L3.
- **처방:** 티어0: 플랫폼 알림 이메일. 티어1/2: SNS/Cloud Monitoring 채널 + 온콜 도구 연동(L3).
- **검증:** O-044와 같은 시험 발송으로 모든 채널 수신 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html ("CloudWatch doesn't test or validate the actions that you specify", 2026-10-01 확인)

### O-046 모니터링·알림 설정의 코드화
- **무엇/왜:** 대시보드·알림·SLO를 콘솔 클릭이 아니라 IaC로 관리하면 리뷰·버전 관리·롤백이 되고, 환경 재생성(D L3 리전 복구) 때 관측도 함께 복구된다.
- **실패 양상:** 복구 리전에 앱은 올라왔는데 알림·대시보드가 없어 아무도 상태를 모른다. 누가 알림 임계값을 바꿨는지 모른다.
- **신호:** 🟢 Terraform `aws_cloudwatch_metric_alarm`, `google_monitoring_alert_policy`, `PrometheusRule` CRD, 대시보드 JSON 커밋 / 🔴 IaC는 있는데 관측 리소스는 0개
- **필요 수준:** 최대 필요 수준 L2 이상.
- **처방:** 공통: P3 실행기가 앱 인프라와 같은 Terraform/Kustomize에 관측 리소스를 생성.
- **검증:** 빈 프로젝트에 IaC 적용 후 알림·대시보드·SLO가 모두 생기는지 확인(복원 리허설 V-062에 포함).
- **비용 영향:** 중립.
- **출처:** https://sre.google/workbook/monitoring/ ("intent-based configuration is preferable to systems that only provide web UIs", 2026-10-01 확인)

## A5. 외부·사용자 관점 관측

### O-047 외부 업타임 체크(여러 지역)
- **무엇/왜:** 시스템 밖에서 공개 URL을 주기적으로 호출해 응답을 확인한다. 내부 지표가 모두 죽어도(완전 장애, DNS·인증서·LB 문제) 잡히는 최후 방어선이고 가장 싸다.
- **실패 양상:** 서버 전체가 내려가 내부 지표가 사라졌는데 알림이 없다. 사용자 신고로 장애를 안다.
- **신호:** 🟢 Terraform `google_monitoring_uptime_check_config`, CloudWatch Synthetics 하트비트 캐너리, 외부 업타임 SaaS 설정 / 🔴 공개 서비스인데 없음
- **필요 수준:** 공개 엔드포인트가 있으면 모든 수준(L0~L1 관측의 전부, §17.4).
- **처방:** 티어0: 무료 외부 업타임 서비스 또는 GCP 업타임 체크. 티어1/2: GCP 업타임 체크(여러 지역, 기본은 두 지역 이상이 1분 이상 실패해야 알림) / CloudWatch Synthetics 캐너리(최소 1분 주기). 대상 URL은 깊은 헬스가 아니라 실제 사용자 페이지나 가벼운 공개 엔드포인트.
- **검증:** 서비스를 내리고 알림이 오는지, 한 지역만의 일시 실패로는 알림이 오지 않는지 확인.
- **비용 영향:** 소폭 증가(GCP 업타임은 무료 할당 있음).
- **출처:** https://docs.cloud.google.com/monitoring/uptime-checks (여러 지역 체커, 기본 알림 조건), https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Synthetics_Canaries.html (1분 주기까지), https://cloud.google.com/stackdriver/pricing (업타임 체크 무료 할당), 2026-10-01 확인

### O-048 합성 사용자 시나리오(로그인 → 쓰기 → 읽기)
- **무엇/왜:** 실제 사용자처럼 핵심 흐름을 주기적으로 실행하는 스크립트다. 홈페이지는 뜨는데 로그인·결제가 안 되는 "부분 장애"를 잡고, 저트래픽 시간에도 SLI 분모를 채운다.
- **실패 양상:** 업타임 체크는 녹색인데 세션 저장소 장애로 로그인만 전부 실패한다.
- **신호:** 🟢 Playwright·Puppeteer 기반 캐너리, k6 browser 정기 실행, 전용 테스트 계정 / 🟡 E2E 테스트(SWA `frontend/e2e/smoke.spec.ts`)는 있지만 CI에서만 돌고 운영 대상 주기 실행은 없음 / 🔴 L3인데 없음
- **필요 수준:** 최대 필요 수준 L3(§17.4). L2에서 결제가 있으면 결제 흐름 하나만.
- **처방:** 티어1/2: CloudWatch Synthetics(Playwright/Puppeteer, 1분~) 또는 Cloud Monitoring 합성 모니터(Cloud Functions 기반). 기존 E2E 스크립트를 재사용. 테스트 데이터는 표시·정리(V-014).
- **검증:** 세션 저장소(Redis)만 차단했을 때 합성 시나리오가 실패하고 업타임 체크는 성공하는지 확인 — 둘의 차이가 이 장치의 존재 이유.
- **비용 영향:** 증가(실행당 과금 + 테스트 데이터 쓰기).
- **출처:** https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Synthetics_Canaries.html ("follow the same routes and perform the same actions as a customer", 2026-10-01 확인)

### O-049 RUM과 Core Web Vitals
- **무엇/왜:** 실제 사용자 브라우저에서 LCP(≤2.5초), INP(≤200ms), CLS(≤0.1)를 75퍼센타일로 잰다. 서버 지연이 좋아도 번들 크기·CDN·렌더링 때문에 사용자 체감은 나쁠 수 있다.
- **실패 양상:** 서버 p95 100ms인데 모바일 사용자 LCP는 6초. 프론트엔드 회귀를 모른다.
- **신호:** 🟢 `web-vitals` 패키지 + `sendBeacon`, `@vercel/speed-insights`, CloudWatch RUM 스니펫 / 🔴 SPA·SSR 프론트엔드가 있고 공개 서비스인데 없음 / 🟡 Lighthouse만(실험실 측정)
- **필요 수준:** 프론트엔드가 있는 T≥1 공개 서비스에서 L2부터. L1은 Lighthouse CI 수준이면 충분.
- **처방:** 티어0: 플랫폼 내장(Vercel Speed Insights 등). 티어1/2: `web-vitals` → 자체 수집 엔드포인트 또는 CloudWatch RUM. 수집 엔드포인트도 레이트 리밋 대상.
- **검증:** 배포 후 테스트 브라우저 세션에서 지표 이벤트가 수집 저장소에 들어오는지 확인. 75퍼센타일이 모바일·데스크톱으로 나뉘어 계산되는지.
- **비용 영향:** 소폭 증가.
- **출처:** https://web.dev/articles/vitals (세 지표 임계값, 75퍼센타일), https://github.com/GoogleChrome/web-vitals (실사용자 측정 라이브러리, sendBeacon 예), 2026-10-01 확인 ⚠️출처확인필요

### O-050 프론트엔드 오류 수집
- **무엇/왜:** 브라우저 JS 예외, 청크 로딩 실패, API 호출 실패를 수집한다. 서버 로그에는 절대 나타나지 않는 오류다.
- **실패 양상:** 배포 후 이전 버전 청크를 요청하던 사용자의 화면이 하얗게 되는데 서버는 정상이다.
- **신호:** 🟢 `@sentry/react`·`@sentry/nextjs`, `window.onerror`/`unhandledrejection` 핸들러 + 수집 / 🔴 프론트엔드 있음 + 없음
- **필요 수준:** 프론트엔드가 있는 공개 서비스 L1부터(O-033과 같은 도구로).
- **처방:** 공통: 에러 추적 SaaS 무료 등급, 소스맵 업로드(비공개), 릴리스 태깅(O-034).
- **검증:** 테스트 빌드에서 의도적 예외 후 이슈 생성 확인. 소스맵이 공개 경로에 노출되지 않았는지 확인.
- **비용 영향:** 소폭 증가.
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### O-051 상태 페이지(외부 공지 채널)
- **무엇/왜:** 장애 중 사용자에게 현재 상태와 다음 공지 시각을 알리는 별도 채널이다. 서비스와 같은 인프라에 두면 함께 죽는다.
- **실패 양상:** 장애 중 고객 문의가 폭주하고, B2B 고객은 계약상 공지 의무 위반을 문제 삼는다.
- **신호:** 🟢 별도 도메인·호스팅의 상태 페이지 링크, README·푸터의 status 링크 / 🔴 B2B·유료 구독 신호(D L2 조건) + 없음
- **필요 수준:** D≥2(유료·B2B) 또는 D=L3(재난·공공 알림 — 장애 공지가 서비스 본질)에서 필요. L1 이하에는 과잉.
- **처방:** 공통: 관리형 상태 페이지 SaaS 또는 정적 호스팅(다른 클라우드·CDN) 페이지. 업데이트 책임자는 인시던트 커뮤니케이션 담당(O-062).
- **검증:** 게임데이(V-057)에서 상태 페이지 게시까지 걸린 시간을 측정. 주 서비스 리전을 차단해도 상태 페이지가 뜨는지 확인.
- **비용 영향:** 소폭 증가.
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

## A6. 헬스 체크와 앱 런타임 계약

### O-052 얕은 liveness, 의미 있는 readiness
- **무엇/왜:** liveness는 "재시작 말고는 회복 불가"(교착 등)만 판단해야 하므로 외부 의존성을 보지 않는 가벼운 체크여야 한다. readiness는 트래픽을 받을 수 있는지 판단하되, 의존성 일부 장애로 모든 Pod가 동시에 빠지지 않게 설계한다.
- **실패 양상:** liveness가 DB를 확인하면 DB 순단 때 모든 Pod가 재시작되어 장애가 증폭된다. 부하 중 liveness 타임아웃으로 재시작 폭주(SWA 로컬 부하 exit 137). readiness가 모든 의존성을 AND로 보면 Redis 하나 장애에 전체가 503.
- **신호:** 🟢 `/healthz`는 상수 응답, `/readyz`는 의존성 중 처리 가능한 기능이 하나라도 있으면 200 (SWA `health.py`: "둘 다 죽었을 때만 트래픽에서 빠진다") / 🔴 liveness 경로가 DB 쿼리, liveness = readiness 같은 엔드포인트에 같은 failureThreshold / 🟡 liveness `timeoutSeconds: 1` + CPU limit 낮음(부하 시 오탐)
- **필요 수준:** 티어1·2 모든 수준. D-CTL-004(D≥2)와 U-CTL-001(U≥1)의 관측 측면.
- **처방:** 티어0: 해당 없음. 티어1: Cloud Run 시작·liveness 프로브 / ECS·ALB 헬스 체크는 얕은 경로로. 티어2: liveness는 얕게 + readiness보다 높은 failureThreshold.
- **검증:** P4에서 DB를 차단(V-037)했을 때 재시작 수가 늘지 않는지, Redis만 차단했을 때 읽기는 계속되는지 확인. 스트레스 중 liveness 실패 재시작 0건.
- **비용 영향:** 중립.
- **출처:** https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/ ("Incorrect implementation of liveness probes can lead to cascading failures", 같은 엔드포인트라면 더 높은 failureThreshold), 2026-10-01 확인

### O-053 startup probe(느린 기동 보호)
- **무엇/왜:** 기동이 느린 앱(마이그레이션 확인, 캐시 예열, JVM)은 startup probe로 liveness를 늦춘다. 그렇지 않으면 기동 중 liveness가 죽여서 영원히 못 뜬다.
- **실패 양상:** 스파이크 때 새 Pod가 기동 중에 liveness로 죽고 다시 뜨기를 반복해 확장이 실패한다.
- **신호:** 🟢 `startupProbe` 설정 / 🔴 `initialDelaySeconds`만 크게(평시 재시작 감지도 늦어짐) 또는 없음 + 기동 30초 이상
- **필요 수준:** T≥1(오토스케일) 티어2. 티어1은 플랫폼 시작 프로브.
- **처방:** 티어1: Cloud Run startup probe / ECS `healthCheck.startPeriod`. 티어2: `startupProbe` failureThreshold × period ≥ 최악 기동 시간.
- **검증:** P4 스파이크에서 새 Pod의 기동~Ready 시간 분포를 측정하고 기동 중 재시작 0건 확인. 확장 완료 시간(V-018)에 반영.
- **비용 영향:** 중립.
- **출처:** https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/ (startup probe의 목적, 2026-10-01 확인)

### O-054 헬스 체크 엔드포인트의 비용과 노출
- **무엇/왜:** 헬스 체크는 초당 여러 번 호출되므로 로그를 남기지 않고, 무거운 쿼리를 하지 않고, 외부에서 호출할 수 없게 한다. LB용(얕은)과 내부 진단용(깊은)을 분리한다.
- **실패 양상:** 깊은 헬스 체크가 DB에 초당 수십 쿼리를 보내고, 외부에서 두드리면 DoS 경로가 된다.
- **신호:** 🟢 `access_log off` (SWA `/nginx-health`), 내부 경로 외부 404 (SWA) / 🔴 헬스 엔드포인트가 `SELECT count(*)`, 공개 노출
- **필요 수준:** 모든 수준(헬스 체크가 있는 한).
- **처방:** 공통: 얕은 헬스는 상수 응답, 깊은 체크는 결과를 수 초 캐시하고 내부에서만.
- **검증:** P4 평시 부하에서 헬스 체크가 차지하는 DB 쿼리 비율 측정, 외부 접근 404 확인.
- **비용 영향:** 감소.
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### O-055 종료 과정의 관측(SIGTERM 수신·드레인 완료 로그)
- **무엇/왜:** SIGTERM 수신 시각, readiness 실패 전환, 진행 중 요청 수, 종료 완료를 로그로 남긴다. 배포 중 5xx가 나면 종료 순서 문제인지 바로 안다.
- **실패 양상:** 롤링 배포마다 5xx가 몇 건 나는데 원인(드레인 전 종료, preStop 부족)을 증명할 수 없다.
- **신호:** 🟢 `ops.sigterm_handler` 사실 + 종료 로그, 종료 시 진행 중 요청 수 기록 / 🟡 핸들러는 있지만 로그 없음 / 🔴 핸들러 없음(U-CTL-002 미충족)
- **필요 수준:** U≥1.
- **처방:** 공통: 종료 훅에 구조화 로그 2줄(시작·완료) + 종료 소요 시간.
- **검증:** 배포 중 부하(V-046) 실행 후 각 Pod의 "SIGTERM→완료" 시간이 유예 시간(k8s 30초, Cloud Run 10초) 안인지 로그로 확인.
- **비용 영향:** 중립.
- **출처:** https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/ (종료 흐름, 2026-10-01 확인). 종료 로그 자체는 일반 원칙. ⚠️근거없음

### O-056 버전·빌드 정보 노출
- **무엇/왜:** 실행 중인 버전을 지표(`build_info{version,commit}`)와 내부 엔드포인트로 노출한다. 롤아웃 중 어느 Pod가 어느 버전인지, 장애 시점 버전이 무엇인지 확인한다.
- **실패 양상:** "고쳤다는 버전이 실제로 배포됐나?"를 확인하지 못한다. 롤백이 됐는지 모른다.
- **신호:** 🟢 `build_info` 게이지, `/version` 내부 경로, OTel `service.version` / 🔴 없음 + 이미지 태그 `latest`
- **필요 수준:** U≥2(자동 롤백 검증에 필요).
- **처방:** 공통: CI가 커밋 SHA 주입(O-034와 같은 값).
- **검증:** 실패 버전 롤백 검증(V-047)에서 롤백 후 모든 Pod의 버전 값이 이전 SHA인지 확인.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### O-057 기동 시 설정 검증과 명확한 실패 로그
- **무엇/왜:** 필수 환경변수·비밀이 없거나 형식이 틀리면 기동 단계에서 어떤 키가 문제인지 한 줄로 남기고 즉시 종료한다. 요청 처리 중에 처음 터지면 원인이 흐려진다.
- **실패 양상:** 배포는 성공했는데 첫 결제 요청에서 `undefined` 키로 500. CrashLoop 로그에 스택만 있고 무엇이 빠졌는지 없다.
- **신호:** 🟢 pydantic `BaseSettings`, `zod`/`envalid` 스키마 검증 / 🔴 `os.environ.get("X")`를 요청 처리 경로에서 처음 읽음, 기본값으로 `localhost`(`config.localhost_hardcoded`)
- **필요 수준:** 모든 수준.
- **처방:** 공통: 설정 스키마 + 기동 검증. P2 코드 처방 후보.
- **검증:** P4 스모크 전, 필수 변수 하나를 뺀 배포가 Ready에 도달하지 못하고 로그에 키 이름이 나오는지(배포 자동 롤백 V-047과 결합).
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인). 설정은 환경변수로 둔다는 원칙은 설계 문서 S1(12factor.net/config, 이번 작업에서 재확인 안 함). ⚠️근거없음

### O-058 컨테이너 런타임 계약 준수(포트·바인딩·쓰기 경로)
- **무엇/왜:** 플랫폼이 주는 `PORT` 환경변수로, `0.0.0.0`에 바인딩하고, 루트 파일시스템이 아닌 지정 경로에만 쓴다. 이 계약을 어기면 헬스 체크 실패로만 보여 원인 파악이 늦다.
- **실패 양상:** 앱이 `127.0.0.1:3000`에 떠서 Cloud Run 헬스 체크가 계속 실패. 읽기 전용 루트에서 임시 파일 쓰기 실패.
- **신호:** 🔴 `listen(3000)` 하드코딩, `host="127.0.0.1"`, 컨테이너 루트 경로에 쓰기 / 🟢 `process.env.PORT`, `--host 0.0.0.0`, `/tmp`·emptyDir만 쓰기
- **필요 수준:** 티어1·2 모든 수준.
- **처방:** P2 코드 처방(포트·호스트), P3 매니페스트(readOnlyRootFilesystem + emptyDir).
- **검증:** P4 스모크(V-001)가 첫 단계로 이 계약을 확인(헬스 체크 통과, 쓰기 경로 동작).
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인). Cloud Run 컨테이너 계약은 설계 문서 S3(이번 작업에서 재확인 안 함). ⚠️근거없음

## A7. 운영 준비도(사람·절차·주변 감시)

### O-059 대시보드(수준별 최소 구성)
- **무엇/왜:** 서비스마다 첫 화면 하나: 골든 시그널 4개 + SLO 예산 + 의존성 상태 + 최근 배포 표시. 수집했지만 대시보드에도 알림에도 안 쓰는 신호는 지운다.
- **실패 양상:** 장애 때 수십 개 대시보드를 뒤지거나, 대시보드가 아예 없어 CLI로 지표를 하나씩 조회한다.
- **신호:** 🟢 대시보드 JSON/Terraform(`aws_cloudwatch_dashboard`, `google_monitoring_dashboard`, Grafana provisioning) / 🔴 L2 이상인데 없음 / 🟡(과잉) L1인데 서비스당 대시보드 여러 개 + 유료 Grafana
- **필요 수준:** 최대 필요 수준 L2 이상(§17.4). L1은 플랫폼 기본 화면으로 충분.
- **처방:** 티어0: 플랫폼 기본. 티어1: CloudWatch 사용자 대시보드(무료 3개) / Cloud Monitoring 대시보드. 티어2: 관리형 Grafana 또는 Cloud Monitoring에 PromQL.
- **검증:** P4 장애 주입 동안 대시보드 첫 화면만 보고 주입된 장애(어느 의존성)를 식별할 수 있는지 게임데이(V-057)에서 확인.
- **비용 영향:** 소폭 증가(무료 할당 초과 시).
- **출처:** https://sre.google/sre-book/monitoring-distributed-systems/ (대시보드 정의, 안 쓰는 신호는 제거 후보), https://aws.amazon.com/cloudwatch/pricing/ (무료 대시보드 3개), 2026-10-01 확인

### O-060 런북(알림마다 대응 절차 링크)
- **무엇/왜:** 페이지 알림마다 "무엇을 확인하고 무엇을 하나"를 적은 런북 링크를 붙인다. 새벽의 온콜·바이브코더 본인이 생각 없이 따라 할 수 있어야 한다.
- **실패 양상:** 알림은 왔는데 무엇을 해야 할지 몰라 RTO를 넘긴다. 절차는 문서에만 있고 한 번도 실행된 적 없다.
- **신호:** 🟢 알림 정의에 `runbook_url` 주석, `docs/runbooks/*.md` / 🔴 페이지 알림 + 런북 없음 / 🟡 런북이 있으나 명령어가 현재 인프라와 다름(오래됨)
- **필요 수준:** 최대 필요 수준 L2 이상. D=L3는 복구 절차 문서가 통제(D-CTL-006).
- **처방:** 공통: infrafit이 생성하는 알림마다 런북 초안을 함께 생성(알림 이유, 확인 대시보드, 조치 명령, 에스컬레이션).
- **검증:** 게임데이(V-057)에서 런북만 보고 처음 보는 사람이 복구할 수 있는지, 걸린 시간 측정(V-059).
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_testing_resiliency_game_days_resiliency.html (런북 적용 범위 검증, "document your procedures, but never exercise them" 안티패턴, 2026-10-01 확인)

### O-061 온콜과 에스컬레이션 경로
- **무엇/왜:** 알림을 받을 사람, 응답 시간 목표, 응답 없을 때 다음 사람을 정한다. 1인 개발자도 "누가, 언제 깨어나는가"를 정해야 한다.
- **실패 양상:** 알림이 공용 채널에 쌓이고 아무도 책임지지 않는다. 혼자 운영하는 사람이 휴가 중 장애.
- **신호:** 🟢 온콜 도구 연동(Opsgenie·PagerDuty 류) 설정, `ONCALL.md` / 🔴 L3인데 알림 수신자 1명 + 에스컬레이션 없음
- **필요 수준:** 최대 필요 수준 L3에서 필수. L2는 업무 시간 대응 + 페이지 수신자 지정. L0~L1은 이메일로 충분.
- **처방:** 공통: 수준에 따라 L1 이메일, L2 메신저 + 지정 수신자, L3 온콜 도구 + 2단계 에스컬레이션.
- **검증:** 시험 페이지에서 1차 수신자 무응답 시 2차로 넘어가는지와 그 시간 확인.
- **비용 영향:** 증가(온콜 도구·인건비). L1 이하에서는 과잉.
- **출처:** https://sre.google/sre-book/being-on-call/ (명확한 에스컬레이션 경로, 2026-10-01 확인)

### O-062 인시던트 대응 체계(지휘·소통·운영 역할)
- **무엇/왜:** 장애가 커지면 지휘자(IC), 소통 담당(CL), 운영 담당(OL)을 나눈다. 빨리 "인시던트 선언"을 하는 것이 해결을 앞당긴다.
- **실패 양상:** 여러 사람이 같은 서버에 동시에 조치해 상황을 악화시키고, 고객 공지는 아무도 하지 않는다.
- **신호:** 🟢 인시던트 절차 문서, 심각도 정의(SEV1~3) / 🔴 D≥2 B2B인데 없음
- **필요 수준:** D≥2 또는 최대 필요 수준 L3. 1인 운영(L1)에는 과잉 — 체크리스트 한 장으로 대체.
- **처방:** 공통: 심각도 표 + 역할 + 선언 기준(예: SLO 페이지 2개 이상 동시) 템플릿.
- **검증:** 게임데이(V-057)에서 역할 지정·선언까지 걸린 시간 측정.
- **비용 영향:** 중립(문서).
- **출처:** https://sre.google/workbook/incident-response/ (IC·CL·OL, 조기 선언의 효과, 2026-10-01 확인)

### O-063 비난 없는 사후 분석
- **무엇/왜:** 사용자 영향, 데이터 손실, 수동 개입, 모니터링 실패(사람이 먼저 발견) 같은 기준을 넘으면 사후 분석을 쓴다. 원인과 개선 항목을 남기고, 개선 항목은 추적한다.
- **실패 양상:** 같은 장애가 반복된다. 특히 "모니터링이 못 잡음"이 반복되면 관측 결함이 고쳐지지 않는다.
- **신호:** 🟢 `postmortems/` 디렉터리, 템플릿 / 🔴 L2 이상 + 없음
- **필요 수준:** 최대 필요 수준 L2 이상.
- **처방:** 공통: 템플릿 + 작성 기준. 개선 항목 중 관측 관련은 infrafit 규칙 후보로 되먹임(§17.5).
- **검증:** 게임데이 후 사후 분석 문서가 실제로 작성되고 개선 항목이 이슈로 등록됐는지 확인.
- **비용 영향:** 중립.
- **출처:** https://sre.google/sre-book/postmortem-culture/ (비난 없는 정의, 작성 기준에 "Monitoring failures" 포함, 2026-10-01 확인)

### O-064 변경 이력과 배포 마커
- **무엇/왜:** 장애의 다수는 변경에서 온다. 배포·설정 변경·기능 플래그 변경 시각을 대시보드에 표시하고 이력으로 남기면 "무엇이 바뀌었나"에 바로 답한다.
- **실패 양상:** 오류율이 14:02에 올랐는데 14:00에 누가 무엇을 배포했는지 찾는 데 30분이 걸린다.
- **신호:** 🟢 CI가 배포 이벤트를 관측 백엔드에 기록(어노테이션), GitOps 커밋 이력, 기능 플래그 감사 로그 / 🟡 CI 로그에만 남음 / 🔴 콘솔 수동 배포
- **필요 수준:** U≥2. L1은 CI 실행 이력으로 충분.
- **처방:** 공통: 배포 파이프라인 마지막 단계에서 어노테이션 이벤트 기록 + 버전 지표(O-056).
- **검증:** P4 배포 중 부하(V-046) 후 대시보드에 배포 마커가 보이는지 확인.
- **비용 영향:** 중립.
- **출처:** https://sre.google/sre-book/introduction/ ("roughly 70% of outages are due to changes in a live system", 2026-10-01 확인)

### O-065 감사 로그(클라우드 API·k8s API)
- **무엇/왜:** 누가 언제 어떤 인프라를 바꿨는지 기록한다. AWS CloudTrail 이벤트 기록은 최근 90일 관리 이벤트를 무료로 보여주고, 장기 보관은 트레일(S3)이 필요하다. GCP 관리 활동 로그는 항상 켜져 있고 데이터 액세스 로그는 대부분 기본 꺼짐. k8s 감사 로그는 정책 수준(None/Metadata/Request/RequestResponse)을 고른다.
- **실패 양상:** 보안 그룹이 열린 이유, DB가 삭제된 경위를 90일 뒤에는 알 수 없다. 반대로 RequestResponse 수준을 전부 켜서 로그 비용 폭증.
- **신호:** 🟢 Terraform `aws_cloudtrail` + S3 수명 주기, GKE/EKS 감사 로그 활성화(`enabled_cluster_log_types = ["audit"]`) / 🔴 B2B·결제인데 트레일 없음 / 🟡(과잉) L1에 데이터 액세스 로그 전체 활성화
- **필요 수준:** D≥2 또는 C=L3에서 장기 보관 필요. L1은 기본 제공(90일 이벤트 기록, GCP 관리 활동)으로 충분.
- **처방:** 티어1/2: 트레일 1개(관리 이벤트, S3 사본 1개는 CloudTrail 요금 없음 — S3 저장 비용만) + 수명 주기. k8s는 Metadata 수준 기본.
- **검증:** 테스트 IAM 변경을 한 뒤 감사 로그에서 행위자·시각이 검색되는지 확인.
- **비용 영향:** 소폭 증가(저장).
- **출처:** https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-user-guide.html (90일 이벤트 기록, 관리 이벤트 사본 1개 무료 전달), https://docs.cloud.google.com/logging/docs/audit (관리 활동 항상 켜짐, 데이터 액세스 기본 꺼짐), https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/ (감사 수준 4가지), 2026-10-01 확인

### O-066 디버그 접근 경로(셸 없는 이미지에서도)
- **무엇/왜:** 운영 중 문제를 조사할 수단을 미리 정한다. distroless·최소 이미지는 셸이 없으므로 k8s ephemeral container(`kubectl debug`)나 플랫폼 콘솔 접근을 쓴다. 접근 자체는 감사 로그에 남겨야 한다.
- **실패 양상:** 장애 중 조사하려고 디버그 도구가 든 이미지를 급히 다시 빌드·배포해 상황이 바뀐다. 또는 상시 SSH·디버그 포트를 열어 보안 구멍을 만든다.
- **신호:** 🟢 런북에 `kubectl debug` 절차, ECS Exec 활성화(`enable_execute_command`)와 그 로그 설정 / 🔴 이미지에 `sshd`, 공개 디버그 포트(`--inspect=0.0.0.0`, `pprof` 공개) / 🟡 디버그 수단 없음 + distroless
- **필요 수준:** 최대 필요 수준 L2 이상에서 절차 문서화. L1은 로그·플랫폼 콘솔로 충분.
- **처방:** 티어1: ECS Exec(감사 로그 설정) / Cloud Run은 로그·트레이스 중심. 티어2: ephemeral container + RBAC로 권한 제한.
- **검증:** 게임데이에서 디버그 경로로 실행 중 Pod의 열린 커넥션 수를 확인해 보고, 그 행위가 감사 로그에 남는지 확인.
- **비용 영향:** 중립.
- **출처:** https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/ (디버그 유틸리티가 없는 이미지에 ephemeral 디버그 컨테이너, 2026-10-01 확인)

### O-067 백업 성공 여부와 복원 가능성 모니터링
- **무엇/왜:** "백업 설정이 있다"와 "어젯밤 백업이 성공했고 복원된다"는 다르다. 백업 작업 실패 알림과 마지막 성공 백업 나이를 감시하고, 주기적 자동 복원 테스트로 복원 가능성과 복원 시간을 측정한다.
- **실패 양상:** 권한 변경·용량 초과로 백업이 몇 주째 실패했는데 복원이 필요한 날에야 안다. 복원 시간이 RTO를 훨씬 넘는다.
- **신호:** 🟢 AWS Backup 복원 테스트 계획(`aws_backup_restore_testing_plan`), 백업 작업 실패 이벤트 알림, `pg_dump` 크론 + 성공 시각 지표 / 🔴 D≥1 + 자체 백업 스크립트 + 성공 확인 없음 / 🟡 관리형 자동 백업만 있고 복원 시험 없음
- **필요 수준:** D≥1(D-CTL-001의 관측 측면). 자동 복원 테스트는 D≥2.
- **처방:** 티어0: Supabase 등 플랫폼 백업 상태 확인 + 월 1회 수동 복원. 티어1/2: 관리형 자동 백업 + AWS Backup 복원 테스트(테스트당 과금) / Cloud SQL 백업 실패 알림 + 정기 복원 Job.
- **검증:** 복원 리허설(V-056)에서 실제 복원 시간과 데이터 시점(RPO)을 측정. 백업을 일부러 실패시켜(권한 제거) 알림이 오는지 확인.
- **비용 영향:** 증가(복원 테스트 자원). D≥2에서는 필요 비용.
- **출처:** https://docs.aws.amazon.com/aws-backup/latest/devguide/restore-testing.html (주기적 복원 가능성 평가와 복원 시간 측정, 테스트당 비용), 2026-10-01 확인. 백업 작업 실패 이벤트 세부는 일반 원칙. ⚠️근거없음

### O-068 인증서 만료 감시
- **무엇/왜:** 만료된 TLS 인증서는 서비스 전체를 즉시 멈춘다. 관리형 인증서는 자동 갱신되지만, 가져온(imported) 인증서나 DNS 검증 실패(CAA 등)는 사람이 개입해야 한다. ACM은 만료 45일(사설·가져온)·30일(공개) 전부터 매일 만료 임박 이벤트를 보낸다.
- **실패 양상:** 수동 발급 인증서가 만료되어 모든 사용자가 브라우저 경고를 본다. 내부 서비스 간 mTLS 인증서 만료로 내부 호출 전부 실패.
- **신호:** 🟢 ACM 관리형 인증서 + EventBridge `ACM Certificate Approaching Expiration`/`Renewal Action Required` 규칙, cert-manager + 만료 지표, 업타임 체크의 인증서 만료 확인 / 🔴 저장소에 `.pem`·`.crt` 파일 + 수동 갱신, `aws_acm_certificate`가 import 방식 + 알림 없음
- **필요 수준:** 사용자 도메인·TLS를 직접 관리하면 모든 수준. 플랫폼 관리 도메인(티어0 기본 도메인)은 해당 없음.
- **처방:** 티어0: 플랫폼 자동 인증서. 티어1: ACM·Google 관리형 인증서 + 갱신 실패 이벤트 알림. 티어2: cert-manager + `certmanager_certificate_expiration_timestamp_seconds` 알림(14일 전).
- **검증:** 만료가 짧은 테스트 인증서(스테이징)로 알림이 임계 시점에 오는지 확인. 업타임 체크가 만료 임박을 경고하는지.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/acm/latest/userguide/supported-events.html (45일/30일 전부터 매일 이벤트, 가져온 인증서는 재가져오기 필요, 갱신 조치 필요 이벤트), 2026-10-01 확인

### O-069 비용 이상 감시와 예산 알림
- **무엇/왜:** 예산 알림은 지출이 임계에 닿으면 알리고(자동 차단은 아님), 비용 이상 탐지는 평소 패턴에서 벗어난 지출을 잡는다. 둘 다 데이터 지연(최대 24시간)이 있으므로 사용량 기반 지표(요청 수·인스턴스 수)와 함께 본다.
- **실패 양상:** 오토스케일 상한 없음 + 봇 트래픽, 무한 재시도 LLM 호출, 로그 폭증으로 하룻밤에 월 예산을 넘긴다.
- **신호:** 🟢 Terraform `aws_budgets_budget`, `aws_ce_anomaly_monitor`, `google_billing_budget` / 🔴 유료 외부 API 호출(COST-008) 또는 오토스케일 상한 없음 + 예산 알림 없음
- **필요 수준:** 모든 수준(설계 원칙 5: 비용은 모든 판정의 필터). 바이브코더 앱에 특히 중요.
- **처방:** 티어0: 플랫폼 지출 한도·알림(지원 시 하드 캡). 티어1/2: 예산 알림(50/80/100%) + AWS Cost Anomaly Detection(하루 약 3회 실행). P4 견적 대비 120% 임계 권장.
- **검증:** P4 소크의 자원 사용량 기반 비용 환산과 다음 날 청구 데이터를 비교(§17.3)해 오차 기록. 예산 알림 시험 임계(현재 지출 + 소액)로 수신 확인.
- **비용 영향:** 감소(사고 방지). 도구 자체는 무료 또는 저렴.
- **출처:** https://docs.aws.amazon.com/cost-management/latest/userguide/manage-ad.html (하루 약 3회, Cost Explorer 최대 24시간 지연, 새 서비스는 10일 이력 필요), https://docs.cloud.google.com/billing/docs/how-to/budgets (알림 전용 예산은 사용을 자동으로 막지 않음), 2026-10-01 확인

### O-070 용량 계획(유기적·비유기적 성장)
- **무엇/왜:** 자연 증가(유기적)와 마케팅·이벤트(비유기적) 수요를 예측하고, 정기 부하 테스트로 "자원 1단위 = 사용자 N명" 관계를 갱신한다. 자원 포화 추세 알림은 페이지가 아니라 티켓이다.
- **실패 양상:** 예고된 이벤트(T L2) 날 노드 한도·DB 크기·계정 할당량(vCPU 쿼터)에 막힌다.
- **신호:** 🟢 HPA·노드 그룹 상한과 할당량 기록, 정기 브레이크포인트 테스트 결과 / 🔴 T≥2 + 이벤트 신호 + 사전 증설 계획 없음(T-CTL-005와 연결)
- **필요 수준:** T≥2.
- **처방:** 공통: P4 브레이크포인트(V-006) 결과로 "동시 N명까지"를 리포트에 넣고, 실측 트래픽 추세(O-072)와 비교해 한도 도달 예상일을 계산. 클라우드 할당량 확인 포함.
- **검증:** 분기마다 브레이크포인트 재측정, 예측 한도와 실측 한도 차이 기록.
- **비용 영향:** 중립(과잉 증설 방지로 감소 가능).
- **출처:** https://sre.google/sre-book/introduction/ (유기적·비유기적 성장, 정기 부하 테스트로 원시 용량과 서비스 용량 연결), https://prometheus.io/docs/practices/alerting/ (용량 알림), 2026-10-01 확인

### O-071 관측 과잉 탐지(안 쓰는 신호·과한 보존·과한 도구)
- **무엇/왜:** 관측도 비용이다. 대시보드·알림 어디에도 안 쓰이는 지표, 분기에 한 번도 쓰이지 않는 수집·알림, L1 서비스의 유료 APM·100% 트레이스는 축소 처방 대상이다.
- **실패 양상:** 관측 요금이 인프라 요금을 넘는다. 아무도 안 보는 알림이 피로만 쌓는다.
- **신호:** 🔴(과잉) 최대 필요 수준 L1 + 유료 APM 에이전트(`ddtrace`, `newrelic`) + 트레이스 샘플링 1.0, 로그 보존 365일 + D≤1 / 🟢 수준에 맞는 구성(§17.4 표)
- **필요 수준:** 모든 수준(축소 규칙).
- **처방:** 공통: §17.4 표보다 높은 관측 구성은 `kind: reduce` 처방 + 월 절감액.
- **검증:** 관측 요금 항목을 청구 데이터에서 분리해 전체 대비 비율을 리포트에 표시.
- **비용 영향:** 감소.
- **출처:** https://sre.google/sre-book/monitoring-distributed-systems/ ("rarely exercised ... should be up for removal", 안 쓰는 신호 제거), 2026-10-01 확인

### O-072 관측에서 진단으로 되먹임(실측으로 가정 교체)
- **무엇/왜:** 운영 관측의 실측 동시 접속·피크·자원 사용량으로 P1의 가정(§4.3)을 주기적으로 교체하고 진단을 다시 돌린다. 수준 상향·티어 하향·right-sizing이 여기서 나온다(§17.5).
- **실패 양상:** 가정한 트래픽의 1/10만 오는데 티어2를 계속 유지(낭비), 또는 가정의 10배가 오는데 수준이 그대로(위험).
- **신호:** 🟢 `infrafit.yaml`의 가정이 최근 실측 날짜를 가짐 / 🔴 가정 값이 초기 기본값 그대로 + 운영 3개월 이상
- **필요 수준:** 운영 관측(C 단계)이 있는 모든 수준. 주기는 기본 2주.
- **처방:** 공통: 실측 피크 동시 접속(LB 지표), p95, CPU·메모리 사용량을 가정 키로 매핑하는 수집기.
- **검증:** 되먹임 실행 후 리포트의 가정 값 출처가 "실측(기간)"으로 바뀌었는지 확인.
- **비용 영향:** 감소(과잉 축소) 또는 증가(위험 해소).
- **출처:** 일반 원칙(설계 문서 §2-3, §17.5) ⚠️근거없음

---

# B. 검증 방법 요소 (P4 테스트 기법 카탈로그)

모든 검증은 필요 수준이 L0인 시나리오에는 적용하지 않는다(§17.2). 결과는 해당 통제의 상태를 "설정 확인"에서 "동작 확인"으로 바꾸는 근거로 `report.json`에 붙는다.

## B1. 부하 테스트 종류

### V-001 스모크 테스트(배포 직후 최소 부하)
- **무엇/왜:** 최소 부하(VU 1~5, 1분)로 스크립트가 동작하고 핵심 경로가 성공하는지 본다. 다른 모든 검증의 선행 조건이다. 스크립트 오류를 시스템 결함으로 오인하지 않게 한다.
- **실패 양상:** 30분짜리 부하 테스트가 로그인 스크립트 오류로 처음부터 실패했는데 "시스템이 못 견딤"으로 판정한다.
- **신호:** 🟢 `k8s/tests/smoke.sh`, `scripts/smoke_backend.py`, Playwright `e2e/smoke.spec.ts`, `make loadtest-quick` (SWA) / 🔴 부하 스크립트만 있고 스모크 없음
- **필요 수준:** 모든 수준(배포가 있으면 L0 포함).
- **처방:** 공통: P4 첫 단계로 스모크 → 통과해야 다음 단계. 검사 항목: 헬스, 핵심 읽기·쓰기, 외부 비공개 경로 404(O-029).
- **검증:** 스모크 자체를 일부러 깨진 배포(잘못된 환경변수)에 돌려 실패를 내는지 확인(음성 대조).
- **비용 영향:** 중립.
- **출처:** https://grafana.com/docs/k6/latest/testing-guides/test-types/ (스모크 테스트 정의, 2026-10-01 확인)

### V-002 평균 부하 테스트
- **무엇/왜:** 가정한 평시 부하(T L1 기본 평시 동시 50)로 일정 시간 돌려 평상시 지연·오류·자원 사용량의 기준선을 만든다. right-sizing(COST-006)과 소크 비교의 기준이다.
- **실패 양상:** 기준선 없이 스파이크 결과만 있어 "평소보다 얼마나 나빠졌나"를 말할 수 없다.
- **신호:** 🟢 k6 `constant-arrival-rate` 평시 단계(SWA `disaster.js`의 BASELINE 단계) / 🔴 없음
- **필요 수준:** T≥1.
- **처방:** 공통: 10~15분, 평시 요청률, 결과는 p50/p95/p99·오류율·Pod당 CPU·메모리.
- **검증:** 같은 조건 2회 반복 결과의 p95 차이가 10% 안인지(재현성, V-024).
- **비용 영향:** 테스트 자원만큼 일시 증가.
- **출처:** https://grafana.com/docs/k6/latest/testing-guides/test-types/ (average-load, 2026-10-01 확인)

### V-003 스텝 부하(가정 피크까지 계단식)
- **무엇/왜:** 평시에서 가정 피크(T L1 = 평시×3, L2 = ×10)까지 계단식으로 올리며 각 단계에서 안정 상태를 본다. 오토스케일이 따라오는지, 어느 단계에서 지연이 꺾이는지 보인다.
- **실패 양상:** 한 번에 피크를 걸어 확장 지연 때문인지 용량 부족 때문인지 구분하지 못한다.
- **신호:** 🟢 단계별 태그(`step`, `op`) 지표 (SWA `steps-summary.json`의 `http_req_duration{step:3,op:read_next}`, nginx perf 로그의 `X-Load-Step` 헤더) / 🔴 단일 단계만
- **필요 수준:** T=L1, L2 (§17.2).
- **처방:** 공통: 단계 4~6개, 단계당 3~5분(HPA 안정화 창보다 길게), 단계 태그를 요청 헤더로 보내 서버 로그와 결합.
- **검증:** 단계별 p95·오류율 표가 나오고, 서버 쪽 로그도 같은 단계 태그로 집계되는지 확인.
- **비용 영향:** 일시 증가.
- **출처:** 일반 원칙(출처 미확인). 단계(stages) 구성은 https://grafana.com/docs/k6/latest/using-k6/scenarios/executors/ 의 ramping 실행기 범위. ⚠️근거없음

### V-004 스파이크 테스트(1분 안에 20배)
- **무엇/왜:** 예고 없는 폭증(T L3: 평시×20, 1분 안)을 재현한다. 확장 지연 동안 큐·백프레셔·리밋·최소 인스턴스가 사용자 영향을 막는지 본다. 두 번째 스파이크로 축소 후 재확장도 본다.
- **실패 양상:** 스텝 테스트는 통과했는데 실제 폭증 때 콜드 스타트·노드 프로비저닝 시간 동안 대량 5xx.
- **신호:** 🟢 SWA `loadtest/disaster.js`(평시 → 30초 만에 20배 → 5분 유지 → 감소 → 2차 폭증, `ramping-arrival-rate`) / 🔴 T=L3인데 없음
- **필요 수준:** T=L3.
- **처방:** 공통: 오픈 모델(V-008), 2회 스파이크, 설계된 거절(V-016) 분리 집계.
- **검증:** 통과 기준(§17.2): 피크 p95 < 1초, 서버 오류율 < 1%, 확장 완료 시간 기록. 생성기 포화가 없었음을 함께 증명(V-010).
- **비용 영향:** 일시 증가(피크 자원).
- **출처:** https://grafana.com/docs/k6/latest/testing-guides/test-types/ (spike, 2026-10-01 확인)

### V-005 스트레스 테스트(가정 초과 부하)
- **무엇/왜:** 가정 피크를 넘는 부하로 시스템이 어떻게 무너지는지 본다. 목표는 "우아한 실패": 오류가 무작위로 퍼지지 않고 설계된 거절(503+Retry-After, 429)로 나오고, 부하가 빠지면 스스로 회복하는지.
- **실패 양상:** 한도를 넘자 DB 커넥션 고갈 → 재시작 폭주 → 부하가 빠진 뒤에도 회복하지 않는 연쇄 장애.
- **신호:** 🟢 피크 이후 회복 단계가 있는 시나리오 / 🔴 T≥2인데 한도 초과 동작 미검증
- **필요 수준:** T≥2(L3 필수).
- **처방:** 공통: 가정 피크의 1.5~2배, 이후 평시로 복귀하는 구간 포함.
- **검증:** 초과 구간의 응답 분포(설계된 거절 비율 vs 기타 5xx), 부하 감소 후 오류율이 평시로 돌아오는 시간 측정.
- **비용 영향:** 일시 증가.
- **출처:** https://grafana.com/docs/k6/latest/testing-guides/test-types/ (stress, 2026-10-01 확인)

### V-006 브레이크포인트 테스트("동시 N명까지")
- **무엇/왜:** 부하를 서서히 올려 SLO가 깨지는 지점을 찾는다. P4 리포트의 "동시 N명까지, 월 $X"의 N이 여기서 나온다. 오토스케일 상한을 일시적으로 풀지, 상한 그대로 잴지를 명시한다.
- **실패 양상:** 한도를 모른 채 운영하다 이벤트 날 처음 알게 된다.
- **신호:** 🟢 상한까지 선형 증가 + `abortOnFail` 임계 / 🔴 없음
- **필요 수준:** T≥2. T=L1은 선택(가정 피크 통과로 충분).
- **처방:** 공통: `ramping-arrival-rate`로 선형 증가, SLO 위반 시 중단(`abortOnFail` + `delayAbortEval`), 깨진 지점의 요청률을 동시 사용자 수로 환산(생각 시간 가정 명시).
- **검증:** 같은 구성에서 2회 측정한 한계 차이가 10% 안인지. 한계 지점에서 병목 자원(USE)이 식별되는지.
- **비용 영향:** 일시 증가.
- **출처:** https://grafana.com/docs/k6/latest/testing-guides/test-types/ (breakpoint), https://grafana.com/docs/k6/latest/using-k6/thresholds/ (`abortOnFail`, `delayAbortEval`), 2026-10-01 확인

### V-007 소크 테스트(평시 + 주기적 폭증, 2~24시간)
- **무엇/왜:** 긴 시간 부하를 유지해 짧은 테스트에서 안 보이는 문제(메모리 누수, 커넥션 증가, 큐 지연 누적, 디스크·로그 증가, 실제 시간당 비용)를 찾는다. 길이는 최대 필요 수준으로: L1 2시간, L2 6시간, L3 24시간(§17.3).
- **실패 양상:** 배포 후 사흘째 OOM 재시작, 일주일째 디스크 가득.
- **신호:** 🟢 장시간 시나리오 + 처음·마지막 30분 비교 자동화 / 🔴 L2 이상인데 수십 분 테스트만
- **필요 수준:** 최대 필요 수준 L1 이상(§17.3).
- **처방:** 공통: 평시 부하 + 1시간마다 피크. 생성기는 별도 장기 실행 VM/Job.
- **검증:** 처음 30분 vs 마지막 30분의 메모리(O-023), DB 커넥션(O-018), 큐 lag(O-020), p95. 추세가 계속 오르면 실패. 자원 사용량 기반 비용 vs 견적.
- **비용 영향:** 증가(최대 24시간 운영 비용). 수준별 길이로 통제.
- **출처:** https://grafana.com/docs/k6/latest/testing-guides/test-types/ (soak, 2026-10-01 확인)

## B2. 부하 모델·생성기·데이터

### V-008 오픈 모델 vs 클로즈드 모델
- **무엇/왜:** 클로즈드 모델(VU가 응답을 받아야 다음 요청)은 시스템이 느려지면 부하도 같이 줄어 실제보다 좋은 결과를 낸다. 실제 사용자는 서버가 느리다고 덜 오지 않으므로 공개 서비스 검증은 도착률 기반 오픈 모델(`constant-arrival-rate`, `ramping-arrival-rate`)로 한다.
- **실패 양상:** 서버가 2초씩 걸리자 VU가 요청을 덜 보내 "오류 0%"로 통과하지만, 실제 폭증에서는 요청이 쌓여 무너진다.
- **신호:** 🟢 `executor: 'ramping-arrival-rate'` (SWA `disaster.js`) / 🔴 `vus`/`duration`만 지정(`constant-vus`, `ramping-vus`) + 지연 임계 판정 / 🟡 Locust·JMeter 기본 스레드 그룹(클로즈드)
- **필요 수준:** T≥1의 모든 부하 검증.
- **처방:** 공통: P4 표준 시나리오는 arrival-rate 실행기. 클로즈드 모델은 "세션 수 고정" 사내 도구(T=L0~L1 사내)에만.
- **검증:** 같은 목표 요청률에서 서버에 인위적 지연(HTTPChaos 500ms)을 넣었을 때 실제 달성 요청률이 유지되는지(오픈) 확인.
- **비용 영향:** 중립.
- **출처:** https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/open-vs-closed/ (클로즈드 모델의 조정 누락, 오픈 모델은 응답 시간이 부하에 영향 없음), https://grafana.com/docs/k6/latest/using-k6/scenarios/executors/ (arrival-rate 실행기), 2026-10-01 확인

### V-009 미발사 요청(dropped_iterations) 감시와 VU 여유
- **무엇/왜:** 오픈 모델에서도 VU가 모자라면 목표 도착률을 못 채우고 그 요청은 "보내지 않은 것"이 된다. `dropped_iterations`가 0이 아니면 그 테스트는 목표 부하를 걸지 못한 것이다.
- **실패 양상:** 피크 400 RPS 목표인데 실제로는 250 RPS만 보냈고, 결과는 "400 RPS 통과"로 기록된다.
- **신호:** 🟢 `preAllocatedVUs`·`maxVUs` 여유(SWA `maxVUs: PEAK * 5`) + `dropped_iterations` 임계 / 🔴 `maxVUs` = 목표 RPS 수준(응답 1초면 바로 부족)
- **필요 수준:** T≥1의 모든 부하 검증.
- **처방:** 공통: `maxVUs ≥ 목표 RPS × 예상 최악 응답 시간(초) × 1.5`, `dropped_iterations: ['count==0']` 임계 추가(또는 목표 대비 1% 미만).
- **검증:** 결과 요약에서 실제 달성 RPS(`iterations` rate)와 목표 RPS 비교를 판정에 포함.
- **비용 영향:** 중립(생성기 메모리 증가).
- **출처:** https://grafana.com/docs/k6/latest/using-k6/metrics/reference/ (`dropped_iterations`: VU 부족 또는 시간 부족으로 시작 못 한 반복, 2026-10-01 확인)

### V-010 부하 생성기 병목 확인
- **무엇/왜:** 생성기가 포화(CPU 80% 초과, 메모리 90% 초과, 네트워크 한도, 파일 디스크립터 고갈)되면 생성기 쪽 대기가 지연으로 측정된다. 생성기 자원을 같이 기록해야 결과가 유효하다.
- **실패 양상:** 측정된 p95 2초의 상당 부분이 생성기 CPU 기아 때문이었다. 특히 생성기와 대상이 같은 머신을 나눠 쓰면 결과를 해석할 수 없다(SWA 로컬: control plane + 20개 Pod + k6가 6 vCPU를 나눔, 원인 분리 실패).
- **신호:** 🟢 별도 VM에서 생성(SWA perf 브랜치 `scripts/gcp-lab.sh`의 lab VM + k6 VM 분리), 생성기 자원 기록 / 🔴 대상 클러스터 안 또는 같은 노트북에서 k6 실행 + 결과를 판정에 사용
- **필요 수준:** T≥1의 모든 부하 검증.
- **처방:** 공통: 생성기를 대상과 다른 머신(같은 리전)에, CPU 20% 이상 여유. 대규모는 분산 실행 또는 관리형 부하 서비스.
- **검증:** 테스트 중 생성기 CPU·메모리·네트워크를 함께 기록하고, CPU 80% 초과 구간이 있으면 그 구간 결과를 무효로 표시. "too many open files" 오류 0건.
- **비용 영향:** 소폭 증가(생성기 VM).
- **출처:** https://grafana.com/docs/k6/latest/testing-guides/running-large-tests/ (CPU 80% 이내, 메모리 90% 이내, 네트워크 포화, 파일 디스크립터, 20% 여유, 2026-10-01 확인)

### V-011 부하 생성 위치와 출발 IP
- **무엇/왜:** 생성기 위치가 지연에 더해진다(리전 밖이면 RTT 수십~수백 ms). 생성기가 IP 하나면 IP 기준 레이트 리밋에 막혀 대상까지 부하가 가지 않는다. 그렇다고 리밋을 풀면 운영 구성과 다른 것을 시험하게 된다.
- **실패 양상:** 해외에서 걸어 p95 목표를 RTT 때문에 실패하거나, 단일 IP 429로 "처리량 한계"를 오판한다(SWA: 로그인 30r/m IP 리밋으로 setup 가입부터 429).
- **신호:** 🟢 생성기 리전 명시, 리밋 완화 오버레이를 별도로 두고 차이를 문서화(SWA `k8s/overlays/local-loadtest`, README의 base vs loadtest 리밋 표) / 🔴 리밋 완화 사실을 결과에 기록하지 않음
- **필요 수준:** T≥1(리밋은 T=L3).
- **처방:** 공통: 같은 리전 다른 네트워크(VPC 밖)에서 생성. 리밋은 (a) 리밋 검증용 실행(운영 값 그대로, 여러 출발 IP), (b) 용량 검증용 실행(테스트 IP 허용 목록) 두 번으로 분리.
- **검증:** 결과 리포트에 생성 위치, 출발 IP 수, 리밋 설정 버전을 함께 기록. 리밋 검증 실행에서 429 비율이 설계 값과 맞는지 확인.
- **비용 영향:** 소폭 증가(생성기 여러 대·NAT IP).
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### V-012 현실적인 요청 혼합과 생각 시간
- **무엇/왜:** 실제 트래픽 비율(예: 읽기 80%, 쓰기 15%, 로그인 5%)과 사용자 행동 순서, 생각 시간을 반영한다. 한 엔드포인트만 두드리면 캐시만 시험하거나 반대로 무거운 경로만 시험한다.
- **실패 양상:** 목록 조회만 부하해서 통과했는데, 실제로는 로그인(argon2) 5%가 CPU를 다 먹어 전체가 느려진다.
- **신호:** 🟢 비율 주석·가중치(SWA `disaster.js` "읽기 80%, 쓰기 15%, 로그인 5%"), `sleep()` 생각 시간 / 🔴 단일 URL 반복, 혼합 근거 없음
- **필요 수준:** T≥1.
- **처방:** 공통: 혼합 비율을 가정(§4.3)의 일부로 리포트에 노출, 운영 관측(O-013 라우트별 요청 수)이 생기면 실측 비율로 교체(O-072).
- **검증:** 테스트 후 서버 지표의 라우트별 요청 비율이 의도한 혼합과 ±5%p 안인지 확인.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### V-013 캐시 적중 분포와 데이터 다양성
- **무엇/왜:** 모든 VU가 같은 게시물·같은 첫 페이지를 읽으면 캐시 적중률이 비현실적으로 100%가 된다. 실제처럼 인기 편중(소수 인기 + 긴 꼬리) 키 분포와 충분한 데이터 양을 쓴다.
- **실패 양상:** 테스트는 캐시만 시험했고, 실제로는 긴 꼬리 요청이 DB로 가서 무너진다. 반대로 완전 무작위면 캐시 효과를 과소평가한다.
- **신호:** 🟢 키 분포 파라미터(편중 분포), 사전 적재 데이터 크기 기록, 서버 캐시 적중률 동시 기록 / 🔴 고정 ID 하나 반복 / 🟡 페이지네이션 첫 페이지 위주
- **필요 수준:** 캐시를 처방한 T≥2.
- **처방:** 공통: 테스트 데이터 N건 사전 적재, 편중 분포로 키 선택, 운영 적중률(O-021)이 생기면 그 값에 맞춰 조정.
- **검증:** 테스트 중 서버 캐시 적중률이 의도한 범위(예: 70~90%)인지 확인. 냉 캐시 시작 구간 결과는 따로 표시(V-017).
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### V-014 테스트 데이터 준비·격리·정리
- **무엇/왜:** 부하·합성 테스트용 계정과 데이터를 실행 ID로 구분해 만들고, 끝나면 지우거나 표시한다. 큰 데이터 파일은 VU마다 복사되지 않게 공유 배열을 쓴다. 가입·로그인 같은 무거운 준비 단계는 리밋·해시 비용을 고려해 나눠 실행한다.
- **실패 양상:** 테스트 계정이 운영 통계·추천·이메일 발송에 섞인다. 같은 이메일로 재실행하다 유니크 제약 오류를 시스템 오류로 센다. 데이터 파일 복사로 생성기 메모리 부족.
- **신호:** 🟢 실행 ID 접두 계정(SWA `lt-${runId}-${i}@example.com`), 준비 배치 크기 제한(SWA `SIGNUP_BATCH = 4`, argon2 동시 처리 한도에 맞춤), `SharedArray`, `setupTimeout` / 🔴 고정 테스트 계정 공유, 정리 단계 없음
- **필요 수준:** T≥1 부하 검증과 O-048 합성 모니터링.
- **처방:** 공통: setup/teardown, 테스트 데이터 표시 컬럼 또는 별도 테넌트, 운영 환경에서는 테스트 이메일 도메인 발송 차단.
- **검증:** 실행 후 테스트 접두 데이터 수가 0(정리됨)이거나 운영 지표에서 제외되는지 확인.
- **비용 영향:** 중립.
- **출처:** https://grafana.com/docs/k6/latest/examples/data-parameterization/ (SharedArray: VU마다 별도 JS VM이라 데이터 복사 방지, 2026-10-01 확인)

### V-015 통과 기준을 코드로(임계치·종료 코드)
- **무엇/왜:** 통과 기준(p95, 오류율, 미발사 요청)을 스크립트의 임계치로 두면 실패 시 0이 아닌 종료 코드가 나와 CI·P4 파이프라인이 자동 판정한다. 기준을 결과를 본 뒤 완화하지 않는다.
- **실패 양상:** 사람이 그래프를 보고 "대충 괜찮다"로 판정, 실행마다 기준이 바뀐다.
- **신호:** 🟢 `thresholds: { read_duration: ['p(95)<300'], server_errors: ['rate<0.01'] }` (SWA, "임계치는 완화하지 않음") / 🔴 임계치 없음, 결과 JSON만 저장
- **필요 수준:** 모든 부하 검증(T≥1).
- **처방:** 공통: 필요 수준의 SLO 목표(O-038)에서 임계치를 생성. 장애 주입 실험은 `abortOnFail`로 안전장치.
- **검증:** 일부러 느린 버전(지연 주입)으로 실행해 종료 코드가 0이 아닌지 확인.
- **비용 영향:** 중립.
- **출처:** https://grafana.com/docs/k6/latest/using-k6/thresholds/ (임계치 실패 시 0이 아닌 종료 코드, `abortOnFail`, 2026-10-01 확인)

### V-016 설계된 거절과 장애를 분리 집계
- **무엇/왜:** 백프레셔 503·리밋 429는 T L3 통제가 동작한 증거다. 서버 오류율에서 빼되 별도 카운트로 남기고, 거절 비율 상한도 기준으로 둔다(거절만 하는 시스템은 통과가 아니다).
- **실패 양상:** 설계된 503 때문에 오류율 기준 실패, 또는 반대로 99%를 거절하고도 "서버 오류 0%"로 통과.
- **신호:** 🟢 SWA `record()`가 `QUEUE_FULL` 503과 `RATE_LIMITED` 429를 분리 / 🔴 `http_req_failed`만으로 판정
- **필요 수준:** T=L3.
- **처방:** 공통: 세 지표(서버 오류율, 거절률, 성공 처리량) 동시 기준. 예: 서버 오류 < 1%, 거절 < 20%(스파이크 구간), 거절 응답에 `Retry-After` 존재.
- **검증:** 큐 한도를 일부러 낮춘 실행에서 거절 카운트가 늘고 서버 오류는 늘지 않는지 확인.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### V-017 웜업·콜드 스타트 구간 분리
- **무엇/왜:** 첫 몇 분(JIT, 커넥션 풀 생성, 냉 캐시, 콜드 스타트)은 평상시와 다르다. 이 구간을 따로 측정해 "확장 직후 사용자 경험"으로 보고, 정상 상태 판정과 섞지 않는다.
- **실패 양상:** 웜업 지연이 섞여 평시 p95가 나쁘게 나오거나, 반대로 콜드 스타트 문제(T L3 최소 인스턴스 필요성, TIER-003)를 평균에 묻는다.
- **신호:** 🟢 단계 태그로 첫 구간 분리, 새 인스턴스 첫 요청 지연 기록 / 🔴 전체 구간 단일 p95
- **필요 수준:** T≥1. 콜드 스타트 분리는 티어0·1(서버리스·scale-to-zero)에서 필수.
- **처방:** 공통: 웜업 단계를 시나리오 앞에 두고 판정에서 제외, 대신 별도 지표로 보고.
- **검증:** 최소 인스턴스 0과 1 이상 두 구성으로 스파이크를 걸어 첫 30초 p95 차이를 리포트(TIER-003 근거 수치).
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### V-018 확장 완료 시간 측정
- **무엇/왜:** 스파이크 시작부터 (a) 확장 결정, (b) 새 인스턴스 Ready, (c) 지연이 기준 안으로 돌아온 시점까지를 잰다. 이 시간이 가정 램프(T L3 1분)보다 길면 그 사이는 큐·최소 인스턴스·여유 용량이 버텨야 한다.
- **실패 양상:** HPA는 "동작"했지만 노드 프로비저닝 3분 동안 요청이 실패했다. HPA 지표 수집 자체가 부하로 끊긴다(SWA 로컬: metrics-server 재시작으로 HPA 지표 `<unknown>`).
- **신호:** 🟢 테스트 중 레플리카 수·Pending Pod 수·노드 수 시계열 수집 / 🔴 확장 여부만 확인
- **필요 수준:** T≥1(L3 필수, §17.2 "확장 완료 시간 기록").
- **처방:** 공통: P4가 HPA/KEDA 이벤트와 Ready 시각을 수집해 세 시점을 계산. 티어2는 노드 프로비저닝 시간 포함(T-CTL-009 판단 근거).
- **검증:** 같은 스파이크 2회의 확장 완료 시간 비교, 램프 가정과의 차이를 리포트.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### V-019 테스트 환경과 운영 구성의 차이 기록
- **무엇/왜:** 테스트 전용 오버레이(리밋 완화, HPA 상한 축소, 프로브 완화, 작은 노드)는 결과를 운영에 그대로 옮길 수 없게 만든다. 차이를 기계가 읽을 수 있게 기록하고, 판정 결과의 유효 범위를 표시한다.
- **실패 양상:** 로컬 축소판 결과로 클라우드 용량을 판정하거나, 리밋을 푼 결과를 "리밋 포함 통과"로 오인한다.
- **신호:** 🟢 오버레이별 차이 표(SWA loadtest README: "로컬 결과는 클라우드 리밋 설정과 비교할 수 없다"), 결과에 오버레이 이름·커밋 기록 / 🔴 어떤 구성으로 돌렸는지 결과에 없음
- **필요 수준:** 모든 부하 검증.
- **처방:** 공통: P4 결과 JSON에 `{commit, overlay, diff_from_prod}` 필드. 운영과 다른 구성의 결과는 "참고"로만 표시하고 통제 상태를 "동작 확인"으로 바꾸지 않는다.
- **검증:** 리포트 생성기가 diff가 있는 결과를 통제 판정에 쓰지 않는지 단위 테스트.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### V-020 부하 중 서버 측 관측 동시 수집
- **무엇/왜:** 클라이언트 지연만으로는 원인을 모른다. 같은 시간 축으로 서버 지표·계층별 로그(O-012)·Server-Timing(O-024)·루프 지연(O-022)을 수집하고, 요청에 단계 태그를 넣어 결합한다. 이 과정이 관측 장치 자체의 검증도 겸한다.
- **실패 양상:** "p95 2초"만 남고 병목이 어디인지 다시 재현해야 한다.
- **신호:** 🟢 요청 헤더 `X-Load-Step`/`X-Load-Op`를 nginx 로그에 기록(SWA perf 브랜치), 부하 후 분석 스크립트로 구간 분해 / 🔴 k6 요약만 저장
- **필요 수준:** T≥2. L1은 플랫폼 기본 지표 캡처로 충분.
- **처방:** 공통: P4가 실행 구간의 지표 스냅샷·로그 쿼리 결과를 결과 묶음에 함께 저장.
- **검증:** 결과 묶음만으로 "어느 단계에서 어느 구간이 가장 느렸나"에 답할 수 있는지 확인.
- **비용 영향:** 소폭 증가(로그량).
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

## B3. 결과 해석

### V-021 조정 누락(coordinated omission)
- **무엇/왜:** 클로즈드 모델이나 "응답 후 다음 요청" 측정은 서버가 멈춘 동안 보냈어야 할 요청을 세지 않는다. 그래서 최악의 순간이 결과에서 빠지고 백분위가 실제보다 좋게 나온다.
- **실패 양상:** 서버가 5초 멈췄는데 그 동안 VU가 대기 중이라 요청 몇 개만 5초로 기록되고 p99는 멀쩡해 보인다.
- **신호:** 🔴 `constant-vus` + 지연 백분위 판정, 자체 루프 스크립트(`while True: requests.get()`) / 🟢 arrival-rate 실행기 + `dropped_iterations` 감시
- **필요 수준:** 지연 기준이 있는 모든 부하 검증(T≥1).
- **처방:** 공통: V-008·V-009 적용. 클로즈드 모델 결과는 지연 판정에 쓰지 않는다.
- **검증:** 서버를 10초 정지(SIGSTOP 또는 네트워크 지연 주입)시키는 대조 실험에서 오픈 모델 결과가 정지를 반영하는지 확인.
- **비용 영향:** 중립.
- **출처:** https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/open-vs-closed/ (클로즈드 모델의 조정 누락 설명, 2026-10-01 확인)

### V-022 백분위 집계 오류
- **무엇/왜:** p95는 평균 낼 수 없다. Pod별·분 단위 p95의 평균, 서비스별 p95의 평균은 의미 없는 숫자다. 원시 히스토그램(버킷)을 합친 뒤 백분위를 계산한다. 또한 여러 경로를 섞은 p95는 무거운 경로를 숨긴다.
- **실패 양상:** 1분 단위 p95들의 평균으로 SLO 통과를 선언했는데, 전체 분포의 p95는 기준을 넘는다.
- **신호:** 🔴 `avg(...{quantile="0.95"})`, 스프레드시트에서 p95 열 평균 / 🟢 `histogram_quantile(0.95, sum(rate(..._bucket[5m])) by (le))`, 경로별(op 태그) p95 분리
- **필요 수준:** 지연 기준이 있는 모든 검증과 SLO.
- **처방:** 공통: P4 결과 계산은 원시 분포 또는 버킷 합산으로만. 경로별 판정(읽기·쓰기 기준이 다름, SWA 임계치처럼).
- **검증:** 같은 원시 데이터로 "p95의 평균"과 "전체 p95"를 계산해 차이를 보여주는 단위 테스트를 계산기에 둔다.
- **비용 영향:** 중립.
- **출처:** https://prometheus.io/docs/practices/histograms/ ("avg(http_request_duration_seconds{quantile="0.95"}) // BAD!", histogram_quantile로 집계, 2026-10-01 확인)

### V-023 클라이언트 지연과 서버 지연의 차이 해석
- **무엇/왜:** k6 `http_req_duration`은 송신+대기+수신이고 DNS·연결 수립은 제외한다. 서버 지표는 앱 처리 시간만이다. 둘의 차이(연결, TLS, 프록시 큐잉, 네트워크)를 따로 보지 않으면 원인을 잘못 짚는다.
- **실패 양상:** 커넥션 재사용이 안 돼 매 요청 TLS 핸드셰이크가 생기는데 `http_req_duration`에는 안 보이고 사용자 체감만 나쁘다.
- **신호:** 🟢 `http_req_connecting`, `http_req_tls_handshaking`, `http_req_waiting` 함께 기록(SWA `steps-summary.json`에 `http_req_connecting` 존재), 서버 `urt`와 비교 / 🔴 `http_req_duration`만
- **필요 수준:** T≥2.
- **처방:** 공통: 결과에 연결·대기·서버 처리 시간 분해 표 포함.
- **검증:** keep-alive를 끈 실행과 켠 실행의 연결 시간 차이가 결과에 드러나는지 확인.
- **비용 영향:** 중립.
- **출처:** https://grafana.com/docs/k6/latest/using-k6/metrics/reference/ (`http_req_duration` = sending + waiting + receiving, DNS·연결 제외, 2026-10-01 확인)

### V-024 반복성과 표본 크기
- **무엇/왜:** 클라우드 성능은 실행마다 흔들린다(이웃 소음, 캐시 상태, 오토스케일 타이밍). 판정은 2~3회 반복의 일관성으로 하고, p99처럼 꼬리 지표는 표본 수가 충분할 때만 쓴다(1,000건 미만에서 p99는 상위 10건 이하로 결정).
- **실패 양상:** 한 번의 운 좋은 실행으로 통과, 또는 한 번의 이상치로 불필요한 증설.
- **신호:** 🟢 결과에 `count` 기록(SWA `summaryTrendStats`에 count 포함), 반복 실행 / 🔴 표본 13건으로 p99 보고(SWA `steps-summary.json`의 `count: 13` 구간처럼 작은 표본은 참고용)
- **필요 수준:** 통제 상태를 "동작 확인"으로 바꾸는 모든 검증.
- **처방:** 공통: 핵심 판정은 2회 이상, 구간별 최소 표본 수(예: p95는 200건, p99는 1,000건 이상) 미달 시 "표본 부족" 표시.
- **검증:** 계산기가 표본 부족 구간을 판정에서 제외하는지 단위 테스트.
- **비용 영향:** 증가(반복 실행 비용).
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### V-025 결과를 용량·비용으로 환산("동시 N명까지, 월 $X")
- **무엇/왜:** 검증 결과를 운영 언어로 바꾼다: 통과한 최대 부하를 동시 사용자 수로(생각 시간 가정 명시), 그때의 자원 사용량을 가격 계층으로 계산해 월 비용으로. 견적(P1)을 실측으로 교체한다.
- **실패 양상:** "p95 280ms 통과"는 바이브코더에게 의미가 없다. 견적과 실제 비용 차이가 운영 후에야 드러난다.
- **신호:** 🟢 결과에 RPS → 동시 사용자 환산식과 자원 사용량 기록 / 🔴 지연 숫자만 보고
- **필요 수준:** T≥1.
- **처방:** 공통: 동시 사용자 = RPS × (평균 응답 시간 + 생각 시간). 비용 = 피크 시 레플리카·노드 수 × 단가(가격 스냅샷) + 평시 구성.
- **검증:** 소크의 자원 기반 비용 환산과 이후 청구 데이터 비교(§17.3), 오차율 기록.
- **비용 영향:** 중립(정확도 향상).
- **출처:** 일반 원칙(설계 문서 §3 P4 출력, §17.3) ⚠️근거없음

### V-026 성능 회귀 기준선
- **무엇/왜:** 이전 통과 결과를 기준선으로 저장하고, 새 버전의 같은 시나리오 결과와 비교해 회귀(예: p95 20% 악화, 요청당 CPU 증가)를 잡는다.
- **실패 양상:** 기능 추가마다 조금씩 느려져 어느 날 SLO를 넘는데, 어느 변경이 원인인지 모른다.
- **신호:** 🟢 결과 JSON 보관(SWA `loadtest/results/`) + 비교 스크립트 / 🔴 결과를 보관하지 않음
- **필요 수준:** U≥2 또는 T≥2(배포 빈도가 높고 성능 기준이 있는 경우).
- **처방:** 공통: 스모크 수준 성능 테스트를 CI에 두고 기준선 대비 임계 비교, 전체 시나리오는 릴리스 전.
- **검증:** 의도적으로 느린 커밋(sleep 추가)에서 회귀가 감지되는지 확인.
- **비용 영향:** 소폭 증가(CI 실행).
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

## B4. 혼돈 실험 설계

### V-027 정상 상태(steady state) 정의
- **무엇/왜:** 실험 전에 "정상"을 측정 가능한 출력으로 정한다(예: 성공 요청률 > 99%, 읽기 p95 < 300ms, 큐 lag < 10초). 내부 지표(CPU)가 아니라 사용자 관점 출력이어야 한다. 정상 상태 지표가 곧 중단 조건(V-030)의 재료다.
- **실패 양상:** 장애를 넣고 "뭔가 바뀌었다"만 관찰해 결론을 낼 수 없다.
- **신호:** 🟢 실험 정의 파일에 정상 상태 지표와 값 / 🔴 장애 주입 스크립트만 있음
- **필요 수준:** D≥1의 모든 장애 주입 검증.
- **처방:** 공통: SLO(O-037) 지표를 그대로 정상 상태로 사용. SLO가 없는 L1은 업타임 + 오류율.
- **검증:** 장애 없이 같은 시간 동안 정상 상태 지표를 재서 기준 변동 폭을 기록(실험 결과 판정의 잡음 기준).
- **비용 영향:** 중립.
- **출처:** https://principlesofchaos.org/ ("defining 'steady state' as some measurable output of a system that indicates normal behavior"), https://docs.aws.amazon.com/fis/latest/userguide/stop-conditions.html (정상 상태를 정의해 중단 조건 알람 생성), 2026-10-01 확인 ⚠️출처부적격

### V-028 가설과 통과 기준
- **무엇/왜:** "DB 페일오버 동안 오류율 < 5%이고 RTO 30분 안에 회복한다"처럼 수준의 가정(§4.3)에서 나온 반증 가능한 가설을 쓴다. 실험은 가설을 반증하려는 시도다.
- **실패 양상:** 실험이 "해봤다"로 끝나고 통제 상태를 바꿀 근거가 없다.
- **신호:** 🟢 실험마다 가설·통과 기준·관련 통제 ID(예: D-CTL-002) / 🔴 없음
- **필요 수준:** D≥1.
- **처방:** 공통: §17.2 표를 실험 템플릿으로: 시나리오·수준 → 주입 → 가설 → 통과 기준 → 통제 ID.
- **검증:** 실험 결과가 가설 통과/반증 중 하나로 기계 판정되는지 확인.
- **비용 영향:** 중립.
- **출처:** https://principlesofchaos.org/ (가설, 실세계 사건을 반영한 변수, 반증 시도), 2026-10-01 확인 ⚠️출처부적격

### V-029 블래스트 반경 제한
- **무엇/왜:** 처음에는 가장 작은 범위(Pod 하나, 트래픽 일부, 스테이징)로 시작해 확신이 쌓이면 넓힌다. 운영에서 실험한다면 피해 최소화는 실험자의 책임이다.
- **실패 양상:** 첫 실험부터 전체 노드를 끊어 실제 장애를 만든다.
- **신호:** 🟢 대상 선택 `mode: one`/`fixed-percent`, FIS 대상 `selectionMode: COUNT(1)`/`PERCENT(n)`, 네임스페이스·레이블 한정 / 🔴 `mode: all` + 운영 네임스페이스 + 중단 조건 없음
- **필요 수준:** 운영 환경에서 실험하는 경우 모든 수준. P4 기본은 검증 전용 환경이므로 L2 이하에서는 운영 실험을 권하지 않는다.
- **처방:** 공통: 단계적 확대(1 Pod → 1 노드 → 1 존). 운영 실험은 D=L3 + 게임데이(V-057)에서만.
- **검증:** 실험 정의 lint: 운영 대상인데 블래스트 반경·중단 조건이 없으면 거부.
- **비용 영향:** 중립.
- **출처:** https://principlesofchaos.org/ (운영 실험 선호와 함께 "the fallout from experiments are minimized and contained"), https://chaos-mesh.org/docs/simulate-time-chaos-on-kubernetes/ (선택 모드 one·all·fixed·fixed-percent·random-max-percent), 2026-10-01 확인 ⚠️출처부적격 ⚠️출처확인필요

### V-030 중단 조건(자동 정지)
- **무엇/왜:** 정상 상태 지표가 허용 범위를 벗어나면 실험을 자동으로 멈춘다. AWS FIS는 CloudWatch 알람을 중단 조건으로 걸 수 있고, 멈춘 실험은 재개할 수 없다. k6는 `abortOnFail`로 부하를 멈춘다.
- **실패 양상:** 실험자가 화면을 보다 늦게 반응해 실제 사용자 영향이 커진다.
- **신호:** 🟢 FIS `stopConditions`에 알람 ARN, Chaos Mesh `duration` 상한 + 수동 중단 절차, k6 `abortOnFail` / 🔴 FIS `"source": "none"` + 운영 대상
- **필요 수준:** 공유 환경·운영에서 실험하면 모든 수준. 격리된 P4 환경에서는 `duration` 상한만으로 충분.
- **처방:** 티어1(AWS): FIS 중단 조건 = 오류율 SLO 알람. 티어2: Chaos Mesh `duration` + 부하 쪽 `abortOnFail` + 정리 스크립트.
- **검증:** 중단 조건 알람을 `set-alarm-state`로 강제해 실험이 실제로 멈추고 주입이 해제되는지 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/fis/latest/userguide/stop-conditions.html (CloudWatch 알람 기반 중단, 재개 불가), https://grafana.com/docs/k6/latest/using-k6/thresholds/ (`abortOnFail`), 2026-10-01 확인

### V-031 대조군 비교
- **무엇/왜:** 장애를 넣은 집단과 넣지 않은 집단(또는 주입 전 구간)을 같은 부하에서 비교해야 차이가 장애 탓인지 안다. 부하 변동·오토스케일 같은 다른 변수를 통제한다.
- **실패 양상:** 장애 주입과 동시에 HPA 확장이 일어나 지연 변화가 어느 쪽 원인인지 모른다.
- **신호:** 🟢 주입 전 정상 구간 + 주입 구간 + 회복 구간을 같은 부하로 / 🔴 부하를 바꾸면서 동시에 주입
- **필요 수준:** D≥2.
- **처방:** 공통: 실험 타임라인 = 정상(5분) → 주입(N분) → 회복(5분), 부하는 일정한 arrival-rate.
- **검증:** 세 구간의 정상 상태 지표를 나란히 리포트.
- **비용 영향:** 중립.
- **출처:** https://principlesofchaos.org/ (대조군과 실험군의 정상 상태 차이로 반증, 2026-10-01 확인) ⚠️출처부적격

## B5. 장애 주입 종류

### V-032 Pod·컨테이너 강제 종료
- **무엇/왜:** 부하 중 Pod를 죽여 레플리카 복구, readiness 기반 트래픽 제외, 진행 중 요청 처리를 본다. D L1 기본 검증이다.
- **실패 양상:** 레플리카 1개라 Pod 종료 = 서비스 중단. 종료된 Pod로 가던 요청이 5xx.
- **신호:** 🟢 Chaos Mesh PodChaos `pod-kill`/`container-kill`, FIS `aws:eks:pod-delete`, `aws:ecs:stop-task` / 🔴 replicas: 1 + D≥1
- **필요 수준:** D≥1 (§17.2 L1).
- **처방:** 티어1: FIS `aws:ecs:stop-task` / Cloud Run은 리비전 재배포로 근사. 티어2: PodChaos `pod-kill`, 대상 1개.
- **검증:** 통과 기준: 자동 복구(새 Pod Ready), 그 동안 오류율이 정상 상태 범위 안 또는 L1 허용치. 재시작·종료 사유 기록(O-027).
- **비용 영향:** 중립.
- **출처:** https://chaos-mesh.org/docs/simulate-pod-chaos-on-kubernetes/ (pod-failure, pod-kill, container-kill), FIS 액션 ID는 https://docs.aws.amazon.com/fis/latest/userguide/fis-actions-reference.html, 2026-10-01 확인 ⚠️출처확인필요

### V-033 노드 drain(유지보수 시뮬레이션)
- **무엇/왜:** 노드 업그레이드·축소 때 일어나는 drain을 부하 중에 재현한다. drain은 PDB를 존중하므로 PDB·preStop·종료 처리를 한꺼번에 검증한다.
- **실패 양상:** PDB가 없어 한 노드의 레플리카가 동시에 축출되거나, PDB가 너무 빡빡해 drain이 영원히 끝나지 않는다(노드 업그레이드 막힘).
- **신호:** 🟢 `kubectl drain --ignore-daemonsets` 시나리오, PDB 존재(SWA `k8s/base/pdb.yaml`) / 🔴 PDB `maxUnavailable: 0` 또는 `minAvailable` = replicas
- **필요 수준:** D≥2, U≥2 (§17.2 D L2).
- **처방:** 티어2: 레플리카가 있는 노드 하나 drain. 티어1: ECS `aws:ecs:drain-container-instances`(EC2 기반) / Fargate는 해당 없음.
- **검증:** 배포 중 5xx 0건 기준(U L2)과 drain 완료 시간 기록. drain이 일정 시간 안에 끝나는지(PDB 과잉 검출).
- **비용 영향:** 중립.
- **출처:** https://kubernetes.io/docs/tasks/administer-cluster/safely-drain-node/ (drain은 PDB를 존중, 동시 drain도 PDB 존중), 2026-10-01 확인

### V-034 노드 종료·존(AZ) 장애
- **무엇/왜:** 노드 그룹 인스턴스 종료 또는 한 존의 네트워크 차단으로 존 하나가 사라진 상황을 만든다. D L2(존 하나가 죽어도 동작)의 핵심 검증이다.
- **실패 양상:** 토폴로지 분산이 설정만 있고 실제로는 Pod가 한 존에 몰려 있다. 남은 존에 여유 용량이 없어 Pending.
- **신호:** 🟢 FIS `aws:eks:terminate-nodegroup-instances`, `aws:network:disrupt-connectivity`(서브넷 대상), ARC 존 이동 `aws:arc:start-zonal-autoshift` / 🔴 D≥2인데 존 장애 시험 없음
- **필요 수준:** D≥2(존 하나 격리는 §17.2 D L3 항목이지만 노드 종료는 L2).
- **처방:** 티어1/2(AWS): FIS 서브넷 연결 차단으로 한 존 격리. GCP: Fault Injection Testing이 Pre-GA라 기본 수단으로 쓰지 않음(설계 §16) → 노드 풀 축소·방화벽 규칙으로 근사.
- **검증:** 존 격리 동안 오류율 < 5%, 남은 존에서 Pending Pod 해소 시간, 격리 해제 후 재분산 확인.
- **비용 영향:** 중립(실험 시간만큼 FIS 과금).
- **출처:** https://docs.aws.amazon.com/fis/latest/userguide/fis-actions-reference.html (액션 ID 목록에서 확인), 2026-10-01 확인

### V-035 DB 페일오버·재부팅
- **무엇/왜:** 관리형 DB의 강제 페일오버로 Multi-AZ가 실제로 넘어가는지, 앱이 끊긴 커넥션을 재연결하는지, DNS 캐시로 옛 주 DB를 붙잡지 않는지 본다.
- **실패 양상:** 페일오버는 1분 만에 끝났는데 앱 커넥션 풀이 죽은 연결을 계속 써서 10분간 오류. 
- **신호:** 🟢 FIS `aws:rds:failover-db-cluster`, `aws:rds:reboot-db-instances`(페일오버 옵션), Cloud SQL 수동 페일오버 / 🔴 D≥2 + Multi-AZ 설정만 있고 시험 없음
- **필요 수준:** D≥2 (§17.2).
- **처방:** 티어1/2: 부하 중 강제 페일오버 1회. 풀 설정(pre-ping, 최대 수명)과 함께 검증.
- **검증:** 통과 기준: 페일오버 동안 오류율 < 5%, RTO 가정 이내, 끝난 뒤 쓰기 손실 0(C L3이면 커밋된 쓰기 대조, V-050).
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/fis/latest/userguide/fis-actions-reference.html (`aws:rds:failover-db-cluster`, `aws:rds:reboot-db-instances` 확인), 2026-10-01 확인. Cloud SQL 수동 페일오버 절차는 이번에 직접 확인하지 못함.

### V-036 네트워크 지연·패킷 손실
- **무엇/왜:** 의존성으로 가는 경로에 지연·지터·손실을 넣어 타임아웃·재시도·서킷 브레이커가 동작하는지 본다. 완전 단절보다 "느린 의존성"이 더 흔하고 더 위험하다.
- **실패 양상:** 타임아웃이 없어(`ext.no_timeout`) 느린 의존성 하나에 워커·커넥션이 모두 묶인다. 재시도가 지연을 몇 배로 키운다.
- **신호:** 🟢 Chaos Mesh NetworkChaos `delay`/`loss`/`netem`, FIS `aws:eks:pod-network-latency`, `aws:ecs:task-network-latency`, `aws:eks:pod-network-packet-loss` / 🔴 D≥3인데 지연 주입 없음
- **필요 수준:** D=L3(D-CTL-005 디그레이드 경로). D L2에서는 DB 경로 지연만 선택.
- **처방:** 티어2: NetworkChaos `delay` 500ms~2s를 의존성 방향으로만. 티어1(ECS): FIS 태스크 네트워크 액션.
- **검증:** 지연이 타임아웃보다 클 때 디그레이드 응답(stale 캐시 등)이 나오고 전체 지연이 타임아웃 근처에서 상한이 걸리는지 확인.
- **비용 영향:** 중립.
- **출처:** https://chaos-mesh.org/docs/simulate-network-chaos-on-kubernetes/ (delay, loss, duplicate, corrupt, partition, bandwidth), https://docs.aws.amazon.com/fis/latest/userguide/fis-actions-reference.html, 2026-10-01 확인 ⚠️출처확인필요

### V-037 의존성 블랙홀·네트워크 분할
- **무엇/왜:** 의존성(DB, Redis, 외부 API)으로 가는 패킷을 응답 없이 버린다. 거절(RST)보다 블랙홀이 더 나쁘다 — 연결이 타임아웃까지 매달린다. D L3의 "Redis·DB 차단" 검증이다.
- **실패 양상:** Redis 차단에 앱 전체가 멈춘다(세션·캐시·큐가 모두 Redis). readiness가 모든 Pod를 동시에 빼서 전면 503.
- **신호:** 🟢 NetworkChaos `partition`, FIS `aws:eks:pod-network-blackhole-port`, `aws:ecs:task-network-blackhole-port` / 🔴 D=L3 + 시험 없음
- **필요 수준:** D=L3 (§17.2: Redis·DB 차단).
- **처방:** 티어2: 의존성 Pod/서비스 방향 partition. 티어1: FIS 블랙홀 포트(Redis 6379, Postgres 5432).
- **검증:** Redis 차단 중 읽기 유지·쓰기 거절 동작(SWA readyz 설계: "Redis만 살아 있으면 글쓰기를, DB만 살아 있으면 읽기를"), 해제 후 자동 회복, 재시작 증가 0.
- **비용 영향:** 중립.
- **출처:** https://chaos-mesh.org/docs/simulate-network-chaos-on-kubernetes/ (partition), https://docs.aws.amazon.com/fis/latest/userguide/fis-actions-reference.html (`aws:eks:pod-network-blackhole-port`), 2026-10-01 확인 ⚠️출처확인필요

### V-038 DNS 실패
- **무엇/왜:** 이름 해석 실패·잘못된 IP를 주입해 DNS 캐시, 재시도, 오류 처리를 본다. 관리형 DB 페일오버는 DNS 갱신에 의존하므로 DNS 동작이 페일오버 시간을 좌우한다.
- **실패 양상:** DNS 오류가 앱 기동 실패로 이어져 CrashLoop. 혹은 JVM 등 무한 DNS 캐시로 페일오버 후에도 옛 IP 사용.
- **신호:** 🟢 Chaos Mesh DNSChaos `error`/`random` / 🔴 D=L3 + 외부 의존성 다수 + 시험 없음
- **필요 수준:** D=L3. D L2에서는 페일오버(V-035)로 간접 확인.
- **처방:** 티어2: DNSChaos(Chaos DNS Server 필요, A/AAAA만). 티어1: 해당 도구 없음 → 의존성 호스트명을 잘못된 값으로 바꾼 리비전으로 근사.
- **검증:** DNS 오류 중 기존 연결은 유지되고 새 연결 실패가 오류로 처리되는지, 해제 후 회복 시간.
- **비용 영향:** 중립.
- **출처:** https://chaos-mesh.org/docs/simulate-dns-chaos-on-kubernetes/ (error·random, Chaos DNS Server 필요, A·AAAA만), 2026-10-01 확인 ⚠️출처확인필요

### V-039 HTTP 수준 오류·지연 주입(외부 API 장애)
- **무엇/왜:** 외부 API(결제, 메일, LLM)가 5xx·지연·잘못된 응답을 줄 때 재시도·멱등성 키·디그레이드가 동작하는지 본다. 운영 외부 API에 직접 장애를 낼 수 없으므로 프록시·모의 서버로 주입한다.
- **실패 양상:** 결제사 타임아웃 후 재시도가 멱등성 키 없이 이중 청구를 만든다(C-CTL-007). LLM API 지연이 요청 스레드를 묶는다.
- **신호:** 🟢 Chaos Mesh HTTPChaos `abort`/`delay`/`replace`/`patch`, 모의 서버(WireMock류)로 외부 의존성 대체, FIS `aws:lambda:invocation-error` / 🔴 외부 결제 + 실패 시나리오 시험 없음
- **필요 수준:** C=L3(결제) 또는 D=L3(외부 의존성 디그레이드).
- **처방:** 티어2: HTTPChaos(HTTPS 미지원, 기존 TCP 연결에는 효과 없음 — 사이드카 모의 서버가 더 확실). 공통: 외부 API 기본 URL을 환경변수로 두어 모의 서버로 바꿀 수 있게.
- **검증:** 모의 결제 API가 첫 요청에 타임아웃 후 성공하도록 설정 → 청구 1건만 기록되는지(V-050 불변식).
- **비용 영향:** 중립.
- **출처:** https://chaos-mesh.org/docs/simulate-http-chaos-on-kubernetes/ (네 가지 동작, HTTPS 미지원, 기존 연결 영향 없음, POST 비멱등 주의), 2026-10-01 확인 ⚠️출처확인필요

### V-040 CPU·메모리 압박
- **무엇/왜:** 컨테이너에 CPU·메모리 부하를 걸어 스로틀링·OOMKilled·HPA 반응·이웃 영향을 본다. 메모리 limit이 실제 사용량에 맞는지(right-sizing)도 확인한다.
- **실패 양상:** 메모리 압박에 OOMKilled가 연쇄적으로 나고, liveness가 CPU 기아로 실패해 재시작 폭주.
- **신호:** 🟢 Chaos Mesh StressChaos(CPU workers×load, 메모리 크기), FIS `aws:eks:pod-cpu-stress`, `aws:eks:pod-memory-stress`, `aws:ecs:task-cpu-stress` / 🔴 limits 없음 + 압박 시험 없음
- **필요 수준:** T≥2 또는 D≥2.
- **처방:** 티어2: StressChaos 단일 Pod. 티어1(ECS): FIS 태스크 CPU 스트레스.
- **검증:** CPU 압박 중 liveness 실패 재시작 0건, 메모리 압박 시 OOM 종료 사유 기록과 자동 복구.
- **비용 영향:** 중립.
- **출처:** https://chaos-mesh.org/docs/simulate-heavy-stress-on-kubernetes/ (CPU·메모리 스트레스), https://docs.aws.amazon.com/fis/latest/userguide/fis-actions-reference.html, 2026-10-01 확인 ⚠️출처확인필요

### V-041 디스크 가득·I/O 오류
- **무엇/왜:** 파일 쓰기에 ENOSPC(28)·I/O 오류(5)·지연을 주입한다. 로그 파일, 임시 업로드, SQLite, 로컬 캐시를 쓰는 앱이 디스크 문제에 어떻게 반응하는지 본다.
- **실패 양상:** 디스크가 차자 앱이 조용히 쓰기를 버리거나(데이터 유실), 로그 쓰기 실패로 요청 처리 자체가 멈춘다.
- **신호:** 🟢 Chaos Mesh IOChaos `fault`(errno 28), `latency`; FIS `aws:ebs:pause-volume-io`, `aws:ebs:volume-io-latency` / 🔴 `state.upload.local_fs`·`db.sqlite_file`·`ops.file_logging` 사실 + 시험 없음
- **필요 수준:** 로컬 디스크에 쓰는 경로가 있고 D≥1일 때. 상태 없는 앱(T-CTL-001 충족)은 해당 없음.
- **처방:** 티어2: IOChaos(데이터 손상 위험 — 검증 환경 전용). 공통: 근본 처방은 D-PRE-001/002(오브젝트 스토리지·관리형 DB).
- **검증:** ENOSPC 주입 중 쓰기 요청이 명확한 오류(5xx + 로그)로 실패하고 성공으로 위장되지 않는지 확인.
- **비용 영향:** 중립.
- **출처:** https://chaos-mesh.org/docs/simulate-io-chaos-on-kubernetes/ (latency, fault errno 예 5·28, 운영 사용 주의), https://docs.aws.amazon.com/fis/latest/userguide/fis-actions-reference.html, 2026-10-01 확인 ⚠️출처확인필요

### V-042 시계 왜곡
- **무엇/왜:** 프로세스 시계를 앞뒤로 옮겨 토큰 만료, 세션 TTL, 예약 오픈 시각, 분산 락 만료, 멱등성 키 보존 기간 계산이 버티는지 본다.
- **실패 양상:** 노드 시계가 몇 분 틀어져 JWT가 "아직 유효하지 않음"으로 거절되거나, 예약 오픈 전 주문이 열린다.
- **신호:** 🟢 Chaos Mesh TimeChaos(PID 1과 자식 프로세스만 영향) / 🔴 T≥2 예약·오픈 시각 신호 또는 `cron.no_lock`·분산 락 + 시험 없음
- **필요 수준:** T=L2(예고 시각 기반) 또는 C≥2(만료 기반 멱등성·락)에서 선택. 그 외에는 과잉.
- **처방:** 티어2: TimeChaos ±5분. 공통 처방: 시각 비교는 DB 서버 시각이나 단조 시계로.
- **검증:** 시계를 5분 뒤로 옮긴 Pod에서 오픈 전 주문이 거절되는지, 만료 계산 오류가 없는지 확인.
- **비용 영향:** 중립.
- **출처:** https://chaos-mesh.org/docs/simulate-time-chaos-on-kubernetes/ (시간 오프셋 주입, PID 1 범위 제한), 2026-10-01 확인 ⚠️출처확인필요

### V-043 캐시·세션 저장소 장애
- **무엇/왜:** 관리형 Redis의 노드·존 장애나 재시작을 주입한다. 캐시는 "없어도 느릴 뿐"이어야 하는데, 세션·큐·락까지 같은 Redis에 있으면 단일 장애점이 된다.
- **실패 양상:** 캐시 장애에 모든 요청이 DB로 몰려(캐시 스탬피드) DB까지 무너진다.
- **신호:** 🟢 FIS `aws:elasticache:replicationgroup-interrupt-az-power`, Redis Pod kill / 🔴 T≥2 캐시 + D≥2 + 시험 없음
- **필요 수준:** 캐시를 처방한 T≥2이면서 D≥2.
- **처방:** 티어1/2(AWS): FIS ElastiCache 존 전원 차단. 티어2 자체 Redis: PodChaos. 공통: V-037(블랙홀)과 함께 "느린 Redis"와 "없는 Redis" 둘 다.
- **검증:** 장애 중 DB 커넥션·CPU가 한도 안인지(O-018), 캐시 적중률 0 구간의 p95, 복구 후 캐시 재적재 시간.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/fis/latest/userguide/fis-actions-reference.html (`aws:elasticache:replicationgroup-interrupt-az-power` 확인), 2026-10-01 확인

### V-044 Spot 중단
- **무엇/왜:** Spot·선점형 노드에 워커를 두면(COST-004) 중단 통보(EC2 2분, GKE Spot 기본 30초) 후 회수된다. 중단 통보를 실제로 보내 작업 재처리·종료 처리를 검증한다.
- **실패 양상:** Spot 회수 때 처리 중이던 큐 메시지가 사라지거나 중복 처리된다.
- **신호:** 🟢 FIS `aws:ec2:send-spot-instance-interruptions` / 🔴 Spot·Fargate Spot 사용 + 중단 시험 없음
- **필요 수준:** Spot을 쓰는 구성(COST-004 처방)이면 수준과 무관하게 필수 — 절감 처방의 전제 검증.
- **처방:** 티어2(EKS): FIS Spot 중단. Fargate Spot은 태스크 중지(`aws:ecs:stop-task`)로 근사.
- **검증:** 중단 중 처리 중인 메시지 손실 0, 중복 처리는 멱등 소비(C-CTL-004)로 결과 1회.
- **비용 영향:** 중립(Spot 절감의 안전 검증).
- **출처:** https://docs.aws.amazon.com/fis/latest/userguide/fis-actions-reference.html (`aws:ec2:send-spot-instance-interruptions` 확인), 2026-10-01 확인. 통보 시간 수치는 설계 문서 S22(이번 작업에서 재확인 안 함).

### V-045 클라우드 API 오류·용량 부족
- **무엇/왜:** 확장 시점에 인스턴스 용량 부족(ICE)·API 스로틀링이 나면 오토스케일이 실패한다. 이 실패에서 시스템이 어떻게 버티는지(다른 인스턴스 타입, 큐 백프레셔) 본다.
- **실패 양상:** 이벤트 날 특정 인스턴스 타입 용량 부족으로 노드가 안 늘어 Pending Pod가 쌓인다.
- **신호:** 🟢 FIS `aws:ec2:api-insufficient-instance-capacity-error`, `aws:ec2:asg-insufficient-instance-capacity-error`, `aws:fis:inject-api-throttle-error` / 🔴 T=L3 + 단일 인스턴스 타입 노드 그룹
- **필요 수준:** T=L3이고 티어2(노드 확장에 의존).
- **처방:** 티어2(AWS): 스파이크 중 ICE 주입. 처방 후보: 노드 그룹 인스턴스 타입 다양화, 여유 용량(T-CTL-009).
- **검증:** ICE 주입 동안 스파이크 통과 기준 유지 여부와 Pending 지속 시간.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/fis/latest/userguide/fis-actions-reference.html (해당 액션 ID 확인), 2026-10-01 확인

## B6. 배포·정합성·기능 검증

### V-046 부하 중 배포
- **무엇/왜:** 평시 부하를 걸어 둔 채 롤링 배포를 실행하고 5xx를 센다. readiness·SIGTERM·preStop·LB 드레이닝(U-CTL-001/002/006)을 한 번에 검증하는 가장 싼 방법이다. 부하 없이 배포하면 끊기는 요청이 없어 아무것도 증명하지 못한다.
- **실패 양상:** "배포 성공"인데 배포마다 수십 건 502. LB가 종료 중인 Pod로 계속 보낸다.
- **신호:** 🟢 CI·P4에 "부하 + `kubectl rollout restart`" 단계 / 🔴 U≥1인데 배포 중 오류 측정 없음
- **필요 수준:** U≥1 (§17.2: L1 롤링, L2 5xx 0건).
- **처방:** 공통: 일정 arrival-rate 부하 → 롤아웃(같은 이미지 재시작 + 새 이미지 둘 다) → 5xx·지연 집계. 종료 로그(O-055)로 순서 확인.
- **검증:** 통과 기준: U L1 오류율 < 0.1%, U L2 5xx 0건. 실패 시 종료 로그로 원인 구간(드레인 전 종료 등)을 표시.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(설계 문서 §17.2). 종료 흐름은 https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/ (2026-10-01 확인). ⚠️근거없음

### V-047 실패 버전 자동 롤백 검증
- **무엇/왜:** 일부러 깨진 버전(기동 실패, readiness 실패, 오류율 급증)을 배포해 자동 롤백이 실제로 일어나는지, 걸린 시간과 그동안의 사용자 영향을 잰다.
- **실패 양상:** 서킷 브레이커·롤백 설정은 있는데 조건이 맞지 않아(예: 기동은 되지만 오류만 내는 버전) 롤백되지 않는다.
- **신호:** 🟢 ECS `deployment_circuit_breaker { enable = true, rollback = true }`, Argo Rollouts 분석, `progressDeadlineSeconds` + 롤백 자동화 / 🔴 U≥2 + 실패 버전 시험 없음
- **필요 수준:** U≥2 (U-CTL-007).
- **처방:** 공통: 실패 버전 3종(기동 실패, readiness 실패, 기동 후 50% 500)으로 각각 시험. 세 번째는 지표 기반 판정(카나리, V-049)이 없으면 롤백되지 않는 것이 정상 결과 — 리포트에 한계로 표시.
- **검증:** 롤백 후 모든 인스턴스 버전이 이전 SHA(O-056), 롤백까지 시간, 그동안 오류율.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인). ECS 서킷 브레이커는 설계 문서 S4(이번 작업에서 재확인 안 함). ⚠️근거없음

### V-048 마이그레이션 호환성 검증(구버전 앱 + 새 스키마)
- **무엇/왜:** 롤링 배포 중에는 구버전과 신버전 앱이 같은 DB를 동시에 쓴다. expand 마이그레이션을 적용한 DB에 구버전 앱의 테스트를 돌려 통과하는지 본다.
- **실패 양상:** 컬럼 이름 변경 마이그레이션 직후 아직 남은 구버전 Pod가 모두 500.
- **신호:** 🟢 CI에서 "새 마이그레이션 적용 → 이전 커밋 앱 테스트" 단계, `db.migration.destructive` 사실 없음 / 🔴 `DROP`/`RENAME`/`NOT NULL` 추가 + 같은 릴리스에 코드 변경
- **필요 수준:** U≥2 (U-CTL-003).
- **처방:** 공통: P4가 마이그레이션 Job 실행 후 이전 이미지로 스모크(V-001) 실행.
- **검증:** 이전 이미지 스모크 통과 + 부하 중 배포(V-046)에서 5xx 0건.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인). expand/contract는 설계 문서 S9(이번 작업에서 재확인 안 함). ⚠️근거없음

### V-049 카나리 분석(카나리 vs 대조군)
- **무엇/왜:** 새 버전에 소량 트래픽을 보내고 같은 시간대의 기존 버전과 지표를 비교해 진행·중단을 자동 판정한다. 전체 집계에서는 소량 카나리의 오류가 묻히므로 버전별로 나눠 본다. 지표는 사용자 영향과 직결되고 변경에 귀속되는 것만 고른다(CPU 같은 잡음 지표 제외).
- **실패 양상:** 카나리 5%가 오류 30%를 내도 전체 오류율은 1.5%라 임계 미만으로 통과.
- **신호:** 🟢 Argo Rollouts `AnalysisTemplate`, Flagger, Cloud Deploy 카나리 + 버전 라벨 지표 / 🔴 U=L3인데 카나리 판정이 시간 경과만(pause)
- **필요 수준:** U=L3 (U-CTL-008).
- **처방:** 티어1: Cloud Run 트래픽 분할 + 버전별 지표 비교 스크립트 / ECS 블루그린(CodeDeploy) + 알람. 티어2: Argo Rollouts·Flagger.
- **검증:** 일부러 오류 20%를 내는 버전을 카나리로 배포해 자동 중단되는지, 정상 버전은 끝까지 진행되는지 둘 다 확인.
- **비용 영향:** 소폭 증가(카나리 동안 추가 인스턴스).
- **출처:** https://sre.google/workbook/canarying-releases/ (버전별 분해, 지표 선택 기준, CPU 같은 잡음 지표 제외), 2026-10-01 확인

### V-050 정합성 불변식 검사
- **무엇/왜:** 테스트·장애 후 데이터가 지켜야 할 식을 SQL로 검사한다. 예: 재고 ≥ 0, 판매 수량 합 ≤ 초기 재고, 결제 금액 합 = 주문 금액 합, 같은 멱등성 키의 처리 결과 1건, 큐에 넣은 작업 수 = 처리 수 + DLQ 수.
- **실패 양상:** 부하 테스트는 "오류 0%"로 통과했는데 데이터는 초과 판매·이중 기록 상태다. 응답 코드만 보는 검증은 정합성을 증명하지 못한다.
- **신호:** 🟢 `tests/invariants/*.sql`, 테스트 후 검사 단계 / 🔴 C≥2 + 불변식 검사 없음
- **필요 수준:** C≥2 (C L3는 필수, §17.2).
- **처방:** 공통: 스키마에서 불변식 후보 자동 생성(재고·잔액 컬럼, 유니크 키) + 사람이 확정. 모든 C 검증과 D 페일오버 검증 뒤에 실행.
- **검증:** 일부러 잠금을 제거한 버전에서 동시 주문 테스트(V-052)를 돌려 불변식 검사가 위반을 잡는지(음성 대조) 확인.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(설계 문서 §17.2) ⚠️근거없음

### V-051 웹훅 중복·순서 뒤집기 재전송
- **무엇/왜:** 같은 이벤트를 여러 번, 순서를 바꿔, 지연시켜 보낸다. 웹훅 제공자는 중복·순서 보장 없음을 명시하므로 이 상황은 일상이다.
- **실패 양상:** 결제 완료 웹훅 두 번에 포인트 이중 적립, `refunded`가 `paid`보다 먼저 와서 상태가 `paid`로 덮인다.
- **신호:** 🟢 웹훅 수신 테스트에 중복·역순 케이스, 공급자 CLI 재전송(Stripe CLI `events resend` 류) / 🔴 `webhook.no_dedupe` 사실
- **필요 수준:** 웹훅 수신이 있으면 C≥2 (C-CTL-002).
- **처방:** 공통: 서명된 테스트 이벤트를 같은 ID로 3회, 역순으로 1회 전송하는 하네스.
- **검증:** 통과 기준: 중복 처리 0건(V-050 불변식), 최종 상태가 이벤트 시각 기준으로 올바름.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(설계 문서 §17.2). 웹훅 중복·순서 근거는 설계 문서 S12(이번 작업에서 재확인 안 함). ⚠️근거없음

### V-052 동시성 경합 테스트(마지막 재고에 동시 요청)
- **무엇/왜:** 마지막 재고 1개에 동시 주문 100건, 같은 계좌에 동시 출금처럼 경합을 의도적으로 만든다. 순차 테스트로는 경쟁 조건이 드러나지 않는다.
- **실패 양상:** 단위 테스트는 통과했는데 실제 선착순 이벤트에서 초과 판매.
- **신호:** 🟢 k6 `shared-iterations`/동시 배치 요청으로 같은 리소스 경합, 결과 불변식 검사 / 🔴 `concurrency.decrement_no_lock` 사실 + 경합 테스트 없음
- **필요 수준:** C=L3 (C-CTL-005).
- **처방:** 공통: 동시 요청 N건을 한 시점에 발사(배치), 여러 Pod에 분산되도록(단일 Pod 내 직렬화로 통과하는 착시 방지).
- **검증:** 통과 기준: 성공 1건, 나머지는 명확한 실패 응답(409 등), 초과 판매 0(V-050). 레플리카 2개 이상에서 실행.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(설계 문서 §17.2) ⚠️근거없음

### V-053 계약 테스트
- **무엇/왜:** 서비스 간(프론트엔드↔API, API↔API) 요청·응답 형식을 소비자 테스트에서 계약으로 만들고 제공자가 검증한다. 독립 배포 시 호환성 깨짐을 배포 전에 잡는다.
- **실패 양상:** API 필드 이름 변경이 배포된 뒤 프론트엔드·다른 서비스가 깨진다. 롤링 배포 중 구·신 버전 간 호출 실패.
- **신호:** 🟢 `pact` 의존성, OpenAPI 스키마 기반 계약 검사 / 🟡 서비스 여러 개 + E2E만 / 🔴(과잉) 단일 서비스 + 계약 테스트 도구
- **필요 수준:** U≥2이고 독립 배포 단위가 2개 이상일 때. 단일 배포 단위에는 과잉.
- **처방:** 공통: OpenAPI 스키마 하위 호환 검사(가벼움)부터, 서비스가 많아지면 소비자 주도 계약.
- **검증:** 필드를 삭제한 제공자 변경이 CI에서 실패하는지 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.pact.io/ (소비자 주도 계약 테스트, 계약은 소비자 테스트 실행 중 생성, 2026-10-01 확인) ⚠️출처확인필요

### V-054 섀도 트래픽(운영 트래픽 미러링)
- **무엇/왜:** 운영 요청을 복제해 새 버전에도 보내고 응답은 버린다. 실제 트래픽 분포로 새 버전의 오류·지연을 사용자 영향 없이 본다.
- **실패 양상:** 도입하지 않으면 합성 부하로는 재현되지 않는 실제 요청 패턴의 문제를 놓친다. 잘못 도입하면 미러된 쓰기 요청이 DB·결제를 두 번 실행한다.
- **신호:** 🟢 Istio `mirror`/`mirrorPercentage`, nginx `mirror` 지시어 + 읽기 경로 한정 / 🔴 쓰기 경로 미러링 + 외부 부작용(결제·메일) 차단 없음
- **필요 수준:** U=L3이고 티어2(서비스 메시·인그레스 지원)에서 선택. 그 외에는 과잉.
- **처방:** 티어2: 읽기 전용(GET) 경로만 미러링, 섀도 버전은 별도 DB 복제본 또는 쓰기 비활성.
- **검증:** 섀도 버전의 오류율·지연을 운영 버전과 비교, 섀도 쪽에서 외부 부작용 호출 0건 확인.
- **비용 영향:** 증가(섀도 인스턴스).
- **출처:** https://istio.io/latest/docs/tasks/traffic-management/mirroring/ ("fire and forget", 응답은 버려짐, 2026-10-01 확인) ⚠️출처확인필요

### V-055 브라우저 E2E 스모크(프론트엔드 포함)
- **무엇/왜:** 배포된 URL에서 실제 브라우저로 핵심 흐름(가입·로그인·쓰기·읽기)을 실행한다. API 스모크로는 CORS·쿠키 속성·정적 자산 경로·CSP 문제를 못 잡는다.
- **실패 양상:** API는 정상인데 `SameSite` 쿠키 설정 때문에 운영 도메인에서만 로그인이 유지되지 않는다.
- **신호:** 🟢 Playwright `e2e/smoke.spec.ts` + `BASE_URL` 주입(SWA `frontend/playwright.config.ts`) / 🔴 프론트엔드 있음 + 브라우저 테스트 없음
- **필요 수준:** 프론트엔드가 있으면 모든 수준(L1부터). 같은 스크립트를 L3 합성 모니터(O-048)로 재사용.
- **처방:** 공통: P4 스모크 단계에서 배포 URL 대상으로 실행.
- **검증:** 쿠키 `Secure` 속성을 일부러 깨뜨린 배포에서 실패하는지 확인.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

## B7. 복구·운영 절차 검증

### V-056 복원 리허설
- **무엇/왜:** 백업에서 새 인스턴스로 실제 복원하고, 걸린 시간(RTO)과 복원된 데이터 시점(RPO)을 잰다. 백업은 복원해 보기 전까지 백업이 아니다.
- **실패 양상:** 복원에 필요한 KMS 권한·서브넷 그룹·파라미터 그룹이 없어 장애 당일 복원이 몇 시간 지연된다. 복원은 됐는데 앱 연결 문자열 전환 절차가 없다.
- **신호:** 🟢 AWS Backup 복원 테스트 계획, 복원 스크립트 + 기록 / 🔴 D≥1 + 복원 기록 없음 (SWA는 D-CTL-006 미충족으로 명시)
- **필요 수준:** D≥1 (§17.2: 복원 리허설 L1 이상).
- **처방:** 티어0: 플랫폼 백업에서 별도 프로젝트로 복원. 티어1/2: AWS Backup 복원 테스트(주기 자동, 검증 후 자동 삭제) / Cloud SQL 백업·PITR을 새 인스턴스로 복원하는 Job.
- **검증:** 통과 기준: 복원 성공, 시간 ≤ RTO 가정, 데이터 손실 ≤ RPO 가정(마지막 쓰기 시각과 복원 데이터 최신 시각 비교), 복원 DB로 앱 스모크 통과.
- **비용 영향:** 증가(복원 인스턴스 시간 + 테스트당 과금).
- **출처:** https://docs.aws.amazon.com/aws-backup/latest/devguide/restore-testing.html (주기적 복원 테스트, 복원 시간 측정, 검증 창, 테스트당 비용, KMS·IAM 실패 원인), 2026-10-01 확인

### V-057 게임데이
- **무엇/왜:** 실제 대응 팀이 미리 공지된 시나리오(장애 주입)에 런북·대시보드·알림만으로 대응해 본다. 시스템뿐 아니라 사람·절차·소통을 검증한다. 결과는 회고로 개선 항목이 된다.
- **실패 양상:** 기술 복구는 자동으로 됐는데 아무도 알림을 못 봤다, 런북 명령이 옛날 것이다, 고객 공지를 누가 할지 몰랐다.
- **신호:** 🟢 게임데이 계획·회고 문서, 정기 일정 / 🔴 D=L3 + 없음 / 🟡 장애 주입은 하지만 사람 대응은 측정 안 함
- **필요 수준:** D=L3에서 필수(D-CTL-006). D L2는 연 1회 권장. L1 이하에는 과잉.
- **처방:** 공통: P4 장애 주입 시나리오 중 하나를 사람 대응과 결합. 측정: 감지 시간(알림 도착), 선언 시간, 완화 시간, 상태 페이지 게시 시간.
- **검증:** 회고에서 나온 개선 항목이 추적되고, 다음 게임데이에서 같은 항목이 다시 나오지 않는지.
- **비용 영향:** 증가(사람 시간 + 실험 자원).
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_testing_resiliency_game_days_resiliency.html (REL12-BP05: 정기 게임데이, 안티패턴, 회고 반영), 2026-10-01 확인

### V-058 알림 발화 검증
- **무엇/왜:** 각 알림이 조건이 되면 실제로 울리고 사람에게 도착하는지 확인한다. 장애 주입 실험마다 "어떤 알림이 몇 분 만에 왔나"를 함께 기록하면 별도 비용 없이 검증된다.
- **실패 양상:** 장애 주입은 통과했지만 알림은 하나도 오지 않았다 — 실제 장애에서는 아무도 모른다.
- **신호:** 🟢 실험 결과에 알림 도착 시각 기록, CloudWatch `SetAlarmState` 시험 / 🔴 알림 정의만 있음
- **필요 수준:** 알림이 있는 모든 수준(L1부터).
- **처방:** 공통: P4가 각 장애 주입에 기대 알림 목록을 붙이고 도착을 확인. 알림만 따로 시험할 때는 `set-alarm-state`(다음 평가 때까지만 유지).
- **검증:** 기대 알림 도착률 100%, 장애 시작~도착 시간이 SLO 소진율 설계(O-039)와 맞는지.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html (`SetAlarmState`로 시험, 다음 평가까지 유지), https://sre.google/workbook/monitoring/ (알림 설정 테스트), 2026-10-01 확인

### V-059 런북 실행 리허설
- **무엇/왜:** 런북을 쓴 사람이 아닌 사람이 런북만 보고 절차를 끝까지 실행한다. 명령이 현재 인프라에서 동작하는지, 권한이 있는지, 걸리는 시간이 RTO 안인지 확인한다.
- **실패 양상:** 런북의 리소스 이름·명령이 IaC 변경 후 바뀌어 장애 중 첫 단계부터 막힌다.
- **신호:** 🟢 런북에 마지막 실행 날짜·실행자 기록 / 🔴 런북 수정일이 IaC 큰 변경보다 오래됨
- **필요 수준:** 최대 필요 수준 L2 이상(런북이 있는 수준).
- **처방:** 공통: 게임데이(V-057) 또는 복원 리허설(V-056)과 함께 실행, 명령 블록은 가능하면 스크립트로.
- **검증:** 실행 시간 기록, 막힌 단계 수 0.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_testing_resiliency_game_days_resiliency.html (런북 적용 범위 확인, 절차 문서를 실행하지 않는 안티패턴), 2026-10-01 확인

### V-060 관측 장치 자체의 검증(주입한 장애가 보이는가)
- **무엇/왜:** 장애를 주입할 때마다 관측이 그것을 보여주는지도 함께 판정한다: 해당 의존성 지표가 변했나, 트레이스에 지연 스팬이 보이나, 로그에 오류가 request_id와 함께 남았나, 대시보드 첫 화면에서 식별되나.
- **실패 양상:** 시스템은 버텼지만 관측에는 아무것도 안 보였다 — 다음 실제 장애에서 원인 분석 불가. 관측 통제가 "설정 있음"에 머문다.
- **신호:** 🟢 실험 결과에 관측 체크리스트 / 🔴 관측 통제를 설정 존재로만 판정
- **필요 수준:** 관측 통제가 있는 모든 수준.
- **처방:** 공통: O 통제마다 `verify`에 이 검증을 연결(§8.3 lint 규칙과 같은 원리).
- **검증:** 장애 유형 → 기대 관측 신호 매핑표에서 누락 0.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(설계 문서 §8.3, §17.1) ⚠️근거없음

### V-061 디그레이드 모드 검증
- **무엇/왜:** 의존성 장애 때 핵심 기능을 줄여서라도 유지하는 설계(D L3: 의존성 장애 시 읽기 유지)가 실제로 동작하는지, 그리고 디그레이드 상태가 관측에 드러나는지(응답 헤더·지표) 확인한다.
- **실패 양상:** 디그레이드 경로가 코드에 있지만 한 번도 실행된 적 없어 실제 장애 때 예외를 던진다. 디그레이드 중임을 아무도 몰라 장기간 방치된다.
- **신호:** 🟢 디그레이드 표시(SWA nginx `X-Auth-Degraded` 헤더 처리, readyz 부분 의존성 설계), 디그레이드 카운터 지표 / 🔴 D=L3 + 디그레이드 경로 시험 없음
- **필요 수준:** D=L3 (D-CTL-005).
- **처방:** 공통: 의존성별 블랙홀(V-037) 중 기능별 기대 동작 표(읽기 OK, 쓰기 503 등)로 판정.
- **검증:** 기대 동작 표 100% 일치, 디그레이드 지표·헤더 노출 확인.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(설계 문서 §4.1 D L3) ⚠️근거없음

### V-062 리전 장애 복구 리허설
- **무엇/왜:** 다른 리전에 IaC로 환경을 새로 만들고 백업·복제본에서 데이터를 복구해 서비스를 여는 전 과정을 리허설한다. 관측·알림·DNS 전환까지 포함한다.
- **실패 양상:** 복구 리전에서 이미지 레지스트리·비밀·할당량이 없어 막힌다. 앱은 떴는데 관측이 없다(O-046).
- **신호:** 🟢 DR 런북 + 리허설 기록 + 교차 리전 백업 복사 / 🔴 D=L3 + 단일 리전 백업만
- **필요 수준:** D=L3에서만. D≤2에는 과잉(COST-007).
- **처방:** 티어1/2: 교차 리전 백업 복사 + IaC 리전 변수화 + 반기 리허설. 비용을 줄이려면 리허설 후 즉시 파기.
- **검증:** 통과 기준: RTO·RPO 가정(D L3: RTO 5분 이하는 백업 복원으로 불가능할 수 있음 → 결과로 DR 전략 등급 판단) 측정, 복구 리전에서 스모크·알림 시험 통과.
- **비용 영향:** 증가(리허설 동안 두 번째 리전 자원).
- **출처:** 일반 원칙(출처 미확인). DR 전략 구분은 설계 문서 S13(이번 작업에서 재확인 안 함). ⚠️근거없음

### V-063 검증 결과를 통제 상태로 되돌리기
- **무엇/왜:** 각 검증은 통제 ID와 연결되고, 통과하면 그 통제 상태가 "설정 확인"에서 "동작 확인"으로 바뀐다. 실패하면 처방이 다시 생긴다. 검증 결과는 커밋·구성·날짜와 함께 남겨 오래되면 재검증 대상이 된다.
- **실패 양상:** 검증은 했는데 리포트에는 여전히 "설정 있음"으로만 나오거나, 반년 전 구성의 통과 결과가 현재 구성의 보증처럼 쓰인다.
- **신호:** 🟢 `report.json` 통제별 `verified_at`, `verified_commit`, `verification_id` / 🔴 검증 결과가 별도 파일에만
- **필요 수준:** 모든 수준(P4 공통).
- **처방:** 공통: 결과 스키마에 검증 ID·커밋·오버레이(V-019)·유효 기간(기본 90일 또는 관련 IaC 변경 시 만료).
- **검증:** 관련 IaC 파일이 바뀌면 해당 통제의 검증 상태가 만료되는지 단위 테스트.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(설계 문서 §8.3, §17.2) ⚠️근거없음

---

## 새 축·규칙 후보

### 1. O 축(관측·운영)을 다섯 번째 시나리오로 둘지에 대한 제안
- **결론 제안:** O는 D/T/U/C처럼 "필요 수준을 따로 정하는 시나리오"가 아니라, **최대 필요 수준에서 파생되는 통제 묶음**으로 두는 편이 규칙이 단순하다(§17.4 표가 이미 이 구조다). 다만 리포트에는 별도 카드로 보여준다.
- **O 수준 정의 초안(파생):**

| O 수준 | 조건 | 통제 |
|---|---|---|
| O0 | 최대 필요 수준 L0 | stdout 로그(O-001), 비용 알림(O-069) |
| O1 | 최대 L1 | + 구조화 로그(O-002), 요청 ID(O-004), 외부 업타임(O-047), 5xx 비율 알림(O-041), 누락 데이터 처리(O-043), 에러 추적(O-033), 로그 보존(O-009), PII 마스킹(O-007, 개인정보 있을 때), 백업 성공 감시(O-067, D≥1), 인증서 만료(O-068) |
| O2 | 최대 L2 | + RED·히스토그램(O-013, O-016), 카디널리티 통제(O-017), SLI/SLO(O-037~O-038), 여러 창 소진율 알림(O-039), 대시보드(O-059), 런북(O-060), 알림 종단 확인(O-044), 사후 분석(O-063), 버전 태깅(O-034, U≥2), 트레이싱(O-031, 서비스 2개 이상) |
| O3 | 최대 L3 | + 의존성별 지표(O-018, O-020, O-021, O-025), 합성 사용자 시나리오(O-048), 온콜·에스컬레이션(O-061), 인시던트 체계(O-062), 상태 페이지(O-051), 게임데이(V-057) |

- **과잉 규칙(축소):** 현재 O 수준이 파생 O 수준보다 2 이상 높으면 `kind: reduce`(O-071).

### 2. 탐지기에 추가할 사실 후보
| 사실 ID | 탐지 패턴 | 쓰는 규칙 |
|---|---|---|
| `obs.log.structured` | `JsonFormatter`, `structlog`, `pino`, `log_format ... escape=json` | O-002 |
| `obs.log.pii_risk` | `logger.*(request.body|req.headers|password)`, Sentry `send_default_pii=True` | O-007 |
| `obs.request_id` / `obs.request_id.untrusted` | `x-request-id` 읽기 / 형식 검사 없이 그대로 사용 | O-004, O-008 |
| `obs.trace.otel` | `opentelemetry-*`, `@opentelemetry/*` | O-005, O-031 |
| `obs.metrics.histogram` / `obs.metrics.summary_avg` | `Histogram(` / `Summary(` + `avg(` 질의 | O-016, V-022 |
| `obs.metrics.high_cardinality` | 라벨에 `url.path`, `originalUrl`, `user_id`, `email` | O-017 |
| `obs.metrics.cumulative_ratio_gauge` | `Gauge` + `set_function` + 비율 계산(누적) | O-021 |
| `obs.loop_lag` | `monitorEventLoopDelay`, 루프 지연 히스토그램 | O-022 |
| `obs.metrics.exposed_public` | 공개 라우터의 `/metrics`, 인그레스 차단 없음 | O-029 |
| `obs.error_tracking` | `sentry-sdk`, `@sentry/*` | O-033, O-050 |
| `obs.rum` | `web-vitals`, `@vercel/speed-insights` | O-049 |
| `tf.log_retention.missing` | `aws_cloudwatch_log_group` without `retention_in_days` | O-009 |
| `tf.alarm.missing_data_not_breaching` | `treat_missing_data = "notBreaching"` on 오류율·지연 알람 | O-043 |
| `tf.budget` / `tf.cost_anomaly` | `aws_budgets_budget`, `aws_ce_anomaly_monitor`, `google_billing_budget` | O-069 |
| `tf.uptime_check` / `tf.synthetics` | `google_monitoring_uptime_check_config`, `aws_synthetics_canary` | O-047, O-048 |
| `tf.restore_testing` | `aws_backup_restore_testing_plan` | O-067, V-056 |
| `k8s.liveness.deep` | liveness 경로 = readiness 경로이면서 같은 failureThreshold, 또는 liveness 핸들러가 DB 호출 | O-052 |
| `loadtest.closed_model` | k6 `vus`/`constant-vus`/`ramping-vus` + 지연 임계 | V-008, V-021 |
| `loadtest.thresholds` | k6 `thresholds` 존재 | V-015 |
| `loadtest.same_host` | 부하 스크립트 대상이 `localhost` + 같은 머신 클러스터(kind) | V-010, V-019 |

### 3. 규칙집 형식에 대한 제안
- **`verify` 필드를 O 통제에도 강제:** 관측 통제도 "설정 있음 ≠ 동작함"이다. 예: O-047(업타임)은 V-058(알림 발화)·V-060(관측 검증) 없이 "충족"이 될 수 없게 한다. §8.3 lint 확장.
- **검증 결과 유효 기간:** 통제의 "동작 확인" 상태는 관련 IaC·매니페스트 파일이 바뀌거나 90일이 지나면 만료(V-063). 출처 90일 규칙과 같은 주기.
- **테스트 환경 차이 표기:** P4 결과에 `overlay`, `diff_from_prod`를 필수로 두고, 운영과 다른 구성의 결과는 통제 상태를 바꾸지 못하게 한다(V-019). SWA의 로컬 결과가 정확히 이 경우다.
- **생성기 유효성 게이트:** 부하 결과는 `dropped_iterations == 0`(또는 목표 대비 1% 미만)과 생성기 CPU < 80%를 만족할 때만 판정에 쓴다(V-009, V-010). 아니면 "측정 무효".
- **표본 부족 게이트:** 구간별 표본 수가 기준 미달이면 그 구간의 p95/p99는 판정에 쓰지 않는다(V-024).
- **비용 규칙 추가 후보:** COST-010 "AWS 로그 그룹 보존 기간 미지정 → 무기한 보존 경고"(O-009), COST-011 "L1 서비스에 유료 APM·100% 트레이스 → 축소"(O-071), COST-012 "Spot 사용인데 중단 검증(V-044) 없음 → 절감 처방 보류".

### 4. simple-web-app에서 확인한 구체적 판정 예(F1 golden 후보)
- 충족: 구조화 JSON 로그 stdout(O-001/002), 요청 ID 전파·응답 헤더(O-004), 라우트 템플릿 라벨(O-017), 큐 lag·DLQ 지표(O-020), 얕은 liveness·부분 의존성 readiness(O-052), 내부 엔드포인트 외부 차단(O-029), 오픈 모델 스파이크 + 임계치 + 거절 분리 집계(V-004, V-008, V-015, V-016), 테스트 데이터 실행 ID 분리(V-014).
- 부분: 외부 `X-Request-ID`를 검증 없이 신뢰(O-008), 캐시 적중률이 누적 게이지(O-021), 트레이스 전파는 `X-Request-ID`만(O-005, D3·T3이므로 L3 대상), 합성 모니터는 CI E2E만(O-048).
- 미충족·무효: 로컬 부하 결과는 생성기와 대상이 같은 머신(V-010)이고 리밋 완화 오버레이(V-019)라 통제 판정에 쓸 수 없음 — README도 같은 결론. 복원 리허설(V-056)·게임데이(V-057) 없음. SLO·소진율 알림·런북(O-037~O-039, O-060) 정의 없음(D3 T3이므로 O3 필요).
