from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Dict, Any, List
from src.core.strategic import ProjectState

class QuestKind(Enum):
    HUNT = auto()
    GATHER = auto()
    EXPLORE = auto()
    LIBERATE = auto()
    BOUNTY = auto()

class QuestStatus(Enum):
    ACTIVE = 1
    COMPLETED = 2
    REWARDED = 3

@dataclass(frozen=True, slots=True)
class RewardState:
    xp: int = 0
    gold: int = 0
    items: List[str] = field(default_factory=list) # Item Template IDs

@dataclass(frozen=True, slots=True)
class QuestState(ProjectState):
    """
    Quest is a specialized ProjectState with a goal and status.
    """
    # Inherits: id, kind, status, score, lock_until_tick, objectives, active_objective_id, created_tick
    quest_kind: QuestKind = QuestKind.HUNT
    quest_status: QuestStatus = QuestStatus.ACTIVE
    goal_value: float = 0.0
    current_value: float = 0.0
    reward: RewardState = field(default_factory=RewardState)
    source_building_id: Optional[int] = None
    source_entity_id: Optional[int] = None
    name: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def replace(self, **kwargs) -> QuestState:
        from dataclasses import replace
        return replace(self, **kwargs)

    @property
    def progress_ratio(self) -> float:
        if self.goal_value <= 0:
            return 1.0
        return min(1.0, self.current_value / self.goal_value)
    
    @property
    def is_finished(self) -> bool:
        return self.current_value >= self.goal_value
