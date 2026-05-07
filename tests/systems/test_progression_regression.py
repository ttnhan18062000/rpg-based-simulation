import pytest
from dataclasses import replace
from src.core.state import (
    AuthoritativeState, EntityState, IdentityComponent, 
    CombatComponent, AttributeComponent, TaskComponent,
    AptitudeComponent, BiologicalComponent
)
from src.core.updates import StateUpdate, EntityUpdate, RewardUpdate, IdentityUpdate
from src.engine.evolution import EvolutionSystem
from src.engine.domain_logic import SimulationDomainLogic

def create_mock_entity(e_id, pos=(0,0)):
    from src.core.builder import V2EntityBuilder
    return (V2EntityBuilder(e_id)
        .kind("HERO")
        .location(pos[0], pos[1])
        .identity(evolution_level=1, evolution_points=0, unspent_ap=0)
        .attributes(strength=10, vitality=10)
        .aptitude(str_apt=1.1, vit_apt=1.2)
        .combat(hp=100, max_hp=100)
        .combat(alive=True)
        .combat(readiness=100.0)
        .build())

def test_evolution_trigger_and_stat_boost():
    """Verify that reaching XP threshold triggers evolution and stat increases."""
    hero = create_mock_entity(1)
    # Give enough XP for Level 10 (Threshold ~11102)
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, reward=RewardUpdate(xp_gain=12000))})
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero})
    
    result = EvolutionSystem.evaluate(state, update)
    
    hero_up = result.entity_updates[1]
    assert hero_up.kind_set == "LEGEND_HERO"
    assert hero_up.identity.evolution_level_set == 10
    # Level 2..10 (9 levels) = 45 AP. Milestones at 5 and 10 = 10 AP. Total 55.
    assert hero_up.identity.unspent_ap_delta == 55

def test_attribute_allocation():
    """Verify that spending AP increases attributes and derived stats."""
    hero = create_mock_entity(1)
    hero = replace(hero, identity=replace(hero.identity, unspent_ap=5))
    
    # Action: ALLOCATE_AP
    payload = {"action": "ALLOCATE_AP", "attribute": "strength", "amount": 3}
    
    # This should be handled by SimulationDomainLogic.execute_action
    result = SimulationDomainLogic.execute_action(hero, payload=payload, current_tick=1)
    
    hero_up = result[1]
    assert hero_up.identity.unspent_ap_delta == -3
    assert hero_up.attributes.strength_delta == 3
    # Derived combat stat boost? (e.g. Strength increases ATK)
    # In a clean system, AttributeComponent.strength_delta should be committed, 
    # and then another system calculates derived stats.
    # OR SimulationDomainLogic does it immediately.
    assert hero_up.combat.atk_delta > 0
