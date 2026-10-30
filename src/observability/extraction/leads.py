"""Lead and belief events of one entity: certainty changes, contradictions, staleness and decision divergence."""

from __future__ import annotations

from typing import Any

from src.core.strategic import LeadState
from src.observability.divergence_episode import DivergenceEpisodes
from src.observability.events import SimulationEvent
from src.observability.extraction.context import ExtractContext

# LeadCertainty enum value → float for band-crossing delta computation (lead_certainty_updated)
CERTAINTY_FLOAT: dict[str, float] = {
    "PRECISE": 1.0, "APPROXIMATE": 0.5, "VAGUE": 0.25, "EXHAUSTED": 0.0,
}

# Ticks without certainty change before a lead is considered stale (belief_stale)
BELIEF_STALE_TICKS = 50

# Project kinds inconsistent with a high-urgency DANGER concern (decision_divergence_detected)
NON_SURVIVAL_PROJECT_KINDS = frozenset(("harvesting", "exploration", "social", "crafting"))


def _certainty_changed_events(ctx: ExtractContext, eid: int, entity: Any, lid: Any, leads: tuple[Any, Any]) -> list[SimulationEvent]:
    """lead_certainty_changed and lead_certainty_updated; ``leads`` is (lead, prior_lead)."""
    tick = ctx.tick
    events: list[SimulationEvent] = []
    lead, prior_lead = leads
    if prior_lead is not None and lead.certainty != prior_lead.certainty:
        events.append(SimulationEvent(
            event_type="lead_certainty_changed", event_category="strategy",
            tick=tick, entity_id=eid, severity="INFO",
            source_system="event_extractor", message="",
            payload={
                "lead_id": lid,
                "from_certainty": str(prior_lead.certainty),
                "to_certainty": str(lead.certainty),
            },
        ))
        # Information: lead_certainty_updated — distinct from lead_certainty_changed;
        # carries float delta so InformationScorer can score direction and magnitude.
        _prior_cv = CERTAINTY_FLOAT.get(getattr(prior_lead.certainty, "value", str(prior_lead.certainty)), 0.0)
        _curr_cv = CERTAINTY_FLOAT.get(getattr(lead.certainty, "value", str(lead.certainty)), 0.0)
        events.append(SimulationEvent(
            event_type="lead_certainty_updated", event_category="strategy",
            tick=tick, entity_id=eid, severity="INFO",
            source_system="event_extractor", message="",
            payload={
                "lead_id": lid,
                "certainty_delta": round(_curr_cv - _prior_cv, 4),
                "lead_active": entity.strategic.current_project_id is not None,
            },
        ))
    return events


def _contradiction_events(ctx: ExtractContext, eid: int, lid: Any, lead: LeadState, prior_lead: LeadState | None) -> list[SimulationEvent]:
    """belief_contradiction and lead_contradiction_resolved."""
    tick = ctx.tick
    events: list[SimulationEvent] = []
    # belief_contradiction / lead_contradiction_resolved (this ticket): fires when
    # LeadContradictionSystem.enforce() (run_phase "lead_contradiction") has just
    # transitioned this lead to EXHAUSTED + test_outcome="FAILURE" this tick. Mirrors
    # the exact payload shape LeadContradictionSystem.enforce() itself builds so a
    # refine()-driven test observes identical events to a direct .enforce() call.
    _prior_failed = (
        prior_lead is not None
        and getattr(prior_lead, "test_outcome", None) == "FAILURE"
        and getattr(prior_lead.certainty, "value", str(prior_lead.certainty)) == "EXHAUSTED"
    )
    _curr_failed = (
        getattr(lead, "test_outcome", None) == "FAILURE"
        and getattr(lead.certainty, "value", str(lead.certainty)) == "EXHAUSTED"
    )
    if prior_lead is not None and _curr_failed and not _prior_failed:
        events.append(SimulationEvent(
            event_type="belief_contradiction", event_category="strategy",
            tick=tick, entity_id=eid, severity="INFO",
            source_system="lead_contradiction_system", message="",
            payload={
                "lead_id": lid,
                "provider_id": getattr(lead, "source_entity_id", None),
                "subject": lead.subject,
                "old_certainty": getattr(prior_lead.certainty, "value", str(prior_lead.certainty)),
                "failure_count": lead.failure_count,
            },
        ))
        events.append(SimulationEvent(
            event_type="lead_contradiction_resolved", event_category="strategy",
            tick=tick, entity_id=eid, severity="INFO",
            source_system="lead_contradiction_system", message="",
            payload={
                "lead_id": lid,
                "subject": lead.subject,
                "failure_count": lead.failure_count,
            },
        ))
    return events


