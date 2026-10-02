# 장애 대응·고가용성·재해 복구

시나리오 D(재난/장애)의 규칙 재료가 되는 고려 요소 카탈로그다. 데이터를 잃지 않는 것(백업·복원·손상 대응), 존과 리전 장애에도 계속 도는 것(Multi-AZ·DR), 의존성이 무너져도 핵심 기능을 지키는 것(격리·디그레이드·정적 안정성)을 다룬다.
트래픽 확장(T), 배포·설정(U), 정합성·멱등성(C), 보안·규제, 비용 최적화, 일반 관측은 다른 카탈로그가 맡는다. 겹치는 항목은 D 관점(장애 시 무엇이 깨지는가)만 적는다.
수치는 아래 출처를 2026-10-01에 직접 열어 확인한 값만 썼다. 확인하지 못한 항목은 "일반 원칙(출처 미확인)"으로 표시했다.

표기: 🟢 코드·설정으로 확정 가능 / 🟡 힌트, 추론 필요 / 🔴 코드에 없음 → 가정으로 처리. 티어0 = Vercel·Supabase·Firebase 등 / 티어1 = Cloud Run·ECS Fargate / 티어2 = GKE·EKS.

## 목차
1. [데이터 백업과 보존](#1-데이터-백업과-보존) — D-001 ~ D-016
2. [복원·PITR·데이터 손상 대응](#2-복원pitr데이터-손상-대응) — D-017 ~ D-024
3. [단일 장애점과 존(AZ) 장애](#3-단일-장애점과-존az-장애) — D-025 ~ D-039
4. [리전 장애와 DR 전략](#4-리전-장애와-dr-전략) — D-040 ~ D-053
5. [헬스 체크와 프로브](#5-헬스-체크와-프로브) — D-054 ~ D-060
6. [의존성 장애 격리](#6-의존성-장애-격리) — D-061 ~ D-070
7. [디그레이드 모드와 정적 안정성](#7-디그레이드-모드와-정적-안정성) — D-071 ~ D-079
8. [캐시·재시도·재접속 폭주](#8-캐시재시도재접속-폭주) — D-080 ~ D-083
9. [DNS·인증서·엣지](#9-dns인증서엣지) — D-084 ~ D-091
10. [외부 SaaS·플랫폼 의존](#10-외부-saas플랫폼-의존) — D-092 ~ D-098
11. [컨트롤 플레인·글로벌 서비스·쿼터](#11-컨트롤-플레인글로벌-서비스쿼터) — D-099 ~ D-104
12. [블래스트 반경과 격리 경계](#12-블래스트-반경과-격리-경계) — D-105 ~ D-108
13. [재난 시 필수 서비스의 특성](#13-재난-시-필수-서비스의-특성) — D-109 ~ D-113
14. [검증과 리허설](#14-검증과-리허설) — D-114 ~ D-116
15. [새 축·규칙 후보](#새-축규칙-후보)

---

## 1. 데이터 백업과 보존

### D-001 영속 데이터 인벤토리
- **무엇/왜:** 백업 전략의 출발점은 "어디에 무엇이 저장되는가"의 목록이다. DB만 백업하고 오브젝트 스토리지, Redis 큐, 업로드 디렉터리, 외부 SaaS에 쌓인 데이터를 빼먹는 일이 흔하다. 재생성 가능한 데이터(캐시, 읽기 복제본)는 백업 대신 재생성 절차를 둔다.
- **실패 양상:** DB는 복원했는데 첨부 파일·프로필 이미지가 사라지거나, 큐에 있던 미처리 쓰기가 사라진다. 복원된 DB가 존재하지 않는 파일 경로를 가리킨다.
- **신호:** 🟢 DB 드라이버(`pg`, `asyncpg`, `prisma`, `@supabase/supabase-js`, `firebase-admin`), 스토리지 SDK(`@aws-sdk/client-s3`, `google-cloud-storage`, `supabase.storage`), `multer`/`UploadFile` 저장 경로, Redis Streams·리스트를 큐로 쓰는 코드(`XADD`, `LPUSH`), Terraform `aws_db_instance`, `aws_s3_bucket`, `google_sql_database_instance`, `aws_elasticache_*`. 🟡 데이터 등급(사용자 생성 vs 재생성 가능)은 추론. ⚠️근거없음
- **시나리오·수준:** D L1 이상 (D L0 판정 자체의 근거)
- **처방:** 모든 티어: 탐지 결과를 "저장소 × 데이터 종류 × 재생성 가능 여부 × 백업 수단" 표로 리포트에 출력.
- **검증:** 정적 검사(탐지된 저장소마다 백업 통제가 하나 이상 매핑되는지). 복원 리허설 때 저장소별 체크리스트로 사용.
- **비용 영향:** 중립. 목록화 자체는 비용 없음.
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_backing_up_data_identified_backups_data.html (2026-10-01)

### D-002 DB 자동 백업 활성화와 보존 기간
- **무엇/왜:** 매니지드 DB의 자동 백업은 켜져 있어야 하고 보존 기간이 RPO·발견 지연을 덮어야 한다. RDS는 API·CLI로 만들 때 보존 기간을 지정하지 않으면 기본 1일, 콘솔은 7일이며 범위는 0~35일, 0은 자동 백업 비활성이다.
- **실패 양상:** 금요일에 생긴 데이터 손상을 월요일에 발견했는데 보존 기간 1일이라 손상 전 시점이 이미 없다. `backup_retention_period = 0`이면 백업 자체가 없다.
- **신호:** 🟢 Terraform `aws_db_instance.backup_retention_period`(없음 → API 기본 1일로 간주), `google_sql_database_instance.settings.backup_configuration.enabled`, `.backup_retention_settings.retained_backups`. 🔴 콘솔로 만든 DB는 코드에 없음 → 가정.
- **시나리오·수준:** D L1 이상 (설계 문서 D-CTL-001과 같음)
- **처방:** 티어0: Supabase Pro 이상(일일 백업 7일, Team 14일, Enterprise 최대 30일). 티어1·2: RDS `backup_retention_period >= 7`, Cloud SQL 자동 백업 활성.
- **검증:** 정적 검사(값 확인) + 복원 리허설(D-017)로 가장 오래된 복원 가능 시점 확인.
- **비용 영향:** 증가(소폭). 보존 기간만큼 백업 스토리지 과금.
- **출처:** https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_WorkingWithAutomatedBackups.BackupRetention.html · https://supabase.com/docs/guides/platform/backups (2026-10-01)

### D-003 Supabase Free 플랜을 운영 데이터에 사용
- **무엇/왜:** Supabase Free 플랜은 자동 백업이 없고(문서는 CLI `db dump`로 직접 내보내기를 권장), 7일 동안 활동이 적으면 프로젝트가 일시정지된다. 바이브코더 앱에서 가장 흔한 D L1 위반이다.
- **실패 양상:** 실수로 테이블을 지우면 복구 수단이 없다. 트래픽이 적은 서비스(예: 재난 때만 쓰는 서비스)가 평시에 일시정지되어 정작 필요할 때 응답하지 않는다.
- **신호:** 🟢 `@supabase/supabase-js`·`supabase/config.toml` 존재. 🟡 플랜은 코드에 없음 → `.env.example`의 프로젝트 URL만으로는 판별 불가. 🔴 플랜 → "Free로 가정"하고 리포트 상단에 표시.
- **시나리오·수준:** D L1 이상. 평시 트래픽이 낮고 D L3인 서비스에는 일시정지 위험이 별도로 치명적.
- **처방:** 티어0: Pro 이상으로 업그레이드(문서의 프로덕션 체크리스트도 일시정지 방지를 위해 Pro 권장). 업그레이드 불가 시 GitHub Actions 등으로 주기적 `supabase db dump`를 외부 저장소에 보관.
- **검증:** 플랜 확인(대시보드·Management API), 덤프 파일 존재와 복원 리허설.
- **비용 영향:** 증가. Pro 플랜 월 요금이 추가된다.
- **출처:** https://supabase.com/docs/guides/platform/backups · https://supabase.com/docs/guides/platform/free-project-pausing · https://supabase.com/docs/guides/deployment/going-into-prod (2026-10-01)

### D-004 PITR(특정 시점 복구) 활성화
- **무엇/왜:** 일일 백업만 있으면 최악 RPO가 24시간이다. PITR은 트랜잭션 로그로 원하는 시점까지 복구한다. RDS는 트랜잭션 로그를 5분마다 S3에 올린다. Supabase PITR은 애드온이며 WAL을 2분 간격으로 보관해 최악 RPO 2분이다. Firestore PITR은 기본 비활성이고 7일 창, 분 단위다.
- **실패 양상:** 오후 3시의 잘못된 배치가 데이터를 덮었는데 마지막 백업이 새벽 3시라 12시간치 정상 쓰기를 함께 잃는다.
- **신호:** 🟢 RDS는 `backup_retention_period > 0`이면 PITR 가능. Cloud SQL `backup_configuration.point_in_time_recovery_enabled`. Firestore `google_firestore_database.point_in_time_recovery_enablement = "POINT_IN_TIME_RECOVERY_ENABLED"`. 🔴 Supabase PITR 애드온 여부는 코드에 없음.
- **시나리오·수준:** D L2 이상 (L2 가정 RPO 5분). Supabase 체크리스트는 DB가 4GB를 넘을 것으로 예상되면 PITR을 권장.
- **처방:** 티어0: Supabase PITR 애드온(7일 보존 약 월 $100, Small 컴퓨트 이상 필요), Firestore PITR 활성. 티어1·2: RDS 자동 백업(PITR 포함), Cloud SQL PITR 활성.
- **검증:** "N분 전 시점"으로 새 인스턴스 복원 후 마지막 행의 타임스탬프로 실제 RPO 측정.
- **비용 영향:** 증가. Supabase는 7일 약 $100/월, 14일 약 $200/월, 28일 약 $400/월. Firestore는 PITR 저장량에 무료 등급이 없다.
- **출처:** https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PIT.html · https://supabase.com/docs/guides/platform/backups · https://firebase.google.com/docs/firestore/pitr (2026-10-01)

### D-005 DB 백업에 오브젝트 파일이 포함되지 않음
- **무엇/왜:** Supabase 백업은 Storage API로 저장한 객체를 포함하지 않는다(DB에는 메타데이터만 있음). S3·GCS 버킷도 DB 스냅샷과 별개다. 파일과 메타데이터의 백업 시점이 어긋나면 복원 후 깨진 링크가 생긴다.
- **실패 양상:** 버킷을 실수로 비웠는데 DB 백업만 있어 파일을 되살릴 수 없다. DB를 어제로 되돌리면 오늘 올린 파일은 고아 객체가 된다.
- **신호:** 🟢 `supabase.storage.from(...).upload`, `PutObjectCommand`, `bucket.upload_blob`. 🟢 Terraform에 버킷은 있는데 `aws_s3_bucket_versioning`·`aws_backup_plan` 대상에 버킷이 없음.
- **시나리오·수준:** D L1 이상 (사용자 업로드가 있을 때)
- **처방:** 티어0: Supabase Storage는 주기적으로 외부 버킷으로 복사(rclone 등). 티어1·2: 버킷 버저닝(D-006) + AWS Backup의 S3 백업 또는 교차 리전 복제.
- **검증:** 복원 리허설에서 DB 행이 가리키는 객체 키가 모두 존재하는지 샘플 대조.
- **비용 영향:** 증가. 파일 사본만큼 저장 비용.
- **출처:** https://supabase.com/docs/guides/platform/backups (2026-10-01)

### D-006 오브젝트 스토리지 버저닝·소프트 삭제
- **무엇/왜:** S3 버저닝은 기본 비활성이며 켜면 삭제가 삭제 마커로 바뀌고 덮어쓰기도 이전 버전을 남긴다. GCS 소프트 삭제는 지원 버킷에 기본 활성, 기본 7일(7~90일 설정, 0이면 끔)이다.
- **실패 양상:** 코드 버그로 같은 키에 빈 파일을 덮어쓰거나 `DeleteObjects`로 접두어 전체를 지우면 영구 손실.
- **신호:** 🟢 `aws_s3_bucket_versioning { status = "Enabled" }` 없음, `google_storage_bucket.soft_delete_policy.retention_duration_seconds = 0`, `versioning { enabled = true }` 유무.
- **시나리오·수준:** D L1 이상 (업로드가 사용자 데이터일 때)
- **처방:** 티어1·2: S3 버저닝 + 비현재 버전 만료 수명 주기 규칙(`noncurrent_version_expiration`), GCS 소프트 삭제 유지 또는 버저닝.
- **검증:** 테스트 객체 삭제 후 이전 버전 복구 스크립트 실행.
- **비용 영향:** 증가. 각 버전은 차분이 아니라 객체 전체로 과금된다. 임시 데이터가 많은 버킷의 소프트 삭제는 비용을 크게 늘릴 수 있다(GCS 문서 경고).
- **출처:** https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html · https://docs.cloud.google.com/storage/docs/soft-delete (2026-10-01)

### D-007 백업 암호화와 접근 분리
- **무엇/왜:** 백업은 운영 데이터와 같은 권한으로 지울 수 있으면 안 된다. Well-Architected는 "백업과 복원 자동화에 데이터와 같은 접근 권한을 갖는 것", "운영과 백업이 같은 보안 도메인"을 안티패턴으로 든다. RDS는 DB가 암호화되어 있으면 백업도 암호화된다.
- **실패 양상:** 유출된 운영 자격 증명 하나로 DB와 스냅샷을 모두 삭제당한다.
- **신호:** 🟢 `aws_db_instance.storage_encrypted`, `kms_key_id`, 앱 IAM 역할에 `rds:DeleteDBSnapshot`·`backup:DeleteRecoveryPoint`·`s3:DeleteObjectVersion` 권한. 🟡 CI 토큰 권한 범위.
- **시나리오·수준:** D L2 이상 (보안 카탈로그와 겹침, 여기서는 "백업 삭제 가능성"만)
- **처방:** 티어1·2: 백업 삭제 권한을 앱·CI 역할에서 제거, 백업 볼트 접근 정책으로 거부.
- **검증:** 앱 역할로 스냅샷 삭제를 시도해 거부되는지 IAM 정책 시뮬레이터로 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_backing_up_data_secured_backups_data.html (2026-10-01)

### D-008 불변(WORM) 백업 — 랜섬웨어·악의적 삭제 대비
- **무엇/왜:** AWS Backup Vault Lock 규정 준수 모드는 유예 기간(최소 3일=72시간)이 지나면 루트 사용자와 AWS도 잠금을 풀거나 보존 기간 전 백업을 지울 수 없다. S3 Object Lock 규정 준수 모드도 루트 포함 누구도 보존 기간 중 덮어쓰기·삭제를 못 한다(버저닝 필수).
- **실패 양상:** 계정 탈취 후 공격자가 운영 DB와 모든 백업을 지우고 몸값을 요구한다.
- **신호:** 🟢 `aws_backup_vault_lock_configuration`(`changeable_for_days` 있으면 규정 준수 모드), `aws_s3_bucket_object_lock_configuration`, GCS `retention_policy.is_locked`. 🔴 대부분 앱 저장소엔 없음.
- **시나리오·수준:** D L3 또는 결제·의료 등 C L3 데이터 (바이브코더 앱 L1·L2에는 과잉일 수 있음)
- **처방:** 티어1·2: 백업 전용 볼트에 Vault Lock(먼저 거버넌스 모드로 시험), 최소·최대 보존 일수 설정.
- **검증:** 잠긴 볼트의 복구 지점 삭제 시도가 거부되는지 확인(`DescribeBackupVault`의 `Locked: true`).
- **비용 영향:** 증가. 잠금 자체는 무료지만 보존 기간 동안 저장 비용을 줄일 수 없다. 보존 "Always" 복구 지점은 영구 과금이 된다.
- **출처:** https://docs.aws.amazon.com/aws-backup/latest/devguide/vault-lock.html · https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html (2026-10-01)

### D-009 교차 계정·논리적 에어갭 백업
- **무엇/왜:** AWS DR 백서는 교차 계정 백업이 내부자 위협과 계정 탈취를 막는다고 설명하고, Well-Architected는 AWS Backup 논리적 에어갭 볼트로 운영과 백업 환경을 분리하라고 권한다.
- **실패 양상:** 결제 미납·계정 정지·계정 탈취로 계정 하나가 통째로 사라지면 그 안의 백업도 함께 사라진다.
- **신호:** 🟢 `aws_backup_plan` 규칙의 `copy_action.destination_vault_arn`이 다른 계정 ARN인지. 🔴 단일 계정 운영은 코드로 거의 확정 불가.
- **시나리오·수준:** D L3 (L2는 선택)
- **처방:** 티어1·2: 백업 전용 계정으로 copy action. 티어0: 주기 덤프를 다른 클라우드 계정의 버킷에 보관.
- **검증:** 백업 계정에서 단독으로 복원 리허설.
- **비용 영향:** 증가. 사본 저장 + 계정 간 전송.
- **출처:** https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html · https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_backing_up_data_secured_backups_data.html (2026-10-01)

### D-010 백업의 교차 리전 사본
- **무엇/왜:** 같은 리전에만 있는 백업은 리전 장애 때 복원에 쓸 수 없다. AWS Backup은 백업을 다른 리전으로 복사할 수 있고, RDS 자동 백업을 다른 리전으로 복제해 두면 원본 DB를 지울 때 "자동 백업 보존"을 고르지 않아도 그 사본은 남는다.
- **실패 양상:** 리전 장애가 길어지는데 백업이 그 리전에 묶여 다른 리전에서 복원하지 못한다.
- **신호:** 🟢 `aws_db_instance_automated_backups_replication`, `aws_backup_plan.rule.copy_action`, Cloud SQL 백업 위치 설정(`backup_configuration.location`).
- **시나리오·수준:** D L3 (백업·복원형 리전 DR의 최소 조건)
- **처방:** 티어1·2: 백업 복사 규칙 추가. 티어0: Supabase 덤프를 다른 리전 버킷에 보관.
- **검증:** 다른 리전에서 복원 리허설, 소요 시간을 RTO와 비교.
- **비용 영향:** 증가. 사본 저장 + 리전 간 전송.
- **출처:** https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html · https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_DeleteInstance.html (2026-10-01)

### D-011 삭제 보호와 최종 스냅샷
- **무엇/왜:** RDS는 콘솔로 만든 인스턴스만 삭제 보호가 기본으로 켜진다. Cloud SQL 삭제 보호는 콘솔이나 Terraform으로 만들 때만 기본 활성이다. Terraform `skip_final_snapshot = true`는 `terraform destroy` 한 번에 DB를 스냅샷 없이 지운다.
- **실패 양상:** 잘못된 워크스페이스에서 `terraform destroy`, 리소스 이름 변경으로 인한 교체(replace)가 운영 DB를 삭제한다.
- **신호:** 🟢 `aws_db_instance.deletion_protection`(없거나 false), `skip_final_snapshot = true`, `google_sql_database_instance.deletion_protection = false`, `settings.deletion_protection_enabled`, `lifecycle { prevent_destroy = true }` 부재.
- **시나리오·수준:** D L1 이상 (Terraform이 있을 때)
- **처방:** 티어1·2: `deletion_protection = true`, `skip_final_snapshot = false` + `final_snapshot_identifier`, 중요 리소스에 `prevent_destroy`.
- **검증:** 정적 검사 + `terraform plan`에서 DB가 `destroy`/`replace`로 표시되면 CI 실패.
- **비용 영향:** 중립(최종 스냅샷 보관 비용 소폭).
- **출처:** https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_DeleteInstance.html · https://docs.cloud.google.com/sql/docs/postgres/deletion-protection (2026-10-01)

### D-012 DB 삭제 시 자동 백업도 사라짐
- **무엇/왜:** RDS에서 "자동 백업 보존"을 고르지 않고 지우면 같은 리전의 자동 백업이 함께 삭제되어 복구할 수 없다(수동 스냅샷은 남음). Cloud SQL도 자동 백업은 인스턴스 삭제 후 하루에 하나씩 순차 삭제되고, 보존 백업 기능을 써야 남는다.
- **실패 양상:** "DB만 지웠다"고 생각했는데 백업까지 같이 사라졌다.
- **신호:** 🟢 Terraform `delete_automated_backups`(기본 true), 정기 수동 스냅샷 자동화 부재.
- **시나리오·수준:** D L1 이상
- **처방:** 티어1·2: `delete_automated_backups = false`, 교차 리전 백업 복제(D-010), AWS Backup 별도 볼트.
- **검증:** 정적 검사.
- **비용 영향:** 증가(소폭). 보존 백업이 과금된다.
- **출처:** https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_DeleteInstance.html · https://docs.cloud.google.com/sql/docs/postgres/backup-recovery/backups (2026-10-01)

### D-013 클러스터 안 자체 운영 DB와 PV 회수 정책
- **무엇/왜:** k8s StatefulSet으로 Postgres·Redis를 돌리면 백업은 전적으로 사용자 책임이다. 동적 프로비저닝된 PV의 기본 회수 정책은 `Delete`라서 PVC를 지우면 디스크도 지워진다.
- **실패 양상:** 네임스페이스 정리나 `kubectl delete -k`로 PVC가 지워지며 DB 디스크가 함께 삭제된다. 백업 CronJob이 없으면 복구 수단이 없다.
- **신호:** 🟢 `kind: StatefulSet` + `image: postgres`/`redis`, `volumeClaimTemplates`, StorageClass `reclaimPolicy` 미지정(기본 Delete), `CronJob`으로 `pg_dump` 부재. 예시 앱 simple-web-app은 클러스터 내 StatefulSet을 로컬 overlay에만 쓰고 클라우드는 매니지드로 분리했다(좋은 사례).
- **시나리오·수준:** D L1 이상에서 운영 환경이 클러스터 내 DB면 결함
- **처방:** 티어2: 운영은 RDS·Cloud SQL로 이전(설계 문서 D-PRE 계열), 불가하면 `reclaimPolicy: Retain` StorageClass + `pg_dump`/WAL 아카이빙 CronJob → 오브젝트 스토리지.
- **검증:** PVC 삭제 시뮬레이션(스테이징), 덤프 복원 리허설.
- **비용 영향:** 매니지드 이전은 증가, 대신 운영 부담 감소.
- **출처:** https://kubernetes.io/docs/concepts/storage/persistent-volumes/ (2026-10-01)

### D-014 컨테이너 로컬 디스크·SQLite·서버리스 /tmp에 영속 데이터
- **무엇/왜:** 컨테이너 파일 시스템, Cloud Run·Vercel 함수의 임시 디스크는 인스턴스와 함께 사라진다. SQLite 파일 DB는 인스턴스가 여러 개면 각자 다른 DB가 된다.
- **실패 양상:** 재배포·스케일 인·인스턴스 교체 때마다 데이터 소실. 인스턴스 2개면 사용자마다 다른 데이터가 보인다.
- **신호:** 🟢 `sqlite3`, `better-sqlite3`, `DATABASE_URL=file:`, Prisma `provider = "sqlite"`, `fs.writeFile`로 `uploads/` 저장, Dockerfile `VOLUME` 없이 쓰기.
- **시나리오·수준:** D L1 이상 (설계 문서 D-PRE-001·002와 같은 결함의 D 측 설명)
- **처방:** 티어0: Supabase/Neon 등 매니지드 Postgres, 오브젝트 스토리지. 티어1·2: 매니지드 DB + S3/GCS.
- **검증:** 인스턴스 강제 재시작 후 데이터 유지 확인.
- **비용 영향:** 증가(매니지드 DB 비용).
- **출처:** 일반 원칙(출처 미확인 — 설계 문서 S1 Twelve-Factor 참조) ⚠️근거없음

### D-015 Redis를 유일한 저장소로 쓰는 데이터의 내구성
- **무엇/왜:** 세션·글쓰기 큐·레이트 리밋 카운터를 Redis에만 두면 Redis 장애가 데이터 손실이 된다. ElastiCache·Memorystore 모두 복제가 비동기라 페일오버 때 확인 응답을 받은 쓰기가 사라질 수 있다. Memorystore Basic 등급은 복제·자동 페일오버가 없다. 복제본이 없는 ElastiCache 기본 노드가 죽으면 새 노드는 빈 상태로 시작한다.
- **실패 양상:** 큐에만 있던 미처리 글쓰기 수천 건이 페일오버와 함께 사라지는데 클라이언트는 이미 `202`를 받았다. 메모리 부족 시 축출 정책 때문에 큐 항목이 지워진다.
- **신호:** 🟢 `XADD`/`LPUSH`로 쓰기를 접수하고 DB 반영은 워커가 함, BullMQ·Celery(Redis 브로커)·RQ. 🟢 Terraform `aws_elasticache_replication_group.num_cache_clusters = 1`, `google_redis_instance.tier = "BASIC"`, `maxmemory-policy`가 `noeviction`이 아님. 예시 앱은 `noeviction`을 배포 계약으로 명시.
- **시나리오·수준:** D L2 이상 (C L2와 겹침: 유실 허용 여부는 C가 판단)
- **처방:** 티어1·2: 복제본 1개 이상 + Multi-AZ, `noeviction`, 접수 응답 문구를 "접수됨(pending)"으로 하고 유실 감지(D-070). 유실 불가 데이터는 SQS 같은 내구성 큐나 DB로.
- **검증:** ElastiCache `test-failover`(24시간당 최대 15개 샤드) 중 쓰기를 넣고 유실 건수 측정.
- **비용 영향:** 증가. 복제본 노드만큼.
- **출처:** https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/AutoFailover.html · https://docs.cloud.google.com/memorystore/docs/redis/high-availability-for-memorystore-for-redis (2026-10-01)

### D-016 코드·설정·IaC도 복구 대상
- **무엇/왜:** 데이터만 있고 인프라를 다시 만들 방법이 없으면 RTO를 지킬 수 없다. AWS DR 백서는 백업·복원 전략에서도 IaC로 배포해야 복구 리전에서 빠르고 오류 없이 재배포할 수 있다고 한다.
- **실패 양상:** 콘솔로 손으로 만든 VPC·보안 그룹·환경 변수를 기억에 의존해 다시 만드느라 몇 시간이 간다.
- **신호:** 🟢 Terraform/CDK/Pulumi 디렉터리 유무, 🟡 README에 "콘솔에서 생성" 문구. 🔴 콘솔 생성 리소스.
- **시나리오·수준:** D L2 이상 (L1은 플랫폼 재배포로 충분한 경우가 많음)
- **처방:** 티어0: `vercel.json`, `supabase/migrations`, `firebase.json`을 저장소에 둠. 티어1·2: 전 인프라 IaC화(P3 산출물).
- **검증:** 빈 계정·프로젝트에 IaC만으로 재구축 리허설, 소요 시간 측정.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html (2026-10-01)

## 2. 복원·PITR·데이터 손상 대응

### D-017 정기 복원 리허설
- **무엇/왜:** 백업은 복원해 봐야 백업이다. Well-Architected 안티패턴: 복원만 하고 데이터를 조회해 보지 않음, 백업이 존재한다고 가정함, 복원 시간이 RTO 안이라고 가정함, 런북 없이 복원함.
- **실패 양상:** 장애 당일 처음 복원해 보니 확장 기능 누락·권한 오류·KMS 키 접근 거부로 실패하거나 RTO를 몇 배 넘긴다.
- **신호:** 🟡 `scripts/restore*`, `docs/runbook*`, CI 스케줄 워크플로(`on: schedule`)에 복원 작업. 🟢 `aws_backup_restore_testing_plan`. 🔴 대부분 없음 → "리허설 없음" 가정.
- **시나리오·수준:** D L2 이상 필수, L1은 최소 1회 (설계 문서 D-CTL-006)
- **처방:** 티어0: 분기마다 Supabase 백업을 새 프로젝트로 복원 + 스모크 쿼리. 티어1·2: AWS Backup 복원 테스트 계획(주기 실행, 검증 후 자동 삭제, 검증용 보존 1~168시간).
- **검증:** P4 복원 리허설: 복원 → 행 수·최신 타임스탬프·체크섬 대조 → 소요 시간 기록.
- **비용 영향:** 증가(소폭). 복원 테스트당 요금과 임시 인스턴스 비용.
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_backing_up_data_periodic_recovery_testing_data.html · https://docs.aws.amazon.com/aws-backup/latest/devguide/restore-testing.html (2026-10-01)

### D-018 복원 소요 시간을 RTO와 비교
- **무엇/왜:** 복원 시간은 DB 크기에 비례한다. Supabase는 복원 중 다운타임이 DB 크기에 따라 길어진다고 명시한다. RDS PITR 인스턴스는 사용 가능 상태가 된 뒤에도 S3에서 블록을 백그라운드로 불러오는 동안 성능이 완전하지 않다.
- **실패 양상:** 데이터가 커지면서 복원이 4시간을 넘어 D L1 가정 RTO를 조용히 깬다. 복원 직후 느린 디스크 때문에 트래픽을 받으면 또 장애가 난다.
- **신호:** 🔴 DB 크기·복원 시간은 코드에 없음 → 가정. 🟡 마이그레이션 수·테이블 수로 규모 추정.
- **시나리오·수준:** D L1 이상
- **처방:** 모든 티어: 리허설 결과를 리포트의 "실측 RTO"로 기록, 가정 RTO 초과 시 PITR·대기 복제본(D-030)으로 상향.
- **검증:** 리허설에서 복원 시작~검증 완료까지 측정.
- **비용 영향:** 중립(측정 자체).
- **출처:** https://supabase.com/docs/guides/platform/backups · https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PIT.html (2026-10-01)

### D-019 PITR은 새 인스턴스로 복원된다 — 전환 절차
- **무엇/왜:** RDS PITR은 원본을 바꾸지 않고 새 인스턴스를 만든다. 기본 파라미터 그룹·옵션 그룹이 붙는다. 따라서 접속 문자열(비밀), 보안 그룹, 파라미터 그룹을 바꾸는 전환 절차가 필요하다.
- **실패 양상:** 복원은 끝났는데 앱이 여전히 손상된 원본을 보고 있거나, 기본 파라미터 그룹 때문에 `max_connections`가 달라 연결 폭주가 난다.
- **신호:** 🟢 DB 엔드포인트가 코드·매니페스트에 하드코딩, 🟢 Secret(`DATABASE_URL`)을 Terraform이 생성. 🟡 커스텀 파라미터 그룹(`aws_db_parameter_group`) 존재.
- **시나리오·수준:** D L2 이상
- **처방:** 티어1·2: 엔드포인트는 Secret/DNS CNAME 한 곳에서만 바꾸게, 복원 런북에 파라미터 그룹 지정 포함.
- **검증:** 리허설에서 앱을 복원 인스턴스로 전환하고 스모크 테스트.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PIT.html (2026-10-01)

### D-020 복제는 논리적 손상을 막지 못한다
- **무엇/왜:** 동기·비동기 복제는 잘못된 `DELETE`, 버그 있는 마이그레이션, 악의적 삭제까지 즉시 복제한다. AWS DR 백서는 연속 복제가 데이터 손상·악의적 삭제를 시점 백업만큼 막지 못하며, 액티브-액티브에서도 데이터 손상 복구는 백업에 의존해 RPO가 0이 아니라고 말한다.
- **실패 양상:** Multi-AZ·교차 리전 복제본이 모두 같은 손상 상태가 된다. "HA가 있으니 백업은 덜 중요"라는 판단이 틀린다.
- **신호:** 🟢 Multi-AZ·복제본은 있는데 PITR·백업 보존이 짧음(D-002·004와 조합 규칙). 🟢 마이그레이션 디렉터리에 `DROP`/`DELETE` 포함.
- **시나리오·수준:** D L2 이상
- **처방:** 모든 티어: HA와 별개로 PITR 유지, S3 복제 시 삭제 마커는 기본적으로 복제되지 않음을 활용.
- **검증:** 스테이징에서 테이블을 지운 뒤 PITR로 손상 직전 시점 복구 리허설.
- **비용 영향:** 중립(이미 있는 백업 활용).
- **출처:** https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html (2026-10-01)

### D-021 위험 작업 전 온디맨드 백업
- **무엇/왜:** 대규모 마이그레이션·일괄 수정 직전에 수동 백업을 떠 두면 자동 백업 주기와 무관한 복원 지점이 생긴다. Cloud SQL 문서는 온디맨드 백업이 위험한 작업 직전에 유용하며 수동 삭제 전까지 보관된다고 한다.
- **실패 양상:** 마이그레이션 실패 후 가장 가까운 복원 지점이 수 시간 전이다.
- **신호:** 🟢 마이그레이션 실행 단계(`prisma migrate deploy`, `alembic upgrade`, k8s Job `db-migrate`) 앞에 스냅샷 단계가 없음.
- **시나리오·수준:** D L2 이상 (U 카탈로그의 마이그레이션 항목과 연결)
- **처방:** 티어1·2: 배포 파이프라인에서 마이그레이션 전 `aws rds create-db-snapshot`/`gcloud sql backups create`. 티어0: `supabase db dump`.
- **검증:** 파이프라인 정적 검사.
- **비용 영향:** 증가(소폭). 수동 스냅샷은 지울 때까지 과금 — 보존 정책 필요.
- **출처:** https://docs.cloud.google.com/sql/docs/postgres/backup-recovery/backups (2026-10-01)

### D-022 부분 복원(선택적 데이터 이식) 런북
- **무엇/왜:** 손상이 테이블 하나·사용자 몇 명에 국한될 때 DB 전체를 되돌리면 그 사이 정상 쓰기를 잃는다. 복원 인스턴스를 옆에 띄우고 필요한 행만 옮기는 절차가 필요하다.
- **실패 양상:** 한 사용자 데이터 복구를 위해 전체 서비스를 몇 시간 전으로 되돌린다.
- **신호:** 🔴 런북 없음. 🟡 다중 테넌트 키(`org_id`, `tenant_id`) 존재 시 부분 복원 필요성 큼.
- **시나리오·수준:** D L2 이상
- **처방:** 모든 티어: "PITR로 별도 인스턴스 → 대상 행 추출(`COPY`) → 운영에 upsert" 런북.
- **검증:** 리허설에서 특정 사용자 데이터만 복구.
- **비용 영향:** 중립(임시 인스턴스 시간만).
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### D-023 앱 수준 소프트 삭제·감사 이력
- **무엇/왜:** 사용자의 실수 삭제는 인프라 복원보다 앱 수준 휴지통(`deleted_at`)으로 푸는 편이 RTO가 짧다. 인프라 백업은 최후 수단이 된다.
- **실패 양상:** "어제 지운 글 살려주세요" 요청마다 DB 복원이 필요하다.
- **신호:** 🟢 스키마에 `deleted_at`·`is_deleted` 유무, `DELETE FROM` 직접 사용.
- **시나리오·수준:** D L1 이상 (권장), 개인정보 삭제 의무와 충돌 여부는 보안·규제 카탈로그가 판단
- **처방:** 모든 티어: 사용자 생성 데이터에 소프트 삭제 + 보존 기간 뒤 영구 삭제 잡.
- **검증:** 삭제→복구 API 테스트.
- **비용 영향:** 중립(저장량 소폭 증가).
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### D-024 백업 무결성 검증 기준
- **무엇/왜:** 복원에 "성공"해도 데이터가 비었거나 일부 테이블이 빠질 수 있다. Well-Architected는 데이터 종류별 검증 기준(형식, 체크섬, 크기, 커스텀 로직)을 정하고 복원 결과가 RPO 안의 최신 레코드를 담는지 확인하라고 한다.
- **실패 양상:** 몇 달째 빈 덤프가 "성공"으로 쌓이고 있었다(예: `pg_dump` 연결 실패가 0바이트 파일로 끝남).
- **신호:** 🟢 덤프 스크립트에 `set -e`·크기 검사·종료 코드 확인 부재. 🔴 검증 기준 없음.
- **시나리오·수준:** D L1 이상 (자체 덤프를 쓸 때 특히)
- **처방:** 모든 티어: 복원 후 테이블별 행 수, 최대 `created_at`, 핵심 테이블 체크섬을 비교하는 검증 스크립트.
- **검증:** 리허설 자동화에 포함, 실패 시 알림.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_backing_up_data_periodic_recovery_testing_data.html (2026-10-01)

## 3. 단일 장애점과 존(AZ) 장애

### D-025 단일 인스턴스·단일 레플리카
- **무엇/왜:** 앱이 Pod·태스크·VM 하나로만 돌면 그 하나의 재시작·노드 장애·배포가 곧 전면 장애다. EKS 모범 사례는 싱글턴 Pod를 피하고 Deployment로 여러 레플리카를 돌리라고 한다.
- **실패 양상:** 노드 교체·커널 패닉·OOM 한 번에 수십 초~수 분 다운. HPA `minReplicas: 1`이면 평시 야간에 레플리카 1개로 줄어 같은 위험.
- **신호:** 🟢 `replicas: 1`(또는 생략), HPA `minReplicas: 1`, `kind: Pod` 직접 배포, ECS `desired_count = 1`, Cloud Run `min_instance_count`는 무관(플랫폼이 재기동). 🟢 docker-compose 단일 서비스로 운영.
- **시나리오·수준:** D L2 이상 (L1은 플랫폼 자동 재기동으로 충분할 수 있음)
- **처방:** 티어0: 해당 없음(플랫폼 관리). 티어1: ECS `desired_count >= 2`. 티어2: `replicas >= 2`, HPA `minReplicas >= 2`.
- **검증:** Pod/태스크 하나 강제 종료 중 요청 오류율 측정(P4 장애 주입).
- **비용 영향:** 증가. 상시 인스턴스 1개 추가.
- **출처:** https://docs.aws.amazon.com/eks/latest/best-practices/application.html (2026-10-01)

### D-026 Pod 존 분산(topologySpreadConstraints)
- **무엇/왜:** 레플리카가 여러 개여도 같은 존·같은 노드에 몰리면 존 장애에 무력하다. `topologyKey: topology.kubernetes.io/zone`, `maxSkew: 1`로 분산한다. `whenUnsatisfiable` 기본값은 `DoNotSchedule`이며, 스케일 인 후에는 분포가 다시 치우칠 수 있다(문서의 알려진 한계).
- **실패 양상:** 존 하나가 죽자 레플리카 3개가 전부 그 존에 있어 전면 장애.
- **신호:** 🟢 `topologySpreadConstraints`·`podAntiAffinity`(`topology.kubernetes.io/zone`) 부재. 🟡 클러스터 기본 분산 제약 설정 여부(관리형마다 다름).
- **시나리오·수준:** D L2 이상 (설계 문서 D-CTL-003)
- **처방:** 티어1: ECS·Cloud Run은 플랫폼이 존 분산(D-029, D-052). 티어2: Deployment마다 존·노드 두 단계 분산, 레플리카 수가 적으면 `ScheduleAnyway`로 배치 실패 방지.
- **검증:** 정적 검사 + `kubectl get pods -o wide`로 존 분포 확인 + 존 하나의 노드 cordon/drain 실험.
- **비용 영향:** 증가(소폭). AZ 간 전송 요금과 존별 노드 여유.
- **출처:** https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/ · https://docs.aws.amazon.com/eks/latest/best-practices/application.html (2026-10-01)

### D-027 노드 그룹·서브넷이 단일 존
- **무엇/왜:** Pod 분산 제약이 있어도 노드 그룹이 한 존 서브넷에만 있으면 분산할 곳이 없다. DB 서브넷 그룹·ALB 서브넷도 둘 이상의 존이어야 한다.
- **실패 양상:** 분산 제약이 `DoNotSchedule`이면 Pod가 Pending, `ScheduleAnyway`면 한 존에 몰린다.
- **신호:** 🟢 `aws_eks_node_group.subnet_ids`가 1개, `aws_subnet`의 `availability_zone`이 하나뿐, GKE `node_locations` 1개, `aws_db_subnet_group` 서브넷 1개.
- **시나리오·수준:** D L2 이상
- **처방:** 티어1·2: 최소 2개(권장 3개) 존 서브넷, 노드 그룹을 존마다 두거나 다중 존 그룹.
- **검증:** 정적 검사(Terraform plan의 AZ 집합 크기).
- **비용 영향:** 증가(소폭). 존별 최소 노드.
- **출처:** 일반 원칙(출처 미확인) — EKS 모범 사례의 "여러 AZ에서 실행" 권고와 같은 맥락(https://docs.aws.amazon.com/eks/latest/best-practices/application.html, 2026-10-01) ⚠️근거없음

### D-028 GKE 존 클러스터 vs 리전 클러스터
- **무엇/왜:** GKE 리전 클러스터는 컨트롤 플레인을 리전 전체에 복제해 존 하나가 죽어도 컨트롤 플레인이 영향받지 않고, 업그레이드 중에도 API를 쓸 수 있다. 기본적으로 노드를 3개 존에 분산한다. 문서는 운영 워크로드에 리전 클러스터를 권한다.
- **실패 양상:** 존 클러스터의 존이 죽거나 컨트롤 플레인 업그레이드 중이면 HPA·배포·자가 치유가 멈춘다.
- **신호:** 🟢 `google_container_cluster.location`이 존(`asia-northeast3-a`)인지 리전(`asia-northeast3`)인지.
- **시나리오·수준:** D L2 이상 (티어2 GKE일 때). EKS 컨트롤 플레인은 AWS 관리(별도 판정 불필요).
- **처방:** 티어2: GKE 리전 클러스터(또는 Autopilot).
- **검증:** 정적 검사.
- **비용 영향:** 증가. 존 간 노드 트래픽 과금, 리전 쿼터를 더 씀. 클러스터 관리비 차이는 설계 문서 S5 참조.
- **출처:** https://docs.cloud.google.com/kubernetes-engine/docs/concepts/regional-clusters (2026-10-01)

### D-029 ECS 서비스의 존 분산·리밸런싱
- **무엇/왜:** Fargate는 접근 가능한 존에 태스크를 최선 노력으로 분산한다. 2025-09-05부터 자격 있는 서비스에 AZ 리밸런싱이 켜진다(생성 시 기본 `ENABLED`, 갱신 시 이전 값이 없으면 `DISABLED`로 취급). `maximumPercent = 100`이면 리밸런싱을 쓸 수 없다.
- **실패 양상:** 존 장애 후 태스크가 한쪽 존에 몰린 채 남아 다음 장애에 취약.
- **신호:** 🟢 `aws_ecs_service.availability_zone_rebalancing`, `deployment_maximum_percent = 100`, 서비스 서브넷 1개.
- **시나리오·수준:** D L2 이상 (티어1 ECS)
- **처방:** 티어1: 서브넷 2개 이상, `desired_count >= 2`, 리밸런싱 `ENABLED`.
- **검증:** 한 존 서브넷의 태스크를 중지시키고 재분산 관찰.
- **비용 영향:** 중립(리밸런싱 중 일시 증가).
- **출처:** https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-rebalancing.html (2026-10-01)

### D-030 DB Multi-AZ / 리전 HA
- **무엇/왜:** RDS Multi-AZ는 다른 존에 동기 대기 복제본을 두고 자동 페일오버하며, 페일오버는 보통 60~120초다. Cloud SQL HA는 두 존의 디스크에 쓰기가 복제된 뒤 커밋을 보고하고, 페일오버 중 약 60초 사용 불가, 같은 IP를 유지한다. Cloud SQL은 기본이 존(단독) 인스턴스다.
- **실패 양상:** 단일 존 DB의 존이 죽으면 백업 복원까지 수십 분~수 시간 다운(D L2 가정 RTO 30분 위반 가능).
- **신호:** 🟢 `aws_db_instance.multi_az`, `google_sql_database_instance.settings.availability_type = "REGIONAL"`. 🔴 Supabase는 이 범위 문서에서 Multi-AZ 옵션을 확인하지 못함 → 가정.
- **시나리오·수준:** D L2 이상 (설계 문서 D-CTL-002)
- **처방:** 티어1·2: RDS `multi_az = true`, Cloud SQL `REGIONAL`. 티어0: 플랫폼 HA 지원 여부를 가정으로 표시, D L2 이상이면 티어1 DB 검토.
- **검증:** RDS "reboot with failover"·Cloud SQL 수동 페일오버 중 앱 오류율과 복구 시간 측정(D-116).
- **비용 영향:** 증가. Cloud SQL HA는 단독 인스턴스의 2배(CPU·메모리·스토리지). RDS Multi-AZ도 대기 인스턴스 비용이 더해진다. 동기 복제로 쓰기 지연도 늘 수 있다.
- **출처:** https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZSingleStandby.html · https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZ.Failover.html · https://docs.cloud.google.com/sql/docs/postgres/high-availability (2026-10-01)

### D-031 Multi-AZ 대기 인스턴스는 읽기 용량이 아니다
- **무엇/왜:** RDS Multi-AZ 인스턴스 배포의 대기 복제본은 읽기 트래픽을 받을 수 없다. 읽기 확장은 읽기 복제본이나 Multi-AZ DB 클러스터가 맡는다. 반대로 읽기 복제본은 비동기라 HA 대체가 아니다.
- **실패 양상:** "Multi-AZ니까 읽기도 분산된다"는 오해로 용량 계획이 틀리거나, "읽기 복제본이 있으니 HA"라고 판정해 페일오버가 수동·지연된다.
- **신호:** 🟢 `multi_az = true`만 있고 `replicate_source_db` 없음 + 읽기 부하 큼(T 신호), 또는 복제본만 있고 `multi_az = false`.
- **시나리오·수준:** D L2 이상 (T 카탈로그와 연결)
- **처방:** 티어1·2: HA는 Multi-AZ, 읽기 확장은 복제본으로 분리 판정.
- **검증:** 정적 검사.
- **비용 영향:** 중립(판정 오류 방지).
- **출처:** https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZSingleStandby.html (2026-10-01)

### D-032 DB 페일오버 후 재연결
- **무엇/왜:** RDS 페일오버는 DB 인스턴스의 DNS 레코드를 대기 쪽으로 바꾸므로 기존 연결은 다시 맺어야 한다. AWS는 JVM DNS 캐시 TTL을 60초 이하로 권하며, 일부 JVM 설정은 재시작 전까지 DNS를 갱신하지 않는다. 커넥션 풀도 죽은 연결을 버리고 재연결해야 한다.
- **실패 양상:** DB는 60초 만에 복구됐는데 앱은 옛 IP의 죽은 연결을 계속 붙잡아 수십 분 오류. 결국 수동 재시작.
- **신호:** 🟢 Java `networkaddress.cache.ttl` 미설정·무한, 커넥션 풀 `pool_pre_ping`(SQLAlchemy)·`testOnBorrow`·`idleTimeoutMillis` 부재, DB IP 하드코딩. 🟢 RDS Proxy 사용 여부.
- **시나리오·수준:** D L2 이상
- **처방:** 티어1·2: 엔드포인트 DNS 이름 사용, 풀 상태 검사(pre-ping), 연결 수명 제한, JVM TTL 60초. Cloud SQL HA는 IP가 유지되어 DNS 문제는 적지만 재연결은 여전히 필요.
- **검증:** 페일오버 주입 중 "DB 복구 시각 → 앱 오류율 정상화 시각" 차이를 측정.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZ.Failover.html · https://docs.cloud.google.com/sql/docs/postgres/high-availability (2026-10-01)

### D-033 캐시·큐(Redis) 고가용성
- **무엇/왜:** ElastiCache Multi-AZ는 다른 존에 복제본이 1개 이상 있어야 하며, 기본 노드 장애 시 복제 지연이 가장 적은 복제본을 몇 초 안에 승격한다. 클러스터 모드 활성은 Multi-AZ가 기본이다. Memorystore Standard 등급은 복제·자동 페일오버를 제공하며 자동 복구 중 평균 30초, 유지 보수 때 15초 사용 불가다.
- **실패 양상:** 단일 노드 Redis가 죽으면 세션 전체 로그아웃, 큐 정지, 캐시 소실로 DB 쇄도(D-080).
- **신호:** 🟢 `aws_elasticache_replication_group.automatic_failover_enabled`, `multi_az_enabled`, `num_cache_clusters`, `aws_elasticache_cluster`(단일 노드), `google_redis_instance.tier`.
- **시나리오·수준:** D L2 이상 (Redis가 세션·큐 등 하드 의존일 때). 순수 캐시면 L2에서도 단일 노드 + 디그레이드(D-080)로 대체 가능.
- **처방:** 티어1·2: ElastiCache 복제본 1개 이상 + Multi-AZ, Memorystore `STANDARD_HA`. 티어0: Upstash 등 서버리스 Redis의 복제 옵션 확인(가정).
- **검증:** `aws elasticache test-failover`, Memorystore 수동 페일오버 중 앱 동작 관찰.
- **비용 영향:** 증가. 복제본 노드 비용(대략 2배).
- **출처:** https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/AutoFailover.html · https://docs.cloud.google.com/memorystore/docs/redis/high-availability-for-memorystore-for-redis (2026-10-01)

### D-034 존에 묶인 블록 볼륨
- **무엇/왜:** EBS·PD 같은 블록 볼륨은 한 존에 속하고, PV의 노드 어피니티가 접근 가능한 노드를 제한한다. 그 존이 죽으면 볼륨을 쓰는 Pod는 다른 존으로 옮겨 가도 볼륨을 붙일 수 없다.
- **실패 양상:** StatefulSet(자체 DB, 업로드 디렉터리)이 존 장애 동안 Pending으로 멈춘다. 레플리카 분산이 무의미해진다.
- **신호:** 🟢 `ReadWriteOnce` PVC를 쓰는 Deployment/StatefulSet, StorageClass `volumeBindingMode`, `allowedTopologies`.
- **시나리오·수준:** D L2 이상
- **처방:** 티어2: 상태는 매니지드 DB·오브젝트 스토리지로 밖으로 빼기. 불가하면 GKE 리전 PD 등 다중 존 볼륨 검토(가정).
- **검증:** 볼륨이 있는 존의 노드를 drain해 재스케줄 가능 여부 확인.
- **비용 영향:** 매니지드 이전은 증가.
- **출처:** https://kubernetes.io/docs/concepts/storage/persistent-volumes/ (2026-10-01)

### D-035 존 하나를 잃어도 버티는 잔여 용량(정적 안정성)
- **무엇/왜:** 존 장애 때 새 인스턴스를 띄워 메우는 설계는 그 순간의 컨트롤 플레인과 남은 존의 용량에 의존한다. Builders' Library는 3개 존이면 50% 과잉 프로비저닝해 각 존이 66% 수준으로 돌게 하라고 예시한다.
- **실패 양상:** 존 하나가 죽고 남은 존의 Pod가 CPU 100%로 지연·타임아웃. 오토스케일러가 노드를 늘리려 하지만 모두가 같은 존으로 몰려 용량이 없다.
- **신호:** 🟢 HPA `minReplicas`와 존 수의 관계(예: 존 3개에 min 2), 노드 그룹 `min_size`, ECS `desired_count`. 🔴 실제 피크 부하는 가정.
- **시나리오·수준:** D L3 (L2는 오토스케일 의존 허용, 리포트에 트레이드오프 명시)
- **처방:** 티어1: 최소 태스크를 "피크 × 존 수/(존 수−1)"로. 티어2: HPA min과 노드 여유를 같은 식으로, 낮은 우선순위 자리표시 Pod(설계 문서 T-CTL-009).
- **검증:** 한 존의 노드·태스크를 모두 제거한 상태에서 피크 부하 테스트(P4: T와 D 결합).
- **비용 영향:** 증가. 3개 존 기준 상시 용량 약 1.5배.
- **출처:** https://aws.amazon.com/builders-library/static-stability-using-availability-zones/ · https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_withstand_component_failures_static_stability.html (2026-10-01)

### D-036 단일 존 스토리지 클래스
- **무엇/왜:** Well-Architected는 S3 One Zone-IA를 정적으로 안정적이라고 보지 말라고 한다. 그 존을 잃으면 데이터 접근이 막힌다.
- **실패 양상:** 비용을 아끼려 One Zone-IA로 옮긴 사용자 파일이 존 장애 동안 접근 불가(또는 손실).
- **신호:** 🟢 `storage_class = "ONEZONE_IA"`, 수명 주기 규칙의 `transition.storage_class = "ONEZONE_IA"`, EFS One Zone.
- **시나리오·수준:** D L2 이상에서 원본 데이터에 쓰이면 결함(재생성 가능한 사본은 허용)
- **처방:** 티어1·2: 원본은 Standard/Standard-IA, One Zone은 재생성 가능 데이터에만.
- **검증:** 정적 검사.
- **비용 영향:** 증가(One Zone 대비).
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_withstand_component_failures_static_stability.html (2026-10-01)

### D-037 존 단위 트래픽 이동(zonal shift)
- **무엇/왜:** 존이 "죽지는 않고 이상한"(회색 장애) 상태면 헬스 체크가 통과해 트래픽이 계속 간다. ARC 존 이동은 지원 리소스(옵트인 필요)의 트래픽을 손상된 존에서 다른 존으로 옮기며, 1분~3일(72시간)의 만료를 정하고 연장할 수 있다. 시작 전에 남은 존의 용량을 미리 늘려 두어야 한다.
- **실패 양상:** 한 존의 패킷 손실로 요청 1/3이 느려지는데 아무도 그 존을 빼지 못한다.
- **신호:** 🟢 `aws_lb` + ARC 존 이동 옵트인 설정, 🔴 운영 런북에 존 이동 절차 없음.
- **시나리오·수준:** D L3 (티어1·2 AWS)
- **처방:** 티어1·2: ALB/NLB 존 이동 옵트인, 런북에 "사전 증설 → 존 이동" 순서. GCP는 출처 미확인. ⚠️근거없음
- **검증:** 스테이징에서 존 이동 실행 후 트래픽 분포 확인.
- **비용 영향:** 중립(사전 증설분만 증가).
- **출처:** https://docs.aws.amazon.com/r53recovery/latest/dg/arc-zonal-shift.html (2026-10-01)

### D-038 PDB를 장애 대책으로 오해
- **무엇/왜:** PDB는 드레인 같은 자발적 중단만 제한하고 하드웨어 장애·노드 소실 같은 비자발적 중단은 막지 못한다(단, 예산 계산에는 포함). Deployment 삭제·롤링 업데이트도 PDB의 제한을 받지 않는다.
- **실패 양상:** "PDB가 있으니 존 장애에도 최소 1개는 남는다"고 판정하지만, 같은 노드에 몰린 레플리카는 노드 장애로 함께 사라진다.
- **신호:** 🟢 PDB는 있는데 분산 제약(D-026)·레플리카 2개 이상(D-025)이 없음.
- **시나리오·수준:** D L2 이상 (U 카탈로그의 PDB 항목과 역할 구분)
- **처방:** 티어2: PDB는 U 통제로, D 통제는 분산 + 레플리카 + 잔여 용량으로 판정.
- **검증:** 규칙 엔진에서 PDB 단독을 D 통제로 인정하지 않도록 정적 규칙.
- **비용 영향:** 중립.
- **출처:** https://kubernetes.io/docs/concepts/workloads/pods/disruptions/ (2026-10-01)

### D-039 존마다 독립된 egress 경로
- **무엇/왜:** 프라이빗 서브넷의 외부 호출(결제·이메일·LLM API)이 NAT Gateway 하나를 거치면 그 존의 장애가 모든 존의 외부 호출을 끊는다.
- **실패 양상:** 존 A의 NAT가 죽자 존 B·C의 Pod도 외부 API 호출이 전부 타임아웃.
- **신호:** 🟢 `aws_nat_gateway` 1개 + 여러 존의 라우트 테이블이 그것을 가리킴. GCP Cloud NAT은 리전 리소스(가정).
- **시나리오·수준:** D L2 이상 (외부 의존이 핵심 경로일 때). 비용 카탈로그의 "AZ별 NAT 과잉"과 충돌하므로 D 수준으로 판정.
- **처방:** 티어1·2: 존마다 NAT 또는 리전 NAT Gateway(설계 문서 S18).
- **검증:** NAT 하나 삭제(스테이징) 후 다른 존의 외부 호출 확인.
- **비용 영향:** 증가. NAT 시간당 요금 × 존 수(가격은 설계 문서 S18).
- **출처:** 일반 원칙(출처 미확인 — 설계 문서 S18의 "복원력을 위해 AZ마다 NAT 권장" 참조, 이번 작업에서 재확인하지 않음) ⚠️근거없음

## 4. 리전 장애와 DR 전략

### D-040 RTO·RPO 목표의 명시
- **무엇/왜:** RTO는 앱이 오프라인이어도 되는 최대 시간, RPO는 잃어도 되는 데이터의 최대 시간이다. 값이 작을수록 비용이 커진다. 목표가 없으면 과잉(멀티 리전)과 부족(백업 없음)을 판정할 기준이 없다.
- **실패 양상:** 팀은 "몇 분이면 복구"라고 믿는데 실제 구성은 일일 백업뿐이다.
- **신호:** 🔴 코드에 없음 → 설계 문서 §4 가정(L1 RPO 24h·RTO 4h, L2 RPO 5m·RTO 30m, L3 RPO ≤1m·RTO ≤5m)을 리포트 상단에 노출. 🟡 README·SLA 문서의 수치.
- **시나리오·수준:** D L1 이상
- **처방:** 모든 티어: 가정 RTO/RPO와 현재 구성으로 달성 가능한 RTO/RPO를 나란히 표시(예: RDS PITR 로그 업로드 5분 → RPO ≈ 5분).
- **검증:** 복원·페일오버 리허설 실측치로 갱신.
- **비용 영향:** 중립.
- **출처:** https://docs.cloud.google.com/architecture/dr-scenarios-planning-guide (2026-10-01)

### D-041 DR 전략 선택(백업·복원 / 파일럿 라이트 / 웜 스탠바이 / 액티브-액티브)
- **무엇/왜:** AWS DR 백서의 4가지 전략은 비용·복잡도 순이다. 물리 데이터센터 하나(존) 수준의 재해라면 잘 설계된 HA 워크로드에는 백업·복원으로 충분할 수 있고, 리전 수준 재해나 규제가 있으면 파일럿 라이트·웜 스탠바이·멀티 사이트를 고려한다.
- **실패 양상:** 커뮤니티 앱에 액티브-액티브(과잉), 재난 알림 서비스에 같은 리전 백업만(부족).
- **신호:** 🟢 두 번째 리전 리소스(Terraform `provider` alias의 다른 `region`), 교차 리전 복제 리소스, Route 53 failover 레코드. 🔴 없으면 "단일 리전 + 백업·복원"으로 판정.
- **시나리오·수준:** D L1·L2 = 백업·복원(리전 DR은 같은 리전 백업 + IaC). D L3 = 교차 리전 백업 + 파일럿 라이트 이상 검토.
- **처방:** 티어0: 플랫폼 단일 리전 + 외부 덤프. 티어1·2: 아래 D-042~D-044 중 RTO/RPO를 만족하는 가장 싼 것.
- **검증:** 선택한 전략으로 리허설해 RTO/RPO 실측.
- **비용 영향:** 전략에 따라 증가 폭이 크게 다름(백업·복원 < 파일럿 라이트 < 웜 스탠바이 < 액티브-액티브).
- **출처:** https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html (2026-10-01)

### D-042 파일럿 라이트
- **무엇/왜:** 데이터는 DR 리전에 계속 복제(DB·오브젝트 스토리지 상시 가동)하고, 앱 서버는 "꺼둔" 상태(배포하지 않고 배포할 수 있는 구성만)로 둔다. 장애 시 켜고 늘린다. 리전마다 다른 계정을 권한다.
- **실패 양상:** 켜는 절차를 한 번도 안 해 봐서 장애 때 이미지·비밀·쿼터가 없다(D-048·D-049).
- **신호:** 🟢 DR 리전에 DB 복제본·버킷 복제는 있는데 컴퓨트 리소스는 `count = 0`/조건부.
- **시나리오·수준:** D L3 (RTO 수십 분 허용 시)
- **처방:** 티어1: DR 리전에 Cloud Run 서비스/ECS 서비스를 0 또는 최소로 정의. 티어2: DR 리전 클러스터는 비용 큼 → 티어1로 DR하는 혼합안 검토.
- **검증:** 분기별 "켜기" 리허설로 RTO 측정.
- **비용 영향:** 증가(데이터 복제·스토리지 상시, 컴퓨트는 최소).
- **출처:** https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html (2026-10-01)

### D-043 웜 스탠바이와 오토스케일 의존의 트레이드오프
- **무엇/왜:** 웜 스탠바이는 축소됐지만 완전히 동작하는 사본이 DR 리전에서 늘 돌아 즉시 (줄어든 용량으로) 트래픽을 받는다. 파일럿 라이트와 달리 "켜기"가 없고 늘리기만 한다. 오토스케일은 컨트롤 플레인 작업이라 의존하면 복구 회복력이 낮아지고, 전량을 미리 갖추면 핫 스탠바이(정적 안정)가 된다.
- **실패 양상:** 페일오버 직후 DR 리전이 평시의 10% 용량으로 전 트래픽을 받아 바로 과부하.
- **신호:** 🟢 DR 리전에 소규모 실행 중인 서비스 + 오토스케일 정책. 🔴 DR 리전 쿼터.
- **시나리오·수준:** D L3 (RTO 수 분)
- **처방:** 티어1·2: 초기 트래픽을 감당할 만큼은 미리 배치하고 나머지는 오토스케일, DR 리전 쿼터를 운영과 같게(D-049).
- **검증:** DR 리전으로 피크 트래픽을 흘리는 리허설.
- **비용 영향:** 증가(상시 축소 사본).
- **출처:** https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html (2026-10-01)

### D-044 멀티 리전 액티브-액티브는 대부분 과잉
- **무엇/왜:** 가장 복잡하고 비싼 전략이다. 쓰기 일관성 설계(write global / write local + last writer wins / write partitioned)가 필요하고, 데이터 손상 복구는 여전히 백업에 의존한다. Well-Architected도 멀티 리전은 상당히 복잡하고 대부분의 워크로드에는 필요하지 않다고 한다.
- **실패 양상:** 바이브코더 앱에 멀티 리전을 붙였다가 리전 간 쓰기 충돌·비용·운영 부담만 늘고, 정작 같은 버그가 두 리전에 동시에 배포된다.
- **신호:** 🟢 두 리전 이상에 동일 서비스 + 지연·지리 기반 라우팅 + DynamoDB 글로벌 테이블·Aurora 글로벌 DB.
- **시나리오·수준:** 비용 축 — D L3 미만에서 발견 시 COST 과잉 규칙. D L3라도 RTO ≤5분을 웜·핫 스탠바이로 달성 가능하면 그쪽 우선.
- **처방:** 모든 티어: 과잉이면 웜 스탠바이로 축소 제안.
- **검증:** 리전 하나 차단 시 나머지가 전 트래픽을 받는지, 데이터 재해(손상) 복구 리허설.
- **비용 영향:** 감소(축소 처방 시). 유지하면 최소 약 2배.
- **출처:** https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html · https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_fault_isolation_use_bulkhead.html (2026-10-01)

### D-045 교차 리전 DB 복제와 승격 시간
- **무엇/왜:** RDS 교차 리전 읽기 복제본 승격은 몇 분 걸리고 재부팅을 포함한다. Aurora 글로벌 데이터베이스는 보통 1초 미만 지연으로 복제하고 리전 장애 시에도 1분 이내 승격을 문서화한다. 비동기라 승격 시점까지의 쓰기는 잃을 수 있다.
- **실패 양상:** 승격 절차를 모르는 채 리전 장애를 맞아 수동 작업으로 RTO를 크게 넘긴다. 승격 후 원래 리전이 돌아오면 두 개의 쓰기 주체가 생긴다.
- **신호:** 🟢 `aws_db_instance.replicate_source_db`가 다른 리전 ARN, `aws_rds_global_cluster`, Cloud SQL 교차 리전 복제본(`master_instance_name` + 다른 `region`).
- **시나리오·수준:** D L3 (리전 RPO 분 단위가 필요할 때)
- **처방:** 티어1·2: RTO 수 분이면 RDS 교차 리전 복제본, 1분 이내면 Aurora 글로벌. 승격·재연결·구 리전 펜싱을 런북화.
- **검증:** DR 리허설에서 승격 시간과 유실 쓰기 수 측정.
- **비용 영향:** 증가. DR 리전 DB 인스턴스 + 리전 간 전송.
- **출처:** https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html (2026-10-01)

### D-046 오브젝트 스토리지 교차 리전 복제와 삭제 마커
- **무엇/왜:** S3 CRR은 DR 리전 버킷으로 비동기 복사한다. 기본적으로 원본에서 삭제하면 삭제 마커는 원본에만 생겨 DR 쪽 데이터가 악의적 삭제로부터 보호된다. 양방향 복제 시 삭제 마커 복제 여부를 의식적으로 정해야 한다.
- **실패 양상:** 삭제 마커 복제를 켜 둔 채 원본에서 대량 삭제 → DR 사본도 함께 "삭제" 상태.
- **신호:** 🟢 `aws_s3_bucket_replication_configuration`, `delete_marker_replication { status = "Enabled" }`, 대상 버킷 버저닝 여부.
- **시나리오·수준:** D L3 (업로드가 핵심 데이터일 때)
- **처방:** 티어1·2: 단방향 CRR + 삭제 마커 비복제 + 대상 버킷 버저닝.
- **검증:** 원본 객체 삭제 후 DR 버킷에 남아 있는지 확인.
- **비용 영향:** 증가. 사본 저장 + 리전 간 전송.
- **출처:** https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html (2026-10-01)

### D-047 리전 페일오버는 사람이 시작하고 절차는 자동화
- **무엇/왜:** 액티브-패시브의 페일오버는 RTO·RPO가 0이 아니라 손실이 따르므로, 헬스 체크·알람 기반 자동 시작은 오경보 시 불필요한 손실을 낸다. AWS 백서는 수동 시작을 흔히 쓰되 절차는 버튼 하나처럼 자동화하라고 한다.
- **실패 양상:** 일시적 네트워크 문제로 자동 페일오버가 발동해 데이터 일부를 잃고 양쪽 리전이 쓰기를 받는다(split-brain).
- **신호:** 🟢 Route 53 failover 레코드 + 헬스 체크로 DB 승격까지 자동 연결된 Lambda/스크립트. 🔴 페일오버 스크립트 없음.
- **시나리오·수준:** D L3
- **처방:** 티어1·2: 트래픽 전환은 데이터 플레인 스위치(ARC 라우팅 컨트롤 등, D-084), DB 승격은 사람 승인 후 스크립트 실행.
- **검증:** 게임데이에서 결정부터 전환 완료까지 시간 측정.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html (2026-10-01)

### D-048 DR 사이트 구성 드리프트
- **무엇/왜:** 운영 리전만 바뀌고 DR 리전은 옛 구성으로 남으면 복구가 실패한다. Well-Architected는 파이프라인이 두 사이트에 모두 배포하되 시차를 두고(staggered), 드리프트 감지·자동 교정, 쿼터·버전 차이 점검을 권한다.
- **실패 양상:** 페일오버해 보니 DR 리전 이미지가 석 달 전 버전이고 새 환경 변수가 없다.
- **신호:** 🟢 CI/CD 배포 대상이 한 리전뿐, Terraform 워크스페이스가 리전별로 따로 관리되고 변수 불일치. 🔴 드리프트 감지 없음.
- **시나리오·수준:** D L3 (DR 리전이 있을 때만)
- **처방:** 티어1·2: 같은 IaC 모듈을 두 리전에 적용, 배포 파이프라인에 DR 단계(운영 확인 후), 정기 `terraform plan` 드리프트 검사.
- **검증:** 주기적 plan diff = 0 확인, DR 리전 스모크 테스트.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_for_recovery_config_drift.html (2026-10-01)

### D-049 페일오버 대상의 쿼터와 용량
- **무엇/왜:** 서비스 쿼터는 계정·리전 단위이며 리전마다 기본값이 다를 수 있다. Well-Architected는 패시브 리전의 쿼터를 피크 용량 기준으로 맞추고 리전 간 "쿼터 드리프트"를 추적하라고 한다. GCP DR 가이드도 복구 환경의 Compute 자원을 미리 확보·예약하라고 한다.
- **실패 양상:** 페일오버는 시작됐는데 DR 리전의 Fargate 태스크·vCPU 쿼터가 기본값이라 10%만 뜬다. 같은 순간 다른 고객도 같은 리전으로 몰려 용량 부족.
- **신호:** 🔴 쿼터는 코드에 없음 → 가정. 🟡 HPA·ECS 최대값과 리전별 기본 쿼터 비교 가능(가격 API처럼 Service Quotas API 조회).
- **시나리오·수준:** D L3 (존 장애 대비 잔여 용량은 D-035)
- **처방:** 티어1·2: DR 리전 쿼터 증설 요청(쿼터 템플릿), 정적 안정 용량 일부 상시 확보.
- **검증:** DR 리전에서 운영 피크 규모까지 스케일 아웃 리허설.
- **비용 영향:** 쿼터 증설 자체는 무료(문서는 "쿼터 증설에 비용이 든다"는 오해를 안티패턴으로 꼽음). 예약 용량은 증가.
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_manage_service_limits_limits_considered.html · https://docs.cloud.google.com/architecture/dr-scenarios-planning-guide (2026-10-01)

### D-050 DB 위치는 생성 후 바꿀 수 없다
- **무엇/왜:** Firestore는 DB 인스턴스를 만든 뒤 위치를 바꿀 수 없다. 멀티 리전 위치의 SLA는 99.999% 이상, 리전 위치는 99.99% 이상이다. 처음 고른 위치가 곧 D 수준의 상한이 된다.
- **실패 양상:** 리전 위치로 시작한 재난 서비스를 나중에 멀티 리전으로 바꾸려면 새 DB로 데이터 이전이 필요하다.
- **신호:** 🟢 `google_firestore_database.location_id`(`nam5`·`eur3` 같은 멀티 리전 vs 단일 리전), `firebase.json`의 Firestore 설정. Supabase 프로젝트 리전은 🔴.
- **시나리오·수준:** D L3에서 리전 위치면 결함 후보, L1·L2는 리전 위치가 정상(비용·쓰기 지연 이점)
- **처방:** 티어0: D L3이면 생성 시 멀티 리전 위치 선택, 이미 리전이면 이전 비용(migration_effort)을 판정에 포함.
- **검증:** 정적 검사.
- **비용 영향:** 증가(멀티 리전 단가).
- **출처:** https://firebase.google.com/docs/firestore/locations (2026-10-01)

### D-051 Vercel 함수의 기본 리전과 리전 페일오버
- **무엇/왜:** Vercel 함수는 새 프로젝트 기본 `iad1`(워싱턴 D.C.)에서 실행된다. 기본으로 다중 AZ 중복은 있지만 리전 페일오버(`functionFailoverRegions`)는 Enterprise 전용이다. 함수 리전 수는 Hobby 1개, Pro 5개(문서 표 기준)다. 함수와 DB가 다른 리전이면 지연이 늘고, DB 리전 장애는 함수 페일오버로 해결되지 않는다.
- **실패 양상:** 서울 사용자용 앱이 `iad1` 함수 + 서울 Supabase 조합으로 모든 쿼리가 태평양을 왕복한다. `iad1` 리전 장애 시 Hobby/Pro는 함수 전체가 멈춘다.
- **신호:** 🟢 `vercel.json`의 `regions`·`functionFailoverRegions` 유무, Supabase/DB URL의 리전 표기(🟡).
- **시나리오·수준:** D L2 이상 (리전 일치는 모든 수준의 성능 위생)
- **처방:** 티어0: 함수 리전을 DB 리전에 맞춤, D L3이면 Enterprise 페일오버 또는 티어1 멀티 리전 검토.
- **검증:** 정적 검사 + 배포 요약의 리전 확인.
- **비용 영향:** 리전 맞춤은 중립, 페일오버는 Enterprise 플랜 비용.
- **출처:** https://vercel.com/docs/functions/configuring-functions/region (2026-10-01)

### D-052 Cloud Run은 존 중복은 기본, 리전 중복은 직접
- **무엇/왜:** Cloud Run은 리전 서비스이고 리전 안 여러 존에 자동 부하 분산되며 존 장애 시 다른 존으로 라우팅한다(기본 N+1 존 중복). 여러 리전으로 서비스하려면 리전별 배포 + 글로벌 외부 Application LB + 서버리스 NEG가 필요하고, 기본 부하 분산은 응답 없는 리전에서 자동으로 다른 리전으로 넘기지 않는다(서비스 상태 기반 페일오버·이상치 감지를 추가해야 함).
- **실패 양상:** "글로벌 LB를 붙였으니 리전 장애도 자동 페일오버"라고 믿었는데 트래픽이 죽은 리전으로 계속 간다.
- **신호:** 🟢 `google_cloud_run_v2_service`의 `multi_region_settings`, `google_compute_region_network_endpoint_group`(serverless) 여러 개, `outlier_detection` 유무.
- **시나리오·수준:** D L2는 단일 리전으로 충족, D L3이면 멀티 리전 + 장애 감지 필요
- **처방:** 티어1: D L3이면 2개 리전 + 글로벌 LB + 이상치 감지/서비스 상태.
- **검증:** 한 리전 서비스를 강제로 5xx 반환시키고 트래픽 이동 확인.
- **비용 영향:** 증가(LB + 두 번째 리전 최소 인스턴스).
- **출처:** https://docs.cloud.google.com/run/docs/zonal-redundancy · https://docs.cloud.google.com/run/docs/multiple-regions (2026-10-01)

### D-053 페일백(원래 리전 복귀) 계획
- **무엇/왜:** DR 리전으로 넘어간 뒤 원래 리전으로 돌아오려면 그동안 쌓인 쓰기를 역복제해야 한다. 페일오버만 연습하고 페일백을 설계하지 않으면 DR 리전에 무기한 머물거나 복귀 중 두 번째 장애를 낸다.
- **실패 양상:** 복귀 시 DR 리전의 새 데이터를 원래 리전 DB가 덮어쓴다.
- **신호:** 🔴 런북 부재.
- **시나리오·수준:** D L3
- **처방:** 모든 티어: 역방향 복제 → 쓰기 중지 → 전환 → 검증 순서의 런북.
- **검증:** 리허설에 페일백까지 포함.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

## 5. 헬스 체크와 프로브

### D-054 liveness가 외부 의존성을 검사함 → 연쇄 재시작
- **무엇/왜:** liveness는 데드락처럼 재시작으로만 풀리는 실패를 잡는 용도다. Kubernetes 문서는 잘못 구현한 liveness가 부하 중 재시작, 확장성 저하, 남은 Pod의 부하 증가라는 연쇄 장애를 부른다고 경고한다. EKS 모범 사례는 liveness가 외부 DB 같은 Pod 밖 요인에 의존하지 않게 하라고 한다.
- **실패 양상:** DB가 30초 느려지자 모든 Pod의 liveness가 실패해 동시에 재시작되고, 재시작한 Pod가 또 DB에 연결을 몰아 회복이 늦어진다. 결국 DB 장애가 앱 전체 장애로 커진다.
- **신호:** 🟢 `livenessProbe.httpGet.path`가 가리키는 핸들러 코드가 DB 쿼리·Redis `PING`·외부 HTTP 호출을 함(경로 → 라우트 함수 추적). `/health`가 `SELECT 1`. 예시 앱은 liveness가 외부 의존성을 보지 않는다고 명시(좋은 사례).
- **시나리오·수준:** D L2 이상 (설계 문서 D-CTL-004). 모든 수준에서 결함으로 보고해도 무방.
- **처방:** 티어1: Cloud Run·ECS 컨테이너 헬스 체크도 같은 원칙. 티어2: `/livez`는 프로세스·이벤트 루프 응답만, 의존성 검사는 별도 엔드포인트로.
- **검증:** DB 차단(장애 주입) 중 Pod 재시작 횟수 = 0인지 확인.
- **비용 영향:** 중립.
- **출처:** https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/ · https://docs.aws.amazon.com/eks/latest/best-practices/application.html (2026-10-01)

### D-055 readiness가 공유 의존성을 검사함 → 전체 트래픽 차단
- **무엇/왜:** EKS 모범 사례는 readiness도 DB 같은 Pod 밖 자원에 의존하지 말라고 한다. 모든 레플리카가 같은 기준을 공유하므로 DB가 닿지 않으면 모든 Pod가 동시에 준비되지 않음 상태가 되어 Service가 트래픽을 전혀 보내지 않는다. 그러면 DB 없이도 가능한 기능(캐시 응답, 정적 페이지, 큐 접수)까지 막힌다.
- **실패 양상:** DB 장애 동안 stale 캐시로 읽기를 유지하도록 설계해 놓고 readiness가 DB를 봐서 디그레이드 모드가 한 번도 사용자에게 닿지 않는다.
- **신호:** 🟢 `readinessProbe` 핸들러가 DB·Redis 연결을 검사. 🟢 디그레이드 코드(stale 캐시 등)와 의존성 검사 readiness가 공존(모순 규칙).
- **시나리오·수준:** D L2 이상, 디그레이드 모드가 있는 D L3에서는 치명적
- **처방:** 티어2: readiness는 "이 Pod가 요청을 받을 준비"(워밍업 완료·과부하 아님)만. 의존성 상태는 메트릭·알림으로.
- **검증:** DB 차단 중 엔드포인트 수가 유지되고 디그레이드 응답이 나오는지 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/eks/latest/best-practices/application.html (2026-10-01)

### D-056 로드 밸런서 헬스 체크의 fail-open 동작
- **무엇/왜:** ALB는 타깃 그룹의 모든 타깃이 비정상이면 상태와 무관하게 모든 타깃으로 라우팅한다(fail-open). 깊은(deep) 헬스 체크가 공유 의존성 때문에 동시에 실패해도 전면 차단은 피하지만, 이 동작을 모르고 헬스 체크를 설계하면 일부만 실패할 때는 남은 소수에 트래픽이 몰린다.
- **실패 양상:** DB 연결 풀이 꽉 찬 Pod 몇 개만 헬스 체크에 실패 → 남은 Pod로 트래픽 집중 → 그들도 실패 → 마지막에 fail-open으로 다시 전체에 퍼지는 진동.
- **신호:** 🟢 `alb.ingress.kubernetes.io/healthcheck-path`, `aws_lb_target_group.health_check.path`가 의존성 검사 엔드포인트, `unhealthy_threshold`·`interval`(기본: 간격 30초, 비정상 임계 2, 정상 임계 5, 타임아웃 5초).
- **시나리오·수준:** D L2 이상
- **처방:** 티어1·2: LB 헬스 체크는 얕게(프로세스 응답), 의존성 장애는 앱 내부 디그레이드로 처리.
- **검증:** 일부 Pod에만 의존성 실패를 주입해 트래픽 쏠림 관찰.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html (2026-10-01)

### D-057 느린 기동에 startupProbe 없음
- **무엇/왜:** 기동이 오래 걸리는 앱(캐시 적재, 마이그레이션 확인, 큰 모델 로드)에 liveness만 있으면 준비 전에 재시작된다. EKS 모범 사례는 기동 시간이 예측 불가하면 startupProbe를, 일정하면 `initialDelaySeconds`를 쓰라고 한다.
- **실패 양상:** 장애 복구로 모든 Pod가 동시에 재시작하는 순간 기동이 느려져(DB가 바쁨) liveness가 죽이고 다시 시작하는 루프 — 복구가 끝나지 않는다.
- **신호:** 🟢 `startupProbe` 없음 + `livenessProbe.initialDelaySeconds` 짧음, 앱 시작 시 무거운 초기화(모델 로드, `await cache.warm()`).
- **시나리오·수준:** D L2 이상
- **처방:** 티어2: startupProbe(`failureThreshold × periodSeconds`가 최악 기동 시간 이상). 티어1: Cloud Run 시작 프로브, ECS `startPeriod`.
- **검증:** DB 지연 주입 상태에서 롤링 재시작이 완료되는지 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/eks/latest/best-practices/application.html (2026-10-01)

### D-058 헬스 엔드포인트 부재·기본 경로 사용
- **무엇/왜:** ALB 헬스 체크 기본 경로는 `/`, 성공 코드 기본값은 200이다. `/`가 무거운 SSR 페이지거나 로그인 리다이렉트(302)를 반환하면 헬스 체크가 부하를 만들거나 늘 실패한다.
- **실패 양상:** 메인 페이지 렌더링이 DB를 치는데 헬스 체크가 30초마다 모든 타깃에서 이를 호출, DB가 느려지면 모든 타깃이 비정상 판정.
- **신호:** 🟢 `/health`·`/healthz`·`/livez` 라우트 부재, 헬스 체크 경로 미지정, `matcher` 미지정 + `/`가 리다이렉트.
- **시나리오·수준:** 모든 수준 (티어1·2)
- **처방:** 티어1·2: 가벼운 전용 엔드포인트 추가(P2 코드 수정 PR 후보).
- **검증:** 정적 검사 + 엔드포인트 응답 시간 측정.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html (2026-10-01)

### D-059 프로세스 상태와 서비스 상태의 분리
- **무엇/왜:** SRE 책은 "바이너리가 응답하는가"(프로세스 헬스)와 "요청을 처리할 수 있는가"(서비스 헬스)를 분리하라고 하고, 헬스 체크가 태스크를 회복보다 빨리 죽이면 일시적으로 끄라고까지 한다. 헬스 체크 자체가 연쇄 장애의 원인이 될 수 있기 때문이다.
- **실패 양상:** 과부하로 응답이 느려진 정상 프로세스를 헬스 체크가 "죽었다"고 판단해 재시작 → 남은 프로세스 과부하 가중.
- **신호:** 🟢 같은 엔드포인트를 liveness·readiness·LB 헬스 체크가 공유, liveness `timeoutSeconds: 1` + 무거운 핸들러.
- **시나리오·수준:** D L2 이상
- **처방:** 티어2: liveness(프로세스) / readiness(수용 가능) / 외부 모니터(서비스 기능)를 각각 다른 엔드포인트로. 비상시 liveness 완화 절차를 런북에.
- **검증:** 과부하 테스트 중 재시작 수와 오류율 상관 관계 확인.
- **비용 영향:** 중립.
- **출처:** https://sre.google/sre-book/addressing-cascading-failures/ (2026-10-01)

### D-060 exec 프로브의 타임아웃 초과
- **무엇/왜:** EKS 모범 사례는 exec 기반 프로브의 셸 명령이 `timeoutSeconds` 전에 끝나지 않으면 노드에 `<defunct>` 프로세스가 쌓여 노드 장애로 이어진다고 경고한다.
- **실패 양상:** `pg_isready`·`redis-cli ping`을 exec 프로브로 쓰다 의존성이 느려지자 좀비 프로세스가 쌓여 노드 전체가 불안정.
- **신호:** 🟢 `livenessProbe.exec.command`/`readinessProbe.exec.command`에 네트워크 호출 명령.
- **시나리오·수준:** D L2 이상 (티어2)
- **처방:** 티어2: HTTP·TCP 프로브로 교체하거나 명령에 자체 타임아웃.
- **검증:** 의존성 지연 주입 후 노드의 defunct 프로세스 수 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/eks/latest/best-practices/application.html (2026-10-01)

## 6. 의존성 장애 격리

### D-061 모든 원격 호출에 연결·요청 타임아웃
- **무엇/왜:** Well-Architected는 모든 서비스 의존성 호출에 연결 타임아웃과 요청 타임아웃을 함께 두고 기본값에 기대지 말라고 한다. 일부 프레임워크는 기본값이 무한이거나 서비스 목표보다 길다. 너무 길면 자원이 묶이고, 너무 짧으면 재시도가 늘어 전면 장애가 될 수 있다.
- **실패 양상:** 외부 API가 응답을 멈추자 워커·스레드·이벤트 루프 슬롯이 모두 대기 상태로 묶여 무관한 요청까지 타임아웃.
- **신호:** 🟢 타임아웃 인자 없는 호출: Python `requests.get(url)`(timeout 미지정), `httpx`는 클라이언트 생성 설정 확인, Node `fetch()`에 `AbortSignal.timeout` 없음, `axios.create()`에 `timeout` 없음, AWS SDK `connectTimeout`/`requestTimeout`·boto3 `Config(connect_timeout, read_timeout)` 미설정, OpenAI·Anthropic SDK `timeout` 미설정. 🟡 라이브러리별 기본값은 버전마다 다르므로 "명시 여부"로 판정.
- **시나리오·수준:** D L1 이상 권장, D L3 필수 (설계 문서 D-CTL-005)
- **처방:** 모든 티어: 호출별 타임아웃을 정상 지연 분포(예: p99) 위로 명시. 서버리스(티어0)는 함수 최대 실행 시간보다 짧게.
- **검증:** 의존성에 지연 주입(toxiproxy·Chaos Mesh 네트워크 지연)해 요청이 타임아웃 값 근처에서 끊기는지 확인. 정적 검사로 미지정 호출 목록화.
- **비용 영향:** 중립(서버리스는 대기 과금 감소).
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_client_timeouts.html (2026-10-01)

### D-062 DB 쿼리·커넥션 획득 타임아웃
- **무엇/왜:** HTTP 호출뿐 아니라 DB 쿼리와 커넥션 풀 대기에도 상한이 필요하다. 느린 쿼리 하나가 풀을 점유하면 나머지 요청이 풀 대기에서 무기한 멈춘다.
- **실패 양상:** 인덱스 없는 쿼리가 락을 잡자 풀 10개가 모두 묶이고 헬스 체크까지 실패.
- **신호:** 🟢 PostgreSQL `statement_timeout`·`idle_in_transaction_session_timeout` 미설정, SQLAlchemy `pool_timeout`, Prisma `connect_timeout`·`pool_timeout`, node-postgres `connectionTimeoutMillis`/`statement_timeout` 미설정.
- **시나리오·수준:** D L2 이상
- **처방:** 모든 티어: 역할별 `statement_timeout`, 풀 대기 타임아웃, 실패 시 503으로 빠르게 실패.
- **검증:** `pg_sleep`·락 주입으로 타임아웃 동작 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_client_timeouts.html (2026-10-01) — 원칙 출처. DB 설정 키 이름은 일반 지식(출처 미확인) ⚠️근거없음

### D-063 재시도는 한 계층에서, 지수 백오프 + 지터 + 최대 횟수
- **무엇/왜:** Well-Architected 안티패턴: 백오프·지터·최대 횟수 없는 재시도, 여러 계층에서의 중복 재시도(재시도 폭풍), 권한·설정 오류 같은 회복 불가 오류의 재시도, 비멱등 호출 재시도. SRE 책은 계층마다 재시도하면 사용자 요청 하나가 기하급수로 불어난다고 경고한다. AWS 아키텍처 블로그 실험은 Full Jitter가 지터 없는 지수 백오프보다 클라이언트 작업량을 절반 이상 줄였다.
- **실패 양상:** 장애가 회복되려는 순간 모든 클라이언트가 같은 간격으로 동시에 재시도해 다시 쓰러뜨린다(메타안정 장애).
- **신호:** 🟢 `tenacity`·`backoff`·`p-retry`·`axios-retry`·`retry` 사용 시 `wait_random_exponential`/`jitter` 유무와 `stop_after_attempt`. 🟢 SDK 내장 재시도(AWS SDK, OpenAI SDK `max_retries`)와 앱 재시도가 중첩. 🟢 `while True:` 재시도 루프, 고정 `sleep(1)`.
- **시나리오·수준:** D L2 이상
- **처방:** 모든 티어: 재시도 계층을 하나로 정하고(보통 가장 바깥 클라이언트 또는 SDK), 지수 백오프 + full jitter + 최대 3회 내외, 4xx(429 제외)는 재시도하지 않음.
- **검증:** 의존성에 50% 오류 주입 시 의존성이 받는 요청 수 배율 측정(1.x배 이내 목표).
- **비용 영향:** 감소(불필요한 호출·과금 API 호출 감소).
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_limit_retries.html · https://sre.google/sre-book/addressing-cascading-failures/ · https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/ (2026-10-01)

### D-064 재시도 예산
- **무엇/왜:** SRE 책의 과부하 처리 장은 요청당 3번 실패하면 호출자에게 실패를 올려 보내고, 클라이언트 단위로는 재시도 비율이 10% 미만일 때만 재시도하게 해 증폭을 일반적으로 1.1배로 묶는다고 한다.
- **실패 양상:** 의존성이 절반쯤 실패할 때 재시도가 정상 트래픽의 두세 배를 만들어 완전 장애로 키운다.
- **신호:** 🟢 재시도 라이브러리에 전역 토큰 버킷·예산 개념 없음(resilience4j `RetryConfig`·Envoy `retry_budget` 등은 있음). 🔴 대부분 앱 코드에 없음.
- **시나리오·수준:** D L3 (L2는 D-063으로 충분)
- **처방:** 티어2: 서비스 메시·Envoy 재시도 예산. 티어0·1: 앱 레벨 토큰 버킷(성공 시 적립, 재시도 시 소모).
- **검증:** 오류율을 올려 가며 재시도 비율이 10% 근처에서 포화되는지 확인.
- **비용 영향:** 감소.
- **출처:** https://sre.google/sre-book/handling-overload/ (2026-10-01)

### D-065 서킷 브레이커
- **무엇/왜:** 의존성이 계속 실패하면 재시도는 부하만 키운다. 서킷 브레이커는 실패가 많으면 호출을 끊고(열림) 가끔만 시험 호출해 회복을 확인한다. Well-Architected는 하류 시스템 과부하와 시간 민감 시스템에 이 패턴을 권한다.
- **실패 양상:** 결제 API가 다운된 동안 모든 체크아웃 요청이 타임아웃까지 기다리며 워커를 점유, 다른 기능까지 느려진다.
- **신호:** 🟢 `opossum`, `cockatiel`, `pybreaker`, `aiobreaker`, `resilience4j`, `polly`, Istio `DestinationRule.outlierDetection`. 부재 시 🔴.
- **시나리오·수준:** D L3 (외부 의존이 많은 경로), L2는 선택
- **처방:** 모든 티어: 외부 SaaS 호출(결제·이메일·LLM)을 감싸고, 열림 상태의 대체 동작(D-071)을 정의. 티어2: 메시의 이상치 감지.
- **검증:** 의존성 다운 주입 → 열림 전환 시간, 열린 동안 응답 시간(즉시 실패), 회복 후 닫힘 확인.
- **비용 영향:** 중립(과금 API 낭비 호출 감소).
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_graceful_degradation.html · https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_client_timeouts.html (2026-10-01)

### D-066 벌크헤드(자원 격리)
- **무엇/왜:** 한 의존성·한 기능이 공유 자원(스레드, 커넥션 풀, CPU, 프로세스)을 다 쓰지 못하게 칸막이를 둔다. 예시 앱은 CPU를 많이 쓰는 로그인(argon2)과 모든 요청이 거치는 세션 확인을 별도 Deployment(`auth-verify`)로 나누고 argon2 동시 실행을 Pod당 4개로 제한했다.
- **실패 양상:** 로그인 폭주로 CPU가 포화되자 세션 확인이 밀려 로그인과 무관한 읽기까지 전부 지연.
- **신호:** 🟢 기능별 Deployment·서비스 분리, `asyncio.Semaphore`·`p-limit`·`bottleneck`으로 의존성별 동시성 제한, 의존성별 별도 HTTP 에이전트·커넥션 풀. 🟡 하나의 프로세스가 모든 라우트를 처리하고 공유 풀만 있음.
- **시나리오·수준:** D L3 (T L3과 결합 시 특히)
- **처방:** 티어1: 무거운 경로를 별도 서비스로 분리. 티어2: 별도 Deployment + HPA·PDB. 모든 티어: 의존성별 세마포어.
- **검증:** 한 경로에 과부하를 걸고 다른 경로의 지연이 유지되는지 확인.
- **비용 영향:** 증가(소폭). 분리된 서비스의 최소 인스턴스.
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_fault_isolation_use_bulkhead.html (2026-10-01) — 셀 수준 벌크헤드 출처. 프로세스 내 세마포어는 일반 원칙(출처 미확인) ⚠️근거없음

### D-067 데드라인 전파와 포기된 요청 처리 중단
- **무엇/왜:** SRE 책은 데드라인을 명시하고, 하위 호출로 넘길 때 이미 쓴 시간만큼 줄여 전파하며, 단계마다 남은 시간을 확인하라고 한다. 클라이언트가 이미 포기한 요청을 계속 처리하면 장애 중 자원을 헛되이 쓴다.
- **실패 양상:** 사용자는 10초 만에 떠났는데 서버는 30초 타임아웃의 하위 호출 체인을 끝까지 처리하며 큐를 막는다.
- **신호:** 🟢 상위 타임아웃 < 하위 타임아웃(예: LB 30초, 앱 → API 60초), gRPC `deadline` 미전파, 요청 취소(`request.is_disconnected()`, `AbortController`) 미처리. 🟡 nginx `proxy_read_timeout`과 앱 타임아웃 비교.
- **시나리오·수준:** D L3
- **처방:** 모든 티어: 바깥에서 안쪽으로 타임아웃이 줄어들도록 계층 정렬(LB > 게이트웨이 > 앱 > 의존성), 취소 전파.
- **검증:** 클라이언트 조기 종료 시 서버 작업이 중단되는지 로그로 확인.
- **비용 영향:** 감소(헛작업 감소).
- **출처:** https://sre.google/sre-book/addressing-cascading-failures/ (2026-10-01)

### D-068 큐 백로그 한도·DLQ·메시지 나이
- **무엇/왜:** Well-Architected 안티패턴: DLQ나 DLQ 알람이 없음, 메시지 나이를 측정하지 않음, 의미 없어진 백로그를 비우지 않음, 엄격한 순서가 필요 없는데 FIFO로 처리해 새 요청까지 늦어짐. 장애 복구 직후 쌓인 백로그를 처리하느라 새 요청이 모두 SLA를 넘길 수 있다.
- **실패 양상:** DB가 1시간 죽은 동안 쌓인 큐를 복구 후 순서대로 처리하느라 새 쓰기가 1시간 늦게 반영된다. 독성 메시지 하나가 소비자를 무한 재시작시킨다.
- **신호:** 🟢 큐 길이 상한(`MAXLEN`, `QUEUE_MAX_LEN`) 유무, DLQ(`redrive_policy`, `posts:dlq`) 유무, 메시지 타임스탬프 기반 나이 메트릭. 예시 앱은 큐 상한 50000 + 503 `QUEUE_FULL` + DLQ를 갖춤.
- **시나리오·수준:** D L2 이상 (큐가 있을 때. 멱등 소비는 C 카탈로그)
- **처방:** 모든 티어: 큐 상한 + 초과 시 빠른 거절, DLQ + 알람, 메시지 나이 메트릭, 오래된 메시지 폐기 정책(업무상 허용 시).
- **검증:** 소비자 중지 → 백로그 생성 → 재개 시 새 메시지 처리 지연 측정.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_fail_fast.html (2026-10-01)

### D-069 큐로 쓰기를 버퍼링해 DB 장애 흡수
- **무엇/왜:** Well-Architected는 단일 쓰기 주체인 RDB가 쓰기의 단일 장애점이므로, 매우 높은 가용성이 필요하면 쓰기를 SQS 같은 큐에 버퍼링해 주 DB가 잠시 없어도 요청을 받을 수 있다고 한다. 예시 앱은 DB 장애 중에도 글쓰기를 큐에 쌓아 두고 복구 후 반영한다.
- **실패 양상:** DB 페일오버 60~120초 동안 모든 쓰기가 실패해 사용자가 입력을 잃는다.
- **신호:** 🟢 쓰기 API가 큐에 넣고 `202` 반환, 워커가 DB 반영. 🟡 동기 쓰기만 있음.
- **시나리오·수준:** D L3 (쓰기 가용성이 핵심일 때). C L3(결제)은 동기 확정이 우선이라 적용 여부를 C가 판정.
- **처방:** 티어0: 서버리스 큐(Upstash QStash 등, 가정). 티어1·2: SQS·Pub/Sub 또는 Redis Streams(내구성 주의, D-015).
- **검증:** DB 차단 중 쓰기 접수율, 복구 후 반영 완료 시간과 유실 0 확인.
- **비용 영향:** 증가(큐·워커).
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_graceful_degradation.html (2026-10-01)

### D-070 의존성 실패 오류 분류와 빠른 실패
- **무엇/왜:** 회복 불가 오류(인증·권한·설정 오류, 4xx)를 재시도하면 자원만 쓴다. 의존성이 실패하면 빨리 실패해 자원을 풀어 주는 것이 회복을 돕는다(fail fast). 회색 장애(성공과 실패가 섞임)인 인스턴스를 라우팅에서 빼지 않는 것도 안티패턴이다.
- **실패 양상:** 만료된 API 키로 외부 호출이 401을 받는데 3회 재시도 × 백오프로 요청마다 수 초씩 지연.
- **신호:** 🟢 재시도 조건이 모든 예외(`except Exception`, `retry_if_exception_type(Exception)`).
- **시나리오·수준:** D L2 이상
- **처방:** 모든 티어: 재시도 대상은 타임아웃·연결 오류·429·5xx로 한정, 나머지는 즉시 실패 + 알림.
- **검증:** 401·400 주입 시 재시도 횟수 0 확인.
- **비용 영향:** 감소.
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_limit_retries.html · https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_fail_fast.html (2026-10-01)

## 7. 디그레이드 모드와 정적 안정성

### D-071 핵심 기능 식별과 하드 의존 → 소프트 의존 전환
- **무엇/왜:** Well-Architected REL05-BP01은 의존성이 없어도 핵심 기능은 (낡은 데이터, 대체 데이터, 빈 데이터로라도) 돌아가게 하라고 한다. 안티패턴: 핵심 기능을 식별하지 않음, 의존성 하나가 실패하면 부분 결과도 돌려주지 않음, 의존성 실패 중 동작을 테스트하지 않음.
- **실패 양상:** 추천 위젯 API 하나가 죽자 홈페이지 전체가 500.
- **신호:** 🟢 `Promise.all`로 여러 의존성을 묶어 하나라도 실패하면 전체 실패(`Promise.allSettled` 아님), `asyncio.gather` 기본(예외 전파). 🟡 페이지당 의존성 수. 예시 앱 README의 "장애 격리 표"가 이 항목의 모범 산출물.
- **시나리오·수준:** D L3 (설계 문서 D L3 정의 "의존성 장애 시 디그레이드 모드")
- **처방:** 모든 티어: 기능 × 의존성 장애 행렬(예시 앱 표 형식)을 리포트로 생성하고, 핵심 기능이 하드 의존하는 칸을 결함으로 표시.
- **검증:** 의존성마다 차단 실험 후 행렬의 기대 동작과 실제 응답 비교(P4).
- **비용 영향:** 중립~소폭 증가.
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_graceful_degradation.html (2026-10-01)

### D-072 stale 캐시 응답
- **무엇/왜:** 원본 조회가 실패할 때 만료된 사본을 돌려준다. HTTP 수준에서는 `Cache-Control: stale-if-error=<초>`가 오류(5xx·네트워크 실패) 시 캐시가 낡은 응답을 내도록 허용하고, `stale-while-revalidate`는 만료 응답을 내면서 백그라운드로 갱신한다. 앱 수준에서는 예시 앱처럼 짧은 TTL 캐시와 긴 TTL 사본(`stale:*`)을 함께 둔다.
- **실패 양상:** DB가 1분 죽은 동안 읽기 트래픽 전부가 503.
- **신호:** 🟢 `stale-if-error`·`stale-while-revalidate` 헤더, Next.js `revalidate`/ISR(빌드·재검증 실패 시 이전 페이지 유지 성격), 앱 코드의 DB 예외 → 캐시 사본 반환 분기.
- **시나리오·수준:** D L3 (읽기 기능 유지가 가정에 포함)
- **처방:** 티어0: CDN 캐시 헤더 + ISR. 티어1·2: CDN `stale-if-error` + 앱 stale 사본.
- **검증:** DB 차단 중 읽기 성공률과 응답 데이터 나이 측정.
- **비용 영향:** 감소(원본 부하 감소) 또는 중립.
- **출처:** https://www.rfc-editor.org/rfc/rfc5861 (2026-10-01)

### D-073 읽기 전용 모드
- **무엇/왜:** 주 DB(쓰기)가 없을 때 읽기 복제본이나 캐시로 읽기를 계속 제공하고 쓰기 UI를 비활성화한다. Well-Architected는 읽기만 하는 쿼리에 복제본을 쓰면 주 DB 장애 시에도 중복성을 얻는다고 한다.
- **실패 양상:** 페일오버·마이그레이션 중 사이트 전체가 에러 페이지.
- **신호:** 🟢 읽기 복제본 엔드포인트를 쓰는 코드 경로(`DATABASE_READ_URL`), 기능 플래그 `READ_ONLY`. 🔴 대부분 없음.
- **시나리오·수준:** D L3
- **처방:** 모든 티어: 전역 읽기 전용 플래그(설정·환경 변수로 즉시 전환) + 쓰기 UI 숨김 + 쓰기 API 503(`Retry-After`).
- **검증:** 플래그 전환 후 읽기 정상·쓰기 거절 확인, 주 DB 차단 시 자동 전환 여부.
- **비용 영향:** 복제본을 새로 둔다면 증가.
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_graceful_degradation.html (2026-10-01)

### D-074 설정·기능 플래그 저장소 장애 시 기본값
- **무엇/왜:** Well-Architected는 파라미터 저장소가 없을 때를 대비해 이미지에 기본 파라미터를 넣어 두거나 캐시하라고 한다(기본값은 최신으로 유지하고 테스트에 포함).
- **실패 양상:** LaunchDarkly·Firebase Remote Config·SSM 조회 실패로 앱이 기동하지 못하거나 모든 플래그가 "끔"이 되어 핵심 기능이 꺼진다.
- **신호:** 🟢 기동 시 원격 설정 필수 조회(`await getConfig()` 실패 시 `process.exit`), 플래그 SDK의 기본값 인자 미지정.
- **시나리오·수준:** D L2 이상 (설정 관리 자체는 U 카탈로그)
- **처방:** 모든 티어: 플래그 SDK 호출마다 안전한 기본값, 마지막으로 성공한 설정을 로컬에 캐시.
- **검증:** 설정 저장소 차단 상태에서 기동·동작 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_graceful_degradation.html (2026-10-01)

### D-075 갱신 실패가 로컬 상태를 비우지 않게
- **무엇/왜:** Well-Architected 안티패턴: "갱신 실패의 결과로 로컬 상태를 무효화하거나 비우는 것". 정적 안정 설계는 일정 주기로 갱신하고 실패하면 이전 캐시 값을 쓰며 알람을 낸다.
- **실패 양상:** JWKS·라우팅 테이블·허용 목록 갱신이 한 번 실패하자 빈 목록으로 교체되어 모든 요청이 거부된다.
- **신호:** 🟢 주기 갱신 코드에서 `catch` 시 캐시를 `null`/`[]`로 설정, 캐시 TTL 만료 시 무조건 삭제(`cache.delete` 후 fetch).
- **시나리오·수준:** D L2 이상
- **처방:** 모든 티어: "갱신 성공 시에만 교체", 만료돼도 원본 실패 시 이전 값 유지 + 경보.
- **검증:** 갱신 대상 차단 후 기존 기능 유지 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_graceful_degradation.html · https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_withstand_component_failures_static_stability.html (2026-10-01)

### D-076 장애 시 캐시를 우회하는 이중 모드
- **무엇/왜:** Well-Architected는 장애 때 클라이언트가 캐시를 우회하게 허용하는 것을 이중 모드(bimodal) 동작의 예로 들며, 워크로드 수요를 크게 바꿔 실패를 부른다고 한다.
- **실패 양상:** "캐시 오류면 DB 직접 조회" 분기가 Redis 장애 순간 DB로 전 트래픽을 보내 DB까지 쓰러진다(D-080과 연결).
- **신호:** 🟢 `try: cache.get() except: return db.query()` 형태의 무조건 우회, 우회 경로에 동시성 제한 없음. 예시 앱은 Redis 장애 시 캐시를 건너뛰고 DB를 직접 조회하므로, 이 경로에 DB 보호(동시성 제한·부하 차단)가 있는지가 판정 포인트.
- **시나리오·수준:** D L2 이상
- **처방:** 모든 티어: 우회 경로에 세마포어·부하 차단 적용, 또는 우회 대신 stale·부분 응답.
- **검증:** Redis 차단 + 피크 부하 결합 테스트에서 DB CPU·연결 수 관찰.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_withstand_component_failures_static_stability.html (2026-10-01)

### D-077 정적 안정성: 장애 중 새 자원 생성에 의존하지 않기
- **무엇/왜:** 정적 안정 설계는 의존성이 손상돼도 새 자원을 만들지 않고 계속 동작한다. Well-Architected 안티패턴: 장애 범위와 무관하게 자원을 항상 만들 수 있다고 가정, 장애 중 동적으로 자원 확보 시도, 컴퓨트만 정적 안정을 고려.
- **실패 양상:** 존 장애 때 오토스케일러가 남은 존에 노드를 만들려 하지만 모두가 같은 시도를 해 용량이 없다. 스케일 투 제로 서비스가 장애 복구 시점에 콜드 스타트 폭주.
- **신호:** 🟢 `minReplicas`/`min_instance_count = 0`(스케일 투 제로) + D L3, 노드 그룹 `min_size`가 피크 필요량보다 훨씬 작음, 런북에 "장애 시 인스턴스 추가".
- **시나리오·수준:** D L3 (L2는 비용과 트레이드오프로 허용, 리포트에 명시)
- **처방:** 티어1: Cloud Run 최소 인스턴스·ECS 최소 태스크. 티어2: 과잉 프로비저닝 노드(자리표시 Pod). D-035와 함께 판정.
- **검증:** 오토스케일러를 끈 상태로 존 장애 + 피크 부하 시험.
- **비용 영향:** 증가(상시 여유 용량).
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_withstand_component_failures_static_stability.html · https://aws.amazon.com/builders-library/static-stability-using-availability-zones/ (2026-10-01)

### D-078 비상 레버(킬 스위치)
- **무엇/왜:** 비상 레버는 알려지고 시험된 방법으로 구성 요소를 끄거나 줄이거나 동작을 바꿔 가용성 영향을 줄이는 빠른 절차다. Well-Architected 안티패턴: 비핵심 의존성 실패가 핵심에 영향, 발동·해제 기준이 없음.
- **실패 양상:** 장애 중 무거운 기능(검색·추천·이미지 변환)을 끌 방법이 배포밖에 없어 20분이 걸린다.
- **신호:** 🟢 기능 플래그 SDK·환경 변수 기반 기능 토글, 관리용 토글 엔드포인트. 🔴 없음.
- **시나리오·수준:** D L3
- **처방:** 모든 티어: 비핵심 기능별 즉시 토글(배포 없이), 발동 기준(지연·오류율)과 담당자를 런북에.
- **검증:** 게임데이에서 레버 발동 → 핵심 기능 지표 회복 시간 측정.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_emergency_levers.html (2026-10-01)

### D-079 디그레이드 모드의 자동 복귀
- **무엇/왜:** SRE 책은 디그레이드 모드가 사람 개입 없이 빠져나오는지 테스트하라고 한다. 디그레이드 경로는 주 경로보다 훨씬 단순해야 하며(Well-Architected), 드물게 실행되는 경로는 정작 필요할 때 동작하지 않는다.
- **실패 양상:** DB가 복구됐는데 서킷이 열린 채로 남거나 읽기 전용 플래그가 꺼지지 않아 몇 시간 동안 쓰기가 막힌다.
- **신호:** 🟢 서킷 브레이커 half-open 설정 유무, 디그레이드 플래그의 자동 해제 로직 유무.
- **시나리오·수준:** D L3
- **처방:** 모든 티어: 자동 복귀 조건 + 복귀 실패 알림.
- **검증:** 장애 주입 → 해제 → 정상 모드 복귀 시간 측정(P4 시나리오에 포함).
- **비용 영향:** 중립.
- **출처:** https://sre.google/sre-book/addressing-cascading-failures/ · https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_graceful_degradation.html (2026-10-01)

## 8. 캐시·재시도·재접속 폭주

### D-080 캐시 장애 시 DB 쇄도(용량 캐시 의존)
- **무엇/왜:** SRE 책은 지연을 줄이는 캐시(latency cache)와 용량을 떠받치는 캐시(capacity cache, 사실상 하드 의존)를 구분하라고 한다. 캐시 적중률 덕분에 버티던 DB는 캐시가 비는 순간 몇 배의 부하를 받는다.
- **실패 양상:** Redis 재시작으로 캐시가 비자 DB 연결이 폭증해 DB가 쓰러지고, 캐시는 영영 채워지지 않는다.
- **신호:** 🟢 캐시 적중 실패 시 DB 조회 경로에 동시성 제한이 없음, DB `max_connections`(설계 문서 S8 계산)가 캐시 미스 100% 상황을 견디지 못함. 🔴 적중률은 가정.
- **시나리오·수준:** D L2 이상 (T L2 이상과 결합 시 필수)
- **처방:** 모든 티어: 캐시를 용량 캐시로 판정하면 캐시 HA(D-033) 또는 DB 보호(동시성 제한·부하 차단) 중 하나 필수.
- **검증:** 캐시 플러시(`FLUSHALL`) + 정상 부하에서 DB 지표 관찰.
- **비용 영향:** 캐시 HA 또는 DB 여유 용량만큼 증가.
- **출처:** https://sre.google/sre-book/addressing-cascading-failures/ (2026-10-01)

### D-081 콜드 캐시와 썬더링 허드(요청 병합)
- **무엇/왜:** 같은 키가 동시에 만료되거나 새 클러스터가 빈 캐시로 시작하면 수많은 요청이 같은 원본 조회를 동시에 한다. SRE 책은 새로 뜬 클러스터에 트래픽을 천천히 늘리고 빈 캐시 상태를 테스트하라고 한다. 예시 앱은 캐시가 비면 락을 잡은 요청 하나만 DB를 조회한다.
- **실패 양상:** 인기 글 캐시가 만료된 순간 1000개 요청이 같은 쿼리를 동시에 실행.
- **신호:** 🟢 캐시 미스 처리에 락·싱글플라이트(`SET NX`, `singleflight`, `p-memoize` 동시 병합) 유무, TTL에 지터 없이 고정값.
- **시나리오·수준:** D L2 이상 (T와 공유 — 장애 복구 직후가 D 관점)
- **처방:** 모든 티어: 요청 병합 + TTL 지터 + 복구 시 트래픽 점증.
- **검증:** 캐시 비운 상태에서 동시 요청 N개 → 원본 조회 1회인지 확인.
- **비용 영향:** 감소(원본 부하 감소).
- **출처:** https://sre.google/sre-book/addressing-cascading-failures/ (2026-10-01)

### D-082 장애 복구 직후 클라이언트 동시 재접속
- **무엇/왜:** 웹소켓·SSE·폴링·모바일 앱은 장애가 끝나는 순간 모두 같이 재접속·재시도한다. 지터 없는 재접속은 복구 직후 부하 스파이크를 만든다(D-063의 클라이언트 측 버전).
- **실패 양상:** 서버가 돌아오자 10만 웹소켓이 1초 안에 재접속해 다시 다운, 이것이 반복된다.
- **신호:** 🟢 프론트엔드의 `reconnectInterval` 고정값(`socket.io` `reconnectionDelay`·`randomizationFactor`, `reconnecting-websocket` 설정), `setInterval` 폴링 고정 주기, TanStack Query `retry`·`retryDelay` 기본값 사용.
- **시나리오·수준:** D L3 (실시간 기능이 있을 때)
- **처방:** 모든 티어: 재접속 지수 백오프 + 지터, 서버의 `Retry-After` 준수, 접속 수용률 제한.
- **검증:** 서버 재시작 시 재접속 곡선(초당 접속 수) 측정.
- **비용 영향:** 중립.
- **출처:** https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/ · https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_limit_retries.html (2026-10-01)

### D-083 부하 차단(load shedding)과 503 + Retry-After
- **무엇/왜:** Google Cloud Well-Architected는 과부하 시 프런트엔드 계층에서 초과 요청을 버려 백엔드를 보호하고, 일부 사용자 오류가 전역 장애보다 낫다고 한다. SRE 책은 처리 중 요청이 임계를 넘으면 503을 반환하라고 한다.
- **실패 양상:** 받을 수 있는 이상을 받아 모든 요청이 느려지고 결국 전부 타임아웃(처리량 0).
- **신호:** 🟢 큐 길이·동시 요청 수 기반 503(`QUEUE_FULL`), nginx `limit_req`/`limit_conn`, `Retry-After` 헤더. 예시 앱 보유.
- **시나리오·수준:** D L3 (T 카탈로그의 레이트 리밋과 구분: 여기서는 "의존성 장애 중 남은 용량 보호")
- **처방:** 모든 티어: 동시성 상한 + 빠른 503 + `Retry-After`, 우선순위(로그인 세션 유지 > 새 글쓰기 등).
- **검증:** 용량의 2배 부하에서 성공 처리량이 무너지지 않고 유지되는지 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.cloud.google.com/architecture/framework/reliability/graceful-degradation · https://sre.google/sre-book/addressing-cascading-failures/ (2026-10-01)

## 9. DNS·인증서·엣지

### D-084 DNS 레코드 수정식 페일오버 금지
- **무엇/왜:** Route 53 관리 API(레코드 생성·수정·삭제)는 컨트롤 플레인이며 `us-east-1` 단일 리전에 있고 SLA에 포함되지 않는다. 반면 DNS 응답과 헬스 체크 평가는 데이터 플레인이며 100% SLA로 설계됐다. Well-Architected는 DNS 레코드 변경에 의존하는 재라우팅을 안티패턴으로 들고, 장애 조치는 헬스 체크 기반 failover 레코드나 ARC 라우팅 컨트롤(데이터 플레인 스위치)로 하라고 한다. 가중치 변경도 컨트롤 플레인 작업이다.
- **실패 양상:** 리전 장애 때 런북의 "Route 53에서 A 레코드를 DR 리전으로 변경" 단계가 컨트롤 플레인 장애로 실행되지 않는다.
- **신호:** 🟢 Route 53 `failover_routing_policy` + `health_check_id` 유무, 런북·스크립트의 `change-resource-record-sets`. 🟢 `aws_route53recoverycontrolconfig_*`.
- **시나리오·수준:** D L3 (리전 페일오버가 있을 때)
- **처방:** 티어1·2: 미리 만든 failover 레코드 + 헬스 체크(또는 ARC 라우팅 컨트롤로 수동 스위치).
- **검증:** 헬스 체크를 강제로 비정상으로 만들어(ARC 스위치 전환) DNS 응답이 바뀌는지 확인.
- **비용 영향:** 증가(소폭). 헬스 체크 요금, ARC는 별도 요금(가격 미확인).
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_withstand_component_failures_avoid_control_plane.html · https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html (2026-10-01)

### D-085 DNS TTL과 클라이언트 측 캐싱
- **무엇/왜:** DNS 기반 전환은 TTL과 클라이언트·런타임 캐시만큼 늦게 반영된다. AWS는 JVM DNS TTL을 60초 이하로 권하며 일부 JVM은 재시작 전까지 갱신하지 않는다. DR 백서는 Global Accelerator가 DNS 캐싱 문제를 피한다고 언급한다.
- **실패 양상:** 페일오버 레코드는 바뀌었는데 TTL 1일짜리 레코드와 앱 내부 DNS 캐시 때문에 사용자 절반이 하루 동안 죽은 엔드포인트로 간다.
- **신호:** 🟢 Route 53·Cloud DNS 레코드 `ttl` 값(페일오버 대상인데 300초 초과 등), Java `networkaddress.cache.ttl`, Node 커스텀 DNS 캐시(`cacheable-lookup`) TTL.
- **시나리오·수준:** D L3
- **처방:** 티어1·2: 페일오버 레코드는 짧은 TTL(또는 별칭 레코드), 런타임 DNS 캐시 60초 이하, 고정 IP가 필요하면 Global Accelerator/글로벌 LB 애니캐스트.
- **검증:** 전환 후 클라이언트 트래픽이 새 엔드포인트로 넘어가는 시간 측정.
- **비용 영향:** 중립(짧은 TTL은 쿼리 요금 소폭 증가).
- **출처:** https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZ.Failover.html · https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html (2026-10-01) — 레코드 TTL 권장값은 일반 원칙(출처 미확인) ⚠️근거없음

### D-086 Route 53 헬스 체크의 판정 방식과 한계
- **무엇/왜:** Route 53 헬스 체커는 전 세계에서 10초 또는 30초 간격으로 검사하고, 18% 초과가 정상이라고 보면 정상으로 판정한다. HTTP(S) 검사는 4초 안에 TCP 연결, 연결 후 2초 안에 2xx/3xx가 와야 한다. 문자열 매칭은 응답 본문 첫 5,120바이트 안에서만 찾는다. **HTTPS 헬스 체크는 TLS 인증서를 검증하지 않아 인증서가 만료돼도 정상으로 판정한다.** 새 헬스 체크는 데이터가 쌓일 때까지 정상으로 간주된다.
- **실패 양상:** 인증서 만료로 모든 브라우저가 접속 실패하는데 DNS 페일오버 헬스 체크는 정상이라 아무 전환도 일어나지 않는다. 헬스 페이지가 2초 넘게 걸려 오탐 페일오버.
- **신호:** 🟢 `aws_route53_health_check.type`(`HTTPS`), `request_interval`, `failure_threshold`, `search_string`.
- **시나리오·수준:** D L3 (리전 페일오버가 있을 때)
- **처방:** 티어1·2: 헬스 체크 대상은 가벼운 엔드포인트(D-058), 인증서 만료는 별도 감시(D-087·D-088), 계산된(calculated) 헬스 체크로 다중 신호 결합.
- **검증:** 엔드포인트 지연 주입으로 판정 시간 측정, 만료 인증서 스테이징에서 동작 확인.
- **비용 영향:** 증가(소폭).
- **출처:** https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-failover-determining-health-of-endpoints.html (2026-10-01)

### D-087 매니지드 인증서 자동 갱신의 전제 조건
- **무엇/왜:** ACM은 DNS 검증으로 발급한 인증서를 자동 갱신하지만 조건이 있다. 만료 45일 전(구 395일 인증서는 60일 전)에 인증서가 AWS 서비스에서 사용 중이고 ACM이 준 CNAME 레코드가 공개 DNS에 남아 있어야 한다. 가져온(imported) 인증서, 이미 만료된 인증서는 갱신 대상이 아니다. 실패하면 30·15·7·3·1일 전에 Health·EventBridge 이벤트를 보낸다. ACM 인증서는 리전 리소스라 리전마다 따로 갱신된다.
- **실패 양상:** DNS 이전 중 ACM 검증 CNAME을 지워 갱신이 실패하고 이벤트를 아무도 구독하지 않아 만료일에 전면 장애. 이메일 검증 인증서는 사람이 메일을 눌러야 한다.
- **신호:** 🟢 `aws_acm_certificate.validation_method = "EMAIL"`, `aws_acm_certificate`의 `private_key`(가져온 인증서), 검증용 `aws_route53_record`가 Terraform에 없음, EventBridge `aws.acm` 규칙 부재.
- **시나리오·수준:** 모든 수준 (HTTPS 서비스면 L0도 해당 — 데이터가 없어도 서비스가 멈춤)
- **처방:** 티어1·2: DNS 검증 + 검증 레코드를 IaC로 고정 + 만료 이벤트 알림. GCP는 Google 관리 인증서(`ManagedCertificate`)의 DNS·LB 연결 상태 확인(출처 미확인). ⚠️근거없음
- **검증:** ACM `RenewalSummary` 상태 확인, 외부에서 인증서 만료일 모니터링.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/acm/latest/userguide/managed-renewal.html · https://docs.aws.amazon.com/acm/latest/userguide/dns-renewal-validation.html (2026-10-01)

### D-088 cert-manager·Let's Encrypt 갱신과 만료 감시
- **무엇/왜:** cert-manager는 기본적으로 인증서 수명의 2/3 시점에 갱신하며, `renewBeforePercentage` 사용을 권한다. Let's Encrypt는 2025-06-04부로 만료 알림 이메일을 중단했다. 즉 "만료 전에 메일이 오겠지"라는 안전망이 없어졌다.
- **실패 양상:** ACME HTTP-01 챌린지가 Ingress 변경·방화벽 때문에 조용히 실패하고, 알림 메일도 없어 만료 당일 발견.
- **신호:** 🟢 `cert-manager.io/cluster-issuer` 어노테이션, `Certificate` 리소스의 `renewBefore`, certbot cron. 🔴 외부 만료 모니터링 부재.
- **시나리오·수준:** 모든 수준 (자체 인증서 관리 시)
- **처방:** 티어2: cert-manager 메트릭(`certmanager_certificate_expiration_timestamp_seconds`, 이름은 일반 지식) 알림 또는 외부 인증서 모니터링. 가능하면 매니지드 인증서(ACM·Google 관리)로. ⚠️근거없음
- **검증:** 스테이징 이슈어로 짧은 수명 인증서를 발급해 갱신 주기 확인.
- **비용 영향:** 중립.
- **출처:** https://cert-manager.io/docs/usage/certificate/ · https://letsencrypt.org/2025/01/22/ending-expiration-emails/ (2026-10-01) ⚠️출처확인필요

### D-089 도메인 등록 만료·DNS 호스팅 단일 공급자
- **무엇/왜:** 도메인 등록 갱신 실패나 DNS 호스팅 공급자 장애는 인프라가 멀쩡해도 서비스를 지운다. 결제 카드 만료로 도메인 자동 갱신이 실패하는 일이 흔하다.
- **실패 양상:** 도메인 만료로 이메일 인증·OAuth 콜백·API까지 모두 해석 불가.
- **신호:** 🔴 코드에 없음. 🟡 `aws_route53domains_registered_domain.auto_renew`.
- **시나리오·수준:** 모든 수준
- **처방:** 모든 티어: 자동 갱신 + 장기 등록 + 만료 모니터링. D L3은 DNS 공급자 이중화 검토.
- **검증:** WHOIS 만료일 정기 조회.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### D-090 CDN 오리진 페일오버와 오리진 장애 시 캐시 서빙
- **무엇/왜:** CloudFront 오리진 페일오버는 요청마다 기본 오리진이 실패하면 보조 오리진으로 보낸다(이후 요청도 계속 기본 오리진부터 시도). CDN의 `stale-if-error`(D-072)와 함께 쓰면 오리진 전체 장애에도 정적·캐시 가능한 콘텐츠를 계속 낼 수 있다.
- **실패 양상:** 오리진(앱 서버) 장애 시 CDN이 있어도 모든 페이지가 502.
- **신호:** 🟢 `aws_cloudfront_distribution.origin_group`·`failover_criteria`, 캐시 정책의 오류 응답 캐싱, Vercel·Cloudflare 캐시 헤더.
- **시나리오·수준:** D L3
- **처방:** 티어0: 정적 페이지·ISR 결과는 CDN에서 계속 서빙되도록 캐시 헤더 설계. 티어1·2: 오리진 그룹(보조 = S3 정적 비상 페이지 또는 DR 리전).
- **검증:** 오리진 차단 후 CDN 응답 확인.
- **비용 영향:** 중립~소폭 증가.
- **출처:** https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html (2026-10-01)

### D-091 Cloud DNS 라우팅 정책 헬스 체크의 범위
- **무엇/왜:** Cloud DNS 페일오버 라우팅 정책은 VPC 안 내부 자원의 액티브-백업용이며, 내부 LB 헬스 체크는 비공개 영역에서만, 외부 엔드포인트 헬스 체크는 공개 영역에서만(인터넷에서 접근 가능해야 함) 된다. "Cloud DNS로 공개 DNS 페일오버"를 설계할 때 이 제약을 확인해야 한다.
- **실패 양상:** 비공개 영역용 설정을 공개 서비스 페일오버로 착각해 실제로는 헬스 체크가 걸리지 않는다.
- **신호:** 🟢 `google_dns_record_set.routing_policy`(`primary_backup`, `health_check`), 관리 영역 `visibility`.
- **시나리오·수준:** D L3 (GCP)
- **처방:** 티어1·2(GCP): 공개 서비스의 리전 페일오버는 글로벌 외부 LB(D-052) 우선, Cloud DNS 정책은 지원 범위 안에서.
- **검증:** 백업 대상 전환 실험.
- **비용 영향:** 중립.
- **출처:** https://docs.cloud.google.com/dns/docs/routing-policies-overview (2026-10-01)

## 10. 외부 SaaS·플랫폼 의존

### D-092 인증 공급자 장애
- **무엇/왜:** Auth0·Clerk·Supabase Auth·Firebase Auth·Cognito가 멈추면 로그인뿐 아니라, 요청마다 공급자 API로 세션을 확인하는 앱은 로그인된 사용자도 모두 막힌다. 서명된 토큰(JWT)을 로컬에서 검증하면 신규 로그인만 막히고 기존 세션은 유지된다. 예시 앱은 DB 장애 때 기존 세션 확인을 정상 유지하고 Redis 장애 때 `X-Auth-Degraded` 헤더로 익명 처리한다.
- **실패 양상:** 인증 SaaS 장애 30분 동안 서비스 전체가 401.
- **신호:** 🟢 요청마다 `supabase.auth.getUser()`(서버 왕복) vs `getClaims()`/로컬 JWT 검증, `clerkClient.sessions.verifySession` 원격 호출, JWKS 캐시 유무(D-075).
- **시나리오·수준:** D L3 (L2는 영향 범위만 리포트)
- **처방:** 모든 티어: 로컬 JWT 검증 + JWKS 캐시(실패 시 이전 키 유지), 공개 읽기 경로는 인증 없이 동작하게.
- **검증:** 인증 공급자 도메인 차단 상태에서 기존 세션 요청 성공률 확인.
- **비용 영향:** 감소(원격 검증 호출 감소).
- **출처:** 일반 원칙(출처 미확인) — 원칙은 https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_graceful_degradation.html (2026-10-01) ⚠️근거없음

### D-093 결제 SaaS 장애
- **무엇/왜:** Stripe·Toss 등 결제 API가 실패해도 장바구니·조회·기존 구독 이용은 계속돼야 한다. 결제 확정의 정합성은 C 카탈로그가, 여기서는 "결제가 안 될 때 나머지 기능이 같이 죽는가"만 본다.
- **실패 양상:** 페이지 로드 시 결제 SDK 초기화·구독 상태 원격 조회가 실패해 유료 사용자 전원이 기능 잠김.
- **신호:** 🟢 요청 경로마다 `stripe.subscriptions.retrieve` 원격 조회(로컬 구독 상태 캐시 없음), 결제 SDK 호출에 타임아웃·서킷 없음.
- **시나리오·수준:** D L2 이상 (결제 신호가 있으면 설계 문서상 D L2)
- **처방:** 모든 티어: 구독 상태는 웹훅으로 DB에 동기화해 로컬 조회, 결제 호출은 서킷 + "잠시 후 다시" 응답.
- **검증:** 결제 API 차단 시 비결제 기능 성공률 확인.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인) — 원칙은 https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_graceful_degradation.html (2026-10-01) ⚠️근거없음

### D-094 이메일·SMS 발송 장애와 기본 발송 한도
- **무엇/왜:** 가입 확인·비밀번호 재설정·OTP·재난 알림이 이메일·SMS에 의존한다. Supabase 기본 SMTP는 이메일 엔드포인트가 시간당 2통으로 제한되어 있고, 프로덕션 체크리스트는 자체 SMTP를 권한다.
- **실패 양상:** 트래픽이 몰린 날 가입 확인 메일이 시간당 2통만 나가 신규 가입이 사실상 정지. 발송 SaaS 장애 시 요청 처리 중 동기 발송이 타임아웃되어 가입 API 자체가 실패.
- **신호:** 🟢 `supabase/config.toml`의 `[auth.email.smtp]` 미설정, 요청 핸들러 안에서 동기 `sendMail`/`resend.emails.send`, 발송 큐 부재.
- **시나리오·수준:** D L2 이상, 재난 알림 서비스는 D L3 핵심 경로
- **처방:** 티어0: 자체 SMTP(Resend·SES 등) 연결. 모든 티어: 발송은 큐로 비동기화 + 재시도, D L3은 대체 채널(푸시·SMS 공급자 이중화).
- **검증:** 발송 공급자 차단 시 가입 API 성공 여부와 큐 적체 후 재발송 확인.
- **비용 영향:** 증가(소폭). 발송 공급자 요금.
- **출처:** https://supabase.com/docs/guides/deployment/going-into-prod (2026-10-01)

### D-095 LLM API 장애·레이트 리밋
- **무엇/왜:** LLM 호출은 지연이 길고 변동이 크며 공급자 장애·429가 잦다. 타임아웃이 없거나 길면 서버리스 함수 최대 실행 시간(설계 문서 S27)까지 대기하며 과금되고, 핵심이 아닌 AI 기능이 전체 페이지를 막는다.
- **실패 양상:** LLM 공급자 장애 시 요청마다 수십 초 대기 → 워커 고갈 → 비AI 기능까지 장애.
- **신호:** 🟢 `openai`·`@anthropic-ai/sdk`·`@google/genai`·`ai`(Vercel AI SDK) 사용, `timeout`·`max_retries` 미설정, 스트리밍 응답에 유휴 타임아웃 없음, 단일 공급자·단일 모델 하드코딩.
- **시나리오·수준:** D L2 이상 (AI가 핵심 기능이면 L3 디그레이드 필수)
- **처방:** 모든 티어: 명시적 타임아웃·재시도 상한(SDK 내장 재시도와 중첩 금지, D-063), 서킷, 대체 모델·공급자 또는 "AI 기능 일시 중단" 디그레이드, 비핵심이면 비동기화.
- **검증:** LLM 엔드포인트에 지연·429·500 주입 후 비AI 경로 정상 여부 확인.
- **비용 영향:** 감소(장애 시 낭비 호출 감소). 대체 공급자 유지는 증가.
- **출처:** 일반 원칙(출처 미확인) — 원칙은 https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_client_timeouts.html (2026-10-01) ⚠️근거없음

### D-096 의존성 가용성의 곱(합성 가용성)
- **무엇/왜:** 직렬로 연결된 하드 의존성의 가용성은 대략 곱해진다. 각 99.9%인 의존성 5개에 직렬로 의존하면 전체 상한은 그보다 낮다. 바이브코더 앱은 BaaS·인증·결제·이메일·LLM·분석 SDK에 동시에 하드 의존하는 경우가 많다.
- **실패 양상:** 각 공급자는 SLA를 지켰는데 서비스는 매달 여러 번 부분 장애.
- **신호:** 🟢 `package.json`·`requirements.txt`의 SaaS SDK 목록 + 요청 경로별 호출 여부(정적 호출 그래프).
- **시나리오·수준:** D L2 이상 (리포트 지표)
- **처방:** 모든 티어: 핵심 경로의 하드 의존 수를 줄이고(소프트 의존으로 전환, D-071), 합성 가용성을 리포트에 표시.
- **검증:** 의존성 그래프 정적 분석.
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### D-097 BaaS 한 공급자 집중
- **무엇/왜:** Supabase·Firebase 하나에 DB·인증·스토리지·함수·실시간을 모두 두면 공급자 프로젝트 하나의 장애·일시정지·결제 문제·계정 정지가 서비스 전체를 멈춘다. 반대로 분산은 복잡도와 비용을 늘리므로 D 수준에 맞춰 판단한다.
- **실패 양상:** 프로젝트 일시정지(D-003)나 리전 장애로 로그인·데이터·파일이 동시에 사라진다.
- **신호:** 🟢 `@supabase/supabase-js`의 `auth`·`storage`·`from()`·`functions`·`channel` 동시 사용, Firebase Auth + Firestore + Storage + Functions.
- **시나리오·수준:** D L3에서만 결함 후보 (L1·L2에서는 단순함이 이점 → 정상)
- **처방:** 티어0: D L3이면 최소한 데이터 외부 백업(D-003·D-005)과 정적 비상 페이지(D-111)를 공급자 밖에 둠.
- **검증:** 공급자 도메인 차단 시 남는 기능 목록 확인.
- **비용 영향:** 증가(외부 사본).
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### D-098 서드파티 프론트엔드 스크립트가 렌더링을 막음
- **무엇/왜:** 분석·채팅 위젯·A/B 테스트·폰트 CDN 스크립트를 동기로 로드하면 그 공급자 장애가 첫 화면 렌더링을 멈춘다. 재난 시에는 대역폭도 부족해 영향이 커진다(D-110).
- **실패 양상:** 분석 SDK CDN이 응답하지 않아 페이지가 하얗게 멈춘다.
- **신호:** 🟢 `<script src="https://...">`에 `async`/`defer` 없음, Next.js `<Script strategy="beforeInteractive">`, 외부 폰트 `@import`.
- **시나리오·수준:** D L3
- **처방:** 티어0: 비핵심 스크립트는 `afterInteractive`/`lazyOnload`, 자체 호스팅 폰트.
- **검증:** 브라우저에서 서드파티 도메인 차단 후 첫 화면 표시 확인(Playwright 라우트 차단).
- **비용 영향:** 중립.
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

## 11. 컨트롤 플레인·글로벌 서비스·쿼터

### D-099 복구 경로에서 컨트롤 플레인 의존 금지
- **무엇/왜:** 컨트롤 플레인(자원 생성·수정·삭제 API)은 데이터 플레인보다 복잡하고 장애 가능성이 높다. Well-Architected는 복구·완화에 컨트롤 플레인 작업을 최소화하고, 오토스케일(컨트롤 플레인) 대신 미리 확장된 자원(데이터 플레인)을, k8s에서는 노드 추가 대신 Pod 추가만으로 대응하라고 한다(과잉 프로비저닝 노드 권장).
- **실패 양상:** 리전 이벤트 때 "새 인스턴스 시작", "읽기 복제본 생성", "LB 생성"이 모두 API 오류로 실패.
- **신호:** 🔴 런북·스크립트의 `create-*`/`run-instances`/`terraform apply` 단계. 🟢 Cluster Autoscaler·Karpenter만 있고 여유 노드·자리표시 Pod 없음.
- **시나리오·수준:** D L3
- **처방:** 티어1·2: DR 자원 사전 생성, 여유 용량 상시 확보, 런북의 각 단계를 컨트롤/데이터 플레인으로 분류해 표시.
- **검증:** 런북 정적 리뷰(컨트롤 플레인 단계 수), 게임데이에서 해당 API 차단 가정 시나리오.
- **비용 영향:** 증가(사전 생성·여유 용량).
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_withstand_component_failures_avoid_control_plane.html · https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html (2026-10-01)

### D-100 us-east-1에 있는 글로벌 서비스 컨트롤 플레인
- **무엇/왜:** `aws` 파티션에서 IAM·Organizations·계정 관리·Route 53 Private DNS의 컨트롤 플레인은 `us-east-1`에, Route 53 공개 DNS·CloudFront·CloudFront용 WAF·CloudFront용 ACM·Shield Advanced의 컨트롤 플레인도 `us-east-1`에 있다. ARC·Global Accelerator·Network Manager는 `us-west-2`. 서울 리전만 쓰더라도 장애 중 IAM 역할 생성·DNS 레코드 수정·CloudFront 오리진 변경이 `us-east-1` 장애의 영향을 받는다. 또 ELB·ElastiCache·API Gateway·EKS 등의 생성은 Route 53 컨트롤 플레인을 거쳐 DNS 레코드를 만든다.
- **실패 양상:** `us-east-1` 장애 날 서울 리전 장애 대응을 위해 새 ALB를 만들려 했는데 DNS 레코드 생성 단계에서 막힌다.
- **신호:** 🟢 런북의 IAM 정책 수정·CloudFront 배포 수정·Route 53 레코드 변경. 🟢 CloudFront·ACM(us-east-1 인증서) 사용.
- **시나리오·수준:** D L3
- **처방:** 티어1·2: 장애 대응에 필요한 IAM 역할·LB·버킷·DNS 레코드는 모두 사전 생성, 복구에 필요한 컨트롤 플레인 정보는 데이터 플레인 저장소(SSM Parameter Store·S3·DynamoDB)에 캐시.
- **검증:** 런북 리뷰 + 게임데이 시나리오 "us-east-1 컨트롤 플레인 불가".
- **비용 영향:** 중립~소폭 증가.
- **출처:** https://docs.aws.amazon.com/whitepapers/latest/aws-fault-isolation-boundaries/global-services.html (2026-10-01)

### D-101 STS 글로벌 엔드포인트 의존
- **무엇/왜:** SDK·CLI의 STS 사용은 (설정에 따라) 기본으로 `us-east-1` 글로벌 엔드포인트를 쓸 수 있다. AWS는 SDK·CLI를 리전 STS 엔드포인트로 설정하라고 권한다.
- **실패 양상:** 서울 리전 워크로드가 역할 자격 증명 갱신을 `us-east-1`에 의존해 그 리전 장애 때 인증 실패.
- **신호:** 🟢 `AWS_STS_REGIONAL_ENDPOINTS` 미설정(구 SDK), `sts.amazonaws.com` 하드코딩, SDK 버전.
- **시나리오·수준:** D L3 (AWS 티어1·2)
- **처방:** 티어1·2: 리전 STS 엔드포인트 설정.
- **검증:** 정적 검사(SDK 설정·환경 변수).
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/whitepapers/latest/aws-fault-isolation-boundaries/global-services.html (2026-10-01)

### D-102 장애 중 버킷·엔드포인트 생성 의존
- **무엇/왜:** S3 `CreateBucket`·`DeleteBucket`은 이름 고유성 때문에 `us-east-1`에 의존하고, 버킷 정책·버저닝·복제·수명 주기 등 설정 변경 API도 `us-east-1`에 의존한다. AWS는 필요한 버킷을 필요한 설정까지 미리 만들어 두라고 한다.
- **실패 양상:** DR 절차의 "새 버킷 만들고 복제 설정" 단계가 실패. 패턴이 뻔한 버킷 이름은 장애 중 다른 누군가가 선점할 수도 있다.
- **신호:** 🟢 런타임 코드의 `CreateBucketCommand`, 런북의 `aws s3 mb`.
- **시나리오·수준:** D L3
- **처방:** 티어1·2: 버킷·복제·정책을 IaC로 사전 생성, 런타임 버킷 생성 제거.
- **검증:** 정적 검사.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/whitepapers/latest/aws-fault-isolation-boundaries/global-services.html (2026-10-01)

### D-103 k8s 컨트롤 플레인·etcd 장애와 자체 관리 클러스터
- **무엇/왜:** etcd가 리더를 선출하지 못하면 클러스터 상태를 바꿀 수 없어 새 Pod를 스케줄할 수 없다(기존 Pod는 계속 돈다). Kubernetes 문서는 etcd 백업 계획과 홀수 멤버(운영은 5개 권장)를 요구한다. EKS·GKE 같은 매니지드는 이를 공급자가 관리하지만, kubeadm·k3s·자체 설치 클러스터는 사용자 책임이다.
- **실패 양상:** 단일 마스터 자체 클러스터의 디스크가 죽어 모든 매니페스트·시크릿 상태를 잃는다.
- **신호:** 🟢 kubeadm 설정, k3s 설치 스크립트, `etcd` 스태틱 Pod 매니페스트, 단일 컨트롤 플레인 노드 Terraform.
- **시나리오·수준:** D L2 이상 (자체 관리 클러스터일 때)
- **처방:** 티어2: 매니지드(EKS·GKE 리전 클러스터) 권장. 자체 관리면 `etcdctl snapshot save` 정기 실행 + 외부 보관 + 3·5 멤버.
- **검증:** 스냅샷으로 테스트 클러스터 복원 리허설.
- **비용 영향:** 매니지드 전환은 관리비 증가(설계 문서 S5), 운영 부담 감소.
- **출처:** https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/ (2026-10-01)

### D-104 브레이크 글라스 접근
- **무엇/왜:** AWS 장애 격리 경계 백서는 IdP(SSO)가 손상되거나 AWS에 같이 호스팅되어 함께 영향받을 경우를 대비해 "브레이크 글라스" 사용자를 미리 만들어 두라고 한다. 운영자가 콘솔·CLI에 못 들어가면 어떤 복구도 못 한다.
- **실패 양상:** SSO 공급자 장애 중 장애 대응을 위해 아무도 AWS 콘솔에 로그인하지 못한다.
- **신호:** 🔴 코드에 없음. 🟡 IAM Identity Center만 쓰고 비상 IAM 사용자 정의 없음(Terraform).
- **시나리오·수준:** D L3
- **처방:** 모든 티어: MFA가 걸린 비상 계정을 금고에 보관, 사용 시 알림. 티어0도 Supabase·Vercel 조직에 두 번째 소유자.
- **검증:** 분기별 비상 계정 로그인 점검.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/whitepapers/latest/aws-fault-isolation-boundaries/global-services.html (2026-10-01)

## 12. 블래스트 반경과 격리 경계

### D-105 셀 기반 아키텍처
- **무엇/왜:** 셀은 상태를 공유하지 않는 워크로드의 독립 사본이며 파티션 키(고객 ID 등)로 요청을 나눈다. 셀 10개면 한 셀 장애 때 요청 90%는 영향받지 않는다. 안티패턴: 셀 무한 성장, 모든 셀 동시 배포, 셀 간 상태 공유, 라우터 계층에 복잡한 로직. 나쁜 배포·독성 요청 같은 막기 어려운 장애를 가둔다.
- **실패 양상:** (없을 때) 특정 대형 테넌트의 요청이 공유 DB를 마비시켜 전 고객 장애. (과할 때) 바이브코더 앱에 셀을 도입해 운영 비용만 폭증.
- **신호:** 🟢 테넌트별 DB/스키마 라우팅, `cell_id`·샤드 라우터. 🟡 B2B 다중 테넌트 신호(`org_id`).
- **시나리오·수준:** D L3 + B2B 대형 테넌트일 때만. 그 외 발견 시 COST 과잉 규칙 후보.
- **처방:** 티어2: 셀 = 네임스페이스·DB 단위 복제. 대부분은 해당 없음으로 판정.
- **검증:** 한 셀에 장애 주입 시 다른 셀 지표 불변 확인.
- **비용 영향:** 증가(셀 수만큼 고정비).
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_fault_isolation_use_bulkhead.html (2026-10-01)

### D-106 운영·개발 환경이 데이터 저장소를 공유
- **무엇/왜:** dev와 prod가 같은 DB·Redis·버킷을 쓰면 개발자의 실수(테이블 삭제, 부하 테스트, 마이그레이션 실험)가 곧 운영 장애·데이터 손실이다. 예시 앱은 dev·prod에 별도 DB·Redis 인스턴스를 둔다.
- **실패 양상:** dev 브랜치의 파괴적 마이그레이션이 운영 DB에 적용된다.
- **신호:** 🟢 `.env.development`와 `.env.production`의 `DATABASE_URL` 호스트 동일, Supabase 프로젝트 ref 하나만 존재, overlay 간 같은 Secret 값.
- **시나리오·수준:** D L1 이상
- **처방:** 티어0: Supabase 브랜칭·별도 프로젝트. 티어1·2: 환경별 인스턴스(dev는 작은 사양).
- **검증:** 정적 검사(환경별 연결 문자열 비교).
- **비용 영향:** 증가(dev 인스턴스).
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### D-107 DR 리전·백업을 별도 계정으로 격리
- **무엇/왜:** AWS DR 백서는 파일럿 라이트에서 리전마다 다른 계정을 쓰면 자원·보안 격리가 가장 높아 자격 증명 탈취가 DR 시나리오에 포함될 때 유리하다고 한다. 백업 계정 분리(D-009)와 같은 원리를 DR 환경 전체로 넓힌 것이다.
- **실패 양상:** 운영 계정이 탈취되자 DR 리전 자원까지 같은 권한으로 삭제된다.
- **신호:** 🟢 Terraform `provider` 블록의 `assume_role`이 리전별로 다른 계정, AWS Organizations 구조.
- **시나리오·수준:** D L3 + 보안 위협을 재해로 포함할 때
- **처방:** 티어1·2: DR·백업 계정 분리, 교차 계정 최소 권한.
- **검증:** 운영 자격 증명으로 DR 계정 자원 접근 시도 → 거부 확인.
- **비용 영향:** 중립(계정 자체는 무료, 운영 복잡도 증가).
- **출처:** https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html (2026-10-01)

### D-108 독성 요청(poison pill) 격리
- **무엇/왜:** 특정 입력이 처리기를 반복해서 죽이면 재시도·재배달 때마다 전체 소비자가 쓰러진다. Well-Architected는 셀 경계가 독성 요청 장애를 가두는 데 유효하고, 처리할 수 없는 메시지는 DLQ로 빼라고 한다.
- **실패 양상:** 깨진 이미지 하나가 썸네일 워커를 OOM으로 죽이고, 메시지가 큐로 돌아가 다음 워커도 죽인다.
- **신호:** 🟢 소비자에 최대 수신 횟수(`maxReceiveCount`, Redis Streams `XPENDING` 재배달 횟수 검사) 없음, DLQ 없음.
- **시나리오·수준:** D L2 이상 (비동기 처리 있을 때)
- **처방:** 모든 티어: 재배달 횟수 상한 → DLQ, 입력 크기·형식 사전 검증, 처리 타임아웃.
- **검증:** 독성 메시지 주입 후 처리량 유지 확인.
- **비용 영향:** 중립.
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_fault_isolation_use_bulkhead.html · https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_fail_fast.html (2026-10-01)

## 13. 재난 시 필수 서비스의 특성

### D-109 트래픽 폭증과 인프라 장애의 동시 발생
- **무엇/왜:** 재난 대응 서비스는 "다른 시스템이 무너질 때 오히려 써야 하는" 서비스다(설계 문서 D L3). 같은 재해가 클라우드 존·통신망에도 영향을 주므로 폭증(T L3)과 부분 장애(D)가 동시에 온다. SRE 책은 점진·순간 부하 모두로 한계까지 테스트하고, 비핵심 백엔드 장애가 핵심 경로를 막지 않는지 시험하라고 한다.
- **실패 양상:** 따로따로 테스트한 오토스케일링과 페일오버가, 존 하나를 잃은 상태에서 피크 20배가 오자 남은 용량·쿼터·DB 연결 한도에서 동시에 무너진다.
- **신호:** 🟡 도메인 추론(재난·안전·공공 알림) → D L3 & T L3 동시. 예시 앱의 k6 재난 시나리오는 부하만 다룬다(장애 결합 없음).
- **시나리오·수준:** D L3 & T L3 결합 (새 축 후보 참조)
- **처방:** 모든 티어: D-035(잔여 용량), D-077(정적 안정), D-083(부하 차단)을 결합 판정.
- **검증:** P4 결합 시나리오: 피크 부하 중 존 하나 제거·Redis 페일오버·DB 페일오버 주입.
- **비용 영향:** 증가(여유 용량).
- **출처:** https://sre.google/sre-book/addressing-cascading-failures/ (2026-10-01)

### D-110 저대역폭·불안정 네트워크 클라이언트와 오프라인 동작
- **무엇/왜:** 재난 지역 사용자는 혼잡한 셀룰러·위성·대피소 와이파이를 쓴다. 큰 JS 번들·이미지는 로드가 끝나지 않는다. 서비스 워커의 "네트워크 실패 시 캐시", "stale-while-revalidate", "캐시 먼저 표시 후 네트워크" 패턴으로 끊겨도 마지막 정보를 보여 줄 수 있다.
- **실패 양상:** 서버는 살아 있는데 3MB 번들이 혼잡망에서 타임아웃되어 사용자에게는 서비스가 죽은 것과 같다. 오프라인이 되면 이미 받은 대피 정보도 사라진다.
- **신호:** 🟢 빌드 산출물 크기, 서비스 워커(`next-pwa`, `workbox`, `vite-plugin-pwa`) 유무, 이미지 최적화 설정, 핵심 정보 페이지의 SSR/정적 여부.
- **시나리오·수준:** D L3 (재난·공공 도메인)
- **처방:** 티어0: 핵심 페이지 정적 생성·경량화, PWA 오프라인 캐시. 모든 티어: 텍스트 우선 경량 모드.
- **검증:** Playwright·Lighthouse 네트워크 스로틀링(느린 3G)·오프라인 모드에서 핵심 정보 표시 확인.
- **비용 영향:** 감소(전송량 감소).
- **출처:** https://web.dev/articles/offline-cookbook (2026-10-01) ⚠️출처확인필요

### D-111 정적 비상 페이지
- **무엇/왜:** 앱·DB·BaaS가 전부 죽어도 오브젝트 스토리지·CDN에서 서빙되는 정적 비상 페이지(공지, 대체 연락처, 마지막 업데이트 시각)가 있으면 사용자가 "서비스 없음"과 "서비스 장애 중"을 구분할 수 있다. CDN 오리진 그룹의 보조 오리진으로 연결한다(D-090).
- **실패 양상:** 장애 중 사용자는 브라우저 오류만 보고, 재난 정보를 다른 곳에서 찾지 못한다.
- **신호:** 🔴 대부분 없음. 🟢 `maintenance.html`, 오리진 그룹, Vercel `rewrites`의 폴백.
- **시나리오·수준:** D L3
- **처방:** 티어0: 별도 정적 호스팅(다른 공급자)에 비상 페이지. 티어1·2: S3/GCS 정적 사이트 + CDN 보조 오리진.
- **검증:** 오리진 차단 시 비상 페이지 표시 확인.
- **비용 영향:** 증가(미미).
- **출처:** https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html (2026-10-01) — 오리진 페일오버 근거. 비상 페이지 운영은 일반 원칙(출처 미확인) ⚠️근거없음

### D-112 장애 공지 채널을 같은 인프라에 두지 않음
- **무엇/왜:** 상태 페이지·공지가 서비스와 같은 클라우드·같은 도메인·같은 BaaS에 있으면 장애 때 함께 사라진다.
- **실패 양상:** 장애 공지를 올릴 상태 페이지가 같은 Vercel 프로젝트라 같이 다운.
- **신호:** 🟡 `status.` 서브도메인이 같은 호스팅을 가리킴. 🔴 대부분 코드 밖.
- **시나리오·수준:** D L3
- **처방:** 모든 티어: 외부 상태 페이지 서비스 또는 다른 공급자의 정적 호스팅.
- **검증:** 운영 인프라 차단 상태에서 상태 페이지 갱신 리허설.
- **비용 영향:** 증가(소폭).
- **출처:** 일반 원칙(출처 미확인) ⚠️근거없음

### D-113 평시 저트래픽 서비스의 휴면 위험
- **무엇/왜:** 재난 서비스는 평시엔 거의 안 쓰이다가 재난 순간 폭증한다. 스케일 투 제로(Cloud Run 기본 최소 0), 서버리스 콜드 스타트, Supabase Free의 7일 비활성 일시정지는 평시 비용을 줄이지만 "첫 순간"에 응답이 늦거나 아예 없다. Cloud Run은 최소 인스턴스로 0에서의 확장 지연을 줄이라고 한다.
- **실패 양상:** 지진 직후 첫 1분 동안 콜드 스타트·일시정지 해제 대기로 응답 없음 → 사용자가 재시도 폭주(D-082).
- **신호:** 🟢 Cloud Run `min_instance_count` 0/미설정, HPA·KEDA `minReplicaCount: 0`, Supabase(D-003). 🟡 도메인 = 재난.
- **시나리오·수준:** D L3 & T L3 (설계 문서 TIER-003과 같은 방향의 D 측 근거)
- **처방:** 티어0: 유료 플랜(일시정지 방지). 티어1: 최소 인스턴스 ≥ 1. 티어2: 최소 레플리카 + 노드 여유.
- **검증:** 장시간 유휴 후 순간 부하 테스트(첫 요청 지연 측정).
- **비용 영향:** 증가. 최소 인스턴스는 유휴 요율로 과금(설계 문서 S21).
- **출처:** https://docs.cloud.google.com/run/docs/configuring/min-instances · https://supabase.com/docs/guides/platform/free-project-pausing (2026-10-01)

## 14. 검증과 리허설

### D-114 장애 주입 실험 카탈로그
- **무엇/왜:** 설정이 있다고 동작이 보장되지 않는다(설계 문서 §8.3: control 규칙은 검증 ID 필수). D 통제마다 대응하는 장애 주입이 있어야 한다. Well-Architected는 실패 경로가 드물게 실행되면 정작 필요할 때 동작하지 않는다고 하고, EKS 모범 사례는 카오스 엔지니어링으로 단일 장애점을 찾으라고 한다.
- **실패 양상:** 서킷 브레이커·stale 캐시·읽기 전용 모드를 구현했지만 한 번도 발동시켜 보지 않아 버그가 장애 당일 드러난다.
- **신호:** 🟢 장애 시나리오 테스트(예시 앱: testcontainers로 Postgres·Redis 장애 테스트, nginx 장애 동작 테스트), Chaos Mesh·Litmus 매니페스트, AWS FIS 템플릿(`aws_fis_experiment_template`).
- **시나리오·수준:** D L2 이상 (L2: 페일오버 실험, L3: 의존성별 전체 행렬)
- **처방:** 모든 티어: 최소 카탈로그 — Pod/태스크 종료, 존 하나 차단, DB 페일오버, Redis 페일오버, 의존성 지연·오류 주입, 외부 SaaS 도메인 차단, 캐시 플러시.
- **검증:** P4 검증 루프에서 실행하고 D-071 행렬과 대조.
- **비용 영향:** 증가(실험 환경·도구).
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_for_recovery_dr_tested.html · https://docs.aws.amazon.com/eks/latest/best-practices/application.html (2026-10-01)

### D-115 게임데이와 런북
- **무엇/왜:** Well-Architected는 "프로덕션에서 페일오버를 한 번도 실행하지 않음"을 안티패턴으로 들고, 복구 경로는 적게 유지하며 자주 실행해야 동작한다고 한다. 리허설 중 런북을 쓰며 문제를 기록하고 다음 테스트 전에 고친다.
- **실패 양상:** 복구 절차가 담당자 한 명의 머릿속에만 있다.
- **신호:** 🟡 `docs/runbook*`, `RUNBOOK.md`, `docs/deploy.md`의 장애 절차 절. 🔴 없음.
- **시나리오·수준:** D L2 이상 (L3는 정기 게임데이)
- **처방:** 모든 티어: 장애 유형별 런북(감지 → 판단 → 조치 → 확인 → 복귀), 분기별 게임데이.
- **검증:** 게임데이 결과(소요 시간, 막힌 단계)를 리포트에 기록.
- **비용 영향:** 중립(사람 시간).
- **출처:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_for_recovery_dr_tested.html · https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/testing-disaster-recovery.html (2026-10-01)

### D-116 매니지드 HA 페일오버의 실제 시험
- **무엇/왜:** Multi-AZ·HA를 "켰다"는 것과 앱이 페일오버를 견딘다는 것은 다르다. RDS는 "reboot with failover"로 수동 페일오버를 일으킬 수 있고, ElastiCache는 `test-failover` API(24시간당 최대 15개 샤드, 대규모 장애 중에는 AWS가 막을 수 있음)를 제공한다. Cloud SQL은 페일오버 중 약 60초 불가다.
- **실패 양상:** DB 페일오버는 60초에 끝났는데 앱의 커넥션 풀이 10분 동안 회복되지 않는다(D-032).
- **신호:** 🟢 Multi-AZ·HA 설정은 있음(D-030·D-033) + 페일오버 테스트 스크립트·CI 잡 없음.
- **시나리오·수준:** D L2 이상
- **처방:** 티어1·2: 분기별 수동 페일오버를 부하 중 실행하고 "앱 오류율 정상화 시간"을 측정. 티어0: 공급자 제공 기능이 없으면 가정으로 표시.
- **검증:** 페일오버 중 요청 오류 수·지속 시간·데이터 유실(Redis) 기록.
- **비용 영향:** 중립(테스트 시간).
- **출처:** https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZ.Failover.html · https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/AutoFailover.html · https://docs.cloud.google.com/sql/docs/postgres/high-availability (2026-10-01)

---

## 새 축·규칙 후보

설계 문서(§4 시나리오 × 수준, §8 규칙)에 반영을 제안하는 사항이다.

1. **D L3 가정 RPO "1분 이하"는 PITR만으로는 달성 불가하다.** RDS PITR은 트랜잭션 로그를 5분마다 업로드하고(D-004), Supabase PITR의 최악 RPO는 2분이다. 존 장애는 동기 복제(Multi-AZ·Cloud SQL HA)로 RPO≈0이지만, 리전 장애에서 RPO 1분 이하는 Aurora 글로벌(보통 1초 미만 지연) 같은 연속 교차 리전 복제가 있어야 한다. 제안: D L3 가정을 "존 장애 RPO 0 / 리전 장애 RPO ≤ 수 분"처럼 장애 범위별로 나누거나, L3 통제에 교차 리전 연속 복제를 명시. 또한 D L2 "RPO 5분"은 RDS PITR과 정확히 경계값이므로 리포트에 "경계"로 표시.
2. **D를 "가용성(D-avail)"과 "데이터 복구(D-data)" 두 하위 축으로 분리.** 복제는 논리적 손상을 막지 못한다(D-020). 커뮤니티 앱은 D-avail L1이어도 D-data L2(PITR)가 필요할 수 있고, 반대로 무상태 재난 정보 중계 서비스는 D-avail L3이지만 D-data L1일 수 있다. 하나의 수준으로 묶으면 과잉·부족이 동시에 생긴다.
3. **"모든 수준" 위생 규칙 분류(HYG) 신설.** 인증서 자동 갱신 조건(D-087·D-088), 도메인 만료(D-089), 헬스 엔드포인트(D-058), 타임아웃 명시(D-061)는 D L0(영속 데이터 없음)이어도 서비스를 멈출 수 있다. 현재 D L0 정의("영속 데이터 없음 → 불필요")에 걸러지지 않도록 수준과 무관한 규칙군이 필요하다.
4. **플랫폼 플랜을 사실(Fact)로 다루는 축.** Supabase Free(백업 없음·7일 일시정지), Vercel Hobby/Pro/Enterprise(리전 수·페일오버), Memorystore Basic/Standard처럼 D 통제가 "플랜·등급"에 묶여 있다. 코드에 플랜이 없으므로 🔴 가정이 되는데, 티어0 처방의 상당수가 "플랜 업그레이드"이고 비용 필터에 플랜 가격이 들어가야 한다. 제안: `platform_plan` 가정 항목을 리포트 상단 가정 목록에 추가하고 기본값은 무료 등급.
5. **결합 시나리오 D×T.** 재난 서비스는 D L3과 T L3이 동시에 온다(D-109, D-113). P4 검증에 "피크 부하 중 존 하나 제거", "피크 부하 중 Redis 페일오버"를 표준 시나리오로 추가하고, 잔여 용량 규칙(D-035)은 T의 피크 가정을 입력으로 받게 한다.
6. **복구 경로의 컨트롤 플레인 의존 정적 검사 규칙.** 런북·스크립트에서 `create-*`, `change-resource-record-sets`, `terraform apply`, IAM 수정 같은 컨트롤 플레인 호출을 찾아 D L3에서 경고(D-084, D-099~D-102). 저장소에 런북이 있을 때만 적용 가능한 🟢 규칙이 된다.
7. **헬스 체크 모순 규칙.** "디그레이드 코드(stale 캐시·큐 접수)가 있는데 readiness/LB 헬스 체크가 그 의존성을 검사"(D-055·D-056)는 단일 사실이 아니라 두 사실의 조합으로만 판정된다. 규칙 엔진에 사실 간 조합 조건(AND) 지원이 필요하다.
8. **과잉 탐지(COST) 후보.** D L3 미만인데 멀티 리전 액티브-액티브(D-044), 셀 아키텍처(D-105), Vault Lock 규정 준수 모드(D-008, 보존 기간 중 비용 회수 불가)를 발견하면 과잉으로 보고.
9. **외부 의존성 인벤토리를 1급 사실로.** SDK 목록에서 인증·결제·이메일·LLM·분석 의존을 추출하고 요청 경로별 하드/소프트 여부를 판정하는 단계(D-071, D-092~D-098)가 있으면 "장애 격리 표"(예시 앱 README 형식)를 자동 생성할 수 있다. 이 표가 D L3 리포트의 핵심 산출물이 된다.
10. **프론트엔드(클라이언트) 회복력 하위 영역.** 재접속 지터(D-082), 서드파티 스크립트(D-098), 오프라인·저대역폭(D-110)은 백엔드 인프라 바깥이지만 재난 시나리오의 실제 체감 가용성을 좌우한다. 탐지 대상에 프론트엔드 코드를 포함하고 D L3에서만 적용.
11. **설계 문서 D-CTL-001 보강.** "보존 기간 ≥ 7일"에 더해 삭제 시 백업 동반 삭제(D-012), `skip_final_snapshot`(D-011), Storage 객체 미포함(D-005)을 같은 통제 묶음으로 넣는 것을 제안. 세 가지 모두 Terraform·코드로 🟢 판정 가능하다.
