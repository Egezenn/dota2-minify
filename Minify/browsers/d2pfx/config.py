import sys

from core import registry

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
    {
        "key": "d2pfx_auto_refresh_catalogue",
        "text": "Auto-Refresh D2PFX Catalogue",
        "default": True,
        "type": "checkbox",
    },
]

# Self-registration
registry.register_browser(sys.modules[__name__])


def on_build(mod_list):
    from browsers.d2pfx.build_hook import run

    run(mod_list)


def on_uninstall():
    from browsers.d2pfx.build_hook import restore_d2pfx_cursors

    restore_d2pfx_cursors()


def on_resize():
    pass


def on_scan_start():
    pass


def on_scan(mod_dir, browser_info):
    pass
