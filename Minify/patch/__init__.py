"The universe"

import os
import shutil
import subprocess
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor

import jsonc
import playsound3
import psutil
import vpk

# isort: split

import conditions
import helper
from core import base, config, constants, fs, log, mods_shared, output, registry, steam, utils

from patch import blacklist, manifest_utils, replacer, styling, unins, vpk_utils, xml_utils


def patcher(mod=None, pakname=None):
    from ui import gui

    with gui.interactive_lock():
        output.clean()

        if conditions.is_dota_running("&close_dota_terminal", "warning"):
            return

        if not conditions.check_binaries():
            conditions.resolve_dependencies()
            if not conditions.check_binaries():
                output.add_text("&failure_terminal", msg_type="error")
                return

        try:
            mod_list = constants.mods_with_order if mod is None else [mod]

            for item in os.listdir(base.logs_dir):
                fs.remove_path(os.path.join(base.logs_dir, item))

            fs.create_dirs(
                base.cache_dir,
                base.build_dir,
                base.replace_dir,
                base.merge_dir,
                constants.minify_dota_compile_input_path,
                constants.minify_dota_tools_required_path,
            )

            blank_file_extensions = helper.get_blank_file_extensions()  # list of extensions in bin/blank-files

            current_dota_version = ""
            if os.path.exists(constants.dota_steam_inf_path):
                with utils.open_utf8(constants.dota_steam_inf_path) as f:
                    current_dota_version = f.read()

            cached_dota_version = ""
            if os.path.exists(base.dota_steam_inf_cache):
                with utils.open_utf8(base.dota_steam_inf_cache) as f:
                    cached_dota_version = f.read()

            dota_version_changed = current_dota_version != cached_dota_version

            if dota_version_changed and current_dota_version:
                with utils.open_utf8(base.dota_steam_inf_cache, "w") as f:
                    f.write(current_dota_version)

            dota_pak_contents = vpk.open(constants.dota_game_pak_path)
            core_pak_contents = vpk.open(constants.dota_core_pak_path)
            dota_extracts = []
            core_extracts = []

            if conditions.workshop_installed:
                styling_dictionary = {}
                xml_modifications = {}
            replacer_source_extracts = []
            replacer_targets = []

            dependency_checkbox_states = [mods_shared.get_state(cb) for cb in mods_shared.mods_with_order]
            dependencies_resolved = False

            while not dependencies_resolved:
                for dependency_dict in constants.mod_dependencies_list:
                    for dependant, dependencies in dependency_dict.items():
                        if mods_shared.get_state(dependant):
                            for dependency in dependencies:
                                try:
                                    if not conditions.workshop_installed:
                                        workshop = False
                                        for method_path in conditions.workshop_required_methods:
                                            if os.path.exists(os.path.join(base.mods_dir, dependency, method_path)):
                                                workshop = True
                                                break
                                        (
                                            mods_shared.set_state(dependency, False)
                                            if workshop
                                            else mods_shared.set_state(dependency, True)
                                        )
                                    else:
                                        mods_shared.set_state(dependency, True)
                                except Exception:
                                    log.write_warning(
                                        f"Mod dependency {dependency} for {mod} couldn't be resolved, might be that the mod doesn't exist."
                                    )
                new_states = [mods_shared.get_state(cb) for cb in mods_shared.mods_with_order]
                if sum(dependency_checkbox_states) == sum(new_states):
                    dependencies_resolved = True
                dependency_checkbox_states = new_states

            if mod is None:
                conflicts_found = {}
                for conflict_dict in constants.mod_conflicts_list:
                    for conflict_mod, conflicts in conflict_dict.items():
                        if conflict_mod in mod_list and mods_shared.get_state(conflict_mod):
                            active_conflicts = []
                            for conflicting_mod in conflicts:
                                if conflicting_mod in mod_list and mods_shared.get_state(conflicting_mod):
                                    active_conflicts.append(conflicting_mod)
                            if active_conflicts:
                                conflicts_found[conflict_mod] = active_conflicts

                if conflicts_found:
                    output.add_text("&conflicts_detected", msg_type="error")
                    for conflict_mod, active_conflicts in conflicts_found.items():
                        output.add_text(f"{conflict_mod} -> {', '.join(active_conflicts)}", msg_type="error")
                    return

                if not base.HEADLESS:
                    from ui import checkboxes as _checkboxes

                    _checkboxes.save()

            game_contents_file_init = False
            for folder in mod_list:
                mod_path = os.path.join(base.mods_dir, folder)
                mod_cfg = manifest_utils.get_mod(mod_path)
                visual = mod_cfg.get("visual", True)

                if mod is None:
                    apply_without_user_confirmation = mod_cfg.get("always", False)
                else:  # will not be in mods.json
                    apply_without_user_confirmation = False

                # ---------------------------------- STEP 1 ---------------------------------- #
                # ---------------- Colect mod data and extract necessary files --------------- #
                # ---------------------------------------------------------------------------- #
                try:
                    if (
                        mod is not None or apply_without_user_confirmation or (visual and mods_shared.get_state(folder))
                    ):  # step into folders that have ticked checkboxes only
                        blacklist_txt = os.path.join(mod_path, "blacklist.txt")
                        if conditions.workshop_installed:
                            styling_css = os.path.join(mod_path, "styling.css")
                            xml_mod_file = xml_utils.get_xml_mod_file(mod_path)
                            files_uncompiled_dir = os.path.join(mod_path, "files_uncompiled")
                        script_file = os.path.join(mod_path, "script.py")
                        replacer_file = os.path.join(mod_path, "replacer.csv")
                        files_dir = os.path.join(mod_path, "files")

                        helper.exec_script(script_file, folder, "loop")
                        output.add_text("&installing_terminal", folder)
                        if conditions.workshop_installed:
                            if os.path.exists(files_uncompiled_dir):
                                shutil.copytree(
                                    files_uncompiled_dir,
                                    constants.minify_dota_compile_input_path,
                                    dirs_exist_ok=True,
                                    ignore=shutil.ignore_patterns("*.gitkeep"),
                                )
                        if os.path.exists(files_dir):
                            shutil.copytree(
                                files_dir,
                                constants.minify_dota_compile_output_path,
                                dirs_exist_ok=True,
                                ignore=shutil.ignore_patterns("*.gitkeep"),
                            )

                        if conditions.workshop_installed and xml_mod_file and os.path.exists(xml_mod_file):
                            with utils.open_utf8(xml_mod_file) as file:
                                mod_xml = jsonc.load(file)
                            for path, mods in mod_xml.items():
                                xml_modifications.setdefault(path, []).extend(mods)

                        if not game_contents_file_init:
                            gamepakcontents_path = os.path.join(base.bin_dir, "gamepakcontents.txt")
                            if dota_version_changed or not os.path.exists(gamepakcontents_path):
                                with utils.open_utf8(gamepakcontents_path, "w") as file:
                                    for filepath in dota_pak_contents:
                                        file.write(filepath + "\n")
                            game_contents_file_init = True

                        # ------------------------------- blacklist.txt ------------------------------ #
                        if os.path.exists(blacklist_txt):
                            blacklist.process(blacklist_txt, folder, blank_file_extensions)

                        # --------------------------------- styling.css --------------------------------- #
                        if conditions.workshop_installed and os.path.exists(styling_css):
                            styling.parse_styling_file(
                                styling_css,
                                mod_cfg,
                                folder,
                                config.get_mod(folder),
                                styling_dictionary,
                                core_extracts,
                                dota_extracts,
                            )

                        # --------------------------------- replacer.csv --------------------------------- #
                        replacer.process(replacer_file, folder, replacer_source_extracts, replacer_targets)

                except Exception:
                    log.write_warning()

                # Extract XMLs to be modified (assume they are in game VPK)
                if conditions.workshop_installed:
                    for path in xml_modifications.keys():
                        compiled = path.replace(".xml", ".vxml_c")
                        dota_extracts.append(compiled)

            if conditions.workshop_installed:
                output.add_text("&starting_extraction")
                core_extracts = list(set(core_extracts))
                dota_extracts = list(set(dota_extracts))
                vpk_utils.extract(core_pak_contents, core_extracts)
                vpk_utils.extract(dota_pak_contents, dota_extracts)
                # ---------------------------------- STEP 2 ---------------------------------- #
                # ------------------- Decompile all files in "build" folder ------------------ #
                # ---------------------------------------------------------------------------- #
                output.add_text("&decompiling_terminal")

                # prevent gameinfo confusion
                dummy_gameinfo = os.path.join(base.build_dir, "gameinfo.gi")
                dota_gameinfo_path = os.path.join(
                    steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota", "gameinfo.gi"
                )
                if os.path.exists(dota_gameinfo_path):
                    shutil.copy(dota_gameinfo_path, dummy_gameinfo)

                with open(base.log_s2v, "w") as file:
                    res = subprocess.run(
                        [
                            constants.s2v_exec_path,
                            "--input",
                            base.build_dir,
                            "--recursive",
                            "--vpk_decompile",
                            "--output",
                            base.build_dir,
                        ],
                        stdout=file,
                        stderr=subprocess.STDOUT,
                        creationflags=subprocess.CREATE_NO_WINDOW if base.OS == base.WIN else 0,
                    )
                    if res.returncode != 0:
                        log.write_warning(
                            f"Source2Viewer exited with code {res.returncode}. See {base.log_s2v} for details."
                        )

                fs.remove_path(dummy_gameinfo)

                with ThreadPoolExecutor() as executor:
                    xml_mod_args = [
                        (os.path.join(base.build_dir, path), mods) for path, mods in xml_modifications.items()
                    ]
                    executor.map(lambda p: xml_utils.apply_modifications(*p), xml_mod_args)
                helper.bulk_exec_script("after_decompile")
                # ---------------------------------- STEP 3 ---------------------------------- #
                # ---------------------------- CSS resourcecompile --------------------------- #
                # ---------------------------------------------------------------------------- #
                output.add_text("&compiling_resource_terminal")
                styles_by_file = {}
                for path, style in styling_dictionary.values():
                    sanitized_path = path[1:] if path.startswith("!") else path
                    css_file_path = os.path.join(base.build_dir, f"{sanitized_path}.css")
                    if css_file_path not in styles_by_file:
                        styles_by_file[css_file_path] = []
                    styles_by_file[css_file_path].append(style)

                with ThreadPoolExecutor() as executor:
                    executor.map(styling.apply_styles_to_file, styles_by_file.items())

                shutil.copytree(
                    base.build_dir,
                    constants.minify_dota_compile_input_path,
                    dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("*.vcss_c", "*.vxml_c"),
                )

                helper.compile()
            helper.bulk_exec_script("after_recompile")

            if replacer_source_extracts:
                vpk_utils.extract(dota_pak_contents, replacer_source_extracts, base.replace_dir)
                with ThreadPoolExecutor() as executor:
                    executor.map(replacer.process_replacer, replacer_targets)

            # ---------------------------------- STEP 4 ---------------------------------- #
            # -------- Create VPK from game folder and save into Minify directory -------- #
            # ---------------------------------------------------------------------------- #
            vpk_utils.dump_metadata(constants.minify_dota_compile_output_path, mod_name=mod)

            fs.create_dirs(helper.output_path)
            native_mods = vpk.new(constants.minify_dota_compile_output_path)
            output.add_text("&compiling_terminal")
            pakname = "pak66" if pakname is None else pakname
            native_mods.save(os.path.join(helper.output_path, f"{pakname}_dir.vpk"))

            # ---------------------------------- STEP 5 ---------------------------------- #
            # -------------------------- Merge VPKs into pak65 --------------------------- #
            # ---------------------------------------------------------------------------- #

            # Check if there are any VPK mods selected
            vpk_mods_to_merge = []
            for mod_name in mod_list:
                if mod_name.endswith(".vpk") and (mod is not None or mods_shared.get_state(mod_name)):
                    vpk_mods_to_merge.append(mod_name)

            # Only create pak65 if there are VPK mods to merge
            if vpk_mods_to_merge:
                output.add_text("&merging_vpks")

                for mod_name in vpk_mods_to_merge:
                    mod_path = os.path.join(base.mods_dir, mod_name)
                    try:
                        mod_vpk = vpk.open(mod_path)
                        vpk_utils.dump(mod_vpk, base.merge_dir, check_exists=True)
                        output.add_text("&merged_mod", mod_name)
                    except Exception:
                        log.write_warning("&failed_merge_mod", mod_name)

                vpk_utils.dump_metadata(base.merge_dir, vpk_mods=vpk_mods_to_merge)

                output.add_text("&creating_merged_vpk")
                merged_mods = vpk.new(base.merge_dir)
                merged_mods.save(os.path.join(helper.output_path, "pak65_dir.vpk"))

                output.add_text("&success_merged_vpk", msg_type="success")
            else:
                # No VPK mods selected - remove pak65 if it exists from previous patches
                pak65_path = os.path.join(helper.output_path, "pak65_dir.vpk")
                if os.path.exists(pak65_path):
                    with utils.try_pass():
                        # Verify it's a Minify-created pak65 by checking metadata
                        pak65_contents = vpk.open(pak65_path)
                        if "minify_vpk_mods.txt" in pak65_contents or "minify_version.txt" in pak65_contents:
                            fs.remove_path(pak65_path)

            # ---------------------------------- STEP 6 ---------------------------------- #
            # --------------------------- Run Browser Hooks ------------------------------ #
            # ---------------------------------------------------------------------------- #
            for browser_config in registry.get_browser_configs():
                if hasattr(browser_config, "on_build"):
                    browser_config.on_build(mod_list, mod)

            # ---------------------------------- STEP 7 ---------------------------------- #
            # -------------------------- Clean paths and inform -------------------------- #
            # ---------------------------------------------------------------------------- #

            fs.remove_path(
                constants.minify_dota_compile_input_path,
                constants.minify_dota_compile_output_path,
                base.build_dir,
                base.replace_dir,
                base.merge_dir,
            )

            # handle language option automatically
            if config.get("fix_options", True):
                if steam.fix_launch_options():
                    fs.open_thing(steam.steam_executable_path, "-exitsteam")
                    steam_close_retries = 0
                    while any(
                        p.info.get("name") == os.path.basename(steam.steam_executable_path)
                        for p in psutil.process_iter(attrs=["name"])
                    ):
                        if steam_close_retries >= 3:
                            output.add_text("&failed_steam_close", 3, msg_type="error")
                            break
                        output.add_text("&waiting_steam_to_close")
                        time.sleep(2)
                        steam_close_retries += 1
                    if steam_close_retries < 5:
                        fs.open_thing(steam.steam_executable_path)

            helper.bulk_exec_script("after_patch", False)

            output.add_separator()
            output.add_text("&success_terminal", msg_type="success")
            output.add_text("&launch_option", config.get("output_locale", "minify"), msg_type="warning")

            if os.path.exists(base.log_warnings) and os.path.getsize(base.log_warnings) != 0:
                output.add_text("&minify_encountered_errors_terminal", msg_type="warning")
            playsound3.playsound(os.path.join(base.sounds_dir, "success.wav"), block=False)

            if config.get("launch_dota_after_patch", False):
                webbrowser.open(f"steam://rungameid/{base.STEAM_DOTA_ID}")
            if config.get("kill_self_after_patch", False):
                gui.close()

        # chimes are from pixabay.com/sound-effects/chime-74910/
        except (PermissionError, playsound3.PlaysoundException):
            log.write_warning()

        except Exception:
            log.write_crashlog()

            output.add_separator()
            output.add_text("&failure_terminal", msg_type="error")
            output.add_text("&check_logs_terminal", msg_type="warning")
            playsound3.playsound(os.path.join(base.sounds_dir, "fail.wav"), block=False)


def patch_seperate():
    # TODO: fix, broken since who knows when
    # Mods that don't end up in config file will not be included (mods that are non-visual), fix?
    # Mods that have nothing to do with the built pak, will also create a pak
    with utils.open_utf8(base.mods_config_dir) as file:
        mods = jsonc.load(file)
    i = 20
    for mod in mods:
        if mods[mod]:
            i += 1
            patcher(mod, f"pak{i}")
            print(f"Created pak{i} with the mod {mod}")
