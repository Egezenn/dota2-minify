"Settings menu"

import os

import dearpygui.dearpygui as dpg
from core import base, config, constants, steam

MOD_SETTINGS_WIDGETS = []

SETTINGS = [
    {
        "key": "steam_root",
        "text": "Steam Root",
        "default": "",
        "type": "inputbox",
    },
    {
        "key": "steam_library",
        "text": "Steam Library",
        "default": "",
        "type": "inputbox",
    },
    {
        "key": "output_path",
        "text": "Output Path",
        "default": "",
        "type": "inputbox",
    },
    {
        "key": "steam_id",
        "text": "Steam ID",
        "default": "",
        "type": "combo",
        "items_getter": steam.get_steam_accounts,
    },
    {
        "key": "opt_into_rcs",
        "text": "Opt into RCs",
        "default": False,
        "type": "checkbox",
    },
    {
        "key": "fix_options",
        "text": "Handle language option (current ID)",
        "default": True,
        "type": "checkbox",
    },
    {
        "key": "apply_for_all",
        "text": "Apply everything for all users",
        "default": True,
        "type": "checkbox",
    },
    {
        "key": "launch_dota_after_patch",
        "text": "Launch Dota2 after patching",
        "default": False,
        "type": "checkbox",
    },
    {
        "key": "kill_self_after_patch",
        "text": "Close Minify after patching",
        "default": False,
        "type": "checkbox",
    },
]


def save(sender=None, app_data=None, user_data=None):
    for opt in SETTINGS:
        val = dpg.get_value(f"opt_{opt['key']}")
        if opt["key"] == "steam_id" and val:
            val = val.split(" - ")[0]
        config.set(opt["key"], val)

    for widget in MOD_SETTINGS_WIDGETS:
        val = dpg.get_value(widget["tag"])
        mod_name = widget["mod_name"]
        setting_key = widget["key"]

        mod_data = config.get_mod(mod_name)
        mod_data[setting_key] = val
        config.set_mod(mod_name, mod_data)


def refresh(sender=None, app_data=None, user_data=None):
    render_menu()


def render_menu():
    global MOD_SETTINGS_WIDGETS
    MOD_SETTINGS_WIDGETS.clear()

    if dpg.does_item_exist("settings_content_group"):
        dpg.delete_item("settings_content_group", children_only=True)
    else:
        dpg.add_group(parent="settings_menu", tag="settings_content_group")

    for opt in SETTINGS:
        with dpg.group(horizontal=True, parent="settings_content_group"):
            _tag = f"opt_{opt['key']}"
            _text = opt.get("text") if opt["type"] == "checkbox" else f"{opt.get('text')}:"
            _default_value = config.get(opt["key"], opt["default"])

            if opt["type"] == "checkbox":
                dpg.add_checkbox(
                    tag=_tag,
                    label=_text,
                    default_value=_default_value,
                )
            elif opt["type"] == "combo":
                dpg.add_text(_text)
                raw_items = opt["items_getter"]() if "items_getter" in opt else []
                if raw_items and isinstance(raw_items[0], dict):
                    items = [f"{item['id']} - {item['name']}" for item in raw_items]
                else:
                    items = raw_items

                if opt["key"] == "steam_id" and _default_value:
                    for item in items:
                        if item.startswith(f"{_default_value} - "):
                            _default_value = item
                            break

                dpg.add_combo(
                    tag=_tag,
                    items=items,
                    default_value=_default_value,
                    width=-1,
                )
            else:
                dpg.add_text(_text)
                dpg.add_input_text(
                    tag=_tag,
                    default_value=_default_value,
                    width=-1,
                )

    mod_settings_found = False
    for mod in constants.visually_available_mods:
        mod_path = os.path.join(base.mods_dir, mod)
        if mod.endswith(".vpk"):
            continue

        mod_cfg_path = os.path.join(mod_path, "modcfg.json")
        mod_config = config.read_json_file(mod_cfg_path)

        if "settings" in mod_config:
            if not mod_settings_found:
                dpg.add_separator(parent="settings_content_group")
                dpg.add_text("Mod Settings", parent="settings_content_group")
                mod_settings_found = True

            dpg.add_text(f"{mod}:", parent="settings_content_group")

            saved_mod_data = config.get_mod(mod)
            for opt in mod_config["settings"]:
                _tag = f"mod_opt_{mod}_{opt['key']}"
                _text = opt.get("text") if opt["type"] == "checkbox" else f"{opt.get('text')}:"
                _default_value = saved_mod_data.get(opt["key"], opt.get("default", ""))

                with dpg.group(horizontal=True, parent="settings_content_group"):
                    if opt["type"] == "checkbox":
                        dpg.add_checkbox(
                            tag=_tag,
                            label=_text,
                            default_value=_default_value,
                        )
                    elif opt["type"] == "combo":
                        dpg.add_text(_text)
                        items = opt.get("items", [])
                        dpg.add_combo(
                            tag=_tag,
                            items=items,
                            default_value=_default_value,
                            width=-1,
                        )
                    else:
                        dpg.add_text(_text)
                        dpg.add_input_text(
                            tag=_tag,
                            default_value=_default_value,
                            width=-1,
                        )

                MOD_SETTINGS_WIDGETS.append({"tag": _tag, "mod_name": mod, "key": opt["key"]})
