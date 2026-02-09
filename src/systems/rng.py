"""Domain-separated deterministic RNG using xxhash.

The Golden Rule: The outcome of Tick T depends ONLY on
WorldSeed + State at T-1. Thread scheduling order must not matter.

Formula: RNG_Value = Hash(WorldSeed, Domain, EntityID, Tick)
"""

from __future__ import annotations

import struct

import xxhash

from src.core.enums import Domain


class DeterministicRNG:
    """Stateless domain-separated pseudo-random number generator.

    Each call is a pure function of (seed, domain, entity_id, tick) —
    no internal mutable state, therefore fully thread-safe.
    """

    __slots__ = ("_seed",)

    _MAX_UINT64 = (1 << 64) - 1

    def __init__(self, seed: int) -> None:
        self._seed = seed

    def _hash(self, domain: Domain, entity_id: int, tick: int) -> int:
        payload = struct.pack("<qiqi", self._seed, domain.value, entity_id, tick)
        return xxhash.xxh64(payload).intdigest()

    def next_float(self, domain: Domain, entity_id: int, tick: int) -> float:
        """Return a deterministic float in [0.0, 1.0)."""
        return self._hash(domain, entity_id, tick) / (self._MAX_UINT64 + 1)

    def next_int(self, domain: Domain, entity_id: int, tick: int, low: int, high: int) -> int:
        """Return a deterministic integer in [low, high] inclusive."""
        f = self.next_float(domain, entity_id, tick)
        return low + int(f * (high - low + 1))

    def next_bool(self, domain: Domain, entity_id: int, tick: int, probability: float = 0.5) -> bool:
        """Return True with the given probability."""
        return self.next_float(domain, entity_id, tick) < probability
