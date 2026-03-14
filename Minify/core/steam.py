import os
import sys

import vdf

from core import base, config, log


def remove_lang_args(arg_string):
    if not arg_string:
        return ""
    tokens = arg_string.split()
    cleaned = []
    skip_next = False

    for i, token in enumerate(tokens):
        if skip_next:
            skip_next = False
            continue

        if token == "-language":
            if i + 1 < len(tokens) and not tokens[i + 1].startswith(("-", "+")):
                skip_next = True
            continue

        cleaned.append(token)

    return " ".join(cleaned)


def fix_parameters():
    from ui import terminal

    from core import fs

    steam_ids = []
    successful_ids = []
    if config.get_config("change_parameters_for_all", True):
        for account in get_steam_accounts():
            steam_ids.append(account["id"])
    else:
        steam_ids.append(config.get_config("steam_id"))

    for steam_id in steam_ids:
        vdf_path = os.path.join(config.get_config("steam_root"), "userdata", steam_id, "config", "localconfig.vdf")
        if not os.path.exists(vdf_path):
            continue

        with open(vdf_path, encoding="utf-8") as file:
            terminal.add_text_to_terminal("&checking_launch_options")
            data = vdf.load(file)

        locale = config.get_config("output_locale")
        try:
            launch_options = data["UserLocalConfigStore"]["Software"]["Valve"]["Steam"]["apps"][base.STEAM_DOTA_ID][
                "LaunchOptions"
            ]
        except KeyError:
            continue
        if f"-language {locale}" not in launch_options or launch_options.count("-language") >= 2:
            user_name = "?"
            for user in get_steam_accounts():
                if user["id"] == steam_id:
                    user_name = user["name"]
                    break

            terminal.add_text_to_terminal("&discrepancy_launch_options", user_name, locale)
            fs.open_thing(steam_executable_path, "-exitsteam")

            data["UserLocalConfigStore"]["Software"]["Valve"]["Steam"]["apps"][base.STEAM_DOTA_ID][
                "LaunchOptions"
            ] = f"-language {locale} {remove_lang_args(launch_options)}"
        with open(vdf_path, "w", encoding="utf-8") as file:
            vdf.dump(data, file, pretty=True)
        successful_ids.append(steam_id)
    return successful_ids


def find_library_from_vdf(steam_root):
    try:
        if (
            steam_root
            and steam_root != "."  # ?
            and os.path.exists(reg_path := os.path.join(steam_root, "config", "libraryfolders.vdf"))
        ):
            with open(os.path.join(reg_path), encoding="utf-8") as dump:
                vdf_data = vdf.load(dump)

            paths = []
            for folder_key in vdf_data.get("libraryfolders", {}):
                folder = vdf_data["libraryfolders"][folder_key]
                # brute
                if "path" in folder:
                    paths.append(folder["path"])

            for path in paths:
                if os.path.exists(os.path.join(path, base.DOTA_EXECUTABLE_PATH)) or os.path.exists(
                    os.path.join(path, base.DOTA_EXECUTABLE_PATH_FALLBACK)
                ):
                    config.set_config("steam_library", path)
                    break

    except:
        log.write_warning("Error reading libraryfolders.vdf")
        config.set_config("steam_library", "")


def get_steam_root_path():
    steam_root = config.get_config("steam_root", "")

    if steam_root and os.path.exists(steam_root):
        return steam_root

    found_path = ""
    # registry
    if base.OS == base.WIN:
        try:
            import winreg

            hkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
            steam_path = winreg.QueryValueEx(hkey, "InstallPath")[0]
            if os.path.exists(steam_path):
                found_path = steam_path
        except:
            pass

    # defaults
    if not found_path and os.path.exists(base.STEAM_DEFAULT_INSTALLATION_PATH):
        found_path = base.STEAM_DEFAULT_INSTALLATION_PATH

    if found_path:
        config.set_config("steam_root", found_path)
        config.set_config("steam_library", found_path)  # assume, will be checked anyway
        return found_path

    return ""


