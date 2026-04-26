import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, IdentityComponent, CombatComponent, TaskComponent
from src.engine.town_resolution import TownResolutionSystem
from src.core.updates import StateUpdate, EntityUpdate, TaskUpdate

def create_mock_entity(eid, pos=(10, 10), hp=50):
    return EntityState(
        id=eid,
        kind="hero",
        position=pos,
        identity=IdentityComponent(faction=0),
        combat=CombatComponent(hp=hp, max_hp=100, alive=True),
        task=TaskComponent()
    )

def test_inn_rest_recovery():
    # Entity at (5,5), which is an INN
    entity = create_mock_entity(1, pos=(5.0, 5.0), hp=50)
    state = AuthoritativeState(
        tick=1, seed=42, 
        entities={1: entity},
        town_tiles={(5, 5)},
        building_tiles={(5, 5): "inn"}
    )
    
    # Propose REST
    raw_update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "REST"}))
    })
    
    # Resolve
    update = TownResolutionSystem.resolve(state, raw_update)
    
    # Passive heal (1) + REST bonus (5) = 6
    combat_upd = update.entity_updates[1].combat
    assert combat_upd.hp_delta == 6
    assert update.entity_updates[1].readiness_delta == 10.0
