param(
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 8000,
    [string]$ReportsRoot = "",
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

$url = "http://$BindHost`:$Port/app/"
if ($OpenBrowser) {
    Start-Process $url | Out-Null
}

Write-Host "Repo root: $RepoRoot"
Write-Host "REPORTS_ROOT: $($env:REPORTS_ROOT)"
Write-Host "Console URL: $url"

Push-Location $RepoRoot
try {
    & $Python -m uvicorn backend.api.app:app --host $BindHost --port $Port
}
finally {
    Pop-Location
}
