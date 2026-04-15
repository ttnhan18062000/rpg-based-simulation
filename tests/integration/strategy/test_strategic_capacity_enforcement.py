import pytest
from src.core.models.world_state import WorldState
from src.core.entities.entity import Entity
from src.core.models.snapshot import Snapshot
from src.core.models.strategy import (
    CognitionCapacityProfile, 
    CandidateZoneRecord, SocialContractRecord, RecruitmentOfferRecord,
    StrategicStatus, ProjectRecord, ProjectKind,
    ConcernRecord, ConcernKind, ContractKind, OfferStatus
)
from src.actions.base import StrategicUpdate
from src.ai.brain import AIBrain
from src.platform.rng import DeterministicRNG
from src.config import SimulationConfig

def create_test_profile(**kwargs):
    """Helper to create a full CognitionCapacityProfile with defaults to satisfy Pydantic validation."""
    base = {
        "planning_budget": 5, "judgment_stability": 0.5,
        "evidence_quality": 0.5, "social_bandwidth": 5, "detour_depth_limit": 3,
        "active_slice_limit": 5, "concern_intake_limit": 3, "lead_retention_limit": 5,
        "candidate_zone_limit": 3, "ally_evaluation_limit": 5, "blocker_resolution_patience": 0.5,
        "resume_reliability": 0.5, "interruption_resistance": 0.5, "abandonment_threshold_mod": 1.0,
        "contradiction_sensitivity": 0.5, "source_trust_learning_rate": 0.5
    }
    base.update(kwargs)
    return CognitionCapacityProfile(**base)

@pytest.fixture
def world():
    from src.core.world.grid import Grid
    from src.platform.spatial_hash import SpatialHash
    grid = Grid(100, 100)
    spatial = SpatialHash(cell_size=10)
    return WorldState(seed=42, grid=grid, spatial_index=spatial)

@pytest.fixture
def brain():
    return AIBrain(SimulationConfig(), DeterministicRNG(0))

def test_budget_enforcement_truncation(brain, world):
    """Verify that candidate_zone_limit and ally_evaluation_limit correctly truncate the pool."""
    hero = Entity(id=1, kind="hero")
    world.add_entity(hero)
    
    # 1. Setup profile with tiny limits
    profile = create_test_profile(
        candidate_zone_limit=2,
        ally_evaluation_limit=2,
        planning_budget=10
    )
    hero.mind.strategic.last_capacity_profile = profile
    
    # 2. Inject excessive candidates
    for i in range(5):
        # Zones score on confidence
        hero.mind.strategic.candidate_zones.append(CandidateZoneRecord(zone_id=f"z{i}", confidence=0.2 * i))
    
    for i in range(5):
        # Offers score on priority (not in model, so defaults to 1.0) and status
        hero.mind.strategic.offers.append(RecruitmentOfferRecord(
            offer_id=f"o{i}", recruiter_id=1, candidate_id=2, 
            contract_kind=ContractKind.EXPEDITION, project_id="p1",
            status=OfferStatus.PENDING
        ))
        
    snapshot = Snapshot.from_world(world)
    state, proposal = brain.decide(hero, snapshot)
    
    strat_up = next((u for u in proposal.updates if isinstance(u, StrategicUpdate)), None)
    assert strat_up is not None
    
    # 3. Verify counts
    assert strat_up.candidate_zones_used <= 2
    assert strat_up.ally_evaluations_used <= 2
    
    # Verify dropped count
    assert strat_up.dropped_candidates_count >= 6

def test_source_trust_durability(brain, world):
    """Verify that source_trust_updates are applied and affect the next appraisal cycle."""
    hero = Entity(id=1, kind="hero")
    world.add_entity(hero)
    
    from src.actions.base import StrategicUpdate
    
    # 1. Initial State: Source "A" is neutral
    hero.mind.strategic.source_trust = {"source_A": 0.5}
    
    # 2. Simulate a StrategicUpdate that downgrades source_A
    # The brain produces absolute values for recalibrated trust
    update = StrategicUpdate(source_trust_updates={"source_A": 0.1}) 
    
    # Use ActionSystem to apply it
    from src.systems.gameplay.action_system import ActionSystem
    from src.actions.base import ActionProposal
    from src.core.models.enums import ActionType
    from src.platform.rng import DeterministicRNG
    
    proposal = ActionProposal(actor_id=hero.id, verb=ActionType.REST, updates=[update])
    # ActionSystem.apply_action_state_transitions(world, config, applied, rng)
    ActionSystem.apply_action_state_transitions(world, SimulationConfig(), [proposal], DeterministicRNG(0))
    
    assert hero.mind.strategic.source_trust["source_A"] == 0.1
    
    # 3. Verify durability
    snapshot = Snapshot.from_world(world)
    state, proposal_after = brain.decide(hero, snapshot)
    
    assert hero.mind.strategic.source_trust["source_A"] == 0.1

def test_overload_metrics_visibility(brain, world):
    """Verify that primary_overload_source and metrics are populated when stressed."""
    hero = Entity(id=1, kind="hero")
    world.add_entity(hero)
    
    # Reduce limits to force overload
    hero.mind.strategic.last_capacity_profile = create_test_profile(
        planning_budget=1,
        concern_intake_limit=1
    )
    
    # Inject 3 concerns
    for i in range(3):
        hero.mind.strategic.concerns.append(ConcernRecord(concern_id=f"c{i}", kind=ConcernKind.THREAT, label=f"T{i}", priority=5.0))
        
    snapshot = Snapshot.from_world(world)
    state, proposal = brain.decide(hero, snapshot)
    
    strat_up = next((u for u in proposal.updates if isinstance(u, StrategicUpdate)), None)
    assert strat_up is not None
    assert strat_up.is_overloaded is True
    assert strat_up.overload_score > 0.0
    # Brain logic: sources > leads -> "complexity"
    assert strat_up.primary_overload_source == "complexity"
    assert strat_up.last_overload_tick == world.tick
