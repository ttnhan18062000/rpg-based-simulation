---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261030-CORPUS-GRADE-GUARD-AVERAGES-A-NO-DATA-SCORE
phase: done
date: 2026-10-30
tags: [simulation-quality, regression]
---

# TCK-20261030-CORPUS-GRADE-GUARD-AVERAGES-A-NO-DATA-SCORE

## Title
The urban_political seed123 500t COGNITION grade guard averages a None score when its anchor is no-data, and crashes with a TypeError. Average only when the score tolerance applies.

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`tests/unit/worldassembly/test_corpus_diversity.py::test_urban_political_seed123_500t_cognition_grade_stability` fails on main de5a223ca. codebase-implementer's log (`/data/vboxuser/tmp/ee/cd_clean.out`, a clean archive of de5a223ca, relayed by codebase-planner on 2026-10-30) shows:

```
tests/unit/worldassembly/test_corpus_diversity.py:680
>       mean_score = sum(trial_scores) / n_trials
E       TypeError: unsupported operand type(s) for +: 'int' and 'NoneType'
```

The cause is in the test, not the simulation:
- #747 (cb4f95015) re-anchored `urban_political_seed123_500t/COGNITION` from `{grade B, score 0.024}` to `{status no-data, reason below_min_events, min_events 3}`.
- The band assertion at line 675 comes before the mean, and it did NOT fire. So `_snap_failure` found the live pillar no-data with the same `min_events`, which matches the anchor.
- A no-data pillar has `normalized_score None`. The test then does `sum(trial_scores)` unconditionally (line 680), before `_score_applies(anchor)` is consulted (line 681).
- So the test has crashed on every run since #747, whatever the simulation does. The live COGNITION status matches its anchor.

rpg-planner-ubuntu checked the other score-mean sites in the same file. The only other no-data anchors the file reads (`simq_routing_test_seed42_500t`, `simq_routing_test_seed42_1000t`, `sandbox_world_seed42_200t` COGNITION) are read by tests that don't average. The multi-pillar guards (lines ~866, 977, 1095, 1185, 1290, 1378, 1489) have the same unguarded pattern, and would crash the same way if any of their pillars were re-anchored to no-data.

