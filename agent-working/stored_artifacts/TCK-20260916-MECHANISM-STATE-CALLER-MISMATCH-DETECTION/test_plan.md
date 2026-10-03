---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260916-MECHANISM-STATE-CALLER-MISMATCH-DETECTION
artifact_type: test_plan
tags: [architecture, schema, simulation-quality]
---

# Test Plan — TCK-20260916-MECHANISM-STATE-CALLER-MISMATCH-DETECTION

## Scoped suite

```
.venv313/bin/python3 -m pytest tests/unit/tools/ tests/unit/engine/test_capability_registry.py tests/mechanic_scenarios/ -q
```

## Cases (`tests/unit/tools/test_mechanism_state_caller_check.py`, 11 tests)

- `_is_shim_file` correctly distinguishes a real backward-compat shim from real code.
- `_symbol_names` finds module-level functions, not just classes (load-bearing regression for the
  `diplomacy` false positive).
- `_real_callers` excludes a comment-only mention (load-bearing regression for the
  `strategic_redirection` false positive) and finds a genuine code reference (positive control,
  `CooperationPhase` from `engine/pipeline.py`).
- `check_mechanism` flags `causal_spatial_memory`'s reconstructed historical buggy state
  (load-bearing: proves the detector would have caught the one real historical defect this epic
  found that fits this check's own shape) and does NOT flag its current, corrected state
  (true-negative companion).
- `check_mechanism` flags a synthetic zero-caller `done` mechanism (check #2 coverage, since no
  real registry entry currently exercises it).
- `check_mechanism` returns nothing for a mechanism with no `implemented_by`.
- `build_report` correctly partitions checked vs. unchecked mechanisms.
- The real registry's own current finding set is pinned (`temporal_pressure`,
  `demographic_cohort_cycle`) so future drift is visible in CI.
- Makefile wiring test.

## Result

180 tests passing in the full scoped suite, both with `graphify-out/` present and with it
genuinely moved aside and restored.
