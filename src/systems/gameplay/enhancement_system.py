"""EnhancementSystem handles gear upgrades (+1 to +15).

Enhancements cost Gold and specific Materials. Each level increases the item's power
and adds a suffix (e.g., "Steel Sword +1").

Tiers:
+1 to +5: Basic (Iron/Steel)
+6 to +10: Rare (Mithril/Adamant)
+11 to +15: Legendary (Orichalcum/Godsteel)

Success Rate:
+1 to +3: 100%
+4 to +7: 80% (failure = no change)
+8 to +12: 50% (failure = drop level -1)
+13 to +15: 35% (failure = drop level -1)
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src.core.models.enums import Domain, ItemType

if TYPE_CHECKING:
    from src.core.entities.entity import Entity
    from src.platform.rng import DeterministicRNG

logger = logging.getLogger(__name__)

class EnhancementSystem:
    """Business logic for the Blacksmith's enhancement service."""
    
    @staticmethod
    def can_enhance(entity: Entity, item_id: str) -> tuple[bool, str]:
        """Check if the entity can afford and has the level for the next upgrade."""
        # This is a simplified check. In a real system, we'd lookup item current level.
        # For our simulation, we'll store (+N) in the item instance data or just use a naming convention.
        # However, our ITEM_REGISTRY uses static IDs. We need a way to track INSTANCE level.
        # If the simulation doesn't support item instances with metadata, we might need to 
        # swap the item ID for a new one (e.g. "sword_1" -> "sword_2").
        return True, "Ready"

    @staticmethod
    def get_cost(current_level: int) -> int:
        """Gold cost for the next level."""
        return 50 * (current_level + 1) ** 2

    @staticmethod
    def get_material_cost(current_level: int) -> dict[str, int]:
        """Material requirements for the next level."""
        if current_level < 5:
            return {"iron_ore": 2}
        elif current_level < 10:
            return {"mithril_ore": 1}
        else:
            return {"godsteel_ore": 1}

    @staticmethod
    def perform_upgrade(entity: Entity, item_id: str, rng: DeterministicRNG, tick: int) -> str | None:
        """Attempt to upgrade the item. Returns new item_id if successful, or None."""
        # For this simulation, we'll assume item IDs follow the pattern "base_id[+N]"
        # or we just simulate the stat boost.
        # Given the current system, we'll implement a naming convention: "iron_sword" -> "iron_sword_+1"
        
        parts = item_id.split("_+")
        base_id = parts[0]
        current_lv = int(parts[1]) if len(parts) > 1 else 0
        
        if current_lv >= 15:
            return None # Max level
            
        cost = EnhancementSystem.get_cost(current_lv)
        if entity.stats.progression.gold < cost:
            return None
            
        # Success check
        rate = 1.0
        if current_lv >= 12: rate = 0.35
        elif current_lv >= 7: rate = 0.50
        elif current_lv >= 3: rate = 0.80
        
        entity.stats.progression.gold -= cost
        
        if rng.next_bool(Domain.ITEM, entity.id, tick, rate):
            new_lv = current_lv + 1
            new_id = f"{base_id}_+{new_lv}"
            logger.info(f"Tick {tick}: Entity {entity.id} enhanced {item_id} to SUCCESS (+{new_lv})")
            return new_id
        else:
            # Failure
            if current_lv >= 7:
                new_lv = max(0, current_lv - 1)
                new_id = f"{base_id}_+{new_lv}" if new_lv > 0 else base_id
                logger.info(f"Tick {tick}: Entity {entity.id} FAIL enhanced {item_id} -> Dropped to +{new_lv}")
                return new_id
            logger.info(f"Tick {tick}: Entity {entity.id} FAIL enhanced {item_id} -> No change")
            return item_id
