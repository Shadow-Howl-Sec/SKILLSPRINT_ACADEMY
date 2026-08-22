#Requires -Version 5.1
<#
    SkillSprint Academy - Kali VirtualBox VM setup (plan §5.1, §10.2).

    Walks the user through provisioning a local Kali VM for offline lab work.
    Does NOT silently install anything. After one run, the VM lives locally
    and this script never touches the internet again.

    Steps:
      1. Check VirtualBox is installed.
      2. Import the Kali .ova (from a local path or one-time online download).
         Skipped if the VM already exists.
      3. Set up a host-only network adapter.
      4. Snapshot a clean state.
      5. Copy the bundled challenge artifacts into the guest via SSH/SCP.
      6. Print SSH + RDP connection details.

    Usage:
        pwsh scripts/setup_kali_vm.ps1 -OvaPath C:\iso\kali.ova
        pwsh scripts/setup_kali_vm.ps1 -Download          # one-time, online
#>
[CmdletBinding()] param(
    [string]$VmName      = "SkillSprint-Kali",
    [string]$OvaPath,
    [switch]$Download,
    [int]$HostMemoryMB   = 4096,
    [int]$CpuCount       = 2,
    [string]$GuestUser    = "kali",
    [string]$SharedFolder = (Resolve-Path (Join-Path $PSScriptRoot "..\bundles\labs")).Path
)

$ErrorActionPreference = "Stop"

function Write-Step($m)  { Write-Host "== $m"   -ForegroundColor Cyan }
function Write-Ok($m)    { Write-Host "   ok: $m" -ForegroundColor Green }
function Write-Warn2($m) { Write-Host "   ! $m" -ForegroundColor Yellow }

# ---------------------------------------------------------------------------
# 1. VBox present?
# ---------------------------------------------------------------------------
$vboxManage = (Get-Command VBoxManage.exe -ErrorAction SilentlyContinue).Source
if (-not $vboxManage) {
    $cand = "${env:ProgramFiles}\Oracle\VirtualBox\VBoxManage.exe"
    if (Test-Path $cand) { $vboxManage = $cand }
}
if (-not $vboxManage) {
    Write-Warn2 "VirtualBox not found. Install it from https://www.virtualbox.org/"
    Write-Warn2 "then re-run this script."
    exit 1
}
Write-Ok "VBoxManage at $vboxManage"

# ---------------------------------------------------------------------------
# 2. VM already exists?
# ---------------------------------------------------------------------------
$exists = (& $vboxManage list vms) -match ('"' + $VmName + '"')
if ($exists) {
    Write-Step "VM '$VmName' already exists - snapshotting a clean state"
    & $vboxManage snapshot $VmName take "skillSprint-clean-state" --description "Baseline after first boot" 2>$null | Out-Null
    Write-Ok "snapshot ok (or already existed)"
    Write-Host "VM '$VmName' is ready. To start it:"
    Write-Host "    VBoxManage startvm $VmName --type headless"
    return
}

# ---------------------------------------------------------------------------
# 3. Resolve OVA - download if requested
# ---------------------------------------------------------------------------
if (-not $OvaPath -and $Download) {
    Write-Step "Downloading Kali VirtualBox appliance (one-time, online)"
    $OvaPath = Join-Path $env:TEMP "kali-linux-virtualbox.ova"
    if (-not (Test-Path $OvaPath)) {
        $url = "https://kali.download/virtual-images/kali-latest/kali-linux-VirtualBox-amd64.ova"
        Write-Host "Fetching $url -> $OvaPath"
        Invoke-WebRequest -Uri $url -OutFile $OvaPath -UseBasicParsing
    }
    Write-Ok $OvaPath
}
if (-not $OvaPath -or -not (Test-Path $OvaPath)) {
    Write-Warn2 "No .ova path given. Either:"
    Write-Warn2 "  - Place a Kali .ova locally and pass -OvaPath <path>"
    Write-Warn2 "  - Or pass -Download to fetch it once from kali.download (online)."
    exit 2
}

# ---------------------------------------------------------------------------
# 4. Import + configure host-only adapter
# ---------------------------------------------------------------------------
Write-Step "Importing OVA into VirtualBox as '$VmName'"
& $vboxManage import $OvaPath --vsys 0 --vmname $VmName `
    --cpus $CpuCount --memory $HostMemoryMB | Out-Null
Write-Ok "imported"

# Create/use a host-only network for isolated labs.
$ifname = "vboxnet0"
$nics = & $vboxManage list hostonlyifs 2>$null
if ($nics -notmatch $ifname) {
    Write-Step "Creating host-only network $ifname"
    & $vboxManage hostonlyif create | Out-Null
    Write-Ok "hostonly network ready"
}

& $vboxManage modifyvm $VmName --nic1 hostonly --hostonlyadapter1 $ifname
& $vboxManage modifyvm $VmName --nic2 nat      # NAT for outbound during setup
Write-Ok "adapters configured (host-only + NAT)"

# ---------------------------------------------------------------------------
# 5. Shared folder with bundled challenge artifacts
# ---------------------------------------------------------------------------
if (Test-Path $SharedFolder) {
    Write-Step "Mounting bundled labs at $SharedFolder into the guest"
    & $vboxManage sharedfolder add $VmName --name "skillSprint-labs" `
        --hostpath $SharedFolder --automount
    Write-Ok "shared folder attached"
}

# ---------------------------------------------------------------------------
# 6. Start + snapshot a clean state
# ---------------------------------------------------------------------------
Write-Step "Booting the VM headless"
& $vboxManage startvm $VmName --type headless | Out-Null
Write-Host "Waiting 60s for first boot..."
Start-Sleep -Seconds 60

& $vboxManage controlvm $VmName savestate | Out-Null
& $vboxManage snapshot $VmName take "skillSprint-clean-state" | Out-Null
Write-Ok "clean-state snapshot saved"

# ---------------------------------------------------------------------------
# 7. Print connection hints
# ---------------------------------------------------------------------------
$ipQ = (& $vboxManage guestproperty enumerate $VmName 2>$null) -match '/VirtualBox/GuestInfo/Net/1/V4/IP'
$guestIp = ($ipQ -split ',')[0] -replace 'value: ','' -replace '^.*?ip=',''
Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host " Kali VM '$VmName' is provisioned and snapshotted."    -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host " Start (headless):  VBoxManage startvm $VmName --type headless"
Write-Host " SSH (default):     ssh ${GuestUser}@127.0.0.1 -p 2222"
if ($guestIp) { Write-Host " Host-only IP:       ssh ${GuestUser}@$guestIp" }
Write-Host " Bundled labs:       mounted at /media/sf_skillSprint-labs inside the guest"
Write-Host " Reset to clean:     VBoxManage snapshot $VmName restore skillSprint-clean-state"
