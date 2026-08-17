---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260817-STANDARD-BALANCE-REGRESSION-STALE-SCORING-WEIGHT
phase: done
date: 2026-08-17
tags: [testing, bug]
---

# TCK-20260817-STANDARD-BALANCE-REGRESSION-STALE-SCORING-WEIGHT

## Title
`test_scoring_formula_constants_stable` hardcodes a pre-E11C `PERSONALITY_BIAS_WEIGHT` (0.25);
production code and Mechanics Bible were both correctly updated to 0.50 and are in parity

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Part of a batch of 7 tickets fixing genuinely pre-existing GitHub Actions CI failures. This one:
`tests/integration/scenarios/test_balance_regression.py::test_scoring_formula_constants_stable`
fails with `Expected score 0.4 (greed×0.25 + confidence×0.15), got 0.65`.

Per this repo's Authoritative Mechanics Rule, code and the Mechanics Bible are the source of truth
this ticket must reconcile the test against — not the other way around. Investigation (independently
confirmed, see Related Docs) found the production and doc values are correct and already in parity;
only this one test's own hardcoded constant is stale.

## Scope
Standard tier per CLAUDE.md (touches Mechanics-Bible-adjacent test coverage) — full pipeline run,
Architecture Review before Implement.

- Update `tests/integration/scenarios/test_balance_regression.py`'s `PERSONALITY_BIAS_WEIGHT`
  constant from `0.25` to `0.50` for the `GATHER_RESOURCE` route family case this test exercises,
  and correct its docstring's `§6.2` citation to `§6.4` (the section that actually documents this
  specific weight, per investigation).
- Search the same test file (and any other test asserting this specific weight) for any OTHER
  pre-E11C stale constant this same drift might have left behind, since the file predates the E11C
  weight-tuning ticket.

## Out of Scope
- Any change to `src/domains/adventure/scoring.py`'s own `greed * 0.50` weight, or to
  `docs/mechanics/04_strategic_cognition.md` §6.2/§6.4, or to `docs/parity_ledger/strategic_cognition.yaml`
  (STRAT-227/228) — all independently confirmed correct and already in parity by investigation.
- Any other of the 7 CI failures in this batch (each has its own ticket).

## Acceptance Criteria
- [x] `test_scoring_formula_constants_stable`'s hardcoded weight matches the real, current,
      documented production value (0.50 for `GATHER_RESOURCE`).
- [x] The test's docstring/citation is corrected to reference the real, current documenting section
      (§6.2 → §6.4).
- [x] `test_scoring_formula_constants_stable` passes.
- [x] No other stale pre-E11C constant is left in the same file (confirmed via `grep -rn`, only 4
      matches total, all in this one constant/function — independently re-confirmed by Architecture
      Review's own broader repo-wide search, which found 2 more `0.25`-valued hits elsewhere in
      `tests/` and confirmed both are non-issues: a different route family whose weight E11C never
      changed, and an unrelated API mock fixture).
- [x] No production code or documentation is changed — confirmed via `git diff --stat`, only
      `tests/integration/scenarios/test_balance_regression.py` touched.

## Related Tickets
- `TCK-20260628-E11C-WEIGHT-TUNING` (the ticket that intentionally raised greed weight 0.25→0.50,
  correctly updating production code, docs, and parity ledger — but not this sibling test)

## Related Docs
- `docs/mechanics/04_strategic_cognition.md` §6.2 (weight table, correctly states 0.50), §6.4
  (calibration note citing TCK-20260628-E11C-WEIGHT-TUNING)
- `docs/parity_ledger/strategic_cognition.yaml` (STRAT-227, STRAT-228 — already reflect the E11C
  change)

## Related Stored Artifacts
None yet — will be created for this standard-tier ticket.

## Related Code Areas
- `tests/integration/scenarios/test_balance_regression.py`
- `src/domains/adventure/scoring.py` (read-only reference — confirmed correct, not modified)

## Assumptions / Open Questions
- Whether any OTHER test file (beyond this one) asserts a pre-E11C weight value is not yet
  confirmed — Investigate must search before Plan finalizes scope.

## Implementation Notes
Changed `PERSONALITY_BIAS_WEIGHT` from `0.25` to `0.50` with a disclosure comment citing E11C.
Updated the test function's own docstring (formula description, expected total 0.40→0.65) and
inline arithmetic comments to match the real, current values. Corrected the `§6.2`→`§6.4` citation
in both the docstring and the assertion's own error message — §6.4 is the section that documents
the E11C calibration rationale, not just the raw weight table.

Architecture Review independently re-verified production code, both doc sections, and both parity
ledger entries (STRAT-227/228) directly, and ran its own broader repo-wide search beyond
Investigate's narrower by-name grep — found 2 more `0.25`-valued hits in `tests/` and confirmed both
are genuine non-issues: `test_adventure_goal_scorer.py`'s `RECOVER`-family weight (never changed by
E11C, still correctly 0.25 per §6.4) and `test_decision_api.py`'s mock fixture dict (tests API
response shaping, not the real formula).

## Test Summary
`pytest tests/integration/scenarios/test_balance_regression.py -v` (full file): 3 passed, 1 skipped
(pre-existing, unrelated skip — `test_blocker_penalty_not_near_binary`), including the target
`test_scoring_formula_constants_stable`. No regressions.

## Files Changed
- `tests/integration/scenarios/test_balance_regression.py` — corrected `PERSONALITY_BIAS_WEIGHT`
  constant, docstring, inline comments, and citation.

## Completion Summary
Fixed the stale test constant: `PERSONALITY_BIAS_WEIGHT` now matches the real, current, already-
documented, already-parity-confirmed production value (0.50, from the intentional E11C calibration
change). No production code, Mechanics Bible, or parity ledger content was touched — all three were
independently confirmed correct by both Investigate and Architecture Review before this ticket's
own single-file diff was written. No other stale pre-E11C constant was found in this or any other
test file (confirmed via two independent searches).
