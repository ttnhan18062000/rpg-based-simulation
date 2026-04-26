"""
Contract tests for Cognition Graph Export.

Covers:
- Part 1 §Strategic: Cognition graph export exposes persisted strategic state
"""
import pytest
from src.core.state import EntityState
from src.core.strategic import (
    StrategicComponent, DirectiveState, DirectivePriority,
    ProjectState, ProjectStatus, ObjectiveState, ObjectiveStatus,
    BlockerState, LeadState, LeadCertainty, ConcernState,
    HypothesisState
)
from src.systems.cognition_export import CognitionGraphExporter


def _make_rich_entity():
    """Build an entity with full strategic state for export testing."""
    strategic = StrategicComponent(
        directives={"d1": DirectiveState(
            id="d1", kind="avenge", target="bandit_001",
            priority=DirectivePriority.HIGH, salience=0.8
        )},
        projects={"p1": ProjectState(
            id="p1", kind="crafting", status=ProjectStatus.ACTIVE, score=50,
            objectives=[
                ObjectiveState(id="o1", kind="acquire_item", target="iron",
                             status=ObjectiveStatus.ACTIVE, blocker_ids=["b1"])
            ],
            active_objective_id="o1"
        )},
        blockers={"b1": BlockerState(
            id="b1", kind="material", subject="iron", severity=0.7
        )},
        leads={"l1": LeadState(
            id="l1", kind="location", subject="iron",
            certainty=LeadCertainty.APPROXIMATE
        )},
        concerns={"c1": ConcernState(
            id="c1", kind="danger", source="swamp", urgency=0.6
        )},
        hypotheses={"h1": HypothesisState(
            id="h1", subject="iron_mine", claim="iron mine in cave",
            confidence=0.7, supporting_lead_ids=["l1"]
        )},
        current_project_id="p1",
        current_objective_id="o1"
    )
    return EntityState(id=1, kind="hero", position=(5.0, 5.0), strategic=strategic)


class TestCognitionGraphExport:
    """Part 1 §Strategic: Cognition graph export."""

    def test_export_empty_strategy(self):
        entity = EntityState(id=1, kind="hero", position=(5.0, 5.0))
        graph = CognitionGraphExporter.export(entity)
        assert graph.entity_id == 1
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_export_rich_strategy(self):
        entity = _make_rich_entity()
        graph = CognitionGraphExporter.export(entity)
        # Should have: 1 directive + 1 project + 1 objective + 1 blocker + 1 lead + 1 concern + 1 hypothesis = 7 nodes
        assert len(graph.nodes) == 7
        # Edges: project→objective, blocker→objective, lead→hypothesis = 3
        assert len(graph.edges) == 3

    def test_export_determinism(self):
        entity = _make_rich_entity()
        assert CognitionGraphExporter.is_deterministic(entity)

    def test_export_does_not_mutate_entity(self):
        entity = _make_rich_entity()
        original_blockers = dict(entity.strategic.blockers)
        CognitionGraphExporter.export(entity)
        assert entity.strategic.blockers == original_blockers

    def test_metadata_contains_current_project(self):
        entity = _make_rich_entity()
        graph = CognitionGraphExporter.export(entity)
        assert graph.metadata["current_project"] == "p1"
        assert graph.metadata["current_objective"] == "o1"

    def test_node_kinds_correct(self):
        entity = _make_rich_entity()
        graph = CognitionGraphExporter.export(entity)
        kinds = {n.kind for n in graph.nodes}
        assert "directive" in kinds
        assert "project" in kinds
        assert "objective" in kinds
        assert "blocker" in kinds
        assert "lead" in kinds
        assert "concern" in kinds
        assert "hypothesis" in kinds
