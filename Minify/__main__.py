import argparse
import os
import sys
import time
import webbrowser

# Ensure root directories
if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(os.path.realpath(sys.executable)))
else:
    os.chdir(current_dir := os.path.dirname(os.path.abspath(__file__)))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

# isort: split

import dearpygui.dearpygui as ui

# isort: split

import build
import conditions
import helper
from core import base, constants, fs, log
from ui import dev_tools, fonts, gui, modals, settings, theme, window

sys.excepthook = log.unhandled_handler()

parser = argparse.ArgumentParser(description="Minify")
parser.add_argument("-v", "--version", action="store_true", help="Print version and exit")
args = parser.parse_args()

if args.version:
    print(base.VERSION)
    sys.exit(0)

fs.create_dirs(base.logs_dir, base.config_dir)

ui.create_context()


def create_ui():
    button_size_x, button_size_y = gui.social_button_size
    with ui.window(tag="primary_window"):
        ui.set_primary_window("primary_window", True)
        with ui.group(tag="center_group", horizontal=True):
            ui.group(tag="text_group")
            ui.add_text(
                default_value=r""" __    __    __    __   __    __    ______  __  __
/\ "-./  \  /\ \  /\ "-.\ \  /\ \  /\  ___\/\ \_\ \  
\ \ \-./\ \ \ \ \ \ \ \-.  \ \ \ \ \ \  __\\ \____ \ 
 \ \_\ \ \_\ \ \_\ \ \_\\"\_\ \ \_\ \ \_\_/ \/\_____\
  \/_/  \/_/  \/_/  \/_/ \/_/  \/_/  \/_/    \/_____/""",
                parent="text_group",
                pos=(4, -12),
            )
            # Creating log terminal
            with ui.group(parent="center_group", tag="button_group"):
                ui.add_spacer(height=6)
                ui.add_button(
                    tag="button_patch", label="Patch", callback=lambda: build.patcher(), enabled=False, width=-1
                )
                ui.add_button(
                    tag="button_select_mods",
                    label="Select Mods",
                    callback=lambda: ui.configure_item("mod_menu", show=True),
                    width=-1,
                )
                ui.add_button(tag="button_uninstall", label="Uninstall", callback=modals.Uninstall.show, width=-1)
        with ui.group(tag="terminal_and_footer_group"):
            ui.add_child_window(tag="terminal_window", no_scrollbar=False, show=True, autosize_x=True, height=-27)
            ui.bind_item_font("terminal_window", "small_font")

            ui.add_child_window(tag="footer", no_scrollbar=True, no_scroll_with_mouse=True, autosize_x=True)
        ui.add_group(tag="footer_main_group", parent="footer", horizontal=True, horizontal_spacing=0)
        ui.add_group(tag="footer_left_group", parent="footer_main_group", horizontal=True, horizontal_spacing=0)
        ui.add_combo(
            parent="footer_left_group",
            tag="lang_select",
            items=(helper.localizations),
            default_value="EN",
            callback=helper.change_localization,
            fit_width=True,
        )
        ui.add_image_button(
            "discord_texture_tag",
            tag="button_discord",
            parent="footer_left_group",
            width=button_size_x,
            height=button_size_y,
            callback=lambda: webbrowser.open(base.discord),
        )
        ui.add_image_button(
            "telegram_texture_tag",
            tag="button_telegram",
            parent="footer_left_group",
            width=button_size_x,
            height=button_size_y,
            callback=lambda: webbrowser.open(base.telegram),
        )
        ui.add_image_button(
            "git_texture_tag",
            tag="button_git",
            parent="footer_left_group",
            width=button_size_x,
            height=button_size_y,
            callback=lambda: webbrowser.open(base.github),
        )
        ui.add_image_button(
            "settings_texture_tag",
            tag="button_settings",
            parent="footer_left_group",
            width=button_size_x,
            height=button_size_y,
            callback=lambda: ui.configure_item("settings_menu", show=True),
        )
        ui.add_image_button(
            "dev_texture_tag",
            tag="button_dev",
            parent="footer_left_group",
            width=button_size_x,
            height=button_size_y,
            callback=lambda: dev_tools.toggle_dev_tools(
                base.TITLE, gui.checkboxes, gui.save_checkbox_state, gui.setup_button_state
            ),
        )
        ui.add_text(tag="language_select", parent="footer_left_group")
        ui.add_combo(
            parent="footer_left_group",
            tag="output_select",
            items=(constants.minify_output_list),
            default_value=fs.get_config("output_locale", "minify"),
            callback=helper.change_output_path,
            fit_width=True,
        )

    # Combined Modal Popup
    ui.add_window(
        modal=True,
        no_move=True,
        tag="modal_popup",
        show=False,
        no_collapse=True,
        no_close=True,
        no_saved_settings=True,
        autosize=True,
        no_resize=True,
        no_title_bar=True,
    )
    ui.add_group(tag="modal_text_wrapper", parent="modal_popup")
    ui.add_group(
        parent="modal_popup",
        tag="modal_button_wrapper",
        horizontal=True,
        horizontal_spacing=10,
    )

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
        width=constants.main_window_width,
        height=constants.main_window_height,
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
        height=constants.main_window_height,
        width=constants.main_window_width,
        show=False,
        no_resize=True,
    )

    settings.render_settings_menu()

    ui.add_spacer(parent="settings_menu", height=10)
    with ui.group(horizontal=True, parent="settings_menu"):
        ui.add_button(label="Save", callback=settings.save_settings, width=100)
        ui.add_button(label="Refresh", callback=settings.refresh_settings, width=100)


