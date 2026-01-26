from datetime import datetime
import glob
import os
import shutil
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
mod_name = os.path.basename(current_dir)
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

import helper
import mpaths

import requests


def main():
    config_data = mpaths.get_mod_config(mod_name)
    steam_id_config = mpaths.get_config("steam_id", "")
    grid_type = mpaths.get_config__dict(config_data, "grid_type", "d2ptrating")
    config_data["grid_type"] = grid_type
    mpaths.set_mod_config(mod_name, config_data)

    userdata_path = os.path.join(mpaths.steam_root, "userdata")
    found = False
    replace_grid = False

    if steam_id_config and os.path.exists(userdata_path):
        id_to_use_path = os.path.join(userdata_path, str(steam_id_config))
        dest_path = os.path.join(id_to_use_path, "570", "remote", "cfg")
        if os.path.exists(dest_path):
            found = True

    if found:
        if grid_path := (glob.glob(os.path.join(current_dir, "dota2protracker_hero_grid*.json"))):
            grid_path = grid_path[0]
            replace_grid = True
        else:
            response = requests.get(
                f"https://dota2protracker.com/meta-hero-grids/download?mode={grid_type}&patch=latest"
            )
            if response.status_code == 200:
                grid_path = os.path.join(current_dir, "grid.json")
                helper.remove_path(grid_path)
                with open(grid_path, "wb") as file:
                    file.write(response.content)
                replace_grid = True
            else:
                mpaths.write_warning(f"Couldn't fetch a grid from {current_dir}.")

        if replace_grid:
            original_grid_path = os.path.join(dest_path, "hero_grid_config.json")
            if not os.path.exists(backup_dir := os.path.join(current_dir, "backup")):
                os.mkdir(backup_dir)
            try:
                formatted_time = datetime.fromtimestamp(os.path.getmtime(original_grid_path)).strftime("%Y-%m-%d_%H%M")
                helper.move_path(
                    original_grid_path,
                    os.path.join(backup_dir, f"{formatted_time}.json"),
                )
            except FileNotFoundError:
                pass
            shutil.copy(grid_path, os.path.join(dest_path, "hero_grid_config.json"))
    else:
        mpaths.write_warning(
            f"A valid user ID or path to your steam installation couldn't be found for {mod_name}, manually set it from `minify_config.json` under `modconf` > `{mod_name}` key with `steam_path`"
        )


if __name__ == "__main__":
    main()

# TODO Do not replace as whole, merge with existing grids
# TODO Implement uninstaller instructions: simply remove kv's that D2PT adds
