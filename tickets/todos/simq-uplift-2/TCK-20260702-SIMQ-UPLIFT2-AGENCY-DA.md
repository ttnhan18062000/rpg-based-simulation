---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA
phase: open
date: 2026-07-02
tags: [simulation_quality, agency, documentation, parity]
---

# TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA

## Title
Document AGENCY=C as design-intentional across non-routing calibration worlds

## Status
OPEN

## Tier
hotfix

## Type
documentation

## Priority
P2

## Request Summary
AGENCY pillar grades C in 27 of 30 calibration runs because `ENABLE_ADVENTURE_ROUTING=OFF` by default.
`AgencyScorer` events (`route_selected`, `action_executed`, `route_family_first_use`) are all gated
behind `AdventureDecisionPhase`, which short-circuits when the flag is OFF. Only `simq_routing_test`
(flag forced ON) shows AGENCY > C (A in 2 runs, B in 1).

The architectural decision (per user direction 2026-07-02) is to keep AGENCY=C in non-routing worlds
as design-intentional: the AdventureDecisionPhase is opt-in by world archetype, not a global default.
This ticket documents that decision with a DA annotation in `eval_matrix_results.md` and updates the
relevant parity ledger entries with `support_boundary` notes — mirroring the pattern used for
dungeon_crawl ECONOMY/COGNITION in TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG.

## Scope
1. Add a DA annotation block to `docs/simulation_quality/eval_matrix_results.md` under a new
   `## AGENCY — Cross-World Design Note` section (or inline after the grade tables) explaining:
   - AGENCY=C in all non-`simq_routing_test` worlds is archetype-correct
   - Root cause: `ENABLE_ADVENTURE_ROUTING=OFF` → `AdventureDecisionPhase` short-circuits →
     zero `route_selected`/`action_executed`/`route_family_first_use` events
   - Anti-drift: if any calibration world enables `ENABLE_ADVENTURE_ROUTING`, AGENCY will activate
     and grade anchors must be updated
2. Find AGENCY-related parity ledger entries in `docs/parity_ledger/strategic_cognition.yaml`
   (or `infrastructure.yaml`) and populate `support_boundary: null` with archetype-block notes.
3. Add a parenthetical note to `docs/simulation_quality/event_type_coverage.md` for
   `route_selected`, `action_executed`, `route_family_first_use` rows if not already present
   (similar to the dungeon_crawl notes added in TCK-DUNGEON-ECON-COG).
4. Run `make evaluate --dry-run` — must exit 0, 0 regressions.
5. Run `make knowledge-index-update`.

## Out of Scope
- Enabling `ENABLE_ADVENTURE_ROUTING` in any calibration world (separate architectural decision)
- Changing AGENCY scoring weights
- Any code changes — documentation only

## Acceptance Criteria
- [ ] `docs/simulation_quality/eval_matrix_results.md` contains a DA annotation explaining AGENCY=C
      as archetype-correct for non-routing worlds
- [ ] Relevant parity ledger entries updated with `support_boundary` notes (not null)
- [ ] `event_type_coverage.md` rows for `route_selected`, `action_executed`, `route_family_first_use`
      note the `ENABLE_ADVENTURE_ROUTING` gate and archetype-intentional zero hits in default worlds
- [ ] `make evaluate --dry-run` exits 0

## Related Tickets
- TCK-20260702-SIMQ-UPLIFT2-FACTION — sibling (same batch)
- TCK-20260702-SIMQ-UPLIFT2-INFORMATION — sibling (same batch)
- TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG — template: same DA documentation pattern

## Related Docs
- `docs/simulation_quality/eval_matrix_results.md` — grade tables; AGENCY=C in 27/30 runs
- `docs/simulation_quality/event_type_coverage.md` — `route_selected`/`action_executed`/`route_family_first_use` rows
- `docs/audits/D20_simq_integration.md` — P1 AGENCY item already resolved as "not a bug"
- `docs/plans/audit_fix_plan.md` — P0-A item: AGENCY routing gate

## Related Stored Artifacts
- `stored_artifacts/TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG/` — DA documentation template

## Related Code Areas
- `src/domains/optimization/feature_flags.py:16` — `ENABLE_ADVENTURE_ROUTING: FeatureMode.OFF`
- `src/domains/adventure/phase.py` — `AdventureDecisionPhase`; short-circuits when flag OFF
- `src/simulation_quality/scorers/agency.py` — `AgencyScorer`; all key events gated by same flag
- `docs/parity_ledger/strategic_cognition.yaml` — check for AGENCY/route_selected entries

## Assumptions / Open Questions
- UQ-1: Are there dedicated parity ledger entries for `route_selected`, `action_executed`, and
  `route_family_first_use` in `strategic_cognition.yaml`? If not, do entries exist in
  `infrastructure.yaml` or another file? Only update existing entries — do not create new P0 entries
  if no existing entry covers these events.

## Implementation Notes
Decision rationale (2026-07-02): the AdventureDecisionPhase is opt-in by world archetype. AGENCY=C
in non-routing worlds is the correct grade — no events should fire. The `simq_routing_test` world
exists precisely to verify that AGENCY *can* activate (AGENCY=A, confirming the scorer and emitters
are wired correctly). The pattern mirrors dungeon_crawl ECONOMY/COGNITION: structurally inactive by
design, not by bug.

Anti-drift note: if a new calibration world enables `ENABLE_ADVENTURE_ROUTING`, it must be identified
in the DA annotation as a routing-capable archetype and its AGENCY grades must be calibrated separately
from the "routing-inactive" majority.

## Test Summary
- No code tests needed (documentation only).
- `make evaluate --dry-run` must pass after any doc changes.

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
