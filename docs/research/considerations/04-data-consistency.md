# 데이터 정합성·저장소·메시징

infrafit 규칙집의 **시나리오 C(정합성)** 재료다. 트랜잭션·잠금·제약 같은 DB 안쪽 통제부터 멱등성·웹훅·큐·아웃박스·캐시·복제처럼 "저장소가 둘 이상일 때 깨지는 것"까지, 바이브코더 앱(Next.js/Prisma/Supabase/Firebase/Stripe/토스페이먼츠/Express/FastAPI/Django)에서 코드 신호로 판정할 수 있는 항목을 모았다.
트래픽·성능(커넥션 풀 포함)은 T, 백업·DR은 D, 배포·마이그레이션은 U, 일반 보안·규제·관측은 다른 문서 담당이다. 각 항목의 비용 영향은 적었지만 비용 판정 자체는 하지 않는다.
출처 URL은 모두 2026-10-01에 실제로 열어 확인했다. 열지 못한 경우 "일반 원칙(출처 미확인)"으로 적었다.

**표기**
- 신호: 🟢 코드·스키마·설정으로 확정 / 🟡 힌트, 추론 필요 / 🔴 코드에 없음 → 가정으로 처리
- 티어: 티어0 = 매니지드 플랫폼 설정(Vercel+Supabase, Firebase 등), 티어1 = 컨테이너 + 매니지드 서비스(Cloud Run, ECS Fargate), 티어2 = Terraform + k8s(EKS/GKE)
- 수준: 설계 문서 §4.1의 C L0~L3. "C L2 이상"은 필요 수준이 L2 이상일 때만 이 통제를 요구한다는 뜻이다.
- 예시 앱: `simple-web-app`(이하 SWA)에서 실제로 쓰인 구현을 신호 예시로 들었다.

## 목차

