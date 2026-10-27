import importlib.util
import os
import sys
import threading
import types
from typing import Any, Dict, List, Optional

from core import base, config, mods_shared, utils


PLUGIN_TAB_NAVIGATION_SCRIPT = """
<script>
  window.addEventListener("keydown", function (event) {
    if (event.ctrlKey && event.key === "Tab") {
      event.preventDefault();
      event.stopPropagation();
      window.parent.postMessage({ type: "CYCLE_TAB", forward: !event.shiftKey }, "*");
    }
  });
</script>
"""


class PluginService:
    def __init__(self) -> None:
        self._lock = threading.Lock()

    @staticmethod
    def _resolve_plugin_entry(p_path: str) -> Optional[str]:
        target = os.path.abspath(os.path.join(p_path, "ui", "index.html"))
        return target if os.path.isfile(target) else None

    @staticmethod
    def _find_plugin_path(plugin_id: str) -> Optional[str]:
        plugins_dir = base.plugins_dir
        direct_path = os.path.join(plugins_dir, plugin_id)
        direct_manifest = os.path.join(direct_path, "manifest.json")
        if os.path.isdir(direct_path) and not os.path.isfile(direct_manifest):
            return direct_path
        if os.path.isdir(direct_path) and os.path.isfile(direct_manifest):
            manifest = config.read_json_file(direct_manifest)
            if isinstance(manifest, dict) and manifest.get("id") == plugin_id:
                return direct_path

        if os.path.isdir(plugins_dir):
            for folder in sorted(os.listdir(plugins_dir)):
                if mods_shared.is_ignored_folder(folder):
                    continue
                p_path = os.path.join(plugins_dir, folder)
                manifest_path = os.path.join(p_path, "manifest.json")
                if not os.path.isdir(p_path) or not os.path.isfile(manifest_path):
                    continue
                manifest = config.read_json_file(manifest_path)
                if isinstance(manifest, dict) and manifest.get("id") == plugin_id:
                    return p_path
        return None

    def get_tabs(self, resolve_func=None) -> List[Dict[str, Any]]:
        tabs = []
        resolve = resolve_func or self._resolve_plugin_entry
        plugins_dir = base.plugins_dir
        if os.path.exists(plugins_dir):
            for p_name in sorted(os.listdir(plugins_dir)):
                if mods_shared.is_ignored_folder(p_name):
                    continue
                p_path = os.path.join(plugins_dir, p_name)
                manifest_path = os.path.join(p_path, "manifest.json")
                if os.path.isfile(manifest_path):
                    manifest = config.read_json_file(manifest_path)
                    if isinstance(manifest, dict) and "id" in manifest and "name" in manifest:
                        abs_entry = resolve(p_path)
                        if abs_entry and os.path.isfile(abs_entry):
                            entry_url = utils.path_to_uri(abs_entry)
                            tabs.append(
                                {
                                    "id": manifest["id"],
                                    "name": manifest["name"],
                                    "entry_point": entry_url,
                                }
                            )
        return tabs

    def get_content(self, plugin_id: str) -> str:
        p_path = self._find_plugin_path(plugin_id)
        if p_path:
            abs_entry = self._resolve_plugin_entry(p_path)
            if abs_entry and os.path.isfile(abs_entry):
                with open(abs_entry, "r", encoding="utf-8") as f:
                    content = f.read()
                from ui.services.config_service import ConfigService

                cs = ConfigService()
                theme_css = cs.get_theme_css(config.get("theme", "light"))
                base_css = cs.get_base_css()
                content = cs.inject_theme_into_content(content, theme_css, base_css)
                head_close = content.rfind("</head>")
                if head_close != -1:
                    return content[:head_close] + PLUGIN_TAB_NAVIGATION_SCRIPT + content[head_close:]
                return PLUGIN_TAB_NAVIGATION_SCRIPT + content
        return ""

    def get_localization(self, plugin_id: str, lang: str = "en") -> Dict[str, str]:
        from core import localization

        p_path = self._find_plugin_path(plugin_id)
        folder = os.path.basename(p_path) if p_path else plugin_id
        return localization.get_for_plugin(folder, lang)

    def call_api(self, plugin_id: str, action: str, params: Dict[str, Any] = None) -> Any:
        p_path = self._find_plugin_path(plugin_id)
        if not p_path:
            raise FileNotFoundError(f"Plugin directory for '{plugin_id}' was not found.")

        api_file = os.path.join(p_path, "api.py")
        if not os.path.isfile(api_file):
            api_file = os.path.join(p_path, "build_hook.py")

        if not os.path.isfile(api_file):
            raise FileNotFoundError(f"No API file (api.py or build_hook.py) found for plugin '{plugin_id}'.")

        mod_name = f"plugins.{plugin_id}.{os.path.splitext(os.path.basename(api_file))[0]}"
        mod = None
        with self._lock:
            package_name = f"plugins.{plugin_id}"
            package = sys.modules.get(package_name)
            if package is None:
                package = types.ModuleType(package_name)
                package.__path__ = [p_path]
                package.__package__ = package_name
                sys.modules[package_name] = package
            elif p_path not in getattr(package, "__path__", []):
                package.__path__ = [p_path]
            if mod_name in sys.modules and sys.modules[mod_name] is not None:
                mod = sys.modules[mod_name]
            else:
                spec = importlib.util.spec_from_file_location(mod_name, api_file)
                if spec and spec.loader:
                    new_mod = importlib.util.module_from_spec(spec)
                    new_mod.__package__ = f"plugins.{plugin_id}"
                    try:
                        spec.loader.exec_module(new_mod)
                        sys.modules[mod_name] = new_mod
                        mod = new_mod
                    except Exception:
                        sys.modules.pop(mod_name, None)
                        raise

        if mod:
            if hasattr(mod, "handle_api"):
                return mod.handle_api(action, params or {})
            elif hasattr(mod, action):
                return getattr(mod, action)(params or {})
            else:
                raise AttributeError(f"Action '{action}' not found in plugin module '{mod_name}'.")
        else:
            raise ImportError(f"Failed to load plugin module '{mod_name}' from '{api_file}'.")
