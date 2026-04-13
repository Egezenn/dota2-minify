# core.utils

## `try_pass()`

*No documentation available.*

<details open><summary>Source</summary>

```python
def try_pass():
    try:
        yield
    except Exception:
        pass

```

</details>

## `is_version_at_least(current, target)`

Compares two semantic version strings.
Returns True if current >= target.

<details open><summary>Source</summary>

```python
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

```

</details>

## `_patch_open_base(encoding_val, errors_val, file, mode)`

*No documentation available.*

<details open><summary>Source</summary>

```python
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

```

</details>

## `open_utf8(file, mode)`

*No documentation available.*

<details open><summary>Source</summary>

```python
def open_utf8(file: Any = None, mode: str = "r", *args: Any, **kwargs: Any) -> Iterator[IO[Any]]:
    with _patch_open_base("utf-8", None, file, mode, *args, **kwargs) as f:
        yield f

```

</details>

## `open_utf8R(file, mode)`

*No documentation available.*

<details open><summary>Source</summary>

```python
def open_utf8R(file: Any = None, mode: str = "r", *args: Any, **kwargs: Any) -> Iterator[IO[Any]]:
    with _patch_open_base("utf-8", "replace", file, mode, *args, **kwargs) as f:
        yield f

```

</details>

## `hex_to_rgba(hex_str)`

*No documentation available.*

<details open><summary>Source</summary>

```python
def hex_to_rgba(hex_str):
    try:
        hex_str = hex_str.lstrip("#")
        if len(hex_str) == 6:
            hex_str += "FF"
        return [int(hex_str[i : i + 2], 16) for i in (0, 2, 4, 6)]
    except (ValueError, IndexError):
        return [255, 255, 255, 255]

```

</details>

## `rgba_to_hex(rgba)`

*No documentation available.*

<details open><summary>Source</summary>

```python
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

```

</details>

## `parse_color(val)`

*No documentation available.*

<details open><summary>Source</summary>

```python
def parse_color(val):
    if isinstance(val, list):
        return val
    return hex_to_rgba(val if val and isinstance(val, str) else "#ffffffff")

```

</details>
