param(
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 8000,
    [string]$ReportsRoot = ""
)

$ErrorActionPreference = "Stop"

$apiScript = Join-Path $PSScriptRoot "start_local_api.ps1"
& $apiScript -BindHost $BindHost -Port $Port -ReportsRoot $ReportsRoot -OpenBrowser
