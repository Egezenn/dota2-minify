import importlib.util
import os
from pathlib import Path
import re
import shlex
import shutil
import stat
import subprocess
import tarfile
import time
import zipfile

import dearpygui.dearpygui as ui
import jsonc
import requests
import vdf
import vpk

import mpaths

compiler_filepicker_path = ""
details_label = ""
locale = ""
localization_dict = {}
localizations = []
mod_selection_window_var = ""
terminal_history = []
output_path = mpaths.get_config("output_path", mpaths.minify_dota_pak_output_path)
workshop_installed = False
workshop_required_methods = ["styling.css", "xml_mod.json", "files_uncompiled"]


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
            with zipfile.ZipFile(archive_path) as zip_ref:
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


def add_text_to_terminal(text_or_id, *args, type: str | None = None, **kwargs):
    if text_or_id.startswith("&"):
        text = localization_dict.get(text_or_id.replace("&", ""), text_or_id)
    else:
        text = text_or_id

    if args:
        text = text.format(*args)

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

    item = ui.add_text(default_value=text, parent="terminal_window", wrap=mpaths.main_window_width - 24, **kwargs)
    terminal_history.append({"id": item, "key": text_or_id.replace("&", ""), "args": args})
    scroll_to_terminal_end()
    return item


def disable_workshop_mods():
    if not workshop_installed:
        for folder in mpaths.mods_with_order:
            mod_path = os.path.join(mpaths.mods_dir, folder)

            for method_path in workshop_required_methods:
                if os.path.exists(os.path.join(mod_path, method_path)):
                    ui.configure_item(folder, enabled=False, default_value=False)
                    break


def get_blank_file_extensions():
    extensions = []
    for file in os.listdir(mpaths.blank_files_dir):
        extensions.append(os.path.splitext(file)[1])
    return extensions


def get_available_localizations():
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
    terminal_history.clear()


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


def render_rich_text(parent, text, font="main_font", base_color=(0, 230, 230), bullet=False):
    """
    Renders text with inline code blocks (wrapped in backticks) in pink.
    Manually handles text wrapping.
    Supports urls (orange), custom font, base color, and bullets.
    """
    if not text:
        return

    avail_width = mpaths.main_window_width - 40

    # Tokenize: Split by backticks
    parts = text.split("`")
    tokens = []

    for i, part in enumerate(parts):
        is_code = i % 2 == 1
        if not part:
            continue

        if is_code:
            tokens.append({"text": part, "type": "code"})
        else:
            words = part.split(" ")
            for j, word in enumerate(words):
                if word:
                    if word.startswith("http://") or word.startswith("https://"):
                        tokens.append({"text": word, "type": "link"})
                    else:
                        tokens.append({"text": word, "type": "normal"})
                if j < len(words) - 1:
                    tokens.append({"text": " ", "type": "normal"})

    # Layout tokens
    lines = []
    current_line = []
    current_line_width = 0

    for token in tokens:
        token_text = token["text"]
        token_width = ui.get_text_size(token_text)[0]

        if font == "large_font":
            token_width *= 1.25

        if token_text == " " and current_line_width == 0:
            continue

        if current_line_width + token_width > avail_width and current_line_width > 0:
            lines.append(current_line)
            current_line = []
            current_line_width = 0

            if token_text == " ":
                continue

        current_line.append(token)
        current_line_width += token_width

    if current_line:
        lines.append(current_line)

    # Render lines
    first_token_rendered = False
    for line_tokens in lines:
        with ui.group(horizontal=True, parent=parent, horizontal_spacing=0):
            for token in line_tokens:
                if token["type"] == "code":
                    color = (255, 105, 180)
                elif token["type"] == "link":
                    color = (255, 165, 0)
                else:
                    color = base_color

                show_bullet = bullet and not first_token_rendered

                text_item = ui.add_text(token["text"], color=color, bullet=show_bullet)
                if font:
                    ui.bind_item_font(text_item, font)

                first_token_rendered = True


def render_markdown(parent, text):
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            ui.add_spacer(parent=parent, height=5)
            continue

        if line.startswith("!!:"):
            content = line[3:].strip()
            render_rich_text(parent, content, font="large_font", base_color=(255, 0, 0))
        elif line.startswith("-"):
            content = line[1:].strip()
            render_rich_text(parent, content, bullet=True)
        else:
            render_rich_text(parent, line)


