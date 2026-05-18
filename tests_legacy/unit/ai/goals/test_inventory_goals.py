import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


"""Tests for inventory-aware goal scoring — verifies bug-02 scenarios.

Bug-02: Hero keeps looting when bag is full. The LootGoal scorer should
return 0.0 when inventory is at max capacity, and TradeGoal should get
a bonus when the bag is nearly full.
"""



from src_legacy.ai.goals.scorers import LootGoal, TradeGoal
from src_legacy.ai.states import AIContext
from src_legacy.config import SimulationConfig
from src_legacy.core.models.enums import AIState, ActionType
from src_legacy.core.gameplay.faction import Faction, FactionRegistry
from src_legacy.core.world.grid import Grid
from src_legacy.core.aspects.inventory import InventoryAspect
from src_legacy.core.entities.entity import Entity, Vector2
from src_legacy.core.models.snapshot import Snapshot
from src_legacy.actions.base import InteractionUpdate
from src_legacy.core.models.world_state import WorldState
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.systems.spatial_hash import SpatialHash
from src_legacy.core.registry.registry_loader import load_all_registries

load_all_registries()


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
    hero = Entity(id=eid, kind="hero")
    hero.spatial.pos = Vector2(x, y)
    hero.identity.faction = Faction.HERO_GUILD
    hero.combat.hp = 50
    hero.combat.max_hp = 50
    hero.combat.atk_base = 10
    hero.combat.def_base = 5
    hero.combat.spd_base = 10
    hero.progression.gold = gold
    
    from src_legacy.core.aspects.inventory import InventoryAspect
    items = ["iron_sword"] * filled_slots
    hero.inventory = InventoryAspect(items=items, max_slots=max_slots, max_weight=100.0)
    return hero


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
        from src_legacy.ai.states import LootingHandler

        loot_pos = Vector2(5, 5)
        world = _make_world_with_loot(loot_pos)
        hero = _make_hero(filled_slots=12, max_slots=12)
        hero.mind.decision.ai_state = AIState.LOOTING
        hero.interaction.loot_progress = 2
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
        from src_legacy.ai.states import LootingHandler

        loot_pos = Vector2(5, 5)
        world = _make_world_with_loot(loot_pos)
        hero = _make_hero(filled_slots=12, max_slots=12)
        hero.mind.decision.ai_state = AIState.LOOTING
        hero.interaction.loot_progress = 2
        world.add_entity(hero)

        ctx = _make_ctx(hero, world)
        handler = LootingHandler()
        _, proposal = handler.handle(ctx)

        inter_up = next((u for u in proposal.updates if isinstance(u, InteractionUpdate)), None)
        assert inter_up and inter_up.loot_progress_set == 0, (
            f"Loot progress reset intent should be 0 in updates, got {inter_up}")

    def test_not_full_bag_continues_looting(self):
        """LootingHandler should continue normally when bag has space."""
        from src_legacy.ai.states import LootingHandler

        loot_pos = Vector2(5, 5)
        world = _make_world_with_loot(loot_pos)
        hero = _make_hero(filled_slots=5, max_slots=12)
        hero.mind.decision.ai_state = AIState.LOOTING
        world.add_entity(hero)

        ctx = _make_ctx(hero, world)
        handler = LootingHandler()
        state, proposal = handler.handle(ctx)

        assert state == AIState.LOOTING, (
            f"Should continue LOOTING with space in bag, got {state}")

    def test_no_inventory_continues_looting(self):
        """Entities without inventory should still be able to loot."""
        from src_legacy.ai.states import LootingHandler

        loot_pos = Vector2(5, 5)
        world = _make_world_with_loot(loot_pos)
        hero = Entity(id=1, kind="hero")
        hero.spatial.pos = Vector2(5, 5)
        hero.identity.faction = Faction.HERO_GUILD
        hero.combat.hp = 50
        hero.combat.max_hp = 50
        hero.combat.atk_base = 10
        hero.combat.def_base = 5
        hero.combat.spd_base = 10
        hero.inventory = None
        hero.mind.decision.ai_state = AIState.LOOTING
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
        hero = Entity(id=eid, kind="hero")
        hero.spatial.pos = Vector2(x, y)
        hero.identity.faction = Faction.HERO_GUILD
        hero.combat.hp = 50
        hero.combat.max_hp = 50
        hero.combat.atk_base = 10
        hero.combat.def_base = 5
        hero.combat.spd_base = 10
        hero.progression.gold = 100
        
        # Fill with heavy items: iron_sword weighs ~3.0
        items = ["iron_sword", "iron_sword"]  # 2 slots used, ~6.0 weight → over cap
        hero.inventory = InventoryAspect(items=items, max_slots=max_slots, max_weight=max_weight)
        return hero

    def test_overweight_aborts_looting(self):
        """LootingHandler should abort when weight is at max, even with free slots."""
        from src_legacy.ai.states import LootingHandler

        loot_pos = Vector2(5, 5)
        world = _make_world_with_loot(loot_pos)
        hero = self._make_heavy_hero(max_slots=12, max_weight=5.0)
        hero.mind.decision.ai_state = AIState.LOOTING
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
        hero1 = Entity(id=1, kind="hero")
        hero1.spatial.pos = Vector2(5, 5)
        hero1.identity.faction = Faction.HERO_GUILD
        hero1.combat.hp = 50
        hero1.combat.max_hp = 50
        hero1.progression.gold = 100
        hero1.inventory = InventoryAspect(items=["small_hp_potion"], max_slots=12, max_weight=0.55)
        world1.add_entity(hero1)
        ctx1 = _make_ctx(hero1, world1)

        # Hero with lots of weight room
        world2 = _make_world_with_loot(loot_pos)
        hero2 = Entity(id=1, kind="hero")
        hero2.spatial.pos = Vector2(5, 5)
        hero2.identity.faction = Faction.HERO_GUILD
        hero2.combat.hp = 50
        hero2.combat.max_hp = 50
        hero2.progression.gold = 100
        hero2.inventory = InventoryAspect(items=["small_hp_potion"], max_slots=12, max_weight=100.0)
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
        hero_light = Entity(id=1, kind="hero")
        hero_light.spatial.pos = Vector2(5, 5)
        hero_light.identity.faction = Faction.HERO_GUILD
        hero_light.combat.hp = 50
        hero_light.combat.max_hp = 50
        hero_light.progression.gold = 100
        hero_light.inventory = InventoryAspect(items=[], max_slots=12, max_weight=100.0)
        world2.add_entity(hero_light)
        ctx_light = _make_ctx(hero_light, world2)

        scorer = TradeGoal()
        score_heavy = scorer.score(ctx_heavy)
        score_light = scorer.score(ctx_light)

        assert score_heavy > score_light, (
            f"Overweight trade score ({score_heavy}) should exceed light ({score_light})")
