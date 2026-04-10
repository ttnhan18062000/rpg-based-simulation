import pytest
from src.core.entities.entity import Entity
from src.ai.states.base import AIContext
from src.ai.strategy.recruitment_negotiation import RecruitmentNegotiationService, OfferAppraisal
from src.core.models.enums import OfferStatus, ContractKind, StrategicStatus
from src.core.models.strategy import RecruitmentOfferRecord, ContractTermRecord, ProjectRecord, ProjectKind
from src.core.logic.contract_consequence_service import ContractConsequenceService
from src.core.models.world_state import WorldState
from src.core.models.vectors import Vector2

from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash
from unittest.mock import MagicMock

@pytest.fixture
def mock_world():
    # WorldState requires seed, grid, spatial_index
    grid = Grid(width=10, height=10)
    spatial_index = SpatialHash(cell_size=8)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial_index)
    
    # Add a recruiter and a candidate
    recruiter = Entity(id=1, kind="hero")
    recruiter.progression.xp = 0
    recruiter.identity.faction = 0
    
    candidate = Entity(id=2, kind="hero")
    candidate.progression.xp = 0
    candidate.identity.faction = 0
    candidate.mind.decision.personality.greed = 0.8 # Greedy candidate
    
    world.add_entity(recruiter)
    world.add_entity(candidate)
    return world

def test_negotiation_haggling_loop(mock_world):
    recruiter = mock_world.get_entity(1)
    candidate = mock_world.get_entity(2)
    
    project = ProjectRecord(
        project_id="prj_test",
        kind=ProjectKind.QUEST,
        label="Test Quest",
        priority=1.0
    )
    recruiter.mind.strategic.projects.append(project)
    
    from src.core.models.snapshot import Snapshot
    snap = Snapshot.from_world(mock_world)
    config = MagicMock()
    rng = MagicMock()
    faction_reg = MagicMock()
    
    ctx_recruiter = AIContext(actor=recruiter, snapshot=snap, config=config, rng=rng, faction_reg=faction_reg)
    ctx_candidate = AIContext(actor=candidate, snapshot=snap, config=config, rng=rng, faction_reg=faction_reg)
    
    # 1. Recruiter creates initial offer
    offer = RecruitmentNegotiationService.create_offer(ctx_recruiter, candidate.id, project)
    assert offer.status == OfferStatus.PENDING
    assert len(offer.negotiation_history) == 1
    
    # 2. Candidate evaluates and COUNTERS (because greed=0.8)
    appraisal = RecruitmentNegotiationService.evaluate_offer(ctx_candidate, offer)
    assert appraisal.status == OfferStatus.COUNTERED
    assert "Haggling" in appraisal.reason
    
    # 3. Recruiter evaluates counter
    offer.negotiation_count += 1
    recruiter_status = RecruitmentNegotiationService.evaluate_counter(ctx_recruiter, offer, appraisal)
    
    # Recruiter should accept if project is important and they are same faction
    assert recruiter_status == OfferStatus.ACCEPTED

def test_contract_breach_consequences(mock_world):
    recruiter = mock_world.get_entity(1)
    candidate = mock_world.get_entity(2)
    
    from src.core.models.strategy import SocialContractRecord
    contract = SocialContractRecord(
        contract_id="ct_test",
        kind=ContractKind.EXPEDITION,
        purpose="Test Purpose",
        founder_id=recruiter.id,
        member_ids=[recruiter.id, candidate.id]
    )
    
    # Manually add contract to recruiter and candidate mind
    recruiter.mind.strategic.contracts.append(contract)
    candidate.mind.strategic.contracts.append(contract.model_copy())
    
    # Initial trust
    initial_trust = mock_world.social_registry.get_bond(candidate.id, recruiter.id).trust
    
    # ABANDON (Breach) the contract
    ContractConsequenceService.apply_resolution(mock_world, contract, StrategicStatus.ABANDONED, 100)
    
    # 1. Reputation should decrease
    assert recruiter.identity.reputation.trustworthiness < 10.0 # Default is 10.0
    
    # 2. Relationship trust should decrease
    new_bond = mock_world.social_registry.get_bond(candidate.id, recruiter.id)
    assert new_bond.trust < initial_trust
    assert new_bond.resentment > 0.0
    
    # 3. Strategic state should be updated
    assert recruiter.mind.strategic.contracts[0].status == StrategicStatus.ABANDONED
    assert recruiter.mind.strategic.contracts[0].resolved_tick == 100
