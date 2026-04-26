from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src_legacy.core.state import EntityState, AuthoritativeState
    from src_legacy.core.updates import EntityUpdate

@dataclass(frozen=True)
class AllocateAttributeAction:
    """Action to spend unspent AP on a specific attribute."""
    attribute_name: str # e.g., "strength", "vitality"

    def execute(self, entity: EntityState, state: AuthoritativeState) -> EntityUpdate:
        from src_legacy.core.updates import EntityUpdate, AttributeUpdate, IdentityUpdate
        
        # 1. Validation: Must have unspent AP
        if entity.identity.unspent_ap <= 0:
            return EntityUpdate(entity_id=entity.id)
            
        # 2. Check if attribute exists and is valid
        if not hasattr(entity.attributes, self.attribute_name):
            return EntityUpdate(entity_id=entity.id)
            
        # 3. Calculate delta (PROG-015: Aptitude multipliers)
        # Mapping attribute names to aptitude field names
        mapping = {
            "strength": "str_apt",
            "agility": "agi_apt",
            "vitality": "vit_apt",
            "endurance": "end_apt",
            "intelligence": "int_apt",
            "spirit": "spi_apt",
            "wisdom": "wis_apt",
            "perception": "per_apt",
            "charisma": "cha_apt"
        }
        
        apt_field = mapping.get(self.attribute_name)
        apt_val = getattr(entity.aptitude, apt_field, 1.0) if apt_field else 1.0

        # Points granted = 1 * aptitude (rounded up to avoid 0)
        points_to_add = max(1, int(1 * apt_val))
        
        # 4. Prepare updates
        attr_kwargs = {f"{self.attribute_name}_delta": points_to_add}
        attr_upd = AttributeUpdate(**attr_kwargs)
        
        # Note: unspent_ap_delta is a custom field I added logic for in ApplyPath
        # I should probably update IdentityUpdate to officially include it or use property_updates.
        # For now, I'll use a property update or just assume IdentityUpdate has it (I'll add it to updates.py).
        
        ident_upd = IdentityUpdate(unspent_ap_delta=-1)

        return EntityUpdate(
            entity_id=entity.id,
            attributes=attr_upd,
            identity=ident_upd
        )

