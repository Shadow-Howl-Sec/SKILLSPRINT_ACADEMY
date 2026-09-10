#Requires -Version 5.1
<#
.SYNOPSIS
    Build SkillSprintAcademy as a standalone Windows executable (.exe)

.DESCRIPTION
    Uses PyInstaller with a .spec file to create an onedir executable and a
    separate updater executable that includes:
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
    Output: release/SkillSprintAcademy.exe
    The exe will create its own instance/ folder on first run for database and configs.
#>

$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..") | Select-Object -ExpandProperty Path
$distPath    = Join-Path $projectRoot "dist"
$buildPath   = Join-Path $projectRoot "build"
$releasePath = Join-Path $projectRoot "release"
$specFile    = Join-Path $projectRoot "build_exe.spec"

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
# Build the main application using the .spec file
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
# Build the external updater
# ---------------------------------------------------------------------------
Write-Step "Building updater executable..."
$updaterBuildPath = Join-Path $buildPath "updater"
$updaterDistPath  = Join-Path $distPath "updater"
& py -3 -m PyInstaller --clean --noconfirm --onefile --name updater `
    --distpath="$updaterDistPath" --workpath="$updaterBuildPath" `
    --hidden-import="cryptography.hazmat.primitives.asymmetric.ed25519" `
    (Join-Path $projectRoot "updater.py")

if ($LASTEXITCODE -ne 0) {
    Write-Error "Updater build failed with exit code $LASTEXITCODE"
    exit 1
}

Write-Ok "Updater build completed"

# ---------------------------------------------------------------------------
# Copy additional files to release folder
# ---------------------------------------------------------------------------
Write-Step "Preparing release folder..."
# Clean and recreate release folder
if (Test-Path $releasePath) { Remove-Item $releasePath -Recurse -Force }
New-Item -ItemType Directory $releasePath | Out-Null

# Copy entire onedir output (folder containing exe + dependencies)
$onedirSrc = Join-Path $distPath "SkillSprintAcademy"
$onedirDst = Join-Path $releasePath "SkillSprintAcademy"
if (Test-Path $onedirSrc) {
    Copy-Item $onedirSrc $onedirDst -Recurse -Force
    Write-Ok "Onedir build copied to release/SkillSprintAcademy/"
} else {
    Write-Error "Onedir build not found at $onedirSrc"
    exit 1
}

$updaterSrc = Join-Path $updaterDistPath "updater.exe"
$updaterDst = Join-Path $releasePath "updater.exe"
if (Test-Path $updaterSrc) {
    Copy-Item $updaterSrc $updaterDst -Force
    Write-Ok "Updater executable copied to release/updater.exe"
} else {
    Write-Error "Updater executable not found at $updaterSrc"
    exit 1
}

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
set "UPDATER_DIR=%LOCALAPPDATA%\SkillSprintAcademy"
if not exist "%UPDATER_DIR%" mkdir "%UPDATER_DIR%"
copy /Y "%~dp0updater.exe" "%UPDATER_DIR%\updater.exe" >nul
echo Starting SkillSprintAcademy...
echo The app will open at http://127.0.0.1:52837
echo Press Ctrl+C to stop the server
echo.
cd /d "%~dp0SkillSprintAcademy"
SkillSprintAcademy.exe
pause
"@
$launcherBat | Out-File -FilePath (Join-Path $releasePath "Start-SkillSprintAcademy.bat") -Encoding ascii
Write-Ok "Launcher batch file created"

# Create README for release
$readme = @"
SkillSprintAcademy - Offline Cybersecurity Learning Platform
=============================================================

Single-user, fully offline cybersecurity training application.
Runs on Windows 10/11 with no internet required after first run.

QUICK START:
1. Double-click SkillSprintAcademy.exe
   OR
2. Double-click Start-SkillSprintAcademy.bat

The launcher installs the signed-update helper to
%LOCALAPPDATA%\SkillSprintAcademy before starting the app.

The app will start a local web server at http://127.0.0.1:52837
and open it in your default browser.

INSTALLER:
- Run SkillSprintAcademy-Setup.exe to register the app in Windows Installed apps.
- The installer creates Start Menu and optional desktop shortcuts.

FIRST RUN:
- Creates instance/ folder for SQLite database and config
- Seeds the 2-stage purple team curriculum (Stage 1: Months 1-3, Stage 2: Ongoing)
- Sets up default user: operator

FEATURES:
- Two-stage Purple Team roadmap (Job-Ready + Mastery)
- 10 Job Role tracks (Purple Team Specialist is default)
- ~68 Topics with prerequisite DAG
- ~70 offline vm_exercise labs (attack + detection per topic)
- 7 Interactive in-browser exercises (Python, regex, cipher, etc.)
- AI Tutor (Ollama local LLM or rules-based fallback)
- XP, Streaks, Skill Radar progress tracking
- ATT&CK Matrix coverage map
- Purple Team exercise log & Markdown portfolio export

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

# Build a per-user installer when Inno Setup is installed.
$iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if ($null -ne $iscc) {
    Write-Step "Building Windows installer..."
    $appVersion = (Get-Content (Join-Path $projectRoot "VERSION") -Raw).Trim()
    & $iscc.Source "/DMyAppVersion=$appVersion" (Join-Path $projectRoot "installer.iss")
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Inno Setup build failed with exit code $LASTEXITCODE"
        exit 1
    }
    Write-Ok "Installer created in release/"
} else {
    Write-Warn "ISCC.exe not found; portable release created without an installer"
    Write-Warn "Install Inno Setup and rerun this script to create SkillSprintAcademy-Setup.exe"
}

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host " BUILD COMPLETE" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host " Onedir build: release\SkillSprintAcademy\"
Write-Host " Updater:      release\updater.exe"
Write-Host " Bundles:      release\bundles\"
Write-Host " Scripts:      release\scripts\"
Write-Host " Launcher:     release\Start-SkillSprintAcademy.bat"
Write-Host " README:       release\README.txt"
if ($null -ne $iscc) { Write-Host " Installer:    release\SkillSprintAcademy-Setup.exe" }
Write-Host ""
Write-Host " To run: Double-click Start-SkillSprintAcademy.bat"
Write-Host "         Or run: release\SkillSprintAcademy\SkillSprintAcademy.exe"
Write-Host " The app creates its own instance/ folder on first run."
Write-Host "===================================================" -ForegroundColor Cyan