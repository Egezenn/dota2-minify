from concurrent.futures import ThreadPoolExecutor
import threading
import csv
import os
import re
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET

import dearpygui.dearpygui as ui
import jsonc
import playsound3  # chimes are from pixabay.com/sound-effects/chime-74910/
import psutil
import vpk

import gui
import helper
import mpaths

game_contents_file_init = False


def patcher(mod=None, pakname=None):
    gui.lock_interaction()
    helper.clean_terminal()
    target = "dota2.exe" if mpaths.OS == "Windows" else "dota2"
    running = False
    for p in psutil.process_iter(attrs=["name"]):
        try:
            name = p.info.get("name") or ""
            if name == target:
                running = True
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    if running:
        helper.add_text_to_terminal(
            helper.localization_dict["close_dota_terminal_text_var"],
            "close_dota_text_tag",
            "warning",
        )
        return

    try:
        mod_list = mpaths.mods_with_order if mod is None else [mod]

        for item in os.listdir(mpaths.logs_dir):
            os.remove(os.path.join(mpaths.logs_dir, item))

        os.makedirs(mpaths.build_dir, exist_ok=True)
        os.makedirs(mpaths.replace_dir, exist_ok=True)
        os.makedirs(mpaths.minify_dota_compile_input_path, exist_ok=True)

        blank_file_extensions = helper.get_blank_file_extensions()  # list of extensions in bin/blank-files
        dota_pak_contents = vpk.open(mpaths.dota_game_pak_path)
        core_pak_contents = vpk.open(mpaths.dota_core_pak_path)
        dota_extracts = []
        core_extracts = []

        mod_menus = []
        styling_data = []  # path and style from every styling.txt
        styling_dictionary = {}
        xml_modifications = {}
        replacer_source_extracts = []
        replacer_targets = []

        dependency_checkbox_states = ui.get_values(gui.checkboxes)
        dependencies_resolved = False

        while not dependencies_resolved:
            for dependency_dict in mpaths.mod_dependencies_list:
                for dependant, dependencies in dependency_dict.items():
                    if ui.get_value(dependant):
                        for dependency in dependencies:
                            try:
                                ui.set_value(dependency, True)
                            except:
                                mpaths.write_warning(
                                    f"Mod dependency {dependency} for {mod} couldn't be resolved, might be that the mod doesn't exist."
                                )
            if sum(dependency_checkbox_states) == (sum(dependency_checkbox_states := ui.get_values(gui.checkboxes))):
                dependencies_resolved = True

        if mod is None:
            gui.save_checkbox_state()

        for folder in mod_list:
            mod_path = os.path.join(mpaths.mods_dir, folder)
            cfg_path = os.path.join(mod_path, "modcfg.json")

            visual, mod_cfg = mpaths.get_key_from_json_file_w_default(cfg_path, "visual", True)

            if mod is None:
                apply_without_user_confirmation = mpaths.get_key_from_dict_w_default(mod_cfg, "always", False)
            else:  # will not be in mods.json
                apply_without_user_confirmation = False

            try:
                if (
                    mod is not None or apply_without_user_confirmation or (visual and ui.get_value(folder))
                ):  # step into folders that have ticked checkboxes only
                    # TODO get rid of custom parsed textfiles
                    blacklist_txt = os.path.join(mod_path, "blacklist.txt")
                    styling_txt = os.path.join(mod_path, "styling.txt")
                    menu_xml = os.path.join(mod_path, "menu.xml")
                    xml_mod_file = os.path.join(mod_path, "xml_mod.json")
                    script_file = os.path.join(mod_path, "script.py")
                    replacer_file = os.path.join(mod_path, "replacer.csv")
                    files_dir = os.path.join(mod_path, "files")

                    helper.exec_script(script_file, folder, "loop")
                    helper.add_text_to_terminal(f"{helper.localization_dict['installing_terminal_text_var']} {folder}")
                    if os.path.exists(files_dir):
                        shutil.copytree(
                            files_dir,
                            mpaths.minify_dota_compile_output_path,
                            dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("*.gitkeep"),
                        )

                    if os.path.exists(menu_xml):
                        with open(menu_xml, "r", encoding="utf-8") as file:
                            data = file.read()
                            if data[:7] == r"<Panel ":
                                mod_menus.append(data)
                            else:
                                mpaths.write_warning(f"Improper mod menu on {folder}!")

                    if os.path.exists(xml_mod_file):
                        with open(xml_mod_file, "r", encoding="utf-8") as file:
                            mod_xml = jsonc.load(file)
                        for path, mods in mod_xml.items():
                            xml_modifications.setdefault(path, []).extend(mods)

                    # ------------------------------- blacklist.txt ------------------------------ #
                    if os.path.exists(blacklist_txt):
                        process_blacklist(blacklist_txt, folder, blank_file_extensions)

                    # --------------------------------- styling.txt --------------------------------- #
                    if os.path.exists(styling_txt):
                        with open(styling_txt) as file:
                            lines = file.readlines()

                            for line in lines:
                                line = line.strip()

                                if line.startswith("#") or line == "":
                                    continue
                                else:
                                    styling_data.append(line)

                        for index, line in enumerate(styling_data):
                            try:
                                line = line.split("@@")
                                path = line[0].strip()
                                style = line[1].strip()

                                styling_dictionary[f"styling-key{index + 1}"] = (
                                    path,
                                    style,
                                )

                            except:
                                mpaths.write_warning(
                                    f" Could not validate '{line}' in --> 'mods/{folder}/styling.txt' [line: {index + 1}]"
                                )

                        for key, path_style in list(styling_dictionary.items()):
                            sanitized_path = (
                                path_style[0][1:] if path_style[0].startswith("!") else path_style[0]
                            )  # horrible hack
                            os.makedirs(
                                os.path.join(
                                    mpaths.build_dir,
                                    os.path.dirname(sanitized_path),
                                ),
                                exist_ok=True,
                            )
                            try:
                                if path_style[0].startswith("!"):
                                    core_extracts.append(f"{sanitized_path}.vcss_c")
                                else:
                                    dota_extracts.append(f"{sanitized_path}.vcss_c")
                            except KeyError:
                                mpaths.write_warning(
                                    f"Path does not exist in VPK -> '{sanitized_path}.vcss_c', error in 'mods/{folder}/styling.txt'"
                                )
                    # --------------------------------- replacer.csv --------------------------------- #
                    if os.path.exists(replacer_file):
                        with open(replacer_file, newline="") as file:
                            for row in csv.reader(file):
                                try:
                                    if not (row[0] == "" and row[1] == ""):
                                        replacer_source_extracts.append(row[0])
                                        replacer_targets.append(row[1])
                                except:
                                    min_len = min(len(replacer_source_extracts), len(replacer_targets))
                                    replacer_source_extracts = replacer_source_extracts[:min_len]
                                    replacer_targets = replacer_targets[:min_len]
                                    mpaths.write_warning()

            except:
                mpaths.write_warning()

        if mod_menus:
            dota_extracts.append("panorama/layout/popups/popup_settings_reborn.vxml_c")
        # Extract XMLs to be modified (assume they are in game VPK)
        for path in xml_modifications.keys():
            compiled = path.replace(".xml", ".vxml_c")
            dota_extracts.append(compiled)

        global game_contents_file_init
        if not game_contents_file_init:
            # TODO: check pak01 hash, log it & run this only if it's different
            extract = subprocess.run(
                [
                    os.path.join(".", mpaths.s2v_executable),
                    "-i",
                    mpaths.dota_game_pak_path,
                    "-l",
                ],
                capture_output=True,
                text=True,
            )
            pattern = r"(.*) CRC:.*"
            replacement = r"\1"

            with open(
                os.path.join(mpaths.bin_dir, "gamepakcontents.txt"),
                "w",
            ) as file:
                for extract_line in extract.stdout.splitlines():
                    new_line = re.sub(pattern, replacement, extract_line.rstrip())
                    file.write(new_line + "\n")
            game_contents_file_init = True

        helper.add_text_to_terminal(helper.localization_dict["starting_extraction_text_var"])
        vpk_extractor(core_pak_contents, core_extracts)
        vpk_extractor(dota_pak_contents, dota_extracts)
        # ---------------------------------- STEP 2 ---------------------------------- #
        # ------------------- Decompile all files in "build" folder ------------------ #
        # ---------------------------------------------------------------------------- #
        helper.add_text_to_terminal(
            helper.localization_dict["decompiling_terminal_text_var"],
            "decompiling_text",
        )
        with open(mpaths.log_s2v, "w") as file:
            try:
                subprocess.run(
                    [
                        os.path.join(".", mpaths.s2v_executable),
                        "--input",
                        mpaths.build_dir,
                        "--recursive",
                        "--vpk_decompile",
                        "--output",
                        mpaths.build_dir,
                    ],
                    stdout=file,
                )
            except:
                mpaths.write_crashlog()

        if mod_menus:
            build_minify_menu(mod_menus)
        with ThreadPoolExecutor() as executor:
            xml_mod_args = [(os.path.join(mpaths.build_dir, path), mods) for path, mods in xml_modifications.items()]
            executor.map(lambda p: apply_xml_modifications(*p), xml_mod_args)
        gui.bulk_exec_script("after_decompile")
        # ---------------------------------- STEP 3 ---------------------------------- #
        # ---------------------------- CSS resourcecompile --------------------------- #
        # ---------------------------------------------------------------------------- #
        helper.add_text_to_terminal(
            helper.localization_dict["compiling_resource_terminal_text_var"],
            "compiling_resourcecompiler_text_tag",
        )

        styles_by_file = {}
        for path, style in styling_dictionary.values():
            sanitized_path = path[1:] if path.startswith("!") else path
            css_file_path = os.path.join(mpaths.build_dir, f"{sanitized_path}.css")
            if css_file_path not in styles_by_file:
                styles_by_file[css_file_path] = []
            styles_by_file[css_file_path].append(style)

        with ThreadPoolExecutor() as executor:
            executor.map(apply_styles_to_file, styles_by_file.items())

        shutil.copytree(
            mpaths.build_dir,
            mpaths.minify_dota_compile_input_path,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("*.vcss_c", "*.vxml_c"),
        )

        if helper.workshop_installed:
            with open(mpaths.log_rescomp, "wb") as file:
                command = [
                    mpaths.dota_resource_compiler_path,
                    "-i",
                    mpaths.minify_dota_compile_input_path + "/*",
                    "-r",
                ]
                if mpaths.OS != "Windows":
                    command.insert(0, "wine")

                rescomp = subprocess.run(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,  # compiler complains if minify_dota_compile_input_path is empty
                )
                if rescomp.stdout != b"":
                    file.write(rescomp.stdout)

                # if sp_compiler.stderr != b"":
                #     decoded_err = sp_compiler.stderr.decode("utf-8")
                #     raise Exception(decoded_err)
        gui.bulk_exec_script("after_recompile")

        if replacer_source_extracts and replacer_targets and (len(replacer_source_extracts) == len(replacer_targets)):
            vpk_extractor(dota_pak_contents, replacer_source_extracts, mpaths.replace_dir)
            with ThreadPoolExecutor() as executor:
                executor.map(process_replacer, replacer_targets)

        # ---------------------------------- STEP 6 ---------------------------------- #
        # -------- Create VPK from game folder and save into Minify directory -------- #
        # ---------------------------------------------------------------------------- #
        # insert metadata to pak
        if mod is None:
            shutil.copy(
                mpaths.mods_config_dir,
                os.path.join(mpaths.minify_dota_compile_output_path, "minify_mods.json"),
            )
        else:
            open(os.path.join(mpaths.minify_dota_compile_output_path, f"{mod}.txt"), "w").close()

        try:
            shutil.copy(
                mpaths.version_file_dir,
                os.path.join(mpaths.minify_dota_compile_output_path, "minify_version.txt"),
            )
        except FileNotFoundError:  # update ignore
            pass

        os.makedirs(helper.output_path, exist_ok=True)
        newpak = vpk.new(mpaths.minify_dota_compile_output_path)
        helper.add_text_to_terminal(
            helper.localization_dict["compiling_terminal_text_var"],
            "compiling_text",
        )
        pakname = "pak66" if pakname is None else pakname
        newpak.save(os.path.join(helper.output_path, f"{pakname}_dir.vpk"))

        helper.remove_path(
            mpaths.minify_dota_compile_input_path,
            mpaths.minify_dota_compile_output_path,
            mpaths.build_dir,
            mpaths.replace_dir,
        )

        gui.unlock_interaction()
        helper.add_text_to_terminal("-------------------------------------------------------", "spacer1_text")
        helper.add_text_to_terminal(
            helper.localization_dict["success_terminal_text_var"],
            "success_text_tag",
            "success",
        )
        # TODO: Use strings like this, without fstrings
        helper.add_text_to_terminal(
            helper.localization_dict["launch_option_text_var"].format(ui.get_value("output_select")),
            "launch_option_text",
            "warning",
        )

        if os.path.exists(mpaths.log_warnings) and os.path.getsize(mpaths.log_warnings) != 0:
            helper.add_text_to_terminal(
                helper.localization_dict["minify_encountered_errors_terminal_text_var"],
                "minify_error_var",
                "warning",
            )
        playsound3.playsound(os.path.join(mpaths.sounds_dir, "success.wav"), block=False)

    except:
        mpaths.write_crashlog()
        helper.open_thing(mpaths.log_crashlog)

        helper.add_text_to_terminal("-------------------------------------------------------", "spacer2_text")
        helper.add_text_to_terminal(
            helper.localization_dict["failure_terminal_text_var"],
            "patching_failed_text_tag",
            "error",
        )
        helper.add_text_to_terminal(
            helper.localization_dict["check_logs_terminal_text_var"],
            "check_logs_text_tag",
            "warning",
        )
        gui.unlock_interaction()
        playsound3.playsound(os.path.join(mpaths.sounds_dir, "fail.wav"), block=False)


