[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Validator = Join-Path $PSScriptRoot "validate_pack.py"

$Candidates = @(
    (Join-Path $Root ".venv\Scripts\python.exe"),
    (Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe")
)
$PythonPath = $Candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $PythonPath) {
    $Python = Get-Command python -ErrorAction SilentlyContinue
    if ($Python) {
        $PythonPath = $Python.Source
    }
}
if (-not $PythonPath) {
    throw "Python was not found on PATH. Run the validator with the approved project interpreter."
}

& $PythonPath $Validator
exit $LASTEXITCODE
