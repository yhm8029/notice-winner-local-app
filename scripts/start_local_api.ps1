param(
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 8000,
    [string]$ReportsRoot = "",
    [string]$SQLitePath = "",
    [switch]$OpenBrowser
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path $PSScriptRoot -Parent
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw ".venv python not found: $Python"
}

if ($ReportsRoot) {
    $env:REPORTS_ROOT = $ReportsRoot
}

if (-not $SQLitePath) {
    $DefaultSQLitePath = Join-Path $RepoRoot "data\local.sqlite3"
    if (Test-Path $DefaultSQLitePath) {
        $SQLitePath = $DefaultSQLitePath
    }
}

if ($SQLitePath) {
    if ([System.IO.Path]::IsPathRooted($SQLitePath)) {
        $ResolvedSQLitePath = [System.IO.Path]::GetFullPath($SQLitePath)
    }
    else {
        $ResolvedSQLitePath = [System.IO.Path]::GetFullPath((Join-Path $RepoRoot $SQLitePath))
    }
    $env:LOCAL_SQLITE_PATH = $ResolvedSQLitePath
    $env:TRACKER_REPOSITORY_BACKEND = "sqlite"
    $env:RUN_REPOSITORY_BACKEND = "sqlite"
    $env:ARTIFACT_REPOSITORY_BACKEND = "sqlite"
    $env:RUN_LOG_REPOSITORY_BACKEND = "sqlite"
    $env:RELATED_NOTICE_CACHE_REPOSITORY_BACKEND = "sqlite"
    $env:RELATED_NOTICE_PUBLICATION_REPOSITORY_BACKEND = "sqlite"
    $env:SALES_CLAIM_REPOSITORY_BACKEND = "sqlite"
    $env:TRACKER_CHANGE_EVENT_REPOSITORY_BACKEND = "sqlite"
    $env:DOWNLOAD_AUDIT_LOG_REPOSITORY_BACKEND = "sqlite"
    $env:LOGIN_AUDIT_LOG_REPOSITORY_BACKEND = "sqlite"
    $env:TRACKER_ENTRY_SNAPSHOT_REPOSITORY_BACKEND = "sqlite"
    $env:HOME_BOOTSTRAP_SNAPSHOT_REPOSITORY_BACKEND = "sqlite"
    $env:BACKFILL_CONFLICT_REPOSITORY_BACKEND = "sqlite"
    $env:SUPABASE_URL = ""
    $env:SUPABASE_SECRET_KEY = ""
    $env:SUPABASE_SECRET = ""
    $env:SUPABASE_SERVICE_ROLE_KEY = ""
    $env:SUPABASE_ANON_KEY = ""
}

$env:LOCAL_APP_DISABLE_LOGIN = "1"
$env:PHASE2_AUTH_ENABLED = "0"

$url = "http://$BindHost`:$Port/app/"
if ($OpenBrowser) {
    Start-Process $url | Out-Null
}

Write-Host "Repo root: $RepoRoot"
Write-Host "REPORTS_ROOT: $($env:REPORTS_ROOT)"
Write-Host "LOCAL_SQLITE_PATH: $($env:LOCAL_SQLITE_PATH)"
Write-Host "Console URL: $url"

Push-Location $RepoRoot
try {
    & $Python -m uvicorn backend.api.app:app --host $BindHost --port $Port
}
finally {
    Pop-Location
}
