# DB Schema Draft

- 문서 역할: DB 계약 reference
- 정본 여부: `reference`
- 이 문서가 답하는 질문: 현재 데이터 모델과 테이블 구조는 어떻게 정의되는가
- 상위 기준 문서: [04_TECHNICAL_SPEC_KR.md](../../spec/TECHNICAL_SPEC_KR.md)
- 충돌 시 우선 문서: [04_TECHNICAL_SPEC_KR.md](../../spec/TECHNICAL_SPEC_KR.md)

## 1. 문서 목적

이 문서는 현재 구현과 Phase 2 방향을 함께 설명하는 `DB 계약 reference`다.

정본 기준은 [04_TECHNICAL_SPEC_KR.md](../../spec/TECHNICAL_SPEC_KR.md)이고, 이 문서는 다음을 구체화한다.

1. 실제 테이블 이름
2. 주요 컬럼과 제약
3. 도메인별 데이터 분리 방식
4. Phase 1 호환 구조와 Phase 2 목표 구조의 관계

## 2. 최상위 원칙

1. 인증 본체는 Supabase Auth의 `auth.users`가 가진다.
2. 앱 프로필은 `user_profiles`에 둔다.
3. 조직 소속과 조직 역할은 `organization_memberships`에 둔다.
4. 초대 lifecycle은 `invitations`에서 관리한다.
5. 감사 이력은 `audit_logs`와 도메인별 이벤트 테이블에서 관리한다.
6. `users.organization_id` 같은 단순 구조를 최종 권한 모델로 사용하지 않는다.

## 3. 표준 용어

- `organization`
- `user_profile`
- `membership`
- `account_status`
- `membership_status`
- `invitation`
- `project_sales_claim`
- `project_sales_claim_event`
- `entry_key`

## 4. 스키마 구성

### 4.1 Auth / Organization

1. `organizations`
2. `user_profiles`
3. `organization_memberships`
4. `invitations`
5. `audit_logs`

### 4.2 Pipeline / Tracker

1. `pipeline_runs`
2. `pipeline_logs`
3. `run_artifacts`
4. `saved_run_presets`
5. `tracker_entries`
6. `tracker_entry_audit_logs`
7. `tracker_change_events`
8. `backfill_conflicts`

### 4.3 Sales Pipeline

1. `project_sales_claims`
2. `project_sales_claim_events`

## 5. organizations

```sql
create table organizations (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text not null unique,
  created_at timestamptz not null default now()
);
```

용도:
- 회사 단위 테넌트
- 사용자, 실행, 트래커, 영업 데이터의 최상위 범위

## 6. user_profiles

`auth.users`와 1:1 대응하는 앱 프로필 테이블이다.

```sql
create table user_profiles (
  id uuid primary key,
  email text not null,
  display_name text not null default '',
  mobile_phone text not null default '',
  office_phone text not null default '',
  account_status text not null default 'active',
  global_role text not null default '',
  last_login_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint user_profiles_account_status_check
    check (account_status in ('active', 'inactive', 'deactivated')),
  constraint user_profiles_global_role_check
    check (global_role in ('', 'platform_admin'))
);
```

핵심 규칙:

1. `id`는 Supabase Auth 사용자 UUID와 동일하게 간다.
2. `global_role`은 조직 역할과 분리한다.
3. `account_status`는 로그인 가능 여부 기준이다.

권장 인덱스:

```sql
create unique index idx_user_profiles_email_lower
  on user_profiles (lower(email));
```

## 7. organization_memberships

조직 소속과 조직 역할의 본체다.

```sql
create table organization_memberships (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  user_profile_id uuid not null references user_profiles(id) on delete cascade,
  role text not null default 'org_member',
  membership_status text not null default 'active',
  team_name text not null default '',
  job_title text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint organization_memberships_role_check
    check (role in ('org_admin', 'org_member')),
  constraint organization_memberships_status_check
    check (membership_status in ('active', 'inactive', 'deactivated')),
  constraint organization_memberships_org_user_unique
    unique (organization_id, user_profile_id)
);
```

핵심 규칙:

1. 권한 판단은 `organization_memberships.role` 기준이다.
2. 한 사용자-한 조직 조합은 membership 1개만 가진다.
3. `membership_status`는 해당 회사 안에서의 활동 여부다.

## 8. invitations

