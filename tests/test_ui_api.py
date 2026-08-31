from unittest.mock import MagicMock, patch

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
    assert len(settings_data["schema"]) >= 7

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

    # Test start_uninstall
    with patch("patch.unins.uninstall") as mock_unins:
        res = api.start_uninstall(remove_everything=False)
        assert res["status"] in ("started", "already_running")


def test_visual_and_always_manifest_options():
    import os

    from core import base

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


def test_mod_settings_injection():
    import os

    from core import base

    real_isdir = os.path.isdir

    def mock_listdir(path):
        if path == base.mods_dir:
            return ["TestMod"]
        return []

    def mock_isdir(path):
        if base.mods_dir in path:
            return True
        return real_isdir(path)

    manifest_settings = [
        {
            "key": "example_inputbox",
            "text": "Display Name",
            "force": False,
            "default": "example_value",
            "type": "inputbox",
        },
        {
            "key": "example_checkbox",
            "text": "Enable Feature",
            "force": False,
            "default": False,
            "type": "checkbox",
        },
        {
            "key": "example_combo",
            "text": "Select Option",
            "force": False,
            "default": "Value 1",
            "type": "combo",
            "items": ["Value 1", "Value 2"],
        },
        {
            "key": "example_number",
            "text": "Number",
            "force": False,
            "default": 10,
            "type": "number",
            "var_type": "int",
            "step": 1,
        },
        {
            "key": "example_slider",
            "text": "Slider",
            "force": False,
            "default": 50,
            "type": "slider",
            "min": 0,
            "max": 100,
            "var_type": "int",
            "step": 5,
        },
        {
            "key": "example_color",
            "text": "Color",
            "force": False,
            "default": "#ff0000ff",
            "type": "color",
        },
        {
            "key": "example_list",
            "text": "List",
            "force": False,
            "default": ["Item 1", "Item 2"],
            "type": "list",
        },
        {
            "key": "example_function",
            "text": "Function",
            "force": False,
            "type": "button",
        },
    ]

    def mock_get_mod(path):
        return {"settings": manifest_settings}

    with (
        patch("os.listdir", side_effect=mock_listdir),
        patch("os.path.isdir", side_effect=mock_isdir),
        patch("patch.manifest_utils.get_mod", side_effect=mock_get_mod),
        patch("core.mods_shared.get_state", return_value=True),
        patch("core.config.get_mod", return_value={"example_inputbox": "custom_val"}),
    ):
        api = Api()
        res = api.get_settings()
        schema = res["schema"]
        values = res["values"]

        mod_items = [item for item in schema if item.get("mod") == "TestMod"]
        assert len(mod_items) == 8

        # Verify values
        assert values["example_inputbox"] == "custom_val"
        assert values["example_checkbox"] is False
        assert values["example_combo"] == "Value 1"
        assert values["example_number"] == 10
        assert values["example_slider"] == 50
        assert values["example_color"] == "#ff0000ff"
        assert values["example_list"] == ["Item 1", "Item 2"]

    # Test set_setting with mod setting
    with patch("core.config.set_mod") as mock_set_mod, patch("core.config.get_mod", return_value={}):
        res = api.set_setting("example_inputbox", "new_val", "TestMod")
        assert res is True
        mock_set_mod.assert_called_with("TestMod", {"example_inputbox": "new_val"})

    # Test run_mod_function
    with (
        patch("os.path.exists", return_value=True),
        patch("helper.exec_script_function") as mock_exec_func,
    ):
        res = api.run_mod_function("TestMod", "example_function")
        assert res is True
        mock_exec_func.assert_called_once()

    # Test reset_native_settings and reset_mod_settings
    with (
        patch("core.config.set") as mock_config_set,
        patch("core.config.get", return_value={"TestMod": {"example_inputbox": "val"}}),
    ):
        assert api.reset_native_settings() is True
        assert api.reset_mod_settings("TestMod") is True
        mock_config_set.assert_called_with("modconf", {})


def test_set_game_language_updates_output_path():
    import helper

    config_store = {"output_locale": "english", "output_path": ""}

    def mock_get(key, default=None):
        return config_store.get(key, default)

    def mock_set(key, val):
        config_store[key] = val
        return val

    with patch("core.config.get", side_effect=mock_get), patch("core.config.set", side_effect=mock_set):
        api = Api()

        # Set to turkish
        assert api.set_game_language("turkish") is True
        assert config_store["output_locale"] == "turkish"
        assert isinstance(config_store["output_path"], str)
        assert "dota_turkish" in config_store["output_path"]
        assert isinstance(helper.output_path, str)
        assert "dota_turkish" in helper.output_path

        # Set back to english (which uses dutch fallback)
        assert api.set_game_language("english") is True
        assert config_store["output_locale"] == "english"
        assert isinstance(config_store["output_path"], str)
        assert "dota_dutch" in config_store["output_path"]
        assert isinstance(helper.output_path, str)
        assert "dota_dutch" in helper.output_path


def test_ui_pickers():
    from ui.pickers import pick_file

    with patch("webview.windows", [MagicMock()]):
        webview_win = __import__("webview").windows[0]
        webview_win.create_file_dialog.return_value = ["/path/to/test.png"]

        res = pick_file("Test Title", ("*.png",))
        assert res == "/path/to/test.png"


def test_ui_alerts():
    from core import localization
    from ui.alerts import alert

    localization.localization_dict["test_alert_key"] = "Hello {0}!"

    with patch("webview.windows", [MagicMock()]):
        webview_win = __import__("webview").windows[0]

        alert("&test_alert_key", "World", msg_type="info")
        webview_win.evaluate_js.assert_called_once_with('alert("[Notice] Hello World!");')
