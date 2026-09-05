from unittest.mock import MagicMock

import pytest
from core import base
from core.steam import add_prelaunch_to_launch_options


@pytest.fixture
def mock_frozen_env(monkeypatch):
    monkeypatch.setattr(base, "FROZEN", True)
    monkeypatch.setattr("sys.executable", "/path/to/minify")

    mock_accounts = [{"id": "123", "name": "User"}]
    monkeypatch.setattr("core.steam.get_steam_accounts", lambda: mock_accounts)

    def config_get_side_effect(key, default=None):
        if key == "apply_for_all":
            return True
        if key == "patch_on_launch":
            return True
        if key == "steam_root":
            return "/fake/steam"
        if key == "steam_id":
            return "123"
        return default

    monkeypatch.setattr("core.config.get", config_get_side_effect)
    monkeypatch.setattr("os.path.exists", lambda path: True)
    monkeypatch.setattr("core.utils.open_utf8R", MagicMock())
    return mock_accounts


def test_not_frozen_returns_false(monkeypatch):
    monkeypatch.setattr(base, "FROZEN", False)
    monkeypatch.setattr("core.config.get", lambda key, default=None: default)
    monkeypatch.setattr("os.path.exists", lambda path: False)

    result = add_prelaunch_to_launch_options()
    assert result is False


def test_patch_on_launch_disabled_returns_false(monkeypatch):
    monkeypatch.setattr(base, "FROZEN", True)
    monkeypatch.setattr("sys.executable", "/path/to/minify")

    def config_get_side_effect(key, default=None):
        if key == "patch_on_launch":
            return False
        if key == "apply_for_all":
            return True
        if key == "steam_root":
            return "/fake/steam"
        if key == "steam_id":
            return "123"
        return default

    monkeypatch.setattr("core.config.get", config_get_side_effect)
    monkeypatch.setattr("core.steam.get_steam_accounts", lambda: [{"id": "123", "name": "User"}])
    monkeypatch.setattr("os.path.exists", lambda path: False)

    result = add_prelaunch_to_launch_options()
    assert result is False


def test_no_command_token_still_adds_prefix(monkeypatch, mock_frozen_env):
    from core import base

    monkeypatch.setattr(base, "is_win", True)
    monkeypatch.setattr(base, "is_linux", False)

    vdf_data = {
        "UserLocalConfigStore": {
            "Software": {
                "Valve": {"Steam": {"apps": {base.STEAM_DOTA_ID: {"LaunchOptions": "-novid -language english"}}}}
            }
        }
    }

    monkeypatch.setattr("vdf.load", lambda f: vdf_data)
    mock_dump = MagicMock()
    monkeypatch.setattr("vdf.dump", mock_dump)

    result = add_prelaunch_to_launch_options()
    assert result is True
    assert mock_dump.called
    assert (
        vdf_data["UserLocalConfigStore"]["Software"]["Valve"]["Steam"]["apps"][base.STEAM_DOTA_ID]["LaunchOptions"]
        == 'cmd /c "/path/to/minify" prelaunch && %command% -novid -language english'
    )


def test_inserts_before_command_windows(monkeypatch, mock_frozen_env):
    from core import base

    monkeypatch.setattr(base, "is_win", True)
    monkeypatch.setattr(base, "is_linux", False)

    vdf_data = {
        "UserLocalConfigStore": {
            "Software": {
                "Valve": {
                    "Steam": {"apps": {base.STEAM_DOTA_ID: {"LaunchOptions": "-novid -language english %command%"}}}
                }
            }
        }
    }

    monkeypatch.setattr("vdf.load", lambda f: vdf_data)
    mock_dump = MagicMock()
    monkeypatch.setattr("vdf.dump", mock_dump)

    result = add_prelaunch_to_launch_options()
    assert result is True
    assert mock_dump.called
    assert (
        vdf_data["UserLocalConfigStore"]["Software"]["Valve"]["Steam"]["apps"][base.STEAM_DOTA_ID]["LaunchOptions"]
        == 'cmd /c "/path/to/minify" prelaunch && %command% -novid -language english'
    )


