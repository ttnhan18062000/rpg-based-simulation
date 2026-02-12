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
from src.core.enums import AIState, ActionType
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


class TestLootingHandlerFullBag:
    """Bug-02 fix: LootingHandler must abort when inventory is full."""

    def test_full_bag_aborts_looting(self):
        """LootingHandler should switch to WANDER when bag is full."""
        from src.ai.states import LootingHandler

        loot_pos = Vector2(5, 5)
        world = _make_world_with_loot(loot_pos)
        hero = _make_hero(filled_slots=12, max_slots=12)
        hero.ai_state = AIState.LOOTING
        hero.loot_progress = 2
        world.add_entity(hero)

        ctx = _make_ctx(hero, world)
        handler = LootingHandler()
        state, proposal = handler.handle(ctx)

        assert state == AIState.WANDER, (
            f"Full bag should abort to WANDER, got {state}")
        assert proposal.verb == ActionType.REST
        assert "Bag full" in proposal.reason

    def test_full_bag_resets_loot_progress(self):
        """Loot progress should be reset when bag-full abort triggers."""
        from src.ai.states import LootingHandler

        loot_pos = Vector2(5, 5)
        world = _make_world_with_loot(loot_pos)
        hero = _make_hero(filled_slots=12, max_slots=12)
        hero.ai_state = AIState.LOOTING
        hero.loot_progress = 2
        world.add_entity(hero)

        ctx = _make_ctx(hero, world)
        handler = LootingHandler()
        handler.handle(ctx)

        assert ctx.actor.loot_progress == 0, (
            f"Loot progress should be reset, got {ctx.actor.loot_progress}")

    def test_not_full_bag_continues_looting(self):
        """LootingHandler should continue normally when bag has space."""
        from src.ai.states import LootingHandler

        loot_pos = Vector2(5, 5)
        world = _make_world_with_loot(loot_pos)
        hero = _make_hero(filled_slots=5, max_slots=12)
        hero.ai_state = AIState.LOOTING
        world.add_entity(hero)

        ctx = _make_ctx(hero, world)
        handler = LootingHandler()
        state, proposal = handler.handle(ctx)

        assert state == AIState.LOOTING, (
            f"Should continue LOOTING with space in bag, got {state}")

    def test_no_inventory_continues_looting(self):
        """Entities without inventory should still be able to loot."""
        from src.ai.states import LootingHandler

        loot_pos = Vector2(5, 5)
        world = _make_world_with_loot(loot_pos)
        stats = Stats(hp=50, max_hp=50, atk=10, def_=5, spd=10)
        hero = Entity(
            id=1, kind="hero", pos=Vector2(5, 5),
            stats=stats, faction=Faction.HERO_GUILD,
            inventory=None,
        )
        hero.ai_state = AIState.LOOTING
        world.add_entity(hero)

        ctx = _make_ctx(hero, world)
        handler = LootingHandler()
        state, proposal = handler.handle(ctx)

        assert state == AIState.LOOTING, (
            f"No-inventory entity should continue looting, got {state}")


