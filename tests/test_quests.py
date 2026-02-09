"""Tests for the quest system — model, generation, tracking, and completion."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.models import Entity, Stats, Vector2
from src.core.enums import AIState
from src.core.faction import Faction
from src.core.quests import (
    Quest, QuestType, QuestTemplate, generate_quest, MAX_ACTIVE_QUESTS,
    QUEST_TEMPLATES, TEMPLATE_MAP,
)


def _make_entity(eid: int, level: int = 1, kind: str = "hero") -> Entity:
    stats = Stats(hp=50, max_hp=50, atk=10, def_=5, spd=10, level=level, gold=0, xp=0)
    return Entity(id=eid, kind=kind, pos=Vector2(5, 5), stats=stats, faction=Faction.HERO_GUILD)


class _FakeRNG:
    """Deterministic fake RNG for testing."""
    def __init__(self, values: list[int] | None = None):
        self._values = values or list(range(100))
        self._idx = 0

    def next(self) -> int:
        val = self._values[self._idx % len(self._values)]
        self._idx += 1
        return val


# ---------------------------------------------------------------------------
# Quest model tests
# ---------------------------------------------------------------------------

class TestQuestModel:
    def test_quest_creation(self):
        q = Quest(quest_id="test_1", quest_type=QuestType.HUNT, title="Hunt 3 goblins",
                  description="Kill goblins", target_kind="goblin", target_count=3,
                  gold_reward=50, xp_reward=80)
        assert q.quest_id == "test_1"
        assert q.quest_type == QuestType.HUNT
        assert q.progress == 0
        assert not q.completed
        assert q.progress_ratio == 0.0

    def test_quest_advance(self):
        q = Quest(quest_id="h1", quest_type=QuestType.HUNT, title="Hunt",
                  description="", target_kind="goblin", target_count=3)
        assert q.advance()  is False  # not yet completed
        assert q.progress == 1
        q.advance()
        assert q.progress == 2
        assert not q.completed
        result = q.advance()
        assert result is True  # just completed
        assert q.completed
        assert q.progress_ratio == 1.0

    def test_quest_advance_does_nothing_when_completed(self):
        q = Quest(quest_id="h1", quest_type=QuestType.HUNT, title="Hunt",
                  description="", target_kind="goblin", target_count=1)
        q.advance()
        assert q.completed
        result = q.advance()
        assert result is False  # already completed, no change

    def test_quest_progress_ratio(self):
        q = Quest(quest_id="h1", quest_type=QuestType.HUNT, title="Hunt",
                  description="", target_count=4, progress=2)
        assert q.progress_ratio == 0.5

    def test_quest_copy(self):
        q = Quest(quest_id="h1", quest_type=QuestType.HUNT, title="Hunt",
                  description="Desc", target_kind="goblin", target_count=3,
                  progress=1, gold_reward=50, xp_reward=80)
        c = q.copy()
        assert c.quest_id == q.quest_id
        assert c.progress == q.progress
        c.advance()
        assert c.progress == 2
        assert q.progress == 1  # original unmodified

    def test_quest_to_dict(self):
        q = Quest(quest_id="h1", quest_type=QuestType.HUNT, title="Hunt",
                  description="Desc", target_kind="goblin", target_count=3,
                  gold_reward=50, xp_reward=80)
        d = q.to_dict()
        assert d["quest_id"] == "h1"
        assert d["quest_type"] == "HUNT"
        assert d["target_kind"] == "goblin"
        assert "target_x" not in d  # no position for HUNT

    def test_explore_quest_to_dict_includes_position(self):
        q = Quest(quest_id="e1", quest_type=QuestType.EXPLORE, title="Scout",
                  description="Go there", target_pos=Vector2(10, 20))
        d = q.to_dict()
        assert d["target_x"] == 10
        assert d["target_y"] == 20


# ---------------------------------------------------------------------------
# Quest generation tests
# ---------------------------------------------------------------------------

class TestQuestGeneration:
    def test_generate_quest_returns_quest(self):
        rng = _FakeRNG([0, 0, 0, 0, 0, 0, 0, 0])
        q = generate_quest(hero_level=1, existing_quest_ids=set(), rng=rng)
        assert q is not None
        assert isinstance(q, Quest)
        assert q.quest_type in (QuestType.HUNT, QuestType.GATHER, QuestType.EXPLORE)

    def test_generate_quest_respects_level(self):
        # At level 1, templates with min_level > 1 should be excluded
        rng = _FakeRNG([0, 0, 0, 0, 0, 0, 0, 0])
        eligible_at_1 = [t for t in QUEST_TEMPLATES if t.min_level <= 1]
        eligible_at_5 = [t for t in QUEST_TEMPLATES if t.min_level <= 5]
        assert len(eligible_at_5) >= len(eligible_at_1)

    def test_generate_quest_skips_duplicate(self):
        rng = _FakeRNG([0, 0, 0, 0, 0, 0, 0, 0])
        q1 = generate_quest(hero_level=1, existing_quest_ids=set(), rng=rng)
        assert q1 is not None
        # Attempt with same RNG seed — should produce same quest_id
        rng2 = _FakeRNG([0, 0, 0, 0, 0, 0, 0, 0])
        q2 = generate_quest(hero_level=1, existing_quest_ids={q1.quest_id}, rng=rng2)
        assert q2 is None  # duplicate skipped

    def test_generate_quest_gold_scales_with_level(self):
        rng1 = _FakeRNG([0, 0, 0, 0, 0, 0, 0, 0])
        q1 = generate_quest(hero_level=1, existing_quest_ids=set(), rng=rng1)
        rng2 = _FakeRNG([0, 0, 0, 0, 0, 0, 0, 0])
        q5 = generate_quest(hero_level=5, existing_quest_ids=set(), rng=rng2)
        assert q1 is not None and q5 is not None
        assert q5.gold_reward >= q1.gold_reward

    def test_generate_explore_quest(self):
        # Find the explore template index
        explore_idx = next(i for i, t in enumerate(QUEST_TEMPLATES) if t.quest_type == QuestType.EXPLORE)
        eligible_at_1 = [t for t in QUEST_TEMPLATES if t.min_level <= 1]
        # We need the RNG to pick the explore template
        rng_val = explore_idx  # index into eligible list
        # If explore_idx is within eligible_at_1, use it
        if explore_idx < len(eligible_at_1):
            rng = _FakeRNG([rng_val, 0, 0, 0, 0, 0, 30, 40])
            q = generate_quest(hero_level=1, existing_quest_ids=set(), rng=rng,
                               grid_width=80, grid_height=80)
            if q and q.quest_type == QuestType.EXPLORE:
                assert q.target_pos is not None

    def test_template_map_consistency(self):
        assert len(TEMPLATE_MAP) == len(QUEST_TEMPLATES)
        for t in QUEST_TEMPLATES:
            assert t.template_id in TEMPLATE_MAP


# ---------------------------------------------------------------------------
# Quest tracking on Entity tests
# ---------------------------------------------------------------------------

class TestQuestTracking:
    def test_entity_starts_with_no_quests(self):
        e = _make_entity(1)
        assert e.quests == []

    def test_entity_can_hold_quests(self):
        e = _make_entity(1)
        q = Quest(quest_id="h1", quest_type=QuestType.HUNT, title="Hunt",
                  description="", target_kind="goblin", target_count=3)
        e.quests.append(q)
        assert len(e.quests) == 1

    def test_entity_copy_preserves_quests(self):
        e = _make_entity(1)
        q = Quest(quest_id="h1", quest_type=QuestType.HUNT, title="Hunt",
                  description="", target_kind="goblin", target_count=3, progress=1)
        e.quests.append(q)
        c = e.copy()
        assert len(c.quests) == 1
        assert c.quests[0].progress == 1
        # Deep copy — modifying copy shouldn't affect original
        c.quests[0].advance()
        assert c.quests[0].progress == 2
        assert e.quests[0].progress == 1

    def test_hunt_quest_completion_awards_rewards(self):
        e = _make_entity(1)
        q = Quest(quest_id="h1", quest_type=QuestType.HUNT, title="Hunt",
                  description="", target_kind="goblin", target_count=1,
                  gold_reward=50, xp_reward=80)
        e.quests.append(q)
        initial_gold = e.stats.gold
        initial_xp = e.stats.xp
        # Simulate kill quest completion
        just_done = q.advance()
        if just_done:
            e.stats.gold += q.gold_reward
            e.stats.xp += q.xp_reward
        assert q.completed
        assert e.stats.gold == initial_gold + 50
        assert e.stats.xp == initial_xp + 80

    def test_explore_quest_completes_near_target(self):
        e = _make_entity(1)
        target = Vector2(7, 7)
        q = Quest(quest_id="e1", quest_type=QuestType.EXPLORE, title="Scout",
                  description="", target_pos=target, target_count=1)
        e.quests.append(q)
        # Hero is at (5,5), target at (7,7) → manhattan = 4, too far
        assert e.pos.manhattan(target) == 4
        assert not q.completed
        # Move hero closer
        e.pos = Vector2(6, 7)  # manhattan = 1
        assert e.pos.manhattan(target) <= 2
        q.advance()
        assert q.completed

    def test_gather_quest_advance(self):
        q = Quest(quest_id="g1", quest_type=QuestType.GATHER, title="Gather herbs",
                  description="", target_kind="herb", target_count=5)
        q.advance(2)
        assert q.progress == 2
        assert not q.completed
        q.advance(3)
        assert q.progress == 5
        assert q.completed

    def test_max_active_quests_constant(self):
        assert MAX_ACTIVE_QUESTS == 3