def test_inserts_before_command_linux(monkeypatch, mock_frozen_env):
    from core import base

    monkeypatch.setattr(base, "is_win", False)
    monkeypatch.setattr(base, "is_linux", True)

    vdf_data = {
        "UserLocalConfigStore": {
            "Software": {
                "Valve": {
                    "Steam": {"apps": {base.STEAM_DOTA_ID: {"LaunchOptions": "-novid -language english %command%"}}}
                }
            }
        }
    }

    monkeypatch.setattr("vdf.load", lambda f: vdf_data)
    mock_dump = MagicMock()
    monkeypatch.setattr("vdf.dump", mock_dump)

    result = add_prelaunch_to_launch_options()
    assert result is True
    assert mock_dump.called
    assert (
        vdf_data["UserLocalConfigStore"]["Software"]["Valve"]["Steam"]["apps"][base.STEAM_DOTA_ID]["LaunchOptions"]
        == 'bash -c "/path/to/minify prelaunch" && %command% -novid -language english'
    )


def test_no_duplicate_insert(monkeypatch, mock_frozen_env):
    from core import base

    monkeypatch.setattr(base, "is_win", True)
    monkeypatch.setattr(base, "is_linux", False)

    vdf_data = {
        "UserLocalConfigStore": {
            "Software": {
                "Valve": {
                    "Steam": {
                        "apps": {
                            base.STEAM_DOTA_ID: {
                                "LaunchOptions": 'cmd /c "/path/to/minify" prelaunch && %command% -novid -language english'
                            }
                        }
                    }
                }
            }
        }
    }

    monkeypatch.setattr("vdf.load", lambda f: vdf_data)
    mock_dump = MagicMock()
    monkeypatch.setattr("vdf.dump", mock_dump)

    result = add_prelaunch_to_launch_options()
    assert result is False
    assert not mock_dump.called
    assert (
        vdf_data["UserLocalConfigStore"]["Software"]["Valve"]["Steam"]["apps"][base.STEAM_DOTA_ID]["LaunchOptions"]
        == 'cmd /c "/path/to/minify" prelaunch && %command% -novid -language english'
    )


def test_path_with_spaces(monkeypatch, mock_frozen_env):
    from core import base

    monkeypatch.setattr(base, "is_win", True)
    monkeypatch.setattr(base, "is_linux", False)
    monkeypatch.setattr("sys.executable", r"C:\Program Files\Dota2 Minify\minify.exe")

    vdf_data = {
        "UserLocalConfigStore": {
            "Software": {"Valve": {"Steam": {"apps": {base.STEAM_DOTA_ID: {"LaunchOptions": "-novid %command%"}}}}}
        }
    }

    monkeypatch.setattr("vdf.load", lambda f: vdf_data)
    mock_dump = MagicMock()
    monkeypatch.setattr("vdf.dump", mock_dump)

    result = add_prelaunch_to_launch_options()
    assert result is True
    assert mock_dump.called
    assert (
        vdf_data["UserLocalConfigStore"]["Software"]["Valve"]["Steam"]["apps"][base.STEAM_DOTA_ID]["LaunchOptions"]
        == r'cmd /c "C:\Program Files\Dota2 Minify\minify.exe" prelaunch && %command% -novid'
    )


def test_multiple_command_tokens(monkeypatch, mock_frozen_env):
    from core import base

    monkeypatch.setattr(base, "is_win", True)
    monkeypatch.setattr(base, "is_linux", False)

    vdf_data = {
        "UserLocalConfigStore": {
            "Software": {
                "Valve": {
                    "Steam": {
                        "apps": {
                            base.STEAM_DOTA_ID: {"LaunchOptions": "-novid -language english %command% -something_else"}
                        }
                    }
                }
            }
        }
    }

    monkeypatch.setattr("vdf.load", lambda f: vdf_data)
    mock_dump = MagicMock()
    monkeypatch.setattr("vdf.dump", mock_dump)

    result = add_prelaunch_to_launch_options()
    assert result is True
    assert mock_dump.called
    assert (
        vdf_data["UserLocalConfigStore"]["Software"]["Valve"]["Steam"]["apps"][base.STEAM_DOTA_ID]["LaunchOptions"]
        == 'cmd /c "/path/to/minify" prelaunch && %command% -novid -language english -something_else'
    )


