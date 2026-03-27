"AKA mod menu stuff"

import concurrent.futures
import os

import dearpygui.dearpygui as dpg
import jsonc
from core import base, config, constants, mods_shared

from ui import details, localization, settings, shared, terminal, theme

checkboxes = []
checkboxes_state = {}


def load():
    global checkboxes_state
    try:
        with open(base.mods_config_dir, encoding="utf-8") as file:
            checkboxes_state = jsonc.load(file)
    except FileNotFoundError:
        open(base.mods_config_dir, "w").close()


def save():
    for box in checkboxes:
        checkboxes_state[box] = dpg.get_value(box)
    with open(base.mods_config_dir, "w", encoding="utf-8") as file:
        jsonc.dump(checkboxes_state, file, indent=2)


def setup_state():
    # base mod is always enabled and is shown in the ui since it received details page

    # for box in checkboxes_state:
    #     if box in checkboxes and ui.get_value(box):
    #         ui.configure_item("button_patch", enabled=True)
    #         break
    #     else:
    #         ui.configure_item("button_patch", enabled=False)
    save()
    settings.refresh()


def show_details(sender, app_data, user_data):
    mod = user_data.replace("_details_window_tag", "")
    details.render_details_window(mod)
    dpg.configure_item(user_data, show=True)
    dpg.focus_item(user_data)


def refresh(sender=None, app_data=None, user_data=None):
    mods_shared.scan_mods()
    create()
    settings.refresh()
    terminal.add_text("&refreshed_mod_list")


def create():
    # Cleanup for reinitialization
    if dpg.does_item_exist("mod_menu"):
        dpg.delete_item("mod_menu", children_only=True)

    for window_tag in shared.tag_data_for_details_windows:
        if dpg.does_item_exist(window_tag):
            dpg.delete_item(window_tag)
    shared.tag_data_for_details_windows.clear()

    if dpg.does_item_exist("mod_images_registry"):
        dpg.delete_item("mod_images_registry", children_only=True)
    shared.mod_details_image_cache.clear()

    checkboxes.clear()

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
            callback=setup_state,
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
                dpg.bind_item_theme(tag_data, theme.settings_theme)

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
