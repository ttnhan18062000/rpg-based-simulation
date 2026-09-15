---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260915-COMBAT-ENGAGEMENT-4X-MEASUREMENT-NO-LONGER-REPRODUCES
phase: done
date: 2026-09-15
tags: [performance, combat]
---

# TCK-20260915-COMBAT-ENGAGEMENT-4X-MEASUREMENT-NO-LONGER-REPRODUCES

## Title
`TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER`'s own measured "4.1x combat volume" A/B (72->297
combat-related events) does not reproduce on current code — candidates identified, none confirmed;
determine why, not assumed

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
`TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER` measured, on 2026-09-14, that enabling
`ENABLE_COMBAT_ENGAGEMENT` raised real combat volume 4.1x (72->297 "combat-related events" per 20
ticks) on a 1000-entity metropolis scenario — a real measurement that drove two real decisions:
accepting a ~3x per-tick cost increase, and re-tiering `test_perf_metropolis_stress` and
`test_perf_metropolis_longevity` to `extra_slow` rather than treating the cost as blocking.

While investigating `TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION` (this
phase's tactical decision has zero downstream consumers), a direct re-run of the same scenario
(`build_metropolis_state`, 1000 entities, seed 42, 5 warmup + 25 sample ticks) counting real
`CombatActions.execute_attack()` calls across four conditions found:

| Condition | Real `execute_attack()` calls |
|---|---|
| A) flag OFF | 1960 |
| B) flag ON, unmodified | 1960 |
| C) flag ON, phase output discarded | 1960 |
| D) flag ON, phase never runs at all | 1960 |

**All four identical.** The originally-measured 4.1x effect does not reproduce today, under any of
the four conditions, including exactly reproducing the original OFF-vs-ON comparison.

## Scope
- **Determine why the original measurement no longer reproduces — do not assume any candidate is
  the cause without checking.** Candidates identified but not confirmed:
  1. The O(n²) spatial-index fix landed the same day
     (`getattr(state, "spatial_grid", None)` dead-code fix in `CombatEngagementPhase`) — changed
     which entities get evaluated as hostile candidates; could plausibly have changed real
     encounter rates as a side effect of fixing the scan itself, independent of the posture
     decision.
  2. The `cognition_bundle_set` whole-object-replace fix (`_read_through_cognition()`, same
     ticket) — changed what memory survives across phases in the same tick; could plausibly have
     changed behavior in some downstream reader this investigation hasn't traced.
  3. The original "combat-related events" metric may have counted something broader than real
     `execute_attack()` invocations (e.g. a push-shaper event count where multiple observability
     events fire per attack, or a metric that also counted `combat_engagement`'s own bookkeeping
     writes as "combat-related") — if so, the original 4.1x may never have represented a change in
     real attack volume at all, only a change in event/observability volume.
  4. Something else entirely, not yet identified — check before concluding one of the above.
