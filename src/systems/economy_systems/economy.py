from __future__ import annotations


class DynamicPriceService:
    """
    Authoritative service for shop prices.
    Buy prices are the item's base value: nothing measured at runtime moves them.
    """

    @staticmethod
    def calculate_buy_price(base_value: float) -> int:
        """
        Calculate the buy price for an item.
        Law: Same State = Same Price. The price is a function of the item's base value only; it used to be
        scaled by `1 + salience`, a pressure signal built from the previous tick's measured compute time,
        so the same seed on a slower host paid more (TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING).
        """
        return max(1, int(base_value))

    @staticmethod
    def calculate_sell_price(base_value: float) -> int:
        """
        Calculate the sell price for an item (currently static 50%).
        PH5 E5.6 Out of Scope: Dynamic selling prices.
        """
        return max(1, int(base_value * 0.5))
