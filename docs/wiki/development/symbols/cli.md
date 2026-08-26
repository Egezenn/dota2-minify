# cli

## `run()`

*No documentation available.*

<details open><summary>Source</summary>

```python
def run():
    _run_init()
    app()

```

</details>

## `run_patch(config_path, mods_path)`

Run a patch.

<details open><summary>Source</summary>

```python
def run_patch(
    config_path: Optional[str] = typer.Option(None, "--config", "-c", help="Path to config file."),
    mods_path: Optional[str] = typer.Option(None, "--mods", "-m", help="Path to mods file."),
):
    """Run a patch."""
    _apply_paths(config_path, mods_path)
    from core import log

    print("Starting patch process...")
    try:
        patch.patcher()
    except Exception:
        log.write_crashlog()

```

</details>

## `run_prelaunch(config_path, mods_path)`

Run prelaunch checks and scripts.

<details open><summary>Source</summary>

```python
def run_prelaunch(
    config_path: Optional[str] = typer.Option(None, "--config", "-c", help="Path to config file."),
    mods_path: Optional[str] = typer.Option(None, "--mods", "-m", help="Path to mods file."),
):
    """Run prelaunch checks and scripts."""
    _apply_paths(config_path, mods_path)
    current_version = ""
    if os.path.exists(constants.dota_steam_inf_path):
        with utils.open_utf8R(constants.dota_steam_inf_path) as f:
            current_version = f.read()

    cached_version = ""
    if os.path.exists(base.dota_steam_inf_cache):
        with utils.open_utf8R(base.dota_steam_inf_cache) as f:
            cached_version = f.read()

    patch_ran = current_version != cached_version or not cached_version

    if patch_ran:
        print("Dota 2 version changed or first run. Starting patch...")
        run_patch(config_path=config_path, mods_path=mods_path)
        _config.set("last_patch_time", int(time.time()))
    else:
        print("Dota 2 version has not changed. Skipping patch.")

    if not patch_ran:
        any_ran = helper.bulk_exec_script("prelaunch")
        if any_ran:
            _config.set("last_patch_time", int(time.time()))

```

</details>

## `config(config_path, editor, show, print_path)`

Interact with the config file.

<details open><summary>Source</summary>

```python
def config(
    config_path: Optional[str] = typer.Option(None, "--config", "-c", help="Path to config file."),
    editor: Optional[str] = typer.Option(None, "--editor", "-e", help="Editor binary to use (defaults to $EDITOR)."),
    show: bool = typer.Option(False, "--json", "-j", help="Print contents."),
    print_path: bool = typer.Option(False, "--path", "-p", help="Print path."),
):
    """Interact with the config file."""
    _apply_paths(config_path, None)
    if show:
        print(json.dumps(_config.read_json_file(base.main_config_file_dir), indent=2))
        return
    if print_path:
        print(base.main_config_file_dir)
        return
    _open_in_editor(base.main_config_file_dir, editor)

```

</details>

## `mods(mods_path, editor, show, print_path)`

Interact with the mods file.

<details open><summary>Source</summary>

```python
def mods(
    mods_path: Optional[str] = typer.Option(None, "--mods", "-m", help="Path to mods file."),
    editor: Optional[str] = typer.Option(None, "--editor", "-e", help="Editor binary to use (defaults to $EDITOR)."),
    show: bool = typer.Option(False, "--json", "-j", help="Print contents."),
    print_path: bool = typer.Option(False, "--path", "-p", help="Print path."),
):
    """Interact with the mods file."""
    _apply_paths(None, mods_path)
    _ensure_mods_file()
    if show:
        print(json.dumps(_config.read_json_file(base.mods_config_dir), indent=2))
        return
    if print_path:
        print(base.mods_config_dir)
        return
    _open_in_editor(base.mods_config_dir, editor)

```

</details>

## `uninstall(config_path, mods_path, force)`

Uninstall all mods.

<details open><summary>Source</summary>

```python
def uninstall(
    config_path: Optional[str] = typer.Option(None, "--config", "-c", help="Path to config file."),
    mods_path: Optional[str] = typer.Option(None, "--mods", "-m", help="Path to mods file."),
    force: bool = typer.Option(False, "--force", "-f", help="Wipe the contents of all language dirs."),
):
    """Uninstall all mods."""
    _apply_paths(config_path, mods_path)
    if force:
        patch.unins.wipe()
    else:
        patch.unins.uninstall()

```

</details>
