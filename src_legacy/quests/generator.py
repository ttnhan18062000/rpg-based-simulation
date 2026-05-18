from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set

from src_legacy.core.quests import QuestState, QuestKind, QuestStatus, RewardState
from src_legacy.core.state import EntityState

@dataclass(frozen=True, slots=True)
class QuestTemplate:
    id: str
    name: str
    kind: QuestKind
    min_level: int
    max_level: int
    base_goal: float
    base_xp: int
    base_gold: int
    items: List[str] = field(default_factory=list)

class QuestGenerator:
    """
    Deterministic quest generator based on hero level and world state.
    """
    
    TEMPLATES = [
        # TIER 1: Levels 1-5
        QuestTemplate("q_slime_cull", "Clear the Slimes", QuestKind.HUNT, 1, 5, 5.0, 100, 50),
        QuestTemplate("q_wood_survey", "Survey the Woods", QuestKind.EXPLORE, 1, 8, 1.0, 80, 30),
        
        # TIER 2: Levels 6-10
        QuestTemplate("q_wolf_hunt", "Wolf Cull", QuestKind.HUNT, 6, 12, 8.0, 300, 150),
        QuestTemplate("q_herb_gather", "Gather Herbs", QuestKind.GATHER, 4, 10, 5.0, 200, 100),
        
        # TIER 3: Levels 11+
        QuestTemplate("q_bandit_bounty", "Bounty: Bandit Leader", QuestKind.BOUNTY, 11, 100, 1.0, 1000, 500, ["iron_sword"]),
        QuestTemplate("q_camp_liberate", "Liberate the Outpost", QuestKind.LIBERATE, 15, 100, 1.0, 2500, 1200, ["leather_armor"]),
    ]

    @staticmethod
    def generate(seed: int, level: int, tick: int, existing_ids: Set[str] | None = None) -> Optional[QuestState]:
        """
        Generate a level-appropriate quest deterministically.
        """
        # 1. Filter by level band
        candidates = [t for t in QuestGenerator.TEMPLATES if t.min_level <= level <= t.max_level]
        if existing_ids:
            candidates = [t for t in candidates if t.id not in existing_ids]
            
        if not candidates:
            return None
            
        # 2. Select template using seed + tick + level
        rng = random.Random(seed + tick + level)
        template = rng.choice(candidates)
        
        # 3. Scale rewards and goal
        # Linear scaling for now: 10% increase per level above min_level
        scale_factor = 1.0 + (level - template.min_level) * 0.1
        
        scaled_goal = round(template.base_goal * (1.0 + (level - template.min_level) * 0.05), 1)
        scaled_xp = int(template.base_xp * scale_factor)
        scaled_gold = int(template.base_gold * scale_factor)
        
        # 4. Build QuestState
        # ID is template_id + tick to ensure uniqueness if needed, 
        # but in strategic state we use ID as key.
        quest_id = f"{template.id}_{tick}"
        
        return QuestState(
            id=quest_id,
            kind="quest",
            quest_kind=template.kind,
            quest_status=QuestStatus.ACTIVE,
            goal_value=scaled_goal,
            current_value=0.0,
            reward=RewardState(
                xp=scaled_xp,
                gold=scaled_gold,
                items=list(template.items)
            ),
            name=template.name,
            created_tick=tick
        )

    @staticmethod
    def generate_quests(seed: int, level: int, tick: int, building_id: int, count: int = 1) -> List[QuestState]:
        """Generate multiple quests for a building."""
        quests = []
        for i in range(count):
            q = QuestGenerator.generate(seed + i, level, tick)
            if q:
                # Add source info
                q = q.replace(source_building_id=building_id)
                quests.append(q)
        return quests
