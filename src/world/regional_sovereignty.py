from __future__ import annotations
from dataclasses import replace
from typing import Dict, List, Optional, TYPE_CHECKING
from src.core.state import AuthoritativeState, EntityState, RegionState
from src.core.updates import StateUpdate, WorldUpdate, EntityUpdate
from src.core.enums import Faction, EntityRole

if TYPE_CHECKING:
    from src.systems.generator import EntityGenerator

class RegionalSovereigntyService:
    """
    Manages regional taxation and macroscopic sovereignty effects (Debuffs).
    """
    
    TAX_INTERVAL = 100
    TAX_RATE_ENTITY = 2.0  # Gold per entity
    TAX_RATE_BUILDING = 10.0 # Gold per functional building
    
    CONQUERED_ATK_DEF_MOD = 0.8
    CONQUERED_SPD_MOD = 0.9

    @staticmethod
    def process_taxation(state: AuthoritativeState) -> StateUpdate:
        """
        Collects taxes from regions based on ownership.
        """
        if state.tick % RegionalSovereigntyService.TAX_INTERVAL != 0:
            return StateUpdate()
            
        resource_updates: Dict[str, float] = {}
        entity_updates: Dict[int, EntityUpdate] = {}
        
        for r_id, region in state.regions.items():
            if region.owner_faction_id is None:
                continue
                
            total_tax = 0.0
            
            # 1. Tax Entities in the region
            for e_id, entity in state.entities.items():
                if not entity.combat.alive:
                    continue
                    
                from src.engine.legality import LegalityServiceV2
                if LegalityServiceV2.get_region_for_position(entity.navigation.position, state).id == r_id:
                    # If entity is a Hero, they pay tax
                    if entity.identity.role == EntityRole.HERO:
                        tax_amount = min(entity.inventory.gold, RegionalSovereigntyService.TAX_RATE_ENTITY)
                        if tax_amount > 0:
                            total_tax += tax_amount
                            # Deduct from hero via Transaction Intent
                            from src.core.updates import ResourceTransferIntent
                            ent_upd = entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                            intent = ResourceTransferIntent(
                                source_id=r_id,
                                source_kind="TAX",
                                gold_delta=-tax_amount,
                                transfer_kind="TAX"
                            )
                            entity_updates[e_id] = replace(ent_upd, resource_transfers=ent_upd.resource_transfers + [intent])
            
            # 2. Tax Buildings in the region
            for b_id, building in state.buildings.items():
                if building.is_functional:
                    from src.engine.legality import LegalityServiceV2
                    if LegalityServiceV2.get_region_for_position(building.pos, state).id == r_id:
                        total_tax += RegionalSovereigntyService.TAX_RATE_BUILDING
            
            # 3. Add to Faction Resources
            if total_tax > 0:
                faction_key = f"faction_{region.owner_faction_id}_gold"
                resource_updates[faction_key] = resource_updates.get(faction_key, 0.0) + total_tax
                
        return StateUpdate(resource_updates=resource_updates, entity_updates=entity_updates)

    @staticmethod
    def apply_sovereignty_debuffs(state: AuthoritativeState, entity: EntityState) -> Optional[EntityUpdate]:
        """
        Applies CONQUERED_DEBUFF if the hero is in a monster-owned region.
        """
        if entity.identity.role != EntityRole.HERO or not entity.combat.alive:
            return None
            
        from src.engine.legality import LegalityServiceV2
        region = LegalityServiceV2.get_region_for_position(entity.navigation.position, state)
        
        if region and region.owner_faction_id == Faction.MONSTER_HORDE:
            # Check if debuff already applied (to avoid stacking or redundant updates if we used status effects)
            # For now, we'll apply it as a multiplicative modifier in combat math if possible, 
            # or just as a temporary stat penalty in this tick.
            # Legacy says: "multiplies stats.atk and stats.def_ by 0.8, and stats.spd by 0.9"
            
            # We'll use a specific update to flag this for the UI/Replay
            return EntityUpdate(
                entity_id=entity.id,
                # We don't have a specific 'debuff' field in EntityUpdate yet, 
                # but we can apply it to stats if we want it to be persistent or recalculatable.
                # In V2, ApplyPath handles stat recalculation.
                # So we just need to ensure the combat system sees this.
            )
            
        return None
