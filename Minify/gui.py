import concurrent.futures
import ctypes
from gc import enable
import os
import re
import shutil
import stat
import subprocess
import threading
import time
import webbrowser

import dearpygui.dearpygui as ui
import jsonc
import psutil
import requests

import build
import helper
import mpaths

checkboxes = []
checkboxes_state = {}
dev_mode_state = -1
gui_lock = False
is_moving_viewport = False
version = None
latest_download_url = None

try:
    with open(mpaths.version_file_dir) as file:
        version = file.readline()
except:
    version = ""

title = f"Minify {version}" if version else "Minify"
spacer = "-" * 75
banner_height = 120


def version_check():
    global version
    global latest_download_url

    if version and mpaths.frozen:
        try:
            api_url = f"https://api.github.com/repos/{mpaths.head_owner}/{mpaths.repo_name}/releases"

            response = requests.get(api_url)
            response.raise_for_status()
            releases = response.json()

            download_url = None
            tag_name = None

            suffix = mpaths.OS.lower() + ".zip"

            if suffix:
                opt_in = mpaths.get_config("opt_into_rcs", False)
                for release in releases:
                    if release["prerelease"] and not re.search(r"rc\d+$", version) and not opt_in:
                        continue  # Show only if the current version is a pre-release
                    for asset in release.get("assets", []):
                        if asset["name"].endswith(suffix):
                            download_url = asset["browser_download_url"]
                            tag_name = release["tag_name"]
                            break
                    if download_url:
                        break
            if download_url and tag_name and version != tag_name[8:]:  # DEPRECATE: bad tag name
                latest_download_url = download_url
                update_popup_show()
        except:
            mpaths.write_warning()


def initiate_conditionals():
    # Updater self-update
    updater = "updater.exe" if mpaths.OS == mpaths.WIN else "updater"
    updater_new = "updater-new.exe" if mpaths.OS == mpaths.WIN else "updater"

    if os.path.exists(updater_new):
        try:
            helper.remove_path(updater)
            helper.move_path(updater_new, updater)
            if mpaths.OS != mpaths.WIN:
                os.chmod(updater, 0o755)
        except:
            mpaths.write_warning()

    setup_system_thread = threading.Thread(target=setup_system)
    load_state_checkboxes_thread = threading.Thread(target=load_checkboxes_state)
    setup_system_thread.start()
    load_state_checkboxes_thread.start()
    setup_system_thread.join()
    load_state_checkboxes_thread.join()

    with ui.texture_registry(tag="mod_images_registry", show=False):
        pass

    create_checkboxes()


def update_popup_show():
    ui.configure_item("update_popup", show=True)


def setup_system():
    os.makedirs("logs", exist_ok=True)
    is_dota_running("error_please_close_dota_terminal", "error")
    is_compiler_found()
    download_dependencies()


def download_dependencies():
    try:
        if not os.path.exists(mpaths.s2v_executable):
            tag = helper.add_text_to_terminal("&downloading_cli_terminal")
            zip_path = mpaths.s2v_latest.split("/")[-1]
            if helper.download_file(mpaths.s2v_latest, zip_path, tag):
                helper.add_text_to_terminal("&downloaded_cli_terminal", zip_path)
                if helper.extract_archive(zip_path, "."):
                    helper.remove_path(zip_path)
                    helper.add_text_to_terminal("&extracted_cli_terminal", zip_path)
                    if mpaths.OS != mpaths.WIN and not os.access(mpaths.s2v_executable, os.X_OK):
                        current_permissions = os.stat(mpaths.s2v_executable).st_mode
                        os.chmod(
                            mpaths.s2v_executable,
                            current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
                        )

        # Prefer system-installed ripgrep when available
        rg_on_path = shutil.which(mpaths.rg_executable)
        if rg_on_path:
            mpaths.rg_executable = rg_on_path
        elif not os.path.exists(mpaths.rg_executable):
            tag = helper.add_text_to_terminal("&downloading_ripgrep_terminal")
            archive_path = mpaths.rg_latest.split("/")[-1]
            archive_name = archive_path[:-4] if archive_path[-4:] == ".zip" else archive_path[:-7]

            if helper.download_file(mpaths.rg_latest, archive_path, tag):
                helper.add_text_to_terminal("&downloaded_cli_terminal", archive_path)

                success = False
                success = helper.extract_archive(archive_path, ".", f"{archive_name}/{mpaths.rg_executable}")

                if success:
                    helper.move_path(
                        os.path.join(archive_name, mpaths.rg_executable),
                        mpaths.rg_executable,
                    )
                    helper.remove_path(archive_path)
                    helper.add_text_to_terminal("&extracted_cli_terminal", archive_path)
                    if mpaths.OS in (mpaths.LINUX, mpaths.MAC) and not os.access(mpaths.rg_executable, os.X_OK):
                        current_permissions = os.stat(mpaths.rg_executable).st_mode
                        os.chmod(
                            mpaths.rg_executable,
                            current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
                        )

    except:
        mpaths.write_crashlog()
        helper.add_text_to_terminal("&failed_download_retrying_terminal", type="error")
        return download_dependencies()


