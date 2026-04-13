"The universe"

import csv
import os
import re
import shutil
import subprocess
import threading
import time
import webbrowser
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

import dearpygui.dearpygui as dpg
import jsonc
import playsound3
import psutil
import vpk

# isort: split

import conditions
import helper
from core import base, config, constants, fs, log, steam, utils
from ui import checkboxes, terminal

game_contents_file_init = False


def patcher(mod=None, pakname=None):
    from ui import gui

    with gui.interactive_lock():
        terminal.clean()

        if conditions.is_dota_running("&close_dota_terminal", "warning"):
            return

    try:
        mod_list = constants.mods_with_order if mod is None else [mod]

        for item in os.listdir(base.logs_dir):
            fs.remove_path(os.path.join(base.logs_dir, item))

        fs.create_dirs(
            base.build_dir,
            base.replace_dir,
            base.merge_dir,
            constants.minify_dota_compile_input_path,
            constants.minify_dota_tools_required_path,
        )

        blank_file_extensions = helper.get_blank_file_extensions()  # list of extensions in bin/blank-files
        dota_pak_contents = vpk.open(constants.dota_game_pak_path)
        core_pak_contents = vpk.open(constants.dota_core_pak_path)
        dota_extracts = []
        core_extracts = []

        if conditions.workshop_installed:
            styling_dictionary = {}
            xml_modifications = {}
        replacer_source_extracts = []
        replacer_targets = []

        dependency_checkbox_states = [dpg.get_value(cb) for cb in checkboxes.checkboxes]
        dependencies_resolved = False

        while not dependencies_resolved:
            for dependency_dict in constants.mod_dependencies_list:
                for dependant, dependencies in dependency_dict.items():
                    if dpg.get_value(dependant):
                        for dependency in dependencies:
                            try:
                                if not conditions.workshop_installed:
                                    workshop = False
                                    for method_path in conditions.workshop_required_methods:
                                        if os.path.exists(os.path.join(base.mods_dir, dependency, method_path)):
                                            workshop = True
                                            break
                                    dpg.set_value(dependency, False) if workshop else dpg.set_value(dependency, True)
                                else:
                                    dpg.set_value(dependency, True)
                            except Exception:
                                log.write_warning(
                                    f"Mod dependency {dependency} for {mod} couldn't be resolved, might be that the mod doesn't exist."
                                )
            new_states = [dpg.get_value(cb) for cb in checkboxes.checkboxes]
            if sum(dependency_checkbox_states) == sum(new_states):
                dependencies_resolved = True
            dependency_checkbox_states = new_states

        if mod is None:
            checkboxes.save()

        for folder in mod_list:
            mod_path = os.path.join(base.mods_dir, folder)
            cfg_path = os.path.join(mod_path, "modcfg.json")

            mod_cfg = config.read_json_file(cfg_path)
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
                    mod is not None or apply_without_user_confirmation or (visual and dpg.get_value(folder))
                ):  # step into folders that have ticked checkboxes only
                    blacklist_txt = os.path.join(mod_path, "blacklist.txt")
                    if conditions.workshop_installed:
                        styling_css = os.path.join(mod_path, "styling.css")
                        xml_mod_file = os.path.join(mod_path, "xml_mod.json")
                        files_uncompiled_dir = os.path.join(mod_path, "files_uncompiled")
                    script_file = os.path.join(mod_path, "script.py")
                    replacer_file = os.path.join(mod_path, "replacer.csv")
                    files_dir = os.path.join(mod_path, "files")

                    helper.exec_script(script_file, folder, "loop")
                    terminal.add_text("&installing_terminal", folder)
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

                    if conditions.workshop_installed and os.path.exists(xml_mod_file):
                        with utils.open_utf8(xml_mod_file) as file:
                            mod_xml = jsonc.load(file)
                        for path, mods in mod_xml.items():
                            xml_modifications.setdefault(path, []).extend(mods)

                    global game_contents_file_init
                    if not game_contents_file_init:
                        # TODO: check pak01 hash, log it & run this only if it's different
                        with utils.open_utf8(
                            os.path.join(base.bin_dir, "gamepakcontents.txt"),
                            "w",
                        ) as file:
                            for filepath in dota_pak_contents:
                                file.write(filepath + "\n")
                        game_contents_file_init = True

                    # ------------------------------- blacklist.txt ------------------------------ #
                    if os.path.exists(blacklist_txt):
                        process_blacklist(blacklist_txt, folder, blank_file_extensions)

                    # --------------------------------- styling.css --------------------------------- #
                    if conditions.workshop_installed and os.path.exists(styling_css):
                        with utils.open_utf8(styling_css) as file:
                            content = file.read()

                        # placeholder replacement
                        mod_settings = config.get_mod(folder)

                        # Fallback to modcfg.json defaults
                        defaults = {
                            s["key"]: s["default"]
                            for s in mod_cfg.get("settings", [])
                            if isinstance(s, dict) and "key" in s and "default" in s
                        }

                        content = re.sub(
                            r"<&(.*?)>",
                            lambda m: str(mod_settings.get(m.group(1), defaults.get(m.group(1), m.group(0)))),
                            content,
                        )

                        matches = list(re.finditer(r"/\*\s*([cg]):(.*?)\s*\*/", content))
                        for i, match in enumerate(matches):
                            indicator = match.group(1)
                            path = match.group(2).strip()

                            start = match.end()
                            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
                            style = content[start:end].strip()

                            if style:
                                path = f"!{path}" if indicator == "c" else path
                                styling_dictionary[f"styling-css-{folder}-{i}"] = (path, style)

                        for _, path_style in list(styling_dictionary.items()):
                            sanitized_path = (
                                path_style[0][1:] if path_style[0].startswith("!") else path_style[0]
                            )  # horrible hack
                            fs.create_dirs(os.path.join(base.build_dir, os.path.dirname(sanitized_path)))
                            try:
                                if path_style[0].startswith("!"):
                                    core_extracts.append(f"{sanitized_path}.vcss_c")
                                else:
                                    dota_extracts.append(f"{sanitized_path}.vcss_c")
                            except KeyError:
                                log.write_warning(
                                    f"Path does not exist in VPK -> '{sanitized_path}.vcss_c', error in 'mods/{folder}/styling.css'"
                                )
                    # --------------------------------- replacer.csv --------------------------------- #
                    if os.path.exists(replacer_file):
                        with utils.open_utf8(replacer_file, newline="") as file:
                            for row in csv.reader(file):
                                if len(row) >= 2 and row[0] and row[1]:
                                    replacer_source_extracts.append(row[1])  # Source (content)
                                    replacer_targets.append((row[1], row[0]))  # (Source, Target)
                                else:
                                    log.write_warning(f"Invalid row in replacer.csv for {folder}: {row}")

            except Exception:
                log.write_warning()

            # Extract XMLs to be modified (assume they are in game VPK)
            if conditions.workshop_installed:
                for path in xml_modifications.keys():
                    compiled = path.replace(".xml", ".vxml_c")
                    dota_extracts.append(compiled)

        if conditions.workshop_installed:
            terminal.add_text("&starting_extraction")
            core_extracts = list(set(core_extracts))
            dota_extracts = list(set(dota_extracts))
            vpk_extractor(core_pak_contents, core_extracts)
            vpk_extractor(dota_pak_contents, dota_extracts)
            # ---------------------------------- STEP 2 ---------------------------------- #
            # ------------------- Decompile all files in "build" folder ------------------ #
            # ---------------------------------------------------------------------------- #
            terminal.add_text("&decompiling_terminal")

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
                        os.path.join(".", constants.s2v_executable),
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
                xml_mod_args = [(os.path.join(base.build_dir, path), mods) for path, mods in xml_modifications.items()]
                executor.map(lambda p: apply_xml_modifications(*p), xml_mod_args)
            helper.bulk_exec_script("after_decompile")
            # ---------------------------------- STEP 3 ---------------------------------- #
            # ---------------------------- CSS resourcecompile --------------------------- #
            # ---------------------------------------------------------------------------- #
            terminal.add_text("&compiling_resource_terminal")
            styles_by_file = {}
            for path, style in styling_dictionary.values():
                sanitized_path = path[1:] if path.startswith("!") else path
                css_file_path = os.path.join(base.build_dir, f"{sanitized_path}.css")
                if css_file_path not in styles_by_file:
                    styles_by_file[css_file_path] = []
                styles_by_file[css_file_path].append(style)

            with ThreadPoolExecutor() as executor:
                executor.map(apply_styles_to_file, styles_by_file.items())

            shutil.copytree(
                base.build_dir,
                constants.minify_dota_compile_input_path,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("*.vcss_c", "*.vxml_c"),
            )

            # TODO: use helper.compile instead
            with open(base.log_rescomp, "wb") as file:
                command = [
                    constants.dota_resource_compiler_path,
                    "-i",
                    constants.minify_dota_compile_input_path + "/*",
                    "-r",
                ]
                if base.OS != base.WIN:
                    command.insert(0, "wine")

                rescomp = subprocess.run(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,  # compiler complains if minify_dota_compile_input_path is empty
                    creationflags=subprocess.CREATE_NO_WINDOW if base.OS == base.WIN else 0,
                )
                if rescomp.stdout != b"":
                    file.write(rescomp.stdout)

                # if sp_compiler.stderr != b"":
                #     decoded_err = sp_compiler.stderr.decode("utf-8")
                #     raise Exception(decoded_err)
        helper.bulk_exec_script("after_recompile")

        if replacer_source_extracts:
            vpk_extractor(dota_pak_contents, replacer_source_extracts, base.replace_dir)
            with ThreadPoolExecutor() as executor:
                executor.map(process_replacer, replacer_targets)

        # ---------------------------------- STEP 4 ---------------------------------- #
        # -------- Create VPK from game folder and save into Minify directory -------- #
        # ---------------------------------------------------------------------------- #
        # insert metadata to pak
        if mod is None:
            shutil.copy(
                base.mods_config_dir,
                os.path.join(constants.minify_dota_compile_output_path, "minify_mods.json"),
            )
        else:
            open(os.path.join(constants.minify_dota_compile_output_path, f"{mod}.txt"), "w").close()

        with utils.open_utf8(os.path.join(constants.minify_dota_compile_output_path, "minify_version.txt"), "w") as f:
            f.write(base.VERSION)

        fs.create_dirs(helper.output_path)
        native_mods = vpk.new(constants.minify_dota_compile_output_path)
        terminal.add_text("&compiling_terminal")
        pakname = "pak66" if pakname is None else pakname
        native_mods.save(os.path.join(helper.output_path, f"{pakname}_dir.vpk"))

        # ---------------------------------- STEP 5 ---------------------------------- #
        # -------------------------- Merge VPKs into pak65 --------------------------- #
        # ---------------------------------------------------------------------------- #

        # Check if there are any VPK mods selected
        vpk_mods_to_merge = []
        for mod_name in mod_list:
            if mod_name.endswith(".vpk") and (mod is not None or dpg.get_value(mod_name)):
                vpk_mods_to_merge.append(mod_name)

        # Only create pak65 if there are VPK mods to merge
        if vpk_mods_to_merge:
            terminal.add_text("&merging_vpks")

            for mod_name in vpk_mods_to_merge:
                mod_path = os.path.join(base.mods_dir, mod_name)
                try:
                    mod_vpk = vpk.open(mod_path)
                    dump_vpk(mod_vpk, base.merge_dir, check_exists=True)
                    terminal.add_text("&merged_mod", mod_name)
                except Exception:
                    log.write_warning("&failed_merge_mod", mod_name)

            # Insert metadata to pak65
            # Create a metadata file listing the VPK mods included
            with utils.open_utf8(os.path.join(base.merge_dir, "minify_vpk_mods.txt"), "w") as f:
                f.write("\n".join(vpk_mods_to_merge))

            with utils.open_utf8(os.path.join(base.merge_dir, "minify_version.txt"), "w") as f:
                f.write(base.VERSION)

            terminal.add_text("&creating_merged_vpk")
            merged_mods = vpk.new(base.merge_dir)
            merged_mods.save(os.path.join(helper.output_path, "pak65_dir.vpk"))

            terminal.add_text("&success_merged_vpk", msg_type="success")
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
                        terminal.add_text("&failed_steam_close", 3, msg_type="error")
                        break
                    terminal.add_text("&waiting_steam_to_close")
                    time.sleep(2)
                    steam_close_retries += 1
                if steam_close_retries < 5:
                    fs.open_thing(steam.steam_executable_path)

        helper.bulk_exec_script("after_patch", False)

        gui.unlock_interaction()
        terminal.add_seperator()
        terminal.add_text("&success_terminal", msg_type="success")
        terminal.add_text("&launch_option", dpg.get_value("output_select"), msg_type="warning")

        if os.path.exists(base.log_warnings) and os.path.getsize(base.log_warnings) != 0:
            terminal.add_text("&minify_encountered_errors_terminal", msg_type="warning")
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

        terminal.add_seperator()
        terminal.add_text("&failure_terminal", msg_type="error")
        terminal.add_text("&check_logs_terminal", msg_type="warning")
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


