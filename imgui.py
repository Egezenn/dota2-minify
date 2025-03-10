import json
import os
import platform
import shutil
import subprocess
import time
import traceback
from shutil import copytree, ignore_patterns

import dearpygui.dearpygui as ui
import psutil
import requests
import vpk

import helper_n as helper
import mpaths
import validatefiles_n as validatefiles

ui.create_context()

version = None

try:
    with open("version", "r") as file:
        version = file.readline()
except:
    pass


localizations = []
patching = False
checkboxes = {}
checkboxes_state = {}
blacklist_dictionary = {}
styling_dictionary = {}

blue = (0, 230, 230)
header_pad_y = 16


def save_init():
    # ui.save_init_file("dpg.ini")
    save_state_checkboxes()


class Extension:
    def __init__(self, path):
        self.path = path
        self.css = path + ".css"
        self.vcss_c = path + ".vcss_c"
        self.xml = path + ".xml"
        self.vxml_C = path + ".vxml_c"


class Path:
    def __init__(self, path, style):
        self.path = Extension(path)
        self.style = style


class TextRedirector(object):
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag

    def write(self, str):
        self.widget.configure(state="normal")
        self.widget.insert("end", " " + str, (self.tag))
        self.widget.see("end")
        self.widget.configure(state="disabled")


def get_available_localizations():
    global localizations
    with open(mpaths.localization_file_dir, "r", encoding="utf-8") as file:
        localization_data = json.load(file)
    sub_headers = set()

    for header in localization_data.values():
        if isinstance(header, dict):
            sub_headers.update(header.keys())

    localizations = list(sub_headers)


def change_localization(init=False):
    with open(mpaths.localization_file_dir, "r", encoding="utf-8") as localization_file:
        localization_data = json.load(localization_file)

    if init == True:
        if os.path.exists(mpaths.locale_file_dir):
            with open(mpaths.locale_file_dir, "r") as file:
                locale = file.readline()
                ui.configure_item("lang_select", default_value=f"{locale}")
    else:
        locale = ui.get_value("lang_select")
        with open(mpaths.locale_file_dir, "w") as file:
            file.write(locale)

    for key, value in localization_data.items():
        try:
            if ui.get_item_info(key).get("type") == "mvAppItemType::mvButton":
                if locale in localization_data[key]:
                    ui.configure_item(key, label=value[locale])
                else:  # default to english if the line isn't available on selected locale
                    ui.configure_item(key, label=value["EN"])

            if ui.get_item_info(key).get("type") == "mvAppItemType::mvText":
                if locale in localization_data[key]:
                    ui.configure_item(key, default_value=value[locale])
                else:
                    ui.configure_item(key, default_value=value["EN"])
        except:  # find out later what this is
            pass  # <built-in function get_item_info> returned a result with an exception set


def lock_interaction():
    ui.configure_item("terminal_window", modal=True)
    time.sleep(0.01)
    ui.configure_item("terminal_window", pos=(0, 197))


def unlock_interaction():
    ui.configure_item("terminal_window", modal=False)


def delete_update_popup():
    ui.configure_item("update_popup", show=False)
    ui.delete_item("update_popup")


def hide_uninstall_popup():
    ui.configure_item("uninstall_popup", show=False)


def open_github_link_and_close_minify():
    open_github_link()  # behavior to download the latest release
    close()


def save_state_checkboxes():
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


# Creating window draging functionality
def drag_viewport(sender, app_data, user_data):
    if (
        ui.is_item_hovered("top_bar") == True
    ):  # Check if mouse is over the top_bar the restrict area of drag handler(Note: If local pos [1] < *Height_of_top_bar is buggy)
        drag_deltas = app_data
        viewport_current_pos = ui.get_viewport_pos()
        new_x_position = viewport_current_pos[0] + drag_deltas[1]
        new_y_position = viewport_current_pos[1] + drag_deltas[2]
        new_y_position = max(
            new_y_position, 0
        )  # prevent the viewport to go off the top of the screen
        ui.set_viewport_pos([new_x_position, new_y_position])


def open_mod_menu():
    ui.configure_item("mod_menu", show=True)


def close_mod_menu():
    ui.configure_item("mod_menu", show=False)


def open_discord_link():
    helper.urlDispatcher(mpaths.discord)


def open_github_link():
    helper.urlDispatcher(mpaths.latest_release)


def close():
    ui.stop_dearpygui()


def unistall_popup_show():
    ui.configure_item("uninstall_popup", show=True)


