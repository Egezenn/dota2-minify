import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
import zipfile
import threading
from urllib.request import urlopen

import dearpygui.dearpygui as ui
import playsound3  # chimes are from pixabay.com/sound-effects/chime-74910/
import psutil
import vpk

import helper
import mpaths
import utils_gui

COPYTREE_IGNORE_PATTERNS = ("*.gitkeep", ".DS_Store", "__MACOSX", "Thumbs.db", "desktop.ini")

game_contents_file_init = False


def patcher():
    utils_gui.lock_interaction()
    helper.clean_terminal()
    target = "dota2.exe" if mpaths.OS == "Windows" else "dota2"
    running = False
    for p in psutil.process_iter(attrs=["name"]):
        try:
            name = p.info.get("name") or ""
            if name == target:
                running = True
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    if running:
        helper.add_text_to_terminal(
            helper.localization_dict["close_dota_terminal_text_var"],
            "close_dota_text_tag",
            "warning",
        )
        return

    try:
        helper.cleanFolders()
        if os.path.exists(mpaths.dota_resource_compiler_path):
            helper.workshop_installed = True

        blank_file_extensions = helper.getBlankFileExtensions(
            mpaths.blank_files_dir
        )  # list of extensions in bin/blank-files
        dota_pak_contents = vpk.open(mpaths.dota_game_pak_path)
        core_pak_contents = vpk.open(mpaths.dota_core_pak_path)
        dota_extracts = set()
        core_extracts = set()

        base_mods_applied = False
        blacklist_data = []  # path from every blacklist.txt
        mod_menus = []
        styling_data = []  # path and style from every styling.txt
        styling_dictionary = {}
        xml_modifications = {}

        for folder in mpaths.mods_folder_application_order:
            try:
                mod_path = os.path.join(mpaths.mods_dir, folder)
                blacklist_txt = os.path.join(mod_path, "blacklist.txt")
                styling_txt = os.path.join(mod_path, "styling.txt")
                menu_xml = os.path.join(mod_path, "menu.xml")
                xml_mod_file = os.path.join(mod_path, "xml_mod.json")
                script_file = os.path.join(mod_path, "script.py")

                for box in utils_gui.checkboxes:
                    if (ui.get_value(box) == True and utils_gui.checkboxes[box] == folder) or (
                        folder == "base" and not base_mods_applied
                    ):  # step into folders that have ticked checkboxes only
                        base_mods_applied = True if folder == "base" else False
                        helper.add_text_to_terminal(
                            f"{helper.localization_dict['installing_terminal_text_var']} {folder}"
                        )
                        if os.path.exists(os.path.join(mod_path, "files")):
                            shutil.copytree(
                                os.path.join(mod_path, "files"),
                                mpaths.minify_dota_compile_output_path,
                                dirs_exist_ok=True,
                                ignore=shutil.ignore_patterns(*COPYTREE_IGNORE_PATTERNS),
                            )

                        if os.path.exists(menu_xml):
                            with open(menu_xml, "r", encoding="utf-8") as file:
                                mod_menus.append(file.read())

                        if os.path.exists(xml_mod_file):
                            with open(xml_mod_file, "r", encoding="utf-8") as file:
                                mod_xml = json.load(file)
                            for path, mods in mod_xml.items():
                                xml_modifications.setdefault(path, []).extend(mods)
                        # ------------------------------- scripting support ------------------------------ #
                        # TODO: adjust placement?
                        if os.path.exists(script_file):
                            if mod_path not in sys.path:
                                sys.path.insert(0, mod_path)
                            script = importlib.import_module("script")
                            if hasattr(script, "main"):
                                helper.add_text_to_terminal(
                                    helper.localization_dict["script_execution_text_var"].format(folder),
                                )
                                try:
                                    script.main()
                                    helper.add_text_to_terminal(
                                        helper.localization_dict["script_success_text_var"].format(folder),
                                        None,
                                        "success",
                                    )
                                except:
                                    helper.add_text_to_terminal(
                                        helper.localization_dict["script_fail_text_var"].format(folder),
                                        None,
                                        "error",
                                    )
                            else:
                                helper.add_text_to_terminal(
                                    helper.localization_dict["script_no_main_text_var"].format(folder),
                                    None,
                                    "warning",
                                )
                            sys.path.remove(mod_path)
                        # ------------------------------- blacklist.txt ------------------------------ #
                        if os.path.exists(blacklist_txt):
                            global game_contents_file_init
                            if not game_contents_file_init:
                                # TODO: check pak01 hash, log it & run this only if it's different
                                extract = subprocess.run(
                                    [
                                        os.path.join(".", mpaths.s2v_executable),
                                        "-i",
                                        mpaths.dota_game_pak_path,
                                        "-l",
                                    ],
                                    capture_output=True,
                                    text=True,
                                )
                                pattern = r"(.*) CRC:.*"
                                replacement = r"\1"

                                with open(
                                    os.path.join(mpaths.bin_dir, "gamepakcontents.txt"),
                                    "w",
                                ) as file:
                                    for extract_line in extract.stdout.splitlines():
                                        new_line = re.sub(pattern, replacement, extract_line.rstrip())
                                        file.write(new_line + "\n")
                                game_contents_file_init = True

                            with open(blacklist_txt) as file:
                                lines = file.readlines()
                                blacklist_data_exclusions = []

                                for index, line in enumerate(lines):
                                    line = line.strip()

                                    if line.startswith("#") or line == "":
                                        continue

                                    elif line.startswith("@@"):
                                        for path in helper.processBlackList(index, line, folder, blank_file_extensions):
                                            blacklist_data.append(path)

                                    elif line.startswith(">>") or line.startswith("**"):
                                        for path in helper.processBlacklistDir(index, line, folder):
                                            blacklist_data.append(path)

                                    elif line.startswith("--"):
                                        blacklist_data_exclusions.append(line[2:])

                                    else:
                                        if line.endswith(tuple(blank_file_extensions)):
                                            blacklist_data.append(line)
                                        else:
                                            helper.warnings.append(
                                                f"[Invalid Extension] '{line}' in 'mods\\{folder}\\blacklist.txt' [line: {index+1}] does not end in one of the valid extensions -> {blank_file_extensions}"
                                            )

                            for exclusion in blacklist_data_exclusions:
                                if exclusion in blacklist_data:
                                    blacklist_data.remove(exclusion)
                                else:
                                    print(
                                        f"[Unnecessary Exclusion] '{exclusion}' in '{folder}' is not necessary, the mod doesn't include this file."
                                    )
                            print(f"{folder}'s blacklist replaced {len(blacklist_data)} files!")

                            for index, line in enumerate(blacklist_data):
                                line = line.strip()
                                path, extension = os.path.splitext(line)

                                os.makedirs(
                                    os.path.join(
                                        mpaths.minify_dota_compile_output_path,
                                        os.path.dirname(path),
                                    ),
                                    exist_ok=True,
                                )

                                try:  # TODO: parallelize filecopy if and when blacklists get bigger
                                    shutil.copy(
                                        os.path.join(mpaths.blank_files_dir, f"blank{extension}"),
                                        os.path.join(
                                            mpaths.minify_dota_compile_output_path,
                                            path + extension,
                                        ),
                                    )
                                except FileNotFoundError as exception:
                                    helper.warnings.append(
                                        f"[Invalid Extension] '{line}' in 'mods\\{os.path.basename(mod_path)}\\blacklist.txt' does not end in one of the valid extensions -> {blank_file_extensions}"
                                    )

                            blacklist_data = []
                            blacklist_data_exclusions = []

                        # --------------------------------- styling.txt --------------------------------- #
                        if os.path.exists(styling_txt):
                            with open(styling_txt) as file:

                                lines = file.readlines()

                                for line in lines:
                                    line = line.strip()

                                    if line.startswith("#") or line == "":
                                        continue

                                    elif line.startswith("@@"):
                                        for path in helper.urlValidator(line):
                                            styling_data.append(path)
                                        continue
                                    else:
                                        styling_data.append(line)

                            for index, line in enumerate(styling_data):
                                try:
                                    line = line.split("@@")
                                    path = line[0].strip()
                                    style = line[1].strip()

                                    styling_dictionary[f"styling-key{index + 1}"] = (
                                        path,
                                        style,
                                    )

                                except Exception as exception:
                                    helper.warnings.append(
                                        f"[{type(exception).__name__}]"
                                        + f" Could not validate '{line}' in --> 'mods\\{folder}\\styling.txt' [line: {index + 1}]"
                                    )

                            for key, path_style in list(styling_dictionary.items()):
                                sanitized_path = (
                                    path_style[0][1:] if path_style[0].startswith("!") else path_style[0]
                                )  # horrible hack
                                os.makedirs(
                                    os.path.join(
                                        mpaths.build_dir,
                                        os.path.dirname(sanitized_path),
                                    ),
                                    exist_ok=True,
                                )
                                try:
                                    if path_style[0].startswith("!"):
                                        core_extracts.add(f"{sanitized_path}.vcss_c")
                                    else:
                                        dota_extracts.add(f"{sanitized_path}.vcss_c")
                                except KeyError:
                                    helper.warnings.append(
                                        f"Path does not exist in VPK -> '{sanitized_path}.vcss_c', error in 'mods\\{folder}\\styling.txt'"
                                    )

            except Exception as exception:
                exceptiondata = traceback.format_exc().splitlines()
                helper.warnings.append(exceptiondata[-1])
        if mod_menus:
            dota_extracts.add("panorama/layout/popups/popup_settings_reborn.vxml_c")
        # Extract XMLs to be modified (assume they are in game VPK)
        for path in xml_modifications.keys():
            compiled = path.replace(".xml", ".vxml_c")
            dota_extracts.add(compiled)

        helper.add_text_to_terminal(helper.localization_dict["starting_extraction_text_var"])
        helper.vpkExtractor(core_pak_contents, list(core_extracts))
        helper.vpkExtractor(dota_pak_contents, list(dota_extracts))

        # ---------------------------------- STEP 2 ---------------------------------- #
        # ------------------- Decompile all files in "build" folder ------------------ #
        # ---------------------------------------------------------------------------- #
        helper.add_text_to_terminal(
            helper.localization_dict["decompiling_terminal_text_var"],
            "decompiling_text",
        )
        with open(os.path.join(mpaths.logs_dir, "Source2Viewer-CLI.txt"), "w") as file:
            try:
                subprocess.run(
                    [
                        os.path.join(".", mpaths.s2v_executable),
                        "--input",
                        "build",
                        "--recursive",
                        "--vpk_decompile",
                        "--output",
                        "build",
                    ],
                    stdout=file,
                )
            except PermissionError:
                helper.add_text_to_terminal(
                    helper.localization_dict["error_no_execution_permission_s2v_var"],
                    "error",
                )

        if mod_menus:
            helper.build_minify_menu(mod_menus)
        for path, mods in xml_modifications.items():
            helper.apply_xml_modifications(os.path.join(mpaths.build_dir, path), mods)
        # ---------------------------------- STEP 3 ---------------------------------- #
        # ---------------------------- CSS resourcecompile --------------------------- #
        # ---------------------------------------------------------------------------- #
        helper.add_text_to_terminal(
            helper.localization_dict["compiling_resource_terminal_text_var"],
            "compiling_resourcecompiler_text_tag",
        )

        for key, path_style in list(styling_dictionary.items()):
            sanitized_path = path_style[0][1:] if path_style[0].startswith("!") else path_style[0]  # hhack
            with open(os.path.join(mpaths.build_dir, f"{sanitized_path}.css"), "r+") as file:
                if path_style[1] not in file.read():
                    file.write("\n" + path_style[1])

        shutil.copytree(
            mpaths.build_dir,
            mpaths.minify_dota_compile_input_path,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("*.vcss_c"),
        )

        if helper.workshop_installed:
            resource_log_path = os.path.join(mpaths.logs_dir, "resourcecompiler.txt")
            with open(resource_log_path, "wb") as file:
                helper.add_text_to_terminal(
                    helper.localization_dict["compiling_terminal_text_var"],
                    "compiling_text",
                )
                input_root = mpaths.minify_dota_compile_input_path
                output_root = mpaths.minify_dota_compile_output_path
                input_count = 0
                for _, _, files in os.walk(input_root):
                    input_count += len(files)
                file.write(f"Input file count: {input_count}\n".encode("utf-8"))
                file.write(f"Input root: {input_root}\n".encode("utf-8"))
                file.write(f"Output root: {output_root}\n".encode("utf-8"))

                compiler_path = mpaths.dota_resource_compiler_path
                input_arg = os.path.join(input_root, "*")
                compiler_dir = os.path.dirname(compiler_path)
                game_path = os.path.normpath(
                    os.path.join(compiler_dir, os.pardir, os.pardir, "dota")
                )
                command = [compiler_path, "-i", input_arg, "-r", "-game", game_path]

                rescomp = subprocess.run(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,  # compiler complains if minify_dota_compile_input_path is empty
                    env=os.environ.copy(),
                )
                file.write(b"Command: " + " ".join(command).encode("utf-8") + b"\n")
                file.write(b"Exit code: " + str(rescomp.returncode).encode("utf-8") + b"\n")
                if rescomp.stdout:
                    file.write(b"--- STDOUT ---\n")
                    file.write(rescomp.stdout)
                if rescomp.stderr:
                    file.write(b"\n--- STDERR ---\n")
                    file.write(rescomp.stderr)

                if rescomp.returncode != 0:
                    helper.add_text_to_terminal(
                        f"resourcecompiler exited with code {rescomp.returncode}. Check logs/resourcecompiler.txt.",
                        type="warning",
                    )
        else:
            helper.add_text_to_terminal(
                "Workshop Tools not detected; skipping resourcecompiler step.",
                type="warning",
            )

        # ---------------------------------- STEP 6 ---------------------------------- #
        # -------- Create VPK from game folder and save into Minify directory -------- #
        # ---------------------------------------------------------------------------- #
        # insert metadata to pak
        shutil.copy(
            mpaths.mods_file_dir,
            os.path.join(mpaths.minify_dota_compile_output_path, "minify_mods.json"),
        )
        try:
            shutil.copy(
                mpaths.version_file_dir,
                os.path.join(mpaths.minify_dota_compile_output_path, "minify_version.txt"),
            )
        except FileNotFoundError:  # update ignore
            pass

        os.makedirs(helper.output_path, exist_ok=True)
        newpak = vpk.new(mpaths.minify_dota_compile_output_path)
        newpak.save(os.path.join(helper.output_path, "pak66_dir.vpk"))

        helper.remove_path(
            mpaths.minify_dota_compile_input_path,
            mpaths.minify_dota_compile_output_path,
            mpaths.build_dir,
        )

        utils_gui.unlock_interaction()
        helper.add_text_to_terminal("-------------------------------------------------------", "spacer1_text")
        helper.add_text_to_terminal(
            helper.localization_dict["success_terminal_text_var"],
            "success_text_tag",
            "success",
        )
        # TODO: Use strings like this, without fstrings
        helper.add_text_to_terminal(
            helper.localization_dict["launch_option_text_var"].format(ui.get_value("output_select")),
            "launch_option_text",
            "warning",
        )

        helper.handleWarnings(mpaths.logs_dir)
        helper.dump_recent_logs()
        playsound3.playsound(os.path.join(mpaths.sounds_dir, "success.wav"))

    except Exception:
        with open(os.path.join(mpaths.logs_dir, "crashlog.txt"), "w") as file:
            file.write(traceback.format_exc())

        helper.add_text_to_terminal("-------------------------------------------------------", "spacer2_text")
        helper.add_text_to_terminal(
            helper.localization_dict["failure_terminal_text_var"],
            "patching_failed_text_tag",
            "error",
        )
        helper.add_text_to_terminal(
            helper.localization_dict["check_logs_terminal_text_var"],
            "check_logs_text_tag",
            "warning",
        )
        helper.dump_recent_logs()
        utils_gui.unlock_interaction()
        playsound3.playsound(os.path.join(mpaths.sounds_dir, "fail.wav"))


