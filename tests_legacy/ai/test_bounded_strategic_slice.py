import pytest
from unittest.mock import MagicMock
from src_legacy.ai.cognition_capacity import CognitionCapacityBuilder, CognitionCapacityProfile
from src_legacy.ai.strategic_bounded_appraisal import BoundedStrategicAppraisalService
from src_legacy.core.models.strategy import StrategicStatus, ProjectRecord, ProjectKind, ConcernRecord, LeadKind, LeadRecord

def create_mock_entity_with_strat(profile_attrs=None):
    # Create simple entity with progression/attributes
    prog = MagicMock()
    prog.attributes = MagicMock()
    prog.attribute_caps = MagicMock()
    
    # Defaults for attributes
    attrs = profile_attrs or {}
    prog.attributes.int_ = attrs.get('int_', 5)
    prog.attributes.wis = attrs.get('wis', 5)
    prog.attributes.per = attrs.get('per', 5)
    prog.attributes.cha = attrs.get('cha', 5)
    prog.attribute_caps.int_cap = 15
    prog.attribute_caps.wis_cap = 15
    prog.attribute_caps.per_cap = 15
    prog.attribute_caps.cha_cap = 15
    prog.stamina = 50
    prog.max_stamina = 50
    
    # Create Strategic State
    strat = MagicMock()
    strat.projects = []
    strat.concerns = []
    strat.obligations = []
    strat.leads = []
    strat.contracts = []
    strat.blockers = []
    strat.current_project_id = None
    strat.current_objective_id = None
    strat.current_project = None
    strat.current_objective = None
    
    entity = MagicMock()
    entity.id = 1
    entity.progression = prog
    entity.mind = MagicMock()
    entity.mind.strategic = strat
    return entity

def test_low_profile_entity_has_smaller_active_slice_than_high_profile_entity():
    # Low profile: all attributes 1
    low_ent = create_mock_entity_with_strat({'int_': 1, 'wis': 1, 'per': 1, 'cha': 1})
    low_profile = CognitionCapacityBuilder.build(low_ent) # active_slice_limit = 3
    
    # High profile: all attributes 15
    high_ent = create_mock_entity_with_strat({'int_': 15, 'wis': 15, 'per': 15, 'cha': 15})
    high_profile = CognitionCapacityBuilder.build(high_ent) # active_slice_limit = 9
    
    # Create 10 candidates (projects)
    projects = [ProjectRecord(project_id=f"p{i}", kind=ProjectKind.SOCIAL, label=f"P{i}", priority=1.0) for i in range(10)]
    
    snapshot = MagicMock()
    snapshot.tick = 100
    
    # Test low profile
    low_ent.mind.strategic.projects = projects
    low_ent.mind.strategic.current_project_id = None
    outcome_low = BoundedStrategicAppraisalService.evaluate(low_ent, snapshot, low_profile)
    assert len(outcome_low.bounded_slice.candidates) == 3
    
    # Test high profile
    high_ent.mind.strategic.projects = projects
    outcome_high = BoundedStrategicAppraisalService.evaluate(high_ent, snapshot, high_profile)
    assert len(outcome_high.bounded_slice.candidates) <= high_profile.active_slice_limit
    assert len(outcome_high.bounded_slice.candidates) == 9

def test_concern_intake_is_capped_by_profile():
    # Low profile: wis=1 -> concern_intake_limit = 2 + 2*0 + 1*0 = 2
    ent = create_mock_entity_with_strat({'int_': 1, 'wis': 1, 'per': 1, 'cha': 1})
    profile = CognitionCapacityBuilder.build(ent)
    
    # 5 unresolved concerns
    concerns = [ConcernRecord(concern_id=f"c{i}", kind=0, label=f"C{i}", priority=2.0) for i in range(5)]
    ent.mind.strategic.concerns = concerns
    
    snapshot = MagicMock()
    snapshot.tick = 100
    
    outcome = BoundedStrategicAppraisalService.evaluate(ent, snapshot, profile)
    # The pool should have dropped 3 concerns
    assert outcome.bounded_slice.dropped_concerns_count == 3
    # Slice might contain other things, but max 2 concerns
    slice_concerns = [c for c in outcome.bounded_slice.candidates if c.kind == "concern"]
    assert len(slice_concerns) == 2

def test_lead_retention_is_capped_by_profile():
    # Low profile: int=1, per=1 -> lead_retention_limit = 2 + 3*0 + 2*0 = 2
    ent = create_mock_entity_with_strat({'int_': 1, 'wis': 1, 'per': 1, 'cha': 1})
    profile = CognitionCapacityBuilder.build(ent)
    
    # 5 leads
    leads = [LeadRecord(lead_id=f"l{i}", kind=0, label=f"L{i}", priority=1.0) for i in range(5)]
    ent.mind.strategic.leads = leads
    
    snapshot = MagicMock()
    snapshot.tick = 100
    
    outcome = BoundedStrategicAppraisalService.evaluate(ent, snapshot, profile)
    assert outcome.bounded_slice.dropped_leads_count == 3
    slice_leads = [c for c in outcome.bounded_slice.candidates if c.kind == "lead"]
    assert len(slice_leads) == 2

def test_reserved_current_project_slot_is_used_when_current_project_exists():
    # Low profile: slice limit 3
    ent = create_mock_entity_with_strat({'int_': 1, 'wis': 1, 'per': 1, 'cha': 1})
    profile = CognitionCapacityBuilder.build(ent)
    
    # 10 other projects, 1 current project
    curr_proj = ProjectRecord(project_id="curr", kind=ProjectKind.SOCIAL, label="CURR", priority=0.1) # VERY LOW SCORE
    others = [ProjectRecord(project_id=f"p{i}", kind=ProjectKind.SOCIAL, label=f"P{i}", priority=5.0) for i in range(10)]
    
    ent.mind.strategic.current_project_id = "curr"
    ent.mind.strategic.projects = [curr_proj] + others
    ent.mind.strategic.current_project = curr_proj
    
    snapshot = MagicMock()
    snapshot.tick = 100
    
    outcome = BoundedStrategicAppraisalService.evaluate(ent, snapshot, profile)
    
    # current project should be in the slice despite low priority
    candidate_ids = [c.source_id for c in outcome.bounded_slice.candidates]
    assert "curr" in candidate_ids
    assert outcome.bounded_slice.reserved_current_project_slot_used is True
    assert len(outcome.bounded_slice.candidates) == 3

def test_dropped_candidate_counts_are_deterministic():
    ent = create_mock_entity_with_strat({'int_': 5, 'wis': 5, 'per': 5, 'cha': 5})
    profile = CognitionCapacityBuilder.build(ent)
    
    # Fixed set of noise
    ent.mind.strategic.concerns = [ConcernRecord(concern_id=f"c{i}", kind=0, label=f"C{i}", priority=2.0) for i in range(10)]
    ent.mind.strategic.leads = [LeadRecord(lead_id=f"l{i}", kind=0, label=f"L{i}", priority=1.0) for i in range(10)]
    
    snapshot = MagicMock()
    snapshot.tick = 100
    
    outcome1 = BoundedStrategicAppraisalService.evaluate(ent, snapshot, profile)
    outcome2 = BoundedStrategicAppraisalService.evaluate(ent, snapshot, profile)
    
    assert outcome1.bounded_slice.dropped_candidates_count == outcome2.bounded_slice.dropped_candidates_count
    assert outcome1.bounded_slice.dropped_concerns_count == outcome2.bounded_slice.dropped_concerns_count
