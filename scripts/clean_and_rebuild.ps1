#Requires -Version 5.1
<#
.SYNOPSIS
    Clean unwanted files and rebuild SkillSprintAcademy executable

.DESCRIPTION
    Performs cleanup of build artifacts, cache files, and optionally test files,
    then rebuilds the executable using the standard build script.

.USAGE
    pwsh scripts/clean_and_rebuild.ps1 [-IncludeTests] [-Force]

.PARAMETER IncludeTests
    Also delete test files in tests/ directory (default: keep tests)

.PARAMETER Force
    Skip confirmation prompts
#>

param(
    [switch]$IncludeTests,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..") | Select-Object -ExpandProperty Path
Set-Location $projectRoot

function Write-Step($msg)  { Write-Host "== $msg" -ForegroundColor Cyan }
function Write-Ok($msg)    { Write-Host "   ok: $msg" -ForegroundColor Green }
function Write-Warn($msg)  { Write-Host "   ! $msg" -ForegroundColor Yellow }
function Write-Info($msg)  { Write-Host "   $msg" -ForegroundColor Gray }

# ---------------------------------------------------------------------------
# Confirmation
# ---------------------------------------------------------------------------
if (-not $Force) {
    $msg = "This will delete:"
    $msg += "`n  - All __pycache__ directories and .pyc files"
    $msg += "`n  - build/ and dist/ directories"
    $msg += "`n  - release/SkillSprintAcademy.exe (will be rebuilt)"
    if ($IncludeTests) { $msg += "`n  - tests/ directory" }
    $msg += "`n`nContinue?"
    $confirm = Read-Host -Prompt "$msg (y/N)"
    if ($confirm -notmatch '^y') { Write-Host "Aborted." -ForegroundColor Red; exit 1 }
}

# ---------------------------------------------------------------------------
# Clean unwanted files
# ---------------------------------------------------------------------------
Write-Step "Cleaning unwanted files..."

# 1. Python cache
Write-Info "Removing __pycache__ directories..."
Get-ChildItem -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
    ForEach-Object { Remove-Item $_.FullName -Recurse -Force; Write-Info "  Deleted $($_.FullName)" }

Write-Info "Removing .pyc/.pyo files..."
Get-ChildItem -Recurse -File -Filter "*.pyc" -ErrorAction SilentlyContinue | Remove-Item -Force
Get-ChildItem -Recurse -File -Filter "*.pyo" -ErrorAction SilentlyContinue | Remove-Item -Force

# 2. Build artifacts
$dirsToClean = @("build", "dist")
foreach ($dir in $dirsToClean) {
    $path = Join-Path $projectRoot $dir
    if (Test-Path $path) {
        Remove-Item $path -Recurse -Force
        Write-Ok "Removed $dir/"
    }
}

# 3. Old executable in release
$oldExe = Join-Path $projectRoot "release\SkillSprintAcademy.exe"
if (Test-Path $oldExe) {
    Remove-Item $oldExe -Force
    Write-Ok "Removed old release/SkillSprintAcademy.exe"
}

# 4. Optional: test files
if ($IncludeTests) {
    $testsDir = Join-Path $projectRoot "tests"
    if (Test-Path $testsDir) {
        Remove-Item $testsDir -Recurse -Force
        Write-Ok "Removed tests/ directory"
    }
}

# 5. Other common cleanup
$otherPatterns = @(
    "*.log",
    "*.tmp",
    "*.temp",
    ".coverage",
    "htmlcov/",
    ".pytest_cache/",
    "*.egg-info/"
)
foreach ($pattern in $otherPatterns) {
    Get-ChildItem -Recurse -Filter $pattern -ErrorAction SilentlyContinue |
        Where-Object { -not $_.FullName.Contains("\.git\") } |
        ForEach-Object { Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue }
}

Write-Ok "Cleanup complete"

# ---------------------------------------------------------------------------
# Rebuild executable
# ---------------------------------------------------------------------------
Write-Step "Rebuilding executable..."
& "$PSScriptRoot\build_exe.ps1"

# ---------------------------------------------------------------------------
# Verify new executable
# ---------------------------------------------------------------------------
$newExe = Join-Path $projectRoot "release\SkillSprintAcademy\SkillSprintAcademy.exe"
if (Test-Path $newExe) {
    $size = (Get-Item $newExe).Length / 1MB
    Write-Ok "New executable created: release\SkillSprintAcademy\SkillSprintAcademy.exe ($([math]::Round($size, 1)) MB)"
} else {
    Write-Error "Build failed - executable not found at $newExe"
    exit 1
}

Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host " CLEANUP AND REBUILD COMPLETE" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host " New executable: release\SkillSprintAcademy\SkillSprintAcademy.exe"
Write-Host "===================================================" -ForegroundColor Cyan