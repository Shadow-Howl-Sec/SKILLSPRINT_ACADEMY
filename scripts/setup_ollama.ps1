#Requires -Version 5.1
<#
    SkillSprint Academy - Ollama setup (plan §7, §10.4).

    Detects Ollama on PATH (or via OllamaSetup.exe in bundles\installers);
    if absent, prints a download link / pulls the bundled installer. Then
    runs `ollama pull <model>` once (online) for the recommended model.

    After this, the AI tutor uses the locally-pulled model forever.
#>
[CmdletBinding()] param(
    [ValidateSet("auto","phi3:mini","llama3.1:8b-instruct","mistral:7b-instruct","qwen2.5-coder:7b")]
    [string]$Model = "auto",

    [int]$TotalRamGB = -1   # -1 = autodetect
)

$ErrorActionPreference = "Stop"

function Write-Step($m)  { Write-Host "== $m"   -ForegroundColor Cyan }
function Write-Ok($m)    { Write-Host "   ok: $m" -ForegroundColor Green }
function Write-Warn2($m) { Write-Host "   ! $m" -ForegroundColor Yellow }

# ---------------------------------------------------------------------------
# Resolve Ollama on PATH
# ---------------------------------------------------------------------------
$ollama = (Get-Command ollama.exe -ErrorAction SilentlyContinue).Source
if (-not $ollama) {
    $cand = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
    if (Test-Path $cand) { $ollama = $cand }
}
if (-not $ollama) {
    $bundled = Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..\bundles\installers")) "OllamaSetup.exe"
    if (Test-Path $bundled) {
        Write-Step "Running bundled OllamaSetup.exe"
        Start-Process -Wait $bundled
        $ollama = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
    }
}
if (-not $ollama) {
    Write-Warn2 "Ollama not installed."
    Write-Warn2 "Download from https://ollama.com/download (one-time online),"
    Write-Warn2 "or place OllamaSetup.exe in bundles\installers\ and re-run this script."
    exit 1
}
Write-Ok "ollama at $ollama"

# Add to PATH for the current user so app detection (which probes PATH first)
# picks it up after install.
$env:Path = "$env:LOCALAPPDATA\Programs\Ollama;" + $env:Path

# ---------------------------------------------------------------------------
# Pick model by RAM if requested
# ---------------------------------------------------------------------------
if ($Model -eq "auto") {
    if ($TotalRamGB -lt 0) {
        try { $TotalRamGB = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB } catch { $TotalRamGB = 16 }
    }
    if     ($TotalRamGB -ge 16) { $Model = "llama3.1:8b-instruct" }
    elseif ($TotalRamGB -ge 12) { $Model = "qwen2.5-coder:7b" }
    else                        { $Model = "phi3:mini" }
    Write-Ok "auto-selected $Model (RAM ~$([math]::Round($TotalRamGB,1))GB)"
}

# ---------------------------------------------------------------------------
# Start Ollama daemon (if not running) + pull model
# ---------------------------------------------------------------------------
Write-Step "Ensuring ollama daemon is running"
$jobs = Get-Process -Name ollama* -ErrorAction SilentlyContinue
if (-not $jobs) {
    Start-Process $ollama "serve"
    Start-Sleep -Seconds 3
}

Write-Step "Pulling model $Model (one-time, online) - this can take several minutes"
& $ollama pull $Model
Write-Ok "model pulled"

# Persist the choice so the launcher/tutor picks it up.
$overrideFile = Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..")) "instance\ollama_model.txt"
$dir = Split-Path $overrideFile -Parent
if (-not (Test-Path $dir)) { New-Item -ItemType Directory $dir | Out-Null }
$Model | Set-Content -Path $overrideFile -Encoding utf8 -NoNewline
Write-Ok "OLLAMA_MODEL=$Model persisted to instance\ollama_model.txt"

# Make sure .env carries OLLAMA_MODEL too (separately maintained)
$envFile = Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..")) ".env"
if (Test-Path $envFile) {
    $c = Get-Content -Raw $envFile
    if ($c -notmatch '(?m)^\s*OLLAMA_MODEL\s*=') {
        Add-Content $envFile "OLLAMA_MODEL=$Model"
    } else {
        ($c -replace '(?m)^\s*OLLAMA_MODEL\s*=.*$', "OLLAMA_MODEL=$Model") |
            Set-Content $envFile -Encoding utf8 -NoNewline
    }
}

Write-Host ""
Write-Host "AI tutor will now use $Model. To verify inside the app, open:" -ForegroundColor Cyan
Write-Host "  http://127.0.0.1:5000/offline/settings/ai-tutor?test=1"       -ForegroundColor Cyan