- [A. 트랜잭션·격리·동시성 제어](#a-트랜잭션격리동시성-제어) — C-001 ~ C-016
- [B. 스키마 제약·데이터 모델링](#b-스키마-제약데이터-모델링) — C-017 ~ C-031
- [C. API 멱등성·재시도](#c-api-멱등성재시도) — C-032 ~ C-038
- [D. 결제·금액](#d-결제금액) — C-039 ~ C-052
- [E. 웹훅 수신](#e-웹훅-수신) — C-053 ~ C-057
- [F. 메시징·큐·비동기 작업](#f-메시징큐비동기-작업) — C-058 ~ C-071
- [G. 이중 쓰기·아웃박스·사가](#g-이중-쓰기아웃박스사가) — C-072 ~ C-077
- [H. 캐시·Redis 일관성](#h-캐시redis-일관성) — C-078 ~ C-083
- [I. 복제·읽기 일관성·시간](#i-복제읽기-일관성시간) — C-084 ~ C-088
- [J. 분산 락·크론·배치](#j-분산-락크론배치) — C-089 ~ C-095
- [K. BaaS 무결성 (Supabase·Firebase)](#k-baas-무결성-supabasefirebase) — C-096 ~ C-102
- [L. 파일·검색·파생 저장소](#l-파일검색파생-저장소) — C-103 ~ C-106
- [M. 삭제·보존·감사](#m-삭제보존감사) — C-107 ~ C-113
- [새 축·규칙 후보](#새-축규칙-후보)

---

## A. 트랜잭션·격리·동시성 제어

### C-001 다중 쓰기의 트랜잭션 경계
- **무엇/왜:** 한 요청이 두 개 이상의 행·테이블을 고치면(주문 생성 + 재고 차감, 이체의 출금 + 입금) 모두 성공하거나 모두 실패해야 한다. ORM은 기본적으로 문장마다 자동 커밋하므로 묶지 않으면 중간 실패가 반쪽 상태를 남긴다.
- **실패 양상:** 주문 행은 생겼는데 재고는 그대로(초과 판매), 출금만 되고 입금 실패(돈 증발), 가입 행은 있는데 프로필 행이 없어 이후 요청이 500.
- **신호:** 🟢 한 핸들러 안에서 `prisma.x.create` / `update`가 2회 이상인데 `prisma.$transaction`(Prisma 7 이하) 또는 `db.transaction(async (tx) => …)`(Prisma 8) 밖에 있음, Django 뷰에 `.save()`/`.create()` 여러 번 + `transaction.atomic` 없음 + `ATOMIC_REQUESTS` 미설정, SQLAlchemy `session.commit()`이 중간에 여러 번. 탐지기 사실 `tx.multi_write_no_tx`.
- **시나리오·수준:** C L1 이상 (L1의 핵심 통제)
- **처방:** 코드: 쓰기 묶음을 트랜잭션 하나로 감싸고, 트랜잭션 안에서는 같은 트랜잭션 클라이언트(`tx`)만 쓴다. 인프라: 없음(모든 티어 공통). 티어0에서 HTTP 기반 서버리스 드라이버를 쓰면 인터랙티브 트랜잭션이 안 될 수 있으니 C-015를 같이 본다.
- **검증:** 두 번째 쓰기 직전에 예외를 주입하는 테스트를 돌리고 첫 번째 쓰기가 롤백됐는지 확인. 불변식 쿼리(예: 주문 수 = 재고 차감 합)를 테스트 후 실행.
- **비용 영향:** 중립. 코드 변경뿐이다.
- **출처:** https://docs.djangoproject.com/en/stable/topics/db/transactions/ (Django 기본 autocommit, `atomic`), https://www.prisma.io/docs/orm/prisma-client/queries/transactions (Prisma 8은 `$transaction`이 없고 `db.transaction(async (tx) => …)`만 있음)

### C-002 읽고-고치고-쓰기(lost update)
- **무엇/왜:** 값을 애플리케이션으로 읽어 와서 더한 뒤 다시 저장하면, 동시에 같은 일을 한 다른 요청의 결과를 덮어쓴다. PostgreSQL 기본 격리 수준(Read Committed)은 이를 막지 않는다.
- **실패 양상:** 좋아요·조회수·포인트·잔액이 동시 요청에서 일부 사라진다. 포인트 적립 2건이 동시에 오면 1건만 반영.
- **신호:** 🟢 `findUnique` → JS에서 `+ 1` → `update({ data: { count: newValue } })`, Django `obj.count += 1; obj.save()`, SQLAlchemy `row.balance -= x` 후 commit. 🟢 반대로 안전한 패턴: Django `F("count") + 1`, raw `UPDATE … SET count = count + 1`, Prisma 7 이하 `{ increment: 1 }`.
- **시나리오·수준:** C L1 이상 (금액·재고면 L3 신호로 승격)
- **처방:** 코드: DB가 계산하도록 원자적 UPDATE로 바꾼다. Prisma 8은 PostgreSQL에서 `increment`가 없으므로 raw SQL `UPDATE … SET x = x + $1`를 쓴다. 복잡한 계산이면 C-004(비관적) 또는 C-005(낙관적) 잠금. 인프라: 없음.
- **검증:** 같은 행에 +1 요청을 100개 동시에 보내고 최종 값이 정확히 +100인지 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.djangoproject.com/en/stable/ref/models/expressions/ ("the work of the first thread will be lost" — F()로 경쟁 조건 회피), https://www.prisma.io/docs/orm/fundamentals/writing-data ("There is no `increment` on PostgreSQL… write the update as raw SQL", Prisma 8 기준), https://www.postgresql.org/docs/current/transaction-iso.html (기본 Read Committed)

### C-003 조건부 차감(재고·좌석·잔액·쿠폰 수량)
- **무엇/왜:** "남은 수량이 충분하면 차감"은 확인과 차감이 한 문장이어야 한다. `SELECT`로 확인하고 `UPDATE`로 차감하면 그 사이에 다른 요청이 끼어든다.
- **실패 양상:** 초과 판매, 같은 좌석 이중 예약, 잔액 음수, 선착순 100명 쿠폰이 130명에게 발급.
- **신호:** 🟢 `if (product.stock >= qty)` 다음 줄에 `update(… stock: product.stock - qty)`, 필드명 `stock|inventory|seats|remaining|balance|quota` 감소 패턴(탐지기 사실 `concurrency.decrement_no_lock`). 🟢 안전 패턴: `UPDATE … SET stock = stock - $1 WHERE id = $2 AND stock >= $1` 후 영향 행 수 확인, `select_for_update()`.
- **시나리오·수준:** C L3 (이 패턴 자체가 L3 판정 신호)
- **처방:** 코드: 조건을 WHERE에 넣은 단일 UPDATE + 영향 행 수 0이면 품절 처리. 추가 방어선으로 `CHECK (stock >= 0)`(C-018). 고경합(선착순)에서는 단일 행 핫스팟이 되므로 T 문서의 큐·토큰 버킷과 함께 판단. 인프라: 없음(티어 무관).
- **검증:** 재고 10에 1개짜리 구매 요청 50개를 동시에 넣고 성공 정확히 10건, 최종 재고 0, 음수 없음 확인.
- **비용 영향:** 중립.
- **출처:** https://www.postgresql.org/docs/current/explicit-locking.html (행 잠금), https://www.postgresql.org/docs/current/ddl-constraints.html (CHECK 제약), https://docs.djangoproject.com/en/stable/ref/models/querysets/ (`select_for_update`)

### C-004 비관적 잠금(SELECT … FOR UPDATE)
- **무엇/왜:** 읽은 값으로 복잡한 판단(여러 행 비교, 외부 규칙)을 한 뒤 써야 하면 읽는 시점에 행을 잠근다. 잠금은 트랜잭션이 끝날 때 풀린다.
- **실패 양상:** 잠금을 트랜잭션 밖에서 잡거나(자동 커밋이면 즉시 풀림) 잠금 없이 판단하면 C-002/C-003과 같은 이중 처리. Django는 트랜잭션 밖에서 `select_for_update`를 평가하면 `TransactionManagementError`.
- **신호:** 🟢 `select_for_update()`, `.with_for_update()`(SQLAlchemy), raw `FOR UPDATE`, `FOR UPDATE NOWAIT`. 🟡 같은 파일에 `transaction.atomic`/`$transaction`이 있는지 함께 확인해야 유효.
- **시나리오·수준:** C L3
- **처방:** 코드: 트랜잭션 안에서 잠그고, 잠금 범위를 최소 행으로, 잠금을 쥔 채 외부 HTTP 호출 금지(C-009). 대기 대신 즉시 실패가 낫다면 `NOWAIT`. 인프라: 없음.
- **검증:** 두 세션에서 같은 행을 `FOR UPDATE`로 잡게 하고 두 번째가 대기(또는 NOWAIT 오류)하는지 확인. 동시 요청 주입 후 불변식 검사.
- **비용 영향:** 중립(경합 시 지연 증가).
- **출처:** https://www.postgresql.org/docs/current/explicit-locking.html ("will be blocked until the current transaction ends"), https://docs.djangoproject.com/en/stable/ref/models/querysets/ (트랜잭션 필수, `nowait`, `skip_locked`)

### C-005 낙관적 잠금(버전 컬럼)
- **무엇/왜:** 사용자가 폼을 오래 열어 두는 편집(문서, 설정, 주문 수정)처럼 잠금을 오래 쥘 수 없을 때, `version` 컬럼을 두고 `UPDATE … WHERE id = ? AND version = ?`로 갱신해 충돌을 감지한다.
- **실패 양상:** 두 관리자가 같은 상품을 동시에 수정하면 나중 저장이 앞의 변경을 조용히 지운다.
- **신호:** 🟢 스키마에 `version Int`/`lock_version`/`updatedAt` 비교 조건 UPDATE. 🟡 편집 폼 + PUT 전체 덮어쓰기 + 버전 필드 없음. 🟡 `If-Match`/ETag 헤더 사용 여부.
- **시나리오·수준:** C L2 이상 (협업 편집·관리자 화면이 있을 때)
- **처방:** 코드: 버전 컬럼 + 조건부 UPDATE, 영향 행 0이면 409 Conflict 반환. HTTP로는 ETag/If-Match. 인프라: 없음.
- **검증:** 같은 버전으로 두 번 PUT하고 두 번째가 409인지 확인.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인). DB 쪽 근거로 조건부 UPDATE의 원자성은 https://www.postgresql.org/docs/current/transaction-iso.html ⚠️근거없음

### C-006 격리 수준과 write skew
- **무엇/왜:** PostgreSQL 기본 Read Committed는 반복 불가 읽기·팬텀·직렬화 이상을 허용한다. "당직 의사가 최소 1명" 같은 **여러 행에 걸친 불변식**은 각 트랜잭션이 서로 다른 행을 고치므로 행 잠금으로 막히지 않는다(write skew).
- **실패 양상:** 두 의사가 동시에 휴무 신청 → 당직 0명. 회의실 예약 시간 겹침 검사를 SELECT로 하고 INSERT → 이중 예약.
- **신호:** 🟡 "존재하지 않음을 확인 후 INSERT"(겹침 검사, 한도 합계 검사) 패턴. 🟢 `SET TRANSACTION ISOLATION LEVEL SERIALIZABLE`, Prisma 7 `isolationLevel: 'Serializable'`, Django `OPTIONS: {"isolation_level": …}`. 🔴 격리 수준 설정이 없으면 기본값(Read Committed)으로 가정.
- **시나리오·수준:** C L3 (예약·좌석·한도 도메인)
- **처방:** 코드: 가능하면 제약으로 바꾼다(유니크, 배타 제약 `EXCLUDE`, 부분 유니크 인덱스). 안 되면 해당 트랜잭션만 SERIALIZABLE + 재시도(C-007). Prisma 8은 `isolationLevel` 옵션이 없으므로 raw `SET TRANSACTION`을 트랜잭션 첫 문장으로. 인프라: 없음.
- **검증:** 겹치는 예약 두 건을 동시에 넣는 테스트를 수백 회 반복해 겹침이 0건인지 확인.
- **비용 영향:** 중립~소폭 증가(재시도로 인한 DB 부하).
- **출처:** https://www.postgresql.org/docs/current/transaction-iso.html (Read Committed 기본, 허용 이상 현상), https://www.postgresql.org/docs/current/ddl-constraints.html (배타 제약), https://www.prisma.io/docs/orm/prisma-client/queries/transactions (Prisma 8에 `isolationLevel` 없음)

### C-007 직렬화 실패·교착 상태의 재시도
- **무엇/왜:** Repeatable Read/Serializable에서는 SQLSTATE `40001`이 정상 동작의 일부이고, 교착 상태는 DB가 한쪽을 중단(`40P01`)시켜 푼다. 앱이 "트랜잭션 전체를 처음부터" 재시도해야 한다. ORM이 대신 해 주지 않는다.
- **실패 양상:** 경합 시간대에 결제·예약이 간헐적 500. 재시도를 문장 단위로만 하면 앞 문장 결과를 잃어 반쪽 처리.
- **신호:** 🟢 `40001`, `40P01`, `serialization_failure`, `deadlock_detected`, `P2034`(Prisma 쓰기 충돌 코드) 처리 코드 유무. SWA는 `is_transient`에서 `40001`, `40P01`을 일시 오류로 분류(rulings Task 9).
- **시나리오·수준:** C L3 (C-006 또는 C-004를 쓰면 반드시 같이)
- **처방:** 코드: 트랜잭션 함수 전체를 감싸는 재시도 래퍼(지수 백오프 + 상한 횟수). 트랜잭션 안에 외부 부수효과를 두지 않아야 재시도가 안전하다(C-009, C-074). 인프라: 없음.
- **검증:** 두 세션으로 교착을 의도적으로 만들고 앱 레벨에서 한쪽이 재시도 후 성공하는지 확인.
- **비용 영향:** 중립.
- **출처:** https://www.postgresql.org/docs/current/transaction-iso.html ("it should abort the current transaction and retry the whole transaction from the beginning"), https://www.postgresql.org/docs/current/explicit-locking.html (교착 자동 감지), https://www.prisma.io/docs/orm/prisma-client/queries/transactions ("Prisma ORM does not retry write conflicts for you")

### C-008 잠금 순서와 교착 회피
- **무엇/왜:** 두 트랜잭션이 A→B, B→A 순서로 잠그면 교착이 난다. 이체(보내는 계좌, 받는 계좌)가 대표적이다.
- **실패 양상:** 서로에게 송금하는 요청이 동시에 오면 한쪽이 교착으로 실패. 재시도가 없으면 사용자 오류.
- **신호:** 🟡 한 트랜잭션에서 같은 테이블의 서로 다른 두 행을 요청 파라미터 순서대로 잠금/갱신(`from`, `to`).
- **시나리오·수준:** C L3
- **처방:** 코드: 항상 ID 오름차순으로 잠근다. C-007 재시도와 병행. 인프라: 없음.
- **검증:** A→B, B→A 이체를 동시에 1,000쌍 실행해 교착 로그가 0건(또는 재시도 후 전부 성공)인지 확인.
- **비용 영향:** 중립.
- **출처:** https://www.postgresql.org/docs/current/explicit-locking.html ("acquire locks on multiple objects in a consistent order")

### C-009 트랜잭션 안의 외부 호출
- **무엇/왜:** DB 트랜잭션 안에서 결제 API·메일·HTTP를 호출하면 (1) 롤백해도 외부 효과는 되돌릴 수 없고 (2) 외부 지연 동안 행 잠금을 쥔다.
- **실패 양상:** 결제는 승인됐는데 이후 DB 오류로 롤백 → 돈은 빠졌는데 주문 없음. 외부 API가 30초 멈추면 같은 행을 기다리는 요청이 줄줄이 타임아웃.
- **신호:** 🟢 `$transaction`/`db.transaction`/`atomic` 블록 안에 `fetch`, `axios`, `stripe.`, `httpx`, `requests.`, `sendMail`, `queue.add` 호출.
- **시나리오·수준:** C L2 이상
- **처방:** 코드: 외부 호출은 트랜잭션 밖으로. 순서는 "로컬에 pending 기록 커밋 → 외부 호출(멱등 키 포함) → 결과 반영" 또는 아웃박스(C-073). 인프라: 없음.
- **검증:** 외부 호출 성공 직후 DB 커밋 실패를 주입해 조정(C-049) 작업이 불일치를 찾아내는지 확인.
- **비용 영향:** 중립.
- **출처:** https://microservices.io/patterns/data/transactional-outbox.html (2PC 없이 DB와 메시지를 원자적으로 다루는 문제), https://docs.djangoproject.com/en/stable/topics/db/transactions/ (`on_commit`은 롤백 시 실행되지 않음) ⚠️출처부적격

### C-010 자동 커밋 기본값과 요청 단위 트랜잭션
- **무엇/왜:** Django·SQLAlchemy·Prisma 모두 명시하지 않으면 문장 단위로 커밋한다. Django `ATOMIC_REQUESTS=True`는 요청 전체를 트랜잭션으로 묶어 주지만 모든 뷰에 비용이 든다.
- **실패 양상:** 개발자는 "요청 하나 = 트랜잭션 하나"라고 믿지만 실제로는 문장마다 커밋되어 C-001 실패가 생긴다.
- **신호:** 🟢 Django `DATABASES[...]["ATOMIC_REQUESTS"]`, `@transaction.non_atomic_requests`. 🟢 SQLAlchemy `autocommit`/`AUTOCOMMIT` 격리 설정. 🔴 설정 없으면 자동 커밋으로 가정.
- **시나리오·수준:** C L1 이상
- **처방:** 코드: 필요한 뷰에만 `atomic`(권장) 또는 `ATOMIC_REQUESTS`. 인프라: 없음.
- **검증:** C-001과 동일한 실패 주입.
- **비용 영향:** 중립(요청 단위 트랜잭션은 DB 부하 소폭 증가).
- **출처:** https://docs.djangoproject.com/en/stable/topics/db/transactions/ (기본 autocommit, ATOMIC_REQUESTS의 트레이드오프)

### C-011 중첩 트랜잭션의 착각
- **무엇/왜:** 트랜잭션 함수 안에서 다른 트랜잭션 함수를 부르면 프레임워크마다 의미가 다르다. Django는 savepoint, Prisma 8은 **중첩되지 않고 별개 트랜잭션**이 된다.
- **실패 양상:** 바깥이 롤백돼도 안쪽 "트랜잭션"은 이미 커밋되어 반쪽 상태.
- **신호:** 🟢 `db.transaction` 콜백 안에서 `db.transaction` 또는 전역 `db`/`prisma` 클라이언트를 호출(전달받은 `tx` 대신). 🟢 서비스 함수가 내부에서 자체 트랜잭션을 여는데 상위에서도 트랜잭션으로 감쌈.
- **시나리오·수준:** C L1 이상
- **처방:** 코드: 트랜잭션 클라이언트를 인자로 전달하는 구조. Django는 `atomic(durable=True)`로 최외곽을 강제할 수 있다. 인프라: 없음.
- **검증:** 바깥 트랜잭션 마지막에 예외를 던지는 테스트에서 안쪽 쓰기가 남지 않는지 확인.
- **비용 영향:** 중립.
- **출처:** https://www.prisma.io/docs/orm/prisma-client/queries/transactions ("calling `db.transaction()` inside a callback doesn't nest"), https://docs.djangoproject.com/en/stable/topics/db/transactions/ (중첩은 savepoint, `durable=True`)

### C-012 찾고 없으면 만들기(get_or_create) 경쟁
- **무엇/왜:** "없으면 INSERT"를 두 요청이 동시에 하면 둘 다 "없음"을 본다. 유니크 제약이 없으면 중복 행이 생긴다.
- **실패 양상:** 같은 이메일 계정 2개, 같은 사용자의 장바구니 2개, 같은 주문의 결제 레코드 2개.
- **신호:** 🟢 Django `get_or_create`/`update_or_create` 대상 필드에 `unique=True`/`UniqueConstraint` 없음. 🟢 `findFirst` → `null`이면 `create`. 🟢 Prisma `upsert`의 `where` 필드가 `@unique`가 아님.
- **시나리오·수준:** C L1 이상
- **처방:** 코드: 조회 키에 유니크 제약 + `INSERT … ON CONFLICT`(C-013) 또는 유니크 위반 예외를 잡아 재조회. 인프라: 없음.
- **검증:** 같은 키로 생성 요청 50개를 동시에 보내고 행이 1개인지 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.djangoproject.com/en/stable/ref/models/querysets/ ("duplicate objects can still be created… Use a unique constraint")

### C-013 원자적 upsert(INSERT … ON CONFLICT)
- **무엇/왜:** PostgreSQL `ON CONFLICT DO UPDATE`는 동시성 아래서도 INSERT 또는 UPDATE 중 하나를 원자적으로 보장한다. `DO NOTHING`은 중복을 조용히 무시하는 멱등 INSERT가 된다.
- **실패 양상:** 애플리케이션 레벨 upsert(조회 후 분기)는 C-012와 같은 중복·유니크 위반 500을 만든다.
- **신호:** 🟢 `ON CONFLICT`, Prisma 8 `conflictOn`, `{ onConflict: "skip" }`, SQLAlchemy `insert(...).on_conflict_do_nothing()`. SWA `posts_repo.py`의 `ON CONFLICT (id) DO NOTHING`이 큐 재전송 시 멱등 INSERT 역할.
- **시나리오·수준:** C L1 이상 (큐 소비자가 있으면 L2 통제)
- **처방:** 코드: 충돌 대상(유니크 인덱스)을 명시한 upsert. 한 문장이 같은 행을 두 번 건드리면 오류가 나므로 배치 입력은 키 중복을 미리 제거. 인프라: 없음.
- **검증:** 같은 배치를 두 번 적재해 행 수가 변하지 않는지 확인.
- **비용 영향:** 중립.
- **출처:** https://www.postgresql.org/docs/current/sql-insert.html ("guarantees an atomic INSERT or UPDATE outcome… even under high concurrency"), https://www.prisma.io/docs/orm/fundamentals/writing-data (`conflictOn`, `onConflict: "skip"`, Prisma 8)

### C-014 DB 테이블을 작업 큐로 쓸 때 SKIP LOCKED
- **무엇/왜:** 별도 브로커 없이 `jobs` 테이블을 큐로 쓰는 앱이 많다. 여러 워커가 같은 행을 집지 않으려면 `FOR UPDATE SKIP LOCKED`로 집고 같은 트랜잭션에서 상태를 바꾼다.
- **실패 양상:** 워커 2대가 같은 작업을 동시에 실행(메일 2통, 정산 2회). 또는 단순 `FOR UPDATE`로 워커들이 줄 서서 처리량이 1대 수준.
- **신호:** 🟢 `status = 'pending'` 조회 후 `status = 'running'` 업데이트가 별개 문장, `SKIP LOCKED` 유무. 🟢 graphile-worker, pg-boss, Solid Queue 같은 PG 기반 큐 라이브러리(이미 처리됨).
- **시나리오·수준:** C L2 이상
- **처방:** 코드: `SELECT … FOR UPDATE SKIP LOCKED LIMIT n` + 같은 트랜잭션에서 상태 변경, 또는 검증된 라이브러리 사용. 인프라: 별도 큐 불필요(티어0~2 모두 비용 절감 선택지).
- **검증:** 워커 N개를 띄우고 작업 1,000건을 넣어 각 작업의 실행 횟수가 정확히 1인지 집계.
- **비용 영향:** 감소 가능(브로커를 따로 두지 않음).
- **출처:** https://www.postgresql.org/docs/current/sql-select.html ("can be used to avoid lock contention with multiple consumers accessing a queue-like table")

### C-015 서버리스 DB 드라이버와 트랜잭션 제약
- **무엇/왜:** 티어0(Vercel·Netlify·Cloudflare)에서 HTTP 기반 서버리스 DB 드라이버나 엣지 런타임을 쓰면 인터랙티브 트랜잭션(읽고 판단하고 쓰기)을 지원하지 않거나 일괄 문장만 지원하는 경우가 있다. 또 트랜잭션 모드 풀러 뒤에서는 세션 단위 기능(세션 advisory lock, `SET`)이 다른 요청으로 새어 나간다.
- **실패 양상:** 개발 환경(TCP 드라이버)에서는 되던 잠금·트랜잭션이 배포 후 무시되거나 오류. 세션 락이 풀리지 않아 크론이 영원히 건너뜀.
- **신호:** 🟢 `@neondatabase/serverless`의 HTTP 모드, `@planetscale/database`, Cloudflare D1, `export const runtime = 'edge'` + DB 쓰기, `pgbouncer=true`/포트 6543(Supabase 트랜잭션 풀러) + `pg_advisory_lock`.
- **시나리오·수준:** C L2 이상에서 티어0 선택 시
- **처방:** 코드: 잠금이 필요한 쓰기는 Node 런타임 + TCP(WebSocket) 드라이버로, 또는 DB 함수(RPC) 하나로 원자화(C-101). 세션 락 대신 트랜잭션 락(`pg_try_advisory_xact_lock`). 인프라: 티어0에서 C L3 경로가 이 제약에 걸리면 티어 제외 규칙 후보(새 규칙 후보 참고).
- **검증:** 배포 환경에서 C-003 동시성 테스트를 다시 실행.
- **비용 영향:** 중립~증가(Node 런타임·직접 연결로 바꾸면 커넥션 관리 비용, T 문서 참고).
- **출처:** 일반 원칙(출처 미확인). advisory lock의 세션/트랜잭션 수명 차이는 https://www.postgresql.org/docs/current/explicit-locking.html ⚠️근거없음

### C-016 advisory lock의 수명(세션 vs 트랜잭션)
- **무엇/왜:** PostgreSQL advisory lock은 세션 수준과 트랜잭션 수준이 있다. 세션 락은 롤백해도 유지되고 명시적으로 풀거나 세션이 끝나야 풀린다.
- **실패 양상:** 예외 경로에서 `pg_advisory_unlock`을 빠뜨리면 커넥션 풀에 남은 세션이 락을 계속 쥐어 작업이 영영 실행되지 않음.
- **신호:** 🟢 `pg_advisory_lock(` / `pg_try_advisory_lock(`(세션) vs `pg_advisory_xact_lock(` / `pg_try_advisory_xact_lock(`(트랜잭션).
- **시나리오·수준:** C L2 이상 (크론·마이그레이션 단일 실행 보장용)
- **처방:** 코드: 가능하면 트랜잭션 수준 `pg_try_advisory_xact_lock` 사용. 세션 락이면 `finally`에서 해제. 인프라: 없음.
- **검증:** 락을 잡은 작업 중간에 예외를 던진 뒤 다른 프로세스가 락을 잡을 수 있는지 확인.
- **비용 영향:** 중립.
- **출처:** https://www.postgresql.org/docs/current/explicit-locking.html ("a lock acquired during a transaction that is later rolled back will still be held"), https://www.postgresql.org/docs/current/functions-admin.html

---

## B. 스키마 제약·데이터 모델링

### C-017 유니크 제약(애플리케이션 검사만으로는 부족)
- **무엇/왜:** "이미 있는지 확인 후 저장"은 동시 요청에서 뚫린다(C-012). 중복이 비즈니스 오류인 키(이메일, 닉네임, 주문번호, 외부 결제 ID, 멱등 키)는 DB 유니크 제약이 최종 방어선이다. PostgreSQL 유니크는 기본적으로 NULL끼리 같지 않다고 본다.
- **실패 양상:** 같은 이메일 계정 2개, 같은 `paymentKey`로 주문 2건, NULL 허용 컬럼에 "값 없음" 행이 여러 개.
- **신호:** 🟢 Prisma `@unique`/`@@unique`, Django `unique=True`/`UniqueConstraint`, SQL `UNIQUE`. 🟢 반례: `email String` 이면서 코드에 `findUnique({ where: { email } })` 대신 `findFirst` + 중복 검사. 🟡 이메일을 소문자로 정규화하지 않고 유니크(대소문자 다른 중복). 🟡 `NULLS NOT DISTINCT` 필요 여부.
- **시나리오·수준:** C L1 이상
- **처방:** 코드: 비즈니스 키에 유니크 제약, 정규화된 값(소문자 이메일 등)에 걸기. 외부 결제·이벤트 ID 컬럼은 반드시 유니크. 인프라: 없음.
- **검증:** 같은 값으로 동시 INSERT 후 유니크 위반이 정확히 n-1건인지 확인. 스키마 정적 검사로 외부 ID 컬럼의 유니크 여부 확인.
- **비용 영향:** 중립(인덱스 저장 공간 소폭).
- **출처:** https://www.postgresql.org/docs/current/ddl-constraints.html ("By default, two null values are not considered equal", `NULLS NOT DISTINCT`)

### C-018 NOT NULL·CHECK를 불변식의 최종 방어선으로
- **무엇/왜:** 재고 ≥ 0, 금액 > 0, 할인가 < 정가, 상태 값 목록 같은 규칙은 코드 버그·수동 SQL·다른 서비스가 우회할 수 있다. CHECK 제약은 DB가 거부한다. 단 CHECK는 NULL이면 통과하므로 NOT NULL과 함께 써야 한다.
- **실패 양상:** 음수 재고, 0원 결제, 오타 상태값(`'canceld'`)이 저장돼 이후 집계·상태 머신이 깨짐.
- **신호:** 🟢 SQL 마이그레이션의 `CHECK (`, Django `CheckConstraint`. 🟢 Prisma 스키마에는 CHECK 문법이 없으므로 마이그레이션 SQL에 직접 추가했는지 확인. 🟡 `Int?`/`null=True`가 금액·수량 컬럼에 붙음.
- **시나리오·수준:** C L1 이상 (재고·금액 컬럼이면 L3에서 필수)
- **처방:** 코드: 핵심 수치 컬럼에 NOT NULL + CHECK. Prisma는 `--create-only`로 만든 마이그레이션에 수동 추가. 인프라: 없음.
- **검증:** 경계값(음수, 0, NULL)을 직접 INSERT해 거부되는지 확인.
- **비용 영향:** 중립.
- **출처:** https://www.postgresql.org/docs/current/ddl-constraints.html (CHECK는 true 또는 null이면 만족, NOT NULL)

### C-019 외래 키와 삭제 정책
- **무엇/왜:** 외래 키는 고아 행(존재하지 않는 사용자의 주문)을 막는다. `ON DELETE` 정책(RESTRICT/CASCADE/SET NULL)은 삭제가 어디까지 번지는지 정한다. 외래 키는 참조하는 쪽 컬럼에 인덱스를 자동으로 만들지 않는다.
- **실패 양상:** FK 없이 사용자 삭제 → 주문·결제 기록이 주인 없는 행으로 남아 조인 결과 누락. 반대로 무심코 `CASCADE`면 사용자 탈퇴 한 번에 결제 기록까지 삭제(감사·회계 기록 소실).
- **신호:** 🟢 Prisma `relationMode = "prisma"`(DB FK를 만들지 않음 — PlanetScale/Vitess 계열에서 흔함), `@relation(onDelete: Cascade)`, Django `on_delete=models.CASCADE`가 결제·주문 모델에 붙음. 🟢 MongoDB·Firestore 등 FK가 없는 저장소.
- **시나리오·수준:** C L1 이상
- **처방:** 코드: 관계에 FK를 두고, 금융·감사 기록은 `RESTRICT` 또는 `SET NULL` + 익명화(C-109). FK가 없는 저장소면 정기 고아 검사 작업. 인프라: 없음.
- **검증:** 부모 삭제 시나리오 테스트, 고아 행 검사 쿼리(`LEFT JOIN … WHERE parent.id IS NULL`)가 0건.
- **비용 영향:** 중립.
- **출처:** https://www.postgresql.org/docs/current/ddl-constraints.html (ON DELETE 동작, "Foreign key constraints do NOT automatically create an index on referencing columns")

### C-020 ID 생성 방식(자동 증가 vs UUIDv4 vs UUIDv7)
- **무엇/왜:** 자동 증가 ID는 짧고 정렬되지만 외부에 노출하면 개수·순서가 드러나고, 여러 저장소·오프라인 클라이언트에서 미리 만들 수 없다. UUIDv4는 어디서든 만들 수 있지만 인덱스 지역성이 나쁘다. UUIDv7은 시간 순 정렬 + 분산 생성이 가능하다.
- **실패 양상:** 큐에 넣기 전에 ID가 필요한데 자동 증가라서 DB 왕복 없이는 멱등 INSERT(C-013)를 못 함. UUIDv4 기본키로 쓰기 많은 테이블의 인덱스 페이지가 흩어짐.
- **신호:** 🟢 Prisma `@default(autoincrement())`, `@default(uuid())`, `@default(uuid(7))`, `@default(cuid())`, SQL `SERIAL`/`IDENTITY`, `gen_random_uuid()`, `uuidv7()`, npm `uuid`의 `v7`, `ulid`. SWA는 API에서 UUID를 미리 발급해 큐 메시지에 넣고 워커가 `ON CONFLICT (id) DO NOTHING`.
- **시나리오·수준:** C L2 이상에서 판단 (비동기 쓰기·멱등 INSERT가 있으면)
- **처방:** 코드: 비동기·분산 생성이 필요하면 UUIDv7(PostgreSQL 18 `uuidv7()`, Prisma `uuid(7)`). 외부 노출 ID와 내부 PK 분리도 선택지. 인프라: 없음(PG 18 미만이면 앱에서 생성).
- **검증:** 생성 ID 정렬이 생성 시각 순과 일치하는지, 큐 재전송 시 행이 하나인지 확인.
- **비용 영향:** 중립(UUID는 키 크기 증가로 저장 공간 소폭 증가).
- **출처:** https://www.rfc-editor.org/rfc/rfc9562.html ("Implementations SHOULD utilize UUIDv7 instead of UUIDv1 and UUIDv6", 인덱스 지역성), https://www.postgresql.org/docs/release/18.0/ (`uuidv7()` 추가), https://www.prisma.io/docs/orm/reference/prisma-schema-reference (`uuid(7)`)

### C-021 시퀀스의 빈 번호와 연속 번호 요구
- **무엇/왜:** PostgreSQL 시퀀스 값은 롤백·충돌·크래시로 건너뛸 수 있고 재사용되지 않는다. 세금계산서·영수증 번호처럼 "빈 번호 없는 연속 번호"가 법적·업무 요구라면 시퀀스로 만들 수 없다.
- **실패 양상:** 감사에서 영수증 번호 누락으로 지적, 회계 대사 실패.
- **신호:** 🟡 `invoiceNumber`, `receipt_no`, `serial_no` 같은 컬럼이 `autoincrement()`/`SERIAL`. 🔴 연속 번호 법적 요구 여부는 코드에 없음 → 도메인(커머스·B2B 청구)이면 가정.
- **시나리오·수준:** C L3 (청구서를 직접 발행하는 경우)
- **처방:** 코드: 별도 카운터 행을 `FOR UPDATE`로 잠그고 같은 트랜잭션에서 증가(직렬화 비용 감수), 또는 번호를 결제 확정 후 배치로 부여. 인프라: 없음.
- **검증:** 실패 주입 후 번호 연속성 검사 쿼리.
- **비용 영향:** 중립(쓰기 직렬화로 처리량 감소).
- **출처:** https://www.postgresql.org/docs/current/functions-sequence.html ("sequence objects cannot be used to obtain 'gapless' sequences")

### C-022 큰 정수 ID·금액의 JavaScript 정밀도
- **무엇/왜:** JS `Number`는 2^53−1(9007199254740991)까지만 정확하다. `BIGINT` ID(스노플레이크, 트위터식 ID)나 원 단위 큰 금액을 JSON 숫자로 내보내면 클라이언트에서 값이 바뀐다.
- **실패 양상:** 상세 조회 ID가 마지막 자리에서 달라져 404 또는 남의 레코드 조회. 금액 합계 오차.
- **신호:** 🟢 Prisma `BigInt` 필드를 `JSON.stringify` 전에 `Number()`로 변환, `BIGSERIAL` + Express `res.json`. 🟡 외부 ID(카카오·디스코드 등 64비트 ID)를 `number` 타입으로 저장.
- **시나리오·수준:** C L1 이상
- **처방:** 코드: 64비트 ID·금액은 문자열로 직렬화, 클라이언트에서 `BigInt` 또는 문자열 유지. 인프라: 없음.
- **검증:** 2^53 + 1 값을 왕복시켜 값이 보존되는지 테스트.
- **비용 영향:** 중립.
- **출처:** https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number/MAX_SAFE_INTEGER ⚠️출처부적격

### C-023 타임스탬프 타입(timestamptz)
- **무엇/왜:** `timestamp with time zone`은 내부적으로 UTC로 저장되고 세션 시간대로 보여 준다. `timestamp without time zone`은 시간대 정보를 버려서 서버·DB·클라이언트 시간대가 다르면 9시간 어긋난 값이 섞인다.
- **실패 양상:** 서울(UTC+9) 서버와 UTC 컨테이너가 같은 테이블에 쓰면 주문 시각 역전, 자정 기준 일별 집계·쿠폰 만료가 9시간 틀어짐.
- **신호:** 🟢 SQL `TIMESTAMP`/`timestamp without time zone`, Prisma `DateTime`(PG에서 기본 `timestamp(3)`인지 마이그레이션 SQL 확인), `@db.Timestamptz`, Django `USE_TZ = False`. 🟢 `new Date().toLocaleString()`을 저장.
- **시나리오·수준:** C L1 이상
- **처방:** 코드: 저장은 timestamptz(UTC), 표시만 현지 시간대. 날짜 경계(일별 정산)는 업무 시간대를 명시해 계산. 인프라: 컨테이너·DB 시간대를 UTC로 고정(티어1·2 이미지 `TZ`).
- **검증:** 서로 다른 TZ 환경변수로 두 인스턴스를 띄워 같은 시각에 쓰고 값이 같은지 비교.
- **비용 영향:** 중립.
- **출처:** https://www.postgresql.org/docs/current/datatype-datetime.html ("All timezone-aware dates and times are stored internally in UTC")

### C-024 상태 컬럼과 허용 전이
- **무엇/왜:** 주문·결제·예약은 상태 머신이다(대기 → 결제됨 → 배송 → 완료, 취소). 아무 상태에서 아무 상태로 덮어쓰면 늦게 온 이벤트가 상태를 되돌린다.
- **실패 양상:** `paid` 이후 늦게 도착한 `pending` 웹훅이 상태를 되돌려 재결제 요청, 취소된 주문이 배송됨.
- **신호:** 🟢 `update({ data: { status: newStatus } })`에 현재 상태 조건 없음. 🟢 반대로 `WHERE status = 'pending'` 조건부 전이, enum 타입. 🟡 상태 필드가 자유 문자열.
- **시나리오·수준:** C L2 이상 (결제가 있으면 L3)
- **처방:** 코드: 전이표를 코드로 두고 `UPDATE … SET status = $new WHERE id = $id AND status IN ($allowed_from)`, 영향 행 0이면 무시·기록. enum + CHECK. 인프라: 없음.
- **검증:** 상태 이벤트를 무작위 순서로 재생하는 속성 기반 테스트에서 최종 상태가 항상 같고 금지 전이가 없는지 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.stripe.com/webhooks ("Stripe doesn't guarantee the delivery of events in the order that they're generated"), https://docs.stripe.com/payments/paymentintents/lifecycle (PaymentIntent 상태 목록) ⚠️출처부적격

### C-025 데이터 모델 선택(RDB vs 문서 DB vs BaaS)
- **무엇/왜:** 여러 엔터티를 함께 고치는 트랜잭션, 유니크·FK 제약, 집계 쿼리가 필요하면 관계형 DB가 기본값이다. 문서 DB·BaaS는 단일 문서 원자성과 규칙 기반 접근 제어가 강점이지만, 다문서 불변식은 앱이 책임진다.
- **실패 양상:** Firestore에 주문·재고·포인트를 나눠 저장하고 클라이언트에서 각각 쓰기 → 일부만 성공, 집계가 안 맞음.
- **신호:** 🟢 `firebase/firestore`, `mongodb`/`mongoose`, `@supabase/supabase-js`, `prisma` provider. 🟡 결제·재고 신호(C L3)가 문서 DB와 함께 있음.
- **시나리오·수준:** 모든 수준에서 판단, C L3에서 문서 DB면 경고
- **처방:** 코드: C L3인데 문서 DB면 핵심 쓰기를 서버 트랜잭션(Firestore `runTransaction`, Mongo 트랜잭션)으로 한정하거나 결제·재고만 관계형 DB로 분리. 인프라: 티어0 Supabase(Postgres)·티어1/2 매니지드 PostgreSQL. 교체 비용이 크므로 "이미 있는 인프라 존중" 원칙에 따라 기존 저장소 위 통제를 우선 처방.
- **검증:** 다문서 쓰기 중간 실패 주입 후 불변식 검사.
- **비용 영향:** 증가 가능(저장소 추가 시).
- **출처:** https://firebase.google.com/docs/firestore/manage-data/transactions (트랜잭션·배치 쓰기로 다문서 원자성), https://www.prisma.io/docs/orm/prisma-client/queries/transactions ("Prisma ORM does not support MongoDB transactions yet", Prisma 8)

### C-026 MongoDB 쓰기 확인 수준과 트랜잭션
- **무엇/왜:** MongoDB 5.0 이상의 암묵적 기본 write concern은 대부분 `{ w: "majority" }`지만, 아비터가 있는 구성 등에서는 `{ w: 1 }`이 된다. `w: 1`은 주 노드 교체 시 롤백될 수 있다. Prisma 8은 MongoDB 트랜잭션을 지원하지 않는다.
- **실패 양상:** 결제 완료 응답 후 프라이머리 교체 → 해당 쓰기 롤백, 사용자는 결제했는데 주문 없음.
- **신호:** 🟢 연결 문자열 `w=1`, `writeConcern: { w: 1 }`, `j: false`. 🟢 Prisma `provider = "mongodb"` + 다문서 쓰기. 🟢 `session.withTransaction`.
- **시나리오·수준:** C L2 이상
- **처방:** 코드: 중요한 쓰기는 `w: "majority"`, 다문서 쓰기는 드라이버 트랜잭션(Prisma 8이면 MongoDB 드라이버 직접 사용). 인프라: 아비터 없는 3노드 이상 레플리카셋(Atlas 기본).
- **검증:** 프라이머리 강제 스텝다운 중 쓰기를 넣고 확인 응답 받은 쓰기가 모두 남는지 확인.
- **비용 영향:** 중립~증가(majority 대기로 지연 증가).
- **출처:** https://www.mongodb.com/docs/manual/reference/write-concern/ ("Data can be rolled back if the primary steps down…"), https://www.prisma.io/docs/orm/prisma-client/queries/transactions

### C-027 DynamoDB 조건부 쓰기·트랜잭션·읽기 일관성
- **무엇/왜:** DynamoDB는 `ConditionExpression`으로 조건부 쓰기, `TransactWriteItems`로 최대 100개 작업의 전부-아니면-전무 쓰기를 한다. 기본 읽기는 최종 일관성이라 쓰기 직후 이전 값을 볼 수 있다.
- **실패 양상:** `BatchWriteItem`을 트랜잭션으로 착각해 일부만 성공. 트랜잭션 직후 일반 읽기로 확인하다 옛 값을 보고 재시도 → 중복.
- **신호:** 🟢 `BatchWriteItem` vs `TransactWriteItems`, `ConditionExpression` 유무, `ClientRequestToken`, `ConsistentRead: true`. 🟢 글로벌 테이블(리전 간 트랜잭션 미지원).
- **시나리오·수준:** C L2 이상
- **처방:** 코드: 원자성이 필요하면 `TransactWriteItems` + `ClientRequestToken`(멱등, 10분 창), 쓰기 후 확인은 강한 일관성 읽기. 인프라: 글로벌 테이블에서는 결제·재고 쓰기를 단일 리전으로.
- **검증:** 같은 토큰 재전송 시 변경 없음, 조건 실패 시 전체 취소 확인.
- **비용 영향:** 증가(트랜잭션은 항목당 읽기/쓰기 2회 소비).
- **출처:** https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/transaction-apis.html (100개 작업, 4MB, 토큰 10분, 2배 용량 소비, 리전 내 ACID)

### C-028 다중 인스턴스에서 SQLite 파일 DB
- **무엇/왜:** SQLite 파일은 프로세스가 붙은 디스크에 있다. 인스턴스가 둘 이상이거나 컨테이너가 교체되면 각자 다른 파일에 쓰게 되어 데이터가 갈라지거나 사라진다.
- **실패 양상:** 오토스케일된 두 인스턴스가 각자 주문을 받아 서로의 데이터를 못 봄. 재배포마다 데이터 초기화.
- **신호:** 🟢 Prisma `provider = "sqlite"`, `file:./dev.db`, Django `ENGINE: django.db.backends.sqlite3`, `better-sqlite3`. 탐지기 사실 `db.sqlite_file`. 🟢 Turso/libSQL·LiteFS 등 복제 계층이 있으면 예외.
- **시나리오·수준:** C L1 이상 (영속 사용자 데이터가 있으면)
- **처방:** 코드: 프로덕션은 매니지드 PostgreSQL로 전환(Prisma provider 교체 + 마이그레이션). 인프라: 티어0 Supabase/Neon, 티어1 Cloud SQL/RDS, 티어2 RDS/Cloud SQL(클러스터 안 DB 비권장). 단일 인스턴스 고정 + 영구 볼륨은 C L1·T L0일 때만 허용.
- **검증:** 인스턴스 2개 + 재배포 후 데이터 연속성 확인.
- **비용 영향:** 증가(매니지드 DB 월 비용).
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### C-029 JSON 컬럼 안에 숨은 불변식
- **무엇/왜:** 금액·수량·상태를 `jsonb`/`Json` 필드 안에 넣으면 CHECK·FK·유니크·원자적 증감을 걸기 어렵고, 전체 문서를 읽고 고쳐 쓰는 lost update(C-002)가 기본 동작이 된다.
- **실패 양상:** 장바구니·포인트 내역을 JSON 배열로 두고 동시 추가 시 항목 유실.
- **신호:** 🟢 Prisma `Json` 필드에 `items`, `balance`, `points`, `inventory` 같은 키를 쓰고 `update({ data: { meta: {...meta, …} } })`. 🟢 Firestore 문서의 배열 필드 전체 덮어쓰기.
- **시나리오·수준:** C L2 이상
- **처방:** 코드: 불변식이 걸린 값은 정규 컬럼·하위 테이블로. 유지해야 하면 `jsonb_set`을 쓰는 원자적 UPDATE 또는 버전 잠금. 인프라: 없음.
- **검증:** 동시 수정 테스트에서 항목 수 보존 확인.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### C-030 비정규화 카운터·집계의 드리프트
- **무엇/왜:** `comment_count`, `like_count`, `order_total` 같은 사본 값은 원본(댓글 행, 주문 항목)과 별도로 갱신되므로 버그·실패·재시도로 어긋난다.
- **실패 양상:** 댓글 수 표시와 실제 개수 불일치, 주문 총액과 항목 합 불일치(결제 금액 오류로 이어짐).
- **신호:** 🟢 `*_count`/`total*` 컬럼 + 별도 increment 호출. 🟡 트리거·재계산 작업 유무.
- **시나리오·수준:** C L1(표시용) / C L3(금액 합계)
- **처방:** 코드: 금액 합계는 저장하지 말고 계산하거나 같은 트랜잭션에서 갱신 + 정기 재계산 작업으로 대사. 표시용 카운터는 근사 허용. 인프라: 재계산 크론(C-091 참고).
- **검증:** 재계산 쿼리와 저장 값의 차이 = 0 확인을 CI·운영 점검에 포함.
- **비용 영향:** 소폭 증가(재계산 작업).
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### C-031 다중 테넌트 키의 무결성
- **무엇/왜:** B2B SaaS에서 모든 행에 `tenant_id`(org_id)가 있는데 관계·유니크 제약에 테넌트가 빠지면, 다른 조직의 행을 참조하거나 조직 간에 이름 충돌이 생긴다.
- **실패 양상:** A사 프로젝트에 B사 사용자가 연결됨, 조직마다 같아도 되는 슬러그가 전역 유니크라 가입 실패.
- **신호:** 🟢 `organizationId|tenantId|workspaceId` 필드 존재 + `@@unique([slug])`처럼 테넌트 없는 유니크, 쿼리 `where`에 테넌트 조건 누락. 🟡 RLS 정책으로 테넌트 격리(C-096).
- **시나리오·수준:** C L2 이상 (B2B 신호가 있으면)
- **처방:** 코드: 유니크·FK에 테넌트 포함(`@@unique([orgId, slug])`, 복합 FK), 쿼리 레이어에서 테넌트 강제 또는 RLS. 인프라: 없음.
- **검증:** 다른 테넌트 ID로 참조를 시도해 거부되는지 테스트.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인). RLS로 행 단위 격리는 https://www.postgresql.org/docs/current/ddl-rowsecurity.html ⚠️근거없음

---

## C. API 멱등성·재시도

### C-032 쓰기 API의 멱등성 키
- **무엇/왜:** 모바일 네트워크 타임아웃, 게이트웨이 재시도, 사용자의 새로고침은 같은 POST를 다시 보낸다. 클라이언트가 만든 요청 ID(멱등성 키)를 서버가 기억해 두면 재시도에 첫 결과를 돌려줄 수 있다.
- **실패 양상:** 주문·송금·글쓰기가 두 번 처리됨. 응답을 못 받은 클라이언트가 "실패"로 알고 다시 시도해 이중 청구.
- **신호:** 🟢 `Idempotency-Key`/`X-Request-Id` 헤더 읽기, 멱등 키 저장(`SET key NX EX`, `idempotency_keys` 테이블). SWA `routes.py`가 `Idempotency-Key`(UUID)를 필수로 받고 `queue.py:33`에서 `redis.set(idem_key, post_id, nx=True, ex=…)`. 🟡 돈·재고를 바꾸는 POST 라우트에 키 처리가 없음. 탐지기 사실 후보 `api.idempotency_key`.
- **시나리오·수준:** C L2 이상 (클라이언트 재시도 경로가 있으면 L2 판정 신호)
- **처방:** 코드: 사용자 범위 키(`user_id + key`)로 저장, 첫 처리 결과(상태 코드 + 본문)를 저장해 재생. 인프라: 키 저장소 — 티어0 Supabase 테이블 또는 Upstash Redis, 티어1/2 같은 PostgreSQL 테이블(유니크 제약) 또는 매니지드 Redis(퇴출 정책 C-081 주의).
- **검증:** 같은 키로 같은 요청을 동시에·순차로 10번 보내 처리 1회, 응답 동일 확인.
- **비용 영향:** 중립~소폭 증가(키 저장소).
- **출처:** https://docs.stripe.com/api/idempotent_requests (결과 저장 후 재생), https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/ (caller-provided client request identifier), https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/ (헤더 표준화 초안, 2026-10-01 기준 만료된 draft-07)

### C-033 같은 멱등 키의 동시 요청
- **무엇/왜:** 키 저장을 "조회 → 없으면 처리 → 결과 저장"으로 하면 동시에 도착한 두 재시도가 둘 다 처리한다. 키를 먼저 원자적으로 선점(진행 중 상태)하고 처리해야 한다.
- **실패 양상:** 더블 탭으로 같은 키 요청 두 개가 몇 ms 간격으로 들어와 둘 다 결제.
- **신호:** 🟢 `GET key` 후 `SET key`(비원자), 테이블 조회 후 INSERT. 🟢 안전 패턴: `SET … NX`, `INSERT … ON CONFLICT DO NOTHING RETURNING`, 상태 `INPROGRESS`.
- **시나리오·수준:** C L2 이상
- **처방:** 코드: 원자적 선점 + 진행 중이면 409(또는 대기 후 결과 반환), 처리 실패 시 선점 해제 또는 만료 시간. 인프라: 없음.
- **검증:** 같은 키 요청을 동시에 50개 보내 처리 1회 + 나머지는 409 또는 동일 결과인지 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/powertools/typescript/latest/features/idempotency/ (INPROGRESS 상태, `IdempotencyAlreadyInProgressError`), https://docs.stripe.com/api/idempotent_requests ("the request conflicts with another request that's executing concurrently")

### C-034 같은 키, 다른 요청 본문
- **무엇/왜:** 클라이언트 버그로 다른 주문에 같은 키를 재사용하면, 서버가 이전 결과를 돌려줘 새 주문이 조용히 무시된다. 키와 함께 요청 지문(본문 해시)을 저장해 다르면 거부해야 한다.
- **실패 양상:** 사용자는 B 상품을 샀다고 생각하지만 서버는 A 주문 결과를 반환, B는 처리되지 않음.
- **신호:** 🟡 키 저장 시 요청 해시를 저장·비교하는 코드 없음.
- **시나리오·수준:** C L2 이상
- **처방:** 코드: 키 레코드에 요청 해시 저장, 불일치 시 422/409. 인프라: 없음.
- **검증:** 같은 키 + 다른 본문 요청이 거부되는지 테스트.
- **비용 영향:** 중립.
- **출처:** https://docs.stripe.com/api/idempotent_requests ("compares incoming parameters to those of the original request and errors if they're not the same"), https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/ (parameter mismatch)

### C-035 멱등 키 보존 기간과 재시도 창
- **무엇/왜:** 키를 너무 짧게 보관하면 늦은 재시도가 새 요청으로 처리되고, 무한 보관하면 저장소가 계속 커진다. 보존 기간은 "클라이언트·큐가 재시도할 수 있는 최대 시간"보다 길어야 한다.
- **실패 양상:** 오프라인 큐가 30분 뒤 재전송했는데 키 TTL이 10분이라 중복 생성.
- **신호:** 🟢 키 저장의 `ex=`/`EX`/`expiresAt` 값. SWA는 `idempotency_ttl_seconds = 600`. 비교 기준: Stripe 키는 24시간 이후 정리 가능, 토스페이먼츠 15일, DynamoDB 트랜잭션 토큰 10분, Powertools 기본 1시간.
- **시나리오·수준:** C L2 이상
- **처방:** 코드: TTL ≥ 최대 재시도 창(클라이언트 재시도 + 큐 재전송 + 웹훅 재시도 기간 중 큰 값). 영구 중복 방지가 필요한 곳(결제 ID)은 TTL 대신 유니크 제약. 인프라: 만료 정리 작업 또는 Redis TTL.
- **검증:** TTL 직전·직후 재전송 시나리오 테스트.
- **비용 영향:** 소폭 증가(보관 기간에 비례한 저장 공간).
- **출처:** https://docs.stripe.com/api/idempotent_requests ("at least 24 hours old"), https://docs.tosspayments.com/reference/using-api/idempotency-key ("처음 요청에 사용한 날부터 15일간 유효"), https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/transaction-apis.html (10분), https://docs.aws.amazon.com/powertools/typescript/latest/features/idempotency/ (기본 3600초)

### C-036 클라이언트 재시도 정책과 키 재사용
- **무엇/왜:** 서버가 멱등 키를 지원해도 클라이언트가 재시도할 때마다 새 키를 만들면 소용없다. 반대로 "사용자가 실패를 보고 다시 누름"은 의도적으로 새 키여야 할 수도 있다(SWA rulings R9: 실패한 글의 재시도는 새 키).
- **실패 양상:** fetch 래퍼가 자동 재시도마다 `crypto.randomUUID()`를 새로 호출 → 서버는 매번 새 요청으로 처리.
- **신호:** 🟢 키 생성 위치가 재시도 루프 안. 🟢 `axios-retry`, `ky` retry, TanStack Query `retry` 옵션이 변경(mutation)에 켜짐. 🟡 `Retry-After` 존중 여부.
- **시나리오·수준:** C L2 이상
- **처방:** 코드: 키는 "사용자 의도 1회"당 한 번 생성해 자동 재시도에서 재사용. 서버가 503 + `Retry-After`를 주면 그 이후에 같은 키로 재시도. 인프라: 없음.
- **검증:** 네트워크 단절을 주입한 E2E에서 자동 재시도가 같은 키를 쓰는지 요청 로그로 확인.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인). 키 재사용 원칙은 https://docs.stripe.com/api/idempotent_requests ⚠️출처부적격 ⚠️근거없음

### C-037 폼 중복 제출·더블 클릭
- **무엇/왜:** 버튼 비활성화는 UX일 뿐 보장이 아니다(새로고침, 뒤로 가기 후 재제출, 탭 두 개). 서버 측 멱등성(C-032) 또는 자연 키 유니크(C-017)가 필요하다.
- **실패 양상:** 같은 글이 두 번 등록, 같은 예약이 두 번 잡힘.
- **신호:** 🟡 프런트에 `disabled={isSubmitting}`만 있고 서버에 키·유니크가 없음. 🟡 Server Action/Route Handler POST가 바로 `create`.
- **시나리오·수준:** C L1 이상
- **처방:** 코드: 폼 렌더 시 키 발급(숨은 필드) → 서버에서 C-032 처리, 또는 자연 키 유니크. 인프라: 없음.
- **검증:** 같은 폼을 연속 두 번 제출하는 E2E.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### C-038 외부 결제·발송 API 호출에 멱등 키 전달
- **무엇/왜:** 우리 서버가 Stripe·토스페이먼츠·메일 API를 부를 때도 타임아웃 후 재시도하면 외부에서 두 번 실행될 수 있다. 공급자가 멱등 키를 지원하면 반드시 넘긴다.
- **실패 양상:** 결제 승인 요청 타임아웃 → 재시도 → 이중 승인. 환불 API 재시도로 이중 환불 시도.
- **신호:** 🟢 `stripe.paymentIntents.create(…, { idempotencyKey })`, 토스 `Idempotency-Key` 헤더 유무. 🟢 결제 SDK 호출이 재시도 래퍼 안에 있는데 키가 없음.
- **시나리오·수준:** C L3
- **처방:** 코드: 주문 ID 기반 결정적 키(예: `order:{id}:confirm`)를 넘긴다. 키에 개인정보를 넣지 않는다. 인프라: 없음.
- **검증:** 공급자 테스트 모드에서 같은 키로 두 번 호출해 같은 객체가 반환되는지 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.stripe.com/api/idempotent_requests ("All POST requests accept idempotency keys", 최대 255자, 민감정보 사용 금지), https://docs.tosspayments.com/reference/using-api/idempotency-key ("모든 POST 메서드 API", 최대 300자) ⚠️출처부적격

---

## D. 결제·금액

### C-039 금액에 부동소수점 금지
- **무엇/왜:** `float`/`double`은 0.1 같은 값을 정확히 표현하지 못해 합계·할인·부가세 계산에서 오차가 쌓인다. 금액은 정수 최소 단위(원, 센트) 또는 `numeric`으로 저장·계산한다.
- **실패 양상:** 결제 금액과 주문 합계가 1원 차이로 검증 실패, 정산 대사 불일치, 환불 금액 초과.
- **신호:** 🟢 Prisma `price Float`(PostgreSQL `double precision`으로 매핑), SQL `REAL`/`DOUBLE PRECISION`/`money`, Django `FloatField`가 `price|amount|total|balance` 이름에. JS에서 `price * 1.1`, `toFixed(2)` 결과를 저장. 🟢 안전 패턴: `Int`(최소 단위), `Decimal`/`numeric`, `decimal.js`/`big.js`, Python `Decimal`.
- **시나리오·수준:** C L1 이상 (금액이 있으면 L3 판정과 함께 필수)
- **처방:** 코드: 정수 최소 단위 또는 `numeric(p,s)`. 반올림 규칙(은행가 반올림 등)을 한 곳에 정의. PostgreSQL `money` 타입은 `lc_monetary` 로캘에 따라 덤프·복원이 깨질 수 있어 피한다. 인프라: 없음.
- **검증:** 0.1 + 0.2 계열 경계값과 대량 항목 합계 테스트, 스키마 정적 검사로 금액 컬럼 타입 확인.
- **비용 영향:** 중립.
- **출처:** https://www.postgresql.org/docs/current/datatype-numeric.html ("especially recommended for storing monetary amounts"), https://www.postgresql.org/docs/current/datatype-money.html ("Floating point numbers should not be used to handle money", 로캘 의존), https://www.prisma.io/docs/orm/reference/prisma-schema-reference (`Float` → `double precision`, `Decimal` → `decimal(65,30)`)

### C-040 통화와 최소 단위(zero-decimal 통화)
- **무엇/왜:** 결제 API는 금액을 통화의 최소 단위 정수로 받는다. USD 10.99는 `1099`지만 KRW·JPY는 소수점이 없는 통화라 500원은 `500`이다. 통화 코드 없이 숫자만 저장하면 다통화 확장 시 해석이 모호해진다.
- **실패 양상:** 원화 결제에 100을 곱해 100배 청구, 또는 달러를 원처럼 처리해 1/100 청구.
- **신호:** 🟢 `amount: price * 100`이 통화와 무관하게 적용, `currency` 컬럼 부재, Stripe `currency: 'krw'` + `* 100`. 🟡 i18n 통화 표시만 있고 저장은 숫자만.
- **시나리오·수준:** C L3 (결제가 있으면)
- **처방:** 코드: (amount_minor, currency) 쌍으로 저장, 통화별 소수 자릿수 표를 한 곳에. 인프라: 없음.
- **검증:** KRW·USD 각각 테스트 모드 결제 금액이 의도와 같은지 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.stripe.com/currencies (minor unit, zero-decimal 통화, 최소 결제 금액 50 KRW) ⚠️출처부적격

### C-041 서버 측 금액 확정과 검증
- **무엇/왜:** 클라이언트가 보낸 금액·가격을 그대로 결제 요청에 쓰면 조작된 금액으로 결제가 승인된다. 금액은 서버의 주문 기록에서 계산하고, 결제 승인 전 PG가 돌려준 금액과 비교한다.
- **실패 양상:** 개발자 도구로 금액을 100원으로 바꿔 고가 상품 구매.
- **신호:** 🟢 `req.body.amount`/`searchParams.get('amount')`를 그대로 `confirm`/`paymentIntents.create`에 전달. 🟢 토스 성공 리다이렉트 처리에서 쿼리 `amount`와 저장된 주문 금액 비교 코드 유무.
- **시나리오·수준:** C L3
- **처방:** 코드: 주문 생성 시 서버에서 금액 계산·저장(`orderId` 발급) → 승인 단계에서 저장 금액과 PG 금액 일치 확인 후 승인. 인프라: 없음.
- **검증:** 조작된 금액으로 승인 요청 시 거부되는지 테스트.
- **비용 영향:** 중립.
- **출처:** https://docs.tosspayments.com/guides/v2/payment-widget/integration ("쿼리 파라미터의 amount 값과 setAmount()의 amount 파라미터의 값이 같은지 반드시 확인하세요") ⚠️출처부적격

### C-042 결제 승인 시한과 대기 주문
- **무엇/왜:** 결제 인증 후 서버 승인까지 시한이 있다(토스페이먼츠: 인증 후 10분 안에 승인, 요청 후 30분이 지나면 `EXPIRED`). 승인을 큐 뒤로 미루거나 승인 실패를 방치하면 재고만 묶이고 결제는 사라진다.
- **실패 양상:** 트래픽 폭증으로 승인 API 호출이 10분 넘게 밀려 결제 데이터 유실, 재고는 "결제 대기"로 묶여 판매 불가.
- **신호:** 🟢 토스 `confirm` 호출이 큐 워커 안에 있음, 대기 주문 만료 처리(`expiresAt`, 정리 크론) 부재. 🟡 재고 선점(hold) 로직 유무.
- **시나리오·수준:** C L3
- **처방:** 코드: 승인은 리다이렉트 처리 경로에서 동기로, 대기 주문에 만료 시각 + 만료 시 재고 반환 작업. 인프라: 만료 처리 크론(C-091 중복 실행 주의).
- **검증:** 승인을 지연시켜 만료 후 재고가 복구되는지, 결제 상태 조회와 로컬 상태가 일치하는지 확인.
- **비용 영향:** 소폭 증가(정리 작업).
- **출처:** https://docs.tosspayments.com/guides/v2/payment-widget/integration ("결제 요청이 완료된 이후 10분 이내에 결제를 승인해야 됩니다"), https://docs.tosspayments.com/reference (`EXPIRED`: 유효 시간 30분 경과) ⚠️출처부적격

### C-043 결제 레코드 모델(주문 1 : 결제 시도 N, 외부 ID 유니크)
- **무엇/왜:** 한 주문에 결제 실패·재시도가 여러 번 생긴다. 주문 행에 결제 정보를 덮어쓰면 이력이 사라지고, 외부 결제 ID(`paymentKey`, `pi_…`)가 유니크가 아니면 같은 결제를 두 주문에 연결할 수 있다.
- **실패 양상:** 실패한 시도의 웹훅이 성공 상태를 덮어씀, 같은 `paymentKey`로 두 주문이 "결제 완료".
- **신호:** 🟢 `Order` 모델에 `paymentKey`/`paymentIntentId` 컬럼이 있고 `@unique` 없음, `Payment` 별도 테이블 부재.
- **시나리오·수준:** C L3
- **처방:** 코드: `payments(id, order_id, provider, provider_payment_id UNIQUE, status, amount, currency, created_at)`. 주문 상태는 성공한 결제가 있을 때만 전이(C-024). 인프라: 없음.
- **검증:** 같은 외부 ID 두 번 저장 시 거부, 실패 시도 후 성공 시도 시나리오에서 이력 보존 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.stripe.com/payments/paymentintents/lifecycle (실패 시 `requires_payment_method`로 돌아가 재시도 가능), https://www.postgresql.org/docs/current/ddl-constraints.html

### C-044 이행(fulfillment)을 정확히 한 번
- **무엇/왜:** 결제 후 상품 지급·권한 부여·배송 요청은 웹훅과 성공 페이지 양쪽에서, 그것도 동시에 호출될 수 있다. 이행 함수는 같은 결제로 여러 번 불려도 한 번만 효과를 내야 한다.
- **실패 양상:** 크레딧 2배 지급, 배송 2건 생성, 확인 메일 여러 통.
- **신호:** 🟢 `checkout.session.completed` 핸들러와 `success_url` 페이지가 같은 지급 함수를 호출, 지급 전 "이미 이행됨" 확인이 조건부 UPDATE가 아님. 🟢 `fulfilled_at` 컬럼 유무.
- **시나리오·수준:** C L3
- **처방:** 코드: `UPDATE orders SET fulfilled_at = now() WHERE id = $1 AND fulfilled_at IS NULL`의 영향 행 수로 이행 권한을 얻은 쪽만 실행(같은 트랜잭션에서 지급 기록). 외부 부수효과는 아웃박스(C-073). 인프라: 없음.
- **검증:** 같은 세션 ID로 웹훅과 성공 페이지를 동시에 50회 호출해 지급 1회 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.stripe.com/checkout/fulfillment ("your fulfill_checkout function might be called multiple times, possibly concurrently, for the same Checkout Session") ⚠️출처부적격

### C-045 리다이렉트만으로 결제 완료 처리 금지
- **무엇/왜:** 성공 페이지 리다이렉트는 사용자가 결제 후 창을 닫거나 네트워크가 끊기면 오지 않는다. 결제 확정의 원천은 서버 간 통신(웹훅 또는 서버의 승인 API 응답)이어야 한다.
- **실패 양상:** 결제는 됐는데 주문은 영원히 "결제 대기", 고객 문의·수동 처리.
- **신호:** 🟢 결제 성공 처리가 `success` 페이지(클라이언트 컴포넌트, `useEffect`)에만 있고 웹훅 라우트가 없음. 🟢 Stripe Checkout 사용 + `/api/webhook` 부재.
- **시나리오·수준:** C L3
- **처방:** 코드: 웹훅 핸들러를 주 경로로, 리다이렉트는 빠른 표시용 보조 경로(둘 다 C-044의 멱등 함수 호출). 인프라: 웹훅을 받을 공개 HTTPS 엔드포인트(모든 티어).
- **검증:** 결제 후 리다이렉트를 차단한 시나리오에서 주문이 완료되는지 확인(Stripe CLI `stripe trigger`).
- **비용 영향:** 중립.
- **출처:** https://docs.stripe.com/checkout/fulfillment ("You can't rely on triggering fulfillment only from your checkout landing page") ⚠️출처부적격

### C-046 비동기 결제수단의 중간 상태
- **무엇/왜:** 계좌이체·가상계좌·은행 자동이체는 "요청 완료"와 "입금 확인"이 다르다. Stripe는 `processing` 후 `async_payment_succeeded`, 토스는 `WAITING_FOR_DEPOSIT` 후 입금 콜백이 온다.
- **실패 양상:** 가상계좌 발급만으로 상품 지급(미입금 손실), 입금 웹훅을 처리하지 않아 입금했는데 주문 미완료.
- **신호:** 🟢 `checkout.session.completed`에서 `payment_status` 확인 없이 지급, `async_payment_succeeded`/`async_payment_failed` 미처리, 토스 `DEPOSIT_CALLBACK`/`WAITING_FOR_DEPOSIT` 미처리. 🟡 결제수단에 가상계좌·계좌이체가 켜져 있는지 설정 확인.
- **시나리오·수준:** C L3
- **처방:** 코드: 결제 상태가 확정(`paid`/`DONE`)일 때만 이행, 대기 상태 만료 처리. 인프라: 없음.
- **검증:** 테스트 모드 지연 결제수단으로 대기 → 성공/실패 각각 시나리오.
- **비용 영향:** 중립.
- **출처:** https://docs.stripe.com/checkout/fulfillment (`payment_status`, `checkout.session.async_payment_succeeded`), https://docs.stripe.com/payments/paymentintents/lifecycle (`processing`), https://docs.tosspayments.com/guides/v2/webhook (`DEPOSIT_CALLBACK` 이벤트), https://docs.tosspayments.com/reference (`WAITING_FOR_DEPOSIT`) ⚠️출처부적격

### C-047 환불·취소의 중복과 한도
- **무엇/왜:** 환불 버튼 연타·재시도·관리자 동시 처리로 같은 환불이 두 번 요청될 수 있다. 부분 취소가 있으면 "누적 환불 ≤ 결제 금액"을 로컬에서도 지켜야 한다.
- **실패 양상:** 이중 환불 시도, 로컬 기록상 환불 합계가 결제 금액 초과, PG와 로컬 상태 불일치.
- **신호:** 🟢 `stripe.refunds.create`/토스 `/v1/payments/{paymentKey}/cancel` 호출에 멱등 키 없음, `cancelAmount` 사용 + 누적 환불 검사 없음.
- **시나리오·수준:** C L3
- **처방:** 코드: 환불 요청 ID 기반 멱등 키, 로컬 `refunds` 테이블 + 누적 합계 조건부 INSERT(잠금 또는 CHECK). 인프라: 없음.
- **검증:** 같은 환불을 동시에 10회 요청해 PG 호출 1회, 부분 환불 누적 초과 요청 거부 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.tosspayments.com/reference (취소 API `cancelAmount`, 멱등키로 중복 취소 방지), https://docs.stripe.com/refunds ("you can't refund a total greater than the original charge amount") ⚠️출처부적격

### C-048 환불 실패·지연 상태 처리
- **무엇/왜:** 환불은 즉시 끝나지 않는다. Stripe 환불은 `pending`·`requires_action`·`failed`·`canceled`가 있고, 실패는 최대 30일 뒤에 알려질 수 있다.
- **실패 양상:** 환불 요청 즉시 "환불 완료"로 표시했는데 나중에 실패해 고객은 돈을 못 받고 시스템은 완료로 기록.
- **신호:** 🟢 `refund.failed`/`refund.updated` 이벤트 미처리, 환불 생성 응답만 보고 상태를 `refunded`로 확정.
- **시나리오·수준:** C L3
- **처방:** 코드: 환불 상태를 별도 상태 머신으로, 실패 이벤트 시 알림·대체 처리. 인프라: 없음.
- **검증:** 테스트 모드 실패 환불 시나리오 재생.
- **비용 영향:** 중립.
- **출처:** https://docs.stripe.com/refunds ("This process can take up to 30 days", `refund.failed`) ⚠️출처부적격

### C-049 결제 대사(reconciliation)
- **무엇/왜:** 웹훅 유실·코드 버그·수동 조작으로 PG 기록과 로컬 DB는 언젠가 어긋난다. 정기적으로 PG의 거래 목록(또는 정산 보고서)과 로컬 결제 테이블을 맞춰 보는 작업이 마지막 안전망이다.
- **실패 양상:** 결제는 됐는데 주문 미완료(고객 불만), 로컬엔 완료인데 PG엔 취소(매출 과대), 정산 금액 차이를 몇 달 뒤 발견.
- **신호:** 🔴 대사 작업은 대개 코드에 없음 → C L3면 "미충족"으로 가정. 🟢 있으면 `paymentIntents.list`/`balanceTransactions.list`, 토스 결제 조회 API를 도는 크론, Stripe Reporting API.
- **시나리오·수준:** C L3
- **처방:** 코드: 매일(또는 매시) 최근 N시간 결제를 PG에서 조회해 로컬과 비교, 불일치 시 자동 보정(멱등 이행 함수 재호출) + 알림. 인프라: 크론(티어0 Vercel Cron, 티어1 Cloud Scheduler/EventBridge Scheduler, 티어2 CronJob `concurrencyPolicy: Forbid`).
- **검증:** 웹훅을 일부러 버린 뒤 대사 작업이 불일치를 찾아 복구하는지 확인.
- **비용 영향:** 소폭 증가(크론 실행 + API 호출).
- **출처:** https://docs.stripe.com/reports/payout-reconciliation ("match the payouts you receive in your bank account with the batches of payments"), https://docs.stripe.com/webhooks ("You can also use the API to retrieve any missing objects") ⚠️출처부적격

### C-050 분쟁과 환불이 겹치는 이중 반환
- **무엇/왜:** 고객이 카드사에 분쟁(차지백)을 건 상태에서 판매자가 환불까지 하면 고객이 두 번 돈을 받을 수 있다. 은행 자동이체 계열에서 특히 위험하다.
- **실패 양상:** 같은 거래에 환불과 차지백이 모두 처리되어 손실 2배.
- **신호:** 🟢 `charge.dispute.created` 미처리, 환불 전 분쟁 여부 확인 없음.
- **시나리오·수준:** C L3
- **처방:** 코드: 분쟁 이벤트 수신 시 주문에 표시하고 환불 경로 차단, 분쟁 대응 절차로 넘김. 인프라: 없음.
- **검증:** 테스트 모드 분쟁 이벤트 후 환불 요청이 차단되는지 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.stripe.com/refunds ("there's a risk of double refund", `charge_for_pending_refund_disputed`) ⚠️출처부적격

### C-051 원장(ledger)은 덧붙이기만
- **무엇/왜:** 잔액·포인트·크레딧을 숫자 하나로만 관리하면 왜 그 값이 됐는지 설명할 수 없고, 잘못된 갱신을 되돌릴 근거도 없다. 변동 내역(원장)을 덧붙이기만 하고 잔액은 그 합(또는 같은 트랜잭션에서 갱신하는 캐시)으로 둔다.
- **실패 양상:** 포인트가 사라졌다는 문의에 근거 없음, 버그 복구 시 어디까지 되돌릴지 모름.
- **신호:** 🟢 `balance`/`points` 컬럼만 있고 `*_transactions`/`ledger` 테이블 없음, 원장 테이블에 UPDATE/DELETE 코드 존재.
- **시나리오·수준:** C L3 (잔액·포인트·크레딧이 있으면)
- **처방:** 코드: 원장 INSERT + 잔액 갱신을 한 트랜잭션에, 원장 행은 수정 대신 상쇄 항목 추가, 각 항목에 원인 ID(주문·결제·이벤트) 유니크로 중복 적립 방지. 인프라: 없음(원장 테이블 권한에서 UPDATE/DELETE 회수는 선택).
- **검증:** 잔액 = 원장 합 불변식 쿼리를 정기 실행.
- **비용 영향:** 소폭 증가(저장 공간).
- **출처:** 일반 원칙(출처 미확인). 감사·이벤트 기록의 이점은 https://microservices.io/patterns/data/event-sourcing.html 참고 ⚠️출처부적격 ⚠️근거없음

### C-052 쿠폰·포인트·체험판의 1회 사용
- **무엇/왜:** "1인 1회" 쿠폰, 첫 구매 할인, 무료 체험은 동시 요청과 재시도로 여러 번 쓰이기 쉽다. 사용 기록에 유니크(또는 부분 유니크) 제약을 걸어 DB가 막게 한다.
- **실패 양상:** 동시 요청 두 개로 쿠폰 2회 적용, 탈퇴 후 재가입으로 체험판 반복.
- **신호:** 🟢 `coupon_redemptions`/`usedAt` 검사가 SELECT 후 INSERT, `(user_id, coupon_id)` 유니크 부재.
- **시나리오·수준:** C L2 이상
- **처방:** 코드: `UNIQUE (user_id, coupon_id)` 또는 "사용 완료인 행만" 유니크하게 부분 유니크 인덱스(`… WHERE status = 'used'`), 선착순 수량은 C-003. 인프라: 없음.
- **검증:** 같은 쿠폰 동시 사용 50회 → 성공 1회.
- **비용 영향:** 중립.
- **출처:** https://www.postgresql.org/docs/current/indexes-partial.html (부분 유니크 인덱스 예시 `… WHERE success`)

---

## E. 웹훅 수신

### C-053 웹훅 이벤트 중복 제거
- **무엇/왜:** 웹훅은 같은 이벤트를 두 번 이상 보낼 수 있다. 처리한 이벤트 ID를 기록하고 이미 처리한 것은 건너뛴다. Stripe는 드물게 **서로 다른 이벤트 객체 두 개**로 같은 변화를 보내므로, 객체 ID + 이벤트 타입으로도 중복을 판단해야 한다.
- **실패 양상:** 같은 `payment_intent.succeeded`가 두 번 처리되어 크레딧 2배 지급, 메일 2통.
- **신호:** 🟢 웹훅 라우트(`/api/webhook`, `stripe.webhooks.constructEvent`, `Webhook.construct_event`)에 `event.id` 저장·유니크 검사 없음. 탐지기 사실 `webhook.no_dedupe`. 🟢 안전 패턴: `processed_events(event_id PRIMARY KEY)` INSERT ON CONFLICT DO NOTHING을 처리와 같은 트랜잭션에.
- **시나리오·수준:** C L2 이상 (웹훅 수신이 L2 판정 신호, 결제 웹훅이면 L3)
- **처방:** 코드: 이벤트 ID 기록과 비즈니스 갱신을 같은 트랜잭션(멱등 소비자 패턴), 그리고 처리 자체를 멱등하게(C-044, C-024). 인프라: 없음.
- **검증:** Stripe CLI `stripe events resend`로 같은 이벤트를 재전송해 상태 변화가 한 번뿐인지 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.stripe.com/webhooks ("Webhook endpoints might occasionally receive the same event more than once… In some cases, two separate Event objects are generated"), https://microservices.io/patterns/communication-style/idempotent-consumer.html ⚠️출처부적격

### C-054 웹훅 순서 비보장
- **무엇/왜:** 웹훅은 발생 순서대로 오지 않는다. `invoice.paid`가 `invoice.created`보다 먼저 올 수 있고, 이벤트의 `created`는 초 단위라 같은 값이 겹친다. 순서에 기대면 상태가 거꾸로 간다.
- **실패 양상:** `customer.subscription.updated(active)` 뒤에 늦게 온 `(incomplete)`가 상태를 덮어 유료 사용자 차단. 아직 없는 레코드에 대한 이벤트가 와서 처리 실패.
- **신호:** 🟢 웹훅 핸들러가 이벤트 페이로드의 상태를 무조건 덮어씀, `event.created` 비교로 순서 판단. 🟡 이벤트 수신 시 API로 최신 객체를 다시 조회하는지.
- **시나리오·수준:** C L2 이상
- **처방:** 코드: (1) 허용 전이만 적용(C-024), (2) 이벤트를 "무언가 바뀌었다는 신호"로 보고 API에서 최신 객체를 조회해 동기화, (3) 선행 레코드가 없으면 API로 가져와 생성. 인프라: 없음.
- **검증:** 같은 시나리오의 이벤트를 무작위 순서로 재생하는 테스트에서 최종 상태가 PG 객체와 같은지 확인.
- **비용 영향:** 소폭 증가(조회 API 호출).
- **출처:** https://docs.stripe.com/webhooks ("Stripe doesn't guarantee the delivery of events in the order… Don't use created to determine event order") ⚠️출처부적격

### C-055 웹훅은 빨리 2xx, 처리는 뒤에서
- **무엇/왜:** 웹훅 발신자는 짧은 시간 안에 2xx를 기대한다(토스페이먼츠 10초). 무거운 처리를 동기로 하면 타임아웃 → 재전송 → 중복 처리가 연쇄된다. 월초 구독 갱신처럼 웹훅이 몰리는 때 특히 위험하다.
- **실패 양상:** 처리 중 타임아웃 판정 → 같은 이벤트 재전송 → 처리 2회(C-053 없으면 이중 반영), 엔드포인트 비활성화.
- **신호:** 🟢 웹훅 핸들러 안에서 메일 발송·이미지 처리·외부 API 다중 호출. 🟡 서버리스 함수 최대 실행 시간과 웹훅 처리 시간 비교.
- **시나리오·수준:** C L2 이상
- **처방:** 코드: 서명 검증 → 이벤트를 수신함(C-056)에 저장 → 2xx → 워커가 처리. 인프라: 큐 또는 DB 수신함 + 워커 — 티어0 Vercel Queues/Inngest/QStash 등 또는 DB 테이블 + 크론, 티어1 Cloud Tasks/SQS + 워커 서비스, 티어2 큐 + 워커 Deployment.
- **검증:** 처리 함수에 15초 지연을 주입해 발신자 쪽 재시도가 생기지 않는지(즉시 2xx) 확인.
- **비용 영향:** 증가(큐·워커 추가) — 웹훅 볼륨이 작으면 DB 수신함 + 크론으로 비용 최소화.
- **출처:** https://docs.stripe.com/webhooks ("Quickly returns a successful status code (2xx) before any complex logic", "Handle events asynchronously"), https://docs.tosspayments.com/guides/v2/webhook ("10 초 이내로 200 응답") ⚠️출처부적격

### C-056 웹훅 수신함(inbox) 영속화
- **무엇/왜:** 2xx를 먼저 돌려주는 순간 발신자는 재전송을 멈춘다. 그 전에 이벤트를 **영속 저장소**에 기록하지 않으면, 프로세스가 죽을 때 이벤트가 영영 사라진다. 반대로 처리 실패 시 5xx를 돌려주면 발신자 재시도(Stripe 라이브 최대 3일, 토스 최대 7회·약 3일 19시간)에 기댈 수 있다.
- **실패 양상:** 메모리 큐(`setImmediate`, 백그라운드 태스크)에 넣고 200 응답 → 배포로 프로세스 교체 → 결제 이벤트 유실.
- **신호:** 🟢 웹훅 핸들러가 200 반환 후 `setTimeout`/`setImmediate`/FastAPI `BackgroundTasks`/`waitUntil`로 처리, 이벤트 저장 없음. 🟢 안전 패턴: `webhook_events` 테이블 INSERT 후 200.
- **시나리오·수준:** C L2 이상 (결제 웹훅이면 L3)
- **처방:** 코드: 원문 이벤트를 DB에 저장(이벤트 ID 유니크) 후 2xx, 처리 상태 컬럼으로 재처리 가능하게. 인프라: C-055와 같음. 수신함 보존 기간을 정하고 정리(C-112).
- **검증:** 2xx 직후 프로세스를 강제 종료하고 재기동 후 이벤트가 처리되는지 확인.
- **비용 영향:** 소폭 증가(저장 공간).
- **출처:** https://docs.stripe.com/webhooks ("Stripe attempts to deliver events to your destination for up to three days with an exponential back off in live mode"), https://docs.tosspayments.com/guides/v2/webhook (최대 7회, 간격 1·4·16·64·256·1024·4096분) ⚠️출처부적격

### C-057 웹훅 서명 검증과 원문 본문
- **무엇/왜:** 서명을 검증하지 않으면 누구나 "결제 완료" 이벤트를 위조해 주문을 완료시킬 수 있다(데이터 무결성 침해). 서명은 원문 바이트로 계산되므로 프레임워크가 JSON으로 파싱한 뒤 다시 직렬화하면 검증이 실패한다. 오래된 타임스탬프는 재생 공격으로 보고 거부한다.
- **실패 양상:** 위조 이벤트로 무료 이행, 또는 검증 실패를 피하려고 검증을 꺼 버림.
- **신호:** 🟢 웹훅 라우트에 `constructEvent`/서명 비교 없음, Express에서 `express.json()`이 웹훅 라우트보다 먼저 전역 적용(`express.raw` 미사용), Next.js에서 `await req.json()` 후 검증. 🟢 Stripe 라이브러리 tolerance를 0으로 설정. 🟡 토스 웹훅은 이벤트 종류별 검증 방식이 다르므로(문서 확인 필요) 수신 후 결제 조회 API로 상태를 재확인하는지.
- **시나리오·수준:** C L2 이상
- **처방:** 코드: 원문 본문(`req.text()`, `express.raw`)으로 공식 라이브러리 검증, 기본 허용 오차(Stripe 라이브러리 5분) 유지, 서버 시계 NTP 동기화. 검증 수단이 약하면 이벤트를 신호로만 쓰고 PG API 조회 결과로 상태 결정. 인프라: 웹훅 시크릿을 비밀 저장소에(티어0 플랫폼 env, 티어1/2 Secret Manager).
- **검증:** 서명 없는·변조된·오래된 이벤트가 400으로 거부되는지 테스트.
- **비용 영향:** 중립.
- **출처:** https://docs.stripe.com/webhooks ("Stripe requires the raw body of the request to perform signature verification", 기본 허용 오차 5분, "Don't use a tolerance value of 0"), https://docs.tosspayments.com/guides/v2/webhook (2026-10-01에 연 페이지 요약에서는 서명 검증 방법이 확인되지 않음) ⚠️출처부적격

---

## F. 메시징·큐·비동기 작업

### C-058 at-least-once 소비자의 멱등성
- **무엇/왜:** SQS 표준 큐, Redis Streams 소비자 그룹, Pub/Sub, Celery(늦은 ack), BullMQ는 모두 "최소 한 번" 전달이다. 소비자가 처리 후 ack 전에 죽으면 같은 메시지를 다시 받는다. 소비자 처리가 멱등이어야 한다.
- **실패 양상:** 워커 재시작·스케일인 때마다 일부 작업 중복(포인트 2배, 메일 2통, 글 2개).
- **신호:** 🟢 큐 라이브러리(`bullmq`, `bee-queue`, `celery`, `rq`, `dramatiq`, `@aws-sdk/client-sqs`, `@google-cloud/pubsub`, `xreadgroup`) + 소비자에서 INSERT/증감을 멱등 장치 없이 수행. 🟢 안전 패턴: 메시지 ID 기록 테이블, `ON CONFLICT DO NOTHING`, 조건부 UPDATE. SWA 워커는 `XREADGROUP` → 멱등 INSERT → `XACK`.
- **시나리오·수준:** C L2 이상 (비동기 작업 큐 존재가 L2 판정 신호)
- **처방:** 코드: 메시지에 안정적 ID(생산자가 부여)를 넣고, 소비자는 ID 기록과 비즈니스 갱신을 같은 트랜잭션에. 인프라: 없음(큐 종류 무관).
- **검증:** 처리 직후·ack 직전에 워커를 kill하는 장애 주입, 같은 메시지 수동 재전송 후 결과 1회 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues.html ("more than one copy of a message might be delivered"), https://redis.io/docs/latest/develop/data-types/streams/ ("duplicate processing is possible on failure"), https://microservices.io/patterns/communication-style/idempotent-consumer.html ⚠️출처부적격

### C-059 ack 시점(조기 ack는 유실, 늦은 ack는 중복)
- **무엇/왜:** 처리 전에 ack하면 워커가 죽을 때 작업이 사라지고, 처리 후 ack하면 중복이 생긴다. 정합성이 필요한 작업은 "늦은 ack + 멱등 처리"가 원칙이다. Celery 기본값은 실행 직전 ack(조기)다.
- **실패 양상:** Celery 기본 설정에서 워커 OOM으로 결제 후처리 작업 영구 유실.
- **신호:** 🟢 Celery `acks_late`/`task_acks_late` 미설정(기본 조기 ack), `task_reject_on_worker_lost`. 🟢 SQS `DeleteMessage`를 처리 전에 호출, Pub/Sub `message.ack()`가 처리 전, Redis Streams `XACK` 위치.
- **시나리오·수준:** C L2 이상
- **처방:** 코드: 늦은 ack로 바꾸고 C-058 멱등 처리. Celery는 `acks_late=True`여도 자식 프로세스가 비정상 종료하면 ack된다는 점을 알고 `task_reject_on_worker_lost` 등으로 보완 판단. 인프라: 없음.
- **검증:** 처리 중 워커 강제 종료 후 작업이 재전달·완료되는지 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.celeryq.dev/en/stable/userguide/tasks.html ("the default behavior is to acknowledge the message in advance", "If your task is idempotent you can set the acks_late option") ⚠️출처부적격

### C-060 가시성 타임아웃·재점유 시간과 처리 시간
- **무엇/왜:** SQS 가시성 타임아웃(기본 30초, 최대 12시간)이나 Redis Streams `XAUTOCLAIM`의 최소 유휴 시간보다 처리가 오래 걸리면, 처리 중인 메시지가 다른 워커에게 다시 간다.
- **실패 양상:** 2분 걸리는 영상 처리 작업을 30초 타임아웃 큐에 넣어 같은 작업이 4개 워커에서 동시에 실행.
- **신호:** 🟢 `VisibilityTimeout` 값, `ChangeMessageVisibility` 하트비트 유무, `xautoclaim(... min_idle_time=…)`, BullMQ `lockDuration`. 🟡 작업 내용(이미지·LLM·외부 API)으로 처리 시간 추정.
- **시나리오·수준:** C L2 이상
- **처방:** 코드: 타임아웃 ≥ p99 처리 시간 × 여유, 긴 작업은 하트비트로 연장하거나 쪼갬. 인프라: 큐 설정값(티어1/2 Terraform `visibility_timeout_seconds`).
- **검증:** 타임아웃보다 긴 작업을 넣어 중복 실행이 없는지(하트비트 동작) 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html (기본 30초, 최대 12시간, 하트비트 권장), https://redis.io/docs/latest/develop/data-types/streams/ (`XAUTOCLAIM` 유휴 시간 기준 재점유)

### C-061 독 메시지와 DLQ
- **무엇/왜:** 처리할 수 없는 메시지(잘못된 데이터, 버그를 건드리는 입력)는 무한 재시도로 큐를 막거나 자원을 태운다. 재전달 횟수 상한을 두고 DLQ로 격리한다.
- **실패 양상:** 메시지 하나가 워커를 계속 크래시시켜 뒤 메시지 전체가 정체(특히 순서 보장 큐), 비용 폭증.
- **신호:** 🟢 SQS `RedrivePolicy`/`maxReceiveCount`, Pub/Sub `deadLetterPolicy`, BullMQ `attempts` + failed 처리, Redis Streams 전달 횟수(`XPENDING`) 기반 DLQ 이동. SWA는 `posts:dlq`와 `dlq_size` 지표. 🟢 DLQ 없음 + 무한 재시도.
- **시나리오·수준:** C L2 이상
- **처방:** 코드: 재시도 상한 + DLQ 이동 + 원래 메시지·오류 원인 보존. 인프라: 티어1/2 DLQ 큐 리소스 + DLQ 크기 알림(관측 문서와 연동).
- **검증:** 항상 실패하는 메시지를 넣어 N회 후 DLQ로 가고 나머지 메시지가 정상 처리되는지 확인.
- **비용 영향:** 소폭 증가(DLQ 리소스), 무한 재시도 비용은 감소.
- **출처:** https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html (`maxReceiveCount`), https://redis.io/docs/latest/develop/data-types/streams/ ("High delivery counter indicates potential poison messages")

### C-062 일시 장애와 영구 오류의 구분
- **무엇/왜:** DB 장애 동안 실패한 메시지를 "N번 실패했으니 DLQ"로 보내면, 멀쩡한 메시지가 장애 시간만큼 DLQ에 쌓인다. 재시도 횟수가 아니라 **오류 종류**로 DLQ 여부를 정해야 한다.
- **실패 양상:** 10분 DB 장애 후 그 사이 들어온 정상 쓰기 수천 건이 DLQ로 가고, 수동 재처리 전까지 사용자 데이터가 사라진 것처럼 보임.
- **신호:** 🟢 SWA rulings Task 9: `is_transient`가 SQLSTATE 클래스 08(연결), 53(자원), 57P01~57P03, 25006, 40001, 40P01과 풀 고갈 `TimeoutError`를 일시 오류로 분류하고 "outage length must never decide DLQ". 🟢 일반 앱: 재시도 횟수만으로 DLQ 이동, 예외 종류 구분 없음.
- **시나리오·수준:** C L2 이상
- **처방:** 코드: 일시 오류(연결·타임아웃·직렬화 실패)는 무기한(백오프) 재시도, 영구 오류(검증 실패·제약 위반)만 DLQ. 재점유 경로에서도 같은 분류. 인프라: 없음.
- **검증:** DB를 10분 내린 뒤 복구했을 때 DLQ가 0건이고 모든 메시지가 처리되는지 확인(SWA의 testcontainers 장애 테스트 방식).
- **비용 영향:** 중립.
- **출처:** https://www.postgresql.org/docs/current/transaction-iso.html (40001은 재시도 대상), https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html ("set the maxReceiveCount high enough to allow for sufficient retries")

### C-063 DLQ 재처리 경로와 보존 기간
- **무엇/왜:** DLQ는 넣기만 하고 꺼낼 방법이 없으면 "조용한 데이터 손실"이다. 재처리(redrive) 도구와, 원래 큐보다 긴 보존 기간이 필요하다. SQS 표준 큐는 DLQ로 옮겨도 원래 enqueue 시각 기준으로 만료된다.
- **실패 양상:** DLQ 보존 기간이 원래 큐와 같아 조사하기 전에 메시지 만료, 버그 수정 후 재처리할 수단 없음.
- **신호:** 🟢 DLQ 큐의 `MessageRetentionPeriod` ≤ 원래 큐, redrive 스크립트·관리 명령 부재. 🔴 운영 절차는 코드에 없음 → 가정.
- **시나리오·수준:** C L2 이상
- **처방:** 코드: DLQ → 원래 큐로 되돌리는 관리 명령(멱등 소비자 전제). 인프라: DLQ 보존 기간을 원래 큐보다 길게(SQS 최대값 활용), Redis Streams DLQ는 `MAXLEN` 트리밍에 주의.
- **검증:** DLQ 메시지를 재처리해 결과가 1회만 반영되는지 확인.
- **비용 영향:** 소폭 증가.
- **출처:** https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html ("always set the retention period of a dead-letter queue to be longer than the retention period of the original queue")

### C-064 순서 보장(FIFO 그룹·순서 키·파티션 키)
- **무엇/왜:** 같은 엔터티의 이벤트(계좌 입출금, 문서 편집)는 순서가 바뀌면 결과가 달라진다. 큐 전체 순서는 비싸므로 엔터티 단위 키(SQS `MessageGroupId`, Pub/Sub ordering key, Kafka 파티션 키) 안에서만 순서를 보장한다. 표준 큐·일반 구독은 순서를 보장하지 않는다.
- **실패 양상:** "잔액 0으로 설정" 뒤 "+1000"이 먼저 처리, 삭제 이벤트가 생성보다 먼저 와서 유령 레코드.
- **신호:** 🟢 SQS 표준 큐 + 순서 의존 처리, `MessageGroupId` 미설정, Pub/Sub `enableMessageOrdering`/`orderingKey`, Kafka `key` 없이 전송. 🟢 워커 동시성 > 1인데 같은 엔터티 메시지를 병렬 처리.
- **시나리오·수준:** C L2 이상 (순서 의존 이벤트가 있으면)
- **처방:** 코드: 순서 의존을 없애는 것이 1순위(버전·상태 전이 조건, C-024). 필요하면 엔터티 ID를 그룹/순서/파티션 키로. 순서 키 하나에 처리량 상한이 있음(Pub/Sub 키당 1 MBps). 인프라: 티어1/2 FIFO 큐 또는 순서 키 구독.
- **검증:** 같은 키 이벤트 1,000개를 넣고 처리 순서를 기록해 단조성 확인.
- **비용 영향:** 증가(FIFO·순서 키는 처리량 제약과 단가 차이).
- **출처:** https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues.html ("messages may occasionally arrive out of order"), https://docs.cloud.google.com/pubsub/docs/ordering (키 안에서만 순서, 키당 1 MBps, 재전달 시 이후 메시지도 재전달), https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html (FIFO 그룹 순차 처리)

### C-065 FIFO 큐 중복 제거 창(5분)의 한계
- **무엇/왜:** SQS FIFO는 5분 중복 제거 창 안의 재전송만 막는다. 생산자가 5분 넘게 지나 재전송하거나, 소비 쪽에서 중복 처리되는 것은 막지 못한다. FIFO가 소비자 멱등성을 대신하지 않는다.
- **실패 양상:** "FIFO니까 중복 없음"이라고 믿고 소비자 멱등성을 생략 → 생산자 장시간 재시도·DLQ 재처리 때 중복.
- **신호:** 🟢 `.fifo` 큐 + `ContentBasedDeduplication` 또는 `MessageDeduplicationId`, 소비자에 멱등 장치 없음.
- **시나리오·수준:** C L2 이상
- **처방:** 코드: FIFO를 쓰더라도 C-058 적용. 인프라: 없음.
- **검증:** 6분 후 같은 메시지 재전송 시 소비 결과 1회 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues-exactly-once-processing.html ("within the 5-minute deduplication interval")

### C-066 "정확히 한 번"의 착각
- **무엇/왜:** 브로커의 exactly-once는 범위가 좁다. Pub/Sub exactly-once는 pull 구독·같은 리전에서만, ack 성공 후 재전달이 없다는 뜻이다. Kafka exactly-once는 Kafka 안(트랜잭션 프로듀서 + read_committed, Streams)에서 성립하고, 외부 DB에 쓰면 오프셋을 결과와 같은 곳에 저장해야 한다. 외부 부수효과(결제, 메일)는 어떤 브로커도 한 번으로 만들어 주지 않는다.
- **실패 양상:** exactly-once 옵션을 켰다고 소비자 멱등성을 빼서, 처리 중 크래시·ack 실패 때 외부 결제가 두 번 실행.
- **신호:** 🟢 Pub/Sub `enableExactlyOnceDelivery`, Kafka `enable.idempotence`/`transactional.id`/`isolation.level=read_committed`, 문서·주석의 "exactly once". 🟢 push 구독 + exactly-once 기대.
- **시나리오·수준:** C L2 이상
- **처방:** 코드: 브로커 설정과 무관하게 C-058 멱등 소비자. Kafka → DB면 오프셋을 결과와 같은 트랜잭션에 저장. 인프라: 없음.
- **검증:** ack 직전 크래시 주입 테스트.
- **비용 영향:** 중립(exactly-once 옵션은 지연·처리량 비용이 있음).
- **출처:** https://docs.cloud.google.com/pubsub/docs/exactly-once-delivery ("Only the pull subscription type supports exactly-once delivery", 같은 리전 한정), https://kafka.apache.org/42/design/design/ ("the consumer can store its offset in the same place as its output")

### C-067 BullMQ jobId 중복 제거의 한계
- **무엇/왜:** BullMQ에서 같은 `jobId`로 추가하면 무시되지만, 완료·실패 후 `removeOnComplete`/`removeOnFail`로 지워진 작업은 중복으로 보지 않는다. 생산 쪽 중복 제거를 jobId에만 의존하면 정리 설정에 따라 결과가 달라진다.
- **실패 양상:** `removeOnComplete: true` 설정 후 같은 주문 처리 작업이 재추가되어 두 번 실행.
- **신호:** 🟢 `queue.add(name, data, { jobId })` + `removeOnComplete: true`/숫자, 소비자 멱등성 없음.
- **시나리오·수준:** C L2 이상
- **처방:** 코드: jobId는 1차 방어, 소비자 멱등성(C-058)이 최종 방어. jobId에 `:` 금지·순수 숫자 금지 규칙 준수. 인프라: 없음.
- **검증:** 작업 완료·제거 후 같은 jobId 재추가 시 결과 1회 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.bullmq.io/guide/jobs/job-ids ("jobs that have been removed… will not be considered as duplicates") ⚠️출처부적격

### C-068 Redis를 큐 저장소로 쓸 때: noeviction + AOF
- **무엇/왜:** BullMQ·Redis Streams·Sidekiq 계열 큐는 Redis 키가 곧 작업이다. 메모리가 차서 퇴출되거나 재시작으로 마지막 몇 분이 사라지면 작업이 조용히 없어진다.
- **실패 양상:** 캐시와 큐를 같은 Redis(`allkeys-lru`)에 두고 트래픽 폭증 → 큐 키 퇴출 → 결제 후처리 작업 유실. RDB만 켠 Redis 재시작으로 최근 작업 유실.
- **신호:** 🟢 `maxmemory-policy`(redis.conf, ElastiCache 파라미터 그룹, Memorystore 설정, Terraform), `appendonly`, `appendfsync`. 🟢 큐 라이브러리 + 캐시 라이브러리가 같은 `REDIS_URL` 사용. 🔴 매니지드 Redis 설정이 코드에 없으면 기본값 가정(공급자별 기본 퇴출 정책 확인 필요).
- **시나리오·수준:** C L2 이상 (Redis 큐가 있으면)
- **처방:** 코드: 큐용·캐시용 연결을 분리. 인프라: 큐용 Redis는 `noeviction` + AOF `everysec`(최대 약 1초 손실 감수), 캐시용은 `allkeys-lru`. 티어0 Upstash 등은 퇴출 설정 확인, 티어1/2 별도 인스턴스 또는 파라미터 그룹.
- **검증:** maxmemory를 작게 잡고 큐를 채워 쓰기가 오류로 거부되는지(퇴출되지 않는지), Redis 강제 재시작 후 작업 수 비교.
- **비용 영향:** 증가(Redis 인스턴스 분리, AOF 디스크 I/O).
- **출처:** https://docs.bullmq.io/guide/going-to-production ("very important to configure the maxmemory-policy setting to noeviction", AOF 권장), https://redis.io/docs/latest/develop/reference/eviction/ (`noeviction`은 쓰기 시 오류 반환, 캐시와 영속 키 혼용 시 인스턴스 분리 권장), https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/ (`everysec`은 1초 손실 가능)

### C-069 LISTEN/NOTIFY를 큐로 쓰기
- **무엇/왜:** PostgreSQL NOTIFY는 커밋 시점에 연결 중인 리스너에게만 전달되고 저장되지 않는다. 리스너가 재시작 중이면 그 알림은 사라진다.
- **실패 양상:** 워커 배포 중 발생한 "주문 생성" 알림 유실 → 후처리 누락.
- **신호:** 🟢 `LISTEN`/`pg_notify`/`NOTIFY` + 작업 처리, 보조 폴링 없음. 🟢 Supabase Realtime(DB 변경 브로드캐스트)을 작업 트리거로 사용 — 🟡 전달 보장 확인 필요.
- **시나리오·수준:** C L2 이상
- **처방:** 코드: NOTIFY는 "깨우기 신호"로만 쓰고 실제 작업은 테이블(C-014)에서 꺼냄, 시작 시·주기적으로 미처리 행 스캔. 인프라: 없음.
- **검증:** 리스너를 끈 상태에서 이벤트 발생 후 재기동 시 처리되는지 확인.
- **비용 영향:** 중립.
- **출처:** https://www.postgresql.org/docs/current/sql-notify.html (커밋 시 전달, 비영속, 큐 8GB, 가득 차면 커밋 실패)

### C-070 프로세스 메모리 안의 백그라운드 작업
- **무엇/왜:** 응답 후 같은 프로세스에서 작업을 돌리는 방식(FastAPI `BackgroundTasks`, `setImmediate`, Next.js `after`/`waitUntil`, 스레드 풀)은 프로세스가 죽거나 교체되면 작업이 사라지고 재시도도 없다.
- **실패 양상:** 배포·스케일인·OOM 때 진행 중이던 결제 후처리·메일 발송 유실. 서버리스는 응답 후 인스턴스가 얼어 작업이 끝나지 않을 수도 있음.
- **신호:** 🟢 `BackgroundTasks.add_task`, `asyncio.create_task`(응답 후), `setImmediate`/`setTimeout`(핸들러 안), `waitUntil`, `after(` + DB 쓰기·외부 호출.
- **시나리오·수준:** C L2 이상 (작업이 정합성에 영향을 주면)
- **처방:** 코드: 잃으면 안 되는 작업은 영속 큐·DB 작업 테이블로. 잃어도 되는 것(분석 이벤트)만 메모리 작업 허용. 인프라: 티어0 매니지드 큐(QStash, Inngest, Vercel Queues 등), 티어1 Cloud Tasks/SQS, 티어2 큐 + 워커.
- **검증:** 작업 실행 중 SIGKILL 후 작업이 재실행되는지 확인.
- **비용 영향:** 증가(큐 도입).
- **출처:** 일반 원칙(출처 미확인). 조기 ack 시 유실과 같은 원리는 https://docs.celeryq.dev/en/stable/userguide/tasks.html ⚠️출처부적격 ⚠️근거없음

### C-071 비동기 쓰기 직후의 상태 조회
- **무엇/왜:** 쓰기를 큐로 넘기고 202를 돌려주면, 사용자가 곧바로 목록·상세를 볼 때 아직 DB에 없다. "내가 쓴 것이 안 보임"은 사용자에게 유실로 보이고 재시도(중복)를 부른다.
- **실패 양상:** 글을 썼는데 목록에 없어서 다시 씀 → 중복 글(멱등 키가 새로 발급되면 C-036).
- **신호:** 🟢 202 + `status: "pending"` 응답, 상태 조회 엔드포인트 유무. SWA: 202 `pending` + 상세 조회가 DB 실패 시 큐 마커로 pending/failed 반환(rulings). 🟢 클라이언트 낙관적 업데이트(TanStack Query `onMutate`).
- **시나리오·수준:** C L2 이상 (비동기 쓰기가 있으면)
- **처방:** 코드: 생성 ID를 즉시 반환하고 상태 조회(pending/done/failed) 제공, 클라이언트는 낙관적 표시 + 폴링. 인프라: 상태 마커 저장소(같은 Redis/DB).
- **검증:** 큐 소비를 멈춘 상태에서 쓰기 후 상세 조회가 pending을 반환하는지 확인.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

---

## G. 이중 쓰기·아웃박스·사가

### C-072 이중 쓰기(DB + 큐·캐시·검색·메일)
- **무엇/왜:** DB에 쓰고 이어서 큐 발행·캐시 갱신·검색 색인·메일 발송을 하면, 두 저장소를 원자적으로 묶을 방법이 없다(분산 트랜잭션은 대개 쓸 수 없다). 둘 중 하나만 성공하는 창이 반드시 있다.
- **실패 양상:** 주문은 저장됐는데 "주문 생성" 이벤트 발행 전 크래시 → 배송·포인트 처리 누락. 반대로 이벤트는 나갔는데 DB 롤백 → 존재하지 않는 주문의 메일 발송.
- **신호:** 🟢 같은 함수에서 `prisma.*.create` 뒤 `queue.add`/`sqs.send`/`publish`/`redis.set`/`index.save`/`sendEmail`, 또는 트랜잭션 안에서 발행(C-009). 탐지기 사실 후보 `dualwrite.db_then_publish`.
- **시나리오·수준:** C L2(이벤트가 부가 기능) / C L3(이벤트가 돈·재고에 영향)
- **처방:** 코드: L3는 아웃박스(C-073), L2는 커밋 후 발행(C-074) + 대사(C-049·C-030)로 보완. 인프라: 아웃박스 릴레이 워커(티어별 C-073).
- **검증:** DB 커밋 직후·발행 직전에 프로세스를 죽이는 장애 주입, 이벤트 누락 여부 확인.
- **비용 영향:** 중립~증가(릴레이 워커).
- **출처:** https://microservices.io/patterns/data/transactional-outbox.html (2PC 없이 DB 갱신과 메시지 발송을 원자적으로 해야 하는 문제) ⚠️출처부적격

### C-073 트랜잭셔널 아웃박스
- **무엇/왜:** 비즈니스 쓰기와 같은 트랜잭션에서 `outbox` 테이블에 메시지를 INSERT하고, 별도 릴레이가 이를 읽어 브로커로 보낸 뒤 표시한다. 커밋된 변경만 발행되고, 발행은 최소 한 번이 된다(소비자 멱등 필수).
- **실패 양상:** (아웃박스가 없을 때) C-072. (있지만 소비자가 멱등이 아닐 때) 릴레이가 발행 후 표시 전에 죽어 중복 발행.
- **신호:** 🟢 `outbox`/`domain_events`/`event_outbox` 테이블, 같은 트랜잭션 INSERT, 릴레이 워커(폴링 + `SKIP LOCKED`). 🔴 C L3인데 아웃박스가 없으면 미충족.
- **시나리오·수준:** C L3 (설계 문서 §4.1 L3 통제)
- **처방:** 코드: 아웃박스 INSERT를 같은 `tx`로, 릴레이는 `FOR UPDATE SKIP LOCKED`로 배치 처리, 메시지에 아웃박스 행 ID를 넣어 소비자 중복 제거. 인프라: 티어0 크론 기반 릴레이(지연 허용 시), 티어1 상시 워커 서비스(min instance 1), 티어2 릴레이 Deployment 또는 CDC(C-075).
- **검증:** 릴레이를 발행 직후 kill → 재기동 후 중복 발행이 소비자에서 무시되는지, 발행 누락 0건인지 확인.
- **비용 영향:** 증가(상시 워커, DB 쓰기 증가).
- **출처:** https://microservices.io/patterns/data/transactional-outbox.html ("The Message relay might publish a message more than once") ⚠️출처부적격

### C-074 커밋 후에만 부수효과 실행
- **무엇/왜:** 아웃박스까지는 과할 때(C L2) 최소한 "트랜잭션이 커밋된 뒤에만" 메일·작업 발행을 한다. Django `transaction.on_commit`이 대표적이다. 롤백 시 실행되지 않지만, 커밋 후 콜백 실패는 롤백되지 않으므로 유실 가능성이 남는다.
- **실패 양상:** 트랜잭션 안에서 Celery 작업을 발행했는데 커밋 전에 워커가 실행 → 아직 없는 행을 못 찾아 실패. 롤백됐는데 메일은 발송됨.
- **신호:** 🟢 `atomic` 블록 안의 `.delay(`/`.apply_async(`/`send_mail(` (on_commit 없이), 🟢 안전 패턴 `transaction.on_commit(lambda: task.delay(id))`. Prisma는 트랜잭션 콜백이 끝난 뒤(await 이후) 발행하는지 확인.
- **시나리오·수준:** C L2
- **처방:** 코드: 커밋 후 발행 + 실패 시 재시도 로그, 결과 대사. 돈·재고가 걸리면 C-073으로 승격. 인프라: 없음.
- **검증:** 트랜잭션 롤백 테스트에서 작업이 발행되지 않는지 확인(Django `captureOnCommitCallbacks`).
- **비용 영향:** 중립.
- **출처:** https://docs.djangoproject.com/en/stable/topics/db/transactions/ (`on_commit`: 롤백 시 실행 안 됨, 트랜잭션의 일부가 아님)

### C-075 CDC 기반 아웃박스(로그 테일링)
- **무엇/왜:** 폴링 릴레이 대신 DB 변경 로그(WAL)를 읽어 아웃박스 행을 브로커로 보낸다(Debezium Outbox Event Router). 폴링 지연·부하가 없지만 Kafka Connect 같은 운영 부담이 생긴다.
- **실패 양상:** (잘못 도입 시) 아웃박스 행을 UPDATE해서 이벤트가 중복·누락, 소비자 중복 제거 생략.
- **신호:** 🟢 Debezium 설정, `transforms.outbox.type=io.debezium.transforms.outbox.EventRouter`, 논리 복제 슬롯(`wal_level=logical`).
- **시나리오·수준:** C L3 + 처리량이 높을 때만 (그 외에는 과잉 → 축소 처방 후보)
- **처방:** 코드: 아웃박스 행은 INSERT만, 이벤트 ID로 소비자 중복 제거. 인프라: 티어2 전용(Kafka + Connect + Debezium), 매니지드 DB에서 논리 복제 활성화 필요.
- **검증:** 커넥터 재시작 중 이벤트 순서·중복 처리 확인.
- **비용 영향:** 증가(Kafka·Connect 클러스터).
- **출처:** https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html ("updates to records in an outbox table are not allowed", 이벤트 ID로 중복 제거) ⚠️출처부적격

### C-076 사가와 보상 트랜잭션
- **무엇/왜:** 여러 서비스·외부 API에 걸친 작업(결제 → 재고 → 배송 예약)은 하나의 DB 트랜잭션으로 묶을 수 없다. 단계별 로컬 트랜잭션 + 실패 시 앞 단계를 되돌리는 보상 작업(환불, 재고 반환)을 설계한다.
- **실패 양상:** 결제 성공 후 재고 예약 실패 → 환불 로직 없음 → 돈만 받고 주문 실패.
- **신호:** 🟢 한 흐름에서 결제 API + 다른 서비스 HTTP 호출 + 로컬 DB 쓰기가 순차로 있고 실패 분기에 되돌리기 없음. 🟢 Temporal·Step Functions·Inngest 같은 오케스트레이터 사용.
- **시나리오·수준:** C L3 (외부 서비스가 2개 이상 엮인 결제 흐름)
- **처방:** 코드: 단계·보상 표를 명시하고 오케스트레이션(중앙 조정자) 또는 코레오그래피(이벤트) 선택, 각 단계·보상은 멱등. 인프라: 티어0 Inngest/Vercel Workflow 등, 티어1 Step Functions/Cloud Workflows, 티어2 Temporal 등. 단순 흐름이면 DB 상태 머신 + 재시도 작업으로 충분(과잉 방지).
- **검증:** 각 단계 실패를 주입해 최종 상태가 "완료" 또는 "완전히 보상됨" 둘 중 하나인지 확인.
- **비용 영향:** 증가(오케스트레이터).
- **출처:** https://microservices.io/patterns/data/saga.html ("design compensating transactions that explicitly undo changes made earlier in a saga") ⚠️출처부적격

### C-077 사가의 격리 부재 대응
- **무엇/왜:** 사가 중간 상태는 다른 요청에게 보인다(ACID의 I가 없음). 보상되기 전의 "결제됨" 상태를 다른 흐름이 읽고 행동할 수 있다.
- **실패 양상:** 아직 확정되지 않은 예약을 근거로 다른 사용자에게 매진 표시, 보상 전에 포인트 사용.
- **신호:** 🟡 C-076 신호 + 중간 상태(`PENDING`, `RESERVED`) 표시 없이 최종 상태로 바로 기록.
- **시나리오·수준:** C L3
- **처방:** 코드: 중간 상태를 명시적 값으로 두고(semantic lock), 다른 흐름은 중간 상태를 확정으로 취급하지 않음. 인프라: 없음.
- **검증:** 사가 진행 중 동시 조회·사용 시나리오 테스트.
- **비용 영향:** 중립.
- **출처:** https://microservices.io/patterns/data/saga.html ("Lack of automatic rollback… lack of isolation", 대응책 설계 필요) ⚠️출처부적격

---

## H. 캐시·Redis 일관성

### C-078 쓰기 후 캐시 무효화의 순서와 경쟁
- **무엇/왜:** DB를 고친 뒤 캐시를 지우는 사이, 또는 캐시를 먼저 지우고 DB를 고치는 사이에 다른 요청이 옛 값을 다시 캐시에 채울 수 있다. 무효화를 트랜잭션 커밋 전에 하거나 아예 빠뜨리면 옛 값이 TTL 동안 고정된다.
- **실패 양상:** 가격 수정 후에도 옛 가격으로 결제 화면 표시, 삭제한 글이 캐시에 남음, 권한 회수 후에도 캐시된 권한으로 접근.
- **신호:** 🟢 쓰기 경로에 캐시 삭제(`redis.del`, `cache.delete`, `revalidateTag`) 없음, 또는 트랜잭션 안에서 삭제. SWA `cache.invalidate`는 `stale:posts:first`까지 지움(rulings). 🟡 캐시 키가 여러 곳(목록·상세·사용자별)에 흩어짐.
- **시나리오·수준:** C L1 이상 (가격·권한·재고 캐시면 L3에서 엄격)
- **처방:** 코드: 커밋 후 삭제(값 갱신보다 삭제), 짧은 TTL을 안전망으로, 가격·재고·권한 같은 결정 데이터는 결제·권한 판단 시 캐시 대신 DB(주 DB)에서 읽기. 인프라: 없음.
- **검증:** 쓰기 직후 읽기 테스트, 동시 읽기·쓰기 반복 후 캐시 값 = DB 값 확인.
- **비용 영향:** 중립(캐시 적중률 소폭 감소).
- **출처:** https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/Strategies.html (lazy loading의 stale 데이터, write-through, TTL)

### C-079 캐시 TTL을 정합성 상한으로
- **무엇/왜:** 무효화는 언젠가 빠진다. 모든 캐시 키에 TTL을 걸면 "최대 얼마 동안 틀릴 수 있다"를 정할 수 있다. TTL 없는 캐시는 버그 하나로 영원히 틀린다.
- **실패 양상:** 무효화 누락 버그로 옛 프로필이 몇 주째 표시.
- **신호:** 🟢 `redis.set(key, value)`(EX/PX 없음), `cache.set(key, value, None)`, `node-cache` stdTTL 0.
- **시나리오·수준:** C L1 이상
- **처방:** 코드: 데이터 종류별 TTL 표(예: SWA 목록 3초, 상세 30초, stale 사본 60초). 인프라: 퇴출 정책과 연계(C-082).
- **검증:** 무효화를 일부러 생략해도 TTL 후 값이 맞는지 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/Strategies.html ("doesn't guarantee that a value isn't stale. However, it keeps data from getting too stale")

### C-080 프레임워크 데이터 캐시와 쓰기 후 읽기(Next.js)
- **무엇/왜:** Next.js App Router의 데이터 캐시는 `revalidateTag(tag, "max")`면 stale-while-revalidate로 동작해 무효화 직후에도 옛 데이터를 한 번 더 준다. 사용자가 방금 쓴 결과를 봐야 하는 Server Action에서는 `updateTag`를 써야 한다. 웹훅 등 Server Action 밖에서는 `{ expire: 0 }`.
- **실패 양상:** 글 수정 → 리다이렉트된 상세 페이지에 옛 내용 → 사용자가 다시 수정(중복 쓰기·혼란). 결제 웹훅 후에도 주문 상태 페이지가 "대기".
- **신호:** 🟢 `'use cache'`, `cacheTag`, `fetch(..., { next: { tags } })`, Server Action 안의 `revalidateTag(tag, 'max')`, 단일 인자 `revalidateTag(tag)`(deprecated), `updateTag` 사용 여부.
- **시나리오·수준:** C L1 이상
- **처방:** 코드: 사용자 본인의 쓰기 직후 화면은 `updateTag`, 외부 이벤트 무효화는 `revalidateTag(tag, { expire: 0 })`, 일반 콘텐츠는 `"max"`. 인프라: 다중 인스턴스 자체 호스팅(티어1/2)이면 캐시 핸들러 공유 여부 확인(인스턴스별 캐시면 무효화가 한 인스턴스에만 적용될 수 있음 — 출처 미확인, 확인 필요). ⚠️근거없음
- **검증:** 쓰기 후 즉시 리다이렉트 E2E에서 새 값 표시 확인.
- **비용 영향:** 중립.
- **출처:** https://nextjs.org/docs/app/api-reference/functions/revalidateTag (stale-while-revalidate, `"max"`, `{ expire: 0 }`, `updateTag`)

### C-081 Redis를 원본 저장소로 쓰기
- **무엇/왜:** 세션·멱등 키·장바구니·카운터·큐를 Redis에만 두면 Redis의 영속성 설정이 곧 RPO다. RDB 스냅샷만 있으면 보통 몇 분, AOF `everysec`이면 최대 약 1초를 잃는다. 영속성이 꺼져 있으면 재시작 = 전부 유실.
- **실패 양상:** Redis 재시작으로 장바구니·멱등 키 소실 → 멱등 키가 사라진 직후 재시도가 중복 처리. 포인트 카운터를 Redis에만 두어 영구 손실.
- **신호:** 🟢 Redis에만 쓰는 비즈니스 데이터(`INCR points:*`, `HSET cart:*`), DB 동기화 없음. 🟢 `appendonly no`, `save ""`. 🟢 매니지드 Redis 티어(영속성 없는 캐시 전용 플랜인지).
- **시나리오·수준:** C L1 이상 (원본 데이터면), D와 연계
- **처방:** 코드: 돈·포인트·주문은 DB가 원본, Redis는 사본·가속. 멱등 키처럼 Redis에 둘 수밖에 없으면 유실 시 동작(DB 유니크 제약이 2차 방어)을 설계. 인프라: 원본을 두면 AOF 활성화 + 복제, 티어1/2 영속성 지원 플랜.
- **검증:** Redis 강제 재시작(kill -9) 후 데이터·중복 방지 동작 확인.
- **비용 영향:** 증가(영속·복제 플랜).
- **출처:** https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/ ("you should be prepared to lose the latest minutes of data", `everysec`은 1초 손실 가능)

### C-082 퇴출 정책과 키 용도 혼용
- **무엇/왜:** 캐시용 `allkeys-lru`는 메모리가 차면 아무 키나 지운다. 같은 인스턴스의 세션·락·멱등 키·큐도 지워진다. `volatile-*`는 TTL 있는 키만 지우고, 그런 키가 없으면 `noeviction`처럼 동작한다.
- **실패 양상:** 트래픽 폭증으로 캐시가 차면서 멱등 키·분산 락이 퇴출 → 중복 결제·크론 이중 실행. 세션 퇴출로 대량 로그아웃.
- **신호:** 🟢 하나의 `REDIS_URL`을 캐시·세션·락·큐가 공유 + `maxmemory-policy allkeys-*`. 🔴 정책 미지정이면 공급자 기본값을 가정(확인 필요).
- **시나리오·수준:** C L2 이상
- **처방:** 코드: 키 용도별 연결 분리(최소 접두사 + 문서화). 인프라: 가능하면 인스턴스 분리(캐시 = `allkeys-lru`, 나머지 = `noeviction`), 비용상 하나면 `volatile-lru` + 캐시 키에만 TTL, 영속 키는 TTL 없이.
- **검증:** maxmemory를 낮춘 환경에서 캐시를 가득 채운 뒤 락·멱등 키가 남아 있는지 확인.
- **비용 영향:** 증가(인스턴스 분리 시).
- **출처:** https://redis.io/docs/latest/develop/reference/eviction/ ("The volatile-xxx policies behave like noeviction if no keys have an associated expiration", "consider running two separate Redis instances")

### C-083 Redis 복제는 비동기(WAIT도 강한 일관성이 아님)
- **무엇/왜:** Redis 복제는 비동기라 프라이머리 장애 후 승격된 레플리카에는 마지막 쓰기가 없을 수 있다. `WAIT`는 레플리카 수신을 기다릴 뿐 강한 일관성을 보장하지 않는다.
- **실패 양상:** 페일오버 직후 락·멱등 키가 사라져 같은 작업이 두 번 실행(C-089).
- **신호:** 🟢 Sentinel/클러스터/매니지드 HA Redis + 락·멱등 키를 Redis에만 의존. 🟢 `WAIT` 사용.
- **시나리오·수준:** C L3
- **처방:** 코드: 정확성이 중요한 중복 방지는 DB 유니크·조건부 UPDATE로 최종 보장, Redis는 1차 필터. 인프라: 없음(페일오버 손실을 인정).
- **검증:** Redis 페일오버 주입 중 같은 요청 반복 → DB 결과 1회 확인.
- **비용 영향:** 중립.
- **출처:** https://redis.io/docs/latest/commands/wait/ ("WAIT does not make Redis a strongly consistent store… it is possible to still lose a write"), https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/ ("Redis replication is asynchronous")

---

## I. 복제·읽기 일관성·시간

### C-084 읽기 복제본 지연과 쓰기 후 읽기
- **무엇/왜:** 읽기 복제본은 비동기로 따라오므로 방금 쓴 데이터가 아직 없을 수 있다. 쓰기 직후 화면·결제 확인·잔액 확인을 복제본에서 읽으면 틀린 판단을 한다.
- **실패 양상:** 결제 후 주문 상세가 "결제 대기"로 보여 재결제, 잔액 확인을 복제본에서 해서 초과 출금, 가입 직후 로그인 실패.
- **신호:** 🟢 Prisma `readReplicas` 확장(`$primary()` 사용 여부), Django `DATABASE_ROUTERS` + `using('replica')`, `DATABASE_URL_READ`/`READER_ENDPOINT` 환경변수, Aurora reader endpoint, Supabase read replica URL.
- **시나리오·수준:** C L3 (설계 문서 §4.1: 쓰기 직후 읽기는 주 DB)
- **처방:** 코드: 쓰기 후 일정 시간·같은 세션의 읽기와 모든 "결정용 읽기"(잔액·재고·권한)는 주 DB, 목록·통계만 복제본. 인프라: 복제본이 정말 필요한지(T 판단)부터 — 필요 없으면 축소 처방.
- **검증:** 복제 지연을 인위로 늘린(또는 지연 지표를 보는) 환경에서 쓰기 직후 읽기 테스트.
- **비용 영향:** 중립(복제본 유지 비용은 T 쪽 판단).
- **출처:** https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_ReadRepl.html ("Amazon RDS copies them asynchronously to the read replica"), https://www.postgresql.org/docs/current/hot-standby.html ("data on the standby is eventually consistent with the primary")

### C-085 동기 복제와 커밋된 쓰기의 보존(RPO 0)
- **무엇/왜:** PostgreSQL 스트리밍 복제는 기본 비동기라 주 서버가 죽으면 커밋된 트랜잭션 일부가 사라질 수 있다. 결제·재고처럼 "커밋 = 잃지 않음"이 필요하면 동기 복제(`synchronous_standby_names` + `synchronous_commit`)나 동기 복제를 내장한 매니지드 HA가 필요하다.
- **실패 양상:** 결제 승인 후 DB 페일오버 → 결제 기록 소실, PG에는 승인됨(대사 전까지 모름).
- **신호:** 🟢 Terraform `multi_az = true`(RDS 인스턴스 Multi-AZ 대기 복제본은 동기), Cloud SQL `availability_type = "REGIONAL"`, 자체 운영 PG의 `synchronous_commit`·`synchronous_standby_names`. 🔴 매니지드 설정이 코드에 없으면 미확인.
- **시나리오·수준:** C L3 (설계 문서 §4.3: 결제·재고 데이터 RPO 0)
- **처방:** 코드: 없음. 인프라: 티어0 Supabase/Neon의 HA 옵션과 복제 방식 확인 필요(공급자 문서 확인 후 판정), 티어1/2 RDS Multi-AZ 또는 Cloud SQL 리전 HA. 자체 운영이면 `synchronous_commit = on`(또는 읽기 일관성까지 `remote_apply`). D 문서의 Multi-AZ 통제와 같은 리소스이므로 중복 과금하지 않게 통합 판정.
- **검증:** 쓰기 부하 중 강제 페일오버 후 클라이언트가 커밋 응답 받은 행이 모두 남아 있는지 확인.
- **비용 영향:** 증가(대기 인스턴스 비용, 쓰기 지연 증가).
- **출처:** https://www.postgresql.org/docs/current/warm-standby.html ("streaming replication is asynchronous by default… some transactions that were committed may not have been replicated"), https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_ReadRepl.html ("Replication with the standby replica is synchronous")

### C-086 Multi-AZ 대기 복제본과 읽기 복제본의 혼동
- **무엇/왜:** RDS 인스턴스 Multi-AZ의 대기 복제본은 동기지만 읽기를 받지 않는다. 읽기 복제본은 읽기를 받지만 비동기다. 둘을 섞어 "복제본이 있으니 RPO 0"이나 "Multi-AZ니까 읽기 분산"으로 오판하기 쉽다.
- **실패 양상:** 읽기 복제본만 두고 결제 데이터 RPO 0이라고 가정 → 페일오버(승격) 시 손실.
- **신호:** 🟢 Terraform `aws_db_instance`의 `replicate_source_db`(읽기 복제본) vs `multi_az`. 🟢 `aws_rds_cluster`(Aurora)·Multi-AZ DB 클러스터는 별도 판정.
- **시나리오·수준:** C L3
- **처방:** 코드: 없음. 인프라: RPO 0 통제는 동기 복제 리소스로 판정, 읽기 분산은 별도 판정.
- **검증:** 리포트에서 두 통제를 별도 근거(`파일:줄`)로 표시하는지 규칙 테스트.
- **비용 영향:** 중립(판정 정확도 문제).
- **출처:** https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_ReadRepl.html ("Unlike a read replica, a standby replica can't serve read traffic")

### C-087 시계·타임스탬프로 순서 정하기
- **무엇/왜:** 서버마다 시계가 조금씩 다르고, 같은 초에 여러 이벤트가 생긴다. "마지막 수정 시각이 더 큰 쪽이 이긴다"를 여러 서버의 벽시계로 하면 순서가 뒤집힌다. 웹훅 서명 검증은 시계가 틀리면 정상 이벤트를 거부한다.
- **실패 양상:** 두 인스턴스의 `updatedAt` 비교로 동기화하다 최신 변경 유실, 서버 시계가 6분 틀려 Stripe 웹훅 전부 거부.
- **신호:** 🟢 `updatedAt`/`created` 비교로 충돌 해결, `Date.now()` 기반 ID·정렬, Stripe `event.created` 정렬. 🟡 컨테이너·VM의 NTP 동기화(대부분 클라우드 기본 제공).
- **시나리오·수준:** C L2 이상
- **처방:** 코드: 순서는 DB가 부여하는 값(시퀀스, 버전 컬럼, 단일 DB의 `now()`)으로, 이벤트 순서는 상태 전이 규칙으로(C-024). 인프라: 호스트 NTP(클라우드 기본), Redis 락 TTL은 벽시계 영향(C-089).
- **검증:** 한 인스턴스 시계를 어긋나게 한 테스트 환경에서 충돌 해결 결과 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.stripe.com/webhooks ("Snapshot events record created in seconds, so distinct events can share a timestamp", NTP 사용 권장), https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/ ("Redis is not using monotonic clock for TTL expiration")

### C-088 리전 간 복제 저장소의 쓰기 충돌
- **무엇/왜:** 여러 리전에서 쓰기를 받는 저장소(DynamoDB 글로벌 테이블, 멀티 리전 Firestore·Cosmos 등)는 리전 간 트랜잭션을 보장하지 않거나 최종 일관성이다. 결제·재고처럼 단일 진실이 필요한 쓰기를 여러 리전에서 받으면 충돌한다.
- **실패 양상:** 두 리전에서 같은 재고를 동시에 차감해 둘 다 성공, 다른 리전에서 부분 완료된 트랜잭션이 보임.
- **신호:** 🟢 Terraform `replica {}` 블록(DynamoDB 글로벌 테이블), 멀티 리전 배포 + 리전별 쓰기 엔드포인트.
- **시나리오·수준:** C L3 (D L3 멀티 리전과 충돌하는 지점)
- **처방:** 코드: 정합성 핵심 쓰기는 단일 "홈 리전"으로 라우팅. 인프라: 멀티 리전은 읽기·DR 용도로 한정 — D 문서와 상충 시 C를 우선(설계 원칙 5: 정합성은 아끼지 않음).
- **검증:** 두 리전 동시 차감 테스트.
- **비용 영향:** 감소 가능(멀티 리전 쓰기 포기).
- **출처:** https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/transaction-apis.html ("Transactions aren't supported across Regions in global tables… You may observe partially completed transactions")

---

## J. 분산 락·크론·배치

### C-089 Redis 락의 올바른 구현
- **무엇/왜:** 단일 Redis 락은 `SET key 고유값 NX PX ttl`로 잡고, 해제는 "값이 내 것일 때만 삭제"(Lua 스크립트, Redis 8.4+ `DELEX … IFEQ`)로 해야 한다. 그냥 `DEL`하면 TTL이 지나 다른 클라이언트가 잡은 락을 지운다. 락은 TTL 동안만 상호 배제를 보장하고, 페일오버(비동기 복제) 시 깨질 수 있다.
- **실패 양상:** 작업이 TTL보다 오래 걸린 클라이언트가 남의 락을 `DEL` → 세 번째 클라이언트까지 진입. `SETNX` 후 `EXPIRE`를 따로 호출하다 그 사이 크래시 → 영원히 안 풀리는 락.
- **신호:** 🟢 `setnx(` + 별도 `expire(`, `set(key, "1", nx=True)`(고정 값) + `delete(key)`, TTL 없는 락. 🟢 안전 패턴: 랜덤 토큰 + 비교 삭제 스크립트, `redlock`/`node-redlock`/`redis-py` `Lock`. SWA `cache.py`의 스탬피드 락은 `"1"` 고정 값 + TTL(캐시 채우기 용도라 상호 배제가 깨져도 결과가 같아 허용 가능 — 정합성 락과 구분).
- **시나리오·수준:** C L2 이상 (락이 정합성을 지키는 용도일 때)
- **처방:** 코드: 랜덤 토큰 + 비교 삭제, TTL ≥ 최대 작업 시간(또는 연장), 정합성이 걸린 곳은 펜싱 토큰(C-090) 또는 DB 잠금으로 대체. 인프라: 없음(락 전용으로 Redis를 새로 두는 것은 과잉일 수 있음 → DB advisory lock 우선 검토).
- **검증:** TTL보다 긴 작업 + 동시 진입 테스트, 락 해제가 남의 락을 지우지 않는지 확인.
- **비용 영향:** 중립.
- **출처:** https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/ ("Using just DEL is not safe as a client may remove another client's lock", 비동기 복제로 인한 안전성 위반 시나리오)

### C-090 펜싱 토큰
- **무엇/왜:** GC 정지·네트워크 지연으로 락이 만료된 줄 모르는 클라이언트가 늦게 쓰기를 하면, 이미 새 소유자가 있는 자원을 덮어쓴다. 락을 잡을 때 단조 증가 번호를 받고, 저장소가 더 작은 번호의 쓰기를 거부해야 안전하다.
- **실패 양상:** 오래 멈춘 워커가 깨어나 새 워커의 결과를 옛 데이터로 덮어씀(정산 결과 역전).
- **신호:** 🟡 분산 락 + 긴 작업 + 공유 자원 쓰기, 쓰기 조건에 토큰·버전 비교 없음.
- **시나리오·수준:** C L3
- **처방:** 코드: 락 획득 시 증가 토큰(DB 시퀀스, 버전 컬럼), 쓰기를 `WHERE fence < $token`으로 조건화. 대부분의 앱은 락 대신 DB 조건부 UPDATE로 같은 효과를 낸다. 인프라: 없음.
- **검증:** 락 보유 클라이언트를 일시 정지시킨 뒤 깨워 늦은 쓰기가 거부되는지 확인.
- **비용 영향:** 중립.
- **출처:** https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html (토큰 33/34 예시), https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/ ("You should implement fencing tokens") ⚠️출처부적격

### C-091 크론 중복 실행
- **무엇/왜:** 스케줄러는 같은 회차를 두 번 실행할 수 있다. k8s CronJob은 기본 `concurrencyPolicy: Allow`이고 "한 회차에 Job 두 개 또는 0개"가 생길 수 있다. Cloud Scheduler는 at-least-once, Vercel Cron도 같은 회차를 중복 호출할 수 있고 이전 실행이 길면 겹친다.
- **실패 양상:** 월 정기결제·정산·포인트 만료 배치가 두 번 실행되어 이중 청구·이중 차감.
- **신호:** 🟢 CronJob에 `concurrencyPolicy` 없음(=Allow), `vercel.json` `crons`, Cloud Scheduler/EventBridge Scheduler 대상, 크론 핸들러에 락·회차 기록 없음. 탐지기 사실 `cron.no_lock`.
- **시나리오·수준:** C L2 이상 (크론이 쓰기를 하면)
- **처방:** 코드: 회차 키(예: `job:billing:2026-10-01`) 유니크 기록으로 회차당 1회, 겹침 방지는 DB advisory xact lock 또는 Redis 락(C-089), 작업 자체를 "상태 설정형"으로(C-094). 인프라: 티어2 `concurrencyPolicy: Forbid` + `startingDeadlineSeconds`, 티어1 스케줄러 재시도 설정 확인, 티어0 `CRON_SECRET` + 앱 레벨 락.
- **검증:** 같은 회차를 동시에 두 번 트리거해 효과 1회 확인.
- **비용 영향:** 중립.
- **출처:** https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/ (Allow 기본, "two Jobs or none"), https://docs.cloud.google.com/scheduler/docs/overview ("it is possible for a job to run multiple times… Your targets should be idempotent"), https://vercel.com/docs/cron-jobs/manage-cron-jobs ("Cron delivery can also occasionally invoke the same scheduled run more than once")

### C-092 크론 누락·실패 후 따라잡기
- **무엇/왜:** 크론은 빠질 수도 있다. Vercel은 전달이 best effort이고 실패해도 재시도하지 않는다. "오늘 할 일"만 처리하는 작업은 한 번 빠지면 그 날 처리가 영원히 없다.
- **실패 양상:** 하루치 구독 갱신·만료 처리·정산 누락이 다음 회차에도 복구되지 않음.
- **신호:** 🟢 크론 작업이 `today`/`now - 1 day` 범위만 처리, 마지막 성공 시각 기록 없음.
- **시나리오·수준:** C L2 이상
- **처방:** 코드: "마지막 성공 이후 미처리분 전부" 처리하는 조정형 작업, 마지막 성공 시각 저장, 미처리 지연 알림. 인프라: 재시도 지원 스케줄러(티어1 Cloud Scheduler 재시도 설정, 티어2 Job `backoffLimit`).
- **검증:** 한 회차를 건너뛴 뒤 다음 회차가 누락분까지 처리하는지 확인.
- **비용 영향:** 중립.
- **출처:** https://vercel.com/docs/cron-jobs/manage-cron-jobs ("Vercel will not retry an invocation if a cron job fails", "Design your operations to be idempotent and reconciliation-based")

### C-093 다중 인스턴스의 프로세스 내장 스케줄러
- **무엇/왜:** `node-cron`, `setInterval`, APScheduler, Celery beat를 웹 프로세스 안에서 돌리면, 오토스케일로 인스턴스가 N개가 될 때 작업도 N번 실행된다. 서버리스(티어0)에서는 아예 안 돌 수도 있다.
- **실패 양상:** 인스턴스 3개 → 매일 알림 메일 3통, 정산 3회.
- **신호:** 🟢 `node-cron`, `cron` 패키지, `setInterval` + DB 쓰기, `apscheduler`, `@nestjs/schedule` `@Cron`, `celery beat`가 웹 프로세스·여러 레플리카에서 기동. 탐지기 사실 `process.cron`.
- **시나리오·수준:** C L1 이상 (인스턴스가 2개 이상이 될 수 있으면)
- **처방:** 코드: 스케줄 작업을 별도 엔트리포인트로 분리 + C-091 락. 인프라: 티어0 플랫폼 크론, 티어1 Cloud Scheduler → 작업 엔드포인트/Job, 티어2 CronJob(웹 Deployment와 분리).
- **검증:** 레플리카를 3개로 늘리고 회차당 실행 횟수 집계.
- **비용 영향:** 중립~감소(웹 인스턴스가 스케줄 때문에 상시 떠 있을 필요가 없어짐).
- **출처:** 일반 원칙(출처 미확인). 중복 실행의 결과와 락 권고는 https://vercel.com/docs/cron-jobs/manage-cron-jobs ⚠️근거없음

### C-094 배치 작업의 재실행 안전성
- **무엇/왜:** 배치는 중간에 실패하고 다시 돈다. "증가형"(포인트 +10, 잔액 차감) 작업은 재실행 시 두 번 반영되고, "설정형"(상태 = active)은 안전하다. 처리 단위마다 완료 표시(체크포인트)가 있어야 이어서 돌릴 수 있다.
- **실패 양상:** 1만 명 정산 배치가 5천 명에서 실패 → 재실행 → 앞 5천 명 이중 정산.
- **신호:** 🟢 배치 루프 안의 `increment`/`balance - x`/`INSERT`(멱등 키 없음), 처리 표시 컬럼 없음, 전체를 하나의 거대한 트랜잭션으로 처리.
- **시나리오·수준:** C L2 이상
- **처방:** 코드: 항목별 처리 기록(배치 회차 + 대상 ID 유니크), 상태 설정형으로 작성, 청크 단위 커밋 + 체크포인트. 인프라: 없음.
- **검증:** 배치 중간 강제 종료 → 재실행 → 결과가 1회 실행과 같은지 비교.
- **비용 영향:** 중립.
- **출처:** https://vercel.com/docs/cron-jobs/manage-cron-jobs ("Good: Set user status to active… Bad: Increment user credit by 10")

### C-095 크론 시간대
- **무엇/왜:** 크론 표현식의 시간대가 UTC인지 현지 시간인지에 따라 "매일 0시 정산"이 9시간 어긋난다. k8s CronJob은 `.spec.timeZone`(v1.27 안정)으로 IANA 시간대를 지정할 수 있다.
- **실패 양상:** 한국 기준 일 마감 정산이 오전 9시에 돌아 전날 15시~24시 거래가 다음 날로 넘어감.
- **신호:** 🟢 CronJob `timeZone` 부재, `vercel.json` 크론 표현식, 코드 주석 "매일 자정" + UTC 스케줄러. 🟡 비즈니스 시간대(통화 KRW, 언어 ko) 추론. ⚠️근거없음
- **시나리오·수준:** C L1 이상 (일 단위 정산·만료가 있으면)
- **처방:** 코드: 작업이 처리 범위를 업무 시간대로 명시 계산(스케줄 시각에 의존하지 않음). 인프라: 티어2 `timeZone: Asia/Seoul`, 티어1 Cloud Scheduler 시간대 필드, 티어0는 플랫폼 시간대 확인 후 UTC 변환.
- **검증:** 경계 시각(현지 23:59, 00:01) 거래로 일 마감 범위 테스트.
- **비용 영향:** 중립.
- **출처:** https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/ (`.spec.timeZone`, v1.27 안정)

---

## K. BaaS 무결성 (Supabase·Firebase)

### C-096 Supabase 노출 스키마의 RLS와 기본 권한
- **무엇/왜:** Supabase는 브라우저가 anon 키로 DB에 직접 쓴다. 노출 스키마의 테이블에 RLS가 없으면 권한이 있는 누구나 읽고 쓸 수 있다. 새 테이블은 `anon`·`authenticated`에 모든 권한이 기본 부여되고, 정책을 추가해도 그 grant는 회수되지 않는다. 데이터 무결성 관점에서 "누가 어떤 행을 쓸 수 있나"가 곧 불변식이다.
- **실패 양상:** 다른 사용자의 주문 상태를 `paid`로 변경, 남의 게시글 삭제, 포인트 컬럼 직접 수정.
- **신호:** 🟢 `supabase/migrations/*.sql`에 `create table` 후 `alter table … enable row level security` 없음, `create policy` 부재, `grant all … to anon`. 🟢 클라이언트 코드 `supabase.from('orders').update(...)`.
- **시나리오·수준:** C L1 이상 (Supabase를 클라이언트에서 직접 쓰면)
- **처방:** 코드: 모든 노출 테이블 RLS 활성화 + 최소 정책, 불필요 grant 회수(`revoke … from anon`). 인프라: 티어0 설정 그 자체. Supabase 대시보드 보안 경고 확인.
- **검증:** anon 키·다른 사용자 토큰으로 직접 REST 호출해 거부되는지 테스트(pgTAP 또는 통합 테스트).
- **비용 영향:** 중립.
- **출처:** https://supabase.com/docs/guides/database/postgres/row-level-security ("A table in an exposed schema without RLS is readable and writable by any role with a grant on it", "Adding policies doesn't take those grants back"), https://www.postgresql.org/docs/current/ddl-rowsecurity.html (정책 없으면 기본 거부)

### C-097 RLS UPDATE 정책의 WITH CHECK
- **무엇/왜:** `USING`은 어떤 기존 행을 건드릴 수 있는지, `WITH CHECK`는 바뀐 결과 행이 허용되는지를 본다. UPDATE에 `WITH CHECK`가 없으면 내 행을 고치면서 `user_id`를 남의 것으로 바꾸거나 금지 값으로 바꿀 수 있다.
- **실패 양상:** 사용자가 자기 주문의 `user_id`를 다른 사람으로 바꿔 떠넘김, `status`를 `refunded`로 직접 변경.
- **신호:** 🟢 `create policy … for update using (...)`에 `with check` 없음, 또는 `with check (true)`. 🟢 클라이언트가 고칠 수 있는 컬럼에 `status`, `amount`, `role`, `points` 포함.
- **시나리오·수준:** C L1 이상
- **처방:** 코드: UPDATE 정책에 `WITH CHECK (auth.uid() = user_id)`, 민감 컬럼은 컬럼 단위 grant 회수 또는 서버 함수로만 변경(C-101). 인프라: 없음.
- **검증:** 클라이언트에서 소유자·상태 컬럼 변경 시도가 거부되는지 테스트.
- **비용 영향:** 중립.
- **출처:** https://supabase.com/docs/guides/database/postgres/row-level-security (USING vs WITH CHECK, UPDATE는 둘 다) ⚠️출처부적격

### C-098 규칙을 우회하는 서버 자격 증명
- **무엇/왜:** Supabase `service_role`은 RLS를 우회하고, Firebase Admin SDK·서버 클라이언트 라이브러리는 보안 규칙을 모두 우회한다. 서버 경로에서는 규칙이 지켜 주던 불변식(소유권, 허용 필드)을 코드가 직접 검사해야 한다. PostgreSQL에서도 테이블 소유자·`BYPASSRLS` 역할은 RLS를 우회한다.
- **실패 양상:** Next.js Route Handler가 `service_role`로 요청 본문 그대로 update → 클라이언트 규칙으로 막던 조작이 서버 경유로 통과. 마이그레이션 계정(소유자)으로 앱을 돌려 RLS가 전혀 작동하지 않음.
- **신호:** 🟢 `SUPABASE_SERVICE_ROLE_KEY` 사용처, `firebase-admin` 초기화 + 요청 본문 직접 저장, DB 접속 사용자가 테이블 소유자. 🟢 `NEXT_PUBLIC_`/`VITE_` 접두사가 붙은 service_role 키(보안 문서와 공유 이슈).
- **시나리오·수준:** C L1 이상
- **처방:** 코드: 서버 경로에서 소유권·필드 화이트리스트 검사, 가능하면 사용자 JWT로 접속해 RLS가 적용되게. 앱 DB 계정은 소유자가 아닌 역할로, 필요 시 `FORCE ROW LEVEL SECURITY`. 인프라: 비밀 키는 서버 환경변수로만.
- **검증:** 서버 API에 남의 리소스 ID를 넣어 변경 시도 → 거부 확인.
- **비용 영향:** 중립.
- **출처:** https://supabase.com/docs/guides/database/postgres/row-level-security ("service_role… bypasses RLS"), https://firebase.google.com/docs/firestore/security/get-started ("The server client libraries bypass all Cloud Firestore Security Rules"), https://www.postgresql.org/docs/current/ddl-rowsecurity.html (소유자·BYPASSRLS 우회, FORCE)

### C-099 Firestore 규칙의 필드 화이트리스트와 타입 검증
- **무엇/왜:** Firestore 보안 규칙은 인증뿐 아니라 쓰기 내용도 검증할 수 있다. `diff().affectedKeys().hasOnly([...])`로 바꿀 수 있는 필드를 제한하고, `is` 연산자로 타입을 검사한다. 없으면 클라이언트가 문서에 아무 필드나 쓴다.
- **실패 양상:** 사용자가 자기 프로필 문서에 `isAdmin: true`, `points: 999999` 기록. 숫자 필드에 문자열 저장으로 집계 깨짐.
- **신호:** 🟢 `firestore.rules`의 `allow write: if request.auth != null;`(내용 검증 없음), `allow read, write: if true`, `hasOnly`/`affectedKeys`/`is` 사용 여부.
- **시나리오·수준:** C L1 이상 (Firebase 클라이언트 쓰기가 있으면)
- **처방:** 코드: 생성은 `keys().hasOnly/hasAll`, 수정은 `diff().affectedKeys().hasOnly`, 타입 검사. 금액·포인트·권한 필드는 클라이언트 쓰기 금지(Cloud Functions에서만). 인프라: 티어0 설정, 규칙 에뮬레이터 테스트를 CI에.
- **검증:** Firebase 에뮬레이터 규칙 단위 테스트로 금지 필드 쓰기 거부 확인.
- **비용 영향:** 중립.
- **출처:** https://firebase.google.com/docs/firestore/security/rules-fields (`diff().affectedKeys().hasOnly()`, `is` 타입 검사)

### C-100 Firestore 트랜잭션의 재실행과 제약
- **무엇/왜:** Firestore 트랜잭션은 경합 시 함수를 자동으로 다시 실행한다. 그래서 트랜잭션 함수 안에서 앱 상태 변경·외부 호출을 하면 여러 번 일어난다. 읽기는 쓰기보다 먼저 해야 하고, 오프라인이면 실패한다.
- **실패 양상:** 트랜잭션 함수 안의 `fetch`·로그·UI 상태 변경이 재시도마다 반복, 오프라인 사용자의 구매가 조용히 실패.
- **신호:** 🟢 `runTransaction(db, async (t) => { … fetch/console/setState … })`, 쓰기 후 `t.get`. 🟢 다문서 갱신을 트랜잭션·`writeBatch` 없이 개별 `updateDoc`으로.
- **시나리오·수준:** C L2 이상
- **처방:** 코드: 트랜잭션 함수는 순수하게(읽기 → 계산 → 쓰기), 부수효과는 커밋 후. 쓰기만 묶으면 `writeBatch`. 돈·재고는 서버(Cloud Functions)에서. 인프라: 없음.
- **검증:** 같은 문서에 동시 트랜잭션을 걸어 재실행 시 부수효과 횟수 확인.
- **비용 영향:** 소폭 증가(재시도 읽기 과금).
- **출처:** https://firebase.google.com/docs/firestore/manage-data/transactions ("Transaction functions should not directly modify application state", 읽기 선행, 오프라인 실패)

### C-101 클라이언트 다단계 쓰기 대신 DB 함수 하나로
- **무엇/왜:** supabase-js로 클라이언트에서 "재고 확인 → 주문 생성 → 재고 차감"을 여러 번 호출하면 원자성이 없다. Postgres 함수 하나에 담아 `rpc()`로 부르면 한 번의 호출 안에서 처리된다. `security definer` 함수는 권한 상승이므로 `search_path`를 고정해야 한다.
- **실패 양상:** 주문 행은 생겼는데 재고 차감 호출이 네트워크 오류로 실패 → 초과 판매. `security definer` 함수가 조작된 `search_path`로 다른 스키마 객체를 실행.
- **신호:** 🟢 클라이언트 컴포넌트에서 `supabase.from(...).insert` 다음 `.update`가 연속, `supabase.rpc(` 사용 여부, 함수 정의의 `security definer` + `set search_path` 유무.
- **시나리오·수준:** C L1 이상 (재고·포인트면 L3)
- **처방:** 코드: 불변식이 걸린 다단계 쓰기는 PL/pgSQL 함수 + `rpc()`(함수 안에서 C-003 조건부 UPDATE), 기본은 `security invoker`, definer면 `set search_path = ''` + 스키마 한정 이름. 인프라: 없음(티어0에서 서버 없이 L3 통제를 얻는 경로).
- **검증:** C-003 동시성 테스트를 rpc 경로로 실행.
- **비용 영향:** 중립.
- **출처:** https://supabase.com/docs/guides/database/functions (`rpc()`로 호출, "Prefer security invoker… When you use security definer, you must set the search_path")

### C-102 뷰가 RLS를 우회
- **무엇/왜:** PostgreSQL 뷰는 기본적으로 뷰 소유자 권한으로 실행되어 기반 테이블의 RLS를 우회한다. Supabase에서 집계·조인 뷰를 노출하면 다른 사용자의 행이 보인다(이어서 그 정보로 조작).
- **실패 양상:** `order_summaries` 뷰로 전체 주문 금액·상태 노출.
- **신호:** 🟢 마이그레이션의 `create view`에 `with (security_invoker = true)` 없음 + 뷰가 `public`(노출) 스키마.
- **시나리오·수준:** C L1 이상 (Supabase)
- **처방:** 코드: `security_invoker = true`(PG 15+) 또는 뷰를 비노출 스키마로, grant 회수. 인프라: 없음.
- **검증:** 다른 사용자 토큰으로 뷰 조회 시 자기 행만 나오는지 확인.
- **비용 영향:** 중립.
- **출처:** https://supabase.com/docs/guides/database/postgres/row-level-security ("By default, views bypass RLS. Use security_invoker = true") ⚠️출처부적격

---

## L. 파일·검색·파생 저장소

### C-103 파일 업로드와 DB 레코드의 일관성(고아 파일·끊긴 링크)
- **무엇/왜:** 파일은 객체 저장소에, 메타데이터는 DB에 있다. 업로드 후 DB 저장이 실패하면 고아 파일이, DB 삭제 후 파일 삭제가 실패하면(또는 반대) 끊긴 링크가 생긴다. Supabase에서는 `storage.objects` 행을 SQL로 지우면 실제 파일은 남는다.
- **실패 양상:** 아무도 참조하지 않는 파일이 쌓여 저장 비용 증가, 탈퇴한 사용자의 사진이 남아 개인정보 삭제 요구 불이행, 게시글 이미지 깨짐.
- **신호:** 🟢 presigned URL 업로드(`getSignedUrl`, `createPresignedPost`, `createSignedUploadUrl`) 후 별도 DB 저장 호출, 레코드 삭제 시 파일 삭제 없음, `delete from storage.objects`. 탐지기 사실 `state.upload.local_fs`(로컬 디스크는 T/D 문제와 겹침).
- **시나리오·수준:** C L1 이상
- **처방:** 코드: "DB에 pending 레코드 → 업로드 → 확정" 순서, 삭제는 DB에서 먼저 표시 후 비동기로 파일 삭제(재시도), 정기 고아 파일 청소(참조 없는 키 + 생성 후 N시간 경과). Supabase는 Storage API로 삭제. 인프라: 임시 업로드 접두사에 수명 주기 만료 규칙(티어1/2 S3/GCS lifecycle, 티어0 플랫폼 기능 확인).
- **검증:** 업로드 후 DB 실패 주입 → 청소 작업이 파일을 지우는지, 레코드 삭제 후 파일 접근이 불가한지 확인.
- **비용 영향:** 감소(고아 파일 저장 비용 제거).
- **출처:** https://supabase.com/docs/guides/storage/management/delete-objects ("Deleting objects via a SQL query will not remove the object from the bucket and will result in the object being orphaned")

### C-104 객체 저장소의 동시 쓰기와 키 충돌
- **무엇/왜:** S3는 PUT·DELETE 후 강한 read-after-write 일관성을 주지만, 같은 키에 동시 PUT은 마지막 타임스탬프가 이기고 객체 잠금은 없다. 키 간 원자적 갱신도 없다. 사용자 입력 파일명을 키로 쓰면 서로 덮어쓴다.
- **실패 양상:** 두 사용자가 `avatar.png`를 같은 경로에 올려 한쪽 사진이 다른 사람 것으로 바뀜, 여러 파일로 된 묶음의 일부만 새 버전.
- **신호:** 🟢 업로드 키에 `file.name`/`originalname`을 그대로 사용, 사용자·UUID 접두사 없음. 🟡 여러 객체를 함께 갱신하는 매니페스트 구조.
- **시나리오·수준:** C L1 이상
- **처방:** 코드: 키는 `{userId}/{uuid}` 같이 충돌 불가하게, 갱신은 새 키에 쓰고 DB 포인터를 원자적으로 교체. 인프라: 덮어쓰기 복구가 필요하면 버전 관리(D 문서와 연계).
- **검증:** 같은 파일명 동시 업로드 테스트.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html ("Amazon S3 does not support object locking for concurrent writers… There is no way to make atomic updates across keys")

### C-105 미완료 멀티파트 업로드 정리
- **무엇/왜:** 대용량 업로드가 중간에 끊기면 업로드된 파트가 보이지 않는 채로 남아 저장 요금이 나온다. 수명 주기 규칙 `AbortIncompleteMultipartUpload`로 일정 일수 후 정리한다.
- **실패 양상:** 객체 목록에는 없는데 저장 요금이 계속 증가.
- **신호:** 🟢 `@aws-sdk/lib-storage` `Upload`, `CreateMultipartUpload`, tus/Uppy 멀티파트 + 버킷 수명 주기 설정 부재(Terraform `aws_s3_bucket_lifecycle_configuration`의 `abort_incomplete_multipart_upload`).
- **시나리오·수준:** C L1 이상 (대용량 업로드가 있으면)
- **처방:** 코드: 실패 시 `AbortMultipartUpload` 호출. 인프라: 티어1/2 수명 주기 규칙(예: 7일).
- **검증:** 업로드 중단 후 규칙 적용 일수 경과 시 파트가 삭제되는지(또는 `ListMultipartUploads` 결과) 확인.
- **비용 영향:** 감소.
- **출처:** https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpu-abort-incomplete-mpu-lifecycle-config.html ("we recommend that you configure a lifecycle rule by using the AbortIncompleteMultipartUpload action to minimize your storage costs")

### C-106 검색 인덱스 동기화
- **무엇/왜:** Elasticsearch·OpenSearch·Algolia·Meilisearch 같은 검색 엔진은 DB의 사본이다. DB 쓰기 후 색인을 같은 요청에서 하면 이중 쓰기(C-072)가 되고, 색인 자체도 즉시 검색되지 않는다(Elasticsearch 기본 1초 refresh, 30초간 검색이 없던 인덱스는 refresh 생략).
- **실패 양상:** 삭제한 상품이 검색에 계속 노출되어 주문 시도, 색인 실패로 새 상품이 영원히 검색 안 됨, 가격이 검색 결과와 상세에서 다름.
- **신호:** 🟢 `@elastic/elasticsearch`, `algoliasearch`, `meilisearch` 클라이언트 호출이 DB 쓰기 직후 같은 핸들러에, 재색인 스크립트 부재.
- **시나리오·수준:** C L2 이상 (검색 결과로 거래 판단을 하면)
- **처방:** 코드: 아웃박스·CDC로 색인 이벤트 전달(C-073), 전체 재색인 작업 보유, 결정 데이터(가격·재고)는 상세 조회 시 DB에서 재확인. 인프라: 색인 워커(티어별 C-073과 공유).
- **검증:** 색인 실패 주입 후 재색인·재처리로 DB와 인덱스 문서 수·해시 일치 확인.
- **비용 영향:** 증가(워커·재색인 작업).
- **출처:** https://www.elastic.co/docs/manage-data/data-store/near-real-time-search ("periodically refreshes indices every second, but only on indices that have received one search request or more in the last 30 seconds")

---

## M. 삭제·보존·감사

### C-107 소프트 삭제와 유니크 제약의 충돌
- **무엇/왜:** `deleted_at`으로 숨기기만 하면 삭제된 행이 유니크 제약을 계속 점유한다. 탈퇴한 이메일로 재가입하거나 같은 슬러그를 다시 쓰려 할 때 막힌다. 반대로 유니크를 빼면 살아 있는 행끼리 중복이 생긴다.
- **실패 양상:** 탈퇴 후 재가입 불가(고객 문의), 또는 유니크를 지운 탓에 활성 계정 중복.
- **신호:** 🟢 `deleted_at`/`deletedAt`/`is_deleted` 컬럼 + 같은 테이블의 전체 유니크(`email UNIQUE`). SWA `auth.users`가 `email UNIQUE` + `deleted_at` 구조(재가입 정책 판단 필요 지점).
- **시나리오·수준:** C L1 이상
- **처방:** 코드: 부분 유니크 인덱스 `UNIQUE (email) WHERE deleted_at IS NULL`, 또는 탈퇴 시 식별자를 익명화해 해제. Prisma 스키마로 부분 인덱스를 못 쓰면 마이그레이션 SQL에 직접. 인프라: 없음.
- **검증:** 가입 → 탈퇴 → 같은 이메일 재가입, 활성 계정 중복 시도 거부 확인.
- **비용 영향:** 중립.
- **출처:** https://www.postgresql.org/docs/current/indexes-partial.html (부분 유니크 인덱스로 일부 행에만 유니크 적용)

### C-108 소프트 삭제 필터 누락
- **무엇/왜:** 소프트 삭제는 모든 조회에 `WHERE deleted_at IS NULL`을 붙여야 한다. 한 곳이라도 빠지면 삭제된 데이터가 다시 나타나거나 집계에 섞인다.
- **실패 양상:** 삭제한 글이 검색·관리자 통계·외부 API에 노출, 삭제된 상품이 장바구니 합계에 포함.
- **신호:** 🟢 `deleted_at` 컬럼이 있는데 `findMany`/`objects.filter` 호출 중 일부에 조건 없음, 전역 필터(Prisma 확장, Django 커스텀 매니저, RLS 정책) 유무.
- **시나리오·수준:** C L1 이상
- **처방:** 코드: 기본 매니저·쿼리 확장·뷰로 필터를 강제, 삭제 포함 조회는 명시적 별도 경로. 인프라: 없음.
- **검증:** 삭제 후 모든 공개 API·집계에서 해당 행이 나오지 않는지 테스트.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### C-109 개인정보 삭제의 전파
- **무엇/왜:** 사용자 삭제·익명화 요청은 DB 한 테이블로 끝나지 않는다. 캐시, 검색 인덱스, 업로드 파일, 큐에 쌓여 있던 미처리 메시지, 분석 이벤트, 로그까지 퍼진 사본이 있다. GDPR 등 규제 판단은 다른 문서 담당이지만 "삭제가 모든 사본에 반영되는가"는 정합성 문제다.
- **실패 양상:** 탈퇴했는데 캐시된 프로필·검색 결과·이미지 URL이 남음, 큐에 밀려 있던 글이 탈퇴 후 작성자 이름으로 저장.
- **신호:** 🟢 탈퇴 핸들러가 users 행만 삭제·표시, 파생 저장소 삭제·익명화 없음. 🟢 SWA: `user_deleted` 이벤트 발행 + 워커가 `deleted_user:<id>` 마커(EX 7200)를 보고 큐 백로그의 글을 익명화(rulings) — 그리고 2시간 넘는 백로그·두 워커 경합 시 일부가 이름 붙은 채 저장되는 것을 알려진 한계로 기록.
- **시나리오·수준:** C L1 이상 (개인정보가 있으면)
- **처방:** 코드: 삭제 이벤트를 아웃박스로 발행하고 각 파생 저장소 소비자가 멱등하게 삭제·익명화, 큐 소비자는 처리 시점에 삭제 여부 확인(마커 TTL ≥ 최대 백로그 지연). 인프라: 없음.
- **검증:** 큐에 사용자 메시지를 쌓은 상태에서 탈퇴 → 백로그 처리 후 해당 사용자 식별 정보가 어디에도 없는지 검사.
- **비용 영향:** 소폭 증가.
- **출처:** 일반 원칙(출처 미확인). 규제 원문(GDPR 제17조)은 이 세션에서 EUR-Lex 본문을 열지 못해 인용하지 않았다. ⚠️근거없음

### C-110 삭제·탈퇴 작업의 재시도 완료성
- **무엇/왜:** 여러 단계로 된 삭제(표시 → 이벤트 발행 → 세션 삭제 → 파일 삭제)는 중간에 실패한다. 재시도했을 때 끝까지 갈 수 있도록, 되돌릴 수 없는 단계(세션·키 삭제)를 마지막에 둬야 한다.
- **실패 양상:** 세션을 먼저 지운 뒤 이벤트 발행 실패 → 사용자는 로그아웃됐고 다시 요청할 방법이 없어 삭제가 반쪽으로 남음.
- **신호:** 🟢 SWA rulings Task 5: `soft_delete → publish_user_deleted → delete_all` 순서로 바꿔 "XADD 실패를 재시도로 복구 가능"하게 함(대가: 재시도 시 이벤트 중복 → 소비자 멱등으로 흡수). 🟢 일반 앱: 탈퇴 핸들러의 단계 순서와 실패 처리.
- **시나리오·수준:** C L2 이상
- **처방:** 코드: 재시도 가능한 단계를 앞에, 비가역 단계를 뒤에, 각 단계 멱등. 인프라: 없음.
- **검증:** 각 단계 사이 실패 주입 후 재요청으로 완료되는지 확인.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인). 근거 사례는 SWA `docs/superpowers/rulings.md` ⚠️근거없음

### C-111 감사 로그
- **무엇/왜:** 누가 언제 무엇을 바꿨는지(관리자 환불, 권한 변경, 금액 수정)는 분쟁·사고 조사·대사의 근거다. 감사 로그를 비즈니스 쓰기와 다른 경로(비동기 로그 전송)로 남기면 커밋된 변경의 기록이 빠질 수 있다.
- **실패 양상:** 환불 분쟁 시 누가 환불했는지 기록 없음, 로그 전송 실패로 권한 상승 기록 누락.
- **신호:** 🟢 `audit_logs`/`activity_log` 테이블, `django-simple-history`/`django-auditlog`, PG 트리거 감사. 🔴 없으면 C L3에서 미충족 가정.
- **시나리오·수준:** C L3 (결제·관리자 기능이 있으면), 그 외 선택
- **처방:** 코드: 감사 행을 같은 트랜잭션에 INSERT(또는 DB 트리거), 수정·삭제 금지(권한 회수), 행위자·대상·이전/이후 값·요청 ID 기록. 인프라: 장기 보관이 필요하면 저비용 저장소로 주기 이관(D·비용 문서와 연계).
- **검증:** 관리자 작업 후 감사 행 존재, 롤백된 작업은 감사 행도 없음을 확인.
- **비용 영향:** 소폭 증가(저장 공간).
- **출처:** 일반 원칙(출처 미확인). 변경 이력의 이점은 https://microservices.io/patterns/data/event-sourcing.html ⚠️출처부적격 ⚠️근거없음

### C-112 보존 기간과 만료 데이터 정리
- **무엇/왜:** 멱등 키, 웹훅 수신함, 아웃박스, 처리 완료 메시지 ID, 세션, 임시 업로드는 기능상 일정 기간만 필요하다. 정리하지 않으면 테이블이 무한히 커지고, 정리를 잘못하면 아직 필요한 키를 지워 중복이 생긴다.
- **실패 양상:** `processed_events` 수억 행으로 INSERT 느려짐, 반대로 하루 만에 지운 이벤트 ID가 3일 재시도 웹훅을 다시 처리.
- **신호:** 🟢 위 테이블들에 `created_at` 인덱스·정리 작업(크론, `pg_cron`, TTL 컬럼) 유무. Redis 키 TTL. 🔴 법정 보존 기간(결제 기록 등)은 코드에 없음 → 규제 문서의 가정 사용.
- **시나리오·수준:** C L2 이상
- **처방:** 코드: 보존 기간 ≥ 상대 시스템의 최대 재시도 기간(Stripe 웹훅 자동 재시도 3일·수동 재전송 최대 30일, 토스 약 3일 19시간, 멱등 키 C-035)으로 정한 뒤 배치 삭제(청크 단위). 결제·감사 기록은 정리 대상에서 제외. 인프라: 정리 크론(C-091), 대형 테이블은 시간 파티션 후 파티션 단위 삭제.
- **검증:** 정리 작업 후 보존 기간 내 재전송이 여전히 중복으로 판정되는지 확인.
- **비용 영향:** 감소(저장 공간·인덱스 크기).
- **출처:** https://docs.stripe.com/webhooks (라이브 자동 재시도 최대 3일, CLI 재전송 30일), https://docs.tosspayments.com/guides/v2/webhook (7회·약 3일 19시간), https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html (보존 기간 설정)

### C-113 이벤트 소싱 채택 여부(과잉 판정 포함)
- **무엇/왜:** 이벤트 소싱은 상태 대신 변경 이벤트를 저장해 감사·시점 조회·신뢰할 수 있는 이벤트 발행을 얻지만, 학습 곡선이 높고 조회를 위해 CQRS(최종 일관성 읽기 모델)가 필요하다. 바이브코더 앱 대부분에는 과잉이다.
- **실패 양상:** (불필요한 채택) 읽기 모델 지연으로 "방금 쓴 게 안 보임"이 상시화, 이벤트 스키마 변경 비용 폭증. (필요한데 없음) 금융 원장의 변경 근거 부재 — 이 경우 C-051 원장이 더 가벼운 대안.
- **신호:** 🟢 `eventstore`, `@eventstore/db-client`, `EventStoreDB`, Axon, `projections`/`aggregates` 디렉터리, 이벤트 테이블에서 상태 재구성 코드.
- **시나리오·수준:** C L3에서도 대부분 불필요 — 존재 시 과잉 여부 판정
- **처방:** 코드: 감사·원장 요구는 C-051·C-111로 충족 가능하면 이벤트 소싱 대신 그것을 권고. 이미 쓰고 있으면 "이미 있는 인프라 존중" — 읽기 모델 지연에 대한 쓰기 후 읽기 처리(C-071) 확인. 인프라: 이벤트 저장소 전용 클러스터는 축소 처방 후보.
- **검증:** 읽기 모델 지연 측정, 프로젝션 재구축 시간 측정.
- **비용 영향:** 감소(미채택 권고 시) / 증가(채택 시).
- **출처:** https://microservices.io/patterns/data/event-sourcing.html ("there is a learning curve", CQRS 필요와 최종 일관성) ⚠️출처부적격

---

## 새 축·규칙 후보

카탈로그를 쓰면서 설계 문서 §4·§6·§8에 넣을 만하다고 본 것들이다.

### 1. C 수준 판정 규칙 보강 (§4.2)
- **C L2 승격 신호 추가:** `api.idempotency_key` 부재와 무관하게, **비동기 백그라운드 작업이 정합성 쓰기를 하는 경우**(C-070), **크론이 쓰기를 하는 경우**(C-091), **Firestore/Supabase 클라이언트 직접 쓰기**(C-096·C-099)도 L2 신호로 넣는다. 현재 표는 웹훅·큐·클라이언트 재시도만 본다.
- **C L3 승격 신호 추가:** `balance|points|credits|wallet` 컬럼(원장 성격, C-051), 예약 겹침 검사(C-006), 선착순 쿠폰(C-052). 현재 표는 결제 SDK와 재고·잔액·좌석 차감 패턴만 본다.
- **C L0 판정 주의:** "쓰기 경로가 캐시·로그·분석뿐"이라도 Redis가 **원본**인 데이터(C-081)가 있으면 L0이 아니다.

### 2. 새 탐지기 사실 후보 (§6.2)
| 사실 ID | 탐지 방법 | 관련 항목 |
|---|---|---|
| `money.float_column` | Prisma `Float`/SQL `REAL`·`DOUBLE`·`money`/Django `FloatField` + 금액 이름 | C-039 |
| `money.client_amount_trusted` | 요청 본문·쿼리 `amount`가 결제 SDK 호출 인자로 흐름(semgrep taint) | C-041 |
| `payment.fulfill_on_redirect_only` | 성공 페이지에만 이행 코드, 웹훅 라우트 없음 | C-045 |
| `payment.external_id_not_unique` | `paymentKey`·`paymentIntentId` 컬럼에 유니크 없음 | C-043 |
| `webhook.ack_before_persist` | 웹훅 200 반환 후 메모리 작업으로 처리 | C-056 |
| `webhook.raw_body_broken` | `express.json()` 전역 + 웹훅 라우트, `req.json()` 후 검증 | C-057 |
| `queue.early_ack` | Celery `acks_late` 미설정, 처리 전 `DeleteMessage`/`ack()` | C-059 |
| `queue.no_dlq` / `queue.dlq_by_count_only` | 재시도 상한·DLQ 부재 / 예외 분류 없는 횟수 기반 DLQ | C-061·C-062 |
| `dualwrite.db_then_publish` | 같은 함수에서 DB 쓰기 후 큐·검색·메일 호출, 아웃박스 없음 | C-072 |
| `tx.external_call_inside` | 트랜잭션 블록 안 HTTP·결제 SDK 호출 | C-009 |
| `redis.shared_cache_and_state` | 같은 `REDIS_URL`을 캐시 + 큐/락/멱등 키가 공유 | C-068·C-082 |
| `redis.lock_unsafe_release` | 고정 값 락 + `DEL` 해제, `SETNX` + 별도 `EXPIRE` | C-089 |
| `db.read_replica_routing` | `readReplicas`, `using('replica')`, reader 엔드포인트 | C-084 |
| `cron.in_process` | `node-cron`·`setInterval`·APScheduler가 웹 프로세스에서 기동 | C-093 |
| `k8s.cronjob.concurrency_allow` | CronJob `concurrencyPolicy` 미설정 | C-091 |
| `supabase.rls_missing` / `supabase.view_definer` | 마이그레이션 `create table` 후 RLS 미활성 / `security_invoker` 없는 뷰 | C-096·C-102 |
| `firestore.rules_no_field_check` | `allow write: if request.auth != null` 등 내용 검증 없음 | C-099 |
| `storage.user_filename_key` | 업로드 키에 원본 파일명 사용 | C-104 |
| `softdelete.unique_conflict` | `deleted_at` + 전체 유니크 | C-107 |
| `prisma.version` | `prisma` 메이저 버전(7 vs 8) — 트랜잭션 API·`increment`·격리 수준 옵션 신호가 버전마다 다름 | C-001·C-002·C-006 |

### 3. 티어 규칙 후보 (§8.2 tier)
- **C-TIER 후보 A:** C L3 경로(조건부 차감·잠금)가 엣지 런타임 또는 HTTP 전용 서버리스 DB 드라이버에서 실행되면 티어0 구성에 "Node 런타임 + TCP 드라이버" 또는 "DB 함수(RPC) 원자화"를 필수 조건으로 단다(C-015·C-101). 둘 다 불가능하면 티어0 제외.
- **C-TIER 후보 B:** 아웃박스(C-073)가 필요한데 상시 워커를 둘 수 없는 티어0라면, 크론 기반 릴레이의 지연(분 단위)이 허용되는지로 가른다. 허용 불가면 티어1(min instance ≥ 1 워커) 이상.
- **C-TIER 후보 C:** 큐용 Redis와 캐시용 Redis를 분리해야 하는데(C-068·C-082) 비용이 문제면, 큐를 PostgreSQL `SKIP LOCKED` 테이블(C-014)로 옮기는 것을 더 싼 대안으로 비교한다.

### 4. 비용 규칙 후보 (§8.2 cost, 과잉 탐지)
- C L2 이하인데 Kafka + Debezium(C-075), 이벤트 소싱 저장소(C-113), 사가 오케스트레이터(C-076)가 있으면 축소 처방 후보.
- C L3 RPO 0 요구(C-085)와 D L2 Multi-AZ 요구는 같은 리소스로 충족되는 경우가 많으므로 견적에서 이중 계상하지 않는다(교차 시나리오 통제 공유 축).
- 고아 파일 청소(C-103)·미완료 멀티파트 정리(C-105)·만료 데이터 정리(C-112)는 정합성 처방이면서 비용 **감소** 처방이다. "비용 감소형 정합성 처방"을 리포트에서 따로 묶어 보여 주면 설득력이 크다.

### 5. 새 축 후보
- **"원본 저장소 지도" 축:** 데이터 종류(주문, 결제, 세션, 멱등 키, 큐, 파일, 검색)마다 원본이 어디인지, 사본이 어디에 몇 개 있는지를 사실로 만든다. 이중 쓰기(C-072), Redis 원본(C-081), 삭제 전파(C-109), 대사(C-049) 판정이 모두 이 지도에서 나온다. 현재 사실 모델(`Fact`)에는 저장소 간 관계를 표현하는 사실이 없다.
- **"재시도 창 정합" 축:** 상대 시스템의 최대 재시도·재전송 기간(웹훅 3일, 큐 보존 기간, 클라이언트 재시도)과 우리 쪽 중복 제거 보존 기간(멱등 키 TTL, 처리 ID 보존, 삭제 마커 TTL)을 비교하는 규칙. SWA의 `deleted_user` 마커 TTL 2시간 < 백로그 가능 시간 같은 불일치가 정확히 이 축에서 잡힌다(C-035·C-109·C-112).
- **"검증 가능성" 축(P4 연계):** 항목마다 적은 검증 방법은 동시 요청 주입(C-002·C-003·C-012·C-033·C-044·C-052), 중복 재전송(C-053·C-058·C-065·C-091), 장애 주입(C-001·C-056·C-059·C-062·C-073·C-085), 불변식 쿼리(C-030·C-049·C-051) 네 종류로 묶인다. P4 검증 루프의 C 시나리오 테스트 템플릿을 이 네 종류로 만들면 규칙의 `verify` ID와 1:1로 붙일 수 있다.
