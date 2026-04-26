from __future__ import annotations
from typing import Optional
from dataclasses import replace
from src_legacy.core.state import AuthoritativeState, EntityState, BiologicalComponent
from src_legacy.core.updates import StateUpdate, EntityUpdate, InventoryUpdate, BiologicalUpdate

class InnAction:
    """Action to rest at the Inn for biological recovery."""

    @staticmethod
    def rest(entity: EntityState, state: AuthoritativeState) -> Optional[StateUpdate]:
        """
        Reset biological debt and apply 'well-rested' status.
        Cost: 10 gold.
        """
        # 1. Validation: Has enough gold
        if entity.inventory.gold < 10:
            return None
            
        # 2. Update Biological Component
        new_bio = replace(
            entity.biological,
            sleep_debt=0.0,
            hunger=max(0.0, entity.biological.hunger - 20.0), # Light meal included
            well_rested_until=state.tick + 100
        )
        
        # 3. Transaction
        return StateUpdate(
            entity_updates={
                entity.id: EntityUpdate(
                    entity_id=entity.id,
                    inventory=InventoryUpdate(gold_delta=-10),
                    biological=BiologicalUpdate(
                        sleep_debt_set=0.0,
                        hunger_delta=-20.0,
                        well_rested_until_set=state.tick + 100
                    )
                )
            }
        )
