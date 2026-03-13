import threading
import time

import dearpygui.dearpygui as ui

modal_queue = []


def show_modal(title, messages, buttons):
    """
    Shows a unified modal popup or queues it if one is already active.
    messages: list of strings
    buttons: list of dicts {"label": str, "callback": func, "user_data": any, "width": int}
    """
    modal_queue.append({"messages": messages, "buttons": buttons})
    if not ui.is_item_shown("modal_popup"):
        _show_next_modal_from_queue()


def _show_next_modal_from_queue():
    if not modal_queue:
        return

    modal_data = modal_queue.pop(0)
    messages = modal_data["messages"]
    buttons = modal_data["buttons"]

    if ui.does_item_exist("modal_text_wrapper"):
        ui.delete_item("modal_text_wrapper", children_only=True)
    if ui.does_item_exist("modal_button_wrapper"):
        ui.delete_item("modal_button_wrapper", children_only=True)

    for msg in messages:
        ui.add_text(msg, parent="modal_text_wrapper", indent=1)

    for btn in buttons:

        def create_wrapped_callback(inner_cb):
            def wrapped_callback(sender, app_data, user_data):
                try:
                    ui.configure_item("modal_popup", show=False)
                    if inner_cb:
                        inner_cb(sender, app_data, user_data)
                except Exception:
                    import traceback

                    traceback.print_exc()

                threading.Timer(0.1, _show_next_modal_from_queue).start()

            return wrapped_callback

        ui.add_button(
            label=btn["label"],
            callback=create_wrapped_callback(btn.get("callback")),
            user_data=btn.get("user_data"),
            width=btn.get("width", 100),
            parent="modal_button_wrapper",
        )

    ui.configure_item("modal_popup", show=True)
    time.sleep(0.1)
    configure_modal_popup()
    time.sleep(0.1)

    from .window import on_primary_window_resize

    on_primary_window_resize()


def configure_modal_popup():
    if not ui.does_item_exist("modal_popup"):
        return

    window_width, window_height = ui.get_item_rect_size("modal_popup")
    ui.configure_item(
        "modal_popup",
        pos=(ui.get_viewport_width() / 2 - window_width / 2, ui.get_viewport_height() / 2 - window_height / 2),
    )

    text_width, text_height = ui.get_item_rect_size("modal_text_wrapper")
    ui.configure_item("modal_text_wrapper", pos=(window_width / 2 - text_width / 2, 20))

    btn_width, btn_height = ui.get_item_rect_size("modal_button_wrapper")
    ui.configure_item("modal_button_wrapper", pos=(window_width / 2 - btn_width / 2, text_height + 40))
