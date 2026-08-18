---
status: historical
layer: simulation
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260817-STANDARD-SIMQ-NARRATIVE-ANCHOR-RECALIBRATION-FRONTIER-BATCH
tags: [simulation-quality, calibration, testing, bug]
---

# Plan — TCK-20260817-STANDARD-SIMQ-NARRATIVE-ANCHOR-RECALIBRATION-FRONTIER-BATCH

## Approach
1. Edit only the `NARRATIVE` entry in each of the 5 tests' `anchors = {...}` dicts to
   `{"grade": "C", "score": 0.0, "abs_floor": 0.05}`.
2. For `frontier_marches_seed42_200t`, also trim the now-superseded session-position-sensitivity
   docstring paragraph and replace it with a pointer to the current explanation.
3. Edit the co-discovered `COMBAT` entry in test 1 to `{"grade": "A", "score": 0.7368,
   "abs_floor": 0.679}`.
4. Verify all 5 individually; re-verify test 1 across 3 consecutive isolated runs given it now has
   two recalibrated anchors.

## Scope guards
- No `src/` change.
- No change to `grade_anchors.json` (per the referenced investigation's own finding, these 5
  anchors live only in `test_corpus_diversity.py`'s own local dicts).
- No change to any other pillar's anchor in any of the 5 tests.
- Any `git worktree` used for the causality check is removed before this ticket closes.

## Acceptance-criteria map
| AC | How satisfied |
|---|---|
| NARRATIVE traced to real evidence | Referenced investigation ticket's own evidence |
| COMBAT traced to real evidence | investigation.md's 3-trial fresh dataset |
| Only NARRATIVE (+COMBAT in test 1) changed | `git diff` review |
| All 5 pass reliably | test_plan.md |
| COMBAT confirmed pre-existing, not caused by spawn-collision fix | investigation.md's worktree check |
| No `src/` change | `git diff --stat` scoped to `tests/` only |
