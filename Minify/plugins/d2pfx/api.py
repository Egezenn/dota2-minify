import os
import re
import tempfile
from typing import Any, Dict, List

from core import base, config, fs, mods_shared, output, utils
from core.plugin_sdk import PluginRouter

from . import __main__ as plugin_main
from .data import DataManager

router = PluginRouter()
D2PFX_INSTALLS_KEY = "d2pfx_installs"


def _install_records() -> Dict[str, Dict[str, Any]]:
    states = utils.read_states()
    records = states.get(D2PFX_INSTALLS_KEY, {})
    if not isinstance(records, dict):
        return {}

    normalized = {}
    for key, record in records.items():
        if not isinstance(record, dict):
            continue
        category = record.get("category")
        name = record.get("name")
        label = record.get("label")
        if isinstance(category, str) and isinstance(name, str):
            normalized_key = _install_key(category, name, label)
        else:
            normalized_key = key.removesuffix("::") if isinstance(key, str) else key
        normalized[normalized_key] = {field: record[field] for field in ("source_date", "folder") if field in record}

    if normalized != records:
        utils.write_states(D2PFX_INSTALLS_KEY, normalized)
    return normalized


def reconcile_install_states() -> None:
    records = _install_records()
    valid_records = {
        key: record
        for key, record in records.items()
        if isinstance(record.get("folder"), str) and os.path.isdir(os.path.join(base.mods_dir, record["folder"]))
    }
    if valid_records != records:
        utils.write_states(D2PFX_INSTALLS_KEY, valid_records)


def _install_key(category: str, name: str, label: str = None) -> str:
    key = f"{category}::{name}"
    return f"{key}::{label}" if label else key


def _save_install_record(record: Dict[str, Any]) -> None:
    records = _install_records()
    records[_install_key(record["category"], record["name"], record.get("label"))] = {
        "source_date": record.get("source_date"),
        "folder": record["folder"],
    }
    utils.write_states(D2PFX_INSTALLS_KEY, records)


def _source_date(mod: Dict[str, Any]):
    meta = mod.get("meta")
    return meta.get("date") if isinstance(meta, dict) else None


