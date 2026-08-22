"""Seed reference data for the SkillSprint CyberSec platform.

Idempotent: only inserts rows that don't already exist (matched by slug /
question text). Run with `py seed.py` after `db.create_all()` has run.

Seeds (plan §16):
  - 9 SkillAreas              (Networking, Linux, Web App Sec, Crypto, OSINT,
                               Scripting/Python, Windows/AD, Cloud, GRC)
  - ~50 Topics with a basic DAG (TopicPrerequisite edges)
  - 9 JobRoles (NIST NICE-aligned) with JobRoleTopic mappings
  - ~45 AssessmentQuestions (5 per area, difficulty 1-5)
  - ~25 Tier-1 Labs (TryHackMe / PortSwigger / OverTheWire / PicoCTF links)
"""
from __future__ import annotations

import json
import re

from app import app
from extensions import db
from models import (
    SkillArea, Topic, TopicPrerequisite, JobRole, JobRoleTopic,
    AssessmentQuestion, Lab, MiniProject,
)


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def get_or_create(model, defaults: dict | None = None, **filters):
    defaults = defaults or {}
    row = model.query.filter_by(**filters).first()
    if row is None:
        # Don't pass filter keys twice when constructing the row.
        merged = dict(filters)
        merged.update(defaults)
        row = model(**merged)
        db.session.add(row)
        db.session.flush()
        return row, True
    return row, False


# ---------------------------------------------------------------------------
# Skill areas — full 5-tier taxonomy (plan §3)
# Tier 0: Computing Foundations / Networking Basics / Linux Fundamentals /
# Windows Fundamentals / Security Mindset
# Tier 1: Networking (deep) / Web App Sec / Cryptography / Scripting & Python / OSINT
# Tier 2: Windows & Active Directory / Linux Hardening & Forensics / Packet Forensics
# Tier 3: Exploit Development / Red Team Operations / Malware Analysis /
# Cloud & Container Pentesting / Blue Team / Detection Engineering
# ---------------------------------------------------------------------------
SKILL_AREAS = [
    # Tier 0 — Absolute Foundations
    ("Computing Foundations",      "💻", "Binary, hex, files, OS concepts — the prerequisites for everything security.", 0),
    ("Networking Basics",          "📡", "OSI, TCP/IP, packets — beginner-friendly entry before the deep Networking area.", 1),
    ("Linux Fundamentals",         "🐧", "Bash, file system, permissions, processes, services.", 2),
    ("Windows Fundamentals",       "🪟", "Windows OS basics: registry, processes, services, users, command line.", 3),
    ("Security Mindset",           "🧠", "CIA triad, threat models, attacker lifecycle, ethics & legality.", 4),
    # Tier 1 — Core Technical Security (already in the original seed; deepened)
    ("Networking",         "🌐", "TCP/IP, OSI, routing, firewalls, packet analysis (deep).", 5),
    ("Web Application Security", "🕸️", "OWASP Top 10, Burp Suite, SQLi, XSS, auth flaws.", 6),
    ("Cryptography",       "🔑", "Symmetric/asymmetric crypto, hashing, PKI, TLS.", 7),
    ("OSINT",              "🔭", "Open-source intelligence gathering & recon.", 8),
    ("Scripting & Python", "🐍", "Automation, parsing, sockets, security tooling.", 9),
    # Tier 2 — Systems & Active Directory (Networking deep + AD + packet forensics)
    ("Windows & Active Directory", "🪟", "AD, Kerberos, GPO, lateral movement, hardening.", 10),
    ("Linux Hardening & Forensics", "🛡️", "Hardening, disk/memory forensics, artifact recovery.", 11),
    ("Packet Forensics",   "📦", "PCAP analysis at incident scale — IoCs, beaconing, exfil detection.", 12),
    # Tier 3 — Advanced Offensive & Defensive
    ("Exploit Development",      "💥", "Stack overflow → ROP → heap, shellcoding, bypassing mitigations.", 13),
    ("Red Team Operations",      "🎯", "C2, lateral movement, OPSEC, evasion.", 14),
    ("Malware Analysis",         "🦠", "Static / dynamic, YARA, sandboxing, unpacking.", 15),
    ("Cloud & Container Pentesting", "☁️", "IAM abuse, K8s attacks, Terraform misconfig hunting.", 16),
    ("Blue Team / Detection Engineering", "🚨", "SIEM queries, sigma rules, threat hunting at scale, SOC playbooks.", 17),
    # Existing / legacy areas still surfaced as tracking buckets
    ("Cloud Security", "☁️", "Legacy cloud-bucket name kept for back-compat with old data.", 18),
    ("GRC",            "📋", "Governance, risk, compliance, NIST, ISO 27001.", 19),
]


def seed_skill_areas() -> dict[str, SkillArea]:
    by_name: dict[str, SkillArea] = {}
    for name, icon, desc, order in SKILL_AREAS:
        slug = slugify(name)
        area, _ = get_or_create(SkillArea, defaults={
            "name": name, "icon_class": icon, "description": desc,
            "color_hex": "#6366f1", "order_index": order,
        }, slug=slug)
        if area.name != name:
            area.name = name
        if area.description != desc:
            area.description = desc
        if area.order_index != order:
            area.order_index = order
        by_name[name] = area
    db.session.flush()
    return by_name


