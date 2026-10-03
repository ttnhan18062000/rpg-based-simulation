---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261003-PERF-WALL-CLOCK-READ-INVENTORY
date: 2026-10-03
tags: [performance, determinism, engine]
---

# Plan: TCK-20261003-PERF-WALL-CLOCK-READ-INVENTORY

## Summary
Add `tools/perf/wall_clock_inventory.py` (stdlib `ast`, no `src` import, deterministic JSON/markdown, `--check`,
`--update-doc`) reusing the scope and guard helpers of `hash_callsite_inventory.py`, plus
`docs/performance/wall_clock_inventory.md` (generated block + hand-traced sinks) and a committed JSON for `--check`.

## Steps
1. Scanner: canonical-name resolution through imports; sources per the ticket plus host entropy (`uuid`, `os.urandom`);
   `psutil.Process` instances; `os.environ` reads by variable name; unresolved receivers listed; import-graph reachability from `src/engine/kernel.py`.
2. Tests in `tests/tools/test_wall_clock_inventory.py`; one map line in `_TOOLS_PERF_BASENAME_MAP`.
3. Trace each tick-reachable read group to its sink by reading the code; classify control decisions with PERF-D1's table.
4. Answer PERF-D1's revisit condition; list what the scan cannot see.
5. perf-planner reviews before close.

## Scope guards
No edit under `src/`, no kernel run, no measurement, no edit of PERF-D1 or any P1 document, no CI wiring of `--check`.
