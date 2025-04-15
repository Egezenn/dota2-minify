import os

import dearpygui.dearpygui as ui
import psutil

import helper
import mpaths


def open_file_dialog():
    ui.add_file_dialog(
        label="Select SteamLibrary",
        default_path=mpaths.steam_dir,
        default_filename="SteamLibrary",
        modal=False,
        tag="file_dialog_tag",
        callback=setFolder,
        cancel_callback=close_file_dialog,
        width=400,
        height=280,
        pos=(0, 0),
    )


def close_file_dialog():
    ui.delete_item("file_dialog_tag")


def setFolder(sender, app_data):
    folder = app_data["current_path"]
    print(folder)
    if folder:  # Check if the user selected a folder
        with open(mpaths.path_file, "w") as file:
            file.write(folder)
        helper.add_text_to_terminal(
            f"{helper.localization_dict["path_saved_terminal_text_var"]}",
            "path_saved_text_tag",
        )
    else:
        helper.add_text_to_terminal(
            f"{helper.localization_dict["path_canceled_terminal_text_var"]}",
            "canceled_path_text_tag",
        )


# this class is called with getattr method and calls all functions here alphabetically
# use naming convention (a_, b_, c_ ...etc) to run this class top to bottom if order mattters


class Requirements:
    def __init__(self, checkboxes):
        self.checkboxes = checkboxes
        self.toggle_flag = False

    def a_isSteamFound(self):
        if mpaths.steam_dir == "":
            mpaths.toggle_flag = True
            helper.add_text_to_terminal(
                text=f"{helper.localization_dict["no_steam_found_terminal_text_var"]}",
                tag="error_steam_not_found_text_tag",
            )

    def b_isDotaInstallFound(self):
        dota2path = os.path.join(
            mpaths.steam_dir,
            "steamapps\\common\\dota 2 beta\\game\\bin\\win64\\dota2.exe",
        )
        normalized_dota2path = os.path.normpath(dota2path)
        if not os.path.exists(normalized_dota2path):
            self.toggle_flag = True
            helper.add_text_to_terminal(
                f"{helper.localization_dict["no_dota_found_terminal_text_var"]}",
                "dota_not_found_text_1_tag",
            )
            helper.add_text_to_terminal(
                f'{helper.localization_dict["no_dota_found_path_terminal_text_var"]}\n\n"{normalized_dota2path}"\n\n',
                "dota_not_found_text_2_tag",
            )
            helper.add_text_to_terminal(
                f"""{helper.localization_dict["please_select_path_terminal_text_var"]}""",
                "dota_not_found_text_3_tag",
            )
            open_file_dialog()

    def c_isMinifyFolderPresent(self):
        if not os.path.exists(mpaths.dota_minify_content):
            os.makedirs(mpaths.dota_minify_content)
        if not os.path.exists(mpaths.dota_minify):
            os.makedirs(mpaths.dota_minify)

    def d_isDotaRunning(self):
        if "dota2.exe" in (p.name() for p in psutil.process_iter()):
            self.toggle_flag = True
            helper.add_text_to_terminal(
                text=f"{helper.localization_dict["error_please_close_dota_terminal_text_var"]}",
                tag="please_close_dota_text_tag",
            )

    def e_isSource2ViewerFound(self):
        if not os.path.exists(os.path.join(mpaths.minify_dir, "Source2Viewer-CLI.exe")):
            self.toggle_flag = True
            helper.add_text_to_terminal(
                text=f"{helper.localization_dict["error_no_cli_found_terminal_text_var"]}",
                tag="error_s2v_not_found_text_tag",
            )

    def f_isDllFound(self):
        if not os.path.exists(os.path.join(mpaths.minify_dir, "libSkiaSharp.dll")):
            self.toggle_flag = True
            helper.add_text_to_terminal(
                text=f"{helper.localization_dict["error_no_dll_found_terminal_text_var"]}",
                tag="error_libskiasharp.dll_not_found_text_tag",
            )

    def g_isCompillerFound(self):
        if not os.path.exists(mpaths.resource_compiler):
            helper.workshop_installed = False
            helper.add_text_to_terminal(
                text=f"""{helper.localization_dict["error_no_workshop_tools_found_terminal_text_var"]}""",
                tag="no_workshop_tools_found_text_tag",
            )
        else:
            helper.workshop_installed = True

    def h_verifyMods(self):
        for folder in mpaths.mods_folders:
            mod_path = os.path.join(mpaths.mods_dir, folder)

            if not os.path.exists(os.path.join(mod_path, "files")):
                self.toggle_flag = True
                helper.add_text_to_terminal(
                    text=f"""{helper.localization_dict["error_no_files_folder_found_terminal_text_var"]}'mods/{format(folder)}'.""",
                    tag="files_folder_not_found_text_tag",
                )

            if not os.path.exists(os.path.join(mod_path, "blacklist.txt")):
                self.toggle_flag = True
                helper.add_text_to_terminal(
                    text=f"""{helper.localization_dict["error_no_blacklist_txt_found_terminal_text_var"]}'mods/{format(folder)}'.""",
                    tag="blacklist_not_found_text_tag",
                )

            if not os.path.exists(os.path.join(mod_path, "styling.txt")):
                self.toggle_flag = True
                helper.add_text_to_terminal(
                    text=f"""{helper.localization_dict["error_no_styling_txt_found_terminal_text_var"]}'mods/{format(folder)}'.""",
                    tag="blacklist_not_found_text_tag",
                )
