"""ProgressionSystem handles level-ups, stamina regeneration, and skill cooldowns."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.systems.infrastructure.base import System
from src.core.models.enums import AIState

if TYPE_CHECKING:
    from src.systems.infrastructure.base import SystemContext

logger = logging.getLogger(__name__)


class ProgressionSystem(System):
    """System for managing entity progression, level-ups, and resource regeneration."""

    def on_tick(self, context: SystemContext, tick: int) -> None:
        """Execute progression sub-phases."""
        self._tick_stamina_and_skills(context)
        self._check_level_ups(context)
        if tick % 100 == 0:
            self._handle_stat_decay(context)

    def _handle_stat_decay(self, context: SystemContext) -> None:
        """Decrease attributes for entities who stay idle for too long."""
        from src.core.gameplay.attributes import decay_attributes
        for entity in context.world.entities.values():
            if not entity.combat.alive or entity.kind == "generator":
                continue
            
            # Decay if idle for > 1000 ticks
            if entity.mind.decision.consecutive_idle_ticks > 1000 and entity.progression.attributes:
                decay_attributes(
                    entity,
                    context.rng,
                    decay_amount=0.1
                )

    def _tick_stamina_and_skills(self, context: SystemContext) -> None:
        """Regenerate stamina and tick skill cooldowns for all entities."""
        for entity in context.world.entities.values():
            if not entity.combat.alive or entity.kind == "generator":
                continue
                
            prog = entity.progression
            if not prog:
                continue
                
            # Pillar 3: Tactical Stamina & Exhaustion
            if prog.stamina <= 0 and entity.mind.decision.ai_state != AIState.EXHAUSTED:
                entity.mind.decision.ai_state = AIState.EXHAUSTED
                logger.info("Tick %s: Entity #%s (%s) is EXHAUSTED!", context.world.tick, entity.id, entity.kind)
            
            # Stamina regen: faster when resting, slower otherwise
            if entity.mind.decision.ai_state == AIState.EXHAUSTED:
                regen = 3 # Recovery is slow but steady
                if prog.stamina >= prog.max_stamina * 0.2:
                    entity.mind.decision.ai_state = AIState.IDLE
                    logger.info("Tick %s: Entity #%s (%s) recovered from exhaustion.", context.world.tick, entity.id, entity.kind)
            elif entity.mind.decision.ai_state in (AIState.RESTING_IN_TOWN, AIState.IDLE):
                regen = 5
            elif entity.mind.decision.ai_state in (AIState.VISIT_SHOP, AIState.VISIT_BLACKSMITH,
                                     AIState.VISIT_GUILD, AIState.VISIT_CLASS_HALL,
                                     AIState.VISIT_INN):
                regen = 4
            else:
                regen = 1
                
            prog.stamina = min(prog.stamina + regen, prog.max_stamina)
            
            # Tick skill cooldowns
            if prog.skills:
                for skill in prog.skills:
                    skill.tick()

    def _check_level_ups(self, context: SystemContext) -> None:
        """Check and apply level-ups and evolution."""
        from src.core.models.enums import RACE_PROFILES
        from src.core.gameplay.attributes import recalc_derived_stats
        
        cfg = context.config
        world = context.world
        
        for entity in world.entities.values():
            if not entity.combat.alive or entity.kind == "generator":
                continue
                
            prog = entity.progression
            combat = entity.combat
            if not prog or not combat:
                continue
                
            # Look up racial profile
            profile = RACE_PROFILES.get(entity.kind, None)
            if not profile:
                base_race = entity.kind.split('_')[0]
                profile = RACE_PROFILES.get(base_race)
                
            if not profile or profile.train_rate == 0.0:
                continue
                
            max_level = min(cfg.max_level, profile.level_cap)
            
            # 1. Check Level Ups
            leveled_up = False
            while prog.xp >= prog.xp_to_next and prog.level < max_level:
                prog.xp -= prog.xp_to_next
                prog.level += 1
                new_level = prog.level
                leveled_up = True
                
                # Check if milestone level
                milestone = cfg.milestone_levels.get(new_level)
                
                if milestone:
                    hp_growth, atk_growth, def_growth, spd_growth = milestone
                    combat.max_hp += hp_growth
                    combat.hp = min(combat.hp + hp_growth, combat.max_hp)
                    combat.atk_base += atk_growth
                    combat.matk += atk_growth
                    combat.def_base += def_growth
                    combat.spd_base += spd_growth
                else:
                    # Normal diminishing returns stat growth
                    if new_level <= 10:
                        hp_g, atk_g, def_g, spd_g = 5, 1, 1, 1
                    elif new_level <= 20:
                        hp_g, atk_g, def_g, spd_g = 3, 1, 1, 1
                    else:
                        hp_g, atk_g, def_g, spd_g = 2, 0, 0, 0
                        
                    combat.max_hp += hp_g
                    combat.hp = min(combat.hp + hp_g, combat.max_hp)
                    combat.atk_base += atk_g
                    combat.matk += atk_g
                    combat.def_base += def_g
                    combat.spd_base += spd_g
                
                # Bracketed XP curve
                if new_level < 10:
                    scale = 1.4
                elif new_level < 20:
                    scale = 1.6
                else:
                    scale = 2.0
                prog.xp_to_next = int(prog.xp_to_next * scale)
                
                # Recalculate derived stats if attributes exist
                if entity.progression.attributes:
                    from src.core.gameplay.attributes import recalc_derived_stats as _recalc, check_breakthroughs
                    # 1. Update breakthroughs (milestones)
                    check_breakthroughs(entity)
                    # 2. Re-derive stats (includes breakthrough bonuses)
                    _recalc(entity, entity.progression.attributes)
                
                # Talent Points at level 25, 50, etc.
                if new_level % 25 == 0:
                    prog.talent_points += 1
                    
                logger.info("Tick %s: Entity #%s (%s) leveled up to %s!", 
                            world.tick, entity.id, entity.kind, new_level)
                if hasattr(world, "event_bus") and world.event_bus:
                    from src.core.data.events import LevelUpEvent
                    world.event_bus.publish(LevelUpEvent(
                        entity_id=entity.id,
                        old_level=new_level - 1,
                        new_level=new_level,
                        attribute_gains={"max_hp": combat.max_hp, "atk": combat.atk, "def": combat.def_, "spd": combat.spd}
                    ))

            # 2. Check Evolution (Phase D)
            if (profile.evolves 
                and prog.level >= profile.level_cap
                and entity.identity.tier < 3):
                self._evolve_entity(context, entity, profile)

    def _evolve_entity(self, context: SystemContext, entity: Any, profile: Any) -> None:
        """Transform an entity into its next tier (Phase D)."""
        from src.core.gameplay.items.items import TIER_KIND_NAMES, RACE_TIER_KINDS, RACE_STARTING_GEAR, TIER_STARTING_GEAR
        from src.core.gameplay.attributes import recalc_derived_stats
        
        base_race = entity.kind.split('_')[0]
        next_tier = entity.identity.tier + 1
        
        # Determine new kind
        tier_kinds = RACE_TIER_KINDS.get(base_race)
        if tier_kinds:
            new_kind = tier_kinds.get(next_tier)
            if not new_kind or new_kind == entity.kind and next_tier < 3:
                next_tier += 1
                new_kind = tier_kinds.get(next_tier)
        else:
            new_kind = TIER_KIND_NAMES.get(next_tier)
            
        if not new_kind:
            return

        old_kind = entity.kind
        entity.kind = new_kind
        entity.identity.tier = next_tier
        
        prog = entity.progression
        combat = entity.combat
        
        # Reset level and scale stats
        prog.level = 1
        prog.xp = 0
        prog.xp_to_next = 100 
        
        # Evolution Bonus
        combat.max_hp += 30
        combat.hp = combat.max_hp
        combat.atk_base += 8
        combat.def_base += 3
        combat.spd_base += 2
        
        # Attribute cap boost
        if entity.progression.attribute_caps:
            entity.progression.attribute_caps.increase_all(10)
            
        # Recalculate
        if entity.progression.attributes:
            recalc_derived_stats(entity, entity.progression.attributes)

        if context.generator and entity.inventory:
            context.generator.equip_entity(entity)

        logger.info("Tick %s: Entity %s (%s) evolved into %s (Tier %s)!", 
                    context.world.tick, entity.id, old_kind, new_kind, next_tier)
        context.emit("evolution", f"Entity {entity.id}: {old_kind} → {new_kind}!",
                   (entity.id,),
                   {"entity_id": entity.id, "old_kind": old_kind, "new_kind": new_kind, "tier": next_tier})