초대 기반 가입을 위한 lifecycle 테이블이다.

```sql
create table invitations (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  email text not null,
  role text not null default 'org_member',
  display_name text not null default '',
  team_name text not null default '',
  job_title text not null default '',
  invite_token text not null unique,
  status text not null default 'pending',
  expires_at timestamptz not null,
  accepted_at timestamptz,
  revoked_at timestamptz,
  accepted_user_id uuid references user_profiles(id) on delete set null,
  created_by uuid references user_profiles(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint invitations_role_check
    check (role in ('org_admin', 'org_member')),
  constraint invitations_status_check
    check (status in ('pending', 'accepted', 'expired', 'revoked'))
);
```

권장 인덱스:

```sql
create unique index idx_invitations_org_email_pending
  on invitations (organization_id, lower(email))
  where status = 'pending';

create index idx_invitations_org_status_created_at
  on invitations (organization_id, status, created_at desc);
```

핵심 규칙:

1. 초대 이메일과 실제 로그인 이메일이 같아야 수락할 수 있다.
2. `pending` 초대는 조직 내 동일 이메일 기준 중복 생성하지 않는다.
3. `accept_invitation(...)` 함수는 idempotent하게 동작해야 한다.
4. `create_invitation(...)` 함수는 org row lock + plan 한도 재검증 뒤 insert를 수행해야 한다.

## 9. audit_logs

최소 운영 감사로그의 범용 저장소다.

```sql
create table audit_logs (
  id bigint generated always as identity primary key,
  organization_id uuid references organizations(id) on delete cascade,
  actor_user_id uuid references user_profiles(id) on delete set null,
  actor_membership_id uuid references organization_memberships(id) on delete set null,
  event_type text not null,
  target_type text not null default '',
  target_id text not null default '',
  payload_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
```

예상 event_type:

- `invite_created`
- `invite_revoked`
- `invite_accepted`
- `membership_role_changed`
- `membership_deactivated`
- `project_transferred`

## 10. legacy users 호환 메모

현재 구현에는 과거 로컬 사용자 테이블 `users`가 남아 있을 수 있다.

이 테이블은 다음 목적의 `호환 계층`으로만 본다.

1. Phase 1 데이터 마이그레이션
2. 구형 run / sales claim 참조 유지
3. 내부 migration bridge

정책:

1. 최종 권한 모델은 `users`가 아니라 `user_profiles + organization_memberships`다.
2. 새 Phase 2 문서는 `users.role`, `users.organization_id`를 정본 권한 모델로 해석하지 않는다.
3. 필요한 경우 `users -> user_profiles / organization_memberships` 브리지 migration을 문서화한다.

## 11. pipeline_runs

```sql
create table pipeline_runs (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  requested_by uuid not null,
  parent_run_id uuid references pipeline_runs(id) on delete set null,
  status text not null default 'queued',
  run_type text not null,
  source_mode text not null default 'web_native',
  started_at timestamptz,
  finished_at timestamptz,
  params_json jsonb not null default '{}'::jsonb,
  summary_json jsonb not null default '{}'::jsonb,
  error_json jsonb not null default '{}'::jsonb,
  progress_stage text not null default '',
  progress_current integer not null default 0,
  progress_total integer not null default 0,
  cancel_requested boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
```

핵심 규칙:

1. `run_type`은 현재 `project_tracker | tracker_export`
2. `tracker_export`는 child run이고 `parent_run_id`를 가진다.
3. `summary_json`, `error_json`은 실행별 결과 스냅샷이다.

## 12. pipeline_logs

```sql
create table pipeline_logs (
  id bigint generated always as identity primary key,
  run_id uuid not null references pipeline_runs(id) on delete cascade,
  organization_id uuid not null references organizations(id) on delete cascade,
  level text not null default 'info',
  stage text not null default '',
  message text not null,
  meta_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
```

## 13. run_artifacts

```sql
create table run_artifacts (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references pipeline_runs(id) on delete cascade,
  organization_id uuid not null references organizations(id) on delete cascade,
  artifact_type text not null,
  storage_path text not null,
  file_name text not null,
  mime_type text not null default 'application/octet-stream',
  size_bytes bigint not null default 0,
  checksum text not null default '',
  meta_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
```

예:

- `winner_csv`
- `summary_json`
- `tracking_excel`
- `error_log`

