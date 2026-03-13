import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
if os.getcwd() != minify_root:
    os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

# isort: split

import requests

# isort: split

import conditions
from core import constants, fs

before_workshop_req = "https://github.com/Egezenn/dota2-minify/blob/Minify-v1.11.2/mods/Auto%20Accept%20Match/files/panorama/layout/popups/popup_accept_match.vxml_c"


def main():
    if not conditions.workshop_installed:
        response = requests.get(before_workshop_req)
        if response.status_code == 200:
            fs.create_dirs(os.path.join(constants.minify_dota_compile_output_path, "panoroma", "layout", "popups"))
            with open(
                os.path.join(
                    constants.minify_dota_compile_output_path,
                    "panoroma",
                    "layout",
                    "popups",
                    "popup_accept_match.vxml_c",
                ),
                "wb",
            ) as file:
                file.write(response.content)
