"""Agency and strategy events of one entity, and the population-level rejection cascade."""

from __future__ import annotations

from typing import Any

from src.observability.events import SimulationEvent
from src.observability.extraction.context import ExtractContext


def route_events(ctx: ExtractContext, eid: int, e_upd_ext: Any) -> list[SimulationEvent]:
    """route_selected, action_executed, route_family_first_use and defer_with_reason (rollback path only)."""
    run_state = ctx.run_state
    tick = ctx.tick
    _push_shapers_phase2_active = ctx.push_shapers_phase2_active
    events: list[SimulationEvent] = []
    prop = getattr(e_upd_ext, "property_updates", None) or {}
    if not _push_shapers_phase2_active:
        # Agency: route_selected / action_executed
        routing_family = prop.get("last_routing_family")
        if routing_family:
            events.append(SimulationEvent(
                event_type="route_selected", event_category="strategy",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={"family": routing_family},
            ))
            events.append(SimulationEvent(
                event_type="action_executed", event_category="strategy",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={"family": routing_family},
            ))
            # Agency: route_family_first_use (once per novel family per entity per run)
            seen = run_state._seen_routing_families.setdefault(eid, set())
            if routing_family not in seen:
                seen.add(routing_family)
                events.append(SimulationEvent(
                    event_type="route_family_first_use", event_category="strategy",
                    tick=tick, entity_id=eid, severity="INFO",
                    source_system="event_extractor", message="",
                    payload={"entity_id": eid, "family": routing_family, "tick": tick},
                ))

        # Agency: defer_with_reason — property set by phase.py on DEFER_WITH_REASON
        # path. Key "last_defer_reason" must match phase.py property_updates key
        # exactly.
        defer_reason = prop.get("last_defer_reason")
        if defer_reason:
            events.append(SimulationEvent(
                event_type="defer_with_reason", event_category="strategy",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={"entity_id": eid, "reason": defer_reason, "tick": tick},
            ))
    return events


def belief_events(ctx: ExtractContext, eid: int, e_upd_ext: Any) -> list[SimulationEvent]:
    """self_model_updated, belief_assimilated, belief_updated, route_new_query and cooperation_event (rollback path only)."""
    tick = ctx.tick
    prior_state = ctx.prior_state
    _push_shapers_phase2_active = ctx.push_shapers_phase2_active
    events: list[SimulationEvent] = []
    prop = getattr(e_upd_ext, "property_updates", None) or {}
    if not _push_shapers_phase2_active:
        # Cognition: self_model_updated (PP-03)
        if getattr(e_upd_ext, "self_model_bundle_set", None) is not None:
            events.append(SimulationEvent(
                event_type="self_model_updated", event_category="strategy",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={},
            ))

        # Information: belief_assimilated + belief_updated (PP-04)
        if prop.get("last_assimilated_tick") == prior_state.tick:
            subject = prop.get("last_assimilated_subject", "unknown")
            events.append(SimulationEvent(
                event_type="belief_assimilated", event_category="strategy",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={"subject": subject},
            ))
            events.append(SimulationEvent(
                event_type="belief_updated", event_category="strategy",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={"subject": subject},
            ))

        # Information: route_new_query (fix 4,
        # TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE)
        if prop.get("last_routed_query_tick") == prior_state.tick:
            subject = prop.get("last_routed_query_subject", "unknown")
            events.append(SimulationEvent(
                event_type="route_new_query", event_category="strategy",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={"subject": subject},
            ))

        # Social: cooperation_event (PP-05)
        if prop.get("last_cooperation_decision") is not None:
            events.append(SimulationEvent(
                event_type="cooperation_event", event_category="social",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={"entity_id": eid,
                         "decision": str(prop["last_cooperation_decision"])},
            ))
    return events


def _rejection_tally(ctx: ExtractContext) -> tuple[int, dict[str, int]]:
    """The number of rejected intent results this tick and a count per reason."""
    update = ctx.update
    _total_rejections = 0
    _reason_counts: dict[str, int] = {}
    _all_upd = getattr(update, "entity_updates", {}) or {}
    for _e_upd in _all_upd.values():
        for _ir in (getattr(_e_upd, "intent_results", None) or []):
            if not getattr(_ir, "accepted", True):
                _total_rejections += 1
                _r = getattr(_ir, "reason", None) or "unknown"
                _reason_counts[_r] = _reason_counts.get(_r, 0) + 1
    return _total_rejections, _reason_counts


def rejection_cascade_events(ctx: ExtractContext) -> list[SimulationEvent]:
    """rejection_cascade_tick, a population aggregate computed after the entity loop (rollback path only)."""
    tick = ctx.tick
    _push_shapers_agency_active = ctx.push_shapers_agency_active
    events: list[SimulationEvent] = []
    # Agency: rejection_cascade_tick — post-entity-loop population aggregate. Flag-gated
    # (TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP): live behind AgencyShaper when
    # ENABLE_PUSH_EVENT_SHAPERS_AGENCY is "ON" (default); the block below is the rollback path.
    if not _push_shapers_agency_active:
        _total_rejections, _reason_counts = _rejection_tally(ctx)
        if _total_rejections >= ctx.max_consecutive_rejections:
            _dominant = max(_reason_counts, key=_reason_counts.__getitem__) if _reason_counts else "unknown"
            events.append(SimulationEvent(
                event_type="rejection_cascade_tick", event_category="strategy",
                tick=tick, entity_id=None, severity="WARNING",
                source_system="event_extractor", message="",
                payload={
                    "count": _total_rejections,
                    "tick": tick,
                    "dominant_failure_reason": _dominant,
                },
            ))
    return events
