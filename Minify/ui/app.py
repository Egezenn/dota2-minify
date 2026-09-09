import os
from pathlib import Path
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

    def get_theme_url(self, theme_name: str | None = None) -> str:
        return self.config_service.get_theme_url(theme_name)

    def get_theme_css(self, theme_name: str | None = None) -> str:
        return self.config_service.get_theme_css(theme_name)

    def is_theme_initialized(self) -> bool:
        states = utils.read_states()
        return bool(states.get("system_theme_init"))

    def set_theme_initialized(self) -> bool:
        utils.write_states("system_theme_init", True)
        return True

    def get_plugin_tabs(self) -> List[Dict[str, Any]]:
        return self.plugin_service.get_tabs(resolve_func=self._resolve_plugin_entry)

    def get_plugin_content(self, plugin_id: str) -> str:
        return self.plugin_service.get_content(plugin_id)

    def _resolve_plugin_entry(self, p_path: str) -> Optional[str]:
        return self.plugin_service._resolve_plugin_entry(p_path)

    def call_plugin_api(self, plugin_id: str, action: str, params: Dict[str, Any] = None) -> Any:
        return self.plugin_service.call_api(plugin_id, action, params)


def launch() -> None:
    if not os.path.isfile(base.dist_index):
        output.add_text(
            f"Error: Web UI build file not found at '{base.dist_index}'. Please run 'npm run build' inside Minify/ui/web.",
            msg_type="error",
        )

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

    api.set_window(window)
    webview.start(debug=debug_mode, icon=base.favicon_file)
