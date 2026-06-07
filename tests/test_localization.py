import json
import os
import subprocess
import sys


def get_git_tracked_py_files(root_dir):
    result = subprocess.run(["git", "ls-files", "Minify"], capture_output=True, text=True, check=True, cwd=root_dir)
    files = result.stdout.splitlines()
    py_files = [os.path.join(root_dir, f) for f in files if f.endswith(".py")]
    return py_files


def test_unused_localization_keys():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    loc_path = os.path.join(root_dir, "Minify", "bin", "localization.json")

    assert os.path.exists(loc_path), f"localization.json not found at {loc_path}"

    with open(loc_path, "r", encoding="utf-8") as f:
        loc_data = json.load(f)

    keys = list(loc_data.keys())
    py_files = get_git_tracked_py_files(root_dir)

    file_contents = {}
    for filepath in py_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                file_contents[filepath] = f.read()
        except Exception:
            try:
                with open(filepath, "r", encoding="latin-1") as f:
                    file_contents[filepath] = f.read()
            except Exception:
                pass

    unused_keys = []
    for key in keys:
        is_used = False
        amp_key = f"&{key}"

        for content in file_contents.values():
            if amp_key in content:
                is_used = True
                break
            if f'"{key}"' in content or f"'{key}'" in content:
                is_used = True
                break
            if "start_text_" in key and "start_text_{i}_var" in content:
                is_used = True
                break

        if not is_used:
            unused_keys.append(key)

    assert len(unused_keys) == 0, f"Unused localization keys found: {unused_keys}"


if __name__ == "__main__":
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    py_files = get_git_tracked_py_files(root)
    loc_path = os.path.join(root, "Minify", "bin", "localization.json")
    with open(loc_path, "r", encoding="utf-8") as f:
        loc_data = json.load(f)
    keys = list(loc_data.keys())
    file_contents = {}
    for filepath in py_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                file_contents[filepath] = f.read()
        except Exception:
            try:
                with open(filepath, "r", encoding="latin-1") as f:
                    file_contents[filepath] = f.read()
            except Exception:
                pass
    unused = []
    for key in keys:
        is_used = False
        amp_key = f"&{key}"
        for content in file_contents.values():
            if amp_key in content:
                is_used = True
                break
            if f'"{key}"' in content or f"'{key}'" in content:
                is_used = True
                break
            if "start_text_" in key and "start_text_{i}_var" in content:
                is_used = True
                break
        if not is_used:
            unused.append(key)
    if unused:
        print("Unused localization keys:")
        for k in sorted(unused):
            print(f"  - {k}")
        sys.exit(1)
    else:
        print("All localization keys are used.")
        sys.exit(0)
