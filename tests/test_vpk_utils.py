import os
from unittest.mock import patch

import pytest
from core import base
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
