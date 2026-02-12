import glob
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
mod_name = os.path.basename(current_dir)
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

import mpaths

import jsonc
import requests


def main():
    steam_id_config = mpaths.get_config("steam_id", "")

    config_data = mpaths.get_mod_config(mod_name)
    grid_type = mpaths.get_config__dict(config_data, "grid_type", "d2ptrating")
    config_data["grid_type"] = grid_type
    mpaths.set_mod_config(mod_name, config_data)

    userdata_path = os.path.join(mpaths.steam_root, "userdata")
    found = False
    replace_grid = False

    if steam_id_config and os.path.exists(userdata_path):
        id_to_use_path = os.path.join(userdata_path, str(steam_id_config))
        dest_path = os.path.join(id_to_use_path, mpaths.STEAM_DOTA_ID, "remote", "cfg")
        if os.path.exists(dest_path):
            found = True

    if found:
        if grid_path := (glob.glob(os.path.join(current_dir, "dota2protracker_hero_grid*.json"))):
            grid_path = grid_path[0]
            replace_grid = True
            with open(grid_path, encoding="utf-8") as f:
                new_grid_data = jsonc.load(f)
        else:
            response = requests.get(
                f"https://dota2protracker.com/meta-hero-grids/download?mode={grid_type}&patch=latest"
            )
            if response.status_code == 200:
                grid_path = os.path.join(current_dir, "grid.json")
                if "application/json" in response.headers.get("Content-Type", ""):
                    new_grid_data = response.json()
                    replace_grid = True
                else:
                    # Fallback if content type isn't explicitly json but content is
                    try:
                        new_grid_data = response.json()
                        replace_grid = True
                    except:
                        mpaths.write_warning(f"Failed to parse JSON from {grid_path}.")
            else:
                mpaths.write_warning(f"Couldn't fetch a grid from {current_dir}.")

        if replace_grid:
            original_grid_path = os.path.join(dest_path, "hero_grid_config.json")

            # Read existing config
            current_config = mpaths.read_json_file(original_grid_path)

            # Initialize if empty or missing structure
            if "configs" not in current_config:
                current_config["configs"] = []
            if "version" not in current_config:
                current_config["version"] = 3

            # Filter out old D2PT configs
            current_config["configs"] = [
                cfg
                for cfg in current_config["configs"]
                if not cfg.get("config_name", "").startswith("Dota2ProTracker ")
            ]

            # Append new configs
            if "configs" in new_grid_data:
                current_config["configs"].extend(new_grid_data["configs"])

                # Write back the updated config
                mpaths.write_json_file(original_grid_path, current_config)
            else:
                mpaths.write_warning("Downloaded grid data missing 'configs' key.")
    else:
        mpaths.write_warning(
            f"A valid user ID or path to your steam installation couldn't be found for {mod_name}, manually set it from `minify_config.json` under `modconf` > `{mod_name}` key with `steam_path`"
        )


if __name__ == "__main__":
    main()
