"Central registry for browsers and plugins"


class BrowserRegistry:
    _configs = []

    @classmethod
    def register(cls, config_module):
        if config_module not in cls._configs:
            cls._configs.append(config_module)

    @classmethod
    def get_configs(cls):
        return cls._configs


def register_browser(config_module):
    BrowserRegistry.register(config_module)


def get_browser_configs():
    return BrowserRegistry.get_configs()
