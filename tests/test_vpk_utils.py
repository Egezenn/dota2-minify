import os
from unittest.mock import patch

import vpk
from patch import vpk_utils


def test_dump_metadata_default_behavior(tmp_path):
    target_dir = str(tmp_path / "output")
    os.makedirs(target_dir, exist_ok=True)

    # Mock config.get to return False for opt_out_vpk_metadata
    def mock_get(key, default=None):
        if key == "opt_out_vpk_metadata":
            return False
        return default

    with patch("core.config.get", side_effect=mock_get):
        # Mock shutil.copy and utils.open_utf8 to avoid hitting real steam.inf or mods.json
        with patch("shutil.copy") as _, patch("patch.vpk_utils.utils.open_utf8") as mock_open:
            vpk_utils.dump_metadata(target_dir, mod_name="test_mod")

            # Since mod_name is provided, it should create {mod_name}.txt
            assert os.path.exists(os.path.join(target_dir, "test_mod.txt"))

            # Should have called open_utf8 to write minify_version.txt
            mock_open.assert_any_call(os.path.join(target_dir, "minify_version.txt"), "w")


def test_dump_metadata_opt_out(tmp_path):
    target_dir = str(tmp_path / "output")
    os.makedirs(target_dir, exist_ok=True)

    # Mock config.get to return True for opt_out_vpk_metadata
    def mock_get(key, default=None):
        if key == "opt_out_vpk_metadata":
            return True
        return default

    with patch("core.config.get", side_effect=mock_get):
        with patch("shutil.copy") as mock_copy, patch("patch.vpk_utils.utils.open_utf8") as mock_open:
            vpk_utils.dump_metadata(target_dir, mod_name="test_mod")

            # Since we opted out, it should return early:
            # {mod_name}.txt should NOT be created, and copy/open should NOT be called.
            assert not os.path.exists(os.path.join(target_dir, "test_mod.txt"))
            mock_copy.assert_not_called()
            mock_open.assert_not_called()


def test_is_minify_pak_detects_metadata_marker(tmp_path):
    pak_dir = tmp_path / "pak"
    pak_dir.mkdir()
    (pak_dir / "minify_version.txt").write_text("1.0.0")
    pak_path = str(tmp_path / "test_dir.vpk")
    vpk.new(str(pak_dir)).save(pak_path)

    assert vpk_utils.is_minify_pak(pak_path) is True


def test_is_minify_pak_rejects_foreign_pak(tmp_path):
    pak_dir = tmp_path / "pak"
    pak_dir.mkdir()
    (pak_dir / "random.txt").write_text("test")
    pak_path = str(tmp_path / "test_dir.vpk")
    vpk.new(str(pak_dir)).save(pak_path)

    assert vpk_utils.is_minify_pak(pak_path) is False


def test_is_minify_pak_missing_file(tmp_path):
    assert vpk_utils.is_minify_pak(str(tmp_path / "missing_dir.vpk")) is False


def test_is_minify_pak_rejects_non_vpk_file(tmp_path):
    invalid_path = tmp_path / "fake_dir.vpk"
    invalid_path.write_text("not a vpk")

    assert vpk_utils.is_minify_pak(str(invalid_path)) is False
