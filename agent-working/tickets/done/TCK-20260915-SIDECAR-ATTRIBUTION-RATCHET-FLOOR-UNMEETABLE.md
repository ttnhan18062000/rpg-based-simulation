---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260915-SIDECAR-ATTRIBUTION-RATCHET-FLOOR-UNMEETABLE
phase: done
date: 2026-09-15
tags: [agent-monitoring, data-quality, testing]
---

# TCK-20260915-SIDECAR-ATTRIBUTION-RATCHET-FLOOR-UNMEETABLE

## Title
`test_real_corpus_is_at_or_above_the_ratchet_floor`'s 74.0% floor is currently unmeetable by the live rolling corpus — real, declining, hand-orchestration-driven gap; lowering the floor is explicitly blocked by the check's own anti-regression guard test

## Status
DONE

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

**Superseded 2026-09-16 by the Decision section below** — the original framing assumed the right
fix was re-pinning the floor or finding a regression. The evidence gathered while pursuing these
same criteria showed no threshold can work; the resolution is gate removal, not a new floor value.

- [x] A same-day trend of the real attribution rate (more than two points) is captured — see the
      four-point monotonic decline (74.7% → 73.7% → 73.6% → 73.5%), later extended to the full
      daily table in the Decision section.
- [x] The shared-`.claude/current_run`-sidecar concurrency hypothesis was checked via the primary
      proposed check (attribution split by session over a 2h window) — result: 0/11 unattributed
      rows all traced to a single session, disproving cross-session collision as the mechanism.
- [x] Either the floor is re-pinned or a genuine regression is found and fixed, with evidence
      either way — evidence found neither applies: re-pinning six times never converged, and the
      absolute-count variant fails identically, so the check itself is the wrong shape.
- [x] Resolved not by making `test_real_corpus_is_at_or_above_the_ratchet_floor` pass, but by
      deleting it and its floor along with it, per the user's Decision — see below.

