"""
Contract tests for Cognition Graph Export.

Covers:
- Part 1 §Strategic: Cognition graph export exposes persisted strategic state
"""
import pytest
from src.core.builder import V2EntityBuilder
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

    directive = DirectiveState(
        id="d1",
        kind="avenge",
        target="bandit_001",
        priority=DirectivePriority.HIGH,
        salience=0.8,
    )

    objective = ObjectiveState(
        id="o1",
        kind="acquire_item",
        target="iron",
        status=ObjectiveStatus.ACTIVE,
        blocker_ids=["b1"],
    )

    project = ProjectState(
        id="p1",
        kind="crafting",
        status=ProjectStatus.ACTIVE,
        score=50,
        objectives=[objective],
        active_objective_id="o1",
    )

    blocker = BlockerState(
        id="b1",
        kind="material",
        subject="iron",
        severity=0.7,
    )

    lead = LeadState(
        id="l1",
        kind="location",
        subject="iron",
        certainty=LeadCertainty.APPROXIMATE,
    )

    concern = ConcernState(
        id="c1",
        kind="danger",
        source="swamp",
        urgency=0.6,
    )

    hypothesis = HypothesisState(
        id="h1",
        subject="iron_mine",
        claim="iron mine in cave",
        confidence=0.7,
        supporting_lead_ids=["l1"],
    )

    return (
        V2EntityBuilder(1)
        .kind("hero")
        .location(5.0, 5.0)
        .strategic(
            directives={"d1": directive},
            projects={"p1": project},
            blockers={"b1": blocker},
            leads={"l1": lead},
            concerns={"c1": concern},
            hypotheses={"h1": hypothesis},
            current_project_id="p1",
            current_objective_id="o1",
        )
        .build()
    )


class TestCognitionGraphExport:
    """Part 1 §Strategic: Cognition graph export."""

    # Logic ID: STRAT-056

    def test_export_empty_strategy(self):
        entity = V2EntityBuilder(1).kind("hero").location(5.0, 5.0).build()
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

    # Logic ID: STRAT-058

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
