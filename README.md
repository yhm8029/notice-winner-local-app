# Project Tracker Web

Web repo for the project tracker rebuild.

## Scope

- `backend/`: FastAPI API scaffold and repository layer
- `supabase/`: Postgres schema migrations and seed data
- `docs/`: canonical/reference/archive documentation hierarchy
- `frontend/`: placeholder for the future UI

## Tracker Repository Backend

The tracker APIs support local SQLite, in-memory, and Supabase/Postgres repository backends.

- `TRACKER_REPOSITORY_BACKEND=in_memory`
  - forces the local in-memory repository
  - uses seeded sample rows for local API scaffolding
- `TRACKER_REPOSITORY_BACKEND=sqlite`
  - reads and writes `tracker_entries` and `tracker_entry_audit_logs` in a local SQLite `local_rows` database
- `TRACKER_REPOSITORY_BACKEND=supabase`
  - reads `tracker_entries_effective`
  - applies edits through `apply_tracker_entry_override(...)`
  - reads `tracker_entry_audit_logs`
- `TRACKER_REPOSITORY_BACKEND=auto`
  - optional explicit auto mode

Default selection:

- if `SUPABASE_URL` plus a backend API key are present, the app auto-selects `supabase`
- otherwise it falls back to `in_memory`

Required env for `supabase`:

- `SUPABASE_URL`
- `SUPABASE_SECRET_KEY`
- fallback: `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_SECRET`, or `SUPABASE_ANON_KEY`
- optional: `SUPABASE_HTTP_TIMEOUT_SECONDS`

The repo also auto-loads a local `.env` file at the project root.

## Run Repository Backend

The run APIs use the same backend split.

- `RUN_REPOSITORY_BACKEND=in_memory`
  - forces the local in-memory run store
- `RUN_REPOSITORY_BACKEND=sqlite`
  - persists `pipeline_runs` in a local SQLite `local_rows` database
- `RUN_REPOSITORY_BACKEND=supabase`
  - persists `pipeline_runs` in Supabase/Postgres
- `RUN_REPOSITORY_BACKEND=auto`
  - optional explicit auto mode

Default selection:

- if unset or `auto`, it inherits `TRACKER_REPOSITORY_BACKEND`
- if neither is set, it auto-selects `supabase` when Supabase env is present, otherwise `in_memory`

Artifact and log repositories follow the same pattern.

SQLite runtime adapters are available for:

- `TRACKER_REPOSITORY_BACKEND=sqlite`
- `RUN_REPOSITORY_BACKEND=sqlite`
- `ARTIFACT_REPOSITORY_BACKEND=sqlite`
- `RUN_LOG_REPOSITORY_BACKEND=sqlite`
- `RELATED_NOTICE_CACHE_REPOSITORY_BACKEND=sqlite`
- `RELATED_NOTICE_PUBLICATION_REPOSITORY_BACKEND=sqlite`
- `SALES_CLAIM_REPOSITORY_BACKEND=sqlite`
- `TRACKER_CHANGE_EVENT_REPOSITORY_BACKEND=sqlite`
- `DOWNLOAD_AUDIT_LOG_REPOSITORY_BACKEND=sqlite`
- `LOGIN_AUDIT_LOG_REPOSITORY_BACKEND=sqlite`
- `TRACKER_ENTRY_SNAPSHOT_REPOSITORY_BACKEND=sqlite`
- `HOME_BOOTSTRAP_SNAPSHOT_REPOSITORY_BACKEND=sqlite`
- `BACKFILL_CONFLICT_REPOSITORY_BACKEND=sqlite`

Set `LOCAL_SQLITE_PATH` to the SQLite file created from the Supabase export. If it is omitted, the app uses `data/local.sqlite3`. The SQLite adapters preserve Supabase-exported JSON rows and keep subsequent local edits in the same database.

## Artifact Files

- `project_tracker` success creates a local `winner_csv` artifact plus a `run_artifacts` row
- `tracker_export` success creates a local `tracking_excel` artifact plus a `run_artifacts` row
- default artifact root: `output/artifacts/`
- default tracker template: `assets/project_tracker_template.xlsx`
- override env:
  - `ARTIFACTS_ROOT`
  - `TRACKER_TEMPLATE_PATH`

Console behavior:

- the artifact panel groups selected runs, parent `project_tracker`, and child `tracker_export` runs separately
- CSV artifacts and `tracking_excel` support an in-console preview
- `tracking_excel` preview is served through `/api/artifacts/{artifact_id}/preview`

## Collect Stage Backend

