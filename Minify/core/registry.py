"""Central registry for plugins."""


class PluginRegistry:
    _plugins = []

    @classmethod
    def register(cls, plugin_obj):
        if plugin_obj not in cls._plugins:
            cls._plugins.append(plugin_obj)

    @classmethod
    def get_plugins(cls):
        return cls._plugins

    @classmethod
    def clear(cls):
        cls._plugins.clear()


def register_plugin(plugin_obj):
    PluginRegistry.register(plugin_obj)


def get_plugins():
    return PluginRegistry.get_plugins()
