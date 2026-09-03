"""Free, high-quality learning paths for every ZeroCipher topic.

Each topic gets five ContentItem tracks:
  Theory        — books, RFCs, official docs
  Video         — free lecture series
  Labs          — extra Lab rows (free CTFs / local setups)
  Automation    — Python-for-security modules
  Soft Skills   — professional practice for the industry

All URLs are free (no paid academy walls). Offline copies can be
cached later via scripts/sync_resource_cache.ps1.
"""
from __future__ import annotations

import json

from extensions import db
from models import ContentItem, Lab, SkillArea, Topic
from seed import get_or_create, slugify


# ---------------------------------------------------------------------------
# Shared soft-skill modules reused across topics
# ---------------------------------------------------------------------------
SOFT = {
    "notes": (
        "Soft Skills — Technical Note-Taking",
        "Keep a dated lab journal: command, expected vs actual, artifact path. "
        "Use the Cornell method. Resource: https://www.nist.gov/cyberframework",
        20,
    ),
    "writeup": (
        "Soft Skills — Professional Write-up",
        "Write a 1-page finding: summary, impact, evidence, remediation. "
        "Model: https://owasp.org/www-project-web-security-testing-guide/",
        25,
    ),
    "comms": (
        "Soft Skills — Incident Communication",
        "Draft a 5-sentence stakeholder update: what, who, impact, next step, ETA. "
        "Guide: https://www.cisa.gov/resources-tools/resources/cybersecurity-incident-and-vulnerability-response-playbooks",
        20,
    ),
    "ethics": (
        "Soft Skills — Authorization & Ethics",
        "Never test without written scope. Review: https://www.sans.org/mlp/ethics-in-cybersecurity/",
        15,
    ),
    "interview": (
        "Soft Skills — Interview Story (STAR)",
        "Turn this lab into a STAR story: Situation, Task, Action, Result with metrics. "
        "NICE framework: https://www.nist.gov/itl/applied-cybersecurity/nice",
        20,
    ),
    "portfolio": (
        "Soft Skills — Portfolio Artifact",
        "Export this exercise to your ZeroCipher portfolio (ATT&CK coverage + write-up). "
        "Public examples: https://github.com/swisskyrepo/PayloadsAllTheThings",
        20,
    ),
}


def _path(theory, video, auto, soft_key, extra_labs=None):
    return {
        "theory": theory,   # (title, url, minutes)
        "video": video,
        "automation": auto,
        "soft": SOFT[soft_key],
        "labs": extra_labs or [],  # list of Lab tuples
    }


