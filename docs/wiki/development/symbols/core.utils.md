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

## `_parse_version(v)`

*No documentation available.*

<details open><summary>Source</summary>

```python
def _parse_version(v: str) -> tuple:
    parts = []
    for part in str(v).split("."):
        match = re.match(r"^(\d+)(.*)$", part)
        if match:
            num = int(match.group(1))
            suffix = match.group(2)
            if suffix:
                if suffix.startswith("rc"):
                    rc_num = suffix[2:]
                    parts.append((num, -1, int(rc_num) if rc_num.isdigit() else 0))
                else:
                    parts.append((num, -2, 0))
            else:
                parts.append((num, 0, 0))
        else:
            raise ValueError(f"Invalid version string part: {part}")
    # Pad to handle cases like "1.13" vs "1.13.0"
    while len(parts) < 4:
        parts.append((0, 0, 0))
    return tuple(parts)

```

</details>

## `is_version_at_least(current, requirements)`

Compares current version against a requirement string (e.g., ">=1.13,<=1.14" or "1.13").
If no operator is provided, defaults to ">=".

<details open><summary>Source</summary>

```python
def is_version_at_least(current: str, requirements: str) -> bool:
    """
    Compares current version against a requirement string (e.g., ">=1.13,<=1.14" or "1.13").
    If no operator is provided, defaults to ">=".
    """
    try:
        if current is None or requirements is None:
            return False

        current_v = _parse_version(current)
        reqs = [r.strip() for r in requirements.split(",") if r.strip()]

        for req in reqs:
            match = re.match(r"^(>=|<=|>|<|==|=)?\s*(.+)$", req)
            if not match:
                return False

            op = match.group(1) or ">="
            target_v = _parse_version(match.group(2))

            if op == ">=":
                if not (current_v >= target_v):
                    return False
            elif op == "<=":
                if not (current_v <= target_v):
                    return False
            elif op == ">":
                if not (current_v > target_v):
                    return False
            elif op == "<":
                if not (current_v < target_v):
                    return False
            elif op in ("==", "="):
                if not (current_v == target_v):
                    return False

        return True
    except (ValueError, AttributeError, IndexError, TypeError):
        return False

```

</details>

## `open_utf8(file, mode)`

*No documentation available.*

<details open><summary>Source</summary>

```python
def open_utf8(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> IO[Any]:
    if "b" not in mode:
        kwargs.setdefault("encoding", "utf-8")
    return _real_open(file, mode, *args, **kwargs)

```

</details>

## `open_utf8R(file, mode)`

*No documentation available.*

<details open><summary>Source</summary>

```python
def open_utf8R(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> IO[Any]:
    if "b" not in mode:
        kwargs.setdefault("encoding", "utf-8")
        kwargs.setdefault("errors", "replace")
    return _real_open(file, mode, *args, **kwargs)

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
        elif len(hex_str) != 8:
            return [255, 255, 255, 255]
        return [int(hex_str[i : i + 2], 16) for i in (0, 2, 4, 6)]
    except (ValueError, IndexError, AttributeError):
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
