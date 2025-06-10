import asyncio
import ctypes
import json
import os
import shutil
import stat
import subprocess
import tarfile
import threading
import time
import traceback
import zipfile
import dearpygui.dearpygui as ui
import requests

import helper
import mpaths
import validatefiles

version = None
checkboxes_state = {}
checkboxes = {}
dev_mode_state = -1

try:
    with open(mpaths.version_file_dir, "r") as file:
        version = file.readline()
except:
    version = ""

title = f"Minify {version}" if version else "Minify"


def version_check():
    global version
    if version:
        try:
            response = requests.get(mpaths.version_query)
            if response.status_code == 200:
                if version == response.text:
                    initiate_conditionals()
                else:
                    version = response.text
                    update_popup_show()
        except:  # no connection
            initiate_conditionals()
            version = ""
    else:
        initiate_conditionals()
        version = ""


def initiate_conditionals():
    setup_system_thread = threading.Thread(target=setupSystem)
    load_state_checkboxes_thread = threading.Thread(target=load_state_checkboxes)
    setup_system_thread.start()
    load_state_checkboxes_thread.start()
    setup_system_thread.join()
    load_state_checkboxes_thread.join()
    create_checkboxes()
    setupButtonState()


def update_popup_show():
    ui.configure_item("update_popup", show=True)


