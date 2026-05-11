import pytest
from src.core.state import AuthoritativeState, CorpseState
from src.core.updates import StateUpdate
from src.engine.apply import ApplyPath

def test_corpse_decay():
    """
    Verify that corpses are removed after their decay_tick.
    Logic ID: WORLD-003 (Corpse decay after fixed duration)
    """
    corpse = CorpseState(
        id=1,
        original_entity_id=10,
        position=(0,0),
        items=[],
        decay_tick=10,
        generation=1
    )
    
    state = AuthoritativeState(
        tick=5,
        seed=42,
        entities={},
        corpses={1: corpse}
    )
    
    # Tick 6: Corpse should still be there
    next_state = ApplyPath.apply_generation(state, StateUpdate(), next_tick=6)
    assert 1 in next_state.corpses
    
    # Tick 11: Corpse should be gone
    state_at_10 = replace(state, tick=10) # Set current tick to 10
    next_state = ApplyPath.apply_generation(state_at_10, StateUpdate(), next_tick=11)
    assert 1 not in next_state.corpses

from dataclasses import replace
