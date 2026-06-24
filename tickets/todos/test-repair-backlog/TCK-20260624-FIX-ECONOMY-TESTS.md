---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260624-FIX-ECONOMY-TESTS
phase: open
date: 2026-06-24
tags: [economy, test-assertions, reputation-discount, pricing]
---

# TCK-20260624-FIX-ECONOMY-TESTS

## Title
Update economy test assertions to reflect post-reputation-discount pricing (TCK-20260619-E33D-REP-DISCOUNTS)

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`TCK-20260619-E33D-REP-DISCOUNTS` introduced a reputation discount: entities with `public_reputation=1.0` (the V2EntityBuilder default) receive a 10% discount on all shop purchases. Five economy tests were not updated after this change and now assert the pre-discount price values (100, 150, 300, 200, etc.) while the implementation correctly returns the discounted values (90, 135, 270, 180).

One additional test (`test_shop_buy_and_sell`) returns `None` from the buy call — likely a different path issue that needs investigation alongside the others.

## Scope
- Update assertions in `test_economy_hardening.py` to match post-discount values, OR switch test entities to `public_reputation=0.0` for pure pricing tests (preferred — makes the intent clearer)
- Investigate `test_shop_buy_and_sell::assert None is not None` — determine if the buy path changed signatures
- Fix `test_insufficient_gold_records_reason` — confirm assertion value after discount

## Out of Scope
- Changing the pricing formula or reputation discount logic
- Updating `docs/mechanics/03_economic_laws.md` (the formula is correct and documented)

## Acceptance Criteria
- All 6 listed tests pass
- Test intent is preserved: pure pricing tests use `public_reputation=0.0` entities; discount tests (if any) explicitly set rep > 0

## Related Tickets
- `TCK-20260619-E33D-REP-DISCOUNTS` (root cause — introduced the discount)

## Related Docs
- `docs/mechanics/03_economic_laws.md §4.1` — pricing formula and reputation discount
- `docs/parity_ledger/town_resource.yaml` — check for `divergent` entries

## Related Stored Artifacts
None

## Related Code Areas
- `tests/unit/resource/test_economy_hardening.py` — 4 failing tests
- `tests/unit/world/test_economy_contract.py::test_shop_buy_and_sell`
- `tests/integration/pipeline/test_transaction_completion.py::TestTransactionRejectionReasons::test_insufficient_gold_records_reason`
- `src/town/shop.py:38` — applies `apply_reputation_discount(total_cost, entity.social.public_reputation)` after price calculation

## Assumptions / Open Questions
- Confirm that `V2EntityBuilder` sets `public_reputation=1.0` by default (the investigation found this to be the case)
- For `test_shop_buy_and_sell` returning `None`: check if `ShopService.buy()` signature changed (returns result object vs raises)
- Decide: update assertions to discounted values, OR use `public_reputation=0.0` entities in pricing-focused tests

## Implementation Notes
Preferred approach for `test_economy_hardening.py`:
```python
# In the test entity builder, set rep=0.0 to test raw pricing
entity = V2EntityBuilder(...).with_social(public_reputation=0.0).build()
# Then assertions remain: assert price == 100  (not 90)
```
Alternative: keep rep=1.0 and update assertions to 90, 135, 270, 180.

For `test_shop_buy_and_sell`: run with `--tb=long`, trace whether `ShopService.buy()` now raises instead of returning, or returns a result object.

## Test Summary
Run: `pytest tests/unit/resource/test_economy_hardening.py tests/unit/world/test_economy_contract.py::test_shop_buy_and_sell tests/integration/pipeline/test_transaction_completion.py::TestTransactionRejectionReasons::test_insufficient_gold_records_reason --tb=short -v`

## Files Changed
TBD

## Completion Summary
TBD
