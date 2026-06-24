# -*- mode: python ; coding: utf-8 -*-


import os

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[('ffmpeg.exe', '.')] if os.path.isfile('ffmpeg.exe') else [],
    datas=[],
    hiddenimports=[
        'yt_dlp',
        'yt_dlp.extractor',
        'yt_dlp.postprocessor',
        'yt_dlp.postprocessor.ffmpeg',
        'requests',
        'urllib3',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
    ],
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
    a.binaries,
    a.datas,
    [],
    name='MusicDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['app.ico'],
)
