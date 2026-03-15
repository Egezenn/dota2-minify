"Settings menu"

import dearpygui.dearpygui as dpg
from core import config, steam

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
        "key": "change_options_for_all",
        "text": "Change language option for all IDs",
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


def refresh(sender=None, app_data=None, user_data=None):
    for opt in SETTINGS:
        if opt["type"] == "combo" and "items_getter" in opt:
            raw_items = opt["items_getter"]()
            if raw_items and isinstance(raw_items[0], dict):
                items = [f"{item['id']} - {item['name']}" for item in raw_items]
            else:
                items = raw_items
            dpg.configure_item(f"opt_{opt['key']}", items=items)

        val = config.get(opt["key"], opt["default"])

        if opt["type"] == "combo" and val:
            current_items = dpg.get_item_configuration(f"opt_{opt['key']}")["items"]
            for item in current_items:
                if item.startswith(f"{val} - "):
                    val = item
                    break

        dpg.set_value(f"opt_{opt['key']}", val)


def render_menu():
    for opt in SETTINGS:
        with dpg.group(horizontal=True, parent="settings_menu"):
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
