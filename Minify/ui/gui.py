import concurrent.futures
import os
import threading
import time

import conditions
import dearpygui.dearpygui as dpg
import jsonc
import screeninfo
from core import base, config, constants, fs, localization, log

from ui import details, modal_shared, shared, terminal

checkboxes = []
checkboxes_state = {}
gui_lock = False

terminal_window_wrap = base.main_window_width - 10

widths = []
heights = []

social_button_size = (18, 18)

for monitor in screeninfo.get_monitors():
    widths.append(monitor.width)
    heights.append(monitor.height)


def initiate_conditionals():
    # Updater self-update
    updater = "updater.exe" if base.OS == base.WIN else "updater"
    updater_new = "updater-new.exe" if base.OS == base.WIN else "updater"

    if os.path.exists(updater_new):
        try:
            fs.remove_path(updater)
            fs.move_path(updater_new, updater)
            if base.OS != base.WIN:
                os.chmod(updater, 0o755)
        except:
            log.write_warning()

    setup_system_thread = threading.Thread(target=setup_system)
    load_state_checkboxes_thread = threading.Thread(target=load_checkboxes_state)
    setup_system_thread.start()
    load_state_checkboxes_thread.start()
    setup_system_thread.join()
    load_state_checkboxes_thread.join()

    with dpg.texture_registry(tag="mod_images_registry", show=False):
        pass

    create_checkboxes()


def setup_system():
    fs.create_dirs(base.logs_dir)
    conditions.is_dota_running("&error_please_close_dota_terminal", "error")
    conditions.is_compiler_found()
    conditions.download_dependencies()


def load_checkboxes_state():
    global checkboxes_state
    try:
        with open(base.mods_config_dir, encoding="utf-8") as file:
            checkboxes_state = jsonc.load(file)
    except FileNotFoundError:
        open(base.mods_config_dir, "w").close()


def save_checkbox_state():
    for box in checkboxes:
        checkboxes_state[box] = dpg.get_value(box)
    with open(base.mods_config_dir, "w", encoding="utf-8") as file:
        jsonc.dump(checkboxes_state, file, indent=2)


def create_checkboxes():
    mod_details_cache = {}

    def scan_mod_details(mod_name):
        mod_p = os.path.join(base.mods_dir, mod_name)
        img_p = os.path.join(mod_p, "preview.png")
        notes_p = os.path.join(mod_p, "notes.md")

        image_data = None
        has_notes = False

        if os.path.exists(img_p):
            try:
                image_data = dpg.load_image(img_p)
            except Exception as err:
                print(f"Failed to load image for {mod_name}: {err}")

        if os.path.exists(notes_p) and os.path.getsize(notes_p) > 0:
            has_notes = True

        return mod_name, image_data, has_notes

    mods_to_scan = [m for m in constants.visually_available_mods if not m.endswith(".vpk")]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(scan_mod_details, mods_to_scan)
        for m_name, img_data, notes_exist in results:
            mod_details_cache[m_name] = (img_data, notes_exist)

    for mod in constants.visually_available_mods:
        mod_path = os.path.join(base.mods_dir, mod)
        if is_vpk := mod.endswith(".vpk"):
            always_val = False
        else:
            mod_cfg_path = os.path.join(mod_path, "modcfg.json")
            always_val = config.read_json_file(mod_cfg_path).get("always", False)

        if always_val:
            enable_ticking = False
            value = True
        else:
            enable_ticking = True
            value = checkboxes_state.get(mod, False)

        dpg.add_group(parent="mod_menu", tag=f"{mod}_group_tag", horizontal=True, width=base.main_window_width)
        dpg.add_checkbox(
            parent=f"{mod}_group_tag",
            label=mod[:-4] if is_vpk else mod,
            tag=mod,
            callback=setup_button_state,
            default_value=value,
            enabled=enable_ticking,
        )

        if not is_vpk:
            img_data, has_notes = mod_details_cache.get(mod, (None, False))

            if img_data or has_notes:
                tag_data = f"{mod}_details_window_tag"
                dpg.add_button(
                    parent=f"{mod}_group_tag",
                    small=True,
                    indent=base.main_window_width - 150,
                    tag=f"{mod}_button_show_details_tag",
                    label=f"{localization.details_label}",
                    callback=show_details,
                    user_data=tag_data,
                )
                shared.tag_data_for_details_windows.append(tag_data)
                dpg.add_window(
                    tag=tag_data,
                    modal=True,
                    pos=(0, 0),
                    show=False,
                    label=mod,
                    no_resize=True,
                    no_move=True,
                    no_close=False,
                    no_collapse=True,
                    width=base.main_window_width,
                    height=base.main_window_height,
                )

                content_group = f"{mod}_details_content_group"
                with dpg.group(parent=tag_data, tag=content_group):
                    pass

                if img_data:
                    try:
                        w, h, _, d = img_data
                        image_tag = f"{mod}_image_texture"
                        dpg.add_static_texture(
                            width=w, height=h, default_value=d, tag=image_tag, parent="mod_images_registry"
                        )
                        shared.mod_details_image_cache[mod] = (w, h, image_tag)
                    except Exception as e:
                        print(f"Failed to display image for {mod}: {e}")

                details.render_details_window(mod)

        checkboxes.append(mod)


def setup_button_state():
    # base mod is always enabled and is shown in the ui since it received details page

    # for box in checkboxes_state:
    #     if box in checkboxes and ui.get_value(box):
    #         ui.configure_item("button_patch", enabled=True)
    #         break
    #     else:
    #         ui.configure_item("button_patch", enabled=False)
    save_checkbox_state()


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


def show_details(sender, app_data, user_data):
    mod = user_data.replace("_details_window_tag", "")
    details.render_details_window(mod)
    dpg.configure_item(user_data, show=True)
    dpg.focus_item(user_data)


def start_text():
    for i in range(1, 6):
        terminal.add_text_to_terminal(f"&start_text_{i}_var")
    dpg.add_separator(parent="terminal_window")


def close_active_window():
    active_window = dpg.get_item_alias(dpg.get_active_window())
    if active_window not in [
        "terminal_window",
        "primary_window",
        "footer",
        "opener",
        "mod_tools",
        "maintenance_tools",
    ]:
        if active_window == "modal_popup":
            dpg.configure_item("modal_popup", show=False)
            threading.Timer(0.1, modal_shared.show_next_modal_from_queue).start()
        else:
            dpg.configure_item(active_window, show=False)


def close():
    dpg.stop_dearpygui()
    time.sleep(0.1)  # Fixed proper saving
