---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261003-PERF-WALL-CLOCK-READ-INVENTORY
date: 2026-10-03
tags: [performance, determinism, engine]
---

# Investigation: TCK-20261003-PERF-WALL-CLOCK-READ-INVENTORY

Full evidence is `docs/performance/wall_clock_inventory.md`. Findings that bear on PERF-D1:

- A fourth input reaches authoritative state: `tick_compute_ms` -> `compute_ratio`/`global_salience` (`kernel.py:661-678`) ->
  `AuthoritativeState.pressure_signals` (`apply.py:335,510`) -> `DynamicPriceService` (`economy.py:27`) -> shop price (`town/shop.py:36-41`).
  `audit_mode` zeroes it. Not in PERF-D1's table.
- The replay backlog (`governor.py:101-102`) is a governor DEGRADED trigger not named in PERF-D1's three inputs.
- `PhaseBudgetGovernor` (`phase_governor.py:108-141`) reads per-phase wall-clock costs independent of mode; PERF-D1 has a table row, not a named input.
- No RNG is seeded from time or entropy; ids and run ids from time/uuid reach only artifacts and observability records.
- 363 reads: 159 in modules the kernel imports, 204 elsewhere; one text-search hit the scanner did not record (an exception class).
