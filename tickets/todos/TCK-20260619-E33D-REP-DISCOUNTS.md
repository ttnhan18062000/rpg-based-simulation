---
status: open
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260619-E33D-REP-DISCOUNTS
phase: open
date: 2026-06-20
tags: [macro-economy, reputation, shop-pricing, known-limitations, phase-3]
---

# TCK-20260619-E33D-REP-DISCOUNTS

## Title
Epic 3.3D · Reputation-Based Shop Discounts

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`docs/engine/known_limitations.md` explicitly states "reputation-based shop discounts unsupported." This ticket closes that gap: entities with high faction reputation get price discounts at that faction's shops. On completion, remove the limitation claim.

**Requires:** TCK-20260619-E33A-HEALTH-MONITOR (active economy needed to test meaningfully)

## Scope

In shop pricing logic (locate `src/domains/economy/` or `src/systems/economy_systems/`):

```python
def apply_reputation_discount(base_price: int, entity_rep: float, faction_id: str, shop_faction: str) -> int:
    """Apply reputation discount if entity is in good standing with shop's faction."""
    if faction_id != shop_faction:
        return base_price
    # rep range: -1.0 to 1.0; discount 0% to 20%
    discount = max(0.0, entity_rep) * 0.20
    return int(base_price * (1.0 - discount))
```

### First step
Find where shop `gold_cost` is computed in the buy transaction flow. This is where the discount multiplier applies. Search `src/engine/interaction.py` or `src/systems/economy_systems/` for shop BUY path.

### After completion
Remove the "reputation discounts unsupported" claim from `docs/engine/known_limitations.md`. Update `docs/mechanics/03_economic_laws.md` with discount formula. Run `make knowledge-index-update`.

## Acceptance Criteria
- Entity with `faction_rep["merchant_league"] = 0.8` pays 16% less at merchant_league shops
- Entity with neutral rep pays full price
- `test_reputation_discount_applies` passes
- `docs/engine/known_limitations.md` updated (claim removed)

## Related Tickets
- TCK-20260619-E33-MACRO-ECONOMY (parent epic)
- TCK-20260619-E33A-HEALTH-MONITOR (needed for meaningful economy context)

## Related Docs
- `docs/engine/known_limitations.md` (remove discount claim on completion)
- `docs/mechanics/03_economic_laws.md` (add discount formula)

## Related Code Areas
- Shop BUY transaction path (find via grep before implementing)
- `docs/engine/known_limitations.md`

## Test Summary
```bash
pytest tests/integration/scenarios/test_macro_economy.py::test_reputation_discount_applies -x -v -m slow
```
## Files Changed
_To be filled on completion._
## Completion Summary
_To be filled on completion._
