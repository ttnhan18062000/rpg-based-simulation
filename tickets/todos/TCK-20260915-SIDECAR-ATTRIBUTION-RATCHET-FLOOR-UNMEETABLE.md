---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260915-SIDECAR-ATTRIBUTION-RATCHET-FLOOR-UNMEETABLE
phase: open
date: 2026-09-15
tags: [agent-monitoring, data-quality, testing]
---

# TCK-20260915-SIDECAR-ATTRIBUTION-RATCHET-FLOOR-UNMEETABLE

## Title
`test_real_corpus_is_at_or_above_the_ratchet_floor`'s 74.0% floor is currently unmeetable by the live rolling corpus — three independent below-floor readings on unrelated pushes, monotonically declining, no regression in any of them

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary

`tests/tools/test_sidecar_attribution_coverage_check.py::test_real_corpus_is_at_or_above_the_ratchet_floor`
(via `tools/gate_checks/sidecar_attribution_coverage_check.py`, introduced today by
`TCK-20260915-SIDECAR-ATTRIBUTION-GAP`, child of
`TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC`) failed on two consecutive, independent CI runs
of PR #205 — a branch that does not touch sidecar-writing code, monitoring instrumentation, or
`agent-monitoring/data/` shard-generation logic in any way relevant to attribution. Per that
check's own file-header comment, the floor (`ATTRIBUTION_RATE_FLOOR = 74.0`) was pinned "with real
headroom below the last observed value (74.7%)" earlier today, 2026-09-15. Both of PR #205's
independent below-floor readings arrived within about an hour of that pin, and `main`'s own most
recent green run of the same job passed shortly before the first of them. This ticket exists to
record that the floor is not holding against the live corpus's actual current trajectory, not to
fix the underlying attribution gap itself (that gap is already accepted, tracked, and out of this
ticket's scope — see `TCK-20260915-SIDECAR-ATTRIBUTION-GAP`).

## Scope

- Document both below-floor CI readings from PR #205 (this ticket).
- Re-derive whether the floor should move, or whether a real new attribution regression has
  landed since the floor was pinned (needs a same-day trend, not just two points).
- Decide whether `ATTRIBUTION_RATE_FLOOR` should be lowered to hold real headroom against the
  rolling window's current trajectory, or whether some other change (window size, re-pin cadence,
  a genuine regression fix) is the right response.

## Out of Scope

- Fixing the underlying attribution gap itself (`TCK-20260915-SIDECAR-ATTRIBUTION-GAP`'s own
  accept-with-floor disposition stands; this ticket is about the check's floor value, not the
  metric it measures).
- Any other check in the monitoring-anomaly-detection batch.
- Any change to PR #205's own diff (execution census tool / mechanic verification scenarios) —
  this failure is unrelated to that diff, confirmed below.

## Acceptance Criteria

- [ ] A same-day trend of the real attribution rate (more than two points) is captured — done:
      see the four-point monotonic decline below (74.7% → 73.7% → 73.6% → 73.5%).
- [ ] The shared-`.claude/current_run`-sidecar concurrency hypothesis below is checked against a
      quiet day (materially lower concurrent-session activity, no relevant code change): does the
      rate partially recover? This is the cheapest available discriminator and should run before
      any other investigation.
- [ ] Either the floor is re-pinned with real headroom below the current trajectory (not the
      instant-of-pin value), or a genuine regression is found and fixed, with evidence either way.
- [ ] `test_real_corpus_is_at_or_above_the_ratchet_floor` passes against the live corpus after
      whichever fix is chosen.