# (title, url, minutes)
PATHS = {
    "Binary, Hex & Number Systems": _path(
        ("Theory — Computer Systems: A Programmer's Perspective notes",
         "https://csapp.cs.cmu.edu/", 45),
        ("Video — CS50 Binary & Hex (Harvard, free)",
         "https://cs50.harvard.edu/x/weeks/0/", 50),
        ("Automation — Python int/hex/bytes conversions",
         "https://docs.python.org/3/library/stdtypes.html#int.to_bytes", 30),
        "notes",
    ),
    "Files & OS Concepts": _path(
        ("Theory — Operating Systems: Three Easy Pieces (free book)",
         "https://pages.cs.wisc.edu/~remzi/OSTEP/", 90),
        ("Video — MIT 6.828 OS Intro (OCW)",
         "https://ocw.mit.edu/courses/6-828-operating-system-engineering-fall-2012/", 60),
        ("Automation — Python os/pathlib file metadata",
         "https://docs.python.org/3/library/pathlib.html", 30),
        "notes",
    ),
    "Networking Basics": _path(
        ("Theory — Cisco Networking Basics (Skills for All, free)",
         "https://www.netacad.com/courses/networking-basics", 90),
        ("Video — Professor Messer Network+ N10-009 (free)",
         "https://www.professormesser.com/network-plus/n10-009/n10-009-video/n10-009-training-course/", 120),
        ("Automation — Python socket TCP handshake demo",
         "https://docs.python.org/3/library/socket.html", 40),
        "notes",
        extra_labs=[
            ("Cisco Packet Tracer: 3-router lab (free)", "Networking Basics",
             "other", "https://www.netacad.com/courses/packet-tracer",
             "self_report", 1, 45, 20, None),
        ],
    ),
    "Linux Fundamentals": _path(
        ("Theory — The Linux Command Line (Shotts, free PDF)",
         "https://linuxcommand.org/tlcl.php", 90),
        ("Video — NetworkChuck Linux for Hackers (free playlist)",
         "https://www.youtube.com/playlist?list=PLIhvC56v63IJVXv0GJcl9vO5Z6znCVb1P", 80),
        ("Automation — Python subprocess for sysadmin tasks",
         "https://docs.python.org/3/library/subprocess.html", 35),
        "notes",
        extra_labs=[
            ("OverTheWire Bandit 0–10", "Linux Fundamentals",
             "overthewire", "https://overthewire.org/wargames/bandit/",
             "flag", 1, 90, 30, "T1059"),
        ],
    ),
    "Windows Fundamentals": _path(
        ("Theory — Microsoft Learn: Windows internals for IT",
         "https://learn.microsoft.com/en-us/windows/win32/sysinfo/operating-system-information", 60),
        ("Video — John Hammond Windows for Hackers (free)",
         "https://www.youtube.com/results?search_query=john+hammond+windows+fundamentals", 60),
        ("Automation — PowerShell + Python winreg inventory",
         "https://docs.python.org/3/library/winreg.html", 40),
        "notes",
    ),
    "Security Mindset & Ethics": _path(
        ("Theory — NIST SP 800-181 NICE Framework",
         "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-181r1.pdf", 45),
        ("Video — DEF CON Talk: Ethics of Offensive Security (free)",
         "https://www.youtube.com/results?search_query=defcon+ethics+offensive+security", 40),
        ("Automation — Python scope-checker (CIDR allowlist)",
         "https://docs.python.org/3/library/ipaddress.html", 25),
        "ethics",
    ),
    "CIA Triad & Threat Models": _path(
        ("Theory — NIST SP 800-30 Risk Assessment",
         "https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-30r1.pdf", 50),
        ("Video — STRIDE threat modeling (Microsoft, free)",
         "https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-getting-started", 40),
        ("Automation — Python STRIDE checklist generator",
         "https://owasp.org/www-community/Threat_Modeling", 30),
        "writeup",
    ),
    "MITRE ATT&CK Overview": _path(
        ("Theory — MITRE ATT&CK Enterprise Matrix (official)",
         "https://attack.mitre.org/", 60),
        ("Video — MITRE ATT&CK for Practitioners (free)",
         "https://www.youtube.com/c/MITREATTCK", 45),
        ("Automation — Python attackcti / ATT&CK JSON parser",
         "https://github.com/mitre/cti", 40),
        "portfolio",
    ),
    "TCP/IP & Subnetting": _path(
        ("Theory — RFC 791 + RFC 793 (IP/TCP)",
         "https://www.rfc-editor.org/rfc/rfc791", 70),
        ("Video — Practical Networking subnetting (free)",
         "https://www.practicalnetworking.net/stand-alone/ip-subnetting/", 60),
        ("Automation — Python ipaddress subnet calculator",
         "https://docs.python.org/3/library/ipaddress.html", 35),
        "notes",
        extra_labs=[
            ("Cisco NetAcad: Intro to Packet Tracer", "TCP/IP & Subnetting",
             "other", "https://www.netacad.com/courses/intro-packet-tracer",
             "self_report", 1, 40, 20, None),
        ],
    ),
    "DNS & HTTP": _path(
        ("Theory — RFC 1035 DNS + MDN HTTP",
         "https://developer.mozilla.org/en-US/docs/Web/HTTP", 60),
        ("Video — Computerphile DNS (free)",
         "https://www.youtube.com/watch?v=mpQZVYPuD-Q", 20),
        ("Automation — Python dnspython + requests recon",
         "https://dnspython.readthedocs.io/", 40),
        "notes",
    ),
    "Packet Analysis & Wireshark": _path(
        ("Theory — Wireshark Official User's Guide (free)",
         "https://www.wireshark.org/docs/wsug_html_chunked/", 70),
        ("Video — Chris Greer Wireshark University (free)",
         "https://www.youtube.com/@ChrisGreer", 80),
        ("Automation — Python scapy PCAP parser",
         "https://scapy.readthedocs.io/en/latest/", 50),
        "writeup",
        extra_labs=[
            ("Wireshark sample captures (official)", "Packet Analysis & Wireshark",
             "other", "https://wiki.wireshark.org/SampleCaptures",
             "self_report", 2, 45, 25, "T1040"),
        ],
    ),
    "Firewalls & Network Hardening": _path(
        ("Theory — NIST SP 800-41 Firewall Guidelines",
         "https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-41r1.pdf", 50),
        ("Video — Professor Messer firewalls (Network+)",
         "https://www.professormesser.com/network-plus/n10-009/n10-009-video/n10-009-training-course/", 40),
        ("Automation — Python nftables/iptables rule auditor",
         "https://docs.python.org/3/library/subprocess.html", 40),
        "comms",
    ),
    "Linux Filesystem & Permissions": _path(
        ("Theory — POSIX permissions + capabilities man pages",
         "https://man7.org/linux/man-pages/man7/inode.7.html", 40),
        ("Video — LiveOverflow Linux privs (free)",
         "https://www.youtube.com/@LiveOverflow", 40),
        ("Automation — Python os.stat permission auditor",
         "https://docs.python.org/3/library/stat.html", 30),
        "notes",
    ),
    "Bash & Scripting Fundamentals": _path(
        ("Theory — GNU Bash Reference Manual",
         "https://www.gnu.org/software/bash/manual/bash.html", 60),
        ("Video — NetworkChuck Bash in 1 hour (free)",
         "https://www.youtube.com/results?search_query=networkchuck+bash+scripting", 55),
        ("Automation — Convert bash one-liners to Python",
         "https://docs.python.org/3/library/shutil.html", 35),
        "notes",
    ),
    "Processes & Services": _path(
        ("Theory — systemd documentation (freedesktop)",
         "https://www.freedesktop.org/software/systemd/man/latest/", 45),
        ("Video — Linux systemd crash course (free)",
         "https://www.youtube.com/results?search_query=systemd+crash+course", 35),
        ("Automation — Python psutil process inventory",
         "https://psutil.readthedocs.io/", 30),
        "notes",
    ),
    "Log Analysis & journald": _path(
        ("Theory — journalctl + syslog RFC 5424",
         "https://www.rfc-editor.org/rfc/rfc5424", 40),
        ("Video — Linux log analysis for SOC (free)",
         "https://www.youtube.com/results?search_query=linux+log+analysis+soc", 40),
        ("Automation — Python parse auth.log / journal JSON",
         "https://docs.python.org/3/library/re.html", 45),
        "writeup",
    ),
    "Web App Basics & HTTP": _path(
        ("Theory — MDN HTTP + OWASP Web Security Testing Guide",
         "https://owasp.org/www-project-web-security-testing-guide/", 70),
        ("Video — PortSwigger Academy HTTP (free)",
         "https://portswigger.net/web-security", 50),
        ("Automation — Python requests session mapper",
         "https://requests.readthedocs.io/", 40),
        "writeup",
    ),
    "OWASP Top 10 Overview": _path(
        ("Theory — OWASP Top 10:2021 (official)",
         "https://owasp.org/Top10/", 50),
        ("Video — OWASP Top 10 explained (free)",
         "https://www.youtube.com/results?search_query=owasp+top+10+2021+explained", 45),
        ("Automation — Python checklist against Top 10",
         "https://owasp.org/www-project-application-security-verification-standard/", 30),
        "interview",
    ),
    "SQL Injection": _path(
        ("Theory — PortSwigger SQLi topic (free labs)",
         "https://portswigger.net/web-security/sql-injection", 70),
        ("Video — LiveOverflow SQLi series (free)",
         "https://www.youtube.com/results?search_query=liveoverflow+sql+injection", 50),
        ("Automation — Python parameterized queries vs payload fuzzer",
         "https://docs.python.org/3/library/sqlite3.html", 40),
        "writeup",
        extra_labs=[
            ("PortSwigger SQLi Apprentice labs", "SQL Injection",
             "portswigger", "https://portswigger.net/web-security/sql-injection",
             "self_report", 2, 60, 30, "T1190"),
        ],
    ),
    "Cross-Site Scripting (XSS)": _path(
        ("Theory — PortSwigger XSS + OWASP XSS Filter Evasion",
         "https://portswigger.net/web-security/cross-site-scripting", 60),
        ("Video — STÖK XSS for beginners (free)",
         "https://www.youtube.com/results?search_query=stok+xss+beginners", 40),
        ("Automation — Python HTML escape vs payload tester",
         "https://docs.python.org/3/library/html.html", 30),
        "writeup",
    ),
    "Burp Suite Essentials": _path(
        ("Theory — Burp Suite Community docs (free edition)",
         "https://portswigger.net/burp/documentation/desktop", 50),
        ("Video — PortSwigger Getting Started with Burp (free)",
         "https://portswigger.net/burp/documentation/desktop/getting-started", 40),
        ("Automation — Python + Burp extender / httpx replay",
         "https://portswigger.net/burp/extender", 40),
        "notes",
    ),
    "Authentication & Session Attacks": _path(
        ("Theory — OWASP Authentication Cheat Sheet",
         "https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html", 45),
        ("Video — PortSwigger Authentication labs walkthrough (free)",
         "https://portswigger.net/web-security/authentication", 50),
        ("Automation — Python JWT decode + cookie jar audit",
         "https://pyjwt.readthedocs.io/", 40),
        "ethics",
    ),
    "Cryptographic Foundations": _path(
        ("Theory — Crypto I (Coursera audit / Boneh notes, free)",
         "https://crypto.stanford.edu/~dabo/cryptobook/", 80),
        ("Video — Computerphile crypto playlist (free)",
         "https://www.youtube.com/playlist?list=PLzH6n4zXuckpKAj1_88VS_4nmf4uJ-SpE", 60),
        ("Automation — Python hashlib / secrets usage",
         "https://docs.python.org/3/library/hashlib.html", 35),
        "notes",
    ),
    "Hashing & Salting": _path(
        ("Theory — OWASP Password Storage Cheat Sheet",
         "https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html", 40),
        ("Video — Computerphile Hashing (free)",
         "https://www.youtube.com/watch?v=b4b8ktEV4Bg", 20),
        ("Automation — Python bcrypt/argon2 vs unsalted SHA demo",
         "https://docs.python.org/3/library/hashlib.html", 35),
        "writeup",
    ),
    "PKI & TLS": _path(
        ("Theory — RFC 8446 TLS 1.3",
         "https://www.rfc-editor.org/rfc/rfc8446", 70),
        ("Video — Computerphile HTTPS (free)",
         "https://www.youtube.com/watch?v=j9QmMEWmcfo", 25),
        ("Automation — Python ssl.get_server_certificate + sslyze-style checks",
         "https://docs.python.org/3/library/ssl.html", 40),
        "comms",
    ),
    "OSINT Foundations": _path(
        ("Theory — OSINT Framework (free map)",
         "https://osintframework.com/", 40),
        ("Video — Bellingcat OSINT online investigation toolkit (free)",
         "https://www.bellingcat.com/resources/", 50),
        ("Automation — Python theHarvester-style recon script",
         "https://github.com/laramies/theHarvester", 45),
        "ethics",
    ),
    "Search & Recon Techniques": _path(
        ("Theory — Google Hacking Database (Exploit-DB, free)",
         "https://www.exploit-db.com/google-hacking-database", 35),
        ("Video — NahamSec recon methodology (free)",
         "https://www.youtube.com/@NahamSec", 40),
        ("Automation — Python crt.sh subdomain enumerator",
         "https://crt.sh/", 40),
        "ethics",
    ),
    "Python for Security": _path(
        ("Theory — Automate the Boring Stuff (free online)",
         "https://automatetheboringstuff.com/", 90),
        ("Video — freeCodeCamp Python for Pentesters (free)",
         "https://www.youtube.com/results?search_query=python+for+pentesters+freecodecamp", 70),
        ("Automation — Build a CLI: argparse + logging + JSON report",
         "https://docs.python.org/3/library/argparse.html", 50),
        "portfolio",
        extra_labs=[
            ("PicoCTF Python challenges", "Python for Security",
             "picoctf", "https://play.picoctf.org/practice?category=General%20Skills",
             "flag", 2, 60, 30, "T1059"),
        ],
    ),
    "Parsing Logs & Automation": _path(
        ("Theory — Regular Expressions info (free)",
         "https://www.regular-expressions.info/", 40),
        ("Video — Corey Schafer Python regex (free)",
         "https://www.youtube.com/watch?v=K8L6KVGG-7o", 50),
        ("Automation — Python parse Windows Event XML / syslog to CSV",
         "https://docs.python.org/3/library/csv.html", 50),
        "writeup",
    ),
    "Building a Basic Port Scanner": _path(
        ("Theory — Nmap Network Scanning (official book, free HTML)",
         "https://nmap.org/book/toc.html", 70),
        ("Video — Nmap for beginners (free)",
         "https://nmap.org/book/man.html", 40),
        ("Automation — Threaded Python TCP/SYN scanner with CIDR input",
         "https://docs.python.org/3/library/socket.html", 60),
        "ethics",
    ),
    "Windows Internals": _path(
        ("Theory — Microsoft Sysinternals docs",
         "https://learn.microsoft.com/en-us/sysinternals/", 50),
        ("Video — Windows Internals for security (free)",
         "https://www.youtube.com/results?search_query=windows+internals+security+sysinternals", 50),
        ("Automation — Python + PowerShell process/token inventory",
         "https://learn.microsoft.com/en-us/powershell/", 40),
        "notes",
    ),
    "Active Directory Fundamentals": _path(
        ("Theory — Microsoft AD DS concepts",
         "https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/virtual-dc/active-directory-domain-services-overview", 60),
        ("Video — SpecterOps AD security (free talks)",
         "https://www.youtube.com/@SpecterOps", 50),
        ("Automation — Python ldap3 user/group enumerator",
         "https://ldap3.readthedocs.io/", 50),
        "writeup",
        extra_labs=[
            ("GOAD local: LDAP enumeration", "Active Directory Fundamentals",
             "self_hosted_offline", "bundles/labs/windows_ad/",
             "self_report_checklist", 3, 90, 50, "T1087.002"),
        ],
    ),
    "Kerberos & BloodHound": _path(
        ("Theory — Kerberos RFC 4120 + BloodHound docs",
         "https://bloodhound.readthedocs.io/", 70),
        ("Video — Harmj0y Kerberoasting / BloodHound (free)",
         "https://www.youtube.com/results?search_query=harmj0y+bloodhound+kerberoasting", 55),
        ("Automation — Python Impacket GetUserSPNs wrapper + CSV report",
         "https://github.com/fortra/impacket", 50),
        "portfolio",
    ),
    "Linux Hardening & Audit": _path(
        ("Theory — CIS Ubuntu Benchmark (free PDF after register) + Lynis",
         "https://cisofy.com/lynis/", 50),
        ("Video — Linux hardening checklist (free)",
         "https://www.youtube.com/results?search_query=linux+hardening+lynis", 40),
        ("Automation — Python Lynis/auditd finding parser",
         "https://github.com/CISOfy/lynis", 40),
        "comms",
    ),
    "Linux Disk & Memory Forensics": _path(
        ("Theory — Volatility 3 documentation (free)",
         "https://volatility3.readthedocs.io/", 60),
        ("Video — 13Cubed DFIR (free)",
         "https://www.youtube.com/@13cubed", 50),
        ("Automation — Python Volatility plugin / timeline CSV",
         "https://github.com/volatilityfoundation/volatility3", 50),
        "writeup",
    ),
    "Packet Forensics at Scale": _path(
        ("Theory — Practical Packet Analysis notes + Zeek docs",
         "https://docs.zeek.org/en/master/", 60),
        ("Video — Zeek / Corelight intro (free)",
         "https://www.youtube.com/results?search_query=zeek+network+security+monitoring", 45),
        ("Automation — Python pyshark/scapy beacon detector",
         "https://scapy.readthedocs.io/", 50),
        "writeup",
    ),
    "SQLi & XSS Deep Dives": _path(
        ("Theory — PayloadAllTheThings SQLi/XSS (free GitHub)",
         "https://github.com/swisskyrepo/PayloadsAllTheThings", 60),
        ("Video — IppSec web challenge recaps (free)",
         "https://www.youtube.com/@ippsec", 50),
        ("Automation — Python sqlmap wrapper with authorized scope file",
         "https://sqlmap.org/", 40),
        "ethics",
    ),
    "Burp Suite Pro Techniques": _path(
        ("Theory — PortSwigger Advanced topics (free academy)",
         "https://portswigger.net/web-security/all-topics", 60),
        ("Video — PortSwigger research talks (free)",
         "https://portswigger.net/research", 45),
        ("Automation — Python turbo-intruder style race script",
         "https://portswigger.net/research/turbo-intruder-unleashing-the-true-potential-of-http-pipelining", 40),
        "writeup",
    ),
    "Web Cache Poisoning": _path(
        ("Theory — PortSwigger Web Cache Poisoning",
         "https://portswigger.net/web-security/web-cache-poisoning", 45),
        ("Video — James Kettle Black Hat cache poisoning (free)",
         "https://portswigger.net/research/practical-web-cache-poisoning", 40),
        ("Automation — Python header-permutation fuzzer",
         "https://requests.readthedocs.io/", 35),
        "writeup",
    ),
    "HTTP Request Smuggling": _path(
        ("Theory — PortSwigger HTTP Request Smuggling",
         "https://portswigger.net/web-security/request-smuggling", 50),
        ("Video — James Kettle HTTP Desync Attacks (free)",
         "https://portswigger.net/research/http-desync-attacks", 45),
        ("Automation — Python raw-socket CL.TE/TE.CL probes",
         "https://docs.python.org/3/library/socket.html", 40),
        "ethics",
    ),
    "Exploit Dev: Stack Overflow": _path(
        ("Theory — LiveOverflow binary exploitation notes + pwn.college",
         "https://pwn.college/", 90),
        ("Video — LiveOverflow Binary Exploitation (free)",
         "https://www.youtube.com/playlist?list=PLhixgUqwRTjxglIswKp9mpkfPNfHkzyeN", 80),
        ("Automation — Python pwntools cyclic / offset finder",
         "https://docs.pwntools.com/", 50),
        "notes",
        extra_labs=[
            ("pwn.college: Program Misuse / Memory Errors", "Exploit Dev: Stack Overflow",
             "other", "https://pwn.college/",
             "self_report", 4, 120, 50, "T1203"),
        ],
    ),
    "Exploit Dev: ROP Chains": _path(
        ("Theory — ROP Emporium (free challenges)",
         "https://ropemporium.com/", 70),
        ("Video — LiveOverflow ROP (free)",
         "https://www.youtube.com/results?search_query=liveoverflow+rop", 50),
        ("Automation — Python ROPgadget + pwntools chain builder",
         "https://github.com/JonathanSalwan/ROPgadget", 50),
        "portfolio",
    ),
    "Exploit Dev: Heap & Mitigations": _path(
        ("Theory — how2heap (free GitHub)",
         "https://github.com/shellphish/how2heap", 80),
        ("Video — LiveOverflow heap intro (free)",
         "https://www.youtube.com/results?search_query=liveoverflow+heap+exploitation", 50),
        ("Automation — Python glibc malloc trace parser",
         "https://sourceware.org/glibc/wiki/MallocInternals", 40),
        "notes",
    ),
    "Shellcoding Basics": _path(
        ("Theory — Linux syscall table + nasm docs",
         "https://blog.rchapman.org/posts/Linux_System_Call_Table_for_x86_64/", 45),
        ("Video — LiveOverflow shellcode (free)",
         "https://www.youtube.com/results?search_query=liveoverflow+shellcode", 40),
        ("Automation — Python assembler/encoder (avoid nulls)",
         "https://docs.pwntools.com/en/stable/asm.html", 45),
        "ethics",
    ),
    "Red Team C2 & Infrastructure": _path(
        ("Theory — MITRE C2 Matrix + Atomic Red Team",
         "https://github.com/redcanaryco/atomic-red-team", 60),
        ("Video — Red Canary Atomic Red Team intro (free)",
         "https://www.youtube.com/results?search_query=atomic+red+team+intro", 40),
        ("Automation — Python ART test runner + result JSON",
         "https://www.atomicredteam.io/", 50),
        "ethics",
    ),
    "Lateral Movement & OPSEC": _path(
        ("Theory — MITRE TA0008 Lateral Movement",
         "https://attack.mitre.org/tactics/TA0008/", 45),
        ("Video — SpecterOps lateral movement (free)",
         "https://www.youtube.com/results?search_query=specterops+lateral+movement", 45),
        ("Automation — Python Impacket wmiexec/smbexec lab wrapper",
         "https://github.com/fortra/impacket", 45),
        "comms",
    ),
    "Evasion & Defense Bypass": _path(
        ("Theory — MITRE TA0005 Defense Evasion",
         "https://attack.mitre.org/tactics/TA0005/", 45),
        ("Video — Elastic detection engineering talks (free)",
         "https://www.elastic.co/security-labs", 40),
        ("Automation — Python AMSI/ETW telemetry checklist (lab-only)",
         "https://attack.mitre.org/techniques/T1562/", 40),
        "ethics",
    ),
    "Bug Bounty Methodology": _path(
        ("Theory — HackerOne Hacktivity (public reports)",
         "https://hackerone.com/hacktivity", 50),
        ("Video — NahamSec bug bounty recon (free)",
         "https://www.youtube.com/@NahamSec", 50),
        ("Automation — Python recon pipeline (subdomains → httpx → nuclei-style checks)",
         "https://github.com/projectdiscovery", 50),
        "portfolio",
    ),
    "Malware Static Analysis": _path(
        ("Theory — Practical Malware Analysis companion + Ghidra docs",
         "https://ghidra-sre.org/", 70),
        ("Video — OALabs / Ghidra beginner (free)",
         "https://www.youtube.com/@OALabs", 60),
        ("Automation — Python pefile / capa / strings extractor",
         "https://github.com/erocarrera/pefile", 45),
        "writeup",
    ),
    "Malware Dynamic Analysis & Sandboxing": _path(
        ("Theory — ANY.RUN docs + Cuckoo (self-host)",
         "https://cuckoo.sh/docs/", 50),
        ("Video — 13Cubed malware detonation (free)",
         "https://www.youtube.com/@13cubed", 40),
        ("Automation — Python sandbox report parser (JSON IOC extract)",
         "https://github.com/cuckoosandbox/cuckoo", 40),
        "comms",
    ),
    "YARA & AV Evasion (detect)": _path(
        ("Theory — YARA documentation (official)",
         "https://yara.readthedocs.io/", 50),
        ("Video — Florian Roth / Sigma+YARA talks (free)",
         "https://www.youtube.com/results?search_query=florian+roth+yara+sigma", 40),
        ("Automation — Python yara-python scanner over lab samples",
         "https://yara.readthedocs.io/en/stable/yarapython.html", 40),
        "portfolio",
    ),
    "Unpacking Practice": _path(
        ("Theory — Unpacking with x64dbg notes",
         "https://x64dbg.com/", 45),
        ("Video — OALabs unpacking (free)",
         "https://www.youtube.com/results?search_query=olabs+unpacking+upx", 40),
        ("Automation — Python UPX detect + entropy map",
         "https://docs.python.org/3/library/collections.html", 35),
        "notes",
    ),
    "Cloud IAM Abuse": _path(
        ("Theory — AWS IAM documentation + CloudGoat",
         "https://github.com/RhinoSecurityLabs/cloudgoat", 60),
        ("Video — AWS re:Inforce IAM talks (free)",
         "https://www.youtube.com/results?search_query=aws+iam+privilege+escalation", 45),
        ("Automation — Python boto3 IAM simulator (localstack)",
         "https://boto3.amazonaws.com/v1/documentation/api/latest/index.html", 50),
        "ethics",
    ),
    "Kubernetes Attack Paths": _path(
        ("Theory — Kubernetes security docs + OWASP K8s Top 10",
         "https://owasp.org/www-project-kubernetes-top-ten/", 55),
        ("Video — ControlPlane / K8s security (free)",
         "https://www.youtube.com/results?search_query=kubernetes+security+owasp", 40),
        ("Automation — Python kubernetes client RBAC auditor",
         "https://github.com/kubernetes-client/python", 45),
        "writeup",
    ),
    "Terraform Misconfig Hunting": _path(
        ("Theory — Checkov / tfsec docs (free OSS)",
         "https://www.checkov.io/", 40),
        ("Video — HashiCorp Terraform security (free)",
         "https://developer.hashicorp.com/terraform/tutorials", 40),
        ("Automation — Python parse terraform plan JSON for open SG",
         "https://developer.hashicorp.com/terraform/internals/json-format", 40),
        "comms",
    ),
    "SIEM Queries & Sigma Rules": _path(
        ("Theory — Sigma specification (free)",
         "https://sigmahq.io/", 55),
        ("Video — Florian Roth Sigma intro (free)",
         "https://www.youtube.com/results?search_query=sigma+rules+florian+roth", 40),
        ("Automation — Python sigma-cli convert → Wazuh XML",
         "https://github.com/SigmaHQ/sigma", 50),
        "portfolio",
        extra_labs=[
            ("SigmaHQ public ruleset review", "SIEM Queries & Sigma Rules",
             "other", "https://github.com/SigmaHQ/sigma",
             "self_report", 2, 45, 25, None),
        ],
    ),
    "Threat Hunting at Scale": _path(
        ("Theory — TaHiTI / Sqrrl hunting papers + MITRE ATT&CK",
         "https://www.threathunting.net/", 50),
        ("Video — SANS Threat Hunting Summit talks (free)",
         "https://www.youtube.com/results?search_query=sans+threat+hunting+summit", 45),
        ("Automation — Python hypothesis → Wazuh query generator",
         "https://documentation.wazuh.com/", 45),
        "interview",
    ),
    "SOC Playbooks": _path(
        ("Theory — CISA Incident Response Playbooks (free)",
         "https://www.cisa.gov/resources-tools/resources/cybersecurity-incident-and-vulnerability-response-playbooks", 50),
        ("Video — NIST IR lifecycle (free)",
         "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r2.pdf", 40),
        ("Automation — Python playbook checklist (JSON → markdown report)",
         "https://www.cisa.gov/resources-tools", 35),
        "comms",
    ),
    "Cloud IAM & S3 Security": _path(
        ("Theory — AWS S3 security best practices (free)",
         "https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html", 45),
        ("Video — AWS S3 public bucket labs (free)",
         "https://www.youtube.com/results?search_query=aws+s3+security+best+practices", 35),
        ("Automation — Python boto3 bucket ACL auditor (localstack)",
         "https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3.html", 40),
        "writeup",
    ),
    "Kubernetes Security Basics": _path(
        ("Theory — CIS Kubernetes Benchmark overview",
         "https://www.cisecurity.org/benchmark/kubernetes", 40),
        ("Video — Kubernetes official security intro (free)",
         "https://kubernetes.io/docs/concepts/security/", 40),
        ("Automation — Python kubeconfig / RBAC dump parser",
         "https://kubernetes.io/docs/reference/access-authn-authz/rbac/", 35),
        "notes",
    ),
    "Risk Management Frameworks": _path(
        ("Theory — NIST RMF SP 800-37",
         "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-37r2.pdf", 55),
        ("Video — NIST CSF 2.0 overview (free)",
         "https://www.nist.gov/cyberframework", 35),
        ("Automation — Python control-to-evidence tracker CSV",
         "https://www.nist.gov/cyberframework/framework", 30),
        "comms",
    ),
    "NIST CSF & ISO 27001": _path(
        ("Theory — NIST CSF 2.0 + ISO/IEC 27001 overview (ISO preview)",
         "https://www.nist.gov/cyberframework", 50),
        ("Video — NIST CSF 2.0 webinar (free)",
         "https://www.nist.gov/cyberframework", 40),
        ("Automation — Python CSF subcategory coverage heatmap",
         "https://www.nist.gov/cyberframework/framework", 35),
        "interview",
    ),
}


