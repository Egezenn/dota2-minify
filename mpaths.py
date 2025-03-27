import os
import traceback
import winreg

try:
    hkey = winreg.OpenKey(
        winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam"
    )
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
if not os.path.exists(
    os.path.join(
        steam_dir, "steamapps\\common\\dota 2 beta\\game\\bin\\win64\\dota2.exe"
    )
):
    path_file = os.path.join(os.getcwd(), "dota2path_minify.txt")

    # make sure the text file exists
    if not os.path.exists(path_file):
        with open(path_file, "a+") as file:
            file.write("")

    # load the path from text file
    with open(path_file, "r") as file:
        for line in file:
            steam_dir = line.strip()

# minify project paths
minify_dir = os.getcwd()
bin_dir = os.path.join(minify_dir, "bin")
build_dir = os.path.join(minify_dir, "build")
logs_dir = os.path.join(minify_dir, "logs")
mods_dir = os.path.join(minify_dir, "mods")
# bin
blank_files_dir = os.path.join(bin_dir, "blank-files")
maps_dir = os.path.join(bin_dir, "maps")

# dota2 paths
content_dir = os.path.join(
    steam_dir, "steamapps\\common\\dota 2 beta\\content\\dota_addons\\minify"
)
game_dir = os.path.join(
    steam_dir, "steamapps\\common\\dota 2 beta\\game\\dota_addons\\minify"
)
resource_compiler = os.path.join(
    steam_dir, "steamapps\\common\\dota 2 beta\\game\\bin\\win64\\resourcecompiler.exe"
)
pak01_dir = os.path.join(
    steam_dir, "steamapps\\common\\dota 2 beta\\game\\dota\\pak01_dir.vpk"
)
itembuilds_dir = os.path.join(
    steam_dir, "steamapps\\common\\dota 2 beta\\game\\dota\\itembuilds"
)
dota_user_map_dir = os.path.join(
    steam_dir, "steamapps\\common\\dota 2 beta\\game\\dota\\maps\\dota.vpk"
)
minify_map = os.path.join(maps_dir, "dota.vpk")
dota_minify_content = os.path.join(
    steam_dir, "steamapps\\common\\dota 2 beta\\content\\dota_minify"
)
dota_minify = os.path.join(
    steam_dir, "steamapps\\common\\dota 2 beta\\game\\dota_minify"
)
dota_minify_maps = os.path.join(dota_minify, "maps")

# exclude invalid mods

mods_folders = []
for mod in os.listdir(mods_dir):
    mods_folders.append(mod)
