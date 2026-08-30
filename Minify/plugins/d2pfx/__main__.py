import sys

from core import registry

VERSION = "0.4"
RENAME_CATEGORIES = ["trees", "river", "shaders", "herofx", "ranged-attack", "hero-items", "optimization"]


# Self-registration
registry.register_plugin(sys.modules[__name__])


def on_build(mod_list):
    from plugins.d2pfx.build_hook import run

    run(mod_list)


def on_uninstall():
    from plugins.d2pfx.build_hook import restore_d2pfx_cursors

    restore_d2pfx_cursors()
