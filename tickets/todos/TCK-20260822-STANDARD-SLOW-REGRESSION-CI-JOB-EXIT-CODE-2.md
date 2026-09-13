---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2
phase: open
date: 2026-08-22
tags: [testing]
---

# TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2

## Title
"Slow regression" CI job (push-to-main only) has failed with exit code 2 on 4 of the last 7 runs

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`.github/workflows/test.yml`'s `slow` job ("Slow regression", `if: github.ref ==
'refs/heads/main' || github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'`
— runs only on push to `main`, never on PR checks, which is why this was not caught by any of
this session's PR-gated CI checks) has failed with **exit code 2** on 4 of the last 7 push-to-main
runs over the past 2 days (run ids 32396405501, 32519599280, 32551803106, 32561870598 — all
"Process completed with exit code 2" per the GitHub check-run annotations, no further detail
visible via `gh api .../annotations` alone). Exit code 2 (vs. 1) suggests a deterministic/systemic
error — e.g. a pytest collection failure, an internal `make` target failure, or an environment
setup problem — rather than ordinary flaky test assertions, though this has not yet been confirmed
by an actual full local reproduction (the job runs 3 heavy steps totaling an estimated 45-90
minutes: `make simq-corpus-diversity-slow-isolated`, `pytest tests/ -m "slow or extra_slow"
--resource-budget large --tb=short -q --ignore=tests/unit/worldassembly/test_corpus_diversity.py`,
and `make lane-legacy-regression`).

**Confirmed NOT caused by any of this session's own changes**: the failure reproduces identically
on commit `5894f8bb` (2026-08-21, predates this session's work) and recurs on the current `main`
tip after this session's own PRs merged cleanly on every job that actually gates PR mergeability.
Both `simq-corpus-diversity-slow-isolated` and `lane-legacy-regression` are confirmed to still
exist as valid `Makefile` targets (not a broken/renamed reference).

**This root cause was independently confirmed TWICE — 2026-08-26 and 2026-09-06 — by two separate
sessions, neither of which wrote it into this ticket, and the second of which did not know the
first had already found it. Recorded here 2026-09-13, the first time either finding reached this
ticket's own body.** This is worse than an unfiled finding: the ticket existed the whole time and
stayed empty while two different sessions independently re-derived the same answer. A known defect
must never live only in session memory — this is what that failure mode costs in practice, not
just in principle.

The 2026-08-26 session confirmed: `Kernel.tick_once()` (`src/engine/kernel.py`, `_phase_resolution()`'s own mid-tick check, and a
softer end-of-tick check feeding the same signal) reads real wall-clock elapsed time
(`time.perf_counter_ns()`) mid-tick, every 10 processed entity results. If elapsed exceeds
`profile.max_tick_budget_ms` **and `self._audit_mode` is `False`** (the default — `True` only if
`Kernel(..., flags={"audit_mode": True})` is passed explicitly), it silently drops the remaining
unprocessed entity results for that tick (`record_dropped_work`) and forces
`RuntimeMode.DEGRADED` directly (`self._governor.force_mode(RuntimeMode.DEGRADED, ...)`). None of
the three affected test files (`tests/integration/kernel/test_long_run_determinism.py`,
`tests/certification/test_cert_long_run_stability.py`,
`tests/simulation_quality/test_grade_regression.py`) set `audit_mode=True`.

Since real per-tick wall-clock timing is subject to host CPU scheduling noise (GC pauses, thread
contention, thermal throttling — not seeded or reproducible), two runs from the identical seed can
diverge in real timing purely by machine luck, causing one run to drop entity updates the other
processes normally — producing genuinely different final entity states and different
`CanonicalStateHasher` hashes. **Directly proven, not just theorized**: `test_1000_tick_determinism`
run twice in a row, identical command (`--resource-budget large`, matching real CI), same machine,
same seed — attempt 1 FAILED (watchdog trip at tick 627, `governance_ecology` phase spiked to 36ms
vs. normal ~0.01-0.15ms), attempt 2 PASSED cleanly. Matches the real CI history this ticket's own
Request Summary above documents (4/7 push-to-main runs failed with exit 2) — same
non-determinism, different runner load each time.

**The second, independent confirmation (2026-09-06)**: a different session investigated this same
ticket's failures again, from a different specific symptom
(`test_hero_guild_routing_seed42_1000t_cognition_grade_stability` failing with `event_count=142`
against the guard's own `<=2` tolerance floor, inside the `simq-corpus-diversity-slow-isolated`
step). That session reproduced the failing test locally twice under real induced load and could
not reproduce the spike, concluding "leaning toward genuine CI-environment timing variance...not
resolved to 100% certainty" — a real, honest, independently-reached data point, but one that never
found the 2026-08-26 session's own already-confirmed root cause, because that finding lived only
in the earlier session's memory, not in this ticket. Both investigations were real and correct as
far as they went; neither had access to the other's work, because neither wrote it here.

**Deferred deliberately, not an oversight**: the user was informed of this root cause and its
recommended fix and said to let it sit (not to pursue a fix now) — this ticket stays open and
undecided-on-purpose, not abandoned or forgotten.

**Downstream consequence, found independently and later (2026-09-13,
`TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION`)**: this same mechanism — real
wall-clock pressure forcing `RuntimeMode.DEGRADED` — was confirmed to reach a concrete, visible
gameplay consequence beyond test-suite non-determinism: under `ScanPolicy.EXACT_DIRTY` (entered
once `DEGRADED` triggers), a freshly-spawned entity with no active AI goal and a static navigation
target could become permanently unable to move — a genuine starvation loop, not mere slowdown.
That ticket's own fix (reduced-cadence movement candidacy) addressed the consequence at
`candidate_selector.py`; it does not touch this ticket's own root cause or change this ticket's own
disposition. Both real `RuntimeMode.DEGRADED`-forcing call sites now carry direct in-code
cross-references back to that ticket: `ResourceGovernor._get_indicated_mode()`'s own
`tick_compute_ms` check (`src/engine/governor.py`) and `Kernel._phase_resolution()`'s own mid-tick
`should_throttle` → `force_mode()` call (`src/engine/kernel.py`) — so anyone revisiting either site
from this ticket, or this ticket from either site, sees the connection without re-deriving it.

## Scope
- Reproduce the job's exact 3-step sequence locally (or via a scoped `workflow_dispatch` run) to
  identify exactly which step and which test/assertion produces exit code 2. **Root cause now
  confirmed** (see Request Summary) — this step is done; recorded here as a record of what was
  found, not new work being requested.
- Fix the real root cause. **Deliberately deferred, not implemented here or now** — the user
  said to let it sit. The recommended fix, if/when this is picked up: a narrow, test-only change
  constructing `Kernel` in the three affected long-run test files with
  `flags={"audit_mode": True}` so wall-clock throttling is disabled during determinism
  verification, matching `audit_mode`'s existing sanctioned purpose elsewhere in `kernel.py`
  (bypassing real-time-dependent shortcuts for audits/certification). No production behavior
  change implied by that fix shape.
- If the root cause turns out to be genuine environment-dependent flakiness (not a real bug),
  document it in `docs/testing/regression_policy.md` as a known category, matching the existing
  precedent for other documented flaky-test categories (e.g. live-server subprocess tests) — do
  not leave it undocumented either way. (Now moot given the root cause above is a real,
  identified logic condition, not undifferentiated flakiness — kept for completeness since the
  disposition is still "let it sit," not "closed.")

## Out of Scope
- Changing the job's trigger conditions (push-to-main-only, per
  `TCK-20260818-STANDARD-SLOW-REGRESSION-OFF-PR-PATH`'s deliberate decision to keep this off the
  PR-blocking path) — that decision is not being revisited here.
