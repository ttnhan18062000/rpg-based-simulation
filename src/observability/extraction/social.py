"""Social events of one entity: group changes and social-memory shifts."""

from __future__ import annotations

from typing import Any

from src.observability.events import SimulationEvent
from src.observability.extraction.context import ExtractContext


def group_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """group_joined and group_left (rollback path only)."""
    tick = ctx.tick
    _push_shapers_phase2_active = ctx.push_shapers_phase2_active
    events: list[SimulationEvent] = []
    # Social: group_joined / group_expelled (PP-34 group membership state diff). Flag-gated
    # (TCK-20260806-PUSH-CUTOVER-PHASE2): live behind SocialShaper when
    # ENABLE_PUSH_EVENT_SHAPERS_PHASE2 is "ON" (default); this block is the rollback path.
    curr_group = getattr(entity, "group_id", None)
    prior_group = getattr(prior_ent, "group_id", None)
    if not _push_shapers_phase2_active and curr_group != prior_group:
        if curr_group is not None:
            events.append(SimulationEvent(
                event_type="group_joined", event_category="social",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={"group_id": str(curr_group)},
            ))
        else:
            events.append(SimulationEvent(
                event_type="group_expelled", event_category="social",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={"prior_group_id": str(prior_group)},
            ))
    return events


def _reputation_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """reputation_delta."""
    tick = ctx.tick
    events: list[SimulationEvent] = []
    curr_rep = getattr(entity.social, "public_reputation", None)
    prior_rep = getattr(prior_ent.social, "public_reputation", None)
    if isinstance(curr_rep, (int, float)) and isinstance(prior_rep, (int, float)):
        delta = curr_rep - prior_rep
    else:
        delta = 0.0
    if isinstance(delta, (int, float)) and abs(delta) > 0.05:
        events.append(SimulationEvent(
            event_type="reputation_delta", event_category="social",
            tick=tick, entity_id=eid, severity="INFO",
            source_system="event_extractor", message="",
            payload={"entity_id": eid, "delta": round(delta, 6)},
        ))
    return events


def _trust_memory_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """social_memory_created, once per pair per run."""
    run_state = ctx.run_state
    tick = ctx.tick
    events: list[SimulationEvent] = []
    # Social: social_memory_created — new or significantly shifted trust entry
    curr_trust = getattr(entity.social, "trust_history", None) or {}
    prior_trust = getattr(prior_ent.social, "trust_history", None) or {}
    for other_id, curr_score in curr_trust.items():
        pair = (eid, other_id)
        if pair in run_state._emitted_social_memory:
            continue
        prior_score = prior_trust.get(other_id)
        is_new = prior_score is None
        is_significant = (
            not is_new
            and isinstance(curr_score, (int, float))
            and isinstance(prior_score, (int, float))
            and abs(curr_score - prior_score) >= run_state._SOCIAL_MEMORY_THRESHOLD
        )
        if is_new or is_significant:
            run_state._emitted_social_memory.add(pair)
            events.append(SimulationEvent(
                event_type="social_memory_created", event_category="social",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={"other_entity_id": other_id,
                         "score": round(float(curr_score), 6)},
            ))
    return events


def social_memory_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """reputation_delta and social_memory_created (rollback path only)."""
    _push_shapers_phase2_active = ctx.push_shapers_phase2_active
    events: list[SimulationEvent] = []
    # Social: reputation_delta (PP-18, significant public reputation change) +
    # social_memory_created below. Flag-gated (TCK-20260806-PUSH-CUTOVER-PHASE2), same
    # rollback pattern.
    if not _push_shapers_phase2_active and hasattr(entity, "social") and hasattr(prior_ent, "social"):
        events.extend(_reputation_events(ctx, eid, entity, prior_ent))
        events.extend(_trust_memory_events(ctx, eid, entity, prior_ent))
    return events
