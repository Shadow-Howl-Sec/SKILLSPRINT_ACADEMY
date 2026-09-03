# -*- mode: python ; coding: utf-8 -*-

import os
import sys

block_cipher = None

added_files = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('bundles', 'bundles'),
]

a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'sqlalchemy.ext.baked',
        'flask_sqlalchemy',
        'flask_migrate',
        'flask_talisman',
        'flask_wtf',
        'wtforms',
        'markdown',
        'markdown.extensions.fenced_code',
        'markdown.extensions.tables',
        'markdown.extensions.codehilite',
        'jinja2',
        'sqlite3',
        'blueprints.roadmap.routes',
        'blueprints.dashboard.routes',
        'blueprints.labs.routes',
        'blueprints.purple_team.routes',
        'blueprints.offline.routes',
        'blueprints.job_roles.routes',
        'blueprints.library.routes',
        'blueprints.assistant.routes',
        'blueprints.assessment.routes',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ZeroCipher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    icon='static/img/skill_logo.ico' if os.path.exists('static/img/skill_logo.ico') else None,
)
