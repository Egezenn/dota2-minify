# core.migrations

## `Migrations()`

*No documentation available.*

<details open><summary>Source</summary>

```python
class Migrations:
    def __init__(self):
        self.rename_modcfg_to_manifest()

    def rename_modcfg_to_manifest(self):
        """
        Scans all mods directories and renames modcfg.json to manifest.json if present.
        """
        if not os.path.exists(base.mods_dir):
            return

        for mod in os.listdir(base.mods_dir):
            mod_path = os.path.join(base.mods_dir, mod)
            if not os.path.isdir(mod_path) or mod.startswith("_"):
                continue

            modcfg_json = os.path.join(mod_path, "modcfg.json")
            manifest_json = os.path.join(mod_path, "manifest.json")

            if os.path.exists(modcfg_json):
                if not os.path.exists(manifest_json):
                    try:
                        os.rename(modcfg_json, manifest_json)
                        log.write_warning(f"Migrated modcfg.json to manifest.json in {mod}")
                    except Exception as e:
                        log.write_warning(f"Failed to migrate modcfg.json to manifest.json in {mod}: {e}")
                else:
                    try:
                        os.remove(modcfg_json)
                        log.write_warning(f"Removed redundant modcfg.json in {mod} since manifest.json exists")
                    except Exception as e:
                        log.write_warning(f"Failed to remove redundant modcfg.json in {mod}: {e}")

```

</details>
