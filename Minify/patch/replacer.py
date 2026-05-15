import csv
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

    with utils.open_utf8(replacer_file, newline="") as file:
        for row in csv.reader(file):
            if len(row) >= 2 and row[0] and row[1]:
                replacer_source_extracts.append(row[1])  # Source (content)
                replacer_targets.append((row[1], row[0]))  # (Source, Target)
            else:
                log.write_warning(f"Invalid row in replacer.csv for {folder}: {row}")
