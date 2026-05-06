def initialize():
    """Import known browsers to trigger self-registration."""
    try:
        import browsers.d2pfx.config
    except ImportError:
        pass
