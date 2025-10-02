"All the necessary file paths & links"

import getpass
import sys
import os
import platform
import traceback
import shutil

import vdf

steam_dir = ""
OS = platform.system()
MACHINE = platform.machine().lower()
ARCHITECTURE = platform.architecture()[0]

# Detect Wine executable on Unix-like systems (prefers wine64 when available)
def _detect_wine_cmd():
    if OS == "Darwin":
        whisky_wine = os.path.expanduser(
            "~/Library/Application Support/com.isaacmarovitz.Whisky/Libraries/Wine/bin/wine64"
        )
        if os.path.exists(whisky_wine) and os.access(whisky_wine, os.X_OK):
            return whisky_wine

    if OS in ("Linux", "Darwin"):
        try:
            for candidate in ("wine64", "wine"):
                if shutil.which(candidate):
                    return candidate
        except Exception:
            pass
    return None

WINE_CMD = _detect_wine_cmd()

# assuming steam runtimes on linux / darwin
if OS == "Linux":
    DOTA_EXECUTABLE_PATH = os.path.join("steamapps", "common", "dota 2 beta", "game", "bin", "linuxsteamrt64", "dota2")
    STEAM_DEFAULT_INSTALLATION_PATH = os.path.join("/", "home", getpass.getuser(), ".local", "share", "Steam")
elif OS == "Darwin":
    DOTA_EXECUTABLE_PATH = os.path.join(
        "steamapps",
        "common",
        "dota 2 beta",
        "game",
        "bin",
        "osx64",
        "dota2.app",
        "Contents",
        "MacOS",
        "dota2",
    )
    STEAM_DEFAULT_INSTALLATION_PATH = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "Steam")
else:
    DOTA_EXECUTABLE_PATH = os.path.join("steamapps", "common", "dota 2 beta", "game", "bin", "win64", "dota2.exe")
    STEAM_DEFAULT_INSTALLATION_PATH = os.path.join("C:\\", "Program Files (x86)", "Steam")

DOTA_TOOLS_EXECUTABLE_PATH = os.path.join("steamapps", "common", "dota 2 beta", "game", "bin", "win64", "dota2cfg.exe")

# launchers for dota2 won't work as it presumes native version, doesn't really matter
if OS == "Windows":
    DOTA_EXECUTABLE_PATH_FALLBACK = os.path.join(
        "steamapps", "common", "dota 2 beta", "game", "bin", "win64", "dota2.exe"
    )
elif OS == "Darwin":
    DOTA_EXECUTABLE_PATH_FALLBACK = DOTA_EXECUTABLE_PATH