- `project_tracker` collect/filter/rescan/export stages run inside this repository by default
- mode selection:
  - `PROJECT_TRACKER_COLLECT_MODE=auto`
    - default
    - tries native API/web stages first
    - if native fails, the run fails unless synthetic debug mode is explicitly enabled
  - `PROJECT_TRACKER_COLLECT_MODE=native`
    - requires a working G2B service key in local env
    - fails the run if native collect cannot execute
  - `PROJECT_TRACKER_COLLECT_MODE=synthetic`
    - debug-only mode
    - requires `PROJECT_TRACKER_ENABLE_SYNTHETIC_DEBUG=1`
    - skips external collection and uses local synthetic collect/filter/rescan/export outputs
- optional env:
  - `RUN_WORKSPACE_ROOT`
  - `PROJECT_TRACKER_ENABLE_SYNTHETIC_DEBUG=1`
    - exposes synthetic mode in the UI
    - allows synthetic fallback and legacy synthetic runs to appear in operational views
- per-request override:
  - `advanced_options.collect_mode`

## Local Run

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m ensurepip --upgrade
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.api.app:app --host 127.0.0.1 --port 8000
```

- open `http://127.0.0.1:8000/app/` for the built-in frontend console

## Desktop WebView App

The local app can also run as a Windows desktop window through `pywebview`.

```powershell
python -m pip install -r backend\requirements.txt -r requirements-desktop.txt
python -m desktop.launcher
```

Build a folder-style Windows executable:

```powershell
.\scripts\build_desktop_exe.ps1 -InstallDependencies -IncludeLocalData
```

For a usable local distribution, pass the real SQLite DB and local `.env` explicitly:

```powershell
.\scripts\build_desktop_exe.ps1 -InstallDependencies -IncludeLocalData -LocalSqlitePath "C:\Users\user\notice-winner-local-app\data\local.sqlite3" -EnvPath "C:\path\to\.env"
```

See `docs/DESKTOP_WEBVIEW_APP_KR.md` for runtime paths and distribution notes.

## Local Conversion Backup Inventory

Before converting the hosted app to local SQLite/storage, create a cloud data inventory.

Create `.env.local-backup` locally. Do not commit it.

```text
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...
EC2_SSH_TARGET=ubuntu@your-ec2-host
EC2_SSH_KEY_PATH=C:\Users\user\.ssh\main-key.pem
EC2_BACKUP_PATHS=/home/ubuntu/notice-winner-pipeline-web/output,/home/ubuntu/notice-winner-pipeline-web/input,/home/ubuntu/notice-winner-pipeline-web/logs
```

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/local_backup_inventory.ps1
```

Add `-DownloadEc2Files` to archive and extract the EC2 paths under the EC2 backup directory.

Outputs are written under `backups/supabase/<timestamp>/` and `backups/ec2/<timestamp>/`. The Supabase manifest contains table row counts and checksums. The EC2 manifest contains app-owned file paths, sizes, and modified timestamps. `artifact_reconciliation.json` reports whether `run_artifacts.storage_path` rows have matching EC2 files.

To create a local SQLite staging database from exported Supabase table JSONL files:

```powershell
.\.venv\Scripts\python.exe scripts\create_local_sqlite_db.py `
  --tables-dir backups\supabase\<timestamp>\tables `
  --output data\local.sqlite3
```

This staging database preserves each Supabase row as JSON in `local_rows`. The command validates `manifest.json` when present. Add `--allow-partial` only when intentionally importing a backup with known failed or missing table exports, and add `--replace` only when intentionally overwriting an existing local SQLite file.

## HTTP Smoke Test

```powershell
.\.venv\Scripts\python.exe scripts\http_smoke_test.py
```

- starts a local uvicorn server
- calls `POST /api/runs`
- polls `GET /api/runs/{id}` until the parent `project_tracker` run completes
- calls `GET /api/runs/{id}/logs`
- calls `POST /api/runs/{id}/tracker-export`
- polls `GET /api/runs/{tracker_run_id}` until the child run completes
- calls `GET /api/runs/{tracker_run_id}/logs`
- calls `GET /api/runs/{id}/artifacts`
- downloads `winner_csv` and `tracking_excel`
- calls `GET /api/tracker-entries`
- calls `PATCH /api/tracker-entries/{id}`
- calls `GET /api/tracker-entries/{id}/audit-logs`
- calls `POST /api/runs/{id}/cancel` on a delayed run and verifies `cancelled`
- deletes temporary test rows

## Native Live Check

Run a real G2B notice check from the terminal:

```powershell
.\.venv\Scripts\python.exe scripts\native_live_check.py `
  --bid-no R25BK00554120 `
  --bid-no R25BK00570104 `
  --start-date 20250101 `
  --end-date 20250131 `
  --api-scope all `
  --output output\native-live-check.json
