import os
import sys
import threading
import time
import webbrowser

# Ensure root directories
if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(os.path.realpath(sys.executable)))
else:
    os.chdir(current_dir := os.path.dirname(os.path.abspath(__file__)))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

os.makedirs("config", exist_ok=True)
os.makedirs("logs", exist_ok=True)

if len(sys.argv) > 1:
    import cli

    cli.run()
    sys.exit(0)

# isort: split

import browsers
import conditions
import dearpygui.dearpygui as dpg
import helper
import patch
from browsers.d2pfx import ui as d2pfx_ui
from core import base, config, constants, log
from ui import (
    checkboxes,
    dev_tools,
    fonts,
    gui,
    localization,
    modals,
    settings,
    shared,
    theme,
    window,
)

sys.excepthook = log.unhandled_handler()
browsers.initialize()

dpg.create_context()


def create_ui():
    button_size_x, button_size_y = gui.social_button_size
    with dpg.window(tag="primary_window"):
        dpg.set_primary_window("primary_window", True)
        with dpg.group(tag="center_group", horizontal=True):
            dpg.group(tag="text_group")
            dpg.add_text(
                tag="banner_text",
                default_value=r""" __    __    __    __   __    __    ______  __  __
/\ "-./  \  /\ \  /\ "-.\ \  /\ \  /\  ___\/\ \_\ \  
\ \ \-./\ \ \ \ \ \ \ \-.  \ \ \ \ \ \  __\\ \____ \ 
 \ \_\ \ \_\ \ \_\ \ \_\\"\_\ \ \_\ \ \_\_/ \/\_____\
  \/_/  \/_/  \/_/  \/_/ \/_/  \/_/  \/_/    \/_____/""",
                parent="text_group",
                pos=(4, -12),
            )
            dpg.bind_item_font("banner_text", "banner_font")
            # Creating log terminal
            with dpg.group(parent="center_group", tag="button_group"):
                dpg.add_spacer(height=6)
                dpg.add_button(
                    tag="button_patch",
                    label="Patch",
                    callback=lambda: threading.Thread(target=patch.patcher, daemon=True).start(),
                    enabled=False,
                    width=-1,
                )
                dpg.add_button(
                    tag="button_select_mods",
                    label="Select Mods",
                    callback=lambda: dpg.configure_item("mod_menu", show=True),
                    width=-1,
                )
                dpg.add_button(tag="button_uninstall", label="Uninstall", callback=modals.Uninstall.show, width=-1)
        with dpg.group(tag="terminal_and_footer_group"):
            dpg.add_child_window(tag="terminal_window", no_scrollbar=False, show=True, autosize_x=True, height=-27)
            dpg.bind_item_font("terminal_window", "small_font")

            dpg.add_child_window(tag="footer", no_scrollbar=True, no_scroll_with_mouse=True, autosize_x=True)
        dpg.add_group(tag="footer_main_group", parent="footer", horizontal=True, horizontal_spacing=0)
        dpg.add_group(tag="footer_left_group", parent="footer_main_group", horizontal=True, horizontal_spacing=0)
        dpg.add_combo(
            parent="footer_left_group",
            tag="lang_select",
            items=(localization.localizations),
            default_value="EN",
            callback=localization.change,
            fit_width=True,
        )
        dpg.add_image_button(
            "discord_texture_tag",
            tag="button_discord",
            parent="footer_left_group",
            width=button_size_x,
            height=button_size_y,
            callback=lambda: webbrowser.open(base.discord),
        )
        dpg.add_image_button(
            "telegram_texture_tag",
            tag="button_telegram",
            parent="footer_left_group",
            width=button_size_x,
            height=button_size_y,
            callback=lambda: webbrowser.open(base.telegram),
        )
        dpg.add_image_button(
            "git_texture_tag",
            tag="button_git",
            parent="footer_left_group",
            width=button_size_x,
            height=button_size_y,
            callback=lambda: webbrowser.open(base.github_io),
        )
        dpg.add_image_button(
            "settings_texture_tag",
            tag="button_settings",
            parent="footer_left_group",
            width=button_size_x,
            height=button_size_y,
            callback=lambda: dpg.configure_item("settings_menu", show=True),
        )
        dpg.add_image_button(
            "dev_texture_tag",
            tag="button_dev",
            parent="footer_left_group",
            width=button_size_x,
            height=button_size_y,
            callback=dev_tools.toggle,
        )
        dpg.add_image_button(
            "refresh_texture_tag",
            tag="button_refresh",
            parent="footer_left_group",
            width=button_size_x,
            height=button_size_y,
            callback=checkboxes.refresh,
        )
        dpg.add_image_button(
            "d2pfx_texture_tag",
            tag="button_browser_d2pfx",
            parent="footer_left_group",
            width=button_size_x,
            height=button_size_y,
            callback=d2pfx_ui.toggle,
        )
        dpg.add_text(tag="language_select", parent="footer_left_group")
        dpg.add_combo(
            parent="footer_left_group",
            tag="output_select",
            items=(constants.minify_output_list),
            default_value=config.get("output_locale", "russian"),
            callback=helper.change_output_path,
            fit_width=True,
        )

    # Combined Modal Popup
    dpg.add_window(
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
        no_scrollbar=True,
    )
    dpg.add_group(tag="modal_text_wrapper", parent="modal_popup")
    dpg.add_group(tag="modal_progress_wrapper", parent="modal_popup", show=False)
    dpg.add_progress_bar(tag="modal_progress", parent="modal_progress_wrapper", width=-1)
    dpg.add_text("", tag="modal_progress_status", parent="modal_progress_wrapper")
    dpg.add_group(
        parent="modal_popup",
        tag="modal_button_wrapper",
        horizontal=True,
        horizontal_spacing=10,
    )

    dpg.add_window(
        tag="mod_menu",
        label=localization.mod_selection_window_var,
        menubar=False,
        no_title_bar=False,
        no_move=True,
        no_collapse=True,
        no_close=False,
        no_open_over_existing_popup=True,
        show=False,
        no_resize=True,
        width=base.main_window_width,
        height=base.main_window_height,
        on_close=checkboxes.save,
    )

    dpg.add_window(
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
        height=base.main_window_height,
        width=base.main_window_width,
        show=False,
        no_resize=True,
    )

    settings.render_menu()

    dpg.add_spacer(parent="settings_menu", height=10)
    with dpg.group(horizontal=True, parent="settings_menu", tag="settings_buttons_group"):
        dpg.add_button(label="Save", callback=settings.save, width=100)
        dpg.add_button(label="Refresh", callback=settings.refresh, width=100)
        dpg.add_button(label="Reset", callback=settings.reset, width=100)