def uninstall(sender=None, app_data=None, user_data=None):
    from ui import gui

    with gui.interactive_lock():
        terminal.clean()
        time.sleep(0.05)

        # smart uninstall
        pak_pattern = r"^pak\d{2}_dir\.vpk$"
        for path in constants.minify_dota_possible_language_output_paths:
            if os.path.isdir(path):
                for item in os.listdir(path):
                    if os.path.isfile(os.path.join(path, item)) and re.fullmatch(pak_pattern, item):
                        pak_contents = vpk.open(os.path.join(path, item))
                        mod_names_with_txt = [s + ".txt" for s in constants.visually_available_mods]
                        for file in [
                            "minify_mods.json",
                            # TODO if this exists, pull & parse to enable uninstallers
                            "minify_vpk_mods.txt",
                            "minify_version.txt",
                            *mod_names_with_txt,
                        ]:
                            if file in pak_contents:
                                fs.remove_path(os.path.join(path, item))
                                break
        # TODO remove lang param if out locale is minify
        helper.bulk_exec_script("uninstall")
        terminal.add_text("&mods_removed_terminal")


def dump_vpk(vpk_obj, output_dir, check_exists=True):
    for filepath in vpk_obj:
        full_path = os.path.join(output_dir, filepath)
        if check_exists and os.path.exists(full_path):
            continue

        fs.create_dirs(os.path.dirname(full_path))
        vpk_obj.get_file(filepath).save(full_path)


