import os
import re
from typing import Any, Dict, List

from core import base, config, fs, mods_shared, output, utils

from . import __main__ as plugin_main
from .data import DataManager


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


def get_installed_mods(params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    from patch import manifest_utils

    installed = []
    if not os.path.exists(base.mods_dir):
        return []
    for folder in os.listdir(base.mods_dir):
        mod_path = os.path.join(base.mods_dir, folder)
        if not os.path.isdir(mod_path):
            continue
        cfg = manifest_utils.get_mod(mod_path)
        browser_info = cfg.get("browser", {})
        if browser_info.get("browser") == "d2pfx":
            installed.append(
                {
                    "name": browser_info.get("name"),
                    "category": browser_info.get("category"),
                    "label": browser_info.get("label"),
                    "folder": folder,
                }
            )
    return installed


def install_mod(params: Dict[str, Any] = None) -> Dict[str, Any]:
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
    target_dir = os.path.join(base.mods_dir, utils.sanitize_win_path(mod_dir_name))

    fs.create_dirs(target_dir)

    # 1. Download Mod File
    mod_dest = os.path.join(target_dir, os.path.basename(mod_url))
    if not dm.download_file(mod_url, mod_dest, name=f"{name} ({cat_id.upper()})"):
        fs.remove_path(target_dir)
        return {"success": False, "error": "Failed to download mod file."}

    # Extract if zip
    if is_zip:
        if not fs.extract_archive(mod_dest, target_dir):
            fs.remove_path(target_dir)
            return {"success": False, "error": "Failed to extract mod archive."}
        fs.remove_path(mod_dest)

    # 2. Download Preview
    preview_file = mod.get("preview")
    if preview_file:
        preview_url = preview_file if preview_file.startswith("http") else dm.get_preview_url(cat_id, preview_file)
        preview_dest = os.path.join(target_dir, "preview.jpg")
        dm.download_file(preview_url, preview_dest)

    # 3. Create manifest.json
    modcfg = {
        "browser": {
            "browser": "d2pfx",
            "name": name,
            "category": cat_id,
            "author": author,
            "sender": sender,
            "links": links,
            "tags": tags,
            "version": plugin_main.VERSION,
            "label": label,
        },
    }
    rename_cats = plugin_main.RENAME_CATEGORIES

    if cat_id in rename_cats:
        modcfg["order"] = 2

    config.write_json_file(os.path.join(target_dir, "manifest.json"), modcfg)

    # 4. Create notes.md
    version = modcfg["browser"]["version"]
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

    mods_shared.scan_mods()
    output.add_text(f"D2PFX mod '{name}' installed successfully.", msg_type="success")

    return {"success": True, "folder": mod_dir_name}


def uninstall_mod(params: Dict[str, Any] = None) -> Dict[str, Any]:
    params = params or {}
    mod_name = params.get("mod_name")
    cat_id = params.get("cat_id")
    label = params.get("label")

    from patch import manifest_utils

    target_dir = None
    if os.path.exists(base.mods_dir):
        for folder in os.listdir(base.mods_dir):
            mod_path = os.path.join(base.mods_dir, folder)
            if not os.path.isdir(mod_path):
                continue
            cfg = manifest_utils.get_mod(mod_path)
            b_info = cfg.get("browser", {})
            if (
                b_info.get("browser") == "d2pfx"
                and b_info.get("name") == mod_name
                and b_info.get("category") == cat_id
                and b_info.get("label") == label
            ):
                target_dir = mod_path
                break

    if not target_dir:
        mod_dir_name = f"D2PFX {cat_id.upper()} - {mod_name}"
        if label:
            mod_dir_name = f"{mod_dir_name} {label}"
        possible_dir = os.path.join(base.mods_dir, utils.sanitize_win_path(mod_dir_name))
        if os.path.exists(possible_dir):
            target_dir = possible_dir

    if target_dir and os.path.exists(target_dir):
        fs.remove_path(target_dir)
        mods_shared.scan_mods()
        output.add_text(f"D2PFX mod '{mod_name}' removed.", msg_type="info")
        return {"success": True}
    else:
        return {"success": False, "error": "Mod directory not found."}


def prune_metadata_cache(params: Dict[str, Any] = None) -> Dict[str, Any]:
    dm = DataManager()
    metadata_file = os.path.join(dm.cache_dir, "mods.json")
    constants_file = os.path.join(dm.cache_dir, "constants.json")
    fs.remove_path(metadata_file, constants_file)
    dm.metadata = {}
    dm.constants = {}
    success = dm.refresh()
    return {"success": success}


def prune_image_cache(params: Dict[str, Any] = None) -> Dict[str, Any]:
    dm = DataManager()
    fs.remove_path(dm.previews_dir)
    fs.create_dirs(dm.previews_dir)
    return {"success": True}


def handle_api(action: str, params: Dict[str, Any] = None) -> Any:
    handlers = {
        "get_categories": get_categories,
        "get_mods": get_mods,
        "get_installed_mods": get_installed_mods,
        "install_mod": install_mod,
        "uninstall_mod": uninstall_mod,
        "prune_metadata_cache": prune_metadata_cache,
        "prune_image_cache": prune_image_cache,
    }
    handler = handlers.get(action)
    if handler:
        return handler(params or {})
    return {"error": f"Unknown action '{action}' in D2PFX plugin API"}
