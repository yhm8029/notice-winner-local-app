param(
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 8000,
    [string]$StartDate = "20250101",
    [string]$EndDate = "20251231",
    [string]$NoticeTitle = "",
    [switch]$DesignCompetitionPreset,
    [string]$DemandOrg = "",
    [string[]]$Regions = @(),
    [switch]$NoRegionSplit,
    [string]$BidNo = "",
    [string]$ContractDateHint = "",
    [ValidateSet("construction", "service", "goods", "all")]
    [string]$ApiScope = "service",
    [int]$RowsPerPage = 999,
    [int]$MaxPages = 15,
    [ValidateSet("auto", "native", "synthetic")]
    [string]$CollectMode = "auto",
    [switch]$LlmCorrect,
    [string]$LlmModel = "claude-haiku-4-5-20251001",
    [int]$LlmMaxRows = 20,
    [int]$FilterRowWorkers = 12,
    [int]$ExportRowWorkers = 8,
    [int]$SimulateStageDelayMs = 20,
    [int]$PollIntervalSeconds = 15,
    [int]$RunTimeoutMinutes = 180,
    [int]$PauseBetweenRunsSeconds = 3,
    [int]$BatchParallelism = 2,
    [string]$OutputPath = "",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Test-YyyyMmDd {
    param([string]$Value)
    return ($Value -match '^\d{8}$')
}

function ConvertTo-Date {
    param([string]$Value)
    return [datetime]::ParseExact($Value, "yyyyMMdd", $null)
}

function Format-DateYyyyMmDd {
    param([datetime]$Value)
    return $Value.ToString("yyyyMMdd")
}

function Get-MonthRanges {
    param(
        [datetime]$RangeStart,
        [datetime]$RangeEnd
    )

    $cursor = Get-Date -Year $RangeStart.Year -Month $RangeStart.Month -Day 1 -Hour 0 -Minute 0 -Second 0
    $ranges = @()

    while ($cursor -le $RangeEnd) {
        $monthStart = $cursor
        $monthEnd = $monthStart.AddMonths(1).AddDays(-1)
        if ($monthEnd -gt $RangeEnd) {
            $monthEnd = $RangeEnd
        }
        $effectiveStart = if ($monthStart -lt $RangeStart) { $RangeStart } else { $monthStart }
        $effectiveEnd = $monthEnd
        $ranges += [pscustomobject]@{
            Label     = $monthStart.ToString("yyyy-MM")
            StartDate = Format-DateYyyyMmDd $effectiveStart
            EndDate   = Format-DateYyyyMmDd $effectiveEnd
        }
        $cursor = $monthStart.AddMonths(1)
    }

    return $ranges
}

function Get-DefaultRegions {
    return @(
        "서울",
        "부산",
        "대구",
        "인천",
        "광주",
        "대전",
        "울산",
        "세종",
        "경기",
        "강원",
        "충북",
        "충남",
        "전북",
        "전남",
        "경북",
        "경남",
        "제주"
    )
}

if (-not (Test-YyyyMmDd $StartDate)) {
    throw "StartDate must be YYYYMMDD: $StartDate"
}
if (-not (Test-YyyyMmDd $EndDate)) {
    throw "EndDate must be YYYYMMDD: $EndDate"
}
if ($DesignCompetitionPreset -and -not $NoticeTitle.Trim()) {
    $NoticeTitle = "설계공모"
}
if (-not ($BidNo.Trim() -or $NoticeTitle.Trim() -or $DemandOrg.Trim())) {
    throw "At least one of BidNo, NoticeTitle, DemandOrg is required."
}

$start = ConvertTo-Date $StartDate
$end = ConvertTo-Date $EndDate
if ($start -gt $end) {
    throw "StartDate must be less than or equal to EndDate."
}

$baseUrl = "http://$BindHost`:$Port"
$ranges = Get-MonthRanges -RangeStart $start -RangeEnd $end
$results = @()
$regionTargets = @()

if ($DemandOrg.Trim()) {
    $regionTargets += [pscustomobject]@{
        Label = $DemandOrg.Trim()
        DemandOrg = $DemandOrg.Trim()
    }
}
elseif ($Regions.Count -gt 0) {
    foreach ($region in $Regions) {
        if (-not $region.Trim()) {
            continue
        }
        $regionTargets += [pscustomobject]@{
            Label = $region.Trim()
            DemandOrg = $region.Trim()
        }
    }
}
elseif (-not $NoRegionSplit) {
    foreach ($region in Get-DefaultRegions) {
        $regionTargets += [pscustomobject]@{
            Label = $region
            DemandOrg = $region
        }
    }
}
else {
    $regionTargets += [pscustomobject]@{
        Label = "전국"
        DemandOrg = ""
    }
}

Write-Host "API: $baseUrl"
Write-Host "Range: $StartDate ~ $EndDate"
Write-Host "Monthly batches: $(@($ranges).Count)"
Write-Host "Region batches: $(@($regionTargets).Count)"
Write-Host "Batch parallelism: $BatchParallelism"

if ($BatchParallelism -lt 1) {
    throw "BatchParallelism must be at least 1."
}

$batches = @()
foreach ($range in $ranges) {
    foreach ($regionTarget in $regionTargets) {
        $batchLabel = if ($regionTarget.DemandOrg) {
            "$($range.Label) / $($regionTarget.Label)"
        }
        else {
            "$($range.Label) / 전국"
        }

        $batches += [pscustomobject]@{
            Label = $batchLabel
            StartDate = $range.StartDate
            EndDate = $range.EndDate
            DemandOrg = $regionTarget.DemandOrg
        }
    }
}

if ($DryRun) {
    foreach ($batch in $batches) {
        Write-Host ""
        Write-Host "[$($batch.Label)] $($batch.StartDate) ~ $($batch.EndDate)"
        $results += [pscustomobject]@{
            label = $batch.Label
            start_date = $batch.StartDate
            end_date = $batch.EndDate
            demand_org = $batch.DemandOrg
            dry_run = $true
        }
    }
}
else {
    $queue = [System.Collections.Generic.Queue[object]]::new()
    foreach ($batch in $batches) {
        $queue.Enqueue($batch)
    }
    $activeRuns = @()

    while ($queue.Count -gt 0 -or $activeRuns.Count -gt 0) {
        while ($queue.Count -gt 0 -and $activeRuns.Count -lt $BatchParallelism) {
            $batch = $queue.Dequeue()
            $payload = @{
                run_type = "project_tracker"
                params = @{
                    start_date = $batch.StartDate
                    end_date = $batch.EndDate
                    contract_date_hint = $ContractDateHint
                    bid_no = $BidNo
                    notice_title = $NoticeTitle
                    demand_org = $batch.DemandOrg
                    rows_per_page = $RowsPerPage
                    max_pages = $MaxPages
                    api_scope = $ApiScope
                }
                advanced_options = @{
                    collect_mode = $CollectMode
                    llm_correct = [bool]$LlmCorrect
                    llm_model = $LlmModel
                    llm_max_rows = $LlmMaxRows
                    filter_row_workers = $FilterRowWorkers
                    export_row_workers = $ExportRowWorkers
                    simulate_stage_delay_ms = $SimulateStageDelayMs
                }
            }

            Write-Host ""
            Write-Host "[$($batch.Label)] $($batch.StartDate) ~ $($batch.EndDate)"

            $payloadJson = $payload | ConvertTo-Json -Depth 8
            $payloadBytes = [System.Text.Encoding]::UTF8.GetBytes($payloadJson)

            $createResponse = Invoke-RestMethod `
                -Method Post `
                -Uri "$baseUrl/api/runs" `
                -ContentType "application/json; charset=utf-8" `
                -Body $payloadBytes

            $runId = [string]$createResponse.id
            Write-Host "Created run: $runId"

            $activeRuns += [pscustomobject]@{
                Label = $batch.Label
                RunId = $runId
                StartDate = $batch.StartDate
                EndDate = $batch.EndDate
                DemandOrg = $batch.DemandOrg
                Deadline = (Get-Date).AddMinutes($RunTimeoutMinutes)
            }

            if ($PauseBetweenRunsSeconds -gt 0) {
                Start-Sleep -Seconds $PauseBetweenRunsSeconds
            }
        }

        Start-Sleep -Seconds $PollIntervalSeconds
        $nextActiveRuns = @()
        foreach ($active in $activeRuns) {
            $detail = Invoke-RestMethod -Method Get -Uri "$baseUrl/api/runs/$($active.RunId)"
            $status = [string]$detail.status
            $stage = [string]$detail.progress_stage
            $current = [int]$detail.progress_current
            $total = [int]$detail.progress_total
            Write-Host "  [$($active.Label)] status=$status stage=$stage progress=$current/$total"

            if ($status -in @("success", "failed", "cancelled")) {
                $results += [pscustomobject]@{
                    label = $active.Label
                    run_id = $active.RunId
                    start_date = $active.StartDate
                    end_date = $active.EndDate
                    demand_org = $active.DemandOrg
                    status = [string]$detail.status
                    progress_stage = [string]$detail.progress_stage
                    created_at = [string]$detail.created_at
                    started_at = [string]$detail.started_at
                    finished_at = [string]$detail.finished_at
                }
                continue
            }

            if ((Get-Date) -gt $active.Deadline) {
                throw "Run timeout after $RunTimeoutMinutes minute(s): $($active.RunId)"
            }

            $nextActiveRuns += $active
        }
        $activeRuns = $nextActiveRuns
    }
}

$resultsJson = $results | ConvertTo-Json -Depth 6
if ($OutputPath) {
    $resolvedOutputPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputPath)
    $outputDir = Split-Path $resolvedOutputPath -Parent
    if ($outputDir -and -not (Test-Path $outputDir)) {
        New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    }
    Set-Content -Path $resolvedOutputPath -Value $resultsJson -Encoding UTF8
    Write-Host ""
    Write-Host "Saved batch summary: $resolvedOutputPath"
}

Write-Host ""
Write-Output $resultsJson
