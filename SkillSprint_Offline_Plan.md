# SkillSprint Academy — Offline Local Cybersecurity Mastery Plan

### From Zero to Expert (0 → 100), Fully Offline on Your Machine

---

## 0. About This Document

This plan **adapts** the existing `SkillSprint_CyberSec_Platform_Plan.md` (a cloud-oriented, SaaS-style platform) into a **strictly offline, single-user, local desktop learning system** that runs entirely on your Windows machine — no internet required after the initial setup.

The existing repo is already ~70% built: Flask app, SQLAlchemy models (User, Course, Track, SkillArea, Topic DAG, JobRole, ContentItem, Lab, Assessment, SkillProfile, Roadmap, RoadmapItem, WeeklyAvailability, UserResource, XPLog, StreakRecord, ChatMessage), eight blueprints (onboarding, assessment, roadmap, dashboard, labs, library, assistant, job_roles), services (roadmap_engine, assessment_engine, scheduler_service, ai_tutor_service, xp_service, link_metadata_service), and a `seed.py` that loads 9 SkillAreas, ~30 Topics, 9 JobRoles, 45 Assessment Questions, 25 Tier-1 link-out Labs.

This document specifies **what to change/add/remove** from that existing codebase to make it a complete offline 0→100 cybersecurity mentor.

---

## 1. Decisions Locked from Clarification Round

| Decision | Choice | Rationale |
|---|---|---|
| AI tutor offline mode | **Optional Ollama + rules-based fallback** | If Ollama is detected running locally, route chat there (fully offline LLM). Otherwise degrade gracefully to a deterministic hint/explanation system tied to each Topic/Lab. No cloud API key required. |
| Hands-on labs offline | **Local Kali VM + bundled challenge artifacts** | Provide setup scripts for a local Kali VirtualBox VM, plus bundled challenge files (PCAPs, log files, source-code-with-vulns, mini-CTF flags). No live internet targets. Docker app-labs deferred. |
| Curriculum depth | **Full 0 → 100 journey** | Foundations → Intermediate → Advanced → Specialization → Capstone. Includes reverse engineering, exploit dev, red team ops, malware analysis, cloud pentest, mock OSCP. |
| Content delivery | **Interactive in-browser exercises + downloadable external resource cache** | Embed quizzes, interactive code cells (Pyodide for in-browser Python), packet/cipher widgets. Optionally one-time online sync caches PDFs/articles for offline read. |
| Dropped features | **Payments/Razorpay, Google OAuth, SMTP email, community/leaderboard sharing** | Simplifies the app, removes external internet dependencies, focuses on single-user local mastery. |

---

## 2. What Changes vs. the Existing Codebase

### 2.1 Remove / Disable (external-internet dependencies)
- `razorpay` import + `create_order` route in `app.py` — gate behind `OFFLINE_MODE` flag (keep code, never invoke).
- `flask_dance` Google OAuth blueprint + `/login/google/authorized` route — disable when `OFFLINE_MODE=true`.
- `flask_mail` reminder/verification/send paths — disable; replace with in-app "Local Inbox" notifications.
- `services/link_metadata_service.py` (OpenGraph/oEmbed scraping for external URLs) — replace with a **local metadata cache** that uses a one-time-synced offline catalog (see §6.2) or manual entry only.
- `link-out labs` to tryhackme/htb/portswigger — keep the rows in DB for reference but **grey them out** in the offline UI; the offline lab path uses bundled challenges instead.

### 2.2 Keep As-Is (already offline-friendly)
- Flask + SQLAlchemy + Jinja2 server-render (no external frontend CDN required after CDN assets are vendored).
- All 22 SQLAlchemy models in `models.py` — the skill taxonomy, Topic DAG, Roadmap, Assessment, XP/Streak, ChatMessage tables work unchanged with SQLite locally.
- `services/roadmap_engine.py`, `services/scheduler_service.py`, `services/assessment_engine.py`, `services/xp_service.py` — pure-Python logic, no I/O changes needed.
- All eight blueprints' route logic — only the **lab detail / submit** and **assistant chat** routes need offline adaptations.