def vpk_extractor(vpk_to_extract_from, paths, path_to_extract_to=base.build_dir):
    if isinstance(paths, str):
        paths = [paths]

    vpk_lock = threading.Lock()

    def extract_file(path):
        if not os.path.exists(full_path := os.path.join(path_to_extract_to, path)):  # extract files from VPK only once
            terminal.add_text("&extracting_terminal", path)
            with vpk_lock:
                pakfile = vpk_to_extract_from.get_file(path)

            if pakfile:
                fs.create_dirs(os.path.dirname(full_path))
                pakfile.save(full_path)
            else:
                log.write_warning(f"File not found in VPK: {path}")

    with ThreadPoolExecutor() as executor:
        executor.map(extract_file, paths)


def apply_xml_modifications(xml_file, modifications):
    # TODO: implement selectors like
    # DOTAXThing#Thing.Thing[attrib="val"]

    if not os.path.exists(xml_file):
        log.write_warning(f"[Missing XML] '{xml_file}' not found; skipping modifications")
        return
    tree = ET.parse(xml_file)
    root = tree.getroot()

    def find_by_id(node, node_id):
        return node.find(f".//*[@id='{node_id}']")

    def find_with_parent_by_id(node, node_id):
        # Returns (element, parent) or (None, None)
        for parent in node.iter():
            for child in list(parent):
                if child.get("id") == node_id:
                    return child, parent
        # root itself
        if node.get("id") == node_id:
            return node, None
        return None, None

    def ensure_unique_include(container_tag, src_value):
        container = root.find(container_tag)
        if container is None:
            container = ET.Element(container_tag)
            # put styles/scripts at the top for readability
            root.insert(0, container)
        # de-duplicate
        for inc in container.findall("include"):
            if inc.get("src") == src_value:
                return  # already present
        include = ET.SubElement(container, "include")
        include.set("src", src_value)

    for mod in modifications:
        action = mod.get("action")

        if action == "add_script":
            src = mod.get("src", "")
            ensure_unique_include("scripts", src)

        elif action == "add_style_include":
            src = mod.get("src", "")
            ensure_unique_include("styles", src)

        elif action == "set_attribute":
            tag = mod.get("tag")
            element = root.find(f".//{tag}")
            if element is None:
                element = root.find(f".//*[@id='{tag}']")
            if element is not None:
                attr = mod.get("attribute")
                val = mod.get("value")
                if attr is not None and val is not None:
                    element.set(attr, val)

        elif action == "add_child":
            parent_id = mod.get("parent_id")
            xml_snippet = mod.get("xml", "")
            if parent_id and xml_snippet:
                parent_elem = find_by_id(root, parent_id)
                if parent_elem is not None:
                    try:
                        child = ET.fromstring(xml_snippet)
                        parent_elem.append(child)
                    except ET.ParseError:
                        log.write_warning("[XML ParseError] add_child")
                else:
                    log.write_warning(f"[add_child] parent id '{parent_id}' not found in {os.path.basename(xml_file)}")

        elif action == "move_into":
            target_id = mod.get("target_id")
            new_parent_id = mod.get("new_parent_id")
            if target_id and new_parent_id:
                elem, old_parent = find_with_parent_by_id(root, target_id)
                new_parent = find_by_id(root, new_parent_id)
                if elem is not None and new_parent is not None:
                    if old_parent is not None:
                        old_parent.remove(elem)
                    new_parent.append(elem)
                else:
                    if elem is None:
                        log.write_warning(
                            f"[move_into] target id '{target_id}' not found in {os.path.basename(xml_file)}"
                        )
                    if new_parent is None:
                        log.write_warning(
                            f"[move_into] new_parent id '{new_parent_id}' not found in {os.path.basename(xml_file)}"
                        )

        elif action == "insert_after":
            target_id = mod.get("target_id")
            xml_snippet = mod.get("xml", "")
            if target_id and xml_snippet:
                target, parent = find_with_parent_by_id(root, target_id)
                if target is not None and parent is not None:
                    try:
                        new_elem = ET.fromstring(xml_snippet)
                        idx = list(parent).index(target)
                        parent.insert(idx + 1, new_elem)
                    except ET.ParseError:
                        log.write_warning("[XML ParseError] insert_after")
                else:
                    log.write_warning(
                        f"[insert_after] target id '{target_id}' not found in {os.path.basename(xml_file)}"
                    )

        elif action == "insert_before":
            target_id = mod.get("target_id")
            xml_snippet = mod.get("xml", "")
            if target_id and xml_snippet:
                target, parent = find_with_parent_by_id(root, target_id)
                if target is not None and parent is not None:
                    try:
                        new_elem = ET.fromstring(xml_snippet)
                        idx = list(parent).index(target)
                        parent.insert(idx, new_elem)
                    except ET.ParseError:
                        log.write_warning("[XML ParseError] insert_before")
                else:
                    log.write_warning(
                        f"[insert_before] target id '{target_id}' not found in {os.path.basename(xml_file)}"
                    )

    try:
        tree.write(xml_file, encoding="utf-8")
    except TypeError:
        # Older Python may not accept encoding for ElementTree.write in text mode
        tree.write(xml_file)


