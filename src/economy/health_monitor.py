from __future__ import annotations
from typing import Optional
from pydantic import BaseModel
from src.core.state import AuthoritativeState


class EconomyHealthSnapshot(BaseModel):
    """Transient read-only economy health sample for one window boundary."""
    tick: int
    gini_coefficient: float
    transaction_velocity: float   # TODO E33A: count trades in window
    avg_price_index: dict         # TODO E33A: per-commodity prices


class EconomyHealthMonitor:
    WINDOW_SIZE: int = 100        # ticks per sampling window

    @staticmethod
    def sample(state: AuthoritativeState, tick: int) -> Optional[EconomyHealthSnapshot]:
        """Sample economy health at window boundaries. Returns None otherwise."""
        if tick % EconomyHealthMonitor.WINDOW_SIZE != 0:
            return None
        entity_gold: list[float] = [
            float(e.inventory.gold)
            for e in state.entities.values()
            if e.combat.alive
        ]
        return EconomyHealthSnapshot(
            tick=tick,
            gini_coefficient=EconomyHealthMonitor._gini(entity_gold),
            transaction_velocity=0.0,   # TODO E33A: count trades in window
            avg_price_index={},         # TODO E33A: per-commodity prices
        )

    @staticmethod
    def _gini(values: list[float]) -> float:
        """Standard discrete Gini coefficient (sorted 1-indexed formula).

        G = (2 * sum(i * x_i) / (n * sum(x_i))) - (n+1)/n
        where x is sorted ascending and i is 1-indexed.
        Returns 0.0 for empty list or all-zero wealth.
        """
        if not values or sum(values) == 0:
            return 0.0
        n = len(values)
        s = sorted(values)
        cum = sum((i + 1) * v for i, v in enumerate(s))
        return (2 * cum) / (n * sum(s)) - (n + 1) / n
