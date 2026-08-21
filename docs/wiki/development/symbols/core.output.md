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

## `add_text(text_or_id)`

*No documentation available.*

<details open><summary>Source</summary>

```python
def add_text(text_or_id, *args, msg_type: str | None = None, **kwargs):
    from core import localization

    text = text_or_id
    if text_or_id.startswith("&"):
        text = localization.localization_dict.get(text_or_id.replace("&", ""), text_or_id)

    if args:
        text = text.format(*args)

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
        try:
            listener(text, msg_type)
        except Exception:
            pass

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
        try:
            listener("-" * 50, "separator")
        except Exception:
            pass
```

</details>
