<#
.SYNOPSIS
    End-to-end PwnzzAI security assessment with Garak (Windows / PowerShell).

.DESCRIPTION
    Brings up the pinned PwnzzAI lab, runs every Garak suite against it, and
    builds the analysis tables and figures. Ollama must already be running on
    the host with the pinned model pulled (llama3.2:1b).

    Nothing here reimplements scanning: each suite is a real Garak run and the
    artifacts under garak_runs/ are Garak's own report.jsonl / report.html.

.EXAMPLE
    pwsh scripts/run_assessment.ps1
    pwsh scripts/run_assessment.ps1 -Suite direct-injection
#>
param(
    [string]$Suite = "all",
    [switch]$SkipLab,
    [switch]$SkipAnalyze
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

# Garak prints emoji; force a UTF-8 console so Windows cp1252 does not crash.
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
$env:PYTHONPATH = $Root

$Python = Join-Path $Root ".venv/Scripts/python.exe"
if (-not (Test-Path $Python)) { $Python = "python" }

if (-not $SkipLab) {
    Write-Host "== bringing up the PwnzzAI lab ==" -ForegroundColor Cyan
    docker compose -f lab/docker-compose.yml up -d
    Write-Host "waiting for the app to answer on 127.0.0.1:18080 ..."
    for ($i = 0; $i -lt 30; $i++) {
        try {
            $r = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:18080/" -TimeoutSec 5
            if ($r.StatusCode -eq 200) { break }
        } catch { Start-Sleep -Seconds 2 }
    }
}

Write-Host "== preflight ==" -ForegroundColor Cyan
& $Python -m garak_pwnzz preflight

Write-Host "== running suite(s): $Suite ==" -ForegroundColor Cyan
& $Python -m garak_pwnzz run $Suite --quiet

if (-not $SkipAnalyze) {
    Write-Host "== building analysis ==" -ForegroundColor Cyan
    & $Python -m garak_pwnzz analyze
}

Write-Host "== done. Artifacts in garak_runs/ and garak_analysis/ ==" -ForegroundColor Green
