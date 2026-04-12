import pytest
from unittest.mock import MagicMock
from src.core.entities.entity import Entity
from src.core.aspects.mind import (
    MindAspect, RoutineState, PersonalityProfile, EmotionState, 
    NavigationState, SocialStance, PerceptionMemory, NarrativeMemory,
    DecisionState
)
from src.core.aspects.identity import IdentityAspect
from src.core.aspects.spatial import SpatialAspect
from src.core.aspects.combat import CombatAspect
from src.core.aspects.progression import ProgressionAspect
from src.core.aspects.interaction import InteractionAspect
from src.core.aspects.inventory import InventoryAspect
from src.core.models.enums import GoalType, AIState, ActionType, EntityRole
from src.core.models.vectors import Vector2
from src.ai.brain import AIBrain
from src.ai.states.base import AIContext
from src.config import SimulationConfig
from src.actions.base import RoutineUpdate, MindUpdate

def create_test_entity(id: int = 1):
    mind = MindAspect(
        decision=DecisionState(
            personality=PersonalityProfile(aggression=0.5, greed=0.5, caution=0.5, curiosity=0.5)
        ),
        perception=PerceptionMemory(),
        emotion=EmotionState(),
        navigation=NavigationState(),
        narrative=NarrativeMemory(),
        routine=RoutineState(sleep_debt=0.0, hunger_level=0.0),
        social=SocialStance()
    )
    mock_storage = MagicMock()
    mock_storage.upgrade_cost.return_value = None
    inventory = InventoryAspect(home_storage=mock_storage)
    
    return Entity(
        id=id, 
        kind="hero",
        identity=IdentityAspect(display_name="Test Actor", role=EntityRole.HERO),
        spatial=SpatialAspect(pos=Vector2(10, 10), region_id="town"),
        combat=CombatAspect(hp=100, max_hp=100),
        progression=ProgressionAspect(stamina=100, max_stamina=100),
        mind=mind,
        interaction=InteractionAspect(),
        inventory=inventory
    )

@pytest.fixture
def routine_entity():
    return create_test_entity()

@pytest.fixture
def ai_brain():
    config = SimulationConfig()
    rng = MagicMock() 
    return AIBrain(config=config, rng=rng)

def test_biological_utility_biasing(ai_brain, routine_entity):
    routine_entity.mind.routine.sleep_debt = 0.9
    routine_entity.mind.routine.hunger_level = 0.9
    
    ctx = AIContext(
        actor=routine_entity,
        snapshot=MagicMock(),
        config=SimulationConfig(),
        rng=MagicMock(),
        faction_reg=MagicMock()
    )
    ctx.snapshot.tick = 100
    ctx.snapshot.hour = 12
    routine_entity.mind.routine.disrupted_until_tick = 0
    routine_entity.mind.emotion.panic = 0.0
    routine_entity.mind.routine_profiles = []
    routine_entity.mind.place_attachments = []
    
    # Night hour for Explore bias
    ctx.snapshot.hour = 2
    updates = []
    ai_brain._memory_appraisal_phase(ctx, updates, {})
    mind_update = next((u for u in updates if isinstance(u, MindUpdate) and u.motive_utility_biases is not None), None)
    
    assert mind_update.motive_utility_biases[GoalType.EXPLORE] < 1.0
    
    assert any(d.label == "Exhausted" for d in mind_update.driver_details)
    assert any(d.label == "Starving" for d in mind_update.driver_details)

def test_inn_visit_leads_to_sleeping(routine_entity):
    from src.ai.states.town import VisitInnHandler
    from src.actions.base import RoutineUpdate
    
    routine_entity.mind.routine.sleep_debt = 0.8
    handler = VisitInnHandler()
    
    mock_inn = MagicMock()
    mock_inn.building_type = "inn"
    mock_inn.spatial.pos = Vector2(10, 10)
    
    snapshot = MagicMock()
    snapshot.buildings = [mock_inn]
    snapshot.tick = 1
    
    ctx = AIContext(
        actor=routine_entity,
        snapshot=snapshot,
        config=SimulationConfig(),
        rng=MagicMock(),
        faction_reg=MagicMock()
    )
    
    new_state, proposal = handler.handle(ctx)
    
    assert new_state == AIState.SLEEPING
    assert proposal.verb == ActionType.SLEEP
    assert any(isinstance(u, RoutineUpdate) and u.is_sleeping for u in proposal.updates)

def test_home_visit_leads_to_eating(routine_entity):
    from src.ai.states.town import VisitHomeHandler
    from src.actions.base import RoutineUpdate
    
    routine_entity.mind.routine.hunger_level = 0.8
    routine_entity.spatial.home_pos = Vector2(10, 10)
    handler = VisitHomeHandler()
    
    ctx = AIContext(
        actor=routine_entity,
        snapshot=MagicMock(),
        config=SimulationConfig(),
        rng=MagicMock(),
        faction_reg=MagicMock()
    )
    ctx.snapshot.tick = 1
    
    new_state, proposal = handler.handle(ctx)
    
    assert new_state == AIState.EATING
    assert proposal.verb == ActionType.EAT
    
    eat_update = next(u for u in proposal.updates if isinstance(u, RoutineUpdate))
    assert eat_update.hunger_delta < 0

def test_sleeping_recovery_cycle(routine_entity):
    from src.ai.states.routine import SleepingHandler
    from src.actions.base import RoutineUpdate
    
    handler = SleepingHandler()
    
    ctx = AIContext(
        actor=routine_entity,
        snapshot=MagicMock(),
        config=SimulationConfig(),
        rng=MagicMock(),
        faction_reg=MagicMock()
    )
    ctx.snapshot.tick = 1
    
    # Case 1: Still tired
    routine_entity.mind.routine.sleep_debt = 0.5
    new_state, proposal = handler.handle(ctx)
    assert new_state == AIState.SLEEPING
    
    # Case 2: Fully rested
    routine_entity.mind.routine.sleep_debt = 0.02
    new_state, proposal = handler.handle(ctx)
    assert new_state == AIState.IDLE
    assert any(isinstance(u, RoutineUpdate) and u.is_sleeping == False for u in proposal.updates)
