import fnmatch
try:
    import jsonc as json
except ImportError:
    import json
import os
import subprocess

import conditions
from core import base, constants, fs, log, output, utils
from patch import manifest_utils


def process(remap_file: str, folder: str, dota_pak_contents, mod_cfg=None, mod_settings=None) -> None:
    """
    Processes remap.json for a mod, matching targeted compiled resources
    and remapping references in decompiled source files.
    """
    if not os.path.exists(remap_file):
        return

    try:
        with utils.open_utf8(remap_file) as file:
            rules: dict = json.load(file)
    except Exception as e:
        log.write_warning(f"Failed to parse remap.json for {folder}: {e}")
        return

    settings = manifest_utils.get_effective_settings(mod_cfg, mod_settings)

    for target_pattern, rule_val in rules.items():
        if not target_pattern or not rule_val or not isinstance(rule_val, dict):
            continue

        target_pattern = manifest_utils.interpolate_variables(target_pattern, settings)

        cond = rule_val.get("if") or rule_val.get("condition")
        if cond is not None and not manifest_utils.evaluate_condition(cond, settings):
            continue

        raw_redirects = (
            rule_val.get("redirects")
            if "redirects" in rule_val and isinstance(rule_val["redirects"], dict)
            else rule_val
        )

        redirect_map: dict[str, str] = {}
        for src_ref, dst_ref in raw_redirects.items():
            if src_ref in ("if", "condition", "redirects"):
                continue
            if isinstance(dst_ref, str):
                src_clean = manifest_utils.interpolate_variables(src_ref, settings)
                dst_clean = manifest_utils.interpolate_variables(dst_ref, settings)
                redirect_map[src_clean] = dst_clean
            elif isinstance(dst_ref, dict):
                sub_cond = dst_ref.get("if") or dst_ref.get("condition")
                if sub_cond is not None and not manifest_utils.evaluate_condition(sub_cond, settings):
                    continue
                target_str = dst_ref.get("target") or dst_ref.get("dst") or dst_ref.get("to")
                if target_str:
                    src_clean = manifest_utils.interpolate_variables(src_ref, settings)
                    dst_clean = manifest_utils.interpolate_variables(str(target_str), settings)
                    redirect_map[src_clean] = dst_clean

        if not redirect_map:
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
