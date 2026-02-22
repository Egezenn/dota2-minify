import os
from re import U
import sys
import threading
import time
from tkinter import EventType
import webbrowser

# Ensure root directories
if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(os.path.realpath(sys.executable)))
else:
    os.chdir(current_dir := os.path.dirname(os.path.abspath(__file__)))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

import dearpygui.dearpygui as ui

import build
import gui
import helper
import mpaths


ui.create_context()


def patcher_start():
    checkbox_state_save_thread = threading.Thread(target=gui.save_checkbox_state)
    checkbox_state_save_thread.start()
    checkbox_state_save_thread.join()
    patch_thread = threading.Thread(target=build.patcher)
    patch_thread.start()
    patch_thread.join()


def create_ui():
    button_size_x, button_size_y = gui.social_button_size
    with ui.window(tag="primary_window"):
        ui.set_primary_window("primary_window", True)
        ui.add_child_window(
            tag="top_bar",
            no_scrollbar=True,
            no_scroll_with_mouse=True,
            auto_resize_y=True,
            autosize_x=True,
        )
        ui.add_group(tag="top_bar_main_group", parent="top_bar", horizontal=True, horizontal_spacing=0)
        ui.add_group(tag="top_bar_left_group", parent="top_bar_main_group", horizontal=True, horizontal_spacing=0)
        ui.add_combo(
            parent="top_bar_left_group",
            tag="lang_select",
            items=(helper.localizations),
            default_value="EN",
            callback=helper.change_localization,
            fit_width=True,
        )
        ui.add_image_button(
            "discord_texture_tag",
            tag="button_discord",
            parent="top_bar_left_group",
            width=button_size_x,
            height=button_size_y,
            callback=lambda: webbrowser.open(mpaths.discord),
        )
        ui.add_image_button(
            "telegram_texture_tag",
            tag="button_telegram",
            parent="top_bar_left_group",
            width=button_size_x,
            height=button_size_y,
            callback=lambda: webbrowser.open(mpaths.telegram),
        )
        ui.add_image_button(
            "git_texture_tag",
            tag="button_git",
            parent="top_bar_left_group",
            width=button_size_x,
            height=button_size_y,
            callback=lambda: webbrowser.open(mpaths.github),
        )
        ui.add_image_button(
            "settings_texture_tag",
            tag="button_settings",
            parent="top_bar_left_group",
            width=button_size_x,
            height=button_size_y,
            callback=gui.open_settings_menu,
        )
        ui.add_image_button(
            "dev_texture_tag",
            tag="button_dev",
            parent="top_bar_left_group",
            width=button_size_x,
            height=button_size_y,
            callback=gui.dev_mode,
        )
        ui.add_text(tag="language_select", parent="top_bar_left_group")
        ui.add_combo(
            parent="top_bar_left_group",
            tag="output_select",
            items=(mpaths.minify_output_list),
            default_value=mpaths.get_config("output_locale", "minify"),
            callback=helper.change_output_path,
            fit_width=True,
        )
        ui.add_group(tag="top_bar_right_group", parent="top_bar_main_group", horizontal=True, horizontal_spacing=0)
        ui.add_button(
            parent="top_bar_right_group",
            tag="button_minimize",
            label="-",
            callback=lambda: ui.minimize_viewport(),
        )
        ui.add_button(
            parent="top_bar_right_group",
            tag="button_maximize",
            label="M",
            # callback=gui.maximize,
        )
        ui.add_button(
            parent="top_bar_right_group",
            tag="button_exit",
            callback=helper.close,
        )

        with ui.group(tag="center_group", horizontal=True):
            ui.group(tag="text_group", xoffset=50)
            ui.add_text(
                default_value=r""" __    __    __    __   __    __    ______  __  __
/\ "-./  \  /\ \  /\ "-.\ \  /\ \  /\  ___\/\ \_\ \  
\ \ \-./\ \ \ \ \ \ \ \-.  \ \ \ \ \ \  __\\ \____ \ 
 \ \_\ \ \_\ \ \_\ \ \_\\"\_\ \ \_\ \ \_\_/ \/\_____\
  \/_/  \/_/  \/_/  \/_/ \/_/  \/_/  \/_/    \/_____/""",
                parent="text_group",
            )
            # Creating log terminal
            with ui.group(parent="center_group", tag="button_group"):
                ui.add_button(tag="button_patch", label="Patch", callback=patcher_start, enabled=False, width=-1)
                ui.add_button(tag="button_select_mods", label="Select Mods", callback=gui.open_mod_menu, width=-1)
                ui.add_button(tag="button_uninstall", label="Uninstall", callback=gui.uninstall_popup_show, width=-1)
        with ui.group():
            ui.add_child_window(tag="terminal_window", no_scrollbar=False, show=True, autosize_x=True)
            ui.bind_item_font("terminal_window", "main_font")

    ui.add_window(
        label="Uninstall",
        modal=True,
        no_move=True,
        tag="uninstall_popup",
        show=False,
        no_collapse=True,
        no_close=True,
        no_saved_settings=True,
        autosize=True,
        no_resize=True,
        no_title_bar=True,
    )
    ui.add_group(tag="uninstall_popup_text_wrapper", parent="uninstall_popup")
    ui.add_text(
        default_value="Remove all mods?",
        parent="uninstall_popup_text_wrapper",
        tag="remove_mods_text_tag",
    )
    with ui.group(
        parent="uninstall_popup",
        tag="uninstall_popup_button_wrapper",
        horizontal=True,
        horizontal_spacing=10,
    ):
        ui.add_button(
            label="Confirm",
            tag="uninstall_confirm_button",
            callback=build.uninstaller,
            width=100,
        )
        ui.add_button(
            label="Cancel",
            tag="uninstall_cancel_button",
            callback=gui.hide_uninstall_popup,
            width=100,
        )
    ui.add_text(gui.title, tag="version_text", parent="primary_window", color=(80, 80, 80, 255), pos=(6, 380))

    ui.add_window(
        tag="mod_menu",
        label=helper.mod_selection_window_var,
        menubar=False,
        no_title_bar=False,
        no_move=True,
        no_collapse=True,
        no_close=False,
        no_open_over_existing_popup=True,
        show=False,
        no_resize=True,
        width=ui.get_viewport_width(),
        height=ui.get_viewport_height(),
        on_close=gui.save_checkbox_state,
    )

    ui.add_window(
        modal=False,
        pos=(0, 0),
        tag="settings_menu",
        label="Settings",
        menubar=False,
        no_title_bar=False,
        no_move=True,
        no_collapse=True,
        no_close=False,
        no_open_over_existing_popup=True,
        height=mpaths.main_window_height,
        width=mpaths.main_window_width,
        show=False,
        no_resize=True,
    )

    for opt in gui.settings_config:
        with ui.group(horizontal=True, parent="settings_menu"):
            _tag = f"opt_{opt["key"]}"
            _text = opt.get("text") if opt["type"] == "checkbox" else f"{opt.get("text")}:"
            _default_value = mpaths.get_config(opt["key"], opt["default"])

            if opt["type"] == "checkbox":
                ui.add_checkbox(
                    tag=_tag,
                    label=_text,
                    default_value=_default_value,
                )
            elif opt["type"] == "combo":
                ui.add_text(_text)
                raw_items = opt["items_getter"]() if "items_getter" in opt else []
                if raw_items and isinstance(raw_items[0], dict):
                    items = [f"{item['id']} - {item['name']}" for item in raw_items]
                else:
                    items = raw_items

                ui.add_combo(
                    tag=_tag,
                    items=items,
                    default_value=_default_value,
                    width=-1,
                )
            else:
                ui.add_text(_text)
                ui.add_input_text(
                    tag=_tag,
                    default_value=_default_value,
                    width=-1,
                )

    ui.add_spacer(parent="settings_menu", height=10)
    with ui.group(horizontal=True, parent="settings_menu"):
        ui.add_button(label="Save", callback=gui.save_settings, width=100)
        ui.add_button(label="Refresh", callback=gui.refresh_settings, width=100)

    ui.add_window(
        modal=True,
        no_move=True,
        tag="update_popup",
        show=False,
        autosize=True,
        no_collapse=True,
        no_close=True,
        no_saved_settings=True,
        no_resize=True,
        no_title_bar=True,
    )
    ui.add_group(parent="update_popup", tag="popup_text_wraper_1")
    ui.add_text(
        default_value="New update is available!",
        parent="popup_text_wraper_1",
        tag="update_popup_text_1_tag",
        indent=1,
    )
    ui.add_group(parent="update_popup", tag="popup_text_wraper_2")
    ui.add_text(
        default_value="Would you like to update?",
        parent="popup_text_wraper_2",
        tag="update_popup_text_2_tag",
        indent=1,
    )
    with ui.group(
        parent="update_popup",
        tag="update_popup_button_group",
        horizontal=True,
        horizontal_spacing=20,
    ):
        ui.add_button(
            label="Yes",
            width=120,
            height=24,
            callback=gui.update,
            tag="update_popup_yes_button",
        )
        ui.add_button(
            label="Ignore updates",
            width=120,
            height=24,
            callback=lambda: gui.delete_update_popup(True),
            tag="update_popup_ignore_button",
        )
        ui.add_button(
            label="No",
            width=120,
            height=24,
            callback=lambda: gui.delete_update_popup(False),
            tag="update_popup_no_button",
        )
    ui.configure_item("primary_window", no_scrollbar=True, no_close=True, no_title_bar=True, autosize=True)


