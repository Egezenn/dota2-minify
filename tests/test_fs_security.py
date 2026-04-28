import os
import sys
import tarfile
import tempfile
import pytest

# Add the project root and Minify directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Minify")))

from core.fs import extract_archive


def test_extract_archive_prevents_zip_slip(tmp_path):
    # Create a malicious tarball
    tar_path = tmp_path / "malicious.tar.gz"
    extract_dir = tmp_path / "extract_dir"
    extract_dir.mkdir()

    # We want the malicious file to attempt to write outside extract_dir, e.g., to tmp_path directly
    malicious_content = b"malicious payload"

    with tarfile.open(tar_path, "w:gz") as tar:
        # Safe file
        safe_info = tarfile.TarInfo(name="safe.txt")
        safe_info.size = len(b"safe")
        import io

        tar.addfile(safe_info, io.BytesIO(b"safe"))

        # Malicious file attempting directory traversal
        malicious_info = tarfile.TarInfo(name="../malicious.txt")
        malicious_info.size = len(malicious_content)
        tar.addfile(malicious_info, io.BytesIO(malicious_content))

    # Extract
    success = extract_archive(str(tar_path), extract_dir=str(extract_dir))

    # Test assertions
    assert success is True

    # Check that safe file was extracted
    assert (extract_dir / "safe.txt").exists()

    # Check that malicious file was NOT extracted outside the directory
    # It would be at tmp_path / "malicious.txt" based on `extract_dir / "../malicious.txt"`
    assert not (tmp_path / "malicious.txt").exists()
