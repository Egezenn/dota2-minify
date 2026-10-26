"Parsing helpers for the --mods-string patch option."


def parse_mods_string(value: str) -> list[str]:
    r"""Split a comma-separated mod list, honoring \, and \\ escapes."""
    mods = []
    current = []
    index = 0

    def flush():
        name = "".join(current).strip()
        if name and name not in mods:
            mods.append(name)
        current.clear()

    while index < len(value):
        char = value[index]
        if char == "\\" and index + 1 < len(value) and value[index + 1] in (",", "\\"):
            current.append(value[index + 1])
            index += 2
            continue
        if char == ",":
            flush()
        else:
            current.append(char)
        index += 1

    flush()
    return mods


def select_mods(requested: list[str], available: list[str]) -> tuple[list[str], list[str]]:
    """Resolve requested names against available mods, case-insensitively."""
    canonical = {mod.casefold(): mod for mod in available}
    selected = []
    missing = []

    for name in requested:
        match = canonical.get(name.casefold())
        if match is None:
            missing.append(name)
        elif match not in selected:
            selected.append(match)

    return selected, missing