def create_checkboxes():
    global checkboxes_state
    for index in range(len(mpaths.mods_folders)):
        name = mpaths.mods_folders[index]
        ui.add_group(
            parent="mod_menu", tag=f"{name}_group_tag", horizontal=True, width=300
        )
        ui.add_checkbox(
            parent=f"{name}_group_tag",
            label=name,
            tag=name,
            default_value=False,
            callback=setupButtonState,
        )
        for key in checkboxes_state.keys():
            if key == name:
                ui.configure_item(
                    name,
                    default_value=checkboxes_state[name],
                )

        mod_path = os.path.join(mpaths.mods_dir, name)
        notes_txt = os.path.join(mod_path, "notes.txt")
        with open(notes_txt, "r", encoding="utf-8") as file:
            data = file.read()

        data2 = f"{name}_details_window_tag"
        ui.add_button(
            parent=f"{name}_group_tag",
            small=True,
            indent=200,
            tag=f"{name}_button_show_details_tag",
            label="Details",
            callback=show_details,
            user_data=f"{name}_details_window_tag",
        )

        ui.add_window(
            tag=f"{name}_details_window_tag",
            pos=(0, 0),
            show=False,
            width=538,
            height=400,
            no_resize=True,
            no_move=True,
            no_collapse=True,
            label=f"{name}",
        )
        ui.add_text(
            default_value=f"{data}", parent=f"{name}_details_window_tag", wrap=482
        )

        current_box = name
        checkboxes[current_box] = name


def show_details(sender, app_data, user_data):
    ui.configure_item(user_data, show=True)


def update_popup_show():
    ui.add_window(
        label=f"Update {version} is now available!",
        modal=True,
        no_move=True,
        tag="update_popup",
        show=True,
        no_collapse=True,
        no_close=True,
        no_saved_settings=True,
        no_resize=True,
        width=310,
        height=100,
    )
    ui.configure_item(
        "update_popup",
        pos=(
            ui.get_viewport_width() / 2 - ui.get_item_width("update_popup") / 2,
            ui.get_viewport_height() / 2 - ui.get_item_height("update_popup") / 2,
        ),
    )
    ui.add_text(
        default_value="Would you like to go to the download page?",
        parent="update_popup",
        indent=1,
        color=blue,
    )
    with ui.group(
        parent="update_popup",
        tag="update_popup_button_group",
        horizontal=True,
        horizontal_spacing=10,
        indent=42,
    ):
        ui.add_button(
            label="Yes",
            width=100,
            height=20,
            callback=open_github_link_and_close_minify,
            tag="update_popup_yes_button",
        )
        ui.add_button(
            label="No",
            width=100,
            height=20,
            callback=delete_update_popup,
            tag="update_popup_no_button",
        )


def setupSystem():
    os.makedirs("logs", exist_ok=True)
    x = validatefiles.Requirements(checkboxes)
    public_methods = [
        method
        for method in dir(x)
        if callable(getattr(x, method))
        if not method.startswith("_")
    ]  # private methods start with _
    try:
        if not (
            os.path.exists(os.path.join(mpaths.minify_dir, "Source2Viewer-CLI.exe"))
            or os.path.exists(os.path.join(mpaths.minify_dir, "libSkiaSharp.dll"))
            or os.path.exists(os.path.join(mpaths.minify_dir, "TinyEXR.Native.dll"))
        ):
            if platform.system() == "Windows":
                helper.add_text_to_terminal(
                    text="Downloading Source2Viewer-CLI...",
                    tag="downloading_s2v_cli_tag",
                )
                helper.scroll_to_terminal_end()
                zip_name = "cli-windows-x64.zip"
                zip_path = os.path.join(mpaths.minify_dir, zip_name)
                response = requests.get(mpaths.v2f_latest_windows_x64)
                if response.status_code == 200:
                    with open(zip_path, "wb") as file:
                        file.write(response.content)
                    helper.add_text_to_terminal(
                        text=f"-> Downloaded {zip_name}", tag="downloaded_text_tag"
                    )
                    helper.scroll_to_terminal_end()
                    shutil.unpack_archive(zip_path, mpaths.minify_dir, "zip")
                    os.remove(zip_path)
                    helper.add_text_to_terminal(
                        text=f"-> Extracted {zip_name}", tag="extracted_text_tag"
                    )
                    helper.scroll_to_terminal_end()
            else:
                ui.add_text(
                    default_value="Error: Instructions to download Source2Viewer binaries for your system is not available yet, click Help for instructions.",
                    parent="terminal_window",
                    tag="error_cli_download_text",
                )
                helper.scroll_to_terminal_end()
        for method in public_methods:
            getattr(x, method)()
            if x.toggle_flag == True:
                lock_interaction()
                break
    except Exception:
        with open(os.path.join(mpaths.logs_dir, "crashlog.txt"), "w") as file:
            file.write(traceback.format_exc())
            lock_interaction()
            ui.add_text(
                default_value="Failed to start!",
                parent="terminal_window",
                tag="failed_to_start_text",
            )
            helper.scroll_to_terminal_end()
            ui.add_text(
                default_value="Check 'logs\\crashlog.txt' for more info.",
                parent="terminal_window",
                tag="check_logs_text",
            )
            helper.scroll_to_terminal_end()


