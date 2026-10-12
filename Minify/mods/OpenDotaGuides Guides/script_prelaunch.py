import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
mod_name = os.path.basename(current_dir)
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

# isort: split

import requests
from core import utils
from script import main as fetch_guides

RELEASE_API_URL = "https://api.github.com/repos/Egezenn/OpenDotaGuides/releases/latest"


def main():
    try:
        response = requests.get(RELEASE_API_URL, timeout=15)
        if response.status_code != 200:
            raise ValueError(f"GitHub API returned status {response.status_code}")
        release_tag = response.json().get("tag_name")
        if not isinstance(release_tag, str) or not release_tag:
            raise ValueError("GitHub API response did not include a release tag")
    except Exception as e:
        from core import log, output

        log.write_warning(f"Failed to check OpenDotaGuides release: {e}")
        output.add_text("&connection_error", msg_type="error", indent=True)
        return

    if release_tag != utils.get_state(mod_name, "last_tag"):
        if fetch_guides(release_tag):
            utils.set_state(mod_name, "last_tag", release_tag)
        return True


if __name__ == "__main__":
    main()
