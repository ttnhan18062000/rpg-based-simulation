"""
tests/integration/domains/memory/test_memory_update_phase_apply.py

TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING: MemoryUpdatePhase.apply() must consume
state.recent_world_events with the same one-tick-lag semantics faction_awareness already uses --
only entities named as the subject of a COMBAT_LOSS WorldEvent gain a new CausalMemoryEntry.
"""
from src.core.state import AuthoritativeState, EntityState
from src.core.updates import StateUpdate
from src.domains.memory.phase import MemoryUpdatePhase
from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory


def test_memory_update_phase_reads_prior_tick_combat_loss_world_events():
    entity_x = EntityState(id=7, kind="HERO")
    entity_y = EntityState(id=8, kind="HERO")

    recent_world_events = [
        WorldEvent(category=WorldEventCategory.COMBAT_LOSS, tick=9, region_id="wolf_den", subject="7"),
    ]
    state = AuthoritativeState(
        tick=10, seed=42, entities={7: entity_x, 8: entity_y},
        recent_world_events=recent_world_events,
    )

    trigger_events = [
        {"entity_id": int(e.subject), "kind": "combat_loss", "id": f"combat_loss_{e.tick}_{e.subject}", "region_id": e.region_id}
        for e in state.recent_world_events
        if e.category == WorldEventCategory.COMBAT_LOSS and e.subject is not None
    ]

    result = MemoryUpdatePhase.apply(state, StateUpdate(), trigger_events)

    x_cognition = result.entity_updates[7].cognition_bundle_set
    assert x_cognition is not None
    assert len(x_cognition.memory.causal.entries) == 1
    assert x_cognition.memory.causal.entries[0].event_kind == "combat_loss"

    y_cognition = result.entity_updates[8].cognition_bundle_set
    assert y_cognition is not None
    assert len(y_cognition.memory.causal.entries) == 0
