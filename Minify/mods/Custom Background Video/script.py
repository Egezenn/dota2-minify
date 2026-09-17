import os
import shutil
import subprocess
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
mod_name = os.path.basename(current_dir)
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
if os.getcwd() != minify_root:
    os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

# isort: split

import conditions
from core import base, constants, fs, output


def main():
    source_file = None
    vid_extensions = (".mp4", ".webm")

    for ext in vid_extensions:
        p = os.path.join(base.config_dir, f"background{ext}")
        if os.path.exists(p):
            actual_ext = fs.get_file_type(p)

            if not actual_ext:
                output.add_text("Unsupported background video format\n   {}", p, msg_type="error", indent=True)
                return

            if actual_ext != ext:
                new_p = os.path.join(base.config_dir, f"background{actual_ext}")
                output.add_text("Background extension mismatch\n   {} -> {}", p, new_p, msg_type="warning", indent=True)
                fs.move_path(p, new_p)
                return

            source_file = p
            break

    if not source_file:
        return

    if conditions.workshop_installed:
        target_file = (
            os.path.join(base.config_dir, "_background.webm") if not source_file.endswith(".webm") else source_file
        )
        if target_file != source_file:
            if (ffmpeg_path := shutil.which("ffmpeg")) is not None:
                subprocess.run(
                    [
                        ffmpeg_path,
                        "-y",
                        "-i",
                        source_file,
                        "-c:v",
                        "libvpx-vp9",
                        "-pix_fmt",
                        "yuv420p",
                        "-deadline",
                        "realtime",
                        "-cpu-used",
                        "4",
                        "-threads",
                        "0",
                        "-an",
                        target_file,
                    ],
                    creationflags=subprocess.CREATE_NO_WINDOW if base.is_win else 0,
                )
            else:
                output.add_text(
                    "Conversion tools missing\n   {} ({})",
                    "FFmpeg",
                    f"{actual_ext} -> .webm",
                    msg_type="error",
                    indent=True,
                )
                return

        if target_file.endswith(".webm") and os.path.exists(target_file):
            fs.create_dirs(
                compile_location := os.path.join(constants.minify_dota_compile_output_path, "panorama", "videos"),
            )
            shutil.copy(target_file, os.path.join(compile_location, "background.webm"))
            if target_file != source_file:
                fs.remove_path(target_file)