# ---------------------------------------------------------------------------
# Topics (title -> skill area) + prerequisites expressed as DAG edges
# (prereq is in the form "TopicA -> TopicB"; A must be created before B.)
# ---------------------------------------------------------------------------
TOPICS = [
    # =================== Tier 0 — Absolute Foundations ==================
    ("Binary, Hex & Number Systems",  "Computing Foundations"),
    ("Files & OS Concepts",           "Computing Foundations"),
    ("Networking Basics",             "Networking Basics"),
    ("Linux Fundamentals",            "Linux Fundamentals"),
    ("Windows Fundamentals",          "Windows Fundamentals"),
    ("Security Mindset & Ethics",      "Security Mindset"),
    ("CIA Triad & Threat Models",     "Security Mindset"),
    ("MITRE ATT&CK Overview",         "Security Mindset"),
    # =================== Tier 1 — Core Technical Security ================
    ("TCP/IP & Subnetting",               "Networking"),
    ("DNS & HTTP",                        "Networking"),
    ("Packet Analysis & Wireshark",       "Networking"),
    ("Firewalls & Network Hardening",     "Networking"),
    ("Linux Filesystem & Permissions",    "Linux Fundamentals"),
    ("Bash & Scripting Fundamentals",     "Linux Fundamentals"),
    ("Processes & Services",              "Linux Fundamentals"),
    ("Log Analysis & journald",           "Linux Fundamentals"),
    ("Web App Basics & HTTP",             "Web Application Security"),
    ("OWASP Top 10 Overview",             "Web Application Security"),
    ("SQL Injection",                     "Web Application Security"),
    ("Cross-Site Scripting (XSS)",        "Web Application Security"),
    ("Burp Suite Essentials",             "Web Application Security"),
    ("Authentication & Session Attacks", "Web Application Security"),
    ("Cryptographic Foundations",         "Cryptography"),
    ("Hashing & Salting",                 "Cryptography"),
    ("PKI & TLS",                         "Cryptography"),
    ("OSINT Foundations",                 "OSINT"),
    ("Search & Recon Techniques",         "OSINT"),
    ("Python for Security",              "Scripting & Python"),
    ("Parsing Logs & Automation",         "Scripting & Python"),
    ("Building a Basic Port Scanner",     "Scripting & Python"),
    # =================== Tier 2 — Systems & AD ==========================
    ("Windows Internals",                 "Windows & Active Directory"),
    ("Active Directory Fundamentals",     "Windows & Active Directory"),
    ("Kerberos & BloodHound",              "Windows & Active Directory"),
    ("Linux Hardening & Audit",           "Linux Hardening & Forensics"),
    ("Linux Disk & Memory Forensics",     "Linux Hardening & Forensics"),
    ("Packet Forensics at Scale",         "Packet Forensics"),
    # =================== Tier 3 — Advanced Offensive & Defensive ========
    ("SQLi & XSS Deep Dives",             "Web Application Security"),
    ("Burp Suite Pro Techniques",         "Web Application Security"),
    ("Web Cache Poisoning",               "Web Application Security"),
    ("HTTP Request Smuggling",            "Web Application Security"),
    ("Exploit Dev: Stack Overflow",       "Exploit Development"),
    ("Exploit Dev: ROP Chains",           "Exploit Development"),
    ("Exploit Dev: Heap & Mitigations",   "Exploit Development"),
    ("Shellcoding Basics",                "Exploit Development"),
    ("Red Team C2 & Infrastructure",       "Red Team Operations"),
    ("Lateral Movement & OPSEC",          "Red Team Operations"),
    ("Evasion & Defense Bypass",          "Red Team Operations"),
    ("Bug Bounty Methodology",            "Red Team Operations"),
    ("Malware Static Analysis",          "Malware Analysis"),
    ("Malware Dynamic Analysis & Sandboxing", "Malware Analysis"),
    ("YARA & AV Evasion (detect)",        "Malware Analysis"),
    ("Unpacking Practice",                "Malware Analysis"),
    ("Cloud IAM Abuse",                   "Cloud & Container Pentesting"),
    ("Kubernetes Attack Paths",           "Cloud & Container Pentesting"),
    ("Terraform Misconfig Hunting",       "Cloud & Container Pentesting"),
    ("SIEM Queries & Sigma Rules",        "Blue Team / Detection Engineering"),
    ("Threat Hunting at Scale",           "Blue Team / Detection Engineering"),
    ("SOC Playbooks",                     "Blue Team / Detection Engineering"),
    # =================== Cloud / GRC (legacy buckets) ===================
    ("Cloud IAM & S3 Security",           "Cloud Security"),
    ("Kubernetes Security Basics",        "Cloud Security"),
    ("Risk Management Frameworks",         "GRC"),
    ("NIST CSF & ISO 27001",               "GRC"),
]

