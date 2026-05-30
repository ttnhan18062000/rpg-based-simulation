"""
src/domains/world_emergence/aggregators.py
───────────────────────────────────────────────────────────────────────────────
Phase 8 — World Event Aggregation.
"""

from __future__ import annotations
from typing import Sequence, Tuple
from collections import defaultdict
from src.domains.world_emergence.schema import WorldEvent, WorldEventAggregate, WorldEventCategory

class WorldEventAggregator:
    """
    Summarizes individual fine-grained world events into region, category, and subject aggregates.
    Avoids O(N) historical scans by processing within a strict window and capping size.
    """

    @staticmethod
    def aggregate(
        events: Sequence[WorldEvent],
        min_tick: int,
        max_tick: int,
    ) -> Tuple[WorldEventAggregate, ...]:
        # Group events by (region_id, category, subject)
        groups = defaultdict(list)
        for ev in events:
            if not (min_tick <= ev.tick <= max_tick):
                continue
            # Cap/ignore ultra-low salience events if necessary
            if ev.severity <= 0.05:
                continue
            key = (ev.region_id, ev.category, ev.subject)
            groups[key].append(ev)

        aggregates = []
        # Sort keys to ensure deterministic ordering of outcomes
        for key in sorted(groups.keys(), key=lambda k: (k[0] or "", k[1].value, k[2] or "")):
            evs = groups[key]
            first_t = min(e.tick for e in evs)
            last_t = max(e.tick for e in evs)
            count = len(evs)
            sev_sum = sum(e.severity for e in evs)
            aggregates.append(WorldEventAggregate(
                region_id=key[0],
                category=key[1],
                subject=key[2],
                count=count,
                severity_sum=sev_sum,
                first_tick=first_t,
                last_tick=last_t
            ))

        return tuple(aggregates)
