"""
JSON(C) config files

Interactions with main config and mod configs
"""

from typing import Any, Optional

import jsonc

from core import base, utils


def read_json_file(path: str) -> dict:
    try:
        with utils.open_utf8R(path) as file:
            return jsonc.load(file)
    except (FileNotFoundError, jsonc.JSONDecodeError):
        return {}


def write_json_file(path: str, data: dict) -> None:
    with utils.open_utf8R(path, "w") as file:
        jsonc.dump(data, file, indent=2)


_main_config_cache: dict | None = None


def update_json_file(path: str, key: str, value: Any) -> Any:
    global _main_config_cache

    data = read_json_file(path)
    data[key] = value
    write_json_file(path, data)

    if path == base.main_config_file_dir:
        if _main_config_cache is not None:
            _main_config_cache[key] = value
        else:
            _main_config_cache = data

    return value


def get(key: str, default_value: Any = None) -> Any:
    global _main_config_cache

    if _main_config_cache is None:
        _main_config_cache = read_json_file(base.main_config_file_dir)

    if key in _main_config_cache:
        return _main_config_cache[key]

    if default_value is not None:
        return update_json_file(base.main_config_file_dir, key, default_value)

    return None


def set(key: str, value: Any) -> Any:
    return update_json_file(base.main_config_file_dir, key, value)


def get_mod(mod_name: str, default: Optional[dict] = None) -> dict:
    if default is None:
        default = {}
    return get("modconf", {}).get(mod_name, default)


def set_mod(mod_name: str, config_data: dict) -> None:
    modconf = get("modconf", {})
    modconf[mod_name] = config_data
    set("modconf", modconf)
