# -*- mode: python ; coding: utf-8 -*-
import os
from glob import glob

datas = []

# Include everything in /bin, including tessdata and tesseract.exe
datas.append(('bin\\tesseract.exe', 'bin'))
datas += [(file, 'bin\\tessdata') for file in glob('bin\\tessdata\\*.traineddata')]

# Include everything from /gui and /scripts
datas += [(os.path.join(root, file), os.path.relpath(root, ".")) 
          for root, _, files in os.walk('gui') for file in files]
datas += [(os.path.join(root, file), os.path.relpath(root, ".")) 
          for root, _, files in os.walk('scripts') for file in files]

# Include requirements.txt (if needed at runtime)
datas.append(('requirements.txt', '.'))

a = Analysis(
    ['scripts\\gui.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['fitz', 'PyMuPDF'],
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
    name='gui',
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
    name='gui',
)
