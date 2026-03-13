import os
import shutil
import webbrowser

import dearpygui.dearpygui as ui

# isort: split

import build
import helper
from core import base, constants, fs, steam

# Developer tools state
dev_mode_state = -1
prev_width = None
prev_height = None


def recalc_rescomp_dirs():
    if constants.rescomp_override:
        constants.minify_dota_compile_input_path = os.path.join(
            base.rescomp_override_dir, "content", "dota_addons", "minify"
        )
        constants.minify_dota_compile_output_path = os.path.join(
            base.rescomp_override_dir, "game", "dota_addons", "minify"
        )
        constants.dota_resource_compiler_path = os.path.join(
            base.rescomp_override_dir, "game", "bin", "win64", "resourcecompiler.exe"
        )


def extract_workshop_tools():
    helper.clean_terminal()
    fs.remove_path(base.rescomp_override_dir)
    fails = 0

    for i, path in enumerate(constants.dota_tools_paths):
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.copytree(path, constants.dota_tools_extraction_paths[i])
            else:
                shutil.copy(path, constants.dota_tools_extraction_paths[i])
        else:
            helper.add_text_to_terminal("&extraction_of_failed", path)
            fails += 1

    if not fails:
        recalc_rescomp_dirs()
        if os.path.exists(constants.dota_resource_compiler_path):
            helper.add_text_to_terminal("&extracted")
        else:
            helper.add_text_to_terminal("&extraction_of_failed", path)


def tick_batch(state: bool, checkboxes, save_cb, setup_cb):
    for box in checkboxes:
        box_cfg = ui.get_item_configuration(box)
        if box_cfg["enabled"]:
            ui.set_value(box, state)
    if save_cb:
        save_cb()
    if setup_cb:
        setup_cb()


