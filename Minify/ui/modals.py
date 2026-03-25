"Modal types"

import re
import webbrowser

import build
import dearpygui.dearpygui as dpg
import requests
from core import base, config, utils

from ui import announcements, modal_shared

# TODO: translations


class Announcements:
    @staticmethod
    def show(announcement):
        modal_shared.show(
            title="Announcement",
            messages=[announcement.get("text", "")],
            buttons=[
                {
                    "label": "OK",
                    "callback": lambda s, a, u: Announcements.callback(s, a, u),
                    "user_data": announcement,
                    "width": 120,
                },
                {
                    "label": "Ignore",
                    "callback": lambda s, a, u: Announcements.callback(s, a, u),
                    "user_data": announcement,
                    "width": 120,
                },
            ],
        )

    @staticmethod
    def callback(sender, app_data, user_data):
        action = "OK" if dpg.get_item_label(sender) == "OK" else "Ignore"
        announcements.handle_announcement_action(user_data, action)

    @staticmethod
    def check():
        pending = announcements.get_pending_announcements()
        for ann in pending:
            Announcements.show(ann)


class Uninstall:
    @staticmethod
    def show():
        modal_shared.show(
            title="Uninstall",
            messages=["Remove all mods?"],
            buttons=[
                {"label": "Confirm", "callback": lambda s, a, u: build.uninstaller(s, a, u), "width": 100},
                {"label": "Cancel", "callback": lambda s, a, u: Uninstall.hide(s, a, u), "width": 100},
            ],
        )

    @staticmethod
    def hide(sender=None, app_data=None, user_data=None):
        pass


class Update:
    @staticmethod
    def show(version):
        modal_shared.show(
            title="Update",
            messages=["New update is available!", f"Version {version} is available. Would you like to update?"],
            buttons=[
                {"label": "Yes", "callback": lambda s, a, u: webbrowser.open(base.github_io), "width": 120},
                {"label": "Ignore update", "callback": lambda s, a, u: Update.delete(True, version), "width": 120},
                {"label": "No", "callback": lambda s, a, u: Update.delete(False), "width": 120},
            ],
        )

    @staticmethod
    def delete(ignore, version=None):
        if ignore and version:
            config.set("ignore_update", version)

    @staticmethod
    def check():
        if base.FROZEN:
            with utils.try_pass():
                api_url = f"https://api.github.com/repos/{base.OWNER}/{base.REPO}/releases"

                response = requests.get(api_url)
                response.raise_for_status()
                releases = response.json()

                download_url = None
                tag_name = None

                suffix = base.OS.lower() + ".zip"

                if suffix:
                    opt_in = config.get("opt_into_rcs", False)
                    for release in releases:
                        if release["prerelease"] and not re.search(r"rc\d+$", base.VERSION) and not opt_in:
                            continue  # Show only if the current version is a pre-release
                        for asset in release.get("assets", []):
                            if asset["name"].endswith(suffix):
                                download_url = asset["browser_download_url"]
                                tag_name = release["tag_name"]
                                break
                        if download_url:
                            break
                if download_url and tag_name:
                    remote_version = tag_name[8:] if len(tag_name) > 8 else tag_name
                    if base.VERSION != remote_version:
                        if config.get("ignore_update") == remote_version:
                            return
