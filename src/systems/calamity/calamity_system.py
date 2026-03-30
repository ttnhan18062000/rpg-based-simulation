"""CalamitySystem manages world boss spawns and global maturity."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.core.models.enums import Domain, EnemyTier, EntityRole
from src.core.models import Vector2
from src.systems.infrastructure.base import System

if TYPE_CHECKING:
    from src.systems.infrastructure.base import SystemContext

logger = logging.getLogger(__name__)


class CalamitySystem(System):
    """System for periodic world events and world boss orchestration."""

    def on_tick(self, context: SystemContext, tick: int) -> None:
        """Execute calamity phases."""
        self._update_world_evolution(context, tick)
        self._check_calamity_spawns(context, tick)
        self._apply_calamity_auras(context, tick)
        self._check_camp_reinforcements(context, tick)
        self._check_faction_raids(context, tick)

    def _update_world_evolution(self, context: SystemContext, tick: int) -> None:
        """Advance world 'maturity' which affects spawn rates and boss stats."""
        cfg = context.config
        world = context.world
        
        # World 'matures' every N ticks, increasing global difficulty
        if tick % 1000 == 0 and tick > 0:
            world.maturity = getattr(world, "maturity", 0) + 1
            if context.emit:
                context.emit("world", f"World maturity increased to level {world.maturity}",
                          metadata={"maturity": world.maturity})

    def _check_calamity_spawns(self, context: SystemContext, tick: int) -> None:
        """Randomly spawn a World Boss if conditions are met."""
        cfg = context.config
        world = context.world
        rng = context.rng
        
        # Check spawn interval
        last_spawn = getattr(world, "last_calamity_tick", 0)
        if tick - last_spawn < 2000 and tick > 0:
            return

        # Guaranteed spawn at 5000/10000 etc. or random chance
        force_spawn = (tick % 5000 == 0 and tick > 0)
        if force_spawn or rng.next_bool(Domain.SPAWN, 0, tick, 0.005):
            self._spawn_world_boss(context, tick)
            world.last_calamity_tick = tick

    def _spawn_world_boss(self, context: SystemContext, tick: int) -> None:
        """Construct and add a World Boss entity and bounty quests."""
        world = context.world
        gen = context.generator
        
        # Position far from town
        pos = Vector2(
            x=context.rng.next_int(Domain.SPAWN, 0, tick, 10, world.grid.width-10),
            y=context.rng.next_int(Domain.SPAWN, 0, tick + 1, 10, world.grid.height-10)
        )
        
        boss = gen.spawn_calamity(world, "gorath") if hasattr(gen, 'spawn_calamity') else gen.spawn_boss(world, pos=pos)
        boss.spatial.pos = pos
        boss.identity.role = EntityRole.WORLD_BOSS
        
        world.add_entity(boss)
        
        # Generate bounties for all high-level heroes
        from src.core.gameplay.quests import Quest, QuestType
        for hero in world.entities.values():
            if hero.combat.alive and hero.identity.role == EntityRole.HERO:
                bounty = Quest(
                    quest_id=f"bounty_{boss.kind}_{tick}_{hero.id}",
                    quest_type=QuestType.BOUNTY,
                    title=f"Bounty: {boss.identity.display_name}",
                    description=f"A great calamity has appeared! Defeat {boss.identity.display_name} to restore peace.",
                    target_kind=boss.identity.display_name,
                    target_count=1,
                    gold_reward=1000,
                    xp_reward=1000
                )
                hero.progression.quests.append(bounty)

        if context.emit:
            context.emit("calamity", f"A great calamity has appeared: {boss.identity.display_name} at {pos}!",
                      entity_ids=(boss.id,),
                      metadata={"kind": boss.kind, "pos": (pos.x, pos.y)})
        logger.warning("Tick %d: Spawned World Boss %s #%d at %s", tick, boss.identity.display_name, boss.id, pos)

    def _apply_calamity_auras(self, context: SystemContext, tick: int) -> None:
        """World Bosses emit global debuffs or local terrain effects."""
        world = context.world
        for entity in world.entities.values():
            if not entity.combat.alive or entity.identity.role != EntityRole.WORLD_BOSS:
                continue
                
            # Local aura: slow nearby non-bosses
            for other in world.entities_at_radius(entity.spatial.pos, 5):
                if other.id != entity.id and other.identity.role != EntityRole.WORLD_BOSS:
                    from src.core.gameplay.effects import skill_effect
                    other.combat.effects.append(skill_effect(
                        spd_mod=-0.3,
                        duration=2,
                        source="Calamity Aura",
                        is_debuff=True
                    ))

    def _check_camp_reinforcements(self, context: SystemContext, tick: int) -> None:
        """Reinforce camps every 500 ticks."""
        if tick % 500 != 0 or tick == 0:
            return
            
        world = context.world
        gen = context.generator
        cfg = context.config
        
        for region in world.regions:
            for loc in region.locations:
                if loc.location_type == "enemy_camp":
                    guards = [e for e in world.entities_at_radius(loc.pos, cfg.camp_radius) 
                              if e.identity.role == EntityRole.MOB and e.spatial.home_pos and e.spatial.home_pos.manhattan(loc.pos) <= cfg.camp_radius]
                    
                    if len(guards) < cfg.camp_max_guards // 2:
                        target_tier = region.difficulty + loc.reinforcement_level
                        mob = gen.spawn(world, tier=min(target_tier, 3), near_pos=loc.pos, difficulty_tier=region.difficulty)
                        world.add_entity(mob)
                    elif len(guards) >= cfg.camp_max_guards:
                        loc.reinforcement_level = min(loc.reinforcement_level + 1, 3)

    def _check_faction_raids(self, context: SystemContext, tick: int) -> None:
        """Spawn a raid targeting the town based on world_day."""
        cfg = context.config
        world = context.world
        gen = context.generator
        
        ticks_per_day = 100
        raid_interval_ticks = cfg.raid_interval_days * ticks_per_day
        if tick % raid_interval_ticks != 0 or tick == 0:
            return
            
        raid_size = cfg.raid_base_strength + (world.world_day // 10)
        
        angle = context.rng.next_float(Domain.CALAMITY, 0, tick) * 6.28
        import math
        dist = cfg.sanctuary_radius + 5
        spawn_pos = Vector2(
            int(cfg.town_center_x + math.cos(angle) * dist),
            int(cfg.town_center_y + math.sin(angle) * dist)
        )
        if not world.grid.is_walkable(spawn_pos):
            spawn_pos = gen._find_nearest_walkable_non_town(world, spawn_pos)
            
        from src.core.models.enums import AIState
        for i in range(raid_size):
            mob = gen.spawn(world, tier=max(1, min(world.world_day // 50, 3)), near_pos=spawn_pos, difficulty_tier=4)
            mob.mind.decision.ai_state = AIState.RAID
            mob.spatial.home_pos = None  # Raid mobs don't return home
            world.add_entity(mob)
            
        if context.emit:
            context.emit("raid", f"A faction raid party of {raid_size} enemies approaches the town!", metadata={"size": raid_size})
        logger.warning("Tick %d: Faction Raid spawned at %s with %d enemies.", tick, spawn_pos, raid_size)
