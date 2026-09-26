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
    vpk_utils.pack(str(pak_dir), pak_path)

    assert vpk_utils.is_minify_pak(pak_path) is True


def test_is_minify_pak_rejects_foreign_pak(tmp_path):
    pak_dir = tmp_path / "pak"
    pak_dir.mkdir()
    (pak_dir / "random.txt").write_text("test")
    pak_path = str(tmp_path / "test_dir.vpk")
    vpk_utils.pack(str(pak_dir), pak_path)

    assert vpk_utils.is_minify_pak(pak_path) is False


def test_is_minify_pak_missing_file(tmp_path):
    assert vpk_utils.is_minify_pak(str(tmp_path / "missing_dir.vpk")) is False


def test_is_minify_pak_rejects_non_vpk_file(tmp_path):
    invalid_path = tmp_path / "fake_dir.vpk"
    invalid_path.write_text("not a vpk")

    assert vpk_utils.is_minify_pak(str(invalid_path)) is False


def test_pack_chunked_and_read(tmp_path):
    source_dir = tmp_path / "source"
    (source_dir / "subdir").mkdir(parents=True)
    (source_dir / "root_file.txt").write_text("Root file content")
    (source_dir / "subdir" / "nested.txt").write_text("Nested file content " * 50)
    (source_dir / "subdir" / "other.bin").write_bytes(b"\x01\x02\x03\x04" * 100)

    out_dir = tmp_path / "out"
    dir_vpk_path = str(out_dir / "pak66_dir.vpk")

    # Use a small chunk size of 300 bytes so multiple chunks are generated
    vpk_utils.pack(str(source_dir), dir_vpk_path, chunk_size=300)

    # Check chunk files exist
    chunk_0 = out_dir / "pak66_000.vpk"
    chunk_1 = out_dir / "pak66_001.vpk"
    assert os.path.exists(dir_vpk_path)
    assert chunk_0.exists()
    assert chunk_1.exists()

    # Read back with standard vpk reader
    pak = vpk.open(dir_vpk_path)
    assert pak.get_file("root_file.txt").read().decode("utf-8") == "Root file content"
    assert pak.get_file("subdir/nested.txt").read().decode("utf-8") == "Nested file content " * 50
    assert pak.get_file("subdir/other.bin").read() == b"\x01\x02\x03\x04" * 100


def test_pack_cleans_stale_chunks(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "file1.txt").write_text("A" * 500)
    (source_dir / "file2.txt").write_text("B" * 500)

    out_dir = tmp_path / "out"
    dir_vpk_path = str(out_dir / "pak66_dir.vpk")

    # First pack with 300 byte chunks creates multiple chunks
    vpk_utils.pack(str(source_dir), dir_vpk_path, chunk_size=300)
    assert (out_dir / "pak66_001.vpk").exists()

    # Second pack with 10MB chunk fits in a single chunk (_000.vpk)
    vpk_utils.pack(str(source_dir), dir_vpk_path, chunk_size=10 * 1024 * 1024)
    assert (out_dir / "pak66_000.vpk").exists()
    assert not (out_dir / "pak66_001.vpk").exists()
