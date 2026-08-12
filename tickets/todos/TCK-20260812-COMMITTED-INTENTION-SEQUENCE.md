---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260812-COMMITTED-INTENTION-SEQUENCE
phase: open
date: 2026-08-12
tags: [cognition, strategy, progression]
---

# TCK-20260812-COMMITTED-INTENTION-SEQUENCE

## Title
Implement `CommittedIntention` durable multi-step planning model

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Follow-up implementation ticket for the accepted design in
`docs/architecture/2026-08-12-multi-step-persistent-planning-design.md`
(`TCK-20260811-MULTI-STEP-PLANNING-DESIGN`, decision: GO). That ticket was design-scoping only —
no production code — and produced a fully-specified but unimplemented model: a new
`CommittedIntention` durable typed record letting an entity commit to a short (2-4 step) ordered
sequence of future intentions (e.g. train -> craft -> quest) rather than re-deciding the single
next action every eligible tick, materialized one step at a time as an ordinary tier-5
`GoalRegistry` candidate through the existing, **unmodified** `evaluate_project_switch()` arbiter.

## Scope
- Add `CommittedIntention` frozen dataclass (`intention_id`, `goal_kind`, `target_hint`,
  `sequence_index`, `status`) and a `committed_intentions: Tuple[CommittedIntention, ...]` field on
  `StrategicComponent` (`src/core/strategic.py`), per the design doc's Design §2
- Add `max_committed_intentions: int = 3` to `CognitionProfile` (`src/core/strategic.py`), per
  Design §2
- Add the materialization hook that feeds `committed_intentions[0]` into `evaluate_strategic_intent()`'s
  tier-5 candidate field when due (current project absent/abandoned/completed), using the same
  per-`goal_kind` mapping pattern already established for tier-5 winners (`RouteToProjectMapper`
  precedent) -- per Design §4
- Implement "losing candidate stays queued, doesn't get discarded" retry semantics: a committed
  intention that loses one tick's arbitration remains at `sequence_index` 0 and re-competes next
  eligible tick until it wins, is explicitly abandoned, or is skipped -- per Design §4. This
  bookkeeping lives entirely in the new `committed_intentions` tracking, not inside
  `evaluate_project_switch()` itself
- Add the Mechanics Bible update (`docs/mechanics/04_strategic_cognition.md`) and a new parity
  ledger entry (`docs/parity_ledger/strategic_cognition.yaml`) documenting the landed mechanism,
  per Design §7 (deferred, not performed by the design-scoping ticket)
- Cap sequences at `max_committed_intentions=3` entries -- no branching, no conditional sequences
  (MVP scope, not the design doc's full illustrative generality)

## Out of Scope
- Any change to `evaluate_project_switch()`'s own code, signature, or the STRAT-236
  `_threat_resolved()` lock-expiry check -- the design's central premise is that committed
  intentions compete as an ordinary, unmodified tier-5 candidate; changing the arbiter itself would
  invalidate that premise and require re-verifying STRAT-185/186/187
- Any change to `ProgressionPlan.goal_queue`, `PlanRevisionService`, or
  `ProgressionPlanExporter`/`Importer` -- the design doc's Design §3 establishes these coexist with
  clearly separated, non-overlapping responsibility; this ticket does not blur that boundary
- Any new `GoalKind`/`GoalScorer` -- committed intentions reuse the existing `GoalKind` vocabulary
  per Design §2
- UI/observability surface beyond the Durable State Rule's minimum (inspection/debug visibility) --
  the exact surface shape (EntityInspector field, decision-trace entry, dedicated debug endpoint)
  is one of the design doc's own genuinely-open implementation questions, not pre-decided here
- Repurposing `CognitionProfile.reserved_detour_depth` -- the design doc's Design §5 confirmed this
  field is unrelated (bounds reactive detour-chain nesting, not proactive intention sequencing)

## Acceptance Criteria
- [ ] `CommittedIntention` dataclass and `committed_intentions` field added to `StrategicComponent`,
      matching the design doc's Design §2 sketch (frozen, `slots=True`-consistent pattern)
- [ ] `max_committed_intentions` field added to `CognitionProfile`, defaulting to 3
- [ ] `evaluate_strategic_intent()` materializes `committed_intentions[0]` (when due) into tier 5's
      candidate field as one ordinary candidate -- no new tier, no bypass, `evaluate_project_switch()`
      itself byte-identical (verify via `git diff --stat -- src/systems/strategic_systems/intelligence.py`
      touching only the materialization/injection point, not the arbiter function's own body)
- [ ] Losing committed intentions are retried next eligible tick, not discarded -- regression test
      proves a losing candidate's `sequence_index`/status persist across a tick where it loses
      arbitration
- [ ] `docs/mechanics/04_strategic_cognition.md` and `docs/parity_ledger/strategic_cognition.yaml`
      updated in the same session, per CLAUDE.md's Authoritative Mechanics Rule
- [ ] STRAT-185/186/187 (`docs/parity_ledger/strategic_cognition.yaml`) re-run and confirmed still
      passing unmodified, since this ticket's design explicitly claims no new arbiter path requires
      their re-verification -- confirm that claim empirically, not just by citation
- [ ] The genuinely-open implementation questions from the design doc are resolved with explicit,
      documented decisions (not silently defaulted): the `max_committed_intentions=3` cap's
      validation, mid-sequence-skip abandonment semantics, `target_hint` re-resolution-failure
      handling, whether `ProgressionPlan.goal_queue` should auto-seed `committed_intentions`, and the
      observability-surface shape

## Related Tickets
- TCK-20260811-MULTI-STEP-PLANNING-DESIGN (DONE -- the design-scoping ticket that produced the
  accepted design this ticket implements)
- TCK-20260619-E61-PROGRESSION

## Related Docs
- docs/architecture/2026-08-12-multi-step-persistent-planning-design.md (the accepted design this
  ticket implements)
- docs/mechanics/04_strategic_cognition.md
- docs/parity_ledger/strategic_cognition.yaml
- docs/simulation/domains/progression_planner_contract.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/core/strategic.py (`StrategicComponent`, `CognitionProfile`)
- src/systems/strategic_systems/intelligence.py (`evaluate_strategic_intent()`'s tier-5
  materialization point)

## Assumptions / Open Questions
- The design doc's own "Open Questions For Implementation" section lists 5 genuinely-unresolved
  details this ticket's Investigate/Plan phases must resolve with real implementation-time
  judgment, not treat as pre-decided: (1) whether `max_committed_intentions=3` is empirically
  right, (2) mid-sequence-skip abandonment semantics, (3) `target_hint` re-resolution-failure
  handling, (4) whether `goal_queue` should auto-seed `committed_intentions`, (5) the
  observability-surface shape
- The design doc traced and confirmed a duplicate-`GoalKind` coexistence scenario (a committed
  intention reusing a kind with a currently-registered live scorer) is structurally harmless against
  current code (`intelligence.py:1393-1408`'s two `.kind` consumers are both duplicate-tolerant) --
  this ticket's Investigate phase should re-verify this trace still holds against the code as it
  exists when this ticket is actually implemented, not assume it's still true unchanged

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
