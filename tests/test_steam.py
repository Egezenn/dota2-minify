from unittest.mock import MagicMock

import pytest
from core.steam import remove_lang_args, remove_minify_lang, remove_specific_lang_arg


def test_remove_specific_lang_arg():
    # Test removing a specific language
    assert remove_specific_lang_arg("-language minify -novid", "minify") == "-novid"
    assert remove_specific_lang_arg("-novid -language minify", "minify") == "-novid"
    assert remove_specific_lang_arg("-language english -language minify", "minify") == "-language english"
    assert remove_specific_lang_arg("-language minify -language english", "minify") == "-language english"

    # Test when language is not present
    assert remove_specific_lang_arg("-novid", "minify") == "-novid"

    # Test when different language is present
    assert remove_specific_lang_arg("-language english", "minify") == "-language english"

    # Test empty string
    assert remove_specific_lang_arg("", "minify") == ""

    # Test None
    assert remove_specific_lang_arg(None, "minify") == ""


@pytest.fixture
def mock_steam_env(monkeypatch):
    mock_accounts = [{"id": "123", "name": "User"}]
    monkeypatch.setattr("core.steam.get_steam_accounts", lambda: mock_accounts)

    def config_get_side_effect(key, default=None):
        if key == "apply_for_all":
            return True
        if key == "steam_root":
            return "/fake/steam"
        if key == "output_locale":
            return "minify"
        if key == "steam_id":
            return "123"
        return default

    monkeypatch.setattr("core.config.get", config_get_side_effect)
    return mock_accounts


def test_remove_minify_lang_success(mock_steam_env, monkeypatch):
    import vdf
    from core import base

    # Mock VDF data
    vdf_data = {
        "UserLocalConfigStore": {
            "Software": {
                "Valve": {"Steam": {"apps": {base.STEAM_DOTA_ID: {"LaunchOptions": "-language minify -novid"}}}}
            }
        }
    }

    monkeypatch.setattr("os.path.exists", lambda path: True)
    monkeypatch.setattr("core.utils.open_utf8R", MagicMock())
    monkeypatch.setattr("core.utils.open_utf8", MagicMock())
    monkeypatch.setattr("vdf.load", lambda f: vdf_data)

    mock_dump = MagicMock()
    monkeypatch.setattr("vdf.dump", mock_dump)

    result = remove_minify_lang()

    assert result == ["123"]
    assert (
        vdf_data["UserLocalConfigStore"]["Software"]["Valve"]["Steam"]["apps"][base.STEAM_DOTA_ID]["LaunchOptions"]
        == "-novid"
    )
    assert mock_dump.called


def test_remove_minify_lang_wrong_locale(mock_steam_env, monkeypatch):
    import vdf

    def config_get_side_effect(key, default=None):
        if key == "apply_for_all":
            return True
        if key == "steam_root":
            return "/fake/steam"
        if key == "output_locale":
            return "english"  # Not minify
        return default

    monkeypatch.setattr("core.config.get", config_get_side_effect)
    monkeypatch.setattr("os.path.exists", lambda path: True)

    mock_load = MagicMock(return_value={})
    monkeypatch.setattr("vdf.load", mock_load)
    mock_dump = MagicMock()
    monkeypatch.setattr("vdf.dump", mock_dump)
    monkeypatch.setattr("core.utils.open_utf8R", MagicMock())

    result = remove_minify_lang()

    assert result == []
    assert mock_load.called
    assert not mock_dump.called


def test_remove_minify_lang_no_vdf(mock_steam_env, monkeypatch):
    monkeypatch.setattr("os.path.exists", lambda path: False)

    result = remove_minify_lang()
    assert result == []


def test_remove_minify_lang_no_language_arg(mock_steam_env, monkeypatch):
    import vdf
    from core import base

    vdf_data = {
        "UserLocalConfigStore": {
            "Software": {"Valve": {"Steam": {"apps": {base.STEAM_DOTA_ID: {"LaunchOptions": "-novid"}}}}}
        }
    }

    monkeypatch.setattr("os.path.exists", lambda path: True)
    monkeypatch.setattr("core.utils.open_utf8R", MagicMock())
    monkeypatch.setattr("vdf.load", lambda f: vdf_data)
    mock_dump = MagicMock()
    monkeypatch.setattr("vdf.dump", mock_dump)

    result = remove_minify_lang()

    assert result == []
    assert not mock_dump.called


def test_remove_minify_lang_single_id(mock_steam_env, monkeypatch):
    import vdf
    from core import base

    # Set apply_for_all to False
    def config_get_side_effect(key, default=None):
        if key == "apply_for_all":
            return False
        if key == "steam_id":
            return "123"
        if key == "steam_root":
            return "/fake/steam"
        if key == "output_locale":
            return "minify"
        return default

    monkeypatch.setattr("core.config.get", config_get_side_effect)

    vdf_data = {
        "UserLocalConfigStore": {
            "Software": {
                "Valve": {"Steam": {"apps": {base.STEAM_DOTA_ID: {"LaunchOptions": "-language minify -novid"}}}}
            }
        }
    }

    monkeypatch.setattr("os.path.exists", lambda path: True)
    monkeypatch.setattr("core.utils.open_utf8R", MagicMock())
    monkeypatch.setattr("core.utils.open_utf8", MagicMock())
    monkeypatch.setattr("vdf.load", lambda f: vdf_data)
    mock_dump = MagicMock()
    monkeypatch.setattr("vdf.dump", mock_dump)

    result = remove_minify_lang()

    assert result == ["123"]
    assert mock_dump.called


def test_remove_minify_lang_no_launch_options(mock_steam_env, monkeypatch):
    import vdf
    from core import base

    vdf_data = {
        "UserLocalConfigStore": {
            "Software": {"Valve": {"Steam": {"apps": {base.STEAM_DOTA_ID: {}}}}}  # Missing LaunchOptions
        }
    }

    monkeypatch.setattr("os.path.exists", lambda path: True)
    monkeypatch.setattr("core.utils.open_utf8R", MagicMock())
    monkeypatch.setattr("vdf.load", lambda f: vdf_data)

    result = remove_minify_lang()
    assert result == []


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
