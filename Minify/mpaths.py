"All the necessary file paths & links"

import getpass
import os
import platform
import sys
import traceback

import jsonc
import vdf

OS = platform.system()
MACHINE = platform.machine().lower()
ARCHITECTURE = platform.architecture()[0]

WIN = "Windows"
LINUX = "Linux"
MAC = "Darwin"

frozen = getattr(sys, "frozen", False)

head_owner = "Egezenn"
repo_name = "dota2-minify"

# assuming steam runtimes on linux / darwin
if OS == LINUX:
    DOTA_EXECUTABLE_PATH = os.path.join("steamapps", "common", "dota 2 beta", "game", "bin", "linuxsteamrt64", "dota2")
    STEAM_DEFAULT_INSTALLATION_PATH = os.path.join("/", "home", getpass.getuser(), ".local", "share", "Steam")
elif OS == MAC:
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
DOTA_EXECUTABLE_PATH_FALLBACK = os.path.join("steamapps", "common", "dota 2 beta", "game", "bin", "win64", "dota2.exe")

# minify project paths
bin_dir = "bin"
build_dir = "vpk_build"
replace_dir = "vpk_replace"
merge_dir = "vpk_merge"
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
rescomp_override_dir = os.path.join(bin_dir, "rescomproot")
sounds_dir = os.path.join(bin_dir, "sounds")

# logs
log_crashlog = os.path.join(logs_dir, "crashlog.txt")
log_warnings = os.path.join(logs_dir, "warnings.txt")
log_unhandled = os.path.join(logs_dir, "unhandled.txt")
log_s2v = os.path.join(logs_dir, "Source2Viewer-CLI.txt")
log_rescomp = os.path.join(logs_dir, "resourcecompiler.txt")

# config
main_config_file_dir = os.path.join(config_dir, "minify_config.json")
mods_config_dir = os.path.join(config_dir, "mods.json")

# killswitch accident 2025-09-25
if frozen:
    version_file_dir = "version"
else:
    version_file_dir = os.path.join(os.pardir, "version")

rescomp_override = True if os.path.exists(rescomp_override_dir) else False


def read_json_file(path):
    try:
        with open(path) as file:
            return jsonc.load(file)
    except (FileNotFoundError, jsonc.JSONDecodeError):
        return {}


def write_json_file(path, data):
    with open(path, "w") as file:
        jsonc.dump(data, file, indent=2)


def update_json_file(path, key, value):
    data = read_json_file(path)
    data[key] = value
    write_json_file(path, data)
    return value


def get_config(key, default_value=None):
    "Get config value from the main config file with default and set the default onto config."
    data = read_json_file(main_config_file_dir)
    if key in data:
        return data[key]

    if default_value is not None:
        return update_json_file(main_config_file_dir, key, default_value)

    return None


def set_config(key, value):
    "Set config value for the main config file."
    return update_json_file(main_config_file_dir, key, value)


def get_config__file(file, key, default=None):
    "Get config value from a file with default and return the dict for later use."
    data = read_json_file(file)
    return data.get(key, default), data


def get_config__dict(data, key, default=None):
    "Get config value from preexisting dict."
    return data.get(key, default)


def get_mod_config(mod_name, default=None):
    "Get config value for mods and return the dict for later use."
    if default is None:
        default = {}
    return get_config("modconf", {}).get(mod_name, default)


def set_mod_config(mod_name, config_data):
    "Set config value for mods."
    modconf = get_config("modconf", {})
    modconf[mod_name] = config_data
    set_config("modconf", modconf)


def write_crashlog(exc_type=None, exc_value=None, exc_traceback=None, header=None, handled=True):
    from helper import add_text_to_terminal, open_thing

    path = log_crashlog if handled else log_unhandled
    with open(path, "w") as file:
        if handled:
            if header:
                file.write(message := f"{header}\n\n{traceback.format_exc()}")
            else:
                file.write(message := traceback.format_exc())
        else:
            file.write(message := f"{''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))}")
    if message:
        add_text_to_terminal(message, type="error")
    open_thing(log_crashlog) if handled else open_thing(log_unhandled)


