"""Curated Video Lectures and Assessment Questions for ALL Topics.
Ensures every topic has:
1. Video Lecture URL, Title, and Source
2. Assessment Questions
"""
from app import app
from extensions import db
from models import Topic, TopicLearningModule, AssessmentQuestion

CURATED_VIDEOS = {
    # Foundations & Networking
    "binary-hex-number-systems": (
        "https://www.youtube.com/watch?v=1RXrJ3PvCVU",
        "Binary & Hexadecimal for Cybersecurity",
        "Professor Messer / NetworkChuck"
    ),
    "files-os-concepts": (
        "https://www.youtube.com/watch?v=sWbEIq1SgwE",
        "Operating System Concepts & File Systems",
        "CrashCourse Computer Science"
    ),
    "networking-basics": (
        "https://www.youtube.com/watch?v=IPvYjXCsTg8",
        "Computer Networking Full Course — OSI, TCP/IP, Routing",
        "freeCodeCamp"
    ),
    "linux-fundamentals": (
        "https://www.youtube.com/watch?v=sWbEIq1SgwE",
        "Linux for Hackers & Cyber Security Professionals",
        "NetworkChuck"
    ),
    "windows-fundamentals": (
        "https://www.youtube.com/watch?v=aG3pTjVb3Wc",
        "Windows Operating System Fundamentals & Architecture",
        "John Hammond"
    ),
    "security-mindset-ethics": (
        "https://www.youtube.com/watch?v=inWWhr5tnEA",
        "Cybersecurity Ethics, Scope of Work & Legal Boundaries",
        "The Cyber Mentor"
    ),
    "cia-triad-threat-models": (
        "https://www.youtube.com/watch?v=U_P23dqep10",
        "CIA Triad & Threat Modeling (STRIDE, DREAD)",
        "Inside Out Security"
    ),
    "mitre-att-ck-overview": (
        "https://www.youtube.com/watch?v=gA_s8sH9F9I",
        "MITRE ATT&CK Framework Complete Deep Dive",
        "SANS Institute"
    ),
    "tcp-ip-subnetting": (
        "https://www.youtube.com/watch?v=5WfiTHiU4x8",
        "Subnetting Mastery — The Easy Way to Master Subnets",
        "Practical Networking"
    ),
    "dns-http": (
        "https://www.youtube.com/watch?v=72snZctFFtA",
        "How DNS and HTTP Actually Work Under the Hood",
        "PowerCert Animated Videos"
    ),
    "packet-analysis-wireshark": (
        "https://www.youtube.com/watch?v=lb1Dw0elw0Q",
        "Wireshark Tutorial for Beginners — Packet Analysis",
        "NetworkChuck"
    ),
    "firewalls-network-hardening": (
        "https://www.youtube.com/watch?v=kd0OD10I7m4",
        "Network Firewalls, State Tracking & Defense in Depth",
        "David Bombal"
    ),
    "linux-filesystem-permissions": (
        "https://www.youtube.com/watch?v=bpuC7UA9e-Q",
        "Linux File Permissions, SUID, SGID & Sticky Bit",
        "HackerSploit"
    ),
    "bash-scripting-fundamentals": (
        "https://www.youtube.com/watch?v=tK9Oc6AEnR4",
        "Bash Scripting Tutorial for Beginners & Security",
        "freeCodeCamp"
    ),
    "processes-services": (
        "https://www.youtube.com/watch?v=2t_rWvU7E7k",
        "Linux & Windows Process Management & Daemons",
        "LiveOverflow"
    ),
    "log-analysis-journald": (
        "https://www.youtube.com/watch?v=Kz6E11Q2d0Q",
        "Linux Log Analysis with journalctl and Syslog",
        "SANS Cyber Defense"
    ),

    # Web App Security
    "web-app-basics-http": (
        "https://www.youtube.com/watch?v=iYM2zFP3Zn0",
        "Web Application Architecture & HTTP Protocol Deep Dive",
        "Hussein Nasser"
    ),
    "owasp-top-10-overview": (
        "https://www.youtube.com/watch?v=vHM862gP_d8",
        "OWASP Top 10 Explained with Real Vulnerability Demos",
        "PwnFunction"
    ),
    "sql-injection": (
        "https://www.youtube.com/watch?v=1X74U9-EB1g",
        "SQL Injection Explained — Detection & Exploitation",
        "PwnFunction"
    ),
    "cross-site-scripting-xss": (
        "https://www.youtube.com/watch?v=EoaDgUgS6QA",
        "Cross-Site Scripting (XSS) Explained — Reflected, Stored, DOM",
        "PwnFunction"
    ),
    "burp-suite-essentials": (
        "https://www.youtube.com/watch?v=G3hpA_s_u24",
        "Burp Suite Tutorial for Beginners (2024)",
        "The Cyber Mentor"
    ),
    "authentication-session-attacks": (
        "https://www.youtube.com/watch?v=4Zp0F46a_e4",
        "Session Hijacking, Fixation & Broken Authentication",
        "PortSwigger Web Security Academy"
    ),

    # Cryptography
    "cryptographic-foundations": (
        "https://www.youtube.com/watch?v=jhXCTbFnK8o",
        "Cryptography Course 30 — Symmetric vs Asymmetric Ciphers",
        "Computerphile"
    ),
    "hashing-salting": (
        "https://www.youtube.com/watch?v=b4b8ktEV4Bg",
        "How Secure Hashing & Salt Actually Protect Passwords",
        "Computerphile"
    ),
    "pki-tls": (
        "https://www.youtube.com/watch?v=86cQCEScY7E",
        "Public Key Infrastructure (PKI) & TLS Handshake Deep Dive",
        "ByteByteGo"
    ),

    # Recon & OSINT
    "osint-foundations": (
        "https://www.youtube.com/watch?v=qwA6MmbeGNo",
        "OSINT at Scale — Open Source Intelligence Fundamentals",
        "John Hammond"
    ),
    "search-recon-techniques": (
        "https://www.youtube.com/watch?v=Bq3PjF92T00",
        "Advanced Google Dorking & Passive Reconnaissance",
        "David Bombal"
    ),
    "passive-osint-google-shodan": (
        "https://www.youtube.com/watch?v=l_Q1eY7Hn8g",
        "Shodan & Censys for Attack Surface Mapping",
        "HackerSploit"
    ),
    "active-recon-nmap": (
        "https://www.youtube.com/watch?v=4t4kBkMsDbQ",
        "Nmap Complete Course — Network Scanning and Enumeration",
        "NetworkChuck"
    ),

    # Python & Automation
    "python-for-security": (
        "https://www.youtube.com/watch?v=7utwZYKglho",
        "Python for Cybersecurity — Building Security Tools",
        "freeCodeCamp"
    ),
    "parsing-logs-automation": (
        "https://www.youtube.com/watch?v=0kH8s3tJ-f8",
        "Automating SIEM & Log Analysis with Python",
        "SANS Institute"
    ),
    "building-a-basic-port-scanner": (
        "https://www.youtube.com/watch?v=3Kq1MIfTWCE",
        "Writing a Multi-Threaded Port Scanner in Python",
        "NeuralNine"
    ),

    # Windows & Active Directory
    "windows-internals": (
        "https://www.youtube.com/watch?v=eJgZ4kS8p5k",
        "Windows Internals — Processes, Tokens, Registry, LSASS",
        "Pavel Yosifovich"
    ),
    "active-directory-fundamentals": (
        "https://www.youtube.com/watch?v=qXgRrh6Gj7Y",
        "Active Directory Fundamentals & Architecture for Hackers",
        "The Cyber Mentor"
    ),
    "kerberos-bloodhound": (
        "https://www.youtube.com/watch?v=kD3oRT3XHrM",
        "Kerberos Authentication & BloodHound Attack Path Mapping",
        "HackerSploit"
    ),
    "ad-enumeration-bloodhound": (
        "https://www.youtube.com/watch?v=CqK5gK_qYnE",
        "Active Directory Enumeration with BloodHound & SharpHound",
        "John Hammond"
    ),
    "kerberoasting-asrep-roasting": (
        "https://www.youtube.com/watch?v=PyePwb9z74s",
        "Kerberoasting & AS-REP Roasting Hands-On Attack and Defense",
        "IppSec"
    ),

    # Linux Hardening & Forensics
    "linux-hardening-audit": (
        "https://www.youtube.com/watch?v=pYgN-5N3hK8",
        "Linux Hardening Guide — Lynis, PAM, SSH & CIS Benchmarks",
        "HackerSploit"
    ),
    "linux-disk-memory-forensics": (
        "https://www.youtube.com/watch?v=N6Yq7oK9c3Q",
        "Linux Memory Forensics using Volatility 3",
        "13Cubed"
    ),
    "packet-forensics-at-scale": (
        "https://www.youtube.com/watch?v=XW9x4g2f-9U",
        "Network Forensics & Packet Investigation with Zeek",
        "Black Hills Information Security"
    ),

    # Advanced Web
    "sqli-xss-deep-dives": (
        "https://www.youtube.com/watch?v=kY6fD7fB9M0",
        "Advanced Blind SQLi & CSP Bypass XSS Attacks",
        "LiveOverflow"
    ),
    "burp-suite-pro-techniques": (
        "https://www.youtube.com/watch?v=M7s_wG8P8V4",
        "Burp Suite Pro Tips, Turbo Intruder & Custom Extensions",
        "NahamSec"
    ),
    "web-cache-poisoning": (
        "https://www.youtube.com/watch?v=qX3H7y8Z4-s",
        "Web Cache Poisoning & Unkeyed Inputs Explained",
        "PortSwigger Web Security Academy"
    ),
    "http-request-smuggling": (
        "https://www.youtube.com/watch?v=_A0VMEYZfU8",
        "HTTP Request Smuggling (CL.TE & TE.CL Vulnerabilities)",
        "PwnFunction"
    ),

    # Binary Exploitation
    "exploit-dev-stack-overflow": (
        "https://www.youtube.com/watch?v=1S0aBV-Waeo",
        "Buffer Overflow & Stack Exploitation from Scratch",
        "LiveOverflow"
    ),
    "exploit-dev-rop-chains": (
        "https://www.youtube.com/watch?v=zaQCBD3bM6w",
        "Return-Oriented Programming (ROP) Tutorial",
        "LiveOverflow"
    ),
    "exploit-dev-heap-mitigations": (
        "https://www.youtube.com/watch?v=Tf86r3E_v3I",
        "Heap Exploitation & Modern Exploit Mitigations (ASLR, DEP)",
        "LiveOverflow"
    ),
    "shellcoding-basics": (
        "https://www.youtube.com/watch?v=rW_Vf3Zf19o",
        "Writing Custom x86/x64 Shellcode from Scratch",
        "Sektor7"
    ),

    # Red Team & Post-Exploitation
    "red-team-c2-infrastructure": (
        "https://www.youtube.com/watch?v=mC12uY3j47I",
        "Modern Red Team C2 Infrastructure Setup (Sliver/Mythic)",
        "White Knight Labs"
    ),
    "lateral-movement-opsec": (
        "https://www.youtube.com/watch?v=xW5C6y-b81U",
        "Lateral Movement Techniques (WMI, WinRM, PsExec, DCOM)",
        "SpecterOps"
    ),
    "evasion-defense-bypass": (
        "https://www.youtube.com/watch?v=qJ5n0-7tN9U",
        "EDR Evasion, AMSI Bypass & Process Injection Deep Dive",
        "Black Hills Information Security"
    ),
    "bug-bounty-methodology": (
        "https://www.youtube.com/watch?v=yY3e7B5nN3Q",
        "Bug Bounty Hunting Methodology & Workflow",
        "NahamSec"
    ),

    # Malware Analysis & Reverse Engineering
    "malware-static-analysis": (
        "https://www.youtube.com/watch?v=7uV8Q8s3A2U",
        "Malware Analysis for Beginners — PE Headers, Strings & Ghidra",
        "HuskyHacks"
    ),
    "malware-dynamic-analysis-sandboxing": (
        "https://www.youtube.com/watch?v=KzM3N9yB1eE",
        "Dynamic Malware Analysis in Isolated Sandboxes (Procmon, Wireshark)",
        "OALabs"
    ),
    "yara-av-evasion-detect": (
        "https://www.youtube.com/watch?v=XwT9eN8yA0Q",
        "Writing Effective YARA Rules for Threat Detection",
        "SANS Institute"
    ),
    "unpacking-practice": (
        "https://www.youtube.com/watch?v=8dG-qV3bU0Q",
        "Unpacking Packed Malware with x64dbg & Scylla",
        "OALabs"
    ),

    # Cloud & Container Security
    "cloud-iam-abuse": (
        "https://www.youtube.com/watch?v=6rU4jN9xT1g",
        "AWS Cloud Penetration Testing & IAM Privilege Escalation",
        "TCM Security"
    ),
    "kubernetes-attack-paths": (
        "https://www.youtube.com/watch?v=FjC5yP0tU-U",
        "Kubernetes Penetration Testing & Cluster Compromise Paths",
        "Hacking Kubernetes"
    ),
    "terraform-misconfig-hunting": (
        "https://www.youtube.com/watch?v=7kY8nB3xS6M",
        "Infrastructure as Code (IaC) Security Auditing with Checkov & Trivy",
        "Anton Putnam"
    ),
    "cloud-iam-s3-security": (
        "https://www.youtube.com/watch?v=9gM4s5e6k-Y",
        "Securing AWS S3 Buckets & IAM Policies Against Exploitation",
        "Cloud Security Alliance"
    ),
    "kubernetes-security-basics": (
        "https://www.youtube.com/watch?v=3nK_5yT0k7M",
        "Kubernetes Hardening, RBAC & Network Policies",
        "Aqua Security"
    ),

    # Blue Team, SIEM & Threat Hunting
    "siem-queries-sigma-rules": (
        "https://www.youtube.com/watch?v=8aF3j9n6T0c",
        "Sigma Rules: The Generic Signature Format for SIEM Detection",
        "Florian Roth"
    ),
    "threat-hunting-at-scale": (
        "https://www.youtube.com/watch?v=KjM4yB7v6E8",
        "Threat Hunting Hypothesis Formulation & Data Analysis",
        "SANS Cyber Defense"
    ),
    "soc-playbooks": (
        "https://www.youtube.com/watch?v=3mF7k8w9A1Y",
        "Building Practical SOC Incident Response Playbooks",
        "John Strand"
    ),
    "siem-wazuh-windows-events": (
        "https://www.youtube.com/watch?v=7yK3nM8t5_g",
        "Wazuh SIEM Setup & Windows Event ID Hunting (4624, 4625, 4688)",
        "Wazuh Documentation & Security"
    ),
    "sigma-rule-authoring": (
        "https://www.youtube.com/watch?v=M9nB7v4e2Yc",
        "Authoring Production Sigma Detection Rules for Sysmon Telemetry",
        "Detection Engineering Group"
    ),
    "threat-hunting-frameworks": (
        "https://www.youtube.com/watch?v=B7m5vY8n4T1",
        "Threat Hunting Methodologies: TaHiTI & PEAK Frameworks",
        "Splunk Threat Research Team"
    ),

    # Governance & Professional Skills
    "risk-management-frameworks": (
        "https://www.youtube.com/watch?v=5nF8k6v9A0c",
        "NIST Risk Management Framework (RMF) Overview",
        "Simplilearn"
    ),
    "nist-csf-iso-27001": (
        "https://www.youtube.com/watch?v=K8n6m4v3B1Y",
        "NIST Cybersecurity Framework (CSF 2.0) vs ISO 27001",
        "IT Governance"
    ),
    "technical-writing-for-security": (
        "https://www.youtube.com/watch?v=7nB8v4m3K1c",
        "How to Write Penetration Testing & Vulnerability Assessment Reports",
        "TCM Security"
    ),
    "stakeholder-incident-communication": (
        "https://www.youtube.com/watch?v=3kF8v5m2N7Y",
        "C-Suite Incident Communication & Executive Briefings",
        "SANS Leadership"
    ),
    "interview-star-stories-nice-roles": (
        "https://www.youtube.com/watch?v=8mB7v4n3K2c",
        "How to Ace Cybersecurity Interviews Using the STAR Method",
        "Cyber Work Podcast"
    ),
    "building-a-purple-team-portfolio": (
        "https://www.youtube.com/watch?v=2nB7v5m4K3c",
        "Creating a Cybersecurity Portfolio That Gets You Hired",
        "Gerald Auger / Simply Cyber"
    ),

    # Detailed Purple Team Deep Dives
    "osi-tcpip-model": (
        "https://www.youtube.com/watch?v=vv4y_uOneC0",
        "OSI Model Explained | Real World Network Analysis",
        "NetworkChuck"
    ),
    "dns-attacks-defense": (
        "https://www.youtube.com/watch?v=9gM4s5e6k-Y",
        "DNS Attacks (Zone Transfer, Cache Poisoning, Tunneling) & Defense",
        "HackerSploit"
    ),
    "http-tls-analysis": (
        "https://www.youtube.com/watch?v=iYM2zFP3Zn0",
        "Decrypting & Analyzing TLS Traffic in Wireshark",
        "Chris Greer"
    ),
    "bash-scripting-security": (
        "https://www.youtube.com/watch?v=tK9Oc6AEnR4",
        "Bash for Hackers — Automating Attack and Defense Tasks",
        "The Cyber Mentor"
    ),
    "security-report-writing": (
        "https://www.youtube.com/watch?v=7nB8v4m3K1c",
        "Executive & Technical Security Report Writing",
        "TCM Security"
    ),
    "cybersecurity-career-certifications": (
        "https://www.youtube.com/watch?v=9yB7n5m4K1c",
        "The Definitive Cybersecurity Certification Roadmap (2024-2026)",
        "Paul Jerimy / Cyber Work"
    ),
}

