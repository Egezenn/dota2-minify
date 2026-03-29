# -*- mode: python ; coding: utf-8 -*-
import os
import platform
import sys


# Import version utility to generate metadata files
sys.path.append(os.path.abspath(SPECPATH))
try:
    import version_util

    if platform.system() == "Windows":
        version_util.generate_metadata()
except ImportError:
    print("Warning: version_util not found, skipping metadata generation")
except Exception as e:
    print(f"Error generating metadata: {e}")

a = Analysis(
    ["../Minify/__main__.py"],
    pathex=["../Minify"],
    hiddenimports=["tkinter"],
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Minify",
    console=False,
    icon=["..\\Minify\\bin\\images\\favicon.ico"],
    version="ffi_main.txt" if os.path.exists("ffi_main.txt") else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="Minify",
)

try:
    os.remove("ffi_main.txt")
except:
    pass
