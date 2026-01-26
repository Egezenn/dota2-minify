import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
if os.getcwd() != minify_root:
    os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

import helper


def main():
    try:
        if helper.workshop_installed:
            helper.remove_path(os.path.join(current_dir, "styling.css"))
    except:
        pass
