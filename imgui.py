import os
import threading
import time

import dearpygui.dearpygui as ui
import screeninfo

import helper
import mpaths
import utils_build
import utils_gui


ui.create_context()

patching = False
blacklist_dictionary = {}
styling_dictionary = {}

ui.add_value_registry(tag="details_tags")

with ui.value_registry():
    ui.add_string_value(default_value="Checking map file...", tag="checking_map_file_var")
    ui.add_string_value(default_value="Want to contribute to the project's growth?", tag="start_text_1_var")
    ui.add_string_value(default_value="-> Join our Discord community!", tag="start_text_2_var")
    ui.add_string_value(default_value="-> Share Minify with your friends and online groups", tag="start_text_3_var")
    ui.add_string_value(default_value="-> Star the project on GitHub", tag="start_text_4_var")
    ui.add_string_value(default_value="-> Create and maintain mods for this project", tag="start_text_5_var")


def patcher_start():
    checkbox_state_save_thread = threading.Thread(target=utils_gui.checkbox_state_save)
    checkbox_state_save_thread.start()
    checkbox_state_save_thread.join()
    patch_thread = threading.Thread(target=utils_build.patcher)
    patch_thread.start()
    patch_thread.join()


def create_ui():
    with ui.window(tag="primary_window", no_close=True, no_title_bar=True):
        ui.set_primary_window("primary_window", True)
        ui.add_child_window(
            tag="top_bar", pos=(-5, -5), height=30, width=499, no_scrollbar=True, no_scroll_with_mouse=True
        )
        ui.add_combo(
            parent="top_bar",
            tag="lang_select",
            items=(helper.localizations),
            default_value="EN",
            width=50,
            pos=(5, 6),
            callback=helper.change_localization,
        )
        ui.add_image_button(
            "discord_texture_tag",
            parent="top_bar",
            width=21,
            height=16,
            pos=(55, 7),
            callback=utils_gui.open_discord_link,
        )
        ui.add_image_button(
            "git_texture_tag", parent="top_bar", width=18, height=18, pos=(87, 6), callback=utils_gui.open_github_link
        )
        ui.add_image_button(
            "dev_texture_tag",
            tag="dev",
            parent="top_bar",
            width=16,
            height=16,
            pos=(115, 6),
            callback=utils_gui.dev_mode,
        )
        ui.add_text("Language:", pos=(138, 3))
        ui.add_combo(
            parent="top_bar",
            tag="output_select",
            items=(mpaths.minify_output_list),
            default_value="minify",
            width=95,
            pos=(210, 8),
            callback=helper.change_output_path,
        )
        ui.add_text(utils_gui.title, pos=(320, 3))
        ui.add_button(
            parent="top_bar", tag="button_exit", label="Close", callback=helper.close, height=28, width=60, pos=(440, 4)
        )

        ui.bind_item_font("lang_select", combo_font)
        with ui.group(horizontal=True):
            with ui.group(pos=(391, 29)):
                ui.add_button(tag="button_patch", label="Patch", width=92, callback=patcher_start)
                ui.add_button(tag="button_select_mods", label="Select Mods", width=92, callback=utils_gui.open_mod_menu)
                ui.add_button(
                    tag="button_uninstall", label="Uninstall", width=92, callback=utils_gui.uninstall_popup_show
                )
            with ui.group(pos=(-45, 4)):
                ui.add_text(
                    r"""
         __    __    __    __   __    __    ______  __  __
        /\ "-./  \  /\ \  /\ "-.\ \  /\ \  /\  ___\/\ \_\ \  
        \ \ \-./\ \ \ \ \ \ \ \-.  \ \ \ \ \ \  __\\ \____ \ 
         \ \_\ \ \_\ \ \_\ \ \_\\"\_\ \ \_\ \ \_\_/ \/\_____\
          \/_/  \/_/  \/_/  \/_/ \/_/  \/_/  \/_/    \/_____/"""
                )
        # Creating log terminal
        with ui.group():
            ui.add_window(
                tag="terminal_window",
                no_scrollbar=False,
                no_title_bar=True,
                no_move=True,
                no_collapse=True,
                modal=False,
                no_close=True,
                no_saved_settings=True,
                show=True,
                height=200,
                width=494,
                pos=(0, 100),
                no_resize=True,
            )

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
    ui.add_text(default_value="Remove all mods?", parent="uninstall_popup_text_wrapper", tag="remove_mods_text_tag")
    with ui.group(
        parent="uninstall_popup", tag="uninstall_popup_button_wrapper", horizontal=True, horizontal_spacing=10
    ):
        ui.add_button(label="Confirm", tag="uninstall_confirm_button", callback=utils_build.uninstaller, width=100)
        ui.add_button(label="Cancel", tag="uninstall_cancel_button", callback=utils_gui.hide_uninstall_popup, width=100)

    # Creating mod selection menu as popup/modal
    ui.add_window(
        modal=False,
        pos=(0, 0),
        tag="mod_menu",
        label=helper.mod_selection_window_var,
        menubar=False,
        no_title_bar=False,
        no_move=True,
        no_collapse=True,
        no_close=False,
        no_open_over_existing_popup=True,
        height=300,
        width=494,
        show=False,
        no_resize=True,
        on_close=utils_gui.checkbox_state_save,
    )

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
        default_value="New update is now available!",
        parent="popup_text_wraper_1",
        tag="update_popup_text_1_tag",
        indent=1,
    )
    ui.add_group(parent="update_popup", tag="popup_text_wraper_2")
    ui.add_text(
        default_value="Would you like to go to the download page?",
        parent="popup_text_wraper_2",
        tag="update_popup_text_2_tag",
        indent=1,
    )
    with ui.group(parent="update_popup", tag="update_popup_button_group", horizontal=True, horizontal_spacing=20):
        ui.add_button(
            label="Yes",
            width=120,
            height=24,
            callback=utils_gui.open_github_link_and_close_minify,
            tag="update_popup_yes_button",
        )
        ui.add_button(
            label="Ignore updates",
            width=120,
            height=24,
            callback=lambda: utils_gui.delete_update_popup(ignore=True),
            tag="update_popup_ignore_button",
        )
        ui.add_button(
            label="No", width=120, height=24, callback=utils_gui.delete_update_popup, tag="update_popup_no_button"
        )


