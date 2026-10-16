"""Grief triggers, read from typed authoritative state (decision 80, grief as state).

A body that died on tick T carries `lifecycle.death_record` with `tick == T` and `lifecycle.active == False`. On tick T+1 every still-active
entity whose trust toward the dead body meets `ALLY_TRUST_THRESHOLD` grieves: a trigger `(griever_id, dead_id, urgency)`. The trigger is a pure
function of the state, so it does not depend on the observability mode. `AuthoritativeState.grief_drained_tick` is the newest death tick whose
triggers have been applied, written through `StateUpdate.grief_drained_tick_set`; it makes the one-shot teardown flush idempotent.
The urgency formula is the one `CampaignOrchestrator._advance_grief_urgencies()` uses, `min(1.0, trust * 0.8)`.
"""
from __future__ import annotations

from typing import List, Tuple

from src.core.social_constants import ALLY_TRUST_THRESHOLD

GriefTrigger = Tuple[int, int, float]


def pending_grief_triggers(state) -> List[GriefTrigger]:
    """The `(griever_id, dead_id, urgency)` triples owed for the bodies that died on the previous tick and are not yet drained."""
    death_tick = state.tick - 1
    if death_tick <= state.grief_drained_tick:
        return []
    triggers: List[GriefTrigger] = []
    for eid, entity in state.entities.items():
        record = entity.lifecycle.death_record
        if entity.lifecycle.active or record is None or record.tick != death_tick:
            continue
        for other_id, other in state.entities.items():
            if other_id == eid or not other.lifecycle.active:
                continue
            trust = getattr(other.social, "trust_history", {}).get(eid, 0.0)
            if trust >= ALLY_TRUST_THRESHOLD:
                triggers.append((other_id, eid, round(min(1.0, trust * 0.8), 6)))
    return triggers
