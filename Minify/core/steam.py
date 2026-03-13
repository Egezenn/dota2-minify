import os

import vdf

from . import base, fs, log


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
                if os.path.exists(os.path.join(path, base.DOTA_EXECUTABLE_PATH)) or os.path.exists(
                    os.path.join(path, base.DOTA_EXECUTABLE_PATH_FALLBACK)
                ):
                    fs.set_config("steam_library", path)
                    break

    except:
        log.write_warning("Error reading libraryfolders.vdf")
        fs.set_config("steam_library", "")


def get_steam_root_path():
    # Try to get steam root from registry keys on windows or known locations

    steam_root = fs.get_config("steam_root", "")

    if steam_root and os.path.exists(steam_root):
        return steam_root

    found_path = ""
    # registry
    if base.OS == base.WIN:
        import winreg

        try:
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
        fs.set_config("steam_root", found_path)
        fs.set_config("steam_library", found_path)  # assume, will be checked anyway
        return found_path

    return ""


def handle_non_default_path(steam_root):
    steam_library = fs.get_config("steam_library", "")
    # when dota2 is not inside root steam installation directory, use library VDFs to determine where it's at
    if not os.path.exists(os.path.join(steam_library, base.DOTA_EXECUTABLE_PATH)):
        find_library_from_vdf(steam_root)

        steam_library = fs.get_config("steam_library", "")

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
                fs.set_config("steam_library", steam_library)

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
                quit()

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
        for user_id in sorted(
            [
                x
                for x in os.listdir(os.path.join(ROOT, "userdata"))
                if x.isdigit() and os.path.isdir(os.path.join(ROOT, "userdata", x))
            ],
            key=lambda x: int(x),
        ):
            if not os.path.exists(os.path.join(ROOT, "userdata", user_id, base.STEAM_DOTA_ID)):
                continue

            localconfig_path = os.path.join(ROOT, "userdata", user_id, "config", "localconfig.vdf")
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
LIBRARY = fs.get_config("steam_library")

# Auto-determine a steam_id if not set
current_steam_id = fs.get_config("steam_id")
if not current_steam_id and ROOT:
    for account in get_steam_accounts():
        fs.set_config("steam_id", account["id"])
        break
