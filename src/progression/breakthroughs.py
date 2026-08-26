from __future__ import annotations
import dataclasses
from typing import Dict, Any, Set
from src.core.state import AttributeComponent

class BreakthroughService:
    """
    Handles special passive perks (Breakthroughs) earned at milestones.
    """
    
    # Placeholder registry for Phase 8 recovery
    REGISTRY = {
        "iron_will": {
            "name": "Iron Will",
            "attribute_bonuses": {"spirit": 2, "wisdom": 2},
            "description": "Inner strength provides permanent spirit and wisdom."
        },
        "fleet_foot": {
            "name": "Fleet Foot",
            "attribute_bonuses": {"agility": 3},
            "evasion_flat": 0.05,
            "description": "Unnatural speed boosts agility and evasion."
        },
        "titan_grip": {
            "name": "Titan Grip",
            "attribute_bonuses": {"strength": 4},
            "description": "Massive power boosts base strength."
        }
    }

    @staticmethod
    def get_breakthrough(b_id: str) -> Dict[str, Any] | None:
        return BreakthroughService.REGISTRY.get(b_id)

    @staticmethod
    def apply_bonuses(breakthrough_ids: Set[str], current_attributes: AttributeComponent) -> AttributeComponent:
        """
        Sums each known breakthrough's attribute_bonuses and applies them to
        current_attributes, returning a new AttributeComponent. Unknown ids are
        ignored. Non-attribute bonus keys (e.g. fleet_foot's evasion_flat) are
        not part of attribute_bonuses and are not applied here.
        """
        if not breakthrough_ids:
            return current_attributes
        deltas: Dict[str, int] = {}
        for b_id in breakthrough_ids:
            entry = BreakthroughService.REGISTRY.get(b_id)
            if not entry:
                continue
            for attr_name, amount in entry.get("attribute_bonuses", {}).items():
                deltas[attr_name] = deltas.get(attr_name, 0) + amount
        if not deltas:
            return current_attributes
        updated = {
            attr_name: getattr(current_attributes, attr_name) + amount
            for attr_name, amount in deltas.items()
        }
        return dataclasses.replace(current_attributes, **updated)