def apply_styles_to_file(item):
    file_path, styles_to_apply = item

    def remove_braced_block(text, start_pattern):
        while True:
            match = re.search(start_pattern, text)
            if not match:
                break

            start_index = match.start()

            open_brace_index = text.find("{", match.end())
            if open_brace_index == -1:
                break

            brace_count = 1
            current_index = open_brace_index + 1
            while brace_count > 0 and current_index < len(text):
                if text[current_index] == "{":
                    brace_count += 1
                elif text[current_index] == "}":
                    brace_count -= 1
                current_index += 1

            if brace_count == 0:
                text = text[:start_index] + text[current_index:]
            else:
                break
        return text

    with utils.open_utf8(file_path) as file:
        content = file.read()

    new_defines = set()
    new_keyframes = set()

    for style in styles_to_apply:
        defines = re.findall(r"@define\s+([\w-]+)\s*:", style)
        new_defines.update(defines)

        keyframes = re.findall(r"@keyframes\s+(?:'|\")?([\w\s-]+)(?:'|\")?", style)
        new_keyframes.update(keyframes)

    for define_name in new_defines:
        pattern = rf"@define\s+{re.escape(define_name)}\s*:\s*.*?(?:;|$)"
        content = re.sub(pattern, "", content, flags=re.DOTALL)

    for keyframe_name in new_keyframes:
        start_pattern = rf"@keyframes\s+(?:'|\")?{re.escape(keyframe_name)}(?:'|\")?"
        content = remove_braced_block(content, start_pattern)

    unique_styles_to_add = []
    for style in styles_to_apply:
        if style not in content and style not in unique_styles_to_add:
            unique_styles_to_add.append(style)

    with utils.open_utf8(file_path, "w") as file:
        file.write(content)
        if unique_styles_to_add:
            file.write("\n" + "\n".join(unique_styles_to_add))


