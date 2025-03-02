import os

import dearpygui.dearpygui as ui
import psutil

import helper_n as helper
import mpaths

# def setFolder(main_window):
#     dialog_root = tk.Tk()
#     dialog_root.withdraw()
#     folder = filedialog.askdirectory()

#     if folder:  # Check if the user selected a folder
#         with open(mpaths.path_file, "w") as file:
#             file.write(folder)
#         messagebox.showinfo("Saved", "Path saved, go start Minify again.")
#     else:
#         messagebox.showinfo("Canceled", "You did not select a folder. Exiting.")

#     dialog_root.destroy()
#     main_window.destroy()


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
            ui.add_text(
                default_value="Dota 2 Not Found",
                tag="dota_not_found_text",
                parent="terminal_window",
            )
            ui.add_text(
                default_value=f'Dota2 not found in\n\n"{normalized_dota2path}"\n\n',
                tag="dota_not_found_text_2",
                parent="terminal_window",
            )
            ui.add_text(
                default_value=f"""Please select the location of your "SteamLibrary" folder, for example "D:\\SteamLibrary".""",
                tag="dota_not_found_text_3",
                parent="terminal_window",
            )

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
            helper.workshop_installed == False
            ui.add_text(
                default_value="""Some mods have been grayed out because you don't have \n Workshop Tools installed. Click Help for instructions.""",
                tag="wst_not_found_text",
                parent="terminal_window",
            )
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
