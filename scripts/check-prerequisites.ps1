[CmdletBinding()]
param()

$ErrorActionPreference = "Continue"

function Show-Tool {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string[]]$VersionArgs
    )

    $Command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $Command) {
        [pscustomobject]@{ Tool = $Name; Found = $false; Version = "NOT FOUND" }
        return
    }

    try {
        $Output = @(& $Command.Source @VersionArgs 2>&1 | ForEach-Object { [string]$_ })
        $VersionLine = $Output |
            Where-Object { $_ -match "(?i)\bversion\b" } |
            Select-Object -Last 1
        if (-not $VersionLine) {
            $VersionLine = $Output | Select-Object -First 1
        }
        [pscustomobject]@{
            Tool = $Name
            Found = $true
            Version = [string]$VersionLine
        }
    }
    catch {
        [pscustomobject]@{
            Tool = $Name
            Found = $true
            Version = "ERROR: $($_.Exception.Message)"
        }
    }
}

$Rows = @(
    Show-Tool -Name "python" -VersionArgs @("--version")
    Show-Tool -Name "git" -VersionArgs @("--version")
    Show-Tool -Name "docker" -VersionArgs @("--version")
    Show-Tool -Name "ollama" -VersionArgs @("--version")
)

$Rows | Format-Table -AutoSize

if (Get-Command docker -ErrorAction SilentlyContinue) {
    try {
        docker compose version 2>$null
    }
    catch {
        Write-Warning "Docker Compose check failed: $($_.Exception.Message)"
    }
}

Write-Output ""
Write-Output "This script is read-only. It does not install software or start services."
