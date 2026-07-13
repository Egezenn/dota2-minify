import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
if os.getcwd() != minify_root:
    os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

# isort: split

from core import fs, steam

dota_fonts_path = os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota", "panorama", "fonts")
bkup_path = os.path.join(minify_root, "backup", "Custom Fonts")


def main():
    fs.restore_directory(dota_fonts_path, bkup_path)


if __name__ == "__main__":
    main()
