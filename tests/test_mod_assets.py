import fnmatch
import json
import os

import helper
from core import base, utils


def test_mod_assets_exist_in_gamepak():
    """
    Validates that file paths declared in mod blacklists, replacers, and RERL rules
    actually exist in the game pak. Only runs if gamepakcontents exists in the
    environment, else passes.
    """
    gamepak_path = base.gamepakcontents_file_dir
    if not os.path.isfile(gamepak_path):
        return

    with utils.open_utf8(gamepak_path) as f:
        gamepak_contents = set(line.strip() for line in f)

    blank_exts = tuple(helper.get_blank_file_extensions())
    errors = []

    for entry in os.scandir(base.mods_dir):
        if not entry.is_dir():
            continue

        # 1. Validate blacklist.txt
        bl_path = os.path.join(entry.path, "blacklist.txt")
        if os.path.isfile(bl_path):
            with utils.open_utf8(bl_path) as f:
                for idx, line in enumerate(f):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith((">>", "**", "*-")):
                        continue
                    if line.startswith("--"):
                        exclusion = line[2:].strip()
                        if exclusion.endswith(blank_exts) and exclusion not in gamepak_contents:
                            errors.append(f"mods/{entry.name}/blacklist.txt:{idx + 1} (exclusion): {exclusion}")
                        continue
                    if line.endswith(blank_exts):
                        if line not in gamepak_contents:
                            errors.append(f"mods/{entry.name}/blacklist.txt:{idx + 1}: {line}")

        # 2. Validate replacer.json
        rep_path = os.path.join(entry.path, "replacer.json")
        if os.path.isfile(rep_path):
            with utils.open_utf8(rep_path) as f:
                replacements = json.load(f)
            for target, source in replacements.items():
                if target and target not in gamepak_contents:
                    errors.append(f"mods/{entry.name}/replacer.json (target): {target}")
                if source and source not in gamepak_contents:
                    errors.append(f"mods/{entry.name}/replacer.json (source): {source}")

        # 3. Validate rerl.json patterns
        rerl_path = os.path.join(entry.path, "rerl.json")
        if os.path.isfile(rerl_path):
            with utils.open_utf8(rerl_path) as f:
                rules = json.load(f)
            for target_pattern in rules:
                if not any(fnmatch.fnmatch(f, target_pattern) for f in gamepak_contents):
                    errors.append(f"mods/{entry.name}/rerl.json (target pattern matched nothing): {target_pattern}")

    assert not errors, "Non-existent asset paths found in mods:\n" + "\n".join(errors)
