---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP
phase: open
date: 2026-08-11
tags: [simulation-quality, calibration, corpus]
---

# TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP

## Title
`/simq-audit mode=full` run `SIMQ-AUDIT-20260811T111151Z` found 2 real, disclosed findings: a
design-acknowledgment gap in yesterday's watchdog-variance fix, and a newly-exposed 7/8-pillar
drift on a never-registered anchor key

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
While satisfying `TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE`'s AC5 (invoke `/simq-audit
mode=full` as a pre-cutover gate and record its verdict), a full audit run
(`SIMQ-AUDIT-20260811T111151Z`) surfaced two distinct real findings that this audit workflow does
not fix itself, per its own governance:

**(1) DA_NEEDED — 4 COGNITION-pillar REGRESS items cross the discrete ±1 grade band, a check
`TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP`'s `watchdog_variance` ceiling mechanism
does not cover:**
- `simq_routing_test_seed42_500t` COGNITION anchor=A actual=C
- `simq_routing_test_seed456_500t` COGNITION anchor=A actual=C
- `hero_guild_routing_seed42_500t` COGNITION anchor=S actual=C
- `hero_guild_routing_seed456_500t` COGNITION anchor=A actual=C

Yesterday's ticket confirmed real, watchdog-throttle-driven (D06 F6) run-to-run non-determinism
on FAST-tier scenarios and added `score_ceilings.json` `watchdog_variance` entries for
`simq_routing_test_seed42_500t` (PROGRESSION, COGNITION), `simq_routing_test_seed123_500t`
(PROGRESSION), and `urban_political_seed456_500t` (ECONOMY, PROGRESSION) — but that ceiling only
feeds `test_grade_regression.py`'s score-tolerance failure-message path
(`_format_score_failures()`), not the separate, harder `_within_band()` discrete-grade check.
Confirmed directly by reading the test file: the two checks are genuinely independent code paths.

Two of today's 4 items were explicitly sampled and pronounced "stable" by yesterday's ticket based
on only light (2x/3x) re-run sampling — `simq_routing_test_seed456_500t` COGNITION ("stable at
0.6415/63 events across 2 re-runs, though only lightly sampled") and `hero_guild_routing_seed42_500t`
("stable or only sub-tolerance noise"). Today's runs (2 independent re-runs, both showing the same
4 items) directly contradict that conclusion. The other 2 items either had a ceiling for a
different pillar/check-branch than what's failing today (`simq_routing_test_seed42_500t`) or were
recalibrated as "confirmed stable via 3x re-run" (`hero_guild_routing_seed456_500t`) — also
contradicted.

**The open design question**: should the `watchdog_variance` ceiling mechanism be extended to also
suppress/annotate discrete grade-band crossings (not just score-tolerance), given the same
low-event-count watchdog-throttle root cause plausibly explains a band crossing too? Or is a grade
crossing of this size (S→C, a 3-band jump) evidence of something beyond ordinary watchdog jitter,
warranting deeper investigation rather than a wider ceiling? This is a real ruling this ticket does
not make itself.

**(2) A newly-exposed, real drift gap on `lifecycle_full_coverage_world_seed42_200t`:**
`TCK-20260808-LIFECYCLE-FULL-COVERAGE-WORLD` added this anchor entry but never registered the key
in `FAST_ANCHOR_KEYS` (confirmed absent from the list) and no dedicated isolated test exists for
it — a genuine "registration step missed" gap, distinct from the two `urban_political_selfmodel_*`
keys (which the audit also flags as "uncovered" but are actually correctly covered by their own
dedicated isolated tests — confirmed false positives, no action needed for those two).

Registering `lifecycle_full_coverage_world_seed42_200t` in `FAST_ANCHOR_KEYS` (a mechanical,
disclosed edit already made — see Files Changed) immediately surfaced that **7 of its 8 pillars**
(COGNITION, AGENCY, COMBAT, PROGRESSION, SOCIAL, WORLD, NARRATIVE — only FACTION is within band)
drift beyond score tolerance against the anchor values committed at creation time, never verified
since. This matches the same SUB-384-cascade drift pattern several other worlds already had fixed
by `TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP` and its predecessor tickets — but this
specific key was never gated, so nobody looked at it during those fixes.

## Scope
1. **Investigate finding (1)**: determine whether the 4 COGNITION band-crossing items share the
   same root cause as yesterday's confirmed watchdog-variance instability (re-sample each with
   multiple re-runs, check for `WatchdogTrip` alerts, compare event counts across runs — same
   methodology `TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP` used). Make a concrete
   recommendation: extend `watchdog_variance` ceiling coverage to the grade-band check too (and
   how — this needs either a `test_grade_regression.py` code change to `_within_band()`, or a
   different mechanism), or treat as a distinct issue requiring its own investigation.
2. **Investigate finding (2)**: confirm `lifecycle_full_coverage_world_seed42_200t`'s 7-pillar
   drift is the same already-understood SUB-384 cascade (via `compile_context.json`
   legacy_roles/legacy_factions inspection, same methodology as prior recalibration tickets) —
   not assumed, verified per-pillar.
3. **Plan/Implement**: for finding (1), implement whatever concrete resolution Investigate
   recommends. For finding (2), if confirmed as the known cascade, recalibrate
   `grade_anchors.json` for the 7 drifted pillars following the established pattern.

## Out of Scope
- `TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE`'s own scope (the shadow-parity test suite that
  triggered this audit run) — already DONE, not revisited here.
- The already-fixed SUB-384 root cause itself (`WorldCompiler.compile()`) — not touched, only
  its downstream calibration-data staleness.
- The already-landed `watchdog_variance` ceiling entries from `TCK-20260810-SIMQ-FAST-TIER-DRIFT-
  AND-RELIABILITY-GAP` for `simq_routing_test_seed42_500t`'s PROGRESSION pillar,
  `simq_routing_test_seed123_500t`, and `urban_political_seed456_500t` — untouched, still correct
  for the score-tolerance check they cover.

## Acceptance Criteria
- [ ] All 4 COGNITION band-crossing items re-sampled with a real multi-trial investigation (not
      assumed); root cause confirmed or ruled out as the same watchdog-variance mechanism
- [ ] A concrete decision made and implemented for extending (or not extending) the
      `watchdog_variance` mechanism to cover discrete grade-band crossings, with reasoning
      recorded
- [ ] `lifecycle_full_coverage_world_seed42_200t`'s 7-pillar drift investigated and confirmed (or
      ruled out) as the SUB-384 cascade pattern
- [ ] `grade_anchors.json` recalibrated for `lifecycle_full_coverage_world_seed42_200t` if
      confirmed as expected drift, following the established methodology
- [ ] `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q` shows 0
      unexplained failures for all 5 items above (either passing, or carrying a `[known ...]`
      annotation with a documented reason)

## Related Tickets
- TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP (DONE — established the watchdog_variance
  mechanism and root-caused the same instability class this ticket extends)
- TCK-20260808-LIFECYCLE-FULL-COVERAGE-WORLD (DONE — created the `lifecycle_full_coverage_world_
  seed42_200t` anchor entry that was never registered/gated)
- TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE (the ticket whose AC5 `/simq-audit` invocation
  discovered this)

## Related Docs
- docs/audits/D06_longrun_health.md (F6, the watchdog-throttle mechanism)
- docs/simulation_quality/audit_workflow.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- tests/simulation_quality/test_grade_regression.py (`_within_band()`, `_format_score_failures()`,
  `FAST_ANCHOR_KEYS` — the newly-added `lifecycle_full_coverage_world_seed42_200t` registration
  already landed here, uncommitted)
- tests/simulation_quality/fixtures/score_ceilings.json (`watchdog_variance` ceiling entries)
- tests/simulation_quality/fixtures/grade_anchors.json

## Assumptions / Open Questions
- The `lifecycle_full_coverage_world_seed42_200t` FAST_ANCHOR_KEYS registration edit is already
  made in the working tree (uncommitted) as a direct result of this audit run — Implement should
  build on it, not re-do it, but should verify it's still correct before assuming so.
- Whether the 4 COGNITION band-crossing items are genuinely the same watchdog mechanism or
  something new is explicitly NOT assumed here — Investigate's own job.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
