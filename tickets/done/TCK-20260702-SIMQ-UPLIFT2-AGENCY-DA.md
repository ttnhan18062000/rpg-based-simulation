---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA
phase: done
date: 2026-07-02
tags: [simulation_quality, agency, documentation, parity]
---

# TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA

## Title
Document AGENCY=C as design-intentional across non-routing calibration worlds

## Status
DONE

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

**Implementation (2026-07-02):**

- Context search confirmed: `search_docs` surfaced `docs/audits/D19_domain_phase_inventory.md`
  §10, `docs/simulation/domains/adventure_contract.md`, and `docs/mechanics/adventure_routing_contract.md`
  as the relevant background on Adventure Routing; `graphify query` traversal did not surface a
  direct AgencyScorer→AdventureDecisionPhase edge, so the gate mechanism was confirmed directly via
  `src/engine/pipeline.py` (the `adventure_decision` phase is wrapped in
  `run_phase(..., "ENABLE_ADVENTURE_ROUTING")`, which short-circuits before
  `AdventureDecisionPhase.apply()` runs when the flag is OFF) and
  `src/domains/optimization/feature_flags.py:16` (`ENABLE_ADVENTURE_ROUTING: FeatureMode.OFF`).
- Added a `## AGENCY — Cross-World Design Note` section to `eval_matrix_results.md` (after the
  existing "AC6 — AGENCY Confirmation" section) covering root cause, the `simq_routing_test`
  counter-example, and the anti-drift note, mirroring the dungeon_crawl ECONOMY/COGNITION DA
  pattern from `stored_artifacts/TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG/`.
- UQ-1 resolved: no AGENCY/route_selected/action_executed/route_family_first_use entries exist in
  `docs/parity_ledger/strategic_cognition.yaml` (confirmed via grep — zero matches). The relevant
  entries are in `docs/parity_ledger/infrastructure.yaml`: `INFRA-237` (AgencyScorer contract
  coverage) and `SIMQ-CALIBRATED-001` (mentions `route_selected`/`action_executed` emission
  wiring directly). Both had `support_boundary: null`; both populated with archetype-block notes
  citing the `ENABLE_ADVENTURE_ROUTING` gate and cross-referencing the new eval_matrix_results.md
  DA note. No new parity entries were created, per UQ-1 guidance.
- Added archetype-intentional cross-reference notes to the `route_selected`, `action_executed`,
  and `route_family_first_use` rows in `event_type_coverage.md` (these rows already documented the
  `ENABLE_ADVENTURE_ROUTING` gate and zero-hit counts from prior tickets, but did not cross-reference
  the archetype-intentional DA framing — added a parenthetical pointing to the new
  eval_matrix_results.md AGENCY Cross-World Design Note, mirroring the `gold_sink_fired` /
  `decision_divergence_detected` dungeon_crawl DA cross-references already in the file).
- `make evaluate --dry-run` (via `.venv/bin/python3 tools/evaluate_simq.py --dry-run`): 250 pillars
  checked, 0 regressions, 0 missing, exit 0.
- `make knowledge-index-update`: incremental update, 2 files re-embedded (eval_matrix_results.md,
  event_type_coverage.md), 1829 unchanged from cache, exit 0.
- No code changes. No new parity ledger entries. No world spec, grade anchor, or scoring weight
  changes.

## Test Summary
- No code tests needed (documentation only).
- `make evaluate --dry-run` must pass after any doc changes.

## Files Changed
- `docs/simulation_quality/eval_matrix_results.md` — added `## AGENCY — Cross-World Design Note`
  section (after "AC6 — AGENCY Confirmation") documenting AGENCY=C as archetype-correct in
  non-routing calibration worlds, the `simq_routing_test` counter-example, and the anti-drift
  note tied to `ENABLE_ADVENTURE_ROUTING`.
- `docs/parity_ledger/infrastructure.yaml` — populated `support_boundary` (previously `null`) on
  `INFRA-237` (AgencyScorer contract coverage) and `SIMQ-CALIBRATED-001` (`route_selected`/
  `action_executed` emission wiring) with archetype-block notes citing the
  `ENABLE_ADVENTURE_ROUTING` gate.
- `docs/simulation_quality/event_type_coverage.md` — added archetype-intentional cross-reference
  notes to the `route_selected`, `action_executed`, and `route_family_first_use` rows, pointing to
  the new eval_matrix_results.md AGENCY Cross-World Design Note.

## Completion Summary
Documented AGENCY=C in 27/30 calibration runs as design-intentional rather than a defect: the
`AdventureDecisionPhase` (and the `AgencyScorer` events it gates — `route_selected`,
`action_executed`, `route_family_first_use`) is opt-in per world archetype via
`ENABLE_ADVENTURE_ROUTING` (default OFF), so zero-hit AGENCY events in non-routing worlds are
expected, not a bug. Confirmed the gate mechanism directly in `src/engine/pipeline.py`
(`adventure_decision` phase wrapped in `run_phase(..., "ENABLE_ADVENTURE_ROUTING")`) and
`src/domains/optimization/feature_flags.py:16`. Added a DA annotation to
`eval_matrix_results.md`, resolved UQ-1 by confirming no AGENCY/route_* entries exist in
`strategic_cognition.yaml` (only in `infrastructure.yaml`), and populated `support_boundary` notes
on `INFRA-237` and `SIMQ-CALIBRATED-001`. Cross-referenced the same framing into
`event_type_coverage.md`, mirroring the dungeon_crawl ECONOMY/COGNITION DA pattern from
`stored_artifacts/TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG/`. No code changes; no new parity
ledger entries created. Verification: `make evaluate --dry-run` — 250 pillars checked, 0
regressions, 0 missing, exit 0; `make knowledge-index-update` — 2 files re-embedded, exit 0.
