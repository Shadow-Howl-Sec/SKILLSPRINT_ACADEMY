SkillSprintAcademy - Offline Cybersecurity Learning Platform
=============================================================

Single-user, fully offline cybersecurity training application.
Runs on Windows 10/11 with no internet required after first run.

QUICK START:
1. Double-click SkillSprintAcademy.exe
   OR
2. Double-click Start-SkillSprintAcademy.bat

The app opens a native desktop window backed by its local web server.
Signed updates are downloaded, verified, and staged by the application.

INSTALLER:
- Run SkillSprintAcademy-Setup.exe to register the app in Windows Installed apps.
- The installer creates Start Menu and optional desktop shortcuts.

FIRST RUN:
- Creates %LOCALAPPDATA%\SkillSprintAcademy\data for the SQLite database
- Seeds the available reference curriculum when the database is empty
- Sets up the default local user: Shubham

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

DATA AND SUPPORT:
- User data is retained at %LOCALAPPDATA%\SkillSprintAcademy\data.
- Check /offline/ for offline mode details and lab setup.