### 2.3 Add New
- `OFFLINE_MODE` config flag in `config.py`.
- Full **5-tier curriculum** (Foundations → Intermediate → Advanced → Specialization → Capstone) — major expansion of `SkillArea`, `Topic`, `JobRoleTopic` seed (currently only intermediate depth).
- `bundles/labs/` directory with offline challenge artifacts (PCAPs, logs, source-code-with-vulns, hidden-flag files, mini-CTF packages).
- `scripts/setup_kali_vm.ps1` PowerShell script that downloads/configures a local Kali VirtualBox VM (one-time online or pre-bundled ISO).
- `scripts/sync_resource_cache.ps1` — one-time optional online sync that downloads and caches public PDFs/articles/pages into `instance/resource_cache/`.
- Ollama integration in `services/ai_tutor_service.py` (replace Anthropic call with `localhost:11434` Ollama HTTP API).
- Interactive in-browser exercise runner: Pyodide integration + a small `ContentItemType = "interactive_exercise"` with a JSON `exercise_spec` column.
- Vendor all CDN assets (Bootstrap, Chart.js, jsdelivr) into `static/vendor/` so the UI renders offline.

---

## 3. Curriculum: The 0 → 100 Path

Five-tier taxonomy. Each tier is a set of `SkillArea` rows with `order_index` reflecting the tier; each `Topic` lives in one SkillArea and the DAG prerequisites enforce tier ordering.

### Tier 0 — Absolute Foundations (no IT background assumed)
SkillAreas: **Computing Foundations** (binary, hex, files, OS concepts), **Networking Basics** (OSI, TCP/IP, packets), **Linux Fundamentals**, **Windows Fundamentals**, **Security Mindset** (CIA triad, threat models, attacker lifecycle, ethics & legality).
~12 Topics. Goal: user can describe what a packet is, run basic shell/PowerShell commands, and explain CIA + MITRE ATT&CK in their own words.

### Tier 1 — Core Technical Security
SkillAreas (existing): **Networking (deep)** with Wireshark, **Web Application Security**, **Cryptography**, **Scripting & Python**, **OSINT**.
~20 Topics + ~30 in-browser exercises. Goal: user can intercept a web request in Burp, write a 30-line port scanner, hash/salt passwords, run a basic OSINT dossier.

### Tier 2 — Systems & Active Directory
SkillAreas: **Windows & Active Directory** (existing, deepened), **Linux Hardening & Forensics**, **Packet Forensics** (PCAP analysis at incident scale).
~12 Topics. Goal: user can enumerate an AD domain with BloodHound, read Kerberos tickets, recover artifacts from a Linux disk image.

### Tier 3 — Advanced Offensive & Defensive
SkillAreas: **Exploit Development** (stack overflow → ROP → heap, shellcoding, bypassing mitigations), **Red Team Operations** (C2, lateral movement, OPSEC, evasion), **Malware Analysis** (static / dynamic, YARA, sandboxing, unpacking), **Cloud & Container Pentesting** (IAM abuse, K8s attacks, Terraform misconfig hunting), **Blue Team / Detection Engineering** (SIEM queries, sigma rules, threat hunting at scale, SOC playbooks).
~25 Topics. Goal: user can write a working stack-overflow PoC, analyze a packed PE in a sandbox, and author a Sigma detection rule.

### Tier 4 — Specialization & Capstone
Two parallel track options, mirroring the existing `JobRole` table:
- **Offensive:** bug bounty hunting methodology, OSCP-style 24-hour mock exam, real-world CVE walk-throughs, write-up craft.
- **Defensive / Blue:** full-scale incident response tabletop, DFIR capstone (analyzing a bundled ransomware artifact set), SOC L2 capstone (triaging a packaged "alert archive").

Each Tier 4 ends with a graded **Capstone Project** stored in `MiniProject` (already modeled) — auto-checked against a rubric where feasible (e.g., flag submission, expected IoCs found in the PCAP), self-graded by checklist otherwise.

### Topic DAG extensions to seed
The existing `seed.py` already has ~30 Topics touching Tiers 1–2. We will **expand** it:
- Add Tier 0 skill areas + ~12 beginner topics (must-come-first in the DAG; everything in current seed acquires `"Computing Foundations"` and `"Security Mindset"` as prerequisites).
- Add Tier 3 advanced skill areas + ~25 advanced topics (children of the existing intermediate ones — e.g., `Burp Suite Essentials → Web Cache Poisoning → HTTP Request Smuggling → Advanced Exploitation Capstone (web)`).
- Expand each `JobRole` row's `recommended_certs` JSON and add a `capstone_project_id` foreign key to `MiniProject` for the role's final project.

