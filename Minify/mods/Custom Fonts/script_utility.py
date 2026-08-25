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


def select_font():
    title = "Select Custom Font File"
    file_types = ("Font Files (*.ttf;*.otf)", "All Files (*.*)")
    file_path = ui.pick_file(title, file_types)
    if not file_path:
        return

    ext = os.path.splitext(file_path)[1].lower()
    allowed_exts = [".ttf", ".otf"]

    if not ext or ext not in allowed_exts:
        ui.alert(
            f"Unsupported Format: Selected file must be a TrueType or OpenType font file (.ttf, .otf). Detected extension: {ext}",
            msg_type="error",
        )
        return

    fs.create_dirs(base.config_dir)

    for old_ext in allowed_exts:
        old_font = os.path.join(base.config_dir, f"font{old_ext}")
        if os.path.exists(old_font):
            with utils.try_pass():
                fs.remove_path(old_font)

    dest_path = os.path.join(base.config_dir, f"font{ext}")

    try:
        shutil.copy2(file_path, dest_path)
    except Exception as e:
        ui.alert(f"Error copying font file: {e}", msg_type="error")
        return

    ui.alert(f"Successfully copied font to {os.path.basename(dest_path)} in config/.", msg_type="success")
