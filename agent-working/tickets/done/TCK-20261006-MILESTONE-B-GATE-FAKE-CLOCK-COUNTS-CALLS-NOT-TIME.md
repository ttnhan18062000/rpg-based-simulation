---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261006-MILESTONE-B-GATE-FAKE-CLOCK-COUNTS-CALLS-NOT-TIME
phase: done
date: 2026-10-06
tags: [testing]
---

# TCK-20261006-MILESTONE-B-GATE-FAKE-CLOCK-COUNTS-CALLS-NOT-TIME

## Title
`test_milestone_b_operational_gate` fakes a clock that counts timing calls, not time

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Measured by `test-architecture-reviewer` 2026-10-06 (row 4 of `TCK-20261006-SLOW-STEP-6-REDS-UNMASKED-BY-GATE-FIX`; relayed by hand, not re-measured by the implementer). `tests/integration/kernel/test_milestone_b_closure.py::test_milestone_b_operational_gate` patches `time.perf_counter_ns` to advance 2 ms per CALL. The governor reads `tick_compute_ms` = (`perf_counter_ns` at `kernel.py:811`) − `_start_perf_ts` (`kernel.py:395-396`), so the faked compute time equals 2 ms × the number of timing calls between those points. That count grew 55 → 67 between 2026-08-26 and main; the first SURVIVAL commit is `a2954cfaae3dffb7f7ca643008e3207fddb7900f` (#101). The test verifies the kernel's instrumentation density, not the governor's thresholds.

## Scope
1. Make the test's pressure input independent of how many `perf_counter_ns` calls a tick makes. Candidate seams (choose by measurement and state why): a fake clock keyed to tick boundaries (it advances a fixed per-tick amount regardless of call count), or setting the compute signal through an existing seam. No new patching of private kernel attributes beyond what the test already does. The kernel has TWO compute figures: `kernel.py:462` (sum of phase costs, used by the budget watchdog) and `kernel.py:811` (start-to-record span, feeds the governor's `PressureSignals`). The test must name which one it drives and why.
2. Keep what the test certifies: NORMAL → (sustained 100–150 ms) DEGRADED → worker cap ≤ 2 → recovery to NORMAL after dwell + confidence. Thresholds unchanged (`max_tick_budget_ms` 100; SURVIVAL at 1.5×).
3. Remove the "~63 call sites per tick" comment and any other call-count assumption.

