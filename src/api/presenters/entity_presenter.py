from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from src.core.entities.entity import Entity
    from src.api.schemas import (
        EntitySlimSchema, EntitySchema, EntityInspectionSchema, 
        CombatTraceSchema, AIDecisionSchema, StatBreakdownSchema,
        SuccessorSummarySchema, HouseholdSummarySchema
    )

# Order must match legacy encoder/frontend expectations for the binary protocol
ENTITY_KEY_MAP = ["id", "x", "y", "hp", "state_id", "target_id", "loot_progress"]

STATE_ENUM_MAP = {
    "IDLE": 0, "MOVE": 1, "COMBAT": 2, "LOOT": 3, "HARVEST": 4,
    "CRAFT": 5, "REST": 6, "DEAD": 7, "FLEE": 8, "WANDER": 9
}

class EntityPresenter:
    """Separation of concerns: Domain models should not know about API schemas."""

    @staticmethod
    def to_inspection_schema(entity: "Entity", loot_duration: int = 3, registry: Any = None, world: Any = None) -> "EntityInspectionSchema":
        from src.api.schemas import (
            EntityInspectionSchema, CombatTraceSchema, MemoryLogSchema,
            SuccessorSummarySchema, HouseholdSummarySchema
        )
        from src.api.presenters.stat_breakdown import StatBreakdownService
        from src.api.presenters.ai_presenter import AIPresenter
        
        # 1. Full Entity Data (including routine)
        full = EntityPresenter.to_full_schema(entity, loot_duration, registry, world)
        
        # 2. Stat Breakdowns
        breakdowns = StatBreakdownService.get_all_breakdowns(entity)
        
        # 3. Combat History (from Aspect Traces)
        history = [
            CombatTraceSchema(
                tick=t.get("tick", 0),
                attacker_id=t.get("attacker_id", 0),
                defender_id=t.get("defender_id", 0),
                skill_used=t.get("skill_used", "attack"),
                raw_damage=t.get("raw_damage", 0),
                mitigation=t.get("mitigation", 0),
                elemental_mult=t.get("elemental_mult", 1.0) if isinstance(t, dict) else getattr(t, "elemental_mult", 1.0),
                is_crit=t.get("is_crit", False) if isinstance(t, dict) else getattr(t, "is_crit", False),
                is_evasion=t.get("is_evasion", False) if isinstance(t, dict) else getattr(t, "is_evasion", False),
                trauma=t.get("trauma", 0.0) if isinstance(t, dict) else getattr(t, "trauma", 0.0),
                threat=t.get("threat", 0.0) if isinstance(t, dict) else getattr(t, "threat", 0.0),
                explanation=f"Damage: {t.get('damage', 0) if isinstance(t, dict) else getattr(t, 'damage', 0)}"
            )
            for t in entity.combat.traces
        ]
        
        # 4. Narrative History (Phase 2 & 3 Integration)
        narrative = [
            MemoryLogSchema(
                tick=log.tick,
                type=log.type,
                impact=log.impact,
                message=EntityPresenter._generate_narrative_message(log, world),
                details=log.details if isinstance(log.details, dict) else log.details.model_dump() if hasattr(log.details, "model_dump") else {}
            )
            for log in entity.mind.narrative.memory_log
        ]
        
        # 5. AI Explanation
        ai_exp = AIPresenter.get_explanation(entity)
        
        # 6. Continuity & Inheritance [PHASE 4]
        successor_sum = None
        household_sum = None
        
        if world:
            # Successor records are keyed by PREDECESSOR ID
            # If this entity is an heir, we find the record where it is the successor
            rec = world.successor_registry.get(entity.id)
            if not rec:
                # Check if this entity was the target successor of another record
                for r in world.successor_registry.values():
                    if r.successor_entity_id == entity.id:
                        rec = r
                        break
            
            if rec:
                successor_sum = SuccessorSummarySchema(
                    source_entity_id=rec.source_entity_id,
                    predecessor_name=rec.motive_fragments.get("predecessor_name", "Unknown Legend"),
                    legacy_level=rec.motive_fragments.get("legacy_level", 1),
                    inherited_motive_count=len(rec.motive_fragments),
                    tick=rec.tick
                )
            
            # Household lookup
            h_id = entity.identity.household_id
            if h_id and h_id in world.household_registry:
                h_rec = world.household_registry[h_id]
                household_sum = HouseholdSummarySchema(
                    household_id=h_id,
                    reputation=h_rec.reputation,
                    member_count=len(h_rec.member_ids),
                    former_member_count=len(h_rec.former_member_ids),
                    heirloom_count=len(h_rec.heirloom_ids),
                    legacy_tags=h_rec.legacy_tags
                )

        return EntityInspectionSchema(
            entity=full,
            routine=full.routine,
            reputation=full.reputation,
            stat_breakdowns=breakdowns,
            combat_history=history,
            ai_explanation=ai_exp,
            narrative_history=narrative,
            turning_points=full.turning_points,
            successor_record=successor_sum,
            household_record=household_sum
        )

    @staticmethod
    def to_slim_schema(entity: "Entity", loot_duration: int = 3) -> "EntitySlimSchema":
        from src.api.schemas import EntitySlimSchema
        
        # Accessing nested aspects directly (the new way)
        identity = entity.identity
        spatial = entity.spatial
        combat = entity.combat
        mind = entity.mind
        progression = entity.progression
        
        return EntitySlimSchema(
            id=entity.id,
            kind=entity.kind,
            display_name=identity.display_name,
            x=spatial.pos.x,
            y=spatial.pos.y,
            hp=combat.hp,
            max_hp=combat.max_hp,
            state=mind.decision.ai_state.name.lower(), # Using the new DecisionState sub-model
            level=progression.level,
            tier=identity.tier,
            faction=identity.faction.name.lower() if hasattr(identity.faction, "name") else str(identity.faction).lower(),
            weapon_range=EntityPresenter._get_weapon_range(entity),
            combat_target_id=combat.combat_target_id,
            loot_progress=entity.interaction.loot_progress,
            loot_duration=loot_duration,
        )

    @staticmethod
    def to_compact_list(entity: "Entity") -> list[Any]:
        """
        Ordered list for high-performance WebSocket streaming.
        Order matches ENTITY_KEY_MAP above.
        """
        state_name = entity.mind.decision.ai_state.name.upper()
        state_id = STATE_ENUM_MAP.get(state_name, 0)
        
        return [
            entity.id,
            int(entity.spatial.pos.x),
            int(entity.spatial.pos.y),
            entity.combat.hp,
            state_id,
            entity.combat.combat_target_id,
            entity.interaction.loot_progress
        ]

    @staticmethod
    def to_full_schema(entity: "Entity", loot_duration: int = 3, registry: Any = None, world: Any = None) -> "EntitySchema":
        from src.api.schemas import (
            EntitySchema, EffectSchema, QuestSchema, RoutineStateSchema,
            SocialBondSchema, ReputationProfileSchema, TurningPointSchema, MemoryLogSchema,
            BeliefRecordSchema, ThreatEstimateSchema, PersonalityProfileSchema, PersonalMotiveSchema,
            SuccessorSummarySchema, HouseholdSummarySchema
        )
        from src.core.models.enums import Element, LifeRole
        from src.api.schemas import PlaceAttachmentSchema

        identity = entity.identity
        spatial = entity.spatial
        combat = entity.combat
        mind = entity.mind
        progression = entity.progression
        inventory = entity.inventory
        interaction = entity.interaction
        
        elem = EntityPresenter._elem_dmg(entity)
        
        return EntitySchema(
            id=entity.id,
            kind=entity.kind,
            display_name=identity.display_name,
            x=spatial.pos.x,
            y=spatial.pos.y,
            hp=combat.hp,
            max_hp=combat.max_hp,
            atk=combat.atk,
            def_=combat.def_,
            spd=combat.spd,
            luck=combat.luck,
            crit_rate=combat.crit_rate,
            evasion=combat.evasion,
            matk=combat.matk,
            mdef=combat.mdef,
            level=progression.level,
            xp=progression.xp,
            xp_to_next=progression.xp_to_next,
            gold=progression.gold,
            tier=identity.tier,
            faction=identity.faction.name.lower() if hasattr(identity.faction, "name") else str(identity.faction).lower(),
            state=mind.decision.ai_state.name.lower(),
            weapon=inventory.weapon if inventory else None,
            armor=inventory.armor if inventory else None,
            accessory=inventory.accessory if inventory else None,
            inventory_count=inventory.used_slots if inventory else 0,
            inventory_max_slots=inventory.max_slots if inventory else 0,
            inventory_items=list(inventory.items) if inventory else [],
            inventory_weight=round(inventory.current_weight, 1) if inventory else 0.0,
            inventory_max_weight=inventory.max_weight if inventory else 0.0,
            vision_range=entity.spatial.vision_range,
            terrain_memory={f"{k[0]},{k[1]}": v for k, v in mind.perception.terrain_memory.items()}, # Using PerceptionMemory sub-model
            entity_memory=[
                BeliefRecordSchema(
                    entity_id=eid,
                    pos=(belief.pos.x, belief.pos.y),
                    last_seen_tick=belief.last_seen_tick,
                    stale_ticks=belief.stale_ticks,
                    confidence=belief.confidence,
                    apparent_faction=belief.apparent_faction,
                    apparent_role=belief.apparent_role,
                    apparent_class=belief.apparent_class,
                    visible_weapon=belief.visible_weapon,
                    visible_injury=belief.visible_injury,
                    threat=ThreatEstimateSchema(
                        overall=belief.threat.overall,
                        melee_threat=belief.threat.melee_threat,
                        ranged_threat=belief.threat.ranged_threat,
                        survivability=belief.threat.survivability,
                        confidence=belief.threat.confidence
                    )
                )
                for eid, belief in mind.perception.entity_memory.items()
            ],
            personality=PersonalityProfileSchema.model_validate(mind.decision.personality.model_dump()) if mind.decision.personality else None,
            motives=[
                PersonalMotiveSchema.model_validate(m.model_dump())
                for m in mind.decision.motives
            ],
            motive_utility_biases={g.name.lower(): v for g, v in mind.decision.motive_utility_biases.items()},
            decision_drivers=list(mind.decision.decision_drivers) if mind.decision.decision_drivers else [],
            goals=list(mind.decision.goals),
            loot_progress=entity.interaction.loot_progress,
            loot_duration=loot_duration,
            known_recipes=list(identity.known_recipes),
            craft_target=identity.craft_target,
            stamina=progression.stamina,
            max_stamina=progression.max_stamina,
            attributes=EntityPresenter._serialize_attrs(entity),
            attribute_caps=EntityPresenter._serialize_caps(entity),
            hero_class=EntityPresenter._serialize_hero_class(entity),
            skills=[EntityPresenter._serialize_skill(s) for s in progression.skills],
            class_mastery=progression.class_mastery,
            active_effects=[
                EffectSchema(
                    effect_type=eff.effect_type.name.lower() if hasattr(eff.effect_type, "name") else str(eff.effect_type).lower(),
                    source=eff.source,
                    remaining_ticks=eff.remaining_ticks,
                    atk_mult=eff.atk_mult,
                    def_mult=eff.def_mult,
                    spd_mult=eff.spd_mult,
                    crit_mult=eff.crit_mult,
                    evasion_mult=eff.evasion_mult,
                    hp_per_tick=eff.hp_per_tick,
                )
                for eff in combat.effects
                if not eff.expired
            ],
            base_atk=combat.atk,
            base_def=combat.def_,
            base_spd=combat.spd,
            base_matk=combat.matk,
            base_mdef=combat.mdef,
            base_crit_rate=combat.crit_rate,
            base_evasion=combat.evasion,
            hp_regen=combat.hp_regen,
            cooldown_reduction=combat.cooldown_reduction,
            loot_bonus=interaction.loot_bonus,
            trade_bonus=interaction.trade_bonus,
            interaction_speed=interaction.interaction_speed,
            rest_efficiency=interaction.rest_efficiency,
            speed_delay_move=round(1.0 * (10.0 / combat.spd), 2) if combat.spd > 0 else 5.0,
            speed_delay_attack=round(0.9 * (10.0 / combat.spd), 2) if combat.spd > 0 else 5.0,
            speed_delay_skill=round(1.2 * (10.0 / combat.spd), 2) if combat.spd > 0 else 5.0,
            speed_delay_harvest=round(0.7 * (10.0 / combat.spd), 2) if combat.spd > 0 else 5.0,
            fire_dmg_mult=elem.fire_dmg_mult,
            ice_dmg_mult=elem.ice_dmg_mult,
            lightning_dmg_mult=elem.lightning_dmg_mult,
            dark_dmg_mult=elem.dark_dmg_mult,
            elem_vuln_fire=combat.elemental_vulnerability(Element.FIRE),
            elem_vuln_ice=combat.elemental_vulnerability(Element.ICE),
            elem_vuln_lightning=combat.elemental_vulnerability(Element.LIGHTNING),
            elem_vuln_dark=combat.elemental_vulnerability(Element.DARK),
            region_id=spatial.region_id,
            difficulty_tier=spatial.difficulty_tier,
            current_region_id=spatial.current_region_id,
            weapon_range=EntityPresenter._get_weapon_range(entity),
            combat_target_id=combat.combat_target_id,
            traits=list(identity.traits),
            generation=identity.generation, # [PHASE 4]
            household_id=identity.household_id, # [PHASE 4]
            world_role=LifeRole(identity.world_role).name.lower() if hasattr(LifeRole(identity.world_role), "name") else str(identity.world_role).lower(),
            cluster_id=identity.cluster_id,
            group_id=identity.group_id,
            place_attachments=[
                PlaceAttachmentSchema(
                    place_id=pa.building_id if pa.building_id else None,
                    place_type=pa.kind.name.lower() if hasattr(pa.kind, "name") else str(pa.kind).lower(),
                    x=int(pa.location_pos.x),
                    y=int(pa.location_pos.y),
                    importance=round(pa.importance, 2),
                    attachment_kind=pa.kind.name.lower() if hasattr(pa.kind, "name") else str(pa.kind).lower()
                )
                for pa in mind.place_attachments
            ],
            home_storage_used=inventory.home_storage.used_slots if inventory and inventory.home_storage else 0,
            home_storage_max=inventory.home_storage.max_slots if inventory and inventory.home_storage else 0,
            home_storage_level=inventory.home_storage.level if inventory and inventory.home_storage else 0,
            quests=[
                QuestSchema(
                    quest_id=q.quest_id,
                    quest_type=q.quest_type.name.lower() if hasattr(q.quest_type, "name") else str(q.quest_type).lower(),
                    title=q.title,
                    description=q.description,
                    target_kind=q.target_kind,
                    target_x=q.target_pos.x if q.target_pos else None,
                    target_y=q.target_pos.y if q.target_pos else None,
                    target_count=q.target_count,
                    progress=q.progress,
                    completed=q.completed,
                    gold_reward=q.gold_reward,
                    xp_reward=q.xp_reward,
                )
                for q in progression.quests
            ],
            routine=RoutineStateSchema(
                sleep_debt=mind.routine.sleep_debt,
                hunger_level=mind.routine.hunger_level,
                is_sleeping=mind.routine.is_sleeping,
                active_hours=f"{mind.routine.active_start_hour:02d}:00 - {mind.routine.active_end_hour:02d}:00"
            ),
            reputation=ReputationProfileSchema(
                heroism=identity.reputation.heroism_score,
                cowardice=identity.reputation.cowardice_score,
                threat_notoriety=identity.reputation.threat_notoriety,
                trustworthiness=identity.reputation.trustworthiness,
                tags=identity.reputation.reputation_tags
            ),
            turning_points=[
                TurningPointSchema(
                    kind=tp.kind.name.lower() if hasattr(tp.kind, "name") else str(tp.kind).lower(),
                    tick=tp.tick,
                    impact=tp.emotional_impact,
                    summary=tp.summary_tag or f"Moment of {tp.kind.name.lower()}",
                    involved_names=[str(eid) for eid in tp.involved_entity_ids]
                )
                for tp in mind.narrative.turning_points
            ],
            memory_log=[
                MemoryLogSchema(
                    tick=log.tick,
                    type=log.type,
                    impact=log.impact,
                    message=EntityPresenter._generate_narrative_message(log, world),
                    details=log.details if isinstance(log.details, dict) else log.details.model_dump() if hasattr(log.details, "model_dump") else {}
                )
                for log in mind.narrative.memory_log
            ],
            social_bonds=EntityPresenter._serialize_social_bonds(entity, registry, world) if registry else []
        )

    @staticmethod
    def _serialize_skill(instance: "SkillInstance") -> "SkillSchema":
        from src.api.schemas import SkillSchema
        from src.core.gameplay.classes import SKILL_DEFS, _MAGICAL_SKILLS, _SKILL_ELEMENTS
        from src.core.models.enums import Element
        
        sdef = SKILL_DEFS.get(instance.skill_id)
        if sdef and hasattr(sdef, "damage_type") and sdef.damage_type is not None:
             dmg_type = "magical" if sdef.damage_type == 1 else "physical"
             element_name = sdef.element.name.lower() if hasattr(sdef, "element") else "none"
        else:
            dmg_type = "magical" if instance.skill_id in _MAGICAL_SKILLS else "physical"
            element_enum = _SKILL_ELEMENTS.get(instance.skill_id, Element.NONE)
            element_name = element_enum.name.lower()
        
        return SkillSchema(
            skill_id=instance.skill_id,
            name=sdef.name if sdef else instance.skill_id,
            cooldown_remaining=instance.cooldown_remaining,
            mastery=instance.mastery,
            times_used=instance.times_used,
            skill_type=sdef.skill_type.name.lower() if sdef else "active",
            target=sdef.target.name.lower() if sdef else "self",
            stamina_cost=instance.effective_stamina_cost(sdef.stamina_cost) if sdef else 0,
            cooldown=instance.effective_cooldown(sdef.cooldown) if sdef else 0,
            power=instance.effective_power(sdef.power) if sdef else 1.0,
            description=sdef.description if sdef else "",
            damage_type=dmg_type,
            element=element_name,
        )

    @staticmethod
    def _get_weapon_range(entity: "Entity") -> int:
        if not entity.inventory or not entity.inventory.weapon:
            return 1
        from src.core.gameplay.items.item_registry import ITEM_REGISTRY
        w = ITEM_REGISTRY.get(entity.inventory.weapon)
        return getattr(w, "range", 1) if w else 1

    @staticmethod
    def _elem_dmg(entity: "Entity"):
        from src.core.models.enums import TraitType
        fire = 1.0; ice = 1.0; lightning = 1.0; dark = 1.0
        traits = entity.identity.traits
        if TraitType.ELEMENTALIST in traits:
            fire += 0.2; ice += 0.2; lightning += 0.2
        if TraitType.ARCANE_GIFTED in traits:
            dark += 0.2
        if TraitType.SPIRIT_TOUCHED in traits:
            fire += 0.1; ice += 0.1; lightning += 0.1; dark += 0.1

        class ElemDmg:
            def __init__(self, f, i, l, d):
                self.fire_dmg_mult = f
                self.ice_dmg_mult = i
                self.lightning_dmg_mult = l
                self.dark_dmg_mult = d
        return ElemDmg(fire, ice, lightning, dark)

    @staticmethod
    def _serialize_attrs(entity: "Entity"):
        if not entity.progression or not entity.progression.attributes:
            return None
        from src.api.schemas import AttributeSchema
        a = entity.progression.attributes
        return AttributeSchema(
            str=a.str_, agi=a.agi, vit=a.vit, int=a.int_,
            spi=a.spi, wis=a.wis, end=a.end, per=a.per, cha=a.cha,
            str_frac=a._str_frac, agi_frac=a._agi_frac, vit_frac=a._vit_frac,
            int_frac=a._int_frac, spi_frac=a._spi_frac, wis_frac=a._wis_frac,
            end_frac=a._end_frac, per_frac=a._per_frac, cha_frac=a._cha_frac
        )

    @staticmethod
    def _serialize_caps(entity: "Entity"):
        if not entity.progression or not entity.progression.attribute_caps:
            return None
        from src.api.schemas import AttributeCapSchema
        c = entity.progression.attribute_caps
        return AttributeCapSchema(
            str_cap=c.str_cap, agi_cap=c.agi_cap, vit_cap=c.vit_cap,
            int_cap=c.int_cap, spi_cap=c.spi_cap, wis_cap=c.wis_cap,
            end_cap=c.end_cap, per_cap=c.per_cap, cha_cap=c.cha_cap
        )

    @staticmethod
    def _serialize_hero_class(entity: "Entity") -> str:
        from src.core.models.enums import HeroClass
        try:
            return HeroClass(entity.progression.hero_class).name.lower()
        except (ValueError, TypeError, AttributeError):
            return "none"

    @staticmethod
    def _serialize_social_bonds(entity: "Entity", registry: Any, world: Any = None) -> list["SocialBondSchema"]:
        from src.api.schemas import SocialBondSchema
        bonds = []
        name_map = {}
        if world:
            name_map = {e.id: e.identity.display_name for e in world.entities.values()}
            
        for key, bond in registry.bonds.items():
            if bond.source_id == entity.id:
                target_name = name_map.get(bond.target_id, f"Entity {bond.target_id}")
                
                # Derive narrative summary from memory logs if available
                narrative = None
                if entity.mind.narrative.memory_log:
                    # Find the most recent social event involving this target
                    recent_events = [
                        log for log in entity.mind.narrative.memory_log
                        if log.type == "social" and log.details.get("target_id") == bond.target_id
                    ]
                    if recent_events:
                        last_event = recent_events[-1]
                        narrative = EntityPresenter._generate_narrative_message(last_event, world)
                
                bonds.append(SocialBondSchema(
                    target_id=bond.target_id,
                    target_name=target_name,
                    trust=bond.trust,
                    fear=bond.fear,
                    rivalry=bond.rivalry,
                    familiarity=bond.familiarity,
                    loyalty=bond.loyalty,
                    resentment=bond.resentment,
                    admiration=bond.admiration,
                    debt=bond.debt,
                    narrative_summary=narrative
                ))
        return sorted(bonds, key=lambda b: (abs(b.trust) + abs(b.fear) + abs(b.rivalry)), reverse=True)

    @staticmethod
    def _generate_narrative_message(log: Any, world: Any = None) -> str:
        """Generates a human-readable summary of a memory log event."""
        log_type = log.type.lower()
        details = log.details
        
        name_map = {}
        if world:
            name_map = {e.id: e.identity.display_name for e in world.entities.values()}
            
        target_id = details.get("target_id")
        target_name = name_map.get(target_id, f"entity {target_id}") if target_id else "unknown"
        
        if log_type == "combat":
            skill = details.get("skill", "attack")
            dmg = details.get("damage", 0)
            if details.get("is_attacker"):
                 return f"Attacked {target_name} with {skill} for {dmg} damage."
            return f"Attacked by {target_name} with {skill} for {dmg} damage."
            
        if log_type == "social":
            event_kind = details.get("event_kind", "interaction")
            return f"Experienced {event_kind} involving {target_name}."
            
        if log_type == "turning_point":
            kind = details.get("kind", "milestone")
            summary = details.get("summary_tag", f"a major {kind}")
            return f"Reached a turning point: {summary}."

        return f"{log.type.title()} event detected."
