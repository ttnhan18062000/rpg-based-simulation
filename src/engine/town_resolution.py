from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Set, Tuple
from dataclasses import replace

from src.core.updates import EntityUpdate, InventoryUpdate, IdentityUpdate, CombatUpdate, BiologicalUpdate

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState
    from src.core.updates import StateUpdate


class TownResolutionSystem:
    """
    Authoritative handler for town territory resolution.
    """

    @staticmethod
    def resolve(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Detect entities in town and apply general passive laws (Healing).
        """
        refined_entity_updates = dict(update.entity_updates)
        
        # Town Configuration Constants (Parity with config.py)
        PASSIVE_HEAL_AMT = 1 # town_passive_heal
        
        for e_id, entity in state.entities.items():
            pos = entity.position
            ent_upd = refined_entity_updates.get(e_id)
            if ent_upd and ent_upd.new_position:
                pos = ent_upd.new_position
            
            tile_pos = (int(pos[0]), int(pos[1]))
            building_type = state.building_tiles.get(tile_pos)
            
            # 1. Passive Healing Law (Always active in town)
            if tile_pos in state.town_tiles:
                current_hp = entity.combat.hp
                max_hp = entity.combat.max_hp
                
                if current_hp < max_hp:
                    existing_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                    combat_upd = existing_upd.combat or CombatUpdate()
                    new_combat_upd = replace(combat_upd, hp_delta=combat_upd.hp_delta + PASSIVE_HEAL_AMT)
                    
                    refined_entity_updates[e_id] = replace(
                        existing_upd,
                        combat=new_combat_upd
                    )

            # 2. Explicit REST Intent (Only in INN/HOME)
            if building_type in ("inn", "home"):
                ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                if ent_upd.task and ent_upd.task.work_kind_set == "ENTITY_ACT" and ent_upd.task.payload_set.get("action") == "REST":
                    # REST gives 5x passive heal and restores readiness
                    REST_HEAL_BONUS = 5
                    REST_SLEEP_RECOVERY = -5.0
                    
                    combat_upd = ent_upd.combat or CombatUpdate()
                    new_combat_upd = replace(combat_upd, hp_delta=combat_upd.hp_delta + REST_HEAL_BONUS)
                    
                    biological_upd = ent_upd.biological or BiologicalUpdate()
                    new_bio_upd = replace(biological_upd, sleep_debt_delta=biological_upd.sleep_debt_delta + REST_SLEEP_RECOVERY)
                    
                    refined_entity_updates[e_id] = replace(
                        ent_upd,
                        combat=new_combat_upd,
                        readiness_delta=ent_upd.readiness_delta + 10.0,
                        biological=new_bio_upd
                    )

            # 3. Explicit EAT Intent (Only in TAVERN)
            if building_type == "tavern":
                ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                if ent_upd.task and ent_upd.task.work_kind_set == "ENTITY_ACT" and ent_upd.task.payload_set.get("action") == "EAT":
                    # EAT restores hunger
                    EAT_HUNGER_RECOVERY = -20.0
                    
                    biological_upd = ent_upd.biological or BiologicalUpdate()
                    new_bio_upd = replace(biological_upd, hunger_delta=biological_upd.hunger_delta + EAT_HUNGER_RECOVERY)
                    
                    refined_entity_updates[e_id] = replace(
                        ent_upd,
                        biological=new_bio_upd
                    )

        return replace(update, entity_updates=refined_entity_updates)
