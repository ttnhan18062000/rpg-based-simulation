---
status: active
layer: strategy
authority: P1
audience: agent
artifact_type: plan
ticket_id: TCK-20260817-STANDARD-BALANCE-REGRESSION-STALE-SCORING-WEIGHT
tags: [testing, bug]
---

# Plan: TCK-20260817-STANDARD-BALANCE-REGRESSION-STALE-SCORING-WEIGHT

## Scope Guard
This plan touches exactly one file: `tests/integration/scenarios/test_balance_regression.py`. No
production code (`src/`), no `docs/mechanics/`, no `docs/parity_ledger/` file is touched — all three
were independently confirmed correct and already in parity by Investigate. If Implement finds any
reason to touch a file outside this list, it must stop and disclose rather than proceed silently.

## Steps

1. In `tests/integration/scenarios/test_balance_regression.py`, change line 27:
   ```python
   PERSONALITY_BIAS_WEIGHT = 0.25
   ```
   to:
   ```python
   PERSONALITY_BIAS_WEIGHT = 0.50  # E11C (2026-06-28): raised from 0.25 -- see §6.4
   ```

2. Update `test_scoring_formula_constants_stable`'s own docstring (lines 179-186) and inline
   comments (lines 199-205) to reflect the real, current expected value (`0.25 + 0.15 = 0.40` →
   `0.50 + 0.15 = 0.65`) and correct the citation from `§6.2` to `§6.4` (the section that documents
   *why* this specific weight is 0.50, per Investigate's finding — §6.2 states the value but §6.4
   is where the E11C calibration rationale lives).

3. Update the f-string error messages at lines 216-218 that reference `docs/mechanics/04_strategic_cognition.md
   §6.2` — same citation correction to `§6.4`.

4. Run `pytest tests/integration/scenarios/test_balance_regression.py -v` (full file) and confirm
   all tests pass, not just the target test.

5. Do NOT touch `src/domains/adventure/scoring.py`, `docs/mechanics/04_strategic_cognition.md`, or
   `docs/parity_ledger/strategic_cognition.yaml` — all three already correctly reflect the 0.50
   weight and require no change (confirmed by Investigate).

## Acceptance-Criteria Map
- AC1 (weight matches current production value) → Step 1.
- AC2 (docstring/citation corrected) → Steps 2-3.
- AC3 (test passes) → Step 4.
- AC4 (no other stale constant left in the file) → already confirmed by Investigate's own
  exhaustive grep (no further action needed, but Step 4's full-file run re-confirms no
  regression).
- AC5 (no production/doc change) → Step 5 (explicit negative constraint).

## Risks and Open Questions
None — this is a narrow, single-file, single-constant correction with the ground truth
(production code + Mechanics Bible + parity ledger) already independently confirmed consistent.

## Deviations (recorded during Implementation)
(none yet)