def process_blacklist(blacklist_txt, folder, blank_file_extensions):
    with utils.open_utf8(blacklist_txt) as file:
        lines = file.readlines()
        blacklist_data = []
        blacklist_data_exclusions = []

        for index, line in enumerate(lines):
            line = line.strip()

            if line.startswith("#") or line == "":
                continue

            elif line.startswith(">>") or line.startswith("**"):
                for path in process_blacklist_dir(index, line, folder):
                    blacklist_data.append(path)

            elif line.startswith("*-"):
                for path in process_blacklist_dir(index, line, folder):
                    blacklist_data_exclusions.append(path)

            elif line.startswith("--"):
                blacklist_data_exclusions.append(line[2:])

            else:
                if line.endswith(tuple(blank_file_extensions)):
                    blacklist_data.append(line)
                else:
                    log.write_warning(
                        f"[Invalid Extension] '{line}' in 'mods/{folder}/blacklist.txt' [line: {index + 1}] does not end in one of the valid extensions -> {blank_file_extensions}"
                    )

    for exclusion in blacklist_data_exclusions:
        if exclusion in blacklist_data:
            blacklist_data.remove(exclusion)
        else:
            print(
                f"[Unnecessary Exclusion] '{exclusion}' in '{folder}' is not necessary, the mod doesn't include this file."
            )

    def copy_blank_file(line):
        line = line.strip()
        path, extension = os.path.splitext(line)

        fs.create_dirs(os.path.join(constants.minify_dota_compile_output_path, os.path.dirname(path)))

        try:
            shutil.copy(
                os.path.join(base.blank_files_dir, f"blank{extension}"),
                os.path.join(
                    constants.minify_dota_compile_output_path,
                    path + extension,
                ),
            )
        except FileNotFoundError:
            log.write_warning(
                f"[Invalid Extension] '{line}' in 'mods/{os.path.basename(folder)}/blacklist.txt' does not end in one of the valid extensions -> {blank_file_extensions}"
            )

    with ThreadPoolExecutor() as executor:
        executor.map(copy_blank_file, blacklist_data)


