import contextlib


@contextlib.contextmanager
def try_pass():
    try:
        yield
    except Exception:
        pass
