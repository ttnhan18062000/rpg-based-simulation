"""Integration tests for Strategic Explainability and Cognitive Bounding.
Verifies that cognitive limits are enforced and that the reasons for overload and project switches are correctly reported.
"""

import pytest
from src_legacy.core.models.world_state import WorldState
from src_legacy.core.entities.entity import Entity
from src_legacy.core.models.vectors import Vector2
from src_legacy.core.models.strategy import (
    StrategicStatus, ProjectKind, ProjectRecord, CandidateZoneRecord, 
    RecruitmentOfferRecord, ContractKind, OfferStatus, SocialContractRecord
)
from src_legacy.ai.brain import AIBrain
from src_legacy.core.models.snapshot import Snapshot
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.config import SimulationConfig
from src_legacy.core.world.grid import Grid
from src_legacy.platform.spatial_hash import SpatialHash
from src_legacy.actions.base import StrategicUpdate
from src_legacy.ai.cognition_capacity import CognitionCapacityProfile

@pytest.fixture
def mock_world():
    grid = Grid(100, 100)
    spatial = SpatialHash(cell_size=10)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    world.entities = {}
    return world

@pytest.fixture
def brain():
    config = SimulationConfig()
    return AIBrain(config, DeterministicRNG(0))

def test_candidate_zone_enforcement(mock_world, brain):
    """Verify that candidate_zone_limit is enforced and drops excess zones."""
    from src_legacy.core.gameplay.attributes import Attributes, AttributeCaps
    hero = Entity(id=1, kind="hero")
    # Initialize attributes to 1
    hero.progression.attributes = Attributes(
        str_=1, agi=1, vit=1, int_=1, spi=1, wis=1, end=1, per=1, cha=1
    )
    hero.progression.attribute_caps = AttributeCaps()
    mock_world.add_entity(hero)
    
    # 1. Add 3 zones
    hero.mind.strategic.candidate_zones = [
        CandidateZoneRecord(zone_id="zone_a", confidence=0.9),
        CandidateZoneRecord(zone_id="zone_b", confidence=0.8),
        CandidateZoneRecord(zone_id="zone_c", confidence=0.7),
    ]
    
    snapshot = Snapshot.from_world(mock_world)
    state, proposal = brain.decide(hero, snapshot)
    
    update = next((u for u in proposal.updates if isinstance(u, StrategicUpdate)), None)
    assert update is not None
    
    # per=1, int=1 => n_per=0, n_int=0
    # candidate_zone_limit = int(1.0 + 3*0 + 1*0) = 1
    assert update.last_capacity_profile.candidate_zone_limit == 1
    assert update.candidate_zones_used <= 1
    assert update.is_overloaded is True

def test_ally_evaluation_enforcement(mock_world, brain):
    """Verify that ally_evaluation_limit caps contracts and offers evaluated."""
    from src_legacy.core.gameplay.attributes import Attributes, AttributeCaps
    hero = Entity(id=1, kind="hero")
    hero.progression.attributes = Attributes(
        str_=1, agi=1, vit=1, int_=1, spi=1, wis=1, end=1, per=1, cha=1
    )
    hero.progression.attribute_caps = AttributeCaps()
    mock_world.add_entity(hero)
    
    # Add 4 items (limit will be 2)
    hero.mind.strategic.contracts = [
        SocialContractRecord(contract_id="c1", kind=ContractKind.EXPEDITION, purpose="A", status=StrategicStatus.ACTIVE, founder_id=1),
        SocialContractRecord(contract_id="c2", kind=ContractKind.EXPEDITION, purpose="B", status=StrategicStatus.ACTIVE, founder_id=1),
    ]
    hero.mind.strategic.offers = [
        RecruitmentOfferRecord(offer_id="o1", recruiter_id=2, candidate_id=1, contract_kind=ContractKind.ESCORT, status=OfferStatus.PENDING),
        RecruitmentOfferRecord(offer_id="o2", recruiter_id=3, candidate_id=1, contract_kind=ContractKind.ESCORT, status=OfferStatus.PENDING)
    ]
    
    snapshot = Snapshot.from_world(mock_world)
    state, proposal = brain.decide(hero, snapshot)
    
    update = next((u for u in proposal.updates if isinstance(u, StrategicUpdate)), None)
    assert update is not None
    
    # cha=1, wis=1 => social_bandwidth = 2 => ally_evaluation_limit = 2
    assert update.last_capacity_profile.ally_evaluation_limit == 2
    assert update.ally_evaluations_used <= 2
    assert update.is_overloaded is True

def test_overload_source_trauma(mock_world, brain):
    """Verify that heavy HP damage triggers 'trauma' as the primary overload source."""
    hero = Entity(id=1, kind="hero")
    mock_world.add_entity(hero)
    
    # Drop HP to 10%
    hero.combat.hp = 10
    hero.combat.max_hp = 100
    
    snapshot = Snapshot.from_world(mock_world)
    state, proposal = brain.decide(hero, snapshot)
    
    update = next((u for u in proposal.updates if isinstance(u, StrategicUpdate)), None)
    assert update is not None
    assert update.is_overloaded is True
    assert update.primary_overload_source == "trauma"

def test_switch_reason_transparency(mock_world, brain):
    """Verify that a project switch provides a human-readable reason."""
    hero = Entity(id=1, kind="hero")
    mock_world.add_entity(hero)
    
    # Current project (minimal priority, zero abandonment cost, zero threshold)
    p1 = ProjectRecord(
        project_id="p1", kind=ProjectKind.QUEST, label="Small Task", 
        priority=1.0, status=StrategicStatus.ACTIVE,
        abandonment_cost=0.0, interruption_threshold=0.0
    )
    hero.mind.strategic.projects.append(p1)
    hero.mind.strategic.current_project_id = "p1"
    
    # Rival project (Max priority + High Urgency)
    p2 = ProjectRecord(project_id="p2", kind=ProjectKind.QUEST, label="Big Quest", priority=5.0, urgency=1.0, status=StrategicStatus.ACTIVE)
    hero.mind.strategic.projects.append(p2)
    
    snapshot = Snapshot.from_world(mock_world)
    state, proposal = brain.decide(hero, snapshot)
    
    update = next((u for u in proposal.updates if isinstance(u, StrategicUpdate)), None)
    assert update is not None
    assert update.current_project_id == "p2"
    
    # Check drivers for reason
    driver = next((d for d in update.strategic_drivers if d.label == "STRATEGIC_SWITCH"), None)
    assert driver is not None
    # Verify exact keyword presence for transparency
    assert "score" in driver.description.lower()
    assert "current" in driver.description.lower()
    assert "margin" in driver.description.lower()

    # 4. Prove Authoritative Commitment (Milestone 4)
    from src_legacy.systems.gameplay.action_system import ActionSystem
    ActionSystem.apply_strategic_update(hero, update)
    
    # recent_drivers should now contain the switch driver
    assert any(d.label == "STRATEGIC_SWITCH" for d in hero.mind.strategic.recent_drivers)
    
    # Verify SCHEMA transparency
    from src_legacy.api.presenters.ai_presenter import AIPresenter
    explanation = AIPresenter.get_explanation(hero)
    strat_schema = explanation.strategy
    assert any(d.label == "STRATEGIC_SWITCH" for d in strat_schema.recent_drivers)
