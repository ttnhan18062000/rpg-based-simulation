"""Entity generators — spawners that create new entities periodically."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.classes import mob_class_for
from src.core.entity_builder import EntityBuilder
from src.core.enums import AIState, Domain, EnemyTier
from src.core.faction import Faction
from src.core.items import (
    Inventory, LOOT_TABLES, TIER_KIND_NAMES, TIER_STARTING_GEAR, ITEM_REGISTRY,
    RACE_TIER_KINDS, RACE_STARTING_GEAR, RACE_STAT_MODS, RACE_LOOT_TABLES, RACE_FACTION,
)
from src.core.models import Entity, Vector2

if TYPE_CHECKING:
    from src.config import SimulationConfig
    from src.core.world_state import WorldState
    from src.systems.rng import DeterministicRNG


# Stat multipliers per tier: (hp_mult, atk_mult, def_base, spd_mod, crit, evasion, luck)
_TIER_STATS: dict[int, tuple[float, float, int, int, float, float, int]] = {
    EnemyTier.BASIC:   (1.0, 1.0, 0,  0, 0.05, 0.00, 0),
    EnemyTier.SCOUT:   (0.8, 0.9, 0,  3, 0.08, 0.05, 2),
    EnemyTier.WARRIOR: (1.5, 1.3, 3,  -1, 0.07, 0.02, 1),
    EnemyTier.ELITE:   (2.5, 1.8, 6,  0, 0.12, 0.05, 5),
}


class EntityGenerator:
    """Spawns entities at a configurable interval up to a population cap."""

    __slots__ = ("_config", "_rng")

    def __init__(self, config: SimulationConfig, rng: DeterministicRNG) -> None:
        self._config = config
        self._rng = rng

    def should_spawn(self, world: WorldState) -> bool:
        alive_count = sum(1 for e in world.entities.values() if e.kind != "generator" and e.alive)
        return (
            world.tick % self._config.generator_spawn_interval == 0
            and alive_count < self._config.generator_max_entities
        )

    def spawn(self, world: WorldState, tier: int | None = None, near_pos: Vector2 | None = None) -> Entity:
        """Create a new tiered entity with deterministic random stats, equipment, and position."""
        eid = world.allocate_entity_id()
        tick = world.tick

        if tier is None:
            tier = self._roll_tier(eid, tick)

        pos = self._resolve_position(world, eid, tick, near_pos)

        # Base stats with tier multipliers
        hp_m, atk_m, def_base, spd_mod, crit, evasion, luck = _TIER_STATS.get(
            tier, _TIER_STATS[EnemyTier.BASIC])

        base_hp = int((15 + self._rng.next_int(Domain.SPAWN, eid, tick + 2, 0, 10)) * hp_m)
        base_atk = int((3 + self._rng.next_int(Domain.SPAWN, eid, tick + 3, 0, 4)) * atk_m)
        base_spd = 8 + self._rng.next_int(Domain.SPAWN, eid, tick + 4, 0, 4) + spd_mod
        base_def = def_base + self._rng.next_int(Domain.SPAWN, eid, tick + 5, 0, 2)

        level = 1 + tier
        kind = TIER_KIND_NAMES.get(tier, "goblin")
        ai_state = self._resolve_ai_state(tier, near_pos)
        inv = self._build_goblin_inventory(eid, tick, tier)

        mob_cls = mob_class_for("goblin", tier)
        return (
            EntityBuilder(self._rng, eid, tick=tick)
            .kind(kind)
            .at(pos)
            .home(near_pos)
            .ai_state(ai_state)
            .faction(Faction.GOBLIN_HORDE)
            .tier(tier)
            .with_base_stats(
                hp=base_hp, atk=base_atk, def_=base_def, spd=max(base_spd, 1),
                luck=luck, crit_rate=crit, crit_dmg=1.5, evasion=evasion,
                level=level, xp_to_next=int(100 * (1.5 ** (level - 1))),
                gold=self._rng.next_int(Domain.LOOT, eid, tick, 0, 10 + tier * 10),
            )
            .with_existing_inventory(inv)
            .with_mob_class(mob_cls)
            .with_mob_attributes(3 + tier * 2, tier)
            .with_race_skills(kind)
            .with_traits(race_prefix="goblin")
            .build()
        )

    def spawn_race(
        self, world: WorldState, race: str,
        tier: int | None = None, near_pos: Vector2 | None = None,
    ) -> Entity:
        """Spawn a race-specific entity (wolf, bandit, undead, orc)."""
        eid = world.allocate_entity_id()
        tick = world.tick

        if tier is None:
            tier = self._roll_tier(eid, tick)

        pos = self._resolve_position(world, eid, tick, near_pos)

        # Race-specific stats
        race_mods = RACE_STAT_MODS.get(race, (1.0, 1.0, 0, 0, 0.05, 0.0, 0))
        r_hp_m, r_atk_m, r_def_mod, r_spd_mod, r_crit, r_evasion, r_luck = race_mods

        # Tier multipliers on top of race
        hp_m, atk_m, def_base, spd_mod, t_crit, t_evasion, t_luck = _TIER_STATS.get(
            tier, _TIER_STATS[EnemyTier.BASIC])

        base_hp = int((15 + self._rng.next_int(Domain.SPAWN, eid, tick + 2, 0, 10)) * hp_m * r_hp_m)
        base_atk = int((3 + self._rng.next_int(Domain.SPAWN, eid, tick + 3, 0, 4)) * atk_m * r_atk_m)
        base_spd = 8 + self._rng.next_int(Domain.SPAWN, eid, tick + 4, 0, 4) + spd_mod + r_spd_mod
        base_def = def_base + r_def_mod + self._rng.next_int(Domain.SPAWN, eid, tick + 5, 0, 2)

        level = 1 + tier
        kind_map = RACE_TIER_KINDS.get(race, {})
        kind = kind_map.get(tier, race)
        faction = RACE_FACTION.get(race, Faction.GOBLIN_HORDE)
        ai_state = self._resolve_ai_state(tier, near_pos)
        inv = self._build_race_inventory(eid, tick, tier, race, kind)

        # Race attribute modifiers
        attr_base = 3 + tier * 2
        r_str = int(r_atk_m * 3)  # races with high ATK get more STR
        r_agi = r_spd_mod          # races with high SPD get more AGI
        r_vit = int(r_hp_m * 3)    # races with high HP get more VIT
        r_spi = int(r_hp_m * 2) if race == "undead" else 0  # undead have more spirit
        r_per = r_spd_mod  # fast races are more perceptive
        r_cha = 0  # monsters generally have low charisma

        mob_cls = mob_class_for(race, tier)
        return (
            EntityBuilder(self._rng, eid, tick=tick)
            .kind(kind)
            .at(pos)
            .home(near_pos)
            .ai_state(ai_state)
            .faction(faction)
            .tier(tier)
            .with_base_stats(
                hp=max(base_hp, 5), atk=max(base_atk, 1),
                def_=max(base_def, 0), spd=max(base_spd, 1),
                luck=r_luck + t_luck, crit_rate=r_crit + t_crit, crit_dmg=1.5,
                evasion=r_evasion + t_evasion, level=level,
                xp_to_next=int(100 * (1.5 ** (level - 1))),
                gold=self._rng.next_int(Domain.LOOT, eid, tick, 0, 10 + tier * 10),
            )
            .with_existing_inventory(inv)
            .with_mob_class(mob_cls)
            .with_race_attributes(
                attr_base, tier,
                r_str=r_str, r_agi=r_agi, r_vit=r_vit,
                r_spi=r_spi, r_per=r_per, r_cha=r_cha,
            )
            .with_race_skills(kind)
            .with_traits(race_prefix=race)
            .build()
        )

    # -------------------------------------------------------------------
    # Shared helpers
    # -------------------------------------------------------------------

    def _resolve_position(
        self, world: WorldState, eid: int, tick: int, near_pos: Vector2 | None,
    ) -> Vector2:
        """Calculate a valid spawn position, ensuring walkability."""
        if near_pos is not None:
            ox = self._rng.next_int(Domain.SPAWN, eid, tick, -3, 3)
            oy = self._rng.next_int(Domain.SPAWN, eid, tick + 1, -3, 3)
            pos = Vector2(near_pos.x + ox, near_pos.y + oy)
        else:
            x = self._rng.next_int(Domain.SPAWN, eid, tick, 0, world.grid.width - 1)
            y = self._rng.next_int(Domain.SPAWN, eid, tick + 1, 0, world.grid.height - 1)
            pos = Vector2(x, y)

        if not world.grid.is_walkable(pos) or world.grid.is_town(pos) or world.grid.is_sanctuary(pos):
            pos = self._find_nearest_walkable_non_town(world, pos)
        return pos

    @staticmethod
    def _resolve_ai_state(tier: int, near_pos: Vector2 | None) -> AIState:
        """Determine initial AI state based on tier and spawn location."""
        if tier == EnemyTier.ELITE or near_pos is not None:
            return AIState.GUARD_CAMP
        return AIState.WANDER

    def _build_goblin_inventory(self, eid: int, tick: int, tier: int) -> Inventory:
        """Build inventory with tier-based starting gear, potions, and loot."""
        inv = Inventory(
            items=[],
            max_slots=self._config.goblin_inventory_slots + tier,
            max_weight=self._config.goblin_inventory_weight + tier * 3.0,
        )

        # Starting equipment from tier template
        gear = TIER_STARTING_GEAR.get(tier, {})
        for slot in ("weapon", "armor", "accessory"):
            item_id = gear.get(slot)
            if item_id and item_id in ITEM_REGISTRY:
                setattr(inv, slot, item_id)

        # Potions based on tier
        potion_count = self._rng.next_int(Domain.ITEM, eid, tick, 0, 1 + tier)
        potion_type = "medium_hp_potion" if tier >= EnemyTier.WARRIOR else "small_hp_potion"
        for _ in range(potion_count):
            inv.add_item(potion_type)

        # Random extra loot
        loot_table = LOOT_TABLES.get(tier, [])
        for item_id, chance in loot_table:
            if self._rng.next_bool(Domain.LOOT, eid, tick + 10 + hash(item_id) % 100, chance * 0.3):
                inv.add_item(item_id)

        return inv

    def _build_race_inventory(
        self, eid: int, tick: int, tier: int, race: str, kind: str,
    ) -> Inventory:
        """Build inventory with race-specific starting gear and loot."""
        inv = Inventory(
            items=[],
            max_slots=self._config.goblin_inventory_slots + tier,
            max_weight=self._config.goblin_inventory_weight + tier * 3.0,
        )

        race_gear = RACE_STARTING_GEAR.get(race, {})
        gear = race_gear.get(tier, {})
        for slot in ("weapon", "armor", "accessory"):
            item_id = gear.get(slot)
            if item_id and item_id in ITEM_REGISTRY:
                setattr(inv, slot, item_id)

        loot_table = RACE_LOOT_TABLES.get(kind, [])
        for item_id, chance in loot_table:
            if self._rng.next_bool(Domain.LOOT, eid, tick + 10 + hash(item_id) % 100, chance * 0.3):
                inv.add_item(item_id)

        return inv

    def _roll_tier(self, eid: int, tick: int) -> int:
        """Deterministic tier roll: mostly BASIC, occasionally higher."""
        roll = self._rng.next_float(Domain.SPAWN, eid, tick + 10)
        if roll < 0.55:
            return EnemyTier.BASIC
        if roll < 0.80:
            return EnemyTier.SCOUT
        if roll < 0.95:
            return EnemyTier.WARRIOR
        return EnemyTier.ELITE

    @staticmethod
    def _find_nearest_walkable(world: WorldState, origin: Vector2) -> Vector2:
        """BFS spiral out from origin to find the nearest walkable tile."""
        from collections import deque

        visited: set[tuple[int, int]] = set()
        queue: deque[Vector2] = deque([origin])
        while queue:
            pos = queue.popleft()
            if world.grid.is_walkable(pos):
                return pos
            for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
                npos = Vector2(pos.x + dx, pos.y + dy)
                key = (npos.x, npos.y)
                if key not in visited and world.grid.in_bounds(npos):
                    visited.add(key)
                    queue.append(npos)
        return origin

    @staticmethod
    def _find_nearest_walkable_non_town(world: WorldState, origin: Vector2) -> Vector2:
        """BFS to find the nearest walkable non-TOWN tile (for goblin spawns)."""
        from collections import deque

        visited: set[tuple[int, int]] = set()
        queue: deque[Vector2] = deque([origin])
        while queue:
            pos = queue.popleft()
            if world.grid.is_walkable(pos) and not world.grid.is_town(pos):
                return pos
            for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
                npos = Vector2(pos.x + dx, pos.y + dy)
                key = (npos.x, npos.y)
                if key not in visited and world.grid.in_bounds(npos):
                    visited.add(key)
                    queue.append(npos)
        return origin