else:
    DOTA_EXECUTABLE_PATH_FALLBACK = os.path.join(
        "steamapps", "common", "dota 2 beta", "game", "bin", "linuxsteamrt64", "dota2"
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

# If running from a macOS .app bundle built by PyInstaller, data files live under Contents/Resources
try:
    if OS == "Darwin" and getattr(sys, "frozen", False):
        app_dir = os.path.dirname(sys.executable)
        resources_dir = os.path.normpath(os.path.join(app_dir, os.pardir, "Resources"))
        if os.path.exists(os.path.join(resources_dir, "bin", "localization.json")):
            bin_dir = os.path.join(resources_dir, "bin")
            mods_dir = os.path.join(resources_dir, "mods")
except Exception:
    pass

# bin
blank_files_dir = os.path.join(bin_dir, "blank-files")
img_dir = os.path.join(bin_dir, "images")
sounds_dir = os.path.join(bin_dir, "sounds")
locale_file_dir = os.path.join(config_dir, "locale")
localization_file_dir = os.path.join(bin_dir, "localization.json")
mods_file_dir = os.path.join(config_dir, "mods.json")
path_file_dir = os.path.join(config_dir, "dota2path_minify.txt")

# Store heavy extracted tools outside the app/repo directory to avoid huge bundles
def _get_user_data_root():
    try:
        if OS == "Windows":
            base = os.getenv("LOCALAPPDATA") or os.path.expanduser("~\\AppData\\Local")
            return os.path.join(base, "Minify")
        elif OS == "Darwin":
            return os.path.join(os.path.expanduser("~"), "Library", "Application Support", "Minify")
        else:
            return os.path.join(os.path.expanduser("~/.local/share"), "minify")
    except Exception:
        return os.path.abspath("logs")  # fallback

user_data_root = _get_user_data_root()
os.makedirs(user_data_root, exist_ok=True)

rescomp_override_dir = os.path.join(user_data_root, "rescomproot")
version_file_dir = "version"

rescomp_override = True if os.path.exists(rescomp_override_dir) else False


def find_library_from_vdf():
    global steam_dir

    try:
        with open(path_file_dir, "r") as file:
            steam_dir = os.path.normpath(file.readline().strip())
    except Exception as error:
        with open(os.path.join(logs_dir, "warnings.txt"), "w") as file:
            file.write(f"Error reading {path_file_dir}: {error}")

    try:
        if steam_dir and steam_dir != ".":  # regkey found
            with open(
                os.path.join(steam_dir, "config", "libraryfolders.vdf"),
                "r",
                encoding="utf-8",
            ) as dump:
                data = vdf.load(dump)
        else:  # try with defaults
            with open(
                os.path.join(STEAM_DEFAULT_INSTALLATION_PATH, "config", "libraryfolders.vdf"),
                "r",
                encoding="utf-8",
            ) as dump:
                data = vdf.load(dump)

        paths = get_steam_library_paths(data)
        for path in paths:
            if os.path.exists(os.path.join(path, DOTA_EXECUTABLE_PATH)) or os.path.exists(
                os.path.join(path, DOTA_EXECUTABLE_PATH_FALLBACK)
            ):
                steam_dir = path
                with open(path_file_dir, "w") as file:
                    file.write(steam_dir)

    except Exception as error:
        with open(os.path.join(logs_dir, "warnings.txt"), "w") as file:
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
    # when dota2 is not inside Steam folder, set new steam directory from 'dota2path_minify.txt
    if not os.path.exists(os.path.join(steam_dir, DOTA_EXECUTABLE_PATH)):
        if not os.path.exists(path_file_dir):
            with open(path_file_dir, "w") as file:
                file.write("")

        find_library_from_vdf()

        with open(path_file_dir, "r") as file:
            steam_dir = os.path.normpath(file.readline().strip())

    # last line of defense
    while not steam_dir or (
        not os.path.exists(os.path.join(steam_dir, DOTA_EXECUTABLE_PATH))
        and not os.path.exists(os.path.join(steam_dir, DOTA_EXECUTABLE_PATH_FALLBACK))
    ):
        # Try to prompt with tkinter if available; otherwise, write guidance and break
        try:
            import tkinter as tk  # type: ignore
            from tkinter import filedialog, messagebox  # type: ignore

            root = tk.Tk()
            root.withdraw()

            root.wm_attributes("-topmost", 1)
            choice = messagebox.askokcancel(
                "Minify Install Path Handler",
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
        except Exception:
            # No tkinter available or failed to prompt. Create a hint and break to avoid import-time crash.
            with open(os.path.join(logs_dir, "crashlog.txt"), "w") as file:
                file.write(
                    "Could not open directory picker. Set your Steam library path in 'config/dota2path_minify.txt' and restart Minify.\n"
                    f"Expected something like: {STEAM_DEFAULT_INSTALLATION_PATH}\n"
                )
            break


def overwrite_ensurance_hack(list_of_string_patterns, strings):
    matched, unmatched = [[], []]
    for string in strings:
        for pattern in list_of_string_patterns:
            if string.startswith(pattern):
                matched.append(string)
                break
        if string not in [*unmatched, *matched]:
            unmatched.append(string)

    return [*unmatched, *matched]


get_steam_path()
handle_non_default_path()


# links
version_query = "https://raw.githubusercontent.com/Egezenn/dota2-minify/refs/heads/main/version"
discord = "https://discord.com/invite/2YDnqpbcKM"
latest_release = "https://github.com/Egezenn/dota2-minify/releases"
odg_latest = "https://github.com/Egezenn/OpenDotaGuides/releases/latest/download/itembuilds.zip"

# source2viewer install
try:
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
        if MACHINE in ["aarch64", "arm64"]:
            s2v_latest = "https://github.com/ValveResourceFormat/ValveResourceFormat/releases/latest/download/cli-linux-arm64.zip"
        elif MACHINE in ["armv7l", "arm"]:
            s2v_latest = (
                "https://github.com/ValveResourceFormat/ValveResourceFormat/releases/latest/download/cli-linux-arm.zip"
            )
        elif ARCHITECTURE == "64bit":
            s2v_latest = (
                "https://github.com/ValveResourceFormat/ValveResourceFormat/releases/latest/download/cli-linux-x64.zip"
            )
    elif OS == "Darwin":
        s2v_executable = "Source2Viewer-CLI"
        s2v_skia_path = "libSkiaSharp.dylib"
        s2v_tinyexr_path = "libTinyEXR.Native.dylib"
        if MACHINE in ["aarch64", "arm64"]:
            s2v_latest = "https://github.com/ValveResourceFormat/ValveResourceFormat/releases/latest/download/cli-macos-arm64.zip"
        else:
            s2v_latest = (
                "https://github.com/ValveResourceFormat/ValveResourceFormat/releases/latest/download/cli-macos-x64.zip"
            )
    else:
        raise Exception("Unsupported Source2Viewer platform!")

    # ripgrep install
    if OS == "Windows":
        rg_executable = "rg.exe"
        if ARCHITECTURE == "64bit":
            rg_latest = "https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-x86_64-pc-windows-msvc.zip"
        else:
            rg_latest = (
                "https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-i686-pc-windows-msvc.zip"
            )
    elif OS == "Linux":
        rg_executable = "rg"
        if MACHINE in ["aarch64", "arm64"]:
            rg_latest = "https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-aarch64-unknown-linux-gnu.tar.gz"
        elif MACHINE in ["armv7l", "arm"]:
            rg_latest = "https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-armv7-unknown-linux-gnueabihf.tar.gz"
        elif MACHINE == "ppc64":  # unlikely
            rg_latest = "https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-powerpc64-unknown-linux-gnu.tar.gz"
        elif MACHINE == "s390x":  # unlikely
            rg_latest = "https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-s390x-unknown-linux-gnu.tar.gz"
        elif ARCHITECTURE == "64bit":
            rg_latest = "https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-x86_64-unknown-linux-musl.tar.gz"
        elif ARCHITECTURE == "32bit":
            rg_latest = "https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-i686-unknown-linux-gnu.tar.gz"
    elif OS == "Darwin":
        rg_executable = "rg"
        if MACHINE in ["aarch64", "arm64"]:
            rg_latest = "https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-aarch64-apple-darwin.tar.gz"
        else:
            rg_latest = "https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-x86_64-apple-darwin.tar.gz"
    else:
        raise Exception("Unsupported ripgrep platform!")

except Exception as error:
    with open(os.path.join(logs_dir, "crashlog.txt"), "w") as file:
        file.write(f"Unsupported configuration ({OS}/{MACHINE}/{ARCHITECTURE})\n{error}")


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
### required dir for tools
minify_dota_tools_required_path = os.path.join(
    steam_dir, "steamapps", "common", "dota 2 beta", "content", "dota_minify"
)
### vpk destination
minify_dota_pak_possible_output_path = os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game")
minify_dota_pak_output_path = os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_minify")
minify_dota_possible_language_output_paths = [
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_minify"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_brazilian"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_bulgarian"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_czech"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_danish"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_dutch"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_finnish"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_french"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_german"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_greek"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_hungarian"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_italian"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_japanese"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_koreana"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_latam"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_norwegian"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_polish"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_portuguese"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_romanian"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_russian"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_schinese"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_spanish"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_swedish"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_tchinese"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_thai"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_turkish"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_ukrainian"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota_vietnamese"),
]
# required for tools to launch
minify_dota_content_path = os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "content", "dota_minify")
minify_output_list = [
    "minify",
    "brazilian",
    "bulgarian",
    "czech",
    "danish",
    "dutch",
    "finnish",
    "french",
    "german",
    "greek",
    "hungarian",
    "italian",
    "japanese",
    "koreana",
    "latam",
    "norwegian",
    "polish",
    "portuguese",
    "romanian",
    "russian",
    "schinese",
    "spanish",
    "swedish",
    "tchinese",
    "thai",
    "turkish",
    "ukrainian",
    "vietnamese",
]

