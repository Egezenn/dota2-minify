"Shared mod scanning logic"

import os
import sys

from core import base, config

mods_alphabetical = []
mods_with_order = []
visually_unavailable_mods = []
visually_available_mods = []
mod_dependencies_list = []
mod_conflicts_list = []


def is_ignored_folder(name: str) -> bool:
    """Returns True if folder is a hidden or ignored directory (starts with . or _)."""
    return name.startswith((".", "_"))


def is_system_mod(name: str) -> bool:
    """Returns True if mod is an internal core system mod (starts with #)."""
    return name.startswith("#")


def is_user_mod(name: str) -> bool:
    """Returns True if mod is a user-selectable mod (not ignored and not a system mod)."""
    return not is_ignored_folder(name) and not is_system_mod(name)


def get_state(mod):
    states = config.read_json_file(base.mods_config_dir)
    return states.get(mod, False)


def set_state(mod, value):
    config.update_json_file(base.mods_config_dir, mod, value)


def enforce_locale_mod_states():
    from core import config, constants

    locale = config.get("output_locale", "english")

    all_locale_mods = set()
    for mods_list in constants.LOCALE_MOD_REQUIREMENTS.values():
        all_locale_mods.update(mods_list)

    required_for_current = set(constants.LOCALE_MOD_REQUIREMENTS.get(locale, []))

    for mod in all_locale_mods:
        set_state(mod, mod in required_for_current)


def scan_mods():
    from patch import manifest_utils

    global \
        mods_alphabetical, \
        mods_with_order, \
        visually_unavailable_mods, \
        visually_available_mods, \
        mod_dependencies_list, \
        mod_conflicts_list

    if not os.path.exists(base.mods_dir):
        sys.exit()

    _alphabetical = []
    _with_order = []
    _unavailable = []
    _available = []
    _dependencies = []
    _conflicts = []

    for mod in sorted(os.listdir(base.mods_dir), key=str.casefold):
        mod_path = os.path.join(base.mods_dir, mod)
        if not is_ignored_folder(mod):
            if os.path.isdir(mod_path):
                _alphabetical.append(mod)

                blacklist_exist = os.path.exists(os.path.join(mod_path, "blacklist.txt"))
                cfg = manifest_utils.get_mod(mod_path)
                order = cfg.get("order", 1)
                dependencies = cfg.get("dependencies", None)
                conflicts = cfg.get("conflicts", None)
                visual = cfg.get("visual", True)
                _available.append(mod) if visual else _unavailable.append(mod)
                if dependencies is not None:
                    _dependencies.append({mod: dependencies})
                if conflicts is not None:
                    _conflicts.append({mod: conflicts})

                # Default order, blacklist mods should always be indexed last
                if blacklist_exist and not cfg:
                    _with_order.append({mod: 2})
                else:
                    _with_order.append({mod: order})

            elif mod.endswith(".vpk"):
                _alphabetical.append(mod)
                _available.append(mod)
                _with_order.append({mod: 1})

    temp_sorted = sorted(_with_order, key=lambda d: list(d.values())[0])
    _with_order = [list(d.keys())[0] for d in temp_sorted]

    # In-place update so all references update
    mods_alphabetical[:] = _alphabetical
    mods_with_order[:] = _with_order
    visually_unavailable_mods[:] = _unavailable
    visually_available_mods[:] = _available
    mod_dependencies_list[:] = _dependencies
    mod_conflicts_list[:] = _conflicts