## 14. saved_run_presets

```sql
create table saved_run_presets (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  created_by uuid not null,
  name text not null,
  params_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
```

## 15. tracker_entries

트래커 웹 화면에서 직접 보여주는 현재값 테이블이다.

핵심 모델:

- `*_source`: 파이프라인/트래커 export가 마지막으로 생성한 원본 값
- `*_override`: 사용자가 웹에서 수정한 값
- 화면 표시값: `coalesce(*_override, *_source)`

대표 스키마:

```sql
create table tracker_entries (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  source_run_id uuid not null references pipeline_runs(id) on delete restrict,
  source_tracker_run_id uuid references pipeline_runs(id) on delete set null,
  project_id uuid,
  entry_key text not null,
  sheet_name text not null default 'Sheet1',
  section_name text not null default '일반관급',
  row_no integer not null default 0,
  source_bid_no text not null default '',
  source_bid_ord text not null default '',
  source_project_name_norm text not null default '',
  project_name_source text not null default '',
  project_name_override text,
  gross_area_scale_source text not null default '',
  gross_area_scale_override text,
  construction_cost_source text not null default '',
  construction_cost_override text,
  demand_org_name_source text not null default '',
  demand_org_name_override text,
  demand_contact_source text not null default '',
  demand_contact_override text,
  client_location_source text not null default '',
  client_location_override text,
  site_location_1_source text not null default '',
  site_location_1_override text,
  site_location_2_source text not null default '',
  site_location_2_override text,
  architect_office_source text not null default '',
  architect_office_override text,
  construction_start_date_source text not null default '',
  construction_start_date_override text,
  last_checked_date_source text not null default '',
  last_checked_date_override text,
  progress_note_source text not null default '',
  progress_note_override text,
  notice_date_source text not null default '',
  notice_date_override text,
  manager_name_source text not null default '',
  manager_name_override text,
  building_automation_estimated_amount_source text not null default '',
  building_automation_estimated_amount_override text,
  last_edited_at timestamptz,
  last_edited_by uuid,
  last_edited_by_label text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (organization_id, entry_key)
);
```

핵심 규칙:

1. `entry_key`는 stable matching key다.
2. `project_id`는 영업 claim 잠금 기준으로 사용한다.
3. `source_tracker_run_id`는 마지막 export child run을 추적한다.

## 16. tracker_entry_audit_logs

```sql
create table tracker_entry_audit_logs (
  id bigint generated always as identity primary key,
  tracker_entry_id uuid not null references tracker_entries(id) on delete cascade,
  organization_id uuid not null references organizations(id) on delete cascade,
  actor_user_id uuid,
  actor_label text not null default '',
  field_name text not null,
  before_value text,
  after_value text,
  change_source text not null default 'web_console',
  created_at timestamptz not null default now()
);
```

핵심 규칙:

1. 트래커 편집은 필드 단위로 감사 로그를 남긴다.
2. `actor_user_id`가 없어도 `actor_label`은 남길 수 있다.

## 16.1 tracker_change_events

```sql
create table tracker_change_events (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  tracker_entry_id uuid not null references tracker_entries(id) on delete cascade,
  event_type text not null,
  field_name text not null default '',
  old_value text not null default '',
  new_value text not null default '',
  old_value_norm text,
  new_value_norm text,
  source_run_id uuid references pipeline_runs(id) on delete set null,
  source_kind text not null default '',
  source_ref text not null default '',
  extractor_version text not null default '',
  reason_code text not null default '',
  batch_key text not null default '',
  dedupe_key text not null default '',
  is_silent boolean not null default false,
  is_read boolean not null default false,
  read_at timestamptz,
  created_at timestamptz not null default now()
);
```

핵심 규칙:

1. organization 범위 최근 변경 알림과 entry 상세 변경 이력을 같이 담는다.
2. `dedupe_key`가 같으면 중복 append 대신 기존 이벤트로 수렴할 수 있다.
3. `is_silent=true`는 상세 조회에는 남기되 기본 알림 목록에서는 숨길 수 있다.

## 16.2 backfill_conflicts

