import os
import re
from typing import Any, Dict, List, Optional

from core import config


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


def get_effective_settings(
    mod_cfg: Optional[Dict[str, Any]], mod_settings: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Combines default setting values defined in mod manifest with configured mod settings.
    """
    settings: Dict[str, Any] = {}
    if mod_cfg and isinstance(mod_cfg, dict):
        for s in mod_cfg.get("settings", []):
            if isinstance(s, dict) and "key" in s and "default" in s:
                settings[s["key"]] = s["default"]
    if mod_settings and isinstance(mod_settings, dict):
        settings.update(mod_settings)
    return settings


def is_truthy(val: Any) -> bool:
    """Determines truthiness for condition evaluations."""
    if val is None:
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val != 0
    s = str(val).strip().lower()
    return s not in ("", "false", "0", "no", "off", "null", "none")


def evaluate_condition(condition_expr: Any, settings: Dict[str, Any]) -> bool:
    """
    Evaluates a condition expression against settings dictionary.
    - None / True -> True
    - False -> False
    - "key" -> is_truthy(settings.get("key"))
    - "key:true" / "key:false" -> is_truthy(settings.get("key")) == expected_bool
    - "key:some_value" -> str(settings.get("key", "")).strip().lower() == "some_value"
    """
    if condition_expr is None or condition_expr is True:
        return True
    if condition_expr is False:
        return False

    if not isinstance(condition_expr, str):
        return bool(condition_expr)

    condition_expr = condition_expr.strip()
    if not condition_expr:
        return True

    if ":" in condition_expr:
        key, expected_val = condition_expr.split(":", 1)
        key = key.strip()
        expected_val = expected_val.strip().lower()
        actual_val = settings.get(key)

        if expected_val in ("true", "1", "yes"):
            return is_truthy(actual_val)
        elif expected_val in ("false", "0", "no"):
            return not is_truthy(actual_val)
        else:
            return str(actual_val).strip().lower() == expected_val
    else:
        key = condition_expr
        actual_val = settings.get(key)
        return is_truthy(actual_val)


def interpolate_variables(text: str, settings: Dict[str, Any]) -> str:
    """Replaces <&var_name> in text with the corresponding value from settings."""
    if not text or not isinstance(text, str) or "<&" not in text:
        return text
    return re.sub(
        r"<&(.*?)>",
        lambda m: str(settings.get(m.group(1), m.group(0))),
        text,
    )


def process_blacklist_lines(lines: List[str], settings: Dict[str, Any]) -> List[str]:
    """
    Filters lines in blacklist.txt by evaluating nestable #if:<expr> / #endif directives
    and interpolating <&var> variables.
    """
    if_re = re.compile(r"^\s*#\s*if:(.+)$", re.IGNORECASE)
    endif_re = re.compile(r"^\s*#\s*endif(?::.*)?$", re.IGNORECASE)

    result = []
    stack: List[bool] = []

    for line in lines:
        stripped = line.strip()

        if_match = if_re.match(stripped)
        if if_match:
            cond_expr = if_match.group(1).strip()
            cond_met = evaluate_condition(cond_expr, settings)
            parent_active = stack[-1] if stack else True
            stack.append(parent_active and cond_met)
            continue

        endif_match = endif_re.match(stripped)
        if endif_match:
            if stack:
                stack.pop()
            continue

        current_active = stack[-1] if stack else True
        if current_active:
            result.append(interpolate_variables(line, settings))

    return result


def process_css_content(content: str, settings: Dict[str, Any]) -> str:
    """
    Processes nestable /* if:<expr> */ / /* endif */ comment directives in CSS content
    and interpolates <&var> variables.
    """
    if_re = re.compile(r"/\*\s*if:(.*?)\s*\*/", re.IGNORECASE)
    endif_re = re.compile(r"/\*\s*endif(?::.*?)?\s*\*/", re.IGNORECASE)

    lines = content.splitlines(keepends=True)
    result = []
    stack: List[bool] = []

    for line in lines:
        if_match = if_re.search(line)
        if if_match:
            cond_expr = if_match.group(1).strip()
            cond_met = evaluate_condition(cond_expr, settings)
            parent_active = stack[-1] if stack else True
            stack.append(parent_active and cond_met)

            line_without = if_re.sub("", line).strip()
            if not line_without:
                continue
            line = if_re.sub("", line)

        endif_match = endif_re.search(line)
        if endif_match:
            if stack:
                stack.pop()
            line_without = endif_re.sub("", line).strip()
            if not line_without:
                continue
            line = endif_re.sub("", line)

        current_active = stack[-1] if stack else True
        if current_active:
            result.append(line)

    text = "".join(result)
    return interpolate_variables(text, settings)

