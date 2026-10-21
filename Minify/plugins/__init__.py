import importlib
import importlib.util
import os
import sys
import types

from core import base, config, output, registry


def initialize():
    """Discover and initialize plugins dynamically from the plugins directory on disk."""
    from core import mods_shared

    plugins_dir = base.plugins_dir

    registry.PluginRegistry.clear()

    if not os.path.exists(plugins_dir):
        return

    parent_dir = os.path.dirname(plugins_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    if plugins_dir not in sys.path:
        sys.path.insert(0, plugins_dir)

    for entry in sorted(os.listdir(plugins_dir)):
        if mods_shared.is_ignored_folder(entry):
            continue

        p_path = os.path.join(plugins_dir, entry)
        if not os.path.isdir(p_path):
            continue

        manifest_path = os.path.join(p_path, "manifest.json")
        if not os.path.isfile(manifest_path):
            continue

        try:
            manifest = config.read_json_file(manifest_path)
            if not isinstance(manifest, dict):
                continue

            py_file = os.path.join(p_path, "__main__.py")
            if os.path.isfile(py_file):
                plugin_id = manifest.get("id")
                if not isinstance(plugin_id, str) or not plugin_id:
                    continue
                package_name = f"plugins.{plugin_id}"
                package = sys.modules.get(package_name)
                if package is None:
                    package = types.ModuleType(package_name)
                    package.__path__ = [p_path]
                    package.__package__ = package_name
                    sys.modules[package_name] = package
                elif p_path not in getattr(package, "__path__", []):
                    output.add_text(f"Duplicate plugin id '{plugin_id}' in '{entry}'.", msg_type="warning")
                    continue
                mod_name = f"{package_name}.__main__"
                spec = importlib.util.spec_from_file_location(
                    mod_name,
                    py_file,
                    submodule_search_locations=[p_path],
                )
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules[mod_name] = mod
                    try:
                        spec.loader.exec_module(mod)
                    except Exception:
                        sys.modules.pop(mod_name, None)
                        raise
                    if mod not in registry.get_plugins():
                        registry.register_plugin(mod)

        except Exception as e:
            output.add_text(f"Error initializing plugin '{entry}': {e}", msg_type="warning")

    for plugin in registry.get_plugins():
        if hasattr(plugin, "on_initialize"):
            try:
                plugin.on_initialize()
            except Exception as e:
                output.add_text(f"Error running plugin initialization hook: {e}", msg_type="warning")
