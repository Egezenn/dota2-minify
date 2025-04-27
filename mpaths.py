import os
import platform
import tkinter as tk
import traceback
from tkinter import messagebox, filedialog
import psutil

steam_dir = ""
path_file = os.path.join(os.getcwd(), "dota2path_minify.txt")
OS = platform.system()


def get_steam_path():
    global steam_dir
    if OS == "Windows":
        import winreg

        try:
            hkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
        except Exception as exception:
            hkey = None
            with open(os.path.join(os.getcwd(), "logs", "registry.txt"), "w") as file:
                file.write(traceback.format_exc())

        try:
            steam_path = winreg.QueryValueEx(hkey, "InstallPath")
        except:
            steam_path = ""
            with open(os.path.join(os.getcwd(), "logs", "registry_query.txt"), "w") as file:
                file.write(traceback.format_exc())

        try:
            steam_dir = steam_path[0]
        except:
            steam_dir = ""

    else:
        steam_dir = ""


def check_for_steam_library():
    global steam_dir
    drives = []
    found = []
    steamapps = "steamapps"
    if OS == "Windows" and not os.path.exists(
        os.path.join(
            steam_dir, "steamapps", "common", "dota 2 beta", "game", "bin", "win64", "dota2.exe"
        )  # Checking if dota was found alredy
    ):
        for partition in psutil.disk_partitions(all=False):  # Getting all the drives
            if "rw" in partition.opts.split(","):
                drives.append(partition.mountpoint)
        for drive in drives:
            try:
                with os.scandir(
                    drive
                ) as folders:  # Getting all the folders in first layer and checking them if library was installed in root of the drive
                    for folder in folders:
                        if folder.is_dir():
                            if folder == steamapps:
                                found.append(folder.path)
                                print(f"Found - {folder.path}")
                            try:
                                with os.scandir(folder) as subfolders:  # Checking for "steamapps" folder in subfolders
                                    for candidate in subfolders:
                                        if candidate.is_dir():
                                            print(f"Searching... {candidate.path}")
                                            dir_name = candidate.name
                                            if dir_name == steamapps:
                                                found.append(folder.path)
                                                print(f"Found - {folder.path}")
                            except PermissionError:
                                print(f"Permission denied accessing {folder}")
                            except Exception as error:
                                print(f"Error scanning {folder}: {error}")
            except PermissionError:
                print(f"Permission denied accessing {drive}")
            except Exception as error:
                print(f"Error scanning {drive}: {error}")
        print("We found:")
        for adress in found:  # checking all found results if dota is present(in case steamcmd present etc.)
            print(adress)
            if os.path.exists(
                os.path.join(adress, "steamapps", "common", "dota 2 beta", "game", "bin", "win64", "dota2.exe")
            ):
                steam_dir = adress
                print(f"Dota found in: {steam_dir}")
                break
    else:
        steam_dir = ""


def handle_non_default_path():
    global steam_dir
    # when dota2 is not inside Steam folder OR host is not on windows, set new steam directory from 'dota2path_minify.txt
    if not steam_dir:
        if not os.path.exists(path_file):
            with open(path_file, "a+") as file:
                file.write("")

        with open(path_file, "r") as file:
            for line in file:
                steam_dir = os.path.normpath(line.strip())

    while not steam_dir or not (
        os.path.exists(
            os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "bin", "win64", "dota2.exe")
        )
        or os.path.exists(
            os.path.join(
                steam_dir,
                "steamapps",
                "common",
                "dota 2 beta",
                "game",
                "bin",
                "linuxsteamrt64",
                "dota2",
            )
        )
    ):
        root = tk.Tk()
        root.withdraw()

        root.wm_attributes("-topmost", 1)  # Make sure root is topmost
        choice = messagebox.askokcancel(
            "Install Path Handler",
            "We couldn't find your Dota2 install path, please select:\n\n"
            "Your SteamLibrary folder if you have Dota2 installed elsewhere\n\n"
            "Steam folder if your OS is not Windows and have Dota2 installed at the default path.",
            parent=root,
        )
        root.lift()
        root.focus_force()

        if choice:
            steam_dir = os.path.normpath(filedialog.askdirectory())
            with open(path_file, "w") as file:
                file.write(steam_dir)
        else:
            quit()

        root.destroy()


