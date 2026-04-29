import re

PATCH_PRIORITY = {
    "mute": 100,
    "remove": 90,
    "transparent_hud": 80,
    "hud_reposition": 70,
}

KNOWN_CONFLICTS = {
    ("transparent_hud", "hud_reposition"): "Both modify HUD layout heavily",
}

MOD_ALIASES = {
    "reposition_rescale_hud": "hud_reposition",
}

DEFAULT_PATCH_PRIORITY = 50


def normalize_mod_id(mod_name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", mod_name.lower()).strip("_")
    return re.sub(r"_+", "_", normalized)


def canonical_mod_id(mod_name: str) -> str:
    normalized = normalize_mod_id(mod_name)
    return MOD_ALIASES.get(normalized, normalized)
