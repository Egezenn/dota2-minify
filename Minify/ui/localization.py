"Dynamic localization handling"

import os

import dearpygui.dearpygui as dpg
import jsonc
from core import base, config, constants, utils

from ui import markdown, shared

locale = ""
localization_dict = {}
localizations = []
details_label = ""
mod_selection_window_var = ""


def get_available():
    global localizations
    # get available variables for text
    with utils.open_utf8(base.localization_file_dir) as file:
        localization_data = jsonc.load(file)
    sub_headers = set()
    for header in localization_data.values():
        if isinstance(header, dict):
            sub_headers.update(header.keys())
    sorted_langs = sorted(lang for lang in sub_headers if lang != "EN")
    localizations = ["EN"] + sorted_langs

    for key, value in localization_data.items():
        if key.endswith("var"):
            localization_dict[key] = value["EN"]


def change(sender=None, app_data=None, user_data=None, init=False):
    global locale, details_label, mod_selection_window_var

    with utils.open_utf8(base.localization_file_dir) as localization_file:
        localization_data = jsonc.load(localization_file)

    if init == True:  # noqa: E712
        locale = config.get("locale", dpg.get_value("lang_select"))
        if locale is None:
            locale = config.set("locale", dpg.get_value("lang_select"))
        dpg.configure_item("lang_select", default_value=locale)
    else:
        locale = dpg.get_value("lang_select")
        config.set("locale", locale)

    for key, values in localization_data.items():
        text = values.get(locale, values.get("EN", ""))
        localization_dict[key] = text

        if dpg.does_item_exist(key):
            item_type = dpg.get_item_info(key).get("type")
            if item_type in [
                "mvAppItemType::mvText",
                "mvAppItemType::mvInputText",
                "mvAppItemType::mvInputInt",
            ]:
                # For input/text items, set value
                dpg.set_value(key, text)
            else:
                # For buttons, menus, etc., set label
                dpg.configure_item(key, label=text)

    # Update terminal history
    for item in shared.terminal_history:
        if dpg.does_item_exist(item["id"]):
            key_data = localization_data.get(item["key"])
            if key_data:
                new_text = key_data.get(locale, key_data.get("EN", item["key"]))
            else:
                new_text = item["key"]

            if item["args"]:
                with utils.try_pass():
                    new_text = new_text.format(*item["args"])
            dpg.set_value(item["id"], new_text)

    # Re-render markdown for available mods
    for mod in constants.visually_available_mods:
        container = f"{mod}_markdown_container"
        if dpg.does_item_exist(container):
            mod_path = os.path.join(base.mods_dir, mod)
            text = markdown.parse_notes(mod_path, locale)
            dpg.delete_item(container, children_only=True)
            markdown.render(container, text, width=base.main_window_width)

    # Update dynamic detail buttons
    details_label = localization_data.get("details_button_label_var", {}).get(
        locale, localization_data["details_button_label_var"]["EN"]
    )
    mod_selection_window_var = localization_data.get("mod_selection_window_var", {}).get(
        locale, localization_data["mod_selection_window_var"]["EN"]
    )

    if dpg.does_item_exist("mod_menu"):
        dpg.configure_item("mod_menu", label=mod_selection_window_var)
        for child_group in dpg.get_item_children("mod_menu", 1):
            for item in dpg.get_item_children(child_group, 1):
                if dpg.get_item_alias(item).endswith("_button_show_details_tag"):
                    dpg.configure_item(item, label=details_label)

    if not init:
        # User changed locale on the fly. Since DPG does not support hot-reloading main_font
        # nicely without a context rebuild, we will prompt the user to restart if they are switching
        # to/from a non-latin locale. (As the font won't render Chinese/Korean characters correctly).
        from ui import modal_shared

        warning_text = "You might need to restart the application for the font to change completely."
        modal_shared.show("Warning", [warning_text], [{"label": "OK"}])
