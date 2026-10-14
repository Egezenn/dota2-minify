import io
import json
import zipfile

import pytest

from core import base
from plugins.community import api as community_api


def _zip_bytes(files):
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as zipped:
        for name, contents in files.items():
            zipped.writestr(name, contents)
    return archive.getvalue()


@pytest.fixture
def registry_environment(tmp_path, monkeypatch):
    root = tmp_path / "Minify"
    mods = root / "mods"
    plugins = root / "plugins"
    themes = root / "themes"
    cache = root / "cache"
    for path in (mods, plugins, themes, cache):
        path.mkdir(parents=True)

    monkeypatch.setattr(base, "base_dir", str(root))
    monkeypatch.setattr(base, "mods_dir", str(mods))
    monkeypatch.setattr(base, "plugins_dir", str(plugins))
    monkeypatch.setattr(base, "themes_dir", str(themes))
    monkeypatch.setattr(base, "cache_dir", str(cache))

    state = {}

    def read_states():
        return json.loads(json.dumps(state))

    def write_states(key, value):
        state[key] = value

    monkeypatch.setattr(community_api.utils, "read_states", read_states)
    monkeypatch.setattr(community_api.utils, "write_states", write_states)
    monkeypatch.setattr(community_api.mods_shared, "set_state", lambda *_args: None)
    monkeypatch.setattr(community_api.mods_shared, "scan_mods", lambda: None)
    monkeypatch.setattr(community_api, "_refresh_plugin_runtime", lambda _plugin_id: None)

    return root, mods, plugins, themes, state


@pytest.mark.parametrize(
    ("item", "files", "expected_path", "extra_record"),
    [
        (
            {"type": "mod", "name": "Example Mod", "repo": "https://github.com/test/mod"},
            {"manifest.json": '{"name":"Example Mod"}', "files/example.txt": "mod"},
            "mods/Example Mod",
            {},
        ),
        (
            {"type": "plugin", "name": "Example Plugin", "repo": "https://github.com/test/plugin"},
            {
                "manifest.json": '{"id":"example-plugin","name":"Example Plugin"}',
                "ui/index.html": "<html></html>",
            },
            "plugins/Example Plugin",
            {"plugin_id": "example-plugin"},
        ),
    ],
)
def test_folder_package_install_and_uninstall(
    registry_environment, monkeypatch, item, files, expected_path, extra_record
):
    _root, _mods, _plugins, _themes, state = registry_environment
    payload = _zip_bytes(files)

    def download(_url, target_path, **_kwargs):
        with open(target_path, "wb") as archive:
            archive.write(payload)
        return True

    monkeypatch.setattr(community_api.fs, "download_file", download)
    item_id = community_api._item_key(item["type"], item["name"])
    record = community_api._install_package(item, {"tag": "v1.0", "asset_url": "https://example.test/item.zip"}, None)
    assert record["path"] == expected_path
    assert record["tag"] == "v1.0"
    assert {key: record[key] for key in extra_record} == extra_record
    assert state[community_api.STATES_KEY][item_id] == record

    community_api.uninstall_item({"id": item_id})
    assert item_id not in state[community_api.STATES_KEY]
    assert not (_root / expected_path).exists()


def test_theme_tracks_each_file_and_removes_only_owned_files(registry_environment, monkeypatch):
    _root, _mods, _plugins, themes, state = registry_environment
    unrelated = themes / "unrelated.txt"
    unrelated.write_text("keep")
    payload = _zip_bytes({"theme.css": "body { color: white }", "wallpaper.png": "image"})

    def download(_url, target_path, **_kwargs):
        with open(target_path, "wb") as archive:
            archive.write(payload)
        return True

    monkeypatch.setattr(community_api.fs, "download_file", download)
    item = {"type": "theme", "name": "Glass Theme", "repo": "https://github.com/test/theme"}
    item_id = community_api._item_key("theme", item["name"])
    record = community_api._install_package(item, {"tag": "v1", "asset_url": "https://example.test/theme.zip"}, None)
    assert set(record["files"]) == {"themes/Glass Theme.css", "themes/wallpaper.png"}
    assert (themes / "Glass Theme.css").is_file()
    assert (themes / "wallpaper.png").is_file()

    monkeypatch.setattr(community_api.config, "get", lambda key, default=None: "light" if key == "theme" else default)
    community_api.uninstall_item({"id": item_id})
    assert not (themes / "Glass Theme.css").exists()
    assert not (themes / "wallpaper.png").exists()
    assert unrelated.read_text() == "keep"
    assert item_id not in state[community_api.STATES_KEY]


