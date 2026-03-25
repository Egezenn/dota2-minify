"Dev tools pane that contains things for easy navigation, workarounds and debugging"

import os
import shutil
import webbrowser

import dearpygui.dearpygui as dpg
import helper
from core import base, config, constants, fs, log, steam

from ui import checkboxes, terminal

# Developer tools state
dev_mode_state = -1
prev_width = None
prev_height = None


def recalc_rescomp_dirs():
    "Swaps the variables for resourcecompiler.exe when extracted"
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
    "Extracts the bare minimum requirements for resourcecompiler.exe"
    terminal.clean()
    fs.remove_path(base.rescomp_override_dir)
    fails = 0

    for i, path in enumerate(constants.dota_tools_paths):
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.copytree(path, constants.dota_tools_extraction_paths[i])
            else:
                shutil.copy(path, constants.dota_tools_extraction_paths[i])
        else:
            terminal.add_text("&extraction_of_failed", path)
            fails += 1

    if not fails:
        recalc_rescomp_dirs()
        if os.path.exists(constants.dota_resource_compiler_path):
            terminal.add_text("&extracted")
        else:
            terminal.add_text("&extraction_of_failed", path)


def tick_batch(state: bool):
    for box in checkboxes.checkboxes:
        box_cfg = dpg.get_item_configuration(box)
        if box_cfg["enabled"]:
            dpg.set_value(box, state)
    checkboxes.save()


