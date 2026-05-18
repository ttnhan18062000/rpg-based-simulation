# Compliance IDs: PERF-014, PERF-015
import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, NavigationComponent, CombatComponent, BiologicalComponent, LifecycleComponent, StaminaComponent, StrategicComponent
from src.core.updates import StateUpdate, EntityUpdate, NavigationUpdate
from src.core.movement_modes import MovementMode
from src.engine.cadence import SystemCadence
from src.engine.apply_plan import ApplyPlanBuilder, ApplyPlan, CacheInvalidationHints
from src.engine.apply import ApplyPath

def create_mock_state():
    ent1 = EntityState(
        id=1,
        kind="HERO",
        navigation=NavigationComponent(position=(10.0, 10.0)),
        combat=CombatComponent(hp=100, max_hp=100, alive=True),
        biological=BiologicalComponent(),
        lifecycle=LifecycleComponent(age_ticks=10, max_age_ticks=1000, active=True),
        stamina=StaminaComponent(current=100.0, max_stamina=100.0),
        strategic=StrategicComponent()
    )
    ent2 = EntityState(
        id=2,
        kind="HERO",
        navigation=NavigationComponent(position=(50.0, 50.0)),
        combat=CombatComponent(hp=50, max_hp=50, alive=True),
        biological=BiologicalComponent(),
        lifecycle=LifecycleComponent(age_ticks=5, max_age_ticks=1000, active=True),
        stamina=StaminaComponent(current=50.0, max_stamina=100.0), # Stamina regenerating
        strategic=StrategicComponent()
    )
    return AuthoritativeState(
        tick=100,
        seed=42,
        world_time=1000,
        entities={1: ent1, 2: ent2}
    )

def test_apply_plan_builder_grouping():
    state = create_mock_state()
    # Update entity 1 with intentional movement
    upd = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, new_position=(20.0, 20.0), moved_this_tick=True)
        }
    )
    cadence = SystemCadence(biological=1000, lifecycle=1000) # Ensure no bio/life decay
    
    plan = ApplyPlanBuilder.build_plan(state, upd, next_tick=101, cadence=cadence, passive=True, compute_entity_changes_fn=ApplyPath._compute_entity_changes)
    
    # Assert entity 1 is in entities_to_replace due to intentional movement
    assert 1 in plan.entities_to_replace
    assert "navigation" in plan.components_to_replace[1]
    
    # Assert entity 2 is also in entities_to_replace because its stamina was < max_stamina (regenerating)
    assert 2 in plan.entities_to_replace
    assert "stamina" in plan.components_to_replace[2]
    
    # Verify cache invalidation hints
    assert not plan.cache_invalidation_hints.invalidate_movement_cache

def test_apply_plan_builder_noop():
    state = create_mock_state()
    # Entity 1 is full stamina, no intentional update, no passive triggers due
    upd = StateUpdate()
    cadence = SystemCadence(biological=1000, lifecycle=1000)
    
    plan = ApplyPlanBuilder.build_plan(state, upd, next_tick=101, cadence=cadence, passive=True, compute_entity_changes_fn=ApplyPath._compute_entity_changes)
    
    # Entity 1 should NOT be replaced
    assert 1 not in plan.entities_to_replace
