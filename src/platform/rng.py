# src/platform/rng.py
from __future__ import annotations
import random
from typing import Any, Optional
from src.core.enums import Domain # Assuming Domain enum exists in src/core/enums.py

class DeterministicRNG:
    """
    Enhanced Deterministic RNG with Domain Separation for V2.
    Ensures that different gameplay domains (e.g., SPAWN vs COMBAT) 
    do not share the same random stream even with the same seed.
    """
    __slots__ = ("_base_seed", "_rng_map")

    def __init__(self, base_seed: int) -> None:
        self._base_seed = base_seed
        self._rng_map: dict[Domain, random.Random] = {}

    def _get_rng(self, domain: Domain) -> random.Random:
        if domain not in self._rng_map:
            # Seed each domain uniquely based on the base seed
            domain_seed = self._base_seed ^ (domain.value << 16)
            self._rng_map[domain] = random.Random(domain_seed)
        return self._rng_map[domain]

    def next_float(self, domain: Domain) -> float:
        return self._get_rng(domain).random()

    def next_int(self, domain: Domain, a: int, b: int) -> int:
        return self._get_rng(domain).randint(a, b)

    def get_state(self) -> dict[int, Any]:
        return {d.value: r.getstate() for d, r in self._rng_map.items()}

    def set_state(self, state: dict[int, Any]) -> None:
        for d_val, r_state in state.items():
            domain = Domain(d_val)
            if domain not in self._rng_map:
                self._rng_map[domain] = random.Random()
            self._rng_map[domain].setstate(r_state)

    @property
    def seed(self) -> int:
        return self._base_seed
