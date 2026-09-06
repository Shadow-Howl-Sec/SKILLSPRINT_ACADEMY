# Purple Team Mastery Curriculum
## SkillSprint Academy - Comprehensive Learning Roadmap

---

## Curriculum Overview

This curriculum transforms a beginner into a proficient Purple Team operator capable of executing offensive security assessments while building robust defensive detection capabilities. The program follows a structured 48-week pathway divided into six mastery domains, each building upon the previous.

### Prerequisites
- Basic computer literacy
- High school mathematics
- Familiarity with at least one operating system
- Ethical mindset and commitment to authorized testing only

### Time Commitment
- **Minimum:** 15 hours/week (3 hours/day, 5 days/week)
- **Accelerated:** 25 hours/week (5 hours/day, 5 days/week)
- **Total Learning Hours:** ~720 hours (48 weeks at 15 hrs/week)

---

## Domain 1: Computer Networking Fundamentals
**Weeks 1-8 | Mastery Hours: 120**

### Learning Objectives
Upon completion, the learner will be able to:
- Explain the OSI 7-layer model and TCP/IP stack in detail
- Analyze network traffic using Wireshark and tcpdump
- Configure and troubleshoot network connectivity
- Understand DNS, DHCP, HTTP/HTTPS, SSH protocols
- Perform subnetting calculations (IPv4 and IPv6)
- Design secure network architectures with proper segmentation

### Sub-Topics & Modules

#### 1.1 OSI Model & TCP/IP Stack (Week 1-2)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| OSI 7-Layer Architecture | 8 | Can draw and explain all 7 layers without reference |
| TCP/IP 4-Layer Model | 6 | Maps TCP/IP to OSI layers |
| Packet Encapsulation | 6 | Trace data through encapsulation/decapsulation |
| Protocol Data Units (PDUs) | 4 | Explain PDU transformations at each layer |

#### 1.2 Network Fundamentals (Week 2-3)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| Ethernet & MAC Addressing | 6 | Analyze ARP requests/replies in Wireshark |
| IPv4 Addressing & Subnetting | 12 | Calculate subnets, CIDR notation fluently |
| IPv6 Fundamentals | 6 | Explain IPv6 address types and autoconfiguration |
| Default Gateways & Routing | 6 | Trace packet path using traceroute |
| NAT & PAT | 4 | Explain how NAT preserves address space |

#### 1.3 Transport Layer Protocols (Week 3-4)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| TCP 3-Way Handshake | 6 | Analyze SYN, SYN-ACK, ACK in packet capture |
| TCP State Machine | 6 | Explain connection states and transitions |
| UDP vs TCP Comparison | 4 | Select appropriate protocol for scenarios |
| Port Numbers & Sockets | 4 | Identify well-known ports 0-1023 |
| TCP Flags & Window Size | 6 | Interpret URG, ACK, PSH, RST, SYN, FIN |

#### 1.4 Application Layer (Week 4-5)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| DNS Resolution | 8 | Trace DNS queries (A, AAAA, MX, TXT, PTR) |
| HTTP/HTTPS Protocol | 10 | Analyze HTTP methods, headers, status codes |
| DHCP Operation | 4 | Capture and explain DORA process |
| SSH & Remote Access | 6 | Establish encrypted remote sessions |
| Email Protocols (SMTP, IMAP, POP) | 4 | Trace email flow |

#### 1.5 Network Analysis & Tools (Week 5-6)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| Wireshark Advanced Usage | 10 | Create display and capture filters |
| tcpdump & tshark | 6 | Capture traffic from CLI |
| Packet Analysis Techniques | 8 | Identify normal vs anomalous traffic |
| Network Segmentation | 6 | Design VLAN architecture |
| Firewall Rules & ACLs | 6 | Configure iptables/nftables |

#### 1.6 Wireless Networking (Week 7)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| 802.11 Standards | 4 | Compare a/b/g/n/ac/ax |
| WLAN Security (WEP, WPA, WPA2, WPA3) | 6 | Audit wireless security configurations |
| Wireless Reconnaissance | 4 | Discover and map wireless networks |
| Bluetooth Security | 2 | Identify Bluetooth attack surfaces |

