import builtins
import contextlib
from unittest.mock import patch

from typing import Any, IO, Iterator, Optional

_real_open = builtins.open


@contextlib.contextmanager
def try_pass():
    try:
        yield
    except Exception:
        pass


@contextlib.contextmanager
def _patch_open_base(
    encoding_val: Optional[str],
    errors_val: Optional[str],
    file: Any,
    mode: str,
    *args: Any,
    **kwargs: Any,
) -> Iterator[Any]:
    if "b" not in mode:
        if encoding_val:
            kwargs.setdefault("encoding", encoding_val)
        if errors_val:
            kwargs.setdefault("errors", errors_val)

    def _patch_open(f, m="r", *a, **kw):
        if "b" not in m:
            if encoding_val:
                kw.setdefault("encoding", encoding_val)
            if errors_val:
                kw.setdefault("errors", errors_val)
        return _real_open(f, m, *a, **kw)

    with patch("builtins.open", _patch_open):
        if file is not None:
            with _real_open(file, mode, *args, **kwargs) as f:
                yield f
        else:
            yield


@contextlib.contextmanager
def open_utf8(file: Any = None, mode: str = "r", *args: Any, **kwargs: Any) -> Iterator[IO[Any]]:
    with _patch_open_base("utf-8", None, file, mode, *args, **kwargs) as f:
        yield f


@contextlib.contextmanager
def open_utf8R(file: Any = None, mode: str = "r", *args: Any, **kwargs: Any) -> Iterator[IO[Any]]:
    with _patch_open_base("utf-8", "replace", file, mode, *args, **kwargs) as f:
        yield f


def hex_to_rgba(hex_str):
    try:
        hex_str = hex_str.lstrip("#")
        if len(hex_str) == 6:
            hex_str += "FF"
        return [int(hex_str[i : i + 2], 16) for i in (0, 2, 4, 6)]
    except (ValueError, IndexError):
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
