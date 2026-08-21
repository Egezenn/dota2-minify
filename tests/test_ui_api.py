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
