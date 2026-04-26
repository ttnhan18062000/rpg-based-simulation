"""
Dynamic Quest Generation System.

Generates quest objectives from environmental state (scars, blockers).

Covers:
- LEG-RPG-141: Dynamic Quests
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from src.core.state import EntityState, RegionState
from src.core.strategic import (
    ProjectState, ProjectStatus, ObjectiveState, ObjectiveStatus,
    BlockerState
)
from src.core.updates import StrategicUpdate


@dataclass(frozen=True, slots=True)
class QuestObjective:
    """A typed quest objective."""
    id: str
    kind: str  # 'investigate', 'clear_threat', 'gather', 'escort', 'deliver'
    target: str
    description: str = ""
    reward_gold: int = 0
    reward_xp: int = 0


@dataclass(frozen=True, slots=True)
class QuestTemplate:
    """A generated quest template."""
    id: str
    kind: str  # 'scar_investigation', 'resource_expedition', 'blocker_resolution'
    title: str
    objectives: List[QuestObjective] = field(default_factory=list)
    difficulty: float = 0.5
    region_id: Optional[str] = None


class QuestGenerationSystem:
    """
    Generates quests from environmental and strategic state.
    Does NOT mutate state — returns quest templates for evaluation.
    """

    @staticmethod
    def generate_from_scar(
        region: RegionState,
        current_tick: int
    ) -> Optional[QuestTemplate]:
        """
        LEG-RPG-141: Quest generation from scar/trauma state.
        Regions with high trauma generate investigation quests.
        """
        if region.trauma_score <= 0.3:
            return None

        quest_id = f"quest_scar_{region.id}_{current_tick}"
        objectives = [
            QuestObjective(
                id=f"{quest_id}_obj_investigate",
                kind="investigate",
                target=region.id,
                description=f"Investigate the scarred region of {region.name}",
                reward_gold=int(region.trauma_score * 100),
                reward_xp=int(region.trauma_score * 50)
            )
        ]

        if region.hazard_level > 0.5:
            objectives.append(QuestObjective(
                id=f"{quest_id}_obj_clear",
                kind="clear_threat",
                target=region.id,
                description=f"Clear the hazards in {region.name}",
                reward_gold=int(region.hazard_level * 150),
                reward_xp=int(region.hazard_level * 80)
            ))

        return QuestTemplate(
            id=quest_id,
            kind="scar_investigation",
            title=f"Investigation: {region.name} Scarring",
            objectives=objectives,
            difficulty=region.trauma_score,
            region_id=region.id
        )

    @staticmethod
    def generate_from_blockers(
        entity: EntityState,
        current_tick: int
    ) -> List[QuestTemplate]:
        """
        LEG-RPG-141: Quest generation from strategic blockers.
        Material blockers generate resource expedition quests.
        """
        quests = []

        for blocker in entity.strategic.blockers.values():
            if blocker.resolved:
                continue
            if blocker.kind != "material":
                continue

            quest_id = f"quest_resource_{blocker.subject}_{current_tick}"
            quest = QuestTemplate(
                id=quest_id,
                kind="resource_expedition",
                title=f"Expedition: Acquire {blocker.subject}",
                objectives=[
                    QuestObjective(
                        id=f"{quest_id}_obj_gather",
                        kind="gather",
                        target=blocker.subject,
                        description=f"Find and acquire {blocker.subject}",
                        reward_gold=50,
                        reward_xp=25
                    )
                ],
                difficulty=blocker.severity
            )
            quests.append(quest)

        return quests

    @staticmethod
    def quest_to_project(quest: QuestTemplate, current_tick: int) -> ProjectState:
        """Convert a quest template to a strategic project."""
        objectives = [
            ObjectiveState(
                id=obj.id,
                kind=obj.kind,
                target=obj.target,
                status=ObjectiveStatus.UNRESOLVED
            )
            for obj in quest.objectives
        ]

        return ProjectState(
            id=quest.id,
            kind="quest",
            status=ProjectStatus.ACTIVE,
            score=quest.difficulty * 60,
            objectives=objectives,
            active_objective_id=objectives[0].id if objectives else None,
            created_tick=current_tick
        )
