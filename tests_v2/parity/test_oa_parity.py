import pytest
from src_v2.core.state import AuthoritativeState, EntityState, IdentityComponent, SocialComponent
from src_v2.engine.movement import MovementSystem
from src_v2.engine.apply import ApplyPath
from src_v2.core.updates import StateUpdate

def test_oa_triggered_on_disengagement():
    """
    Parity Test: LEG-RPG-099 / test_oa_triggered_on_disengagement
    Verify that moving while adjacent to a hostile entity triggers an Opportunity Attack.
    """
    # 1. Setup Initial State
    # Entity 1 (Hero) is at (0,0)
    # Entity 2 (Enemy) is at (1,0)
    hero = EntityState(
        id=1, kind="hero", position=(0.0, 0.0),
        identity=IdentityComponent(faction=1)
    )
    enemy = EntityState(
        id=2, kind="enemy", position=(1.0, 0.0),
        identity=IdentityComponent(faction=2)
    )
    
    state = AuthoritativeState(
        tick=1, seed=42,
        entities={1: hero, 2: enemy}
    )
    
    # 2. Hero intends to move to (0,1) - still adjacent to enemy but disengaging from the current tile
    # Wait, in the simplified P0, any move from an engaged tile triggers an OA.
    target_pos = (0.0, 1.0)
    
    # 3. Resolve the move
    hero_update = MovementSystem.resolve_move(state, hero, target_pos)
    
    # 4. Verify OA trigger
    assert hero_update.combat is not None
    assert hero_update.combat.is_opportunity_attack is True
    assert hero_update.combat.attacker_id == 2
    
    # 5. Apply the update and verify damage
    new_hero_state = ApplyPath._apply_entity_update(hero, hero_update)
    assert new_hero_state.properties["total_damage_taken"] == 5.0
    assert new_hero_state.properties["last_attacker_id"] == 2

def test_no_oa_if_no_hostiles():
    """
    Verify that moving while NOT engaged does NOT trigger an OA.
    """
    hero = EntityState(
        id=1, kind="hero", position=(0.0, 0.0),
        identity=IdentityComponent(faction=1)
    )
    # Friend is adjacent but in same faction
    friend = EntityState(
        id=2, kind="hero", position=(1.0, 0.0),
        identity=IdentityComponent(faction=1)
    )
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: friend})
    hero_update = MovementSystem.resolve_move(state, hero, (0.0, 1.0))
    
    assert hero_update.combat is None
