"""
Social relationship and reputation tests.
- RPG-0056: social_reputation_vs_meaning
"""
import pytest
from src.core.state import AuthoritativeState
from src.core.updates import EntityUpdate, SocialUpdate, StateUpdate
from src.engine.apply import ApplyPath
from src.core.builder import V2EntityBuilder

def test_relationship_familiarity_gain():
    entity = V2EntityBuilder(entity_id=1).role(0).build()
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})
    
    # Increase familiarity with entity 99
    update = EntityUpdate(
        entity_id=1,
        social=SocialUpdate(familiarity_delta={99: 0.1})
    )
    state_upd = StateUpdate(entity_updates={1: update})
    
    new_state = ApplyPath.apply_generation(state, state_upd)
    social = new_state.entities[1].social
    
    assert social.familiarity_history[99] == 0.1

def test_relationship_trust_evidence():
    entity = V2EntityBuilder(entity_id=1).role(0).build()
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})
    
    # Increase trust with entity 99
    update = EntityUpdate(
        entity_id=1,
        social=SocialUpdate(trust_delta={99: 0.5})
    )
    state_upd = StateUpdate(entity_updates={1: update})
    
    new_state = ApplyPath.apply_generation(state, state_upd)
    social = new_state.entities[1].social
    
    assert social.trust_history[99] == 0.5

def test_relationship_debt_and_fear():
    entity = V2EntityBuilder(entity_id=1).role(0).build()
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})
    
    # Increase debt and fear with entity 99
    update = EntityUpdate(
        entity_id=1,
        social=SocialUpdate(debt_delta={99: 0.3}, fear_delta={99: 0.2})
    )
    state_upd = StateUpdate(entity_updates={1: update})
    
    new_state = ApplyPath.apply_generation(state, state_upd)
    social = new_state.entities[1].social
    
    assert social.debt_history[99] == 0.3
    assert social.fear_history[99] == 0.2

def test_public_reputation_impact():
    entity = V2EntityBuilder(entity_id=1).role(0).build()
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})
    
    # Perform heroic deed
    update = EntityUpdate(
        entity_id=1,
        social=SocialUpdate(heroism_delta=0.5)
    )
    state_upd = StateUpdate(entity_updates={1: update})
    
    new_state = ApplyPath.apply_generation(state, state_upd)
    social = new_state.entities[1].social
    
    assert social.heroism_score == 0.5
    assert social.public_reputation == 1.5 # Base 1.0 + 0.5

def test_relationship_salience_pruning():
    from src.social.relationships import RelationshipService
    entity = V2EntityBuilder(entity_id=1).role(0).build()
    
    # Add two entities: one salient, one not
    update = EntityUpdate(
        entity_id=1,
        social=SocialUpdate(
            salience_delta={10: 0.1, 20: 0.01},
            trust_delta={10: 0.5, 20: 0.5}
        )
    )
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})
    state_upd = StateUpdate(entity_updates={1: update})
    
    new_state = ApplyPath.apply_generation(state, state_upd)
    social = new_state.entities[1].social
    
    # Prune
    pruned_social = RelationshipService.prune_low_salience(social, threshold=0.05)
    
    assert 10 in pruned_social.trust_history
    assert 20 not in pruned_social.trust_history
    assert 10 in pruned_social.salience_history
    assert 20 not in pruned_social.salience_history
