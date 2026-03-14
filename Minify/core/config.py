"JSON(C) config files"

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


def get_config(key, default_value=None):
    "Get config value from the main config file with default and set the default onto config."
    data = read_json_file(base.main_config_file_dir)
    if key in data:
        return data[key]

    if default_value is not None:
        return update_json_file(base.main_config_file_dir, key, default_value)

    return None


def set_config(key, value):
    "Set config value for the main config file."
    return update_json_file(base.main_config_file_dir, key, value)


def get_mod_config(mod_name, default=None):
    "Get config value for mods."
    if default is None:
        default = {}
    return get_config("modconf", {}).get(mod_name, default)


def set_mod_config(mod_name, config_data):
    "Set config value for mods."
    modconf = get_config("modconf", {})
    modconf[mod_name] = config_data
    set_config("modconf", modconf)
