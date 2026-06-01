# API Spec

- 문서 역할: API 계약 reference
- 정본 여부: `reference`
- 이 문서가 답하는 질문: 현재 HTTP API 계약과 request/response 흐름은 어떻게 정의되는가
- 상위 기준 문서: [04_TECHNICAL_SPEC_KR.md](../../spec/TECHNICAL_SPEC_KR.md)
- 충돌 시 우선 문서: [04_TECHNICAL_SPEC_KR.md](../../spec/TECHNICAL_SPEC_KR.md)

## 1. 문서 목적

이 문서는 현재 구현 API를 도메인별로 정리한 `부속 계약 문서`다.

정본 기준은 [04_TECHNICAL_SPEC_KR.md](../../spec/TECHNICAL_SPEC_KR.md)이고, 본 문서는 다음을 구체화한다.

1. 엔드포인트 목록
2. 대표 request / response shape
3. 인증/권한 전제
4. 주요 validation 규칙

## 2. 공통 규칙

### 2.1 응답 규칙

1. validation 실패: `400`
2. 인증 실패: `401`
3. 권한 부족: `403`
4. 리소스 없음: `404`
5. 상태 충돌/중복 잠금: `409`

에러 기본 형식:

```json
{
  "error": {
    "code": "validation_error",
    "message": "상세 오류 메시지"
  }
}
```

### 2.2 인증 규칙

1. `/api/auth/session`, `/api/auth/session/import`, `/api/auth/sign-in`, `/api/auth/sign-up`, `/api/auth/sign-out`는 auth shell 기본 API다.
2. 관리자 전용 API는 `platform_admin` 또는 `org_admin`이 필요하다.
3. 초대 수락은 초대 이메일과 실제 로그인 이메일이 일치해야 한다.

## 3. Auth API

### 3.1 세션 조회

`GET /api/auth/session`

응답:

```json
{
  "enabled": true,
  "authenticated": true,
  "authorized": true,
  "bootstrap_email": "yhm8029@gmail.com",
  "message": "",
  "user": {
    "auth_user_id": "uuid",
    "local_user_id": "uuid",
    "membership_id": "uuid",
    "email": "user@example.com",
    "display_name": "홍길동",
    "role": "org_admin",
    "status": "active",
    "account_status": "active",
    "membership_status": "active",
    "organization_id": "uuid",
    "organization_name": "Internal Operations",
    "mobile_phone": "",
    "office_phone": ""
  }
}
```

### 3.2 세션 import

`POST /api/auth/session/import`

요청:

```json
{
  "access_token": "supabase_access_token",
  "refresh_token": "supabase_refresh_token"
}
```

용도:

1. 이메일 초대 링크 또는 외부 로그인 후 브라우저 hash/token을 앱 세션으로 가져온다.
2. 성공 시 앱 쿠키 세션을 다시 쓴다.

### 3.3 로그인

`POST /api/auth/sign-in`

요청:

```json
{
  "email": "user@example.com",
  "password": "secret-password",
  "display_name": "",
  "invite_token": ""
}
```

규칙:

1. 이메일/비밀번호 로그인
2. `invite_token`이 있으면 로그인 후 초대 수락 흐름과 연결될 수 있다

### 3.4 가입

`POST /api/auth/sign-up`

요청:

```json
{
  "email": "user@example.com",
  "password": "secret-password",
  "display_name": "홍길동",
  "invite_token": "optional_invite_token"
}
```

규칙:

1. Phase 2 기준 가입은 사실상 초대 기반을 전제로 한다.
2. `invite_token`이 있는 경우 초대 이메일과 가입 이메일이 같아야 한다.
3. mismatch면 가입/수락이 실패한다.

### 3.5 로그아웃

`POST /api/auth/sign-out`

효과:

1. 서버 세션 payload 정리
2. 앱 쿠키 삭제

### 3.6 회원정보 수정

`PATCH /api/auth/profile`

요청:

```json
{
  "display_name": "홍길동",
  "mobile_phone": "010-0000-0000",
  "office_phone": "02-000-0000",
  "current_password": "현재 비밀번호",
  "password": "새 비밀번호"
}
```

