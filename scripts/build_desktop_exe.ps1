param(
    [switch]$InstallDependencies,
    [switch]$IncludeLocalData,
    [string]$LocalSqlitePath = "",
    [string]$EnvPath = ""
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Python = if (Test-Path $VenvPython) { $VenvPython } else { "python" }

if ($InstallDependencies) {
    & $Python -m pip install -r backend\requirements.txt -r requirements-desktop.txt
}

& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --name notice-winner `
    --paths . `
    --add-data "frontend;frontend" `
    --add-data "assets;assets" `
    --collect-submodules backend `
    --collect-submodules desktop `
    --hidden-import backend.api.app `
    --hidden-import uvicorn.logging `
    --hidden-import uvicorn.loops.auto `
    --hidden-import uvicorn.protocols.http.auto `
    --hidden-import uvicorn.protocols.websockets.auto `
    desktop\launcher.py

$DistRoot = Join-Path $RepoRoot "dist\notice-winner"
New-Item -ItemType Directory -Force -Path (Join-Path $DistRoot "data") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $DistRoot "output\artifacts") | Out-Null

if ($IncludeLocalData) {
    $LocalDb = if ($LocalSqlitePath) { $LocalSqlitePath } else { Join-Path $RepoRoot "data\local.sqlite3" }
    if (Test-Path $LocalDb) {
        Copy-Item -Force $LocalDb (Join-Path $DistRoot "data\local.sqlite3")
    } else {
        Write-Warning "Local SQLite file was not found: $LocalDb"
    }
}

if ($EnvPath) {
    if (Test-Path $EnvPath) {
        Copy-Item -Force $EnvPath (Join-Path $DistRoot ".env")
    } else {
        Write-Warning "Env file was not found: $EnvPath"
    }
}

Write-Host "Desktop app build complete: $DistRoot\notice-winner.exe"