## Out of Scope
The four perf bench timeouts (with perf on #355), the job-level `timeout-minutes`, and any governor change.

## Acceptance Criteria
- [x] The test passes on main at `--resource-budget large` (run shown).
- [x] Mutation proof: adding K extra `perf_counter_ns` calls per tick (K = 0, 12 and 50, e.g. a monkeypatched no-op phase that calls the clock) leaves the verdict unchanged, recorded here. On the old test, K = 12 on the 08-26 tree is exactly the observed flip.
- [x] Negative control: with the injected compute at ≥ 150 ms the gate reaches SURVIVAL, asserted in a sibling test or shown once here, so the fake still drives the governor.
- [x] Audit line: `tests/unit/kernel/test_replay_shutdown_budget.py:29` and `:43` patch `time.perf_counter` with a fixed `side_effect` list. They are call-count-coupled too, but fail loudly (StopIteration) rather than silently changing the verdict. Recorded as audited; fixing them is out of scope unless trivial.

## Related Tickets
- TCK-20261006-SLOW-STEP-6-REDS-UNMASKED-BY-GATE-FIX (row 4)
- TCK-20261005-SLOW-REGRESSION-GATE-SKIPS-ITS-ONLY-TEST-STEP-ON-MAIN

## Related Docs
- None.

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261006-MILESTONE-B-GATE-FAKE-CLOCK-COUNTS-CALLS-NOT-TIME/`

## Related Code Areas
- `tests/integration/kernel/test_milestone_b_closure.py`, `src/engine/kernel.py` (read only), `tests/unit/kernel/test_replay_shutdown_budget.py` (audit)

## Assumptions / Open Questions
- Which seam (tick-keyed fake clock vs an existing signal seam) is cleanest is to be decided by measurement.

## Implementation Notes
**Seam chosen:** a tick-keyed fake clock (`TickKeyedClock` in `tests/integration/kernel/test_milestone_b_closure.py`), patched over `time.perf_counter_ns` as before. The first reading in a tick is the tick's base time and every later reading is base + `compute_ms`; the test calls `clock.begin_tick()` before each `tick_once`. Chosen over setting the signal through another seam because it keeps the kernel's own measurement path under test.

**Which compute figure it drives:** `kernel.py:811` (`_final_compute_ms`, the start-to-record span that feeds the governor's `PressureSignals.tick_compute_ms`). `kernel.py:462` (phase-cost sum) also sees the fake and equals `compute_ms` too (the init phase takes the whole jump, the others 0).

**Watchdog under the fake:** from tick 6, the 120 ms figure exceeds `min(100, max(20, 2 x previous))`, so the watchdog logs "exceeded budget" and records dropped work 9999 on every fake tick. The probe shows `dropped=[9999, 9999]` at K = 0, 12 and 50, so its effect is identical and it cannot change the verdict. The test asserts the mode sequence (NORMAL, then DEGRADED, no SURVIVAL) and the recorded compute figure (120.0 ms).

**Reproduction on `origin/main` f1ec31e25:** the old test fails (164 ms per tick, SURVIVAL), as the reviewer measured.

**Mutation proof (probe in `agent-working/stored_artifacts/TCK-20261006-MILESTONE-B-GATE-FAKE-CLOCK-COUNTS-CALLS-NOT-TIME/probe_mb_extra_clock_calls.py`, a patched `Kernel._phase_persistence` making K extra clock calls):** K = 0, 12, 50 all give modes NORMAL then DEGRADED, compute_ms 120.0, phase-cost sum 120.0, dropped [9999, 9999]. Verdict unchanged. Not kept as a permanent test.

**Negative control:** `test_milestone_b_gate_reaches_survival_at_injected_150ms_plus` drives 160 ms and asserts SURVIVAL and a recorded 160.0 ms.

**Runtime and marker:** at the default budget the gate takes 2.0 s (call) and the sibling 0.5 s (3 tests in 4.4 s with setup), under the ~5 s bar, so `@pytest.mark.slow` is dropped from both; they now run under `-m "not slow"` (2 passed). `test_milestone_b_memory_survival_gate` keeps its `slow` marker (0.38 s; not touched, out of scope).

**Audit (no change):** `tests/unit/kernel/test_replay_shutdown_budget.py:29` and `:43` patch `time.perf_counter` with a fixed `side_effect` list of 3 values. They are call-count-coupled but fail loudly (StopIteration) rather than silently changing a verdict. Recorded as audited; not fixed.

**At `--resource-budget large`:** `pytest tests/integration/kernel/test_milestone_b_closure.py --resource-budget large`: 3 passed in 3.68 s.

## Test Summary
`tests/integration/kernel/test_milestone_b_closure.py`: 3 passed (default budget, 4.4 s); `-m "not slow"`: 2 passed. Old test on main: 1 failed (164 ms, SURVIVAL). Probe K = 0/12/50: 3 passed.

## Files Changed
- `tests/integration/kernel/test_milestone_b_closure.py` (tick-keyed clock, sibling SURVIVAL test, `slow` marker dropped from the two gate tests)
- `agent-working/stored_artifacts/TCK-20261006-MILESTONE-B-GATE-FAKE-CLOCK-COUNTS-CALLS-NOT-TIME/` (plan, investigation, test_plan, probe)

## Completion Summary
`test_milestone_b_operational_gate` now drives the governor through a tick-keyed fake clock, so its verdict no longer depends on how many timing calls the kernel makes per tick. All four acceptance criteria met (see Implementation Notes). No `src/` change. The `slow` marker is dropped from the gate and its new SURVIVAL sibling, so PR lanes run them. Measured figures about the original flip are the reviewer's, relayed by hand; the reproduction, probe and timings above were run in this session.
