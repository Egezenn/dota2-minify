# -*- mode: python ; coding: utf-8 -*-
import os
import platform
import re
import sys


def ffi_generator(v_str, version, type, flags=0x0):
    return f"""# UTF-8
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({v_str}),
    prodvers=({v_str}),
    mask=0x3f,
    flags={hex(flags)},
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Egezenn'),
        StringStruct(u'FileDescription', u'{"Dota2-Minify" if type == "main" else "Dota2-Minify Updater"}'),
        StringStruct(u'FileVersion', u'{version}'),
        StringStruct(u'InternalName', u'{"Minify" if type == "main" else "Minify-updater"}'),
        StringStruct(u'LegalCopyright', u'Copyright (c) Egezenn'),
        StringStruct(u'OriginalFilename', u'{"Minify.exe" if type == "main" else "updater.exe"}'),
        StringStruct(u'ProductName', u'{"Minify" if type == "main" else "Minify-updater"}'),
        StringStruct(u'ProductVersion', u'{version}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""


def generate_version_info(version):
    try:
        match = re.match(r"(\d+)\.(\d+)\.(\d+)(?:rc(\d+))?", version)
        if not match:
            parts = version.split(".")
            while len(parts) < 4:
                parts.append("0")
            v_tuple = tuple(int(p) for p in parts[:4])
        else:
            major, minor, patch, rc = match.groups()
            v_tuple = (int(major), int(minor), int(patch), int(rc) if rc else 0)
        v_str = ", ".join(str(p) for p in v_tuple)

        flags = 0x0
        if version == "0":
            flags = 0x1
        elif "rc" in version:
            flags = 0x2

        content_main = ffi_generator(v_str, version, "main", flags)
        content_updater = ffi_generator(v_str, version, "updater", flags)

        with open("ffi_main.txt", "w", encoding="utf-8") as f:
            f.write(content_main)
        with open("ffi_updater.txt", "w", encoding="utf-8") as f:
            f.write(content_updater)

    except Exception as e:
        print(f"Error generating version info: {e}")
        sys.exit(1)


if platform.system() == "Windows":
    try:
        with open(os.path.join(os.pardir, "version")) as f:
            version = f.read()
    except FileNotFoundError:
        version = "0"
    generate_version_info(version)

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

a_updater = Analysis(
    ["../Minify/updater.py"],
    pathex=["../Minify"],
)
pyz_updater = PYZ(a_updater.pure)

exe_updater = EXE(
    pyz_updater,
    a_updater.scripts,
    a_updater.binaries,
    a_updater.datas,
    [],
    name="updater",
    icon=["..\\Minify\\bin\\images\\favicon.ico"],
    version="ffi_updater.txt" if os.path.exists("ffi_updater.txt") else None,
)

coll = COLLECT(
    exe,
    exe_updater,
    a.binaries,
    a.datas,
    name="Minify",
)

try:
    os.remove("ffi_main.txt")
    os.remove("ffi_updater.txt")
except:
    pass