def toggle_dev_tools(title, checkboxes, save_cb, setup_cb):
    global dev_mode_state
    width_increase = 450
    height_increase = 200 if fs.get_config("debug_env", False) else 0

    target_width = constants.main_window_width + width_increase
    target_height = constants.main_window_height + height_increase

    current_w = prev_width if prev_width is not None else constants.main_window_width
    current_h = prev_height if prev_height is not None else constants.main_window_height

    expanded_w = max(current_w, target_width)
    expanded_h = max(current_h, target_height)

    tools_height = constants.main_window_height // 2
    debug_env = fs.get_config("debug_env", False) if not base.FROZEN else False

    if dev_mode_state == -1:  # init
        dev_mode_state = 1
        ui.configure_viewport(
            item=title,
            width=expanded_w,
            height=expanded_h,
            min_width=target_width,
            min_height=target_height,
        )
        with ui.window(
            label="Path & File Opener",
            tag="opener",
            pos=(constants.main_window_width, 0),
            width=width_increase // 2,
            height=constants.main_window_height,
            no_resize=True,
            no_move=True,
            no_close=True,
            no_collapse=True,
        ):
            ui.add_button(
                label="Path: Compile output path",
                callback=lambda: fs.open_thing(os.path.join(helper.output_path)),
            )
            ui.add_button(
                label="File: Compiled pak66 VPK",
                callback=lambda: fs.open_thing(os.path.join(helper.output_path, "pak66_dir.vpk")),
            )
            ui.add_spacer(width=0, height=5)
            ui.add_button(
                label="Path: Minify root",
                callback=lambda: fs.open_thing(os.getcwd()),
            )
            ui.add_button(
                label="Path: Logs",
                callback=lambda: fs.open_thing(base.logs_dir),
            )
            ui.add_button(
                label="Path: Config",
                callback=lambda: fs.open_thing(base.config_dir),
            )
            ui.add_button(
                label="Path: Mods",
                callback=lambda: fs.open_thing(base.mods_dir),
            )
            ui.add_spacer(width=0, height=5)
            ui.add_button(
                label="Path: Dota2",
                callback=lambda: fs.open_thing(os.path.join(steam.steam_library, "steamapps", "common", "dota 2 beta")),
            )
            ui.add_button(
                label="File: Dota2 pak01 VPK",
                callback=lambda: fs.open_thing(constants.dota_game_pak_path),
            )
            ui.add_button(
                label="File: Dota2 pak01(core) VPK",
                callback=lambda: fs.open_thing(constants.dota_core_pak_path),
            )
            ui.add_spacer(width=0, height=5)
            ui.add_button(
                label="Executable: Dota2 Tools",
                callback=lambda: fs.open_thing(
                    constants.dota2_tools_executable,
                    f"-addon a -language {fs.get_config('output_locale')} -novid -console",
                ),
            )
            ui.add_text("^ Requires steam to be open")
            ui.add_button(
                label="Executable: Dota2",
                callback=lambda: fs.open_thing(
                    constants.dota2_executable, f"-language {fs.get_config('output_locale')} -novid -console"
                ),
            )
            ui.add_button(label="Create debug zip", callback=helper.create_debug_zip)

        with ui.window(
            label="Mod Tools",
            tag="mod_tools",
            pos=(constants.main_window_width + width_increase // 2, 0),
            width=width_increase // 2,
            height=tools_height,
            no_resize=True,
            no_move=True,
            no_close=True,
            no_collapse=True,
        ):
            ui.add_button(
                label="Select path to compile",
                callback=lambda: ui.show_item("compile_file_dialog"),
            )
            ui.add_file_dialog(
                show=False,
                modal=False,
                min_size=(480, 260),
                callback=helper.select_compile_dir,
                tag="compile_file_dialog",
                directory_selector=True,
            )
            ui.add_button(
                label="Compile items from path",
                callback=lambda: helper.compile(
                    input_path=os.path.join(base.config_dir, "custom"),
                    output_path=os.path.join(base.config_dir, "compiled"),
                ),
            )
            ui.add_spacer(width=0, height=5)
            ui.add_button(label="Create a blank mod", callback=build.create_blank_mod)
            # ui.add_spacer(width=0, height=5)
            # ui.add_button(label="Patch with seperate paks", callback=build.patch_seperate) # broken
            ui.add_spacer(width=0, height=5)
            ui.add_button(label="Untick all mods", callback=lambda: tick_batch(False, checkboxes, save_cb, setup_cb))
            ui.add_button(label="Tick all mods", callback=lambda: tick_batch(True, checkboxes, save_cb, setup_cb))

        with ui.window(
            label="Maintenance Tools",
            tag="maintenance_tools",
            pos=(constants.main_window_width + width_increase // 2, tools_height),
            width=width_increase // 2,
            height=constants.main_window_height - tools_height,
            no_resize=True,
            no_move=True,
            no_close=True,
            no_collapse=True,
        ):
            ui.add_button(label="Wipe language paths", callback=build.wipe_lang_dirs)
            ui.add_spacer(width=0, height=5)
            ui.add_button(label="Extract workshop tools", callback=extract_workshop_tools)
            ui.add_spacer(width=0, height=5)
            ui.add_button(
                label="Launch Steam", callback=lambda: fs.open_thing(constants.steam_executable_path, "-silent")
            )
            ui.add_button(
                label="Kill Steam", callback=lambda: fs.open_thing(constants.steam_executable_path, "-exitsteam")
            )
            ui.add_button(
                label="Validate Dota2", callback=lambda: webbrowser.open(f"steam://validate/{base.STEAM_DOTA_ID}")
            )

        if not base.FROZEN and debug_env:
            with ui.window(
                label="Debug tools",
                tag="debug_tools",
                pos=(constants.main_window_width, constants.main_window_height),
                width=width_increase,
                height=150,
                no_resize=True,
                no_move=True,
                no_close=True,
                no_collapse=True,
            ):
                ui.add_button(label="debug", callback=ui.show_debug)
                ui.add_button(label="item_registry", callback=ui.show_item_registry)
                ui.add_button(label="metrics", callback=ui.show_metrics)
                ui.add_button(label="style_editor", callback=ui.show_style_editor)
                ui.add_button(label="font_manager", callback=ui.show_font_manager)

    elif dev_mode_state == 1:  # Currently open -> Close
        dev_mode_state = 0
        ui.configure_viewport(
            item=title,
            width=current_w,
            height=current_h,
            min_width=constants.main_window_width,
            min_height=constants.main_window_height,
        )
        ui.configure_item("opener", show=False)
        ui.configure_item("mod_tools", show=False)
        ui.configure_item("maintenance_tools", show=False)
        if not base.FROZEN and debug_env:
            ui.configure_item("debug_tools", show=False)

    else:  # Currently closed (0) -> Open
        dev_mode_state = 1
        ui.configure_viewport(
            item=title,
            width=expanded_w,
            height=expanded_h,
            min_width=target_width,
            min_height=target_height,
        )
        ui.configure_item("opener", show=True)
        ui.configure_item("mod_tools", show=True)
        ui.configure_item("maintenance_tools", show=True)
        if not base.FROZEN and debug_env:
            ui.configure_item("debug_tools", show=True)
