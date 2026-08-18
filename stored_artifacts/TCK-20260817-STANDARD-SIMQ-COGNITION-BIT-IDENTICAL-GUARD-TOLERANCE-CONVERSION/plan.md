---
status: historical
layer: simulation
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260817-STANDARD-SIMQ-COGNITION-BIT-IDENTICAL-GUARD-TOLERANCE-CONVERSION
tags: [simulation-quality, calibration, testing, bug]
---

# Plan — TCK-20260817-STANDARD-SIMQ-COGNITION-BIT-IDENTICAL-GUARD-TOLERANCE-CONVERSION

## Approach
1. Replace `test_urban_political_seed123_500t_cognition_bit_identical_under_load` (idle-vs-load
   equality assertion) with `test_urban_political_seed123_500t_cognition_grade_stability`
   (3-trial band+score-tolerance guard), dropping the now-unnecessary multiprocessing busy-loop
   machinery since plain reruns already exhibit the bimodal behavior.
2. Use anchor `{"grade": "S", "score": 3.536, "abs_floor": 4.482, "band_tolerance": 2}`, calling
   `_within_band(snap.grade, anchor["grade"], tolerance=anchor["band_tolerance"])` explicitly at
   this one call site rather than changing `_within_band`'s own default.
3. Fix the 11 sibling docstrings in the same file that named the old test as an illustrative
   "bit-identical shape" example — rephrase to describe the pattern without a dangling reference.
4. Append a new dated section to `docs/simulation_quality/eval_matrix_results.md` (never rewrite
   the original `## COGNITION Loop-Detection Nondeterminism Verification` section — it's an
   accurate historical record of what was true in 2026-07).
5. Do not implement the dedup-gate source fix — document the investigation and recommendation in
   the ticket's Out of Scope / Implementation Notes instead.
6. Investigate (read-only, isolated `git worktree`, no changes to the shared working tree) the
   `3d992dd0` compounding-factor lead; document findings whether conclusive or not.

## Scope guards
- No change to any `src/` file.
- No change to `_within_band`'s or `_within_score_tolerance`'s default parameter values.
- No change to `docs/guidelines/intentional_divergences.md`'s F6 entry (explicitly protected by
  the establishing ticket's precedent).
- No change to any other test in the file besides the docstring cross-reference fixes.
- Any `git worktree` used for the bisect investigation is removed before this ticket closes —
  never left behind, never allowed to interfere with the shared working tree's other concurrent
  session.

## Acceptance-criteria map
| AC | How satisfied |
|---|---|
| New anchor/tolerance traced to real evidence | investigation.md's 10-trial dataset |
| `_within_band` default unchanged | `test_within_band_default_tolerance_unchanged` still passes (verified in test_plan.md) |
| New test passes | test_plan.md |
| No stale cross-references | `grep` check in test_plan.md |
| eval_matrix_results.md updated (appended) | New dated section, old section untouched |
| No `src/` change | `git diff --stat` scoped to `tests/` and `docs/` only |
