import os
import shutil
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

# isort: split

from core import constants, fs, output


def main():
    bkup_dir = os.path.join(minify_root, "backup", "#English Fix")
    if not os.path.isdir(bkup_dir):
        output.add_text("No backup found for #English Fix disk files.", msg_type="warning")
        return

    game_root = os.path.dirname(os.path.dirname(constants.dota_game_pak_path))
    restored = 0

    for dirpath, _, filenames in os.walk(bkup_dir):
        for fname in filenames:
            bkup_file = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(bkup_file, bkup_dir).replace("\\", "/")
            dest = os.path.join(game_root, rel_path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(bkup_file, dest)
            restored += 1

    fs.remove_path(bkup_dir)
    output.add_text(f"Restored {restored} disk files from backup.", msg_type="success")


if __name__ == "__main__":
    main()