## Related Tickets
- `TCK-20260915-SIDECAR-ATTRIBUTION-GAP` — introduced the check and the accept-with-floor
  disposition; this ticket does not reopen that disposition, only the floor's real-world
  durability.
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` — parent epic.
- `TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE` — the already-filed gap
  this ticket's 2026-09-16 diagnostic is a confirmed, freshly-measured recurrence of (0/11 recent
  rows unattributed, all from one hand-orchestrated session); strengthens the case for
  prioritizing that ticket's remediation over treating this as a new problem.
- `TCK-20260915-CI-TRIAGE-HAS-NO-ABSENT-RUN-BRANCH` (owned by `agent-working-design`) — filed
  today in the same territory; peer session routed this ticket's finding there directly.

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

**This is a confirmed recurrence of an already-filed gap, not a new discovery.**
`TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE` already covers
hand-orchestrated ticket closures missing monitoring coverage — this ticket's finding is that same
gap, now observed with fresh, quantified measurement (0/11 recent rows, five monotonic
below-floor readings) rather than a qualitative description. That strengthens the case for
prioritizing TCK-20260903's own remediation over treating this as a standalone new problem.

**The defect is self-referential, and that is the cleanest explanation of the whole trend.** Every
hand-orchestrated investigation — including the one that produced this ticket's own findings —
adds more unattributed rows to the corpus. 2026-09-15 saw heavy hand-orchestration across at least
three concurrent sessions (this one included). So the metric degrades *because* work is happening
this way, will keep declining for as long as this arc continues to rely on hand-orchestration, and
cannot recover through more hand-orchestrated investigation of itself — each further diagnostic
pass (this one included) makes the measured rate slightly worse, not better. This is the simplest
account of the five monotonic below-floor readings recorded above (74.7% → 73.7% → 73.6% → 73.5%
→ 73.4%, now 72.7% a day later).

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
- `pytest tests/tools/test_sidecar_attribution_coverage_check.py -v` (`.venv313`, Python 3.13.14,
  CI-matching): 4 passed — the two remaining measurement tests
  (`test_compute_attribution_rate`, `test_rows_outside_the_14_day_window_are_excluded`), a new
  `test_compute_attribution_rate_on_no_recent_rows_returns_none` (covers the same no-recent-rows
  path the deleted `check_sidecar_attribution_coverage` used to test, now against
  `compute_attribution_rate` directly since the wrapping function is gone), and the unchanged
  `test_makefile_wires_sidecar_attribution_coverage_check`.
- `python3 tools/gate_checks/sidecar_attribution_coverage_check.py` run standalone: prints
  `MARKER:[{"status": "PASS", "evidence": "attribution rate 72.1% (35483/49227 tool rows over the
  last 14 days)"}]` — always PASS now, reporting the rate rather than gating on it.
- Verified before editing (not assumed): `grep` across `tools/`, `tests/`, `.github/workflows/`,
  and `Makefile` for `ATTRIBUTION_RATE_FLOOR` / `check_sidecar_attribution_coverage` /
  `sidecar_attribution_coverage_check` found no consumer outside this module and its own test —
  `tools/gate_checks/monitoring_anomaly_validator.py` does not import from this module, and
  `tools/agent-monitoring/generate_retro.py`'s own attribution-adjacent reporting
  (`spend_proxy_coverage`) is a separately-computed `cost_proxy_score` coverage figure, not a call
  into this check — so removing the blocking function does not affect retro report rendering.
- `pytest tests/tools/ -m "not slow and not extra_slow"` (`.venv313`): 2683 passed, 25 skipped,
  28 deselected, 1 xfailed, 0 failed — no regression from the deletion anywhere else in the suite.

## Files Changed
- `tools/gate_checks/sidecar_attribution_coverage_check.py` — removed `ATTRIBUTION_RATE_FLOOR` and
  `check_sidecar_attribution_coverage()` (the blocking floor check); kept
  `compute_attribution_rate()` unchanged for retro reporting; rewrote the module docstring to
  record why this must not be rebuilt as a threshold; `__main__` now reports the rate as an
  always-PASS informational marker instead of gating on it.
- `tests/tools/test_sidecar_attribution_coverage_check.py` — removed the four tests that exercised
  the deleted floor/guard (`test_passes_on_no_recent_rows`, `test_passes_when_rate_at_or_above_floor`,
  `test_fails_when_rate_drops_below_floor`, `test_floor_may_only_increase_never_used_to_paper_over_a_regression`)
  and the corpus-blocking test (`test_real_corpus_is_at_or_above_the_ratchet_floor`); added
  `test_compute_attribution_rate_on_no_recent_rows_returns_none` to keep that code path covered
  against the surviving function.
- `Makefile` — reworded the `sidecar-attribution-coverage-check` target's help text from "Ratcheted
  floor check" to "Report ... (non-blocking; see module docstring)"; target itself unchanged.
- This ticket file — moved `tickets/todos/` → `tickets/inprogress/` → `tickets/done/`.
- `docs/REGISTRY.yaml` — regenerated unconditionally as part of this closure (no manual edits).

## Completion Summary
Per the user's direct 2026-09-16 decision (recorded above, verbatim, from
`agent-working-design`'s own commit `07b2c2bf3` and independently re-verified against the raw
`agent-monitoring/data/*/tools.jsonl` shards before acting), the sidecar-attribution-coverage
blocking gate is deleted rather than re-pinned. The underlying measurement survives for retro
reporting; only the threshold and its two supporting tests are gone. This closes the ticket that
originally observed the floor was unmeetable — the resolution is that no floor should have gated
this metric at all, not a new floor value.

## Decision — 2026-09-16 (user, via `agent-working-design`)

**Remove the gate. Do not lower the floor, do not re-pin it, do not convert it to an absolute
count.** The Scope section above frames this as "which value or window should the floor use" — that
framing is superseded: no threshold works, because the metric does not measure what the check
claims.

### The governing principle (user, 2026-09-16)

> "we don't need to make the test too strictly for agent working, since it's just the side effect,
> not the core simulation feature"

