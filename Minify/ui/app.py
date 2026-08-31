import os
from typing import Any, Dict, List, Optional

import webview
from core import base, config, output, utils

from ui.services import ConfigService, DialogService, ModService, PatchService, PluginService


class Api:
    def __init__(self) -> None:
        self.patch_service = PatchService()
        self.mod_service = ModService()
        self.config_service = ConfigService()
        self.plugin_service = PluginService()
        self.dialog_service = DialogService()

    def set_window(self, window: Any) -> None:
        self.patch_service.set_window(window)

    def start_patch(self) -> Dict[str, Any]:
        return self.patch_service.start_patch()

    def start_uninstall(self, remove_everything: bool = False) -> Dict[str, Any]:
        return self.patch_service.start_uninstall(remove_everything)

    def is_patching(self) -> bool:
        return self.patch_service.is_patching()

    def get_logs(self) -> List[Dict[str, Any]]:
        return self.patch_service.get_logs()

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

    def get_localization(self, lang: str = "EN") -> Dict[str, str]:
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

    def get_plugin_tabs(self) -> List[Dict[str, Any]]:
        return self.plugin_service.get_tabs(resolve_func=self._resolve_plugin_entry)

    def get_plugin_content(self, plugin_id: str) -> str:
        return self.plugin_service.get_content(plugin_id)

    def _resolve_plugin_entry(self, p_path: str) -> Optional[str]:
        return self.plugin_service._resolve_plugin_entry(p_path)

    def call_plugin_api(self, plugin_id: str, action: str, params: Dict[str, Any] = None) -> Any:
        return self.plugin_service.call_api(plugin_id, action, params)


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
    _apply_tiling_wm_floating_hints()

    url = base.dist_index
    if not os.path.isfile(url):
        output.add_text(
            f"Error: Web UI build file not found at '{url}'. Please run 'npm run build' inside Minify/ui/web.",
            msg_type="error",
        )

    debug_mode = bool(config.get("debug_env"))
    webview.settings["OPEN_DEVTOOLS_IN_DEBUG"] = False
    webview.settings["ALLOW_FILE_URLS"] = True

    states = utils.read_states()
    window_size = states.get("window_size", {}) if isinstance(states, dict) else {}
    initial_width = window_size.get("width", 960)
    initial_height = window_size.get("height", 680)

    if not isinstance(initial_width, int) or initial_width < 700:
        initial_width = 960
    if not isinstance(initial_height, int) or initial_height < 500:
        initial_height = 680

    api = Api()
    window = webview.create_window(
        title=base.TITLE,
        url=url,
        js_api=api,
        width=initial_width,
        height=initial_height,
        min_size=(700, 500),
        resizable=True,
    )

    def _save_window_size(*args: Any, **kwargs: Any) -> None:
        w = getattr(window, "width", None)
        h = getattr(window, "height", None)
        if w is None and len(args) >= 2:
            w, h = args[0], args[1]
        if w and h and isinstance(w, (int, float)) and isinstance(h, (int, float)):
            w_int, h_int = int(w), int(h)
            if w_int >= 700 and h_int >= 500:
                utils.write_states("window_size", {"width": w_int, "height": h_int})

    window.events.resized += _save_window_size
    window.events.closing += _save_window_size

    api.set_window(window)
    webview.start(debug=debug_mode)
