"""Spawn, despawn and movement events of one entity (the first blocks of the old run_state.extract loop)."""

from __future__ import annotations

from typing import Any

from src.observability.config import ObservabilityMode
from src.observability.events import LifecycleEvent, MovementEvent, SimulationEvent
from src.observability.extraction.combat import real_combat_update
from src.observability.extraction.context import ExtractContext


def despawn_events(ctx: ExtractContext, eid: int, prior_ent: Any) -> list[SimulationEvent]:
    """A despawned entity: the despawn lifecycle event, plus demographic_mortality on the rollback path."""
    tick = ctx.tick
    now = ctx.now
    update = ctx.update
    _push_shapers_phase2_active = ctx.push_shapers_phase2_active
    events: list[SimulationEvent] = []
    if prior_ent is not None:
        events.append(LifecycleEvent(
            tick=tick, timestamp=now, entity_id=eid,
            action="despawn", details={"kind": prior_ent.kind, "position": prior_ent.navigation.position}
        ))
        # Demographic mortality — despawn without a combat attacker. Flag-gated
        # (TCK-20260806-PUSH-CUTOVER-PHASE2): live behind DeferredInstrumentationShaper
        # when ENABLE_PUSH_EVENT_SHAPERS_PHASE2 is "ON" (default); this branch is the
        # rollback path when it isn't. LifecycleEvent (despawn) above stays
        # unconditional — it is not a migrated event.
        if not _push_shapers_phase2_active:
            e_upd = update.entity_updates.get(eid) if update and hasattr(update, "entity_updates") else None
            has_attacker = real_combat_update(e_upd) is not None
            if not has_attacker:
                events.append(SimulationEvent(
                    event_type="demographic_mortality", event_category="lifecycle",
                    tick=tick, entity_id=eid, severity="INFO",
                    source_system="event_extractor", message="",
                    payload={"kind": prior_ent.kind},
                ))
    return events


def spawn_events(ctx: ExtractContext, eid: int, entity: Any) -> list[SimulationEvent]:
    """A newly present entity: the spawn lifecycle event, plus demographic_birth on the rollback path."""
    tick = ctx.tick
    now = ctx.now
    _push_shapers_phase2_active = ctx.push_shapers_phase2_active
    events: list[SimulationEvent] = []
    events.append(LifecycleEvent(
        tick=tick, timestamp=now, entity_id=eid,
        action="spawn", details={"kind": entity.kind, "position": entity.navigation.position}
    ))
    # demographic_birth: flag-gated (TCK-20260806-PUSH-CUTOVER-PHASE2), same pattern —
    # LifecycleEvent (spawn) above stays unconditional.
    if not _push_shapers_phase2_active:
        events.append(SimulationEvent(
            event_type="demographic_birth", event_category="lifecycle",
            tick=tick, entity_id=eid, severity="INFO",
            source_system="event_extractor", message="",
            payload={"kind": entity.kind},
        ))
    return events


def movement_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """A position change (not emitted in LIGHT or LONG_RUN mode)."""
    tick = ctx.tick
    now = ctx.now
    mode = ctx.mode
    events: list[SimulationEvent] = []
    # Movement (exclusively low-volume for non-LIGHT/LONG_RUN modes)
    if prior_ent.navigation.position != entity.navigation.position:
        if mode not in (ObservabilityMode.LIGHT, ObservabilityMode.LONG_RUN):
            events.append(MovementEvent(
                tick=tick, timestamp=now, entity_id=eid,
                start_pos=prior_ent.navigation.position,
                end_pos=entity.navigation.position
            ))
    return events
