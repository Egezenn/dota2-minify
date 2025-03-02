import json
import os
import platform
import random
import shutil
import subprocess
import sys
import textwrap
import threading
import time
import traceback
from functools import partial
from shutil import copytree, ignore_patterns

import dearpygui.dearpygui as ui
import psutil
import requests
import vpk

import helper_n as helper
import mpaths
import validatefiles_n as validatefiles

# Setting up context for GUI
ui.create_context()

# Variables

version = "1.09"

localizations = []
patching = False
checkboxes = {}
checkboxes_state = {}
blacklist_dictionary = {}
styling_dictionary = {}
response = {}

blue = (0, 230, 230)
banner_pad_y = 16

# Debug_text
text = r"""-> Installing Auto Accept Match"""


def save_init():
    ui.save_init_file("dpg.ini")

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


def change_localization():
    with open(mpaths.localization_file_dir, "r", encoding="utf-8") as localization_file:
        localization_data = json.load(localization_file)
    locale = ui.get_value("lang_select")
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
    open_github_link()
    close()


def add_text_to_terminal():
    global text
    ui.add_text(text, parent="terminal_window", wrap=400, color=blue)
    scroll_to_terminal_end()

def scroll_to_terminal_end():
    time.sleep(0.02)    
    ui.set_y_scroll("terminal_window", ui.get_y_scroll_max("terminal_window"))

def save_state_checkboxes():
    for box in checkboxes:
        global checkboxes_state
        checkboxes_state[box] = (ui.get_value(box))
        with open('state_persistence.json', 'w', encoding='utf-8') as f:
            json.dump(checkboxes_state, f, ensure_ascii=False, indent=4)

def load_state_checkboxes():
    global checkboxes_state
    with open('state_persistence.json', 'r', encoding='utf-8') as f:
        x = f.read()
        checkboxes_state = json.loads(x)

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
    save_state_checkboxes()
    ui.configure_item("mod_menu", show=False)


def open_discord_link():
    helper.urlDispatcher("https://discord.com/invite/2YDnqpbcKM")


def open_github_link():
    helper.urlDispatcher("https://github.com/Egezenn/dota2-minify/releases/latest")


def close():
    ui.stop_dearpygui()


def unistall_popup_show():
    ui.configure_item("uninstall_popup", show=True)
    

def create_checkboxes():
    global checkboxes_state
    for index in range(len(mpaths.mods_folders)):
        name = mpaths.mods_folders[index]
        ui.add_group(parent="mod_menu", tag=f"{name}_group_tag", horizontal=True, width=300)
        ui.add_checkbox(
            parent=f"{name}_group_tag",
            label=name,
            tag=f"{name}_checkbox_tag",
            default_value=False,
            callback=setupButtonState
        )
        x = checkboxes_state.keys()
        for key in x:
            if key == f"{name}_checkbox_tag":
                ui.configure_item(f"{name}_checkbox_tag", default_value=checkboxes_state[f"{name}_checkbox_tag"])
            
        mod_path = os.path.join(mpaths.mods_dir, name)
        notes_txt = os.path.join(mod_path, "notes.txt")
        ui.add_button(
            parent=f"{name}_group_tag",
            small=True,
            indent=200,
            tag=f"{name}_details_tag",
            label="Details",
            #callback=OPEN NOTES TODO) 
        )
        current_box = f"{name}_checkbox_tag"
        checkboxes[current_box] = (name)