Total target after expansion: **~14 SkillAreas, ~100 Topics, ~250 ContentItems, ~60 in-browser interactive exercises, ~80 bundled offline labs, 9 fully-mapped JobRole tracks.**

---

## 4. Interactive In-Browser Exercises (new `ContentItem.type`)

Add `interactive_exercise` to the `ContentItem.type` enum values (already VARCHAR). Add a nullable `exercise_spec` JSON column (can be stored in `body_markdown` for MVP to avoid a migration, or as a proper column).

Supported exercise types (all client-side, fully offline via Pyodide/JS):

| Kind | What the user does | Grading |
|---|---|---|
| `code_py` | Write Python in a `<textarea>`, run in-browser via Pyodide, see stdout. Unit tests in spec validate. | Auto-pass/fail |
| `code_js` | Same but in-browser JS via `eval` in a sandboxed iframe. | Auto |
| `pcap_challenge` | A bundled PCAP is loaded into a small JS packet viewer widget; user answers questions about it (e.g., "what port did the C2 beacon use?"). | Answers checked against spec |
| `cipher_lab` | Interactive Caesar/Vigenère/RSA widgets — user encrypts/decrypts by clicking. | Auto |
| `regex_lab` | Write a regex that matches given payloads; client-side regex tester validates. | Auto |
| `quiz_interactive` | Branching scenario quiz ("Choose your response to this SIEM alert…") — outcome depends on choices. | Branch outcome stored |
| `binary_inspector` | Hex viewer over a bundled binary; user finds a specific byte pattern. | Auto |

All specs are stored in JSON in the DB (`exercise_spec` field); the renderer is a generic Jinja2 template (`templates/exercises/<kind>.html`) that consumes the spec. This means **adding new exercises is a content-authoring task, not a code change** — consistent with the original plan's §5.6 admin CMS vision.

### Pyodide notes
- Pyodide is a large download (~10MB) — vendored once into `static/vendor/pyodide/` so it runs fully offline.
- A single `static/js/exercise_runner.js` boots Pyodide on demand and exposes `window.runPython(code)`.

---

## 5. Offline Labs Strategy — Kali VM + Bundled Challenges

### 5.1 Kali VM setup script (`scripts/setup_kali_vm.ps1`)
A PowerShell script for the host (your Windows machine) that:
1. Checks VirtualBox is installed; if not, prints install instructions (we will not silently install).
2. Downloads the Kali VirtualBox appliance `.ova` from a user-specified local path OR (one-time online) from `https://www.kali.org/get-kali/`. **Skipped** if the VM already exists.
3. Imports the appliance, sets up a host-only adapter, snapshots a clean state, and prints SSH + RDP connection details.
4. Copies a `~/skillSprint-labs/` directory inside the guest containing the bundled challenge artifacts.

After the script runs once, the VM lives locally and the script never needs the internet again.

### 5.2 Bundled challenge artifacts (`bundles/labs/`)
Directory tree shipped with the app:

```
bundles/labs/
├── networking/
│   ├── capture_challenge1.pcap (flag inside a TCP stream)
│   └── README.md
├── linux/
│   ├── forensics_disk_image.img.xz (mini)
│   └── auth.log (find the brute force)
├── web/
│   ├── vuln_app_source.zip (find the 5 OWASP vulns by reading code — static)
│   └── writeup_checklist.md
├── crypto/
│   ├── hashes_challenge.txt (rockyou subset bundled for offline cracking demo)
│   └── rsa_challenge.pem
├── osint/
│   └── simulated_target_archive.zip (fake company website + WHOIS dump)
├── windows_ad/
│   ├── simulated_ntds.dit (sanitized, for offline hash extraction + cracking)
│   └── bloodhound_export.json (analyze an existing graph, no live query)
├── exploit_dev/
│   ├── stack_overflow_binary.exe (32-bit, vulnerable, no ASLR for tier-3 entry)
│   └── rop_gadget_notes.txt
├── malware/
│   ├── sample_packed_pe.exe.inert (.setInternet=False wrapper, inert)
│   └── yara_challenge.yar (write the rule)
└── ctf/
    └── mini_ctf_bundle.zip (30 small challenges across categories, flag-checked)
```

