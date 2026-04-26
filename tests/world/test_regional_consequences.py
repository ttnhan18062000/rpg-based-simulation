import pytest
from src.core.state import EntityState, RegionState, AuthoritativeState, CombatComponent
from src.core.updates import StateUpdate, EntityUpdate, TaskUpdate
from src.engine.apply import ApplyPath
from src.engine.pipeline import AuthoritativeApplyPipeline

def test_regional_hazard_drain():
    """Verify that entities in high hazard regions take passive HP damage."""
    # Region from (0,0) to (10,10) with hazard 0.5
    region = RegionState(id="volcano", name="Volcano", bounds=(0, 0, 10, 10), hazard_level=0.5)
    
    # Entity at (5,5) with 100 HP
    hero = EntityState(id=1, kind="HERO", position=(5.0, 5.0), 
                       combat=CombatComponent(hp=100))
    
    state = AuthoritativeState(tick=100, seed=42, 
                               regions={"volcano": region},
                               entities={1: hero})
    
    update = StateUpdate()
    # Apply one tick
    next_state = ApplyPath.apply_generation(state, update, 101, 101)
    
    # damage = hazard(0.5) * 10 * (1 + calamity(0.0)) = 5
    assert next_state.entities[1].combat.hp == 95

def test_regional_suppression_blocks_sabotage():
    """Verify that SABOTAGE action is blocked in a suppressed region."""
    # Region with suppression
    region = RegionState(id="holy_city", name="Holy City", bounds=(0, 0, 10, 10), suppression_active=True)
    
    hero = EntityState(id=1, kind="HERO", position=(5.0, 5.0))
    state = AuthoritativeState(tick=100, seed=42, 
                               regions={"holy_city": region},
                               entities={1: hero})
    
    # Try to SABOTAGE
    task_upd = TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "SABOTAGE", "target_id": 99})
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, task=task_upd)})
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    # Should be FAILURE due to REGIONAL_SUPPRESSION
    ent_upd = refined.entity_updates[1]
    assert ent_upd.task.payload_set["outcome"] == "FAILURE"
    assert ent_upd.task.payload_set["reason"] == "REGIONAL_SUPPRESSION"

def test_regional_suppression_allows_attack():
    """Verify that ATTACK is NOT blocked (only strategic actions like SABOTAGE/RECRUIT)."""
    region = RegionState(id="holy_city", name="Holy City", bounds=(0, 0, 10, 10), suppression_active=True)
    
    hero = EntityState(id=1, kind="HERO", position=(5.0, 5.0))
    state = AuthoritativeState(tick=100, seed=42, 
                               regions={"holy_city": region},
                               entities={1: hero})
    
    # Try to ATTACK
    task_upd = TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "ATTACK", "target_id": 2})
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, task=task_upd)})
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    # Should NOT be blocked by verify_action_legality (it might fail later for target=None, but not suppression)
    ent_upd = refined.entity_updates[1]
    assert ent_upd.task.payload_set.get("reason") != "REGIONAL_SUPPRESSION"
