from unittest.mock import MagicMock

import pytest
from core.constants import resolve_locale
from core.steam import (
    fix_launch_options,
    remove_lang_args,
    remove_minify_lang,
    remove_specific_lang_arg,
    restore_boot_language,
)


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


def test_resolve_locale():
    assert resolve_locale("dutch") == "dutch"
    assert resolve_locale("english") == "dutch"
    assert resolve_locale("minify") == "minify"
    assert resolve_locale("french") == "french"
    assert resolve_locale("unknown") == "unknown"


def test_remove_minify_lang_success(mock_steam_env, monkeypatch):
    from core import base

    # English locale should resolve to dutch and remove -language dutch
    def config_get_side_effect(key, default=None):
        if key == "apply_for_all":
            return True
        if key == "steam_root":
            return "/fake/steam"
        if key == "output_locale":
            return "english"
        if key == "steam_id":
            return "123"
        return default

    monkeypatch.setattr("core.config.get", config_get_side_effect)

    vdf_data = {
        "UserLocalConfigStore": {
            "Software": {
                "Valve": {"Steam": {"apps": {base.STEAM_DOTA_ID: {"LaunchOptions": "-language dutch -novid"}}}}
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

    def config_get_side_effect(key, default=None):
        if key == "apply_for_all":
            return True
        if key == "steam_root":
            return "/fake/steam"
        if key == "output_locale":
            return "french"  # Not dutch/english
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
    from core import base

    # English locale should resolve to dutch
    def config_get_side_effect(key, default=None):
        if key == "apply_for_all":
            return False
        if key == "steam_id":
            return "123"
        if key == "steam_root":
            return "/fake/steam"
        if key == "output_locale":
            return "english"
        return default

    monkeypatch.setattr("core.config.get", config_get_side_effect)

    vdf_data = {
        "UserLocalConfigStore": {
            "Software": {
                "Valve": {"Steam": {"apps": {base.STEAM_DOTA_ID: {"LaunchOptions": "-language dutch -novid"}}}}
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


def test_fix_launch_options_no_change_needed(monkeypatch):
    from core import base

    def config_get_side_effect(key, default=None):
        if key == "apply_for_all":
            return True
        if key == "steam_root":
            return "/fake/steam"
        if key == "output_locale":
            return "dutch"
        if key == "steam_id":
            return "123"
        return default

    monkeypatch.setattr("core.config.get", config_get_side_effect)
    monkeypatch.setattr("core.steam.get_steam_accounts", lambda: [{"id": "123", "name": "User"}])

    vdf_data = {
        "UserLocalConfigStore": {
            "Software": {
                "Valve": {"Steam": {"apps": {base.STEAM_DOTA_ID: {"LaunchOptions": "-language dutch -novid"}}}}
            }
        }
    }

    monkeypatch.setattr("os.path.exists", lambda path: True)
    monkeypatch.setattr("core.utils.open_utf8R", MagicMock())
    monkeypatch.setattr("vdf.load", lambda f: vdf_data)
    mock_dump = MagicMock()
    monkeypatch.setattr("vdf.dump", mock_dump)

    result = fix_launch_options()
    assert result == []
    assert not mock_dump.called


def test_restore_boot_language_restores_to_english(monkeypatch):

    def config_get_side_effect(key, default=None):
        if key == "output_locale":
            return "english"
        return default

    monkeypatch.setattr("core.config.get", config_get_side_effect)

    vdf_data = {"boot": {"UILanguage": "dutch", "AudioLanguage": "english"}}
    monkeypatch.setattr("os.path.exists", lambda path: True)
    monkeypatch.setattr("core.utils.open_utf8R", MagicMock())
    monkeypatch.setattr("core.utils.open_utf8", MagicMock())
    monkeypatch.setattr("vdf.load", lambda f: vdf_data)
    mock_dump = MagicMock()
    monkeypatch.setattr("vdf.dump", mock_dump)

    assert restore_boot_language() is True
    assert vdf_data["boot"]["UILanguage"] == "english"
    assert vdf_data["boot"]["AudioLanguage"] == "english"
    assert mock_dump.called


def test_restore_boot_language_wrong_locale(monkeypatch):

    def config_get_side_effect(key, default=None):
        if key == "output_locale":
            return "french"
        return default

    monkeypatch.setattr("core.config.get", config_get_side_effect)
    mock_dump = MagicMock()
    monkeypatch.setattr("vdf.dump", mock_dump)

    assert restore_boot_language() is False
    assert not mock_dump.called


def test_restore_boot_language_not_dutch(monkeypatch):

    monkeypatch.setattr("core.config.get", lambda key, default=None: "english" if key == "output_locale" else default)

    vdf_data = {"boot": {"UILanguage": "english", "AudioLanguage": "english"}}
    monkeypatch.setattr("os.path.exists", lambda path: True)
    monkeypatch.setattr("core.utils.open_utf8R", MagicMock())
    monkeypatch.setattr("core.utils.open_utf8", MagicMock())
    monkeypatch.setattr("vdf.load", lambda f: vdf_data)
    mock_dump = MagicMock()
    monkeypatch.setattr("vdf.dump", mock_dump)

    assert restore_boot_language() is False
    assert not mock_dump.called


def test_restore_boot_language_no_vcfg(monkeypatch):

    monkeypatch.setattr("core.config.get", lambda key, default=None: "english" if key == "output_locale" else default)
    monkeypatch.setattr("os.path.exists", lambda path: False)
    mock_dump = MagicMock()
    monkeypatch.setattr("vdf.dump", mock_dump)

    assert restore_boot_language() is False
    assert not mock_dump.called


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
