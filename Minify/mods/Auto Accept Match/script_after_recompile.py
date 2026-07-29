import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
if os.getcwd() != minify_root:
    os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

# isort: split

import conditions
import requests
from core import fs, log, output

before_workshop_req = "https://raw.githubusercontent.com/Egezenn/dota2-minify/refs/tags/Minify-v1.11.2/mods/Auto%20Accept%20Match/files/panorama/layout/popups/popup_accept_match.vxml_c"

fallback_dir = os.path.join(current_dir, "files", "panorama", "layout", "popups")
fallback_path = os.path.join(fallback_dir, "popup_accept_match.vxml_c")


def main():
    if conditions.workshop_installed:
        fs.remove_path(fallback_path)
        return

    if not (conditions.workshop_installed and os.path.exists(fallback_path)):
        response = requests.get(before_workshop_req)
        if response.status_code == 200:
            fs.create_dirs(fallback_dir)
            with open(fallback_path, "wb") as file:
                file.write(response.content)
            output.add_text(f"Downloaded the static 10s file for {current_dir}")
        else:
            log.write_warning("Fallback download failed!")
