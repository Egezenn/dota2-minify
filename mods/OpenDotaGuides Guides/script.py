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


odg_latest = "https://github.com/Egezenn/OpenDotaGuides/releases/latest/download/itembuilds.zip"
zip_path = os.path.join(current_dir, "files", "OpenDotaGuides.zip")
temp_dump_path = os.path.join(current_dir, "files", "temp")


def main():
    if os.path.exists(zip_path):
        os.remove(zip_path)

    response = requests.get(odg_latest)
    if response.status_code == 200:
        with open(zip_path, "wb") as file:
            file.write(response.content)
        helper.add_text_to_terminal("   Downloaded latest OpenDotaGuides guides.", None, "success")
        os.makedirs(os.path.join(mpaths.dota_itembuilds_path, "bkup"), exist_ok=True)
        try:
            for name in os.listdir(mpaths.dota_itembuilds_path):
                if name != "bkup":
                    os.rename(
                        os.path.join(mpaths.dota_itembuilds_path, name),
                        os.path.join(mpaths.dota_itembuilds_path, "bkup", name),
                    )
            helper.add_text_to_terminal("   Replaced default guides with OpenDotaGuides.", None, "success")
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
