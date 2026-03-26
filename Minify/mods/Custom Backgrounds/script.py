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
from core import base, config, constants, fs
from ui import terminal

mod_name = os.path.basename(current_dir)


def main():
    img_available, vid_available = False, False
    source_file = None

    # Potential extensions
    img_extensions = (".png", ".jpg", ".jpeg", ".webp")
    vid_extensions = (".mp4", ".webm")

    # Search for background.<ext> in config dir
    for ext in img_extensions + vid_extensions:
        p = os.path.join(base.config_dir, f"background{ext}")
        if os.path.exists(p):
            source_file = p
            if ext in img_extensions:
                img_available = True
            else:
                vid_available = True
            break

    if not source_file:
        return

    if conditions.workshop_installed:
        if img_available:
            # Handle conversion if not already .png
            target_file = (
                os.path.join(base.config_dir, "_background.png") if not source_file.endswith(".png") else source_file
            )
            if target_file != source_file:
                if (magick_path := shutil.which("magick")) is not None:
                    subprocess.run(
                        [magick_path, source_file, target_file],
                        creationflags=subprocess.CREATE_NO_WINDOW if base.OS == base.WIN else 0,
                    )
                else:
                    terminal.add_text(f"imagemagick is not available on path, unable to convert {source_file}")
                    return

            if target_file.endswith(".png"):
                # reference to the file to compile to vtex
                xml_template = helper.create_img_ref_xml(["panorama/images/backgrounds/background.png"])
                fs.create_dirs(
                    compile_location := os.path.join(
                        constants.minify_dota_compile_input_path, "panorama", "images", "backgrounds"
                    )
                )

                shutil.copy(target_file, os.path.join(compile_location, "background.png"))

                with open(os.path.join(compile_location, "imgref.xml"), "w") as xml:
                    xml.write(xml_template)

                # Use placeholder for background image style
                config.set_mod(
                    mod_name,
                    {
                        "bg_img_style": 'url("s2r://panorama/images/backgrounds/background_png.vtex"), url("s2r://panorama/images/loadingscreens/international_2025_ls_3/loadingscreen.vtex")'
                    },
                )

        elif vid_available:
            # Handle conversion if not already .webm
            target_file = (
                os.path.join(base.config_dir, "_background.webm") if not source_file.endswith(".webm") else source_file
            )
            if target_file != source_file:
                if (ffmpeg_path := shutil.which("ffmpeg")) is not None:
                    subprocess.run(
                        [
                            ffmpeg_path,
                            "-y",
                            "-i",
                            source_file,
                            "-c:v",
                            "libvpx-vp9",
                            "-deadline",
                            "realtime",
                            "-cpu-used",
                            "4",
                            "-threads",
                            "0",
                            target_file,
                        ],
                        creationflags=subprocess.CREATE_NO_WINDOW if base.OS == base.WIN else 0,
                    )
                else:
                    terminal.add_text(f"ffmpeg is not available on path, unable to convert {source_file}")
                    return

            if target_file.endswith(".webm"):
                fs.create_dirs(
                    compile_location := os.path.join(constants.minify_dota_compile_output_path, "panorama", "videos"),
                )
                shutil.copy(target_file, os.path.join(compile_location, "background.webm"))

                # Use placeholder to collapse background image when video is present
                config.set_mod(mod_name, {"bg_img_style": "none"})
