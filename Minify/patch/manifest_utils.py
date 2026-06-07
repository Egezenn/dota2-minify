import os
import re

from core import config, log


def _parse_version(v: str) -> tuple:
    parts = []
    for part in str(v).split("."):
        match = re.match(r"^(\d+)(.*)$", part)
        if match:
            num = int(match.group(1))
            suffix = match.group(2)
            if suffix:
                if suffix.startswith("rc"):
                    rc_num = suffix[2:]
                    parts.append((num, -1, int(rc_num) if rc_num.isdigit() else 0))
                else:
                    parts.append((num, -2, 0))
            else:
                parts.append((num, 0, 0))
        else:
            raise ValueError(f"Invalid version string part: {part}")
    # Pad to handle cases like "1.13" vs "1.13.0"
    while len(parts) < 4:
        parts.append((0, 0, 0))
    return tuple(parts)


def is_version_at_least(current: str, requirements: str) -> bool:
    """
    Compares current version against a requirement string (e.g., ">=1.13,<=1.14" or "1.13").
    If no operator is provided, defaults to ">=".
    """
    try:
        if current is None or requirements is None:
            return False

        current_v = _parse_version(current)
        reqs = [r.strip() for r in requirements.split(",") if r.strip()]

        for req in reqs:
            match = re.match(r"^(>=|<=|>|<|==|=)?\s*(.+)$", req)
            if not match:
                return False

            op = match.group(1) or ">="
            target_v = _parse_version(match.group(2))

            if op == ">=":
                if not (current_v >= target_v):
                    return False
            elif op == "<=":
                if not (current_v <= target_v):
                    return False
            elif op == ">":
                if not (current_v > target_v):
                    return False
            elif op == "<":
                if not (current_v < target_v):
                    return False
            elif op in ("==", "="):
                if not (current_v == target_v):
                    return False

        return True
    except (ValueError, AttributeError, IndexError, TypeError):
        return False


def get_mod(mod_path):
    manifest_json = os.path.join(mod_path, "manifest.json")

    if os.path.exists(manifest_json):
        return config.read_json_file(manifest_json)

    return {}
