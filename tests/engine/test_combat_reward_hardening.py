
import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, IdentityComponent, CombatComponent, ResourceNodeState, ItemStack, StrategicComponent, InventoryComponent, StaminaComponent, BiologicalComponent, LifecycleComponent, AptitudeComponent, SocialComponent, NavigationComponent, PersonalityComponent, TaskComponent
from src.core.enums import EntityRole
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.apply import ApplyPath
from src.core.updates import StateUpdate, EntityUpdate, InteractionUpdate, ResourceTransferIntent, NavigationUpdate, TaskUpdate

def create_mock_entity(id, faction="HERO_FACTION", role=EntityRole.HERO, pos=(0,0), hp=100, readiness=100.0, evolution_level=1):
    return EntityState(
        id=id,
        kind="ACTOR",
        position=pos,
        identity=IdentityComponent(faction=faction, role=role, evolution_level=evolution_level),
        combat=CombatComponent(hp=hp, max_hp=100, atk=100, range=1, alive=hp > 0), # High attack to ensure kill
        readiness=readiness,
        active=True,
        inventory=InventoryComponent(max_slots=10, max_weight=100.0, gold=0),
        stamina=StaminaComponent(current=100.0),
        strategic=StrategicComponent(),
        biological=BiologicalComponent(),
        lifecycle=LifecycleComponent(),
        aptitude=AptitudeComponent(),
        social=SocialComponent(),
        navigation=NavigationComponent(),
        task=TaskComponent()
    )

def test_combat_reward_consolidation_xp_gold():
    """
    RPG-1699: unified_reward_consolidation
    P0.4: Verify that combat rewards flow through ResourceTransferIntent and NOT CombatUpdate fields.
    """
    attacker = create_mock_entity(1, hp=100)
    # Monster with level 5
    monster = create_mock_entity(2, faction="MONSTER_FACTION", role=EntityRole.MONSTER, hp=10, evolution_level=5)
    
    state = AuthoritativeState(tick=1, seed=1, entities={1: attacker, 2: monster})
    
    # Hero attacks Monster
    update = StateUpdate(entity_updates={
        1: EntityUpdate(
            entity_id=1, 
            task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "ATTACK", "target_id": 2})
        )
    })
    
    # 1. Refine the update
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    # 2. Check Attacker's update
    attacker_upd = refined.entity_updates[1]
    
    # XP and Gold gain should NOT be in CombatUpdate (AttributeError if we try to access them)
    with pytest.raises(AttributeError):
        _ = attacker_upd.combat.xp_gain
    with pytest.raises(AttributeError):
        _ = attacker_upd.combat.gold_gain
        
    # Rewards should have been processed into the reward component
    assert attacker_upd.reward is not None
    assert attacker_upd.reward.xp_gain == 0 # Consumed by EvolutionSystem
    assert attacker_upd.inventory.gold_delta == 25
    
    # Check that they came from a successful COMBAT intent
    assert any(res.source_kind == "COMBAT" and res.accepted for res in attacker_upd.intent_results)
    
    # 3. Apply the generation
    final_state = ApplyPath.apply_generation(state, refined)
    
    # 4. Verify results
    final_attacker = final_state.entities[1]
    assert final_attacker.inventory.gold == 25
    assert final_attacker.identity.evolution_points == 50
    assert final_state.entities[2].combat.alive is False

def test_skill_reward_consolidation():
    """
    Verify that skill usage also consolidates rewards into intents.
    """
    attacker = create_mock_entity(1, hp=100)
    attacker = replace(attacker, identity=replace(attacker.identity, learned_skills={"power_strike"}))
    monster = create_mock_entity(2, faction="MONSTER_FACTION", role=EntityRole.MONSTER, hp=10, evolution_level=2)
    
    state = AuthoritativeState(tick=1, seed=1, entities={1: attacker, 2: monster})
    
    update = StateUpdate(entity_updates={
        1: EntityUpdate(
            entity_id=1, 
            task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "SKILL", "skill_id": "power_strike", "target_id": 2})
        )
    })
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    attacker_upd = refined.entity_updates[1]
    
    # Check processed rewards
    assert attacker_upd.reward is not None
    assert attacker_upd.reward.xp_gain == 0 # Consumed by EvolutionSystem
    assert any(res.source_kind == "COMBAT" and res.accepted for res in attacker_upd.intent_results)
    
    final_state = ApplyPath.apply_generation(state, refined)
    assert final_state.entities[1].identity.evolution_points == 20