Agent-monitoring telemetry records *how work happened*. It is not a simulation behaviour, and it
does not warrant a blocking gate. Core simulation properties (mechanics, parity, determinism) are
what deserve hard gating.

### The evidence that settles it

Daily attribution rate, measured directly from the shards 2026-09-16:

| Date | Total rows | Unattributed | Rate |
|---|---|---|---|
| 2026-09-08 | 2,002 | 40 | 98.0% |
| 2026-09-09 | 756 | 6 | 99.2% |
| 2026-09-10 | 1,581 | 0 | **100.0%** |
| 2026-09-11 | 3,302 | 1,492 | **54.8%** |
| 2026-09-12 | 2,947 | 2,044 | 30.6% |
| 2026-09-13 | 5,139 | 3,183 | 38.1% |
| 2026-09-14 | 2,589 | 1,808 | 30.2% |
| 2026-09-15 | 1,528 | 595 | 61.1% |

**Nothing regressed on 2026-09-11.** That is the day a hand-orchestrated batch began. The check did
not detect a defect; it detected a change in working style that `CLAUDE.md` explicitly sanctions.
A check that fires because legitimate work is happening is an *inverted* signal, not a weak one.

Supporting facts, each verified rather than assumed:

- **It has never caught a regression.** Created 2026-09-15 by
  `TCK-20260915-SIDECAR-ATTRIBUTION-GAP`; every subsequent movement was ambient corpus drift, and
  every response was re-pinning: 75.3 → 74.0 → (73.0, reverted).
- **The 73.0 attempt required editing its own guard test**
  (`test_floor_may_only_increase_never_used_to_paper_over_a_regression`) to accept the lowered
  value — the exact anti-pattern that test exists to prevent. Caught in peer review and reverted.
- **Re-pinning cannot converge.** Six readings, monotonic, never recovering:
  74.7 → 73.7 → 73.6 → 73.5 → 73.4 → 72.7 → 72.6. Each pin was breached faster than the last.
- **The rolling 14-day window guarantees further decline** regardless of any change: the 98-100%
  days above are still aging out of the denominator.
- **The absolute-count variant fails identically** — and this was checked specifically because it
  had been recommended twice before being tested. The raw unattributed count swings
  0 → 1,492 → 2,044 → 595 day to day, tracking working style exactly as the rate does.
- **`main` is red on this too**, for its last three runs, and has been all day. This is not a
  property of any branch.
- **Cross-session sidecar collision was disproved** by controlled measurement
  (`rpg-feature-planning`): attribution split by session over a 2h window returned 0/11 from a
  *single* session. The cause is that hand-orchestrated work never opens a `run_id` at all.

### What to do

1. **Delete the blocking gate**: `tools/gate_checks/sidecar_attribution_coverage_check.py`'s
   floor-failure path and `test_real_corpus_is_at_or_above_the_ratchet_floor`. Remove
   `ATTRIBUTION_RATE_FLOOR` and its guard test with it — a constant nothing gates on is dead weight.
2. **Keep the measurement as a reported number.** The rate is genuinely informative in
   `RETRO-*.md` (it is already surfaced there); losing the number is not the goal, losing the
   *gate* is.
3. **Record why in the module**, briefly, so the next person does not rebuild it: the metric moves
   with working style, so no threshold over it can distinguish regression from legitimate activity.

### If a real detector is wanted later (not this ticket)

Scope it to a population where attribution is *expected to hold*: pipeline runs that opened a
`run_id` whose own tool rows lack one. That should be zero and stay zero, so any nonzero is a true
defect. That is a different, narrower check than a corpus-wide rate diluted by sanctioned
hand-orchestration — and it belongs in its own ticket, with a measured baseline, not here.

### Consequence

Removing the gate turns `main` and PR #208 green honestly, without lowering any threshold or
weakening any guard. `TCK-20260915-SIDECAR-ATTRIBUTION-GAP`'s underlying accept-and-document
disposition for the ~25% unattributed rows is unchanged; only the blocking check is removed.
