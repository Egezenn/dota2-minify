import json
import os
import shutil

from core import base, constants, fs, log, output, utils


def process_replacer(item):
    source, target = item
    output.add_text("&replacing_terminal", source, target)
    fs.create_dirs(os.path.dirname(target_dir := os.path.join(constants.minify_dota_compile_output_path, target)))
    shutil.copy(os.path.join(base.replace_dir, source), target_dir)


def process(replacer_file, folder, replacer_source_extracts, replacer_targets):
    if not os.path.exists(replacer_file):
        return

    try:
        with utils.open_utf8(replacer_file) as file:
            replacements = json.load(file)

        for target, source in replacements.items():
            if target and source:
                replacer_source_extracts.append(source)  # Source (content)
                replacer_targets.append((source, target))  # (Source, Target)
            else:
                log.write_warning(f"Invalid entry in replacer.json for {folder}: {target} -> {source}")
    except Exception as e:
        log.write_warning(f"Failed to parse replacer.json for {folder}: {e}")
