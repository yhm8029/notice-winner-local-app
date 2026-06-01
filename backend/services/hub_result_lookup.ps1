param(
    [string]$QueryBase64,
    [string]$OutputPath,
    [int]$MaxResults = 5,
    [double]$TimeoutSec = 20
)
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = `
    [Net.SecurityProtocolType]::Tls12 -bor `
    [Net.SecurityProtocolType]::Tls11 -bor `
    [Net.SecurityProtocolType]::Tls
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = 'Stop'

$query = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($QueryBase64))
$listUrl = 'https://www.hub.go.kr/portal/dps/dsr/idx-dsr-selectDesignPbpPbancList.do'
$awardUrl = 'https://www.hub.go.kr/portal/dps/dpr/idx-dpr-designPbpPrwinPdtList.do'
$headers = @{
    'User-Agent' = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    'Accept-Language' = 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
}
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$first = Invoke-WebRequest -Uri $listUrl -Headers $headers -WebSession $session -UseBasicParsing -TimeoutSec ([int][Math]::Ceiling($TimeoutSec))
$csrf = [regex]::Match($first.Content, '<meta name="_csrf" content="([^"]+)"').Groups[1].Value
if (-not $csrf) {
    Set-Content -Path $OutputPath -Value '[]' -Encoding UTF8
    exit 0
}
$headers['X-CSRF-TOKEN'] = $csrf

$form = [ordered]@{
    '_csrf' = $csrf
    'designPbpNo' = ''
    'cycl' = ''
    'schdlSn' = '2'
    'detailMode' = ''
    'tabNo' = '4'
    'listRetUrl' = ''
    'dtlSearchYn' = ''
    'pageIndex' = '1'
    'pstnSggCd' = ''
    'pbpWayCd' = ''
    'instTypeCd' = ''
    'bdstMnUsgCd' = ''
    'sBdstScale' = ''
    'sPrnmntDsco' = ''
    'archActCd' = ''
    'searchCondition' = 'DESIGN_PBP_NM'
    'searchKeyword' = $query
}
$page = Invoke-WebRequest -Uri $listUrl -Method POST -Body $form -Headers $headers -WebSession $session -ContentType 'application/x-www-form-urlencoded' -UseBasicParsing -TimeoutSec ([int][Math]::Ceiling($TimeoutSec))
$pattern = '(?s)<p class="tit link"><a href="#" onclick="fnDprDesignDtlInfo\(''([^'']+)'',''([^'']+)'',''([^'']+)'',''([^'']+)''\);">([^<]+)</a></p>'
$matches = [regex]::Matches($page.Content, $pattern)
$ajaxHeaders = @{
    'User-Agent' = $headers['User-Agent']
    'Accept-Language' = $headers['Accept-Language']
    'X-CSRF-TOKEN' = $csrf
    'X-Requested-With' = 'XMLHttpRequest'
    'Accept' = 'application/json, text/javascript, */*; q=0.01'
}
$results = New-Object System.Collections.Generic.List[object]
foreach ($m in ($matches | Select-Object -First $MaxResults)) {
    $designPbpNo = $m.Groups[1].Value
    $cycl = $m.Groups[2].Value
    $title = $m.Groups[5].Value.Trim()
    try {
        $body = @{ designPbpNo = $designPbpNo; cycl = $cycl } | ConvertTo-Json -Compress
        $resp = Invoke-RestMethod -Uri $awardUrl -Method POST -Body $body -Headers $ajaxHeaders -WebSession $session -ContentType 'application/json; charset=UTF-8' -TimeoutSec ([int][Math]::Ceiling($TimeoutSec))
        foreach ($award in @($resp.prwinPdtList)) {
            if (($award.prwinYn -eq 'Y') -and [string]$award.rprsBzentyNm) {
                $results.Add([pscustomobject]@{
                    title = $title
                    winnerOffice = [string]$award.rprsBzentyNm
                    winnerRank = [string]$award.wnpzNm
                    designPbpNo = $designPbpNo
                    cycl = $cycl
                })
            }
        }
    } catch {
        continue
    }
}

$json = $results | ConvertTo-Json -Depth 10 -Compress
if (-not $json) {
    $json = '[]'
}
Set-Content -Path $OutputPath -Value $json -Encoding UTF8
