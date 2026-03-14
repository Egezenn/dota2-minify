"Things that are required"

import os
import shutil
import stat

import dearpygui.dearpygui as dpg
import psutil
from core import base, constants, fs, log
from ui.terminal import add_text_to_terminal

workshop_installed = False
workshop_required_methods = ["styling.css", "xml_mod.json", "files_uncompiled"]


def is_dota_running(text_tag, text_type):
    target = "dota2.exe" if base.OS == base.WIN else "dota2"
    running = any(p.info.get("name") == target for p in psutil.process_iter(attrs=["name"]))

    if running:
        add_text_to_terminal(text_tag, msg_type=text_type)
    return running


def is_compiler_found():
    global workshop_installed
    if not os.path.exists(constants.dota_resource_compiler_path):
        workshop_installed = False
        add_text_to_terminal("&error_no_workshop_tools_found_terminal", msg_type="warning")
    else:
        workshop_installed = True


def download_dependencies(retries=0):
    try:
        if workshop_installed:
            if not os.path.exists(constants.s2v_executable):
                tag = add_text_to_terminal("&downloading_cli_terminal")
                zip_path = constants.s2v_latest.split("/")[-1]
                if fs.download_file(constants.s2v_latest, zip_path, tag):
                    add_text_to_terminal("&downloaded_cli_terminal", zip_path)
                    if fs.extract_archive(zip_path, "."):
                        fs.remove_path(zip_path)
                        add_text_to_terminal("&extracted_cli_terminal", zip_path)
                        if base.OS != base.WIN and not os.access(constants.s2v_executable, os.X_OK):
                            current_permissions = os.stat(constants.s2v_executable).st_mode
                            os.chmod(
                                constants.s2v_executable,
                                current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
                            )
        elif os.path.exists(constants.s2v_executable):
            fs.remove_path(constants.s2v_executable)

        # Prefer system-installed ripgrep when available
        rg_on_path = shutil.which(constants.rg_executable)
        if rg_on_path:
            constants.rg_executable = rg_on_path
        elif not os.path.exists(constants.rg_executable):
            tag = add_text_to_terminal("&downloading_ripgrep_terminal")
            archive_path = constants.rg_latest.split("/")[-1]
            archive_name = archive_path[:-4] if archive_path[-4:] == ".zip" else archive_path[:-7]

            if fs.download_file(constants.rg_latest, archive_path, tag):
                add_text_to_terminal("&downloaded_cli_terminal", archive_path)

                success = fs.extract_archive(archive_path, ".", f"{archive_name}/{constants.rg_executable}")

                if success:
                    fs.move_path(
                        os.path.join(archive_name, constants.rg_executable),
                        constants.rg_executable,
                    )
                    fs.remove_path(archive_path)
                    add_text_to_terminal("&extracted_cli_terminal", archive_path)
                    if base.OS in (base.LINUX, base.MAC) and not os.access(constants.rg_executable, os.X_OK):
                        current_permissions = os.stat(constants.rg_executable).st_mode
                        os.chmod(
                            constants.rg_executable,
                            current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
                        )

    except:
        log.write_crashlog()
        add_text_to_terminal("&failed_download_retrying_terminal", msg_type="error")
        if retries < 3:
            return download_dependencies(retries + 1)
        add_text_to_terminal("&failed_download", 3, msg_type="error")
        return


def disable_workshop_mods():
    if not workshop_installed:
        for folder in constants.mods_with_order:
            mod_path = os.path.join(base.mods_dir, folder)

            for method_path in workshop_required_methods:
                if os.path.exists(os.path.join(mod_path, method_path)):
                    dpg.configure_item(folder, enabled=False, default_value=False)
                    break
