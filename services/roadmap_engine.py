"""Roadmap generation / re-planning engine — ZeroCipher Purple Team Mastery Path.

Two-phase design:
  Phase 1 (Months 1-3): Job-Ready Track — Core purple team skills to be employable
  Phase 2 (Month 4+): Mastery Track — Advanced topics, capstones, continuous practice

No assessment — everyone starts at zero. The roadmap is a fixed, comprehensive
purple team curriculum with every topic having labs. No skipping allowed.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum

from flask import current_app
from extensions import db
from models import (
    Roadmap, RoadmapItem, Topic, JobRole, JobRoleTopic, ContentItem, Lab,
    WeeklyAvailability, CurriculumWeek, UserResource,
)

from services.scheduler_service import schedule_items, availability_for_user


class RoadmapPhase(Enum):
    JOB_READY = "job_ready"      # Months 1-3: Core employable skills
    MASTERY = "mastery"          # Month 4+: Advanced, continuous


@dataclass
class TopicScheduleItem:
    topic: Topic
    phase: RoadmapPhase
    week_number: int
    order_in_week: int


# ---------------------------------------------------------------------------
# Helpers: DAG topological order
# ---------------------------------------------------------------------------

def _topo_order(topics: list[Topic], prerequisites: dict[int, list[int]]) -> list[Topic]:
    """Kahn's algorithm restricted to `topics`. `prerequisites` maps
    topic_id -> list of prerequisite topic_ids (which may include topics
    outside this set; those are ignored)."""
    by_id = {t.id: t for t in topics}
    indeg: dict[int, int] = {t.id: 0 for t in topics}
    for t in topics:
        for p in prerequisites.get(t.id, []):
            if p in by_id:
                indeg[t.id] += 1

    q = [tid for tid, d in indeg.items() if d == 0]
    order: list[Topic] = []
    while q:
        q.sort(key=lambda tid: by_id[tid].difficulty if by_id[tid].difficulty else 1)
        tid = q.pop(0)
        order.append(by_id[tid])
        for other in topics:
            if tid in prerequisites.get(other.id, []):
                indeg[other.id] -= 1
                if indeg[other.id] == 0 and other not in order and other.id not in q:
                    q.append(other.id)
    # Append any leftover (cycles / unresolved deps)
    for t in topics:
        if t not in order:
            order.append(t)
    return order


def _topic_prerequisites_map(topics: list[Topic]) -> dict[int, list[int]]:
    result: dict[int, list[int]] = {}
    for t in topics:
        result[t.id] = [p.prerequisite_topic_id for p in t.prerequisites
                        if p.prerequisite_topic_id is not None]
    return result


# ---------------------------------------------------------------------------
# Purple Team Curriculum Definition
# ---------------------------------------------------------------------------

# Phase 1: Job-Ready (Weeks 1-12) - Core Purple Team Skills
JOB_READY_WEEKS = {
    1: {
        "title": "Network Recon & Discovery",
        "topics": [
            "Networking Basics",
            "TCP/IP & Subnetting",
            "DNS & HTTP",
            "Packet Analysis & Wireshark",
        ],
        "goal": "Master network scanning, enumeration, and service identification using Nmap, Masscan, and DNS tools against Metasploitable2 and GOAD.",
    },
    2: {
        "title": "Linux & Windows Fundamentals",
        "topics": [
            "Linux Fundamentals",
            "Linux Filesystem & Permissions",
            "Bash & Scripting Fundamentals",
            "Processes & Services",
            "Log Analysis & journald",
            "Windows Fundamentals",
            "Windows Internals",
            "Security Mindset & Ethics",
            "CIA Triad & Threat Models",
            "MITRE ATT&CK Overview",
        ],
        "goal": "Build fluency in Linux (permissions, services, logs) and Windows (registry, PowerShell, AD basics) — the OS layer every attacker and defender needs.",
    },
    3: {
        "title": "Web App Recon & OWASP Top 10",
        "topics": [
            "Web App Basics & HTTP",
            "OWASP Top 10 Overview",
            "SQL Injection",
            "Cross-Site Scripting (XSS)",
            "Burp Suite Essentials",
            "Authentication & Session Attacks",
        ],
        "goal": "Map web applications, discover attack surface, and understand the OWASP Top 10 vulnerability classes through DVWA/Juice Shop.",
    },
    4: {
        "title": "Active Directory Enumeration",
        "topics": [
            "Active Directory Fundamentals",
            "Kerberos & BloodHound",
            "Windows Internals",
        ],
        "goal": "Enumerate GOAD domain: users, groups, GPOs, trusts, SPNs, and delegation settings using BloodHound, ldapsearch, and PowerView.",
    },
    5: {
        "title": "Credential Attacks: Kerberoasting & AS-REP Roasting",
        "topics": [
            "Kerberos & BloodHound",
            "Active Directory Fundamentals",
            "Cryptographic Foundations",
            "Hashing & Salting",
        ],
        "goal": "Execute Kerberoasting and AS-REP roasting against GOAD service accounts; crack hashes with Hashcat; detect via Event ID 4769/4768.",
    },
    6: {
        "title": "Lateral Movement & Privilege Escalation",
        "topics": [
            "Active Directory Fundamentals",
            "Kerberos & BloodHound",
            "Windows Internals",
            "Lateral Movement & OPSEC",
        ],
        "goal": "Practice Pass-the-Hash, Pass-the-Ticket, and SMB relay; escalate via misconfigured services and delegation; detect via Event ID 4624/4672.",
    },
    7: {
        "title": "Persistence & Defense Evasion",
        "topics": [
            "Windows Internals",
            "Active Directory Fundamentals",
            "Linux Hardening & Audit",
            "Evasion & Defense Bypass",
        ],
        "goal": "Implement registry run keys, scheduled tasks, WMI event subscriptions, and DLL hijacking; detect via Sysmon Event ID 12/13/14.",
    },
    8: {
        "title": "Command & Control & Exfiltration",
        "topics": [
            "Packet Forensics at Scale",
            "Malware Static Analysis",
            "Red Team C2 & Infrastructure",
        ],
        "goal": "Simulate C2 channels (DNS, HTTP, HTTPS) and data exfiltration; build Sigma/Wazuh rules for beaconing and large transfers.",
    },
    9: {
        "title": "SIEM Queries & Sigma Rule Development",
        "topics": [
            "SIEM Queries & Sigma Rules",
            "Threat Hunting at Scale",
            "Packet Forensics at Scale",
        ],
        "goal": "Write advanced Wazuh/Sigma rules for ATT&CK techniques covered; tune for low false positives; test against Atomic Red Team.",
    },
    10: {
        "title": "Threat Hunting at Scale",
        "topics": [
            "Threat Hunting at Scale",
            "SIEM Queries & Sigma Rules",
            "Packet Forensics at Scale",
        ],
        "goal": "Hypothesis-driven hunting: use MITRE ATT&CK to structure hunts; query Wazuh/Elastic for anomalous patterns across GOAD environment.",
    },
    11: {
        "title": "SOC Playbooks & Incident Response",
        "topics": [
            "SOC Playbooks",
            "Threat Hunting at Scale",
            "Malware Dynamic Analysis & Sandboxing",
        ],
        "goal": "Build and execute IR playbooks for ransomware, credential theft, and web shell scenarios; practice containment, eradication, recovery.",
    },
    12: {
        "title": "Purple Team Capstone: Full Attack+Detect Chain",
        "topics": [
            "Kerberos & BloodHound",
            "Active Directory Fundamentals",
            "Lateral Movement & OPSEC",
            "SIEM Queries & Sigma Rules",
        ],
        "goal": "End-to-end exercise: attack GOAD (Kerberoasting → PTH → Lateral), detect each stage via Wazuh/Sigma, document in professional report.",
    },
}

# Phase 2: Mastery (Week 13+) - Advanced & Continuous
MASTERY_WEEKS = {
    13: {
        "title": "Advanced AD Attacks: Delegation & Trust Abuse",
        "topics": [
            "Kerberos & BloodHound",
            "Active Directory Fundamentals",
            "Red Team C2 & Infrastructure",
        ],
        "goal": "Master constrained/unconstrained delegation, resource-based constrained delegation, cross-forest trusts, and golden/silver ticket attacks.",
    },
    14: {
        "title": "Advanced Web Exploitation",
        "topics": [
            "SQLi & XSS Deep Dives",
            "Burp Suite Pro Techniques",
            "Web Cache Poisoning",
            "HTTP Request Smuggling",
        ],
        "goal": "Deep dive into complex web vulns: SSRF, deserialization, template injection, and advanced Burp workflows.",
    },
    15: {
        "title": "Malware Analysis & Reverse Engineering",
        "topics": [
            "Malware Static Analysis",
            "Malware Dynamic Analysis & Sandboxing",
            "YARA & AV Evasion (detect)",
            "Unpacking Practice",
        ],
        "goal": "Static/dynamic analysis of real malware samples; YARA rule writing; unpacking UPX, custom packers; shellcode extraction.",
    },
    16: {
        "title": "Exploit Development Fundamentals",
        "topics": [
            "Exploit Dev: Stack Overflow",
            "Exploit Dev: ROP Chains",
            "Exploit Dev: Heap & Mitigations",
            "Shellcoding Basics",
        ],
        "goal": "Buffer overflow → ROP → heap exploitation; bypass ASLR, DEP, CFG; write portable shellcode.",
    },
    17: {
        "title": "Cloud & Container Pentesting",
        "topics": [
            "Cloud IAM Abuse",
            "Kubernetes Attack Paths",
            "Terraform Misconfig Hunting",
            "Cloud & Container Pentesting",
        ],
        "goal": "IAM privilege escalation, K8s RBAC abuse, container escape, supply chain attacks on Terraform.",
    },
    18: {
        "title": "Advanced Detection Engineering",
        "topics": [
            "SIEM Queries & Sigma Rules",
            "Threat Hunting at Scale",
            "SOC Playbooks",
        ],
        "goal": "Multi-stage detection logic, behavioral analytics, MITRE ATT&CK coverage mapping, detection-as-code CI/CD.",
    },
    19: {
        "title": "Purple Team Automation & Tooling",
        "topics": [
            "Scripting & Python",
            "Red Team C2 & Infrastructure",
            "SIEM Queries & Sigma Rules",
        ],
        "goal": "Build custom C2, automated adversary emulation, detection rule generators, and purple team reporting dashboards.",
    },
    20: {
        "title": "Threat Intelligence & Attribution",
        "topics": [
            "OSINT Foundations",
            "Search & Recon Techniques",
            "Malware Static Analysis",
        ],
        "goal": "APT tracking, IOC enrichment, malware family classification, threat intel platform integration (MISP/OpenCTI).",
    },
    # Ongoing mastery weeks (21+) - rotate advanced topics
    21: {
        "title": "Ongoing: Advanced Red Team Operations",
        "topics": [
            "Red Team C2 & Infrastructure",
            "Lateral Movement & OPSEC",
            "Evasion & Defense Bypass",
        ],
        "goal": "Continuous practice: new C2 frameworks, OPSEC techniques, and evasion methods as they emerge.",
    },
    22: {
        "title": "Ongoing: Advanced Blue Team & Detection",
        "topics": [
            "SIEM Queries & Sigma Rules",
            "Threat Hunting at Scale",
            "SOC Playbooks",
        ],
        "goal": "Continuous practice: new detection rules, hunting hypotheses, and IR playbooks for emerging threats.",
    },
    23: {
        "title": "Ongoing: Cloud & Emerging Tech Security",
        "topics": [
            "Cloud IAM Abuse",
            "Kubernetes Attack Paths",
            "Cloud & Container Pentesting",
        ],
        "goal": "Continuous practice: new cloud services, K8s vulnerabilities, and container security techniques.",
    },
}


def _get_purple_team_role() -> JobRole | None:
    """Get the Purple Team Specialist role."""
    return JobRole.query.filter_by(slug="purple-team").first()


def _get_all_purple_team_topics() -> list[Topic]:
    """Get all topics mapped to the Purple Team role, DAG-ordered."""
    role = _get_purple_team_role()
    if not role:
        # Fallback: all active topics
        return Topic.query.filter_by(is_active=True).all()
    
    role_rows = (JobRoleTopic.query
                 .filter_by(job_role_id=role.id)
                 .order_by(JobRoleTopic.order_index)
                 .all())
    topics = [r.topic for r in role_rows if r.topic and r.topic.is_active]
    
    prerequisites = _topic_prerequisites_map(topics)
    return _topo_order(topics, prerequisites)


def _assign_phase_and_week(topics: list[Topic]) -> list[TopicScheduleItem]:
    """Assign each topic to a phase (job_ready/mastery) and week number.
    
    Uses the curriculum week mapping. Topics not explicitly mapped
    go to mastery phase based on their difficulty/tier.
    """
    # Build topic -> (phase, week) mapping from curriculum
    topic_to_week: dict[str, tuple[RoadmapPhase, int]] = {}
    
    # Phase 1: Job-Ready (weeks 1-12)
    for week_num, week_data in JOB_READY_WEEKS.items():
        for topic_title in week_data["topics"]:
            topic_to_week[topic_title] = (RoadmapPhase.JOB_READY, week_num)
    
    # Phase 2: Mastery (weeks 13+)
    for week_num, week_data in MASTERY_WEEKS.items():
        for topic_title in week_data["topics"]:
            topic_to_week[topic_title] = (RoadmapPhase.MASTERY, week_num)
    
    # Assign to each topic
    schedule_items: list[TopicScheduleItem] = []
    for order_idx, topic in enumerate(topics):
        phase_week = topic_to_week.get(topic.title)
        if phase_week:
            phase, week = phase_week
        else:
            # Fallback: assign based on difficulty/tier
            if topic.difficulty <= 2:
                phase, week = RoadmapPhase.JOB_READY, min(12, max(1, topic.difficulty * 3))
            else:
                phase, week = RoadmapPhase.MASTERY, 13 + (topic.difficulty - 3) * 2
        
        schedule_items.append(TopicScheduleItem(
            topic=topic,
            phase=phase,
            week_number=week,
            order_in_week=order_idx,
        ))
    
    # Sort by phase (job_ready first), then week, then order
    schedule_items.sort(key=lambda x: (
        0 if x.phase == RoadmapPhase.JOB_READY else 1,
        x.week_number,
        x.order_in_week,
    ))
    
    return schedule_items


# ---------------------------------------------------------------------------
# Item expansion: for each topic, emit RoadmapItem-equivalent dicts
# ---------------------------------------------------------------------------

def _is_vm_exercise_lab(lab: Lab) -> bool:
    return lab.provider == "vm_exercise"


def expand_topic_to_items(topic: Topic, phase: RoadmapPhase, job_role_id: int | None = None) -> list[dict]:
    """Produce a flat list of schedule items for a topic.
    
    Every topic MUST have content + labs. No skipping allowed.
    For vm_exercise labs, they include both attack and detection phases.
    """
    items: list[dict] = []
    
    # Add content items (lessons, readings, videos)
    content = (ContentItem.query
               .filter_by(topic_id=topic.id, is_active=True)
               .order_by(ContentItem.order_index)
               .all())
    for c in content:
        items.append({
            "item_type": "content_item",
            "content_item_id": c.id,
            "topic_id": topic.id,
            "estimated_minutes": c.estimated_minutes or 15,
            "title": c.title,
            "phase": phase.value,
        })
    
    # Add labs - prioritize vm_exercise for offline operation
    labs = (Lab.query
            .filter_by(topic_id=topic.id, is_active=True)
            .order_by(Lab.difficulty)
            .all())
    
    vm_exercise_labs = [l for l in labs if _is_vm_exercise_lab(l)]
    other_labs = [l for l in labs if not _is_vm_exercise_lab(l)]
    
    # vm_exercise labs come first (they're the core purple team labs)
    for lab in vm_exercise_labs:
        items.append({
            "item_type": "lab",
            "lab_id": lab.id,
            "topic_id": topic.id,
            "estimated_minutes": lab.estimated_minutes or 60,
            "title": lab.title,
            "phase": phase.value,
            "is_vm_exercise": True,
        })
    
    # Then other labs
    for lab in other_labs:
        items.append({
            "item_type": "lab",
            "lab_id": lab.id,
            "topic_id": topic.id,
            "estimated_minutes": lab.estimated_minutes or 30,
            "title": lab.title,
            "phase": phase.value,
            "is_vm_exercise": False,
        })

    # Add Checkpoint Quiz for this topic
    items.append({
        "item_type": "checkpoint_quiz",
        "topic_id": topic.id,
        "estimated_minutes": 20,
        "title": f"Checkpoint Quiz: {topic.title}",
        "phase": phase.value,
    })
    
    # If topic has no resources, still schedule a placeholder
    if not items:
        items.append({
            "item_type": "content_item",
            "topic_id": topic.id,
            "estimated_minutes": topic.estimated_minutes or 60,
            "title": f"Study: {topic.title}",
            "phase": phase.value,
        })
    
    return items


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def _append_external_resources(items: list[dict], user_id: int) -> list[dict]:
    """Append user-added (unscheduled) external resources at the end."""
    pending = (UserResource.query
                .filter_by(user_id=user_id, is_completed=False)
                .order_by(UserResource.added_at)
                .all())
    for r in pending:
        items.append({
            "item_type": "external_resource",
            "user_resource_id": r.id,
            "estimated_minutes": r.estimated_minutes or 30,
            "title": r.title,
            "phase": "custom",
        })
    return items


def _persist_roadmap(user_id: int, job_role_id: int | None,
                     scheduled: list[dict], total_minutes: int) -> Roadmap:
    """Invalidate any prior active roadmap and persist a new one + items."""
    prior = Roadmap.query.filter_by(user_id=user_id, status="active").all()
    for r in prior:
        r.status = "paused"

    roadmap = Roadmap(
        user_id=user_id,
        job_role_id=job_role_id,
        target_completion_date=scheduled[-1]["scheduled_date"] if scheduled else None,
        status="active",
        version=(max([r.version for r in prior], default=0) + 1),
    )
    db.session.add(roadmap)
    db.session.flush()

    for s in scheduled:
        item = RoadmapItem(
            roadmap_id=roadmap.id,
            item_type=s["item_type"],
            content_item_id=s.get("content_item_id"),
            lab_id=s.get("lab_id"),
            topic_id=s.get("topic_id"),
            user_resource_id=s.get("user_resource_id"),
            scheduled_date=s["scheduled_date"],
            time_slot=s.get("time_slot"),
            order_index=s["order_index"],
            estimated_minutes=s["estimated_minutes"],
            status="pending",
        )
        db.session.add(item)
    db.session.flush()
    return roadmap


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_roadmap(user_id: int, job_role_id: int | None = None,
                     start_date: date | None = None) -> Roadmap:
    """Generate the complete Zero-to-Mastery Purple Team roadmap.
    
    No assessment — everyone gets the full curriculum from zero.
    Phase 1 (weeks 1-12): Job-Ready track
    Phase 2 (week 13+): Mastery track
    """
    start = start_date or date.today()
    
    # Get all purple team topics in DAG order
    topics = _get_all_purple_team_topics()
    
    # Assign phase and week to each topic
    schedule_plan = _assign_phase_and_week(topics)
    
    # Expand each topic into roadmap items
    raw_items: list[dict] = []
    for plan_item in schedule_plan:
        topic_items = expand_topic_to_items(plan_item.topic, plan_item.phase, job_role_id)
        raw_items.extend(topic_items)
    
    # Append user's external resources
    raw_items = _append_external_resources(raw_items, user_id)
    
    # Schedule using availability and time blocks
    availability = availability_for_user(user_id, WeeklyAvailability)
    buffer_pct = float(current_app.config.get("ROADMAP_BUFFER_PERCENT", 0.15))
    
    scheduled = schedule_items(raw_items, availability,
                               user_id=user_id, model_cls=WeeklyAvailability,
                               start_date=start, buffer_percent=buffer_pct)
    
    total_minutes = sum(s["estimated_minutes"] for s in scheduled)
    return _persist_roadmap(user_id, job_role_id, scheduled, total_minutes)


def replan_roadmap(roadmap: Roadmap) -> Roadmap:
    """Re-generate the roadmap preserving completed items' progress."""
    completed = [(i.item_type, i.content_item_id, i.lab_id,
                  i.topic_id, i.user_resource_id, i.completed_at)
                 for i in roadmap.items if i.status == "done"]
    
    new_roadmap = generate_roadmap(roadmap.user_id,
                                   job_role_id=roadmap.job_role_id)
    
    # Re-match completed items onto the new plan
    for it in new_roadmap.items:
        for (itype, cid, lid, tid, urid, done_at) in completed:
            if (itype == it.item_type and cid == it.content_item_id
                    and lid == it.lab_id and tid == it.topic_id
                    and urid == it.user_resource_id):
                it.status = "done"
                it.completed_at = done_at
    db.session.flush()
    return new_roadmap


def get_roadmap_phase_info(roadmap: Roadmap) -> dict:
    """Get phase information for display in the UI."""
    job_ready_items = [i for i in roadmap.items if getattr(i, 'phase', 'job_ready') == 'job_ready' or 
                       (i.topic and any(t.title == i.topic.title for w in JOB_READY_WEEKS.values() for t in [Topic.query.filter_by(title=t).first()] if t))]
    mastery_items = [i for i in roadmap.items if i not in job_ready_items]
    
    # Calculate progress per phase
    job_ready_total = len(job_ready_items)
    job_ready_done = len([i for i in job_ready_items if i.status == "done"])
    mastery_total = len(mastery_items)
    mastery_done = len([i for i in mastery_items if i.status == "done"])
    
    return {
        "job_ready": {
            "total": job_ready_total,
            "completed": job_ready_done,
            "percentage": round((job_ready_done / job_ready_total * 100) if job_ready_total else 0, 1),
            "weeks": 12,
        },
        "mastery": {
            "total": mastery_total,
            "completed": mastery_done,
            "percentage": round((mastery_done / mastery_total * 100) if mastery_total else 0, 1),
            "weeks": "ongoing",
        },
        "current_phase": "job_ready" if job_ready_done < job_ready_total else "mastery",
    }