def test_env_vars_and_wrappers_moved_after_command(monkeypatch, mock_frozen_env):
    from core import base

    monkeypatch.setattr(base, "is_win", True)
    monkeypatch.setattr(base, "is_linux", False)

    vdf_data = {
        "UserLocalConfigStore": {
            "Software": {
                "Valve": {
                    "Steam": {
                        "apps": {
                            base.STEAM_DOTA_ID: {
                                "LaunchOptions": "WAYLAND=1 mangohud %command% -novid -language english"
                            }
                        }
                    }
                }
            }
        }
    }

    monkeypatch.setattr("vdf.load", lambda f: vdf_data)
    mock_dump = MagicMock()
    monkeypatch.setattr("vdf.dump", mock_dump)

    result = add_prelaunch_to_launch_options()
    assert result is True
    assert mock_dump.called
    assert (
        vdf_data["UserLocalConfigStore"]["Software"]["Valve"]["Steam"]["apps"][base.STEAM_DOTA_ID]["LaunchOptions"]
        == 'cmd /c "/path/to/minify" prelaunch && %command% WAYLAND=1 mangohud -novid -language english'
    )


def test_apply_for_all_false(monkeypatch):
    from core import base

    monkeypatch.setattr(base, "FROZEN", True)
    monkeypatch.setattr("sys.executable", "/path/to/minify")
    monkeypatch.setattr(base, "is_win", True)
    monkeypatch.setattr(base, "is_linux", False)

    mock_accounts = [{"id": "123", "name": "User1"}, {"id": "456", "name": "User2"}]

    def config_get_side_effect(key, default=None):
        if key == "apply_for_all":
            return False
        if key == "patch_on_launch":
            return True
        if key == "steam_root":
            return "/fake/steam"
        if key == "steam_id":
            return "123"
        return default

    monkeypatch.setattr("core.config.get", config_get_side_effect)
    monkeypatch.setattr("core.steam.get_steam_accounts", lambda: mock_accounts)
    monkeypatch.setattr("os.path.exists", lambda path: True)
    monkeypatch.setattr("core.utils.open_utf8R", MagicMock())


    vdf_data = {
        "UserLocalConfigStore": {
            "Software": {"Valve": {"Steam": {"apps": {base.STEAM_DOTA_ID: {"LaunchOptions": "-novid %command%"}}}}}
        }
    }

    monkeypatch.setattr("vdf.load", lambda f: vdf_data)
    mock_dump = MagicMock()
    monkeypatch.setattr("vdf.dump", mock_dump)

    result = add_prelaunch_to_launch_options()
    assert result is True
    assert mock_dump.called
    assert (
        vdf_data["UserLocalConfigStore"]["Software"]["Valve"]["Steam"]["apps"][base.STEAM_DOTA_ID]["LaunchOptions"]
        == 'cmd /c "/path/to/minify" prelaunch && %command% -novid'
    )


def test_missing_launch_options(monkeypatch, mock_frozen_env):

    vdf_data = {"UserLocalConfigStore": {"Software": {"Valve": {"Steam": {"apps": {base.STEAM_DOTA_ID: {}}}}}}}

    monkeypatch.setattr("vdf.load", lambda f: vdf_data)
    mock_dump = MagicMock()
    monkeypatch.setattr("vdf.dump", mock_dump)

    result = add_prelaunch_to_launch_options()
    assert result is False
    assert not mock_dump.called


def test_missing_vdf_file(monkeypatch, mock_frozen_env):
    monkeypatch.setattr("os.path.exists", lambda path: False)

    result = add_prelaunch_to_launch_options()
    assert result is False


def test_empty_launch_options(monkeypatch, mock_frozen_env):
    from core import base

    monkeypatch.setattr(base, "is_win", True)
    monkeypatch.setattr(base, "is_linux", False)

    vdf_data = {
        "UserLocalConfigStore": {
            "Software": {"Valve": {"Steam": {"apps": {base.STEAM_DOTA_ID: {"LaunchOptions": ""}}}}}
        }
    }

    monkeypatch.setattr("vdf.load", lambda f: vdf_data)
    mock_dump = MagicMock()
    monkeypatch.setattr("vdf.dump", mock_dump)

    result = add_prelaunch_to_launch_options()
    assert result is True
    assert mock_dump.called
    assert (
        vdf_data["UserLocalConfigStore"]["Software"]["Valve"]["Steam"]["apps"][base.STEAM_DOTA_ID]["LaunchOptions"]
        == 'cmd /c "/path/to/minify" prelaunch && %command%'
    )
