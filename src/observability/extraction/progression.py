"""Progression events of one entity: xp, level, evolution, skills, traits, conversion and the plateau signal."""

from __future__ import annotations

from typing import Any

from src.observability.events import SimulationEvent
from src.observability.extraction.context import ExtractContext

# How many ticks without XP before progression_plateau_detected fires (xp_rate_zero)
XP_PLATEAU_TICKS = 50


def xp_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """xp_granted and level_up (rollback path only)."""
    tick = ctx.tick
    _push_shapers_phase2_active = ctx.push_shapers_phase2_active
    events: list[SimulationEvent] = []
    # XP granted and level-up (via IdentityComponent). Flag-gated
    # (TCK-20260806-PUSH-CUTOVER-PHASE2): live behind ProgressionShaper when
    # ENABLE_PUSH_EVENT_SHAPERS_PHASE2 is "ON" (default); this block is the rollback path.
    if not _push_shapers_phase2_active and hasattr(entity, "identity") and hasattr(prior_ent, "identity"):
        xp_delta = entity.identity.evolution_points - prior_ent.identity.evolution_points
        if xp_delta > 0:
            events.append(SimulationEvent(
                event_type="xp_granted", event_category="lifecycle",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={"amount": xp_delta},
            ))
        if entity.identity.evolution_level > prior_ent.identity.evolution_level:
            events.append(SimulationEvent(
                event_type="level_up", event_category="lifecycle",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={"new_level": entity.identity.evolution_level},
            ))
    return events


def evolution_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """entity_evolved (rollback path only)."""
    tick = ctx.tick
    _push_shapers_phase2_active = ctx.push_shapers_phase2_active
    events: list[SimulationEvent] = []
    # Species evolution (TCK-20260906-ENTITY-EVOLVED-EVENT-GAP): EvolutionSystem
    # (src/engine/evolution.py) transforms `kind` at level thresholds 10/25/50
    # (e.g. GOBLIN->GOBLIN_WARRIOR). `kind` is a plain EntityState field, not gated
    # behind identity/combat, so this check does not need the `hasattr` guards above.
    # Flag-gated, same rollback pattern as the XP/level-up block above.
    if (not _push_shapers_phase2_active
            and getattr(entity, "kind", None) != getattr(prior_ent, "kind", None)):
        events.append(SimulationEvent(
            event_type="entity_evolved", event_category="lifecycle",
            tick=tick, entity_id=eid, severity="INFO",
            source_system="event_extractor", message="",
            payload={"previous_kind": prior_ent.kind, "new_kind": entity.kind},
        ))
    return events


def _unlock_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """skill_unlocked, trait_expressed and pillar_trait_unlocked, each in sorted id order."""
    tick = ctx.tick
    events: list[SimulationEvent] = []
    _curr_id = entity.identity
    _prior_id = prior_ent.identity
    _curr_skills = getattr(_curr_id, "learned_skills", None) or frozenset()
    _prior_skills = getattr(_prior_id, "learned_skills", None) or frozenset()
    for _sk in sorted(set(_curr_skills) - set(_prior_skills), key=lambda _id: _id):
        events.append(SimulationEvent(
            event_type="skill_unlocked", event_category="lifecycle",
            tick=tick, entity_id=eid, severity="INFO",
            source_system="event_extractor", message="",
            payload={"skill_id": _sk, "tick": tick},
        ))

    _curr_traits = getattr(_curr_id, "traits", None) or frozenset()
    _prior_traits = getattr(_prior_id, "traits", None) or frozenset()
    for _tr in sorted(set(_curr_traits) - set(_prior_traits), key=lambda _id: _id):
        events.append(SimulationEvent(
            event_type="trait_expressed", event_category="lifecycle",
            tick=tick, entity_id=eid, severity="INFO",
            source_system="event_extractor", message="",
            payload={"trait_id": _tr, "tick": tick},
        ))

    _curr_breaks = getattr(_curr_id, "active_breakthroughs", None) or frozenset()
    _prior_breaks = getattr(_prior_id, "active_breakthroughs", None) or frozenset()
    for _bt in sorted(set(_curr_breaks) - set(_prior_breaks), key=lambda _id: _id):
        events.append(SimulationEvent(
            event_type="pillar_trait_unlocked", event_category="lifecycle",
            tick=tick, entity_id=eid, severity="INFO",
            source_system="event_extractor", message="",
            payload={"trait_id": _bt, "tick": tick},
        ))
    return events


def _plateau_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """progression_conversion_applied and progression_plateau_detected."""
    run_state = ctx.run_state
    tick = ctx.tick
    events: list[SimulationEvent] = []
    _curr_id = entity.identity
    _prior_id = prior_ent.identity
    _curr_skills = getattr(_curr_id, "learned_skills", None) or frozenset()
    _prior_skills = getattr(_prior_id, "learned_skills", None) or frozenset()
    # progression_conversion_applied: unspent_ap decreased = AP converted to permanent stat
    _curr_ap = getattr(_curr_id, "unspent_ap", 0)
    _prior_ap = getattr(_prior_id, "unspent_ap", 0)
    if isinstance(_curr_ap, int) and isinstance(_prior_ap, int) and _curr_ap < _prior_ap:
        events.append(SimulationEvent(
            event_type="progression_conversion_applied", event_category="lifecycle",
            tick=tick, entity_id=eid, severity="INFO",
            source_system="event_extractor", message="",
            payload={"ap_spent": _prior_ap - _curr_ap, "tick": tick},
        ))

    # progression_plateau_detected: XP rate dropped to zero or skill silence
    _curr_xp = getattr(_curr_id, "evolution_points", 0)
    _prior_xp = getattr(_prior_id, "evolution_points", 0)
    if _curr_xp != _prior_xp:
        run_state._last_xp_tick[eid] = tick
    elif eid not in run_state._emitted_plateau:
        _since = tick - run_state._last_xp_tick.get(eid, 0)
        if _since > XP_PLATEAU_TICKS:
            run_state._emitted_plateau.add(eid)
            events.append(SimulationEvent(
                event_type="progression_plateau_detected", event_category="lifecycle",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={"type": "xp_rate_zero", "ticks_since_xp": _since},
            ))
        elif (getattr(_curr_id, "evolution_level", 1) >= 5
                and not set(_curr_skills)):
            run_state._emitted_plateau.add(eid)
            events.append(SimulationEvent(
                event_type="progression_plateau_detected", event_category="lifecycle",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={"type": "skill_silence",
                         "level": getattr(_curr_id, "evolution_level", 1)},
            ))
    return events


def progression_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """The rollback-path progression block: unlocks, conversion and plateau."""
    _push_shapers_phase2_active = ctx.push_shapers_phase2_active
    events: list[SimulationEvent] = []
    # Progression: skill_unlocked, trait_expressed, pillar_trait_unlocked,
    # progression_conversion_applied, progression_plateau_detected. Flag-gated
    # (TCK-20260806-PUSH-CUTOVER-PHASE2): live behind ProgressionShaper when
    # ENABLE_PUSH_EVENT_SHAPERS_PHASE2 is "ON" (default); this block is the rollback path.
    if not _push_shapers_phase2_active and hasattr(entity, "identity") and hasattr(prior_ent, "identity"):
        events.extend(_unlock_events(ctx, eid, entity, prior_ent))
        events.extend(_plateau_events(ctx, eid, entity, prior_ent))
    return events
