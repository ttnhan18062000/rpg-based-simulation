---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS
phase: open
date: 2026-07-07T16:31:09Z
tags: [simulation-quality, corpus, calibration, world]
---

# TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS

## Title
Establish `generated_frontier_3_42`'s first-ever grade anchors (200t baseline + capped long-run tier)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` §1.2 found that
`generated_frontier_3_42` has **zero anchors of any kind** in
`tests/simulation_quality/fixtures/grade_anchors.json` — not even a 200t short-run anchor — despite
having its own calibration profile at
`config/simulation_quality/profiles/generated_frontier_3_42.yaml`. This was found incidentally during
the long-run coverage audit and is a distinct, smaller gap from the main long-run-anchor thread: this
world has never been grade-anchored at any tick count, so it currently has zero regression protection
from `test_grade_regression.py` at all.

## Scope
1. Confirm live (do not assume) that `generated_frontier_3_42` compiles and runs cleanly through the
   standard calibration harness (`python3 tools/calibrate_simq.py --name generated_frontier_3_42
   --seed <N> --ticks <T>`) — if it does not, that is itself a genuine finding to document, not paper
   over.
2. Establish the world's first-ever 200t anchor(s), matching the rest of the short-run corpus's
   convention (per investigation.md §1.2's framing of "matching the rest of the short-run corpus
   convention").
3. Establish at least one long-run tier anchor (1000t), capped at 2000t maximum per this epic's
   overall scope cap — do not exceed 2000t.
4. Add each anchor via the same data-only mechanism used elsewhere in this epic (investigation.md
   §4): calibration artifact at `data/calibration/{run_key}/quality_report.json`, entry in
   `grade_anchors.json`, and (for the long-run tier only) an entry in `SLOW_ANCHOR_KEYS` in
   `test_grade_regression.py`.
5. Document the resulting grades in `docs/simulation_quality/eval_matrix_results.md`, noting this is
   the world's first-ever calibration entry.
6. Run `make evaluate --dry-run` to confirm 0 regressions on the rest of the corpus after the new
   entries are added.

## Out of Scope
- Any anchor beyond 2000 ticks.
- Any content/catalog changes to `generated_frontier_3_42` itself — if Scope item 1 reveals the world
  does not compile/run cleanly, document the blocker and escalate rather than fixing world content in
  this ticket (that would be a separate follow-up).
- Adding `generated_frontier_3_42` to `POPULATION_STABILITY_WORLDS` — that is
  `TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP`'s scope; do not duplicate (though this
  ticket's Related Tickets notes the overlap for awareness).
- Work on any other world — this ticket is scoped to `generated_frontier_3_42` only.

## Acceptance Criteria
- [ ] `generated_frontier_3_42` confirmed to compile and run cleanly through the calibration harness
      (or the blocker is documented if it does not)
- [ ] At least one 200t anchor added, matching corpus convention
- [ ] At least one long-run anchor added (1000t), not exceeding 2000t
- [ ] All new anchors added via the data-only mechanism (calibration artifact + `grade_anchors.json`
      + `SLOW_ANCHOR_KEYS` for the long-run entry)
- [ ] `eval_matrix_results.md` documents the new grades as this world's first-ever calibration entry
- [ ] `make evaluate --dry-run` confirms 0 regressions on the rest of the corpus

## Related Tickets
- TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC (parent epic)
- TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP — sibling ticket also touching
  `generated_frontier_3_42` (population-stability test coverage, not grade anchors); no scope
  overlap, but both should be checked against each other's outcome before either closes
- TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS — sibling long-run-anchor ticket for other worlds;
  this ticket is independent of it (different world, no shared dependency) and can run in parallel

## Related Docs
- `staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` §1.2 (the exact finding:
  zero anchors of any kind despite having a calibration profile)
- `docs/simulation_quality/eval_matrix_results.md` — to be updated with this world's first entry

## Related Stored Artifacts
- `staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` (see Related Docs)

## Related Code Areas
- `tests/simulation_quality/fixtures/grade_anchors.json`
- `tests/simulation_quality/test_grade_regression.py` — `SLOW_ANCHOR_KEYS`
- `tools/calibrate_simq.py`
- `config/simulation_quality/profiles/generated_frontier_3_42.yaml`
- `data/worlds/generated_frontier_3_42/`

## Assumptions / Open Questions
- Investigation.md §5 Q4 left open whether this world's total absence from `grade_anchors.json` is
  intentional (used only for corpus-diversity/population-stability tests, not grade calibration) or
  an oversight. This ticket proceeds on the assumption it is an oversight worth closing (per the
  epic's decision to give it its own ticket) — if Scope item 1's live check reveals a structural
  reason the world was never anchored (e.g. it doesn't compile, or its content is intentionally
  minimal/non-representative), that finding overrides this assumption and should be documented
  instead of forcing an anchor.

## Implementation Notes
(to be filled during implementation)

## Test Summary
(to be filled during implementation)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
