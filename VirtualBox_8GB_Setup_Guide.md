# Step-by-Step VirtualBox Lab Setup (Optimized for 8GB RAM)

This replaces the full-GOAD version of the lab with a version that actually runs on your hardware: one Kali VM, one Metasploitable2 VM, one single vulnerable Domain Controller (instead of full GOAD), and Wazuh built but used only in dedicated sessions. Follow in order.

---

## Step 0 — Prep Your Host Before Installing Anything

1. Close every unnecessary application on your host — browser tabs, background apps. You need as much of your 8GB free as possible.
2. Check virtualization is enabled: restart into BIOS/UEFI, confirm **Intel VT-x / AMD-V** is enabled (usually is by default; look under CPU or Advanced settings).
3. **If your host is Windows**: disable Hyper-V and Memory Integrity, since they conflict with VirtualBox and also eat RAM in the background.
   - Settings → **Windows Security → Device Security → Core Isolation** → turn OFF Memory Integrity.
   - Search "Turn Windows features on or off" → uncheck **Hyper-V** and **Virtual Machine Platform** if checked.
   - Reboot after this step — required for it to take effect.
4. Check free disk space: aim for at least 100GB free (this reduced lab needs far less than the full GOAD version, but Windows Server + Kali + Metasploitable2 disks still add up).

---

## Step 1 — Install VirtualBox

1. Download VirtualBox from virtualbox.org for your host OS.
2. Install it with default options.
3. Download the **matching-version** VirtualBox Extension Pack from the same page.
4. Open VirtualBox → **File → Tools → Extension Pack Manager** (or just double-click the downloaded `.vbox-extpack` file) → Install.

---

## Step 2 — Create the Isolated Internal Network

You'll attach this to every VM as a second adapter so they can talk to each other without touching your real network.

1. In VirtualBox: **Tools → Network Manager → Host-only Networks → Create.** Note the name it gives (e.g. `vboxnet0`) — you'll use a Host-only Adapter (not Internal Network) this time, because with only one or two VMs running at once, you'll actually want your **host machine** to reach into whichever VM is running (e.g., open the Wazuh dashboard from your host browser) rather than fully isolating VM-to-VM only.
2. You don't need to do anything else here yet — you'll attach each VM to this Host-only network as you create it below.

---

## Step 3 — Build Kali Linux (Lightweight)

1. Go to kali.org/get-kali → **Virtual Machines** → download the VirtualBox image. If a "Kali Everything" vs a smaller/Xfce variant is offered, pick the smaller one.
2. Import it: **File → Import Appliance**, select the downloaded file.
3. Before first boot, select the VM → **Settings**:
   - **System → Motherboard**: Base Memory = **2048 MB**.
   - **System → Processor**: 2 CPUs.
   - **Display**: reduce Video Memory to 16MB if it defaults higher (frees a little RAM).
   - **Network → Adapter 1**: NAT (keep enabled for now, for setup).
   - **Network → Adapter 2**: Enable, Attach to **Host-only Adapter**, select the network from Step 2.
4. Boot it. Default login `kali`/`kali` — change the password immediately: `passwd`.
5. Update: `sudo apt update && sudo apt full-upgrade -y` (this can take a while on first run — let it finish).
6. Install Docker: `sudo apt install docker.io -y && sudo systemctl enable --now docker`.
7. Pull the web-app images now, while NAT/internet is on:
   ```
   sudo docker pull vulnerables/web-dvwa
   sudo docker pull bkimminich/juice-shop
   ```
