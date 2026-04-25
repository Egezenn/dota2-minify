import os
import sys
from unittest.mock import MagicMock

# 1. Add Minify and scripts to sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
minify_dir = os.path.join(root_dir, "Minify")
scripts_dir = os.path.join(root_dir, "scripts")

# Change CWD to Minify so relative paths (logs/, config/, etc.) go there
os.chdir(minify_dir)

sys.path.insert(0, minify_dir)
sys.path.insert(0, scripts_dir)

# isort: split

# Create logs directory for side effects
from core import base

os.makedirs(base.logs_dir, exist_ok=True)

# 2. Mock core.config early
import core.config


def fake_config_get(key, default=None):
    if key in ("steam_root", "steam_library"):
        return "/fake/steam"
    if key == "apply_for_all":
        return True
    if key == "output_locale":
        return "minify"
    return default


core.config.get = MagicMock(side_effect=fake_config_get)
core.config.set = MagicMock()

# 3. Mock UI and other side-effect heavy modules
sys.modules["ui.terminal"] = MagicMock()
sys.modules["tkinter"] = MagicMock()
sys.modules["tkinter.filedialog"] = MagicMock()
sys.modules["tkinter.messagebox"] = MagicMock()
sys.modules["playsound3"] = MagicMock()

# 4. Mock os.path.exists to avoid entering the steam discovery loops
import os
from core import base

original_exists = os.path.exists


def fake_exists(path):
    if "/fake/steam" in path or "steamapps" in path or "dota" in path or path == base.mods_dir:
        return True
    return original_exists(path)


os.path.exists = fake_exists

original_listdir = os.listdir


def fake_listdir(path):
    if path == base.mods_dir:
        return []
    return original_listdir(path)


os.listdir = fake_listdir
