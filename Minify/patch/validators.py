import re

from core import base

_RESOURCECOMPILER_SUMMARY = re.compile(
    rb"(?im)^\s*(?:[A-Z][A-Z ]*:\s*)?\d+\s+compiled,\s*(\d+)\s+failed,\s*\d+\s+skipped(?:,\s*[^\r\n]*)?\s*$"
)
_S2V_FAILURE = re.compile(rb"(?im)^\s*(\d+)\s+file\(s\)\s+failed to process\.\s*$")


def resourcecompiler(returncode: int, output: bytes) -> None:
    if returncode != 0:
        raise RuntimeError(f"resourcecompiler exited with code {returncode}. See {base.log_rescomp} for details.")

    summary = _RESOURCECOMPILER_SUMMARY.search(output)
    if summary is None:
        raise RuntimeError(f"resourcecompiler did not report a compilation summary. See {base.log_rescomp}.")

    failed = int(summary.group(1))
    if failed:
        raise RuntimeError(
            f"resourcecompiler failed to compile {failed} resource(s). See {base.log_rescomp} for details."
        )


def source2viewer(returncode: int, output: bytes) -> None:
    if returncode != 0:
        raise RuntimeError(f"Source2Viewer exited with code {returncode}. See {base.log_s2v} for details.")

    failure = _S2V_FAILURE.search(output)
    if failure and int(failure.group(1)):
        raise RuntimeError(
            f"Source2Viewer failed to decompile {failure.group(1).decode()} file(s). See {base.log_s2v} for details."
        )
