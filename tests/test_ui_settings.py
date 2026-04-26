import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../Minify")))


@pytest.fixture
def mock_dpg():
    with patch("ui.settings.dpg") as mock:
        yield mock


@pytest.fixture
def mock_config():
    with patch("ui.settings.config") as mock:
        mock.get_mod.return_value = {}
        yield mock


def test_apply_preset(mock_dpg, mock_config):
    from ui.settings import apply_preset

    mock_dpg.get_value.return_value = "Preset Name"

    mock_config.get_mod.return_value = {"existing_key": "existing_value"}

    user_data = {
        "mod_name": "TestMod",
        "combo_tag": "preset_combo_TestMod",
        "presets": [{"name": "Preset Name", "values": {"setting1": "value1", "setting2": 42}}],
    }

    with patch("ui.settings.refresh") as mock_refresh:
        apply_preset(None, None, user_data)

        mock_config.set_mod.assert_called_once_with(
            "TestMod", {"existing_key": "existing_value", "setting1": "value1", "setting2": 42}
        )
        mock_refresh.assert_called_once()


def test_apply_preset_not_found(mock_dpg, mock_config):
    from ui.settings import apply_preset

    mock_dpg.get_value.return_value = "Unknown Preset"

    user_data = {
        "mod_name": "TestMod",
        "combo_tag": "preset_combo_TestMod",
        "presets": [{"name": "Preset Name", "values": {"setting1": "value1"}}],
    }

    with patch("ui.settings.refresh") as mock_refresh:
        apply_preset(None, None, user_data)

        mock_config.set_mod.assert_not_called()
        mock_refresh.assert_not_called()
