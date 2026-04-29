from dataclasses import dataclass, field


@dataclass(frozen=True)
class FileConflict:
    path: str
    mods: tuple[str, ...]
    sources: tuple[str, ...] = ()
    reason: str = "Multiple selected mods write the same game file."


@dataclass(frozen=True)
class StyleConflict:
    path: str
    mods: tuple[str, ...]
    scope: str = "game"
    selectors: tuple[str, ...] = ()
    defines: tuple[str, ...] = ()
    keyframes: tuple[str, ...] = ()
    reason: str = "Multiple selected mods modify the same stylesheet target."


@dataclass(frozen=True)
class BlacklistConflict:
    path: str
    mods: tuple[str, ...]
    affected_mods: tuple[str, ...] = ()
    reason: str = "Selected mods blacklist overlapping game files."


@dataclass
class ConflictReport:
    file_conflicts: list[FileConflict] = field(default_factory=list)
    style_conflicts: list[StyleConflict] = field(default_factory=list)
    blacklist_conflicts: list[BlacklistConflict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    suggested_patch_order: list[str] = field(default_factory=list)

    def has_conflicts(self) -> bool:
        return bool(
            self.file_conflicts
            or self.style_conflicts
            or self.blacklist_conflicts
            or self.warnings
        )

    def total_findings(self) -> int:
        return (
            len(self.file_conflicts)
            + len(self.style_conflicts)
            + len(self.blacklist_conflicts)
            + len(self.warnings)
        )