def write_warning(header=None):
    from helper import add_text_to_terminal, open_thing

    if not os.path.exists(log_warnings):
        open(log_warnings, "w").close()

    with open(log_warnings, "a") as file:
        if "NoneType: None" not in traceback.format_exc():
            if header:
                file.write(message := f"{header}\n\n{traceback.format_exc()}\n{'-' * 50}\n\n")
            else:
                file.write(message := traceback.format_exc() + f"\n{'-' * 50}\n\n")
        else:
            file.write(message := f"{header}\n{'-' * 50}\n\n")
    if message:
        add_text_to_terminal(message, type="warning")


def unhandled_handler(handled=False):
    def handler(exc_type, exc_value, exc_traceback):
        return write_crashlog(exc_type, exc_value, exc_traceback, handled=handled)

    return handler


sys.excepthook = unhandled_handler()


def find_library_from_vdf(steam_root):
    try:
        if (
            steam_root
            and steam_root != "."  # ?
            and os.path.exists(reg_path := os.path.join(steam_root, "config", "libraryfolders.vdf"))
        ):
            with open(
                os.path.join(reg_path),
                encoding="utf-8",
            ) as dump:
                vdf_data = vdf.load(dump)

            paths = []
            for folder_key in vdf_data.get("libraryfolders", {}):
                folder = vdf_data["libraryfolders"][folder_key]
                # brute
                if "path" in folder:
                    paths.append(folder["path"])

            for path in paths:
                if os.path.exists(os.path.join(path, DOTA_EXECUTABLE_PATH)) or os.path.exists(
                    os.path.join(path, DOTA_EXECUTABLE_PATH_FALLBACK)
                ):
                    set_config("steam_library", path)
                    break

    except:
        write_warning("Error reading libraryfolders.vdf")
        set_config("steam_library", "")


def get_steam_root_path():
    # Try to get steam root from registry keys on windows or known locations

    steam_root = get_config("steam_root", "")

    if steam_root and os.path.exists(steam_root):
        return steam_root

    found_path = ""
    # registry
    if OS == WIN:
        import winreg

        try:
            hkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
            steam_path = winreg.QueryValueEx(hkey, "InstallPath")[0]
            if os.path.exists(steam_path):
                found_path = steam_path
        except:
            pass

    # defaults
    if not found_path and os.path.exists(STEAM_DEFAULT_INSTALLATION_PATH):
        found_path = STEAM_DEFAULT_INSTALLATION_PATH

    if found_path:
        set_config("steam_root", found_path)
        set_config("steam_library", found_path)  # assume, will be checked anyway
        return found_path

    return ""


def handle_non_default_path(steam_root):
    steam_library = get_config("steam_library", "")
    # when dota2 is not inside root steam installation directory, use library VDFs to determine where it's at
    if not os.path.exists(os.path.join(steam_library, DOTA_EXECUTABLE_PATH)):
        find_library_from_vdf(steam_root)

        steam_library = get_config("steam_library", "")

    # last line of defense
    while not steam_library or (
        not os.path.exists(os.path.join(steam_library, DOTA_EXECUTABLE_PATH))
        and not os.path.exists(os.path.join(steam_library, DOTA_EXECUTABLE_PATH_FALLBACK))
    ):
        try:
            import tkinter as tk
            from tkinter import filedialog, messagebox

            root = tk.Tk()
            root.withdraw()

            root.wm_attributes("-topmost", 1)
            choice = messagebox.askokcancel(
                "Minify Install Path Handler",
                "We couldn't find your Dota2 install path, please select your steam installation directory or the library that Dota2 is located in",
                parent=root,
            )
            root.lift()
            root.focus_force()

            if choice:
                steam_library = os.path.normpath(filedialog.askdirectory())
                set_config("steam_library", steam_library)

                # if user selected installdir instead of library(steamapps|steamlibrary) try to get vdf
                if (
                    os.path.exists(os.path.join(steam_library, "config", "libraryfolders.vdf"))
                    and not steam_library
                    or (
                        not os.path.exists(os.path.join(steam_library, DOTA_EXECUTABLE_PATH))
                        and not os.path.exists(os.path.join(steam_library, DOTA_EXECUTABLE_PATH_FALLBACK))
                    )
                ):
                    find_library_from_vdf(steam_root)

            else:
                quit()

            root.destroy()
            break
        except:
            write_crashlog(
                "Could not open directory picker. Set your Steam library path in 'config/minify_config.json[\"steam_library\"]' and restart Minify.\n"
                f"Expected something like: {STEAM_DEFAULT_INSTALLATION_PATH}\n",
            )
            break