#### 1.7 Network Security Architecture (Week 8)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| DMZ Architecture | 4 | Design three-tier network |
| Zero Trust Architecture | 4 | Explain ZTA principles |
| Proxy & Reverse Proxy | 4 | Configure forward and reverse proxies |
| VPN Technologies | 6 | Implement site-to-site and remote access VPN |

### Assessment
- **Checkpoint Quiz:** OSI/TCP-IP knowledge
- **Lab Exercise:** Analyze full HTTP session in Wireshark
- **Capstone:** Design a secure network for a mid-size organization

---

## Domain 2: Linux Administration & Command Line
**Weeks 9-16 | Mastery Hours: 140**

### Learning Objectives
Upon completion, the learner will be able to:
- Navigate and manage files in Linux from the command line
- Write and debug Bash scripts for automation
- Manage users, groups, and permissions securely
- Configure and harden Linux services
- Monitor system resources and diagnose performance issues
- Implement logging and auditing per security best practices

### Sub-Topics & Modules

#### 2.1 Linux Fundamentals (Week 9-10)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| Linux History & Distributions | 4 | Compare RHEL, Debian, Arch use cases |
| Filesystem Hierarchy Standard (FHS) | 6 | Navigate /etc, /var, /usr, /home |
| Essential Commands (ls, cp, mv, rm, chmod, chown) | 10 | Perform file operations without reference |
| Text Processing (cat, grep, sed, awk) | 10 | Parse logs and config files |
| Package Management (apt, yum, dnf) | 6 | Install, update, remove software |

#### 2.2 User & Group Management (Week 10-11)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| User Accounts (/etc/passwd, /etc/shadow) | 6 | Add, modify, delete users |
| Group Management | 4 | Manage supplementary groups |
| Sudo & Privilege Escalation | 8 | Configure sudo access securely |
| PAM Configuration | 6 | Implement authentication policies |
| Password Policies | 4 | Set aging, complexity requirements |

#### 2.3 Process & Service Management (Week 11-12)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| Process Lifecycle | 6 | Monitor and manage processes |
| systemd & SysVinit | 8 | Create and manage services |
| cron & at Scheduling | 6 | Automate tasks securely |
| Systemd Journal & rsyslog | 6 | Configure centralized logging |
| Resource Limits (ulimit, cgroups) | 4 | Prevent resource exhaustion |

#### 2.4 Networking in Linux (Week 12-13)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| Network Configuration (ip, nmcli) | 6 | Configure interfaces statically |
| firewall & nftables | 10 | Create firewall rules |
| SSHD Hardening | 6 | Secure SSH configurations |
| Network Diagnostics (ss, netstat, ping) | 4 | Troubleshoot connectivity |
| Linux as Router | 4 | Configure IP forwarding |

#### 2.5 Storage & Filesystem Management (Week 13-14)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| Filesystem Types (ext4, xfs, btrfs) | 6 | Select appropriate filesystems |
| LVM Configuration | 6 | Create and manage logical volumes |
| Disk Quotas | 4 | Enforce storage limits |
| Mounting & /etc/fstab | 4 | Automount filesystems |
| RAID Configuration | 6 | Implement software RAID |

#### 2.6 Security Hardening (Week 14-15)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| SELinux & AppArmor | 8 | Configure and troubleshoot |
| Kernel Hardening | 6 | Tune kernel parameters |
| AIDE & Tripwire | 6 | Implement file integrity monitoring |
| Linux Audit Framework | 6 | Configure audit rules |
| Container Security (Docker) | 8 | Secure container deployments |

#### 2.7 Scripting & Automation (Week 15-16)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| Bash Scripting Fundamentals | 10 | Write scripts with conditionals/loops |
| Advanced Bash (functions, arrays) | 8 | Create modular scripts |
| Python for Sysadmins | 10 | Automate with Python |
| Ansible Basics | 6 | Write basic playbooks |
| Git for Version Control | 4 | Manage configuration as code |

### Assessment
- **Checkpoint Quiz:** Linux administration concepts
- **Lab Exercise:** Configure a hardened LAMP server
- **Capstone:** Build an automated hardening script for RHEL/CentOS

---

## Domain 3: Information Gathering & Reconnaissance
**Weeks 17-22 | Mastery Hours: 100**

### Learning Objectives
Upon completion, the learner will be able to:
- Conduct comprehensive reconnaissance using passive and active techniques
- Perform OSINT using industry-standard tools and methodologies
- Enumerate network resources and identify potential attack surfaces
- Gather intelligence on targets for authorized security assessments
- Document findings in professional reports

