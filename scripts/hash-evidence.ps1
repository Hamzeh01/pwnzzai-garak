[CmdletBinding()]
param(
    [string]$InputPath,
    [string]$OutputPath
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not $InputPath) {
    $InputPath = Join-Path $Root "evidence"
}
if (-not $OutputPath) {
    $OutputPath = Join-Path $Root "evidence\evidence-sha256.csv"
}

$ResolvedInput = (Resolve-Path -LiteralPath $InputPath).Path
$Files = Get-ChildItem -LiteralPath $ResolvedInput -File -Recurse -Force |
    Where-Object { $_.FullName -ne $OutputPath } |
    Sort-Object FullName

$Rows = foreach ($File in $Files) {
    $Hash = Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256
    [pscustomobject]@{
        Path = $File.FullName.Substring($ResolvedInput.Length).TrimStart("\")
        SHA256 = $Hash.Hash.ToLowerInvariant()
        SizeBytes = $File.Length
        LastWriteTimeUtc = $File.LastWriteTimeUtc.ToString("o")
    }
}

$Rows | Export-Csv -LiteralPath $OutputPath -NoTypeInformation -Encoding UTF8
Write-Output "Wrote $($Rows.Count) hash record(s) to $OutputPath"