def _vpk_contains_minify_marker(path):
    """Return tuple (contains_marker, unicode_error) for given VPK path."""
    unicode_error = None

    try:
        pak = vpk.open(path)
    except UnicodeDecodeError as err:
        unicode_error = err
    else:
        try:
            pak.get_file("minify_mods.json")
            return True, None
        except KeyError:
            return False, None
        except UnicodeDecodeError as err:
            unicode_error = err

    if unicode_error is None:
        return False, None

    try:
        pak = vpk.open(path, path_enc=None)
    except Exception as err:
        raise err from unicode_error

    try:
        pak.get_file(b"minify_mods.json")
        return True, unicode_error
    except KeyError:
        return False, unicode_error


def uninstaller():
    utils_gui.hide_uninstall_popup()
    helper.clean_terminal()
    time.sleep(0.05)
    utils_gui.lock_interaction()

    # smart uninstall
    pak_pattern = r"^pak\d{2}_dir\.vpk$"
    for dir in mpaths.minify_dota_possible_language_output_paths:
        if os.path.isdir(dir):
            for item in os.listdir(dir):
                path = os.path.join(dir, item)
                if os.path.isfile(path) and re.fullmatch(pak_pattern, item):
                    try:
                        should_remove, _ = _vpk_contains_minify_marker(path)
                    except UnicodeDecodeError as e:
                        with open(os.path.join(mpaths.logs_dir, "uninstaller_vpk_error.txt"), "a") as file:
                            file.write(f"UnicodeDecodeError inspecting {path}: {e}\n")
                        helper.warnings.append(f"Skipping VPK during inspection: {path}")
                        continue
                    except Exception:
                        with open(os.path.join(mpaths.logs_dir, "uninstaller_vpk_error.txt"), "a") as file:
                            file.write(traceback.format_exc() + "\n")
                        helper.warnings.append(f"Error inspecting VPK: {path}")
                        continue

                    if should_remove:
                        os.remove(path)

    # TODO: implement mod specific uninstall instructions without relying on base code
    # odg
    try:
        with open(os.path.join(mpaths.dota_itembuilds_path, "default_antimage.txt"), "r") as file:
            lines = file.readlines()
        if len(lines) >= 3:
            if "OpenDotaGuides" in lines[2]:
                for name in os.listdir(mpaths.dota_itembuilds_path):
                    if name != "bkup":
                        os.remove(os.path.join(mpaths.dota_itembuilds_path, name))
                for name in os.listdir(os.path.join(mpaths.dota_itembuilds_path, "bkup")):
                    os.rename(
                        os.path.join(mpaths.dota_itembuilds_path, "bkup", name),
                        os.path.join(mpaths.dota_itembuilds_path, name),
                    )
                helper.remove_path(os.path.join(mpaths.dota_itembuilds_path, "bkup"))
    except FileNotFoundError:
        helper.warnings.append(
            "Unable to recover backed up default guides or the itembuilds directory is empty, verify files to get the default guides back"
        )
    helper.add_text_to_terminal(
        helper.localization_dict["mods_removed_terminal_text_var"],
        "uninstaller_text_tag",
    )
    utils_gui.unlock_interaction()