def test_theme_refuses_to_overwrite_untracked_file(registry_environment, monkeypatch):
    _root, _mods, _plugins, themes, _state = registry_environment
    (themes / "shared.png").write_text("original")
    payload = _zip_bytes({"theme.css": "body {}", "shared.png": "replacement"})

    def download(_url, target_path, **_kwargs):
        with open(target_path, "wb") as archive:
            archive.write(payload)
        return True

    monkeypatch.setattr(community_api.fs, "download_file", download)
    item = {"type": "theme", "name": "Theme", "repo": "https://github.com/test/theme"}
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        community_api._install_package(item, {"tag": "v1", "asset_url": "https://example.test/theme.zip"}, None)
    assert (themes / "shared.png").read_text() == "original"


@pytest.mark.parametrize(
    ("item", "first_files", "updated_files", "expected_owned"),
    [
        (
            {"type": "mod", "name": "Update Mod", "repo": "https://github.com/test/mod"},
            {"manifest.json": '{"name":"Update Mod"}', "v1.txt": "one"},
            {"manifest.json": '{"name":"Update Mod"}', "v2.txt": "two"},
            {"v2.txt"},
        ),
        (
            {"type": "plugin", "name": "Update Plugin", "repo": "https://github.com/test/plugin"},
            {"manifest.json": '{"id":"update-plugin"}', "ui/index.html": "v1"},
            {"manifest.json": '{"id":"update-plugin"}', "ui/index.html": "v2"},
            {"ui/index.html"},
        ),
        (
            {"type": "theme", "name": "Update Theme", "repo": "https://github.com/test/theme"},
            {"theme.css": "v1", "old.png": "old"},
            {"theme.css": "v2", "new.png": "new"},
            {"Update Theme.css", "new.png"},
        ),
    ],
)
def test_update_replaces_package_and_refreshes_tracked_files(
    registry_environment, monkeypatch, item, first_files, updated_files, expected_owned
):
    _root, _mods, _plugins, themes, state = registry_environment
    archives = {
        "https://example.test/v1.zip": _zip_bytes(first_files),
        "https://example.test/v2.zip": _zip_bytes(updated_files),
    }

    def download(url, target_path, **_kwargs):
        with open(target_path, "wb") as archive:
            archive.write(archives[url])
        return True

    monkeypatch.setattr(community_api.fs, "download_file", download)
    item_id = community_api._item_key(item["type"], item["name"])
    community_api._install_package(item, {"tag": "v1", "asset_url": "https://example.test/v1.zip"}, None)
    monkeypatch.setattr(community_api, "_get_registry", lambda: [dict(item, versions=[base.VERSION])])
    monkeypatch.setattr(
        community_api,
        "_latest_release",
        lambda _item: {"tag": "v2", "asset_url": "https://example.test/v2.zip"},
    )

    result = community_api.update_item({"id": item_id})
    record = result["installed"]
    assert record["tag"] == "v2"
    if item["type"] == "theme":
        owned = {path.removeprefix("themes/") for path in record["files"]}
        assert owned == expected_owned
        assert not (themes / "old.png").exists()
        assert (themes / "new.png").read_text() == "new"
    else:
        target = _root / record["path"]
        if item["type"] == "mod":
            assert {path.name for path in target.iterdir()} == expected_owned | {"manifest.json"}
            assert not (target / "v1.txt").exists()
            assert (target / "v2.txt").read_text() == "two"
        else:
            assert (target / "ui" / "index.html").read_text() == "v2"
    assert state[community_api.STATES_KEY][item_id]["tag"] == "v2"


def test_plugin_id_resolves_from_registry_name_folder(tmp_path, monkeypatch):
    plugin_dir = tmp_path / "Wiki Browser"
    plugin_dir.mkdir()
    (plugin_dir / "manifest.json").write_text('{"id":"wiki-browser","name":"Wiki"}', encoding="utf-8")
    (plugin_dir / "ui").mkdir()
    (plugin_dir / "ui" / "index.html").write_text("<html>Wiki</html>", encoding="utf-8")
    monkeypatch.setattr(base, "plugins_dir", str(tmp_path))

    from ui.services.plugin_service import PluginService

    service = PluginService()
    assert service._find_plugin_path("wiki-browser") == str(plugin_dir)
    assert service._resolve_plugin_entry(str(plugin_dir)) == str(plugin_dir / "ui" / "index.html")


