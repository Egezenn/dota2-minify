import os
import shutil
import sys
import tkinter as tk
from tkinter import filedialog

current_dir = os.path.dirname(os.path.abspath(__file__))
mod_name = os.path.basename(current_dir)
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
if os.getcwd() != minify_root:
    os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

from core import base, fs
from ui import modal_shared


def select_background():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select Background Image or Video",
        filetypes=[("Media Files", "*.png *.jpg *.jpeg *.webp *.mp4 *.webm")],
        initialdir=os.getcwd(),
    )
    root.destroy()

    if not file_path:
        return

    actual_ext = fs.get_file_type(file_path)
    if actual_ext == ".jpeg":
        actual_ext = ".jpg"

    allowed_exts = [".png", ".jpg", ".webp", ".mp4", ".webm"]

    if not actual_ext or actual_ext not in allowed_exts:
        modal_shared.show(
            title="Unsupported Format",
            messages=[f"The selected file has an unsupported format or invalid magic bytes. Detected: {actual_ext}"],
            buttons=[{"label": "OK", "width": 100}],
        )
        return

    dest_path = os.path.join(base.config_dir, f"background{actual_ext}")

    try:
        shutil.copy2(file_path, dest_path)
    except Exception as e:
        modal_shared.show(
            title="Error", messages=[f"Failed to copy file:\n{e}"], buttons=[{"label": "OK", "width": 100}]
        )
        return

    messages = [f"Successfully set background to {os.path.basename(dest_path)}."]

    original_ext = os.path.splitext(file_path)[1].lower()
    if original_ext == ".jpeg":
        original_ext = ".jpg"

    if original_ext != actual_ext:
        messages.append(f"Warning: Extension mismatch. Renamed from {original_ext} to {actual_ext}.")

    if actual_ext in [".jpg", ".webp"]:
        if shutil.which("magick") is None:
            messages.append(
                "Warning: ImageMagick (magick) is required to convert this image to PNG during patching but is not found on your system."
            )
    elif actual_ext == ".mp4":
        if shutil.which("ffmpeg") is None:
            messages.append(
                "Warning: FFmpeg is required to convert this video to WEBM during patching but is not found on your system."
            )

    modal_shared.show(title="Background Selected", messages=messages, buttons=[{"label": "OK", "width": 100}])
