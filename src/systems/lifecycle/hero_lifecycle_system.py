"""Hero Lifecycle System — Manages hero specific progression events like familiarity and permadeath."""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from src.core.entities.entity import Entity
from src.systems.infrastructure.base import System, SystemContext
from src.core.models.world_state import WorldState
from src.core.models.enums import AIState, ItemType, Domain
from src.core.gameplay.faction import Faction
from src.core.world.monuments import Monument
from src.core.models.history import HistoricalEvent, EventKind # [PHASE 4]
from src.core.models.continuity import SuccessorRecord # [PHASE 4]
from src.core.models.strategy import DirectiveKind # [PHASE 1 STAGE 13]

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
                    
                    # Authoritative bond lookup from registry
                    bond = ctx.world.social_registry.get_bond(h1.id, h2.id)
                    old_score = bond.familiarity

                    # Pillar 7: CHA-based Familiarity (Charisma impact)
                    # Base gain 0.002, scales with CHA (1% per point)
                    gain = 0.002 * h1.interaction.trade_bonus
                    
                    # Update both directions for symmetry
                    ctx.world.social_registry.update_bond(h1.id, h2.id, familiarity_delta=gain, tick=tick)
                    ctx.world.social_registry.update_bond(h2.id, h1.id, familiarity_delta=gain, tick=tick)
                    
                    new_score = ctx.world.social_registry.get_bond(h1.id, h2.id).familiarity
                    
                    if old_score < 0.5 <= new_score:
                        logger.info("Tick %d: %s and %s are now Allies!", tick, h1.identity.display_name, h2.identity.display_name)
                        if ctx.emit:
                            ctx.emit("alliance", f"{h1.identity.display_name} and {h2.identity.display_name} are now Allies",
                                       entity_ids=(h1.id, h2.id),
                                       metadata={"hero1_id": h1.id, "hero2_id": h2.id, "score": new_score})
                                   
        # 2. Decay for everyone else who has a familiarity entry
        # Note: In the authoritative registry, we only decay bonds that exist and are > 0
        all_bonds = list(ctx.world.social_registry.bonds.items())
        for key, bond in all_bonds:
            if bond.familiarity <= 0:
                continue
            
            # Key format: f"{source_id}:{target_id}"
            src_id, tgt_id = map(int, key.split(":"))
            
            # Check if source is one of our active heroes
            hero_ids = [h.id for h in heroes]
            if src_id not in hero_ids:
                continue
                
            pair = tuple(sorted((src_id, tgt_id)))
            if pair in nearby_pairs:
                continue
            
            # Decay Apart: -0.0005
            ctx.world.social_registry.update_bond(src_id, tgt_id, familiarity_delta=-0.0005, tick=tick)

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
            # Phase 4: History and Succession
            event_id = f"death_{entity.id}_{tick}"
            death_event = HistoricalEvent(
                event_id=event_id,
                tick=tick,
                kind=EventKind.DEATH,
                location=entity.spatial.pos,
                description=f"Hero {entity.identity.display_name} has fallen permanently.",
                involved_ids={entity.id},
                summary=f"The legend of {entity.identity.display_name} ends at tick {tick}."
            )
            ctx.world.world_history.add_event(death_event)
            
            # Find/Ensure Household
            h_id = entity.identity.household_id
            if not h_id and entity.spatial.home_pos:
                # Try to find by home_pos
                h_id = f"house_{entity.spatial.home_pos.x}_{entity.spatial.home_pos.y}"
                entity.identity.household_id = h_id
            
            household = None
            if h_id:
                if h_id not in ctx.world.household_registry:
                    # Create household record on the fly if missing (migration/first-death case)
                    from src.core.models.households import HouseholdRecord
                    ctx.world.household_registry[h_id] = HouseholdRecord(
                        household_id=h_id,
                        home_building_id=0 # TODO: find building ID if needed
                    )
                household = ctx.world.household_registry[h_id]
                household.former_member_ids.append(entity.id)
                household.related_event_ids.append(event_id)
            
            # Create Successor Record
            legacy_directives = [
                d.model_dump() for d in entity.mind.strategic.directives 
                if d.kind in (DirectiveKind.PERSONAL, DirectiveKind.FACTIONAL)
            ]
            successor_rec = SuccessorRecord(
                source_entity_id=entity.id,
                household_id=h_id,
                death_event_id=event_id,
                tick=tick,
                motive_fragments={
                    "legacy_level": entity.progression.level,
                    "predecessor_name": entity.identity.display_name,
                    "directives": legacy_directives # [PHASE 1 STAGE 13]
                }
            )
            ctx.world.successor_registry[entity.id] = successor_rec
            
            # Heirloom Transfer
            if entity.inventory and household:
                # Rule: Weapon, Armor, and RARE items are Heirlooms
                heirlooms = []
                remaining = []
                from src.core.gameplay.items.item_registry import ITEM_REGISTRY, Rarity
                
                # Check equipped
                for slot in ["weapon", "armor"]:
                    iid = getattr(entity.inventory, slot)
                    if iid:
                        heirlooms.append(iid)
                        setattr(entity.inventory, slot, None)
                
                # Check bag
                for iid in list(entity.inventory.items):
                    t = ITEM_REGISTRY.get(iid)
                    if t and (t.rarity >= Rarity.RARE):
                        heirlooms.append(iid)
                        entity.inventory.items.remove(iid)
                    else:
                        remaining.append(iid)
                
                if heirlooms:
                    household.heirloom_ids.extend(heirlooms)
                    logger.info("Tick %d: %d heirlooms transferred to Household %s", 
                                tick, len(heirlooms), h_id)
                
                # Wealth Transfer [PHASE 1 STAGE 13]
                gold = getattr(entity.progression, "gold", 0)
                if gold > 0:
                    legacy_contribution = int(gold * 0.5) # 50% goes to the family
                    household.legacy_gold += legacy_contribution
                    entity.progression.gold -= legacy_contribution
                    logger.info("Tick %d: %d gold moved to Household %s legacy fund.", 
                                tick, legacy_contribution, h_id)
                
                if remaining:
                    ctx.world.drop_items(entity.spatial.pos, remaining)

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

    def _schedule_hero_replacement(self, dead_hero: Entity, tick: int) -> None:
        """Schedule a new hero to spawn after a delay to replace a permadead one."""
        spawn_tick = tick + self.config.hero_respawn_ticks
        self._pending_hero_replacements.append({
            "tick": spawn_tick,
            "generation": dead_hero.identity.generation + 1,
            "home_pos": dead_hero.spatial.home_pos,
            "predecessor_id": dead_hero.id,
            "household_id": dead_hero.identity.household_id,
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

                # Phase 4: Consumption of Succession Record
                household_id = rep.get("household_id")
                motive_frags = {}
                predecessor_id = rep.get("predecessor_id")
                
                if predecessor_id and predecessor_id in ctx.world.successor_registry:
                    rec = ctx.world.successor_registry[predecessor_id]
                    household_id = rec.household_id
                    motive_frags = rec.motive_fragments
                    # Cleanup record
                    del ctx.world.successor_registry[predecessor_id]

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
                
                # Apply inherited data
                hero.identity.household_id = household_id
                if motive_frags:
                    # Transfer motives (Pillar 1)
                    hero.identity.titles.append(f"Heir of {motive_frags.get('predecessor_name')}")
                
                # Assign to household member list
                if household_id and household_id in ctx.world.household_registry:
                    ctx.world.household_registry[household_id].member_ids.add(new_eid)
                    
                    # Apply Inherited Directives [PHASE 1 STAGE 13]
                    inherited_directives = motive_frags.get("directives", [])
                    if inherited_directives:
                        from src.core.models.strategy import DirectiveRecord
                        for d_dict in inherited_directives:
                            # Soften/Prefix legacy directives
                            d_dict["label"] = f"Legacy: {d_dict['label']}"
                            hero.mind.strategic.directives.append(DirectiveRecord.model_validate(d_dict))

                    # Inherit heirlooms
                    heirlooms = ctx.world.household_registry[household_id].heirloom_ids
                    if heirlooms:
                        for iid in list(heirlooms):
                            hero.inventory.add_item(iid)
                            hero.inventory.auto_equip_best(iid, getattr(hero.progression, "hero_class", 0))
                        # Note: heirlooms remain in the 'registry' as historical markers but 
                        # are removed from active household storage once claimed by the heir.
                        ctx.world.household_registry[household_id].heirloom_ids = []

                    # Starting Stipend from Legacy Wealth [PHASE 1 STAGE 13]
                    household = ctx.world.household_registry[household_id]
                    if household.legacy_gold > 100:
                        stipend = int(household.legacy_gold * 0.1) # 10% of family wealth
                        household.legacy_gold -= stipend
                        hero.progression.gold += stipend
                        logger.info("Tick %d: Successor %d received %d gold legacy stipend.", 
                                    tick, new_eid, stipend)

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
