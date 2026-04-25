"Crashlogs, warnings and debug zip creation"

import os
import time
import traceback
import zipfile

from core import base, utils


def write_crashlog(exc_type=None, exc_value=None, exc_traceback=None, header=None, handled=True):
    from ui import terminal

    path = base.log_crashlog if handled else base.log_unhandled
    with utils.open_utf8R(path, "w") as file:
        if handled:
            if header:
                file.write(message := f"{header}\n\n{traceback.format_exc()}")
            else:
                file.write(message := traceback.format_exc())
        else:
            file.write(message := f"{''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))}")

    with utils.try_pass():
        from ui import terminal

        if message and not handled:
            terminal.add_text(message, msg_type="error")
    if base.FROZEN:
        create_debug_zip()


def write_warning(header=None):
    from ui import terminal

    if not os.path.exists(base.log_warnings):
        with utils.open_utf8R(base.log_warnings, "w") as file:
            pass

    console_message = ""
    with utils.open_utf8R(base.log_warnings, "a") as file:
        if "NoneType: None" not in traceback.format_exc():
            if header:
                console_message = f"{header}\n\n{traceback.format_exc()}"
            else:
                console_message = traceback.format_exc()
        else:
            console_message = f"{header}"

        file.write(f"{console_message}\n{'-' * 50}\n\n")

    if console_message:
        terminal.add_text(console_message, msg_type="warning")


def unhandled_handler(handled=False):
    def handler(exc_type, exc_value, exc_traceback):
        return write_crashlog(exc_type, exc_value, exc_traceback, handled=handled)

    return handler


def create_debug_zip():
    from core import fs

    with utils.try_pass():
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        zip_filename = f"minify_debug_{timestamp}.zip"

        files_to_include = [
            base.main_config_file_dir,
            base.mods_config_dir,
        ]

        if os.path.exists(base.logs_dir):
            for file in os.listdir(base.logs_dir):
                files_to_include.append(os.path.join(base.logs_dir, file))

        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in files_to_include:
                if os.path.exists(file_path):
                    zipf.write(file_path)

        with utils.try_pass():
            from ui import terminal

            terminal.add_text("&heeeeeeeeeeeeeelp", zip_filename)
        fs.open_thing(".")