def handle_non_default_path(steam_root):
    steam_library = config.get_config("steam_library", "")
    # when dota2 is not inside root steam installation directory, use library VDFs to determine where it's at
    if not os.path.exists(os.path.join(steam_library, base.DOTA_EXECUTABLE_PATH)):
        find_library_from_vdf(steam_root)
        steam_library = config.get_config("steam_library", "")

    # last line of defense
    while not steam_library or (
        not os.path.exists(os.path.join(steam_library, base.DOTA_EXECUTABLE_PATH))
        and not os.path.exists(os.path.join(steam_library, base.DOTA_EXECUTABLE_PATH_FALLBACK))
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
                config.set_config("steam_library", steam_library)

                # if user selected installdir instead of library(steamapps|steamlibrary) try to get vdf
                if (
                    os.path.exists(os.path.join(steam_library, "config", "libraryfolders.vdf"))
                    and not steam_library
                    or (
                        not os.path.exists(os.path.join(steam_library, base.DOTA_EXECUTABLE_PATH))
                        and not os.path.exists(os.path.join(steam_library, base.DOTA_EXECUTABLE_PATH_FALLBACK))
                    )
                ):
                    find_library_from_vdf(steam_root)

            else:
                sys.exit()

            root.destroy()
            break
        except:
            log.write_crashlog(
                "Could not open directory picker. Set your Steam library path in 'config/minify_config.json[\"steam_library\"]' and restart Minify.\n"
                f"Expected something like: {base.STEAM_DEFAULT_INSTALLATION_PATH}\n",
            )
            break


def get_steam_accounts():
    accounts = []
    if not ROOT or not os.path.exists(os.path.join(ROOT, "userdata")):
        return accounts

    try:
        user_ids = sorted(
            [
                x
                for x in os.listdir(os.path.join(ROOT, "userdata"))
                if x.isdigit() and os.path.isdir(os.path.join(ROOT, "userdata", x))
            ],
            key=lambda x: int(x),
        )
        for user_id in user_ids:
            if not os.path.exists(os.path.join(ROOT, "userdata", user_id, base.STEAM_DOTA_ID)):
                continue

            localconfig_path = os.path.join(ROOT, "userdata", user_id, "config", "localconfig.vdf")
            if os.path.exists(localconfig_path):
                try:
                    with open(localconfig_path, encoding="utf-8") as f:
                        data = vdf.load(f)
                        friends = data.get("UserLocalConfigStore", {}).get("friends", {})
                        username = friends.get("PersonaName", "?")
                        accounts.append({"id": user_id, "name": username})
                except:
                    accounts.append({"id": user_id, "name": "?"})
    except:
        log.write_warning("Failed to fetch steam accounts")

    return accounts


# case 1: got steam path from query_steam_path and dota exists under the installdir => pass
# case 2: got steam path from query_steam_path but dota doesn't exist under the installdir => read vdf
# case 3: query_steam_path failed
#         => try to get it with default installdirs
#                 => steam exists under default installdirs => read vdf
#                 => steam doesn't exist under default installdirs => prompt user for the library dota OR steam installdir
ROOT = get_steam_root_path()
handle_non_default_path(ROOT)
LIBRARY = config.get_config("steam_library")

# Auto-determine a steam_id if not set
current_steam_id = config.get_config("steam_id")
if not current_steam_id and ROOT:
    for account in get_steam_accounts():
        config.set_config("steam_id", account["id"])
        break

# paths
if base.OS == base.WIN:
    steam_executable_path = os.path.join(ROOT, "steam.exe")
elif base.OS == base.LINUX:
    steam_executable_path = os.path.join(ROOT, "steam.exe")
elif base.OS == base.MAC:
    steam_executable_path = os.path.join(ROOT, "steam")  # ?
