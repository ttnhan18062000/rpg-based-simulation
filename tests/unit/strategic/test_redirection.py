from src.core.builder import V2EntityBuilder
from src.core.models.inventory import ItemStack
from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate
from src.systems.strategic_systems.redirection import StrategicRedirectionSystem


def _entity_with_items(entity_id: int, x: float, y: float):
    return (
        V2EntityBuilder(entity_id)
        .kind("hero")
        .location(x, y)
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
        .lifecycle(active=True)
        .inventory(items=[ItemStack(item_id="iron_ore", quantity=1)])
        .build()
    )


def test_redirection_enforce_targets_nearest_town_tile_not_arbitrary_sort():
    """StrategicRedirectionSystem.enforce()'s return-to-town fallback must pick the town tile
    nearest to the requesting entity, not the globally-lowest-sorted tile across every town
    region in the world (TCK-20260824-TOWN-CENTER-POINTER-FIX). An entity near (70, 70) with a
    far cluster near (10, 10) and a near cluster near (70, 70) must be routed to the near
    cluster -- the old sorted(list(town_tiles))[0] pick would send it to (10, 10) instead, since
    (10, 10) sorts lowest regardless of entity position."""
    entity = _entity_with_items(1, 70.0, 70.0)
    town_tiles = {(10, 10), (70, 70)}
    # tick=9, entity_id=1: default SystemCadence.strategic_intelligence=10, and should_run's
    # stagger is (tick + entity_id) % cadence == 0 -> (9 + 1) % 10 == 0, so this entity's
    # redirection pass actually runs on this tick.
    state = AuthoritativeState(
        tick=9, seed=1, entities={1: entity}, town_tiles=town_tiles, town_center=(0.0, 0.0)
    )

    result = StrategicRedirectionSystem.enforce(state, StateUpdate())

    nav = result.entity_updates[1].navigation
    assert nav is not None and nav.target_set == (70.0, 70.0), (
        f"expected nearest town tile (70.0, 70.0), got {nav.target_set if nav else None}"
    )