def load_checkboxes_state():
    global checkboxes_state
    try:
        with open(mpaths.mods_config_dir, encoding="utf-8") as file:
            checkboxes_state = jsonc.load(file)
    except FileNotFoundError:
        open(mpaths.mods_config_dir, "w").close()


def save_checkbox_state():
    for box in checkboxes:
        checkboxes_state[box] = ui.get_value(box)
    with open(mpaths.mods_config_dir, "w", encoding="utf-8") as file:
        jsonc.dump(checkboxes_state, file, indent=2)


def create_checkboxes():
    global checkboxes_state

    mod_details_cache = {}

    def scan_mod_details(mod_name):
        mod_p = os.path.join(mpaths.mods_dir, mod_name)
        img_p = os.path.join(mod_p, "preview.png")
        notes_p = os.path.join(mod_p, "notes.md")

        image_data = None
        has_notes = False

        if os.path.exists(img_p):
            try:
                image_data = ui.load_image(img_p)
            except Exception as err:
                print(f"Failed to load image for {mod_name}: {err}")

        if os.path.exists(notes_p) and os.path.getsize(notes_p) > 0:
            has_notes = True

        return mod_name, image_data, has_notes

    mods_to_scan = [m for m in mpaths.visually_available_mods if not m.endswith(".vpk")]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(scan_mod_details, mods_to_scan)
        for m_name, img_data, notes_exist in results:
            mod_details_cache[m_name] = (img_data, notes_exist)

    for mod in mpaths.visually_available_mods:
        mod_path = os.path.join(mpaths.mods_dir, mod)
        if is_vpk := mod.endswith(".vpk"):
            always_val = False
        else:
            mod_cfg_path = os.path.join(mod_path, "modcfg.json")
            always_val = mpaths.read_json_file(mod_cfg_path).get("always", False)

        if always_val:
            enable_ticking = False
            value = True
        else:
            enable_ticking = True
            value = checkboxes_state.get(mod, False)

        ui.add_group(parent="mod_menu", tag=f"{mod}_group_tag", horizontal=True, width=mpaths.main_window_width)
        ui.add_checkbox(
            parent=f"{mod}_group_tag",
            label=mod[:-4] if is_vpk else mod,
            tag=mod,
            callback=setup_button_state,
            default_value=value,
            enabled=enable_ticking,
        )

        if not is_vpk:
            img_data, has_notes = mod_details_cache.get(mod, (None, False))

            if img_data or has_notes:
                tag_data = f"{mod}_details_window_tag"
                ui.add_button(
                    parent=f"{mod}_group_tag",
                    small=True,
                    indent=mpaths.main_window_width - 150,
                    tag=f"{mod}_button_show_details_tag",
                    label=f"{helper.details_label}",
                    callback=show_details,
                    user_data=tag_data,
                )

                ui.add_window(
                    tag=tag_data,
                    pos=(0, 0),
                    show=False,
                    width=mpaths.main_window_width,
                    height=mpaths.main_window_height,
                    no_resize=True,
                    no_move=True,
                    no_collapse=True,
                    label=mod,
                )

                if img_data:
                    try:
                        w, h, _, d = img_data
                        image_tag = f"{mod}_image_texture"
                        ui.add_static_texture(
                            width=w, height=h, default_value=d, tag=image_tag, parent="mod_images_registry"
                        )

                        avail_width = mpaths.main_window_width - 40
                        max_height = mpaths.main_window_height - 50 - 20

                        aspect_ratio = w / h

                        display_w = avail_width
                        display_h = display_w / aspect_ratio

                        if display_h > max_height:
                            display_h = max_height
                            display_w = display_h * aspect_ratio

                        scale = min(1.0, avail_width / w, max_height / h)
                        display_w = int(w * scale)
                        display_h = int(h * scale)

                        ui.add_image(image_tag, width=display_w, height=display_h, parent=tag_data)
                        ui.add_separator(parent=tag_data)
                    except Exception as e:
                        print(f"Failed to display image for {mod}: {e}")

                container = f"{mod}_markdown_container"
                with ui.group(parent=tag_data, tag=container):
                    pass

                text = helper.parse_markdown_notes(mod_path, helper.locale)
                helper.render_markdown(container, text)

        checkboxes.append(mod)


