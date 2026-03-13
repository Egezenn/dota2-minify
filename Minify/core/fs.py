"Filesystem access"

import os
import shlex
import shutil
import stat
import subprocess

import jsonc

from . import base, log


def open_thing(path, args=""):
    try:
        # If args are provided and target is executable, prefer launching directly
        if args:
            if base.OS == base.WIN:
                os.startfile(path, arguments=args)
                return
            # POSIX: launch executable directly when possible
            if os.access(path, os.X_OK) and os.path.isfile(path):
                cmd = [path] + shlex.split(args)
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            # Non-executables with args: fall back to opening container directory
            path = os.path.dirname(path) or "."

        # No args path open
        if os.path.isdir(path):
            if base.OS == base.WIN:
                os.startfile(path)
            elif base.OS == base.MAC:
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])
        else:
            if base.OS == base.WIN:
                os.startfile(path)
            elif base.OS == base.MAC:
                # Reveal the file in Finder to avoid missing-app association errors
                subprocess.run(["open", "-R", path])
            else:
                subprocess.run(["xdg-open", path])
    except FileNotFoundError:
        import helper

        helper.add_text_to_terminal("&open_dir_fail", path, type="error")


def move_path(src, dst):
    "Superset of `shutil.move`, `os.rename` to handle permissions for moving and renaming."
    try:
        shutil.move(src, dst)
    except PermissionError:
        try:
            paths_to_chmod = []
            if os.path.exists(src):
                paths_to_chmod.append(src)
            if os.path.exists(dst):
                paths_to_chmod.append(dst)

            for path in paths_to_chmod:
                if os.path.isdir(path):
                    for dir, _, filenames in os.walk(path):
                        current_dir_mode = os.stat(dir).st_mode
                        os.chmod(dir, current_dir_mode | stat.S_IWUSR)

                        for filename in filenames:
                            filepath = os.path.join(dir, filename)
                            current_file_mode = os.stat(filepath).st_mode
                            os.chmod(filepath, current_file_mode | stat.S_IWUSR)
                else:
                    current_file_mode = os.stat(path).st_mode
                    os.chmod(path, current_file_mode | stat.S_IWUSR)

            return move_path(src, dst)
        except:
            log.write_warning()
    except FileNotFoundError:
        print(f"Skipped move of: {src} (not found)")


def remove_path(*paths):
    "Superset of `shutil.rmtree` to handle permissions and take in list of paths and also delete files."
    try:
        for path in paths:
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except FileNotFoundError:
                print(f"Skipped deletion of: {path}")

    except PermissionError:
        try:
            for path in paths:
                if os.path.isdir(path):
                    for dir, _, filenames in os.walk(path):
                        current_dir_mode = os.stat(dir).st_mode
                        os.chmod(dir, current_dir_mode | stat.S_IWUSR)

                        for filename in filenames:
                            filepath = os.path.join(dir, filename)
                            current_file_mode = os.stat(filepath).st_mode
                            os.chmod(filepath, current_file_mode | stat.S_IWUSR)
                else:
                    current_file_mode = os.stat(path).st_mode
                    os.chmod(path, current_file_mode | stat.S_IWUSR)

            return remove_path(*paths)
        except:
            log.write_warning()


def create_dirs(*paths):
    for path in paths:
        os.makedirs(path, exist_ok=True)


def read_json_file(path):
    try:
        with open(path, encoding="utf-8") as file:
            return jsonc.load(file)
    except (FileNotFoundError, jsonc.JSONDecodeError):
        return {}


def write_json_file(path, data):
    with open(path, "w", encoding="utf-8") as file:
        jsonc.dump(data, file, indent=2)


def update_json_file(path, key, value):
    data = read_json_file(path)
    data[key] = value
    write_json_file(path, data)
    return value


def get_config(key, default_value=None):
    "Get config value from the main config file with default and set the default onto config."
    data = read_json_file(base.main_config_file_dir)
    if key in data:
        return data[key]

    if default_value is not None:
        return update_json_file(base.main_config_file_dir, key, default_value)

    return None


def set_config(key, value):
    "Set config value for the main config file."
    return update_json_file(base.main_config_file_dir, key, value)


def get_mod_config(mod_name, default=None):
    "Get config value for mods."
    if default is None:
        default = {}
    return get_config("modconf", {}).get(mod_name, default)


def set_mod_config(mod_name, config_data):
    "Set config value for mods."
    modconf = get_config("modconf", {})
    modconf[mod_name] = config_data
    set_config("modconf", modconf)
