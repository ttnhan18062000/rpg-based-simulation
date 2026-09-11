---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260619-PARITY-P0-BUGS
phase: done
date: 2026-06-19
tags: [parity-ledger, combat, p0-bugs, aoe-legality, wound-threshold, missing-tests]
---

# TCK-20260619-PARITY-P0-BUGS

## Title
Parity Ledger P0/P1 Bug Cluster — COMB-006, COMB-290, COMB-133/134, STRAT-164/177, SOC-134

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P0

## Request Summary
Six parity ledger items resolved: behavioral fix (COMB-006), doc correction (COMB-290), stub documentation (COMB-133/134), and missing tests (STRAT-164, STRAT-177, SOC-134).

## Scope
- **COMB-006**: Added `alive/active` checks to AoE radius loop in `combat.py` — dead/inactive entities can no longer receive splash damage
- **COMB-290**: Updated `01_entity_anatomy.md` wound threshold to `> 0.25`; added wound section to `02_combat_laws.md` — docs now match code
- **COMB-133/134**: Marked `unsupported` — Phase 8/9 combat milestone stubs have no corresponding M8/M9 docs (M7 is current boundary)
- **STRAT-164**: Written `test_trait_serialization` — TraitDefinition Pydantic fields preserved from YAML
- **STRAT-177**: Written `test_all_trait_types_have_definitions` — all trait catalog entries have unique non-empty ids
- **SOC-134**: Written `test_social_appraisal_with_narrative` — public_reputation drives trust calculation; zero-rep rejected, high-rep accepted

## Out of Scope
- Broader combat refactoring beyond specific parity items
- Other P2 parity items

## Acceptance Criteria
- [x] COMB-006: status=verified, test_path populated, behavioral fix in place
- [x] COMB-290: status=verified, docs corrected to 25% threshold
- [x] COMB-133/134: status=unsupported with explanatory notes
- [x] STRAT-164, STRAT-177, SOC-134: status=verified, test_paths populated

## Related Tickets
- TCK-20260619-P0-CI-AUTOMATION

## Related Docs
- `docs/parity_ledger/combat_movement.yaml`
- `docs/parity_ledger/strategic_cognition.yaml`
- `docs/parity_ledger/social_narrative.yaml`
- `docs/mechanics/01_entity_anatomy.md`
- `docs/mechanics/02_combat_laws.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260618-AUDIT-EPIC/`

## Related Code Areas
- `src/engine/combat.py:513` (AoE radius loop)

## Assumptions / Open Questions
None.

## Implementation Notes
COMB-006 fix: 2-line guard in radius loop — `if not other_ent.combat.alive or not other_ent.lifecycle.active: continue`. This is the "radius application legality" check missing from the original implementation.

COMB-290: The divergence_note already said code was authoritative. Fixed docs to match code, not the other way around.

COMB-133/134: Stubs referenced "Phase 8/9 owns:" with no content and no corresponding docs. Marked unsupported rather than inventing behaviors.

STRAT-164/177: TraitDefinition is a `CatalogBaseDefinition(BaseModel)` with `extra="forbid"`, so Pydantic already enforces field integrity. Tests confirm fields load from traits.yaml correctly.

SOC-134: `public_reputation / 2.0` is the narrative trust signal. Zero-rep → trust=0.15 < 0.2 threshold → CANCELLED. rep=2.0 → trust=0.85 → ACCEPTED.

## Test Summary
- New `tests/unit/combat/test_parity_comb_006.py` — 3 tests (pass)
- New `tests/unit/content/test_parity_trait_defs.py` — 3 tests (pass)
- New `tests/unit/social/test_parity_soc_134.py` — 2 tests (pass)
- Existing AoE tests (`test_aoe_splash.py`, `test_phase5_combat_legality.py`) — still pass after COMB-006 fix

## Files Changed
- `src/engine/combat.py` — COMB-006: add alive/active guard in radius loop
- `docs/mechanics/01_entity_anatomy.md` — COMB-290: wound threshold corrected to `> 0.25`
- `docs/mechanics/02_combat_laws.md` — COMB-290: new Section 5 for wound threshold
- `docs/parity_ledger/combat_movement.yaml` — COMB-006, COMB-133, COMB-134, COMB-290 updated
- `docs/parity_ledger/strategic_cognition.yaml` — STRAT-164, STRAT-177 updated
- `docs/parity_ledger/social_narrative.yaml` — SOC-134 updated
- `tests/unit/combat/test_parity_comb_006.py` — NEW
- `tests/unit/content/test_parity_trait_defs.py` — NEW
- `tests/unit/social/test_parity_soc_134.py` — NEW

## Completion Summary
All 6 parity ledger items resolved. 8 new tests added. COMB-006 behavioral fix eliminates dead entity splash damage. COMB-290 docs now match source. COMB-133/134 stubs acknowledged as unsupported future scope.
