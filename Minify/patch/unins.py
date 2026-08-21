import os
import re
import time

import helper
from core import constants, fs, output, registry, steam

from patch import vpk_utils


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
                    pak_path = os.path.join(path, item)
                    if os.path.isfile(pak_path) and re.fullmatch(pak_pattern, item):
                        if vpk_utils.is_minify_pak(pak_path):
                            # TODO if this exists, pull & parse to enable uninstallers
                            # depends on opt-out not being true
                            fs.remove_path(pak_path)

        steam.remove_minify_lang()
        steam.restore_boot_language()

        for browser_config in registry.get_browser_configs():
            if hasattr(browser_config, "on_uninstall"):
                browser_config.on_uninstall()

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
