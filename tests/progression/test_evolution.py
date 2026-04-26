import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EquipSlot
from src.core.updates import EntityUpdate, IdentityUpdate, StateUpdate
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.apply import ApplyPath
from src.core.builder import V2EntityBuilder
from src.progression.leveling import LevelingService

def test_goblin_evolution():
    # Create goblin_0 at level 9
    entity = V2EntityBuilder(entity_id=1).monster("goblin", 0).build()
    entity = replace(entity, identity=replace(entity.identity, evolution_level=9, evolution_points=0))
    
    # Give enough XP to reach level 10
    xp_needed = LevelingService.get_xp_required(9)
    update = EntityUpdate(
        entity_id=1,
        identity=IdentityUpdate(evolution_points_delta=xp_needed)
    )
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})
    state_upd = StateUpdate(entity_updates={1: update})
    
    refined = AuthoritativeApplyPipeline.refine(state, state_upd)
    new_state = ApplyPath.apply_generation(state, refined)
    new_entity = new_state.entities[1]
    
    assert new_entity.kind == "goblin_1"
    # Verify gear refresh
    assert new_entity.equipment.slots[EquipSlot.MAIN_HAND] == "iron_sword"
    assert new_entity.equipment.slots[EquipSlot.TORSO] == "leather_armor"

def test_no_evolution_before_threshold():
    # Create goblin_0 at level 8, gain 1 level -> level 9
    entity = V2EntityBuilder(entity_id=1).monster("goblin", 0).build()
    entity = replace(entity, identity=replace(entity.identity, evolution_level=8, evolution_points=0))
    
    xp_needed = LevelingService.get_xp_required(8)
    update = EntityUpdate(
        entity_id=1,
        identity=IdentityUpdate(evolution_points_delta=xp_needed)
    )
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})
    state_upd = StateUpdate(entity_updates={1: update})
    
    refined = AuthoritativeApplyPipeline.refine(state, state_upd)
    new_state = ApplyPath.apply_generation(state, refined)
    new_entity = new_state.entities[1]
    
    assert new_entity.kind == "goblin_0"
    assert new_entity.identity.evolution_level == 9
