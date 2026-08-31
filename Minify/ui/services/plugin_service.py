import os
import sys
import threading
from typing import Any, Dict, List, Optional

from core import base, config, mods_shared, output, utils


class PluginService:
    def __init__(self) -> None:
        self._lock = threading.Lock()

    @staticmethod
    def _resolve_plugin_entry(p_path: str) -> Optional[str]:
        target = os.path.abspath(os.path.join(p_path, "ui", "index.html"))
        return target if os.path.isfile(target) else None

    def get_tabs(self, resolve_func=None) -> List[Dict[str, Any]]:
        tabs = []
        resolve = resolve_func or self._resolve_plugin_entry
        try:
            plugins_dir = base.plugins_dir
            if os.path.exists(plugins_dir):
                for p_name in sorted(os.listdir(plugins_dir)):
                    if mods_shared.is_ignored_folder(p_name):
                        continue
                    p_path = os.path.join(plugins_dir, p_name)
                    manifest_path = os.path.join(p_path, "manifest.json")
                    if os.path.isfile(manifest_path):
                        try:
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

                        except Exception as e:
                            output.add_text(f"Error reading plugin manifest {manifest_path}: {e}", msg_type="warning")
        except Exception as e:
            output.add_text(f"get_plugin_tabs error: {e}", msg_type="error")
        return tabs

    def get_content(self, plugin_id: str) -> str:
        try:
            plugins_dir = base.plugins_dir
            p_path = os.path.join(plugins_dir, plugin_id)
            manifest_path = os.path.join(p_path, "manifest.json")
            if os.path.isfile(manifest_path):
                abs_entry = self._resolve_plugin_entry(p_path)
                if abs_entry and os.path.isfile(abs_entry):
                    with open(abs_entry, "r", encoding="utf-8") as f:
                        return f.read()
        except Exception as e:
            output.add_text(f"get_plugin_content error: {e}", msg_type="error")
        return ""

    def call_api(self, plugin_id: str, action: str, params: Dict[str, Any] = None) -> Any:
        try:
            import importlib.util

            plugins_dir = base.plugins_dir
            p_path = os.path.join(plugins_dir, plugin_id)
            if not os.path.isdir(p_path):
                return {"error": f"Plugin directory for '{plugin_id}' not found on disk at '{p_path}'."}

            api_file = os.path.join(p_path, "api.py")
            if not os.path.isfile(api_file):
                api_file = os.path.join(p_path, "build_hook.py")

            if not os.path.isfile(api_file):
                return {"error": f"No API file (api.py or build_hook.py) found for plugin '{plugin_id}'."}

            mod_name = f"plugins.{plugin_id}.{os.path.splitext(os.path.basename(api_file))[0]}"
            mod = None
            with self._lock:
                if mod_name in sys.modules and sys.modules[mod_name] is not None:
                    mod = sys.modules[mod_name]
                else:
                    spec = importlib.util.spec_from_file_location(
                        mod_name, api_file, submodule_search_locations=[p_path]
                    )
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
                    return {"error": f"Action '{action}' not found in plugin module '{mod_name}'."}
            else:
                return {"error": f"Failed to load plugin module '{mod_name}' from '{api_file}'."}
        except Exception as e:
            mod_name = f"plugins.{plugin_id}.api"
            if mod_name in sys.modules:
                sys.modules.pop(mod_name, None)
            output.add_text(f"call_plugin_api error ({plugin_id}.{action}): {e}", msg_type="error")
            return {"error": str(e)}
