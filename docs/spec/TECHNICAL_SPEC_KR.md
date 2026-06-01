# 기술명세서

- 문서 역할: 기술명세서
- 정본 여부: `canonical`
- 이 문서가 답하는 질문: API/DB/상태/이벤트/필드/외부 연동 계약은 무엇인가
- 이 문서가 답하지 않는 질문: 왜 이 기능이 필요한가, 어떤 화면이 더 좋은가, 운영 우선순위는 무엇인가
- 상위 기준 문서: [00_CANONICAL_INDEX_KR.md](../00_CANONICAL_INDEX_KR.md), [FUNCTIONAL_SPEC_KR.md](./FUNCTIONAL_SPEC_KR.md), [SYSTEM_DESIGN_KR.md](./SYSTEM_DESIGN_KR.md)
- 충돌 시 우선 문서: [00_CANONICAL_INDEX_KR.md](../00_CANONICAL_INDEX_KR.md)

작성일: 2026-03-22  
상태: 통합 초안 v1

## 1. 문서 목적

이 문서는 현재 분산되어 있는 기술 계약 문서를 하나의 본문 기준으로 통합하기 위한 `기술명세 정본`이다.

현재 기준으로 기술 계약은 아래 문서에 흩어져 있다.

- [reference/source/TECHNICAL_SPEC_GUI_PARITY_KR.md](../reference/source/TECHNICAL_SPEC_GUI_PARITY_KR.md)
- [reference/contracts/api-spec.md](../reference/contracts/api-spec.md)
- [reference/contracts/db-schema.md](../reference/contracts/db-schema.md)
- [reference/contracts/job-lifecycle.md](../reference/contracts/job-lifecycle.md)
- [reference/contracts/request-response-examples.md](../reference/contracts/request-response-examples.md)

본 문서는 위 문서들을 대체하는 것이 아니라, 우선순위를 묶는 `기술명세 본문` 역할을 한다. 상세 계약과 예시는 당분간 부속 reference 문서에 남겨두고, 추후 점진적으로 흡수한다.

## 2. 문서 경계

이 문서에 포함:

1. 시스템 상태 모델
2. 엔터티와 식별자 모델
3. API/DB/이벤트/필드 계약의 상위 기준
4. Phase 1 GUI parity 구현에 필요한 기술 규칙
5. Phase 2 Auth/Organization 도입에 따른 기술 표준

이 문서에서 제외:

1. 기능 우선순위와 제품 로드맵
2. 운영 정책의 상세 판단
3. 리뷰/실험/핸드오프 기록
4. 화면 카피와 세부 UI 배치

## 3. 기술 기준 원칙

1. 기능 요구사항은 [FUNCTIONAL_SPEC_KR.md](./FUNCTIONAL_SPEC_KR.md)를 따른다.
2. 시스템 경계와 컴포넌트 책임은 [SYSTEM_DESIGN_KR.md](./SYSTEM_DESIGN_KR.md)를 따른다.
3. API/DB/상태/이벤트 계약 충돌 시 본 문서를 우선한다.
4. 예시 문서는 이해를 돕기 위한 참고이며, 계약 충돌 시 본문이 우선한다.

## 4. 용어 표준

아래 용어는 기술 문서 전체에서 표준으로 사용한다.

- `platform_admin`
- `org_admin`
- `org_member`
- `organization`
- `membership`
- `account_status`
- `membership_status`

추가 원칙:

1. `platform_admin`은 조직 역할 안에 넣지 않는다.
2. 단순 `users.organization_id` 구조를 최종 권한 모델로 사용하지 않는다.
3. 조직 권한은 `membership` 기준으로 해석한다.

### 4.1 식별자 모델

핵심 식별자:

- `run_id`
- `artifact_id`
- `tracker_entry_id`
- `entry_key`
- `project_id`
- `user_profile_id`
- `membership_id`
- `invitation_id`

규칙:

1. 외부 노출 식별자는 UUID를 기본으로 한다.
2. `entry_key`는 사용자 표시용이 아니라 stable matching key다.
3. 영업 claim 잠금 기준은 `entry_id`가 아니라 `project_id`다.
4. 감사 로그는 `target_type + target_id` 조합으로 대상을 식별한다.

## 5. 상태 모델

### 5.1 파이프라인 실행 상태

- `queued`
- `running`
- `success`
- `failed`
- `cancelled`

진행 필드:

