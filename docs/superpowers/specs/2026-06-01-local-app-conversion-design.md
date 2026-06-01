# Local App Conversion Design

Date: 2026-06-01

## 1. Goal

Convert `notice-winner-pipeline-web` from a hosted Vercel/EC2/Supabase web app into a local Windows-run application.

The local app must preserve the current product behavior where it matters, but remove hosted web deployment and login requirements. It will still use the internet for public lookup sources such as G2B, 건축HUB, 세움터/EAIS, LOFIN, and education-office related sources.

## 2. Non-Negotiable Requirements

1. Supabase data must be backed up before any app-level migration.
2. EC2 data and generated files must be backed up before any app-level migration.
3. Data needed by the app must be copied into local storage and loaded from local storage.
4. Login must be removed from the local app.
5. Login-related data must not be discarded. It must be backed up and, where useful, kept as read-only audit/history data.
6. Google Search and Google Sheets features must be removed or kept disabled only as a temporary safety measure during migration.
7. Public lookup integrations must remain available:
   - 나라장터/G2B
   - 건축HUB
   - 세움터/EAIS
   - LOFIN/지방재정365
   - education-office related lookup paths
8. "External connection removal" means removing hosted cloud app dependencies, not blocking internet access entirely.

## 3. Current State

The current repository is already close to a local web app shape:

- Frontend assets live in `frontend/`.
- Backend is FastAPI under `backend/api/app.py`.
- Local launch scripts already exist:
  - `scripts/start_local_api.ps1`
  - `scripts/start_local_console.ps1`
- Vercel currently rewrites `/api/:path*` to the EC2 API at `http://15.164.149.28:8000/api/:path*`.
- Repository storage currently supports `in_memory`, `supabase`, `postgres`, and `postgrest`.
- If Supabase env vars are absent, repositories default to `in_memory`, which is not acceptable for the final local app because data must persist.
- Auth middleware already has a switch: when `auth_is_enabled()` is false, API auth enforcement is skipped.

Supabase is not only login. It also contains domain data, run metadata, audit logs, tracker data, sales claim data, related notice caches, and artifacts metadata. Treating it as "login only" would risk data loss.

## 4. Recommended Architecture

Use the existing frontend and FastAPI backend, but replace hosted persistence with local persistence.

```text
notice-winner-local/
  app/
  backend/
  frontend/
  data/
    local.sqlite
    manifest.json
  storage/
    artifacts/
    downloads/
    uploads/
    run-workspaces/
  exports/
  logs/
  backups/
    supabase/
    ec2/
  scripts/
    start-local.ps1
    backup-supabase.ps1
    backup-ec2.ps1
    migrate-to-sqlite.ps1
```

The first implementation can remain browser-based:

```text
http://127.0.0.1:8000/app/
```

A packaged `.exe` can be a later step if needed. The first priority is data correctness and reliable local execution.

## 5. Persistence Design

Add a new repository backend:

```text
TRACKER_REPOSITORY_BACKEND=sqlite
RUN_REPOSITORY_BACKEND=sqlite
ARTIFACT_REPOSITORY_BACKEND=sqlite
RUN_LOG_REPOSITORY_BACKEND=sqlite
RELATED_NOTICE_CACHE_REPOSITORY_BACKEND=sqlite
RELATED_NOTICE_PUBLICATION_REPOSITORY_BACKEND=sqlite
SALES_CLAIM_REPOSITORY_BACKEND=sqlite
DOWNLOAD_AUDIT_LOG_REPOSITORY_BACKEND=sqlite
LOGIN_AUDIT_LOG_REPOSITORY_BACKEND=sqlite
```

Local SQLite should become the default for the local app distribution. `in_memory` can remain only for tests and development fixtures.

SQLite tables should preserve Supabase IDs and timestamps where possible. JSONB columns should become JSON text columns with explicit serialization/deserialization in repository code. UUID values can remain text. `timestamptz` values should be stored as ISO 8601 text in UTC, while UI display can continue using KST where the app already does that.

## 6. Supabase Data Backup And Migration Scope

Before changing app behavior, create a full Supabase export under:

