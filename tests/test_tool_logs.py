from unittest.mock import MagicMock
from unittest.mock import patch as mock_patch

import helper
from patch import validators
import pytest


@pytest.mark.parametrize(
    "summary",
    [
        b"OK: 80 compiled, 0 failed, 0 skipped",
        b"WARNING: 86 compiled, 0 failed, 0 skipped, 0m:01s",
        b"Intel warning\nOK: 0 compiled, 0 failed, 0 skipped\nLeaked KeyValues blocks: 157",
    ],
)
def test_resourcecompiler_accepts_success_summary(summary):
    validators.validate_resourcecompiler_result(0, summary)


@pytest.mark.parametrize(
    "returncode, output",
    [
        (0, b"OK: 79 compiled, 1 failed, 0 skipped"),
        (0, b"compiler stopped unexpectedly"),
        (1, b"compiler error"),
    ],
)
def test_resourcecompiler_rejects_failures(returncode, output):
    with pytest.raises(RuntimeError):
        validators.validate_resourcecompiler_result(returncode, output)


def test_source2viewer_accepts_successful_run():
    validators.validate_source2viewer_result(0, b"--- Dump written to file.xml\n")


@pytest.mark.parametrize(
    "returncode, output",
    [
        (0, b"2 file(s) failed to process."),
        (2, b"1 file(s) failed to process."),
    ],
)
def test_source2viewer_rejects_decompile_failure(returncode, output):
    with pytest.raises(RuntimeError):
        validators.validate_source2viewer_result(returncode, output)


def test_resourcecompiler_writes_combined_log_and_validates():
    result = MagicMock(returncode=0, stdout=b"stderr warning\nOK: 1 compiled, 0 failed, 0 skipped\n")
    with (
        mock_patch.object(helper.base, "log_rescomp", "resourcecompiler-test.log"),
        mock_patch("helper.subprocess.run", return_value=result),
        mock_patch("builtins.open", mock_open := MagicMock()),
    ):
        helper.compile()

    mock_open.return_value.__enter__.return_value.write.assert_called_once_with(result.stdout)