Each challenge corresponds to a `Lab` row with `provider="self_hosted_offline"`, `url_or_container_ref` pointing to the relative `bundles/...` path, `proof_type="flag"` (sometimes `writeup_url`), and a pre-computed `flag_hash` so the existing `submit` route can verify it offline.

### 5.3 Lab runner UI (`/lab/<id>` offline mode)
The lab detail template renders differently when `OFFLINE_MODE` is on and `lab.provider == "self_hosted_offline"`:
- An **"Open challenge files"** button that links to a Flask static route serving the bundled file (so the user can download the PCAP / source pack / VM snapshot).
- A **"Setup the Kali VM"** callout linking to the README.
- The existing flag submission box (already implemented in `labs/routes.py:submit`) — the SHA-256 comparison works entirely offline.

### 5.4 What about the original Tier-1 (online) lab rows?
Keep them in `Lab` table but tag with a derived `is_offline_available=False`. The browse UI (existing `labs/browse.html`) filters them out in offline mode and shows a small notice: "Requires internet — disabled in offline mode."

---

## 6. Content Delivery — Bundled Lessons + Resource Cache

### 6.1 Bundled Markdown lessons (offline by default)
~250 `ContentItem` rows of `type="lesson_md"` with `body_markdown` populated. Authored once, shipped with `seed_lessons.py` (a new seed file, idempotent, mirrors the structure of `seed.py`).

Lesson template sub-structure (consistent across all topics):
1. **Why this matters** (1 paragraph, scenarios).
2. **Conceptual core** (definitions, diagrams as inline SVG or bundled PNGs in `static/lessons/<slug>/`).
3. **Hands-on example** (3–6 steps the user can do entirely inside the in-browser interactive exercise).
4. **Common mistakes / misconceptions.**
5. **Checkpoint** — 3 MCQ questions inline (stored as a `quiz_checkpoint` ContentItem immediately after).

### 6.2 Downloadable external resource cache (one-time online sync — optional)
```
scripts/sync_resource_cache.ps1
```
A configurable PowerShell script that:
- Reads a `resource_catalog.json` (shipped) listing public-domain or CC-licensed pages/PDFs (e.g., OWASP Cheat Sheet Series, NIST publications, MITRE ATT&CK technique pages, PortSwigger articles).
- Downloads each to `instance/resource_cache/<sha256-of-url>.html` (or `.pdf`).
- Builds an index table `CachedResource (id, original_url, local_path, title, fetched_at, content_hash)` that the existing `link_metadata_service` reads from instead of fetching live.

After the sync runs once, the platform is fully offline and serves cached content from disk.
- New `UserResource` rows added by the user can link to a `CachedResource` if one exists, or fall back to "you added this manually — file not available offline" placeholder.

### 6.3 Vendoring the CDN assets
Currently `app.py` Talisman CSP allows `https://cdn.jsdelivr.net`, `https://fonts.googleapis.com`, etc. For offline, we:
1. Download Bootstrap 5, Bootstrap Icons, Chart.js, and a fallback Google Font into `static/vendor/`.
2. Update `templates/base_cybersec.html` (and others) to use `{% if offline_mode %}/static/vendor/...{% else %}CDN{% endif %}`.
3. Tighten Talisman CSP in `OFFLINE_MODE` to `'self'` only.

---

## 7. AI Tutor — Ollama + Rules Fallback

### 7.1 Ollama integration (`services/ai_tutor_service.py`)
Refactor the existing `answer()` function (currently calls Anthropic) into a strategy picker:

```
def answer(query, topic_id=None):
    topic = ...
    context = _retrieve_context(topic_id, query)
    system = _build_system_prompt(topic)

    provider = current_app.config.get("AI_TUTOR_PROVIDER", "auto")
    if provider == "auto":
        provider = "ollama" if _ollama_alive() else "rules"

    if provider == "ollama":
        return _ollama_reply(query, system, context, topic)
    if provider == "anthropic" and current_app.config.get("ANTHROPIC_API_KEY"):
        return _anthropic_reply(...)            # kept for online users
    return _rules_reply(query, topic)            # always available
```

