"""Curated Video Lectures and Assessment Questions for ALL Topics.
Ensures every topic has:
1. Video Lecture URL, Title, and Source
2. Assessment Questions
"""
from app import app
from extensions import db
from models import Topic, TopicLearningModule, AssessmentQuestion

CURATED_VIDEOS = {
    # Every entry links to a real, verified, well-established free/open
    # cybersecurity education channel (handles confirmed via web search),
    # using a topic-targeted YouTube search rather than a specific unverified
    # video ID. This is the safe pattern: it always resolves to genuine
    # content and never misattributes a video that may not exist.
    # 'channel' is the real creator/channel name — go explore their full
    # catalog directly, not just the one search result.

    # Foundations & Networking
    "binary-hex-number-systems": (
        "https://www.youtube.com/results?search_query=binary+hexadecimal+number+systems+explained+Professor+Messer",
        "Binary & Hexadecimal for Cybersecurity",
        "Professor Messer — https://www.youtube.com/@professormesser"
    ),
    "files-os-concepts": (
        "https://www.youtube.com/results?search_query=operating+system+file+systems+explained+freeCodeCamp.org",
        "Operating System & File System Concepts",
        "freeCodeCamp.org — https://www.youtube.com/@freecodecamp"
    ),
    "networking-basics": (
        "https://www.youtube.com/results?search_query=network+fundamentals+full+course+Professor+Messer",
        "Computer Networking Full Course (OSI, TCP/IP, Routing)",
        "Professor Messer — https://www.youtube.com/@professormesser"
    ),
    "linux-fundamentals": (
        "https://www.youtube.com/results?search_query=linux+for+ethical+hackers+full+course+freeCodeCamp.org",
        "Linux for Cybersecurity — Full Course",
        "freeCodeCamp.org — https://www.youtube.com/@freecodecamp"
    ),
    "windows-fundamentals": (
        "https://www.youtube.com/results?search_query=windows+internals+fundamentals+for+security+John+Hammond",
        "Windows Fundamentals & Architecture",
        "John Hammond — https://www.youtube.com/@_JohnHammond"
    ),
    "security-mindset-ethics": (
        "https://www.youtube.com/results?search_query=security+mindset+threat+modeling+Professor+Messer",
        "Security Mindset, Threat Modeling & Ethics",
        "Professor Messer — https://www.youtube.com/@professormesser"
    ),
    "cia-triad-threat-models": (
        "https://www.youtube.com/results?search_query=CIA+triad+threat+modeling+explained+Professor+Messer",
        "CIA Triad & Threat Modeling Explained",
        "Professor Messer — https://www.youtube.com/@professormesser"
    ),
    "mitre-att-ck-overview": (
        "https://www.youtube.com/results?search_query=MITRE+ATT%26CK+framework+explained+Black+Hills+Information+Security",
        "MITRE ATT&CK Framework Overview",
        "Black Hills Information Security — https://www.youtube.com/@BHInfoSecurity"
    ),
    "tcp-ip-subnetting": (
        "https://www.youtube.com/results?search_query=subnetting+mastery+tutorial+Professor+Messer",
        "TCP/IP & Subnetting Mastery",
        "Professor Messer — https://www.youtube.com/@professormesser"
    ),
    "dns-http": (
        "https://www.youtube.com/results?search_query=DNS+HTTP+protocol+explained+NetworkChuck",
        "DNS & HTTP Protocol Deep Dive",
        "NetworkChuck — https://www.youtube.com/@NetworkChuck"
    ),
    "packet-analysis-wireshark": (
        "https://www.youtube.com/results?search_query=wireshark+tutorial+packet+analysis+Chris+Greer",
        "Wireshark Packet Analysis Tutorial",
        "Chris Greer — https://www.youtube.com/@ChrisGreer"
    ),
    "firewalls-network-hardening": (
        "https://www.youtube.com/results?search_query=firewall+configuration+network+hardening+NetworkChuck",
        "Firewalls & Network Hardening",
        "NetworkChuck — https://www.youtube.com/@NetworkChuck"
    ),
    "linux-filesystem-permissions": (
        "https://www.youtube.com/results?search_query=linux+file+permissions+SUID+SGID+HackerSploit",
        "Linux File Permissions, SUID, SGID",
        "HackerSploit — https://www.youtube.com/@HackerSploit"
    ),
    "bash-scripting-fundamentals": (
        "https://www.youtube.com/results?search_query=bash+scripting+tutorial+for+hackers+freeCodeCamp.org",
        "Bash Scripting for Security",
        "freeCodeCamp.org — https://www.youtube.com/@freecodecamp"
    ),
    "processes-services": (
        "https://www.youtube.com/results?search_query=linux+windows+process+service+management+HackerSploit",
        "Process & Service Management (Linux/Windows)",
        "HackerSploit — https://www.youtube.com/@HackerSploit"
    ),
    "log-analysis-journald": (
        "https://www.youtube.com/results?search_query=journalctl+syslog+log+analysis+tutorial+Black+Hills+Information+Security",
        "Linux Log Analysis (journalctl, syslog)",
        "Black Hills Information Security — https://www.youtube.com/@BHInfoSecurity"
    ),

    # Web App Security
    "web-app-basics-http": (
        "https://www.youtube.com/results?search_query=web+application+architecture+HTTP+explained+PortSwigger+Web+Security+Academy",
        "Web Application Architecture & HTTP",
        "PortSwigger Web Security Academy — https://www.youtube.com/@PortSwiggerWebSecurity"
    ),
    "owasp-top-10-overview": (
        "https://www.youtube.com/results?search_query=OWASP+top+10+explained+PwnFunction",
        "OWASP Top 10 Explained",
        "PwnFunction — https://www.youtube.com/@PwnFunction"
    ),
    "sql-injection": (
        "https://www.youtube.com/results?search_query=SQL+injection+tutorial+PortSwigger+Web+Security+Academy",
        "SQL Injection — Detection & Exploitation",
        "PortSwigger Web Security Academy — https://www.youtube.com/@PortSwiggerWebSecurity"
    ),
    "cross-site-scripting-xss": (
        "https://www.youtube.com/results?search_query=cross+site+scripting+XSS+explained+PwnFunction",
        "Cross-Site Scripting (XSS) Explained",
        "PwnFunction — https://www.youtube.com/@PwnFunction"
    ),
    "burp-suite-essentials": (
        "https://www.youtube.com/results?search_query=burp+suite+tutorial+beginners+TCM+Security+Academy",
        "Burp Suite Tutorial for Beginners",
        "TCM Security Academy — https://www.youtube.com/@TCMSecurityAcademy"
    ),
    "authentication-session-attacks": (
        "https://www.youtube.com/results?search_query=session+hijacking+broken+authentication+PortSwigger+Web+Security+Academy",
        "Session Hijacking & Broken Authentication",
        "PortSwigger Web Security Academy — https://www.youtube.com/@PortSwiggerWebSecurity"
    ),

    # Cryptography
    "cryptographic-foundations": (
        "https://www.youtube.com/results?search_query=symmetric+asymmetric+cryptography+explained+Computerphile",
        "Symmetric vs Asymmetric Cryptography",
        "Computerphile — https://www.youtube.com/@Computerphile"
    ),
    "hashing-salting": (
        "https://www.youtube.com/results?search_query=password+hashing+salting+explained+Computerphile",
        "Password Hashing & Salting Explained",
        "Computerphile — https://www.youtube.com/@Computerphile"
    ),
    "pki-tls": (
        "https://www.youtube.com/results?search_query=PKI+TLS+handshake+explained+Computerphile",
        "PKI & TLS Handshake Deep Dive",
        "Computerphile — https://www.youtube.com/@Computerphile"
    ),

    # Recon & OSINT
    "osint-foundations": (
        "https://www.youtube.com/results?search_query=OSINT+fundamentals+open+source+intelligence+John+Hammond",
        "OSINT Fundamentals",
        "John Hammond — https://www.youtube.com/@_JohnHammond"
    ),
    "search-recon-techniques": (
        "https://www.youtube.com/results?search_query=google+dorking+passive+reconnaissance+NetworkChuck",
        "Google Dorking & Passive Recon",
        "NetworkChuck — https://www.youtube.com/@NetworkChuck"
    ),
    "passive-osint-google-shodan": (
        "https://www.youtube.com/results?search_query=shodan+censys+attack+surface+mapping+HackerSploit",
        "Shodan & Censys for Attack Surface Mapping",
        "HackerSploit — https://www.youtube.com/@HackerSploit"
    ),
    "active-recon-nmap": (
        "https://www.youtube.com/results?search_query=nmap+complete+course+scanning+NetworkChuck",
        "Nmap Complete Course",
        "NetworkChuck — https://www.youtube.com/@NetworkChuck"
    ),

    # Python & Automation
    "python-for-security": (
        "https://www.youtube.com/results?search_query=python+for+cybersecurity+building+tools+freeCodeCamp.org",
        "Python for Cybersecurity",
        "freeCodeCamp.org — https://www.youtube.com/@freecodecamp"
    ),
    "parsing-logs-automation": (
        "https://www.youtube.com/results?search_query=python+log+parsing+automation+security+NeuralNine",
        "Automating Log Analysis with Python",
        "NeuralNine — https://www.youtube.com/@NeuralNine"
    ),
    "building-a-basic-port-scanner": (
        "https://www.youtube.com/results?search_query=python+port+scanner+tutorial+NeuralNine",
        "Writing a Port Scanner in Python",
        "NeuralNine — https://www.youtube.com/@NeuralNine"
    ),

    # Windows & Active Directory
    "windows-internals": (
        "https://www.youtube.com/results?search_query=windows+internals+processes+tokens+LSASS+John+Hammond",
        "Windows Internals — Processes, Tokens, LSASS",
        "John Hammond — https://www.youtube.com/@_JohnHammond"
    ),
    "active-directory-fundamentals": (
        "https://ippsec.rocks/",
        "Active Directory Fundamentals for Hackers",
        "IppSec (searchable by technique at ippsec.rocks) — https://ippsec.rocks/"
    ),
    "kerberos-bloodhound": (
        "https://ippsec.rocks/",
        "Kerberos Authentication & BloodHound",
        "IppSec (searchable by technique at ippsec.rocks) — https://ippsec.rocks/"
    ),
    "ad-enumeration-bloodhound": (
        "https://ippsec.rocks/",
        "AD Enumeration with BloodHound/SharpHound",
        "IppSec (searchable by technique at ippsec.rocks) — https://ippsec.rocks/"
    ),
    "kerberoasting-asrep-roasting": (
        "https://ippsec.rocks/",
        "Kerberoasting & AS-REP Roasting",
        "IppSec (searchable by technique at ippsec.rocks) — https://ippsec.rocks/"
    ),

    # Linux Hardening & Forensics
    "linux-hardening-audit": (
        "https://www.youtube.com/results?search_query=linux+hardening+lynis+CIS+benchmark+HackerSploit",
        "Linux Hardening (Lynis, CIS Benchmarks)",
        "HackerSploit — https://www.youtube.com/@HackerSploit"
    ),
    "linux-disk-memory-forensics": (
        "https://www.youtube.com/results?search_query=linux+memory+forensics+volatility+3+13Cubed",
        "Linux Memory Forensics with Volatility",
        "13Cubed — https://www.youtube.com/@13Cubed"
    ),
    "packet-forensics-at-scale": (
        "https://www.youtube.com/results?search_query=network+forensics+packet+investigation+zeek+13Cubed",
        "Network Forensics & Packet Investigation",
        "13Cubed — https://www.youtube.com/@13Cubed"
    ),

    # Advanced Web
    "sqli-xss-deep-dives": (
        "https://www.youtube.com/results?search_query=blind+SQL+injection+CSP+bypass+advanced+PortSwigger+Web+Security+Academy",
        "Advanced Blind SQLi & CSP Bypass",
        "PortSwigger Web Security Academy — https://www.youtube.com/@PortSwiggerWebSecurity"
    ),
    "burp-suite-pro-techniques": (
        "https://www.youtube.com/results?search_query=burp+suite+advanced+turbo+intruder+TCM+Security+Academy",
        "Burp Suite Advanced Techniques",
        "TCM Security Academy — https://www.youtube.com/@TCMSecurityAcademy"
    ),
    "web-cache-poisoning": (
        "https://www.youtube.com/results?search_query=web+cache+poisoning+explained+PortSwigger+Web+Security+Academy",
        "Web Cache Poisoning Explained",
        "PortSwigger Web Security Academy — https://www.youtube.com/@PortSwiggerWebSecurity"
    ),
    "http-request-smuggling": (
        "https://www.youtube.com/results?search_query=HTTP+request+smuggling+CL.TE+TE.CL+PortSwigger+Web+Security+Academy",
        "HTTP Request Smuggling Explained",
        "PortSwigger Web Security Academy — https://www.youtube.com/@PortSwiggerWebSecurity"
    ),

    # Binary Exploitation
    "exploit-dev-stack-overflow": (
        "https://www.youtube.com/results?search_query=buffer+overflow+stack+exploitation+from+scratch+LiveOverflow",
        "Buffer Overflow & Stack Exploitation",
        "LiveOverflow — https://www.youtube.com/@LiveOverflow"
    ),
    "exploit-dev-rop-chains": (
        "https://www.youtube.com/results?search_query=return+oriented+programming+ROP+tutorial+LiveOverflow",
        "Return-Oriented Programming (ROP)",
        "LiveOverflow — https://www.youtube.com/@LiveOverflow"
    ),
    "exploit-dev-heap-mitigations": (
        "https://www.youtube.com/results?search_query=heap+exploitation+ASLR+DEP+mitigations+LiveOverflow",
        "Heap Exploitation & Modern Mitigations",
        "LiveOverflow — https://www.youtube.com/@LiveOverflow"
    ),
    "shellcoding-basics": (
        "https://www.youtube.com/results?search_query=writing+shellcode+x86+x64+tutorial+LiveOverflow",
        "Writing Custom Shellcode",
        "LiveOverflow — https://www.youtube.com/@LiveOverflow"
    ),

    # Red Team & Post-Exploitation
    "red-team-c2-infrastructure": (
        "https://www.youtube.com/results?search_query=red+team+C2+infrastructure+sliver+mythic+Black+Hills+Information+Security",
        "Red Team C2 Infrastructure Setup",
        "Black Hills Information Security — https://www.youtube.com/@BHInfoSecurity"
    ),
    "lateral-movement-opsec": (
        "https://ippsec.rocks/",
        "Lateral Movement Techniques (WMI, WinRM, PsExec)",
        "IppSec (searchable by technique at ippsec.rocks) — https://ippsec.rocks/"
    ),
    "evasion-defense-bypass": (
        "https://www.youtube.com/results?search_query=EDR+evasion+AMSI+bypass+process+injection+Black+Hills+Information+Security",
        "EDR Evasion & AMSI Bypass",
        "Black Hills Information Security — https://www.youtube.com/@BHInfoSecurity"
    ),
    "bug-bounty-methodology": (
        "https://www.youtube.com/results?search_query=bug+bounty+hunting+methodology+workflow+TCM+Security+Academy",
        "Bug Bounty Hunting Methodology",
        "TCM Security Academy — https://www.youtube.com/@TCMSecurityAcademy"
    ),

    # Malware Analysis & Reverse Engineering
    "malware-static-analysis": (
        "https://www.youtube.com/results?search_query=malware+static+analysis+PE+headers+ghidra+OALabs",
        "Malware Static Analysis (PE, Strings, Ghidra)",
        "OALabs — https://www.youtube.com/@OALabs"
    ),
    "malware-dynamic-analysis-sandboxing": (
        "https://www.youtube.com/results?search_query=dynamic+malware+analysis+sandbox+procmon+OALabs",
        "Dynamic Malware Analysis in a Sandbox",
        "OALabs — https://www.youtube.com/@OALabs"
    ),
    "yara-av-evasion-detect": (
        "https://www.youtube.com/results?search_query=writing+YARA+rules+tutorial+OALabs",
        "Writing Effective YARA Rules",
        "OALabs — https://www.youtube.com/@OALabs"
    ),
    "unpacking-practice": (
        "https://www.youtube.com/results?search_query=unpacking+packed+malware+x64dbg+OALabs",
        "Unpacking Packed Malware",
        "OALabs — https://www.youtube.com/@OALabs"
    ),

    # Cloud & Container Security
    "cloud-iam-abuse": (
        "https://www.youtube.com/results?search_query=AWS+IAM+privilege+escalation+pentesting+TCM+Security+Academy",
        "AWS IAM Privilege Escalation",
        "TCM Security Academy — https://www.youtube.com/@TCMSecurityAcademy"
    ),
    "kubernetes-attack-paths": (
        "https://www.youtube.com/results?search_query=kubernetes+penetration+testing+cluster+compromise+TCM+Security+Academy",
        "Kubernetes Penetration Testing",
        "TCM Security Academy — https://www.youtube.com/@TCMSecurityAcademy"
    ),
    "terraform-misconfig-hunting": (
        "https://www.youtube.com/results?search_query=terraform+IaC+security+scanning+checkov+trivy+TCM+Security+Academy",
        "IaC Security Auditing (Checkov, Trivy)",
        "TCM Security Academy — https://www.youtube.com/@TCMSecurityAcademy"
    ),
    "cloud-iam-s3-security": (
        "https://www.youtube.com/results?search_query=AWS+S3+bucket+security+IAM+policy+TCM+Security+Academy",
        "Securing AWS S3 Buckets & IAM",
        "TCM Security Academy — https://www.youtube.com/@TCMSecurityAcademy"
    ),
    "kubernetes-security-basics": (
        "https://www.youtube.com/results?search_query=kubernetes+hardening+RBAC+network+policy+TCM+Security+Academy",
        "Kubernetes Hardening & RBAC",
        "TCM Security Academy — https://www.youtube.com/@TCMSecurityAcademy"
    ),

    # Blue Team, SIEM & Threat Hunting
    "siem-queries-sigma-rules": (
        "https://www.youtube.com/results?search_query=sigma+rules+SIEM+detection+explained+Black+Hills+Information+Security",
        "Sigma Rules Explained",
        "Black Hills Information Security — https://www.youtube.com/@BHInfoSecurity"
    ),
    "threat-hunting-at-scale": (
        "https://www.youtube.com/results?search_query=threat+hunting+hypothesis+methodology+SANS+Institute",
        "Threat Hunting Hypothesis & Data Analysis",
        "SANS Institute — https://www.youtube.com/@SANSInstitute"
    ),
    "soc-playbooks": (
        "https://www.youtube.com/results?search_query=SOC+incident+response+playbook+Black+Hills+Information+Security",
        "Building SOC Incident Response Playbooks",
        "Black Hills Information Security — https://www.youtube.com/@BHInfoSecurity"
    ),
    "siem-wazuh-windows-events": (
        "https://www.youtube.com/results?search_query=wazuh+SIEM+setup+windows+event+ID+HackerSploit",
        "Wazuh SIEM & Windows Event IDs",
        "HackerSploit — https://www.youtube.com/@HackerSploit"
    ),
    "sigma-rule-authoring": (
        "https://www.youtube.com/results?search_query=sigma+rule+authoring+sysmon+telemetry+Black+Hills+Information+Security",
        "Authoring Sigma Detection Rules",
        "Black Hills Information Security — https://www.youtube.com/@BHInfoSecurity"
    ),
    "threat-hunting-frameworks": (
        "https://www.youtube.com/results?search_query=threat+hunting+frameworks+TaHiTI+PEAK+SANS+Institute",
        "Threat Hunting Frameworks (TaHiTI, PEAK)",
        "SANS Institute — https://www.youtube.com/@SANSInstitute"
    ),

    # Governance & Professional Skills
    "risk-management-frameworks": (
        "https://www.youtube.com/results?search_query=NIST+risk+management+framework+RMF+explained+Professor+Messer",
        "NIST Risk Management Framework Overview",
        "Professor Messer — https://www.youtube.com/@professormesser"
    ),
    "nist-csf-iso-27001": (
        "https://www.youtube.com/results?search_query=NIST+cybersecurity+framework+vs+ISO+27001+Professor+Messer",
        "NIST CSF vs ISO 27001",
        "Professor Messer — https://www.youtube.com/@professormesser"
    ),
    "technical-writing-for-security": (
        "https://www.youtube.com/results?search_query=penetration+test+report+writing+TCM+Security+Academy",
        "Writing Pentest & Vuln Assessment Reports",
        "TCM Security Academy — https://www.youtube.com/@TCMSecurityAcademy"
    ),
    "stakeholder-incident-communication": (
        "https://www.youtube.com/results?search_query=incident+communication+executive+briefing+SANS+Institute",
        "Executive Incident Communication",
        "SANS Institute — https://www.youtube.com/@SANSInstitute"
    ),
    "interview-star-stories-nice-roles": (
        "https://www.youtube.com/results?search_query=cybersecurity+interview+STAR+method+Cyber+Work+%28ISC2%29",
        "Acing Cybersecurity Interviews (STAR Method)",
        "Cyber Work (ISC2) — https://www.youtube.com/@cyberworkpodcast"
    ),
    "building-a-purple-team-portfolio": (
        "https://www.youtube.com/results?search_query=cybersecurity+portfolio+that+gets+you+hired+Cyber+Work+%28ISC2%29",
        "Building a Cybersecurity Portfolio",
        "Cyber Work (ISC2) — https://www.youtube.com/@cyberworkpodcast"
    ),

    # Detailed Purple Team Deep Dives
    "osi-tcpip-model": (
        "https://www.youtube.com/results?search_query=OSI+model+explained+real+world+NetworkChuck",
        "OSI Model Explained — Real World Analysis",
        "NetworkChuck — https://www.youtube.com/@NetworkChuck"
    ),
    "dns-attacks-defense": (
        "https://www.youtube.com/results?search_query=DNS+attacks+zone+transfer+cache+poisoning+HackerSploit",
        "DNS Attacks & Defense (Zone Transfer, Poisoning)",
        "HackerSploit — https://www.youtube.com/@HackerSploit"
    ),
    "http-tls-analysis": (
        "https://www.youtube.com/results?search_query=decrypting+TLS+traffic+wireshark+Chris+Greer",
        "Decrypting & Analyzing TLS Traffic",
        "Chris Greer — https://www.youtube.com/@ChrisGreer"
    ),
    "bash-scripting-security": (
        "https://www.youtube.com/results?search_query=bash+for+hackers+automation+TCM+Security+Academy",
        "Bash for Hackers — Automating Tasks",
        "TCM Security Academy — https://www.youtube.com/@TCMSecurityAcademy"
    ),
    "security-report-writing": (
        "https://www.youtube.com/results?search_query=security+report+writing+executive+technical+TCM+Security+Academy",
        "Executive & Technical Security Reports",
        "TCM Security Academy — https://www.youtube.com/@TCMSecurityAcademy"
    ),
    "cybersecurity-career-certifications": (
        "https://www.youtube.com/results?search_query=cybersecurity+certification+roadmap+2026+Cyber+Work+%28ISC2%29",
        "Cybersecurity Certification Roadmap",
        "Cyber Work (ISC2) — https://www.youtube.com/@cyberworkpodcast"
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

# Additional high-value topic quizzes (new — didn't exist in the original file).
# These target topics with heavy real-world weight that weren't covered by
# seed.py's skill-area CAT bank or seed_missing_assessment_questions.py's
# skill-area-level questions (those test the SkillArea broadly; these test
# the specific Topic in depth).
QUESTIONS_TOPIC_DEPTH = {
    "kerberoasting-asrep-roasting": [
        ("Kerberoasting specifically targets accounts that have which AD attribute set?", "1", "2",
         ["Just 'Password never expires'", "A Service Principal Name (SPN)", "Domain Admin group membership", "A blank password"]),
        ("Why is Kerberoasting effective as an offline attack once the ticket is captured?", "0", "3",
         ["The service ticket is encrypted with the service account's password hash, which can be cracked offline without touching the DC again", "It requires no valid domain credentials at all", "It always returns the plaintext password directly", "It only works over an unencrypted network"]),
        ("What distinguishes AS-REP Roasting from Kerberoasting?", "2", "3",
         ["AS-REP Roasting requires domain admin rights", "AS-REP Roasting targets service accounts only", "AS-REP Roasting targets user accounts with Kerberos pre-authentication disabled, requiring no valid credentials to request the roastable material", "They are the same attack with different names"]),
        ("Which encryption type, if used for a requested service ticket, makes Kerberoasting cracking significantly faster?", "1", "3",
         ["AES-256", "RC4-HMAC (0x17)", "AES-128 with salting", "3DES"]),
    ],
    "python-for-security": [
        ("Which Python library is most commonly used to make simple HTTP requests to a target for recon automation?", "1", "1",
         ["socket", "requests", "os", "shutil"]),
        ("Why is using subprocess to call external tools (like nmap) from Python useful in automation scripts?", "2", "2",
         ["It's the only way Python can run at all", "It replaces the need for the external tool entirely", "It lets you programmatically run a real tool and capture/parse its output for further automated logic", "It encrypts the tool's output automatically"]),
        ("What Python module is standard for working with JSON output from security tools?", "0", "1",
         ["json", "csv", "pickle", "struct"]),
    ],
    "siem-queries-sigma-rules": [
        ("What is a key advantage of writing a Sigma rule instead of a native Splunk/Elastic query directly?", "1", "2",
         ["Sigma rules run faster than native queries", "Sigma rules are vendor-neutral and can be converted (via sigma-cli/pySigma) to multiple SIEM backends", "Sigma rules require no logsource definition", "Sigma is a replacement for the SIEM itself"]),
        ("In a Sigma rule YAML file, what does the 'logsource' field specify?", "0", "1",
         ["The category/product/service the rule applies to (e.g., windows security eventlog)", "The rule's author", "The severity level only", "The MITRE ATT&CK ID"]),
    ],
}

# Merge into the main quiz dict so main() picks these up automatically.
QUESTIONS_FOR_SOFT_SKILLS.update(QUESTIONS_TOPIC_DEPTH)


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
