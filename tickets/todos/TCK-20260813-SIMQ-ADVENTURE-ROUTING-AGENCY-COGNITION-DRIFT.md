---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT
phase: open
date: 2026-08-13
tags: [simulation-quality, calibration, corpus, agency, cognition, adventure]
---

# TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT

## Title
AGENCY has drifted to 0/C on all 4 `ENABLE_ADVENTURE_ROUTING=ON` COGNITION-anchor items, plus a
milder COGNITION+AGENCY score-tolerance drift on the un-named `seed123` variants — disclosed but
explicitly out of scope by `TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP`,
and the two stale `_1000t` SLOW-tier COGNITION guard tests sharing the same root-cause family

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
While implementing `TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP` (a
COGNITION-only recalibration for 4 named `ENABLE_ADVENTURE_ROUTING=ON` FAST-tier anchors plus
`lifecycle_full_coverage_world_seed42_200t`'s 8-pillar drift), that ticket's own mandatory
Implement-time fresh re-verification (`tools/calibrate_simq.py`'s real internals, 2 independent
trials per item, run 2026-08-13) surfaced findings beyond its named scope that it explicitly did
not fix, per its own Decision 2 and Scope Guards:

**(1) AGENCY drift, confirmed broader than originally disclosed.** Investigation for that ticket
had flagged AGENCY drifting from `A/0.918` to `0 events/0.0/C` on exactly one run_key
(`simq_routing_test_seed42_500t`), plausibly caused by
`docs/guidelines/intentional_divergences.md` §2.41 "Adventure-Route Defer-Reason Observability
Gap" (`TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE` deleting `AdventureDecisionPhase` without
porting `last_defer_reason`/`defer_with_reason` emission). Fresh re-verification during
Implement (2 independent trials each, bit-identical) confirms the SAME `0 events/0.0/C` AGENCY
outcome on **all 4** of that ticket's named COGNITION-anchor run_keys, not just one:
- `simq_routing_test_seed42_500t` AGENCY: anchor A/0.918 → actual 0/0.0/C (band-crossing failure)
- `simq_routing_test_seed456_500t` AGENCY: anchor A/0.6415 → actual 0/0.0/C (band-crossing failure)
- `hero_guild_routing_seed42_500t` AGENCY: anchor A/0.9777 → actual 0/0.0/C (band-crossing failure)
- `hero_guild_routing_seed456_500t` AGENCY: anchor A/0.6727 → actual 0/0.0/C (band-crossing
  failure; ECONOMY and PROGRESSION also drifted beyond score tolerance on this run_key, both
  score-tolerance-only, not band-crossing — see raw pytest output cited in Related Stored
  Artifacts)

**(2) A milder, previously-undisclosed COGNITION+AGENCY score-tolerance drift on the un-named
`seed123` variants of the same two worlds** (neither is one of the 4 items named by the
originating ticket, so its own scope never covered them):
- `simq_routing_test_seed123_500t`: COGNITION actual_score=0.04 vs anchor 0.5295 (score-tolerance
  failure, NOT a band crossing — grade stays in-band); AGENCY actual_score=0.168 vs anchor 0.6415
  (same, score-tolerance only)
- `hero_guild_routing_seed123_500t`: COGNITION actual_score=0.0467 vs anchor 0.5295 (score-tolerance
  only); AGENCY actual_score=0.1963 vs anchor 0.6415 (score-tolerance only)

Note `tests/simulation_quality/fixtures/score_ceilings.json` already carries a
`simq_routing_test_seed123_500t`/PROGRESSION `watchdog_variance` entry (from
`TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP`) whose own reason text states COGNITION
was "stable at 0.5295/52 events across both re-runs" for this run_key at the time — i.e. this is a
**new** drift since that entry was written, not a re-confirmation of already-known variance.

**(3) Two stale, currently-failing SLOW-tier COGNITION guard tests sharing Finding 1's exact root
cause** (`TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION`, bisected to commit `3d992dd0`) for
the `_1000t` variant of the same two worlds:
`tests/unit/worldassembly/test_corpus_diversity.py::test_simq_routing_test_seed42_1000t_cognition_grade_stability`
(line ~600) and `::test_hero_guild_routing_seed42_1000t_cognition_grade_stability` (line ~684).
Both still carry the old 3-trial tolerance-guard shape and a stale F6/watchdog-variance-framed
docstring, and are mechanically excluded from `TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-
LIFECYCLE-ANCHOR-GAP`'s own AC5 gate (`-m "not slow"` never runs `@pytest.mark.slow` tests).

None of (1)/(2)/(3) were fixed by the originating ticket — its own Decision 2 and Scope Guards
explicitly ruled AGENCY-fixing and the `_1000t` guards out of scope (different pillar / different
root-cause ticket than its own Finding 1), directing this follow-up instead of silently absorbing
or silently leaving them untracked.