def setupButtonState():
    for box in checkboxes:
        if ui.get_value(box) == True:
            ui.configure_item("button_patch", enabled=True)
            # self.patchBtn.config(state="normal", cursor="hand2")
            break
        else:
            ui.configure_item("button_patch", enabled=False)  # Disabled theme? TODO
            # self.patchBtn.config(state="disabled", cursor="")
    if helper.workshop_installed == False:
        print(f"Disabling mods cause {helper.workshop_installed}")
        helper.disableWorkshopMods(mpaths.mods_dir, mpaths.mods_folders, checkboxes)


def uninstaller():
    hide_uninstall_popup()
    clean_terminal()
    time.sleep(0.01)
    # lock_interaction()
    # remove pak01_dir.vpk if it exists
    vpkPath = os.path.join(mpaths.dota_minify, "pak01_dir.vpk")
    if os.path.exists(vpkPath):
        os.remove(vpkPath)

    # remove dota.vpk if it exists
    mapPath = os.path.join(mpaths.dota_minify_maps, "dota.vpk")
    if os.path.exists(mapPath):
        os.remove(mapPath)

    try:
        with open(
            os.path.join(mpaths.itembuilds_dir, "default_antimage.txt"), "r"
        ) as file:
            lines = file.readlines()
        if len(lines) >= 3:
            if "OpenDotaGuides" in lines[2]:
                for name in os.listdir(mpaths.itembuilds_dir):
                    if name != "bkup":
                        os.remove(os.path.join(mpaths.itembuilds_dir, name))
                # print(os.path.join(mpaths.itembuilds_dir, "bkup"))
                for name in os.listdir(os.path.join(mpaths.itembuilds_dir, "bkup")):
                    os.rename(
                        os.path.join(mpaths.itembuilds_dir, "bkup", name),
                        os.path.join(mpaths.itembuilds_dir, name),
                    )
    except FileNotFoundError:
        helper.warnings.append(
            "Unable to recover backed up default guides or the itembuilds directory is empty, verify files to get the default guides back"
        )
    helper.add_text_to_terminal(
        text="All Minify mods have been removed.", tag="uninstaller_text_tag"
    )
    helper.scroll_to_terminal_end()
    # unlock_interaction()


def clean_terminal():
    ui.delete_item("terminal_window", children_only=True)