def create_base_ui():
    dev_tools.recalc_rescomp_dirs()
    helper.get_available_localizations()
    create_ui()
    gui.lock_interaction()
    theme.enable_dark_titlebar(base.TITLE)
    window.focus_window()
    theme.theme()
    helper.change_localization(init=True)
    gui.start_text()
    modals.Update.check()
    modals.Announcements.check()
    gui.initiate_conditionals()
    conditions.disable_workshop_mods()
    time.sleep(0.05)
    helper.bulk_exec_script("initial", False)
    gui.setup_button_state()
    gui.unlock_interaction()
    with ui.item_handler_registry(tag="widget_handler"):
        ui.add_item_resize_handler(callback=window.on_primary_window_resize)
    ui.bind_item_handler_registry("primary_window", "widget_handler")
    window.on_primary_window_resize()


fonts.register_fonts()


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
    ui.configure_viewport(base.TITLE, width=1040, height=700)


# Adding mouse handler to ui registry
with ui.handler_registry():
    ui.add_mouse_drag_handler(tag="drag_handler", button=0, threshold=4, callback=window.drag_viewport)
    ui.add_mouse_release_handler(button=0, callback=window.stop_drag_viewport)
    ui.add_key_release_handler(0x20E, callback=gui.close_active_window)
    if fs.get_config("debug_env", False):
        ui.add_key_release_handler(0x20, callback=increase_scale)

with ui.texture_registry(show=False):
    w, h, _, d = ui.load_image(os.path.join(base.img_dir, "Discord.png"))
    ui.add_static_texture(width=w, height=h, default_value=d, tag="discord_texture_tag")

    w, h, _, d = ui.load_image(os.path.join(base.img_dir, "github.png"))
    ui.add_static_texture(width=w, height=h, default_value=d, tag="git_texture_tag")

    w, h, _, d = ui.load_image(os.path.join(base.img_dir, "cog-wheel.png"))
    ui.add_static_texture(width=w, height=h, default_value=d, tag="settings_texture_tag")

    w, h, _, d = ui.load_image(os.path.join(base.img_dir, "dev.png"))
    ui.add_static_texture(width=w, height=h, default_value=d, tag="dev_texture_tag")

    w, h, _, d = ui.load_image(os.path.join(base.img_dir, "telegram.png"))
    ui.add_static_texture(width=w, height=h, default_value=d, tag="telegram_texture_tag")

# Creating_main_viewport

ui.create_viewport(
    title=base.TITLE,
    width=constants.main_window_width,
    height=constants.main_window_height,
    min_width=constants.main_window_width,
    min_height=constants.main_window_height,
    x_pos=min(gui.widths) // 2 - constants.main_window_width // 2,
    y_pos=max(0, min(gui.heights) // 2 - constants.main_window_height // 2 - 120),
    resizable=True,
    decorated=True,
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
