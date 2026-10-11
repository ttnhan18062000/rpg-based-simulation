---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261009-AUTONOMOUS-LOOP-DRIFT-GUARD-RUNS-WITHOUT-AUDIT-MODE-SO-HOST-LOAD-FLIPS-IT
phase: done
date: 2026-10-09
tags: []
---

# TCK-20261009-AUTONOMOUS-LOOP-DRIFT-GUARD-RUNS-WITHOUT-AUDIT-MODE-SO-HOST-LOAD-FLIPS-IT

## Title
The determinism drift guard runs without audit_mode, so a known, documented host-speed input (the governor) can flip it on a loaded host. It should assert the determinism contract as it stands today and point to the open host-speed item.

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
tests/integrity/test_logic_guards.py::test_autonomous_loop_determinism_drift_guard (slow) runs INTEG_RESOURCE_LOOP twice (seed 42, 100 ticks) through `Kernel(profile, initial_state, DeterministicRNG(seed))`, with the default governor, the default tick budget and audit_mode OFF. It failed locally for agent-working-planner during #459 and is green in every slow CI run. Relayed by testing-planner on 2026-10-09.
docs/engine/deterministic_execution.md ("What runs today", items 1-4, and line ~144) already documents that with audit_mode off the governor's tick_compute_ms input differs by host, so outcomes can depend on host speed. Deterministic proxies replace it in perf's Canonical contract (PERF-M1), which is not implemented yet. audit_mode is the documented configuration that suppresses all four wall-clock inputs.
rpg-planner ruling: do NOT hide the host-speed dependence. It is a real, documented, perf-owned open item. But this guard's job is to catch logic nondeterminism (dict order, id()-keyed caches, RNG misuse; see TCK-20261005-DIRTY-SET-DEDUPES-UPDATES-BY-ID...), and that can only be read with the documented wall-clock inputs suppressed.

## Scope
- Run the guard under the documented determinism configuration: audit_mode on, plus the sequential executor and a raised budget if the contract lists them. Cite the doc section in the docstring.
- The docstring also states what it does NOT cover: host-speed dependence through the governor, an open item under PERF-M1 (deterministic_execution.md). Link it; don't restate it.
- Optional, only if cheap: a second, non-blocking report that runs it unpinned and records the governor-mode transitions of each run, so a host-load divergence shows as "mode changed" rather than as an unexplained diff.

## Out of Scope
- Fixing the governor's host-speed input: perf, PERF-M1; governor.py is Phase B held.
- Whether rpg behaviour should hold up under degraded modes: rpg-planner's separate design question.

## Acceptance Criteria
- The guard is stable alone, in the slow suite, and under CPU load (e.g. alongside `pytest -n auto` of another directory), 3 runs each.
- If it still diverges under audit_mode: first log the governor mode, replay_backlog_kb and PhaseBudgetGovernor budgets per tick in both runs (testing-planner's caveat (a): audit_mode might not suppress every governor input; by code, ZeroedSignalSource zeroes compute/worker/queue/memory and force_mode has no src caller, but backlog and phase costs are unverified). If the mode or budgets differ, correct deterministic_execution.md and report to rpg-planner. If they don't, it is a real logic-nondeterminism bug. Stop and report it to rpg-planner; don't change the guard further.

## Related Tickets
TCK-20261009-PINNED-NORMAL-GOVERNOR-SHARED-TEST-HELPER (CONFLICT-04 governor-mode sensitivity, confirmed); TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE; TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY.

## Related Docs
docs/engine/deterministic_execution.md; docs/engine/known_limitations.md; docs/engine/kernel.md.

## Related Stored Artifacts
None.

## Related Code Areas
tests/integrity/test_logic_guards.py (`_run_integrated_loop`).

## Assumptions / Open Questions
- Lane: the next free rpg lane slot. It's tests-only, so the Phase B freeze doesn't apply.

## Implementation Notes
_run_integrated_loop passes flags={"audit_mode": True}; the guard's docstring cites docs/engine/deterministic_execution.md and states what it does not cover (host-speed dependence through the governor, PERF-M1). The optional unpinned governor-mode report was not built (not cheap).

## Test Summary
test_autonomous_loop_determinism_drift_guard under -m slow: 3 runs alone (21.3 s each) and 3 runs under 8 CPU-burning processes (25.5 s each): the equality assertion held in all 6; each ends in the known xfail (steel_sword), as before.

## Files Changed
tests/integrity/test_logic_guards.py

## Completion Summary
The drift guard runs under audit_mode and says what it does not cover. Stable alone and under CPU load, 3 runs each.
