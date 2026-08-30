import base64
import json
import os
import re
import sys

import threading
import time
from typing import Any, Dict, List, Optional


import helper
import patch
import webview
from core import base, config, constants, localization, mods_shared, output, utils


class Api:
    def __init__(self) -> None:
        self._window: Any = None
        self._is_patching: bool = False
        self._logs: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

        output.register_listener(self._on_output_log)
        output.register_download_listener(self._on_download_progress)

    def set_window(self, window: Any) -> None:
        self._window = window

    def _on_download_progress(self, data: Dict[str, Any]) -> None:
        if self._window:
            try:
                js_str = json.dumps(data)
                self._window.evaluate_js(f"window.onDownloadProgress && window.onDownloadProgress({js_str});")
            except Exception:
                pass

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

    @staticmethod
    def _get_mod_preview(mod_path: str) -> str | None:
        if not os.path.isdir(mod_path):
            return None
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
                        return f"data:{mime_type};base64,{encoded}"
                except Exception as e:
                    output.add_text(
                        f"Error loading preview image for {os.path.basename(mod_path)}: {e}", msg_type="warning"
                    )
        return None

    def get_mods(self) -> List[Dict[str, Any]]:
        try:
            mods_shared.scan_mods()
            from patch import manifest_utils

            mod_list = mods_shared.visually_available_mods
            mods_data = []
            for mod in mod_list:
                mod_path = os.path.join(base.mods_dir, mod)
                always = False
                if os.path.isdir(mod_path):
                    cfg = manifest_utils.get_mod(mod_path)
                    always = bool(cfg.get("always", False))
                preview = self._get_mod_preview(mod_path)
                mods_data.append(
                    {
                        "name": mod,
                        "enabled": always or mods_shared.get_state(mod),
                        "always": always,
                        "preview": preview,
                    }
                )
            return mods_data
        except Exception as e:
            output.add_text(f"get_mods error: {e}", msg_type="error")
            return []

    def get_mod_details(self, mod_name: str, lang: str | None = None) -> Dict[str, Any]:
        try:
            if not lang:
                lang = config.get("locale") or "EN"
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

            preview_data_url = self._get_mod_preview(mod_path)

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
            from patch import manifest_utils

            for mod_name, enabled in data.items():
                mod_path = os.path.join(base.mods_dir, mod_name)
                if os.path.isdir(mod_path):
                    cfg = manifest_utils.get_mod(mod_path)
                    if cfg.get("always", False):
                        continue
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
            return bool(config.get("debug_env"))
        except Exception:
            return False

    def get_localization(self, lang: str = "EN") -> Dict[str, str]:
        try:
            if not lang:
                lang = config.get("locale") or "EN"
            return localization.get_for_locale(lang) or {}
        except Exception:
            return {}

    def get_current_locale(self) -> str:
        try:
            return config.get("locale") or "EN"
        except Exception:
            return "EN"

    def set_locale(self, lang: str) -> bool:
        try:
            config.set("locale", lang)
            localization.load_headless()
            return True
        except Exception:
            return False

    def get_available_game_languages(self) -> List[str]:
        try:
            return constants.minify_output_list
        except Exception:
            return ["english"]

    def get_current_game_language(self) -> str:
        try:
            return config.get("output_locale", "english")
        except Exception:
            return "english"

    def set_game_language(self, lang: str) -> bool:
        try:
            config.set("output_locale", lang)
            helper.sync_output_path()
            mods_shared.enforce_locale_mod_states()
            return True
        except Exception:
            return False

    def _parse_setting_item(
        self, item: dict, mod_folder: str | None = None, plugin_folder: str | None = None
    ) -> Dict[str, Any] | None:
        if not isinstance(item, dict):
            return None
        key = item.get("key")
        stype = item.get("type")
        if not key or not stype:
            return None

        stype_str = str(stype).lower()
        default_val = item.get("default")
        if default_val is None:
            if stype_str == "checkbox":
                default_val = False
            elif stype_str in ("inputbox", "text", "color"):
                default_val = ""
            elif stype_str in ("number", "slider"):
                default_val = item.get("min", 0)
            elif stype_str == "list":
                default_val = []
            elif stype_str == "combo":
                items = item.get("items", [])
                default_val = items[0] if items else ""

        schema_entry = {
            "key": key,
            "text": item.get("text", key),
            "type": stype_str,
            "default": default_val,
        }

        if mod_folder:
            schema_entry["mod"] = mod_folder
        if plugin_folder:
            schema_entry["plugin"] = plugin_folder
        if "force" in item:
            schema_entry["force"] = bool(item["force"])

        if stype_str == "combo":
            schema_entry["items"] = item.get("items", [])
        elif stype_str in ("number", "slider"):
            vtype = item.get("var_type")
            if not vtype:
                vtype = "float" if isinstance(default_val, float) else "int"
            schema_entry["var_type"] = vtype
            schema_entry["step"] = item.get("step", 0.1 if vtype == "float" else 1)
            if "min" in item:
                schema_entry["min"] = item["min"]
            elif stype_str == "slider":
                schema_entry["min"] = 0
            if "max" in item:
                schema_entry["max"] = item["max"]
            elif stype_str == "slider":
                schema_entry["max"] = 100

        return schema_entry

    def get_settings(self) -> Dict[str, Any]:
        try:
            mods_shared.scan_mods()
            from patch import manifest_utils

            settings_json_path = os.path.join(base.bin_dir, "settings.json")
            native_schema = config.read_json_file(settings_json_path)
            if not isinstance(native_schema, list):
                native_schema = []

            settings_schema = []
            values = {}

            for item in native_schema:
                parsed = self._parse_setting_item(item)
                if parsed:
                    settings_schema.append(parsed)
                    values[parsed["key"]] = config.get(parsed["key"], parsed["default"])

            if os.path.exists(base.mods_dir):
                for mod_folder in sorted(os.listdir(base.mods_dir)):
                    if mod_folder.startswith((".", "_")):
                        continue
                    mod_path = os.path.join(base.mods_dir, mod_folder)
                    if not os.path.isdir(mod_path):
                        continue

                    cfg = manifest_utils.get_mod(mod_path)
                    mod_settings_list = cfg.get("settings")
                    if not isinstance(mod_settings_list, list):
                        continue

                    always = bool(cfg.get("always", False))
                    mod_enabled = always or mods_shared.get_state(mod_folder)

                    for item in mod_settings_list:
                        force = bool(item.get("force", False)) if isinstance(item, dict) else False
                        if not (force or mod_enabled):
                            continue

                        parsed = self._parse_setting_item(item, mod_folder=mod_folder)
                        if parsed:
                            mod_store = config.get_mod(mod_folder, {})
                            cur_val = mod_store.get(parsed["key"], parsed["default"])
                            values[parsed["key"]] = cur_val
                            settings_schema.append(parsed)

            # Plugin manifest settings discovery
            plugins_dir = base.plugins_dir
            if os.path.exists(plugins_dir):
                for plugin_folder in sorted(os.listdir(plugins_dir)):
                    if plugin_folder.startswith((".", "_")):
                        continue
                    plugin_path = os.path.join(plugins_dir, plugin_folder)
                    if not os.path.isdir(plugin_path):
                        continue

                    manifest_path = os.path.join(plugin_path, "manifest.json")
                    if os.path.isfile(manifest_path):
                        try:
                            manifest = config.read_json_file(manifest_path)
                            if isinstance(manifest, dict):
                                plugin_settings_list = manifest.get("settings")
                                if isinstance(plugin_settings_list, list):
                                    for item in plugin_settings_list:
                                        parsed = self._parse_setting_item(item, plugin_folder=plugin_folder)
                                        if parsed:
                                            settings_schema.append(parsed)
                                            values[parsed["key"]] = config.get(parsed["key"], parsed["default"])
                        except Exception as e:
                            output.add_text(f"Error reading plugin manifest {manifest_path}: {e}", msg_type="warning")

            return {"schema": settings_schema, "values": values}
        except Exception as e:
            output.add_text(f"get_settings error: {e}", msg_type="error")
            return {"schema": [], "values": {}}

    def set_setting(self, key: str, value: Any, mod_name: str | None = None) -> bool:
        try:
            if mod_name:
                modconf = config.get_mod(mod_name, {})
                modconf[key] = value
                config.set_mod(mod_name, modconf)
            else:
                config.set(key, value)
            return True
        except Exception as e:
            output.add_text(f"set_setting error for {key}: {e}", msg_type="error")
            return False

    def run_mod_function(self, mod_name: str, function_name: str) -> bool:
        try:
            mod_path = os.path.join(base.mods_dir, mod_name)
            script_path = os.path.join(mod_path, "script_utility.py")
            if not os.path.exists(script_path):
                output.add_text(f"script_utility.py not found for mod '{mod_name}'", msg_type="warning")
                return False
            helper.exec_script_function(script_path, mod_name, function_name)
            return True
        except Exception as e:
            output.add_text(f"run_mod_function error ({mod_name}.{function_name}): {e}", msg_type="error")
            return False

    def reset_native_settings(self) -> bool:
        try:
            settings_json_path = os.path.join(base.bin_dir, "settings.json")
            native_schema = config.read_json_file(settings_json_path)
            if isinstance(native_schema, list):
                for item in native_schema:
                    if isinstance(item, dict) and "key" in item and "default" in item:
                        config.set(item["key"], item["default"])
            return True
        except Exception as e:
            output.add_text(f"reset_native_settings error: {e}", msg_type="error")
            return False

    def reset_mod_settings(self, mod_name: str) -> bool:
        try:
            modconf = config.get("modconf", {})
            if isinstance(modconf, dict) and mod_name in modconf:
                modconf.pop(mod_name, None)
                config.set("modconf", modconf)
            return True
        except Exception as e:
            output.add_text(f"reset_mod_settings error for {mod_name}: {e}", msg_type="error")
            return False

    def _resolve_plugin_entry(self, p_path: str) -> Optional[str]:
        target = os.path.abspath(os.path.join(p_path, "ui", "index.html"))
        return target if os.path.isfile(target) else None

    def get_plugin_tabs(self) -> List[Dict[str, Any]]:
        tabs = []
        try:
            plugins_dir = base.plugins_dir
            if os.path.exists(plugins_dir):
                for p_name in sorted(os.listdir(plugins_dir)):
                    p_path = os.path.join(plugins_dir, p_name)
                    manifest_path = os.path.join(p_path, "manifest.json")
                    if os.path.isfile(manifest_path):
                        try:
                            manifest = config.read_json_file(manifest_path)
                            if isinstance(manifest, dict) and "id" in manifest and "name" in manifest:
                                abs_entry = self._resolve_plugin_entry(p_path)
                                if abs_entry and os.path.isfile(abs_entry):
                                    entry_url = (
                                        f"file://{abs_entry}"
                                        if not base.is_win
                                        else f"file:///{abs_entry.replace('\\', '/')}"
                                    )
                                    tabs.append(
                                        {
                                            "id": manifest["id"],
                                            "name": manifest["name"],
                                            "entry_point": entry_url,
                                        }
                                    )

                        except Exception as e:
                            output.add_text(f"Error reading plugin manifest {manifest_path}: {e}", msg_type="warning")
        except Exception as e:
            output.add_text(f"get_plugin_tabs error: {e}", msg_type="error")
        return tabs

    def get_plugin_content(self, plugin_id: str) -> str:
        try:
            plugins_dir = base.plugins_dir
            p_path = os.path.join(plugins_dir, plugin_id)
            manifest_path = os.path.join(p_path, "manifest.json")
            if os.path.isfile(manifest_path):
                manifest = config.read_json_file(manifest_path)
                abs_entry = self._resolve_plugin_entry(p_path)
                if abs_entry and os.path.isfile(abs_entry):
                    with open(abs_entry, "r", encoding="utf-8") as f:
                        content = f.read()

                    plugin_dir = os.path.dirname(abs_entry)

                    def _inline_file(match, attr_name: str, template: str) -> str:
                        url = match.group(attr_name)
                        if url.startswith(("http://", "https://", "data:", "//")):
                            return match.group(0)
                        file_path = os.path.normpath(os.path.join(plugin_dir, url.lstrip("./")))
                        if os.path.isfile(file_path):
                            with open(file_path, "r", encoding="utf-8") as f:
                                return template.format(f.read())
                        return match.group(0)

                    content = re.sub(
                        r'<link\s+[^>]*?href=["\'](?P<url>[^"\']+)["\'][^>]*?>',
                        lambda m: _inline_file(m, "url", "<style>\n{}\n</style>"),
                        content,
                        flags=re.IGNORECASE,
                    )
                    content = re.sub(
                        r'<script\s+[^>]*?src=["\'](?P<url>[^"\']+)["\'][^>]*?>\s*</script>',
                        lambda m: _inline_file(m, "url", '<script type="module">\n{}\n</script>'),
                        content,
                        flags=re.IGNORECASE,
                    )
                    return content
        except Exception as e:
            output.add_text(f"get_plugin_content error: {e}", msg_type="error")
        return ""

    def call_plugin_api(self, plugin_id: str, action: str, params: Dict[str, Any] = None) -> Any:
        try:
            import importlib.util

            plugins_dir = base.plugins_dir
            p_path = os.path.join(plugins_dir, plugin_id)
            if not os.path.isdir(p_path):
                return {"error": f"Plugin '{plugin_id}' not found on disk."}

            api_file = os.path.join(p_path, "api.py")
            if not os.path.isfile(api_file):
                api_file = os.path.join(p_path, "build_hook.py")

            mod = None
            if os.path.isfile(api_file):
                mod_name = f"plugins.{plugin_id}.{os.path.splitext(os.path.basename(api_file))[0]}"
                if mod_name in sys.modules:
                    mod = sys.modules[mod_name]
                else:
                    spec = importlib.util.spec_from_file_location(
                        mod_name, api_file, submodule_search_locations=[p_path]
                    )
                    if spec and spec.loader:
                        mod = importlib.util.module_from_spec(spec)
                        sys.modules[mod_name] = mod
                        spec.loader.exec_module(mod)

            if mod:
                if hasattr(mod, "handle_api"):
                    return mod.handle_api(action, params or {})
                elif hasattr(mod, action):
                    return getattr(mod, action)(params or {})
        except Exception as e:
            output.add_text(f"call_plugin_api error ({plugin_id}.{action}): {e}", msg_type="error")
            return {"error": str(e)}
        return {"error": f"Action '{action}' not handled by plugin '{plugin_id}'."}


def _apply_tiling_wm_floating_hints() -> None:
    if not base.is_linux:
        return

    # GTK platform
    with utils.try_pass():
        import gi

        gi.require_version("Gtk", "3.0")
        gi.require_version("Gdk", "3.0")
        import webview.platforms.gtk as gtk_platform
        from gi.repository import Gdk, Gtk

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
    with utils.try_pass():
        import webview.platforms.qt as qt_platform

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

    _apply_tiling_wm_floating_hints()

    url = base.dist_index
    if not os.path.isfile(url):
        output.add_text(
            f"Error: Web UI build file not found at '{url}'. Please run 'npm run build' inside Minify/ui/web.",
            msg_type="error",
        )

    debug_mode = bool(config.get("debug_env"))
    webview.settings["OPEN_DEVTOOLS_IN_DEBUG"] = False

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
