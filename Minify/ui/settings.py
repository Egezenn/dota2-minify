"Settings menu"

import os

import dearpygui.dearpygui as dpg
import helper
from core import base, config, constants, steam, utils


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
MOD_SETTINGS_WIDGETS = []


def save(sender=None, app_data=None, user_data=None):
    for opt in SETTINGS:
        val = dpg.get_value(f"opt_{opt['key']}")
        if opt["key"] == "steam_id" and val:
            val = val.split(" - ")[0]
        config.set(opt["key"], val)

    for widget in MOD_SETTINGS_WIDGETS:
        if widget.get("type") == "button":
            continue
        tag = widget["tag"]
        mod_name = widget["mod_name"]
        setting_key = widget["key"]
        widget_type = widget["type"]

        if widget_type == "list":
            val = dpg.get_item_configuration(tag)["items"]
        elif widget_type == "color":
            val = dpg.get_value(tag)
        else:
            val = dpg.get_value(tag)

        mod_data = config.get_mod(mod_name)
        mod_data[setting_key] = val
        config.set_mod(mod_name, mod_data)


def handle_button_click(sender, app_data, user_data):
    mod_name = user_data["mod_name"]
    function_name = user_data["key"]
    script_path = os.path.join(base.mods_dir, mod_name, "script_utility.py")
    helper.exec_script_function(script_path, mod_name, function_name)


def refresh(sender=None, app_data=None, user_data=None):
    render_menu()


def reset(sender=None, app_data=None, user_data=None):
    config.set("modconf", {})
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
    for mod in constants.mods_alphabetical:
        mod_path = os.path.join(base.mods_dir, mod)
        if mod.endswith(".vpk"):
            continue

        mod_cfg_path = os.path.join(mod_path, "modcfg.json")
        mod_config = config.read_json_file(mod_cfg_path)

        always = mod_config.get("always", False)
        utility = mod_config.get("utility", False)

        if "settings" in mod_config and (always or utility or (dpg.does_item_exist(mod) and dpg.get_value(mod))):
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
                    elif opt["type"] == "number":
                        dpg.add_text(_text)
                        var_type = opt.get("var_type", "int")
                        if var_type == "float":
                            dpg.add_input_float(
                                tag=_tag,
                                default_value=float(_default_value) if _default_value else 0.0,
                                step=opt.get("step", 0.1),
                                width=-1,
                            )
                        else:
                            dpg.add_input_int(
                                tag=_tag,
                                default_value=int(_default_value) if _default_value else 0,
                                step=opt.get("step", 1),
                                width=-1,
                            )
                    elif opt["type"] == "slider":
                        dpg.add_text(_text)
                        var_type = opt.get("var_type", "int")
                        min_val = opt.get("min", 0)
                        max_val = opt.get("max", 100)
                        step = opt.get("step")
                        _callback = snap_slider if step else None
                        _user_data = {"step": step} if step else None
                        if var_type == "float":
                            dpg.add_slider_float(
                                tag=_tag,
                                default_value=float(_default_value) if _default_value else 0.0,
                                min_value=float(min_val),
                                max_value=float(max_val),
                                width=-1,
                                callback=_callback,
                                user_data=_user_data,
                            )
                        else:
                            dpg.add_slider_int(
                                tag=_tag,
                                default_value=int(_default_value) if _default_value else 0,
                                min_value=int(min_val),
                                max_value=int(max_val),
                                width=-1,
                                callback=_callback,
                                user_data=_user_data,
                            )
                    elif opt["type"] == "color":
                        dpg.add_text(_text)
                        with dpg.group(horizontal=True):
                            dpg.add_input_text(
                                tag=_tag,
                                default_value=(
                                    _default_value
                                    if isinstance(_default_value, str)
                                    else utils.rgba_to_hex(_default_value)
                                ),
                                width=-120,
                                callback=lambda s, a, u: dpg.set_value(u, utils.hex_to_rgba(a)),
                                user_data=f"{_tag}_preview",
                            )
                            dpg.add_color_button(
                                tag=f"{_tag}_preview",
                                default_value=utils.parse_color(_default_value),
                            )
                    elif opt["type"] == "list":
                        with dpg.group(horizontal=False):
                            dpg.add_text(_text)
                            items = _default_value if isinstance(_default_value, list) else []
                            dpg.add_listbox(tag=_tag, items=items, width=-1, num_items=5)
                            with dpg.group(horizontal=True):
                                input_tag = f"{_tag}_input"
                                dpg.add_input_text(tag=input_tag, width=-130)
                                dpg.add_button(
                                    label="Add",
                                    width=60,
                                    callback=add_to_list,
                                    user_data={"listbox_tag": _tag, "input_tag": input_tag},
                                )
                                dpg.add_button(
                                    label="Remove",
                                    width=60,
                                    callback=remove_from_list,
                                    user_data={"listbox_tag": _tag},
                                )

                    elif opt["type"] == "button":
                        dpg.add_button(
                            tag=_tag,
                            label=opt.get("text", opt["key"]),
                            callback=handle_button_click,
                            user_data={"mod_name": mod, "key": opt["key"]},
                            width=-1,
                        )
                    else:
                        dpg.add_text(_text)
                        dpg.add_input_text(
                            tag=_tag,
                            default_value=_default_value,
                            width=-1,
                        )

                MOD_SETTINGS_WIDGETS.append({"tag": _tag, "mod_name": mod, "key": opt["key"], "type": opt["type"]})


def add_to_list(sender, app_data, user_data):
    listbox_tag = user_data["listbox_tag"]
    input_tag = user_data["input_tag"]
    new_item = dpg.get_value(input_tag)
    if new_item:
        items = dpg.get_item_configuration(listbox_tag)["items"]
        if new_item not in items:
            items.append(new_item)
            dpg.configure_item(listbox_tag, items=items)
            dpg.set_value(input_tag, "")


def remove_from_list(sender, app_data, user_data):
    listbox_tag = user_data["listbox_tag"]
    selected_item = dpg.get_value(listbox_tag)
    if selected_item:
        items = dpg.get_item_configuration(listbox_tag)["items"]
        if selected_item in items:
            items.remove(selected_item)
            dpg.configure_item(listbox_tag, items=items)


def snap_slider(sender, app_data, user_data):
    step = user_data.get("step")
    if step:
        step = float(step)
        snapped_val = round(app_data / step) * step
        dpg.set_value(sender, snapped_val)