def seed_learning_paths(topics_by_title: dict[str, Topic]) -> tuple[int, int]:
    """Attach theory/video/automation/soft-skill ContentItems + extra labs."""
    n_items = 0
    n_labs = 0
    for title, topic in topics_by_title.items():
        spec = PATHS.get(title)
        if spec is None:
            spec = {
                "theory": (
                    f"Theory — MITRE ATT&CK + official docs for {title}",
                    "https://attack.mitre.org/",
                    40,
                ),
                "video": (
                    f"Video — Free lecture search: {title}",
                    f"https://www.youtube.com/results?search_query={title.replace(' ', '+')}+cybersecurity",
                    40,
                ),
                "automation": (
                    f"Automation — Python lab script for {title}",
                    "https://docs.python.org/3/library/index.html",
                    30,
                ),
                "soft": SOFT["notes"],
                "labs": [],
            }

        tracks = [
            ("theory", spec["theory"], 10),
            ("video", spec["video"], 11),
            ("automation", spec["automation"], 12),
            ("soft", spec["soft"], 13),
        ]
        for kind, (ctitle, url, minutes), order in tracks:
            item, created = get_or_create(
                ContentItem,
                defaults={
                    "topic_id": topic.id,
                    "type": "external_link",
                    "title": ctitle,
                    "url": url,
                    "body_markdown": f"**Track:** {kind}\n\nFree resource: {url}",
                    "estimated_minutes": minutes,
                    "order_index": order,
                    "source": "in_house",
                    "is_active": True,
                },
                topic_id=topic.id,
                title=ctitle,
            )
            if created:
                n_items += 1
            elif item.url != url:
                item.url = url

        for lab_tuple in spec.get("labs", []):
            (ltitle, topic_title, provider, url, proof, diff, minutes, xp, mitre) = lab_tuple
            exists = Lab.query.filter_by(title=ltitle).first()
            if exists:
                continue
            db.session.add(Lab(
                topic_id=topic.id,
                title=ltitle,
                description=f"Free lab ({provider}): {ltitle}",
                provider=provider,
                url_or_container_ref=url,
                difficulty=diff,
                estimated_minutes=minutes,
                proof_type=proof,
                xp_reward=xp,
                mitre_techniques=json.dumps([mitre]) if mitre else None,
            ))
            n_labs += 1

    db.session.flush()
    return n_items, n_labs


def seed_professional_skills_area(areas_by_name: dict[str, SkillArea],
                                  topics_by_title: dict[str, Topic]) -> None:
    """Add a Professional Skills area used by interview/soft-skill topics."""
    area, _ = get_or_create(SkillArea, defaults={
        "name": "Professional Skills",
        "icon_class": "bi-people",
        "description": "Writing, communication, ethics, interviewing, and portfolio craft.",
        "color_hex": "#10b981",
        "order_index": 20,
    }, slug="professional-skills")
    areas_by_name["Professional Skills"] = area

    extra_topics = [
        ("Technical Writing for Security", 45),
        ("Stakeholder Incident Communication", 40),
        ("Interview STAR Stories & NICE Roles", 40),
        ("Building a Purple Team Portfolio", 50),
    ]
    for title, mins in extra_topics:
        slug = slugify(title)
        topic, created = get_or_create(Topic, defaults={
            "title": title,
            "difficulty": 1,
            "estimated_minutes": mins,
            "skill_area_id": area.id,
            "description": title,
        }, slug=slug)
        if created:
            topics_by_title[title] = topic
        else:
            topics_by_title.setdefault(title, topic)
    db.session.flush()
