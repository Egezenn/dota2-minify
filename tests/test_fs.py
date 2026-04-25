import os
import sys
from unittest.mock import call, patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Minify")))

from core import fs


def test_create_dirs_single():
    with patch("os.makedirs") as mock_makedirs:
        fs.create_dirs("test_dir")
        mock_makedirs.assert_called_once_with("test_dir", exist_ok=True)


def test_create_dirs_multiple():
    with patch("os.makedirs") as mock_makedirs:
        fs.create_dirs("dir1", "dir2", "dir3")
        assert mock_makedirs.call_count == 3
        mock_makedirs.assert_has_calls(
            [call("dir1", exist_ok=True), call("dir2", exist_ok=True), call("dir3", exist_ok=True)]
        )


def test_create_dirs_empty_and_falsy():
    with patch("os.makedirs") as mock_makedirs:
        fs.create_dirs("", None, "valid_dir", False)
        # Only 'valid_dir' is truthy
        mock_makedirs.assert_called_once_with("valid_dir", exist_ok=True)


def test_create_dirs_no_args():
    with patch("os.makedirs") as mock_makedirs:
        fs.create_dirs()
        mock_makedirs.assert_not_called()


def test_get_file_type_magic_png(tmp_path):
    file_path = tmp_path / "test_file.bin"
    file_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"dummy data")
    assert fs.get_file_type(str(file_path)) == ".png"


def test_get_file_type_magic_jpg(tmp_path):
    file_path = tmp_path / "test_file.bin"
    file_path.write_bytes(b"\xff\xd8\xff" + b"dummy data")
    assert fs.get_file_type(str(file_path)) == ".jpg"


def test_get_file_type_magic_webp(tmp_path):
    file_path = tmp_path / "test_file.bin"
    file_path.write_bytes(b"RIFF\x00\x00\x00\x00WEBP" + b"dummy data")
    assert fs.get_file_type(str(file_path)) == ".webp"


def test_get_file_type_magic_webm(tmp_path):
    file_path = tmp_path / "test_file.bin"
    file_path.write_bytes(b"\x1a\x45\xdf\xa3" + b"dummy data")
    assert fs.get_file_type(str(file_path)) == ".webm"


def test_get_file_type_magic_mp4(tmp_path):
    file_path = tmp_path / "test_file.bin"
    file_path.write_bytes(b"\x00\x00\x00\x00ftyp" + b"dummy data")
    assert fs.get_file_type(str(file_path)) == ".mp4"


def test_get_file_type_magic_gif(tmp_path):
    file_path = tmp_path / "test_file.bin"
    file_path.write_bytes(b"GIF89a" + b"dummy data")
    assert fs.get_file_type(str(file_path)) == ".gif"

    file_path.write_bytes(b"GIF87a" + b"dummy data")
    assert fs.get_file_type(str(file_path)) == ".gif"


def test_get_file_type_fallback_extension(tmp_path):
    file_path = tmp_path / "test_file.txt"
    file_path.write_bytes(b"just text data")
    assert fs.get_file_type(str(file_path)) == ".txt"


def test_get_file_type_fallback_no_extension(tmp_path):
    file_path = tmp_path / "test_file"
    file_path.write_bytes(b"just text data")
    assert fs.get_file_type(str(file_path)) == "test_file"


def test_get_file_type_missing_file():
    assert fs.get_file_type("nonexistent_file.txt") is None


def test_move_path_success(tmp_path):
    src = tmp_path / "src.txt"
    src.write_text("content")
    dst = tmp_path / "dst.txt"

    fs.move_path(str(src), str(dst))

    assert not src.exists()
    assert dst.exists()
    assert dst.read_text() == "content"


def test_move_path_file_not_found(capsys):
    fs.move_path("non_existent_src", "dst")
    captured = capsys.readouterr()
    assert "Skipped move of: non_existent_src (not found)" in captured.out


@patch("shutil.move")
@patch("os.chmod")
def test_move_path_permission_error_fallback(mock_chmod, mock_move, tmp_path):
    src = tmp_path / "src_dir"
    src.mkdir()
    (src / "file.txt").write_text("content")
    dst = tmp_path / "dst_dir"

    # First time raise PermissionError, second time succeed
    mock_move.side_effect = [PermissionError("mocked"), None]

    fs.move_path(str(src), str(dst))

    assert mock_move.call_count == 2
    assert mock_chmod.call_count == 2  # Once for dir, once for file


