---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261006-MILESTONE-B-GATE-FAKE-CLOCK-COUNTS-CALLS-NOT-TIME
artifact_type: plan
tags: [testing]
---

# plan: TCK-20261006-MILESTONE-B-GATE-FAKE-CLOCK-COUNTS-CALLS-NOT-TIME

Replace the per-call fake `time.perf_counter_ns` in `test_milestone_b_operational_gate` with a tick-keyed fake clock (`TickKeyedClock`): the first reading in a tick is the tick base, every later reading is base + compute_ms, so both kernel compute figures (kernel.py:811 start-to-record span, which feeds the governor's PressureSignals, and kernel.py:462 phase-cost sum, which feeds the budget watchdog) equal compute_ms however many timing calls a tick makes. The test drives 120 ms (between DEGRADED 100 ms and SURVIVAL 150 ms). A sibling test drives 160 ms and asserts SURVIVAL. Test-only change; no src/ edit. Seam chosen over setting the signal directly because it keeps the kernel's own measurement path (start-to-record span) under test.
