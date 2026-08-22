# SkillSprint Academy — Cybersecurity Personalized Learning Platform
### Complete Project Plan

---

## 0. About This Document

This plan turns your existing repo (`Shadow-Howl-Sec/SKILLSPRINT_ACADEMY`) — currently a generic Flask course-selling platform (auth, Razorpay payments, course/enrollment/practice-test/mini-project models, admin panel) — into a **cybersecurity-focused adaptive learning platform**, inspired by Hack The Box (HTB), TryHackMe (THM), LetsDefend, and RangeForce.

Core loop: `Pick a course/role → Take an assessment → Get a personalized roadmap → Get a daily study schedule → Study on a dashboard → Do labs → Track progress → Roadmap adapts`.

---

## 1. What Already Exists in Your Repo (Reusable Foundation)

| File | What it does today | Keep / Extend / Replace |
|---|---|---|
| `models.py` | `User`, `Course`, `Enrollment`, `Payment`, `Coupon`, `AdminLog`, `PracticeTest`, `TestAttempt`, `MiniProject`, `ProjectSubmission` | **Keep & extend.** Good base — add new tables (see §7). |
| `auth.py` | Registration, login, password reset, email verification | **Keep.** Add OAuth (Google), 2FA later. |
| `admin.py` | Admin dashboards/APIs | **Extend** — add roadmap/lab/content management. |
| `app.py` | Entry point, main routes | **Restructure** into blueprints as app grows (see §12). |
| `config.py`, `extensions.py`, `forms.py` | Flask config, extensions, WTForms | **Keep.** |
| Razorpay/payment logic | Paid course purchase | **Keep**, but re-scope: sell "Pro roadmap / labs" subscriptions instead of flat courses (see §14 Monetization). |

**Gap analysis — what's missing for your vision:**
1. No skill-assessment engine (adaptive quiz to gauge starting level).
2. No roadmap-generation engine (rule-based/AI logic mapping assessment → personalized path).
3. No job-role tracks (e.g., SOC Analyst, Pentester).
4. No virtual lab environment or lab-provider integration.
5. No daily scheduler that fits study into the user's available hours.
6. No "today's dashboard" view.
7. No external-link ingestion system (user adds a YouTube/Udemy/blog link → it gets slotted into the schedule).
8. No AI tutor/chat assistant.
9. No progress-adaptive re-planning (roadmap should adjust if user falls behind or aces something).

---

## 2. Reference Platform Analysis

| Platform | What to borrow | What to avoid/skip for MVP |
|---|---|---|
| **TryHackMe** | Guided "Learning Paths" (Pre Security, Jr Penetration Tester), room-based micro-lessons + embedded VM, streak tracking, beginner-friendly UX | Their full custom VPN/VM infra (too heavy for MVP) |
| **Hack The Box** | Skill-based ranking (Noob→Omniscient), realistic machine-based labs, Academy modules with cubes/tiers, job-role paths (Pentester, SOC Analyst, Bug Bounty) | Their proprietary lab network engineering (replicate via Docker/cloud VMs instead) |
| **LetsDefend** | SOC-analyst-specific simulated alerts/dashboard (great model for "Blue Team" job-role track) | — |
| **RangeForce** | Enterprise skill-gap assessment mapped to NIST/MITRE ATT&CK | Use MITRE ATT&CK / NIST NICE framework as your **skill taxonomy backbone** — this is the single best design decision you can make |
| **Coursera / Udemy** | Structured video + quiz sequencing, certificates | — |
| **Duolingo** | Daily streak, XP, spaced repetition scheduling, gentle daily nudge notifications | — |

**Key design takeaway:** Anchor your skill taxonomy on an established framework — **NIST NICE Cybersecurity Workforce Framework** (role definitions) + **MITRE ATT&CK** (technique/skill tags). This makes your assessment-to-roadmap mapping defensible, extensible, and industry-recognizable instead of ad hoc.

---

## 3. Product Vision & Goals

**Vision:** *"A personal cybersecurity mentor that knows exactly where you stand, tells you exactly what to do today, and gets you job-ready — using the best labs and content on the internet, whether we host them or someone else does."*