```sql
create table backfill_conflicts (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  tracker_entry_id uuid not null references tracker_entries(id) on delete cascade,
  field_name text not null,
  current_value text not null default '',
  candidate_value text not null default '',
  current_value_norm text,
  candidate_value_norm text,
  reason_code text not null,
  source_kind text not null,
  source_ref text,
  source_run_id uuid references pipeline_runs(id) on delete set null,
  extractor_version text,
  detected_at timestamptz not null default now(),
  resolved_at timestamptz,
  resolution text,
  conflict_key text not null
);
```

핵심 규칙:

1. safe backfill이 자동 반영하지 못한 충돌 후보를 organization 범위로 저장한다.
2. 기본 운영 inbox는 `resolved_at is null`인 열린 항목만 본다.
3. `resolution`은 `kept_current`, `applied_manually`, `applied_via_backfill`, `dismissed` 중 하나다.
4. `conflict_key`는 동일 충돌의 upsert 기준이다.

## 17. project_sales_claims

영업 현재 상태 테이블이다. 잠금 기준은 `project_id`다.

```sql
create table project_sales_claims (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  project_id uuid not null,
  source_entry_id uuid references tracker_entries(id) on delete set null,
  source_run_id uuid references pipeline_runs(id) on delete set null,
  project_name text not null default '',
  owner_user_id uuid not null,
  owner_email text not null default '',
  owner_display_name text not null default '',
  claimed_at timestamptz not null default now(),
  current_owner_assigned_at timestamptz not null default now(),
  released_at timestamptz,
  is_active boolean not null default true,
  claim_status text not null default 'active',
  closed_at timestamptz,
  closed_by uuid,
  sales_note text not null default '',
  sales_note_updated_at timestamptz,
  sales_note_updated_by uuid,
  estimated_amount_text text not null default '',
  estimated_amount_low_krw bigint,
  estimated_amount_high_krw bigint,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint project_sales_claims_status_check
    check (claim_status in ('active', 'won', 'lost'))
);
```

핵심 규칙:

1. 활성 잠금은 조직 내 `project_id` 기준 1개만 가진다.
2. `claimed_at`은 프로젝트 최초 영업 시작일이다.
3. `current_owner_assigned_at`은 현재 담당 시작일이다.
4. `claim_status`
   - `active`
   - `won`
   - `lost`

권장 인덱스:

```sql
create unique index ux_project_sales_claims_active_project
  on project_sales_claims (organization_id, project_id)
  where is_active = true;
```

## 18. project_sales_claim_events

영업 이력 이벤트 테이블이다.

```sql
create table project_sales_claim_events (
  id bigint generated always as identity primary key,
  organization_id uuid not null references organizations(id) on delete cascade,
  claim_id uuid not null references project_sales_claims(id) on delete cascade,
  project_id uuid not null,
  actor_user_id uuid,
  actor_email text not null default '',
  actor_display_name text not null default '',
  event_type text not null,
  old_value_json jsonb not null default '{}'::jsonb,
  new_value_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint project_sales_claim_events_type_check
    check (event_type in (
      'claim',
      'release',
      'force_release',
      'note_update',
      'transfer',
      'close_won',
      'close_lost'
    ))
);
```

핵심 규칙:

1. 현재 상태는 `project_sales_claims`에서 읽는다.
2. 이력은 `project_sales_claim_events`에서 읽는다.
3. owner 변경은 `transfer` 이벤트를 남긴다.

## 19. projects 선택 모델

Phase 2 이후 필요 시 `projects`를 별도 테이블로 분리할 수 있다.

현재 기준:

1. 영업 claim과 트래커는 `project_id`를 공유 식별자로 사용한다.
2. 별도 `projects` 테이블은 필수는 아니다.
3. 다만 장기적으로 회사별 프로젝트 대시보드가 커지면 독립 테이블을 고려할 수 있다.

## 20. 정리

현재 DB 계약을 한 줄로 정리하면 이렇다.

1. Auth는 `auth.users`
2. 앱 프로필은 `user_profiles`
3. 조직 권한은 `organization_memberships`
4. 초대는 `invitations`
5. 감사는 `audit_logs`
6. 실행/로그/아티팩트는 `pipeline_*`
7. 트래커 현재값은 `tracker_entries`
8. 영업 현재값은 `project_sales_claims`
9. 영업 이력은 `project_sales_claim_events`

상세 기술 기준 충돌 시 [04_TECHNICAL_SPEC_KR.md](../../spec/TECHNICAL_SPEC_KR.md)를 우선한다.

