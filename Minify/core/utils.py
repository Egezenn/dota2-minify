import builtins
import contextlib
import functools
import json
import os
import re
import uuid
from typing import IO, Any

from core import base

_real_open = builtins.open


_MOD_STATES_FILE = os.path.join(base.cache_dir, ".mod_states.json")


def read_mod_states() -> dict:
    if os.path.exists(_MOD_STATES_FILE):
        try:
            with open_utf8R(_MOD_STATES_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def write_mod_states(states: dict) -> None:
    os.makedirs(base.cache_dir, exist_ok=True)
    with open_utf8R(_MOD_STATES_FILE, "w") as f:
        json.dump(states, f, indent=2)


def get_mod_state(mod_name: str, key: str, default=None):
    states = read_mod_states()
    mod_data = states.get(mod_name, {})
    if key not in mod_data and default is not None:
        states.setdefault(mod_name, {})[key] = default
        write_mod_states(states)
    return mod_data.get(key, default)


def set_mod_state(mod_name: str, key: str, value) -> None:
    states = read_mod_states()
    states.setdefault(mod_name, {})[key] = value
    write_mod_states(states)


def ignore_if_headless(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if base.HEADLESS:
            return None
        return func(*args, **kwargs)

    return wrapper


@contextlib.contextmanager
def try_pass():
    try:
        yield
    except Exception:
        pass


def open_utf8(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> IO[Any]:
    if "b" not in mode:
        kwargs.setdefault("encoding", "utf-8")
    return _real_open(file, mode, *args, **kwargs)


def open_utf8R(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> IO[Any]:
    if "b" not in mode:
        kwargs.setdefault("encoding", "utf-8")
        kwargs.setdefault("errors", "replace")
    return _real_open(file, mode, *args, **kwargs)


def hex_to_rgba(hex_str):
    try:
        hex_str = hex_str.lstrip("#")
        if len(hex_str) == 6:
            hex_str += "FF"
        elif len(hex_str) != 8:
            return [255, 255, 255, 255]
        return [int(hex_str[i : i + 2], 16) for i in (0, 2, 4, 6)]
    except (ValueError, IndexError, AttributeError):
        return [255, 255, 255, 255]


def rgba_to_hex(rgba):
    try:
        return "#{:02x}{:02x}{:02x}{:02x}".format(
            int(max(0, min(255, rgba[0]))),
            int(max(0, min(255, rgba[1]))),
            int(max(0, min(255, rgba[2]))),
            int(max(0, min(255, rgba[3]))),
        )
    except (TypeError, IndexError, ValueError):
        return "#ffffffff"


def parse_color(val):
    if isinstance(val, list):
        return val
    return hex_to_rgba(val if val and isinstance(val, str) else "#ffffffff")


def setup_system():
    import conditions
    import helper
    import browsers

    from core import fs, migrations, utils, localization

    localization.load_headless()
    conditions.is_dota_running("&error_please_close_dota_terminal", "error")
    conditions.is_compiler_found()
    conditions.resolve_dependencies()
    browsers.initialize()
    helper.bulk_exec_script("initial", False)


def sanitize_win_path(name):
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).rstrip(" .") or uuid.uuid4().hex[:8]


def _find_font_linux(font_name: str) -> str | None:
    import subprocess

    try:
        res = subprocess.run(["fc-match", "-f", "%{file}", font_name], capture_output=True, text=True, check=True)
        path = res.stdout.strip()
        if path and os.path.exists(path):
            return path
    except Exception:
        pass
    return None


def _normalize_filename(filename: str) -> str:
    stem = os.path.splitext(filename)[0]
    return stem.lower().replace(" ", "").replace("-", "").replace("_", "")


def find_system_font(font_name: str) -> str | None:
    normalized = font_name.lower().replace(" ", "").replace("-", "").replace("_", "")

    if base.is_win:
        windir = os.environ.get("windir", "C:\\Windows")
        font_dirs = [os.path.join(windir, "Fonts")]
    elif base.is_linux:
        result = _find_font_linux(font_name)
        if result:
            return result
        font_dirs = [
            "/usr/share/fonts",
            "/usr/local/share/fonts",
            os.path.expanduser("~/.fonts"),
            os.path.expanduser("~/.local/share/fonts"),
        ]
    elif base.is_mac:
        font_dirs = ["/System/Library/Fonts", "/Library/Fonts", os.path.expanduser("~/Library/Fonts")]
    else:
        return None

    for d in font_dirs:
        if not os.path.exists(d):
            continue
        for root, _, files in os.walk(d):
            for f in files:
                if f.lower().endswith((".ttf", ".otf")) and normalized in _normalize_filename(f):
                    return os.path.join(root, f)
    return None