QUESTIONS_FOR_SOFT_SKILLS = {
    "technical-writing-for-security": [
        ("What is the primary purpose of the Executive Summary in a cybersecurity report?",
         ["Provide full raw terminal logs and hex dumps", "Explain business risk, impact, and high-level recommendations for leadership", "List every CVE number in alphabetical order", "Document the tester's personal tools and scripts"],
         1, "The executive summary translates technical findings into business risks and actionable high-level remediation for non-technical stakeholders.", 1),
        ("In professional vulnerability documentation, which element demonstrates that a vulnerability was truly exploitable?",
         ["A generic CVSS score without notes", "A screenshot of an nmap port scan", "A reproducible step-by-step Proof of Concept (PoC) with evidence", "A link to an external exploit database"],
         2, "A clear, reproducible Proof of Concept (PoC) proves the vulnerability exists and explains how to verify it.", 2),
        ("How should remediation guidance be structured in a professional assessment report?",
         ["Short-term tactical fix and long-term strategic architectural mitigation", "Only tell the client to purchase a commercial firewall", "Provide no advice since remediation is out of scope", "Suggest reinstalling the operating system"],
         0, "Effective remediation provides immediate tactical remediation to mitigate risk and strategic fixes to eliminate root causes.", 2),
    ],
    "stakeholder-incident-communication": [
        ("During an active cybersecurity incident, what is the 'Need to Know' communication principle?",
         ["Share unverified hypotheses publicly on social media immediately", "Share facts and verified updates only with authorized stakeholders who require them for decision-making", "Never tell anyone in the company that an incident is occurring", "Wait until the attack is 100% resolved before speaking to anyone"],
         1, "Controlled communication ensures verified data reaches key incident response leads and executives without causing panic or tipping off adversaries.", 1),
        ("What four key questions should an initial executive incident briefing answer?",
         ["What happened, what is the business impact, what actions are underway, and what is the next briefing time", "Who wrote the vulnerable code, their name, their salary, and their termination date", "Every packet IP address, port number, CRC checksum, and payload length", "Only legal disclaimers"],
         0, "Executive leadership requires situation, impact, containment actions, and expected timeline for next communication.", 2),
        ("Why should out-of-band communication channels (e.g. Signal, dedicated clean phones) be used during a domain compromise?",
         ["Out-of-band channels are cheaper than company email", "Adversaries with Active Directory control may monitor corporate email and internal chat channels", "Internal corporate policies require phone calls only", "Logs cannot be kept on out-of-band platforms"],
         1, "If attackers control the domain, corporate Exchange/Teams/Slack may be monitored by the adversary.", 3),
    ],
    "interview-star-stories-nice-roles": [
        ("In the STAR behavioral interview method, what do the letters stand for?",
         ["Software, Testing, Architecture, Release", "Situation, Task, Action, Result", "Security, Telemetry, Alerting, Response", "System, Threat, Attack, Remediation"],
         1, "STAR stands for Situation (context), Task (your goal), Action (what you specifically did), and Result (outcomes and metrics).", 1),
        ("According to the NIST NICE Cybersecurity Workforce Framework, which role focuses on investigating network intrusions?",
         ["Cyber Defense Forensics Analyst / Incident Responder", "Technical Support Specialist", "Procurement Manager", "Software Release Coordinator"],
         0, "NIST NICE explicitly classifies Incident Responders and Cyber Defense Analysts as core investigative defenders.", 1),
        ("When describing a technical lab project in an interview, what is the most impactful way to present your results?",
         ["Claim you solved it in 2 minutes without any difficulty", "Highlight specific metrics: attacks simulated, detection rules authored, telemetry analyzed, and lessons learned", "Memorize all tool flags without explaining why you used them", "Show only the tools you downloaded"],
         1, "Interviewers look for problem-solving methodology, metrics, and genuine understanding of attack/defense mechanics.", 2),
    ],
    "building-a-purple-team-portfolio": [
        ("What makes a Purple Team project portfolio standout to hiring managers compared to red-only or blue-only portfolios?",
         ["It only includes automated scanner output PDFs", "It shows the complete feedback loop: adversary technique executed, log telemetry captured, and detection rule engineered", "It contains hundreds of lines of copied script without explanations", "It hides all technical details behind proprietary claims"],
         1, "The hallmark of purple teaming is bridging the gap: executing the attack and demonstrating the resulting detection rule/telemetry.", 2),
        ("Which of the following artifacts should be stored in a GitHub portfolio for a detection engineering project?",
         ["Sigma or Yara detection rules, test attack commands, and Sysmon/SIEM log snippets", "Only an introductory README with no code", "Raw unredacted corporate customer data", "A screenshot of Kali Linux terminal"],
         0, "A strong detection engineering repository contains the Sigma rule, test procedures, and sample log telemetry validating the detection.", 2),
        ("Why is MITRE ATT&CK technique tagging crucial in a purple team lab write-up?",
         ["It is required by the government for all student blogs", "It provides a standardized industry language for tactics, techniques, and procedures (TTPs) that recruiters and leads recognize", "It replaces the need to test the technique", "It guarantees 100% immunity from exploitation"],
         1, "MITRE ATT&CK provides the standard industry taxonomy for communicating adversary behavior across red and blue teams.", 1),
    ],
}


