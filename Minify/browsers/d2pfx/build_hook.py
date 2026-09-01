import os
import shutil

import helper
import vpk
from core import base, constants, fs, log, mods_shared, output
from patch import manifest_utils, vpk_utils

from browsers.d2pfx import config as browser_config


def run(mod_list, current_mod=None):
    # Shared storage for identified mods
    pfx_high_priority = {}  # mod_name: [vpk_paths]
    pfx_normal = {}  # mod_name: [vpk_paths]
    map_vpk_paths = []
    cursor_mod_paths = []

    # List of all active VPK-based mods (for pak65 metadata)
    all_active_vpk_mods = []

    for mod_name in mod_list:
        # Check if mod is active
        if not (current_mod is not None or mods_shared.get_state(mod_name)):
            continue

        mod_path = os.path.join(base.mods_dir, mod_name)
        if not os.path.isdir(mod_path):
            continue

        # 1. Identify Standard VPK mods (for pak65 metadata reconstruction)
        if mod_name.endswith(".vpk"):
            all_active_vpk_mods.append(mod_name)
            continue

        # 2. Identify D2PFX mods via manifest/modcfg
        cfg = manifest_utils.get_mod(mod_path)
        if not cfg:
            continue

        browser_info = cfg.get("browser", {})

        is_d2pfx = browser_info.get("browser") == "d2pfx" or str(browser_info.get("name", "")).startswith("d2pfx")

        if not is_d2pfx:
            continue

        cat = browser_info.get("category")

        # Cursors are directories containing cursor image/resource files
        if cat == "cursors":
            cursor_mod_paths.append(mod_path)
            continue

        # Find VPKs for VPK-based D2PFX mods
        vpk_files = []
        for root, _, files in os.walk(mod_path):
            for f in files:
                if f.endswith(".vpk"):
                    vpk_files.append(os.path.join(root, f))

        if not vpk_files:
            continue

        if cat == "terrains":
            if os.path.isdir(os.path.join(mod_path, "maps")):
                map_vpk_paths.extend(vpk_files)
            else:
                pfx_normal[mod_name] = vpk_files
                all_active_vpk_mods.append(mod_name)
        elif cat in browser_config.RENAME_CATEGORIES:
            pfx_high_priority[mod_name] = vpk_files
        else:
            pfx_normal[mod_name] = vpk_files
            all_active_vpk_mods.append(mod_name)

    # --- BUILD EXECUTION ---

    # 1. Maps (dota.vpk)
    if map_vpk_paths:
        output.add_text("&merging_vpks")
        maps_output_dir = os.path.join(helper.output_path, "maps")
        fs.create_dirs(maps_output_dir)
        fs.remove_path(base.merge_dir)
        fs.create_dirs(base.merge_dir)

        # Dump the last found map VPK (highest priority)
        try:
            vpk_utils.dump(vpk.open(map_vpk_paths[-1]), base.merge_dir)
        except Exception:
            log.write_warning("&failed_merge_mod", os.path.basename(map_vpk_paths[-1]))

        vpk_utils.dump_metadata(base.merge_dir)
        vpk.new(base.merge_dir).save(os.path.join(maps_output_dir, "dota.vpk"))
        fs.remove_path(base.merge_dir)
    else:
        dota_vpk_path = os.path.join(helper.output_path, "maps", "dota.vpk")
        if os.path.exists(dota_vpk_path):
            if vpk_utils.is_minify_pak(dota_vpk_path):
                fs.remove_path(dota_vpk_path)
                maps_output_dir = os.path.join(helper.output_path, "maps")
                if os.path.isdir(maps_output_dir) and not os.listdir(maps_output_dir):
                    fs.remove_path(maps_output_dir)

    # 2. Cursors
    if cursor_mod_paths:
        game_root = os.path.dirname(os.path.dirname(constants.dota_game_pak_path))
        minify_root = os.path.dirname(os.path.abspath(base.mods_dir))
        cursor_bkup_dir = os.path.join(minify_root, "backup", "d2pfx_cursors")
        dota_cursor_dir = os.path.join(game_root, "dota", "resource", "cursor")

        output.add_text("&installing_terminal", "D2PFX Cursors")

        for mod_path in cursor_mod_paths:
            cursor_source_dir = None
            for root, dirs, _ in os.walk(mod_path):
                for d in dirs:
                    if d.lower() == "cursor":
                        cursor_source_dir = os.path.join(root, d)
                        break
                if cursor_source_dir:
                    break

            if not cursor_source_dir:
                cursor_source_dir = mod_path

            for root, _, files in os.walk(cursor_source_dir):
                for fname in files:
                    ext = os.path.splitext(fname)[1].lower()
                    if ext in (".ani", ".bmp", ".cur", ".res", ".png", ".jpg", ".jpeg"):
                        src_file = os.path.join(root, fname)
                        dest_file = os.path.join(dota_cursor_dir, fname)
                        bkup_file = os.path.join(cursor_bkup_dir, "dota", "resource", "cursor", fname)

                        if os.path.isfile(dest_file) and not os.path.exists(bkup_file):
                            fs.create_dirs(os.path.dirname(bkup_file))
                            shutil.copy2(dest_file, bkup_file)

                        fs.create_dirs(os.path.dirname(dest_file))
                        shutil.copy2(src_file, dest_file)
    else:
        restore_d2pfx_cursors()

    # 3. Normal Priority (pak65)
    if pfx_normal:
        output.add_text("&merging_vpks")
        fs.remove_path(base.merge_dir)
        fs.create_dirs(base.merge_dir)

        pak65_path = os.path.join(helper.output_path, "pak65_dir.vpk")
        # Extract existing pak65 (from build.py) to merge D2PFX on top
        if os.path.exists(pak65_path):
            try:
                vpk_utils.dump(vpk.open(pak65_path), base.merge_dir)
            except Exception:
                pass

        for mod_name, vpk_paths in pfx_normal.items():
            for path in vpk_paths:
                try:
                    vpk_utils.dump(vpk.open(path), base.merge_dir, check_exists=True)
                    output.add_text("&merged_mod", mod_name)
                except Exception:
                    log.write_warning("&failed_merge_mod", mod_name)

        vpk_utils.dump_metadata(base.merge_dir, vpk_mods=all_active_vpk_mods)
        vpk.new(base.merge_dir).save(pak65_path)
        fs.remove_path(base.merge_dir)

    # 4. High Priority (pak67)
    if pfx_high_priority:
        output.add_text("&merging_vpks")
        fs.remove_path(base.merge_dir)
        fs.create_dirs(base.merge_dir)

        for mod_name, vpk_paths in pfx_high_priority.items():
            for path in vpk_paths:
                try:
                    vpk_utils.dump(vpk.open(path), base.merge_dir, check_exists=True)
                    output.add_text("&merged_mod", mod_name)
                except Exception:
                    log.write_warning("&failed_merge_mod", mod_name)

        vpk_utils.dump_metadata(base.merge_dir, extra_lists={"minify_d2pfx_mods.txt": list(pfx_high_priority.keys())})
        vpk.new(base.merge_dir).save(os.path.join(helper.output_path, "pak67_dir.vpk"))
        fs.remove_path(base.merge_dir)
    else:
        pak67_path = os.path.join(helper.output_path, "pak67_dir.vpk")
        if os.path.exists(pak67_path):
            fs.remove_path(pak67_path)


def restore_d2pfx_cursors():
    minify_root = os.path.dirname(os.path.abspath(base.mods_dir))
    cursor_bkup_dir = os.path.join(minify_root, "backup", "d2pfx_cursors")
    if os.path.isdir(cursor_bkup_dir):
        game_root = os.path.dirname(os.path.dirname(constants.dota_game_pak_path))
        restored = 0
        for dirpath, _, filenames in os.walk(cursor_bkup_dir):
            for fname in filenames:
                bkup_file = os.path.join(dirpath, fname)
                rel_path = os.path.relpath(bkup_file, cursor_bkup_dir).replace("\\", "/")
                dest_file = os.path.join(game_root, rel_path)
                fs.create_dirs(os.path.dirname(dest_file))
                shutil.copy2(bkup_file, dest_file)
                restored += 1
        fs.remove_path(cursor_bkup_dir)
        if restored > 0:
            output.add_text(f"Restored {restored} original cursor files.", msg_type="success")
