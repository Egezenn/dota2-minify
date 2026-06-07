"Modal types"

import os
import re
import threading
import time
import webbrowser

import dearpygui.dearpygui as dpg
import patch
import requests
from core import base, config, fs, log, utils

from ui import announcements, modal_shared, shared

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
                {
                    "label": "Confirm",
                    "callback": lambda s, a, u: threading.Thread(
                        target=patch.unins.uninstall, args=(s, a, u), daemon=True
                    ).start(),
                    "width": 100,
                },
                {"label": "Cancel", "callback": lambda s, a, u: Uninstall.hide(s, a, u), "width": 100},
            ],
        )

    @staticmethod
    def hide(sender=None, app_data=None, user_data=None):
        pass


class WorkshopTools:
    _watcher_thread = None

    @staticmethod
    def show():
        config.set("workshop_modal_shown", True)
        if base.OS == base.WIN:
            modal_shared.show(
                title="Workshop Tools Not Found",
                messages=[
                    "Dota 2 Workshop Tools are not installed.",
                    "Some mods require them and have been disabled.",
                    "Would you like to install them now?",
                ],
                buttons=[
                    {
                        "label": "Yes",
                        "callback": lambda s, a, u: WorkshopTools._handle_yes(),
                        "width": 100,
                    },
                    {"label": "No", "width": 100},
                ],
            )
        else:
            modal_shared.show(
                title="Workshop Tools Not Found",
                messages=[
                    "Dota 2 Workshop Tools are not installed.",
                    "Some mods require them and have been disabled.",
                    "Click OK to go to the related wiki section.",
                ],
                buttons=[
                    {
                        "label": "OK",
                        "callback": lambda s, a, u: webbrowser.open(
                            "https://egezenn.github.io/dota2-minify/wiki/#/troubleshooting_faq?id=workshop-tools-dlc"
                        ),
                        "width": 100,
                    },
                    {"label": "No", "width": 100},
                ],
            )

    @staticmethod
    def _handle_yes():
        webbrowser.open(f"steam://install/{base.STEAM_DOTA_WORKSHOP_TOOLS_ID}")
        WorkshopTools._start_watcher()

    @staticmethod
    def _start_watcher():
        if WorkshopTools._watcher_thread and WorkshopTools._watcher_thread.is_alive():
            return

        def watch():
            import conditions
            from core import output

            from ui import checkboxes, gui

            while gui.gui_lock:
                time.sleep(0.1)

            was_downloading = False

            while True:
                app_state = conditions.get_dota_app_state()
                is_enabled = conditions.get_workshop_tools_status(app_state)
                try:
                    state_flags = int(app_state.get("StateFlags", 0))
                except (ValueError, TypeError):
                    state_flags = 0
                is_installed = bool(state_flags & 4) and is_enabled

                if is_installed:
                    break

                downloading = is_enabled and (
                    not (state_flags & 4)
                    or base.STEAM_DOTA_WORKSHOP_TOOLS_ID in app_state.get("DlcDownloads", {})
                )

                if downloading and not was_downloading:
                    output.add_text("Downloading Dota 2 Workshop Tools...", msg_type="warning")
                    gui.lock_interaction()
                    was_downloading = True
                elif not downloading and was_downloading:
                    gui.unlock_interaction()
                    was_downloading = False

                time.sleep(1)

            if was_downloading:
                gui.unlock_interaction()

            conditions.is_compiler_found()
            checkboxes.refresh()
            modal_shared.show(
                title="Workshop Tools Ready",
                messages=["Dota 2 Workshop Tools detected!", "Workshop mods have been enabled."],
                buttons=[{"label": "OK", "width": 80}],
            )

        WorkshopTools._watcher_thread = threading.Thread(target=watch, daemon=True)
        WorkshopTools._watcher_thread.start()


class Update:
    @staticmethod
    def show(version):
        modal_shared.show(
            title="Update",
            messages=["New update is available!", f"Version {version} is available. Would you like to update?"],
            buttons=[
                {"label": "Yes", "callback": lambda s, a, u: Update.perform_update(), "width": 120},
                {"label": "Ignore update", "callback": lambda s, a, u: Update.delete(True, version), "width": 120},
                {"label": "No", "callback": lambda s, a, u: Update.delete(False), "width": 120},
            ],
        )

    @staticmethod
    def is_portable():
        import sys

        if not base.FROZEN:
            return True
        return not os.path.exists(os.path.join(os.path.dirname(sys.executable), "unins000.exe"))

    @staticmethod
    def perform_update():
        if base.OS != base.WIN or not shared.update_url or Update.is_portable():
            webbrowser.open(base.github_io)
            fs.open_thing(".")
            return

        def download_thread():
            url = shared.update_url
            try:
                temp_dir = os.environ.get("TEMP", os.environ.get("TMP", "."))
                installer_name = url.split("/")[-1]
                installer_path = os.path.join(temp_dir, installer_name)

                response = requests.get(url, stream=True)
                response.raise_for_status()
                total_length = response.headers.get("content-length")

                modal_shared.show_progress(["Downloading update...", f"File: {installer_name}"])

                downloaded = 0
                with open(installer_path, "wb") as f:
                    if total_length is None:  # no content length header
                        f.write(response.content)
                        modal_shared.set_progress(1.0, "Download complete!")
                    else:
                        total_length = int(total_length)
                        last_report_time = 0
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                downloaded += len(chunk)
                                f.write(chunk)

                                current_time = time.time()
                                if current_time - last_report_time >= 0.1:
                                    progress = downloaded / total_length
                                    mb_downloaded = downloaded / (1024 * 1024)
                                    mb_total = total_length / (1024 * 1024)
                                    modal_shared.set_progress(
                                        progress, f"Progress: {mb_downloaded:.1f}MB / {mb_total:.1f}MB"
                                    )
                                    last_report_time = current_time

                # Launch installer and exit
                modal_shared.set_progress(1.0, "Launching installer...")
                time.sleep(0.5)
                os.startfile(installer_path)
                os._exit(0)
            except Exception as e:
                log.write_crashlog(f"Update failed: {e}")
                modal_shared.show("Error", ["Update failed to download.", str(e)], [{"label": "OK", "width": 120}])
                webbrowser.open(base.github_io)
            fs.open_thing(".")

        threading.Thread(target=download_thread, daemon=True).start()

    @staticmethod
    def delete(ignore, version=None):
        if ignore and version:
            config.set("ignore_update", version)

    @staticmethod
    def check():
        if base.FROZEN or config.get("debug_env", False):
            with utils.try_pass():
                if config.get("debug_env", False):
                    api_url = "http://localhost:8000/releases_mock.json"
                else:
                    api_url = f"https://api.github.com/repos/{base.OWNER}/{base.REPO}/releases"

                response = requests.get(api_url)
                response.raise_for_status()
                releases = response.json()

                download_url = None
                tag_name = None

                suffix = ".exe" if base.OS == base.WIN else ".zip"

                if suffix:
                    opt_in = config.get("opt_into_rcs", False)
                    debug = config.get("debug_env", False)
                    for release in releases:
                        if (
                            release["prerelease"]
                            and not re.search(r"rc\d+$", base.VERSION)
                            and not opt_in
                            and not debug
                        ):
                            continue  # Show only if the current version is a pre-release or in debug mode
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
                        if config.get("ignore_update") == remote_version and not debug:
                            return
                        shared.update_url = download_url
                        Update.show(remote_version)
