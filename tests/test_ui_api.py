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

    # Test get_mod_details
    details = api.get_mod_details("Dark Terrain", "EN")
    assert isinstance(details, dict)
    assert details["name"] == "Dark Terrain"
    assert "has_notes" in details
    assert "has_preview" in details
    if details["has_notes"]:
        assert isinstance(details["notes"], str)
    if details["has_preview"]:
        assert details["preview"].startswith("data:image/")

    # Test get_mod_details for non-existent mod
    non_existent = api.get_mod_details("NonExistentMod123")
    assert non_existent["has_notes"] is False
    assert non_existent["has_preview"] is False

    # Test is_debug_env
    assert isinstance(api.is_debug_env(), bool)


def test_visual_and_always_manifest_options():
    import os
    from core import base, mods_shared

    real_isdir = os.path.isdir

    def mock_listdir(path):
        if path == base.mods_dir:
            return ["AlwaysMod", "HiddenMod", "NormalMod"]
        return []

    def mock_isdir(path):
        if base.mods_dir in path:
            return True
        return real_isdir(path)

    def mock_get_mod(path):
        mod_name = os.path.basename(path)
        if mod_name == "AlwaysMod":
            return {"always": True}
        elif mod_name == "HiddenMod":
            return {"visual": False}
        return {}

    with (
        patch("os.listdir", side_effect=mock_listdir),
        patch("os.path.isdir", side_effect=mock_isdir),
        patch("patch.manifest_utils.get_mod", side_effect=mock_get_mod),
    ):
        api = Api()
        mods = api.get_mods()
        mods_dict = {m["name"]: m for m in mods}

        # AlwaysMod (always: true) should be in UI grid with always=True, enabled=True
        assert "AlwaysMod" in mods_dict
        assert mods_dict["AlwaysMod"]["always"] is True
        assert mods_dict["AlwaysMod"]["enabled"] is True

        # NormalMod (default visual: true) should be in UI grid
        assert "NormalMod" in mods_dict
        assert mods_dict["NormalMod"]["always"] is False

        # HiddenMod (visual: false) must be excluded from UI grid
        assert "HiddenMod" not in mods_dict

