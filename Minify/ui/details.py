"Mod details window logic"

import os

import dearpygui.dearpygui as dpg
from core import base, utils

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
        img_val = shared.mod_details_image_cache[mod]
        if isinstance(img_val, str):
            img_path = img_val
            try:
                res = utils.load_dpg_image_resized(img_path, max_width=800, max_height=600)
                if res:
                    w, h, _, d = res
                    image_tag = f"{mod}_image_texture"
                    if not dpg.does_item_exist("mod_images_registry"):
                        dpg.add_texture_registry(tag="mod_images_registry", show=False)
                    if not dpg.does_item_exist(image_tag):
                        dpg.add_static_texture(
                            width=w, height=h, default_value=d, tag=image_tag, parent="mod_images_registry"
                        )
                    shared.mod_details_image_cache[mod] = (w, h, image_tag)
                else:
                    shared.mod_details_image_cache.pop(mod, None)
            except Exception as e:
                print(f"Failed to load image for {mod}: {e}")
                shared.mod_details_image_cache.pop(mod, None)

    if mod in shared.mod_details_image_cache and not isinstance(shared.mod_details_image_cache[mod], str):
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
