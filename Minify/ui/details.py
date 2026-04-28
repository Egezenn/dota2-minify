"Mod details window logic"

import os

import dearpygui.dearpygui as dpg
from core import base

from ui import localization, markdown, shared


def render_details_window(mod):
    content_group = f"{mod}_details_content_group"
    if not dpg.does_item_exist(content_group):
        return

    dpg.delete_item(content_group, children_only=True)

    try:
        window_width = dpg.get_item_width("primary_window")
        window_height = dpg.get_item_height("primary_window")
    except Exception:
        window_width = base.main_window_width
        window_height = base.main_window_height

    avail_width = window_width - 40
    max_height = window_height - 50 - 20

    if mod in shared.mod_details_image_cache:
        w, h, image_tag = shared.mod_details_image_cache[mod]

        scale = min(1.0, avail_width / w, max_height / h) * 0.7
        display_w = int(w * scale)
        display_h = int(h * scale)

        dpg.add_image(image_tag, width=display_w, height=display_h, parent=content_group)
        dpg.add_separator(parent=content_group)

    mod_path = os.path.join(base.mods_dir, mod)
    text = markdown.parse_notes(mod_path, localization.locale)

    container = f"{mod}_markdown_container"
    with dpg.group(parent=content_group, tag=container):
        pass
    markdown.render(container, text, width=avail_width)
