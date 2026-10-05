# perf-m1-kernel-slice

Released by the owner on 2026-10-06 (`performance_optimization_roadmap.md`, "Gate definition and
partial lift", item 6; plan reviewed by rpg-planner on PR #355). The partial lift extends to
`src/engine/kernel.py` and `src/certification/harness.py` for this batch only. `state.py`, `apply.py`
and `pipeline.py` stay gated. No RPG-core PR edits `kernel.py` until this batch's PR merges, so keep
the batch short.

1. `TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY`: the mid-tick throttle and the end-of-tick
   check stop changing outcomes (PERF-D1 inputs 2 and 3). It closes one criterion-1 determinism break.
2. `TCK-20261006-PERF-M1-KERNEL-DIGESTS-VIA-SCHEDULER` (PERF-M1-T03b): kernel digests through
   `CanonicalHashScheduler`, typed status, `HashMode` removed.

The two are independent in code. Do them in this order (1 closes a determinism break; 2 is cleanup).
One branch (`perf-m1-kernel-slice`), one PR. perf-planner reviews each ticket before close and the PR
before merge. After merge: tell the user so the salience fix (Lane A) can start, and notify
`test-architecture-reviewer` (ticket 1, AC 9).
