---
status: historical
layer: engine
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260817-STANDARD-SPAWN-PLACEMENT-COLLISION-HERO-MONSTER-DIAGONAL
tags: [engine, bug, testing]
---

# Investigation — TCK-20260817-STANDARD-SPAWN-PLACEMENT-COLLISION-HERO-MONSTER-DIAGONAL

## Failing tests
Real CI failure, "API / tools / logging" job:
`tests/observability/test_metrics_export.py::test_metrics_endpoint_direct[asyncio]` and
`::test_multiple_registries_prevent_collision` — both raise
`HardLawViolationError: [ERROR] LAW-SPAWN-OCCUPANCY on entity 1: Initial placement collision on
tile (64, 64): entity 1 and entity 6 both occupy this space.`

## Root cause (real production bug, not test-fixture scope)
`src/api/engine_manager.py::V2EngineManager._build()` places the hero at a fixed `(64.0, 64.0)`
and monsters along a diagonal `(60.0 + i, 60.0 + i)` for `i in range(entities_count - 1)`. With
the default `entities_count=10` (both this class's own default and `src/api/server.py`'s real
startup call site — `create_v2_app`/lifespan), `i=4` produces `(64.0, 64.0)`, landing exactly on
the hero's tile. Entity IDs land as hero=1, 5th monster=6, matching the CI error text verbatim.

This is not test-fixture-only scope, unlike the precedent ticket
`TCK-20260807-SCALE-VALIDATION-ENTITY-COLLISION-BUG` (a test file placing 100 entities at one
literal coordinate) — `V2EngineManager` is real production code, reachable from the real server
bootstrap path with the exact default that triggers the collision.

`_run_initial_placement_check` (`src/engine/kernel.py`) — the check that catches this — was newly
added by commit `29d78798` and is the first check to ever inspect the full compiled spawn state;
it correctly caught a pre-existing latent collision that was previously invisible.

## Compounding factor: a test-isolation leak made this a hard failure, not a warning
Whether `_run_initial_placement_check` raises vs. only logs depends on
`ObservabilityConfig.get_mode()` (default `LIGHT` = warn-only). `tests/engine/test_hard_law_monitor.py::test_observability_modes_and_kernel_integration`
sets a `DEBUG` mode override (`ObservabilityConfig.set_override_mode`) and never reset it — no
`finally`, no teardown. `ObservabilityConfig._override_mode` is class-level global state, so the
override survives across the rest of the same pytest process. CI's "API / tools / logging" job
runs `pytest tests/api tests/cli tests/tools tests/logging tests/engine tests/observability -m
"not slow"` in one process — `tests/engine` collects before `tests/observability`, so the leaked
`DEBUG` override flips the two `test_metrics_export.py` tests from "would warn" to "raises".

Reproduced deterministically: `test_metrics_export.py` alone passes (mode defaults to `LIGHT`);
running `tests/engine/test_hard_law_monitor.py tests/observability/test_metrics_export.py`
together reproduces the exact CI failure text 100% of the time.

## Verification
- `pytest tests/observability/test_metrics_export.py -q` alone: 5 passed (collision present but
  silent under default `LIGHT` mode — confirms the collision itself is real but was previously
  masked).
- `pytest tests/engine/test_hard_law_monitor.py tests/observability/test_metrics_export.py -q`:
  reproduced the exact CI failure before the fix.
- No `docs/mechanics/` or `docs/parity_ledger/` entry references `LAW-SPAWN-OCCUPANCY` or this
  specific spawn-placement pattern (verified via grep) — this is scaffolding/demo bootstrap code,
  not a documented mechanic, so no Mechanics Bible/parity ledger update is required.
