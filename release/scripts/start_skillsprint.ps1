#Requires -Version 5.1
<#
    SkillSprint Academy — one-command offline launcher (plan §10.1).

    What it does:
      1. Verifies Python 3.11+ is on PATH.
      2. Creates/activates a venv if missing.
      3. Installs requirements. Falls back to vendored wheels when offline.
      4. Forces OFFLINE_MODE=true in .env if not present.
      5. Boots Flask on http://127.0.0.1:5000 (offline bind host).
      6. Opens the browser to that URL.

    Usage:
        pwsh scripts/start_skillsprint.ps1
#>

[CmdletBinding()] param(
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..") | Select-Object -ExpandProperty Path
$venvPath    = Join-Path $projectRoot "venv"
$envFile     = Join-Path $projectRoot ".env"
$wheelsPath  = Join-Path $projectRoot "bundles\wheels"
$reqPath     = Join-Path $projectRoot "requirements.txt"
$appPy       = Join-Path $projectRoot "app.py"
$dbPath      = Join-Path $projectRoot "instance\skillsprint.db"

function Write-Step($msg)  { Write-Host "== $msg" -ForegroundColor Cyan }
function Write-Ok($msg)    { Write-Host "   ok: $msg" -ForegroundColor Green }
function Write-Warn2($msg) { Write-Host "   ! $msg" -ForegroundColor Yellow }

# ---------------------------------------------------------------------------
# 1. Python check
# ---------------------------------------------------------------------------
Write-Step "Checking Python 3.11+"
try {
    $pyVer = (& py -3 --version 2>$null) -replace '^Python\s*', ''
    if (-not $pyVer) { $pyVer = (& python --version 2>$null) -replace '^Python\s*', '' }
    if (-not $pyVer) { throw "no python output" }
    $parts = $pyVer.Split('.')
    [int]$major = $parts[0]; [int]$minor = $parts[1]
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
        Write-Warn2 "Detected Python $pyVer but 3.11+ is recommended. Proceeding anyway."
    } else {
        Write-Ok "Python $pyVer"
    }
} catch {
    Write-Warn2 "Could not detect Python version via 'py'/'python'. Make sure it is installed."
    $py = Read-Host "Path to python.exe (Enter to exit)"
    if (-not $py) { exit 1 }
    Set-Alias -Name pyexe -Value $py
}

# ---------------------------------------------------------------------------
# 2. venv
# ---------------------------------------------------------------------------
if (-not (Test-Path $venvPath)) {
    Write-Step "Creating virtual environment at $venvPath"
    & py -3 -m venv $venvPath
    Write-Ok "venv created"
}
$activate = Join-Path $venvPath "Scripts\Activate.ps1"
if (Test-Path $activate) {
    . $activate
    Write-Ok "venv activated"
} else {
    Write-Warn2 "venv missing activate script; continuing with system Python"
}

# ---------------------------------------------------------------------------
# 3. pip install
# ---------------------------------------------------------------------------
Write-Step "Checking dependencies"
$online = $false
try {
    $null = Invoke-WebRequest -Uri 'https://pypi.org' -TimeoutSec 3 -UseBasicParsing
    $online = $true
} catch { $online = $false }
if (-not $online -and (Test-Path $wheelsPath)) {
    Write-Warn2 "Internet appears unavailable - installing from bundles\wheels (offline)"
    & py -3 -m pip install --no-index --find-links=$wheelsPath -r $reqPath
} else {
    & py -3 -m pip install -r $reqPath
}
Write-Ok "dependencies resolved"

# ---------------------------------------------------------------------------
# 4. .env
# ---------------------------------------------------------------------------
Write-Step "Ensuring OFFLINE_MODE=true in .env"
if (-not (Test-Path $envFile)) { "" | Out-File -FilePath $envFile -Encoding utf8 }
$content = Get-Content -Raw $envFile
if ($content -notmatch '(?m)^\s*OFFLINE_MODE\s*=') {
    Add-Content -Path $envFile -Value "OFFLINE_MODE=true"
    Write-Ok "OFFLINE_MODE=true added to .env"
} else {
    # Force ON (replace the line).
    $new = $content -replace '(?m)^\s*OFFLINE_MODE\s*=.*$', 'OFFLINE_MODE=true'
    $new | Set-Content -Path $envFile -Encoding utf8 -NoNewline
    Write-Ok "OFFLINE_MODE=true set in .env"
}

# ---------------------------------------------------------------------------
# 5. DB + seed (idempotent)
# ---------------------------------------------------------------------------
Write-Step "Creating database tables (if missing)"
if (-not (Test-Path (Split-Path $dbPath -Parent))) {
    New-Item -ItemType Directory (Split-Path $dbPath -Parent) | Out-Null
}
& py -3 -c 'from app import create_tables; create_tables()' | Out-Null
Write-Ok "tables ok"

Write-Step "Running seed.py (idempotent - adds new curriculum + capstones)"
& py -3 seed.py | Out-Null
Write-Ok "seed ok"

# ---------------------------------------------------------------------------
# 6. Launch
# ---------------------------------------------------------------------------
$bind = "http://127.0.0.1:5000"
Write-Step "Starting Flask on $bind (Ctrl+C to stop)"
if (-not $NoBrowser) {
    try { Start-Process $bind } catch { Write-Warn2 "Open $bind manually" }
}
& py -3 $appPy
