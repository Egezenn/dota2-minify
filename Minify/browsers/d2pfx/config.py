import sys
from core.registry import register_browser

VERSION = "0.3"
RESIZE_TAGS = ["d2pfx_browser_window", "d2pfx_details_modal"]
RENAME_CATEGORIES = ["trees", "river", "shaders", "herofx", "ranged-attack", "hero-items", "optimization"]

# Self-registration
register_browser(sys.modules[__name__])


def on_build(mod_list, current_mod=None):
    from .build_hook import run

    run(mod_list, current_mod)


def on_resize():
    from .ui import BrowserUI

    BrowserUI.get_instance().update_layout()


def on_scan_start():
    from .ui import BrowserUI

    BrowserUI.get_instance().clear_installed_mods()


def on_scan(mod_dir, browser_info):
    is_d2pfx = browser_info.get("browser") == "d2pfx" or str(browser_info.get("name", "")).startswith("d2pfx")
    if is_d2pfx:
        from .ui import BrowserUI

        BrowserUI.get_instance().register_installed_mod(mod_dir, browser_info)
