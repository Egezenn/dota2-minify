import os
import json
import shutil
import sys
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

    if host:
        _open_in_browser()
        return

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
        print("WebView2 not installed, opening in browser...")
        _open_in_browser()
        return

    api.set_window(window)
    try:
        webview.start(debug=debug_mode, icon=base.favicon_file)
    except Exception as e:
        if base.is_win and not is_webview2_installed():
            print(e)
            _open_in_browser()
            return
        raise


def _open_in_browser() -> None:
    import webbrowser

    stop_event = threading.Event()
    api = Api()
    server = _start_local_server(os.path.dirname(base.dist_index), api)
    api.set_host_shutdown(lambda: _request_host_shutdown(stop_event, server))
    url = f"http://127.0.0.1:{server.server_port}/index.html"
    if not webbrowser.open(url):
        _stop_local_server(server)
        return
    try:
        stop_event.wait()
    except KeyboardInterrupt:
        pass
    finally:
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


