from __future__ import annotations
from typing import Optional
from src.core.state import AuthoritativeState, EntityState
from src.core.updates import StateUpdate, EntityUpdate, BiologicalUpdate, StrategicUpdate, InventoryUpdate

class HomeAction:
    """Action for private rest and home upgrades."""

    @staticmethod
    def rest(entity: EntityState, state: AuthoritativeState) -> Optional[StateUpdate]:
        """
        Private rest (Free, but only reduces debt by 40%).
        """
        return StateUpdate(
            entity_updates={
                entity.id: EntityUpdate(
                    entity_id=entity.id,
                    biological=BiologicalUpdate(
                        sleep_debt_delta=-(entity.biological.sleep_debt * 0.4)
                    )
                )
            }
        )

    @staticmethod
    def upgrade(entity: EntityState, state: AuthoritativeState) -> Optional[StateUpdate]:
        """
        Upgrade home to resolve maintenance blockers.
        Cost: 100 gold.
        """
        if entity.inventory.gold < 100:
            return None
            
        # Find maintenance blockers
        resolved_blockers = []
        for b_id, b in entity.strategic.blockers.items():
            if b.kind == "maintenance":
                resolved_blockers.append(b_id)
                
        if not resolved_blockers:
            return None
            
        # 3. Transaction with Contingent Updates
        from src.core.updates import ResourceTransferIntent
        intent = ResourceTransferIntent(
            source_id="HOME",
            source_kind="TOWN_SERVICE",
            gold_delta=-100,
            transfer_kind="HOME_UPGRADE",
            strategic_upd=StrategicUpdate(blockers_remove=resolved_blockers)
        )
        
        return StateUpdate(
            entity_updates={
                entity.id: EntityUpdate(
                    entity_id=entity.id,
                    resource_transfers=[intent]
                )
            }
        )
