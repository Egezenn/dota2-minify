import json
import os
import shutil
import stat
import subprocess
import time
import urllib.error
from urllib.request import urlopen
import webbrowser
import xml.etree.ElementTree as ET

import dearpygui.dearpygui as ui

import mpaths

compile_path = ""
details_label_text_var = ""
locale = ""
localization_dict = {}
localizations = []
mod_selection_window_var = ""
output_path = mpaths.minify_dota_pak_output_path
warnings = []
workshop_installed = False


def handleWarnings(logs_dir):
    global warnings

    if len(warnings) != 0:
        with open(os.path.join(logs_dir, "warnings.txt"), "w") as file:
            for line in warnings:
                file.write(line + "\n")
        add_text_to_terminal(
            localization_dict["minify_encountered_errors_terminal_text_var"], "minify_error_var", "warning"
        )


def scroll_to_terminal_end():
    time.sleep(0.05)
    ui.set_y_scroll("terminal_window", ui.get_y_scroll_max("terminal_window"))


# TODO: revise
def add_text_to_terminal(text, tag: int | str | None = None, type: str | None = None):
    kwargs = {}
    if tag is not None:
        kwargs["tag"] = tag
    if type is not None:
        if type == "error":
            color = (255, 0, 0)

        elif type == "warning":
            color = (255, 255, 0)

        elif type == "success":
            color = (0, 255, 0)

        else:
            color = (0, 230, 230)

        kwargs["color"] = color

    ui.add_text(default_value=text, parent="terminal_window", wrap=482, **kwargs)
    scroll_to_terminal_end()


def disableWorkshopMods(mods_dir, mods_folders, checkboxes):
    for folder in mods_folders:
        mod_path = os.path.join(mods_dir, folder)
        styling_txt = os.path.join(mod_path, "styling.txt")
        for box in checkboxes:
            if checkboxes[box] == folder:
                if os.path.exists(styling_txt):
                    ui.configure_item(box, enabled=False, default_value=False)


def cleanFolders():
    for root, dirs, files in os.walk(mpaths.logs_dir):
        for filename in files:
            open(os.path.join(root, filename), "w").close()

    os.makedirs(mpaths.build_dir, exist_ok=True)
    os.makedirs(mpaths.minify_dota_compile_input_path, exist_ok=True)


def urlDispatcher(url):
    webbrowser.open(url)


def getBlankFileExtensions(blank_files_dir):
    extensions = []
    for file in os.listdir(blank_files_dir):
        extensions.append(os.path.splitext(file)[1])
    return extensions


def get_available_localizations():
    "Initializes `localization_dict` at startup"
    global localizations
    # get available variables for text
    with open(mpaths.localization_file_dir, "r", encoding="utf-8") as file:
        localization_data = json.load(file)
    sub_headers = set()
    for header in localization_data.values():
        if isinstance(header, dict):
            sub_headers.update(header.keys())
    localizations = sorted(list(sub_headers))

    for key, value in localization_data.items():
        if key.endswith("var") == True:
            localization_dict[key] = value["EN"]


def clean_terminal():
    ui.delete_item("terminal_window", children_only=True)


def close():
    ui.stop_dearpygui()


# TODO: also revise this
def change_localization(init=False):
    global locale
    with open(mpaths.localization_file_dir, "r", encoding="utf-8") as localization_file:
        localization_data = json.load(localization_file)
        if init == True:
            if os.path.exists(mpaths.locale_file_dir):
                with open(mpaths.locale_file_dir, "r") as file:
                    locale = file.readline()
                    ui.configure_item("lang_select", default_value=locale)
            else:
                locale = ui.get_value("lang_select")
                with open(mpaths.locale_file_dir, "w") as file:
                    file.write(locale)

        for key, value in localization_data.items():
            locale = ui.get_value("lang_select")
            if key.endswith("var") == True:
                if ui.does_item_exist(key) == True:
                    if locale in localization_data[key]:
                        localization_dict[key] = value[locale]
                        ui.set_value(key, value=value[locale])
                    else:
                        ui.set_value(key, value=value["EN"])
                else:
                    if locale in localization_data[key]:
                        localization_dict[key] = value[locale]
                    else:
                        localization_dict[key] = value["EN"]
            if ui.does_item_exist(key) == True:
                if key.endswith("var") == False and ui.get_item_info(key).get("type") == "mvAppItemType::mvButton":
                    if locale in localization_data[key]:
                        ui.configure_item(key, label=value[locale])
                    else:  # default to english if the line isn't available on selected locale
                        ui.configure_item(key, label=value["EN"])
                if key.endswith("var") == False and ui.get_item_info(key).get("type") == "mvAppItemType::mvText":
                    if locale in localization_data[key]:
                        ui.configure_item(key, default_value=value[locale])
                    else:
                        ui.configure_item(key, default_value=value["EN"])
                with open(mpaths.locale_file_dir, "w") as file:
                    file.write(locale)

        for tag_id in ui.get_item_children("details_tags")[1]:
            tag = ui.get_item_alias(tag_id).removesuffix("_details_text_value_tag")
            mod_path = os.path.join(mpaths.mods_dir, tag)
            note_path = os.path.join(mod_path, f"notes_{locale}.txt")
            try:
                if os.path.exists(note_path):
                    with open(note_path, "r", encoding="utf-8") as file:
                        data = file.read()
                    ui.configure_item(tag_id, default_value=data)
                else:
                    note_path = os.path.join(mod_path, "notes_en.txt")
                    with open(note_path, "r", encoding="utf-8") as file:
                        data = file.read()
                    ui.configure_item(tag_id, default_value=data)
            except FileNotFoundError:
                data = ""
        global details_label_text_var, mod_selection_window_var
        details_label_text_var = localization_data["details_button_label_var"][locale]
        mod_selection_window_var = localization_data["mod_selection_window_var"][locale]
        ui.configure_item("mod_menu", label=mod_selection_window_var)
        for id in ui.get_item_children("mod_menu")[1]:
            for item in ui.get_item_children(id)[1]:
                if ui.get_item_alias(item).endswith("_button_show_details_tag"):
                    ui.configure_item(item, label=localization_data["details_button_label_var"][locale])