규칙:

1. `display_name`, `mobile_phone`, `office_phone`, 비밀번호 수정 지원
2. 현재 비밀번호 확인이 필요하다
3. 수정 후 세션 응답을 새 값으로 다시 돌려준다

## 4. Invitation API

### 4.1 초대 목록 조회

`GET /api/auth/invitations`

규칙:

1. 관리자만 조회 가능
2. 현재 운영 UI는 `pending` 초대 중심으로 보여준다
3. `platform_admin`은 `org_admin`, `org_member` pending invite를 모두 조회/관리할 수 있다.
4. `org_admin`은 자신이 관리 가능한 `org_member` pending invite만 조회/관리할 수 있다.
5. `plan_summary`의 카운트는 조직 전체 기준이며, `items`는 actor role 기준으로 더 적을 수 있다.

응답:

```json
{
  "items": [
    {
      "id": "uuid",
      "organization_id": "uuid",
      "email": "user@example.com",
      "role": "org_member",
      "display_name": "홍길동",
      "team_name": "영업팀",
      "job_title": "대리",
      "invite_token": "token",
      "invite_url": "http://127.0.0.1:8019/app/?invite_token=...",
      "status": "pending",
      "expires_at": "2026-03-29T00:00:00+09:00",
      "accepted_at": null,
      "revoked_at": null,
      "accepted_user_id": null,
      "created_by": "uuid",
      "created_at": "2026-03-22T10:00:00+09:00",
      "updated_at": "2026-03-22T10:00:00+09:00",
      "delivery_status": "sent",
      "delivery_message": ""
    }
  ],
  "plan_summary": {
    "organization_id": "uuid",
    "organization_name": "Internal Operations",
    "plan_code": "A",
    "plan_label": "플랜 A",
    "active_user_limit": 5,
    "pending_invite_limit": 5,
    "active_user_count": 3,
    "pending_invite_count": 2,
    "remaining_active_user_slots": 2,
    "remaining_pending_invite_slots": 3,
    "active_user_limit_reached": false,
    "pending_invite_limit_reached": false,
    "upgrade_required": false,
    "upgrade_message": "",
    "next_plan_code": "B"
  }
}
```

### 4.2 초대 생성

`POST /api/auth/invitations`

요청:

```json
{
  "email": "user@example.com",
  "role": "org_member",
  "display_name": "홍길동",
  "team_name": "영업팀",
  "job_title": "대리",
  "expires_in_days": 7
}
```

규칙:

1. 관리자만 생성 가능
2. 현재 로그인한 본인 이메일로 자기 자신 초대 불가
3. 기본 전달 경로는 초대 링크 + 초기 암호 수동 전달이다
4. 자동 메일 발송은 별도 opt-in 설정일 때만 시도한다
5. 생성은 DB transaction/RPC 내부에서 org 단위 한도를 다시 검증한 뒤 반영한다

### 4.3 초대 수락

`POST /api/auth/invitations/accept`

요청:

```json
{
  "invite_token": "token"
}
```

규칙:

1. 로그인된 세션이 필요하다
2. 로그인 이메일과 초대 이메일이 같아야 한다
3. idempotent하게 동작해야 한다

### 4.4 초대 철회

`POST /api/auth/invitations/{invitation_id}/revoke`

규칙:

1. 관리자만 가능
2. `org_admin`은 `org_member` 초대만 철회할 수 있다
3. `platform_admin`이 만든 `org_admin` 초대는 `platform_admin`만 철회할 수 있다
4. 철회된 초대는 운영 UI에서 더 이상 active 목록으로 볼 필요가 없다

### 4.5 조직 감사 로그 조회

`GET /api/auth/audit-logs?limit=20`

규칙:

1. 관리자만 조회 가능
2. 응답은 현재 actor의 `organization_id` 범위 최근 로그만 반환한다
3. `actor_email`, `actor_display_name`, `actor_role`은 현재 조직 사용자 정보로 enrich한 표시용 필드다
4. 조직 관리자 화면에서는 초대/수락/철회, 역할 변경, 소속 상태 변경 이벤트를 이 API로 보여준다
5. 현재 범위는 self-service 운영 추적용 조회까지만 포함하며, cross-org 검색, 고급 필터, 내보내기 기능은 제공하지 않는다

