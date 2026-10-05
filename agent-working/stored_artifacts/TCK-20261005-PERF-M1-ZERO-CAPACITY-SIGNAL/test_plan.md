---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261005-PERF-M1-ZERO-CAPACITY-SIGNAL
date: 2026-10-05
tags: [performance, determinism, testing]
---

# Test plan: TCK-20261005-PERF-M1-ZERO-CAPACITY-SIGNAL

New file `tests/unit/kernel/test_worker_capacity_semantics.py`, docstrings cite PERF-D1; none
asserts the old `1.0`.

| State | Case | Expected |
|---|---|---|
| unavailable | after `shutdown()` | not found: stats stay numeric, execution local (recorded) |
| disabled | workers 0, queue 100 | worker util `0.0`, queue util by peak/limit |
| configured-zero | workers 0, queue 0 | constructs; both utilizations `0.0` |
| configured-zero | workers >= 1, queue 0 | `ValueError` naming both |
| configured-zero | negative workers / negative queue | `ValueError` |
| local | queue limit reached forces local | results complete, util <= `1.0` |
| idle | no work | `0.0` |
| busy | partial peak | strictly between |
| saturated | peak == limit | `1.0` |

Governor (`test_resource_governor_contract.py`): disabled and no-queue stats stay `NORMAL`;
saturated stats reach DEGRADED. Regression set: AC 8 list. Mutation check: revert the guard and
confirm the rejection test fails for the right reason.
