"""
Unit tests for the blocker-triggered quest activation pathway.

Ticket: TCK-20260627-P1B-QUEST-ACTIVATION
Parity: STRAT-235

Tests that:
  - QuestGenerationSystem.generate_from_blockers() produces quest templates for material blockers
  - QuestGenerationSystem.quest_to_project() produces a ProjectState with the first objective
    in ObjectiveStatus.ACTIVE (so StrategicIntelligenceSystem can navigate/resolve it)
  - The quest project is accepted by StrategicIntelligenceSystem.evaluate_project_switch()
"""
from __future__ import annotations

import pytest
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.strategic import (
    BlockerState,
    ProjectStatus,
    ObjectiveStatus,
)
from src.systems.world_systems.quests import QuestGenerationSystem
from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entity_with_material_blocker(subject: str = "iron_ore"):
    """Return an entity that has one unresolved material blocker."""
    blocker = BlockerState(
        id=f"blocker_mat_{subject}",
        kind="material",
        subject=subject,
        severity=1.0,
    )
    return (
        V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .identity(class_id="hero")
        .strategic(blockers={blocker.id: blocker})
        .build()
    )


def _entity_with_only_non_triggering_blockers():
    """Return an entity whose blockers should NOT produce quest templates."""
    resolved_blocker = BlockerState(
        id="blocker_mat_gold",
        kind="material",
        subject="gold",
        severity=1.0,
        resolved=True,
    )
    access_blocker = BlockerState(
        id="blocker_access_wall",
        kind="access",
        subject="(5.0, 5.0)",
        severity=0.8,
    )
    return (
        V2EntityBuilder(2)
        .kind("hero")
        .location(0, 0)
        .identity(class_id="hero")
        .strategic(
            blockers={
                resolved_blocker.id: resolved_blocker,
                access_blocker.id: access_blocker,
            }
        )
        .build()
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGenerateFromBlockers:
    def test_returns_quest_template_for_material_blocker(self):
        """AC1/AC2: material blocker → non-empty quest template list."""
        entity = _entity_with_material_blocker("iron_ore")
        templates = QuestGenerationSystem.generate_from_blockers(entity, current_tick=100)

        assert len(templates) >= 1, "Expected at least one quest template for a material blocker"
        t = templates[0]
        assert t.kind == "resource_expedition"
        assert len(t.objectives) >= 1

    def test_template_targets_blocked_resource(self):
        """Objectives in the template should target the blocked resource."""
        entity = _entity_with_material_blocker("wood")
        templates = QuestGenerationSystem.generate_from_blockers(entity, current_tick=50)

        assert templates, "Expected at least one quest template"
        obj = templates[0].objectives[0]
        assert obj.target == "wood", (
            f"Expected objective target 'wood', got '{obj.target}'"
        )

    def test_skips_resolved_and_non_material_blockers(self):
        """Resolved blockers and non-material blockers must not generate quest templates."""
        entity = _entity_with_only_non_triggering_blockers()
        templates = QuestGenerationSystem.generate_from_blockers(entity, current_tick=100)

        assert templates == [], (
            f"Expected empty template list for resolved/non-material blockers, got {templates}"
        )

    def test_no_blockers_returns_empty(self):
        """Entity with no blockers produces no quest templates."""
        entity = (
            V2EntityBuilder(3)
            .kind("hero")
            .location(0, 0)
            .identity(class_id="hero")
            .build()
        )
        templates = QuestGenerationSystem.generate_from_blockers(entity, current_tick=200)
        assert templates == []


class TestQuestToProject:
    def _make_project(self, subject: str = "iron_ore", tick: int = 100):
        entity = _entity_with_material_blocker(subject)
        templates = QuestGenerationSystem.generate_from_blockers(entity, current_tick=tick)
        assert templates, "Prerequisite: need at least one template"
        return QuestGenerationSystem.quest_to_project(templates[0], tick)

    def test_project_kind_is_quest(self):
        project = self._make_project()
        assert project.kind == "quest"

    def test_project_status_is_active(self):
        project = self._make_project()
        assert project.status == ProjectStatus.ACTIVE

    def test_active_objective_id_is_set(self):
        project = self._make_project()
        assert project.active_objective_id is not None

    def test_first_objective_has_active_status(self):
        """Bug-fix regression guard (STRAT-235).

        The first objective must be ACTIVE, not UNRESOLVED. If UNRESOLVED,
        fused_strategic_pass() cannot drive navigation or blocker resolution.
        """
        project = self._make_project()
        assert project.objectives, "Project must have at least one objective"
        first_obj = project.objectives[0]
        assert first_obj.status == ObjectiveStatus.ACTIVE, (
            f"First quest objective must be ACTIVE for strategic processing; "
            f"got {first_obj.status!r}. "
            f"fused_strategic_pass() only processes objectives with status==ACTIVE."
        )

    def test_active_objective_id_points_to_active_objective(self):
        """active_objective_id must reference the ACTIVE objective."""
        project = self._make_project()
        target = next(
            (o for o in project.objectives if o.id == project.active_objective_id),
            None,
        )
        assert target is not None, "active_objective_id references a non-existent objective"
        assert target.status == ObjectiveStatus.ACTIVE, (
            f"Objective referenced by active_objective_id has status {target.status!r}, expected ACTIVE"
        )

    def test_subsequent_objectives_are_unresolved(self):
        """Objectives after the first should remain UNRESOLVED (not yet active)."""
        entity = _entity_with_material_blocker("iron_ore")
        # Inject a second blocker to guarantee multiple objectives
        blocker2 = BlockerState(
            id="blocker_mat_wood",
            kind="material",
            subject="wood",
            severity=0.8,
        )
        entity = replace(
            entity,
            strategic=replace(
                entity.strategic,
                blockers={**entity.strategic.blockers, blocker2.id: blocker2},
            ),
        )
        templates = QuestGenerationSystem.generate_from_blockers(entity, current_tick=100)
        # Use the template that has the most objectives (both blockers may produce single-obj templates)
        # Pick any template that actually has >1 objective, or confirm single-obj templates are fine
        for t in templates:
            project = QuestGenerationSystem.quest_to_project(t, 100)
            for i, obj in enumerate(project.objectives):
                if i == 0:
                    assert obj.status == ObjectiveStatus.ACTIVE
                else:
                    assert obj.status == ObjectiveStatus.UNRESOLVED


class TestQuestActivationPathwayEndToEnd:
    def test_quest_project_accepted_by_evaluate_project_switch(self):
        """
        AC1/AC2: Full end-to-end pathway.

        entity has material gap
        → generate_from_blockers() returns template
        → quest_to_project() returns valid ProjectState
        → evaluate_project_switch() accepts it as the new current project

        Exercises src/systems/world_systems/quests.py and
        src/systems/strategic_systems/intelligence.py together.
        """
        entity = _entity_with_material_blocker("iron_ore")
        tick = 100

        # Generate blocker-triggered quest
        templates = QuestGenerationSystem.generate_from_blockers(entity, current_tick=tick)
        assert templates, "Prerequisite: generate_from_blockers must return at least one template"

        quest_project = QuestGenerationSystem.quest_to_project(templates[0], tick)
        assert quest_project.kind == "quest"
        assert quest_project.status == ProjectStatus.ACTIVE

        # Entity has no current project — switch should be accepted
        switch_update = StrategicIntelligenceSystem.evaluate_project_switch(
            entity, quest_project, tick
        )
        assert switch_update is not None, (
            "evaluate_project_switch() must accept the quest project when entity has no current project"
        )
        assert switch_update.current_project_id_set == quest_project.id
        assert quest_project in switch_update.projects_add_or_update

    def test_quest_project_beats_low_score_project_in_switch(self):
        """Quest project with higher score displaces a low-score current project."""
        from src.core.strategic import ProjectState as PS, ObjectiveState, ObjectiveStatus as OS

        low_score_proj = PS(
            id="proj_low",
            kind="harvesting",
            status=ProjectStatus.ACTIVE,
            score=5.0,
            lock_until_tick=0,
            created_tick=50,
        )
        entity = (
            V2EntityBuilder(10)
            .kind("hero")
            .location(0, 0)
            .identity(class_id="hero")
            .strategic(
                projects={"proj_low": low_score_proj},
                current_project_id="proj_low",
            )
            .build()
        )
        blocker = BlockerState(
            id="blocker_mat_iron_ore",
            kind="material",
            subject="iron_ore",
            severity=1.0,
        )
        entity = replace(
            entity,
            strategic=replace(
                entity.strategic,
                blockers={blocker.id: blocker},
            ),
        )

        templates = QuestGenerationSystem.generate_from_blockers(entity, current_tick=100)
        assert templates

        quest_project = QuestGenerationSystem.quest_to_project(templates[0], 100)
        # Difficulty=1.0 → score=60.0, which beats the low_score_proj at 5.0
        assert quest_project.score > low_score_proj.score, (
            f"quest_project.score={quest_project.score} must exceed low_score_proj.score={low_score_proj.score}"
        )

        switch_update = StrategicIntelligenceSystem.evaluate_project_switch(
            entity, quest_project, current_tick=100
        )
        assert switch_update is not None, (
            "Quest project with higher score must displace a lower-score current project"
        )
        assert switch_update.current_project_id_set == quest_project.id
