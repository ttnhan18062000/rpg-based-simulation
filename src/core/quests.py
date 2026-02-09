"""Quest system — generation, tracking, and completion for heroes.

Quest types:
  - HUNT: Kill N enemies of a specific kind.
  - EXPLORE: Visit a specific map coordinate.
  - GATHER: Collect N of a specific item.

Quests are generated at the Guild building and tracked per-entity.
Completion awards gold, XP, and optionally items.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum, unique
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.models import Vector2
    from src.systems.rng import DeterministicRNG


# ---------------------------------------------------------------------------
# Quest type enum
# ---------------------------------------------------------------------------

@unique
class QuestType(IntEnum):
    HUNT = 0       # Kill N enemies of a kind
    EXPLORE = 1    # Visit a map tile
    GATHER = 2     # Collect N items


# ---------------------------------------------------------------------------
# Quest data model
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class Quest:
    """A single quest tracked on a hero."""

    quest_id: str              # Unique identifier, e.g. "hunt_goblin_3"
    quest_type: QuestType
    title: str
    description: str
    # Target specification
    target_kind: str = ""      # Enemy kind for HUNT, item_id for GATHER
    target_pos: Vector2 | None = None  # For EXPLORE
    target_count: int = 1      # How many to kill/collect
    # Progress
    progress: int = 0
    completed: bool = False
    # Rewards
    gold_reward: int = 0
    xp_reward: int = 0
    item_reward: str = ""      # Optional item_id reward

    @property
    def progress_ratio(self) -> float:
        if self.target_count <= 0:
            return 1.0
        return min(self.progress / self.target_count, 1.0)

    def advance(self, amount: int = 1) -> bool:
        """Advance quest progress. Returns True if quest just completed."""
        if self.completed:
            return False
        self.progress = min(self.progress + amount, self.target_count)
        if self.progress >= self.target_count:
            self.completed = True
            return True
        return False

    def copy(self) -> Quest:
        return Quest(
            quest_id=self.quest_id,
            quest_type=self.quest_type,
            title=self.title,
            description=self.description,
            target_kind=self.target_kind,
            target_pos=self.target_pos,
            target_count=self.target_count,
            progress=self.progress,
            completed=self.completed,
            gold_reward=self.gold_reward,
            xp_reward=self.xp_reward,
            item_reward=self.item_reward,
        )

    def to_dict(self) -> dict:
        d: dict = {
            "quest_id": self.quest_id,
            "quest_type": self.quest_type.name,
            "title": self.title,
            "description": self.description,
            "target_kind": self.target_kind,
            "target_count": self.target_count,
            "progress": self.progress,
            "completed": self.completed,
            "gold_reward": self.gold_reward,
            "xp_reward": self.xp_reward,
            "item_reward": self.item_reward,
        }
        if self.target_pos is not None:
            d["target_x"] = self.target_pos.x
            d["target_y"] = self.target_pos.y
        return d


# ---------------------------------------------------------------------------
# Quest templates — used by the generator
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class QuestTemplate:
    """Blueprint for generating quests."""
    template_id: str
    quest_type: QuestType
    title_fmt: str             # Python format string, e.g. "Hunt {count} {kind}"
    desc_fmt: str
    target_kinds: list[str]    # Possible target kinds/items
    count_range: tuple[int, int] = (1, 5)
    gold_range: tuple[int, int] = (20, 100)
    xp_range: tuple[int, int] = (30, 150)
    min_level: int = 1


QUEST_TEMPLATES: list[QuestTemplate] = [
    # Hunt quests
    QuestTemplate(
        "hunt_goblin", QuestType.HUNT,
        "Hunt {count} {kind}s", "Track down and eliminate {count} {kind}s terrorizing the region.",
        ["goblin", "goblin_scout", "goblin_warrior"],
        count_range=(2, 6), gold_range=(25, 80), xp_range=(40, 120),
    ),
    QuestTemplate(
        "hunt_wolf", QuestType.HUNT,
        "Cull {count} {kind}s", "The wolf population is growing. Cull {count} {kind}s.",
        ["wolf", "dire_wolf"],
        count_range=(2, 5), gold_range=(20, 60), xp_range=(30, 100),
    ),
    QuestTemplate(
        "hunt_bandit", QuestType.HUNT,
        "Eliminate {count} {kind}s", "Bandits have been raiding travelers. Eliminate {count} of them.",
        ["bandit", "bandit_archer", "bandit_chief"],
        count_range=(2, 5), gold_range=(30, 90), xp_range=(50, 130),
        min_level=2,
    ),
    QuestTemplate(
        "hunt_undead", QuestType.HUNT,
        "Purge {count} {kind}s", "Undead creatures stir in the swamps. Purge {count} {kind}s.",
        ["skeleton", "zombie"],
        count_range=(2, 5), gold_range=(35, 100), xp_range=(50, 140),
        min_level=3,
    ),
    QuestTemplate(
        "hunt_orc", QuestType.HUNT,
        "Defeat {count} {kind}s", "Orcs from the mountains threaten the realm. Defeat {count}.",
        ["orc", "orc_warrior"],
        count_range=(1, 4), gold_range=(50, 150), xp_range=(80, 200),
        min_level=4,
    ),
    # Gather quests
    QuestTemplate(
        "gather_herbs", QuestType.GATHER,
        "Gather {count} herbs", "The apothecary needs {count} herbs for potions.",
        ["herb"],
        count_range=(3, 8), gold_range=(15, 50), xp_range=(20, 60),
    ),
    QuestTemplate(
        "gather_ore", QuestType.GATHER,
        "Collect {count} iron ore", "The blacksmith needs raw materials.",
        ["iron_ore"],
        count_range=(2, 5), gold_range=(30, 80), xp_range=(30, 80),
        min_level=2,
    ),
    QuestTemplate(
        "gather_pelts", QuestType.GATHER,
        "Collect {count} wolf pelts", "The tanner needs wolf pelts for crafting.",
        ["wolf_pelt"],
        count_range=(2, 4), gold_range=(25, 60), xp_range=(25, 70),
    ),
    # Explore quests (target_pos filled at generation time)
    QuestTemplate(
        "explore_region", QuestType.EXPLORE,
        "Scout the frontier", "Explore an uncharted area of the map and report back.",
        [],
        count_range=(1, 1), gold_range=(20, 60), xp_range=(30, 80),
    ),
]

TEMPLATE_MAP: dict[str, QuestTemplate] = {t.template_id: t for t in QUEST_TEMPLATES}


# ---------------------------------------------------------------------------
# Quest generation
# ---------------------------------------------------------------------------

MAX_ACTIVE_QUESTS = 3  # Max quests a hero can hold at once


def generate_quest(
    hero_level: int,
    existing_quest_ids: set[str],
    rng: DeterministicRNG,
    grid_width: int = 100,
    grid_height: int = 100,
) -> Quest | None:
    """Generate a random quest appropriate for the hero's level.

    Returns None if no suitable template is available.
    """
    from src.core.models import Vector2

    eligible = [t for t in QUEST_TEMPLATES if hero_level >= t.min_level]
    if not eligible:
        return None

    # Shuffle and pick first non-duplicate
    rng_val = rng.next()
    idx = rng_val % len(eligible)
    template = eligible[idx]

    # Pick target kind
    if template.target_kinds:
        kind_idx = rng.next() % len(template.target_kinds)
        target_kind = template.target_kinds[kind_idx]
    else:
        target_kind = ""

    # Determine count
    lo, hi = template.count_range
    count = lo + (rng.next() % max(1, hi - lo + 1))

    # Build quest ID
    suffix = target_kind or "explore"
    quest_id = f"{template.template_id}_{suffix}_{count}"

    # Skip if hero already has this exact quest
    if quest_id in existing_quest_ids:
        return None

    # Gold and XP rewards scale with count and level
    g_lo, g_hi = template.gold_range
    gold = g_lo + (rng.next() % max(1, g_hi - g_lo + 1))
    gold = int(gold * (1.0 + hero_level * 0.1))

    x_lo, x_hi = template.xp_range
    xp = x_lo + (rng.next() % max(1, x_hi - x_lo + 1))
    xp = int(xp * (1.0 + hero_level * 0.1))

    # Format title and description
    kind_display = target_kind.replace("_", " ")
    title = template.title_fmt.format(count=count, kind=kind_display)
    desc = template.desc_fmt.format(count=count, kind=kind_display)

    # Target position for EXPLORE quests
    target_pos = None
    if template.quest_type == QuestType.EXPLORE:
        tx = 5 + (rng.next() % max(1, grid_width - 10))
        ty = 5 + (rng.next() % max(1, grid_height - 10))
        target_pos = Vector2(tx, ty)
        title = f"Scout ({tx},{ty})"
        desc = f"Travel to coordinates ({tx},{ty}) and survey the area."

    return Quest(
        quest_id=quest_id,
        quest_type=template.quest_type,
        title=title,
        description=desc,
        target_kind=target_kind,
        target_pos=target_pos,
        target_count=count,
        gold_reward=gold,
        xp_reward=xp,
    )
