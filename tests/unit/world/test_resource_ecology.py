# Tests for TCK-20260619-E21B-REGEN-SERVICE
# Covers: RESOURCE_DEPLETED emitter, regen loop, RESOURCE_RECOVERED event, parity guards
import pytest
from dataclasses import replace

from src.core.state import AuthoritativeState, ResourceNodeState, InventoryComponent, ItemStack
from src.core.updates import StateUpdate, EntityUpdate, ResourceTransferIntent, ResourceNodeUpdate
from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.world.ecology import ResourceEcologyService
from src.core.builder import V2EntityBuilder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_node(
    node_id: int = 1,
    remaining_charges: int = 5,
    max_charges: int = 5,
    regen_rate_per_tick: int = 0,
    cooldown_remaining: int = 0,
) -> ResourceNodeState:
    return ResourceNodeState(
        id=node_id,
        kind="WOOD",
        position=(10.0, 10.0),
        yields_item="wood",
        remaining_charges=remaining_charges,
        max_charges=max_charges,
        required_ticks=1,
        regen_rate_per_tick=regen_rate_per_tick,
        cooldown_remaining=cooldown_remaining,
    )


def _make_harvest_intent(node_id: int, txn_id: str = "txn-1") -> ResourceTransferIntent:
    return ResourceTransferIntent(
        transaction_id=txn_id,
        source_id=node_id,
        source_kind="NODE",
        items_add=[ItemStack("wood", 1)],
        transfer_kind="HARVEST",
    )


def _make_actor(entity_id: int, pos=(10.0, 10.0), full_inventory: bool = False):
    builder = V2EntityBuilder(entity_id).location(*pos).combat(readiness=100.0)
    if full_inventory:
        builder = builder.replace_inventory(
            InventoryComponent(max_slots=1, items=[ItemStack("wood", 20)])
        )
    return builder.build()


class _FakeGenerator:
    """Minimal stub for EntityGenerator — ecology only uses rng.get_float."""
    class _RNG:
        def get_float(self, *args, **kwargs):
            return 0.9  # > 0.5, so no seeding
    rng = _RNG()


# ---------------------------------------------------------------------------
# Group A — RESOURCE_DEPLETED emitter
# ---------------------------------------------------------------------------

def test_depleted_event_emitted_when_last_charge_harvested():
    node = _make_node(node_id=10, remaining_charges=1, max_charges=5)
    actor = _make_actor(1)
    state = AuthoritativeState(
        tick=1, seed=42,
        entities={1: actor},
        resource_nodes={10: node},
    )
    update = StateUpdate(
        entity_updates={1: EntityUpdate(entity_id=1, resource_transfers=[_make_harvest_intent(10)])}
    )
    refined = AuthoritativeApplyPipeline.refine(state, update)

    depleted_events = [
        e for e in refined.world_events_add
        if e.category == WorldEventCategory.RESOURCE_DEPLETED
    ]
    assert len(depleted_events) == 1
    assert depleted_events[0].subject == "10"


def test_depleted_event_not_emitted_when_charges_remain():
    node = _make_node(node_id=10, remaining_charges=3, max_charges=5)
    actor = _make_actor(1)
    state = AuthoritativeState(
        tick=1, seed=42,
        entities={1: actor},
        resource_nodes={10: node},
    )
    update = StateUpdate(
        entity_updates={1: EntityUpdate(entity_id=1, resource_transfers=[_make_harvest_intent(10)])}
    )
    refined = AuthoritativeApplyPipeline.refine(state, update)

    depleted_events = [
        e for e in refined.world_events_add
        if e.category == WorldEventCategory.RESOURCE_DEPLETED
    ]
    assert len(depleted_events) == 0


