"Dynamic localization handling"

import os

import jsonc

from core import base, config, utils

locale = ""
localization_dict = {}
localizations = []


def _load_dict(locales_dir: str, lang: str = "en") -> dict:
    if not locales_dir or not os.path.isdir(locales_dir):
        return {}
    result = {}
    # 1. Base English fallback
    en_file = os.path.join(locales_dir, "en.json")
    if os.path.isfile(en_file):
        try:
            with utils.open_utf8(en_file) as f:
                data = jsonc.load(f)
            if isinstance(data, dict):
                result.update(data)
        except Exception:
            pass

    # 2. Overlay target language
    lang = (lang or "en").lower()
    if lang != "en":
        target_file = os.path.join(locales_dir, f"{lang}.json")
        if os.path.isfile(target_file):
            try:
                with utils.open_utf8(target_file) as f:
                    data = jsonc.load(f)
                if isinstance(data, dict):
                    result.update(data)
            except Exception:
                pass

    return result


def _merge_plugin_localizations(target_dict: dict, lang: str = "en"):
    plugins_dir = getattr(base, "plugins_dir", None)
    if not plugins_dir or not os.path.isdir(plugins_dir):
        return
    for plugin_folder in sorted(os.listdir(plugins_dir)):
        p_locales = os.path.join(plugins_dir, plugin_folder, "locales")
        if os.path.isdir(p_locales):
            target_dict.update(_load_dict(p_locales, lang))


def load_headless():
    global localization_dict, locale
    locale = (config.get("locale") or "en").lower()
    localization_dict = _load_dict(base.locales_dir, locale)
    _merge_plugin_localizations(localization_dict, locale)


def get_available() -> list[str]:
    global localizations
    langs = set()
    if getattr(base, "locales_dir", None) and os.path.isdir(base.locales_dir):
        for fname in os.listdir(base.locales_dir):
            if fname.endswith(".json"):
                langs.add(fname[:-5].lower())

    plugins_dir = getattr(base, "plugins_dir", None)
    if plugins_dir and os.path.isdir(plugins_dir):
        for plugin_folder in sorted(os.listdir(plugins_dir)):
            p_loc = os.path.join(plugins_dir, plugin_folder, "locales")
            if os.path.isdir(p_loc):
                for fname in os.listdir(p_loc):
                    if fname.endswith(".json"):
                        langs.add(fname[:-5].lower())

    sorted_langs = sorted(l for l in langs if l != "en")
    localizations = ["en"] + sorted_langs if "en" in langs else sorted_langs
    return localizations


def get_for_locale(lang: str = "en") -> dict:
    lang = (lang or "en").lower()
    result = _load_dict(base.locales_dir, lang)
    _merge_plugin_localizations(result, lang)
    return result


def get_for_plugin(plugin_id: str, lang: str = "en") -> dict:
    plugins_dir = getattr(base, "plugins_dir", None)
    if not plugins_dir:
        return {}
    p_locales = os.path.join(plugins_dir, plugin_id, "locales")
    return _load_dict(p_locales, (lang or "en").lower())
