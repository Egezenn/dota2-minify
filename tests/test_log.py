import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# isort: split

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../Minify")))
sys.modules["ui.terminal"] = MagicMock()
sys.modules["core.fs"] = MagicMock()

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


def test_create_debug_zip(mock_env, tmp_path):
    (mock_env / "test.log").write_text("data")
    os.chdir(tmp_path)
    log.create_debug_zip()
    assert len(list(tmp_path.glob("*.zip"))) == 1


def test_unhandled_handler():
    with patch("core.log.write_crashlog") as mock:
        log.unhandled_handler(handled=True)(TypeError, None, None)
        mock.assert_called_once()
