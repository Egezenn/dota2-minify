import os

import dearpygui.dearpygui as ui
import psutil
import time

import helper
import mpaths


def open_file_dialog():
    ui.configure_item("button_patch", enabled=False)
    ui.add_file_dialog(
        label="Select SteamLibrary",
        default_filename="SteamLibrary",
        default_path="",
        modal=True,
        tag="file_dialog_tag",
        callback=setFolder,
        cancel_callback=close_file_dialog,
        min_size=(480, 260),
        directory_selector=True,
    )


def close_file_dialog():
    ui.configure_item("button_patch", enabled=False)
    helper.add_text_to_terminal(
        helper.localization_dict["path_canceled_terminal_text_var"],
        "canceled_path_text_tag",
    )
    ui.delete_item("file_dialog_tag")
    time.sleep(3)
    helper.close()


def setFolder(sender, app_data):
    ui.configure_item("button_patch", enabled=False)
    folder = app_data["current_path"]
    print(folder)

    if folder:  # Check if the user selected a folder
        with open(mpaths.path_file, "w") as file:
            file.write(folder)
        helper.add_text_to_terminal(
            helper.localization_dict["path_saved_terminal_text_var"],
            "path_saved_text_tag",
        )
    time.sleep(3)
    helper.close()


class Requirements:
    def __init__(self, checkboxes):
        self.checkboxes = checkboxes
        self.toggle_flag = False

    def a_isSteamFound(self):
        if mpaths.steam_dir == "":
            mpaths.toggle_flag = True
            helper.add_text_to_terminal(
                text=helper.localization_dict["no_steam_found_terminal_text_var"],
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
                helper.localization_dict["no_dota_found_terminal_text_var"],
                "dota_not_found_text_1_tag",
            )
            helper.add_text_to_terminal(
                f'{helper.localization_dict["no_dota_found_path_terminal_text_var"]}\n\n"{normalized_dota2path}"\n\n',
                "dota_not_found_text_2_tag",
            )
            helper.add_text_to_terminal(
                f"{helper.localization_dict["please_select_path_terminal_text_var"]}",
                "dota_not_found_text_3_tag",
            )
            open_file_dialog()

    def c_isMinifyFolderPresent(self):
        if not os.path.exists(mpaths.minify_dota_pak_output_path):
            os.makedirs(mpaths.minify_dota_pak_output_path)

    def d_isDotaRunning(self):
        if "dota2.exe" in (p.name() for p in psutil.process_iter()):
            self.toggle_flag = True
            helper.add_text_to_terminal(
                text=helper.localization_dict["error_please_close_dota_terminal_text_var"],
                tag="please_close_dota_text_tag",
            )

    def e_isSource2ViewerFound(self):
        if not os.path.exists(os.path.join(mpaths.minify_dir, "Source2Viewer-CLI.exe")):
            self.toggle_flag = True
            helper.add_text_to_terminal(
                text=helper.localization_dict["error_no_cli_found_terminal_text_var"],
                tag="error_s2v_not_found_text_tag",
            )

    def f_isDllFound(self):
        if not os.path.exists(os.path.join(mpaths.minify_dir, "libSkiaSharp.dll")):
            self.toggle_flag = True
            helper.add_text_to_terminal(
                text=helper.localization_dict["error_no_dll_found_terminal_text_var"],
                tag="error_libskiasharp.dll_not_found_text_tag",
            )

    def g_isCompillerFound(self):
        if not os.path.exists(mpaths.dota_resource_compiler_path):
            helper.workshop_installed = False
            helper.add_text_to_terminal(
                text=helper.localization_dict["error_no_workshop_tools_found_terminal_text_var"],
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
                    text=f"{helper.localization_dict["error_no_files_folder_found_terminal_text_var"]}'mods/{format(folder)}'.",
                    tag="files_folder_not_found_text_tag",
                )

            if not os.path.exists(os.path.join(mod_path, "blacklist.txt")):
                self.toggle_flag = True
                helper.add_text_to_terminal(
                    text=f"{helper.localization_dict["error_no_blacklist_txt_found_terminal_text_var"]}'mods/{format(folder)}'.",
                    tag="blacklist_not_found_text_tag",
                )

            if not os.path.exists(os.path.join(mod_path, "styling.txt")):
                self.toggle_flag = True
                helper.add_text_to_terminal(
                    text=f"{helper.localization_dict["error_no_styling_txt_found_terminal_text_var"]}'mods/{format(folder)}'.",
                    tag="blacklist_not_found_text_tag",
                )

    def validate_map_file(self):
        helper.add_text_to_terminal(helper.localization_dict["checking_map_file_var"], "map_check_text_tag")

        os.makedirs(mpaths.maps_dir, exist_ok=True)

        if os.path.exists(mpaths.minify_map_dir) == False:
            helper.shutil.copyfile(mpaths.dota_map_path, mpaths.minify_map_dir)
            helper.add_text_to_terminal(
                helper.localization_dict["updating_map_file_terminal_text_var"],
                "map_update_text_tag",
            )
            helper.add_text_to_terminal(
                helper.localization_dict["map_file_uptodate_terminal_text_var"],
                "map_up_to_date_text_tag",
            )

        elif os.path.exists(mpaths.minify_map_dir) and (
            helper.calculate_md5(mpaths.dota_map_path) != helper.calculate_md5(mpaths.minify_map_dir)
        ):
            helper.add_text_to_terminal(
                helper.localization_dict["updating_map_file_terminal_text_var"],
                "map_update_text_tag",
            )
            os.remove(mpaths.minify_map_dir)
            helper.shutil.copyfile(mpaths.dota_map_path, mpaths.minify_map_dir)
            helper.add_text_to_terminal(
                helper.localization_dict["map_file_uptodate_terminal_text_var"],
                "map_up_to_date_text_tag",
            )

        else:
            helper.add_text_to_terminal(
                helper.localization_dict["map_file_uptodate_terminal_text_var"],
                "map_up_to_date_text_tag",
            )