- `progress_stage`
- `progress_current`
- `progress_total`
- `cancel_requested`

### 5.2 계정/조직 상태

- `account_status`
  - `active`
  - `inactive`
  - `deactivated`
- `membership_status`
  - `active`
  - `inactive`
  - `deactivated`
- invitation status
  - `pending`
  - `accepted`
  - `expired`
  - `revoked`

### 5.3 실행 상태 전이 규칙

허용 전이:

| 현재 | 이벤트 | 다음 |
| --- | --- | --- |
| `queued` | 워커 시작 | `running` |
| `queued` | 실행 전 취소 승인 | `cancelled` |
| `running` | 정상 완료 | `success` |
| `running` | 예외 발생 | `failed` |
| `running` | 취소 반영 | `cancelled` |

허용하지 않는 전이:

1. `success -> running`
2. `failed -> running`
3. `cancelled -> running`
4. `success -> failed`

### 5.4 보조 진행 필드

- `cancel_requested: boolean`
- `progress_stage: text`
- `progress_current: integer`
- `progress_total: integer`

규칙:

1. `progress_stage`는 현재 단계명을 가진다.
2. `progress_total = 0`은 총량 미확정 상태를 허용한다.
3. `running` 상태에서만 진행률을 신뢰한다.

## 6. 엔터티 기준

### 6.1 파이프라인 엔터티

- `pipeline_runs`
- `pipeline_logs`
- `run_artifacts`
- `saved_run_presets`
- `projects` 선택

### 6.2 Auth/Organization 엔터티

- `user_profiles`
- `organization_memberships`
- `invitations`
- `audit_logs`

### 6.3 영업 파이프라인 엔터티

- `project_sales_claims`
- `project_sales_claim_events`

### 6.4 엔터티 분리 원칙

1. 인증 사용자는 Supabase Auth가 가진다.
2. 앱 프로필은 `user_profiles`에 둔다.
3. 조직 소속과 조직 역할은 `organization_memberships`에 둔다.
4. 초대는 `invitations`에서 lifecycle을 관리한다.
5. 영업 현재 상태는 `project_sales_claims`, 이력은 `project_sales_claim_events`에서 분리한다.

## 7. 실행 모델 기준

1. 부모 run은 `project_tracker`
2. child run은 `tracker_export`
3. `tracker_export`는 부모 run의 후처리 실행이며 부모 run 상태를 직접 실패로 되돌리지 않는다
4. tracker export 결과는 tracker row와 tracking workbook 생성으로 이어진다

### 7.1 run_type 기준

- `project_tracker`
- `tracker_export`

### 7.2 단계 모델

`project_tracker` 단계:

1. `collect`
2. `filter`
3. `rescan`
4. `export`
5. `finalize`

`tracker_export` 단계:

1. `tracker_export`
2. `finalize`

### 7.3 child run 규칙

1. `POST /api/runs/{run_id}/tracker-export`는 기존 run을 재사용하지 않는다.
2. 항상 새 child run을 만든다.
3. child run은 `parent_run_id`로 부모 `project_tracker`를 참조한다.
4. child run 실패는 부모 run을 실패로 되돌리지 않는다.

## 8. API 계약 기준

필수 API 묶음:

1. 파이프라인 실행 API
2. 로그/아티팩트 조회 API
3. 트래커 조회/수정 API
4. Auth/Profile/Membership API
5. 영업 claim / transfer / close API

세부 계약은 [reference/contracts/api-spec.md](../reference/contracts/api-spec.md)를 부속 문서로 유지한다.

### 8.0 공통 응답 규칙

1. validation 실패는 `400`을 사용한다.
2. 인증 실패는 `401`을 사용한다.
3. 권한 부족은 `403`을 사용한다.
4. 존재하지 않는 리소스는 `404`를 사용한다.
5. 이미 잠긴 영업 대상에 대한 중복 claim은 `409`를 사용할 수 있다.
6. 목록 응답은 가능하면 `items/page/page_size/total` 구조를 유지한다.

### 8.1 파이프라인 API 핵심 엔드포인트

1. `POST /api/runs`
2. `GET /api/runs`
3. `GET /api/runs/{run_id}`
4. `POST /api/runs/{run_id}/cancel`
5. `GET /api/runs/{run_id}/logs`
6. `GET /api/runs/{run_id}/artifacts`
7. `POST /api/runs/{run_id}/tracker-export`

### 8.2 트래커 API 핵심 엔드포인트

