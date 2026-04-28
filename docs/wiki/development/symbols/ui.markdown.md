# ui.markdown

Custom markdown parsing & rendering for details pages

## `parse_notes(mod_path, locale)`

*No documentation available.*

<details open><summary>Source</summary>

```python
def parse_notes(mod_path, locale):
    try:
        notes_md_path = os.path.join(mod_path, "notes.md")
        if os.path.exists(notes_md_path):
            with utils.open_utf8(notes_md_path) as file:
                raw_notes = file.read()

            user_locale = locale.upper()
            sections = {}

            parts = re.split(r"<!-- LANG:([\w-]+) -->", raw_notes)

            if len(parts) > 1:
                for i in range(1, len(parts), 2):
                    lang = parts[i].upper()
                    content = parts[i + 1].strip()
                    sections[lang] = content
            else:
                sections["EN"] = raw_notes.strip()

            return sections.get(user_locale, sections.get("EN", ""))
    except Exception as e:
        print(f"Error parsing notes for {mod_path}: {e}")
    return ""

```

</details>

## `is_cjk(char)`

Checks if a character is a CJK character (Chinese, Japanese, Korean)
or full-width punctuation.

<details open><summary>Source</summary>

```python
def is_cjk(char):
    """
    Checks if a character is a CJK character (Chinese, Japanese, Korean)
    or full-width punctuation.
    """
    cp = ord(char)
    return (
        0x4E00 <= cp <= 0x9FFF  # CJK Unified Ideographs
        or 0x3040 <= cp <= 0x309F  # Hiragana
        or 0x30A0 <= cp <= 0x30FF  # Katakana
        or 0xAC00 <= cp <= 0xD7AF  # Hangul
        or 0xFF00 <= cp <= 0xFFEF  # Full-width punctuation
    )

```

</details>

## `render_rich_text(parent, text, font, base_color, bullet, width)`

Renders text with inline code blocks (wrapped in backticks) in pink.
Manually handles text wrapping.
Supports urls (orange), custom font, base color, and bullets.

<details open><summary>Source</summary>

```python
def render_rich_text(parent, text, font="main_font", base_color=(0, 230, 230), bullet=False, width=None):
    """
    Renders text with inline code blocks (wrapped in backticks) in pink.
    Manually handles text wrapping.
    Supports urls (orange), custom font, base color, and bullets.
    """
    if not text:
        return

    if width is None:
        try:
            # Try to get width from parent, fallback to primary window
            width = dpg.get_item_width(parent)
            if width <= 0:
                width = shared.window_width or dpg.get_item_width("primary_window")
        except Exception:
            width = shared.window_width or 640

    avail_width = max(100, width - 40)

    # Tokenize: Split by backticks
    parts = text.split("`")
    tokens = []

    for i, part in enumerate(parts):
        is_code = i % 2 == 1
        if not part:
            continue

        if is_code:
            tokens.append({"text": part, "type": "code"})
        else:
            words = part.split(" ")
            for j, word in enumerate(words):
                if word:
                    if word.startswith("http://") or word.startswith("https://"):
                        tokens.append({"text": word, "type": "link"})
                    else:
                        # CJK-aware tokenization for normal text
                        current_token = ""
                        for char in word:
                            if is_cjk(char):
                                if current_token:
                                    tokens.append({"text": current_token, "type": "normal"})
                                    current_token = ""
                                tokens.append({"text": char, "type": "normal"})
                            else:
                                current_token += char
                        if current_token:
                            tokens.append({"text": current_token, "type": "normal"})

                if j < len(words) - 1:
                    tokens.append({"text": " ", "type": "normal"})
            if i < len(parts) - 1:
                tokens.append({"text": " ", "type": "normal"})

    # Layout tokens
    lines = []
    current_line = []
    current_line_width = 0

    for token in tokens:
        token_text = token["text"]
        token_width = dpg.get_text_size(token_text)[0]

        if font == "large_font":
            token_width *= 1.25

        if token_text == " " and current_line_width == 0:
            continue

        if current_line_width + token_width > avail_width and current_line_width > 0:
            lines.append(current_line)
            current_line = []
            current_line_width = 0

            if token_text == " ":
                continue

        current_line.append(token)
        current_line_width += token_width

    if current_line:
        lines.append(current_line)

    # Render lines
    first_token_rendered = False
    for line_tokens in lines:
        with dpg.group(horizontal=True, parent=parent, horizontal_spacing=0):
            for token in line_tokens:
                if token["type"] == "code":
                    color = (255, 105, 180)
                elif token["type"] == "link":
                    color = (255, 165, 0)
                else:
                    color = base_color

                show_bullet = bullet and not first_token_rendered

                text_item = dpg.add_text(token["text"], color=color, bullet=show_bullet)
                if font:
                    dpg.bind_item_font(text_item, font)

                first_token_rendered = True

```

</details>

## `render(parent, text, width)`

*No documentation available.*

<details open><summary>Source</summary>

```python
def render(parent, text, width=None):
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            dpg.add_spacer(parent=parent, height=5)
            continue

        if line.startswith("!!:"):
            content = line[3:].strip()
            render_rich_text(parent, content, font="large_font", base_color=(255, 0, 0), width=width)
        elif line.startswith("-"):
            content = line[1:].strip()
            render_rich_text(parent, content, bullet=True, width=width)
        else:
            render_rich_text(parent, line, width=width)

```

</details>
