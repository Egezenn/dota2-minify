import os
import time
import traceback
import zipfile

from core import base


def write_crashlog(exc_type=None, exc_value=None, exc_traceback=None, header=None, handled=True):
    from ui.terminal import add_text_to_terminal

    path = base.log_crashlog if handled else base.log_unhandled
    with open(path, "w") as file:
        if handled:
            if header:
                file.write(message := f"{header}\n\n{traceback.format_exc()}")
            else:
                file.write(message := traceback.format_exc())
        else:
            file.write(message := f"{''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))}")
    if message:
        add_text_to_terminal(message, msg_type="error")
    if base.FROZEN:
        create_debug_zip()


def write_warning(header=None):
    from ui.terminal import add_text_to_terminal

    if not os.path.exists(base.log_warnings):
        open(base.log_warnings, "w").close()

    with open(base.log_warnings, "a") as file:
        if "NoneType: None" not in traceback.format_exc():
            if header:
                file.write(message := f"{header}\n\n{traceback.format_exc()}\n{'-' * 50}\n\n")
            else:
                file.write(message := traceback.format_exc() + f"\n{'-' * 50}\n\n")
        else:
            file.write(message := f"{header}\n{'-' * 50}\n\n")
    if message:
        add_text_to_terminal(message, msg_type="warning")


def unhandled_handler(handled=False):
    def handler(exc_type, exc_value, exc_traceback):
        return write_crashlog(exc_type, exc_value, exc_traceback, handled=handled)

    return handler


def create_debug_zip():
    from core import fs
    from ui import terminal

    try:
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

        terminal.add_text_to_terminal("&heeeeeeeeeeeeeelp", zip_filename)
        fs.open_thing(".")

    except:
        pass
