param(
    [ValidateSet('all', 'en', 'fa')]
    [string]$Language = 'all',
    [switch]$Clean
)

$ErrorActionPreference = 'Stop'
$paperRoot = $PSScriptRoot
$buildRoot = Join-Path $paperRoot 'build'
$outputRoot = Join-Path $paperRoot 'output'

function Assert-PaperChild([string]$Path) {
    $full = [IO.Path]::GetFullPath($Path)
    $prefix = [IO.Path]::GetFullPath($paperRoot) + [IO.Path]::DirectorySeparatorChar
    if (-not $full.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to operate outside the paper directory: $full"
    }
}

function Invoke-Checked(
    [string]$Command,
    [string[]]$Arguments,
    [string]$Label,
    [string]$Transcript
) {
    & $Command @Arguments *> $Transcript
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n$Label failed. Last 40 transcript lines:" -ForegroundColor Red
        Get-Content -LiteralPath $Transcript -Tail 40
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

function Assert-CleanLog([string]$LogPath) {
    $bad = Select-String -LiteralPath $LogPath -Pattern @(
        'LaTeX Warning: Citation .* undefined',
        'LaTeX Warning: There were undefined references',
        'LaTeX Warning: Label\(s\) may have changed',
        'Overfull \\hbox',
        'Underfull \\hbox',
        'Overfull \\vbox',
        'Underfull \\vbox'
    )
    if ($bad) {
        $bad | ForEach-Object { Write-Host $_.Line }
        throw "Layout or reference warnings remain in $LogPath"
    }
}

$miktexBin = 'D:\Programs\MiKTeX\miktex\bin\x64'
if (-not (Get-Command pdflatex -ErrorAction SilentlyContinue) -and
    (Test-Path (Join-Path $miktexBin 'pdflatex.exe'))) {
    $env:PATH = "$miktexBin;$env:PATH"
}

$required = @('pdflatex', 'bibtex', 'xelatex')
foreach ($name in $required) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        throw "Required LaTeX command not found: $name"
    }
}

$selected = if ($Language -eq 'all') { @('en', 'fa') } else { @($Language) }
foreach ($code in $selected) {
    $dir = Join-Path $buildRoot $code
    Assert-PaperChild $dir
    if ($Clean -and (Test-Path $dir)) {
        Remove-Item -LiteralPath $dir -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}
New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null

if ($selected -contains 'en') {
    $source = Join-Path $paperRoot 'en'
    $build = Join-Path $buildRoot 'en'
    $job = 'paper-en'
    $common = @(
        '-interaction=nonstopmode',
        '-halt-on-error',
        "-jobname=$job",
        "-output-directory=$build",
        'main.tex'
    )
    $oldBibInputs = $env:BIBINPUTS
    $env:BIBINPUTS = "$source;"
    Push-Location $source
    try {
        Invoke-Checked pdflatex $common 'English pdflatex pass 1' (Join-Path $build 'pass-1.txt')
        Invoke-Checked bibtex @((Join-Path $build $job)) 'English BibTeX' (Join-Path $build 'bibtex.txt')
        Invoke-Checked pdflatex $common 'English pdflatex pass 2' (Join-Path $build 'pass-2.txt')
        Invoke-Checked pdflatex $common 'English pdflatex pass 3' (Join-Path $build 'pass-3.txt')
    } finally {
        Pop-Location
        $env:BIBINPUTS = $oldBibInputs
    }
    Assert-CleanLog (Join-Path $build "$job.log")
    if (Select-String -LiteralPath (Join-Path $build "$job.blg") -Pattern '^Warning--') {
        throw 'BibTeX warnings remain in the English build.'
    }
    Copy-Item -LiteralPath (Join-Path $build "$job.pdf") `
        -Destination (Join-Path $outputRoot "$job.pdf") -Force
    Write-Host 'English PDF built successfully.' -ForegroundColor Green
}

if ($selected -contains 'fa') {
    $source = Join-Path $paperRoot 'fa'
    $build = Join-Path $buildRoot 'fa'
    $job = 'paper-fa'
    $common = @(
        '-interaction=nonstopmode',
        '-halt-on-error',
        "-jobname=$job",
        "-output-directory=$build",
        'main.tex'
    )
    $oldFontConfig = $env:FONTCONFIG_FILE
    $env:FONTCONFIG_FILE = Join-Path $source 'fonts.conf'
    Push-Location $source
    try {
        Invoke-Checked xelatex $common 'Persian XeLaTeX pass 1' (Join-Path $build 'pass-1.txt')
        Invoke-Checked xelatex $common 'Persian XeLaTeX pass 2' (Join-Path $build 'pass-2.txt')
    } finally {
        Pop-Location
        $env:FONTCONFIG_FILE = $oldFontConfig
    }
    Assert-CleanLog (Join-Path $build "$job.log")
    Copy-Item -LiteralPath (Join-Path $build "$job.pdf") `
        -Destination (Join-Path $outputRoot "$job.pdf") -Force
    Write-Host 'Persian PDF built successfully.' -ForegroundColor Green
}
