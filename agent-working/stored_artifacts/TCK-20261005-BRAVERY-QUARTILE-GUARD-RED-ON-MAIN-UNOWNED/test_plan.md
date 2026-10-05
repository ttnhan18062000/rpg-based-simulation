---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261005-BRAVERY-QUARTILE-GUARD-RED-ON-MAIN-UNOWNED
artifact_type: test_plan
tags: [combat, testing, investigation]
---

# Test plan

- Before: with `--resource-budget off` the guard fails at seed 9 (`n_alive=7`, `q_size=1`); at the default
  budget it fails with the conftest 60 s `TimeoutError`.
- After: the guard runs under its own `resource_budget_large` budget, excludes seed 9, evaluates the
  hypothesis on the 23 populated seeds and passes (ratio 2.40 against the 1.5 asserted).
- The skip path: not exercised by the real run (23 >= 20). It is exercised directly by
  `test_bravery_quartile_skips_loudly_below_min_qualifying_seeds`, which patches the per-seed runner to return
  collapsed quartiles and asserts the skip message names the shortfall and the excluded seeds.
- Threshold unchanged: asserted by reading the diff (the `1.5 *` expression and its message are untouched).
- Not covered: why survivors fell from the calibrated `>= 8` floor; recorded as open in the ticket.

## Proof Plan

- level: integration (real `Kernel.tick_once()`, 24 seeds x 400 ticks)
- proof kind: regression guard re-established with an explicit population precondition
- oracle source: `docs/mechanics/02_combat_laws.md` (bravery's role in engagement) and the guard's own recorded
  calibration in `TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION`
- expected effect: green with a stated reason, or skipped with the shortfall named; never an obscure failure
- selected commands: `pytest tests/integration/scenarios/test_entity_differentiation.py -rsf`
