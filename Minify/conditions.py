"Checks for various things"

import os
import shutil
import stat
import webbrowser

import dearpygui.dearpygui as dpg
import psutil
import vdf
from core import base, constants, fs, log, output, steam

workshop_installed = False
workshop_required_methods = ["styling.css", "xml.json", "files_uncompiled"]


def is_dota_running(text_tag, text_type):
    target = "dota2.exe" if base.is_win else "dota2"
    running = any(p.info.get("name") == target for p in psutil.process_iter(attrs=["name"]))

    if running:
        output.add_text(text_tag, msg_type=text_type)
    return running


def get_dota_app_state():
    """
    Reads the Dota 2 appmanifest ACF file and returns the AppState dictionary.
    """
    acf_path = os.path.join(steam.LIBRARY, "steamapps", f"appmanifest_{base.STEAM_DOTA_ID}.acf")
    try:
        with open(acf_path, encoding="utf-8") as f:
            return vdf.load(f).get("AppState", {})
    except Exception as e:
        log.write_warning("Failed to read ACF", e)
        return {}


def get_workshop_tools_status(app_state):
    """
    Checks if Workshop Tools are enabled (mounted and not disabled) in the app state.
    """
    mounted_str = app_state.get("MountedConfig", {}).get("optionaldlc", "")
    disabled_str = app_state.get("MountedConfig", {}).get("DisabledDLC", "")

    mounted_set = {token.strip() for token in mounted_str.replace(",", " ").split() if token.strip()}
    disabled_set = {token.strip() for token in disabled_str.replace(",", " ").split() if token.strip()}

    return base.STEAM_DOTA_WORKSHOP_TOOLS_ID in mounted_set and base.STEAM_DOTA_WORKSHOP_TOOLS_ID not in disabled_set


def is_compiler_found():
    global workshop_installed
    workshop_installed = os.path.exists(constants.dota_resource_compiler_path)
    if not workshop_installed and not base.HEADLESS:
        output.add_text("&error_no_workshop_tools_found_terminal", msg_type="warning")


def resolve_dependencies(retries=0):
    """
    Attempts to download dependencies ripgrep and Source2Viewer-CLI(if workshop tools are available)
    for 3 times and opens up their download URLs if they don't exist.

    Checks for existence on `PATH` first then checks existence on root.
    """
    try:
        if workshop_installed:
            s2v_on_path = shutil.which(constants.s2v_executable)
            if s2v_on_path:
                constants.s2v_executable = s2v_on_path
            else:
                constants.s2v_executable = os.path.basename(constants.s2v_executable)

            if not os.path.exists(constants.s2v_executable):
                tag = output.add_text("&downloading_cli_terminal")
                zip_path = constants.s2v_latest.split("/")[-1]
                if fs.download_file(constants.s2v_latest, zip_path, tag):
                    output.add_text("&downloaded_cli_terminal", zip_path)
                    if fs.extract_archive(zip_path, "."):
                        fs.remove_path(zip_path)
                        output.add_text("&extracted_cli_terminal", zip_path)
                        constants.s2v_executable = os.path.basename(constants.s2v_executable)

                        if base.is_win and not os.access(constants.s2v_executable, os.X_OK):
                            current_permissions = os.stat(constants.s2v_executable).st_mode
                            os.chmod(
                                constants.s2v_executable,
                                current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
                            )
        elif os.path.exists(constants.s2v_executable):
            fs.remove_path(constants.s2v_executable)

        rg_on_path = shutil.which(constants.rg_executable)
        if rg_on_path:
            constants.rg_executable = rg_on_path
        else:
            constants.rg_executable = os.path.basename(constants.rg_executable)

        if not os.path.exists(constants.rg_executable):
            tag = output.add_text("&downloading_ripgrep_terminal")
            archive_path = constants.rg_latest.split("/")[-1]
            archive_name = archive_path[:-4] if archive_path[-4:] == ".zip" else archive_path[:-7]

            if fs.download_file(constants.rg_latest, archive_path, tag):
                output.add_text("&downloaded_cli_terminal", archive_path)

                rg_binary_name = os.path.basename(constants.rg_executable)
                success = fs.extract_archive(archive_path, ".", f"{archive_name}/{rg_binary_name}")

                if success:
                    fs.move_path(
                        os.path.join(archive_name, rg_binary_name),
                        rg_binary_name,
                    )
                    fs.remove_path(archive_path, archive_name)
                    output.add_text("&extracted_cli_terminal", archive_path)

                    constants.rg_executable = rg_binary_name

                    if (base.is_linux or base.is_mac) and not os.access(constants.rg_executable, os.X_OK):
                        current_permissions = os.stat(constants.rg_executable).st_mode
                        os.chmod(
                            constants.rg_executable,
                            current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
                        )
        constants.s2v_exec_path = (
            constants.s2v_executable
            if os.path.isabs(constants.s2v_executable)
            else os.path.join(".", constants.s2v_executable)
        )
        constants.rg_exec_path = (
            constants.rg_executable
            if os.path.isabs(constants.rg_executable)
            else os.path.join(".", constants.rg_executable)
        )

    except Exception:
        log.write_crashlog()
        output.add_text("&failed_download_retrying_terminal", msg_type="error")
        if retries < 3:
            return resolve_dependencies(retries + 1)
        output.add_text("&failed_download", 3, msg_type="error")
        output.add_text("&connection_error", msg_type="error")
        webbrowser.open(constants.rg_latest)
        if workshop_installed:
            webbrowser.open(constants.s2v_latest)
        return


def check_binaries():
    """
    Checks if required binaries exist.
    """
    if workshop_installed:
        s2v_on_path = shutil.which(constants.s2v_executable)
        if not os.path.exists(constants.s2v_executable) and not s2v_on_path:
            return False
        if s2v_on_path and not os.path.isabs(constants.s2v_executable):
            constants.s2v_executable = s2v_on_path
            constants.s2v_exec_path = s2v_on_path

    rg_on_path = shutil.which(constants.rg_executable)
    if not os.path.exists(constants.rg_executable) and not rg_on_path:
        return False
    if rg_on_path and not os.path.isabs(constants.rg_executable):
        constants.rg_executable = rg_on_path
        constants.rg_exec_path = rg_on_path

    return True


def disable_workshop_mods():
    if not workshop_installed:
        for folder in constants.mods_with_order:
            mod_path = os.path.join(base.mods_dir, folder)

            for method_path in workshop_required_methods:
                if os.path.exists(os.path.join(mod_path, method_path)):
                    dpg.configure_item(folder, enabled=False, default_value=False)
                    break