1. `GET /api/tracker-entries`
2. `PATCH /api/tracker-entries/{id}`
3. `GET /api/tracker-entries/{id}/audit-logs`

규칙:

1. 트래커 편집은 1회 요청당 1개 field만 수정한다.
2. 웹 표시값은 `effective value` 기준이다.
3. 감사 로그를 반드시 남긴다.

### 8.3 Auth/Profile/Membership API 핵심 엔드포인트

1. `GET /api/auth/session`
2. `POST /api/auth/login`
3. `POST /api/auth/logout`
4. `PATCH /api/auth/profile`
5. `GET /api/auth/users`
6. `GET /api/auth/invitations`
7. `GET /api/auth/audit-logs`
8. `POST /api/auth/invitations`
9. `POST /api/auth/invitations/accept`

### 8.4 영업 API 핵심 엔드포인트

1. `GET /api/sales-claims`
2. `GET /api/sales-claims/summary-by-user`
3. `POST /api/sales-claims/{project_id}/claim`
4. `PATCH /api/sales-claims/{project_id}`
5. `POST /api/sales-claims/{project_id}/transfer`
6. `POST /api/sales-claims/{project_id}/release`
7. `POST /api/sales-claims/{project_id}/close`

### 8.5 invitation 수락 기술 규칙

1. 초대 수락은 같은 토큰에 대해 여러 번 호출돼도 안전해야 한다.
2. 수락 시 membership 생성/연결은 transaction으로 묶는다.
3. 초대 이메일과 실제 인증 이메일이 다르면 수락되지 않는다.
4. `pending`이 아닌 invitation은 수락 대상이 아니다.
5. 초대 생성 시 `actor role`과 `target role` 조합을 검증해야 한다.
6. `GET /api/auth/invitations`는 `items` 외에 `plan_summary`를 함께 반환할 수 있어야 하며, `items`는 actor role 기준으로 관리 가능한 pending invite만 포함한다.
7. `plan_summary`는 최소 `plan_code`, `plan_label`, `active_user_count`, `pending_invite_count`, `remaining_*`, `upgrade_required`, `upgrade_message`를 포함할 수 있어야 한다.
8. 초대 생성은 DB transaction/RPC 내부에서 stale expire, org lock, `pending invite limit`/`active user limit` 재검증, insert를 한 번에 처리해야 한다.
9. 초대 수락 시 `active user limit`를 다시 검증해야 한다.
10. `GET /api/auth/audit-logs`는 actor organization 범위 최근 이벤트를 반환하고, 표시용 actor 메타를 함께 제공할 수 있어야 한다.
11. 현재 감사로그 조회 범위는 self-service 운영 추적용 최근 이벤트 확인까지만 포함하며, cross-org 검색, 고급 필터, 내보내기 기능은 후속 운영 고도화 범위로 분리한다.

### 8.6 세션/프로필 API 기술 규칙

1. `GET /api/auth/session`은 인증 여부뿐 아니라 앱 권한 해석 결과를 함께 반환한다.
2. 세션 응답은 최소 `authenticated`, `authorized`, `email`, `global_role`, `memberships`, `active_membership`를 포함할 수 있어야 한다.
3. `PATCH /api/auth/profile`은 현재 비밀번호 검증 실패 시 프로필 필드 변경도 거부한다.
4. 보호 API는 세션이 없으면 `401`, 세션은 있지만 membership이 없거나 비활성이면 `403`을 반환한다.
5. 현재는 단일 활성 세션을 보장하지 않으며, 현재 범위는 signed cookie + refresh 세션 유지까지다.
6. 단일 활성 세션 강제와 세션 동시성 제어는 별도 hardening 단계로 분리한다.

### 8.7 엑셀 다운로드 API 기술 규칙

1. 영업 목록 다운로드는 로컬 tracker workbook 양식을 재사용한다.
2. `my` 범위와 `company` 범위 다운로드는 같은 workbook 구조를 사용하고 데이터 범위만 다르게 적용한다.
3. 다운로드 응답은 화면 카드와 같은 effective 값을 사용한다.
4. 다운로드 생성은 tracker 원본 row를 수정하지 않는다.

## 9. DB 계약 기준

1. Auth 사용자와 앱 프로필을 분리한다.
2. 앱 프로필과 조직 소속을 분리한다.
3. 전역 역할과 조직 역할을 분리한다.
4. hard delete보다 상태 전이를 우선한다.
5. 영업 owner 변경은 release보다 transfer 중심으로 기록한다.

