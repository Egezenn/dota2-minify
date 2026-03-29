import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
mod_name = os.path.basename(current_dir)
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

# isort: split

import requests

# isort: split

from core import base, config, log, steam

IMPORT_SUFFIX = " #Minify-Import"
REMOTE_URL = "https://github.com/Egezenn/dota2-precompiled-grids/releases/latest/download/hero_grid_config.json"


def main():
    steam_id_config = config.get("steam_id", "")

    userdata_path = os.path.join(steam.ROOT, "userdata")
    found = False
    new_grid_data = None

    if steam_id_config and os.path.exists(userdata_path):
        id_to_use_path = os.path.join(userdata_path, str(steam_id_config))
        dest_path = os.path.join(id_to_use_path, base.STEAM_DOTA_ID, "remote", "cfg")
        if os.path.exists(dest_path):
            found = True

    if not found:
        log.write_warning(
            f"A valid user ID or path to your steam installation couldn't be found for {mod_name}, manually set it from `minify_config.json` under `modconf` > `{mod_name}` key with `steam_path`"
        )
        return

    # Check for local config first
    local_config_path = os.path.join(current_dir, "config", "hero_grid_config.json")
    if os.path.exists(local_config_path):
        new_grid_data = config.read_json_file(local_config_path)
    else:
        # Fetch from remote
        try:
            response = requests.get(REMOTE_URL, timeout=10)
            if response.status_code == 200:
                new_grid_data = response.json()
            else:
                log.write_warning(f"Couldn't fetch grids from {REMOTE_URL}. Status: {response.status_code}")
        except Exception as e:
            log.write_warning(f"Failed to fetch remote grids: {e}")

    if new_grid_data and "configs" in new_grid_data:
        original_grid_path = os.path.join(dest_path, "hero_grid_config.json")

        # Read existing config
        current_config = config.read_json_file(original_grid_path)

        # Initialize if empty or missing structure
        if "configs" not in current_config:
            current_config["configs"] = []
        if "version" not in current_config:
            current_config["version"] = 3

        # Filter out old Minify-Imported configs
        current_config["configs"] = [
            cfg for cfg in current_config["configs"] if not cfg.get("config_name", "").endswith(IMPORT_SUFFIX)
        ]

        # Prepare new configs with suffix
        for cfg in new_grid_data["configs"]:
            if not cfg.get("config_name", "").endswith(IMPORT_SUFFIX):
                cfg["config_name"] += IMPORT_SUFFIX

        # Append new configs
        current_config["configs"].extend(new_grid_data["configs"])

        # Write back the updated config
        config.write_json_file(original_grid_path, current_config)
    else:
        log.write_warning("No grid data found to import.")


if __name__ == "__main__":
    main()