def update_popup_show():
    ui.add_window(label=f"Update {response.text} is now available!",
                    modal=True, 
                    no_move=True, 
                    tag="update_popup", 
                    show=True,
                    no_collapse=True,
                    no_close=True,
                    no_saved_settings=True,
                    no_resize=True,
                    width=310,
                    height=100
                    )
    ui.configure_item("update_popup", 
                      pos=(ui.get_viewport_width()/2-ui.get_item_width("update_popup")/2, ui.get_viewport_height()/2-ui.get_item_height("update_popup")/2)
                      )
    ui.add_text(default_value="Would you like to go to the download page?",
                parent="update_popup",
                color=blue)
    with ui.group(parent="update_popup", 
                  tag="update_popup_button_group",
                  horizontal=True,
                  horizontal_spacing=10,
                  indent=42
                  ):
        ui.add_button(label="Yes", 
                        width=100,
                        height=20, 
                        callback=open_github_link_and_close_minify,
                        tag="update_popup_yes_button",
                        )
        ui.add_button(label="No", 
                        width=100,
                        height=20, 
                        callback=delete_update_popup,
                        tag="update_popup_no_button"
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
                    ui.add_text(default_value="Downloading Source2Viewer-CLI...", parent="terminal_window")
                    scroll_to_terminal_end()
                    zip_name = "cli-windows-x64.zip"
                    zip_path = os.path.join(mpaths.minify_dir, zip_name)
                    # need to update regularly, can't do latest and call it a day
                    response = requests.get(
                        "https://github.com/ValveResourceFormat/ValveResourceFormat/releases/latest/download/cli-windows-x64.zip"
                    )
                    if response.status_code == 200:
                        with open(zip_path, "wb") as file:
                            file.write(response.content)
                        ui.add_text(default_value=f"-> Downloaded {zip_name}", parent="terminal_window", tag="downloaded_text")
                        scroll_to_terminal_end()
                        shutil.unpack_archive(zip_path, mpaths.minify_dir, "zip")
                        os.remove(zip_path)
                        ui.add_text(default_value=f"-> Extracted {zip_name}.", parent="terminal_window", tag="extracted_text")
                        scroll_to_terminal_end()
                else:
                    ui.add_text(
                        default_value="Error: Instructions to download Source2Viewer binaries for your system is not available yet, click Help for instructions.",
                        parent="terminal_window", 
                        tag="error_cli_download_text")      
                    scroll_to_terminal_end()
            for method in public_methods:
                getattr(x, method)()
                if x.toggle_flag == True:
                    lock_interaction()
                    break
        except Exception:
            with open(os.path.join(mpaths.logs_dir, "crashlog.txt"), "w") as file:
                file.write(traceback.format_exc())
                lock_interaction()
                ui.add_text(default_value="Failed to start!", parent="terminal_window", tag="failed_to_start_text")
                scroll_to_terminal_end()
                ui.add_text(default_value="Check 'logs\\crashlog.txt' for more info.", parent="terminal_window", tag="check_logs_text")
                scroll_to_terminal_end()

def setupButtonState():
        for box in checkboxes:
            if ui.get_value(box) == True:
                ui.configure_item("button_patch", enabled=True)
                #self.patchBtn.config(state="normal", cursor="hand2")
                break
            else:
                ui.configure_item("button_patch", enabled=False) #Disabled theme? TODO
                #self.patchBtn.config(state="disabled", cursor="")
        if helper.workshop_installed == False:
            helper.disableWorkshopMods(mpaths.mods_dir, mpaths.mods_folders, checkboxes)

def uninstaller():
    hide_uninstall_popup()
    clean_terminal()
    time.sleep(0.01)
    #lock_interaction()
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
                #print(os.path.join(mpaths.itembuilds_dir, "bkup"))
                for name in os.listdir(
                    os.path.join(mpaths.itembuilds_dir, "bkup")
                ):
                    os.rename(
                        os.path.join(mpaths.itembuilds_dir, "bkup", name),
                        os.path.join(mpaths.itembuilds_dir, name),
                    )
    except FileNotFoundError:
        helper.warnings.append(
            "Unable to recover backed up default guides or the itembuilds directory is empty, verify files to get the default guides back"
        )   
    ui.add_text(
                "All Minify mods have been removed.",
                tag="uninstaller_text",
                color=blue,
                parent="terminal_window"
            )
    scroll_to_terminal_end()
    #unlock_interaction()
    
def clean_terminal():
    ui.delete_item("terminal_window", children_only=True)

def patcher():
    global patching
    clean_terminal()
    #lock_interaction()
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
        helper.warnings = []

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
                        ui.add_text(
                            default_value=f"-> Installing {folder}",
                            tag=f"installing_{folder}_text",
                            parent="terminal_window",
                            wrap=400,
                            color=blue)  ###???  #print("→ Installing " + folder)
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
                            response = requests.get(
                                "https://github.com/Egezenn/OpenDotaGuides/releases/latest/download/itembuilds.zip"
                            )
                            if response.status_code == 200:
                                with open(zip_path, "wb") as file:
                                    file.write(response.content)
                                ui.add_text(
                                    default_value="-> Downloaded latest OpenDotaGuides guides.",
                                    tag="downloaded_open_dota_guides_text",
                                    parent="terminal_window",
                                    wrap=400,
                                    color=blue
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
                                ui.add_text(
                                    default_value="-> Replaced default guides with OpenDotaGuides guides.",
                                    tag="replaced_open_dota_guides_text",
                                    parent="terminal_window",
                                    wrap=400,
                                    color=blue
                                )
                                if os.path.exists(zip_path):
                                    os.remove(zip_path)
                            else:
                                ui.add_text(
                                    default_value="-> Failed to download latest OpenDotaGuides guides.",
                                    tag="failed_downloading_open_dota_guides",
                                    parent="terminal_window",
                                    wrap=400,
                                    color=blue
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
                                            helper.warnings.append(
                                                f"[Invalid Extension] '{line}' in 'mods\\{folder}\\blacklist.txt' [line: {index+1}] does not end in one of the valid extensions -> {blank_file_extensions}"  ###???
                                            )

                            # print(f"    blacklist.txt: Found {len(blacklist_data)} paths")

                            for index, line in enumerate(blacklist_data):
                                line = line.strip()
                                path, extension = os.path.splitext(line)

                                # blacklist_dictionary["blacklist-key{}".format(index+1)] = path, extension

                                if not os.path.exists(
                                    os.path.join(
                                        mpaths.game_dir, os.path.dirname(path)
                                    )
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
                                        os.path.join(
                                            mpaths.game_dir, path + extension
                                        ),
                                    )
                                except FileNotFoundError as exception:
                                    helper.warnings.append(
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
                                    helper.warnings.append(
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
                                        helper.warnings.append(
                                            "Path does not exist in VPK -> '{}', error in 'mods\\{}\\styling.txt'".format(
                                                construct1.path.vcss_c, folder
                                            )  ###???
                                        )
                                        del styling_dictionary[key]

            except Exception as exception:
                exceptiondata = traceback.format_exc().splitlines()
                helper.warnings.append(exceptiondata[-1])
        # ---------------------------------- STEP 2 ---------------------------------- #
        # ------------------- Decompile all files in "build" folder ------------------ #
        # ---------------------------------------------------------------------------- #
        ui.add_text(
            default_value="-> Decompiling",
            tag="decompiling_text",
            parent="terminal_window",
            wrap=400,
            color=blue
        )
        with open(os.path.join(mpaths.logs_dir, "Source2Viewer-CLI.txt"), "w"
        ) as file:
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
        ui.add_text(
            default_value="-> Patching",
            tag="patching_text",
            parent="terminal_window",
            wrap=400,
            color=blue)
        
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
                ui.add_text(
                    default_value="-> Compiling",
                    tag="compiling_text",
                    parent="terminal_window",
                    wrap=400,
                    color=blue
                )
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

        #unlock_interaction()

        ui.add_text(
            default_value="-> Done!",
            tag="done_text",
            parent="terminal_window",
            wrap=400,
            color=blue,
        )

        ui.add_text(
            default_value="-------------------------------------------------------",
            parent="terminal_window",
            wrap=400,
            color=blue,
        )

        ui.add_text(
            default_value="Remember to add '-language minify' to dota2 launch options",
            tag="launch_option_text",
            parent="terminal_window",
            wrap=400,
            color=blue,
        )

        ui.add_text(
            default_value="Click Help button below for instructions",
            tag="help_text",
            parent="terminal_window",
            wrap=400,
            color=blue,
        )

        helper.handleWarnings(mpaths.logs_dir)

    except Exception:
        with open(os.path.join(mpaths.logs_dir, "crashlog.txt"), "w") as file:
            file.write(traceback.format_exc())

        patching = False

        ui.add_text(
            default_value="Patching failed.",
            tag="patching_failed_text",
            parent="terminal_window",
            wrap=400,
            color=blue,
        )

        ui.add_text(
            default_value="""Check 'logs\\crashlog.txt' for more info.""",
            tag="check_logs_text",
            parent="terminal_window",
            wrap=400,
            color=blue,
        )

        ui.add_text(
            default_value="-------------------------------------------------------",
            parent="terminal_window",
            wrap=400,
            color=blue,
        )


def version_check():
    global response
    if version is not None:
        response = requests.get(
            "https://raw.githubusercontent.com/Egezenn/dota2-minify/refs/heads/stable/version"
        )
        if response.status_code == 200:
            if version == response.text:
                ui.configure_item("button_latest", enabled=False)
            else:
                ui.configure_item("button_latest", enabled=True)
                update_popup_show()

def app_start():
    ui.configure_app(init_file="dpg.ini")
    get_available_localizations()
    create_ui()
    setupSystem()
    load_state_checkboxes()
    version_check()
    create_checkboxes()
    setupButtonState()
    item_handler_registry()

# Adding font to the ui registry
with ui.font_registry():
    with ui.font(f"{mpaths.bin_dir}/FiraMono-Medium.ttf", 14) as main_font:
        ui.add_font_range_hint(ui.mvFontRangeHint_Default)
        ui.add_font_range_hint(ui.mvFontRangeHint_Cyrillic)
        ui.bind_font(main_font)


# Adding mouse handler to ui registry
with ui.handler_registry():
    ui.add_mouse_drag_handler(
        parent="top_bar", button=0, threshold=0.0, callback=drag_viewport
    )

def item_handler_registry():
    with ui.item_handler_registry(tag="resize_handler") as handler:
        ui.add_item_resize_handler(callback=scroll_to_terminal_end)
    ui.bind_item_handler_registry("terminal_window", "resize_handler")


# Creating_main_viewport
ui.create_viewport(
    title="Minify",
    height=400,
    width=538,
    resizable=False,
    decorated=False,
    vsync=True,
    clear_color=(0, 0, 0, 255)
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
                    callback=open_discord_link
                    )
                ui.add_button(
                    tag="button_latest", 
                    label="Latest", 
                    width=100, 
                    callback=open_github_link
                    )
                ui.add_button(
                    tag="uninstall_button", 
                    label="Uninstall", 
                    width=100, 
                    callback=unistall_popup_show
                    )
                ui.add_button(
                    tag="exit_button", 
                    label="Exit", 
                    width=100, 
                    callback=close
                    )
            with ui.group(pos=(67, -2)):
                ui.add_text(r"""
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
                    color=blue,
                    pos=(124, 15 + banner_pad_y * 5),
                )
                ui.add_text(
                    "-> Join our Discord community!",
                    tag="header_text_2",
                    color=blue,
                    pos=(123, 15 + banner_pad_y * 6),
                )
                ui.add_text(
                    "-> Share Minify with your friends and online groups",
                    tag="header_text_3",
                    color=blue,
                    pos=(123, 15 + banner_pad_y * 7),
                )
                ui.add_text(
                    "-> Star the project on GitHub",
                    tag="header_text_4",
                    color=blue,
                    pos=(123, 15 + banner_pad_y * 8),
                )
                ui.add_text(
                    "-> Create and maintain mods for this project",
                    tag="header_text_5",
                    color=blue,
                    pos=(123, 15 + banner_pad_y * 9),
                )
                ui.add_text(
                    "----------------------------------------------------------",
                    color=blue,
                    pos=(123, 15 + banner_pad_y * 10),
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
                no_resize=True
            )

    ui.add_window(label="Uninstall",
                  modal=True, 
                  no_move=True, 
                  tag="uninstall_popup", 
                  show=False,
                  no_collapse=True,
                  no_close=True,
                  no_saved_settings=True
                )
    ui.add_text(default_value="Remove all mods?",
                parent="uninstall_popup",
                color=blue)
    with ui.group(parent="uninstall_popup", horizontal=True):
        ui.add_button(label="Confirm", tag="confirm_button", callback=uninstaller)
        ui.add_button(label="Cancel", tag="cancel_button", callback=hide_uninstall_popup)

    # Creating mod selection menu as popup/modal
    ui.add_window(
        modal=True,
        tag="mod_menu",
        menubar=False,
        no_title_bar=True,
        no_move=True,
        no_collapse=True,
        no_close=True,
        no_open_over_existing_popup=True,
        height=394,
        width=532,
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
