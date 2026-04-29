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
    VERIFIED v2: DeterministicRNG
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
        """DEPRECATED: Stateful, order-dependent. Use get_float() for concurrent contexts."""
        return self._get_rng(domain).random()

    def next_int(self, domain: Domain, a: int, b: int) -> int:
        """DEPRECATED: Stateful, order-dependent. Use get_int() for concurrent contexts."""
        return self._get_rng(domain).randint(a, b)

    def get_state(self) -> dict[int, Any]:
        return {d.value: r.getstate() for d, r in self._rng_map.items()}

    def set_state(self, state: dict[int, Any]) -> None:
        for d_val, r_state in state.items():
            domain = Domain(d_val)
            if domain not in self._rng_map:
                self._rng_map[domain] = random.Random()
            self._rng_map[domain].setstate(r_state)

    @staticmethod
    def _composite_seed(base_seed: int, domain: Domain, tick: int, entity_id: int, sub_id: int) -> int:
        """Generates a stable, order-independent composite seed."""
        # Simple fast integer hash composition
        seed = base_seed
        seed ^= (domain.value << 48)
        seed ^= (tick << 32)
        if isinstance(entity_id, str):
            # Simple hash for string IDs
            h = 0
            for char in entity_id:
                h = (h * 31 + ord(char)) & 0xFFFFFFFF
            entity_id = h
            
        seed ^= (entity_id << 16)
        seed ^= sub_id
        return seed

    def get_float(self, domain: Domain, tick: int, entity_id: int, sub_id: int = 0) -> float:
        """Stateless, order-independent random float in [0.0, 1.0)."""
        seed = self._composite_seed(self._base_seed, domain, tick, entity_id, sub_id)
        return random.Random(seed).random()

    def get_int(self, domain: Domain, tick: int, entity_id: int, a: int, b: int, sub_id: int = 0) -> int:
        """Stateless, order-independent random integer in [a, b]."""
        seed = self._composite_seed(self._base_seed, domain, tick, entity_id, sub_id)
        return random.Random(seed).randint(a, b)
        
    def choice(self, domain: Domain, tick: int, entity_id: int, seq: Any, sub_id: int = 0) -> Any:
        """Stateless, order-independent choice from a sequence."""
        seed = self._composite_seed(self._base_seed, domain, tick, entity_id, sub_id)
        return random.Random(seed).choice(seq)

    def sample(self, domain: Domain, tick: int, entity_id: int, population: Any, k: int, sub_id: int = 0) -> list:
        """Stateless, order-independent sample from a population."""
        seed = self._composite_seed(self._base_seed, domain, tick, entity_id, sub_id)
        return random.Random(seed).sample(population, k)

    @property
    def seed(self) -> int:
        return self._base_seed
