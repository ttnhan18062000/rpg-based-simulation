import pytest
from src.core.models.world_state import WorldState
from src.config import SimulationConfig
from src.core.models.vectors import Vector2
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash
from src.core.faction import FactionRegistry
from src.core.logic.knowledge_propagation import KnowledgePropagationService
from src.systems.gameplay.action_system import ActionSystem
from src.api.presenters.ai_presenter import AIPresenter
from src.core.models.enums import AIState, ActionType, InterpretedLifeEventKind
from src.core.logic.event_interpreter import EventInterpreterService
from src.core.logic.social_state_applicator import SocialStateApplicator
from src.actions.base import ActionProposal
from src.systems.rng import DeterministicRNG
from src.core.entities.entity import Entity

@pytest.fixture
def basic_world():
    config = SimulationConfig()
    width, height = 20, 20
    grid = Grid(width=width, height=height, tiles=bytearray(width * height))
    spatial_index = SpatialHash(cell_size=4)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial_index)
    world.tick = 100
    return world, config

@pytest.mark.integration
def test_proximity_gossip_propagation(basic_world):
    world, config = basic_world
    
    # 1. Setup: 3 entities
    # A (sharer), B (recipient), C (target of gossip)
    a = Entity(id=1, kind="hero")
    a.spatial.pos = Vector2(x=5, y=5)
    
    b = Entity(id=2, kind="hero")
    b.spatial.pos = Vector2(x=6, y=5) # Nearby
    
    c = Entity(id=3, kind="hero")
    c.spatial.pos = Vector2(x=15, y=15) # Far away
    
    world.add_entity(a)
    world.add_entity(b)
    world.add_entity(c)
    
    # Enable combat aspect so alive check passes
    a.combat.hp = 100
    b.combat.hp = 100
    c.combat.hp = 100
    
    # 2. Give A knowledge of C
    from src.ai.beliefs import BeliefService
    a_belief_c = BeliefService.refresh_belief_from_observation(a, c, 100)
    a.mind.perception.entity_memory[c.id] = a_belief_c
    
    # 3. Trigger gossip via ActionSystem
    updates = []
    ActionSystem._process_proximity_gossip(world, a, updates)
    
    # Find PerceptionUpdate for B
    up_for_b = next((u for u in updates if u.target_id == b.id), None)
    assert up_for_b is not None, "B should receive a perception update from A"
    assert c.id in up_for_b.entity_memory, "Update should contain knowledge of C"
    
    # Apply update to B
    proposal = ActionProposal(actor_id=b.id, verb=ActionType.REST)
    ActionSystem._apply_updates(world, b, [up_for_b], proposal)
    
    # Verify B has indirect knowledge of C
    b_belief_c = b.mind.perception.entity_memory.get(c.id)
    assert b_belief_c is not None
    assert b_belief_c.knowledge_source == "indirect"
    assert b_belief_c.directness < 1.0

@pytest.mark.integration
def test_reputation_penalty_on_trust_gain(basic_world):
    world, config = basic_world
    
    # A (betrayer), B (observer)
    a = Entity(id=1, kind="hero")
    a.identity.reputation.reputation_tags.append("Ally-Slayer")
    
    b = Entity(id=2, kind="hero")
    
    world.add_entity(a)
    world.add_entity(b)
    
    # Create an event that normally grants trust
    from src.core.models.life_events import InterpretedLifeEvent
    event = InterpretedLifeEvent(
        event_id="test-val",
        kind=InterpretedLifeEventKind.AVENGED_ALLY,
        tick=100,
        actor_id=a.id,
        relationship_deltas={b.id: {"trust": 0.5}},
        subject_ids=[b.id]
    )
    
    # Interpret (modifiers should trigger here)
    EventInterpreterService._apply_reputation_modifiers(a, event)
    
    # Trust delta should be halfed
    assert event.relationship_deltas[b.id]["trust"] == 0.25

@pytest.mark.integration
def test_narrative_explanation_presenter(basic_world):
    world, config = basic_world
    
    a = Entity(id=1, kind="hero")
    a.identity.display_name = "Arthas"
    
    b = Entity(id=2, kind="hero")
    b.identity.display_name = "Uther"
    
    world.add_entity(a)
    world.add_entity(b)
    
    # Presenter needs world for name resolution
    # In full system, entity.world is usually set or passed.
    # AIPresenter.get_explanation(entity) uses entity.world.get_entity(...)
    a.world = world 
    
    # Add a dramatic turning point to A
    from src.core.models.life_events import TurningPointRecord
    from src.core.models.enums import TurningPointKind
    tp = TurningPointRecord(
        event_id="tp1",
        kind=TurningPointKind.BETRAYAL,
        tick=100,
        involved_entity_ids=[b.id],
        summary_tag="Stratholme",
        emotional_impact=9.0,
        salience_score=10.0,
        still_salient=True
    )
    a.mind.narrative.turning_points.append(tp)
    
    # Get explanation
    explanation = AIPresenter.get_explanation(a)
    
    # Check for presence of the narrative impact
    assert any("Betrayal" in s and "Uther" in s for s in explanation.narrative_impacts)