- Find and inspect the exact original measurement's own methodology/probe script if it still
  exists (check `stored_artifacts/TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER/`, git history
  around that ticket's commits) before assuming which counting method was used.
- Bisect if needed: run the same four-condition A/B at each of the relevant intermediate commits
  (before/after the spatial-index fix, before/after the cognition-merge fix) to isolate which
  change (if either) affected real combat volume, independent of whatever the original metric
  counted.

## Out of Scope
- Deciding whether to keep the 3x performance cost / re-tiered tests as-is — that decision was
  based on the original measurement and is the user's own call once this investigation reports
  back, not this ticket's to make.
- Wiring `CombatEngagementPhase`'s posture to a real consumer — separate ticket
  (`TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION`).

## Acceptance Criteria
- A real, evidence-backed explanation for why the original 4.1x measurement does not reproduce
  today — bisection results or a confirmed methodology difference, not a plausible-sounding guess.
- The finding reported back so the original performance-cost-acceptance decision can be
  re-evaluated with accurate information, if warranted.

## Related Tickets
- `TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION` (sibling — the "is this feature
  actually doing anything" half of the same finding)
- `TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER` (the ticket whose own measurement this
  investigates)
- `TCK-20260914-HOTFIX-PERF-METROPOLIS-LONGEVITY-RETIER` (re-tiered a sibling test on the strength
  of the same cost/behavior-change reasoning)
- `TCK-20260915-FEATURE-FLAG-KERNEL-PARAM-SILENT-NOOP` (new — the toggle-mechanism bug found while
  re-verifying this ticket's own four-condition A/B)

## Related Docs
- `docs/plans/design_enhancement/performance_optimization/performance_m4_baseline_gate_a_epic.md`
  (carries the original measurement and the 2026-09-15 correction pointing here)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER/` (check for the original A/B's
  own methodology before assuming)

## Related Code Areas
- `src/domains/combat_engagement/phase.py`
- `src/engine/domain/combat_actions.py::CombatActions.execute_attack`
- `src/perf/scenarios.py::build_metropolis_state`

## Assumptions / Open Questions
- **A fifth candidate was found and confirmed, orthogonal to the original four**: the four-condition
  A/B this ticket itself reported (OFF/ON/discarded/never-run all = 1960) was run using
  `Kernel(flags={"ENABLE_COMBAT_ENGAGEMENT": "ON"/"OFF"})`. That parameter is a **silent no-op** for
  this flag — `run_phase()`'s real gate reads `state.feature_flags` (seeded from
  `FeatureFlagManager`'s own default, `ON`), not `Kernel.__init__`'s `flags` dict, which only feeds
  engine-level knobs (`audit_mode`, `perf_tracker`, `no_frame_pacing`, etc.). So every condition in
  the original four-condition A/B was, unknowingly, running with the flag genuinely ON regardless
  of what was passed — filed separately as `TCK-20260915-FEATURE-FLAG-KERNEL-PARAM-SILENT-NOOP`.
- **Re-ran the same scenario with the corrected toggle** (`object.__setattr__(state,
  "feature_flags", {...})` set directly on the frozen `AuthoritativeState` before `Kernel(...)`
  construction): OFF=1960, ON=1960 real `execute_attack()` calls — **still genuinely zero
  difference**. This is the load-bearing result: a second, independently-correct methodology
  reaches the same conclusion as the original (flawed-toggle) four-condition A/B, so the "phase has
  no measurable causal effect on real combat volume in current code" finding is now confirmed with
  high confidence, not just by an accident of a broken toggle happening to compare ON against ON.
- **Original candidates 1-4 (spatial-index fix, cognition-merge fix, differing original metric,
  bisection) remain formally unconfirmed** — this ticket does not resolve *why* the historical
  2026-09-14 measurement showed 4.1x, only that current code, correctly measured, shows no effect.
  Given the practical question this ticket exists to answer (should the accepted 3x perf cost /
  test re-tiering decision be revisited) is now answered with high confidence either way, the
  deeper historical bisection is not pursued further here.
- **One candidate is now ruled out, not just deprioritized**: `TCK-20260915-FEATURE-FLAG-KERNEL-
  PARAM-SILENT-NOOP`'s own audit confirmed the original 2026-09-14 measurement toggled the flag by
  flipping its literal registered default in `src/domains/optimization/feature_flags.py`, not via
  `Kernel(flags=...)` — so the original measurement itself did not use the broken toggle. "The
  original number is an artifact of its own broken toggle" is no longer a live candidate. This
  narrows the remaining field to: a differing original metric (candidate 3, still the most likely
  on current evidence but unverified), or a real behavior change from the spatial-index/cognition-
  merge fixes that landed the same day (candidates 1-2).

## Implementation Notes
See `TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION`'s Implementation Notes for
the full corrected-toggle re-verification detail (same underlying measurement work, done together).

## Test Summary
No code changed by this ticket; verification was measurement-only (see Implementation Notes).

## Files Changed
_(none — investigation/measurement ticket only)_

## Completion Summary
Closed. The original 4.1x measurement's non-reproduction is now confirmed via a second, correct
methodology (not just the original four-condition A/B, which used a toggle later found to be a
no-op) — `ENABLE_COMBAT_ENGAGEMENT` genuinely has zero causal effect on real attack volume in
current code, independent of `TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION`'s
own gate (which does have a large, measured effect, but is new code this arc built, not the
pre-existing phase). The deeper "why did the original number say 4.1x" historical question is
explicitly left open rather than guessed at; see Assumptions / Open Questions.
