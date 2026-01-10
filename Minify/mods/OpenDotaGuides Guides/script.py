import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
if os.getcwd() != minify_root:
    os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

import shutil

import requests

import helper
import mpaths

dota_itembuilds_path = os.path.join(
    mpaths.steam_library, "steamapps", "common", "dota 2 beta", "game", "dota", "itembuilds"
)
odg_latest = "https://github.com/Egezenn/OpenDotaGuides/releases/latest/download/itembuilds.zip"
zip_path = os.path.join(current_dir, "files", "OpenDotaGuides.zip")
temp_dump_path = os.path.join(current_dir, "files", "temp")


def main():
    try:
        if helper.workshop_installed:
            shutil.copy(
                os.path.join(current_dir, "_styling.txt"),
                os.path.join(current_dir, "styling.txt"),
            )
    except:
        pass

    helper.remove_path(zip_path)

    response = requests.get(odg_latest)
    if response.status_code == 200:
        with open(zip_path, "wb") as file:
            file.write(response.content)
        os.makedirs(os.path.join(dota_itembuilds_path, "bkup"), exist_ok=True)
        try:
            for name in os.listdir(dota_itembuilds_path):
                if name != "bkup":
                    helper.move_path(
                        os.path.join(dota_itembuilds_path, name),
                        os.path.join(dota_itembuilds_path, "bkup", name),
                    )
        except FileExistsError:
            pass  # backup was created and opendotaguides was replacing the guides already
        shutil.unpack_archive(zip_path, temp_dump_path, format="zip")
        for file in os.listdir(temp_dump_path):
            shutil.copy(
                os.path.join(temp_dump_path, file),
                os.path.join(dota_itembuilds_path, file),
            )
        helper.remove_path(temp_dump_path, zip_path)


if __name__ == "__main__":
    main()
