from __future__ import annotations

import random
from typing import Any


class DeterministicRNG:
    """
    Wrapper for Python's random.Random to ensure simulation isolation.
    Authoritative logic must never use the global 'random' module.
    """
    __slots__ = ("_rng", "_seed")

    def __init__(self, seed: int) -> None:
        self._seed = seed
        self._rng = random.Random(seed)

    def next_float(self) -> float:
        """Return a random float in range [0.0, 1.0)."""
        return self._rng.random()

    def next_int(self, a: int, b: int) -> int:
        """Return a random integer N such that a <= N <= b."""
        return self._rng.randint(a, b)

    def get_state(self) -> Any:
        """Capture the internal state for checkpoints."""
        return self._rng.getstate()

    def set_state(self, state: Any) -> None:
        """Restore internal state from a checkpoint."""
        self._rng.setstate(state)

    @property
    def seed(self) -> int:
        return self._seed
