# core.output

Agnostic output interface

## `register_listener(callback)`

*No documentation available.*

<details open><summary>Source</summary>

```python
def register_listener(callback):
    if callback not in _listeners:
        _listeners.append(callback)
```

</details>

## `unregister_listener(callback)`

*No documentation available.*

<details open><summary>Source</summary>

```python
def unregister_listener(callback):
    if callback in _listeners:
        _listeners.remove(callback)
```

</details>

## `register_download_listener(callback)`

*No documentation available.*

<details open><summary>Source</summary>

```python
def register_download_listener(callback):
    if callback not in _download_listeners:
        _download_listeners.append(callback)
```

</details>

## `unregister_download_listener(callback)`

*No documentation available.*

<details open><summary>Source</summary>

```python
def unregister_download_listener(callback):
    if callback in _download_listeners:
        _download_listeners.remove(callback)
```

</details>

## `emit_download_progress(task_id, name, downloaded_bytes, total_bytes, status, error)`

*No documentation available.*

<details open><summary>Source</summary>

```python
def emit_download_progress(
    task_id: str, name: str, downloaded_bytes: int, total_bytes: int, status: str, error: str | None = None
):
    data = {
        "id": task_id,
        "name": name,
        "downloaded_bytes": downloaded_bytes,
        "total_bytes": total_bytes,
        "status": status,
        "error": error,
    }
    for listener in list(_download_listeners):
        try:
            listener(data)
        except Exception:
            pass
```

</details>

## `add_text(text_or_id)`

*No documentation available.*

<details open><summary>Source</summary>

```python
def add_text(text_or_id, *args, msg_type: str | None = None, indent: bool = False, **kwargs):
    from core import localization

    text = text_or_id
    if text_or_id.startswith("&"):
        text = localization.localization_dict.get(text_or_id.replace("&", ""), text_or_id)

    if args:
        text = text.format(*args)

    if indent:
        indent_str = "   " if isinstance(indent, bool) else (" " * indent if isinstance(indent, int) else "   ")
        text = "\n".join(f"{indent_str}{line}" if line else "" for line in text.split("\n"))

    prefix = ""
    if msg_type == "error":
        prefix = f"{RED}"
    elif msg_type == "warning":
        prefix = f"{YELLOW}"
    elif msg_type == "success":
        prefix = f"{GREEN}"

    try:
        print(f"{prefix}{text}{RESET}")
    except UnicodeEncodeError:
        print(f"{prefix}{text.encode('ascii', 'replace').decode('ascii')}{RESET}")

    for listener in list(_listeners):
        listener(text, msg_type)

    return None
```

</details>

## `add_separator()`

*No documentation available.*

<details open><summary>Source</summary>

```python
def add_separator():
    print("-" * 50)
    for listener in list(_listeners):
        listener("", "separator")
```

</details>

## `clean()`

*No documentation available.*

<details open><summary>Source</summary>

```python
def clean():
    for listener in list(_listeners):
        try:
            listener("", "clear")
        except Exception:
            pass
```

</details>
