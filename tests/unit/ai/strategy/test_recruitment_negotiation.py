import pytest
from src.ai.brain import AIContext
from src.core.entities.entity import Entity
from src.core.models.snapshot import Snapshot
from src.core.models.enums import AIState, StrategicStatus, OfferStatus, ContractKind, ProjectKind
from src.platform.rng import DeterministicRNG
from src.config import SimulationConfig
from src.core.models.strategy import ProjectRecord, RecruitmentOfferRecord, ContractTermRecord
from src.core.models.life_events import SocialBondRecord
from src.core.models.world_state import WorldState
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash
from src.core.gameplay.faction import FactionRegistry
from src.ai.strategy.recruitment_negotiation import RecruitmentNegotiationService

def test_recruitment_offer_generation():
    """Verify that a recruiter creates a reasonable offer based on greed and risk. [PHASE 4]"""
    rng = DeterministicRNG(seed=123)
    config = SimulationConfig()
    faction_reg = FactionRegistry()
    
    actor = Entity(id=1, kind="hero")
    actor.mind.decision.personality.greed = 0.8 # Greedy founder
    
    project = ProjectRecord(
        project_id="prj_dragon",
        kind=ProjectKind.QUEST,
        label="Dragon Hunt",
        metadata={"risk": 0.9} # High risk
    )
    
    world = WorldState(seed=42, grid=Grid(10,10), spatial_index=SpatialHash(16))
    world.tick = 100
    world.add_entity(actor)
    snapshot = Snapshot.from_world(world)
    
    ctx = AIContext(actor=actor, snapshot=snapshot, config=config, rng=rng, faction_reg=faction_reg)
    
    offer = RecruitmentNegotiationService.create_offer(ctx, candidate_id=2, project=project)
    
    assert offer.recruiter_id == 1
    assert offer.candidate_id == 2
    assert offer.project_id == "prj_dragon"
    assert offer.status == OfferStatus.PENDING
    
    # Greedy founder (0.8) offers less: 0.5 - (0.8 * 0.4) = 0.5 - 0.32 = 0.18
    payout = next(t for t in offer.proposed_terms if t.term_type == "payout")
    assert payout.params["value"] == pytest.approx(0.18)
    
    # High risk project (0.9 > 0.5) prefer "vanguard" role
    role = next(t for t in offer.proposed_terms if t.term_type == "behavior")
    assert role.params["role"] == "vanguard"

def test_recruitment_offer_evaluation_acceptance():
    """Verify candidate accepts a fair offer from a trusted friend. [PHASE 4]"""
    rng = DeterministicRNG(seed=123)
    config = SimulationConfig()
    faction_reg = FactionRegistry()
    
    candidate = Entity(id=2, kind="hero")
    candidate.mind.decision.personality.greed = 0.2 # Generous candidate
    
    # Trusting relationship with recruiter
    candidate.mind.social.known_bonds[1] = SocialBondRecord(target_id=1, trust=0.8, loyalty=0.5)
    
    offer = RecruitmentOfferRecord(
        offer_id="off_1",
        recruiter_id=1,
        candidate_id=2,
        contract_kind=ContractKind.EXPEDITION,
        status=OfferStatus.PENDING,
        proposed_terms=[ContractTermRecord(term_type="payout", label="Share", params={"value": 0.3})]
    )
    
    recruiter = Entity(id=1, kind="hero")
    world = WorldState(seed=42, grid=Grid(10,10), spatial_index=SpatialHash(16))
    world.tick = 100
    world.add_entity(recruiter)
    world.add_entity(candidate)
    snapshot = Snapshot.from_world(world)
    
    ctx = AIContext(actor=candidate, snapshot=snapshot, config=config, rng=rng, faction_reg=faction_reg)
    
    appraisal = RecruitmentNegotiationService.evaluate_offer(ctx, offer)
    assert appraisal.status == OfferStatus.ACCEPTED

def test_recruitment_haggling_counter_offer():
    """Verify greedy candidate counter-offers when the payout is too low. [PHASE 4]"""
    rng = DeterministicRNG(seed=123)
    config = SimulationConfig()
    faction_reg = FactionRegistry()
    
    candidate = Entity(id=2, kind="hero")
    candidate.mind.decision.personality.greed = 0.9 # Greedy candidate
    candidate.mind.social.known_bonds[1] = SocialBondRecord(target_id=1, trust=0.2) # Neutral trust
    
    offer = RecruitmentOfferRecord(
        offer_id="off_2",
        recruiter_id=1,
        candidate_id=2,
        contract_kind=ContractKind.EXPEDITION,
        status=OfferStatus.PENDING,
        proposed_terms=[ContractTermRecord(term_type="payout", label="Share", params={"value": 0.1, "is_negotiable": True})],
        negotiation_count=0
    )
    
    recruiter = Entity(id=1, kind="hero")
    world = WorldState(seed=42, grid=Grid(10,10), spatial_index=SpatialHash(16))
    world.tick = 100
    world.add_entity(recruiter)
    world.add_entity(candidate)
    snapshot = Snapshot.from_world(world)
    
    ctx = AIContext(actor=candidate, snapshot=snapshot, config=config, rng=rng, faction_reg=faction_reg)
    
    appraisal = RecruitmentNegotiationService.evaluate_offer(ctx, offer)
    
    assert appraisal.status == OfferStatus.COUNTERED
    assert "Haggling" in appraisal.reason
    
    payout = next(t for t in appraisal.counter_terms if t.term_type == "payout")
    # Payout appraisal for greed 0.9: 
    # expected_share = 0.2 + (0.9 * 0.3) = 0.47
    # Counter asks for expected_share + greed*0.1 = 0.47 + 0.09 = 0.56
    assert payout.params["value"] == 0.56

def test_recruiter_evaluates_counter():
    """Verify recruiter accepts a counter-offer for an urgent project. [PHASE 4]"""
    rng = DeterministicRNG(seed=123)
    config = SimulationConfig()
    faction_reg = FactionRegistry()
    
    recruiter = Entity(id=1, kind="hero")
    project = ProjectRecord(
        project_id="prj_urg",
        kind=ProjectKind.QUEST,
        label="Urgent Hunt",
        priority=5.0, # Very high priority
        urgency=1.0
    )
    recruiter.mind.strategic.projects = [project]
    
    from src.ai.strategy.recruitment_negotiation import OfferAppraisal
    
    offer = RecruitmentOfferRecord(
        offer_id="off_3",
        recruiter_id=1,
        candidate_id=2,
        project_id="prj_urg",
        contract_kind=ContractKind.EXPEDITION,
        status=OfferStatus.PENDING
    )
    
    # Counter asks for 30% payout
    appraisal = OfferAppraisal(
        status=OfferStatus.COUNTERED,
        counter_terms=[ContractTermRecord(term_type="payout", label="Share", params={"value": 0.3})]
    )
    
    world = WorldState(seed=42, grid=Grid(10,10), spatial_index=SpatialHash(16))
    world.tick = 100
    world.add_entity(recruiter)
    snapshot = Snapshot.from_world(world)
    
    ctx = AIContext(actor=recruiter, snapshot=snapshot, config=config, rng=rng, faction_reg=faction_reg)
    
    final_status = RecruitmentNegotiationService.evaluate_counter(ctx, offer, appraisal)
    assert final_status == OfferStatus.ACCEPTED
