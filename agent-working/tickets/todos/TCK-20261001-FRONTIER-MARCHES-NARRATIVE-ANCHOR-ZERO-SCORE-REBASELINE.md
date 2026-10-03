---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261001-FRONTIER-MARCHES-NARRATIVE-ANCHOR-ZERO-SCORE-REBASELINE
phase: open
date: 2026-10-01
tags: [simulation-quality, grade-thresholds, testing]
---

# TCK-20261001-FRONTIER-MARCHES-NARRATIVE-ANCHOR-ZERO-SCORE-REBASELINE

## Title
`test_frontier_marches_seed42_200t_narrative_grade_stability` asserts a NARRATIVE `anchor_score` of
`0.0` while the simulation now reliably produces narrative — a stale anchor, re-baseline per
`regression_policy.md` §9-11

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Found by `TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED` during its (a)/(b)/(c) classification
pass. Measured at `HEAD = 71c4aa321` with `src/` and `tests/` verified clean, under
`--resource-budget large` so the known 60s SIGALRM cap could not masquerade as the result:

```
NARRATIVE: mean_score=0.2665 across 3 trials outside tolerance of anchor_score=0.0 (abs_floor=0.05)
           per-trial values: [0.41818181818181815, 0.22916666666666666, 0.15204678362573099]
```
(`tests/unit/worldassembly/test_corpus_diversity.py:2071`)

**The anchor expects a NARRATIVE score of `0.0`** — it was set when this world produced no narrative at
all. The simulation now produces narrative on every trial. **This is a class (a) finding: the anchor's
expected value is stale and the current behaviour is correct — in fact better.** The drift direction is
improvement, not regression.

**It also supersedes the recorded reason for this anchor's failure.** The module docstring in
`test_corpus_diversity.py` (from `TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH`,
2026-08-29) records this anchor as crashing with
`TypeError: can only concatenate tuple (not "list") to tuple` at `lifecycle.py:122` in death/heir
succession. **That bug is fixed** — the concat now reads `list(entity.inventory.items) + heirloom_stacks`
at `lifecycle.py:252`. The docstring's classification of this anchor is therefore stale and should be
corrected as part of this ticket.

**Why this is its own ticket.** The parent ticket's Out of Scope forbids blanket-adjusting anchors to
green, but explicitly permits the opposite: "Re-baselining a specific anchor against evidence is
legitimate and is handled per `docs/testing/regression_policy.md` §9-11 in its own ticket." This mirrors
how `TCK-20261001-SIMQ-UNIT-SELFMODEL-PILOT-ECONOMY-ANCHOR-REBASELINE` was split out of the same family.

## Scope
- Gather enough fresh trials to meet `docs/testing/regression_policy.md` §9-11's evidence bar. **Three
  trials is what the failing assertion itself ran and is below that bar** — do not re-baseline on the
  numbers quoted above.
- Derive a new `anchor_score` and tolerance that covers the genuine per-trial variability. The observed
  spread is 0.152 → 0.418, roughly 2.75x, so a tolerance derived only from the mean will flake.
- Record the derivation in the test's own docstring, matching the style the re-baselined anchors in this
  file already use.
- Correct the module docstring's stale `TypeError` classification for this anchor.
- State whether the narrative that now appears is itself expected — i.e. confirm the increase traces to
  intended narrative-system work and is not a symptom. A stale anchor and a real behaviour change can
  look identical from the anchor alone.

## Out of Scope
- The other 12 red grade anchors — `TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED` owns the
  family-level classification and the reporting path. ~10 of them are class (c) and are **not**
  re-baselining candidates.
- `TCK-20261001-SIMQ-UNIT-SELFMODEL-PILOT-ECONOMY-ANCHOR-REBASELINE` — a different anchor, already owned.
- Making CI gate on `@slow`.
- The `QueueDrainWorker` teardown leak — already root-caused as a consequence of the backpressure issue.

## Acceptance Criteria
1. A new `anchor_score` and tolerance for the NARRATIVE pillar, derived from enough trials to satisfy
   `regression_policy.md` §9-11, with the derivation recorded in the test docstring.
2. The tolerance demonstrably covers the observed per-trial variability (no flake across a fresh run of
   at least the trial count the policy requires).
3. A stated judgement on whether the narrative increase is intended behaviour, with evidence — not an
   assumption that a red anchor must mean a stale anchor.
4. The module docstring's stale `TypeError`-crash classification for this anchor is corrected.
5. The anchor passes under the same conditions the parent ticket measured (clean tree, stated budget).

## Related Tickets
- `TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED` — parent; found and classified this.
- `TCK-20261001-SIMQ-UNIT-SELFMODEL-PILOT-ECONOMY-ANCHOR-REBASELINE` — sibling, same split pattern.
- `TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH` — recorded the now-stale reason.
- `TCK-20260817-STANDARD-SIMQ-COGNITION-BIT-IDENTICAL-GUARD-TOLERANCE-CONVERSION` — established the
  3-trial tolerance assertion shape this anchor uses.

## Related Docs
- `docs/testing/regression_policy.md` §9-11 — the mandatory re-baselining procedure.
- `docs/testing/test_taxonomy.md` — what `@slow` is meant to signify.

## Related Stored Artifacts
- `stored_artifacts/TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED/` (once migrated) — carries
  the measurement and the family-level classification this ticket was split from.

## Related Code Areas
- `tests/unit/worldassembly/test_corpus_diversity.py` — the anchor (~:2071) and the module docstring.
- `src/simulation_quality/` — the NARRATIVE pillar scorer.

## Assumptions / Open Questions
- Assumes the narrative increase is intended. **Not verified** — AC3 exists precisely because assuming a
  stale anchor is the comfortable conclusion and would erase a real behaviour change if wrong.
- Whether the ~2.75x per-trial spread is itself acceptable, or whether this anchor is partly class (c)
  and needs a wider structural fix rather than a re-centred value, is open.

## Implementation Notes
_To be completed during implementation._

## Test Summary
_To be completed during implementation._

## Files Changed
_To be completed during implementation._

## Completion Summary
_To be completed during implementation._