def create_base_ui():
    localization.get_available()
    create_ui()
    with gui.interactive_lock():
        theme.enable_dark_titlebar()
        window.focus()
        theme.apply()
        localization.change(init=True)
        gui.start_text()
        modals.Update.check()
        modals.Announcements.check()
        gui.initiate_conditionals()
        conditions.disable_workshop_mods()
        if not conditions.workshop_installed and not config.get("workshop_modal_shown", False):
            modals.WorkshopTools.show()
        if not config.get("language_modal_shown", False):
            modals.LanguageSetup.show()
        time.sleep(0.05)
        helper.bulk_exec_script("initial", False)
        checkboxes.setup_state()
    with dpg.item_handler_registry(tag="widget_handler"):
        dpg.add_item_resize_handler(callback=window.on_resize)
    dpg.bind_item_handler_registry("primary_window", "widget_handler")
    window.on_resize()


fonts.register(config.get("locale", "EN"))


with dpg.handler_registry():
    dpg.add_mouse_drag_handler(tag="drag_handler", button=0, threshold=4, callback=window.drag)
    dpg.add_mouse_release_handler(button=0, callback=window.stop_drag)
    dpg.add_key_release_handler(dpg.mvKey_Escape, callback=gui.close_active_window)

    def modal_accept():
        from ui import modal_shared

        if dpg.is_item_shown("modal_popup") and modal_shared.active_modal_callback:
            modal_shared.active_modal_callback()

    dpg.add_key_release_handler(dpg.mvKey_Return, callback=modal_accept)

with dpg.texture_registry(show=False):
    w, h, _, d = dpg.load_image(os.path.join(base.img_dir, "Discord.png"))
    dpg.add_static_texture(width=w, height=h, default_value=d, tag="discord_texture_tag")

    w, h, _, d = dpg.load_image(os.path.join(base.img_dir, "github.png"))
    dpg.add_static_texture(width=w, height=h, default_value=d, tag="git_texture_tag")

    w, h, _, d = dpg.load_image(os.path.join(base.img_dir, "cog-wheel.png"))
    dpg.add_static_texture(width=w, height=h, default_value=d, tag="settings_texture_tag")

    w, h, _, d = dpg.load_image(os.path.join(base.img_dir, "dev.png"))
    dpg.add_static_texture(width=w, height=h, default_value=d, tag="dev_texture_tag")

    w, h, _, d = dpg.load_image(os.path.join(base.img_dir, "telegram.png"))
    dpg.add_static_texture(width=w, height=h, default_value=d, tag="telegram_texture_tag")

    w, h, _, d = dpg.load_image(os.path.join(base.img_dir, "refresh.png"))
    dpg.add_static_texture(width=w, height=h, default_value=d, tag="refresh_texture_tag")

    w, h, _, d = dpg.load_image(os.path.join(base.img_dir, "d2pfx.png"))
    dpg.add_static_texture(width=w, height=h, default_value=d, tag="d2pfx_texture_tag")

# Creating_main_viewport

viewport_width = max(base.main_window_width, config.get("window_width", base.main_window_width))
viewport_height = max(base.main_window_height, config.get("window_height", base.main_window_height))

shared.viewport_width = viewport_width
shared.viewport_height = viewport_height

dpg.create_viewport(
    title=base.TITLE,
    width=viewport_width,
    height=viewport_height,
    min_width=base.main_window_width,
    min_height=base.main_window_height,
    x_pos=min(gui.widths) // 2 - viewport_width // 2,
    y_pos=max(0, min(gui.heights) // 2 - viewport_height // 2 - 120),
    resizable=True,
    decorated=True,
    vsync=True,
    clear_color=(0, 0, 0, 255),
)

dpg.set_frame_callback(1, callback=create_base_ui)  # On first frame execute app_start

dpg.set_viewport_small_icon("./bin/images/favicon.ico")
dpg.set_viewport_large_icon("./bin/images/favicon.ico")
dpg.setup_dearpygui()
dpg.show_viewport()
try:
    dpg.start_dearpygui()
except KeyboardInterrupt:
    pass

if shared.viewport_width > 0:
    config.set("window_width", shared.viewport_width)
if shared.viewport_height > 0:
    config.set("window_height", shared.viewport_height)

dpg.destroy_context()