## Scope
1. At line 680, compute `mean_score` only when `_score_applies(anchor)` is true. Short-circuit the existing assertion so the mean is never computed for a no-data anchor.
2. Apply the same guard to every per-pillar `mean_score = sum(trial_scores[pillar]) / n_trials` site in the file: compute it only when `_score_applies(targets[pillar])` (or that test's own anchor variable). Leave assertions, anchors, tolerances and band values unchanged.
3. Add a small unit test in the same file, or in `tests/unit/tools/` if that's where the comparison helpers are tested. It feeds a no-data anchor and a no-data live pillar through the same mean/score path and shows that the path passes without computing a mean. Positive control: the old code shape raises TypeError on the same input.

## Out of Scope
- Any anchor value, tolerance or band change.
- `test_urban_political_selfmodel_probe_seed42_200t_social_world_grade_stability` (a real WORLD drift, 0.25 vs 0.32). That is TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT.
- `hero_guild_routing_seed42_1000t` (held-rows ticket).
- Any src change.

## Acceptance Criteria
1. `test_urban_political_seed123_500t_cognition_grade_stability` passes on current main. It's one 500-tick audit_mode run, so it's light enough to need no heavy slot; ask rpg-planner-ubuntu if a quiet window is in force. If it fails on a status/band assertion instead, STOP and report: that would be a real drift.
2. Every score-mean site in the file is guarded by `_score_applies`. A `grep -n "sum(trial_scores" tests/unit/worldassembly/test_corpus_diversity.py` listing in the ticket shows each one.
3. The new unit test passes. The positive control is shown.
4. `pytest tests/unit/worldassembly/test_corpus_diversity.py -m "not slow"` passes, and the slow test above passes once.
5. If a `slow_known_reds.yaml` entry was added for this test in the meantime, this ticket removes it. (rpg-planner ruled (b): none is added.)
6. No silent pass (rpg-planner's condition, 2026-10-30): at all 8 sites, an applicability mismatch between live and anchor still FAILS, with a clear message. That covers both a live score against a no-data anchor, and a no-data live pillar against a scored anchor. Only the both-no-data case skips the mean. Add a unit case for each direction alongside the TypeError positive control. If `_snap_failure`, which `compare_pillar` calls before the mean (the assertion at :675 for this test), already fails both directions at every site, cite the line and the case instead of adding a new check. Confirm that each of the 8 sites asserts its band/status failures before it computes the mean.

## Related Tickets
- TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT (test 3; separate)
- TCK-20261014-SIMQ-SINGLE-REANCHOR-ON-BASELINE-V1 (#747, which made this anchor no-data)

## Related Docs
- none

## Related Stored Artifacts
- none

## Related Code Areas
- tests/unit/worldassembly/test_corpus_diversity.py

## Assumptions / Open Questions
- Dispatch is under S4 (#715 6473439661). rpg-planner OK'd the plan on 2026-10-30, relayed via lead-planner-u24 and lead-planner, adding AC6. It changes no expectation, only a crash before the expectation is checked.
- Ownership: `test_corpus_diversity.py` is rpg-domain (rpg-planner, 2026-10-30).

## Implementation Notes
- New helper `_mean_score(target, scores, n_trials)` returns the mean only when `_score_applies(target)`, else `None`. All 12 mean sites use it: the 500t COGNITION guard (`:687`) and 11 per-pillar guards (`:873, 984, 1102, 1192, 1297, 1385, 1496, 1587, 1698, 1788, 1884`). The ticket text said 7 per-pillar sites; the file has 11. Each per-pillar site now reads `mean_score = _mean_score(...)` then `if mean_score is not None and not _within_score_tolerance(...)`; the 500t site asserts `mean_score is None or _within_score_tolerance(...)`. Anchors, tolerances, bands and messages are unchanged.
- AC6: a live/anchor applicability mismatch cannot reach the mean because every one of the 12 sites asserts `not band_failures` (from `_snap_failure` -> `compare_pillar`) before it takes the mean (checked by line: the band assertion precedes the mean by 5 lines at `:682/:687` and 7 lines at each of the other 11). `_snap_failure` fails both directions: scored anchor with a no-data live pillar ("lost its data") and no-data anchor with a scored live pillar ("gained data"), plus a changed `min_events`. Existing case `test_snap_failure_four_way_on_hub_snapshots` covers both; the new `test_a_status_mismatch_between_live_and_anchor_still_fails_before_any_mean_is_taken` states each direction on its own and that only both-no-data passes.
- No `slow_known_reds.yaml` entry (ruling b).

## Test Summary
- `pytest tests/unit/worldassembly/test_corpus_diversity.py -m "not slow"`: 65 passed, 32 deselected.
- New tests: `test_mean_score_is_computed_only_where_the_score_tolerance_applies` (includes the positive control: the old shape `sum([None]) / 1` raises TypeError) and the two-direction mismatch test above.
- `test_urban_political_seed123_500t_cognition_grade_stability` (slow, one 500t audit_mode run, `urban_political` seed 123): passed once (49 s, 2026-10-30 about 15:54 +07). The run dir it wrote (`data/runs/urban_political_123_500_1122998_c86444a1`) was cleaned by run id.

## Files Changed
- `tests/unit/worldassembly/test_corpus_diversity.py`

## Completion Summary
The guard crashed with a TypeError whenever its anchor was no-data, whatever the simulation did. The mean is now taken only where the score tolerance applies, at all 12 sites, with no change to any anchor, tolerance or band. A status mismatch in either direction still fails earlier, and both directions have a unit case. The slow guard passes on current main with the fix (live COGNITION no-data with the same `min_events` as its anchor).