PREREQUISITES = [
    # --- Tier 0 internal ordering ---
    ("Files & OS Concepts", "Security Mindset & Ethics"),
    ("Networking Basics", "Security Mindset & Ethics"),
    ("Linux Fundamentals", "Security Mindset & Ethics"),
    ("Windows Fundamentals", "Security Mindset & Ethics"),
    ("Security Mindset & Ethics", "CIA Triad & Threat Models"),
    ("CIA Triad & Threat Models", "MITRE ATT&CK Overview"),
    ("Binary, Hex & Number Systems", "Files & OS Concepts"),
    # --- Tier 0 → Tier 1 (everything advanced must depend on Tier 0) ---
    ("Networking Basics", "TCP/IP & Subnetting"),
    ("Networking Basics", "Linux Filesystem & Permissions"),
    ("Networking Basics", "Web App Basics & HTTP"),
    ("Linux Fundamentals", "Linux Filesystem & Permissions"),
    ("Linux Fundamentals", "Bash & Scripting Fundamentals"),
    ("Windows Fundamentals", "Windows Internals"),
    ("MITRE ATT&CK Overview", "TCP/IP & Subnetting"),
    ("MITRE ATT&CK Overview", "OWASP Top 10 Overview"),
    # --- Tier 1 internal DAG ---
    ("TCP/IP & Subnetting", "DNS & HTTP"),
    ("DNS & HTTP", "Web App Basics & HTTP"),
    ("DNS & HTTP", "Packet Analysis & Wireshark"),
    ("Packet Analysis & Wireshark", "Firewalls & Network Hardening"),
    ("Bash & Scripting Fundamentals", "Processes & Services"),
    ("Processes & Services", "Log Analysis & journald"),
    ("Web App Basics & HTTP", "OWASP Top 10 Overview"),
    ("OWASP Top 10 Overview", "SQL Injection"),
    ("OWASP Top 10 Overview", "Cross-Site Scripting (XSS)"),
    ("SQL Injection", "Burp Suite Essentials"),
    ("Cross-Site Scripting (XSS)", "Authentication & Session Attacks"),
    ("Cryptographic Foundations", "Hashing & Salting"),
    ("Hashing & Salting", "PKI & TLS"),
    ("OSINT Foundations", "Search & Recon Techniques"),
    ("Python for Security", "Parsing Logs & Automation"),
    ("Parsing Logs & Automation", "Building a Basic Port Scanner"),
    ("Bash & Scripting Fundamentals", "Python for Security"),
    # --- Tier 1 → Tier 2 ---
    ("Windows Internals", "Active Directory Fundamentals"),
    ("Active Directory Fundamentals", "Kerberos & BloodHound"),
    ("Linux Filesystem & Permissions", "Linux Hardening & Audit"),
    ("Linux Hardening & Audit", "Linux Disk & Memory Forensics"),
    ("Packet Analysis & Wireshark", "Packet Forensics at Scale"),
    ("Log Analysis & journald", "Packet Forensics at Scale"),
    # --- Tier 1/2 → Tier 3 (advanced offensive) ---
    ("SQL Injection", "SQLi & XSS Deep Dives"),
    ("Cross-Site Scripting (XSS)", "SQLi & XSS Deep Dives"),
    ("Burp Suite Essentials", "Burp Suite Pro Techniques"),
    ("Burp Suite Pro Techniques", "Web Cache Poisoning"),
    ("Web Cache Poisoning", "HTTP Request Smuggling"),
    ("Python for Security", "Exploit Dev: Stack Overflow"),
    ("Exploit Dev: Stack Overflow", "Exploit Dev: ROP Chains"),
    ("Exploit Dev: ROP Chains", "Exploit Dev: Heap & Mitigations"),
    ("Exploit Dev: ROP Chains", "Shellcoding Basics"),
    ("Kerberos & BloodHound", "Red Team C2 & Infrastructure"),
    ("Red Team C2 & Infrastructure", "Lateral Movement & OPSEC"),
    ("Lateral Movement & OPSEC", "Evasion & Defense Bypass"),
    ("SQLi & XSS Deep Dives", "Bug Bounty Methodology"),
    ("Burp Suite Pro Techniques", "Bug Bounty Methodology"),
    ("OSINT Foundations", "Bug Bounty Methodology"),
    # --- Tier 1/2 → Tier 3 (advanced defensive) ---
    ("Packet Forensics at Scale", "Malware Static Analysis"),
    ("Packet Forensics at Scale", "SIEM Queries & Sigma Rules"),
    ("Malware Static Analysis", "Malware Dynamic Analysis & Sandboxing"),
    ("Malware Static Analysis", "YARA & AV Evasion (detect)"),
    ("Malware Dynamic Analysis & Sandboxing", "Unpacking Practice"),
    ("Cloud IAM & S3 Security", "Cloud IAM Abuse"),
    ("Kubernetes Security Basics", "Kubernetes Attack Paths"),
    ("Cloud IAM Abuse", "Terraform Misconfig Hunting"),
    ("SIEM Queries & Sigma Rules", "Threat Hunting at Scale"),
    ("Threat Hunting at Scale", "SOC Playbooks"),
    # --- cloud + GRC legacy ---
    ("Cloud IAM & S3 Security", "Kubernetes Security Basics"),
    ("Risk Management Frameworks", "NIST CSF & ISO 27001"),
]


