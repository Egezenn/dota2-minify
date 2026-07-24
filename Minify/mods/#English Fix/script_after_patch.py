import os
import sys

import vpk

current_dir = os.path.dirname(os.path.abspath(__file__))
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

# isort: split

from core import config, constants, fs, output
import helper
import patch


def main():
    output.add_text("Checking if localization swaps needs to be redone.")
    # TODO: Need to dynamically check the ones on disk aswell, as file integrity checks will override them
    if patch.dota_version_changed or "-f" in sys.argv:
        english_files = []
        dota_pak = vpk.open(constants.dota_game_pak_path)

        for filepath in dota_pak:
            if filepath.endswith("_english.txt") or filepath.endswith("_english.vtt"):
                english_files.append(filepath)

        game_root = os.path.dirname(os.path.dirname(constants.dota_game_pak_path))
        locale = config.get("output_locale")

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

        if not english_files and not disk_locale_files:
            output.add_text("No *_english.txt files found in game VPK or game files.", msg_type="warning")
            return

        compile_dir = os.path.join(current_dir, "compile")
        vpk_dest = os.path.join(helper.output_path, "pak99_dir.vpk")
        fs.remove_path(compile_dir, vpk_dest)
        fs.create_dirs(compile_dir)

        for filepath in english_files:
            data = dota_pak[filepath].read()
            russian_path = filepath.replace("_english.txt", f"_{locale}.txt").replace("_english.vtt", f"_{locale}.vtt")
            dest = os.path.join(compile_dir, russian_path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
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
            os.makedirs(os.path.dirname(bkup_dest), exist_ok=True)
            with open(locale_file, "rb") as src_f, open(bkup_dest, "wb") as bk_f:
                bk_f.write(src_f.read())
            with open(english_file, "rb") as src_f, open(locale_file, "wb") as dst_f:
                dst_f.write(src_f.read())

        total = len(english_files) + len(disk_locale_files)
        output.add_text(
            f"Extracted and renamed {total} localization files ({len(disk_locale_files)} from game files).",
            msg_type="success",
        )

        pak = vpk.new(compile_dir)
        pak.save(vpk_dest)
        output.add_text(f"Saved pak to {vpk_dest}", msg_type="success")

        fs.remove_path(compile_dir)
    else:
        output.add_text("Build version hasn't changed, skipping.")


if __name__ == "__main__":
    main()
