import os
import shutil
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
mod_name = os.path.basename(current_dir)
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
if os.getcwd() != minify_root:
    os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

import ui
from core import base, fs, output, utils


def select_background():
    title = "Select Background Image or Video"
    file_types = ("Media Files (*.png;*.jpg;*.jpeg;*.webp;*.mp4;*.webm)", "All Files (*.*)")
    file_path = ui.pick_file(title, file_types)
    if not file_path:
        return

    actual_ext = fs.get_file_type(file_path)
    if actual_ext == ".jpeg":
        actual_ext = ".jpg"

    allowed_exts = [".png", ".jpg", ".webp", ".mp4", ".webm"]

    if not actual_ext or actual_ext not in allowed_exts:
        ui.alert(
            f"Unsupported Format: The selected file has an unsupported format or invalid magic bytes. Detected: {actual_ext}",
            msg_type="error",
        )
        return

    fs.create_dirs(base.config_dir)

    for ext in allowed_exts:
        old_bg = os.path.join(base.config_dir, f"background{ext}")
        if os.path.exists(old_bg):
            with utils.try_pass():
                fs.remove_path(old_bg)

    dest_path = os.path.join(base.config_dir, f"background{actual_ext}")

    try:
        shutil.copy2(file_path, dest_path)
    except Exception as e:
        ui.alert(f"Error copying file: {e}", msg_type="error")
        return

    ui.alert(f"Successfully set background to {os.path.basename(dest_path)}.", msg_type="success")

    original_ext = os.path.splitext(file_path)[1].lower()
    if original_ext == ".jpeg":
        original_ext = ".jpg"

    if original_ext != actual_ext:
        ui.alert(
            f"Warning: Extension mismatch. Renamed from {original_ext} to {actual_ext}.", msg_type="warning"
        )

    if actual_ext in [".jpg", ".webp"]:
        if shutil.which("magick") is None:
            ui.alert(
                "Warning: ImageMagick (magick) is required to convert this image to PNG during patching but is not found on your system.",
                msg_type="warning",
            )
    elif actual_ext == ".mp4":
        if shutil.which("ffmpeg") is None:
            ui.alert(
                "Warning: FFmpeg is required to convert this video to WEBM during patching but is not found on your system.",
                msg_type="warning",
            )