def seed_topics(areas) -> dict[str, Topic]:
    by_title: dict[str, Topic] = {}
    for title, area_name in TOPICS:
        slug = slugify(title)
        defaults = {
            "title": title, "difficulty": 2,
            "estimated_minutes": 60,
            "skill_area_id": areas[area_name].id,
        }
        topic, created = get_or_create(Topic, defaults=defaults, slug=slug)
        if created:
            topic.skill_area_id = areas[area_name].id
        by_title[title] = topic
    db.session.flush()

    # Add prerequisite edges (idempotent)
    for prereq_title, topic_title in PREREQUISITES:
        t = by_title.get(topic_title)
        p = by_title.get(prereq_title)
        if t is None or p is None:
            continue
        edge = TopicPrerequisite.query.filter_by(
            topic_id=t.id, prerequisite_topic_id=p.id).first()
        if edge is None:
            db.session.add(TopicPrerequisite(topic_id=t.id,
                                              prerequisite_topic_id=p.id))
    db.session.flush()
    return by_title


# ---------------------------------------------------------------------------
# Tier 4 capstone projects — one per JobRole (plan §3, Phase B5)
# Created BEFORE roles so JobRole.capstone_project_id can reference them.
# ---------------------------------------------------------------------------
CAPSTONES = [
    ("Pentester Mock OSCP 24-hour Lab",
     "Graded 24-hour mock OSCP exam against a 5-machine vulnerable VM pack. "
     "Submit AD-, web-, and privesc-user flags; self-grade by checklist.",
     "hard", 24, "flag_submission"),
    ("AppSec Capstone: Secure SDLC Audit",
     "Audit a bundled vulnerable web app source pack; identify OWASP Top 10 "
     "issues, propose fixes, write a DAST/SAST report, self-grade.",
     "medium", 12, "self_grade_checklist"),
    ("SOC Analyst L2 Capstone: Alert Triage",
     "Triage a packaged 'alert archive' of 20 SIEM alerts. Classify FP/TP, "
     "scope blast radius, propose containment. Auto-checked where feasible.",
     "medium", 8, "ioc_checklist"),
    ("Incident Responder Tabletop",
     "Full-scale IR tabletop exercise: ransomware artifact set including PCAP, "
     "host logs, IOCs. Produce a written after-action report (self-grade).",
     "hard", 10, "self_grade_checklist"),
    ("Cloud Security Capstone: K8s + IAM Attack Chain",
     "Identify and chain 5 cloud misconfigs (IAM, K8s, Terraform) on bundled "
     "manifests. Submit flags per stage.",
     "hard", 10, "flag_submission"),
    ("GRC Audit Capstone",
     "Map a fictional company's controls to NIST CSF + ISO 27001 Annex A and "
     "produce a gap-analysis report.",
     "medium", 8, "self_grade_checklist"),
    ("Bug Bounty Capstone: Public Program Write-up",
     "Pick a public-domain vulnerable app, hunt, document a vuln chain, write "
     "the write-up, self-grade by reproducibility/harshness rubric.",
     "hard", 12, "self_grade_checklist"),
    ("DFIR Capstone: Ransomware Artifact Analysis",
     "Analyze the bundled ransomware artifact set: identify IoCs, recover the "
     "encryption scheme, decode the staged data-exfil PCAP.",
     "hard", 14, "ioc_checklist"),
    ("Vulnerability Assessment Capstone",
     "Run a packaged scan over a vulnerable VM image; prioritize, write a "
     "remediation plan. Self/IOC-checked.",
     "medium", 10, "self_grade_checklist"),
]

# Maps JobRole slug -> capstone title (so the role row gets the right FK)
CAPSTONE_BY_ROLE = {
    "pentester":          "Pentester Mock OSCP 24-hour Lab",
    "appsec-engineer":    "AppSec Capstone: Secure SDLC Audit",
    "soc-analyst":        "SOC Analyst L2 Capstone: Alert Triage",
    "incident-responder": "Incident Responder Tabletop",
    "cloud-security":     "Cloud Security Capstone: K8s + IAM Attack Chain",
    "grc-analyst":        "GRC Audit Capstone",
    "bug-bounty":         "Bug Bounty Capstone: Public Program Write-up",
    "dfir":               "DFIR Capstone: Ransomware Artifact Analysis",
    "vuln-assessor":      "Vulnerability Assessment Capstone",
}


def seed_capstones() -> dict[str, MiniProject]:
    by_title: dict[str, MiniProject] = {}
    for title, desc, diff, hours, grading in CAPSTONES:
        project, _ = get_or_create(MiniProject, defaults={
            "title": title, "description": desc,
            "project_brief": desc, "difficulty_level": diff,
            "estimated_hours": hours, "grading_method": grading,
            "is_active": True,
        }, title=title)
        by_title[title] = project
    db.session.flush()
    return by_title


