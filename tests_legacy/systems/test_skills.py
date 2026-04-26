import pytest
from src_legacy.core.state import AuthoritativeState, EntityState, IdentityComponent
from src_legacy.core.updates import StateUpdate, EntityUpdate, IdentityUpdate
from src_legacy.systems.skills import SkillSystem

def test_skill_unlocks_on_level_up():
    """
    Phase 8: Verify that entities automatically unlock skills when they meet level requirements.
    """
    # 1. Setup Entity (Level 4, WARRIOR)
    identity = IdentityComponent(
        evolution_level=4, 
        class_id="WARRIOR",
        learned_skills={"basic_attack"}
    )
    entity = EntityState(
        id=1, kind="HERO", position=(0.0, 0.0),
        identity=identity
    )
    state = AuthoritativeState(tick=0, seed=0, entities={1: entity})
    
    # 2. Simulate level up to Level 5
    # From Registry, "heavy_strike" requires Level 5 and class WARRIOR
    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                identity=IdentityUpdate(
                    evolution_level_set=5
                )
            )
        }
    )
    
    # 3. Process Skill Unlocks
    refined_update = SkillSystem.process_skill_unlocks(state, update)
    
    # 4. Assert
    # The IdentityUpdate should now contain "heavy_strike" in skills_learned
    id_upd = refined_update.entity_updates[1].identity
    assert id_upd is not None
    assert "heavy_strike" in id_upd.skills_learned
    assert "fireball" not in id_upd.skills_learned # Wrong class
