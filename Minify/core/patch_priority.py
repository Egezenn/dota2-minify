from core.conflict_rules import DEFAULT_PATCH_PRIORITY, PATCH_PRIORITY, canonical_mod_id, normalize_mod_id


def priority_for_mod(mod_name: str) -> int:
    normalized = normalize_mod_id(mod_name)
    canonical = canonical_mod_id(mod_name)

    if canonical in PATCH_PRIORITY:
        return PATCH_PRIORITY[canonical]
    if normalized in PATCH_PRIORITY:
        return PATCH_PRIORITY[normalized]

    tokens = set(normalized.split("_"))
    matching_priorities = [priority for key, priority in PATCH_PRIORITY.items() if key in tokens]
    if matching_priorities:
        return max(matching_priorities)

    return DEFAULT_PATCH_PRIORITY


def sort_mods(mods):
    indexed_mods = list(enumerate(mods))
    sorted_mods = sorted(indexed_mods, key=lambda item: (priority_for_mod(item[1]), item[0]))
    return [mod for _, mod in sorted_mods]
