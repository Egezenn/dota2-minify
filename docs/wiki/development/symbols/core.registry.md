# core.registry

Central registry for plugins.

## `PluginRegistry()`

*No documentation available.*

<details open><summary>Source</summary>

```python
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
```

</details>

## `register_plugin(plugin_obj)`

*No documentation available.*

<details open><summary>Source</summary>

```python
def register_plugin(plugin_obj):
    PluginRegistry.register(plugin_obj)
```

</details>

## `get_plugins()`

*No documentation available.*

<details open><summary>Source</summary>

```python
def get_plugins():
    return PluginRegistry.get_plugins()
```

</details>
