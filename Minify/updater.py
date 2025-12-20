"Updater executable."

import os
import sys
import shutil
import time
import zipfile
import subprocess
import tempfile
import argparse
import glob

# Configuration
# - bin/rescomproot -> keep
# - config -> keep
# - mods -> rename to mods_old_v{version}
# - mods* -> keep
# - Source2Viewer-CLI.exe -> keep
# - rg.exe -> keep
# - updater.exe -> keep (self)


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

    zip_path = args.zip_path

    if not os.path.exists(zip_path):
        print(f"Error: Update file {zip_path} not found.")
        time.sleep(3)
        return

    print("Starting update process...")

    time.sleep(2)  # Give a moment for Minify to close

    current_version = get_current_version()
    print(f"Current Version: {current_version}")

    try:
        print(f"Extracting {zip_path}...")
        temp_dir = tempfile.mkdtemp()
        with zipfile.ZipFile(zip_path) as zip_ref:
            zip_ref.extractall(temp_dir)

        backup_dir = tempfile.mkdtemp()

        items_to_keep = [
            ("bin/rescomproot", "bin/rescomproot"),
            ("config", "config"),
            ("Source2Viewer-CLI.exe", "Source2Viewer-CLI.exe"),
            ("Source2Viewer-CLI", "Source2Viewer-CLI"),
            ("rg.exe", "rg.exe"),
            ("rg", "rg"),
        ]

        if os.path.exists("mods"):
            mods_dest = f"mods_old_v{current_version}"
            print(f"Backing up mods to {mods_dest}...")
            shutil.move("mods", os.path.join(backup_dir, mods_dest))

        for item in glob.glob("mods*"):
            print(f"Preserving {item}...")
            shutil.move(item, os.path.join(backup_dir, item))

        for item_path, item_name in items_to_keep:
            if os.path.exists(item_path):
                print(f"Preserving {item_path}...")
                dest = os.path.join(backup_dir, item_name)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.move(item_path, dest)

        print("Cleaning up old files...")

        # Identify self executable name to avoid deleting it
        self_name = os.path.basename(sys.argv[0])
        # Also avoid deleting the zip file we are using!
        zip_name = os.path.basename(zip_path)

        for item in os.listdir("."):
            if item.lower() == self_name.lower() or item.lower() == zip_name.lower():
                continue

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
        if os.path.exists("Minify.exe"):
            subprocess.Popen(["Minify.exe"])
        elif os.path.exists("Minify"):
            subprocess.Popen(["./Minify"])

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
