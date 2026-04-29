import os
import re
from dataclasses import dataclass, field

from core import base, config, utils
from core.conflict_models import BlacklistConflict, ConflictReport, FileConflict, StyleConflict
from core.conflict_rules import KNOWN_CONFLICTS, canonical_mod_id, normalize_mod_id
from core.patch_priority import sort_mods

STYLE_MARKER_RE = re.compile(r"/\*\s*([cg]):(.*?)\s*\*/")
DEFINE_RE = re.compile(r"@define\s+([\w-]+)\s*:")
KEYFRAME_RE = re.compile(r"@keyframes\s+(?:'|\")?([\w\s-]+)(?:'|\")?")
SELECTOR_RE = re.compile(r"(?m)(?:^|[}\n])\s*([^@{}][^{};]+?)\s*\{")


@dataclass(frozen=True)
class _StyleEdit:
    mod: str
    path: str
    scope: str
    selectors: set[str] = field(default_factory=set)
    defines: set[str] = field(default_factory=set)
    keyframes: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class _BlacklistRule:
    mod: str
    value: str
    raw: str
    rule_type: str
    line_number: int
    pattern: re.Pattern | None = None

    def matches(self, path: str) -> bool:
        if self.rule_type == "file":
            return path == self.value
        if self.rule_type == "directory":
            directory = self.value.rstrip("/")
            return path == directory or path.startswith(f"{directory}/")
        if self.rule_type == "pattern" and self.pattern is not None:
            return bool(self.pattern.search(path))
        return False


@dataclass
class _BlacklistData:
    mod: str
    exact_paths: set[str] = field(default_factory=set)
    explicit_paths: set[str] = field(default_factory=set)
    include_rules: list[_BlacklistRule] = field(default_factory=list)
    exclude_rules: list[_BlacklistRule] = field(default_factory=list)

    def matches(self, path: str) -> bool:
        if any(rule.matches(path) for rule in self.exclude_rules):
            return False
        return path in self.exact_paths or any(rule.matches(path) for rule in self.include_rules)


@dataclass
class _ModScan:
    mod: str
    files: dict[str, set[str]] = field(default_factory=dict)
    style_edits: list[_StyleEdit] = field(default_factory=list)
    blacklist: _BlacklistData | None = None
    mod_cfg: dict = field(default_factory=dict)


