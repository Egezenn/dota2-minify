"Updater executable."

import argparse
import glob
import os
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import zipfile

import psutil


host = platform.system()


def get_current_version():
    try:
        with open("version") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "unknown"


def safe_rmtree(path):
    try:
        if os.path.isfile(path) or os.path.islink(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
    except Exception as e:
        print(f"Failed to delete {path}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Minify Updater")
    parser.add_argument("zip_path", help="Path to the update zip file")
    args = parser.parse_args()

    if getattr(sys, "frozen", False):
        os.chdir(os.path.dirname(sys.executable))
    else:
        sys.exit("Please run this script as a frozen executable.")

    zip_path = args.zip_path

    if not os.path.exists(zip_path):
        print(f"Error: Update file {zip_path} not found.")
        time.sleep(3)
        return

    print("Starting update process...")

    target = "Minify.exe" if host == "Windows" else "Minify"
    while any(p.info.get("name") == target for p in psutil.process_iter(attrs=["name"])):
        print(f"Waiting for {target} to close...")
        time.sleep(5)

    current_version = get_current_version()
    print(f"Current Version: {current_version}")

    try:
        print(f"Extracting {zip_path}...")
        temp_dir = tempfile.mkdtemp()
        with zipfile.ZipFile(zip_path) as zip_ref:
            zip_ref.extractall(temp_dir)

        backup_dir = tempfile.mkdtemp()

        items_to_keep = [
            os.path.join("bin", "rescomproot"),
            "config",
        ]

        if os.path.exists("mods"):
            mods_dest = f"mods_old_v{current_version}"
            print(f"Backing up mods to {mods_dest}...")
            shutil.move("mods", os.path.join(backup_dir, mods_dest))

        for item in glob.glob("mods*"):
            print(f"Preserving {item}...")
            shutil.move(item, os.path.join(backup_dir, item))

        for item_path in items_to_keep:
            if os.path.exists(item_path):
                print(f"Preserving {item_path}...")
                dest = os.path.join(backup_dir, item_path)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.move(item_path, dest)

        print("Cleaning up old files...")

        items_to_delete = [
            "_internal",
            "bin",
            "mods",
            "LICENSE",
            "Minify.exe",
            "Minify",
            "readme.md",
            "version",
            "Source2Viewer-CLI.exe",
            "Source2Viewer-CLI",
            "rg.exe",
            "rg",
        ]

        for item in items_to_delete:
            safe_rmtree(item)

        print("Installing new files...")
        for item in os.listdir(temp_dir):
            s = os.path.join(temp_dir, item)
            d = os.path.join(".", item)
            if os.path.exists(d):
                safe_rmtree(d)
            shutil.move(s, d)

        print("Restoring preserved files...")
        for item in os.listdir(backup_dir):
            s = os.path.join(backup_dir, item)
            d = os.path.join(".", item)
            if os.path.exists(d):
                safe_rmtree(d)
            shutil.move(s, d)

        print("Update complete!")
        if host == "Windows":
            subprocess.Popen(
                ["Minify.exe"],
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                close_fds=True,
            )
        else:
            current_permissions = os.stat("Minify").st_mode
            os.chmod(
                "Minify",
                current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
            )
            subprocess.Popen(["./Minify"], start_new_session=True, close_fds=True)

    except Exception as e:
        print(f"Error: {e}")
        time.sleep(10)
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)
        shutil.rmtree(temp_dir, ignore_errors=True)
        shutil.rmtree(backup_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
