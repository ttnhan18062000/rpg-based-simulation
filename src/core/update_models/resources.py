from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.core.models.inventory import ItemStack
    from src.core.updates import (
        BiologicalUpdate, AttributeUpdate, IdentityUpdate, 
        CombatUpdate, StrategicUpdate, EquipmentUpdate, RewardUpdate
    )

@dataclass(frozen=True, slots=True)
class ResourceTransferIntent:
    """
    Proposed atomic transfer between a world source and an entity.
    Used by ResourceTransactionResolver to enforce conservation laws.
    VERIFIED v2: ResourceTransferIntent
    """
    source_id: str | int
    source_kind: str # "NODE", "GROUND_ITEM", "CORPSE", "CRAFTING", "SHOP_BUY", "SHOP_SELL"
    items_add: List[ItemStack] = field(default_factory=list)
    items_remove: List[ItemStack] = field(default_factory=list)
    gold_delta: int = 0
    gold_cost: int = 0
    price_multiplier: float = 1.0
    xp_reward: int = 0
    transfer_kind: str = "AUTO" # "HARVEST", "LOOT", "PICKUP", "CRAFT", "BUY", "SELL"
    transaction_id: Optional[str] = None
    group_id: Optional[str] = None
    is_group_required: bool = True
    # Contingent updates (applied only on transaction success)
    biological_upd: Optional[BiologicalUpdate] = None
    attributes_upd: Optional[AttributeUpdate] = None
    identity_upd: Optional[IdentityUpdate] = None
    combat_upd: Optional[CombatUpdate] = None
    strategic_upd: Optional[StrategicUpdate] = None
    equipment_upd: Optional[EquipmentUpdate] = None
    reward_upd: Optional[RewardUpdate] = None
