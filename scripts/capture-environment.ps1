[CmdletBinding()]
param(
    [string]$PwnzzAIPath,
    [string]$PwnzzAIImage = "ghcr.io/owasp/pwnzzai:latest",
    [string]$PwnzzAIBaseUrl = "http://localhost:8080",
    [string]$OllamaHost = "http://localhost:11434",
    [string]$OllamaModel = "REPLACE_WITH_PINNED_MODEL",
    [string]$OutputPath
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
if (-not $OutputPath) {
    $Stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
    $OutputPath = Join-Path $Root "environment\captured\environment-$Stamp.json"
}

function Get-FirstLine {
    param([scriptblock]$Command)
    try {
        [string](& $Command 2>&1 | Select-Object -First 1)
    }
    catch {
        "UNAVAILABLE: $($_.Exception.Message)"
    }
}

$PythonCommand = Get-Command python -ErrorAction SilentlyContinue
$PythonVersion = if ($PythonCommand) {
    Get-FirstLine { python --version }
} else {
    "UNAVAILABLE"
}
$PythonExecutable = if ($PythonCommand) { $PythonCommand.Source } else { "UNAVAILABLE" }

$GarakVersion = if ($PythonCommand) {
    Get-FirstLine { python -m garak --version }
} else {
    "UNAVAILABLE"
}

$DockerVersion = Get-FirstLine { docker --version 2>$null }
$ComposeVersion = Get-FirstLine { docker compose version 2>$null }
$OllamaVersion = Get-FirstLine { ollama --version }

$PwnzzAICommit = "UNAVAILABLE"
if ($PwnzzAIPath -and (Test-Path -LiteralPath (Join-Path $PwnzzAIPath ".git"))) {
    $PwnzzAICommit = Get-FirstLine { git -C $PwnzzAIPath rev-parse HEAD }
}

$ImageDigest = "UNAVAILABLE"
try {
    $ImageDigest = docker image inspect $PwnzzAIImage --format "{{index .RepoDigests 0}}" 2>$null
    if (-not $ImageDigest) { $ImageDigest = "UNAVAILABLE" }
}
catch {}

$ModelDigest = "UNAVAILABLE"
$ModelQuantization = $null
$ModelSize = $null
try {
    $Tags = Invoke-RestMethod -Uri "$OllamaHost/api/tags" -Method Get -TimeoutSec 10
    $Match = $Tags.models | Where-Object {
        $_.name -eq $OllamaModel -or $_.model -eq $OllamaModel
    } | Select-Object -First 1
    if ($Match) {
        $ModelDigest = [string]$Match.digest
        $ModelQuantization = [string]$Match.details.quantization_level
        $ModelSize = [int64]$Match.size
    }
}
catch {}

$Cpu = "UNAVAILABLE"
$Gpu = "UNAVAILABLE"
$Ram = $null
try {
    $Cpu = [string](Get-CimInstance Win32_Processor -ErrorAction Stop |
        Select-Object -First 1 -ExpandProperty Name)
}
catch {}
try {
    $Ram = [int64](Get-CimInstance Win32_ComputerSystem -ErrorAction Stop |
        Select-Object -ExpandProperty TotalPhysicalMemory)
}
catch {}
try {
    $Gpu = [string](Get-CimInstance Win32_VideoController -ErrorAction Stop |
        Select-Object -First 1 -ExpandProperty Name)
}
catch {}

$Manifest = [ordered]@{
    schema_version = "1.0.0"
    captured_at = (Get-Date).ToUniversalTime().ToString("o")
    host = [ordered]@{
        os = [Environment]::OSVersion.VersionString
        architecture = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()
        cpu = $Cpu
        gpu = $Gpu
        ram_bytes = $Ram
    }
    python = [ordered]@{
        version = $PythonVersion
        executable = $PythonExecutable
    }
    garak = [ordered]@{
        version = $GarakVersion
        requirements_lock_sha256 = $null
    }
    docker = [ordered]@{
        version = $DockerVersion
        compose_version = $ComposeVersion
    }
    pwnzzai = [ordered]@{
        commit = $PwnzzAICommit
        image = $PwnzzAIImage
        image_digest = [string]$ImageDigest
        base_url = $PwnzzAIBaseUrl
    }
    ollama = [ordered]@{
        version = $OllamaVersion
        host = $OllamaHost
        model = $OllamaModel
        model_digest = $ModelDigest
        quantization = $ModelQuantization
        size_bytes = $ModelSize
    }
    notes = @(
        "Review UNAVAILABLE fields manually.",
        "No environment-variable values were captured."
    )
}

$Parent = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Path $Parent -Force | Out-Null
$Manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
Write-Output "Environment manifest written to $OutputPath"
Write-Output "Review the file before committing it."
