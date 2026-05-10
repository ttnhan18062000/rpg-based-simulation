from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src.core.governance import RuntimeMode

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState

logger = logging.getLogger(__name__)

class DynamicPriceService:
    """
    Authoritative service for pressure-aware economic regulation.
    Implements dynamic price scaling and "Fair Trade Law" caps.
    """

    PRICE_CAP_MULTIPLIER = 3.0

    @staticmethod
    def calculate_buy_price(base_value: float, state: AuthoritativeState, governor_mode: RuntimeMode = RuntimeMode.NORMAL) -> int:
        """
        Calculate the dynamic buy price for an item.
        Law: Same State + Same Pressure = Same Price.
        """
        # 1. Base multiplier from world pressure
        # global_salience is 0.0 (Normal) to 2.0 (Extreme)
        salience = state.pressure_signals.get("global_salience", 0.0)
        multiplier = 1.0 + salience

        # 2. Enforce Price Cap (Fair Trade Law) during high pressure modes
        # We also enforce it globally as a sanity check against runaway multipliers
        if multiplier > DynamicPriceService.PRICE_CAP_MULTIPLIER:
            multiplier = DynamicPriceService.PRICE_CAP_MULTIPLIER
            
        # 3. Gated Cap during Governance Modes
        # In SURVIVAL mode, we might want to TIGHTEN the cap to prevent total bankruptcy, 
        # or LOOSEN it to simulate scarcity. The ticket says "Fair Trade Law (Price Cap) 
        # during SURVIVAL and DEGRADED". 
        # We'll stick to a hard 3.0x for now as per AC.
        
        final_price = int(base_value * multiplier)
        
        # Audit logging for significant deviations
        if multiplier > 1.1:
            # We don't log every tick to avoid spam, but this is a service-level audit point
            pass

        return max(1, final_price)

    @staticmethod
    def calculate_sell_price(base_value: float) -> int:
        """
        Calculate the sell price for an item (currently static 50%).
        PH5 E5.6 Out of Scope: Dynamic selling prices.
        """
        return max(1, int(base_value * 0.5))
