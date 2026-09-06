---
status: active
layer: testing
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260906-AGE-TIER-TIMING-BUG-AND-CORPUS-TEST
date: 2026-09-06
---

# Test Plan: TCK-20260906-AGE-TIER-TIMING-BUG-AND-CORPUS-TEST

## Regression Surface
- `tests/unit/progression/test_lifecycle.py`
- `tests/unit/strategic/test_life_stage_transitions.py`
- `tests/unit/strategic/test_coming_of_age_archetype_choice.py`
- `tests/unit/world/test_demographics.py`
- `tests/simulation_quality/` (broad)

## New Tests Required
- `tests/simulation_quality/test_age_tier_transitions_corpus.py`:
  - `test_young_adult_transition_and_coming_of_age_fire_at_real_threshold`
  - `test_adult_elder_transition_and_elder_attribute_deltas_fire_at_real_threshold`
- `tools/` has no test suite convention (tooling scripts) — the guard is smoke-tested directly by
  invoking `main()`/the guard function with an inadequate `--ticks` value and asserting a warning
  is printed, added to `tests/tools/` if a suitable existing file exists, else a small new one.

## Scoped Pytest Commands
```
.venv/bin/python3 -m pytest tests/simulation_quality/test_age_tier_transitions_corpus.py \
  tests/unit/progression/test_lifecycle.py tests/unit/strategic/test_life_stage_transitions.py \
  tests/unit/strategic/test_coming_of_age_archetype_choice.py tests/unit/world/test_demographics.py \
  tests/tools/ -q
```

## Anti-Drift Test Guards
- The new corpus test must NOT duplicate the exact assertions already in
  `test_lifecycle.py`/`test_coming_of_age_archetype_choice.py` — it adds the multi-entity,
  SimQ-corpus-framed angle (both transitions in one scenario, both roles CITIZEN), not a
  re-verification of what's already proven.
