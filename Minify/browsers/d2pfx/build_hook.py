import os
import shutil
import vpk
import dearpygui.dearpygui as dpg
from core import base, config, fs, log, vpk_utils
from ui import terminal
import helper
from . import config as browser_config


def run(mod_list, current_mod=None):
    # Shared storage for identified mods
    pfx_high_priority = {}  # mod_name: [vpk_paths]
    pfx_normal = {}  # mod_name: [vpk_paths]
    map_vpk_paths = []

    # List of all active VPK-based mods (for pak65 metadata)
    all_active_vpk_mods = []

    for mod_name in mod_list:
        # Check if mod is active
        if not (current_mod is not None or dpg.get_value(mod_name)):
            continue

        mod_path = os.path.join(base.mods_dir, mod_name)
        if not os.path.isdir(mod_path):
            continue

        # 1. Identify Standard VPK mods (for pak65 metadata reconstruction)
        if mod_name.endswith(".vpk"):
            all_active_vpk_mods.append(mod_name)
            continue

        # 2. Identify D2PFX mods via modcfg.json
        cfg_path = os.path.join(mod_path, "modcfg.json")
        if not os.path.exists(cfg_path):
            continue

        cfg = config.read_json_file(cfg_path)
        browser_info = cfg.get("browser", {})

        is_d2pfx = browser_info.get("browser") == "d2pfx" or str(browser_info.get("name", "")).startswith("d2pfx")

        if not is_d2pfx:
            continue

        # It's a D2PFX mod - find all VPKs once
        vpk_files = []
        for root, _, files in os.walk(mod_path):
            for f in files:
                if f.endswith(".vpk"):
                    vpk_files.append(os.path.join(root, f))

        if not vpk_files:
            continue

        cat = browser_info.get("category")
        if cat == "terrains":
            map_vpk_paths.extend(vpk_files)
        elif cat in browser_config.RENAME_CATEGORIES:
            pfx_high_priority[mod_name] = vpk_files
        else:
            pfx_normal[mod_name] = vpk_files
            all_active_vpk_mods.append(mod_name)

    # --- BUILD EXECUTION ---

    # 1. Maps (dota.vpk)
    if map_vpk_paths:
        terminal.add_text("&merging_vpks")
        maps_output_dir = os.path.join(helper.output_path, "maps")
        fs.create_dirs(maps_output_dir)
        # Just copy the last found map VPK
        shutil.copy2(map_vpk_paths[-1], os.path.join(maps_output_dir, "dota.vpk"))
    else:
        dota_vpk_path = os.path.join(helper.output_path, "maps", "dota.vpk")
        if os.path.exists(dota_vpk_path):
            fs.remove_path(dota_vpk_path)

    # 2. Normal Priority (pak65)
    if pfx_normal:
        terminal.add_text("&merging_vpks")
        fs.remove_path(base.merge_dir)
        fs.create_dirs(base.merge_dir)

        pak65_path = os.path.join(helper.output_path, "pak65_dir.vpk")
        # Extract existing pak65 (from build.py) to merge D2PFX on top
        if os.path.exists(pak65_path):
            try:
                vpk_utils.dump_vpk(vpk.open(pak65_path), base.merge_dir)
            except Exception:
                pass

        for mod_name, vpk_paths in pfx_normal.items():
            for path in vpk_paths:
                try:
                    vpk_utils.dump_vpk(vpk.open(path), base.merge_dir, check_exists=True)
                    terminal.add_text("&merged_mod", mod_name)
                except Exception:
                    log.write_warning("&failed_merge_mod", mod_name)

        vpk_utils.dump_metadata(base.merge_dir, vpk_mods=all_active_vpk_mods)
        vpk.new(base.merge_dir).save(pak65_path)
        fs.remove_path(base.merge_dir)

    # 3. High Priority (pak67)
    if pfx_high_priority:
        terminal.add_text("&merging_vpks")
        fs.remove_path(base.merge_dir)
        fs.create_dirs(base.merge_dir)

        for mod_name, vpk_paths in pfx_high_priority.items():
            for path in vpk_paths:
                try:
                    vpk_utils.dump_vpk(vpk.open(path), base.merge_dir, check_exists=True)
                    terminal.add_text("&merged_mod", mod_name)
                except Exception:
                    log.write_warning("&failed_merge_mod", mod_name)

        vpk_utils.dump_metadata(base.merge_dir, extra_lists={"minify_d2pfx_mods.txt": list(pfx_high_priority.keys())})
        vpk.new(base.merge_dir).save(os.path.join(helper.output_path, "pak67_dir.vpk"))
        fs.remove_path(base.merge_dir)
    else:
        pak67_path = os.path.join(helper.output_path, "pak67_dir.vpk")
        if os.path.exists(pak67_path):
            fs.remove_path(pak67_path)
