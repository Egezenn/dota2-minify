import os
import time

import dearpygui.dearpygui as ui
import psutil

import helper
import mpaths

import crossfiledialog


checkboxes = {}


def open_file_dialog():
    ui.configure_item("button_patch", enabled=False)
    steam_dir = crossfiledialog.choose_folder("Select SteamLibrary Folder", "")
    mpaths.recalculate_paths(steam_dir)
    x = Requirements(checkboxes)
    public_methods = [method for method in dir(x) if callable(getattr(x, method)) if not method.startswith("_")]
    for method in public_methods:
        getattr(x, method)()
        # helper.unlock_interaction()
    # setFolder
    # close_file_dialog


class Requirements:
    def __init__(self, checkboxes):
        self.checkboxes = checkboxes
        self.toggle_flag = False
        print(f"{self.toggle_flag}")

    def a_isSteamFound(self):
        if mpaths.steam_dir == "":
            self.toggle_flag = True
            helper.add_text_to_terminal(
                text=helper.localization_dict["no_steam_found_terminal_text_var"],
                tag=f"{ui.generate_uuid()}",
            )
        else:
            self.toggle_flag = False
        print(f"{self.toggle_flag}")

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
                f"{ui.generate_uuid()}",
            )
            helper.add_text_to_terminal(
                f'{helper.localization_dict["no_dota_found_path_terminal_text_var"]}\n\n"{normalized_dota2path}"\n\n',
                f"{ui.generate_uuid()}",
            )
            helper.add_text_to_terminal(
                f"{helper.localization_dict["please_select_path_terminal_text_var"]}",
                f"{ui.generate_uuid()}",
            )
            open_file_dialog()
        else:
            self.toggle_flag = False
        print(f"{self.toggle_flag}")

    def c_isMinifyFolderPresent(self):
        os.makedirs(mpaths.minify_dota_content_path, exist_ok=True)
        os.makedirs(mpaths.minify_dota_pak_output_path, exist_ok=True)
        print(f"{self.toggle_flag}")

    def d_isDotaRunning(self):
        if "dota2.exe" in (p.name() for p in psutil.process_iter()):
            self.toggle_flag = True
            helper.add_text_to_terminal(
                text=helper.localization_dict["error_please_close_dota_terminal_text_var"],
                tag=f"{ui.generate_uuid()}",
            )
        else:
            self.toggle_flag = False
        print(f"{self.toggle_flag}")

    def e_isSource2ViewerFound(self):
        if not os.path.exists(os.path.join(mpaths.minify_dir, "Source2Viewer-CLI.exe")):
            self.toggle_flag = True
            helper.add_text_to_terminal(
                text=helper.localization_dict["error_no_cli_found_terminal_text_var"],
                tag=f"{ui.generate_uuid()}",
            )
        else:
            self.toggle_flag = False
        print(f"{self.toggle_flag}")

    def f_isDllFound(self):
        if not os.path.exists(os.path.join(mpaths.minify_dir, "libSkiaSharp.dll")):
            self.toggle_flag = True
            helper.add_text_to_terminal(
                text=helper.localization_dict["error_no_dll_found_terminal_text_var"],
                tag=f"{ui.generate_uuid()}",
            )
        else:
            self.toggle_flag = False
        print(f"{self.toggle_flag}")

    def g_isCompillerFound(self):
        if not os.path.exists(mpaths.dota_resource_compiler_path):
            helper.workshop_installed = False
            helper.add_text_to_terminal(
                text=helper.localization_dict["error_no_workshop_tools_found_terminal_text_var"],
                tag=f"{ui.generate_uuid()}",
            )
            self.toggle_flag = False
        else:
            helper.workshop_installed = True
        print(f"{self.toggle_flag}")

    def h_verifyMods(self):
        for folder in mpaths.mods_folders:
            mod_path = os.path.join(mpaths.mods_dir, folder)

            if not os.path.exists(os.path.join(mod_path, "files")):
                self.toggle_flag = True
                helper.add_text_to_terminal(
                    text=f"{helper.localization_dict["error_no_files_folder_found_terminal_text_var"]}'mods/{format(folder)}'.",
                    tag=f"{ui.generate_uuid()}",
                )

            if not os.path.exists(os.path.join(mod_path, "blacklist.txt")):
                self.toggle_flag = True
                helper.add_text_to_terminal(
                    text=f"{helper.localization_dict["error_no_blacklist_txt_found_terminal_text_var"]}'mods/{format(folder)}'.",
                    tag=f"{ui.generate_uuid()}",
                )

            if not os.path.exists(os.path.join(mod_path, "styling.txt")):
                self.toggle_flag = True
                helper.add_text_to_terminal(
                    text=f"{helper.localization_dict["error_no_styling_txt_found_terminal_text_var"]}'mods/{format(folder)}'.",
                    tag=f"{ui.generate_uuid()}",
                )
        print(f"{self.toggle_flag}")

    def validate_map_file(self):
        helper.add_text_to_terminal(helper.localization_dict["checking_map_file_var"], f"{ui.generate_uuid()}")

        os.makedirs(mpaths.maps_dir, exist_ok=True)

        if os.path.exists(mpaths.minify_map_dir) == False:
            helper.shutil.copyfile(mpaths.dota_map_path, mpaths.minify_map_dir)
            helper.add_text_to_terminal(
                helper.localization_dict["updating_map_file_terminal_text_var"],
                f"{ui.generate_uuid()}",
            )
            helper.add_text_to_terminal(
                helper.localization_dict["map_file_uptodate_terminal_text_var"],
                f"{ui.generate_uuid()}",
            )
        elif os.path.exists(mpaths.minify_map_dir) and (
            helper.calculate_md5(mpaths.dota_map_path) != helper.calculate_md5(mpaths.minify_map_dir)
        ):
            helper.add_text_to_terminal(
                helper.localization_dict["updating_map_file_terminal_text_var"],
                f"{ui.generate_uuid()}",
            )
            os.remove(mpaths.minify_map_dir)
            helper.shutil.copyfile(mpaths.dota_map_path, mpaths.minify_map_dir)
            helper.add_text_to_terminal(
                helper.localization_dict["map_file_uptodate_terminal_text_var"],
                f"{ui.generate_uuid()}",
            )

        else:
            helper.add_text_to_terminal(
                helper.localization_dict["map_file_uptodate_terminal_text_var"],
                f"{ui.generate_uuid()}",
            )
        print(f"{self.toggle_flag}")
        print("Finished")
