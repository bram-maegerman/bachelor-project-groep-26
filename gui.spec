# gui.spec

# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

a = Analysis(
    ['scripts/gui.py'],          # jouw hoofdscript
    pathex=[],               # root folder van je project
    binaries=[
        ('bin/tesseract.exe', 'bin'),  # tesseract exe meegeven
    ],
    datas=[
        ('scripts/config.json', '.'),          # bestaand config.json
        ('gui/assets/img', 'gui/assets/img'),
        ('gui/*.html', 'gui'),                  # alle html bestanden in gui/
        ('gui/style/*.css', 'gui/style'),       # alle css in gui/style/
        ('gui/js/*.js', 'gui/js'),                       # alle js bestanden in js/
        ('scripts/*.py', 'scripts')
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='scan-checker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='scan-checker'
)