### Sub-Topics & Modules

#### 3.1 OSINT Fundamentals (Week 17-18)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| OSINT Framework & Methodology | 6 | Plan reconnaissance approach |
| Search Engine Discovery | 8 | Use advanced Google hacking |
| WHOIS & DNS Enumeration | 8 | Extract DNS records and ownership |
| Social Media Intelligence | 6 | Analyze public social profiles |
| Email Harvesting & Leak Databases | 4 | Find email addresses |

#### 3.2 Network Reconnaissance (Week 18-19)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| Host Discovery Techniques | 6 | Identify live hosts |
| Port Scanning with Nmap | 10 | Perform comprehensive port scans |
| Service & Version Detection | 6 | Identify running services |
| OS Fingerprinting | 4 | Determine target OS |
| Nmap Scripting Engine (NSE) | 8 | Run vulnerability scripts |

#### 3.3 Web Application Reconnaissance (Week 19-20)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| Web Crawling & Spidering | 6 | Map web application structure |
| Directory Enumeration | 6 | Discover hidden files/directories |
| Parameter Discovery | 4 | Find injectable parameters |
| WAF Detection & Fingerprinting | 4 | Identify protection mechanisms |
| Burp Suite Professional | 10 | Use proxy for web testing |

#### 3.4 Cloud Reconnaissance (Week 20-21)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| AWS Reconnaissance | 8 | Enumerate S3, EC2, IAM |
| Azure & GCP OSINT | 6 | Discover cloud resources |
| Cloud Metadata Endpoints | 4 | Exploit IMDS |
| Cloud Service Enumeration | 4 | Find misconfigured buckets |

#### 3.5 Threat Intelligence (Week 21-22)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| MITRE ATT&CK Framework | 6 | Map techniques to tactics |
| Threat Actor Profiling | 4 | Analyze adversary TTPs |
| OSINT Automation (theHarvester, Recon-ng) | 6 | Automate reconnaissance |
| Data Feeds & Threat Intel Sources | 4 | Integrate threat intelligence |
| Footprinting Documentation | 6 | Create professional reports |

### Assessment
- **Checkpoint Quiz:** OSINT techniques and tools
- **Lab Exercise:** Complete reconnaissance on lab environment
- **Capstone:** Produce comprehensive OSINT report on fictional target

---

## Domain 4: Red Team Operations
**Weeks 23-34 | Mastery Hours: 200**

### Learning Objectives
Upon completion, the learner will be able to:
- Execute comprehensive penetration tests against network infrastructure
- Exploit web application vulnerabilities using manual techniques
- Perform post-exploitation activities including lateral movement
- Maintain access using various persistence techniques
- Execute coordinated red team operations with C2 infrastructure
- Bypass common security controls and detection mechanisms

### Sub-Topics & Modules

#### 4.1 Exploitation Fundamentals (Week 23-24)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| Exploitation Lifecycle | 6 | Explain attack chain |
| Metasploit Framework | 10 | Use msfvenom and Meterpreter |
| Exploit Development Basics | 8 | Understand stack overflows |
| Buffer Overflows (Linux x86) | 12 | Exploit simple buffer overflow |
| Shellcode Writing | 8 | Write position-independent shellcode |

#### 4.2 Network Penetration Testing (Week 24-26)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| SMB/NetBIOS Exploitation | 8 | Attack Windows shares |
| LDAP & Active Directory Attacks | 10 | Exploit AD misconfigurations |
| Pass-the-Hash & Token Passing | 8 | Lateral movement techniques |
| Remote Services (RDP, SSH, VNC) | 8 | Attack remote access |
| WNP & Rogue Access Points | 4 | Wireless attacks |

#### 4.3 Web Application Attacks (Week 26-28)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| SQL Injection (In-Band, Blind, Time-Based) | 12 | Exploit SQL databases |
| Cross-Site Scripting (Reflected, Stored, DOM) | 10 | Execute client-side attacks |
| CSRF & IDOR | 6 | Exploit authorization flaws |
| File Inclusion & Upload Vulnerabilities | 8 | Achieve RCE via file ops |
| Command Injection | 6 | Exploit OS command injection |

