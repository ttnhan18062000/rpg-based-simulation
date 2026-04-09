import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


import pytest
from src.api.schemas import EntityInspectionSchema, SchedulerTimelineItemSchema
from src.core.entities.entity_builder import EntityBuilder
from src.core.models.world_state import WorldState
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash
from src.platform.rng import DeterministicRNG
from src.config import SimulationConfig
from src.actions.base import MindUpdate

@pytest.fixture
def world():
    grid = Grid(10, 10)
    spatial = SpatialHash(cell_size=2)
    return WorldState(seed=42, grid=grid, spatial_index=spatial)

@pytest.fixture
def rng():
    return DeterministicRNG(42)

def test_stat_breakdown_service(world, rng):
    from src.api.presenters.stat_breakdown import StatBreakdownService
    
    # Create a hero with some attributes
    hero = EntityBuilder(rng, 1).kind("hero").build()
    hero.progression.attributes.str_ = 20
    
    breakdown = StatBreakdownService.get_breakdown(hero, "atk")
    
    assert breakdown.stat_name == "atk"
    assert breakdown.base_value == 5
    # Check if 'Attributes' source is present
    sources = [s.source_name for s in breakdown.sources]
    assert "Attributes" in sources

from src.core.models.vectors import Vector2

def test_combat_trace_recording(world, rng):
    from src.actions.combat import CombatAction
    from src.actions.base import ActionProposal
    
    attacker = EntityBuilder(rng, 1).kind("hero").at(Vector2(0,0)).build()
    defender = EntityBuilder(rng, 2).kind("mob").at(Vector2(1,0)).build()
    world.add_entity(attacker)
    world.add_entity(defender)
    
    action = CombatAction(SimulationConfig(), rng)
    from src.core.models.enums import ActionType
    prop = ActionProposal(actor_id=1, verb=ActionType.ATTACK, target=2)
    
    # Apply attack
    action.apply(prop, world)
    from src.systems.gameplay.action_system import ActionSystem
    ActionSystem.apply_action_state_transitions(world, SimulationConfig(), [prop], rng=rng)
    
    # Defender should have a trace
    assert len(defender.combat.traces) > 0
    trace = defender.combat.traces[0]
    assert trace.attacker_id == 1
    assert trace.details.raw_damage > 0
    assert trace.damage > 0

def test_ai_explainability_persistence(world, rng):
    from src.ai.brain import AIBrain
    from src.core.models.snapshot import Snapshot
    from src.systems.gameplay.action_system import ActionSystem
    from src.systems.infrastructure.base import SystemContext
    
    config = SimulationConfig()
    brain = AIBrain(config, rng)
    hero = EntityBuilder(rng, 1).kind("hero").at(Vector2(0,0)).build()
    hero.mind.decision.goal_committed_at = -10 # Bypass commitment lock
    world.add_entity(hero)
    
    # Force a decision
    snapshot = Snapshot.from_world(world)
    new_state, proposal = brain.decide(hero, snapshot)
    
    # DEBUG: Check if proposal has the updates
    print(f"PROPOSAL UPDATES: {proposal.updates}")
    
    # Apply via ActionSystem
    action_sys = ActionSystem(config, rng)
    sys_ctx = SystemContext(config, world, rng, None, None, lambda x: None)
    action_sys.process_applied_actions(sys_ctx, [proposal])
    
    # Check persistence
    print(f"ENTITY GOAL SCORES: {hero.mind.decision.goal_scores}")
    mind_up = next((u for u in proposal.updates if isinstance(u, MindUpdate) and u.goal_scores), None)
    assert mind_up and mind_up.goal_scores, f"Proposal missing goal_scores in any MindUpdate. Updates: {proposal.updates}"
    assert len(mind_up.goal_scores) > 0, "Goal scores dict is empty in updates"
    assert len(hero.mind.decision.goal_scores) > 0, f"Entity goal_scores empty after application. Update was: {mind_up.goal_scores}"
    assert hero.mind.decision.last_goal == mind_up.last_goal

def test_scheduler_timeline(world, rng):
    from src.api.presenters.scheduler_presenter import SchedulerPresenter
    
    e1 = EntityBuilder(rng, 1).build()
    e1.next_act_at = 10
    e2 = EntityBuilder(rng, 2).build()
    e2.next_act_at = 5
    
    world.add_entity(e1)
    world.add_entity(e2)
    
    timeline = SchedulerPresenter.get_timeline(world)
    
    # e2 (at 5) should be first
def test_behavioral_realism_api_integration(world, rng):
    from src.api.presenters.ai_presenter import AIPresenter
    from src.core.aspects.mind import PersonalityProfile, PersonalMotive, BeliefRecord, ThreatEstimate
    from src.core.models.vectors import Vector2
    
    hero = EntityBuilder(rng, 1).kind("hero").build()
    hero.mind.decision.personality = PersonalityProfile(aggression=0.8, caution=0.2)
    hero.mind.decision.motives = [PersonalMotive(motive_id="wealth_1", kind="build_wealth", priority=1.0)]
    hero.mind.perception.entity_memory[2] = BeliefRecord(
        entity_id=2, pos=Vector2(0,0), threat=ThreatEstimate(overall=0.9)
    )
    hero.mind.decision.decision_drivers = ["Aggressive nature", "Sensed danger"]
    
    explanation = AIPresenter.get_explanation(hero)
    
    # Check for Stage 1 fields in the explanation (via schemas)
    assert explanation.personality is not None
    assert explanation.personality["aggression"] == 0.8
    assert len(explanation.motives) == 1
    assert explanation.motives[0]["kind"] == "build_wealth"
    assert len(explanation.beliefs) >= 1
    assert explanation.beliefs[0]["entity_id"] == 2
    assert explanation.beliefs[0]["threat"]["overall"] == 0.9
    assert "Aggressive nature" in explanation.decision_drivers
