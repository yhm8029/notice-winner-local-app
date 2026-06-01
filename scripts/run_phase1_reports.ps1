param(
    [string]$GuiSourceRoot = "",
    [string]$SeedCsv = "",
    [int]$SeedLimit = 3,
    [string]$StartDate = "20250101",
    [string]$EndDate = "20250228"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path $PSScriptRoot -Parent
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw ".venv python not found: $Python"
}

$resolvedGuiRoot = ""
if ($GuiSourceRoot) {
    $resolvedGuiRoot = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($GuiSourceRoot)
}
elseif ($env:GUI_PARITY_SOURCE_ROOT) {
    $resolvedGuiRoot = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($env:GUI_PARITY_SOURCE_ROOT)
}
if (-not $resolvedGuiRoot) {
    throw "GuiSourceRoot or GUI_PARITY_SOURCE_ROOT is required for parity reports."
}
if (-not (Test-Path $resolvedGuiRoot)) {
    throw "GUI source root not found: $resolvedGuiRoot"
}
$env:GUI_PARITY_SOURCE_ROOT = $resolvedGuiRoot

if (-not $SeedCsv -and $resolvedGuiRoot) {
    $defaultSeed = Join-Path $resolvedGuiRoot "tests\winner_pipeline_seed_input.csv"
    if (Test-Path $defaultSeed) {
        $SeedCsv = $defaultSeed
    }
}

$equivalenceOutput = Join-Path $RepoRoot "output\phase1-equivalence-report.json"
$artifactOutput = Join-Path $RepoRoot "output\phase1-artifact-diff-report.json"

Push-Location $RepoRoot
try {
    & $Python "scripts\phase1_equivalence_runner.py" --output $equivalenceOutput --gui-source-root $resolvedGuiRoot

    $artifactArgs = @(
        "scripts\phase1_artifact_diff_runner.py",
        "--output", $artifactOutput,
        "--gui-source-root", $resolvedGuiRoot,
        "--seed-limit", $SeedLimit,
        "--start-date", $StartDate,
        "--end-date", $EndDate
    )
    if ($SeedCsv) {
        $artifactArgs += @("--seed-csv", $SeedCsv)
    }
    & $Python @artifactArgs
}
finally {
    Pop-Location
}
