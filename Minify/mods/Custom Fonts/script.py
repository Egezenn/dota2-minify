import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
if os.getcwd() != minify_root:
    os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

# isort: split

import shutil
import struct
import uuid

from core import config, fs, output, steam
from ui.fonts import find_system_font

dota_fonts_path = os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota", "panorama", "fonts")
bkup_path = os.path.join(minify_root, "backup", "Custom Fonts")

REPLACE_MAP = {
    "radiance-black.otf": ("Radiance Black", "Radiance Black", "Radiance-Black"),
    "radiance-blackitalic.otf": ("Radiance Black", "Radiance Black Italic", "Radiance-BlackItalic"),
    "radiance-bold.otf": ("Radiance", "Radiance Bold", "Radiance-Bold"),
    "radiance-bolditalic.otf": ("Radiance", "Radiance Bold Italic", "Radiance-BoldItalic"),
    "radiance-light.otf": ("Radiance", "Radiance Light", "Radiance-Light"),
    "radiance-lightitalic.otf": ("Radiance", "Radiance Light Italic", "Radiance-LightItalic"),
    "radiance-regular.otf": ("Radiance", "Radiance Regular", "Radiance-Regular"),
    "radiance-regularitalic.otf": ("Radiance", "Radiance Regular Italic", "Radiance-RegularItalic"),
    "radiance-semibold.otf": ("Radiance Semibold", "Radiance Semibold", "Radiance-Semibold"),
    "radiance-semibolditalic.otf": ("Radiance Semibold", "Radiance Semibold Italic", "Radiance-SemiboldItalic"),
    "radiance-ultralight.otf": ("Radiance UltraLight", "Radiance UltraLight", "Radiance-UltraLight"),
    "radiance-ultralightitalic.otf": ("Radiance", "Radiance UltraLight Italic", "Radiance-UltraLightItalic"),
    "radiancem-black.otf": ("RadianceM Black", "RadianceM Black", "RadianceM-Black"),
    "radiancem-blackitalic.otf": ("RadianceM Black", "RadianceM Black Italic", "RadianceM-BlackItalic"),
    "radiancem-bold.otf": ("RadianceM", "RadianceM Bold", "RadianceM-Bold"),
    "radiancem-bolditalic.otf": ("RadianceM", "RadianceM Bold Italic", "RadianceM-BoldItalic"),
    "radiancem-italic.otf": ("RadianceM", "RadianceM Italic", "RadianceM-Italic"),
    "radiancem-light.otf": ("RadianceM", "RadianceM Light", "RadianceM-Light"),
    "radiancem-lightitalic.otf": ("RadianceM", "RadianceM Light Italic", "RadianceM-LightItalic"),
    "radiancem-regular.otf": ("RadianceM", "RadianceM Regular", "RadianceM-Regular"),
    "radiancem-regularitalic.otf": ("RadianceM", "RadianceM Regular Italic", "RadianceM-RegularItalic"),
    "radiancem-semibold.otf": ("RadianceM Semibold", "RadianceM Semibold", "RadianceM-Semibold"),
    "radiancem-semibolditalic.otf": ("RadianceM Semibold", "RadianceM Semibold Italic", "RadianceM-SemiboldItalic"),
    "radiancem-ultralight.otf": ("RadianceM UltraLight", "RadianceM UltraLight", "RadianceM-UltraLight"),
    "reaver-black.otf": ("Reaver Black", "Reaver Black", "Reaver-Black"),
    "reaver-bold.otf": ("Reaver", "Reaver Bold", "Reaver-Bold"),
    "reaver-light.otf": ("Reaver Light", "Reaver Light", "Reaver-Light"),
    "reaver-regular.otf": ("Reaver", "Reaver Regular", "Reaver-Regular"),
    "reaver-semibold.otf": ("Reaver SemiBold", "Reaver SemiBold", "Reaver-SemiBold"),
}

FONT_EXTENSIONS = (".otf", ".ttf")


def _patch_font(font_path, family, fullname, postscript):
    patches = {1: family, 4: fullname, 6: postscript}

    with open(font_path, "rb") as f:
        data = bytearray(f.read())

    num_tables = struct.unpack_from(">H", data, 4)[0]
    table_dir = 12
    name_offset = name_length = os2_offset = None

    for i in range(num_tables):
        entry = table_dir + i * 16
        tag = data[entry : entry + 4]
        if tag == b"name":
            name_offset = struct.unpack_from(">I", data, entry + 8)[0]
            name_length = struct.unpack_from(">I", data, entry + 12)[0]
        elif tag == b"OS/2":
            os2_offset = struct.unpack_from(">I", data, entry + 8)[0]

    if os2_offset is not None:
        struct.pack_into(">H", data, os2_offset + 8, 0)

    if name_offset is None:
        return

    count = struct.unpack_from(">H", data, name_offset + 2)[0]
    strings_base = name_offset + struct.unpack_from(">H", data, name_offset + 4)[0]
    rec_start = name_offset + 6

    records = []
    for i in range(count):
        r_start = rec_start + i * 12
        platformID, encID, langID, nameID, length, offset = struct.unpack_from(">6H", data, r_start)
        s = data[strings_base + offset : strings_base + offset + length]
        if nameID in patches and platformID == 3:
            s = patches[nameID].encode("utf-16-be")
        records.append((platformID, encID, langID, nameID, s))

    new_str_off = 6 + len(records) * 12
    str_buf = bytearray()
    rec_buf = bytearray()
    for plat, enc, lang, nid, s in records:
        rec_buf.extend(struct.pack(">6H", plat, enc, lang, nid, len(s), len(str_buf)))
        str_buf.extend(s)

    new_table = struct.pack(">HHH", 0, len(records), new_str_off) + rec_buf + str_buf
    pad = (4 - len(new_table) % 4) % 4
    new_table += b"\x00" * pad

    data[name_offset : name_offset + name_length] = new_table

    for i in range(num_tables):
        entry = table_dir + i * 16
        if struct.unpack_from(">I", data, entry + 8)[0] > name_offset:
            struct.pack_into(
                ">I", data, entry + 8, struct.unpack_from(">I", data, entry + 8)[0] + len(new_table) - name_length
            )

    with open(font_path, "wb") as f:
        f.write(data)


def main():
    mod_data = config.get_mod("Custom Fonts")

    found_font = None

    config_dir = os.path.join(minify_root, "config")
    for ext in FONT_EXTENSIONS:
        path = os.path.join(config_dir, f"font{ext}")
        if os.path.exists(path):
            found_font = path

    if not found_font:
        font_string = mod_data.get("font_string", "Calibri")
        if font_string.strip():
            for name in font_string.split(","):
                found_font = find_system_font(name.strip().strip("'\""))
                if found_font:
                    break

    if not found_font:
        output.add_text(
            "No font configured: set a font name in settings or place font.otf/ttf in config/", msg_type="error"
        )
        return

    fs.backup_directory(dota_fonts_path, bkup_path)

    for name, (family, fullname, postscript) in REPLACE_MAP.items():
        fs.remove_path(os.path.join(dota_fonts_path, name))
        dest = os.path.join(dota_fonts_path, name)
        shutil.copy2(found_font, dest)
        _patch_font(dest, family, fullname, postscript)
        output.add_text(f"Installed: {name}")

    with open(os.path.join(dota_fonts_path, ".uuid"), "w") as f:
        f.write(str(uuid.uuid4()))


if __name__ == "__main__":
    main()
