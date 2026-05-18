# Compliance IDs: PERF-015
import pytest
from src.core.state import (
    AuthoritativeState, EntityState, NavigationComponent, CombatComponent,
    BiologicalComponent, LifecycleComponent, StaminaComponent, StrategicComponent,
    AttributeComponent, IdentityComponent, InventoryComponent
)
from src.core.updates import (
    StateUpdate, EntityUpdate, NavigationUpdate, CombatUpdate, AttributeUpdate, IdentityUpdate
)
from src.engine.cadence import SystemCadence
from src.engine.apply import ApplyPath
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.patches import extract_patches, NavigationPatch, CombatPatch, AttributePatch, IdentityPatch

def test_component_patch_apply_parity():
    # Setup rich multi-domain entity state
    entities = {}
    for i in range(1, 11):
        entities[i] = EntityState(
            id=i,
            kind="HERO",
            navigation=NavigationComponent(position=(float(i * 10), float(i * 10))),
            combat=CombatComponent(hp=100, max_hp=100, alive=True, atk=15, def_stat=5, speed=1, readiness=100.0),
            biological=BiologicalComponent(),
            lifecycle=LifecycleComponent(age_ticks=50, max_age_ticks=2000, active=True),
            stamina=StaminaComponent(current=100.0, max_stamina=100.0),
            attributes=AttributeComponent(strength=10, agility=10),
            identity=IdentityComponent(role="WARRIOR", evolution_level=1),
            inventory=InventoryComponent(),
            strategic=StrategicComponent()
        )
    
    state = AuthoritativeState(tick=10, seed=12345, world_time=5000, entities=entities)
    
    # Construct complex update across multiple components
    e_upds = {
        1: EntityUpdate(entity_id=1, navigation=NavigationUpdate(target_set=(50.0, 50.0))),
        3: EntityUpdate(entity_id=3, attributes=AttributeUpdate(strength_delta=5)),
        4: EntityUpdate(entity_id=4, identity=IdentityUpdate(role_set="PALADIN"))
    }
    
    update = StateUpdate(entity_updates=e_upds, force_full_scan=True)
    
    # Verify patch extraction
    patches1 = extract_patches(1, e_upds[1])
    assert any(isinstance(p, NavigationPatch) for p in patches1)
    
    # Refine through pipeline
    refined_upd = AuthoritativeApplyPipeline.refine(state, update)
    
    # Authoritative systems (like combat resolution) attach combat updates to the refined update
    refined_e_upds = dict(refined_upd.entity_updates)
    combat_upd = EntityUpdate(entity_id=2, combat=CombatUpdate(hp_delta=-25), readiness_delta=15.0)
    patches2 = extract_patches(2, combat_upd)
    assert any(isinstance(p, CombatPatch) for p in patches2)
    refined_e_upds[2] = combat_upd
    refined_upd = refined_upd.replace(entity_updates=refined_e_upds)
    
    # Apply through ApplyPath
    new_state = ApplyPath.apply_generation(state, refined_upd, next_tick=11, cadence=SystemCadence())
    
    # Assert correct component transformations
    assert new_state.tick == 11
    assert new_state.entities[1].navigation.position == (10.0, 11.0)
    assert new_state.entities[2].combat.hp == 75
    assert new_state.entities[2].combat.readiness == 100.0 # 100 + 15 clamped to 100.0
    assert new_state.entities[3].attributes.strength == 15
    assert new_state.entities[4].identity.role == "PALADIN"