# case 1: got steam path from query_steam_path and dota exists under the installdir => pass
# case 2: got steam path from query_steam_path but dota doesn't exist under the installdir => read vdf
# case 3: query_steam_path failed
#         => try to get it with default installdirs
#                 => steam exists under default installdirs => read vdf
#                 => steam doesn't exist under default installdirs => prompt user for the library dota OR steam installdir
steam_root = get_steam_root_path()
handle_non_default_path(steam_root)
steam_library = get_config("steam_library")


def get_steam_accounts():
    accounts = []
    if not steam_root or not os.path.exists(os.path.join(steam_root, "userdata")):
        return accounts

    try:
        for user_id in sorted(os.listdir(os.path.join(steam_root, "userdata")), key=lambda x: int(x)):
            if not os.path.exists(os.path.join(steam_root, "userdata", user_id, "570")):
                continue

            localconfig_path = os.path.join(steam_root, "userdata", user_id, "config", "localconfig.vdf")
            if os.path.exists(localconfig_path):
                try:
                    with open(localconfig_path, encoding="utf-8") as f:
                        data = vdf.load(f)
                        store = data.get("UserLocalConfigStore", {})
                        friends = store.get("friends", {})

                        username = friends.get("PersonaName")

                        if not username:
                            username = "?"

                        accounts.append(
                            {
                                "id": user_id,
                                "name": username,
                            }
                        )
                except:
                    accounts.append({"id": user_id, "name": "?", "avatar": ""})
    except:
        write_warning("Failed to fetch steam accounts")

    return accounts


# Auto-determine a steam_id if not set
current_steam_id = get_config("steam_id")
if not current_steam_id and steam_root:
    for account in get_steam_accounts():
        set_config("steam_id", account["id"])
        break


# links
version_query = f"https://raw.githubusercontent.com/{head_owner}/{repo_name}/refs/heads/main/version"
discord = "https://discord.com/invite/2YDnqpbcKM"
latest_release = f"https://github.com/{head_owner}/{repo_name}/releases"
s2v_cli_ver = "17.0"
rg_ver = "15.1.0"

