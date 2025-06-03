"All the necessary file paths & links"

import getpass
import os
import platform
import tkinter as tk
import traceback
from tkinter import filedialog, messagebox

import vdf

steam_dir = ""
OS = platform.system()
machine = platform.machine().lower()
architecture = platform.architecture()[0]
STEAM_DEFAULT_INSTALLATION_PATH = (
    os.path.join("C:\\", "Program Files (x86)", "Steam")
    if OS == "Windows"
    else os.path.join("/", "home", getpass.getuser(), ".local", "share", "Steam")
)
DOTA_EXECUTABLE_PATH = (
    os.path.join("steamapps", "common", "dota 2 beta", "game", "bin", "win64", "dota2.exe")
    if OS == "Windows"
    else os.path.join("steamapps", "common", "dota 2 beta", "game", "bin", "linuxsteamrt64", "dota2")
)

# minify project paths
bin_dir = "bin"
build_dir = "build"
logs_dir = "logs"
mods_dir = "mods"
config_dir = "config"


def create_dirs(*paths):
    for path in paths:
        os.makedirs(path, exist_ok=True)


create_dirs(logs_dir, config_dir)

# bin
blank_files_dir = os.path.join(bin_dir, "blank-files")
img_dir = os.path.join(bin_dir, "images")
localization_file_dir = os.path.join(bin_dir, "localization.json")
maps_dir = os.path.join(bin_dir, "maps")
minify_map_dir = os.path.join(maps_dir, "dota.vpk")
locale_file_dir = os.path.join(config_dir, "locale")
mods_file_dir = os.path.join(config_dir, "mods.json")
path_file_dir = os.path.join(config_dir, "dota2path_minify.txt")
version_file_dir = "version"


def find_library_from_vdf():
    global steam_dir
    path_from_txt = ""

    try:
        with open(path_file_dir, "r") as file:
            for line in file:
                path_from_txt = os.path.normpath(line.strip())
    except Exception as error:
        with open(os.path.join(logs_dir, "crashlog.txt"), "w") as file:
            file.write(f"Error reading {path_file_dir}: {error}")

    try:
        if steam_dir:  # regkey found
            with open(os.path.join(steam_dir, "config", "libraryfolders.vdf"), "r", encoding="utf-8") as dump:
                data = vdf.load(dump)
        else:  # try with defaults
            with open(
                os.path.join(STEAM_DEFAULT_INSTALLATION_PATH, "config", "libraryfolders.vdf"), "r", encoding="utf-8"
            ) as dump:
                data = vdf.load(dump)

        paths = get_steam_library_paths(data)
        for path in paths:
            if os.path.exists(os.path.join(path, DOTA_EXECUTABLE_PATH)):
                steam_dir = path
                if not os.path.exists(path_file_dir) or path_from_txt == "":
                    with open(path_file_dir, "w") as file:
                        file.write(steam_dir)

    except Exception as error:
        with open(os.path.join(logs_dir, "crashlog.txt"), "w") as file:
            file.write(f"Error reading libraryfolders.vdf: {error}")
            steam_dir = ""


def get_steam_library_paths(vdf_data):
    paths = []
    for folder_key in vdf_data.get("libraryfolders", {}):
        folder = vdf_data["libraryfolders"][folder_key]
        # could check if "apps" key has 570 in it and return only one path, would require tests though
        if "path" in folder:
            paths.append(folder["path"])
    return paths


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
    if not os.path.exists(os.path.join(steam_dir, DOTA_EXECUTABLE_PATH)):
        if not os.path.exists(path_file_dir):
            with open(path_file_dir, "a+") as file:
                file.write("")

        find_library_from_vdf()

        with open(path_file_dir, "r") as file:
            for line in file:
                steam_dir = os.path.normpath(line.strip())

    # last line of defense
    while not steam_dir or not os.path.exists(os.path.join(steam_dir, DOTA_EXECUTABLE_PATH)):
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
            with open(path_file_dir, "w") as file:
                file.write(steam_dir)
        else:
            quit()

        root.destroy()


def overwrite_ensurance_hack(list_of_words, list):
    to_move = [s for s in list if any(s.startswith(word) for word in list_of_words)]
    others = [s for s in list if not any(s.startswith(word) for word in list_of_words)]
    return others + to_move


get_steam_path()
handle_non_default_path()


# links
version_query = "https://raw.githubusercontent.com/Egezenn/dota2-minify/refs/heads/main/version"
discord = "https://discord.com/invite/2YDnqpbcKM"
latest_release = "https://github.com/Egezenn/dota2-minify/releases"
odg_latest = "https://github.com/Egezenn/OpenDotaGuides/releases/latest/download/itembuilds.zip"

# source2viewer install
if OS == "Windows":
    s2v_executable = "Source2Viewer-CLI.exe"
    s2v_skia_path = "libSkiaSharp.dll"
    s2v_tinyexr_path = "TinyEXR.Native.dll"
    s2v_latest = (
        "https://github.com/ValveResourceFormat/ValveResourceFormat/releases/latest/download/cli-windows-x64.zip"
    )
elif OS == "Linux":
    s2v_executable = "Source2Viewer-CLI"
    s2v_skia_path = "libSkiaSharp.so"
    s2v_tinyexr_path = "libTinyEXR.Native.so"
    if machine in ["aarch64", "arm64"]:
        s2v_latest = (
            "https://github.com/ValveResourceFormat/ValveResourceFormat/releases/latest/download/cli-linux-arm64.zip"
        )
    elif machine in ["armv7l", "arm"]:
        s2v_latest = (
            "https://github.com/ValveResourceFormat/ValveResourceFormat/releases/latest/download/cli-linux-arm.zip"
        )
    elif architecture == "64bit":
        s2v_latest = (
            "https://github.com/ValveResourceFormat/ValveResourceFormat/releases/latest/download/cli-linux-x64.zip"
        )
else:
    raise Exception("Unsupported Source2Viewer platform!")

# ripgrep install
if OS == "Windows":
    rg_executable = "rg.exe"
    if architecture == "64bit":
        rg_latest = (
            "https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-x86_64-pc-windows-msvc.zip"
        )
    else:
        rg_latest = (
            "https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-i686-pc-windows-msvc.zip"
        )
elif OS == "Linux":
    rg_executable = "rg"
    if machine in ["aarch64", "arm64"]:
        rg_latest = "https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-aarch64-unknown-linux-gnu.tar.gz"
    elif machine in ["armv7l", "arm"]:
        rg_latest = "https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-armv7-unknown-linux-gnueabihf.tar.gz"
    elif machine == "ppc64":  # unlikely
        rg_latest = "https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-powerpc64-unknown-linux-gnu.tar.gz"
    elif machine == "s390x":  # unlikely
        rg_latest = "https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-s390x-unknown-linux-gnu.tar.gz"
    elif architecture == "64bit":
        rg_latest = "https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-x86_64-unknown-linux-musl.tar.gz"
    elif architecture == "32bit":
        rg_latest = "https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-i686-unknown-linux-gnu.tar.gz"
else:
    raise Exception("Unsupported ripgrep platform!")


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

# Rubberband fix to always do blacklists at last for them to make overwrites
mods_folder_compilation_order = overwrite_ensurance_hack(
    ["Mute", "Remove", "Minify Base Attacks", "Minify Spells & Items", "Misc Optimization"], mods_folders
)
mods_folder_compilation_order = overwrite_ensurance_hack(["Hide ALL", "Remove ALL", "Mute ALL"], mods_folders)
