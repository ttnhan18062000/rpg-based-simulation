# tests/verify/test_recovery_gaps.py
import pytest
from src_legacy.core.state import AuthoritativeState, EntityState, IdentityComponent, CombatComponent, RegionState, BuildingState, TaskComponent
from src_legacy.core.updates import StateUpdate, EntityUpdate, IdentityUpdate, TaskUpdate
from src_legacy.engine.pipeline import AuthoritativeApplyPipeline

def test_regional_hazard_impact():
    # Setup state with a hazardous region
    region = RegionState(id="r1", name="Toxic Swamp", bounds=(0,0,10,10), hazard_level=10.0)
    entity = EntityState(id=1, kind="HERO", position=(5,5), 
                         combat=CombatComponent(hp=100, max_hp=100))
    state = AuthoritativeState(tick=1, seed=42, 
                               entities={1: entity},
                               regions={"r1": region})
    
    # Propose empty update
    raw_update = StateUpdate()
    
    # Refine (should apply hazard)
    refined = AuthoritativeApplyPipeline.refine(state, raw_update)
    
    # Verify refined update has HP drain
    # Formula: 0.5 * 10 * (1 + 0) = 5
    ent_upd = refined.entity_updates[1]
    assert ent_upd.combat is not None
    assert ent_upd.combat.hp_delta == -5

def test_building_sabotage():
    # Setup state with a functional shop
    building = BuildingState(id=1, kind="shop", position=(10,10), hp=100)
    # Entity with sabotage intent
    entity = EntityState(id=2, kind="HERO", position=(9,10), 
                         task=TaskComponent(work_kind="SABOTAGE", payload={"target_pos": (10,10)}))
    state = AuthoritativeState(tick=1, seed=42, 
                               entities={2: entity},
                               buildings={1: building},
                               building_tiles={(10,10): "shop"})
    
    # Propose sabotage (Intent mapping)
    # In a real run, the worker would propose this. We simulate the proposal here.
    raw_update = StateUpdate(entity_updates={
        2: EntityUpdate(entity_id=2, task=TaskUpdate(work_kind_set="SABOTAGE", payload_set={"target_pos": (10,10)}))
    })
    
    # Refine
    refined = AuthoritativeApplyPipeline.refine(state, raw_update)
    
    # Verify building update
    b_upd = refined.building_updates[1]
    assert b_upd.hp_delta == -50
    assert b_upd.functional_set is True # Still has 50 HP left

def test_evolution_trigger():
    # Setup state with entity near threshold
    entity = EntityState(id=3, kind="GOBLIN", position=(0,0),
                         identity=IdentityComponent(evolution_points=950))
    state = AuthoritativeState(tick=1, seed=42, entities={3: entity})
    
    # Propose 60 points delta
    raw_update = StateUpdate(entity_updates={3: EntityUpdate(entity_id=3, 
        identity=IdentityUpdate(evolution_points_delta=60))})
    
    # Refine
    refined = AuthoritativeApplyPipeline.refine(state, raw_update)
    
    # Verify evolution
    ent_upd = refined.entity_updates[3]
    assert ent_upd.kind_set == "GOBLIN_WARRIOR"
    assert ent_upd.identity.evolution_level_set == 2
    # Points delta should be 60 (proposed) - 1000 (consumed) = -940
    # So new state points will be 950 - 940 = 10
    assert ent_upd.identity.evolution_points_delta == -940
