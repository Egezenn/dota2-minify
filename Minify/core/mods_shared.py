"Shared mod scanning logic"

import os
import sys

import jsonc

from core import base, utils

mods_alphabetical = []
mods_with_order = []
visually_unavailable_mods = []
visually_available_mods = []
mod_dependencies_list = []
mod_conflicts_list = []

_get_state_callback = None
_set_state_callback = None


def register_state_callbacks(get_cb, set_cb):
    global _get_state_callback, _set_state_callback
    _get_state_callback = get_cb
    _set_state_callback = set_cb


def get_state(mod):
    if _get_state_callback:
        return _get_state_callback(mod)

    try:
        with utils.open_utf8(base.mods_config_dir) as file:
            states = jsonc.load(file)
            return states.get(mod, False)
    except Exception:
        return False


def set_state(mod, value):
    if _set_state_callback:
        return _set_state_callback(mod, value)

    try:
        states = {}
        if os.path.exists(base.mods_config_dir):
            with utils.open_utf8(base.mods_config_dir) as file:
                states = jsonc.load(file)

        states[mod] = value
        with utils.open_utf8(base.mods_config_dir, "w") as file:
            jsonc.dump(states, file, indent=2)
    except Exception:
        pass


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
        if not mod.startswith("_"):
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
