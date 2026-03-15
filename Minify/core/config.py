"""
JSON(C) config files

Interactions with main config and mod configs
"""

import jsonc

from core import base


def read_json_file(path):
    try:
        with open(path, encoding="utf-8") as file:
            return jsonc.load(file)
    except (FileNotFoundError, jsonc.JSONDecodeError):
        return {}


def write_json_file(path, data):
    with open(path, "w", encoding="utf-8") as file:
        jsonc.dump(data, file, indent=2)


def update_json_file(path, key, value):
    data = read_json_file(path)
    data[key] = value
    write_json_file(path, data)
    return value


def get(key, default_value=None):
    data = read_json_file(base.main_config_file_dir)
    if key in data:
        return data[key]

    if default_value is not None:
        return update_json_file(base.main_config_file_dir, key, default_value)

    return None


def set(key, value):
    return update_json_file(base.main_config_file_dir, key, value)


def get_mod(mod_name, default=None):
    if default is None:
        default = {}
    return get("modconf", {}).get(mod_name, default)


def set_mod(mod_name, config_data):
    modconf = get("modconf", {})
    modconf[mod_name] = config_data
    set("modconf", modconf)
