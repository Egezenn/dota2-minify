"Agnostic output interface"

RED = "\033[38;2;255;0;0m"
YELLOW = "\033[38;2;255;255;0m"
GREEN = "\033[38;2;0;255;0m"
RESET = "\033[0m"


_listeners = []
_download_listeners = []


def register_listener(callback):
    if callback not in _listeners:
        _listeners.append(callback)


def unregister_listener(callback):
    if callback in _listeners:
        _listeners.remove(callback)


def register_download_listener(callback):
    if callback not in _download_listeners:
        _download_listeners.append(callback)


def unregister_download_listener(callback):
    if callback in _download_listeners:
        _download_listeners.remove(callback)


def emit_download_progress(
    task_id: str, name: str, downloaded_bytes: int, total_bytes: int, status: str, error: str | None = None
):
    data = {
        "id": task_id,
        "name": name,
        "downloaded_bytes": downloaded_bytes,
        "total_bytes": total_bytes,
        "status": status,
        "error": error,
    }
    for listener in list(_download_listeners):
        try:
            listener(data)
        except Exception:
            pass


def add_text(text_or_id, *args, msg_type: str | None = None, **kwargs):
    from core import localization

    text = text_or_id
    if text_or_id.startswith("&"):
        text = localization.localization_dict.get(text_or_id.replace("&", ""), text_or_id)

    if args:
        text = text.format(*args)

    prefix = ""
    if msg_type == "error":
        prefix = f"{RED}"
    elif msg_type == "warning":
        prefix = f"{YELLOW}"
    elif msg_type == "success":
        prefix = f"{GREEN}"

    try:
        print(f"{prefix}{text}{RESET}")
    except UnicodeEncodeError:
        print(f"{prefix}{text.encode('ascii', 'replace').decode('ascii')}{RESET}")

    for listener in list(_listeners):
        listener(text, msg_type)

    return None


def add_separator():
    print("-" * 50)
    for listener in list(_listeners):
        listener("", "separator")
