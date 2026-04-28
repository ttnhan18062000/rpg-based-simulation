from __future__ import annotations
from typing import Optional
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, BiologicalComponent
from src.core.updates import StateUpdate, EntityUpdate, InventoryUpdate, BiologicalUpdate

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
            
        # 2. Transaction with Contingent Updates
        from src.core.updates import ResourceTransferIntent
        intent = ResourceTransferIntent(
            source_id="INN",
            source_kind="TOWN_SERVICE",
            gold_delta=-10,
            transfer_kind="INN_REST",
            biological_upd=BiologicalUpdate(
                sleep_debt_set=0.0,
                hunger_delta=-20.0,
                well_rested_until_set=state.tick + 100
            )
        )
        
        return StateUpdate(
            entity_updates={
                entity.id: EntityUpdate(
                    entity_id=entity.id,
                    resource_transfers=[intent]
                )
            }
        )