#### 4.4 Post-Exploitation (Week 28-30)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| Windows Post-Exploitation | 10 | Collect credentials, persist |
| Linux Post-Exploitation | 8 | Maintain access on Linux |
| Credential Dumping (Mimikatz, LSASS) | 8 | Extract credentials |
| Kerberoasting & Golden Tickets | 8 | AD persistence techniques |
| Lateral Movement Strategies | 8 | Move through network |

#### 4.5 Red Team Operations (Week 30-32)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| C2 Infrastructure (Cobalt Strike, Mythic) | 10 | Set up C2 servers |
| Domain Fronting & Redirection | 6 | Hide C2 traffic |
| Phishing & Social Engineering | 10 | Execute spear phishing |
| Physical Security Testing | 6 | Bypass physical controls |
| Supply Chain Attacks | 4 | Attack development pipeline |

#### 4.6 Evasion & Anti-Forensics (Week 32-34)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| Antivirus Evasion | 8 | Bypass AV signatures |
| Logging Evasion & Clearing | 6 | Cover tracks |
| Lateral Movement Detection Avoidance | 8 | Bypass EDR |
| Traffic Tunneling & Port Forwarding | 8 | Pivot through networks |
| Data Exfiltration Techniques | 6 | Steal data covertly |

### Assessment
- **Checkpoint Quiz:** Exploitation techniques and methodologies
- **Lab Exercise:** Complete boot2root challenges (HackTheBox tier 2)
- **Capstone:** Execute full red team engagement against lab infrastructure

---

## Domain 5: Blue Team Operations & Detection Engineering
**Weeks 35-44 | Mastery Hours: 180**

### Learning Objectives
Upon completion, the learner will be able to:
- Deploy and configure SIEM systems for log collection and analysis
- Develop detection rules using Sigma and SIEM query languages
- Perform threat hunting using hypothesis-driven approaches
- Conduct digital forensics and incident response
- Implement defense-in-depth architectures
- Measure security posture using purple team exercises

### Sub-Topics & Modules

#### 5.1 SIEM Fundamentals (Week 35-36)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| SIEM Architecture & Deployment | 8 | Design SIEM architecture |
| Log Sources & Normalization | 8 | Configure log forwarding |
| Splunk Search Processing Language | 10 | Write SPL queries |
| Elastic Stack (Elasticsearch, Logstash, Kibana) | 10 | Manage ELK stack |
| Log Correlation & Alerting | 6 | Create correlation alerts |

#### 5.2 Detection Engineering (Week 36-38)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| Sigma Rules Development | 10 | Write and test Sigma rules |
| MITRE ATT&CK Mapping | 8 | Map detections to ATT&CK |
| Wazuh & Open Source SIEM | 10 | Deploy Wazuh rules |
| YARA Rule Writing | 8 | Create YARA signatures |
| Detection Logic & Tuning | 8 | Reduce false positives |

#### 5.3 Endpoint Detection & Response (Week 38-39)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| EDR Architecture & Telemetry | 8 | Understand endpoint visibility |
| Sysmon Configuration | 10 | Configure Sysmon for detection |
| Memory Forensics (Volatility) | 10 | Analyze memory dumps |
| Malicious Process Detection | 8 | Identify rogue processes |
| Persistence Mechanism Detection | 6 | Find autorun malware |

#### 5.4 Threat Hunting (Week 39-41)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| Hypothesis-Driven Hunting | 8 | Structure hunt operations |
| Data Sources for Hunting | 8 | Identify hunting data needs |
| Hunting Frameworks (Sqrrl, MITRE) | 6 | Apply hunting methodology |
| Indicator of Compromise (IOC) Hunting | 8 | Hunt using IOCs |
| Anomaly Detection & Baselines | 6 | Establish behavioral baselines |

#### 5.5 Incident Response (Week 41-43)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| NIST Incident Response Lifecycle | 8 | Apply NIST framework |
| Digital Forensics Fundamentals | 10 | Collect and preserve evidence |
| Windows Event Log Analysis | 10 | Interpret Windows security logs |
| Network Forensics & PCAP Analysis | 8 | Analyze network traffic |
| Malware Analysis Basics | 8 | Analyze suspicious files |

#### 5.6 Purple Team Exercises (Week 43-44)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| Attack Simulation & Detection Validation | 10 | Test defensive controls |
| Purple Team Collaboration | 6 | Bridge red and blue efforts |
| Detection Gap Analysis | 6 | Identify coverage gaps |
| Security Control Assessment | 8 | Measure control effectiveness |

