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
`test_real_corpus_is_at_or_above_the_ratchet_floor`'s 74.0% floor is currently unmeetable by the live rolling corpus — real, declining, hand-orchestration-driven gap; lowering the floor is explicitly blocked by the check's own anti-regression guard test

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
- [ ] The shared-`.claude/current_run`-sidecar concurrency hypothesis below is checked via the
      primary proposed check: measure attribution directly on records written in the last few
      hours (ideally split by session), not the 14-day rolling average. Near-zero on recent
      records while the 14-day average still reads ~73.5% confirms the hypothesis with one query;
      normal recent-record attribution kills it. Run this before anything else.
- [ ] Secondary confirmation once available: does the 14-day rate partially recover on a day with
      markedly less concurrent session activity and no corresponding code change?
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
**Numerator/denominator arithmetic strengthens this beyond the trend line alone.** Comparing the
first and third readings above:

- Δnumerator (attributed) = 38037 − 38246 = **−209**
- Δdenominator (total) = 51745 − 51893 = **−148**

The attributed count fell by 61 more than the total count did. In a rolling window, that is only
possible if the records *entering* the window over that hour are worse-attributed than the records
*ageing out* of it — it cannot be produced by volume alone, by old data simply expiring, or by any
mechanism that treats incoming and outgoing records symmetrically. So the decline is not the
window slowly drifting; it is newly-written records arriving badly attributed and dragging a
~52k-record rolling average down 0.2 points in about an hour. Moving an average that large that
fast implies the incoming attribution rate is *well* below 73%, not marginally below it — the
exact magnitude depends on the window's retention mechanics (not visible from these CI reads), so
no specific incoming-rate number is asserted here, only the direction.

This is exactly what concurrent sessions overwriting one shared `.claude/current_run` would
produce: each session's freshly-written tool rows resolve `run_id` against whichever session last
wrote the sidecar, so most land wrongly-attributed or unattributed at write time — a defect in
*new* records, not a decay of old ones.

**Primary proposed check (cheap, available now, replaces the quiet-day test as the first thing to
run):** measure attribution directly on records written in the last few hours — ideally split by
session — instead of the 14-day rolling average. If that recent-records rate comes back near zero
while the 14-day average still reads ~73.5%, the hypothesis is confirmed with one query and no
further investigation. If recent records attribute normally, the hypothesis is dead and the
decline has some other cause. This distinguishes *which* records are bad, not just that the
average moved, and doesn't require waiting for a quiet day.

**Secondary confirmation, cheap but slower:** if concurrency is the real driver, the 14-day rolling
rate should also partially recover on a day with markedly less concurrent session activity and no
corresponding code change. Useful as a second, independent signal once available, but the recent-
records check above should run first.

This hypothesis and both checks are flagged for the owning epic to run — not investigated or run
from this ticket or this branch.

**UPDATE 2026-09-16: the primary proposed check was run (read-only, real corpus, no code
touched), and it redirects the root-cause explanation.** Prompted by a direct user request to
resolve the failing CI check on PR #205, I ran the exact diagnostic this ticket proposed —
attribution rate on records written in the last few hours, split by session, against
`agent-monitoring/data/*/tools.jsonl` directly (script not committed; read-only, used
`generate_retro._load_source` the same way the check itself does):

```
14-day: 72.7% (36548/50293)   [confirmed via the real check's own compute_attribution_rate()]
24h:    38.6% (858/2225)
2h:      0.0% (0/11)   — all 11 rows this session's own session_id, all run_id=None
```

The recent-records rate did come back near zero, confirming the *shape* the shared-sidecar
hypothesis predicted — but the split-by-session breakdown does NOT support cross-session
overwriting as the mechanism. All 11 unattributed rows in the last 2 hours belong to a single
session (this one), not several sessions colliding on one file. That session was doing exactly
the kind of ad-hoc, hand-orchestrated work (CI triage, filing this very ticket) that never opens
a tracked pipeline run in the first place — there is no `run_id` to attribute to, not a wrong one
written by a colliding session. This matches the check's own module docstring precisely: "the
live gap is dominated by real, in-principle-attributable ticket work... missing sidecar coverage
for hand-orchestration compliance reasons." **Revised read: the decline is real, but it's driven
by the volume of hand-orchestrated (non-pipeline-tracked) tool-call activity across the corpus
growing relative to pipeline-tracked activity, not by concurrent sessions corrupting each other's
`run_id`s.** The shared-`.claude/current_run` file may still be a contributing factor for
sessions that *do* have a run_id but get the wrong one — that's not ruled out — but it is not the
dominant mechanism the single-session 0/11 breakdown shows.

**This also settles what CANNOT be done to close this ticket.**
`tests/tools/test_sidecar_attribution_coverage_check.py::test_floor_may_only_increase_never_used_to_paper_over_a_regression`
is a dedicated guard, already in the repo, asserting `ATTRIBUTION_RATE_FLOOR == 74.0` with an
explicit message: "never lower it to paper over a new regression." Lowering the floor to make CI
pass would fail this test directly — it is not an available fix, it is the exact maneuver this
check's own author built a second test specifically to block. Confirmed by running
`pytest tests/tools/test_sidecar_attribution_coverage_check.py -v`: 7 passed (including the
guard), 1 failed (the ratchet-floor check itself, real corpus at 72.7%).

**Conclusion for whoever picks this up:** there is no code-level fix available from a PR that
doesn't touch attribution-writing paths. The real fix is raising actual attribution coverage —
most plausibly, giving hand-orchestrated/non-pipeline tool calls a way to attribute to *something*
(even a synthetic "hand-orchestrated" run marker) rather than `None` — which is a substantive,
cross-cutting change to how/when `run_id` gets written, squarely inside
`TCK-20260915-SIDECAR-ATTRIBUTION-GAP`'s and the owning epic's territory, not a floor tweak.

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
