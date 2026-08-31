from unittest.mock import MagicMock, patch

import plugins
from core import registry


def test_plugin_registry():
    registry.PluginRegistry.clear()
    assert len(registry.get_plugins()) == 0

    dummy_plugin = MagicMock()
    registry.register_plugin(dummy_plugin)
    assert len(registry.get_plugins()) == 1
    assert registry.get_plugins()[0] == dummy_plugin

    # Duplicate registration should be ignored
    registry.register_plugin(dummy_plugin)
    assert len(registry.get_plugins()) == 1

    registry.PluginRegistry.clear()
    assert len(registry.get_plugins()) == 0


def test_dynamic_plugin_discovery():
    plugins.initialize()
    active_plugins = registry.get_plugins()
    assert len(active_plugins) >= 1

    plugin_names = [getattr(p, "__name__", str(p)) for p in active_plugins]
    assert any("d2pfx" in p_name for p_name in plugin_names)


def test_plugin_build_and_uninstall_hooks():
    plugins.initialize()
    active_plugins = registry.get_plugins()
    assert len(active_plugins) > 0

    target_plugin = active_plugins[0]
    with (
        patch.object(target_plugin, "on_build", create=True) as mock_build,
        patch.object(target_plugin, "on_uninstall", create=True) as mock_unins,
    ):
        for p in registry.get_plugins():
            if hasattr(p, "on_build"):
                p.on_build(["test_mod"])

        mock_build.assert_called_once_with(["test_mod"])

        for p in registry.get_plugins():
            if hasattr(p, "on_uninstall"):
                p.on_uninstall()

        mock_unins.assert_called_once()


def test_plugin_tabs_filtered_when_unbuilt():
    from ui.app import Api

    api = Api()
    with patch.object(api, "_resolve_plugin_entry", return_value=None):
        tabs = api.get_plugin_tabs()
        assert tabs == []


def test_get_plugin_content_inlining():
    from ui.app import Api

    api = Api()
    content = api.get_plugin_content("d2pfx")
    if content:
        assert "<script" in content or "<style" in content


def test_plugin_settings_json_discovery():
    from ui.app import Api

    api = Api()
    settings_data = api.get_settings()
    schema = settings_data["schema"]
    plugin_setting_keys = [item["key"] for item in schema if item.get("plugin") == "d2pfx"]
    assert "d2pfx_auto_refresh_catalogue" in plugin_setting_keys


def test_call_plugin_api():
    from ui.app import Api

    api = Api()
    res = api.call_plugin_api("d2pfx", "get_installed_mods")
    assert isinstance(res, list)


def test_demo_plain_js_plugin(tmp_path):
    from ui.app import Api

    demo_dir = tmp_path / "demo"
    demo_dir.mkdir()
    api_file = demo_dir / "api.py"
    api_file.write_text("def ping(params):\n    return {'status': 'success', 'echo': params.get('message')}\n")

    with patch("core.base.plugins_dir", str(tmp_path)):
        api = Api()
        res = api.call_plugin_api("demo", "ping", {"message": "Hello Test"})
        assert res.get("status") == "success"
        assert res.get("echo") == "Hello Test"
