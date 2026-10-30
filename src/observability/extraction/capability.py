"""Capability trend events of one entity: capability_growth_stalled."""

from __future__ import annotations

from typing import Any

from src.observability.events import SimulationEvent
from src.observability.extraction.context import ExtractContext

# How many ticks with zero movement across level/skills/gear/gold before
# capability_growth_stalled fires (TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE)
CAPABILITY_STALL_TICKS = 300


def _capability_growth(entity: Any, prior_ent: Any) -> tuple[bool, Any]:
    """Whether level, skills, gear or gold grew, and the current level."""
    _cap_curr_id = entity.identity
    _cap_curr_level = getattr(_cap_curr_id, "evolution_level", 1)
    _cap_prior_level = getattr(prior_ent.identity, "evolution_level", 1)
    _cap_curr_skills = getattr(_cap_curr_id, "learned_skills", None) or frozenset()
    _cap_prior_skills = getattr(prior_ent.identity, "learned_skills", None) or frozenset()
    _cap_curr_gold = getattr(entity.inventory, "gold", 0)
    _cap_prior_gold = getattr(prior_ent.inventory, "gold", 0)
    _cap_curr_slots = getattr(entity.equipment, "slots", None)
    _cap_prior_slots = getattr(prior_ent.equipment, "slots", None)
    _cap_curr_gear = (sum(1 for v in _cap_curr_slots.values() if v)
                      if isinstance(_cap_curr_slots, dict) else 0)
    _cap_prior_gear = (sum(1 for v in _cap_prior_slots.values() if v)
                       if isinstance(_cap_prior_slots, dict) else 0)
    _cap_levels_numeric = isinstance(_cap_curr_level, (int, float)) and isinstance(_cap_prior_level, (int, float))
    _cap_gold_numeric = isinstance(_cap_curr_gold, (int, float)) and isinstance(_cap_prior_gold, (int, float))

    _cap_grew = (
        (_cap_levels_numeric and _cap_curr_level > _cap_prior_level)
        or len(_cap_curr_skills) > len(_cap_prior_skills)
        or _cap_curr_gear > _cap_prior_gear
        or (_cap_gold_numeric and _cap_curr_gold > _cap_prior_gold)
    )
    return _cap_grew, _cap_curr_level


def capability_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """capability_growth_stalled, once per entity per run."""
    run_state = ctx.run_state
    tick = ctx.tick
    events: list[SimulationEvent] = []
    # Capability trend / life-arc coherence (TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-
    # LIFECYCLE). NEW signal, not a Phase 1/2 migration — no ProgressionShaper equivalent
    # exists, so there is no double-fire risk and this block is deliberately NOT gated
    # behind _push_shapers_phase2_active; it always runs regardless of that flag's value
    # (see agent-working/staging_artifacts/TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE/
    # investigation.md's architecture-decision section for the full reasoning).
    if (hasattr(entity, "identity") and hasattr(prior_ent, "identity")
            and hasattr(entity, "lifecycle") and hasattr(entity, "equipment")
            and hasattr(entity, "inventory")):
        _cap_grew, _cap_curr_level = _capability_growth(entity, prior_ent)
        if eid not in run_state._last_capability_growth_tick:
            run_state._last_capability_growth_tick[eid] = tick
        if _cap_grew:
            run_state._last_capability_growth_tick[eid] = tick
        elif eid not in run_state._emitted_capability_stalled:
            _since_growth = tick - run_state._last_capability_growth_tick[eid]
            if _since_growth > CAPABILITY_STALL_TICKS:
                run_state._emitted_capability_stalled.add(eid)
                events.append(SimulationEvent(
                    event_type="capability_growth_stalled", event_category="lifecycle",
                    tick=tick, entity_id=eid, severity="INFO",
                    source_system="event_extractor", message="",
                    payload={"ticks_since_growth": _since_growth, "level": _cap_curr_level},
                ))
    return events
