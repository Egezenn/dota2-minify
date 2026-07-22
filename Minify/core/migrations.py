import os

from core import base, fs, log


class Migrations:
    def __init__(self):
        self._rename_file_in_mods("modcfg.json", "manifest.json")
        self._rename_file_in_mods("xml_mod.json", "xml.json")

    def _rename_file_in_mods(self, src_name, dest_name):
        if not os.path.exists(base.mods_dir):
            return

        for mod in os.listdir(base.mods_dir):
            mod_path = os.path.join(base.mods_dir, mod)
            if not os.path.isdir(mod_path) or mod.startswith("_"):
                continue

            src = os.path.join(mod_path, src_name)
            dest = os.path.join(mod_path, dest_name)

            if os.path.exists(src):
                if not os.path.exists(dest):
                    try:
                        fs.move_path(src, dest)
                        log.write_warning(f"Migrated {src_name} to {dest_name} in {mod}")
                    except Exception as e:
                        log.write_warning(f"Failed to migrate {src_name} to {dest_name} in {mod}: {e}")
                else:
                    try:
                        fs.remove_path(src)
                        log.write_warning(f"Removed redundant {src_name} in {mod} since {dest_name} exists")
                    except Exception as e:
                        log.write_warning(f"Failed to remove redundant {src_name} in {mod}: {e}")


# Run migrations upon initialization (import)
Migrations()
