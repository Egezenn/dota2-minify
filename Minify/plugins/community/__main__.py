import sys

from core import registry

registry.register_plugin(sys.modules[__name__])


def on_initialize():
    from plugins.community.api import reconcile_install_states

    reconcile_install_states()
