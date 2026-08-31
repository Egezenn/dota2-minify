"Variables that almost never change"

import getpass
import os
import platform
import sys

VERSION = "1.13.1"
TITLE = f"Minify {VERSION}"

OS = platform.system()
MACHINE = platform.machine().lower()
ARCHITECTURE = platform.architecture()[0]

is_win = True if OS == "Windows" else False
is_linux = True if OS == "Linux" else False
is_mac = True if OS == "Darwin" else False

FROZEN = getattr(sys, "frozen", False)
HEADLESS = True

OWNER = "Egezenn"
REPO = "dota2-minify"


if is_linux:
    if os.environ.get("WAYLAND_DISPLAY") or os.environ.get("XDG_SESSION_TYPE") == "wayland":
        os.environ.setdefault("GDK_BACKEND", "x11")
        os.environ.setdefault("WEBKIT_DISABLE_DMABUF_RENDERER", "1")

    DOTA_EXECUTABLE_PATH = os.path.join("steamapps", "common", "dota 2 beta", "game", "bin", "linuxsteamrt64", "dota2")
    STEAM_DEFAULT_INSTALLATION_PATH = os.path.join("/", "home", getpass.getuser(), ".local", "share", "Steam")
elif is_mac:
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

STEAM_DOTA_ID = "570"
STEAM_DOTA_WORKSHOP_TOOLS_ID = "313250"

# static directory names
if FROZEN:
    base_dir = os.path.dirname(os.path.abspath(sys.executable))
    bundle_dir = getattr(sys, "_MEIPASS", base_dir)
    web_dir = os.path.abspath(os.path.join(bundle_dir, "ui"))
else:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bundle_dir = base_dir
    web_dir = os.path.abspath(os.path.join(base_dir, "ui", "web", "dist"))

plugins_dir = os.path.abspath(os.path.join(base_dir, "plugins"))
dist_index = os.path.abspath(os.path.join(web_dir, "index.html"))

if base_dir not in sys.path:
    sys.path.insert(0, base_dir)


bin_dir = "bin"
bundle_bin_dir = os.path.abspath(os.path.join(bundle_dir, "bin"))
build_dir = "vpk_build"
replace_dir = "vpk_replace"
merge_dir = "vpk_merge"
logs_dir = "logs"
mods_dir = "mods"
config_dir = "config"
cache_dir = "cache"


# bin
blank_files_dir = os.path.join(bin_dir, "blank-files")
img_dir = os.path.join(bin_dir, "images")
localization_file_dir = os.path.join(bundle_bin_dir, "localization.json")
settings_file_dir = os.path.join(bundle_bin_dir, "settings.json")
rescomp_override_dir = os.path.join(bin_dir, "rescomproot")
sounds_dir = os.path.join(bin_dir, "sounds")

# logs
log_crashlog = os.path.join(logs_dir, "crashlog.txt")
log_warnings = os.path.join(logs_dir, "warnings.txt")
log_unhandled = os.path.join(logs_dir, "unhandled.txt")
log_s2v = os.path.join(logs_dir, "Source2Viewer-CLI.txt")
log_rescomp = os.path.join(logs_dir, "resourcecompiler.txt")

# cache
dota_steam_inf_cache = os.path.join(cache_dir, "steam.inf")
states_file_dir = os.path.join(cache_dir, "states.json")

# config
main_config_file_dir = os.path.join(config_dir, "minify_config.json")
mods_config_dir = os.path.join(config_dir, "mods.json")

# links
discord = "https://discord.com/invite/9867CPv7cy"
telegram = "https://t.me/dota2minify"
github = f"https://github.com/{OWNER}/{REPO}"
github_latest = github + "/releases/latest"
github_io = f"https://{OWNER}.github.io/{REPO}"
