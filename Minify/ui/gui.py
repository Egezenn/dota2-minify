import concurrent.futures
import os
import threading

import dearpygui.dearpygui as ui
import jsonc
import screeninfo

# isort: split

import conditions
import helper
from core import base, constants, fs, log

from . import modal_shared

checkboxes = []
checkboxes_state = {}
gui_lock = False

terminal_window_wrap = constants.main_window_width - 10
tag_data_for_details_windows = []
mod_details_image_cache = {}

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

    with ui.texture_registry(tag="mod_images_registry", show=False):
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
        checkboxes_state[box] = ui.get_value(box)
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
                image_data = ui.load_image(img_p)
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
            always_val = fs.read_json_file(mod_cfg_path).get("always", False)

        if always_val:
            enable_ticking = False
            value = True
        else:
            enable_ticking = True
            value = checkboxes_state.get(mod, False)

        ui.add_group(parent="mod_menu", tag=f"{mod}_group_tag", horizontal=True, width=constants.main_window_width)
        ui.add_checkbox(
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
                ui.add_button(
                    parent=f"{mod}_group_tag",
                    small=True,
                    indent=constants.main_window_width - 150,
                    tag=f"{mod}_button_show_details_tag",
                    label=f"{helper.details_label}",
                    callback=show_details,
                    user_data=tag_data,
                )
                tag_data_for_details_windows.append(tag_data)
                ui.add_window(
                    tag=tag_data,
                    modal=True,
                    pos=(0, 0),
                    show=False,
                    label=mod,
                    no_resize=True,
                    no_move=True,
                    no_close=False,
                    no_collapse=True,
                    width=constants.main_window_width,
                    height=constants.main_window_height,
                )

                content_group = f"{mod}_details_content_group"
                with ui.group(parent=tag_data, tag=content_group):
                    pass

                if img_data:
                    try:
                        w, h, _, d = img_data
                        image_tag = f"{mod}_image_texture"
                        ui.add_static_texture(
                            width=w, height=h, default_value=d, tag=image_tag, parent="mod_images_registry"
                        )
                        mod_details_image_cache[mod] = (w, h, image_tag)
                    except Exception as e:
                        print(f"Failed to display image for {mod}: {e}")

                render_details_window(mod)

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
    ui.configure_item("button_patch", enabled=False)
    ui.configure_item("button_select_mods", enabled=False)
    ui.configure_item("button_uninstall", enabled=False)
    ui.configure_item("lang_select", enabled=False)
    ui.configure_item("output_select", enabled=False)


def unlock_interaction():
    global gui_lock
    gui_lock = False
    ui.configure_item("button_patch", enabled=True)
    ui.configure_item("button_select_mods", enabled=True)
    ui.configure_item("button_uninstall", enabled=True)
    ui.configure_item("lang_select", enabled=True)
    ui.configure_item("output_select", enabled=True)


def render_details_window(mod):
    content_group = f"{mod}_details_content_group"
    if not ui.does_item_exist(content_group):
        return

    ui.delete_item(content_group, children_only=True)

    try:
        window_width = ui.get_item_width("primary_window")
        window_height = ui.get_item_height("primary_window")
    except:
        window_width = constants.main_window_width
        window_height = constants.main_window_height

    avail_width = window_width - 40
    max_height = window_height - 50 - 20

    if mod in mod_details_image_cache:
        w, h, image_tag = mod_details_image_cache[mod]

        scale = min(1.0, avail_width / w, max_height / h) * 0.7
        display_w = int(w * scale)
        display_h = int(h * scale)

        ui.add_image(image_tag, width=display_w, height=display_h, parent=content_group)
        ui.add_separator(parent=content_group)

    mod_path = os.path.join(base.mods_dir, mod)
    text = helper.parse_markdown_notes(mod_path, helper.locale)

    container = f"{mod}_markdown_container"
    with ui.group(parent=content_group, tag=container):
        pass
    helper.render_markdown(container, text)


def show_details(sender, app_data, user_data):
    mod = user_data.replace("_details_window_tag", "")
    render_details_window(mod)
    ui.configure_item(user_data, show=True)
    ui.focus_item(user_data)


def start_text():
    for i in range(1, 6):
        helper.add_text_to_terminal(f"&start_text_{i}_var")
    ui.add_separator(parent="terminal_window")


def close_active_window():
    active_window = ui.get_item_alias(ui.get_active_window())
    if active_window not in [
        "terminal_window",
        "primary_window",
        "footer",
        "opener",
        "mod_tools",
        "maintenance_tools",
    ]:
        if active_window == "modal_popup":
            ui.configure_item("modal_popup", show=False)
            threading.Timer(0.1, modal_shared._show_next_modal_from_queue).start()
        else:
            ui.configure_item(active_window, show=False)
