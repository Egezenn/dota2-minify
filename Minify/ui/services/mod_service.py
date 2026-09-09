import base64
import os
from typing import Any, Dict, List

from core import base, config, mods_shared, output, utils


class ModService:
    @staticmethod
    def get_mod_preview(mod_path: str) -> str | None:
        if not os.path.isdir(mod_path):
            return None
        for filename in os.listdir(mod_path):
            if filename.lower() in (
                "preview.jpg",
                "preview.jpeg",
                "preview.png",
                "preview.webp",
                "preview.gif",
            ):
                p_path = os.path.join(mod_path, filename)
                try:
                    ext = filename.lower().rsplit(".", 1)[-1]
                    mime_type = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
                    with open(p_path, "rb") as img_file:
                        encoded = base64.b64encode(img_file.read()).decode("utf-8")
                        return f"data:{mime_type};base64,{encoded}"
                except Exception as e:
                    output.add_text(
                        f"Error loading preview image for {os.path.basename(mod_path)}: {e}", msg_type="warning"
                    )
        return None

    def get_mods(self) -> List[Dict[str, Any]]:
        try:
            mods_shared.scan_mods()
            from patch import manifest_utils

            mod_list = mods_shared.visually_available_mods
            mods_data = []
            for mod in mod_list:
                mod_path = os.path.join(base.mods_dir, mod)
                always = False
                if os.path.isdir(mod_path):
                    cfg = manifest_utils.get_mod(mod_path)
                    always = bool(cfg.get("always", False))
                preview = self.get_mod_preview(mod_path)
                mods_data.append(
                    {
                        "name": mod,
                        "enabled": always or mods_shared.get_state(mod),
                        "always": always,
                        "preview": preview,
                    }
                )
            return mods_data
        except Exception as e:
            output.add_text(f"get_mods error: {e}", msg_type="error")
            return []

    @staticmethod
    def _build_directory_tree(dir_path: str) -> Dict[str, Any]:
        dir_name = os.path.basename(dir_path)

        def _scan(current_path: str, rel_path: str) -> Dict[str, Any]:
            children = []
            try:
                entries = sorted(
                    os.listdir(current_path),
                    key=lambda x: (not os.path.isdir(os.path.join(current_path, x)), x.lower()),
                )
                for entry in entries:
                    if entry.startswith((".", "_")) or entry == "__pycache__":
                        continue
                    full_entry_path = os.path.join(current_path, entry)
                    entry_rel = os.path.join(rel_path, entry).replace("\\", "/") if rel_path else entry
                    if os.path.isdir(full_entry_path):
                        children.append(_scan(full_entry_path, entry_rel))
                    else:
                        size = 0
                        try:
                            size = os.path.getsize(full_entry_path)
                        except OSError:
                            pass
                        children.append(
                            {
                                "name": entry,
                                "type": "file",
                                "path": entry_rel,
                                "size": size,
                            }
                        )
            except Exception as e:
                output.add_text(f"Error scanning directory {current_path}: {e}", msg_type="warning")
            return {
                "name": os.path.basename(current_path) if rel_path else dir_name,
                "type": "directory",
                "path": rel_path,
                "children": children,
            }

        return _scan(dir_path, "")

    @staticmethod
    def _count_tree_files(node: Dict[str, Any]) -> int:
        if node.get("type") == "file":
            return 1
        return sum(ModService._count_tree_files(child) for child in node.get("children", []))

    @staticmethod
    def _build_vpk_tree(mod_name: str, vpk_path: str) -> Dict[str, Any]:
        import vpk

        root: Dict[str, Any] = {
            "name": mod_name,
            "type": "directory",
            "path": "",
            "children": [],
        }
        try:
            pak = vpk.open(vpk_path)
            for path_str in sorted(pak):
                parts = path_str.replace("\\", "/").strip("/").split("/")
                curr = root
                curr_path = ""
                for i, part in enumerate(parts):
                    curr_path = f"{curr_path}/{part}" if curr_path else part
                    is_file = i == len(parts) - 1
                    found = None
                    for child in curr["children"]:
                        if child["name"] == part and child["type"] == ("file" if is_file else "directory"):
                            found = child
                            break
                    if not found:
                        found = {
                            "name": part,
                            "type": "file" if is_file else "directory",
                            "path": curr_path,
                        }
                        if not is_file:
                            found["children"] = []
                        curr["children"].append(found)
                    curr = found
        except Exception as e:
            output.add_text(f"Error reading VPK {mod_name}: {e}", msg_type="warning")

        def _sort(node: Dict[str, Any]) -> None:
            if "children" in node:
                node["children"].sort(key=lambda x: (0 if x["type"] == "directory" else 1, x["name"].lower()))
                for c in node["children"]:
                    _sort(c)

        _sort(root)
        return root

    @staticmethod
    def _format_json(raw_text: str) -> str:
        trimmed = raw_text.strip()
        if "\n" in trimmed:
            return trimmed
        try:
            import json

            return json.dumps(json.loads(trimmed), indent=2)
        except Exception:
            return trimmed

    def get_mod_methods(self, mod_name: str, mod_path: str) -> List[Dict[str, Any]]:
        methods: List[Dict[str, Any]] = []

        if mod_name.endswith(".vpk") and os.path.isfile(mod_path):
            vpk_tree = self._build_vpk_tree(mod_name, mod_path)
            count = self._count_tree_files(vpk_tree)
            methods.append(
                {
                    "name": mod_name,
                    "type": "tree",
                    "tree": vpk_tree,
                    "badge": f"{count} file" if count == 1 else f"{count} files",
                }
            )
            return methods

        if not os.path.isdir(mod_path):
            return methods

        # 1. files directory
        files_dir = os.path.join(mod_path, "files")
        if os.path.isdir(files_dir):
            tree = self._build_directory_tree(files_dir)
            count = self._count_tree_files(tree)
            methods.append(
                {
                    "name": "files",
                    "type": "tree",
                    "tree": tree,
                    "badge": f"{count} file" if count == 1 else f"{count} files",
                }
            )

        # 2. files_uncompiled directory
        files_uncompiled_dir = os.path.join(mod_path, "files_uncompiled")
        if os.path.isdir(files_uncompiled_dir):
            tree = self._build_directory_tree(files_uncompiled_dir)
            count = self._count_tree_files(tree)
            methods.append(
                {
                    "name": "files_uncompiled",
                    "type": "tree",
                    "tree": tree,
                    "badge": f"{count} file" if count == 1 else f"{count} files",
                }
            )

        # 3. blacklist.txt
        blacklist_path = os.path.join(mod_path, "blacklist.txt")
        if os.path.isfile(blacklist_path):
            try:
                with utils.open_utf8(blacklist_path) as f:
                    bl_content = f.read()
                lines = bl_content.splitlines()
                methods.append(
                    {
                        "name": "blacklist.txt",
                        "type": "blacklist",
                        "content": bl_content,
                        "badge": f"{len(lines)} line" if len(lines) == 1 else f"{len(lines)} lines",
                    }
                )
            except Exception as e:
                output.add_text(f"Error reading blacklist.txt for {mod_name}: {e}", msg_type="warning")

        # 4. xml.json
        xml_path = os.path.join(mod_path, "xml.json")
        if os.path.isfile(xml_path):
            try:
                with utils.open_utf8(xml_path) as f:
                    raw_xml = f.read()
                fmt_xml = self._format_json(raw_xml)
                lines = fmt_xml.splitlines()
                methods.append(
                    {
                        "name": "xml.json",
                        "type": "json",
                        "content": fmt_xml,
                        "badge": f"{len(lines)} line" if len(lines) == 1 else f"{len(lines)} lines",
                    }
                )
            except Exception as e:
                output.add_text(f"Error reading xml.json for {mod_name}: {e}", msg_type="warning")

        # 5. replacer.json
        replacer_path = os.path.join(mod_path, "replacer.json")
        if os.path.isfile(replacer_path):
            try:
                with utils.open_utf8(replacer_path) as f:
                    raw_replacer = f.read()
                fmt_replacer = self._format_json(raw_replacer)
                lines = fmt_replacer.splitlines()
                methods.append(
                    {
                        "name": "replacer.json",
                        "type": "json",
                        "content": fmt_replacer,
                        "badge": f"{len(lines)} line" if len(lines) == 1 else f"{len(lines)} lines",
                    }
                )
            except Exception as e:
                output.add_text(f"Error reading replacer.json for {mod_name}: {e}", msg_type="warning")

        # 6. styling.css
        styling_path = os.path.join(mod_path, "styling.css")
        if os.path.isfile(styling_path):
            try:
                with utils.open_utf8(styling_path) as f:
                    css_content = f.read()
                lines = css_content.splitlines()
                methods.append(
                    {
                        "name": "styling.css",
                        "type": "css",
                        "content": css_content,
                        "badge": f"{len(lines)} line" if len(lines) == 1 else f"{len(lines)} lines",
                    }
                )
            except Exception as e:
                output.add_text(f"Error reading styling.css for {mod_name}: {e}", msg_type="warning")

        # 7. Python scripts
        script_priority = [
            "script_initial.py",
            "script.py",
            "script_after_decompile.py",
            "script_after_recompile.py",
            "script_after_patch.py",
            "script_prelaunch.py",
            "script_uninstall.py",
            "script_utility.py",
        ]
        script_files = [
            f
            for f in os.listdir(mod_path)
            if f.startswith("script") and f.endswith(".py") and os.path.isfile(os.path.join(mod_path, f))
        ]
        script_files.sort(key=lambda x: (script_priority.index(x) if x in script_priority else 999, x.lower()))
        for s_file in script_files:
            s_path = os.path.join(mod_path, s_file)
            try:
                with utils.open_utf8(s_path) as f:
                    py_content = f.read()
                lines = py_content.splitlines()
                methods.append(
                    {
                        "name": s_file,
                        "type": "python",
                        "content": py_content,
                        "badge": f"{len(lines)} line" if len(lines) == 1 else f"{len(lines)} lines",
                    }
                )
            except Exception as e:
                output.add_text(f"Error reading {s_file} for {mod_name}: {e}", msg_type="warning")

        # 8. manifest.json
        manifest_path = os.path.join(mod_path, "manifest.json")
        if os.path.isfile(manifest_path):
            try:
                with utils.open_utf8(manifest_path) as f:
                    raw_manifest = f.read()
                fmt_manifest = self._format_json(raw_manifest)
                lines = fmt_manifest.splitlines()
                methods.append(
                    {
                        "name": "manifest.json",
                        "type": "json",
                        "content": fmt_manifest,
                        "badge": f"{len(lines)} line" if len(lines) == 1 else f"{len(lines)} lines",
                    }
                )
            except Exception as e:
                output.add_text(f"Error reading manifest.json for {mod_name}: {e}", msg_type="warning")

        # 9. Other custom files
        known_files = {
            "notes.md",
            "preview.jpg",
            "preview.jpeg",
            "preview.png",
            "preview.webp",
            "preview.gif",
            "blacklist.txt",
            "xml.json",
            "replacer.json",
            "styling.css",
            "manifest.json",
            "files",
            "files_uncompiled",
            "__pycache__",
        }
        for item in sorted(os.listdir(mod_path), key=str.lower):
            if item.lower() in known_files or item.startswith(("script", ".", "_")):
                continue
            item_path = os.path.join(mod_path, item)
            if os.path.isfile(item_path):
                ext = item.lower().rsplit(".", 1)[-1] if "." in item else ""
                type_str = "text"
                if ext == "json":
                    type_str = "json"
                elif ext in ("xml", "vxml"):
                    type_str = "xml"
                elif ext == "css":
                    type_str = "css"
                elif ext == "py":
                    type_str = "python"
                try:
                    with utils.open_utf8(item_path) as f:
                        other_content = f.read()
                    lines = other_content.splitlines()
                    methods.append(
                        {
                            "name": item,
                            "type": type_str,
                            "content": other_content,
                            "badge": f"{len(lines)} line" if len(lines) == 1 else f"{len(lines)} lines",
                        }
                    )
                except Exception:
                    pass

        return methods

    def get_mod_details(self, mod_name: str, lang: str | None = None) -> Dict[str, Any]:
        try:
            if not lang:
                lang = config.get("locale") or "EN"
            mod_path = os.path.join(base.mods_dir, mod_name)
            methods = self.get_mod_methods(mod_name, mod_path)

            if not os.path.isdir(mod_path):
                return {
                    "name": mod_name,
                    "notes": None,
                    "preview": None,
                    "has_notes": False,
                    "has_preview": False,
                    "methods": methods,
                }

            notes_path = os.path.join(mod_path, "notes.md")
            notes_content = None
            if os.path.exists(notes_path):
                try:
                    with utils.open_utf8(notes_path) as f:
                        raw_notes = f.read()
                    notes_content = self.parse_notes_for_locale(raw_notes, lang)
                except Exception as e:
                    output.add_text(f"Error reading notes for {mod_name}: {e}", msg_type="warning")

            preview_data_url = self.get_mod_preview(mod_path)

            return {
                "name": mod_name,
                "notes": notes_content,
                "preview": preview_data_url,
                "has_notes": bool(notes_content),
                "has_preview": bool(preview_data_url),
                "methods": methods,
            }
        except Exception as e:
            output.add_text(f"get_mod_details error: {e}", msg_type="error")
            return {
                "name": mod_name,
                "notes": None,
                "preview": None,
                "has_notes": False,
                "has_preview": False,
                "methods": [],
            }

    @staticmethod
    def parse_notes_for_locale(notes_text: str, lang: str) -> str:
        if not notes_text or "<!-- LANG:" not in notes_text:
            return notes_text.strip()

        sections: Dict[str, str] = {}
        current_lang: str | None = None
        lines: List[str] = []

        for line in notes_text.splitlines():
            trimmed = line.strip()
            if trimmed.startswith("<!-- LANG:") and trimmed.endswith("-->"):
                if current_lang:
                    sections[current_lang] = "\n".join(lines).strip()
                current_lang = trimmed[10:-3].strip().upper()
                lines = []
            else:
                lines.append(line)
        if current_lang:
            sections[current_lang] = "\n".join(lines).strip()

        target_lang = (lang or "EN").upper()
        if target_lang in sections:
            return sections[target_lang]
        elif "EN" in sections:
            return sections["EN"]
        elif sections:
            return next(iter(sections.values()))

        return notes_text.strip()

    def set_mods(self, data: Dict[str, bool]) -> bool:
        try:
            from patch import manifest_utils

            for mod_name, enabled in data.items():
                mod_path = os.path.join(base.mods_dir, mod_name)
                if os.path.isdir(mod_path):
                    cfg = manifest_utils.get_mod(mod_path)
                    if cfg.get("always", False):
                        continue
                mods_shared.set_state(mod_name, bool(enabled))
            return True
        except Exception:
            return False
