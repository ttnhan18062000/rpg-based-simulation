from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel
from src.core.state import AuthoritativeState
from src.observability.events import (
    SimulationEvent,
    InflationSpiralEvent,
    GoldHoardingEvent,
)


class EconomyHealthSnapshot(BaseModel):
    """Transient read-only economy health sample for one window boundary."""
    tick: int
    gini_coefficient: float
    transaction_velocity: float   # TODO E33A: count trades in window
    avg_price_index: dict         # TODO E33A: per-commodity prices


class EconomyHealthMonitor:
    WINDOW_SIZE: int = 100        # ticks per sampling window
    INFLATION_SPIRAL_GINI_THRESHOLD: float = 0.7
    GOLD_HOARDING_GINI_THRESHOLD: float = 0.8

    @staticmethod
    def check_alerts(
        snapshot: EconomyHealthSnapshot,
        tick: int,
        region_id: Optional[str] = None,
    ) -> List[SimulationEvent]:
        """Evaluate alert conditions on a snapshot.

        Returns a (possibly empty) list of SimulationEvent alert instances.
        ECONOMIC_COLLAPSE and DEFLATION_RISK are deferred to E33C (transaction_velocity
        is stub=0.0 in E33B and cannot reliably distinguish collapse from stub).
        """
        alerts: List[SimulationEvent] = []
        gini = snapshot.gini_coefficient
        if gini > EconomyHealthMonitor.GOLD_HOARDING_GINI_THRESHOLD:
            alerts.append(GoldHoardingEvent(
                tick=tick,
                gini_coefficient=gini,
                region_id=region_id,
            ))
        elif gini > EconomyHealthMonitor.INFLATION_SPIRAL_GINI_THRESHOLD:
            alerts.append(InflationSpiralEvent(
                tick=tick,
                gini_coefficient=gini,
                region_id=region_id,
            ))
        return alerts

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
