import os
from typing import Any, Dict, List

import helper
from core import base, config, constants, localization, mods_shared, output


class ConfigService:
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

    @staticmethod
    def parse_setting_item(
        item: dict, mod_folder: str | None = None, plugin_folder: str | None = None
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

            native_schema = config.read_json_file(base.settings_file_dir)
            if not isinstance(native_schema, list):
                native_schema = []

            settings_schema = []
            values = {}

            for item in native_schema:
                parsed = self.parse_setting_item(item)
                if parsed:
                    settings_schema.append(parsed)
                    values[parsed["key"]] = config.get(parsed["key"], parsed["default"])

            # Plugin manifest settings discovery
            plugins_dir = base.plugins_dir
            if os.path.exists(plugins_dir):
                for plugin_folder in sorted(os.listdir(plugins_dir)):
                    if mods_shared.is_ignored_folder(plugin_folder):
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
                                        parsed = self.parse_setting_item(item, plugin_folder=plugin_folder)
                                        if parsed:
                                            settings_schema.append(parsed)
                                            values[parsed["key"]] = config.get(parsed["key"], parsed["default"])
                        except Exception as e:
                            output.add_text(f"Error reading plugin manifest {manifest_path}: {e}", msg_type="warning")

            # Mod manifest settings discovery
            if os.path.exists(base.mods_dir):
                for mod_folder in sorted(os.listdir(base.mods_dir)):
                    if mods_shared.is_ignored_folder(mod_folder):
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

                        parsed = self.parse_setting_item(item, mod_folder=mod_folder)
                        if parsed:
                            mod_store = config.get_mod(mod_folder, {})
                            cur_val = mod_store.get(parsed["key"], parsed["default"])
                            values[parsed["key"]] = cur_val
                            settings_schema.append(parsed)

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
            native_schema = config.read_json_file(base.settings_file_dir)
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
