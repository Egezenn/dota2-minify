from datetime import datetime
import glob
import os
import shutil
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

import mpaths

import requests


def main():
    path_from_config, config_data = mpaths.get_key_from_json_file_w_default(
        config_path := os.path.join(current_dir, "config.json"), "steam_path", ""
    )
    possible_userdata_paths = [
        os.path.join(path_from_config, "userdata"),
        os.path.join(mpaths.steam_dir, "userdata"),
        os.path.join(mpaths.STEAM_DEFAULT_INSTALLATION_PATH, "userdata"),
    ]
    found = False
    for userdata_path in possible_userdata_paths:
        if os.path.exists(userdata_path):
            found = True
            break

    if found:
        if grid_path := (glob.glob(os.path.join(current_dir, "dota2protracker_hero_grid*.json"))):
            grid_path = grid_path[0]
            replace_grid = True
        else:
            grid_type = mpaths.get_key_from_dict_w_default(config_data, "grid_type", "d2ptrating")
            patch_name = mpaths.get_key_from_dict_w_default(config_data, "patch", "7.39e")  # to be fixed later
            response = requests.get(
                f"https://dota2protracker.com/meta-hero-grids/download?mode={grid_type}&patch={patch_name}"
            )
            if response.status_code == 200:
                if os.path.exists(grid_path := os.path.join(current_dir, "grid.json")):
                    os.remove(grid_path)
                with open(grid_path, "wb") as file:
                    file.write(response.content)
                replace_grid = True
            else:
                mpaths.write_warning("Couldn't fetch a grid from D2PT.")
                replace_grid = False

        if replace_grid:
            found_id = False
            if steam_id := mpaths.get_key_from_dict_w_default(config_data, "steam_id", ""):
                id_to_use_path = os.path.join(userdata_path, str(steam_id))
                found_id = True
            elif steam_ids := sorted(os.listdir(userdata_path)):
                id_to_use_path = os.path.join(userdata_path, steam_ids[0])
                found_id = True

            mpaths.set_key_for_json_file(config_path, "steam_path", os.path.dirname(userdata_path))
            mpaths.set_key_for_json_file(config_path, "steam_id", os.path.basename(id_to_use_path))
            mpaths.set_key_for_json_file(config_path, "grid_type", grid_type)
            mpaths.set_key_for_json_file(config_path, "patch_name", patch_name)

            if found_id and os.path.isdir(dest_path := os.path.join(id_to_use_path, "570", "remote", "cfg")):
                formatted_time = datetime.fromtimestamp(
                    os.path.getmtime(original_grid_path := os.path.join(dest_path, "hero_grid_config.json"))
                ).strftime("%Y-%m-%d_%H%M")
                if not os.path.exists(backup_dir := os.path.join(current_dir, "backup")):
                    os.mkdir(backup_dir)
                # TODO detect grids from D2PT to not backup them?
                # user could be using a merged one though
                os.rename(
                    original_grid_path,
                    os.path.join(backup_dir, f"{formatted_time}.json"),
                )
                shutil.copy(grid_path, os.path.join(dest_path, "hero_grid_config.json"))
    else:
        mpaths.write_warning(
            "Path to your steam installation couldn't be found for D2PT Hero Grids, manually set it from `config.json` with the key `steam_path`"
        )


if __name__ == "__main__":
    main()


# TODO Implement uninstaller instructions
