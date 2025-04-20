import json
import os
import platform
import shutil
import subprocess
import threading
import time
import traceback
from shutil import copytree, ignore_patterns

import dearpygui.dearpygui as ui
import psutil
import requests
import vpk

import helper
import mpaths
import validatefiles

ui.create_context()

version = None

try:
    with open("version", "r") as file:
        version = file.readline()
except:
    pass


patching = False
checkboxes = {}
checkboxes_state = {}
blacklist_dictionary = {}
styling_dictionary = {}

ui.add_value_registry(tag="details_tags")

with ui.value_registry():
    ui.add_string_value(default_value="Checking map file...", tag="checking_map_file_var")
    ui.add_string_value(
        default_value="Want to contribute to the project's growth?",
        tag="start_text_1_var",
    )
    ui.add_string_value(default_value="-> Join our Discord community!", tag="start_text_2_var")
    ui.add_string_value(
        default_value="-> Share Minify with your friends and online groups",
        tag="start_text_3_var",
    )
    ui.add_string_value(default_value="-> Star the project on GitHub", tag="start_text_4_var")
    ui.add_string_value(
        default_value="-> Create and maintain mods for this project",
        tag="start_text_5_var",
    )


class TextRedirector(object):
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag

    def write(self, str):
        self.widget.configure(state="normal")
        self.widget.insert("end", " " + str, (self.tag))
        self.widget.see("end")
        self.widget.configure(state="disabled")


def save_state():
    checkbox_state_save()


def lock_interaction():
    ui.configure_item("button_patch", enabled=False)
    ui.configure_item("button_select_mods", enabled=False)
    ui.configure_item("button_uninstall", enabled=False)
    ui.configure_item("exit_button", enabled=False)


def unlock_interaction():
    ui.configure_item("button_patch", enabled=True)
    ui.configure_item("button_select_mods", enabled=True)
    ui.configure_item("button_uninstall", enabled=True)
    ui.configure_item("exit_button", enabled=True)


def delete_update_popup():
    ui.configure_item("update_popup", show=False)
    ui.delete_item("update_popup")
    initiate_conditionals()


def hide_uninstall_popup():
    ui.configure_item("uninstall_popup", show=False)


def open_github_link_and_close_minify():
    open_github_link()  # behavior to download the latest release
    helper.close()


def checkbox_state_save():
    global checkboxes_state
    for box in checkboxes:
        checkboxes_state[box] = ui.get_value(box)
        with open("states.json", "w", encoding="utf-8") as file:
            json.dump(checkboxes_state, file, indent=4)


def load_state_checkboxes():
    global checkboxes_state
    try:
        with open("states.json", "r", encoding="utf-8") as file:
            checkboxes_state = json.load(file)
    except FileNotFoundError:
        pass


def drag_viewport(sender, app_data, user_data):
    if ui.get_item_alias(ui.get_active_window()) != None and (
        ui.is_item_hovered("primary_window") == True
        or ui.is_item_hovered("terminal_window") == True
        or ui.is_item_hovered("top_bar") == True
        or ui.is_item_hovered("mod_menu") == True
        or ui.get_item_alias(ui.get_active_window()).endswith("details_window_tag") == True
    ):  # Note: If local pos [1] < *Height_of_top_bar is buggy)
        drag_deltas = app_data
        viewport_current_pos = ui.get_viewport_pos()
        new_x_position = viewport_current_pos[0] + drag_deltas[1]
        new_y_position = viewport_current_pos[1] + drag_deltas[2]
        new_y_position = max(new_y_position, 0)  # prevent the viewport to go off the top of the screen
        ui.set_viewport_pos([new_x_position, new_y_position])


def open_mod_menu():
    ui.configure_item("mod_menu", show=True)


def open_discord_link():
    helper.urlDispatcher(mpaths.discord)


def open_github_link():
    helper.urlDispatcher(mpaths.latest_release)


def uninstall_popup_show():
    ui.configure_item("uninstall_popup", show=True)
    time.sleep(0.05)
    configure_uninstall_popup()


def create_checkboxes():
    global checkboxes_state
    for index in range(len(mpaths.mods_folders)):
        name = mpaths.mods_folders[index]
        ui.add_group(parent="mod_menu", tag=f"{name}_group_tag", horizontal=True, width=300)
        ui.add_checkbox(
            parent=f"{name}_group_tag",
            label=name,
            tag=name,
            default_value=False,
            callback=setupButtonState,
        )
        for key in checkboxes_state.keys():
            if key == name:
                if checkboxes_state[name] == None:
                    ui.configure_item(name, default_value=False)
                else:
                    ui.configure_item(name, default_value=checkboxes_state[name])
        mod_path = os.path.join(mpaths.mods_dir, name)
        notes_txt = os.path.join(mod_path, f"notes_{helper.locale}.txt")
        with open(notes_txt, "r", encoding="utf-8") as file:
            data = file.read()

        data2 = f"{name}_details_window_tag"
        ui.add_button(
            parent=f"{name}_group_tag",
            small=True,
            indent=250,
            tag=f"{name}_button_show_details_tag",
            label=f"{helper.details_label_text_var}",
            callback=show_details,
            user_data=f"{name}_details_window_tag",
        )

        ui.add_window(
            tag=f"{name}_details_window_tag",
            pos=(0, 0),
            show=False,
            width=494,
            height=300,
            no_resize=True,
            no_move=True,
            no_collapse=True,
            label=f"{name}",
        )
        ui.add_string_value(
            parent="details_tags",
            default_value=f"{data}",
            tag=f"{name}_details_text_value_tag",
        )
        ui.add_text(
            source=f"{name}_details_text_value_tag",
            parent=f"{name}_details_window_tag",
            wrap=480,
        )

        current_box = name
        checkboxes[current_box] = name