def change_output_path():
    global output_path
    selection = ui.get_value("output_select")
    output_path = [lang for lang in mpaths.minify_dota_possible_language_output_paths if selection in lang][0]


def vpkExtractor(vpk_to_extract_from, paths):
    if isinstance(paths, str):
        paths = [paths]
    for path in paths:
        fullPath = os.path.join(mpaths.build_dir, path)
        if not os.path.exists(fullPath):  # extract files from VPK only once
            add_text_to_terminal(
                f"{localization_dict['extracting_terminal_text_var']}{path}",
                f"extracting_{path}_tag",
            )
            vpk_path = path.replace(os.sep, "/")
            pakfile = vpk_to_extract_from.get_file(vpk_path)
            os.makedirs(os.path.dirname(fullPath), exist_ok=True)
            pakfile.save(fullPath)


def apply_xml_modifications(xml_file, modifications):
    if not os.path.exists(xml_file):
        warnings.append(f"[Missing XML] '{xml_file}' not found; skipping modifications")
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
                    except ET.ParseError as e:
                        warnings.append(f"[XML ParseError] add_child -> {e}")
                else:
                    warnings.append(f"[add_child] parent id '{parent_id}' not found in {os.path.basename(xml_file)}")

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
                        warnings.append(
                            f"[move_into] target id '{target_id}' not found in {os.path.basename(xml_file)}"
                        )
                    if new_parent is None:
                        warnings.append(
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
                    except ET.ParseError as e:
                        warnings.append(f"[XML ParseError] insert_after -> {e}")
                else:
                    warnings.append(f"[insert_after] target id '{target_id}' not found in {os.path.basename(xml_file)}")

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
                    except ET.ParseError as e:
                        warnings.append(f"[XML ParseError] insert_before -> {e}")
                else:
                    warnings.append(
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

        settings_path = os.path.join(mpaths.build_dir, "panorama", "layout", "popups", "popup_settings_reborn.xml")
        tree = ET.parse(settings_path)
        root = tree.getroot()
        settings_body = root.find(".//PopupSettingsRebornSettingsBody")
        if settings_body is not None:
            settings_body.append(minify_section)
            tree.write(settings_path)
    except ET.ParseError:
        pass


def urlValidator(url):
    content = []
    url = url.replace("@@", "")

    try:
        for line in urlopen(url):
            try:
                line = line.decode("utf-8").split()
                line = "".join(line)
            except UnicodeDecodeError as exception:
                warnings.append(
                    f"[{type(exception).__name__}]"
                    + " Cannot decode -> "
                    + str(line)
                    + " Make sure your URL is using a 'utf-8' charset"
                )

            content.append(line)

    except urllib.error.HTTPError as exception:
        warnings.append(f"[{type(exception).__name__}]" + f" Could not connect to -> " + url)

    except ValueError as exception:
        warnings.append(f"[{type(exception).__name__}]" + f" Invalid URL -> " + url)

    except urllib.error.URLError as exception:
        warnings.append(f"[{type(exception).__name__}]" + f" Invalid URL -> " + url)

    return content


def processBlacklistDir(index, line, folder):
    data = []

    line = line[2:] if line.startswith(">>") or line.startswith("**") else line

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
        warnings.append(
            f"[Directory Not Found] Could not find '{line}' in pak01_dir.vpk -> mods\\{folder}\\blacklist.txt [line: {index+1}]"
        )

    return data


def processBlackList(index, line, folder, blank_file_extensions):
    data = []

    if line.startswith("@@"):
        content = urlValidator(line)

        for line in content:

            if line.startswith("#") or line == "":
                continue

            if line.startswith(">>") or line.startswith("**"):
                for path in processBlacklistDir(index, line, folder):
                    data.append(path)
                continue

            try:
                if line.endswith(tuple(blank_file_extensions)):
                    data.append(line)
                else:
                    warnings.append(
                        f"[Invalid Extension] '{line}' in 'mods\\{folder}\\blacklist.txt' [line: {index+1}] does not end in one of the valid extensions -> {blank_file_extensions}"
                    )

            except TypeError as exception:
                warnings.append(f"[{type(exception).__name__}]" + " Invalid data type in line -> " + str(line))

    return data


def open_dir(path, args=""):
    """Open a directory/file or launch an executable with optional args.

    - Directories: open in system file manager.
    - Files: on macOS, reveal in Finder to avoid "no app" errors; otherwise try default handler.
    - Executables: launch via subprocess (Windows uses startfile).
    """
    import shlex
    if path == mpaths.dota2_tools_executable:
        os.makedirs(mpaths.minify_dota_tools_required_path, exist_ok=True)
    try:
        # Normalize path
        target = path

        # If args are provided and target is executable, prefer launching directly
        if args:
            if mpaths.OS == "Windows":
                os.startfile(target, arguments=args)
                return
            # POSIX: launch executable directly when possible
            if os.access(target, os.X_OK) and os.path.isfile(target):
                cmd = [target] + shlex.split(args)
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            # Non-executables with args: fall back to opening container directory
            target = os.path.dirname(target) or "."

        # No args path open
        if os.path.isdir(target):
            if mpaths.OS == "Windows":
                os.startfile(target)
            elif mpaths.OS == "Darwin":
                subprocess.run(["open", target])
            else:
                subprocess.run(["xdg-open", target])
        else:
            if mpaths.OS == "Windows":
                os.startfile(target)
            elif mpaths.OS == "Darwin":
                # Reveal the file in Finder to avoid missing-app association errors
                subprocess.run(["open", "-R", target])
            else:
                subprocess.run(["xdg-open", target])
    except FileNotFoundError:
        add_text_to_terminal(f"{path}{localization_dict['open_dir_fail_text_var']}", type="error")


def compile(sender, app_data, user_data):
    folder = compile_path
    compile_output_path = os.path.join(folder, "compiled")
    clean_terminal()

    if not folder and os.path.exists(os.path.join(mpaths.config_dir, "custom")):
        add_text_to_terminal(localization_dict["compile_fallback_path_usage_text_var"])
        folder = os.path.join(mpaths.config_dir, "custom")
        compile_output_path = os.path.join(mpaths.config_dir, "compiled")

    if folder:
        remove_path(mpaths.minify_dota_compile_input_path, compile_output_path)
        os.makedirs(mpaths.minify_dota_compile_input_path)

        items = os.listdir(folder)
        try:
            items.remove("compiled")
        except ValueError:
            pass

        for item in items:
            if os.path.isdir(os.path.join(folder, item)):
                shutil.copytree(os.path.join(folder, item), os.path.join(mpaths.minify_dota_compile_input_path, item))
            else:
                shutil.copy(os.path.join(folder, item), mpaths.minify_dota_compile_input_path)
        with open(os.path.join(mpaths.logs_dir, "resourcecompiler.txt"), "w") as file:
            subprocess.run(
                [
                    mpaths.dota_resource_compiler_path,
                    "-i",
                    mpaths.minify_dota_compile_input_path + "/*",
                    "-r",
                ],
                stdout=file,
            )

        os.makedirs(mpaths.minify_dota_compile_output_path, exist_ok=True)
        shutil.copytree(os.path.join(mpaths.minify_dota_compile_output_path), compile_output_path)

        remove_path(mpaths.minify_dota_compile_input_path, mpaths.minify_dota_compile_output_path)
        os.makedirs(mpaths.minify_dota_tools_required_path, exist_ok=True)

        add_text_to_terminal(localization_dict["compile_successful_text_var"])
    else:
        add_text_to_terminal(localization_dict["compile_no_path_text_var"])


def select_compile_dir(sender, app_data):
    global compile_path
    compile_path = app_data["current_path"]


def remove_path(*paths):
    "Superset of `shutil.rmtree` to handle permissions and take in list of paths and also delete files."
    for path in paths:
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        except PermissionError:
            os.chmod(path, stat.S_IWUSR)
            shutil.rmtree(path)
            print(f"Forced deletion of: {path}")
        except FileNotFoundError:
            print(f"Skipped deletion of: {path}")
