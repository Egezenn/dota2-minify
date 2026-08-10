from unittest.mock import MagicMock
from unittest.mock import patch as mock_patch

import patch as patch_mod
from cli import app
from core import base, constants, mods_shared
from typer.testing import CliRunner

runner = CliRunner()


def test_version_prints_base_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert base.VERSION in result.output


def test_patch_calls_patcher():
    with mock_patch.object(patch_mod, "patcher") as mock_patcher:
        result = runner.invoke(app, ["patch"])

    assert result.exit_code == 0
    mock_patcher.assert_called_once()


def test_patch_accepts_config_and_mods_paths(tmp_path):
    cfg_file = str(tmp_path / "cfg.json")
    mods_file = str(tmp_path / "mods.json")
    with (
        mock_patch.object(patch_mod, "patcher"),
        mock_patch.object(base, "main_config_file_dir", base.main_config_file_dir),
        mock_patch.object(base, "mods_config_dir", base.mods_config_dir),
    ):
        result = runner.invoke(app, ["patch", "-c", cfg_file, "-m", mods_file])

        assert result.exit_code == 0
        assert base.main_config_file_dir == cfg_file
        assert base.mods_config_dir == mods_file


def test_patch_resolves_paths_against_original_cwd(tmp_path):
    with (
        mock_patch.object(patch_mod, "patcher"),
        mock_patch.object(base, "main_config_file_dir", base.main_config_file_dir),
        mock_patch.object(base, "mods_config_dir", base.mods_config_dir),
        mock_patch.object(base, "original_cwd", str(tmp_path), create=True),
    ):
        result = runner.invoke(app, ["patch", "-m", "based.json"])

        assert result.exit_code == 0
        assert base.mods_config_dir == str(tmp_path / "based.json")


def test_patch_writes_crashlog_on_error():
    with (
        mock_patch.object(patch_mod, "patcher", side_effect=RuntimeError("boom")),
        mock_patch("core.log.write_crashlog") as mock_crashlog,
    ):
        result = runner.invoke(app, ["patch"])

    assert result.exit_code == 0
    mock_crashlog.assert_called_once()


def test_uninstall_calls_uninstaller():
    unins = MagicMock()
    with mock_patch.object(patch_mod, "unins", unins):
        result = runner.invoke(app, ["uninstall"])

    assert result.exit_code == 0
    unins.uninstall.assert_called_once()
    unins.wipe.assert_not_called()


def test_config_show_prints_config():
    import json as json_mod

    with (
        mock_patch.object(base, "main_config_file_dir", base.main_config_file_dir),
        mock_patch("cli._config.read_json_file", return_value={"locale": "EN", "output_locale": "english"}),
    ):
        result = runner.invoke(app, ["config", "-j"])

    assert result.exit_code == 0
    assert json_mod.loads(result.output) == {"locale": "EN", "output_locale": "english"}


def test_mods_show_outputs_valid_json():
    import json as json_mod

    with (
        mock_patch.object(base, "mods_config_dir", base.mods_config_dir),
        mock_patch("cli._config.read_json_file", return_value={"Mod A": True, "Mod B": False}),
    ):
        result = runner.invoke(app, ["mods", "-j"])

    assert result.exit_code == 0
    assert json_mod.loads(result.output) == {"Mod A": True, "Mod B": False}


def test_config_prints_path(tmp_path):
    config_file = str(tmp_path / "minify_config.json")
    with mock_patch.object(base, "main_config_file_dir", config_file):
        result = runner.invoke(app, ["config", "-p"])

    assert result.exit_code == 0
    assert result.output.strip() == config_file


def test_mods_prints_path(tmp_path):
    mods_file = str(tmp_path / "mods.json")
    with (
        mock_patch.object(base, "mods_config_dir", base.mods_config_dir),
        mock_patch.object(base, "original_cwd", str(tmp_path), create=True),
    ):
        result = runner.invoke(app, ["mods", "-p", "-m", "mods.json"])

    assert result.exit_code == 0
    assert result.output.strip() == mods_file


def test_config_opens_default_config_in_editor(tmp_path):
    config_file = str(tmp_path / "minify_config.json")
    with (
        mock_patch.object(base, "main_config_file_dir", config_file),
        mock_patch("cli.subprocess.run", return_value=MagicMock(returncode=0)) as mock_run,
    ):
        result = runner.invoke(app, ["config", "-e", "vim"])

    assert result.exit_code == 0
    mock_run.assert_called_once()
    args = mock_run.call_args.args[0]
    assert args[0] == "vim"
    assert args[1] == config_file


def test_mods_opens_mods_file_in_editor(tmp_path):
    mods_file = str(tmp_path / "mods.json")
    with (
        mock_patch.object(base, "mods_config_dir", base.mods_config_dir),
        mock_patch.object(base, "original_cwd", str(tmp_path), create=True),
        mock_patch("cli.subprocess.run", return_value=MagicMock(returncode=0)) as mock_run,
    ):
        result = runner.invoke(app, ["mods", "-m", "mods.json", "-e", "vi"])

    assert result.exit_code == 0
    mock_run.assert_called_once()
    args = mock_run.call_args.args[0]
    assert args[0] == "vi"
    assert args[1] == mods_file


def test_uninstall_force_calls_wipe():
    unins = MagicMock()
    with mock_patch.object(patch_mod, "unins", unins):
        result = runner.invoke(app, ["uninstall", "-f"])

    assert result.exit_code == 0
    unins.wipe.assert_called_once()
    unins.uninstall.assert_not_called()
