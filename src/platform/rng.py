"""Domain-separated deterministic RNG using xxhash.

The Golden Rule: The outcome of Tick T depends ONLY on
WorldSeed + State at T-1. Thread scheduling order must not matter.

Formula: RNG_Value = Hash(WorldSeed, Domain, EntityID, Tick)
"""

from __future__ import annotations
import struct
import xxhash
from src.core.models.enums import Domain

class DeterministicRNG:
    """Stateless domain-separated pseudo-random number generator.
    Each call is a pure function of (seed, domain, entity_id, tick).
    """

    __slots__ = ("_seed",)
    _MAX_UINT64 = (1 << 64) - 1

    def __init__(self, seed: int) -> None:
        self._seed = seed

    def _hash(self, domain: Domain, entity_id: int, tick: int, sub_id: int = 0) -> int:
        payload = struct.pack("<qiqii", self._seed, domain.value, entity_id, tick, sub_id)
        return xxhash.xxh64(payload).intdigest()

    def next_float(self, domain: Domain, entity_id: int, tick: int, sub_id: int = 0) -> float:
        """Return a deterministic float in [0.0, 1.0)."""
        return self._hash(domain, entity_id, tick, sub_id) / (self._MAX_UINT64 + 1)

    def next_int(self, domain: Domain, entity_id: int, tick: int, low: int, high: int, sub_id: int = 0) -> int:
        """Return a deterministic integer in [low, high] inclusive."""
        f = self.next_float(domain, entity_id, tick, sub_id)
        return low + int(f * (high - low + 1))

    def next_bool(self, domain: Domain, entity_id: int, tick: int, probability: float = 0.5, sub_id: int = 0) -> bool:
        """Return True with the given probability."""
        return self.next_float(domain, entity_id, tick, sub_id) < probability

    def next_hex(self, domain: Domain, entity_id: int, tick: int, length: int = 8, sub_id: int = 0) -> str:
        """Return a deterministic hex string."""
        h = self._hash(domain, entity_id, tick, sub_id)
        return hex(h)[2:2+length]

    def weighted_choice(self, domain: Domain, entity_id: int, tick: int, items: list, weights: list[float]):
        """Deterministic weighted choice."""
        total = sum(weights)
        if total <= 0: return items[0]
        roll = self.next_float(domain, entity_id, tick) * total
        accum = 0.0
        for i, weight in enumerate(weights):
            accum += weight
            if roll <= accum:
                return items[i]
        return items[-1]
