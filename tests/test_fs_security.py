import io
import os
import sys
import tarfile
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../Minify")))

mock_config = MagicMock()
mock_config.get = MagicMock(side_effect=lambda key, default=None: default)
mock_config.set = MagicMock()
sys.modules["core.config"] = mock_config

mock_terminal = MagicMock()
mock_terminal.add_text = MagicMock()
sys.modules["ui.terminal"] = mock_terminal

from core.fs import extract_archive


def test_extract_archive_prevents_zip_slip(tmp_path):
    # Create a malicious tarball
    tar_path = tmp_path / "malicious.tar.gz"
    extract_dir = tmp_path / "extract_dir"
    extract_dir.mkdir()

    malicious_content = b"malicious payload"

    with tarfile.open(tar_path, "w:gz") as tar:
        # Safe file
        safe_info = tarfile.TarInfo(name="safe.txt")
        safe_info.size = len(b"safe")
        tar.addfile(safe_info, io.BytesIO(b"safe"))

        # Malicious file attempting directory traversal
        malicious_info = tarfile.TarInfo(name="../malicious.txt")
        malicious_info.size = len(malicious_content)
        tar.addfile(malicious_info, io.BytesIO(malicious_content))

    # Extract
    success = extract_archive(str(tar_path), extract_dir=str(extract_dir))

    # Test assertions
    assert success is True
    assert (extract_dir / "safe.txt").exists()
    assert not (tmp_path / "malicious.txt").exists()


def test_extract_archive_target_file_safe(tmp_path):
    tar_path = tmp_path / "test.tar.gz"
    extract_dir = tmp_path / "extract_dir"
    extract_dir.mkdir()

    with tarfile.open(tar_path, "w:gz") as tar:
        info = tarfile.TarInfo(name="safe.txt")
        info.size = len(b"safe")
        tar.addfile(info, io.BytesIO(b"safe"))

    success = extract_archive(str(tar_path), extract_dir=str(extract_dir), target_file="safe.txt")
    assert success is True
    assert (extract_dir / "safe.txt").exists()


def test_extract_archive_target_file_malicious(tmp_path):
    tar_path = tmp_path / "test.tar.gz"
    extract_dir = tmp_path / "extract_dir"
    extract_dir.mkdir()

    with tarfile.open(tar_path, "w:gz") as tar:
        info = tarfile.TarInfo(name="../malicious.txt")
        info.size = len(b"payload")
        tar.addfile(info, io.BytesIO(b"payload"))

    # Should skip the malicious member even when requested directly
    success = extract_archive(str(tar_path), extract_dir=str(extract_dir), target_file="../malicious.txt")
    assert success is True
    assert not (tmp_path / "malicious.txt").exists()
    assert not (extract_dir / "../malicious.txt").exists()


def test_extract_archive_unsupported_format(tmp_path):
    dummy_file = tmp_path / "test.txt"
    dummy_file.write_text("not an archive")

    # Clear previous calls
    mock_terminal.add_text.reset_mock()

    success = extract_archive(str(dummy_file), extract_dir=str(tmp_path))
    assert success is False
    mock_terminal.add_text.assert_called()
    args, kwargs = mock_terminal.add_text.call_args
    assert "Unsupported archive format" in args[0]
    assert kwargs["msg_type"] == "error"


def test_extract_archive_nonexistent_file(tmp_path):
    nonexistent = tmp_path / "ghost.tar.gz"

    # Clear previous calls
    mock_terminal.add_text.reset_mock()

    success = extract_archive(str(nonexistent), extract_dir=str(tmp_path))
    assert success is False
    # Verifies that it logs the exception error
    args, kwargs = mock_terminal.add_text.call_args
    assert "Extraction failed" in args[0]
    assert kwargs["msg_type"] == "error"
