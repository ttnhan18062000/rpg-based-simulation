from __future__ import annotations
from dataclasses import dataclass, field, replace
from typing import List, Optional, TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from src.core.quests import QuestStatus

@dataclass(frozen=True, slots=True)
class QuestUpdate:
    """Updates to quest progress and status."""
    quest_id: str
    progress_delta: float = 0.0
    status_set: Optional[QuestStatus] = None
    multi_updates: List[QuestUpdate] = field(default_factory=list)

    def merge(self, other: QuestUpdate) -> QuestUpdate:
        """
        M10 Law: Quest updates must merge deterministically.
        If merging different quest IDs, produces a 'MULTI' update container.
        """
        if not other:
            return self
        
        # Flattening logic: if either is MULTI, we take their constituents.
        # This prevents QuestUpdate(MULTI, [QuestUpdate(MULTI, ...)]) nesting.
        my_constituents = self.multi_updates if self.quest_id == "MULTI" else [self]
        their_constituents = other.multi_updates if other.quest_id == "MULTI" else [other]
        
        by_id: Dict[str, QuestUpdate] = {}
        
        for qu in my_constituents + their_constituents:
            # Skip any recursive MULTI that might have leaked in
            if qu.quest_id == "MULTI":
                for sub_qu in qu.multi_updates:
                    if sub_qu.quest_id in by_id:
                        by_id[sub_qu.quest_id] = by_id[sub_qu.quest_id].merge(sub_qu)
                    else:
                        by_id[sub_qu.quest_id] = sub_qu
                continue

            if qu.quest_id in by_id:
                # Merge individual quest updates
                current = by_id[qu.quest_id]
                # If both are non-MULTI and same ID, merge them
                by_id[qu.quest_id] = replace(current,
                    progress_delta=current.progress_delta + qu.progress_delta,
                    status_set=qu.status_set if qu.status_set is not None else current.status_set,
                    multi_updates=[]
                )
            else:
                # Ensure child is not marked as MULTI and has no children of its own
                by_id[qu.quest_id] = replace(qu, multi_updates=[])
        
        # If only one quest ID exists after merge, return it directly instead of MULTI
        if len(by_id) == 1:
            return next(iter(by_id.values()))
            
        return replace(self, 
            quest_id="MULTI", 
            multi_updates=sorted(list(by_id.values()), key=lambda x: x.quest_id), 
            progress_delta=0.0,
            status_set=None
        )

    def is_noop(self) -> bool:
        if self.quest_id == "MULTI":
            return not self.multi_updates or all(qu.is_noop() for qu in self.multi_updates)
        return self.progress_delta == 0.0 and self.status_set is None