try:
    if OS == WIN:
        steam_executable_path = os.path.join(
            get_config("steam_root", os.path.join(STEAM_DEFAULT_INSTALLATION_PATH)), "steam.exe"
        )

        s2v_executable = "Source2Viewer-CLI.exe"

        if MACHINE in ["aarch64", "arm64"]:
            s2v_latest = f"https://github.com/ValveResourceFormat/ValveResourceFormat/releases/download/{s2v_cli_ver}/cli-macos-x64.zip"
        else:
            s2v_latest = f"https://github.com/ValveResourceFormat/ValveResourceFormat/releases/download/{s2v_cli_ver}/cli-windows-x64.zip"

        rg_executable = "rg.exe"
        if ARCHITECTURE == "64bit":
            rg_latest = f"https://github.com/BurntSushi/ripgrep/releases/download/{rg_ver}/ripgrep-{rg_ver}-x86_64-pc-windows-msvc.zip"
        else:
            rg_latest = f"https://github.com/BurntSushi/ripgrep/releases/download/{rg_ver}/ripgrep-{rg_ver}-i686-pc-windows-msvc.zip"

    elif OS == LINUX:
        steam_executable_path = os.path.join(
            get_config("steam_root", os.path.join(STEAM_DEFAULT_INSTALLATION_PATH)), "steam.exe"
        )

        s2v_executable = "Source2Viewer-CLI"
        if MACHINE in ["aarch64", "arm64"]:
            s2v_latest = f"https://github.com/ValveResourceFormat/ValveResourceFormat/releases/download/{s2v_cli_ver}/cli-linux-arm64.zip"
        elif MACHINE in ["armv7l", "arm"]:
            s2v_latest = f"https://github.com/ValveResourceFormat/ValveResourceFormat/releases/download/{s2v_cli_ver}/cli-linux-arm.zip"
        elif ARCHITECTURE == "64bit":
            s2v_latest = f"https://github.com/ValveResourceFormat/ValveResourceFormat/releases/download/{s2v_cli_ver}/cli-linux-x64.zip"

        rg_executable = "rg"
        if MACHINE in ["aarch64", "arm64"]:
            rg_latest = f"https://github.com/BurntSushi/ripgrep/releases/download/{rg_ver}/ripgrep-{rg_ver}-aarch64-unknown-linux-gnu.tar.gz"
        elif MACHINE in ["armv7l", "arm"]:
            rg_latest = f"https://github.com/BurntSushi/ripgrep/releases/download/{rg_ver}/ripgrep-{rg_ver}-armv7-unknown-linux-gnueabihf.tar.gz"
        elif MACHINE == "ppc64":  # unlikely
            rg_latest = f"https://github.com/BurntSushi/ripgrep/releases/download/{rg_ver}/ripgrep-{rg_ver}-powerpc64-unknown-linux-gnu.tar.gz"
        elif MACHINE == "s390x":  # unlikely
            rg_latest = f"https://github.com/BurntSushi/ripgrep/releases/download/{rg_ver}/ripgrep-{rg_ver}-s390x-unknown-linux-gnu.tar.gz"
        elif ARCHITECTURE == "64bit":
            rg_latest = f"https://github.com/BurntSushi/ripgrep/releases/download/{rg_ver}/ripgrep-{rg_ver}-x86_64-unknown-linux-musl.tar.gz"
        elif ARCHITECTURE == "32bit":
            rg_latest = f"https://github.com/BurntSushi/ripgrep/releases/download/{rg_ver}/ripgrep-{rg_ver}-i686-unknown-linux-gnu.tar.gz"

    elif OS == MAC:
        steam_executable_path = os.path.join(
            get_config("steam_root", os.path.join(STEAM_DEFAULT_INSTALLATION_PATH)), "steam"  # ?
        )

        s2v_executable = "Source2Viewer-CLI"
        if MACHINE in ["aarch64", "arm64"]:
            s2v_latest = f"https://github.com/ValveResourceFormat/ValveResourceFormat/releases/download/{s2v_cli_ver}/cli-macos-arm64.zip"
        elif ARCHITECTURE == "64bit":
            s2v_latest = f"https://github.com/ValveResourceFormat/ValveResourceFormat/releases/download/{s2v_cli_ver}/cli-macos-x64.zip"

        rg_executable = "rg"
        if MACHINE in ["aarch64", "arm64"]:
            rg_latest = f"https://github.com/BurntSushi/ripgrep/releases/download/{rg_ver}/ripgrep-{rg_ver}-aarch64-apple-darwin.tar.gz"
        else:
            rg_latest = f"https://github.com/BurntSushi/ripgrep/releases/download/{rg_ver}/ripgrep-{rg_ver}-x86_64-apple-darwin.tar.gz"
    else:
        raise Exception("Unsupported platform!")

except:
    write_crashlog(f"Unsupported configuration ({OS}/{MACHINE}/{ARCHITECTURE})")

