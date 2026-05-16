"Agnostic output interface"

_output_callback = None
_separator_callback = None
_clean_callback = None


def register_output_callback(callback):
    global _output_callback
    _output_callback = callback


def register_separator_callback(callback):
    global _separator_callback
    _separator_callback = callback


def register_clean_callback(callback):
    global _clean_callback
    _clean_callback = callback


def add_text(text_or_id, *args, msg_type: str | None = None, **kwargs):
    if _output_callback:
        return _output_callback(text_or_id, *args, msg_type=msg_type, **kwargs)

    # Fallback to console if no callback registered
    from ui import localization

    text = text_or_id
    if text_or_id.startswith("&"):
        text = localization.localization_dict.get(text_or_id.replace("&", ""), text_or_id)

    if args:
        text = text.format(*args)

    prefix = ""
    if msg_type == "error":
        prefix = "[ERROR] "
    elif msg_type == "warning":
        prefix = "[WARNING] "
    elif msg_type == "success":
        prefix = "[SUCCESS] "

    try:
        print(f"{prefix}{text}")
    except UnicodeEncodeError:
        print(f"{prefix}{text.encode('ascii', 'replace').decode('ascii')}")
    return None


def add_separator():
    if _separator_callback:
        _separator_callback()
    else:
        print("-" * 50)


def clean():
    if _clean_callback:
        _clean_callback()
