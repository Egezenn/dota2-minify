import os
import json
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse
from typing import Any, Dict, List, Optional

import webview
from core import base, config, constants, fs, output, utils

from ui.services import ConfigService, DialogService, ModService, PatchService, PluginService


class Api:
    def __init__(self) -> None:
        self._host_shutdown: Any = None
        self.patch_service = PatchService()
        self.mod_service = ModService()
        self.config_service = ConfigService()
        self.plugin_service = PluginService()
        self.dialog_service = DialogService()

    def set_window(self, window: Any) -> None:
        self.patch_service.set_window(window)

    def set_host_shutdown(self, callback: Any) -> None:
        self._host_shutdown = callback

    def shutdown_host(self) -> bool:
        if self._host_shutdown:
            self._host_shutdown()
        return True

    def start_patch(self) -> Dict[str, Any]:
        return self.patch_service.start_patch()

    def start_uninstall(self, remove_everything: bool = False) -> Dict[str, Any]:
        return self.patch_service.start_uninstall(remove_everything)

    def open_url(self, url: str) -> None:
        import webbrowser

        webbrowser.open(url)

    def open_config_directory(self) -> None:
        fs.open_thing(base.config_dir)

    def create_debug_zip(self) -> Dict[str, Any]:
        from core import log

        try:
            log.create_debug_zip()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_readme_content(self) -> Dict[str, Any]:
        try:
            readme_path = os.path.join(base.base_dir, "README.md")
            license_path = os.path.join(base.base_dir, "LICENSE")
            readme = ""
            license_text = ""
            if os.path.exists(readme_path):
                with open(readme_path, "r", encoding="utf-8") as f:
                    readme = f.read()
            if os.path.exists(license_path):
                with open(license_path, "r", encoding="utf-8") as f:
                    license_text = f.read()
            return {"success": True, "readme": readme, "license": license_text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def is_patching(self) -> bool:
        return self.patch_service.is_patching()

    def get_logs(self) -> List[Dict[str, Any]]:
        return self.patch_service.get_logs()

    def get_downloads(self) -> List[Dict[str, Any]]:
        return self.patch_service.get_downloads()

    def clear_logs(self) -> bool:
        return self.patch_service.clear_logs()

    def get_mods(self) -> List[Dict[str, Any]]:
        return self.mod_service.get_mods()

    def get_mod_details(self, mod_name: str, lang: str | None = None) -> Dict[str, Any]:
        return self.mod_service.get_mod_details(mod_name, lang)

    def set_mods(self, data: Dict[str, bool]) -> bool:
        return self.mod_service.set_mods(data)

    def get_available_languages(self) -> List[str]:
        return self.config_service.get_available_languages()

    def is_debug_env(self) -> bool:
        return self.config_service.is_debug_env()

    def get_version(self) -> str:
        return base.VERSION

    @staticmethod
    def is_portable() -> bool:
        if not base.FROZEN:
            return True
        return not os.path.exists(os.path.join(os.path.dirname(sys.executable), "unins000.exe"))

    def perform_update(self, url: str) -> bool:
        if not base.is_win or self.is_portable():
            import webbrowser

            webbrowser.open(base.github_io)
            return False

        import tempfile
        import threading
        import time

        from core import fs, log

        def _update_thread():
            temp_dir = os.environ.get("TEMP", os.environ.get("TMP", tempfile.gettempdir()))
            clean_url = url.split("?")[0]
            installer_name = clean_url.split("/")[-1] or "Minify-Setup.exe"
            installer_path = os.path.join(temp_dir, installer_name)

            output.add_text(f"Downloading update: {installer_name}...")
            success = fs.download_file(
                url=url,
                target_path=installer_path,
                name=installer_name,
                task_id="app-update",
                emit_progress=True,
            )
            if success and os.path.exists(installer_path):
                time.sleep(2)
                output.add_text("Launching installer and closing Minify...")
                try:
                    os.startfile(installer_path)
                except Exception as e:
                    log.write_crashlog(f"Failed to launch installer: {e}")
                    output.add_text(f"Failed to launch installer: {e}", msg_type="error")
                finally:
                    os._exit(0)
            else:
                output.add_text("Update download failed.", msg_type="error")

        threading.Thread(target=_update_thread, daemon=True).start()
        return True

    def get_localization(self, lang: str = "en") -> Dict[str, str]:
        return self.config_service.get_localization(lang)

    def get_current_locale(self) -> str:
        return self.config_service.get_current_locale()

    def set_locale(self, lang: str) -> bool:
        return self.config_service.set_locale(lang)

    def get_available_game_languages(self) -> List[str]:
        return self.config_service.get_available_game_languages()

    def get_current_game_language(self) -> str:
        return self.config_service.get_current_game_language()

    def set_game_language(self, lang: str) -> bool:
        return self.config_service.set_game_language(lang)

    def get_steam_accounts(self) -> List[Dict[str, Any]]:
        return self.config_service.get_steam_accounts()

    def get_settings(self) -> Dict[str, Any]:
        return self.config_service.get_settings()

    def set_setting(self, key: str, value: Any, mod_name: str | None = None) -> bool:
        return self.config_service.set_setting(key, value, mod_name)

    def run_mod_function(self, mod_name: str, function_name: str) -> bool:
        return self.config_service.run_mod_function(mod_name, function_name)

    def reset_native_settings(self) -> bool:
        return self.config_service.reset_native_settings()

    def reset_mod_settings(self, mod_name: str) -> bool:
        return self.config_service.reset_mod_settings(mod_name)

    def get_available_themes(self) -> List[Dict[str, str]]:
        return self.config_service.get_available_themes()

    def get_theme_css(self, theme_name: str | None = None) -> str:
        return self.config_service.get_theme_css(theme_name)

    def get_state(self, key: str, default: Any = None) -> Any:
        states = utils.read_states()
        return states.get(key, default)

    def set_state(self, key: str, value: Any) -> bool:
        utils.write_states(key, value)
        return True

    def check_workshop_tools_needed(self) -> bool:
        import conditions

        return base.is_linux and not constants.rescomp_override and conditions.workshop_installed

    def extract_workshop_tools(self) -> bool:
        import helper

        return helper.extract_workshop_tools()

    def get_legacy_mods(self) -> List[str]:
        backup_dirs = sorted(path for path in Path(base.base_dir).glob("mods_old_*") if path.is_dir())
        entries = []
        if backup_dirs:
            backup_dir = backup_dirs[-1]
            mods_dir = Path(base.mods_dir)
            entries.extend(
                f"{backup_dir.name}/{entry.name}"
                for entry in sorted(backup_dir.iterdir())
                if not (mods_dir / entry.name).exists()
            )
        return entries

    def import_legacy_mods(self, import_mods: bool = True) -> Dict[str, Any]:
        migrated = []
        discarded = []
        fs.create_dirs(base.mods_dir)
        backup_dirs = sorted(path for path in Path(base.base_dir).glob("mods_old_*") if path.is_dir())
        backup_dir = backup_dirs[-1] if backup_dirs else None
        if backup_dir:
            for source in sorted(backup_dir.iterdir()):
                destination = Path(base.mods_dir) / source.name
                try:
                    if not import_mods or destination.exists():
                        discarded.append(source.name)
                        fs.remove_path(str(source))
                    else:
                        shutil.move(str(source), str(destination))
                        migrated.append(source.name)
                except OSError:
                    discarded.append(source.name)
                    fs.remove_path(str(source))
            try:
                backup_dir.rmdir()
            except OSError:
                pass
            for stale_dir in backup_dirs[:-1]:
                fs.remove_path(str(stale_dir))
        return {"migrated": migrated, "discarded": discarded}

    def is_workshop_installed(self) -> bool:
        import conditions

        return bool(conditions.workshop_installed)

    def download_workshop_tools(self) -> bool:
        import tempfile
        import requests
        import conditions
        from core import fs, log

        repo_url = (
            "https://github.com/Dota-Modding-Community/workshoptools/releases/latest/download/resourcecompiler.zip"
        )
        api_url = "https://api.github.com/repos/Dota-Modding-Community/workshoptools/releases/latest"
        download_url = repo_url

        try:
            resp = requests.get(api_url, headers={"User-Agent": "dota2-minify"}, timeout=10)
            if resp.status_code == 200:
                assets = resp.json().get("assets", [])
                for asset in assets:
                    if asset.get("name", "").endswith(".zip"):
                        download_url = asset.get("browser_download_url", repo_url)
                        break
        except Exception as e:
            log.write_warning(f"Could not query GitHub API for workshoptools release: {e}")

        temp_dir = os.environ.get("TEMP", os.environ.get("TMP", tempfile.gettempdir()))
        zip_path = os.path.join(temp_dir, "workshoptools.zip")

        output.add_text(f"Downloading Workshop Tools from {download_url}...")
        success = fs.download_file(
            url=download_url,
            target_path=zip_path,
            name="workshoptools.zip",
            task_id="workshoptools",
            emit_progress=True,
        )
        if not success or not os.path.exists(zip_path):
            output.add_text("Failed to download Workshop Tools.", msg_type="error")
            return False

        output.add_text("Expanding Workshop Tools to config/rescomproot...")
        target_dir = base.rescomp_override_dir
        fs.create_dirs(target_dir)
        extract_success = fs.extract_archive(zip_path, target_dir)
        if not extract_success:
            output.add_text("Failed to extract Workshop Tools archive.", msg_type="error")
            return False

        inner_dir = os.path.join(target_dir, "resourcecompiler")
        if os.path.isdir(inner_dir):
            for item in os.listdir(inner_dir):
                src = os.path.join(inner_dir, item)
                dst = os.path.join(target_dir, item)
                if os.path.exists(dst):
                    fs.remove_path(dst)
                fs.move_path(src, dst)
            fs.remove_path(inner_dir)

        fs.remove_path(zip_path)

        constants.recalc_rescomp_dirs()

        if (base.is_linux or base.is_mac) and os.path.exists(constants.dota_resource_compiler_path):
            import stat

            st = os.stat(constants.dota_resource_compiler_path)
            os.chmod(
                constants.dota_resource_compiler_path,
                st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
            )

        compiler_exists = os.path.exists(constants.dota_resource_compiler_path)
        conditions.workshop_installed = compiler_exists

        if compiler_exists:
            output.add_text("Workshop Tools installed successfully!", msg_type="success")
            return True
        else:
            output.add_text(
                f"resourcecompiler.exe was not found at {constants.dota_resource_compiler_path}",
                msg_type="error",
            )
            return False

    def get_plugin_tabs(self) -> List[Dict[str, Any]]:
        return self.plugin_service.get_tabs(resolve_func=self._resolve_plugin_entry)

    def get_plugin_content(self, plugin_id: str) -> str:
        return self.plugin_service.get_content(plugin_id)

    def get_plugin_localization(self, plugin_id: str, lang: str = "en") -> Dict[str, str]:
        return self.plugin_service.get_localization(plugin_id, lang)

    def _resolve_plugin_entry(self, p_path: str) -> Optional[str]:
        return self.plugin_service._resolve_plugin_entry(p_path)

    def call_plugin_api(self, plugin_id: str, action: str, params: Dict[str, Any] = None) -> Any:
        return self.plugin_service.call_api(plugin_id, action, params)


def launch(host: bool = False) -> None:
    if not os.path.isfile(base.dist_index):
        output.add_text(
            f"Error: Web UI build file not found at '{base.dist_index}'. Please run 'npm run build' inside Minify/ui/web.",
            msg_type="error",
        )

    if host:
        _open_in_browser()
        return

    if base.is_win:
        os.environ.setdefault("WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS", "--disable-gpu")  # #186

    debug_mode = bool(config.get("debug_env"))
    webview.settings["OPEN_DEVTOOLS_IN_DEBUG"] = False
    webview.settings["ALLOW_FILE_URLS"] = True

    url = Path(base.dist_index).as_uri()

    states = utils.read_states()
    window_size = states.get("window_size", {}) if isinstance(states, dict) else {}
    initial_width = window_size.get("width", 960)
    initial_height = window_size.get("height", 680)

    if not isinstance(initial_width, int) or initial_width < 700:
        initial_width = 960
    if not isinstance(initial_height, int) or initial_height < 500:
        initial_height = 680

    api = Api()
    active_theme = config.get("theme", "light")
    theme_css = api.get_theme_css(active_theme)
    bg_color = api.config_service.extract_bg_color(theme_css)
    window = webview.create_window(
        title=base.TITLE,
        url=url,
        js_api=api,
        width=initial_width,
        height=initial_height,
        min_size=(700, 500),
        resizable=True,
        background_color=bg_color,
    )

    def _save_window_size(*args: Any, **kwargs: Any) -> None:
        w, h = None, None
        if len(args) >= 2:
            w, h = args[0], args[1]
        if w and h and isinstance(w, (int, float)) and isinstance(h, (int, float)):
            w_int, h_int = int(w), int(h)
            if w_int >= 700 and h_int >= 500:
                utils.write_states("window_size", {"width": w_int, "height": h_int})

    window.events.resized += _save_window_size

    # to prevent MSHTML
    if base.is_win and not is_webview2_installed():
        output.add_text("WebView2 not installed, opening in browser...", msg_type="warning")
        _open_in_browser()
        return

    webview_failed = False

    if base.is_win:
        try:
            from webview.platforms.edgechromium import EdgeChrome

            orig_on_ready = EdgeChrome.on_webview_ready

            def _patched_on_ready(self_ec: Any, sender: Any, args: Any) -> Any:
                nonlocal webview_failed
                if not getattr(args, "IsSuccess", True):
                    output.add_text(
                        f"WebView2 initialization failed ({getattr(args, 'InitializationException', 'unknown error')}), opening in browser...",
                        msg_type="warning",
                    )
                    webview_failed = True
                    try:
                        self_ec.form.Close()
                    except Exception:
                        pass
                    return
                return orig_on_ready(self_ec, sender, args)

            EdgeChrome.on_webview_ready = _patched_on_ready
        except Exception:
            pass

    api.set_window(window)
    try:
        webview.start(debug=debug_mode, icon=base.favicon_file)
    except Exception as e:
        output.add_text(f"WebView initialization failed, opening in browser: {e}", msg_type="warning")
        _open_in_browser()
        return

    if webview_failed:
        _open_in_browser()


def _find_app_browser() -> Optional[str]:
    candidates: List[str] = []
    if base.is_win:
        local = os.environ.get("LOCALAPPDATA", "")
        pf = os.environ.get("ProgramFiles", r"C:\Program Files")
        pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        candidates = [
            os.path.join(pf, "Chromium", "Application", "chrome.exe"),
            os.path.join(pf86, "Chromium", "Application", "chrome.exe"),
            os.path.join(local, "Chromium", "Application", "chrome.exe"),
            os.path.join(pf, "Helium", "Application", "helium.exe"),
            os.path.join(pf86, "Helium", "Application", "helium.exe"),
            os.path.join(local, "Helium", "Application", "helium.exe"),
            os.path.join(local, "Programs", "Helium", "helium.exe"),
            os.path.join(pf, "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
            os.path.join(local, "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
            os.path.join(pf, "Vivaldi", "Application", "vivaldi.exe"),
            os.path.join(pf86, "Vivaldi", "Application", "vivaldi.exe"),
            os.path.join(local, "Vivaldi", "Application", "vivaldi.exe"),
            os.path.join(pf, "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(pf86, "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(local, "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(pf86, "Microsoft", "Edge", "Application", "msedge.exe"),
            os.path.join(pf, "Microsoft", "Edge", "Application", "msedge.exe"),
            os.path.join(local, "Microsoft", "Edge", "Application", "msedge.exe"),
            os.path.join(pf, "Opera", "opera.exe"),
            os.path.join(local, "Programs", "Opera", "opera.exe"),
            os.path.join(pf, "Opera GX", "opera.exe"),
            os.path.join(local, "Programs", "Opera GX", "opera.exe"),
        ]
    elif base.is_mac:
        candidates = [
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Helium.app/Contents/MacOS/Helium",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            "/Applications/Vivaldi.app/Contents/MacOS/Vivaldi",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Opera.app/Contents/MacOS/Opera",
            "/Applications/Opera GX.app/Contents/MacOS/Opera GX",
        ]
    elif base.is_linux:
        for name in (
            "chromium",
            "chromium-browser",
            "helium",
            "helium-browser",
            "brave-browser",
            "vivaldi",
            "vivaldi-stable",
            "google-chrome",
            "google-chrome-stable",
            "microsoft-edge",
            "microsoft-edge-stable",
            "opera",
        ):
            path = shutil.which(name)
            if path:
                candidates.append(path)

    for path in candidates:
        if path and os.path.isfile(path):
            return path
    return None


def _resolve_browser_exe() -> Optional[str]:
    browser = config.get("browser_exec")
    if isinstance(browser, str) and browser.strip():
        exe = os.path.expanduser(browser.strip())
        candidates = [exe, shutil.which(exe)]
        original_cwd = getattr(base, "original_cwd", None)
        if original_cwd:
            candidates.append(os.path.join(original_cwd, exe))
        for candidate in candidates:
            if candidate and os.path.isfile(candidate):
                return candidate
        output.add_text(f"Browser not found at '{browser}', trying auto-detection...", msg_type="warning")
    return _find_app_browser()


def _launch_app_window(url: str) -> Optional[tuple[Any, str]]:
    exe = _resolve_browser_exe()
    if not exe:
        return None
    profile_dir = tempfile.mkdtemp(prefix="minify-browser-")
    try:
        process = subprocess.Popen(
            [
                exe,
                f"--app={url}",
                f"--user-data-dir={profile_dir}",
                "--window-size=960,680",
                "--no-first-run",
                "--no-default-browser-check",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        shutil.rmtree(profile_dir, ignore_errors=True)
        return None
    return process, profile_dir


def _open_in_browser() -> None:
    import webbrowser

    stop_event = threading.Event()
    api = Api()
    server = _start_local_server(os.path.dirname(base.dist_index), api)
    api.set_host_shutdown(lambda: _request_host_shutdown(stop_event, server))
    url = f"http://127.0.0.1:{server.server_port}/index.html"
    launch_result = _launch_app_window(url)
    app_window = launch_result[0] if launch_result else None
    profile_dir = launch_result[1] if launch_result else None
    if app_window is None and not webbrowser.open(url):
        _stop_local_server(server)
        return
    try:
        if app_window is not None:
            while app_window.poll() is None and not stop_event.is_set():
                stop_event.wait(0.5)
        else:
            stop_event.wait()
    except KeyboardInterrupt:
        pass
    finally:
        if app_window is not None and app_window.poll() is None:
            app_window.terminate()
            try:
                app_window.wait(timeout=5)
            except subprocess.TimeoutExpired:
                app_window.kill()
        if profile_dir:
            shutil.rmtree(profile_dir, ignore_errors=True)
        _stop_local_server(server)


def _request_host_shutdown(stop_event: threading.Event, server: ThreadingHTTPServer) -> None:
    stop_event.set()
    threading.Thread(target=_stop_local_server, args=(server,), daemon=True).start()


def _stop_local_server(server: ThreadingHTTPServer) -> None:
    server.shutdown()
    server.server_close()
    serve_thread = getattr(server, "_serve_thread", None)
    if serve_thread is not None and serve_thread is not threading.current_thread():
        serve_thread.join(timeout=5)


def _start_local_server(directory: str, api: Api) -> ThreadingHTTPServer:
    def _host_file_urls(value: Any) -> Any:
        if isinstance(value, str) and value.startswith("file://"):
            path = unquote(urlparse(value).path).replace("/", os.sep)
            if len(path) > 2 and path[0] == os.sep and path[2] == ":":
                path = path[1:]
            for root, prefix in ((base.themes_dir, "/themes/"), (base.plugins_dir, "/plugins/")):
                try:
                    relative = os.path.relpath(path, root)
                except ValueError:
                    continue
                if not relative.startswith(".."):
                    return prefix + relative.replace(os.sep, "/")
        if isinstance(value, list):
            return [_host_file_urls(item) for item in value]
        if isinstance(value, dict):
            return {key: _host_file_urls(item) for key, item in value.items()}
        return value

    class LocalHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, directory=directory, **kwargs)

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/favicon.ico":
                try:
                    with open(base.favicon_file, "rb") as favicon:
                        payload = favicon.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "image/x-icon")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except OSError:
                    self.send_error(404)
                return
            if parsed.path.startswith("/themes/"):
                self.path = unquote(parsed.path[len("/themes/") :])
                self.directory = base.themes_dir
            elif parsed.path.startswith("/plugins/"):
                self.path = unquote(parsed.path[len("/plugins/") :])
                self.directory = base.plugins_dir
            super().do_GET()

        def do_POST(self) -> None:
            if self.path != "/api":
                self.send_error(404)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                request = json.loads(self.rfile.read(length))
                method_name = request["method"]
                method = getattr(api, method_name)
                if method_name.startswith("_") or not callable(method):
                    raise ValueError("Invalid API method")
                result = method(*request.get("args", []), **request.get("kwargs", {}))
                result = _host_file_urls(result)
                payload = json.dumps({"result": result}).encode("utf-8")
                self.send_response(200)
            except Exception as error:
                payload = json.dumps({"error": str(error)}).encode("utf-8")
                self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    handler = LocalHandler
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    server.daemon_threads = True
    serve_thread = threading.Thread(target=server.serve_forever, daemon=False, name="minify-http-server")
    server._serve_thread = serve_thread
    serve_thread.start()
    return server


def is_webview2_installed() -> bool:
    candidate_dirs = [
        os.path.join(
            os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "Microsoft", "EdgeWebView", "Application"
        ),
        os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Microsoft", "EdgeWebView", "Application"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "EdgeWebView", "Application"),
    ]

    for base_dir in candidate_dirs:
        if not base_dir or not os.path.isdir(base_dir):
            continue
        try:
            for _, _, files in os.walk(base_dir):
                if "msedgewebview2.exe" in files:
                    return True
        except OSError:
            pass
    return False