def patcher():
    global patching
    clean_terminal()
    # lock_interaction()
    if "dota2.exe" in (p.name() for p in psutil.process_iter()):
        ui.add_text(
            default_value="Please close Dota 2 first and then patch.",
            tag="close_dota_text",
            parent="terminal_window",
            wrap=400,
            color=blue,
        )
        return

    patching = True

    try:
        # clean up previous patching data
        helper.cleanFolders(
            mpaths.build_dir,
            mpaths.logs_dir,
            mpaths.content_dir,
            mpaths.game_dir,
            mpaths.minify_dir,
            mpaths.dota_minify_maps,
        )

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
                            f"-> Installing {folder}", f"installing_{folder}_text"
                        )
                        if (
                            checkboxes[box] == "Dark Terrain"
                            or checkboxes[box] == "Remove Foilage"
                        ):
                            shutil.copytree(
                                mpaths.maps_dir,
                                os.path.join(
                                    mpaths.dota_minify,
                                    os.path.basename(mpaths.maps_dir),
                                ),
                                dirs_exist_ok=True,
                            )
                        if checkboxes[box] == "OpenDotaGuides Guides":
                            zip_path = os.path.join(
                                mod_path, "files", "OpenDotaGuides.zip"
                            )
                            temp_dump_path = os.path.join(mod_path, "files", "temp")
                            if os.path.exists(zip_path):
                                os.remove(zip_path)
                            response = requests.get(mpaths.odg_latest)
                            if response.status_code == 200:
                                with open(zip_path, "wb") as file:
                                    file.write(response.content)
                                helper.add_text_to_terminal(
                                    "-> Downloaded latest OpenDotaGuides guides.",
                                    "downloaded_open_dota_guides_text",
                                )
                                os.makedirs(
                                    os.path.join(mpaths.itembuilds_dir, "bkup"),
                                    exist_ok=True,
                                )
                                for name in os.listdir(mpaths.itembuilds_dir):
                                    try:
                                        if name != "bkup":
                                            os.rename(
                                                os.path.join(
                                                    mpaths.itembuilds_dir, name
                                                ),
                                                os.path.join(
                                                    mpaths.itembuilds_dir,
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
                                        os.path.join(mpaths.itembuilds_dir, file),
                                    )
                                shutil.rmtree(temp_dump_path)
                                os.remove(zip_path)
                                helper.add_text_to_terminal(
                                    "-> Replaced default guides with OpenDotaGuides guides.",
                                    "replaced_open_dota_guides_text",
                                )
                                if os.path.exists(zip_path):
                                    os.remove(zip_path)
                            else:
                                helper.add_text_to_terminal(
                                    "-> Failed to download latest OpenDotaGuides guides.",
                                    "failed_downloading_open_dota_guides",
                                )
                        # ----------------------------------- files ---------------------------------- #
                        # if files_total == 0:    pass
                        # elif files_total == 1:  print(f"    files: Found {files_total} file")
                        # else:                   print(f"    files: Found {files_total} files")
                        shutil.copytree(
                            os.path.join(mod_path, "files"),
                            mpaths.game_dir,
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
                                            mpaths.pak01_dir,
                                        ):
                                            blacklist_data.append(path)
                                        continue

                                    elif line.startswith(">>"):
                                        for path in helper.processBlacklistDir(
                                            index, line, folder, mpaths.pak01_dir
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

                            # print(f"    blacklist.txt: Found {len(blacklist_data)} paths")

                            for index, line in enumerate(blacklist_data):
                                line = line.strip()
                                path, extension = os.path.splitext(line)

                                # blacklist_dictionary["blacklist-key{}".format(index+1)] = path, extension

                                if not os.path.exists(
                                    os.path.join(mpaths.game_dir, os.path.dirname(path))
                                ):
                                    os.makedirs(
                                        os.path.join(
                                            mpaths.game_dir, os.path.dirname(path)
                                        )
                                    )

                                try:
                                    shutil.copy(
                                        os.path.join(
                                            mpaths.blank_files_dir, "blank{}"
                                        ).format(extension),
                                        os.path.join(mpaths.game_dir, path + extension),
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

                            # print(f"    styling.txt: Found styling.txt")

                            for index, line in enumerate(styling_data):
                                try:
                                    line = line.split("@@")
                                    path = line[0].strip()
                                    style = line[1].strip()

                                    styling_dictionary[
                                        "styling-key{}".format(index + 1)
                                    ] = (path, style)

                                except Exception as exception:
                                    warnings.append(
                                        "[{}]".format(type(exception).__name__)
                                        + " Could not validate '{}' in --> 'mods\\{}\\styling.txt' [line: {}]".format(
                                            line, folder, index + 1
                                        )  ###???
                                    )

                                if not os.path.exists(
                                    os.path.join(
                                        mpaths.build_dir, os.path.dirname(path)
                                    )
                                ):
                                    os.makedirs(
                                        os.path.join(
                                            mpaths.build_dir, os.path.dirname(path)
                                        )
                                    )

                                for key, value in list(styling_dictionary.items()):
                                    construct1 = Path(value[0], value[1])
                                    try:
                                        helper.vpkExtractor(
                                            construct1.path.vcss_c,
                                            mpaths.pak01_dir,
                                            mpaths.build_dir,
                                        )
                                    except KeyError:
                                        warnings.append(
                                            "Path does not exist in VPK -> '{}', error in 'mods\\{}\\styling.txt'".format(
                                                construct1.path.vcss_c, folder
                                            )  ###???
                                        )
                                        del styling_dictionary[key]

            except Exception as exception:
                exceptiondata = traceback.format_exc().splitlines()
                warnings.append(exceptiondata[-1])
        # ---------------------------------- STEP 2 ---------------------------------- #
        # ------------------- Decompile all files in "build" folder ------------------ #
        # ---------------------------------------------------------------------------- #
        helper.add_text_to_terminal("-> Decompiling", "decompiling_text")
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
        helper.add_text_to_terminal("-> Patching", "patching_text")

        for key, value in list(styling_dictionary.items()):
            construct2 = Path(value[0], value[1])

            with open(
                os.path.join(mpaths.build_dir, construct2.path.css), "r+"
            ) as file:
                if construct2.style not in file.read():
                    file.write("\n" + construct2.style.strip())
        # ---------------------------------- STEP 4 ---------------------------------- #
        # -----------------  Move uncompiled files in build to content --------------- #
        # ---------------------------------------------------------------------------- #
        copytree(
            mpaths.build_dir,
            mpaths.content_dir,
            dirs_exist_ok=True,
            ignore=ignore_patterns("*.vcss_c"),
        )
        # ---------------------------------- step 5 ---------------------------------- #
        # -------------- Compile content to game with resource compiler -------------- #
        # ---------------------------------------------------------------------------- #
        if helper.workshop_installed == True:
            with open(
                os.path.join(mpaths.logs_dir, "resourcecompiler.txt"), "wb"
            ) as file:
                helper.add_text_to_terminal("-> Compiling", "compiling_text")
                sp_compiler = subprocess.run(
                    [
                        mpaths.resource_compiler,
                        "-i",
                        mpaths.content_dir + "/*",
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
        newpak = vpk.new(mpaths.game_dir)
        newpak.save(os.path.join(mpaths.dota_minify, "pak01_dir.vpk"))

        patching = False

        # unlock_interaction()
        helper.add_text_to_terminal("-> Done!", "done_text")
        helper.add_text_to_terminal(
            "-------------------------------------------------------", "spacer1_text"
        )
        helper.add_text_to_terminal(
            "Remember to add '-language minify' to dota2 launch options",
            "launch_option_text",
        )
        helper.add_text_to_terminal(
            "Click Help button below for instructions", "help_text"
        )

        helper.handleWarnings(mpaths.logs_dir)

    except Exception:
        with open(os.path.join(mpaths.logs_dir, "crashlog.txt"), "w") as file:
            file.write(traceback.format_exc())

        patching = False
        helper.add_text_to_terminal("Patching failed.", "patching_failed_text")
        helper.add_text_to_terminal(
            """Check 'logs\\crashlog.txt' for more info.""", "check_logs_text"
        )
        helper.add_text_to_terminal(
            "-------------------------------------------------------", "spacer2_text"
        )


def version_check():
    global version
    if version is not None:
        response = requests.get(mpaths.version_query)
        if response.status_code == 200:
            if version == response.text:
                ui.configure_item("button_latest", enabled=False)
            else:
                ui.configure_item("button_latest", enabled=True)
                version = response.text
                update_popup_show()


def app_start():
    ui.configure_app(init_file="dpg.ini")
    get_available_localizations()
    create_ui()
    change_localization(init=True)
    version_check()
    setupSystem()
    load_state_checkboxes()
    helper.validate_map_file()
    create_checkboxes()
    setupButtonState()
    ui.show_style_editor()
    ui.show_metrics()


# Adding font to the ui registry
with ui.font_registry():
    with ui.font(f"{mpaths.bin_dir}/FiraMono-Medium.ttf", 14) as main_font:
        ui.add_font_range_hint(ui.mvFontRangeHint_Default)
        ui.add_font_range_hint(ui.mvFontRangeHint_Cyrillic)
        ui.bind_font(main_font)


def close_active_window():
    if (
        ui.get_active_window() != 29
        and ui.get_active_window() != 49
        and ui.get_active_window() != 30
    ):
        ui.configure_item(ui.get_active_window(), show=False)


# Adding mouse handler to ui registry
with ui.handler_registry():
    ui.add_mouse_drag_handler(
        parent="top_bar", button=0, threshold=0.0, callback=drag_viewport
    )
    ui.add_key_release_handler(0x20E, callback=close_active_window)


# Creating_main_viewport
ui.create_viewport(
    title="Minify",
    height=400,
    width=538,
    resizable=False,
    decorated=False,
    vsync=True,
    clear_color=(0, 0, 0, 255),
)


# Creating main window of GUI and UI elements
def create_ui():
    with ui.window(tag="primary_window", no_close=True, no_title_bar=True):
        ui.set_primary_window("primary_window", True)
        ui.add_child_window(tag="top_bar", pos=(-5, -5), height=25, width=543)
        with ui.group(horizontal=True):
            with ui.group(pos=(8, 27)):
                ui.add_button(
                    tag="button_patch",
                    label="Patch",
                    width=100,
                    callback=patcher,
                )
                ui.add_button(
                    tag="button_select_mods",
                    label="Select Mods",
                    width=100,
                    callback=open_mod_menu,
                )
                ui.add_combo(
                    tag="lang_select",
                    items=(localizations),
                    default_value="EN",
                    width=100,
                    callback=change_localization,
                )
                ui.add_button(
                    tag="button_discord",
                    label="Discord",
                    width=100,
                    callback=open_discord_link,
                )
                ui.add_button(
                    tag="button_latest",
                    label="Latest",
                    width=100,
                    callback=open_github_link,
                )
                ui.add_button(
                    tag="uninstall_button",
                    label="Uninstall",
                    width=100,
                    callback=unistall_popup_show,
                )
                ui.add_button(
                    tag="exit_button", label="Exit", width=100, callback=close
                )
            with ui.group(pos=(67, -2)):
                ui.add_text(
                    r"""
         __    __     __     __   __     __     ______   __  __
        /\ "-./  \   /\ \   /\ "-.\ \   /\ \   /\  ___\ /\ \_\ \  
        \ \ \-./\ \  \ \ \  \ \ \-.  \  \ \ \  \ \  __\ \ \____ \ 
         \ \_\ \ \_\  \ \_\  \ \_\\"\_\  \ \_\  \ \_\_/  \/\_____\
          \/_/  \/_/   \/_/   \/_/ \/_/   \/_/   \/_/     \/_____/
        ----------------------------------------------------------""",
                    color=blue,
                )
                ui.add_text(
                    "Want to contribute to the project's growth?",
                    tag="header_text_1",
                    pos=(124, 15 + header_pad_y * 5),
                    color=blue,
                )
                ui.add_text(
                    "-> Join our Discord community!",
                    tag="header_text_2",
                    color=blue,
                    pos=(123, 15 + header_pad_y * 6),
                )
                ui.add_text(
                    "-> Share Minify with your friends and online groups",
                    tag="header_text_3",
                    color=blue,
                    pos=(123, 15 + header_pad_y * 7),
                )
                ui.add_text(
                    "-> Star the project on GitHub",
                    tag="header_text_4",
                    color=blue,
                    pos=(123, 15 + header_pad_y * 8),
                )
                ui.add_text(
                    "-> Create and maintain mods for this project",
                    tag="header_text_5",
                    color=blue,
                    pos=(123, 15 + header_pad_y * 9),
                )
                ui.add_text(
                    "----------------------------------------------------------",
                    color=blue,
                    pos=(123, 15 + header_pad_y * 10),
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
                height=203,
                width=538,
                pos=(0, 197),
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
        width=310,
        height=100,
        no_resize=True,
    )
    ui.configure_item(
        "uninstall_popup",
        pos=(
            ui.get_viewport_width() / 2 - ui.get_item_width("uninstall_popup") / 2,
            ui.get_viewport_height() / 2 - ui.get_item_height("uninstall_popup") / 2,
        ),
    )
    ui.add_text(
        default_value="Remove all mods?",
        parent="uninstall_popup",
        color=blue,
        indent=91,
    )
    with ui.group(
        parent="uninstall_popup", horizontal=True, horizontal_spacing=10, indent=42
    ):
        ui.add_button(
            label="Confirm", tag="confirm_button", callback=uninstaller, width=100
        )
        ui.add_button(
            label="Cancel",
            tag="cancel_button",
            callback=hide_uninstall_popup,
            width=100,
        )

    # Creating mod selection menu as popup/modal
    ui.add_window(
        modal=False,
        pos=(0, 0),
        tag="mod_menu",
        label="Mod Selection Menu",
        menubar=False,
        no_title_bar=False,
        no_move=True,
        no_collapse=True,
        no_close=True,
        no_open_over_existing_popup=True,
        height=400,
        width=538,
        show=False,
        no_resize=True,
    )
    ui.add_button(parent="mod_menu", label="SAVE", callback=close_mod_menu)


ui.set_frame_callback(1, callback=app_start)
ui.set_exit_callback(save_init)


# DearPyGyi Setup
ui.setup_dearpygui()
ui.show_viewport()
ui.start_dearpygui()
ui.destroy_context()
