import os
import tkinter as tk
from tkinter import filedialog, messagebox

import psutil

import helper
import mpaths


def setFolder(main_window):
    dialog_root = tk.Tk()
    dialog_root.withdraw()
    folder = filedialog.askdirectory()

    if folder:  # Check if the user selected a folder
        with open(mpaths.path_file, "w") as file:
            file.write(folder)
        messagebox.showinfo("Saved", "Path saved, go start Minify again.")
    else:
        messagebox.showinfo("Canceled", "You did not select a folder. Exiting.")

    dialog_root.destroy()
    main_window.destroy()


# this class is called with getattr method and calls all functions here alphabetically
# use naming convention (a_, b_, c_ ...etc) to run this class top to bottom if order mattters


class MyClass:
    def __init__(self, checkboxes, main_window):
        self.checkboxes = checkboxes
        self.toggle_flag = False
        self.main_window = main_window

    def a_isSteamFound(self):
        if mpaths.steam_dir == "":
            mpaths.toggle_flag = True
            print("Error: 'Steam is not installed on this system.")

    def b_isDotaInstallFound(self):
        dota2path = os.path.join(
            mpaths.steam_dir,
            "steamapps\\common\\dota 2 beta\\game\\bin\\win64\\dota2.exe",
        )
        normalized_dota2path = os.path.normpath(dota2path)

        if not os.path.exists(normalized_dota2path):
            self.toggle_flag = True

            message_root = tk.Tk()
            message_root.withdraw()
            messagebox.showinfo(
                "Dota 2 Not Found",
                f'Dota2 not found in\n\n"{normalized_dota2path}"\n\n'
                'Please select the location of your "SteamLibrary" folder, for example "D:\\SteamLibrary".',
            )
            message_root.destroy()
            setFolder(self.main_window)

    def c_isMinifyFolderPresent(self):
        if not os.path.exists(mpaths.dota_minify_content):
            os.makedirs(mpaths.dota_minify_content)
        if not os.path.exists(mpaths.dota_minify):
            os.makedirs(mpaths.dota_minify)

    def d_isDotaRunning(self):
        if "dota2.exe" in (p.name() for p in psutil.process_iter()):
            self.toggle_flag = True
            print("Error: Please close Dota 2 and restart Minify.")

    def e_isSource2ViewerFound(self):
        if not os.path.exists(os.path.join(mpaths.minify_dir, "Source2Viewer-CLI.exe")):
            self.toggle_flag = True
            print(
                "Error: 'Source2Viewer-CLI.exe' not found, click Help for instructions."
            )

    def f_isDllFound(self):
        if not os.path.exists(os.path.join(mpaths.minify_dir, "libSkiaSharp.dll")):
            self.toggle_flag = True
            print("Error: 'libSkiaSharp.dll' not found, click Help for instructions.")

    def g_isCompillerFound(self):
        if not os.path.exists(mpaths.resource_compiler):
            helper.workshop_installed == False
            print(
                "Some mods have been grayed out because you don't have \n Workshop Tools installed. Click Help for instructions."
            )
        else:
            helper.workshop_installed = True

    def h_verifyMods(self):
        for folder in mpaths.mods_folders:
            mod_path = os.path.join(mpaths.mods_dir, folder)

            if not os.path.exists(os.path.join(mod_path, "files")):
                self.toggle_flag = True
                print("Missing 'files' folder in 'mods/{}'".format(folder))
            if not os.path.exists(os.path.join(mod_path, "blacklist.txt")):
                self.toggle_flag = True
                print("Missing 'blacklist.txt' folder in 'mods/{}'".format(folder))
            if not os.path.exists(os.path.join(mod_path, "styling.txt")):
                self.toggle_flag = True
                print("Missing 'styling.txt' folder in 'mods/{}'".format(folder))
