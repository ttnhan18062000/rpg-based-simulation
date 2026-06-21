"""reputation_discount.py — Pure reputation-to-discount helper.

No external dependencies. No state mutation.
Formula from TCK-20260619-E33D-REP-DISCOUNTS / docs/mechanics/03_economic_laws.md §4.1.
"""


def apply_reputation_discount(base_cost: int, public_reputation: float) -> int:
    """Return the discounted price for a shop purchase.

    Args:
        base_cost: Pre-discount gold cost (must be >= 1).
        public_reputation: Entity's public reputation (SocialComponent.public_reputation).
                           Expected range 0.0–2.0; values outside range are clamped.

    Returns:
        Discounted cost, floored to a minimum of 1 gold.

    Formula:
        entity_rep  = clamp(public_reputation, 0.0, 2.0) / 2.0   # normalize to [0, 1]
        discount    = entity_rep * 0.20                            # max 20% at rep=2.0
        discounted  = int(base_cost * (1.0 - discount))
        return max(1, discounted)
    """
    entity_rep = max(0.0, min(public_reputation, 2.0)) / 2.0
    discount = entity_rep * 0.20
    return max(1, int(base_cost * (1.0 - discount)))
