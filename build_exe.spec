# build_exe.spec
# PyInstaller spec for SkillSprint Academy — Purple Team Personal Academy
#
# This MUST be run on Windows (windows-latest GitHub Actions runner, or a real
# Windows/Windows VM) — PyInstaller does not cross-compile.
#
# Output mode: onedir (a folder, not a single .exe file). This is deliberate —
# the auto-update system replaces this entire folder wholesale on every update,
# which only works cleanly with onedir. Do NOT switch this to --onefile.
#
# Build with:
#   pyinstaller build_exe.spec
#
# Output appears at: dist/SkillSprintAcademy/

import os
import sys
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Get the directory containing this spec file
# In PyInstaller spec context, __file__ is not available, use sys.argv[0] or cwd
SPEC_DIR = os.path.dirname(os.path.abspath(sys.argv[0])) if '__file__' not in globals() else os.path.dirname(os.path.abspath(__file__))
# Fallback to current working directory
if not SPEC_DIR or SPEC_DIR == os.path.dirname(os.path.abspath(sys.executable)):
    SPEC_DIR = os.getcwd()

# Non-Python assets that must be bundled alongside the code.
# Format: (source_path_relative_to_this_spec_file, destination_folder_in_bundle)
# Directories are copied recursively, preserving their internal structure.
project_datas = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('bundles', 'bundles'),
    ('migrations', 'migrations'),
    ('VERSION', '.'),
    ('seed.py', '.'),
    ('seed_comprehensive.py', '.'),
    ('seed_resources.py', '.'),
    ('config.py', '.'),
    ('models.py', '.'),
    ('extensions.py', '.'),
    ('paths.py', '.'),
    ('updater.py', '.'),
    ('version_info.txt', '.'),
    ('requirements.txt', '.'),
    ('.env', '.'),
]

# Only include files/folders that actually exist, so a missing optional
# folder doesn't break the build.
project_datas = [(src, dst) for src, dst in project_datas if os.path.exists(os.path.join(SPEC_DIR, src))]

# Flask registers blueprints dynamically (imported inside create_app()),
# so PyInstaller's static import scanner can miss them entirely — the build
# would succeed but every route would 404 at runtime. List every blueprint
# module explicitly here (only those that EXIST in the codebase).
blueprint_hidden_imports = [
    'blueprints.roadmap.routes',
    'blueprints.dashboard.routes',
    'blueprints.labs.routes',
    'blueprints.purple_team.routes',
    'blueprints.offline.routes',
    'blueprints.job_roles.routes',
    'blueprints.library.routes',
    'blueprints.assistant.routes',
    'blueprints.assessment.routes',
    'blueprints.settings.routes',
]

# SQLAlchemy/Flask-Migrate/APScheduler/Markdown also sometimes need a nudge —
# these are common misses for this exact stack.
misc_hidden_imports = [
    'sqlalchemy.sql.default_comparator',
    'flask_migrate',
    'alembic',
    'apscheduler.triggers.cron',
    'apscheduler.triggers.interval',
    'apscheduler.executors.pool',
    'apscheduler.jobstores.sqlalchemy',
    'markdown',
    'markdown.extensions.fenced_code',
    'markdown.extensions.tables',
    'markdown.extensions.codehilite',
    'waitress',
    'jinja2',
    'jinja2.ext',
    'sqlite3',
    'werkzeug.security',
    'cryptography.fernet',
    'cryptography.hazmat.primitives',
    'cryptography.hazmat.primitives.kdf.pbkdf2',
    'email_validator',
]

all_hidden_imports = blueprint_hidden_imports + misc_hidden_imports

a = Analysis(
    ['app.py'],
    pathex=[SPEC_DIR],
    binaries=[],
    datas=project_datas,
    hiddenimports=all_hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',   # not used — excluding trims build size if pulled in
        'tkinter',      # incidentally by some other dependency
        'test', 'pytest', 'unittest',
        'notebook', 'jupyter', 'IPython',
        'webview',      # pywebview NOT used — exclude to save 50MB
        'oracledb',     # unused Oracle driver
        'razorpay',     # unused payment gateway
        'flask_dance',  # unused OAuth
        'oauthlib',     # unused OAuth
        'flask_mail',   # unused SMTP
        'dnspython',    # only if DNS tools used in labs
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SkillSprintAcademy',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # windowed app — no black console window behind it
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='static/img/skill_logo.ico' if os.path.exists('static/img/skill_logo.ico') else None,
    version='version_info.txt',   # see companion file below; remove this line if skipping it
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SkillSprintAcademy',
)

# Final output: dist/SkillSprintAcademy/  (this whole folder is what your
# GitHub Actions workflow zips and what the auto-updater swaps in place —
# nothing outside this folder, like your data\ directory, is ever touched.)