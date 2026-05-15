"Checks for various things"

import os
import shutil
import stat
import webbrowser

import dearpygui.dearpygui as dpg
import psutil
import vdf
from core import base, constants, fs, log, steam
from ui import terminal

workshop_installed = False
workshop_required_methods = ["styling.css", "xml_mod.json", "files_uncompiled"]


def is_dota_running(text_tag, text_type):
    target = "dota2.exe" if base.OS == base.WIN else "dota2"
    running = any(p.info.get("name") == target for p in psutil.process_iter(attrs=["name"]))

    if running:
        terminal.add_text(text_tag, msg_type=text_type)
    return running


def is_compiler_found():
    # ACF is the authoritative Steam source; file presence alone doesn't confirm the DLC is active
    global workshop_installed
    acf_path = os.path.join(steam.LIBRARY, "steamapps", f"appmanifest_{base.STEAM_DOTA_ID}.acf")
    try:
        with open(acf_path, encoding="utf-8") as f:
            app_state = vdf.load(f).get("AppState", {})
    except Exception as e:
        log.write_warning("Failed to read ACF", e)
        app_state = {}
    mounted = app_state.get("MountedConfig", {}).get("optionaldlc", "")
    disabled = app_state.get("MountedConfig", {}).get("DisabledDLC", "")
    if (
        app_state.get("StateFlags") == "4"
        and base.STEAM_DOTA_WORKSHOP_TOOLS_ID in mounted
        and base.STEAM_DOTA_WORKSHOP_TOOLS_ID not in disabled
    ):
        workshop_installed = True
    else:
        workshop_installed = False
        terminal.add_text("&error_no_workshop_tools_found_terminal", msg_type="warning")


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
                tag = terminal.add_text("&downloading_cli_terminal")
                zip_path = constants.s2v_latest.split("/")[-1]
                if fs.download_file(constants.s2v_latest, zip_path, tag):
                    terminal.add_text("&downloaded_cli_terminal", zip_path)
                    if fs.extract_archive(zip_path, "."):
                        fs.remove_path(zip_path)
                        terminal.add_text("&extracted_cli_terminal", zip_path)
                        constants.s2v_executable = os.path.basename(constants.s2v_executable)

                        if base.OS != base.WIN and not os.access(constants.s2v_executable, os.X_OK):
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
            tag = terminal.add_text("&downloading_ripgrep_terminal")
            archive_path = constants.rg_latest.split("/")[-1]
            archive_name = archive_path[:-4] if archive_path[-4:] == ".zip" else archive_path[:-7]

            if fs.download_file(constants.rg_latest, archive_path, tag):
                terminal.add_text("&downloaded_cli_terminal", archive_path)

                rg_binary_name = os.path.basename(constants.rg_executable)
                success = fs.extract_archive(archive_path, ".", f"{archive_name}/{rg_binary_name}")

                if success:
                    fs.move_path(
                        os.path.join(archive_name, rg_binary_name),
                        rg_binary_name,
                    )
                    fs.remove_path(archive_path, archive_name)
                    terminal.add_text("&extracted_cli_terminal", archive_path)

                    constants.rg_executable = rg_binary_name

                    if base.OS in (base.LINUX, base.MAC) and not os.access(constants.rg_executable, os.X_OK):
                        current_permissions = os.stat(constants.rg_executable).st_mode
                        os.chmod(
                            constants.rg_executable,
                            current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
                        )

    except Exception:
        log.write_crashlog()
        terminal.add_text("&failed_download_retrying_terminal", msg_type="error")
        if retries < 3:
            return resolve_dependencies(retries + 1)
        terminal.add_text("&failed_download", 3, msg_type="error")
        terminal.add_text("&connection_error", msg_type="error")
        webbrowser.open(constants.rg_latest)
        if workshop_installed:
            webbrowser.open(constants.s2v_latest)
        return


def check_binaries():
    """
    Checks if required binaries exist.
    """
    if workshop_installed:
        if not os.path.exists(constants.s2v_executable) and not shutil.which(constants.s2v_executable):
            return False

    if not os.path.exists(constants.rg_executable) and not shutil.which(constants.rg_executable):
        return False

    return True


def disable_workshop_mods():
    if not workshop_installed:
        for folder in constants.mods_with_order:
            mod_path = os.path.join(base.mods_dir, folder)

            for method_path in workshop_required_methods:
                if os.path.exists(os.path.join(mod_path, method_path)):
                    dpg.configure_item(folder, enabled=False, default_value=False)
                    break