- `_ollama_alive()` does a 200ms `localhost:11434/api/tags` probe; if it fails, falls back.
- `_ollama_reply()` POSTs to `http://localhost:11434/api/chat` with the chosen model (default `llama3.1:8b-instruct` or `mistral:7b-instruct`, configurable via `OLLAMA_MODEL` env). No streaming for MVP — single shot.
- A `/settings/ai-tutor` page lets the user pick the model and test connection. The existing `ChatMessage` table stores conversation history exactly as before.

### 7.2 Rules-based fallback
A deterministic tutor that:
- Looks up the current `Topic` and finds authored hints in a new `TopicHint` table (`id, topic_id, trigger_keywords (JSON), hint_text (Markdown), hint_level (1-3)`).
- If the user's query matches a hint's keywords, returns the hint at the appropriate level.
- If no match: returns a templated answer with the topic's lesson summary + suggested next steps.
- Lab hint detection: if the query mentions "help", "hint", "stuck" → returns escalating `_rules_reply` levels without leaking the flag (mirrors §5.10 of the original plan).

Seed `TopicHint` rows for every Topic so the fallback is never empty.

### 7.3 Suggested local models
| Model | Size | Use case | Min RAM |
|---|---|---|---|
| `phi3:mini` | ~2.3GB | Fast, low-RAM machines, decent explanations | 8GB |
| `llama3.1:8b-instruct` | ~4.7GB | Recommended default — best quality/size balance | 16GB |
| `mistral:7b-instruct` | ~4.1GB | Good alternative default | 16GB |
| `qwen2.5-coder:7b` | ~4.7GB | Best for the scripting / exploit-dev tier topics | 16GB |

The setup script (§10) prints the recommended command per RAM tier.

---

## 8. Database & Storage (SQLite locally)

- Default `DATABASE_URL` already supports SQLite (`sqlite:///skillsprint.db`). No change needed — keep SQLite. Disable the Postgres/Oracle mentions in the original plan.
- Migrations: keep `Flask-Migrate` (already on); the first offline migration creates a single `skillSprint.db` in `instance/`.
- Bundled content (lessons, exercises, labs, resource cache) lives on disk and is referenced by path from the DB. The SQLite DB stays small and fast.
- Location of generated artifacts:
  - `instance/skillsprint.db` — main DB
  - `instance/resource_cache/` — synced external content
  - `instance/user_uploads/` — any writeups/screenshots the user submits
  - `bundles/` — shipped with the app (read-only)
  - `static/lessons/<topic-slug>/` — bundled lesson images/SVGs

---

## 9. Removed / Simplified Routes (offline mode)

Existing route | Offline behavior
---|---
`POST /create_order` (Razorpay) | Disabled — returns 404 in `OFFLINE_MODE`
`/login/google/authorized` | Disabled
`POST /contact` (sends email) | Replaced with in-app "Local Inbox" — message stored in a new `LocalInbox` model and shown on dashboard
`auth.py` email-verification flow (`/verify/<token>`) | Auto-marks `email_verified=True` on registration since no SMTP is available
`password reset` (`/reset_password`) | Replaced with a "local reset" flow: admin(user)-set password from the admin panel, or a CLI command `python manage.py reset-password <email>`
`assistant/chat` | Routes Ollama or rules engine (see §7)
`labs/detail` for online-provider labs | Filtered out, never shown
`library/add` external URL fetch | Disabled — user must manually enter title/thumbnail/notes; or links to a `CachedResource` if one exists in the local cache
`admin/community moderation` (v2) | Not built — community features out of scope offline

---

## 10. Local Setup & One-Time Bootstrap

### 10.1 Single-command launcher (`scripts/start_skillsprint.ps1`)
A PowerShell script that:
1. Verifies Python 3.11+ is on PATH.
2. Creates/activates `venv` if missing.
3. `pip install -r requirements.txt` (works offline after first run if wheels are cached, or vendored — see §10.3).
4. Sets `OFFLINE_MODE=true` in `.env` if not set.
5. Runs `python app.py` to start Flask on `http://127.0.0.1:5000`.
6. Opens the default browser to that URL.

