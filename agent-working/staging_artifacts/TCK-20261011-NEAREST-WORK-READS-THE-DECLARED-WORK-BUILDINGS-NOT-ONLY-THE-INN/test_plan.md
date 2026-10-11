---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261011-NEAREST-WORK-READS-THE-DECLARED-WORK-BUILDINGS-NOT-ONLY-THE-INN
artifact_type: test_plan
tags: []
---

# test_plan — TCK-20261011-NEAREST-WORK-READS-THE-DECLARED-WORK-BUILDINGS-NOT-ONLY-THE-INN

## Tests (written with the change)
- State: the two fields default to 0, round-trip through `to_canonical_dict` and checkpoint, and `needed` is copied from content at compile.
- Update/apply: delta adds, set resets, set-then-delta in one tick keeps the delta; a merge of two updates is order-independent.
- Reset: at a tax tick `done` returns to 0 for every standing building and not on other ticks; a wrecked building is skipped.
- Derived upkeep: `required = needed x WAGE_GOLD`; a purse of 11 with needed 2 tops up 1 from the treasury; neither can pay closes the building; paying reopens it; `MAINTENANCE_COST` no longer exists.
- Shift counting: a paid shift increments `done`; a building with `done == needed` is not chosen by `nearest_work` and its WORK action pays nothing; the treasury top-up never exceeds the remaining need.
- `nearest_work`: reaches a non-inn building that declares shifts (a kind not named in the test's code under test), prefers the nearest in reach, respects `serves` and `way_in_range`, and does not name a building kind in source (an ast-grep style check on the module).
- Conservation: coin is conserved over a period with shifts (purse + treasury + worker purses unchanged in total); no coin minted.
- Inn: unchanged for a subject at an inn whose need is not met; Q1 decides the capped case.
- Integration: a gate world where a broke subject reaches a treasury building's shift and is paid; the `free-meal-OFF` arm measurement (purse balances, top-up counts, wages per kind).
- Regression: the batch-3 treasury tests (test_work_shift_pays_a_wage..., test_tax_and_upkeep, test_treasury_account), mechanism-registry pins, golden live-signal fixture.
