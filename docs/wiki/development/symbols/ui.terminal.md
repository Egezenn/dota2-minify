# ui.terminal

Text waterfall

## `scroll_to_end()`

*No documentation available.*

<details open><summary>Source</summary>

```python
def scroll_to_end():
    time.sleep(0.05)
    dpg.set_y_scroll("terminal_window", dpg.get_y_scroll_max("terminal_window"))

```

</details>

## `add_text(text_or_id)`

*No documentation available.*

<details open><summary>Source</summary>

```python
def add_text(text_or_id, *args, msg_type: str | None = None, **kwargs):
    from ui import localization

    if text_or_id.startswith("&"):
        text = localization.localization_dict.get(text_or_id.replace("&", ""), text_or_id)
    else:
        text = text_or_id

    if args:
        text = text.format(*args)

    if msg_type is not None:
        if msg_type == "error":
            color = (255, 0, 0)
        elif msg_type == "warning":
            color = (255, 255, 0)
        elif msg_type == "success":
            color = (0, 255, 0)
        else:
            color = (0, 230, 230)
        kwargs["color"] = color

    item = dpg.add_text(default_value=text, parent="terminal_window", wrap=wrap_size, indent=10, **kwargs)
    shared.terminal_history.append({"id": item, "key": text_or_id.replace("&", ""), "args": args})
    scroll_to_end()
    return item

```

</details>

## `add_seperator()`

*No documentation available.*

<details open><summary>Source</summary>

```python
def add_seperator():
    dpg.add_separator(parent="terminal_window")

```

</details>

## `clean()`

*No documentation available.*

<details open><summary>Source</summary>

```python
def clean():
    dpg.delete_item("terminal_window", children_only=True)
    shared.terminal_history.clear()

```

</details>