def _stale_events(ctx: ExtractContext, eid: int, lid: Any, lead: Any, _stale_emitted: set[str]) -> list[SimulationEvent]:
    """belief_stale, once per lead per run."""
    tick = ctx.tick
    events: list[SimulationEvent] = []
    # belief_stale: lead dormant for > threshold ticks without certainty update
    # Uses discovered_tick as staleness proxy (last_updated_tick not tracked on LeadState)
    _cert_str = getattr(lead.certainty, "value", str(lead.certainty))
    _discovered = getattr(lead, "discovered_tick", tick)
    try:
        _age = tick - int(_discovered)
    except (TypeError, ValueError):
        _age = 0
    if (lid not in _stale_emitted
            and _cert_str in ("VAGUE", "EXHAUSTED")
            and _age > BELIEF_STALE_TICKS):
        _stale_emitted.add(lid)
        events.append(SimulationEvent(
            event_type="belief_stale", event_category="strategy",
            tick=tick, entity_id=eid, severity="INFO",
            source_system="event_extractor", message="",
            payload={"lead_id": lid, "certainty": _cert_str},
        ))
    return events


def _lead_loop_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """The per-lead events for every lead the entity holds."""
    run_state = ctx.run_state
    events: list[SimulationEvent] = []
    curr_leads = getattr(entity.strategic, "leads", None) or {}
    prior_leads = getattr(prior_ent.strategic, "leads", None) or {}
    _stale_emitted = run_state._emitted_stale_leads.setdefault(eid, set())
    for lid, lead in curr_leads.items():
        prior_lead = prior_leads.get(lid)
        events.extend(_certainty_changed_events(ctx, eid, entity, lid, (lead, prior_lead)))
        events.extend(_contradiction_events(ctx, eid, lid, lead, prior_lead))
        events.extend(_stale_events(ctx, eid, lid, lead, _stale_emitted))
    return events


def _belief_divergence_events(ctx: ExtractContext, eid: int, entity: Any) -> list[SimulationEvent]:
    """decision_diverged_by_belief."""
    tick = ctx.tick
    events: list[SimulationEvent] = []
    curr_leads = getattr(entity.strategic, "leads", None) or {}
    # decision_diverged_by_belief: entity pursuing non-information project while
    # holding VAGUE/EXHAUSTED leads — indicates stale belief driving sub-optimal choice
    _curr_proj_id = entity.strategic.current_project_id
    _proj_kind = DivergenceEpisodes.project_kind(_curr_proj_id, entity.strategic.projects, curr_leads)
    if DivergenceEpisodes.started(eid, _proj_kind):
        events.append(SimulationEvent(
            event_type="decision_diverged_by_belief", event_category="strategy",
            tick=tick, entity_id=eid, severity="INFO",
            source_system="event_extractor", message="",
            payload={"project_kind": _proj_kind},
        ))
    return events


def _danger_divergence_events(ctx: ExtractContext, eid: int, entity: Any) -> list[SimulationEvent]:
    """decision_divergence_detected."""
    tick = ctx.tick
    events: list[SimulationEvent] = []
    _curr_proj_id = entity.strategic.current_project_id
    # decision_divergence_detected (COGNITION): active project kind inconsistent with
    # top-urgency concern — e.g., harvesting while DANGER concern is critical
    _concerns = getattr(entity.strategic, "concerns", None) or {}
    if _curr_proj_id and _concerns:
        _top_concern = max(_concerns.values(), key=lambda c: getattr(c, "urgency", 0.0), default=None)
        _top_urgency = getattr(_top_concern, "urgency", 0.0)
        _top_kind = getattr(getattr(_top_concern, "kind", None), "value",
                            str(getattr(_top_concern, "kind", ""))) if _top_concern else ""
        if _top_urgency > 0.7 and _top_kind == "danger":
            _curr_proj2 = entity.strategic.projects.get(_curr_proj_id)
            _pk2 = getattr(getattr(_curr_proj2, "kind", None), "value",
                           str(getattr(_curr_proj2, "kind", ""))) if _curr_proj2 else ""
            if _pk2 in NON_SURVIVAL_PROJECT_KINDS:
                events.append(SimulationEvent(
                    event_type="decision_divergence_detected", event_category="strategy",
                    tick=tick, entity_id=eid, severity="INFO",
                    source_system="event_extractor", message="",
                    payload={"project_kind": _pk2, "concern_kind": _top_kind,
                             "concern_urgency": round(_top_urgency, 4)},
                ))
    return events


def lead_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """The rollback-path lead and decision block."""
    _push_shapers_phase2_active = ctx.push_shapers_phase2_active
    events: list[SimulationEvent] = []
    # Cognition: lead_certainty_changed (PP-30 side effect — state diff)
    # Information: lead_certainty_updated (band-crossing), belief_stale, decision signals
    # Flag-gated (TCK-20260806-PUSH-CUTOVER-PHASE2): the entire block below
    # (lead_certainty_changed through decision_divergence_detected) is migrated to
    # StrategyShaper — live when ENABLE_PUSH_EVENT_SHAPERS_PHASE2 is "ON" (default); this
    # block is the rollback path when it isn't.
    if not _push_shapers_phase2_active and hasattr(entity, "strategic") and hasattr(prior_ent, "strategic"):
        events.extend(_lead_loop_events(ctx, eid, entity, prior_ent))
        events.extend(_belief_divergence_events(ctx, eid, entity))
        events.extend(_danger_divergence_events(ctx, eid, entity))
    return events
