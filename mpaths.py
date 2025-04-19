import os
import traceback
import winreg

try:
    hkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
except Exception as exception:
    hkey = None
    with open(os.path.join(os.getcwd(), "logs\\registry.txt"), "w") as file:
        file.write(traceback.format_exc())

try:
    steam_path = winreg.QueryValueEx(hkey, "InstallPath")
except:
    steam_path = None
    with open(os.path.join(os.getcwd(), "logs\\registry_query.txt"), "w") as file:
        file.write(traceback.format_exc())

try:
    steam_dir = steam_path[0]
except:
    steam_dir = ""

# when dota2 is not inside Steam folder then set new steam directory from 'dota2path_minify.txt
# this text file is created and set by the user in validatefiles.py during startup
if not os.path.exists(os.path.join(steam_dir, "steamapps\\common\\dota 2 beta\\game\\bin\\win64\\dota2.exe")):
    path_file = os.path.join(os.getcwd(), "dota2path_minify.txt")

    # make sure the text file exists
    if not os.path.exists(path_file):
        with open(path_file, "a+") as file:
            file.write("")

    # load the path from text file
    with open(path_file, "r") as file:
        for line in file:
            steam_dir = line.strip()

# links
version_query = "https://raw.githubusercontent.com/Egezenn/dota2-minify/refs/heads/stable/version"
discord = "https://discord.com/invite/2YDnqpbcKM"
latest_release = "https://github.com/Egezenn/dota2-minify/releases/latest"
s2v_latest_windows_x64 = (
    "https://github.com/ValveResourceFormat/ValveResourceFormat/releases/latest/download/cli-windows-x64.zip"
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

# dota2 paths
## minify
### resourcecompiler required dir
minify_dota_compile_input_path = os.path.join(steam_dir, "steamapps\\common\\dota 2 beta\\content\\dota_addons\\minify")
### compiled files from resourcefiles
minify_dota_compile_output_path = os.path.join(steam_dir, "steamapps\\common\\dota 2 beta\\game\\dota_addons\\minify")
### vpk destination
minify_dota_pak_output_path = os.path.join(steam_dir, "steamapps\\common\\dota 2 beta\\game\\dota_minify")
minify_dota_maps_output_path = os.path.join(minify_dota_pak_output_path, "maps")

## base game
dota_pak01_path = os.path.join(steam_dir, "steamapps\\common\\dota 2 beta\\game\\dota\\pak01_dir.vpk")
dota_itembuilds_path = os.path.join(steam_dir, "steamapps\\common\\dota 2 beta\\game\\dota\\itembuilds")
dota_map_path = os.path.join(steam_dir, "steamapps\\common\\dota 2 beta\\game\\dota\\maps\\dota.vpk")
dota_resource_compiler_path = os.path.join(
    steam_dir, "steamapps\\common\\dota 2 beta\\game\\bin\\win64\\resourcecompiler.exe"
)

mods_folders = []
for mod in os.listdir(mods_dir):
    mods_folders.append(mod)
