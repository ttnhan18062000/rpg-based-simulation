"""Entity generators — spawners that create new entities periodically."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.core.gameplay.classes import mob_class_for
from src.core.entities.entity_builder import EntityBuilder
from src.core.models.enums import AIState, Domain, EnemyTier, RACE_PROFILES
from src.core.gameplay.faction import Faction
from src.core.gameplay.items.item_registry import ITEM_REGISTRY, ItemTemplate
from src.core.world.spawn_config import SPAWN_CONFIGS, LOOT_CONFIGS
from src.core.entities.entity import Entity, Vector2, Inventory
from src.core.world.regions import DIFFICULTY_TIERS

if TYPE_CHECKING:
    from src.config import SimulationConfig
    from src.core.models.world_state import WorldState
    from src.platform.rng import DeterministicRNG


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
        alive_count = sum(1 for e in world.entities.values() if e.kind != "generator" and e.combat.alive)
        return (
            world.tick % self._config.generator_spawn_interval == 0
            and alive_count < self._config.generator_max_entities
        )

    def equip_entity(self, entity: Entity) -> None:
        """Refresh an entity's equipment based on its current race and tier."""
        from src.core.gameplay.items.items import RACE_STARTING_GEAR, TIER_STARTING_GEAR
        from src.core.gameplay.items.item_registry import ITEM_REGISTRY

        if not entity.inventory:
            return

        base_race = entity.kind.split('_')[0]
        tier = entity.tier
        
        gear = RACE_STARTING_GEAR.get(base_race, {}).get(tier)
        if not gear:
            gear = TIER_STARTING_GEAR.get(tier)
            
        if gear:
            for item_id in gear.values():
                if item_id in ITEM_REGISTRY:
                    entity.inventory.add_item(item_id)
                    entity.inventory.auto_equip_best(item_id)

    def spawn_calamity(self, world: WorldState, template_id: str) -> Entity:
        """Spawn a unique World Boss (Calamity)."""
        from src.core.models.calamities import CALAMITY_TEMPLATES
        from src.core.models.enums import Domain, EntityRole

        template = CALAMITY_TEMPLATES.get(template_id)
        if not template:
            raise ValueError(f"Unknown calamity template: {template_id}")

        eid = world.allocate_entity_id()
        tick = world.tick

        # Calamity stats are significantly higher than Elites
        mult = template.stat_multiplier
        world_mod = world.difficulty_modifier
        
        # Scale stats
        base_hp = int(100 * mult * world_mod)
        base_atk = int(20 * mult * world_mod)
        base_def = int(10 * mult)
        
        # The Generator doesn't have a context-aware logger yet, but we can at least make this JSON-safe
        # by using a named logger. However, it's better to use the root logger which is already configured.
        logging.getLogger("generator").info(
            "Spawning calamity: %s", template_id,
            extra={'tick': tick, 'entity_id': eid, 'component': 'generator'}
        )
        
        base_spd = 12 + self._rng.next_int(Domain.SPAWN, eid, tick, 0, 4)
        pos = self._resolve_position(world, eid, tick, None)
        
        inv = Inventory(items=[], max_slots=20, max_weight=100.0)
        for item_id in template.legendary_loot:
            inv.add_item(item_id)
            inv.auto_equip_best(item_id)

        builder = EntityBuilder(self._rng, eid, tick=tick)
        entity = (
            builder
            .kind(template_id)
            .with_identity(display_name=template.name)
            .at(pos)
            .ai_state(AIState.WANDER)
            .faction(template.faction)
            .role(EntityRole.WORLD_BOSS)
            .with_base_stats(
                hp=base_hp, atk=base_atk, def_=base_def, spd=base_spd,
                luck=20, crit_rate=0.2, crit_dmg=2.0, evasion=0.1,
                level=30, xp_to_next=999999,
                gold=5000,
            )
            .with_existing_inventory(inv)
            .with_mob_class(template.archetype)
            .with_mob_attributes(50, 4)
            .with_traits(trait_ids=template.traits)
            .is_world_boss(True)
            .build()
        )
        return entity

    def spawn(
        self, world: WorldState, tier: int | None = None,
        near_pos: Vector2 | None = None, difficulty_tier: int = 1,
    ) -> Entity:
        """Create a new tiered entity, picking race based on terrain."""
        eid = world.allocate_entity_id()
        tick = world.tick

        if tier is None:
            # We don't know the race yet, so pass None for faction
            tier = self._roll_tier(eid, tick, faction=None, world=world)

        pos = self._resolve_position(world, eid, tick, near_pos)
        
        # Terrain-based race lookup (using fallback to goblin)
        terrain_type = int(world.grid.get(pos)) if hasattr(world, "grid") else 1
        from src.core.gameplay.items.items import TERRAIN_RACE
        race = TERRAIN_RACE.get(terrain_type, "goblin")
        
        return self.spawn_race(world, race, tier=tier, near_pos=pos, difficulty_tier=difficulty_tier)

    def spawn_race(
        self, world: WorldState, race: str,
        tier: int | None = None, near_pos: Vector2 | None = None,
        difficulty_tier: int = 1,
    ) -> Entity:
        """Spawn a race-specific entity."""
        eid = world.allocate_entity_id()
        tick = world.tick

        pos = self._resolve_position(world, eid, tick, near_pos)
        
        # Milestone 7: Safe-zone Expansion (Regional Suppression)
        is_safe_zone = False
        for r in world.regions:
            dist = pos.manhattan(r.center)
            if dist <= r.radius:
                control = world.region_control.get(r.region_id, 0.0)
                if control > 80.0:
                    is_safe_zone = True
                    # 50% chance to skip spawn in Safe-zones
                    if self._rng.next_int(Domain.SPAWN, eid, tick + 7, 0, 100) < 50:
                        return None 
                break

        if tier is None:
            profile = RACE_PROFILES.get(race)
            faction = profile.factions[0] if profile and profile.factions else Faction.GOBLIN_HORDE
            tier = self._roll_tier(eid, tick, faction=faction, world=world)
            
            # Safe-zones cap tiers at BASIC or SCOUT
            if is_safe_zone:
                tier = min(tier, EnemyTier.SCOUT)
        diff = DIFFICULTY_TIERS.get(difficulty_tier, DIFFICULTY_TIERS[1])

        profile = RACE_PROFILES.get(race)
        race_mods = profile.stat_mods if profile else [1.0, 1.0, 0, 0, 0.05, 0.0, 0]
        r_hp_m, r_atk_m, r_def_mod, r_spd_mod, r_crit, r_evasion, r_luck = race_mods

        hp_m, atk_m, def_base, spd_mod, t_crit, t_evasion, t_luck = _TIER_STATS.get(
            tier, _TIER_STATS[EnemyTier.BASIC])

        # World Age Scaling (Epic 17 Phase 2)
        world_age_mult = 1.0 + (world.world_day / 200) * 0.5
        
        base_hp = int((15 + self._rng.next_int(Domain.SPAWN, eid, tick + 2, 0, 10)) * hp_m * r_hp_m * diff.hp * world_age_mult)
        base_atk = int((3 + self._rng.next_int(Domain.SPAWN, eid, tick + 3, 0, 4)) * atk_m * r_atk_m * diff.atk * world_age_mult)
        base_spd = 8 + self._rng.next_int(Domain.SPAWN, eid, tick + 4, 0, 4) + spd_mod + r_spd_mod
        base_def = int((def_base + r_def_mod + self._rng.next_int(Domain.SPAWN, eid, tick + 5, 0, 2)) * diff.def_ * world_age_mult)

        level_min = diff.level_min + (world.world_day // 50)
        level_max = diff.level_max + (world.world_day // 30)
        level = self._rng.next_int(Domain.SPAWN, eid, tick + 6, level_min, level_max)
        
        spawn_cfg = SPAWN_CONFIGS.get((race, EnemyTier(tier)))
        kind = spawn_cfg.kind if spawn_cfg else race
        
        # Factions are now in RaceProfile
        faction = profile.factions[0] if profile and profile.factions else Faction.GOBLIN_HORDE
        ai_state = self._resolve_ai_state(tier, near_pos)
        inv = self._build_race_inventory(eid, tick, tier, race, kind, difficulty_tier)

        attr_base = 3 + tier * 2
        r_str = int(r_atk_m * 3)
        r_agi = r_spd_mod
        r_vit = int(r_hp_m * 3)
        r_spi = int(r_hp_m * 2) if race == "undead" else 0
        r_per = r_spd_mod
        r_cha = 0

        mob_cls = mob_class_for(race, tier)
        entity = (
            EntityBuilder(self._rng, eid, tick=tick)
            .kind(kind)
            .at(pos)
            .home(near_pos)
            .leash(self._config.mob_leash_radius)
            .ai_state(ai_state)
            .faction(faction)
            .tier(tier)
            .with_base_stats(
                hp=max(base_hp, 5), atk=max(base_atk, 1),
                def_=max(base_def, 0), spd=max(base_spd, 1),
                luck=r_luck + t_luck, crit_rate=r_crit + t_crit, crit_dmg=1.5,
                evasion=r_evasion + t_evasion, level=level,
                xp_to_next=int(100 * (1.5 ** (level - 1))),
                gold=int(self._rng.next_int(Domain.LOOT, eid, tick, 0, 10 + tier * 10) * diff.gold),
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
            .with_talents(race=race)
            .build()
        )
        entity.difficulty_tier = difficulty_tier
        return entity

    def _resolve_position(
        self, world: WorldState, eid: int, tick: int, near_pos: Vector2 | None,
    ) -> Vector2:
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

    def _resolve_ai_state(self, tier: int, near_pos: Vector2 | None) -> AIState:
        if tier == EnemyTier.ELITE or near_pos is not None:
            return AIState.GUARD_CAMP
        return AIState.WANDER

    def _build_race_inventory(
        self, eid: int, tick: int, tier: int, race: str, kind: str,
        difficulty_tier: int = 1,
    ) -> Inventory:
        from src.core.gameplay.items.items import Inventory
        inv = Inventory(
            items=[],
            max_slots=self._config.goblin_inventory_slots + tier,
            max_weight=self._config.goblin_inventory_weight + tier * 3.0,
        )
        
        spawn_cfg = SPAWN_CONFIGS.get((race, EnemyTier(tier)))
        if spawn_cfg:
            for item_id in spawn_cfg.starting_gear:
                if item_id in ITEM_REGISTRY:
                    inv.add_item(item_id)
                    inv.auto_equip_best(item_id)

        # Loot from LootConfig
        loot_cfg = LOOT_CONFIGS.get(kind)
        if loot_cfg:
            from src.core.gameplay.items.items import DIFFICULTY_DROP_MULTIPLIER
            drop_mult = DIFFICULTY_DROP_MULTIPLIER.get(difficulty_tier, 1.0)
            
            # Check for loot
            if self._rng.next_bool(Domain.LOOT, eid, tick, loot_cfg.drop_chance * drop_mult):
                for item_id in loot_cfg.guaranteed_items:
                    inv.add_item(item_id)
                
                # Roll for random pool
                for item_id in loot_cfg.random_pool:
                    if self._rng.next_bool(Domain.LOOT, eid, tick + hash(item_id) % 100, 0.2):
                         inv.add_item(item_id)

        return inv

    def _roll_tier(self, eid: int, tick: int, faction: Faction | None = None, world: WorldState | None = None) -> int:
        roll = self._rng.next_float(Domain.SPAWN, eid, tick + 10)
        
        # War Bonus: Shift distribution towards higher tiers
        war_bonus = 0.0
        if world and faction and world.war_status.get(int(faction), False):
            war_bonus = 0.15 # 15% shift
            
        if roll < (0.55 - war_bonus):
            return EnemyTier.BASIC
        if roll < (0.80 - war_bonus):
            return EnemyTier.SCOUT
        if roll < (0.95 - war_bonus):
            return EnemyTier.WARRIOR
        return EnemyTier.ELITE

    @staticmethod
    def _find_nearest_walkable_non_town(world: WorldState, origin: Vector2) -> Vector2:
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
