from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional

from src.core.items import ItemRegistry

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, BuildingState

# What an item the catalog does not know is worth.
UNKNOWN_ITEM_BASE_VALUE = 10.0


class MarketSystem:
    """
    Authoritative logic for market pricing and deterministic fluctuations.
    VERIFIED v2: market_pricing_determinism
    """

    @staticmethod
    def get_item_base_value(item_id: str) -> float:
        """The item's content base value (EXCH-01, D79): the catalog is the only price source. Only an item the catalog does not know defaults to 10."""
        definition = ItemRegistry.get(item_id)
        return float(definition.value) if definition is not None else UNKNOWN_ITEM_BASE_VALUE

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
        """The item's content kind (MATERIAL, WEAPON, ARMOR, CONSUMABLE, CURRENCY), the key regional and building price modifiers use; OTHER for an unknown item."""
        definition = ItemRegistry.get(item_id)
        return definition.kind.value if definition is not None else "OTHER"
