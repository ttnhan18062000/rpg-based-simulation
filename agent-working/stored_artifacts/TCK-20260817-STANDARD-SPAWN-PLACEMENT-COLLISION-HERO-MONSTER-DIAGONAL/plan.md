---
status: historical
layer: engine
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260817-STANDARD-SPAWN-PLACEMENT-COLLISION-HERO-MONSTER-DIAGONAL
tags: [engine, bug, testing]
---

# Plan — TCK-20260817-STANDARD-SPAWN-PLACEMENT-COLLISION-HERO-MONSTER-DIAGONAL

## Two independent fixes, one ticket (both required, neither alone is sufficient)

### 1. `src/api/engine_manager.py::V2EngineManager._build()`
Real production bug: the diagonal monster-placement loop can land exactly on the hero's fixed
spawn tile. Fix: skip any diagonal offset whose integer-truncated tile equals the hero's tile
(matching `LAW-SPAWN-OCCUPANCY`'s own `int(x)/int(y)` collision granularity, per the
`TCK-20260807-SCALE-VALIDATION-ENTITY-COLLISION-BUG` precedent — traced from the real check, not
assumed), continuing the diagonal afterward so entity count and visual pattern are otherwise
unchanged. General for any `entities_count`, not just the default 10.

### 2. `tests/engine/test_hard_law_monitor.py::test_observability_modes_and_kernel_integration`
Test-isolation bug: this test sets `ObservabilityConfig`'s class-level global override mode to
`DEBUG` and never resets it. Fix: `request.addfinalizer(ObservabilityConfig.clear_all_overrides)`
at the top of the test, using the dedicated reset classmethod already provided by
`ObservabilityConfig` for exactly this purpose.

## Why both are needed
Fix 1 alone removes the specific collision this session found, but the underlying test-isolation
bug remains latent — any other real, order-dependent interaction between a global-mode-setting
test and a hard-law check test would resurface the same class of flake. Fix 2 alone would leave a
real, reachable production bug (real server bootstrap default triggers a hard-law violation) live,
merely making it silent again under `LIGHT` mode rather than actually correct.

## Out of scope
- Any other ticket in this batch.
- `_run_initial_placement_check`/`HardLawMonitor.check_initial_placement` themselves — confirmed
  correctly implemented and correctly newly catching a real, pre-existing bug; not touched.
- No Mechanics Bible/parity ledger entry references this spawn pattern (verified via grep) — none
  needs updating.