def test_remove_path_success(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("content")
    dir_path = tmp_path / "test_dir"
    dir_path.mkdir()

    fs.remove_path(str(file_path), str(dir_path))

    assert not file_path.exists()
    assert not dir_path.exists()


def test_remove_path_file_not_found(capsys):
    fs.remove_path("non_existent")
    captured = capsys.readouterr()
    assert "Skipped deletion of: non_existent" in captured.out


@patch("shutil.rmtree")
@patch("os.remove")
@patch("os.chmod")
def test_remove_path_permission_error_fallback(mock_chmod, mock_remove, mock_rmtree, tmp_path):
    dir_path = tmp_path / "test_dir"
    dir_path.mkdir()
    file_path = dir_path / "file.txt"
    file_path.write_text("content")

    # First time raise PermissionError, second time succeed
    mock_rmtree.side_effect = [PermissionError("mocked"), None]

    fs.remove_path(str(dir_path))

    assert mock_rmtree.call_count == 2
    assert mock_chmod.call_count == 2  # Once for dir, once for file


@patch("requests.get")
@patch("dearpygui.dearpygui.set_value")
def test_download_file_success(mock_set_value, mock_get, tmp_path):
    target = tmp_path / "downloaded.txt"

    class MockResponse:
        def __init__(self):
            self.headers = {"content-length": "2048"}

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size):
            yield b"a" * 1024
            yield b"b" * 1024

    mock_get.return_value = MockResponse()

    result = fs.download_file("http://example.com/file", str(target), progress_tag="prog")

    assert result is True
    assert target.exists()
    assert target.read_bytes() == (b"a" * 1024 + b"b" * 1024)
    # Check that progress was updated
    assert mock_set_value.call_count > 0


@patch("requests.get")
@patch("ui.terminal.add_text")
def test_download_file_exception(mock_add_text, mock_get, tmp_path):
    target = tmp_path / "failed_download.txt"
    mock_get.side_effect = Exception("Network error")

    result = fs.download_file("http://example.com/fail", str(target))

    assert result is False
    assert not target.exists()
    mock_add_text.assert_called_once()
    assert "Failed to open" in mock_add_text.call_args[0][0]
    assert "Network error" in mock_add_text.call_args[0][0]


import tarfile
import zipfile


def test_extract_archive_zip_all(tmp_path):
    zip_path = tmp_path / "test.zip"
    extract_dir = tmp_path / "extract_all_zip"

    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("file1.txt", "content1")
        zf.writestr("dir/file2.txt", "content2")

    result = fs.extract_archive(str(zip_path), extract_dir=str(extract_dir))

    assert result is True
    assert (extract_dir / "file1.txt").read_text() == "content1"
    assert (extract_dir / "dir/file2.txt").read_text() == "content2"


def test_extract_archive_zip_target(tmp_path):
    zip_path = tmp_path / "test2.zip"
    extract_dir = tmp_path / "extract_target_zip"

    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("file1.txt", "content1")
        zf.writestr("file2.txt", "content2")

    result = fs.extract_archive(str(zip_path), extract_dir=str(extract_dir), target_file="file2.txt")

    assert result is True
    assert not (extract_dir / "file1.txt").exists()
    assert (extract_dir / "file2.txt").read_text() == "content2"


def test_extract_archive_tar_all(tmp_path):
    tar_path = tmp_path / "test.tar.gz"
    extract_dir = tmp_path / "extract_all_tar"

    source_file = tmp_path / "source.txt"
    source_file.write_text("tar content")

    with tarfile.open(tar_path, "w:gz") as tf:
        tf.add(source_file, arcname="source.txt")

    result = fs.extract_archive(str(tar_path), extract_dir=str(extract_dir))

    assert result is True
    assert (extract_dir / "source.txt").read_text() == "tar content"


def test_extract_archive_tar_target(tmp_path):
    tar_path = tmp_path / "test2.tar.gz"
    extract_dir = tmp_path / "extract_target_tar"

    source1 = tmp_path / "source1.txt"
    source1.write_text("content1")
    source2 = tmp_path / "source2.txt"
    source2.write_text("content2")

    with tarfile.open(tar_path, "w:gz") as tf:
        tf.add(source1, arcname="file1.txt")
        tf.add(source2, arcname="file2.txt")

    result = fs.extract_archive(str(tar_path), extract_dir=str(extract_dir), target_file="file2.txt")

    assert result is True
    assert not (extract_dir / "file1.txt").exists()
    assert (extract_dir / "file2.txt").read_text() == "content2"


@patch("ui.terminal.add_text")
def test_extract_archive_unsupported(mock_add_text, tmp_path):
    unsupported_path = tmp_path / "test.rar"
    result = fs.extract_archive(str(unsupported_path))

    assert result is False
    mock_add_text.assert_called_once()
    assert "Unsupported archive format" in mock_add_text.call_args[0][0]