def test_depleted_event_not_emitted_twice_same_tick_two_actors():
    node = _make_node(node_id=10, remaining_charges=1, max_charges=5)
    actor_a = _make_actor(1)
    actor_b = _make_actor(2)
    state = AuthoritativeState(
        tick=1, seed=42,
        entities={1: actor_a, 2: actor_b},
        resource_nodes={10: node},
    )
    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, resource_transfers=[_make_harvest_intent(10, "txn-a")]),
            2: EntityUpdate(entity_id=2, resource_transfers=[_make_harvest_intent(10, "txn-b")]),
        }
    )
    refined = AuthoritativeApplyPipeline.refine(state, update)

    depleted_events = [
        e for e in refined.world_events_add
        if e.category == WorldEventCategory.RESOURCE_DEPLETED
    ]
    assert len(depleted_events) == 1


def test_depleted_event_not_emitted_on_failed_harvest():
    node = _make_node(node_id=10, remaining_charges=1, max_charges=5)
    actor = _make_actor(1, full_inventory=True)
    state = AuthoritativeState(
        tick=1, seed=42,
        entities={1: actor},
        resource_nodes={10: node},
    )
    update = StateUpdate(
        entity_updates={1: EntityUpdate(entity_id=1, resource_transfers=[_make_harvest_intent(10)])}
    )
    refined = AuthoritativeApplyPipeline.refine(state, update)

    depleted_events = [
        e for e in refined.world_events_add
        if e.category == WorldEventCategory.RESOURCE_DEPLETED
    ]
    assert len(depleted_events) == 0


# ---------------------------------------------------------------------------
# Group B — Regen loop
# ---------------------------------------------------------------------------

def _ecology_tick_state(tick: int, nodes: dict) -> AuthoritativeState:
    return AuthoritativeState(
        tick=tick, seed=42,
        resource_nodes=nodes,
        regions={},
    )


def test_regen_increments_charges_per_ecology_interval():
    node = _make_node(node_id=5, remaining_charges=2, max_charges=5, regen_rate_per_tick=1)
    state = _ecology_tick_state(tick=200, nodes={5: node})
    result = ResourceEcologyService.process_ecology(state, _FakeGenerator())

    assert 5 in result.node_updates
    assert result.node_updates[5].charges_delta == 1


def test_regen_capped_at_max_charges():
    node = _make_node(node_id=5, remaining_charges=4, max_charges=5, regen_rate_per_tick=2)
    state = _ecology_tick_state(tick=200, nodes={5: node})
    result = ResourceEcologyService.process_ecology(state, _FakeGenerator())

    assert 5 in result.node_updates
    assert result.node_updates[5].charges_delta == 1  # capped: min(5, 4+2)-4 = 1


def test_regen_skipped_when_already_at_max():
    node = _make_node(node_id=5, remaining_charges=5, max_charges=5, regen_rate_per_tick=1)
    state = _ecology_tick_state(tick=200, nodes={5: node})
    result = ResourceEcologyService.process_ecology(state, _FakeGenerator())

    assert 5 not in result.node_updates


def test_regen_skipped_when_rate_is_zero():
    node = _make_node(node_id=5, remaining_charges=2, max_charges=5, regen_rate_per_tick=0)
    state = _ecology_tick_state(tick=200, nodes={5: node})
    result = ResourceEcologyService.process_ecology(state, _FakeGenerator())

    assert 5 not in result.node_updates


def test_regen_skipped_during_cooldown():
    node = _make_node(
        node_id=5, remaining_charges=0, max_charges=5,
        regen_rate_per_tick=1, cooldown_remaining=50,
    )
    state = _ecology_tick_state(tick=200, nodes={5: node})
    result = ResourceEcologyService.process_ecology(state, _FakeGenerator())

    assert 5 not in result.node_updates


def test_regen_not_fired_on_non_ecology_tick():
    node = _make_node(node_id=5, remaining_charges=1, max_charges=5, regen_rate_per_tick=1)
    state = _ecology_tick_state(tick=201, nodes={5: node})
    result = ResourceEcologyService.process_ecology(state, _FakeGenerator())

    assert result.is_noop()


