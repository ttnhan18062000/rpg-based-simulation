---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING
artifact_type: test_plan
tags: [determinism, economy, engine]
---

# Test plan

New: `tests/unit/resource/test_buy_price_independent_of_host_timing.py` (4 tests, `audit_mode=False`, faked clock; all fail on pre-fix `origin/main`, pass after). Rewritten: `tests/unit/resource/test_economy_hardening.py` (`test_buy_price_ignores_a_stale_salience_entry`; arbitrage expects 100).

Existing, rerun with the CI jobs' exact directory lists (`.github/workflows/test.yml`): the unit-core, unit-domain, unit-infra and integration jobs, plus `tests/integrity` and `tests/architecture`; the Tools job's `tests/tools/test_perf_inventories_committed_in_sync.py` and `test_wall_clock_inventory.py`. Gates: code-health ratchet, parity-ledger schema, mypy baseline, frontmatter, registry clean-export check.

## Proof Plan
- **Level**: unit (price function), kernel-level (no `pressure_signals` write).
- **Proof kind**: regression test with a disabling control (fails on the pre-fix tree under `audit_mode=False`).
- **Oracle source**: PERF-D1 amendment A1 (a game-facing signal is computed from deterministic inputs only) and owner decision 2026-10-04.
- **Expected effect**: the buy price equals `max(1, int(base_value))` under any injected `tick_compute_ms`; the kernel leaves `pressure_signals` untouched.
- **Selected commands**: `pytest tests/unit/resource tests/unit/economy tests/integrity tests/integration tests/architecture`; the CI unit job lists; `pytest tests/tools/test_perf_inventories_committed_in_sync.py tests/tools/test_wall_clock_inventory.py`.
