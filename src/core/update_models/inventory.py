from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

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

    def is_noop(self) -> bool:
        return not self.items_add and not self.items_remove and self.gold_delta == 0


@dataclass(frozen=True, slots=True)
class ItemInstanceUpdate:
    """RESULT TYPE ONLY. Appends a new owner to an existing ItemInstance's owner_history.
    Law: only ApplyPath may consume this — no direct mutation of a live ItemInstance.

    CONTRACT (see plan.md Step 4, 'ItemInstanceUpdate.merge() — resolved'): StateUpdate.merge_many
    combines item_instance_updates by plain last-write-wins dict overwrite per instance_id, NOT
    by combining owner_history_append values. At most one ItemInstanceUpdate per instance_id per
    tick is supported today. Proposing two updates for the same instance_id within the same tick
    will silently keep only the last one merged — acceptable only because this ticket ships zero
    real production call sites that mint or transfer ItemInstances. A future ticket must add real
    per-instance merge semantics (e.g. concatenating owner_history_append in order) before any
    production caller can propose more than one transfer per instance per tick.
    """
    instance_id: int
    owner_history_append: Optional[str] = None

    def is_noop(self) -> bool:
        return self.owner_history_append is None
