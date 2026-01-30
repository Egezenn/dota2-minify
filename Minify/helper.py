import importlib.util
import os
import re
import shlex
import shutil
import stat
import subprocess
import tarfile
import time
import webbrowser
import zipfile

import dearpygui.dearpygui as ui
import jsonc
import requests

import mpaths

compile_path = ""
details_label_text_var = ""
locale = ""
localization_dict = {}
localizations = []
mod_selection_window_var = ""
output_path = mpaths.get_config("output_path", mpaths.minify_dota_pak_output_path)
workshop_installed = False


def download_file(url, target_path, progress_tag=None):
    """
    Downloads a file from url to target_path using requests.
    Updates the UI progress_tag with "Downloading: X.XX/Y.YY MB" if provided.
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        total_size = int(response.headers.get("content-length", 0))
        block_size = 8192
        downloaded = 0
        last_report_time = 0

        with open(target_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_tag:
                        current_time = time.time()
                        if current_time - last_report_time >= 0.1:
                            downloaded_mb = downloaded / (1024 * 1024)
                            total_size_mb = total_size / (1024 * 1024)
                            if total_size > 0:
                                # TODO: localize texts, use single string for downloads
                                #       "Downloading {}".format(item)
                                #       "Downloading {}".format(progress)
                                ui.set_value(
                                    progress_tag,
                                    f"Downloading: {downloaded_mb:.2f}/{total_size_mb:.2f} MB",
                                )
                            else:
                                ui.set_value(progress_tag, f"Downloading: {downloaded_mb:.2f} MB")
                            last_report_time = current_time
        return True
    except Exception as e:
        add_text_to_terminal(f"Download failed: {e}", type="error")
        return False


def extract_archive(archive_path, extract_dir=".", target_file=None):
    """
    Extracts an archive (zip or tar.gz).
    If target_file is provided, extracts only that file (or directory structure leading to it).
    """
    try:
        if archive_path.endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                if target_file:
                    zip_ref.extract(target_file, path=extract_dir)
                else:
                    zip_ref.extractall(extract_dir)
        elif archive_path.endswith((".tar.gz", ".tgz")):
            with tarfile.open(archive_path, "r:gz") as tar:
                if target_file:
                    member = tar.getmember(target_file)
                    tar.extract(member, path=extract_dir)
                else:
                    tar.extractall(extract_dir)
        else:
            add_text_to_terminal(f"Unsupported archive format: {archive_path}", type="error")
            return False
        return True
    except Exception as e:
        add_text_to_terminal(f"Extraction failed: {e}", type="error")
        return False


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

    ui.add_text(default_value=text, parent="terminal_window", wrap=mpaths.main_window_width - 20, **kwargs)
    scroll_to_terminal_end()


def disable_workshop_mods():
    if not workshop_installed:
        for folder in mpaths.mods_with_order:
            mod_path = os.path.join(mpaths.mods_dir, folder)
            worskhop_required_modification_methods = [
                "styling.css",
                "menu.xml",
                "xml_mod.json",
            ]

            for method_file in worskhop_required_modification_methods:
                if os.path.exists(os.path.join(mod_path, method_file)):
                    ui.configure_item(folder, enabled=False, default_value=False)
                    break


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
    with open(mpaths.localization_file_dir, encoding="utf-8") as file:
        localization_data = jsonc.load(file)
    sub_headers = set()
    for header in localization_data.values():
        if isinstance(header, dict):
            sub_headers.update(header.keys())
    localizations = sorted(list(sub_headers))

    for key, value in localization_data.items():
        if key.endswith("var"):
            localization_dict[key] = value["EN"]


def clean_terminal():
    ui.delete_item("terminal_window", children_only=True)


def close():
    ui.stop_dearpygui()


def parse_markdown_notes(mod_path, locale):
    try:
        notes_md_path = os.path.join(mod_path, "notes.md")
        if os.path.exists(notes_md_path):
            with open(notes_md_path, encoding="utf-8") as file:
                raw_notes = file.read()

            user_locale = locale.upper()
            sections = {}

            parts = re.split(r"<!-- LANG:(\w+) -->", raw_notes)

            if len(parts) > 1:
                for i in range(1, len(parts), 2):
                    lang = parts[i].upper()
                    content = parts[i + 1].strip()
                    sections[lang] = content
            else:
                sections["EN"] = raw_notes.strip()

            return sections.get(user_locale, sections.get("EN", ""))
    except Exception as e:
        print(f"Error parsing notes for {mod_path}: {e}")
    return ""


def render_markdown(parent, text):
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            ui.add_spacer(parent=parent, height=5)
            continue

        ui.add_text(line, parent=parent, wrap=mpaths.main_window_width - 20)


# TODO: also revise this
def change_localization(init=False):
    global locale
    with open(mpaths.localization_file_dir, encoding="utf-8") as localization_file:
        localization_data = jsonc.load(localization_file)
    if init == True:  # gets broken equality check is not there # noqa: E712
        if (locale := mpaths.get_config("locale", ui.get_value("lang_select"))) is not None:
            ui.configure_item("lang_select", default_value=locale)
        else:
            locale = mpaths.set_config("locale", ui.get_value("lang_select"))
        ui.configure_item("lang_select", default_value=locale)

    for key, value in localization_data.items():
        locale = ui.get_value("lang_select")
        if key.endswith("var"):
            if ui.does_item_exist(key):
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
        if ui.does_item_exist(key):
            if not key.endswith("var") and ui.get_item_info(key).get("type") == "mvAppItemType::mvButton":
                if locale in localization_data[key]:
                    ui.configure_item(key, label=value[locale])
                else:  # default to english if the line isn't available on selected locale
                    ui.configure_item(key, label=value["EN"])
            if not key.endswith("var") and ui.get_item_info(key).get("type") == "mvAppItemType::mvText":
                if locale in localization_data[key]:
                    ui.configure_item(key, default_value=value[locale])
                else:
                    ui.configure_item(key, default_value=value["EN"])
            mpaths.set_config("locale", locale)

    for mod in mpaths.visually_available_mods:
        container = f"{mod}_markdown_container"
        if ui.does_item_exist(container):
            mod_path = os.path.join(mpaths.mods_dir, mod)
            text = parse_markdown_notes(mod_path, locale)
            ui.delete_item(container, children_only=True)
            render_markdown(container, text)

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
    mpaths.set_config("output_locale", selection)
    mpaths.set_config("output_path", output_path)


def open_thing(path, args=""):
    try:
        # If args are provided and target is executable, prefer launching directly
        if args:
            if mpaths.OS == mpaths.WIN:
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
            if mpaths.OS == mpaths.WIN:
                os.startfile(path)
            elif mpaths.OS == mpaths.MAC:
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])
        else:
            if mpaths.OS == mpaths.WIN:
                os.startfile(path)
            elif mpaths.OS == mpaths.MAC:
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
        with open(mpaths.log_rescomp, "w") as file:
            command = (
                mpaths.dota_resource_compiler_path,
                "-i",
                mpaths.minify_dota_compile_input_path + "/*",
                "-r",
            )

            if mpaths.OS != mpaths.WIN:
                command.insert(0, "wine")

            subprocess.run(
                stdout=file,
                creationflags=subprocess.CREATE_NO_WINDOW if mpaths.OS == mpaths.WIN else 0,
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


def move_path(src, dst):
    "Superset of `shutil.move`, `os.rename` to handle permissions for moving and renaming."
    try:
        shutil.move(src, dst)
    except PermissionError:
        try:
            paths_to_chmod = []
            if os.path.exists(src):
                paths_to_chmod.append(src)
            if os.path.exists(dst):
                paths_to_chmod.append(dst)

            for path in paths_to_chmod:
                if os.path.isdir(path):
                    for dir, _, filenames in os.walk(path):
                        current_dir_mode = os.stat(dir).st_mode
                        os.chmod(dir, current_dir_mode | stat.S_IWUSR)

                        for filename in filenames:
                            filepath = os.path.join(dir, filename)
                            current_file_mode = os.stat(filepath).st_mode
                            os.chmod(filepath, current_file_mode | stat.S_IWUSR)
                else:
                    current_file_mode = os.stat(path).st_mode
                    os.chmod(path, current_file_mode | stat.S_IWUSR)

            return move_path(src, dst)
        except:
            mpaths.write_warning()
    except FileNotFoundError:
        print(f"Skipped move of: {src} (not found)")


def remove_path(*paths):
    "Superset of `shutil.rmtree` to handle permissions and take in list of paths and also delete files."
    try:
        for path in paths:
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except FileNotFoundError:
                print(f"Skipped deletion of: {path}")

    except PermissionError:
        try:
            for path in paths:
                if os.path.isdir(path):
                    for dir, _, filenames in os.walk(path):
                        current_dir_mode = os.stat(dir).st_mode
                        os.chmod(dir, current_dir_mode | stat.S_IWUSR)

                        for filename in filenames:
                            filepath = os.path.join(dir, filename)
                            current_file_mode = os.stat(filepath).st_mode
                            os.chmod(filepath, current_file_mode | stat.S_IWUSR)
                else:
                    current_file_mode = os.stat(path).st_mode
                    os.chmod(path, current_file_mode | stat.S_IWUSR)

            return remove_path(*paths)
        except:
            mpaths.write_warning()


def exec_script(script_path, mod_name, order_name, _terminal_output=True):
    if os.path.exists(script_path):
        module_name = mod_name.replace(" ", "").lower() + f"_{order_name}_script"
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        main_func = getattr(module, "main", None)
        if callable(main_func):
            if _terminal_output:
                add_text_to_terminal(
                    localization_dict["script_execution_text_var"].format(mod_name, order_name),
                )
            main_func()
            if _terminal_output:
                add_text_to_terminal(
                    localization_dict["script_success_text_var"].format(mod_name, order_name),
                    type="success",
                )
        else:
            mpaths.write_warning(localization_dict["script_no_main_text_var"].format(mod_name, order_name))
            add_text_to_terminal(
                localization_dict["script_no_main_text_var"].format(mod_name, order_name),
                type="warning",
            )
