"""Hero Lifecycle System — Manages hero specific progression events like familiarity and permadeath."""

import logging
from src.systems.infrastructure.base import System, SystemContext
from src.core.models.world_state import WorldState
from src.core.models.enums import AIState, ItemType, Domain
from src.core.gameplay.faction import Faction
from src.core.world.monuments import Monument

logger = logging.getLogger(__name__)


class HeroLifecycleSystem(System):
    """System to extract Hero-specific tick constraints, bonding, and permadeath spanning."""

    def __init__(self, config, rng):
        super().__init__(config, rng)
        self._pending_hero_replacements: list[dict] = []

    def on_tick(self, ctx: SystemContext, tick: int) -> None:
        """Executed during the standard core tick interval sequence.
        
        Responsibilities:
        - Determine Hero proximity bonding vectors.
        - Handle any Pending Replacement hero spawning intervals.
        """
        self._tick_proximity_familiarity(ctx, tick)
        self._tick_inn_gossip(ctx, tick)
        self._tick_hero_trading(ctx, tick)
        self._process_hero_replacements(ctx, tick)

    # -------------------------------------------------------------------------
    # Proximity Familiarity
    # -------------------------------------------------------------------------
    def _tick_proximity_familiarity(self, ctx: SystemContext, tick: int) -> None:
        """Increase mutual familiarity between heroes in close proximity.
        
        Optimized: uses spatial index for O(1) neighbor lookup.
        """
        heroes = [e for e in ctx.world.entities.values() if e.kind == "hero" and e.combat.alive]
        if len(heroes) < 2:
            return
            
        v_range = self.config.vision_range
        
        # 1. Increase for those nearby (using spatial index)
        nearby_pairs = set()
        for h1 in heroes:
            nearby = ctx.world.entities_at_radius(h1.spatial.pos, v_range)
            for h2 in nearby:
                if h1.id == h2.id or h2.kind != "hero" or not h2.combat.alive:
                    continue
                
                # Precise distance check (spatial index is just a coarse filter)
                if h1.spatial.pos.manhattan(h2.spatial.pos) > v_range:
                    continue
                
                pair = tuple(sorted((h1.id, h2.id)))
                if pair not in nearby_pairs:
                    nearby_pairs.add(pair)
                    
                    old1 = h1.identity.hero_familiarity.get(h2.id, 0.0)
                    # Pillar 7: CHA-based Familiarity (Charisma impact)
                    # Base gain 0.002, scales with CHA (1% per point)
                    # Using interaction.trade_bonus which is (1.0 + cha * 0.01)
                    gain = 0.002 * h1.interaction.trade_bonus
                    new1 = min(1.0, old1 + gain)
                    h1.identity.hero_familiarity[h2.id] = new1
                    h2.identity.hero_familiarity[h1.id] = new1 # Symmetric
                    
                    if old1 < 0.5 <= new1:
                        logger.info("Tick %d: %s and %s are now Allies!", tick, h1.identity.display_name, h2.identity.display_name)
                        if ctx.emit:
                            ctx.emit("alliance", f"{h1.identity.display_name} and {h2.identity.display_name} are now Allies",
                                       entity_ids=(h1.id, h2.id),
                                       metadata={"hero1_id": h1.id, "hero2_id": h2.id, "score": new1})
                                   
        # 2. Decay for everyone else who has a familiarity entry
        for h1 in heroes:
            for h2_id in list(h1.identity.hero_familiarity.keys()):
                pair = tuple(sorted((h1.id, h2_id)))
                if pair in nearby_pairs:
                    continue
                
                # Decay Apart: -0.0005
                h1.identity.hero_familiarity[h2_id] = max(0.0, h1.identity.hero_familiarity[h2_id] - 0.0005)
                # Symmetric decay for the other hero
                if h2_id in ctx.world.entities and ctx.world.entities[h2_id].kind == "hero":
                    ctx.world.entities[h2_id].identity.hero_familiarity[h1.id] = h1.identity.hero_familiarity[h2_id]

    def _tick_inn_gossip(self, ctx: SystemContext, tick: int) -> None:
        """Heroes at the same Inn share random entity memories."""
        at_inn = [h for h in ctx.world.entities.values() if h.kind == "hero" and h.combat.alive and h.mind.decision.ai_state == AIState.VISIT_INN]
        if len(at_inn) < 2:
            return
            
        # Group by position
        by_pos: dict[tuple[int, int], list[Any]] = {}
        for h in at_inn:
            pos = (h.spatial.pos.x, h.spatial.pos.y)
            if pos not in by_pos:
                by_pos[pos] = []
            by_pos[pos].append(h)
            
        for pos, group in by_pos.items():
            if len(group) < 2:
                continue
            
            # Gossip chance: 20% per tick
            if self.rng.next_float(Domain.AI_DECISION, group[0].id, tick) > 0.2:
                continue
                
            # Pick two random heroes
            h1 = group[self.rng.next_int(Domain.AI_DECISION, group[0].id, tick + 1, 0, len(group)-1)]
            h2 = group[self.rng.next_int(Domain.AI_DECISION, group[1].id, tick + 2, 0, len(group)-1)]
            if h1.id == h2.id:
                continue
                
            # Transfer a random memory entry
            if h1.mind.perception.entity_memory:
                mem_keys = list(h1.mind.perception.entity_memory.keys())
                mem_id = mem_keys[self.rng.next_int(Domain.AI_DECISION, h1.id, tick, 0, len(mem_keys)-1)]
                mem = h1.mind.perception.entity_memory[mem_id]
                
                # Check if h2 already knows this
                if mem_id not in h2.mind.perception.entity_memory:
                    h2.mind.perception.entity_memory[mem_id] = mem.model_copy(deep=True)
                    if ctx.emit:
                        kind = getattr(mem, 'kind', 'something')
                        ctx.emit("social", f"{h1.identity.display_name} shared rumors about {kind} with {h2.identity.display_name}",
                                   entity_ids=(h1.id, h2.id),
                                   metadata={"rumor_id": mem_id})

    def _tick_hero_trading(self, ctx: SystemContext, tick: int) -> None:
        """Heroes at the same resting place share items they don't need."""
        # Active in Visit Inn or Visit Guild
        at_rest = [h for h in ctx.world.entities.values() if h.kind == "hero" and h.combat.alive and h.mind.decision.ai_state in (AIState.VISIT_INN, AIState.VISIT_GUILD)]
        if len(at_rest) < 2:
            return
            
        from src.core.gameplay.items.item_registry import ITEM_REGISTRY, ItemTemplate
        
        def item_pwr(template: ItemTemplate) -> int:
            return (template.atk_bonus + template.def_bonus + template.matk_bonus + template.mdef_bonus + 
                    template.max_hp_bonus // 5 + int(template.crit_rate_bonus * 100) + 
                    int(template.evasion_bonus * 100))

        # Group by position
        by_pos: dict[tuple[int, int], list[Any]] = {}
        for h in at_rest:
            pos = (h.spatial.pos.x, h.spatial.pos.y)
            if pos not in by_pos:
                by_pos[pos] = []
            by_pos[pos].append(h)
            
        for pos, group in by_pos.items():
            if len(group) < 2:
                continue
            
            # Trading chance: 15% per tick
            if self.rng.next_float(Domain.AI_DECISION, group[0].id, tick) > 0.15:
                continue
                
            # Pick donor and recipient
            h1 = group[self.rng.next_int(Domain.AI_DECISION, group[0].id, tick + 3, 0, len(group)-1)]
            h2 = group[self.rng.next_int(Domain.AI_DECISION, group[1].id, tick + 4, 0, len(group)-1)]
            if h1.id == h2.id or not h1.inventory or not h2.inventory:
                continue
                
            # Donor (h1) looks for an item they don't have equipped and don't need
            # For simplicity, donor just checks all items in inventory
            for iid in list(h1.inventory.items):
                t = ITEM_REGISTRY.get(iid)
                if not t or t.item_type not in (ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY):
                    continue
                
                # h1 doesn't need it if they have better equipped
                eq_id = h1.inventory.equipped.get(t.item_type)
                if eq_id:
                    eq_t = ITEM_REGISTRY.get(eq_id)
                    if eq_t and item_pwr(t) <= item_pwr(eq_t):
                        # h1 has better, so this iid is a "spare"
                        # Check if h2 can use it
                        h2_eq_id = h2.inventory.equipped.get(t.item_type)
                        better_for_h2 = False
                        if not h2_eq_id:
                            better_for_h2 = True
                        else:
                            h2_eq_t = ITEM_REGISTRY.get(h2_eq_id)
                            if h2_eq_t and item_pwr(t) > item_pwr(h2_eq_t):
                                better_for_h2 = True
                        
                        if better_for_h2 and h2.inventory.can_add(iid):
                            # Trade!
                            h1.inventory.remove_item(iid)
                            h2.inventory.add_item(iid)
                            h2.inventory.auto_equip_best(iid, getattr(h2.progression, "hero_class", 0))
                            if ctx.emit:
                                ctx.emit("social", f"{h1.identity.display_name} gifted {t.name} to {h2.identity.display_name}",
                                           entity_ids=(h1.id, h2.id),
                                           metadata={"item_id": iid})
                            break

    # -------------------------------------------------------------------------
    # Mortality Escallation
    # -------------------------------------------------------------------------
    def process_hero_death(self, ctx: SystemContext, entity, tick: int) -> bool:
        """Handle dropping bags and tracking permadeath strikes.
        Returns False if generic handling is sufficient, True if this handler fully resolved removal.
        """
        if entity.identity.faction != Faction.HERO_GUILD or entity.spatial.home_pos is None:
            return False

        entity.identity.death_count += 1
        is_permadeath = entity.identity.death_count >= self.config.death_tier_max
        
        if is_permadeath:
            if entity.inventory:
                dropped = entity.inventory.get_all_item_ids()
                if dropped:
                    ctx.world.drop_items(entity.spatial.pos, dropped)
            
            logger.info("Tick %d: Hero %s (%s Lv%d) has DIED PERMANENTLY (deaths=%d).", 
                        tick, (entity.identity.display_name or f"#{entity.id}"), entity.kind, 
                        entity.progression.level, entity.identity.death_count)
            
            if hasattr(ctx.world, "event_bus") and ctx.world.event_bus:
                from src.core.data.events import DeathEvent
                ctx.world.event_bus.publish(DeathEvent(
                    entity_id=entity.id, killer_id=None,
                    x=entity.spatial.pos.x, y=entity.spatial.pos.y,
                    level_at_death=entity.progression.level,
                    is_permadeath=True
                ))
            
            # Monument spawning
            if entity.progression.level >= 15:
                m_id = f"monument_{entity.id}_{tick}"
                from src.core.models.enums import HeroClass
                hc = getattr(entity.progression, 'hero_class', None)
                bt = "hp"
                if hc == HeroClass.WARRIOR: bt = "hp"
                elif hc == HeroClass.MAGE: bt = "atk"
                elif hc == HeroClass.RANGER: bt = "atk"
                
                monument = Monument(m_id, entity.identity.display_name or f"#{entity.id}", 
                                    hc.name if hc else "NONE", 
                                    entity.progression.level, entity.spatial.home_pos, bt, 0.1)
                ctx.world.monuments.append(monument)

            ctx.world.remove_entity(entity.id)
            self._schedule_hero_replacement(entity, tick)
            return True

        entity.combat.hp = entity.combat.max_hp
        old_pos = entity.spatial.pos
        entity.spatial.pos = entity.spatial.home_pos
        entity.mind.decision.ai_state = AIState.RESTING_IN_TOWN
        ctx.world.spatial_index.move(entity.id, old_pos, entity.spatial.home_pos)
        entity.next_act_at = float(tick + self.config.hero_respawn_ticks)
        entity.mind.perception.entity_memory.clear()
        entity.combat.effects.clear()
        
        # Tiered drop algorithm
        if entity.inventory:
            dropped_ids = []
            dropped_ids.extend(entity.inventory.items)
            entity.inventory.items.clear()
            
            if entity.identity.death_count >= 2 and entity.inventory.accessory:
                dropped_ids.append(entity.inventory.accessory)
                entity.inventory.accessory = None
            if entity.identity.death_count >= 3 and entity.inventory.armor:
                dropped_ids.append(entity.inventory.armor)
                entity.inventory.armor = None
                
            if dropped_ids:
                ctx.world.drop_items(old_pos, dropped_ids)
                logger.info("Tick %d: Hero #%d dropped %d items on death tier %d",
                            tick, entity.id, len(dropped_ids), entity.identity.death_count)
        
        logger.info("Tick %d: Hero %s died → respawning at home %s.",
                    tick, (entity.identity.display_name or f"#{entity.id}"), entity.spatial.home_pos)
        
        if hasattr(ctx.world, "event_bus") and ctx.world.event_bus:
            from src.core.data.events import DeathEvent
            ctx.world.event_bus.publish(DeathEvent(
                entity_id=entity.id, killer_id=None,
                x=entity.spatial.pos.x, y=entity.spatial.pos.y,
                level_at_death=entity.progression.level,
                is_permadeath=False
            ))
            
        # Returning True skips standard mob death procedures.
        return True

    def _schedule_hero_replacement(self, dead_hero, tick: int) -> None:
        """Schedule a new hero to spawn after a delay to replace a permadead one."""
        spawn_tick = tick + 50
        self._pending_hero_replacements.append({
            "tick": spawn_tick,
            "generation": dead_hero.identity.generation + 1,
            "home_pos": dead_hero.spatial.home_pos,
        })
        logger.info("Tick %d: Hero replacement scheduled for tick %d (Gen %d)", 
                    tick, spawn_tick, dead_hero.identity.generation + 1)

    def _process_hero_replacements(self, ctx: SystemContext, tick: int) -> None:
        """Spawn replacements for permadead heroes after their countdown."""
        from src.core.gameplay.classes import HeroClass, HERO_STARTING_GEAR
        from src.core.entities.entity_builder import EntityBuilder
        from src.core.data.hero_names import generate_hero_name
        from src.core.models.enums import Faction, EntityRole
        
        still_pending = []
        class_choices = [HeroClass.WARRIOR, HeroClass.RANGER, HeroClass.MAGE, HeroClass.ROGUE]

        for rep in self._pending_hero_replacements:
            if tick >= rep["tick"]:
                new_eid = ctx.world.allocate_entity_id()
                h_class = class_choices[new_eid % len(class_choices)]
                gear = HERO_STARTING_GEAR.get(h_class, {})
                home_pos = rep["home_pos"]

                builder = (
                    EntityBuilder(self.rng, new_eid, tick=tick)
                    .kind("hero")
                    .at(home_pos)
                    .home(home_pos)
                    .faction(Faction.HERO_GUILD)
                    .role(EntityRole.HERO)
                )
                builder.with_traits(race_prefix="hero")
                hero_name = generate_hero_name(self.rng, new_eid, tick, builder._traits)

                hero = (
                    builder
                    .with_identity(display_name=hero_name, generation=rep["generation"])
                    .with_base_stats(hp=50, atk=10, def_=3, spd=10, luck=3,
                                     crit_rate=0.08, crit_dmg=1.8, evasion=0.03, gold=50)
                    .with_hero_class(h_class)
                    .with_race_skills("hero")
                    .with_class_skills(h_class, level=1)
                    .with_inventory(max_slots=self.config.hero_inventory_slots,
                                    max_weight=self.config.hero_inventory_weight,
                                    weapon=gear.get("weapon", "iron_sword"),
                                    armor=gear.get("armor", "leather_vest"),
                                    accessory=gear.get("accessory"))
                    .with_starting_items(["small_hp_potion"] * 3)
                    .with_home_storage()
                    .with_talents(race="hero")
                    .build()
                )
                ctx.world.add_entity(hero)
                hero.inventory.auto_equip_best(gear.get("weapon"), hero.progression.hero_class)
                hero.inventory.auto_equip_best(gear.get("armor"), hero.progression.hero_class)
                hero.inventory.auto_equip_best(gear.get("accessory"), hero.progression.hero_class)

                for b in ctx.world.buildings:
                    if b.spatial.pos == home_pos and b.building_type == "hero_house":
                        b.name = f"{hero_name}'s House"
                
                logger.info("Tick %d: New hero %s (Gen %d) has arrived!", 
                            tick, hero_name, hero.identity.generation)
                if ctx.emit:
                    ctx.emit("hero_arrival", f"Hero {hero_name} arrives (Gen {hero.identity.generation})",
                               entity_ids=(new_eid,),
                               metadata={"entity_id": new_eid, "name": hero_name, "generation": hero.identity.generation})
            else:
                still_pending.append(rep)
        self._pending_hero_replacements = still_pending
