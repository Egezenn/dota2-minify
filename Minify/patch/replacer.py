try:
    import jsonc as json
except ImportError:
    import json
import os
import shutil

from core import base, constants, fs, log, output, utils
from patch import manifest_utils


def process_replacer(item):
    source, target = item
    output.add_text("&replacing_terminal", source, target, indent=True)
    fs.create_dirs(os.path.dirname(target_dir := os.path.join(constants.minify_dota_compile_output_path, target)))
    shutil.copy(os.path.join(base.replace_dir, source), target_dir)


def process(
    replacer_file,
    folder,
    replacer_source_extracts,
    replacer_targets,
    mod_cfg=None,
    mod_settings=None,
):
    if not os.path.exists(replacer_file):
        return

    try:
        with utils.open_utf8(replacer_file) as file:
            replacements = json.load(file)

        settings = manifest_utils.get_effective_settings(mod_cfg, mod_settings)

        for target, source_val in replacements.items():
            if not target or source_val is None:
                continue

            target_clean = manifest_utils.interpolate_variables(str(target), settings)

            if isinstance(source_val, str):
                source_clean = manifest_utils.interpolate_variables(source_val, settings)
                replacer_source_extracts.append(source_clean)
                replacer_targets.append((source_clean, target_clean))
            elif isinstance(source_val, dict):
                cond = source_val.get("if") or source_val.get("condition")
                if cond is not None and not manifest_utils.evaluate_condition(cond, settings):
                    continue
                src = source_val.get("source") or source_val.get("src")
                if src:
                    source_clean = manifest_utils.interpolate_variables(str(src), settings)
                    replacer_source_extracts.append(source_clean)
                    replacer_targets.append((source_clean, target_clean))
                else:
                    log.write_warning(f"Missing 'source' in replacer.json rule for {folder}: {target}")
            else:
                log.write_warning(f"Invalid entry in replacer.json for {folder}: {target} -> {source_val}")
    except Exception as e:
        log.write_warning(f"Failed to parse replacer.json for {folder}: {e}")

