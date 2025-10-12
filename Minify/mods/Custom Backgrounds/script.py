import os
import shutil
import subprocess
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
if os.getcwd() != minify_root:
    os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

import helper
import mpaths


def main():
    img_available, vid_available = False, False

    for file in sorted(os.listdir(current_dir)):
        if file.endswith((".png", ".jpg", ".jpeg", ".webp")):
            img_available = True
            break
        elif file.endswith((".mp4", ".webm")):
            vid_available = True
            file_ext = os.path.splitext(file)[1]
            break

    if helper.workshop_installed and (img_available or vid_available):
        filepath = os.path.join(current_dir, file)
        if img_available:

            # reference to the file to compile to vtex
            xml_template = r"""<root>
    <Panel class="AddonLoadingRoot">
        <Image src="file://{images}/backgrounds/background.png" />
    </Panel>
</root>
"""
            if not filepath.endswith(".png"):
                if (magick_path := shutil.which("magick")) is not None:
                    subprocess.run([magick_path, filepath, filepath := os.path.join(current_dir, "background.png")])
                else:
                    helper.add_text_to_terminal(f"imagemagick is not available on path, unable to convert {file}")

            if filepath.endswith(".png"):
                os.makedirs(
                    compile_location := os.path.join(
                        mpaths.minify_dota_compile_input_path, "panorama", "images", "backgrounds"
                    ),
                    exist_ok=True,
                )

                shutil.copy(filepath, os.path.join(compile_location, "background.png"))

                with open(os.path.join(compile_location, "imgref.xml"), "w") as xml:
                    xml.write(xml_template)

        elif vid_available:
            # TODO implement panorama side of things
            os.makedirs(
                compile_location := os.path.join(mpaths.minify_dota_compile_output_path, "panorama", "videos"),
                exist_ok=True,
            )
            shutil.copy(filepath, os.path.join(compile_location, "background" + file_ext))