```text
backups/supabase/YYYYMMDD_HHMMSS/
```

The backup should include:

- schema SQL
- per-table CSV or JSONL export
- row counts
- checksum or file size manifest
- export timestamp
- source project URL
- migration script version

The app-level local import must include at least these tables or views, if present:

### Auth And Organization Data

- `organizations`
- `users`
- `user_profiles`
- `organization_memberships`
- `invitations`
- `audit_logs`
- Supabase Auth `auth.users`, if accessible through admin/service-role export

These are no longer used for login enforcement in the local app. They are preserved as backup and audit/history data.

### Audit Data

- `login_audit_logs`
- `download_audit_logs`
- `tracker_entry_audit_logs`

`login_audit_logs` must remain queryable as historical data even after login is removed.

### Pipeline And Artifact Metadata

- `pipeline_runs`
- `pipeline_logs`
- `run_artifacts`
- `saved_run_presets`

Artifact metadata must be reconciled with EC2/local files. A row in `run_artifacts` is not enough unless the referenced file is also backed up.

### Tracker Data

- `tracker_entries`
- `tracker_entries_effective` logic
- `tracker_change_events`
- `tracker_entry_snapshots`
- `home_bootstrap_snapshots`
- `backfill_conflicts`

For SQLite, `tracker_entries_effective` can be recreated as a SQLite view or computed in repository/service code. The preferred first version is a SQLite view if it keeps queries simple.

### Sales And Related Notice Data

- `project_sales_claims`
- `project_sales_claim_events`
- `project_related_notice_cache`
- `related_notice_publications`

These are domain data, not login data, and must be migrated into the local app.

## 7. EC2 Data Backup And Migration Scope

Before removing EC2 dependency, create a full EC2 backup under:

```text
backups/ec2/YYYYMMDD_HHMMSS/
```

The backup should include every app-owned directory that can contain generated or uploaded data:

- pipeline run workspaces
- input files
- output files
- exported Excel/CSV files
- downloaded files
- generated reports
- artifact files referenced by `run_artifacts.storage_path`
- application logs
- scheduler or process logs, if present
- deployment metadata needed to understand the running version

The backup should also capture configuration names without writing secrets into git:

- env var names
- service ports
- working directories
- process manager unit names, if any
- cron/task scheduler entries, if any

Secrets should go into a local private backup file outside version control or into a user-managed password store. They must not be committed.

## 8. Login Removal Design

The local app should not show or require login.

Backend:

- Set auth disabled by default for local mode.
- Remove mandatory session checks from local execution paths.
- Replace required actor identity with a fixed local actor:
  - `local_admin`
  - label: `Local Admin`
- Preserve audit compatibility by writing actor labels where historical code expects an actor.

Frontend:

- Remove login, sign-up, invitation, password reset, organization admin account management, and session import UI from the local app entry path.
- If account/admin pages still exist for historical inspection, keep them hidden or read-only until explicitly needed.

Data:

- Do not delete login history.
- `login_audit_logs` remains a read-only historical table.
- Existing user/profile/org records remain in backup and may be imported for display labels, ownership, and audit context.

## 9. Google Feature Removal

Remove or hard-disable:

- Google Sheets admin bootstrap/sync APIs
- Google Sheets frontend tabs and runtime modules
- Google Sheets env requirements
- Google Search fallback path in filtering/search logic
- DuckDuckGo fallback path if it only exists as a Google fallback substitute

Because this code may be connected to older fallback behavior, removal should be staged:

1. First implementation: block the runtime path and add tests proving public source lookups still work without Google/DuckDuckGo.
2. After verification: delete unused Google Sheets UI/API modules and old search fallback code.

This avoids breaking G2B direct URL processing and public source lookups during the local migration.

## 10. Public Lookup Integrations To Keep

Keep and verify these source integrations:

- G2B contract and notice APIs
- 건축HUB design competition list/winner pages
- 세움터/EAIS architecture office and permit-related pages
- LOFIN/지방재정365 planned order or finance-related pages
- education-office related lookup paths used by the current pipeline

The local app can still use internet access for these public sources. The app should not depend on Vercel, EC2, Supabase, Google Sheets, or hosted login.

