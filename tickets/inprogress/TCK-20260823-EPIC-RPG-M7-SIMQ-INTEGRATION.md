---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260823-EPIC-RPG-M7-SIMQ-INTEGRATION
phase: open
date: 2026-09-06
tags: [simulation-quality, calibration, content]
---

# TCK-20260823-EPIC-RPG-M7-SIMQ-INTEGRATION

## Title
Simulation Quality Pillar Integration (M7) — tracking epic for the 2-ticket SimQ audit/calibration sweep

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
`docs/plans/rpg_design_roadmap/rpg_m7_simq_pillar_integration_epic.md` (a single follow-up epic, not
per-milestone acceptance criteria) is gated on M1 through M6. Re-verified 2026-09-06: M1 (DONE), M2
(PR #101), M3 (PR #107), M4 (PR #115), M5 (PR #128), M6 (PR #133, merged today) are all real,
confirmed DONE — this milestone's gate is now clear for the first time. This epic scopes M7 into its
2 real child tickets so the M5/M6 implementer session can pick it up next, without itself doing any
implementation.

This epic tracks child tickets only; no direct implementation happens here.

**Real findings from this scoping pass, not inherited uncritically:**
- **The epic doc's own gate is now genuinely clear, not just "M1-M6 exist."** All 6 milestones were
  independently re-verified DONE with real merged-PR citations during this scoping pass (M5/M6's own
  roadmap headers were themselves stale — still describing gate conditions rather than shipped status
  — corrected in this same pass, see Related Docs).
- **A real, concrete complication for this epic's own Scope items 2 and 5, surfaced by this
  session's own prior review work, not assumed here:** at least 3 of the 65 ideas shipped across
  M5/M6 are disclosed as "built, not yet visible in play" — real code, real tests, but zero live
  reach in production today: idea 57 (`FameDeriver`/`LegendFact` — Perception/Motivation wiring
  targets two systems with zero live pipeline call sites), idea 62 (`FidelityDeriver` — ships with no
  live consumer yet), and idea 56 (`LoyaltyDriftService` — the one live per-tick call site never
  passes its signal, silently defaulting to 0.0). Per this epic's own Scope item 5 ("every idea
  Pillar Reach says should touch a pillar needs a traceable rule or an explicit, written reason it
  doesn't"), these three need an explicit, honest disposition in M7's audit — most likely "no live
  event type exists yet to register, tracked as a known gap" rather than either a fabricated SimQ
  rule for an event that never fires, or a silent omission from the completeness check.
- **The epic doc's own Open Question (one pass vs. two, after M1-M3 then M4-M6) is effectively
  resolved by the calendar, not decided here**: since M1-M6 all landed before M7 was ever scoped, a
  split-pass approach is now moot — this epic runs as the single, consolidated sweep the doc's own
  Problem section argued for.

## Scope
- Track, at epic level only, the 2 child tickets below, in the confirmed build order (mapping/rules
  before calibration/completeness — the second ticket's calibration run needs the first ticket's rule
  set to exist).
- Serve as the `## Related Tickets` link target once either child ticket is picked up for real
  implementation.
- Nothing else. No investigation.md/plan.md/test_plan.md staging artifacts at the epic level — each
  child ticket carries its own once picked up for implementation, per the epic-tier convention
  (`TCK-20260902-EPIC-RPG-M3-REPRODUCTION`, `TCK-20260823-EPIC-RPG-M6-POLITICAL-IDENTITY` precedent).

## Out of Scope
- Anything from Milestones 1 through 6's own functional scope — all confirmed DONE, not re-litigated
  here; this epic only touches SimQ's scoring rules, never the mechanisms themselves.
- Designing any signal rule before the event type it covers actually exists in shipped code.
- The metamorphic-lab balance-testing work (idea 37's pilot) — a different system, out of scope per
  the epic doc's own text.
- Actually implementing either child ticket — that is real, separate future work for whoever picks
  this epic up next.
- M9's own `CampaignScorecardEvaluator` field gap (Campaign-mode corpus grading) — a related but
  distinct SimQ gap, tracked in `docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md`,
  not this epic's scope.

## Acceptance Criteria
- [x] This epic ticket exists at `## Status: EPIC_SCOPED`, listing both child tickets in confirmed
      build order, with no implementation performed as part of closing this acceptance criterion.
- [x] The parent roadmap's M5/M6 sections are corrected from stale gate-status language to real
      shipped-status citations (done in this same pass, see Related Docs).
- [ ] A future session that picks up either child ticket runs it through the full standard-tier
      pipeline (Investigate → Plan → Implement → ... → Finalize) and links back to this epic.

## Related Tickets
### Child tickets (implementation sequence — see `tickets/todos/m7-simq-pillar-integration/SEQUENCE.md`)
- `TCK-20260906-SIMQ-PILLAR-MAPPING-AND-RULES` (epic Scope items 1-3) — no deps in this batch, land
  first.
- `TCK-20260906-SIMQ-CALIBRATION-AND-COMPLETENESS` (epic Scope items 4-5) — depends on (1) landing
  first; its calibration run needs a real rule set to exercise, and its completeness check needs (1)'s
  named-pillar mapping to check against.

### Related, not children
- `docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md` — a related but distinct SimQ
  gap (`CampaignScorecardEvaluator`'s own field coverage), not this epic's scope.

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_m7_simq_pillar_integration_epic.md`
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` — M5/M6 sections corrected in this same pass
  from stale gate-status language to real shipped-status citations (PR #128, PR #133)
- `docs/simulation_quality/quality_scoring_contract.md` — §1 Purpose & Scope, §5 The 10 Pillars
- `docs/brainstorm/design_merit_scorecard.html` — Pillar Reach axis, all 65 ideas
- `docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md`,
  `docs/plans/rpg_design_roadmap/rpg_m6_political_identity_epic.md` — the source of the 3
  "built, not yet visible in play" ideas flagged above

## Related Stored Artifacts
None — epic tier tracks child tickets only; each child ticket carries its own staging artifacts once
picked up for implementation.

## Related Code Areas
- `src/simulation_quality/` (`scorers/`, `pillar_accumulator.py`, `quality_report.py`, `quality_hub.py`)
- `tools/calibrate_simq.py`
- `docs/simulation_quality/quality_scoring_contract.md`
- `src/domains/fame/`, `src/domains/fidelity/`, `src/systems/social_systems/loyalty_drift.py` (the 3
  flagged "built, not yet visible in play" ideas)

## Assumptions / Open Questions
- Whether the 3 flagged dormant ideas (57, 62, 56) should be excluded from M7's pillar-mapping
  entirely, or included with an explicit "no live event type yet" note, is left to the first child
  ticket's own Investigate/Plan phases — not decided here.
- `SEQUENCE.md` in `tickets/todos/m7-simq-pillar-integration/` enforces the build order above for
  `implement-epic`.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