def setup_button_state():
    for box in checkboxes_state:
        if box in checkboxes and ui.get_value(box):
            ui.configure_item("button_patch", enabled=True)
            break
        else:
            ui.configure_item("button_patch", enabled=False)
    save_checkbox_state()


def lock_interaction():
    global gui_lock
    gui_lock = True
    ui.configure_item("button_patch", enabled=False)
    ui.configure_item("button_select_mods", enabled=False)
    ui.configure_item("button_uninstall", enabled=False)
    ui.configure_item("lang_select", enabled=False)
    ui.configure_item("output_select", enabled=False)


def unlock_interaction():
    global gui_lock
    gui_lock = False
    ui.configure_item("button_patch", enabled=True)
    ui.configure_item("button_select_mods", enabled=True)
    ui.configure_item("button_uninstall", enabled=True)
    ui.configure_item("lang_select", enabled=True)
    ui.configure_item("output_select", enabled=True)


def show_details(sender, app_data, user_data):
    ui.configure_item(user_data, show=True)


def focus_window():
    if mpaths.OS == mpaths.WIN:
        try:
            hwnd = ctypes.windll.user32.FindWindowW(None, "Minify")
            if hwnd != 0:
                ctypes.windll.user32.ShowWindow(hwnd, 9)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
        except:
            mpaths.write_warning()
    else:
        try:
            subprocess.run(
                ["wmctrl", "-a", "Minify"],
                check=True,
            )
        except:
            pass


def delete_update_popup(ignore):
    if ignore:
        helper.remove_path(mpaths.version_file_dir)
    ui.configure_item("update_popup", show=False)
    ui.delete_item("update_popup")


def hide_uninstall_popup():
    ui.configure_item("uninstall_popup", show=False)


def update():
    def threaded_update():
        try:
            global latest_download_url
            download_url = latest_download_url

            if download_url:
                tag = helper.add_text_to_terminal("Downloading update...")

                target_zip = "update.zip"
                helper.remove_path(target_zip)

                if not helper.download_file(download_url, target_zip, tag):
                    webbrowser.open(mpaths.github_latest)
                    helper.close()
                    return

                helper.add_text_to_terminal("Download complete. Launching updater...")

                if mpaths.OS == mpaths.WIN:
                    cmd = ["updater.exe", target_zip]
                    subprocess.Popen(
                        cmd,
                        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                        close_fds=True,
                    )
                else:
                    cmd = ["./updater", target_zip]
                    current_permissions = os.stat(cmd[0]).st_mode
                    os.chmod(
                        cmd[0],
                        current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
                    )
                    subprocess.Popen(cmd, start_new_session=True, close_fds=True)

                helper.close()
                return

        except Exception as e:
            print(f"Update failed: {e}")
            webbrowser.open(mpaths.github_latest)
            helper.close()

    delete_update_popup(ignore=False)

    t = threading.Thread(target=threaded_update)
    t.start()


def drag_viewport(sender, app_data, user_data):
    global is_moving_viewport

    if is_moving_viewport:
        drag_deltas = app_data
        viewport_current_pos = ui.get_viewport_pos()
        new_x_position = viewport_current_pos[0] + drag_deltas[1]
        new_y_position = viewport_current_pos[1] + drag_deltas[2]
        new_y_position = max(new_y_position, 0)  # prevent the viewport to go off the top of the screen
        ui.set_viewport_pos([new_x_position, new_y_position])
    elif ui.get_item_alias(ui.get_active_window()) is not None and (
        ui.is_item_hovered("primary_window")
        or ui.is_item_hovered("terminal_window")
        or ui.is_item_hovered("top_bar")
        or ui.is_item_hovered("mod_menu")
        or ui.is_item_hovered("settings_menu")
        or ui.get_item_alias(ui.get_active_window()).endswith("details_window_tag")
    ):  # Note: If local pos [1] < *Height_of_top_bar is buggy)
        is_moving_viewport = True
        drag_deltas = app_data
        viewport_current_pos = ui.get_viewport_pos()
        new_x_position = viewport_current_pos[0] + drag_deltas[1]
        new_y_position = viewport_current_pos[1] + drag_deltas[2]
        new_y_position = max(new_y_position, 0)  # prevent the viewport to go off the top of the screen
        ui.set_viewport_pos([new_x_position, new_y_position])