def test_catalogue_keeps_incompatible_installs_visible(monkeypatch):
    monkeypatch.setattr(base, "VERSION", "2rc6")
    monkeypatch.setattr(
        community_api,
        "_get_registry",
        lambda: [
            {
                "name": "Compatible",
                "type": "mod",
                "releases": {"1.0.0": ["2rc5"], "1.0.1": ["2rc6"]},
            },
            {"name": "Incompatible", "type": "plugin", "releases": {"1.0.0": ["2rc5"]}},
            {"name": "Not Installed", "type": "theme", "releases": {"1.0.0": ["2rc5"]}},
        ],
    )
    monkeypatch.setattr(
        community_api,
        "_install_records",
        lambda: {
            "mod:Compatible": {"tag": "1.0.0"},
            "plugin:Incompatible": {"tag": "1.0.0"},
        },
    )
    monkeypatch.setattr(
        community_api,
        "_latest_release",
        lambda _item: {"tag": "1.0.1", "asset_url": "https://example.test/package.zip"},
    )

    entries = community_api.get_catalogue()
    assert [entry["name"] for entry in entries] == ["Compatible", "Incompatible"]
    assert entries[0]["installed_tag"] == "1.0.0"
    assert entries[0]["installed_compatible"] is False
    assert entries[0]["latest_tag"] == "1.0.1"
    assert entries[0]["update_available"] is True
    assert entries[1]["installed"] is True
    assert entries[1]["installed_compatible"] is False
    assert entries[1]["latest_tag"] is None
    assert entries[1]["update_available"] is False


@pytest.mark.parametrize(
    ("locale", "expected"),
    [("tr", "Turkish notes."), ("de", "English notes."), ("en", "English notes.")],
)
def test_item_details_filters_notes_by_locale(monkeypatch, locale, expected):
    class Response:
        text = "<!-- lang:en -->\n\nEnglish notes.\n\n<!-- lang:tr -->\n\nTurkish notes.\n"

        def raise_for_status(self):
            return None

    monkeypatch.setattr(
        community_api,
        "_get_registry",
        lambda: [{"name": "Example", "type": "mod", "notes": "https://example.test/notes.md"}],
    )
    monkeypatch.setattr(community_api.requests, "get", lambda *_args, **_kwargs: Response())
    monkeypatch.setattr(
        community_api.config,
        "get",
        lambda key, default=None: locale if key == "locale" else default,
    )

    details = community_api.get_item_details({"id": "mod:Example"})
    assert details["notes"] == expected


def test_latest_release_selects_newest_release_compatible_with_minify(monkeypatch):
    monkeypatch.setattr(base, "VERSION", "2rc6")

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return [
                {
                    "tag_name": "1.0.2",
                    "html_url": "https://github.com/test/theme/releases/tag/1.0.2",
                    "assets": [
                        {
                            "name": "theme.zip",
                            "browser_download_url": ("https://github.com/test/theme/releases/download/1.0.2/theme.zip"),
                        }
                    ],
                },
                {
                    "tag_name": "1.0.1",
                    "html_url": "https://github.com/test/theme/releases/tag/1.0.1",
                    "assets": [
                        {
                            "name": "theme.zip",
                            "browser_download_url": ("https://github.com/test/theme/releases/download/1.0.1/theme.zip"),
                        }
                    ],
                },
            ]

    monkeypatch.setattr(community_api.requests, "get", lambda *_args, **_kwargs: Response())
    item = {
        "repo": "https://github.com/test/theme",
        "latest-asset": "https://github.com/test/theme/releases/latest/download/theme.zip",
        "releases": {"1.0.2": ["2rc7"], "1.0.1": ["2rc6"]},
    }
    assert community_api._latest_release(item) == {
        "tag": "1.0.1",
        "asset_url": "https://github.com/test/theme/releases/download/1.0.1/theme.zip",
    }


def test_latest_release_accepts_repository_rename_and_uses_release_asset(monkeypatch):
    class Response:
        url = "https://api.github.com/repos/Egezenn/minify-wiki-browser/releases/latest"

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "tag_name": "v1.0",
                "html_url": "https://github.com/Egezenn/minify-wiki-browser/releases/tag/v1.0",
                "assets": [
                    {
                        "name": "minify-wiki-browser.zip",
                        "browser_download_url": (
                            "https://github.com/Egezenn/minify-wiki-browser/releases/download/"
                            "v1.0/minify-wiki-browser.zip"
                        ),
                    }
                ],
            }

    monkeypatch.setattr(community_api.requests, "get", lambda *_args, **_kwargs: Response())
    item = {
        "repo": "https://github.com/Egezenn/minifiy-wiki-browser",
        "latest-asset": (
            "https://github.com/Egezenn/minify-wiki-browser/releases/latest/download/minify-wiki-browser.zip"
        ),
    }
    result = community_api._latest_release(item)
    assert result["tag"] == "v1.0"
    assert result["asset_url"].endswith("/v1.0/minify-wiki-browser.zip")


def test_archive_extraction_rejects_path_traversal(tmp_path):
    archive_path = tmp_path / "bad.zip"
    archive_path.write_bytes(_zip_bytes({"../escape.txt": "bad"}))

    with pytest.raises(ValueError, match="Unsafe path"):
        community_api._unpack_zip(str(archive_path), str(tmp_path / "out"))


@pytest.mark.parametrize("name", ["CON", "nul.txt", "../outside", "name.", "has/name"])
def test_rejects_invalid_windows_package_names(name):
    with pytest.raises(ValueError, match="cannot be used as a folder name"):
        community_api._safe_package_name(name)
