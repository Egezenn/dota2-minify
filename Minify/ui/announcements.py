import time
import webbrowser

import jsonc
import requests
from core import base, config


def parse_time_condition(time_str):
    """
    Parses time condition strings:
    - "timestamp" (just an identifier, no timing conditions)
    - "timestamp-" (expiry: show if current <= timestamp)
    - "timestamp+" (after: show if current >= timestamp)
    - "t1=t2" (range: show if t1 <= current <= t2, t1 will be saved to seen)
    """
    current_time = int(time.time())

    if "-" in time_str:
        ts = int(time_str.replace("-", ""))
        return current_time <= ts
    elif "+" in time_str:
        ts = int(time_str.replace("+", ""))
        return current_time >= ts
    elif "=" in time_str:
        parts = time_str.split("=")
        if len(parts) == 2:
            t1 = int(parts[0])
            t2 = int(parts[1])
            return t1 <= current_time <= t2
    else:
        # Just an identifier, always true for the condition itself
        # Persistence check happens elsewhere
        return True


def check_version(versions_str, current_version):
    if not versions_str:
        return True

    allowed_versions = [v.strip() for v in versions_str.split(",")]
    return current_version in allowed_versions


def fetch_remote_announcements():
    """
    Fetches announcements from the github.io repository.
    """
    # Testing URL pointing to local server
    url = f"{base.github_io}/announcements.json"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return jsonc.loads(response.text)
    except:
        return []


def get_pending_announcements():
    """
    Returns a list of announcements that should be shown.
    Only active in frozen mode (compiled executable).
    """
    if not base.FROZEN:
        return []

    announcements = fetch_remote_announcements()
    if not announcements:
        return []

    seen = config.get_config("announcements_seen", [])
    current_version = base.VERSION

    pending = []
    for ann in announcements:
        time_cond = ann.get("time")
        text = ann.get("text")

        if not time_cond or not text:
            continue

        # Identifier is the timestamp part
        identifier = time_cond.replace("-", "").replace("+", "").split("=")[0]

        if identifier in seen:
            continue

        if not parse_time_condition(time_cond):
            continue

        versions = ann.get("versions")
        if not check_version(versions, current_version):
            continue

        pending.append(ann)

    return pending


def mark_as_seen(identifier):
    seen = config.get_config("announcements_seen", [])
    if identifier not in seen:
        seen.append(identifier)
        config.set_config("announcements_seen", seen)


def handle_announcement_action(announcement, action):
    "action: 'OK' or 'Ignore'"
    time_cond = announcement.get("time")
    identifier = time_cond.replace("-", "").replace("+", "").split("=")[0]

    if action == "OK":
        url = announcement.get("url")
        if url:
            webbrowser.open(url)

    mark_as_seen(identifier)
