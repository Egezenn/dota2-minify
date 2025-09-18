import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
if minify_root not in sys.path:
    sys.path.insert(0, minify_root)


import mpaths


for file in sorted(os.listdir(current_dir)):
    if file.endswith((".png", ".jpg", ".jpeg", ".webm")):
        img_available = True
        break


def main():
    global img_available
    if img_available:
        os.remove(
            os.path.join(mpaths.minify_dota_compile_output_path, "panorama", "images", "backgrounds", "imgref.vxml_c")
        )