def clean_lang_dirs():
    helper.clean_terminal()
    uninstaller()
    for path in mpaths.minify_dota_possible_language_output_paths:
        if os.path.isdir(path):
            helper.remove_path(path)
            helper.add_text_to_terminal(helper.localization_dict["clean_lang_dirs_text_var"].format(path))


def create_blank_mod():
    mod_name = "_test"
    path_to_mod = os.path.join(mpaths.mods_dir, mod_name)

    blacklist_template = r"""# This file is a list of path to files used to override those with blanks.
# Supported file types are can be found in `bin/blank-files`.

# A list of all the files (from the game pak) can be found in `bin/gamepakcontents.txt`.

# Syntax for this file starting from the line beginning is as follows:
# `#`: Comments
# `>>`: Directories
# `**`: RegExp patterns
# `--`: Exclusions (for when you want to exclude specific files from bulk additions)
# `@@`: Links to raw data

# After that with no blank spaces you put the path to the file you want to override.
# path/to/file

# particles/base_attacks/ranged_goodguy_launch.vpcf_c
# >>particles/sprays
# **taunt.*\.vsnd_c
# @@link-to-url
"""
    styling_template = r"""# This file is a list of CSS paths and styling that will be appended to them.
# By the nature of this method modifications done here may break the original XML or CSS that gets updated resulting in a bad layout.
# In such cases, a repatch is required.

# If you encounter errors while patching, it's most likely that your CSS is invalid or the path is wrong.

# For Source 2 flavored CSS properties, refer to: https://developer.valvesoftware.com/wiki/Dota_2_Workshop_Tools/Panorama/CSS_Properties
# To live inspect the layout, open the workshop tools and press F6 and select the element you'd like to select from the XML.

# Syntax for this file starting from the line beginning is as follows:
# `#`: Comments 
# `!`: By default, the file is pulled from `dota 2 beta/game/dota/pak01_dir.vpk`.
#      However to change this behavior and pull files from `dota 2 beta/game/core/pak01_dir.vpk`, you can use this.
# `@@`: Links to raw data

# path/to/file_without_extension @@ #example_id { property: value; }
"""
    script_template = r"""# This script template can be run both manually and from minify.
# You are able to use packages and modules from minify (you need an activated environment from the minify root or running with the tool `uv` can automatically handle this.)
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

# Any package or module native to minify can be imported here
# import requests
#
# import mpaths
# ...


def main():
    pass
    # Code specific to your mod goes here, minify will try to execute this block.
    # If any exceptions occur, it'll be written to `logs/warnings.txt`


if __name__ == "__main__":
    main()
"""
    mod_menu_template = r""
    xml_mod_template = r"{}"

    helper.remove_path(path_to_mod)
    os.mkdir(path_to_mod)
    os.mkdir(os.path.join(path_to_mod, "files"))
    open(os.path.join(path_to_mod, "files", ".gitkeep"), "w").close()
    for locale in helper.localizations:
        open(os.path.join(path_to_mod, f"notes_{locale.lower()}.txt"), "w").close()
    with open(os.path.join(path_to_mod, "blacklist.txt"), "w") as file:
        file.write(blacklist_template)
    with open(os.path.join(path_to_mod, "styling.txt"), "w") as file:
        file.write(styling_template)
    with open(os.path.join(path_to_mod, "script.py"), "w") as file:
        file.write(script_template)
    with open(os.path.join(path_to_mod, "menu.xml"), "w") as file:
        file.write(mod_menu_template)
    with open(os.path.join(path_to_mod, "xml_mod.json"), "w") as file:
        file.write(xml_mod_template)


