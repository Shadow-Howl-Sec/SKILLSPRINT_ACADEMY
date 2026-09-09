SkillSprintAcademy - Offline Cybersecurity Learning Platform
=============================================================

Single-user, fully offline cybersecurity training application.
Runs on Windows 10/11 with no internet required after first run.

QUICK START:
1. Double-click SkillSprintAcademy.exe
   OR
2. Double-click Start-SkillSprintAcademy.bat

The launcher installs the signed-update helper to
%LOCALAPPDATA%\SkillSprintAcademy before starting the app.

The app will start a local web server at http://127.0.0.1:5000
and open it in your default browser.

FIRST RUN:
- Creates instance/ folder for SQLite database and config
- Seeds the 2-stage purple team curriculum (Stage 1: Months 1-3, Stage 2: Ongoing)
- Sets up default user: operator

FEATURES:
- Two-stage Purple Team roadmap (Job-Ready + Mastery)
- 10 Job Role tracks (Purple Team Specialist is default)
- ~68 Topics with prerequisite DAG
- ~70 offline vm_exercise labs (attack + detection per topic)
- 7 Interactive in-browser exercises (Python, regex, cipher, etc.)
- AI Tutor (Ollama local LLM or rules-based fallback)
- XP, Streaks, Skill Radar progress tracking
- ATT&CK Matrix coverage map
- Purple Team exercise log & Markdown portfolio export

LAB SETUP:
Run scripts/setup_kali_vm.ps1 to provision a local Kali VM for hands-on labs.
Bundled challenge files are in bundles/labs/

AI TUTOR:
Install Ollama locally: scripts/setup_ollama.ps1
Configure model at /offline/settings/ai-tutor

REQUIREMENTS:
- Windows 10/11 (64-bit)
- ~500 MB disk space for app + bundles
- 8 GB+ RAM recommended (for Ollama AI tutor)

SUPPORT:
Check /offline/about for offline mode details.
Check /offline/lab-setup for Kali VM setup guide.