def create_base_ui():
    helper.get_available_localizations()
    create_ui()
    utils_gui.focus_window()
    utils_gui.start_text()
    utils_gui.theme()
    helper.change_localization(init=True)
    utils_gui.version_check()
    time.sleep(0.05)
    utils_gui.configure_update_popup()


# Adding font to the ui registry
with ui.font_registry():
    with ui.font(os.path.join("bin", "FiraMono-Medium.ttf"), 14) as main_font:
        ui.add_font_range_hint(ui.mvFontRangeHint_Default)
        ui.add_font_range_hint(ui.mvFontRangeHint_Cyrillic)
        ui.add_font_range(0x0100, 0x017F)  # Turkish set
        ui.bind_font(main_font)
    with ui.font(os.path.join("bin", "FiraMono-Medium.ttf"), 16) as combo_font:
        ui.add_font_range_hint(ui.mvFontRangeHint_Default)
        ui.add_font_range_hint(ui.mvFontRangeHint_Cyrillic)
        ui.add_font_range(0x0100, 0x017F)  # Turkish set

# Adding mouse handler to ui registry
with ui.handler_registry():
    ui.add_mouse_drag_handler(parent="top_bar", button=0, threshold=4, callback=utils_gui.drag_viewport)
    ui.add_key_release_handler(0x20E, callback=utils_gui.close_active_window)

width_discord, height_discord, channels_discord, data_discord = ui.load_image(
    os.path.join(mpaths.img_dir, "Discord.png")
)

width_git, height_git, channels_git, data_git = ui.load_image(os.path.join(mpaths.img_dir, "github.png"))
width_dev, height_dev, channels_dev, data_dev = ui.load_image(os.path.join(mpaths.img_dir, "cog-wheel.png"))

with ui.texture_registry(show=False):
    ui.add_static_texture(
        width=width_discord, height=height_discord, default_value=data_discord, tag="discord_texture_tag"
    )
    ui.add_static_texture(width=width_git, height=height_git, default_value=data_git, tag="git_texture_tag")
    ui.add_static_texture(width=width_dev, height=height_dev, default_value=data_dev, tag="dev_texture_tag")


# Creating_main_viewport
widths = []
heights = []

for monitor in screeninfo.get_monitors():
    widths.append(monitor.width)
    heights.append(monitor.height)


ui.create_viewport(
    title=utils_gui.title,
    height=300,
    width=494,
    x_pos=min(widths) // 2 - 494 // 2,
    y_pos=min(heights) // 2 - 300 // 2 - 40,
    resizable=False,
    decorated=False,
    vsync=True,
    clear_color=(0, 0, 0, 255),
)

ui.set_frame_callback(1, callback=create_base_ui)  # On first frame execute app_start


ui.set_viewport_small_icon("./bin/favicon.ico")
ui.set_viewport_large_icon("./bin/favicon.ico")
ui.setup_dearpygui()
ui.show_viewport()
ui.start_dearpygui()
ui.destroy_context()