- Fixing any other CI job's unrelated flakiness (e.g. `API / tools / logging`'s separate,
  already-known live-server/websocket/CLI-subprocess/knowledge-gateway environment-noise
  category — different job, different symptom, not this ticket's scope).

## Acceptance Criteria
- [x] Root cause identified: `Kernel`'s wall-clock mid-tick throttle (`_phase_resolution()`,
      `should_throttle = not self._audit_mode and elapsed > hard_cap`) breaks determinism when
      `audit_mode=False` (the default, and what all 3 long-run/certification test files use) —
      confirmed via a direct back-to-back repro, not reasoning alone.
- [ ] A real fix lands. **Deliberately deferred** — the user said to let it sit; this remains
      unchecked on purpose, not an oversight. Do not check this box without the user's own
      instruction to proceed.
- [ ] The next several push-to-main "Slow regression" runs are confirmed green — moot while the
      fix is deferred; left unchecked, consistent with the item above.

## Related Tickets
- Discovered as a byproduct of monitoring CI health during TCK-20260821-WORLD-RENDER-CORE's PR
  merge flow, not tied to any prior ticket.
- `TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION` (done) — an independently-found,
  observed downstream consequence of this same root cause (real wall-clock pressure forcing
  `RuntimeMode.DEGRADED`), reaching movement-candidacy starvation rather than test-suite
  non-determinism. That ticket's fix does not touch this ticket's own root cause or disposition.

## Related Docs
- docs/testing/regression_policy.md
- .github/workflows/test.yml

## Related Stored Artifacts
None yet.

## Related Code Areas
- .github/workflows/test.yml (the `slow` job definition)
- Makefile (`simq-corpus-diversity-slow-isolated`, `lane-legacy-regression` targets)
- `src/engine/kernel.py` (`_phase_resolution()`'s own mid-tick `should_throttle` check — the
  confirmed root cause; also directly forces `RuntimeMode.DEGRADED` via `force_mode()`)
- `src/engine/governor.py` (`ResourceGovernor._get_indicated_mode()`'s own `tick_compute_ms`
  check — a second, structurally separate real-wall-clock-driven path to the same
  `RuntimeMode.DEGRADED`, confirmed under `TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION`)

## Assumptions / Open Questions
- Whether this is a real, fixable bug or genuine environment-dependent flakiness under CI's
  specific resource constraints (45-90 min heavy suite) is the central open question this
  ticket's own investigation must resolve — not assumed either way here.

## Implementation Notes
**2026-09-13 update: record-only, not new work.** The durable lesson here is not just "root cause
confirmed" — it's that this root cause was independently confirmed **twice** (2026-08-26 and
2026-09-06) by two different sessions, and neither wrote it into this ticket, so the second never
found the first's already-complete answer. A defect living only in session memory is bad; a
defect re-derived twice because the ticket that exists specifically to hold it stayed empty both
times is worse — the file was there, and it didn't help. Transcribed both investigations into
Request Summary above (explicitly naming both dates and both symptoms, not just the final answer),
added the deferred recommended fix to Scope, and cross-referenced the independently-found
downstream consequence (`TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION`) and its own
two `RuntimeMode.DEGRADED`-forcing code sites (which now carry matching in-code cross-references
back to this ticket). Also corrected the two now-stale session-memory records of this finding to
point here instead of repeating their own snapshots. No code changed by this update. The user's
own "let it sit" instruction stands — this ticket remains `OPEN` in `tickets/todos/`, not
implemented, not closed.

## Test Summary
_(unchanged — no test work performed; this is a documentation-only update)_

## Files Changed
_(this ticket file only — no source/test files changed)_

## Completion Summary
_(unchanged — this ticket is not being closed; the fix remains deliberately deferred)_
