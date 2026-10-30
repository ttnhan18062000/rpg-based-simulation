"""Contract lifecycle events of one entity."""

from __future__ import annotations

from typing import Any

from src.observability.events import SimulationEvent
from src.observability.extraction.context import ExtractContext


def _new_contract_events(ctx: ExtractContext, eid: int, cid: Any, cs: Any) -> list[SimulationEvent]:
    """contract_offer_created for a contract that was not there before."""
    tick = ctx.tick
    events: list[SimulationEvent] = []
    new_status = getattr(getattr(cs, "status", None), "name",
                         str(getattr(cs, "status", "")))
    if new_status == "OFFERED":
        events.append(SimulationEvent(
            event_type="contract_offer_created", event_category="social",
            tick=tick, entity_id=eid, severity="INFO",
            source_system="event_extractor", message="",
            payload={"contract_id": cid},
        ))
    return events


def _status_change_events(ctx: ExtractContext, eid: int, cid: Any, cs: Any, prior_cs: Any) -> list[SimulationEvent]:
    """contract_offer_accepted, contract_completed, contract_lapsed and contract_expired_offer on a status change."""
    tick = ctx.tick
    events: list[SimulationEvent] = []
    curr_status = getattr(getattr(cs, "status", None), "name", str(getattr(cs, "status", "")))
    prior_status = getattr(getattr(prior_cs, "status", None), "name", str(getattr(prior_cs, "status", "")))
    if curr_status == prior_status:
        return events
    if prior_status == "OFFERED" and curr_status == "ACTIVE":
        events.append(SimulationEvent(
            event_type="contract_offer_accepted", event_category="social",
            tick=tick, entity_id=eid, severity="INFO",
            source_system="event_extractor", message="",
            payload={"contract_id": cid},
        ))
    elif curr_status == "FULFILLED":
        events.append(SimulationEvent(
            event_type="contract_completed", event_category="social",
            tick=tick, entity_id=eid, severity="INFO",
            source_system="event_extractor", message="",
            payload={"contract_id": cid},
        ))
    elif curr_status == "EXPIRED":
        if prior_status == "ACTIVE":
            events.append(SimulationEvent(
                event_type="contract_lapsed", event_category="social",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={"contract_id": cid},
            ))
        elif prior_status == "OFFERED":
            events.append(SimulationEvent(
                event_type="contract_expired_offer", event_category="social",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={"contract_id": cid},
            ))
    return events


def _transition_events(ctx: ExtractContext, eid: int, curr_contracts: Any, prior_contracts: Any) -> list[SimulationEvent]:
    """Contract offered, accepted, completed and expired transitions."""
    events: list[SimulationEvent] = []
    for cid, cs in curr_contracts.items():
        prior_cs = prior_contracts.get(cid)
        if prior_cs is None:
            events.extend(_new_contract_events(ctx, eid, cid, cs))
            continue
        events.extend(_status_change_events(ctx, eid, cid, cs, prior_cs))
    return events


def _reaped_offer_events(ctx: ExtractContext, eid: int, curr_contracts: Any, prior_contracts: Any) -> list[SimulationEvent]:
    """contract_expired_offer for a contract removed entirely."""
    tick = ctx.tick
    events: list[SimulationEvent] = []
    # PP-36: contract_expired_offer from reap path (contract removed entirely)
    for cid, prior_cs in prior_contracts.items():
        if cid in curr_contracts:
            continue
        prior_status = getattr(getattr(prior_cs, "status", None), "name",
                               str(getattr(prior_cs, "status", "")))
        if prior_status == "OFFERED":
            events.append(SimulationEvent(
                event_type="contract_expired_offer", event_category="social",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={"contract_id": cid},
            ))
    return events


def _threshold_events(ctx: ExtractContext, cid: Any, cs: Any, progress: float, source_id: Any) -> list[SimulationEvent]:
    """contract_milestone_completed for each threshold the progress passed, once per run."""
    run_state = ctx.run_state
    tick = ctx.tick
    events: list[SimulationEvent] = []
    for threshold, label in run_state._CONTRACT_MILESTONE_THRESHOLDS:
        gate_key = f"{cid}:{label}"
        if gate_key in run_state._emitted_contract_milestones:
            continue
        if progress >= threshold:
            run_state._emitted_contract_milestones.add(gate_key)
            events.append(SimulationEvent(
                event_type="contract_milestone_completed",
                event_category="social",
                tick=tick, entity_id=source_id, severity="INFO",
                source_system="event_extractor", message="",
                payload={"contract_id": cid, "milestone": label,
                         "kind": str(getattr(cs, "kind", ""))},
            ))
    return events


def _milestone_events(ctx: ExtractContext, eid: int, curr_contracts: Any) -> list[SimulationEvent]:
    """contract_milestone_completed for ACTIVE duration contracts."""
    tick = ctx.tick
    events: list[SimulationEvent] = []
    # Contract milestones: time-gated progress signals for ACTIVE duration
    # contracts. Uses (contract_id, label) gate so each milestone fires
    # exactly once per run regardless of which entity processes the contract.
    for cid, cs in curr_contracts.items():
        cs_status = getattr(getattr(cs, "status", None), "name",
                            str(getattr(cs, "status", "")))
        if cs_status != "ACTIVE":
            continue
        expiry = getattr(cs, "expiry_tick", -1)
        created = getattr(cs, "created_tick", 0)
        if not isinstance(expiry, int) or not isinstance(created, int):
            continue
        if expiry <= 0 or expiry <= created:
            continue
        elapsed = tick - created
        if elapsed <= 0:
            continue
        progress = elapsed / (expiry - created)
        source_id = getattr(cs, "source_id", eid)
        events.extend(_threshold_events(ctx, cid, cs, progress, source_id))
    return events


def contract_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """The rollback-path contract block."""
    _push_shapers_phase2_active = ctx.push_shapers_phase2_active
    events: list[SimulationEvent] = []
    # Social: contract lifecycle events (PP-35 contracts state diff). Flag-gated
    # (TCK-20260806-PUSH-CUTOVER-PHASE2): the entire block below (through
    # contract_milestone_completed) is migrated to SocialShaper — live when
    # ENABLE_PUSH_EVENT_SHAPERS_PHASE2 is "ON" (default); this block is the rollback path.
    # The Quest progress lifecycle block right after this one is a SEPARATE, unrelated,
    # NOT-migrated block (QuestEvent, out of this epic's scope) — not touched here.
    if not _push_shapers_phase2_active and hasattr(entity, "strategic") and hasattr(prior_ent, "strategic"):
        curr_contracts = getattr(entity.strategic, "contracts", None) or {}
        prior_contracts = getattr(prior_ent.strategic, "contracts", None) or {}
        events.extend(_transition_events(ctx, eid, curr_contracts, prior_contracts))
        events.extend(_reaped_offer_events(ctx, eid, curr_contracts, prior_contracts))
        events.extend(_milestone_events(ctx, eid, curr_contracts))
    return events
