# ZeroCipher

A **fully offline-capable Flask learning platform** for cybersecurity education. Built around a personalized, assessment-driven curriculum with hands-on labs, AI tutoring, and gamified progress tracking.

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Key Features](#key-features)
- [Curriculum Structure](#curriculum-structure)
- [Offline Mode](#offline-mode)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Development](#development)
- [Deployment](#deployment)
- [License](#license)

---

## Overview

ZeroCipher is a **single-user, offline-first** Flask application designed to teach cybersecurity through a structured, personalized learning path. It combines:

- **Adaptive skill assessment** (CAT-style) to determine starting proficiency
- **AI-generated roadmaps** that respect prerequisites and user availability
- **Hands-on labs** — both link-out (TryHackMe, Hack The Box, PortSwigger, PicoCTF, OverTheWire) and **fully bundled offline challenges** (PCAP analysis, cipher labs, regex labs, code exercises, binary inspection)
- **Local AI tutor** powered by Ollama with a deterministic rules-based fallback
- **Gamification** (XP, streaks, levels) and progress analytics
- **Capstone projects** — graded Tier-4 projects per job role (mock OSCP, IR tabletop, cloud attack chain, etc.)

> **Default mode is OFFLINE**. The platform binds to `127.0.0.1:5000`, requires no internet, no SMTP, no external APIs. All external dependencies (Razorpay, Google OAuth, external labs) are gated behind `OFFLINE_MODE=False`.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Flask Application                       │
├─────────────────────────────────────────────────────────────┤
│  Blueprints (8 core + 1 offline helper)                      │
│  ┌──────────┬───────────┬─────────┬────────┬────────────┐   │
│  │Onboarding│Assessment │ Roadmap │Dashboard│   Labs    │   │
│  └──────────┴───────────┴─────────┴────────┴────────────┘   │
│  ┌──────────┬───────────┬─────────┬────────┬────────────┐   │
│  │ Library  │ Assistant │Job Roles│ Offline │            │   │
│  └──────────┴───────────┴─────────┴────────┴────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  Services Layer                                              │
│  ┌──────────────┬─────────────┬───────────┬──────────────┐  │
│  │assessment_eng│roadmap_eng  │ ai_tutor  │ xp_service   │  │
│  └──────────────┴─────────────┴───────────┴──────────────┘  │
│  ┌──────────────┬─────────────┬───────────┬──────────────┐  │
│  │scheduler_svc │link_metadata│ (more)    │              │  │
│  └──────────────┴─────────────┴───────────┴──────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  SQLAlchemy Models (20+ tables)                              │
│  User, SkillArea, Topic, JobRole, Lab, Assessment*,          │
│  Roadmap, RoadmapItem, SkillProfile, XPLog, StreakRecord,   │
│  ChatMessage, ContentItem, UserResource, CachedResource,    │
│  MiniProject, TopicHint, LocalInbox, ...                    │
├─────────────────────────────────────────────────────────────┤
│  Extensions: SQLAlchemy, Migrate, Limiter, Talisman, CSRF   │
└─────────────────────────────────────────────────────────────┘
```

### Design Principles
- **Single-user context**: No multi-tenant complexity; `g.user` loaded once per request
- **Offline-first**: Every external call has a local fallback or is disabled in offline mode
- **Data-driven curriculum**: SkillAreas → Topics (DAG) → JobRole templates → personalized roadmap
- **Idempotent seeding**: Run `seed.py` anytime to populate reference data
- **Blueprint isolation**: Each feature area is a self-contained blueprint

---

## Key Features

### 1. Onboarding Flow (`/onboarding/*`)
Three-step wizard:
1. **Domain** — Currently Cybersecurity only (extensible)
2. **Goal** — General foundations vs. Job-Role track (9 NIST NICE-aligned roles)
3. **Availability** — Weekly minutes per day (Mon–Sun)

### 2. Adaptive Assessment (`/assessment/*`)
- Computerized Adaptive Testing (CAT) per skill area
- Starts at medium difficulty (configurable), walks up/down based on correctness
- 5 questions per area (configurable via `ASSESSMENT_QUESTIONS_PER_AREA`)
- Produces **SkillProfile** (0–100 score + confidence: low/medium/high) per area
- Results feed directly into roadmap personalization

### 3. Roadmap Engine (`/roadmap/*`)
**Two-layer design:**
- **Layer A (Curriculum Graph)**: Admin-authored Topic DAG + per-role ordered templates (`JobRoleTopic`)
- **Layer B (Personalization)**:
  1. Select base template (role or general)
  2. Prune using SkillProfile (skip if score ≥80, remediate if <30)
  3. Expand each topic → ContentItems + Labs (in order)
  4. Schedule via `scheduler_service` using user's `WeeklyAvailability`
  5. Persist `Roadmap` + `RoadmapItem` rows

**Re-planning** (`POST /roadmap/replan`) preserves completed items and re-applies them to the new plan.

### 4. Dashboard (`/dashboard`, `/progress`)
- **Today view**: Header strip (XP, level, streak), today's schedule, "Continue" item, 7-day week strip, roadmap % progress
- **Progress analytics**: Skill radar chart (Chart.js), XP history, streak record

### 5. Labs System (`/labs/*`)
| Provider | Type | Offline Support |
|----------|------|-----------------|
| TryHackMe | Link-out | ❌ Greyed out in offline |
| Hack The Box | Link-out | ❌ Greyed out in offline |
| PortSwigger | Link-out | ❌ Greyed out in offline |
| PicoCTF | Link-out | ❌ Greyed out in offline |
| OverTheWire | Link-out | ❌ Greyed out in offline |
| **self_hosted_offline** | **Bundled files** | ✅ **Full support** |

**Offline labs** (`provider=self_hosted_offline`):
- Artifacts stored under `bundles/labs/<topic>/...` (PCAPs, binaries, ciphertexts, regex corpora, code templates)
- Served read-only via `/lab/<id>/file/<path>` with path traversal protection
- Proof types: `flag` (SHA-256 verified), `self_report`, `screenshot`, `writeup_url`
- XP awarded on completion; streak updated

### 6. Interactive Exercises (`/offline/exercise/<id>`)
ContentItems with `type=interactive_exercise` and `exercise_spec` JSON:
| Kind | Template | Description |
|------|----------|-------------|
| `code_py` | `exercises/code_py.html` | Python snippet with unit tests (Pyodide in browser) |
| `code_js` | `exercises/code_js.html` | JavaScript snippet |
| `quiz_interactive` | `exercises/quiz_interactive.html` | MCQ with instant feedback |
| `regex_lab` | `exercises/regex_lab.html` | Regex builder + test corpus |
| `cipher_lab` | `exercises/cipher_lab.html` | Classical/modern cipher encoder/decoder |
| `pcap_challenge` | `exercises/pcap_challenge.html` | PCAP file viewer + questions |
| `binary_inspector` | `exercises/binary_inspector.html` | Hex/strings/ELF/PE inspector |

### 7. AI Personal Teacher (`/assistant`, `/api/assistant/chat`)
**Provider strategy** (config `AI_TUTOR_PROVIDER`):
- `auto` → Ollama if reachable (200ms probe), else rules
- `ollama` → Local LLM at `OLLAMA_BASE_URL` (default `http://127.0.0.1:11434`)
- `anthropic` → Cloud API (requires `ANTHROPIC_API_KEY`, disabled in offline)
- `rules` → Deterministic `TopicHint` lookup (never empty, never leaks flags)

**Rules fallback** (plan §7.2):
- `TopicHint` rows keyed by `trigger_keywords` (JSON) + `hint_level` (1–3)
- Escalates on repeated "help/hint/stuck" queries
- Falls back to templated lesson summary + next-step table

**Settings UI**: `/offline/settings/ai-tutor` — model picker, connection test, persistence to `instance/ollama_model.txt`

### 8. Personal Library (`/library/*`)
- Add external resources by URL → auto-fetches metadata (title, type, thumbnail, duration) via `link_metadata_service`
- In offline mode, metadata fetched from `CachedResource` table (pre-synced via `sync_resource_cache.ps1`)
- Schedule any resource into roadmap as `external_resource` item

### 9. Job Roles (`/job-roles/*`)
9 NIST NICE-aligned roles, each with:
- Description, salary band, recommended certifications
- Ordered topic template (`JobRoleTopic`)
- **Tier-4 Capstone** (`MiniProject` with `grading_method`: `flag_submission`, `ioc_checklist`, or `self_grade_checklist`)

| Role | Slug | Capstone |
|------|------|----------|
| SOC Analyst | `soc-analyst` | Alert Triage (IOC checklist) |
| Penetration Tester | `pentester` | Mock OSCP 24hr (flag submission) |
| AppSec Engineer | `appsec-engineer` | Secure SDLC Audit (self-grade) |
| Incident Responder | `incident-responder` | IR Tabletop (self-grade) |
| Cloud Security | `cloud-security` | K8s + IAM Attack Chain (flag) |
| GRC Analyst | `grc-analyst` | NIST/ISO Gap Analysis (self-grade) |
| Bug Bounty Hunter | `bug-bounty` | Public Program Write-up (self-grade) |
| Blue Team / DFIR | `dfir` | Ransomware Artifact Analysis (IOC) |
| Vuln Assessment | `vuln-assessor` | Scan + Remediation Plan (self-grade) |

### 10. Gamification (`services/xp_service.py`)
| Source | XP (configurable) |
|--------|-------------------|
| Content item | `XP_PER_CONTENT_ITEM` (default 10) |
| Lab | `XP_PER_LAB` (default 25) |
| Quiz/Checkpoint | `XP_PER_QUIZ` (default 15) |
| Assessment completion | `XP_PER_QUIZ` |
| Streak bonus (every 7 days) | `XP_STREAK_BONUS` (default 5) |

**Streak rules** (Duolingo-style):
- Consecutive days → +1
- 1-day gap with freeze available → consume freeze, +1
- Larger gap → reset to 1
- Freezes refill weekly (ISO week), default 1/week (`STREAK_FREEZES_PER_WEEK`)

### 11. Contact / Local Inbox (`/contact`)
- Online mode: Sends email via Flask-Mail
- Offline mode: Stores in `LocalInbox` table (viewable in admin or DB)

### 12. Offline Helpers (`/offline/*`)
| Route | Purpose |
|-------|---------|
| `/offline/about` | Explains offline capabilities/limitations |
| `/offline/lab-setup` | Kali VM setup guide + bundled challenge index |
| `/offline/resource-cache` | Status of one-time `CachedResource` sync |
| `/offline/settings/ai-tutor` | Ollama model selection + connection test |

---

## Curriculum Structure

### Skill Areas (9 core + 2 legacy)
| Tier | Area | Slug | Icon | Description |
|------|------|------|------|-------------|
| 0 | Computing Foundations | `computing-foundations` | 💻 | Binary, hex, files, OS concepts |
| 0 | Networking Basics | `networking-basics` | 📡 | OSI, TCP/IP, packets |
| 0 | Linux Fundamentals | `linux-fundamentals` | 🐧 | Bash, FS, permissions, processes |
| 0 | Windows Fundamentals | `windows-fundamentals` | 🪟 | Registry, processes, services, CLI |
| 0 | Security Mindset | `security-mindset` | 🧠 | CIA, threat models, MITRE ATT&CK |
| 1 | Networking | `networking` | 🌐 | Deep TCP/IP, routing, firewalls, PCAP |
| 1 | Web Application Security | `web-application-security` | 🕸️ | OWASP Top 10, Burp, SQLi, XSS |
| 1 | Cryptography | `cryptography` | 🔑 | Symmetric/asymmetric, PKI, TLS |
| 1 | OSINT | `osint` | 🔭 | Recon, search, CT logs |
| 1 | Scripting & Python | `scripting-python` | 🐍 | Automation, sockets, tooling |
| 2 | Windows & Active Directory | `windows-active-directory` | 🪟 | AD, Kerberos, GPO, lateral movement |
| 2 | Linux Hardening & Forensics | `linux-hardening-forensics` | 🛡️ | Hardening, disk/memory forensics |
| 2 | Packet Forensics | `packet-forensics` | 📦 | Incident-scale PCAP analysis |
| 3 | Exploit Development | `exploit-development` | 💥 | Stack overflow → ROP → heap |
| 3 | Red Team Operations | `red-team-operations` | 🎯 | C2, OPSEC, evasion |
| 3 | Malware Analysis | `malware-analysis` | 🦠 | Static/dynamic, YARA, unpacking |
| 3 | Cloud & Container Pentesting | `cloud-container-pentesting` | ☁️ | IAM, K8s, Terraform |
| 3 | Blue Team / Detection Engineering | `blue-team-detection-engineering` | 🚨 | SIEM, Sigma, threat hunting, SOC |
| — | Cloud Security (legacy) | `cloud-security` | ☁️ | Back-compat bucket |
| — | GRC (legacy) | `grc` | 📋 | Governance, risk, compliance |

### Topics (~70)
Each topic has:
- `skill_area_id`, `difficulty` (1–5), `estimated_minutes`
- Prerequisites via `TopicPrerequisite` (DAG edges)
- `ContentItem` children (lessons, videos, PDFs, quizzes, interactive exercises)
- `Lab` children (link-out or bundled)

### Assessment Questions (~45)
5 MCQ/short-answer per skill area, difficulty 1–5, tagged with MITRE technique IDs and applicable job roles.

---

## Offline Mode

Controlled by `OFFLINE_MODE` environment variable (default: `True`).

### What Works Offline
| Feature | Implementation |
|---------|----------------|
| Web server | Binds to `127.0.0.1` (config `OFFLINE_BIND_HOST`) |
| Database | SQLite (`sqlite:///zerocipher.db`) |
| Authentication | Single local user (auto-created: `operator` / `zerocipher`) |
| Labs | Only `self_hosted_offline` labs visible; bundled files served locally |
| AI Tutor | Ollama (local) → Rules fallback (zero external calls) |
| Contact form | Stores to `LocalInbox` table |
| Resource metadata | Pre-synced `CachedResource` table (run `sync_resource_cache.ps1` once) |
| Static assets | Bootstrap, Chart.js, fonts, Pyodide — all vendored in `static/` |
| Capstone projects | Bundled artifacts under `bundles/labs/` |

### What's Disabled Offline
- Razorpay payments
- Google OAuth login
- SMTP email (Flask-Mail)
- External lab links (TryHackMe, HTB, PortSwigger, PicoCTF, OverTheWire) — shown as "requires internet"
- Anthropic API calls
- Live external resource fetching (uses cache)

### Talisman CSP (Offline)
```
default-src: 'self'
script-src: 'self', 'unsafe-inline'
style-src: 'self', 'unsafe-inline'
font-src: 'self', data:
img-src: 'self', data:
connect-src: 'self', OLLAMA_BASE_URL
force_https: False
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- (Optional) Ollama for local AI tutor: `curl -fsSL https://ollama.com/install.sh | sh && ollama serve && ollama pull llama3.1:8b-instruct`

### Installation
```powershell
# 1. Clone & enter
cd V:\Projects\ZeroCipher_Academy\ZEROCIPHER_ACADEMY

# 2. Create venv
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Configure .env — defaults work out of the box
# Copy .env.example to .env and edit if needed

# 5. Run
python app.py
```

The app will:
1. Create `zerocipher.db` (SQLite)
2. Run `db.create_all()` → tables
3. Seed the default user (`operator` / `zerocipher`)
4. Start on `http://127.0.0.1:5000`

### First Run — Seed Curriculum Data
```powershell
# After first startup (tables exist), run the seed script:
python seed.py
```

This populates:
- 21 SkillAreas
- ~70 Topics with full DAG prerequisites
- 9 JobRoles with capstone projects
- ~45 AssessmentQuestions
- ~25 Tier-1 Labs (link-out)
- TopicHints for AI tutor fallback

### Verify
Open `http://127.0.0.1:5000` → redirects to `/dashboard` → onboarding starts automatically.

---

## Configuration

All settings in `config.py` via environment variables (loaded from `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `default-dev-secret-key` | Flask secret |
| `OFFLINE_MODE` | `True` | **Master switch** — offline defaults to ON |
| `OFFLINE_BIND_HOST` | `127.0.0.1` | Bind address in offline mode |
| `OFFLINE_BIND_PORT` | `5000` | Port |
| `DATABASE_URL` | `sqlite:///zerocipher.db` | SQLAlchemy URI |
| `AI_TUTOR_PROVIDER` | `auto` | `auto` \| `ollama` \| `anthropic` \| `rules` |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Local Ollama endpoint |
| `OLLAMA_MODEL` | `llama3.1:8b-instruct` | Model name |
| `OLLAMA_PROBE_TIMEOUT` | `0.2` | Seconds for health probe |
| `ANTHROPIC_API_KEY` | `` | Cloud fallback (ignored offline) |
| `XP_PER_CONTENT_ITEM` | `10` | XP for lesson completion |
| `XP_PER_LAB` | `25` | XP for lab completion |
| `XP_PER_QUIZ` | `15` | XP for quiz/checkpoint |
| `XP_STREAK_BONUS` | `5` | Bonus every 7-day streak |
| `STREAK_FREEZES_PER_WEEK` | `1` | Freeze tokens per ISO week |
| `ASSESSMENT_QUESTIONS_PER_AREA` | `5` | Questions per skill area |
| `ASSESSMENT_START_DIFFICULTY` | `3` | Starting difficulty (1–5) |
| `ROADMAP_BUFFER_PERCENT` | `0.20` | 20% buffer for spaced repetition |
| `MAIL_*` | Gmail SMTP | Disabled when `OFFLINE_MODE=True` |
| `RAZORPAY_*` | Test keys | Disabled when `OFFLINE_MODE=True` |
| `GOOGLE_OAUTH_*` | Placeholders | Disabled when `OFFLINE_MODE=True` |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Defaults | Admin bootstrap creds |

### Static Asset Vendoring (Offline)
Run once to download all CDN assets to `static/vendor/`:
```powershell
# Bootstrap 5.3 (CSS + JS)
.\download_bootstrap.ps1

# Chart.js 4.x
.\download_icons_chartjs.ps1

# Fonts (Inter, JetBrains Mono, Bootstrap Icons)
.\download_fonts.ps1

# Pyodide (for in-browser Python execution)
.\download_pyodide.ps1
```

---

## Project Structure

```
ZEROCIPHER_ACADEMY/
├── app.py                      # Flask factory, blueprint registration, global context
├── config.py                   # Config classes (Config, DevelopmentConfig, ProductionConfig)
├── extensions.py               # SQLAlchemy, Migrate, Limiter, Talisman, CSRF
├── models.py                   # 20+ SQLAlchemy models
├── forms.py                    # WTForms (currently minimal; auth uses custom)
├── seed.py                     # Idempotent curriculum seed (run after db.create_all)
├── seed_topic_hints.py         # Seeds TopicHint rows for AI tutor fallback
├── seed_exercises.py           # Seeds interactive_exercise ContentItems
├── seed_offline_labs.py        # Seeds self_hosted_offline Lab rows
├── requirements.txt            # Pinned dependencies
├── manage.py                   # Flask CLI (if used)
├── .env                        # Local env (gitignored)
├── .gitignore
├── instance/
│   ├── zerocipher.db          # SQLite database (gitignored)
│   ├── resource_cache/         # CachedResource files (gitignored)
│   ├── user_uploads/           # User file uploads (gitignored)
│   └── ollama_model.txt        # Persisted Ollama model override
├── bundles/
│   └── labs/                   # Offline lab artifacts (PCAPs, bins, etc.)
├── static/
│   ├── css/                    # Custom styles
│   ├── js/                     # Custom JS (dashboard, roadmap, labs, assistant)
│   ├── vendor/                 # Vendored: bootstrap, chartjs, fonts, pyodide
│   └── images/
├── templates/
│   ├── base_cybersec.html      # Base layout (navbar, footer, CSP nonce)
│   ├── index.html              # Landing (redirects to dashboard)
│   ├── about.html, contact.html, privacy.html, terms.html
│   ├── errors/404.html, 500.html
│   ├── onboarding/             # domain.html, goal.html, availability.html
│   ├── assessment/             # take.html, result.html
│   ├── roadmap/                # view.html, calendar.html
│   ├── dashboard/              # today.html, progress.html
│   ├── labs/                   # browse.html, detail.html
│   ├── library/                # list.html, add.html
│   ├── assistant/              # chat.html
│   ├── job_roles/              # browse.html, detail.html
│   ├── exercises/              # base.html + 7 kind-specific templates
│   ├── offline/                # about.html, lab_setup.html, resource_cache.html, ai_tutor_settings.html
│   └── admin/                  # (legacy/admin panels — not used in offline MVP)
├── services/
│   ├── __init__.py
│   ├── assessment_engine.py    # CAT logic, grading, SkillProfile computation
│   ├── roadmap_engine.py       # DAG ordering, personalization, scheduling, persistence
│   ├── scheduler_service.py    # Calendar scheduling from availability
│   ├── ai_tutor_service.py     # Provider strategy, Ollama, Anthropic, rules fallback
│   ├── xp_service.py           # XP awards, streak tracking
│   └── link_metadata_service.py# URL metadata fetch (online) / cache lookup (offline)
├── blueprints/
│   ├── onboarding/routes.py
│   ├── assessment/routes.py
│   ├── roadmap/routes.py
│   ├── dashboard/routes.py
│   ├── labs/routes.py
│   ├── library/routes.py
│   ├── assistant/routes.py
│   ├── job_roles/routes.py
│   └── offline/routes.py
├── release/
│   ├── ZeroCipher.exe  # PyInstaller standalone executable
│   ├── Start-ZeroCipher.bat   # Windows launcher
│   ├── scripts/
│   │   ├── build_exe.ps1       # PyInstaller build script
│   │   ├── start_zerocipher.ps1
│   │   ├── setup_ollama.ps1
│   │   ├── setup_kali_vm.ps1
│   │   └── sync_resource_cache.ps1
│   └── README.txt
└── ZeroCipher_Technical_Standard_and_EXE_Packaging.md  # Architecture & packaging docs
```

---

## Development

### Run with Auto-reload
```powershell
python app.py
# Flask debug mode enabled by default in DevelopmentConfig
```

### Database Migrations
```powershell
# After model changes:
flask db migrate -m "description"
flask db upgrade
```

### Seed / Reseed Data
```powershell
python seed.py              # Core curriculum
python seed_topic_hints.py  # AI tutor hints
python seed_exercises.py    # Interactive exercises
python seed_offline_labs.py # Bundled offline labs
```

### Add a New Skill Area / Topic / Lab
1. Add to `seed.py` arrays (`SKILL_AREAS`, `TOPICS`, `PREREQUISITES`, `LABS`)
2. Run `python seed.py` (idempotent)

### Add a New Interactive Exercise Kind
1. Create template in `templates/exercises/<kind>.html`
2. Register in `blueprints/offline/routes.py:_KIND_TEMPLATE`
3. Seed via `seed_exercises.py` with `exercise_spec.kind = "<kind>"`

### Run Tests
```powershell
# No formal test suite yet; manual verification via:
# - http://127.0.0.1:5000/health  → {"status":"healthy","database":"connected","offline":true}
# - Complete onboarding → assessment → roadmap → dashboard flow
```

---

## Deployment

### Standalone Windows EXE (Recommended for Offline Distribution)
```powershell
cd release/scripts
.\build_exe.ps1
# Output: release/ZeroCipher.exe (~150-200 MB)
```

The exe bundles:
- Python interpreter + all dependencies
- `static/`, `templates/`, `bundles/`
- `instance/` (empty; DB created on first run)
- Launcher script `Start-ZeroCipher.bat`

### Manual Production (Linux/WSL)
```bash
# 1. Set production config
export FLASK_ENV=production
export OFFLINE_MODE=False   # or True for air-gapped
export SECRET_KEY="$(openssl rand -hex 32)"
export DATABASE_URL="postgresql://user:pass@host/db"
# ... other vars

# 2. Install gunicorn
pip install gunicorn

# 3. Run migrations
flask db upgrade

# 4. Seed
python seed.py && python seed_topic_hints.py && python seed_exercises.py && python seed_offline_labs.py

# 5. Start
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Reverse Proxy (Nginx Example)
```nginx
server {
    listen 80;
    server_name zerocipher.local;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## License

This project does not include an explicit license file. Add one (e.g., MIT, Apache-2.0) if you intend to share or publish.

---

## Acknowledgments

- **Flask** & extensions (SQLAlchemy, Migrate, Limiter, Talisman, WTF, Mail, Login, Dance)
- **Ollama** for local LLM inference
- **Pyodide** for in-browser Python execution
- **Chart.js** for progress radar charts
- **Bootstrap 5** + **Bootstrap Icons** for UI
- **TryHackMe, Hack The Box, PortSwigger, PicoCTF, OverTheWire** for free lab content (link-out)
- **NIST NICE Framework** for job-role alignment

---

*Built for learning. Runs anywhere. No cloud required.*