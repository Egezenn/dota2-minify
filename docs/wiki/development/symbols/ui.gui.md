# ui.gui

## `initiate_conditionals()`

*No documentation available.*

<details open><summary>Source</summary>

```python
def initiate_conditionals():
    setup_system_thread = threading.Thread(target=setup_system)
    load_state_checkboxes_thread = threading.Thread(target=checkboxes.load)
    setup_system_thread.start()
    load_state_checkboxes_thread.start()
    setup_system_thread.join()
    load_state_checkboxes_thread.join()

    with dpg.texture_registry(tag="mod_images_registry", show=False):
        pass

    checkboxes.create()

```

</details>

## `setup_system()`

*No documentation available.*

<details open><summary>Source</summary>

```python
def setup_system():
    fs.create_dirs(base.logs_dir)
    conditions.is_dota_running("&error_please_close_dota_terminal", "error")
    conditions.is_compiler_found()
    conditions.resolve_dependencies()

```

</details>

## `lock_interaction()`

*No documentation available.*

<details open><summary>Source</summary>

```python
def lock_interaction():
    global gui_lock
    gui_lock = True
    dpg.configure_item("button_patch", enabled=False)
    dpg.configure_item("button_select_mods", enabled=False)
    dpg.configure_item("button_uninstall", enabled=False)
    dpg.configure_item("lang_select", enabled=False)
    dpg.configure_item("output_select", enabled=False)

```

</details>

## `unlock_interaction()`

*No documentation available.*

<details open><summary>Source</summary>

```python
def unlock_interaction():
    global gui_lock
    gui_lock = False
    dpg.configure_item("button_patch", enabled=True)
    dpg.configure_item("button_select_mods", enabled=True)
    dpg.configure_item("button_uninstall", enabled=True)
    dpg.configure_item("lang_select", enabled=True)
    dpg.configure_item("output_select", enabled=True)

```

</details>

## `interactive_lock()`

*No documentation available.*

<details open><summary>Source</summary>

```python
def interactive_lock():
    lock_interaction()
    try:
        yield
    finally:
        unlock_interaction()

```

</details>

## `start_text()`

*No documentation available.*

<details open><summary>Source</summary>

```python
def start_text():
    for i in range(1, 6):
        terminal.add_text(f"&start_text_{i}_var")
    terminal.add_seperator()

```

</details>

## `close_active_window()`

*No documentation available.*

<details open><summary>Source</summary>

```python
def close_active_window():
    active_window_id = dpg.get_active_window()
    if not active_window_id:
        return

    active_window = dpg.get_item_alias(active_window_id) or active_window_id
    is_modal_active = (
        active_window == "modal_popup"
        or active_window_id == dpg.get_alias_id("modal_popup")
        or active_window in ["modal_text_wrapper", "modal_button_wrapper"]
    )

    if is_modal_active:
        dpg.configure_item("modal_popup", show=False)
        threading.Timer(0.1, modal_shared.show_next_from_queue).start()
    elif active_window not in [
        "terminal_window",
        "primary_window",
        "footer",
        "opener",
        "mod_tools",
        "maintenance_tools",
    ]:
        dpg.configure_item(active_window, show=False)

```

</details>

## `close()`

*No documentation available.*

<details open><summary>Source</summary>

```python
def close():
    dpg.stop_dearpygui()
    time.sleep(0.1)

```

</details>
