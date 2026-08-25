import os

from core import utils


def pick_file(title="Select File", file_types=(), initial_dir=None):
    """Open a dialog to select a single file."""
    initial_dir = initial_dir or os.getcwd()
    with utils.try_pass():
        import webview

        if webview.windows:
            window = webview.windows[0]
            result = window.create_file_dialog(
                dialog_type=webview.OPEN_DIALOG,
                directory=initial_dir,
                allow_multiple=False,
                file_types=tuple(file_types),
            )
            if result and len(result) > 0:
                return result[0]

    with utils.try_pass():
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", 1)
        file_path = filedialog.askopenfilename(
            title=title,
            initialdir=initial_dir,
        )
        root.destroy()
        return file_path or None

    return None


def pick_files(title="Select Files", file_types=(), initial_dir=None):
    """Open a dialog to select multiple files."""
    initial_dir = initial_dir or os.getcwd()
    with utils.try_pass():
        import webview

        if webview.windows:
            window = webview.windows[0]
            result = window.create_file_dialog(
                dialog_type=webview.OPEN_DIALOG,
                directory=initial_dir,
                allow_multiple=True,
                file_types=tuple(file_types),
            )
            if result:
                return list(result)

    with utils.try_pass():
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", 1)
        files = filedialog.askopenfilenames(
            title=title,
            initialdir=initial_dir,
        )
        root.destroy()
        return list(files) if files else []

    return []


def pick_folder(title="Select Folder", initial_dir=None):
    """Open a dialog to select a directory/folder."""
    initial_dir = initial_dir or os.getcwd()
    with utils.try_pass():
        import webview

        if webview.windows:
            window = webview.windows[0]
            result = window.create_file_dialog(
                dialog_type=webview.FOLDER_DIALOG,
                directory=initial_dir,
            )
            if result and len(result) > 0:
                return result[0]

    with utils.try_pass():
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", 1)
        folder_path = filedialog.askdirectory(
            title=title,
            initialdir=initial_dir,
        )
        root.destroy()
        return folder_path or None

    return None


def pick_save_file(title="Save File", default_filename="", file_types=(), initial_dir=None):
    """Open a dialog to choose a file save location."""
    initial_dir = initial_dir or os.getcwd()
    with utils.try_pass():
        import webview

        if webview.windows:
            window = webview.windows[0]
            result = window.create_file_dialog(
                dialog_type=webview.SAVE_DIALOG,
                directory=initial_dir,
                save_filename=default_filename,
                file_types=tuple(file_types),
            )
            if result:
                return result if isinstance(result, str) else result[0]

    with utils.try_pass():
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", 1)
        save_path = filedialog.asksaveasfilename(
            title=title,
            initialfile=default_filename,
            initialdir=initial_dir,
        )
        root.destroy()
        return save_path or None

    return None
