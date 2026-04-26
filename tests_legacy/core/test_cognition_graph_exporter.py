"""Unit tests for EntityCognitionExporter. [MILESTONE 6]"""

import pytest
from unittest.mock import MagicMock
from src_legacy.core.logic.cognition_graph_exporter import EntityCognitionExporter
from src_legacy.core.models.strategy import (
    StrategicState, DirectiveRecord, ProjectRecord, ObjectiveRecord
)
from src_legacy.core.models.enums import (
    StrategicStatus, ProjectKind, ObjectiveKind, DirectiveKind
)

@pytest.fixture
def mock_entity():
    entity = MagicMock()
    entity.id = 99
    entity.mind = MagicMock()
    return entity

def test_export_empty_strategy(mock_entity):
    """Verify export from an entity with no strategic state."""
    mock_entity.mind.strategic = None
    graph = EntityCognitionExporter.export(mock_entity, tick=10)
    
    assert graph.entity_id == 99
    assert graph.tick == 10
    assert len(graph.nodes) == 1 # Only root node
    assert graph.nodes[0].kind == "entity"
    assert len(graph.edges) == 0

def test_export_with_core_strategic_state(mock_entity):
    """Verify export of directives, projects, and objectives."""
    strat = StrategicState()
    
    # Add Directive
    d = DirectiveRecord(directive_id="d1", label="Directive 1", priority=2.0, kind=DirectiveKind.PERSONAL)
    strat.directives.append(d)
    
    # Add Project
    p = ProjectRecord(project_id="p1", kind=ProjectKind.EXPLORATION, label="Project 1", active_objective_id="o1")
    o = ObjectiveRecord(objective_id="o1", project_id="p1", kind=ObjectiveKind.VISIT, label="Objective 1")
    p.objectives.append(o)
    strat.projects.append(p)
    
    strat.current_project_id = "p1"
    strat.current_objective_id = "o1"
    
    mock_entity.mind.strategic = strat
    
    graph = EntityCognitionExporter.export(mock_entity, tick=10)
    
    # 5 nodes: Root, Directive, Project, Objective
    # wait, 4 nodes: Entity, Directive, Project, Objective
    node_kinds = [n.kind for n in graph.nodes]
    assert "entity" in node_kinds
    assert "directive" in node_kinds
    assert "project" in node_kinds
    assert "objective" in node_kinds
    
    # Verify Edges
    edge_kinds = [e.kind for e in graph.edges]
    assert "has_directive" in edge_kinds
    assert "owns_project" in edge_kinds
    assert "has_objective" in edge_kinds
    assert "pursuing" in edge_kinds # Entity -> current project
    assert "active_objective" in edge_kinds # Project -> Objective OR Entity -> Objective

def test_export_determinism(mock_entity):
    """Verify that multiple exports from the same state are identical."""
    strat = StrategicState()
    strat.directives.append(DirectiveRecord(directive_id="d1", label="D1", kind=DirectiveKind.PERSONAL))
    strat.directives.append(DirectiveRecord(directive_id="d2", label="D2", kind=DirectiveKind.PERSONAL))
    strat.projects.append(ProjectRecord(project_id="p1", kind=ProjectKind.QUEST, label="P1"))
    
    mock_entity.mind.strategic = strat
    
    graph1 = EntityCognitionExporter.export(mock_entity, tick=10)
    graph2 = EntityCognitionExporter.export(mock_entity, tick=10)
    
    assert graph1.model_dump() == graph2.model_dump()

def test_non_mutation(mock_entity):
    """Verify that exporter does not mutate the source entity."""
    strat = StrategicState()
    strat.current_project_id = "p1"
    mock_entity.mind.strategic = strat
    
    original_dump = strat.model_dump()
    
    EntityCognitionExporter.export(mock_entity, tick=10)
    
    assert strat.model_dump() == original_dump
