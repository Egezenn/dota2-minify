import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
if os.getcwd() != minify_root:
    os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

# isort: split

from core import fs, log, steam

dota_itembuilds_path = os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota", "itembuilds")


def main():
    bkup_path = os.path.join(dota_itembuilds_path, "bkup")
    if not os.path.exists(bkup_path):
        return

    try:
        with open(os.path.join(dota_itembuilds_path, "default_antimage.txt")) as file:
            lines = file.readlines()
        if len(lines) >= 3:
            if "OpenDotaGuides" in lines[2]:
                for name in os.listdir(dota_itembuilds_path):
                    if name != "bkup":
                        fs.remove_path(os.path.join(dota_itembuilds_path, name))
                for name in os.listdir(bkup_path):
                    fs.move_path(
                        os.path.join(bkup_path, name),
                        os.path.join(dota_itembuilds_path, name),
                    )
                fs.remove_path(bkup_path)
    except FileNotFoundError:
        log.write_warning(
            "Unable to recover backed up default guides or the itembuilds directory is empty, verify files to get the default guides back"
        )


if __name__ == "__main__":
    main()
