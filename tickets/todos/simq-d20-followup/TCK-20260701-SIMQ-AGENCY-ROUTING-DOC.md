---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260701-SIMQ-AGENCY-ROUTING-DOC
phase: open
date: 2026-07-01
tags: [simq, agency, documentation, feature-flag]
---

# TCK-20260701-SIMQ-AGENCY-ROUTING-DOC

## Title
Close out AGENCY zero-score investigation: confirmed non-bug, same root cause as P0-A

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
D20 audit (Actionable Next Steps, P1 row #2) asked to "investigate AGENCY zero-score — confirm
whether `route_family_first_use`/`action_executed` conditions are hit in any world... may be
legitimate or a diff condition bug." Investigation traced the full chain and found **this is
not a bug**:

- `route_selected`/`action_executed`/`route_family_first_use` all depend on
  `property_updates["last_routing_family"]` being set (`src/observability/event_extractor.py`,
  ~L240-263).
- That field is only written in `src/domains/adventure/phase.py` (~L137-139) inside
  `AdventureDecisionPhase`.
- `AdventureDecisionPhase` is gated by the `ENABLE_ADVENTURE_ROUTING` feature flag
  (`src/domains/adventure/service.py` call site in `src/engine/pipeline.py` ~L227-236,
  `run_phase()` short-circuits entirely when the flag is `OFF`).
- `ENABLE_ADVENTURE_ROUTING` defaults to `FeatureMode.OFF`
  (`src/domains/optimization/feature_flags.py:16`) — this is **already tracked** as
  `P0-A` in `docs/plans/audit_fix_plan.md` ("all 8 feature flags... default to OFF").
- Confirms the audit's own §"What SimQ Actually Shows" note: AGENCY scores B in
  `simq_routing_test` (where the flag is force-enabled via env var) and C everywhere else.

`commitment_abandoned` and `rejection_cascade_tick` (also zero in sandbox_world) are
independently legitimate zero-signal: sandbox_world has no project abandonment and rejection
volume never crosses the 20/tick cascade threshold in a combat-only scenario — not
routing-gated, just genuinely inactive conditions.

This ticket is documentation-only: there is no code fix here distinct from resolving P0-A.

## Scope
1. Update `docs/audits/D20_simq_integration.md` "Actionable Next Steps" P1 row #2 — mark
   resolved, cross-reference `P0-A` in `audit_fix_plan.md` as the actual blocker (not an AGENCY
   scorer defect).
2. Update `docs/simulation_quality/event_type_coverage.md` notes for `route_selected`,
   `action_executed`, `route_family_first_use` to state the `ENABLE_ADVENTURE_ROUTING` gate
   explicitly (currently the doc shows `calibration_hits` without explaining the zero-hit
   worlds' cause).
3. No source code change.

## Out of Scope
- Deciding the default state of `ENABLE_ADVENTURE_ROUTING` (that decision belongs to P0-A)
- Any scorer or emitter logic changes — emitters are confirmed correct

## Acceptance Criteria
- [ ] D20 audit's P1 AGENCY action item updated from "investigate" to "resolved — see P0-A"
- [ ] `event_type_coverage.md` AGENCY routing rows explain the feature-flag gate
- [ ] No source files touched
- [ ] `docs/plans/audit_fix_plan.md` P0-A entry cross-links back to this finding

## Related Tickets
- P0-A (`docs/plans/audit_fix_plan.md`, `ENABLE_ADVENTURE_ROUTING` defaults to OFF) — the
  actual root cause; this ticket does not duplicate that decision, only documents the link
- TCK-20260701-SIMQ-EMIT-AGENCY2 — added the 4 emitters confirmed correct here
- TCK-20260630-SIMQ-ROUTING-TEST — built `simq_routing_test` world proving AGENCY scores B
  once routing is enabled
- TCK-20260628-SIMQ-EPIC — parent epic (done)

## Related Docs
- `docs/audits/D20_simq_integration.md` — Actionable Next Steps, P1 row #2
- `docs/plans/audit_fix_plan.md` — P0-A section
- `docs/simulation_quality/event_type_coverage.md` §1.1 (route_selected/action_executed)

## Related Stored Artifacts
- (none yet)

## Related Code Areas
- `src/domains/optimization/feature_flags.py:16` (ENABLE_ADVENTURE_ROUTING default — read-only reference)
- `src/engine/pipeline.py` ~L211-236 (`run_phase` gate)
- `src/domains/adventure/phase.py` ~L137-139 (`last_routing_family` write site)
- `src/observability/event_extractor.py` ~L240-263 (AGENCY emitter diff condition)

## Assumptions / Open Questions
- Assumes P0-A remains a deliberately separate decision (production feature-gate policy)
  rather than something this ticket should resolve. If P0-A is resolved first (flag flips
  to ON), re-verify AGENCY scores non-zero in sandbox_world as a quick confirmation, but
  that's incidental validation, not new scope.

## Implementation Notes
(to be filled at implementation)

## Test Summary
(to be filled at implementation)

## Files Changed
(to be filled at implementation)

## Completion Summary
(to be filled at completion)