def create_base_ui():
    gui.recalc_rescomp_dirs()
    helper.get_available_localizations()
    create_ui()
    gui.lock_interaction()
    gui.focus_window()
    gui.theme()
    helper.change_localization(init=True)
    gui.start_text()
    gui.version_check()
    gui.initiate_conditionals()
    helper.disable_workshop_mods()
    time.sleep(0.05)
    gui.configure_update_popup()
    gui.bulk_exec_script("initial", False)
    gui.setup_button_state()
    gui.unlock_interaction()
    cursor_manager_thread = threading.Thread(target=gui.cursor_manager_check, daemon=True)
    cursor_manager_thread.start()
    ui.show_style_editor()
    ui.show_debug()
    ui.show_metrics()
    ui.show_item_registry()
    with ui.item_handler_registry(tag="widget_handler") as handler:
        ui.add_item_resize_handler(callback=gui.on_primary_window_resize)
    ui.bind_item_handler_registry("primary_window", "widget_handler")


# Adding font to the ui registry
with ui.font_registry():
    with ui.font(os.path.join("bin", "FiraMono-Medium.ttf"), 16, tag="main_font") as main_font:
        ui.add_font_range_hint(ui.mvFontRangeHint_Default)
        ui.add_font_range_hint(ui.mvFontRangeHint_Cyrillic)
        ui.add_font_range(0x0100, 0x017F)  # Turkish set
        ui.add_font_range(0x0370, 0x03FF)  # Greek set
        ui.bind_font(main_font)

    with ui.font(os.path.join("bin", "FiraMono-Medium.ttf"), 14, tag="small_font") as small_font:
        ui.add_font_range_hint(ui.mvFontRangeHint_Default)
        ui.add_font_range_hint(ui.mvFontRangeHint_Cyrillic)
        ui.add_font_range(0x0100, 0x017F)  # Turkish set
        ui.add_font_range(0x0370, 0x03FF)  # Greek set

    with ui.font(os.path.join("bin", "FiraMono-Medium.ttf"), 20, tag="large_font") as large_font:
        ui.add_font_range_hint(ui.mvFontRangeHint_Default)
        ui.add_font_range_hint(ui.mvFontRangeHint_Cyrillic)
        ui.add_font_range(0x0100, 0x017F)  # Turkish set
        ui.add_font_range(0x0370, 0x03FF)  # Greek set

    with ui.font(os.path.join("bin", "FiraMono-Medium.ttf"), 32, tag="very_large_font") as very_large_font:
        ui.add_font_range_hint(ui.mvFontRangeHint_Default)
        ui.add_font_range_hint(ui.mvFontRangeHint_Cyrillic)
        ui.add_font_range(0x0100, 0x017F)  # Turkish set
        ui.add_font_range(0x0370, 0x03FF)  # Greek set


