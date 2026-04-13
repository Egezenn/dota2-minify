# ui.window

Main window dragging, resizing and focus

## `drag(sender, app_data, user_data)`

*No documentation available.*

<details open><summary>Source</summary>

```python
def drag(sender, app_data, user_data):
    global is_moving_viewport

    if is_moving_viewport:
        drag_deltas = app_data
        viewport_current_pos = dpg.get_viewport_pos()
        new_x_position = viewport_current_pos[0] + drag_deltas[1]
        new_y_position = viewport_current_pos[1] + drag_deltas[2]
        new_y_position = max(new_y_position, 0)  # prevent the viewport to go off the top of the screen
        dpg.set_viewport_pos([new_x_position, new_y_position])
    # TODO: add dev windows conditionally
    elif dpg.get_item_alias(dpg.get_active_window()) is not None and (
        dpg.is_item_hovered("primary_window")
        or dpg.is_item_hovered("terminal_window")
        or dpg.is_item_hovered("footer")
        or dpg.is_item_hovered("mod_menu")
        or dpg.is_item_hovered("settings_menu")
        or dpg.get_item_alias(dpg.get_active_window()).endswith("details_window_tag")
    ):
        is_moving_viewport = True
        drag_deltas = app_data
        viewport_current_pos = dpg.get_viewport_pos()
        new_x_position = viewport_current_pos[0] + drag_deltas[1]
        new_y_position = viewport_current_pos[1] + drag_deltas[2]
        new_y_position = max(new_y_position, 0)  # prevent the viewport to go off the top of the screen
        dpg.set_viewport_pos([new_x_position, new_y_position])

```

</details>

## `stop_drag()`

*No documentation available.*

<details open><summary>Source</summary>

```python
def stop_drag():
    global is_moving_viewport
    is_moving_viewport = False

```

</details>

## `focus()`

*No documentation available.*

<details open><summary>Source</summary>

```python
def focus():
    with utils.try_pass():
        if base.OS == base.WIN:
            hwnd = ctypes.windll.user32.FindWindowW(None, "Minify")
            if hwnd != 0:
                ctypes.windll.user32.ShowWindow(hwnd, 9)
                ctypes.windll.user32.SetForegroundWindow(hwnd)

        else:
            subprocess.run(
                ["wmctrl", "-a", "Minify"],
                check=True,
            )

```

</details>

## `on_resize()`

*No documentation available.*

<details open><summary>Source</summary>

```python
def on_resize():
    from ui import dev_tools, modal_shared

    if dev_tools.dev_mode_state != 1:
        dev_tools.prev_width = dpg.get_viewport_width()
        dev_tools.prev_height = dpg.get_viewport_height()
    # terminal wrap size
    window_width = dpg.get_item_width("primary_window")
    window_height = dpg.get_item_height("primary_window")
    terminal.wrap_size = base.main_window_width - 20 if dev_tools.dev_mode_state == 1 else window_width - 10

    for item in shared.terminal_history:
        idx = item["id"]
        if dpg.does_item_exist(idx):
            dpg.configure_item(idx, wrap=terminal.wrap_size)

    # details windows resize
    for window_tag in shared.tag_data_for_details_windows:
        if dpg.does_item_exist(window_tag):
            dpg.configure_item(window_tag, width=window_width, height=window_height)
            if dpg.is_item_shown(window_tag):
                mod = window_tag.replace("_details_window_tag", "")
                details.render_details_window(mod)

    # menus resize
    if dpg.does_item_exist("mod_menu"):
        dpg.configure_item("mod_menu", width=window_width, height=window_height)

    if dpg.does_item_exist("settings_menu"):
        dpg.configure_item("settings_menu", width=window_width, height=window_height)

    if dpg.is_item_shown("modal_popup"):
        modal_shared.configure()

```

</details>
