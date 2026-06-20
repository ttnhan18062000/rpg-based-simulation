from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Dict, Any, List, Tuple, TYPE_CHECKING
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
    REWARD_PENDING = 4

class QuestOpportunityStatus(str, Enum):
    OFFERED = "OFFERED"
    ACTIVE = "ACTIVE"
    PROGRESSED = "PROGRESSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"

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


@dataclass(frozen=True, slots=True)
class QuestOpportunity:
    """
    A world-level quest opportunity derived from pressure signals (RESOURCE_DEPLETED,
    high-severity threat events). Read-only — never written to quest_registry here.
    Lifecycle registration is E23B's responsibility.

    id: deterministic — f"{kind}_{source_event_id}_{tick % 10000}"
    """
    id: str
    kind: str                          # "resource_crisis" | "threat_response" | "diplomatic_errand"
    trigger_condition: str             # human-readable description of the triggering condition
    objective_chain: Tuple[str, ...]   # ordered objective tokens e.g. ("fetch:iron_ore:3",)
    reward_spec: Dict[str, Any]        # {"gold": int, "xp": int, "faction_rep": float}
    faction_source: Optional[str]      # faction offering the quest; None = world event
    expiry_ticks: int                  # tick at which this opportunity expires if not taken
    source_event_id: Optional[str]     # ID of the WorldEvent that triggered this opportunity
    status: QuestOpportunityStatus = QuestOpportunityStatus.OFFERED
