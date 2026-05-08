import json
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../Minify")))

# Languages that had people review and want to show as "Source/Complete" in Weblate
# Everything else will stay in localization.json as machine-translation
# but will show as 0% in Weblate (because we won't export them).
TRUSTED_LANGUAGES = ["EN", "RU", "TR"]


def split_localization():
    """Splits the main localization.json into individual language files."""
    # Resolve absolute paths
    minify_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../Minify"))
    loc_file = os.path.join(minify_dir, "bin", "localization.json")
    locales_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "weblate"))
    os.makedirs(locales_dir, exist_ok=True)

    with open(loc_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # We ONLY split the trusted/source languages.
    # Weblate will handle propagating new keys from EN.json to other languages.
    for lang in TRUSTED_LANGUAGES:
        lang_data = {}
        for key in data:
            if lang in data[key]:
                lang_data[key] = data[key][lang]

        output_path = os.path.join(locales_dir, f"{lang}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(lang_data, f, indent=2, ensure_ascii=False)

    print(f"Successfully split source localization ({', '.join(TRUSTED_LANGUAGES)}) into {locales_dir}")

    # Handle notes.md files
    split_notes(minify_dir, locales_dir)


def split_notes(minify_dir, locales_dir):
    """Bundles notes.md files from all whitelisted mods into single JSON files per language."""
    mods_dir = os.path.join(minify_dir, "mods")

    # Read .gitignore to find whitelisted mods
    gitignore_path = os.path.abspath(os.path.join(minify_dir, "../.gitignore"))
    whitelisted_mods = []
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("!Minify/mods/"):
                    mod_name = line.replace("!Minify/mods/", "").strip()
                    if mod_name:
                        whitelisted_mods.append(mod_name)

    # Bundle data by language
    bundled_data = {lang: {} for lang in TRUSTED_LANGUAGES}

    for mod_name in os.listdir(mods_dir):
        if mod_name not in whitelisted_mods:
            continue

        mod_path = os.path.join(mods_dir, mod_name)
        if not os.path.isdir(mod_path):
            continue

        notes_path = os.path.join(mod_path, "notes.md")
        if os.path.exists(notes_path):
            with open(notes_path, "r", encoding="utf-8") as f:
                content = f.read()

            parts = re.split(r"<!-- LANG:([\w-]+) -->", content)
            if len(parts) > 1:
                for i in range(1, len(parts), 2):
                    lang = parts[i].upper()
                    if lang in TRUSTED_LANGUAGES:
                        bundled_data[lang][mod_name] = parts[i + 1].strip()
            else:
                bundled_data["EN"][mod_name] = content.strip()

    # Write bundled JSON files
    notes_dir = os.path.join(locales_dir, "mods")
    os.makedirs(notes_dir, exist_ok=True)

    for lang, data in bundled_data.items():
        if data:
            output_path = os.path.join(notes_dir, f"{lang}.json")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Bundled notes for {lang} into {output_path}")


def merge_localization():
    """Merges individual language files back into the main localization.json."""
    # Resolve absolute paths
    minify_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../Minify"))
    loc_file = os.path.join(minify_dir, "bin", "localization.json")
    locales_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "weblate"))

    if not os.path.exists(locales_dir):
        print(f"Error: {locales_dir} does not exist.")
        return

    # 1. Start with the original data (preserving machine translations)
    with open(loc_file, "r", encoding="utf-8") as f:
        final_data = json.load(f)

    # 2. Update with anything found in the weblate folder (human translations)
    for filename in os.listdir(locales_dir):
        if filename.endswith(".json"):
            lang = filename[:-5]
            with open(os.path.join(locales_dir, filename), "r", encoding="utf-8") as f:
                lang_data = json.load(f)

            for key, translation in lang_data.items():
                if key not in final_data:
                    final_data[key] = {}
                final_data[key][lang] = translation

    with open(loc_file, "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)

    print(f"Successfully merged locales back into {loc_file}")

    # Handle notes.md files
    merge_notes(minify_dir, locales_dir)


def merge_notes(minify_dir, locales_dir):
    """Merges bundled JSON files back into individual notes.md files in mods."""
    notes_dir = os.path.join(locales_dir, "mods")
    if not os.path.exists(notes_dir):
        return

    # 1. Identify all languages present in the mods folder
    langs = []
    for filename in os.listdir(notes_dir):
        if filename.endswith(".json"):
            langs.append(filename[:-5].upper())

    if not langs:
        return

    # 2. Group data by mod name
    # {ModName: {LANG: content}}
    mod_data = {}

    for lang in langs:
        file_path = os.path.join(notes_dir, f"{lang}.json")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for mod_name, content in data.items():
            if mod_name not in mod_data:
                mod_data[mod_name] = {}
            mod_data[mod_name][lang] = content

    # 3. Process each mod
    for mod_name, sections in mod_data.items():
        mod_path = os.path.join(minify_dir, "mods", mod_name)
        if not os.path.exists(mod_path):
            continue

        notes_path = os.path.join(mod_path, "notes.md")

        # Load existing sections (preserving machine translations)
        current_sections = {}
        if os.path.exists(notes_path):
            with open(notes_path, "r", encoding="utf-8") as f:
                content = f.read()
            parts = re.split(r"<!-- LANG:([\w-]+) -->", content)
            if len(parts) > 1:
                for i in range(1, len(parts), 2):
                    current_sections[parts[i].upper()] = parts[i + 1].strip()
            else:
                current_sections["EN"] = content.strip()

        # Update with new sections
        current_sections.update(sections)

        # Write back
        if current_sections:
            output = []
            available_langs = sorted(current_sections.keys())
            if "EN" in available_langs:
                available_langs.remove("EN")
                available_langs.insert(0, "EN")

            for lang in available_langs:
                if current_sections[lang]:
                    output.append(f"<!-- LANG:{lang} -->\n\n{current_sections[lang]}")

            with open(notes_path, "w", encoding="utf-8") as f:
                f.write("\n\n".join(output))
            print(f"Merged notes for mod: {mod_name}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python localization_manager.py [split|merge]")
        sys.exit(1)

    command = sys.argv[1].lower()
    if command == "split":
        split_localization()
    elif command == "merge":
        merge_localization()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