### 9.1 파이프라인 데이터 모델 원칙

1. `pipeline_runs`는 실행 기준 테이블이다.
2. `pipeline_logs`는 append-only 로그 테이블이다.
3. `run_artifacts`는 산출물 메타와 저장 경로를 가진다.
4. `saved_run_presets`는 저장된 실행 조건을 가진다.

### 9.2 트래커 데이터 모델 원칙

1. `tracker_entries`는 화면 표시용 현재값 테이블이다.
2. `*_source`는 파이프라인이 생성한 값이다.
3. `*_override`는 사용자가 수정한 값이다.
4. 화면 표시값은 `coalesce(*_override, *_source)` 원칙을 따른다.
5. `entry_key`는 재실행 후에도 안정적으로 같은 row를 찾기 위한 stable key다.

세부 규칙:

1. `null override`는 사용자 수정 없음이다.
2. 빈 문자열 override는 사용자가 의도적으로 비운 값이다.
3. effective view는 읽기 전용이다.
4. 실제 수정은 base table 또는 전용 RPC에서 수행한다.

### 9.3 Auth/Organization 데이터 모델 원칙

1. `user_profiles.id`는 가능하면 `auth.users.id`와 동일 UUID를 사용한다.
2. `organization_memberships`는 실질적인 조직 권한 본체다.
3. `(organization_id, user_profile_id)`는 unique해야 한다.
4. `platform_admin`은 membership 바깥의 전역 역할로 해석한다.
5. 조직 플랜/한도는 `organizations`에서 관리한다.

권장 필드:

1. `global_role`
2. `account_status`
3. `membership_status`
4. `team_name`
5. `job_title`
6. `mobile_phone`
7. `office_phone`
8. `plan_code`
9. `active_user_limit`
10. `pending_invite_limit`

추가 규칙:

1. `plan_code`는 현재 기준 `A/B/C`를 사용한다.
2. `active_user_limit`은 `active account + active membership` 사용자 수 기준이다.
3. `pending_invite_limit`은 `pending invitations` 수 기준이다.
4. 정책/계약/API 응답/UI 라벨은 `active_user_limit`, `pending_invite_limit`를 표준 용어로 사용한다.
5. `platform_admin`은 기본 seat 계산에서 제외할 수 있다.

### 9.4 Invitation 데이터 모델 원칙

최소 필드:

1. `organization_id`
2. `email`
3. `role`
4. `status`
5. `invite_token`
6. `expires_at`
7. `accepted_at`
8. `accepted_user_id`
9. `created_by`

권장 추가 필드:

1. `display_name`
2. `team_name`
3. `job_title`
4. `expires_days`

### 9.5 Audit 데이터 모델 원칙

최소 필드:

1. `organization_id`
2. `actor_user_id`
3. `actor_membership_id`
4. `event_type`
5. `target_type`
6. `target_id`
7. `payload_json`
8. `created_at`

### 9.6 Sales Claim 데이터 모델 원칙

현재 상태 필드:

1. `project_id`
2. `owner_user_id`
3. `owner_membership_id`
4. `claimed_at`
5. `owner_assigned_at`
6. `claim_status`
7. `closed_at`
8. `closed_by`

이력 이벤트 예시:

1. `claimed`
2. `note_added`
3. `transferred`
4. `released`
5. `force_released`
6. `closed_won`
7. `closed_lost`
8. `admin_note_deleted`

### 9.7 트랜잭션/일관성 규칙

1. invitation 수락은 `invitation 상태 변경 + membership 생성/연결 + audit 기록`을 하나의 transaction으로 묶는다.
2. sales claim transfer는 `현재 owner 갱신 + event row 추가 + audit 기록`을 하나의 일관된 작업으로 본다.
3. claim close는 `claim_status`, `closed_at`, `closed_by`, 필요 시 `contract_amount_text` 반영이 한 번에 끝나야 한다.
4. 화면 요약 응답이 늦게 갱신되더라도 원본 상태 row와 이벤트 row가 먼저 일관성을 가져야 한다.

### 9.8 읽기 모델 생성 규칙

1. `내가 진행 중인 영업`, `회사 전체 진행 중인 영업`, `종료/완료 정리`는 모두 claim/event 원본에서 파생된 읽기 모델이다.
2. summary 응답은 화면 최적화 목적이며, 원본 상태/이력 계약을 대체하지 않는다.
3. `전체 영업 대상 프로젝트` 목록은 `미배정 + 미종료` 조건을 적용한 읽기 모델이다.

