import builtins
import contextlib
from typing import IO, Any

_real_open = builtins.open


@contextlib.contextmanager
def try_pass():
    try:
        yield
    except Exception:
        pass


def is_version_at_least(current: str, target: str) -> bool:
    """
    Compares two semantic version strings.
    Returns True if current >= target.
    """
    try:
        c = tuple(map(int, current.split(".")))
        t = tuple(map(int, target.split(".")))
        return c >= t
    except (ValueError, AttributeError, IndexError):
        return False


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
