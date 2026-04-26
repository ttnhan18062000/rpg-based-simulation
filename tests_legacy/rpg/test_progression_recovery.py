import pytest
from src_legacy.core.state import AuthoritativeState, EntityState, IdentityComponent, AttributeComponent
from src_legacy.systems.progression import ProgressionSystem
from src_legacy.core.updates import StateUpdate, EntityUpdate, RewardUpdate, IdentityUpdate

def test_xp_gain_and_level_up():
    """
    Law: XP gain must lead to level up and attribute growth.
    """
    # 1. Setup: Level 1 entity with 0 points
    entity = EntityState(
        id=1, kind="HERO", position=(0,0),
        identity=IdentityComponent(evolution_level=1, evolution_points=0),
        attributes=AttributeComponent(strength=10, vitality=10)
    )
    
    state = AuthoritativeState(tick=10, seed=1, entities={1: entity})
    
    # 2. Grant 120 XP (enough for level 1 -> 2 threshold which is 100)
    upd = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, reward=RewardUpdate(xp_gain=120))
    })
    
    # Resolve rewards (XP -> points)
    upd_resolved = ProgressionSystem.resolve_rewards(state, upd)
    
    ent_upd = upd_resolved.entity_updates[1]
    assert ent_upd.identity.evolution_points_delta == 120
    assert ent_upd.reward is None
    
    # Process progression (level up)
    upd_leveled = ProgressionSystem.process_progression(state, upd_resolved)
    
    ent_upd_final = upd_leveled.entity_updates[1]
    # Level 1 -> 2 consumes 100 points. Remaining points: 120 - 100 = 20.
    assert ent_upd_final.identity.evolution_level_set == 2
    assert ent_upd_final.identity.evolution_points_delta == 20
    
    # Check attributes (Auto-invested 5 AP)
    # HERO auto-invest: STR+2, VIT+2, AGI+1
    assert ent_upd_final.attributes.strength_delta == 2
    assert ent_upd_final.attributes.vitality_delta == 2
    assert ent_upd_final.attributes.agility_delta == 1
    # AP consumed
    assert ent_upd_final.identity.unspent_ap_delta == 0
