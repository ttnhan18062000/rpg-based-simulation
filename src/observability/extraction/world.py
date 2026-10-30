"""World-level region, calamity and boss-spawn events."""

from __future__ import annotations

import logging
from typing import Any

from src.core.updates import decode_owner_faction_id_set
from src.observability.entity_kind_constants import BOSS_ENTITY_KINDS
from src.observability.events import SimulationEvent
from src.observability.extraction.context import ExtractContext

logger = logging.getLogger(__name__)


def _threat_events(ctx: ExtractContext, rid: Any, w_upd: Any) -> list[SimulationEvent]:
    """threat_evolved when trauma crosses a tier threshold."""
    tick = ctx.tick
    prior_state = ctx.prior_state
    events: list[SimulationEvent] = []
    # World: threat_evolved — trauma crossing major thresholds (25, 50, 75, 100) signals tier shift
    _prior_region = getattr(prior_state, "regions", {}).get(rid) if prior_state else None
    if _prior_region is not None:
        try:
            _prior_trauma = float(getattr(_prior_region, "trauma_score", 0.0))
            _trauma_delta = float(getattr(w_upd, "trauma_delta", 0.0))
            _new_trauma = _prior_trauma + _trauma_delta
            for _threshold in (25.0, 50.0, 75.0, 100.0):
                if _prior_trauma < _threshold <= _new_trauma:
                    events.append(SimulationEvent(
                        event_type="threat_evolved", event_category="region",
                        tick=tick, entity_id=None, severity="WARNING",
                        source_system="event_extractor", message="",
                        payload={"region_id": rid, "threshold": _threshold,
                                 "prior_trauma": round(_prior_trauma, 2),
                                 "new_trauma": round(_new_trauma, 2)},
                    ))
                    break
        except (TypeError, ValueError):
            logger.debug("threat_evolved skipped for region %s: trauma is not numeric", rid)
    return events


def region_update_events(ctx: ExtractContext) -> list[SimulationEvent]:
    """region_trauma_delta, threat_evolved, region_ownership_changed and region_transformed (rollback path only)."""
    tick = ctx.tick
    update = ctx.update
    _push_shapers_phase2_active = ctx.push_shapers_phase2_active
    events: list[SimulationEvent] = []
    # World dynamics events — from StateUpdate world_updates and entities_add. Flag-gated
    # (TCK-20260806-PUSH-CUTOVER-PHASE2): region_trauma_delta through region_transformed are
    # migrated to WorldDynamicsShaper — live when ENABLE_PUSH_EVENT_SHAPERS_PHASE2 is "ON"
    # (default); this loop is the rollback path. building_sabotaged below is a SEPARATE loop,
    # guarded independently.
    for rid, w_upd in ([] if _push_shapers_phase2_active else (getattr(update, "world_updates", None) or {}).items()):
        if getattr(w_upd, "trauma_delta", 0.0) != 0.0:
            events.append(SimulationEvent(
                event_type="region_trauma_delta", event_category="region",
                tick=tick, entity_id=None, severity="INFO",
                source_system="event_extractor", message="",
                payload={"region_id": rid, "delta": w_upd.trauma_delta},
            ))
        events.extend(_threat_events(ctx, rid, w_upd))
        if getattr(w_upd, "owner_faction_id_set", None) is not None:
            events.append(SimulationEvent(
                event_type="region_ownership_changed", event_category="region",
                tick=tick, entity_id=None, severity="WARNING",
                source_system="event_extractor", message="",
                # TCK-20261003-REGION-OWNER-NONE-SENTINEL-PERSISTED-RAW: decode the
                # unowned sentinel so a liberation reports "None", not a literal "-1".
                payload={"region_id": rid,
                         "new_owner": str(decode_owner_faction_id_set(w_upd.owner_faction_id_set))},
            ))
        if getattr(w_upd, "kind_set", None) is not None:
            events.append(SimulationEvent(
                event_type="region_transformed", event_category="region",
                tick=tick, entity_id=None, severity="INFO",
                source_system="event_extractor", message="",
                payload={"region_id": rid, "new_kind": w_upd.kind_set},
            ))
    return events


def calamity_events(ctx: ExtractContext) -> list[SimulationEvent]:
    """calamity_spawned (rollback path only)."""
    tick = ctx.tick
    update = ctx.update
    prior_state = ctx.prior_state
    _push_shapers_phase2_active = ctx.push_shapers_phase2_active
    events: list[SimulationEvent] = []
    # calamity_spawned: flag-gated (TCK-20260806-PUSH-CUTOVER-PHASE2), same rollback pattern.
    if not _push_shapers_phase2_active and getattr(update, "last_calamity_tick_set", None) == prior_state.tick:
        events.append(SimulationEvent(
            event_type="calamity_spawned", event_category="lifecycle",
            tick=tick, entity_id=None, severity="CRITICAL",
            source_system="event_extractor", message="",
            payload={"tick": tick},
        ))
    return events


def boss_spawn_events(ctx: ExtractContext) -> list[SimulationEvent]:
    """boss_spawned, narrative_milestone and raid_party_spawned (rollback path only)."""
    tick = ctx.tick
    update = ctx.update
    _push_shapers_phase2_active = ctx.push_shapers_phase2_active
    events: list[SimulationEvent] = []
    # boss_spawned / narrative_milestone (boss variant) / raid_party_spawned: flag-gated
    # (TCK-20260806-PUSH-CUTOVER-PHASE2), same rollback pattern.
    for new_ent in ([] if _push_shapers_phase2_active else (getattr(update, "entities_add", None) or [])):
        kind = getattr(new_ent, "kind", None)
        if kind in BOSS_ENTITY_KINDS:
            events.append(SimulationEvent(
                event_type="boss_spawned", event_category="lifecycle",
                tick=tick, entity_id=getattr(new_ent, "id", None), severity="WARNING",
                source_system="event_extractor", message="",
                payload={"kind": kind},
            ))
            # NARRATIVE: narrative_milestone — boss spawn (D2, D5 from plan/UQ-1)
            events.append(SimulationEvent(
                event_type="narrative_milestone",
                event_category="lifecycle",
                tick=tick,
                entity_id=getattr(new_ent, "id", None),
                severity="WARNING",
                source_system="event_extractor",
                message="",
                payload={"milestone": "first_boss_spawned", "kind": kind},
            ))
        elif kind == "goblin_raider":
            events.append(SimulationEvent(
                event_type="raid_party_spawned", event_category="lifecycle",
                tick=tick, entity_id=getattr(new_ent, "id", None), severity="WARNING",
                source_system="event_extractor", message="",
                payload={"kind": kind},
            ))
    return events
