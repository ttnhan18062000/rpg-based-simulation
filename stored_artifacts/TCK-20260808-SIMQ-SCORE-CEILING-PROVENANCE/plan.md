---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-SIMQ-SCORE-CEILING-PROVENANCE
artifact_type: plan
tags: [simulation-quality, calibration]
---

# Plan — TCK-20260808-SIMQ-SCORE-CEILING-PROVENANCE

## File layout

- `tests/simulation_quality/fixtures/score_ceilings.json` — the provenance data file, sibling to
  `grade_anchors.json`. Two kinds of entries: `corpus_wide` (keyed by pillar only — e.g. COMBAT's
  flag_gated ceiling applies identically to all affected run_keys, one entry not 26 duplicates)
  and `per_run_key` (keyed by `(run_key, pillar)` — for cases that genuinely vary per scenario,
  like tick_budget, which depends on each scenario's own tick count).
- `tools/simq_ceiling.py` — computation module: `tick_budget_ceilings()` (fully computed from
  `detection_params.yaml` + `corpus_registry.yaml`), `lookup_ceiling(run_key, pillar)` (checks
  computed tick_budget results + the static `flag_gated`/`corrected` table +
  `score_ceilings.json`'s manually-curated `content_threshold` entries, in that order).

## Steps

1. `tools/simq_ceiling.py`: `FLAG_GATED_PILLAR_CEILINGS` (hand-verified table, COMBAT entry),
   `tick_budget_ceilings()` (computed from `corpus_registry.yaml` + `detection_params.yaml`),
   `lookup_ceiling(run_key, pillar) -> CeilingInfo | None`.
2. `tests/simulation_quality/fixtures/score_ceilings.json`: `corrected` entry for NARRATIVE.
3. `tests/tools/test_score_ceilings.py`: the 5 tests from test_plan.md.
4. `tests/simulation_quality/test_grade_regression.py`: wire the score-tolerance failure message
   to call `lookup_ceiling` and append the classification if one exists.
5. `docs/simulation_quality/current_state.md`: pointer to the new files.

## Acceptance-criteria map

| AC | Step |
|---|---|
| investigation.md confirms computation sources, designs content_threshold schema | Investigate (done) |
| Provenance file with ceiling_kind distinguishing deterministic vs judgment-call, plus corrected state | Steps 1-2 |
| 3 real cases backfilled (COMBAT flag_gated x26 via corpus-wide entry, NARRATIVE corrected) | Steps 1-2 |
| test_grade_regression.py surfaces classification in failure output | Step 4 |
| Scoped pytest passes | Step 3 |
