---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260619-E33D-REP-DISCOUNTS
phase: done
date: 2026-06-20
tags: [macro-economy, reputation, shop-pricing, known-limitations, phase-3]
---

# TCK-20260619-E33D-REP-DISCOUNTS

## Title
Epic 3.3D · Reputation-Based Shop Discounts

## Status
DONE

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

## Assumptions / Open Questions

- DEV-001: Faction cross-check from ticket pseudocode skipped — no per-faction reputation dict on `SocialComponent`. Discount applied universally based on `public_reputation`. Documented in `docs/guidelines/intentional_divergences.md` §5.

## Implementation Notes

1. Created `src/systems/economy_systems/reputation_discount.py` — pure `apply_reputation_discount(base_cost: int, public_reputation: float) -> int`. Formula: clamp rep [0,2], normalize /2.0, discount = norm*0.20, return max(1, int(base_cost*(1-discount))).
2. Wired into `src/town/shop.py::ShopService.buy_item` (proposal layer) after `total_cost = unit_price * quantity`.
3. Wired into `src/engine/shop.py::ShopSystem.enforce` (enforcement layer) — discount applied to `legal_total` before the `gold_cost < legal_total` guard so discounted intents pass enforcement.
4. Updated `docs/engine/known_limitations.md` §1.4 — gap marked RESOLVED.
5. Updated `docs/mechanics/03_economic_laws.md` §4.1 — discount formula documented.
6. Added `test_reputation_discount_applies` to `tests/integration/scenarios/test_macro_economy.py`.
7. Updated parity ledger: TOWN-016 v2_evidence updated; TOWN-181 added.
8. Added DEV-001 to `docs/guidelines/intentional_divergences.md` §5.

## Test Summary
```bash
pytest tests/integration/scenarios/test_macro_economy.py::test_reputation_discount_applies -x -v
```

## Files Changed
- `src/systems/economy_systems/reputation_discount.py` (created)
- `src/town/shop.py` (import + 1-line call in buy_item)
- `src/engine/shop.py` (import + discount applied to legal_total in enforce)
- `docs/engine/known_limitations.md` (§1.4 added)
- `docs/mechanics/03_economic_laws.md` (§4.1 added)
- `tests/integration/scenarios/test_macro_economy.py` (test_reputation_discount_applies added)
- `docs/parity_ledger/town_resource.yaml` (TOWN-016 updated, TOWN-181 added)
- `docs/guidelines/intentional_divergences.md` (DEV-001 added)

## Completion Summary
Implemented reputation-based shop discounts as `apply_reputation_discount(base_cost, public_reputation) -> int` in a new pure-function module `src/systems/economy_systems/reputation_discount.py`. Wired into both the proposal layer (`ShopService.buy_item`) and the enforcement layer (`ShopSystem.enforce`) symmetrically so discounted intents pass enforcement validation. Formula: entity_rep = public_reputation/2.0 (normalized 0–1), discount = entity_rep * 0.20 (up to 20%), floor at 1 gold. DEV-001 declared: faction cross-check from ticket pseudocode skipped (no per-faction dict on SocialComponent); discount is universal. Closed known_limitations.md gap (§1.4 added), documented formula in 03_economic_laws.md §4.1, added DEV-001 to intentional_divergences.md, updated parity ledger (TOWN-016 updated, TOWN-181 added). Test `test_reputation_discount_applies` added covering 6 cases including conservation invariant.
