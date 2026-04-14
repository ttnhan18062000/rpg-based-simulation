import pytest
from unittest.mock import MagicMock
from src.ai.cognition_capacity import CognitionCapacityBuilder
from src.ai.strategic_bounded_appraisal import BoundedStrategicAppraisalService
from src.core.models.strategy import StrategicStatus, ProjectRecord, ProjectKind

def create_mock_entity_with_strat(profile_attrs=None):
    prog = MagicMock()
    prog.attributes = MagicMock()
    prog.attribute_caps = MagicMock()
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

def test_project_retention_when_rival_is_below_margin():
    # Low profile: interruption_resistance ~ 0.0, switch_margin ~ 0.10 + 0.25*0 + 0.15*0 = 0.10
    ent = create_mock_entity_with_strat({'int_': 1, 'wis': 1, 'per': 1, 'cha': 1})
    profile = CognitionCapacityBuilder.build(ent)
    
    # Current project (p1)
    p1 = ProjectRecord(project_id="p1", kind=ProjectKind.SOCIAL, label="P1", priority=1.0)
    # Rival project (p2) slightly better
    p2 = ProjectRecord(project_id="p2", kind=ProjectKind.SOCIAL, label="P2", priority=1.5)
    
    ent.mind.strategic.current_project_id = "p1"
    ent.mind.strategic.projects = [p1, p2]
    ent.mind.strategic.current_project = p1
    
    snapshot = MagicMock()
    snapshot.tick = 100
    
    outcome = BoundedStrategicAppraisalService.evaluate(ent, snapshot, profile)
    # switch_margin is ~0.10. 
    # score p1: ~0.3*0.5 + 0.2*0.5 + 0.15*0.5 + 0.25*0.5 + 0.1*0.0 = 0.450
    # score p2: ~0.3*0.75 + 0.2*0.5 + 0.15*0.5 + 0.25*0.5 + 0.1*0.0 = 0.525
    # diff: 0.075 < 0.10 -> should KEEP
    assert outcome.kept_current_project is True
    assert outcome.selected_project_id == "p1"

def test_project_switch_when_rival_is_above_margin():
    # Low profile: switch_margin ~ 0.10
    ent = create_mock_entity_with_strat({'int_': 1, 'wis': 1, 'per': 1, 'cha': 1})
    profile = CognitionCapacityBuilder.build(ent)
    
    # Current project (p1)
    p1 = ProjectRecord(project_id="p1", kind=ProjectKind.SOCIAL, label="P1", priority=0.1)
    # Rival project (p2) much better
    p2 = ProjectRecord(project_id="p2", kind=ProjectKind.SOCIAL, label="P2", priority=5.0)
    
    ent.mind.strategic.current_project_id = "p1"
    ent.mind.strategic.projects = [p1, p2]
    ent.mind.strategic.current_project = p1
    
    snapshot = MagicMock()
    snapshot.tick = 100
    
    outcome = BoundedStrategicAppraisalService.evaluate(ent, snapshot, profile)
    assert outcome.switched_project is True
    assert outcome.selected_project_id == "p2"

def test_switch_margin_increases_with_higher_resistance_profile():
    # High resistance: wis=15, cha=15 -> interruption_resistance=1.0, judgment_stability=1.0
    # switch_margin = 0.10 + 0.25*1.0 + 0.15*1.0 = 0.50 (clamped to 0.45)
    ent = create_mock_entity_with_strat({'int_': 15, 'wis': 15, 'per': 15, 'cha': 15})
    profile = CognitionCapacityBuilder.build(ent)
    assert profile.interruption_resistance == 0.8
    
    # Switch margin should be 0.45
    # score diff needs to be > 0.45 to trigger switch
    p1 = ProjectRecord(project_id="p1", kind=ProjectKind.SOCIAL, label="P1", priority=0.1)
    p2 = ProjectRecord(project_id="p2", kind=ProjectKind.SOCIAL, label="P2", priority=2.0)
    
    ent.mind.strategic.current_project_id = "p1"
    ent.mind.strategic.projects = [p1, p2]
    ent.mind.strategic.current_project = p1
    
    snapshot = MagicMock()
    snapshot.tick = 100
    
    outcome = BoundedStrategicAppraisalService.evaluate(ent, snapshot, profile)
    # margin used should be 0.435
    assert outcome.switch_margin_used == 0.435
    # With margin 0.45, even a moderately better rival won't cause a switch
    assert outcome.kept_current_project is True
    assert outcome.selected_project_id == "p1"
