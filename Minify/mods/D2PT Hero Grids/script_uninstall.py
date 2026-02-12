import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
mod_name = os.path.basename(current_dir)
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

import mpaths


def main():
    steam_id_config = mpaths.get_config("steam_id", "")
    userdata_path = os.path.join(mpaths.steam_root, "userdata")
    found = False

    if steam_id_config and os.path.exists(userdata_path):
        id_to_use_path = os.path.join(userdata_path, str(steam_id_config))
        dest_path = os.path.join(id_to_use_path, mpaths.STEAM_DOTA_ID, "remote", "cfg")
        if os.path.exists(dest_path):
            found = True

    if found:
        original_grid_path = os.path.join(dest_path, "hero_grid_config.json")

        # Read existing config
        current_config = mpaths.read_json_file(original_grid_path)

        # Check if configs exists
        if "configs" in current_config:
            initial_count = len(current_config["configs"])

            # Filter out D2PT configs
            current_config["configs"] = [
                cfg
                for cfg in current_config["configs"]
                if not cfg.get("config_name", "").startswith("Dota2ProTracker ")
            ]

            final_count = len(current_config["configs"])
            removed_count = initial_count - final_count

            if removed_count > 0:
                mpaths.write_json_file(original_grid_path, current_config)
            else:
                mpaths.write_warning("No Dota2ProTracker hero grids found to remove.")
        else:
            mpaths.write_warning("Config file missing 'configs' key.")

    else:
        mpaths.write_warning(
            f"A valid user ID or path to your steam installation couldn't be found for {mod_name}, manually set it from `minify_config.json` under `modconf` > `{mod_name}` key with `steam_path`"
        )


if __name__ == "__main__":
    main()