**MVP Goals (v1):**
- User can pick a **domain** (Cybersecurity) → a **track** (general skill-based OR specific job role).
- User takes an **adaptive assessment**.
- System generates a **personalized roadmap** (topics, order, resources, labs, estimated hours).
- Roadmap is broken into a **daily schedule** based on user's available time/day.
- **Dashboard** shows "Today," with tasks, links, lab access, and quick actions.
- User can **add external links** (YouTube, blog, PDF, other course) which get slotted into their schedule like any other resource.
- Progress is tracked; missed days trigger **re-scheduling**, not guilt-tripping.

**v2+ Goals:** live labs (own infra), AI chat tutor, mock interviews, certificates, community/leaderboard, mobile app, employer-facing "verified skill" export.

---

## 4. User Personas

1. **Aditya, 2nd-year CS student** — wants to break into cybersecurity, zero background, needs full "beginner path," ~1 hr/day.
2. **Priya, working professional (network admin)** — wants to become SOC Analyst, has decent networking knowledge, 30 min/day, needs targeted gap-filling not a full beginner course.
3. **Rahul, self-taught, prepping for OSCP** — wants a pentester job-role track with heavy lab time, 3 hrs/day on weekends.
4. **Admin/Content curator (you)** — needs to add courses, labs, questions, and external resources easily, and monitor engagement.

---

## 5. Core Feature List (Detailed)

### 5.1 Onboarding & Domain/Track Selection
- Landing → Sign up (email+password or Google OAuth, reuse existing `auth.py`).
- Step 1: Choose **Domain** — for MVP just "Cybersecurity" (architecture supports adding "Cloud," "Data Science" later — this matches your `Course.category` field already).
- Step 2: Choose **Goal type**:
  - (a) *General skill track* — "I want to learn Cybersecurity broadly."
  - (b) *Job-role track* — pick from: SOC Analyst (L1/L2), Penetration Tester, Red Teamer, Blue Team/Incident Responder, Cloud Security Engineer, Application Security Engineer, GRC Analyst, Bug Bounty Hunter.
- Step 3: Set **weekly availability** — days available + hours/day per day (e.g., Mon-Fri 1hr, Sat-Sun 3hr) → stored as a weekly template, editable anytime.
- Step 4: Take the **Skill Assessment** (see §5.2).

### 5.2 Adaptive Skill Assessment Engine
- Question bank tagged by: `domain_area` (Networking, Linux, Web App Sec, Crypto, OSINT, Cloud, Scripting, Windows/AD, Malware Analysis, Cryptography, GRC, etc.), `difficulty` (1-5), `mitre_technique_id` (optional), `job_roles[]` (which roles this maps to).
- **Adaptive logic (Computerized Adaptive Testing - CAT lite):**
  - Start at medium difficulty per domain area.
  - Correct answer → next question in that area is harder; wrong → easier.
  - Stop a domain area after N questions or when confidence interval on skill estimate is tight enough (simple version: fixed 5 questions/area for MVP; true IRT/Elo-based CAT for v2).
  - Include a few **practical/scenario-based questions** (not just MCQ) where possible — e.g., "what command would you run to..." — scored by keyword/regex matching for MVP, full lab-graded practicals in v2.
- Output: a **Skill Profile** — per-domain-area score (0-100) + overall level (Beginner/Intermediate/Advanced) + confidence flags ("Not enough data on Cloud Security — treated as beginner").
- Assessment retake allowed every N days (or on demand) to recalibrate roadmap.

### 5.3 Roadmap Generation Engine ⭐ (core differentiator)
This is the heart of the product. Two-layer design:

**Layer A — Curriculum Graph (admin-authored, reusable):**
- A directed graph/DAG of **Topics**, each with prerequisites.
  - e.g., `Networking Basics → Linux Fundamentals → Web App Basics → OWASP Top 10 → Burp Suite → SQLi/XSS Labs → ...`
- Each Topic has: theory resources (in-house lessons, external links, videos), practice questions, and 0+ **Labs**.
- Each **Job Role** has a mapped **subset + ordering** of the graph (a template roadmap), e.g. "SOC Analyst" path = Networking → Windows/Linux basics → SIEM/Log analysis → Incident Response → (skip most of Web App Pentesting).

