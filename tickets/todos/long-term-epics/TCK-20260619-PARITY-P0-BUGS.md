---
status: open
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260619-PARITY-P0-BUGS
phase: open
date: 2026-06-19
tags: [parity-ledger, combat, p0-bugs, aoe-legality, wound-threshold, missing-tests]
---

# TCK-20260619-PARITY-P0-BUGS

## Title
Parity Ledger P0/P1 Bug Cluster — COMB-006, COMB-290, COMB-133/134, STRAT-164/177, SOC-134

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P0

## Request Summary
Six already-flagged parity ledger items are unresolved. Per the Authoritative Mechanics Rule, P0 parity items block certification and must not wait on epic prioritization. These are pre-existing, acknowledged debt in the project's own parity ledger.

Source: `docs/plans/engine_future_epics_roadmap.md` § Immediate Cheap Fixes; `docs/parity_ledger/combat_movement.yaml`, `strategic_cognition.yaml`, `social_narrative.yaml`.

## Scope

**COMB-006** — AoE legality split (P0, `combat_movement.yaml`, status=missing):
- Impact-center and radius legality are currently unified in one check. Mechanics require split legality evaluation
- Implement split AoE legality check per mechanics contract; update parity entry to `verified`

**COMB-290** — Wound threshold divergence (P1, `combat_movement.yaml`, status=divergent):
- Code uses `damage > max_hp * 0.25`; mechanics bible specifies a different threshold
- Reconcile: either update code to match mechanics bible or document intentional divergence in `docs/guidelines/v2_intentional_divergences.md`

**COMB-133, COMB-134** — Empty ledger stubs "Phase 8 owns:" / "Phase 9 owns:" (P0, status=missing):
- Two parity entries with no content — documentation gap, not behavior gap
- Fill stub entries with the actual behavior they were intended to document; mark verified

**STRAT-164, STRAT-177** — Missing parity tests for strategic cognition (P0, `strategic_cognition.yaml`, status=missing):
- Two P0 ledger entries lack a `test_path`
- Write tests covering the documented behavior; update ledger entries with `test_path`

**SOC-134** — Missing parity test for social narrative (P0, `social_narrative.yaml`, status=missing):
- One P0 ledger entry lacks a `test_path`
- Write test; update ledger entry

## Out of Scope
- Broader combat refactoring beyond the specific parity items
- Parity ledger P2 items

## Acceptance Criteria
- All 6 parity items above have status=verified in their respective YAML files
- All P0 items have a non-empty `test_path` that points to a passing test
- COMB-290: either code matches mechanics bible, or an entry appears in `docs/guidelines/v2_intentional_divergences.md`

## Related Tickets
- TCK-20260619-P0-CI-AUTOMATION (P0 parity tests will run in CI after that ticket)

## Related Docs
- `docs/plans/engine_future_epics_roadmap.md` § Immediate Cheap Fixes
- `docs/parity_ledger/combat_movement.yaml`
- `docs/parity_ledger/strategic_cognition.yaml`
- `docs/parity_ledger/social_narrative.yaml`
- `docs/mechanics/02_combat_laws.md` (authoritative AoE legality and wound threshold formulas — COMB-006 and COMB-290 must match values here after fix)
- `docs/mechanics/04_strategic_cognition.md` (STRAT-164 and STRAT-177 behaviors are documented here — tests must match this doc exactly)
- `docs/guidelines/v2_intentional_divergences.md` (for COMB-290 if divergence is intentional)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260618-AUDIT-EPIC/`

## Related Code Areas
- `src/domains/` (combat resolution — AoE legality logic)
- `tests/` (find existing combat tests to extend for parity coverage)

## Assumptions / Open Questions
- For COMB-290: is the 0.25 threshold a deliberate gameplay decision or an error? Read `docs/mechanics/02_combat_laws.md` for the authoritative value, then compare to code
- For COMB-133/134: what do "Phase 8 owns" and "Phase 9 owns" refer to? Check pipeline phases in `src/engine/pipeline.py`

## Implementation Notes
Read each parity YAML entry before touching code. For each item: understand the documented behavior → find the code → verify or fix → update ledger entry. COMB-006 is a behavioral change; COMB-133/134 and STRAT/SOC missing tests are documentation/test debt.

After each item is verified: update the relevant parity YAML (`combat_movement.yaml`, `strategic_cognition.yaml`, or `social_narrative.yaml`) — set `status: verified`, populate `test_path`, add `v2_evidence`. For COMB-290: if divergence is intentional, add an entry to `docs/guidelines/v2_intentional_divergences.md`. Run `make knowledge-index-update` after any docs/ changes.

## Test Summary
- New file `tests/unit/combat/test_parity_p0_bugs.py`:
  - `test_aoe_legality_split_impact_vs_radius()` — COMB-006: configure AoE attack; assert impact-center legality and radius legality are evaluated independently (not unified)
  - `test_wound_threshold_matches_mechanics_bible()` — COMB-290: assert wound threshold constant matches `docs/mechanics/02_combat_laws.md` authoritative value (or that divergence is documented in `v2_intentional_divergences.md`)
  - `test_comb_133_phase8_behavior_documented()` — COMB-133: assert ledger stub is filled (non-empty v2_evidence)
  - `test_comb_134_phase9_behavior_documented()` — COMB-134: assert ledger stub is filled (non-empty v2_evidence)
- New file `tests/unit/cognition/test_parity_strat_164_177.py`:
  - `test_strat_164_behavior()` — STRAT-164: test the specific behavior described in the ledger entry (read entry first for exact behavior)
  - `test_strat_177_behavior()` — STRAT-177: test the specific behavior described in the ledger entry
- New file `tests/unit/social/test_parity_soc_134.py`:
  - `test_soc_134_behavior()` — SOC-134: test the specific behavior described in the ledger entry
- All test paths must be referenced in the parity YAML `test_path` fields after passing

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
