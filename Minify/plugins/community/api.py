import hashlib
import hmac
import json
import os
import re
import shutil
import stat
import sys
import tempfile
import time
import urllib.parse
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

import requests

from core import base, config, fs, localization, mods_shared, utils

REGISTRY_URL = "https://raw.githubusercontent.com/Dota-Modding-Community/community/main/registry.json"
STATES_KEY = "community_installs"
REGISTRY_TYPES = {"mod", "plugin", "theme"}
HEADERS = {"User-Agent": "Dota2-Minify-Community-Registry"}
MAX_ARCHIVE_SIZE = 5 * 1024 * 1024 * 1024
REGISTRY_CACHE_NAME = "registry.json"
REGISTRY_STATE_KEY = "community_registry"
REGISTRY_REFRESH_INTERVAL = 86400


def _get_registry() -> list[dict[str, Any]]:
    cache_path = os.path.join(base.cache_dir, "plugins", "community", REGISTRY_CACHE_NAME)
    last_refresh = utils.get_state(REGISTRY_STATE_KEY, "last_refresh", 0)
    cache_exists = os.path.isfile(cache_path)
    refresh_due = (
        config.get("community_auto_refresh_catalogue", True)
        and (time.time() - last_refresh) > REGISTRY_REFRESH_INTERVAL
    )

    if cache_exists and not refresh_due:
        return _read_registry_cache(cache_path)

    try:
        response = requests.get(REGISTRY_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        registry = response.json()
        if not isinstance(registry, list):
            raise ValueError("The community registry must contain a JSON array.")
        registry = [item for item in registry if isinstance(item, dict)]
        fs.create_dirs(os.path.dirname(cache_path))
        with open(cache_path, "w", encoding="utf-8") as cache_file:
            json.dump(registry, cache_file, indent=2)
        utils.set_state(REGISTRY_STATE_KEY, "last_refresh", int(time.time()))
        return registry
    except (OSError, requests.RequestException, ValueError, TypeError) as exc:
        if cache_exists:
            return _read_registry_cache(cache_path)
        raise RuntimeError(f"Failed to fetch the community registry: {exc}") from exc


def _read_registry_cache(cache_path: str) -> list[dict[str, Any]]:
    try:
        with open(cache_path, "r", encoding="utf-8") as cache_file:
            registry = json.load(cache_file)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Failed to read the cached community registry: {exc}") from exc
    if not isinstance(registry, list):
        raise ValueError("The cached community registry must contain a JSON array.")
    return [item for item in registry if isinstance(item, dict)]


def _latest_release(item: dict[str, Any]) -> dict[str, Any]:
    releases = _release_compatibility(item)
    asset_template = item.get("asset-url")
    if not isinstance(asset_template, str) or not asset_template or "{tag}" not in asset_template:
        raise ValueError("The registry entry has an invalid asset URL template.")

    if releases is None:
        tag = "latest"
    else:
        compatible_tags = [tag for tag, versions in releases.items() if base.VERSION in versions]
        tag = max(compatible_tags, key=_release_version_key, default=None)
        if tag is None:
            raise ValueError(f"No release supports Minify {base.VERSION}.")

    asset_url = asset_template.replace("{tag}", urllib.parse.quote(tag, safe=""))
    parsed_asset = urllib.parse.urlparse(asset_url)
    if parsed_asset.scheme != "https" or not parsed_asset.netloc:
        raise ValueError("The registry entry has an invalid asset URL template.")
    checksums = item.get("sha512")
    release = {"tag": tag, "asset_url": asset_url}
    if isinstance(checksums, dict):
        checksum = checksums.get(tag)
        if not isinstance(checksum, str) or not re.fullmatch(r"[0-9a-fA-F]{128}", checksum):
            raise ValueError(f"The registry entry has no valid SHA-512 checksum for release {tag}.")
        release["sha512"] = checksum.lower()
    return release


def _verify_archive_checksum(archive_path: str, expected: Any) -> None:
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-fA-F]{128}", expected):
        raise ValueError("The release has no valid SHA-512 checksum.")
    digest = hashlib.sha512()
    with open(archive_path, "rb") as archive:
        for chunk in iter(lambda: archive.read(1024 * 1024), b""):
            digest.update(chunk)
    actual = digest.hexdigest()
    if not hmac.compare_digest(actual, expected.lower()):
        raise ValueError("Downloaded package checksum does not match the registry.")


