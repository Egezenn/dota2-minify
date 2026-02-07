import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
mod_name = os.path.basename(current_dir)
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

import mpaths


def main():
    config_data = mpaths.get_mod_config(mod_name)
    font_string = mpaths.get_config__dict(config_data, "font_string", "Calibri, sans-serif")

    css = os.path.join(current_dir, "styling.css")
    target_string = f": {font_string};"
    with open(css) as f:
        data = f.read()
    data = data.replace(target_string, ": <insert_fonts_here>;")
    with open(css, "w") as f:
        f.write(data)
