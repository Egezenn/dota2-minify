import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import time
import urllib.error
import webbrowser
from urllib.request import urlopen

import dearpygui.dearpygui as ui
import vpk

import mpaths

workshop_installed = False
localizations = []
locale = ""
localization_dict = {}
details_label_text_var = ""
mod_selection_window_var = ""
compile_path = ""
pak1_contents = vpk.open(mpaths.dota_pak01_path)  # debugger complains because of 350k elements
warnings = []


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
    time.sleep(0.02)
    ui.set_y_scroll("terminal_window", ui.get_y_scroll_max("terminal_window"))


# TODO revise
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
                if os.stat(styling_txt).st_size != 0:
                    ui.configure_item(box, enabled=False, default_value=False)


def cleanFolders():
    rmtrees(mpaths.build_dir, mpaths.minify_dota_maps_output_path)
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
    localizations = list(sub_headers)

    for key, value in localization_data.items():
        if key.endswith("var") == True:
            localization_dict[key] = value["EN"]


def clean_terminal():
    ui.delete_item("terminal_window", children_only=True)


def close():
    ui.stop_dearpygui()


# TODO fix a crash where if a mod doesn't have the selected locales notes
# TODO also revise this
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
            if os.path.exists(note_path):
                with open(note_path, "r", encoding="utf-8") as file:
                    data = file.read()
                ui.configure_item(tag_id, default_value=data)
            else:
                note_path = os.path.join(mod_path, "notes_en.txt")
                with open(note_path, "r", encoding="utf-8") as file:
                    data = file.read()
                ui.configure_item(tag_id, default_value=data)

        global details_label_text_var
        global mod_selection_window_var
        details_label_text_var = localization_data["details_button_label_var"][locale]
        mod_selection_window_var = localization_data["mod_selection_window_var"][locale]
        ui.configure_item("mod_menu", label=mod_selection_window_var)
        for id in ui.get_item_children("mod_menu")[1]:
            for item in ui.get_item_children(id)[1]:
                if ui.get_item_alias(item).endswith("_button_show_details_tag"):
                    ui.configure_item(item, label=localization_data["details_button_label_var"][locale])


def vpkExtractor(path):
    global pak1_contents
    # TODO implement functionality to pull from core
    fullPath = os.path.join(mpaths.build_dir, path)
    if not os.path.exists(fullPath):  # extract files from VPK only once
        add_text_to_terminal(f"{localization_dict["extracting_terminal_text_var"]}{path}", f"extracting_{path}_tag")
        path = path.replace(os.sep, "/")
        pakfile = pak1_contents.get_file(path)
        pakfile.save(os.path.join(fullPath))


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
                    "[{}]".format(type(exception).__name__)
                    + " Cannot decode -> "
                    + str(line)
                    + " Make sure your URL is using a 'utf-8' charset"
                )

            content.append(line)

    except urllib.error.HTTPError as exception:
        warnings.append("[{}]".format(type(exception).__name__) + f" Could not connect to -> " + url)

    except ValueError as exception:
        warnings.append("[{}]".format(type(exception).__name__) + f" Invalid URL -> " + url)

    except urllib.error.URLError as exception:
        warnings.append("[{}]".format(type(exception).__name__) + f" Invalid URL -> " + url)

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
            os.path.join(mpaths.bin_dir, "pak1contents.txt"),
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
                warnings.append("[{}]".format(type(exception).__name__) + " Invalid data type in line -> " + str(line))

    return data


def write_locale(text):
    with open("locale.txt", "w") as file:
        file.write(text)


def calculate_md5(file_path):
    "Calculates the MD5 hash of a file."
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as file:
        for byte_block in iter(lambda: file.read(4096), b""):
            md5_hash.update(byte_block)
    return md5_hash.hexdigest()


async def open_dir(path, args=""):
    try:
        if args:
            if mpaths.OS == "Windows":
                os.startfile(path, arguments=args)
            elif mpaths.OS == "Darwin":
                os.system(f'open "{path} {args}')
            else:
                os.system(f'xdg-open "{path} {args}')
        else:
            if mpaths.OS == "Windows":
                os.startfile(path)
            elif mpaths.OS == "Darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
    except FileNotFoundError:
        add_text_to_terminal(f"{path}{localization_dict["open_dir_fail_text_var"]}", type="error")


def compile(sender, app_data, user_data):
    folder = compile_path
    if folder:
        clean_terminal()
        compile_output_path = os.path.join(folder, "compiled")

        rmtrees(mpaths.minify_dota_compile_input_path, compile_output_path)
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
        with open(os.path.join(mpaths.logs_dir, "Source2Viewer-CLI.txt"), "w") as file:
            subprocess.run(
                [
                    mpaths.dota_resource_compiler_path,
                    "-i",
                    mpaths.minify_dota_compile_input_path + "/*",
                    "-r",
                ],
                stdout=file,
            )

        shutil.copytree(os.path.join(mpaths.minify_dota_compile_output_path), compile_output_path)

        rmtrees(mpaths.minify_dota_compile_input_path, mpaths.minify_dota_compile_output_path)

        add_text_to_terminal(localization_dict["compile_successful_text_var"])
    else:
        clean_terminal()
        add_text_to_terminal(localization_dict["compile_no_folder_text_var"])


def select_compile_dir(sender, app_data):
    global compile_path
    compile_path = app_data["current_path"]


def rmtrees(*paths):
    "Superset of `shutil.rmtree` to handle permissions and take in list of paths."
    for path in paths:
        try:
            shutil.rmtree(path)
        except PermissionError:
            if mpaths.OS == "Windows":
                os.chmod(path, stat.S_IWRITE)
            else:
                os.chmod(path, os.stat(path).st_mode | stat.S_IWUSR)
            shutil.rmtree(path)
            print(f"Forced deletion of: {path}")
        except FileNotFoundError:
            print(f"Skipped deletion of: {path}")
