"""Seed offline (bundled) labs (plan §5 / Phase D).

Adds `Lab` rows with provider='self_hosted_offline' whose
url_or_container_ref points at a path under bundles/labs/. Each row's
`flag_hash` is the SHA-256 of the expected flag so the existing
submit() route can verify it offline.

Idempotent — matched by (title). Run: `py seed_offline_labs.py`
"""
from __future__ import annotations

import hashlib
import json

from app import app
from extensions import db
from models import Lab, Topic


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# (title, topic_slug, bundle_path, difficulty, minutes, xp, proof, flag, mitre)
OFFLINE_LABS = [
    ("PCAP: discover the C2 beacon",
     "packet-analysis-wireshark", "networking/capture_challenge1.pcap",
     2, 30, 25, "flag", "flag{c2_beacon_4444}", "T1071"),
    ("PCAP: find the exfil channel",
     "packet-forensics-at-scale", "networking/exfil_capture.pcap",
     3, 45, 35, "flag", "flag{dns_exfil_via Resolver}", "T1048"),
    ("Linux auth.log: spot the brute force",
     "log-analysis-journald", "linux/auth.log",
     1, 20, 20, "flag", "flag{5_attempts_root}", "T1110"),
    ("Web: find 5 OWASP vulns in source",
     "owasp-top-10-overview", "web/vuln_app_source.zip",
     2, 45, 35, "writeup_url", "", "T1190"),
    ("Crypto: crack the hashes",
     "hashing-salting", "crypto/hashes_challenge.txt",
     2, 30, 25, "flag", "flag{rainbow_beats_repetition}", None),
    ("Crypto: RSA small-exponent challenge",
     "pki-tls", "crypto/rsa_challenge.pem",
     3, 60, 40, "flag", "flag{e=3_cuberoot_attack}", None),
    ("OSINT: corporate target recon",
     "search-recon-techniques", "osint/simulated_target_archive.zip",
     2, 45, 30, "writeup_url", "", "T1582"),
    ("Windows: NTDS hash extraction",
     "kerberos-bloodhound", "windows_ad/simulated_ntds.dit",
     3, 60, 40, "flag", "flag{gold_ticket_krbtgt}", "T1003"),
    ("Windows: BloodHound graph walkthrough",
     "kerberos-bloodhound", "windows_ad/bloodhound_export.json",
     3, 45, 35, "writeup_url", "", "T1087"),
    ("Exploit dev: stack overflow PoC",
     "exploit-dev-stack-overflow", "exploit_dev/stack_overflow_binary.exe",
     4, 90, 90, "flag", "flag{ret_to_buffer}", "T1055"),
    ("Malware: write the YARA rule",
     "yara-av-evasion-detect", "malware/yara_challenge.yar",
     3, 60, 45, "writeup_url", "", "T1027"),
    ("Mini-CTF bundle (30 challenges)",
     "owasp-top-10-overview", "ctf/mini_ctf_bundle.zip",
     3, 120, 100, "flag", "flag{mini_ctf_complete}", None),
]


def main() -> None:
    with app.app_context():
        added, updated = 0, 0
        for title, topic_slug, bundle, diff, mins, xp, proof, flag, mitre in OFFLINE_LABS:
            topic = Topic.query.filter_by(slug=topic_slug).first()
            if topic is None:
                print(f"  skip '{title}' — topic '{topic_slug}' not found")
                continue
            lab = Lab.query.filter_by(title=title).first()
            if lab is None:
                lab = Lab(topic_id=topic.id, title=title,
                          description=f"Offline bundled challenge: {bundle}")
                db.session.add(lab)
                added += 1
            else:
                updated += 1
            lab.provider = "self_hosted_offline"
            lab.url_or_container_ref = bundle
            lab.difficulty = diff
            lab.estimated_minutes = mins
            lab.xp_reward = xp
            lab.proof_type = proof
            lab.flag_hash = sha256(flag) if flag else None
            lab.mitre_techniques = json.dumps([mitre]) if mitre else None
            lab.is_active = True
        db.session.commit()
        print(f"[OK] seed_offline_labs: {added} new, {updated} updated.")


if __name__ == "__main__":
    main()