응답:

```json
{
  "items": [
    {
      "id": 101,
      "organization_id": "uuid",
      "actor_user_id": "uuid",
      "actor_membership_id": "uuid",
      "actor_email": "admin@example.com",
      "actor_display_name": "관리자",
      "actor_role": "org_admin",
      "event_type": "invite_created",
      "target_type": "invitation",
      "target_id": "uuid",
      "payload_json": {
        "email": "member@example.com",
        "role": "org_member"
      },
      "created_at": "2026-03-25T10:00:00+09:00"
    }
  ]
}
```

## 5. Organization User API

### 5.1 사용자 목록 조회

`GET /api/auth/users`

쿼리:

- `include_inactive=false`

규칙:

1. `include_inactive=true`는 관리자만 허용한다
2. 응답은 membership 기준 사용자 목록이다

### 5.2 사용자 상태 변경

`PATCH /api/auth/users/{user_id}/status`

요청:

```json
{
  "status": "inactive"
}
```

규칙:

1. 관리자만 가능
2. bootstrap platform admin 계정은 비활성화 금지
3. 자기 자신의 상태를 이 화면에서 바꾸지 않는다
4. 진행 중 영업이 남아 있으면 비활성화 불가

### 5.3 사용자 소속 정보 수정

`PATCH /api/auth/users/{user_id}`

요청:

```json
{
  "role": "org_admin",
  "membership_status": "active",
  "team_name": "영업팀",
  "job_title": "과장"
}
```

규칙:

1. 관리자만 가능
2. 수정 대상은 membership 역할/상태와 팀/직책이다

## 6. Run API

### 6.1 실행 생성

`POST /api/runs`

요청:

```json
{
  "run_type": "project_tracker",
  "params": {
    "start_date": "20250101",
    "end_date": "20250630",
    "contract_date_hint": "20250715",
    "bid_no": "",
    "notice_title": "건축 설계공모",
    "demand_org": "",
    "rows_per_page": 100,
    "max_pages": 3,
    "api_scope": "construction"
  },
  "advanced_options": {}
}
```

규칙:

1. 현재 기본 run type은 `project_tracker`
2. validation 실패는 `400 validation_error`
3. `requested_by`는 서버가 기록한다

### 6.2 실행 목록

`GET /api/runs`

쿼리:

- `status`
- `run_type`
- `from`
- `to`
- `page`
- `page_size`

### 6.3 실행 상세

`GET /api/runs/{run_id}`

주요 필드:

- `status`
- `run_type`
- `parent_run_id`
- `progress_stage`
- `progress_current`
- `progress_total`
- `cancel_requested`
- `params`
- `summary`
- `error`

### 6.4 실행 취소

`POST /api/runs/{run_id}/cancel`

규칙:

1. `queued` 또는 `running`에서만 허용
2. 먼저 `cancel_requested=true`를 세운다

### 6.5 실행 로그 / 이벤트 / 아티팩트

- `GET /api/runs/{run_id}/logs`
- `GET /api/runs/{run_id}/events`
- `GET /api/runs/{run_id}/artifacts`

### 6.6 tracker export child run 생성

`POST /api/runs/{run_id}/tracker-export`

규칙:

1. 부모 run은 `project_tracker`여야 한다
2. 부모 run 상태는 `success`여야 한다
3. 새 child run을 만들어 `tracker_export`를 수행한다

## 7. Tracker API

### 7.1 트래커 목록

`GET /api/tracker-entries`

쿼리:

- `q`
- `edited_only`
- `source_run_id`
- `source_tracker_run_id`
- `sheet_name`
- `section_name`
- `page`
- `page_size`

규칙:

1. 응답은 effective value 기준이다
2. `coalesce(*_override, *_source)` 규칙을 따른다

### 7.2 누락 리포트

- `GET /api/tracker-entries/missing-report`
- `GET /api/tracker-entries/missing-report/download`

### 7.3 트래커 엔트리 상세

`GET /api/tracker-entries/{entry_id}`

### 7.4 트래커 엔트리 수정

