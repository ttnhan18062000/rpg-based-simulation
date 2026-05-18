import pytest
from src_legacy.core.state import AuthoritativeState, EntityState, InventoryComponent, NavigationComponent, IdentityComponent, CombatComponent
from src_legacy.core.enums import EntityRole
from src_legacy.core.movement_modes import MovementMode
from src_legacy.engine.movement import MovementSystem

@pytest.fixture
def yield_state():
    # Hero at (0,0) wants to move to (1,0)
    hero = EntityState(
        id=1,
        kind="HERO",
        position=(0, 0),
        identity=IdentityComponent(role=EntityRole.HERO),
        navigation=NavigationComponent(target=(1, 0), mode=MovementMode.PURSUE),
        combat=CombatComponent(hp=100, max_hp=100)
    )
    
    # Villager at (1,0)
    villager = EntityState(
        id=2,
        kind="VILLAGER",
        position=(1, 0),
        identity=IdentityComponent(role=EntityRole.CITIZEN),
        navigation=NavigationComponent(mode=MovementMode.WANDER),
        combat=CombatComponent(hp=100, max_hp=100)
    )
    
    return AuthoritativeState(
        tick=1,
        seed=42,
        entities={1: hero, 2: villager},
        terrain={(0,0): "FLOOR", (1,0): "FLOOR", (1,1): "FLOOR", (0, 1): "WALL", (0, -1): "WALL"}
    )

def test_hero_forces_villager_to_yield(yield_state):
    # Run MovementSystem
    hero = yield_state.entities[1]
    updates = MovementSystem.resolve_move(yield_state, hero, (1, 0))
    
    # Check updates
    assert 1 in updates
    assert 2 in updates # Villager should have a yield update
    
    hero_upd = updates[1]
    villager_upd = updates[2]
    
    assert hero_upd.new_position == (1, 0)
    assert villager_upd.new_position is not None
    assert villager_upd.new_position != (1, 0)
    assert villager_upd.navigation.failure_reason == "YIELDED"
    
    # Apply updates
    from src_legacy.engine.apply import ApplyPath
    from src_legacy.core.updates import StateUpdate
    state_upd = StateUpdate(entity_updates=updates)
    final_state = ApplyPath.apply_generation(yield_state, state_upd)
    
    assert final_state.entities[1].position == (1, 0)
    assert final_state.entities[2].position != (1, 0)
    assert final_state.entities[2].position != (0, 0) # Should not yield to mover's start tile
