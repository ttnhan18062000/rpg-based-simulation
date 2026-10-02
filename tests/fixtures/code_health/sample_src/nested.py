"""Fixture: three different things named step."""


class Worker:
    """A class."""

    def step(self):
        """A method."""
        return 1


def step():
    """A function."""

    def step():
        return 2

    return step
