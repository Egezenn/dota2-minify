# core.localization

Dynamic localization handling

## `load_headless()`

*No documentation available.*

<details open><summary>Source</summary>

```python
def load_headless():
    global localization_dict, locale
    locale = (config.get("locale") or "en").lower()
    localization_dict = _load_dict(base.locales_dir, locale)
    _merge_plugin_localizations(localization_dict, locale)
```

</details>

## `get_available()`

*No documentation available.*

<details open><summary>Source</summary>

```python
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
```

</details>

## `get_for_locale(lang)`

*No documentation available.*

<details open><summary>Source</summary>

```python
def get_for_locale(lang: str = "en") -> dict:
    lang = (lang or "en").lower()
    result = _load_dict(base.locales_dir, lang)
    _merge_plugin_localizations(result, lang)
    return result
```

</details>

## `get_for_plugin(plugin_id, lang)`

*No documentation available.*

<details open><summary>Source</summary>

```python
def get_for_plugin(plugin_id: str, lang: str = "en") -> dict:
    plugins_dir = getattr(base, "plugins_dir", None)
    if not plugins_dir:
        return {}
    p_locales = os.path.join(plugins_dir, plugin_id, "locales")
    return _load_dict(p_locales, (lang or "en").lower())
```

</details>