# ---------------------------------------------------------------------------
# Job roles (NIST NICE aligned) + per-role topic mapping
# ---------------------------------------------------------------------------
ROLES = [
    ("SOC Analyst",      "soc-analyst",       "🛡️",
     "Blue-team detection & triage — SIEM, log analysis, incident triage.",
     "₹6-15 LPA", ["CompTIA Security+", "CompTIA CySA+"],
     ["Networking Basics", "Linux Fundamentals", "Windows Fundamentals",
      "Security Mindset & Ethics", "Packet Analysis & Wireshark",
      "Windows Internals", "Log Analysis & journald",
      "Firewalls & Network Hardening", "Packet Forensics at Scale",
      "SIEM Queries & Sigma Rules", "Threat Hunting at Scale", "SOC Playbooks"]),
    ("Penetration Tester", "pentester",      "🎯",
     "Offensive security — find & exploit weaknesses across network, web, AD.",
     "₹8-25 LPA", ["OSCP", "eJPT"],
     ["Binary, Hex & Number Systems", "Files & OS Concepts",
      "Networking Basics", "Linux Fundamentals", "Windows Fundamentals",
      "Security Mindset & Ethics", "MITRE ATT&CK Overview",
      "TCP/IP & Subnetting", "DNS & HTTP",
      "Linux Filesystem & Permissions", "Bash & Scripting Fundamentals",
      "Web App Basics & HTTP", "OWASP Top 10 Overview", "SQL Injection",
      "Cross-Site Scripting (XSS)", "Burp Suite Essentials",
      "Active Directory Fundamentals", "Kerberos & BloodHound",
      "Python for Security", "Exploit Dev: Stack Overflow",
      "Exploit Dev: ROP Chains", "Red Team C2 & Infrastructure",
      "Lateral Movement & OPSEC", "Bug Bounty Methodology"]),
    ("AppSec Engineer",   "appsec-engineer",   "🐞",
     "Secure SDLC, threat modeling, code review & DAST/SAST tooling.",
     "₹10-30 LPA", ["OffSec WEB-300", "CSSLP"],
     ["Networking Basics", "Linux Fundamentals", "Web App Basics & HTTP",
      "OWASP Top 10 Overview", "SQL Injection", "Cross-Site Scripting (XSS)",
      "Authentication & Session Attacks", "Python for Security",
      "Hashing & Salting", "SQLi & XSS Deep Dives", "Burp Suite Pro Techniques",
      "Web Cache Poisoning", "HTTP Request Smuggling",
      "Bug Bounty Methodology"]),
    ("Incident Responder","incident-responder","🚒",
     "Contain, eradicate & recover from active incidents — RDP, ransomware, IR playbooks.",
     "₹8-20 LPA", ["GCIH", "GCFA"],
     ["Networking Basics", "Windows Fundamentals", "Windows Internals",
      "Log Analysis & journald", "Packet Analysis & Wireshark",
      "Active Directory Fundamentals", "Packet Forensics at Scale",
      "Malware Static Analysis", "SIEM Queries & Sigma Rules",
      "SOC Playbooks"]),
    ("Cloud Security Engineer","cloud-security","☁️",
     "Harden cloud workloads — IAM, S3, K8s misconfigurations.",
     "₹12-35 LPA", ["AWS Security Specialty", "CCSK"],
     ["Networking Basics", "Linux Fundamentals", "Cloud IAM & S3 Security",
      "Kubernetes Security Basics", "Hashing & Salting",
      "Cloud IAM Abuse", "Kubernetes Attack Paths",
      "Terraform Misconfig Hunting"]),
    ("GRC Analyst","grc-analyst","📋",
     "Policy, risk, and compliance — NIST CSF, ISO 27001, audit prep.",
     "₹8-18 LPA", ["CISA", "ISO 27001 LA"],
     ["Security Mindset & Ethics", "Risk Management Frameworks",
      "NIST CSF & ISO 27001", "Cryptographic Foundations",
      "CIA Triad & Threat Models"]),
    ("Bug Bounty Hunter","bug-bounty","🏆",
     "Hunt vulnerabilities on public bug-bounty programs — web-focused.",
     "Varies (per-bounty)", ["OSCP", "BBJS"],
     ["Networking Basics", "Web App Basics & HTTP", "OWASP Top 10 Overview",
      "SQL Injection", "Cross-Site Scripting (XSS)",
      "Authentication & Session Attacks", "Burp Suite Essentials",
      "OSINT Foundations", "SQLi & XSS Deep Dives",
      "Burp Suite Pro Techniques", "Web Cache Poisoning",
      "HTTP Request Smuggling", "Bug Bounty Methodology"]),
    ("Blue Team / DFIR","dfir","🏥",
     "Digital forensics & incident response — memory, disk, network artifacts.",
     "₹8-25 LPA", ["GCFA", "GNFA"],
     ["Networking Basics", "Linux Fundamentals", "Windows Fundamentals",
      "Windows Internals", "Log Analysis & journald",
      "Packet Analysis & Wireshark", "Cryptographic Foundations",
      "Packet Forensics at Scale", "Linux Disk & Memory Forensics",
      "Malware Static Analysis", "Malware Dynamic Analysis & Sandboxing",
      "YARA & AV Evasion (detect)"]),
    ("Vulnerability Assessment Analyst","vuln-assessor","🔍",
     "Identify & prioritize vulnerabilities across the estate.",
     "₹6-18 LPA", ["CompTIA Security+", "Nessus TCNA"],
     ["Networking Basics", "Linux Fundamentals",
      "Linux Filesystem & Permissions", "Firewalls & Network Hardening",
      "OWASP Top 10 Overview", "Python for Security"]),
]


