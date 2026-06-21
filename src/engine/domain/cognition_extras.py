"""
src/engine/domain/cognition_extras.py
───────────────────────────────────────────────────────────────────────────────
Epic 4.2A — InformationNeed detector.

Converts high-priority UnknownFact entries (priority > SEEKING_THRESHOLD, not
yet linked to a seeking project) into a StrategicUpdate that creates an
INFORMATION_SEEKING ProjectState with an ASK_INFORMATION objective.

Design:
  - Pure static class: reads entity state, returns Optional[StrategicUpdate].
  - No direct state writes; all durable changes go through StrategicUpdate.
  - Deterministic: depends only on entity state and tick (no randomness).

Wire-up: call detect_and_generate() in CognitionDomain.execute_brain() after
existing project evaluation and before route scoring.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from src.core.strategic import (
    ObjectiveKind,
    ObjectiveState,
    ObjectiveStatus,
    ProjectKind,
    ProjectState,
    ProjectStatus,
)
from src.core.updates import StrategicUpdate

if TYPE_CHECKING:
    from src.core.state import EntityState


class InformationNeedDetector:
    """
    Detects high-priority UnknownFact entries and generates an
    INFORMATION_SEEKING project for the most urgent one.

    Logic ID: E42A-001
    """

    SEEKING_THRESHOLD: float = 0.5

    @staticmethod
    def detect_and_generate(
        entity: "EntityState",
        tick: int,
    ) -> Optional[StrategicUpdate]:
        """
        Scan entity.self_model.knowledge.unknowns for candidates.

        A candidate is an UnknownFact where:
          - priority > SEEKING_THRESHOLD (strictly greater)
          - seeking_project_id is None (not already linked to a project)

        Returns a StrategicUpdate with one INFORMATION_SEEKING ProjectState
        (highest-priority candidate), or None if no candidates exist.
        """
        knowledge = entity.self_model.knowledge
        if not knowledge.unknowns:
            return None

        candidates = [
            uf
            for uf in knowledge.unknowns.values()
            if uf.priority > InformationNeedDetector.SEEKING_THRESHOLD
            and uf.seeking_project_id is None
        ]

        if not candidates:
            return None

        # Pick the highest-priority unknown; break ties by subject for determinism.
        best = max(candidates, key=lambda uf: (uf.priority, uf.subject))

        proj_id = f"info_seek_{best.subject}_{tick}"
        obj_id = f"ask_{best.subject}_{tick}"

        objective = ObjectiveState(
            id=obj_id,
            kind=ObjectiveKind.ASK_INFORMATION,
            target=best.subject,
            status=ObjectiveStatus.ACTIVE,
        )

        project = ProjectState(
            id=proj_id,
            kind=ProjectKind.INFORMATION_SEEKING,
            status=ProjectStatus.ACTIVE,
            objectives=[objective],
            active_objective_id=obj_id,
            created_tick=tick,
            score=best.priority * 100.0,  # scale to be comparable with goal scorer utilities
        )

        return StrategicUpdate(projects_add_or_update=[project])
