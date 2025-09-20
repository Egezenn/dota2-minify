import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

import mpaths
import helper


def main():
    try:
        with open(os.path.join(mpaths.dota_itembuilds_path, "default_antimage.txt"), "r") as file:
            lines = file.readlines()
        if len(lines) >= 3:
            if "OpenDotaGuides" in lines[2]:
                for name in os.listdir(mpaths.dota_itembuilds_path):
                    if name != "bkup":
                        os.remove(os.path.join(mpaths.dota_itembuilds_path, name))
                for name in os.listdir(os.path.join(mpaths.dota_itembuilds_path, "bkup")):
                    os.rename(
                        os.path.join(mpaths.dota_itembuilds_path, "bkup", name),
                        os.path.join(mpaths.dota_itembuilds_path, name),
                    )
                helper.remove_path(os.path.join(mpaths.dota_itembuilds_path, "bkup"))
    except FileNotFoundError:
        helper.add_text_to_terminal(
            "Unable to recover backed up default guides or the itembuilds directory is empty, verify files to get the default guides back"
        )
        helper.warnings.append(
            "Unable to recover backed up default guides or the itembuilds directory is empty, verify files to get the default guides back"
        )


if __name__ == "__main__":
    main()