def process_replacer(item):
    source, target = item
    terminal.add_text("&replacing_terminal", source, target)
    fs.create_dirs(os.path.dirname(target_dir := os.path.join(constants.minify_dota_compile_output_path, target)))
    shutil.copy(os.path.join(base.replace_dir, source), target_dir)


def process_blacklist_dir(index, line, folder):
    data = []

    line = line[2:] if line.startswith("**") or line.startswith("*-") else line
    line = line + "/" if line.startswith(">>") else line
    line = line[2:] if line.startswith(">>") else line

    lines = subprocess.run(
        [
            os.path.join(".", constants.rg_executable),
            "--no-filename",
            "--no-line-number",
            "--color=never",
            line,
            os.path.join(base.bin_dir, "gamepakcontents.txt"),
        ],
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW if base.OS == base.WIN else 0,
    )
    data = lines.stdout.splitlines()

    if not data:
        log.write_warning(
            f"[Directory Not Found] Could not find '{line}' in pak01_dir.vpk -> mods/{folder}/blacklist.txt [line: {index + 1}]"
        )

    return data


def wipe_lang_dirs():
    terminal.clean()
    uninstall()
    for path in constants.minify_dota_possible_language_output_paths:
        if os.path.isdir(path):
            fs.remove_path(path)
            terminal.add_text("&clean_lang_dirs", path)