## 11. Migration Flow

### Phase 1: Inventory

1. List Supabase tables and views.
2. Record row counts for every table.
3. Export table samples for shape verification.
4. List EC2 app directories and candidate data directories.
5. Match `run_artifacts.storage_path` rows to actual files.
6. Produce a migration inventory report.

### Phase 2: Full Backup

1. Export Supabase schema and data.
2. Download EC2 app-owned files.
3. Generate backup manifests.
4. Verify row counts and file counts.
5. Do not change production app behavior in this phase.

### Phase 3: Local Schema

1. Create SQLite schema.
2. Recreate required indexes and views.
3. Implement SQLite repository classes behind existing repository interfaces.
4. Add local file storage adapter for artifacts/downloads/uploads.

### Phase 4: Import

1. Import Supabase rows into SQLite.
2. Copy EC2 files into local `storage/`.
3. Rewrite artifact paths to local relative paths where needed.
4. Preserve original cloud paths in metadata for traceability.
5. Generate import verification report.

### Phase 5: Local App Runtime

1. Default repositories to SQLite in local mode.
2. Start FastAPI locally.
3. Serve frontend locally.
4. Disable auth by default.
5. Remove Vercel rewrite dependency.
6. Verify tracker, runs, downloads, audit history, sales views, and related notices load from local data.

### Phase 6: Cloud Feature Removal

1. Remove/hide login UI and auth routes from the local app.
2. Remove Google Sheets UI and APIs.
3. Remove or permanently disable Google/DuckDuckGo search fallback.
4. Keep public source lookup tests passing.

## 12. Verification Requirements

The migration is not complete until these checks pass:

1. Supabase exported row count equals local imported row count for every migrated table.
2. Every `run_artifacts` row either has a local file or is explicitly listed as missing in the migration report.
3. Tracker entries load from SQLite after restarting the app.
4. Download history loads from SQLite after restarting the app.
5. Login history loads as read-only historical data after restarting the app.
6. New local pipeline runs write to SQLite and local storage.
7. No API call is made to Supabase during normal local app use.
8. No API call is made to EC2 during normal local app use.
9. No Google Sheets endpoint is required.
10. Google/DuckDuckGo search fallback is not invoked.
11. G2B, 건축HUB, 세움터/EAIS, LOFIN, and education-office source lookups still work.

## 13. Risks And Mitigations

### Risk: Supabase data is broader than login data

Mitigation: perform full table inventory and full backup before code removal. Treat auth data as historical, but migrate domain data into SQLite.

### Risk: Artifact metadata exists without files

Mitigation: reconcile `run_artifacts.storage_path` with EC2 files during backup. Missing files must be listed in a report instead of silently ignored.

### Risk: Google fallback removal changes result quality

Mitigation: first disable the runtime path, then compare a representative run using G2B direct URLs and public source lookups. Delete code only after confirming no required data source depends on it.

### Risk: SQLite does not behave exactly like Postgres

Mitigation: keep repository interfaces stable, add focused tests for JSON serialization, timestamp ordering, upsert behavior, audit log writes, and effective tracker views.

### Risk: Login removal breaks audit writes

Mitigation: use a fixed local actor label for new local changes and preserve imported historical users/profiles for old records.

## 14. Open Items To Resolve During Implementation Planning

1. EC2 SSH/access method and exact data directory locations.
2. Whether Supabase Auth `auth.users` can be exported with available credentials.
3. Whether local app should support multi-organization filtering or collapse everything into one default local organization.
4. Whether the first delivery should be script-based local execution or packaged as a Windows executable.
5. Exact education-office lookup modules and endpoints currently used by the pipeline.

## 15. Recommended First Implementation Plan

Start with data safety, not UI removal.

1. Build inventory and backup scripts.
2. Produce Supabase and EC2 backup reports.
3. Add SQLite schema and repositories.
4. Import data locally and verify counts.
5. Run the current app locally on SQLite.
6. Remove login from local runtime.
7. Disable Google Search/DuckDuckGo fallback and Google Sheets.
8. Remove unused cloud deployment paths after verification.

This order protects the existing data first, then changes runtime behavior.
