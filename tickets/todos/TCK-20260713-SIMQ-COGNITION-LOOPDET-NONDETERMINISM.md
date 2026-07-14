---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM
phase: open
date: 2026-07-13
tags: [simulation-quality, cognition, self-model, determinism]
---

# TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM

## Title
COGNITION self-model loop-detection produces a load-sensitive, non-reproducible runaway-loop
result under sustained system load — a real "do not break determinism" violation

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Discovered as a side finding during `TCK-20260713-SIMQ-SCORE-CEILING-FIX`'s Step 12 live-mode
`evaluate_simq.py` corpus sweep. The scenario `urban_political_seed123_500t` is committed in
`tests/simulation_quality/fixtures/grade_anchors.json` with COGNITION grade B (`raw_score=11.0`,
`event_count=2`) — reproduced identically 3 separate times outside the live sweep (once during
SCORE-CEILING-FIX's own Step 6 regeneration, twice more standalone afterward), all bit-for-bit
identical. But one specific run of the full-corpus live-mode sweep (run under ~30 minutes of
sustained concurrent system load, with repeated `WatchdogTrip`/tick-budget-exceeded warnings
throughout its own log) produced a wildly different result for the exact same scenario/seed:
`grade=S`, `raw_score=3521.0`, `event_count=119`, `loop_detected=True` on
`self_model_active`/`subjective_divergence` — a runaway-loop signature in the self-model cognition
subsystem's loop-detection path.

This was confirmed NOT caused by SCORE-CEILING-FIX's diff (that ticket's `git diff` touches zero
COGNITION-related code, weights, or config) and NOT reflective of the true, stable scenario
behavior (3/3 clean reproductions match the committed anchor). It is real evidence that the
project's "do not break determinism" hard rule is not currently holding for the COGNITION
self-model's loop-detection path under sustained system load — a pre-existing, load-sensitive
nondeterminism, not a corpus/anchor staleness issue.

## Scope
- Investigate `src/` COGNITION self-model loop-detection logic (the path producing
  `loop_detected`/`self_model_active`/`subjective_divergence` signals) for what state it reads that
  could be load/timing-sensitive (e.g. wall-clock reads, tick-budget-driven early-exit branches,
  any non-deterministic iteration order or race in shared state).
- Reproduce the runaway-loop condition deliberately under induced system load (e.g. concurrent
  CPU-bound background processes) to confirm the load-sensitivity hypothesis with a controlled
  repro, rather than relying on the one incidental sweep observation.
- Determine root cause and fix so the same scenario/seed produces bit-identical COGNITION output
  regardless of concurrent system load.

## Out of Scope
- Any of SCORE-CEILING-FIX's weight/threshold changes — confirmed unrelated via `git diff`, not
  reopened here.
- Any other pillar's determinism — this is scoped to COGNITION's self-model loop-detection path
  specifically, the only place this symptom was observed.

## Acceptance Criteria
- [ ] Root cause of the load-sensitive nondeterminism identified with file:line evidence.
- [ ] A deliberate repro (controlled induced load) demonstrates the bug before the fix, and its
      absence after.
- [ ] `urban_political_seed123_500t` (and ideally a broader COGNITION-active sample) produces
      bit-identical output across multiple runs under both idle and induced-load conditions.
- [ ] No regressions in `tests/simulation_quality/test_grade_regression.py` or the COGNITION
      scorer/self-model test suites.

## Related Tickets
- `TCK-20260713-SIMQ-SCORE-CEILING-FIX` (done) — where this was discovered as a side finding during
  Step 12's live-mode sweep; confirmed unrelated to that ticket's own diff.

## Related Docs
- `docs/mechanics/04_strategic_cognition.md` — self-model/cognition mechanics chapter.
- `docs/engine/kernel.md` — tick-budget/watchdog behavior (the `WatchdogTrip` warnings observed
  alongside the anomalous result).

## Related Stored Artifacts
None yet.

## Related Code Areas
- COGNITION self-model loop-detection path (locate via `graphify query "self model loop detection"`
  or `grep -rn "loop_detected" src/`) — not yet pinned to a specific file:line, first investigation
  task.
- `src/engine/kernel.py` (tick-budget/watchdog — possible interaction, not confirmed).

## Assumptions / Open Questions
- Whether the root cause is in the self-model subsystem itself or in how the kernel's tick-budget
  throttle interacts with it under load is not yet known — first investigation task.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
