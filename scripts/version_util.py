"Shared utility to parse version, create necessary files for builds"

import os
import re


def ffi_generator(v_tuple, version, flags=0x0):
    v_str = ", ".join(str(p) for p in v_tuple)
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
        StringStruct(u'FileDescription', u'Dota2-Minify'),
        StringStruct(u'FileVersion', u'{version}'),
        StringStruct(u'InternalName', u'Minify'),
        StringStruct(u'LegalCopyright', u'Copyright (c) Egezenn'),
        StringStruct(u'OriginalFilename', u'Minify.exe'),
        StringStruct(u'ProductName', u'Minify'),
        StringStruct(u'ProductVersion', u'{version}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""


def generate_metadata():
    try:
        # Source path relative to this script
        base_py_path = os.path.join(os.path.dirname(__file__), "..", "Minify", "core", "base.py")
        if not os.path.exists(base_py_path):
            # Fallback for different working directories
            base_py_path = os.path.join("Minify", "core", "base.py")

        with open(base_py_path, "r") as f:
            content = f.read()
            match = re.search(r'^VERSION = ["\'](.*)["\']', content, re.M)
            version = match.group(1) if match else "1.0"
    except Exception as e:
        print(f"Error reading version: {e}")
        version = "1.0"

    print(f"Generating metadata for version: {version}")

    # Prune RC for numeric version parts (e.g. 1.13rc7 -> 1.13.0.0, 1.13.1rc7 -> 1.13.1.0)
    clean_v = re.sub(r"rc.*", "", version)
    parts = clean_v.split(".")
    v_list = [0, 0, 0, 0]
    for i in range(min(len(parts), 4)):
        try:
            v_list[i] = int(re.sub(r"\D", "", parts[i])) if parts[i] else 0
        except ValueError:
            v_list[i] = 0

    # Save PyInstaller FFI file
    flags = 0x0
    if "rc" in version:
        flags = 0x2

    content_main = ffi_generator(v_list, version, flags)
    with open("ffi_main.txt", "w", encoding="utf-8") as f:
        f.write(content_main)

    # Save Inno Setup version file
    v_dotted = ".".join(str(p) for p in v_list)
    with open("version_info.iss", "w", encoding="utf-8") as f:
        f.write(f'#define AppVersion "{version}"\n')
        f.write(f'#define NumericVersion "{v_dotted}"\n')

    print(f"Numeric version: {v_dotted}")


if __name__ == "__main__":
    generate_metadata()
