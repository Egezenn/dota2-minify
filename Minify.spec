# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['imgui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('bin/FiraMono-Medium.ttf', 'bin'),
        ('bin/localization.json', 'bin'),
        ('bin/blank-files/*', 'bin/blank-files'),
        ('bin/images/*', 'bin/images'),
        ('bin/sounds/*', 'bin/sounds'),
        ('mods/*', 'mods'),
        ('version', '.'),
    ],
    hiddenimports=['tkinter'],
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
    name='Minify',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
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
    name='Minify',
)
app = BUNDLE(
    coll,
    name='Minify.app',
    icon=None,
    bundle_identifier=None,
)
