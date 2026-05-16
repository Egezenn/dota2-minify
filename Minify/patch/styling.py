import os
import re

from core import base, fs, utils


def apply_styles_to_file(item):
    file_path, styles_to_apply = item

    def remove_braced_block(text, start_pattern):
        while True:
            match = re.search(start_pattern, text)
            if not match:
                break

            start_index = match.start()

            open_brace_index = text.find("{", match.end())
            if open_brace_index == -1:
                break

            brace_count = 1
            current_index = open_brace_index + 1
            while brace_count > 0 and current_index < len(text):
                next_open = text.find("{", current_index)
                next_close = text.find("}", current_index)

                if next_close == -1:
                    break

                if next_open != -1 and next_open < next_close:
                    brace_count += 1
                    current_index = next_open + 1
                else:
                    brace_count -= 1
                    current_index = next_close + 1

            if brace_count == 0:
                text = text[:start_index] + text[current_index:]
            else:
                break
        return text

    with utils.open_utf8(file_path) as file:
        content = file.read()

    new_defines = set()
    new_keyframes = set()

    define_pattern = re.compile(r"@define\s+([\w-]+)\s*:")
    keyframe_pattern = re.compile(r"@keyframes\s+(?:'|\")?([\w\s-]+)(?:'|\")?")

    for style in styles_to_apply:
        defines = define_pattern.findall(style)
        new_defines.update(defines)

        keyframes = keyframe_pattern.findall(style)
        new_keyframes.update(keyframes)

    for define_name in new_defines:
        pattern = rf"@define\s+{re.escape(define_name)}\s*:\s*.*?(?:;|$)"
        content = re.sub(pattern, "", content, flags=re.DOTALL)

    for keyframe_name in new_keyframes:
        start_pattern = rf"@keyframes\s+(?:'|\")?{re.escape(keyframe_name)}(?:'|\")?"
        content = remove_braced_block(content, start_pattern)

    unique_styles_to_add = []
    for style in styles_to_apply:
        if style not in content and style not in unique_styles_to_add:
            unique_styles_to_add.append(style)

    with utils.open_utf8(file_path, "w") as file:
        file.write(content)
        if unique_styles_to_add:
            file.write("\n" + "\n".join(unique_styles_to_add))


def parse_styling_file(styling_css, mod_cfg, folder, mod_settings, styling_dictionary, core_extracts, dota_extracts):
    with utils.open_utf8(styling_css) as file:
        content = file.read()

    # Fallback to manifest defaults
    defaults = {
        s["key"]: s["default"]
        for s in mod_cfg.get("settings", [])
        if isinstance(s, dict) and "key" in s and "default" in s
    }

    content = re.sub(
        r"<&(.*?)>",
        lambda m: str(mod_settings.get(m.group(1), defaults.get(m.group(1), m.group(0)))),
        content,
    )

    matches = list(re.finditer(r"/\*\s*([cg]):(.*?)\s*\*/", content))
    for i, match in enumerate(matches):
        indicator = match.group(1)
        path = match.group(2).strip()

        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        style = content[start:end].strip()

        if style:
            path = f"!{path}" if indicator == "c" else path
            styling_dictionary[f"styling-css-{folder}-{i}"] = (path, style)

    # Note: Only process the NEW entries for this mod
    for key, path_style in styling_dictionary.items():
        if not key.startswith(f"styling-css-{folder}-"):
            continue

        path_indicator, _ = path_style
        sanitized_path = path_indicator[1:] if path_indicator.startswith("!") else path_indicator
        fs.create_dirs(os.path.join(base.build_dir, os.path.dirname(sanitized_path)))

        if path_indicator.startswith("!"):
            core_extracts.append(f"{sanitized_path}.vcss_c")
        else:
            dota_extracts.append(f"{sanitized_path}.vcss_c")
