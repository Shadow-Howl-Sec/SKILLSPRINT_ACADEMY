SkillSprint Academy - Offline Cybersecurity Learning Platform
=============================================================

Single-user, fully offline cybersecurity training application.
Runs on Windows 10/11 with no internet required after first run.

QUICK START:
1. Double-click SkillSprintAcademy.exe
   OR
2. Double-click Start-SkillSprint.bat

The app will start a local web server at http://127.0.0.1:5000
and open it in your default browser.

FIRST RUN:
- Creates instance/ folder for SQLite database and config
- Seeds the cybersecurity curriculum (Tiers 0-4)
- Sets up default user: Shubham

FEATURES:
- 5-tier curriculum (Foundations to Capstone)
- 9 Job Role tracks (SOC Analyst, Penetration Tester, etc.)
- 62 Topics with prerequisite DAG
- 37 Offline Labs (PCAP, log analysis, crypto, malware, etc.)
- 7 Interactive in-browser exercises (Python, regex, cipher, etc.)
- AI Tutor (Ollama local LLM or rules-based fallback)
- XP, Streaks, Skill Radar progress tracking

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

