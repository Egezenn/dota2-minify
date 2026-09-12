import os

from core import base, config, fs, log, mods_shared


class Migrations:
    def __init__(self):
        self._migrate_locale_config()
        self._rename_file_in_mods("modcfg.json", "manifest.json")
        self._rename_file_in_mods("xml_mod.json", "xml.json")
        self._migrate_rescomproot_and_bin()

    def _migrate_locale_config(self):
        locale = config.get("output_locale")
        path = config.get("output_path")
        ui_locale = config.get("locale")

        if isinstance(ui_locale, str) and any(c.isupper() for c in ui_locale):
            config.set("locale", "en")
            log.write_warning(f"Migrated capitalized locale '{ui_locale}' to 'en'")

        changed = False

        if locale == "minify":
            config.set("output_locale", "english")
            changed = True

        if path and "dota_minify" in path:
            config.set("output_path", path.replace("dota_minify", "dota_dutch"))
            changed = True

        if changed:
            log.write_warning("Migrated legacy 'minify' locale to 'english' (dutch fallback)")

    def _rename_file_in_mods(self, src_name, dest_name):
        if not os.path.exists(base.mods_dir):
            return

        for mod in os.listdir(base.mods_dir):
            mod_path = os.path.join(base.mods_dir, mod)
            if not os.path.isdir(mod_path) or mods_shared.is_ignored_folder(mod):
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

    def _migrate_rescomproot_and_bin(self):
        legacy_bin = "bin"
        legacy_rescomp = os.path.join(legacy_bin, "rescomproot")
        target_rescomp = os.path.abspath(base.rescomp_override_dir)

        if not os.path.exists(legacy_rescomp):
            alt_rescomp = os.path.join(base.base_dir, "bin", "rescomproot")
            if os.path.exists(alt_rescomp):
                legacy_rescomp = alt_rescomp
                legacy_bin = os.path.join(base.base_dir, "bin")

        if os.path.exists(legacy_rescomp):
            if not os.path.exists(target_rescomp):
                try:
                    fs.create_dirs(os.path.dirname(target_rescomp))
                    fs.move_path(legacy_rescomp, target_rescomp)
                    log.write_warning("Migrated rescomproot to config/")
                except Exception as e:
                    log.write_warning(f"Failed to migrate rescomproot: {e}")
            else:
                try:
                    fs.remove_path(legacy_rescomp)
                    log.write_warning("Removed redundant bin/rescomproot since config/rescomproot exists")
                except Exception as e:
                    log.write_warning(f"Failed to remove redundant bin/rescomproot: {e}")

            # Delete the bin directory when rescomproot migration occurs
            if os.path.exists(legacy_bin):
                try:
                    fs.remove_path(legacy_bin)
                    log.write_warning(f"Removed legacy {legacy_bin} folder")
                except Exception as e:
                    log.write_warning(f"Failed to remove legacy {legacy_bin} folder: {e}")


Migrations()
