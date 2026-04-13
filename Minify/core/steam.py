"""
Module to find steam root and library that Dota2 is in (always accounts the Windows' executable path to find if used through an emulation layer).
Also fixes language argument for the user(s)
"""

import os
import sys

import vdf

from core import base, config, log, utils


def remove_lang_args(arg_string):
    "Parse launch options, remove language argument and return a clean string"

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


def fix_launch_options():
    """
    Fixes user(s) launch options with the language argument that has the current output path.
    Does it for all accounts available if "apply_for_all" key is set.
    """
    from ui import terminal

    steam_ids = []
    successful_ids = []
    if config.get("apply_for_all", True):
        for account in get_steam_accounts():
            steam_ids.append(account["id"])
    else:
        steam_ids.append(config.get("steam_id"))

    for steam_id in steam_ids:
        vdf_path = os.path.join(config.get("steam_root"), "userdata", steam_id, "config", "localconfig.vdf")
        if not os.path.exists(vdf_path):
            continue

        with utils.open_utf8R(vdf_path) as file:
            terminal.add_text("&checking_launch_options")
            data = vdf.load(file)

        locale = config.get("output_locale")
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

            terminal.add_text("&discrepancy_launch_options", user_name, locale)

            data["UserLocalConfigStore"]["Software"]["Valve"]["Steam"]["apps"][base.STEAM_DOTA_ID]["LaunchOptions"] = (
                f"-language {locale} {remove_lang_args(launch_options)}"
            )
        with utils.open_utf8R(vdf_path, "w") as file:
            vdf.dump(data, file, pretty=True)
        successful_ids.append(steam_id)
    return successful_ids


def find_library_from_vdf(steam_root):
    "Find the Dota2 library from VDF"
    try:
        if (
            steam_root
            and steam_root != "."  # ?
            and os.path.exists(reg_path := os.path.join(steam_root, "config", "libraryfolders.vdf"))
        ):
            with utils.open_utf8R(os.path.join(reg_path)) as dump:
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
                    config.set("steam_library", path)
                    return True
        return False

    except Exception:
        log.write_warning("Error reading libraryfolders.vdf")
        config.set("steam_library", "")
        return False


def get_steam_root_path():
    """
    Get steam root path via
    Windows: registry, default
    Linux: default(`.local/share/Steam` for most major distrubitions)
    MacOS: default
    """
    steam_root = config.get("steam_root", "")

    if steam_root and os.path.exists(steam_root):
        return steam_root

    found_path = ""
    # registry
    if base.OS == base.WIN:
        with utils.try_pass():
            import winreg

            hkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
            steam_path = winreg.QueryValueEx(hkey, "InstallPath")[0]
            if os.path.exists(steam_path):
                found_path = steam_path

    # defaults
    if not found_path and os.path.exists(base.STEAM_DEFAULT_INSTALLATION_PATH):
        found_path = base.STEAM_DEFAULT_INSTALLATION_PATH

    if found_path:
        config.set("steam_root", found_path)
        config.set("steam_library", found_path)  # assume, will be checked anyway
        return found_path

    return ""


def handle_non_default_path(steam_root):
    """
    Handles Dota2 finding
    root = library: found
    root != library: find from library VDF
    if root is unknown: user is manually prompted to select root, library will be found via VDF
    """
    steam_library = config.get("steam_library", "")
    if not os.path.exists(os.path.join(steam_library, base.DOTA_EXECUTABLE_PATH)):
        find_library_from_vdf(steam_root)
        steam_library = config.get("steam_library", "")

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
                "We couldn't find your Steam installation, please select your Steam installation directory",
                parent=root,
            )
            root.lift()
            root.focus_force()

            if choice:
                steam_root = os.path.normpath(filedialog.askdirectory())
                config.set("steam_root", steam_root)
                find_library_from_vdf(steam_root)
                steam_library = config.get("steam_library")

            else:
                sys.exit()

            root.destroy()

        except Exception as e:
            messagebox.showerror(
                "Minify Install Path Handler",
                f'An unexpected error happened. Set your Steam paths in \'config/minify_config.json > "steam_root", "steam_library"\' and restart Minify.\n\nError: {e}',
                parent=root,
            )
            root.lift()
            root.focus_force()
            break
    return steam_root


def get_steam_accounts():
    "Get all users that have Dota2 data"
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
                    with utils.open_utf8R(localconfig_path) as f:
                        data = vdf.load(f)
                        friends = data.get("UserLocalConfigStore", {}).get("friends", {})
                        username = friends.get("PersonaName", "?")
                        accounts.append({"id": user_id, "name": username})
                except Exception:
                    accounts.append({"id": user_id, "name": "?"})
    except Exception:
        log.write_warning("Failed to fetch steam accounts")

    return accounts


ROOT = get_steam_root_path()
ROOT = handle_non_default_path(ROOT)
LIBRARY = config.get("steam_library")

# Auto-determine a steam_id if not set
current_steam_id = config.get("steam_id")
if not current_steam_id and ROOT:
    for account in get_steam_accounts():
        config.set("steam_id", account["id"])
        break

# paths
if base.OS == base.WIN:
    steam_executable_path = os.path.join(ROOT, "steam.exe")
elif base.OS == base.LINUX:
    steam_executable_path = os.path.join(ROOT, "steam")
elif base.OS == base.MAC:
    steam_executable_path = os.path.join(ROOT, "steam")  # ?