### Assessment
- **Checkpoint Quiz:** SIEM, detection rules, and incident response
- **Lab Exercise:** Detect red team activities in Wazuh
- **Capstone:** Conduct purple team exercise with full detection lifecycle

---

## Domain 6: Professional Development
**Weeks 45-48 | Mastery Hours: 60**

### Learning Objectives
Upon completion, the learner will be able to:
- Communicate technical findings to non-technical stakeholders
- Write professional security assessment reports
- Navigate cybersecurity career paths and certifications
- Practice ethical decision-making in security operations
- Build and maintain professional network in security community
- Mentor junior team members

### Sub-Topics & Modules

#### 6.1 Technical Communication (Week 45)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| Executive Report Writing | 6 | Create board-level reports |
| Penetration Test Reports | 6 | Document assessment findings |
| Risk Metrics & KPIs | 4 | Measure security posture |
| Presentation Skills | 4 | Present to technical audiences |

#### 6.2 Career Development (Week 46)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| Cybersecurity Certifications Path | 4 | Plan OSCP, CISSP, GCIH journey |
| Resume & LinkedIn Optimization | 4 | Market security skills |
| Interview Preparation | 6 | Practice technical interviews |
| Continuing Education | 2 | Plan ongoing learning |

#### 6.3 Ethics & Professionalism (Week 47)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| ISC2 Code of Ethics | 4 | Apply ethical decision framework |
| Legal Aspects of Security Testing | 6 | Understand laws and regulations |
| Responsible Disclosure | 4 | Handle vulnerability reporting |
| Social Responsibility | 2 | Balance security and privacy |

#### 6.4 Leadership & Mentorship (Week 48)
| Topic | Hours | Mastery Criteria |
|-------|-------|------------------|
| Team Leadership Fundamentals | 4 | Lead security projects |
| Mentoring Junior Analysts | 4 | Transfer knowledge effectively |
| Building Security Culture | 4 | Promote security awareness |
| Industry Community Engagement | 4 | Contribute to security community |

### Capstone Project
- **Final Assessment:** Comprehensive security assessment combining all domains
- **Report:** Professional penetration test report with executive summary
- **Presentation:** 30-minute presentation to fictional board

---

## Certification Alignment

| Domain | Aligned Certifications |
|--------|----------------------|
| Networking | CompTIA Network+, CCNA |
| Linux | RHCSA, LFCS, CompTIA Linux+ |
| OSINT | eCPTX, CRTO |
| Red Team | OSCP, OSEP, CRTO, eCPPT |
| Blue Team | GCIH, GCDA, CLOUDSEC, Splunk Core |
| Professional | CISSP (after 5 years experience) |

---

## Mastery Milestones

### Bronze Level (Weeks 1-12)
- Complete networking fundamentals
- Demonstrate Linux CLI proficiency
- Pass Domain 1 & 2 checkpoint quizzes
- Build home lab with 3 VMs

### Silver Level (Weeks 13-24)
- Complete OSINT and reconnaissance
- Execute basic penetration test
- Deploy and configure SIEM
- Pass Domain 3 & 4 checkpoint quizzes

### Gold Level (Weeks 25-36)
- Perform full red team engagement
- Write working exploit code
- Develop Sigma detection rules
- Conduct incident response exercise

### Platinum Level (Weeks 37-48)
- Execute purple team operations
- Mentor junior team members
- Produce professional security reports
- Present capstone to industry panel

---

## Lab Environment Requirements

### Minimum (Budget Lab)
- **CPU:** 4 cores
- **RAM:** 16 GB
- **Storage:** 500 GB SSD
- **VMs:** Kali Linux, Metasploitable2, Ubuntu Server, Windows 10

### Recommended (Professional Lab)
- **CPU:** 8+ cores
- **RAM:** 32+ GB
- **Storage:** 1 TB NVMe
- **VMs:** Kali, Parrot OS, 2x Windows (Server + Desktop), Ubuntu, pfSense, Wazuh Server

### Advanced (Purple Team Lab)
- AD Domain with Domain Controller
- Multiple subnets with firewall
- EDR solutions (Wazuh, Velociraptor)
- Full purple team infrastructure

---

*Curriculum Version 1.0 | SkillSprint Academy | Purple Team Mastery Track*
