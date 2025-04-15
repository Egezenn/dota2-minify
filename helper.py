import hashlib
import json
import os
import shutil
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

# ---------------------------------------------------------------------------- #
#                                   Warnings                                   #
# ---------------------------------------------------------------------------- #
# Output can be passed here to display as warnings at the end of patching.

warnings = []


def handleWarnings(logs_dir):
    global warnings

    if len(warnings) != 0:
        with open(os.path.join(logs_dir, "warnings.txt"), "w") as file:
            for line in warnings:
                file.write(line + "\n")
            # print(f"{len(warnings)} error occured. Check logs\\warnings.txt for details.")
        add_text_to_terminal(
            "Minify encountered errors. Check Minify\\logs\\warnings.txt for details.",
            "minify_error_var",
        )


def scroll_to_terminal_end():
    time.sleep(0.02)
    ui.set_y_scroll("terminal_window", ui.get_y_scroll_max("terminal_window"))


def add_text_to_terminal(text, tag):
    ui.add_text(default_value=text, parent="terminal_window", wrap=482, tag=tag)
    scroll_to_terminal_end()


def disableWorkshopMods(mods_dir, mods_folders, checkboxes):
    for folder in mods_folders:
        mod_path = os.path.join(mods_dir, folder)
        styling_txt = os.path.join(mod_path, "styling.txt")
        for box in checkboxes:
            if checkboxes[box] == folder:
                if os.stat(styling_txt).st_size != 0:
                    ui.configure_item(box, enabled=False, default_value=False)


def cleanFolders(
    build_dir, logs_dir, content_dir, game_dir, minify_dir, dota_minify_maps
):
    shutil.rmtree(build_dir, ignore_errors=True)

    for root, dirs, files in os.walk(logs_dir):
        for filename in files:
            open(os.path.join(root, filename), "w").close()
    for root, dirs, files in os.walk(content_dir):
        for filename in files:
            os.remove(os.path.join(root, filename))
    for root, dirs, files in os.walk(game_dir):
        for filename in files:
            os.remove(os.path.join(root, filename))
    for root, dirs, files in os.walk(dota_minify_maps):
        for filename in files:
            os.remove(os.path.join(root, filename))
    os.makedirs(os.path.join(minify_dir, "build"))


def urlDispatcher(url):
    webbrowser.open(url)


def getBlankFileExtensions(blank_files_dir):
    extensions = []
    for file in os.listdir(blank_files_dir):
        extensions.append(os.path.splitext(file)[1])
    return extensions


def get_available_localizations():
    global localizations
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


def change_localization(init=False):
    global locale
    with open(mpaths.localization_file_dir, "r", encoding="utf-8") as localization_file:
        localization_data = json.load(localization_file)
        if init == True:
            if os.path.exists(mpaths.locale_file_dir):
                with open(mpaths.locale_file_dir, "r") as file:
                    locale = file.readline()
                    ui.configure_item("lang_select", default_value=f"{locale}")
            else:
                locale = ui.get_value("lang_select")
                with open(mpaths.locale_file_dir, "w") as file:
                    file.write(locale)
        for key, value in localization_data.items():
            locale = ui.get_value("lang_select")
            if key.endswith("var") == True:
                print(key)
                if locale in localization_data[key]:
                    localization_dict[key] = value[locale]
                    ui.set_value(key, value=value[locale])
                else:
                    ui.set_value(key, value=value["EN"])
            if ui.does_item_exist(key) == True:
                if (
                    key.endswith("var") == False
                    and ui.get_item_info(key).get("type") == "mvAppItemType::mvButton"
                ):
                    if locale in localization_data[key]:
                        ui.configure_item(key, label=value[locale])
                    else:  # default to english if the line isn't available on selected locale
                        ui.configure_item(key, label=value["EN"])
                if (
                    key.endswith("var") == False
                    and ui.get_item_info(key).get("type") == "mvAppItemType::mvText"
                ):
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
                note_path = os.path.join(mod_path, f"notes_en.txt")
                with open(note_path, "r", encoding="utf-8") as file:
                    data = file.read()
                ui.configure_item(tag_id, default_value=data)


def validate_map_file():
    add_text_to_terminal(
        f"{localization_dict["checking_map_file_var"]}", "map_check_text_tag"
    )

    os.makedirs(mpaths.maps_dir, exist_ok=True)

    if os.path.exists(mpaths.minify_map) == False:
        shutil.copyfile(mpaths.dota_user_map_dir, mpaths.minify_map)
        add_text_to_terminal("""-> Updating map file...""", "map_update_text_tag")

    elif os.path.exists(mpaths.minify_map) and (
        calculate_md5(mpaths.dota_user_map_dir) != calculate_md5(mpaths.minify_map)
    ):
        add_text_to_terminal("""-> Updating map file...""", "map_update_text_tag")
        os.remove(mpaths.minify_map)
        shutil.copyfile(mpaths.dota_user_map_dir, mpaths.minify_map)

    else:
        add_text_to_terminal(
            """-> Map file is up to date...""", "map_up_to_date_text_tag"
        )


def vpkExtractor(path, pak01_dir, build_dir):
    pak1 = vpk.open(pak01_dir)
    fullPath = os.path.join(build_dir, path)
    if not os.path.exists(fullPath):  # extract files from VPK only once
        add_text_to_terminal(f"    extracting: {path}", f"extracting_{path}_tag")
        path = path.replace(os.sep, "/")
        pakfile = pak1.get_file(path)
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
        warnings.append(
            "[{}]".format(type(exception).__name__) + f" Could not connect to -> " + url
        )

    except ValueError as exception:
        warnings.append(
            "[{}]".format(type(exception).__name__) + f" Invalid URL -> " + url
        )

    except urllib.error.URLError as exception:
        warnings.append(
            "[{}]".format(type(exception).__name__) + f" Invalid URL -> " + url
        )

    return content


def processBlacklistDir(index, line, folder, pak01_dir):
    data = []
    line = line.replace(">>", "")
    line = line.replace(os.sep, "/")
    pak1 = vpk.open(pak01_dir)

    for filepath in pak1:
        if filepath.startswith(line):
            data.append(filepath)

    if not data:
        warnings.append(
            f"[Directory Not Found] Could not find '{line}' in pak01_dir.vpk -> mods\\{folder}\\blacklist.txt [line: {index+1}]"
        )

    return data


def processBlackList(index, line, folder, blank_file_extensions, pak01_dir):
    data = []

    if line.startswith("@@"):
        content = urlValidator(line)

        for line in content:

            if line.startswith("#"):
                continue

            if line.startswith(">>"):
                for path in processBlacklistDir(index, line, folder, pak01_dir):
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
                warnings.append(
                    "[{}]".format(type(exception).__name__)
                    + " Invalid data type in line -> "
                    + str(line)
                )

    return data


def write_locale(text):
    with open("locale.txt", "w") as file:
        file.write(text)


def calculate_md5(file_path):
    """Calculates the MD5 hash of a file."""
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as file:
        for byte_block in iter(lambda: file.read(4096), b""):
            md5_hash.update(byte_block)
    return md5_hash.hexdigest()
