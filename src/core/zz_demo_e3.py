"""Demo only, never merged: one silent `except` whose body is only `pass`."""


def demo(path: str) -> None:
    """Read a path and ignore any error."""
    try:
        open(path).close()
    except OSError:
        pass
