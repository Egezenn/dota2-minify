from unittest.mock import patch

import pytest
from core import log


@pytest.fixture
def mock_env(tmp_path, monkeypatch):
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    monkeypatch.setattr(log.base, "log_crashlog", str(logs_dir / "crashlog.txt"))
    monkeypatch.setattr(log.base, "log_warnings", str(logs_dir / "warnings.txt"))
    monkeypatch.setattr(log.base, "logs_dir", str(logs_dir))
    return logs_dir


def test_write_crashlog(mock_env):
    log.write_crashlog(header="Test", handled=True)
    assert "Test" in open(log.base.log_crashlog).read()


def test_write_warning(mock_env):
    log.write_warning(header="Test")
    assert "Test" in open(log.base.log_warnings).read()


def test_create_debug_zip(mock_env, tmp_path, monkeypatch):
    (mock_env / "test.log").write_text("data")
    monkeypatch.chdir(tmp_path)
    with patch("core.fs.open_thing") as mock_open:
        log.create_debug_zip()
        mock_open.assert_called_once_with(".")
    assert len(list(tmp_path.glob("*.zip"))) == 1


def test_unhandled_handler():
    with patch("core.log.write_crashlog") as mock:
        log.unhandled_handler(handled=True)(TypeError, None, None)
        mock.assert_called_once()
