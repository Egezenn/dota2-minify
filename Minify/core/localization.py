"Dynamic localization handling"

import jsonc

from core import base, config, utils

locale = ""
localization_dict = {}
localizations = []


def load_headless():
    global localization_dict, locale
    with utils.open_utf8(base.localization_file_dir) as f:
        data = jsonc.load(f)
    locale = config.get("locale", "EN")
    for key, values in data.items():
        if isinstance(values, dict):
            localization_dict[key] = values.get(locale, values.get("EN", ""))
        else:
            localization_dict[key] = values


def get_available():
    global localizations
    with utils.open_utf8(base.localization_file_dir) as file:
        localization_data = jsonc.load(file)
    sub_headers = set()
    for header in localization_data.values():
        if isinstance(header, dict):
            sub_headers.update(header.keys())
    sorted_langs = sorted(lang for lang in sub_headers if lang != "EN")
    localizations = ["EN"] + sorted_langs

    for key, value in localization_data.items():
        if key.endswith("var") and isinstance(value, dict):
            localization_dict[key] = value.get("EN", "")
