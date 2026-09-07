#Requires -Version 5.1
<#
    SkillSprint Academy - one-time online sync of the external resource cache
    (plan §6.2).

    Reads ../resource_catalog.json (shipped) listing public-domain / CC-licensed
    pages and PDFs, downloads each to ../instance/resource_cache/<sha256>.ext,
    and writes a CachedResource row into the DB via a small Python helper so
    the link_metadata_service serves cached metadata forever after.

    Re-running is safe: rows are upserted by original_url.
#>
[CmdletBinding()] param()

$ErrorActionPreference = "Stop"

function Write-Step($m)  { Write-Host "== $m" -ForegroundColor Cyan }
function Write-Ok($m)    { Write-Host "   ok: $m" -ForegroundColor Green }
function Write-Warn2($m) { Write-Host "   ! $m" -ForegroundColor Yellow }

$root = Resolve-Path (Join-Path $PSScriptRoot "..") | Select-Object -ExpandProperty Path
$catalog = Join-Path $root "resource_catalog.json"
$cacheDir = Join-Path $root "instance\resource_cache"
if (-not (Test-Path $cacheDir)) { New-Item -ItemType Directory $cacheDir | Out-Null }

if (-not (Test-Path $catalog)) {
    Write-Warn2 "$catalog not found - nothing to sync."
    exit 1
}

$items = Get-Content $catalog -Raw | ConvertFrom-Json
if (-not $items) { Write-Warn2 "catalog empty"; exit 1 }

Write-Step "Syncing $($items.Count) resources from catalog"

$cached = @()
foreach ($it in $items) {
    $url = $it.url
    if (-not $url) { continue }
    $title = $it.title
    $rtype = $it.resource_type
    $pages = $it.pages  # optional list of sub-pages

    $toFetch = @($url) + @($pages | Where-Object { $_ })
    foreach ($u in $toFetch) {
        $ext = if ($u -match '\.pdf$') { ".pdf" } else { ".html" }
        $sha = [System.Security.Cryptography.SHA256]::Create().ComputeHash(
                    [System.Text.Encoding]::UTF8.GetBytes($u))
        $shaHex = ($sha | ForEach-Object { $_.ToString("x2") }) -join ''
        $dest = Join-Path $cacheDir ($shaHex + $ext)
        if (Test-Path $dest) { Write-Ok "cached $u"; continue }
        try {
            Invoke-WebRequest -Uri $u -OutFile $dest -UseBasicParsing -TimeoutSec 15
            Write-Ok "fetched $u"
            $cached += [pscustomobject]@{
                url           = $u
                local_path    = (Resolve-Path $dest).Path
                title         = $title
                resource_type = $rtype
                fetched_at    = (Get-Date).ToString("o")
                content_hash  = $shaHex
            }
        } catch {
            Write-Warn2 "skip $u ($($_.Exception.Message))"
        }
    }
}

if ($cached.Count -eq 0) { Write-Ok "nothing new to sync"; return }

# ---------------------------------------------------------------------------
# Upsert CachedResource rows via a tiny inline Python helper
# ---------------------------------------------------------------------------
$py = @"
import json, sys
from app import app
from extensions import db
from models import CachedResource
from datetime import datetime

rows = json.loads(sys.stdin.read())
with app.app_context():
    for r in rows:
        existing = CachedResource.query.filter_by(original_url=r['url']).first()
        if existing:
            existing.local_path = r['local_path']
            existing.title = r['title']
            existing.resource_type = r['resource_type']
            existing.fetched_at = datetime.fromisoformat(r['fetched_at'])
            existing.content_hash = r['content_hash']
        else:
            db.session.add(CachedResource(
                original_url=r['url'], local_path=r['local_path'],
                title=r['title'], resource_type=r['resource_type'],
                fetched_at=datetime.fromisoformat(r['fetched_at']),
                content_hash=r['content_hash'],
            ))
    db.session.commit()
"@

Write-Step "Persisting $($cached.Count) CachedResource rows to DB"
$cached | ConvertTo-Json -Depth 4 | & py -3 -c $py
Write-Ok "cache DB rows updated"
