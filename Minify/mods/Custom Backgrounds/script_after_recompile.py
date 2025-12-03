import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
if os.getcwd() != minify_root:
    os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

import mpaths
import helper


def main():
    img_available = False

    for file in sorted(os.listdir(current_dir)):
        if file.endswith((".png", ".jpg", ".jpeg", ".webp")):
            img_available = True
            break

    if helper.workshop_installed and img_available:
        helper.remove_path(
            os.path.join(
                mpaths.minify_dota_compile_output_path,
                "panorama",
                "images",
                "backgrounds",
                "imgref.vxml_c",
            )
        )