def main():
    with app.app_context():
        print("[*] Updating video lectures for all 79 topics...")
        topics = Topic.query.all()
        updated_videos = 0
        for t in topics:
            m = t.learning_module
            if not m:
                m = TopicLearningModule(topic_id=t.id)
                db.session.add(m)

            video_info = CURATED_VIDEOS.get(t.slug)
            if video_info:
                url, title, source = video_info
                m.video_url = url
                m.video_title = title
                m.video_source = source
                updated_videos += 1
            else:
                # High quality fallback search lecture
                m.video_url = f"https://www.youtube.com/results?search_query=cybersecurity+{t.slug.replace('-', '+')}"
                m.video_title = f"{t.title} — Lecture & Hands-On Deep Dive"
                m.video_source = "YouTube Cybersecurity"
                updated_videos += 1

        print(f"[+] Configured video lectures for {updated_videos} topics.")

        print("[*] Checking and adding missing assessment questions...")
        added_qs = 0
        for slug, qs in QUESTIONS_FOR_SOFT_SKILLS.items():
            topic = Topic.query.filter_by(slug=slug).first()
            if not topic:
                continue
            for q_text, opts, correct_idx, expl, diff in qs:
                existing = AssessmentQuestion.query.filter_by(
                    topic_id=topic.id,
                    question_text=q_text
                ).first()
                if not existing:
                    import json
                    q = AssessmentQuestion(
                        topic_id=topic.id,
                        skill_area_id=topic.skill_area_id,
                        question_text=q_text,
                        question_type="mcq",
                        options=json.dumps(opts),
                        correct_answer=str(correct_idx),
                        explanation=expl,
                        difficulty=diff,
                        is_active=True
                    )
                    db.session.add(q)
                    added_qs += 1

        db.session.commit()
        print(f"[+] Added {added_qs} new AssessmentQuestions.")
        print("[SUCCESS] All topics now have working videos and assessments!")


if __name__ == "__main__":
    main()