## Scope
1. Determine the precise root cause of the AGENCY drift on all 4 `simq_routing_test_seed{42,456}
   _500t` / `hero_guild_routing_seed{42,456}_500t` run_keys — confirm or rule out
   `docs/guidelines/intentional_divergences.md` §2.41's `defer_with_reason` observability gap as
   the mechanism (not yet verified beyond a plausibility note), and determine why it manifests as
   a full `0/C` band-crossing on these 4 items but only a partial score-tolerance drift on the
   `seed123` variants.
2. Recalibrate `grade_anchors.json`'s AGENCY field for the 4 confirmed-drifted run_keys (and
   COGNITION/AGENCY for the 2 `seed123` variants, if confirmed same cause) following the
   established point-edit methodology, once root cause is confirmed.
3. Update `test_simq_routing_test_seed42_1000t_cognition_grade_stability` and
   `test_hero_guild_routing_seed42_1000t_cognition_grade_stability` to the deterministic
   bit-identical shape (matching how
   `TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP` converted the sibling
   `_500t` guard), once their own root cause is confirmed via a fresh multi-trial repro (not
   assumed identical just because the 500t sibling was).

## Out of Scope
- Any further work on `TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP`'s
  own named 4 COGNITION items or the `lifecycle_full_coverage_world_seed42_200t` anchor — already
  closed by that ticket.
- The pre-existing, unrelated `[known tick_budget: ...]` score-tolerance failures across the wider
  FAST_ANCHOR_KEYS corpus (computed deterministically from `detection_params.yaml` time_gates vs.
  `corpus_registry.yaml` tick counts, `tools/simq_ceiling.py`) — accepted, already-documented
  noise per established precedent, not this ticket's concern.
- `src/domains/adventure/`, `src/systems/strategic_systems/intelligence.py`, or any other
  production strategic-cognition code — Investigate first; only Plan/Implement touches source if a
  real code gap (not just a stale anchor) is confirmed.

## Acceptance Criteria
- [ ] Root cause of the AGENCY drift confirmed (or ruled out) as §2.41's `defer_with_reason` gap,
      via direct evidence (event-extractor/shaper trace), not assumed
- [ ] `grade_anchors.json` AGENCY (and COGNITION/AGENCY for the `seed123` variants, if in scope
      per Investigate's findings) recalibrated to confirmed live values
- [ ] `test_simq_routing_test_seed42_1000t_cognition_grade_stability` and
      `test_hero_guild_routing_seed42_1000t_cognition_grade_stability` re-verified fresh and
      updated to match their confirmed current behavior (deterministic bit-identical shape if
      confirmed no-longer-variable, matching the `_500t` sibling's precedent)
- [ ] `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q` shows 0
      unexplained failures for the 6 run_keys named in this ticket's Request Summary
- [ ] `pytest tests/unit/worldassembly/test_corpus_diversity.py -m slow -v` shows the 2 named
      `_1000t` guards passing (or a documented, deliberate decision not to convert them, with
      reasoning recorded)

## Related Tickets
- TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP (originating ticket;
  disclosed these findings via its own Implement-time fresh re-verification rather than fixing or
  silently absorbing them)
- TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION (DONE — root cause of the COGNITION-side
  drift for the same 4 run_keys; plausibly also touches AGENCY's mechanism, not confirmed)
- TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE (DONE — introduced §2.41's `defer_with_reason`
  observability gap, the leading hypothesis for the AGENCY drift)
- TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP (DONE — established the
  `watchdog_variance` ceiling mechanism and the `simq_routing_test_seed123_500t`/PROGRESSION
  ceiling entry whose own reason text is the "COGNITION stable" baseline this ticket's finding
  (2) contradicts)

## Related Docs
- docs/guidelines/intentional_divergences.md §2.40, §2.41
- docs/simulation_quality/eval_matrix_results.md (`simq_routing_test`, `hero_guild_routing`
  sections — NOTE blocks added by the originating ticket)

## Related Stored Artifacts
- staging_artifacts/TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP/ (once
  moved to stored_artifacts/ — investigation.md's "Adjacent, out-of-scope discovery" section and
  this ticket's own Implementation Notes record the raw pytest evidence for findings (1) and (2))

## Related Code Areas
- tests/simulation_quality/fixtures/grade_anchors.json (AGENCY fields for the 6 named run_keys)
- tests/unit/worldassembly/test_corpus_diversity.py (`test_simq_routing_test_seed42_1000t_cognition_grade_stability`,
  `test_hero_guild_routing_seed42_1000t_cognition_grade_stability`)
- src/domains/adventure/ (AGENCY event emission — `last_defer_reason`/`defer_with_reason`)
- src/observability/event_extractor.py / event_shapers.py (AGENCY event shaping)

## Assumptions / Open Questions
- Whether the full-zero AGENCY outcome on the 4 named `_500t` items vs. the partial score-tolerance
  drift on the 2 `seed123` variants is the same mechanism at different magnitudes, or two distinct
  mechanisms, is not yet determined — Investigate's job, not assumed here.
- Whether `docs/guidelines/intentional_divergences.md` §2.41 is the complete explanation, or only
  a partial one (given 3 more tier-5 GoalScorer commits landed in the same window per the
  originating ticket's investigation.md Risk #1), is not yet determined.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