8. Shut down the VM, then **Settings → Network → Adapter 1 → disable** (you're done needing NAT for Kali's base setup — you'll re-enable briefly only when you need to pull a new tool later).
9. Boot back up, take a **Snapshot** (VirtualBox menu → **Machine → Take Snapshot**), name it `Kali - clean + docker ready`.

**Run DVWA/Juice Shop whenever you need them:**
```
sudo docker run -d --name dvwa -p 8081:80 vulnerables/web-dvwa
sudo docker run -d --name juiceshop -p 3000:3000 bkimminich/juice-shop
```
Access at `http://localhost:8081` and `http://localhost:3000` from Kali's own browser. DVWA login: `admin`/`password`, then set Security level to Low under "DVWA Security."

---

## Step 4 — Build Metasploitable2

1. Download the Metasploitable2 zip (search "Metasploitable2 download," it's hosted on SourceForge — comes with a `.vmdk` file inside).
2. Extract the zip.
3. In VirtualBox: **Machine → New**. Name: `Metasploitable2`. Type: Linux, Version: "Other Linux (64-bit)."
4. Memory: **768 MB**.
5. Hard disk: choose **"Use an existing virtual hard disk file"**, browse to the extracted `.vmdk`.
6. **Settings → Network → Adapter 1**: attach to **Host-only Adapter** (the Step 2 network) — this VM should never get a NAT/internet adapter at all, it's deliberately full of unpatched vulnerabilities.
7. Boot it. Login `msfadmin`/`msfadmin` — no further config needed.
8. Take a snapshot: `Metasploitable2 - stock`.

**Note on RAM budgeting:** Kali (2GB) + Metasploitable2 (768MB) run together comfortably within 8GB alongside your host OS. This is your "recon/exploitation day" pairing.

---

## Step 5 — Build the Single Vulnerable Domain Controller (Replaces Full GOAD)

This is the part that changes most from the original plan. Instead of 5 GOAD VMs, you build **one** Windows Server as a Domain Controller, using Server Core (no GUI) to save RAM, then run a script to inject the same vulnerable misconfigurations GOAD teaches against.

### 5a. Get Windows Server

1. Download the free Windows Server evaluation ISO from Microsoft's Evaluation Center (search "Windows Server evaluation download," current LTSC version — 180-day free trial, fine for a lab you'll periodically rebuild).
2. During download, if given a choice, pick the **Server Core** installation option later during setup (not "Desktop Experience") — this is the RAM-saving choice.

### 5b. Create the VM

1. **Machine → New**. Name: `DC01`. Type: Windows, Version: Windows Server 2022 (64-bit) or whatever version you downloaded.
2. Memory: **3072-4096 MB** (this is your biggest single VM — give it as much as you can spare while still leaving ~1.5-2GB for the host).
3. Processor: 2 CPUs.
4. Create a new virtual hard disk, dynamically allocated, at least 60GB.
5. **Settings → Storage**: attach the downloaded ISO to the virtual optical drive.
6. **Settings → Network → Adapter 1**: NAT (needed for initial setup/updates). **Adapter 2**: Host-only Adapter (Step 2's network).
7. Boot the VM, run through Windows Server setup, and **choose "Windows Server (Standard Evaluation) — Server Core"** at the installation-type screen. Set a strong local Administrator password when prompted.

### 5c. Promote It to a Domain Controller (No GUI — Use PowerShell)

Server Core boots to a command prompt. Type `powershell` to get a better shell, then:

```powershell
# Set a static internal IP for the Host-only adapter (adjust interface index/IP for your setup — check with Get-NetAdapter first)
New-NetIPAddress -InterfaceAlias "Ethernet 2" -IPAddress 192.168.56.10 -PrefixLength 24
Set-DnsClientServerAddress -InterfaceAlias "Ethernet 2" -ServerAddresses 127.0.0.1

# Rename the computer and reboot
Rename-Computer -NewName "DC01" -Restart
```
After reboot, log back in via `powershell` and install the AD Domain Services role, then promote:
```powershell
Install-WindowsFeature -Name AD-Domain-Services -IncludeManagementTools

Import-Module ADDSDeployment
Install-ADDSForest `
  -DomainName "purplelab.local" `
  -DomainNetbiosName "PURPLELAB" `
  -InstallDns:$true `
  -SafeModeAdministratorPassword (ConvertTo-SecureString "ChangeThisPassword123!" -AsPlainText -Force) `
  -Force:$true
```
The VM will reboot as a domain controller. This is a genuinely valuable exercise on its own — you're learning real AD administration, not just attacking someone else's pre-built lab.

### 5d. Add a Few Regular Domain Users (You Need Targets to Attack)

Once back in as an admin on the domain, still via PowerShell:
```powershell
New-ADUser -Name "svc_web" -SamAccountName "svc_web" -AccountPassword (ConvertTo-SecureString "P@ssw0rd123" -AsPlainText -Force) -Enabled $true -ServicePrincipalNames "HTTP/web01.purplelab.local"
New-ADUser -Name "jdoe" -SamAccountName "jdoe" -AccountPassword (ConvertTo-SecureString "Summer2024!" -AsPlainText -Force) -Enabled $true
```
`svc_web` with an SPN set is now Kerberoastable — this alone gets you a working Kerberoasting target without needing a second VM.

### 5e. Inject Additional Vulnerable Misconfigurations (Optional, While Online)

While the DC still has NAT enabled, you can pull down a vulnerable-AD-configuration script (search GitHub for "Vulnerable-AD" — WazeHell's project is a well-known one that scripts out AS-REP roastable accounts, weak ACLs, GPP passwords, and other common misconfigurations onto a fresh domain) and run it to get broader attack-surface coverage than the manual steps above, saving you from hand-crafting every misconfiguration yourself.

### 5f. Air-Gap and Snapshot

1. Once the domain is built and populated, go to **Settings → Network → Adapter 1 → disable** (remove NAT).
2. Take a snapshot immediately: `DC01 - domain built + vulnerable users`. This is the snapshot you'll restore to after every AD attack exercise.

---

## Step 6 — Install Sysmon on the DC (Your Blue-Team Visibility, No Extra VM Needed)

Do this while NAT is briefly re-enabled (or download it via a shared folder from your host — see Step 8 note below):

```powershell
# Download Sysmon and a solid default config first, then:
.\Sysmon64.exe -accepteula -i sysmonconfig-export.xml
```
Use the **SwiftOnSecurity sysmon-config** file (search GitHub for it) as your config — it's the standard beginner-friendly starting point.

**For now, skip a separate SIEM.** Read Sysmon/Security events directly:
```powershell
Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" -MaxEvents 20
```
Or, since you're on Server Core with no GUI, use **PowerShell remoting or RSAT from Kali/your host** to pull events remotely once you're comfortable, or temporarily install Windows Admin Center for a browser-based management view if a GUI-free workflow feels too limiting at first.

Re-disable NAT and snapshot again: `DC01 - Sysmon installed`.

---

## Step 7 — Build Wazuh (Build Now, Use Later — Dedicated Sessions Only)

Build this once, but understand you will **not** run it alongside Kali/Metasploitable/DC together — only pair it with the DC in a dedicated "detection day" session.

1. Download the Wazuh OVA (check documentation.wazuh.com's current install guide for the virtual-appliance download link).
2. **File → Import Appliance** in VirtualBox.
3. Memory: **4096 MB minimum** — this is Wazuh's stated floor for the all-in-one indexer+manager+dashboard stack; don't try to shrink it further or it may fail to start reliably.
4. **Settings → Network → Adapter 1**: NAT (briefly, for first-boot setup). **Adapter 2**: Host-only Adapter (Step 2's network).
5. Boot it. Note the dashboard URL and generated admin password printed on first boot.
6. From your host browser (thanks to the Host-only adapter), open the Wazuh dashboard URL and log in.
7. Use the "Add agent" wizard in the dashboard to generate an enrollment command, then run that command on the DC (which needs to be booted at the same time as Wazuh for this one-time enrollment step — this is the one moment you'll need both running simultaneously; do it, then you can go back to running them separately).
8. Confirm the DC shows as an "Active" agent in Wazuh.
9. Disable NAT on the Wazuh VM, snapshot: `Wazuh - DC enrolled`.

---