import os
import sys
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
mod_name = os.path.basename(current_dir)
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

# isort: split

from core import utils

# isort: split

from script import main as fetch_guides


def main():
    last_time = utils.get_state(mod_name, "last_run_time", 0)
    if time.time() - last_time > 86400:
        fetch_guides()
        utils.set_state(mod_name, "last_run_time", int(time.time()))
        return True


if __name__ == "__main__":
    main()
