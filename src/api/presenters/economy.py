"""Economy API presenter — shapes AuthoritativeState into REST read models.

Architecture rule: MUST NOT mutate authoritative state. Returns plain dicts only.
Ticket: TCK-20260619-E33B-ALERTS-REST
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from src.core.state import AuthoritativeState
from src.economy.health_monitor import EconomyHealthMonitor, EconomyHealthSnapshot


class EconomyPresenter:
    """Shape economy health data from AuthoritativeState into API-safe dicts."""

    @staticmethod
    def present_health(state: AuthoritativeState) -> Dict[str, Any]:
        """Return per-region economy health derived from the current state.

        Groups alive entities by region_id (None → "global"), computes per-region
        Gini coefficient, and evaluates alert conditions using EconomyHealthMonitor.
        Returns a shaped read model — no raw domain objects exposed.
        """
        # Group alive-entity gold values by region
        region_gold: Dict[str, list[float]] = {}
        for entity in state.entities.values():
            if not entity.combat.alive:
                continue
            nav_region = getattr(entity.navigation, "region_id", None)
            region_key: str = nav_region if nav_region is not None else "global"
            region_gold.setdefault(region_key, []).append(float(entity.inventory.gold))

        regions: Dict[str, Any] = {}
        for region_id, gold_values in region_gold.items():
            gini = EconomyHealthMonitor._gini(gold_values)
            # Build a transient snapshot to reuse check_alerts logic
            snapshot = EconomyHealthSnapshot(
                tick=state.tick,
                gini_coefficient=gini,
                transaction_velocity=0.0,
                avg_price_index={},
            )
            alerts = EconomyHealthMonitor.check_alerts(
                snapshot, tick=state.tick, region_id=region_id
            )
            alert_type: Optional[str] = alerts[0].event_type if alerts else None
            regions[region_id] = {
                "gini": gini,
                "transaction_velocity": 0.0,
                "alert": alert_type,
            }

        return {
            "tick": state.tick,
            "regions": regions,
        }
