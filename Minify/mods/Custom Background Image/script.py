import os
import shutil
import subprocess
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
mod_name = os.path.basename(current_dir)
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
if os.getcwd() != minify_root:
    os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

# isort: split

import conditions
import helper
from core import base, config, constants, fs, output


def main():
    source_file = None
    img_extensions = (".png", ".jpg", ".jpeg", ".webp")

    for ext in img_extensions:
        p = os.path.join(base.config_dir, f"background{ext}")
        if os.path.exists(p):
            actual_ext = fs.get_file_type(p)
            if actual_ext == ".jpeg":
                actual_ext = ".jpg"

            if not actual_ext:
                output.add_text("Unsupported background image format\n   {}", p, msg_type="error", indent=True)
                return

            if actual_ext != ext:
                new_p = os.path.join(base.config_dir, f"background{actual_ext}")
                output.add_text("Background extension mismatch\n   {} -> {}", p, new_p, msg_type="warning", indent=True)
                fs.move_path(p, new_p)
                return

            source_file = p
            break

    if not source_file:
        return

    if conditions.workshop_installed:
        target_file = (
            os.path.join(base.config_dir, "_background.png") if not source_file.endswith(".png") else source_file
        )
        if target_file != source_file:
            if (magick_path := shutil.which("magick")) is not None:
                subprocess.run(
                    [magick_path, source_file, target_file],
                    creationflags=subprocess.CREATE_NO_WINDOW if base.is_win else 0,
                )
            else:
                output.add_text(
                    "Conversion tools missing\n   {} ({})",
                    "ImageMagick",
                    f"{actual_ext} -> .png",
                    msg_type="error",
                    indent=True,
                )
                return

        if target_file.endswith(".png") and os.path.exists(target_file):
            xml_template = helper.create_img_ref_xml(["panorama/images/backgrounds/background.png"])
            fs.create_dirs(
                compile_location := os.path.join(
                    constants.minify_dota_compile_input_path, "panorama", "images", "backgrounds"
                )
            )

            shutil.copy(target_file, os.path.join(compile_location, "background.png"))

            with open(os.path.join(compile_location, "imgref.xml"), "w") as xml:
                xml.write(xml_template)

            config.set_mod(
                mod_name,
                {
                    "bg_img_style": 'url("s2r://panorama/images/backgrounds/background_png.vtex"), url("s2r://panorama/images/loadingscreens/international_2026_ls_5/loadingscreen.vtex")'
                },
            )