def _ensure_steamcmd_windows_binary():
    """Download steamcmd.exe (Windows build) locally if missing and return its path."""
    tools_dir = os.path.join(mpaths.user_data_root, "tools")
    steamcmd_dir = os.path.join(tools_dir, "steamcmd")
    os.makedirs(steamcmd_dir, exist_ok=True)

    steamcmd_exe = os.path.join(steamcmd_dir, "steamcmd.exe")
    if os.path.exists(steamcmd_exe):
        return steamcmd_exe

    helper.add_text_to_terminal("Downloading SteamCMD (Windows)...")
    url = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip"
    try:
        with urlopen(url) as resp:
            data = resp.read()
        zip_path = os.path.join(steamcmd_dir, "steamcmd.zip")
        with open(zip_path, "wb") as f:
            f.write(data)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(steamcmd_dir)
        os.remove(zip_path)
        if not os.path.exists(steamcmd_exe):
            raise FileNotFoundError("steamcmd.exe not found after extraction")
    except Exception:
        with open(os.path.join(mpaths.logs_dir, "steamcmd_download.txt"), "w") as f:
            f.write(traceback.format_exc())
        helper.add_text_to_terminal("Failed to download SteamCMD. See logs/steamcmd_download.txt", type="error")
        return None

    return steamcmd_exe


