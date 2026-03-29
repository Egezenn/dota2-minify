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

WIN = "Windows"
LINUX = "Linux"
MAC = "Darwin"

FROZEN = getattr(sys, "frozen", False)

OWNER = "Egezenn"
REPO = "dota2-minify"


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

STEAM_DOTA_ID = "570"
STEAM_DOTA_WORKSHOP_TOOLS_ID = "313250"

# static directory names
bin_dir = "bin"
build_dir = "vpk_build"
replace_dir = "vpk_replace"
merge_dir = "vpk_merge"
logs_dir = "logs"
mods_dir = "mods"
config_dir = "config"

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

# links
discord = "https://discord.com/invite/9867CPv7cy"
telegram = "https://t.me/dota2minify"
github = f"https://github.com/{OWNER}/{REPO}"
github_latest = github + "/releases/latest"
github_io = f"https://{OWNER}.github.io/{REPO}"

main_window_width = 550
main_window_height = 440