### 10.2 Kali VM bootstrap (`scripts/setup_kali_vm.ps1`)
Step 1 of the offline journey: walks the user through installing VirtualBox + Kali, then "Snapshots" a clean state. Listed as an in-app **"Lab setup guide"** link found in:
- the lab browse page footer
- every lab detail page that requires the VM
- the onboarding flow right after the user picks the job-role track

### 10.3 Offline pip install (key for true no-internet recovery)
- Vendored wheels in `bundles/wheels/` for every pinned version in `requirements.txt`. Generated once via `pip download -r requirements.txt -d bundles/wheels/`.
- The launcher detects offline and runs `pip install --no-index --find-links=bundles/wheels -r requirements.txt`.

### 10.4 Ollama installer + model pull (`scripts/setup_ollama.ps1`)
- Detects if `ollama` is on PATH; if absent, prints a link to the Windows installer (one-time online or pre-bundled `OllamaSetup.exe` in `bundles/installers/`).
- Runs `ollama pull <model>` for the recommended model — online just once.
- After this, `OLLAMA_MODEL` env var is set and the tutor uses the local model forever.

---

## 11. Development / Build Roadmap (phased)

### Phase A — Trim & Vendoring (3–5 days)
A1. Add `OFFLINE_MODE` flag to `config.py` with all env defaults.
A2. Gate Razorpay, Google OAuth, SMTP routes behind the flag (keep code; flip off).
A3. Vendor Bootstrap / Bootstrap Icons / Chart.js + a font under `static/vendor/`; update templates + CSP.
A4. Offline pip wheels: run `pip download` once, commit `bundles/wheels/`.
A5. Write `scripts/start_skillsprint.ps1`.
Deliverable: app launches from a clean clone with one PowerShell command, entirely offline, UI renders, the existing assessment → roadmap → dashboard loop still works end-to-end.

### Phase B — Curriculum Expansion (1–2 weeks)
B1. Add Tier 0 (5 new SkillAreas + ~12 Topics) and re-wire DAG prerequisites so existing topics depend on them.
B2. Add Tier 3 (5 advanced SkillAreas + ~25 advanced Topics).
B3. Extend `~250 ContentItem` lesson-Markdown rows in a new `seed_lessons.py` (modular, idempotent).
B4. Extend the 9 `JobRole` rows with `capstone_project_id` + deeper `JobRoleTopic` mappings.
B5. Add 1 `MiniProject` capstone per role (9 total).
Deliverable: the user can pick "Pentester" and see a roadmap of 60+ topics spanning networking basics → AD exploitation → bug bounty → capstone mock OSCP, correctly DAG-ordered.

### Phase C — Interactive In-Browser Exercises (1 week)
C1. Add `exercise_spec` storage (rollback-safe: store in `body_markdown` of `interactive_exercise` ContentItems as JSON for MVP).
C2. Vendored Pyodide under `static/vendor/pyodide/`.
C3. Implement `static/js/exercise_runner.js` covering `code_py`, `quiz_interactive`, `regex_lab`, `cipher_lab`, `pcap_challenge`, `binary_inspector` widgets.
C4. Author ~60 `interactive_exercise` ContentItems, 1–3 per topic across the curriculum.
Deliverable: the learner can do real hands-on activities without ever leaving the browser or installing anything else.

### Phase D — Offline Labs Bundle (1–2 weeks)
D1. Create `bundles/labs/` structure.
D2. Curate or author ~80 offline lab artifacts (PCAPs from public pcap4edu samples, sanitized NTDS.dit, sample vulnerable source packs, mini-CTF ZIP, etc.).
D3. Seed matching `Lab` rows with `provider=self_hosted_offline`, `flag_hash` pre-computed.
D4. Update `labs/browse.html` and `labs/detail.html` to handle offline labs + a "Lab setup guide" page.
D5. Write `scripts/setup_kali_vm.ps1`.
Deliverable: the lab browse page lists 80 offline challenges; clicking one shows the file bundle + flag submission form; submitting the right flag awards XP.

