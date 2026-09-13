import os

from core import base, config, fs, log, mods_shared, output


class Migrations:
    def __init__(self):
        self._migrate_locale_config()
        self._rename_file_in_mods("modcfg.json", "manifest.json")
        self._rename_file_in_mods("xml_mod.json", "xml.json")
        self._migrate_rescomproot_and_bin()
        self._migrate_legacy_paks()
        self._migrate_flatten_d2pfx_manifests()

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
                        output.add_text(f"Migrated {src_name} to {dest_name} in {mod}")
                    except Exception as e:
                        log.write_warning(f"Failed to migrate {src_name} to {dest_name} in {mod}: {e}")
                else:
                    try:
                        fs.remove_path(src)
                        output.add_text(f"Removed redundant {src_name} in {mod} since {dest_name} exists")
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
                    output.add_text("Migrated rescomproot to config/")
                except Exception as e:
                    log.write_warning(f"Failed to migrate rescomproot: {e}")
            else:
                try:
                    fs.remove_path(legacy_rescomp)
                    output.add_text("Removed redundant bin/rescomproot since config/rescomproot exists")
                except Exception as e:
                    log.write_warning(f"Failed to remove redundant bin/rescomproot: {e}")

            # Delete the bin directory when rescomproot migration occurs
            if os.path.exists(legacy_bin):
                try:
                    fs.remove_path(legacy_bin)
                    output.add_text(f"Removed legacy {legacy_bin} folder")
                except Exception as e:
                    log.write_warning(f"Failed to remove legacy {legacy_bin} folder: {e}")

    def _migrate_legacy_paks(self):
        from patch import vpk_utils

        from core import constants, utils

        states = utils.read_states()
        if states.get("legacy_paks_migrated"):
            return

        target_dir = config.get("output_path", constants.minify_default_dota_pak_output_path)

        if os.path.isdir(target_dir):
            for item in ("pak65_dir.vpk", "pak67_dir.vpk"):
                pak_path = os.path.join(target_dir, item)
                if os.path.isfile(pak_path) and vpk_utils.is_minify_pak(pak_path):
                    try:
                        fs.remove_path(pak_path)
                        output.add_text(f"Migrated and removed legacy Minify pak: {pak_path}")
                    except Exception as e:
                        log.write_warning(f"Failed to remove legacy pak {pak_path}: {e}")

        utils.write_states("legacy_paks_migrated", True)

    def _migrate_flatten_d2pfx_manifests(self):
        if not os.path.exists(base.mods_dir):
            return

        for mod in os.listdir(base.mods_dir):
            mod_path = os.path.join(base.mods_dir, mod)
            if not os.path.isdir(mod_path) or mods_shared.is_ignored_folder(mod):
                continue

            manifest_path = os.path.join(mod_path, "manifest.json")
            if not os.path.isfile(manifest_path):
                continue

            try:
                manifest = config.read_json_file(manifest_path)
                if not isinstance(manifest, dict):
                    continue

                browser_info = manifest.get("browser")
                if not isinstance(browser_info, dict):
                    continue

                if browser_info.get("browser") != "d2pfx":
                    continue

                raw_tags = browser_info.get("tags")
                if isinstance(raw_tags, dict):
                    tags = [k for k, v in raw_tags.items() if v]
                elif isinstance(raw_tags, list):
                    tags = raw_tags
                elif raw_tags is None:
                    tags = []
                else:
                    tags = [str(raw_tags)]

                new_manifest = {
                    "browser": "d2pfx",
                    "name": browser_info.get("name"),
                    "category": browser_info.get("category"),
                    "author": browser_info.get("author"),
                    "sender": browser_info.get("sender"),
                    "links": browser_info.get("links", []),
                    "tags": tags,
                    "version": browser_info.get("version"),
                    "label": browser_info.get("label"),
                }

                for k, v in browser_info.items():
                    if k not in new_manifest:
                        new_manifest[k] = v

                for k, v in manifest.items():
                    if k != "browser" and k not in new_manifest:
                        new_manifest[k] = v

                config.write_json_file(manifest_path, new_manifest)
                output.add_text(f"Flattened d2pfx manifest in {mod}")
            except Exception as e:
                log.write_warning(f"Failed to flatten d2pfx manifest in {mod}: {e}")


Migrations()