# ---------------------------------------------------------------------------
# Group C — RESOURCE_RECOVERED event
# ---------------------------------------------------------------------------

def test_recovered_event_emitted_when_depleted_node_regens():
    node = _make_node(node_id=7, remaining_charges=0, max_charges=5, regen_rate_per_tick=1)
    state = _ecology_tick_state(tick=200, nodes={7: node})
    result = ResourceEcologyService.process_ecology(state, _FakeGenerator())

    recovered = [
        e for e in result.world_events_add
        if e.category == WorldEventCategory.RESOURCE_RECOVERED
    ]
    assert len(recovered) == 1
    assert recovered[0].subject == "7"


def test_recovered_event_not_emitted_when_node_already_has_charges():
    node = _make_node(node_id=7, remaining_charges=2, max_charges=5, regen_rate_per_tick=1)
    state = _ecology_tick_state(tick=200, nodes={7: node})
    result = ResourceEcologyService.process_ecology(state, _FakeGenerator())

    recovered = [
        e for e in result.world_events_add
        if e.category == WorldEventCategory.RESOURCE_RECOVERED
    ]
    assert len(recovered) == 0


def test_recovered_event_not_emitted_twice():
    # First call: node is depleted (remaining=0) → RECOVERED emitted
    node = _make_node(node_id=7, remaining_charges=0, max_charges=5, regen_rate_per_tick=1)
    state = _ecology_tick_state(tick=200, nodes={7: node})
    result1 = ResourceEcologyService.process_ecology(state, _FakeGenerator())

    recovered1 = [
        e for e in result1.world_events_add
        if e.category == WorldEventCategory.RESOURCE_RECOVERED
    ]
    assert len(recovered1) == 1

    # Second call: node now has 1 charge (was_depleted=False) → no RECOVERED
    node2 = _make_node(node_id=7, remaining_charges=1, max_charges=5, regen_rate_per_tick=1)
    state2 = _ecology_tick_state(tick=400, nodes={7: node2})
    result2 = ResourceEcologyService.process_ecology(state2, _FakeGenerator())

    recovered2 = [
        e for e in result2.world_events_add
        if e.category == WorldEventCategory.RESOURCE_RECOVERED
    ]
    assert len(recovered2) == 0


# ---------------------------------------------------------------------------
# Group D — Parity / structural guards
# ---------------------------------------------------------------------------

def test_regen_charges_delta_is_positive():
    for remaining in range(0, 5):
        node = _make_node(node_id=1, remaining_charges=remaining, max_charges=5, regen_rate_per_tick=1)
        if remaining == 5:
            continue
        state = _ecology_tick_state(tick=200, nodes={1: node})
        result = ResourceEcologyService.process_ecology(state, _FakeGenerator())
        if 1 in result.node_updates:
            assert result.node_updates[1].charges_delta >= 1


def test_world_event_category_depleted_and_recovered_importable():
    assert WorldEventCategory.RESOURCE_DEPLETED == "RESOURCE_DEPLETED"
    assert WorldEventCategory.RESOURCE_RECOVERED == "RESOURCE_RECOVERED"


def test_state_update_carries_world_events():
    e = WorldEvent(category=WorldEventCategory.RESOURCE_DEPLETED, tick=1, subject="42")
    s = StateUpdate(world_events_add=[e])
    assert not s.is_noop()
    assert len(s.world_events_add) == 1

    s2 = StateUpdate(world_events_add=[e])
    merged = s.merge_many([s2])
    assert len(merged.world_events_add) == 2


def test_recent_world_events_on_authoritative_state():
    e = WorldEvent(category=WorldEventCategory.RESOURCE_RECOVERED, tick=1, subject="node_7")
    state = AuthoritativeState(tick=1, seed=42, recent_world_events=[e])
    assert len(state.recent_world_events) == 1
    # getattr fallback now returns the real field, not []
    result = getattr(state, "recent_world_events", [])
    assert result is state.recent_world_events
    assert len(result) == 1
