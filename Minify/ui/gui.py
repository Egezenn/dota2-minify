import contextlib
import threading
import time

import conditions
import dearpygui.dearpygui as dpg
import screeninfo
from core import base, fs

from ui import checkboxes, modal_shared, terminal

gui_lock = False

terminal_window_wrap = base.main_window_width - 10

widths = []
heights = []

social_button_size = (18, 18)

for monitor in screeninfo.get_monitors():
    widths.append(monitor.width)
    heights.append(monitor.height)


def initiate_conditionals():
    setup_system_thread = threading.Thread(target=setup_system)
    load_state_checkboxes_thread = threading.Thread(target=checkboxes.load)
    setup_system_thread.start()
    load_state_checkboxes_thread.start()
    setup_system_thread.join()
    load_state_checkboxes_thread.join()

    with dpg.texture_registry(tag="mod_images_registry", show=False):
        pass

    checkboxes.create()


def setup_system():
    fs.create_dirs(base.logs_dir)
    conditions.is_dota_running("&error_please_close_dota_terminal", "error")
    conditions.is_compiler_found()
    conditions.resolve_dependencies()


def lock_interaction():
    global gui_lock
    gui_lock = True
    dpg.configure_item("button_patch", enabled=False)
    dpg.configure_item("button_select_mods", enabled=False)
    dpg.configure_item("button_uninstall", enabled=False)
    dpg.configure_item("lang_select", enabled=False)
    dpg.configure_item("output_select", enabled=False)


def unlock_interaction():
    global gui_lock
    gui_lock = False
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


def close_active_window():
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
    elif active_window not in [
        "terminal_window",
        "primary_window",
        "footer",
        "opener",
        "mod_tools",
        "maintenance_tools",
    ]:
        dpg.configure_item(active_window, show=False)


def close():
    dpg.stop_dearpygui()
    time.sleep(0.1)  # Fixed proper saving
