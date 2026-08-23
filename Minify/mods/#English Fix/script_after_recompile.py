import os
import shutil
import sys

import vpk

current_dir = os.path.dirname(os.path.abspath(__file__))
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

# isort: split

from core import config, constants, fs, output


def main():
    english_files = []
    dota_pak = vpk.open(constants.dota_game_pak_path)

    for filepath in dota_pak:
        if filepath.endswith("_english.txt") or filepath.endswith("_english.vtt"):
            english_files.append(filepath)

    game_root = os.path.dirname(os.path.dirname(constants.dota_game_pak_path))
    locale = config.get_locale()

    disk_locale_files = []
    disk_walk_dirs = ["core", "dota_addons"]
    for sub in disk_walk_dirs:
        walk_root = os.path.join(game_root, sub)
        if not os.path.isdir(walk_root):
            continue
        for dirpath, _, filenames in os.walk(walk_root):
            for fname in filenames:
                if fname.endswith(f"_{locale}.txt") or fname.endswith(f"_{locale}.vtt"):
                    abs_path = os.path.join(dirpath, fname)
                    rel_path = os.path.relpath(abs_path, game_root).replace("\\", "/")
                    disk_locale_files.append(rel_path)

    compile_dir = constants.minify_dota_compile_output_path
    fs.create_dirs(compile_dir)

    for filepath in english_files:
        data = dota_pak[filepath].read()
        renamed_paths = filepath.replace("_english.txt", f"_{locale}.txt").replace("_english.vtt", f"_{locale}.vtt")
        dest = os.path.join(compile_dir, renamed_paths)
        fs.create_dirs(os.path.dirname(dest))
        with open(dest, "wb") as f:
            f.write(data)

    bkup_dir = os.path.join(minify_root, "backup", "#English Fix")
    for rel_path in disk_locale_files:
        locale_file = os.path.join(game_root, rel_path)
        english_file = os.path.join(
            game_root, rel_path.replace(f"_{locale}.txt", "_english.txt").replace(f"_{locale}.vtt", "_english.vtt")
        )
        if not os.path.isfile(english_file):
            continue
        bkup_dest = os.path.join(bkup_dir, rel_path)
        fs.create_dirs(os.path.dirname(bkup_dest))
        with open(english_file, "rb") as src_f:
            eng_data = src_f.read()
        with open(locale_file, "rb") as src_f, open(bkup_dest, "wb") as bk_f:
            bk_f.write(src_f.read())
        with open(locale_file, "wb") as dst_f:
            dst_f.write(eng_data)

    files_dir = os.path.join(current_dir, "files")
    if os.path.exists(files_dir):
        shutil.copytree(files_dir, compile_dir, dirs_exist_ok=True)

    total = len(english_files) + len(disk_locale_files)
    output.add_text(
        f"Extracted and renamed {total} localization files ({len(disk_locale_files)} from game files).",
        msg_type="success",
    )


if __name__ == "__main__":
    main()