`PATCH /api/tracker-entries/{entry_id}`

규칙:

1. 1회 요청당 1 field 수정
2. 감사 로그를 남긴다

### 7.5 트래커 감사 로그

`GET /api/tracker-entries/{entry_id}/audit-logs`

### 7.6 트래커 변경 이벤트

- `GET /api/tracker-change-events/unread-count`
- `GET /api/tracker-change-events`
- `POST /api/tracker-change-events/mark-read`

규칙:

1. organization 범위 최근 변경 알림과 entry 상세 변경 이력은 같은 이벤트 저장소를 사용한다
2. `include_silent=true`일 때만 조용한 내부 이벤트를 포함한다
3. `mark-read`는 `event_ids` 또는 `tracker_entry_id` 기준으로 동작한다

### 7.7 백필 충돌 검토

- `GET /api/backfill-conflicts`
- `POST /api/backfill-conflicts/{conflict_id}/resolve`

규칙:

1. 기본 목록은 `resolved_at is null`인 열린 충돌만 반환한다
2. `include_resolved=true`일 때 해결된 항목까지 포함한다
3. `resolution`은 `kept_current`, `applied_manually`, `applied_via_backfill`, `dismissed`만 허용한다

## 8. Sales Claim API

### 8.1 진행 중 claim 목록

`GET /api/sales-claims`

### 8.2 진행 중 claim 엑셀 다운로드

`GET /api/sales-claims/export`

쿼리:

- `scope=my`
- `scope=company`

### 8.3 영업 시작

`POST /api/sales-claims/projects/{project_id}/claim`

요청:

```json
{
  "source_entry_id": "uuid",
  "source_run_id": "uuid",
  "project_name": "프로젝트명",
  "estimated_amount_text": "1.0~1.5억원"
}
```

규칙:

1. 잠금 기준은 `project_id`
2. 이미 active claim이 있으면 `409` 가능

### 8.4 영업현황 메모 수정

`PATCH /api/sales-claims/projects/{project_id}`

요청:

```json
{
  "sales_note": "오늘 1차 미팅",
  "force_admin_override": false
}
```

규칙:

1. 일반 사용자는 본인 claim 건만 수정
2. 관리자는 강제 override 가능

### 8.5 담당 이관

`POST /api/sales-claims/projects/{project_id}/transfer`

요청:

```json
{
  "target_user_id": "uuid",
  "target_email": "",
  "force": false
}
```

규칙:

1. owner 변경은 `release`보다 `transfer`를 기본으로 한다
2. 이관 이벤트를 남긴다

### 8.6 종료 처리

`POST /api/sales-claims/projects/{project_id}/close`

요청:

```json
{
  "outcome": "won",
  "contract_amount_text": "100,000,000",
  "force": false
}
```

규칙:

1. `outcome`은 `won` 또는 `lost`
2. `won`이면 `contract_amount_text` 필수
3. 종료 후 active target 목록에서는 빠진다

### 8.7 해제

`POST /api/sales-claims/projects/{project_id}/release`

요청:

```json
{
  "force": false
}
```

규칙:

1. 일반 사용자는 본인 claim만 해제 가능
2. 관리자는 강제 해제 가능

### 8.8 영업사원별 집계

`GET /api/sales-claims/summary-by-user`

용도:

1. 관리자 화면의 영업사원별 진행 현황
2. 프로젝트 수, 총 추정금액, 진행일 계산

## 9. API와 문서 체계의 관계

이 문서는 구현 엔드포인트와 대표 payload를 요약한 reference다.

우선순위는 아래와 같다.

1. 용어/상태/엔터티 해석: [04_TECHNICAL_SPEC_KR.md](../../spec/TECHNICAL_SPEC_KR.md)
2. 운영 판단: [05_OPERATION_POLICY_SPEC_KR.md](../../spec/OPERATIONS_POLICY_KR.md)
3. 기능 목적: [02_FUNCTIONAL_SPEC_KR.md](../../spec/FUNCTIONAL_SPEC_KR.md)

즉 API 형식 예시와 상세 payload는 본 문서를 보되, 충돌 시 기술명세 본문을 우선한다.

