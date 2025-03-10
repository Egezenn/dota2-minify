import os

import dearpygui.dearpygui as ui
import psutil

import helper
import mpaths



def open_file_dialog():
    ui.add_file_dialog(label='Select dota2.exe', default_path=mpaths.steam_dir, default_filename="dota2.exe", modal=False, tag="file_dialog_tag", callback=setFolder, cancel_callback=close_file_dialog, width=500, height=300)
    ui.add_file_extension(parent="file_dialog_tag", extension=".exe")

def close_file_dialog():
    ui.delete_item("file_dialog_tag")

def setFolder(sender, app_data):
    folder = app_data["current_path"]
    print(folder)
    if folder:   #Check if the user selected a folder
        with open(mpaths.path_file, "w") as file:
            file.write(folder)
        helper.add_text_to_terminal("Path saved, please restart Minify", "path_saved_text_tag")
    else:
        helper.add_text_to_terminal("Canceled, you did not select a folder.", "canceled_path_text_tag")


# this class is called with getattr method and calls all functions here alphabetically
# use naming convention (a_, b_, c_ ...etc) to run this class top to bottom if order mattters

class Requirements:
    def __init__(self, checkboxes):
        self.checkboxes = checkboxes
        self.toggle_flag = False

    def a_isSteamFound(self):
        if mpaths.steam_dir == "":
            mpaths.toggle_flag = True
            ui.add_text(
                default_value="Error: 'Steam is not installed on this system.",
                tag="error_steam_not_found_text",
                parent="terminal_window",
            )

    def b_isDotaInstallFound(self):
        dota2path = os.path.join(
            mpaths.steam_dir,
            "steamapps\\common\\dota 2 beta\\game\\bin\\win64\\dota2.exe",
        )
        normalized_dota2path = os.path.normpath(dota2path)

        if not os.path.exists(normalized_dota2path):
            self.toggle_flag = True
            helper.add_text_to_terminal("Dota 2 Not Found", "dota_not_found_text")
            helper.add_text_to_terminal(f'Dota 2 not found in\n\n"{normalized_dota2path}"\n\n', "dota_not_found_text_2")
            helper.add_text_to_terminal(f"""Please select the location of your "SteamLibrary" folder, for example "D:\\SteamLibrary".""", "dota_not_found_text_3")
            open_file_dialog()

    def c_isMinifyFolderPresent(self):
        if not os.path.exists(mpaths.dota_minify_content):
            os.makedirs(mpaths.dota_minify_content)
        if not os.path.exists(mpaths.dota_minify):
            os.makedirs(mpaths.dota_minify)

    def d_isDotaRunning(self):
        if "dota2.exe" in (p.name() for p in psutil.process_iter()):
            self.toggle_flag = True
            ui.add_text(
                default_value="Error: Please close Dota 2 and restart Minify.",
                tag="please_close_dota_text",
                parent="terminal_window",
            )

    def e_isSource2ViewerFound(self):
        if not os.path.exists(os.path.join(mpaths.minify_dir, "Source2Viewer-CLI.exe")):
            self.toggle_flag = True
            ui.add_text(
                default_value="Error: 'Source2Viewer-CLI.exe' not found, click Help for instructions.",
                tag="error_s2v_not_found_text",
                parent="terminal_window",
            )

    def f_isDllFound(self):
        if not os.path.exists(os.path.join(mpaths.minify_dir, "libSkiaSharp.dll")):
            self.toggle_flag = True
            ui.add_text(
                default_value="Error: 'libSkiaSharp.dll' not found, click Help for instructions.",
                tag="error_libskiasharp.dll_not_found_text",
                parent="terminal_window",
            )

    def g_isCompillerFound(self):
        if not os.path.exists(mpaths.resource_compiler):
            helper.workshop_installed = False
            helper.add_text_to_terminal("""Some mods have been grayed out because you don't have Workshop Tools installed. Click Help for instructions.""", "wst_not_found_text")
        else:
            helper.workshop_installed = True

    def h_verifyMods(self):
        for folder in mpaths.mods_folders:
            mod_path = os.path.join(mpaths.mods_dir, folder)

            if not os.path.exists(os.path.join(mod_path, "files")):
                self.toggle_flag = True
                ui.add_text(
                    default_value=f"""Missing 'files' folder in 'mods/{format(folder)}'.""",
                    tag="files_folder_not_found_text",
                    parent="terminal_window",
                )

            if not os.path.exists(os.path.join(mod_path, "blacklist.txt")):
                self.toggle_flag = True
                ui.add_text(
                    default_value=f"""Missing 'blacklist.txt' folder in 'mods/{format(folder)}'.""",
                    tag="blacklist_not_found_text",
                    parent="terminal_window",
                )

            if not os.path.exists(os.path.join(mod_path, "styling.txt")):
                self.toggle_flag = True
                ui.add_text(
                    default_value=f"""Missing 'styling.txt' folder in 'mods/{format(folder)}'.""",
                    tag="blacklist_not_found_text",
                    parent="terminal_window",
                )
