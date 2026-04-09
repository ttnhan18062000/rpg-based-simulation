from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

"""Tests for inventory-aware goal scoring — verifies bug-02 scenarios.

Bug-02: Hero keeps looting when bag is full. The LootGoal scorer should
return 0.0 when inventory is at max capacity, and TradeGoal should get
a bonus when the bag is nearly full.
"""

import pytest
from src.ai.goals.scorers import LootGoal, TradeGoal
from src.ai.states import AIContext
from src.config import SimulationConfig
from src.core.models.enums import AIState, ActionType, GoalType
from src.core.gameplay.faction import Faction, FactionRegistry
from src.core.world.grid import Grid
from src.core.gameplay.items.item_registry import ITEM_REGISTRY
from src.core.aspects.inventory import InventoryAspect as Inventory
from src.core.entities.entity import Entity
from src.core.models.vectors import Vector2
from src.core.models.snapshot import Snapshot
from src.core.models.world_state import WorldState
from src.platform.rng import DeterministicRNG
from src.core.registry.registry_loader import load_all_registries
from src.systems.spatial_hash import SpatialHash
from src.core.aspects.combat import CombatAspect

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
    combat = CombatAspect(hp=50, max_hp=50, atk_base=10, def_base=5)
    items = ["iron_sword"] * filled_slots
    inv = Inventory(items=items, max_slots=max_slots, max_weight=100.0)
    hero = Entity(id=eid, kind="hero")
    hero.spatial.pos = Vector2(x, y)
    hero.combat = combat
    hero.identity.faction = Faction.HERO_GUILD
    hero.inventory = inv
    hero.progression.gold = gold
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
        hero2 = _make_hero(eid=2, filled_slots=0, max_slots=12)
        world2.add_entity(hero2)
        ctx2 = _make_ctx(hero2, world2)
        score_empty = scorer.score(ctx2)

        assert score_nearly_full < score_empty, (
            f"Nearly-full bag ({score_nearly_full}) should score lower than empty ({score_empty})"
        )

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
        hero_empty = _make_hero(eid=2, filled_slots=0, max_slots=12)
        world2.add_entity(hero_empty)
        ctx_empty = _make_ctx(hero_empty, world2)

        scorer = TradeGoal()
        score_full = scorer.score(ctx_full)
        score_empty = scorer.score(ctx_empty)

        assert score_full > score_empty, (
            f"Nearly-full bag trade score ({score_full}) should be higher than empty ({score_empty})"
        )

class TestLootingHandlerFullBag:
    """Bug-02 fix: LootingHandler must abort when inventory is full."""

    def test_full_bag_aborts_looting(self):
        """LootingHandler should switch to WANDER when bag is full."""
        from src.ai.states import LootingHandler

        loot_pos = Vector2(5, 5)
        world = _make_world_with_loot(loot_pos)
        hero = _make_hero(filled_slots=12, max_slots=12)
        hero.mind.decision.ai_state = AIState.LOOTING
        hero.interaction.loot_progress = 2
        world.add_entity(hero)

        ctx = _make_ctx(hero, world)
        handler = LootingHandler()
        state, proposal = handler.handle(ctx)

        # In current design, aborting loot might go to WANDER or idle
        assert state != AIState.LOOTING, f"Full bag should abort LOOTING, got {state}"
        assert proposal.verb == ActionType.REST or "Bag full" in proposal.reason

    def test_full_bag_resets_loot_progress(self):
        """Loot progress should be reset when bag-full abort triggers."""
        from src.ai.states import LootingHandler
        from src.actions.base import InteractionUpdate

        loot_pos = Vector2(5, 5)
        world = _make_world_with_loot(loot_pos)
        hero = _make_hero(filled_slots=12, max_slots=12)
        hero.mind.decision.ai_state = AIState.LOOTING
        hero.interaction.loot_progress = 2
        world.add_entity(hero)

        ctx = _make_ctx(hero, world)
        handler = LootingHandler()
        state, proposal = handler.handle(ctx)

        # In AOA, the handler emits an InteractionUpdate to reset progress
        has_reset = any(
            isinstance(u, InteractionUpdate) and u.loot_progress_set == 0 
            for u in proposal.updates
        )
        assert has_reset, f"LootingHandler should emit InteractionUpdate to reset progress, got updates: {proposal.updates}"

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
        combat = CombatAspect(hp=50, max_hp=50, atk_base=10, def_base=5)
        # Fill with heavy items: iron_sword weighs ~3.0
        items = ["iron_sword", "iron_sword"]  # 2 slots used, ~6.0 weight → over cap
        inv = Inventory(items=items, max_slots=max_slots, max_weight=max_weight)
        hero = Entity(id=eid, kind="hero")
        hero.spatial.pos = Vector2(x, y)
        hero.combat = combat
        hero.inventory = inv
        return hero

    def test_overweight_aborts_looting(self):
        """LootingHandler should abort when weight is at max, even with free slots."""
        from src.ai.states import LootingHandler

        loot_pos = Vector2(5, 5)
        world = _make_world_with_loot(loot_pos)
        hero = self._make_heavy_hero(max_slots=12, max_weight=5.0)
        hero.mind.decision.ai_state = AIState.LOOTING
        world.add_entity(hero)

        ctx = _make_ctx(hero, world)
        handler = LootingHandler()
        state, proposal = handler.handle(ctx)

        assert state != AIState.LOOTING, f"Overweight hero should abort looting, got {state}"
        assert "Bag full" in proposal.reason or "weight" in proposal.reason.lower()