```

- starts a temporary local API server
- runs `project_tracker` in `native` mode for each bid number
- runs `tracker_export` when the winner run succeeds
- prints the winner summary plus tracker 핵심 필드 to stdout
- writes an optional JSON report with the same data

## Phase 1 Equivalence Runner

```powershell
.\.venv\Scripts\python.exe scripts\phase1_equivalence_runner.py --output output\phase1-equivalence-report.json
```

- runs the documented Phase 1 scenarios as a single report
- pass `--gui-source-root "C:\path\to\gui-repo"` to probe the real GUI parity path
- without a GUI repo, the quota/fallback parity case is reported as `skipped`

## Phase 1 Artifact Diff Runner

```powershell
.\.venv\Scripts\python.exe scripts\phase1_artifact_diff_runner.py `
  --gui-source-root "C:\path\to\gui-repo" `
  --notice-title "설계공모" `
  --demand-org "부산" `
  --seed-limit 3 `
  --output output\phase1-artifact-diff-report.json
```

- fetches or reuses a seed CSV and runs both the direct GUI modules and the web stage pipeline from the same seed input
- compares `candidate_csv`, `internal_nav_csv`, `winner_csv`, `tracking_excel`, and progress log messages
- use `--seed-limit` for faster spot checks before running a full-seed comparison
- pass `--seed-csv C:\path\to\project_tracker_seed_input.csv` to skip live seed collection and diff downstream outputs only

## Local Run Scripts

Open the local console in one command:

```powershell
.\scripts\start_local_console.ps1
```

Start only the API server:

```powershell
.\scripts\start_local_api.ps1 -Port 8000 -SQLitePath data\local.sqlite3
```

Run both parity reports with the GUI comparison repo path set explicitly:

```powershell
.\scripts\run_phase1_reports.ps1 -GuiSourceRoot "C:\path\to\gui-repo" -SeedLimit 3
```

- `start_local_api.ps1 -SQLitePath ...` disables hosted login, clears Supabase runtime env vars, and switches all supported repositories to SQLite
- `start_local_console.ps1` starts the API server and opens `http://127.0.0.1:8000/app/`
- `run_phase1_reports.ps1` runs `phase1_equivalence_runner.py` and `phase1_artifact_diff_runner.py` sequentially
- parity reports require an explicit `-GuiSourceRoot` or `GUI_PARITY_SOURCE_ROOT`
- `/app/` exposes recent parity job history, selected job detail, and an optional `검증 실행` button for GUI comparison reports

## API Contract Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

- runs the Phase 1 API contract tests for success, validation failure, cancellation, tracker export success, and tracker export failure isolation

## CI

- GitHub Actions runs the same API contract suite on every `main` push and pull request via [.github/workflows/api-contract-tests.yml](C:/Users/pc/Desktop/git/notice-winner-pipeline-web/.github/workflows/api-contract-tests.yml)
- manual parity runs are available via [.github/workflows/manual-phase1-parity.yml](C:/Users/pc/Desktop/git/notice-winner-pipeline-web/.github/workflows/manual-phase1-parity.yml)
- the manual parity workflow is intended for a Windows `self-hosted` runner that already has access to the local GUI repo path
- workflow artifacts upload `phase1-equivalence-report.json` and `phase1-artifact-diff-report.json`

## Reference

- local GUI repo: `../notice-winner-pipeline-project`
- GUI rebuild reference: `docs/reference/source/APP_REBUILD_SPEC_KR.md`
- canonical document index: `docs/00_CANONICAL_INDEX_KR.md`
  - canonical set:
  - `docs/spec/FUNCTIONAL_SPEC_KR.md`
  - `docs/spec/SYSTEM_DESIGN_KR.md`
  - `docs/spec/TECHNICAL_SPEC_KR.md`
  - `docs/spec/OPERATIONS_POLICY_KR.md`
  - `docs/spec/UI_SCREEN_SPEC_KR.md`
  - `docs/spec/REBUILD_IMPLEMENTATION_PLAYBOOK_KR.md`
- reference documents index: `docs/reference/00_REFERENCE_INDEX_KR.md`
  - rebuild support set:
  - `docs/reference/rebuild/REBUILD_GOLDEN_SCENARIOS_KR.md`
  - `docs/reference/rebuild/SCREEN_API_DB_FIELD_MAPPING_KR.md`
  - `docs/reference/rebuild/UI_STATE_MATRIX_KR.md`
- archive documents index: `docs/archive/00_ARCHIVE_INDEX_KR.md`

