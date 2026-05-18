from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Dict

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, BuildingState

class MarketSystem:
    """
    Authoritative logic for market pricing and deterministic fluctuations.
    VERIFIED v2: market_pricing_determinism
    """

    @staticmethod
    def get_item_base_value(item_id: str) -> float:
        """Returns the static base value for an item."""
        # Baseline values (Milestone 8)
        bases = {
            "gold": 1.0,
            "wood": 2.0,
            "iron_ore": 5.0,
            "steel_ore": 15.0,
            "leather": 4.0,
            "cloth": 3.0,
            "herb": 2.5,
            
            "iron_sword": 50.0,
            "steel_sword": 150.0,
            "iron_plate": 80.0,
            "steel_plate": 240.0,
            "health_potion": 20.0,
            "stamina_potion": 15.0
        }
        return bases.get(item_id, 10.0)

    @staticmethod
    def calculate_price(
        state: AuthoritativeState, 
        building: BuildingState, 
        item_id: str, 
        is_buy: bool = True
    ) -> int:
        """
        Calculates the final gold price for an item at a specific shop.
        
        Law: Price = Base * RegionMod * BuildingMod * (0.8 if Sell else 1.2 if Buy)
        """
        base_val = MarketSystem.get_item_base_value(item_id)
        
        # 1. Regional Modifier
        from src.engine.legality import LegalityServiceV2
        region = LegalityServiceV2.get_region_for_position(building.position, state)
        region_mod = 1.0
        if region:
            # Check for general or item-specific modifiers
            region_mod = region.price_modifiers.get("ALL", 1.0)
            # Item-specific modifier (e.g. "WEAPON", "MATERIAL")
            # For now, we use item_id directly or a kind mapping
            item_kind = MarketSystem.get_item_kind(item_id)
            region_mod *= region.price_modifiers.get(item_kind, 1.0)
        
        # 2. Building Modifier
        building_mod = building.price_modifiers.get("ALL", 1.0)
        item_kind = MarketSystem.get_item_kind(item_id)
        building_mod *= building.price_modifiers.get(item_kind, 1.0)
        
        # 3. Transaction Type Bias
        # Buying from shop is more expensive than selling to shop (Spread)
        type_bias = 1.2 if is_buy else 0.8
        
        final_price = base_val * region_mod * building_mod * type_bias
        
        # Ensure minimum 1 gold
        return max(1, int(final_price))

    @staticmethod
    def get_item_kind(item_id: str) -> str:
        """Maps item IDs to broader categories for modifiers."""
        if "sword" in item_id or "plate" in item_id:
            return "GEAR"
        if "ore" in item_id or item_id in ("wood", "leather", "cloth"):
            return "MATERIAL"
        if "potion" in item_id or item_id == "herb":
            return "CONSUMABLE"
        return "OTHER"
