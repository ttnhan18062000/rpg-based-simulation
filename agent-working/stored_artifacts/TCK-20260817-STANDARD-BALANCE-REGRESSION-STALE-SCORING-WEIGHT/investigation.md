---
status: active
layer: strategy
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20260817-STANDARD-BALANCE-REGRESSION-STALE-SCORING-WEIGHT
tags: [testing, bug]
---

# Investigation: TCK-20260817-STANDARD-BALANCE-REGRESSION-STALE-SCORING-WEIGHT

## Current Behavior (file:line refs)

`tests/integration/scenarios/test_balance_regression.py:27` hardcodes:
```python
PERSONALITY_BIAS_WEIGHT = 0.25
```
Used only at `tests/integration/scenarios/test_balance_regression.py:213-217` in
`test_scoring_formula_constants_stable`, which asserts a `GATHER_RESOURCE` route with greed=1.0,
confidence=1.0 scores `PERSONALITY_BIAS_WEIGHT * 1.0 + CONFIDENCE_BONUS_WEIGHT * 1.0 == 0.40`.

Real production code, `src/domains/adventure/scoring.py:214-215`:
```python
elif route.family in (RouteFamily.GATHER_RESOURCE, RouteFamily.SELL_LOOT_FOR_GOLD, RouteFamily.TAKE_EASY_QUEST):
    personality_bias += greed * 0.50
```
Real computed score for this scenario: `0.50 + 0.15 = 0.65` — exactly matching the CI failure output.

## Mechanics/Engine Constraints

Per CLAUDE.md's Authoritative Mechanics Rule, `docs/mechanics/` is the definitive source for
simulation laws. `docs/mechanics/04_strategic_cognition.md` §6.2 (line 192) and §6.4 (line 278)
both state the greed weight for this route family is `0.50` (§6.2 explicitly notes: "not a flat
0.25; see §6.4"). §6.4 documents this as an intentional calibration change from
`TCK-20260628-E11C-WEIGHT-TUNING` (2026-06-28): greed 0.25→0.50, sociability 0.25→0.40, after an
E11B personality audit found greed/sociability had negligible (Δ<0.05) effect on route selection
versus bravery's strong multiplicative effect.

`docs/parity_ledger/strategic_cognition.yaml` (STRAT-227, STRAT-228) already reflects the E11C
change — confirmed present and correctly attributing the weight change to that ticket.

**Conclusion: production code and the Mechanics Bible are already in parity and correct.** This is
the inverse of the usual case — the code is right, the doc is right, only the test is stale.

## Docs Requiring Update
None. `docs/mechanics/04_strategic_cognition.md` and `docs/parity_ledger/strategic_cognition.yaml`
are already correct and require no change.

## Parity Ledger Overlap (IDs + status)
`STRAT-227`, `STRAT-228` (`docs/parity_ledger/strategic_cognition.yaml`) — both already `verified`,
already reflect the E11C weight change. No update needed; this ticket doesn't touch production
behavior.

## Prior Work
`TCK-20260628-E11C-WEIGHT-TUNING` (2026-06-28) — the ticket that raised greed weight 0.25→0.50 in
`scoring.py`, updated the mechanics doc §6.4, updated the parity ledger, and added 4 new unit tests
in `tests/unit/domains/adventure/test_phase3_route_scoring.py` covering the new weight. Its own
Files Changed list did NOT include `tests/integration/scenarios/test_balance_regression.py`.

**Root cause of the drift**: `git blame` shows the `greed * 0.50` line in `scoring.py` and the
entire `test_scoring_formula_constants_stable` test function were BOTH touched in a later commit,
`6e25d4f2` (2026-07-02, "Engine audit documentation, simulation quality (in-progress), test refactor
and fixing #19") — but the weight change itself had already landed correctly in `817ca9d2`
(2026-06-28, matching the E11C ticket date). Whoever authored/refactored the balance-regression test
in `6e25d4f2` hardcoded the PRE-E11C weight (0.25) instead of reading the then-current production
value — a test-authoring oversight in a refactor commit, never a code or doc regression.

## Risks and Open Questions
- **Checked**: no other test in `tests/integration/scenarios/test_balance_regression.py` asserts
  `PERSONALITY_BIAS_WEIGHT`, `CONFIDENCE_BONUS_WEIGHT`, or any other pre-E11C weight value —
  `test_scoring_formula_constants_stable` is the only test in the file referencing these constants
  (confirmed via `grep -n "CONFIDENCE_BONUS_WEIGHT\|PERSONALITY_BIAS_WEIGHT"`, 4 matches total, all
  in the constant declarations and this one test function).
- **Checked**: `route_blocked`'s own assertion (`scored_blocked.score == 0.0`) references the
  `expected_score` *variable* (not a separate hardcoded literal), so it will automatically adapt
  once `expected_score` is correctly computed from the corrected constant — no separate fix needed
  there.
- No other test file in the repo references `PERSONALITY_BIAS_WEIGHT` by name (searched, no other
  hits) — this stale constant is fully contained to this one file.

## Anti-Drift Hazards
None identified — this is a self-contained, single-file test-constant correction with no production
or doc changes.
