"Unified modal internals"

import threading
import time
import traceback

import dearpygui.dearpygui as dpg

modal_queue = []

active_width = 500
active_height = 300


def show(title, messages, buttons, width=500, height=300):
    """
    Shows a unified modal popup or queues it if one is already active.
    messages: list of strings
    buttons: list of dicts {"label": str, "callback": func, "user_data": any, "width": int}
    """
    modal_queue.append({"messages": messages, "buttons": buttons, "width": width, "height": height})
    if not dpg.is_item_shown("modal_popup"):
        show_next_from_queue()


def show_progress(messages, width=500, height=300):
    """Shows the modal with a progress bar and status text."""
    global active_width, active_height
    active_width = width
    active_height = height

    if dpg.does_item_exist("modal_text_wrapper"):
        dpg.delete_item("modal_text_wrapper", children_only=True)

    with dpg.child_window(parent="modal_text_wrapper", width=width - 16, height=(height - 80) / 2, border=False):
        for msg in messages:
            dpg.add_text(msg, wrap=width - 40)

    dpg.configure_item("modal_progress_wrapper", show=True)
    dpg.configure_item("modal_button_wrapper", show=False)
    dpg.configure_item("modal_popup", show=True)
    configure()


def set_progress(value, status_text=None):
    """Updates the progress bar value (0.0 to 1.0) and status text."""
    if dpg.does_item_exist("modal_progress"):
        dpg.set_value("modal_progress", value)
    if status_text is not None and dpg.does_item_exist("modal_progress_status"):
        dpg.set_value("modal_progress_status", status_text)


def show_next_from_queue():
    if not modal_queue:
        return

    global active_width, active_height
    modal_data = modal_queue.pop(0)
    messages = modal_data["messages"]
    buttons = modal_data["buttons"]
    width = modal_data.get("width", 500)
    height = modal_data.get("height", 300)

    active_width = width
    active_height = height

    if dpg.does_item_exist("modal_progress_wrapper"):
        dpg.configure_item("modal_progress_wrapper", show=False)

    if dpg.does_item_exist("modal_text_wrapper"):
        dpg.delete_item("modal_text_wrapper", children_only=True)
    if dpg.does_item_exist("modal_button_wrapper"):
        dpg.delete_item("modal_button_wrapper", children_only=True)

    dpg.configure_item("modal_button_wrapper", show=True)

    with dpg.child_window(parent="modal_text_wrapper", width=width - 16, height=height - 80, border=False):
        for msg in messages:
            dpg.add_text(msg, wrap=width - 40)

    for btn in buttons:

        def create_wrapped_callback(inner_cb):
            def wrapped_callback(sender, app_data, user_data):
                try:
                    dpg.configure_item("modal_popup", show=False)
                    if inner_cb:
                        inner_cb(sender, app_data, user_data)
                except Exception:
                    traceback.print_exc()

                threading.Timer(0.1, show_next_from_queue).start()

            return wrapped_callback

        dpg.add_button(
            label=btn["label"],
            callback=create_wrapped_callback(btn.get("callback")),
            user_data=btn.get("user_data"),
            width=btn.get("width", 100),
            parent="modal_button_wrapper",
        )

    dpg.configure_item("modal_popup", show=True)
    time.sleep(0.1)
    configure()
    time.sleep(0.1)

    from ui import window

    window.on_resize()


def configure(width=None, height=None):
    if width is None:
        width = active_width
    if height is None:
        height = active_height

    if not dpg.does_item_exist("modal_popup"):
        return

    dpg.configure_item(
        "modal_popup",
        width=width,
        height=height,
        autosize=False,
        pos=(
            dpg.get_viewport_width() / 2 - width / 2,
            dpg.get_viewport_height() / 2 - height / 2,
        ),
    )

    dpg.configure_item("modal_text_wrapper", pos=[8, 8])

    btn_width, _ = dpg.get_item_rect_size("modal_button_wrapper")
    dpg.configure_item("modal_button_wrapper", pos=(width / 2 - btn_width / 2 - 8, height - 50))
