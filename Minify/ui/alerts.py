import json
from core import localization, output, utils


def alert(text_or_id, *args, msg_type="info", title=None, **kwargs):
    """Display a user-facing alert dialog box / notification in the UI with & localization support."""
    text = text_or_id
    if isinstance(text_or_id, str) and text_or_id.startswith("&"):
        text = localization.localization_dict.get(text_or_id.replace("&", ""), text_or_id)

    if args and isinstance(text, str):
        text = text.format(*args)

    title = title or ("Error" if msg_type == "error" else "Warning" if msg_type == "warning" else "Notice")

    output.add_text(text_or_id, *args, msg_type=msg_type, **kwargs)

    with utils.try_pass():
        import webview

        if webview.windows:
            window = webview.windows[0]
            formatted_msg = f"[{title}] {text}" if title else text
            js_msg = json.dumps(formatted_msg)
            window.evaluate_js(f"alert({js_msg});")
            return

    with utils.try_pass():
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", 1)
        if msg_type == "error":
            messagebox.showerror(title, text)
        elif msg_type == "warning":
            messagebox.showwarning(title, text)
        else:
            messagebox.showinfo(title, text)
        root.destroy()