def _release_version_key(tag: str) -> tuple[int, ...]:
    numbers = re.findall(r"\d+", tag)
    return tuple(int(number) for number in numbers) if numbers else (-1,)


def _install_records() -> dict[str, dict[str, Any]]:
    states = utils.read_states()
    records = states.get(STATES_KEY, {})
    return records if isinstance(records, dict) else {}


def _remove_missing_install_records(records: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    valid_records = {}
    for key, record in records.items():
        if not isinstance(record, dict):
            continue
        item_type = record.get("type")
        if item_type in {"mod", "plugin"}:
            relative = record.get("path")
            exists = isinstance(relative, str) and os.path.isdir(os.path.join(base.base_dir, relative))
        elif item_type == "theme":
            files = record.get("files")
            exists = (
                isinstance(files, list)
                and bool(files)
                and all(isinstance(path, str) and os.path.isfile(os.path.join(base.base_dir, path)) for path in files)
            )
        else:
            exists = False
        if exists:
            valid_records[key] = record
    if valid_records != records:
        utils.write_states(STATES_KEY, valid_records)
    return valid_records


def reconcile_install_states() -> None:
    _remove_missing_install_records(_install_records())


def _item_key(item_type: str, name: str) -> str:
    return f"{item_type}:{name}"


def _release_compatibility(item: dict[str, Any]) -> dict[str, list[str]] | None:
    releases = item.get("releases")
    if not isinstance(releases, dict):
        return None
    return {tag: _version_list(versions) for tag, versions in releases.items() if isinstance(tag, str) and tag}


def _version_list(versions: Any) -> list[str]:
    if isinstance(versions, str):
        return [version.strip() for version in versions.split(",") if version.strip()]
    if isinstance(versions, list):
        return [str(version).strip() for version in versions if str(version).strip()]
    return []


def _compatible_versions(item: dict[str, Any]) -> list[str]:
    releases = _release_compatibility(item)
    if releases is not None:
        return list(dict.fromkeys(version for versions in releases.values() for version in versions))
    versions = item.get("versions")
    return _version_list(versions)


def _tag_is_compatible(item: dict[str, Any], tag: Any) -> bool:
    releases = _release_compatibility(item)
    if releases is not None:
        return isinstance(tag, str) and base.VERSION in releases.get(tag, [])
    return base.VERSION in _compatible_versions(item)


def _enrich_entry(item: dict[str, Any], records: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    item_type = str(item.get("type", "")).lower()
    name = item.get("name")
    if item_type not in REGISTRY_TYPES or not isinstance(name, str) or not name.strip():
        return None

    key = _item_key(item_type, name)
    record = records.get(key, {})
    installed = isinstance(record, dict) and bool(record)
    compatible = base.VERSION in _compatible_versions(item)
    if not compatible and not installed:
        return None
    result = {
        "id": key,
        "name": name,
        "type": item_type,
        "repo": item.get("repo", ""),
        "preview": item.get("preview", ""),
        "notes_url": item.get("notes", ""),
        "manifest_url": item.get("manifest", ""),
        "compatible_versions": _compatible_versions(item),
        "installed": installed,
        "installed_tag": record.get("tag") if isinstance(record, dict) else None,
        "installed_compatible": installed and _tag_is_compatible(item, record.get("tag")),
        "current_version": base.VERSION,
        "latest_tag": None,
        "update_available": False,
        "available": False,
        "error": None,
    }
    if compatible:
        try:
            latest = _latest_release(item)
            result.update(latest_tag=latest["tag"], available=True)
            result["update_available"] = installed and result["installed_tag"] != latest["tag"]
        except (requests.RequestException, ValueError, KeyError) as exc:
            result["error"] = str(exc)
    return result


def get_catalogue(params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    records = _install_records()
    entries = [_enrich_entry(item, records) for item in _get_registry()]
    return [entry for entry in entries if entry is not None]


def get_item_details(params: dict[str, Any] | None = None) -> dict[str, Any]:
    item_id = (params or {}).get("id")
    for item in _get_registry():
        item_type = item.get("type")
        name = item.get("name")
        if item_type in REGISTRY_TYPES and isinstance(name, str) and _item_key(item_type, name) == item_id:
            notes_url = item.get("notes")
            notes = ""
            if notes_url:
                response = requests.get(notes_url, headers=HEADERS, timeout=15)
                response.raise_for_status()
                lang = config.get("locale") or "en"
                notes = localization.parse_notes_for_locale(response.text[:100_000], lang)
            return {"notes": notes, "manifest_url": item.get("manifest", "")}
    raise ValueError("The registry item no longer exists.")


def _safe_package_name(name: str) -> str:
    windows_device_names = {"CON", "PRN", "AUX", "NUL"}
    windows_device_names.update(f"COM{index}" for index in range(1, 10))
    windows_device_names.update(f"LPT{index}" for index in range(1, 10))
    if (
        not name
        or name in {".", ".."}
        or name != name.strip()
        or name.endswith(".")
        or any(char in name for char in '<>:"/\\|?*')
        or any(ord(char) < 32 for char in name)
        or name.split(".", maxsplit=1)[0].upper() in windows_device_names
    ):
        raise ValueError(f"Registry name cannot be used as a folder name: {name!r}")
    return name


def _unpack_zip(archive_path: str, destination: str) -> None:
    declared_total = 0
    extracted_total = 0
    root = Path(destination).resolve()
    with zipfile.ZipFile(archive_path) as archive:
        for info in archive.infolist():
            member_name = info.filename.replace("\\", "/")
            member = PurePosixPath(member_name)
            if (
                member.is_absolute()
                or not member.parts
                or ":" in member_name
                or any(part in {"", ".", ".."} for part in member.parts)
            ):
                raise ValueError(f"Unsafe path in archive: {info.filename}")
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise ValueError(f"Symbolic links are not allowed in archives: {info.filename}")
            declared_total += info.file_size
            if declared_total > MAX_ARCHIVE_SIZE:
                raise ValueError("Archive contents exceed the 5 GiB extraction limit.")
            target = (root / Path(*member.parts)).resolve()
            if not target.is_relative_to(root):
                raise ValueError(f"Archive path escapes its destination: {info.filename}")
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source, target.open("wb") as output:
                    while chunk := source.read(64 * 1024):
                        extracted_total += len(chunk)
                        if extracted_total > MAX_ARCHIVE_SIZE:
                            raise ValueError("Archive contents exceed the 5 GiB extraction limit.")
                        output.write(chunk)


def _package_root(directory: str) -> str:
    root = Path(directory)
    entries = list(root.iterdir())
    if len(entries) == 1 and entries[0].is_dir():
        return str(entries[0])
    return directory


def _relative_to_base(path: str) -> str:
    return os.path.relpath(path, base.base_dir).replace("\\", "/")


def _record_owned_files(record: dict[str, Any]) -> list[str]:
    files = record.get("files", [])
    if not isinstance(files, list) or not all(isinstance(path, str) for path in files):
        raise ValueError("Saved theme installation record is invalid.")
    root = Path(base.themes_dir).resolve()
    result = []
    for relative in files:
        target = (Path(base.base_dir) / relative).resolve()
        if not target.is_relative_to(root) or target == root:
            raise ValueError(f"Saved theme path is outside the themes directory: {relative}")
        result.append(str(target))
    return result


def _remove_empty_parents(path: str, root: str) -> None:
    parent = os.path.dirname(path)
    root = os.path.abspath(root)
    while os.path.abspath(parent).startswith(root + os.sep):
        try:
            os.rmdir(parent)
        except OSError:
            break
        parent = os.path.dirname(parent)


def _delete_record_files(record: dict[str, Any], item_type: str) -> None:
    root_dir = {"mod": base.mods_dir, "plugin": base.plugins_dir, "theme": base.themes_dir}[item_type]
    root = Path(root_dir).resolve()
    if item_type == "theme":
        for target in _record_owned_files(record):
            if os.path.isfile(target):
                os.remove(target)
                _remove_empty_parents(target, str(root))
        return

    relative = record.get("path")
    if not isinstance(relative, str):
        raise ValueError("Saved package installation record is invalid.")
    target = (Path(base.base_dir) / relative).resolve()
    if not target.is_relative_to(root) or target == root:
        raise ValueError(f"Saved package path is outside its install directory: {relative}")
    if os.path.exists(str(target)):
        shutil.rmtree(target)


def _theme_files(source_root: str, name: str) -> list[tuple[str, str]]:
    files = []
    for root, _, filenames in os.walk(source_root):
        for filename in filenames:
            source = os.path.join(root, filename)
            relative = os.path.relpath(source, source_root)
            files.append((source, relative.replace("\\", "/")))
    stylesheets = sorted(
        (entry for entry in files if entry[1].lower().endswith(".css")),
        key=lambda entry: entry[1].lower(),
    )
    if not stylesheets:
        raise ValueError("Theme archive does not contain a CSS stylesheet.")

    primary_path = stylesheets[0][1]
    if "/" in primary_path:
        raise ValueError("Theme archive must place its main stylesheet at the package root.")
    canonical_css = f"{_safe_package_name(name)}.css"
    result = [(source, canonical_css if relative == primary_path else relative) for source, relative in files]
    destinations = [relative.casefold() for _, relative in result]
    if len(destinations) != len(set(destinations)):
        raise ValueError("Theme archive contains file paths that collide after installation.")
    return result


def _refresh_plugin_runtime(plugin_id: str) -> None:
    package_name = f"plugins.{plugin_id}"
    for module_name in list(sys.modules):
        if module_name == package_name or module_name.startswith(package_name + "."):
            sys.modules.pop(module_name, None)
    import plugins

    plugins.initialize()


def _plugin_id_from_record(record: dict[str, Any]) -> str:
    plugin_id = record.get("plugin_id")
    if isinstance(plugin_id, str) and plugin_id:
        return plugin_id
    folder = record.get("path")
    if isinstance(folder, str):
        manifest_path = Path(base.base_dir) / folder / "manifest.json"
        if manifest_path.is_file():
            with manifest_path.open(encoding="utf-8") as manifest_file:
                manifest = json.load(manifest_file)
            plugin_id = manifest.get("id") if isinstance(manifest, dict) else None
            if isinstance(plugin_id, str) and plugin_id:
                return plugin_id
    raise ValueError("Cannot determine the plugin id for the installed package.")


def _install_package(item: dict[str, Any], release: dict[str, Any], record: dict[str, Any] | None) -> dict[str, Any]:
    item_type = str(item.get("type", "")).lower()
    name = _safe_package_name(str(item.get("name", "")))
    root_dir = {"mod": base.mods_dir, "plugin": base.plugins_dir, "theme": base.themes_dir}[item_type]
    fs.create_dirs(root_dir)
    fs.create_dirs(base.cache_dir)
    key = _item_key(item_type, name)
    records = _install_records()
    old_record = record or records.get(key)
    target = os.path.join(root_dir, name)

    with tempfile.TemporaryDirectory(prefix="community-", dir=base.cache_dir) as work_dir:
        archive_path = os.path.join(work_dir, "package.zip")
        if not fs.download_file(
            release["asset_url"],
            archive_path,
            name=f"{name} ({release['tag']})",
            task_id=f"community:{key}",
        ):
            raise RuntimeError(f"Failed to download {name} ({release['tag']}).")
        if "sha512" in release:
            _verify_archive_checksum(archive_path, release["sha512"])
        extracted_root = os.path.join(work_dir, "extracted")
        os.makedirs(extracted_root)
        _unpack_zip(archive_path, extracted_root)
        package_root = _package_root(extracted_root)

        if item_type in {"mod", "plugin"}:
            manifest_path = os.path.join(package_root, "manifest.json")
            if not os.path.isfile(manifest_path):
                raise ValueError(f"{item_type.title()} archive is missing its root manifest.json.")
            with open(manifest_path, encoding="utf-8") as manifest_file:
                manifest = json.load(manifest_file)
            if not isinstance(manifest, dict):
                raise ValueError(f"{item_type.title()} manifest must contain a JSON object.")
            plugin_id = None
            if item_type == "plugin":
                plugin_id = manifest.get("id")
                if not isinstance(plugin_id, str) or not plugin_id.strip():
                    raise ValueError("Plugin manifest must declare a non-empty id.")
                if not os.path.isfile(os.path.join(package_root, "ui", "index.html")):
                    raise ValueError("Plugin archive is missing ui/index.html.")
                for folder in os.listdir(base.plugins_dir):
                    other_path = os.path.join(base.plugins_dir, folder)
                    other_manifest = os.path.join(other_path, "manifest.json")
                    if os.path.isdir(other_path) and folder != name and os.path.isfile(other_manifest):
                        try:
                            with open(other_manifest, encoding="utf-8") as manifest_file:
                                if json.load(manifest_file).get("id") == plugin_id:
                                    raise ValueError(f"Another plugin already uses the id {plugin_id!r}.")
                        except (json.JSONDecodeError, AttributeError):
                            continue

            if os.path.exists(target) and not old_record:
                raise FileExistsError(f"Install folder already exists and is not managed by the registry: {target}")

            backup = os.path.join(work_dir, "previous")
            if old_record and os.path.exists(target):
                expected_path = (Path(base.base_dir) / str(old_record.get("path", ""))).resolve()
                if expected_path != Path(target).resolve():
                    raise ValueError("Saved package path does not match its registry-name folder.")
                os.replace(target, backup)
            try:
                os.replace(package_root, target)
                if item_type == "mod":
                    mods_shared.set_state(name, True)
                    mods_shared.scan_mods()
            except Exception:
                if os.path.exists(target):
                    shutil.rmtree(target)
                if os.path.exists(backup):
                    os.replace(backup, target)
                raise

            records[key] = {
                "type": item_type,
                "name": name,
                "repo": item.get("repo", ""),
                "tag": release["tag"],
                "path": _relative_to_base(target),
            }
            if plugin_id:
                records[key]["plugin_id"] = plugin_id
        else:
            install_files = _theme_files(package_root, name)
            old_files = _record_owned_files(old_record) if old_record else []
            old_set = {os.path.normcase(path) for path in old_files}
            planned = []
            for source, relative in install_files:
                destination = os.path.abspath(os.path.join(base.themes_dir, *PurePosixPath(relative).parts))
                if not Path(destination).resolve().is_relative_to(Path(base.themes_dir).resolve()):
                    raise ValueError(f"Theme archive path escapes the themes directory: {relative}")
                if os.path.exists(destination) and os.path.normcase(destination) not in old_set:
                    raise FileExistsError(f"Theme file already exists; refusing to overwrite it: {destination}")
                planned.append((source, destination))

            backup_dir = os.path.join(work_dir, "previous-theme-files")
            os.makedirs(backup_dir)
            backed_up = {}
            for index, old_file in enumerate(old_files):
                if os.path.isfile(old_file):
                    backup_file = os.path.join(backup_dir, str(index))
                    shutil.copy2(old_file, backup_file)
                    backed_up[old_file] = backup_file
            removed = []
            created = []
            try:
                for old_file in old_files:
                    if os.path.isfile(old_file):
                        os.remove(old_file)
                        removed.append(old_file)
                for source, destination in planned:
                    os.makedirs(os.path.dirname(destination), exist_ok=True)
                    shutil.copy2(source, destination)
                    created.append(destination)
            except Exception:
                for destination in created:
                    if os.path.isfile(destination):
                        os.remove(destination)
                for old_file in removed:
                    os.makedirs(os.path.dirname(old_file), exist_ok=True)
                    shutil.copy2(backed_up[old_file], old_file)
                raise
            for old_file in old_files:
                _remove_empty_parents(old_file, base.themes_dir)
            records[key] = {
                "type": item_type,
                "name": name,
                "repo": item.get("repo", ""),
                "tag": release["tag"],
                "files": [_relative_to_base(destination) for _, destination in planned],
            }

    utils.write_states(STATES_KEY, records)
    if item_type == "plugin":
        _refresh_plugin_runtime(records[key]["plugin_id"])
    return records[key]


def install_item(params: dict[str, Any] | None = None) -> dict[str, Any]:
    item_id = (params or {}).get("id")
    records = _install_records()
    existing = records.get(item_id)
    if existing:
        raise ValueError("This item is already installed. Use Update or Uninstall.")
    item = _find_compatible_item(item_id)
    release = _latest_release(item)
    record = _install_package(item, release, None)
    return {"success": True, "installed": record}


def update_item(params: dict[str, Any] | None = None) -> dict[str, Any]:
    item_id = (params or {}).get("id")
    records = _install_records()
    existing = records.get(item_id)
    if not isinstance(existing, dict):
        raise ValueError("This item is not installed.")
    item = _find_compatible_item(item_id)
    release = _latest_release(item)
    if release["tag"] == existing.get("tag"):
        raise ValueError("This item is already up to date.")
    record = _install_package(item, release, existing)
    return {"success": True, "installed": record}


def uninstall_item(params: dict[str, Any] | None = None) -> dict[str, Any]:
    item_id = (params or {}).get("id")
    records = _install_records()
    record = records.get(item_id)
    if not isinstance(record, dict) or record.get("type") not in REGISTRY_TYPES:
        raise ValueError("This item is not installed by the community registry.")
    plugin_id = _plugin_id_from_record(record) if record["type"] == "plugin" else None
    _delete_record_files(record, record["type"])
    records.pop(item_id)
    utils.write_states(STATES_KEY, records)
    if record["type"] == "mod":
        mods_shared.set_state(record["name"], False)
        mods_shared.scan_mods()
    elif record["type"] == "theme" and config.get("theme") == f"{_safe_package_name(record['name'])}":
        config.set("theme", "light")
    elif record["type"] == "plugin" and plugin_id:
        _refresh_plugin_runtime(plugin_id)
    return {"success": True}


def _find_compatible_item(item_id: str) -> dict[str, Any]:
    for item in _get_registry():
        if item.get("type") not in REGISTRY_TYPES or not isinstance(item.get("name"), str):
            continue
        if _item_key(item["type"], item["name"]) != item_id:
            continue
        if base.VERSION not in _compatible_versions(item):
            raise ValueError(f"This item does not support Minify {base.VERSION}.")
        return item
    raise ValueError("The registry item no longer exists.")


def handle_api(action: str, params: dict[str, Any] | None = None) -> Any:
    routes = {
        "get_catalogue": get_catalogue,
        "get_item_details": get_item_details,
        "install_item": install_item,
        "update_item": update_item,
        "uninstall_item": uninstall_item,
    }
    if action not in routes:
        raise ValueError(f"Unknown community registry action: {action}")
    return routes[action](params)
