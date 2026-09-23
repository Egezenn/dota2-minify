import json
import os
import subprocess

MODS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Minify", "mods"))


def get_languages_from_weblate() -> list[str]:
    try:
        res = subprocess.run(
            ["git", "ls-tree", "--name-only", "weblate:mod"],
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
        )
        languages = []
        for line in res.stdout.splitlines():
            line = line.strip()
            if line.endswith(".json"):
                languages.append(line[:-5])
        # Always put english first, then alphabetical for the rest
        return sorted(languages, key=lambda l: (0 if l == "en" else 1, l))
    except Exception as e:
        print(f"Warning: Failed to discover languages from weblate:mod: {e}")
        return []


def get_json_from_weblate(lang: str) -> dict:
    try:
        res = subprocess.run(
            ["git", "show", f"weblate:mod/{lang}.json"],
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
        )
        return json.loads(res.stdout)
    except Exception as e:
        print(f"Warning: Failed to read weblate:mod/{lang}.json: {e}")
        return {}


def main():
    languages = get_languages_from_weblate()
    if not languages:
        print("No language files found in weblate:mod.")
        return

    all_locales = {}
    for lang in languages:
        data = get_json_from_weblate(lang)
        if data:
            all_locales[lang] = data
            print(f"Loaded {len(data)} translations for '{lang}'")

    if not all_locales:
        print("No localization data found from weblate branch.")
        return

    target_mods = [d for d in os.listdir(MODS_DIR) if os.path.isdir(os.path.join(MODS_DIR, d))]

    for mod_name in sorted(target_mods):
        mod_path = os.path.join(MODS_DIR, mod_name)
        notes_file = os.path.join(mod_path, "notes.md")

        sections = []
        for lang in languages:
            text = all_locales.get(lang, {}).get(mod_name)
            if text and text.strip():
                sections.append(f"<!-- lang:{lang} -->\n\n{text.strip()}")

        if sections:
            content = "\n\n".join(sections) + "\n"
            with open(notes_file, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
            print(f"Updated {mod_name}/notes.md with {len(sections)} language(s)")


if __name__ == "__main__":
    main()