@router.route
def get_categories(params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    dm = DataManager()
    if dm.load():
        categories = dm.get_categories()
        res = []
        for cat_id in categories:
            res.append(
                {
                    "id": cat_id,
                    "name": dm.get_category_name(cat_id),
                    "description": dm.get_category_description(cat_id),
                }
            )
        return res
    return []


@router.route
def get_mods(params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    params = params or {}
    cat_id = params.get("cat_id", "")
    search = params.get("search", "")
    sort_mode = params.get("sort_mode", "")

    dm = DataManager()
    if not dm.load():
        return []

    raw_mods = dm.get_mods(cat_id)

    expanded_mods = []
    for m in raw_mods:
        if "styles" in m and isinstance(m["styles"], list):
            for style in m["styles"]:
                m_style = dict(m)
                m_style.update(style)
                expanded_mods.append(m_style)
        else:
            expanded_mods.append(dict(m))

    filter_nsfw = bool(config.get("d2pfx_filter_nsfw", True))
    filter_anime = bool(config.get("d2pfx_filter_anime", False))

    filtered = []
    for m in expanded_mods:
        tags = m.get("tags", {})
        if filter_nsfw:
            is_adult = False
            if isinstance(tags, dict):
                is_adult = any(k.lower() == "adult" and v for k, v in tags.items())
            elif isinstance(tags, list):
                is_adult = any(str(t).lower() == "adult" for t in tags)
            if is_adult:
                continue

        if filter_anime:
            is_anime = False
            if isinstance(tags, dict):
                is_anime = any(k.lower() == "anime" and v for k, v in tags.items())
            elif isinstance(tags, list):
                is_anime = any(str(t).lower() == "anime" for t in tags)
            if is_anime:
                continue

        filtered.append(m)

    if search:
        tokens = re.findall(r"(?:by:|tag:|sort:)?\S+", search.lower())
        for token in tokens:
            if token.startswith("by:"):
                val = token[3:]
                if val:

                    def _has_author(m):
                        a = m.get("author")
                        if not a:
                            return False
                        if isinstance(a, list):
                            return any(val in str(x).lower() for x in a)
                        return val in str(a).lower()

                    filtered = [m for m in filtered if _has_author(m)]
            elif token.startswith("tag:"):
                val = token[4:]
                if val:
                    filtered = [m for m in filtered if any(val in str(t).lower() for t in (m.get("tags") or []))]
            elif token.startswith("sort:"):
                sort_mode = token[5:]
            else:
                filtered = [
                    m for m in filtered if token in m.get("name", "").lower() or token in m.get("label", "").lower()
                ]

    if sort_mode:
        if sort_mode == "a-z":
            filtered.sort(key=lambda m: m.get("name", "").lower())
        elif sort_mode == "z-a":
            filtered.sort(key=lambda m: m.get("name", "").lower(), reverse=True)
        elif sort_mode == "new":
            filtered.sort(key=lambda m: m.get("meta", {}).get("date", 0), reverse=True)
        elif sort_mode == "old":
            filtered.sort(key=lambda m: m.get("meta", {}).get("date", 0))

    for m in filtered:
        prev = m.get("preview")
        if prev and not prev.startswith("http"):
            m["preview_url"] = dm.get_preview_url(cat_id, prev)
        elif prev:
            m["preview_url"] = prev
        else:
            m["preview_url"] = None

    return filtered


def _resolve_mod_folder(name: str, cat_id: str, label: str = None) -> str:
    from patch import manifest_utils

    if os.path.exists(base.mods_dir):
        for folder in os.listdir(base.mods_dir):
            mod_path = os.path.join(base.mods_dir, folder)
            if not os.path.isdir(mod_path):
                continue
            cfg = manifest_utils.get_mod(mod_path)
            if (
                cfg.get("browser") == "d2pfx"
                and cfg.get("name") == name
                and cfg.get("category") == cat_id
                and cfg.get("label") == label
            ):
                return folder

    mod_dir_name = f"D2PFX {cat_id.upper()} - {name}"
    if label:
        mod_dir_name = f"{mod_dir_name} {label}"
    return utils.sanitize_win_path(mod_dir_name)


@router.route
def get_installed_mods(params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    from patch import manifest_utils

    installed = []
    records = _install_records()
    if not os.path.exists(base.mods_dir):
        return []
    for folder in os.listdir(base.mods_dir):
        mod_path = os.path.join(base.mods_dir, folder)
        if not os.path.isdir(mod_path):
            continue
        cfg = manifest_utils.get_mod(mod_path)
        if cfg.get("browser") == "d2pfx":
            record = records.get(_install_key(cfg.get("category", ""), cfg.get("name", ""), cfg.get("label")), {})
            installed.append(
                {
                    "name": cfg.get("name"),
                    "category": cfg.get("category"),
                    "label": cfg.get("label"),
                    "folder": folder,
                    "enabled": mods_shared.get_state(folder),
                    "source_date": record.get("source_date", cfg.get("source_date"))
                    if isinstance(record, dict)
                    else cfg.get("source_date"),
                }
            )
    return installed


@router.route
def set_mod_state(params: Dict[str, Any] = None) -> Dict[str, Any]:
    params = params or {}
    mod_name = params.get("mod_name") or params.get("name", "")
    cat_id = params.get("cat_id", "")
    label = params.get("label")
    enabled = bool(params.get("enabled", True))

    folder = _resolve_mod_folder(mod_name, cat_id, label)
    mods_shared.set_state(folder, enabled)
    return {"success": True, "folder": folder, "enabled": enabled}


@router.route
def install_mod(params: Dict[str, Any] = None) -> Dict[str, Any]:
    return _install_mod(params)


@router.route
def update_mod(params: Dict[str, Any] = None) -> Dict[str, Any]:
    params = params or {}
    mod = params.get("mod", {})
    cat_id = params.get("cat_id", "")
    target_dir = os.path.join(base.mods_dir, _resolve_mod_folder(mod.get("name", ""), cat_id, mod.get("label")))
    if not os.path.isdir(target_dir):
        return {"success": False, "error": "Installed mod directory not found."}
    return _install_mod(params, update_target=target_dir)


def _install_mod(params: Dict[str, Any] = None, update_target: str = None) -> Dict[str, Any]:
    params = params or {}
    mod = params.get("mod", {})
    cat_id = params.get("cat_id", "")

    dm = DataManager()
    name = mod.get("name", "Unknown")
    label = mod.get("label")
    author = mod.get("author")
    sender = mod.get("sender")
    tags = mod.get("tags", [])
    links = mod.get("links", [])

    vpk_link = next((link for link in links if link.get("url", "").endswith(".vpk")), None)
    zip_link = next((link for link in links if link.get("url", "").endswith(".zip")), None)
    mod_url = None
    is_zip = False

    if mod.get("file"):
        f = mod.get("file")
        if f.endswith(".vpk"):
            mod_url = f
        elif f.endswith(".zip"):
            mod_url = f
            is_zip = True

    if not mod_url:
        if vpk_link:
            mod_url = vpk_link["url"]
        elif zip_link:
            mod_url = zip_link["url"]
            is_zip = True

    if not mod_url:
        return {"success": False, "error": f"No compatible mod file (.vpk/.zip) found for '{name}'."}

    if not mod_url.startswith("http"):
        mod_url = dm.get_file_url(cat_id, mod_url)

    mod_dir_name = f"D2PFX {cat_id.upper()} - {name}"
    if label:
        mod_dir_name = f"{mod_dir_name} {label}"
    final_target_dir = update_target or os.path.join(base.mods_dir, utils.sanitize_win_path(mod_dir_name))
    target_dir = tempfile.mkdtemp(prefix=".d2pfx-update-", dir=base.mods_dir) if update_target else final_target_dir

    fs.create_dirs(target_dir)

    # 1. Download Mod File and Preview File concurrently
    import concurrent.futures

    mod_dest = os.path.join(target_dir, os.path.basename(mod_url))

    preview_file = mod.get("preview")
    preview_url = None
    preview_dest = None
    if preview_file:
        preview_url = preview_file if preview_file.startswith("http") else dm.get_preview_url(cat_id, preview_file)
        preview_dest = os.path.join(target_dir, "preview.webp")

    def _download_preview():
        if preview_url and preview_dest:
            dm.download_file(
                preview_url,
                preview_dest,
                emit_progress=False,
                fallback_url=dm.to_hf_fallback(preview_url),
            )

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_preview = executor.submit(_download_preview) if preview_url else None
        future_mod = executor.submit(
            dm.download_file,
            mod_url,
            mod_dest,
            None,
            f"{name} ({cat_id.upper()})",
            True,
            dm.to_hf_fallback(mod_url),
        )

        mod_success = future_mod.result()
        if future_preview:
            try:
                future_preview.result()
            except Exception:
                pass

    if not mod_success:
        fs.remove_path(target_dir)
        return {"success": False, "error": "Failed to download mod file."}

    # Extract if zip
    if is_zip:
        if not fs.extract_archive(mod_dest, target_dir):
            fs.remove_path(target_dir)
            return {"success": False, "error": "Failed to extract mod archive."}
        fs.remove_path(mod_dest)

    # 3. Create manifest.json
    if isinstance(tags, dict):
        active_tags = [k for k, v in tags.items() if v]
    elif isinstance(tags, list):
        active_tags = tags
    elif tags is None:
        active_tags = []
    else:
        active_tags = [str(tags)]

    modcfg = {
        "browser": "d2pfx",
        "name": name,
        "category": cat_id,
        "author": author,
        "sender": sender,
        "links": links,
        "tags": active_tags,
        "version": plugin_main.VERSION,
        "label": label,
        "source_date": _source_date(mod),
    }
    rename_cats = plugin_main.RENAME_CATEGORIES

    if cat_id in rename_cats:
        modcfg["order"] = 2

    config.write_json_file(os.path.join(target_dir, "manifest.json"), modcfg)

    # 4. Create notes.md
    version = modcfg.get("version") or plugin_main.VERSION
    notes_content = f"Installed via D2PFX Browser {version}\n\n"
    if cat_id and cat_id.lower() != "unknown":
        notes_content += f"Category: {cat_id}\n"

    type_labels = {
        "author": "Author",
        "source": "Source",
        "modded": "Modded",
        "sender": "Sender",
    }

    for t_key in ["author", "source", "modded", "sender"]:
        t_links = [l for l in links if l.get("type") == t_key]
        t_vals = [l.get("name") or l.get("url") for l in t_links]
        t_vals = [x for x in t_vals if x]
        if t_vals:
            notes_content += f"{type_labels[t_key]}: {', '.join(t_vals)}\n"

    if tags:
        if isinstance(tags, dict):
            active_tags = [k for k, v in tags.items() if v]
        elif isinstance(tags, list):
            active_tags = tags
        else:
            active_tags = [str(tags)]
        if active_tags:
            notes_content += f"Tags: {', '.join(active_tags)}\n"

    with open(os.path.join(target_dir, "notes.md"), "w", encoding="utf-8") as f:
        f.write(notes_content)

    if update_target:
        backup_dir = tempfile.mkdtemp(prefix=".d2pfx-backup-", dir=base.mods_dir)
        os.rmdir(backup_dir)
        os.replace(final_target_dir, backup_dir)
        try:
            os.replace(target_dir, final_target_dir)
        except OSError:
            os.replace(backup_dir, final_target_dir)
            fs.remove_path(target_dir)
            raise
        fs.remove_path(backup_dir)

    _save_install_record({**modcfg, "folder": os.path.basename(final_target_dir)})
    if update_target is None:
        mods_shared.set_state(os.path.basename(final_target_dir), True)
    mods_shared.scan_mods()
    output.add_text(f"D2PFX mod '{name}' installed successfully.", msg_type="success")

    return {"success": True, "folder": os.path.basename(final_target_dir)}


@router.route
def uninstall_mod(params: Dict[str, Any] = None) -> Dict[str, Any]:
    params = params or {}
    mod_name = params.get("mod_name")
    cat_id = params.get("cat_id")
    label = params.get("label")

    from patch import manifest_utils

    target_dir = None
    target_folder = None
    if os.path.exists(base.mods_dir):
        for folder in os.listdir(base.mods_dir):
            mod_path = os.path.join(base.mods_dir, folder)
            if not os.path.isdir(mod_path):
                continue
            cfg = manifest_utils.get_mod(mod_path)
            if (
                cfg.get("browser") == "d2pfx"
                and cfg.get("name") == mod_name
                and cfg.get("category") == cat_id
                and cfg.get("label") == label
            ):
                target_dir = mod_path
                target_folder = folder
                break

    if not target_dir:
        mod_dir_name = f"D2PFX {cat_id.upper()} - {mod_name}"
        if label:
            mod_dir_name = f"{mod_dir_name} {label}"
        target_folder = utils.sanitize_win_path(mod_dir_name)
        possible_dir = os.path.join(base.mods_dir, target_folder)
        if os.path.exists(possible_dir):
            target_dir = possible_dir

    if target_dir and os.path.exists(target_dir):
        fs.remove_path(target_dir)
        records = _install_records()
        records.pop(_install_key(cat_id, mod_name, label), None)
        utils.write_states(D2PFX_INSTALLS_KEY, records)
        if target_folder:
            states = config.read_json_file(base.mods_config_dir)
            if target_folder in states:
                del states[target_folder]
                config.write_json_file(base.mods_config_dir, dict(sorted(states.items())))
        mods_shared.scan_mods()
        output.add_text(f"D2PFX mod '{mod_name}' removed.", msg_type="info")
        return {"success": True}
    else:
        return {"success": False, "error": "Mod directory not found."}


@router.route
def prune_metadata_cache(params: Dict[str, Any] = None) -> Dict[str, Any]:
    dm = DataManager()
    metadata_file = os.path.join(dm.cache_dir, "mods.json")
    constants_file = os.path.join(dm.cache_dir, "constants.json")
    fs.remove_path(metadata_file, constants_file)
    dm.metadata = {}
    dm.constants = {}
    success = dm.refresh()
    return {"success": success}


def handle_api(action: str, params: Dict[str, Any] = None) -> Any:
    return router.dispatch(action, params)