def seed_roles(topics_by_title, capstones_by_title) -> None:
    for name, slug, emoji, desc, salary, certs, topic_titles in ROLES:
        capstone_title = CAPSTONE_BY_ROLE.get(slug)
        capstone_id = (capstones_by_title[capstone_title].id
                       if capstone_title and capstone_title in capstones_by_title
                       else None)
        role, created = get_or_create(JobRole, defaults={
            "name": name, "description": desc,
            "avg_salary_note": salary,
            "recommended_certs": json.dumps(certs),
            "icon_emoji": emoji, "difficulty_label": "Beginner Friendly",
            "color_hex": "#6366f1",
            "capstone_project_id": capstone_id,
        }, slug=slug)
        if not created:
            # Update the capstone FK for roles that already existed from the
            # original seed (pre-Tier-4 rows).
            if role.capstone_project_id != capstone_id and capstone_id is not None:
                role.capstone_project_id = capstone_id
            # Repopulate topic mapping so newly-added Tier 0/3 topics attach.
            JobRoleTopic.query.filter_by(job_role_id=role.id).delete()
            db.session.flush()
        for order, t_title in enumerate(topic_titles):
            t = topics_by_title.get(t_title)
            if t is None:
                continue
            db.session.add(JobRoleTopic(
                job_role_id=role.id, topic_id=t.id,
                order_index=order, is_core=(order < 4),
            ))
    db.session.flush()


# ---------------------------------------------------------------------------
# Assessment questions — 5 per area, difficulty 1..5
# ---------------------------------------------------------------------------
QUESTIONS = {
    "Networking": [
        ("Which OSI layer does TCP operate on?", "3", "1", [
            "Application", "Transport", "Network", "Data Link"]),
        ("Default port for HTTPS?", "2", "2", ["80", "21", "443", "8080"]),
        ("Subnet mask /24 allows how many usable host addresses?", "2", "3", ["255", "254", "128", "62"]),
        ("What protocol resolves domain names to IPs?", "0", "4", ["DNS", "ARP", "DHCP", "ICMP"]),
        ("Which flag in a SYN scan indicates an open port?", "1", "5", ["RST", "SYN/ACK", "FIN", "ACK"]),
    ],
    "Linux Fundamentals": [
        ("Which command shows long-format file permissions?", "3", "1", ["cd","pwd","whoami","ls -l"]),
        ("Path of the system password hashes (legacy)?", "2", "2", ["/etc/passwd","/etc/hosts","/etc/shadow","/var/log/auth.log"]),
        ("Which command grants execute permission to all?", "1", "3", ["chmod a+r file","chmod a+x file","chmod 600 file","chmod -x file"]),
        ("Tool to view systemd journal logs?", "1", "4", ["tail","journalctl","dmesg","cat"]),
        ("Which signal does `kill -9` send?", "2", "5", ["SIGTERM","SIGINT","SIGKILL","SIGHUP"]),
    ],
    "Web Application Security": [
        ("Which OWASP issue allows injection of client-side script?", "2", "1", ["SQLi","CSRF","XSS","SSRF"]),
        ("Best mitigation for SQL Injection?", "2", "2", ["URL encoding","Escaping separators","Prepared statements","CSP"]),
        ("Which header best mitigates clickjacking?", "1", "3", ["Content-Security-Policy","X-Frame-Options","X-XSS-Protection","Strict-Transport-Security"]),
        ("Default/common port for HTTP proxies like Burp?", "2", "4", ["443","21","8080","22"]),
        ("JWT signing algorithm that uses no secret at all?", "2", "5", ["HS256","RS256","none","ES256"]),
    ],
    "Cryptography": [
        ("Which is a hashing algorithm?", "0", "1", ["AES","SHA-256","RSA","DES"]),
        ("Property: same input always yields same hash?", "0", "2", ["Determinism","Salted","Reversible","Symmetric"]),
        ("Which cipher is asymmetric?", "2", "3", ["AES","DES","RSA","3DES"]),
        ("TLS handshake step where shared secret is established?", "2", "4", ["Hello","Certificate","Key Exchange","Finished"]),
        ("Why salt passwords before hashing?", "1", "5", ["Performance","Defeat rainbow tables","Shorten the hash","Compress them"]),
    ],
    "OSINT": [
        ("Which tool searches for leaked email/password pairs?", "2", "1", ["whois","nmap","haveibeenpwned","theHarvester"]),
        ("DNS record type identifying mail servers?", "2", "2", ["A","CNAME","MX","TXT"]),
        ("Which search operator restricts results to a site? (Google)", "2", "3", ["site:","inurl:","intitle:","related:"]),
        ("Best passive technique to enumerate subdomains?", "2", "4", ["nmap -sS","zone transfer (axfr)","certificate transparency logs","brute forcing"]),
        ("What does `theHarvester` primarily collect?", "0", "5", ["Emails & subdomains","Passwords","Packet captures","Registry keys"]),
    ],
    "Scripting & Python": [
        ("Python statement to handle exceptions?", "1", "1", ["throw","try/except","catch","raise"]),
        ("Module for making HTTP requests?", "2", "2", ["http","socket","requests","urllib3"]),
        ("Library for TCP packet crafting from scapy family?", "2", "3", ["netcat","nmap","scapy","paramiko"]),
        ("How to read a file line by line idiomatically?", "0", "4", ["for line in open(f):","while f.read():","f.readlines_until():","load(f)"]),
        ("Which argument enables argparse required fields?", "2", "5", ["mandatory=True","req=True","required=True","need=True"]),
    ],
    "Windows & Active Directory": [
        ("Default port for RDP?", "1", "1", ["443","3389","22","445"]),
        ("Protocol at the heart of AD authentication?", "1", "2", ["NTLM","Kerberos","LDAP","SMB"]),
        ("Tool to map AD trust relationships graphically?", "1", "3", ["Wireshark","BloodHound","Mimikatz","Responder"]),
        ("Extension of PowerShell modules?", "2", "4", [".psm1",".py",".sh",".dll"]),
        ("LSASS stores what attacker-coveted material?", "1", "5", ["Firewall rules","Credentials/tickets","Certificates","Event logs"]),
    ],
    "Cloud Security": [
        ("Best practice for storing cloud secrets?", "1", "1", ["Environment variables","Secrets manager","README","Source code"]),
        ("Which AWS resource has an SCP-like policy scope?", "2", "2", ["VPC","S3","IAM Role","KMS"]),
        ("Most common Kubernetes misconfiguration type?", "0", "3", ["RBAC overly broad","Open kubelet port","Overloaded CPU","TLS termination"]),
        ("Control that can restrict S3 to a specific VPC endpoint?", "2", "4", ["CORS","WAF","Bucket policy","IAM Role"]),
        ("The 'shared responsibility' model applies because cloud providers secure what?", "0", "5", ["The cloud (infra)","Data you create","Customer IAM policy","Your app source"]),
    ],
    "GRC": [
        ("NIST CSF core function that includes detection?", "1", "1", ["Identify","Detect","Respond","Recover"]),
        ("ISO 27001 clause families are labeled as?", "2", "2", ["Annex A controls","TLS standards","OWASP Top 10","MITRE ATT&CK"]),
        ("A 'risk register' is best described as?", "2", "3", ["A back-up schedule","A list of credentials","A log of identified risks","A contract template"]),
        ("Which best describes 'residual risk'?  Neither", "3", "4", ["Zero risk","Inherent risk","Risk after controls applied","Risk transferred to insurer"]),
        ("SOC 2 Type II differs from Type I by?", "0", "5", ["Testing over a period","Self-assessment","Scope of controls","Number of controls"]),
    ],
}


