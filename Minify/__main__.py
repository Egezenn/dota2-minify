import os
import sys

from core import base

base.original_cwd = os.getcwd()
current_dir = os.path.dirname(os.path.abspath(__file__))

# Ensure root directories
if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(os.path.realpath(sys.executable)))
else:
    os.chdir(current_dir)
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

os.makedirs("cache", exist_ok=True)
os.makedirs("config", exist_ok=True)
os.makedirs("logs", exist_ok=True)

import json
import shlex
import subprocess
import time
from typing import Optional

import helper
import patch
import typer
import ui
from core import base, constants, mods_shared, utils
from core import config as _config

app = typer.Typer(
    name="dota2-minify",
    help="Dota2-Minify CLI and GUI.",
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _version_callback(value: bool) -> None:
    if value:
        print(base.VERSION)
        raise typer.Exit()


def _resolve_path(path: str) -> str:
    if os.path.isabs(path):
        return path
    original_cwd = getattr(base, "original_cwd", None)
    return os.path.abspath(os.path.join(original_cwd, path)) if original_cwd else os.path.abspath(path)


def _apply_paths(config_path: Optional[str], mods_path: Optional[str]) -> None:
    if config_path:
        base.main_config_file_dir = _resolve_path(config_path)
    if mods_path:
        base.mods_config_dir = _resolve_path(mods_path)


def _ensure_mods_file() -> None:
    mods_shared.scan_mods()
    states = _config.read_json_file(base.mods_config_dir) if os.path.exists(base.mods_config_dir) else {}
    if any(mod not in states for mod in constants.mods_with_order):
        for mod in constants.mods_with_order:
            states.setdefault(mod, False)
        _config.write_json_file(base.mods_config_dir, dict(sorted(states.items())))


def _open_in_editor(file: str, editor: Optional[str]) -> None:
    if not os.path.exists(file):
        _config.write_json_file(file, {})
    editor_cmd = editor or os.environ.get("EDITOR") or ("notepad" if os.name == "nt" else "vi")
    result = subprocess.run([*shlex.split(editor_cmd), file])
    raise typer.Exit(result.returncode)


@app.callback(invoke_without_command=True)
def _main(
    ctx: typer.Context,
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Print version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
):
    if ctx.invoked_subcommand is None:
        ui.launch()


@app.command(name="patch")
def run_patch(
    config_path: Optional[str] = typer.Option(None, "--config", "-c", help="Path to config file."),
    mods_path: Optional[str] = typer.Option(None, "--mods", "-m", help="Path to mods file."),
):
    """Run a patch."""
    _apply_paths(config_path, mods_path)
    print("Starting patch process...")
    patch.patcher()


@app.command(name="prelaunch")
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


@app.command()
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


@app.command()
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


@app.command()
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


if __name__ == "__main__":
    has_subcommand = len(sys.argv) > 1 and sys.argv[1] not in ["-h", "--help", "-v", "--version"]
    base.HEADLESS = bool(has_subcommand)
    utils.setup_system()
    app()