def change_localization(sender=None, app_data=None, user_data=None, init=False):
    global locale
    with open(mpaths.localization_file_dir, encoding="utf-8") as localization_file:
        localization_data = jsonc.load(localization_file)

    if init == True:  # noqa: E712
        locale = mpaths.get_config("locale", ui.get_value("lang_select"))
        if locale is None:
            locale = mpaths.set_config("locale", ui.get_value("lang_select"))
        ui.configure_item("lang_select", default_value=locale)
    else:
        locale = ui.get_value("lang_select")
        mpaths.set_config("locale", locale)

    for key, values in localization_data.items():
        text = values.get(locale, values.get("EN", ""))
        localization_dict[key] = text

        if ui.does_item_exist(key):
            item_type = ui.get_item_info(key).get("type")
            if item_type in [
                "mvAppItemType::mvText",
                "mvAppItemType::mvInputText",
                "mvAppItemType::mvInputInt",
            ]:
                # For input/text items, set value
                ui.set_value(key, text)
            else:
                # For buttons, menus, etc., set label
                ui.configure_item(key, label=text)

    # Update terminal history
    for item in terminal_history:
        if ui.does_item_exist(item["id"]):
            key_data = localization_data.get(item["key"])
            if key_data:
                new_text = key_data.get(locale, key_data.get("EN", item["key"]))
            else:
                new_text = item["key"]

            if item["args"]:
                try:
                    new_text = new_text.format(*item["args"])
                except Exception:
                    pass  # Keep original text if formatting fails
            ui.set_value(item["id"], new_text)

    # Re-render markdown for available mods
    for mod in mpaths.visually_available_mods:
        container = f"{mod}_markdown_container"
        if ui.does_item_exist(container):
            mod_path = os.path.join(mpaths.mods_dir, mod)
            text = parse_markdown_notes(mod_path, locale)
            ui.delete_item(container, children_only=True)
            render_markdown(container, text)

    # Update dynamic detail buttons
    global details_label, mod_selection_window_var
    details_label = localization_data.get("details_button_label_var", {}).get(
        locale, localization_data["details_button_label_var"]["EN"]
    )
    mod_selection_window_var = localization_data.get("mod_selection_window_var", {}).get(
        locale, localization_data["mod_selection_window_var"]["EN"]
    )

    if ui.does_item_exist("mod_menu"):
        for child_group in ui.get_item_children("mod_menu", 1):
            for item in ui.get_item_children(child_group, 1):
                if ui.get_item_alias(item).endswith("_button_show_details_tag"):
                    ui.configure_item(item, label=details_label)


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
        add_text_to_terminal("&open_dir_fail", path, type="error")


def compile(input_path=None, output_path=None, pak_path=None, sender=None, app_data=None, user_data=None):
    if compiler_filepicker_path:
        input_path = compiler_filepicker_path
        output_path = os.path.join(input_path, os.pardir, "compiled")
        clean_terminal()
    if not output_path:
        output_path = os.path.join(input_path, os.pardir, "compiled")

    img_list = [str(f.relative_to(input_path)) for f in Path(input_path).rglob("*.png") if f.is_file()]

    if input_path:
        add_text_to_terminal("&compile_init", input_path)
        remove_path(mpaths.minify_dota_compile_input_path, output_path)
        os.makedirs(mpaths.minify_dota_compile_input_path)

        with open(os.path.join(input_path, "ref.xml"), "w") as file:
            file.write(create_img_ref_xml(img_list))

        items = os.listdir(input_path)

        for item in items:
            if os.path.isdir(os.path.join(input_path, item)):
                shutil.copytree(
                    os.path.join(input_path, item),
                    os.path.join(mpaths.minify_dota_compile_input_path, item),
                )
            else:
                shutil.copy(os.path.join(input_path, item), mpaths.minify_dota_compile_input_path)

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
                command,
                stdout=file,
                creationflags=subprocess.CREATE_NO_WINDOW if mpaths.OS == mpaths.WIN else 0,
            )

        os.makedirs(mpaths.minify_dota_compile_output_path, exist_ok=True)
        shutil.copytree(os.path.join(mpaths.minify_dota_compile_output_path), output_path)

        remove_path(
            mpaths.minify_dota_compile_input_path,
            mpaths.minify_dota_compile_output_path,
            os.path.join(input_path, "ref.xml"),
            os.path.join(output_path, "ref.vxml_c"),
        )
        os.makedirs(mpaths.minify_dota_tools_required_path, exist_ok=True)

        add_text_to_terminal("&compile_successful", output_path)

        if pak_path:
            vpk_file = vpk.new(output_path)
            vpk_file.save(pak_path)
            add_text_to_terminal("&compile_created_pak", pak_path)
    else:
        add_text_to_terminal("&compile_no_path")


