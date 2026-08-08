---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE
artifact_type: test_plan
tags: [simulation-quality, progression]
---

# test_plan.md — TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE

## Regression Surface

- `tests/unit/observability/test_event_extractor_simq.py` / `test_event_extractor_world.py`
  (existing `event_extractor.py` test suites — must still pass unmodified, this ticket only adds
  new code, does not touch any existing branch)
- `tests/simulation_quality/test_progression_scorer.py` (existing `ProgressionScorer` suite —
  must still pass unmodified)

## New Tests Required

- `event_extractor.py`: `capability_growth_stalled` fires after `_CAPABILITY_STALL_TICKS` ticks
  with zero movement on all 4 dimensions; does NOT fire if any one dimension moved (level, skill,
  gear, or gold, tested independently); does not fire twice for the same entity; a
  freshly-first-observed entity (mid-run) does not immediately appear stalled.
- `event_extractor.py`: `life_arc_incoherent` fires when `generation >= 2` and `evolution_level <=
  1` and zero skills; does NOT fire at `generation == 1`; does NOT fire if level > 1 despite
  `generation >= 2`; does not fire twice for the same entity.
- `ProgressionScorer`: `capability_growth_stalled` and `life_arc_incoherent` each score their
  configured weight and tag, using an injected `ScoringWeights` fixture (not production config).

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/unit/observability/test_event_extractor_simq.py \
  tests/unit/observability/test_event_extractor_world.py \
  tests/simulation_quality/test_progression_scorer.py -q
```

## Anti-Drift Test Guards

- Any future change to `EquipmentComponent`/`InventoryComponent`/`LifecycleComponent`'s field
  names must re-verify this ticket's own `getattr(..., default)` reads still resolve correctly —
  they use `getattr` with defaults specifically so a missing/renamed field degrades to "no growth
  detected" rather than raising, but a silent misread (e.g. a renamed field silently returning the
  default forever) would make these rules permanently inert without any test failure — worth a
  periodic real-kernel sanity check (not just unit tests), same caution `test_plan.md` for
  `TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE` established for wiring-gap-class bugs.
