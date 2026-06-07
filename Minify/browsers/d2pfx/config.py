import sys

from core import registry, utils

VERSION = "0.4"
RESIZE_TAGS = ["d2pfx_browser_window", "d2pfx_details_modal"]
RENAME_CATEGORIES = ["trees", "river", "shaders", "herofx", "ranged-attack", "hero-items", "optimization"]

SETTINGS = [
    {
        "key": "d2pfx_filter_nsfw",
        "text": "Filter 18+ Mods (D2PFX)",
        "default": True,
        "type": "checkbox",
    },
    {
        "key": "d2pfx_filter_anime",
        "text": "Filter Anime Mods (D2PFX)",
        "default": False,
        "type": "checkbox",
    },
]

# Self-registration
registry.register_browser(sys.modules[__name__])


def on_build(mod_list, current_mod=None):
    from browsers.d2pfx.build_hook import run

    run(mod_list, current_mod)


@utils.ignore_if_headless
def on_resize():
    from browsers.d2pfx.ui import BrowserUI

    BrowserUI.get_instance().update_layout()


@utils.ignore_if_headless
def on_scan_start():
    from browsers.d2pfx.ui import BrowserUI

    BrowserUI.get_instance().clear_installed_mods()


@utils.ignore_if_headless
def on_scan(mod_dir, browser_info):
    is_d2pfx = browser_info.get("browser") == "d2pfx" or str(browser_info.get("name", "")).startswith("d2pfx")
    if is_d2pfx:
        from browsers.d2pfx.ui import BrowserUI

        BrowserUI.get_instance().register_installed_mod(mod_dir, browser_info)