get_steam_path()
# check_for_steam_library()
handle_non_default_path()

# links
version_query = "https://raw.githubusercontent.com/Egezenn/dota2-minify/refs/heads/main/version"
discord = "https://discord.com/invite/2YDnqpbcKM"
latest_release = "https://github.com/Egezenn/dota2-minify/releases/latest"
s2v_latest_windows_x64 = (
    "https://github.com/ValveResourceFormat/ValveResourceFormat/releases/latest/download/cli-windows-x64.zip"
)
s2v_latest_linux_x64 = (
    "https://github.com/ValveResourceFormat/ValveResourceFormat/releases/latest/download/cli-linux-x64.zip"
)
s2v_latest_linux_arm = (
    "https://github.com/ValveResourceFormat/ValveResourceFormat/releases/latest/download/cli-linux-arm.zip"
)
s2v_latest_linux_arm_x64 = (
    "https://github.com/ValveResourceFormat/ValveResourceFormat/releases/latest/download/cli-linux-arm64.zip"
)
odg_latest = "https://github.com/Egezenn/OpenDotaGuides/releases/latest/download/itembuilds.zip"

# minify project paths
minify_dir = os.getcwd()
bin_dir = os.path.join(minify_dir, "bin")
build_dir = os.path.join(minify_dir, "build")
logs_dir = os.path.join(minify_dir, "logs")
mods_dir = os.path.join(minify_dir, "mods")

# bin
blank_files_dir = os.path.join(bin_dir, "blank-files")
maps_dir = os.path.join(bin_dir, "maps")
img_dir = os.path.join(bin_dir, "images")
minify_map_dir = os.path.join(maps_dir, "dota.vpk")
localization_file_dir = os.path.join(bin_dir, "localization.json")
locale_file_dir = "locale"
s2v_executable = "Source2Viewer-CLI.exe" if OS == "Windows" else "Source2Viewer-CLI"
s2v_executable_path = os.path.join(minify_dir, s2v_executable)
s2v_skia_path = (
    os.path.join(minify_dir, "libSkiaSharp.dll") if OS == "Windows" else os.path.join(minify_dir, "libSkiaSharp.so")
)
s2v_tinyexr_path = (
    os.path.join(minify_dir, "TinyEXR.Native.dll")
    if OS == "Windows"
    else os.path.join(minify_dir, "libTinyEXR.Native.so")
)

# dota2 paths
## minify
### resourcecompiler required dir
minify_dota_compile_input_path = os.path.join(
    steam_dir, "steamapps", "common", "dota 2 beta", "content", "dota_addons", "minify"
)
### compiled files from resourcefiles
minify_dota_compile_output_path = os.path.join(
    steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_addons", "minify"
)
### vpk destination
minify_dota_pak_output_path = os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_minify")
minify_dota_maps_output_path = os.path.join(minify_dota_pak_output_path, "maps")
# required for tools to launch
minify_dota_content_path = os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "content", "dota_minify")

## base game
dota2_executable = os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "bin", "win64", "dota2.exe")
dota2_tools_executable = os.path.join(
    steam_dir, "steamapps", "common", "dota 2 beta", "game", "bin", "win64", "dota2cfg.exe"
)
dota_core_pak01_path = os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "core", "pak01_dir.vpk")
dota_pak01_path = os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota", "pak01_dir.vpk")
dota_itembuilds_path = os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota", "itembuilds")
dota_map_path = os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota", "maps", "dota.vpk")
dota_resource_compiler_path = os.path.join(
    steam_dir, "steamapps", "common", "dota 2 beta", "game", "bin", "win64", "resourcecompiler.exe"
)

mods_folders = []
for mod in os.listdir(mods_dir):
    mods_folders.append(mod)
