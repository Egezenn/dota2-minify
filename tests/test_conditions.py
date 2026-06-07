import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../Minify")))

from core import base


def test_check_workshop_tools():
    import conditions

    # 1. StateFlags = "4" (fully installed) and optionaldlc contains the correct ID
    fake_app_state_1 = {
        "StateFlags": "4",
        "MountedConfig": {"optionaldlc": base.STEAM_DOTA_WORKSHOP_TOOLS_ID, "DisabledDLC": ""},
    }
    with patch("conditions.get_dota_app_state", return_value=fake_app_state_1):
        assert conditions.check_workshop_tools() is True

    # 2. StateFlags = "6" (installed but update required) and optionaldlc contains the correct ID
    fake_app_state_2 = {
        "StateFlags": "6",
        "MountedConfig": {"optionaldlc": base.STEAM_DOTA_WORKSHOP_TOOLS_ID, "DisabledDLC": ""},
    }
    with patch("conditions.get_dota_app_state", return_value=fake_app_state_2):
        assert conditions.check_workshop_tools() is True

    # 3. StateFlags = "2" (not installed)
    fake_app_state_3 = {
        "StateFlags": "2",
        "MountedConfig": {"optionaldlc": base.STEAM_DOTA_WORKSHOP_TOOLS_ID, "DisabledDLC": ""},
    }
    with patch("conditions.get_dota_app_state", return_value=fake_app_state_3):
        assert conditions.check_workshop_tools() is False

    # 4. StateFlags = invalid/non-integer
    fake_app_state_4 = {
        "StateFlags": "invalid",
        "MountedConfig": {"optionaldlc": base.STEAM_DOTA_WORKSHOP_TOOLS_ID, "DisabledDLC": ""},
    }
    with patch("conditions.get_dota_app_state", return_value=fake_app_state_4):
        assert conditions.check_workshop_tools() is False

    # 5. Workshop tools DLC is disabled
    fake_app_state_5 = {
        "StateFlags": "6",
        "MountedConfig": {
            "optionaldlc": base.STEAM_DOTA_WORKSHOP_TOOLS_ID,
            "DisabledDLC": base.STEAM_DOTA_WORKSHOP_TOOLS_ID,
        },
    }
    with patch("conditions.get_dota_app_state", return_value=fake_app_state_5):
        assert conditions.check_workshop_tools() is False