## base game
if OS == "Windows":
    dota2_executable = os.path.join(steam_dir, DOTA_EXECUTABLE_PATH)
    dota2_tools_executable = os.path.join(steam_dir, DOTA_TOOLS_EXECUTABLE_PATH)
elif OS == "Linux":
    dota2_executable = os.path.join(steam_dir, DOTA_EXECUTABLE_PATH)
    # tools launcher path kept as Windows for extraction override flow
    dota2_tools_executable = os.path.join(steam_dir, DOTA_TOOLS_EXECUTABLE_PATH)
elif OS == "Darwin":
    dota2_executable = os.path.join(steam_dir, DOTA_EXECUTABLE_PATH)
    # tools not available on macOS; keep Windows placeholder
    dota2_tools_executable = os.path.join(steam_dir, DOTA_TOOLS_EXECUTABLE_PATH)
dota_game_pak_path = os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota", "pak01_dir.vpk")
dota_core_pak_path = os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "core", "pak01_dir.vpk")
dota_itembuilds_path = os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota", "itembuilds")
dota_map_path = os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota", "maps", "dota.vpk")
dota_resource_compiler_path = os.path.join(
    steam_dir,
    "steamapps",
    "common",
    "dota 2 beta",
    "game",
    "bin",
    "win64",
    "resourcecompiler.exe",
)

