# Compliance IDs: PROG-001, PROG-002, PROG-003, PROG-004, PROG-007, PROG-008
# src/engine/evolution.py
# Phase 8 Implementation: Handles Entity Growth Milestones and Role Transformations (LEG-RPG-143).
from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING
from src.core.state import EntityState, EquipSlot
from src.core.updates import EntityUpdate, IdentityUpdate, CombatUpdate, RewardUpdate

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState
    from src.core.updates import StateUpdate

class EvolutionSystem:
    """
    Law: Entities transform upon reaching growth milestones (LEG-RPG-143).
    Ensures that identity transformations are authoritative and auditable.
    """

    # Default threshold for evolution. In a full system, this would come from a profile.
    EVOLUTION_THRESHOLD = 1000 

    @staticmethod
    def evaluate(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Check for evolution triggers (level cap or XP thresholds) and apply transformations.
        Consolidates all XP sources and applies multipliers (e.g. Well Rested).
        """
        for e_id, ent_upd in update.entity_updates.items():
            entity = state.entities.get(e_id)
            if not entity or not entity.lifecycle.active:
                continue
            
            # 1. Consolidate XP Sources
            raw_delta = 0
            if ent_upd.identity:
                raw_delta += ent_upd.identity.evolution_points_delta
            if ent_upd.reward:
                raw_delta += ent_upd.reward.xp_gain
            
            if raw_delta == 0 and not ent_upd.identity:
                continue
                
            # 2. Apply Multipliers (Pillar 2: Biological impacts)
            xp_mult = 1.0
            if entity.biological.well_rested_until >= state.tick:
                xp_mult = 1.5
            
            total_proposed_delta = int(raw_delta * xp_mult)
            total_points = entity.identity.evolution_points + total_proposed_delta
            
            # 3. Evaluate Level Ups (PROG-001: Dynamic Thresholds)
            from src.progression.leveling import LevelingService
            levels_gained = 0
            remaining_points = total_points
            current_eval_level = entity.identity.evolution_level
            
            while current_eval_level < 100:
                req = LevelingService.get_xp_required(current_eval_level)
                if remaining_points >= req:
                    remaining_points -= req
                    levels_gained += 1
                    current_eval_level += 1
                else:
                    break
            
            # If capped, excess XP is lost? Or kept?
            # Law says cap is 100. Usually XP stays at 0 or maxed.
            if current_eval_level >= 100:
                remaining_points = min(remaining_points, 0) # Cap XP too if at level 100?
            
            # 4. Finalize Components
            id_upd = ent_upd.identity or IdentityUpdate()
            cb_upd = ent_upd.combat or CombatUpdate()
            from src.core.updates import EquipmentUpdate
            eq_upd = ent_upd.equipment or EquipmentUpdate()
            
            # Zero out Reward XP (consumed)
            new_reward = ent_upd.reward
            if ent_upd.reward and ent_upd.reward.xp_gain != 0:
                from src.core.updates import RewardUpdate
                new_reward = replace(ent_upd.reward, xp_gain=0)
            
            # Default state (no level up)
            new_kind = entity.kind
            new_level = current_eval_level
            total_ap_gain = 0
            new_slots = eq_upd.slot_updates
            
            # Level Up Logic
            if levels_gained > 0:
                old_level = entity.identity.evolution_level
                
                # Check for species evolution thresholds (EVO-001)
                evolved = False
                for threshold in [10, 25, 50]:
                    if old_level < threshold <= new_level:
                        evolved = True
                        break
                
                new_kind = EvolutionSystem._get_evolved_kind(entity.kind) if evolved else entity.kind
                
                # Stat & Gear Growth
                if evolved:
                    new_slots = dict(eq_upd.slot_updates)
                    if "goblin" in new_kind.lower():
                        if "1" in new_kind:
                            new_slots[EquipSlot.MAIN_HAND] = "iron_sword"
                            new_slots[EquipSlot.TORSO] = "leather_armor"
                        elif "2" in new_kind:
                            new_slots[EquipSlot.MAIN_HAND] = "steel_sword"
                            new_slots[EquipSlot.TORSO] = "chainmail"
                
                from src.core.enums import EntityRole
                if entity.identity.role == EntityRole.HERO:
                    total_ap_gain = levels_gained * 5
                    skills_to_learn = []
                    
                    for lvl in range(old_level + 1, new_level + 1):
                        if lvl % 5 == 0:
                            total_ap_gain += 5
                        skills_to_learn.extend(LevelingService.get_unlocked_skills(lvl))
                    
                    id_upd = replace(id_upd, 
                        unspent_ap_delta=id_upd.unspent_ap_delta + total_ap_gain,
                        learned_skills=list(set(id_upd.learned_skills + skills_to_learn))
                    )
                else:
                    from src.core.updates import AttributeUpdate
                    attr_upd = ent_upd.attributes or AttributeUpdate()
                    ent_upd = replace(ent_upd, attributes=replace(attr_upd,
                        vitality_delta=attr_upd.vitality_delta + int(5 * entity.aptitude.vit_apt * levels_gained),
                        strength_delta=attr_upd.strength_delta + int(5 * entity.aptitude.str_apt * levels_gained),
                        endurance_delta=attr_upd.endurance_delta + int(2 * entity.aptitude.end_apt * levels_gained)
                    ))
                
                cb_upd = replace(cb_upd, hp_delta=cb_upd.hp_delta + (20 * levels_gained))

            update.entity_updates[e_id] = replace(
                ent_upd,
                kind_set=new_kind,
                identity=replace(id_upd, 
                    evolution_level_set=new_level,
                    evolution_points_delta=remaining_points - entity.identity.evolution_points
                ),
                reward=new_reward,
                equipment=replace(eq_upd, slot_updates=new_slots) if new_slots != eq_upd.slot_updates else ent_upd.equipment,
                combat=cb_upd,
                property_updates={
                    **ent_upd.property_updates,
                    "evolved_this_tick": levels_gained > 0, 
                    "levels_gained": levels_gained,
                    "previous_kind": entity.kind
                }
            )
        
        return update

    @staticmethod
    def _get_evolved_kind(kind: str) -> str:
        """Determines the next semantic stage for an entity kind."""
        mapping = {
            "GOBLIN": "GOBLIN_WARRIOR",
            "GOBLIN_WARRIOR": "ORC_SCOUT",
            "WOLF": "DIRE_WOLF",
            "HERO": "LEGEND_HERO"
        }
        if "_" in kind:
            parts = kind.rsplit("_", 1)
            if parts[1].isdigit():
                return f"{parts[0]}_{int(parts[1]) + 1}"
        return mapping.get(kind.upper(), kind + "_EVOLVED")