def _run_steamcmd(app_id: str, install_dir: str, username: str | None, password: str | None, guard: str | None):
    """Run SteamCMD to app_update the given app_id into install_dir (Windows platform)."""
    steamcmd_exe = _ensure_steamcmd_windows_binary()
    if not steamcmd_exe:
        return False

    cmd = []
    if mpaths.OS != "Windows":
        helper.add_text_to_terminal(
            "SteamCMD downloads now require Windows; please run on a Windows system.",
            type="error",
        )
        return False

    cmd = [steamcmd_exe]

    os.makedirs(install_dir, exist_ok=True)
    cmd += ["+force_install_dir", install_dir]

    # Optional Steam Guard code first
    if guard:
        cmd += ["+set_steam_guard_code", guard]

    if username and password:
        cmd += ["+login", username, password]
    else:
        # Without credentials, DLC depots won't download; attempt anonymous to validate plumbing
        cmd += ["+login", "anonymous"]

    # Fetch Windows build of Dota 2 (app 570). If user owns DLC 313250, its depots will be fetched too.
    cmd += ["+app_update", app_id, "-validate", "+quit"]

    helper.add_text_to_terminal("Running SteamCMD to fetch Dota 2 (Windows) build...")
    try:
        with open(os.path.join(mpaths.logs_dir, "steamcmd.txt"), "w", encoding="utf-8", errors="ignore") as logf:
            proc = subprocess.run(cmd, stdout=logf, stderr=subprocess.STDOUT)
        if proc.returncode != 0:
            helper.add_text_to_terminal(
                "SteamCMD failed. Check logs/steamcmd.txt. If first time, you may need credentials and Steam Guard.",
                type="error",
            )
            return False
    except Exception:
        with open(os.path.join(mpaths.logs_dir, "steamcmd_run.txt"), "w") as f:
            f.write(traceback.format_exc())
        helper.add_text_to_terminal("SteamCMD execution failed. See logs/steamcmd_run.txt", type="error")
        return False

    return True


