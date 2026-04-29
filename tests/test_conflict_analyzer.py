import os

from core.conflict_analyzer import ConflictAnalyzer
from core.patch_priority import sort_mods


def write_file(path, content=""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        file.write(content)


def test_scan_detects_file_and_blacklist_asset_conflicts(tmp_path):
    mods_root = os.path.join(str(tmp_path), "mods")
    shared_file = os.path.join("panorama", "styles", "hud", "topbar.vcss_c")

    write_file(os.path.join(mods_root, "Transparent HUD", "files", shared_file), "a")
    write_file(os.path.join(mods_root, "Reposition & Rescale HUD", "files", shared_file), "b")
    write_file(os.path.join(mods_root, "Remove HUD", "blacklist.txt"), shared_file)

    report = ConflictAnalyzer(mods_root=mods_root).scan(
        ["Transparent HUD", "Reposition & Rescale HUD", "Remove HUD"]
    )

    assert report.has_conflicts()
    assert len(report.file_conflicts) == 1
    assert report.file_conflicts[0].path == "panorama/styles/hud/topbar.vcss_c"
    assert report.file_conflicts[0].mods == ("Transparent HUD", "Reposition & Rescale HUD")

    blacklist_conflicts = [
        conflict for conflict in report.blacklist_conflicts if conflict.reason.startswith("A selected mod")
    ]
    assert len(blacklist_conflicts) == 1
    assert blacklist_conflicts[0].mods == ("Remove HUD",)
    assert blacklist_conflicts[0].affected_mods == ("Transparent HUD", "Reposition & Rescale HUD")


def test_scan_detects_style_scope_and_known_conflicts(tmp_path):
    mods_root = os.path.join(str(tmp_path), "mods")
    style = """
/* g:panorama/styles/hud/topbar */
.HudTopBar
{
    opacity: 0.4;
}
@define hud-offset: 10px;
"""

    write_file(os.path.join(mods_root, "Transparent HUD", "styling.css"), style)
    write_file(os.path.join(mods_root, "Reposition & Rescale HUD", "styling.css"), style)

    report = ConflictAnalyzer(mods_root=mods_root).scan(["Transparent HUD", "Reposition & Rescale HUD"])

    assert len(report.style_conflicts) == 1
    assert report.style_conflicts[0].path == "panorama/styles/hud/topbar.vcss_c"
    assert report.style_conflicts[0].selectors == (".HudTopBar",)
    assert report.style_conflicts[0].defines == ("hud-offset",)
    assert any("Known conflict" in warning for warning in report.warnings)
    assert report.suggested_patch_order == ["Reposition & Rescale HUD", "Transparent HUD"]


def test_blacklist_directory_rules_respect_exclusions(tmp_path):
    mods_root = os.path.join(str(tmp_path), "mods")
    gamepakcontents = os.path.join(str(tmp_path), "gamepakcontents.txt")
    blocked_file = "panorama/styles/hud/blocked.vcss_c"
    excluded_file = "panorama/styles/hud/excluded.vcss_c"

    write_file(gamepakcontents, f"{blocked_file}\n{excluded_file}\n")
    write_file(
        os.path.join(mods_root, "Remove HUD", "blacklist.txt"),
        f">>panorama/styles/hud\n--{excluded_file}\n",
    )
    write_file(os.path.join(mods_root, "HUD Asset Mod", "files", blocked_file), "blocked")
    write_file(os.path.join(mods_root, "HUD Asset Mod", "files", excluded_file), "excluded")

    report = ConflictAnalyzer(mods_root=mods_root, gamepakcontents_path=gamepakcontents).scan(
        ["Remove HUD", "HUD Asset Mod"]
    )

    conflict_paths = {conflict.path for conflict in report.blacklist_conflicts}
    assert blocked_file in conflict_paths
    assert excluded_file not in conflict_paths


def test_sort_mods_prioritizes_mute_and_remove_mods_last():
    mods = ["Mute Ambient Sounds", "Transparent HUD", "Tree Mod", "Remove River", "Reposition & Rescale HUD"]

    assert sort_mods(mods) == [
        "Tree Mod",
        "Reposition & Rescale HUD",
        "Transparent HUD",
        "Remove River",
        "Mute Ambient Sounds",
    ]
