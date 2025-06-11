# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['scripts\\executable_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('gui/*', 'gui'),
        ('bin/tesseract/tesseract.zip', 'bin/tesseract'),
    ],
    hiddenimports=['multiprocessing', 'pytesseract', 'webview', 'tesseract-ocr'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Scan-Checker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Scan-Checker',
)