def seed_questions(areas) -> None:
    for area_name, qs in QUESTIONS.items():
        area = areas.get(area_name)
        if area is None:
            continue
        for i, (q_text, correct_idx, difficulty, opts) in enumerate(qs):
            exists = AssessmentQuestion.query.filter_by(
                skill_area_id=area.id, question_text=q_text).first()
            if exists:
                continue
            db.session.add(AssessmentQuestion(
                skill_area_id=area.id,
                question_text=q_text,
                question_type="mcq",
                options=json.dumps(opts),
                correct_answer=str(correct_idx),
                explanation=None,
                difficulty=int(difficulty),
                applicable_roles=json.dumps([]),
            ))
    db.session.flush()


# ---------------------------------------------------------------------------
# Labs (Tier-1: curated free link-out labs)
# ---------------------------------------------------------------------------
LABS = [
    # (title, topic, provider, url, proof, diff, min, xp, mitre)
    ("TryHackMe: Pre-Security Learning Path", "Networking Basics", "tryhackme",
     "https://tryhackme.com/path/outline/presecurity", "self_report", 1, 30, 25, None),
    ("OverTheWire: Bandit Level 0", "Linux Filesystem & Permissions", "overthewire",
     "https://overthewire.org/wargames/bandit/bandit0.html", "flag", 1, 15, 15,
     "T1059"),
    ("OverTheWire: Bandit Level 5", "Bash & Scripting Fundamentals", "overthewire",
     "https://overthewire.org/wargames/bandit/bandit5.html", "flag", 2, 30, 25,
     "T1059"),
    ("PortSwigger: SQLi Cheat Sheet Lab (Apprentice)", "SQL Injection", "portswigger",
     "https://portswigger.net/web-security/sql-injection/server-side/lab-series/vulnerable", "writeup_url", 2, 30, 25,
     "T1190"),
    ("PortSwigger: XSS Apprentice Series", "Cross-Site Scripting (XSS)", "portswigger",
     "https://portswigger.net/web-security/cross-site-scripting", "self_report", 2, 30, 25,
     "T1059"),
    ("PortSwigger: Burp Suite Basics Lab", "Burp Suite Essentials", "portswigger",
     "https://portswigger.net/burp", "self_report", 1, 15, 15, None),
    ("HTB Academy: Using Web Proxies (Tier 1)", "Burp Suite Essentials", "htb",
     "https://academy.hackthebox.com/catalog/academy/using-web-proxies", "self_report", 2, 45, 30,
     "T1059"),
    ("PicoCTF: Forensics Intro", "Packet Analysis & Wireshark", "picoctf",
     "https://play.picoctf.org/practice?category=Forensics&page=1", "flag", 2, 30, 25,
     "T1580"),
    ("TryHackMe: Introduction to Cyber Security", "OWASP Top 10 Overview", "tryhackme",
     "https://tryhackme.com/room/introtooffensivesecurity", "self_report", 1, 60, 25,
     "T1592"),
    ("TryHackMe: Linux Fundamentals 1", "Linux Filesystem & Permissions", "tryhackme",
     "https://tryhackme.com/room/linuxfundamentals1", "self_report", 1, 60, 25,
     "T1059"),
    ("PortSwigger: OS User Auth Lab Series", "Authentication & Session Attacks", "portswigger",
     "https://portswigger.net/web-security/authentication", "self_report", 3, 60, 35,
     "T1110"),
    ("OverTheWire: Natas Level 0", "Authentication & Session Attacks", "overthewire",
     "https://overthewire.org/wargames/natas/natas0.html", "flag", 2, 30, 25,
     "T1110"),
    ("OverTheWire: Leviathan Level 0", "Bash & Scripting Fundamentals", "overthewire",
     "https://overthewire.org/wargames/leviathan/leviathan0.html", "flag", 2, 30, 25,
     "T1059"),
    ("TryHackMe: DNS in Detail", "DNS & HTTP", "tryhackme",
     "https://tryhackme.com/room/dnsindetail", "self_report", 1, 45, 25, None),
    ("TryHackMe: Intro to Cryptography", "Cryptographic Foundations", "tryhackme",
     "https://tryhackme.com/room/cryptography", "self_report", 2, 60, 30, None),
    ("TryHackMe: Windows Internals", "Windows Internals", "tryhackme",
     "https://tryhackme.com/room/windowsinternals", "self_report", 2, 60, 30,
     "T1082"),
    ("TryHackMe: Active Directory Basics", "Active Directory Fundamentals", "tryhackme",
     "https://tryhackme.com/room/activedirectorybasics", "self_report", 3, 60, 35,
     "T1087"),
    ("TryHackMe: OSINT Intro", "OSINT Foundations", "tryhackme",
     "https://tryhackme.com/room/osint", "self_report", 2, 30, 25, "T1582"),
    ("TryHackMe: Python Basics", "Python for Security", "tryhackme",
     "https://tryhackme.com/room/pythonbasics", "self_report", 1, 60, 25,
     "T1059"),
    ("TryHackMe: Intro to IAM (AWS)", "Cloud IAM & S3 Security", "tryhackme",
     "https://tryhackme.com/room/iam000", "self_report", 3, 60, 35, None),
    ("TryHackMe: Kubernetes Basics", "Kubernetes Security Basics", "tryhackme",
     "https://tryhackme.com/room/kubernetes", "self_report", 3, 60, 35, None),
    ("TryHackMe: Unattended Networks & Wireshark", "Packet Analysis & Wireshark", "tryhackme",
     "https://tryhackme.com/room/abchat", "self_report", 2, 45, 25, "T1040"),
    ("PortSwigger: Server-side Request Forgery", "Web App Basics & HTTP", "portswigger",
     "https://portswigger.net/web-security/ssrf", "self_report", 3, 60, 35,
     "T1190"),
    ("TryHackMe: Intro to NIST CSF", "NIST CSF & ISO 27001", "tryhackme",
     "https://tryhackme.com/room/cybersecurityframeworks", "self_report", 1, 45, 25, None),
    ("OverTheWire: Krypton Level 0", "Cryptographic Foundations", "overthewire",
     "https://overthewire.org/wargames/krypton/krypton0.html", "flag", 2, 30, 25, None),
]