### Phase E — Ollama Tutor + Rules Fallback (3–5 days)
E1. Refactor `ai_tutor_service.py` to strategy picker (§7.1).
E2. Add `TopicHint` model + seed hints for every Topic.
E3. Implement `_ollama_reply()` + `_rules_reply()`.
E4. Add `/settings/ai-tutor` page (model picker, connection test).
E5. Write `scripts/setup_ollama.ps1`.
Deliverable: with Ollama running, the chat widget answers naturally; without Ollama, it gives authored hints tied to the current topic.

### Phase F — Resource Cache + Local Inbox contacts (3–4 days)
F1. Author `resource_catalog.json` (CC-licensed / public-domain pages).
F2. `scripts/sync_resource_cache.ps1` + new `CachedResource` model.
F3. Update `link_metadata_service.py` to read from local cache instead of live HTTP.
F4. Replace `/contact` mail send with `LocalInbox` model + dashboard notification.
Deliverable: after one `sync_resource_cache.ps1` run, the platform serves cached external content offline; the contact form works locally.

### Phase G — Polish, Admin CMS, Analytics (1 week)
G1. Admin CMS extension in `admin.py` for Topics / ContentItems / Labs / TopicsHints (CRUD).
G2. Skill radar chart on `/progress` (already exists — confirm Chart.js renders offline).
G3. In-app "Lab setup guide", "AI tutor setup", "About offline mode" static pages.
G4. Single-user onboarding simplification (auto-verify emails, skip payment step).
Deliverable: a single administrator (you) can add topics, lessons, labs, hints without editing code — but everything runs locally and offline.

**Estimated total: ~6–9 weeks of dedicated solo work**, expandable based on lesson-writing throughput in Phase B.

---

## 12. Folder Structure (additions to current repo)

```
SKILLSPRINT_ACADEMY/
├── app.py, auth.py, admin.py, config.py, extensions.py, forms.py, models.py  (modified)
├── seed.py                  (extended with Tier 0 + Tier 3)
├── seed_lessons.py           (new — Markdown lesson seeds)
├── seed_exercises.py         (new — interactive_exercise seeds)
├── seed_offline_labs.py      (new — self_hosted_offline Lab rows)
├── seed_topic_hints.py       (new — TopicHint seeds for rules fallback)
├── manage.py                 (new — CLI for local password reset, re-seed, etc.)
├── blueprints/  (existing, light edits)
├── services/  (existing, ai_tutor_service.py heavily refactored)
├── bundles/                  (NEW — shipped, read-only)
│   ├── labs/                 (PCAPs, source zips, NTDS, mini-CTF ZIP, etc.)
│   ├── installers/           (OllamaSetup.exe, Kali .ova — too big for git? use LFS or instructions)
│   └── wheels/               (offline pip wheels)
├── scripts/                  (NEW)
│   ├── start_skillsprint.ps1
│   ├── setup_kali_vm.ps1
│   ├── setup_ollama.ps1
│   └── sync_resource_cache.ps1
├── static/
│   ├── vendor/               (NEW — Bootstrap, Chart.js, Pyodide, fonts)
│   ├── lessons/              (NEW — lesson images/SVGs by topic slug)
│   └── js/exercise_runner.js (NEW)
├── templates/
│   ├── exercises/            (NEW — per-kind interactive templates)
│   ├── offline/             (NEW — setup guides, lab setup helper, AI tutor settings)
│   └── ...existing...
└── instance/
    ├── skillsprint.db
    ├── resource_cache/       (NEW — populated by sync_resource_cache)
    └── user_uploads/
```

---

## 13. Curriculum Preview — Pentester track (0 → Job-Ready → Expert)

Illustrative subset to show the depth; full mapping lives in `seed.py` post-Phase B.

```
Tier 0 — Absolute Foundations
  Computing Foundations → Security Mindset & Ethics
  → Networking Basics → Linux Fundamentals → Windows Fundamentals

Tier 1 — Core Technical Security
  → TCP/IP Deep → Wireshark → HTTP & Web Basics → OWASP Top 10
  → Scripting & Python → Cryptography Foundations → OSINT Foundations

Tier 2 — Systems & AD
  → Windows Internals → Active Directory Fundamentals → BloodHound
  → Linux Hardening → Packet Forensics

Tier 3 — Advanced Offensive
  → SQLi/XSS Deep → Burp Suite Pro techniques
  → Exploit Dev: Stack Overflow → ROP → Bypassing Mitigations
  → Red Team Ops: C2 → Lateral Movement → OPSEC
  → Bug Bounty Methodology

Tier 4 — Capstone
  → Mock OSCP 24-hour Lab (bundled vulnerable VM pack, 5 machines)
  → Write-up Authoring → Submit & self-grade by checklist
```

