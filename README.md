# SkillSprint Academy

SkillSprint Academy is an offline-first Flask learning platform for cybersecurity. It combines adaptive skill assessment, a Purple Team curriculum, practical labs, learning resources, an AI tutor, and progress tracking in a local web application.

## What It Includes

- CAT-style assessments across 20 skill areas, with questions ranging from foundations to advanced detection and offensive security.
- A Purple Team default track covering networking, systems, web security, Active Directory, forensics, malware, cloud, containers, and detection engineering.
- Topic prerequisites, personalized roadmaps, job-role tracks, capstone projects, and weekly curriculum planning.
- Offline labs from `bundles/labs/` and external lab links for online use.
- Interactive exercises for Python, JavaScript, regular expressions, ciphers, PCAPs, and binary inspection.
- A local AI tutor using Ollama when available, with a deterministic rules-based fallback.
- XP, streaks, skill profiles, dashboards, resource caching, and update checks.

The application defaults to offline mode and binds to `127.0.0.1:52837`.

## Requirements

- Windows, Linux, or macOS for development.
- Python 3.11 or newer. The current Windows build has been verified with Python 3.14.
- Dependencies from `requirements.txt`.
- Optional: Ollama for local AI tutoring.
- Optional: VirtualBox/Kali for the VM-based lab environment.

## Quick Start

From the repository root:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py app.py
```

Open <http://127.0.0.1:52837>.

On first startup the application creates the database tables and the local default user. The database is stored in the configured SQLite location and is ignored by Git.

## Seed the Curriculum

The seed scripts are idempotent and can be rerun. The recommended complete seed is:

```powershell
py seed_comprehensive.py
```

`seed_comprehensive.py` includes:

- Skill areas, topics, prerequisites, job roles, capstones, and curriculum weeks.
- Content items and offline VM labs for topics.
- Topic checkpoint questions.
- Skill-area CAT questions and Tier-1 external labs from `seed.py`.
- Open-source security resources from `seed_top_open_source.py`.
- Curated video search links and soft-skill questions.

For a smaller baseline seed, use:

```powershell
py seed.py
```

The open-source resource layer can also be run independently after the base topics exist:

```powershell
py seed_top_open_source.py
```

`seed_purple_team_curriculum.py` is a separate, more detailed Phase 2 curriculum seed. Review its destructive/reset behavior before running it on an existing database.

## Configuration

Configuration is loaded from environment variables and optional `.env` values. Important settings include:

| Variable | Default | Purpose |
| --- | --- | --- |
| `OFFLINE_MODE` | `True` | Disable external services and external resource fetching. |
| `OFFLINE_BIND_HOST` | `127.0.0.1` | Local server bind address. |
| `OFFLINE_BIND_PORT` | `52837` | Local server port. |
| `DATABASE_URL` | SQLite | SQLAlchemy database URL. |
| `AI_TUTOR_PROVIDER` | `auto` | `auto`, `ollama`, `anthropic`, or `rules`. |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama server URL. |
| `OLLAMA_MODEL` | `llama3.1:8b-instruct` | Ollama model name. |
| `ASSESSMENT_QUESTIONS_PER_AREA` | `5` | Questions selected per skill area. |
| `ASSESSMENT_START_DIFFICULTY` | `3` | Initial CAT difficulty from 1 to 5. |
| `SECRET_KEY` | Development default | Flask session signing key. Set a private value outside development. |

Offline mode keeps the core application local. External lab links, cloud AI, SMTP, OAuth, and payment integrations require the corresponding online configuration.

## Main Routes

- `/` - application home and onboarding entry point
- `/assessment/` - adaptive skill assessment
- `/roadmap/` - personalized learning roadmap
- `/dashboard` - daily progress and activity
- `/labs/` - available labs and bundled exercises
- `/library/` - saved learning resources
- `/assistant` - AI tutor
- `/job-roles/` - job-role tracks and capstones
- `/offline/` - offline status, lab setup, resource cache, and tutor settings
- `/health` - application and database health check

## Run Tests and Checks

Run the complete test suite:

```powershell
py -m unittest discover -s tests
```

Compile every Python file without creating bytecode caches:

```powershell
py -W error::SyntaxWarning -c "import pathlib; files=list(pathlib.Path('.').rglob('*.py')); [compile(p.read_text(encoding='utf-8'), str(p), 'exec') for p in files]; print(f'Checked {len(files)} Python files')"
```

Generated caches can be removed safely because they are ignored by Git:

```powershell
Get-ChildItem -Recurse -Force -Directory |
  Where-Object { $_.Name -in @('__pycache__','.pytest_cache') } |
  Remove-Item -Recurse -Force
```

## Build the Windows Application

The repository uses PyInstaller in **onedir** mode. The output is a folder containing the executable and its runtime files, not a single self-contained EXE.

```powershell
.\scripts\build_exe.ps1
```

The script:

1. Removes previous `build/`, `dist/`, and `release/` outputs.
2. Builds from `build_exe.spec`.
3. Copies the onedir application to `release/SkillSprintAcademy/`.
4. Copies bundles and helper scripts.
5. Creates `release/Start-SkillSprintAcademy.bat` and `release/README.txt`.

Run the packaged application with:

```powershell
.\release\Start-SkillSprintAcademy.bat
```

Or launch the executable directly:

```powershell
.\release\SkillSprintAcademy\SkillSprintAcademy.exe
```

The EXE creates its writable database and configuration data on first run. Do not delete the `_internal` directory beside the executable.

## Repository Layout

```text
app.py                         Flask application entry point
config.py                      Environment-backed configuration
models.py                      SQLAlchemy models
extensions.py                  Flask extension setup
seed.py                        Baseline taxonomy, CAT questions, and labs
seed_comprehensive.py          Complete curriculum seed entry point
seed_top_open_source.py        Open-source resource seed layer
seed_all_videos_and_quizzes.py Video search links and soft-skill questions
seed_purple_team_curriculum.py Detailed Phase 2 curriculum seed
services/                      Roadmap, tutor, scheduler, XP, and update services
blueprints/                    Feature route modules
templates/                     Jinja templates
static/                        CSS, JavaScript, images, fonts, and vendor assets
bundles/labs/                  Offline lab artifacts
migrations/                    Alembic migration files
tests/                         Automated tests
scripts/build_exe.ps1          Windows PyInstaller build script
build_exe.spec                 PyInstaller onedir specification
release/                       Generated Windows distribution output
```

## Security and Data Notes

- Keep `SECRET_KEY`, API keys, OAuth credentials, and mail credentials out of source control.
- Use only authorized systems for labs and external assessments.
- Offline lab artifacts are served read-only with path traversal protections.
- The default development credentials and SQLite database are intended for local development only.

## License

No license file is currently included. Add an explicit license before distributing the project publicly.