import os
import re
import time

import helper
import vpk
from core import constants, fs, output, steam


def uninstall(sender=None, app_data=None, user_data=None):
    from ui import gui

    with gui.interactive_lock():
        output.clean()
        time.sleep(0.05)

        # smart uninstall
        pak_pattern = r"^pak\d{2}_dir\.vpk$"
        for path in constants.minify_dota_possible_language_output_paths:
            if os.path.isdir(path):
                maps_vpk_path = os.path.join(path, "maps", "dota.vpk")
                if os.path.exists(maps_vpk_path):
                    fs.remove_path(os.path.join(path, "maps"))

                for item in os.listdir(path):
                    if os.path.isfile(os.path.join(path, item)) and re.fullmatch(pak_pattern, item):
                        pak_contents = vpk.open(os.path.join(path, item))
                        mod_names_with_txt = [s + ".txt" for s in constants.visually_available_mods]
                        for file in [
                            "minify_mods.json",
                            # TODO if this exists, pull & parse to enable uninstallers
                            "minify_vpk_mods.txt",
                            "minify_version.txt",
                            *mod_names_with_txt,
                        ]:
                            if file in pak_contents:
                                fs.remove_path(os.path.join(path, item))
                                break

        steam.remove_minify_lang()

        helper.bulk_exec_script("uninstall")
        output.add_text("&mods_removed_terminal")


def wipe():
    from ui import gui

    with gui.interactive_lock():
        output.clean()
        uninstall()
        for path in constants.minify_dota_possible_language_output_paths:
            if os.path.isdir(path):
                fs.remove_path(path)
                output.add_text("&clean_lang_dirs", path)
