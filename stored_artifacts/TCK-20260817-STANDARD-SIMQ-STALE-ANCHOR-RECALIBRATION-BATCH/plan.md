---
status: historical
layer: simulation
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260817-STANDARD-SIMQ-STALE-ANCHOR-RECALIBRATION-BATCH
tags: [simulation-quality, calibration, testing, bug]
---

# Plan — TCK-20260817-STANDARD-SIMQ-STALE-ANCHOR-RECALIBRATION-BATCH

## Approach
Straight recalibration, no source-code change. For each of the 4 tests, edit only the
`anchors = {...}` dict literal in `tests/unit/worldassembly/test_corpus_diversity.py`:

1. `test_urban_political_seed42_200t_social_grade_stability` — SOCIAL score `7.525` → `16.815`
   (synced from `grade_anchors.json`), `abs_floor` `1.5275` → `4.225`.
2. `test_urban_political_selfmodel_probe_seed42_200t_social_world_grade_stability` — SOCIAL score
   `7.525` → `17.895` (synced from `grade_anchors.json`), `abs_floor` `0.546` → `7.579`. WORLD
   anchor untouched (already passing).
3. `test_frontier_living_world_seed42_200t_social_grade_stability` — SOCIAL score `4.9625` →
   `33.7` (synced from `grade_anchors.json`), `abs_floor` `1.0757` → `5.382`.
4. `test_unit_selfmodel_pilot_seed42_1000t_cognition_economy_narrative_grade_stability` —
   NARRATIVE score `0.3715` → `0.0`, `abs_floor` `0.0908` → `0.05`. Grade kept at `B` (score 0.0
   sits exactly on the S/A/B/C threshold table's B boundary,
   `src/simulation_quality/pillars.py:85-91`; already within the existing anchor's ±1 band, no
   band-check change needed). COGNITION/ECONOMY anchors untouched (already passing).

Each edit gets an inline comment above the changed dict entry citing this ticket ID and a
one-line rationale, so a future reader hitting this anchor again doesn't have to re-derive the
history.

## Scope guards
- No change to any `src/` file — all 4 root causes are confirmed test-side staleness, not code
  regressions.
- No change to `tests/simulation_quality/fixtures/grade_anchors.json` — Tests 1–3's target values
  are read from it (already correct there), and Test 4's fixture entry is deliberately left
  untouched per the investigation's Out of Scope (unverifiable without regenerating a
  non-git-tracked calibration snapshot).
- No change to any other test in the file — the other 6 failing tests belong to sibling tickets.

## Acceptance-criteria map
| AC | How satisfied |
|---|---|
| New anchor causally traced before changing | investigation.md per-test root-cause sections, each citing a same-commit fixture or a specific closed ticket |
| Fresh abs_floor derived from real data | Computed directly from investigation.md's measured trial samples using the file's own `1.3x max deviation, floor 0.05` rule |
| All 4 tests pass individually | Verified in Test Summary (test_plan.md) |
| No `src/` change | `git diff --stat` limited to `tests/unit/worldassembly/test_corpus_diversity.py` only |

## Rollout / verification order
1. Apply all 4 edits.
2. Run each of the 4 tests individually (`pytest <nodeid> -m slow --resource-budget large -q`) —
   isolated, not concurrently, to avoid the documented session-load-flake confounder.
3. If any test still fails after isolated re-run, re-open investigation for that specific test
   rather than widening its tolerance further (a widening loop without new evidence would be
   editing the artifact to make the gate pass, prohibited by this repo's hard rules).
