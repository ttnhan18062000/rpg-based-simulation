---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260817-STANDARD-BEHAVIORAL-5K-BASELINE-REFRESH
phase: done
date: 2026-08-17
tags: [simulation-quality, testing, bug]
---

# TCK-20260817-STANDARD-BEHAVIORAL-5K-BASELINE-REFRESH

## Title
Refresh the stale `baseline_5k.json` regression baseline, causally confirmed to be intentional
drift from 2 already-closed goal-arbitration fixes, not a bug

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`tests/regression/test_behavioral_5k.py::test_behavioral_5k_regression` — one of the 439 tests
never run by any CI job (in one of the 16 orphaned test directories added by commit `29d78798`).
A local run (`--resource-budget large`, matching CI's `slow` job) fails for real:
`alive_avg` +17.3% (limit ±10%), `gold_avg` +27.7% (limit ±20%) vs. the committed baseline
(generated 2026-06-28).

Root-caused the drift to two already-closed, documented tickets squashed into the same commit
(`29d78798`) that introduced this orphaned test directory:
`TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT` (fixed HARVESTING starved by
COMBAT_ENGAGE/REGION_STABILIZATION in tier-5 goal competition) and
`TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5` (fixed ADVENTURE_ROUTE being
structurally dead in goal scoring). Both directly explain higher survival/economic activity —
previously-starved goal kinds now winning some competitions. The baseline was simply never
refreshed against these intentional changes because this regression test isn't in CI.

## Scope
- Confirm the drift is fully explained by the two cited tickets before refreshing (per this
  repo's hard rule against editing an artifact just to make a gate pass).
- `make regression-baseline` to regenerate `tests/regression/baseline_5k.json`.

## Out of Scope
- Any change to `src/ai/goals/` or goal-arbitration logic — already correctly fixed by the two
  cited tickets; this ticket only catches the baseline up.
- An exhaustive commit-by-commit audit of the entire squashed `29d78798` commit — the
  working_log.csv cross-reference for goal-scoring-tagged tickets was judged sufficient given the
  exact directional/causal match.
- Any other ticket in this batch.

## Acceptance Criteria
- [x] Drift causally confirmed as intentional before any refresh (not assumed).
- [x] `test_behavioral_5k_regression` passes with the refreshed baseline.
- [x] Refreshed baseline's metrics exactly match the pre-refresh failing run's actual values
      (confirms the refresh captured the real, current, deterministic behavior).

## Related Tickets
- `TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT` (causal source)
- `TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5` (causal source)

## Related Docs
None.

## Related Stored Artifacts
`stored_artifacts/TCK-20260817-STANDARD-BEHAVIORAL-5K-BASELINE-REFRESH/`

## Related Code Areas
- `tests/regression/baseline_5k.json`

## Assumptions / Open Questions
None.

## Implementation Notes
Reproduced the drift deterministically (seed=42, byte-identical across 2 runs: `alive_avg=13.3`,
`gold_avg=584.16`), confirmed it's fully explained by 2 real, closed tickets whose own root-cause
descriptions (DEBUG-traced win-rate starvation, a miscalibrated denominator) directly predict this
exact direction of change, then ran `make regression-baseline` to regenerate the committed file.

## Test Summary
- Pre-refresh: `pytest tests/regression/test_behavioral_5k.py -m extra_slow --resource-budget
  large -q`: 1 failed (2 metrics out of band).
- Post-refresh: same command: 1 passed in 104.95s.

## Files Changed
- `tests/regression/baseline_5k.json`

## Completion Summary
Confirmed the drift was the intentional, expected consequence of two already-closed
goal-arbitration fixes squashed into the same commit that introduced this orphaned test directory,
not a regression the refresh would mask. Refreshed the baseline per the test's own documented
"if intentional, refresh and commit" instruction.
