"""Seed roadmap.sh as a curated external curriculum reference layer.

The local curriculum remains authoritative and offline-first. This additive,
idempotent seed adds links to roadmap.sh pages that expand the matching topic.
Run directly or through seed_comprehensive.py.
"""
from __future__ import annotations

from app import app
from extensions import db
from models import ContentItem, Topic
from seed import get_or_create


ROADMAP_SH_BASE = "https://roadmap.sh"


# (local topic title, roadmap title, roadmap path, minutes)
ROADMAP_SH_RESOURCES = [
    ("Security Mindset & Ethics", "Cyber Security Expert roadmap", "/cyber-security", 30),
    ("Networking Basics", "Cyber Security Expert: networking fundamentals", "/cyber-security", 30),
    ("TCP/IP & Subnetting", "Cyber Security Expert: networking knowledge", "/cyber-security", 45),
    ("DNS & HTTP", "DevOps: DNS and HTTP fundamentals", "/devops", 30),
    ("Linux Fundamentals", "Linux Roadmap", "/linux", 45),
    ("Linux Filesystem & Permissions", "Linux: filesystem and permissions", "/linux", 30),
    ("Bash & Scripting Fundamentals", "DevOps: Bash and scripting", "/devops", 30),
    ("Processes & Services", "Linux: process and service management", "/linux", 30),
    ("Log Analysis & journald", "Linux: checking service logs", "/linux", 30),
    ("Python for Security", "Python Developer roadmap", "/python", 45),
    ("Parsing Logs & Automation", "Python: regular expressions and testing", "/python", 30),
    ("Building a Basic Port Scanner", "Python: sockets and networking", "/python", 30),
    ("Web App Basics & HTTP", "DevOps: HTTP, HTTPS and reverse proxies", "/devops", 30),
    ("Cryptographic Foundations", "Cyber Security Expert: SSL and TLS basics", "/cyber-security", 30),
    ("Active Directory Fundamentals", "Cyber Security Expert: operating systems and permissions", "/cyber-security", 30),
    ("Cloud IAM & S3 Security", "DevOps: cloud providers and infrastructure", "/devops", 45),
    ("Kubernetes Security Basics", "Kubernetes Roadmap", "/kubernetes", 45),
    ("Terraform Misconfig Hunting", "DevOps: Terraform and infrastructure as code", "/devops", 45),
]


def seed_roadmap_sh_resources() -> tuple[int, int]:
    """Add roadmap.sh references for topics that already exist."""
    added = 0
    skipped = 0

    for topic_title, resource_title, path, minutes in ROADMAP_SH_RESOURCES:
        topic = Topic.query.filter_by(title=topic_title).first()
        if topic is None:
            skipped += 1
            continue

        url = f"{ROADMAP_SH_BASE}{path}"
        item, created = get_or_create(
            ContentItem,
            defaults={
                "type": "external_link",
                "title": resource_title,
                "url": url,
                "body_markdown": (
                    f"**Source:** roadmap.sh\n\n"
                    f"Use this roadmap as a structured external reference for **{topic_title}**.\n\n"
                    f"Link: {url}"
                ),
                "estimated_minutes": minutes,
                "order_index": 20,
                "source": "external_admin",
                "is_active": True,
            },
            topic_id=topic.id,
            title=resource_title,
        )
        if not created:
            changed = False
            for field, value in (
                ("url", url),
                ("source", "external_admin"),
                ("is_active", True),
            ):
                if getattr(item, field) != value:
                    setattr(item, field, value)
                    changed = True
            if changed:
                db.session.add(item)
        else:
            added += 1

    db.session.flush()
    return added, skipped


def main() -> None:
    with app.app_context():
        added, skipped = seed_roadmap_sh_resources()
        db.session.commit()
    print(f"[OK] roadmap.sh resources seeded: {added} added, {skipped} skipped.")


if __name__ == "__main__":
    main()
