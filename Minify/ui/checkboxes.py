"AKA mod menu stuff"

import concurrent.futures
import os

import conditions
import dearpygui.dearpygui as dpg
import jsonc
from core import base, constants, mods_shared, output, registry, utils
from patch import manifest_utils

from ui import details, localization, settings, shared, theme

checkboxes = []
checkboxes_state = {}
mod_filter_query = ""
mod_filter_metadata = {}
mod_filter_item_tags = {}


def _stringify_filter_values(value):
    if isinstance(value, dict):
        for nested_key, nested_value in value.items():
            yield str(nested_key)
            yield from _stringify_filter_values(nested_value)
    elif isinstance(value, (list, tuple, set)):
        for nested_value in value:
            yield from _stringify_filter_values(nested_value)
    elif value is None:
        yield "null"
    elif isinstance(value, bool):
        yield str(value).lower()
    else:
        yield str(value)


def _iter_manifest_path_values(value, path):
    if not path:
        yield value
        return

    if isinstance(value, dict):
        target_key = path[0]
        for current_key, current_value in value.items():
            if str(current_key).casefold() == target_key:
                yield from _iter_manifest_path_values(current_value, path[1:])
    elif isinstance(value, (list, tuple, set)):
        for nested_value in value:
            yield from _iter_manifest_path_values(nested_value, path)


def _iter_manifest_values_for_key(value, key):
    if "." in key:
        path = [part.casefold() for part in key.split(".")]
        if any(not part for part in path):
            return
        for matched_value in _iter_manifest_path_values(value, path):
            yield from _stringify_filter_values(matched_value)
        return

    target_key = key.casefold()
    if isinstance(value, dict):
        direct_values = [
            current_value for current_key, current_value in value.items() if str(current_key).casefold() == target_key
        ]
        if direct_values:
            for direct_value in direct_values:
                yield from _stringify_filter_values(direct_value)
            return

        for current_value in value.values():
            yield from _iter_manifest_values_for_key(current_value, key)
    elif isinstance(value, (list, tuple, set)):
        for nested_value in value:
            yield from _iter_manifest_values_for_key(nested_value, key)


def _tokenize_mod_filter(query):
    tokens = []
    current = []
    quote = None
    had_quote = False
    index = 0

    while index < len(query):
        char = query[index]
        if quote:
            if char == "\\" and index + 1 < len(query) and query[index + 1] == quote:
                current.append(quote)
                index += 1
            elif char == quote:
                quote = None
                had_quote = True
            else:
                current.append(char)
        elif char in ('"', "'") and (not current or current[-1] == ":"):
            quote = char
            had_quote = True
        elif char.isspace():
            if current or had_quote:
                tokens.append(("".join(current), had_quote))
                current = []
                had_quote = False
        else:
            current.append(char)
        index += 1

    if current or had_quote:
        tokens.append(("".join(current), had_quote))

    return tokens


def _is_filter_start(token, has_open_filter):
    key, separator, value = token.partition(":")
    key_parts = key.strip().split(".")
    valid_key = separator and all(
        part and all(char.isalnum() or char in ("_", "-") for char in part) for part in key_parts
    )
    if not valid_key:
        return False

    if has_open_filter and (value.startswith("//") or (len(key) == 1 and value.startswith(("\\", "/")))):
        return False

    return True


def parse_mod_filter(query):
    query = str(query or "").strip()
    if not query:
        return []

    parsed_tokens = []
    open_filter_index = None

    for token, had_quote in _tokenize_mod_filter(query):
        if not token:
            continue

        if _is_filter_start(token, open_filter_index is not None):
            parsed_tokens.append(token)
            open_filter_index = None if had_quote else len(parsed_tokens) - 1
        elif open_filter_index is not None:
            parsed_tokens[open_filter_index] += f" {token}"
        else:
            parsed_tokens.append(token)

    return parsed_tokens


def mod_matches_filter(mod_name, manifest, query):
    mod_name = str(mod_name).casefold()
    manifest = manifest if isinstance(manifest, dict) else {}

    for token in parse_mod_filter(query):
        key, separator, expected = token.partition(":")
        if separator:
            key = key.strip().casefold()
            expected = expected.strip().casefold()
            if not key or not expected:
                return False

            if key == "mod":
                values = (mod_name,)
            else:
                values = _iter_manifest_values_for_key(manifest, key)

            if not any(expected in value.casefold() for value in values):
                return False
        elif token.casefold() not in mod_name:
            return False

    return True


def filter_mods(sender=None, app_data=None, user_data=None):
    global mod_filter_query
    if app_data is not None:
        mod_filter_query = str(app_data)

    for mod, manifest in mod_filter_metadata.items():
        group_tag = mod_filter_item_tags.get(mod)
        if group_tag and dpg.does_item_exist(group_tag):
            dpg.configure_item(group_tag, show=mod_matches_filter(mod, manifest, mod_filter_query))


def load():
    global checkboxes_state
    try:
        with utils.open_utf8(base.mods_config_dir) as file:
            checkboxes_state = jsonc.load(file)
    except FileNotFoundError:
        with utils.open_utf8(base.mods_config_dir, "w") as file:
            pass

    for mod in constants.visually_unavailable_mods:
        checkboxes_state.setdefault(mod, False)


def save():
    for box in checkboxes:
        checkboxes_state[box] = dpg.get_value(box)
    with utils.open_utf8(base.mods_config_dir, "w") as file:
        jsonc.dump(dict(sorted(checkboxes_state.items())), file, indent=2)


def setup_state():
    save()
    settings.refresh()


