"Font registrations with range hints"

import os
import subprocess

import dearpygui.dearpygui as dpg

from core import base, fs, log

# Map of locales to preferred system fonts per OS
# DPG font loader requires TTF or OTF files.
# Locales like EN, ES, FR, DE mostly use the default FiraMono font correctly.
# The issue primarily affects CJK (Chinese, Japanese, Korean) and some extended scripts.

# Noto URLs (Variable fonts or specific weights if variable is not supported well, we use regular TTF/OTF)
# Note: Locales refer to the ISO codes or internal codes matching localization.json
NOTO_FONTS = {
    "koreana": "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/Korean/NotoSansCJKkr-Regular.otf",
    "schinese": "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf",
    "tchinese": "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/TraditionalChinese/NotoSansCJKtc-Regular.otf",
    "japanese": "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansCJKjp-Regular.otf",
    "russian": "https://github.com/notofonts/notofonts.github.io/raw/main/fonts/NotoSans/hinted/ttf/NotoSans-Regular.ttf",
    "ru": "https://github.com/notofonts/notofonts.github.io/raw/main/fonts/NotoSans/hinted/ttf/NotoSans-Regular.ttf",
    "ukrainian": "https://github.com/notofonts/notofonts.github.io/raw/main/fonts/NotoSans/hinted/ttf/NotoSans-Regular.ttf",
    "uk": "https://github.com/notofonts/notofonts.github.io/raw/main/fonts/NotoSans/hinted/ttf/NotoSans-Regular.ttf",
    "bulgarian": "https://github.com/notofonts/notofonts.github.io/raw/main/fonts/NotoSans/hinted/ttf/NotoSans-Regular.ttf",
    "bg": "https://github.com/notofonts/notofonts.github.io/raw/main/fonts/NotoSans/hinted/ttf/NotoSans-Regular.ttf",
    "thai": "https://github.com/notofonts/notofonts.github.io/raw/main/fonts/NotoSansThai/hinted/ttf/NotoSansThai-Regular.ttf",
    "th": "https://github.com/notofonts/notofonts.github.io/raw/main/fonts/NotoSansThai/hinted/ttf/NotoSansThai-Regular.ttf",
    "vietnamese": "https://github.com/notofonts/notofonts.github.io/raw/main/fonts/NotoSans/hinted/ttf/NotoSans-Regular.ttf",
    "vi": "https://github.com/notofonts/notofonts.github.io/raw/main/fonts/NotoSans/hinted/ttf/NotoSans-Regular.ttf",
}

SYSTEM_FONTS = {
    "koreana": {
        "Windows": ["malgun.ttf", "batang.ttc"],
        "Darwin": ["AppleGothic.ttf", "AppleMyungjo.ttf"],
        "Linux": ["NotoSansCJK-Regular.ttc", "NotoSansCJKkr-Regular.otf", "UnDotum.ttf", "NanumGothic.ttf"],
    },
    "schinese": {
        "Windows": ["msyh.ttc", "simsun.ttc", "simhei.ttf"],
        "Darwin": ["PingFang.ttc", "STHeiti Light.ttc"],
        "Linux": ["NotoSansCJK-Regular.ttc", "NotoSansCJKsc-Regular.otf", "wqy-microhei.ttc"],
    },
    "tchinese": {
        "Windows": ["msjh.ttc", "mingliu.ttc"],
        "Darwin": ["PingFang.ttc", "STHeiti Light.ttc"],
        "Linux": ["NotoSansCJK-Regular.ttc", "NotoSansCJKtc-Regular.otf"],
    },
    "japanese": {
        "Windows": ["meiryo.ttc", "msgothic.ttc"],
        "Darwin": ["Hiragino Sans GB.ttc", "AppleGothic.ttf"],
        "Linux": ["NotoSansCJK-Regular.ttc", "NotoSansCJKjp-Regular.otf", "TakaoPGothic.ttf"],
    },
    "russian": {
        "Windows": ["arial.ttf", "times.ttf"],
        "Darwin": ["Arial.ttf"],
        "Linux": ["DejaVuSans.ttf", "LiberationSans-Regular.ttf", "NotoSans-Regular.ttf"],
    },
    "ru": {
        "Windows": ["arial.ttf", "times.ttf"],
        "Darwin": ["Arial.ttf"],
        "Linux": ["DejaVuSans.ttf", "LiberationSans-Regular.ttf", "NotoSans-Regular.ttf"],
    },
    "ukrainian": {
        "Windows": ["arial.ttf", "times.ttf"],
        "Darwin": ["Arial.ttf"],
        "Linux": ["DejaVuSans.ttf", "LiberationSans-Regular.ttf", "NotoSans-Regular.ttf"],
    },
    "uk": {
        "Windows": ["arial.ttf", "times.ttf"],
        "Darwin": ["Arial.ttf"],
        "Linux": ["DejaVuSans.ttf", "LiberationSans-Regular.ttf", "NotoSans-Regular.ttf"],
    },
    "bulgarian": {
        "Windows": ["arial.ttf", "times.ttf"],
        "Darwin": ["Arial.ttf"],
        "Linux": ["DejaVuSans.ttf", "LiberationSans-Regular.ttf", "NotoSans-Regular.ttf"],
    },
    "bg": {
        "Windows": ["arial.ttf", "times.ttf"],
        "Darwin": ["Arial.ttf"],
        "Linux": ["DejaVuSans.ttf", "LiberationSans-Regular.ttf", "NotoSans-Regular.ttf"],
    },
    "thai": {
        "Windows": ["tahoma.ttf", "leelawad.ttf"],
        "Darwin": ["Thonburi.ttf", "Ayuthaya.ttf"],
        "Linux": ["Kinnari.ttf", "Norasi.ttf", "NotoSansThai-Regular.ttf"],
    },
    "th": {
        "Windows": ["tahoma.ttf", "leelawad.ttf"],
        "Darwin": ["Thonburi.ttf", "Ayuthaya.ttf"],
        "Linux": ["Kinnari.ttf", "Norasi.ttf", "NotoSansThai-Regular.ttf"],
    },
    "vietnamese": {
        "Windows": ["arial.ttf", "times.ttf"],
        "Darwin": ["Arial.ttf"],
        "Linux": ["DejaVuSans.ttf", "LiberationSans-Regular.ttf", "NotoSans-Regular.ttf"],
    },
    "vi": {
        "Windows": ["arial.ttf", "times.ttf"],
        "Darwin": ["Arial.ttf"],
        "Linux": ["DejaVuSans.ttf", "LiberationSans-Regular.ttf", "NotoSans-Regular.ttf"],
    },
}


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


def register(locale: str = "EN"):
    target_font = get_font_for_locale(locale.lower())
    if not os.path.exists(target_font):
        target_font = os.path.join("bin", "FiraMono-Medium.ttf")

    with dpg.font_registry():
        with dpg.font(target_font, 16, tag="main_font") as main_font:
            dpg.bind_font(main_font)

        dpg.font(target_font, 14, tag="small_font")
        dpg.font(target_font, 20, tag="large_font")
        dpg.font(target_font, 32, tag="very_large_font")
