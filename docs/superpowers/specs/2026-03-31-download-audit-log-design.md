# Download Audit Log Design

## Goal

Track successful spreadsheet downloads for sales and tracker project lists so administrators can review who downloaded potentially sensitive data.

## Scope

Log successful downloads for these flows:

- `내가 진행중인 영업` Excel download
- `회사 전체 진행중인 영업` Excel download
- `전체 영업 대상 프로젝트` CSV/XLSX download

Expose the audit trail only in admin mode.

## Out of Scope

- Failed download attempts
- Cancelled browser downloads
- File content retention or DLP controls
- Blocking downloads

## Approach Options

### Option 1: Server file log

- Append successful downloads to a server-side log file

Pros:

- Fastest to add
- No database migration

Cons:

- Hard to filter in UI
- Weak queryability for admins
- Poor fit for multi-instance/server rotation

### Option 2: Supabase audit table

- Add a dedicated audit table and insert one row per successful server-side download

Pros:

- Best fit for admin UI filtering and audit review
- Queryable by organization/user/scope/time
- Cleanly isolated from existing business tables

Cons:

- Requires one migration
- Requires backend write/read paths

### Option 3: External analytics or SIEM

- Emit download events to an external logging system

Pros:

- Strong long-term observability

Cons:

- Overkill for the current requirement
- Adds infrastructure and operations burden

## Recommended Design

Use **Option 2**.

Add a dedicated download audit table in Supabase and write to it from the backend download endpoints only after the server has prepared a successful download response. This keeps the signal focused on actual file deliveries rather than button clicks.

## Data Model

New table: `download_audit_logs`

Fields:

- `id` UUID primary key
- `organization_id` UUID not null
- `user_id` UUID nullable
- `user_email` text not null
- `user_role` text not null
- `download_scope` text not null
  - `my`
  - `company`
  - `global`
- `download_format` text not null
  - `xlsx`
  - `csv`
- `source_page` text not null
  - `my_active_sales`
  - `company_active_sales`
  - `tracker_entries`
- `file_name` text not null
- `created_at` timestamptz not null default now()

Indexes:

- `(organization_id, created_at desc)`
- `(organization_id, source_page, created_at desc)`

## Backend Changes

Add audit inserts to the successful spreadsheet download endpoints in `backend/api/app.py`.

Logging rule:

- Only log after request validation succeeds and a successful file response is being returned
- Do not log validation errors or failed requests

Read API:

- Add an admin-only endpoint to fetch recent download audit records for the current organization
- Default sort: newest first
- Initial limit can be fixed or small and simple

## Frontend Changes

Add an admin-mode-only panel for recent download history.

Initial display fields:

- Download time
- User name or email
- Scope
- Format
- Source page
- File name

The panel must not be visible in user mode.

## Security and Operational Notes

- This is an audit trail, not a prevention mechanism
- Browser-level cancellation after response start is out of scope
- Because this adds a new append-only auxiliary table, risk to existing operational data is low

## Testing

Backend:

- Successful `my/company/global` download requests create one audit row each
- Unauthorized or invalid requests do not create rows
- Admin-only read endpoint rejects non-admin users

Frontend:

- Admin mode shows the panel
- User mode hides the panel
- Download audit rows render expected labels

## Rollout

1. Implement on a feature branch
2. Verify in preview/staging
3. Apply the single Supabase migration
4. Merge to `main` and deploy
