import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

# isort: split

from core import fs
from ui import terminal


def main():
    if not os.path.exists(os.path.join(current_dir, "styling.css")):
        terminal.add_text(
            f'You have {os.path.basename(current_dir)} mod enabled but haven\'t created a "styling.css" file yet.\n'
            "To prevent breaking changes without your consent we insist you to take a glance at the file first and keep only the snippets you'd like then rename _styling.css back to styling.css.",
            msg_type="warning",
        )
        fs.open_thing(os.path.join(current_dir, "_styling.css"))
        fs.open_thing(current_dir)