**Layer B — Personalization Algorithm (per user):**
```
INPUT: skill_profile (per-area scores), goal (general | job_role), weekly_availability_hours

1. Select base template:
   - If job_role selected → start from that role's Topic DAG.
   - Else → start from "General Cybersecurity Foundations" DAG.

2. Prune / reorder using skill_profile:
   - For each Topic, compute a "readiness score" from prerequisite area scores.
   - If user already scores high (>80%) in a Topic's area → mark as "Skip / Quick Review" 
     (still listed, but compressed into a 1-item checkpoint quiz instead of full lessons).
   - If user scores low in an area that ISN'T on the direct path to the goal but is a 
     prerequisite → insert a remedial mini-module before the dependent topic.

3. Estimate time per topic:
   - Each resource/lab has an estimated_minutes field (admin-set, refined later by 
     actual completion-time analytics across all users).
   - Sum → total roadmap hours.

4. Sequence into calendar using weekly_availability_hours:
   - Greedy bin-packing: fill each available day with topic items up to that day's hour 
     budget, respecting DAG order (don't schedule a topic before its prerequisite topic 
     is scheduled).
   - Reserve ~20% buffer time per week for review/catch-up (spaced repetition of 
     completed topics using a simple SM-2-like interval schedule).

5. Output: RoadmapItem[] each mapped to a specific calendar date + ordering index.
```
- Roadmap is **not fixed** — nightly job (or on-demand) re-evaluates: if user is ahead of schedule, pull future items forward; if behind, auto-compress (drop "optional/stretch" resources first) or push dates back and notify user.
- User can **manually reorder/swap out** resources for an equivalent one (e.g., swap "video lesson" for "written article" on the same topic) — respects different learning styles.

### 5.4 Job-Role Tracks
- Admin-curated list, each a Topic-DAG template + a **role description card** (what the job does, average salary range info if desired, required certs like Security+, CEH, OSCP, typical interview topics).
- Examples to seed: SOC Analyst, Penetration Tester, Red Team Operator, Cloud Security Engineer, AppSec Engineer, DFIR/Incident Responder, GRC/Compliance Analyst, Bug Bounty Hunter, Malware Analyst.
- Each role's roadmap ends with a **"Job-Ready Checklist"**: skills mastered, certs recommended, a mock-interview module (v2), and a portfolio project list (reuses your existing `MiniProject` model!).

### 5.5 Virtual Labs
Three integration tiers — build in this order:

1. **Tier 1 (MVP, fastest): Link-out labs.** Curate and embed links to free rooms/labs on TryHackMe, HTB Academy (free tier), OverTheWire, PicoCTF, PortSwigger Web Security Academy (fully free, great for AppSec). Track completion via **self-report + a proof field** (flag submission text box, screenshot upload, or write-up link) — reuses your existing `ProjectSubmission` pattern.
2. **Tier 2 (in-house, moderate effort): Dockerized challenge labs.** Host your own simple vulnerable containers (DVWA, Juice Shop, WebGoat, bWAPP, custom CTF-style challenges) on a cloud VM; spin up per-user via Docker + a reverse proxy (Traefik) with a session timeout; user submits a **flag** which the backend validates (like a CTF flag-checker) → auto-marks lab complete + awards XP.
3. **Tier 3 (v2+, resource-heavy): Full attack-range VMs.** Guacamole (Apache) + KVM/Proxmox or cloud (AWS/Azure) for real Windows/AD labs, browser-based RDP/SSH access like HTB Pwnbox — significant infra cost, defer until you have paying users to justify it.

Every lab entry has: `lab_provider` (self-hosted/HTB/THM/PortSwigger/etc.), `url_or_container_ref`, `difficulty`, `estimated_minutes`, `flag_or_proof_type`, `xp_reward`, `mitre_techniques[]`.

### 5.6 Theory / Content Module
- Lesson types: in-house written lesson (Markdown-rendered), embedded video (YouTube/self-hosted), PDF/slide, external article link, quiz checkpoint.
- Each Course/Topic has an ordered list of Content Items (extend existing `Course.roadmap_steps`/`video_links` JSON fields into a proper `ContentItem` table — see §7).
- Support **admin CMS** to add/edit/reorder content without code changes (Markdown editor + drag-drop ordering in admin panel).