def _steamcmd_base(username: str | None, password: str | None, guard: str | None):
    steamcmd_exe = _ensure_steamcmd_windows_binary()
    if not steamcmd_exe:
        return None
    cmd = []
    if mpaths.OS != "Windows":
        helper.add_text_to_terminal(
            "SteamCMD downloads now require Windows; please run on a Windows system.",
            type="error",
        )
        return None

    cmd = [steamcmd_exe]
    if guard:
        cmd += ["+set_steam_guard_code", guard]
    if username and password:
        cmd += ["+login", username, password]
    else:
        cmd += ["+login", "anonymous"]
    return cmd


def _steamcmd_run_and_capture(args: list[str]) -> tuple[int, str]:
    try:
        proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="ignore")
        return proc.returncode, proc.stdout or ""
    except Exception:
        return 1, traceback.format_exc()


def _steamcmd_stream_output(args: list[str], log_path: str) -> tuple[bool, bool, bool]:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    guard_prompted = False
    rate_limited = False
    with open(log_path, "w", encoding="utf-8", errors="ignore") as logf:
        try:
            proc = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="ignore",
            )
            for line in proc.stdout or []:
                line = line.rstrip()
                logf.write(line + "\n")
                low = line.lower()
                if "%" in line or "downloading" in low or "bytes" in low:
                    helper.add_text_to_terminal(line)
                if "steam guard" in line or "two-factor" in low or "enter the current code" in line:
                    guard_prompted = True
                if "rate limit exceeded" in low:
                    rate_limited = True
            proc.wait()
            return proc.returncode == 0, guard_prompted, rate_limited
        except Exception:
            logf.write(traceback.format_exc())
            return False, guard_prompted, rate_limited


def _download_depots_only(depots: list[dict], username: str | None, password: str | None, guard: str | None) -> tuple[bool, str, bool]:
    base = _steamcmd_base(username, password, guard)
    if not base:
        return False, "", False
    args = base[:]
    for d in depots:
        if d.get("manifest"):
            args += ["+download_depot", d["app_id"], d["id"], d["manifest"]]
        else:
            # No manifest -> download latest
            args += ["+download_depot", d["app_id"], d["id"]]
    args += ["+quit"]
    log_path = os.path.join(mpaths.logs_dir, "steamcmd_progress.txt")
    # Up to 3 attempts total with backoff
    for i in range(3):
        ok, guard_prompted, rate_limited = _steamcmd_stream_output(args, log_path)
        if ok:
            break
        if guard_prompted and i == 0:
            helper.add_text_to_terminal("Approve the sign-in on your phone (30s)...")
            time.sleep(30)
            ok, guard_prompted, rate_limited = _steamcmd_stream_output(args, log_path)
            if ok:
                break
        if not ok and guard_prompted and i == 1:
            helper.add_text_to_terminal("Steam Guard requested. Please provide the current 2FA code.")
            new_code = _await_guard_code_from_user()
            if not new_code:
                break
            base2 = _steamcmd_base(username, password, new_code)
            if not base2:
                break
            args = base2 + args[len(base):]  # replace login portion
            ok, guard_prompted, rate_limited = _steamcmd_stream_output(args, log_path)
            if ok:
                break
        if rate_limited:
            backoff = 60 * (i + 1)
            helper.add_text_to_terminal(f"Steam rate limit hit. Waiting {backoff}s before retry...", type="warning")
            time.sleep(backoff)
            continue
        # If failed without specific signal, break
        break
    steamcmd_exe = _ensure_steamcmd_windows_binary()
    content_root = os.path.join(os.path.dirname(steamcmd_exe), "steamapps", "content") if steamcmd_exe else ""
    return ok, content_root, guard_prompted


