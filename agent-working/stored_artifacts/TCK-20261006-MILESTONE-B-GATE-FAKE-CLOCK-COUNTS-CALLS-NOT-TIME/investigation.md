---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261006-MILESTONE-B-GATE-FAKE-CLOCK-COUNTS-CALLS-NOT-TIME
artifact_type: investigation
tags: [testing]
---

# investigation: TCK-20261006-MILESTONE-B-GATE-FAKE-CLOCK-COUNTS-CALLS-NOT-TIME

Reproduction on origin/main f1ec31e25: the old test fails (compute 164 ms per tick, SURVIVAL; 67 timing calls x 2 ms plus 30 ms). Relayed by test-architecture-reviewer: 55 calls / 126 ms / DEGRADED at eedf7d5b4 (2026-08-26) vs 67 calls / 164 ms on main; first SURVIVAL commit a2954cfaa (#101). Watchdog under the fake: from tick 6 on, _final_compute_ms (120) > min(100, max(20, 2 x previous)) so it logs 'exceeded budget' and records dropped_work 9999 on every fake tick; identical at K = 0, 12 and 50, so it cannot change the verdict. Probe: probe_mb_extra_clock_calls.py (copy it into tests/integration/kernel/ to run).
