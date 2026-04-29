import build

from core import constants
from core.conflict_analyzer import ConflictAnalyzer
from core.conflict_models import ConflictReport
from ui import modal_shared

MAX_FINDINGS_PER_SECTION = 4


def analyze_and_patch():
    build.resolve_dependencies_for_current_selection()
    selected_mods = build.get_active_mods()
    report = ConflictAnalyzer().scan(selected_mods)

    if report.has_conflicts():
        show_conflict_popup(report)
        return

    build.patcher()


def show_conflict_popup(report: ConflictReport):
    modal_shared.show(
        title="Potential conflicts detected",
        messages=_format_report_messages(report),
        buttons=[
            {
                "label": "Auto Fix Patch Order",
                "callback": _patch_with_suggested_order,
                "user_data": report,
                "width": 170,
            },
            {
                "label": "Patch Anyway",
                "callback": lambda s, a, u: build.patcher(),
                "width": 120,
            },
            {
                "label": "Cancel",
                "width": 90,
            },
        ],
    )


def _patch_with_suggested_order(sender=None, app_data=None, user_data=None):
    report = user_data
    if not isinstance(report, ConflictReport) or not report.suggested_patch_order:
        build.patcher()
        return

    build.patcher(mod_order=_merge_suggested_order(report.suggested_patch_order))


def _merge_suggested_order(suggested_order: list[str]) -> list[str]:
    suggested_mods = list(suggested_order)
    suggested_set = set(suggested_mods)
    merged_order = []
    suggested_index = 0

    for mod in constants.mods_with_order:
        if mod not in suggested_set:
            merged_order.append(mod)
            continue

        if suggested_index < len(suggested_mods):
            merged_order.append(suggested_mods[suggested_index])
            suggested_index += 1

    for mod in suggested_mods[suggested_index:]:
        if mod not in merged_order:
            merged_order.append(mod)

    return merged_order


def _format_report_messages(report: ConflictReport) -> list[str]:
    messages = [
        "Potential conflicts detected",
        "Selected mods touch overlapping files, styles, or blacklist rules. Review the warnings before patching.",
    ]

    for conflict in report.file_conflicts[:MAX_FINDINGS_PER_SECTION]:
        messages.append(f"Shared file: {conflict.path}")
        messages.append(f"Mods: {', '.join(conflict.mods)}")

    for conflict in report.style_conflicts[:MAX_FINDINGS_PER_SECTION]:
        details = []
        if conflict.selectors:
            details.append("selectors: " + ", ".join(conflict.selectors[:3]))
        if conflict.defines:
            details.append("defines: " + ", ".join(conflict.defines[:3]))
        if conflict.keyframes:
            details.append("keyframes: " + ", ".join(conflict.keyframes[:3]))

        messages.append(f"Style target: {conflict.scope}:{conflict.path}")
        messages.append(f"Mods: {', '.join(conflict.mods)}")
        if details:
            messages.append("; ".join(details))

    for conflict in report.blacklist_conflicts[:MAX_FINDINGS_PER_SECTION]:
        messages.append(f"Blacklist overlap: {conflict.path}")
        if conflict.affected_mods:
            messages.append(
                f"Blacklisted by {', '.join(conflict.mods)}; used by {', '.join(conflict.affected_mods)}"
            )
        else:
            messages.append(f"Mods: {', '.join(conflict.mods)}")

    for warning in report.warnings[:MAX_FINDINGS_PER_SECTION]:
        messages.append(warning)

    remaining = report.total_findings() - _visible_findings_count(report)
    if remaining > 0:
        messages.append(f"...and {remaining} more finding(s).")

    for recommendation in report.recommendations[:MAX_FINDINGS_PER_SECTION]:
        messages.append("Recommended: " + recommendation)

    return messages


def _visible_findings_count(report: ConflictReport) -> int:
    return (
        min(len(report.file_conflicts), MAX_FINDINGS_PER_SECTION)
        + min(len(report.style_conflicts), MAX_FINDINGS_PER_SECTION)
        + min(len(report.blacklist_conflicts), MAX_FINDINGS_PER_SECTION)
        + min(len(report.warnings), MAX_FINDINGS_PER_SECTION)
    )
