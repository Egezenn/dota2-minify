import fnmatch
import json
import os

from core import constants, fs, log, output, rerl, utils


def process(rerl_file: str, folder: str, dota_pak_contents) -> None:
    """
    Processes rerl.json for a mod, matching targeted compiled resources
    and rewriting their RERL external references.
    """
    if not os.path.exists(rerl_file):
        return

    try:
        with utils.open_utf8(rerl_file) as file:
            rules: dict[str, dict[str, str]] = json.load(file)
    except Exception as e:
        log.write_warning(f"Failed to parse rerl.json for {folder}: {e}")
        return

    for target_pattern, redirect_map in rules.items():
        if not target_pattern or not redirect_map:
            continue

        target_paths = []
        if any(c in target_pattern for c in ("*", "?", "[")):
            for filepath in dota_pak_contents:
                if fnmatch.fnmatch(filepath, target_pattern):
                    target_paths.append(filepath)
        else:
            target_paths.append(target_pattern)

        if not target_paths:
            log.write_warning(f"No assets found matching '{target_pattern}' in rerl.json for {folder}")
            continue

        for path in target_paths:
            clean_path = path.strip().strip('"').strip("'").replace("\\", "/").lstrip("/")
            dest_file = os.path.join(constants.minify_dota_compile_output_path, clean_path)

            try:
                if os.path.exists(dest_file):
                    with open(dest_file, "rb") as f:
                        data = f.read()
                else:
                    pakfile = dota_pak_contents.get_file(clean_path)
                    if not pakfile:
                        log.write_warning(f"Target asset '{clean_path}' not found in game VPK for {folder}")
                        continue
                    data = pakfile.read()

                # Quick pre-check: only process if at least one redirect target is present
                if not any(src.encode("utf-8") in data for src in redirect_map.keys()):
                    continue

                patched_data, count = rerl.patch_resource_rerl(data, redirect_map)
                if count > 0:
                    fs.create_dirs(os.path.dirname(dest_file))
                    with open(dest_file, "wb") as f:
                        f.write(patched_data)
                    output.add_text(f"Decoupled {count} RERL reference(s) in {clean_path}", indent=True)

            except Exception as e:
                log.write_warning(f"Failed to patch RERL for '{clean_path}' in {folder}: {e}")