def seed_labs(topics_by_title) -> None:
    for title, topic_title, provider, url, proof, diff, minutes, xp, mitre in LABS:
        topic = topics_by_title.get(topic_title)
        if topic is None:
            continue
        exists = Lab.query.filter_by(title=title).first()
        if exists:
            continue
        mitre_json = json.dumps([mitre]) if mitre else None
        db.session.add(Lab(
            topic_id=topic.id, title=title, description=f"Lab from {provider}: {title}",
            provider=provider, url_or_container_ref=url,
            difficulty=diff, estimated_minutes=minutes,
            proof_type=proof, xp_reward=xp,
            mitre_techniques=mitre_json,
        ))
    db.session.flush()


def main() -> None:
    from models import MiniProject
    with app.app_context():
        areas = seed_skill_areas()
        topics = seed_topics(areas)
        capstones = seed_capstones()
        seed_roles(topics, capstones)
        seed_questions(areas)
        seed_labs(topics)
        db.session.commit()
        n_areas = SkillArea.query.count()
        n_topics = Topic.query.count()
        n_roles = JobRole.query.count()
        n_capstones = MiniProject.query.count()
        n_q = AssessmentQuestion.query.count()
        n_labs = Lab.query.count()
    print(f"[OK] Seed complete: {n_areas} areas, {n_topics} topics, "
          f"{n_roles} roles, {n_capstones} capstone projects, "
          f"{n_q} questions, {n_labs} labs.")


if __name__ == "__main__":
    main()
