import fnmatch
import json
import os
import subprocess

import conditions
from core import base, constants, fs, log, output, utils


def process(remap_file: str, folder: str, dota_pak_contents) -> None:
    """
    Processes remap.json for a mod, matching targeted compiled resources
    and remapping references in decompiled source files.
    """
    if not os.path.exists(remap_file):
        return

    try:
        with utils.open_utf8(remap_file) as file:
            rules: dict[str, dict[str, str]] = json.load(file)
    except Exception as e:
        log.write_warning(f"Failed to parse remap.json for {folder}: {e}")
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
            log.write_warning(f"No assets found matching '{target_pattern}' in remap.json for {folder}")
            continue

        for path in target_paths:
            clean_path = path.strip().strip('"').strip("'").replace("\\", "/").lstrip("/")

            try:
                dest_file = os.path.join(constants.minify_dota_compile_output_path, clean_path)
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

                if clean_path.endswith("_c") and conditions.workshop_installed:
                    source_rel = clean_path.removesuffix("_c")
                    out_source = os.path.join(base.build_dir, source_rel)
                    fs.create_dirs(os.path.dirname(out_source))

                    temp_c = os.path.join(base.build_dir, clean_path)
                    fs.create_dirs(os.path.dirname(temp_c))
                    with open(temp_c, "wb") as f:
                        f.write(data)

                    res = subprocess.run(
                        [constants.s2v_exec_path, "-i", temp_c, "-d", "-o", out_source],
                        capture_output=True,
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW if base.is_win else 0,
                    )
                    fs.remove_path(temp_c)

                    if res.returncode == 0 and os.path.exists(out_source):
                        try:
                            with utils.open_utf8(out_source) as f:
                                source_content = f.read()

                            for src_ref, dst_ref in redirect_map.items():
                                source_content = source_content.replace(src_ref, dst_ref)

                            with utils.open_utf8(out_source, "w") as f:
                                f.write(source_content)

                            output.add_text(f"Remapped references in {clean_path}", indent=True)
                        except Exception as e:
                            log.write_warning(f"Failed to remap references in '{out_source}': {e}")
                    else:
                        log.write_warning(f"Failed to decompile '{clean_path}' for {folder}")

            except Exception as e:
                log.write_warning(f"Failed to process remap for '{clean_path}' in {folder}: {e}")
