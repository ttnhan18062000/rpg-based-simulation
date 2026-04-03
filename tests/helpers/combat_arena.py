from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

"""CombatArena — E2E test fixture for combat mechanics.

Creates a minimal but fully-functional WorldLoop with controllable entities,
runs ticks, and collects events for assertion.

Usage:
    arena = CombatArena()
    arena.add_melee_hero(1, pos=(5, 5))
    arena.add_mob(2, pos=(6, 5), weapon="rusty_sword")
    events = arena.run_ticks(10)
    assert arena.entity(2).combat.hp < arena.entity(2).combat.max_hp
"""



from src.config import SimulationConfig
from src.core.gameplay.attributes import Attributes, AttributeCaps, recalc_derived_stats
from src.core.gameplay.classes import HeroClass, SkillInstance, SKILL_DEFS
from src.core.gameplay.effects import StatusEffect
from src.core.models.enums import AIState, EnemyTier, Material, EntityRole
from src.core.gameplay.faction import Faction, FactionRegistry
from src.core.world.grid import Grid
from src.core.gameplay.items.item_registry import ITEM_REGISTRY
from src.core.aspects.identity import IdentityAspect
from src.core.aspects.spatial import SpatialAspect
from src.core.aspects.combat import CombatAspect
from src.core.aspects.inventory import InventoryAspect
from src.core.aspects.progression import ProgressionAspect
from src.core.aspects.mind import MindAspect
from src.core.aspects.interaction import InteractionAspect
from src.core.entities.entity import Entity, Vector2
from src.core.models.world_state import WorldState
from src.engine.conflict_resolver import ConflictResolver
from src.engine.worker_pool import WorkerPool
from src.engine.world_loop import WorldLoop
from src.systems.world.generator import EntityGenerator
from src.platform.rng import DeterministicRNG
from src.platform.spatial_hash import SpatialHash
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
            num_workers=1,  # Inline AI — skip RabbitMQ connection
        )
        defaults.update(config_overrides)
        self.config = SimulationConfig(**defaults)
        self.rng = DeterministicRNG(seed=seed)

        grid = Grid(width, height)
        spatial = SpatialHash(self.config.spatial_cell_size)
        self.world = WorldState(seed=seed, grid=grid, spatial_index=spatial)

        from src.core.registry.registry_loader import load_all_registries
        load_all_registries()
        
        brain_mod = __import__("src.ai.brain", fromlist=["AIBrain"])
        brain = brain_mod.AIBrain(self.config, self.rng)
        pool = WorkerPool(self.config, brain, self.rng)
        resolver = ConflictResolver(self.config, self.rng)
        gen = EntityGenerator(self.config, self.rng)
        from src.core.gameplay.faction import Faction, FactionRegistry
        faction_reg = FactionRegistry.default()

        self.loop = WorldLoop(
            self.config, self.world, pool, resolver, gen,
            rng=self.rng, faction_reg=faction_reg,
        )
        self._all_events: list[SimEvent] = []

    # -- Entity builders --

    def _make_inventory(self, weapon: str | None = None, armor: str | None = None) -> InventoryAspect:
        inv = InventoryAspect(items=[], max_slots=12, max_weight=50.0)
        if weapon:
            inv.weapon = weapon
            if item_id := weapon: # handle potential None if needed, but here we assume it's an ID
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
        level: int = 1,
        xp: int = 0,
        mastery: dict[str, float] | None = None,
    ) -> Entity:
        """Add a fully customizable entity to the arena."""
        identity = IdentityAspect(
            display_name=kind, 
            faction=faction, 
            tier=tier,
            is_world_boss="boss" in kind.lower() or tier >= 2 # Tier 2+ is usually boss
        )
        spatial = SpatialAspect(pos=Vector2(*pos), home_pos=Vector2(*home_pos) if home_pos else None)
        combat = CombatAspect(
            hp=hp,
            max_hp=hp,
            atk_base=atk,
            matk=matk,
            def_base=def_,
            mdef=mdef,
            spd_base=spd
        )
        mind = MindAspect()
        mind.decision.ai_state = ai_state
        interaction = InteractionAspect()
        
        attrs = attributes or Attributes(
            str_=5, agi=5, vit=5, int_=5, spi=5, wis=5, end=5, per=5, cha=5,
        )
        caps = AttributeCaps()
        
        prog = ProgressionAspect(
            level=level, xp=xp,
            attributes=attrs,
            attribute_caps=caps,
            hero_class=hero_class,
        )
        if effects:
            combat.effects = list(effects)
            
        inv = self._make_inventory(weapon, armor)
        skill_list = []
        if skills:
            for sname in skills:
                sdef = SKILL_DEFS.get(sname)
                if sdef:
                    m_val = mastery.get(sname, 0.0) if mastery else 0.0
                    skill_list.append(SkillInstance(skill_id=sname, cooldown_remaining=0, mastery=m_val))
                else:
                    print(f"ERROR_SETUP: Skill {sname} not found in registry!")
        prog.skills = skill_list

        entity = Entity(
            id=eid,
            kind=kind,
            next_act_at=next_act_at,
            identity=identity,
            spatial=spatial,
            combat=combat,
            progression=prog,
            mind=mind,
            interaction=interaction,
            inventory=inv,
        )
        # Apply attribute-derived stat bonuses
        recalc_derived_stats(entity, attrs)
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
        home_pos: tuple[int, int] | None = None,
        **kwargs,
    ) -> Entity:
        """Convenience: add a hero entity with sensible defaults."""
        kwargs.setdefault("faction", Faction.HERO_GUILD)
        kwargs.setdefault("ai_state", AIState.WANDER)
        # Heroes need a home_pos to respawn correctly in the lifecycle system
        h_pos = home_pos or pos
        return self.add_entity(
            eid, kind="hero", pos=pos,
            hero_class=hero_class, weapon=weapon, armor=armor,
            home_pos=h_pos,
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
            tick_events = self.loop.tick_events
            for evt in tick_events:
                print(f"DEBUG_EMIT: {evt.category} {evt.message} metadata={evt.metadata}")
            events.extend(tick_events)
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
        return e is not None and e.combat.alive

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
