---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260701-SIMQ-AGENCY-ROUTING-DOC
phase: done
date: 2026-07-01
tags: [simq, agency, documentation, feature-flag]
---

# TCK-20260701-SIMQ-AGENCY-ROUTING-DOC

## Title
Close out AGENCY zero-score investigation: confirmed non-bug, same root cause as P0-A

## Status
DONE

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
Context scan (mandatory): `mcp__knowledge-search__search_docs` for "AGENCY zero-score route_selected
action_executed ENABLE_ADVENTURE_ROUTING feature flag" and `graphify query` for the same topic
confirmed the D19/mechanics/TCK-20260627-P0A-ADVENTURE-FLAG chain — P0-A decision (Option B: all 10
Phase 10 flags stay OFF by default) is already recorded in `known_limitations.md` §1.5 and
`v2_intentional_divergences.md`. No conflicting or duplicate work found.

Three doc edits made (all doc-only, no source touched):
1. `docs/audits/D20_simq_integration.md` — Actionable Next Steps P1 AGENCY row rewritten from
   "Investigate AGENCY zero-score" to a resolved entry explaining the `last_routing_family` →
   `AdventureDecisionPhase` → `ENABLE_ADVENTURE_ROUTING` chain, cross-referencing P0-A and this ticket.
2. `docs/simulation_quality/event_type_coverage.md` §1.1 — `route_selected`/`action_executed` notes
   now state the 20 calibration_hits come entirely from `simq_routing_test` (flag forced ON) and are
   0 elsewhere because the flag defaults OFF. `route_family_first_use` note extended to explain its
   0 hits even in `simq_routing_test`: that calibration artifact (TCK-20260630-SIMQ-ROUTING-TEST) was
   captured before the emitter existed (TCK-20260701-SIMQ-EMIT-AGENCY2 added it later) — not
   recalibrated yet, tracked as a P0-A follow-up rather than a new gap.
3. `docs/plans/audit_fix_plan.md` — added a cross-reference line inside the P0-A entry (after the
   "Record the decision..." sentence) pointing to the D20 audit conclusion and this ticket. This
   satisfies acceptance criterion 4 (P0-A entry cross-links back to this finding); the ticket's
   "## Scope" section only listed 2 files but the acceptance criteria required a 3rd — treated the
   acceptance criteria as controlling since it is more specific/complete.

Parity check: searched all `docs/parity_ledger/*.yaml` for `route_selected`, `action_executed`,
`route_family_first_use`, `ENABLE_ADVENTURE_ROUTING`. Found 3 entries in `infrastructure.yaml`
(`INFRA-221`, `INFRA-250`, `SIMQ-CALIBRATED-001`) — all already `status: verified`, already describe
the emitters as correct and the flag as the gating mechanism, `test_path`s are current. No parity
ledger edit needed; nothing stale found. `strategic_cognition.yaml` has no AGENCY-routing entries.

## Test Summary
No code changed — no test run applicable. Doc-only ticket; source files unmodified (verified via
`git status --porcelain` before finalize — only the 3 docs files + this ticket file +
`agent-monitoring/tools.jsonl` show as changed).

## Files Changed
- `docs/audits/D20_simq_integration.md` (modified)
- `docs/simulation_quality/event_type_coverage.md` (modified)
- `docs/plans/audit_fix_plan.md` (modified)
- `tickets/inprogress/TCK-20260701-SIMQ-AGENCY-ROUTING-DOC.md` → `tickets/done/TCK-20260701-SIMQ-AGENCY-ROUTING-DOC.md` (this file)

## Completion Summary
Closed out the AGENCY zero-score investigation as a confirmed non-bug. Updated 3 docs to make the
`ENABLE_ADVENTURE_ROUTING` gate the explicit, cross-linked explanation everywhere the zero-score
previously read as an open question: `D20_simq_integration.md` (Actionable Next Steps P1 row
resolved), `event_type_coverage.md` (§1.1 notes for `route_selected`/`action_executed`/
`route_family_first_use`), and `audit_fix_plan.md` (P0-A entry cross-links back to the D20 finding
and this ticket). No source code touched. No behavior changed — parity ledger checked
(`infrastructure.yaml` INFRA-221/INFRA-250/SIMQ-CALIBRATED-001), all already accurate, no edits
needed. `make knowledge-index-update` run to re-embed the 3 changed docs. All 4 acceptance criteria
met.
