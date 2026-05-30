"""
src/domains/time/service.py
───────────────────────────────────────────────────────────────────────────────
Phase 13 — TemporalPressureService

Converts deadlines, cooldowns, and staleness ratings into a dynamic urgency utility.
"""

from __future__ import annotations
from typing import Dict, Mapping
from src.core.state import EntityState
from src.core.cognition import DeadlineEntry, CooldownEntry, StalenessEntry

class TemporalPressureService:
    """Calculates active urgency ratings based on temporal limits."""

    @staticmethod
    def calculate_urgencies(entity: EntityState, current_tick: int) -> Mapping[str, float]:
        urgency_map: Dict[str, float] = {}

        # 1. Evaluate Deadlines (higher urgency as tick approaches expiry)
        for key, dl in entity.cognition.subjective.time.deadlines.items():
            ticks_left = dl.expiry_tick - current_tick
            if ticks_left <= 0:
                urgency_map[key] = 1.0  # Expired
            elif ticks_left < 100:
                # Scaled pressure: 0.1 to 0.95
                urgency_map[key] = 1.0 - (ticks_left / 100.0) * 0.9
            else:
                urgency_map[key] = 0.1

        # 2. Evaluate Cooldowns
        for key, cd in entity.cognition.subjective.time.cooldowns.items():
            if current_tick < cd.ready_tick:
                # Active cooldown: urgency of retrying is 0.0 (blocked)
                urgency_map[key] = 0.0
            else:
                urgency_map[key] = 0.5

        # 3. Evaluate Staleness
        for key, stale in entity.cognition.subjective.time.stale_facts.items():
            age = current_tick - stale.last_verified_tick
            # Older information has higher staleness pressure (forcing re-verification)
            urgency_map[key] = min(1.0, age * 0.002)

        return urgency_map
