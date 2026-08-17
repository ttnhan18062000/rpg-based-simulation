---
status: historical
layer: engine
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260817-STANDARD-SPAWN-PLACEMENT-COLLISION-HERO-MONSTER-DIAGONAL
tags: [engine, bug, testing]
---

# Test Plan — TCK-20260817-STANDARD-SPAWN-PLACEMENT-COLLISION-HERO-MONSTER-DIAGONAL

## Normal flow
- `pytest tests/engine/test_hard_law_monitor.py tests/observability/test_metrics_export.py -q` —
  the exact combined scope that reproduced the CI failure — must pass.
- `pytest tests/api tests/cli tests/tools tests/logging tests/engine tests/observability -m "not
  slow" -q` — the real, full CI "API / tools / logging" job invocation — must show no failures
  attributable to this bug.

## Regression check
- `V2EngineManager` with the default `entities_count=10` (both the class default and
  `src/api/server.py`'s real call site) no longer raises/warns `LAW-SPAWN-OCCUPANCY` on
  construction.
- Monster count is unchanged (`entities_count - 1` monsters are always placed, regardless of the
  skip) — verified by construction not raising and entity dict size matching expectation.

## Edge case
- The fix must generalize beyond `entities_count=10` — verified by the fix's own loop structure
  (skip-and-continue on any offset landing on the hero's tile), not a special-cased check for the
  one observed collision.

## Failure mode covered
- Test-isolation: confirms `test_observability_modes_and_kernel_integration`'s `DEBUG` override no
  longer leaks into `test_metrics_export.py` when run in the same pytest process, by running them
  together (previously reproduced the failure; now passes).

## Results
- `pytest tests/engine/test_hard_law_monitor.py tests/observability/test_metrics_export.py -q`:
  17 passed.
- `pytest tests/api tests/cli tests/tools tests/logging tests/engine tests/observability -m "not
  slow" -q`: see ticket's Test Summary for full count.
