# ui.fonts

Font registrations with range hints

## `_find_font_linux(font_name)`

*No documentation available.*

<details open><summary>Source</summary>

```python
def _find_font_linux(font_name: str) -> str | None:
    try:
        result = subprocess.run(["fc-match", "-f", "%{file}", font_name], capture_output=True, text=True, check=True)
        if result.stdout and os.path.exists(result.stdout.strip()):
            return result.stdout.strip()
    except Exception:
        pass

    # fallback search in common directories
    common_dirs = [
        "/usr/share/fonts",
        "/usr/local/share/fonts",
        os.path.expanduser("~/.fonts"),
        os.path.expanduser("~/.local/share/fonts"),
    ]
    for d in common_dirs:
        for root, _, files in os.walk(d):
            if font_name in files:
                return os.path.join(root, font_name)
    return None

```

</details>

## `get_system_font(locale)`

*No documentation available.*

<details open><summary>Source</summary>

```python
def get_system_font(locale: str) -> str | None:
    fonts = SYSTEM_FONTS.get(locale, {}).get(base.OS, [])
    if not fonts:
        return None

    if base.OS == base.WIN:
        windir = os.environ.get("windir", "C:\\Windows")
        for font in fonts:
            path = os.path.join(windir, "Fonts", font)
            if os.path.exists(path):
                return path
    elif base.OS == base.MAC:
        font_dirs = ["/System/Library/Fonts", "/Library/Fonts", os.path.expanduser("~/Library/Fonts")]
        for font in fonts:
            for d in font_dirs:
                path = os.path.join(d, font)
                if os.path.exists(path):
                    return path
    elif base.OS == base.LINUX:
        for font in fonts:
            path = _find_font_linux(font)
            if path:
                return path

    return None

```

</details>

## `get_font_for_locale(locale)`

*No documentation available.*

<details open><summary>Source</summary>

```python
def get_font_for_locale(locale: str) -> str:
    # Use default Fira Mono for basic locales where it works fine
    default_font = os.path.join("bin", "FiraMono-Medium.ttf")

    # Check if we need a specific font for this locale
    if locale not in SYSTEM_FONTS:
        return default_font

    system_font = get_system_font(locale)
    if system_font:
        return system_font

    # Fallback to downloading
    url = NOTO_FONTS.get(locale)
    if not url:
        return default_font

    fs.create_dirs(base.cache_dir)
    filename = url.split("/")[-1]
    cached_font_path = os.path.join(base.cache_dir, f"{locale}_{filename}")

    if os.path.exists(cached_font_path):
        return cached_font_path

    log.write_warning(f"System font for {locale} not found. Downloading fallback font...")
    success = fs.download_file(url, cached_font_path)
    if success:
        return cached_font_path

    return default_font

```

</details>

## `register(locale)`

*No documentation available.*

<details open><summary>Source</summary>

```python
def register(locale: str = "EN"):
    locale_lower = locale.lower()
    target_font = get_font_for_locale(locale_lower)
    if not os.path.exists(target_font):
        target_font = os.path.join("bin", "FiraMono-Medium.ttf")

    # works if you just use the language with that specific font at init
    # not if you change it afterwards, it doesnt recalculate the hints
    import warnings

    warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*add_font_range_hint.*")

    def apply_hints():
        import sys
        import io

        # DPG forcefully prints this warning, bypassing warnings.filterwarnings.
        # We must temporarily redirect stderr to silence it completely.
        original_stderr = sys.stderr
        sys.stderr = io.StringIO()
        try:
            if locale_lower in ["ja", "japanese"]:
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Japanese)
            elif locale_lower in ["ko", "koreana"]:
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Korean)
            elif locale_lower in ["zh-cn", "schinese"]:
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Chinese_Simplified_Common)
            elif locale_lower in ["zh-tw", "tchinese"]:
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Chinese_Full)
            elif locale_lower in ["th", "thai"]:
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Thai)
            elif locale_lower in ["vi", "vietnamese"]:
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Vietnamese)
            elif locale_lower in ["ru", "russian", "uk", "ukrainian", "bg", "bulgarian"]:
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
        finally:
            sys.stderr = original_stderr

    with dpg.font_registry():
        fira_font_path = os.path.join("bin", "FiraMono-Medium.ttf")
        with dpg.font(fira_font_path, 14, tag="banner_font"):
            pass

        with dpg.font(target_font, 16, tag="main_font") as main_font:
            apply_hints()
            dpg.bind_font(main_font)

        with dpg.font(target_font, 14, tag="small_font"):
            apply_hints()
        with dpg.font(target_font, 20, tag="large_font"):
            apply_hints()
        with dpg.font(target_font, 32, tag="very_large_font"):
            apply_hints()

```

</details>