def patch_seperate():
    # Mods that don't end up in config file will not be included (mods that are non-visual), fix?
    # Mods that have nothing to do with the built pak, will also create a pak
    with open(mpaths.mods_config_dir) as file:
        mods = jsonc.load(file)
    i = 20
    for mod in mods:
        if mods[mod]:
            i += 1
            patcher(mod, f"pak{i}")
            print(f"Created pak{i} with the mod {mod}")


def uninstaller():
    gui.hide_uninstall_popup()
    helper.clean_terminal()
    time.sleep(0.05)
    gui.lock_interaction()

    # smart uninstall
    pak_pattern = r"^pak\d{2}_dir\.vpk$"
    for dir in mpaths.minify_dota_possible_language_output_paths:
        if os.path.isdir(dir):
            for item in os.listdir(dir):
                if os.path.isfile(os.path.join(dir, item)) and re.fullmatch(pak_pattern, item):
                    pak_contents = vpk.open(os.path.join(dir, item))
                    mod_names_with_txt = [s + ".txt" for s in mpaths.visually_available_mods]
                    for file in ["minify_mods.json", "minify_version.txt", *mod_names_with_txt]:
                        if file in pak_contents:
                            os.remove(os.path.join(dir, item))
                            break

    gui.bulk_exec_script("uninstall")
    helper.add_text_to_terminal(
        helper.localization_dict["mods_removed_terminal_text_var"],
        "uninstaller_text_tag",
    )
    gui.unlock_interaction()