### 5.7 External Resource / "Add Your Own Course" Feature ⭐ (your explicit ask)
- User-facing "Add a Resource" button anywhere in the roadmap/dashboard:
  - Paste a URL (YouTube, Udemy, blog, PDF, GitHub repo, another platform's course link).
  - Auto-fetch metadata (title, thumbnail via oEmbed/OpenGraph scraping) — fallback to manual entry.
  - User sets: estimated time to complete, which Topic/skill area it belongs to (dropdown from taxonomy), and where in the schedule to slot it (today / this week / append to roadmap after a specific topic).
  - Once added, it behaves exactly like any platform-native resource: appears on dashboard, can be marked complete, counts toward XP/streak.
- **Personal Library** page — all external links a user has added, reusable/reorderable, optionally shareable (v2: "publish to community" so good external finds become admin-reviewed additions to the global content pool).

### 5.8 Daily Scheduler / Calendar
- **Today view** (dashboard default): list of today's scheduled items in order — theory, quiz, lab, external resource — each with checkbox, estimated time, and quick-launch link.
- **Week/Month calendar view**: drag-and-drop reschedule of any pending item (updates the roadmap engine's plan, doesn't just move a UI card).
- **Availability settings**: editable anytime (e.g., "I'm traveling next week, reduce to 15 min/day") → triggers re-plan (§5.3 step 5).
- **Smart reminders**: push/email at user's preferred time ("Your 6 PM cybersecurity session is ready — today: SQL Injection basics + 1 lab, ~45 min").
- Spaced-repetition review items auto-inserted (e.g., "Quick review: Networking basics" reappears 7/21/45 days after first completion).

### 5.9 Dashboard (Post-login Home)
Sections:
1. **Header strip:** current streak (days), XP/level, overall roadmap progress %, days-to-target-date estimate.
2. **Today's Schedule:** ordered task list (from §5.8), each with type icon (theory/lab/quiz/external), time estimate, "Start" button.
3. **Continue where you left off:** last incomplete item, one click resume.
4. **This week at a glance:** mini calendar strip.
5. **Roadmap snapshot:** progress bar per major phase (e.g., Foundations 100%, Web AppSec 40%, Labs 25%).
6. **Recommended next external resources** (optional, admin/AI curated based on gaps).
7. **Notifications/announcements** (new lab added, streak about to break, etc.).
8. **Quick links:** Personal Library, Job-Role Info, Assessment Retake, Settings.

### 5.10 AI "Personal Teacher" Assistant
- Chat widget available on every page (dashboard, lesson, lab pages).
- Capabilities (MVP → advanced):
  - MVP: Answer conceptual questions about the current topic using an LLM (Anthropic API) with the lesson content as context (RAG over your own content library).
  - Explain-like-I'm-5 / deeper-dive toggle for any lesson.
  - Hint system for labs (progressive hints, doesn't give the flag directly — preserves learning value, mirrors HTB's hint system).
  - v2: Can answer "why is my roadmap structured this way" and let user request roadmap adjustments in natural language ("I want to focus more on cloud security this month") which calls the roadmap engine's re-plan function.
  - v2: Mock interview mode for job-role tracks (LLM role-plays as interviewer for chosen role, e.g., SOC Analyst interview questions).

### 5.11 Gamification & Motivation
- XP per completed item (weighted by difficulty), levels, streak counter (with 1 "streak freeze" per week to reduce burnout-guilt like Duolingo), badges (e.g., "First Blood" for first lab, "7-Day Warrior"), optional public/friends leaderboard (opt-in, privacy-respecting).

### 5.12 Progress Tracking & Analytics
- Per-user: skill radar chart (per domain area, before vs. now), completion history, time-spent analytics, assessment score trend over retakes.
- Per-admin: content engagement (which lessons/labs are skipped, average completion time vs. estimate — feeds back into §5.3 step 3 estimates), drop-off points in roadmaps, most-added external resources (surface candidates for official curation).

### 5.13 Admin Panel (extends existing `admin.py`)
- Manage: Topics/DAG editor, Job Role templates, Assessment question bank, Labs (incl. Docker image refs for Tier 2), Content Items, Users, Coupons/Payments (existing), review queue for user-submitted external resources wanting to go "official," moderation of any community features.
- Dashboard: DAU/WAU, retention/streak stats, revenue (existing Payment model), roadmap completion funnel.

---

## 6. Information Architecture / Sitemap

```
/                              Landing page
/signup, /login                Auth (existing)
/onboarding/domain              Step 1: choose domain
/onboarding/goal                 Step 2: general vs job-role
/onboarding/availability          Step 3: weekly hours
/assessment/:trackId               Step 4: adaptive quiz
/assessment/:trackId/result          Skill profile summary + "Generate my roadmap"
/dashboard                     Today view (home after login)
/roadmap                       Full roadmap (phases/topics, progress)
/roadmap/calendar              Week/Month calendar, drag-reschedule
/topic/:id                     Topic detail: theory + resources + linked labs
/lesson/:id                    Individual lesson/content item viewer
/lab/:id                       Lab launcher (embed / redirect / flag submission)
/library                       My added external resources
/library/add                   Add external resource modal/page
/job-roles                     Browse job-role tracks
/job-roles/:id                 Role detail + "Start this track"
/progress                      Analytics: skill radar, history, streak calendar
/assistant                     Full-page AI tutor chat (also as floating widget)
/settings/availability         Edit weekly schedule
/settings/profile              Account settings
/leaderboard                   Optional gamification page
/admin/...                     Existing + new admin CMS pages
```

---

## 7. Database Schema (extends `models.py`)

**Existing tables kept as-is:** `User`, `Payment`, `Coupon`, `AdminLog`.
**Existing tables repurposed:** `Course` → becomes a "Track" (job-role or general); `PracticeTest`/`TestAttempt` → reused for both assessments AND topic checkpoint quizzes; `MiniProject`/`ProjectSubmission` → reused for portfolio projects AND lab flag submissions.

**New tables to add:**

```
SkillArea
  id, name (e.g. "Web App Security"), slug, description, parent_id (nullable, for sub-areas)

Topic
  id, title, slug, description, skill_area_id (FK), difficulty (1-5),
  estimated_minutes, is_active
TopicPrerequisite            # DAG edges
  id, topic_id (FK), prerequisite_topic_id (FK)

JobRole
  id, name, slug, description, avg_salary_note, recommended_certs (JSON),
  icon_url, is_active
JobRoleTopic                 # ordered template mapping
  id, job_role_id (FK), topic_id (FK), order_index, is_core (bool: core vs optional)

ContentItem                  # theory content, replaces loose JSON fields on Course
  id, topic_id (FK), type (lesson_md | video | pdf | external_link | quiz_checkpoint),
  title, body_markdown (nullable), url (nullable), estimated_minutes,
  order_index, source (in_house | external_admin | external_user), created_by_user_id (nullable)

Lab
  id, topic_id (FK), title, description, provider (self_hosted | tryhackme | htb |
  portswigger | overthewire | picoctf | other), url_or_container_ref,
  difficulty, estimated_minutes, proof_type (flag | screenshot | writeup_url),
  flag_hash (nullable, for self-hosted flag checking), xp_reward

AssessmentQuestion
  id, skill_area_id (FK), question_text, question_type (mcq | short_answer | scenario),
  options (JSON, for mcq), correct_answer, difficulty (1-5),
  mitre_technique_id (nullable), job_roles (JSON list of applicable role slugs)

AssessmentSession             # one per assessment attempt
  id, user_id (FK), track_type (general | job_role), job_role_id (nullable FK),
  started_at, completed_at, status (in_progress | completed)
AssessmentResponse
  id, session_id (FK), question_id (FK), answer_given, is_correct, difficulty_at_time

SkillProfile                  # latest computed scores per user per area
  id, user_id (FK), skill_area_id (FK), score (0-100), confidence (low|medium|high),
  last_updated

Roadmap
  id, user_id (FK), job_role_id (nullable FK), created_at, target_completion_date,
  status (active | paused | completed), version (int, increments on re-plan)
RoadmapItem
  id, roadmap_id (FK), item_type (content_item | lab | checkpoint_quiz | review),
  content_item_id / lab_id / topic_id (nullable FKs as applicable),
  scheduled_date, order_index, status (pending | in_progress | done | skipped),
  estimated_minutes, actual_minutes (nullable), completed_at (nullable)

WeeklyAvailability
  id, user_id (FK), day_of_week (0-6), available_minutes

UserResource                  # "add your own course" library
  id, user_id (FK), title, url, resource_type (video|article|course|pdf|other),
  thumbnail_url, estimated_minutes, skill_area_id (nullable FK), added_at,
  is_shared_to_community (bool, v2), review_status (v2: pending|approved|rejected)

XPLog
  id, user_id (FK), source_type (roadmap_item|lab|streak_bonus), source_id, xp_amount, created_at
StreakRecord
  id, user_id (FK), current_streak, longest_streak, last_active_date, freezes_available

ChatMessage                   # AI tutor history (for context + review)
  id, user_id (FK), session_id, role (user|assistant), content, related_topic_id (nullable),
  created_at
```

---

## 8. System Architecture

```
                         ┌─────────────────────────┐
                         │   Browser (Web App)      │
                         │ HTML/Jinja2 + JS + Chart.js│
                         └──────────┬───────────────┘
                                    │ HTTPS
                    ┌───────────────▼────────────────┐
                    │      Flask App (Blueprints)      │
                    │  auth | onboarding | assessment  │
                    │  roadmap | dashboard | labs       │
                    │  library | admin | assistant(API) │
                    └───┬───────────┬───────────┬──────┘
                        │           │           │
              ┌─────────▼──┐ ┌──────▼─────┐ ┌───▼─────────────┐
              │ PostgreSQL │ │ Redis       │ │ Background Jobs  │
              │ (SQLAlchemy│ │ (cache,     │ │ (Celery/RQ):     │
              │  models)   │ │  session,   │ │ nightly re-plan, │
              │            │ │  rate-limit)│ │ email/push cron, │
              └────────────┘ └─────────────┘ │ metadata scraping│
                                              └──────────────────┘
     ┌────────────────────────┐   ┌─────────────────────────┐
     │ Docker Lab Host (Tier2)│   │ Anthropic API (AI Tutor) │
     │ Traefik + per-user     │   │ + RAG over ContentItem   │
     │ ephemeral containers    │   │ table (embeddings store) │
     └────────────────────────┘   └─────────────────────────┘
```

**Recommended tech stack:**
- **Backend:** Flask (keep — reuse existing codebase), Blueprints for modularity, SQLAlchemy (existing), Celery + Redis for background jobs (roadmap re-plan, reminders, streak checks) — or lightweight `APScheduler` if you want to avoid a Celery worker for MVP.
- **DB:** Move from SQLite (dev) → PostgreSQL (prod) — you'll need JSONB and better concurrency once assessments/roadmaps get relational.
- **Frontend:** Keep server-rendered Jinja2 + Bootstrap (matches existing `templates/`/`static/`) for MVP speed; consider htmx for the drag-drop calendar and dashboard interactivity without a full SPA rewrite. Chart.js for skill radar/progress charts.
- **Auth:** Flask-Login (existing) + Google OAuth (`GOOGLE_OAUTH_CLIENT_ID` already in your `.env` template — just needs implementing).
- **AI Tutor:** Anthropic API (Claude) — use tool/RAG pattern: retrieve relevant `ContentItem` rows (simple keyword or pgvector embedding search) and pass as context.
- **Labs Tier 2:** Docker + Traefik on a single cloud VM (DigitalOcean/Hetzner cheap tier) to start; move to Kubernetes only once scale demands it.
- **Email:** Flask-Mail (existing config) for reminders/verification.
- **Push notifications:** Web Push (VAPID) for browser; defer native mobile push until a mobile app exists.

---

## 9. API Endpoint Sketch (selected)

```
POST   /api/onboarding/availability          save weekly hours
POST   /api/assessment/start                  {track_type, job_role_id?} → session_id
GET    /api/assessment/:session_id/next       next adaptive question
POST   /api/assessment/:session_id/answer     submit answer → next question or "complete"
GET    /api/assessment/:session_id/result     skill profile summary
POST   /api/roadmap/generate                  {skill_profile, job_role_id?} → roadmap_id
POST   /api/roadmap/replan                    triggered by availability change / drift
GET    /api/dashboard/today                   today's RoadmapItems
POST   /api/roadmap-item/:id/complete         mark done, log XP, update streak
POST   /api/lab/:id/submit-flag               validate flag, mark complete
POST   /api/library/add                       add external resource (URL, metadata)
POST   /api/library/:id/schedule              slot into roadmap on a date
POST   /api/assistant/chat                    {message, context_topic_id} → AI response
GET    /api/progress/skill-radar               chart data
GET    /admin/api/topics (CRUD)                content management
GET    /admin/api/labs (CRUD)
GET    /admin/api/questions (CRUD)
```

---

## 10. Suggested Folder Structure

```
skillsprint/
├── app.py                     # app factory, blueprint registration
├── config.py
├── extensions.py
├── models/
│   ├── user.py  ├── course_track.py  ├── assessment.py
│   ├── roadmap.py  ├── content_lab.py  ├── gamification.py
├── blueprints/
│   ├── auth/            (existing, extended w/ OAuth)
│   ├── onboarding/
│   ├── assessment/
│   ├── roadmap/
│   ├── dashboard/
│   ├── labs/
│   ├── library/
│   ├── assistant/
│   └── admin/            (existing, extended)
├── services/
│   ├── roadmap_engine.py      # §5.3 algorithm
│   ├── assessment_engine.py   # adaptive question selection + scoring
│   ├── scheduler_service.py   # bin-packing + re-plan
│   ├── xp_service.py
│   ├── link_metadata_service.py  # oEmbed/OpenGraph fetch for external links
│   └── ai_tutor_service.py    # Anthropic API wrapper + RAG
├── tasks/                     # Celery/APScheduler jobs
│   ├── nightly_replan.py
│   ├── reminder_emails.py
│   └── streak_check.py
├── static/  (existing)
├── templates/  (existing, extended)
├── migrations/                # Flask-Migrate/Alembic (add this — you don't have it yet)
├── tests/
├── requirements.txt
└── README.md
```

**Immediate technical debt to address early:** add **Flask-Migrate** (Alembic) now — your current setup auto-creates tables on startup with no migration history, which will break the moment you need to alter a table in production.

---

## 11. Development Roadmap / Phases

**Phase 0 — Foundations (1-2 weeks)**
- Add Flask-Migrate, move dev DB to Postgres, restructure `app.py` into blueprints, set up staging environment.

**Phase 1 — Assessment + Static Roadmap (2-3 weeks)**
- `SkillArea`, `Topic`, `TopicPrerequisite`, `AssessmentQuestion/Session/Response`, `SkillProfile` tables.
- Build assessment UI + basic (non-adaptive first, adaptive later) scoring.
- Seed ~150-200 questions across 8-10 skill areas (Networking, Linux, Web Security, Windows/AD basics, Cryptography, OSINT, Scripting/Python, Cloud basics).
- Roadmap engine v0: rule-based, non-time-boxed (just an ordered topic list per skill profile).

**Phase 2 — Scheduling + Dashboard (2-3 weeks)**
- `WeeklyAvailability`, `Roadmap`, `RoadmapItem` tables + bin-packing scheduler.
- Build Today dashboard, calendar view, streak/XP system.

**Phase 3 — Content + External Library (2 weeks)**
- `ContentItem` CMS in admin, seed initial lessons for top 3-4 topics (Networking, Linux, Web AppSec basics — link out to PortSwigger Academy which is free and excellent for this).
- Build "Add External Resource" flow + metadata scraping.

**Phase 4 — Labs Tier 1 (1-2 weeks)**
- `Lab` table, curate ~30-50 free rooms/labs from TryHackMe/HTB Academy free tier/PortSwigger/OverTheWire, proof-submission UI.

**Phase 5 — Job Roles (1-2 weeks)**
- `JobRole`, `JobRoleTopic`; seed 3 initial roles (SOC Analyst, Penetration Tester, AppSec Engineer — pick the 3 with best free-lab coverage first).

**Phase 6 — AI Tutor MVP (1-2 weeks)**
- Chat widget + Anthropic API integration + simple RAG over `ContentItem`.

**Phase 7 — Polish, Analytics, Beta Launch (2 weeks)**
- Progress/analytics pages, admin dashboards, bug bash, invite beta users (your college/network is a great first cohort given the existing `college`/`branch` fields in `User`!).

**Post-MVP (v2 backlog):** Tier 2/3 self-hosted labs, adaptive IRT-based assessment, community-shared external resources with moderation, mock interview mode, mobile app, certificates/verified-skill export, team/college accounts.

---

## 12. Non-Functional Requirements

- **Security (must be exemplary — it's a security-education product):** bcrypt/argon2 password hashing (verify `werkzeug` config strength), rate-limiting on auth + assessment endpoints, CSRF protection (Flask-WTF, likely already partial via `forms.py`), input sanitization for user-submitted external URLs (SSRF protection when scraping metadata — never fetch internal/private IP ranges), sandboxing for any self-hosted lab containers (no host network access, resource limits, auto-destroy after session).
- **Privacy:** clear data policy since you collect college/branch/phone (existing fields) — make these optional or clearly disclosed.
- **Performance:** cache skill-taxonomy and topic-DAG reads (Redis) since roadmap generation is read-heavy on relatively static reference data.
- **Accessibility:** keyboard navigation for dashboard, alt text for icons, WCAG AA color contrast.
- **Scalability:** keep lab hosting decoupled (separate VM/service) from the main app so a lab-usage spike doesn't take down the core platform.

---

## 13. MITRE ATT&CK / NIST NICE Mapping (Recommended Taxonomy Seed)

Use NIST NICE work roles as your `JobRole` seed list (industry-standard, gives you credibility and easy resume/cert alignment):
- Cyber Defense Analyst (≈ SOC Analyst)
- Vulnerability Assessment Analyst (≈ Pentester Jr.)
- Exploitation Analyst / Penetration Tester
- Incident Responder
- Secure Software Assessor (≈ AppSec)
- Systems Security Analyst / Cloud Security

Tag `AssessmentQuestion` and `Lab` rows with relevant **MITRE ATT&CK technique IDs** where applicable (e.g., T1110 Brute Force, T1059 Command/Scripting Interpreter) — this lets you later show users "you've demonstrated skill against these real-world adversary techniques," which is a strong differentiator over generic course platforms.

---

## 14. Monetization (adjust existing Payment/Coupon system)

- **Freemium model:** Free tier = 1 active roadmap, Tier-1 (link-out) labs only, limited AI tutor messages/day.
- **Pro subscription** (reuse `Payment`/`Coupon`/Razorpay integration, switch from one-time `Course` purchase to recurring): unlocks self-hosted labs (Tier 2/3), unlimited AI tutor, multiple parallel roadmaps (e.g., prep for 2 job roles), priority content requests, certificate/export.
- Optional: **College/Team plans** (you already capture `college`/`branch` — natural upsell to campus placement cells).

---

## 15. Success Metrics

- Assessment completion rate, roadmap adherence rate (% of scheduled items completed on time), 7-day/30-day retention, average streak length, lab completion rate, external-resource additions per active user, AI tutor engagement, (later) self-reported job placement / interview success.

---

## 16. Immediate Next Steps (Actionable)

1. Set up Postgres + Flask-Migrate on top of current repo.
2. Design and seed `SkillArea` + `Topic` + `TopicPrerequisite` (start with 8-10 areas, 40-60 topics — this is the single highest-leverage content task).
3. Write ~150 assessment questions (mix MCQ + a few scenario/short-answer) tagged to those skill areas.
4. Build `roadmap_engine.py` v0 (non-adaptive, rule-based ordering) — get a working end-to-end flow (assessment → roadmap → dashboard) before investing in the adaptive/AI layers.
5. Curate Tier-1 labs (free TryHackMe rooms, PortSwigger Academy labs, OverTheWire wargames) for the first 3-4 topics so the roadmap has real, usable content from day one.
6. Then layer in scheduling (§5.8), external library (§5.7), gamification (§5.11), and AI tutor (§5.10) in that order.
