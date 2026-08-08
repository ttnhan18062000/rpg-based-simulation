---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF
artifact_type: test_plan
phase: investigate
date: 2026-08-08
tags: [feature-flags, progression, world]
---

# Test Plan — TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF

## No new unit tests — this is a config + calibration-data change

No `src/` logic changes, so no new unit test is warranted. Verification is via:

1. `pytest tests/integration/scenarios/test_balance_regression.py -q` — confirm
   `test_adventure_routing_defaults_off` still passes (the GLOBAL default is untouched; only
   `frontier_marches`'s own profile changes).
2. `pytest tests/simulation_quality/test_grade_regression.py tests/simulation_quality/
   fixtures/ -k frontier_marches -q` (or the closest scoped equivalent found in Implement) —
   confirm the updated `grade_anchors.json` entries are internally consistent with the schema and
   the regression harness accepts them.
3. Real `tools/calibrate_simq.py` runs for all 3 `frontier_marches` seeds at 200 ticks
   (`dropped_count == 0` required) — the actual source of the new anchor values, not a
   hypothesis.
4. `pytest tests/unit/config/test_phase10_feature_flags.py -q` — confirm the global
   `ENABLE_ADVENTURE_ROUTING` default is still `OFF` (this ticket's fix must not regress that).

## Scoped pytest command

```
pytest tests/integration/scenarios/test_balance_regression.py tests/unit/config/test_phase10_feature_flags.py tests/simulation_quality/test_grade_regression.py -q
```