def toggle():
    import build

    global dev_mode_state
    width_increase = 450
    height_increase = 200 if config.get("debug_env", False) else 0

    target_width = base.main_window_width + width_increase
    target_height = base.main_window_height + height_increase

    current_w = prev_width if prev_width is not None else base.main_window_width
    current_h = prev_height if prev_height is not None else base.main_window_height

    expanded_w = max(current_w, target_width)
    expanded_h = max(current_h, target_height)

    tools_height = base.main_window_height // 2
    debug_env = config.get("debug_env", False) if not base.FROZEN else False

    if dev_mode_state == -1:  # init
        dev_mode_state = 1
        dpg.configure_viewport(
            item=base.TITLE,
            width=expanded_w,
            height=expanded_h,
            min_width=target_width,
            min_height=target_height,
        )
        with dpg.window(
            label="Path & File Opener",
            tag="opener",
            pos=(base.main_window_width, 0),
            width=width_increase // 2,
            height=base.main_window_height,
            no_resize=True,
            no_move=True,
            no_close=True,
            no_collapse=True,
        ):
            dpg.add_button(
                label="Path: Compile output path",
                callback=lambda: fs.open_thing(os.path.join(helper.output_path)),
            )
            dpg.add_button(
                label="File: Compiled pak66 VPK",
                callback=lambda: fs.open_thing(os.path.join(helper.output_path, "pak66_dir.vpk")),
            )
            dpg.add_spacer(width=0, height=5)
            dpg.add_button(
                label="Path: Minify root",
                callback=lambda: fs.open_thing(os.getcwd()),
            )
            dpg.add_button(
                label="Path: Logs",
                callback=lambda: fs.open_thing(base.logs_dir),
            )
            dpg.add_button(
                label="Path: Config",
                callback=lambda: fs.open_thing(base.config_dir),
            )
            dpg.add_button(
                label="Path: Mods",
                callback=lambda: fs.open_thing(base.mods_dir),
            )
            dpg.add_spacer(width=0, height=5)
            dpg.add_button(
                label="Path: Dota2",
                callback=lambda: fs.open_thing(
                    os.path.join(config.get("steam_library"), "steamapps", "common", "dota 2 beta")
                ),
            )
            dpg.add_button(
                label="File: Dota2 pak01 VPK",
                callback=lambda: fs.open_thing(constants.dota_game_pak_path),
            )
            dpg.add_button(
                label="File: Dota2 pak01(core) VPK",
                callback=lambda: fs.open_thing(constants.dota_core_pak_path),
            )
            dpg.add_spacer(width=0, height=5)
            dpg.add_button(
                label="Executable: Dota2 Tools",
                callback=lambda: fs.open_thing(
                    constants.dota2_tools_executable,
                    f"-addon a -language {config.get('output_locale')} -novid -console",
                ),
            )
            dpg.add_text("^ Requires steam to be open")
            dpg.add_button(
                label="Executable: Dota2",
                callback=lambda: fs.open_thing(
                    constants.dota2_executable, f"-language {config.get('output_locale')} -novid -console"
                ),
            )
            dpg.add_button(label="Create debug zip", callback=log.create_debug_zip)

        with dpg.window(
            label="Mod Tools",
            tag="mod_tools",
            pos=(base.main_window_width + width_increase // 2, 0),
            width=width_increase // 2,
            height=tools_height,
            no_resize=True,
            no_move=True,
            no_close=True,
            no_collapse=True,
        ):
            dpg.add_button(
                label="Select path to compile",
                callback=lambda: dpg.show_item("compile_file_dialog"),
            )
            dpg.add_file_dialog(
                show=False,
                modal=False,
                min_size=(480, 260),
                callback=helper.select_compile_dir,
                tag="compile_file_dialog",
                directory_selector=True,
            )
            dpg.add_button(
                label="Compile items from path",
                callback=lambda: helper.compile_assets(
                    input_path=os.path.join(base.config_dir, "custom"),
                    output_path=os.path.join(base.config_dir, "compiled"),
                ),
            )
            dpg.add_spacer(width=0, height=5)
            dpg.add_button(label="Create a blank mod", callback=build.create_blank_mod)
            # ui.add_spacer(width=0, height=5)
            # ui.add_button(label="Patch with seperate paks", callback=build.patch_seperate) # broken
            dpg.add_spacer(width=0, height=5)
            dpg.add_button(label="Untick all mods", callback=lambda: tick_batch(False))
            dpg.add_button(label="Tick all mods", callback=lambda: tick_batch(True))

        with dpg.window(
            label="Maintenance Tools",
            tag="maintenance_tools",
            pos=(base.main_window_width + width_increase // 2, tools_height),
            width=width_increase // 2,
            height=base.main_window_height - tools_height,
            no_resize=True,
            no_move=True,
            no_close=True,
            no_collapse=True,
        ):
            dpg.add_button(label="Wipe language paths", callback=build.wipe_lang_dirs)
            dpg.add_spacer(width=0, height=5)
            dpg.add_button(label="Extract workshop tools", callback=extract_workshop_tools)
            dpg.add_spacer(width=0, height=5)
            dpg.add_button(label="Launch Steam", callback=lambda: fs.open_thing(steam.steam_executable_path, "-silent"))
            dpg.add_button(
                label="Kill Steam", callback=lambda: fs.open_thing(steam.steam_executable_path, "-exitsteam")
            )
            dpg.add_button(
                label="Validate Dota2", callback=lambda: webbrowser.open(f"steam://validate/{base.STEAM_DOTA_ID}")
            )

        if not base.FROZEN and debug_env:
            with dpg.window(
                label="Debug tools",
                tag="debug_tools",
                pos=(base.main_window_width, base.main_window_height),
                width=width_increase,
                height=150,
                no_resize=True,
                no_move=True,
                no_close=True,
                no_collapse=True,
            ):
                dpg.add_button(label="debug", callback=dpg.show_debug)
                dpg.add_button(label="item_registry", callback=dpg.show_item_registry)
                dpg.add_button(label="metrics", callback=dpg.show_metrics)
                dpg.add_button(label="style_editor", callback=dpg.show_style_editor)
                dpg.add_button(label="font_manager", callback=dpg.show_font_manager)

    elif dev_mode_state == 1:  # Currently open -> Close
        dev_mode_state = 0
        dpg.configure_viewport(
            item=base.TITLE,
            width=current_w,
            height=current_h,
            min_width=base.main_window_width,
            min_height=base.main_window_height,
        )
        dpg.configure_item("opener", show=False)
        dpg.configure_item("mod_tools", show=False)
        dpg.configure_item("maintenance_tools", show=False)
        if not base.FROZEN and debug_env:
            dpg.configure_item("debug_tools", show=False)

    else:  # Currently closed (0) -> Open
        dev_mode_state = 1
        dpg.configure_viewport(
            item=base.TITLE,
            width=expanded_w,
            height=expanded_h,
            min_width=target_width,
            min_height=target_height,
        )
        dpg.configure_item("opener", show=True)
        dpg.configure_item("mod_tools", show=True)
        dpg.configure_item("maintenance_tools", show=True)
        if not base.FROZEN and debug_env:
            dpg.configure_item("debug_tools", show=True)
