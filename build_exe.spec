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
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# ---------------------------------------------------------------------------
# pywebview on Windows uses the WebView2/edgechromium backend, which pulls in
# some dynamic imports PyInstaller's static analysis can miss on its own.
# collect_all() grabs its submodules, data files, and binaries automatically.
# ---------------------------------------------------------------------------
webview_datas, webview_binaries, webview_hidden = collect_all('webview')

# ---------------------------------------------------------------------------
# Non-Python assets that must be bundled alongside the code.
# Format: (source_path_relative_to_this_spec_file, destination_folder_in_bundle)
# Directories are copied recursively, preserving their internal structure.
# ---------------------------------------------------------------------------
project_datas = [
    ('app/templates', 'app/templates'),
    ('app/static', 'app/static'),
    ('content', 'content'),
    ('migrations', 'migrations'),
    ('VERSION', '.'),
]

# Only include files/folders that actually exist, so a missing optional
# folder (e.g. you haven't created migrations/ yet) doesn't break the build.
project_datas = [(src, dst) for src, dst in project_datas if os.path.exists(src)]

# ---------------------------------------------------------------------------
# Flask registers blueprints dynamically (imported inside create_app()),
# so PyInstaller's static import scanner can miss them entirely — the build
# would succeed but every route would 404 at runtime. List every blueprint
# module explicitly here.
# ---------------------------------------------------------------------------
blueprint_hidden_imports = [
    'app.blueprints.onboarding',
    'app.blueprints.onboarding.routes',
    'app.blueprints.assessment',
    'app.blueprints.assessment.routes',
    'app.blueprints.roadmap',
    'app.blueprints.roadmap.routes',
    'app.blueprints.dashboard',
    'app.blueprints.dashboard.routes',
    'app.blueprints.labs',
    'app.blueprints.labs.routes',
    'app.blueprints.library',
    'app.blueprints.library.routes',
    'app.blueprints.progress',
    'app.blueprints.progress.routes',
    'app.blueprints.settings',
    'app.blueprints.settings.routes',
    'app.blueprints.purple_team',
    'app.blueprints.purple_team.routes',
]

# SQLAlchemy/Flask-Migrate/APScheduler also sometimes need a nudge —
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
    'waitress',
]

all_hidden_imports = blueprint_hidden_imports + misc_hidden_imports + webview_hidden

a = Analysis(
    ['desktop_launcher.py'],
    pathex=[],
    binaries=webview_binaries,
    datas=project_datas + webview_datas,
    hiddenimports=all_hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',   # not used — excluding trims build size if pulled in
        'tkinter',      # incidentally by some other dependency
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
    icon='app_icon.ico',    # place an .ico file at the repo root, or remove this line
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
