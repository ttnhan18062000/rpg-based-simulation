# src_v2/engine/evolution.py
# Phase 8 Implementation: Handles Entity Growth Milestones and Role Transformations (LEG-RPG-143).
from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING
from src_v2.core.updates import EntityUpdate, IdentityUpdate, CombatUpdate

if TYPE_CHECKING:
    from src_v2.core.state import AuthoritativeState, EntityState
    from src_v2.core.updates import StateUpdate

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
        """
        for e_id, entity in state.entities.items():
            if not entity.active: continue
            
            ent_upd = update.entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            
            # Current points + proposed delta from this tick
            xp_mult = 1.0
            if entity.biological.well_rested_until >= state.tick:
                xp_mult = 1.5
            
            proposed_delta = 0
            if ent_upd.identity:
                proposed_delta = int(ent_upd.identity.evolution_points_delta * xp_mult)
            
            total_points = entity.identity.evolution_points + proposed_delta
            
            if xp_mult != 1.0 and ent_upd.identity and ent_upd.identity.evolution_points_delta != 0:
                ent_upd = replace(ent_upd, identity=replace(ent_upd.identity, evolution_points_delta=proposed_delta))
                update.entity_updates[e_id] = ent_upd

            if total_points >= EvolutionSystem.EVOLUTION_THRESHOLD:
                # Trigger Authoritative Evolution
                new_level = entity.identity.evolution_level + 1
                new_kind = EvolutionSystem._get_evolved_kind(entity.kind)
                
                # Consolidate updates
                id_upd = ent_upd.identity or IdentityUpdate()
                cb_upd = ent_upd.combat or CombatUpdate()
                
                # Apply Transformation Update
                update.entity_updates[e_id] = replace(
                    ent_upd,
                    kind_set=new_kind,
                    identity=replace(id_upd, 
                        evolution_level_set=new_level,
                        evolution_points_delta=proposed_delta - EvolutionSystem.EVOLUTION_THRESHOLD
                    ),
                    # Evolution provides a 'Restoration' and stat boost
                    combat=replace(cb_upd,
                        hp_delta=cb_upd.hp_delta + 50 # Partial heal on level up
                    ),
                    property_updates={
                        **ent_upd.property_updates,
                        "evolved_this_tick": True, 
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
        # Fallback to suffix if no mapping exists
        return mapping.get(kind.upper(), kind + "_EVOLVED")
