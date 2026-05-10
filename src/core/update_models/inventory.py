from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.models.inventory import ItemStack

@dataclass(frozen=True, slots=True)
class InventoryUpdate:
    """
    RESULT TYPE ONLY. 
    Updates to item container and currency.
    Law: Workers must NOT emit this directly for gold/items; use ResourceTransferIntent.
    """
    items_add: List[ItemStack] = field(default_factory=list)
    items_remove: List[ItemStack] = field(default_factory=list)
    gold_delta: int = 0
    
    def merge(self, other: InventoryUpdate) -> InventoryUpdate:
        """Merge another InventoryUpdate into this one."""
        from dataclasses import replace
        return replace(self,
            items_add=self.items_add + other.items_add,
            items_remove=self.items_remove + other.items_remove,
            gold_delta=self.gold_delta + other.gold_delta
        )
