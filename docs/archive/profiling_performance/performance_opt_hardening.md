---
status: archive
authority: P2
audience: historical
layer: performance
original_date: unknown
---

RevoZ
revoz_r06
ogu

RevoZ [GDev],  — 04/05/2026 5:30 CH
## Summary

I parsed the uploaded dependency graph as a directed dependency graph using `source -> target` even though the JSON marks the graph as `directed: false`, because the edges contain dependency semantics such as `uses`, `calls`, `imports_from`, and `inherits`.

High-level result: the structure is not cyclic at node level, but it has several serious architecture concentration problems. The codebase is structurally centered around a few giant core models and update objects: `AuthoritativeState`, `EntityState`, `StateUpdate`, and `EntityUpdate`. That is the main architectural risk.

resource_v2_graph_review.md
18 KB
RevoZ [GDev],  — 06/05/2026 9:48 CH
from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set

from src.core.state import (

message.txt
29 KB
RevoZ [GDev],  — 06/05/2026 9:56 CH
#!/usr/bin/env python3
"""
Codemod tests from old V2EntityBuilder API to fresh builder API.

Dry-run by default.
Use --write to modify files.

message.txt
7 KB
RevoZ [GDev],  — 06/05/2026 10:16 CH
#!/usr/bin/env python3
"""
Conservative codemod for migrating old V2EntityBuilder test usage to the fresh builder API.

It rewrites only builder chains that are proven to be rooted at:
- V2EntityBuilder(...)

message.txt
11 KB
RevoZ [GDev],  — 12/05/2026 1:31 SA
# 1. Performance testing goals

The engine performance test should answer these questions:

```text
1. How many entities can the engine support under different workloads?

performance_implementation.md
33 KB
RevoZ [GDev],  — 13/05/2026 12:04 SA
# Engine Performance Improvement Plan

Goal:

```text
Improve large-entity performance without breaking the correctness-first architecture.

optimization_implementation.md
23 KB
# Real-world scenarios when profile resources hit limits

Current design is basically:

```text
PressureSignals

performance_scenarios.md
15 KB
Using the latest design pattern in your uploaded source, the current solution is:

```text
resource pressure signal
→ ResourceGovernor evaluates against RuntimeProfile limits
→ RuntimeStatus changes operational mode

resource_signal_current.md
10 KB
#!/usr/bin/env python3

from pathlib import Path
import re
import sys

split_milestone.py
2 KB
RevoZ [GDev],  — 13/05/2026 5:26 CH
Yes. Python profiling is exactly what you should add before deciding optimization.

Use profiling in this order:

```text
1. cProfile / pstats

profiling.md
13 KB
Using the current/latest engine design, the tick processing model is basically:

```text
Kernel.tick_once()
  ├─ INIT
  ├─ SCHEDULING

current_engine_process.md
18 KB
# Goal

Increase TPS by scaling engine execution in two directions:

```text
1. Asynchronous execution inside one engine instance

optimization_implementation_worker.md
21 KB
RevoZ [GDev],  — 15/05/2026 12:56 SA
## Implementation Plan — Optimization & Profiling Hardening

Core rule:

```text
Do not add more optimization until measurement correctness and DirtySet correctness are proven.

message.txt
31 KB
RevoZ [GDev],  — 15/05/2026 5:08 CH
## Verification result: **not accepted yet**

I split the updated aggregate files into a runnable project under:

```text id="qc2mvv"
/mnt/data/rpg_verify

message.txt
13 KB
RevoZ [GDev],  — 4:00 CH
# Improvement Implementation Plan — Performance Optimization Hardening

Use this order. Do **not** reorder it. The biggest remaining risk is that the benchmark/profiler is now mostly honest, but the “reference truth path” is still incomplete because `force_full_scan` is not respected everywhere.

---

message.txt
18 KB
﻿
# Improvement Implementation Plan — Performance Optimization Hardening

Use this order. Do **not** reorder it. The biggest remaining risk is that the benchmark/profiler is now mostly honest, but the “reference truth path” is still incomplete because `force_full_scan` is not respected everywhere.

---

# Milestone 1 — Fix `force_full_scan` as a real reference path

## Goal

Make full-scan mode truly process all relevant entities, regardless of DirtySet.

Right now, `_refresh_dirty_set()` knows about `force_full_scan`, but some phases still read `dirty_set` directly and narrow processing incorrectly. The interaction routing path is the key example: it uses DirtySet movement/strategic IDs instead of honoring full-scan mode.  

## Tasks

| Task ID | Task                                              | Implementation logic                                                                                             | Acceptance criteria                                                                       |
| ------- | ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| M1.1    | Audit all DirtySet consumers                      | Search for all direct usages of `update.dirty_set` in systems/phases.                                            | Every consumer is listed in a small audit table.                                          |
| M1.2    | Fix `InteractionPhase.route_interaction_intent()` | If `update.force_full_scan is True`, use `state.entities.keys()` instead of DirtySet IDs.                        | Full-scan interaction test passes.                                                        |
| M1.3    | Add shared helper                                 | Create helper like `get_relevant_entity_ids(state, update, domains)` to avoid repeated incorrect DirtySet logic. | Interaction, strategic, group, shop, capacity phases use helper or equivalent safe logic. |
| M1.4    | Add regression test                               | Test entity with valid navigation target + empty DirtySet + `force_full_scan=True`.                              | Interaction update is generated.                                                          |
| M1.5    | Add audit-mode assertion                          | In audit mode, compare full-scan candidate IDs vs optimized candidate IDs where practical.                       | Audit failure happens if optimized path skips required candidate.                         |

## Required test

```python
def test_force_full_scan_interaction_phase_processes_all_entities():
    """
    Law:
        force_full_scan must ignore DirtySet narrowing.

    Fraud this catches:
        - full-scan reference path is not really full scan
        - interaction routing silently skips entities with existing targets
        - O(Dirty) parity tests compare against an incomplete reference
    """
```

## Done means

```text
[ ] force_full_scan is honored by interaction routing.
[ ] force_full_scan behavior is tested with empty DirtySet.
[ ] Every direct DirtySet consumer is audited.
[ ] O(Dirty) vs O(N) parity tests use a real O(N) reference path.
```

---

# Milestone 2 — Move runtime budget enforcement after final tick cost

## Goal

Make runtime budget/degradation decisions use the complete tick cost, not partial tick cost.

Profiler reporting is fixed: `Kernel.tick_once()` now includes persistence and final phase accounting.  But budget enforcement still happens too early, before the final compute total is assigned.

## Tasks

| Task ID | Task                                  | Implementation logic                                                               | Acceptance criteria                                                   |
| ------- | ------------------------------------- | ---------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| M2.1    | Locate budget enforcement             | Find where `max_tick_budget_ms` or `_final_compute_ms` is checked.                 | Exact enforcement location identified.                                |
| M2.2    | Move enforcement after full phase sum | Run budget check after `self._final_compute_ms = sum(self._phase_costs.values())`. | Budget check sees final tick cost.                                    |
| M2.3    | Add over-budget synthetic test        | Create profile with very low tick budget and workload with measurable cost.        | Kernel records/handles budget violation based on final cost.          |
| M2.4    | Verify persistence-heavy case         | Add/force a tick where persistence cost pushes total over budget.                  | Budget enforcement detects violation only after persistence included. |

## Required test

```python
def test_budget_enforcement_uses_final_tick_compute_cost():
    """
    Law:
        Runtime budget enforcement must use complete tick cost,
        including persistence and final integrity.

    Fraud this catches:
        - budget check runs before final phase accounting
        - expensive persistence/final-integrity cost is ignored
    """
```

## Done means

```text
[ ] Budget enforcement uses final phase-summed tick cost.
[ ] Persistence/final-integrity cost can trigger over-budget behavior.
[ ] Profiler reporting and runtime governance use the same compute definition.
```

---

# Milestone 3 — Remove hot-path `print()` calls

## Goal

Remove benchmark pollution and hot-path I/O overhead.

There are still `print()` calls inside performance-sensitive engine/system code, including final-integrity breakdown and intelligence debug output. Hot-path prints pollute timing and benchmark output. 

## Tasks

| Task ID | Task                       | Implementation logic                                               | Acceptance criteria                        |
| ------- | -------------------------- | ------------------------------------------------------------------ | ------------------------------------------ |
| M3.1    | Search hot-path prints     | Search `print(` under `src/engine`, `src/systems`, `src/ai`.       | All hot-path print locations listed.       |
| M3.2    | Replace with logger        | Use `logger.debug(...)`, not `print(...)`.                         | No hot-path `print()` remains.             |
| M3.3    | Add perf debug flag        | Only emit phase breakdown if `perf_debug_enabled` or `audit_mode`. | Normal benchmark output is clean.          |
| M3.4    | Add test preventing prints | Add static test scanning forbidden paths for `print(`.             | Test fails if new hot-path print is added. |

## Required test

```python
def test_no_hot_path_prints_in_engine_or_systems():
    """
    Law:
        Engine hot paths must not use print(), because print() pollutes
        benchmark timing and CI logs.

    Allowed:
        tests
        scripts
        CLI-only modules
    """
```

## Done means

```text
[ ] No print() in engine hot path.
[ ] Debug output is logger-based and flag-gated.
[ ] Benchmark output is clean.
```

---

# Milestone 4 — Make API snapshot performance tests CI-safe

## Goal

Separate CI smoke tests from manual heavy benchmarks.

The current API snapshot perf test compares `deepcopy`, `to_readonly`, minimal presenter, and full presenter at large entity counts. The 5,000-entity case is too heavy for normal CI and can time out. 

## Tasks

| Task ID | Task                          | Implementation logic                                                       | Acceptance criteria                                      |
| ------- | ----------------------------- | -------------------------------------------------------------------------- | -------------------------------------------------------- |
| M4.1    | Split smoke vs slow tests     | Keep 100 and 1,000 entities in CI. Move 5,000 to `@pytest.mark.slow`.      | Normal CI avoids 5,000 deepcopy test.                    |
| M4.2    | Remove 5,000 deepcopy from CI | Either skip deepcopy at 5,000 or move to manual benchmark script.          | No normal test does 20 samples of 5,000-entity deepcopy. |
| M4.3    | Add strict smoke thresholds   | Assert minimal presenter is O(1)-like and full presenter is bounded.       | Smoke tests fail on major regression.                    |
| M4.4    | Add manual benchmark command  | Example: `pytest -m "perf and slow" tests/perf/test_api_snapshot_perf.py`. | Heavy benchmark remains available manually.              |

## Suggested structure

```text
tests/perf/test_api_snapshot_perf.py
    CI-safe 100/1000 tests

tests/perf/slow/test_api_snapshot_deepcopy_5000.py
    manual slow benchmark
```

## Done means

```text
[ ] CI test runtime is predictable.
[ ] 5,000-entity snapshot benchmark is still available manually.
[ ] Minimal snapshot remains proven cheap.
[ ] Full snapshot has an explicit threshold.
```

---

# Milestone 5 — Turn passive scaling from report into real test

## Goal

Stop pretending printed metrics are tests.

A test with no assertion is not a test. It is a benchmark report.

## Tasks

| Task ID | Task                      | Implementation logic                                           | Acceptance criteria                           |
| ------- | ------------------------- | -------------------------------------------------------------- | --------------------------------------------- |
| M5.1    | Add compute threshold     | Assert `p95_tick_compute_ms` below profile-specific limit.     | Test fails on tick-time regression.           |
| M5.2    | Add memory threshold      | Assert peak RSS / memory delta below limit.                    | Test fails on memory growth.                  |
| M5.3    | Add compute TPS threshold | Assert `compute_tps` above minimum.                            | Test fails if throughput collapses.           |
| M5.4    | Add phase threshold       | Assert no single phase exceeds expected budget.                | Bottleneck regression becomes visible.        |
| M5.5    | Save report separately    | Still print/save JSON report, but assertions define pass/fail. | Report is supplementary, not the test itself. |

## Example acceptance thresholds

Use conservative numbers first:

```text
100 entities:
  p95_tick_compute_ms < 50ms

1,000 entities:
  p95_tick_compute_ms < 200ms

5,000 entities:
  p95_tick_compute_ms < 800ms
  slow/manual only
```

## Done means

```text
[ ] Passive scaling test has real assertions.
[ ] Report-only behavior is removed from normal tests.
[ ] Slow scale is marked slow/manual.
```

---

# Milestone 6 — Register pytest markers and clean CI filtering

## Goal

Make perf/slow test selection explicit.

Current perf tests emit `PytestUnknownMarkWarning` because `perf` is not registered.

## Tasks

| Task ID | Task                | Implementation logic                                   | Acceptance criteria                   |
| ------- | ------------------- | ------------------------------------------------------ | ------------------------------------- |
| M6.1    | Add `pytest.ini`    | Register `perf`, `slow`, `integration`, `e2e` markers. | No unknown marker warnings.           |
| M6.2    | Categorize tests    | Mark heavy benchmark tests as `perf` and `slow`.       | CI can select smoke vs full perf.     |
| M6.3    | Add CI command docs | Document commands for unit, smoke perf, full perf.     | Developers know which command to run. |

## Required `pytest.ini`

```ini
[pytest]
markers =
    perf: performance and benchmark tests
    slow: slow tests not intended for normal CI
    integration: integration tests
    e2e: end-to-end tests
```

## Done means

```text
[ ] No PytestUnknownMarkWarning.
[ ] Normal CI can exclude slow tests.
[ ] Full perf suite can be run intentionally.
```

---

# Milestone 7 — Make perf baseline gate real in CI

## Goal

Prevent silent performance regression.

The current baseline behavior can skip when baseline is missing. That is acceptable locally, but useless in CI.

## Tasks

| Task ID | Task                         | Implementation logic                                              | Acceptance criteria                           |
| ------- | ---------------------------- | ----------------------------------------------------------------- | --------------------------------------------- |
| M7.1    | Commit smoke baseline JSON   | Store stable baseline for small deterministic scenarios.          | Baseline file exists in repo.                 |
| M7.2    | Add CI mode                  | Use env var like `CI=true` or `STRICT_PERF_BASELINE=true`.        | Missing baseline fails in CI.                 |
| M7.3    | Keep local flexibility       | Local missing baseline may skip or warn.                          | Local developer workflow stays usable.        |
| M7.4    | Compare compute metrics only | Use `p95_tick_compute_ms`, phase p95, memory; not wall-clock TPS. | Gate is not polluted by machine sleep/pacing. |
| M7.5    | Add baseline update script   | Script regenerates baseline intentionally.                        | Baseline update is explicit.                  |

## Required test behavior

```text
Local:
  missing baseline -> skip/warn

CI:
  missing baseline -> fail
```

## Done means

```text
[ ] CI cannot silently skip perf regression gate.
[ ] Baseline file has schema validation.
[ ] Regression threshold is explicit.
[ ] Baseline update is intentional.
```

---

# Milestone 8 — Re-run optimization proof matrix

## Goal

Re-prove performance optimization after correctness fixes.

Do this only after Milestones 1–7 pass.

## Tasks

| Task ID | Task                             | Implementation logic                                         | Acceptance criteria                          |
| ------- | -------------------------------- | ------------------------------------------------------------ | -------------------------------------------- |
| M8.1    | Run profiler integrity           | `tests/perf/test_profiler_integrity.py`                      | All pass.                                    |
| M8.2    | Run DirtySet integrity           | DirtySet tests + dirty refresh test.                         | All pass.                                    |
| M8.3    | Run O(Dirty) vs full-scan parity | Full-scan must now be real.                                  | All pass.                                    |
| M8.4    | Run local vs concurrent parity   | Idle, movement, resource, combat, strategic, chunk boundary. | All pass.                                    |
| M8.5    | Run perf smoke                   | Resource, strategic, combat, movement, passive scaling.      | All pass under thresholds.                   |
| M8.6    | Run selected 5,000 manual perf   | Movement/API snapshot/strategic if needed.                   | Report generated, not required in normal CI. |

## Required command group

```bash
python -m compileall -q src tests

pytest -q tests/perf/test_profiler_integrity.py
pytest -q tests/perf/test_dirty_set_integrity.py tests/unit/test_dirty_refresh.py
pytest -q tests/perf/test_dirty_parity.py
pytest -q tests/perf/test_concurrency_parity.py

pytest -q -m "perf and not slow" tests/perf
```

Manual:

```bash
pytest -q -m "perf and slow" tests/perf
```

## Done means

```text
[ ] Correctness proof passes.
[ ] Profiler proof passes.
[ ] Perf smoke passes.
[ ] Slow/manual benchmark report exists.
```

---

# Final task order

```text
1. Fix force_full_scan reference path.
2. Move runtime budget enforcement after final compute.
3. Remove hot-path prints.
4. Split API snapshot perf into CI-safe and slow/manual.
5. Add real assertions to passive scaling.
6. Register pytest markers.
7. Make baseline regression strict in CI.
8. Re-run full optimization proof matrix.
```

