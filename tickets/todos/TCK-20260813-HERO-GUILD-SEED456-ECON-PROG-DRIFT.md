---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT
phase: open
date: 2026-08-13
tags: [simulation-quality, calibration, corpus, economy, progression]
---

# TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT

## Title
`hero_guild_routing_seed456_500t` ECONOMY/PROGRESSION drift beyond band/tolerance, plus a related
unannotated `simq_routing_test_seed456_500t` PROGRESSION score-tolerance drift found during
Implement — both disclosed but out of `TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT`'s
own named scope

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Filed as the required follow-up ticket for a finding explicitly deferred by
`TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT` (that ticket's Scope named only
AGENCY + the `seed123` COGNITION/AGENCY pair; this ECONOMY/PROGRESSION drift on a different
run_key was confirmed present in the same fresh committed report but deliberately not folded into
that ticket's recalibration — see its Scope Guards and plan.md Step 9b).

**(1) `hero_guild_routing_seed456_500t` ECONOMY/PROGRESSION drift (named by the originating
ticket).** Fresh calibration at current HEAD (`tools/calibrate_simq.py --ticks 500 --seed 456
--name hero_guild_routing`) shows:
- ECONOMY: anchor grade B (`score=0.10972568578553615`) vs. actual `0.0` — outside score
  tolerance, no `score_ceilings.json` ceiling annotation covers this.
- PROGRESSION: anchor grade D (`score=-0.6212534059945504`) vs. actual `-0.3025210084033613` —
  outside score tolerance, no ceiling annotation.

**(2) `simq_routing_test_seed456_500t` PROGRESSION drift (newly found during the originating
ticket's Implement phase, not previously named by any ticket).** This run_key's PROGRESSION was
previously masked from view: the `test_grade_within_anchor_band` assertion order evaluates
`band_failures` before `score_failures`, and prior to the originating ticket's AGENCY recalibration
this run_key's AGENCY band-crossing failure short-circuited the test before its PROGRESSION
score-tolerance failure was ever surfaced. Once AGENCY was recalibrated, PROGRESSION became
visible: anchor `score=-0.6927374301675978` vs. actual `-0.15483870967741936` — outside score
tolerance, no `score_ceilings.json` ceiling annotation covers this run_key's PROGRESSION either.
`simq_routing_test_seed456_500t`'s own COMBAT drift in the same fresh run (`actual=0.0727...` vs
anchor `0.0`) IS already covered by an existing `flag_gated` ceiling annotation
(`ENABLE_COMBAT_ENGAGEMENT` corpus-wide OFF) — only PROGRESSION is new/unexplained.

Neither drift was fixed or recalibrated by the originating ticket — its own Scope Guards
explicitly forbid touching `hero_guild_routing_seed456_500t`'s ECONOMY/PROGRESSION fields, and
`simq_routing_test_seed456_500t`'s PROGRESSION drift was outside its named scope entirely (only
discovered as a side effect of that ticket's own AGENCY fix unmasking a previously-hidden
assertion).

## Scope
- Determine the root cause of `hero_guild_routing_seed456_500t`'s ECONOMY and PROGRESSION drift —
  confirm whether it shares the same commit-cluster cause as the AGENCY/COGNITION drift
  (`3d992dd0`/`TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION`, or the `AdventureDecisionPhase`
  deletion) or is a distinct mechanism.
- Determine the root cause of `simq_routing_test_seed456_500t`'s PROGRESSION drift — confirm
  whether it is the same mechanism as (1), the same class of pre-existing `watchdog_variance` noise
  already documented for sibling run_keys' PROGRESSION fields, or something new.
- Recalibrate `grade_anchors.json` for whichever fields are confirmed genuine drift (not a bug to
  fix), or add a `score_ceilings.json` ceiling annotation if the root cause is the same
  low-event-count watchdog-throttle sensitivity already documented for sibling run_keys'
  PROGRESSION fields.

## Out of Scope
- AGENCY/COGNITION for any of the 6 run_keys `TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT`
  already recalibrated — already closed by that ticket.
- The `_1000t` guard test conversions — already closed by that ticket.
- `src/domains/adventure/`, `src/systems/strategic_systems/intelligence.py`, or any other
  production code — Investigate first; only fix source if a real code gap (not a stale anchor) is
  confirmed.

## Acceptance Criteria
- [ ] Root cause of `hero_guild_routing_seed456_500t`'s ECONOMY/PROGRESSION drift confirmed via
      direct evidence, not assumed
- [ ] Root cause of `simq_routing_test_seed456_500t`'s PROGRESSION drift confirmed via direct
      evidence, not assumed
- [ ] `grade_anchors.json` and/or `score_ceilings.json` updated to reflect confirmed current,
      correctly-classified values for both run_keys
- [ ] `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q -k
      "hero_guild_routing_seed456_500t or simq_routing_test_seed456_500t"` shows 0 unexplained
      failures

## Related Tickets
- TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT (originating ticket; disclosed (1) via
  its own Scope/investigation.md Risk #3, and (2) was found and disclosed during that ticket's own
  Implement-phase verification of its AGENCY recalibration)
- TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP (established the `watchdog_variance`
  ceiling mechanism these fields may or may not qualify for)

## Related Docs
- docs/guidelines/intentional_divergences.md §2.40, §2.41

## Related Stored Artifacts
- stored_artifacts/TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT/ (once moved —
  investigation.md Finding 1's raw pytest evidence for (1); this ticket's own filing session for
  (2))

## Related Code Areas
- tests/simulation_quality/fixtures/grade_anchors.json (`hero_guild_routing_seed456_500t`,
  `simq_routing_test_seed456_500t` ECONOMY/PROGRESSION fields)
- tests/simulation_quality/fixtures/score_ceilings.json

## Assumptions / Open Questions
- Whether (1) and (2) share a single root cause or are two distinct mechanisms is not determined —
  Investigate's job.
- Whether either qualifies for the `watchdog_variance` ceiling mechanism (real run-to-run
  non-determinism at low event counts, per the precedent in
  `TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP`) or represents a genuine anchor drift
  requiring recalibration is not determined here.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
