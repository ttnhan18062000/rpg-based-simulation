import pytest
from unittest.mock import MagicMock
from src_legacy.ai.cognition_capacity import CognitionCapacityBuilder
from src_legacy.ai.strategic_bounded_appraisal import BoundedStrategicAppraisalService
from src_legacy.core.models.strategy import StrategicStatus, ProjectRecord, ProjectKind, ObjectiveRecord, BlockerRecord
from src_legacy.core.models.enums import ObjectiveKind, BlockerKind

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

def test_objective_derivation_precedence_blocker_first():
    ent = create_mock_entity_with_strat({'int_': 15, 'wis': 15, 'per': 15, 'cha': 15})
    profile = CognitionCapacityBuilder.build(ent)
    assert profile.interruption_resistance == 0.8
    
    # Project with an objective
    obj1 = ObjectiveRecord(objective_id="obj1", project_id="p1", kind=ObjectiveKind.VISIT, label="OBJ1", priority=1.0, status=StrategicStatus.ACTIVE)
    p1 = ProjectRecord(project_id="p1", kind=ProjectKind.SOCIAL, label="P1", priority=1.0, objectives=[obj1], active_objective_id="obj1")
    
    # Blocker tied to project
    b1 = BlockerRecord(blocker_id="blocker1", severity=1.0, spawned_from_id="p1", kind=BlockerKind.KNOWLEDGE, label="KNOW")
    
    # Start with NO project to force derivation
    ent.mind.strategic.current_project_id = None
    ent.mind.strategic.current_objective_id = None
    ent.mind.strategic.projects = [p1]
    ent.mind.strategic.blockers = [b1]
    ent.mind.strategic.current_project = None
    
    snapshot = MagicMock()
    snapshot.tick = 100
    
    outcome = BoundedStrategicAppraisalService.evaluate(ent, snapshot, profile)
    # Project p1 should be selected
    assert outcome.selected_project_id == "p1"
    # Objective should be the blocker
    assert outcome.selected_objective_id == "blocker1"

def test_objective_derivation_precedence_active_objective_if_no_blocker():
    ent = create_mock_entity_with_strat()
    profile = CognitionCapacityBuilder.build(ent)
    
    obj1 = ObjectiveRecord(objective_id="obj1", project_id="p1", kind=ObjectiveKind.VISIT, label="OBJ1", priority=1.0, status=StrategicStatus.ACTIVE)
    p1 = ProjectRecord(project_id="p1", kind=ProjectKind.SOCIAL, label="P1", priority=1.0, objectives=[obj1], active_objective_id="obj1")
    
    # Trigger re-derivation by having no current project (initial selection)
    ent.mind.strategic.current_project_id = None
    ent.mind.strategic.current_objective_id = None
    ent.mind.strategic.projects = [p1]
    ent.mind.strategic.current_project = None
    
    snapshot = MagicMock()
    snapshot.tick = 100
    
    outcome = BoundedStrategicAppraisalService.evaluate(ent, snapshot, profile)
    assert outcome.selected_project_id == "p1"
    assert outcome.selected_objective_id == "obj1"

def test_objective_derivation_precedence_first_unresolved_if_no_active():
    ent = create_mock_entity_with_strat()
    profile = CognitionCapacityBuilder.build(ent)
    
    obj1 = ObjectiveRecord(objective_id="obj1", project_id="p1", kind=ObjectiveKind.VISIT, label="OBJ1", priority=1.0, status=StrategicStatus.RESOLVED)
    obj2 = ObjectiveRecord(objective_id="obj2", project_id="p1", kind=ObjectiveKind.VISIT, label="OBJ2", priority=1.0, status=StrategicStatus.ACTIVE)
    p1 = ProjectRecord(project_id="p1", kind=ProjectKind.SOCIAL, label="P1", priority=1.0, objectives=[obj1, obj2], active_objective_id=None)
    
    # Trigger re-derivation by having no current project
    ent.mind.strategic.current_project_id = None
    ent.mind.strategic.projects = [p1]
    ent.mind.strategic.current_project = None
    
    snapshot = MagicMock()
    snapshot.tick = 100
    
    outcome = BoundedStrategicAppraisalService.evaluate(ent, snapshot, profile)
    assert outcome.selected_project_id == "p1"
    # obj1 is resolved, so it should pick obj2
    assert outcome.selected_objective_id == "obj2"
