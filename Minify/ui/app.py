import base64
import json
import os
import threading
import time
from typing import Any, Dict, List

from core import base, constants, localization, mods_shared, output, utils
from core import config as _config

import webview

import browsers
import helper
import patch


class Api:
    def __init__(self) -> None:
        self._window: Any = None
        self._is_patching: bool = False
        self._logs: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

        output.register_listener(self._on_output_log)

    def set_window(self, window: Any) -> None:
        self._window = window

    def _on_output_log(self, text: str, msg_type: str | None) -> None:
        log_entry = {
            "text": text,
            "type": msg_type or "info",
            "timestamp": time.strftime("%H:%M:%S"),
        }
        with self._lock:
            self._logs.append(log_entry)

        if self._window:
            try:
                js_str = json.dumps(log_entry)
                self._window.evaluate_js(f"window.onLogReceived && window.onLogReceived({js_str});")
            except Exception:
                pass

    def start_patch(self) -> Dict[str, Any]:
        if self._is_patching:
            return {"status": "already_running"}

        self._is_patching = True
        if self._window:
            try:
                self._window.evaluate_js("window.onPatchStatusChange && window.onPatchStatusChange(true);")
            except Exception:
                pass

        def run_patch_thread() -> None:
            try:
                patch.patcher()
            except Exception as e:
                output.add_text(f"Patch failed: {e}", msg_type="error")
            finally:
                self._is_patching = False
                if self._window:
                    try:
                        self._window.evaluate_js("window.onPatchStatusChange && window.onPatchStatusChange(false);")
                    except Exception:
                        pass

        threading.Thread(target=run_patch_thread, daemon=True).start()
        return {"status": "started"}

    def is_patching(self) -> bool:
        return self._is_patching

    def get_logs(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._logs)

    def clear_logs(self) -> bool:
        with self._lock:
            self._logs.clear()
        return True

    def get_mods(self) -> List[Dict[str, Any]]:
        try:
            mods_shared.scan_mods()
            mod_list = mods_shared.visually_available_mods or mods_shared.mods_alphabetical
            return [{"name": mod, "enabled": mods_shared.get_state(mod)} for mod in mod_list]
        except Exception as e:
            output.add_text(f"get_mods error: {e}", msg_type="error")
            return []

    def get_mod_details(self, mod_name: str, lang: str | None = None) -> Dict[str, Any]:
        try:
            if not lang:
                lang = _config.get("locale") or "EN"
            mod_path = os.path.join(base.mods_dir, mod_name)
            if not os.path.isdir(mod_path):
                return {
                    "name": mod_name,
                    "notes": None,
                    "preview": None,
                    "has_notes": False,
                    "has_preview": False,
                }

            notes_path = os.path.join(mod_path, "notes.md")
            notes_content = None
            if os.path.exists(notes_path):
                try:
                    with utils.open_utf8(notes_path) as f:
                        raw_notes = f.read()
                    notes_content = self._parse_notes_for_locale(raw_notes, lang)
                except Exception as e:
                    output.add_text(f"Error reading notes for {mod_name}: {e}", msg_type="warning")

            preview_data_url = None
            if os.path.exists(mod_path):
                for filename in os.listdir(mod_path):
                    if filename.lower() in (
                        "preview.jpg",
                        "preview.jpeg",
                        "preview.png",
                        "preview.webp",
                        "preview.gif",
                    ):
                        p_path = os.path.join(mod_path, filename)
                        try:
                            ext = filename.lower().rsplit(".", 1)[-1]
                            mime_type = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
                            with open(p_path, "rb") as img_file:
                                encoded = base64.b64encode(img_file.read()).decode("utf-8")
                                preview_data_url = f"data:{mime_type};base64,{encoded}"
                            break
                        except Exception as e:
                            output.add_text(f"Error loading preview image for {mod_name}: {e}", msg_type="warning")

            return {
                "name": mod_name,
                "notes": notes_content,
                "preview": preview_data_url,
                "has_notes": bool(notes_content),
                "has_preview": bool(preview_data_url),
            }
        except Exception as e:
            output.add_text(f"get_mod_details error: {e}", msg_type="error")
            return {
                "name": mod_name,
                "notes": None,
                "preview": None,
                "has_notes": False,
                "has_preview": False,
            }

    @staticmethod
    def _parse_notes_for_locale(notes_text: str, lang: str) -> str:
        if not notes_text or "<!-- LANG:" not in notes_text:
            return notes_text.strip()

        sections: Dict[str, str] = {}
        current_lang: str | None = None
        lines: List[str] = []

        for line in notes_text.splitlines():
            trimmed = line.strip()
            if trimmed.startswith("<!-- LANG:") and trimmed.endswith("-->"):
                if current_lang:
                    sections[current_lang] = "\n".join(lines).strip()
                current_lang = trimmed[10:-3].strip().upper()
                lines = []
            else:
                lines.append(line)
        if current_lang:
            sections[current_lang] = "\n".join(lines).strip()

        target_lang = (lang or "EN").upper()
        if target_lang in sections:
            return sections[target_lang]
        elif "EN" in sections:
            return sections["EN"]
        elif sections:
            return next(iter(sections.values()))

        return notes_text.strip()

    def set_mods(self, data: Dict[str, bool]) -> bool:
        try:
            for mod_name, enabled in data.items():
                mods_shared.set_state(mod_name, bool(enabled))
            return True
        except Exception:
            return False

    def get_available_languages(self) -> List[str]:
        try:
            return localization.get_available() or ["EN"]
        except Exception:
            return ["EN"]

    def is_debug_env(self) -> bool:
        try:
            return bool(_config.get("debug_env"))
        except Exception:
            return False

    def get_localization(self, lang: str = "EN") -> Dict[str, str]:
        try:
            if not lang:
                lang = _config.get("locale") or "EN"
            return localization.get_for_locale(lang) or {}
        except Exception:
            return {}

    def get_current_locale(self) -> str:
        try:
            return _config.get("locale") or "EN"
        except Exception:
            return "EN"

    def set_locale(self, lang: str) -> bool:
        try:
            _config.set("locale", lang)
            localization.load_headless()
            return True
        except Exception:
            return False

    def get_available_game_languages(self) -> List[str]:
        try:
            return constants.minify_output_list or ["english"]
        except Exception:
            return ["english"]

    def get_current_game_language(self) -> str:
        try:
            return _config.get("output_locale") or "english"
        except Exception:
            return "english"

    def set_game_language(self, lang: str) -> bool:
        try:
            _config.set("output_locale", lang)
            return True
        except Exception:
            return False

    def get_settings(self) -> Dict[str, Any]:
        settings_schema = [
            {
                "key": "opt_into_rcs",
                "text": "Opt into RCs",
                "default": _config.DEFAULT_SETTINGS["opt_into_rcs"],
                "type": "checkbox",
            },
            {
                "key": "fix_options",
                "text": "Handle language option (current ID)",
                "default": _config.DEFAULT_SETTINGS["fix_options"],
                "type": "checkbox",
            },
            {
                "key": "patch_on_launch",
                "text": "Run patches upon launch if required",
                "default": _config.DEFAULT_SETTINGS["patch_on_launch"],
                "type": "checkbox",
            },
            {
                "key": "apply_for_all",
                "text": "Apply everything for all users",
                "default": _config.DEFAULT_SETTINGS["apply_for_all"],
                "type": "checkbox",
            },
            {
                "key": "launch_dota_after_patch",
                "text": "Launch Dota2 after patching",
                "default": _config.DEFAULT_SETTINGS["launch_dota_after_patch"],
                "type": "checkbox",
            },
            {
                "key": "kill_self_after_patch",
                "text": "Close Minify after patching",
                "default": _config.DEFAULT_SETTINGS["kill_self_after_patch"],
                "type": "checkbox",
            },
            {
                "key": "opt_out_vpk_metadata",
                "text": "Opt-out of VPK metadata",
                "default": _config.DEFAULT_SETTINGS["opt_out_vpk_metadata"],
                "type": "checkbox",
            },
        ]
        values = {item["key"]: _config.get(item["key"]) for item in settings_schema}
        return {"schema": settings_schema, "values": values}

    def set_setting(self, key: str, value: Any) -> bool:
        try:
            _config.set(key, value)
            return True
        except Exception:
            return False


