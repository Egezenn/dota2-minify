import json

from core import base
from plugins.d2pfx import api as d2pfx_api


def test_d2pfx_install_and_uninstall_persist_install_record(tmp_path, monkeypatch):
    root = tmp_path / "Minify"
    mods = root / "mods"
    config_dir = root / "config"
    cache = root / "cache"
    for path in (mods, config_dir, cache):
        path.mkdir(parents=True)

    monkeypatch.setattr(base, "mods_dir", str(mods))
    monkeypatch.setattr(base, "mods_config_dir", str(config_dir / "mods.json"))
    state = {"existing": {"preserved": True}}
    monkeypatch.setattr(d2pfx_api.utils, "read_states", lambda: json.loads(json.dumps(state)))
    monkeypatch.setattr(d2pfx_api.utils, "write_states", lambda key, value: state.update({key: value}))
    monkeypatch.setattr(d2pfx_api.mods_shared, "scan_mods", lambda: None)
    monkeypatch.setattr(d2pfx_api.output, "add_text", lambda *_args, **_kwargs: None)

    class FakeDataManager:
        @staticmethod
        def to_hf_fallback(url):
            return None

        def download_file(self, url, destination, *_args, **_kwargs):
            with open(destination, "wb") as mod_file:
                mod_file.write(b"updated mod" if "v2" in url else b"mod")
            return True

    monkeypatch.setattr(d2pfx_api, "DataManager", FakeDataManager)

    mod = {
        "name": "Example Mod",
        "author": "Example Author",
        "file": "https://example.test/v1/mod.vpk",
        "tags": ["visual"],
        "meta": {"date": 100},
    }
    result = d2pfx_api.install_mod({"mod": mod, "cat_id": "effects"})

    assert result["success"] is True
    install_key = "effects::Example Mod"
    manifest = json.loads((mods / result["folder"] / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["source_date"] == 100
    assert state[d2pfx_api.D2PFX_INSTALLS_KEY][install_key] == {
        "source_date": 100,
        "folder": result["folder"],
    }
    assert state["existing"] == {"preserved": True}
    assert json.loads((config_dir / "mods.json").read_text(encoding="utf-8"))[result["folder"]] is True

    updated_mod = {**mod, "file": "https://example.test/v2/mod.vpk", "meta": {"date": 200}}
    updated = d2pfx_api.update_mod({"mod": updated_mod, "cat_id": "effects"})
    assert updated["success"] is True
    assert (mods / result["folder"] / "mod.vpk").read_bytes() == b"updated mod"
    manifest = json.loads((mods / result["folder"] / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["source_date"] == 200
    assert state[d2pfx_api.D2PFX_INSTALLS_KEY][install_key]["source_date"] == 200
    assert list(mods.iterdir()) == [mods / result["folder"]]

    removed = d2pfx_api.uninstall_mod({"mod_name": "Example Mod", "cat_id": "effects"})

    assert removed["success"] is True
    assert install_key not in state[d2pfx_api.D2PFX_INSTALLS_KEY]
    assert state["existing"] == {"preserved": True}


def test_install_records_compacts_legacy_records(monkeypatch):
    legacy_record = {
        "browser": "d2pfx",
        "name": "Example Mod",
        "category": "effects",
        "label": None,
        "source_date": 100,
        "folder": "D2PFX EFFECTS - Example Mod",
    }
    state = {d2pfx_api.D2PFX_INSTALLS_KEY: {"effects::Example Mod::": legacy_record}}
    monkeypatch.setattr(d2pfx_api.utils, "read_states", lambda: json.loads(json.dumps(state)))
    monkeypatch.setattr(d2pfx_api.utils, "write_states", lambda key, value: state.update({key: value}))

    records = d2pfx_api._install_records()
    compact_record = {"source_date": 100, "folder": "D2PFX EFFECTS - Example Mod"}
    assert records == {"effects::Example Mod": compact_record}
    assert state[d2pfx_api.D2PFX_INSTALLS_KEY] == {"effects::Example Mod": compact_record}


def test_reconcile_install_states_removes_missing_mods(tmp_path, monkeypatch):
    mods = tmp_path / "mods"
    mods.mkdir()
    present = mods / "Present Mod"
    present.mkdir()
    state = {
        d2pfx_api.D2PFX_INSTALLS_KEY: {
            "effects::Present Mod": {"source_date": 100, "folder": "Present Mod"},
            "effects::Missing Mod": {"source_date": 100, "folder": "Missing Mod"},
        }
    }
    monkeypatch.setattr(base, "mods_dir", str(mods))
    monkeypatch.setattr(d2pfx_api.utils, "read_states", lambda: json.loads(json.dumps(state)))
    monkeypatch.setattr(d2pfx_api.utils, "write_states", lambda key, value: state.update({key: value}))

    d2pfx_api.reconcile_install_states()

    assert set(state[d2pfx_api.D2PFX_INSTALLS_KEY]) == {"effects::Present Mod"}
