"""Entity generators — spawners that create new entities periodically."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.attributes import Attributes, AttributeCaps
from src.core.enums import AIState, Domain, EnemyTier
from src.core.faction import Faction
from src.core.items import (
    Inventory, LOOT_TABLES, TIER_KIND_NAMES, TIER_STARTING_GEAR, ITEM_REGISTRY,
    RACE_TIER_KINDS, RACE_STARTING_GEAR, RACE_STAT_MODS, RACE_LOOT_TABLES, RACE_FACTION,
)
from src.core.models import Entity, Stats, Vector2

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

        # Determine tier if not specified
        if tier is None:
            tier = self._roll_tier(eid, tick)

        # Position
        if near_pos is not None:
            # Spawn near a specific position (e.g., camp)
            ox = self._rng.next_int(Domain.SPAWN, eid, tick, -3, 3)
            oy = self._rng.next_int(Domain.SPAWN, eid, tick + 1, -3, 3)
            pos = Vector2(near_pos.x + ox, near_pos.y + oy)
        else:
            x = self._rng.next_int(Domain.SPAWN, eid, tick, 0, world.grid.width - 1)
            y = self._rng.next_int(Domain.SPAWN, eid, tick + 1, 0, world.grid.height - 1)
            pos = Vector2(x, y)

        # Ensure walkable spawn (goblins can't spawn on TOWN or SANCTUARY tiles)
        if not world.grid.is_walkable(pos) or world.grid.is_town(pos) or world.grid.is_sanctuary(pos):
            pos = self._find_nearest_walkable_non_town(world, pos)

        # Base stats with tier multipliers
        hp_m, atk_m, def_base, spd_mod, crit, evasion, luck = _TIER_STATS.get(
            tier, _TIER_STATS[EnemyTier.BASIC])

        base_hp = int((15 + self._rng.next_int(Domain.SPAWN, eid, tick + 2, 0, 10)) * hp_m)
        base_atk = int((3 + self._rng.next_int(Domain.SPAWN, eid, tick + 3, 0, 4)) * atk_m)
        base_spd = 8 + self._rng.next_int(Domain.SPAWN, eid, tick + 4, 0, 4) + spd_mod
        base_def = def_base + self._rng.next_int(Domain.SPAWN, eid, tick + 5, 0, 2)

        # Level scales with tier
        level = 1 + tier
        xp_to_next = int(100 * (1.5 ** (level - 1)))

        kind = TIER_KIND_NAMES.get(tier, "goblin")

        stats = Stats(
            hp=base_hp, max_hp=base_hp, atk=base_atk, def_=base_def,
            spd=max(base_spd, 1), luck=luck, crit_rate=crit, crit_dmg=1.5,
            evasion=evasion, level=level, xp=0, xp_to_next=xp_to_next, gold=self._rng.next_int(Domain.LOOT, eid, tick, 0, 10 + tier * 10),
        )

        # Build inventory with starting gear + potions
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

        # Give some potions based on tier
        potion_count = self._rng.next_int(Domain.ITEM, eid, tick, 0, 1 + tier)
        for i in range(potion_count):
            if tier >= EnemyTier.WARRIOR:
                inv.add_item("medium_hp_potion")
            else:
                inv.add_item("small_hp_potion")

        # Random extra loot from loot table
        loot_table = LOOT_TABLES.get(tier, [])
        for item_id, chance in loot_table:
            if self._rng.next_bool(Domain.LOOT, eid, tick + 10 + hash(item_id) % 100, chance * 0.3):
                inv.add_item(item_id)

        # Determine initial AI state and home
        if tier == EnemyTier.ELITE:
            ai_state = AIState.GUARD_CAMP
        elif near_pos is not None:
            ai_state = AIState.GUARD_CAMP
        else:
            ai_state = AIState.WANDER

        # Generate attributes scaled by tier
        attr_base = 3 + tier * 2
        attrs = Attributes(
            str_=attr_base + self._rng.next_int(Domain.SPAWN, eid, tick + 20, 0, 3),
            agi=attr_base + self._rng.next_int(Domain.SPAWN, eid, tick + 21, 0, 3),
            vit=attr_base + self._rng.next_int(Domain.SPAWN, eid, tick + 22, 0, 3),
            int_=max(1, attr_base - 2 + self._rng.next_int(Domain.SPAWN, eid, tick + 23, 0, 2)),
            wis=max(1, attr_base - 2 + self._rng.next_int(Domain.SPAWN, eid, tick + 24, 0, 2)),
            end=attr_base + self._rng.next_int(Domain.SPAWN, eid, tick + 25, 0, 3),
        )
        caps = AttributeCaps(
            str_cap=15 + tier * 5, agi_cap=15 + tier * 5, vit_cap=15 + tier * 5,
            int_cap=10 + tier * 3, wis_cap=10 + tier * 3, end_cap=15 + tier * 5,
        )
        stamina = 30 + attrs.end * 2
        stats.stamina = stamina
        stats.max_stamina = stamina

        # Add race skills
        from src.core.classes import RACE_SKILLS, SKILL_DEFS, SkillInstance
        race_skill_ids = RACE_SKILLS.get(kind, [])
        skills = [SkillInstance(skill_id=sid) for sid in race_skill_ids if sid in SKILL_DEFS]

        entity = Entity(
            id=eid, kind=kind, pos=pos,
            stats=stats, ai_state=ai_state,
            faction=Faction.GOBLIN_HORDE,
            next_act_at=float(tick),
            home_pos=near_pos,
            tier=tier,
            inventory=inv,
            attributes=attrs,
            attribute_caps=caps,
            skills=skills,
        )
        return entity

    def spawn_race(
        self, world: WorldState, race: str,
        tier: int | None = None, near_pos: Vector2 | None = None,
    ) -> Entity:
        """Spawn a race-specific entity (wolf, bandit, undead, orc)."""
        eid = world.allocate_entity_id()
        tick = world.tick

        if tier is None:
            tier = self._roll_tier(eid, tick)

        # Position
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
        xp_to_next = int(100 * (1.5 ** (level - 1)))

        kind_map = RACE_TIER_KINDS.get(race, {})
        kind = kind_map.get(tier, race)

        stats = Stats(
            hp=max(base_hp, 5), max_hp=max(base_hp, 5),
            atk=max(base_atk, 1), def_=max(base_def, 0),
            spd=max(base_spd, 1), luck=r_luck + t_luck,
            crit_rate=r_crit + t_crit, crit_dmg=1.5,
            evasion=r_evasion + t_evasion, level=level,
            xp=0, xp_to_next=xp_to_next,
            gold=self._rng.next_int(Domain.LOOT, eid, tick, 0, 10 + tier * 10),
        )

        inv = Inventory(
            items=[],
            max_slots=self._config.goblin_inventory_slots + tier,
            max_weight=self._config.goblin_inventory_weight + tier * 3.0,
        )

        # Race-specific starting gear
        race_gear = RACE_STARTING_GEAR.get(race, {})
        gear = race_gear.get(tier, {})
        for slot in ("weapon", "armor", "accessory"):
            item_id = gear.get(slot)
            if item_id and item_id in ITEM_REGISTRY:
                setattr(inv, slot, item_id)

        # Loot from race-specific tables
        loot_table = RACE_LOOT_TABLES.get(kind, [])
        for item_id, chance in loot_table:
            if self._rng.next_bool(Domain.LOOT, eid, tick + 10 + hash(item_id) % 100, chance * 0.3):
                inv.add_item(item_id)

        faction = RACE_FACTION.get(race, Faction.GOBLIN_HORDE)

        if tier == EnemyTier.ELITE:
            ai_state = AIState.GUARD_CAMP
        elif near_pos is not None:
            ai_state = AIState.GUARD_CAMP
        else:
            ai_state = AIState.WANDER

        # Generate attributes scaled by tier + race modifiers
        attr_base = 3 + tier * 2
        r_str = int(r_atk_m * 3)  # races with high ATK get more STR
        r_agi = r_spd_mod          # races with high SPD get more AGI
        r_vit = int(r_hp_m * 3)    # races with high HP get more VIT
        attrs = Attributes(
            str_=max(1, attr_base + r_str + self._rng.next_int(Domain.SPAWN, eid, tick + 20, 0, 3)),
            agi=max(1, attr_base + r_agi + self._rng.next_int(Domain.SPAWN, eid, tick + 21, 0, 3)),
            vit=max(1, attr_base + r_vit + self._rng.next_int(Domain.SPAWN, eid, tick + 22, 0, 3)),
            int_=max(1, attr_base - 2 + self._rng.next_int(Domain.SPAWN, eid, tick + 23, 0, 2)),
            wis=max(1, attr_base - 2 + self._rng.next_int(Domain.SPAWN, eid, tick + 24, 0, 2)),
            end=max(1, attr_base + self._rng.next_int(Domain.SPAWN, eid, tick + 25, 0, 3)),
        )
        caps = AttributeCaps(
            str_cap=15 + tier * 5, agi_cap=15 + tier * 5, vit_cap=15 + tier * 5,
            int_cap=10 + tier * 3, wis_cap=10 + tier * 3, end_cap=15 + tier * 5,
        )
        stamina = 30 + attrs.end * 2
        stats.stamina = stamina
        stats.max_stamina = stamina

        # Add race skills
        from src.core.classes import RACE_SKILLS, SKILL_DEFS, SkillInstance
        race_skill_ids = RACE_SKILLS.get(kind, [])
        skills = [SkillInstance(skill_id=sid) for sid in race_skill_ids if sid in SKILL_DEFS]

        return Entity(
            id=eid, kind=kind, pos=pos,
            stats=stats, ai_state=ai_state,
            faction=faction,
            next_act_at=float(tick),
            home_pos=near_pos,
            tier=tier,
            inventory=inv,
            attributes=attrs,
            attribute_caps=caps,
            skills=skills,
        )

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
