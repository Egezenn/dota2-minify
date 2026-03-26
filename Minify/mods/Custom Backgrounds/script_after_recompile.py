import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
if os.getcwd() != minify_root:
    os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

# isort: split

import conditions
from core import base, constants, fs


def main():
    img_available = False

    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        if os.path.exists(os.path.join(base.config_dir, f"background{ext}")):
            img_available = True
            break

    if conditions.workshop_installed and img_available:
        fs.remove_path(
            os.path.join(
                constants.minify_dota_compile_output_path,
                "panorama",
                "images",
                "backgrounds",
                "imgref.vxml_c",
            )
        )