@patch("ui.terminal.add_text")
def test_extract_archive_exception(mock_add_text, tmp_path):
    # Pass a nonexistent zip file
    missing_zip = tmp_path / "missing.zip"
    result = fs.extract_archive(str(missing_zip))

    assert result is False
    mock_add_text.assert_called_once()
    assert "Extraction failed" in mock_add_text.call_args[0][0]


@patch("core.base.OS", "windows")
@patch("core.base.WIN", "windows")
@patch("os.startfile", create=True)
def test_open_thing_windows_dir(mock_startfile, tmp_path):
    dir_path = tmp_path / "test_dir"
    dir_path.mkdir()

    fs.open_thing(str(dir_path))
    mock_startfile.assert_called_once_with(str(dir_path))


@patch("core.base.OS", "windows")
@patch("core.base.WIN", "windows")
@patch("os.startfile", create=True)
def test_open_thing_windows_file(mock_startfile, tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("content")

    fs.open_thing(str(file_path))
    mock_startfile.assert_called_once_with(str(file_path))


@patch("core.base.OS", "windows")
@patch("core.base.WIN", "windows")
@patch("os.startfile", create=True)
def test_open_thing_windows_with_args(mock_startfile, tmp_path):
    file_path = tmp_path / "test.exe"
    file_path.write_text("dummy")

    fs.open_thing(str(file_path), args="-h")
    mock_startfile.assert_called_once_with(str(file_path), arguments="-h")


@patch("core.base.OS", "mac")
@patch("core.base.MAC", "mac")
@patch("subprocess.run")
def test_open_thing_mac_dir(mock_run, tmp_path):
    dir_path = tmp_path / "test_dir"
    dir_path.mkdir()

    fs.open_thing(str(dir_path))
    mock_run.assert_called_once_with(["open", str(dir_path)])


@patch("core.base.OS", "mac")
@patch("core.base.MAC", "mac")
@patch("subprocess.run")
def test_open_thing_mac_file(mock_run, tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("content")

    fs.open_thing(str(file_path))
    mock_run.assert_called_once_with(["open", "-R", str(file_path)])


@patch("core.base.OS", "linux")
@patch("core.base.WIN", "windows")
@patch("core.base.MAC", "mac")
@patch("subprocess.run")
def test_open_thing_linux_dir(mock_run, tmp_path):
    dir_path = tmp_path / "test_dir"
    dir_path.mkdir()

    fs.open_thing(str(dir_path))
    mock_run.assert_called_once_with(["xdg-open", str(dir_path)])


@patch("core.base.OS", "linux")
@patch("core.base.WIN", "windows")
@patch("core.base.MAC", "mac")
@patch("subprocess.run")
def test_open_thing_linux_file(mock_run, tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("content")

    fs.open_thing(str(file_path))
    mock_run.assert_called_once_with(["xdg-open", str(file_path)])


@patch("core.base.OS", "linux")
@patch("core.base.WIN", "windows")
@patch("os.access")
@patch("subprocess.Popen")
def test_open_thing_posix_with_args_executable(mock_popen, mock_access, tmp_path):
    file_path = tmp_path / "script.sh"
    file_path.write_text("#!/bin/sh")

    mock_access.return_value = True

    fs.open_thing(str(file_path), args="--help")

    mock_popen.assert_called_once()
    assert mock_popen.call_args[0][0] == [str(file_path), "--help"]


@patch("core.base.OS", "linux")
@patch("core.base.WIN", "windows")
@patch("os.access")
@patch("subprocess.run")
def test_open_thing_posix_with_args_non_executable(mock_run, mock_access, tmp_path):
    file_path = tmp_path / "doc.txt"
    file_path.write_text("content")

    mock_access.return_value = False

    fs.open_thing(str(file_path), args="--help")

    # Since it's not executable but args are provided, it falls back to opening the parent dir
    mock_run.assert_called_once_with(["xdg-open", str(tmp_path)])


@patch("os.path.isdir")
@patch("ui.terminal.add_text")
def test_open_thing_file_not_found(mock_add_text, mock_isdir):
    # Simulate FileNotFoundError when checking if it's a directory
    mock_isdir.side_effect = FileNotFoundError()

    fs.open_thing("nonexistent_path")

    mock_add_text.assert_called_once()
    assert mock_add_text.call_args[0][0] == "&open_thing_fail"
    assert mock_add_text.call_args[0][1] == "nonexistent_path"
    assert mock_add_text.call_args[1]["msg_type"] == "error"
