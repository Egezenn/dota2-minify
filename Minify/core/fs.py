"Filesystem access"

import os
import shlex
import shutil
import stat
import subprocess
import tarfile
import time
import zipfile

import dearpygui.dearpygui as dpg
import requests

from core import base, log


def open_thing(path, args=""):
    "Opens files or directories in their regsitered applications"
    from ui import terminal

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
        terminal.add_text("&open_thing_fail", path, msg_type="error")


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
                    for root, _, filenames in os.walk(path):
                        current_dir_mode = os.stat(root).st_mode
                        os.chmod(root, current_dir_mode | stat.S_IWUSR)

                        for filename in filenames:
                            filepath = os.path.join(root, filename)
                            current_file_mode = os.stat(filepath).st_mode
                            os.chmod(filepath, current_file_mode | stat.S_IWUSR)
                else:
                    current_file_mode = os.stat(path).st_mode
                    os.chmod(path, current_file_mode | stat.S_IWUSR)

            return move_path(src, dst)
        except Exception:
            log.write_warning()
    except FileNotFoundError:
        print(f"Skipped move of: {src} (not found)")


def remove_path(*paths):
    "Superset of `shutil.rmtree` & `os.remove` to handle permissions. Takes in list of paths."
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
                    for root, _, filenames in os.walk(path):
                        current_dir_mode = os.stat(root).st_mode
                        os.chmod(root, current_dir_mode | stat.S_IWUSR)

                        for filename in filenames:
                            filepath = os.path.join(root, filename)
                            current_file_mode = os.stat(filepath).st_mode
                            os.chmod(filepath, current_file_mode | stat.S_IWUSR)
                else:
                    current_file_mode = os.stat(path).st_mode
                    os.chmod(path, current_file_mode | stat.S_IWUSR)

            return remove_path(*paths)
        except Exception:
            log.write_warning()


def create_dirs(*paths):
    "`os.makedirs(path, exist_ok=True)` that takes list of paths."
    for path in paths:
        os.makedirs(path, exist_ok=True)


def download_file(url, target_path, progress_tag=None):
    """
    Downloads a file from url to target_path using requests.
    Updates the UI progress_tag with "Downloading: X.XX/Y.YY MB" if provided.
    """
    from ui import terminal

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        total_size = int(response.headers.get("content-length", 0))
        block_size = 8192
        downloaded = 0
        last_report_time = 0

        with open(target_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_tag:
                        current_time = time.time()
                        if current_time - last_report_time >= 0.1:
                            downloaded_mb = downloaded / (1024 * 1024)
                            total_size_mb = total_size / (1024 * 1024)
                            if total_size > 0:
                                # TODO: localize texts, use single string for downloads
                                #       "Downloading {}".format(item)
                                #       "Downloading {}".format(progress)
                                dpg.set_value(
                                    progress_tag,
                                    f"Downloading: {downloaded_mb:.2f}/{total_size_mb:.2f} MB",
                                )
                            else:
                                dpg.set_value(progress_tag, f"Downloading: {downloaded_mb:.2f} MB")
                            last_report_time = current_time
        return True
    except Exception as e:
        terminal.add_text(f"Failed to open {target_path}: {e}", msg_type="error")
        return False


def extract_archive(archive_path, extract_dir=".", target_file=None):
    """
    Extracts an archive (zip or tar.gz).
    If target_file is provided, extracts only that file (or directory structure leading to it).
    """
    from ui import terminal

    try:
        if archive_path.endswith(".zip"):
            with zipfile.ZipFile(archive_path) as zip_ref:
                if target_file:
                    zip_ref.extract(target_file, path=extract_dir)
                else:
                    zip_ref.extractall(extract_dir)
        elif archive_path.endswith((".tar.gz", ".tgz")):
            with tarfile.open(archive_path, "r:gz") as tar:
                if target_file:
                    member = tar.getmember(target_file)
                    tar.extract(member, path=extract_dir)
                else:
                    tar.extractall(extract_dir)
        else:
            terminal.add_text(f"Unsupported archive format: {archive_path}", msg_type="error")
            return False
        return True
    except Exception as e:
        terminal.add_text(f"Extraction failed: {e}", msg_type="error")
        return False


def get_file_type(path):
    """
    Identifies the file type using magic bytes.
    Returns extension string (e.g., '.png', '.jpg', '.webm') or None if unknown.
    """
    try:
        if not os.path.exists(path):
            return None

        with open(path, "rb") as f:
            header = f.read(16)

            # PNG: 89 50 4E 47 0D 0A 1A 0A
            if header.startswith(b"\x89PNG\r\n\x1a\n"):
                return ".png"

            # JPEG: FF D8 FF (Start of Image + specific marker)
            if header.startswith(b"\xff\xd8\xff"):
                return ".jpg"

            # WEBP: RIFF....WEBP
            if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
                return ".webp"

            # WEBM/MKV: 1A 45 DF A3 (EBML)
            if header.startswith(b"\x1a\x45\xdf\xa3"):
                return ".webm"

            # MP4: ....ftyp
            if header[4:8] == b"ftyp":
                return ".mp4"

            # GIF
            if header.startswith(b"GIF87a") or header.startswith(b"GIF89a"):
                return ".gif"

    except Exception:
        pass
    return None