def create_img_ref_xml(img_path_list):
    "Helper function to create reference XMLs for images"
    xml_list = []
    for img_path in img_path_list:
        xml_list.append(f'\t\t\t<Image src="file://{img_path}" />')

    return rf"""<root>
    <Panel class="AddonLoadingRoot">
{"\n".join(xml_list)}
    </Panel>
</root>
"""


def select_compile_dir(sender, app_data):
    global compiler_filepicker_path
    compiler_filepicker_path = app_data["current_path"]


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
                add_text_to_terminal("&script_execution", mod_name, order_name)
            main_func()
            if _terminal_output:
                add_text_to_terminal("&script_success", mod_name, order_name, type="success")
        else:
            mpaths.write_warning("&script_no_main", mod_name, order_name)


def remove_lang_args(arg_string):
    tokens = arg_string.split()
    cleaned = []
    skip_next = False

    for i, token in enumerate(tokens):
        if skip_next:
            skip_next = False
            continue

        if token == "-language":
            if i + 1 < len(tokens) and not tokens[i + 1].startswith(("-", "+")):
                skip_next = True
            continue

        cleaned.append(token)

    return " ".join(cleaned)


def fix_parameters():
    steam_ids = []
    successful_ids = []
    if mpaths.get_config("change_parameters_for_all", True):
        for account in mpaths.get_steam_accounts():
            steam_ids.append(account["id"])
    else:
        steam_ids.append(mpaths.get_config("steam_id"))

    for steam_id in steam_ids:
        with open(
            vdf_path := os.path.join(
                mpaths.get_config("steam_root"), "userdata", steam_id, "config", "localconfig.vdf"
            ),
            encoding="utf-8",
        ) as file:
            add_text_to_terminal("&checking_launch_options")
            data = vdf.load(file)
        locale = mpaths.get_config("output_locale")
        try:
            launch_options = data["UserLocalConfigStore"]["Software"]["Valve"]["Steam"]["apps"][mpaths.STEAM_DOTA_ID][
                "LaunchOptions"
            ]
        except KeyError:
            continue
        if f"-language {locale}" not in launch_options or launch_options.count("-language") >= 2:
            for user in mpaths.get_steam_accounts():
                if steam_id in user:
                    break
            add_text_to_terminal("&discrepancy_launch_options", user["name"], locale)
            open_thing(mpaths.steam_executable_path, "-exitsteam")
            data["UserLocalConfigStore"]["Software"]["Valve"]["Steam"]["apps"][mpaths.STEAM_DOTA_ID][
                "LaunchOptions"
            ] = f"-language {locale} {remove_lang_args(launch_options)}"
        with open(vdf_path, "w", encoding="utf-8") as file:
            vdf.dump(data, file, pretty=True)
        successful_ids.append(steam_id)
    return successful_ids


def create_debug_zip():
    try:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        zip_filename = f"minify_debug_{timestamp}.zip"

        files_to_include = [
            mpaths.main_config_file_dir,
            mpaths.mods_config_dir,
        ]

        if os.path.exists(mpaths.logs_dir):
            for file in os.listdir(mpaths.logs_dir):
                files_to_include.append(os.path.join(mpaths.logs_dir, file))

        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in files_to_include:
                if os.path.exists(file_path):
                    zipf.write(file_path)

        add_text_to_terminal("&heeeeeeeeeeeeeelp", zip_filename)
        open_thing(".")

    except:
        pass
