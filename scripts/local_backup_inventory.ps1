param(
  [string]$EnvFile = ".env.local-backup",
  [string]$BackupRoot = "backups",
  [string]$Timestamp = "",
  [switch]$DryRunEc2
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Timestamp)) {
  $Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd_HHmmss")
}

$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $repoRoot

function Invoke-CheckedPython {
  param(
    [Parameter(Mandatory = $true)]
    [string[]]$Arguments
  )

  python @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "python $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
  }
}

Invoke-CheckedPython @(
  "scripts/backup_supabase_inventory.py",
  "--env-file", $EnvFile,
  "--backup-root", $BackupRoot,
  "--timestamp", $Timestamp
)

$ec2Args = @(
  "scripts/backup_ec2_inventory.py",
  "--env-file", $EnvFile,
  "--backup-root", $BackupRoot,
  "--timestamp", $Timestamp
)
if ($DryRunEc2) {
  $ec2Args += "--dry-run"
}
Invoke-CheckedPython $ec2Args

$supabaseDir = Join-Path $BackupRoot "supabase\$Timestamp"
$ec2Dir = Join-Path $BackupRoot "ec2\$Timestamp"
Invoke-CheckedPython @(
  "scripts/reconcile_backup_artifacts.py",
  "--supabase-dir", $supabaseDir,
  "--ec2-dir", $ec2Dir,
  "--output-dir", $supabaseDir
)

Write-Host "Local backup inventory complete: $Timestamp"