class TestWeightBasedInventoryChecks:
    """Bug-02 extension: inventory fullness checks must consider weight, not just slots."""

    def _make_heavy_hero(
        self,
        eid: int = 1,
        x: int = 5, y: int = 5,
        max_slots: int = 12,
        max_weight: float = 5.0,
    ) -> Entity:
        """Hero with lots of slots but very low weight cap — will hit weight limit first."""
        stats = Stats(hp=50, max_hp=50, atk=10, def_=5, spd=10, gold=100)
        # Fill with heavy items: iron_sword weighs ~3.0
        items = ["iron_sword", "iron_sword"]  # 2 slots used, ~6.0 weight → over cap
        inv = Inventory(items=items, max_slots=max_slots, max_weight=max_weight)
        return Entity(
            id=eid, kind="hero", pos=Vector2(x, y),
            stats=stats, faction=Faction.HERO_GUILD,
            inventory=inv,
        )

    def test_overweight_aborts_looting(self):
        """LootingHandler should abort when weight is at max, even with free slots."""
        from src.ai.states import LootingHandler

        loot_pos = Vector2(5, 5)
        world = _make_world_with_loot(loot_pos)
        hero = self._make_heavy_hero(max_slots=12, max_weight=5.0)
        hero.ai_state = AIState.LOOTING
        world.add_entity(hero)

        ctx = _make_ctx(hero, world)
        handler = LootingHandler()
        state, proposal = handler.handle(ctx)

        assert state == AIState.WANDER, (
            f"Overweight hero should abort looting, got {state}")
        assert "Bag full" in proposal.reason

    def test_overweight_loot_score_zero(self):
        """LootGoal should return 0 when weight is at max, even with free slots."""
        loot_pos = Vector2(6, 5)
        world = _make_world_with_loot(loot_pos)
        hero = self._make_heavy_hero(max_slots=12, max_weight=5.0)
        world.add_entity(hero)

        ctx = _make_ctx(hero, world)
        scorer = LootGoal()
        score = scorer.score(ctx)

        assert score == 0.0, (
            f"Overweight hero loot score should be 0.0, got {score}")

    def test_near_weight_limit_penalizes_loot(self):
        """Loot score should be penalized when weight ratio >= 0.9."""
        loot_pos = Vector2(6, 5)

        # Hero near weight cap (small_hp_potion weighs 0.5; 0.5/0.55 ≈ 0.91 ratio)
        world1 = _make_world_with_loot(loot_pos)
        stats1 = Stats(hp=50, max_hp=50, atk=10, def_=5, spd=10, gold=100)
        inv1 = Inventory(items=["small_hp_potion"], max_slots=12, max_weight=0.55)
        hero1 = Entity(id=1, kind="hero", pos=Vector2(5, 5),
                        stats=stats1, faction=Faction.HERO_GUILD, inventory=inv1)
        world1.add_entity(hero1)
        ctx1 = _make_ctx(hero1, world1)

        # Hero with lots of weight room
        world2 = _make_world_with_loot(loot_pos)
        stats2 = Stats(hp=50, max_hp=50, atk=10, def_=5, spd=10, gold=100)
        inv2 = Inventory(items=["small_hp_potion"], max_slots=12, max_weight=100.0)
        hero2 = Entity(id=1, kind="hero", pos=Vector2(5, 5),
                        stats=stats2, faction=Faction.HERO_GUILD, inventory=inv2)
        world2.add_entity(hero2)
        ctx2 = _make_ctx(hero2, world2)

        scorer = LootGoal()
        score_heavy = scorer.score(ctx1)
        score_light = scorer.score(ctx2)

        assert score_heavy < score_light, (
            f"Near-weight-limit hero ({score_heavy}) should score lower than light hero ({score_light})")

    def test_overweight_boosts_trade(self):
        """TradeGoal should get urgency bonus when weight ratio >= 0.9."""
        world1 = _make_world_with_loot(loot_pos=None)
        hero_heavy = self._make_heavy_hero(max_slots=12, max_weight=5.0)
        world1.add_entity(hero_heavy)
        ctx_heavy = _make_ctx(hero_heavy, world1)

        world2 = _make_world_with_loot(loot_pos=None)
        stats2 = Stats(hp=50, max_hp=50, atk=10, def_=5, spd=10, gold=100)
        inv2 = Inventory(items=[], max_slots=12, max_weight=100.0)
        hero_light = Entity(id=1, kind="hero", pos=Vector2(5, 5),
                            stats=stats2, faction=Faction.HERO_GUILD, inventory=inv2)
        world2.add_entity(hero_light)
        ctx_light = _make_ctx(hero_light, world2)

        scorer = TradeGoal()
        score_heavy = scorer.score(ctx_heavy)
        score_light = scorer.score(ctx_light)

        assert score_heavy > score_light, (
            f"Overweight trade score ({score_heavy}) should exceed light ({score_light})")
