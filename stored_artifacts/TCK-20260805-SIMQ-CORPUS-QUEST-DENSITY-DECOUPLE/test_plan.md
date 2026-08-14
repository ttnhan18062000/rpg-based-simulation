---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260805-SIMQ-CORPUS-QUEST-DENSITY-DECOUPLE
artifact_type: test_plan
tags: [simulation-quality, world, progression, corpus, calibration]
---

# test_plan.md — TCK-20260805-SIMQ-CORPUS-QUEST-DENSITY-DECOUPLE

## Regression Surface (existing tests that must pass)

- `tests/simulation_quality/test_grade_regression.py -m "not slow"` — all existing anchors must
  remain unaffected by the 3 new `quest_dense_frontier` entries.

## New Tests Required (per AC)

- 3 new anchor entries in `grade_anchors.json` (`quest_dense_frontier_seed{42,123,456}_200t`).
- `FAST_ANCHOR_KEYS` extended with the 3 new run keys.
- `test_grade_anchors_entry_count_unchanged` updated (76 → 79).

## Scoped Pytest Commands

```
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q
```

## Anti-Drift Test Guards

The 3 new anchors are real, live-engine-calibrated values (not synthetic), matching the corpus's
existing anchor-authoring convention (3 seeds, 200t, for a new stress-tier world).
