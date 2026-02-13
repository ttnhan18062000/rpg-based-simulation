"""CombatArena — E2E test fixture for combat mechanics.

Creates a minimal but fully-functional WorldLoop with controllable entities,
runs ticks, and collects events for assertion.

Usage:
    arena = CombatArena()
    arena.add_melee_hero(1, pos=(5, 5))
    arena.add_mob(2, pos=(6, 5), weapon="rusty_sword")
    events = arena.run_ticks(10)
    assert arena.entity(2).stats.hp < arena.entity(2).stats.max_hp
"""

from __future__ import annotations

import sys
import os
from typing import Callable

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.config import SimulationConfig
from src.core.attributes import Attributes, AttributeCaps, recalc_derived_stats
from src.core.classes import HeroClass, SkillInstance
from src.core.effects import StatusEffect
from src.core.enums import AIState, EnemyTier, Material
from src.core.faction import Faction, FactionRegistry
from src.core.grid import Grid
from src.core.items import Inventory, ITEM_REGISTRY
from src.core.models import Entity, Stats, Vector2
from src.core.world_state import WorldState
from src.engine.conflict_resolver import ConflictResolver
from src.engine.worker_pool import WorkerPool
from src.engine.world_loop import WorldLoop
from src.systems.generator import EntityGenerator
from src.systems.rng import DeterministicRNG
from src.systems.spatial_hash import SpatialHash
from src.utils.event_log import SimEvent


