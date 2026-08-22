"""Seed interactive in-browser exercises (plan §4 / Phase C).

Idempotent — only inserts/updates exercises by (topic, title). To keep the
launch footprint small this file ships ~12 representative exercises (1 per
Tier-0/Tier-1 topic family). Authors expand by editing this file.

Run: `py seed_exercises.py`  (after `py seed.py` has populated Topics)
"""
from __future__ import annotations

import json

from app import app
from extensions import db
from models import ContentItem, Topic


# ---------------------------------------------------------------------------
# Exercise spec authoring helpers
# ---------------------------------------------------------------------------
def by_title(slug: str):
    return Topic.query.filter_by(slug=slug).first()


# kind: code_py | regex_lab | quiz_interactive | cipher_lab | pcap_challenge | binary_inspector
EXERCISES = [
    # ---------------- code_py ----------------
    ("python-for-security", "Build a port scanner",
     "code_py",
     {"kind": "code_py",
      "prompt": "Write a function `scan(host, ports)` that returns the list of open ports (stub the socket to 'open').",
      "starter": "import socket\n\ndef scan(host, ports):\n    open_ = []\n    # TODO\n    return open_\n",
      "tests": [
          {"name": "scan returns a list", "expr": "isinstance(scan('127.0.0.1', []), list)"},
          {"name": "accepts empty input",
           "expr": "scan('127.0.0.1', []) == []"},
      ]}),

    ("log-analysis-journald", "Parse an auth.log line",
     "code_py",
     {"kind": "code_py",
      "prompt": "Implement `parse(line)` returning a dict with keys 'user' and 'action'.",
      "starter": "import re\n\ndef parse(line):\n    m = re.search(r'sshd.*for (?:invalid user )?(\\w+)', line)\n    # TODO\n    return {}\n",
      "tests": [
          {"name": "returns user from sshd line",
           "expr": "parse('Apr 1 12:00:00 host sshd[42]: Failed password for invalid user root').get('user') == 'root'"},
      ]}),

    # ---------------- regex_lab ----------------
    ("python-for-security", "Write a regex for emails",
     "regex_lab",
     {"kind": "regex_lab",
      "prompt": "Write a regex that matches simple emails like a@b.com but rejects 'foo@example' or '@example.com'",
      "starter": "^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$",
      "flags": "",
      "samples": [
          {"input": "alice@example.com", "shouldMatch": True},
          {"input": "bob@b.io",          "shouldMatch": True},
          {"input": "foo@example",       "shouldMatch": False},
          {"input": "@example.com",      "shouldMatch": False},
      ]}),

    # ---------------- quiz_interactive ----------------
    ("siem-queries-sigma-rules", "Triage a SIEM alert",
     "quiz_interactive",
     {"kind": "quiz_interactive",
      "prompt": "Branching scenario — you received an alert about a new admin login from an unusual country.",
      "scenes": [
          {"id": "start", "text": "A login to the prod-DC at 03:00 from an unknown ASN. What do you do?",
           "choices": [
               {"label": "Block the IP immediately", "next": "block"},
               {"label": "Correlate with prior logins", "next": "correlate"},
               {"label": "Dismiss it as noise",        "next": "miss"},
           ]},
          {"id": "block", "text": "You blocked the IP but the user may be locked out — and the attacker retries from another IP.",
           "outcome": "fail"},
          {"id": "correlate", "text": "You correlated logins: it is an admin working late — false positive. Document and close.",
           "outcome": "pass"},
          {"id": "miss", "text": "You dismissed — by morning the domain was ransomed.",
           "outcome": "fail"},
      ]}),

    # ---------------- cipher_lab ----------------
    ("cryptographic-foundations", "Caesar / Vigenere sandbox",
     "cipher_lab",
     {"kind": "cipher_lab",
      "prompt": "Encrypt a word with the given key (numeric = ROT, alphabetic = Vigenere).",
      "starter": "ATTACKATDAWN",
      "key": "LEMON",
      "expected": "LXFOPVEFRNHR"}),

    # ---------------- pcap_challenge ----------------
    ("packet-analysis-wireshark", "Find the C2 beacon port",
     "pcap_challenge",
     {"kind": "pcap_challenge",
      "prompt": "Download the capture, open in Wireshark, and report the destination port the C2 beacon uses.",
      "lab_title": "PCAP: discover the C2 beacon",   # resolved to lab_id at seed time
      "pcap_path": "networking/capture_challenge1.pcap",
      "questions": [{"question": "Destination port of the C2 beacon?",
                     "expected": "4444"}]}),

    # ---------------- binary_inspector ----------------
    ("binary-hex-number-systems", "Find the hidden marker",
     "binary_inspector",
     {"kind": "binary_inspector",
      "prompt": "Open the bundled binary in a hex viewer (xxd / HxD) and find the 4-byte marker.",
      "lab_title": "Exploit dev: stack overflow PoC",  # resolved to lab_id
      "binary_path": "exploit_dev/stack_overflow_binary.exe",
      "marker_hex": "DEADBEEF"}),
]


def main() -> None:
    from models import Lab
    with app.app_context():
        n_added, n_updated = 0, 0
        for topic_slug, title, kind_type, spec in EXERCISES:
            topic = by_title(topic_slug)
            if topic is None:
                print(f"  skip '{title}' — topic '{topic_slug}' not found")
                continue
            # Resolve optional lab_title -> lab_id for templates that need it
            if "lab_title" in spec:
                lab = Lab.query.filter_by(title=spec["lab_title"]).first()
                if lab:
                    spec["lab_id"] = lab.id
                spec.pop("lab_title", None)
            item = ContentItem.query.filter_by(
                topic_id=topic.id, title=title).first()
            if item is None:
                item = ContentItem(topic_id=topic.id, title=title,
                                    type="interactive_exercise",
                                    source="in_house",
                                    estimated_minutes=20)
                db.session.add(item)
                n_added += 1
            else:
                n_updated += 1
            item.exercise_spec = json.dumps(spec)
            item.type = "interactive_exercise"
            item.is_active = True
            # Helpful inline body so non-interactive listings still show something.
            item.body_markdown = f"Interactive exercise: {kind_type} — {spec.get('prompt','')[:200]}"
            # Give them stable order indices so they show after lesson_md content.
            existing = ContentItem.query.filter_by(topic_id=topic.id).count()
            item.order_index = existing
        db.session.commit()
        print(f"[OK] seed_exercises: {n_added} new, {n_updated} updated.")


if __name__ == "__main__":
    main()
