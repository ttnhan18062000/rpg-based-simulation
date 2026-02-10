"""Tests for inventory-aware goal scoring — verifies bug-02 scenarios.

Bug-02: Hero keeps looting when bag is full. The LootGoal scorer should
return 0.0 when inventory is at max capacity, and TradeGoal should get
a bonus when the bag is nearly full.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.ai.goals.scorers import LootGoal, TradeGoal
from src.ai.states import AIContext
from src.config import SimulationConfig
from src.core.enums import AIState
from src.core.faction import Faction, FactionRegistry
from src.core.grid import Grid
from src.core.items import Inventory
from src.core.models import Entity, Stats, Vector2
from src.core.snapshot import Snapshot
from src.core.world_state import WorldState
from src.systems.rng import DeterministicRNG
from src.systems.spatial_hash import SpatialHash


def _make_world_with_loot(loot_pos: Vector2 | None = None) -> WorldState:
    """Create a minimal world, optionally with ground loot."""
    grid = Grid(32, 32)
    spatial = SpatialHash(8)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    if loot_pos is not None:
        world.ground_items[(loot_pos.x, loot_pos.y)] = ["iron_sword"]
    return world


def _make_hero(
    eid: int = 1,
    x: int = 5, y: int = 5,
    max_slots: int = 12,
    filled_slots: int = 0,
    gold: int = 100,
) -> Entity:
    """Create a hero entity with configurable inventory fill level."""
    stats = Stats(hp=50, max_hp=50, atk=10, def_=5, spd=10, gold=gold)
    items = ["iron_sword"] * filled_slots
    inv = Inventory(items=items, max_slots=max_slots, max_weight=100.0)
    return Entity(
        id=eid, kind="hero", pos=Vector2(x, y),
        stats=stats, faction=Faction.HERO_GUILD,
        inventory=inv,
    )


def _make_ctx(entity: Entity, world: WorldState) -> AIContext:
    """Build an AIContext from entity + world."""
    cfg = SimulationConfig()
    rng = DeterministicRNG(42)
    faction_reg = FactionRegistry.default()
    snapshot = Snapshot.from_world(world)
    return AIContext(
        actor=snapshot.entities[entity.id],
        snapshot=snapshot,
        config=cfg,
        rng=rng,
        faction_reg=faction_reg,
    )


class TestLootGoalInventoryCheck:
    """LootGoal.score() must respect inventory capacity."""

    def test_full_bag_returns_zero(self):
        """When inventory is completely full, loot score must be 0."""
        loot_pos = Vector2(6, 5)
        world = _make_world_with_loot(loot_pos)
        hero = _make_hero(filled_slots=12, max_slots=12)
        world.add_entity(hero)

        ctx = _make_ctx(hero, world)
        scorer = LootGoal()
        score = scorer.score(ctx)

        assert score == 0.0, f"Full bag should return 0.0 loot score, got {score}"

    def test_nearly_full_bag_penalized(self):
        """When only 1–2 slots free, loot score should be significantly reduced."""
        loot_pos = Vector2(6, 5)
        world = _make_world_with_loot(loot_pos)
        hero = _make_hero(filled_slots=11, max_slots=12)  # 1 free slot
        world.add_entity(hero)

        ctx = _make_ctx(hero, world)
        scorer = LootGoal()
        score_nearly_full = scorer.score(ctx)

        # Compare with empty bag
        world2 = _make_world_with_loot(loot_pos)
        hero2 = _make_hero(eid=1, filled_slots=0, max_slots=12)
        world2.add_entity(hero2)
        ctx2 = _make_ctx(hero2, world2)
        score_empty = scorer.score(ctx2)

        assert score_nearly_full < score_empty, (
            f"Nearly-full bag ({score_nearly_full}) should score lower than empty ({score_empty})"
        )

    def test_empty_bag_with_nearby_loot_scores_positive(self):
        """Empty bag + nearby loot = positive score."""
        loot_pos = Vector2(6, 5)  # 1 tile away
        world = _make_world_with_loot(loot_pos)
        hero = _make_hero(filled_slots=0, max_slots=12)
        world.add_entity(hero)

        ctx = _make_ctx(hero, world)
        scorer = LootGoal()
        score = scorer.score(ctx)

        assert score > 0.0, f"Empty bag with nearby loot should score positive, got {score}"

    def test_no_nearby_loot_low_score(self):
        """No ground loot nearby = low/zero base score."""
        world = _make_world_with_loot(loot_pos=None)  # no loot
        hero = _make_hero(filled_slots=0, max_slots=12)
        world.add_entity(hero)

        ctx = _make_ctx(hero, world)
        scorer = LootGoal()
        score = scorer.score(ctx)

        # Without any loot nearby, base should be near 0 (only trait bonus)
        assert score <= 0.1, f"No nearby loot should score very low, got {score}"


class TestTradeGoalFullBag:
    """TradeGoal should incentivize selling when bag is nearly full."""

    def test_nearly_full_bag_boosts_trade(self):
        """Trade score should be higher when bag is nearly full."""
        world = _make_world_with_loot(loot_pos=None)

        # Nearly full hero
        hero_full = _make_hero(eid=1, filled_slots=11, max_slots=12)
        world.add_entity(hero_full)
        ctx_full = _make_ctx(hero_full, world)

        # Empty bag hero
        world2 = _make_world_with_loot(loot_pos=None)
        hero_empty = _make_hero(eid=1, filled_slots=0, max_slots=12)
        world2.add_entity(hero_empty)
        ctx_empty = _make_ctx(hero_empty, world2)

        scorer = TradeGoal()
        score_full = scorer.score(ctx_full)
        score_empty = scorer.score(ctx_empty)

        assert score_full > score_empty, (
            f"Nearly-full bag trade score ({score_full}) should be higher than empty ({score_empty})"
        )

    def test_full_bag_trade_outscores_loot(self):
        """When bag is full, trade score should exceed loot score."""
        loot_pos = Vector2(6, 5)
        world = _make_world_with_loot(loot_pos)
        hero = _make_hero(filled_slots=12, max_slots=12)
        world.add_entity(hero)

        ctx = _make_ctx(hero, world)

        loot_score = LootGoal().score(ctx)
        trade_score = TradeGoal().score(ctx)

        assert trade_score > loot_score, (
            f"With full bag: trade ({trade_score}) should outscore loot ({loot_score})"
        )