def _apply_tiling_wm_floating_hints() -> None:
    if not base.is_linux:
        return

    # GTK platform
    with utils.try_pass:
        import gi

        gi.require_version("Gtk", "3.0")
        gi.require_version("Gdk", "3.0")
        from gi.repository import Gdk, Gtk
        import webview.platforms.gtk as gtk_platform

        orig_gtk_init = gtk_platform.BrowserView.__init__

        def patched_gtk_init(self: Any, window: Any) -> None:
            orig_gtk_init(self, window)
            if isinstance(self.window, Gtk.Window):
                try:
                    dummy_parent = Gtk.Window()
                    dummy_parent.realize()
                    self.window.set_transient_for(dummy_parent)
                except Exception:
                    pass
                self.window.set_type_hint(Gdk.WindowTypeHint.DIALOG)
                self.window.set_role("dialog")
                self.window.set_modal(True)
                try:
                    self.window.set_wmclass("Minify", "Minify")
                except Exception:
                    pass

        gtk_platform.BrowserView.__init__ = patched_gtk_init

    # Qt platform
    with utils.try_pass:
        import webview.platforms.qt as qt_pBlatform

        orig_qt_init = qt_platform.BrowserView.__init__

        def patched_qt_init(self: Any, window: Any) -> None:
            orig_qt_init(self, window)
            try:
                from PyQt5.QtCore import Qt

                self.window.setWindowFlags(self.window.windowFlags() | Qt.Dialog | Qt.Tool)
            except Exception:
                pass

        qt_platform.BrowserView.__init__ = patched_qt_init


def launch() -> None:
    base.HEADLESS = False

    os.makedirs("cache", exist_ok=True)
    os.makedirs("config", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    localization.load_headless()
    utils.setup_system()
    browsers.initialize()
    helper.bulk_exec_script("initial", False)

    _apply_tiling_wm_floating_hints()

    ui_dir = os.path.dirname(os.path.abspath(__file__))
    dist_index = os.path.join(ui_dir, "web", "dist", "index.html")
    url = dist_index

    debug_mode = bool(_config.get("debug_env"))

    api = Api()
    window = webview.create_window(
        title=base.TITLE,
        url=url,
        js_api=api,
        width=960,
        height=680,
        min_size=(700, 500),
        resizable=True,
    )
    api.set_window(window)
    webview.start(debug=debug_mode)
