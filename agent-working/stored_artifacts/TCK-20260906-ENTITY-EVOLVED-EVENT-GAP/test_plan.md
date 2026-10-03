---
status: active
layer: simulation
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260906-ENTITY-EVOLVED-EVENT-GAP
date: 2026-09-06
---

# Test Plan: TCK-20260906-ENTITY-EVOLVED-EVENT-GAP

## Regression Surface
- `tests/unit/observability/` (event_shapers/event_extractor suites) — must stay 100% passing;
  updated shared mock helpers (`_entity()`/`_entity_update()` in
  `test_event_shapers_progression.py`) must not change any existing test's behavior.
- `tests/simulation_quality/test_progression_scorer.py` — must stay 100% passing.
- `tests/unit/progression/test_evolution.py` — must stay 100% passing; new test reuses the real
  `EvolutionSystem.evaluate()` path already exercised there.

## New Tests Required (per AC)
- AC1 (event fires on the real transition): `test_entity_evolved` (ProgressionShaper, mock-level),
  `test_entity_evolved_emitted_on_kind_change` (EventExtractor rollback path, mock-level), and
  `test_goblin_evolution_emits_entity_evolved_observability_event` (real
  `EvolutionSystem.evaluate()` output wired into the real `ProgressionShaper` — the actual
  end-to-end proof, not just a hand-built mock).
- Negative path (regression-catching, not tautological): `test_entity_evolved_not_emitted_when_kind_unchanged`
  in both the shaper and extractor test files.
- AC2 (registered with SimQ): `TestEntityEvolved::test_species_evolution` in
  `test_progression_scorer.py`.

## Scoped Pytest Commands
```
pytest tests/unit/observability/ tests/simulation_quality/ tests/unit/progression/ -q
```

## Anti-Drift Test Guards
- The negative-path tests must genuinely construct a `kind_set == prior kind` case (not merely omit
  a field) — proves the diff-based detection, not a bare non-None check.
- The real-`EvolutionSystem` integration test must NOT hand-construct a fake `kind_set` — it must
  come from the real `EvolutionSystem.evaluate()` call, otherwise it does not actually prove the two
  independently-built systems (evolution mechanic, observability layer) connect correctly.
