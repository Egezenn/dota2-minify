# ui.modals

Modal types

## `Announcements()`

*No documentation available.*

<details open><summary>Source</summary>

```python
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

```

</details>

## `Uninstall()`

*No documentation available.*

<details open><summary>Source</summary>

```python
class Uninstall:
    @staticmethod
    def show():
        modal_shared.show(
            title="Uninstall",
            messages=["Remove all mods?"],
            buttons=[
                {"label": "Confirm", "callback": lambda s, a, u: build.uninstall(s, a, u), "width": 100},
                {"label": "Cancel", "callback": lambda s, a, u: Uninstall.hide(s, a, u), "width": 100},
            ],
        )

    @staticmethod
    def hide(sender=None, app_data=None, user_data=None):
        pass

```

</details>

## `Update()`

*No documentation available.*

<details open><summary>Source</summary>

```python
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
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                downloaded += len(chunk)
                                f.write(chunk)
                                progress = downloaded / total_length
                                mb_downloaded = downloaded / (1024 * 1024)
                                mb_total = total_length / (1024 * 1024)
                                modal_shared.set_progress(
                                    progress, f"Progress: {mb_downloaded:.1f}MB / {mb_total:.1f}MB"
                                )
                                time.sleep(1)

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

```

</details>
