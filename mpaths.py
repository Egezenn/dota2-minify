import os
import platform
import tkinter as tk
import traceback
from tkinter import messagebox, filedialog
import vdf

steam_dir = ""
path_file = os.path.join(os.getcwd(), "dota2path_minify.txt")
OS = platform.system()


def find_library_from_file():
    global steam_dir
    path_from_txt = ""

    try:
        with open(path_file, "r") as file:
            for line in file:
                path_from_txt = os.path.normpath(line.strip())
    except Exception as error:
        with open(os.path.join(logs_dir, "crashlog.txt"), "w") as file:
            file.write(f"Error reading {path_file}: {error}")

    try:
        with open(os.path.join(steam_dir, "config", "libraryfolders.vdf"), "r", encoding="utf-8") as dump:
            data = vdf.load(dump)
            paths = get_steam_library_paths(data)
    except Exception as error:
        with open(os.path.join(logs_dir, "crashlog.txt"), "w") as file:
            file.write(f"Error reading libraryfolders.vdf: {error}")

    for path in paths:
        if os.path.exists(
            os.path.join(path, "steamapps", "common", "dota 2 beta", "game", "bin", "win64", "dota2.exe")
        ):
            steam_dir = path
            if not os.path.exists(path_file) or path_from_txt == "":
                with open(path_file, "w") as file:
                    file.write(steam_dir)


def get_steam_library_paths(vdf_data):
    libraries = []
    for folder_key in vdf_data.get("libraryfolders", {}):
        folder = vdf_data["libraryfolders"][folder_key]
        if "path" in folder:
            libraries.append(folder["path"])
    return libraries


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


def handle_non_default_path():
    global steam_dir
    # when dota2 is not inside Steam folder OR host is not on windows, set new steam directory from 'dota2path_minify.txt
    if not os.path.exists(
        os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "bin", "win64", "dota2.exe")
    ) or not os.path.exists(
        os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "bin", "linuxsteamrt64", "dota2")
    ):
        if not os.path.exists(path_file):
            with open(path_file, "a+") as file:
                file.write("")

        with open(path_file, "r") as file:
            for line in file:
                steam_dir = os.path.normpath(line.strip())

    if OS == "Windows" and not os.path.exists(
        os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "bin", "win64", "dota2.exe")
    ):
        find_library_from_file()

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