# dota2 paths
## minify
### resourcecompiler required dir
minify_dota_compile_input_path = os.path.join(
    steam_library, "steamapps", "common", "dota 2 beta", "content", "dota_addons", "minify"
)
### compiled files from resourcefiles
minify_dota_compile_output_path = os.path.join(
    steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_addons", "minify"
)
### required dir for tools
minify_dota_tools_required_path = os.path.join(
    steam_library, "steamapps", "common", "dota 2 beta", "content", "dota_minify"
)
### vpk destination
minify_dota_pak_output_path = os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_minify")
minify_dota_possible_language_output_paths = [
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_minify"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_brazilian"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_bulgarian"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_czech"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_danish"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_dutch"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_finnish"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_french"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_german"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_greek"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_hungarian"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_italian"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_japanese"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_koreana"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_latam"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_norwegian"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_polish"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_portuguese"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_romanian"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_russian"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_schinese"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_spanish"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_swedish"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_tchinese"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_thai"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_turkish"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_ukrainian"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota_vietnamese"),
]
# required for tools to launch
minify_dota_content_path = os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "content", "dota_minify")
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
dota2_executable = os.path.join(steam_library, DOTA_EXECUTABLE_PATH)
dota2_tools_executable = os.path.join(steam_library, DOTA_TOOLS_EXECUTABLE_PATH)
dota_game_pak_path = os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota", "pak01_dir.vpk")
dota_core_pak_path = os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "core", "pak01_dir.vpk")
dota_map_path = os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota", "maps", "dota.vpk")
dota_resource_compiler_path = os.path.join(
    steam_library,
    "steamapps",
    "common",
    "dota 2 beta",
    "game",
    "bin",
    "win64",
    "resourcecompiler.exe",
)

dota_tools_paths = [
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "bin"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "core"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota", "bin"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota", "tools"),
    os.path.join(steam_library, "steamapps", "common", "dota 2 beta", "game", "dota", "gameinfo.gi"),
]
dota_tools_extraction_paths = [
    os.path.join(rescomp_override_dir, "game", "bin"),
    os.path.join(rescomp_override_dir, "game", "core"),
    os.path.join(rescomp_override_dir, "game", "dota", "bin"),
    os.path.join(rescomp_override_dir, "game", "dota", "tools"),
    os.path.join(rescomp_override_dir, "game", "dota", "gameinfo.gi"),
]

mods_alphabetical = []
mods_with_order = []
visually_unavailable_mods = []
visually_available_mods = []
mod_dependencies_list = []
for mod in sorted(os.listdir(mods_dir)):
    mod_path = os.path.join(mods_dir, mod)
    if not mod.startswith("_"):
        if os.path.isdir(mod_path):
            mods_alphabetical.append(mod)

            cfg_exist = os.path.exists(mod_cfg := os.path.join(mod_path, "modcfg.json"))
            blacklist_exist = os.path.exists(os.path.join(mod_path, "blacklist.txt"))

            order, cfg = get_config__file(mod_cfg, "order", 1)
            dependencies = get_config__dict(cfg, "dependencies", None)
            visual = get_config__dict(cfg, "visual", True)
            visually_available_mods.append(mod) if visual else visually_unavailable_mods.append(mod)
            if dependencies is not None:
                mod_dependencies_list.append({mod: dependencies})

            # Default order, blacklist mods should always be indexed last
            if blacklist_exist and not cfg_exist:
                mods_with_order.append({mod: 2})
            else:
                mods_with_order.append({mod: order})

        elif mod.endswith(".vpk"):
            mods_alphabetical.append(mod)
            visually_available_mods.append(mod)
            mods_with_order.append({mod: 1})

mods_with_order = sorted(mods_with_order, key=lambda d: list(d.values())[0])
mods_with_order = [list(d.keys())[0] for d in mods_with_order]

main_window_width = 550
main_window_height = 400
