---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261006-PERF-LIVE-CONTROL-TRACE
phase: open
date: 2026-10-06
tags: [performance, determinism, engine]
---

# TCK-20261006-PERF-LIVE-CONTROL-TRACE

## Title
PERF-D1 Live bounded contract: a versioned, bounded control trace records every runtime decision that changes what is computed, and a trace-consuming replay reproduces a Live run's hashes

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The owner filed this on 2026-10-06, accepting the recommendation in the design of
`TCK-20261006-PERF-GOVERNOR-WALL-CLOCK-INPUTS-DETERMINISTIC-PROXY` (plan.md §4; decisions in
`performance_optimization_decisions.md`, PERF-D1 "Update 2026-10-06"). That ticket builds the
**Canonical** half: modelled signals, opt-in through `RuntimeProfile.signal_contract`. This ticket builds
the **Live bounded** half, which PERF-D1 (approved 2026-10-03) defines as follows:

> Real wall-clock and resource signals are allowed. Every decision that changes what is computed is
> either written to a versioned, bounded control trace or is derivable from one that is. Guarantee: a
> Live run is reproducible **given its trace** — a Canonical-mode replay that consumes the trace reaches
> the same hashes.

Until this exists, a Live run that leaves `NORMAL` keeps the `verification_level = REDUCED` label
(INFRA-363), and the live server is reproducible only under `audit_mode`.

**Gate:** waits for the full lift. The writer and the replay hook touch `kernel.py` (where the decisions
are applied) and `replay_manager.py`. It also depends on the governor ticket's `signal_contract` field.

## Scope
1. **Decision inventory.** List every runtime decision that changes what a tick computes:
   - `RuntimeMode` transitions;
   - the emitted `GovernorPolicy` (cadence, concurrency limit, replay richness, trace flags);
   - `PhaseBudgets` (scan policy, candidate, strategic and movement budgets, sweep interval);
   - anything else the inventory finds.
   Use the governor design's investigation and `docs/performance/wall_clock_inventory.md`. The kernel's
   overrun records are report-only since #379. Include them only as annotations, never as inputs.
2. **Trace format.**
   - Versioned (a scheme name like the proof digest's) and bounded: a size budget per tick and per run,
     with a rule for what happens at the bound.
   - Records only decisions, not raw signals, unless a decision cannot be derived without them.
   - Stored next to the replay stream; `ReplayManager` writes it.
3. **Trace-consuming replay.** A Canonical-mode run that reads the trace and applies the recorded
   decisions instead of evaluating the governors, reaching the same canonical hash at every tick.
4. **Memory and backlog guard.** Canonical deliberately dropped them (Q-A). Under Live they stay,
   because every decision they cause is recorded.
5. **Verification-level rule.** Define when a Live run with a complete trace stops being `REDUCED`
   (INFRA-363), and update the label logic.
6. **Docs and parity:** `deterministic_execution.md` ("Live bounded contract"), the replay doc, the
   parity ledger, and the PERF-D1 status.

## Out of Scope
- The Canonical proxies (the governor ticket).
- Changing governor logic or thresholds.
- Trace compression or storage tiers beyond the stated bound.

## Acceptance Criteria
1. A Live run under real load (mode changes forced by a patched or real clock) writes a trace, and a
   trace-consuming replay reaches the same canonical hash at every tick. The test passes 10 of 10 runs.
2. The trace has a scheme and version, and the reader refuses an unknown one.
3. The size bound is enforced and tested, and behaviour at the bound is defined and tested.
4. The verification-level rule is updated and tested.
5. Docs and parity ledger updated. `uv run make code-health` and `uv run make typecheck-py` report no new
   or worse finding.
6. No `src/` edit before the full lift (or an owner partial lift naming the files), recorded in the
   ticket.

## Related Tickets
- `TCK-20261006-PERF-GOVERNOR-WALL-CLOCK-INPUTS-DETERMINISTIC-PROXY` (prerequisite: the `signal_contract` field)
- `TCK-20261006-PERF-M1-KERNEL-DIGESTS-VIA-SCHEDULER` (done; typed digests the replay compares)
- `TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY` (done; overruns are annotations, not decisions)

## Related Docs
- `docs/architecture/performance_optimization_decisions.md` (PERF-D1, update 2026-10-06)
- `docs/engine/deterministic_execution.md`
- `docs/plans/design_enhancement/performance_optimization/system_design_terms_and_concepts.md` (control trace)

## Related Stored Artifacts
- The governor design's staging artifacts (plan.md §4), when stored

## Related Code Areas
- `src/engine/kernel.py`, `src/engine/replay_manager.py`, `src/engine/governor.py`,
  `src/engine/phase_governor.py`, `src/engine/policy.py`, the replay reader

## Assumptions / Open Questions
- Whether `PhaseBudgets` can be re-derived from the recorded mode plus deterministic state, or must be
  recorded itself. The design decides.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
