# Project Tracker Web

Web repo for the project tracker rebuild.

## Scope

- `backend/`: FastAPI API scaffold and repository layer
- `supabase/`: Postgres schema migrations and seed data
- `docs/`: canonical/reference/archive documentation hierarchy
- `frontend/`: placeholder for the future UI

## Tracker Repository Backend

The tracker APIs support two repository backends.

- `TRACKER_REPOSITORY_BACKEND=in_memory`
  - forces the local in-memory repository
  - uses seeded sample rows for local API scaffolding
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
- `RUN_REPOSITORY_BACKEND=supabase`
  - persists `pipeline_runs` in Supabase/Postgres
- `RUN_REPOSITORY_BACKEND=auto`
  - optional explicit auto mode

Default selection:

- if unset or `auto`, it inherits `TRACKER_REPOSITORY_BACKEND`
- if neither is set, it auto-selects `supabase` when Supabase env is present, otherwise `in_memory`

Artifact and log repositories follow the same pattern.

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

## Local Conversion Backup Inventory

Before converting the hosted app to local SQLite/storage, create a cloud data inventory.

Create `.env.local-backup` locally. Do not commit it.

```text
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...
EC2_SSH_TARGET=ubuntu@your-ec2-host
EC2_BACKUP_PATHS=/home/ubuntu/notice-winner-pipeline-web/output,/home/ubuntu/notice-winner-pipeline-web/input,/home/ubuntu/notice-winner-pipeline-web/logs
```

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/local_backup_inventory.ps1
```

Outputs are written under `backups/supabase/<timestamp>/` and `backups/ec2/<timestamp>/`. The Supabase manifest contains table row counts and checksums. The EC2 manifest contains app-owned file paths, sizes, and modified timestamps. `artifact_reconciliation.json` reports whether `run_artifacts.storage_path` rows have matching EC2 files.

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
.\scripts\start_local_api.ps1 -Port 8000
```

Run both parity reports with the GUI comparison repo path set explicitly:

```powershell
.\scripts\run_phase1_reports.ps1 -GuiSourceRoot "C:\path\to\gui-repo" -SeedLimit 3
```

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

