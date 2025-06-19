import os

import psutil

import helper
import mpaths


# TODO most of these are met and handled correctly, remove
class Requirements:
    def __init__(self, checkboxes):
        self.checkboxes = checkboxes
        self.toggle_flag = False

    def a_isSteamFound(self):
        if not mpaths.steam_dir:
            self.toggle_flag = True
            helper.add_text_to_terminal(
                helper.localization_dict["no_steam_found_terminal_text_var"],
                "error_steam_not_found_text_tag",
                "error",
            )

    def b_isDotaInstallFound(self):
        dota2path = os.path.normpath(os.path.join(mpaths.steam_dir, mpaths.DOTA_EXECUTABLE_PATH))

        if not os.path.exists(dota2path):
            self.toggle_flag = True
            helper.add_text_to_terminal(
                helper.localization_dict["no_dota_found_terminal_text_var"], "dota_not_found_text_1_tag", "error"
            )
            helper.add_text_to_terminal(
                f'{helper.localization_dict["no_dota_found_path_terminal_text_var"]}\n\n"{dota2path}"\n\n',
                "dota_not_found_text_2_tag",
                "warning",
            )
            helper.add_text_to_terminal(
                f"{helper.localization_dict["please_select_path_terminal_text_var"]}",
                "dota_not_found_text_3_tag",
                "warning",
            )

    def c_isMinifyFolderPresent(self):
        os.makedirs(mpaths.minify_dota_content_path, exist_ok=True)

    def d_isDotaRunning(self):
        if "dota2.exe" in (p.name() for p in psutil.process_iter()):
            self.toggle_flag = True
            helper.add_text_to_terminal(
                helper.localization_dict["error_please_close_dota_terminal_text_var"],
                "please_close_dota_text_tag",
                "error",
            )

    def e_isSource2ViewerFound(self):
        if not (os.path.exists(mpaths.s2v_executable)):
            self.toggle_flag = True
            helper.add_text_to_terminal(
                helper.localization_dict["error_no_cli_found_terminal_text_var"],
                "error_s2v_not_found_text_tag",
                "error",
            )

    def f_isDllFound(self):
        if not (os.path.exists(mpaths.s2v_skia_path)) and (os.path.exists(mpaths.s2v_tinyexr_path)):
            self.toggle_flag = True
            helper.add_text_to_terminal(
                helper.localization_dict["error_no_dll_found_terminal_text_var"],
                "error_dlls_not_found_text_tag",
                "error",
            )

    def g_isCompilerFound(self):
        if not os.path.exists(mpaths.dota_resource_compiler_path):
            helper.workshop_installed = False
            helper.add_text_to_terminal(
                helper.localization_dict["error_no_workshop_tools_found_terminal_text_var"],
                "no_workshop_tools_found_text_tag",
                "warning",
            )
        else:
            helper.workshop_installed = True

    def h_verifyMods(self):
        for folder in mpaths.mods_folders:
            mod_path = os.path.join(mpaths.mods_dir, folder)

            if not os.path.exists(os.path.join(mod_path, "files")):
                self.toggle_flag = True
                helper.add_text_to_terminal(
                    f"{helper.localization_dict["error_no_files_folder_found_terminal_text_var"]}'mods/{folder}'.",
                    "files_folder_not_found_text_tag",
                    "error",
                )

            if not os.path.exists(os.path.join(mod_path, "blacklist.txt")):
                self.toggle_flag = True
                helper.add_text_to_terminal(
                    f"{helper.localization_dict["error_no_blacklist_txt_found_terminal_text_var"]}'mods/{folder}'.",
                    "blacklist_not_found_text_tag",
                    "error",
                )

            if not os.path.exists(os.path.join(mod_path, "styling.txt")):
                self.toggle_flag = True
                helper.add_text_to_terminal(
                    f"{helper.localization_dict["error_no_styling_txt_found_terminal_text_var"]}'mods/{folder}'.",
                    "blacklist_not_found_text_tag",
                    "error",
                )
