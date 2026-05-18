from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List
from src_legacy.core.quests import QuestKind

@dataclass(frozen=True)
class QuestTemplate:
    kind: QuestKind
    base_name: str
    base_goal: float
    base_xp: int
    base_gold: int
    subject_options: List[str]

QUEST_TEMPLATES: Dict[QuestKind, QuestTemplate] = {
    QuestKind.HUNT: QuestTemplate(
        kind=QuestKind.HUNT,
        base_name="Hunt {subject}",
        base_goal=5.0,
        base_xp=100,
        base_gold=50,
        subject_options=["Wolf", "Goblin", "Spider", "Slime"]
    ),
    QuestKind.GATHER: QuestTemplate(
        kind=QuestKind.GATHER,
        base_name="Gather {subject}",
        base_goal=10.0,
        base_xp=80,
        base_gold=40,
        subject_options=["Herb", "Wood", "Iron", "Berry"]
    ),
    QuestKind.EXPLORE: QuestTemplate(
        kind=QuestKind.EXPLORE,
        base_name="Explore {subject}",
        base_goal=1.0,
        base_xp=150,
        base_gold=20,
        subject_options=["Deep Cave", "Ancient Ruin", "Forbidden Grove"]
    ),
}