class ConflictAnalyzer:
    def __init__(self, mods_root: str | None = None, gamepakcontents_path: str | None = None):
        self.mods_root = mods_root or base.mods_dir
        self.gamepakcontents_path = gamepakcontents_path or os.path.join(base.bin_dir, "gamepakcontents.txt")
        self._gamepak_contents: list[str] | None = None

    def scan(self, selected_mods) -> ConflictReport:
        report = ConflictReport()
        selected_mods = self._dedupe_mods(selected_mods)
        order_map = {mod: index for index, mod in enumerate(selected_mods)}

        scans = []
        for mod in selected_mods:
            if mod.endswith(".vpk"):
                continue

            mod_path = os.path.join(self.mods_root, mod)
            if not os.path.isdir(mod_path):
                report.warnings.append(f"Selected mod '{mod}' is missing from the mods directory.")
                continue

            scans.append(self._scan_mod(mod, mod_path, report))

        self._find_file_conflicts(scans, report, order_map)
        self._find_style_conflicts(scans, report, order_map)
        self._find_blacklist_conflicts(scans, report, order_map)
        self._find_declared_conflicts(scans, report, selected_mods)
        self._find_known_conflicts(selected_mods, report)
        self._add_recommendations(report, selected_mods)

        return report

    def _scan_mod(self, mod: str, mod_path: str, report: ConflictReport) -> _ModScan:
        mod_cfg = config.read_json_file(os.path.join(mod_path, "modcfg.json"))
        scan = _ModScan(mod=mod, mod_cfg=mod_cfg)

        self._scan_file_tree(scan, mod_path, "files")
        self._scan_file_tree(scan, mod_path, "files_uncompiled")
        scan.style_edits.extend(self._scan_styles(mod, mod_path, report))
        scan.blacklist = self._scan_blacklist(mod, mod_path, report)

        return scan

    def _scan_file_tree(self, scan: _ModScan, mod_path: str, directory_name: str) -> None:
        root = os.path.join(mod_path, directory_name)
        if not os.path.isdir(root):
            return

        for current_dir, _, filenames in os.walk(root):
            for filename in filenames:
                if filename == ".gitkeep":
                    continue

                full_path = os.path.join(current_dir, filename)
                relative_path = os.path.relpath(full_path, root)
                game_path = self._normalize_game_path(relative_path)
                if game_path:
                    scan.files.setdefault(game_path, set()).add(directory_name)

    def _scan_styles(self, mod: str, mod_path: str, report: ConflictReport) -> list[_StyleEdit]:
        style_path = os.path.join(mod_path, "styling.css")
        if not os.path.exists(style_path):
            return []

        try:
            with utils.open_utf8R(style_path) as file:
                content = file.read()
        except OSError as err:
            report.warnings.append(f"Could not read styling.css for '{mod}': {err}")
            return []

        edits = []
        matches = list(STYLE_MARKER_RE.finditer(content))
        for index, match in enumerate(matches):
            indicator = match.group(1)
            raw_path = match.group(2).strip()
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
            style = content[start:end].strip()
            if not raw_path or not style:
                continue

            selectors, defines, keyframes = self._extract_style_tokens(style)
            edits.append(
                _StyleEdit(
                    mod=mod,
                    path=self._style_target_path(raw_path),
                    scope="core" if indicator == "c" else "game",
                    selectors=selectors,
                    defines=defines,
                    keyframes=keyframes,
                )
            )

        return edits

    def _scan_blacklist(self, mod: str, mod_path: str, report: ConflictReport) -> _BlacklistData:
        blacklist = _BlacklistData(mod=mod)
        blacklist_path = os.path.join(mod_path, "blacklist.txt")
        if not os.path.exists(blacklist_path):
            return blacklist

        try:
            with utils.open_utf8R(blacklist_path) as file:
                lines = file.readlines()
        except OSError as err:
            report.warnings.append(f"Could not read blacklist.txt for '{mod}': {err}")
            return blacklist

        for line_number, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            rule = self._parse_blacklist_rule(mod, line, line_number, report)
            if rule is None:
                continue

            if line.startswith(("--", "*-")):
                blacklist.exclude_rules.append(rule)
            elif rule.rule_type == "file":
                blacklist.explicit_paths.add(rule.value)
                blacklist.exact_paths.add(rule.value)
            else:
                blacklist.include_rules.append(rule)

        gamepak_contents = self._load_gamepak_contents()
        if gamepak_contents:
            for rule in blacklist.include_rules:
                blacklist.exact_paths.update(path for path in gamepak_contents if rule.matches(path))

            for rule in blacklist.exclude_rules:
                blacklist.exact_paths = {path for path in blacklist.exact_paths if not rule.matches(path)}

        return blacklist

    def _parse_blacklist_rule(
        self,
        mod: str,
        line: str,
        line_number: int,
        report: ConflictReport,
    ) -> _BlacklistRule | None:
        if line.startswith(">>"):
            return _BlacklistRule(
                mod=mod,
                value=self._normalize_game_path(line[2:]),
                raw=line,
                rule_type="directory",
                line_number=line_number,
            )
        if line.startswith(("**", "*-")):
            pattern_text = line[2:]
            try:
                pattern = re.compile(pattern_text)
            except re.error as err:
                report.warnings.append(f"Invalid blacklist pattern in '{mod}' line {line_number}: {err}")
                return None

            return _BlacklistRule(
                mod=mod,
                value=pattern_text,
                raw=line,
                rule_type="pattern",
                line_number=line_number,
                pattern=pattern,
            )
        if line.startswith("--"):
            return _BlacklistRule(
                mod=mod,
                value=self._normalize_game_path(line[2:]),
                raw=line,
                rule_type="file",
                line_number=line_number,
            )

        return _BlacklistRule(
            mod=mod,
            value=self._normalize_game_path(line),
            raw=line,
            rule_type="file",
            line_number=line_number,
        )

    def _find_file_conflicts(
        self,
        scans: list[_ModScan],
        report: ConflictReport,
        order_map: dict[str, int],
    ) -> None:
        owners_by_path: dict[str, dict[str, set[str]]] = {}
        for scan in scans:
            for path, sources in scan.files.items():
                owners_by_path.setdefault(path, {}).setdefault(scan.mod, set()).update(sources)

        for path, owners in owners_by_path.items():
            if len(owners) < 2:
                continue

            mods = self._sort_mods(owners.keys(), order_map)
            sources = sorted({source for mod_sources in owners.values() for source in mod_sources})
            report.file_conflicts.append(
                FileConflict(
                    path=path,
                    mods=tuple(mods),
                    sources=tuple(sources),
                )
            )

    def _find_style_conflicts(
        self,
        scans: list[_ModScan],
        report: ConflictReport,
        order_map: dict[str, int],
    ) -> None:
        edits_by_target: dict[tuple[str, str], list[_StyleEdit]] = {}
        for scan in scans:
            for edit in scan.style_edits:
                edits_by_target.setdefault((edit.scope, edit.path), []).append(edit)

        for (scope, path), edits in edits_by_target.items():
            mods = self._sort_mods({edit.mod for edit in edits}, order_map)
            if len(mods) < 2:
                continue

            shared_selectors = self._shared_style_tokens(edits, "selectors")
            shared_defines = self._shared_style_tokens(edits, "defines")
            shared_keyframes = self._shared_style_tokens(edits, "keyframes")

            if shared_selectors or shared_defines or shared_keyframes:
                report.style_conflicts.append(
                    StyleConflict(
                        path=path,
                        mods=tuple(mods),
                        scope=scope,
                        selectors=tuple(shared_selectors),
                        defines=tuple(shared_defines),
                        keyframes=tuple(shared_keyframes),
                        reason="Selected mods edit the same stylesheet target and reuse CSS scopes.",
                    )
                )
                continue

            report.warnings.append(
                f"Multiple selected mods append styling to {scope}:{path}: {', '.join(mods)}. "
                "Final cascade order may change the HUD result."
            )

    def _find_blacklist_conflicts(
        self,
        scans: list[_ModScan],
        report: ConflictReport,
        order_map: dict[str, int],
    ) -> None:
        explicit_blacklist_owners: dict[str, set[str]] = {}
        rule_owners: dict[str, set[str]] = {}
        blacklists = [scan.blacklist for scan in scans if scan.blacklist is not None]

        for blacklist in blacklists:
            for path in blacklist.explicit_paths:
                explicit_blacklist_owners.setdefault(path, set()).add(blacklist.mod)
            for rule in blacklist.include_rules:
                rule_owners.setdefault(f"{rule.rule_type}:{rule.value}", set()).add(blacklist.mod)

        seen: set[tuple[str, tuple[str, ...], tuple[str, ...], str]] = set()
        for path, owners in explicit_blacklist_owners.items():
            if len(owners) < 2:
                continue

            mods = tuple(self._sort_mods(owners, order_map))
            self._add_blacklist_conflict(
                report,
                seen,
                BlacklistConflict(
                    path=path,
                    mods=mods,
                    reason="Multiple selected mods explicitly blacklist the same file.",
                ),
            )

        for rule_key, owners in rule_owners.items():
            if len(owners) < 2:
                continue

            mods = tuple(self._sort_mods(owners, order_map))
            self._add_blacklist_conflict(
                report,
                seen,
                BlacklistConflict(
                    path=rule_key,
                    mods=mods,
                    reason="Multiple selected mods use the same blacklist rule.",
                ),
            )

        file_owners = self._file_owners(scans)
        for path, owners in file_owners.items():
            blacklist_mods = [blacklist.mod for blacklist in blacklists if blacklist.matches(path)]
            if not blacklist_mods:
                continue

            affected_mods = [mod for mod in owners if mod not in blacklist_mods]
            if not affected_mods:
                continue

            mods = tuple(self._sort_mods(blacklist_mods, order_map))
            affected = tuple(self._sort_mods(affected_mods, order_map))
            self._add_blacklist_conflict(
                report,
                seen,
                BlacklistConflict(
                    path=path,
                    mods=mods,
                    affected_mods=affected,
                    reason="A selected mod blacklists a file shipped by another selected mod.",
                ),
            )

    def _find_declared_conflicts(
        self,
        scans: list[_ModScan],
        report: ConflictReport,
        selected_mods: list[str],
    ) -> None:
        selected_lookup = self._selected_lookup(selected_mods)
        seen_pairs = set()

        for scan in scans:
            conflicts = scan.mod_cfg.get("conflicts", [])
            if not isinstance(conflicts, list):
                continue

            for conflict in conflicts:
                if not isinstance(conflict, str):
                    continue

                active_conflict = self._lookup_selected_mod(conflict, selected_lookup)
                if active_conflict is None or active_conflict == scan.mod:
                    continue

                pair = tuple(sorted((scan.mod, active_conflict)))
                if pair in seen_pairs:
                    continue

                seen_pairs.add(pair)
                report.warnings.append(
                    f"Declared conflict: {scan.mod} conflicts with {active_conflict}. Disable one of them."
                )

    def _find_known_conflicts(self, selected_mods: list[str], report: ConflictReport) -> None:
        canonical_to_mods: dict[str, list[str]] = {}
        for mod in selected_mods:
            canonical_to_mods.setdefault(canonical_mod_id(mod), []).append(mod)

        for (left, right), reason in KNOWN_CONFLICTS.items():
            left_mods = canonical_to_mods.get(left, [])
            right_mods = canonical_to_mods.get(right, [])
            if not left_mods or not right_mods:
                continue

            for left_mod in left_mods:
                for right_mod in right_mods:
                    if left_mod == right_mod:
                        continue
                    report.warnings.append(f"Known conflict: {left_mod} conflicts with {right_mod}. {reason}.")

    def _add_recommendations(self, report: ConflictReport, selected_mods: list[str]) -> None:
        suggested_order = sort_mods(selected_mods)
        report.suggested_patch_order = suggested_order

        if suggested_order != selected_mods:
            report.recommendations.append("Suggested patch order: " + " -> ".join(suggested_order))

        if report.file_conflicts:
            report.recommendations.append(
                "Keep only one selected mod for each shared file unless the overwrite is intentional."
            )
        if report.style_conflicts:
            report.recommendations.append(
                "Apply broad HUD layout mods later, or disable one of the overlapping style edits."
            )
        if report.blacklist_conflicts:
            report.recommendations.append(
                "Review blacklist.txt collisions before patching; blank files can override shipped mod assets."
            )

    def _load_gamepak_contents(self) -> list[str]:
        if self._gamepak_contents is not None:
            return self._gamepak_contents

        if not os.path.exists(self.gamepakcontents_path):
            self._gamepak_contents = []
            return self._gamepak_contents

        with utils.try_pass():
            with utils.open_utf8R(self.gamepakcontents_path) as file:
                self._gamepak_contents = [self._normalize_game_path(line) for line in file if line.strip()]

        if self._gamepak_contents is None:
            self._gamepak_contents = []
        return self._gamepak_contents

    def _extract_style_tokens(self, style: str) -> tuple[set[str], set[str], set[str]]:
        cleaned = re.sub(r"/\*.*?\*/", "", style, flags=re.DOTALL)
        defines = {token.strip() for token in DEFINE_RE.findall(cleaned) if token.strip()}
        keyframes = {" ".join(token.split()) for token in KEYFRAME_RE.findall(cleaned) if token.strip()}
        selectors = set()

        for match in SELECTOR_RE.finditer(cleaned):
            selector_group = match.group(1).strip()
            if not selector_group or selector_group.startswith(("@define", "@keyframes")):
                continue

            for selector in selector_group.split(","):
                selector = " ".join(selector.split())
                if selector and selector not in {"from", "to", "progress"}:
                    selectors.add(selector)

        return selectors, defines, keyframes

    def _style_target_path(self, raw_path: str) -> str:
        path = self._normalize_game_path(raw_path)
        root, ext = os.path.splitext(path)

        if ext in {".css", ".vcss"}:
            return f"{root}.vcss_c"
        if path.endswith(".vcss_c"):
            return path
        return f"{path}.vcss_c"

    def _shared_style_tokens(self, edits: list[_StyleEdit], attribute: str) -> list[str]:
        owners: dict[str, set[str]] = {}
        for edit in edits:
            for token in getattr(edit, attribute):
                owners.setdefault(token, set()).add(edit.mod)

        return sorted(token for token, mods in owners.items() if len(mods) > 1)

    def _file_owners(self, scans: list[_ModScan]) -> dict[str, set[str]]:
        owners: dict[str, set[str]] = {}
        for scan in scans:
            for path in scan.files:
                owners.setdefault(path, set()).add(scan.mod)
        return owners

    def _add_blacklist_conflict(
        self,
        report: ConflictReport,
        seen: set[tuple[str, tuple[str, ...], tuple[str, ...], str]],
        conflict: BlacklistConflict,
    ) -> None:
        key = (conflict.path, conflict.mods, conflict.affected_mods, conflict.reason)
        if key in seen:
            return

        seen.add(key)
        report.blacklist_conflicts.append(conflict)

    def _selected_lookup(self, selected_mods: list[str]) -> dict[str, str]:
        lookup = {}
        for mod in selected_mods:
            lookup[mod] = mod
            lookup[normalize_mod_id(mod)] = mod
            lookup[canonical_mod_id(mod)] = mod
        return lookup

    def _lookup_selected_mod(self, mod_name: str, selected_lookup: dict[str, str]) -> str | None:
        return (
            selected_lookup.get(mod_name)
            or selected_lookup.get(normalize_mod_id(mod_name))
            or selected_lookup.get(canonical_mod_id(mod_name))
        )

    def _dedupe_mods(self, selected_mods) -> list[str]:
        deduped = []
        seen = set()
        for mod in selected_mods or []:
            if not isinstance(mod, str) or mod in seen:
                continue
            seen.add(mod)
            deduped.append(mod)
        return deduped

    def _sort_mods(self, mods, order_map: dict[str, int]) -> list[str]:
        return sorted(mods, key=lambda mod: order_map.get(mod, len(order_map)))

    def _normalize_game_path(self, path: str) -> str:
        normalized = path.replace("\\", "/").strip()
        while normalized.startswith("./"):
            normalized = normalized[2:]
        return normalized.lstrip("/").lower()