def stop_drag_viewport():
    global is_moving_viewport
    is_moving_viewport = False


def open_mod_menu():
    ui.configure_item("mod_menu", show=True)


def open_settings_menu():
    ui.configure_item("settings_menu", show=True)


settings_config = [
    {
        "key": "steam_root",
        "text": "Steam Root",
        "default": "",
        "type": "inputbox",
    },
    {
        "key": "steam_library",
        "text": "Steam Library",
        "default": "",
        "type": "inputbox",
    },
    {
        "key": "output_path",
        "text": "Output Path",
        "default": "",
        "type": "inputbox",
    },
    {
        "key": "steam_id",
        "text": "Steam ID",
        "default": "",
        "type": "combo",
        "items_getter": mpaths.get_steam_accounts,
    },
    {
        "key": "opt_into_rcs",
        "text": "Opt into RCs",
        "default": False,
        "type": "checkbox",
    },
    {
        "key": "fix_parameters",
        "text": "Handle language parameter (current ID)",
        "default": True,
        "type": "checkbox",
    },
    {
        "key": "change_parameters_for_all",
        "text": "Change language parameter for all IDs",
        "default": True,
        "type": "checkbox",
    },
    {
        "key": "launch_dota_after_patch",
        "text": "Launch Dota2 after patching",
        "default": False,
        "type": "checkbox",
    },
    {
        "key": "kill_self_after_patch",
        "text": "Close Minify after patching",
        "default": False,
        "type": "checkbox",
    },
]


def save_settings():
    for opt in settings_config:
        val = ui.get_value(f"opt_{opt["key"]}")
        if opt["key"] == "steam_id" and val:
            val = val.split(" - ")[0]
        mpaths.set_config(opt["key"], val)


def refresh_settings():
    for opt in settings_config:
        if opt["type"] == "combo" and "items_getter" in opt:
            raw_items = opt["items_getter"]()
            if raw_items and isinstance(raw_items[0], dict):
                items = [f"{item['id']} - {item['name']}" for item in raw_items]
            else:
                items = raw_items
            ui.configure_item(f"opt_{opt["key"]}", items=items)

        val = mpaths.get_config(opt["key"], opt["default"])

        if opt["type"] == "combo" and val:
            current_items = ui.get_item_configuration(f"opt_{opt["key"]}")["items"]
            for item in current_items:
                if item.startswith(f"{val} - "):
                    val = item
                    break

        ui.set_value(f"opt_{opt["key"]}", val)


def uninstall_popup_show():
    ui.configure_item("uninstall_popup", show=True)
    time.sleep(0.05)
    configure_uninstall_popup()


def configure_uninstall_popup():
    ui.configure_item(
        "uninstall_popup",
        pos=(
            ui.get_viewport_width() / 2 - ui.get_item_rect_size("uninstall_popup")[0] / 2,
            ui.get_viewport_height() / 2 - ui.get_item_rect_size("uninstall_popup")[1] / 2,
        ),
    )
    ui.configure_item(
        "uninstall_popup_text_wrapper",
        pos=(
            ui.get_item_rect_size("uninstall_popup")[0] / 2
            - ui.get_item_rect_size("uninstall_popup_text_wrapper")[0] / 2,
            ui.get_item_rect_size("uninstall_popup")[1] / 2
            - ui.get_item_rect_size("uninstall_popup_text_wrapper")[1] / 2
            - 20,
        ),
    )
    ui.configure_item(
        "uninstall_popup_button_wrapper",
        pos=(
            ui.get_item_rect_size("uninstall_popup")[0] / 2
            - ui.get_item_rect_size("uninstall_popup_button_wrapper")[0] / 2,
            ui.get_item_rect_size("uninstall_popup")[1] / 2
            - ui.get_item_rect_size("uninstall_popup_button_wrapper")[1] / 2
            + 10,
        ),
    )


