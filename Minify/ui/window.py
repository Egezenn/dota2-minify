import ctypes
import subprocess

import dearpygui.dearpygui as ui
import helper
from core import base, constants, log

from . import dev_tools, modal_shared

is_moving_viewport = False


def drag_viewport(sender, app_data, user_data):
    global is_moving_viewport

    if is_moving_viewport:
        drag_deltas = app_data
        viewport_current_pos = ui.get_viewport_pos()
        new_x_position = viewport_current_pos[0] + drag_deltas[1]
        new_y_position = viewport_current_pos[1] + drag_deltas[2]
        new_y_position = max(new_y_position, 0)  # prevent the viewport to go off the top of the screen
        ui.set_viewport_pos([new_x_position, new_y_position])
    # TODO: add dev windows conditionally
    elif ui.get_item_alias(ui.get_active_window()) is not None and (
        ui.is_item_hovered("primary_window")
        or ui.is_item_hovered("terminal_window")
        or ui.is_item_hovered("footer")
        or ui.is_item_hovered("mod_menu")
        or ui.is_item_hovered("settings_menu")
        or ui.get_item_alias(ui.get_active_window()).endswith("details_window_tag")
    ):
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


def focus_window():
    if base.OS == base.WIN:
        try:
            hwnd = ctypes.windll.user32.FindWindowW(None, "Minify")
            if hwnd != 0:
                ctypes.windll.user32.ShowWindow(hwnd, 9)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
        except:
            log.write_warning()
    else:
        try:
            subprocess.run(
                ["wmctrl", "-a", "Minify"],
                check=True,
            )
        except:
            pass


def on_primary_window_resize():
    if dev_tools.dev_mode_state != 1:
        dev_tools.prev_width = ui.get_viewport_width()
        dev_tools.prev_height = ui.get_viewport_height()
    # terminal wrap size
    window_width = ui.get_item_width("primary_window")
    window_height = ui.get_item_height("primary_window")
    helper.wrap_size = constants.main_window_width - 20 if dev_tools.dev_mode_state == 1 else window_width - 10

    for item in helper.terminal_history:
        idx = item["id"]
        if ui.does_item_exist(idx):
            ui.configure_item(idx, wrap=helper.wrap_size)

    from .gui import render_details_window, tag_data_for_details_windows

    # details windows resize
    for window_tag in tag_data_for_details_windows:
        if ui.does_item_exist(window_tag):
            ui.configure_item(window_tag, width=window_width, height=window_height)
            if ui.is_item_shown(window_tag):
                mod = window_tag.replace("_details_window_tag", "")
                render_details_window(mod)

    # menus resize
    if ui.does_item_exist("mod_menu"):
        ui.configure_item("mod_menu", width=window_width, height=window_height)

    if ui.does_item_exist("settings_menu"):
        ui.configure_item("settings_menu", width=window_width, height=window_height)

    if ui.is_item_shown("modal_popup"):
        modal_shared.configure_modal_popup()
