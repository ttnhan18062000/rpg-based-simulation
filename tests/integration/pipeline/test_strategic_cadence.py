import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate, EntityUpdate, StrategicUpdate
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.cadence import SystemCadence
from src.core.builder import V2EntityBuilder

@pytest.fixture
def base_state():
    return AuthoritativeState(
        seed=42,
        tick=0,
        entities={},
        regions={}
    )

def test_strategic_cadence_gating(base_state):
    # Setup: 1 entity
    builder = V2EntityBuilder(1)
    entity = builder.build()
    state = replace(base_state, tick=1, entities={1: entity})
    
    # Custom cadence: strategic intelligence every 10 ticks
    cadence = SystemCadence(strategic_intelligence=10)
    
    # Tick 1: Strategic Intelligence should NOT run (1 % 10 != 0)
    # Actually, should_run(1, 1, 10) -> (1 + 1) % 10 == 2 != 0
    # Trigger dirty tracking by adding a dummy strategic update
    from src.core.updates import StrategicUpdate
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, strategic=StrategicUpdate())})
    
    # We'll mock StrategicIntelligenceSystem to see if it's called
    with mock.patch("src.systems.strategic_systems.intelligence.StrategicIntelligenceSystem.evaluate_strategic_intent") as mock_eval:
        mock_eval.return_value = StrategicUpdate()
        
        # Run pipeline
        AuthoritativeApplyPipeline.refine(state, update, cadence=cadence)
        assert mock_eval.call_count == 0
        
        # Tick 9: (9 + 1) % 10 == 0 -> SHOULD run
        state_tick_9 = replace(state, tick=9)
        AuthoritativeApplyPipeline.refine(state_tick_9, update, cadence=cadence)
        assert mock_eval.call_count == 1

def test_town_resolution_cadence_gating(base_state):
    # Setup
    state = replace(base_state, tick=1)
    update = StateUpdate()
    
    cadence = SystemCadence(town_resolution=5)
    
    with mock.patch("src.engine.town_resolution.TownResolutionSystem.resolve") as mock_resolve:
        mock_resolve.side_effect = lambda s, u, **kwargs: u
        
        # Tick 1: should not run
        AuthoritativeApplyPipeline.refine(state, update, cadence=cadence)
        assert mock_resolve.call_count == 0
        
        # Tick 5: should run
        state_tick_5 = replace(state, tick=5)
        AuthoritativeApplyPipeline.refine(state_tick_5, update, cadence=cadence)
        assert mock_resolve.call_count == 1

def test_world_dynamics_cadence_gating(base_state):
    state = replace(base_state, tick=1)
    update = StateUpdate()
    
    cadence = SystemCadence(world_dynamics=50)
    
    # We need to mock things inside resolve_dynamics or the whole thing
    # Actually, we want to see if section 3 is skipped.
    # But since it's an internal block, we can't easily mock it unless we mock CalamityService etc.
    
    with mock.patch("src.world.calamity.CalamityService.process_world_dynamics") as mock_calamity:
        from src.core.updates import StateUpdate as NewStateUpdate
        mock_calamity.return_value = NewStateUpdate()
        
        # Tick 1: Section 3 should be skipped
        AuthoritativeApplyPipeline.refine(state, update, cadence=cadence)
        assert mock_calamity.call_count == 0
        
        # Tick 50: Section 3 should run
        state_tick_50 = replace(state, tick=50)
        AuthoritativeApplyPipeline.refine(state_tick_50, update, cadence=cadence)
        assert mock_calamity.call_count == 1

def test_building_sabotage_cadence_gating(base_state):
    state = replace(base_state, tick=1)
    update = StateUpdate()
    
    cadence = SystemCadence(building_sabotage=100)
    
    with mock.patch("src.engine.sabotage.BuildingSabotageSystem.resolve") as mock_sabotage:
        mock_sabotage.side_effect = lambda s, u, **kwargs: u
        
        # Tick 1: should not run
        AuthoritativeApplyPipeline.refine(state, update, cadence=cadence)
        assert mock_sabotage.call_count == 0
        
        # Tick 100: should run
        state_tick_100 = replace(state, tick=100)
        AuthoritativeApplyPipeline.refine(state_tick_100, update, cadence=cadence)
        assert mock_sabotage.call_count == 1

import unittest.mock as mock
