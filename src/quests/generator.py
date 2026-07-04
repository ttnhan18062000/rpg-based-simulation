from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set

from src.core.quests import QuestState, QuestKind, QuestStatus, RewardState
from src.core.state import EntityState
from src.core.enums import Domain
from src.platform.rng import DeterministicRNG

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

@dataclass(frozen=True, slots=True)
class QuestPressureProfile:
    """
    Ephemeral, read-time-derived pressure signals used to WEIGHT (never gate) quest
    template selection. Computed fresh on every GuildAction.visit() call from durable
    RegionState/ResourceNodeState fields -- this profile itself is never persisted
    (mirrors how `Opportunity` in src/world/providers/resources.py is a derived
    read-model, not durable state; see docs/mechanics/05_world_evolution.md for the
    underlying durable trauma/hazard fields and the "Derived Scarcity Ratio"
    subsection for the scarcity-ratio formula).

    All fields are conventionally in [0.0, 1.0]. The all-zero default is the neutral
    profile: it must reduce selection to today's exact uniform rng.choice() behavior
    (see QuestGenerator.generate()'s "collapse to legacy path" check).
    """
    trauma: float = 0.0
    hazard: float = 0.0
    scarcity: float = 0.0

# Maps each QuestKind to the QuestPressureProfile field it is weighted by.
# EXPLORE has no directional pressure driver -- it stays at baseline weight,
# which is also what keeps a genuinely neutral profile perfectly uniform.
PRESSURE_AFFINITY: Dict[QuestKind, str] = {
    QuestKind.HUNT: "trauma",
    QuestKind.BOUNTY: "trauma",
    QuestKind.LIBERATE: "hazard",
    QuestKind.GATHER: "scarcity",
    QuestKind.EXPLORE: "none",
}
PRESSURE_WEIGHT_SCALE = 2.0  # max additive bonus at signal strength 1.0

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
    def _pressure_weight(template: "QuestTemplate", profile: Optional["QuestPressureProfile"]) -> float:
        if profile is None:
            return 1.0
        signal_name = PRESSURE_AFFINITY.get(template.kind, "none")
        if signal_name == "none":
            return 1.0
        signal_value = getattr(profile, signal_name, 0.0)
        return 1.0 + PRESSURE_WEIGHT_SCALE * max(0.0, min(1.0, signal_value))

    @staticmethod
    def generate(
        seed: int,
        level: int,
        tick: int,
        existing_ids: Set[str] | None = None,
        pressure_profile: Optional["QuestPressureProfile"] = None,
    ) -> Optional[QuestState]:
        """
        Generate a level-appropriate quest deterministically.
        """
        # 1. Filter by level band
        candidates = [t for t in QuestGenerator.TEMPLATES if t.min_level <= level <= t.max_level]
        if existing_ids:
            candidates = [t for t in candidates if t.id not in existing_ids]

        if not candidates:
            return None

        # 2. Select template using DeterministicRNG.
        rng = DeterministicRNG(seed)
        weights = [QuestGenerator._pressure_weight(t, pressure_profile) for t in candidates]

        # Collapse-to-legacy-path guarantee: when the profile is None, or every candidate
        # resolves to the same weight (neutral profile, or a level band where no candidate's
        # QuestKind has a live pressure affinity), draw with the exact same rng.choice() call
        # as before this ticket -- byte-identical distribution, not just "approximately
        # uniform." Only diverge to the weighted draw when pressure actually differentiates
        # the candidates.
        if pressure_profile is None or len(set(weights)) == 1:
            template = rng.choice(Domain.QUEST, tick, level, candidates)
        else:
            template = rng.weighted_choice(Domain.QUEST, tick, level, candidates, weights)

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
    def generate_quests(
        seed: int,
        level: int,
        tick: int,
        building_id: int,
        count: int = 1,
        pressure_profile: Optional["QuestPressureProfile"] = None,
    ) -> List[QuestState]:
        """Generate multiple quests for a building."""
        quests = []
        for i in range(count):
            q = QuestGenerator.generate(seed + i, level, tick, pressure_profile=pressure_profile)
            if q:
                # Add source info
                q = q.replace(source_building_id=building_id)
                quests.append(q)
        return quests
