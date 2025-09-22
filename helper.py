from ctypes import WinError
import importlib.util
import json
import os
import shlex
import shutil
import stat
import subprocess
import time
import urllib.error
from urllib.request import urlopen
import webbrowser

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


def handle_warnings():
    global warnings

    if len(warnings) != 0:
        with open(warning_log_path := os.path.join(mpaths.logs_dir, "warnings.txt"), "a") as file:
            for line in warnings:
                file.write(line + "\n")
        add_text_to_terminal(
            localization_dict["minify_encountered_errors_terminal_text_var"],
            "minify_error_var",
            "warning",
        )
        open_thing(os.path.join(warning_log_path))


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


def disable_workshop_mods(checkboxes):
    if not workshop_installed:
        for folder in mpaths.mods_folders:
            mod_path = os.path.join(mpaths.mods_dir, folder)
            worskhop_required_modification_methods = ["styling.txt", "menu.xml", "xml_mod.json"]

            for box in checkboxes:
                if checkboxes[box] == folder:
                    for method_file in worskhop_required_modification_methods:
                        if os.path.exists(os.path.join(mod_path, method_file)):
                            ui.configure_item(box, enabled=False, default_value=False)
                            break


def clean_folders():
    for root, dirs, files in os.walk(mpaths.logs_dir):
        for filename in files:
            open(os.path.join(root, filename), "w").close()

    os.makedirs(mpaths.build_dir, exist_ok=True)
    os.makedirs(mpaths.minify_dota_compile_input_path, exist_ok=True)


def url_dispatcher(url):
    webbrowser.open(url)


def get_blank_file_extensions():
    extensions = []
    for file in os.listdir(mpaths.blank_files_dir):
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
                    ui.configure_item(
                        item,
                        label=localization_data["details_button_label_var"][locale],
                    )


def change_output_path():
    global output_path
    selection = ui.get_value("output_select")
    output_path = [lang for lang in mpaths.minify_dota_possible_language_output_paths if selection in lang][0]


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


def open_thing(path, args=""):
    if path == mpaths.dota2_tools_executable:
        os.makedirs(mpaths.minify_dota_tools_required_path, exist_ok=True)
    try:
        # If args are provided and target is executable, prefer launching directly
        if args:
            if mpaths.OS == "Windows":
                os.startfile(path, arguments=args)
                return
            # POSIX: launch executable directly when possible
            if os.access(path, os.X_OK) and os.path.isfile(path):
                cmd = [path] + shlex.split(args)
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            # Non-executables with args: fall back to opening container directory
            path = os.path.dirname(path) or "."

        # No args path open
        if os.path.isdir(path):
            if mpaths.OS == "Windows":
                os.startfile(path)
            elif mpaths.OS == "Darwin":
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])
        else:
            if mpaths.OS == "Windows":
                os.startfile(path)
            elif mpaths.OS == "Darwin":
                # Reveal the file in Finder to avoid missing-app association errors
                subprocess.run(["open", "-R", path])
            else:
                subprocess.run(["xdg-open", path])
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
                shutil.copytree(
                    os.path.join(folder, item),
                    os.path.join(mpaths.minify_dota_compile_input_path, item),
                )
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

        remove_path(
            mpaths.minify_dota_compile_input_path,
            mpaths.minify_dota_compile_output_path,
        )
        os.makedirs(mpaths.minify_dota_tools_required_path, exist_ok=True)

        add_text_to_terminal(localization_dict["compile_successful_text_var"])
    else:
        add_text_to_terminal(localization_dict["compile_no_path_text_var"])


def select_compile_dir(sender, app_data):
    global compile_path
    compile_path = app_data["current_path"]


def remove_path(*paths):
    "Superset of `shutil.rmtree` to handle permissions and take in list of paths and also delete files."
    try:
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

    except WinError:
        for dir, dirnames, filenames in os.walk(path):
            current_dir_mode = os.stat(dir).st_mode
            os.chmod(dir, current_dir_mode | stat.S_IWUSR)

            for filename in filenames:
                filepath = os.path.join(dir, filename)
                current_file_mode = os.stat(filepath).st_mode
                os.chmod(filepath, current_file_mode | stat.S_IWUSR)
        return remove_path(*paths)


def exec_script(script_path, mod_name, order_name):
    if os.path.exists(script_path):
        module_name = mod_name.replace(" ", "").lower() + f"_{order_name}_script"
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        main_func = getattr(module, "main", None)
        if callable(main_func):
            if order_name != "initial":
                add_text_to_terminal(
                    localization_dict["script_execution_text_var"].format(mod_name, order_name),
                )
            main_func()
            if order_name != "initial":
                add_text_to_terminal(
                    localization_dict["script_success_text_var"].format(mod_name, order_name),
                    None,
                    "success",
                )
        else:
            warnings.append(localization_dict["script_no_main_text_var"].format(mod_name, order_name))
            add_text_to_terminal(
                localization_dict["script_no_main_text_var"].format(mod_name, order_name),
                None,
                "warning",
            )
