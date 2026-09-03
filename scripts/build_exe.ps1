#Requires -Version 5.1
<#
.SYNOPSIS
    Build ZeroCipher as a standalone Windows executable (.exe)

.DESCRIPTION
    Uses PyInstaller with a .spec file to create a single-file executable that includes:
    - Python runtime
    - All dependencies (Flask, SQLAlchemy, etc.)
    - Static assets (templates, vendor CSS/JS)
    - Bundles (labs, wheels)
    - Instance folder structure

.REQUIREMENTS
    - Python 3.11+
    - PyInstaller: pip install pyinstaller

.USAGE
    pwsh scripts/build_exe.ps1

.NOTES
    Output: release/ZeroCipher.exe
    The exe will create its own instance/ folder on first run for database and configs.
#>

$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..") | Select-Object -ExpandProperty Path
$distPath    = Join-Path $projectRoot "dist"
$buildPath   = Join-Path $projectRoot "build"
$releasePath = Join-Path $projectRoot "release"
$specFile    = Join-Path $projectRoot "ZeroCipher.spec"

function Write-Step($msg)  { Write-Host "== $msg" -ForegroundColor Cyan }
function Write-Ok($msg)    { Write-Host "   ok: $msg" -ForegroundColor Green }
function Write-Warn($msg)  { Write-Host "   ! $msg" -ForegroundColor Yellow }

# ---------------------------------------------------------------------------
# Clean previous builds
# ---------------------------------------------------------------------------
Write-Step "Cleaning previous builds..."
if (Test-Path $distPath) { Remove-Item $distPath -Recurse -Force }
if (Test-Path $buildPath) { Remove-Item $buildPath -Recurse -Force }
if (Test-Path $releasePath) { Remove-Item $releasePath -Recurse -Force }
Write-Ok "Cleaned"

# ---------------------------------------------------------------------------
# Install PyInstaller if needed
# ---------------------------------------------------------------------------
Write-Step "Checking PyInstaller..."
try {
    py -3 -m PyInstaller --version 2>$null | Out-Null
    Write-Ok "PyInstaller available"
} catch {
    Write-Warn "PyInstaller not found, installing..."
    py -3 -m pip install pyinstaller
    Write-Ok "PyInstaller installed"
}

# ---------------------------------------------------------------------------
# Build using .spec file
# ---------------------------------------------------------------------------
Write-Step "Building executable using .spec file (this may take 2-5 minutes)..."
Write-Host "Spec file: $specFile" -ForegroundColor Gray

& py -3 -m PyInstaller --clean --noconfirm --distpath="$distPath" --workpath="$buildPath" "$specFile"

if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller build failed with exit code $LASTEXITCODE"
    exit 1
}

Write-Ok "Build completed"

# ---------------------------------------------------------------------------
# Copy additional files to release folder
# ---------------------------------------------------------------------------
Write-Step "Preparing release folder..."
New-Item -ItemType Directory $releasePath | Out-Null

# Copy executable
$exeSrc = Join-Path $distPath "ZeroCipher.exe"
$exeDst = Join-Path $releasePath "ZeroCipher.exe"
Copy-Item $exeSrc $exeDst -Force
Write-Ok "Executable copied to release/"

# Copy bundles for lab challenges
$bundlesSrc = Join-Path $projectRoot "bundles"
$bundlesDst = Join-Path $releasePath "bundles"
if (Test-Path $bundlesSrc) {
    Copy-Item $bundlesSrc $bundlesDst -Recurse -Force
    Write-Ok "Bundles copied to release/bundles/"
}

# Copy scripts
$scriptsSrc = Join-Path $projectRoot "scripts"
$scriptsDst = Join-Path $releasePath "scripts"
if (Test-Path $scriptsSrc) {
    Copy-Item $scriptsSrc $scriptsDst -Recurse -Force
    Write-Ok "Scripts copied to release/scripts/"
}

# Create a simple launcher batch file for convenience
$launcherBat = @"
@echo off
echo Starting ZeroCipher...
echo The app will open at http://127.0.0.1:5000
echo Press Ctrl+C to stop the server
echo.
ZeroCipher.exe
pause
"@
$launcherBat | Out-File -FilePath (Join-Path $releasePath "Start-ZeroCipher.bat") -Encoding ascii
Write-Ok "Launcher batch file created"

# Create README for release
$readme = @"
ZeroCipher - Offline Cybersecurity Learning Platform
=============================================================

Single-user, fully offline cybersecurity training application.
Runs on Windows 10/11 with no internet required after first run.

QUICK START:
1. Double-click ZeroCipher.exe
   OR
2. Double-click Start-ZeroCipher.bat

The app will start a local web server at http://127.0.0.1:5000
and open it in your default browser.

FIRST RUN:
- Creates instance/ folder for SQLite database and config
- Seeds the cybersecurity curriculum (Tiers 0-4)
- Sets up default user: Shubham

FEATURES:
- 5-tier curriculum (Foundations to Capstone)
- 9 Job Role tracks (SOC Analyst, Penetration Tester, etc.)
- 62 Topics with prerequisite DAG
- 37 Offline Labs (PCAP, log analysis, crypto, malware, etc.)
- 7 Interactive in-browser exercises (Python, regex, cipher, etc.)
- AI Tutor (Ollama local LLM or rules-based fallback)
- XP, Streaks, Skill Radar progress tracking

LAB SETUP:
Run scripts/setup_kali_vm.ps1 to provision a local Kali VM for hands-on labs.
Bundled challenge files are in bundles/labs/

AI TUTOR:
Install Ollama locally: scripts/setup_ollama.ps1
Configure model at /offline/settings/ai-tutor

REQUIREMENTS:
- Windows 10/11 (64-bit)
- ~500 MB disk space for app + bundles
- 8 GB+ RAM recommended (for Ollama AI tutor)

SUPPORT:
Check /offline/about for offline mode details.
Check /offline/lab-setup for Kali VM setup guide.

"@
$readme | Out-File -FilePath (Join-Path $releasePath "README.txt") -Encoding utf8
Write-Ok "README created"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host " BUILD COMPLETE" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host " Executable: release\ZeroCipher.exe"
Write-Host " Bundles:    release\bundles\"
Write-Host " Scripts:    release\scripts\"
Write-Host " Launcher:   release\Start-ZeroCipher.bat"
Write-Host " README:     release\README.txt"
Write-Host ""
Write-Host " To run: Double-click ZeroCipher.exe or Start-ZeroCipher.bat"
Write-Host " The app creates its own instance/ folder on first run."
Write-Host "===================================================" -ForegroundColor Cyan