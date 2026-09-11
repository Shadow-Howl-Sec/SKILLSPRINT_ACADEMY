# SkillSprint Academy

SkillSprint Academy is a local-first cybersecurity learning platform for building practical Purple Team skills. It combines adaptive assessments, guided roadmaps, job-role tracks, offline labs, interactive exercises, resource tracking, progress analytics, and an optional local AI tutor.

The application runs as a local Flask server and, when launched from the packaged Windows build, opens in a native desktop webview. It defaults to offline mode and listens on `http://127.0.0.1:52837`.

## Features

- Adaptive CAT-style assessments across foundational, defensive, and offensive security skills.
- A two-stage Purple Team curriculum covering networking, systems, web security, Active Directory, forensics, malware, cloud, containers, and detection engineering.
- Prerequisites, personalized roadmaps, weekly plans, capstones, and job-role tracks.
- Bundled offline labs under `bundles/labs/` plus links to external labs.
- Browser exercises for Python, JavaScript, regular expressions, ciphers, PCAPs, and binary inspection.
- Ollama-backed AI tutoring when available, with a deterministic rules-based fallback.
- XP, streaks, skill profiles, dashboards, cached resources, ATT&CK coverage, and update checks.

## Windows Quick Start

### Packaged release

The verified build is an onedir distribution. Keep the entire `release/SkillSprintAcademy/` folder together; the executable depends on its adjacent `_internal` directory and bundled assets.

```powershell
.\release\Start-SkillSprintAcademy.bat
```

You can also start the executable directly:

```powershell
.\release\SkillSprintAcademy\SkillSprintAcademy.exe
```

The launcher starts the local server and the desktop window. On first run, the application creates its database and initializes reference data. Do not delete `_internal` or move the EXE out of its folder.

### Installer

If the build finds Inno Setup's `ISCC.exe`, it also creates `release\SkillSprintAcademy-Setup.exe`. Run that file for a per-user installation with a Start Menu shortcut and an optional desktop shortcut. The installer does not require administrator privileges.

The installer is optional. Without Inno Setup, the portable `release/` folder is still complete and runnable.

## Build the Windows Release

Build on Windows from the repository root. PyInstaller cannot cross-compile Windows executables.

Requirements:

- Python 3.11 or newer. Python 3.14 is supported by the current build.
- Project dependencies from `requirements.txt`.
- PyInstaller. The build script installs it automatically when missing.
- Optional: Inno Setup 6 for `SkillSprintAcademy-Setup.exe`.

```powershell
py -m pip install -r requirements.txt
.\scripts\build_exe.ps1
```

The script removes old `build/`, `dist/`, and `release/` folders, runs `build_exe.spec`, copies the executable and runtime files, includes labs and helper scripts, and writes a portable launcher and release README. The generated files are:

```text
release/
  SkillSprintAcademy/              PyInstaller onedir application
    SkillSprintAcademy.exe
    _internal/                     Runtime, templates, static assets, and dependencies
  bundles/                         Offline lab files
  scripts/                         VM and Ollama helper scripts
  Start-SkillSprintAcademy.bat     Portable launcher
  SkillSprintAcademy-Setup.exe     Optional Inno Setup installer
```

To create the installer, install Inno Setup 6, ensure `ISCC.exe` is on `PATH`, and rerun the build script. The installer reads the version from `VERSION`.

## Development Setup

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py app.py
```

Open `http://127.0.0.1:52837` in a browser. For development, SQLite defaults to `skillsprint.db` in the current working directory. The packaged application stores user data at `%LOCALAPPDATA%\SkillSprintAcademy\data`, which is separate from the application files and survives upgrades.

## Curriculum Data

The recommended complete seed is idempotent and can be rerun:

```powershell
py seed_comprehensive.py
```

It loads skill areas, topics, prerequisites, roles, capstones, curriculum weeks, content, offline labs, checkpoint questions, CAT questions, open-source resources, video links, and soft-skill questions. For a smaller baseline, run `py seed.py`. The separate `seed_purple_team_curriculum.py` script contains a more detailed Phase 2 curriculum; review its reset behavior before using it on an existing database.

## Configuration

Settings come from environment variables and optional `.env` values.

| Variable | Default | Purpose |
| --- | --- | --- |
| `OFFLINE_BIND_HOST` | `127.0.0.1` | Local server bind address. |
| `OFFLINE_BIND_PORT` | `52837` | Local server port. |
| `DATABASE_URL` | Local SQLite | SQLAlchemy database URL. |
| `AI_TUTOR_PROVIDER` | `auto` | `auto`, `ollama`, `anthropic`, or `rules`. |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama server URL. |
| `OLLAMA_MODEL` | `llama3.1:8b-instruct` | Ollama model name. |
| `SECRET_KEY` | Development value | Set a private value for non-development use. |
| `UPDATE_HMAC_SECRET` | Empty | Secret used when signed update verification is configured. |

The core application does not require internet access. Ollama, external lab links, cloud AI, VirtualBox/Kali labs, and other integrations are optional.

## Useful Routes

`/` home and onboarding; `/assessment/` adaptive assessment; `/roadmap/` roadmap; `/dashboard` progress; `/labs/` labs and exercises; `/library/` resources; `/assistant` tutor; `/job-roles/` role tracks; `/offline/` local settings and lab setup; `/health` application and database health.

## Tests and Checks

```powershell
py -m unittest discover -s tests
py -W error::SyntaxWarning -c "import pathlib; files=list(pathlib.Path('.').rglob('*.py')); [compile(p.read_text(encoding='utf-8'), str(p), 'exec') for p in files]; print(f'Checked {len(files)} Python files')"
```

## Repository Map

```text
app.py                         Flask entry point
config.py / paths.py           Configuration and persistent data paths
models.py / extensions.py      Database models and Flask extensions
blueprints/                    Feature route modules
services/                      Roadmap, tutor, scheduler, XP, and updates
templates/ and static/         UI templates and assets
bundles/labs/                  Offline lab artifacts
migrations/                    Alembic migrations
tests/                         Automated tests
scripts/build_exe.ps1          Windows release builder
build_exe.spec                 PyInstaller onedir specification
installer.iss                  Inno Setup installer definition
```

## Security and Data

- Keep secrets, API keys, credentials, and private VM configuration out of source control.
- Use labs and external assessments only on systems you own or are authorized to test.
- The application serves bundled lab artifacts with path traversal protections.
- The default local user and development `SECRET_KEY` are not suitable for a shared or public deployment.

## License

No license file is currently included. Add an explicit license before distributing the project publicly.