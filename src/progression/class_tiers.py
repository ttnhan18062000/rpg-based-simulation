from __future__ import annotations
import dataclasses
from typing import Dict, Optional
from src.core.state import AttributeComponent
from src.core.classes import CLASS_TIER_REGISTRY

class ClassTierService:
    """
    Applies a class-tier's attribute_bonuses to an AttributeComponent, live-recomputed
    from the durable class_id on every call (never stored as a permanent delta) —
    mirrors BreakthroughService.apply_bonuses().
    """

    @staticmethod
    def _lookup(class_id: Optional[str]) -> Optional[Dict[str, int]]:
        if not class_id:
            return None
        for options in CLASS_TIER_REGISTRY.values():
            for opt in options:
                if opt.tier_id == class_id:
                    return opt.attribute_bonuses
        return None

    @staticmethod
    def apply_bonuses(class_id: Optional[str], current_attributes: AttributeComponent) -> AttributeComponent:
        bonuses = ClassTierService._lookup(class_id)
        if not bonuses:
            return current_attributes
        updated = {
            attr_name: getattr(current_attributes, attr_name) + amount
            for attr_name, amount in bonuses.items()
        }
        return dataclasses.replace(current_attributes, **updated)
