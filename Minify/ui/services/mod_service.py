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

    def get_mod_details(self, mod_name: str, lang: str | None = None) -> Dict[str, Any]:
        try:
            if not lang:
                lang = config.get("locale") or "EN"
            mod_path = os.path.join(base.mods_dir, mod_name)
            if not os.path.isdir(mod_path):
                return {
                    "name": mod_name,
                    "notes": None,
                    "preview": None,
                    "has_notes": False,
                    "has_preview": False,
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
            }
        except Exception as e:
            output.add_text(f"get_mod_details error: {e}", msg_type="error")
            return {
                "name": mod_name,
                "notes": None,
                "preview": None,
                "has_notes": False,
                "has_preview": False,
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
