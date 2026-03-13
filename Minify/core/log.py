import os
import traceback

from . import base


def write_crashlog(exc_type=None, exc_value=None, exc_traceback=None, header=None, handled=True):
    from helper import add_text_to_terminal, create_debug_zip

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
        add_text_to_terminal(message, type="error")
    if base.FROZEN:
        create_debug_zip()


def write_warning(header=None):
    from helper import add_text_to_terminal

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
        add_text_to_terminal(message, type="warning")


def unhandled_handler(handled=False):
    def handler(exc_type, exc_value, exc_traceback):
        return write_crashlog(exc_type, exc_value, exc_traceback, handled=handled)

    return handler
