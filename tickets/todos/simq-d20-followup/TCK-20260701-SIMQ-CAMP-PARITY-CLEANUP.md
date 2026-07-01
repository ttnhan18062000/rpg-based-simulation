---
status: active
layer: simulation
authority: P3
audience: agent
ticket_id: TCK-20260701-SIMQ-CAMP-PARITY-CLEANUP
phase: open
date: 2026-07-01
tags: [simq, parity-ledger, documentation, camp_constructed]
---

# TCK-20260701-SIMQ-CAMP-PARITY-CLEANUP

## Title
Update stale parity-ledger language for camp_constructed (still says "blocked", not "no engine path")

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
D20 audit (Actionable Next Steps, P3 row) asks to formally remove `camp_constructed` from the
82-event scored set in `event_type_coverage.md` if the mechanic isn't planned.
`event_type_coverage.md` itself is already correct — it lists `camp_constructed` under
`no_engine_path` (count 1), separate from `scored` (81), with a clear note that
`TCK-20260701-SIMQ-EMIT-CAMP` closed with the finding that no dynamic camp construction
mechanic exists (`StateUpdate` has no `camps_add`; camps are pre-placed at world generation).

However, two other docs still carry the stale "blocked, future ticket" framing that
`TCK-20260701-SIMQ-EMIT-CAMP` superseded:
- `docs/parity_ledger/world_dynamics.yaml`, entry `WORLD-109`: `divergence_note` says
  "camp_constructed blocked: CampService (src/world/camp.py) has no event recorder interface;
  adding it requires an interface change tracked as a future ticket." This contradicts the
  closed ticket's actual conclusion (no viable path, not planned — not "future ticket").
- `docs/simulation_quality/quality_scoring_contract.md` line ~805 lists `camp_constructed` in
  the WORLD dynamics "Event types scored" list with no caveat, implying it's live when it
  isn't.

This is pure documentation consistency — no code or scorer changes (the scorer keeps its
`camp_constructed` branch and test per `src/simulation_quality/scorers/world_dynamics.py:28,166`
and `tests/simulation_quality/test_world_dynamics_scorer.py:137`, since the scorer entry is
intentionally retained for if/when a camp-construction mechanic is ever added).

## Scope
1. Update `docs/parity_ledger/world_dynamics.yaml` `WORLD-109` divergence_note to match the
   current, correct conclusion: camp_constructed has no viable engine path under the current
   camp lifecycle model (pre-placed at world gen, `CampService` only evolves existing camps);
   remove the "tracked as a future ticket" framing since `TCK-20260701-SIMQ-EMIT-CAMP` closed
   without a follow-up planned.
2. Add a footnote/caveat to `quality_scoring_contract.md`'s WORLD dynamics event list marking
   `camp_constructed` as "registered, not currently emittable — see event_type_coverage.md §3.9".
3. No changes to `src/simulation_quality/scorers/world_dynamics.py` or its tests.

## Out of Scope
- Adding a dynamic camp-construction mechanic to the engine
- Removing the `camp_constructed` scorer branch or its test
- Any change to `event_type_coverage.md` (already correct)

## Acceptance Criteria
- [ ] `world_dynamics.yaml` WORLD-109 divergence_note no longer implies pending/future work
- [ ] `quality_scoring_contract.md` WORLD dynamics event list caveats `camp_constructed`
- [ ] No source or test files changed
- [ ] Cross-check `docs/plans/audit_fix_plan.md:465` (WORLD dynamics signals list) for the
      same stale framing and correct if present

## Related Tickets
- TCK-20260701-SIMQ-EMIT-CAMP — closed; established the "no viable engine path" conclusion
  this ticket propagates into the parity ledger
- TCK-20260701-SIMQ-EMIT-WORLD-DYNAMICS — added WORLD-108/109 parity entries
- TCK-20260628-SIMQ-EPIC — parent epic (done)

## Related Docs
- `docs/simulation_quality/event_type_coverage.md` §3.9 (already correct — reference only)
- `docs/parity_ledger/world_dynamics.yaml` — WORLD-109
- `docs/simulation_quality/quality_scoring_contract.md` — WORLD dynamics event list
- `docs/plans/audit_fix_plan.md:465`

## Related Stored Artifacts
- (none yet)

## Related Code Areas
- `src/simulation_quality/scorers/world_dynamics.py:28,166` (reference only, no change)
- `tests/simulation_quality/test_world_dynamics_scorer.py:137` (reference only, no change)

## Assumptions / Open Questions
- None — this is a low-ambiguity doc-consistency fix.

## Implementation Notes
(to be filled at implementation)

## Test Summary
(to be filled at implementation)

## Files Changed
(to be filled at implementation)

## Completion Summary
(to be filled at completion)
