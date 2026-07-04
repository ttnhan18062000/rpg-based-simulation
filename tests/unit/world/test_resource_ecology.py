# Tests for TCK-20260619-E21B-REGEN-SERVICE
# Covers: RESOURCE_DEPLETED emitter, regen loop, RESOURCE_RECOVERED event, parity guards
import pytest
from dataclasses import replace

from src.core.state import AuthoritativeState, ResourceNodeState, InventoryComponent, ItemStack, RegionState
from src.core.updates import StateUpdate, EntityUpdate, ResourceTransferIntent, ResourceNodeUpdate
from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.world.ecology import ResourceEcologyService
from src.core.builder import V2EntityBuilder
from src.core.registries import ResourceRegistry


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


class _FakeGeneratorSeeded:
    """Stub forcing the seed-chance branch at ecology.py:122 (< 0.5) to fire."""
    class _RNG:
        def get_float(self, *args, **kwargs):
            return 0.1  # < 0.5, so seeding always fires
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


# ---------------------------------------------------------------------------
# Group E — Density-dependent regen (E21D)
# ---------------------------------------------------------------------------

def test_density_modifier_zero_entities():
    assert ResourceEcologyService._density_modifier(0) == 1.0


def test_density_modifier_at_half_cap():
    # 8 entities, cap=16: 1.0 - (8/16) * (1.0 - 0.25) = 0.625
    assert ResourceEcologyService._density_modifier(8) == 0.625


def test_density_modifier_at_cap():
    assert ResourceEcologyService._density_modifier(16) == 0.25


def test_density_modifier_above_cap_clamps_to_floor():
    assert ResourceEcologyService._density_modifier(32) == 0.25


def _ecology_tick_state_with_region(tick: int, nodes: dict, entities: dict = None) -> AuthoritativeState:
    """State with a single region covering (0,0)-(100,100) for density tests."""
    region = RegionState(id="forest_1", name="Forest", bounds=(0, 0, 100, 100))
    return AuthoritativeState(
        tick=tick,
        seed=42,
        resource_nodes=nodes,
        regions={"forest_1": region},
        entities=entities or {},
    )


def test_empty_region_regens_at_full_rate():
    """No entities → density_mod=1.0 → effective_regen = regen_rate_per_tick."""
    node = _make_node(node_id=5, remaining_charges=0, max_charges=10, regen_rate_per_tick=4)
    state = _ecology_tick_state_with_region(tick=200, nodes={5: node}, entities={})
    result = ResourceEcologyService.process_ecology(state, _FakeGenerator())
    assert 5 in result.node_updates
    assert result.node_updates[5].charges_delta == 4


def test_crowded_region_reduces_effective_regen():
    """16 entities in region → density_mod=0.25 → effective_regen = max(1, round(4*0.25)) = 1."""
    node = _make_node(node_id=5, remaining_charges=0, max_charges=10, regen_rate_per_tick=4)
    entities = {
        i: V2EntityBuilder(i).location(float(i * 5), float(i * 3)).combat(hp=10, max_hp=10).build()
        for i in range(1, 17)  # 16 entities
    }
    state = _ecology_tick_state_with_region(tick=200, nodes={5: node}, entities=entities)
    result = ResourceEcologyService.process_ecology(state, _FakeGenerator())
    assert 5 in result.node_updates
    # density_mod=0.25 → effective_regen = max(1, round(4 * 0.25)) = 1 (< 4)
    assert result.node_updates[5].charges_delta == 1


def test_partial_density_reduces_regen_proportionally():
    """8 entities → density_mod=0.625 → effective_regen = max(1, round(8*0.625)) = 5."""
    node = _make_node(node_id=5, remaining_charges=0, max_charges=20, regen_rate_per_tick=8)
    entities = {
        i: V2EntityBuilder(i).location(float(i * 5), float(i * 3)).combat(hp=10, max_hp=10).build()
        for i in range(1, 9)  # 8 entities
    }
    state = _ecology_tick_state_with_region(tick=200, nodes={5: node}, entities=entities)
    result = ResourceEcologyService.process_ecology(state, _FakeGenerator())
    assert 5 in result.node_updates
    # density_mod=0.625 → effective_regen = max(1, round(8 * 0.625)) = 5
    assert result.node_updates[5].charges_delta == 5


def test_effective_regen_never_below_one():
    """Even at max density, effective_regen >= 1 (min floor)."""
    node = _make_node(node_id=5, remaining_charges=0, max_charges=10, regen_rate_per_tick=1)
    entities = {
        i: V2EntityBuilder(i).location(float(i * 3), float(i * 3)).combat(hp=10, max_hp=10).build()
        for i in range(1, 33)  # 32 entities, well above cap
    }
    state = _ecology_tick_state_with_region(tick=200, nodes={5: node}, entities=entities)
    result = ResourceEcologyService.process_ecology(state, _FakeGenerator())
    assert 5 in result.node_updates
    assert result.node_updates[5].charges_delta >= 1


# ---------------------------------------------------------------------------
# Group F — Seeded node kind must always be a registered catalog id
# (TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP)
# ---------------------------------------------------------------------------

def _seed_state(region_kind: str) -> AuthoritativeState:
    """State with a single empty region of the given kind, sized so target_count >= 1."""
    region = RegionState(id="r1", name="Region", bounds=(0, 0, 100, 100), kind=region_kind)
    return AuthoritativeState(
        tick=200, seed=42,
        resource_nodes={},
        regions={"r1": region},
        entities={},
    )


def test_seeded_node_kind_registered_for_forest_region():
    state = _seed_state("FOREST")
    result = ResourceEcologyService.process_ecology(state, _FakeGeneratorSeeded())

    assert len(result.nodes_add) == 1
    node = result.nodes_add[0]
    assert node.kind == "wood_node"
    assert ResourceRegistry.contains(node.kind)
    assert ResourceRegistry.get(node.kind).yield_item == node.yields_item


def test_seeded_node_kind_registered_for_mountain_region():
    state = _seed_state("MOUNTAIN")
    result = ResourceEcologyService.process_ecology(state, _FakeGeneratorSeeded())

    assert len(result.nodes_add) == 1
    node = result.nodes_add[0]
    assert node.kind == "iron_vein"
    assert ResourceRegistry.contains(node.kind)
    assert ResourceRegistry.get(node.kind).yield_item == node.yields_item


def test_seeded_node_kind_registered_for_other_region():
    """This is the exact fallback branch that produced the reported STONE crash."""
    state = _seed_state("TOWN")
    result = ResourceEcologyService.process_ecology(state, _FakeGeneratorSeeded())

    assert len(result.nodes_add) == 1
    node = result.nodes_add[0]
    assert node.kind == "stone_outcrop"
    assert ResourceRegistry.contains(node.kind)
    assert ResourceRegistry.get(node.kind).yield_item == node.yields_item


@pytest.mark.parametrize("region_kind", ["FOREST", "MOUNTAIN", "TOWN", "SWAMP"])
def test_process_ecology_never_emits_unregistered_kind(region_kind):
    state = _seed_state(region_kind)
    result = ResourceEcologyService.process_ecology(state, _FakeGeneratorSeeded())

    assert len(result.nodes_add) == 1
    for node in result.nodes_add:
        assert ResourceRegistry.contains(node.kind)
