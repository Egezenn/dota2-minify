import os
import sys
import builtins
import pytest
from unittest.mock import MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Minify")))

# We can bypass the initialization logic in `steam.py` by mocking the `handle_non_default_path`
# and `get_steam_root_path` before the module executes it. But Python executes module-level
# code immediately upon import.

# One trick is to patch `core.config.get` to return a valid path so it passes os.path.exists checks
# and skips the tkinter block.
import core.config


def fake_config_get(key, default=""):
    if key == "steam_library" or key == "steam_root":
        return os.path.dirname(os.path.abspath(__file__))  # Any valid dir
    return default


core.config.get = MagicMock(side_effect=fake_config_get)
core.config.set = MagicMock()

# create a dummy base.DOTA_EXECUTABLE_PATH file
import core.base

dummy_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), core.base.DOTA_EXECUTABLE_PATH)
os.makedirs(os.path.dirname(dummy_exe), exist_ok=True)
with open(dummy_exe, "w") as f:
    f.write("")

from core.steam import remove_lang_args


@pytest.mark.parametrize(
    "input_string, expected",
    [
        # Empty/None cases
        (None, ""),
        ("", ""),
        ("   ", ""),
        # Normal cases
        ("-language english -console", "-console"),
        ("-novid -language turkish -console +fps_max 60", "-novid -console +fps_max 60"),
        # No language flag
        ("-console -novid", "-console -novid"),
        # Trailing without value
        ("-console -language", "-console"),
        # Followed by another flag
        ("-language -console", "-console"),
        ("-language +fps_max 60 -console", "+fps_max 60 -console"),
        # Multiple language flags
        ("-language english -console -language russian", "-console"),
        ("-language english -language turkish", ""),
        # Edge cases
        ("-language", ""),
        ("-language english", ""),
    ],
)
def test_remove_lang_args(input_string, expected):
    assert remove_lang_args(input_string) == expected
