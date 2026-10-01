---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261001-SIMQ-UNIT-SELFMODEL-PILOT-ECONOMY-ANCHOR-REBASELINE
phase: open
date: 2026-10-01
tags: [simulation-quality, economy, calibration]
---

# TCK-20261001-SIMQ-UNIT-SELFMODEL-PILOT-ECONOMY-ANCHOR-REBASELINE

## Title
Re-baseline the `unit_selfmodel_pilot_seed42_1000t` ECONOMY (and marginally NARRATIVE) slow-tier SimQ anchor that moved upward because compile-time herb nodes now yield a real item and herb harvesting completes

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
`TCK-20260930-RESOURCE-NODE-YIELDS-ITEM-COLLIDES-WITH-RESOURCE-KIND` made herb harvesting complete for the first
time. Measured with the fix, `tests/unit/worldassembly/test_corpus_diversity.py::
test_unit_selfmodel_pilot_seed42_1000t_cognition_economy_narrative_grade_stability` fails on a real, tight,
**upward** shift: ECONOMY anchor 0.1465 -> mean ~0.287 (per-trial 0.2886 / 0.2841 / 0.2886, abs_floor 0.0866);
NARRATIVE anchor 0.0 -> ~0.05 (per-trial 0.064 / 0.044 / 0.044, abs_floor 0.05, marginal). The same test passes on
untouched origin/main 73cbf116b. The user chose to name the drift and defer the re-baseline to this ticket rather
than edit anchors in the fix's PR.

## Scope
- Re-measure this test's pillars with the multi-batch method in `docs/testing/regression_policy.md` sections 9-11
  (fresh isolated re-run first; confirm the cause is the herb-yield fix, not something else).
- Check direction: ECONOMY up is consistent with real harvest activity; confirm NARRATIVE's movement is explained
  before touching it (marginal, at its abs_floor).
- Re-derive and record the new anchor/tolerance with a written rationale and the before/after numbers.
- Classify, do not re-baseline, any other anchor found failing for a reason a floor cannot fix.

## Out of Scope
- The other 11 `test_corpus_diversity.py` tests that already fail on untouched origin/main (pre-existing, unrelated
  to the herb-yield fix); they need their own owner.
- Editing any anchor without the measurement method above.
- `frontier_marches` population stability: 5-trial comparison showed noise (fix tree final alive 46/36/47/41/43,
  untouched main 42/46/47/36/39, floor 37.2).

## Acceptance Criteria
- [ ] Fresh isolated re-run confirms or corrects the ECONOMY/NARRATIVE measurements above.
- [ ] Anchor/tolerance updated with a recorded rationale, or the test is left failing with the reason disclosed.
- [ ] The ticket states which tests were re-baselined and which were not, and why.

## Related Tickets
- `TCK-20260930-RESOURCE-NODE-YIELDS-ITEM-COLLIDES-WITH-RESOURCE-KIND` (cause)

## Related Docs
- `docs/testing/regression_policy.md` sections 9-11
- `docs/guidelines/intentional_divergences.md` section 2.60

## Related Stored Artifacts
- `stored_artifacts/TCK-20260930-RESOURCE-NODE-YIELDS-ITEM-COLLIDES-WITH-RESOURCE-KIND/investigation.md`

## Related Code Areas
- `tests/unit/worldassembly/test_corpus_diversity.py`
- `tests/simulation_quality/fixtures/grade_anchors.json`

## Assumptions / Open Questions
- Other slow-tier SimQ anchors may move for the same reason in worlds not in this test's 16-test failing set; only
  the 16 tests in `test_corpus_diversity.py` were measured.
- Whether pre-batch corpus baselines elsewhere (SimQ calibration, determinism hashes) need regenerating is unmeasured.

## Implementation Notes
_(not started)_

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_