dota_tools_paths = [
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "bin"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "core"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota", "bin"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota", "tools"),
    os.path.join(steam_dir, "steamapps", "common", "dota 2 beta", "game", "dota", "gameinfo.gi"),
]
dota_tools_extraction_paths = [
    os.path.join(rescomp_override_dir, "game", "bin"),
    os.path.join(rescomp_override_dir, "game", "core"),
    os.path.join(rescomp_override_dir, "game", "dota", "bin"),
    os.path.join(rescomp_override_dir, "game", "dota", "tools"),
    os.path.join(rescomp_override_dir, "game", "dota", "gameinfo.gi"),
]


try:
    if not os.path.isdir(mods_dir):
        raise FileNotFoundError(mods_dir)
    filtered_entries = []
    for entry in os.listdir(mods_dir):
        if entry.startswith('.'):
            continue
        if entry in {"__MACOSX"}:
            continue
        full_path = os.path.join(mods_dir, entry)
        if not os.path.isdir(full_path):
            continue
        filtered_entries.append(entry)
    mods_folders = sorted(filtered_entries)
except Exception:
    # Fallback to a minimal list to avoid crashing at import time
    mods_folders = ["base"]

if "base" in mods_folders:
    try:
        i = mods_folders.index("base")
        mods_folders.pop(i)
        mods_folders.insert(0, "base")
    except ValueError:
        pass

# Rubberband fix to always do blacklists at last for them to make overwrites
mods_folder_application_order = overwrite_ensurance_hack(
    [
        "Mute",
        "Remove",
        "Minify Base Attacks",
        "Minify Spells & Items",
        "Misc Optimization",
        "User Styles",
        "_",
    ],
    mods_folders,
)