class CombatArena:
    """E2E test fixture for combat mechanics.

    Creates a small world with a full WorldLoop pipeline.
    Add entities, run ticks, inspect state and events.
    """

    def __init__(
        self,
        width: int = 20,
        height: int = 20,
        seed: int = 42,
        **config_overrides,
    ):
        defaults = dict(
            max_ticks=9999,
            initial_entity_count=0,
            generator_max_entities=0,
            num_camps=0,
            hero_respawn_ticks=9999,
        )
        defaults.update(config_overrides)
        self.config = SimulationConfig(**defaults)
        self.rng = DeterministicRNG(seed=seed)

        grid = Grid(width, height)
        spatial = SpatialHash(self.config.spatial_cell_size)
        self.world = WorldState(seed=seed, grid=grid, spatial_index=spatial)

        brain_mod = __import__("src.ai.brain", fromlist=["AIBrain"])
        brain = brain_mod.AIBrain(self.config, self.rng)
        pool = WorkerPool(self.config, brain)
        resolver = ConflictResolver(self.config, self.rng)
        gen = EntityGenerator(self.config, self.rng)
        faction_reg = FactionRegistry.default()

        self.loop = WorldLoop(
            self.config, self.world, pool, resolver, gen,
            rng=self.rng, faction_reg=faction_reg,
        )
        self._all_events: list[SimEvent] = []

    # -- Entity builders --

    def _make_inventory(self, weapon: str | None = None, armor: str | None = None) -> Inventory:
        inv = Inventory(items=[], max_slots=12, max_weight=50.0)
        if weapon:
            inv.weapon = weapon
            if weapon not in inv.items:
                inv.items.append(weapon)
        if armor:
            inv.armor = armor
            if armor not in inv.items:
                inv.items.append(armor)
        return inv

    def add_entity(
        self,
        eid: int,
        kind: str = "hero",
        pos: tuple[int, int] = (5, 5),
        *,
        hp: int = 100,
        atk: int = 10,
        matk: int = 10,
        def_: int = 5,
        mdef: int = 5,
        spd: int = 10,
        weapon: str | None = None,
        armor: str | None = None,
        faction: Faction = Faction.HERO_GUILD,
        ai_state: AIState = AIState.WANDER,
        hero_class: int = HeroClass.NONE,
        skills: list[str] | None = None,
        effects: list[StatusEffect] | None = None,
        attributes: Attributes | None = None,
        tier: int = EnemyTier.BASIC,
        home_pos: tuple[int, int] | None = None,
        next_act_at: float = 0.0,
    ) -> Entity:
        """Add a fully customizable entity to the arena."""
        stats = Stats(
            hp=hp, max_hp=hp, atk=atk, matk=matk, def_=def_, mdef=mdef,
            spd=spd, stamina=100, max_stamina=100,
        )
        attrs = attributes or Attributes(
            str_=5, agi=5, vit=5, int_=5, spi=5, wis=5, end=5, per=5, cha=5,
        )
        caps = AttributeCaps()
        inv = self._make_inventory(weapon, armor)
        skill_list = []
        if skills:
            for sid in skills:
                skill_list.append(SkillInstance(skill_id=sid, cooldown_remaining=0))

        entity = Entity(
            id=eid,
            kind=kind,
            pos=Vector2(*pos),
            stats=stats,
            faction=faction,
            ai_state=ai_state,
            hero_class=hero_class,
            inventory=inv,
            attributes=attrs,
            attribute_caps=caps,
            skills=skill_list,
            effects=list(effects or []),
            tier=tier,
            home_pos=Vector2(*home_pos) if home_pos else None,
            next_act_at=next_act_at,
        )
        # Apply attribute-derived stat bonuses
        recalc_derived_stats(entity.stats, entity.attributes)
        self.world.add_entity(entity)
        return entity

    def add_hero(
        self,
        eid: int,
        pos: tuple[int, int] = (5, 5),
        *,
        hero_class: int = HeroClass.WARRIOR,
        weapon: str | None = "iron_sword",
        armor: str | None = "leather_vest",
        **kwargs,
    ) -> Entity:
        """Convenience: add a hero entity with sensible defaults."""
        kwargs.setdefault("faction", Faction.HERO_GUILD)
        kwargs.setdefault("ai_state", AIState.WANDER)
        return self.add_entity(
            eid, kind="hero", pos=pos,
            hero_class=hero_class, weapon=weapon, armor=armor,
            **kwargs,
        )

    def add_mob(
        self,
        eid: int,
        pos: tuple[int, int] = (10, 10),
        *,
        kind: str = "goblin",
        weapon: str | None = "rusty_sword",
        tier: int = EnemyTier.BASIC,
        **kwargs,
    ) -> Entity:
        """Convenience: add a hostile mob entity."""
        kwargs.setdefault("faction", Faction.GOBLIN_HORDE)
        kwargs.setdefault("ai_state", AIState.WANDER)
        return self.add_entity(
            eid, kind=kind, pos=pos, weapon=weapon, tier=tier,
            **kwargs,
        )

    # -- Grid manipulation --

    def set_tile(self, x: int, y: int, material: int) -> None:
        """Set a tile material at the given position."""
        self.world.grid.set(Vector2(x, y), material)

    def set_wall(self, x: int, y: int) -> None:
        """Place a WALL tile."""
        self.set_tile(x, y, Material.WALL)

    # -- Running --

    def run_ticks(self, n: int) -> list[SimEvent]:
        """Run n ticks and return all events emitted during those ticks."""
        events: list[SimEvent] = []
        for _ in range(n):
            self.loop.tick_once()
            events.extend(self.loop.tick_events)
        self._all_events.extend(events)
        return events

    def run_until(
        self,
        predicate: Callable[[CombatArena], bool],
        max_ticks: int = 100,
    ) -> list[SimEvent]:
        """Run ticks until predicate(arena) returns True or max_ticks reached."""
        events: list[SimEvent] = []
        for _ in range(max_ticks):
            self.loop.tick_once()
            tick_evts = self.loop.tick_events
            events.extend(tick_evts)
            if predicate(self):
                break
        self._all_events.extend(events)
        return events

    # -- Queries --

    def entity(self, eid: int) -> Entity | None:
        """Get an entity by ID from the world (or None if removed)."""
        return self.world.entities.get(eid)

    def entity_alive(self, eid: int) -> bool:
        """Check if entity exists and is alive."""
        e = self.world.entities.get(eid)
        return e is not None and e.alive

    def all_events(self) -> list[SimEvent]:
        """All events collected across all run calls."""
        return list(self._all_events)

    def events_by_category(self, category: str) -> list[SimEvent]:
        """Filter all collected events by category."""
        return [e for e in self._all_events if e.category == category]

    def events_for_entity(self, eid: int) -> list[SimEvent]:
        """Filter all collected events involving a specific entity."""
        return [e for e in self._all_events if eid in (e.entity_ids or ())]

    def combat_events(self) -> list[SimEvent]:
        """All combat + skill events."""
        return [e for e in self._all_events if e.category in ("combat", "skill")]

    def death_events(self) -> list[SimEvent]:
        """All death events."""
        return self.events_by_category("death")

    @property
    def tick(self) -> int:
        """Current world tick."""
        return self.world.tick
