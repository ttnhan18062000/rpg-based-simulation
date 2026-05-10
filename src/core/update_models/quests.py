from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.quests import QuestStatus

@dataclass(frozen=True, slots=True)
class QuestUpdate:
    """Updates to quest progress and status."""
    quest_id: str
    progress_delta: float = 0.0
    status_set: Optional[QuestStatus] = None
    multi_updates: List[QuestUpdate] = field(default_factory=list)
    def merge(self, other: 'QuestUpdate') -> 'QuestUpdate':
        from dataclasses import replace
        from typing import Dict
        
        # 1. If either is "MULTI", we need to handle list merging
        if self.quest_id == "MULTI" or other.quest_id == "MULTI":
            my_updates = self.multi_updates if self.quest_id == "MULTI" else [replace(self, multi_updates=[])]
            their_updates = other.multi_updates if other.quest_id == "MULTI" else [replace(other, multi_updates=[])]
            
            # Merge by ID
            by_id: Dict[str, QuestUpdate] = {}
            for qu in my_updates + their_updates:
                if qu.quest_id in by_id:
                    by_id[qu.quest_id] = by_id[qu.quest_id].merge(qu)
                else:
                    by_id[qu.quest_id] = qu
            
            # If only one quest type remains, return it as a single update
            if len(by_id) == 1:
                return list(by_id.values())[0]
            
            # Otherwise return a MULTI update
            return replace(self, quest_id="MULTI", multi_updates=list(by_id.values()), progress_delta=0.0)
            
        # 2. Both are single-quest updates. If same ID, sum deltas.
        if self.quest_id == other.quest_id:
            return replace(self,
                progress_delta=self.progress_delta + other.progress_delta,
                status_set=other.status_set if other.status_set is not None else self.status_set
            )
            
        # 3. Different IDs, create a MULTI update
        return replace(self, quest_id="MULTI", multi_updates=[
            replace(self, multi_updates=[]),
            replace(other, multi_updates=[])
        ], progress_delta=0.0)
