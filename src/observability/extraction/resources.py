"""World-level resource, ecology, spawn-cadence and economy-conservation events."""

from __future__ import annotations

from src.observability.entity_kind_constants import SPAWN_CADENCE_EXCLUDED_KINDS
from src.observability.events import SimulationEvent
from src.observability.extraction.context import ExtractContext

# Spawn interval (the retired SpawnService's 50-tick interval; kept as this extractor's own cadence for the spawn-density events, 2.122)
_SPAWN_INTERVAL = 50


def resource_node_events(ctx: ExtractContext) -> list[SimulationEvent]:
    """resource_node_depleted, resource_node_regenerated and node_recharged (rollback path only)."""
    tick = ctx.tick
    prior_state = ctx.prior_state
    current_state = ctx.current_state
    _push_shapers_phase2_active = ctx.push_shapers_phase2_active
    events: list[SimulationEvent] = []
    # Resource node depletion and regeneration. Flag-gated (TCK-20260806-PUSH-CUTOVER-PHASE2):
    # live behind DeferredInstrumentationShaper when ENABLE_PUSH_EVENT_SHAPERS_PHASE2 is "ON"
    # (default); this block is the rollback path.
    if not _push_shapers_phase2_active and hasattr(current_state, "resource_nodes") and hasattr(prior_state, "resource_nodes"):
        for node_id, node in current_state.resource_nodes.items():
            prior_node = prior_state.resource_nodes.get(node_id)
            if prior_node is None:
                continue
            if prior_node.remaining_charges > 0 and node.remaining_charges == 0:
                events.append(SimulationEvent(
                    event_type="resource_node_depleted", event_category="resource",
                    tick=tick, entity_id=None, severity="INFO",
                    source_system="event_extractor", message="",
                    payload={"node_id": node_id, "charges": 0, "max_charges": node.max_charges},
                ))
            elif prior_node.remaining_charges == 0 and node.remaining_charges > 0:
                events.append(SimulationEvent(
                    event_type="resource_node_regenerated", event_category="resource",
                    tick=tick, entity_id=None, severity="INFO",
                    source_system="event_extractor", message="",
                    payload={"node_id": node_id, "charges": node.remaining_charges, "max_charges": node.max_charges},
                ))
                # World: node_recharged — distinct from resource_node_regenerated (scored by WorldDynamicsScorer)
                # Only on 0→>0 transition (node_recharged is the scored event; resource_node_regenerated is unscored_intentional)
                events.append(SimulationEvent(
                    event_type="node_recharged", event_category="resource",
                    tick=tick, entity_id=None, severity="INFO",
                    source_system="event_extractor", message="",
                    payload={"node_id": node_id, "charges": node.remaining_charges},
                ))
    return events


def ecology_events(ctx: ExtractContext) -> list[SimulationEvent]:
    """ecology_cycle_completed every 200 ticks (rollback path only)."""
    tick = ctx.tick
    current_state = ctx.current_state
    _push_shapers_phase2_active = ctx.push_shapers_phase2_active
    events: list[SimulationEvent] = []
    # World: ecology_cycle_completed — fires once per region per ecology interval (every 200 ticks)
    # ResourceEcologyService.ECOLOGY_INTERVAL == 200. Flag-gated
    # (TCK-20260806-PUSH-CUTOVER-PHASE2): live behind WorldDynamicsShaper when
    # ENABLE_PUSH_EVENT_SHAPERS_PHASE2 is "ON" (default); this block is the rollback path.
    if not _push_shapers_phase2_active and tick % 200 == 0 and hasattr(current_state, "regions"):
        for _r_id, _region in (current_state.regions or {}).items():
            events.append(SimulationEvent(
                event_type="ecology_cycle_completed", event_category="region",
                tick=tick, entity_id=None, severity="INFO",
                source_system="event_extractor", message="",
                payload={"region_id": _r_id,
                         "cycle_type": getattr(_region, "kind", "unknown"),
                         "net_pressure_delta": 0.0},
            ))
    return events


def spawn_cadence_events(ctx: ExtractContext) -> list[SimulationEvent]:
    """spawn_cadence_fired (rollback path only)."""
    tick = ctx.tick
    update = ctx.update
    _push_shapers_phase2_active = ctx.push_shapers_phase2_active
    events: list[SimulationEvent] = []
    # World: spawn_cadence_fired — detects spawn batch committed on cadence tick. Flag-gated
    # (TCK-20260806-PUSH-CUTOVER-PHASE2), same rollback pattern.
    if not _push_shapers_phase2_active and tick % _SPAWN_INTERVAL == 0:
        _spawned_monsters = [
            e for e in (getattr(update, "entities_add", None) or [])
            if getattr(e, "kind", None) not in SPAWN_CADENCE_EXCLUDED_KINDS
        ]
        if _spawned_monsters:
            events.append(SimulationEvent(
                event_type="spawn_cadence_fired", event_category="lifecycle",
                tick=tick, entity_id=None, severity="INFO",
                source_system="event_extractor", message="",
                payload={"spawned_count": len(_spawned_monsters), "tick": tick},
            ))
    return events


def conservation_events(ctx: ExtractContext, emitted: list[SimulationEvent]) -> list[SimulationEvent]:
    """conservation_law_verified when this extract() call already emitted an economy event (rollback path only)."""
    tick = ctx.tick
    _push_shapers_phase2_active = ctx.push_shapers_phase2_active
    events: list[SimulationEvent] = []
    # Economy: conservation_law_verified — throttled (1 per 50 ticks) to avoid noise
    # Fires when economy transactions occurred this tick, implying the conservation law was
    # checked. Flag-gated (TCK-20260806-PUSH-CUTOVER-PHASE2): live behind
    # run_shadow_shapers()'s own cross-shaper aggregation when ENABLE_PUSH_EVENT_SHAPERS_PHASE2
    # is "ON" (default); this block is the rollback path.
    if not _push_shapers_phase2_active and tick % 50 == 0:
        _has_economy_tx = any(
            e.event_type in ("resource_harvested", "item_crafted", "shop_transaction",
                             "paid_information_transaction", "gold_sink_fired")
            for e in emitted
        )
        if _has_economy_tx:
            events.append(SimulationEvent(
                event_type="conservation_law_verified", event_category="economy",
                tick=tick, entity_id=None, severity="INFO",
                source_system="event_extractor", message="",
                payload={"tick": tick},
            ))
    return events