## Related Tickets
- `TCK-20260915-SIDECAR-ATTRIBUTION-GAP` — introduced the check and the accept-with-floor
  disposition; this ticket does not reopen that disposition, only the floor's real-world
  durability.
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` — parent epic.

## Related Docs
- None yet — no doc currently describes floor re-pinning cadence for this check.

## Related Stored Artifacts
- None.

## Related Code Areas
- `tools/gate_checks/sidecar_attribution_coverage_check.py` (`ATTRIBUTION_RATE_FLOOR`)
- `tests/tools/test_sidecar_attribution_coverage_check.py`

## Assumptions / Open Questions
- Is the rolling 14-day window still declining, or did it stabilize slightly below 74.0% and the
  pin simply didn't hold enough headroom? The two readings here alone can't distinguish these —
  see Acceptance Criteria.
- Is there a real subagent-attribution regression that started right around the pin, or was the
  pin already too tight the moment it landed (both are consistent with the evidence below)?

## Implementation Notes

**Both below-floor readings, from PR #205's own CI (branch `simulation-execution-census-plan`,
diff scope: execution census tool + mechanic verification scenarios — no sidecar/monitoring
instrumentation code touched):**

| Run | Job | Timestamp (approx, UTC) | Rate | Attributed/Total | Floor | Result |
|---|---|---|---|---|---|---|
| `34957214623` | API / tools / logging | 2026-09-15, ~1st run after `d20e42aa3`/`4cdef718e` push | 73.7% | 38246/51893 | 74.0% | FAIL |
| `34957624316` | API / tools / logging (job `104343457040`) | 2026-09-15T10:28:30Z | 73.6% | 38121/51811 | 74.0% | FAIL |
| `34958449595` | API / tools / logging (job `104346046401`) | 2026-09-15T10:38:28Z | 73.5% | 38037/51745 | 74.0% | FAIL |

On this third run, `test_live_health_api_suite[asyncio]` (the environment-dependent live-server
flake noted below) did NOT recur — only the ratchet-floor check failed, consistent with that
other failure being genuinely transient/environment noise as classified, not a second real issue
riding along.

**`main`'s own most recent run of the same job, for comparison:**

| Run | Job | Timestamp (UTC) | Head SHA | Result |
|---|---|---|---|---|
| `34954193214` (job `104332152014`) | API / tools / logging | 2026-09-15T09:44:41Z | `6e422112a9a2...` | **PASS** |

`main`'s three other recent runs in the same window failed only on unrelated jobs (`Slow
regression` x2, `Frontend` x1) — `API / tools / logging` did not appear among them, confirming the
09:44Z pass is the most recent real data point for that job on `main`.

**Why this is not attributable to PR #205's own diff**: the branch adds `tools/execution_census.py`,
`tests/mechanic_scenarios/`, two `.github/workflows/test.yml` fast-lane path-list edits, and
docs/tickets — nothing that writes to `agent-monitoring/data/*/tools.jsonl` or touches
`writeSidecar()`/`run_id` attribution logic. The metric this check reads is a 14-day rolling
window over the *entire* repo's cross-session tool-call corpus, not anything scoped to this PR's
own commits.

**Reading the trend**: 74.7% (pin time, per the check's own file header) → 73.7% → 73.6% → 73.5%
is four points, monotonically declining across roughly an hour, with `main` itself passing at
09:44Z sitting between the pin and the first failure chronologically. A monotonic decline across
four points inside one session is stronger evidence of active degradation than a single breach
sitting flat just under the line — the floor was re-pinned with no real headroom against a metric
that was still moving, not one that had already settled.

**Candidate cause (hypothesis, not investigated — flagged for the owning epic, per peer
session review; do not chase this from this ticket or this branch):** `.claude/current_run` is a
single shared sidecar file across concurrent Claude sessions — a confirmed live defect (see
`project_sidecar_cross_session_contamination` in this repo's own agent-monitoring history, and the
2026-08-24 confirmed case of `tools.jsonl` continuing to log to an already-closed ticket 2 days
after closure). 2026-09-15 has had at least three sessions running concurrently and heavily
(`rpg-implementer`, `rpg-feature-planning`, and `agent-working-design` plus its own implementer).
If `run_id` attribution is resolved through that shared sidecar, concurrent sessions would
overwrite each other's run context mid-flight and produce exactly this shape: a percentage that
degrades as same-day concurrency rises, continuously rather than in a step, and invisible to any
single branch's own diff — because no one branch causes it. This fits every measurement above.
**Falsifiable prediction, cheap to check without investigating anything**: if concurrency is the
real driver, this metric should partially recover on a day with markedly less concurrent session
activity and no corresponding code change. Re-check the rate on such a day before concluding
either way.

## Test Summary
Not yet started — this ticket currently only records the observation per explicit instruction
from the peer session directing this work ("if that check fails again, file it with both
measurements and the main-passes-at-09:44Z data point... Then hold").

## Files Changed
None yet (this ticket file only).

## Completion Summary
Not complete. Filed per explicit instruction to record the finding and hold, not to implement a
fix in the same session — the batch owning `ATTRIBUTION_RATE_FLOOR` and its re-pin cadence
(`TCK-20260915-SIDECAR-ATTRIBUTION-GAP`'s epic) should decide the right response with the full
trend, not a two-point read from an unrelated PR's CI.