Each topic has: Markdown lesson · interactive exercise · 1–3 labs from `bundles/labs/` · checkpoint quiz · roadmap-scheduled completion · XP award.

---

## 14. Non-Functional (offline-flavored)

- **Security:** Since it's a security-training system that runs as a local Flask dev server, default to `127.0.0.1` only (the existing `host="0.0.0.0"` in `app.py:320` is overridden to `127.0.0.1` when `OFFLINE_MODE=true`).
- **No SSRF risk:** the metadata-scraping service is gone offline; external URL metadata comes from local cache only.
- **Lab sandboxing:** bundled challenge files are read-only static artifacts; the Kali VM is the user's own sandboxed guest. No host-network bridging required — host-only adapter for the VM is the recommended default.
- **Resilience:** zero internet dependency after first setup — verified by an `offline_check.py` test that asserts no route makes an outbound HTTP call when `OFFLINE_MODE=true`.
- **Talisman CSP** is tightened to `'self'` only in offline mode (no remote scripts/fonts/styles).
- **Privacy:** truly zero data leaves the machine (no analytics, no telemetry, no email).
- **Backup:** `scripts/backup_progress.ps1` zips `instance/` for user-defined snapshots before risky phases (optional, deferred to v2 polish).

---

## 15. Success Definition (single-user)

1. After running `start_skillsprint.ps1` once, the user lands on the dashboard.
2. They pick "Penetration Tester", complete the 0 → 100 path across all 5 tiers.
3. They can take the in-browser exercises, attempt bundled labs against the local Kali VM, ask the AI tutor (Ollama) questions, and earn XP/streaks — all without touching the internet.
4. On completing a JobRole track, the capstone bundle is loaded in the Kali VM, and the final write-up + flag submissions are graded automatically where feasible.
5. The user's skill radar on `/progress` visibly grows from all-area-zero to a populated OSCP-ready profile.

"When someone with zero background can sit down at this machine, follow the dashboard for 6 months, and walk out able to land a junior pentester job — Phase B's curriculum + Phase D's labs succeeded."

---

## 16. Immediate Next Steps (Actionable, in order)

1. **Phase A1–A2:** Add `OFFLINE_MODE` flag and gate the three external-internet routes (Razorpay, OAuth, SMTP). Verify the app still boots and the existing assessment → roadmap loop runs.
2. **Phase A3–A5:** Vendor Bootstrap/Chart.js/font, write `start_skillsprint.ps1`. You now have a one-click offline launcher.
3. **Phase D1–D2:** Begin assembling `bundles/labs/` — start with the easiest win (10 PCAP challenges from public-domain datasets + 20 mini-CTF challenges). Wire the matching `Lab` rows.
4. **Phase E1:** Refactor `ai_tutor_service.py` to try Ollama, fall back to rules. Even with zero authored hints, the rules fallback tells the user "Ollama not running — set me up".
5. **Phase B1:** Add Tier 0 SkillAreas & Topics + re-wire prerequisites; users with zero background now get a valid entry point.
6. Then proceed through B → C → D → E → F → G in parallel where the content-authoring work can be staggered.

---

## 17. What This Plan Deliberately Does NOT Do (deferred)

- Live multi-user cloud deployment, containers orchestration (Kubernetes), CI/CD — out of scope.
- Tier-2 Docker app-labs (DVWA, Juice Shop running in containers) — optional Phase D+ once Docker is confirmed on the user's machine; the bundled-challenge approach is preferred first.
- True CAT/IRT-based adaptive assessment (the existing `assessment_engine` is a simple per-area fixed-N version) — the user can reseed more questions per area in Phase B but the engine itself stays as is.
- Mobile app, native push notifications, employer-facing "verified skill" export — all v2 of the cloud plan, ignored offline.
- Auto-translate lessons — bundled lessons are in English (or whichever language you author them in).
