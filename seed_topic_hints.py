"""Seed TopicHint rows for the AI-tutor rules fallback (plan §7.2).

Idempotent: rows are keyed on (topic_id, hint_level). Re-seeding updates
the hint text in place so authors can iterate without manual cleanup.

Run: `py seed_topic_hints.py`
"""
from __future__ import annotations

import json

from app import app
from extensions import db
from models import Topic, TopicHint


# Authored hint sets. The trigger keywords are matched case-insensitively
# against the user's query inside services/ai_tutor_service._rules_reply.
HINTS = [
    # ---------------- Networking Basics ----------------
    ("networking-basics", [
        {"level": 1, "keywords": ["what is a packet"],
         "text": "A packet is a small chunk of data with a header carrying the source/destination addresses."},
        {"level": 1, "keywords": ["help", "hint", "stuck"],
         "text": "Start by recalling the OSI model layers. A packet lives on Layer 3 (Network)."},
        {"level": 2, "keywords": ["osi", "layers"],
         "text": "The OSI model has 7 layers: Physical → Data Link → Network → Transport → Session → Presentation → Application. TCP is Transport (L4)."},
    ]),
    # ---------------- SQL Injection ----------------
    ("sql-injection", [
        {"level": 1, "keywords": ["how", "start"],
         "text": "Try a single quote ' in the username field — if the page errors, the input is concatenated into a query."},
        {"level": 2, "keywords": ["hint", "stuck"],
         "text": "Once you confirm error-on-quote, look for a UNION SELECT payload. The classic pattern is `' UNION SELECT 1,2,3-- -`."},
        {"level": 3, "keywords": ["exfiltrate", "data", "where"],
         "text": "You can switch to a different table using `FROM information_schema.tables` to learn table names."},
    ]),
    # ---------------- XSS ----------------
    ("cross-site-scripting-xss", [
        {"level": 1, "keywords": ["reflect", "store"],
         "text": "Reflected XSS bounces your input back to you in the response. Stored XSS is saved and shown to other users."},
        {"level": 2, "keywords": ["payload", "script"],
         "text": "Try `<script>alert(1)</script>` first — if `<script>` is stripped, try `<img src=x onerror=alert(1)>`."},
    ]),
    # ---------------- Bash ----------------
    ("bash-scripting-fundamentals", [
        {"level": 1, "keywords": ["pipe", "redirect"],
         "text": "Pipe with `|`, redirect stdout with `>`, append with `>>`, redirect stderr with `2>`."},
        {"level": 2, "keywords": ["loop"],
         "text": "Bash for-loops: `for i in $(seq 1 10); do echo $i; done`."},
    ]),
    # ---------------- Exploit Dev: Stack Overflow ----------------
    ("exploit-dev-stack-overflow", [
        {"level": 1, "keywords": ["offset"],
         "text": "Use a cyclic pattern (e.g. `pattern_create`) to find which 4 bytes overwrite the saved EIP."},
        {"level": 2, "keywords": ["eip", "control"],
         "text": "Once you control EIP, choose a register/memory address you can reach — e.g. a `jmp esp` gadget — as the new return target."},
        {"level": 3, "keywords": ["shellcode"],
         "text": "Send your shellcode right after the return address; the ESP will then point at it. Don't forget the NOP sled."},
    ]),
    # ---------------- Forensics / Log Analysis ----------------
    ("log-analysis-journald", [
        {"level": 1, "keywords": ["failed", "login"],
         "text": "Filter on `Failed password` lines, then group by source IP."},
        {"level": 2, "keywords": ["brute force"],
         "text": "5+ failed attempts from the same IP within 60s is the canonical brute-force indicator."},
    ]),
]


def main() -> None:
    with app.app_context():
        added, updated = 0, 0
        for slug, hints in HINTS:
            topic = Topic.query.filter_by(slug=slug).first()
            if topic is None:
                print(f"  skip '{slug}' — topic not found")
                continue
            for h in hints:
                row = TopicHint.query.filter_by(
                    topic_id=topic.id, hint_level=h["level"]).first()
                if row is None:
                    row = TopicHint(topic_id=topic.id,
                                    hint_level=h["level"],
                                    hint_text=h["text"],
                                    trigger_keywords=json.dumps(h["keywords"]))
                    db.session.add(row)
                    added += 1
                else:
                    row.hint_text = h["text"]
                    row.trigger_keywords = json.dumps(h["keywords"])
                    row.is_active = True
                    updated += 1
        db.session.commit()
        print(f"[OK] seed_topic_hints: {added} new, {updated} updated.")


if __name__ == "__main__":
    main()
