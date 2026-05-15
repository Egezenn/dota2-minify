import contextlib
import threading
import time

import dearpygui.dearpygui as dpg
import screeninfo
from core import base, utils

from ui import terminal

gui_lock = False

terminal_window_wrap = base.main_window_width - 10

widths = []
heights = []

social_button_size = (18, 18)

if not base.HEADLESS:
    for monitor in screeninfo.get_monitors():
        widths.append(monitor.width)
        heights.append(monitor.height)


def initiate_conditionals():
    from ui import checkboxes

    setup_system_thread = threading.Thread(target=utils.setup_system)
    load_state_checkboxes_thread = threading.Thread(target=checkboxes.load)
    setup_system_thread.start()
    load_state_checkboxes_thread.start()
    setup_system_thread.join()
    load_state_checkboxes_thread.join()

    with dpg.texture_registry(tag="mod_images_registry", show=False):
        pass

    checkboxes.create()


@utils.ignore_if_headless
def lock_interaction():
    global gui_lock
    gui_lock = True
    dpg.set_viewport_title(f"{base.TITLE} - LOCKED")
    dpg.configure_item("button_patch", enabled=False)
    dpg.configure_item("button_select_mods", enabled=False)
    dpg.configure_item("button_uninstall", enabled=False)
    dpg.configure_item("lang_select", enabled=False)
    dpg.configure_item("output_select", enabled=False)


@utils.ignore_if_headless
def unlock_interaction():
    global gui_lock
    gui_lock = False
    dpg.set_viewport_title(base.TITLE)
    dpg.configure_item("button_patch", enabled=True)
    dpg.configure_item("button_select_mods", enabled=True)
    dpg.configure_item("button_uninstall", enabled=True)
    dpg.configure_item("lang_select", enabled=True)
    dpg.configure_item("output_select", enabled=True)


@contextlib.contextmanager
def interactive_lock():
    lock_interaction()
    try:
        yield
    finally:
        unlock_interaction()


def start_text():
    for i in range(1, 6):
        terminal.add_text(f"&start_text_{i}_var")
    terminal.add_seperator()


persistent_windows = [
    "terminal_window",
    "primary_window",
    "footer",
    "opener",
    "mod_tools",
    "maintenance_tools",
]


def register_persistent_window(tag):
    if tag not in persistent_windows:
        persistent_windows.append(tag)


def close_active_window():
    from ui import modal_shared

    active_window_id = dpg.get_active_window()
    if not active_window_id:
        return

    active_window = dpg.get_item_alias(active_window_id) or active_window_id

    is_modal_active = (
        active_window == "modal_popup"
        or active_window_id == dpg.get_alias_id("modal_popup")
        or active_window in ["modal_text_wrapper", "modal_button_wrapper"]
    )

    if is_modal_active:
        dpg.configure_item("modal_popup", show=False)
        threading.Timer(0.1, modal_shared.show_next_from_queue).start()
    elif active_window not in persistent_windows:
        dpg.configure_item(active_window, show=False)


@utils.ignore_if_headless
def close():
    dpg.stop_dearpygui()
    time.sleep(0.1)  # Fixed proper saving
