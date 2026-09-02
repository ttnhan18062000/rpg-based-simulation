import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, StatusEffectState
from src.core.updates import StateUpdate, EntityUpdate
from src.systems.strategic import StrategicIntelligenceSystem
from src.core.enums import ReasonCode
from src.core.builder import V2EntityBuilder

def test_frozen_actor_skips_strategic_intent(frozen_actor_state):
    """
    Law: Incapacitated (frozen) actors must not evaluate strategic intent.
    """
    state, actor_id = frozen_actor_state
    actor = state.entities[actor_id]
    
    # 1. Ensure the actor is processing this tick (staggered tick match)
    # Staggering rule: (state.tick + entity.id) % 10 == 0
    new_tick = (10 - (actor_id % 10)) % 10
    state = replace(state, tick=new_tick)
    
    # 2. Mark as frozen
    actor = replace(actor, combat=replace(actor.combat,
        status_effects=[StatusEffectState(kind="frozen", source="test_fixture", magnitude=1.0, expires_tick=-1)]))
    state = replace(state, entities={actor_id: actor})
    
    # 3. Evaluate strategic intent
    update = StrategicIntelligenceSystem.evaluate_strategic_intent(state, actor)
    
    # 4. Verify no changes proposed (early exit)
    assert not update.directives_add_or_update
    assert not update.projects_add_or_update
    assert not update.concerns_add_or_update

def test_stunned_actor_skips_strategic_concerns(frozen_actor_state):
    """
    Law: Incapacitated (stunned) actors must not evaluate strategic concerns.
    """
    state, actor_id = frozen_actor_state
    actor = state.entities[actor_id]
    
    # 1. Ensure the actor is processing this tick
    new_tick = (10 - (actor_id % 10)) % 10
    state = replace(state, tick=new_tick)
    
    # 2. Mark as stunned
    actor = replace(actor, combat=replace(actor.combat,
        status_effects=[StatusEffectState(kind="stunned", source="test_fixture", magnitude=1.0, expires_tick=-1)]))
    state = replace(state, entities={actor_id: actor})
    
    # 3. Evaluate all concerns
    update = StateUpdate()
    update = StrategicIntelligenceSystem.evaluate_all_concerns(state, update)
    
    # 4. Verify the actor's concerns were not updated
    ent_upd = update.entity_updates.get(actor_id)
    if ent_upd and ent_upd.strategic:
        assert not ent_upd.strategic.concerns_add_or_update

def test_staggered_frequency_distribution(frozen_actor_state):
    """
    Law: Strategic evaluation must follow a strict 10-tick staggered frequency.
    """
    state, actor_id = frozen_actor_state
    actor = state.entities[actor_id]
    
    # Test ticks 0-19
    for t in range(20):
        state = replace(state, tick=t)
        update = StrategicIntelligenceSystem.evaluate_strategic_intent(state, actor)
        
        should_process = (t + actor_id) % 10 == 0
        if not should_process:
            # If not processing, it returns an empty StrategicUpdate
            assert not update.directives_add_or_update
            assert not update.projects_add_or_update

@pytest.fixture
def frozen_actor_state():
    actor_id = 42
    actor = (V2EntityBuilder(actor_id)
             .kind("hero")
             .location(0.0, 0.0)
             .build())
    
    state = AuthoritativeState(
        seed=123,
        tick=0,
        entities={actor_id: actor}
    )
    return state, actor_id
