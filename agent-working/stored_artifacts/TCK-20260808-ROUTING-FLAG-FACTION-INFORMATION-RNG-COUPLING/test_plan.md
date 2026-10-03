---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260808-ROUTING-FLAG-FACTION-INFORMATION-RNG-COUPLING
artifact_type: test_plan
tags: [feature-flags, determinism]
---

# Test Plan — TCK-20260808-ROUTING-FLAG-FACTION-INFORMATION-RNG-COUPLING

## Normal flow
- Real controlled before/after comparison (`frontier_marches`, seed 42, 1 tick,
  `ENABLE_ADVENTURE_ROUTING` toggled): `refine()`'s own returned `faction_updates` count and
  content must be identical (58 updates) in both ON and OFF configurations. Verified already
  during investigation — re-verify post-formal-fix landing.
- `AdventureDecisionPhase`'s own routing behavior must be unregressed: heroes must still receive
  real strategic projects across a multi-tick run with routing ON.

## Edge cases
- A tick with NO heroes present (routing phase returns its own empty `StateUpdate()` early) must
  still correctly merge (a no-op merge) rather than error.
- SHADOW-mode `ENABLE_ADVENTURE_ROUTING` (not just ON/OFF) must still correctly discard aspect
  mutations per `run_phase`'s own SHADOW handling, now operating on properly-merged updates instead
  of the bug's raw phase_upd.

## Failure modes
- If `simq_routing_test`/`hero_guild_routing`'s own real recalibration (200/500/1000t, all seeds
  already anchored) shows real ECONOMY-grade drift from this fix, that drift is real signal being
  restored, not a regression — re-verified and re-committed per `corpus_tier_taxonomy.md`'s own
  Regression/baseline-tier drift-handling precedent, not silently left inconsistent with the
  now-fixed engine behavior.

## Regression-prone paths
- Full existing pipeline/movement/combat test suites must still pass — this touches a shared
  pipeline call site every routing-enabled world's tick goes through.

## Scoped test commands
- `pytest tests/unit/movement/ tests/unit/combat/ tests/integration/pipeline/ -q`
- `pytest tests/unit/strategic/ -k routing -q` / any existing `adventure_decision`-specific tests
- Full `tests/simulation_quality/test_grade_regression.py -q` (grade-anchor consistency,
  including the 2 routing-enabled worlds)
