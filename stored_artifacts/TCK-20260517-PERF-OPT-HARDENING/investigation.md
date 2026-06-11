---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260517-PERF-OPT-HARDENING
artifact_type: investigation
tags: [perf, opt, hardening]
---

# Investigation Notes: Performance Optimization Hardening

## Overview
Based on `performance_opt_hardening.md`, while the baseline profiler and DirtySet tracking mechanics are highly effective, several subtle gaps remain in ensuring 100% measurement honesty and reference path parity:
1. `force_full_scan` is recognized during dirty set refresh but ignored by individual pipeline phases (e.g., interaction routing, strategic redirection, group updates, shop, capacity enforcement, and town resolution), which directly access `update.dirty_set`.
2. Budget enforcement in `Kernel.tick_once()` executes mid-tick before persistence and final phase accounting complete, operating on stale latency values and triggering premature pressure drops.
3. Multiple `print()` statements in hot paths (`pipeline.py`, `intelligence.py`, `tactical.py`, `inventory.py`) introduce I/O latency and pollute benchmark logs.
4. The 5,000-entity API snapshot benchmark performs 20 deepcopy samples, which is prohibitively slow for standard CI passes.
5. Passive scaling tests emit benchmark reports without enforcing automated p95 latency and memory assertions.
6. Pytest markers (`perf`, `slow`, `integration`, `e2e`) are not fully registered in `pyproject.toml`, resulting in warning spam during test collection.
7. Performance baseline regression checks should strictly fail in CI mode (`CI=true` or `STRICT_PERF_BASELINE=true`) if baseline reports are missing.

## Key Findings & Proposed Solutions
- Centralize entity filtering in `src/core/dirty.py` via `get_relevant_entity_ids` to ensure all phases seamlessly respect `force_full_scan`.
- Relocate budget enforcement in `kernel.py` to line 226 after persistence and final phase summing.
- Replace hot-path `print()` statements with `logger.debug`.
- Parameterize `test_perf_api_snapshot.py` to separate CI smoke tests (100, 1000) from manual slow benchmarks (5000).
- Add strict latency thresholds to `test_perf_passive_scaling.py`.
- Update `pyproject.toml` markers and CI regression gates.