def setupSystem():
    os.makedirs("logs", exist_ok=True)
    # TODO do this.. normally
    x = validatefiles.Requirements(checkboxes)
    public_methods = [
        method for method in dir(x) if callable(getattr(x, method)) if not method.startswith("_")
    ]  # private methods start with _
    try:
        if not (
            os.path.exists(mpaths.s2v_executable)
            and os.path.exists(mpaths.s2v_skia_path)
            and os.path.exists(mpaths.s2v_tinyexr_path)
        ):
            helper.add_text_to_terminal(helper.localization_dict["downloading_cli_terminal_text_var"])
            zip_path = mpaths.s2v_latest.split("/")[-1]
            response = requests.get(mpaths.s2v_latest)
            if response.status_code == 200:
                with open(zip_path, "wb") as file:
                    file.write(response.content)
                helper.add_text_to_terminal(f"{helper.localization_dict["downloaded_cli_terminal_text_var"]}{zip_path}")
                shutil.unpack_archive(zip_path, format="zip")
                os.remove(zip_path)
                helper.add_text_to_terminal(f"{helper.localization_dict["extracted_cli_terminal_text_var"]}{zip_path}")
                if mpaths.OS == "Linux" and not os.access(mpaths.s2v_executable, os.X_OK):
                    current_permissions = os.stat(mpaths.s2v_executable).st_mode
                    os.chmod(mpaths.s2v_executable, current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        if not os.path.exists(mpaths.rg_executable):
            helper.add_text_to_terminal(helper.localization_dict["downloading_ripgrep_terminal_text_var"])
            archive_path = mpaths.rg_latest.split("/")[-1]
            archive_name = archive_path[:-4] if archive_path[-4:] == ".zip" else archive_path[:-7]
            archive_extension = archive_path[-4:] if archive_path[-4:] == ".zip" else archive_path[-7:]
            response = requests.get(mpaths.rg_latest)
            if response.status_code == 200:
                with open(archive_path, "wb") as file:
                    file.write(response.content)
                helper.add_text_to_terminal(
                    f"{helper.localization_dict["downloaded_cli_terminal_text_var"]}{archive_path}"
                )
                if archive_extension == ".zip":
                    with zipfile.ZipFile(archive_path, "r") as zip_ref:
                        zip_ref.extract(archive_name + "/" + mpaths.rg_executable)
                else:
                    with tarfile.open(archive_path, "r:gz") as tar:
                        tar.extractall()
                os.rename(os.path.join(archive_name, mpaths.rg_executable), mpaths.rg_executable)
                helper.rmtrees(archive_name)
                os.remove(archive_path)
                helper.add_text_to_terminal(
                    f"{helper.localization_dict["extracted_cli_terminal_text_var"]}{archive_path}"
                )
                if mpaths.OS == "Linux" and not os.access(mpaths.rg_executable, os.X_OK):
                    current_permissions = os.stat(mpaths.s2v_executable).st_mode
                    os.chmod(mpaths.s2v_executable, current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        for method in public_methods:
            getattr(x, method)()
            if x.toggle_flag == True:
                lock_interaction()
                break

    except Exception:
        with open(os.path.join(mpaths.logs_dir, "crashlog.txt"), "w") as file:
            file.write(traceback.format_exc())
            lock_interaction()
            helper.add_text_to_terminal(
                helper.localization_dict["failed_to_start_terminal_text_var"],
                "failed_to_start_text_tag",
                "error",
            )
            helper.add_text_to_terminal(
                helper.localization_dict["check_crashlog_terminal_text_var"],
                "check_logs_text_tag",
                "error",
            )


def load_state_checkboxes():
    global checkboxes_state
    try:
        with open(mpaths.mods_file_dir, "r", encoding="utf-8") as file:
            checkboxes_state = json.load(file)
    except FileNotFoundError:
        pass


def create_checkboxes():
    global checkboxes_state
    for index in range(len(mpaths.mods_folders)):
        name = mpaths.mods_folders[index]
        ui.add_group(parent="mod_menu", tag=f"{name}_group_tag", horizontal=True, width=300)
        ui.add_checkbox(
            parent=f"{name}_group_tag", label=name, tag=name, default_value=False, callback=setupButtonState
        )
        for key in checkboxes_state.keys():
            if key == name:
                if checkboxes_state[name] == None:
                    ui.configure_item(name, default_value=False)
                else:
                    ui.configure_item(name, default_value=checkboxes_state[name])
        mod_path = os.path.join(mpaths.mods_dir, name)
        notes_txt = os.path.join(mod_path, f"notes_{helper.locale.lower()}.txt")
        with open(notes_txt, "r", encoding="utf-8") as file:
            data = file.read()

        data2 = f"{name}_details_window_tag"
        ui.add_button(
            parent=f"{name}_group_tag",
            small=True,
            indent=250,
            tag=f"{name}_button_show_details_tag",
            label=f"{helper.details_label_text_var}",
            callback=show_details,
            user_data=f"{name}_details_window_tag",
        )

        ui.add_window(
            tag=f"{name}_details_window_tag",
            pos=(0, 0),
            show=False,
            width=494,
            height=300,
            no_resize=True,
            no_move=True,
            no_collapse=True,
            label=name,
        )
        ui.add_string_value(parent="details_tags", default_value=data, tag=f"{name}_details_text_value_tag")
        ui.add_text(source=f"{name}_details_text_value_tag", parent=f"{name}_details_window_tag", wrap=480)

        current_box = name
        checkboxes[current_box] = name


def setupButtonState():
    for box in checkboxes:
        if ui.get_value(box) == True:
            ui.configure_item("button_patch", enabled=True)
            break
        else:
            ui.configure_item("button_patch", enabled=False)
    if not helper.workshop_installed:
        helper.disableWorkshopMods(mpaths.mods_dir, mpaths.mods_folders, checkboxes)


def lock_interaction():
    ui.configure_item("button_patch", enabled=False)
    ui.configure_item("button_select_mods", enabled=False)
    ui.configure_item("button_uninstall", enabled=False)


def unlock_interaction():
    ui.configure_item("button_patch", enabled=True)
    ui.configure_item("button_select_mods", enabled=True)
    ui.configure_item("button_uninstall", enabled=True)


def show_details(sender, app_data, user_data):
    ui.configure_item(user_data, show=True)


def focus_window():
    if mpaths.OS == "Windows":
        try:
            hwnd = ctypes.windll.user32.FindWindowW(None, "Minify")
            if hwnd != 0:
                ctypes.windll.user32.ShowWindow(hwnd, 9)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception as error:
            with open(os.path.join(mpaths.logs_dir, "crashlog.txt"), "w") as file:
                file.write(f"Windows focus error: {error}")
    else:
        try:
            subprocess.run(["wmctrl", "-a", "Minify"], check=True)
        except FileNotFoundError:
            with open(os.path.join(mpaths.logs_dir, "crashlog.txt"), "w") as file:
                file.write("wmctrl not installed")
        except subprocess.CalledProcessError as error:
            with open(os.path.join(mpaths.logs_dir, "crashlog.txt"), "w") as file:
                file.write(f"Linux focus error: {error}")


def delete_update_popup(ignore=False):
    if ignore:
        os.remove(mpaths.version_file_dir)
    ui.configure_item("update_popup", show=False)
    ui.delete_item("update_popup")
    initiate_conditionals()


def hide_uninstall_popup():
    ui.configure_item("uninstall_popup", show=False)


def open_github_link_and_close_minify():
    open_github_link()  # TODO updater behavior
    helper.close()


def checkbox_state_save():
    for box in checkboxes:
        checkboxes_state[box] = ui.get_value(box)
        with open(mpaths.mods_file_dir, "w", encoding="utf-8") as file:
            json.dump(checkboxes_state, file, indent=4)


def drag_viewport(sender, app_data, user_data):
    if ui.get_item_alias(ui.get_active_window()) != None and (
        ui.is_item_hovered("primary_window") == True
        or ui.is_item_hovered("terminal_window") == True
        or ui.is_item_hovered("top_bar") == True
        or ui.is_item_hovered("mod_menu") == True
        or ui.get_item_alias(ui.get_active_window()).endswith("details_window_tag") == True
    ):  # Note: If local pos [1] < *Height_of_top_bar is buggy)
        drag_deltas = app_data
        viewport_current_pos = ui.get_viewport_pos()
        new_x_position = viewport_current_pos[0] + drag_deltas[1]
        new_y_position = viewport_current_pos[1] + drag_deltas[2]
        new_y_position = max(new_y_position, 0)  # prevent the viewport to go off the top of the screen
        ui.set_viewport_pos([new_x_position, new_y_position])


def open_mod_menu():
    ui.configure_item("mod_menu", show=True)


def open_discord_link():
    helper.urlDispatcher(mpaths.discord)


def open_github_link():
    helper.urlDispatcher(mpaths.latest_release)


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
    ui.add_text(source="start_text_1_var", parent="terminal_window")
    ui.add_text(source="start_text_2_var", parent="terminal_window")
    ui.add_text(source="start_text_3_var", parent="terminal_window")
    ui.add_text(source="start_text_4_var", parent="terminal_window")
    ui.add_text(source="start_text_5_var", parent="terminal_window")
    ui.add_text(
        default_value="------------------------------------------------------------------",
        parent="terminal_window",
        tag="spacer_start_text_tag",
    )
    helper.scroll_to_terminal_end()


def close_active_window():
    active_window = ui.get_item_alias(ui.get_active_window())
    if active_window not in ["terminal_window", "primary_window", "top_bar", "opener", "tools"]:
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
            ui.add_theme_color(ui.mvThemeCol_CheckMark, (29, 29, 30, 255))
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
    ui.bind_item_theme("mod_menu", mod_menu_theme)
    ui.bind_item_theme("top_bar", top_bar_theme)
    ui.bind_item_theme("update_popup", popup_theme)
    ui.bind_item_theme("uninstall_popup", popup_theme)


def dev_mode():
    global dev_mode_state
    if dev_mode_state == -1:
        ui.configure_viewport(item="main_viewport", resizable=True, height=600)
        ui.configure_viewport(item="primary_window", resizable=True)
        with ui.window(
            label="Path and file opener",
            tag="opener",
            pos=(0, 300),
            width=240,
            height=300,
            no_resize=True,
            no_move=True,
            no_close=True,
            no_collapse=True,
        ):
            ui.add_button(
                label="Path: Dota2 Minify",
                callback=lambda: asyncio.run(helper.open_dir(os.path.join(mpaths.minify_dota_pak_output_path))),
            )
            ui.add_button(
                label="File: Dota2 Minify pak66 VPK",
                callback=lambda: asyncio.run(
                    helper.open_dir(os.path.join(mpaths.minify_dota_pak_output_path, "pak66_dir.vpk"))
                ),
            )
            ui.add_spacer(width=0, height=10)
            ui.add_button(label="Path: Minify", callback=lambda: helper.open_dir(os.getcwd()))
            ui.add_button(label="Path: Logs", callback=lambda: helper.open_dir(os.path.join(mpaths.logs_dir)))
            ui.add_button(
                label="Path: Dota2",
                callback=lambda: asyncio.run(
                    helper.open_dir(os.path.join(mpaths.steam_dir, "steamapps", "common", "dota 2 beta"))
                ),
            )
            ui.add_button(
                label="File: Dota2 pak01 VPK", callback=lambda: asyncio.run(helper.open_dir(mpaths.dota_pak01_path))
            )
            ui.add_button(
                label="File: Dota2 pak01(core) VPK",
                callback=lambda: asyncio.run(helper.open_dir(mpaths.dota_core_pak01_path)),
            )
            ui.add_spacer(width=0, height=10)
            ui.add_button(
                label="Executable: Dota2 Tools",
                callback=lambda: asyncio.run(
                    helper.open_dir(mpaths.dota2_tools_executable, "-addon a -language minify -novid -console")
                ),
            )
            ui.add_text("* Requires steam to be open")
            ui.add_button(
                label="Executable: Dota2",
                callback=lambda: asyncio.run(
                    helper.open_dir(mpaths.dota2_executable, "-language minify -novid -console")
                ),
            )

        with ui.window(
            label="Tools",
            tag="tools",
            pos=(240, 300),
            width=253,
            height=300,
            no_resize=True,
            no_move=True,
            no_close=True,
            no_collapse=True,
        ):
            ui.add_button(label="Select folder to compile", callback=lambda: ui.show_item("compile_file_dialog"))
            ui.add_file_dialog(
                show=False,
                modal=False,
                min_size=(480, 260),
                callback=helper.select_compile_dir,
                tag="compile_file_dialog",
                directory_selector=True,
            )
            ui.add_button(label="Compile files from folder", callback=helper.compile)
            ui.add_spacer(width=0, height=140)
            ui.add_text(
                "* You won't be able use any of these (except opening paths) if you're not on Windows because Source2Viewer's GUI and Dota2 Tools aren't crossplatform.",
                wrap=240,
            )
        dev_mode_state = 1

    elif dev_mode_state == 0:
        ui.configure_viewport(item="main_viewport", resizable=True, height=300)
        ui.configure_item("opener", show=False)
        ui.configure_item("tools", show=False)
        dev_mode_state = 1

    else:
        ui.configure_viewport(item="main_viewport", resizable=True, height=600)
        ui.configure_item("opener", show=True)
        ui.configure_item("tools", show=True)
        dev_mode_state = 0


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
