import pytest
from src.api.schemas import EntityInspectionSchema, SchedulerTimelineItemSchema
from src.core.entities.entity_builder import EntityBuilder
from src.core.models.world_state import WorldState
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash
from src.platform.rng import DeterministicRNG
from src.config import SimulationConfig

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
    prop = ActionProposal(actor_id=1, verb="attack", target=2)
    
    # Apply attack
    action.apply(prop, world)
    
    # Defender should have a trace
    assert len(defender.combat.traces) > 0
    trace = defender.combat.traces[0]
    assert trace["attacker_id"] == 1
    assert "raw_damage" in trace

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
    
    # DEBUG: Check if proposal has the metadata
    print(f"PROPOSAL METADATA: {proposal.intent_metadata}")
    
    # Apply via ActionSystem
    action_sys = ActionSystem(config, rng)
    sys_ctx = SystemContext(config, world, rng, None, None, lambda x: None)
    action_sys.process_applied_actions(sys_ctx, [proposal])
    
    # Check persistence
    print(f"ENTITY GOAL SCORES: {hero.mind.decision.goal_scores}")
    assert "goal_scores" in proposal.intent_metadata, "Proposal missing goal_scores metadata"
    assert len(proposal.intent_metadata["goal_scores"]) > 0, "Goal scores dict is empty in metadata"
    assert len(hero.mind.decision.goal_scores) > 0, f"Entity goal_scores empty after application. Metadata was: {proposal.intent_metadata.get('goal_scores')}"
    assert hero.mind.decision.last_goal == proposal.intent_metadata.get("selected_goal")

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
    assert timeline[0].entity_id == 2
    assert timeline[1].entity_id == 1
