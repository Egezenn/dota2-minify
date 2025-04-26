import os
import shutil

import psutil

import helper
import mpaths


class Requirements:
    def __init__(self, checkboxes):
        self.checkboxes = checkboxes
        self.toggle_flag = False

    def a_isSteamFound(self):
        if not mpaths.steam_dir:
            mpaths.toggle_flag = True
            helper.add_text_to_terminal(
                text=helper.localization_dict["no_steam_found_terminal_text_var"],
                tag="error_steam_not_found_text_tag",
            )

    def b_isDotaInstallFound(self):
        if mpaths.OS == "Windows":
            dota2path = os.path.normpath(
                os.path.join(
                    mpaths.steam_dir,
                    "steamapps",
                    "common",
                    "dota 2 beta",
                    "game",
                    "bin",
                    "win64",
                    "dota2.exe",
                )
            )
        elif mpaths.OS == "Linux":
            dota2path = os.path.normpath(
                os.path.join(
                    mpaths.steam_dir, "steamapps", "common", "dota 2 beta", "game", "bin", "linuxsteamrt64", "dota2"
                )
            )
        else:
            quit()

        if not os.path.exists(dota2path):
            self.toggle_flag = True
            helper.add_text_to_terminal(
                helper.localization_dict["no_dota_found_terminal_text_var"],
                "dota_not_found_text_1_tag",
            )
            helper.add_text_to_terminal(
                f'{helper.localization_dict["no_dota_found_path_terminal_text_var"]}\n\n"{dota2path}"\n\n',
                "dota_not_found_text_2_tag",
            )
            helper.add_text_to_terminal(
                f"{helper.localization_dict["please_select_path_terminal_text_var"]}",
                "dota_not_found_text_3_tag",
            )

    def c_isMinifyFolderPresent(self):
        os.makedirs(mpaths.minify_dota_content_path, exist_ok=True)
        os.makedirs(mpaths.minify_dota_pak_output_path, exist_ok=True)

    def d_isDotaRunning(self):
        if "dota2.exe" in (p.name() for p in psutil.process_iter()):
            self.toggle_flag = True
            helper.add_text_to_terminal(
                text=helper.localization_dict["error_please_close_dota_terminal_text_var"],
                tag="please_close_dota_text_tag",
            )

    def e_isSource2ViewerFound(self):
        if not (os.path.exists(os.path.join(mpaths.s2v_executable_path))):
            self.toggle_flag = True
            helper.add_text_to_terminal(
                text=helper.localization_dict["error_no_cli_found_terminal_text_var"],
                tag="error_s2v_not_found_text_tag",
            )

    def f_isDllFound(self):
        if not ((os.path.exists(mpaths.s2v_skia_path)) and (os.path.exists(mpaths.s2v_tinyexr_path))):
            self.toggle_flag = True
            helper.add_text_to_terminal(
                text=helper.localization_dict["error_no_dll_found_terminal_text_var"],
                tag="error_dlls_not_found_text_tag",
            )

    def g_isCompilerFound(self):
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
            shutil.copyfile(mpaths.dota_map_path, mpaths.minify_map_dir)
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
