---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-VERIFICATION-INSTRUMENT-TRANSPARENCY
phase: done
date: 2026-09-20
tags: [architecture, schema, simulation-quality]
---

# Test Plan — TCK-20260920-MECHANISM-VERIFICATION-INSTRUMENT-TRANSPARENCY

## New tests

- `test_rollup_runtime_verified_share_is_a_rate_of_verified_not_of_count` — confirms the
  denominator is `verified`, not `count`.
- `test_rollup_runtime_verified_share_is_zero_not_undefined_when_nothing_verified` — the 0-verified
  edge case.
- `test_render_rollup_includes_runtime_share_of_verified_column` (HTML) — confirms the column
  renders with real numbers matching `build_system_rollup()`'s own output.

## Results

Full `tests/unit/tools/` suite: 263 passed. `registry.py::validate()`: clean, 93 mechanisms. All 5
blocking checks: clean. Zero `verified` entries in `registries/mechanisms.yaml` touched.
