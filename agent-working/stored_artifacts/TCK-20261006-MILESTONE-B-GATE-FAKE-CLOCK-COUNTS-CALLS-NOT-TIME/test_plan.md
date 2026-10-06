---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261006-MILESTONE-B-GATE-FAKE-CLOCK-COUNTS-CALLS-NOT-TIME
artifact_type: test_plan
tags: [testing]
---

# test_plan: TCK-20261006-MILESTONE-B-GATE-FAKE-CLOCK-COUNTS-CALLS-NOT-TIME

1) tests/integration/kernel/test_milestone_b_closure.py passes (3 tests). 2) Mutation probe K = 0, 12, 50 in a patched Kernel._phase_persistence: verdict unchanged. 3) Negative control: sibling test at 160 ms reaches SURVIVAL. 4) Runtime measured at the default budget: gate 2.0 s call, sibling 0.5 s, so the slow marker is dropped from both.

## Proof Plan

- Level: integration test of the real Kernel and governor with an injected clock.
- Proof kind: mutation check (K = 0, 12, 50 extra timing calls per tick leave the verdict unchanged) with a negative control (160 ms reaches SURVIVAL).
- Oracle source: the governor thresholds in `src/engine/governor.py` (DEGRADED above `max_tick_budget_ms` 100, SURVIVAL at 1.5x).
- Expected effect: verdict NORMAL then DEGRADED then NORMAL at 120 ms regardless of K; SURVIVAL at 160 ms.
- Selected commands: `pytest tests/integration/kernel/test_milestone_b_closure.py --resource-budget large`; `probe_mb_extra_clock_calls.py` copied under `tests/integration/kernel/` and run with `-s`.