def _get_app_info_text(app_id: str, username: str | None, password: str | None, guard: str | None, retries: int = 2) -> str | None:
    base_args = _steamcmd_base(username, password, guard)
    if not base_args:
        return None
    attempt = 0
    args = base_args + ["+app_info_update", "1", "+app_info_print", app_id, "+quit"]
    log_file = os.path.join(mpaths.logs_dir, f"steam_app_{app_id}.txt")
    out = ""
    while attempt <= retries:
        code, out = _steamcmd_run_and_capture(args)
        with open(log_file, "w", encoding="utf-8", errors="ignore") as f:
            f.write(out)
        low = out.lower()
        guard_needed = ("steam guard" in out or "two-factor" in low or "enter the current code" in out or "two-factor code mismatch" in out)
        if guard_needed and attempt == 0:
            helper.add_text_to_terminal("Approve the sign-in on your phone (30s)...")
            time.sleep(30)
            code, out = _steamcmd_run_and_capture(args)
            with open(log_file, "w", encoding="utf-8", errors="ignore") as f:
                f.write(out)
            low = out.lower()
            guard_needed = ("steam guard" in out or "two-factor" in low or "enter the current code" in out or "two-factor code mismatch" in out)
            if guard_needed:
                helper.add_text_to_terminal("Steam Guard required. Please enter the current 2FA code.")
                new_code = _await_guard_code_from_user()
                if not new_code:
                    return None
                base_args2 = _steamcmd_base(username, password, new_code)
                if not base_args2:
                    return None
                args = base_args2 + ["+app_info_update", "1", "+app_info_print", app_id, "+quit"]
                code, out = _steamcmd_run_and_capture(args)
                with open(log_file, "w", encoding="utf-8", errors="ignore") as f:
                    f.write(out)
                low = out.lower()
        if "rate limit exceeded" in low and attempt < retries:
            backoff = 60 * (attempt + 1)
            helper.add_text_to_terminal(f"Steam rate limit hit during app info. Waiting {backoff}s before retry...", type="warning")
            time.sleep(backoff)
            attempt += 1
            continue
        break
    if code != 0:
        # If depots content is present, proceed anyway
        if '"depots"' in out:
            helper.add_text_to_terminal(f"app_info for {app_id} returned non-zero but contains depots; continuing.", type="warning")
            return out
        helper.add_text_to_terminal(f"Failed to fetch app_info for {app_id}. See {log_file}", type="error")
        return None
    return out


def download_workshop_tools_via_steamcmd(username: str | None = None, password: str | None = None, guard: str | None = None):
    """Download only the Dota 2 Workshop Tools depots via SteamCMD and copy into rescomproot.

    Uses explicit depots under app 570:
      - 381450 (Workshop Tools, DLC 313250) manifest 709350790366570241
      - 373303 (Dota 2 Win64 binaries) manifest 1983977856334381899
    Credentials can be provided via parameters or env vars (MINIFY_STEAM_USER/MINIFY_STEAM_PASS/MINIFY_STEAM_GUARD).
    Streams SteamCMD output to the terminal for progress lines, and supports phone approval/2FA codes.
    """
    utils_gui.lock_interaction()
    try:
        helper.clean_terminal()
        helper.add_text_to_terminal("Preparing SteamCMD and staging explicit depot downloads...")
        app_main = "570"
        # Forced depots with manifests (as of 2025-09-15)
        forced_depots = [
            {"app_id": "570", "id": "381450", "manifest": "709350790366570241"},
            {"app_id": "570", "id": "373303", "manifest": "1983977856334381899"},
        ]
        user = username or os.getenv("MINIFY_STEAM_USER")
        pwd = password or os.getenv("MINIFY_STEAM_PASS")
        guard_code = guard or os.getenv("MINIFY_STEAM_GUARD")

        # Deduplicate (future safe if adjusted)
        seen = set()
        unique_depots = []
        for d in forced_depots:
            key = (d["app_id"], d["id"])
            if key in seen:
                continue
            seen.add(key)
            unique_depots.append(d)

        helper.add_text_to_terminal(f"Downloading {len(unique_depots)} depot(s) from app 570...")
        ok, content_root, guard_prompted = _download_depots_only(unique_depots, user, pwd, guard_code)
        if not ok and guard_prompted:
            # Ask for a fresh 2FA code and retry once
            helper.add_text_to_terminal("Steam Guard requested. Please provide the current 2FA code.")
            new_code = _await_guard_code_from_user()
            if not new_code:
                helper.add_text_to_terminal("No Steam Guard code provided. Aborting.", type="error")
                return
            ok, content_root, _ = _download_depots_only(unique_depots, user, pwd, new_code)

        if not ok:
            helper.add_text_to_terminal("SteamCMD depot download failed. See logs/steamcmd_progress.txt", type="error")
            return
        if not _copy_tools_from_content_root(content_root):
            helper.add_text_to_terminal("Download complete, but could not locate expected game folders in depots.", type="error")
            return

        # Write steam_appid.txt next to Win64 binaries so tools can launch outside Steam
        steam_appid_path = os.path.join(mpaths.rescomp_override_dir, "game", "bin", "win64", "steam_appid.txt")
        os.makedirs(os.path.dirname(steam_appid_path), exist_ok=True)
        try:
            with open(steam_appid_path, "w") as f:
                f.write(app_main + "\n")
        except Exception:
            pass

        os.makedirs(mpaths.rescomp_override_dir, exist_ok=True)
        utils_gui.recalc_rescomp_dirs()
        helper.workshop_installed = os.path.exists(mpaths.dota_resource_compiler_path)
        # Refresh UI buttons immediately
        try:
            utils_gui.setupButtonState()
        except Exception:
            pass
        helper.add_text_to_terminal("Workshop Tools (381450) and Win64 binaries (373303) downloaded and configured.", type="success")
    except Exception:
        with open(os.path.join(mpaths.logs_dir, "steamcmd_pipeline.txt"), "w") as f:
            f.write(traceback.format_exc())
        helper.add_text_to_terminal("Unexpected error during SteamCMD pipeline. See logs/steamcmd_pipeline.txt", type="error")
    finally:
        utils_gui.unlock_interaction()


