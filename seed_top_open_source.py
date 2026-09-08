"""
seed_top_open_source_resources.py
==================================
Additive, idempotent seed layer that adds the best current open-source
purple-team and security-automation resources on top of the EXISTING
topics already created by seed.py / seed_comprehensive.py /
seed_purple_team_curriculum.py.

Why a separate file instead of editing the other five:
  - Those files total 6,000+ lines; editing them in place risks silently
    corrupting curriculum content that's already working.
  - This file only ever ADDS ContentItems and Labs to topics that already
    exist (looked up by title) — it never creates or modifies a Topic,
    SkillArea, JobRole, or CurriculumWeek. If a topic title doesn't match
    anything in your DB yet, that entry is just skipped (printed as a
    warning), nothing breaks.
  - Safe to re-run any time — every insert is get_or_create'd by title.

Run AFTER your existing seed scripts:
    python seed.py
    python seed_purple_team_curriculum.py   (if used)
    python seed_top_open_source_resources.py
"""
from __future__ import annotations

import json

from app import app
from extensions import db
from models import ContentItem, Lab, Topic
from seed import get_or_create  # reuse the existing helper — no duplication


# ---------------------------------------------------------------------------
# Format: (topic_title, kind_label, content_title, url, minutes)
# kind_label is just for the body_markdown prefix, matching your existing
# ContentItem "Track:" convention from seed_resources.py.
# ---------------------------------------------------------------------------
TOP_RESOURCES = [
    # --- Red Team / Attack Simulation --------------------------------------
    ("Red Team C2 & Infrastructure", "automation",
     "MITRE Caldera — Automated Adversary Emulation Platform",
     "https://github.com/mitre/caldera", 60),
    ("Red Team C2 & Infrastructure", "labs",
     "Atomic Red Team — ATT&CK-mapped attack simulation library",
     "https://github.com/redcanaryco/atomic-red-team", 45),
    ("Red Team C2 & Infrastructure", "automation",
     "Invoke-AtomicRedTeam — PowerShell runner for Atomic Red Team",
     "https://github.com/redcanaryco/invoke-atomicredteam", 40),
    ("Cloud IAM Abuse", "labs",
     "Stratus Red Team — Cloud-native attack technique emulation (AWS/Azure/GCP/K8s)",
     "https://github.com/DataDog/stratus-red-team", 45),

    # --- AD Attack Tooling (Python automation, not just usage) -------------
    ("Kerberos & BloodHound", "automation",
     "Impacket — Python library implementing Windows network protocols (the engine behind Kerberoasting/PTH/DCSync tools)",
     "https://github.com/fortra/impacket", 60),
    ("Lateral Movement & OPSEC", "automation",
     "NetExec (formerly CrackMapExec) — unified AD lateral movement & enumeration tool built on Impacket",
     "https://github.com/Pennyw0rth/NetExec", 45),

    # --- Blue Team / Detection Engineering ----------------------------------
    ("SIEM Queries & Sigma Rules", "labs",
     "SigmaHQ — 15,000+ vendor-neutral community detection rules",
     "https://github.com/SigmaHQ/sigma", 45),
    ("SOC Playbooks", "automation",
     "VECTR — Free purple-team exercise tracking (attack/detect/gap logging)",
     "https://github.com/SecurityRiskAdvisors/VECTR", 50),
    ("Packet Forensics at Scale", "automation",
     "Scapy — interactive Python packet crafting/sniffing/dissection",
     "https://github.com/secdev/scapy", 45),

    # --- Automated Lab Building (directly relevant to your VirtualBox build) -
    ("Active Directory Fundamentals", "labs",
     "DetectionLab — Vagrant/Packer automation that builds a full AD + logging lab unattended",
     "https://github.com/clong/DetectionLab", 90),

    # --- Cloud Security Automation -------------------------------------------
    ("Cloud IAM & S3 Security", "automation",
     "Prowler — open-source Python cloud security automation (AWS/Azure/GCP/K8s CIS audits)",
     "https://github.com/prowler-cloud/prowler", 50),

    # --- Reference / Knowledge Bases -------------------------------------------
    ("OWASP Top 10 Overview", "theory",
     "HackTricks — encyclopedic pentesting/CTF technique reference",
     "https://book.hacktricks.wiki/", 40),
    ("SQL Injection", "theory",
     "PayloadsAllTheThings — curated payload/bypass list for every vulnerability class",
     "https://github.com/swisskyrepo/PayloadsAllTheThings", 40),
]


def seed_top_resources() -> tuple[int, int]:
    n_added = 0
    n_skipped = 0
    for topic_title, kind, ctitle, url, minutes in TOP_RESOURCES:
        topic = Topic.query.filter_by(title=topic_title).first()
        if topic is None:
            print(f"[SKIP] Topic not found (add it first in an existing seed "
                  f"file, or fix the title match): {topic_title!r}")
            n_skipped += 1
            continue

        item, created = get_or_create(
            ContentItem,
            defaults={
                "type": "external_link",
                "title": ctitle,
                "url": url,
                "body_markdown": f"**Track:** {kind}\n\nTop open-source resource: {url}",
                "estimated_minutes": minutes,
                "order_index": 15,  # after the existing theory/video/automation/soft tracks (10-13)
                "source": "in_house",
                "is_active": True,
            },
            topic_id=topic.id,
            title=ctitle,
        )
        if created:
            n_added += 1
        elif item.url != url:
            item.url = url

    db.session.flush()
    return n_added, n_skipped


def main() -> None:
    with app.app_context():
        n_added, n_skipped = seed_top_resources()
        db.session.commit()
    print(f"[OK] Top open-source resources seed complete: "
          f"{n_added} added, {n_skipped} skipped (topic not found).")


if __name__ == "__main__":
    main()
