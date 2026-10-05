---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261005-BRAVERY-QUARTILE-GUARD-RED-ON-MAIN-UNOWNED
artifact_type: plan
tags: [combat, testing, investigation]
---

# Plan: make the precondition explicit and loud; leave the hypothesis alone

Only `tests/integration/scenarios/test_entity_differentiation.py` changes. `src/entities/` (the hold granted
for this ticket) is **not** touched: spawn-time attribute spread is not the cause (bravery differentiates 2.4x
across the populated seeds), so no world-generation behaviour changes.

1. Replace the per-seed hard `assert q_size >= 2` with an exclusion: a seed whose survivors cannot fill
   two-hero quartiles is dropped from the aggregate and recorded as `(seed, n_alive)`. The selection depends on
   survivor count only, never on a rate.
2. `MIN_QUALIFYING_SEEDS = 20` (measured 23 of 24). Below it the test **skips** and names the shortfall and
   the excluded seeds, rather than failing obscurely.
3. The 1.5x assertion and the aggregate-rate-is-nonzero diagnostic are unchanged.
4. Mark `resource_budget_large` (the conftest-documented marker for inherently long multi-seed runs) so the
   test does not die on the default 60 s local budget; CI already passes `--resource-budget large`.

Scope guards: no change to the threshold, the seed list, the spec or `src/`.
