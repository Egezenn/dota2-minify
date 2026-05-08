# core.registry

Central registry for browsers and plugins

## `BrowserRegistry()`

*No documentation available.*

<details open><summary>Source</summary>

```python
class BrowserRegistry:
    _configs = []

    @classmethod
    def register(cls, config_module):
        if config_module not in cls._configs:
            cls._configs.append(config_module)

    @classmethod
    def get_configs(cls):
        return cls._configs

```

</details>

## `register_browser(config_module)`

*No documentation available.*

<details open><summary>Source</summary>

```python
def register_browser(config_module):
    BrowserRegistry.register(config_module)

```

</details>

## `get_browser_configs()`

*No documentation available.*

<details open><summary>Source</summary>

```python
def get_browser_configs():
    return BrowserRegistry.get_configs()

```

</details>
