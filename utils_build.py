import os
import shutil
import subprocess
import time
import traceback

import dearpygui.dearpygui as ui
import psutil
import requests
import vpk

import helper
import mpaths
import utils_gui


def patcher():
    global patching
    utils_gui.lock_interaction()
    helper.clean_terminal()
    if "dota2.exe" in (p.name() for p in psutil.process_iter()):
        helper.add_text_to_terminal(
            helper.localization_dict["close_dota_terminal_text_var"], "close_dota_text_tag", "warning"
        )
        return

    patching = True

    try:
        helper.cleanFolders()

        styling_dictionary = {}
        # blacklist_dictionary = {}

        blank_file_extensions = helper.getBlankFileExtensions(
            mpaths.blank_files_dir
        )  # list of extensions in bin/blank-files
        blacklist_data = []  # path from every blacklist.txt
        styling_data = []  # path and style from every styling.txt

        for folder in mpaths.mods_folder_compilation_order:
            try:
                mod_path = os.path.join(mpaths.mods_dir, folder)
                blacklist_txt = os.path.join(mod_path, "blacklist.txt")
                styling_txt = os.path.join(mod_path, "styling.txt")

                for box in utils_gui.checkboxes:
                    if (
                        ui.get_value(box) == True and utils_gui.checkboxes[box] == folder
                    ):  # step into folders that have ticked checkboxes only
                        helper.add_text_to_terminal(
                            f"{helper.localization_dict["installing_terminal_text_var"]} {folder}",
                            tag=f"installing_{folder}_text_tag",
                        )
                        if utils_gui.checkboxes[box] == "Dark Terrain" or utils_gui.checkboxes[box] == "Remove Foilage":
                            shutil.copytree(
                                mpaths.maps_dir,
                                os.path.join(mpaths.minify_dota_pak_output_path, os.path.basename(mpaths.maps_dir)),
                                dirs_exist_ok=True,
                            )
                        if utils_gui.checkboxes[box] == "OpenDotaGuides Guides":
                            zip_path = os.path.join(mod_path, "files", "OpenDotaGuides.zip")
                            temp_dump_path = os.path.join(mod_path, "files", "temp")
                            if os.path.exists(zip_path):
                                os.remove(zip_path)
                            try:
                                response = requests.get(mpaths.odg_latest)
                                if response.status_code == 200:
                                    with open(zip_path, "wb") as file:
                                        file.write(response.content)
                                    helper.add_text_to_terminal(
                                        helper.localization_dict["downloaded_latest_opendotaguides_terminal_text_var"],
                                        "downloaded_open_dota_guides_text_tag",
                                    )
                                    os.makedirs(os.path.join(mpaths.dota_itembuilds_path, "bkup"), exist_ok=True)
                                    for name in os.listdir(mpaths.dota_itembuilds_path):
                                        try:
                                            if name != "bkup":
                                                os.rename(
                                                    os.path.join(mpaths.dota_itembuilds_path, name),
                                                    os.path.join(mpaths.dota_itembuilds_path, "bkup", name),
                                                )
                                        except FileExistsError:
                                            pass  # backup was created and opendotaguides was replacing the guides already
                                    shutil.unpack_archive(zip_path, temp_dump_path, format="zip")
                                    for file in os.listdir(temp_dump_path):
                                        shutil.copy(
                                            os.path.join(temp_dump_path, file),
                                            os.path.join(mpaths.dota_itembuilds_path, file),
                                        )
                                    helper.rmtrees(temp_dump_path)
                                    os.remove(zip_path)
                                    helper.add_text_to_terminal(
                                        helper.localization_dict["replaced_guides_terminal_text_var"],
                                        "replaced_open_dota_guides_text_tag",
                                    )
                                    if os.path.exists(zip_path):
                                        os.remove(zip_path)
                                else:
                                    helper.add_text_to_terminal(
                                        helper.localization_dict["failed_to_download_opendotaguides_terminal_text_var"],
                                        "failed_downloading_open_dota_guides_text_tag",
                                        "error",
                                    )
                            except:  # no connection
                                helper.add_text_to_terminal(
                                    helper.localization_dict["failed_to_download_opendotaguides_terminal_text_var"],
                                    "failed_downloading_open_dota_guides_text_tag",
                                    "error",
                                )
                        shutil.copytree(
                            os.path.join(mod_path, "files"),
                            mpaths.minify_dota_compile_output_path,
                            dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("*.gitkeep"),
                        )
                        # ------------------------------- blacklist.txt ------------------------------ #
                        if os.stat(blacklist_txt).st_size == 0:
                            pass
                        else:
                            with open(blacklist_txt) as file:
                                lines = file.readlines()

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

                                    else:
                                        if line.endswith(tuple(blank_file_extensions)):
                                            blacklist_data.append(line)
                                        else:
                                            helper.warnings.append(
                                                f"[Invalid Extension] '{line}' in 'mods\\{folder}\\blacklist.txt' [line: {index+1}] does not end in one of the valid extensions -> {blank_file_extensions}"
                                            )

                            for index, line in enumerate(blacklist_data):
                                line = line.strip()
                                path, extension = os.path.splitext(line)

                                os.makedirs(
                                    os.path.join(mpaths.minify_dota_compile_output_path, os.path.dirname(path)),
                                    exist_ok=True,
                                )

                                try:  # TODO faster filecopy?
                                    shutil.copy(
                                        os.path.join(mpaths.blank_files_dir, "blank{}").format(extension),
                                        os.path.join(mpaths.minify_dota_compile_output_path, path + extension),
                                    )
                                except FileNotFoundError as exception:
                                    helper.warnings.append(
                                        f"[Invalid Extension] '{line}' in 'mods\\{os.path.basename(mod_path)}\\blacklist.txt' does not end in one of the valid extensions -> {blank_file_extensions}"
                                    )

                            blacklist_data = []

                        # --------------------------------- styling.txt --------------------------------- #
                        if os.stat(styling_txt).st_size == 0:
                            pass
                        else:
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

                                    styling_dictionary["styling-key{}".format(index + 1)] = (path, style)

                                except Exception as exception:
                                    helper.warnings.append(
                                        "[{}]".format(type(exception).__name__)
                                        + " Could not validate '{}' in --> 'mods\\{}\\styling.txt' [line: {}]".format(
                                            line, folder, index + 1
                                        )
                                    )

                                os.makedirs(os.path.join(mpaths.build_dir, os.path.dirname(path)), exist_ok=True)

                                for key, path_style in list(styling_dictionary.items()):
                                    try:
                                        helper.vpkExtractor(f"{path_style[0]}.vcss_c")
                                    except KeyError:
                                        helper.warnings.append(
                                            "Path does not exist in VPK -> '{}', error in 'mods\\{}\\styling.txt'".format(
                                                f"{path_style[0]}.vcss_c", folder
                                            )
                                        )
                                        del styling_dictionary[key]

            except Exception as exception:
                exceptiondata = traceback.format_exc().splitlines()
                helper.warnings.append(exceptiondata[-1])
        # ---------------------------------- STEP 2 ---------------------------------- #
        # ------------------- Decompile all files in "build" folder ------------------ #
        # ---------------------------------------------------------------------------- #
        helper.add_text_to_terminal(helper.localization_dict["decompiling_terminal_text_var"], "decompiling_text")
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
                    "error_no_execution_permission_s2v",
                    "error",
                )
        # ---------------------------------- STEP 3 ---------------------------------- #
        # ---------------------------- CSS resourcecompile --------------------------- #
        # ---------------------------------------------------------------------------- #
        helper.add_text_to_terminal(helper.localization_dict["patching_terminal_text_var"], "patching_text_tag")

        for key, path_style in list(styling_dictionary.items()):
            with open(os.path.join(mpaths.build_dir, f"{path_style[0]}.css"), "r+") as file:
                if path_style[1] not in file.read():
                    file.write("\n" + path_style[1])

        shutil.copytree(
            mpaths.build_dir,
            mpaths.minify_dota_compile_input_path,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("*.vcss_c"),
        )

        if helper.workshop_installed == True:
            with open(os.path.join(mpaths.logs_dir, "resourcecompiler.txt"), "wb") as file:
                helper.add_text_to_terminal(helper.localization_dict["compiling_terminal_text_var"], "compiling_text")
                sp_compiler = subprocess.run(
                    [
                        mpaths.dota_resource_compiler_path,
                        "-i",
                        mpaths.minify_dota_compile_input_path + "/*",
                        "-r",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,  # compiler complains if minify_dota_compile_input_path is empty
                )
                if sp_compiler.stdout != b"":
                    file.write(sp_compiler.stdout)

                if sp_compiler.stderr != b"":
                    decoded_err = sp_compiler.stderr.decode("utf-8")
                    raise Exception(decoded_err)
        # ---------------------------------- STEP 6 ---------------------------------- #
        # -------- Create VPK from game folder and save into Minify directory -------- #
        # ---------------------------------------------------------------------------- #
        # insert metadata to pak
        shutil.copy(mpaths.mods_file_dir, os.path.join(mpaths.minify_dota_compile_output_path, "minify_mods.json"))
        try:
            shutil.copy(
                mpaths.version_file_dir, os.path.join(mpaths.minify_dota_compile_output_path, "minify_version.txt")
            )
        except FileNotFoundError:
            pass
        newpak = vpk.new(mpaths.minify_dota_compile_output_path)
        newpak.save(os.path.join(mpaths.minify_dota_pak_output_path, "pak66_dir.vpk"))

        patching = False

        helper.rmtrees(mpaths.minify_dota_compile_input_path, mpaths.minify_dota_compile_output_path, mpaths.build_dir)

        utils_gui.unlock_interaction()
        helper.add_text_to_terminal("-------------------------------------------------------", "spacer1_text")
        helper.add_text_to_terminal(
            helper.localization_dict["success_terminal_text_var"], "success_text_tag", "success"
        )
        helper.add_text_to_terminal(helper.localization_dict["launch_option_text_var"], "launch_option_text", "warning")

        helper.handleWarnings(mpaths.logs_dir)

    except Exception:
        with open(os.path.join(mpaths.logs_dir, "crashlog.txt"), "w") as file:
            file.write(traceback.format_exc())

        patching = False
        helper.add_text_to_terminal("-------------------------------------------------------", "spacer2_text")
        helper.add_text_to_terminal(
            helper.localization_dict["failure_terminal_text_var"], "patching_failed_text_tag", "error"
        )
        helper.add_text_to_terminal(
            helper.localization_dict["check_logs_terminal_text_var"], "check_logs_text_tag", "warning"
        )
        utils_gui.unlock_interaction()


def uninstaller():
    utils_gui.hide_uninstall_popup()
    helper.clean_terminal()
    time.sleep(0.05)
    utils_gui.lock_interaction()
    # TODO make use of the included minify.txt at root
    vpkPath = os.path.join(mpaths.minify_dota_pak_output_path, "pak66_dir.vpk")
    if os.path.exists(vpkPath):
        os.remove(vpkPath)

    # remove dota.vpk if it exists
    helper.rmtrees(mpaths.minify_dota_maps_output_path)

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
    except FileNotFoundError:
        helper.warnings.append(
            "Unable to recover backed up default guides or the itembuilds directory is empty, verify files to get the default guides back"
        )
    helper.add_text_to_terminal(helper.localization_dict["mods_removed_terminal_text_var"], "uninstaller_text_tag")
    utils_gui.unlock_interaction()
