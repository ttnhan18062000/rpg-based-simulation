import pytest
import io
import sys
from unittest.mock import MagicMock
from src_legacy.ui.cli.inspector import EntityInspector
from src_legacy.core.models.strategy import (
    StrategicState, ProjectRecord, StrategicStatus, 
    DirectiveRecord, DirectiveKind, ConcernRecord,
    SocialContractRecord, ContractKind,
    RecruitmentOfferRecord, OfferStatus,
    ObligationRecord, HypothesisRecord,
    CandidateZoneRecord, LeadRecord
)
from src_legacy.core.models.cognition import CognitionCapacityProfile
from src_legacy.core.models.enums import AIState, ConcernKind, LeadKind, ProjectKind

class MockEntity:
    def __init__(self, eid=1, name="Hero"):
        self.id = eid
        self.identity = MagicMock()
        self.identity.display_name = name
        self.identity.tier = "Bronze"
        self.progression = MagicMock()
        self.progression.level = 1
        self.spatial = MagicMock()
        self.spatial.pos = MagicMock(x=10.0, y=20.0)
        self.combat = MagicMock()
        self.combat.hp = 100
        self.combat.max_hp = 100
        self.mind = MagicMock()
        self.mind.decision = MagicMock()
        self.mind.decision.ai_state = AIState.IDLE
        self.mind.strategic = None

def test_empty_strategic_state_rendering():
    """Verify that the inspector handles empty strategic state without crashing. [Strategy M1]"""
    entity = MockEntity()
    entity.mind.strategic = StrategicState() # All lists empty
    
    output = io.StringIO()
    sys.stdout = output
    try:
        EntityInspector.render_strategic_domain(entity)
    finally:
        sys.stdout = sys.__stdout__
    
    text = output.getvalue()
    assert "No active projects" in text
    assert "No active directives" in text
    assert "STRATEGIC DOMAIN" in text

def test_uncertainty_rendering():
    """Verify rendering of hypotheses, zones, and leads. [Strategy M1]"""
    entity = MockEntity()
    strat = StrategicState()
    
    # 1. Add Hypothesis
    strat.hypotheses.append(HypothesisRecord(
        hypothesis_id="h1",
        label="Ancient Temple Theory",
        confidence=0.75,
        is_active=True
    ))
    
    # 2. Add Candidate Zone
    strat.candidate_zones.append(CandidateZoneRecord(
        zone_id="Forest_A",
        region_id="Forest",
        confidence=0.6,
        last_search_tick=0
    ))
    
    # 3. Add Lead
    strat.leads.append(LeadRecord(
        lead_id="l1",
        kind=LeadKind.LOCATION,
        label="Mysterious Map",
        certainty=0.9,
        subject="Artifact"
    ))
    
    entity.mind.strategic = strat
    
    output = io.StringIO()
    sys.stdout = output
    try:
        EntityInspector.render_uncertainty_layer(entity)
    finally:
        sys.stdout = sys.__stdout__
    
    text = output.getvalue()
    assert "STRATEGIC UNCERTAINTY" in text
    assert "Ancient Temple Theory" in text
    assert "Forest_A" in text
    assert "Mysterious Map" in text
    assert "Conf: 0.75" in text

def test_social_contract_rendering():
    """Verify rendering of contracts, offers, and obligations. [Strategy M1]"""
    entity = MockEntity()
    strat = StrategicState()
    
    # 1. Add Contract
    strat.contracts.append(SocialContractRecord(
        contract_id="c1",
        purpose="City Defense",
        kind=ContractKind.MERCENARY,
        founder_id=1,
        member_ids=[2, 3],
        member_roles={1: "Commander"}
    ))
    
    # 2. Add Offer
    strat.offers.append(RecruitmentOfferRecord(
        offer_id="o1",
        recruiter_id=2,
        candidate_id=1,
        contract_kind=ContractKind.EXPEDITION,
        status=OfferStatus.PENDING
    ))
    
    # 3. Add Obligation
    strat.obligations.append(ObligationRecord(
        obligation_id="obl1",
        label="Taxes",
        target_id=0, # The Town
        priority=3.0,
        deadline_tick=100
    ))
    
    entity.mind.strategic = strat
    
    output = io.StringIO()
    sys.stdout = output
    try:
        EntityInspector.render_social_contracts(entity)
    finally:
        sys.stdout = sys.__stdout__
    
    text = output.getvalue()
    assert "SOCIAL CONTRACTS & OBLIGATIONS" in text
    assert "City Defense" in text
    assert "Commander" in text
    assert "Taxes" in text
    assert "⬅️" in text # Direction icon for incoming offer
    assert "Due: T100" in text

def test_mixed_partial_state_rendering():
    """Heavy test with multiple sections populated. [Strategy M1]"""
    entity = MockEntity()
    strat = StrategicState()
    
    # Projects
    strat.projects.append(ProjectRecord(
        project_id="p1",
        kind=ProjectKind.QUEST,
        label="Main Quest",
        status=StrategicStatus.ACTIVE,
        objectives=[]
    ))
    strat.current_project_id = "p1"
    
    # Directives
    strat.directives.append(DirectiveRecord(
        directive_id="d1",
        label="Kill Goblins",
        kind=DirectiveKind.PERSONAL
    ))
    
    # Capacity
    strat.last_capacity_profile = CognitionCapacityProfile(
        planning_budget=10,
        judgment_stability=0.8,
        evidence_quality=0.7,
        social_bandwidth=5,
        detour_depth_limit=2,
        active_slice_limit=5,
        concern_intake_limit=5,
        lead_retention_limit=10,
        candidate_zone_limit=3,
        ally_evaluation_limit=5,
        blocker_resolution_patience=1.0,
        resume_reliability=1.0,
        interruption_resistance=1.0,
        abandonment_threshold_mod=1.0,
        contradiction_sensitivity=1.0,
        source_trust_learning_rate=0.1
    )
    strat.active_slice_used = 2
    strat.is_overloaded = True
    strat.primary_overload_source = "complexity"
    
    entity.mind.strategic = strat
    
    output = io.StringIO()
    sys.stdout = output
    try:
        # Full strategic domain render
        EntityInspector.render_strategic_domain(entity)
    finally:
        sys.stdout = sys.__stdout__
    
    text = output.getvalue()
    assert "[CURRENT]" in text or "Main Quest" in text
    assert "Kill Goblins" in text
    assert "COGNITION & CAPACITY" in text
    assert "COGNITIVE OVERLOAD ALERT" in text
    assert "complexity" in text