def show_details(sender, app_data, user_data):
    ui.configure_item(user_data, show=True)


def update_popup_show():
    ui.configure_item("update_popup", show=True)


def setupSystem():
    os.makedirs("logs", exist_ok=True)
    # TODO do this.. normally
    x = validatefiles.Requirements(checkboxes)
    public_methods = [
        method for method in dir(x) if callable(getattr(x, method)) if not method.startswith("_")
    ]  # private methods start with _
    try:
        if not (
            os.path.exists(os.path.join(mpaths.minify_dir, "Source2Viewer-CLI.exe"))
            or os.path.exists(os.path.join(mpaths.minify_dir, "libSkiaSharp.dll"))
            or os.path.exists(os.path.join(mpaths.minify_dir, "TinyEXR.Native.dll"))
        ):
            if platform.system() == "Windows":
                helper.add_text_to_terminal(
                    text=helper.localization_dict["downloading_cli_terminal_text_var"],
                    tag="downloading_s2v_cli_tag",
                )
                zip_name = "cli-windows-x64.zip"
                zip_path = os.path.join(mpaths.minify_dir, zip_name)
                response = requests.get(mpaths.s2v_latest_windows_x64)
                if response.status_code == 200:
                    with open(zip_path, "wb") as file:
                        file.write(response.content)
                    helper.add_text_to_terminal(
                        text=f"{helper.localization_dict["downloaded_cli_terminal_text_var"]}{zip_name}",
                        tag="downloaded_text_tag",
                    )
                    shutil.unpack_archive(zip_path, mpaths.minify_dir, "zip")
                    os.remove(zip_path)
                    helper.add_text_to_terminal(
                        text=f"{helper.localization_dict["extracted_cli_terminal_text_var"]}{zip_name}",
                        tag="extracted_text_tag",
                    )
            else:
                helper.add_text_to_terminal(
                    text=helper.localization_dict["no_instructions_cli_terminal_text_var"],
                    tag="error_cli_download_text_tag",
                )
        for method in public_methods:
            getattr(x, method)()
            if x.toggle_flag == True:
                lock_interaction()
                break
    except Exception:
        with open(os.path.join(mpaths.logs_dir, "crashlog.txt"), "w") as file:
            file.write(traceback.format_exc())
            lock_interaction()
            helper.add_text_to_terminal(
                text=helper.localization_dict["failed_to_start_terminal_text_var"],
                tag="failed_to_start_text_tag",
            )
            helper.add_text_to_terminal(
                text=helper.localization_dict["check_crashlog_terminal_text_var"],
                tag="check_logs_text_tag",
            )


def setupButtonState():
    for box in checkboxes:
        if ui.get_value(box) == True:
            ui.configure_item("button_patch", enabled=True)
            break
        else:
            ui.configure_item("button_patch", enabled=False)
    if helper.workshop_installed == False:
        helper.disableWorkshopMods(mpaths.mods_dir, mpaths.mods_folders, checkboxes)


def uninstaller():
    hide_uninstall_popup()
    clean_terminal()
    time.sleep(0.05)
    lock_interaction()
    # remove pak01_dir.vpk if it exists
    vpkPath = os.path.join(mpaths.minify_dota_pak_output_path, "pak66_dir.vpk")
    if os.path.exists(vpkPath):
        os.remove(vpkPath)

    # remove dota.vpk if it exists
    shutil.rmtree(mpaths.minify_dota_maps_output_path, ignore_errors=True)

    try:
        with open(os.path.join(mpaths.dota_itembuilds_path, "default_antimage.txt"), "r") as file:
            lines = file.readlines()
        if len(lines) >= 3:
            if "OpenDotaGuides" in lines[2]:
                for name in os.listdir(mpaths.dota_itembuilds_path):
                    if name != "bkup":
                        os.remove(os.path.join(mpaths.dota_itembuilds_path, name))
                # print(os.path.join(mpaths.itembuilds_dir, "bkup"))
                for name in os.listdir(os.path.join(mpaths.dota_itembuilds_path, "bkup")):
                    os.rename(
                        os.path.join(mpaths.dota_itembuilds_path, "bkup", name),
                        os.path.join(mpaths.dota_itembuilds_path, name),
                    )
    except FileNotFoundError:
        helper.warnings.append(
            "Unable to recover backed up default guides or the itembuilds directory is empty, verify files to get the default guides back"
        )
    helper.add_text_to_terminal(
        text=helper.localization_dict["mods_removed_terminal_text_var"],
        tag="uninstaller_text_tag",
    )
    unlock_interaction()


