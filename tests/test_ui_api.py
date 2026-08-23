from unittest.mock import patch

from ui import Api


def test_api_endpoints():
    api = Api()

    # Test get_localization
    loc = api.get_localization("EN")
    assert isinstance(loc, dict)
    assert len(loc) > 0

    # Test get_mods
    mods = api.get_mods()
    assert isinstance(mods, list)

    # Test set_mods
    if mods:
        test_mod = mods[0]["name"]
        initial_state = mods[0]["enabled"]
        new_state = not initial_state

        with patch("core.mods_shared.set_state") as mock_set:
            res = api.set_mods({test_mod: new_state})
            assert res is True
            mock_set.assert_called_with(test_mod, new_state)

    # Test settings
    settings_data = api.get_settings()
    assert "schema" in settings_data
    assert "values" in settings_data
    assert len(settings_data["schema"]) == 7

    with patch("core.config.set") as mock_config_set:
        res = api.set_setting("patch_on_launch", True)
        assert res is True
        mock_config_set.assert_called_with("patch_on_launch", True)
