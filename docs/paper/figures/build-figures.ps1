# Render every figure the paper needs into PDF, in this directory.
#
#   1. Mermaid sources (*.mmd, authored here) -> *.pdf  via mermaid-cli
#   2. Analysis charts (garak_analysis/figures/*.svg) -> *.pdf via an SVG converter
#
# Requirements (any one SVG converter is enough):
#   Mermaid CLI plus Google Chrome (MERMAID_CLI can override its path)
#   rsvg-convert  OR  inkscape  OR  python -m pip install svglib
#
# Nothing here is required to *read* the draft: paper.tex draws a labelled
# placeholder for any figure that has not been built.

$ErrorActionPreference = 'Continue'
Set-Location $PSScriptRoot

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$analysisFigs = Join-Path $projectRoot 'garak_analysis\figures'
$venvPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
$python = if (Test-Path $venvPython) {
    $venvPython
} else {
    (Get-Command python -ErrorAction SilentlyContinue).Source
}
$failed = $false

function Test-NeedsBuild($sourcePath, $outputPath) {
    if (-not (Test-Path $outputPath)) { return $true }
    return (Get-Item $sourcePath).LastWriteTimeUtc -gt
        (Get-Item $outputPath).LastWriteTimeUtc
}

# --- 1. Mermaid -> PDF ------------------------------------------------
$npx = Get-Command npx.cmd -ErrorAction SilentlyContinue
$pathMmdc = Get-Command mmdc.cmd -ErrorAction SilentlyContinue
$mermaidCliCandidates = @(
    $env:MERMAID_CLI,
    'D:\Programs\MermaidCLI\node_modules\.bin\mmdc.cmd',
    $(if ($pathMmdc) { $pathMmdc.Source })
)
$mermaidCli = $mermaidCliCandidates |
    Where-Object { $_ -and (Test-Path $_) } |
    Select-Object -First 1
$chromeCandidates = @(
    'C:\Program Files\Google\Chrome\Application\chrome.exe',
    'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
    (Join-Path $env:LOCALAPPDATA 'Google\Chrome\Application\chrome.exe')
)
$chrome = $chromeCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (($mermaidCli -or $npx) -and $chrome) {
    $puppeteerConfig = Join-Path $env:TEMP 'pwnzzai-mermaid-puppeteer.json'
    $configJson = @{
        executablePath = $chrome
        protocolTimeout = 300000
        args = @('--disable-gpu')
    } | ConvertTo-Json
    [System.IO.File]::WriteAllText(
        $puppeteerConfig,
        $configJson,
        [System.Text.UTF8Encoding]::new($false)
    )
    $env:PUPPETEER_SKIP_DOWNLOAD = 'true'
    $env:npm_config_cache = Join-Path $env:TEMP 'pwnzzai-mermaid-npm-cache'

    foreach ($src in Get-ChildItem -Filter '*.mmd') {
        $out = [System.IO.Path]::ChangeExtension($src.Name, 'pdf')
        $outPath = Join-Path $PSScriptRoot $out
        if (-not (Test-NeedsBuild $src.FullName $outPath)) {
            Write-Host "mermaid: $($src.Name) is up to date"
            continue
        }
        Write-Host "mermaid: $($src.Name) -> $out"
        $mermaidArgs = @(
            '-p', $puppeteerConfig,
            '-i', $src.Name,
            '-o', $out,
            '--pdfFit',
            '--backgroundColor', 'white'
        )
        if ($mermaidCli) {
            & $mermaidCli @mermaidArgs
        } else {
            & $npx.Source -y '@mermaid-js/mermaid-cli' @mermaidArgs
        }
        if ($LASTEXITCODE -ne 0) {
            Write-Host '  FAILED'
            $failed = $true
        }
    }
} else {
    Write-Warning 'npx and Google Chrome are required to render Mermaid diagrams.'
    $failed = $true
}

# --- 2. SVG -> PDF ----------------------------------------------------
function Convert-SvgToPdf($sourcePath, $outputPath) {
    if (Get-Command rsvg-convert -ErrorAction SilentlyContinue) {
        rsvg-convert -f pdf -o $outputPath $sourcePath
        return $LASTEXITCODE -eq 0
    }
    if (Get-Command inkscape -ErrorAction SilentlyContinue) {
        inkscape $sourcePath --export-type=pdf --export-filename=$outputPath
        return $LASTEXITCODE -eq 0
    }
    if ($python) {
        & $python -c 'import svglib.svglib' 2>$null
        if ($LASTEXITCODE -eq 0) {
            & $python (Join-Path $PSScriptRoot 'svg_to_pdf.py') `
                $sourcePath $outputPath
            return $LASTEXITCODE -eq 0
        }
    }
    return $false
}

if (Test-Path $analysisFigs) {
    foreach ($src in Get-ChildItem -Path $analysisFigs -Filter '*.svg') {
        $out = [System.IO.Path]::ChangeExtension($src.Name, 'pdf')
        $outPath = Join-Path $PSScriptRoot $out
        if (-not (Test-NeedsBuild $src.FullName $outPath)) {
            Write-Host "svg:     $($src.Name) is up to date"
            continue
        }
        Write-Host "svg:     $($src.Name) -> $out"
        if (-not (Convert-SvgToPdf $src.FullName $outPath)) {
            Write-Warning 'No working SVG converter found (rsvg-convert / inkscape / svglib).'
            $failed = $true
            break
        }
    }
} else {
    Write-Warning "$analysisFigs not found; run 'python -m garak_pwnzz analyze' first."
    $failed = $true
}

if ($failed) {
    Write-Host ''
    Write-Host 'Some figures were not built. paper.tex will show placeholders for those.'
    exit 1
}

Write-Host ''
Write-Host 'All paper figures are ready.'
exit 0