def clean_terminal():
    ui.delete_item("terminal_window", children_only=True)


def patcher_start():
    checkbox_state_save_thread = threading.Thread(target=checkbox_state_save)
    checkbox_state_save_thread.start()
    checkbox_state_save_thread.join()
    patch_thread = threading.Thread(target=patcher)
    patch_thread.start()
    patch_thread.join()


def patcher():
    global patching
    lock_interaction()
    clean_terminal()
    if "dota2.exe" in (p.name() for p in psutil.process_iter()):
        helper.add_text_to_terminal(
            text=helper.localization_dict["close_dota_terminal_text_var"],
            tag="close_dota_text_tag",
        )
        return

    patching = True

    try:
        # clean up previous patching data
        helper.cleanFolders()

        styling_dictionary = {}
        # blacklist_dictionary = {}
        warnings = []

        blank_file_extensions = helper.getBlankFileExtensions(
            mpaths.blank_files_dir
        )  # list of extensions in bin/blank-files
        blacklist_data = []  # path from every blacklist.txt
        styling_data = []  # path and style from every styling.txt

        for folder in mpaths.mods_folders:
            try:
                mod_path = os.path.join(mpaths.mods_dir, folder)
                # files_total = sum([len(files) for r, d, files in os.walk(os.path.join(mod_path, 'files'))])
                blacklist_txt = os.path.join(mod_path, "blacklist.txt")
                styling_txt = os.path.join(mod_path, "styling.txt")

                for box in checkboxes:
                    if (
                        ui.get_value(box) == True and checkboxes[box] == folder
                    ):  # step into folders that have ticked checkboxes only
                        helper.add_text_to_terminal(
                            f"{helper.localization_dict["installing_terminal_text_var"]} {folder}",
                            tag=f"istalling_{folder}_text_tag",
                        )
                        if checkboxes[box] == "Dark Terrain" or checkboxes[box] == "Remove Foilage":
                            shutil.copytree(
                                mpaths.maps_dir,
                                os.path.join(
                                    mpaths.minify_dota_pak_output_path,
                                    os.path.basename(mpaths.maps_dir),
                                ),
                                dirs_exist_ok=True,
                            )
                        if checkboxes[box] == "OpenDotaGuides Guides":
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
                                    os.makedirs(
                                        os.path.join(mpaths.dota_itembuilds_path, "bkup"),
                                        exist_ok=True,
                                    )
                                    for name in os.listdir(mpaths.dota_itembuilds_path):
                                        try:
                                            if name != "bkup":
                                                os.rename(
                                                    os.path.join(mpaths.dota_itembuilds_path, name),
                                                    os.path.join(
                                                        mpaths.dota_itembuilds_path,
                                                        "bkup",
                                                        name,
                                                    ),
                                                )
                                        except FileExistsError:
                                            pass  # backup was created and opendotaguides was replacing the guides already
                                    shutil.unpack_archive(zip_path, temp_dump_path, "zip")
                                    for file in os.listdir(temp_dump_path):
                                        shutil.copy(
                                            os.path.join(temp_dump_path, file),
                                            os.path.join(mpaths.dota_itembuilds_path, file),
                                        )
                                    shutil.rmtree(temp_dump_path)
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
                                    )
                            except:  # no connection
                                helper.add_text_to_terminal(
                                    helper.localization_dict["failed_to_download_opendotaguides_terminal_text_var"],
                                    "failed_downloading_open_dota_guides_text_tag",
                                )
                        # ----------------------------------- files ---------------------------------- #
                        # if files_total == 0:    pass
                        # elif files_total == 1:  print(f"   files: Found {files_total} file")
                        # else:                   print(f"   files: Found {files_total} files")
                        shutil.copytree(
                            os.path.join(mod_path, "files"),
                            mpaths.minify_dota_compile_output_path,
                            dirs_exist_ok=True,
                            ignore=ignore_patterns("*.gitkeep"),
                        )
                        # ------------------------------- blacklist.txt ------------------------------ #
                        if os.stat(blacklist_txt).st_size == 0:
                            pass
                        else:
                            with open(blacklist_txt) as file:

                                lines = file.readlines()

                                for index, line in enumerate(lines):
                                    line = line.strip()

                                    if line.startswith("#") or line.isspace():
                                        continue

                                    elif line.startswith("@@"):
                                        for path in helper.processBlackList(
                                            index,
                                            line,
                                            folder,
                                            blank_file_extensions,
                                            mpaths.dota_pak01_path,
                                        ):
                                            blacklist_data.append(path)
                                        continue

                                    elif line.startswith(">>"):
                                        for path in helper.processBlacklistDir(
                                            index, line, folder, mpaths.dota_pak01_path
                                        ):
                                            blacklist_data.append(path)
                                        continue

                                    else:
                                        if line.endswith(tuple(blank_file_extensions)):
                                            blacklist_data.append(line)
                                        else:
                                            warnings.append(
                                                f"[Invalid Extension] '{line}' in 'mods\\{folder}\\blacklist.txt' [line: {index+1}] does not end in one of the valid extensions -> {blank_file_extensions}"  ###???
                                            )

                            # print(f"   blacklist.txt: Found {len(blacklist_data)} paths")

                            for index, line in enumerate(blacklist_data):
                                line = line.strip()
                                path, extension = os.path.splitext(line)

                                # blacklist_dictionary["blacklist-key{}".format(index+1)] = path, extension

                                if not os.path.exists(
                                    os.path.join(mpaths.minify_dota_compile_output_path, os.path.dirname(path))
                                ):
                                    os.makedirs(
                                        os.path.join(mpaths.minify_dota_compile_output_path, os.path.dirname(path))
                                    )

                                try:
                                    shutil.copy(
                                        os.path.join(mpaths.blank_files_dir, "blank{}").format(extension),
                                        os.path.join(mpaths.minify_dota_compile_output_path, path + extension),
                                    )
                                except FileNotFoundError as exception:
                                    warnings.append(
                                        f"[Invalid Extension] '{line}' in 'mods\\{os.path.basename(mod_path)}\\blacklist.txt' does not end in one of the valid extensions -> {blank_file_extensions}"  ###???
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

                                    if line.startswith("#") or line.isspace():
                                        continue

                                    elif line.startswith("@@"):
                                        for path in helper.urlValidator(line):
                                            styling_data.append(path)
                                        continue
                                    else:
                                        styling_data.append(line)

                            # print(f"   styling.txt: Found styling.txt")

                            for index, line in enumerate(styling_data):
                                try:
                                    line = line.split("@@")
                                    path = line[0].strip()
                                    style = line[1].strip()

                                    styling_dictionary["styling-key{}".format(index + 1)] = (path, style)

                                except Exception as exception:
                                    warnings.append(
                                        "[{}]".format(type(exception).__name__)
                                        + " Could not validate '{}' in --> 'mods\\{}\\styling.txt' [line: {}]".format(
                                            line, folder, index + 1
                                        )  ###???
                                    )

                                if not os.path.exists(os.path.join(mpaths.build_dir, os.path.dirname(path))):
                                    os.makedirs(os.path.join(mpaths.build_dir, os.path.dirname(path)))

                                for key, path_style in list(styling_dictionary.items()):
                                    try:
                                        helper.vpkExtractor(
                                            f"{path_style[0]}.vcss_c",
                                            mpaths.dota_pak01_path,
                                            mpaths.build_dir,
                                        )
                                    except KeyError:
                                        warnings.append(
                                            "Path does not exist in VPK -> '{}', error in 'mods\\{}\\styling.txt'".format(
                                                f"{path_style[0]}.vcss_c", folder
                                            )  ###???
                                        )
                                        del styling_dictionary[key]

            except Exception as exception:
                exceptiondata = traceback.format_exc().splitlines()
                warnings.append(exceptiondata[-1])
        # ---------------------------------- STEP 2 ---------------------------------- #
        # ------------------- Decompile all files in "build" folder ------------------ #
        # ---------------------------------------------------------------------------- #
        helper.add_text_to_terminal(
            helper.localization_dict["decompiling_terminal_text_var"],
            "decompiling_text",
        )
        with open(os.path.join(mpaths.logs_dir, "Source2Viewer-CLI.txt"), "w") as file:
            subprocess.run(
                [
                    mpaths.minify_dir + "/Source2Viewer-CLI.exe",
                    "--input",
                    "build",
                    "--recursive",
                    "--vpk_decompile",
                    "--output",
                    "build",
                ],
                stdout=file,
            )
        # ---------------------------------- STEP 3 ---------------------------------- #
        # -------- Check what .css files are in "build" folder and write mods -------- #
        # ---------------------------------------------------------------------------- #
        helper.add_text_to_terminal(
            helper.localization_dict["patching_terminal_text_var"],
            "patching_text_tag",
        )

        for key, path_style in list(styling_dictionary.items()):
            with open(os.path.join(mpaths.build_dir, f"{path_style[0]}.css"), "r+") as file:
                if path_style[1] not in file.read():
                    file.write("\n" + path_style[1])
        # ---------------------------------- STEP 4 ---------------------------------- #
        # -----------------  Move uncompiled files in build to content --------------- #
        # ---------------------------------------------------------------------------- #
        copytree(
            mpaths.build_dir,
            mpaths.minify_dota_compile_input_path,
            dirs_exist_ok=True,
            ignore=ignore_patterns("*.vcss_c"),
        )
        # ---------------------------------- step 5 ---------------------------------- #
        # -------------- Compile content to game with resource compiler -------------- #
        # ---------------------------------------------------------------------------- #
        if helper.workshop_installed == True:
            with open(os.path.join(mpaths.logs_dir, "resourcecompiler.txt"), "wb") as file:
                helper.add_text_to_terminal(
                    helper.localization_dict["compiling_terminal_text_var"],
                    "compiling_text",
                )
                sp_compiler = subprocess.run(
                    [
                        mpaths.dota_resource_compiler_path,
                        "-i",
                        mpaths.minify_dota_compile_input_path + "/*",
                        "-r",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                if sp_compiler.stdout != b"":
                    file.write(sp_compiler.stdout)

                if sp_compiler.stderr != b"":
                    decoded_err = sp_compiler.stderr.decode("utf-8")
                    raise Exception(decoded_err)
        # ---------------------------------- STEP 6 ---------------------------------- #
        # -------- Create VPK from game folder and save into Minify directory -------- #
        # ---------------------------------------------------------------------------- #
        newpak = vpk.new(mpaths.minify_dota_compile_output_path)
        newpak.save(os.path.join(mpaths.minify_dota_pak_output_path, "pak66_dir.vpk"))

        patching = False

        shutil.rmtree(mpaths.minify_dota_compile_input_path)
        shutil.rmtree(mpaths.minify_dota_compile_output_path)
        shutil.rmtree(mpaths.build_dir)

        unlock_interaction()
        helper.add_text_to_terminal("-------------------------------------------------------", "spacer1_text")
        helper.add_text_to_terminal(
            helper.localization_dict["success_terminal_text_var"],
            "success_text_tag",
        )
        helper.add_text_to_terminal(
            helper.localization_dict["launch_option_text_var"],
            "launch_option_text",
        )

        helper.handleWarnings(mpaths.logs_dir)

    except Exception:
        with open(os.path.join(mpaths.logs_dir, "crashlog.txt"), "w") as file:
            file.write(traceback.format_exc())

        patching = False
        helper.add_text_to_terminal("-------------------------------------------------------", "spacer2_text")
        helper.add_text_to_terminal(
            helper.localization_dict["failure_terminal_text_var"],
            "patching_failed_text_tag",
        )
        helper.add_text_to_terminal(
            helper.localization_dict["check_logs_terminal_text_var"],
            "check_logs_text_tag",
        )
        unlock_interaction()


def version_check():
    global version
    if version is not None:
        try:
            response = requests.get(mpaths.version_query)
            if response.status_code == 200:
                if version == response.text:
                    initiate_conditionals()
                else:
                    version = response.text
                    update_popup_show()
        except:  # no connection
            initiate_conditionals()


def start_text():
    ui.add_text(
        default_value="------------------------------------------------------------------",
        parent="terminal_window",
        tag="spacer_start_text_tag",
    )
    ui.add_text(source="start_text_1_var", parent="terminal_window")
    ui.add_text(source="start_text_2_var", parent="terminal_window")
    ui.add_text(source="start_text_3_var", parent="terminal_window")
    ui.add_text(source="start_text_4_var", parent="terminal_window")
    ui.add_text(source="start_text_5_var", parent="terminal_window")
    ui.add_text(default_value="", parent="terminal_window")
    ui.add_text(default_value="", parent="terminal_window")
    helper.scroll_to_terminal_end()


def close_active_window():
    active_window = ui.get_item_alias(ui.get_active_window())
    if active_window != "terminal_window" and active_window != "primary_window" and active_window != "top_bar":
        if active_window == "update_popup":
            delete_update_popup()
        else:
            ui.configure_item(active_window, show=False)


def create_ui():
    with ui.window(tag="primary_window", no_close=True, no_title_bar=True):
        ui.set_primary_window("primary_window", True)
        ui.add_child_window(
            tag="top_bar",
            pos=(-5, -5),
            height=30,
            width=499,
            no_scrollbar=True,
            no_scroll_with_mouse=True,
        )
        ui.add_image_button(
            "discord_texture_tag",
            parent="top_bar",
            width=21,
            height=16,
            pos=(55, 7),
            callback=open_discord_link,
        )
        ui.add_image_button(
            "git_texture_tag",
            parent="top_bar",
            width=18,
            height=18,
            pos=(87, 6),
            callback=open_github_link,
        )
        ui.add_button(
            parent="top_bar",
            tag="exit_button",
            label="Close",
            callback=helper.close,
            height=28,
            width=60,
            pos=(440, 5),
        )
        ui.add_combo(
            parent="top_bar",
            tag="lang_select",
            items=(helper.localizations),
            default_value="EN",
            width=50,
            pos=(5, 6),
            callback=helper.change_localization,
        )
        ui.bind_item_font("lang_select", combo_font)
        with ui.group(horizontal=True):
            with ui.group(pos=(391, 29)):
                ui.add_button(
                    tag="button_patch",
                    label="Patch",
                    width=92,
                    callback=patcher_start,
                )
                ui.add_button(
                    tag="button_select_mods",
                    label="Select Mods",
                    width=92,
                    callback=open_mod_menu,
                )
                ui.add_button(
                    tag="button_uninstall",
                    label="Uninstall",
                    width=92,
                    callback=uninstall_popup_show,
                )
            with ui.group(pos=(-45, 4)):
                ui.add_text(
                    r"""
         __    __    __    __   __    __    ______  __  __
        /\ "-./  \  /\ \  /\ "-.\ \  /\ \  /\  ___\/\ \_\ \  
        \ \ \-./\ \ \ \ \ \ \ \-.  \ \ \ \ \ \  __\\ \____ \ 
         \ \_\ \ \_\ \ \_\ \ \_\\"\_\ \ \_\ \ \_\_/ \/\_____\
          \/_/  \/_/  \/_/  \/_/ \/_/  \/_/  \/_/    \/_____/""",
                )
        # Creating log terminal
        with ui.group():
            ui.add_window(
                tag="terminal_window",
                no_scrollbar=False,
                no_title_bar=True,
                no_move=True,
                no_collapse=True,
                modal=False,
                no_close=True,
                no_saved_settings=True,
                show=True,
                height=200,
                width=494,
                pos=(0, 100),
                no_resize=True,
            )

    ui.add_window(
        label="Uninstall",
        modal=True,
        no_move=True,
        tag="uninstall_popup",
        show=False,
        no_collapse=True,
        no_close=True,
        no_saved_settings=True,
        autosize=True,
        no_resize=True,
        no_title_bar=True,
    )
    ui.add_group(tag="uninstall_popup_text_wrapper", parent="uninstall_popup")
    ui.add_text(
        default_value="Remove all mods?",
        parent="uninstall_popup_text_wrapper",
        tag="remove_mods_text_tag",
    )
    with ui.group(
        parent="uninstall_popup",
        tag="uninstall_popup_button_wrapper",
        horizontal=True,
        horizontal_spacing=10,
    ):
        ui.add_button(
            label="Confirm",
            tag="uninstall_confirm_button",
            callback=uninstaller,
            width=100,
        )
        ui.add_button(
            label="Cancel",
            tag="uninstall_cancel_button",
            callback=hide_uninstall_popup,
            width=100,
        )

    # Creating mod selection menu as popup/modal
    ui.add_window(
        modal=False,
        pos=(0, 0),
        tag="mod_menu",
        label=f"{helper.mod_selection_window_var}",
        menubar=False,
        no_title_bar=False,
        no_move=True,
        no_collapse=True,
        no_close=False,
        no_open_over_existing_popup=True,
        height=300,
        width=494,
        show=False,
        no_resize=True,
        on_close=save_state,
    )

    ui.add_window(
        modal=True,
        no_move=True,
        tag="update_popup",
        show=False,
        autosize=True,
        no_collapse=True,
        no_close=True,
        no_saved_settings=True,
        no_resize=True,
        no_title_bar=True,
    )
    ui.add_group(parent="update_popup", tag="popup_text_wraper_1")
    ui.add_text(
        default_value="New update is now available!",
        parent="popup_text_wraper_1",
        tag="update_popup_text_1_tag",
        indent=1,
    )
    ui.add_group(parent="update_popup", tag="popup_text_wraper_2")
    ui.add_text(
        default_value="Would you like to go to the download page?",
        parent="popup_text_wraper_2",
        tag="update_popup_text_2_tag",
        indent=1,
    )
    with ui.group(
        parent="update_popup",
        tag="update_popup_button_group",
        horizontal=True,
        horizontal_spacing=20,
    ):
        ui.add_button(
            label="Yes",
            width=120,
            height=24,
            callback=open_github_link_and_close_minify,
            tag="update_popup_yes_button",
        )
        ui.add_button(
            label="No",
            width=120,
            height=24,
            callback=delete_update_popup,
            tag="update_popup_no_button",
        )


def configure_update_popup():
    ui.configure_item(
        "update_popup",
        pos=(
            ui.get_viewport_width() / 2 - ui.get_item_rect_size("update_popup")[0] / 2,
            ui.get_viewport_height() / 2 - ui.get_item_rect_size("update_popup")[1] / 2,
        ),
    )
    ui.configure_item(
        "popup_text_wraper_1",
        pos=(
            ui.get_item_rect_size("update_popup")[0] / 2 - ui.get_item_rect_size("popup_text_wraper_1")[0] / 2,
            ui.get_item_rect_size("update_popup")[1] / 2 - ui.get_item_rect_size("popup_text_wraper_1")[1] / 2 - 30,
        ),
    )
    ui.configure_item(
        "popup_text_wraper_2",
        pos=(
            ui.get_item_rect_size("update_popup")[0] / 2 - ui.get_item_rect_size("popup_text_wraper_2")[0] / 2,
            ui.get_item_rect_size("update_popup")[1] / 2 - ui.get_item_rect_size("popup_text_wraper_2")[1] / 2 - 8,
        ),
    )
    ui.configure_item(
        "update_popup_button_group",
        pos=(
            ui.get_item_rect_size("update_popup")[0] / 2 - ui.get_item_rect_size("update_popup_button_group")[0] / 2,
            ui.get_item_rect_size("update_popup")[1] / 2
            - ui.get_item_rect_size("update_popup_button_group")[1] / 2
            + 26,
        ),
    )


def configure_uninstall_popup():
    ui.configure_item(
        "uninstall_popup",
        pos=(
            ui.get_viewport_width() / 2 - ui.get_item_rect_size("uninstall_popup")[0] / 2,
            ui.get_viewport_height() / 2 - ui.get_item_rect_size("uninstall_popup")[1] / 2,
        ),
    )
    ui.configure_item(
        "uninstall_popup_text_wrapper",
        pos=(
            ui.get_item_rect_size("uninstall_popup")[0] / 2
            - ui.get_item_rect_size("uninstall_popup_text_wrapper")[0] / 2,
            ui.get_item_rect_size("uninstall_popup")[1] / 2
            - ui.get_item_rect_size("uninstall_popup_text_wrapper")[1] / 2
            - 20,
        ),
    )
    ui.configure_item(
        "uninstall_popup_button_wrapper",
        pos=(
            ui.get_item_rect_size("uninstall_popup")[0] / 2
            - ui.get_item_rect_size("uninstall_popup_button_wrapper")[0] / 2,
            ui.get_item_rect_size("uninstall_popup")[1] / 2
            - ui.get_item_rect_size("uninstall_popup_button_wrapper")[1] / 2
            + 10,
        ),
    )


def create_base_ui():
    helper.get_available_localizations()
    create_ui()
    theme()
    helper.change_localization(init=True)
    version_check()
    time.sleep(0.05)  # if popup's sizes break, increase this value
    configure_update_popup()


def initiate_conditionals():
    setup_system_thread = threading.Thread(target=setupSystem)
    load_state_checkboxes_thread = threading.Thread(target=load_state_checkboxes)
    setup_system_thread.start()
    load_state_checkboxes_thread.start()
    setup_system_thread.join()
    load_state_checkboxes_thread.join()
    create_checkboxes()
    setupButtonState()
    start_text()


# Adding font to the ui registry
with ui.font_registry():
    with ui.font(f"{mpaths.bin_dir}/FiraMono-Medium.ttf", 14) as main_font:
        ui.add_font_range_hint(ui.mvFontRangeHint_Default)
        ui.add_font_range_hint(ui.mvFontRangeHint_Cyrillic)
        ui.bind_font(main_font)
    with ui.font(f"{mpaths.bin_dir}/FiraMono-Medium.ttf", 16) as combo_font:
        ui.add_font_range_hint(ui.mvFontRangeHint_Default)
        ui.add_font_range_hint(ui.mvFontRangeHint_Cyrillic)

# Adding mouse handler to ui registry
with ui.handler_registry():
    ui.add_mouse_drag_handler(parent="top_bar", button=0, threshold=0.0, callback=drag_viewport)
    ui.add_key_release_handler(0x20E, callback=close_active_window)

width_discord, height_discord, channels_discord, data_discord = ui.load_image(
    f"{mpaths.img_dir}\\Discord-Symbol-White.png"
)

width_git, height_git, channels_git, data_git = ui.load_image(f"{mpaths.img_dir}\\github-mark-white.png")

with ui.texture_registry(show=False):
    ui.add_static_texture(
        width=width_discord,
        height=height_discord,
        default_value=data_discord,
        tag="discord_texture_tag",
    )
    ui.add_static_texture(
        width=width_git,
        height=height_git,
        default_value=data_git,
        tag="git_texture_tag",
    )


def theme():
    with ui.theme() as global_theme:
        with ui.theme_component(ui.mvAll):
            ui.add_theme_style(ui.mvStyleVar_WindowPadding, x=12, y=4)
            ui.add_theme_color(ui.mvThemeCol_Text, (0, 230, 230))
            ui.add_theme_color(ui.mvThemeCol_WindowBg, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_ChildBg, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_ScrollbarBg, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_ScrollbarGrab, (0, 200, 200))
            ui.add_theme_color(ui.mvThemeCol_ScrollbarGrabHovered, (0, 170, 170))
            ui.add_theme_color(ui.mvThemeCol_ScrollbarGrabActive, (0, 120, 120))
            ui.add_theme_color(ui.mvThemeCol_TitleBg, (35, 35, 35, 255))
            ui.add_theme_color(ui.mvThemeCol_TitleBgActive, (35, 35, 35, 255))
            ui.add_theme_color(ui.mvThemeCol_Header, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_HeaderHovered, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_HeaderActive, (17, 17, 18, 255))

    ui.bind_theme(global_theme)

    with ui.theme() as main_buttons_theme:
        with ui.theme_component():
            ui.add_theme_color(ui.mvThemeCol_Button, (0, 230, 230, 6))
            ui.add_theme_color(ui.mvThemeCol_ButtonHovered, (17, 17, 18, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonActive, (15, 15, 15, 255))
            ui.add_theme_style(ui.mvStyleVar_ButtonTextAlign, x=0, y=0.5)
        with ui.theme_component(enabled_state=False):
            ui.add_theme_color(ui.mvThemeCol_Text, (0, 100, 100))
            ui.add_theme_color(ui.mvThemeCol_Button, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonHovered, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonActive, (29, 29, 30, 255))
            ui.add_theme_style(ui.mvStyleVar_ButtonTextAlign, x=0, y=0.5)

    with ui.theme() as close_button_theme:
        with ui.theme_component():
            ui.add_theme_color(ui.mvThemeCol_Text, (0, 230, 230))
            ui.add_theme_color(ui.mvThemeCol_Button, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonHovered, (17, 17, 18, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonActive, (15, 15, 15, 255))
        with ui.theme_component(enabled_state=False):
            ui.add_theme_color(ui.mvThemeCol_Text, (0, 100, 100))
            ui.add_theme_color(ui.mvThemeCol_Button, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonHovered, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonActive, (29, 29, 30, 255))

    with ui.theme() as mod_menu_theme:
        with ui.theme_component():
            ui.add_theme_color(ui.mvThemeCol_FrameBg, (24, 24, 24, 255))
            ui.add_theme_color(ui.mvThemeCol_CheckMark, (0, 230, 230, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgHovered, (20, 20, 20, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgActive, (20, 20, 20, 255))
        with ui.theme_component(ui.mvCheckbox, enabled_state=False):
            ui.add_theme_color(ui.mvThemeCol_Text, (0, 100, 100))
            ui.add_theme_color(ui.mvThemeCol_FrameBg, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgHovered, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgActive, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_CheckMark, (29, 29, 30, 255))
        with ui.theme_component():
            ui.add_theme_color(ui.mvThemeCol_Text, (0, 230, 230))
            ui.add_theme_color(ui.mvThemeCol_Button, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonHovered, (17, 17, 18, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonActive, (29, 29, 30, 255))
        with ui.theme_component(enabled_state=False):
            ui.add_theme_color(ui.mvThemeCol_Button, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_Text, (0, 100, 100))
            ui.add_theme_color(ui.mvThemeCol_ButtonHovered, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonActive, (29, 29, 30, 255))

    with ui.theme() as top_bar_theme:
        with ui.theme_component():
            ui.add_theme_color(ui.mvThemeCol_Text, (0, 230, 230))
            ui.add_theme_color(ui.mvThemeCol_Button, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonHovered, (17, 17, 18, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonActive, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBg, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgHovered, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgActive, (29, 29, 30, 255))
        with ui.theme_component(enabled_state=False):
            ui.add_theme_color(ui.mvThemeCol_Button, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_Text, (0, 100, 100))
            ui.add_theme_color(ui.mvThemeCol_ButtonHovered, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonActive, (29, 29, 30, 255))
        with ui.theme_component(ui.mvCheckbox):
            ui.add_theme_color(ui.mvThemeCol_FrameBg, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgHovered, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgActive, (29, 29, 30, 255))

    with ui.theme() as popup_theme:
        with ui.theme_component():
            ui.add_theme_color(ui.mvThemeCol_Text, (0, 230, 230))
            ui.add_theme_color(ui.mvThemeCol_Button, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonHovered, (17, 17, 18, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonActive, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBg, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgHovered, (29, 29, 30, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgActive, (29, 29, 30, 255))

    ui.bind_item_theme("button_patch", main_buttons_theme)
    ui.bind_item_theme("button_select_mods", main_buttons_theme)
    ui.bind_item_theme("button_uninstall", main_buttons_theme)
    ui.bind_item_theme("exit_button", close_button_theme)
    ui.bind_item_theme("mod_menu", mod_menu_theme)
    ui.bind_item_theme("top_bar", top_bar_theme)
    ui.bind_item_theme("update_popup", popup_theme)
    ui.bind_item_theme("uninstall_popup", popup_theme)


# Creating_main_viewport
ui.create_viewport(
    title="Minify",
    height=300,
    width=494,
    resizable=False,
    decorated=False,
    vsync=True,
    clear_color=(0, 0, 0, 255),
)

ui.set_frame_callback(1, callback=create_base_ui)  # On first frame execute app_start


# DearPyGyi Setup
ui.setup_dearpygui()
ui.show_viewport()
ui.start_dearpygui()
ui.destroy_context()