def increase_scale():  # prototype
    height, width = gui.social_button_size
    height += 14
    width += 14
    ui.configure_item("button_discord", height=height, width=width)
    ui.configure_item("button_telegram", height=height, width=width)
    ui.configure_item("button_git", height=height, width=width)
    ui.configure_item("button_dev", height=height, width=width)
    ui.configure_item("button_settings", height=height, width=width)
    font = ui.get_alias_id("very_large_font")
    ui.bind_item_font("primary_window", font)
    ui.configure_viewport(f"{gui.title}", width=1040, height=700)


# Adding mouse handler to ui registry
with ui.handler_registry():
    ui.add_mouse_drag_handler(tag="drag_handler", button=0, threshold=4, callback=gui.drag_viewport)
    ui.add_mouse_release_handler(button=0, callback=gui.stop_drag_viewport)
    ui.add_key_release_handler(0x20E, callback=gui.close_active_window)
    ui.add_mouse_click_handler(callback=gui.resize)
    ui.add_key_release_handler(0x20, callback=increase_scale)

with ui.texture_registry(show=False):
    w, h, _, d = ui.load_image(os.path.join(mpaths.img_dir, "Discord.png"))
    ui.add_static_texture(width=w, height=h, default_value=d, tag="discord_texture_tag")

    w, h, _, d = ui.load_image(os.path.join(mpaths.img_dir, "github.png"))
    ui.add_static_texture(width=w, height=h, default_value=d, tag="git_texture_tag")

    w, h, _, d = ui.load_image(os.path.join(mpaths.img_dir, "cog-wheel.png"))
    ui.add_static_texture(width=w, height=h, default_value=d, tag="settings_texture_tag")

    w, h, _, d = ui.load_image(os.path.join(mpaths.img_dir, "dev.png"))
    ui.add_static_texture(width=w, height=h, default_value=d, tag="dev_texture_tag")

    w, h, _, d = ui.load_image(os.path.join(mpaths.img_dir, "telegram.png"))
    ui.add_static_texture(width=w, height=h, default_value=d, tag="telegram_texture_tag")

# Creating_main_viewport

ui.create_viewport(
    title=gui.title,
    width=mpaths.main_window_width,
    height=mpaths.main_window_height,
    x_pos=min(gui.widths) // 2 - mpaths.main_window_width // 2,
    y_pos=max(0, min(gui.heights) // 2 - mpaths.main_window_height // 2 - 120),
    resizable=False,
    decorated=False,
    vsync=True,
    clear_color=(0, 0, 0, 255),
)

ui.set_frame_callback(1, callback=create_base_ui)  # On first frame execute app_start

ui.set_viewport_small_icon("./bin/images/favicon.ico")
ui.set_viewport_large_icon("./bin/images/favicon.ico")
ui.setup_dearpygui()
ui.show_viewport()
try:
    ui.start_dearpygui()
except KeyboardInterrupt:
    pass
ui.destroy_context()
