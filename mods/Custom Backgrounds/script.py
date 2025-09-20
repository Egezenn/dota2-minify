import os
import shutil
import subprocess
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
if minify_root not in sys.path:
    sys.path.insert(0, minify_root)


import helper
import mpaths


img_available = False


for file in sorted(os.listdir(current_dir)):
    if file.endswith((".png", ".jpg", ".jpeg", ".webp")):
        img_available = True
        break


def main():
    if helper.workshop_installed:
        global img_available
        if img_available:
            filepath = os.path.join(current_dir, file)

            xml_template = r"""<root>
    <Panel class="AddonLoadingRoot">
        <Image src="file://{images}/backgrounds/background.png" />
    </Panel>
</root>
"""
            if not filepath.endswith(".png"):
                if (magick_path := shutil.which("magick")) is not None:
                    subprocess.call(f"{magick_path} {filepath} background.png", shell=True)
                    filepath = "background.png"
            else:
                helper.add_text_to_terminal(
                    warning := f"imagemagick is not available on path, unable to convert {file}"
                )
                helper.warnings.append(warning)

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
