import os
import shutil

import helper
import vpk
from core import base, constants, fs, log, mods_shared, output, utils
from patch import manifest_utils, vpk_utils

from . import __main__ as plugin_main


def scan_d2pfx_mods(mod_list):
    pfx_high_priority = {}  # mod_name: [vpk_paths]
    pfx_normal = {}  # mod_name: [vpk_paths]
    map_vpk_paths = []
    cursor_mod_paths = []
    standalone_vpk_paths = []

    for mod_name in mod_list:
        if not mods_shared.get_state(mod_name):
            continue

        mod_path = os.path.join(base.mods_dir, mod_name)
        if not os.path.isdir(mod_path):
            continue

        cfg = manifest_utils.get_mod(mod_path)
        if not cfg or cfg.get("browser") != "d2pfx":
            continue

        cat = cfg.get("category")
        if cat == "cursors":
            cursor_mod_paths.append(mod_path)
            continue

        vpk_files = []
        for root, _, files in os.walk(mod_path):
            for f in files:
                if f.endswith(".vpk"):
                    vpk_files.append(os.path.join(root, f))

        if not vpk_files:
            continue

        # Prevent pak66_dir.vpk from overflowing 2GB (signed 32-bit offset causes Dota crash: Failed to read 16 bytes)
        remaining_vpks = []
        for vpk_file in vpk_files:
            fname = os.path.basename(vpk_file).lower()
            fsize = os.path.getsize(vpk_file)
            if fname.startswith("pak") and fname.endswith("_dir.vpk") and fname != "pak66_dir.vpk" and fsize > 100 * 1024 * 1024:
                standalone_vpk_paths.append((mod_name, vpk_file))
            else:
                remaining_vpks.append(vpk_file)

        if not remaining_vpks:
            continue

        if cat == "terrains":
            if os.path.isdir(os.path.join(mod_path, "maps")):
                map_vpk_paths.extend(remaining_vpks)
            else:
                pfx_normal[mod_name] = remaining_vpks
        elif cat in plugin_main.RENAME_CATEGORIES:
            pfx_high_priority[mod_name] = remaining_vpks
        else:
            pfx_normal[mod_name] = remaining_vpks

    return pfx_normal, pfx_high_priority, map_vpk_paths, cursor_mod_paths, standalone_vpk_paths


def run_pre_build(mod_list):
    pfx_normal, _, map_vpk_paths, cursor_mod_paths, standalone_vpk_paths = scan_d2pfx_mods(mod_list)

    # Standalone large VPKs (e.g. Warcraft III voices) copied directly to prevent 2GB overflow
    for mod_name, vpk_path in standalone_vpk_paths:
        dest_file = os.path.join(helper.output_path, os.path.basename(vpk_path))
        try:
            if not os.path.exists(dest_file) or os.path.getsize(dest_file) != os.path.getsize(vpk_path):
                shutil.copy2(vpk_path, dest_file)
            output.add_text("&merged_mod", mod_name, indent=True)
        except Exception:
            log.write_warning("&failed_merge_mod", mod_name)

    # 1. Maps (dota.vpk)
    if map_vpk_paths:
        output.add_text("&merging_vpks")
        maps_output_dir = os.path.join(helper.output_path, "maps")
        fs.create_dirs(maps_output_dir)
        fs.remove_path(base.merge_dir)
        fs.create_dirs(base.merge_dir)

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

    # 3. Normal Priority VPKs (Base Layer)
    if pfx_normal:
        output.add_text("&merging_vpks")
        for mod_name, vpk_paths in pfx_normal.items():
            for path in vpk_paths:
                try:
                    vpk_utils.dump(
                        vpk.open(path),
                        constants.minify_dota_compile_output_path,
                        check_exists=True,
                    )
                    output.add_text("&merged_mod", mod_name, indent=True)
                except Exception:
                    log.write_warning("&failed_merge_mod", mod_name)


def run_post_build(mod_list):
    _, pfx_high_priority, _, _, _ = scan_d2pfx_mods(mod_list)

    # High Priority VPKs (Override Layer)
    if pfx_high_priority:
        output.add_text("&merging_vpks")
        for mod_name, vpk_paths in pfx_high_priority.items():
            for path in vpk_paths:
                try:
                    vpk_utils.dump(
                        vpk.open(path),
                        constants.minify_dota_compile_output_path,
                        check_exists=False,
                    )
                    output.add_text("&merged_mod", mod_name, indent=True)
                except Exception:
                    log.write_warning("&failed_merge_mod", mod_name)


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
            output.add_text(f"Restored {restored} original cursor files.", msg_type="success", indent=True)
