import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

import shutil

import requests

import helper
import mpaths


def main():
    zip_path = os.path.join(current_dir, "files", "OpenDotaGuides.zip")
    temp_dump_path = os.path.join(current_dir, "files", "temp")
    if os.path.exists(zip_path):
        os.remove(zip_path)

    response = requests.get(mpaths.odg_latest)
    if response.status_code == 200:
        with open(zip_path, "wb") as file:
            file.write(response.content)
        os.makedirs(os.path.join(mpaths.dota_itembuilds_path, "bkup"), exist_ok=True)
        for name in os.listdir(mpaths.dota_itembuilds_path):
            try:
                if name != "bkup":
                    os.rename(
                        os.path.join(mpaths.dota_itembuilds_path, name),
                        os.path.join(mpaths.dota_itembuilds_path, "bkup", name),
                    )
            except FileExistsError:
                pass  # backup was created and opendotaguides was replacing the guides already
        shutil.unpack_archive(zip_path, temp_dump_path, format="zip")
        for file in os.listdir(temp_dump_path):
            shutil.copy(
                os.path.join(temp_dump_path, file),
                os.path.join(mpaths.dota_itembuilds_path, file),
            )
        helper.remove_path(temp_dump_path)
        os.remove(zip_path)
        if os.path.exists(zip_path):
            os.remove(zip_path)


if __name__ == "__main__":
    main()
