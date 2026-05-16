import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState
from src.core.dirty import DirtySet
from src.core.updates import StateUpdate, EntityUpdate, CombatUpdate, ResourceNodeUpdate
from src.core.state import ResourceNodeState
from src.perf.scenarios import V2EntityBuilder

def test_dirty_set_refresh_with_base_dirty_adds_later_resource_node_update():
    state = AuthoritativeState(tick=0, seed=42)

    ent = V2EntityBuilder(1).build()
    node = ResourceNodeState(
        id=99,
        kind="WOOD",
        position=(0, 0),
        yields_item="wood",
        remaining_charges=10,
        max_charges=10,
        required_ticks=5,
    )

    state = replace(
        state,
        entities={1: ent},
        resource_nodes={99: node},
    )

    phase1 = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                combat=CombatUpdate(hp_delta=-1),
            )
        }
    )
    d1 = DirtySet.from_update(state, phase1)

    phase2 = replace(
        phase1,
        node_updates={
            99: ResourceNodeUpdate(node_id=99, charges_delta=-1)
        },
        dirty_set=d1,
    )

    d2 = DirtySet.from_update(state, phase2, base_dirty=d1)

    assert 99 in d2.resource_node_ids
    assert 1 in d2.combat_entities