def vpk_extractor(vpk_to_extract_from, paths, path_to_extract_to=mpaths.build_dir):
    if isinstance(paths, str):
        paths = [paths]

    vpk_lock = threading.Lock()

    def extract_file(path):
        if not os.path.exists(full_path := os.path.join(path_to_extract_to, path)):  # extract files from VPK only once
            helper.add_text_to_terminal(
                helper.localization_dict["extracting_terminal_text_var"].format(path), f"extracting_{path}_tag"
            )
            vpk_path = path.replace(os.sep, "/")

            with vpk_lock:
                pakfile = vpk_to_extract_from.get_file(vpk_path)

            if pakfile:
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                pakfile.save(full_path)
            else:
                mpaths.write_warning(f"File not found in VPK: {vpk_path}")

    with ThreadPoolExecutor() as executor:
        executor.map(extract_file, paths)


def apply_xml_modifications(xml_file, modifications):
    if not os.path.exists(xml_file):
        mpaths.write_warning(f"[Missing XML] '{xml_file}' not found; skipping modifications")
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
                        mpaths.write_warning("[XML ParseError] add_child")
                else:
                    mpaths.write_warning(
                        f"[add_child] parent id '{parent_id}' not found in {os.path.basename(xml_file)}"
                    )

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
                        mpaths.write_warning(
                            f"[move_into] target id '{target_id}' not found in {os.path.basename(xml_file)}"
                        )
                    if new_parent is None:
                        mpaths.write_warning(
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
                        mpaths.write_warning("[XML ParseError] insert_after")
                else:
                    mpaths.write_warning(
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
                        mpaths.write_warning("[XML ParseError] insert_before")
                else:
                    mpaths.write_warning(
                        f"[insert_before] target id '{target_id}' not found in {os.path.basename(xml_file)}"
                    )

    try:
        tree.write(xml_file, encoding="utf-8")
    except TypeError:
        # Older Python may not accept encoding for ElementTree.write in text mode
        tree.write(xml_file)


def build_minify_menu(menus):
    minify_section_xml = r"""
<Panel class="SettingsSectionContainer" section="#minify" icon="s2r://panorama/images/control_icons/24px/check.vsvg">
  <Panel class="SettingsSectionTitleContainer LeftRightFlow">
    <Image class="SettingsSectionTitleIcon" texturewidth="48px" textureheight="48px" scaling="stretch-to-fit-preserve-aspect" src="s2r://panorama/images/control_icons/24px/check.vsvg" />
    <Label class="SettingsSectionTitle" text="Minify" />
  </Panel>
</Panel>
"""

    minify_section = ET.fromstring(minify_section_xml)
    try:
        for menu in menus:
            menu_element = ET.fromstring(menu)
        minify_section.append(menu_element)

        settings_path = os.path.join(
            mpaths.build_dir,
            "panorama",
            "layout",
            "popups",
            "popup_settings_reborn.xml",
        )
        tree = ET.parse(settings_path)
        root = tree.getroot()
        settings_body = root.find(".//PopupSettingsRebornSettingsBody")
        if settings_body is not None:
            settings_body.append(minify_section)
            tree.write(settings_path)
    except ET.ParseError:
        mpaths.write_warning()


def apply_styles_to_file(item):
    file_path, styles_to_apply = item
    with open(file_path, "r+") as file:
        content = file.read()

        unique_styles_to_add = []
        for style in styles_to_apply:
            if style not in content and style not in unique_styles_to_add:
                unique_styles_to_add.append(style)

        if unique_styles_to_add:
            file.write("\n" + "\n".join(unique_styles_to_add))


def process_blacklist(blacklist_txt, folder, blank_file_extensions):
    with open(blacklist_txt) as file:
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
                    mpaths.write_warning(
                        f"[Invalid Extension] '{line}' in 'mods/{folder}/blacklist.txt' [line: {index + 1}] does not end in one of the valid extensions -> {blank_file_extensions}"
                    )

    for exclusion in blacklist_data_exclusions:
        if exclusion in blacklist_data:
            blacklist_data.remove(exclusion)
        else:
            print(
                f"[Unnecessary Exclusion] '{exclusion}' in '{folder}' is not necessary, the mod doesn't include this file."
            )
    print(f"{folder}'s blacklist replaced {len(blacklist_data)} files!")

    def copy_blank_file(line):
        line = line.strip()
        path, extension = os.path.splitext(line)

        os.makedirs(
            os.path.join(
                mpaths.minify_dota_compile_output_path,
                os.path.dirname(path),
            ),
            exist_ok=True,
        )

        try:
            shutil.copy(
                os.path.join(mpaths.blank_files_dir, f"blank{extension}"),
                os.path.join(
                    mpaths.minify_dota_compile_output_path,
                    path + extension,
                ),
            )
        except FileNotFoundError:
            mpaths.write_warning(
                f"[Invalid Extension] '{line}' in 'mods/{os.path.basename(folder)}/blacklist.txt' does not end in one of the valid extensions -> {blank_file_extensions}"
            )

    with ThreadPoolExecutor() as executor:
        executor.map(copy_blank_file, blacklist_data)


def process_replacer(target):
    helper.add_text_to_terminal(helper.localization_dict["replacing_terminal_text_var"].format(target, target))
    os.makedirs(
        os.path.dirname(target_dir := os.path.join(mpaths.minify_dota_compile_output_path, target)),
        exist_ok=True,
    )
    shutil.copy(os.path.join(mpaths.replace_dir, target), target_dir)


def process_blacklist_dir(index, line, folder):
    data = []

    line = line[2:] if line.startswith("**") or line.startswith("*-") else line
    line = line + "/" if line.startswith(">>") else line
    line = line[2:] if line.startswith(">>") else line

    lines = subprocess.run(
        [
            os.path.join(".", mpaths.rg_executable),
            "--no-filename",
            "--no-line-number",
            "--color=never",
            line,
            os.path.join(mpaths.bin_dir, "gamepakcontents.txt"),
        ],
        capture_output=True,
        text=True,
    )
    data = lines.stdout.splitlines()
    data.pop(0)

    if not data:
        mpaths.write_warning(
            f"[Directory Not Found] Could not find '{line}' in pak01_dir.vpk -> mods/{folder}/blacklist.txt [line: {index + 1}]"
        )

    return data


def clean_lang_dirs():
    helper.clean_terminal()
    uninstaller()
    for path in mpaths.minify_dota_possible_language_output_paths:
        if os.path.isdir(path):
            helper.remove_path(path)
            helper.add_text_to_terminal(helper.localization_dict["clean_lang_dirs_text_var"].format(path))


def create_blank_mod():
    mod_name = "!Your-Mod-Name"
    path_to_mod = os.path.join(mpaths.mods_dir, mod_name)

    blacklist_template = r"""# This file is a list of path to files used to override those with blanks.
# Supported file types are can be found in `bin/blank-files`.

# A list of all the files (from the game pak) can be found in `bin/gamepakcontents.txt`.

# Syntax for this file starting from the line beginning is as follows:
# `#`: Comments
# `>>`: Directories
# `**`: RegExp patterns
# `*-`: RegExp patterns for exclusion
# `--`: Exclusions (for when you want to exclude specific files from bulk additions)

# After that with no blank spaces you put the path to the file you want to override.
# path/to/file

# particles/base_attacks/ranged_goodguy_launch.vpcf_c
# >>particles/sprays
# **taunt.*\.vsnd_c
"""
    styling_template = r"""# This file is a list of CSS paths and styling that will be appended to them.
# By the nature of this method modifications done here may break the original XML or CSS that gets updated resulting in a bad layout.
# In such cases, a repatch is required.

# If you encounter errors while patching, it's most likely that your CSS is invalid or the path is wrong.

# For Source 2 flavored CSS properties, refer to: https://developer.valvesoftware.com/wiki/Dota_2_Workshop_Tools/Panorama/CSS_Properties
# To live inspect the layout, open the workshop tools and press F6 and select the element you'd like to select from the XML.

# Syntax for this file starting from the line beginning is as follows:
# `#`: Comments 
# `!`: By default, the file is pulled from `dota 2 beta/game/dota/pak01_dir.vpk`.
#      However to change this behavior and pull files from `dota 2 beta/game/core/pak01_dir.vpk`, you can use this.

# path/to/file_without_extension @@ #example_id { property: value; }
"""
    script_template = r"""# This script template can be run both manually and from minify.
# You are able to use packages and modules from minify (you need an activated environment from the minify root or running with the tool `uv` can automatically handle this.)
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
if os.getcwd() != minify_root:
    os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

# Any package or module native to minify can be imported here
# import requests
#
# import mpaths
# ...


def main():
    pass
    # Code specific to your mod goes here, minify will try to execute this block.
    # If any exceptions occur, it'll be written to `logs` directory


if __name__ == "__main__":
    main()
"""
    mod_config_template = r"""{ // defaults doesn't need to be indicated
  "always": false, // false by default, apply them without checking mods.json or checkbox
  "dependencies": ["<mod>"], // None by default, add a mod dependency's name here 
  "order": 1, // default is 1, ordered from negative to positive to resolve any conflicts
  "visual": true // true by default, show it in the UI as a checkbox
}"""

    mod_menu_template = r""
    xml_mod_template = r"{}"

    helper.remove_path(path_to_mod)
    os.mkdir(path_to_mod)
    os.mkdir(os.path.join(path_to_mod, "files"))
    open(os.path.join(path_to_mod, "files", ".gitkeep"), "w").close()
    for locale in helper.localizations:
        open(os.path.join(path_to_mod, f"notes_{locale.lower()}.txt"), "w").close()
    with open(os.path.join(path_to_mod, "blacklist.txt"), "w") as file:
        file.write(blacklist_template)
    with open(os.path.join(path_to_mod, "styling.txt"), "w") as file:
        file.write(styling_template)
    with open(os.path.join(path_to_mod, "script.py"), "w") as file:
        file.write(script_template)
    with open(os.path.join(path_to_mod, "modcfg.json"), "w") as file:
        file.write(mod_config_template)
    with open(os.path.join(path_to_mod, "menu.xml"), "w") as file:
        file.write(mod_menu_template)
    with open(os.path.join(path_to_mod, "xml_mod.json"), "w") as file:
        file.write(xml_mod_template)