def _parse_dlc_depots(app_info_text: str, dlc_app_id: str = "313250", os_filter: str = "windows", app_id: str = "570") -> list[dict]:
    """Parse depots from Steam app_info text where depot belongs to the DLC.
    Matches either dlcappid=<dlc> or depotfromapp=<dlc>. Returns list of dicts with app_id, id, manifest.
    """
    depots: list[dict] = []
    lines = app_info_text.splitlines()
    in_depots = False
    brace_level = 0
    current = None
    for raw in lines:
        line = raw.strip()
        if not in_depots and line.startswith('"depots"'):
            in_depots = True
            continue
        if in_depots:
            if "{" in line:
                brace_level += line.count("{")
            if "}" in line:
                brace_level -= line.count("}")
                if current is not None and brace_level == 1:
                    depots.append(current)
                    current = None
                if brace_level <= 0:
                    break
            m = re.match(r'^"(\d+)"\s*\{\s*$', line)
            if m and brace_level == 1:
                current = {"id": m.group(1), "dlcappid": None, "depotfromapp": None, "oslist": None, "manifest": None, "app_id": app_id}
                continue
            if current is None:
                continue
            m = re.match(r'^"dlcappid"\s*"(\d+)"', line)
            if m:
                current["dlcappid"] = m.group(1)
            m = re.match(r'^"depotfromapp"\s*"(\d+)"', line)
            if m:
                current["depotfromapp"] = m.group(1)
            m = re.match(r'^"oslist"\s*"([^"]+)"', line)
            if m:
                current["oslist"] = m.group(1)
            # public manifest id is nested under manifests/public
            m = re.match(r'^"public"\s*"(\d+)"', line)
            if m:
                current["manifest"] = m.group(1)
    results = [
        {"app_id": d["app_id"], "id": d["id"], "manifest": d["manifest"]}
        for d in depots
        if d.get("manifest") and (d.get("oslist") is None or os_filter in d.get("oslist", "")) and (d.get("dlcappid") == dlc_app_id or d.get("depotfromapp") == dlc_app_id)
    ]
    return results


def _parse_app_depots(app_info_text: str, app_id: str, os_filter: str = "windows") -> list[dict]:
    """Parse any depots directly listed under given app. Returns list of dicts with app_id, id, manifest."""
    depots: list[dict] = []
    lines = app_info_text.splitlines()
    in_depots = False
    brace_level = 0
    current = None
    for raw in lines:
        line = raw.strip()
        if not in_depots and line.startswith('"depots"'):
            in_depots = True
            continue
        if in_depots:
            if "{" in line:
                brace_level += line.count("{")
            if "}" in line:
                brace_level -= line.count("}")
                if current is not None and brace_level == 1:
                    depots.append(current)
                    current = None
                if brace_level <= 0:
                    break
            m = re.match(r'^"(\d+)"\s*\{\s*$', line)
            if m and brace_level == 1:
                current = {"id": m.group(1), "oslist": None, "manifest": None, "app_id": app_id}
                continue
            if current is None:
                continue
            m = re.match(r'^"oslist"\s*"([^"]+)"', line)
            if m:
                current["oslist"] = m.group(1)
            m = re.match(r'^"public"\s*"(\d+)"', line)
            if m:
                current["manifest"] = m.group(1)
    results = [
        {"app_id": d["app_id"], "id": d["id"], "manifest": d["manifest"]}
        for d in depots
        if d.get("manifest") and (d.get("oslist") is None or os_filter in d.get("oslist", ""))
    ]
    return results


def _copy_tools_from_content_root(content_root: str) -> bool:
    """Copy required folders from downloaded depots content tree into rescomproot."""
    if not content_root or not os.path.isdir(content_root):
        return False
    copied_any = False
    # Walk app_* folders
    for app_folder in os.listdir(content_root):
        app_path = os.path.join(content_root, app_folder)
        if not os.path.isdir(app_path) or not app_folder.startswith("app_"):
            continue
        for depot_folder in os.listdir(app_path):
            depot_path = os.path.join(app_path, depot_folder)
            if not os.path.isdir(depot_path):
                continue
            # Locate 'game' directory inside depot
            candidate_game = None
            for root, dirs, files in os.walk(depot_path):
                if os.path.basename(root) == "game":
                    candidate_game = root
                    break
            if not candidate_game:
                continue
            src_root = candidate_game
            paths = {
                os.path.join(src_root, "bin"): os.path.join(mpaths.rescomp_override_dir, "game", "bin"),
                os.path.join(src_root, "core"): os.path.join(mpaths.rescomp_override_dir, "game", "core"),
                os.path.join(src_root, "dota", "bin"): os.path.join(mpaths.rescomp_override_dir, "game", "dota", "bin"),
                os.path.join(src_root, "dota", "tools"): os.path.join(mpaths.rescomp_override_dir, "game", "dota", "tools"),
            }
            gameinfo_src = os.path.join(src_root, "dota", "gameinfo.gi")
            gameinfo_dst = os.path.join(mpaths.rescomp_override_dir, "game", "dota", "gameinfo.gi")
            for s, d in paths.items():
                if os.path.exists(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                    copied_any = True
            if os.path.exists(gameinfo_src):
                os.makedirs(os.path.dirname(gameinfo_dst), exist_ok=True)
                shutil.copy(gameinfo_src, gameinfo_dst)
                copied_any = True
    return copied_any
