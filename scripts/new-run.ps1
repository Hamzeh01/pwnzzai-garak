[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern("^[A-Za-z0-9._-]{3,80}$")]
    [string]$RunId
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Targets = @(
    (Join-Path $Root "results\raw\$RunId"),
    (Join-Path $Root "results\normalized\$RunId"),
    (Join-Path $Root "evidence\attacks\$RunId")
)

foreach ($Target in $Targets) {
    if (Test-Path -LiteralPath $Target) {
        throw "Run path already exists; choose a new RunId: $Target"
    }
}

foreach ($Target in $Targets) {
    New-Item -ItemType Directory -Path $Target | Out-Null
}

$Template = Join-Path $Root "templates\experiment-config.example.json"
$Destination = Join-Path $Targets[0] "experiment-config.json"
Copy-Item -LiteralPath $Template -Destination $Destination

Write-Output "Initialized run: $RunId"
Write-Output "Review $Destination and keep allow_attack_execution=false until Phase 5 approval."