def start_text():
    helper.add_text_to_terminal("&start_text_1_var")
    helper.add_text_to_terminal("&start_text_2_var")
    helper.add_text_to_terminal("&start_text_3_var")
    helper.add_text_to_terminal("&start_text_4_var")
    helper.add_text_to_terminal("&start_text_5_var")
    helper.add_text_to_terminal(spacer)


def close_active_window():
    active_window = ui.get_item_alias(ui.get_active_window())
    if active_window not in [
        "terminal_window",
        "primary_window",
        "top_bar",
        "opener",
        "mod_tools",
        "maintenance_tools",
    ]:
        if active_window == "update_popup":
            delete_update_popup()
        else:
            ui.configure_item(active_window, show=False)


def theme():
    with ui.theme() as global_theme:
        with ui.theme_component(ui.mvAll):
            ui.add_theme_style(ui.mvStyleVar_WindowPadding, x=12, y=4)
            ui.add_theme_color(ui.mvThemeCol_Text, (0, 230, 230))
            ui.add_theme_color(ui.mvThemeCol_WindowBg, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_ChildBg, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_ScrollbarBg, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_ScrollbarGrab, (0, 200, 200))
            ui.add_theme_color(ui.mvThemeCol_ScrollbarGrabHovered, (0, 170, 170))
            ui.add_theme_color(ui.mvThemeCol_ScrollbarGrabActive, (0, 120, 120))
            ui.add_theme_color(ui.mvThemeCol_TitleBg, (35, 35, 35, 255))
            ui.add_theme_color(ui.mvThemeCol_TitleBgActive, (35, 35, 35, 255))
            ui.add_theme_color(ui.mvThemeCol_Header, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_HeaderHovered, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_HeaderActive, (17, 17, 18, 255))

    ui.bind_theme(global_theme)

    with ui.theme() as main_buttons_theme:
        with ui.theme_component():
            ui.add_theme_color(ui.mvThemeCol_Button, (0, 230, 230, 6))
            ui.add_theme_color(ui.mvThemeCol_ButtonHovered, (17, 17, 18, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonActive, (15, 15, 15, 255))
            ui.add_theme_style(ui.mvStyleVar_ButtonTextAlign, x=0, y=0.5)
        with ui.theme_component(enabled_state=False):
            ui.add_theme_color(ui.mvThemeCol_Text, (0, 100, 100))
            ui.add_theme_color(ui.mvThemeCol_Button, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonHovered, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonActive, (29, 29, 30, 255))
            ui.add_theme_style(ui.mvStyleVar_ButtonTextAlign, x=0, y=0.5)

    with ui.theme() as close_button_theme:
        with ui.theme_component():
            ui.add_theme_color(ui.mvThemeCol_Text, (0, 230, 230))
            ui.add_theme_color(ui.mvThemeCol_Button, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonHovered, (17, 17, 18, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonActive, (15, 15, 15, 255))
        with ui.theme_component(enabled_state=False):
            ui.add_theme_color(ui.mvThemeCol_Text, (0, 100, 100))
            ui.add_theme_color(ui.mvThemeCol_Button, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonHovered, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonActive, (29, 29, 30, 255))

    with ui.theme() as mod_menu_theme:
        with ui.theme_component():
            ui.add_theme_color(ui.mvThemeCol_FrameBg, (24, 24, 24, 255))
            ui.add_theme_color(ui.mvThemeCol_CheckMark, (0, 230, 230, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgHovered, (20, 20, 20, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgActive, (20, 20, 20, 255))
        with ui.theme_component(ui.mvCheckbox, enabled_state=False):
            ui.add_theme_color(ui.mvThemeCol_Text, (0, 100, 100))
            ui.add_theme_color(ui.mvThemeCol_FrameBg, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgHovered, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgActive, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_CheckMark, (0, 70, 70, 255))
        with ui.theme_component():
            ui.add_theme_color(ui.mvThemeCol_Text, (0, 230, 230))
            ui.add_theme_color(ui.mvThemeCol_Button, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonHovered, (17, 17, 18, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonActive, (29, 29, 30, 255))
        with ui.theme_component(enabled_state=False):
            ui.add_theme_color(ui.mvThemeCol_Button, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_Text, (0, 100, 100))
            ui.add_theme_color(ui.mvThemeCol_ButtonHovered, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonActive, (29, 29, 30, 255))

    with ui.theme() as top_bar_theme:
        with ui.theme_component():
            ui.add_theme_color(ui.mvThemeCol_Text, (0, 230, 230))
            ui.add_theme_color(ui.mvThemeCol_Button, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonHovered, (17, 17, 18, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonActive, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBg, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgHovered, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgActive, (29, 29, 30, 255))
        with ui.theme_component(enabled_state=False):
            ui.add_theme_color(ui.mvThemeCol_Button, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_Text, (0, 100, 100))
            ui.add_theme_color(ui.mvThemeCol_ButtonHovered, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonActive, (29, 29, 30, 255))
        with ui.theme_component(ui.mvCheckbox):
            ui.add_theme_color(ui.mvThemeCol_FrameBg, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgHovered, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgActive, (29, 29, 30, 255))

    with ui.theme() as popup_theme:
        with ui.theme_component():
            ui.add_theme_color(ui.mvThemeCol_Text, (0, 230, 230))
            ui.add_theme_color(ui.mvThemeCol_Button, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonHovered, (17, 17, 18, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonActive, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBg, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgHovered, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgActive, (29, 29, 30, 255))

    ui.bind_item_theme("button_patch", main_buttons_theme)
    ui.bind_item_theme("button_select_mods", main_buttons_theme)
    ui.bind_item_theme("button_uninstall", main_buttons_theme)
    ui.bind_item_theme("button_exit", close_button_theme)
    ui.bind_item_theme("button_minimize", close_button_theme)
    ui.bind_item_theme("mod_menu", mod_menu_theme)
    ui.bind_item_theme("top_bar", top_bar_theme)
    ui.bind_item_theme("update_popup", popup_theme)
    ui.bind_item_theme("uninstall_popup", popup_theme)


def dev_mode():
    global dev_mode_state
    height_increase = 400
    tools_height = 220
    if not mpaths.frozen:
        debug_env = mpaths.get_config("debug_env", False)

    if dev_mode_state == -1:  # init
        dev_mode_state = 1
        ui.configure_viewport(
            item="main_viewport",
            resizable=False,
            width=mpaths.main_window_width,
            height=mpaths.main_window_height + height_increase,
        )
        ui.configure_viewport(item="primary_window", resizable=False)
        with ui.window(
            label="Path & File Opener",
            tag="opener",
            pos=(0, mpaths.main_window_height),
            width=mpaths.main_window_width // 2,
            height=height_increase,
            no_resize=True,
            no_move=True,
            no_close=True,
            no_collapse=True,
        ):
            ui.add_button(
                label="Path: Compile output path",
                callback=lambda: helper.open_thing(os.path.join(helper.output_path)),
            )
            ui.add_button(
                label="File: Compiled pak66 VPK",
                callback=lambda: helper.open_thing(os.path.join(helper.output_path, "pak66_dir.vpk")),
            )
            ui.add_spacer(width=0, height=5)
            ui.add_button(
                label="Path: Minify root",
                callback=lambda: helper.open_thing(os.getcwd()),
            )
            ui.add_button(
                label="Path: Logs",
                callback=lambda: helper.open_thing(mpaths.logs_dir),
            )
            ui.add_button(
                label="Path: Config",
                callback=lambda: helper.open_thing(mpaths.config_dir),
            )
            ui.add_button(
                label="Path: Mods",
                callback=lambda: helper.open_thing(mpaths.mods_dir),
            )
            ui.add_spacer(width=0, height=5)
            ui.add_button(
                label="Path: Dota2",
                callback=lambda: helper.open_thing(
                    os.path.join(mpaths.steam_library, "steamapps", "common", "dota 2 beta")
                ),
            )
            ui.add_button(
                label="File: Dota2 pak01 VPK",
                callback=lambda: helper.open_thing(mpaths.dota_game_pak_path),
            )
            ui.add_button(
                label="File: Dota2 pak01(core) VPK",
                callback=lambda: helper.open_thing(mpaths.dota_core_pak_path),
            )
            ui.add_spacer(width=0, height=5)
            ui.add_button(
                label="Executable: Dota2 Tools",
                callback=lambda: helper.open_thing(
                    mpaths.dota2_tools_executable,
                    f"-addon a -language {mpaths.get_config("output_locale")} -novid -console",
                ),
            )
            ui.add_text("^ Requires steam to be open")
            ui.add_button(
                label="Executable: Dota2",
                callback=lambda: helper.open_thing(
                    mpaths.dota2_executable, f"-language {mpaths.get_config("output_locale")} -novid -console"
                ),
            )
            ui.add_button(label="Create debug zip", callback=helper.create_debug_zip)

        with ui.window(
            label="Mod Tools",
            tag="mod_tools",
            pos=(mpaths.main_window_width // 2, mpaths.main_window_height),
            width=mpaths.main_window_width // 2,
            height=tools_height,
            no_resize=True,
            no_move=True,
            no_close=True,
            no_collapse=True,
        ):
            ui.add_button(
                label="Select path to compile",
                callback=lambda: ui.show_item("compile_file_dialog"),
            )
            ui.add_file_dialog(
                show=False,
                modal=False,
                min_size=(480, 260),
                callback=helper.select_compile_dir,
                tag="compile_file_dialog",
                directory_selector=True,
            )
            ui.add_button(
                label="Compile items from path",
                callback=lambda: helper.compile(
                    input_path=os.path.join(mpaths.config_dir, "custom"),
                    output_path=os.path.join(mpaths.config_dir, "compiled"),
                ),
            )
            ui.add_spacer(width=0, height=5)
            ui.add_button(label="Create a blank mod", callback=build.create_blank_mod)
            ui.add_spacer(width=0, height=5)
            ui.add_button(label="Patch with seperate paks", callback=build.patch_seperate)
            ui.add_spacer(width=0, height=5)
            ui.add_button(label="Untick all mods", callback=lambda: tick_batch(False))
            ui.add_button(label="Tick all mods", callback=lambda: tick_batch(True))

        with ui.window(
            label="Maintenance Tools",
            tag="maintenance_tools",
            pos=(mpaths.main_window_width // 2, mpaths.main_window_height + tools_height),
            width=mpaths.main_window_width // 2,
            height=height_increase - tools_height,
            no_resize=True,
            no_move=True,
            no_close=True,
            no_collapse=True,
        ):
            ui.add_button(label="Wipe language paths", callback=build.wipe_lang_dirs)
            ui.add_spacer(width=0, height=5)
            ui.add_button(label="Extract workshop tools", callback=extract_workshop_tools)
            ui.add_spacer(width=0, height=5)
            ui.add_button(
                label="Launch Steam", callback=lambda: helper.open_thing(mpaths.steam_executable_path, "-silent")
            )
            ui.add_button(
                label="Kill Steam", callback=lambda: helper.open_thing(mpaths.steam_executable_path, "-exitsteam")
            )
            ui.add_button(
                label="Validate Dota2", callback=lambda: webbrowser.open(f"steam://validate/{mpaths.STEAM_DOTA_ID}")
            )

        if not mpaths.frozen and debug_env:
            with ui.window(
                label="Debug tools",
                tag="debug_tools",
                pos=(0, mpaths.main_window_height + height_increase),
                width=mpaths.main_window_width,
                height=300,
                no_resize=True,
                no_move=True,
                no_close=True,
                no_collapse=True,
            ):
                ui.add_button(label="debug", callback=ui.show_debug)
                ui.add_button(label="item_registry", callback=ui.show_item_registry)
                ui.add_button(label="metrics", callback=ui.show_metrics)
                ui.add_button(label="style_editor", callback=ui.show_style_editor)
                ui.add_button(label="font_manager", callback=ui.show_font_manager)

    elif dev_mode_state == 0:  # open
        dev_mode_state = 1
        ui.configure_viewport(
            item="main_viewport",
            resizable=False,
            width=mpaths.main_window_width,
            height=mpaths.main_window_height + height_increase,
        )
        ui.configure_item("opener", show=True)
        ui.configure_item("mod_tools", show=True)
        ui.configure_item("maintenance_tools", show=True)
        if not mpaths.frozen and debug_env:
            ui.configure_item("debug_tools", show=True)

    else:  # close
        dev_mode_state = 0
        ui.configure_viewport(
            item="main_viewport",
            resizable=False,
            width=mpaths.main_window_width,
            height=mpaths.main_window_height,
        )
        ui.configure_item("opener", show=False)
        ui.configure_item("mod_tools", show=False)
        ui.configure_item("maintenance_tools", show=False)
        if not mpaths.frozen and debug_env:
            ui.configure_item("debug_tools", show=False)


def configure_update_popup():
    ui.configure_item(
        "update_popup",
        pos=(
            ui.get_viewport_width() / 2 - ui.get_item_rect_size("update_popup")[0] / 2,
            ui.get_viewport_height() / 2 - ui.get_item_rect_size("update_popup")[1] / 2,
        ),
    )
    ui.configure_item(
        "popup_text_wraper_1",
        pos=(
            ui.get_item_rect_size("update_popup")[0] / 2 - ui.get_item_rect_size("popup_text_wraper_1")[0] / 2,
            ui.get_item_rect_size("update_popup")[1] / 2 - ui.get_item_rect_size("popup_text_wraper_1")[1] / 2 - 30,
        ),
    )
    ui.configure_item(
        "popup_text_wraper_2",
        pos=(
            ui.get_item_rect_size("update_popup")[0] / 2 - ui.get_item_rect_size("popup_text_wraper_2")[0] / 2,
            ui.get_item_rect_size("update_popup")[1] / 2 - ui.get_item_rect_size("popup_text_wraper_2")[1] / 2 - 8,
        ),
    )
    ui.configure_item(
        "update_popup_button_group",
        pos=(
            ui.get_item_rect_size("update_popup")[0] / 2 - ui.get_item_rect_size("update_popup_button_group")[0] / 2,
            ui.get_item_rect_size("update_popup")[1] / 2
            - ui.get_item_rect_size("update_popup_button_group")[1] / 2
            + 26,
        ),
    )


def is_dota_running(text_tag, text_type):
    target = "dota2.exe" if mpaths.OS == mpaths.WIN else "dota2"
    running = any(p.info.get("name") == target for p in psutil.process_iter(attrs=["name"]))

    if running:
        helper.add_text_to_terminal(text_tag, type=text_type)
    return running


def is_compiler_found():
    if not os.path.exists(mpaths.dota_resource_compiler_path):
        helper.workshop_installed = False
        helper.add_text_to_terminal("&error_no_workshop_tools_found_terminal", type="warning")
    else:
        helper.workshop_installed = True


def recalc_rescomp_dirs():
    if mpaths.rescomp_override:
        mpaths.minify_dota_compile_input_path = os.path.join(
            mpaths.rescomp_override_dir, "content", "dota_addons", "minify"
        )
        mpaths.minify_dota_compile_output_path = os.path.join(
            mpaths.rescomp_override_dir, "game", "dota_addons", "minify"
        )
        mpaths.dota_resource_compiler_path = os.path.join(
            mpaths.rescomp_override_dir, "game", "bin", "win64", "resourcecompiler.exe"
        )


def extract_workshop_tools():
    helper.clean_terminal()
    helper.remove_path(mpaths.rescomp_override_dir)
    fails = 0

    for i, path in enumerate(mpaths.dota_tools_paths):
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.copytree(path, mpaths.dota_tools_extraction_paths[i])
            else:
                shutil.copy(path, mpaths.dota_tools_extraction_paths[i])

        else:
            helper.add_text_to_terminal("&extraction_of_failed", path)
            fails += 1

    if not fails:
        recalc_rescomp_dirs()
        if os.path.exists(mpaths.dota_resource_compiler_path):
            helper.add_text_to_terminal("&extracted")
        else:
            helper.add_text_to_terminal("&extraction_of_failed", path)


def bulk_exec_script(order_name, terminal_output=True):
    bulk_name = f"script_{order_name}.py"
    for root, _, files in os.walk(mpaths.mods_dir):
        if bulk_name in files and not os.path.basename(root).startswith("_"):
            mod_cfg_path = os.path.join(root, "modcfg.json")
            cfg = mpaths.read_json_file(mod_cfg_path)
            always = cfg.get("always", False)
            visual = cfg.get("visual", True)

            # TODO: pull the file from pak66 to check if it was enabled for uninstallers
            if always or order_name in ["initial", "uninstall"] or (visual and ui.get_value(os.path.basename(root))):
                helper.exec_script(
                    os.path.join(root, bulk_name), os.path.basename(root), order_name, _terminal_output=terminal_output
                )


def tick_batch(state: bool):
    for box in checkboxes:
        box_cfg = ui.get_item_configuration(box)
        if box_cfg["enabled"]:
            ui.set_value(box, state)
    save_checkbox_state()
    setup_button_state()
