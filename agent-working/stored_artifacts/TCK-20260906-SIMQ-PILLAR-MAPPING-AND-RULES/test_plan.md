---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260906-SIMQ-PILLAR-MAPPING-AND-RULES
artifact_type: test_plan
tags: [simulation-quality, content]
---

# Test Plan — TCK-20260906-SIMQ-PILLAR-MAPPING-AND-RULES

## Regression Surface

- `tests/simulation_quality/` — the full SimQ test suite, especially `test_information_scorer.py`
  (or equivalent) covering `InformationScorer`'s existing 7 event types, must still pass unmodified
  after adding the 8th (`route_new_query`).
- `tests/simulation_quality/test_quality_hub_event_translation.py` — confirms the translation table
  is untouched (this ticket adds no translation entry — `route_new_query` is contract vocabulary
  already, direct emission).
- `tests/tools/test_ci_workflow_test_coverage.py` — confirm no new test directory needs fast-lane
  CI wiring (this ticket adds a test to an existing, already-wired directory).

## New Tests Required (per AC)

- A new test confirming `InformationScorer.score()` returns a real, non-None `ScoreRecord` for a
  `route_new_query` event envelope, with the correct pillar (`PillarId.INFORMATION`), a positive
  delta, and a distinguishing tag — mirroring the exact test shape already used for
  `belief_assimilated`/`belief_stale` in the same test file.
- A test confirming `InformationScorer.EVENT_TYPES` contains `"route_new_query"`.

## Scoped Pytest Commands

```
/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest tests/simulation_quality/ -q
```

## Anti-Drift Test Guards

- Confirm the new test actually imports and exercises the real `InformationScorer` class, not a
  mock — matching this pillar's own existing test file's convention.
- Confirm no existing `test_information_scorer.py` (or equivalent) test's assertion count/order
  changes — only a new test method is added, nothing existing is altered.