def show_details(sender, app_data, user_data):
    mod = user_data.replace("_details_window_tag", "")
    details.render_details_window(mod)
    dpg.configure_item(user_data, show=True)
    dpg.focus_item(user_data)


def refresh(sender=None, app_data=None, user_data=None):
    mods_shared.scan_mods()
    create()
    settings.refresh()
    output.add_text("&refreshed_mod_list")


def create():
    # Cleanup for reinitialization
    if dpg.does_item_exist("mod_menu"):
        dpg.delete_item("mod_menu", children_only=True)

    for window_tag in shared.tag_data_for_details_windows:
        if dpg.does_item_exist(window_tag):
            dpg.delete_item(window_tag)
    shared.tag_data_for_details_windows.clear()

    for browser_config in registry.get_browser_configs():
        if hasattr(browser_config, "on_scan_start"):
            browser_config.on_scan_start()

    if dpg.does_item_exist("mod_images_registry"):
        dpg.delete_item("mod_images_registry", children_only=True)
    shared.mod_details_image_cache.clear()

    checkboxes.clear()
    mod_filter_metadata.clear()
    mod_filter_item_tags.clear()

    dpg.add_input_text(
        parent="mod_menu",
        tag="mod_search_input",
        hint="Search by mod name or manifest key:value...",
        default_value=mod_filter_query,
        width=-1,
        callback=filter_mods,
    )
    dpg.add_separator(parent="mod_menu")

    mod_details_cache = {}

    def scan_mod_details(mod_name):
        mod_p = os.path.join(base.mods_dir, mod_name)
        img_p = os.path.join(mod_p, "preview.jpg")
        if not os.path.exists(img_p):
            img_p = os.path.join(mod_p, "preview.png")
        notes_p = os.path.join(mod_p, "notes.md")

        image_data = None
        has_notes = False

        if os.path.exists(img_p):
            try:
                image_data = dpg.load_image(img_p)
            except Exception as err:
                print(f"Failed to load image for {mod_name}: {err}")

        if os.path.exists(notes_p) and os.path.getsize(notes_p) > 0:
            has_notes = True

        return mod_name, image_data, has_notes

    mods_to_scan = [m for m in constants.visually_available_mods if not m.endswith(".vpk")]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(scan_mod_details, mods_to_scan)
        for m_name, img_data, notes_exist in results:
            mod_details_cache[m_name] = (img_data, notes_exist)

    for mod in constants.visually_available_mods:
        mod_path = os.path.join(base.mods_dir, mod)
        unsupported_version = False
        if is_vpk := mod.endswith(".vpk"):
            always_val = False
            cfg = {}
        else:
            cfg = manifest_utils.get_mod(mod_path)
            always_val = cfg.get("always", False)

            if browser_info := cfg.get("browser"):
                for browser_config in registry.get_browser_configs():
                    if hasattr(browser_config, "on_scan"):
                        browser_config.on_scan(mod, browser_info)
            if version_req := cfg.get("version"):
                if not manifest_utils.is_version_at_least(base.VERSION, version_req):
                    unsupported_version = True

        if unsupported_version:
            enable_ticking = False
            value = False
            if checkboxes_state.get(mod, False):
                checkboxes_state[mod] = False
                save()
            output.add_text(f"Disabled {mod} (Requires version {version_req})", msg_type="warning")
        elif always_val:
            enable_ticking = False
            value = True
        else:
            enable_ticking = True
            value = checkboxes_state.get(mod, False)

        group_tag = f"{mod}_group_tag"
        mod_filter_metadata[mod] = cfg
        mod_filter_item_tags[mod] = group_tag
        dpg.add_group(parent="mod_menu", tag=group_tag, horizontal=True, width=base.main_window_width)
        dpg.add_checkbox(
            parent=group_tag,
            label=mod[:-4] if is_vpk else mod,
            tag=mod,
            callback=setup_state,
            default_value=value,
            enabled=enable_ticking,
        )

        if not is_vpk:
            img_data, has_notes = mod_details_cache.get(mod, (None, False))

            if img_data or has_notes:
                tag_data = f"{mod}_details_window_tag"
                dpg.add_button(
                    parent=f"{mod}_group_tag",
                    small=True,
                    indent=base.main_window_width - 150,
                    tag=f"{mod}_button_show_details_tag",
                    label=f"{localization.details_label}",
                    callback=show_details,
                    user_data=tag_data,
                )
                shared.tag_data_for_details_windows.append(tag_data)
                dpg.add_window(
                    tag=tag_data,
                    modal=True,
                    pos=(0, 0),
                    show=False,
                    label=mod,
                    no_resize=True,
                    no_move=True,
                    no_close=False,
                    no_collapse=True,
                    width=base.main_window_width,
                    height=base.main_window_height,
                )
                dpg.bind_item_theme(tag_data, theme.settings_theme)

                content_group = f"{mod}_details_content_group"
                with dpg.group(parent=tag_data, tag=content_group):
                    pass

                if img_data:
                    try:
                        w, h, _, d = img_data
                        image_tag = f"{mod}_image_texture"
                        dpg.add_static_texture(
                            width=w, height=h, default_value=d, tag=image_tag, parent="mod_images_registry"
                        )
                        shared.mod_details_image_cache[mod] = (w, h, image_tag)
                    except Exception as e:
                        print(f"Failed to display image for {mod}: {e}")

                details.render_details_window(mod)

        checkboxes.append(mod)

    conditions.disable_workshop_mods()
    filter_mods(app_data=mod_filter_query)


def get_value(mod):
    return dpg.get_value(mod)


def set_value(mod, value):
    if dpg.does_item_exist(mod):
        dpg.set_value(mod, value)


mods_shared.register_state_callbacks(get_value, set_value)
