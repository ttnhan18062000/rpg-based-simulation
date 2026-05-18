# Compliance IDs: PERF-014, PERF-015
import pytest
from src.core.state import AuthoritativeState, EntityState, NavigationComponent, CombatComponent, BiologicalComponent, LifecycleComponent, StaminaComponent, StrategicComponent, ResourceNodeState
from src.core.updates import StateUpdate, EntityUpdate, WoundUpdate, NavigationUpdate
from src.core.enums import Faction
from src.engine.cadence import SystemCadence
from src.engine.apply import ApplyPath
from src.engine.pipeline import AuthoritativeApplyPipeline

def test_apply_plan_full_pipeline_parity():
    # 1. Setup multi-entity state
    entities = {}
    for i in range(1, 101):
        entities[i] = EntityState(
            id=i,
            kind="HERO" if i % 2 == 0 else "MONSTER",
            navigation=NavigationComponent(position=(float(i * 10), float(i * 10))),
            combat=CombatComponent(hp=100, max_hp=100, alive=True, atk=15, def_stat=5, speed=1, readiness=100.0),
            biological=BiologicalComponent(),
            lifecycle=LifecycleComponent(age_ticks=50, max_age_ticks=2000, active=True),
            stamina=StaminaComponent(current=100.0 if i < 50 else 80.0, max_stamina=100.0),
            strategic=StrategicComponent()
        )
    
    node1 = ResourceNodeState(id=1, kind="WOOD", position=(50.0, 50.0), yields_item="WOOD_LOG", remaining_charges=10, max_charges=10, required_ticks=5)
    
    state = AuthoritativeState(
        tick=10,
        seed=12345,
        world_time=5000,
        entities=entities,
        resource_nodes={1: node1}
    )
    
    # 2. Build multi-domain state update using legal worker proposals (NavigationUpdate target)
    e_upds = {
        1: EntityUpdate(entity_id=1, navigation=NavigationUpdate(target_set=(15.0, 15.0))),
        2: EntityUpdate(entity_id=2, wound_update=WoundUpdate(wounds_add=[], scars_add=[])),
        50: EntityUpdate(entity_id=50, property_updates={"test_prop": 42})
    }
    
    update = StateUpdate(
        entity_updates=e_upds,
        node_updates={},
        force_full_scan=True
    )
    
    # 3. Refine update through full pipeline (invoking compactor and pipeline phases)
    refined_upd = AuthoritativeApplyPipeline.refine(state, update)
    
    # 4. Apply refined update using our refactored ApplyPlan precomputing engine
    new_state = ApplyPath.apply_generation(state, refined_upd, next_tick=11, cadence=SystemCadence())
    
    # 5. Verify exact determinism and correct state transition
    assert new_state.tick == 11
    # 1 step towards (15.0, 15.0) from (10.0, 10.0) is (10.0, 11.0)
    assert new_state.entities[1].navigation.position == (10.0, 11.0)
    # Entities 50..100 had stamina < max_stamina (80.0), so their stamina should have regenerated
    assert new_state.entities[75].stamina.current > 80.0
    # Unaffected entity 10 aged by 1 tick
    assert new_state.entities[10].lifecycle.age_ticks == 51