## 10. 이벤트/감사 계약 기준

최소 감사로그 이벤트:

- `invite_created`
- `invite_revoked`
- `invite_accepted`
- `membership_role_changed`
- `membership_deactivated`
- `project_transferred`

추가 원칙:

1. 이벤트는 현재 상태 테이블과 별개로 append-only로 남긴다.
2. sales claim은 현재 상태와 이력 로그를 함께 가진다.
3. 초대 수락은 idempotent + transaction 기준으로 구현한다.

### 10.1 영업 이벤트 저장 규칙

1. 메모는 append-only를 기본으로 한다.
2. 일반 사용자 메모 삭제는 허용하지 않는다.
3. 관리자 삭제는 예외적 관리 액션으로 기록한다.
4. transfer/release/close는 모두 별도 이벤트로 남긴다.

### 10.2 actor 기록 규칙

1. invitation 관련 이벤트는 `actor_user_id`와 가능하면 `actor_membership_id`를 함께 남긴다.
2. sales claim 관련 이벤트는 `actor_user_id`, `actor_membership_id`, `project_id`를 함께 남긴다.
3. 시스템 이벤트라도 payload에서 `system`과 `human actor`를 구분할 수 있어야 한다.
4. 관리자 강제 해제/강제 삭제는 일반 사용자 액션과 다른 event type으로 구분한다.

## 11. 메일/외부 인증 기술 기준

1. 인증/초대/비밀번호 재설정 메일은 `Supabase Auth + Custom SMTP` 기준으로 운영한다.
2. 현재 임시 운영 채널은 `Gmail SMTP`다.
3. 장기 운영 채널은 `Resend + 회사 도메인 기반 no-reply 주소`다.
4. 이 부분의 운영 판단은 [OPERATIONS_POLICY_KR.md](./OPERATIONS_POLICY_KR.md)를 따른다.

### 11.1 발신 주소 원칙

1. 초기 개발/임시 운영에서는 `Gmail SMTP`를 사용할 수 있다.
2. 장기 운영에서는 `no-reply@회사도메인` 계열 발신 주소를 사용한다.
3. 공급자 교체가 가능하도록 SMTP 경계를 유지한다.

### 11.2 세션/토큰 기술 기준

1. 앱 세션 cookie와 Supabase access token은 분리해서 본다.
2. access token은 짧은 수명을 가져도 refresh token으로 연장 가능해야 한다.
3. 앱은 장기 로그인 유지를 위해 refresh 기반 세션 복원을 지원한다.
4. 세션 만료 정책의 운영 판단은 [OPERATIONS_POLICY_KR.md](./OPERATIONS_POLICY_KR.md)를 따른다.

### 11.3 메일 공급자 추상화 원칙

1. 초대/가입/비밀번호 재설정 메일은 `Supabase Auth`가 보내더라도, 공급자 선택은 SMTP 설정 레이어에서 바꿀 수 있어야 한다.
2. `Gmail SMTP`는 임시 공급자, `Resend + 회사 도메인`은 목표 공급자로 분리해 기술적으로 교체 가능해야 한다.
3. 메일 본문 템플릿, 발신 주소, redirect URL은 공급자 교체와 분리된 설정 요소로 관리한다.

## 12. 부속 reference 문서

- [reference/source/TECHNICAL_SPEC_GUI_PARITY_KR.md](../reference/source/TECHNICAL_SPEC_GUI_PARITY_KR.md)
- [reference/contracts/api-spec.md](../reference/contracts/api-spec.md)
- [reference/contracts/db-schema.md](../reference/contracts/db-schema.md)
- [reference/contracts/job-lifecycle.md](../reference/contracts/job-lifecycle.md)
- [reference/contracts/request-response-examples.md](../reference/contracts/request-response-examples.md)

## 13. 다음 통합 대상

향후 아래 항목을 본문으로 더 흡수한다.

1. `reference/contracts/api-spec.md`의 상세 request/response 계약
2. `reference/contracts/db-schema.md`의 최신 auth/org 테이블 모델
3. `reference/contracts/job-lifecycle.md`의 상태 전이 표
4. `reference/source/TECHNICAL_SPEC_GUI_PARITY_KR.md`의 fallback/후처리 규칙
5. workbook 다운로드 상세 계약

